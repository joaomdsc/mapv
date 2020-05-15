# mapv/draw.py - map viewer drawing code

import wx

from bitmaps import nbr_brush
from bufwin import BufferedWindow
from PIL import Image, ImageDraw, ImageFont, ImageColor
from style import get_style

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
# DrawingLayer
#-------------------------------------------------------------------------------
  
class DrawingLayer:
    def __init__(self, drawing_code, visible=False):
        self.name = name
        self.drawing_code = drawing_code
        self.visible = visible
        self.image = None

#-------------------------------------------------------------------------------
# DrawingArea
#-------------------------------------------------------------------------------
  
class DrawingArea(BufferedWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # State we need to keep around
        self.model = None  # The view needs the model to be able to draw it
        self.t = None  # Transformation is (x_win, y_win)

        self.layers = []

    def check_layer(self, i, state):
        self.layers[i-1].visible = state

    def render(self, dc):
        dc.SetBackground(wx.Brush("White"))
        dc.Clear()

        # If there are no models yet, nothing to paint
        if self.model is None:
            return

        # Define transformation form model to drawing window 
        self.t = self.get_transform(self.model.bounding_box())

        if self.model.kind == 'Usgs':
            # Models should expose iterators/generators on polygons, lines,
            # nodes, so that any model can be drawn.
            self.draw_usgs(dc, self.model)
            return

        elif self.model.kind == 'Route500':
            self.draw_shp_lines(d, self.model.dlgs[0])
            return im

        # Draw all DLGs
        for dlg in self.model.dlgs:
            self.dlg_draw(dc, dlg)

        # Special requests act on dlgs[0]
        if self.model.line is not None:
            self.draw_line(dc, self.model.dlgs[0], self.model.line, pen=wx.Pen('red'))
        if self.model.area is not None:
            self.draw_area(dc, self.model.dlgs[0], self.model.area, pen=wx.Pen('black'),
                           brush=wx.Brush('red'))
                           # brush=nbr_brush(area.id))

    def produce_bitmap(self, details):
        im = self.render()
        w, h = self.size
        bmp = wx.Bitmap.FromBufferRGBA(w, h, im.tobytes())
        return bmp

    def render(self):
        im = Image.new('RGBA', self.size)
        d = ImageDraw.Draw(im, 'RGBA')
        # Opaque white background
        d.rectangle([0, 0, self.size[0], self.size[1]], fill='white')

        # If there are no models yet, nothing to paint
        if self.model is None:
            return im

        # Define transformation form model to drawing window 
        self.t = self.get_transform(self.model.bounding_box())

        if self.model.kind == 'Usgs':
            # Models should expose iterators/generators on polygons, lines,
            # nodes, so that any model can be drawn.
            self.draw_usgs(d, self.model)
            return im

        elif self.model.kind == 'UsgsNames':
            self.draw_usgs_names(d, self.model)
            return im

        elif self.model.kind == 'Route500':
            self.draw_shp_lines(d, self.model.dlgs[0])
            return im

        # Draw all DLGs
        for dlg in self.model.dlgs:
            self.dlg_draw(d, dlg)

        # Special requests act on dlgs[0]
        if self.model.line is not None:
            self.draw_line(d, self.model.dlgs[0], self.model.line, pen='red')
        if self.model.area is not None:
            self.draw_area(d, self.model.dlgs[0], self.model.area, pen='black',
                           brush='red')
                           # brush=nbr_brush(area.id))

        # Return the prepared image
        return im

#-------------------------------------------------------------------------------
# Drawing
#-------------------------------------------------------------------------------

    def write_annotation(self, d, s):
        fn = ImageFont.truetype(r'C:\Windows\Fonts\calibri.ttf', 14)
        d.text((10, 10), s, font=fn, fill=(0, 0, 255))

    def get_transform(self, bbox):
        """Get the transformation functions from map to drawing.

        This changes on two occasions:
          - when another DLG file is added (new bbox)
          - when the window is resized (w_wx, h_wx are the window size)
          """
        # FIXME get_transform works from a model, of which I have two. Define
        # the model's API and re-factor this..
        
        # Size of drawing area
        w_wx = self.size[0]
        h_wx = self.size[1]
        # print(f'dc.GetSize: w={w_wx}, h={h_wx}')
        pad = 10
        
        # Drawable area (after padding)
        w_draw = w_wx - 2*pad
        h_draw = h_wx - 2*pad
        ratio_draw = w_draw/h_draw

        # Map proportions
        min_lat, max_lat, min_long, max_long = bbox
            
        w_map = max_long - min_long
        h_map = max_lat - min_lat
        ratio_map = w_map/h_map
            
        if ratio_draw > ratio_map:
            # Drawable area more landscapish than the map quad, fit height first
            k = h_draw/h_map
            h_win = h_draw  # Height of drawing window == height of drawable
            w_win = k*w_map  # Width of drawing window must be computed
            horiz_offset = (w_draw - w_win)/2
            orig_win = (pad + horiz_offset, pad)
        else:
            # Drawable area more portraitish than the map quad, fit width first
            k = w_draw/w_map
            w_win = w_draw  # Width of drawing window == width of drawable
            h_win = k*h_map  # Height of drawing window must be computed
            vert_offset = (h_draw - h_win)/2
            orig_win = (pad, pad + vert_offset)
    
        def x_win(long_):
            # Axis direction: longitude grows to the right
            return int(round(orig_win[0] + k*(long_ - min_long)))

        def y_win(lat):
            return int(round(orig_win[1] + k*(max_lat - lat)))

        # Return the required functions
        return x_win, y_win

    #---------------------------------------------------------------------------
    # DLG-3 with Pillow
    #---------------------------------------------------------------------------

    def dlg_draw(self, d, dlg):
        x_win, y_win = self.t
        
        # Draw areas
        for a in dlg.areas:
            self.draw_area(d, dlg, a)
        
        # Draw lines
        for line in dlg.lines:
            self.draw_line(d, dlg, line)
            
    def draw_area(self, d, dlg, area, pen=None, brush=None):
        """Paint the area's polygon, and all the areas inside its islands."""
        # pen and brush are now colors
        if dlg.categ.name == 'BOUNDARIES':
            self.draw_area_boundaries(d, dlg, area, pen, brush)
            return
        x_win, y_win = self.t

        # Draw the area's polygon with its own style 
        attr_pen = attr_brush = None
        if area.attrs is not None and len(area.attrs) > 0:
            maj, min = area.attrs[0]
            attr_pen, attr_brush = get_style(dlg.categ.name.lower(), 'areas', maj, min, id=area.id)

        # Priority: function argument, then attributes, then default
        outline_color = (pen if pen is not None else
                         attr_pen if attr_pen is not None else
                         'black')
        fill_color = (brush if brush is not None else
                      attr_brush if attr_brush is not None else
                      'white')
        
        points = [(x_win(long_), y_win(lat))
                      for long_, lat in area.get_points(dlg)]
        d.polygon(points, fill=fill_color, outline=outline_color)

        # Now draw all the areas inside the islands
        for a in area.inner_areas():
            self.draw_area(d, dlg, a)

    def draw_area_boundaries(self, d, dlg, area, pen=None, brush=None):
        """Paint the area's polygon, and all the areas inside its islands."""
        x_win, y_win = self.t

        # Draw the area's polygon with its own style 
        attr_pen = attr_brush = None
        if area.attrs is not None and len(area.attrs) > 0:
            for a in area.attrs:
                maj, min = a
                if int(maj) == 90:
                    attr_pen, attr_brush = get_style(dlg.categ.name.lower(), 'areas',
                                                     maj, min, id=area.id)
                    if attr_brush is not None:
                        # Priority: function argument, then attributes, then default
                        outline_color = (attr_pen if attr_pen is not None else 'black')

                        points = [(x_win(long_), y_win(lat))
                                      for long_, lat in area.get_points(dlg)]
                        d.polygon(points, fill=attr_brush, outline=outline_color)

                        # Now draw all the areas inside the islands
                        for a in area.inner_areas():
                            self.draw_area(d, dlg, a)

    def draw_line(self, d, dlg, line, pen=None, brush=None):
        x_win, y_win = self.t

        attr_pen = attr_brush = None
        if line.attrs is not None and len(line.attrs) > 0:
            maj, min = line.attrs[0]
            attr_pen, attr_brush = get_style(dlg.categ.name.lower(), 'lines', maj, min)
            
        # Priority: function argument, then attributes, then default
        outline_color = (pen if pen is not None else
                         attr_pen if attr_pen is not None else
                         'black')
        
        if len(line.coords) > 1:
            # Draw line segment from prev to current
            d.line([(x_win(long_), y_win(lat)) for long_, lat in line.coords],
                   fill=outline_color)

    #---------------------------------------------------------------------------
    # Shapefiles
    #---------------------------------------------------------------------------

    def draw_shp_lines(self, d, shp):
        x_win, y_win = self.t

        for rec in shp.recs:
            d.line([(x_win(x), y_win(y)) for x, y in rec.points], fill='black')
        self.write_annotation(d, f'{len(shp.recs)} lines')

    #---------------------------------------------------------------------------
    # USGS Quads
    #---------------------------------------------------------------------------

    def draw_usgs(self, d, model):
        x_win, y_win = self.t

        # Draw rectangles that hold a named place from control points
        for mapname, zone, box in model.named_rects_ctrl():
            # print(f'Ctrl: {mapname} {box}')
            min_lat, max_lat, min_long, max_long = box
            SW = x_win(min_long), y_win(min_lat)
            NW = x_win(min_long), y_win(max_lat)
            NE = x_win(max_long), y_win(max_lat)
            SE = x_win(max_long), y_win(min_lat)
            d.polygon([SW, NW, NE, SE], outline='black')

            # Box dimensions
            box_w = SE[0] - SW[0]
            box_h = SW[1] - NW[1]
            
            # Write something inside the box
            fn = ImageFont.truetype(r'C:\Windows\Fonts\calibri.ttf', 12)
            d.text((SW[0] + 5, NW[1] + 5), mapname, font=fn, fill='black')

            fn = ImageFont.truetype(r'C:\Windows\Fonts\calibri.ttf', 14)
            w, h = d.textsize(str(zone), font=fn)
            x = int(round((box_w - w)/2))
            y = int(round((box_h - h)/2))
            d.text((SW[0] + x, NW[1] + y), str(zone), font=fn, fill='black')

    def draw_usgs_names(self, d, model):
        x_win, y_win = self.t

        # Draw rectangles when they hold a named place
        x_prev = self.model.lng_min
        for x in range(self.model.lng_min + 1, self.model.lng_max):
            lat_prev = self.model.lat_min
            for y in range(10*(self.model.lat_min + 5),
                           10*(self.model.lat_max + 1), 5):
                lat = y/10
                # Paint the rectangle gray if it contains a named place
                if self.model.get_place(lat_prev, x) is not None:
                    points = [
                        (x_win(x_prev), y_win(lat_prev)),
                        (x_win(x), y_win(lat_prev)),
                        (x_win(x), y_win(lat)),
                        (x_win(x_prev), y_win(lat)),
                    ]
                    d.polygon(points, fill='#e0e0e0', outline='black')
                lat_prev = lat
            x_prev = x

        # Draw horizontal lines
        for y in range(10*self.model.lat_min, 10*(self.model.lat_max + 1), 5):
            lat = y/10
            d.line([x_win(self.model.lng_min), y_win(lat),
                             x_win(self.model.lng_max), y_win(lat)], fill='black')

        # Draw vertical lines
        for x in range(self.model.lng_min, self.model.lng_max):
            d.line([x_win(x), y_win(self.model.lat_min), 
                             # The "+ 0.5" below is actually something like a
                             # "next(self.model.lat_max)" in the iterator sense
                             x_win(x), y_win(self.model.lat_max + 0.5)],
                   fill='black')

        # Pinpoint the named places
        for lng, lat in self.model.get_name_coords():
            X = x_win(lng)
            Y = y_win(lat)
            d.ellipse([X-2, Y-2, X+2, Y+2], fill='red', outline='black')
        
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    