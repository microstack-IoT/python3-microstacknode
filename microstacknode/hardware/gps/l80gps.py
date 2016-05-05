# http://www.gsm-rainbow.ru/sites/default/files/l80_gps_protocol_specification_v1.0.pdf
import re
import io
import sys
import time
import serial
import logging
import datetime
import threading
import subprocess
# logging.basicConfig(level=logging.DEBUG)


# Test these with `echo -e "\$PMTK161,0*28\r\n" > /dev/ttyAMA0`
PMTK_STANDBY = '$PMTK161,0*28\r\n'
PMTK_SET_PERIODIC_MODE_NORMAL = '$PMTK225,0*2B\r\n'
PMTK_SET_PERIODIC_MODE_AUTO_LOCATE_STANDBY = '$PMTK225,8*23\r\n'
PMTK_SET_PERIODIC_MODE_SLEEP = '$PMTK225,2,3000,12000,18000,72000*15\r\n'
PMTK_LOCUS_QUERY_STATUS = '$PMTK183*38\r\n'
PMTK_LOCUS_ERASE_FLASH = '$PMTK184,1*22\r\n'
PMTK_LOCUS_STOP_LOGGER = '$PMTK185,1*23\r\n'
PMTK_LOCUS_START_LOGGER = '$PMTK185,0*22\r\n'
PMTK_Q_LOCUS_DATA_FULL = '$PMTK622,0*28\r\n'
PMTK_Q_LOCUS_DATA_PARTIAL = '$PMTK622,1*29\r\n'


# setup default GPS device (different on Raspberry Pi 3 and above)
def get_rpi_revision():
    """Returns the version number from the revision line."""
    for line in open("/proc/cpuinfo"):
        if "Revision" in line:
            return re.sub('Revision\t: ([a-z0-9]+)\n', r'\1', line)


rpi_revision = get_rpi_revision()
if (rpi_revision and
      (rpi_revision != 'Beta') and
      (int('0x'+rpi_revision, 16) >= 0xa02082)):
    # RPi 3 and above
    DEFAULT_GPS_DEVICE = '/dev/ttyS0'
else:
    # RPi 2 and below
    DEFAULT_GPS_DEVICE = '/dev/ttyAMA0'


class NMEAPacketNotFoundError(Exception):
    pass


class DataInvalidError(Exception):
    pass


class LOCUSQueryDataError(Exception):
    pass


class L80GPS(object):
    """Thread that reads a stream of L80 GPS protocol lines and stores the
    information. Methods may raise exceptions if data is invalid (usually
    becasue of a poor GPS reception - try moving the GPS module outside).
    """

    def __init__(self, device=DEFAULT_GPS_DEVICE):
        self.device_tx_rx = serial.Serial(device,
                                          baudrate=9600,
                                          bytesize=8,
                                          parity='N',
                                          stopbits=1,
                                          timeout=0.5,
                                          rtscts=0)

    ####################################################################
    # REMOVE PROPERTIES
    ####################################################################
    def _property_depricated_warning(self, p):
        print('WARNING: properties will be removed in next major version. '
              'Use `l80gps.get_{}()` instead of `l80gps.{}`'.format(p),
              file=sys.stderr)

    @property
    def gprmc(self):
        self._property_depricated_warning('gprmc')
        return self.get_gprmc()

    @property
    def gpvtg(self):
        self._property_depricated_warning('gpvtg')
        return self.get_gpvtg()

    @property
    def gpgga(self):
        self._property_depricated_warning('gpgga')
        return self.get_gpgga()

    @property
    def gpgsa(self):
        self._property_depricated_warning('gpgsa')
        return self.get_gpgsa()

    @property
    def gpgsv(self):
        self._property_depricated_warning('gpgsv')
        return self.get_gpgsv()

    @property
    def gpgll(self):
        self._property_depricated_warning('gpgll')
        return self.get_gpgll()

    @property
    def gptxt(self):
        self._property_depricated_warning('gptxt')
        return self.get_gptxt()
    ####################################################################

    def get_gprmc(self):
        """Returns the latest GPRMC message.

        :rasies: DataInvalidError
        """
        pkt = self.get_nmea_pkt('GPRMC')
        gprmc_dict, checksum = gprmc_as_dict(pkt)
        if gprmc_dict['data_valid'] == "A":
            return gprmc_dict
        else:
            raise DataInvalidError("Indicated by data_valid field.")

    def get_gpvtg(self):
        """Returns the latest GPVTG message."""
        pkt = self.get_nmea_pkt('GPVTG')
        gpvtg_dict, checksum = gpvtg_as_dict(pkt)
        return gpvtg_dict

    def get_gpgga(self):
        """Returns the latest GPGGA message."""
        pkt = self.get_nmea_pkt('GPGGA')
        gpgga_dict, checksum = gpgga_as_dict(pkt)
        return gpgga_dict

    def get_gpgsa(self):
        """Returns the latest GPGSA message."""
        pkt = self.get_nmea_pkt('GPGSA')
        gpgsa_dict, checksum = gpgsa_as_dict(pkt)
        return gpgsa_dict

    def get_gpgsv(self):
        """Returns the latest GPGSV message."""
        pkt = self.get_nmea_pkt('GPGSV')
        gpgsv_dict, checksum = gpgsv_as_dict(pkt)
        return gpgsv_dict

    def get_gpgll(self):
        """Returns the latest GPGLL message.

        :rasies: DataInvalidError
        """
        pkt = self.get_nmea_pkt('GPGLL')
        gpgll_dict, checksum = gpgll_as_dict(pkt)
        if gpgll_dict['data_valid'] == "A":
            return gpgll_dict
        else:
            raise DataInvalidError("Indicated by data_valid field.")

    def get_gptxt(self):
        """Returns the latest GPTXT message."""
        pkt = self.get_nmea_pkt('GPTXT')
        gptxt_dict, checksum = gptxt_as_dict(pkt)
        return gptxt_dict

    def check_pmtk_ack(self):
        '''Waits for an validates a PMTK_ACK. Raises an exception if
        PMTK_ACK reports error.
        '''
        pkt = self.get_nmea_pkt('$PMTK001')
        ack_data = pkt.split('*').split(',')
        flag = int(ack_data[2])
        if flag == 0:
            raise PMTKACKError('Invalid packet')
        elif flag == 1:
            raise PMTKACKError('Unsupported packet type')
        elif flag == 2:
            raise PMTKACKError('Valid packet but action failed')
        elif flag == 3:
            return  # success!
        else:
            raise PMTKACKError('Unknown flag in ack.')

    def standby(self):
        '''Puts the GPS into standby mode.'''
        self.send_nmea_pkt(PMTK_STANDBY)
        self.check_pmtk_ack()

    def always_locate(self):
        '''Turns on AlwaysLocate(TM). Turn off with `set_periodic_normal`.'''
        self.send_nmea_pkt(PMTK_SET_PERIODIC_MODE_AUTO_LOCATE_STANDBY)
        self.check_pmtk_ack()

    def sleep(self):
        '''Puts the GPS into sleep mode. Wake with `set_periodic_normal`.'''
        self.send_nmea_pkt(PMTK_SET_PERIODIC_MODE_SLEEP)
        self.check_pmtk_ack()

    def set_periodic_normal(self):
        '''Sets the periodic mode to normal.'''
        self.send_nmea_pkt(PMTK_SET_PERIODIC_MODE_NORMAL)
        self.check_pmtk_ack()

    def locus_query(self):
        """Returns the status of the locus logger."""
        self.send_nmea_pkt(PMTK_LOCUS_QUERY_STATUS)
        pmtklog_dict, checksum = pmtklog_as_dict(self.get_nmea_pkt('PMTKLOG'))
        return pmtklog_dict

    def locus_erase(self):
        """Erases the internal log."""
        self.send_nmea_pkt(PMTK_LOCUS_ERASE_FLASH)

    def locus_start(self):
        """Starts the logger."""
        self.send_nmea_pkt(PMTK_LOCUS_START_LOGGER)

    def locus_stop(self):
        """Stops the logger."""
        self.send_nmea_pkt(PMTK_LOCUS_STOP_LOGGER)

    def locus_query_data(self, raw=False, num_attempts=5):
        """Returns a list of parsed LOCUS log data.

        :param raw: Return raw bytearray instead of list of dict's.
        :type raw: boolean
        :param num_attempts: Number of attempts to get raw data (it sometimes
                             fails)
        :type num_attempts: int
        :rasies: LOCUSQueryDataError
        """
        attempt = 0
        success = False
        while success == False and attempt < num_attempts:
            try:
                data = self._locus_query_data_raw()
            except NMEAPacketNotFoundError:
                attempt += 1
            else:
                success = True
        if not success:
            raise LOCUSQueryDataError(
                "Max number of attempts ({}) reached.".format(num_attempts))
        elif raw:
            return data
        else:
            return parse_locus_data(data)

    def _locus_query_data_raw(self):
        """Returns a byte array of the log data (you can parse this later).

        Example packets returned:


        Data: $PMTKLOX,1,0,0100010B,1F000000,0F000000,0000100B,00000000,
              00000000,00000003,FFFFFFFF,FFFFFFFF,FFFFFFFF,FFFFFFFF,
              FFFFFFFF,FFFFFFFF,FFFFFFFF,FFFFFFFF,00FC8C1C,0DE9E753,
              02A54356,42777508,C0A300C9,1CE9E753,02A14356,42397508,
              C0A30092*2E

        """
        locus_data_ptn_start = 'PMTKLOX,0'
        locus_data_ptn = 'PMTKLOX,1'
        locus_data_ptn_end = 'PMTKLOX,2'
        self.send_nmea_pkt(PMTK_Q_LOCUS_DATA_PARTIAL)

        # get the start packet (not that we do anything with it, the returned
        # number of packets doesn't even equal what this packet says it will!)
        pkt = self.get_nmea_pkt(locus_data_ptn_start)
        pkt, checksum = pkt.split('*') # data is already confirmed valid
        message_id, type, num_pkts = pkt.split(',')

        # get all the data packets until the end packet pattern if found
        databytes = bytearray()
        for i in range(int(num_pkts)):
            pkt = self.get_nmea_pkt(locus_data_ptn)
            pkt, checksum = pkt.split('*') # data is already confirmed valid
            pkt_list = pkt.split(',')
            # do some sanity checking
            message_id, lox_type, index = pkt_list[:3]
            # print("Hi", message_id, lox_type, index)
            assert message_id == '$PMTKLOX'
            assert lox_type == '1'
            assert int(index) == i
            # put the data into bytes
            for hexstr in pkt_list[3:]:
                databytes += hexstr2bytearray(hexstr)
        # end pkt
        pkt = self.get_nmea_pkt(locus_data_ptn_end)
        return databytes

    def get_nmea_pkt(self, pattern):
        """Returns the next valid NMEA string which contains the pattern
        provided. For example:

            >>> gps.get_nmea_pkt('GPRMC')
            '$GPRMC,013732.000,A,3150.7238,N,11711.7278,E,0.00,0.00,220413,,,A*68'

        """
        pattern_bytes = bytes(pattern, 'utf-8')
        while True:
            line = self.device_tx_rx.readline()
            # logging.debug("L80GPS:readline returned - "+str(line))
            if line == b'':
                raise NMEAPacketNotFoundError(
                    "Timed out before valid '{}'.".format(pattern))
            elif not l80gps_checksum_is_valid(line):
                continue
            elif pattern_bytes in line:
                return str(line, 'utf-8')

    def send_nmea_pkt(self, pkt):
        """Write pkt to the serial port."""
        self.device_tx_rx.write(bytes(pkt, 'utf-8'))


def parse_locus_data(data, format='basic'):
    """Returns the LOCUS data in a sensible structure according to the format."""
    # assuming basic format
    # utc (4), fix (1), latitude (4), longitude (4), altitude (2), checksum (1)
    # sample data
    data.reverse()
    parsed_data = []
    while True:
        try:
            data_bytes = [data.pop() for i in range(16)]
        except IndexError:
            return parsed_data
        else:
            utc = parse_long(data_bytes[:4])
            checksum = data_bytes[15]
            if not checksum_is_valid(data_bytes[:15], checksum):
                # invalid checksum, this datum is useless
                continue
            elif utc >= 0xffffffff:
                # data is empty, don't add to parsed_data
                continue
            else:
                parsed_data.append(
                    {'utc': datetime.datetime.fromtimestamp(utc),
                     'fix': data_bytes[4],
                     'latitude': parse_float(data_bytes[5:9]),
                     'longitude': parse_float(data_bytes[9:13]),
                     'altitude': parse_int(data_bytes[13:15]),
                     'checksum': checksum})


def gprmc_as_dict(gprmc_str):
    """Returns the GPRMC as a dictionary and the checksum.

        >>> gprmc_as_dict('$GPRMC,013732.000,A,3150.7238,N,11711.7278,E,0.00,0.00,220413,,,A*68')
        ({'message_id': 'GPRMC',
          'utc': 0.0,
          'data_valid': 'A',
          'latitude': 3150.7238,
          'ns': 0.0,
          'longitude': 0.1,
          'ew': 'A',
          'speed':,
          'cog':,
          'date':,
          'mag_var':,
          'eq':,
          'pos_mode':},
          0C)
    """
    gprmc, checksum = gprmc_str.split('*')
    message_id, utc, data_valid, latitude, ns, longitude, ew, speed, cog, \
        date, mag_var, eq, pos_mode = gprmc.split(',')
    utc = 0.0 if utc == '' else utc
    latitude = 0.0 if latitude == '' else latitude
    longitude = 0.0 if longitude == '' else longitude
    gprmc_dict = {'message_id': message_id,
                  'utc': float(utc),
                  'data_valid': data_valid,
                  'latitude': dm2d(float(latitude), ns),
                  'ns': ns,
                  'longitude': dm2d(float(longitude), ew),
                  'ew': ew,
                  'speed': speed,
                  'cog': cog,
                  'date': date,
                  'mag_var': mag_var,
                  'eq': eq,
                  'pos_mode': pos_mode}
    return (gprmc_dict, checksum)

def gpvtg_as_dict(gpvtg_str):
    """Returns the GPVTG as a dictionary and the checksum.

        >>> gpvtg_as_dict('$GPVTG,0.0,T,,M,0.0,N,0.1,K,A*0C')
        ({'message_id': 'GPVTG',
          'cogt': 0.0,
          't': 'A',
          'cogm': '',
          'speedn': 0.0,
          'speedk': 0.1,
          'pos_mode': 'A'},
          0C)
    """
    gpvtg, checksum = gpvtg_str.split('*')
    message_id, cogt, t, cogm, m, speedn, n, speedk, k, pos_mode = \
        gpvtg.split(',')
    gpvtg_dict = {'message_id': message_id,
                  'cogt': cogt,
                  'cogm': cogm,
                  'speedn': float(speedn),
                  'speedk': float(speedk),
                  'pos_mode': pos_mode}
    return (gpvtg_dict, checksum)

def gpgga_as_dict(gpgga_str):
    """Returns the GPGGA as a dictionary and the checksum.

    Returns latitude and longitude as degrees.

        >>> gpgga_as_dict('$GPGGA,015540.000,A,3150.68378,N,11711.93139,E,1,17,0.6,0051.6,M,0.0,M,,*58')
        ({'message_id': 'GPGGA',
          'utc': 015540.000,
          'latitude': 3150.68378,
          'ns': 'N',
          'longitude': 11711.93139,
          'ew': 'E',
          'fix': 1,
          'number_of_sv': 17,
          'hdop': 0.6,
          'altitude': 0051.6,
          'geoid_seperation': 0.0,
          'dgps_age': '',
          'dgps_station_id': ''},
          77)
    """
    gpgga, checksum = gpgga_str.split('*')
    print(gpgga_str)
    message_id, utc, latitude, ns, longitude, ew, fix, \
        number_of_sv, hdop, altitude, m, geoid_seperation, m, dgps_age, \
        dgps_station_id = gpgga.split(',')
    utc = 0.0 if utc == '' else utc
    latitude = 0.0 if latitude == '' else latitude
    longitude = 0.0 if longitude == '' else longitude
    gpgga_dict = {'message_id': message_id,
                  'utc': float(utc),
                  'latitude': dm2d(float(latitude), ns),
                  'ns': ns,
                  'longitude': dm2d(float(longitude), ew),
                  'ew': ew,
                  'fix': fix,
                  'number_of_sv': number_of_sv,
                  'hdop': hdop,
                  'altitude': altitude,
                  'geoid_seperation': geoid_seperation,
                  'dgps_age': dgps_age,
                  'dgps_station_id': dgps_station_id}
    return (gpgga_dict, checksum)


def gpgsa_as_dict(gpgsa_str):
    """Returns the GPGSA as a dictionary and the checksum.

        >>> gpgsa_as_dict('$GPGSA,A,3,14,06,16,31,23,,,,,,,,1.66,1.42,0.84*0F')
        ({'message_id': 'GPGSA',
          'mode': 'A',
          'fix': 3,
          'satellites_on_channel': [14, 06, 16, 31, 23, 0, 0, 0, 0, 0, 0, 0],
          'pdop': 1.66,
          'hdop': 1.42,
          'vdop': 0.84},
          77)
    """
    gpgsa, checksum = gpgsa_str[1:].split("*")  # remove `$` split *
    gpgsa_data = gpgsa.split(',')
    message_id, mode, fix = gpgsa_data[:3]
    satellites_on_ch = gpgsa_data[3:-3]
    pdop, hdop, vdop = gpgsa_data[-3:]
    # set all blank channels to 0
    satellites_on_ch = map(lambda s: 0 if s == '' else s, satellites_on_ch)
    gpgsa_dict = {'message_id': message_id,
                  'mode': mode,
                  'fix': fix,
                  'satellites_on_channel': satellites_on_ch,
                  'pdop': pdop,
                  'hdop': hdop,
                  'vdop': vdop}
    return (gpgsa_dict, checksum)

def gpgsv_as_dict(gpgsv_str):
    """Returns the GPGSV as a dictionary and the checksum.

        >>> gpgsv_as_dict('$GPGSV,3,1,12,01,05,060,18,02,17,259,43,04,56,287,28,09,08,277,28*77')
        ({'message_id': 'GPGSV',
          'num_messages': 3,
          'sequence_num': 1,
          'satellites_in_view': 12,
          'satellite': [{'id': 01,
                         'elevation': 05,
                         'azimuth': 060,
                         'snr': 18},
                        {'id': 02,
                         'elevation': 17,
                         'azimuth': 259,
                         'snr': 43},
                        {'id': 04,
                         'elevation': 56,
                         'azimuth': 287,
                         'snr': 28},
                        {'id': 09,
                         'elevation': 08,
                         'azimuth': 277,
                         'snr': 28}]},
          77)
    """
    # TODO varaible length string depending on number of satellites
    gpgsv, checksum = gpgsv_str[1:].split("*")  # remove `$` split *
    message_id, num_messages, sequence_num, satellites_in_view, \
        satellite_1_id, satellite_1_elevation, satellite_1_azimuth, \
        satellite_1_snr, satellite_2_id, satellite_2_elevation, \
        satellite_2_azimuth, satellite_2_snr, satellite_3_id, \
        satellite_3_elevation, satellite_3_azimuth, satellite_3_snr, \
        satellite_4_id, satellite_4_elevation, satellite_4_azimuth, \
        satellite_4_snr = gpgsv.split(",")
    gpgsv_dict = {'message_id': message_id,
                  'num_messages': num_messages,
                  'sequence_num': sequence_num,
                  'satellites_in_view': satellites_in_view,
                  'satellite': [{'id': satellite_1_id,
                                 'elevation': satellite_1_elevation,
                                 'azimuth': satellite_1_azimuth,
                                 'snr': satellite_1_snr},
                                {'id': satellite_2_id,
                                 'elevation': satellite_2_elevation,
                                 'azimuth': satellite_2_azimuth,
                                 'snr': satellite_2_snr},
                                {'id': satellite_3_id,
                                 'elevation': satellite_3_elevation,
                                 'azimuth': satellite_3_azimuth,
                                 'snr': satellite_3_snr},
                                {'id': satellite_4_id,
                                 'elevation': satellite_4_elevation,
                                 'azimuth': satellite_4_azimuth,
                                 'snr': satellite_4_snr}]}
    return (gpgsv_dict, checksum)


def gpgll_as_dict(gpgll_str):
    """Returns the GPGLL as a dictionary and the checksum.

        >>> gpgll_as_dict('$GPGLL,3110.2908,N,12123.2348,E,041139.000,A,A*59')
        ({'message_id': GPGLL,
          'latitude': 3110.2908,
          'ns': 'N',
          'longitude': 12123.2348,
          'ew': 'E',
          'utc': 041139.000,
          'data_valid': 'A',
          'pos_mode': 'A'},
         59)

    """
    gpgll, checksum = gpgll_str[1:].split("*")  # remove `$` split *
    message_id, latitude, ns, longitude, ew, utc, data_valid, pos_mode = \
        gpgll.split(",")
    latitude = 0.0 if latitude == '' else latitude
    longitude = 0.0 if longitude == '' else longitude
    utc = 0.0 if utc == '' else utc
    gpgll_dict = ({"message_id": message_id,
                   "latitude": dm2d(float(latitude), ns),
                   "ns": ns,
                   "longitude": dm2d(float(longitude), ew),
                   "ew": ew,
                   "utc": float(utc),
                   "data_valid": data_valid,
                   "pos_mode": pos_mode},
                  checksum)
    # logging.debug("L80GPS:Converting '{}'\ninto: {}".format(gpgll_str, gpgll_dict))
    return gpgll_dict


def gptxt_as_dict(self):
    """
    GPTXT Message ID
    XX Total number of messages in this transmission. (01~99)
    YY Message number in this transmission. (01~99)
    ZZ
    Severity of the message
    ‘00’= ERROR
    ‘01’= WARNING
    ‘02’= NOTICE
    ‘07’= USER
    Text messasage
    """
    # TODO fix this
    pass


def pmtklog_as_dict(pmtklog_str):
    """Returns the PMTKLOG as a dictionary and the checksum.

        >>> pmtklog_as_dict('$PMTKLOG,456,0,11,31,2,0,0,0,3769,46*48')
        ({'message_id': 'PMTKLOG',
          'serial': 456,
          'type': 0,
          'mode': 11,
          'content': 31,
          'interval': 2,
          'distance': 0,
          'speed': 0,
          'status': 0,
          'number': 3769,
          'percent': 46},
         48)

    """
    pmtklog, checksum = pmtklog_str[1:].split('*')  # remove `$` split *
    message_id, serial, type, mode, content, interval, distance, speed,\
        status, number, percent = pmtklog.split(',')
    pmtklog_dict = ({'message_id': 'PMTKLOG',
                     'serial': serial,
                     'type': type,
                     'mode': int(mode, 16),
                     'content': content,
                     'interval': interval,
                     'distance': distance,
                     'speed': speed,
                     'status': status,
                     'number': number,
                     'percent': percent},
                    checksum)
    return pmtklog_dict


def l80gps_checksum_is_valid(gps_str):
    """Returns True if the checksum is valid in an GPS L80 protocol line.

        !!!! This method assumes gps_str is a byte string. !!!!

    """
    if gps_str[0] != ord(b'$'):
        return False
    try:
        gpgll, checksum = gps_str[1:].split(b'*')  # remove `$` split *
    except:
        # logging.debug("L80GPS:Invalid GPS str")
        # logging.debug(gps_str)
        return False
    else:
      return checksum_is_valid(gpgll, int(checksum, 16))


def checksum_is_valid(data_bytes, checksum):
    """Returns True is the logical OR of each consecutive databyte is
    the same as the checksum.
    """
    check = 0
    for b in data_bytes:
      check ^= b
    return check == checksum


def hexstr2bytearray(s):
    """Converts a string of hex characters to bytes.

        'DEADBEEF'

    becomes

        bytearray(b'\\\\xde\\\\xad\\\\xbe\\\\xef')

    """
    # split the string into a list of strings, each two characters long
    # then turn each two character string into an int (base 16) and put
    # that array into a bytearray
    n = 2
    return bytearray([int(s[i:i+n], 16) for i in range(0, len(s), n)])


def parse_float(bytes):
    """Converts four bytes into a float."""
    longValue = parse_long(bytes)
    exponent = ((longValue >> 23) & 0xff) # float
    exponent -= 127.0
    exponent = pow(2,exponent)
    mantissa = (longValue & 0x7fffff)
    mantissa = 1.0 + (mantissa/8388607.0)
    floatValue = mantissa * exponent
    if ((longValue & 0x80000000) == 0x80000000):
        floatValue = -floatValue
    return floatValue


def parse_long(bytes):
    """Converts four bytes into a long integer."""
    assert len(bytes) == 4
    return ((0xFF & bytes[3]) << 24 |
            (0xFF & bytes[2]) << 16 |
            (0xFF & bytes[1]) << 8 |
            (0xFF & bytes[0]))


def parse_int(bytes):
    """Converts two bytes into an interger."""
    assert len(bytes) == 2
    number = ((0xFF & bytes[1]) << 8 | (0xFF & bytes[0]))
    return number


def dm2d(degrees_and_minutes, direction):
    """Converts dddmm.mmmm to ddd.dddd...
    direction's 's' and 'w' are negative.
    """
    degrees = int(degrees_and_minutes / 100)
    minutes = degrees_and_minutes % 100
    degrees += (minutes / 60)
    if direction.lower() == 's' or direction.lower() == 'w':
        return -1 * degrees
    else:
        return degrees
