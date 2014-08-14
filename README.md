microstack-node
================
Common functions for interacting with Microstack node boards (Accelerometer,
GPS, etc).

Documentation
=============
[http://microstack.github.io/microstack-node/](http://microstack.github.io/microstack-node/)

You can also find the documentation installed at:

    /usr/share/doc/python3-microstack-node/

Install
=======
Make sure you are using the lastest version of Raspbian:

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install `microstack-node` (for Python 3 and 2) with the following command:

    $ sudo apt-get install python{,3}-microstack-node


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
