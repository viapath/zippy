#!/bin/bash
#For modifications, work in the zoppi_install.bash script, because the versioned script
# is overwritten automatically ewhen make archive is executed
zippy_parent_folder=$(pwd)
version=$(cat version.dat)
zippy_folder_title=zippy-${version}
zippy_folder=${zippy_parent_folder}/${zippy_folder_title}
#Tests it it is centos or ubuntu
distro=$(./get_distro.bash)
yum --help&>/dev/null && distro=centos || distro=ubuntu
function install(){
    if [[ $distro = "ubuntu" ]]
    then
        sudo apt-get -y upgrade
        sudo apt-get -y install less make wget curl vim git sudo tar gzip #gunzip
    else
        sudo yum -y upgrade --skip-broken
        sudo yum -y install less make wget curl vim git sudo tar gzip #gunzip
    fi
    sudo chmod -R 777 ${zippy_folder}
    #if [[ $1 = "--fast" ]]
    #then
    make print_flags VERSION=${version} distro=${distro}
    make clean VERSION=${version} distro=${distro}
    make install VERSION=${version} distro=${distro}
    make webservice VERSION=${version} distro=${distro}
    #make import-shipped-refgene VERSION=${version} distro=${distro}
    make annotation VERSION=${version} distro=${distro}
    make genome VERSION=${version} distro=${distro}
    #make unstash-resources VERSION=${version} distro=${distro}
    #else
        #make cleanall recover-resources install webservice resources distro=${distro}
        #make cleanall install webservice resources distro=${distro}
    #fi
    echo To run the server, now go to /usr/local/zippy and execute ´make run´
}
qseqdnamatch=`expr match "$(pwd)" '.*\(${zippy_folder_title}\)'`
if [[ $qseqdnamatch = "${zippy_folder_title}" ]]
then
    echo "Already in zippy folder."
    install $@
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
