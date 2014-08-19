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
PMTK_LOCUS_STOP_LOGGER = '$PMTK185,1*23\r\n' # start/sto
PMTK_Q_LOCUS_DATA_FULL = '$PMTK622,0*29\r\n'
PMTK_Q_LOCUS_DATA_PARTIAL = '$PMTK622,1*29\r\n'


class NMEAPacketNotFoundError(Exception):
    pass


class GPGLLInvalidError(Exception):
    pass


class L80GPS(object):
    """Thread that reads a stream of L80 GPS protocol lines and stores the
    information.
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
    def gpgll(self):
        pkt = self.get_nmea_pkt('GPGLL')
        gpgll_dict, checksum = gpgll_as_dict(pkt)
        if gpgll_dict['data_valid'] == "A":
            return gpgll_dict
        else:
            raise GPGLLInvalidError("Indicated by data_valid field.")

    def locus_query(self):
        """Returns the status of the locus logger."""
        self.send_nmea_pkt(PMTK_LOCUS_QUERY_STATUS)
        pmtklog_dict, checksum = pmtklog_as_dict(self.get_nmea_pkt('PMTKLOG'))
        return pmtklog_dict

    def locus_erase(self):
        """Erases the internal log."""
        self.send_nmea_pkt(PMTK_LOCUS_ERASE_FLASH)

    def locus_start_stop(self):
        """Starts or stops the logger."""
        self.send_nmea_pkt(PMTK_LOCUS_STOP_LOGGER)

    def locus_query_data(self):
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

    def parse_locus_data(self, data, format='basic'):
        """Returns the data in a sensible structure according to the format."""
        # assuming basic format
        # utc (4)
        # fix (1)
        # lat (4)
        # lon (4)
        # height (2)
        # checksum (1)
        # DEBUGING
        # sample data: bytearray(b'\x01\x00\x01\x0b\x1f\x00\x00\x00\x0f\x00\x00\x00\x00\x00\x10\x0b')
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
                        {'utc': datetime.date.fromtimestamp(utc),
                         'fix': data_bytes[4],
                         'lat': parse_float(data_bytes[5:9]),
                         'lon': parse_float(data_bytes[9:13]),
                         'height': parse_int(data_bytes[13:15]),
                         'checksum': checksum})


    def get_nmea_pkt(self, pattern):
        """Returns the next valid NMEA which contains the pattern provided.
        For example:

            gps.get_nmea_pkt('GPRMC')

        Returns

            $GPRMC,013732.000,A,3150.7238,N,11711.7278,E,0.00,0.00,220413,,,A*68

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


def gpgll_as_dict(gpgll_str):
    """Returns the GPGLL as a dictionary and the checksum.

         in: $GPGLL,3110.2908,N,12123.2348,E,041139.000,A,A*59
        out: ({"message_id": GPGLL,
               "latitude": 3110.2908,
               "ns": "N",
               "longitude": 12123.2348,
               "ew": "E",
               "utc": 041139.000,
               "data_valid": "A",
               "pos_mode": "A"},
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


def pmtklog_as_dict(pmtklog_str):
    """Returns the PMTKLOG as a dictionary and the checksum.

         in: $PMTKLOG,456,0,11,31,2,0,0,0,3769,46*48
        out: ({'message_id': 'PMTKLOG',
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
                     'mode': mode,
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

        bytearray(b'\xde\xad\xbe\xef')

    """
    # split the string into a list of strings, each two characters long
    # then turn each two character string into an int (base 16) and put
    # that array into a bytearray
    n = 2
    return bytearray([int(s[i:i+n], 16) for i in range(0, len(s), n)])


def parse_float(bytes):
    longValue = parse_long(bytes)

    # borrowed code from https://github.com/douggilliland/Dougs-Arduino-Stuff/blob/master/Host%20code/parseLOCUS/parseLOCUS.cpp
    exponent = ((longValue >> 23) & 0xff) # float
    exponent -= 127.0
    exponent = pow(2,exponent)
    mantissa = (longValue & 0x7fffff)
    mantissa = 1.0 + (mantissa/8388607.0)
    floatValue = mantissa * exponent
    if ((longValue & 0x80000000) == 0x80000000):
        floatValue = -floatValue


def parse_long(bytes):
    if len(bytes) != 4:
        print >> sys.stderr, "WARNING: expecting 4 bytes got %s" % bytes
    number = ((0xFF & bytes[3]) << 24) | ((0xFF & bytes[2]) << 16) | ((0xFF & bytes[1]) << 8) | (0xFF & bytes[0])
    return number


def parse_int(bytes):
    if len(bytes) != 2:
        print >> sys.stderr, "WARNING: expecting 2 bytes got %s" % bytes
    number = ((0xFF & bytes[1]) << 8) | (0xFF & bytes[0])
    return number