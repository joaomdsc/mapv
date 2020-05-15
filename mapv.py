# mapv.py - map viewer

import os
import wx
from ui import DlgFrame
      
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

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    arg = None
    if len(sys.argv) == 2:
        arg = sys.argv[1]

    app = wx.App()
    if arg is None:
        DlgFrame()
    elif os.path.isfile(arg):
        DlgFrame(filepath=arg)
    else:
        DlgFrame(mapname=arg)
    app.MainLoop()
