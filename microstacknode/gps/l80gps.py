# http://www.gsm-rainbow.ru/sites/default/files/
# l80_gps_protocol_specification_v1.0.pdf
import threading
import subprocess
import logging
import time
import serial
import io
import datetime
logging.basicConfig(level=logging.DEBUG)


PMTK_LOCUS_QUERY_STATUS = '$PMTK183*38\r\n'
PMTK_LOCUS_ERASE_FLASH = '$PMTK184,1*22\r\n'
PMTK_LOCUS_STOP_LOGGER = '$PMTK185,1*23\r\n'
PMTK_LOCUS_START_LOGGER = '$PMTK185,0*22\r\n'
PMTK_Q_LOCUS_DATA_FULL = '$PMTK622,0*28\r\n'
PMTK_Q_LOCUS_DATA_PARTIAL = '$PMTK622,1*29\r\n'


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

    def __init__(self, device="/dev/ttyAMA0"):
        super().__init__()
        self.device_tx_rx = serial.Serial(device,
                                          baudrate=9600,
                                          bytesize=8,
                                          parity='N',
                                          stopbits=1,
                                          timeout=0.5,
                                          rtscts=0)

    @property
    def gprmc(self):
        """Returns the latest GPRMC message.

        :rasies: DataInvalidError
        """
        pkt = self.get_nmea_pkt('GPRMC')
        gprmc_dict, checksum = gprmc_as_dict(pkt)
        if gprmc_dict['data_valid'] == "A":
            return gprmc_dict
        else:
            raise DataInvalidError("Indicated by data_valid field.")

    @property
    def gpvtg(self):
        """Returns the latest GPVTG message."""
        pkt = self.get_nmea_pkt('GPVTG')
        gpvtg_dict, checksum = gpvtg_as_dict(pkt)
        return gpvtg_dict

    @property
    def gpgga(self):
        """Returns the latest GPGGA message.

        :rasies: DataInvalidError
        """
        pkt = self.get_nmea_pkt('GPGGA')
        gpgga_dict, checksum = gprmc_as_dict(pkt)
        if gpgga_dict['data_valid'] == "A":
            return gpgga_dict
        else:
            raise DataInvalidError("Indicated by data_valid field.")

    @property
    def gpgsa(self):
        """Returns the latest GPGSA message."""
        pkt = self.get_nmea_pkt('GPGSA')
        gpgsa_dict, checksum = gprmc_as_dict(pkt)
        return gpgsa_dict

    @property
    def gpgsv(self):
        """Returns the latest GPGSV message."""
        pkt = self.get_nmea_pkt('GPGSV')
        gpgsv_dict, checksum = gprmc_as_dict(pkt)
        return gpgsv_dict

    @property
    def gpgll(self):
        """Returns the latest GPGLL message.

        :rasies: DataInvalidError
        """
        pkt = self.get_nmea_pkt('GPGLL')
        gpgll_dict, checksum = gpgll_as_dict(pkt)
        if gpgll_dict['data_valid'] == "A":
            return gpgll_dict
        else:
            raise DataInvalidError("Indicated by data_valid field.")

    @property
    def gptxt(self):
        """Returns the latest GPTXT message."""
        pkt = self.get_nmea_pkt('GPTXT')
        gptxt_dict, checksum = gprmc_as_dict(pkt)
        return gptxt_dict

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


def gprmc_as_dict(pkt):
"""
GPRMC Message ID
UTC time Time in format ‘hhmmss.sss’
Data valid
‘V’ =Invalid
‘A’ = Valid
Latitude Latitude in format ‘ddmm.mmmm’ (degree and minutes)
N/S
‘N’ = North
‘S’ = South
Longitude Longitude in format ‘dddmm.mmmm’ (degree and minutes)
E/W
‘E’ = East
‘W’ = West
Speed Speed over ground in knots
COG Course over ground in degree
Date Date in format ‘ddmmyyyy’
Magnetic variation Magnetic variation in degree, not being output
E/W Magnetic variation E/W indicator, not being output
Positioning mode
‘N’ = No fix
‘A’ = Autonomous GNSS fix
‘D’ = Differential GNSS fix
"""

def gpvtg_as_dict(self):
"""
GPVTG Message ID
COG(T) Course over ground (true) in degree
T Fixed field, true
COG(M) Course over ground (magnetic), not being output
M Fixed field, magnetic
Speed Speed over ground in knots
N Fixed field, knots
Speed Speed over ground in km/h
k Fixed field, km/h
Positionin
"""

def gpgga_as_dict(self):
"""
UTC time Time in format ‘hhmmss.sss’
Data valid
‘V’ =Invalid
‘A’ = Valid
Latitude Latitude in format ‘ddmm.mmmm’ (degree and minutes)
N/S
‘N’ = North
‘S’ = South
Longitude Longitude in format ‘dddmm.mmmm’ (degree and minutes)
E/W
‘E’ = East
‘W’ = West
Fix status
‘0’ =Invalid
‘1’ = GNSS fix
‘2’ = DGPS fix
Number of SV Number of satellites being used (0 ~ 12)
HDOP Horizontal Dilution Of Precision
Altitude Altitude in meters according to WGS84 ellipsoid
M Fixed field, meter
GeoID separation Height of GeoID (mean sea level) above WGS84 ellipsoid, meter
M Fixed field, meter
DGPS age Age of DGPS data in seconds, empty if DGPS is not used
DGPS station ID DGPS station ID, empty if DGPS is not used
"""


def gpgsa_as_dict(self):
"""
Mode
Auto selection of 2D or 3D fix
‘M’ = Manual, forced to switch 2D/3D mode
‘A’ = Allowed to automatically switch 2D/3D mode
Fix status
‘1’ = No fix
‘2’ = 2D fix
‘3’ = 3D fix
Satellite used 1 Satellite used on channel 1
Satellite used 2 Satellite used on channel 2
Satellite used 3 Satellite used on channel 3
Satellite used 4 Satellite used on channel 4
Satellite used 5 Satellite used on channel 5
Satellite used 6 Satellite used on channel 6
Satellite used 7 Satellite used on channel 7
Satellite used 8 Satellite used on channel 8
Satellite used 9 Satellite used on channel 9
Satellite used 10 Satellite used on channel 10
Satellite used 11 Satellite used on channel 11
Satellite used 12 Satellite used on channel 12
PDOP Position Dilution Of Precision
HDOP Horizontal Dilution Of Precision
VDOP Vertical Dilution Of Precision
"""

def gpgsv_as_dict(self):
    """Returns the GPGSV as a dictionary and the checksum.

        >>> gpgsv_as_dict('$GPGSV,3,1,12,01,05,060,18,02,17,259,43,04,56,287,28,09,08,277,28*77')
        ({'message_id': 'GPGSV',
          'num_messages': 3,
          'sequence_num': 1,
          'satellites_in_view': 12,
          'satellite_1_id': 01,
          'satellite_1_elevation': 05,
          'satellite_1_azimuth': 060,
          'satellite_1_snr': 18,
          'satellite_2_id': 02,
          'satellite_2_elevation':17,
          'satellite_2_azimuth':259,
          'satellite_2_snr':43,
          'satellite_3_id':04,
          'satellite_3_elevation':56,
          'satellite_3_azimuth':287,
          'satellite_3_snr':28,
          'satellite_4_id':09,
          'satellite_4_elevation':08,
          'satellite_4_azimuth':277,
          'satellite_4_snr': 28},
          77)
    """
    gpgsv, checksum = gpgsv_str[1:].split("*")  # remove `$` split *
    message_id, num_messages, sequence_num, satellites_in_view, \
        satellite_1_id, satellite_1_elevation, satellite_1_azimuth, \
        satellite_1_snr, satellite_2_id, satellite_2_elevation, \
        satellite_2_azimuth, satellite_2_snr, satellite_3_id, \
        satellite_3_elevation, satellite_3_azimuth, satellite_3_snr, \
        satellite_4_id, satellite_4_elevation, satellite_4_azimuth, \
        satellite_4_snr = gpgsv.split(",")
    latitude = 0.0 if latitude == '' else latitude
    longitude = 0.0 if longitude == '' else longitude
    utc = 0.0 if utc == '' else utc
    gpgsv_dict = {'message_id': message_id,
                  'num_messages': num_messages,
                  'sequence_num': sequence_num,
                  'satellites_in_view': satellites_in_view,
                  'satellite_1_id': satellite_1_id,
                  'satellite_1_elevation': satellite_1_elevation,
                  'satellite_1_azimuth': satellite_1_azimuth,
                  'satellite_1_snr': satellite_1_snr,
                  'satellite_2_id': satellite_2_id,
                  'satellite_2_elevation':satellite_2_elevation,
                  'satellite_2_azimuth':satellite_2_azimuth,
                  'satellite_2_snr':satellite_2_snr,
                  'satellite_3_id':satellite_3_id,
                  'satellite_3_elevation':satellite_3_elevation,
                  'satellite_3_azimuth':satellite_3_azimuth,
                  'satellite_3_snr':satellite_3_snr,
                  'satellite_4_id':satellite_4_id,
                  'satellite_4_elevation':satellite_4_elevation,
                  'satellite_4_azimuth':satellite_4_azimuth,
                  'satellite_4_snr': satellite_4_snr}
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
                   "latitude": float(latitude),
                   "ns": ns,
                   "longitude": float(longitude),
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
