# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         ipython21/__init__.py
# Purpose:      music21 iPython Notebook support
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
iPython extension to music21.  In IPython Notebook call:

   %load_ext music21.ipython21

and show will take place inside the browser
'''
__all__ = ['ipExtension', 'objects', 'loadNoMagic', 'load_ipython_extension']

from music21.ipython21 import ipExtension
from music21.ipython21 import objects
from music21.ipython21.ipExtension import load_ipython_extension

from music21 import common

def loadNoMagic():
    '''
    Load the magic functions when running iPython
    '''
    if common.runningUnderIPython():
        # noinspection PyPackageRequirements
        from IPython.core.interactiveshell import InteractiveShell
        if InteractiveShell.initialized():
            localIP = InteractiveShell.instance()
            load_ipython_extension(localIP)


# if we are imported in an IPython environment, then load magic after half a second
if common.runningUnderIPython():  # @UndefinedVariable
    from threading import Timer
    t = Timer(2, loadNoMagic)
    t.start()
    # ipython21.load_no_magic() # @UndefinedVariable
