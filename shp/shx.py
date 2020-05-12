# mapv/shp/shx.py

"""Shapefile index file parser."""

import sys
from .common import ShapeType, ShpParser, MainFileHeader
import shp.common as c

#-------------------------------------------------------------------------------
# IndexRec
#-------------------------------------------------------------------------------

class IndexRec():
    def __init__(self, offset, content_len):
        self.offset = offset
        self.content_len = content_len

    def __str__(self):
        s = ''
        s += f'{self.offset:_} {self.content_len}'
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        offset = 2*(c.int_big_end(s[0:4]))  # in bytes
        content_len = 2*(c.int_big_end(s[4:8]))  # in bytes

        return cls(offset, content_len)

#-------------------------------------------------------------------------------
# ShxFile - 
#-------------------------------------------------------------------------------

class ShxFile():
    def __init__(self, hdr):
        self.hdr = hdr
        self.recs = []

    def __str__(self):
        s = ''
        s += f'{self.hdr}\n'
        for r in self.recs:
            s += f'{r}\n'
        return s

#-------------------------------------------------------------------------------
# Building a ShxFile from outside data
#-------------------------------------------------------------------------------

def build_record(f):
    """Offset is the current offset in the file."""
    # Record header (length is number of 16-bit words)
    s = f.read(8)
    if s == b'':
        # EOF (note the 'b' above)
        return None
    rec = IndexRec.build(s)

    return rec

def _build(f):
    # Get the header first
    shx = _build_header(f)

    # Get the datarecords
    while True:
        rec = build_record(f)
        if rec is None:
            break
        shx.recs.append(rec)
    return shx

def build(filepath):
    """Build a class instance from a file."""
    with open(filepath, 'rb') as f:
        return _build(f)

def _build_header(f):
    hdr = MainFileHeader.build(f.read(100))
    return ShxFile(hdr)

def build_header(filepath):
    """Create a class instance from just the file header."""
    with open(filepath, 'rb') as f:
        return _build_header(f)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} <filepath>')
        exit(-1)

    filepath = sys.argv[1]

    with open(filepath, 'rb') as f:
        s = f.read()
    print(f'File is {len(s):_} bytes long, hence {int((len(s)-100)/8)} records.')
    shx = build(filepath)
    print(shx)
