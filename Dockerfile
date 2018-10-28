#FROM lucioric/zippy:centos1.0.0 
#This dockerfile is crafted to only re install the scripts and the dependencies, but to pull the other data from lucioric/zippy:centos1.0.0
MAINTAINER lucioric

RUN yum -y install less make wget curl vim
#As the base image is a zippy image, we first need to delete the software part of this image
RUN cd /zippy && make -f Makefile_centos cleansoftware
RUN cd /zippy && make -f Makefile_centos cleandb

# install zippy
ADD . /zippy

RUN cd /zippy && make -f Makefile_centos install
RUN cd /zippy && make -f Makefile_centos webservice-docker
# prepare genome
#RUN cd /zippy && make -f Makefile_centos genome-download
#RUN cd /zippy && make -f Makefile_centos genome-index

# get annotation
#RUN cd /zippy && make -f Makefile_centos variation-download
#RUN cd /zippy && make -f Makefile_centos refgene-download

EXPOSE 80

CMD /bin/bash /zippy/zippyd_CentOS7.sh
#The path of zippy.py is
# sudo docker run -it lucioric/zippy usr/local/zippy/venv/bin/python /zippy/zippy/zippy.py