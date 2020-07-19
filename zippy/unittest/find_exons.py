#!/usr/bin/env python

import unittest, pysam, json, sys
from zippy import zippy
from zippy.zippylib import range_string
from zippy.zippylib.database import PrimerDB

with open("zippy/zippy.json") as conf:
    config = json.load(conf)
    db = PrimerDB(config['database'],dump=config['ampliconbed'])
    zippy.gplist = None
    results = zippy.zippyPrimerQuery(config, sys.argv[1], True, None, db,
        None, [0, 1, 2], name_to_dump=sys.argv[2])
