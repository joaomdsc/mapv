# category.py

"""Run this module with the pathname of a mapname-e_STATE/layer directory to
get a list and count of the attributes present in the 4 or 16 files of data for
this layer.  """

import os
import sys
import dlg

categories = [
    'boundaries',
    'hydrography',
    'hypsography',
    'public_lands',
    'transportation',
]

#-------------------------------------------------------------------------------
# show_category - 
#-------------------------------------------------------------------------------

def category_attr_counts(dirpath):
    """Read all the files under this category (half a quad)"""
    if dirpath[-1] == '/':
        # Remove trailing slash, otherwise basename will be empty
        dirpath = dirpath[:-1]
    base = os.path.basename(dirpath)
    if base not in categories:
        print(f'Unknown category "{base}", exiting.')
        exit()

    # Dictionaries for cumulating attribute counts 
    d_nodes = {}
    d_areas = {}
    d_lines = {}

    # Iterate over files in this category (sections of the quad)
    for f in os.listdir(dirpath):
        if not f.endswith('.opt.gz'):
            continue
        print(f'Processing {f}')
        dlgf = dlg.load_data(os.path.join(dirpath, f))
        d_nodes = dlg.merge_attrs(d_nodes, dlg.attrs_counts(dlgf.nodes))
        d_areas = dlg.merge_attrs(d_areas, dlg.attrs_counts(dlgf.areas))
        d_lines = dlg.merge_attrs(d_lines, dlg.attrs_counts(dlgf.lines))

    return d_nodes, d_areas, d_lines

def show_attributes(dirpath):
    d_nodes, d_areas, d_lines = category_attr_counts(dirpath)

    s = ''
    s += 'Nodes:\n'
    for k, v in sorted(d_nodes.items()):
        s += f'  {k}\t{v}\n'
    s += 'Areas:\n'
    for k, v in sorted(d_areas.items()):
        s += f'  {k}\t{v}\n'
    s += 'Lines:\n'
    for k, v in sorted(d_lines.items()):
        s += f'  {k}\t{v}\n'
    return s

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} <dirpath>')
        exit(-1)
    dirpath = sys.argv[1]
    
    print(show_attributes(dirpath))
