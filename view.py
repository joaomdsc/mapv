# mapv.py - map viewer

import os
import wx
from panel import MainPanel
from summary import SummaryDialog
from style import get_style
from dlg import load_data

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
        self.SetMenuBar(self.create_menus())
        self.Show(True)

        # Main panel
        self.panel = MainPanel(self, parent_frame=self)
        self.panel.Bind(wx.EVT_SIZE, self.on_size)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)

        # The view needs its model, so it can show it
        self.dlgs = None

        # Transformation is (x_win, y_win)
        self.t = None
        
        self.file = None
        self.line_nbr = None
        self.area_nbr = None

        # Misc
        self.request = ''

        # Initially open file
        if filepath is not None:
            self.set_dir(os.path.dirname(filepath))
            self.file = os.path.basename(filepath)
            
            self.dlgs = [load_data(filepath)]

        if mapname is not None:
            path = r'C:\x\data\dds.cr.usgs.gov\pub\data\DLG\100K'
            path = os.path.join(path, mapname[0].upper())
            path = os.path.join(path, mapname)

            if not os.path.isdir(path):
                print(f"Can't find '{mapname}'")
            else:
                self.dlgs = []
                for f in os.listdir(path):
                    if f != 'hydrography':
                        continue
                    layer = os.path.join(path, f)
                    if os.path.isdir(layer):
                        for g in os.listdir(layer):
                            if g.endswith('.opt.gz'):
                                filepath = os.path.join(layer, g)
                                try:
                                    self.dlgs.append(load_data(filepath))
                                except ValueError:
                                    pass

    def show_summary(self, e):
        if self.dlg is None:
            self.GetStatusBar().PushStatusText('No file open')
            return
        with SummaryDialog(filename=self.file,
                           values=self.dlg.summary()) as d:
            d.ShowModal()

    def show_colors(self, e):
        data = wx.ColourData()
        with wx.ColourDialog(self, data) as d:
            d.ShowModal()
            data = d.GetColourData()
            c = data.GetColour()
            print(f'Color: {c}')
            
    def create_menus(self):
        fm = wx.Menu()
        mi = fm.Append(wx.ID_OPEN, '&New', 'Open a new DLG-3 file')
        self.Bind(wx.EVT_MENU, self.on_new, mi)
        mi = fm.Append(wx.ID_ANY, '&Open', 'Open another DLG-3 file on top')
        self.Bind(wx.EVT_MENU, self.on_open, mi)
        mi = fm.Append(wx.ID_ANY, 'Refresh', 'Clear and refresh')
        self.Bind(wx.EVT_MENU, self.on_refresh, mi)
        mi = fm.Append(wx.ID_ANY, 'Summary', 'Show a summary of file')
        self.Bind(wx.EVT_MENU, self.show_summary, mi)
        mi = fm.Append(wx.ID_ANY, 'Colors', 'Color picker')
        self.Bind(wx.EVT_MENU, self.show_colors, mi)
        mi = fm.Append(wx.ID_ABOUT, '&About', 'Yet another map viewer')
        self.Bind(wx.EVT_MENU, self.on_about, mi)
        fm.AppendSeparator()
        mi = fm.Append(wx.ID_EXIT, '&Exit', 'Terminate the program')
        self.Bind(wx.EVT_MENU, self.on_quit, mi)
        mb = wx.MenuBar()
        mb.Append(fm, '&File')
        return mb

    def get_dir(self):
        """Retrieve the directory path for opening files.

        Each time a file is opened, mapv stores the directory path in a
        file, so it can be reused. This function returns that path.
        """
        filepath = os.path.join(os.environ.get('HOME'), '.mapv')
        if not os.path.isfile(filepath):
            return r'C:\x\data\dds.cr.usgs.gov\pub\data\DLG\100K'
        with open(filepath, 'r') as f:
            # Assume file contains just the directory path
            return f.read().strip()

    def set_dir(self, dir):
        filepath = os.path.join(os.environ.get('HOME'), '.mapv')
        with open(filepath, 'w') as f:
            f.write(dir)

    def on_new(self, e):
        d = wx.FileDialog(self, 'Choose a new file to open', self.get_dir(), '',
                          '*.*', wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            self.set_dir(dir)
            self.file = d.GetFilename()
            filepath = os.path.join(dir, self.file)

            self.dlgs = [load_data(filepath)]
            self.Refresh()
        d.Destroy()

    def on_open(self, e):
        d = wx.FileDialog(self, 'Open another file on top', self.get_dir(), '',
                          '*.*', wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            self.set_dir(dir)
            file = d.GetFilename()
            filepath = os.path.join(dir, file)

            self.dlgs.append(load_data(filepath))
            self.Refresh()
        d.Destroy()

    def updt_listener(self, arg):
        if self.request == 'new':
            self.dlg = arg
            s = str(self.dlg)
        else:
            self.dlg2 = arg
            s = str(self.dlg2)
        self.GetStatusBar().PushStatusText(str(s))
        self.Refresh()
            
    def on_refresh(self, e):
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        self.Refresh()
            
    def on_about(self, e):
        s = 'Mapv is a viewer for USGS DLG-3 cartographic data.'
        d = wx.MessageDialog(self, s, 'About Mapv')
        d.ShowModal()
        d.Destroy()

    def on_quit(self, e):
        self.Close(True)

    # FIXME move this to a helpers module with unit tests
    def bbox_union(self, b1, b2):
        min_lat = b1[0] if b1[0] < b2[0] else b2[0]
        max_lat = b1[1] if b1[1] > b2[1] else b2[1]
        min_long = b1[2] if b1[2] < b2[2] else b2[2]
        max_long = b1[3] if b1[3] > b2[3] else b2[3]
        return min_lat, max_lat, min_long, max_long
        
    def get_transform(self):
        """Get the transformation functions from map to drawing.

        This changes on two occasions:
          - when another DLG file is added
          - when the window is resized
          """
        
        # Size of device context
        w_wx, h_wx = self.dc.GetSize()
        pad = 10
        
        # Drawable area (after padding)
        w_draw = w_wx - 2*pad
        h_draw = h_wx - 2*pad
        ratio_draw = w_draw/h_draw

        # Map proportions
        if len(self.dlgs) == 1:
            min_lat, max_lat, min_long, max_long = self.dlgs[0].bounding_box()
        else:
            box = self.dlgs[0].bounding_box()
            for d in self.dlgs[1:]:
               box =  self.bbox_union(box, d.bounding_box())
            # Note the trailing comma that makes it a tuple
            min_lat, max_lat, min_long, max_long = *box,
            
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

        # Draw the lines in black
        default_pen = wx.Pen('black')
        default_brush = wx.Brush('black')
        
        for l in dlg.lines:
            if len(l.coords) > 1:
                # l.coords is a list of (long, lat) couples
                pen = brush = None
                if l.attrs is not None and len(l.attrs) > 0:
                    maj, min = l.attrs[0]
                    # print(f'Line {l.id}: "{maj}", "{min}"')
                    pen, brush = get_style('hydrography', 'lines', maj, min)
                    
                self.dc.SetPen(default_pen if pen is None else pen)
                self.dc.SetBrush(default_brush if brush is None else brush)
                
                prev_long, prev_lat = l.coords[0]
                for long_, lat in l.coords[1:]:
                    # Draw line segment from prev to current
                    self.dc.DrawLine(x_win(prev_long), y_win(prev_lat),
                                x_win(long_), y_win(lat))
                    prev_lat = lat
                    prev_long = long_

        # Draw areas that meet certain criteria
        for a in dlg.areas:
            if a.nb_islands > 0 or a.attrs is None or len(a.attrs) == 0:
                continue
            maj, min = a.attrs[0]
            # print(f'Area {a.id}: "{maj}", "{min}"')
            pen, brush = get_style('hydrography', 'areas', maj, min)
            if pen is None and brush is None:
                continue
            self.dc.SetPen(default_pen if pen is None else pen)
            self.dc.SetBrush(default_brush if brush is None else brush)
            points = [(x_win(long_), y_win(lat))
                              for long_, lat in a.get_points(dlg)]
            self.dc.DrawPolygon(points)

    def on_draw_line(self, line_nbr):
        self.line_nbr = line_nbr
        self.Refresh()

    def draw_line(self, line_nbr):
        x_win, y_win = self.t

        pen, brush = wx.Pen('black'), wx.Brush('black')
        line = self.dlg.lines[line_nbr - 1]
        if line.attrs is not None and len(line.attrs) > 0:
            maj, min = line.attrs[0]
            pen, brush = get_style('hydrography', 'lines', maj, min)
        self.dc.SetPen(pen)
        self.dc.SetBrush(brush)
        if len(line.coords) > 1:
            # line.coords is a list of (long, lat) couples
            prev_long, prev_lat = line.coords[0]
            for long_, lat in line.coords[1:]:
                # Draw line segment from prev to current
                self.dc.DrawLine(x_win(prev_long), y_win(prev_lat),
                            x_win(long_), y_win(lat))
                prev_lat = lat
                prev_long = long_

    def on_draw_area(self, area_nbr):
        self.area_nbr = area_nbr
        self.Refresh()

    def draw_area(self, area_nbr):
        x_win, y_win = self.t
        
        pen, brush = wx.Pen('red'), wx.Brush('orange')
        a = self.dlg.areas[area_nbr-1]
        if a.attrs is not None and len(a.attrs) > 0:
            maj, min == a.attrs[0]
            pen, brush = get_style('hydrography', 'areas', maj, min)
        self.dc.SetPen(pen)
        self.dc.SetBrush(brush)
        # print(f"Area {a.id}: {', '.join([str(x) for x in a.adj_lines])}")
        points = [(x_win(long_), y_win(lat))
                      for long_, lat in a.get_points(self.dlg)]
        self.dc.DrawPolygon(points)

    def on_size(self, e):
        self.Refresh()

    def on_paint(self, e):
        self.dc = wx.PaintDC(self.panel)
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()

        # If there's no data yet, nothing to paint
        if self.dlgs is None:
            return
        
        # Transform requires a wx.DC
        self.t = self.get_transform()

        # Draw all DLGs
        for dlg in self.dlgs:
            self.dlg_draw(dlg)
            
        # Special requests
        # FIXME line/area is no longer enough when there are several quad's open
        if self.line_nbr is not None:
            self.draw_line(self.line_nbr)
        if self.area_nbr is not None:
            self.draw_area(self.area_nbr)
    
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    