"""Displays XYZ gravity values."""
import time
import datetime
from microstacknode.hardware.display.ssd1306 import SSD1306
from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q
from microstacknode.hardware.display.font import (FourByFiveFont,
                                                  BlockFont)
from microstacknode.hardware.display.sprite import StringSprite


if __name__ == '__main__':
    with SSD1306() as display, MMA8452Q() as accelerometer:
        while True:
            x, y, z = accelerometer.get_xyz()
            xy_str = 'x:{:.2f} y:{:.2f}'.format(x, y)
            z_str = 'z:{:.2f}'.format(z)

            font = BlockFont()
            xy_str_sprite = StringSprite(xy_str, 'R', font)
            z_str_sprite = StringSprite(z_str, 'R', font)

            display.draw_sprite(0, 0, xy_str_sprite)
            display.draw_sprite(0, 8, z_str_sprite)
            time.sleep(0.1)
