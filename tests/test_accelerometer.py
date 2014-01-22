#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknode.accelerometer.mma8452q


class TestMMA8452Q(unittest.TestCase):
    def setUp(self):
        self.accelerometer = microstacknode.accelerometer.mma8452q.MMA8452Q()
        self.accelerometer.init()

    def test_MMA8452Q(self):
        try:
            while True:
                # x, y, z = self.accelerometer.get_xyz(raw=True, res12=False)
                # print(" 8-bit raw X: {:}, Y: {:}, Z: {:}".format(bin(x),
                #                                                  bin(y),
                #                                                  bin(z)))
                x, y, z = self.accelerometer.get_xyz(res12=False)
                print(" 8-bit X: {:.12}, Y: {:.12}, Z: {:.12}".format(x, y, z))
                # x, y, z = self.accelerometer.get_xyz()
                # print("12-bit X: {:.12}, Y: {:.12}, Z: {:.12}".format(x, y, z))
                print()
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    unittest.main()
