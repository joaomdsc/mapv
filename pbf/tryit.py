import sys
from osm_pbf import testing, level_1, OsmPbfFile

# testing()

filepath = 'd:/w/download.openstreetmap.fr/extracts/europe/france/rhone_alpes/savoie.osm.pbf'
# level_1(filepath)
f = OsmPbfFile.build(filepath)
print(f.show())
print()

b = f.primitive_blocks(f.first_way)
g = b.groups[1]
w = g.primitives[0]  # First way

print(f'Way {w.id}, rels={rels}')
