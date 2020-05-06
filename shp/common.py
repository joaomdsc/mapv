# mapv/shp/common.py

"""Common functions for Shapefile parsing."""

import struct
from enum import Enum, auto, unique

#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------

# int_/dbl_ return a single value, ints_/dbls_ return an array of values
def int_big_end(data):
    """Convert 4 bytes in data (big-endian) to an integer"""
    return struct.unpack(f'>i', data)[0]

def ints_big_end(data, n=1):
    """Convert 4*n bytes in data (big-endian) to an array of n integers"""
    return struct.unpack(f'>{n}i', data)

def int_lit_end(data):
    """Convert 4 bytes in data (little-endian) to an integer"""
    return struct.unpack(f'<i', data)[0]

def ints_lit_end(data, n=1):
    """Convert 4*n bytes in data (little-endian) to an array of n integers"""
    return struct.unpack(f'<{n}i', data)

def dbl_big_end(data):
    """Convert 8 bytes in data (big-endian) to a double"""
    return struct.unpack(f'>d', data)[0]

def dbls_big_end(data, n=1):
    """Convert 8*n bytes in data (big-endian) to an array of n doubles"""
    return struct.unpack(f'>{n}d', data)

def dbl_lit_end(data):
    """Convert 8 bytes in data (little-endian) to a double"""
    return struct.unpack(f'<d', data)[0]

def dbls_lit_end(data, n=1):
    """Convert 8*n bytes in data (little-endian) to an array of n doubles"""
    return struct.unpack(f'<{n}d', data)

def fmt_data(x):
    return f'{x:_.2f}' if x > 1e-38 else ''

def fmt_no_data(x):
    return f'{x:_.2f}' if x > 1e-38 else 'no_data'

#-------------------------------------------------------------------------------
# Shape type enum
#-------------------------------------------------------------------------------

@unique
class ShapeType(Enum):
    """Represent the possible shape types."""
    NullShape = auto()
    Point = auto()
    PolyLine = auto()
    Polygon = auto()
    MultiPoint = auto()
    PointZ = auto()
    PolyLineZ = auto()
    PolygonZ = auto()
    MultiPointZ = auto()
    PointM = auto()
    PolyLineM = auto()
    PolygonM = auto()
    MultiPointM = auto()
    MultiPatch = auto()

    def __str__(self):
        """Print out 'Point' instead of 'ShapeType.Point'."""
        return self.name

    # Enumeration
    def from_int(n):
        return (ShapeType.NullShape if n == 0 else
                ShapeType.Point if n == 1 else
                ShapeType.PolyLine if n == 3 else
                ShapeType.Polygon if n == 5 else
                ShapeType.MultiPoint if n == 8 else
                ShapeType.PointZ if n == 11 else
                ShapeType.PolyLineZ if n == 13 else
                ShapeType.PolygonZ if n == 15 else
                ShapeType.MultiPointZ if n == 18 else
                ShapeType.PointM if n == 21 else
                ShapeType.PolyLineM if n == 23 else
                ShapeType.PolygonM if n == 25 else
                ShapeType.MultiPointM if n == 28 else
                ShapeType.MultiPatch if n == 31 else
                None)

#-------------------------------------------------------------------------------
# Parsing error
#-------------------------------------------------------------------------------

class ShpParser(Exception):
    def __init__(self, msg):
        super().__init__(msg)

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
        s += f'Shape type: {self.shape_type}\n'
        s += f'Bboxes: minXY=({self.Xmin:_.2f}, {self.Ymin:_.2f})\n'
        s += f'Bboxes: maxXY=({self.Xmax:_.2f}, {self.Ymax:_.2f})\n'
        s += f'Bboxes: Z=({fmt_no_data(self.Zmin)}, {fmt_no_data(self.Zmax)})\n'
        s += f'Bboxes: M=({fmt_no_data(self.Mmin)}, {fmt_no_data(self.Mmax)})'
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        file_code = int_big_end(s[0:4])
        file_length = 2*(int_big_end(s[24:28]))  # in bytes
        version = int_lit_end(s[28:32])
        shape_type = ShapeType.from_int(int_lit_end(s[32:36]))
        Xmin = dbl_lit_end(s[36:44])
        Ymin = dbl_lit_end(s[44:52])
        Xmax = dbl_lit_end(s[52:60])
        Ymax = dbl_lit_end(s[60:68])
        Zmin = dbl_big_end(s[68:76])
        Zmax = dbl_big_end(s[76:84])
        Mmin = dbl_big_end(s[84:92])
        Mmax = dbl_big_end(s[92:100])

        return cls(file_code, file_length, version, shape_type, Xmin, Ymin,
                   Xmax, Ymax, Zmin, Zmax, Mmin, Mmax)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    