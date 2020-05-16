# mapv/storage.py

"""This module handles everything related to the filesystem, it doesn't know
about file contents."""

import os
import re
      
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
dlg_base_dir = r'C:\x\carto\data\dds.cr.usgs.gov\pub\data\DLG\100K'

pattern = "^([a-z'-_.]+-[ew])_([A-Z]{2})$"

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
    """DLG-3 filenames in the given mapname."""
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

def local_categories(mapname):
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

    for mp in local_mapnames():
        for l, f in local_categories(mp):
            print(f'{os.path.basename(mp)} {os.path.basename(l)} {os.path.basename(f)}')