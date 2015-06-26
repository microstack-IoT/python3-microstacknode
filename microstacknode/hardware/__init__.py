import logging
import serial
from microstacknode.hardware.gps.l80gps import L80GPS
from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q


# logging.basicConfig(level=logging.DEBUG)


class MicrostackHardwareError(Exception):
    pass

class HardwareNotFoundError(MicrostackHardwareError):
    pass

class InitError(MicrostackHardwareError):
    pass


class MicrostackPeripheral(object):

    def init(self):
        pass


class MicrostackL80GPS(L80GPS, MicrostackPeripheral):

    def __init__(self, device="/dev/ttyAMA0"):
        try:
            super().__init__(device)
        except serial.serialutil.SerialException as e:
          raise InitError(str(e))


class MicrostackHardwareManager(object):

    ALL_GPS = (L80GPS)
    ALL_ACCELEROMETER = (MMA8452Q)

    def __init__(self):
        self.accelerometer_index = None
        self.gps_index = None
        self.init_device()
        self.init_peripherals()

    def init_device(self):
        logging.debug("Initialising the device.")

    def init_peripherals(self):
        # YOU ARE HERE
        logging.debug("Initialising peripherals.")
        self.peripherals = list()
        self.peripherals.extend(
            self.get_peripheral(self.ALL_ACCELEROMETER, "accelerometer"))

    def get_accelerometer(self):
        """Returns the first available Accelerometer."""
        return self.peripherals[self.accelerometer_index]

    def get_gps(self):
        """Returns the first available GPS."""
        self.get_peripheral(self.ALL_GPS, "GPS")

    def get_peripheral(self, hw_classes, hw_text):
        """Returns the first available hardware."""
        for c in hw_classes:
            try:
                return c()
            except InitError:
                continue
        else:
            raise HardwareNotFoundError(
                "Could not find available {}".format(hw_text))
