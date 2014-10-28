"""Calculate the angles required to move the accelerometer in order to
return it to an upright position.
"""
import time
import datetime
from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q


if __name__ == '__main__':
    with MMA8452Q() as accelerometer:
        while True:
            x, y, z = accelerometer.get_xyz()
            x_angle = x * -180
            y_angle = y * -180
            z_angle = 90 - (180 * z)
            print('Angle to upright @ {}:'.format(datetime.datetime.now()))
            print('x:{:.2f}°'.format(x_angle))
            print('y:{:.2f}°'.format(y_angle))
            print('z:{:.2f}°'.format(z_angle))
            print()
            time.sleep(1)
