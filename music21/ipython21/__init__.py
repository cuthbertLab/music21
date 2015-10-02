# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         ipython21/__init__.py
# Purpose:      music21 iPython Notebook support
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
iPython extension to music21.  In IPython Notebook call:

   %load_ext music21.ipython21
   
and show will take place inside the browser
'''
__all__ = ['ipExtension', 'objects']

from music21.ipython21 import ipExtension
from music21.ipython21 import objects
from music21.ipython21.ipExtension import load_ipython_extension

from music21 import common
localIP = None

def loadNoMagic():
    if common.runningUnderIPython():
        from IPython.core.interactiveshell import InteractiveShell
        if InteractiveShell.initialized():        
            localIP = InteractiveShell.instance()    
            load_ipython_extension(localIP)
            
if common.runningUnderIPython(): # @UndefinedVariable
    from threading import Timer
    t = Timer(0.5, loadNoMagic)
    t.start()
    #ipython21.load_no_magic() # @UndefinedVariable
