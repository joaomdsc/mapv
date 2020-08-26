# mapv/storage.py

"""This module handles everything related to the filesystem, it doesn't know
about file contents."""

import os
import re

# This contradicts the above.
from dlg import load_headers

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
# Globals
#-------------------------------------------------------------------------------

# This directory holds 1846 different place names
dlg_base_dir = r'C:\a\carto\data\dds.cr.usgs.gov\pub\data\DLG\100K'

pattern = "^([a-z'-_.]+-[ew])_([A-Z]{2})$"

dense = {
    'F01': ('S01', 'S02', 'S09', 'S10'),
    'F02': ('S03', 'S04', 'S11', 'S12'),
    'F03': ('S05', 'S06', 'S13', 'S14'),
    'F04': ('S07', 'S08', 'S15', 'S16'),
    'F05': ('S17', 'S18', 'S25', 'S26'),
    'F06': ('S19', 'S20', 'S27', 'S28'),
    'F07': ('S21', 'S22', 'S29', 'S30'),
    'F08': ('S23', 'S24', 'S31', 'S32'),
}

normal = {
    'S01': 'F01',
    'S02': 'F01',
    'S03': 'F02',
    'S04': 'F02',
    'S05': 'F03',
    'S06': 'F03',
    'S07': 'F04',
    'S08': 'F04',
    'S09': 'F01',
    'S10': 'F01',
    'S11': 'F02',
    'S12': 'F02',
    'S13': 'F03',
    'S14': 'F03',
    'S15': 'F04',
    'S16': 'F04',
    'S17': 'F05',
    'S18': 'F05',
    'S19': 'F06',
    'S20': 'F06',
    'S21': 'F07',
    'S22': 'F07',
    'S23': 'F08',
    'S24': 'F08',
    'S25': 'F05',
    'S26': 'F05',
    'S27': 'F06',
    'S28': 'F06',
    'S29': 'F07',
    'S30': 'F07',
    'S31': 'F08',
    'S32': 'F08',
}

categ_dir = dict(
    HY='hydrography',
    BO='boundaries',
    HP='hypsography',
    PL='public_lands',
    RR='transportation',
    MT='transportation',
    RD='transportation',
)

#-------------------------------------------------------------------------------
# mapnames
#-------------------------------------------------------------------------------

def mapnames():
    """(state, place name) couples."""
    states = {}
    for f in os.listdir(dlg_base_dir):
        if len(f) > 1:
            continue
        # Uppercase initials
        letter = os.path.join(dlg_base_dir, f)

        for name in os.listdir(letter):
            if name == 'index.html' or name.endswith('.1'):
                continue
            m = re.match(pattern, name)
            if not m:
                continue
            name = m.group(1)
            state = m.group(2)
            yield state, name
 
#-------------------------------------------------------------------------------
# mapname_filepaths
#-------------------------------------------------------------------------------

def mapname_filepaths(mapname, category=None):
    """DLG-3 filepaths in the given mapname."""
    path = os.path.join(dlg_base_dir, mapname[0].upper())
    path = os.path.join(path, mapname)

    if not os.path.isdir(path):
        print(f"Can't find '{mapname}'")
        return
    for f in os.listdir(path):
        if category is not None and f != category:
            continue
        layer = os.path.join(path, f)
        if os.path.isdir(layer):
            for g in os.listdir(layer):
                if g.endswith('.opt.gz'):
                    filepath = os.path.join(layer, g)
                    yield filepath
 
#-------------------------------------------------------------------------------
# local_mapnames
#-------------------------------------------------------------------------------

def local_mapnames(ca_only=False):
    """Directory paths for mapnames saved locally."""
    path = os.path.join(dlg_base_dir)
    for f in os.listdir(path):
        m = re.match('[A-Z]', f)
        if not m:
            continue
        letter = os.path.join(path, f)
        for f in os.listdir(letter):
            m = re.match(pattern, f)
            if not m:
                continue
            # Temp. just California (pb with UTM zones)
            if ca_only and not f.endswith('_CA'):
                continue
            map_path = os.path.join(letter, f)
            # When a mapname hasn't been downloaded, the directory usually
            # holds just an index.html file.
            if len(os.listdir(map_path)) <= 1:
                continue
            # print(f'Yielding {map_path}')
            yield map_path
 
#-------------------------------------------------------------------------------
# local_categories
#-------------------------------------------------------------------------------

# FIXME unused

def local_categories():
    """Mapname/categories that have been saved locally (incl. CA)."""
    path = os.path.join(dlg_base_dir)
    # One directory for each uppercase letter
    for f in os.listdir(path):
        m = re.match('[A-Z]', f)
        if not m:
            continue
        letter = os.path.join(path, f)
        # Mapnames that start with this letter
        for mapname in os.listdir(letter):
            m = re.match(pattern, mapname)
            if not m:
                continue
            map_path = os.path.join(letter, mapname)
            if not os.path.isdir(map_path):
                # We are only interested in the sub-directories here, but there
                # is also an index.html file, and wget tends to create spurious
                # files named *.1, ignore them both.
                continue
            # When a mapname hasn't been downloaded, the directory usually
            # holds just an index.html file.
            if len(os.listdir(map_path)) <= 1:
                continue
            # Under the map path there are categories, plus an index.html file
            for category in os.listdir(map_path):
                yield os.path.join(map_path, category)
 
#-------------------------------------------------------------------------------
# local_files
#-------------------------------------------------------------------------------

# FIXME re-write in terms of local_categories
def local_files(mapname):
    """List of (category, sample_filepath) couples for a local mapname."""
    path = os.path.join(dlg_base_dir, mapname[0].upper())
    path = os.path.join(path, mapname)

    if not os.path.isdir(path):
        print(f"Can't find '{mapname}'")
        return
    for f in os.listdir(path):
        layer = os.path.join(path, f)
        if os.path.isdir(layer):
            for g in os.listdir(layer):
                if g.endswith('.opt.gz'):
                    filepath = os.path.join(layer, g)
                    yield layer, filepath
                    break

#-------------------------------------------------------------------------------
# local_everything
#-------------------------------------------------------------------------------

def local_everything():
    """Summary of everything that's been saved locally (incl. CA)."""
    path = dlg_base_dir
    # One directory for each uppercase letter
    for f in os.listdir(path):
        m = re.match('[A-Z]', f)
        if not m:
            continue
        letter = os.path.join(path, f)
        # Mapnames that start with this letter
        for mapname in os.listdir(letter):
            m = re.match(pattern, mapname)
            if not m:
                continue
            map_path = os.path.join(letter, mapname)
            if not os.path.isdir(map_path):
                # We are only interested in the sub-directories here, but there
                # is also an index.html file, and wget tends to create spurious
                # files named *.1, ignore them both.
                continue
            # When a mapname hasn't been downloaded, the directory usually
            # holds just an index.html file.
            if len(os.listdir(map_path)) <= 1:
                continue
            # Under the map path there are categories, plus an index.html file
            for category in os.listdir(map_path):
                categ_path = os.path.join(map_path, category)
                if not os.path.isdir(categ_path):
                    # We are only interested in the sub-directories here, but there
                    # is also an index.html file, ignore it.
                    continue
                for f in os.listdir(categ_path):
                    filepath = os.path.join(categ_path, f)
                    if os.path.isdir(filepath) or not f.endswith('.opt.gz'):
                        # We are only interested in files ending in '.opt.gz'.
                        continue
                    yield filepath
 
def every_categ():
    """Category directory name, 2-letter filename code, internal name."""

    # csv file header
    s = ''
    s += 'Mapname\tCategDir\tCategFile\tCode\tSection\tNumber\tFilename'
    print(s)

    for filepath in local_everything():
        filename = os.path.basename(filepath)
        m = re.match('([0-9]+)\.([A-Z]{2}).opt.gz', filename)
        number = m.group(1)
        code = m.group(2)
        
        categ_path = os.path.dirname(filepath)
        category = os.path.basename(categ_path)

        map_path = os.path.dirname(categ_path)
        mapname = os.path.basename(map_path)
        
        try:
            d = load_headers(filepath)
        except ValueError:
            continue

        s = ''
        s += f'{mapname}\t{category}\t{code}\t{d.categ.name}\t{d.section}\t{number}\t{filename}'
        print(s)

def everything_csv():
    """Summary of everything that's been saved locally in a .csv file."""

    # csv file header
    s = ''
    s += 'Mapname\tCategory\tFilename\tZone\tSection\tData cell\tCategory'
    print(s)

    for filepath in local_everything():
        try:
            d = load_headers(filepath)
        except ValueError:
            continue

        # Reconstruct mapname and category from filepath 
        s = ''
        s += f'{mapname}\t{category}\t{d.filename}\t{d.zone}'
        s += f'\t{d.section}\t{d.data_cell}\t{d.category}'
        print(s)

#-------------------------------------------------------------------------------
# get_matching_filepaths
#-------------------------------------------------------------------------------
  
def get_matching_filepaths(mapname, category, section):
    """Return an array of filepaths matching this 3-uple.
    
    The return value is either None, if this mapname does not include this
    section, or an array. The array contains a single filepath if the section
    is normal, or four filepaths if the section is dense.
    """
    # Get the mapname/category directory
    path = os.path.join(dlg_base_dir, mapname[0].upper())
    path = os.path.join(path, mapname)
    path = os.path.join(path, categ_dir[category])

    if not os.path.isdir(path):
        return

    # If category == 'RD', and: if there are more than 4 RD files, or, if any
    # RD file has sectional indicator 'S': then the target section is dense.
    if category != 'RD':
        is_dense = False
    else:
        for f in os.listdir(path):
            filepath = os.path.join(path, f)
            m = re.match('[0-9]+.RD.opt.gz', f)
            if m:
                d = load_headers(filepath)
                is_dense = d.section.startswith('S')

    # This is what we need to retrieve
    target = dense[section] if is_dense else [section]

    # This is what we actually retrieve
    filepaths = []

    for f in os.listdir(path):
        # Get one file
        filepath = os.path.join(path, f)
        if os.path.isdir(filepath) or not f.endswith('.opt.gz'):
            continue
        try:
            d = load_headers(filepath)
        except ValueError:
            continue

        # Does it match our requirements?
        if d.section in target:
            filepaths.append(filepath)
            if len(filepaths) == len(target):
                return filepaths
  
#-------------------------------------------------------------------------------
# Persist a directory path between program runs
#-------------------------------------------------------------------------------
  
def get_dir():
    """Retrieve the persisted directory path."""
    filepath = os.path.join(os.environ.get('HOME'), '.mapv')
    if not os.path.isfile(filepath):
        return dlg_base_dir
    with open(filepath, 'r') as f:
        # Assume file contains just the directory path
        return f.read().strip()

def set_dir(dir):
    """Persist the given directory path."""
    filepath = os.path.join(os.environ.get('HOME'), '.mapv')
    with open(filepath, 'w') as f:
        f.write(dir)
  
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # print('This module is not meant to be executed directly.')
    # for s, n in sorted(mapnames()):
    #     print(f'{s}\t{n}')

    # for mp in local_mapnames():
    #     for l, f in local_files(mp):
    #         print(f'{os.path.basename(mp)} {os.path.basename(l)} {os.path.basename(f)}')

    every_categ()