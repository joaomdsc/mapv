# concat.py -

"""Concatenate all the individual attributes pages into a single csv file.

Each individual file (73.txt to 92.txt) corresponds to a page in the DLG-3 data
users guide. The columns in the files have been manually aligned, so this
script can parse the files based on fixed positions.
"""

import os
import re

def handle_file(f):
    lines = f.readlines()
    for l in lines[2:]:
        l2 = l.strip()
        if l2 == '':
            continue
        data_category = l[0:29].strip()
        type_of_code = l[29:52].strip()
        application = l[52:70].strip()
        old_major = l[70:71].strip()
        major = l[71:76].strip()
        old_minor = l[76:77].strip()
        minor = l[77:83].strip()
        description = l[83:].strip()

        s = ''
        s += f'{data_category}\t{type_of_code}\t{application}\t{old_major}'
        s += f'\t{major}\t{old_minor}\t{minor}\t{description}'
        print(s)

hdr = 'Data category\tType of code\tApplication\tOld\tMajor\tOld\tMinor\tDescription'
print(hdr)

for f in os.listdir('.'):
    m = re.match('[0-9]{2}.txt', f)
    if not m:
        continue
    with open(f, 'r') as g:
        handle_file(g)