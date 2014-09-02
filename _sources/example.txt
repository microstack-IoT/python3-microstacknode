########
Examples
########

L80 GPS
=======

.. note:: It usually takes about two minutes for the GPS module to get
          a GPS fix. Until then, the L80GPS object may throw exceptions.

.. note:: Some commands may take one or more seconds to return. This is becasue
          L80GPS reading the latest data from the serial port which the
          GPS module is connected to. It only updates every second. It is
          normal for ``locus_query_data`` to take a long time to return.

.. todo:: Link to GPS command wiki describing what each of the GP*** do.

Basic GPS (GPGLL is useful for location/time)::

    >>> import microstacknode.gps.l80gps
    >>> gps = microstacknode.gps.l80gps.L80GPS()  # creates a GPS object
    >>> gps.gprmc  # print the latest GPRMC data (errors if poor reception)
    >>> gps.gpvtg
    >>> gps.gpgga
    >>> gps.gpgsa
    >>> gps.gpgsv
    >>> gps.gpgll
    >>> gps.gptxt

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

    >>> import microstacknode.accelerometer.mma8452q
    >>> accelerometer = microstacknode.accelerometer.mma8452q.MMA8452Q()
    >>> accelerometer.init()

    >>> accelerometer.get_xyz()
    (0.00927734375, 0.00341796875, 0.49853515625)

    >>> accelerometer.get_xyz(res12=False)  # turn off 12-bit resolution
    (-0.0078125, -0.0078125, 0.5078125)
