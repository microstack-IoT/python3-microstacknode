'''Prints the accelerometer values every second.'''
import time
import datetime
from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q


G_RANGE = 2
INTERVAL = 0.5  # seconds

if __name__ == '__main__':
    with MMA8452Q() as accelerometer:
        # configure
        accelerometer.standby()
        accelerometer.set_g_range(G_RANGE)
        accelerometer.activate()
        print("g = {}".format(G_RANGE))
        time.sleep(INTERVAL)  # settle

        # print data
        while True:
            rx, ry, rz = accelerometer.get_xyz(raw=True)
            gx, gy, gz = accelerometer.get_xyz()
            mx, my, mz = accelerometer.get_xyz_ms2()
            print("----")
            print(datetime.datetime.now())
            print('  raw | x: {}, y: {}, z: {}'.format(rx, ry, rz))
            print('    G | x: {:.2f}, y: {:.2f}, z: {:.2f}'.format(gx, gy, gz))
            print('m/s^2 | x: {:.2f}, y: {:.2f}, z: {:.2f}'.format(mx, my, mz))
            time.sleep(INTERVAL)
