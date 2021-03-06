# dlg.py

"""DLG-3 optional format parser."""

import gzip
import os
import re
import sys
    
#-------------------------------------------------------------------------------
# Helper functions
#-------------------------------------------------------------------------------

def fortran(s):
    """Parse fortran numbers in D-scientific notation."""
    return float(s.replace('D', 'E'))

def int_blank(s):
    return None if s == ' '*len(s) else int(s)

def float_blank(s):
    return None if s == ' '*len(s) else float(s)
   
def attrs_counts(stuff):
    """Count occurrences of attributes in one kind of stuff.

    Here stuff means an array of objects that have attributes, typically
    dlg.nodes, or areas, or lines..
    """
    d = {}
    for x in stuff:
        # For all nodes, ... or all areas...
        if x.attrs is not None and len(x.attrs) > 0:
            for maj, min in x.attrs:
                # attrs is an array of (major, minor) attribute codes. Store the
                # count of occurrences of these attributes in a dictionary.
                s = f'({maj.strip()},{min.strip()})'
                if s in d:
                    d[s] += 1
                else:
                    d[s] = 1
    return d

def merge_attrs(d1, d2):
    """Merge the two dictionaries, adding the values of common keys."""
    d3 = {**d1, **d2}  # Keeps values from d2
    for k, v in d3.items():
        if k in d1 and k in d2:
            d3[k] += d1[k]
    return d3

# Iterators on line id's
def zero_stop(ids):
    """Ids before the first zero."""
    for i in ids:
        if i == 0:
            return
        yield i

def between_zeroes(ids):
    """Sequences of ids bracketed by zeroes."""
    zeroes = [i for i, e in enumerate(ids) if e == 0]
    zeroes += [len(ids)]  # Add a final zero
    z_prev = zeroes[0]
    for z in zeroes[1:]:
        yield ids[z_prev+1:z]
        z_prev = z
    
#-------------------------------------------------------------------------------
# File identification and description records
#-------------------------------------------------------------------------------

class Header1():
    def __init__(self, banner):
        self.banner = banner

    def __str__(self):
        return self.banner


    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        # print(f'[{len(s)}] s="{s}"')
        banner = s[0:72]

        return cls(banner)

class Header2():
    def __init__(self, data_cell, states, src_date, qualifier, scale, section):
        self.data_cell = data_cell
        self.states = states
        self.src_date = src_date
        self.qualifier = qualifier
        self.scale = scale
        self.section = section

    def __str__(self):
        return (f'{self.data_cell}, {self.states}, {self.src_date}'
                    + f', {self.qualifier}, {self.scale}, {self.section}')

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        # print(f'[{len(s)}] s="{s}"')
        # Name of digital cartographic unit
        m = re.search('([A-Z]+),\s+([A-Z-]+)', s[0:40])
        data_cell = states = ''
        if m:
            data_cell = m.group(1)
            states = m.group(2)

        src_date = s[41:51]  # Date of original source material
        qualifier = s[51:52]  # Date qualifier
        scale = s[52:60]  # Scale of original source material
        section = s[63:66]  # Sectional indicator (100k files)

        return cls(data_cell, states, src_date, qualifier, scale, section)

class Header3():
    def __init__(self, larg_contour_int, larg_bathy_int, small_contour_int,
                 small_bathy_int, flags, EDGEWS, EDGEWR, EDGENS, EDGENR, EDGEES,
                     EDGEER, EDGESS, EDGESR):
        self.larg_contour_int = larg_contour_int
        self.larg_bathy_int = larg_bathy_int
        self.small_contour_int = small_contour_int
        self.small_bathy_int = small_bathy_int
        self.flags = flags

        self.EDGEWS = EDGEWS
        self.EDGEWR = EDGEWR
        self.EDGENS = EDGENS
        self.EDGENR = EDGENR
        self.EDGEES = EDGEES
        self.EDGEER = EDGEER
        self.EDGESS = EDGESS
        self.EDGESR = EDGESR

    def __str__(self):
        s = ''
        s += f'{self.larg_contour_int}, {self.larg_bathy_int}'
        s += f', {self.small_contour_int}, {self.small_bathy_int}, {self.flags}'
        s += f', {self.EDGEWS}, {self.EDGEWR}, {self.EDGENS}, {self.EDGENR}'
        s += f', {self.EDGEES}, {self.EDGEER}, {self.EDGESS}, {self.EDGESR}'
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        # print(f'[{len(s)}] s="{s}"')
        larg_contour_int = s[41:45]
        larg_bathy_int = s[46:50]
        small_contour_int = s[51:55]
        small_bathy_int = s[56:60]
        flags = s[60:64].replace('\x00\x00\x00', '   ')

        EDGEWS = s[64:65]
        EDGEWR = s[65:66]
        EDGENS = s[66:67]
        EDGENR = s[67:68]
        EDGEES = s[68:69]
        EDGEER = s[69:70]
        EDGESS = s[70:71]
        EDGESR = s[71:72]

        return cls(larg_contour_int, larg_bathy_int, small_contour_int,
                   small_bathy_int, flags, EDGEWS, EDGEWR, EDGENS, EDGENR,
                       EDGEES, EDGEER, EDGESS, EDGESR)

class Header4():
    def __init__(self, dlg_level, planimetric, zone, units, resolution,
                 nb_params, accur_recs, nb_ctrl_pts, nb_categs):
        self.dlg_level = dlg_level
        self.planimetric = planimetric
        self.zone = zone
        self.units = units
        self.resolution = resolution
        self.nb_params = nb_params
        self.accur_recs = accur_recs
        self.nb_ctrl_pts = nb_ctrl_pts
        self.nb_categs = nb_categs

    def __str__(self):
        s = ''
        s += f'{self.dlg_level}, {self.planimetric}, {self.zone}, {self.units}'
        s += f', {self.resolution}, {self.nb_params}, {self.accur_recs}'
        s += f', {self.nb_ctrl_pts}, {self.nb_categs}'
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        # print(f'[{len(s)}] s="{s}"')
        dlg_level = int(s[0:6])
        planimetric = int(s[6:12])
        zone =  int(s[12:18])
        units = int(s[18:24])
        resolution = fortran(s[24:42])
        nb_params = int(s[42:48])
        accur_recs = int(s[48:54])
        nb_ctrl_pts = int(s[54:60])
        nb_categs = int(s[60:66])

        return cls(dlg_level, planimetric, zone, units, resolution, nb_params,
                   accur_recs, nb_ctrl_pts, nb_categs)

#-------------------------------------------------------------------------------
# Control point identification records
#-------------------------------------------------------------------------------

class CtrlPoint():
    def __init__(self, label, lat, long, x, y):
        self.label = label
        self.lat = lat
        self.long = long
        self.x = x  # Easting
        self.y = y  # Northing

    def __str__(self):
        return (f'{self.label}, {self.lat:.2f}, {self.long:.2f}, {self.x:.2f}'
                    + f', {self.y:.2f}')

    @classmethod
    def build(cls, s):
        """Build a class instance from a string.

        The Data Users Guide does not explain how (x,y) coordinates (in
        control point records and all of the node, area, line records)
        are related to latitude and longitude.

        Given the order, we would expect x, y to mean lat, long. The
        node and area record mentions "Number of x,y or lat-long points
        in area-coordinate list", which seems to confirm this hypothesis. 

        It turns out that the opposite is true: x is longitude, y is
        latitude. (x,y) == (long, lat).

        This can be seen by looking at the changes in the control point
        coordinates when moving east-west or north-south, see below.
"""
        label = s[0:6].rstrip()
        lat = fortran(s[6:18])
        long =  fortran(s[18:30])
        x = fortran(s[36:48])  # x is longitude
        y = fortran(s[48:60])  # y is latitude

        # Example: boston-e_MA/hydrography/444596.HY.opt.gz
        # Boston is located at:
        #
        #     Latitude	42.361145
        #     Longitude	-71.057083
        #
        # Control points in the file:
        #       lat    long       x           y
        # SW, 42.25, -71.25, 314380.82, 4679772.20
        # NW, 42.50, -71.25, 315116.59, 4707532.36
        # NE, 42.50, -71.00, 335661.31, 4707017.26
        # SE, 42.25, -71.00, 335006.86, 4679257.61
        #
        # Percentage changes:
        #                     lat     long        x        y            
        # From SW to NW    0,5917   0,0000   0,2340   0,5932
        # From NW to NE    0,0000  -0,3509   6,5197  -0,0109
        # From NE to SE   -0,5882   0,0000  -0,1950  -0,5898
        # From SE to SW    0,0000   0,3521  -6,1569   0,0110
        #
        # When moving east-west, x changes by 6% and y by 0%, so x is longitude
        # and y is latitude.
        
        return cls(label, lat, long, x, y)

#-------------------------------------------------------------------------------
# Data category identification records
#-------------------------------------------------------------------------------

class DataCategory():
    def __init__(self, name, codes, max_node, nb_nodes, node_area_links, node_line_links,
                 max_area, nb_areas, area_node_links, area_line_links, area_lists, max_lines,
                     nb_lines, line_lists):
        self.name = name
        self.codes = codes
        self.max_node = max_node
        self.nb_nodes = nb_nodes
        self.node_area_links = node_area_links
        self.node_line_links = node_line_links
        self.max_area = max_area
        self.nb_areas = nb_areas
        self.area_node_links = area_node_links
        self.area_line_links = area_line_links
        self.area_lists = area_lists
        self.max_lines = max_lines
        self.nb_lines = nb_lines
        self.line_lists = line_lists

    def __str__(self):
        s = ''
        s += f'{self.name}, {self.codes}, {self.max_node}, {self.nb_nodes}'
        s += f', {self.node_area_links}, {self.node_line_links}, {self.max_area}'
        s += f', {self.nb_areas}, {self.area_node_links}, {self.area_line_links}'
        s += f', {self.area_lists}, {self.max_lines}, {self.nb_lines}, {self.line_lists}'
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        name = s[0:20].rstrip()
        codes = int(s[20:24])
        max_node =  int(s[24:30])
        nb_nodes = int(s[30:36])
        node_area_links = s[36:37] == '1'
        node_line_links = s[38:39] == '1'
        max_area =  int(s[40:46])
        nb_areas = int(s[46:52])
        area_node_links = s[53:54] == '1'
        area_line_links = s[54:55] == '1'
        area_lists = s[55:56] == '1'
        max_lines =  int(s[56:62])
        nb_lines = int(s[62:68])
        line_lists = s[71:72] == '1'

        return cls(name, codes, max_node, nb_nodes, node_area_links, node_line_links,
                   max_area, nb_areas, area_node_links, area_line_links, area_lists, max_lines,
                       nb_lines, line_lists)

#-------------------------------------------------------------------------------
# Node and area identification records
#-------------------------------------------------------------------------------
 
class NodeOrArea():
    def __init__(self, dlg, type, id, long_, lat, nb_na_links, nb_line_links,
                 nb_points, nb_attr_pairs, nb_chars, nb_islands):
        self.dlg = dlg
        self.type = type
        self.id = id
        self.long = long_
        self.lat = lat
        self.nb_na_links = nb_na_links
        self.nb_line_links = nb_line_links
        self.nb_points = nb_points
        self.nb_attr_pairs = nb_attr_pairs
        self.nb_chars = nb_chars
        self.nb_islands = nb_islands
        self.adj_line_ids= None
        self.attrs = None  # array of (major, minor) string couples
        self.islands = None

    def __str__(self):
        s = ''
        s += f'{self.type}, {self.id}, {self.long}, {self.lat}'
        s += f', {self.nb_na_links}, {self.nb_line_links}, {self.nb_points}'
        s += f', {self.nb_attr_pairs}, {self.nb_chars}, {self.nb_islands}'

        # Node-to-line or area-to-line linkage records
        if self.adj_line_ids is not None:
            s += '\n'
            s += ', '.join([str(l) for l in self.adj_line_ids])

        # Attribute code records
        if self.attrs is not None and len(self.attrs) > 0:
            s += '\n'
            s += ', '.join([f'({maj},{min})' for maj, min in self.attrs])
        
        return s

    @classmethod
    def build(cls, dlg, s):
        """Build a class instance from a string."""
        type = s[0:1]
        id = int(s[1:6])
        long_ =  float_blank(s[6:18])
        lat = float_blank(s[18:30])
        nb_na_links = int_blank(s[30:36])
        nb_line_links = int_blank(s[36:42])

        # Number of points in area-coordinate list
        nb_points = int(s[42:48]) if type == 'A' else None

        nb_attr_pairs = int_blank(s[48:54])
        nb_chars = int_blank(s[54:60])

        # Number of islands within area
        nb_islands = int(s[60:66]) if type == 'A' else None

        return cls(dlg, type, id, long_, lat, nb_na_links, nb_line_links, nb_points,
                   nb_attr_pairs, nb_chars, nb_islands)

    # Node-to-line linkage records
    def node_line_links(self, s):
        """Parse one node-to-line linkage record.

        DLG Data Users Guide:
        FORTRAN FORMAT (12I6), for each node: The list consists of line
        internal ID numbers (which appear in bytes 2-6 of the line
        identification records) of all the lines that connect to that
        node. The lines that begin at this node are included in the list
        as positive ID numbers. The lines which terminate at this node
        are included as negative ID numbers. There is no logical order
        to the list.
        """
        pass

    # Area-to-line linkage records
    def area_line_links(self, s):
        """Parse all the area-to-line linkage record.

        DLG Data Users Guide:

        FORTRAN format (12I6), for each area: The list consists of line
        internal ID numbers (which appear in bytes 2-6 of the line
        identification records) of all lines that bound that area. and lines
        which are adjacent to an area. For those areas with islands (indicated
        by bytes 61-66 of the area's first record), the number zero, used as a
        delimiter, marking the beginning of islands. Lines with this area to the
        right are included as positive ID numbers. Lines with this area to the
        left are included as negative ID numbers. The list is ordered clockwise
        around the perimeter of the area and counterclockwise around each
        island, if any (counterclockwise around an island of an area is still a
        clockwise direction in reference to the area itself). The number zero is
        inserted in the list before each island sublist. Lines that do not
        contribute to the effective boundary of the area (those having both
        their area left and area right assigned to the same area) are not
        considered bounding lines. Therefore, these lines, while still present
        in the file, will not be referenced in the area-to-line linkage
        records.
        """
        pass

    def get_points(self, dlg):
        # FIXME make this a lazy generator, coords will be transformed 
        if self.type == 'N':
            return None
        points = []
        for l in self.adj_line_ids:
            if l == 0:
                # Don't return the island points 
                return points
            line = dlg.lines[abs(l)-1]

            # Negative line id: the list of coords must be read in reverse order
            x = line.coords if l > 0 else list(reversed(line.coords))

            # Don't duplicate the first point
            if len(points) > 0 and points[-1] == line.coords[0]:
                x = x[1:]
                
            points += x
        return points

    def inner_areas(self):
        """Toplevel inner sub-areas inside every one of this area's islands."""
        for isle in self.islands:
            for a in isle.inner_toplevel_areas():
                yield a

    def outside_areas(self):
        """Outside neighboring areas.

        Areas that neighbor outside the current area, as opposed to neighboring
        areas inside islands inside the current area.

        """
        return self.dlg.beyond(self, zero_stop(self.adj_line_ids))

    def create_islands(self):
        # Each border is a list of line_ids that delimit an island
        self.islands = [Island(self, border)
                            for border in between_zeroes(self.adj_line_ids)]

#-------------------------------------------------------------------------------
# Line identification records
#-------------------------------------------------------------------------------
 
class Line():
    def __init__(self, dlg, type, id, start_node, end_node, left_area,
                 right_area, nb_xy_pairs, nb_attr_pairs, nb_chars):
        self.dlg = dlg
        self.type = type
        self.id = id
        self.start_node = start_node
        self.end_node = end_node
        self.left_area = left_area
        self.right_area = right_area
        self.nb_xy_pairs = nb_xy_pairs
        self.nb_attr_pairs = nb_attr_pairs
        self.nb_chars = nb_chars
        self.coords= None  # list of (longitude, latitude) couples
        self.attrs = None # array of (major, minor) string couples

    def __str__(self):
        s = ''
        s += f'{self.type}, {self.id}, {self.start_node}, {self.end_node}'
        s += f', {self.left_area}, {self.right_area}, {self.nb_xy_pairs}'
        s += f', {self.nb_attr_pairs}, {self.nb_chars}'

        # Node-to-line linkage records
        if self.coords is not None:
            s += '\n'
            nlines = self.nb_xy_pairs//3
            rem = self.nb_xy_pairs%3
            for k in range(nlines):
                s += ', '.join([f'({x},{y})' for x, y in self.coords[3*k:3*(k+1)]])
            if rem > 0:
                s += ', '.join([f'({x},{y})' for x, y in self.coords[3*nlines:]])
            
        # Attribute code records
        if self.attrs is not None and len(self.attrs) > 0:
            s += '\n'
            s += ', '.join([f'({maj},{min})' for maj, min in self.attrs])
        
        return s

    @classmethod
    def build(cls, dlg, s):
        """Build a class instance from a string."""
        type = s[0:1]
        id = int(s[1:6])
        start_node =  int(s[6:12])
        end_node = int(s[12:18])
        left_area = int(s[18:24])
        right_area = int(s[24:30])

        # Number of x, y coordiante pairs listed
        nb_xy_pairs = int(s[42:48])

        nb_attr_pairs = int_blank(s[48:54])
        nb_chars = int_blank(s[54:60])

        return cls(dlg, type, id, start_node, end_node, left_area, right_area,
                   nb_xy_pairs, nb_attr_pairs, nb_chars)

#-------------------------------------------------------------------------------
# Island - 
#-------------------------------------------------------------------------------

class Island():
    """An island appears inside an area.

    It is defined by the list of lines that border the enclosing
    area. In the area's list of adjacent lines, islands are introduced
    by a zero. Each of these lines has the enclosing area on one side,
    and some other area on the other side.

    Areas inside the island may have inner neighboring areas that have
    no common border with the island's enclosing border. These areas can
    only be found by checking each area's neighbors recursively.

    Every area inside an island may have its own islands.

    A double recursion is necessary to find all the areas in an island:
      - over all the neighboring areas,
      - over all the islands
    """
    def __init__(self, outside_area, island_border):
        """Initialize a new island.

        island_border is a list of line ids
        """
        self.outside_area = outside_area
        self.island_border = island_border

        # These are just the border areas
        self.inner_border_areas = outside_area.dlg.beyond(outside_area,
                                                   self.island_border)

    def __str__(self):
        s = ''
        s += f"    Border: {', '.join([str(x) for x in self.island_border])}\n"
        s += (f"    Inner border areas: {', '.join([str(x.id) for x in self.inner_border_areas])}\n")
        s += (f"    Inner toplevel areas: {', '.join([str(x.id) for x in self.inner_toplevel_areas()])}")
        return s

    def neighbors(self, area, dont_visit, result):
        dont_visit.add(area)
        if not area in result:
            result.append(area)
        for a in area.outside_areas():
            if a in dont_visit:
                continue
            result = self.neighbors(a, dont_visit, result)
        return result
            
    def inner_toplevel_areas(self):
        # FIXME can this be turned into a generator ?
        """Get neighboring areas by moving inside into the island.

        Toplevel is in terms of containment, these areas are directly
        contained inside the enclosing area. This function returns the
        list of all such areas. What it doesn't do is look into inner
        areas' islands, if any.
        """
        result = self.inner_border_areas
        dont_visit = set([self.outside_area])
        for area in self.inner_border_areas:
            result = self.neighbors(area, dont_visit, result)
        return result

#-------------------------------------------------------------------------------
# Node - 
#-------------------------------------------------------------------------------

class Node:
    """Node in the DLG's island tree"""
    def __init__(self, area=None):
        self.area = area
        self.kids = []

    def show_node(self, level):
        indent = ' '*4
        for k in self.kids:
            print(f"{indent*level}{k.area.id}")
            k.show_node(level+1)

#-------------------------------------------------------------------------------
# DlgFile - 
#-------------------------------------------------------------------------------

class DlgFile():
    def __init__(self, hdr1, hdr2, hdr3, hdr4, proj_params, file_to_map,
                 ctrl_pts, categ):
        self.hdr1 = hdr1
        self.hdr2 = hdr2
        self.hdr3 = hdr3
        self.hdr4 = hdr4
        self.proj_params = proj_params
        self.file_to_map = file_to_map
        self.ctrl_pts = ctrl_pts
        self.categ = categ
        self.nodes = None
        self.areas = None
        self.lines = None
        # Metadata
        self.filepath = None

    #---------------------------------------------------------------------------
    # Properties
    #---------------------------------------------------------------------------
    
    @property
    def filename(self):
        return os.path.basename(self.filepath)

    @property
    def zone(self):
        return self.hdr4.zone

    @property
    def section(self):
        return self.hdr2.section

    @property
    def data_cell(self):
        return self.hdr2.data_cell

    @property
    def category(self):
        return self.categ.name
    
    #---------------------------------------------------------------------------
    # Methods
    #---------------------------------------------------------------------------

    def __str__(self):
        return f'{self.hdr2.data_cell}, {self.hdr2.states}, {self.hdr2.section}'

    def show_headers(self):
        s = ''
        # s += f'{self.hdr1}\n'
        s += f'{self.hdr2}\n'
        # s += f'{self.hdr3}\n'
        s += f'{self.hdr4}\n'

        # Projection parameters for map transformation
        # for i in range(5):
        #     s += ', '.join([f'{self.proj_params[3*i+j]:1.8f}' for j in range(3)])
        #     s += '\n'
        i = 0
        s += ', '.join([f'{self.proj_params[3*i+j]:1.8f}' for j in range(2)]) + '\n'

        # # Internal file-to-map projection transformation parameters
        # s += ', '.join([f'{x:1.8f}' for x in self.file_to_map]) + '\n'

        # Control points
        for cp in self.ctrl_pts:
            s += f'{cp}\n'

        # Data category identification records
        s += f'{self.categ}\n'

        return s
    
    def show_all(self):
        s = self.show_headers()
        # Nodes
        for x in self.nodes:
            s += f'{x}\n'
        # Areas
        for x in self.areas:
            s += f'{x}\n'
        # Lines
        for x in self.lines:
            s += f'{x}\n'
        return s

    def show_tgt_areas(self):
        # Target is of the form (min_lat, max_lat, min_long, max_long)
        tgt = self.target(0, 10, 0, 33)

        s = ''
        for x in self.areas:
            if self.inclusion((x.long, x.lat), tgt):
                s += f'{x}\n'
        return s
        
    def presences(self):
        c = self.categ
        s = ''
        s += f'Node-to-area linkage records: {c.node_area_links}\n'
        s += f'Node-to-line linkage records: {c.node_line_links}\n'
        s += f'Area-to-node linkage records: {c.area_node_links}\n'
        s += f'Area-to-line linkage records: {c.area_line_links}\n'
        s += f'Area-coordinate lists: {c.area_lists}\n'
        s += f'Line-coordinate lists: {c.line_lists}\n'
        return s

    def bounding_box(self, adj=False):
        """Determine this file's bounding box from its data.

        This box is determined by the actual data inside the file, by iterating
        over all the coordinates of points in the lines.
        """
        a = self.areas[0]
        min_lat = min_long = 99_999_999.00
        max_lat = max_long = -99_999_999.00
        for l in a.adj_line_ids:
            # Line ids count from 1, not 0
            # FIXME expose the iterable sowe can factor this code
            for long_, lat in self.lines[abs(l)-1].coords:
                if lat < min_lat:
                    min_lat = lat
                if lat > max_lat:
                    max_lat = lat
                if long_ < min_long:
                    min_long = long_
                if long_ > max_long:
                    max_long = long_

        if adj:
            # California is in zone 10, Boston in zone 19
            t = (self.hdr4.zone - 10)*500_000
            min_lat += t
            max_lat += t
            min_long += t
            max_long += t
            
        return min_lat, max_lat, min_long, max_long

    def ctrl_points_bbox(self):
        """Determine this file's bounding box from its control points.

        This box is determined by iterating over the coordinates of the 4
        control points in the file's header.
        """
        min_lat = min_long = 99_999_999.00
        max_lat = max_long = -99_999_999.00
        for cp in self.ctrl_pts:
            # cp.y = easting (~latitude)
            if cp.y < min_lat:
                min_lat = cp.y
            if cp.y > max_lat:
                max_lat = cp.y
            # cp.x = northing (~longitude)
            if cp.x < min_long:
                min_long = cp.x
            if cp.x > max_long:
                max_long = cp.x
            
        return min_lat, max_lat, min_long, max_long

    def target(self, min_lat_pc, max_lat_pc, min_long_pc, max_long_pc):
        """Args are percentage of min_lat, max_lat, etc, applied to bbox.

        I'm trying to identify an area that appears to be (by looking at
        the drawing on the screen) in the first (lowest) 10% of
        longitude and in the middle tier of latitude. So I'll be calling

            target(33, 66, 0, 10)
            
        to get a bounding box in map coordinates, and then test each
        area's representative point for inclusion.
        """
        # This quad's bounding box in map coordinates
        min_lat, max_lat, min_long, max_long = self.bounding_box()
        lat_height = max_lat - min_lat
        long_width = max_long - min_long
        
        tgt_min_lat = lat_height*min_lat_pc/100 + min_lat
        tgt_max_lat = lat_height*max_lat_pc/100 + min_lat
        
        tgt_min_long = long_width*min_long_pc/100 + min_long
        tgt_max_long = long_width*max_long_pc/100 + min_long
        
        return tgt_min_lat, tgt_max_lat, tgt_min_long, tgt_max_long

    def inclusion(self, pt, tgt):
        """pt is a 2-uple, tgt is a 4-uple.

        pt = (long, lat)
        tgt = min_lat, max_lat, min_long, max_long
        """
        return tgt[0] <= pt[1] <= tgt[1] and tgt[2] <= pt[0] <= tgt[3]

    def show_attributes(self):
        s = ''
        s += 'Nodes:\n'
        for k, v in sorted(attrs_counts(self.nodes).items()):
            s += f'  {k}\t{v}\n'
        s += 'Areas:\n'
        for k, v in sorted(attrs_counts(self.areas).items()):
            s += f'  {k}\t{v}\n'
        s += 'Lines:\n'
        for k, v in sorted(attrs_counts(self.lines).items()):
            s += f'  {k}\t{v}\n'
        return s

    def summary(self):
        """Return a set of data summarizing this DLG file."""
        return dict(
            banner=self.hdr1.banner,
            data_cell=self.hdr2.data_cell,
            states=self.hdr2.states,
            src_date=self.hdr2.src_date,
            qualifier=self.hdr2.qualifier,
            scale=self.hdr2.scale,
            section=self.hdr2.section,
            zone=self.hdr4.zone,
            ref_point=dict(
                lng=self.proj_params[0],
                lat=self.proj_params[1]
            ),
            ctrl_pts=self.ctrl_pts,
            category=self.categ.name,
            nb_nodes=self.categ.nb_nodes,
            nb_areas=self.categ.nb_areas,
            nb_lines=self.categ.nb_lines,
        )

    def beyond(self, area, border):
        """Areas that lie beyond the given border, inside/outside."""
        r = []
        for l in border:
            line = self.lines[abs(l) - 1]
            id = (line.left_area if line.left_area != area.id else
                      line.right_area)
            a = self.areas[id - 1]
            if not a in r:
                r.append(a)
        return r

    def areas_with_islands(self):
        """Areas in this DLG-3 file that have islands."""
        for area in self.areas:
            if area.nb_islands > 0:
                yield area
    
    def build_tree(self, area=None):
        """Recursively build the island tree."""
        n = Node(area)
        for isle in area.islands:
            for a in isle.inner_toplevel_areas():
                if a.nb_islands > 0:
                    # a becomes a node in the tree
                    n.kids.append(self.build_tree(a))
                else:
                    n.kids.append(Node(a))
        return n

    def island_tree(self):
        """Initiate the island tree."""
        root = Node()
        for a in self.areas_with_islands():
            root.kids.append(self.build_tree(a))
        return root

    def has_attribute(self, major, minor):
        """Occurrences of the given attribute pair (major, minor are ints)."""
        r = {}
        for x in self.nodes:
            if x.attrs is None:
                continue
            for s_maj, s_min in x.attrs:
                maj = int(s_maj)
                min = int(s_min)
                if maj == major and min == minor:
                    if 'nodes' not in r:
                        r['nodes'] = []
                    r['nodes'].append(x.id)

        for x in self.areas:
            if x.attrs is None:
                continue
            for s_maj, s_min in x.attrs:
                maj = int(s_maj)
                min = int(s_min)
                if maj == major and min == minor:
                    if 'areas' not in r:
                        r['areas'] = []
                    r['areas'].append(x.id)

        for x in self.lines:
            if x.attrs is None:
                continue
            for s_maj, s_min in x.attrs:
                maj = int(s_maj)
                min = int(s_min)
                if maj == major and min == minor:
                    if 'lines' not in r:
                        r['lines'] = []
                    r['lines'].append(x.id)
        return r

#-------------------------------------------------------------------------------
# load_links - 
#-------------------------------------------------------------------------------

def load_links(f, nb_links):
        nlines = nb_links//12
        rem = nb_links%12
        lines = []
        for k in range(nlines):
            s = f.read(80)
            lines.extend([int(s[6*i:6*(i+1)]) for i in range(12)])
        if rem > 0:
            s = f.read(80)
            lines.extend([int(s[6*i:6*(i+1)]) for i in range(rem)])
        return lines
        
#-------------------------------------------------------------------------------
# load_attributes - 
#-------------------------------------------------------------------------------

def load_attributes(f, nb_attrs):
        """Parse all the attribute code pairs records.

        As major-minor code attribute pairs, FORTRAN format (6(2I6)):
        Within each pair, the first integer is the major code and the second
        integer is the minor code. Each major and minor code is a
        one--to-four-digit integer, right justified within the six-byte field.

        Return an array of 2-uples of strings in the form (major, minor).
        """
        nlines = nb_attrs//6
        rem = nb_attrs%6
        attrs = []
        for k in range(nlines):
            s = f.read(80)
            for i in range(6):
                major = s[12*i:12*i+6]
                minor = s[12*i+6:12*i+12]
                attrs.append((major, minor))
        if rem > 0:
            s = f.read(80)
            for i in range(rem):
                major = s[12*i:12*i+6]
                minor = s[12*i+6:12*i+12]
                attrs.append((major, minor))
        return attrs
        
#-------------------------------------------------------------------------------
# load_coords - 
#-------------------------------------------------------------------------------

def load_coords(f, nb_coords):
        nlines = nb_coords//3
        rem = nb_coords%3
        coords = []
        for k in range(nlines):
            s = f.read(80)
            for i in range(3):
                x = float(s[24*i:24*i+12])
                y = float(s[24*i+12:24*i+24])
                # (x,y) is (long, lat), see control points above
                coords.append((x, y))
        if rem > 0:
            s = f.read(80)
            for i in range(rem):
                x = float(s[24*i:24*i+12])
                y = float(s[24*i+12:24*i+24])
                # (x,y) is (long, lat), see control points above
                coords.append((x, y))
        return coords
        
#-------------------------------------------------------------------------------
# load_headers - 
#-------------------------------------------------------------------------------

def _load_headers(f):
    # Headers
    hdr1 = Header1.build(f.read(80))
    hdr2 = Header2.build(f.read(80))
    hdr3 = Header3.build(f.read(80))
    hdr4 = Header4.build(f.read(80))

    # Projection parameters for map transformation (headers 5-9)
    proj_params = []
    for i in range(5):
        s = f.read(80)
        for j in range(3):
            proj_params.append(fortran(s[24*j:24*(j+1)]))

    # Internal file-to-map projection transformation parameters (header 10)
    file_to_map = []
    s = f.read(80)
    for i in range(4):
        file_to_map.append(fortran(s[18*i:18*(i+1)]))

    # Control points
    ctrl_pts =[]
    for i in range(hdr4.nb_ctrl_pts):
        ctrl_pts.append(CtrlPoint.build(f.read(80)))

    # Data category identification records
    categ = DataCategory.build(f.read(80))
       
    # Return a partial DlgFile instance with the headers
    return DlgFile(hdr1, hdr2, hdr3, hdr4, proj_params, file_to_map,
                   ctrl_pts, categ)
 
#-------------------------------------------------------------------------------
# load_data - 
#-------------------------------------------------------------------------------

def _load_data(f, filepath):
    # Get the headers first
    dlg = _load_headers(f)
    dlg.filepath = filepath

    categ = dlg.categ

    # Node records
    nodes = []
    for i in range(categ.nb_nodes):
        # Node identification record
        x = NodeOrArea.build(dlg, f.read(80))

        # Node-to-line linkage record
        if categ.node_line_links and x.nb_line_links > 0:
            x.adj_line_ids = load_links(f, x.nb_line_links)

        # Attribute code records
        if x.nb_attr_pairs > 0:
            x.attrs = load_attributes(f, x.nb_attr_pairs)

        nodes.append(x)

    # Area records
    areas = []
    for i in range(categ.nb_areas):
        # Area identification record
        x = NodeOrArea.build(dlg, f.read(80))

        # Area-to-line linkage record
        if categ.area_line_links:
            x.adj_line_ids = load_links(f, x.nb_line_links)

        # Attribute code records
        if x.nb_attr_pairs > 0:
            x.attrs = load_attributes(f, x.nb_attr_pairs)

        areas.append(x)

    # Line records
    lines = []
    for i in range(categ.nb_lines):
        # Line identification record
        x = Line.build(dlg, f.read(80))

        # Line-to-line linkage record
        if categ.line_lists:
            x.coords = load_coords(f, x.nb_xy_pairs)

        # Attribute code records
        if x.nb_attr_pairs > 0:
            x.attrs = load_attributes(f, x.nb_attr_pairs)

        lines.append(x)

    # Return the completed DlgFile instance
    dlg.nodes = nodes
    dlg.areas = areas
    dlg.lines = lines

    # Now that we have lines, we can create islands
    for a in areas:
        a.create_islands()

    return dlg

def load_headers(filepath):
    """Create python objects from just the file headers."""
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt') as f:
            return _load_headers(f)
    else:
        with open(filepath, 'r') as f:
            return _load_headers(f)

def load_data(filepath):
    """Create python objects from file."""
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt') as f:
            return _load_data(f, filepath)
    else:
        with open(filepath, 'r') as f:
            return _load_data(f, filepath)
    
#-------------------------------------------------------------------------------
# show_data - 
#-------------------------------------------------------------------------------

def show_data(filepath):
    """Break into 80-character lines."""
    with open(filepath, 'r') as f:
        while True:
            s = f.read(80)
            if s == '':
                break
            # Null characters break emacs' EOL recognition algorithm
            print(s.replace('\x00\x00\x00', '   '))

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} <filepath>')
        exit(-1)

    filepath = sys.argv[1]
    dlg = load_data(filepath)
    # print(dlg.presences())
    # print(f'Bbox: {dlg.bounding_box()}')
    # print()
    # print(dlg.show_headers())
    
    print(dlg.show_all())

    # print(dlg.show_attributes())

    # show_data(filepath)
    # print(dlg.show_tgt_areas())

    # print(dlg.has_attribute(91, 13))
