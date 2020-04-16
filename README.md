# Zippy
Primer database and design tool

- [Zippy](#zippy)
  - [Description](#description)
    - [Primer design](#primer-design)
    - [Storage Management](#storage-management)
    - [Batch processing](#batch-processing)
  - [Install](#install)
    - [Docker setup](#docker-setup)
      - [Configuration](#configuration)
    - [Native Install](#native-install)
  - [Usage](#usage)
    - [Webservice](#webservice)
    - [Command line interface](#command-line-interface)
      - [Importing exisitng primer library](#importing-exisitng-primer-library)
  - [Release Notes](#release-notes)
    - [v1.0](#v10)
    - [v1.1](#v11)
    - [v1.2](#v12)
    - [v2.0.0](#v200)
    - [v2.0.1](#v201)
    - [v2.1.0](#v210)
    - [v2.2.0](#v220)
    - [v2.2.1](#v221)
    - [v2.2.2](#v222)
    - [v2.3.0](#v230)
    - [v2.4.0](#v240)
    - [FUTURE](#future)
  - [Resource Info](#resource-info)
    - [Reference Genome](#reference-genome)
    - [Common variation](#common-variation)

  - [Reference Genome](#reference-genome)

## Description
This program integrates a simple SQLite primer database and design tool based on the Primer3 library.
It allows the automatic generation of primer pairs based on a VCF, BED or SNPpy result table.

### Primer design
Zippy's primary functionality is the automatic design of working sequencing primer pairs. It uses Primer3 as a backend and verifies the uniqueness of resulting sequencing amplicons, identifying overlap with potentially interfering common variation in the genome. Multiple design parameter sets can be specified and Zippy will autmatically move on to the next, less stringent parameter sets if the design process does not yield any good primer pairs (deep searching).

### Storage Management
Zippy also manages storage of primer pairs in boxes (vessel) and wells. It also provides functionality for barcode tracking of primer dilutions ready for sequencing.

### Batch processing
Zippy encourages a workflow of variant confirmations from Variant scoring with SNPpy. It directly reads output from such and generates multiple outputs:

1. Overview of sequencing primers selected for variant confirmation (TXT)
2. Worksheet to assist and track the confirmation workflow (PDF)
3. Program instruction for Hamilton robot to prepare plates for Sanger sequencing confirmations (CVS)
4. Barcoded tube labels for Primer dilutions (ZPL)
5. Worksheet and Program for test of new primers (optional,PDF/CSV)
6. A list of variants with no suitable sequencing primers (optional,TXT)

For information on the Hamilton Robot program please contact the authors.

## Install
The installation procedure installs an Apache2 webserver and installs all required python modules in a *virtualenv* in `/usr/local/zippy`. Genomic data is stored

### Docker setup
The easiest way to test zippy without changing your existing system is to run zippy from a docker container. The webinterface is exposed on port `5000`.

1. Build the image (requires installation of docker)
> `docker build -t kingspm/zippy .`
Alternatively you can pull an image from DockerHub
> `docker pull kingspm/zippy`
2. start the image as a daemon (bind to local port 9999)
> `docker run -d -p 9999:5000 -m 6144m kingspm/zippy`
3. Web interface can be accessed on `localhost:9999`

This procedure will create a monolithic docker image that contains all genome, annotation and variation data (it will be big). If you want to mount those resources from a directory a host, the container can be built using the `bare` target to prevent adding those resources to the image.
> `docker build --target bare -t kingspm/zippy:bare`

#### Configuration
The configured password can be overridden using the ZIPPY_PASSWORD environment variable.

If you require a custom configuration file, mount your configuration file to `/usr/local/zippy/zippy/zippy.json` as below:
> `docker run -d -p 9999:5000 -v zippy.json:/usr/local/zippy/zippy/zippy.json`

You should consider mounting database and log files, if those should persist beyond container lifetime.
For example, the database can be persisted as follows:
> `docker run -d -p 9999:5000 -v zippy.sqlite:/var/local/zippy/zippy.sqlite kingspm/zippy`

The following files should be persisted outside of the docker container in a production setup:

|File|Description|
|:---|:---|
|`/var/local/zippy/zippy.sqlite`|Primer database (SQLite3)|
|`/var/local/zippy/zippy.log`|Log file|
|`/var/local/zippy/.blacklist.cache`|Blacklisted Primer Cache (pickle)|
|`/var/local/zippy/zippy.bed`|BED file of all amplicons in database (updates on database change)|
|`/var/local/zippy/zippy_access.log`|Access log (gunicorn in docker)|
|`/var/local/zippy/zippy_error.log`|Error log (gunicorn in docker)|
|`/var/local/zippy/uploads`|Uploads folder|
|`/var/local/zippy/results`|Results folder (eg Worksheets)|

fire up the virtual machine and connect with
> `vagrant up && vagrant ssh`

then follow the local installation instructions below.

### Native Install
The current installation routine will download and build the human *GRCh_37* genome index and download the common variantion data from *dbsnp1xx*. If you desire to use your own resources or an alternative reference genome simply put everything into the `./resource` directory and it will be imported to `/var/local/zippy/resources` during the installation process.
Make sure to modify the configuration file `zippy.json` accordingly.

To install the development version (uses zippy from mounted NFS volume) run
> `sudo make install`

You can download b37 genomes, index and annotations with
> `sudo make resources`

NB: The default install makes the database/resource directory accessible for all users.

## Usage

### Webservice
The application runs on gunicorn using WSGI.
The standard install exposes the service on port 5000 on the guest.

Currently the design process is executed synchronously. This can potentially lead to timeouts during the design process if many target regions are requested. In this case please run *zippy* from the command line interface.

### Command line interface
Before running zippy from the CLI, make sure to activate the virtual environment first
> `source /usr/local/zippy/venv/bin/activate`

To design primers and query existing
> `zippy.py get <VCF/BED> --design`

add primers to database
> `zippy.py add <FASTA>`

retrieve (and design) primer for a single location
> `zippy.py get chr1:202030-202100 --design`

design/retrieve primers for a SNPpy result (batch mode)
> `zippy.py batch <SNPpy>`

Blacklist primer
> `zippy.py update -b <PRIMERNAME>`

Set/update primer storage location
> `zippy.py update -l <PRIMERNAME> <VESSEL> <WELL>`

#### Importing exisitng primer library
Exisitng primers can be imported from the command line with:
> `zippy.py add <FASTA>`
The entries in the FASTA file should pair the primers using `_rev` or `_fwd` suffixes in their names.
On import all primers will be checked against the design limits specified in the configuration. This allows to import and validate existing primers against a new genome assembly.

## Release Notes
### v1.0
- Primer3 base design
- genome mispriming check (bowtie)
- SNPcheck (crossvalidate primer location with indexed VCF)
- amplicon size validation on import
- batch processing of SNPpy results

### v1.1
- worksheet and robot CSV file generation

### v1.2
- Webinterface/GUI
- Tube Label Generation
- Fixed Plate filling
- GenePred input for design

### v2.0.0
- changed version scheme
- New database schema to allow for primer collections
- Primer tag tracking
- Primer table import
- Storage by Primer and storage validation
- Allows for same primer in multiple pairs
- Added primer redundancy query
- Primer design parameter sets (deep digging for primers)
- Importing of primer pairs with multiple amplicons
- Blacklist cache for design
- Improved webinterface
- Apache Webserver in VM
- New setup routines (zippyprimer on PyPi)
- Easier VM provisioning

### v2.0.1
- option to install production version on VM
- fixed import of primers with shared primers (multiple amplicons)
- Added SMB share for windows installs
- Fixed page breaking in tables
- Added primer table dump for reimport and easier migration to future versions
- Automatic primer/pair renaming on conflict

### v2.1.0
- Loci stored with Tm (prep for future in silico PCR)
- Mispriming check with thermodynamic alignments and 3prime match
- amplicon rescue for non-specific primers on import
- Bugfixes

### v2.2.0
- Web interface changes (search by date, batch location update)

### v2.2.1
- Bugfixes

### v2.2.2
- bugfix in exon annotation of batched variants
- predesign exons now filtered by requested variants for speed

### v2.3.0
- added gap-PCR functionality
- added WSGI file for gunicorn
- bugfixes

### v2.4.0
- simplified installation
- switched to gunicorn (+nginx) webserver
- Updated README
- added optional blat indexing (not implemented in Zippy yet)
- Reset configuration to sensible defaults

### FUTURE
- Support for primer collections (multiplexing)
- Asynchronous design process on webinterface
- Web GUI extensions
- Storage map (suggest new locations?)
- Import from files (fasta,list)
- Better detection of foreign amplicons

## Resource Info

### Reference Genome
Primers are designed from the unmasked 1kg reference genome while ignoring simple repeat regions.
Alternatively, use a Repeatmasked reference genome. Even better if common SNPs are masked as well (eg. >1%).
BEDTOOLS offers `maskfasta` for this purpose. Masking data in BED format can be obtained from UCSC (http://genome.ucsc.edu/cgi-bin/hgTables?command=start).

### Common variation
The default setup and the docker image contain a copy of the common variation listed in dbSNP (see `Makefile` for version). This includes known polymorphisms above 1% population frequency. Design paramteres can allow or restrict presence of SNPs in the whole primer, or in the 3' end of the primer (last third of the total length) for which allele specific amplification is likely.
