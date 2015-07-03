########
Examples
########

L80 GPS
=======

.. note:: It usually takes about two minutes for the GPS module to get
          a GPS fix (indicated by a red flashing LED on the GPS module).
          Until then, the L80GPS object may throw exceptions.

.. note:: Some commands may take one or more seconds to return. This is becasue
          L80GPS reading the latest data from the serial port which the
          GPS module is connected to. It only updates every second. It is
          normal for ``locus_query_data`` to take a long time to return.

.. todo:: Link to GPS command wiki describing what each of the GP*** do.

Basic GPS (GPGLL is useful for location/time)::

    >>> import microstacknode.hardware.gps.l80gps
    >>> gps = microstacknode.hardware.gps.l80gps.L80GPS()  # creates a GPS object
    >>> gps.get_gprmc()  # get latest GPRMC data as a dictionary
    >>> gps.get_gpvtg()
    >>> gps.get_gpgga()
    >>> gps.get_gpgsa()
    >>> gps.get_gpgsv()
    >>> gps.get_gpgll()
    >>> gps.get_gptxt()

Extra modes::

    >>> gps.standby()
    >>> gps.always_locate()
    >>> gps.sleep()
    >>> gps.set_periodic_normal()  # wakes from sleep or always locate off


LOCUS Data Logging
------------------
The GPS unit can log data to its internal memory without anything
driving it using the LOCUS logging system. The following commands
interface with LOCUS::

    >>> gps.locus_query()       # Query the status of the LOCUS logger
    >>> gps.locus_start()       # Start the logger
    >>> gps.locus_stop()        # Stop the logger
    >>> gps.locus_erase()       # Erase all data items in the log
    >>> gps.locus_query_data()  # Return a list of data items in the logger

For example, you could issue the following command::

    >>> gps.locus_start()

Shutdown/halt the device running Python, go for a walk, reboot, start
Python and then run the following command and receive GPS data for the
walk::

    >>> gps.locus_query_data()

The logger will continue to log GPS data until it runs out of memory, at
which point it will stop. Manually stop the LOCUS logger with::

    >>> gps.locus_stop()


MMA8452 Accelerometer
=====================
::

    >>> import microstacknode.hardware.accelerometer.mma8452q
    >>> accelerometer = microstacknode.hardware.accelerometer.mma8452q.MMA8452Q()
    >>> accelerometer.open()

    >>> accelerometer.get_xyz()
    {'x': 0.00927734375, 'y': 0.00341796875, 'z': 0.49853515625}

    >>> accelerometer.get_xyz(res12=False)  # turn off 12-bit resolution
    {'x': -0.0078125, 'y', -0.0078125, 'z': 0.5078125}


You don't have to call `open()` if you're using the `with` statement::

    import time
    from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q

    with MMA8452Q() as accelerometer:
        while True:
            print(accelerometer.get_xyz())

You can configure the range recorded by the accelerometer and change the
output data rate (how fast the accelerometer is sampled)::

    import time
    from microstacknode.hardware.accelerometer.mma8452q import MMA8452Q

    with MMA8452Q() as accelerometer:
        # change the settings
        accelerometer.standby()  # call standby before changing settings
        accelerometer.set_g_range(2)  # Either 2G, 4G or 8G
        accelerometer.set_output_data_rate(800)
        accelerometer.activate()

        # let the accelerometer settle before reading again
        time.sleep(0.5)

        while True:
            print(accelerometer.get_xyz())


SHT21 Temperature and Humidity Sensor
=====================================
This behaves very similar to the accelerometer::

    >>> from microstacknode.hardware.humiditytemperature.sht21 import SHT21
    >>> sht21 = SHT21()
    >>> sht21.open()
    >>> sht21.get_humidity()
    >>> sht21.get_temperature()

or even using `with` (Python-magic will call `open()`)::

    with SHT21() as htsensor:
        while True:
            humidity = htsensor.get_humidity()
            temperature = htsensor.get_temperature()
            print('Humidity: {:.2f} %RH'.format(humidity))
            print('Temperature: {:.2f}°C'.format(temperature))
            print()
            time.sleep(1)
