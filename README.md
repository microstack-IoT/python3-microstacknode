microstack-node
================
Common functions for interacting with Microstack node boards (Accelerometer,
GPS, etc).

Documentation
=============
[http://python3-microstacknode.readthedocs.org](http://python3-microstacknode.readthedocs.org)


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
