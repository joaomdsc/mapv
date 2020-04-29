# mapv/names.py

"""Parse the directory structure of the dds.cr.usgs.gov site and extract the
list of all the names of places with their states.  """

import os
import re

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
        # We can't assume foobar-w_XY follows foobar-e_XY, because foobar may
        # appear in more than one state.
        n = m.group(1)
        s = m.group(2)
        # n, s is designated as a quadrangle, with two halves (east/west). Each
        # half represents a 30-minute area.
        if s in states:
            if n not in states[s]:
                states[s][n] = True
        else:
            states[s] = {}
            states[s][n] = True

cnt = 0
for s in sorted(states.keys()):
    for n in states[s].keys():
        print(f'{s}\t{n}')
        cnt += 1

print(f'Found {len(states.keys())} states, a total of {cnt} names/places.')