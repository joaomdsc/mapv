# summary.py - 

import wx

#-------------------------------------------------------------------------------
# SummaryDialog
#-------------------------------------------------------------------------------

class SummaryDialog(wx.Dialog):
    
    def __init__(self, filename=None, values=None):
        super(SummaryDialog, self).__init__(None)

        self.SetSize((550, 250))
        self.SetTitle(f'Summary of file {filename}')

        # Spacings
        left_pad = 15
        top_pad = 15
        horiz_spacing = 10
        interline = 5
        
        lbl_font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD) 
      
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Banner
        b = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, -1, label='Banner : ')
        t.SetFont(lbl_font)
        b.Add(t, flag=wx.LEFT, border=left_pad)
        
        t = wx.StaticText(self, -1, label=f" {values['banner']}", style=wx.BORDER_SIMPLE)
        # t = wx.RichTextCtrl(self)
        # t.Freeze()
        # t.WriteText(values['banner'])
        # t.Thaw()
        # t.SetMargins((3, 3))
        t.SetBackgroundColour('white')
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)
        vbox.Add(b, proportion=0, flag=wx.TOP, border=top_pad)
        
        # Data cell
        b = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, -1, label=values['data_cell'])
        t.SetBackgroundColour('white')
        b.Add(t, flag=wx.LEFT, border=left_pad)

        t = wx.StaticText(self, -1, label=values['states'])
        t.SetBackgroundColour('white')
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)

        t = wx.StaticText(self, -1, label=values['src_date'])
        t.SetBackgroundColour('white')
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)

        t = wx.StaticText(self, -1, label=values['qualifier'])
        t.SetBackgroundColour('white')        
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)

        t = wx.StaticText(self, -1, label=values['scale'])
        t.SetBackgroundColour('white')        
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)

        t = wx.StaticText(self, -1, label=values['section'])
        t.SetBackgroundColour('white')        
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)
        vbox.Add(b, proportion=0, flag=wx.TOP, border=interline)

        # Category
        b = wx.BoxSizer(wx.HORIZONTAL)
        t = wx.StaticText(self, -1, label='Category : ')
        t.SetFont(lbl_font)
        b.Add(t, flag=wx.LEFT, border=left_pad)

        t = wx.StaticText(self, -1, label=f" {values['category']} ", style=wx.BORDER_SIMPLE)
        t.SetBackgroundColour('white')        
        b.Add(t, flag=wx.LEFT, border=horiz_spacing)
        vbox.Add(b, proportion=0, flag=wx.TOP, border=interline)

        # Nodes
        b = wx.BoxSizer(wx.HORIZONTAL)
        b.Add(wx.StaticText(self, -1, label='Nodes : '), flag=wx.LEFT, border=left_pad)
        t = wx.StaticText(self, -1, label=str(values['nb_nodes']))
        t.SetBackgroundColour('white')        
        b.Add(t)
        vbox.Add(b, proportion=0, flag=wx.TOP, border=interline)

        # Areas
        b = wx.BoxSizer(wx.HORIZONTAL)
        b.Add(wx.StaticText(self, -1, label='Areas : '), flag=wx.LEFT, border=left_pad)
        t = wx.StaticText(self, -1, label=str(values['nb_areas']))
        t.SetBackgroundColour('white')        
        b.Add(t)
        vbox.Add(b, proportion=0, flag=wx.TOP, border=interline)

        # Lines
        b = wx.BoxSizer(wx.HORIZONTAL)
        b.Add(wx.StaticText(self, -1, label='Lines : '), flag=wx.LEFT, border=left_pad)
        t = wx.StaticText(self, -1, label=str(values['nb_lines']))
        t.SetBackgroundColour('white')        
        b.Add(t)
        vbox.Add(b, proportion=0, flag=wx.TOP, border=interline)

        #  button
        b = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, label='Close')
        btn.Bind(wx.EVT_BUTTON, self.OnClose)
        b.Add(btn, flag=wx.LEFT, border=left_pad)
        
        vbox.Add(b, proportion=0, flag=wx.TOP, border=interline)

        self.SetSizer(vbox)
        self.Layout()

    def OnClose(self, e):
        self.Destroy()
    
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')
    