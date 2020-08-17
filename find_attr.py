# find_attr.py

"""Run this module with the pathname of a mapname-e_STATE/layer directory, and
a (major, minor) attribute pair, to get the occurrences of the attribute pair
in the 4 or 16 files of data for this layer.

"""

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
# find_attributes - 
#-------------------------------------------------------------------------------

def find_attributes(dirpath, major, minor):
    """Read all the files under this category (half a quad)"""
    if dirpath[-1] == '/':
        # Remove trailing slash, otherwise basename will be empty
        dirpath = dirpath[:-1]
    base = os.path.basename(dirpath)
    if base not in categories:
        print(f'Unknown category "{base}", exiting.')
        exit()

    # Iterate over files in this category (sections of the quad)
    for f in os.listdir(dirpath):
        if not f.endswith('.opt.gz'):
            continue
        print(f'Processing {f}')
        dlgf = dlg.load_data(os.path.join(dirpath, f))
        finds = dlgf.has_attribute(major, minor)

        s = ''
        for elem_type in ['nodes', 'areas', 'lines']:
            if elem_type not in finds:
                continue
            # print(f'len={len(finds[elem_type])}')
            s += f'{elem_type}\n'
            for elem_id in finds[elem_type]:
                s += f"{' '*4}{elem_id}"
        print(s)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) != 4:
        print(f'usage: {sys.argv[0]} <dirpath> <major> <minor>')
        exit(-1)
    dirpath = sys.argv[1]
    
    print(find_attributes(dirpath, int(sys.argv[2]), int(sys.argv[3])))
