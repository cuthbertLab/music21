# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------


def processDocstring(app, what, name, obj, options, lines):
    '''Process the ``lines`` of each docstring in place.'''
    pass


def setup(app):
    app.connect('autodoc-process-docstring', processDocstring)
