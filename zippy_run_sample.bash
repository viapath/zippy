#!/bin/bash
sudo yum -y upgrade
sudo yum install less make wget curl vim
make -f Makefile_centos genome #genome index and genome download
#https://ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b147_GRCh37p13/VCF/00-common_all.vcf.gz
make -f Makefile_centos install
#make -f Makefile_centos genome-index
make -f Makefile_centos variation-download
make -f Makefile_centos refgene-download
make -f Makefile_centos webservice