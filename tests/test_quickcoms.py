#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknetwork.radios
import microstacknetwork.radios.nrf24l01
import microstacknetwork.packets
from microstacknetwork.handshake import HandshakeError


BEACON_ADDRESS = 0x1234567890


class TestMicrostackNode(unittest.TestCase):

    def test_quick_hello(self):
        radio = microstacknetwork.radios.nrf24l01.NRF24L01()
        radio.init()

        msnp = microstacknetwork.packets
        hello = msnp.HandshakeMicrostackPacket()
        hello.address = 0xb0f0a09034

        interval = 0.0

        while True:
            # print("sending hello...", end="")
            try:
                microstacknetwork.radios.radio_send(radio,
                                                    3,
                                                    hello.to_bytes(),
                                                    BEACON_ADDRESS)
            except microstacknetwork.radios.RadioSendError as e:
                # ok, so there must have been a collision?
                print("TOTAL FAILURE! WAITING FOR BEACON!")
                pass
            else:
                # print("success!")
                pass

            radio.start_listening(addresses=hello.address)
            try:
                pipe, data = radio.recv(timeout=2)
            except microstacknetwork.radios.nrf24l01.RXTimeoutError as e:
                radio.stop_listening()
                print("failed rx")
                # ignore failed rx for hello
                # raise HandshakeError("RX Timeout.") from e
            else:
                radio.stop_listening()
                p = microstacknetwork.packets.HandshakeMicrostackPacket()
                p.from_bytes(data)
                # print("RX: ", p)

            time.sleep(interval)


if __name__ == "__main__":
    unittest.main()
