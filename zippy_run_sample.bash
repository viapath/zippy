#!/bin/bash
sudo yum -y upgrade
sudo yum install less make wget curl vim
make -f Makefile_centos genome #genome index and genome download
make -f Makefile_centos install
make -f Makefile_centos variation-download
make -f Makefile_centos refgene-download
make -f Makefile_centos webservice