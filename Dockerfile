FROM debian:jessie
MAINTAINER dbrawand@nhs.net

RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install less make wget vim curl
ADD Makefile /usr/local/zippy/Makefile
ADD package-requirements.txt /usr/local/zippy/package-requirements.txt
WORKDIR /usr/local/zippy
RUN make essential
RUN make install-dockerized
RUN make variation-download
RUN make refgene-download
RUN make genome
ADD . /usr/local/zippy
EXPOSE 5000
CMD ["gunicorn","wsgi:app"]
