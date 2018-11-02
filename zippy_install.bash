#!/bin/bash
sudo yum -y upgrade
sudo yum install less make wget curl vim git sudo
srv_zippy=/srv/qgen/zippy

qseqdnamatch=`expr match "$(pwd)" '.*\(zippy\)'`
if [[ $qseqdnamatch = "zippy" ]]
then
    echo "Already in zippy folder."
    sudo chmod -R 777 ${srv_zippy}
    git pull origin master
	make cleansoftware
	make cleandb
	make install
	make webservice
	make annotation
	make genome
else
    echo "Not in zippy folder."
    sudo mkdir -p ${srv_zippy}
    cd /srv/qgen
    git clone --recursive https://github.com/Lucioric2000/zippy
    sudo chmod -R 777 ${srv_zippy}
    cd zippy
    ./zippy_install.bash $@
fi
