# test_dlg.py -*- coding: utf-8 -*-

import unittest
from dlg import merge_attrs

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

# -----------------------------------------------------------------------------
# DlgTest
# -----------------------------------------------------------------------------

class DlgTest(unittest.TestCase):

    def test_01_both_dictionaries_empty(self):
        self.assertEqual({}, merge_attrs({}, {}))

    def test_02_one_empty_dictionary(self):
        d1 = dict(a=3)
        d3 = dict(a=3)
        self.assertEqual(d3, merge_attrs(d1, {}))

    def test_03_other_empty_dictionary(self):
        d2 = dict(a=3)
        d3 = dict(a=3)
        self.assertEqual(d3, merge_attrs({}, d2))

    def test_04_single_key_same(self):
        d1 = dict(a=3)
        d2 = dict(a=5)
        d3 = dict(a=8)
        self.assertEqual(d3, merge_attrs(d1, d2))

    def test_04_single_key_different(self):
        d1 = dict(a=3)
        d2 = dict(b=5)
        d3 = dict(a=3, b=5)
        self.assertEqual(d3, merge_attrs(d1, d2))

    def test_09_general_case(self):
        d1 = dict(aa=3, bb=5, gg=77, kk=89)
        d2 = dict(dd=91, bb=2, ff=52, kk=3, zz=75)
        d3 = dict(aa=3, bb=7, dd=91, ff=52, gg=77, kk=92, zz=75)
        self.assertEqual(d3, merge_attrs(d1, d2))

if __name__ == '__main__':
    unittest.main(verbosity=2)
