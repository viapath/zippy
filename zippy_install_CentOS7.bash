#!/bin/bash
sudo yum -y upgrade
sudo yum install less make wget curl vim git
srv_zippy=/srv/zippy

qseqdnamatch=`expr match "$(pwd)" '.*\(zippy\)'`
if [[ $qseqdnamatch = "zippy" ]]
then
    echo "Already in zippy folder."
    sudo chmod -R 777 ${srv_zippy}
else
    echo "Not in zippy folder."
    sudo mkdir -p ${srv_zippy}
    cd ${srv_zippy}
    sudo chmod -R 777 ${srv_zippy}
    git clone --recursive https://github.com/Lucioric2000/zippy
    cd zippy
fi

make -f Makefile_centos install
make -f Makefile_centos webservice
make -f Makefile_centos variation-download
make -f Makefile_centos refgene-download
make -f Makefile_centos genome #genome index and genome download
