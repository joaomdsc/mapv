# mapv/ui.py - map viewer user interface

import os

import wx

from bitmaps import nbr_brush
from draw import DrawingArea
from model import Model
from model_dlg3 import Dlg3Model
from model_shp import Shapefile
from model_usgs import UsgsModel
from panel import MainPanel
from storage import mapname_filepaths, get_dir, set_dir
from summary import SummaryDialog
from usgs import Usgs

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
# DlgFrame - a window whose size and position can be changed by the user
#-------------------------------------------------------------------------------

class DlgFrame(wx.Frame):

    def __init__(self, filepath=None, mapname=None):
        """mapname is the mapname-e_STATE identifier described in DLG 00README.
        """
        super().__init__(None, -1, title='Mapv', size=(900, 600))

        self.SetTitle('Mapv')
        self.CreateStatusBar()

        # Menus
        self.places_submenu = None  # for adding/removing items
        self.places_menuitem = None  # for enabling/disabling the submenu
        self.SetMenuBar(self.create_menus())
        self.Show(True)

        # Horizontal sizer
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        # Controls panel
        self.panel = MainPanel(self)
        hbox.Add(self.panel, 0, wx.EXPAND, 0)

        # Drawing area
        self.win = DrawingArea(self, size=(600,800))
        hbox.Add(self.win, 1, wx.EXPAND, 0)
        
        hbox.SetSizeHints(self)
        self.SetSizer(hbox)

        # Initially open file
        if filepath is not None:
            set_dir(os.path.dirname(filepath))
            self.win.model = Dlg3Model()
            self.win.model.open(filepath)
            
        if mapname is not None:
            self.win.model = Dlg3Model()
            self.win.model.open_mapname(mapname)

        # Reflect the current state 
        self.win.update_view()

#-------------------------------------------------------------------------------
# UI
#-------------------------------------------------------------------------------

    def on_open_route(self, _):
        wildcard = 'Shapefiles (*.shp)|*.shp|All files (*.*)|*.*'
        d = wx.FileDialog(self, message='Open a shapefile', defaultDir=get_dir(),
                          defaultFile='', wildcard=wildcard, style=wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            set_dir(dir)
            file = d.GetFilename()
            # FIXME
            if self.win.model is None or self.win.model.kind != 'Shapefile':
                self.win.model = Shapefile()
            self.win.model.open(os.path.join(dir, file))
            self.win.update_view()
        d.Destroy()

    def on_open_file(self, _):
        d = wx.FileDialog(self, 'Open a DLG-3 file', get_dir(), '',
                          '*.*', wx.FD_OPEN)
        if d.ShowModal() == wx.ID_OK:
            dir = d.GetDirectory()
            self.category = os.path.split(dir)[1]
            set_dir(dir)
            file = d.GetFilename()
            if self.win.model is None or self.win.model.kind != 'Dlg3':
                self.win.model = Dlg3Model()
            filepath = os.path.join(dir, file)
            try:
                category = self.win.model.open(filepath)
            # FIXME define an application-specific exception
            except ValueError:
                s = f"Can't open '{filepath}'"
                self.GetStatusBar().PushStatusText(s)
            # A file has been opened in category
            print('File has been opened')
            self.win.update_view()
        d.Destroy()

    def on_open_place(self, e):
        obj = e.GetEventObject()
        id = e.GetId()
        mapname = obj.GetLabel(id)
        s = f'Opening {mapname}'
        self.GetStatusBar().PushStatusText(s)
        if self.win.model is None or self.win.model.kind == 'Usgs':
            self.win.model = Dlg3Model()
        self.win.model.open_mapname(mapname)
        self.win.update_view()
            
    def on_clear(self, _):
        # FIXME clear line and area text boxes in the controls panel
        self.win.model = None
        self.showing_usgs = None
        self.win.update_view()

    def show_usgs(self, _):
        self.win.model = UsgsModel()
        s = f'Loaded {len(self.win.model.names.keys())} DLG-3 files'
        self.GetStatusBar().PushStatusText(s)
        self.add_menu_entries(self.win.model.places())
        self.win.update_view()

    def show_usgs_names(self, _):
        self.win.model = Usgs()
        self.win.update_view()

    def show_summary(self, _):
        if self.win.model is None:
            self.GetStatusBar().PushStatusText('No file open')
            return
        with SummaryDialog(filename=self.win.model.file,
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

    def on_draw_area(self, area_nbr):
        if self.win.model is None:
            self.GetStatusBar().PushStatusText('No file open')
            return
        self.win.model.area = (self.win.model.dlgs[0].areas[area_nbr-1]
                           if area_nbr != -1 else None)
        self.win.update_view()

    def on_draw_line(self, line_nbr):
        if self.win.model is None:
            self.GetStatusBar().PushStatusText('No file open')
            return
        self.win.model.line = self.win.model.dlgs[0].lines[line_nbr-1] if line_nbr != -1 else None
        self.win.update_view()
 
    def on_check_layer(self, name, state):
        self.win.check_layer(name, state)
        print('Layer box has been checked')
        # Redoing layer compositing is internal to our drawing mechanisms. From
        # the point of view of the BufferedWindow class, the bitmap must be
        # changed, so we call update_view() as usual.
        self.win.update_view(layering=True)

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

        mi = fm.Append(wx.ID_ANY, '&Open shapefile', 'Open a shapefile')
        self.Bind(wx.EVT_MENU, self.on_open_route, mi)
        
        mi = fm.Append(wx.ID_ANY, '&Clear', 'Clear all files')
        self.Bind(wx.EVT_MENU, self.on_clear, mi)
        mi = fm.Append(wx.ID_ANY, 'USGS Quads', 'Show a map of the USGS quads')
        self.Bind(wx.EVT_MENU, self.show_usgs, mi)
        mi = fm.Append(wx.ID_ANY, 'USGS Names', 'Show the named places')
        self.Bind(wx.EVT_MENU, self.show_usgs_names, mi)
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
        
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    