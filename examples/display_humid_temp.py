"""Displays the humidity and temperature."""
import time
import datetime
from microstacknode.hardware.display.ssd1306 import SSD1306
from microstacknode.hardware.humiditytemperature.sht21 import SHT21
from microstacknode.hardware.display.font import (FourByFiveFont,
                                                  BlockFont)
from microstacknode.hardware.display.sprite import StringSprite


if __name__ == '__main__':
    with SSD1306() as display, SHT21() as htsensor:
        while True:
            humidity_str = 'H:{:.2f}%RH'.format(htsensor.get_humidity())
            # temperature_str = 'Temp: {:.2f}°C'.format(
            #     htsensor.get_temperature())
            temperature_str = 'Temp:{:.2f}°C'.format(
                 htsensor.get_temperature())

            font = BlockFont()
            humidity_str_sprite = StringSprite(humidity_str, 'R', font)
            temperature_str_sprite = StringSprite(temperature_str, 'R', font)

            display.draw_sprite(0, 0, humidity_str_sprite)
            display.draw_sprite(0, 8, temperature_str_sprite)
            time.sleep(1)
