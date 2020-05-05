# mapv/shp/shp.py

"""Shapefile parser."""

import re
import sys
import struct

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------

def int_big_end(data):
    """Convert 4 bytes in data (big-endian) to an integer"""
    return struct.unpack('>i', data)[0]

def int_lit_end(data):
    """Convert 4 bytes in data (little-endian) to an integer"""
    return struct.unpack('<i', data)[0]

def dbl_big_end(data):
    """Convert 8 bytes in data (big-endian) to an integer"""
    return struct.unpack('>d', data)[0]

def dbl_lit_end(data):
    """Convert 8 bytes in data (little-endian) to an integer"""
    return struct.unpack('<d', data)[0]

# Enumeration
def shape_type(n):
    return ('NullShape' if n == 0 else
            'Point' if n == 1 else
            'PolyLine' if n == 3 else
            'Polygon' if n == 5 else
            'MultiPoint' if n == 8 else
            'PointZ' if n == 11 else
            'PolyLineZ' if n == 13 else
            'PolygonZ' if n == 15 else
            'MultiPointZ' if n == 18 else
            'PointM' if n == 21 else
            'PolyLineM' if n == 23 else
            'PolygonM' if n == 25 else
            'MultiPointM' if n == 28 else
            'MultiPatch' if n == 31 else
            None)

#-------------------------------------------------------------------------------
# Main file header
#-------------------------------------------------------------------------------

class MainFileHeader():
    def __init__(self, file_code, file_length, version, shape_type, Xmin, Ymin,
                 Xmax, Ymax, Zmin, Zmax, Mmin, Mmax):
        self.file_code = file_code
        self.file_length = file_length
        self.version = version
        self.shape_type = shape_type
        self.Xmin = Xmin
        self.Ymin = Ymin
        self.Xmax = Xmax
        self.Ymax = Ymax
        self.Zmin = Zmin
        self.Zmax = Zmax
        self.Mmin = Mmin
        self.Mmax = Mmax

    def __str__(self):
        s = ''
        s += f'File code: {self.file_code}\n'
        s += f'Length: {self.file_length:_}\n'
        s += f'Version: {self.version}\n'
        s += f'Shape type: {shape_type(self.shape_type)}\n'
        s += f'Bboxes: minXY=({self.Xmin:_.2f}, {self.Ymin:_.2f})\n'
        s += f'Bboxes: maxXY=({self.Xmax:_.2f}, {self.Ymax:_.2f})\n'
        s += f'Bboxes: Z=({self.Zmin:_.2f}, {self.Zmax:_.2f})\n'
        s += f'Bboxes: M=({self.Mmin:_.2f}, {self.Mmax:_.2f})\n'
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        file_code = int_big_end(s[0:4])
        file_length = int_big_end(s[24:28])
        version = int_lit_end(s[28:32])
        shape_type = int_lit_end(s[32:36])
        Xmin = dbl_lit_end(s[36:44])
        Ymin = dbl_lit_end(s[44:52])
        Xmax = dbl_lit_end(s[52:60])
        Ymax = dbl_lit_end(s[60:68])
        Zmin = dbl_lit_end(s[68:76])
        Zmax = dbl_lit_end(s[76:84])
        Mmin = dbl_lit_end(s[84:92])
        Mmax = dbl_lit_end(s[92:100])

        return cls(file_code, file_length, version, shape_type, Xmin, Ymin,
                   Xmax, Ymax, Zmin, Zmax, Mmin, Mmax)

#-------------------------------------------------------------------------------
# ShapeFile - 
#-------------------------------------------------------------------------------

class ShapeFile():
    def __init__(self, hdr):
        self.hdr = hdr

    def __str__(self):
        return f'{self.hdr}'

#-------------------------------------------------------------------------------
# load_headers - 
#-------------------------------------------------------------------------------

def _load_headers(f):
    # Headers
    hdr = MainFileHeader.build(f.read(100))
       
    # Return a partial ShapeFile instance with the headers
    return ShapeFile(hdr)

def load_headers(filepath):
    """Create python objects from just the file headers."""
    with open(filepath, 'rb') as f:
        return _load_headers(f)

#-------------------------------------------------------------------------------
# load_data - 
#-------------------------------------------------------------------------------

def _load_data(f):
    # Get the headers first
    shp = _load_headers(f)

    return shp

def load_data(filepath):
    """Create python objects from file."""
    with open(filepath, 'rb') as f:
        return _load_data(f)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} <filepath>')
        exit(-1)

    filepath = sys.argv[1]
    shp = load_data(filepath)
    print(shp)
