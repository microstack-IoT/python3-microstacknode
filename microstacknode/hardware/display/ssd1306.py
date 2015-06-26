import math
from microstackcommon.i2c import I2CMaster, writing_bytes, writing, reading


# TODO not sure why these values
WIDTH = 128
NUM_PAGES = 8


DEFAULT_I2C_BUS = 1
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


class SSD1306(I2CMaster):
    """SSD1306 128x64 dot matrix OLED."""

    def __enter__(self):
        self = super().__enter__()
        self.init()
        return self

    def _send_command(self, *cmd):
        # co = 0
        # dc = 0
        # control = (co << 7) | (dc << 6)
        control = 0x00
        self.transaction(writing_bytes(I2C_ADDR, control, *cmd))

    def _send_data(self, *cmd):
        # co = 0
        # dc = 1
        # control = (co << 7) | (dc << 6)
        control = 0x40
        self.transaction(writing_bytes(I2C_ADDR, control, *cmd))

    def _clear_buffer(self):
        # Buffer is one dimensional becasue we can send the whole thing
        # over I2C at once.
        self._buffer = [0x00] * (WIDTH * NUM_PAGES)
        # self._buffer = [[0x00 for i in range(WIDTH)] for j in range(NUM_PAGES)]

    def set_low_col_start_addr(self, address):
        """This command specifies the lower nibble of the 8-bit column
        start address for the display data RAM under Page Addressing
        Mode. The column address will be incremented by each data
        access.
        """
        self._send_command(CMD_SET_LOW_COL_START_ADDR, address)

    def set_high_col_start_addr(self, address):
        """This command specifies the higher nibble of the 8-bit column
        start address for the display data RAM under Page Addressing
        Mode. The column address will be incremented by each data
        access.
        """
        self._send_command(CMD_SET_HIGH_COL_START_ADDR, address)

    def set_mem_addr_mode(self, mode):
        """There are 3 different memory addressing mode in SSD1306:
        page addressing mode, horizontal addressing mode and vertical
        addressing mode. This command sets the way of memory addressing
        into one of the above three modes.
        """
        self._send_command(CMD_SET_MEM_ADDR_MODE, mode)

    def set_col_address(self, start, end):
        """This triple byte command specifies column start address and
        end address of the display data RAM. This command also sets the
        column address pointer to column start address. This pointer is
        used to define the current read/write column address in graphic
        display data RAM. If horizontal address increment mode is
        enabled by command 20h, after finishing read/write one column
        data, it is incremented automatically to the next column
        address. Whenever the column address pointer finishes accessing
        the end column address, it is reset back to start column address
        and the row address is incremented to the next row.
        """
        self._send_command(CMD_SET_COL_ADDR, start, end)

    def set_page_address(self, start, end):
        """This triple byte command specifies page start address and end
        address of the display data RAM. This command also sets the page
        address pointer to page start address. This pointer is used to
        define the current read/write page address in graphic display
        data RAM. If vertical address increment mode is enabled by
        command 20h, after finishing read/write one page data, it is
        incremented automatically to the next page address. Whenever the
        page address pointer finishes accessing the end page address, it
        is reset back to start page address.
        """
        self._send_command(CMD_SET_PAGE_ADDR, start, end)

    def set_display_start_line(self, start_line=0):
        """This command sets the Display Start Line register to
        determine starting address of display RAM, by selecting a value
        from 0 to 63. With value equal to 0, RAM row 0 is mapped to
        COM0. With value equal to 1, RAM row 1 is mapped to COM0 and so
        on.
        """
        self._send_command(CMD_SET_DISPLAY_START_LINE, start_line)

    def set_contrast_control_bank0(self, contrast):
        """This command sets the Contrast Setting of the display. The
        chip has 256 contrast steps from 00h to FFh. The segment output
        current increases as the contrast step value increases.
        """
        self._send_command(CMD_SET_CONTRAST_CONTROL_BANK0, contrast)

    def set_segment_remap_col_0(self):
        """This command changes the mapping between the display data
        column address and the segment driver. It allows flexibility in
        OLED module design. This command only affects subsequent data
        input. Data already stored in GDDRAM will have no changes.
        """
        self._send_command(CMD_SET_SEGMENT_REMAP_COL_0)

    def set_segment_remap_col_127(self):
        """See `set_segment_remap_col_0`"""
        self._send_command(CMD_SET_SEGMENT_REMAP_COL_127)

    def set_entire_display_ram(self):
        """Enable display outputs according to the GDDRAM contents."""
        self._send_command(CMD_ENTIRE_DISPLAY_RAM)

    def set_entire_display_on(self):
        """Resumes the display from entire display “ON” stage. Forces
        the entire display to be “ON”, regardless of the contents of the
        display data RAM.
        """
        self._send_command(CMD_ENTIRE_DISPLAY_ON)

    def set_normal_display(self):
        """In a normal display a RAM data of 1 indicates an “ON” pixel."""
        self._send_command(CMD_SET_NORMAL_DISPLAY)

    def set_inverse_display(self):
        """In an inverse display a RAM data of 0 indicates an “ON” pixel."""
        self._send_command(CMD_SET_INVERSE_DISPLAY)

    def set_multiplex_ratio(self, ratio):
        """This command switches the default 63 multiplex mode to any
        multiplex ratio, ranging from 16 to 63. The output pads
        COM0~COM63 will be switched to the corresponding COM signal.
        """
        self._send_command(CMD_SET_MULTIPLEX_RATIO, ratio)

    def set_display_on(self):
        """Turns the display on."""
        self._send_command(CMD_SET_DISPLAY_ON)

    def set_display_off(self):
        """Turns the display off."""
        self._send_command(CMD_SET_DISPLAY_OFF)

    def set_page_start_address(self, page_address):
        """This command positions the page start address from 0 to 7 in
        GDDRAM under Page Addressing Mode.
        """
        self._send_command(CMD_SET_PAGE_START_ADDRESS | (0x7 & page_address))

    def set_com_output_scan_direction_from_0(self):
        """This command sets the scan direction of the COM output,
        allowing layout flexibility in the OLED module design.
        Additionally, the display will show once this command is issued.
        For example, if this command is sent during normal display then
        the graphic display will be vertically flipped immediately
        """
        self._send_command(CMD_SET_COM_OUTPUT_SCAN_DIRECTION_FROM_0)

    def set_com_output_scan_direction_to_0(self):
        """This command sets the scan direction of the COM output,
        allowing layout flexibility in the OLED module design.
        Additionally, the display will show once this command is issued.
        For example, if this command is sent during normal display then
        the graphic display will be vertically flipped immediately
        """
        self._send_command(CMD_SET_COM_OUTPUT_SCAN_DIRECTION_TO_0)

    def set_display_offset(self, offset):
        """This is a double byte command. The second command specifies
        the mapping of the display start line to one of COM0~COM63
        (assuming that COM0 is the display start line then the display
        start line register is equal to 0). For example, to move the
        COM16 towards the COM0 direction by 16 lines the 6-bit data in
        the second byte should be given as 010000b. To move in the
        opposite direction by 16 lines the 6-bit data should be given by
        64 – 16, so the second byte would be 100000b. The following two
        tables (Table 10-1, Table 10-2) show the example of setting the
        command C0h/C8h and D3h.
        """
        # TODO negative offset
        self._send_command(CMD_SET_DISPLAY_OFFSET, offset)

    def set_display_clock_divide_ratio(self, freq_and_ratio):
        """This command consists of two functions:

            Display Clock Divide Ratio (D)(A[3:0])
            Set the divide ratio to generate DCLK (Display Clock) from
            CLK. The divide ratio is from 1 to 16, with reset value = 1.
            Please refer to section 8.3 for the details relationship of
            DCLK and CLK.

            Oscillator Frequency (A[7:4])
            Program the oscillator frequency Fosc that is the source of
            CLK if CLS pin is pulled high. The 4-bit value results in 16
            different frequency settings available as shown below. The
            default setting is 1000b.

        """
        self._send_command(CMD_SET_DISPLAY_CLOCK_DIVIDE_RATIO, freq_and_ratio)

    def set_pre_charge_period(self, pre_charge_period):
        """This command is used to set the duration of the pre-charge
        period. The interval is counted in number of DCLK, where RESET
        equals 2 DCLKs.
        """
        self._send_command(CMD_SET_PRE_CHARGE_PERIOD, pre_charge_period)

    def set_com_pins_hardware_configuration(self, config):
        """This command sets the COM signals pin configuration to match
        the OLED panel hardware layout. The table below shows the COM
        pin configuration under different conditions (for MUX ratio =64)
        """
        self._send_command(CMD_SET_COM_PINS_HARDWARE_CONFIGURATION, config)

    def set_vcomh_deselect_level(self, level):
        """This command adjusts the VCOMH regulator output."""
        self._send_command(CMD_SET_VCOMH_DESELECT_LEVEL, level)

    def enable_charge_pump(self):
        """Enable charge pump during display on."""
        self._send_command(0x8D, 0x14)

    def init(self, clear_display=True):
        """Initialises and clears the screen.

        :param clear_display: Clear the screen after initialisation (default: True)
        :type clear_display: boolean
        """
        # self.open()
        self._clear_buffer()
        self.set_display_off()
        self.set_display_clock_divide_ratio(0x80)
        self.set_multiplex_ratio(0x0F)
        self.set_display_offset(0x00)
        self.set_display_start_line()
        self.set_segment_remap_col_127()
        self.set_com_output_scan_direction_to_0()
        self.set_com_pins_hardware_configuration(0x02)
        self.set_contrast_control_bank0(0xAF)
        self.set_pre_charge_period(0xF1)
        self.set_vcomh_deselect_level(0x20)
        self.set_entire_display_ram()
        self.set_normal_display()
        self.set_mem_addr_mode(0x00)
        self.enable_charge_pump()
        if clear_display:
            self.clear_display()
        self.set_display_on()

    # def close(self):
    #     self.close()

    def update_display(self):
        self.set_col_address(0x00, WIDTH-1)
        self.set_page_address(0x00, NUM_PAGES-1)
        self._send_data(*self._buffer)

    def clear_display(self, update_display=True):
        """Clears the display.

        :param update_display: Update display after writing to buffer.
        :type update_display: boolean
        """
        self._clear_buffer()
        if update_display:
            self.update_display()

    def set_pixel(self, x, y, state, update_display=True):
        """Sets the pixel at (x, y) to be on or off.

        :param x: X coordinate of the pixel.
        :type x: integer
        :param y: Y coordinate of the pixel.
        :type y: integer
        :param state: On/Off state.
        :type state: boolean/integer
        :param update_display: Update display after writing to buffer.
        :type update_display: boolean
        """
        page = math.floor(y / 8)
        col = self._buffer[(WIDTH * page) + x]
        page_y = y % 8
        if state:
            col |= 1 << page_y
        else:
            col &= 0xff ^ (1 << page_y)
        self._buffer[(WIDTH * page) + x] = col
        if update_display:
            self.update_display()

    def draw_sprite(self, x, y, sprite, update_display=True):
        """Draw the sprite onto the display at (x, y).

        :param update_display: Update display after writing to buffer.
        :type update_display: boolean
        """
        for j in range(sprite.height):
            for i in range(sprite.width):
                self.set_pixel(x+i,
                               y+j,
                               sprite.get_pixel(i, j),
                               update_display=False)
        if update_display:
            self.update_display()
