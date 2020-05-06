# mapv/shp/route500

import os
from shp import build_header

#-------------------------------------------------------------------------------
# I want stdout to be unbuffered, always
#-------------------------------------------------------------------------------

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout = Unbuffered(sys.stdout)

#-------------------------------------------------------------------------------
# catégories
#-------------------------------------------------------------------------------

def catégories():
    path = (r'C:\x\w\carto\ROUTE500_3-0__SHP_LAMB93_FXX_2019-10-30\ROUTE500'
            r'\1_DONNEES_LIVRAISON_2019-11-00280\R500_3-0_SHP_LAMB93_FXX-ED191')
    for f in os.listdir(path):
        categ_path = os.path.join(path, f)
        if os.path.isdir(categ_path):
            print(f'{f}')
            for f in os.listdir(categ_path):
                if not f.endswith('.shp'):
                    continue
                ss_categ = os.path.splitext(f)[0]
                print(f'    {ss_categ}')

#-------------------------------------------------------------------------------
# route_500
#-------------------------------------------------------------------------------

def route_500():
    path = (r'C:\x\w\carto\ROUTE500_3-0__SHP_LAMB93_FXX_2019-10-30\ROUTE500'
            r'\1_DONNEES_LIVRAISON_2019-11-00280\R500_3-0_SHP_LAMB93_FXX-ED191')
    for f in os.listdir(path):
        categ_path = os.path.join(path, f)
        if os.path.isdir(categ_path):
            categ = f
            for f in os.listdir(categ_path):
                if not f.endswith('.shp'):
                    continue
                ss_categ = os.path.splitext(f)[0]
                print(f'\n{categ}/{ss_categ} :')

                shp = build_header(os.path.join(categ_path, f'{ss_categ}.shp'))
                print(shp)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    catégories()
    route_500()