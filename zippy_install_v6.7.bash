#!/bin/bash
sudo yum -y upgrade
sudo yum -y install less make wget curl vim git sudo tar gzip #gunzip
zippy_parent_folder=/root
zippy_folder_title=zippy-3.11
zippy_folder=${zippy_parent_folder}/${zippy_folder_title}

function install(){
    sudo chmod -R 777 ${zippy_folder}
    #if [[ $1 = "--fast" ]]
    #then
    make clean
    make install
    make webservice
    make import-shipped-refgene
    make annotation
    make genome
    #else
        #make cleanall recover-resources install webservice resources
        #make cleanall install webservice resources
    #fi
    echo To run the server, now go to /usr/local/zippy
    echo and execute ´make run´
    echo ****Bioinformatics is enjoyable****
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
