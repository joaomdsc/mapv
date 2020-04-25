# model.py - model (as in MVC) for DLG-3 map viewer

import os
import wx
from pubsub import pub
from dlg import load_data

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
# DlgModel - 
#-------------------------------------------------------------------------------

class DlgModel:
    def __init__(self):
        self.dlg = None

    def dlg_open(self, filepath):
        # Perform the requested action
        self.dlg = load_data(filepath)

        # Publish a data message
        topic = 'model_updates'
        # print(f'Sending on topic: {topic}')
        pub.sendMessage(topic, arg=self.dlg)

#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    print('This module is not meant to be executed directly.')