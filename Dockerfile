# bare container without resources (must be mounted into /var/local/zippy/resources)
FROM debian:jessie as bare
LABEL maintainer="dbrawand@nhs.net"
RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install less make wget vim curl
ADD Makefile /usr/local/zippy/Makefile
ADD package-requirements.txt /usr/local/zippy/package-requirements.txt
ADD run.py /usr/local/zippy
ADD LICENSE /usr/local/zippy
ADD resources /usr/local/zippy/resources
ADD gunicorn.conf.py /usr/local/zippy
ADD zippy /usr/local/zippy/zippy
WORKDIR /usr/local/zippy
RUN make install-dockerized
EXPOSE 5000
CMD ["gunicorn","zippy:app"]

## monolithic image with all genome resources
FROM bare as mono
ADD prebuilt_resources/* /var/local/zippy/resources
RUN make resources
