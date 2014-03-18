# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         naturalLanguageObjects.py
# Purpose:      Multi-lingual conversion of pitch, etc. objects
# Authors:      David Perez
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
r'''
Module docs...
'''

import unittest
from music21 import pitch

def toPitch(pitchString, languageString):
    '''
    Converts a string to a :class:`music21.pitch.Pitch` object given a language.
    
    Supported languages are German, French, Italian
    
    TODO: Fix
    
    >>> languageExcerpts.naturalLanguageObjects.toPitch("Es", "de")
    <music21.pitch.Pitch E->
    
    
    Commented out until works...
    
    #>>> languageExcerpts.naturalLanguageObjects.toPitch("H", "de")
    #<music21.pitch.Pitch B>
    #>>> for i in ['As','A','Ais']:
    #...     print languageExcerpts.naturalLanguageObjects.toPitch(i, "de")
    
    '''    
    return pitch.Pitch('E-')

def toNote():
    pass

def toChord():
    pass

def toDuration():
    pass
#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testConvertGerman(self):
        self.assertEquals(1, 1)


#------------------------------------------------------------------------------
# define presented order in documentation


_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
