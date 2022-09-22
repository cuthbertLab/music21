# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         ipython21/__init__.py
# Purpose:      music21 IPython Notebook support
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
IPython extension to music21.  In Jupyter Notebook call:

   %load_ext music21.ipython21

and show will take place inside the browser.  But currently not needed.
'''
__all__ = ['ipExtension', 'objects', 'loadNoMagic', 'load_ipython_extension']

from music21.ipython21 import ipExtension
from music21.ipython21 import objects
from music21.ipython21.ipExtension import load_ipython_extension

from music21 import common

def loadNoMagic():
    '''
    Load the magic functions of load_ipython_extension when running IPython
    '''
    if common.runningUnderIPython():
        # noinspection PyPackageRequirements
        from IPython.core.interactiveshell import InteractiveShell  # type: ignore
        if InteractiveShell.initialized():
            localIP = InteractiveShell.instance()
            load_ipython_extension(localIP)


def inGoogleColabNotebook():
    if not common.runningUnderIPython():
        return False
    try:
        # get_ipython is loaded into global scope in IPython and Google Colab
        # because we already returned False above, the NameError should never
        # be triggered, but better safe than sorry.  And helps type checkers.
        return get_ipython().__class__.__module__ == 'google.colab._shell'
    except NameError:
        return False


# if we are imported in an IPython environment, then load magic after two seconds
if common.runningUnderIPython():
    from threading import Timer
    t = Timer(2, loadNoMagic)
    t.start()
    # ipython21.load_no_magic()
