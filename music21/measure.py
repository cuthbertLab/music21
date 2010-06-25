#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         measure.py
# Purpose:      music21 classes for representing measurs
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest

import music21
from music21 import meter
from music21 import note
from music21 import musicxml
musicxmlMod = musicxml # alias as to avoid name conflicts


# TODO: it seems that this module might be better named bar

#-------------------------------------------------------------------------------
class Barline(music21.Music21Object):
    valid_styles = ["regular", "dotted", "dashed", "heavy", "light-light", "light-heavy", "heavy-light", "heavy-heavy", "tick", "short", "none"]
        #defined in MusicXML barline.dtd
    valid_repeats = ["right","left","both"]
    repeat_dots = None
    style = None
    pause = None  # can be music21.expressions.Fermata object
    
    def __init__(self, blStyle = None):
        if blStyle == "final":
            blStyle = "light-heavy"
        if blStyle == "double":
            blStyle = "light-light"
        
        if blStyle in self.valid_styles:
            self.style = blStyle
            

#-------------------------------------------------------------------------------
class Repeat(music21.Music21Object):
    '''The Repeat object defines a jump but not a change in barline style.  However
    the Measure object\'s addRepeat both adds a Repeat object and changes the appropriate
    Barline style.  So it is to be preferred.'''
    pass




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   


if __name__ == "__main__":
    music21.mainTest(Test)
