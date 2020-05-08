# panel.py - 

import wx

#-------------------------------------------------------------------------------
# MainPanel
#-------------------------------------------------------------------------------

class MainPanel(wx.Panel):
    """The main application panel.

    The main panel has two sub-panels: the left one (larger) is used for
    drawing the maps, the right one (smaller) is for controls.
    """
    
    def __init__(self, *args, **kw):
        super(MainPanel, self).__init__(*args, **kw)

        # Lay out controls vertically
        vbox = wx.BoxSizer(wx.VERTICAL)

        # First row
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
        txt = wx.StaticText(self, label="Map controls")
        txt.SetFont(txt.GetFont().MakeBold())
        
        hbox1.Add(txt)
        vbox.Add(hbox1, flag=wx.TOP|wx.LEFT, border=10)

        # Second row - draw line
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(self, label='Line nbr'), flag=wx.RIGHT, border=8)

        self.tcl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox1.Add(self.tcl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Third row
        btn = wx.Button(self, label='Draw line', size=(70, 30))
        vbox.Add(btn, flag=wx.LEFT|wx.TOP, border=10)
        self.Bind(wx.EVT_BUTTON, self.on_button_line, btn)

        # Fourth row - draw area
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(self, label='Area nbr'), flag=wx.RIGHT, border=8)

        self.tca = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox1.Add(self.tca, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Fifth row
        btn = wx.Button(self, label='Draw area', size=(70, 30))
        vbox.Add(btn, flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=10)
        self.Bind(wx.EVT_BUTTON, self.on_button_area, btn)

        # Finished doing layout
        self.SetSizer(vbox)

    def on_button_line(self, _):
        s = self.tcl.GetValue()
        line_nbr = -1 if s == '' else int(s)
        self.GetParent().on_draw_line(line_nbr)

    def on_button_area(self, _):
        s = self.tca.GetValue()
        area_nbr = -1 if s == '' else int(s)
        self.GetParent().on_draw_area(area_nbr)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    