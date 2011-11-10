#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         testConf.py
# Purpose:      Documentation configuration file
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

# The master toctree document.
# master_doc = 'contents'


extensions = []
extensions.append('sphinx.ext.doctest')


# General substitutions.
project = 'music21'
release = music21.VERSION_STR
copyright = '2009-2011 The music21 Project'


html_last_updated_fmt = '%b %d, %Y'

html_title = 'music21 Documentation'
html_short_title = 'music21'

# html_sidebars = {'**': ['relations.html', 'localtoc.html', 'globaltoc.html',  'searchbox.html']}
# html_show_sourcelink = False


def _shell():
    '''
    >>> True
    True
    '''
    pass





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def setUp(self):
        pass

    def testToRoman(self):
        self.assertEqual(True, True)



if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

