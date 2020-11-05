import unittest, pysam, gzip, itertools, math
from zippy.zippylib import files
import unittest, pytest

class TestVcf:
    def test_aller_vcf_lines(self):
        with gzip.open("/var/local/zippy/resources/00-All.vcf.gz", "rb") as opf:
            for (iline, line) in enumerate(opf):
                print("linea", line)
                if iline == 10:
                    break

    def test_commoner_vcf_lines(self):
        with open("/var/local/zippy/resources/00-common_all.vcf.gz", "rb") as opf:
            for (iline, line) in enumerate(opf):
                print("lineb", line)
                if iline == 10:
                    break

    def test_gnomad_vcf_lines(self):
        with gzip.open("/var/local/zippy/resources/gnomad.exomes.r2.1.1.sites.Y.vcf.bgz", "rb") as opf:
            for (iline, line) in enumerate(opf):
                print("lineg", line)
                if not(line.startswith(b"#")):
                #if iline==1000:
                    #assert 0, "www"
                    break

##gnomad.exomes.r2.1.1.sites.Y.vcf.bgz
