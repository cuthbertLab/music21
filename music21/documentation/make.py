#! /usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         documentation/make.py
# Purpose:      music21 documentation script, v. 2.0
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

import os
import sys
import webbrowser

try:
    import sphinx
except ImportError:
    raise ImportError("Sphinx is required to build documentation; download from http://sphinx-doc.org")

def _main(target):
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
    sphinxOptions.extend(('-b', target))
    sphinxOptions.extend(('-d', doctreesDirectoryPath))
    sphinxOptions.append(sourceDirectoryPath)
    sphinxOptions.append(buildDirectories[target])
    sphinx.main(sphinxOptions)
    if target == 'html':
        launchPath = os.path.join(
            buildDirectories[target],
            'index.html',
            )
        # TODO: test launching on Windows; what is the path like there?
        if launchPath.startswith('/'):
            launchPath = 'file://' + launchPath
        webbrowser.open(launchPath)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = 'html'
    _main(target)
