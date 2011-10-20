# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         harmony.py
# Purpose:      music21 classes for representing harmonies and chord symbols
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
An object representation of harmony, as encountered as chord symbols or other chord representations with a defined root.
'''


import unittest, doctest

import music21
from music21 import common
from music21 import pitch
from music21 import roman
from music21 import interval
from music21 import duration

from music21 import environment
_MOD = "harmony.py"
environLocal = environment.Environment(_MOD)
#-------------------------------------------------------------------------------
# kind values defined in musicxml

# <xs:enumeration value="major"/>
# <xs:enumeration value="minor"/>
# <xs:enumeration value="augmented"/>
# <xs:enumeration value="diminished"/>
# <xs:enumeration value="dominant"/>
# <xs:enumeration value="major-seventh"/>
# <xs:enumeration value="minor-seventh"/>
# <xs:enumeration value="diminished-seventh"/>
# <xs:enumeration value="augmented-seventh"/>
# <xs:enumeration value="half-diminished"/>
# <xs:enumeration value="major-minor"/>
# <xs:enumeration value="major-sixth"/>
# <xs:enumeration value="minor-sixth"/>
# <xs:enumeration value="dominant-ninth"/>
# <xs:enumeration value="major-ninth"/>
# <xs:enumeration value="minor-ninth"/>
# <xs:enumeration value="dominant-11th"/>
# <xs:enumeration value="major-11th"/>
# <xs:enumeration value="minor-11th"/>
# <xs:enumeration value="dominant-13th"/>
# <xs:enumeration value="major-13th"/>
# <xs:enumeration value="minor-13th"/>
# <xs:enumeration value="suspended-second"/>
# <xs:enumeration value="suspended-fourth"/>
# <xs:enumeration value="Neapolitan"/>
# <xs:enumeration value="Italian"/>
# <xs:enumeration value="French"/>
# <xs:enumeration value="German"/>
# <xs:enumeration value="pedal"/>
# <xs:enumeration value="power"/>
# <xs:enumeration value="Tristan"/>
# <xs:enumeration value="other"/>
# <xs:enumeration value="none"/>
def getduration(piece):
    pf = piece.flat
    onlychords = pf.getElementsByClass(ChordSymbol)
    first = True
    for cs in onlychords:
        if first:
            lastchord = cs
            first = False
            continue
        else:
            lastchord.duration.quarterLength = cs.getOffsetBySite(pf) - lastchord.getOffsetBySite(pf)
            if onlychords.index(cs) == (len(onlychords) - 1):
                cs.duration.quarterLength = pf.highestOffset - cs.getOffsetBySite(pf)
            lastchord = cs
    return pf

#-------------------------------------------------------------------------------
class HarmonyDegreeException(Exception):
    pass

class HarmonyException(Exception):
    pass

#-------------------------------------------------------------------------------
class HarmonyDegree(object):
    '''HarmonyDegree objects define the specification of harmony degree alterations, subtractions, or additions, as used in :class:`~music21.harmony.Harmony` objects

    >>> from music21 import harmony
    >>> hd = harmony.HarmonyDegree('add', 4)
    >>> hd
    <music21.harmony.HarmonyDegree type=add degree=4 interval=None>
    >>> hd = harmony.HarmonyDegree('alter', 3, 1)
    >>> hd
    <music21.harmony.HarmonyDegree type=alter degree=3 interval=<music21.interval.Interval A1>>

    '''
    def __init__(self, type=None, degree=None, interval=None):
        self._type = None # add, alter, subtract
        self._interval = None # alteration of degree, alter ints in mxl
        self._degree = None # the degree number, where 3 is the third

        # use properties if defind
        if type is not None:    
            self.type = type
        if degree is not None:
            self.degree = degree
        if interval is not None:
            self.interval = interval
    
    def __repr__(self):
        return '<music21.harmony.HarmonyDegree type=%s degree=%s interval=%s>' % (self.type, self.degree, self.interval)
        
    #---------------------------------------------------------------------------
    def _setType(self, value):
        if value is not None and common.isStr(value):
            if value.lower() in ['add', 'subtract', 'alter']:
                self._type = value.lower()
                return            
        raise HarmonyDegreeException('not a valid degree type: %s' % value)

    def _getType(self):
        return self._type

    type = property(_getType, _setType, doc= '''
        Get or set the HarmonyDegree type, where permitted types are the strings add, subtract, or alter.

        >>> from music21 import *
        >>> hd = harmony.HarmonyDegree()
        >>> hd.type = 'add'
        >>> hd.type
        'add'
        >>> hd.type = 'juicy'
        Traceback (most recent call last):
        HarmonyDegreeException: not a valid degree type: juicy
        ''')

    #---------------------------------------------------------------------------
    def _setInterval(self, value):
        if value in [None]: 
            self._interval = None

        elif hasattr(value, 'classes') and 'Interval' in value.classes:
            # an interval object: set directly
            self._interval = value
        else:
            # accept numbers to permit loading from mxl alter specs
            if value in [1]:
                self._interval = interval.Interval('a1')
            elif value in [2]: # double augmented
                self._interval = interval.Interval('aa1')
            elif value in [-1]:
                self._interval = interval.Interval('-a1')
            elif value in [-2]:
                self._interval = interval.Interval('-aa1')
            else: # try to create intervla object
                self._interval = interval.Interval(value)

    def _getInterval(self):
        return self._interval

    interval = property(_getInterval, _setInterval, doc= '''
        Get or set the alteration of this degree as a :class:`~music21.interval.Interval` object.

        >>> from music21 import *
        >>> hd = harmony.HarmonyDegree()
        >>> hd.interval = 1
        >>> hd.interval
        <music21.interval.Interval A1>
        >>> hd.interval = -2
        >>> hd.interval
        <music21.interval.Interval AA-1>
        ''')

    #---------------------------------------------------------------------------
    def _setDegree(self, value):
        if value is not None and common.isNum(value):
            self._degree = int(value) # should always be an integer
            return            
        raise HarmonyDegreeException('not a valid degree: %s' % value)

    def _getDegree(self):
        return self._degree

    degree = property(_getDegree, _setDegree, doc= '''

        >>> from music21 import *
        >>> hd = harmony.HarmonyDegree()
        >>> hd.degree = 3
        >>> hd.degree
        3
        >>> hd.degree = 'juicy'
        Traceback (most recent call last):
        HarmonyDegreeException: not a valid degree: juicy

        ''')



#-------------------------------------------------------------------------------
class Harmony(music21.Music21Object):
    '''
    >>> from music21 import *
    >>> h = harmony.Harmony() 
    >>> h.kind = 'major'
    >>> h.kindStr = 'M'
    >>> h.root = 'b-'
    >>> h.bass = 'd'
    >>> h.inversion = 1
    >>> h.addHarmonyDegree(harmony.HarmonyDegree('add', 4))
    >>> h
    <music21.harmony.Harmony kind=major (M) root=B- bass=D inversion=1 duration=0.0 harmonyDegrees=<music21.harmony.HarmonyDegree type=add degree=4 interval=None>>

    '''
    # TODO: accept some creation args
    def __init__(self):
        music21.Music21Object.__init__(self)

        self._root = None # a pitch object
        self._bass = None # a pitch object
        self._roman = None # a romanNumeral numeral object, musicxml stores this within a node called <function> which might conflict with the Harmony...
        self._inversion = None # an integer

        # TODO: properties for these need to be implemented
        self.kind = '' # a string from defined list of harmonies
        self.kindStr = '' # the presentation of the kind or label of symbol

        # specify an array of degree alteration objects
        self._harmonyDegrees = []


    def __repr__(self):
        if len(self._harmonyDegrees) == 0:
            return '<music21.harmony.%s kind=%s (%s) root=%s bass=%s inversion=%s duration=%s>' % (self.__class__.__name__, self.kind, self.kindStr, self.root, self.bass, self.inversion, self.duration.quarterLength)
        else:
            return '<music21.harmony.%s kind=%s (%s) root=%s bass=%s inversion=%s duration=%s harmonyDegrees=%s>' % (self.__class__.__name__, self.kind, self.kindStr, self.root, self.bass, self.inversion, self.duration.quarterLength,''.join([str(x) for x in self._harmonyDegrees]))


    #---------------------------------------------------------------------------
    def _setRoot(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._root = value
            return
        try: # try to create a Pitch object
            self._root = pitch.Pitch(value)
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getRoot(self):
        return self._root

    root = property(_getRoot, _setRoot, doc= '''
        Get or set the root of the Harmony as a :class:`~music21.pitch.Pitch` object. String representations accepted by Pitch are also accepted.

        >>> from music21 import *
        >>> h = harmony.Harmony()
        >>> h.root = 'a#'
        >>> h.root
        A#
        >>> h.root = pitch.Pitch('c#')
        >>> h.root
        C#
        >>> h.root = 'juicy'
        Traceback (most recent call last):
        HarmonyException: not a valid pitch specification: juicy
        ''')

    #---------------------------------------------------------------------------
    def _setBass(self, value):
        if hasattr(value, 'classes') and 'Pitch' in value.classes:
            self._bass = value
            return
        try: # try to create a Pitch object
            self._bass = pitch.Pitch(value)
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getBass(self):
        return self._bass

    bass = property(_getBass, _setBass, doc= '''
        Get or set the bass of the Harmony as a :class:`~music21.pitch.Pitch` object. String representations accepted by Pitch are also accepted.

        >>> from music21 import *
        >>> h = harmony.Harmony()
        >>> h.bass = 'a#'
        >>> h.bass
        A#
        >>> h.bass = pitch.Pitch('d-')
        >>> h.bass
        D-
        >>> h.bass = 'juicy'
        Traceback (most recent call last):
        HarmonyException: not a valid pitch specification: juicy
        ''')

    #---------------------------------------------------------------------------
    def _setInversion(self, value):
        if common.isNum(value):
            self._inversion = int(value)
            return
        raise HarmonyException('not a valid inversion specification: %s' % value)

    def _getInversion(self):
        return self._inversion

    inversion = property(_getInversion, _setInversion, doc= '''
        Get or set the inversion of this Harmony as an a positive integer.

        >>> from music21 import *
        >>> h = harmony.Harmony()
        >>> h.inversion = 2
        >>> h.inversion
        2
        ''')


    #---------------------------------------------------------------------------
    def _setRoman(self, value):
        if hasattr(value, 'classes') and 'RomanNumeral' in value.classes:
            self._roman = value
            return
        try: # try to create 
            self._roman = roman.RomanNumeral(value)
            return
        except music21.Music21Exception: 
            pass
        raise HarmonyException('not a valid pitch specification: %s' % value)

    def _getRoman(self):
        return self._roman

    romanNumeral = property(_getRoman, _setRoman, doc= '''
        Get or set the romanNumeral numeral function of the Harmony as a :class:`~music21.romanNumeral.RomanNumeral` object. String representations accepted by RomanNumeral are also accepted.

        >>> from music21 import *
        >>> h = harmony.Harmony()
        >>> h.romanNumeral = 'III'
        >>> h.romanNumeral
        <music21.roman.RomanNumeral III>
        >>> h.romanNumeral = roman.RomanNumeral('vii')
        >>> h.romanNumeral
        <music21.roman.RomanNumeral vii>

        ''')


    #---------------------------------------------------------------------------
    # adding and processing HarmonyDegree objects

    def addHarmonyDegree(self, degree):
        '''Add a harmony degree specification to this Harmony as a :class:`~music21.harmony.HarmonyDegree` object.

        >>> from music21 import *
        >>> hd = harmony.HarmonyDegree('add', 4)
        >>> h = harmony.Harmony()
        >>> h.addHarmonyDegree(hd)
        >>> h.addHarmonyDegree('juicy')
        Traceback (most recent call last):
        HarmonyException: cannot add this object as a degree: juicy

        '''
        if not isinstance(degree, HarmonyDegree):
            # TODO: possibly create HarmonyDegree objects from other 
            # specifications
            raise HarmonyException('cannot add this object as a degree: %s' % degree)
        else:
            self._harmonyDegrees.append(degree)
        
        
    def getHarmonyDegrees(self):
        '''Return all harmony degrees as a list.
        '''
        return self._harmonyDegrees

class ChordSymbol(Harmony):
    pass

'''
     >>> from music21 import *
     >>> cs = harmony.ChordSymbol()
     >>> cs
     <music21.harmony.ChordSymbol kind= () root=None bass=None inversion=None duration=0.0>
    
'''


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass


    def testBasic(self):
        from music21 import harmony
        h = harmony.Harmony()
        hd = harmony.HarmonyDegree('add', 4)
        h.addHarmonyDegree(hd)
        self.assertEqual(len(h._harmonyDegrees), 1)


    def testCountHarmonicMotion(self):
        from music21 import converter
        s = converter.parse('http://wikifonia.org/node/8859')
        harms = s.flat.getElementsByClass('Harmony')
        
        totMotion = [0,0,0,0,0,0,0,0,0,0,0,0]
        totalHarmonicMotion = 0
        lastHarm = None
        
        for thisHarm in harms:
            if lastHarm is None:
                lastHarm = thisHarm
            else:
                if lastHarm.bass is not None:
                    lastBass = lastHarm.bass
                else:
                    lastBass = lastHarm.root
                    
                if thisHarm.bass is not None:
                    thisBass = thisHarm.bass
                else:
                    thisBass = thisHarm.root
                    
                if lastBass.pitchClass == thisBass.pitchClass:
                    pass
                else:
                    halfStepMotion = (lastBass.pitchClass - thisBass.pitchClass) % 12
                    totMotion[halfStepMotion] += 1
                    totalHarmonicMotion += 1
                    lastHarm = thisHarm
                    
        if totalHarmonicMotion == 0:
            vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        else:
            totHarmonicMotionFraction = [0.0, 0,0, 0,0,0, 0,0,0, 0,0,0]
            for i in range(1, 12):
                totHarmonicMotionFraction[i] = float(totMotion[i]) / totalHarmonicMotion
            vector = totHarmonicMotionFraction

        print vector




#-------------------------------------------------------------------------------
# define presented order in documentation

_DOC_ORDER = [Harmony, HarmonyDegree, ChordSymbol]



if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof







