# usgs.py - list of geocoded USGS map names

import json

class Usgs:
    def __init__(self):
        # FIXME json is not converting to float
        with open('usgs_geocoded_names.json', 'r') as f:
            self.obj = json.loads(f.read())

    def bbox(self):
        min_lat = min_long = 99_999_999.00
        max_lat = max_long = -99_999_999.00

        # FIXME expose the iterable sowe can factor this code
        for state, names in self.obj.items():
            for nm, (s_lat, s_lng) in names.items():
                lat = float(s_lat)
                lng = float(s_lng)
                
                if lat < min_lat:
                    min_lat = lat
                if lat > max_lat:
                    max_lat = lat
                if lng < min_long:
                    min_long = lng
                if lng > max_long:
                    max_long = lng

        return min_lat, max_lat, min_long, max_long

    def get_name_coords(self):
        """Return an array of (longitude, latitude) coordinates."""
        return [(float(lng), float(lat)) for state, names in self.obj.items()
                      for nm, (lat, lng) in names.items()]
