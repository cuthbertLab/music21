#! /usr/bin/env python
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


def _main():
    from music21 import documentation
    documentation.ModuleReferenceReSTWriter()()
    documentation.CorpusReferenceReSTWriter()()
    documentation.IPythonNotebookReSTWriter()()


if __name__ == '__main__':
    _main()
