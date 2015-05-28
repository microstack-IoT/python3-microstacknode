import math
import unittest
from microstacknode.hardware.accelerometer.lsm9ds0 import LSM9DS0


class TestLSM9DS0(unittest.TestCase):

    def test_whoami(self):
        with LSM9DS0(1) as l:
            l.verify_whoami()

    def test_temperature(self):
        with LSM9DS0(1) as l:
            l.enable_temperature()
            self.assertTrue(l.get_temperature() > 0)

    def test_accelerometer(self):
        with LSM9DS0(1) as l:
            l.setup_accelerometer()
            print("Accelerometer: {}".format(l.get_accelerometer()))
            print("Accelerometer (raw): {}".format(
                l.get_accelerometer(raw=True)))

    def test_magnetometer(self):
        with LSM9DS0(1) as l:
            l.setup_magnetometer()
            print("Magnetometer (raw): {}".format(
                l.get_magnetometer(raw=True)))
            m = l.get_magnetometer()
            print("Magnetometer: {}".format(m))

    def test_gyroscope(self):
        with LSM9DS0(1) as l:
            l.setup_gyroscope()
            print("Gyroscope (raw): {}".format(
                l.get_gyroscope(raw=True)))
            print("Gyroscope: {}".format(l.get_gyroscope()))


if __name__ == "__main__":
    unittest.main()
