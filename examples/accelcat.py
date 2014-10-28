'''Prints the accelerometer values every second.'''
import time
from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q


if __name__ == '__main__':
    with MMA8452Q() as accelerometer:
        while True:
            x, y, z = accelerometer.get_xyz()
            print('x: {:.2f}, y: {:.2f}, z: {:.2f}'.format(x, y, z))
            time.sleep(0.5)
