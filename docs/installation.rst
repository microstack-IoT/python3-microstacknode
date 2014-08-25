############
Installation
############
Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install ``microstack-node`` (for Python 3 and 2) with the following
command::

    $ sudo apt-get install python{,3}-microstack-node

GPS
===
The GPS uses the serial port which is usually configured to output logging
data from the Raspberry Pi (for debugging). This needs to be disabled
before the GPS can be used.

Comment out the following line in `/etc/inittab` by putting a hash in
front of it so that it goes from this::

    T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100

To this::

    #T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100

Also, remove all references to ttyAMA0 in `/boot/cmdline.txt` so that it
goes from this::

    dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait

to this::

    dwc_otg.lpm_enable=0 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait

You might also want to install standard GPS software::

    $ sudo apt-get install gpsd gpsd-clients python-gps

Automatically Starting GPS
--------------------------
Reconfigure the GPS daemon and choose <yes> when asked if you want to
start `gpsd` automatically (use the defaults for the remaining options)::

    $ sudo dpkg-reconfigure gpsd

Testing
=======
Accelerometer
-------------
Dump accelerometer data with::

    $ python3 /usr/share/doc/python3-microstack-node/examples/accelcat.py

GPS
---
Dump GPS data::

    $ python3 /usr/share/doc/python3-microstack-node/examples/gpscat.py

or::

    $ sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock

or::

    $ cgps -s