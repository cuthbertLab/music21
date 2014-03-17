# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         naturalLanguageObjects.py
# Purpose:      Multi-lingual conversion of pitch, etc. objects
# Authors:      David Perez
#
# Copyright:    Copyright © 2014 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

import unittest
from music21 import pitch

def toPitch(pitchString, languageString):
    '''
    Converts a string to a :class:`music21.pitch.Pitch` object given a language.
    
    Supported languages are German, French, Italian
    
    TODO: Fix
    
    >>> languageExcerpts.naturalLanguageObjects.toPitch("Es", "de")
    <music21.pitch.Pitch E->
    >>> languageExcerpts.naturalLanguageObjects.toPitch("H", "de")
    <music21.pitch.Pitch B>
    >>> for i in ['As','A','Ais']:
    ...     print languageExcerpts.naturalLanguageObjects.toPitch(i, "de")
    
    '''
    return pitch.Pitch('E-')


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------
# define presented order in documentation


_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
