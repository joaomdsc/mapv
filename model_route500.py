# mapv/model.py - as in MVC, somewhat

import os
from storage import mapname_files
from model import Model
from shp.shp import build

class Route500(Model):

    def __init__(self):
        self.kind = 'Route500'
        self.dlgs = None
        self.file = None
        self.line = None
        self.area = None

    def open(self, filepath):
        if self.dlgs is None:
            self.dlgs = []
        self.dlgs.append(build(filepath))
        self.file = os.path.basename(filepath)

    def open_mapname(self, mapname):
        for f in mapname_files(mapname, 'hydrography'):
            self.open(f)

    def bounding_box(self):
        """Return this model's bounding box in model coordinates.

        If severaL dlg files are open, we need to compute the union of all the
        bounding boxes.
        """
        hdr = self.dlgs[0].hdr
        return hdr.Ymin, hdr.Ymax, hdr.Xmin, hdr.Xmax
