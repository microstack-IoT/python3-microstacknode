"""Calculate the angles required to move the accelerometer in order to
return it to an upright position.
"""
import time
import datetime
from microstacknode.accelerometer.mma8452q import MMA8452Q


if __name__ == '__main__':
    with MMA8452Q() as accelerometer:
        while True:
            x, y, z = accelerometer.get_xyz()
            x_angle = x * -180
            y_angle = y * -180
            z_angle = 90 - (180 * z)
            print('Angle to upright @ {}:'.format(datetime.datetime.now()))
            print('x:{}°'.format(x_angle))
            print('y:{}°'.format(y_angle))
            print('z:{}°'.format(z_angle))
            print()
            time.sleep(0.5)
