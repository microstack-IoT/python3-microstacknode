#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknode.core


class TestMicrostackNode(unittest.TestCase):

    def test_node(self):
        microstacknode.core.start()


if __name__ == "__main__":
    unittest.main()
