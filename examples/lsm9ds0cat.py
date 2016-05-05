'''Prints the accelerometer values every second.'''
import time
import datetime
from microstacknode.hardware.accelerometer.lsm9ds0 import LSM9DS0


if __name__ == '__main__':
    # with LSM9DS0(i2c_addr_xm=0x1d, i2c_addr_g=0x6b) as lsm:
    with LSM9DS0() as lsm:
        lsm.enable_temperature()
        lsm.setup_accelerometer()
        lsm.setup_magnetometer()
        lsm.setup_gyroscope()
        while True:
            print("----------------------------------------")
            print(datetime.datetime.now())
            print("Temperature: {}°C".format(lsm.get_temperature()))
            print("Magnetometer: {}".format(lsm.get_magnetometer()))
            print("Accelerometer: {}".format(lsm.get_accelerometer()))
            print("Gyroscope: {}".format(lsm.get_gyroscope()))
            time.sleep(1)
