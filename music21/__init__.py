#!/usr/bin/python

'''
The music21 Framework is Copyright (c) 2008-10 music21lab 
(Michael Scott Cuthbert, principal investigator; cuthbert@mit.edu)

Some Rights Reserved
Released under the LGPL license

Roughly speaking, this means that anyone can use this software for
free, they can distribute it to anyone, so long as this acknowledgment
of copyright and ownership remain publicly accessible.  You may also
modify this software or use it in your own programs so long as you do
not sell your product and so long as you make your product available
under the same license.  You may also link to this code as a library
from your commercial product so long as this code remains open and
accessible, this license is made accessible, and the developers are
credited.

The development of music21 was supported by a grant
from the Seaver Institute and with the support of the MIT
Music and Theater Arts section and the School of Humanities, Arts,
and Social Sciences. 

music21 outputs a subset of XML data defined by the  MusicXML 2.0 
standard, &copy; Recordare LLC;  License available at
http://www.recordare.com/dtds/license.html

music21 incorporates Microsoft Excel reading via the included 
xlrd library:
   Portions copyright (c) 2005-2006, Stephen John Machin, Lingfo Pty Ltd
   All rights reserved.
see trecento/xlrd/licenses.py for the complete disclaimer and conditions

'''

# put these in alphabetical order FIRST dirs then modules
__all__ = ["analysis", "composition", "counterpoint", "corpus", \
           "demos", "doc", "humdrum", \
           "lily", "musicxml", "test", "trecento", \
           \
           "articulations", \
           "chord", "chordTables", "clef","common", "converter", \
           "defaults", "duration", "dynamics",\
           "editorial","enharmonic", "environment", \
           "graph", \
           "interval", "instrument", "key", \
           "measure", "meter", \
           "expressions", "note", \
           "pitch", "ratios", \
           "scale", "serial", "stream", 
           "tempo", "text", "tinyNotation", \
           "voiceLeading"]

# skipped purposely, "base", "node"

#-------------------------------------------------------------------------------
# base Music21Object -- all objects should inherit from this!
import base
from base import *

#-------------------------------------------------------------------------------
# place the parse function directly in the music21 namespace
# this cannot go in music21/base.py

import converter
parse = converter.parse
