# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         object.py
# Purpose:      music21 classes for indicating Braille formatting, etc.
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

from __future__ import division, print_function

import unittest

from music21.base import Music21Object

class BrailleSegmentDivision(Music21Object):
    '''
    Represents that a segment must divide at this point.
    
    >>> bsd = braille.objects.BrailleSegmentDivision()
    >>> bsd
    <music21.braille.objects.BrailleSegmentDivision object at 0x10afc1a58>
    '''

class BrailleOptionalSegmentDivision(BrailleSegmentDivision):
    '''
    Represents that a segment might divide at this point.

    >>> bosd = braille.objects.BrailleOptionalSegmentDivision()
    >>> bosd
    <music21.braille.objects.BrailleOptionalSegmentDivision object at 0x10afc1b38>
    '''

class BrailleOptionalNoteDivision(Music21Object):
    '''
    Represents the best place in a measure to divide notes
    if the measure needs to be divided.

    >>> bond = braille.objects.BrailleOptionalNoteDivision()
    >>> bond
    <music21.braille.objects.BrailleOptionalNoteDivision object at 0x10afc19b0>
    '''

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
