#!/usr/bin/env python

import unittest, pysam, json, pytest, logging, os
from zippy import zippy
from zippy.zippylib import range_string
from zippy.zippylib.database import PrimerDB
logger = logging.getLogger(__name__)
# This script is prepared to be run run from the zippy root folder as python -m zippy.unittest.test

config_json = os.environ.get("CONFIG_FILE", "zippy/zippy.json")
#config_json = os.environ.get("CONFIG_FILE", "zippy/extra_configs/zippy_v7.6.json")
logger.info(f"config_json: {config_json}")


@pytest.fixture
def config():
    with open(config_json) as conf:
        config = json.load(conf)
        config["used"] = ["common", "all", 0.1]
        config["blacklistcache"] = "/dev/null"
        return config

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

    # def setUp(self):
    #     # add primers to database
    #     raise NotImplementedError

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


#@pytest.mark.skip("accelerate the testing")
class TestGnomad:
    @pytest.mark.skip("gone")
    def test_chr6(self, config):
        config["snpcheck"]["used"] = ["common", "all", 0.000001]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        results = zippy.zippyPrimerQuery(config, "6:26092913-26093188", True, None, db,
                                         None, [0], name_to_dump=None)
        exon_number = 1 + config["exon_numbering_base"]
        logger.debug(f"ress {results}")
        assert len(results[0]) == 0, results
        config["snpcheck"]["used"] = ["common", "all", 0.007]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        results = zippy.zippyPrimerQuery(config, "6:26092913-26093188", True, None, db,
                                         None, [0], name_to_dump=None)
        exon_number = 1 + config["exon_numbering_base"]
        logger.debug(f"ress {results}")
        assert len(results[0]) > 0, results

    @pytest.mark.skip("well")
    def test_chr12(self, config):
        config["snpcheck"]["used"] = ["common", "all", 0.001]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "DNM1L"
        results = zippy.zippyPrimerQuery(
            config, "12:32895523-32895682", True, None, db, None, [0],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) == 0, results
        config["snpcheck"]["used"] = ["common", "all", 0.08]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        results = zippy.zippyPrimerQuery(
            config, "12:32895523-32895682", True, None, db, None, [0],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) > 0, results

    @pytest.mark.skip("well")
    def test_chr12_2(self, config):
        config["snpcheck"]["used"] = ["common", "all", 0.0001]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "TBX3"
        results = zippy.zippyPrimerQuery(
            config, "12:115115461-115116484", True, None, db, None, [0, 1, 2, 3],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) == 0, results
        config["snpcheck"]["used"] = ["common", "all", 0.08]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        results = zippy.zippyPrimerQuery(
            config, "12:115115461-115116484", True, None, db, None, [0, 1, 2, 3],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) > 0, results

    #@pytest.mark.skip("fasten tests")
    def test_chr22(self, config):
        config["snpcheck"]["used"] = ["common", "all", 0.000001]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "HFE"
        results = zippy.zippyPrimerQuery(
            config, "22:41568503-41568667", True, None, db, None, [0],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) == 0, results
        config["snpcheck"]["used"] = ["common", "all", 0.1]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "HFE"
        results = zippy.zippyPrimerQuery(
            config, "22:41568503-41568667", True, None, db, None, [0],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) > 0, results

    #@pytest.mark.skip("well")
    def test_chrX(self, config):
        config["snpcheck"]["used"] = ["common", "all", 0.1]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "RBM10"
        results = zippy.zippyPrimerQuery(
            config, "X:47045555-47045786", True, None, db, None, [0,],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) > 0, results
        config["snpcheck"]["used"] = ["common", "all"]
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "RBM10"
        results = zippy.zippyPrimerQuery(
            config, "X:47045555-47045786", True, None, db, None, [0,],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)
        assert len(results[0]) > 0, results


class TestGenome:
    def test_chr10(self):
        pfile = pysam.FastaFile("/var/local/zippy/resources/human_g1k_v37.fasta")
        args = ('10', 43613278, 43614409)
        fetched = pfile.fetch(*args)
        assert fetched == """TGGTAACTAACGGAGTGTGAGCTGCTGACGTGTGTGTGACGGATACATCAGCAGCACAGGAGATGCCTGGGCTCCAGGCTGGCCATCTCAGACAGGAGCGGGAAATGGGGAGCCTGGTCGCGGTGTGTGGACCTCCTTTATGGCTCTCCACCTTCTCCAGGGCCTCTCCCGACAAGTGGGTGTGTGGGTACCCCTCACCTTTCCAGAATGATTAATGCGGGGAATTTCTGTGGACGACTGTCTTCTAAAGACAATGACTACAGGAACATAATGCCACATACACAGGTGGCCCAGCCCTGGGACACTCTGGGGAAAGATCCGGCATGTGTGGTTGCTGGCTCCTCAGGGTGCTTCTTCCTCAGGGTGGATGAGGCCCCTGTCCACTGATCCCAAAGGCTGGGAGAAGCCTCAAGCAGCATCGTCTTTGCAGGCCTCTCTGTCTGAACTTGGGCAAGGCGATGCAGGTCCATCCTGACCTGGTATGGTCATGGAAGGGGCTTCCAGGAGCGATCGTTTGCAACCTGCTCTGTGCTGCATTTCAGAGAACGCCTCCCCGAGTGAGCTGCGAGACCTGCTGTCAGAGTTCAACGTCCTGAAGCAGGTCAACCACCCACATGTCATCAAATTGTATGGGGCCTGCAGCCAGGATGGTAAGGCCAGCTGCAGGGTGAGGTGGGCAGCCACTGCACCCAGGCTGGGGGCTCCATACAGCCCTGTTCTCCCTCTTTCTCCCTTTCCCTACTGCTCCTGCCCTGTTTCCTGTTCTCCCTCTTTCTGGAAGCCTGGCTCAGGCCCCAGCCTGGAGCTTGTGTCTAGCTGAGTCCACGGGCTGAGTGGTCACTTTCCATCAGAGGGGCCCCGCGCTAGCGGCACTCCCTGGGCCCACAGGGCTACTCAGAGGTCTCTGGTGTGACACTGCCATGTGTCCTCACCCAGTTCGGGGCTGGGCCCGTGGGGCAGGGAGCTCTAGGAATGGACAGTGCATCCTGGGTACTAGGGTACCCTGGGTACCACAGGGCACCAGGTGTGCTGTGACCTCAGGTGACCCCAGCCCCGCCCTGCATGGCAGGAACATTGTCACCATTTCTCAGATAAAGACCCAGGAGACCAGCCTGGTTTGTTGGTTTTCCA"""

    def test_primerexonname2(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        name_to_dump = "DNM1L"
        results = zippy.zippyPrimerQuery(
            config, "12:32895523-32895682", True, None, db, None, [0],
            name_to_dump=name_to_dump, noncoding=False, combine=True,
            getgenes=None)

    @pytest.mark.skip("wait")
    def test_base0_vs_base1(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        name_to_dump = "DNM1L"
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
        zippy.gplist = None
        #assert 0, (results0, results1)

    def test_primerexonname208(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        results = zippy.zippyPrimerQuery(config, "12:25398208-25398318", True, None, db,
                                         None, [0, 1, 2], name_to_dump="KRAS")
        exon_number = 1 + config["exon_numbering_base"]
        assert results[0][0][0:2] == ['12:25398208-25398318', f'KRAS_{exon_number}'], results

    def test_chr11(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        results = zippy.zippyPrimerQuery(config, "11:118343121-118343321", True, None, db,
                                         None, [0, 1, 2], name_to_dump=None)
        logging.info(f"chr11 {results}")
        exon_number = 2 + config["exon_numbering_base"]
        assert results[0][0][0:2] == ['11:118343121-118343321', f'KMT2A_{exon_number}_2-3'],\
            results

    def test_chr12_2missing(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        results = zippy.zippyPrimerQuery(config, "12:115115461-115116484", True, None, db,
                                         None, [0, 1, 2], name_to_dump=None)
        assert len(results[0]) == 0, results

    @pytest.mark.skip("fastening tests")
    def test_primerexonname50(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        results = zippy.zippyPrimerQuery(config, "12:32892997-32893452", True, None, db,
                                         None, [0, 1, 2], name_to_dump="DNM1L")
        assert 0, results

    @pytest.mark.skip("fastening tests")
    def test_primerexonname3(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        results = zippy.zippyPrimerQuery(config, "12:32895351-32895785", True, None, db,
                                         None, [0, 1, 2], name_to_dump="DNM1L")
        assert 0, results

    @pytest.mark.skip("fastening tests")
    def test_primerexonname6(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        results = zippy.zippyPrimerQuery(config, "6:26091069-26091332", True, None, db,
                                         None, [0, 1, 2], name_to_dump=None)
        assert 0, results

    def test_snplimits(self, config):
        db = PrimerDB(config['database'], dump=config['ampliconbed'])
        zippy.gplist = None
        config["designlimits"]["criticalsnp"] == 20
        config["designlimits"]["snpcount"] == 20
        results = zippy.zippyPrimerQuery(config, "uploads/NEB_S2.smCounter.anno.vcf", True,
                                         None, db, None, [0, 1, 2], name_to_dump=None)
        zippy.gplist = None
        config["designlimits"]["criticalsnp"] == 0
        config["designlimits"]["snpcount"] == 0
        results2 = zippy.zippyPrimerQuery(config, "uploads/NEB_S2.smCounter.anno.vcf", True,
                                          None, db, None, [0, 1, 2], name_to_dump=None)
        zippy.gplist = None
        assert results == results2, (results, results2)

#if __name__ == '__main__':
#    unittest.main()
