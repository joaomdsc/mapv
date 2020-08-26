# pbf/pbf_blobs.py - reading an OSM file (lower-level)

"""On a first level, an OSM .pbf file can be seen a series of Blob structures,
with BlobHeader and Blob, and a mechanism for extracting a payload from the
Blob. This level is described in fileformat.proto and used here.

"""
import zlib
import struct

from .fileformat_pb2 import Blob, BlobHeader

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
        blob = Blob()
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
        blob_hdr = BlobHeader()
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
# Print out level 1 
#-------------------------------------------------------------------------------

def level_1(filepath):
    g = blob_structs(filepath)

    # Header blob
    hdr_blob = next(g)
    print(f'[000] {hdr_blob.show(0)}')
    
    i = 1
    while True:
        try:
            data_blob = next(g)
        except StopIteration:
                    break
        print(f'[{i:03}] {data_blob.show(0)}')
        i += 1

# End of pbf_blobs.py
#===============================================================================
