# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         ipython21/__init__.py
# Purpose:      music21 Jupyter Notebook support
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-23 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
IPython/Jupyter extension to music21.  In Jupyter Notebook call:

   %load_ext music21.ipython21

and show will take place inside the browser.

Since at least music21 v5, however, when music21 is imported we set a timer
for two seconds to everything to settle and then load our extension (which
now just calls matplotlib inline)
'''
from __future__ import annotations

__all__ = ['converters', 'ipExtension', 'objects',
           'loadNoMagic', 'load_ipython_extension']

from music21 import common

from music21.ipython21 import converters
from music21.ipython21 import ipExtension
from music21.ipython21 import objects
from music21.ipython21.ipExtension import load_ipython_extension

def loadNoMagic():
    '''
    Load the magic functions of load_ipython_extension when running IPython
    without needing to call a %magic function
    '''
    if common.runningInNotebook():
        # noinspection PyPackageRequirements
        from IPython.core.interactiveshell import InteractiveShell  # type: ignore
        if InteractiveShell.initialized():
            localIP = InteractiveShell.instance()
            load_ipython_extension(localIP)


# if we are imported in a Jupyter environment, then load magic after a second
# so that everything can settle.
if common.runningInNotebook():
    from threading import Timer
    t = Timer(1, loadNoMagic)
    t.start()
