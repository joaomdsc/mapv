# mapv/shp/shp.py

"""Shapefile parser."""

import os
import sys
from .common import ShapeType, ShpParser, MainFileHeader
import shp.common as c
from .shx import build_header

first = True

#-------------------------------------------------------------------------------
# ShpBaseRec
#-------------------------------------------------------------------------------

class ShpBaseRec:
    def __init__(self, rec_nbr, offset, rec_len, shape_type):
       self.rec_nbr = rec_nbr
       self.offset = offset
       self.rec_len = rec_len
       self.shape_type = shape_type
 
    def __str__(self):
        s = ''
        s += f'{self.rec_nbr:>06} {self.offset:_} {self.rec_len}'
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s):
        """Build a class instance from a string."""
        shape_type = ShapeType.from_int(c.int_lit_end(s[32:36]))

        return cls(rec_nbr, offset, rec_len, shape_type)

#-------------------------------------------------------------------------------
# NullShapeRec
#-------------------------------------------------------------------------------

class NullShapeRec(ShpBaseRec):
    def __init__(self, rec_nbr, offset, rec_len, shape_type):
        super().__init__(rec_nbr, offset, rec_len, shape_type)
 
    def __str__(self):
        s = ''
        s += super().__str__()
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s):
        """Build a class instance from a string."""
        shape_type = ShapeType.from_int(c.int_lit_end(s[32:36]))

        return cls(rec_nbr, offset, rec_len, shape_type)

#-------------------------------------------------------------------------------
# PointRec
#-------------------------------------------------------------------------------

class PointRec(ShpBaseRec):
    def __init__(self, rec_nbr, offset, rec_len, shape_type, X, Y):
        super().__init__(rec_nbr, offset, rec_len, shape_type)
        self.X = X
        self.Y = Y

    def __str__(self):
        s = ''
        s += super().__str__()
        s += f', (X,Y)=({self.X:_.2f}, {self.Y:_.2f})'
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s, shape_type):
        """Build a class instance from a string."""
        X = c.dbl_lit_end(s[4:12])
        Y = c.dbl_lit_end(s[12:20])

        return cls(rec_nbr, offset, rec_len, shape_type, X, Y)

#-------------------------------------------------------------------------------
# PolyRec
#-------------------------------------------------------------------------------

class PolyRec(ShpBaseRec):
    """Represents both PolyLines and Polygons"""
    def __init__(self, rec_nbr, offset, rec_len, shape_type, box, num_parts,
                 num_points, parts, points):
        super().__init__(rec_nbr, offset, rec_len, shape_type)
        self.box = box  # array of 4 doubles
        self.num_parts = num_parts
        self.num_points = num_points
        self.parts = parts  # array of num_parts integers
        self.points = points  # array of num_points (X, Y) couples (doubles)

    def __str__(self):
        s = ''
        s += super().__str__()
        s += f', parts={self.num_parts:_}, points={self.num_points:_}'
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s, shape_type):
        """Build a class instance from a string."""
        box = c.dbls_lit_end(s[4:36], n=4)
        num_parts = c.int_lit_end(s[36:40])
        num_points = c.int_lit_end(s[40:44])
        X = 44 + 4*num_parts
        parts = c.ints_lit_end(s[44:X], num_parts)
        Y = X + 16*num_points
        coords = c.dbls_lit_end(s[X:Y], 2*num_points)
        points = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

        return cls(rec_nbr, offset, rec_len, shape_type, box, num_parts,
                   num_points, parts, points)

#-------------------------------------------------------------------------------
# PointMRec
#-------------------------------------------------------------------------------

class PointMRec(PointRec):
    def __init__(self, rec_nbr, offset, rec_len, shape_type, X, Y, M=None):
        super().__init__(rec_nbr, offset, rec_len, shape_type, X, Y)
        self.M = M

    def __str__(self):
        s = ''
        s += super().__str__()
        s += f', M={c.fmt_data(self.M)}'
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s, shape_type):
        """Build a class instance from a string."""
        
        # Call superclass's factory method, Alex Martelli says it will create
        # an instance of this class.
        obj = super().build(rec_nbr, offset, rec_len, s, shape_type)

        # Enrich with subclass members.
        obj.M = c.dbl_lit_end(s[20:28])

        return obj

#-------------------------------------------------------------------------------
# PointZRec
#-------------------------------------------------------------------------------

class PointZRec(PointRec):
    def __init__(self, rec_nbr, offset, rec_len, shape_type, X, Y, Z=None,
                 M=None):
        super().__init__(rec_nbr, offset, rec_len, shape_type, X, Y)
        self.Z = Z
        self.M = M

    def __str__(self):
        s = ''
        s += super().__str__()
        z = f'{c.fmt_data(self.Z)}'
        if len(z) > 0:
            s += f', Z={z}'
        m = f'{c.fmt_data(self.M)}'
        if len(m) > 0:
            s += f', M={m}'
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s, shape_type):
        """Build a class instance from a string."""
        
        # # Call superclass's factory method, Alex Martelli says it will create
        # # an instance of this class. FIXME Could I have called this 'build'
        # # instead of 'buildM', and called super().build() instead of 'build' ??
        obj = super().build(rec_nbr, offset, rec_len, s, shape_type)

        # Enrich with subclass members. 
        obj.Z = c.dbl_lit_end(s[20:28])
        obj.M = c.dbl_lit_end(s[28:36])

        return obj

#-------------------------------------------------------------------------------
# PolyMRec
#-------------------------------------------------------------------------------

class PolyMRec(PolyRec):
    """Represents both PolyLineM's and PolygonM's"""
    def __init__(self, rec_nbr, offset, rec_len, shape_type, box, num_parts,
                 num_points, parts, points, Mmin=None, Mmax=None, Marray=None):
        super().__init__(rec_nbr, offset, rec_len, shape_type)
        self.Mmin = Mmin
        self.Mmax = Mmax
        self.Marray = Marray

    def __str__(self):
        s = ''
        s += super().__str__()
        mn = f'{c.fmt_data(self.Mmin)}'
        if len(mn) > 0:
            s += f', Mmin={mn}'
        mx = f'{c.fmt_data(self.Mmax)}'
        if len(mx) > 0:
            s += f', Mmax={mx}'        
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s, shape_type):
        """Build a class instance from a string."""
        
        # # Call superclass's factory method, Alex Martelli says it will create
        # # an instance of this class.
        obj = super().build(rec_nbr, offset, rec_len, s, shape_type)

        # Enrich with subclass members. See PolyRec:build(), and the shapefile
        # specification p.8, p.13 fo the explanation of X, Y.
        X = 44 + 4*obj.num_parts
        Y = X + 16*obj.num_points
        obj.Mmin, obj.Mmax = c.dbls_lit_end(s[Y:Y+16], n=2)
        obj.Marray = c.dbls_lit_end(s[Y+16:Y+16+8*obj.num_points],
                                    n=obj.num_points)
        return obj

#-------------------------------------------------------------------------------
# PolyZRec
#-------------------------------------------------------------------------------

class PolyZRec(PolyRec):
    """Represents both PolyLineZ's and PolygonZ's"""
    def __init__(self, rec_nbr, offset, rec_len, shape_type, box, num_parts,
                 num_points, parts, points, Zmin=None, Zmax=None, Zarray=None,
                 Mmin=None, Mmax=None, Marray=None):
        super().__init__(rec_nbr, offset, rec_len, shape_type, box, num_parts,
                 num_points, parts, points)
        # Specific to subclass
        self.Zmin = Zmin
        self.Zmax = Zmax
        self.Zarray = Zarray
        self.Mmin = Mmin
        self.Mmax = Mmax
        self.Marray = Marray

    def __str__(self):
        s = ''
        s += super().__str__()
        zn = f'{c.fmt_data(self.Zmin)}'
        if len(zn) > 0:
            s += f', Zmin={zn}'
        zx = f'{c.fmt_data(self.Zmax)}'
        if len(zx) > 0:
            s += f', Zmax={zx}'        
        mn = f'{c.fmt_data(self.Mmin)}'
        if len(mn) > 0:
            s += f', Mmin={mn}'
        mx = f'{c.fmt_data(self.Mmax)}'
        if len(mx) > 0:
            s += f', Mmax={mx}'        
        return s

    @classmethod
    def build(cls, rec_nbr, offset, rec_len, s, shape_type):
        """Build a class instance from a string."""

        # Call the superclass's factory method, it will still create an
        # instance of *this* class, PolyZRec, and not PolyRec. The call to
        # cls(...) in PolyRec:build() actually calls PolyZRec's __init__
        # function, which is why Zmin, Zmax, etc, are optional. If not, we get
        # the error : "TypeError: __init__() missing 6 required positional
        # arguments: 'Zmin', 'Zmax', 'Zarray', 'Mmin', 'Mmax', and 'Marray'"

        obj = super().build(rec_nbr, offset, rec_len, s, shape_type)

        # Enrich this instance of PolyZRec (only the base class part has been
        # done so far)
        X = 44 + 4*obj.num_parts
        Y = X + 16*obj.num_points
        obj.Zmin, obj.Zmax = c.dbls_lit_end(s[Y:Y+16], n=2)
        Z = Y+16+8*obj.num_points
        obj.Zarray = c.dbls_lit_end(s[Y+16:Z], n=obj.num_points)
        obj.Mmin, obj.Mmax = c.dbls_lit_end(s[Z:Z+16], n=2)
        obj.Marray = c.dbls_lit_end(s[Z+16:Z+16+8*obj.num_points],
                                    n=obj.num_points)
        return obj

#-------------------------------------------------------------------------------
# ShapeFile - 
#-------------------------------------------------------------------------------

class ShapeFile:
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
# Building a ShapeFile from outside data
#-------------------------------------------------------------------------------

def build_record(f, offset, hdr_shape_type):
    """Offset is the current offset in the file."""
    # Record header (length is number of 16-bit words)
    s = f.read(8)
    if s == b'':
        # EOF (note the 'b' above)
        return None, offset
    rec_nbr = c.int_big_end(s[0:4])
    rec_len = 2*(c.int_big_end(s[4:8]))  # in bytes

    # Read the rest of the record
    s = f.read(rec_len)
    shape_type = ShapeType.from_int(c.int_lit_end(s[0:4]))
    if shape_type != hdr_shape_type:
        msg = f'Record has shape type {shape_type}, should be {hdr_shape_type}'
        raise(ShpParser(msg))

    # Dispatch based on shape type
    if shape_type == ShapeType.NullShape:
        rec = NullShapeRec.build(rec_nbr, offset, rec_len)
    elif shape_type == ShapeType.Point:
        rec = PointRec.build(rec_nbr, offset, rec_len, s, shape_type)
    elif shape_type == ShapeType.PointM:
        rec = PointMRec.build(rec_nbr, offset, rec_len, s, shape_type)
    elif shape_type == ShapeType.PointZ:
        rec = PointZRec.build(rec_nbr, offset, rec_len, s, shape_type)
    elif shape_type in [ShapeType.PolyLine, ShapeType.Polygon]:
        rec = PolyRec.build(rec_nbr, offset, rec_len, s, shape_type)
    elif shape_type in [ShapeType.PolyLineM, ShapeType.PolygonM]:
        rec = PolyMRec.build(rec_nbr, offset, rec_len, s, shape_type)
    elif shape_type in [ShapeType.PolyLineZ, ShapeType.PolygonZ]:
        rec = PolyZRec.build(rec_nbr, offset, rec_len, s, shape_type)
    else:
        raise NotImplementedError
    return rec, offset + 8 + rec_len

def _build(f):
    # Get the header first
    shp = _build_header(f)

    # Get the datarecords
    offset = 100  # main file header size in bytes
    while True:
        rec, offset = build_record(f, offset, shp.hdr.shape_type)
        if rec is None:
            break
        shp.recs.append(rec)
    return shp

def build(filepath):
    """Build a class instance from a file."""
    # First, load the .shp file itself
    with open(filepath, 'rb') as f:
        shp = _build(f)

    # Second, get the corresponding index file
    root, ext = os.path.splitext(filepath)
    filepath = f'{root}.shx'
    idx = build_header(filepath)

    # Check the number of records
    nbr_recs = int((idx.hdr.file_length - 100)/8)
    # FIXME derive an IndexFileHeader class from MainFileHeader, and add the
    # nbr_recs property
    if len(shp.recs) == nbr_recs:
        print(f'File has {nbr_recs} records.')
    else:
        print('Inconsistent number of records:'
              f' {len(shp.recs)} in .shp, {nbr_recs} in .shx')

    # We're done
    return shp

def _build_header(f):
    hdr = MainFileHeader.build(f.read(100))
    return ShapeFile(hdr)

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

    # with open(filepath, 'rb') as f:
    #     s = f.read()
    # print(f'File is {len(s):_} bytes long.')

    # shp = build_header(filepath)
    shp = build(filepath)
    print(shp)
