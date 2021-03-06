# mapv/model_shp.py - shapefile models

import os
from storage import mapname_filepaths
from model import Model
from shp.shp import build

class Shapefile(Model):

    def __init__(self):
        super().__init__('Shapefile')
        # self.kind = 'Shapefile'
        self.files = None
        self.line = None
        self.area = None

    def open(self, filepath):
        if self.files is None:
            self.files = []
        self.files.append(build(filepath))

    @property
    def first_file(self):
        return self.files[0]

    def open_files(self):
        return self.files

    def open_mapname(self, mapname):
        for f in mapname_filepaths(mapname, 'hydrography'):
            self.open(f)

    def bounding_box(self):
        """Return this model's bounding box in model coordinates."""
        hdr = self.files[0].hdr
        return hdr.Ymin, hdr.Ymax, hdr.Xmin, hdr.Xmax
