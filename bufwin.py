# bufwin.py

"""Buffered window for drawing on."""

import wx

class BufferedWindow(wx.Window):
    """Handle all the double-buffering mechanics.
    
    Subclass this and define a render() method that takes a gc to draw to, and
    performs the actual drawing. The window will automatically be double
    buffered, and the screen will be automatically updated when a Paint event
    is received.

    When the drawing needs to change, the user application needs to call the
    update_view() method, which will cause render(gc) to be called on the next
    idle event.

    """
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

        # Setup event handlers
        self.Bind(wx.EVT_PAINT, self.on_paint)       
        self.Bind(wx.EVT_IDLE, self.on_idle)
        self.Bind(wx.EVT_SIZE, self.on_size)

        # Initialize the bitmap with the right size. Note that ClientSize has
        # type 'wx.Size', not tuple, this breaks pillow code so we fix it.
        self.size = self.ClientSize.width, self.ClientSize.height
        self.bitmap = wx.Bitmap(self.size)

        self.redraw_needed = False
        self.layering = False

    def on_paint(self, _):
        """Copy the bitmap to the screen"""
        dc = wx.BufferedPaintDC(self, self.bitmap)

    def on_size(self, _):
        """Mark redraw as needed because the size has changed."""
        # Convert wx.Size to tuple
        sz = self.ClientSize.width, self.ClientSize.height
        if sz != self.size:
            self.size = sz
            self.update_view()

    def on_idle(self, _):
        """Rebuild the bitmap, update drawing, if needed."""
        if self.redraw_needed:
            # render_bitmap is implemented in the derived classes
            self.bitmap = self.render_bitmap(self.layering)
            self.redraw_needed = False
            self.Refresh()

    def update_view(self, layering=False):
        """Outside world's interface to request a redraw."""
        self.redraw_needed = True
        self.layering = layering
