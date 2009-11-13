#-------------------------------------------------------------------------------
# Name:         clef.py
# Purpose:      Objects for representing clefs
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import unittest

import music21

from music21 import musicxml
from music21.lily import LilyString



class ClefException(Exception):
    pass


#-------------------------------------------------------------------------------
class Clef(music21.Music21Object):

    def _getMX(self):
        mxClef = musicxml.Clef()
        mxClef.set('sign', self.sign)
        mxClef.set('line', self.line)
        return mxClef

    mx = property(_getMX)


class PercussionClef(Clef):
    pass

class NoClef(Clef):
    pass


class PitchClef(Clef):
    lilyName = ""

    def _getLily(self):
        return LilyString("\\clef \"" + self.lilyName + "\" ")

    lily = property(_getLily)


#-------------------------------------------------------------------------------
class GClef(PitchClef):
    sign = "G"

class FrenchViolinClef(GClef):
    line = 1
    lowestLine = (7*4) + 5

class TrebleClef(GClef):
    lilyName = "treble"
    line = 2
    lowestLine = (7*4) + 3  # 4 octaves + 3 notes = e4

class Treble8vbClef(TrebleClef):
    lilyName = "treble_8"
    clefOctaveChange = -1
    lowestLine = (7*3) + 3

class GSopranoClef(GClef):
    line = 3
    lowestLine = (7*4) + 1

class CClef(PitchClef):
    sign = "C"
    
class SopranoClef(CClef):
    line = 1
    lowestLine = (7*4) + 1

class MezzoSopranoClef(CClef):
    line = 2
    lowestLine = (7*3) + 6
    
class AltoClef(CClef):
    line = 3
    lowestLine = (7*3) + 4

class TenorClef(CClef):
    line = 4
    lowestLine = (7*3) + 2

class CBaritoneClef(CClef):
    line = 5
    lowestLine = (7*2) + 7


#-------------------------------------------------------------------------------
class FClef(PitchClef):
    sign = "F"

class FBaritoneClef(FClef):
    line = 3
    lowestLine = (7*2) + 7

class BassClef(FClef):
    lilyName = "bass"
    line = 4
    lowestLine = (7*2) + 5

class SubBassClef(FClef):
    line = 5
    lowestLine = (7*2) + 3




#-------------------------------------------------------------------------------
CLASS_FROM_TYPE = {
    "G": [None, FrenchViolinClef, TrebleClef, GSopranoClef, None, None],
    "C": [None, SopranoClef, MezzoSopranoClef, AltoClef, TenorClef, CBaritoneClef],
    "F": [None, None, None, FBaritoneClef, BassClef, SubBassClef]
    }


def standardClefFromXN(xnStr):
    '''
    Returns a Clef object given a string like "G2" or "F4" etc.
    '''
    
    (thisType, lineNum) = (xnStr[0], xnStr[1])
    if thisType is False or lineNum is False:
        raise ClefException("can't read %s as clef str, should be G2, F4, etc.", xnStr)
    lineNum = int(lineNum)
    if lineNum < 1 or lineNum > 5:
        raise ClefException("line number (second character) must be 1-5;" + 
                            "do not use this function for clefs on special staves: %s", xnStr)
    if thisType not in CLASS_FROM_TYPE:
        raise ClefException("cannot use type %s as a clef type, try G, C, or F", xnStr)
    if CLASS_FROM_TYPE[thisType][lineNum] is None:
        return None
    else:
        return CLASS_FROM_TYPE[thisType][lineNum]()
        




class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testConversionMX(self):
        for clefObjName in [FrenchViolinClef, TrebleClef, Treble8vbClef, 
                GSopranoClef, SopranoClef, MezzoSopranoClef,
                TenorClef, CBaritoneClef, FBaritoneClef, BassClef, 
                SubBassClef]:
            a = clefObjName()
            mxClef = a.mx


if __name__ == "__main__":
    music21.mainTest(Test)



