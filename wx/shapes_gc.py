# shapes_gc.py -

"""
https://github.com/wxWidgets/Phoenix/blob/master/demo/GraphicsContext.py
"""

import wx
import colorsys
from math import cos, sin, radians

BASE  = 80.0    # sizes used in shapes drawn below
BASE2 = BASE/2
BASE4 = BASE/4

USE_BUFFER = ('wxMSW' in wx.PlatformInfo) # use buffered drawing on Windows

class TopFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.SetTitle("Graphics Context Demo")
        if USE_BUFFER:
            self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, e):
        self.init_buffer()
        e.Skip()
        
    def on_paint(self, e):
        if USE_BUFFER:
            dc = wx.BufferedPaintDC(self, self._buffer)
        else:
            dc = wx.PaintDC(self)
            gc = self.make_gc(dc)
            self.render(gc)

    def init_buffer(self):
        sz = self.GetClientSize()
        sz.width = max(1, sz.width)
        sz.height = max(1, sz.height)
        self._buffer = wx.Bitmap(sz.width, sz.height, 32)

        dc = wx.MemoryDC(self._buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        gc = self.make_gc(dc)
        self.render(gc)

    def make_gc(self, dc):
        return wx.GraphicsContext.Create(dc)

    def render(self, gc):
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        gc.SetFont(font, wx.Colour('black'))

        # Make a path that contains a circle and some lines, centered at 0,0
        path = gc.CreatePath()
        path.AddCircle(0, 0, BASE2)
        path.MoveToPoint(0, -BASE2)
        path.AddLineToPoint(0, BASE2)
        path.MoveToPoint(-BASE2, 0)
        path.AddLineToPoint(BASE2, 0)
        path.CloseSubpath()
        path.AddRectangle(-BASE4, -BASE4/2, BASE2, BASE4)


        # Now use that path to demonstrate various capbilites of the grpahics context
        gc.PushState()             # save current translation/scale/other state 
        gc.Translate(60, 75)       # reposition the context origin

        gc.SetPen(wx.Pen("navy", 1))
        gc.SetBrush(wx.Brush("pink"))

        # show the difference between stroking, filling and drawing
        for label, PathFunc in [("StrokePath", gc.StrokePath),
                                ("FillPath",   gc.FillPath),
                                ("DrawPath",   gc.DrawPath)]:
            w, h = gc.GetTextExtent(label)
            
            gc.DrawText(label, -w/2, -BASE2-h-4)
            PathFunc(path)
            gc.Translate(2*BASE, 0)

            
        gc.PopState()              # restore saved state
        gc.PushState()             # save it again
        gc.Translate(60, 200)      # offset to the lower part of the window
        
        gc.DrawText("Scale", 0, -BASE2)
        gc.Translate(0, 20)

        # for testing clipping
        #gc.Clip(0, 0, 100, 100)
        #rgn = wx.RegionFromPoints([ (0,0), (75,0), (75,25,), (100, 25),
        #                            (100,100), (0,100), (0,0)  ])
        #gc.ClipRegion(rgn)
        #gc.ResetClip()
        
        gc.SetBrush(wx.Brush(wx.Colour(178,  34,  34, 128)))   # 128 == half transparent
        for cnt in range(8):
            gc.Scale(1.08, 1.08)    # increase scale by 8%
            gc.Translate(5,5)     
            gc.DrawPath(path)


        gc.PopState()              # restore saved state
        gc.PushState()             # save it again
        gc.Translate(400, 200)
        gc.DrawText("Rotate", 0, -BASE2)

        # Move the origin over to the next location
        gc.Translate(0, 75)

        # draw our path again, rotating it about the central point,
        # and changing colors as we go
        for angle in range(0, 360, 30):
            gc.PushState()         # save this new current state so we can 
                                   # pop back to it at the end of the loop
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(float(angle)/360, 1, 1)]
            gc.SetBrush(wx.Brush(wx.Colour(r, g, b, 64)))
            gc.SetPen(wx.Pen(wx.Colour(r, g, b, 128)))
            
            # use translate to artfully reposition each drawn path
            gc.Translate(1.5 * BASE2 * cos(radians(angle)),
                         1.5 * BASE2 * sin(radians(angle)))

            # use Rotate to rotate the path
            gc.Rotate(radians(angle))

            # now draw it
            gc.DrawPath(path)
            gc.PopState()

        # Draw a bitmap with an alpha channel on top of the last group
        bmp = wx.Bitmap('toucan.png')
        bsz = bmp.GetSize()
        gc.DrawBitmap(bmp,
                      #-bsz.width, 
                      #-bsz.height/2,

                      -bsz.width/2.5, 
                      -bsz.height/2.5,
                      
                      bsz.width, bsz.height)


        gc.PopState()
        
def main():
    app = wx.App()
    TopFrame(None).Show()
    app.MainLoop()

if __name__ == '__main__':
    main()

