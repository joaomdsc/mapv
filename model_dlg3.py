# mapv/model_dlg3.py - as in MVC, somewhat

import os
import re
from storage import dlg_base_dir, mapname_filepaths, get_matching_filepaths
from model import Model
from dlg import load_data

#-------------------------------------------------------------------------------
# Dlg3Model
#-------------------------------------------------------------------------------

class Dlg3LocalObject:
    def __init__(self, dlg_instance, filepath, mapname, category, filename):
        self.dlg_instance = dlg_instance
        self.filepath = filepath
        self.mapname = mapname
        self.category = category
        self.filename = filename

class Dlg3Model(Model):
    
    def __init__(self):
        super().__init__('Dlg3')
        # self.kind = 'Dlg3'
        self.line = None
        self.area = None

        # The set of open files
        self.files = {}

    #---------------------------------------------------------------------------
    # Open single files, or whole categories or mapnames 
    #---------------------------------------------------------------------------

    # FIXME When the model is changed, the mapping from map coordinates to
    # screen coordinates needs to be recalculated (get_transform).

    def open(self, filepath):
        """Open a single file.

        This corresponds to a certain mapname, section, and category.
        """
        # mapname / category / filename
        filename = os.path.basename(filepath)
        m = re.match('[0-9]+.([A-Z]{2}).opt.gz', filename)
        if not m:
            return
        category = m.group(1)
        
        dir = os.path.dirname(os.path.dirname(filepath))
        mapname = os.path.basename(dir)

        # Get the actual data from the DLG-3 file
        try:
            dlg_instance = load_data(filepath)
        except ValueError:
            return
        obj = Dlg3LocalObject(dlg_instance, filepath, mapname, category,
                                    filename)
        section = obj.dlg_instance.section

        # The set of open files is organized as a dictionary of categories,
        # each category has a dictionary of mapnames, and each mapname has a
        # dictionary of (section, file) couples.
        if category not in self.files:
            d = {}
            d[mapname] = {}
            d[mapname][section] = obj
            self.files[category] = d
        else:
            d = self.files[category]
            if mapname not in d:
                d[mapname] = {}
                d[mapname][section] = obj
            else:
                # FIXME are we replacing with the same thing ?
                d[mapname][section] = obj

        print(self.get_local_mapnames())
        # Let the client know what we've loaded
        return mapname, category, filename

    def open_mapname(self, mapname):
        """Open all the files in a given mapname.
        """
        for f in mapname_filepaths(mapname):
            self.open(f)
                    
    def open_files_category(self, tgt_category):
        """Request to have this category in all the currently open files.

        The tgt_category is given as the two-letter code.

        If there are mapnames/files open that do not have this category, then
        we add it by opening the relevant files. Note that not every mapname
        has every category, we may well find that the tgt_category is absent.
        """
        print(tgt_category)
        if tgt_category in self.files:
            # Invariant: when a category exists in the data structure, all open
            # mapnames have the files for this category.
            return
        self.files[tgt_category] = {}
        for mapname in self.get_local_mapnames():
            print(mapname)
            # print(f'open_files_category: mapname={mapname}')
            self.files[tgt_category][mapname] = {}
            # Now we need to know what files are open from this mapname. It's
            # not in terms of files, it's in terms of sections: the same
            # section, F03 for example, can have files open in many category.
            
            for src_section in self.get_sections(mapname):
                # Each of these sections has a file open in some category

                # If tgt_category is 'roads and trails' (code RD), then every
                # current section is normal. Every section we find will be F0x,
                # but in getting the files, we might need to get 4 files
                # instead of just 1 if the target is RD and dense (this is
                # handled by storage.py).

                # If tgt_category is not a transportation one (RR, MT, or RD):
                #
                #   - if no section is currently open on transportation, then
                #     it's a one-for-one mapping.
                #
                #   - if there is some transportation section open, and it is
                #     dense, then the target section is bigger than the current
                #     section, and we will find 4 source sections pointing to
                #     the same target section.

                # Request the file(s) from storage module
                filepaths = get_matching_filepaths(mapname, tgt_category,
                                                   src_section)
                if filepaths is None:
                    s = f'tgt_category=={tgt_category}, mapname={mapname}'
                    s += f', no filepaths found for section {src_section}'
                    print(s)
                    continue
                
                # Get the actual data from the DLG-3 file
                for f in filepaths:
                    try:
                        dlg_instance = load_data(f)
                    except ValueError:
                        continue
                    filename = os.path.basename(f)
                    obj = Dlg3LocalObject(dlg_instance, f, mapname,
                                          tgt_category, filename)
                    self.files[tgt_category][mapname][src_section] = obj

    def clear_model(self):
        """Close all open files."""
        self.files = {}
        
    #---------------------------------------------------------------------------
    # Accessing the set of open files
    #---------------------------------------------------------------------------
                    
    def get_local_mapnames(self):
        """List of currently open mapnames."""
        names = set()
        for category in self.files.values():
            for mapname in category.keys():
                names.add(mapname)
        return list(names)
                    
    def get_sections(self, mapname):
        """List of sections from all the open files, in all categories.

        Mapname is the east/west half of a place. It is split in 4 or 16
        sections depending on density. Each section is a file.
        """
        sections = set()
        for category in self.files.values():
            for map_dict in category.values():
                sections.update(map_dict.keys())
        return list(sections)

    def get_first_file(self):
        if len(self.files.keys()) > 0:
            category = list(self.files.keys())[0]
            mapname = list(self.files[category].keys())[0]
            section = list(self.files[category][mapname].keys())[0]
            obj = self.files[category][mapname][section]
            return obj.dlg_instance

    # FIXME make a single get_files() with category argument
    def get_files_by_category(self, category):
        """Files currently open in the given category"""
        if category not in self.files:
            return
        for map_dict in self.files[category].values():
            for section, obj in map_dict.items():
                yield obj.dlg_instance

    def get_all_files(self):
        for categ in self.files.values():
            for map_dict in categ.values():
                # Dictionary of (section, file) couples
                for section, obj in map_dict.items():
                    yield obj.dlg_instance
                
    #---------------------------------------------------------------------------
    # Model's bounding box (inherited)
    #---------------------------------------------------------------------------

    def bounding_box(self):
        """Return this model's bounding box in model coordinates.

        If severaL dlg files are open, we need to compute the union of all the
        bounding boxes.
        """
        # Get a list of all DLG files
        all_files = list(self.get_all_files())
        
        if len(all_files) == 1:
            return all_files[0].bounding_box()
        elif len(all_files) > 1:
            box = all_files[0].bounding_box()
            for d in all_files[1:]:
                d_box = d.bounding_box()
                box = Model.bbox_union(box,  d_box)
            return box