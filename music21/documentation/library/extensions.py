# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         convertIPythonNotebooksToReST.py
# Purpose:      music21 documentation IPython notebook to ReST converter
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------


def processDocstring(app, what, name, obj, options, lines):
    '''Process the ``lines`` of each docstring, in place.'''
    print
    print 'WHAT ', what
    print 'NAME ', name
    print 'OBJ  ', obj
    print 'OPTS ', options
    print 'LINES', lines
    for i, line in enumerate(lines):
        if 'OMIT_FROM_DOCS' in line:
            lines[i:] = []
            break


def setup(app):
    app.connect('autodoc-process-docstring', processDocstring)
