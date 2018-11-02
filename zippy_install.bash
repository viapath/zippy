#!/bin/bash
sudo yum -y upgrade
sudo yum install less make wget curl vim git
srv_zippy=/srv/qgen/zippy

qseqdnamatch=`expr match "$(pwd)" '.*\(zippy\)'`
if [[ $qseqdnamatch = "zippy" ]]
then
    echo "Already in zippy folder."
    sudo chmod -R 777 ${srv_zippy}
    git pull origin master
else
    echo "Not in zippy folder."
    sudo mkdir -p ${srv_zippy}
    cd /srv/qgen
    git clone --recursive https://github.com/Lucioric2000/zippy
    sudo chmod -R 777 ${srv_zippy}
    cd zippy
fi

ake cleansoftware
make cleandb
make install
make webservice
make variation-download
make refgene-download
make genome
