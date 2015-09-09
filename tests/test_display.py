#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
from microstacknode.hardware.display.ssd1306 import SSD1306_96x16
from microstacknode.hardware.display.font import (FourByFiveFont,
                                                  BlockFont)
from microstacknode.hardware.display.sprite import (Sprite,
                                                    CharSprite,
                                                    StringSprite)


class TestSSD1306(unittest.TestCase):

    @unittest.skip('')
    def test_character_printing(self):
        char_sprite = CharSprite('a', FourByFiveFont())
        self.draw_sprite_on_display(char_sprite)

    @unittest.skip('')
    def test_str_printing(self):
        str_sprite = StringSprite('ALPHABET', 'R', BlockFont())
        self.draw_sprite_on_display(str_sprite)

    # @unittest.skip('')
    def test_rectangle(self):
        # draw checkerboard
        sprite = Sprite(96, 16)
        sprite.draw_rectangle(0, 0, 96, 16, 1)
        y = 0
        for x in range(0, 96, 8):
            sprite.draw_rectangle(x, y, 8, 8)
            y = 0 if y == 8 else 8
        self.draw_sprite_on_display(sprite)

    @unittest.skip('')
    def test_set_pixel(self):
        with SSD1306_96x16() as display:
            display.init()
            display.clear_display()
            display.set_pixel(0, 0, 1)
            display.update_display()

    def draw_sprite_on_display(self, sprite):
        with SSD1306_96x16() as display:
            display.init()
            display.clear_display()
            display.draw_sprite(0, 0, sprite)
            display.update_display()


if __name__ == "__main__":
    unittest.main()
