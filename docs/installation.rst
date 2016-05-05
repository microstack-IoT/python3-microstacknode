############
Installation
############
First, make sure you have enabled I2C and SPI by running::

    sudo raspi-config

and then navigating to::

    Advanced Options > Would you like the I2C interface to be enabled? > Yes
    Would you like the I2C kernel module to be loaded by default? > Yes

and::

    Advanced Options > Would you like the SPI interface to be enabled? > Yes
    Would you like the SPI kernel module to be loaded by default? > Yes

Then reboot.

You can install `microstacknode` with either `apt-get` or `pip`.

Installing with `apt-get`
-------------------------
Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update && sudo apt-get upgrade

Install ``microstacknode`` for Python 3 with the following command::

    $ sudo apt-get install python3-microstacknode

Installing with `pip`
---------------------
.. warning:: Do not install `microstacknode` with both `apt-get` and `pip`
             as unexpected things will happen. Consider using virtual
             environments.

Make sure `pip` is installed::

    sudo apt-get install python3-pip

Install microstacknode using pip::

    sudo pip3 install microstacknode


GPS
===
The GPS uses the serial port. By default it is configured to output the
login shell. You must disable this before GPS will work. To do so, run::

    sudo raspi-config

Navigate to ``Advanced Options`` > ``Serial``, disable the login shell
and then reboot.

.. note:: If you're using a Raspberry Pi 3 you will also need to fix the
          CPU `core_freq` at 250 otherwise the serial port baud rate
          will not stay constant. To do this add ``core_freq=250`` to
          ``/boot/config.txt``.


Testing
=======
Accelerometer
-------------
Dump accelerometer data with::

    $ python3 /usr/share/doc/python3-microstacknode/examples/accelcat.py

GPS
---
Dump GPS data::

    $ python3 /usr/share/doc/python3-microstacknode/examples/gpscat.py


Other GPS Software
==================
You might also want to install standard GPS software::

    $ sudo apt-get install gpsd gpsd-clients python-gps

You can dump GPS data with::

    $ sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock

or::

    $ cgps -s

Replace ``/dev/ttyAMA0`` with ``/dev/ttyS0`` if you're using a
Raspberry Pi 3.


Automatically Starting GPS
==========================
Reconfigure the GPS daemon and choose <yes> when asked if you want to
start `gpsd` automatically (use the defaults for the remaining options)::

    $ sudo dpkg-reconfigure gpsd
