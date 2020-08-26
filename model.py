# mapv/model.py - as in MVC, somewhat

class Model:
    
    def __init__(self, kind):
        self.kind = kind

    # Methods implemented by derived classes
    def open(self, filepath):
        pass

    def first_file(self):
        pass

    def open_files(self):
        pass

    @staticmethod
    def bbox_union(b1, b2):
        min_lat = b1[0] if b1[0] < b2[0] else b2[0]
        max_lat = b1[1] if b1[1] > b2[1] else b2[1]
        min_long = b1[2] if b1[2] < b2[2] else b2[2]
        max_long = b1[3] if b1[3] > b2[3] else b2[3]
        return min_lat, max_lat, min_long, max_long
