import sys
import time
import select
import microstackcommon.gpio
import microstackcommon.i2c


DEFAULT_I2C_BUS = 1
DEFAULT_I2C_ADDR_XM = 0x1E
DEFAULT_I2C_ADDR_G = 0x6A

# Register addresses
# Gyroscope register addresses
WHO_AM_I_G = 0x0F
CTRL_REG1_G = 0x20
CTRL_REG2_G = 0x21
CTRL_REG3_G = 0x22
CTRL_REG4_G = 0x23
CTRL_REG5_G = 0x24
REFERENCE_G = 0x25
STATUS_REG_G = 0x27
OUT_X_L_G = 0x28
OUT_X_H_G = 0x29
OUT_Y_L_G = 0x2A
OUT_Y_H_G = 0x2B
OUT_Z_L_G = 0x2C
OUT_Z_H_G = 0x2D
FIFO_CTRL_REG_G = 0x2E
FIFO_SRC_REG_G = 0x2F
INT1_CFG_G = 0x30
INT1_SRC_G = 0x31
INT1_TSH_XH_G = 0x32
INT1_TSH_XL_G = 0x33
INT1_TSH_YH_G = 0x34
INT1_TSH_YL_G = 0x35
INT1_TSH_ZH_G = 0x36
INT1_TSH_ZL_G = 0x37
INT1_DURATION_G = 0x38
# Accelerometer register addresses
OUT_TEMP_L_XM = 0x05
OUT_TEMP_H_XM = 0x06
STATUS_REG_M = 0x07
OUT_X_L_M = 0x08
OUT_X_H_M = 0x09
OUT_Y_L_M = 0x0A
OUT_Y_H_M = 0x0B
OUT_Z_L_M = 0x0C
OUT_Z_H_M = 0x0D
WHO_AM_I_XM = 0x0F
INT_CTRL_REG_M = 0x12
INT_SRC_REG_M = 0x13
INT_THS_L_M = 0x14
INT_THS_H_M = 0x15
OFFSET_X_L_M = 0x16
OFFSET_X_H_M = 0x17
OFFSET_Y_L_M = 0x18
OFFSET_Y_H_M = 0x19
OFFSET_Z_L_M = 0x1A
OFFSET_Z_H_M = 0x1B
REFERENCE_X = 0x1C
REFERENCE_Y = 0x1D
REFERENCE_Z = 0x1E
CTRL_REG0_XM = 0x1F
CTRL_REG1_XM = 0x20
CTRL_REG2_XM = 0x21
CTRL_REG3_XM = 0x22
CTRL_REG4_XM = 0x23
CTRL_REG5_XM = 0x24
CTRL_REG6_XM = 0x25
CTRL_REG7_XM = 0x26
STATUS_REG_A = 0x27
OUT_X_L_A = 0x28
OUT_X_H_A = 0x29
OUT_Y_L_A = 0x2A
OUT_Y_H_A = 0x2B
OUT_Z_L_A = 0x2C
OUT_Z_H_A = 0x2D
FIFO_CTRL_REG = 0x2E
FIFO_SRC_REG = 0x2F
INT_GEN_1_REG = 0x30
INT_GEN_1_SRC = 0x31
INT_GEN_1_THS = 0x32
INT_GEN_1_DURATION = 0x33
INT_GEN_2_REG = 0x34
INT_GEN_2_SRC = 0x35
INT_GEN_2_THS = 0x36
INT_GEN_2_DURATION = 0x37
CLICK_CFG = 0x38
CLICK_SRC = 0x39
CLICK_THS = 0x3A
TIME_LIMIT = 0x3B
TIME_LATENCY = 0x3C
TIME_WINDOW = 0x3D
ACT_THS = 0x3E
ACT_DUR = 0x3F


class LSM9DS0():
    """iNEMO inertial module: 3D accelerometer, 3D gyroscope, 3D magnetometer.

        http://www.st.com/web/en/catalog/sense_power/FM89/SC1448/PF258556
        http://www.st.com/st-web-ui/static/active/en/resource/technical/document/datasheet/DM00087365.pdf

    The following attributes are configurable:

               i2c_master - Controls which I2CMaster bus is used to talk
                            to the device.
              i2c_reading - Generates I2C read messages for i2c_master.
        i2c_writing_bytes - Generates I2C write messages for i2c_master.
              i2c_addr_xm - I2C Address of the accelerometer.
               i2c_addr_g - I2C Address of the Gyroscope.
    """

    def __init__(self,
                 i2c_master=microstackcommon.i2c.I2CMaster(DEFAULT_I2C_BUS),
                 i2c_reading=microstackcommon.i2c.reading,
                 i2c_writing_bytes=microstackcommon.i2c.writing_bytes,
                 i2c_addr_xm=DEFAULT_I2C_ADDR_XM,
                 i2c_addr_g=DEFAULT_I2C_ADDR_G):
        self.i2c_master = i2c_master
        self.i2c_reading = i2c_reading
        self.i2c_writing_bytes = i2c_writing_bytes
        self.i2c_addr_xm = i2c_addr_xm
        self.i2c_addr_g = i2c_addr_g

        self.int_xm_pin = microstackcommon.gpio.Pin(
            27,
            direction=microstackcommon.gpio.IN,
            interrupt=microstackcommon.gpio.FALLING)
        self.int_xm_pin_epoll = select.epoll()

        self.int_g_pin = microstackcommon.gpio.Pin(
            23,
            direction=microstackcommon.gpio.IN,
            interrupt=microstackcommon.gpio.FALLING)
        self.int_g_pin_epoll = select.epoll()

    def __enter__(self):
        self.i2c_master = self.i2c_master.__enter__()
        self.verify_whoami()
        # interrupts TODO do this in the set method for each thing
        # self.int_xm_pin.open()
        # self.int_xm_pin_epoll.register(self.int_xm_pin,
        #                                select.EPOLLPRI | select.EPOLLET)
        # # ???
        # self.int_xm_pin_epoll.poll(timeout=0.001)
        return self

    def __exit__(self, *args):
        self.i2c_master.__exit__(*args)

    def get(self, device_address, register_address):
        return self.i2c_master.transaction(
            self.i2c_writing_bytes(device_address, register_address),
            self.i2c_reading(device_address, 1))[0][0]

    def get_xm(self, register_address):
        return self.get(self.i2c_addr_xm, register_address)

    def get_g(self, register_address):
        return self.get(self.i2c_addr_g, register_address)

    def get_bulk(self, device_address, register_address, num_registers):
        """Returns many registers starting from (and including) this one.
        Returns registers in byte format, access using indexes.
        """
        RAAI = 0x80  # Register Address Auto Increment
        return self.i2c_master.transaction(
            self.i2c_writing_bytes(device_address, RAAI | register_address),
            self.i2c_reading(device_address, num_registers))[0]

    def get_bulk_xm(self, register_address, num_registers):
        return self.get_bulk(self.i2c_addr_xm, register_address, num_registers)

    def get_bulk_g(self, register_address, num_registers):
        return self.get_bulk(self.i2c_addr_g, register_address, num_registers)

    def set(self, device_address, register_address, v):
        self.i2c_master.transaction(
            self.i2c_writing_bytes(device_address, register_address, v))

    def set_xm(self, register_address, v):
        self.set(self.i2c_addr_xm, register_address, v)

    def set_g(self, register_address, v):
        self.set(self.i2c_addr_g, register_address, v)

    def verify_whoami(self):
        assert(self.get_xm(WHO_AM_I_XM) == 0x49)
        assert(self.get_g(WHO_AM_I_G) == 0xD4)

    def enable_temperature(self):
        self.set_xm(CTRL_REG5_XM, self.get_xm(CTRL_REG5_XM) | 0x80)

    def get_temperature(self):
        t_low, t_high = self.get_bulk_xm(OUT_TEMP_L_XM, 2)
        return twos_complement((t_high << 8) | t_low, 12)

    def setup_interrupts(self):
        # interrupts
        # CTRL_REG3
        # ctrl_reg3_value = 0
        # self.set_xm(CTRL_REG3_XM, ctrl_reg3_value)
        # CTRL_REG4
        # ctrl_reg4_value = 0
        # self.set_xm(CTRL_REG4_XM, ctrl_reg4_value)
        raise NotImplementedError()

    def setup_accelerometer(self,
                            fifo_enable=False,
                            fifo_watermark_enable=False,
                            high_pass_filter_enable=False,
                            data_rate=100,
                            continious_update=True,
                            x_enable=True,
                            y_enable=True,
                            z_enable=True,
                            anti_alias_filter_bandwidth=773,
                            full_scale=2,
                            self_test='normal',
                            interrupt_enable=False,
                            interrupt_on_all=False,
                            enable_6d=False,
                            x_high_interrupt_enable=False,
                            y_high_interrupt_enable=False,
                            z_high_interrupt_enable=False,
                            x_low_interrupt_enable=False,
                            y_low_interrupt_enable=False,
                            z_low_interrupt_enable=False,
                            interrupt_duration=0,
                            interrupt_threshold=0,
                            boot_int1_xm_enable=False,
                            tap_gen_on_int1_xm=False,
                            intertial_interrupt_gen1_on_int1_xm=False,
                            intertial_interrupt_gen2_on_int1_xm=False,
                            accelerometer_data_ready_on_int1_xm=False,
                            fifo_empty_on_int1_xm=False,
                            latch_interrupt_request_1=False,
                            latch_interrupt_request_2=False,
                            high_pass_filter_mode='normalreset',
                            filtered_data_selection=False):
        # CTRL_REG0
        ctrl_reg0_value = 0
        if fifo_enable:
            ctrl_reg0_value |= 1 << 6
        if fifo_watermark_enable:
            ctrl_reg0_value |= 1 << 5
        if high_pass_filter_enable:
            ctrl_reg0_value |= 1 << 2
        self.set_xm(CTRL_REG0_XM, ctrl_reg0_value)

        # CTRL_REG1
        ctrl_reg1_value = 0
        acceleration_data_rates = {0: 0b0000 << 4,
                                   3.125: 0b0001 << 4,
                                   6.25: 0b0010 << 4,
                                   12.5: 0b0011 << 4,
                                   25: 0b0100 << 4,
                                   50: 0b0101 << 4,
                                   100: 0b0110 << 4,
                                   200: 0b0111 << 4,
                                   400: 0b1000 << 4,
                                   800: 0b1001 << 4,
                                   1600: 0b1010 << 4}
        if data_rate in acceleration_data_rates:
            ctrl_reg1_value |= acceleration_data_rates[data_rate]
        if not continious_update:
            ctrl_reg1_value |= 1 << 3
        if z_enable:
            ctrl_reg1_value |= 1 << 2
        if y_enable:
            ctrl_reg1_value |= 1 << 1
        if x_enable:
            ctrl_reg1_value |= 1
        self.set_xm(CTRL_REG1_XM, ctrl_reg1_value)

        # CTRL_REG2
        ctrl_reg2_value = 0
        aaafb = {773: 0b00 << 5,
                 194: 0b01 << 5,
                 362: 0b10 << 5,
                 50: 0b11 << 5}
        if anti_alias_filter_bandwidth in aaafb:
            ctrl_reg2_value |= aaafb[anti_alias_filter_bandwidth]
        fss = {2: 0b000 << 3,
               4: 0b001 << 3,
               6: 0b010 << 3,
               8: 0b011 << 3,
               16: 0b100 << 3}
        if full_scale in fss:
            ctrl_reg2_value |= fss[full_scale]
            self._accelerometer_full_scale = full_scale
        st = {'normal': 0b00 << 1,
              'positive': 0b01 << 1,
              'negative': 0b10 << 1}
        if self_test in st:
            ctrl_reg2_value |= st[self_test]
        self.set_xm(CTRL_REG2_XM, ctrl_reg2_value)

        # CTRL_REG3
        ctrl_reg3_value = 0
        if boot_int1_xm_enable:
            ctrl_reg3_value |= 1 << 7
        if tap_gen_on_int1_xm:
            ctrl_reg3_value |= 1 << 6
        if intertial_interrupt_gen1_on_int1_xm:
            ctrl_reg3_value |= 1 << 5
        if intertial_interrupt_gen2_on_int1_xm:
            ctrl_reg3_value |= 1 << 4
        if accelerometer_data_ready_on_int1_xm:
            ctrl_reg3_value |= 1 << 2
        if fifo_empty_on_int1_xm:
            ctrl_reg3_value |= 1
        # do not disturb the magnetometer values
        ctrl_reg3_value |= self.get_xm(CTRL_REG3_XM) & 0x0A
        self.set_xm(CTRL_REG3_XM, ctrl_reg3_value)

        # CTRL_REG4
        # int2_xm config -- not wired in
        # ctrl_reg4_value = 0
        # if tap_generator_on_int2_xm:
        #     ctrl_reg4_value |= 1 << 7
        # if intertial_interrupt_gen1_on_int2_xm:
        #     ctrl_reg4_value |= 1 << 6
        # if intertial_interrupt_gen2_on_int2_xm:
        #     ctrl_reg4_value |= 1 << 5
        # if accelerometer_data_ready_on_int2_xm:
        #     ctrl_reg4_value |= 1 << 3
        # if fifo_overrun_on_int2_xm:
        #     ctrl_reg4_value |= 1 << 1
        # if fifo_watermark_on_int2_xm:
        #     ctrl_reg4_value |= 1
        # # do not disturb the magnetometer values
        # ctrl_reg4_value |= self.get_xm(CTRL_REG4_XM) & 0x14
        # self.set_xm(CTRL_REG4_XM, ctrl_reg4_value)

        # CTRL_REG5
        ctrl_reg5_value = 0
        if latch_interrupt_request_2:
            ctrl_reg5_value |= 1 << 1
        if latch_interrupt_request_1:
            ctrl_reg5_value |= 1
        # do not disturb the magnetometer values
        ctrl_reg5_value |= self.get_xm(CTRL_REG5_XM) & 0xFC
        self.set_xm(CTRL_REG5_XM, ctrl_reg5_value)

        # CTRL_REG7
        ctrl_reg7_value = 0
        high_pass_filter_modes = {'normalreset': 0b00 << 6,
                                  'reference': 0b01 << 6,
                                  'normal': 0b10 << 6,
                                  'autoreset': 0b11 << 6}
        if high_pass_filter_mode in high_pass_filter_modes:
            ctrl_reg7_value |= high_pass_filter_modes[high_pass_filter_mode]
        if filtered_data_selection:
            ctrl_reg7_value |= 1 << 5
        # do not disturb other half of CTRL_REG7
        ctrl_reg7_value |= self.get_xm(CTRL_REG7_XM) & 0x1F
        self.set_xm(CTRL_REG7_XM, ctrl_reg7_value)

        if interrupt_enable:
            int_gen_2_reg_value = 0
            if interrupt_on_all:
                int_gen_2_reg_value |= 1 << 7
            if enable_6d:
                int_gen_2_reg_value |= 1 << 6
            if z_high_interrupt_enable:
                int_gen_2_reg_value |= 1 << 5
            if z_low_interrupt_enable:
                int_gen_2_reg_value |= 1 << 4
            if y_high_interrupt_enable:
                int_gen_2_reg_value |= 1 << 3
            if y_low_interrupt_enable:
                int_gen_2_reg_value |= 1 << 2
            if x_high_interrupt_enable:
                int_gen_2_reg_value |= 1 << 1
            if x_low_interrupt_enable:
                int_gen_2_reg_value |= 1
            self.set_xm(INT_GEN_2_REG, int_gen_2_reg_value)

            self.set_xm(INT_GEN_1_DURATION, 0x7f & interrupt_duration)
            interrupt_threshold_raw = int(
                interrupt_threshold / self._accelerometer_full_scale * 0x7f)
            self.set_xm(INT_GEN_1_THS, 0x7f & interrupt_threshold_raw)

            if not self.int_xm_pin.closed:
                self.int_xm_pin.open()
                self.int_xm_pin_epoll.register(self.int_xm_pin,
                                               select.EPOLLPRI | select.EPOLLET)
                # ??? get rid of the first interrupt
                self.int_xm_pin_epoll.poll(timeout=0.001)

    def setup_magnetometer(self,
                           temperature_sensor_enable=True,
                           high_resolution=False,
                           data_rate=25,
                           latch_interrupt_request_2=False,
                           latch_interrupt_request_1=False,
                           full_scale=4,
                           low_power=False,
                           sensor_mode='single',
                           interrupt_enable=False,
                           x_interrupt_enable=False,
                           y_interrupt_enable=False,
                           z_interrupt_enable=False,
                           open_drain=False,
                           interrupt_active_high=False,
                           latch_interrupt_request=False,
                           enable_4d=False,
                           interrupt_threshold=0):

        if interrupt_enable:
            # INT_CTRL_REG_M
            int_ctrl_reg_m_value = 0
            int_ctrl_reg_m_value |= 1 # interrupt enable
            if x_interrupt_enable:
                int_ctrl_reg_m_value |= 1 << 7
            if y_interrupt_enable:
                int_ctrl_reg_m_value |= 1 << 6
            if z_interrupt_enable:
                int_ctrl_reg_m_value |= 1 << 5
            if open_drain:
                int_ctrl_reg_m_value |= 1 << 4
            if interrupt_active_high:
                int_ctrl_reg_m_value |= 1 << 3
            if latch_interrupt_request:
                int_ctrl_reg_m_value |= 1 << 2
            if enable_4d:
                int_ctrl_reg_m_value |= 1 << 1
            self.set_xm(INT_CTRL_REG_M, int_ctrl_reg_m_value)

            self.set_xm(INT_THS_H_M, 0xff & (interrupt_threshold >> 8))
            self.set_xm(INT_THS_L_M, 0xff & interrupt_threshold)

            if not self.int_xm_pin.closed:
                self.int_xm_pin.open()
                self.int_xm_pin_epoll.register(self.int_xm_pin,
                                               select.EPOLLPRI | select.EPOLLET)
                # ??? get rid of the first interrupt
                self.int_xm_pin_epoll.poll(timeout=0.001)

        # CTRL_REG5
        ctrl_reg5_value = 0
        if temperature_sensor_enable:
            ctrl_reg5_value |= 1 << 7
        if high_resolution:
            ctrl_reg5_value |= 0b11 << 5
        data_rates = {3.125: 0b000 << 2,
                      6.25: 0b001 << 2,
                      12.5: 0b010 << 2,
                      25: 0b011 << 2,
                      50: 0b100 << 2,
                      100: 0b101 << 2}
        if data_rate in data_rates:
            ctrl_reg5_value |= data_rates[data_rate]
        if latch_interrupt_request_2:
            ctrl_reg5_value |= 1 << 1
        if latch_interrupt_request_1:
            ctrl_reg5_value |= 1
        self.set_xm(CTRL_REG5_XM, ctrl_reg5_value)

        # CTRL_REG6
        ctrl_reg6_value = 0
        full_scales = {2: 0b00 << 5,
                       4: 0b01 << 5,
                       8: 0b10 << 5,
                       12: 0b11 << 5}
        if full_scale in full_scales:
            ctrl_reg6_value |= full_scales[full_scale]
            self._magnetometer_full_scale = full_scale
        self.set_xm(CTRL_REG6_XM, ctrl_reg6_value)

        # CTRL_REG7
        ctrl_reg7_value = 0
        if low_power:
            ctrl_reg7_value |= 1 << 2
        sensor_modes = {'continious': 0b00,
                        'single': 0b01,
                        'powerdown': 0b10}
        if sensor_mode in sensor_modes:
            ctrl_reg7_value |= sensor_modes[sensor_mode]
        # do not disturb other half of CTRL_REG7
        ctrl_reg7_value |= self.get_xm(CTRL_REG7_XM) & 0xF8
        self.set_xm(CTRL_REG7_XM, ctrl_reg7_value)

    def setup_gyroscope(self,
                        data_rate=95,
                        cutoff_selection=0,
                        power_down=False,
                        x_enable=True,
                        y_enable=True,
                        z_enable=True,
                        high_pass_filter_mode='normalreset',
                        high_pass_filter_cutoff_selection=0,
                        continious_update=True,
                        big_endian=False,
                        full_scale=245,
                        self_test_mode='normal',
                        reboot_memory_content=False,
                        fifo_enable=False,
                        high_pass_filter_enable=False,
                        interrupt_enable=False,
                        boot_status_available=False,
                        interrupt_active_low=False,
                        open_drain=False,
                        int1_selection=0,
                        out_selection=0,
                        fifo_mode='bypass',
                        fifo_watermark=0,
                        interrupt_on_all=False,
                        latch_interrupt_request=False,
                        x_high_interrupt_enable=False,
                        x_low_interrupt_enable=False,
                        y_high_interrupt_enable=False,
                        y_low_interrupt_enable=False,
                        z_high_interrupt_enable=False,
                        z_low_interrupt_enable=False,
                        x_interrupt_threshold=0,
                        y_interrupt_threshold=0,
                        z_interrupt_threshold=0,
                        interrupt_duration=0):
        if interrupt_enable:
            int1_cfg_g_value = 0
            if interrupt_on_all:
                int1_cfg_g_value |= 1 << 7
            if latch_interrupt_request:
                int1_cfg_g_value |= 1 << 6
            if z_high_interrupt_enable:
                int1_cfg_g_value |= 1 << 5
            if z_low_interrupt_enable:
                int1_cfg_g_value |= 1 << 4
            if y_high_interrupt_enable:
                int1_cfg_g_value |= 1 << 3
            if y_low_interrupt_enable:
                int1_cfg_g_value |= 1 << 2
            if x_high_interrupt_enable:
                int1_cfg_g_value |= 1 << 1
            if x_low_interrupt_enable:
                int1_cfg_g_value |= 1
            self.set_g(INT1_CFG_G, int1_cfg_g_value)

            self.set_g(INT1_TSH_XH_G, 0xff & (x_interrupt_threshold >> 8))
            self.set_g(INT1_TSH_XL_G, 0xff & x_interrupt_threshold)
            self.set_g(INT1_TSH_YH_G, 0xff & (y_interrupt_threshold >> 8))
            self.set_g(INT1_TSH_YL_G, 0xff & y_interrupt_threshold)
            self.set_g(INT1_TSH_ZH_G, 0xff & (z_interrupt_threshold >> 8))
            self.set_g(INT1_TSH_ZL_G, 0xff & z_interrupt_threshold)

            if interrupt_duration:
                self.set_g(INT1_DURATION_G, 0x80 | (0x7f & interrupt_duration))

            self.int_g_pin.open()
            self.int_g_pin_epoll.register(self.int_g_pin,
                                          select.EPOLLPRI | select.EPOLLET)
            # ??? get rid of the first interrupt
            self.int_g_pin_epoll.poll(timeout=0.001)

        # CTRL_REG1
        ctrl_reg1_value = 0
        data_rates = {95: 0b00 << 6,
                      190: 0b01 << 6,
                      380: 0b10 << 6,
                      760: 0b11 << 6}
        if data_rate in data_rates:
            ctrl_reg1_value |= data_rates[data_rate]
        if cutoff_selection in range(4):
            ctrl_reg1_value |= cutoff_selection << 4
        if not power_down:
            ctrl_reg1_value |= 1 << 3
        if z_enable:
            ctrl_reg1_value |= 1 << 2
        if y_enable:
            ctrl_reg1_value |= 1 << 1
        if x_enable:
            ctrl_reg1_value |= 1
        self.set_g(CTRL_REG1_G, ctrl_reg1_value)

        # CTRL_REG2
        ctrl_reg2_value = 0
        high_pass_filter_modes = {'normalreset': 0b00 << 4,
                                  'reference': 0b01 << 4,
                                  'normal': 0b10 << 4,
                                  'autoreset': 0b11 << 4}
        if high_pass_filter_mode in high_pass_filter_modes:
            ctrl_reg2_value |= high_pass_filter_modes[high_pass_filter_mode]
        if high_pass_filter_cutoff_selection in range(10):
            ctrl_reg2_value |= high_pass_filter_cutoff_selection
        self.set_g(CTRL_REG2_G, ctrl_reg2_value)

        # CTRL_REG3
        ctrl_reg3_value = 0
        if interrupt_enable:
            ctrl_reg3_value |= 1 << 7
        if boot_status_available:
            ctrl_reg3_value |= 1 << 6
        if interrupt_active_low:
            ctrl_reg3_value |= 1 << 5
        if open_drain:
            ctrl_reg3_value |= 1 << 4
        # lower nibble is to do with watermark on DRDY which is not connected.
        self.set_g(CTRL_REG3_G, ctrl_reg3_value)

        # CTRL_REG4
        ctrl_reg4_value = 0
        if not continious_update:
            ctrl_reg4_value |= 1 << 7
        if big_endian:
            ctrl_reg4_value |= 1 << 6
        full_scales = {245: 0b00 << 4,
                       500: 0b01 << 4,
                       2000: 0b10 << 4}
        if full_scale in full_scales:
            ctrl_reg4_value |= full_scales[full_scale]
            self._gyroscope_full_scale = full_scale
        self_test_modes = {'normal': 0b00 << 1,
                           'selftest0': 0b01 << 1,
                           'selftest1': 0b11 << 1}
        if self_test_mode in self_test_modes:
            ctrl_reg4_value |= self_test_modes[self_test_mode]
        # SPI mode (bit 0) is obviously disabled since this is an I2C module
        self.set_g(CTRL_REG4_G, ctrl_reg4_value)

        # CTRL_REG5
        ctrl_reg5_value = 0
        if reboot_memory_content:
            ctrl_reg5_value |= 1 << 7
        if fifo_enable:
            ctrl_reg5_value |= 1 << 6
        if high_pass_filter_enable:
            ctrl_reg5_value |= 1 << 4
        if int1_selection in range(4):
            ctrl_reg5_value |= int1_selection << 2
        if out_selection in range(4):
            ctrl_reg5_value |= out_selection
        self.set_g(CTRL_REG5_G, ctrl_reg5_value)

        # DEBUG print out all control registers
        # ctrlregs = self.get_bulk(CTRL_REG1_G, 5)
        # for i in range(5):
        #     print("CTRL_REG{}_G: {}".format(i+1, hex(ctrlregs[i])))

        fifo_ctrl_reg_g_value = 0
        fifo_modes = {'bypass': 0b000 << 5,
                      'fifo': 0b001 << 5,
                      'stream': 0b010 << 5,
                      'streamtofifo': 0b011 << 5,
                      'bypasstostream': 0b100 << 5}
        if fifo_mode in fifo_modes:
            fifo_ctrl_reg_g_value |= fifo_modes[fifo_mode]
        if fifo_watermark in range(32):
            fifo_ctrl_reg_g_value |= fifo_watermark
        self.set_g(FIFO_CTRL_REG_G, fifo_ctrl_reg_g_value)

    def _get_twos_complement_xyz(self, start_register_addr):
        xlo, xhi, ylo, yhi, zlo, zhi = self.get_bulk_xm(start_register_addr, 6)
        v = {'x': xhi << 8 | xlo, 'y': yhi << 8 | ylo, 'z': zhi << 8 | zlo}
        return {axis: twos_complement(magnitude, 16)
                for axis, magnitude in v.items()}

    def _scale(self, magnitude, scale):
        return magnitude / 2**15 * scale

    def get_accelerometer(self, raw=False):
        acceleration_vector = self._get_twos_complement_xyz(OUT_X_L_A)
        if raw:
            return acceleration_vector
        else:
            return {axis: self._scale(magnitude,
                                      self._accelerometer_full_scale)
                    for axis, magnitude in acceleration_vector.items()}

    def get_magnetometer(self, raw=False):
        magnetic_vector = self._get_twos_complement_xyz(OUT_X_L_M)
        if raw:
            return magnetic_vector
        else:
            return {axis: self._scale(magnitude, self._magnetometer_full_scale)
                    for axis, magnitude in magnetic_vector.items()}

    def get_gyroscope(self, raw=False):
        gyro_vector = self._get_twos_complement_xyz(OUT_X_L_G)
        if raw:
            return gyro_vector
        else:
            return {axis: self._scale(magnitude, self._gyroscope_full_scale)
                    for axis, magnitude in gyro_vector.items()}

    def wait_for_gyroscope_interrupt(self, timeout=None):
        while True:
            if timeout is not None:
                events = self.int_g_pin_epoll.poll(timeout)
            else:
                events = self.int_g_pin_epoll.poll()

            for fileno, event in events:
                if fileno == self.int_g_pin.fileno():
                    int_src = self.get_g(INT1_SRC_G)
                    return {'active': (1 & (int_src >> 6)) == 1,
                            'z_high': (1 & (int_src >> 5)) == 1,
                            'z_low': (1 & (int_src >> 4)) == 1,
                            'y_high': (1 & (int_src >> 3)) == 1,
                            'y_low': (1 & (int_src >> 2)) == 1,
                            'x_high': (1 & (int_src >> 1)) == 1,
                            'x_low': (1 & int_src) == 1}

    def wait_for_accelerometer_interrupt(self, timeout=None):
        while True:
            if timeout is not None:
                events = self.int_xm_pin_epoll.poll(timeout)
            else:
                events = self.int_xm_pin_epoll.poll()

            for fileno, event in events:
                if fileno == self.int_xm_pin.fileno():
                    int_src = self.int_gen_1_src.get()
                    return {'active': (1 & (int_src >> 6)) == 1,
                            'z_high': (1 & (int_src >> 5)) == 1,
                            'z_low': (1 & (int_src >> 4)) == 1,
                            'y_high': (1 & (int_src >> 3)) == 1,
                            'y_low': (1 & (int_src >> 2)) == 1,
                            'x_high': (1 & (int_src >> 1)) == 1,
                            'x_low': (1 & int_src) == 1}

    def wait_for_magnetometer_interrupt(self, timeout=None):
        while True:
            if timeout is not None:
                events = self.int_xm_pin_epoll.poll(timeout)
            else:
                events = self.int_xm_pin_epoll.poll()

            for fileno, event in events:
                if fileno == self.int_xm_pin.fileno():
                    int_src = self.int_src_reg_m.get()
                    return {'x_positive': (1 & (int_src >> 7)) == 1,
                            'y_positive': (1 & (int_src >> 6)) == 1,
                            'z_positive': (1 & (int_src >> 5)) == 1,
                            'x_negative': (1 & (int_src >> 4)) == 1,
                            'y_negative': (1 & (int_src >> 3)) == 1,
                            'z_negative': (1 & (int_src >> 2)) == 1,
                            'range_overflow': (1 & (int_src >> 1)) == 1,
                            'active': (1 & int_src) == 1}


def twos_complement(value, bits):
    """Signs a value with an arbitary number of bits."""
    if value >= (1 << (bits - 1)):
        value = -((~value + 1) + (1 << bits))
    return value
