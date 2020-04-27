# mapv.py - map viewer

import os
import wx
from pubsub import pub
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

        # Other widgets
        self.panel = wx.Panel(self)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.caption = wx.StaticText(self, -1, "My text caption")
        self.control = wx.TextCtrl(self, -1, size=(200,150), style=wx.TE_MULTILINE)
        self.sizer.Add(self.caption, proportion=0)
        self.sizer.Add(self.control, proportion=0)
        self.sizer.Add(self.panel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(self.sizer)

        # The view needs its model, so it can show it
        self.dlg = None  # open
        self.dlg2 = None  # add
        self.file = None

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
                  
    def dlg_draw(self, dc, dlg, pen, brush):
        # Size of device context
        w_wx, h_wx = dc.GetSize()
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

        # # Control points
        # for cp in dlg.ctrl_pts:
        #     print(cp, end='')
        #     print(f', x={x_win(cp.y)}, y={y_win(cp.x)}')

        # # Bounding box
        # print(f'Bbox: {dlg.bounding_box()}')

        dc.SetBrush(brush)
        dc.SetPen(pen)
        cnt_lines = 0
        for l in dlg.lines:
            if len(l.coords) > 1:
                # l.coords is a list of (long, lat) couples
                prev_long, prev_lat = l.coords[0]
                cnt_coords = 0
                for long_, lat in l.coords[1:]:
                    # Draw line segment from prev to current
                    dc.DrawLine(x_win(prev_long), y_win(prev_lat),
                                x_win(long_), y_win(lat))
                    prev_lat = lat
                    prev_long = long_
        
    def on_paint(self, e):
        self.dc = wx.PaintDC(self.panel)
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        if self.dlg is None:
            return
        self.dlg_draw(self.dc, self.dlg, wx.Pen('sky blue'), wx.Brush('sky blue'))
        if self.dlg2 is not None:
            self.dlg_draw(self.dc, self.dlg2, wx.Pen('black'), wx.Brush('black'))
    
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    