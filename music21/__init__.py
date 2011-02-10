#!/usr/bin/python

'''
The music21 Framework is Copyright (c) 2008-10 music21 lab 
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


# this defines what  is loaded when importing __all__
# put these in alphabetical order FIRST dirs then modules
# but: base must come first; in some cases other modules depend on 
# definitions in base

__all__ = ['base', 

           # sub folders
           'abc', 'abj', 'analysis', 'composition', 'counterpoint', 'corpus', 
           'demos', 'doc', 'figuredBass', 'humdrum', 
           'lily', 'musicxml', 'romanText', 'test', 'trecento', 'midi', 
           
           # individual modules
           'articulations', 'bar',
           'chord', 'chordTables', 'clef','common', 'converter',
           'defaults', 'duration', 'dynamics',
           'editorial', 'environment', 
           'graph', 
           'interval', 'intervalNetwork', 'instrument', 'key', 'layout',
           'metadata', 'meter', 'musedata', 
           'expressions', 'note', 
           'pitch', 'ratios', 'roman',
           'spanner', 'scale', 'serial', 'sieve', 'stream', 
           'tempo', 'text', 'tie', 'tinyNotation', 
           'voiceLeading']


#print __all__
# skipped purposely, "base", "node"

#-------------------------------------------------------------------------------
# for sub packages, need to manually add the modules in these subpackages
#from music21.analysis import *


#-------------------------------------------------------------------------------
# base Music21Object -- all objects should inherit from this!
import base
from base import *

#-------------------------------------------------------------------------------
# place the parse function directly in the music21 namespace
# this cannot go in music21/base.py

import converter
parse = converter.parse


#------------------------------------------------------------------------------
# this bring all of the __all__ names into the music21 package namespace
from music21 import *

#------------------------------------------------------------------------------
# eof


