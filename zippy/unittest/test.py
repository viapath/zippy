#!/usr/bin/env python

import unittest, pysam, json
from zippy import zippy
#assert 0, zippy
#from . import zippy
from zippy.zippylib.database import PrimerDB
#This script is prepared to be run run from the zippy root folder as python -m zippy.unittest.test

class TestPrimers(unittest.TestCase):

    def setUp(self):
        # add primers to database
        raise NotImplementedError

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

class TestGenome(unittest.TestCase):
    def test_chr10(self):
        pfile = pysam.FastaFile("/var/local/zippy/resources/human_g1k_v37.fasta")
        args =('10', 43613278, 43614409)
        fetched = pfile.fetch(*args)
        print("testchr10", fetched)
    def test_primerexonname2(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            results = zippy.zippyPrimerQuery(config, "12:32895523-32895682", True, None, db,
                None, [0, 1, 2])
            assert 0, results
        """
ordinal 0-based chr start emn name strand
1 0 12      32832297        32832399        DNM1L 1
2 1 12      32854348        32854496        DNM1L 1
3 2 12      32858758        32858797        DNM1L 1
4 3 12      32860300        32860347        DNM1L 1
5 4 12      32861086        32861158        DNM1L 1
6 5 12      32863862        32863949        DNM1L 1
7 6 12      32866142        32866305        DNM1L 1
8 7 12      32871576        32871697        DNM1L 1
9 8 12      32873597        32873729        DNM1L 1
10 9 12     32875360        32875567        DNM1L 1
11 10 12    32883947        32884068        DNM1L 1
12 11 12    32884289        32884445        DNM1L 1
13 12 12    32884787        32884877        DNM1L 1
14 13 12    32886648        32886741        DNM1L 1
15 14 12    32890038        32890095        DNM1L 1
16 15 12    32890798        32890876        DNM1L 1
17 16 12    32891197        32891230        DNM1L 1
18 17 12    32892997        32893174        DNM1L 1
19 18 12    32893342        32893452        DNM1L 1
20 19 12    32895522        32895682        DNM1L 1
21 20 12    32896287        32896344        DNM1L 1

        """
    def wtest_primerexonname1(self):
        with open("zippy/zippy.json") as conf:
            config = json.load(conf)
            db = PrimerDB(config['database'],dump=config['ampliconbed'])
            results = zippy.zippyPrimerQuery(config, "6:26091069-26091332", True, None, db,
                None, [0, 1, 2])
            assert 0, results

if __name__ == '__main__':
    unittest.main()
