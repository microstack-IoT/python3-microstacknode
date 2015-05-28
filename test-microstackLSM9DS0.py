import unittest
from microstacknode.hardware.accelerometer.lsm9ds0 import LSM9DS0


class TestLSM9DS0(unittest.TestCase):

    def test_temperature(self):
        with LSM9DS0(1) as l:
            l.enable_temperature()
            self.assertTrue(l.get_temperature() > 0)

    def test_accelerometer(self):
        with LSM9DS0(1) as l:
            l.setup_accelerometer()
            print(l.get_accelerometer())
            print(l.get_accelerometer(raw=True))



if __name__ == "__main__":
    unittest.main()
