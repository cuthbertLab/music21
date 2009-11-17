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

from music21 import common
from music21 import musicxml
from music21.lily import LilyString



class ClefException(Exception):
    pass


#-------------------------------------------------------------------------------
class Clef(music21.Music21Object):
    def __init__(self):
        music21.Music21Object.__init__(self)
        self.sign = None
        self.line = None

        # mxl has an attribute forr clefOctaveChange, and integer to show 
        # transposing clefs

    def _getMX(self):
        '''
        This might be mobed only into PitchClef.

        >>> b = GClef()
        >>> a = b.mx
        >>> a.get('sign')
        'G'
        '''

        mxClef = musicxml.Clef()
        mxClef.set('sign', self.sign)
        mxClef.set('line', self.line)
        return mxClef

    def _setMX(self, mxClefList):
        '''
        This might be mobed only into PitchClef.

        >>> a = musicxml.Clef()   
        >>> a.set('sign', 'G')
        >>> a.set('line', 2)
        >>> b = Clef()
        >>> b.mx = a
        >>> b.sign
        'G'
        '''
        if not common.isListLike(mxClefList):
            mxClef = mxClefList # its not a list
        else: # just get first for now
            mxClef = mxClefList[0]

        # this is not trying to load special clef classes below
        self.sign = mxClef.get('sign')
        self.line = mxClef.get('line')

    mx = property(_getMX, _setMX)


class PercussionClef(Clef):
    pass

class NoClef(Clef):
    pass


class PitchClef(Clef):

    def __init__(self):
        Clef.__init__(self)
        self.lilyName = ""

    
    def _getLily(self):
        return LilyString("\\clef \"" + self.lilyName + "\" ")

    lily = property(_getLily)


#-------------------------------------------------------------------------------
class GClef(PitchClef):
    def __init__(self):
        '''
        >>> a = GClef()
        >>> a.sign
        'G'
        '''
        PitchClef.__init__(self)
        self.sign = "G"


class FrenchViolinClef(GClef):
    def __init__(self):
        '''
        >>> a = FrenchViolinClef()
        >>> a.sign
        'G'
        '''
        GClef.__init__(self)
        self.line = 1
        self.lowestLine = (7*4) + 5

class TrebleClef(GClef):
    def __init__(self):
        '''
        >>> a = TrebleClef()
        >>> a.sign
        'G'
        '''
        GClef.__init__(self)
        self.lilyName = "treble"
        self.line = 2
        self.lowestLine = (7*4) + 3  # 4 octaves + 3 notes = e4

class Treble8vbClef(TrebleClef):
    def __init__(self):
        '''
        >>> a = Treble8vbClef()
        >>> a.sign
        'G'
        '''
        TrebleClef.__init__(self)
        self.lilyName = "treble_8"
        self.clefOctaveChange = -1
        self.lowestLine = (7*3) + 3

class GSopranoClef(GClef):
    def __init__(self):
        '''
        >>> a = GSopranoClef()
        >>> a.sign
        'G'
        '''
        GClef.__init__(self)
        self.line = 3
        self.lowestLine = (7*4) + 1

#-------------------------------------------------------------------------------
class CClef(PitchClef):
    def __init__(self):
        '''
        >>> a = CClef()
        >>> a.sign
        'C'
        '''
        PitchClef.__init__(self)
        self.sign = "C"
    
class SopranoClef(CClef):
    def __init__(self):
        '''
        >>> a = SopranoClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 1
        self.lowestLine = (7*4) + 1

class MezzoSopranoClef(CClef):
    def __init__(self):
        '''
        >>> a = MezzoSopranoClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 2
        self.lowestLine = (7*3) + 6
    
class AltoClef(CClef):
    def __init__(self):
        '''
        >>> a = AltoClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 3
        self.lowestLine = (7*3) + 4

class TenorClef(CClef):
    def __init__(self):
        '''
        >>> a = TenorClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 4
        self.lowestLine = (7*3) + 2

class CBaritoneClef(CClef):
    def __init__(self):
        '''
        >>> a = CBaritoneClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 5
        self.lowestLine = (7*2) + 7


#-------------------------------------------------------------------------------
class FClef(PitchClef):
    def __init__(self):
        '''
        >>> a = FClef()
        >>> a.sign
        'F'
        '''
        PitchClef.__init__(self)
        self.sign = "F"

class FBaritoneClef(FClef):
    def __init__(self):
        '''
        >>> a = FBaritoneClef()
        >>> a.sign
        'F'
        '''
        FClef.__init__(self)
        self.line = 3
        self.lowestLine = (7*2) + 7

class BassClef(FClef):
    def __init__(self):
        '''
        >>> a = BassClef()
        >>> a.sign
        'F'
        '''
        FClef.__init__(self)
        self.lilyName = "bass"
        self.line = 4
        self.lowestLine = (7*2) + 5

class SubBassClef(FClef):
    def __init__(self):
        '''
        >>> a = SubBassClef()
        >>> a.sign
        'F'
        '''
        FClef.__init__(self)
        self.line = 5
        self.lowestLine = (7*2) + 3




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



