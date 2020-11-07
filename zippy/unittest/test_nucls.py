#!/usr/bin/env python

import unittest, pysam, json, pytest, logging, os
from zippy import zippy
from zippy.zippylib import range_string
from zippy.zippylib.database import PrimerDB
logger = logging.getLogger(__name__)
# This script is prepared to be run run from the zippy root folder as python -m zippy.unittest.test


@pytest.mark.skip("accelerate the testing")
class TestRanges:
    def test_range1(self):
        rs = range_string([1, 2, 3, 4, 5, 7, 8, 9, 11, 14])
        assert rs == "1-5,7-9,11,14"

    def test_range2(self):
        rs = range_string([1, 3, 4, 5, 7, 8, 9, 11, 14])
        assert rs == "1,3-5,7-9,11,14"


@pytest.mark.skip("accelerate the testing")
class TestPrimers:

    #def setUp(self):
    #    # add primers to database
    #    raise NotImplementedError

    def test_retrival(self):
        # get
        raise NotImplementedError

    def test_design(self):
        # get with design
        raise NotImplementedError

    def test_isupper(self):
        assert 'FOO'.isupper()
        assert not 'Foo'.isupper()

    def test_split(self):
        s = 'hello world'
        assert s.split() == ['hello', 'world']
        # check that s.split fails when the separator is not a string
        try:
            s.split(2)
        except TypeError:
            pass  # then the test is OK
        else:
            raise AssertionError("test split failed")


class TestGenome:
    config_json = os.environ.get("CONFIG_FILE", "zippy/zippy.json")
    #config_json = os.environ.get("CONFIG_FILE", "zippy/extra_configs/zippy_v7.6.json")
    @pytest.mark.skip("fastening tests")
    def test_chr10(self):
        pfile = pysam.FastaFile("/var/local/zippy/resources/human_g1k_v37.fasta")
        args = ('10', 43613278, 43614409)
        fetched = pfile.fetch(*args)
        assert fetched == """TGGTAACTAACGGAGTGTGAGCTGCTGACGTGTGTGTGACGGATACATCAGCAGCACAGGAGATGCCTGGGCTCCAGGCTGGCCATCTCAGACAGGAGCGGGAAATGGGGAGCCTGGTCGCGGTGTGTGGACCTCCTTTATGGCTCTCCACCTTCTCCAGGGCCTCTCCCGACAAGTGGGTGTGTGGGTACCCCTCACCTTTCCAGAATGATTAATGCGGGGAATTTCTGTGGACGACTGTCTTCTAAAGACAATGACTACAGGAACATAATGCCACATACACAGGTGGCCCAGCCCTGGGACACTCTGGGGAAAGATCCGGCATGTGTGGTTGCTGGCTCCTCAGGGTGCTTCTTCCTCAGGGTGGATGAGGCCCCTGTCCACTGATCCCAAAGGCTGGGAGAAGCCTCAAGCAGCATCGTCTTTGCAGGCCTCTCTGTCTGAACTTGGGCAAGGCGATGCAGGTCCATCCTGACCTGGTATGGTCATGGAAGGGGCTTCCAGGAGCGATCGTTTGCAACCTGCTCTGTGCTGCATTTCAGAGAACGCCTCCCCGAGTGAGCTGCGAGACCTGCTGTCAGAGTTCAACGTCCTGAAGCAGGTCAACCACCCACATGTCATCAAATTGTATGGGGCCTGCAGCCAGGATGGTAAGGCCAGCTGCAGGGTGAGGTGGGCAGCCACTGCACCCAGGCTGGGGGCTCCATACAGCCCTGTTCTCCCTCTTTCTCCCTTTCCCTACTGCTCCTGCCCTGTTTCCTGTTCTCCCTCTTTCTGGAAGCCTGGCTCAGGCCCCAGCCTGGAGCTTGTGTCTAGCTGAGTCCACGGGCTGAGTGGTCACTTTCCATCAGAGGGGCCCCGCGCTAGCGGCACTCCCTGGGCCCACAGGGCTACTCAGAGGTCTCTGGTGTGACACTGCCATGTGTCCTCACCCAGTTCGGGGCTGGGCCCGTGGGGCAGGGAGCTCTAGGAATGGACAGTGCATCCTGGGTACTAGGGTACCCTGGGTACCACAGGGCACCAGGTGTGCTGTGACCTCAGGTGACCCCAGCCCCGCCCTGCATGGCAGGAACATTGTCACCATTTCTCAGATAAAGACCCAGGAGACCAGCCTGGTTTGTTGGTTTTCCA"""

    @pytest.mark.skip("fastening tests")
    def test_primerexonname2(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"] = "/dev/null"
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            # name_to_dump = "DNM1L"
            name_to_dump = None
            results = zippy.zippyPrimerQuery(
                config, "12:32895523-32895682", True, None, db, None, [0],
                name_to_dump=name_to_dump, noncoding=False, combine=True,
                getgenes=None)

    @pytest.mark.skip("fastening tests")
    def test_base0_vs_base1(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"] = "/dev/null"
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            name_to_dump = "DNM1L"
            #name_to_dump = None
            config["exon_numbering_base"] = 0
            results0 = zippy.zippyPrimerQuery(
                config, "12:32895523-32895682", True, None, db, None, [0],
                name_to_dump=name_to_dump, noncoding=False, combine=True,
                getgenes=None)
            zippy.gplist = None
            config["exon_numbering_base"] = 1
            results1 = zippy.zippyPrimerQuery(
                config, "12:32895523-32895682", True, None, db, None, [0],
                name_to_dump=name_to_dump, noncoding=False, combine=True,
                getgenes=None)
            logger.info("ress0 {}".format(results0))
            logger.info("ress1 {}".format(results1))
            assert 0, (results0, results1)

    #@pytest.mark.skip("fastening tests")
    def test_primerexonname208(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"] = "/dev/null"
            #config["snpcheck"]["used"] = "common"
            #config["exon_numbering_base"] = 1
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:25398208-25398318", True, None, db,
                                             None, [0, 1, 2], name_to_dump="KRAS")
            assert results[0][0][0:2] == ['12:25398208-25398318', 'KRAS_1'], results

    def test_primerexonname_ever_erroring(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"] = "/dev/null"
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32895523-32895682", True, None, db,
                                             None, [0, 1, 2], name_to_dump=None)
            assert results[0][0][0:2] == ['12:32895523-32895682', 'DNM1L_19'], results
            #assert len(results[0])>0, results

    def test_chr11(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"] = "/dev/null"
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "11:118343121-118343321", True, None, db,
                                             None, [0, 1, 2], name_to_dump=None)
            logging.info(f"chr11 {results}")
            assert results[0][0][0:2] == ['11:118343121-118343321', 'KMT2A_2_2-3'], results

    def test_chr12_2missing(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"] = "/dev/null"
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:115115461-115116484", True, None, db,
                                             None, [0, 1, 2], name_to_dump=None)
            assert len(results[0])==0, results

    @pytest.mark.skip("fastening tests")
    def test_primerexonname50(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32892997-32893452", True, None, db,
                                             None, [0, 1, 2], name_to_dump="DNM1L")
            assert 0, results

    @pytest.mark.skip("fastening tests")
    def test_primerexonname3(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32895351-32895785", True, None, db,
                None, [0, 1, 2], name_to_dump="DNM1L")
            assert 0, results

    @pytest.mark.skip("fastening tests")
    def test_primerexonname1(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "6:26091069-26091332", True, None, db,
                None, [0, 1, 2], name_to_dump=None)
            assert 0, results

    @pytest.mark.skip("fastening tests")
    def test_snplimits(self):
        with open(self.config_json) as conf:
            config = json.load(conf)
            config["blacklistcache"]="/dev/null"
            db = PrimerDB(config['database'], dump=config['ampliconbed'])
            zippy.gplist = None
            config["designlimits"]["criticalsnp"] == 20
            config["designlimits"]["snpcount"] == 20
            results = zippy.zippyPrimerQuery(config, "uploads/NEB_S2.smCounter.anno.vcf", True, None, db,
                None, [0, 1, 2], name_to_dump=None)
            zippy.gplist = None
            config["designlimits"]["criticalsnp"] == 0
            config["designlimits"]["snpcount"] == 0
            results2 = zippy.zippyPrimerQuery(config, "uploads/NEB_S2.smCounter.anno.vcf", True, None, db,
                None, [0, 1, 2], name_to_dump=None)
            assert results == results2, (results, results2)

#if __name__ == '__main__':
#    unittest.main()
