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

from music21 import environment
_MOD = "clef.py"
environLocal = environment.Environment(_MOD)


class ClefException(Exception):
    pass



# TODO: should lilyName, here and elsewhere, be a private variable, _lilyName?

#-------------------------------------------------------------------------------
class Clef(music21.Music21Object):
    def __init__(self):
        music21.Music21Object.__init__(self)
        self.sign = None
        self.line = None
        self.octaveChange = 0 # set to zero as default

        # mxl has an attribute forr clefOctaveChange, and integer to show 
        # transposing clefs

    def _getMX(self):
        '''Given a music21 Clef object, return a MusicXML Clef object.

        This might be moved only into PitchClef.

        >>> b = GClef()
        >>> a = b.mx
        >>> a.get('sign')
        'G'

        >>> b = Treble8vbClef()
        >>> b.octaveChange
        -1
        >>> a = b.mx
        >>> a.get('sign')
        'G'
        >>> a.get('clefOctaveChange')
        -1
        '''

        mxClef = musicxml.Clef()
        mxClef.set('sign', self.sign)
        mxClef.set('line', self.line)
        if self.octaveChange != 0:
            mxClef.set('clefOctaveChange', self.octaveChange)
        return mxClef

    def _setMX(self, mxClefList):
        '''Given a MusicXML Clef object, return a music21 Clef object

        This might be moved only into PitchClef.

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
        if self.sign in ['TAB', 'percussion', 'none']:
            if self.sign == 'TAB':
                self.__class__ = TabClef
            elif self.sign == 'percussion':
                self.__class__ = PercussionClef
            elif self.sign == 'none':
                self.__class__ = NoClef

        else:
            self.line = int(mxClef.get('line'))
            mxOctaveChange = mxClef.get('clefOctaveChange')
            if mxOctaveChange != None:
                self.octaveChange = int(mxOctaveChange)
    
            # specialize class based on sign, line, ocatve
            params = (self.sign, self.line, self.octaveChange)
            if params == ('G', 1, 0):
                self.__class__ = FrenchViolinClef
            elif params == ('G', 2, 0):
                self.__class__ = TrebleClef
            elif params == ('G', 2, -1):
                self.__class__ = Treble8vbClef
            elif params == ('G', 2, 1):
                self.__class__ = Treble8vaClef
            elif params == ('G', 3, 0):
                self.__class__ = GSopranoClef
            elif params == ('C', 1, 0):
                self.__class__ = SopranoClef
            elif params == ('C', 2, 0):
                self.__class__ = MezzoSopranoClef
            elif params == ('C', 3, 0):
                self.__class__ = AltoClef
            elif params == ('C', 4, 0):
                self.__class__ = TenorClef
            elif params == ('C', 5, 0):
                self.__class__ = CBaritoneClef
            elif params == ('F', 3, 0):
                self.__class__ = FBaritoneClef
            elif params == ('F', 4, 0):
                self.__class__ = BassClef
            elif params == ('F', 4, -1):
                self.__class__ = Bass8vbClef
            elif params == ('F', 4, 1):
                self.__class__ = Bass8vaClef
            elif params == ('F', 5, 0):
                self.__class__ = SubBassClef
            else:
                raise ClefException('cannot match clef parameters (%s/%s/%s) to a Clef subclass' % (params[0], params[1], params[2]))

    mx = property(_getMX, _setMX)


class PercussionClef(Clef):
    pass

class NoClef(Clef):
    pass

class TabClef(Clef):
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
        self.lowestLine = None

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
        >>> a.octaveChange
        -1
        '''
        TrebleClef.__init__(self)
        self.lilyName = "treble_8"
        self.octaveChange = -1
        self.lowestLine = (7*3) + 3

class Treble8vaClef(TrebleClef):
    def __init__(self):
        '''
        >>> a = Treble8vaClef()
        >>> a.sign
        'G'
        >>> a.octaveChange
        1
        '''
        TrebleClef.__init__(self)
        self.octaveChange = 1
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
        self.lowestLine = None

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
        >>> a.line
        4
        
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
        >>> a.line
        5
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
        self.lowestLine = None

class FBaritoneClef(FClef):
    def __init__(self):
        '''
        >>> a = FBaritoneClef()
        >>> a.sign
        'F'
        >>> a.line
        3
        >>> b = CBaritoneClef()
        >>> a.lowestLine == b.lowestLine
        True
        >>> a.sign == b.sign
        False
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

class Bass8vbClef(FClef):
    def __init__(self):
        '''
        >>> a = Bass8vbClef()
        >>> a.sign
        'F'
        >>> a.octaveChange
        -1
        '''
        FClef.__init__(self)
        self.line = 4
        self.octaveChange = -1
        self.lowestLine = (7*2) + 5

class Bass8vaClef(FClef):
    def __init__(self):
        '''
        >>> a = Bass8vaClef()
        >>> a.sign
        'F'
        '''
        FClef.__init__(self)
        self.line = 4
        self.octaveChange = 1
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
        


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

    def testConversionMX(self):
        # test basic creation
        for clefObjName in [FrenchViolinClef, TrebleClef, Treble8vbClef, 
                GSopranoClef, SopranoClef, MezzoSopranoClef,
                TenorClef, CBaritoneClef, FBaritoneClef, BassClef, 
                SubBassClef]:
            a = clefObjName()
            mxClef = a.mx

        # test specific clefs
        a = Treble8vbClef()
        mxClef = a.mx
        self.assertEqual(mxClef.get('clefOctaveChange'), -1)

    def testConversionClassMatch(self):

        src = [
            [('G', 1, 0), FrenchViolinClef],
            [('G', 2, 0), TrebleClef],
            [('G', 2, -1), Treble8vbClef],
            [('G', 2, 1), Treble8vaClef],
            [('G', 3, 0), GSopranoClef],
            [('C', 1, 0), SopranoClef],
            [('C', 2, 0), MezzoSopranoClef],
            [('C', 3, 0), AltoClef],
            [('C', 4, 0), TenorClef],
            [('C', 5, 0), CBaritoneClef],
            [('F', 3, 0), FBaritoneClef],
            [('F', 4, 0), BassClef],
            [('F', 4, 1), Bass8vaClef],
            [('F', 4, -1), Bass8vbClef],
            [('F', 5, 0), SubBassClef]
        ]

        for params, className in src:
            mxClef = musicxml.Clef()
            mxClef.set('sign', params[0])
            mxClef.set('line', params[1])
            mxClef.set('octaveChange', params[2])

            c = Clef()
            c.mx = mxClef

            #environLocal.printDebug([type(c).__name__])

            self.assertEqual(c.sign, params[0])
            self.assertEqual(c.line, params[1])
            self.assertEqual(c.octaveChange, params[2])
            self.assertEqual(isinstance(c, className), True)

    def xtestContexts(self):
        from music21 import stream
        from music21 import note
        from music21 import meter
        
        n1 = note.Note("C")
        n1.offset = 10
        c1 = AltoClef()
        c1.offset = 0
        s1 = stream.Stream([c1, n1])
        
        self.assertTrue(s1.getContextByClass(Clef) is c1)
           ## equally good: getContextsByClass(Clef)[0]

        del(s1)
        
        n2 = note.Note("D")
        n2.duration.type = "whole"
        n3 = note.Note("E")
        n3.duration.type = "whole"
        ts1 = meter.TimeSignature("4/4")
        s2 = stream.Stream()
        s2.append(c1)
        s2.append(ts1)
        s2.append(n2)
        s2.append(n3)
        s2.makeMeasures()
        self.assertFalse(n2.getContextByClass(stream.Measure) is n3.getContextByClass(stream.Measure))
        self.assertTrue(n2.getContextByClass(Clef) is c1)

        del(s2)
        
        n4 = note.Note("F")
        n4.duration.type = "half"
        n5 = note.Note("G")
        n5.duration.type = "half"
        n6 = note.Note("A")
        n6.duration.type = "whole"
        
        ts2 = meter.TimeSignature("4/4")
        bc1 = BassClef()
        tc1 = TrebleClef()
        
        s3 = stream.Stream()
        s3.append(bc1)
        s3.append(ts2)
        s3.append(n4)
        s3.append(tc1)
        s3.append(n5)
        s3.append(n6)
        s3.makeMeasures()

        self.assertTrue(n4.getContextByClass(stream.Measure) is n5.getContextByClass(stream.Measure))
        self.assertTrue(n4.getContextByClass(Clef) is bc1)
        self.assertTrue(n5.getContextByClass(Clef) is tc1)
        self.assertTrue(n6.getContextByClass(Clef) is tc1)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Clef, TrebleClef, BassClef]


if __name__ == "__main__":
    music21.mainTest(Test)



