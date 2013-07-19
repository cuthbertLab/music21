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


_DOC_IGNORE_MODULE_OR_PACKAGE = True


def processDocstring(app, what, name, obj, options, lines):
    '''Process the ``lines`` of each docstring, in place.'''
    #    print
    #    print 'WHAT ', what
    #    print 'NAME ', name
    #    print 'OBJ  ', obj
    #    print 'OPTS ', options
    #    print 'LINES', lines
    newLines = []
    for i, line in enumerate(lines):
        if ' #_DOCS_SHOW ' in line:
            newLines.append(line.replace(' #_DOCS_SHOW ', ' '))
        elif '#_DOCS_HIDE' in line:
            continue
        elif 'OMIT_FROM_DOCS' in line:
            break
        else:
            newLines.append(line)
    lines[:] = newLines


def setup(app):
    app.connect('autodoc-process-docstring', processDocstring)
    
