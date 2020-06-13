#!/usr/bin/env python

import unittest, pysam

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
        assert 0, fetched

if __name__ == '__main__':
    unittest.main()
