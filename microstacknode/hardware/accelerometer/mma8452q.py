import sys
import time
from microstackcommon.i2c import I2CMaster, writing_bytes, writing, reading


DEFAULT_I2C_BUS = 1
DEFAULT_I2C_ADDRESS = 0x1d
# DEFAULT_I2C_ADDRESS = 0x1c

# register addresses
STATUS = 0x00
OUT_X_MSB = 0x01
OUT_X_LSB = 0x02
OUT_Y_MSB = 0x03
OUT_Y_LSB = 0x04
OUT_Z_MSB = 0x05
OUT_Z_LSB = 0x06
SYSMOD = 0x0B
INT_SOURCE = 0x0C
WHO_AM_I = 0x0D
XYZ_DATA_CFG = 0x0E
HP_FILTER_CUTOFF = 0x0F
PL_STATUS = 0x10
PL_CFG = 0x11
PL_COUNT = 0x12
PL_BF_ZCOMP = 0x13
P_L_THS_REG = 0x14
FF_MT_CFG = 0x15
FF_MT_SRC = 0x16
FF_MT_SRC = 0x17
FF_MT_COUNT = 0x18
TRANSIENT_CFG = 0x1D
TRANSIENT_THS = 0x1F
TRANSIENT_COUNT = 0x20
PULSE_CFG = 0x21
PULSE_SRC = 0x22
PULSE_THSX = 0x23
PULSE_THSY = 0x24
PULSE_THSZ = 0x25
PULSE_TMLT = 0x26
PULSE_LTCY = 0x27
PULSE_WIND = 0x28
ASLP_COUNT = 0x29
CTRL_REG1 = 0x2A
CTRL_REG2 = 0x2B
CTRL_REG3 = 0x2C
CTRL_REG4 = 0x2D
CTRL_REG5 = 0x2E
OFF_X = 0x2F
OFF_Y = 0x30
OFF_Z = 0x31

# register values
# CTRL_REG1 Register (Read/Write)
# +------------+------------+-------+-------+------+--------+--------+--------+
# | bit 7      | bit 6      | bit 5 | bit 4 | bit 3| bit 2  | bit 1  | bit 0  |
# +------------+------------+-------+-------+------+--------+--------+--------+
# | ASLP_RATE1 | ASLP_RATE0 | DR2   | DR1   | DR0  | LNOISE | F_READ | ACTIVE |
# +------------+------------+-------+-------+------+--------+--------+--------+
CTRL_REG1_SET_ACTIVE = 0x01
# DR2 DR1 DR0
CTRL_REG1_ODR_800 = 1 << 3  # period = 1.25 ms
CTRL_REG1_ODR_400 = 2 << 3  # period = 2.5 ms
CTRL_REG1_ODR_200 = 3 << 3  # period = 5 ms
CTRL_REG1_ODR_100 = 4 << 3  # period = 10 ms
CTRL_REG1_ODR_50 = 5 << 3  # period = 20 ms
CTRL_REG1_ODR_12_5 = 6 << 3  # period = 80 ms
CTRL_REG1_ODR_6_25 = 7 << 3  # period = 160 ms
CTRL_REG1_ODR_1_56 = 8 << 3  # period = 640 ms

# XYZ_DATA_CFG (Read/Write)
# +-------+-------+-------+---------+-------+-------+-------+-------+
# | bit 7 | bit 6 | bit 5 | bit 4   | bit 3 | bit 2 | bit 1 | bit 0 |
# +-------+-------+-------+---------+-------+-------+-------+-------+
# | 0     | 0     | 0     | HPF_OUT | 0     | 0     | FS1   | FS0   |
# +-------+-------+-------+---------+-------+-------+-------+-------+
XYZ_DATA_CFG_FSR_2G = 0x00
XYZ_DATA_CFG_FSR_4G = 0x01
XYZ_DATA_CFG_FSR_8G = 0x02


STANDARD_GRAVITY = 9.80665


class MMA8452Q(I2CMaster):
    """Freescale MMA8452Q accelerometer.

    http://www.freescale.com/files/sensors/doc/data_sheet/MMA8452Q.pdf

    """
    # This chip uses an SMBus implementation which is not well supported on
    # the Raspberry Pi (at least, not in Python 3). We can write to registers
    # but reading requires sending multiple START signals. This somehow resets
    # the requested register address to 0x00. So we *can* read, but only from
    # register 0x00 and subsequent registers (using a multiple read). Luckily
    # the XYZ registers are in the first few and we can access them using a
    # multi-read.

    # One might be inclined to multi-read the whole register bank however the
    # auto increment resets to 0x00 shortly after the XYZ registers.

    # Maybe we can get it working though. Try getting python-smbus working
    # with Python 3
    # http://www.spinics.net/lists/linux-i2c/msg08427.html
    #http://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/plain/Documentation/i2c/smbus-protocol

    # Special thanks for John Nivard for providing a working class, which
    # this one is based off. I have made changes for consistency with other
    # Microstack modules.

    def __init__(self,
                 i2c_bus=DEFAULT_I2C_BUS,
                 i2c_address=DEFAULT_I2C_ADDRESS):
        super().__init__(i2c_bus)
        self.i2c_address = i2c_address
        self.xyz_data_cfg = MMA8452QRegister(XYZ_DATA_CFG,
                                             self.i2c_address,
                                             self)
        self.ctrl_reg1 = MMA8452QRegister(CTRL_REG1, self.i2c_address, self)
        # have to store some registers locally since we can't read
        self._xyz_data_cfg_value = 0
        self._ctrl_reg1_value = 0

    def __enter__(self):
        self = super().__enter__()
        self.init()
        return self

    def init(self):
        """Initalises the accelerometer with some default values."""
        self.standby()
        self.set_output_data_rate(800)  # Hz
        self.set_g_range(2)
        self.activate()

    def reset(self):
        """Resets the accelerometer."""
        self._ctrl_reg1_value = 0
        self.ctrl_reg1.set(self._ctrl_reg1_value)

    def activate(self):
        """Start recording the accelerometer values. Call this after
        changing any settings.
        """
        self._ctrl_reg1_value |= CTRL_REG1_SET_ACTIVE
        self.ctrl_reg1.set(self._ctrl_reg1_value)

    def standby(self):
        """Stop recording the accelerometer values. Call this before
        changing any settings.
        """
        self._ctrl_reg1_value &= 0xff ^ CTRL_REG1_SET_ACTIVE
        self.ctrl_reg1.set(self._ctrl_reg1_value)

    def get_xyz(self, raw=False, res12=True):
        """Returns the x, y and z values as a dictionary. By default it returns
        signed values at 12-bit resolution. You can specify a lower resolution
        (8-bit) or request the raw register values. Signed values are
        in G's. You can alter the recording range with `set_g_range()`.

        :param raw: If True: return raw, unsigned data, else: sign values
        :type raw: boolean (default: False)
        :param res12: If True: read 12-bit resolution, else: 8-bit
        :type res12: boolean (default: True)
        """
        # Since we can't read arbitary registers from this chip over I2C
        # (because there is no decent SMBus implementation, in Python 3 at
        # least) we have to just read the first 7 registers and pull the
        # XYZ data from that.

        # Notes:

        # - 12-bit resolution from OUT MSB and OUT LSB registers:

        #     +--------+-----------------+
        #     | msb    | lsb             |
        #     +--------+--------+--------+
        #     | 8 bits | 4 bits | 4 bits |
        #     +--------+--------+--------+
        #     | value (12 bits) | unused |
        #     +--------+--------+--------+

        # - 8-bit resolution just from OUT MSB:

        #     +--------+--------+
        #     | msb    | lsb    |
        #     +--------+--------+
        #     | 8 bits | 8 bits |
        #     +--------+--------+
        #     | value  | unused |
        #     +--------+--------+

        # bulk read works
        buf = self.transaction(reading(self.i2c_address, 7))[0]
        # status = buf[0]
        if res12:
            x = (buf[1] << 4) | (buf[2] >> 4)
            y = (buf[3] << 4) | (buf[4] >> 4)
            z = (buf[5] << 4) | (buf[6] >> 4)
        else:
            x, y, z = buf[1], buf[3], buf[5]

        if not raw:
            # get range
            fsr = self._xyz_data_cfg_value & 0x03
            g_ranges = {XYZ_DATA_CFG_FSR_2G: 2,
                        XYZ_DATA_CFG_FSR_4G: 4,
                        XYZ_DATA_CFG_FSR_8G: 8}
            g_range = g_ranges[fsr]
            resolution = 12 if res12 else 8
            gmul = g_range / (2 ** (resolution - 1))
            x = twos_complement(x, resolution) * gmul
            y = twos_complement(y, resolution) * gmul
            z = twos_complement(z, resolution) * gmul

        return {'x': x, 'y': y, 'z': z}

    def get_xyz_ms2(self):
        """Returns the x, y, z values as a dictionary in SI units (m/s^2)."""
        xyz = self.get_xyz(raw=False, res12=True)
        # multiply each xyz value by the standard gravity value
        return {direction: magnitude * STANDARD_GRAVITY
                for direction, magnitude in xyz.items()}

    def set_g_range(self, g_range):
        """Sets the force range (in Gs -- where 1G is the force of gravity).

        Be sure to call `standby()` before using this method and `activate()`
        after using this method.

        :param g_range: The force range in Gs.
        :type g_range: int (acceptable ranges: 2, 4 or 8)
        """
        g_ranges = {2: XYZ_DATA_CFG_FSR_2G,
                    4: XYZ_DATA_CFG_FSR_4G,
                    8: XYZ_DATA_CFG_FSR_8G}
        if g_range in g_ranges:
            self._xyz_data_cfg_value &= 0b11111100
            self._xyz_data_cfg_value |= g_ranges[g_range]
            self.xyz_data_cfg.set(self._xyz_data_cfg_value)

    def set_output_data_rate(self, output_data_rate):
        """Sets the output data rate in Hz.

        Be sure to call `standby()` before using this method and `activate()`
        after using this method.

        :param output_data_rate: The output data rate.
        :type output_data_rate: int (acceptable rates: 800, 400, 200, 100,
                                50, 12.5, 6.25, 1.56)
        """
        output_data_rates = {800: CTRL_REG1_ODR_800,
                             400: CTRL_REG1_ODR_400,
                             200: CTRL_REG1_ODR_200,
                             100: CTRL_REG1_ODR_100,
                             50: CTRL_REG1_ODR_50,
                             12.5: CTRL_REG1_ODR_12_5,
                             6.25: CTRL_REG1_ODR_6_25,
                             1.56: CTRL_REG1_ODR_1_56}
        if output_data_rate in output_data_rates:
            self._ctrl_reg1_value &= 0b11100111
            self._ctrl_reg1_value |= output_data_rates[output_data_rate]
            self.ctrl_reg1.set(self._ctrl_reg1_value)


class MMA8452QRegister(object):
    """An 8 bit register inside an MMA8452Q. Since the native I2C driver
    does not support multiple starts (SMBus) we cannot implement register
    reads.
    """

    def __init__(self, register_address, device_address, i2c_master):
        self.register_address = register_address
        self.device_address = device_address
        self.i2c_master = i2c_master

    def set(self, v):
        self.i2c_master.transaction(
            writing_bytes(self.device_address, self.register_address, v))


def twos_complement(value, bits):
    """Signs a value with an arbitary number of bits."""
    if value >= (1 << (bits - 1)):
        value = -((~value + 1) + (1 << bits))
    return value
