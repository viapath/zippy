# installation makefile

ZIPPYPATH=/usr/local/zippy
ZIPPYVAR=/var/local/zippy
ZIPPYWWW=/var/www/zippy

genome=human_g1k_v37

#See which distro does the host have
platform=$(python -mplatform)
ifneq (,$(findstring ubuntu,${platform}))
	distro=ubuntu
	WWWGROUP=www-data
	WWWUSER=flask
else
	distro=centos
	WWWGROUP=apache
	WWWUSER=apache
endif
# production install
release: install_${distro} resources webservice

# development installs (with mounted volume)
all: install resources

zippy-install: zippy-install_${distro}
essential: essential_${distro}
very_essential: very_essential_${distro}
install: essential bowtie zippy-install
webservice: webservice_${distro}
webservice-docker: webservice-docker_${distro}
webservice-dev: webservice-dev_${distro}

deploy: zippy-install webservice



# requirements
essential_ubuntu:
	echo Platform: ${platform}
	apt-get update && apt-get -y upgrade
	sudo apt-get install -y sudo less make wget curl vim apt-utils
	sudo apt-get install -y sqlite3 unzip git htop libcurl3-dev
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
	sudo apt-get install -y apache2 apache2.2-common apache2-mpm-prefork apache2-utils libexpat1 ssl-cert
	sudo apt-get install -y libapache2-mod-wsgi
	# disable default site
	sudo a2dissite 000-default
essential_centos:
	echo Platform: ${platform}
	sudo yum -y install epel-release
	sudo yum repolist
	sudo yum -y update
	sudo yum install -y sudo wget less make curl vim sqlite unzip git htop python2-pip python2-devel ncurses-devel
	#apachectl restart graceful
	#kill -USR1 `cat /usr/local/httpd/logs/httpd.pid`
	#kill -USR1 `cat /usr/local/apache2/logs/httpd.pid`
	sudo yum install -y libxslt-devel libxml2-devel libffi-devel redis mod_wsgi python-virtualenv httpd
	echo y|sudo yum groupinstall 'Development Tools'
	sudo yum install -y libjpeg-devel freetype-devel python-imaging mysql postgresql postgresql-devel #-client llibcurl3-devel
	#Python-dev(el) no se pone por que ya etá python2-devel y se supone que usamos Python 2
	sudo groupadd -f $(WWWGROUP)
	getent passwd $(WWWUSER)>/dev/null||sudo adduser $(WWWUSER) -g $(WWWGROUP)
	#If the user does exists, does not execute the part of the command. This behavior is
	#achieved because this instruction is taken as a boolean construct (as all in shell finally, that lines have a return code), with || as the operator (OR).
	#If the first command (before the ||) gives a zero return value (if the user exists) there is no need to execute the second part of the statement to 
	#calculate the return value of the line
	#usermod -g $(WWWGROUP) $(WWWUSER)#Pero 1003 es el gid que le tocó por azar al grupo www-data
	sudo usermod -s /bin/false $(WWWUSER)
	sudo usermod -L $(WWWUSER)
	# install apache/wsgi
	#yum -y apache2 apache2.2-common apache2-mpm-prefork apache2-utils libexpat1 ssl-cert libapache2-mod-wsgi
	# disable default site
	#a2dissite 000-default
very_essential_ubuntu:
	apt-get install -y sudo
	sudo apt-get install -y sudo less make wget curl vim apt-utils
very_essential_centos:
	yum install -y sudo
	sudo yum install -y sudo wget less make curl vim

bowtie:
	wget -c http://netix.dl.sourceforge.net/project/bowtie-bio/bowtie2/2.2.6/bowtie2-2.2.6-linux-x86_64.zip && \
	unzip bowtie2-2.2.6-linux-x86_64.zip && \
	cd bowtie2-2.2.6 && sudo mv bowtie2* /usr/local/bin
	rm -rf bowtie2-2.2.6 bowtie2-2.2.6-linux-x86_64.zip

# zippy setup (will move to distutils in future release)
zippy-install_ubuntu:
	# virtualenv
	sudo mkdir -p $(ZIPPYPATH)
	cd $(ZIPPYPATH) && sudo /usr/bin/virtualenv venv
	sudo $(ZIPPYPATH)/venv/bin/pip install --upgrade pip
	sudo $(ZIPPYPATH)/venv/bin/pip install Cython==0.24
	sudo $(ZIPPYPATH)/venv/bin/pip install -r package-requirements.txt
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
	# create empty database
	sudo mkdir -p $(ZIPPYVAR)
	sudo touch $(ZIPPYVAR)/zippy.sqlite
	sudo touch $(ZIPPYVAR)/zippy.log
	sudo touch $(ZIPPYVAR)/.blacklist.cache
	sudo touch $(ZIPPYVAR)/zippy.bed
	sudo chmod 666 $(ZIPPYVAR)/zippy.sqlite
	sudo chmod 666 $(ZIPPYVAR)/zippy.log
	sudo chmod 666 $(ZIPPYVAR)/.blacklist.cache
	sudo chmod 666 $(ZIPPYVAR)/zippy.bed
	mkdir -p $(ZIPPYVAR)/uploads
	mkdir -p $(ZIPPYVAR)/results
	#sudo chown -R flask:www-data /var/local/zippy
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)
	#sudo chmod -R 777 $(ZIPPYVAR)
zippy-install_centos:
	# virtualenv
	sudo mkdir -p $(ZIPPYPATH)
	cd $(ZIPPYPATH) && sudo /usr/bin/virtualenv venv
	sudo $(ZIPPYPATH)/venv/bin/pip install --upgrade pip
	sudo $(ZIPPYPATH)/venv/bin/pip install Cython==0.24
	sudo $(ZIPPYPATH)/venv/bin/pip install -r package-requirements.txt
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
	# create empty database
	sudo mkdir -p $(ZIPPYVAR)
	#sudo chown -R root:root $(ZIPPYVAR)
	#sudo touch $(ZIPPYVAR)/zippy.sqlite
	#sudo touch $(ZIPPYVAR)/zippy.log
	#sudo touch $(ZIPPYVAR)/.blacklist.cache
	#sudo touch $(ZIPPYVAR)/zippy.bed
	#sudo chmod 666 $(ZIPPYVAR)/zippy.sqlite
	#sudo chmod 666 $(ZIPPYVAR)/zippy.log
	#sudo chmod 666 $(ZIPPYVAR)/.blacklist.cache
	#sudo chmod 666 $(ZIPPYVAR)/zippy.bed
	sudo mkdir -p $(ZIPPYVAR)/uploads
	sudo mkdir -p $(ZIPPYVAR)/results
	sudo mkdir -p $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)


#Cleans
cleanall: cleansoftware cleandata cleandb
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

# gunicorn/nginx webserver
unicorn:
	apt-get install nginx
	# start gunicorn with
	# gunicorn --bind 0.0.0.0:8000 wsgi:app

# webservice install (for the interior of a docker container)
webservice-docker_ubuntu:
	rsync -a --exclude-from=.gitignore . $(ZIPPYPATH)
	# make WWW directories
	mkdir -p $(ZIPPYWWW)
	cp install/zippy.wsgi $(ZIPPYWWW)/zippy.wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	cp install/zippy.hostconfig /etc/apache2/sites-available/zippy.conf
	#echo "ServerName localhost" >> /etc/apache2/apache2.conf
	# enable site and restart
	a2ensite zippy
	#/etc/init.d/apache2 restart
# webservice install (production)
webservice_ubuntu:
	rsync -a --exclude-from=.gitignore . $(ZIPPYPATH)
	# make WWW directories
	mkdir -p $(ZIPPYWWW)
	cp install/zippy.wsgi $(ZIPPYWWW)/zippy.wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	cp install/zippy.hostconfig /etc/apache2/sites-available/zippy.conf
	echo "ServerName localhost" > /etc/httpd/conf.d/zippy_servernameconf.conf
	# enable site and restart
	a2ensite zippy
	/etc/init.d/apache2 restart
# same for development environment (not maintained)
webservice-dev_ubuntu:
	# make WWW directories
	mkdir -p $(ZIPPYWWW)
	cp install/zippy_dev.wsgi $(ZIPPYWWW)/zippy.wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	cp install/zippy_dev.hostconfig /etc/apache2/sites-available/zippy.conf
	# enable site and restart
	a2ensite zippy
	/etc/init.d/apache2 restart

# webservice install (production)
webservice_centos:
	sudo rsync -a --exclude-from=.gitignore . $(ZIPPYPATH)
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
	# make WWW directories
	sudo mkdir -p $(ZIPPYWWW)
	sudo cp install/zippy.wsgi $(ZIPPYWWW)/zippy.wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	sudo cp install/zippy.hostconfig_centos /etc/httpd/conf.d/zippy.conf
	# enable site and restart
	#sudo echo "ServerName localhost" > /etc/httpd/conf.d/zippy_servernameconf.conf
	sudo systemctl restart httpd
	#Opens the port 80 in the firewall in the system, for public access
	sudo firewall-cmd --zone=public --add-service=http --permanent
	sudo firewall-cmd --reload
# webservice install (for the interior of a docker container)
webservice-docker_centos:
	sudo rsync -a --exclude-from=.gitignore . $(ZIPPYPATH)
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYPATH)
	# make WWW directories
	sudo mkdir -p $(ZIPPYWWW)
	sudo cp install/zippy.wsgi $(ZIPPYWWW)/zippy.wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	sudo cp install/zippy.hostconfig /etc/httpd/conf.d/zippy.conf
	# enable site and restart
	#sudo echo "ServerName localhost" > /etc/httpd/conf.d/zippy_servernameconf.conf
# same for development environment (not maintained)
webservice-dev_centos:
	# make WWW directories
	sudo mkdir -p $(ZIPPYWWW)
	sudo cp install/zippy_dev.wsgi $(ZIPPYWWW)/zippy_dev.wsgi
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYWWW)
	# apache WSGI config
	sudo cp install/zippy_dev.hostconfig_centos /etc/httpd/conf.d/zippy.conf
	# enable site and restart
	#sudo echo "ServerName localhost" > /etc/httpd/conf.d/zippy_servernameconf.conf
	#a2ensite zippy
	sudo systemctl start httpd.service
	#Opens the port 5000 in the firewall in the system
	sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
	sudo firewall-cmd --reload


#### genome resources
import-resources:
	# Copy resource files
	sudo mkdir -p $(ZIPPYVAR)/resources
	rsync -avPp resources $(ZIPPYVAR)
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)
stash-resources:
	# Copy resource files
	echo Stashing resources
	#sudo mkdir -p /srv/zippy_resources
	#sudo mv $(ZIPPYVAR)/resources/* /srv/zippy_resources/
	#sudo chown -R $(WWWUSER):$(WWWGROUP) /srv/zippy_resources
unstash-resources:
	# Copy resource files
	echo Unstashing resources
	#sudo ln -s /srv/zippy_resources $(ZIPPYVAR)/resources
	#sudo mkdir -p $(ZIPPYVAR)/resources
	#for file in $(ls /srv/zippy_resources);
	#do
	#	sudo rm $(ZIPPYVAR)/$file
	#	sudo ln -s /srv/zippy_resources/$file $(ZIPPYVAR)/$file
	#done
	#sudo mv /srv/zippy_resources/* $(ZIPPYVAR)/resources/
	#sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

resources: genome annotation

genome: genome-download genome-index

genome-download:
	#sudo mkdir -p $(ZIPPYVAR)/resources
	#sudo ln -s /srv/zippy_resources $(ZIPPYVAR)/resources
	#sudo chmod -R 777 $(ZIPPYVAR)/resources
	#cd $(ZIPPYVAR)/resources
	ls $(ZIPPYVAR)/resources/${genome}.fasta &>/dev/null && ( \
		echo File ${genome}.fasta.gz exists, not downloading it again ) || ( \
		cd $(ZIPPYVAR)/resources; \
		echo Downloading genome to $(ZIPPYVAR)/resources/${genome} ; \
		wget -qO- ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/${genome}.fasta.gz | \
		gzip -dcq | cat >${genome}.fasta && rm -f ${genome}.fasta.gz )
	ls $(ZIPPYVAR)/resources/${genome}.fasta.fai &>/dev/null && \
		echo File $(ZIPPYVAR)/resources/${genome}.fasta.fai exists, not downloading it again || \
		( cd $(ZIPPYVAR)/resources; wget -c ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/${genome}.fasta.fai )
	sudo chmod 644 $(ZIPPYVAR)/resources/*
	sudo chmod 755 $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

genome-index:
	#sudo mkdir -p $(ZIPPYVAR)/resources
	#sudo ln -s /srv/zippy_resources $(ZIPPYVAR)/resources
	#sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources
	#ls $(ZIPPYVAR)/resources/${genome}.bowtie.rev.2.bt2 &>/dev/null && sudo chmod -R 777 $(ZIPPYVAR)/resources && ( \
	ls $(ZIPPYVAR)/resources/${genome}.bowtie.rev.2.bt2 &>/dev/null ( \
		echo bowtie file $(ZIPPYVAR)/resources/${genome}.bowtie exists, thus not running bowtie command ) || \
		( cd $(ZIPPYVAR)/resources; sudo /usr/local/bin/bowtie2-build ${genome}.fasta ${genome}.bowtie )
	sudo chmod 644 $(ZIPPYVAR)/resources/*
	sudo chmod 755 $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

annotation: variation-download refgene-download

variation-download:
	#The files specified by the following commands did not exist as of 30 th, Jly, 2018, so that were updated by the later version present: b151_GRCh37p13
	#sudo ln -s /srv/zippy_resources $(ZIPPYVAR)/resources
	#sudo mkdir -p $(ZIPPYVAR)/resources
	#cd $(ZIPPYVAR)/resources && sudo chmod -R 777 $(ZIPPYVAR)/resources && \
	cd $(ZIPPYVAR)/resources && \
	( ls 00-common_all.vcf.gz &>/dev/null && echo 00-common_all.vcf.gz already found || sudo wget -c ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/00-common_all.vcf.gz )
	cd $(ZIPPYVAR)/resources && sudo wget -c ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/00-common_all.vcf.gz.tbi
	#sudo chmod 644 $(ZIPPYVAR)/resources/*
	#sudo chmod 755 $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

refgene-download:
	#sudo ln -s /srv/zippy_resources $(ZIPPYVAR)/resources
	#sudo chmod 777 $(ZIPPYVAR)/resources
	#sudo mkdir -p $(ZIPPYVAR)/resources && sudo chmod -R 777 $(ZIPPYVAR)/resources && cd $(ZIPPYVAR)/resources && \
	cd $(ZIPPYVAR)/resources && \
	mysql --user=genome --host=genome-mysql.cse.ucsc.edu -A -N -D hg19 -P 3306 \
	 -e "SELECT DISTINCT r.bin,CONCAT(r.name,'.',i.version),c.ensembl,r.strand, r.txStart,r.txEnd,r.cdsStart,r.cdsEnd,r.exonCount,r.exonStarts,r.exonEnds,r.score,r.name2,r.cdsStartStat,r.cdsEndStat,r.exonFrames FROM refGene as r, hgFixed.gbCdnaInfo as i, ucscToEnsembl as c WHERE r.name=i.acc AND c.ucsc = r.chrom ORDER BY r.bin;" > refGene
	#sudo chmod 644 $(ZIPPYVAR)/resources/*
	#sudo chmod 755 $(ZIPPYVAR)/resources
	sudo chown -R $(WWWUSER):$(WWWGROUP) $(ZIPPYVAR)/resources

#sudo firewall-cmd --zone=public --list-all
#sudo firewall-cmd --zone=public --add-port=5000/tcp
#sudo firewall-cmd --zone=public --add-service=http
#sudo firewall-cmd --reload
