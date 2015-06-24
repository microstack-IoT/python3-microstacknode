#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
from microstacknode.hardware.humiditytemperature.sht21 import SHT21


if __name__ == '__main__':
    with SHT21() as ht:
        while True:
            print("Humidity: {}% RH".format(ht.get_humidity()))
            print("Temperature: {}°C".format(ht.get_temperature()))
            time.sleep(0.25)
