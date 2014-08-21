'''Prints the latitude and longitude every second.'''
import time
import microstacknode.gps.l80gps


if __name__ == '__main__':
    gps = microstacknode.gps.l80gps.L80GPS()
    while True:
        gpgll = gps.gpgll
        print('latitude:  {}'.format(gpgll['latitude']))
        print('longitude: {}'.format(gpgll['longitude']))
        print()
        time.sleep(1)
