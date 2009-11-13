#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         notationMod.py
# Purpose:      notation mods
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import doctest, unittest

import music21
import music21.interval

from music21 import musicxml


_MOD = 'notationMod'



class Ornament(music21.Music21Object):
    connectedToPrevious = True  # should follow directly on previous; true for most "ornaments".

class GeneralMordent(Ornament):
    direction = ""  # up or down
    size = None # music21.interval.Interval (General, etc.) class

class Mordent(GeneralMordent):
    direction = "down"

class HalfStepMordent(Mordent):
    def __init__(self):
        self.size = music21.interval.generateIntervalFromString("m2")

class WholeStepMordent(Mordent):
    def __init__(self):
        self.size = music21.interval.generateIntervalFromString("M2")

class InvertedMordent(GeneralMordent):
    direction = "up"

class HalfStepInvertedMordent(InvertedMordent):
    def __init__(self):
        self.size = music21.interval.generateIntervalFromString("m2")

class WholeStepInvertedMordent(InvertedMordent):
    def __init__(self):
        self.size = music21.interval.generateIntervalFromString("M2")

class Trill(Ornament):
    size = None
    placement = None

    def _getMX(self):
        '''
        returns a musicxml.DynamicMark object
        >>> a = Trill()
        >>> a.placement = 'above'
        >>> mxTrillMark = a.mx
        >>> mxTrillMark.get('placement')
        'above'
        '''
        mxTrillMark = musicxml.TrillMark()
        mxTrillMark.set('placement', self.placement)
        return mxTrillMark


    def _setMX(self, mxTrillMark):
        '''
        given an mxDynamicMark, load instance

        >>> mxTrillMark = musicxml.TrillMark()
        >>> mxTrillMark.set('placement', 'above')
        >>> a = Trill()
        >>> a.mx = mxTrillMark
        >>> a.placement
        'above'
        '''
        self.placement = mxTrillMark.get('placement')

    mx = property(_getMX, _setMX)




class HalfStepTrill(Trill):
    def __init__(self):
        self.size = music21.interval.generateIntervalFromString("m2")

class WholeStepTrill(Trill):
    def __init__(self):
        self.size = music21.interval.generateIntervalFromString("M2")

class Turn(Ornament):
    pass

class InvertedTurn(Ornament):
    pass

class Fermata(music21.Music21Object):
    shape = "normal"
    type  = ""
    lily  = "\\fermata"







#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testBasic(self):
        pass


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testBasic(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)