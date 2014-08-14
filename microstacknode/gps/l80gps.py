# http://www.gsm-rainbow.ru/sites/default/files/
# l80_gps_protocol_specification_v1.0.pdf
import threading
import subprocess
import logging
import time
logging.basicConfig(level=logging.DEBUG)


PMTK_LOCUS_QUERY_STATUS = "$PMTK183*38\r\n"
PMTK_LOCUS_ERASE_FLASH = "$PMTK184,1*22\r\n"
PMTK_LOCUS_STOP_LOGGER  ="$PMTK185,1*23\r\n" # start/stop
PMTK_Q_LOCUS_DATA = "$PMTK622,1*29\r\n"


class L80GPS(threading.Thread):
    """Thread that reads a stream of L80 GPS protocol lines and stores the
    information."""

    def __init__(self, device="/dev/ttyAMA0"):
        super().__init__()
        self.device = device
        self.device_tx = open(self.device, "w")
        self.device_rx = open(self.device, "r")
        self._running = False
        self._gpgll = None
        self._pmtk_response = None
        self._pmtk_rep_buf = None

    def run(self):
        self._running = True
        for line in self.device_rx:
            if ("GPGLL" in line
                    and l80gps_checksum_is_valid(line)
                    and gpgll_as_dict(line)[0]['data_valid'] == "A"):
                        self._gpgll = line
                        logging.debug("L80GPS:Setting GPGLL to {}"
                                      .format(line))
                        subprocess.call(['sudo su -c "echo 1 > '
                                         '/sys/class/leds/led0/brightness"'],
                                        shell=True)
                        time.sleep(0.3)
                        subprocess.call(['sudo su -c "echo 0 > '
                                         '/sys/class/leds/led0/brightness"'],
                                        shell=True)
                        time.sleep(0.2)

            elif "$PMTKLOG" in line:
                logging.debug("L80GPS:Found PMTKLOG, adding to response:{}".format(
                    line))
                if self._pmtk_rep_buf is None:
                    self._pmtk_rep_buf = line
                else:
                    self._pmtk_rep_buf += line

            elif "$PMTK001" in line:
                logging.debug("L80GPS:Found PMTKACK, dealing with response")
                logging.debug("L80GPS:self._pmtk_rep_buf is " + self._pmtk_rep_buf)
                buf = self._pmtk_rep_buf
                self._pmtk_rep_buf = None
                if self._pmtk_response is not None:
                    self._pmtk_response(buf)

            if self._running is False:
                break

    def stop(self):
        self._running = False

    def _pmtk_response(self, response):
        """Acts on the PMTK response."""
        logging.debug("L80GPS:Acting on response (Making callback)")
        if self._pmtk_callback:
            logging.debug("L80GPS:There is a callback")
            self._pmtk_callback(response)

    def locus_query(self, callback):
        logging.debug("L80GPS:locus query")
        self._pmtk_callback = callback
        self.device_tx.write(PMTK_LOCUS_QUERY_STATUS)

    def locus_erase(self):
        logging.debug("L80GPS:locus erase")
        self._pmtk_callback = None
        self.device_tx.write(PMTK_LOCUS_ERASE_FLASH)

    def locus_start_stop(self):
        logging.debug("L80GPS:locus start_stop")
        self._pmtk_callback = None
        self.device_tx.write(PMTK_LOCUS_STOP_LOGGER)

    def locus_query_data(self, callback):
        logging.debug("L80GPS:locus query_data")
        self._pmtk_callback = callback
        self.device_tx.write(PMTK_LOCUS_QUERY_STATUS)

    @property
    def gpgll(self):
        if self._gpgll is None:
            return "$GPGLL,3110.2908,N,12123.2348,E,041139.000,A,A*59"
        else:
            return self._gpgll


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
    return ({"message_id": message_id,
             "latitude": float(latitude),
             "ns": ns,
             "longitude": float(longitude),
             "ew": ew,
             "utc": float(utc),
             "data_valid": data_valid,
             "pos_mode": pos_mode},
            checksum)


def l80gps_checksum_is_valid(gps_str):
    """Returns True if the checksum is valid in an GPS L80 protocol packet."""
    gpgll, checksum = gps_str[1:].split("*")  # remove `$` split *
    check = 0
    for char in gpgll:
        check ^= ord(char)
    return check == int(checksum, 16)  # checksum is hex string
