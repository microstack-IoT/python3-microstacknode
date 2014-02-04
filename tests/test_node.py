#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknode.core
import argparse


# server_address = None
# node_address = None


class TestMicrostackNode(unittest.TestCase):

    def test_node(self):
        # global server_address
        # global node_address
        # if node_address is not None and server_address is not None:
        #     node = microstacknode.core.MicrostackNode(int(node_address, 16),
        #                                               int(server_address, 16))
        # else:
        node = microstacknode.core.MicrostackNode()
        node.handshake()

        node.run()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-sa', '--server-address',
    #                     help="Server address.",
    #                     type=str)
    # parser.add_argument('-na', '--node-address',
    #                     help="This nodes address.",
    #                     type=str)
    # args = parser.parse_args()

    # if args.server_address and args.node_address:
    #     global server_address
    #     global node_address
    #     server_address = args.server_address
    #     node_address = args.node_address

    unittest.main()
