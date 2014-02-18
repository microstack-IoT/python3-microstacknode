# http://www.gsm-rainbow.ru/sites/default/files/
# l80_gps_protocol_specification_v1.0.pdf
import threading
import logging
logging.basicConfig(level=logging.DEBUG)


class L80GPS(threading.Thread):
    """Thread that reads a stream of L80 GPS protocol lines and stores the
    information."""

    def __init__(self, input_stream):
        super().__init__()
        self.input_stream = input_stream
        self._running = False
        self._gpgll = None

    def run(self):
        self._running = True
        for line in self.input_stream:
            if ("GPGLL" in line
                    and l80gps_checksum_is_valid(line)
                    and gpgll_as_dict(line)[0]['data_valid'] == "A"):
                        self._gpgll = line
                        logging.debug("L80GPS:Setting GPGLL to {}"
                                      .format(line))
            if self._running is False:
                break

    def stop(self):
        self._running = False

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
