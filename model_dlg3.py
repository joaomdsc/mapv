# mapv/model.py - as in MVC, somewhat

import os
from storage import mapname_files
from model import Model
from dlg import load_data

class Dlg3Model(Model):
    
    def __init__(self):
        self.kind = 'Dlg3'
        self.dlgs = None
        self.file = None
        self.line = None
        self.area = None

    def open(self, filepath):
        if self.dlgs is None:
            self.dlgs = []
        self.dlgs.append(load_data(filepath))
        self.file = os.path.basename(filepath)

    def open_mapname(self, mapname):
        for f in mapname_files(mapname, 'hydrography'):
            self.open(f)

    def bounding_box(self):
        """Return this model's bounding box in model coordinates.

        If severaL dlg files are open, we need to compute the union of all the
        bounding boxes.
        """
        if len(self.dlgs) == 1:
            return self.dlgs[0].bounding_box()
        else:
            box = self.dlgs[0].bounding_box()
            for d in self.dlgs[1:]:
                d_box = d.bounding_box()
                box = Model.bbox_union(box, d_box)
            return box