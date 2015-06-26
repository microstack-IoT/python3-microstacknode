import time
from microstackcommon.i2c import I2CMaster, writing_bytes, writing, reading


DEFAULT_I2C_BUS = 1


class ChecksumFailedError(Exception):
    pass


class SHT21(I2CMaster):
    """SHT21 temperature and humidity sensor."""

    _I2C_ADDRESS = 0x40

    # control constants
    _CMD_SOFTRESET = 0xFE
    _CMD_TEMPERATURE_NO_HOLD = 0xF3
    _CMD_HUMIDITY_NO_HOLD = 0xF5

    def __init__(self, i2c_bus=DEFAULT_I2C_BUS):
        super().__init__(i2c_bus)

    def __enter__(self):
        self = super().__enter__()
        self.reset()
        return self

    def reset(self):
        """Resets the SHT12."""
        self.transaction(
            writing_bytes(self._I2C_ADDRESS, self._CMD_SOFTRESET))
        time.sleep(0.050)

    def get_temperature(self):
        """Reads the temperature from the sensor. This call blocks
        for 250ms to allow the sensor to return the data.
        """
        self.transaction(
            writing_bytes(self._I2C_ADDRESS,
                          self._CMD_TEMPERATURE_NO_HOLD))
        time.sleep(0.250)
        data = self.transaction(reading(self._I2C_ADDRESS, 3))[0]
        if _calculate_checksum(data, 2) != data[2]:
            raise ChecksumFailedError("Temperature checksum failed.")
        else:
            return _get_temperature_from_buffer(data)

    def get_humidity(self):
        """Reads the humidity from the sensor. This call blocks
        for 250ms to allow the sensor to return the data"""
        self.transaction(
            writing_bytes(self._I2C_ADDRESS,
                          self._CMD_HUMIDITY_NO_HOLD))
        time.sleep(0.250)
        data = self.transaction(reading(self._I2C_ADDRESS, 3))[0]
        if _calculate_checksum(data, 2) != data[2]:
            raise ChecksumFailedError("Humidity checksum failed.")
        else:
            return _get_humidity_from_buffer(data)


def _calculate_checksum(data, nbrOfBytes):
    """5.7 CRC Checksum using teh polynomial given in the datasheet"""
    # CRC
    POLYNOMIAL = 0x131 # //P(x)=x^8+x^5+x^4+1 = 100110001
    crc = 0
    #calculates 8-Bit checksum with given polynomial
    for byteCtr in range(nbrOfBytes):
        crc ^= data[byteCtr]
        for bit in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ POLYNOMIAL
            else:
                crc = (crc << 1)
    return crc

def _get_temperature_from_buffer(data):
    """This function reads the first two bytes of data and
    returns the temperature in C by using the following function:
    T = =46.82 + (172.72 * (ST/2^16))
    where ST is the value from the sensor
    """
    unadjusted = (data[0] << 8) + data[1]
    unadjusted *= 175.72
    unadjusted /= 1 << 16 # divide by 2^16
    unadjusted -= 46.85
    return unadjusted


def _get_humidity_from_buffer(data):
    """This function reads the first two bytes of data and returns
    the relative humidity in percent by using the following function:
    RH = -6 + (125 * (SRH / 2 ^16))
    where SRH is the value read from the sensor
    """
    unadjusted = (data[0] << 8) + data[1]
    unadjusted *= 125.0
    unadjusted /= 1 << 16 # divide by 2^16
    unadjusted -= 6
    return unadjusted
