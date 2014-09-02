microstack-node
================
Common functions for interacting with Microstack node boards (Accelerometer,
GPS, etc).

Documentation
=============
[http://microstack-iot.github.io/](http://microstack-iot.github.io/)

You can also find the documentation installed at:

    /usr/share/doc/python3-microstacknode/

Install
=======
Make sure you are using the lastest version of Raspbian:

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install `microstacknode` for Python 3 with the following command:

    $ sudo apt-get install python3-microstacknode


Enable Serial Port on Raspberry Pi for GPS
==========================================
1. Disable serial port login
   Comment out `T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100` in
   `/etc/inittab`

2. Disable bootup info. Remove references to `ttyAMA0` in `/boot/cmdline.txt`.

  That is, change from:

       dwc_otg.lpm_enable=0 console=ttyAMA0,115200 kgdboc=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p6 rootfstype=ext4 elevator=deadline rootwait

   to:

        dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p6 rootfstype=ext4 elevator=deadline rootwait

3. Reboot.


Controlling the on board OK LED (Raspberry Pi)
==============================================

    # disable mmc0 for led
    echo none >/sys/class/leds/led0/trigger

    # enable mmc0 for led
    echo mmc0 >/sys/class/leds/led0

    # turn on led
    echo 1 >/sys/class/leds/led0

    # turn off led
    echo 0 >/sys/class/leds/led0
