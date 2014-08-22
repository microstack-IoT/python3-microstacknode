#!/bin/bash

## docs
cd docs/
make html
cd -

python setup.py --command-packages=stdeb.command sdist_dsc

version=$(cat microstacknode/version.py | sed 's/.*\([0-9]\.[0-9]\.[0-9]\).*/\1/')
cd deb_dist/microstacknode-$version/

cp {../../dpkg-files,debian}/control
cp {../../dpkg-files,debian}/copyright
cp {../../dpkg-files,debian}/rules

cp {../../dpkg-files,debian}/python-microstacknode.install
# cp {../../dpkg-files,debian}/python-microstacknode.udev
# cp ../../dpkg-files/post-installation.sh debian/python-microstacknode.postinst
# cp ../../bin/post-removal.sh debian/python-microstacknode.postrm

cp {../../dpkg-files,debian}/python3-microstacknode.install
# cp {../../dpkg-files,debian}/python3-microstacknode.udev
# cp ../../dpkg-files/post-installation.sh debian/python3-microstacknode.postinst
# cp ../../bin/post-removal.sh debian/python3-microstacknode.postrm

# examples
ls ../../examples/ | while read example
do
    echo ../../examples/$example >> debian/python-microstacknode.examples
    echo ../../examples/$example >> debian/python3-microstacknode.examples
done

dpkg-buildpackage -us -uc
