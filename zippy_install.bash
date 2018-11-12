#!/bin/bash
sudo yum -y upgrade
sudo yum -y install less make wget curl vim git sudo
srv_zippy=/srv/qgen/zippy

qseqdnamatch=`expr match "$(pwd)" '.*\(zippy\)'`
if [[ $qseqdnamatch = "zippy" ]]
then
    echo "Already in zippy folder."
    sudo chmod -R 777 ${srv_zippy}
    git pull origin master
    make stash-resources
    #make cleansoftware
    #make cleandb
    make cleanall
    make install
    make unstash-resources
    make webservice
    make annotation
    make genome
else
    if [[ -d "${srv_zippy}" ]]
    then
        echo "Not in zippy folder, but this folder exists."
        cd "${srv_zippy}" && ./zippy_install.bash $@
        exit
    elif [[ -e "${srv_zippy}" ]]
    then
        echo "File ${srv_zippy} exists but it is not a directory, thus we can not create a directory with that path tho hold the software reposotory. \
        See if it is safe to delete or move it, and then execute again this script."
    else
        echo "Not in zippy folder, and the zippy folder does not exist."
        sudo mkdir -p /srv/qgen
        sudo chmod -R 777 /srv/qgen
        cd /srv/qgen && git clone --recursive https://github.com/Lucioric2000/zippy
        cd "${srv_zippy}" && ./zippy_install.bash $@
    fi
fi
