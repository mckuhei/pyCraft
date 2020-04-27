#!/bin/sh

VERSION="1.15.2"

wget -O/tmp/mcdata.zip https://apimon.de/mcdata/$VERSION/$VERSION.zip
rm -rf mcdata
mkdir mcdata
unzip /tmp/mcdata.zip -d mcdata
rm /tmp/mcdata.zip
