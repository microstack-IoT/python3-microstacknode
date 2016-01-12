'''Prints the latitude and longitude every second.'''
import time
from microstacknode.hardware.gps.l80gps import L80GPS


if __name__ == '__main__':
    gps = L80GPS()
    while True:
        gpgll = gps.get_gpgll()
        print('latitude:  {}'.format(gpgll['latitude']))
        print('longitude: {}'.format(gpgll['longitude']))
        print()
        time.sleep(1)
