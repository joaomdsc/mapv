# usgs.py - list of geocoded USGS map names

import json
      
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
# Usgs
#-------------------------------------------------------------------------------

class Usgs:
    # Conversion formulas
    def lat2idx(self, lat):
        return int(2*(lat - self.lat_min))

    def idx2lat(self, idx):
        return idx/2 + self.lat_min

    def lng2idx(self, lng):
        return lng - self.lng_min
    
    # usgs_geocoded_names.json      - only conterminous U.S.
    # usgs_geocoded_names_all.json  - all the named places
    def __init__(self):

        # self.obj is a dictionary with key = state, and value a dictionary of
        # names with an associate tuple (long., lat.)
        
        # FIXME json is not converting to float
        with open('usgs_geocoded_names.json', 'r') as f:
            self.obj = json.loads(f.read())

        # Bounding box of the U.S.A. in degrees
        self.lat_min = 25
        self.lat_max = 50
        self.lng_min = -124
        self.lng_max = -64
        
        # Conterminous U.S. coordinates vary between 25 and 50 latitude and
        # between -124 and -64 longitude
        self.lat_height = self.lat_max - self.lat_min + 1
        self.lng_width = self.lng_max - self.lng_min + 1

        # Create a second structure organized by coordinates 
        self.coords = self.by_coords()        
        
    def by_coords(self):
        # Initialize array with lat_height rows and lng_width columns
        coords = [[None for lng in range(self.lng_width)]
                      for lat in range(2*self.lat_height)]

        total = 0
        for state, names in self.obj.items():
            for nm, (s_lat, s_lng) in names.items():
                # Quads are a full degree wide (longitude) but only half a
                # degree tall (latitude).

                # Latitude
                y = float(s_lat)
                lat = round(y)
                if (lat - y) > 0:
                    lat -= 0.5

                # Longitude
                lng = int(round(float(s_lng)))
                
                total += 1
                try:
                    coords[self.lat2idx(lat)][self.lng2idx(lng)] = \
                      (nm, state, (s_lat, s_lng), (lat, lng))
                except IndexError:
                    s = ''
                    s += f'Oops: {nm},  {state}, (lat,lng): '
                    s += f'orig=({s_lat},{s_lng}), int=({lat},{lng})'
                    print(s)
        return coords

    def get_place(self, lat, lng):
        try:
            return self.coords[self.lat2idx(lat)][self.lng2idx(lng)]
        except KeyError:
            return None

    def get_lng_data(self, lng):
        """Get all the data from a single longitude."""
        return [(self.idx2lat(i), self.coords[i][self.lng2idx(lng)])
            for i in reversed(range(2*self.lat_height))]

    def bbox(self):
        min_lat = min_long = 99_999_999.00
        max_lat = max_long = -99_999_999.00

        # FIXME expose the iterable so we can factor this code
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

    def bbox_int(self):
        min_lat, max_lat, min_long, max_long = self.bbox()
        return (int(round(min_lat)), int(round(max_lat)) + 1,
                    int(round(min_long)) - 1, int(round(max_long)))
        
    def get_name_coords(self):
        """Return an array of (longitude, latitude) coordinates."""
        return [(float(lng), float(lat)) for state, names in self.obj.items()
                      for nm, (lat, lng) in names.items()]

    def histogram(self):
        min_lat, max_lat, min_long, max_long = self.bbox_int()
        lat_height = max_lat - min_lat + 1
        long_width = max_long - min_long + 1

        histo_lat = [0]*lat_height
        histo_long = [0]*long_width
        
        for state, names in self.obj.items():
            for nm, (s_lat, s_lng) in names.items():
                lat = round(float(s_lat))
                lng = round(float(s_lng))
                if lat == 0 and lng == 0:
                    continue

                histo_lat[lat] += 1
                histo_long[lng] += 1
        return histo_lat, histo_long

    def conterminous_only(self):
        """Write JSON file with only conterminous US places."""
        states = {}
        for state, names in self.obj.items():
            for nm, (s_lat, s_lng) in names.items():
                lat = float(s_lat)
                lng = float(s_lng)

                # Conterminous U.S. takes up 26 different latitudes and 61
                # different longitudes.
                if 25 <= lat <= 50 and -124 <= lng <= -64:
                    # Include this named geocoded place in target dict
                    if not state in states:
                        states[state] = {}
                    states[state][nm] = (s_lat, s_lng)

        with open('usgs_geocoded_names_cont.json', 'w') as f:
            f.write(json.dumps(states, indent=4))

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <longitude>')
        exit(-1)
    lng = int(sys.argv[1])
    
    u = Usgs()
    # print(f'Bbox int (lat, long)={u.bbox_int()}')
    
    # histo_lat, histo_long = u.histogram()

    # print('Latitude')
    # for i, lat in enumerate(histo_lat):
    #     print(f'{i:>3} {lat}')

    # print('Longitude')
    # for i, lng in enumerate(histo_long):
    #     print(f'{i-161:>3} {lng}')

    # u.conterminous_only()

    def show_col(lng):
        col = u.get_lng_data(lng)
        for x in col:
            print(x)

    show_col(lng)

    # The json file has 1766 entries, the grid has 52x61 = 3172 cells