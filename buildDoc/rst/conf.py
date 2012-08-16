# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         conf.py
# Purpose:      Documentation configuration file
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2010, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

import sys, os
import unittest, doctest
import music21


# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'contents'

try:
    import rst2pdf
    extensions = ['rst2pdf.pdfbuilder']
except ImportError:
    extensions = []


# extensions.append('sphinx.ext.inheritance_diagram')
# 
# inheritance_graph_attrs = dict(rankdir="TB", fontsize=6, nodesep=0.2, ranksep=0.2)
# 
# inheritance_node_attrs = dict(fontsize=8, style='"filled"', color='"#666666"', fillcolor='"#605C7F"', fontcolor='"#ffffff"', height=.25, width=2)
# 
# inheritance_edge_attrs = dict(dir="back", arrowhead="none", arrowtail="empty", arrowsize=0.7, color='"#666666"')


# General substitutions.
project = 'music21'
release = music21.VERSION_STR
copyright = 'Copyright &copy; 2009-2012, Michael Scott Cuthbert and the music21 Project'


html_last_updated_fmt = '%b %d, %Y'

# Content template for the index page.
html_index = 'index.html'

html_theme = 'music21doc'
html_theme_path = ["."] # search for theme in this dir


html_title = 'music21 Documentation'
html_short_title = 'music21'
html_sidebars = {'**': ['relations.html', 'localtoc.html', 'globaltoc.html',  'searchbox.html']}
html_show_sourcelink = False

html_theme_options = {
    }


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

