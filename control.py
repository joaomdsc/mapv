# mapv.py - controller (as in MVC) for map viewer

import os
import wx
from pubsub import pub
from model import DlgModel
from view import DlgView
      
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
# Controller - 
#-------------------------------------------------------------------------------

class Controller:
    def __init__(self, filepath=None):
        self.model = DlgModel()
        
        pub.subscribe(self.handle_request, 'view_requests')
        self.view = DlgView(filepath)
        self.view.Show()

    def handle_request(self, arg):
        filepath = arg
        self.model.dlg_open(filepath)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    filepath = None
    if len(sys.argv) == 2:
        filepath = sys.argv[1]
        
    app = wx.App()
    c = Controller(filepath=filepath)
    app.MainLoop()
