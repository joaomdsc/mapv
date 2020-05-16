# mapv/model_dlg3.py - as in MVC, somewhat

import os
from storage import dlg_base_dir, mapname_filepaths
from model import Model
from dlg import load_data

class Dlg3LocalObject:
    def __init__(self, dlg_instance, filepath, mapname, category, filename):
        self.dlg_instance = dlg_instance
        self.filepath = filepath
        self.mapname = mapname
        self.category = category
        self.filename = filename

class Dlg3Model(Model):
    
    def __init__(self):
        self.kind = 'Dlg3'
        self.line = None
        self.area = None

        # The set of open files
        self.files = {}

    #---------------------------------------------------------------------------
    # Open single files, or whole categories or mapnames 
    #---------------------------------------------------------------------------

    def open(self, filepath):
        # mapname / category / filename
        filename = os.path.basename(filepath)
        dir = os.path.dirname(filepath)
        category = os.path.basename(dir)
        dir = os.path.dirname(dir)
        mapname = os.path.basename(dir)
        # Show thos in the UI
        # print(f'Opening {mapname} / {category} / {filename}')

        # Get the actual data from the DLG-3 file
        try:
            dlg_instance = load_data(filepath)
        except ValueError:
            return
        obj = Dlg3LocalObject(dlg_instance, filepath, mapname, category,
                                    filename)

        # The set of open files is organized as a dictionary of categories,
        # each category has a dictionary of mapnames, with an array of files
        if category not in self.files:
            self.files[category] = {}
            self.files[category][mapname] = [obj]
        else:
            if mapname not in self.files[category]:
                self.files[category][mapname] = [obj]
            else:
                self.files[category][mapname].append(obj)

        # Let the client know what we've loaded
        return category

    def open_mapname(self, mapname):
        """Request to open all the files in a given mapname."""
        for f in mapname_filepaths(mapname, 'hydrography'):
            self.open(f)
                    
    def open_category(self, category):
        """Request to have all the files open in a given category.

        This method only adds new files in already open mapnames, it does not
        retrieve new mapnames. It does not reopen files that are already open.
        """
        for mapname in self.get_mapnames():
            if category in self.files:
                local_filenames = [obj.filename
                                   for obj in self.files[category][mapname]]
            else:
                local_filenames = []
            # This is a mapname that I have, I want to get all the other files
            # in this mapname and category pair.
            for filepath in mapname_filepaths(mapname, category):
                filename = os.path.basename(filepath)
                if not filename in local_filenames:
                    self.open(filepath)

    #---------------------------------------------------------------------------
    # Accessing the set of open files
    #---------------------------------------------------------------------------
                    
    def get_mapnames(self):
        """List of currently open mapnames."""
        names = set()
        for category in self.files.values():
            for mapname in category.keys():
                names.add(mapname)
        return list(names)

    def get_first_file(self):
        if len(self.files.keys()) > 0:
            category = list(self.files.keys())[0]
            mapname = list(self.files[category].keys())[0]
            obj = self.files[category][mapname][0]
            return obj.dlg_instance

    def get_files_by_category(self, category):
        """Files currently open in the given category"""
        if category not in self.files:
            return
        for mapname in self.files[category].values():
            for obj in mapname:
                yield obj.dlg_instance

    def get_all_files(self):
        for categ_dict in self.files.values():
            for file_array in categ_dict.values():
                # Array of file objects
                for obj in file_array:
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