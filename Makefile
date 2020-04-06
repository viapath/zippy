# installation makefile

ZIPPYPATH=/usr/local/zippy
ZIPPYVAR=/var/local/zippy
ZIPPYRESOURCES=$(ZIPPYVAR)/resources
VPATH=$(ZIPPYRESOURCES)

# docker build (all in one)
build:
	docker build --target mono -t kingspm/zippy .

# installs
native: install resources

# zippy install with virtual env
install: essential zippy-setup
	# virtualenv
	cd $(ZIPPYPATH) && virtualenv venv
	$(ZIPPYPATH)/venv/bin/pip2 install Cython==0.24
	$(ZIPPYPATH)/venv/bin/pip2 install -r package-requirements.txt

# native zippy install (eg for containers)
install-dockerized: essential zippy-setup
	# do not use a venv (eg for docker images)
	pip install Cython==0.24
	pip install cffi==1.14.0
	pip install -r package-requirements.txt

# requirements
essential:
	apt-get install -y wget sqlite3 unzip git htop jq
	apt-get install -y python-pip python2.7-dev ncurses-dev python-virtualenv
	apt-get install -y libxslt-dev libxml2-dev libffi-dev
	apt-get install -y redis-server
	apt-get install -y build-essential libjpeg-dev libfreetype6-dev python-dev python-imaging libcurl3-dev
	apt-get install -y mysql-client
	apt-get install -y bowtie2
	apt-get install -y postgresql-server-dev-9.4
	wget -O /usr/local/bin/blat http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/blat/blat && chmod +x /usr/local/bin/blat
	wget -O /usr/local/bin/faToTwoBit http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/faToTwoBit && chmod +x /usr/local/bin/faToTwoBit

# setup paths and files for zippy
zippy-setup:
	# create empty database
	mkdir -p $(ZIPPYVAR)
	touch $(ZIPPYVAR)/zippy.sqlite
	touch $(ZIPPYVAR)/zippy.log
	touch $(ZIPPYVAR)/.blacklist.cache
	mkdir -p $(ZIPPYRESOURCES)
	mkdir -p $(ZIPPYVAR)/uploads
	mkdir -p $(ZIPPYVAR)/results
	chmod -R 777 $(ZIPPYVAR)

######################
## genome resources ##
######################

resources: genome annotation

genome: human_g1k_v37.fasta human_g1k_v37.fasta.fai genome-index

human_g1k_v37.fasta:
	cd $(ZIPPYRESOURCES) && \
	wget -qO- ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/human_g1k_v37.fasta.gz | \
	gzip -dcq | cat > human_g1k_v37.fasta && rm -f human_g1k_v37.fasta.gz

human_g1k_v37.fasta.fai:
	cd $(ZIPPYRESOURCES) && \
	wget -c ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/human_g1k_v37.fasta.fai

genome-index: human_g1k_v37.bowtie.rev.1.bt2 human_g1k_v37.bowtie.rev.2.bt2 human_g1k_v37.bowtie.4.bt2 human_g1k_v37.bowtie.3.bt2 human_g1k_v37.bowtie.2.bt2 human_g1k_v37.bowtie.1.bt2

human_g1k_v37.bowtie.rev.1.bt2 human_g1k_v37.bowtie.rev.2.bt2 human_g1k_v37.bowtie.4.bt2 human_g1k_v37.bowtie.3.bt2 human_g1k_v37.bowtie.2.bt2 human_g1k_v37.bowtie.1.bt2 &:
	cd $(ZIPPYRESOURCES) && \
	bowtie2-build human_g1k_v37.fasta human_g1k_v37.bowtie

genome-index-blat: human_g1k_v37.2bit

human_g1k_v37.2bit:
	cd $(ZIPPYRESOURCES) && \
	faToTwoBit human_g1k_v37.fasta human_g1k_v37.2bit

annotation: 00-common_all.vcf.gz 00-common_all.vcf.gz.tbi refGene

00-common_all.vcf.gz:
	cd $(ZIPPYRESOURCES) && \
	wget -c ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/00-common_all.vcf.gz

00-common_all.vcf.gz.tbi:
	cd $(ZIPPYRESOURCES) && \
	wget -c ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/00-common_all.vcf.gz.tbi

refGene:
	cd $(ZIPPYRESOURCES) && \
	mysql --user=genome --host=genome-mysql.cse.ucsc.edu -A -N -D hg19 -P 3306 \
	 -e "SELECT DISTINCT r.bin,CONCAT(r.name,'.',i.version),c.ensembl,r.strand, r.txStart,r.txEnd,r.cdsStart,r.cdsEnd,r.exonCount,r.exonStarts,r.exonEnds,r.score,r.name2,r.cdsStartStat,r.cdsEndStat,r.exonFrames FROM refGene as r, hgFixed.gbCdnaInfo as i, ucscToEnsembl as c WHERE r.name=i.acc AND c.ucsc = r.chrom ORDER BY r.bin;" > refGene
