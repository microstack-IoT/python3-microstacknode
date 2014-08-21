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

Basic GPS::

    >>> import microstacknode.gps.l80gps
    >>> gps = microstacknode.gps.l80gps.L80GPS()  # creates a GPS object
    >>> gps.gpgll  # print the latest GPGLL data (errors if poor reception)

LOCUS data logging::

    >>> gps.locus_query()       # Query the status of the LOCUS logger
    >>> gps.locus_start()       # Start the logger
    >>> gps.locus_stop()        # Stop the logger
    >>> gps.locus_erase()       # Erase all data items in the log
    >>> gps.locus_query_data()  # Return a list of data items in the logger


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
