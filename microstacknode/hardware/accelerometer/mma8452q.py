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


class MMA8452Q(object):
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
        self.i2c_master = I2CMaster(i2c_bus)
        self.i2c_address = i2c_address

        self.int_source = MMA8452QRegister(INT_SOURCE, self)
        self.xyz_data_cfg = MMA8452QRegister(XYZ_DATA_CFG, self)
        self.ctrl_reg1 = MMA8452QRegister(CTRL_REG1, self)
        self.off_x = MMA8452QRegister(OFF_X, self)
        self.off_y = MMA8452QRegister(OFF_Y, self)
        self.off_z = MMA8452QRegister(OFF_Z, self)
        # need to finish adding registers...

    def init(self):
        self.i2c_master.open()
        self.standby()
        self.ctrl_reg1.value = CTRL_REG1_ODR_800  # set sample rate 800Hz
        self.xyz_data_cfg.value = XYZ_DATA_CFG_FSR_2G  # +0.5 == 1G
        self.activate()

    def close(self):
        self.i2c_master.close()

    def reset(self):
        self.ctrl_reg1.value = 0

    def activate(self):
        self.ctrl_reg1.value |= CTRL_REG1_SET_ACTIVE

    def standby(self):
        self.ctrl_reg1.value &= 0xff ^ CTRL_REG1_SET_ACTIVE

    def get_xyz(self, raw=False, res12=True):
        """Returns the values of the XYZ registers. By default it returns
        signed values at 12-bit resolution. You can specify a lower resolution
        (8-bit) or request the raw register values. Signed values are
        between the range -1 to +1 which are relative to the configured
        Full Scale Range (FSR).

        Since we can't read arbitary registers from this chip over I2C
        (because there is no decent SMBus implementation, in Python 3 at
        least) we have to just read the first 7 registers and pull the
        XYZ data from that.

        Notes:

        - 12-bit resolution from OUT MSB and OUT LSB registers:

            +--------+-----------------+
            | msb    | lsb             |
            +--------+--------+--------+
            | 8 bits | 4 bits | 4 bits |
            +--------+--------+--------+
            | value (12 bits) | unused |
            +--------+--------+--------+

        - 8-bit resolution just from OUT MSB:

            +--------+--------+
            | msb    | lsb    |
            +--------+--------+
            | 8 bits | 8 bits |
            +--------+--------+
            | value  | unused |
            +--------+--------+

        :param raw: If True: return raw, unsigned data, else: sign values
        :type raw: boolean (default: False)
        :param res12: If True: read 12-bit resolution, else: 8-bit
        :type res12: boolean (default: True)
        """
        buf = self.i2c_master.transaction(reading(self.i2c_address, 7))[0]
        # status = buf[0]
        if res12:
            x = (buf[1] << 4) | (buf[2] >> 4)
            y = (buf[3] << 4) | (buf[4] >> 4)
            z = (buf[5] << 4) | (buf[6] >> 4)
        else:
            x, y, z = buf[1], buf[3], buf[5]

        if not raw:
            fsr = self.xyz_data_cfg.value & 0x03  # get range
            if fsr == XYZ_DATA_CFG_FSR_2G:
                g_range = 2
            elif fsr == XYZ_DATA_CFG_FSR_4G:
                g_range = 4
            elif fsr == XYZ_DATA_CFG_FSR_8G:
                g_range = 8

            resolution = 12 if res12 else 8
            gmul = g_range / (2 ** resolution)
            x = twos_complement(x, resolution) * gmul
            y = twos_complement(y, resolution) * gmul
            z = twos_complement(z, resolution) * gmul

        return x, y, z


class MMA8452QRegister(object):
    """An 8 bit register inside an MMA8452Q. Since the native I2C driver
    does not support multiple starts (SMBus) we cannot fully implement
    register reads. Therefore the register value is stored locally.
    """
    def __init__(self, address, chip):
        self._value = 0
        self.address = address
        self.chip = chip

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self.chip.i2c_master.transaction(writing_bytes(self.chip.i2c_address,
                                                       self.address,
                                                       v))
        self._value = v

    def all_high(self):
        self.value = 0xff

    def all_low(self):
        self.value = 0

    def toggle(self):
        self.value = 0xff ^ self.value


def twos_complement(value, bits):
    """Signs a value with an arbitary number of bits."""
    if value >= (1 << (bits - 1)):
        value = -((~value + 1) + (1 << bits))
    return value
