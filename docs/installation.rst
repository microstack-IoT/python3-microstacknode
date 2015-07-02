############
Installation
############
First, make sure you have enabled I2C and SPI by running::

    sudo raspi-config

And then navigating to::

    Advanced Options > I2C > Enable
    Advanced Options > SPI > Enable

Then reboot.

You can install `microstacknode` with either `apt-get` or `pip`.

apt-get
-------
Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update && sudo apt-get upgrade

Install ``microstacknode`` for Python 3 with the following command::

    $ sudo apt-get install python3-microstacknode

pip
---
Make sure `pip` is installed::

    sudo apt-get install python3-pip

Install microstacknode using pip::

    sudo pip-3.2 install microstackcommon microstacknode


Note: Generally, it's best to install packages into a
[virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
when using `pip` so that they remain project specific.

Install `virtualenv`::

    sudo pip-3.2 install virtualenv

Move into your project and create the virtual environment::

    cd my_project_directory/
    virtualenv-3.2 venv

Activate the virtual environment::

    source venv/bin/activate

You should notice that your command prompt has changed. `pip` will now
install all packages into the virtual environment instead of littering
your system files::

    pip install microstackcommon microstacknode

Now you can work on your application with microstack. Once you're done,
deactivate the virtual environment::

    deactivate

You will not be able to use packages installed in the virtual environment
until you activate it again (`source venv/bin/activate`).


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

Automatically Starting GPS
--------------------------
Reconfigure the GPS daemon and choose <yes> when asked if you want to
start `gpsd` automatically (use the defaults for the remaining options)::

    $ sudo dpkg-reconfigure gpsd
