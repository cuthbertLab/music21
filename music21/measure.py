#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         measure.py
# Purpose:      music21 classes for representing measurs
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest


import music21

from music21 import meter
from music21 import note
from music21 import musicxml
musicxmlMod = musicxml # alias as to avoid name conflicts


# TODO: it seems that this module might be better named bar
# as it defines measure attributes and not Measures

#-------------------------------------------------------------------------------
class Barline(music21.Music21Object):
    valid_styles = ["regular", "dotted", "dashed", "heavy", "light-light", "light-heavy",
                    "heavy-light", "heavy-heavy", "tick", "short", "none"]
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
# this is now defined n Stream.

# class Part(object):
#     '''Terminal, non stream representation of a Part. Does not contain
#     notes, measures, Streams, ora ny other attributes that will occur 
#     more than once. 
# 
#     Should be able ot represent MusicXML Parts and PartGroups?
# 
#         self.groupName = None
#         self.groupAbbreviaton = None
#         self.groupBarline = None
# 
#     '''
#     
#     def __init__(self):
# 
#         # should be .name
#         self.partName = None
#         self.partAbbreviation = None
# 
# 
#     def _getMX(self):
#         '''
#         Returns an incomplete mxSorePart object
#         '''
#         mxScorePart = musicxmlMod.ScorePart()
#         mxScorePart.set('partName', self.partName)
#         mxScorePart.set('partAbbreviation', self.partAbbreviation)
#         return mxScorePart
# 
#     def _setMX(self, mxNote):
#         '''
#         Given a lost of one or more MusicXML Note objects, read in and create
#         Duration
# 
#         '''
#         pass
# 
#     mx = property(_getMX, _setMX)
# 
# 








#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
   


if __name__ == "__main__":
    music21.mainTest(Test)
