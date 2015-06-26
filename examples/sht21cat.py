'''Prints the humidity and temperature values every second.'''
import time
from microstacknode.hardware.humiditytemperature.sht21 import SHT21


if __name__ == '__main__':
    with SHT21() as htsensor:
        while True:
            humidity = htsensor.get_humidity()
            temperature = htsensor.get_temperature()
            print('Humidity: {:.2f} %RH'.format(humidity))
            print('Temperature: {:.2f}°C'.format(temperature))
            print()
            time.sleep(1)
