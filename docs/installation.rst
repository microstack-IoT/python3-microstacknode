############
Installation
############
Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install ``microstack-node`` (for Python 3 and 2) with the following command::

    $ sudo apt-get install python{,3}-microstack-node

Test by running one of the example programs which dump IO board data::

    $ python3 /usr/share/doc/python3-microstack-node/examples/accelcat.py
    $ python3 /usr/share/doc/python3-microstack-node/examples/gpscat.py
