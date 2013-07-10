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

import os
import sphinx
import sys
import webbrowser


def _main(buildFormat):
    from music21 import documentation
    documentationDirectoryPath = documentation.__path__[0]
    sourceDirectoryPath = os.path.join(
        documentationDirectoryPath,
        'source',
        )
    buildDirectoryPath = os.path.join(
        documentationDirectoryPath,
        'build',
        )
    doctreesDirectoryPath = os.path.join(
        buildDirectoryPath,
        'doctrees',
        )
    buildDirectories = {
        'html': os.path.join(
            buildDirectoryPath,
            'html',
            ),
        'latex': os.path.join(
            buildDirectoryPath,
            'latex',
            ),
        'latexpdf': os.path.join(
            buildDirectoryPath,
            'latex',
            ),
    }
    documentation.ModuleReferenceReSTWriter()()
    documentation.CorpusReferenceReSTWriter()()
    documentation.IPythonNotebookReSTWriter()()
    sphinxOptions = ['sphinx']
    sphinxOptions.extend(('-b', buildFormat))
    sphinxOptions.extend(('-d', doctreesDirectoryPath))
    sphinxOptions.append(sourceDirectoryPath)
    sphinxOptions.append(buildDirectories[buildFormat])
    sphinx.main(sphinxOptions)
    if buildFormat == 'html':
        launchPath = os.path.join(
            buildDirectories[buildFormat],
            'index.html',
            )
        # TODO: test launching on Windows; what is the path like there?
        if launchPath.startswith('/'):
            launchPath = 'file://' + launchPath
        webbrowser.open(launchPath)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        buildFormat = sys.argv[1]
    else:
        buildFormat = 'html'
    _main(buildFormat)
