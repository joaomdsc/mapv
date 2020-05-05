# mapv/names.py

"""Parse the directory structure of the dds.cr.usgs.gov site and extract the
list of all the names of places with their states.  """

import os
import re
import json
import requests
# import geocoder
from storage import mapnames
      
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
# count_names
#-------------------------------------------------------------------------------

def count_names(states):
    cnt = 0
    for state, names in states.items():
        cnt += len(names)
    return cnt

#-------------------------------------------------------------------------------
# filesystem_names
#-------------------------------------------------------------------------------

def filesystem_names():
    """Return a 2-level hierarchy of state/place name dictionaries."""

    states = {}
    for state, name in mapnames():
        # state, name corresponds to a quadrangle, with two halves
        # (east/west). Each half represents a 30-minute area.
        if state not in states:
            states[state] = {}
        states[state][name] = True
    return states

#-------------------------------------------------------------------------------
# clean_names
#-------------------------------------------------------------------------------

def cleanup_names(names):
    """Cleanup a list of names to avoid query misses and duplicates
    when calling geocoding. WARNING: this generates duplicates."""
    cnt = 0
    for state, name in names:
        m = re.match(f"([a-z'-_.]+)_(east|west|north|south|island|mountain)",
                     name)
        if not m:
            yield(state, name)
        else:
            cnt += 1
    print(f'unclean={cnt}')
        

def clean_names():
    states = {}
    for state, name in cleanup_names(mapnames()):
        # state, name corresponds to a quadrangle, with two halves
        # (east/west). Each half represents a 30-minute area.
        if state not in states:
            states[state] = {}
        states[state][name] = True
    return states
    
#-------------------------------------------------------------------------------
# geocode_names
#-------------------------------------------------------------------------------

def geocode_names(states):
    d = {}
    with requests.Session() as session:
        for state in sorted(states.keys()):
            d[state] = {}
            for name in states[state].keys():
                # FIXME underscore in the name breaks the query
                query = f'{name}, {state}, USA'
                g = geocoder.osm(query, session=session)
                if g.ok:
                    d[state][name] = g.latlng
                    print(f'{name}, {state}: {g.latlng}.')
                else:
                    d[state][name] = True
                    print(f'{name}, {state}: not found.')
    return d

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':

    nm = filesystem_names()
    clean_nm = clean_names()
    print(f'Names: total={count_names(nm)}, clean={count_names(clean_nm)}')
