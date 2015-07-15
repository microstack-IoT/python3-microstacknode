#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknode.hardware.accelerometer.mma8452q


class TestMMA8452Q(unittest.TestCase):

    # def test_with(self):

    def test_MMA8452Q(self):
        self.accelerometer = microstacknode.hardware.accelerometer.mma8452q.MMA8452Q()
        self.accelerometer.init()
        try:
            while True:
                x, y, z = self.accelerometer.get_xyz(res12=False)
                x = "X:{:.6}".format(x)
                y = "Y:{:.6}".format(y)
                z = "Z:{:.6}".format(z)
                print(" 8-bit {:12}, {:12}, {:12}".format(x, y, z))
                # print()
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    unittest.main()
