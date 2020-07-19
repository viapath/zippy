#!/usr/bin/env python

import unittest, pysam, json
from zippy import zippy
from zippy.zippylib import range_string
from zippy.zippylib.database import PrimerDB
#This script is prepared to be run run from the zippy root folder as python -m zippy.unittest.test

class TestRanges(unittest.TestCase):
    def test_range1(self):
        rs = range_string([1,2,3,4,5, 7,8,9, 11, 14])
        self.assertEqual(rs, "1-5,7-9,11,14")
    def test_range2(self):
        rs = range_string([1,3,4,5, 7,8,9, 11, 14])
        self.assertEqual(rs, "1,3-5,7-9,11,14")

class TestPrimers(unittest.TestCase):

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
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

#@unittest.skip("accelerate the testing")
class TestGenome(unittest.TestCase):
    def test_chr10(self):
        pfile = pysam.FastaFile("/var/local/zippy/resources/human_g1k_v37.fasta")
        args =('10', 43613278, 43614409)
        fetched = pfile.fetch(*args)
        self.assertEqual(fetched, """TGGTAACTAACGGAGTGTGAGCTGCTGACGTGTGTGTGACGGATACATCAGCAGCACAGGAGATGCCTGGGCTCCAGGCTGGCCATCTCAGACAGGAGCGGGAAATGGGGAGCCTGGTCGCGGTGTGTGGACCTCCTTTATGGCTCTCCACCTTCTCCAGGGCCTCTCCCGACAAGTGGGTGTGTGGGTACCCCTCACCTTTCCAGAATGATTAATGCGGGGAATTTCTGTGGACGACTGTCTTCTAAAGACAATGACTACAGGAACATAATGCCACATACACAGGTGGCCCAGCCCTGGGACACTCTGGGGAAAGATCCGGCATGTGTGGTTGCTGGCTCCTCAGGGTGCTTCTTCCTCAGGGTGGATGAGGCCCCTGTCCACTGATCCCAAAGGCTGGGAGAAGCCTCAAGCAGCATCGTCTTTGCAGGCCTCTCTGTCTGAACTTGGGCAAGGCGATGCAGGTCCATCCTGACCTGGTATGGTCATGGAAGGGGCTTCCAGGAGCGATCGTTTGCAACCTGCTCTGTGCTGCATTTCAGAGAACGCCTCCCCGAGTGAGCTGCGAGACCTGCTGTCAGAGTTCAACGTCCTGAAGCAGGTCAACCACCCACATGTCATCAAATTGTATGGGGCCTGCAGCCAGGATGGTAAGGCCAGCTGCAGGGTGAGGTGGGCAGCCACTGCACCCAGGCTGGGGGCTCCATACAGCCCTGTTCTCCCTCTTTCTCCCTTTCCCTACTGCTCCTGCCCTGTTTCCTGTTCTCCCTCTTTCTGGAAGCCTGGCTCAGGCCCCAGCCTGGAGCTTGTGTCTAGCTGAGTCCACGGGCTGAGTGGTCACTTTCCATCAGAGGGGCCCCGCGCTAGCGGCACTCCCTGGGCCCACAGGGCTACTCAGAGGTCTCTGGTGTGACACTGCCATGTGTCCTCACCCAGTTCGGGGCTGGGCCCGTGGGGCAGGGAGCTCTAGGAATGGACAGTGCATCCTGGGTACTAGGGTACCCTGGGTACCACAGGGCACCAGGTGTGCTGTGACCTCAGGTGACCCCAGCCCCGCCCTGCATGGCAGGAACATTGTCACCATTTCTCAGATAAAGACCCAGGAGACCAGCCTGGTTTGTTGGTTTTCCA""")
        #print("testchr10", fetched)
    #@unittest.skip("fastening tests")
    def test_primerexonname2(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            config["blacklistcache"]="/dev/null"
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32895523-32895682", True, None, db,
                None, [0, 1, 2], name_to_dump="DNM1L")
            assert 0, results
    @unittest.skip("fastening tests")
    def test_primerexonname2_dontcombine(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            config["blacklistcache"]="/dev/null"
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32895523-32895682", True, None, db,
                None, [0, 1, 2], name_to_dump="DNM1L")
            assert 0, results
    @unittest.skip("fastening tests")
    def test_primerexonname50(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32892997-32893452", True, None, db,
                None, [0, 1, 2], name_to_dump="DNM1L")
            assert 0, results
    @unittest.skip("fastening tests")
    def test_primerexonname3(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "12:32895351-32895785", True, None, db,
                None, [0, 1, 2], name_to_dump="DNM1L")
            assert 0, results
    @unittest.skip("fastening tests")
    def test_primerexonname1(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            zippy.gplist = None
            results = zippy.zippyPrimerQuery(config, "6:26091069-26091332", True, None, db,
                None, [0, 1, 2], name_to_dump=None)
            assert 0, results
    @unittest.skip("fastening tests")
    def test_snplimits(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            config["blacklistcache"]="/dev/null"
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
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
            assert results==results2, (results, results2)

if __name__ == '__main__':
    unittest.main()
