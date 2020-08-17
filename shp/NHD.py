import os
from shp import build_header

path = 'c:/x/w/carto/NHD_H_01090001_HU8_Shape/Shape'
for f in os.listdir(path):
    if not f.endswith('.shp'):
        continue
    shp = build_header(os.path.join(path, f))
    print(f'{f}\t{shp.hdr.shape_type}')