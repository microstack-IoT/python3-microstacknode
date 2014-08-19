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

    # @unittest.skip
    # def test_locus_query(self):
    #     self.gps.locus_query()

    # @unittest.skip
    # def test_locus_erase(self):
    #     pass
    #     # self.gps.locus_erase()

    # @unittest.skip
    # def test_locus_start_stop(self):
    #     pass
    #     # self.gps.locus_start_stop()

    # @unittest.skip
    # def test_locus_query_data(self):
    #     self.gps.locus_query_data()

    def test_locus_query_data_and_parsing(self):
        print("Starting locus")
        self.gps.locus_start_stop()

        print("Getting data.")
        attempt = 0
        success = False
        while success == False and attempt < 5:
            try:
                data = self.gps.locus_query_data()
            except microstacknode.gps.l80gps.NMEAPacketNotFoundError:
                print("Getting data failed, trying again.")
                attempt += 1
            else:
                success = True
        self.assertTrue(success)
        print(data)

        print("=================\nParsing data.\n=================")
        for d in self.gps.parse_locus_data(data):
            print(d)

        print("Stopping locus")
        self.gps.locus_start_stop()


if __name__ == "__main__":
    unittest.main()
