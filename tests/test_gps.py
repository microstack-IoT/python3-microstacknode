#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknode.gps.l80gps


class TestL80GPS(unittest.TestCase):
    def setUp(self):
        self.gps = microstacknode.gps.l80gps.L80GPS()
        self.gps.start()

    def test_locus_query(self):
        def print_response(r):
            print(r)
        self.gps.locus_query(print_response)

if __name__ == "__main__":
    unittest.main()
