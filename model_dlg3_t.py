# mapv/model_dlg3_t.py

"""model_dlg3.py implements a complex structure to represent files that are
open at any given time. The structure can be accessed by mapname or category,
and files can be opened by mapname, category, or individual filepath.

We have currenty 23 mapnames:

    boston-e_MA
    boston-w_MA
    cambria-e_CA
    cambria-w_CA
    cuyama-e_CA
    cuyama-w_CA
    long_beach-e_CA
    los_angeles-e_CA
    los_angeles-w_CA
    monterey-e_CA
    monterey-w_CA
    new_roads-e_LA
    new_roads-w_LA
    san_francisco-e_CA
    san_francisco-w_CA
    san_jose-e_CA
    san_jose-w_CA
    san_luis_obispo-e_CA
    san_luis_obispo-w_CA
    santa_barbara-e_CA
    santa_barbara-w_CA
    santa_maria-e_CA
    santa_maria-w_CA

There are normally 5 categories:

    boundaries
    hydrography
    hypsography
    public_lands
    transportation

So we should have 115 (mapname, category) couples, but:

    boston does not have public_lands
    monterey does not have hypsography

Which leaves us with 111 files available, but:

    boston, san_francisco, san_jose: boundaries files are unreadable

(We need to implement support for a variation on the DLG-3 file format that
uses variable-length records). So in the end there are 105 files that can be
opened.

"""
import os
import unittest

from dlg import load_data
from model_dlg3 import Dlg3Model
from storage import dlg_base_dir

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
# Dlg3Test
#-------------------------------------------------------------------------------

class Dlg3Test(unittest.TestCase):

    def test00_empty_model(self):
        model = Dlg3Model()
        category = 'hydrography'
        self.assertEqual(0, len(model.get_mapnames()))
        self.assertIsNone(model.get_first_file())
        self.assertIsNone(model.bounding_box())
        
        # Test the 'get_files_by_category' method
        g = model.get_files_by_category(category)
        with self.assertRaises(StopIteration):
            next(g)
  
        # Test open_category. Should add nothing, no new files, because there
        # is no open mapname yet.
        model.open_category(category)

        # Check that there areno files in this category
        g = model.get_files_by_category(category)
        with self.assertRaises(StopIteration):
            next(g)

    def test01_single_file(self):
        model = Dlg3Model()
        mapname = 'boston-e_MA'
        category = 'hydrography'

        # Build a file path
        path = os.path.join(dlg_base_dir, 'B')
        path = os.path.join(path, mapname)
        path = os.path.join(path, category)
        filepath = os.path.join(path, '444595.HY.opt.gz')

        # Open file in the model
        model.open(filepath)

        self.assertEqual([mapname], model.get_mapnames())

        # Open another instance for comparison purposes
        d = load_data(filepath)
        hdr_d = d.show_headers()

        # Test the 'get_first_file' method

        # FIXME the DlgFile class does not implement __eq__, so we can't test
        # dlg instances for equality. In the mean time, we settle for comparing
        # the dlg file headers.
        md = model.get_first_file()
        hdr_md = md.show_headers()
        self.assertEqual(hdr_d, hdr_md)

        # Test the 'get_files_by_category' method
        x = list(model.get_files_by_category(category))
        self.assertEqual(1, len(x))
        md = x[0]
        hdr_md = md.show_headers()
        self.assertEqual(hdr_d, hdr_md)

        # Open all the other files in the same category
        model.open_category(category)
        
        # Mapnames haven't changed
        self.assertEqual([mapname], model.get_mapnames())
        
        # There are now 4 files in the hydrography catgeory
        files = list(model.get_files_by_category(category))
        self.assertEqual(4, len(files))

        # FIXME make several tests
        
        # Open an entirely different category
        new_categ = 'transportation'
        model.open_category(new_categ)
        
        # Mapnames haven't changed
        self.assertEqual([mapname], model.get_mapnames())
        
        # There are still 4 files in the hydrography category...
        files = list(model.get_files_by_category(category))
        self.assertEqual(4, len(files))
        
        # ...but now there are 24 files in the new catgeory
        files = list(model.get_files_by_category(new_categ))
        self.assertEqual(24, len(files))
        
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
