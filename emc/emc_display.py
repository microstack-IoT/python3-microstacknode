#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
from microstacknode.hardware.display.ssd1306 import SSD1306
from microstacknode.hardware.display.font import BlockFont
from microstacknode.hardware.display.sprite import StringSprite


if __name__ == '__main__':
    with SSD1306() as display:
        number = 0
        while True:
            number += 1
            str_sprite = StringSprite(str(number), 'R', BlockFont())
            display.draw_sprite(0, 0, str_sprite)
            time.sleep(0.25)
