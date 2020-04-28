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
    
    def __init__(self, *args, parent_frame=None, **kw):
        super(MainPanel, self).__init__(*args, **kw)

        self.parent_frame = parent_frame
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Create controls panel
        ctrl = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)

        # First row
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        txt = wx.StaticText(ctrl, -1, "Map controls")
        hbox1.Add(txt, flag=wx.RIGHT, border=8)
        vbox.Add(txt)

        # Draw line

        # Third row
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(ctrl, label='Line nbr')
        hbox1.Add(lbl, flag=wx.RIGHT, border=8)
        
        self.tcl = wx.TextCtrl(ctrl, style=wx.TE_PROCESS_ENTER)
        hbox1.Add(self.tcl, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Fourth row
        btn = wx.Button(ctrl, label='Draw line', size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnButtonLine, btn)
        vbox.Add(btn, flag=wx.LEFT, border=10)

        # Draw area

        # Third row
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        lbl = wx.StaticText(ctrl, label='Area nbr')
        hbox1.Add(lbl, flag=wx.RIGHT, border=8)
        
        self.tca = wx.TextCtrl(ctrl, style=wx.TE_PROCESS_ENTER)
        hbox1.Add(self.tca, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Fourth row
        btn = wx.Button(ctrl, label='Draw area', size=(70, 30))
        self.Bind(wx.EVT_BUTTON, self.OnButtonArea, btn)
        vbox.Add(btn, flag=wx.LEFT, border=10)

        ctrl.SetSizer(vbox)

        hbox.Add(ctrl, flag=wx.EXPAND)

        # Create drawing panel
        drw = wx.Panel(self)
        hbox.Add(drw, proportion=1)
        
        self.SetSizer(hbox)

    def OnButtonLine(self, e):
        line = int(self.tcl.GetValue())
        # print(f'Drawing line {line}.')
        self.parent_frame.on_draw_line(line)

    def OnButtonArea(self, e):
        area = int(self.tca.GetValue())
        # print(f'Drawing area {area}.')
        self.parent_frame.on_draw_area(area)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    