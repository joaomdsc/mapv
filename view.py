# mapv.py - map viwer

import os
import wx
from pubsub import pub

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

    def __init__(self):
        wx.Frame.__init__(self, None, -1, title='Mapv', size=(900, 600))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.SetTitle('Mapv')
        self.CreateStatusBar()
        self.SetMenuBar(self.create_menus())
        self.Show(True)

        # The view needs its model, so it can show it
        self.dlg = None

        # Listen to model updates
        pub.subscribe(self.updt_listener, 'model_updates')

    def create_menus(self):
        fm = wx.Menu()
        mi = fm.Append(wx.ID_OPEN, '&Open', 'Open a DLG-3 file')
        self.Bind(wx.EVT_MENU, self.on_open, mi)
        mi = fm.Append(wx.ID_ANY, 'Refresh', 'Clear and refresh')
        self.Bind(wx.EVT_MENU, self.on_refresh, mi)
        mi = fm.Append(wx.ID_ABOUT, '&About', 'Yet another map viewer')
        self.Bind(wx.EVT_MENU, self.on_about, mi)
        fm.AppendSeparator()
        mi = fm.Append(wx.ID_EXIT, '&Exit', 'Terminate the program')
        self.Bind(wx.EVT_MENU, self.on_quit, mi)
        mb = wx.MenuBar()
        mb.Append(fm, '&File')
        return mb

    def on_open(self, e):
        dir = (r'C:\x\data\dds.cr.usgs.gov\pub\data\DLG\100K\B\boston-e_MA'
            '\hydrography')
        d = wx.FileDialog(self, 'Choose a file', dir, '', '*.*', wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            file = d.GetFilename()
            filepath = os.path.join(dir, file)
            topic = 'view_requests'
            # print(f'Sending on topic: {topic}, msg={filepath}')
            pub.sendMessage('view_requests', arg=filepath)
        d.Destroy()

    def updt_listener(self, arg):
        self.dlg = arg
        self.GetStatusBar().PushStatusText(str(self.dlg))
        # self.dlg_draw(self.dc)
        self.Refresh()
            
    def on_refresh(self, e):
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        self.Refresh()
            
    def on_about(self, e):
        d = wx.MessageDialog(self, 'Mapv is a viewer for USGS DLG-3 cartographic data.', 'About Mapv')
        d.ShowModal()
        d.Destroy()

    def on_quit(self, e):
        self.Close(True)
                  
    def dlg_draw(self, dc):
        # Size of device context
        w_wx, h_wx = dc.GetSize()
        pad = 10
        # Drawable area (after padding)
        w_draw = w_wx - 2*pad
        h_draw = h_wx - 2*pad
        ratio_draw = w_draw/h_draw

        # Map proportions
        min_lat, max_lat, min_long, max_long = self.dlg.bounding_box()
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

        # Control points
        for cp in self.dlg.ctrl_pts:
            print(cp, end='')
            print(f', x={x_win(cp.y)}, y={y_win(cp.x)}')

        # Bounding box
        print(f'Bbox: {self.dlg.bounding_box()}')

        dc.SetBrush(wx.Brush('sky blue'))
        dc.SetPen(wx.Pen('sky blue'))
        cnt_lines = 0
        for l in self.dlg.lines:
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
        self.dc = wx.PaintDC(self)
        self.dc.SetBackground(wx.Brush('white'))
        self.dc.Clear()
        if self.dlg is None:
            return
        self.dlg_draw(self.dc)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')