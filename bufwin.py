# bufwin.py

"""Buffered window for drawing on."""

import wx

class BufferedWindow(wx.Window):
    """Handle all the double-buffering mechanics.
    
    Subclass this and define a render() method that takes a dc to draw to, and
    performs the actual drawing. The window will automatically be double
    buffered, and the screen will be automatically updated when a Paint event
    is received.

    When the drawing needs to change, the user application needs to call the
    update_drawing() method (which calls render()).
    """
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

        # Setup event handlers
        self.Bind(wx.EVT_PAINT, self. on_paint)       
        self.Bind(wx.EVT_SIZE, self.on_size)

        # Initialize the bitmap with the right size
        self.bitmap = wx.Bitmap(self.ClientSize)

    def on_paint(self, _):
        """Copy the bitmap to the screen"""
        dc = wx.BufferedPaintDC(self, self.bitmap)

    def on_size(self, _):
        """Re-initialize the bitmap with the new size and update drawing."""
        self.bitmap = wx.Bitmap(self.ClientSize)
        self.update_drawing()

    def update_drawing(self):
        """Called by the client when the drawing needs to be rendered anew."""
        dc = wx.MemoryDC()
        dc.SelectObject(self.bitmap)
        self.render(dc)
        del dc
        self.Refresh()
