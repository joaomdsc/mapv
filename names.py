# mapv/names.py

"""Parse the directory structure of the dds.cr.usgs.gov site and extract the
list of all the names of places with their states.  """

import os
import re
import json
import requests
import geocoder
      
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
# names_from_filesystem
#-------------------------------------------------------------------------------

def names_from_filesystem():
    """Return a 2-level hierarchy of state/place name dictionaries."""
    
    path = r'C:\x\data\dds.cr.usgs.gov\pub\data\DLG\100K'

    states = {}
    for f in os.listdir(path):
        if len(f) > 1:
            continue
        # Uppercase initials
        letter = os.path.join(path, f)

        for name in os.listdir(letter):
            if name == 'index.html':
                continue
            m = re.match("([a-z'-_.]+)-[ew]_([A-Z]{2})", name)
            if not m:
                print(F'Unable to parse "{name}"')
                continue
            # We can't assume foobar-w_XY follows foobar-e_XY, because foobar
            # may appear in more than one state.
            n = m.group(1)
            s = m.group(2)
            # n, s is designated as a quadrangle, with two halves
            # (east/west). Each half represents a 30-minute area.
            if s in states:
                if n not in states[s]:
                    states[s][n] = True
            else:
                states[s] = {}
                states[s][n] = True
    return states

#-------------------------------------------------------------------------------
# cleanup_names
#-------------------------------------------------------------------------------

def cleanup_names(states):
    """Cleanup the list of names to avoid query misses and duplicates."""
    d = {}
    for state in sorted(states.keys()):
        d[state] = {}
        for name in states[state].keys():
            m = re.match(f"([a-z'-_.]+)_(east|west|north|south|island)", name)
            if m:
                d[state][m.group(1)] = True
            else:
                d[state][name] = True
    return d
            
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
    with open('usgs_geocoded_names.json', 'r') as f:
        obj = json.loads(f.read())

    # print(f'Found {len(obj)} states')
    # total = 0
    # limbo = []
    # for k, v in obj.items():
    #     print(f'{k} {len(v)}')
    #     total += len(v)
        
    #     # Names in this state with unknown coordinates
    #     limbo += [(name, k) for name, coords in v.items()
    #                     if coords[0] == '0.0' and coords[1] == '0.0']

    # print(f'Found {len(limbo)} unknown locations')
    # for name in limbo:
    #     print(name)
    # print(f'Total {total} names')

    for k, v in sorted(obj.items()):
        for nm in sorted(v.keys()):
            print(f'{k}\t{nm}')