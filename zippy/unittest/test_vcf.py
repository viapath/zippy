import unittest, pysam, gzip, itertools, math, pytest
from zippy.zippylib import files


#@unittest.skip("accelerate the testing")
#class TestVcf(unittest.TestCase):
class TestVcf:
    def test_aller_vcf_lines(self):
        with gzip.open("/var/local/zippy/resources/00-All.vcf.gz", "rb") as opf:
            for (iline, line) in enumerate(opf):
                print("linea", line)
                if iline == 10:
                    break

    def test_commoner_vcf_lines(self):
        with open("/var/local/zippy/resources/00-common_all.vcf", "rb") as opf:
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

    @pytest.markskip("Now the compressed files are not used")
    def test_gnomad_vcf_pysam(self):
        files.VCF.create_stripped_vcf("/var/local/zippy/resources/gnomad.exomes.r2.1.1.sites.Y.vcf.bgz", "/var/local/zippy/resources/gnomad.exomes.r2.1.1.sites.Y.onlyAFmetadata.vcf")
        original_vcf = pysam.VariantFile("/var/local/zippy/resources/gnomad.exomes.r2.1.1.sites.Y.vcf.bgz")
        stripped_vcf = pysam.VariantFile("/var/local/zippy/resources/gnomad.exomes.r2.1.1.sites.Y.onlyAFmetadata.vcf")
        iorig = -1
        stripped_vcf_iterator = stripped_vcf.fetch()
        #for (origvcf_record, strippedvcf_record) in itertools.zip_longest(original_vcf.fetch(), stripped_vcf.fetch()):
        for origvcf_record in original_vcf.fetch():
            strippedvcf_record = next(stripped_vcf_iterator)
            assert origvcf_record is not None and strippedvcf_record is not None, (origvcf_record, strippedvcf_record)
            # info of strippedvcf_record should be a subset of info of origvcf_record, qual
            iorig += 1
            for attr in ('alleles', 'alts', 'chrom', 'contig', 'filter', 'id', 'pos', 'ref', 'rid', 'rlen', 'samples', 'start', 'stop'):
                strippedvalue = getattr(strippedvcf_record, attr)
                origvalue = getattr(origvcf_record, attr)
                assert strippedvalue == origvalue, (attr, origvalue, strippedvalue)
            strippedvalue = strippedvcf_record.qual
            origvalue = origvcf_record.qual
            isclose = math.isclose(strippedvalue, origvalue, rel_tol=1e-05)
            assert isclose, (strippedvalue, origvalue)
            if len(strippedvcf_record.info.keys()) == 0:
                assert "AF" not in origvcf_record.info
            else:
                assert len(strippedvcf_record.info.keys()) == 1, strippedvcf_record.info.keys()
                strippedkey = next(iter(strippedvcf_record.info.keys()))
                assert strippedkey == "AF"
                assert strippedvcf_record.info["AF"] == origvcf_record.info["AF"]
        try:
            strippedvcf_record = next(stripped_vcf_iterator)
        except StopIteration:
            pass
        else:
            assert 0, ('xorto', strippedvcf_record)
##gnomad.exomes.r2.1.1.sites.Y.vcf.bgz
#if __name__=="__main__":
#    unittest.main()
    #tvcf = TestVcf()
    #tvcf.test_aller_vcf_lines()
    #tvcf.test_commoner_vcf_lines()
    #tvcf.test_gnomad_vcf_lines()