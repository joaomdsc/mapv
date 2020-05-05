# mapv/view.py - map viewer

import os
import wx
from panel import MainPanel
from summary import SummaryDialog
from style import get_style
from storage import mapname_files, get_dir, set_dir
from dlg import load_data
from usgs import Usgs
from model import Model
from model_usgs import UsgsModel
from model_dlg3 import Dlg3Model
from bitmaps import nbr_brush

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
# DlgView - a window whose size and position can be changed by the user
#-------------------------------------------------------------------------------

class DlgView(wx.Frame):

    def __init__(self, filepath=None, mapname=None):
        """mapname is the mapname-e_STATE identifier described in DLG 00README.
        """
        super(DlgView, self).__init__(None, -1, title='Mapv', size=(900, 600))

        self.SetTitle('Mapv')
        self.CreateStatusBar()

        # Menus
        self.places_submenu = None  # for adding/removing items
        self.places_menuitem = None  # for enabling/disabling the submenu
        self.SetMenuBar(self.create_menus())
        self.Show(True)

        # Main panel
        self.panel = MainPanel(self, parent_frame=self)
        # self.panel.Bind(wx.EVT_SIZE, self.on_size)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.pen = None
        self.brush = None

        # The view needs its model, so it can show it
        self.model = None

        # Transformation is (x_win, y_win)
        self.t = None

        # Initially open file
        if filepath is not None:
            set_dir(os.path.dirname(filepath))
            self.model = Dlg3Model()
            self.model.open(filepath)

        if mapname is not None:
            self.model = Dlg3Model()
            open_mapname(mapname)

    def on_open_file(self, _):
        d = wx.FileDialog(self, 'Open a DLG-3 file', get_dir(), '',
                          '*.*', wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            set_dir(dir)
            file = d.GetFilename()
            if self.model is None or self.model.kind == 'Usgs':
                self.model = Dlg3Model()
            self.model.open(os.path.join(dir, file))
            self.Refresh()
        d.Destroy()

    def on_open_place(self, e):
        obj = e.GetEventObject()
        id = e.GetId()
        mapname = obj.GetLabel(id)
        print(f'{obj.GetLabel(id)}')
        s = f'Opening {mapname}'
        self.GetStatusBar().PushStatusText(s)
        if self.model is None or self.model.kind == 'Usgs':
            self.model = Dlg3Model()
        self.model.open_mapname(mapname)
        self.Refresh()
            
    def on_clear(self, _):
        self.model = None
        self.showing_usgs = None
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        self.Refresh()
            
    def on_refresh(self, _):
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        self.Refresh()

    def show_usgs(self, _):
        self.model = UsgsModel()
        s = f'Loaded {len(self.model.names.keys())} DLG-3 files'
        self.GetStatusBar().PushStatusText(s)
        self.add_menu_entries(self.model.places())
        self.Refresh()

    def show_summary(self, _):
        if self.model is None:
            self.GetStatusBar().PushStatusText('No file open')
            return
        with SummaryDialog(filename=self.model.file,
                           values=self.dlg.summary()) as d:
            d.ShowModal()

    def show_colors(self, _):
        data = wx.ColourData()
        with wx.ColourDialog(self, data) as d:
            d.ShowModal()
            data = d.GetColourData()
            c = data.GetColour()
            # print(f'Color: {c}')

    def on_about(self, _):
        s = 'Mapv is a viewer for USGS DLG-3 cartographic data.'
        d = wx.MessageDialog(self, s, 'About Mapv')
        d.ShowModal()
        d.Destroy()

    def on_quit(self, _):
        self.Close(True)
        
    def create_menus(self):
        fm = wx.Menu()
        mi = fm.Append(wx.ID_ANY, '&Open file', 'Open a DLG-3 file')
        self.Bind(wx.EVT_MENU, self.on_open_file, mi)

        # Sub-menu
        m = wx.Menu()
        mi = fm.Append(wx.ID_ANY, '&Open place', m)
        mi.Enable(False)

        # Persist
        self.places_submenu = m  # for adding/removing items
        self.places_menuitem = mi  # for enabling/disabling the submenu

        mi = fm.Append(wx.ID_ANY, '&Clear', 'Clear all files')
        self.Bind(wx.EVT_MENU, self.on_clear, mi)
        mi = fm.Append(wx.ID_ANY, 'Refresh', 'Refresh the display')
        self.Bind(wx.EVT_MENU, self.on_refresh, mi)
        mi = fm.Append(wx.ID_ANY, 'USGS Quads', 'Show a map of the USGS quads')
        self.Bind(wx.EVT_MENU, self.show_usgs, mi)
        mi = fm.Append(wx.ID_ANY, 'Summary', 'Show a summary of a file')
        self.Bind(wx.EVT_MENU, self.show_summary, mi)
        mi = fm.Append(wx.ID_ANY, 'Colors', 'Color picker')
        self.Bind(wx.EVT_MENU, self.show_colors, mi)
        mi = fm.Append(wx.ID_ANY, '&About', 'Yet another map viewer')
        self.Bind(wx.EVT_MENU, self.on_about, mi)
        fm.AppendSeparator()
        mi = fm.Append(wx.ID_ANY, '&Exit', 'Terminate the program')
        self.Bind(wx.EVT_MENU, self.on_quit, mi)
        mb = wx.MenuBar()
        mb.Append(fm, '&File')
        return mb

    def add_menu_entries(self, places):
        m = self.places_submenu

        for p in places:
            # The first string appears on the menu itself, and it's what we
            # retrieve in obj.GetLabel(id) in the event handler. The second
            # string is displayed on the status bar.
            mi = m.Append(wx.ID_ANY, p, p)
            self.Bind(wx.EVT_MENU, self.on_open_place, mi)
        self.places_menuitem.Enable(True)
        
    def get_transform(self):
        """Get the transformation functions from map to drawing.

        This changes on two occasions:
          - when another DLG file is added
          - when the window is resized
          """
        # FIXME get_transform works from a model, of which I have two. Define
        # the model's API and re-factor this..
        
        # Size of device context
        w_wx, h_wx = self.dc.GetSize()
        # print(f'dc.GetSize: w={w_wx}, h={h_wx}')
        pad = 10
        
        # Drawable area (after padding)
        w_draw = w_wx - 2*pad
        h_draw = h_wx - 2*pad
        ratio_draw = w_draw/h_draw

        # Map proportions
        min_lat, max_lat, min_long, max_long = self.model.bounding_box()
            
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

    def dlg_draw(self, dlg):
        x_win, y_win = self.t
        
        # Draw areas
        for a in dlg.areas:
            self.draw_area(dlg, a)

        # Draw lines
        for line in dlg.lines:
            self.draw_line(dlg, line)

    def on_draw_area(self, area_nbr):
        self.model.area = (self.model.dlgs[0].areas[area_nbr-1]
                           if area_nbr != -1 else None)
        self.bitmap_brush = nbr_brush(area_nbr)
        self.Refresh()

    def draw_area(self, dlg, area, pen=None, brush=None):
        """Paint the area's polygon, and all the areas inside its islands."""
        x_win, y_win = self.t

        # Draw the area's polygon with its own style 
        attr_pen = attr_brush = None
        if area.attrs is not None and len(area.attrs) > 0:
            maj, min = area.attrs[0]
            attr_pen, attr_brush = get_style('hydrography', 'areas', maj, min)

        # Priority: function argument, then attributes, then default
        self.dc.SetPen(pen if pen is not None else
                 attr_pen if attr_pen is not None else
                 self.pen)
        self.dc.SetBrush(brush if brush is not None else
                 attr_brush if attr_brush is not None else
                 self.brush)
        
        points = [(x_win(long_), y_win(lat))
                      for long_, lat in area.get_points(dlg)]
        self.dc.DrawPolygon(points)

        # Now draw all the areas inside the islands
        for a in area.inner_areas():
            self.draw_area(dlg, a)
 
    def on_draw_line(self, line_nbr):
        self.model.line = self.model.dlgs[0].lines[line_nbr-1] if line_nbr != -1 else None
        self.Refresh()

    def draw_line(self, dlg, line, pen=None, brush=None):
        x_win, y_win = self.t

        attr_pen = attr_brush = None
        if line.attrs is not None and len(line.attrs) > 0:
            maj, min = line.attrs[0]
            attr_pen, attr_brush = get_style('hydrography', 'lines', maj, min)
            
        # Priority: function argument, then attributes, then default
        self.dc.SetPen(pen if pen is not None else
                 attr_pen if attr_pen is not None else
                 self.pen)
        self.dc.SetBrush(brush if brush is not None else
                 attr_brush if attr_brush is not None else
                 self.brush)
        
        if len(line.coords) > 1:
            # line.coords is a list of (long, lat) couples
            prev_long, prev_lat = line.coords[0]
            for long_, lat in line.coords[1:]:
                # Draw line segment from prev to current
                self.dc.DrawLine(x_win(prev_long), y_win(prev_lat),
                            x_win(long_), y_win(lat))
                prev_lat = lat
                prev_long = long_

    def draw_usgs(self, model):
        x_win, y_win = self.t

        # Draw rectangles that hold a named place from control points
        for mapname, zone, box in model.named_rects_ctrl():
            # print(f'Ctrl: {mapname} {box}')
            min_lat, max_lat, min_long, max_long = box
            SW = x_win(min_long), y_win(min_lat)
            NW = x_win(min_long), y_win(max_lat)
            NE = x_win(max_long), y_win(max_lat)
            SE = x_win(max_long), y_win(min_lat)
            self.dc.DrawPolygon([SW, NW, NE, SE])

            # Box dimensions
            box_w = SE[0] - SW[0]
            box_h = SW[1] - NW[1]
            
            # Write something inside the box
            self.dc.DrawText(mapname, SW[0] + 5, NW[1] + 5)

            w, h = self.dc.GetTextExtent(str(zone))
            x = int(round((box_w - w)/2))
            y = int(round((box_h - h)/2))
            self.dc.DrawText(str(zone), SW[0] + x, NW[1] + y)

    def draw_names(self):
        x_win, y_win = self.t

        # Draw rectangles when they hold a named place
        self.dc.SetPen(wx.Pen('black'))
        self.dc.SetBrush(wx.Brush('#e0e0e0'))
        x_prev = self.usgs.lng_min
        for x in range(self.usgs.lng_min + 1, self.usgs.lng_max):
            lat_prev = self.usgs.lat_min
            for y in range(10*(self.usgs.lat_min + 5),
                           10*(self.usgs.lat_max + 1), 5):
                lat = y/10
                # Paint the rectangle gray if it contains a named place
                if self.usgs.get_place(lat_prev, x) is not None:
                    points = [
                        (x_win(x_prev), y_win(lat_prev)),
                        (x_win(x), y_win(lat_prev)),
                        (x_win(x), y_win(lat)),
                        (x_win(x_prev), y_win(lat)),
                    ]
                    self.dc.DrawPolygon(points)
                lat_prev = lat
            x_prev = x

        # Draw horizontal lines
        self.dc.SetPen(wx.Pen('black'))
        for y in range(10*self.usgs.lat_min, 10*(self.usgs.lat_max + 1), 5):
            lat = y/10
            self.dc.DrawLine(x_win(self.usgs.lng_min), y_win(lat),
                             x_win(self.usgs.lng_max), y_win(lat))

        # Draw vertical lines
        for x in range(self.usgs.lng_min, self.usgs.lng_max):
            self.dc.DrawLine(x_win(x), y_win(self.usgs.lat_min),
                             # The "+ 0.5" below is actually something like a
                             # "next(self.usgs.lat_max)" in the iterator sense
                             x_win(x), y_win(self.usgs.lat_max + 0.5))

        # Pinpoint the named places
        self.dc.SetBrush(wx.Brush('red'))
        for lng, lat in self.name_points:
            self.dc.DrawCircle(x_win(lng), y_win(lat), 2)

    def on_size(self, _):
        self.Refresh()

    def on_paint(self, _):
        self.dc = wx.PaintDC(self.panel)
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        self.pen = self.dc.GetPen()
        self.brush = self.dc.GetBrush()
            
        # If there are no models yet, nothing to paint
        if self.model is None:
            return
        
        # Define transformation form model to drawing window 
        self.t = self.get_transform()

        if self.model.kind == 'Usgs':
            # Models should expose iterators/generators on polygons, lines,
            # nodes, so that any model can be drawn.
            self.draw_usgs(self.model)
            return

        # Draw all DLGs
        for dlg in self.model.dlgs:
            self.dlg_draw(dlg)
            
        # Special requests act on dlgs[0]
        if self.model.line is not None:
            self.draw_line(self.model.dlgs[0], self.model.line, pen=wx.Pen('red'))
        if self.model.area is not None:
            self.draw_area(self.model.dlgs[0], self.model.area, pen=wx.Pen('black'),
                           brush=wx.Brush('red'))
                           # brush=self.bitmap_brush)
    
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    