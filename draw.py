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
    def __init__(self, code):
        self.code = code
        self.visible = False
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

        self.layers = [
            DrawingLayer('HY'),
            DrawingLayer('BO'),
            DrawingLayer('HP'),
            DrawingLayer('PL'),
            DrawingLayer('RR'),
            DrawingLayer('MT'),
            DrawingLayer('RD'),
        ]

    def clear(self):
        self.model = None
        for layer in self.layers:
            layer.visible = False
            layer.image = None

    def check_layer(self, code, state):
        """User has checked/unchecked the 'code' layer box."""
        for layer in self.layers:
            if layer.code == code:
                layer.visible = state
                return

    def render_bitmap(self, layering=False):
        """Recreate the bitmap to be displayed.

        When render_bitmap is called, the contents of all the layer bitmaps
        normally need to be redrawn, because either the model data has changed,
        or the window size has changed; one exception to this rule is when the
        visibility of some layer has been toggled, which requires only the
        compositing to be redone. We check for for this exception so we can
        avoid the redrawing overhead.
        """
        w, h = self.size
        if self.model is None:
            im = self.render_layer_zero()
            return wx.Bitmap.FromBufferRGBA(w, h, im.tobytes())
        elif self.model.kind != 'Dlg3':
            im = self.render()
            return wx.Bitmap.FromBufferRGBA(w, h, im.tobytes())
        
        im = self.render_layer_zero()
        for layer in self.layers:
            if layer.visible:
                if layer.image is None:
                    # The user checked some layername's box for the first time,
                    # we need to get that layer's data and draw it.
                    self.model.open_files_category(layer.code)
                    layer.image = self.render_dlg_layer(layer.code)

                elif not layering:
                    # We're not just toggling layer visibility, the model or
                    # window size have actually changed, so the bitmap needs ot
                    # be redrawn.

                    # We could distinguish redrawing on the same size (keep im
                    # and d objects) and changing sizes (im and d need to be
                    # recreated), not sure if it's worth it.
                    layer.image = self.render_dlg_layer(layer.code)
                im = Image.alpha_composite(im, layer.image)
        
        return wx.Bitmap.FromBufferRGBA(w, h, im.tobytes())

    def render_layer_zero(self):
        im = Image.new('RGBA', self.size)
        d = ImageDraw.Draw(im, 'RGBA')
        # Opaque white background
        d.rectangle([0, 0, self.size[0], self.size[1]], fill='white')
        return im

    def render_dlg_layer(self, category):
        print(f'render_dlg_layer, code={category}')
        im = Image.new('RGBA', self.size)
        d = ImageDraw.Draw(im, 'RGBA')

        # Define transformation form model to drawing window
        # FIXME this doesn't need to be done all the time
        bbox = self.model.bounding_box()
        self.t = self.get_transform(bbox)

        # Draw a single layer/category
        for dlg in self.model.get_files_by_category(category):
            print(dlg)
            self.dlg_draw(d, dlg)

        # Special requests act on the first file
        if self.model.line is not None:
            self.draw_line(d, self.model.get_first_file(), self.model.line,
                           pen='red')
        if self.model.area is not None:
            self.draw_area(d, self.model.get_first_file(), self.model.area,
                           pen='black',
                           brush='red')
                           # brush=nbr_brush(area.id))
        return im

    def render(self):
        im = Image.new('RGBA', self.size)
        d = ImageDraw.Draw(im, 'RGBA')
        # Opaque white background
        d.rectangle([0, 0, self.size[0], self.size[1]], fill='white')

        # Define transformation from model to drawing window 
        self.t = self.get_transform(self.model.bounding_box())

        # Models should expose iterators/generators on polygons, lines, nodes,
        # so that any model can be drawn with the same code.

        if self.model.kind == 'Usgs':
            self.draw_usgs(d, self.model)
            return im

        elif self.model.kind == 'UsgsNames':
            self.draw_usgs_names(d, self.model)
            return im

        elif self.model.kind == 'Shapefile':
            self.draw_shp_lines(d, self.model.first_file)
            return im

        elif self.model.kind == 'Osm':
            self.draw_osm_lines(d, self.model.first_file)
            return im

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
        if dlg.categ.name.lower() == 'boundaries':
            self.draw_area_boundaries(d, dlg, area, pen, brush)
            return
        if dlg.categ.name.lower() != 'hydrography':
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
                if int(maj) in [90, 92]:
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
        # print(f'dlg.categ.name={dlg.categ.name}')
        if dlg.categ.name.lower() == 'railroads':
            self.draw_line_roads(d, dlg, line, pen, brush)
            return
        elif dlg.categ.name.lower() == 'roads and trails':
            return
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

    def draw_line_roads(self, d, dlg, line, pen=None, brush=None):
        x_win, y_win = self.t

        attr_pen = attr_brush = None
        if line.attrs is not None and len(line.attrs) > 0:
            maj, min = line.attrs[0]
            categ = dlg.categ.name.lower()
            # print(f'categ="{categ}"')
            categ = categ.replace(' ', '_')
            attr_pen, attr_brush = get_style(categ, 'lines', maj, min)

            if attr_pen is None:
                return
            # Priority: function argument, then attributes, then default
            # print(f'attr_pen={attr_pen}')
            outline_color = attr_pen
            outline_color = 'green'

            if len(line.coords) > 1:
                # Draw line segment from prev to current
                d.line([(x_win(long_), y_win(lat)) for long_, lat in line.coords],
                       fill=outline_color, width=2)

    #---------------------------------------------------------------------------
    # Shapefiles
    #---------------------------------------------------------------------------

    def draw_shp_lines(self, d, shp):
        x_win, y_win = self.t

        for rec in shp.recs:
            d.line([(x_win(x), y_win(y)) for x, y in rec.points], fill='black')
        self.write_annotation(d, f'{len(shp.recs)} lines')

    #---------------------------------------------------------------------------
    # OpenStreetMap
    #---------------------------------------------------------------------------

    def draw_osm_lines(self, d, osm):
        x_win, y_win = self.t

        for w in osm.ways:
            # w is an OsmWay, w.refs is an array of OsmNode references
            points = []
            for n in w.refs:
                try:
                    nd = osm.node_dict[n]
                except KeyError as e:
                    print(f'Node {n} not found')
                points.append((x_win(nd.lon), y_win(nd.lat)))
            d.line(points, fill='black')
            # d.line([(x_win(x), y_win(y)) for n in w.refs], fill='black')
        self.write_annotation(d, f'{len(osm.ways)} lines')

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
    