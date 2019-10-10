# installation makefile

ZIPPYPATH=/usr/local/zippy
ZIPPYVAR=/var/local/zippy
ZIPPYWWW=/var/www/zippy
VERSION=3.12
SOURCE=zippy
INSTALLER=zippy_install_v6.7.bash

genome=human_g1k_v37
server=nginx#Can be nginx or apache
server_suffix=_privateserver
env_suffix=#Can be an empty string, _dev or _docker

#See which distro does the host have
platform=${python -mplatform}
ifneq (,$(findstring ubuntu,${platform}))
	distro=ubuntu
	WWWGROUP=www-data
	WWWUSER=flask
	PKGINSTALL=apt-get
	distro_suffix=
	ifeq ($(server),nginx)
		serving_packages=nginx
	else
		serving_packages=apache2 apache2.2-common apache2-mpm-prefork apache2-utils libexpat1 ssl-cert libapache2-mod-wsgi
	endif
else
	distro=centos
	WWWGROUP=$(server)
	WWWUSER=$(server)
	PKGINSTALL=yum
	distro_suffix=_centos
	ifeq ($(server),nginx)
		serving_packages=nginx
	else
		serving_packages=mod_wsgi httpd
	endif
endif
ifeq ($(env_suffix),_dev)
	environment=_dev
else
	environment=
endif

# development installs (with mounted volume)
all: install resources webservice

essential: essential_${distro}
very_essential: very_essential_${distro}
install: essential bowtie zippy-install
webservice: webservice_${distro}
stop: stop_${server}_service
#webservice-docker: webservice-docker_${distro}
webservice-dev: webservice-dev_${distro}

deploy: cleansoftware cleandb zippy-install webservice
deploy-dev: cleansoftware cleandb zippy-install webservice-dev



# requirements
essential_ubuntu:
	echo Platform: ${platform}
	apt-get update && apt-get -y upgrade
	sudo apt-get install -y sudo less make wget curl vim apt-utils
	sudo apt-get install -y sqlite3 unzip htop libcurl3-dev #git
	sudo apt-get install -y python-pip python2.7-dev ncurses-dev python-virtualenv
	sudo apt-get install -y libxslt-dev libxml2-dev libffi-dev redis-server mysql-client
	sudo apt-get install -y build-essential libjpeg-dev libfreetype6-dev python-dev python-imaging
	sudo apt-get install -y postgresql postgresql-client postgresql-server-dev-9.4
	# add apache user
	sudo useradd -M $(WWWUSER)
	sudo usermod -s /bin/false $(WWWUSER)
	sudo usermod -L $(WWWUSER)
	sudo adduser $(WWWUSER) $(WWWGROUP)
	# install apache/wsgi
	sudo apt-get install -y $(serving_packages)
	# disable default site
	sudo a2dissite 000-default
essential_centos:
	echo Platform: ${platform}
	sudo yum -y install epel-release
	sudo yum repolist
	sudo yum -y update
	sudo yum install -y sudo wget less make curl vim sqlite unzip htop python2-pip python2-devel ncurses-devel gzip #git
	#apachectl restart graceful
	#kill -USR1 `cat /usr/local/httpd/logs/httpd.pid`
	#kill -USR1 `cat /usr/local/apache2/logs/httpd.pid`
	sudo yum install -y libxslt-devel libxml2-devel libffi-devel redis python-virtualenv
	sudo yum install -y $(serving_packages)
	echo y|sudo yum groupinstall 'Development Tools'
	sudo yum install -y libjpeg-devel freetype-devel python-imaging mysql postgresql postgresql-devel #-client llibcurl3-devel
	#Python-dev(el) no se pone por que ya etá python2-devel y se supone que usamos Python 2
	sudo groupadd -f $(WWWGROUP)
	getent passwd $(WWWUSER)>/dev/null||sudo adduser $(WWWUSER) -g $(WWWGROUP)
	#If the user does exists, does not execute the part of the command. This behavior is
	#achieved because this instruction is taken as a boolean construct (as all in shell finally, that lines have a return code), with || as the operator (OR).
	#If the first command (before the ||) gives a zero return value (if the user exists) there is no need to execute the second part of the statement to 
	#calculate the return value of the line
	sudo usermod -s /bin/false $(WWWUSER)
	sudo usermod -L $(WWWUSER)
	# disable default site
	#a2dissite 000-default
print_flags:
	echo "Installing for platform $(platform), expressed as distro $(distro)"
	echo "Installing for server $(server), location ${server_suffix} and enviromnent ${env_suffix}"


very_essential_ubuntu:
	apt-get -y update
	apt-get -y upgrade
	apt-get install -y sudo
	sudo apt-get install -y sudo less make wget curl vim apt-utils rsync
very_essential_centos:
	yum -y update
	yum -y upgrade
	yum install -y sudo
	sudo yum install -y sudo wget less make curl vim rsync

bowtie:
	wget -c http://netix.dl.sourceforge.net/project/bowtie-bio/bowtie2/2.2.6/bowtie2-2.2.6-linux-x86_64.zip && \
	unzip bowtie2-2.2.6-linux-x86_64.zip && \
	cd bowtie2-2.2.6 && sudo mv bowtie2* /usr/local/bin
	rm -rf bowtie2-2.2.6 bowtie2-2.2.6-linux-x86_64.zip

# zippy setup (will move to distutils in future release)
update-zippy-package:
	sudo rsync -a . $(ZIPPYPATH)
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
zippy-install:
	# virtualenv
	sudo mkdir -p $(ZIPPYPATH)
	cd $(ZIPPYPATH) && sudo /usr/bin/virtualenv venv
	sudo $(ZIPPYPATH)/venv/bin/pip install --upgrade pip
	sudo $(ZIPPYPATH)/venv/bin/pip install Cython==0.24
	sudo $(ZIPPYPATH)/venv/bin/pip install -r requirements.txt
	#sudo rsync -a --exclude-from=.gitignore . $(ZIPPYPATH)
	sudo rsync -a . $(ZIPPYPATH)
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
	cd $(ZIPPYPATH)/download && sudo $(ZIPPYPATH)/venv/bin/python setup.py install
	cd $(ZIPPYPATH) && sudo $(ZIPPYPATH)/venv/bin/python setup.py install
	#sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
	# create empty database
	sudo mkdir -p $(ZIPPYVAR)
	sudo mkdir -p $(ZIPPYVAR)/logs
	sudo mkdir -p $(ZIPPYVAR)/uploads
	sudo mkdir -p $(ZIPPYVAR)/results
	sudo mkdir -p $(ZIPPYVAR)/resources
	sudo touch $(ZIPPYVAR)/zippy.sqlite
	sudo touch $(ZIPPYVAR)/zippy.log
	sudo touch $(ZIPPYVAR)/logs/gunicorn_access.log
	sudo touch $(ZIPPYVAR)/logs/gunicorn_error.log
	sudo touch $(ZIPPYVAR)/zippy.log
	sudo touch $(ZIPPYVAR)/logs
	sudo touch $(ZIPPYVAR)/.blacklist.cache
	sudo touch $(ZIPPYVAR)/zippy.bed
	#sudo chmod 666 $(ZIPPYVAR)/zippy.sqlite $(ZIPPYVAR)/zippy.log $(ZIPPYVAR)/logs $(ZIPPYVAR)/.blacklist.cache $(ZIPPYVAR)/zippy.bed
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)
	sudo chmod -R 777 $(ZIPPYVAR)


#Cleans
cleanall: cleansoftware cleandata cleandb #Deep clean, rarely needed
clean: cleandb cleansoftware
cleansoftware:
	sudo rm -rf $(ZIPPYPATH)
	sudo rm -rf $(ZIPPYWWW)
	sudo rm -f /etc/httpd/conf.d/zippy.conf
cleandata:
	sudo rm -rf $(ZIPPYVAR)
cleandb:
	sudo rm -f $(ZIPPYVAR)/zippy.sqlite
	sudo rm -f $(ZIPPYVAR)/zippy.log
	sudo rm -f $(ZIPPYVAR)/.blacklist.cache
	sudo rm -rf $(ZIPPYVAR)/uploads
	sudo rm -rf $(ZIPPYVAR)/results

# webservice install (production)
webservice_ubuntu:
	# make WWW directories
	mkdir -p $(ZIPPYWWW)
	sudo cp install/zippy$(environment).wsgi $(ZIPPYWWW)/zippy$(environment).wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	cp install/zippy$(environment).hostconfig$(server_suffix) /etc/apache2/sites-available/zippy.conf
	# enable site and restart
	make start_$(server)_service$(env_suffix)
	#Opens the port 80 in the firewall in the system, for public access
	#Disable SELINUX, this disabling is full while we don't know how to open only the sippy directories to SELINUX.
	sudo firewall-cmd --zone=public --add-service=http --permanent&&sudo firewall-cmd --reload||echo "You don't have a firewall running"
	sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent&&sudo firewall-cmd --reload||echo "You don't have a firewall running"
	sudo setenforce 0||echo "Could not activate SELINUX properly"

# webservice install (production)
webservice_centos:
	# make WWW directories
	sudo mkdir -p $(ZIPPYWWW)
	sudo cp install/zippy$(environment).wsgi $(ZIPPYWWW)/zippy$(environment).wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# enable site and restart
	make start_$(server)_service$(env_suffix)

start_apache_service:
	# enable site and restart
	#a2ensite zippy
	# apache WSGI config
	sudo cp install/zippy$(environment).hostconfig$(distro_suffix)$(server_suffix) /etc/httpd/conf.d/zippy.conf
	sudo ln -sf /etc/apache2/sites-available/zippy.conf /etc/apache2/sites-enabled/zippy.conf
	#sudo echo "ServerName localhost" > /etc/httpd/conf.d/zippy_servernameconf.conf
	#/etc/init.d/apache2 start
	/etc/init.d/apache2 restart
	#Opens the port 80 in the firewall in the system, for public access
	#Disable SELINUX, this disabling is full while we don't know how to open only the sippy directories to SELINUX.
	sudo firewall-cmd --zone=public --add-service=http --permanent&&sudo firewall-cmd --reload||echo "You don't have a firewall running"
	sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent&&sudo firewall-cmd --reload||echo "You don't have a firewall running"
	sudo setenforce 0||echo "Could not activate SELINUX properly"

start_apache_service_docker:
	# enable site and restart
	#a2ensite zippy
	# apache WSGI config
	sudo cp install/zippy$(environment).hostconfig$(distro_suffix)$(server_suffix) /etc/httpd/conf.d/zippy.conf
	sudo ln -sf /etc/apache2/sites-available/zippy.conf /etc/apache2/sites-enabled/zippy.conf

enable_nginx_service:
	sudo systemctl enable zippy
disable_nginx_service:
	sudo systemctl disable zippy
start_nginx_service:
	# enable site and restart
	#sudo cp install/zippy /etc/nginx/sites-available/zippy
	#sudo ln -sf /etc/nginx/sites-available/zippy /etc/nginx/sites-enabled/zippy
	#ls -lRt /etc/nginx
	sudo cp install/zippy /etc/nginx/conf.d/zippy
	sudo cp install/zippy.service /etc/systemd/system/zippy.service
	sudo cp install/zippy.socket /etc/systemd/system/zippy.socket
	sudo systemctl daemon-reload
	sudo systemctl restart nginx
	sudo systemctl restart zippy
	#Opens the port 80 in the firewall in the system, for public access
	#Disable SELINUX, this disabling is full while we don't know how to open only the sippy directories to SELINUX.
	sudo firewall-cmd --zone=public --add-service=http --permanent&&sudo firewall-cmd --reload||echo "You don't have a firewall running"
	sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent&&sudo firewall-cmd --reload||echo "You don't have a firewall running"
	sudo setenforce 0||echo "Could not activate SELINUX properly"

start_nginx_service_docker:
	# enable site and restart
	#sudo cp install/zippy /etc/nginx/sites-available/zippy
	#sudo ln -sf /etc/nginx/sites-available/zippy /etc/nginx/sites-enabled/zippy
	ls -lRt /etc/nginx
	sudo cp install/zippy /etc/nginx/conf.d/zippy
	sudo cp install/zippy.service /etc/systemd/system/zippy.service
	sudo cp install/zippy.socket /etc/systemd/system/zippy.socket

stop_apache_service:
	/etc/init.d/apache2 stop

stop_nginx_service:
	# enable site and restart
	sudo ln -sf /etc/nginx/sites-available/zippy /etc/nginx/sites-enabled/zippy
	#/etc/init.d/apache2 start
	sudo systemctl stop nginx
	sudo systemctl stop zippy
	sudo systemctl stop zippy.socket

# Webservers
gunicorn:
	source /usr/local/zippy/venv/bin/activate && gunicorn --bind 0.0.0.0:8000 wsgi:app
run:
	source /usr/local/zippy/venv/bin/activate && export FLASK_DEBUG=1 && export FLASK_ENV=development && export FLASK_APP=zippy && python run.py
runp:
	source /usr/local/zippy/venv/bin/activate && python run.py
zippy:
	source /usr/local/zippy/venv/bin/activate && cd /usr/local/zippy/zippy && python zippy.py $@


#### genome resources
import-shipped-resources:
	# Copy resource files
	#sudo mkdir -p $(ZIPPYVAR)/resources
	rsync -avPp resources $(ZIPPYVAR)
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)
import-shipped-refgene:
	# Copy resource files
	#sudo mkdir -p $(ZIPPYVAR)/resources
	rsync -avPp resources/refGene $(ZIPPYVAR)/resources/refGene
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)
stash-resources:
	# Copy resource files
	echo Stashing resources
	sudo mkdir -p /srv/zippy_resources
	sudo cp -i $(ZIPPYVAR)/resources/* /srv/zippy_resources/
	sudo chown -R $(WWWUSER):$(WWWGROUP) /srv/zippy_resources
recover-resources:
	# Copy resource files
	echo Unstashing resources
	#sudo ln -s /srv/zippy_resources $(ZIPPYVAR)/resources
	sudo mkdir -p $(ZIPPYVAR)/resources
	sudo cp -i /srv/zippy_resources/* $(ZIPPYVAR)/resources/
	#for file in $(ls /srv/zippy_resources);
	#do
	#	sudo rm $(ZIPPYVAR)/$file
	#	sudo ln -s /srv/zippy_resources/$file $(ZIPPYVAR)/$file
	#done
	#sudo mv /srv/zippy_resources/* $(ZIPPYVAR)/resources/
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

resources: genome annotation

genome: genome-download genome-index

genome-download:
	source /usr/local/zippy/venv/bin/activate && cd $(ZIPPYPATH) && python download_resources.py $(ZIPPYVAR)/resources/${genome}.fasta http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/${genome}.fasta.gz
	source /usr/local/zippy/venv/bin/activate && cd $(ZIPPYPATH) && python download_resources.py $(ZIPPYVAR)/resources/${genome}.fasta.fai http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/${genome}.fasta.fai
	sudo chmod 644 $(ZIPPYVAR)/resources/*
	sudo chmod 755 $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

genome-index:
	ls $(ZIPPYVAR)/resources/${genome}.bowtie.rev.2.bt2 &>/dev/null && ( \
		echo bowtie file $(ZIPPYVAR)/resources/${genome}.bowtie exists, thus not running bowtie command ) || \
		( cd $(ZIPPYVAR)/resources; /usr/local/bin/bowtie2-build ${genome}.fasta ${genome}.bowtie )
	sudo chmod 644 $(ZIPPYVAR)/resources/*
	sudo chmod 755 $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

annotation: variation-download refgene-download

variation-download:
	#The files specified by the following commands did not exist as of 30 th, July, 2018, so that were updated by the later version present: b151_GRCh37p13
	sudo mkdir -p $(ZIPPYVAR)/resources && cd $(ZIPPYVAR)/resources && \
	( ls 00-common_all.vcf.gz &>/dev/null && echo 00-common_all.vcf.gz already found || wget -c ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/00-common_all.vcf.gz )
	cd $(ZIPPYVAR)/resources && wget -c ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/00-common_all.vcf.gz.tbi
	

refgene-download:
	sudo firewall-cmd --zone=public --add-port=3306/tcp &&sudo firewall-cmd --reload||echo "You didn't have the port 3306 blocked"
	(cd $(ZIPPYVAR)/resources && ls refGene &>/dev/null) && echo refGene file exists || \
	mysql --user=genome --host=genome-mysql.cse.ucsc.edu -A -N -D hg19 -P 3306 \
	-e "SELECT DISTINCT r.bin,CONCAT(r.name,'.',i.version),c.ensembl,r.strand, r.txStart,r.txEnd,r.cdsStart,r.cdsEnd,r.exonCount,r.exonStarts,r.exonEnds,r.score,r.name2,r.cdsStartStat,r.cdsEndStat,r.exonFrames FROM refGene as r, hgFixed.gbCdnaInfo as i, ucscToEnsembl as c WHERE r.name=i.acc AND c.ucsc = r.chrom ORDER BY r.bin;" > refGene

archive:
	p=`pwd` && rm -f $$p/$(SOURCE)-$(VERSION).tar.gz && tar --transform="s@^@$(SOURCE)-$(VERSION)/@" -cvzf $$p/$(SOURCE)-$(VERSION).tar.gz *

gitarchive:
	@echo Running git archive...
	@use HEAD if tag doesn't exist yet, so that development is easier...
	@rm -f $$p/$(SOURCE)-$(VERSION).tar.gz
	@git archive  --prefix=$(SOURCE)-$(VERSION)/ -o $(SOURCE)-$(VERSION).tar $(VERSION) 2> /dev/null || (echo 'Warning: $(VERSION) does not exist.' && git archive --prefix=$(SOURCE)-$(VERSION)/ -o $(SOURCE).tar HEAD)
	@#TODO: if git archive had a --submodules flag this would easier!
	@echo Running git archive submodules...
	@#I thought i would need --ignore-zeros, but it doesn't seem necessary!
	p=`pwd` && (echo .; git submodule foreach) | while read entering path; do \
		temp="$${path%\'}"; \
		temp="$${temp#\'}"; \
		path=$$temp; \
		[ "$$path" = "" ] && continue; \
		(cd $$path && git archive --prefix=$(SOURCE)-$(VERSION)/ HEAD > $$p/tmp.tar && tar --concatenate --file=$$p/$(SOURCE)-$(VERSION).tar $$p/tmp.tar && rm $$p/tmp.tar); \
	done && gzip -f $$p/$(SOURCE)-$(VERSION).tar

toroot:
	sudo cp -f $(SOURCE)-$(VERSION).tar.gz /root/$(SOURCE)-$(VERSION).tar.gz
	sudo cp -f $(INSTALLER) /root/$(INSTALLER)
	sudo chmod +x /root/$(INSTALLER)
cleanrootinstallers:
	sudo rm -rf /root/zippy*
#sudo firewall-cmd --zone=public --list-all
#sudo firewall-cmd --zone=public --add-port=5000/tcp
#sudo firewall-cmd --zone=public --add-service=http
#sudo firewall-cmd --reload
