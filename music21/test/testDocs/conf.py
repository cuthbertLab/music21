#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         testConf.py
# Purpose:      A simple configuration used only for testing select doc files. 
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import sys, os
import unittest, doctest
import music21


# The suffix of source filenames.
source_suffix = '.rst'
extensions = []
extensions.append('sphinx.ext.doctest')

# General substitutions.
project = 'music21'
release = music21.VERSION_STR
copyright = '2009-2011 The music21 Project'

html_last_updated_fmt = '%b %d, %Y'
html_title = 'music21 Documentation'
html_short_title = 'music21'

def _shell():
    '''
    >>> True
    True
    '''
    pass




