FROM lucioric/zippy:centos1.0.0 
#This dockerfile is crafted to only re install the scripts and the dependencies, but to pull the other data from lucioric/zippy:centos1.0.0
MAINTAINER lucioric


# install zippy
ADD . /zippy
#As the base image is a zippy image, we first need to delete the software part of this image
RUN cd /zippy && make print_flags env_suffix=_docker
RUN cd /zippy && make very_essential env_suffix=_docker
RUN cd /zippy && make cleansoftware env_suffix=_docker
RUN cd /zippy && make cleandb env_suffix=_docker

RUN cd /zippy && make install env_suffix=_docker
RUN cd /zippy && make webservice env_suffix=_docker
# prepare genome
#RUN cd /zippy && make genome-download env_suffix=_docker
#RUN cd /zippy && make genome-index env_suffix=_docker

# get annotation
#RUN cd /zippy && make variation-download env_suffix=_docker
#RUN cd /zippy && make refgene-download env_suffix=_docker

EXPOSE 80

CMD /bin/bash /zippy/zippyd.sh
#The command for executing zippy.py is
# sudo docker run -it lucioric/zippy usr/local/zippy/venv/bin/python /zippy/zippy/zippy.py