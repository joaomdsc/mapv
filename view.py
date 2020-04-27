# mapv.py - map viewer

import os
import wx
from pubsub import pub
from panel import MainPanel
from summary import SummaryDialog

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

    def __init__(self, filepath=None):
        super(DlgView, self).__init__(None, -1, title='Mapv', size=(900, 600))

        self.SetTitle('Mapv')
        self.CreateStatusBar()
        self.SetMenuBar(self.create_menus())
        self.Show(True)

        # Main panel
        self.panel = MainPanel(self, parent_frame=self)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)

        # The view needs its model, so it can show it
        self.dlg = None  # open
        self.dlg2 = None  # add
        self.file = None
        self.line_nbr = None
        self.area_nbr = None

        # Listen to model updates
        pub.subscribe(self.updt_listener, 'model_updates')

        # Misc
        self.request = ''

        # Initially open file
        if filepath is not None:
            self.set_dir(os.path.dirname(filepath))
            self.file = os.path.basename(filepath)
            topic = 'view_requests'
            self.request = 'open'
            pub.sendMessage('view_requests', arg=filepath)


    def show_summary(self, e):
        if self.dlg is None:
            self.GetStatusBar().PushStatusText('No file open')
            return
        with SummaryDialog(filename=self.file,
                           values=self.dlg.summary()) as d:
            d.ShowModal()
            
    def create_menus(self):
        fm = wx.Menu()
        mi = fm.Append(wx.ID_OPEN, '&Open', 'Open a DLG-3 file')
        self.Bind(wx.EVT_MENU, self.on_open, mi)
        mi = fm.Append(wx.ID_ANY, '&Add', 'Add a DLG-3 file on top')
        self.Bind(wx.EVT_MENU, self.on_add, mi)
        mi = fm.Append(wx.ID_ANY, 'Refresh', 'Clear and refresh')
        self.Bind(wx.EVT_MENU, self.on_refresh, mi)
        mi = fm.Append(wx.ID_ANY, 'Summary', 'Show a summary of file')
        self.Bind(wx.EVT_MENU, self.show_summary, mi)
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

    def on_open(self, e):
        d = wx.FileDialog(self, 'Choose a file to open', self.get_dir(), '',
                          '*.*', wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            self.set_dir(dir)
            # FIXME self.file should be set by the update listener
            self.file = d.GetFilename()
            filepath = os.path.join(dir, self.file)
            topic = 'view_requests'
            self.request = 'open'
            pub.sendMessage('view_requests', arg=filepath)
        d.Destroy()

    def on_add(self, e):
        d = wx.FileDialog(self, 'Add a file on top', self.open_dir, '', '*.*',
                          wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            self.open_dir = d.GetDirectory()
            file = d.GetFilename()
            filepath = os.path.join(self.open_dir, file)
            topic = 'view_requests'
            self.request = 'add'
            pub.sendMessage('view_requests', arg=filepath)
        d.Destroy()

    def updt_listener(self, arg):
        if self.request == 'open':
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

    def get_transform(self, dlg):
        """Get the transformation functions from map to drawing."""
        
        # Size of device context
        w_wx, h_wx = self.dc.GetSize()
        pad = 10
        
        # Drawable area (after padding)
        w_draw = w_wx - 2*pad
        h_draw = h_wx - 2*pad
        ratio_draw = w_draw/h_draw

        # Map proportions
        min_lat, max_lat, min_long, max_long = dlg.bounding_box()
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
        
    def dlg_draw(self, dlg, pen, brush):
        # Transforming coordinates from map to drawing
        x_win, y_win = self.get_transform(dlg)

        # Draw the lines in black
        self.dc.SetBrush(brush)
        self.dc.SetPen(pen)
        for l in dlg.lines:
            if len(l.coords) > 1:
                # l.coords is a list of (long, lat) couples
                prev_long, prev_lat = l.coords[0]
                for long_, lat in l.coords[1:]:
                    # Draw line segment from prev to current
                    self.dc.DrawLine(x_win(prev_long), y_win(prev_lat),
                                x_win(long_), y_win(lat))
                    prev_lat = lat
                    prev_long = long_

        # Draw areas that meet certain criteria
        self.dc.SetBrush(wx.Brush('sky blue'))
        self.dc.SetPen(wx.Pen('black'))
        for a in dlg.areas:
            print(f"Area {a.id}: {', '.join([str(x) for x in a.adj_lines])}")
            if a.attrs is not None and len(a.attrs) > 0 and a.nb_islands == 0:
                for maj, min in a.attrs:
                    if int(maj) == 50 and int(min) in [116, 412, 421]:
                        points = [(x_win(long_), y_win(lat))
                                      for long_, lat in a.get_points(self.dlg)]
                        self.dc.DrawPolygon(points)

    def draw_red_line(self, line_nbr):
        self.line_nbr = line_nbr
        self.Refresh()

    def draw_line(self, line_nbr):
        # Transforming coordinates from map to drawing
        x_win, y_win = self.get_transform(self.dlg)

        self.dc.SetBrush(wx.Brush('black'))
        self.dc.SetPen(wx.Pen('red'))
        line = self.dlg.lines[line_nbr - 1]
        if len(line.coords) > 1:
            # line.coords is a list of (long, lat) couples
            prev_long, prev_lat = line.coords[0]
            for long_, lat in line.coords[1:]:
                # Draw line segment from prev to current
                self.dc.DrawLine(x_win(prev_long), y_win(prev_lat),
                            x_win(long_), y_win(lat))
                prev_lat = lat
                prev_long = long_

    def draw_blue_area(self, area_nbr):
        self.area_nbr = area_nbr
        self.Refresh()

    def draw_area(self, area_nbr):
        # Transforming coordinates from map to drawing
        x_win, y_win = self.get_transform(self.dlg)
        
        self.dc.SetBrush(wx.Brush('sky blue'))
        self.dc.SetPen(wx.Pen('black'))
        a = self.dlg.areas[area_nbr-1]
        print(f"Area {a.id}: {', '.join([str(x) for x in a.adj_lines])}")
        points = [(x_win(long_), y_win(lat))
                      for long_, lat in a.get_points(self.dlg)]
        self.dc.DrawPolygon(points)

    def on_paint(self, e):
        self.dc = wx.PaintDC(self.panel)
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        if self.dlg is None:
            return
        self.dlg_draw(self.dlg, wx.Pen('black'), wx.Brush('black'))
        if self.dlg2 is not None:
            self.dlg_draw(self.dlg2, wx.Pen('black'), wx.Brush('black'))
        if self.line_nbr is not None:
            self.draw_line(self.line_nbr)
        if self.area_nbr is not None:
            self.draw_area(self.area_nbr)
    
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    