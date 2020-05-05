# mapv/places.py

"""Given a place name and state, print out the headers of all the DLG-3 files
that make up both halves of the quadrangle.  """

import os
import sys
import dlg

#-------------------------------------------------------------------------------
# show_headers - 
#-------------------------------------------------------------------------------

def show_headers(name, state):
    path = r'C:\x\data\dds.cr.usgs.gov\pub\data\DLG\100K'
    path = os.path.join(path, name[0].upper())

    for half in 'ew':
        mapname = f'{name}-{half}_{state}'
        map_path = os.path.join(path, mapname)
        if not os.path.isdir(map_path):
            print(f"Can't find '{mapname}'")
        else:
            layer_path = os.path.join(map_path, 'hydrography')
            for f in os.listdir(layer_path):
                if f.endswith('.opt.gz'):
                    filepath = os.path.join(layer_path, f)
                    d = dlg.load_data(filepath)
                    print(d.show_headers())
            
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    # Check cmd line args
    if len(sys.argv) != 3:
        print(f'usage: {sys.argv[0]} <place> <state>')
        exit(-1)
    name = sys.argv[1]
    state = sys.argv[2]
    
    show_headers(name, state)
