import time
import unittest
from microstacknode.hardware.accelerometer.lsm9ds0 import LSM9DS0


class TestLSM9DS0Gyro(unittest.TestCase):

    def test_gyroscope(self):
        with LSM9DS0(1) as l:
            l.setup_gyroscope()
            while True:
                print("Gyroscope: {}".format(l.get_gyroscope()))
                time.sleep(0.1)


if __name__ == "__main__":
    unittest.main()
