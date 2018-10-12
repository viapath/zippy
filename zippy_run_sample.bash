#!/bin/bash
sudo yum -y upgrade
sudo yum install less make wget curl vim
make -f Makefile_centos genome
make -f Makefile_centos install
#make -f Makefile_centos genome-index
make -f Makefile_centos variation-download
make -f Makefile_centos refgene-download