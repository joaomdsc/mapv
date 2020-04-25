# dlg.py

"""DLG-3 optional format parser."""

import re
import sys
import gzip
    
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
    
#-------------------------------------------------------------------------------
# File identification and description records
#-------------------------------------------------------------------------------

class Header1():
    def __init__(self, banner):
        self.banner = banner

    def __str__(self):
        return self.banner

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
        # Name of digital cartographic unit
        m = re.search('([A-Z]+),\s+([A-Z-]+)', s[0:40])
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
        self.x = x
        self.y = y

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
    def __init__(self, type, id, lat, long, nb_na_links, nb_line_links,
                 nb_points, nb_attr_pairs, nb_chars, nb_islands):
        self.type = type
        self.id = id
        self.lat = lat
        self.long = long
        self.nb_na_links = nb_na_links
        self.nb_line_links = nb_line_links
        self.nb_points = nb_points
        self.nb_attr_pairs = nb_attr_pairs
        self.nb_chars = nb_chars
        self.nb_islands = nb_islands
        self.adj_lines= None
        self.attrs = None

    def __str__(self):
        s = ''
        s += f'{self.type}, {self.id}, {self.lat}, {self.long}'
        s += f', {self.nb_na_links}, {self.nb_line_links}, {self.nb_points}'
        s += f', {self.nb_attr_pairs}, {self.nb_chars}, {self.nb_islands}'

        # Node-to-line or area-to-line linkage records
        if self.adj_lines is not None:
            s += '\n'
            s += ', '.join([str(l) for l in self.adj_lines])
            
        # Attribute code records
        if self.attrs is not None and len(self.attrs) > 0:
            s += '\n'
            s += ', '.join([f'({maj},{min})' for maj, min in self.attrs])
        
        return s

    @classmethod
    def build(cls, s):
        """Build a class instance from a string."""
        type = s[0:1]
        id = int(s[1:6])
        lat =  float_blank(s[6:18])
        long = float_blank(s[18:30])
        nb_na_links = int_blank(s[30:36])
        nb_line_links = int_blank(s[36:42])

        # Number of points in area-coordinate list
        nb_points = int(s[42:48]) if type == 'A' else None

        nb_attr_pairs = int_blank(s[48:54])
        nb_chars = int_blank(s[54:60])

        # Number of islands within area
        nb_islands = int(s[60:66]) if type == 'A' else None

        return cls(type, id, lat, long, nb_na_links, nb_line_links, nb_points,
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

#-------------------------------------------------------------------------------
# Line identification records
#-------------------------------------------------------------------------------
 
class Line():
    def __init__(self, type, id, start_node, end_node, left_area, right_area,
                 nb_xy_pairs, nb_attr_pairs, nb_chars):
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
        self.attrs = None

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
    def build(cls, s):
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

        return cls(type, id, start_node, end_node, left_area, right_area,
                   nb_xy_pairs, nb_attr_pairs, nb_chars)

#-------------------------------------------------------------------------------
# DlgFile - 
#-------------------------------------------------------------------------------

class DlgFile():
    def __init__(self, hdr1, hdr2, hdr3, hdr4, proj_params, file_to_map,
                 ctrl_pts, categ, nodes, areas, lines):
        self.hdr1 = hdr1
        self.hdr2 = hdr2
        self.hdr3 = hdr3
        self.hdr4 = hdr4
        self.proj_params = proj_params
        self.file_to_map = file_to_map
        self.ctrl_pts = ctrl_pts
        self.categ = categ
        self.nodes = nodes
        self.areas = areas
        self.lines = lines

    def __str__(self):
        return f'{self.hdr2.data_cell}, {self.hdr2.states}, {self.hdr2.section}'
    
    def show(self):
        s = ''
        s += f'{self.hdr1}\n'
        s += f'{self.hdr2}\n'
        s += f'{self.hdr3}\n'
        s += f'{self.hdr4}\n'

        # Projection parameters for map transformation
        for i in range(5):
            s += ', '.join([f'{self.proj_params[3*i+j]:1.8f}' for j in range(3)])
            s += '\n'
            
        # Internal file-to-map projection transformation parameters
        s += ', '.join([f'{x:1.8f}' for x in self.file_to_map]) + '\n'

        # Control points
        for cp in self.ctrl_pts:
            s += f'{cp}\n'

        # Data category identification records
        s += f'{self.categ}\n'

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

    def bounding_box(self):
        """Determine this file's bounding box, in the file's internal units."""
        a = self.areas[0]
        min_lat = min_long = 99_999_999.00
        max_lat = max_long = -99_999_999.00
        for l in a.adj_lines:
            # Line ids count from 1, not 0
            for long_, lat in self.lines[abs(l-1)].coords:
                if lat < min_lat:
                    min_lat = lat
                if lat > max_lat:
                    max_lat = lat
                if long_ < min_long:
                    min_long = long_
                if long_ > max_long:
                    max_long = long_
        width = max_long - min_long
        height = max_lat - min_lat

        return min_lat, max_lat, min_long, max_long
        
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
        """
        nlines = nb_attrs//6
        rem = nb_attrs%6
        attrs = []
        for k in range(nlines):
            s = f.read(80)
            for i in range(6):
                major = int(s[12*i:12*i+6])
                minor = int(s[12*i+6:12*i+12])
                attrs.append((major, minor))
        if rem > 0:
            s = f.read(80)
            for i in range(rem):
                major = int(s[12*i:12*i+6])
                minor = int(s[12*i+6:12*i+12])
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
# load_data - 
#-------------------------------------------------------------------------------

def _load_data(f):
    # Headers
    hdr1 = Header1(f.read(80)[0:71])
    hdr2 = Header2.build(f.read(80))
    hdr3 = Header3.build(f.read(80))
    hdr4 = Header4.build(f.read(80))

    # Projection parameters for map transformation
    proj_params = []
    for i in range(5):
        s = f.read(80)
        for j in range(3):
            proj_params.append(fortran(s[24*j:24*(j+1)]))

    # Internal file-to-map projection transformation parameters
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

    # Node records
    nodes = []
    for i in range(categ.nb_nodes):
        # Node identification record
        x = NodeOrArea.build(f.read(80))

        # Node-to-line linkage record
        if categ.node_line_links and x.nb_line_links > 0:
            x.adj_lines = load_links(f, x.nb_line_links)

        # Attribute code records
        if x.nb_attr_pairs > 0:
            x.attrs = load_attributes(f, x.nb_attr_pairs)

        nodes.append(x)

    # Area records
    areas = []
    for i in range(categ.nb_areas):
        # Area identification record
        x = NodeOrArea.build(f.read(80))

        # Area-to-line linkage record
        if categ.area_line_links:
            x.adj_lines = load_links(f, x.nb_line_links)

        # Attribute code records
        if x.nb_attr_pairs > 0:
            x.attrs = load_attributes(f, x.nb_attr_pairs)

        areas.append(x)

    # Line records
    lines = []
    for i in range(categ.nb_lines):
        # Line identification record
        x = Line.build(f.read(80))

        # Line-to-line linkage record
        if categ.line_lists:
            x.coords = load_coords(f, x.nb_xy_pairs)

        # Attribute code records
        if x.nb_attr_pairs > 0:
            x.attrs = load_attributes(f, x.nb_attr_pairs)

        lines.append(x)

    # Return a DlgFile instance
    return DlgFile(hdr1, hdr2, hdr3, hdr4, proj_params, file_to_map,
                   ctrl_pts, categ, nodes, areas, lines)

def load_data(filepath):
    """Create python objects from file."""
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rt') as f:
            return _load_data(f)
    else:
        with open(filepath, 'r') as f:
            return _load_data(f)
    
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
    print(dlg.presences())
    print(f'Bbox: {dlg.bounding_box()}')
    print()
    print(dlg.show())
