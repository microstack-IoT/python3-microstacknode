import getpass
from microstacknode.hardware.display.ssd1306 import SSD1306_96x16
from microstacknode.hardware.display.sprite import (Sprite, StringSprite)
from microstacknode.hardware.display.font import FourByFiveFont


if __name__ == '__main__':
    with SSD1306_96x16() as display:
        display.init()

        # draw a border box
        sprite = Sprite(96, 16)
        sprite.draw_rectangle(0, 0, 96, 16, line_weight=1)
        display.draw_sprite(0, 0, sprite)
        display.update_display()

        # draw the username
        username = getpass.getuser()
        strspr = StringSprite("User: {}".format(username),
                              'R',
                              FourByFiveFont())
        display.draw_sprite(3, 6, strspr)
        display.update_display()
