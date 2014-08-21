'''Prints the accelerometer values every second.'''
import time
import microstacknode.accelerometer.mma8452q


if __name__ == '__main__':
    accelerometer = microstacknode.accelerometer.mma8452q.MMA8452Q()
    while True:
        x, y, z = accelerometer.get_xyz()
        print('x: {}, y: {}, z: {}'.format(x, y, z))
        time.sleep(0.5)
