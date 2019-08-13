#!/bin/bash
sudo yum -y upgrade
sudo yum -y install less make wget curl vim git sudo tar gzip #gunzip
zippy_parent_folder=/root
zippy_folder_title=zippy-3.7
zippy_folder=${zippy_parent_folder}/${zippy_folder_title}

function install(){
    sudo chmod -R 777 ${zippy_folder}
    #make stash-resources
    make clean
    #make cleanall
    make install
    #make unstash-resources
    make webservice
    #make webservice-dev
    sudo -u apache -g apache make annotation
    sudo -u apache -g apache make genome

}
qseqdnamatch=`expr match "$(pwd)" '.*\(${zippy_folder_title}\)'`
if [[ $qseqdnamatch = "${zippy_folder_title}" ]]
then
    echo "Already in zippy folder."
    install
else
    if [[ -d "${zippy_folder}" ]]
    then
        echo "Not in zippy folder, but this folder exists."
        cd "${zippy_folder}"
        install $@
    elif [[ -e "${zippy_folder}" ]]
    then
        echo "File ${zippy_folder} exists but it is not a directory, thus we can not create a directory with that path tho hold the software reposotory. \
        See if it is safe to delete or move it, and then execute again this script."
    else
        echo "Not in zippy folder, and the zippy folder does not exist."
        sudo mkdir -p ${zippy_parent_folder}
        sudo chmod -R 777 ${zippy_parent_folder}
        cd "${zippy_parent_folder}" && tar -xvzf ${zippy_folder_title}.tar.gz
        cd "${zippy_folder}" && install $@
    fi
fi
