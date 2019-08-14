#!/bin/bash
sudo yum -y upgrade
sudo yum -y install less make wget curl vim git sudo tar gzip #gunzip
zippy_parent_folder=/root
zippy_folder_title=zippy-3.7
zippy_folder=${zippy_parent_folder}/${zippy_folder_title}

function install(){
    sudo chmod -R 777 ${zippy_folder}
    if [[ $1 = "--reset" ]]
    then
        #echo "Writing installer output to zippy_install.log"
        #echo "if you want to monitor the status of the installation, you can use tail -f zippy_install.log"
        #echo ================================================================== &>> zippy_install.log &
        #echo Running make cleanall install webservice annotation genome at $(date):&>> zippy_install.log &
        make cleanall install webservice annotation genome # &>> zippy_install.log &
    else
        make clean
        make install
        make webservice
        make annotation
        make genome
    fi
}
qseqdnamatch=`expr match "$(pwd)" '.*\(${zippy_folder_title}\)'`
if [[ $qseqdnamatch = "${zippy_folder_title}" ]]
then
    echo "Already in zippy folder."
    install
else
    p=$(pwd);
    echo "Not in zippy folder, but in $p."
    sudo mkdir -p ${zippy_parent_folder}
    sudo chmod -R 777 ${zippy_parent_folder}
    rm -rf "${zippy_folder_title}"
    cd "${zippy_parent_folder}" && tar -xvzf ${zippy_folder_title}.tar.gz
    cd "${zippy_folder}" && install $@
    cd $p;
fi
