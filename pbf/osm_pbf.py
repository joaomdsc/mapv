# pbf/osm_pbf.py - reading an OSM file

"""The underlying file format is chosen to support random access at the
'fileblock' granularity. Each file-block is independently decodable and
contains a series of encoded PrimitiveGroups, with each PrimitiveGroup
containing ~8k OSM entities in the default configuration. There is no tag
hardcoding used; all keys and values are stored in full as opaque strings.

On a first level, the file can be seen a series of Blob structures, with
BlobHeader and Blob, and a mechanism for extracting a payload from the
Blob. This level is described in fileformat.proto.

On a second level, dealing with the payloads
"""
import os
import sys
import zlib
import struct
from datetime import datetime

import pbf.fileformat_pb2 as ff
import pbf.osmformat_pb2 as of
# from pbf.fileformat_pb2 import fileformat_pb2
# from pbf.osmformat_pb2 import osmformat_pb2
  
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

    def show(self, level):
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
    def __init__(self, primitives):
        # Array of OSMPrimitives, all of the same type
        self.primitives = primitives

    def show(self, level):
        return '\n'.join([p.show(level) for p in self.primitives[:10]])

    @classmethod
    def build(cls, pg):
        """pg is a protobuf PrimitiveGroup message.

        The docs say "All primitives in a group must be the same type".
        """
        if len(pg.nodes) > 0:
            # Group of Nodes
            nodes = [OsmNode(x.id, None, x.lat, x.lon) for x in pg.nodes]
            return cls(nodes)
        
        elif pg.HasField('dense') and len(pg.dense.id) > 0:
            # Group of Nodes, delta-coded
            nodes = [OsmNode(id, None, lat, lon)
                     for id, lat, lon in zip(undelta(pg.dense.id),
                                             undelta(pg.dense.lat),
                                             undelta(pg.dense.lon))]
            return cls(nodes)

        elif len(pg.ways) > 0:
            # Group of Ways
            ways = [OsmWay(x.id, None, x.refs) for x in pg.ways]
            return cls(ways)

        elif len(pg.relations) > 0:
            # Group of relations, delta-coded
            relations = []
            for rel in pg.relations:
                array = list(zip(rel.roles_sid, undelta(rel.memids), rel.types))
                relations.append(OsmRelation(rel.id, None, array))
            return cls(relations)

#-------------------------------------------------------------------------------
# OsmPbfPrimitiveBlock
#-------------------------------------------------------------------------------

class OsmPbfPrimitiveBlock:
    """This is what the docs call a file block, independently decodable."""
    def __init__(self, string_table, groups, granularity, lat_offset,
                 lon_offset, date_granularity):
        self.string_table = string_table
        self.groups = groups
        self.granularity = granularity
        self.lat_offset = lat_offset
        self.lon_offset = lon_offset
        self.date_granularity = date_granularity

    def show(self, level):
        s = ''
        s += f'{indent*level}PrimitiveBlock\n'
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
        prim_blk = of.PrimitiveBlock()
        prim_blk.ParseFromString(blob.get_data())

        # Extract the string table and factory-build instance of primitive groups
        string_table = prim_blk.stringtable.s

        groups = [OsmPbfPrimitiveGroup.build(pg)
                  for pg in prim_blk.primitivegroup]

        # FIXME optional fields
        return cls(string_table, groups, prim_blk.granularity,
                   prim_blk.lat_offset, prim_blk.lon_offset,
                   prim_blk.date_granularity)
        
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
        hdr_blk = of.HeaderBlock()
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
# OsmPbfBlob
#-------------------------------------------------------------------------------

class OsmPbfBlob:
    """Format described in fileformat.proto"""
    def __init__(self, raw, raw_size, zlib_data, lzma_data):
        self.raw = raw
        self.raw_size = raw_size
        self.zlib_data = zlib_data
        self.lzma_data = lzma_data

    def show(self, level):
        s = ''
        s += f'{indent*level}Blob'
        # Note the initial '\n' in the strings below
        if self.raw is not None:
            s += f'\n{indent*(level+1)}len(raw)={len(self.raw)}'
        if self.raw_size is not None:
            s += f'\n{indent*(level+1)}raw_size={self.raw_size}'
        if self.zlib_data is not None:
            s += f'\n{indent*(level+1)}len(zlib_data)={len(self.zlib_data)}'
        if self.lzma_data is not None:
            s += f'\n{indent*(level+1)}len(lzma_data)={len(self.lzma_data)}'
        # The returned string must never end in a newline
        return s

    @classmethod
    def build(cls, data):
        blob = ff.Blob()
        blob.ParseFromString(data)

        opt_raw = blob.raw if blob.HasField('raw') else None
        opt_raw_size = blob.raw_size if blob.HasField('raw_size') else None
        opt_zlib_data = blob.zlib_data if blob.HasField('zlib_data') else None
        opt_lzma_data = blob.lzma_data if blob.HasField('lzma_data') else None

        return cls(opt_raw, opt_raw_size, opt_zlib_data, opt_lzma_data)
 
#-------------------------------------------------------------------------------
# OsmPbfBlobHeader
#-------------------------------------------------------------------------------

class OsmPbfBlobHeader:
    """Format described in fileformat.proto"""
    def __init__(self, type_, indexdata, datasize):
        self.type_ = type_
        self.indexdata = indexdata
        self.datasize = datasize

    def show(self, level):
        s = ''
        s += f'{indent*level}BlobHeader\n'
        s += f'{indent*(level+1)}type={self.type_}'
        if self.indexdata is not None:
            # Note the initial '\n' in the string below
            s += f'\n{indent*(level+1)}len(indexdata)={len(self.indexdata)}'
        s += f'\n{indent*(level+1)}datasize={self.datasize}'
        return s

    @classmethod
    def build(cls, data):
        blob_hdr = ff.BlobHeader()
        blob_hdr.ParseFromString(data)
        
        opt_data = blob_hdr.indexdata if blob_hdr.HasField('indexdata') else None
        
        return cls(blob_hdr.type, opt_data, blob_hdr.datasize)

#-------------------------------------------------------------------------------
# OsmPbfBlobStruct
#-------------------------------------------------------------------------------

class OsmPbfBlobStruct:
    """Format described in fileformat.proto (sortof).

    A file contains a sequence of fileblock headers, each prefixed by their
    length in network byte order, followed by a data block containing the
    actual data.
    """
    def __init__(self, blob_hdr_len, blob_hdr, blob):
        self.blob_hdr_len = blob_hdr_len
        self.blob_hdr = blob_hdr
        self.blob = blob

    def get_data(self):
        return zlib.decompress(self.blob.zlib_data)

    def show(self, level):
        s = ''
        s += f'Blob structure\n'
        s += f'{indent}len(BlobHeader)={self.blob_hdr_len}\n'
        s += self.blob_hdr.show(level+1) + '\n'
        s += self.blob.show(level+1)
        return s

#-------------------------------------------------------------------------------
# blob_structs generator
#-------------------------------------------------------------------------------

def blob_structs(filepath):
    """Blob structures from an OSM .pbf file as OsmPbfBlobStruct instances.

    An OSM .pbf file is a series of blob structures. Each blob structure (or
    FileBlock) has three parts:

    - int4: length of the BlobHeader message in network byte order
    - serialized BlobHeader message
    - serialized Blob message (size is given in the header)

    Blob structures have variable length, as both the BlobHeader and the Blob
    itself have variable lenghts (Blob length is given inside the BlobHeader).

    See https://wiki.openstreetmap.org/wiki/PBF_Format

    """
    with open(filepath, 'rb') as f:
        data = f.read()

    while data != b'':
        # int4: length of the BlobHeader message in network byte order
        blob_hdr_len = int_big_end(data[:4])
        data = data[4:]

        # BlobHeader message
        blob_header = OsmPbfBlobHeader.build(data[:blob_hdr_len])
        data = data[blob_hdr_len:]

        # Parse the blob itself
        blob = OsmPbfBlob.build(data[:blob_header.datasize])
        data = data[blob_header.datasize:]

        yield OsmPbfBlobStruct(blob_hdr_len, blob_header, blob)
    
#-------------------------------------------------------------------------------
# OsmPbfFile
#-------------------------------------------------------------------------------

class OsmPbfFile:
    """Level 2: a file contains a sequence of file blocks.

    First block: HeaderBlock.
    Subsequent blocks: PrimitiveBlocks.
    """
    def __init__(self, header_block, primitive_blocks):
        self.header_block = header_block
        self.primitive_blocks = primitive_blocks

    def show(self):
        s = ''
        s += self.header_block.show(0) + '\n'
        for pg in self.primitive_blocks:
            s += pg.show(0) + '\n'
        return s
        
    @classmethod
    def build(cls, filepath):
        g = blob_structs(filepath)

        # First blob in the file is a HeaderBlock
        hdr = OsmPbfHeaderBlock.build(next(g))

        # FIXME can I do a list comprehension skipping the first element ? 
        array = []
        while True:
            # Following blocks are PrimitiveBlocks
            try:
                array.append(OsmPbfPrimitiveBlock.build(next(g)))
            except StopIteration:
                break

        return cls(hdr, array)

#-------------------------------------------------------------------------------
# Print out level 1 
#-------------------------------------------------------------------------------

def level_1(filepath):
    g = blob_structs(filepath)

    # Header blob
    hdr_blob = next(g)
    print(f'[000] {hdr_blob.show(0)}')
    
    i = 1
    while True:
        data_blob = next(g)
        print(f'[{i:03}] {data_blob.show(0)}')
        i += 1

#-------------------------------------------------------------------------------
# Testing
#-------------------------------------------------------------------------------

def testing():
    n1 = OsmNode(1, None, 23, 56)
    n2 = OsmNode(2, None, 123, 14)
    w1 = OsmWay(1, None, [1, 2])
    w2 = OsmWay(2, None, [9, 4, 7])
    w3 = OsmWay(3, None, [5, 8, 1, 54, 12])
    array = [
        ('house', 0, 'NODE'),
        ('highway', 0, 'WAY'),
        ('xxx', 0, 'RELATION'),
    ]
    r1 = OsmRelation(1, None, array)
    r2 = OsmRelation(2, None, array)
    r3 = OsmRelation(3, None, array)

    primitives = []
    primitives.append(w1)
    primitives.append(r2)
    primitives.append(n1)
    primitives.append(w2)
    primitives.append(r1)
    primitives.append(n2)
    primitives.append(w3)
    primitives.append(r3)

    for p in primitives:
        print(p.show(0))

# End of osm_pbf.py
#===============================================================================
