#!/usr/bin/env python3
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import time
import unittest
import microstacknode.hardware.display.ssd1306
from microstacknode.hardware.display.font import (FourByFiveFont,
                                                  BlockFont)
from microstacknode.hardware.display.sprite import (Sprite,
                                                    CharSprite,
                                                    StringSprite)


class TestSSD1306(unittest.TestCase):

    # def setUp(self):
    #     self.display = microstacknode.hardware.display.ssd1306.SSD1306()
    #     self.display.init()

    # @unittest.skip('')
    # def test_character_printing(self):
    #     char_sprite = CharSprite('a', FourByFiveFont())
    #     self.display.draw_sprite(0, 0, char_sprite)

    # @unittest.skip('')
    # def test_character_printing(self):
    #     str_sprite = StringSprite('ALPHABET', 'R', MinecraftiaFont())
    #     self.display.draw_sprite(0, 0, str_sprite)

    # @unittest.skip('')
    # def test_rectangle(self):
    #     sprite = Sprite(10, 16)
    #     sprite.draw_rectangle(0, 0, 10, 16, 1)
    #     sprite.draw_rectangle(1, 1, 5, 5)
    #     self.display.draw_sprite(0, 0, sprite)
    #     # time.sleep(1)
    #     # sprite.invert_vertical()
    #     # self.display.draw_sprite(0, 0, sprite)
    #     # time.sleep(1)
    #     # sprite.invert_horizontal()
    #     # self.display.draw_sprite(0, 0, sprite)
    #     time.sleep(1)
    #     sprite.rotate90(3)
    #     self.display.clear_display()
    #     self.display.draw_sprite(0, 0, sprite)

    #     # time.sleep(1)
    #     # sprite.rotate90()
    #     # self.display.clear_display()
    #     # self.display.draw_sprite(0, 0, sprite)

    #     # time.sleep(1)
    #     # sprite.rotate90()
    #     # self.display.clear_display()
    #     # self.display.draw_sprite(0, 0, sprite)

    def test_set_pixel(self):
        with microstacknode.hardware.display.ssd1306.SSD1306() as ssd1306:
            ssd1306.set_pixel(0, 0, 1)


if __name__ == "__main__":
    unittest.main()
