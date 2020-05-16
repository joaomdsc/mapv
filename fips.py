"""
State FIPS codes from:
https://www.nrcs.usda.gov/wps/portal/nrcs/detail/?cid=nrcs143_013696

County FIPS codes from:
https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697
"""
import json

from lxml import etree, html
      
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

def states():
    states = {}
    with open('fips_states.txt', 'r') as f:
        for line in f.readlines():
            line = line.rstrip()
            fields = line.split('\t')
            states[fields[2]] = (fields[1], fields[0])

    with open('fips_states.json', 'w') as f:
        f.write(json.dumps(states, indent=4))
    return states

def st_name_by_alpha(d_states, st_alpha_code):
    for k, v in d_states.items():
        if v[0] == st_alpha_code:
            return v[1]

def counties(d_states):
    root = html.parse('fips_county.html')
    with open('fips_counties.txt', 'w') as f, open('fips_counties.json', 'w') as g:
        states_counties = {}
        for tr in root.findall('.//tr'):
            (c_code, county, st_code) = [td.text for td in tr]
            # print(c_code, county, st_code)
            
            # Text file
            f.write(f'{c_code}\t{county}\t{st_code}\n')
            
            # Dictionary for JSON file
            state = int(c_code[0:2])
            county_code = int(c_code[2:5])
            if state not in states_counties:
                # Each state is a 2-array (st_code, dict_of_counties)
                states_counties[state] = [st_code, st_name_by_alpha(d_states, st_code), {}]
            states_counties[state][2][county_code] = county
        g.write(json.dumps(states_counties, indent=4))

d_states = states()
counties(d_states)
