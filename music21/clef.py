# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         clef.py
# Purpose:      Objects for representing clefs
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#
# Changes:      04th March 2014 by Michael Bodenbach
#               - TabClef added
#-------------------------------------------------------------------------------
'''
This module defines numerous subclasses of 
:class:`~music21.clef.Clef`, providing object representations for all 
commonly used clefs. Clef objects are often found 
within :class:`~music21.stream.Measure` objects.  
'''
 
import unittest

from music21 import base
from music21 import common
from music21 import exceptions21
from music21 import environment
_MOD = "clef.py"
environLocal = environment.Environment(_MOD)


class ClefException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
class Clef(base.Music21Object):
    '''
    A Clef is a basic music21 object for representing musical clefs
    (Treble, Bass, etc.)
    
    
    Some clefs only represent the graphical element of the clef, 
    such as G clef, which is subclassed by TrebleClef() and FrenchViolinClef().
    
    >>> tc = clef.TrebleClef()
    >>> tc
    <music21.clef.TrebleClef>
    >>> tc.sign
    'G'
    >>> tc.line
    2
        
    Most clefs also have a "lowestLine" function which represents the
    :attr:`~music21.pitch.Pitch.diatonicNoteNum` of the note that would fall on the
    lowest line if the Clef were put on a five-line staff. (Where C4,C#4,C##4,C-4
    etc. = 29, all types of D4 = 30, etc.)
    
    >>> tc.lowestLine
    31
    '''
    
    classSortOrder = 0

    def __init__(self):
        base.Music21Object.__init__(self)
        self.sign = None
        # line counts start from the bottom up, the reverse of musedata
        self.line = None
        self.octaveChange = 0 # set to zero as default
        # musicxml has an attribute for clefOctaveChange, 
        # an integer to show transposing clef

    def __repr__(self):
        # get just the clef name of this instance
        return "<music21.clef.%s>" % common.classToClassStr(self.__class__)
        #return "<music21.clef.%s>" % str(self.__class__).split('.')[-1][:-2]

    def __eq__(self, other):
        '''
        two Clefs are equal if their class is the same, their sign is the same,
        their line is the same and their octaveChange is the same.
        
        
        >>> c1 = clef.PercussionClef()
        >>> c2 = clef.NoClef()
        >>> c1 == c2
        False
        >>> c3 = clef.TrebleClef()
        >>> c4 = clef.TrebleClef()
        >>> c3 == c4
        True
        >>> c4.octaveChange = -1
        >>> c3 == c4
        False
        '''
        try:
            if self.__class__ == other.__class__ and self.sign == other.sign \
                    and self.line == other.line and self.octaveChange == other.octaveChange:
                return True
            else:
                return False
        except AttributeError:
            return False

#-------------------------------------------------------------------------------
class PitchClef(Clef):
    '''
    superclass for all other clef subclasses that use pitches...
    '''
    def __init__(self):
        Clef.__init__(self)


class PercussionClef(Clef):
    '''
    represents a Percussion clef. 
    
    >>> pc = clef.PercussionClef()
    >>> pc.sign
    'percussion'
    >>> pc.line is None
    True

    Percussion clefs should not, technically. have a
    lowest line, but it is a common usage to assume that
    in pitch-centric contexts to use the pitch numbers
    from treble clef for percussion clefs.  Thus:
    
    >>> pc.lowestLine == clef.TrebleClef().lowestLine
    True
    '''    
    def __init__(self):
        Clef.__init__(self)
        self.sign = 'percussion'
        self.lowestLine = (7*4) + 3  # 4 octaves + 3 notes = e4
        
class NoClef(Clef):
    '''
    represents the absence of a Clef. 
    
    >>> nc = clef.NoClef()
    >>> nc.sign
    'none'
    
    Note that the sign is the string 'none' not the None object
    
    >>> nc.sign is None
    False
    '''
    def __init__(self):
        Clef.__init__(self)
        self.sign = 'none'

class JianpuClef(NoClef):
    '''
    Jianpu notation does not use a clef, but musicxml marks it
    with a specialized "jianpu" sign.
    
    >>> jc = clef.JianpuClef()
    >>> jc.sign
    'jianpu'
    '''
    def __init__(self):
        NoClef.__init__(self)
        self.sign = 'jianpu'


class TabClef(PitchClef):
    '''
    represents a Tablature clef. 

    >>> a = clef.TabClef()
    >>> a.sign
    'TAB'
    '''
    def __init__(self):
        PitchClef.__init__(self)
        self.sign = "TAB"
        self.line = 5

#-------------------------------------------------------------------------------
class GClef(PitchClef):
    def __init__(self):
        '''
        
        >>> a = clef.GClef()
        >>> a.sign
        'G'
        '''
        PitchClef.__init__(self)
        self.sign = "G"
        self.lowestLine = None

class FrenchViolinClef(GClef):
    def __init__(self):
        '''
        
        >>> a = clef.FrenchViolinClef()
        >>> a.sign
        'G'
        '''
        GClef.__init__(self)
        self.line = 1
        self.lowestLine = (7*4) + 5

class TrebleClef(GClef):
    def __init__(self):
        '''
        
        >>> a = clef.TrebleClef()
        >>> a.sign
        'G'
        '''
        GClef.__init__(self)
        self.line = 2
        self.lowestLine = (7*4) + 3  # 4 octaves + 3 notes = e4

class Treble8vbClef(TrebleClef):
    def __init__(self):
        '''
        
        >>> a = clef.Treble8vbClef()
        >>> a.sign
        'G'
        >>> a.octaveChange
        -1
        '''
        TrebleClef.__init__(self)
        self.octaveChange = -1
        self.lowestLine = (7*3) + 3

class Treble8vaClef(TrebleClef):
    def __init__(self):
        '''
        
        >>> a = clef.Treble8vaClef()
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
        
        >>> a = clef.GSopranoClef()
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
        
        >>> a = clef.CClef()
        >>> a.sign
        'C'
        '''
        PitchClef.__init__(self)
        self.sign = "C"
        self.lowestLine = None

class SopranoClef(CClef):
    def __init__(self):
        '''
        
        >>> a = clef.SopranoClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 1
        self.lowestLine = (7*4) + 1

class MezzoSopranoClef(CClef):
    def __init__(self):
        '''
        
        >>> a = clef.MezzoSopranoClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 2
        self.lowestLine = (7*3) + 6
    
class AltoClef(CClef):
    def __init__(self):
        '''
        
        >>> a = clef.AltoClef()
        >>> a.sign
        'C'
        '''
        CClef.__init__(self)
        self.line = 3
        self.lowestLine = (7*3) + 4

class TenorClef(CClef):
    def __init__(self):
        '''
        
        >>> a = clef.TenorClef()
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
        
        >>> a = clef.CBaritoneClef()
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
        
        >>> a = clef.FClef()
        >>> a.sign
        'F'
        '''
        PitchClef.__init__(self)
        self.sign = "F"
        self.lowestLine = None

class FBaritoneClef(FClef):
    def __init__(self):
        '''
        
        >>> a = clef.FBaritoneClef()
        >>> a.sign
        'F'
        >>> a.line
        3
        >>> b = clef.CBaritoneClef()
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
        
        >>> a = clef.BassClef()
        >>> a.sign
        'F'
        '''
        FClef.__init__(self)
        self.line = 4
        self.lowestLine = (7*2) + 5

class Bass8vbClef(FClef):
    def __init__(self):
        '''
        
        >>> a = clef.Bass8vbClef()
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
        
        >>> a = clef.Bass8vaClef()
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
        An F clef on the top line.
        
        
        >>> a = clef.SubBassClef()
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
    "F": [None, None, None, FBaritoneClef, BassClef, SubBassClef],
    "TAB" : [None, None, None, None, None, TabClef]
    }



def clefFromString(clefString, octaveShift = 0):
    '''
    Returns a Clef object given a string like "G2" or "F4" etc.
    
    Does not refer to a violin/guitar string.

    
    >>> tc = clef.clefFromString("G2")
    >>> tc
    <music21.clef.TrebleClef>
    >>> nonStandard1 = clef.clefFromString("F1")
    >>> nonStandard1
    <music21.clef.FClef>
    >>> nonStandard1.line
    1
    >>> nonStandard2 = clef.clefFromString("D4")
    >>> nonStandard2
    <music21.clef.PitchClef>
    >>> nonStandard2.sign
    'D'
    >>> nonStandard2.line
    4


    >>> tc8vb = clef.clefFromString("G2", -1)
    >>> tc8vb
    <music21.clef.Treble8vbClef>

    Three special clefs, Tab, Percussion, and None are also supported.

    >>> tabClef = clef.clefFromString("TAB")
    >>> tabClef
    <music21.clef.TabClef>

    Case does not matter.

    >>> tc8vb = clef.clefFromString("g2", -1)
    >>> tc8vb
    <music21.clef.Treble8vbClef>

    >>> percussionClef = clef.clefFromString('Percussion')
    >>> percussionClef
    <music21.clef.PercussionClef>

    >>> noClef = clef.clefFromString('None')
    >>> noClef
    <music21.clef.NoClef>
    '''
    xnStr = clefString.strip()
    if xnStr.lower() in ('tab', 'percussion', 'none', 'jianpu'):
        if xnStr.lower() == 'tab':
            return TabClef()
        elif xnStr.lower() == 'percussion':
            return PercussionClef()
        elif xnStr.lower() == 'none':
            return NoClef()
        elif xnStr.lower() == 'jianpu':
            return JianpuClef()
    
    if len(xnStr) > 1:
        (thisType, lineNum) = (xnStr[0], xnStr[1])
    elif len(xnStr) == 1: # some Humdrum files have just ClefG, eg. Haydn op. 9 no 3, mvmt 1
        thisType = xnStr[0].upper()
        if thisType == "G":
            lineNum = 2
        elif thisType == "F":
            lineNum = 4
        elif thisType == "C":
            lineNum = 3
    else:
        raise ClefException("Entry has clef info but no clef specified")

    if octaveShift != 0:
        params = (thisType.upper(), int(lineNum), octaveShift)
        if params == ('G', 2, -1):
            return Treble8vbClef()
        elif params == ('G', 2, 1):
            return Treble8vaClef()
        elif params == ('F', 4, -1):
            return Bass8vbClef()
        elif params == ('F', 4, 1):
            return Bass8vaClef()
        ### other octaveShifts will pass through
    
    if thisType is False or lineNum is False:
        raise ClefException("can't read %s as clef str, should be G2, F4, etc.", xnStr)
    lineNum = int(lineNum)
    if lineNum < 1 or lineNum > 5:
        raise ClefException("line number (second character) must be 1-5;" + 
                            "do not use this function for clefs on special staves: %s", xnStr)

    clefObj = None
    if thisType in CLASS_FROM_TYPE:
        if CLASS_FROM_TYPE[thisType][lineNum] is None:
            if thisType == "G":
                clefObj = GClef()
            elif thisType == "F":
                clefObj = FClef()
            elif thisType == "C":
                clefObj = CClef()
            elif thisType == "TAB":
                clefObj = TabClef()
            clefObj.line = lineNum
        else:
            clefObj = CLASS_FROM_TYPE[thisType][lineNum]()
    else:
        clefObj = PitchClef()
        clefObj.sign = thisType
        clefObj.line = lineNum

    if octaveShift != 0:
        clefObj.octaveChange = octaveShift
    
    return clefObj

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__:
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
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)


    def testConversionClassMatch(self):
        from xml.etree.ElementTree import fromstring as El
        from music21.musicxml.xmlToM21 import MeasureParser
        from music21 import clef
        # need to get music21.clef.X, not X, because
        # we are comparing the result to a translation outside
        # clef.py
        src = [
            [('G', 1, 0), clef.FrenchViolinClef],
            [('G', 2, 0), clef.TrebleClef],
            [('G', 2, -1), clef.Treble8vbClef],
            [('G', 2, 1), clef.Treble8vaClef],
            [('G', 3, 0), clef.GSopranoClef],
            [('C', 1, 0), clef.SopranoClef],
            [('C', 2, 0), clef.MezzoSopranoClef],
            [('C', 3, 0), clef.AltoClef],
            [('C', 4, 0), clef.TenorClef],
            [('C', 5, 0), clef.CBaritoneClef],
            [('F', 3, 0), clef.FBaritoneClef],
            [('F', 4, 0), clef.BassClef],
            [('F', 4, 1), clef.Bass8vaClef],
            [('F', 4, -1), clef.Bass8vbClef],
            [('F', 5, 0), clef.SubBassClef],
            [('TAB', 5, 0), clef.TabClef]
        ]

        MP = MeasureParser()
        
        for params, className in src:
            sign, line, octaveChange = params
            mxClef = El(r'<clef><sign>' + sign + '</sign><line>' + str(line) + '</line>' +
                        '<clef-octave-change>' + str(octaveChange) + '</clef-octave-change></clef>')
            c = MP.xmlToClef(mxClef)

            #environLocal.printDebug([type(c).__name__])

            self.assertEqual(c.sign, params[0])
            self.assertEqual(c.line, params[1])
            self.assertEqual(c.octaveChange, params[2])
            self.assertEqual(isinstance(c, className), True, "Failed Conversion of classes: %s is not a %s" % (c, className))

    def testContexts(self):
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
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

