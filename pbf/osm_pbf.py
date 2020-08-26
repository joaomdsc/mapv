# pbf/osm_pbf.py - reading an OSM file

"""The underlying file format is chosen to support random access at the
'fileblock' granularity. Each file-block is independently decodable and
contains a series of encoded PrimitiveGroups, with each PrimitiveGroup
containing ~8k OSM entities in the default configuration. There is no tag
hardcoding used; all keys and values are stored in full as opaque strings.

On a first level, the file can be seen a series of Blob structures, see
pbf_blobs.py. The second level, implemented here, handles the OSM payloads
extracted from the blobs.

"""
import os
import sys
import zlib
import struct
from datetime import datetime

from .pbf_blobs import blob_structs
from .osmformat_pb2 import HeaderBlock, PrimitiveBlock

#-------------------------------------------------------------------------------
# Globals
#-------------------------------------------------------------------------------

# Indentation prefix
indent = ' '*4

#-------------------------------------------------------------------------------
# Helpers
#-------------------------------------------------------------------------------

def int_big_end(data):
    """Convert 4 bytes in data (big-endian) to an integer"""
    return struct.unpack(f'>i', data)[0]

#-------------------------------------------------------------------------------
# OsmInfo
#-------------------------------------------------------------------------------

class OsmInfo:
    def __init__(self, version, timestamp, changeset, uid, user_sid, visible):
        self.version = version
        self.timestamp = timestamp
        self.changeset = changeset
        self.uid = uid
        self.user_sid = user_sid
        self.visible = visible

#-------------------------------------------------------------------------------
# OsmPrimitive
#-------------------------------------------------------------------------------

class OsmPrimitive:
    def __init__(self, id_, tags):
        self.id_ = id_
        self.tags = tags

    def show(self, prim_name, level):
       s = ''
       s += f'{indent*level}{prim_name.capitalize()}: id={self.id_}'
       # FIXME do something about tags
       return s

#-------------------------------------------------------------------------------
# OsmNode
#-------------------------------------------------------------------------------

class OsmNode(OsmPrimitive):
    def __init__(self, id_, tags, lat, lon):
        super().__init__(id_, tags)
        self.lat = lat
        self.lon = lon

    def show(self, level=0):
        # Single-line print
        s = ''
        s += super().show('node', level)
        s += f', (lat,lon)={self.lat, self.lon}'
        return s

#-------------------------------------------------------------------------------
# OsmWay
#-------------------------------------------------------------------------------

class OsmWay(OsmPrimitive):
    def __init__(self, id_, tags, refs):
        super().__init__(id_, tags)
        self.refs = refs

    def show(self, level):
        # Single-line print
        s = ''
        s += super().show('way', level)
        s += f', len(refs)={len(self.refs)}'
        return s

#-------------------------------------------------------------------------------
# OsmRelation
#-------------------------------------------------------------------------------

class OsmRelation(OsmPrimitive):
    def __init__(self, id_, tags, array):
        super().__init__(id_, tags)
        self.array = array

    def show(self, level):
        # Multi-line print
        s = ''
        s += super().show('relation', level)
        s += '\n'
        
        s_array = []
        for role_sid, memid, type in self.array[:10]:
            # Each of these must be on its own line
            t = ''
            t += f'{indent*(level+1)}role={role_sid}'
            t += f', memid={memid}'
            t += f', type={type}'
            s_array.append(t)
        s += '\n'.join(s_array)
        return s

#-------------------------------------------------------------------------------
# undelta
#-------------------------------------------------------------------------------

def undelta(array):
    """Remove delta-coding from the input array, creating a new array."""
    newarr = [array[0]]
    for j, x in enumerate(array[1:]):
        newarr.append(newarr[j] + x)
    return newarr

#-------------------------------------------------------------------------------
# OsmPbfPrimitiveGroup
#-------------------------------------------------------------------------------

class OsmPbfPrimitiveGroup:
    """A PrimitiveGroup is a group of OSMPrimitives that share a string table.

    All primitives in a group must be the same type, either nodes, ways,
    relation, or changesets.
    """
    def __init__(self, elem, primitives, bbox=None):
        # Array of OSMPrimitives, all of the same type
        self.elem = elem
        self.primitives = primitives
        self.bbox = bbox

    def show(self, level):
        # Dictionary of nodes, arrays of ways and relations
        prims = list(self.primitives.values())[:10] if self.elem == 'node' \
            else self.primitives[:10]

        return '\n'.join([p.show(level) for p in prims])

    @classmethod
    def build(cls, pg):
        """pg is a protobuf PrimitiveGroup message.

        The docs say "All primitives in a group must be the same type".
        """
        if len(pg.nodes) > 0 or pg.HasField('dense') and len(pg.dense.id) > 0:
            # Group of nodes            
            if len(pg.nodes) > 0:
                # Normal
                nodes = {x.id: OsmNode(x.id, None, x.lat, x.lon) for x in pg.nodes}
            else:
                # Delta-coded
                nodes = {id: OsmNode(id, None, lat, lon)
                         for id, lat, lon in zip(undelta(pg.dense.id),
                                                 undelta(pg.dense.lat),
                                                 undelta(pg.dense.lon))}
            # Bounding box
            lat_min, lat_max, lon_min, lon_max = 9_999_999_999, \
                -9_999_999_999, 9_999_999_999, -9_999_999_999
            for n in nodes.values():
                if n.lat < lat_min:
                    lat_min = n.lat
                if n.lat > lat_max:
                    lat_max = n.lat
                if n.lon < lon_min:
                    lon_min = n.lon
                if n.lon > lon_max:
                    lon_max = n.lon
            bbox = lat_min, lat_max, lon_min, lon_max
                    
            return cls('node', nodes, bbox)

        elif len(pg.ways) > 0:
            # Group of ways
            # FIXME undelta code the refs here
            ways = [OsmWay(x.id, None, undelta(x.refs)) for x in pg.ways]
            return cls('way', ways)

        elif len(pg.relations) > 0:
            # Group of relations, delta-coded
            relations = []
            for rel in pg.relations:
                array = list(zip(rel.roles_sid, undelta(rel.memids), rel.types))
                relations.append(OsmRelation(rel.id, None, array))
            return cls('rel', relations)

#-------------------------------------------------------------------------------
# OsmPbfPrimitiveBlock
#-------------------------------------------------------------------------------

class OsmPbfPrimitiveBlock:
    """This is what the docs call a file block, independently decodable."""
    def __init__(self, string_table, groups, granularity, lat_offset,
                 lon_offset, date_granularity, elems):
        self.string_table = string_table
        self.groups = groups
        self.granularity = granularity
        self.lat_offset = lat_offset
        self.lon_offset = lon_offset
        self.date_granularity = date_granularity
        self.elems = elems

    def show(self, level):
        s = ''
        s += f'{indent*level}PrimitiveBlock {self.elems}\n'
        s += f'{indent*(level+1)}len(string_table)={len(self.string_table)}\n'
        s += f'{indent*(level+1)}PrimitiveGroups\n'

        for i, grp in enumerate(self.groups):
            # grp is a OsmPbfPrimitiveGroup instance
            s += f'{indent*(level+2)}Group {i}:\n'
            s += grp.show(level+3) + '\n'
        
        s += f'{indent*(level+1)}granularity={self.granularity}\n'
        s += f'{indent*(level+1)}lat_offset={self.lat_offset}\n'
        s += f'{indent*(level+1)}lon_offset={self.lon_offset}\n'
        s += f'{indent*(level+1)}date_granularity={self.date_granularity}'
        return s

    @classmethod
    def build(cls, blob):
        """Argument blob is an instance of OsmPbfBlobStruct where the type in the
        BlobHeader is OSMData.
        """
        has_node = has_way = has_rel = False
        
        prim_blk = PrimitiveBlock()
        prim_blk.ParseFromString(blob.get_data())

        # Extract the string table and factory-build instance of primitive groups
        string_table = prim_blk.stringtable.s

        groups = [OsmPbfPrimitiveGroup.build(pg)
                  for pg in prim_blk.primitivegroup]

        # Mark the block according to the group contents
        elems = set()
        for g in groups:
            if g.elem == 'node':
                elems.add('node')
            elif g.elem == 'way':
                elems.add('way')
            elif g.elem == 'rel':
                elems.add('rel')

        # FIXME optional fields
        return cls(string_table, groups, prim_blk.granularity,
                   prim_blk.lat_offset, prim_blk.lon_offset,
                   prim_blk.date_granularity, elems)
        
#-------------------------------------------------------------------------------
# OsmPbfHeaderBlock
#-------------------------------------------------------------------------------

class OsmPbfHeaderBlock:
    def __init__(self, bbox, required_features, optional_features,
                 writing_program, source, osmo_timestamp, osmo_seq_number,
                 osmo_base_url):
        self.bbox = bbox
        self.required_features = required_features
        self.optional_features = optional_features
        self.writing_program = writing_program
        self.source = source
        self.osmo_timestamp = osmo_timestamp
        self.osmo_seq_number = osmo_seq_number
        self.osmo_base_url = osmo_base_url

    def show(self, level):
        s = ''
        s += f'{indent*level}HeaderBlock'
        if self.bbox is not None:
            s += f'\n{indent*(level+1)}Bbox: ({self.bbx.left}, {self.bbx.right}'\
                f', {self.bbx.top}, {self.bbx.bottom})'
            
        s += f'\n{indent*(level+1)}required_features=' \
            f'{self.required_features}\n'
        s += f'{indent*(level+1)}optional_features=' \
            f'{self.optional_features}'

        if self.writing_program is not None:
            s += f'\n{indent*(level+1)}writing_program=' \
                f'{self.writing_program}'
        if self.source is not None:
            s += f'\n{indent*(level+1)}source={self.source}'

        s += f'\n{indent*(level+1)}osmosis replication:'
        if self.osmo_timestamp is not None:
            s += f'\n{indent*(level+2)}osmo_timestamp={self.osmo_timestamp}'
        if self.osmo_seq_number is not None:
            s += f'\n{indent*(level+2)}osmo_seq_number={self.osmo_seq_number}'
        if self.osmo_base_url is not None:
            s += f'\n{indent*(level+2)}osmo_base_url={self.osmo_base_url}'
        return s

    @classmethod
    def build(cls, blob):
        """Argument blob is an instance of OsmPbfBlobStruct where the type in the
        BlobHeader is OSMHeader.
        """
        hdr_blk = HeaderBlock()
        hdr_blk.ParseFromString(blob.get_data())

        if hdr_blk.HasField('bbox'):
            b = hdr_blk.bbox
            opt_bbox = (b.left, b.right, b.top, b.bottom)
        else:
            opt_bbox = None

        opt_writing_program = hdr_blk.writingprogram \
            if hdr_blk.HasField('writingprogram') else None
        opt_source = hdr_blk.source \
            if hdr_blk.HasField('source') else None
        opt_osmo_timestamp = hdr_blk.osmosis_replication_timestamp \
            if hdr_blk.HasField('osmosis_replication_timestamp') else None
        opt_osmo_seq_number = hdr_blk.osmosis_replication_sequence_number \
            if hdr_blk.HasField('osmosis_replication_sequence_number') else None
        opt_osmo_base_url = hdr_blk.osmosis_replication_base_url \
            if hdr_blk.HasField('osmosis_replication_base_url') else None

        return cls(opt_bbox, hdr_blk.required_features,
               hdr_blk.optional_features, opt_writing_program, opt_source,
               opt_osmo_timestamp, opt_osmo_seq_number, opt_osmo_base_url)
     
#-------------------------------------------------------------------------------
# OsmPbfFile
#-------------------------------------------------------------------------------

class OsmPbfFile:
    """Level 2: a file contains a sequence of file blocks.

    First block: HeaderBlock.
    Subsequent blocks: PrimitiveBlocks.

    This implementation mirrors the structure of the .pbf file. As such, it is
    a good starting point to learn about the file contents, but it may not be
    the best solution for subsequently using the data. Directly accessing
    arrays of nodes, ways, relations could be better, we start by implementing
    generators for those.

    """
    def __init__(self, header_block, primitive_blocks, first_way, first_rel,
                 node_dict):
        self.header_block = header_block
        self.primitive_blocks = primitive_blocks
        self.first_way = first_way
        self.first_rel = first_rel
        self.node_dict = node_dict

    def show(self):
        s = ''
        s += f'Total {len(self.primitive_blocks)} file-blocks' + \
          f', first way={self.first_way}, first rel={self.first_rel}\n'
        s += self.header_block.show(0) + '\n'
        for i, pg in enumerate(self.primitive_blocks):
            s += f'{i:03} ' + pg.show(0) + '\n'
        return s

    @classmethod
    def build(cls, filepath):
        g = blob_structs(filepath)

        # First blob in the file is a HeaderBlock
        hdr = OsmPbfHeaderBlock.build(next(g))

        # FIXME can I do a list comprehension skipping the first element ? 
        array = []
        d = {}
        while True:
            # Following blocks are PrimitiveBlocks
            try:
                b = OsmPbfPrimitiveBlock.build(next(g))
            except StopIteration:
                break

            # Accumulate node dictionaries
            if 'node' in b.elems:
                grp = b.groups[0]
                # g.primitives is a dictionary of nodes
                d.update(grp.primitives)
            
            # Save the indexes of the first blocks with ways and relations
            if 'node' in b.elems and 'way' in b.elems:
                first_way = len(array)
            if 'way' in b.elems and 'rel' in b.elems:
                first_rel = len(array)

            array.append(b)

        return cls(hdr, array, first_way, first_rel, d)

    @staticmethod
    def bbox_union(b1, b2):
        min_lat = b1[0] if b1[0] < b2[0] else b2[0]
        max_lat = b1[1] if b1[1] > b2[1] else b2[1]
        min_long = b1[2] if b1[2] < b2[2] else b2[2]
        max_long = b1[3] if b1[3] > b2[3] else b2[3]
        return min_lat, max_lat, min_long, max_long

    @property
    def bbox(self):
        """Bounding box of this file's nodes."""
        # FIXME should be the bounding box of the ways
        # Initialize min,max bbox
        bbox0 = 9_999_999_999, -9_999_999_999, 9_999_999_999, -9_999_999_999
        for b in self.primitive_blocks:
            for g in b.groups:
                if g.elem == 'node':
                    bbox0 = OsmPbfFile.bbox_union(bbox0, g.bbox)
        return bbox0

    @property
    def ways(self):
        arr = []
        
        # First block is special
        g = self.primitive_blocks[self.first_way].groups[1]
        arr.extend(g.primitives)

        for b in self.primitive_blocks[self.first_way+1:self.first_rel]:
            arr.extend(b.groups[0].primitives)

        # FIXME what a drawing model needs is an array of points, maybe this
        # could simply generate an array of (lon, lat)
        return arr

# End of osm_pbf.py
#===============================================================================
