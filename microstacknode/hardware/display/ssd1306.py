import time
import math
from microstackcommon.i2c import I2CMaster, writing_bytes, writing, reading


I2C_ADDR = 0x3C

# Commands
CMD_SET_LOW_COL_START_ADDR = 0x00  # 0x0F
CMD_SET_HIGH_COL_START_ADDR = 0x10  # 0x1F
CMD_SET_MEM_ADDR_MODE = 0x20
CMD_SET_COL_ADDR = 0x21
CMD_SET_PAGE_ADDR = 0x22
CMD_SET_DISPLAY_START_LINE = 0x40  # 0x7F
CMD_SET_CONTRAST_CONTROL_BANK0 = 0x81
CMD_SET_SEGMENT_REMAP_COL_0 = 0xA0
CMD_SET_SEGMENT_REMAP_COL_127 = 0xA1
CMD_ENTIRE_DISPLAY_RAM = 0xA4
CMD_ENTIRE_DISPLAY_ON = 0xA5
CMD_SET_NORMAL_DISPLAY = 0xA6
CMD_SET_INVERSE_DISPLAY = 0xA7
CMD_SET_MULTIPLEX_RATIO = 0xA8
CMD_SET_DISPLAY_ON = 0xAF
CMD_SET_DISPLAY_OFF = 0xAE
CMD_SET_PAGE_START_ADDRESS = 0xB0
CMD_SET_COM_OUTPUT_SCAN_DIRECTION_FROM_0 = 0xC0
CMD_SET_COM_OUTPUT_SCAN_DIRECTION_TO_0 = 0xC8
CMD_SET_DISPLAY_OFFSET = 0xD3
CMD_SET_DISPLAY_CLOCK_DIVIDE_RATIO = 0xD5
CMD_SET_PRE_CHARGE_PERIOD = 0xD9
CMD_SET_COM_PINS_HARDWARE_CONFIGURATION = 0xDA
CMD_SET_VCOMH_DESELECT_LEVEL = 0xDB
CMD_SET_CHARGE_PUMP = 0x8D


class SSD1306_96x16(I2CMaster):
    """SSD1306 96x16 dot matrix OLED."""

    pixel_width = 96
    pixel_height = 16
    num_pages = pixel_height / 8 # one page is 8 bits high
    rotate_display_180 = True

    def send_command(self, *cmd):
        # co = 0
        # dc = 0
        # control = (co << 7) | (dc << 6)
        control = 0x00
        self.transaction(writing_bytes(I2C_ADDR, control, *cmd))

    def send_data(self, *data):
        # co = 0
        # dc = 1
        # control = (co << 7) | (dc << 6)
        control = 0x40
        self.transaction(writing_bytes(I2C_ADDR, control, *data))

    def init(self):
        """Initialises and clears the screen."""
        self.set_display_enabled(False)
        # set display clock divide ratio
        # upper nibble: oscillator freq, lowser nibble: divider
        self.send_command(CMD_SET_DISPLAY_CLOCK_DIVIDE_RATIO, 0x80)
        self.send_command(CMD_SET_MULTIPLEX_RATIO, 0x0F)
        self.send_command(CMD_SET_DISPLAY_OFFSET, 0x00)
        self.send_command(CMD_SET_DISPLAY_START_LINE | 0)
        self.send_command(CMD_SET_CHARGE_PUMP, 0x14) # enable charge pump
        self.send_command(CMD_SET_MEM_ADDR_MODE, 0x00) # horizontal addressing
        self.send_command(CMD_SET_SEGMENT_REMAP_COL_127) # set segment remap
        if self.rotate_display_180:
            # Flip display (reverse buffer later)
            self.send_command(CMD_SET_COM_OUTPUT_SCAN_DIRECTION_TO_0)
        else:
            self.send_command(CMD_SET_COM_OUTPUT_SCAN_DIRECTION_FROM_0)
        self.send_command(CMD_SET_COM_PINS_HARDWARE_CONFIGURATION, 0x02)
        self.send_command(CMD_SET_CONTRAST_CONTROL_BANK0, 0xAF)
        self.send_command(CMD_SET_PRE_CHARGE_PERIOD, 0xF1)
        self.send_command(CMD_SET_VCOMH_DESELECT_LEVEL, 0x40)
        self.send_command(CMD_ENTIRE_DISPLAY_RAM)
        self.set_inverse_display(False)
        self.clear_display()
        time.sleep(0.1)
        self.set_display_enabled(True)

    def clear_buffer(self):
        # Buffer is one dimensional becasue we can send the whole thing
        # over I2C at once.
        self._buffer = [0x00] * int(self.pixel_width * self.num_pages)

    def set_inverse_display(self, enabled):
        """In an inverse display a RAM data of 0 indicates an “ON” pixel."""
        if enabled:
            self.send_command(CMD_SET_INVERSE_DISPLAY)
        else:
            self.send_command(CMD_SET_NORMAL_DISPLAY)

    def set_display_enabled(self, enabled):
        """Turns the display on or off."""
        if enabled:
            self.send_command(CMD_SET_DISPLAY_ON)
        else:
            self.send_command(CMD_SET_DISPLAY_OFF)

    def update_display(self):
        # Set col addr so that reads beyond this boundary wrap around.
        self.send_command(CMD_SET_COL_ADDR, 0, self.pixel_width-1)
        # Same with pages. Each page is eight bits tall (so 2 pages for 16px)
        self.send_command(CMD_SET_PAGE_ADDR, 0, 1)
        if self.rotate_display_180:
            # flip buffer
            pages = [list(reversed(self._buffer[:int(self.pixel_width)])),
                     list(reversed(self._buffer[int(self.pixel_width):]))]
            buf = pages[0] + pages[1]
            self.send_data(*buf)
        else:
            self.send_data(*self._buffer)

    def clear_display(self):
        """Clears the display."""
        self.clear_buffer()
        self.update_display()

    def set_pixel(self, x, y, state):
        """Sets the pixel at (x, y) to be on or off.

        :param x: X coordinate of the pixel.
        :type x: integer
        :param y: Y coordinate of the pixel.
        :type y: integer
        :param state: On/Off state.
        :type state: boolean/integer
        """
        page = math.floor(y / 8)
        col_index = (self.pixel_width * page) + x
        col = self._buffer[col_index]
        bit_shift = y % 8
        if state:
            col |= 1 << bit_shift
        else:
            col &= 0xff ^ (1 << bit_shift)
        self._buffer[col_index] = col

    def draw_sprite(self, x, y, sprite):
        """Draw the sprite onto the display at (x, y)."""
        for j in range(sprite.height):
            for i in range(sprite.width):
                self.set_pixel(x+i, y+j, sprite.get_pixel(i, j))
