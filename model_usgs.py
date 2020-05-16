# mapv/model_usgs.py - USGS coverage of continental US with 100k DLG-3

import os

from dlg import load_data
from model import Model
import storage as st

class UsgsModel(Model):
    
    def __init__(self):
        self.kind = 'Usgs'
        self.names = {}

        # Get data = file summaries
        for p in st.local_mapnames(ca_only=True):
            # Example mapname is boston-e_CA, with four sections
            mapname = os.path.basename(p)
            for mp in st.mapname_filepaths(mapname, 'hydrography'):
                # Four sections, four dlg files 
                dlg = load_data(mp)
                r = dlg.summary()
                # if not r['states'] == 'CA':
                #     continue
                if not mapname in self.names:
                    self.names[mapname] = []
                self.names[mapname].append((dlg, r))

    def bounding_box(self):
        """Return this model's bounding box in model coordinates.

        This implementation uses the control points for the bounding box of
        each section. It could use the union of both bounding boxes, data and
        ctrl points.
        """
        sect_boxes = []
        for mapname, sections in self.names.items():
            if len(sections) == 0:
                print(f'{mapname} has no sections')
                continue
            # Compute section's bounding box
            dlg, _ = sections[0]
            box = dlg.ctrl_points_bbox()
            for dlg, _ in sections[1:]:
                d_box = dlg.ctrl_points_bbox()
                box = Model.bbox_union(box, d_box)
                sect_boxes.append(box)

        # Now coalesce the array into a single box
        box = sect_boxes[0]
        for sect_box in sect_boxes[1:]:
            box = Model.bbox_union(box, sect_box)

        return box

    def named_rects(self):
        for mapname, sections in self.names.items():
            # One dlg is just one section. There are four sections to each e/w
            # half, eight sections to each named place.
            dlg, r = sections[0]
            box = dlg.bounding_box()
            for dlg, r in sections[1:]:
                d_box = dlg.bounding_box()
                box =  Model.bbox_union(box, d_box)
            yield (mapname, r['zone'], box)

    def named_rects_ctrl(self):
        for mapname, sections in self.names.items():
            # One dlg is just one section. There are four sections to each e/w
            # half, eight sections to each named place.
            dlg, r = sections[0]
            box = dlg.ctrl_points_bbox()
            for dlg, r in sections[1:]:
                d_box = dlg.ctrl_points_bbox()
                box =  Model.bbox_union(box, d_box)
            yield (mapname, r['zone'], box)

    def places(self):
        return self.names.keys()
