# mapv/model_dlg3_t.py

"""model_dlg3.py implements a complex structure to represent files that are
open at any given time. The structure can be accessed by mapname or category,
and files can be opened by mapname, category, or individual filepath.

As of 2020/05/17, we have currenty 25 mapnames:

    boston-e_MA
    boston-w_MA
    brunswick-e_GA
    brunswick-w_GA
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

So we should have 125 (mapname, category) couples, but:

    boston, brunswick don't have public_lands
    monterey does not have hypsography

Which leaves us with 119 files available, but:

    boston, san_francisco, san_jose: boundaries files are unreadable

(We need to implement support for a variation on the DLG-3 file format that
uses variable-length records). So in the end there are 113 files that can be
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
# Helper functions
#-------------------------------------------------------------------------------

def build_filepath(mapname, category, filename):
    path = os.path.join(dlg_base_dir, mapname[0].upper())
    path = os.path.join(path, mapname)
    path = os.path.join(path, category)
    return os.path.join(path, filename)

#-------------------------------------------------------------------------------
# Dlg3_01_EmptyTest
#-------------------------------------------------------------------------------

class Dlg3_01_EmptyTest(unittest.TestCase):

    def test00_empty_model(self):
        model = Dlg3Model()
        category = 'hydrography'
        self.assertEqual(0, len(model.get_local_mapnames()))
        self.assertIsNone(model.get_first_file())
        self.assertIsNone(model.bounding_box())
        
        # Test the 'get_files_by_category' method
        g = model.get_files_by_category(category)
        with self.assertRaises(StopIteration):
            next(g)

        # Test open_files_category. Should add nothing, no new files, because
        # there is no open mapname yet.
        model.open_files_category(category)

        # Check that there are no files in this category
        g = model.get_files_by_category(category)
        with self.assertRaises(StopIteration):
            next(g)

#-------------------------------------------------------------------------------
# Dlg3_02_SingleTest
#-------------------------------------------------------------------------------

class Dlg3_02_SingleTest(unittest.TestCase):
    """Open a single file, then test all the available functions."""

    @classmethod
    def setUpClass(cls):
        """Called once before the tests are run.

        This loads one file into the model."""
        cls.model = Dlg3Model()
        cls.mapname = 'boston-e_MA'
        cls.category = 'hydrography'

        # Build a file path
        cls.filepath = build_filepath(cls.mapname, cls.category,
                                      '444595.HY.opt.gz')

        # Open file in the model
        cls.model.open(cls.filepath)
        
    def test01_first_file(self):
        # Check the file loaded in setUp(). Note that we use self to access the
        # class variables.
        self.assertEqual([self.mapname], self.model.get_local_mapnames())
        
    def test02_second_file(self):
        # Open another instance of the same file (only in the context of this
        # method, not in the shared model) for comparison purposes
        d = load_data(self.filepath)
        hdr_2nd = d.show_headers()

        # Test the 'get_first_file' method

        # FIXME the DlgFile class does not implement __eq__, so we can't test
        # dlg instances for equality. In the mean time, we settle for comparing
        # the dlg file headers.
        md = self.model.get_first_file()
        hdr_md = md.show_headers()
        self.assertEqual(hdr_2nd, hdr_md)

        # Test the 'get_files_by_category' method
        x = list(self.model.get_files_by_category(self.category))
        self.assertEqual(1, len(x))
        md = x[0]
        hdr_md = md.show_headers()
        self.assertEqual(hdr_2nd, hdr_md)

    def test04_more_in_category(self):
        # Open all the files for this category in already open sections
        self.model.open_files_category(self.category)
        
        # Mapnames haven't changed
        self.assertEqual([self.mapname], self.model.get_local_mapnames())
        
        # The hydrography category has not changed
        files = list(self.model.get_files_by_category(self.category))
        self.assertEqual(1, len(files))

        # FIXME make several tests
        
    def test05_another_category(self):
        # Open an entirely different category
        new_categ = 'transportation'
        self.model.open_files_category(new_categ)
        
        # Mapnames haven't changed
        self.assertEqual([self.mapname], self.model.get_local_mapnames())
        
        # There is still one file in the hydrography category...
        files = list(self.model.get_files_by_category(self.category))
        self.assertEqual(1, len(files))
        
        # ...but now there are 24 files in the new category
        files = list(self.model.get_files_by_category(new_categ))
        self.assertEqual(24, len(files))
      
#-------------------------------------------------------------------------------
# Dlg3_03_GetAllFilesTest
#-------------------------------------------------------------------------------

class Dlg3_03_GetAllFilesTest(unittest.TestCase):
    """Test the get_all_files method in various situations.

    When the model is empty.
    When there is just one file.
    When there are two files from the same mapname and category.
    When there are several files in the same mapname and several categories.
    When there are several files in several mapnames and categories.
    """
         
    def test01_empty_model(self):
        model = Dlg3Model()
        g = model.get_all_files()
        # Check that there are no files
        with self.assertRaises(StopIteration):
            next(g)
         
    def test02_single_file(self):
        model = Dlg3Model()
        filename = '453066.HY.opt.gz'
        model.open(build_filepath('brunswick-e_GA', 'hydrography',
                                  filename))
        x = list(model.get_all_files())
        self.assertEqual(1, len(x))
        self.assertEqual(filename, x[0].filename)
        
        # FIXME how can I check more about the file ?
         
    def test03_two_files(self):
        model = Dlg3Model()
        filename1 = '453066.HY.opt.gz'
        model.open(build_filepath('brunswick-e_GA', 'hydrography',
                                  filename1))
        filename2 = '453067.HY.opt.gz'
        model.open(build_filepath('brunswick-e_GA', 'hydrography',
                                  filename2))
        x = list(model.get_all_files())
        self.assertEqual(2, len(x))
        names = [y.filename for y in x]
        self.assertIn(filename1, names)
        self.assertIn(filename2, names)
         
    def test04_two_mapnames(self):
        model = Dlg3Model()
        filename1 = '525694.HY.opt.gz'
        model.open(build_filepath('los_angeles-e_CA', 'hydrography',
                                  filename1))
        filename2 = '525802.HY.opt.gz'
        model.open(build_filepath('long_beach-e_CA', 'hydrography',
                                  filename2))
        x = list(model.get_all_files())
        self.assertEqual(2, len(x))
        names = [y.filename for y in x]
        self.assertIn(filename1, names)
        self.assertIn(filename2, names)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
