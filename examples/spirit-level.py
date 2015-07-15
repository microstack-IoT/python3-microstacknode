"""Displays a spirit level on the display."""
import time
from microstacknode.hardware.display.ssd1306 import SSD1306
from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q
from microstacknode.hardware.display.sprite import Sprite



def draw_circle(display):
    circle_sprite = Sprite(7, 7)
    circle_sprite.pixel_state = [[0, 1, 1, 1, 1, 1, 0],
                                 [1, 0, 0, 0, 0, 0, 1],
                                 [1, 0, 0, 0, 0, 0, 1],
                                 [1, 0, 0, 0, 0, 0, 1],
                                 [1, 0, 0, 0, 0, 0, 1],
                                 [1, 0, 0, 0, 0, 0, 1],
                                 [0, 1, 1, 1, 1, 1, 0]]
    display.draw_sprite(45, 6, circle_sprite, update_display=False)


def draw_dot(display, x_angle, y_angle, z_angle):
    x = int((x_angle + 40) / 80 * 96)
    y = 16 - int((y_angle + 20) / 40 * 16)
    if 0 <= x < 96:
        display.set_pixel(x, y, 1, update_display=False)


if __name__ == '__main__':
    with SSD1306() as display, MMA8452Q() as accelerometer:
        while True:
            xyz = accelerometer.get_xyz()
            x_angle = xyz['x'] * -180
            y_angle = xyz['y'] * -180
            z_angle = 90 - (180 * xyz['z'])
            display.clear_display(update_display=False)
            draw_circle(display)
            draw_dot(display, x_angle, y_angle, z_angle)
            display.update_display()
            # time.sleep(0.05)
