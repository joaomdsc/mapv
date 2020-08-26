
# FIXME move this out of the package directory

import sys
from datetime import datetime
from pbf_blobs import level_1
from osm_pbf import OsmNode, OsmWay, OsmRelation
from osm_pbf import undelta, OsmPbfFile
  
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

#-------------------------------------------------------------------------------
# level_2
#-------------------------------------------------------------------------------

def level_2(filepath):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'{dt} Before build')

    f = OsmPbfFile.build(filepath)  # Timed to 3 seconds (Haute-Savoie)

    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'{dt} after build, before show')

    print(f.show())  # Timed to less than one second

    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'{dt} After show')
    print()

    b = f.primitive_blocks[f.first_way]
    g = b.groups[1]
    w = g.primitives[0]  # First way

    print(f'Way {w.id_}, refs={w.refs}')

    # Print the nodes in the ref
    s = ''
    for n in w.refs:
        # n is a Node is, look for it
        s += f'{f.node_dict[n].show()}\n'
    print(s)

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

# testing()

filepath = 'C:/a/carto/data/download.openstreetmap.fr/extracts/europe/france' \
    '/rhone_alpes/savoie.osm.pbf'
# level_1(filepath)
level_2(filepath)

