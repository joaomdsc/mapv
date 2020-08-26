# mapv/model_osm.py - OpenStreetMap models

import os
from model import Model
from pbf.osm_pbf import OsmPbfFile

class Osm(Model):

    def __init__(self):
        super().__init__('Osm')
        self.files = None
        self.line = None
        self.area = None

    def open(self, filepath):
        if self.files is None:
            self.files = []
        print(f'Opening {filepath}')
        self.files.append(OsmPbfFile.build(filepath))
        print('Done.')

    @property
    def first_file(self):
        return self.files[0]

    def open_files(self):
        return self.files

    def bounding_box(self):
        """Return this model's bounding box in model coordinates."""
        return self.files[0].bbox
