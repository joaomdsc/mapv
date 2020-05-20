# mapv/storage_t.py

import os
import unittest

from storage import dlg_base_dir, get_matching_filepaths

#-------------------------------------------------------------------------------
# I want stdout to be unbuffered, always
#-------------------------------------------------------------------------------

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout = Unbuffered(sys.stdout)

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------

def categ_filepath(mapname, category):
    path = os.path.join(dlg_base_dir, mapname[0].upper())
    path = os.path.join(path, mapname)
    return os.path.join(path, category)

#-------------------------------------------------------------------------------
# StorageTest
#-------------------------------------------------------------------------------

class StorageTest(unittest.TestCase):

    def test00_no_match(self):
        mapname = 'boston-e_MA'
        category = 'hydrography'
        x = get_matching_filepaths(mapname, category, 'F01')
        self.assertIsNone(x)

    def test01_hydrography(self):
        mapname = 'boston-e_MA'
        category = 'hydrography'
        x = get_matching_filepaths(mapname, category, 'F03')
        s = os.path.join(categ_filepath(mapname, category), '444595.HY.opt.gz')
        self.assertEqual([s], x)

    def test02_boundaries(self):
        mapname = 'boston-e_MA'
        category = 'boundaries'
        x = get_matching_filepaths(mapname, category, 'F08')
        s = os.path.join(categ_filepath(mapname, category), '444640.BD.opt.gz')
        self.assertEqual([s], x)

    def test03_transportation(self):
        mapname = 'boston-e_MA'
        category = 'transportation'
        x = get_matching_filepaths(mapname, category, 'F04')
        
        arr = []
        s = os.path.join(categ_filepath(mapname, category), '444637.RD.opt.gz')
        arr.append(s)
        s = os.path.join(categ_filepath(mapname, category), '444618.RD.opt.gz')
        arr.append(s)
        s = os.path.join(categ_filepath(mapname, category), '444629.RD.opt.gz')
        arr.append(s)
        s = os.path.join(categ_filepath(mapname, category), '444628.RD.opt.gz')
        arr.append(s)
        
        self.assertEqual(sorted(arr), x)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
