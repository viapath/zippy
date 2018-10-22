FROM centos:centos7.3.1611
MAINTAINER lucioric

RUN yum -y install less make wget curl vim
# install zippy
ADD . /zippy

RUN cd /zippy && make -f Makefile_centos install
RUN cd /zippy && make -f Makefile_centos webservice_docker
RUN systemctl restart httpd
# prepare genome
RUN cd /zippy && make -f Makefile_centos genome-download
RUN cd /zippy && make -f Makefile_centos genome-index

# get annotation
RUN cd /zippy && make -f Makefile_centos variation-download
RUN cd /zippy && make -f Makefile_centos refgene-download

EXPOSE 80

CMD /bin/bash /zippy/zippyd.sh
#The path of zippy.py is
# sudo docker run -it lucioric/zippy usr/local/zippy/venv/bin/python /zippy/zippy/zippy.py