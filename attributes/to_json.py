# to_json.py -

import os
import json

with open('attrs_modified.txt', 'r') as f:
    lines = f.readlines()

cnt_entries = 0
attributes = {}
categ_name = code_type = app = major = None
for l in lines[1:]:
    l = l.rstrip('\r\n')
    l2 = l.strip()
    if l2 == '':
        continue
    fields = l.split('\t')
    if len(fields) != 8:
        print(f'len={len(fields)}, l="{l}"')
        exit()
    if fields[0] not in ['', categ_name]:
        if categ_name != None:
            # There's a previous category (and code type, app, major) to finish
            app_dict[major] = major_dict
            code_type_dict[app] = app_dict
            categ_dict[code_type] = code_type_dict
            attributes[categ_name] = categ_dict
        # New category
        categ_name = fields[0]
        categ_dict = {}
        code_type = fields[1]
        code_type_dict = {}
        app = fields[2]
        app_dict = {}
        major = fields[4]
        major_dict = {}
    if fields[1] not in ['', code_type]:
        if code_type != None:
            # There's a previous code type (and app, major) to finish
            app_dict[major] = major_dict
            code_type_dict[app] = app_dict
            categ_dict[code_type] = code_type_dict
        # New type of code
        code_type = fields[1]
        code_type_dict = {}
        app = fields[2]
        app_dict = {}
        major = fields[4]
        major_dict = {}
    if fields[2] not in ['', app]:
        if app != None:
            # There's a previous application (and major) to finish
            app_dict[major] = major_dict
            code_type_dict[app] = app_dict
        # New application
        app = fields[2]
        app_dict = {}
        major = fields[4]
        major_dict = {}
    if fields[4] not in  ['', major]:
        if major != None:
            # There's a previous major to finish
            app_dict[major] = major_dict
        # New major code
        major = fields[4]
        major_dict = {}
    # Each triplet (categ, code type, app) can have entries
    minor = fields[6]
    description = fields[7]
    major_dict[minor] = description
    cnt_entries += 1
    
# There's everything previous to finish
app_dict[major] = major_dict
code_type_dict[app] = app_dict
categ_dict[code_type] = code_type_dict
attributes[categ_name] = categ_dict

with open('attributes.json', 'w') as f:
    f.write(json.dumps(attributes, indent=4))

print(f'Entries in the file: {len(lines) - 1}')
print(f'Entries in json: {cnt_entries}')