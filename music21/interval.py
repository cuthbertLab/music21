# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         interval.py
# Purpose:      music21 classes for representing intervals
#
# Authors:      Michael Scott Cuthbert
#               Jackie Rogoff
#               Amy Hailes 
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines various types of interval objects. 
Fundamental classes are :class:`~music21.interval.Interval`, 
:class:`~music21.interval.GenericInterval`, 
and :class:`~music21.interval.ChromaticInterval`.
'''
from fractions import Fraction

import abc
import copy
import math
import unittest

from music21 import base
from music21 import common 
from music21 import exceptions21

from music21.ext import six
#from music21 import pitch # SHOULD NOT, b/c of enharmonics

from music21 import environment
_MOD = "interval.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
# constants

STEPNAMES = ('C', 'D', 'E', 'F', 'G', 'A', 'B')

DESCENDING = -1
OBLIQUE    = 0
ASCENDING  = 1
directionTerms = {DESCENDING:"Descending", 
                  OBLIQUE:"Oblique", 
                  ASCENDING:"Ascending"}

# specifiers are derived from these two lists; 
# perhaps better represented with a dictionary
# perhaps the first entry, below, should be None, like in prefixSpecs?
niceSpecNames = ['ERROR', 'Perfect', 'Major', 'Minor', 'Augmented', 'Diminished', 
                 'Doubly-Augmented', 'Doubly-Diminished', 'Triply-Augmented', 
                 'Triply-Diminished', "Quadruply-Augmented", "Quadruply-Diminished"]
prefixSpecs = [None, 'P', 'M', 'm', 'A', 'd', 'AA', 'dd', 'AAA', 'ddd', 'AAAA', 'dddd']

# constants provide the common numerical representation of an interval. 
# this is not the number of half tone shift. 

PERFECT    = 1
MAJOR      = 2
MINOR      = 3
AUGMENTED  = 4
DIMINISHED = 5
DBLAUG     = 6
DBLDIM     = 7
TRPAUG     = 8
TRPDIM     = 9
QUADAUG    = 10
QUADDIM    = 11

# ordered list of perfect specifiers
orderedPerfSpecs = ['dddd', 'ddd', 'dd', 'd', 'P', 'A', 'AA', 'AAA', 'AAAA']
perfSpecifiers = [QUADDIM, TRPDIM, DBLDIM, DIMINISHED, PERFECT, 
                  AUGMENTED, DBLAUG, TRPAUG, QUADAUG]
perfOffset = 4 # that is, Perfect is third on the list.s

# ordered list of imperfect specifiers
orderedImperfSpecs = ['dddd', 'ddd', 'dd', 'd', 'm', 'M', 'A', 'AA', 'AAA', 'AAAA']
# why is this not called imperfSpecifiers?
specifiers = [QUADDIM, TRPDIM, DBLDIM, DIMINISHED, MINOR, MAJOR, 
              AUGMENTED, DBLAUG, TRPAUG, QUADAUG]
majOffset  = 5 # index of Major

# the following dictionaries provide half step shifts given key values
# either as integers (generic) or as strings (adjust perfect/imprefect)
#assuming Perfect or Major
semitonesGeneric = {1:0, 2:2, 3:4, 4:5, 5:7, 6:9, 7:11} 
semitonesAdjustPerfect = {"P":0, "A":1, "AA":2, "AAA":3, 'AAAA': 4,
                          "d":-1, "dd":-2, "ddd":-3, 'dddd': -4} #offset from Perfect
semitonesAdjustImperf = {"M":0, "m":-1, "A":1, "AA":2, "AAA":3, "AAAA": 4, 
                         "d":-2, "dd":-3, "ddd":-4, 'dddd': -5} #offset from Major


#-------------------------------------------------------------------------------
class IntervalException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
# some utility functions



def convertStaffDistanceToInterval(staffDist):
    '''
    Returns an integer of the generic interval number 
    (P5 = 5, M3 = 3, minor 3 = 3 also) etc. from the given staff distance.

    
    >>> interval.convertStaffDistanceToInterval(3)
    4
    >>> interval.convertStaffDistanceToInterval(7)
    8
    >>> interval.convertStaffDistanceToInterval(0)
    1
    >>> interval.convertStaffDistanceToInterval(-1)
    -2
    '''
    if staffDist == 0:
        return 1
    elif staffDist > 0:
        return staffDist + 1
    else:
        return staffDist - 1


def convertDiatonicNumberToStep(dn):
    '''
    Convert a diatonic number to a step name (without accidental) and a octave integer. 
    The lowest C on a Bosendorfer Imperial Grand is assigned 1 the D above it is 2,
    E is 3, etc.  See pitch.diatonicNoteNum for more details

    
    >>> interval.convertDiatonicNumberToStep(15)
    ('C', 2)
    >>> interval.convertDiatonicNumberToStep(23)
    ('D', 3)
    >>> interval.convertDiatonicNumberToStep(0)
    ('B', -1)
    >>> interval.convertDiatonicNumberToStep(1)
    ('C', 0)


    Extremely high and absurdly low numbers also produce "notes".
    

    >>> interval.convertDiatonicNumberToStep(2100)
    ('B', 299)
    >>> interval.convertDiatonicNumberToStep(-19)
    ('D', -3)
    
    
    OMIT_FROM_DOCS
    >>> interval.convertDiatonicNumberToStep(2)
    ('D', 0)
    >>> interval.convertDiatonicNumberToStep(3)
    ('E', 0)
    >>> interval.convertDiatonicNumberToStep(4)
    ('F', 0)
    >>> interval.convertDiatonicNumberToStep(5)
    ('G', 0)
    >>> interval.convertDiatonicNumberToStep(-1)
    ('A', -1)
    >>> interval.convertDiatonicNumberToStep(-2)
    ('G', -1)
    >>> interval.convertDiatonicNumberToStep(-6)
    ('C', -1)
    >>> interval.convertDiatonicNumberToStep(-7)
    ('B', -2)
    '''
    if dn == 0:
        return 'B', -1
    elif dn > 0:
        octave = int((dn-1)/7.0)
        stepNumber = (dn-1) - (octave * 7)
        return STEPNAMES[stepNumber], octave

#        remainder, octave = math.modf((dn-1)/7.0)
        # what is .001 doing here? -- A: prevents floating point errors
#        return STEPNAMES[int((remainder*7)+.001)], int(octave)
    elif dn < 0:
        octave = int((dn)/7.0)
        stepNumber = (dn-1) - (octave * 7)
        return STEPNAMES[stepNumber], (octave - 1)


def convertSpecifier(specifier):
    '''
    Given an integer or a string representing a "specifier" (major, minor,
    perfect, diminished, etc.), return a tuple of (1) an integer which 
    refers to the appropriate specifier in a list and (2) a standard form
    for the specifier.

    This function permits specifiers to specified in a flexible manner.

    
    >>> interval.convertSpecifier(3)
    (3, 'm')
    >>> interval.convertSpecifier('p')
    (1, 'P')
    >>> interval.convertSpecifier('P')
    (1, 'P')
    >>> interval.convertSpecifier('M')
    (2, 'M')
    >>> interval.convertSpecifier('major')
    (2, 'M')
    >>> interval.convertSpecifier('m')
    (3, 'm')
    >>> interval.convertSpecifier('Augmented')
    (4, 'A')
    >>> interval.convertSpecifier('a')
    (4, 'A')
    >>> interval.convertSpecifier(None)
    (None, None)
    '''
    post = None
    postStr = None
    if common.isNum(specifier):
        post = specifier
    # check string matches
    if isinstance(specifier, six.string_types):
        if specifier in prefixSpecs:
            post = prefixSpecs.index(specifier)
        # permit specifiers as prefixes without case; this will not distinguish
        # between m and M, but was taken care of in the line above
        elif specifier.lower() in [x.lower() for x in prefixSpecs[1:]]:    
            for i in range(len(prefixSpecs)):
                if prefixSpecs[i] is None: 
                    continue
                if specifier.lower() == prefixSpecs[i].lower():
                    post = i
                    break

        elif specifier.lower() in [x.lower() for x in niceSpecNames[1:]]:    
            for i in range(len(niceSpecNames)):
                if niceSpecNames[i] is None: 
                    continue
                if specifier.lower() == niceSpecNames[i].lower():
                    post = i
                    break
    # if no match or None, None will be returned
    if post != None:
        postStr = prefixSpecs[post]
    return post, postStr


def convertGeneric(value):
    '''Convert an interval specified in terms of its name (second, third) 
    into an integer. If integers are passed, assume the are correct.

    # TODO: use common.numberTools.musicOrdinals

    
    >>> interval.convertGeneric(3)
    3
    >>> interval.convertGeneric('third')
    3
    >>> interval.convertGeneric('3rd')
    3
    >>> interval.convertGeneric('octave')
    8
    >>> interval.convertGeneric('twelfth')
    12
    >>> interval.convertGeneric('descending twelfth')
    -12
    >>> interval.convertGeneric(12)
    12
    >>> interval.convertGeneric(-12)
    -12
    >>> interval.convertGeneric(1)
    1
    
    >>> interval.convertGeneric(None)
    Traceback (most recent call last):
    music21.interval.IntervalException: Cannot get a direction from None
    
    Strings are not the same as numbers...
    
    >>> interval.convertGeneric("1")
    Traceback (most recent call last):
    music21.interval.IntervalException: Cannot get a direction from 1
    '''
    post = None
    if common.isNum(value):
        post = value
        directionScalar = 1 # may still be negative
    elif isinstance(value, six.string_types):
        # first, see if there is a direction term
        directionScalar = ASCENDING # assume ascending
        for direction in [DESCENDING, ASCENDING]:
            if directionTerms[direction].lower() in value.lower():
                directionScalar = direction # assign numeric value
                # strip direction
                value = value.lower()
                value = value.replace(directionTerms[direction].lower(), '')
                value = value.strip()

        if value.lower() in ['unison']:
            post = 1
        elif value.lower() in ['2nd', 'second']:
            post = 2
        elif value.lower() in ['3rd', 'third']:
            post = 3
        elif value.lower() in ['4th', 'fourth']:
            post = 4
        elif value.lower() in ['5th', 'fifth']:
            post = 5
        elif value.lower() in ['6th', 'sixth']:
            post = 6
        elif value.lower() in ['7th', 'seventh']:
            post = 7
        elif value.lower() in ['8th', 'eighth', 'octave']:
            post = 8
        elif value.lower() in ['9th', 'ninth']:
            post = 9
        elif value.lower() in ['10th', 'tenth']:
            post = 10
        elif value.lower() in ['11th', 'eleventh']:
            post = 11
        elif value.lower() in ['12th', 'twelfth']:
            post = 12
        elif value.lower() in ['13th', 'thirteenth']:
            post = 13
        elif value.lower() in ['14th', 'fourteenth']:
            post = 14
        elif value.lower() in ['15th', 'fifteenth']:
            post = 15
        elif value.lower() in ['16th', 'sixteenth']:
            post = 16
    if post is None:
        raise IntervalException("Cannot get a direction from " + str(value))
    post = post * directionScalar
    return post

def convertSemitoneToSpecifierGenericMicrotone(count):
    '''
    Given a number of semitones, return a default diatonic specifier and cent offset.

    DEPRECATED if it can be moved..

    >>> interval.convertSemitoneToSpecifierGenericMicrotone(2.5)
    ('M', 2, 50.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(2.25)
    ('M', 2, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.0)
    ('m', 2, 0.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.75)
    ('M', 2, -25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.9)
    ('M', 2, -10.0...)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(0.25)
    ('P', 1, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(12.25)
    ('P', 8, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(24.25)
    ('P', 15, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(23.75)
    ('P', 15, -25.0)
    '''
    if count < 0: 
        dirScale = -1
    else:
        dirScale = 1

    count, micro = divmod(count, 1)
    # convert micro to cents
    cents = micro * 100.0
    if cents > 50:
        cents = cents - 100
        count += 1

    count = int(count)
    size = abs(count) % 12
    octave = abs(count) // 12 # let floor to int 

    if size == 0:
        spec = 'P'
        generic = 1
    elif size == 1:
        spec = 'm'
        generic = 2
    elif size == 2:
        spec = 'M'
        generic = 2
    elif size == 3:
        spec = 'm'
        generic = 3
    elif size == 4:
        spec = 'M'
        generic = 3
    elif size == 5:
        spec = 'P'
        generic = 4
    elif size == 6:
        spec = 'd'
        generic = 5
    elif size == 7:
        spec = 'P'
        generic = 5
    elif size == 8:
        spec = 'm'
        generic = 6
    elif size == 9:
        spec = 'M'
        generic = 6
    elif size == 10:
        spec = 'm'
        generic = 7
    elif size == 11:
        spec = 'M'
        generic = 7
    else:
        raise IntervalException('cannot match interval size: %s' % size)

    return spec, (generic+(octave*7)) * dirScale, cents



def convertSemitoneToSpecifierGeneric(count):
    '''
    Given a number of semitones, return a default diatonic specifier.

    
    >>> interval.convertSemitoneToSpecifierGeneric(0)
    ('P', 1)
    >>> interval.convertSemitoneToSpecifierGeneric(-2)
    ('M', -2)
    >>> interval.convertSemitoneToSpecifierGeneric(1)
    ('m', 2)
    >>> interval.convertSemitoneToSpecifierGeneric(7)
    ('P', 5)
    >>> interval.convertSemitoneToSpecifierGeneric(11)
    ('M', 7)
    >>> interval.convertSemitoneToSpecifierGeneric(12)
    ('P', 8)
    >>> interval.convertSemitoneToSpecifierGeneric(13)
    ('m', 9)
    >>> interval.convertSemitoneToSpecifierGeneric(-15)
    ('m', -10)
    >>> interval.convertSemitoneToSpecifierGeneric(24)
    ('P', 15)
    '''
    # strip off microtone
    return convertSemitoneToSpecifierGenericMicrotone(count)[:2]


_pythagorean_cache = {}

def intervalToPythagoreanRatio(intervalObj):
    r'''
    Returns the interval ratio in pythagorean tuning, always as a Fraction object.

    >>> iList = [interval.Interval(name) for name in ('P4', 'P5', 'M7')]
    >>> iList
    [<music21.interval.Interval P4>, <music21.interval.Interval P5>, <music21.interval.Interval M7>]
    
    >>> [interval.intervalToPythagoreanRatio(i) for i in iList]
    [Fraction(4, 3), Fraction(3, 2), Fraction(243, 128)]

    Throws an exception if no ratio can be found, such as for quarter tones.

    >>> p1, p2 = pitch.Pitch('C1'), pitch.Pitch('C1')
    >>> p2.accidental = 'half-sharp'
    
    >>> fiftyCent = interval.Interval(p1, p2)
    >>> fiftyCent
    <music21.interval.Interval A1 (-50c)>
    
    >>> interval.intervalToPythagoreanRatio(fiftyCent)
    Traceback (most recent call last):
    music21.interval.IntervalException: Could not find a pythagorean ratio for 
        <music21.interval.Interval A1 (-50c)>.
    '''
    from music21.pitch import Pitch

    start_pitch = Pitch('C1')
    end_pitch_wanted = start_pitch.transpose(intervalObj)

    if end_pitch_wanted.name in _pythagorean_cache:
        end_pitch, ratio = _pythagorean_cache[end_pitch_wanted.name]

    else:
        end_pitch_up = start_pitch
        end_pitch_down = start_pitch

        # when counter == 36, it wraps back to 'C' because of
        # music21's limiting of accidentals
        for counter in range(37):
            if end_pitch_up.name == end_pitch_wanted.name:
                ratio = Fraction(3, 2) ** counter
                end_pitch = end_pitch_up
                break
                
            elif end_pitch_down.name == end_pitch_wanted.name:
                ratio = Fraction(2, 3) ** counter
                end_pitch = end_pitch_down
                break

            else:
                end_pitch_up = end_pitch_up.transpose('P5')
                end_pitch_down = end_pitch_down.transpose('-P5')
        else:
            raise IntervalException(
                'Could not find a pythagorean ratio for {}.'.format(intervalObj))

        _pythagorean_cache[end_pitch_wanted.name] = end_pitch, ratio

    octaves = int((end_pitch_wanted.ps - end_pitch.ps)/12)
    return ratio * Fraction(2, 1) ** octaves

#-------------------------------------------------------------------------------
class IntervalBase(base.Music21Object):
    '''
    General base class for inheritance.
    '''
    def transposeNote(self, note1):
        '''
        Uses self.transposePitch to do the same to a note.
        
        >>> n1 = note.Note("C#4", quarterLength=2.0)
        >>> i = interval.Interval('d5')
        >>> n2 = i.transposeNote(n1)
        >>> n2
        <music21.note.Note G>
        >>> n2.pitch
        <music21.pitch.Pitch G4>
        >>> n2.duration.type
        'half'
        '''
        newPitch = self.transposePitch(note1.pitch)
        newNote = copy.deepcopy(note1)
        newNote.pitch = newPitch
        return newNote
    
    @abc.abstractmethod
    def transposePitch(self, pitch1):
        '''
        IntervalBase does not know how to do this, so it must be overridden in
        derived classes.
        '''
        raise NotImplementedError

class GenericInterval(IntervalBase):
    '''
    A GenericInterval is an interval such as Third, Seventh, Octave, or Tenth.
    Constructor takes an integer or string specifying the interval and direction. 

    The interval is not specified in half-steps, but in numeric values 
    derived from interval names: 
    a Third is 3; a Seventh is 7, etc. String values for interval names ('3rd' or 'third') 
    are generally accepted, but discouraged since not every one will work.
    
    staffDistance: the number of lines or spaces apart, eg:
      
        E.g. C4 to C4 = 0;  C4 to D4 = 1;  C4 to B3 = -1
    
    Two generic intervals are the equal if their size and direction are the same.
    
    '''
    def __init__(self, value = "unison"):
        '''
        
        >>> gi = interval.GenericInterval(8)
        >>> gi
        <music21.interval.GenericInterval 8>

        >>> aInterval = interval.GenericInterval(3)
        >>> aInterval.directed
        3
        >>> aInterval.direction
        1
        >>> aInterval.perfectable
        False
        >>> aInterval.staffDistance
        2

        >>> aInterval = interval.GenericInterval('Third')
        >>> aInterval.directed
        3
        >>> aInterval.staffDistance
        2

        >>> aInterval = interval.GenericInterval(-12)
        >>> aInterval.niceName
        'Twelfth'
        >>> aInterval.perfectable
        True
        >>> aInterval.staffDistance
        -11
        >>> aInterval.mod7
        4
        >>> aInterval.directed
        -12
        >>> aInterval.undirected
        12

        >>> bInterval = aInterval.complement()
        >>> bInterval.staffDistance
        3

        >>> aInterval = interval.GenericInterval('descending twelfth')
        >>> aInterval.perfectable
        True
        >>> aInterval.staffDistance
        -11

        >>> aInterval = interval.GenericInterval(0)
        Traceback (most recent call last):
        music21.interval.IntervalException: The Zeroth is not an interval

        >>> aInterval = interval.GenericInterval(24)
        >>> aInterval.niceName
        '24'
        >>> aInterval.isDiatonicStep
        False
        >>> aInterval.isStep
        False

        >>> aInterval = interval.GenericInterval(2)
        >>> aInterval.isDiatonicStep
        True
        >>> aInterval.isStep
        True


        Intervals >= 23rd use numbers instead of names
        
        >>> aInterval = interval.GenericInterval(23)
        >>> aInterval.niceName
        '23'
        '''
        IntervalBase.__init__(self)

        self.value = convertGeneric(value)
        self.directed = self.value
        self.undirected = abs(self.value)

        if self.directed == 1:
            self.direction = OBLIQUE
#         elif self.directed == -1:
#             raise IntervalException("Descending P1s not allowed; did you mean to write a " + 
#                                     "diminished unison instead?")
        elif self.directed == 0:
            raise IntervalException("The Zeroth is not an interval")
        elif self.directed == self.undirected:
            self.direction = ASCENDING
        else:
            self.direction = DESCENDING

        if self.undirected > 2: 
            self.isSkip = True
        else: 
            self.isSkip = False

        if self.undirected == 2: 
            self.isDiatonicStep = True
        else: 
            self.isDiatonicStep = False
        
        self.isStep = self.isDiatonicStep
        
        if self.undirected == 1:
            self.isUnison = True
        else:
            self.isUnison = False
        
        # unisons (even augmented) are neither steps nor skips.
        steps, octaves = math.modf(self.undirected/7.0)
        steps = int(steps*7 + .001)
        octaves = int(octaves)
        if (steps == 0):
            octaves = octaves - 1
            steps = 7
        self.simpleUndirected = steps

        # semiSimpleUndirected, same as simple, but P8 != P1
        self.semiSimpleUndirected = steps
        self.undirectedOctaves = octaves
        
        if (steps == 1 and octaves >= 1):
            self.semiSimpleUndirected = 8

        if (self.direction == DESCENDING):
            self.octaves = -1 * octaves
            if (steps != 1):
                self.simpleDirected = -1 * steps
            else:
                self.simpleDirected = 1  # no descending unisons...
            self.semiSimpleDirected = -1 * self.semiSimpleUndirected
        else:
            self.octaves = octaves
            self.simpleDirected = steps
            self.semiSimpleDirected = self.semiSimpleUndirected
            
        if (self.simpleUndirected==1) or \
           (self.simpleUndirected==4) or \
           (self.simpleUndirected==5):
            self.perfectable = True
        else:
            self.perfectable = False

        if self.undirected < len(common.musicOrdinals):
            self.niceName = common.musicOrdinals[self.undirected]
            self.simpleNiceName = common.musicOrdinals[self.simpleUndirected]
            self.semiSimpleNiceName = common.musicOrdinals[self.semiSimpleUndirected]

        else:
            self.niceName = str(self.undirected)
            self.simpleNiceName = str(self.simpleUndirected)
            self.semiSimpleNiceName = str(self.semiSimpleUndirected)
        
 
        if abs(self.directed) == 1:
            self.staffDistance = 0
        elif self.directed > 1:
            self.staffDistance = self.directed - 1
        elif self.directed < -1:
            self.staffDistance = self.directed + 1
        else:
            raise IntervalException("Non-integer, -1, or 0 not permitted as a diatonic interval")

        #  2 -> 7; 3 -> 6; 8 -> 1 etc.
        self.mod7inversion = 9 - self.semiSimpleUndirected 

        if self.direction == DESCENDING:
            self.mod7 = self.mod7inversion  ## see chord.semitonesFromChordStep for usage...
        else:
            self.mod7 = self.simpleDirected


    def __repr__(self):
        return "<music21.interval.GenericInterval %s>" % self.directed

    def __eq__(self, other):
        '''
        >>> a = interval.GenericInterval('Third')
        >>> b = interval.GenericInterval(-3)
        >>> c = interval.GenericInterval(3)
        >>> d = interval.GenericInterval(6)
        >>> a == b
        False
        >>> a == a == c
        True
        >>> b == c
        False
        >>> a != d
        True
        >>> a in [b, c, d]
        True
        
        >>> a == ""
        False
        >>> a is None
        False
        '''
        if other is None:
            return False
        elif not hasattr(other, "value"):
            return False
        elif not hasattr(other, "directed"):
            return False
        elif self.value == other.value and self.directed == other.directed:
            return True
        else:
            return False

    def complement(self):
        '''Returns a new GenericInterval object where descending 3rds are 6ths, etc.

        
        >>> aInterval = interval.GenericInterval('Third')
        >>> aInterval.complement()
        <music21.interval.GenericInterval 6>
        '''
        return GenericInterval(self.mod7inversion)

    def reverse(self):
        '''Returns a new GenericInterval object that is inverted. 

        >>> aInterval = interval.GenericInterval('Third')
        >>> aInterval.reverse()
        <music21.interval.GenericInterval -3>

        >>> aInterval = interval.GenericInterval(-13)
        >>> aInterval.direction
        -1
        >>> aInterval.reverse()
        <music21.interval.GenericInterval 13>
        
        Unisons invert to unisons
                
        >>> aInterval = interval.GenericInterval(1)
        >>> aInterval.reverse()
        <music21.interval.GenericInterval 1>
        '''
        if self.undirected == 1:
            return GenericInterval(1)
        else:
            return GenericInterval(self.undirected * (-1 * self.direction))

    def transposePitch(self, p):
        '''
        transpose a pitch, retaining the accidental if any.
        
        >>> aPitch = pitch.Pitch('g4')
        >>> genericFifth = interval.GenericInterval(5)
        >>> bPitch = genericFifth.transposePitch(aPitch)
        >>> bPitch
        <music21.pitch.Pitch D5>

        >>> a2 = pitch.Pitch('B-')
        >>> cPitch = genericFifth.transposePitch(a2)
        >>> cPitch
        <music21.pitch.Pitch F->
        >>> a2.octave == cPitch.octave
        True
        '''
        if p.octave is None:
            useImplicitOctave = True
        else:
            useImplicitOctave = False
        pdnn = p.diatonicNoteNum
        newPitch = copy.deepcopy(p)
        newPitch.diatonicNoteNum = pdnn + self.staffDistance
        if useImplicitOctave is True:
            newPitch.octave = None
        return newPitch
        

    def getDiatonic(self, specifier):
        '''
        Given a specifier, return a :class:`~music21.interval.DiatonicInterval` object. 

        Specifier should be provided as a string name, such as 'dd', 'M', or 'perfect'.

        
        >>> aInterval = interval.GenericInterval('Third')
        >>> aInterval.getDiatonic('major')
        <music21.interval.DiatonicInterval M3>
        >>> aInterval.getDiatonic('minor')
        <music21.interval.DiatonicInterval m3>
        >>> aInterval.getDiatonic('d')
        <music21.interval.DiatonicInterval d3>
        >>> aInterval.getDiatonic('a')
        <music21.interval.DiatonicInterval A3>
        >>> aInterval.getDiatonic(2)
        <music21.interval.DiatonicInterval M3>

        >>> bInterval = interval.GenericInterval('fifth')
        >>> bInterval.getDiatonic('perfect')
        <music21.interval.DiatonicInterval P5>
        '''             
        return DiatonicInterval(specifier, self)


class DiatonicInterval(IntervalBase):
    '''
    A class representing a diatonic interval. Two required arguments are a string `specifier` 
    (such as perfect, major, or minor) and `generic`, either an int of an interval size (such as 
    2, 2nd, or second) or a :class:`~music21.interval.GenericInterval` object.

    Two DiatonicIntervals are the same if their GenericIntervals are the same and their specifiers 
    are the same and they should be
    if their directions are the same, but this is not checked yet.    
    '''
    _DOC_ATTR = {
        'name': 'The name of the interval in abbreviated form without direction.',
        'niceName': 'The name of the interval in full form.',
        'directedName': 'The name of the interval in abbreviated form with direction.',
        'directedNiceName': 'The name of the interval in full form with direction.',
    }

    def __init__(self, specifier="P", generic=1):
        '''
        The `specifier` is an integer or string specifying a value in the `prefixSpecs` and 
        `niceSpecNames` lists. 

        The `generic` is an integer or GenericInterval instance.

        
        >>> aInterval = interval.DiatonicInterval(1, 1)
        >>> aInterval.simpleName
        'P1'
        >>> aInterval = interval.DiatonicInterval('p', 1)
        >>> aInterval.simpleName
        'P1'
        >>> aInterval = interval.DiatonicInterval('major', 3)
        >>> aInterval.simpleName
        'M3'
        >>> aInterval.niceName
        'Major Third'
        >>> aInterval.semiSimpleName
        'M3'
        >>> aInterval.directedSimpleName
        'M3'
        >>> aInterval.invertedOrderedSpecifier
        'm'
        >>> aInterval.mod7
        'M3'

        >>> aInterval = interval.DiatonicInterval('major', 'third')
        >>> aInterval.niceName
        'Major Third'

        >>> aInterval = interval.DiatonicInterval('perfect', 'octave')
        >>> aInterval.niceName
        'Perfect Octave'

        >>> aInterval = interval.DiatonicInterval('minor', 10)
        >>> aInterval.mod7
        'm3'
        >>> aInterval.isDiatonicStep
        False
        >>> aInterval.isStep
        False

        >>> aInterval = interval.DiatonicInterval('major', 2)
        >>> aInterval.isDiatonicStep
        True
        >>> aInterval.isStep
        True


        >>> augAscending = interval.DiatonicInterval('augmented', 1)
        >>> augAscending
        <music21.interval.DiatonicInterval A1>
        >>> augAscending.isDiatonicStep
        False
        >>> augAscending.isStep  # TODO: should this be True???
        False
        >>> augAscending.directedNiceName
        'Ascending Augmented Unison'
        
        Diatonic interval is ascending, but generic is oblique:
        
        >>> augAscending.direction == interval.ASCENDING
        True
        >>> augAscending.generic.direction == interval.ASCENDING
        False

        >>> dimDescending = augAscending.reverse()
        >>> dimDescending
        <music21.interval.DiatonicInterval d1>
        >>> dimDescending.directedNiceName
        'Descending Diminished Unison'
        >>> dimDescending.direction == interval.DESCENDING
        True
        '''
        IntervalBase.__init__(self)

        if specifier is not None and generic is not None:
            if common.isNum(generic) or isinstance(generic, six.string_types):
                self.generic = GenericInterval(generic)
            elif isinstance(generic, GenericInterval): 
                self.generic = generic
            else:
                raise IntervalException('incorrect generic argument: %s' % generic)

        self.name = ""
        # translate strings, if provided, to integers
        # specifier here is the index number in the prefixSpecs list
        self.specifier, unused_specifierStr = convertSpecifier(specifier)
        if self.generic.undirected != 1 or specifier == PERFECT:
            self.direction = self.generic.direction
        else: 
            # assume in the absence of other evidence, 
            # that augmented unisons are ascending and dim are descending 
            if perfSpecifiers.index(self.specifier) <= perfSpecifiers.index(DIMINISHED):
                self.direction = DESCENDING
            else:
                self.direction = ASCENDING
        diatonicDirectionNiceName = directionTerms[self.direction]


        if self.specifier is not None:
            self.name = (prefixSpecs[self.specifier] +
                        str(self.generic.undirected))
            self.niceName = (niceSpecNames[self.specifier] + " " +
                             self.generic.niceName)
            self.simpleName = (prefixSpecs[self.specifier] +
                              str(self.generic.simpleUndirected))
            self.simpleNiceName = (niceSpecNames[self.specifier] + " " +
                                  self.generic.simpleNiceName)
            self.semiSimpleName = (prefixSpecs[self.specifier] +
                                 str(self.generic.semiSimpleUndirected))
            self.semiSimpleNiceName = (niceSpecNames[self.specifier] + " " + 
                                    self.generic.semiSimpleNiceName)

            self.directedName = (prefixSpecs[self.specifier] +
                                 str(self.generic.directed))
            self.directedNiceName = (diatonicDirectionNiceName + 
                                    " " + self.niceName)
            self.directedSimpleName = (prefixSpecs[self.specifier] +
                                     str(self.generic.simpleDirected))
            self.directedSemiSimpleName = (prefixSpecs[self.specifier] +
                                 str(self.generic.semiSimpleDirected))
            self.directedSimpleNiceName = (diatonicDirectionNiceName + " " + 
                                           self.simpleNiceName)
            self.directedSemiSimpleNiceName = (diatonicDirectionNiceName + " " + 
                                               self.semiSimpleNiceName)

            self.specificName = niceSpecNames[self.specifier]
            self.prefectable = self.generic.perfectable

            self.isDiatonicStep = self.generic.isDiatonicStep
            self.isStep = self.generic.isStep
            

            # for inversions 
            if self.prefectable: # inversions P <-> P; d <-> A; dd <-> AA; etc. 
                self.orderedSpecifierIndex = orderedPerfSpecs.index(
                                             prefixSpecs[self.specifier])
                self.invertedOrderedSpecIndex = (len(orderedPerfSpecs) - 
                                        1 - self.orderedSpecifierIndex)
                self.invertedOrderedSpecifier = orderedPerfSpecs[
                                        self.invertedOrderedSpecIndex]
            else: # generate inversions.  m <-> M; d <-> A; etc.
                self.orderedSpecifierIndex = orderedImperfSpecs.index(
                                            prefixSpecs[self.specifier])
                self.invertedOrderedSpecIndex = (len(orderedImperfSpecs) - 
                                        1 - self.orderedSpecifierIndex)
                self.invertedOrderedSpecifier = orderedImperfSpecs[
                                        self.invertedOrderedSpecIndex]

            self.mod7inversion = self.invertedOrderedSpecifier + str(
                                 self.generic.mod7inversion)
            if self.direction == DESCENDING:
                self.mod7 = self.mod7inversion
            else:
                self.mod7 = self.simpleName

    def __repr__(self):
        return "<music21.interval.DiatonicInterval %s>" % self.name

    def __eq__(self, other):
        '''
        >>> a = interval.DiatonicInterval('major', 3)
        >>> b = interval.DiatonicInterval('minor', 3)
        >>> c = interval.DiatonicInterval('major', 3)
        >>> d = interval.DiatonicInterval('diminished', 4)
        >>> a == b
        False
        >>> a == c
        True
        >>> a == d
        False
        >>> e = interval.DiatonicInterval('d', 4)
        >>> d == e
        True        
        '''
        if other is None:
            return False
        elif not hasattr(other, "generic"):
            return False
        elif not hasattr(other, "specifier"):
            return False

        if other is None:
            return False
        
        ## untested...
        #if self.direction != other.direction:
        #    return False
        if (self.generic == other.generic 
            and self.specifier == other.specifier 
            and self.direction == other.direction):
            return True
        else:
            return False


    def reverse(self):
        '''
        Return a :class:`~music21.interval.DiatonicInterval` that is an inversion of this Interval.
        
        >>> aInterval = interval.DiatonicInterval('major', 3)
        >>> aInterval.reverse().directedName
        'M-3'

        >>> aInterval = interval.DiatonicInterval('augmented', 5)
        >>> aInterval.reverse().directedName
        'A-5'

        (Ascending) Augmented Unisons reverse to (Descending) Diminished Unisons and vice-versa

        >>> aInterval = interval.DiatonicInterval('augmented', 1)
        >>> aInterval.direction
        1
        >>> aInterval.directedName
        'A1'
        >>> dimUnison = aInterval.reverse()
        >>> dimUnison.directedName
        'd1'
        >>> dimUnison.directedNiceName
        'Descending Diminished Unison'
        '''
        # self.invertedOrderedSpecifier gives a complement, not an inversion?
        if self.generic.directed == 1:
            perfectPoint = perfSpecifiers.index(PERFECT)
            specifierPoint = perfSpecifiers.index(self.specifier)
            offsetFromPerfect = specifierPoint - perfectPoint
            reversedOffsetFromPerfect = -1 * offsetFromPerfect
            newSpecifierIndex = reversedOffsetFromPerfect + perfectPoint
            newSpecifier = perfSpecifiers[newSpecifierIndex]
            return DiatonicInterval(newSpecifier, 1)
        else:
            return DiatonicInterval(self.specifier,
                                    self.generic.reverse())

    def getChromatic(self):
        '''
        Return a :class:`music21.interval.ChromaticInterval` based on the size of this Interval.

        
        >>> aInterval = interval.DiatonicInterval('major', 'third')
        >>> aInterval.niceName
        'Major Third'
        >>> aInterval.getChromatic()
        <music21.interval.ChromaticInterval 4>

        >>> aInterval = interval.DiatonicInterval('augmented', -5)
        >>> aInterval.niceName
        'Augmented Fifth'
        >>> aInterval.getChromatic()
        <music21.interval.ChromaticInterval -8>

        >>> aInterval = interval.DiatonicInterval('minor', 'second')
        >>> aInterval.niceName
        'Minor Second'
        >>> aInterval.getChromatic()
        <music21.interval.ChromaticInterval 1>
        
        '''
        # note: part of this functionality used to be in the function
        # _stringToDiatonicChromatic(), which used to be named something else

        octaveOffset = int(abs(self.generic.staffDistance)/7)
        semitonesStart = semitonesGeneric[self.generic.simpleUndirected]
        specName = prefixSpecs[self.specifier]

        if self.generic.perfectable:
            # dictionary of semitones distance from perfect
            semitonesAdjust = semitonesAdjustPerfect[specName] 
        else:
            # dictionary of semitones distance from major
            semitonesAdjust = semitonesAdjustImperf[specName] 
    
        semitones = (octaveOffset*12) + semitonesStart + semitonesAdjust
        # want direction to be same as original direction
        if self.generic.direction == DESCENDING: 
            semitones *= -1 # (automatically positive until this step)

        return ChromaticInterval(semitones)

    def transposePitch(self, p):
        '''
        Calls transposePitch from a full interval object.

        This is not particularly optimized since it requires creating both a ChromaticInterval
        object and a full Interval object. But it's here for completeness.
        
        >>> di = interval.DiatonicInterval('P', 11)
        >>> di.transposePitch(pitch.Pitch('C#4'))
        <music21.pitch.Pitch F#5>
        '''
        fullIntervalObject = Interval(diatonic=self, chromatic=self.getChromatic())
        return fullIntervalObject.transposePitch(p)


    @property
    def specifierAbbreviation(self):
        '''
        Returns the abbreviation for the specifier.
        
        >>> i = interval.Interval('M-10')
        >>> d = i.diatonic
        >>> d.specifierAbbreviation
        'M'
        '''
        return prefixSpecs[self.specifier]

    @property
    def cents(self):
        '''
        Return a cents representation of this interval as a float, 
        always assuming an equal-tempered presentation. 
        
        >>> i = interval.DiatonicInterval('minor', 'second')
        >>> i.niceName
        'Minor Second'
        >>> i.cents
        100.0
        '''
        c = self.getChromatic()
        return c.cents







class ChromaticInterval(IntervalBase):
    '''
    Chromatic interval class. Unlike a :class:`~music21.interval.DiatonicInterval`, this Interval 
    class treats interval spaces in half-steps.  So Major 3rd and Diminished 4th are the same.
    
    Two ChromaticIntervals are equal if their size and direction are equal.

    '''
    def __init__(self, value=0):
        '''
        
        >>> aInterval = interval.ChromaticInterval(-14)
        >>> aInterval.semitones
        -14
        >>> aInterval.undirected
        14
        >>> aInterval.mod12
        10
        >>> aInterval.intervalClass
        2
        >>> aInterval.isChromaticStep
        False
        >>> aInterval.isStep
        False

        >>> aInterval = interval.ChromaticInterval(1)
        >>> aInterval.isChromaticStep
        True
        >>> aInterval.isStep
        True
        '''
        IntervalBase.__init__(self)

        if value == int(value):
            value = int(value)

        self.semitones = value
        self.cents = round(value * 100.0, 5)
        self.directed = value
        self.undirected = abs(value)

        if (self.directed == 0):
            self.direction = OBLIQUE
        elif (self.directed == self.undirected):
            self.direction = ASCENDING
        else:
            self.direction = DESCENDING

        self.mod12 = self.semitones % 12
        self.simpleUndirected = self.undirected % 12
        if (self.direction == DESCENDING):
            self.simpleDirected = -1 * self.simpleUndirected
        else:
            self.simpleDirected = self.simpleUndirected

        self.intervalClass = self.mod12
        if (self.mod12 > 6):
            self.intervalClass = 12 - self.mod12

        if self.undirected == 1:
            self.isChromaticStep = True
        else:
            self.isChromaticStep = False

        self.isStep = self.isChromaticStep

    def __repr__(self):
        return "<music21.interval.ChromaticInterval %s>" % self.directed

    def __eq__(self, other):
        '''
        
        >>> a = interval.ChromaticInterval(-14)
        >>> b = interval.ChromaticInterval(14)
        >>> c = interval.ChromaticInterval(-14)
        >>> d = interval.ChromaticInterval(7)
        >>> e = interval.ChromaticInterval(2)

        >>> a == b
        False
        >>> a == c
        True
        >>> a == d
        False
        >>> b == e
        False
        '''
        if other is None:
            return False
        elif not hasattr(other, "semitones"):
            return False

        if self.semitones == other.semitones:
            return True
        else:
            return False


    def reverse(self):
        '''
        Return an inverted :class:`~music21.interval.ChromaticInterval`, 
        that is, reversing the direction.

        
        >>> aInterval = interval.ChromaticInterval(-14)
        >>> aInterval.reverse()
        <music21.interval.ChromaticInterval 14>

        >>> aInterval = interval.ChromaticInterval(3)
        >>> aInterval.reverse()
        <music21.interval.ChromaticInterval -3>
        '''
        return ChromaticInterval(self.undirected * (-1 * self.direction))

    def getDiatonic(self):
        '''
        Given a ChromaticInterval, return a :class:`~music21.interval.DiatonicInterval` 
        object of the same size. 
        
        While there is more than one Generic Interval for any given chromatic 
        interval, this is needed to to permit easy chromatic specification of 
        Interval objects.  No augmented or diminished intervals are returned
        except for for interval of 6 which returns a diminished fifth, not
        augmented fourth.

        >>> aInterval = interval.ChromaticInterval(5)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval P4>

        >>> aInterval = interval.ChromaticInterval(6)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval d5>

        >>> aInterval = interval.ChromaticInterval(7)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval P5>

        >>> aInterval = interval.ChromaticInterval(11)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval M7>

        '''
        # ignoring microtone here
        specifier, generic = convertSemitoneToSpecifierGeneric(self.semitones)
        return DiatonicInterval(specifier, generic)
    
    def transposePitch(self, p):
        '''
        Given a :class:`~music21.pitch.Pitch` object, return a new, 
        transposed Pitch, that is transformed 
        according to this ChromaticInterval. 
        
        Because :class:`~music21.interval.ChromaticInterval` object 
        do not take into account diatonic spelling,
        the new Pitch is simplified to the most common intervals.  See
        :meth:`~music21.pitch.Pitch.simplifyEnharmonic` with ``mostCommon = True``
        to see the results.
                
        
        >>> ci = interval.ChromaticInterval(6)
        >>> p = pitch.Pitch("E#4")
        >>> p2 = ci.transposePitch(p)
        >>> p2
        <music21.pitch.Pitch B4>
        >>> p3 = ci.transposePitch(p2)
        >>> p3
        <music21.pitch.Pitch F5>

        If no octave number is given then octaves "wrap around" and thus even
        after transposing upward, you could end up with a pitch that is
        displayed as lower than the original:

        >>> p4 = pitch.Pitch("B")
        >>> p4.ps
        71.0
        >>> p5 = ci.transposePitch(p4)
        >>> p5.ps
        65.0
        '''
        if p.octave is None:
            useImplicitOctave = True
        else:
            useImplicitOctave = False
        pps = p.ps
        newPitch = copy.deepcopy(p)
        newPitch.ps = pps + self.semitones
        if useImplicitOctave is True:
            newPitch.octave = None
        return newPitch


#-------------------------------------------------------------------------------
def _stringToDiatonicChromatic(value):
    '''
    A function for processing interval strings and returning 
    diatonic and chromatic interval objects. Used by the Interval class, below. 

    >>> interval._stringToDiatonicChromatic('P5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>)
    >>> interval._stringToDiatonicChromatic('p5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>)
    >>> interval._stringToDiatonicChromatic('perfect5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>)

    >>> interval._stringToDiatonicChromatic('P-5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval -7>)
    >>> interval._stringToDiatonicChromatic('M3')
    (<music21.interval.DiatonicInterval M3>, <music21.interval.ChromaticInterval 4>)
    >>> interval._stringToDiatonicChromatic('m3')
    (<music21.interval.DiatonicInterval m3>, <music21.interval.ChromaticInterval 3>)

    >>> interval._stringToDiatonicChromatic('whole')
    (<music21.interval.DiatonicInterval M2>, <music21.interval.ChromaticInterval 2>)
    >>> interval._stringToDiatonicChromatic('half')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval 1>)
    >>> interval._stringToDiatonicChromatic('-h')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval -1>)

    >>> interval._stringToDiatonicChromatic('semitone')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval 1>)

    '''
    # find direction        
    if '-' in value:
        value = value.replace('-', '') # remove
        dirScale = -1
    else:
        dirScale = 1

    # permit whole and half appreviations
    if value.lower() in ['w', 'whole', 'tone']:
        value = 'M2'
    elif value.lower() in ['h', 'half', 'semitone']:
        value = 'm2'

    # apply dir shift value here
    found, remain = common.getNumFromStr(value)
    genericNumber = int(found) * dirScale
    #generic = int(value.lstrip('PMmAd')) * dirShift # this will be a number
    specName = remain  # value.rstrip('-0123456789')

    gInterval = GenericInterval(genericNumber)    
    dInterval = gInterval.getDiatonic(specName)
    return dInterval, dInterval.getChromatic()



def notesToGeneric(n1, n2):
    '''
    Given two :class:`~music21.note.Note` objects, 
    returns a :class:`~music21.interval.GenericInterval` object.
    
    Works equally well with :class:`~music21.pitch.Pitch` objects
    
    
    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g5')
    >>> aInterval = interval.notesToGeneric(aNote, bNote)
    >>> aInterval
    <music21.interval.GenericInterval 12>

    >>> aPitch = pitch.Pitch('c#4')
    >>> bPitch = pitch.Pitch('f-5')
    >>> bInterval = interval.notesToGeneric(aPitch, bPitch)
    >>> bInterval
    <music21.interval.GenericInterval 11>

    '''
    staffDist = n2.diatonicNoteNum - n1.diatonicNoteNum
    genDist = convertStaffDistanceToInterval(staffDist)
    return GenericInterval(genDist)

def notesToChromatic(n1, n2):
    '''
    Given two :class:`~music21.note.Note` objects, 
    returns a :class:`~music21.interval.ChromaticInterval` object.
    
    Works equally well with :class:`~music21.pitch.Pitch` objects.
    
    
    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g#5')
    >>> interval.notesToChromatic(aNote, bNote)
    <music21.interval.ChromaticInterval 20>

    >>> aPitch = pitch.Pitch('c#4')
    >>> bPitch = pitch.Pitch('f-5')
    >>> bInterval = interval.notesToChromatic(aPitch, bPitch)
    >>> bInterval
    <music21.interval.ChromaticInterval 15>

    '''
    if hasattr(n1, 'pitch'):
        p1 = n1.pitch
    else:
        p1 = n1
        
    if hasattr(n2, 'pitch'):
        p2 = n2.pitch
    else:
        p2 = n2

    return ChromaticInterval(p2.ps - p1.ps)


def _getSpecifierFromGenericChromatic(gInt, cInt):
    '''
    Given a :class:`~music21.interval.GenericInterval` and 
    a :class:`~music21.interval.ChromaticInterval` object, return a specifier 
    (i.e. MAJOR, MINOR, etc...).

    >>> aInterval = interval.GenericInterval('seventh')
    >>> bInterval = interval.ChromaticInterval(11)
    >>> interval._getSpecifierFromGenericChromatic(aInterval, bInterval)
    2
    >>> interval.convertSpecifier('major')
    (2, 'M')
    
    Absurdly altered interval:
    
    >>> cInterval = interval.GenericInterval('second')
    >>> dInterval = interval.ChromaticInterval(10)  # 8x augmented second
    >>> interval._getSpecifierFromGenericChromatic(cInterval, dInterval)
    Traceback (most recent call last):
    music21.interval.IntervalException: cannot get a specifier for a note with 
        this many semitones off of Major: 8
    '''        
    noteVals = [None, 0, 2, 4, 5, 7, 9, 11]
    normalSemis = noteVals[gInt.simpleUndirected] + 12 * gInt.undirectedOctaves

    if (gInt.direction != cInt.direction 
        and gInt.direction != OBLIQUE and cInt.direction != OBLIQUE):
        # intervals like d2 and dd2 etc. 
        # (the last test doesn't matter, since -1*0 == 0, but in theory it should be there)
        theseSemis = -1 * cInt.undirected
    elif gInt.undirected == 1:
        theseSemis = cInt.directed # matters for unison
    else:
        # all normal intervals
        theseSemis  = cInt.undirected
    # round out microtones
    # fix python3 rounding...
    if cInt.undirected > 0:
        roundingError = 0.0001
    else:
        roundingError = -0.0001
    
    semisRounded = int(round(theseSemis + roundingError)) # python3 rounding
    if gInt.perfectable:
        try:
            specifier = perfSpecifiers[perfOffset + semisRounded - normalSemis]
        except IndexError:
            raise IntervalException("cannot get a specifier for a note with this many semitones " +
                                    "off of Perfect: " + str(theseSemis - normalSemis))
    else:
        try:
            specifier = specifiers[majOffset + semisRounded - normalSemis]
        except IndexError:
            raise IntervalException("cannot get a specifier for a note with this many semitones " +
                                    "off of Major: " + str(theseSemis - normalSemis))

    return specifier    

    
def intervalsToDiatonic(gInt, cInt):
    '''
    Given a :class:`~music21.interval.GenericInterval` and 
    a :class:`~music21.interval.ChromaticInterval` object, 
    return a :class:`~music21.interval.DiatonicInterval`.    

    
    >>> aInterval = interval.GenericInterval('descending fifth')
    >>> bInterval = interval.ChromaticInterval(-7)
    >>> cInterval = interval.intervalsToDiatonic(aInterval, bInterval)
    >>> cInterval
    <music21.interval.DiatonicInterval P5>
    '''
    specifier = _getSpecifierFromGenericChromatic(gInt, cInt)
    return DiatonicInterval(specifier, gInt)
    
def intervalFromGenericAndChromatic(gInt, cInt):
    '''
    Given a :class:`~music21.interval.GenericInterval` and a 
    :class:`~music21.interval.ChromaticInterval` object, return 
    a full :class:`~music21.interval.Interval`.    

    
    >>> aInterval = interval.GenericInterval('descending fifth')
    >>> bInterval = interval.ChromaticInterval(-8)
    >>> cInterval = interval.intervalFromGenericAndChromatic(aInterval, bInterval)
    >>> cInterval
    <music21.interval.Interval A-5>

    >>> cInterval.name
    'A5'
    >>> cInterval.directedName
    'A-5'    
    >>> cInterval.directedNiceName
    'Descending Augmented Fifth'

    >>> interval.intervalFromGenericAndChromatic(3, 4)
    <music21.interval.Interval M3>
    >>> interval.intervalFromGenericAndChromatic(3, 3)
    <music21.interval.Interval m3>

    >>> interval.intervalFromGenericAndChromatic(5, 6)
    <music21.interval.Interval d5>
    >>> interval.intervalFromGenericAndChromatic(5, 5)
    <music21.interval.Interval dd5>
    >>> interval.intervalFromGenericAndChromatic(-2, -2)
    <music21.interval.Interval M-2>

    >>> interval.intervalFromGenericAndChromatic(1, 0.5)
    <music21.interval.Interval A1 (-50c)>

    '''
    if common.isNum(gInt):
        gInt = GenericInterval(gInt)
    if common.isNum(cInt):
        cInt = ChromaticInterval(cInt)

    specifier = _getSpecifierFromGenericChromatic(gInt, cInt)
    dInt = DiatonicInterval(specifier, gInt)
    return Interval(diatonic = dInt, chromatic = cInt)


#-------------------------------------------------------------------------------

# store implicit diatonic if set from chromatic specification
# if implicit, turing transpose, set to simplifyEnharmonic


class Interval(IntervalBase):
    '''
    An Interval class that encapsulates both :class:`~music21.interval.ChromaticInterval` and 
    :class:`~music21.interval.DiatonicInterval` objects all in one model. 

     The interval is specified either as named arguments, a 
     :class:`~music21.interval.DiatonicInterval` and 
     a :class:`~music21.interval.ChromaticInterval`, 
     or two :class:`~music21.note.Note` objects (or :class:`~music21.interval.Pitch` objects), 
     from which both a ChromaticInterval and DiatonicInterval are derived. 

    
    >>> n1 = note.Note('c3')
    >>> n2 = note.Note('c5')
    >>> aInterval = interval.Interval(noteStart=n1, noteEnd=n2)
    >>> aInterval
    <music21.interval.Interval P15>
    >>> aInterval.name
    'P15'
    >>> aInterval.noteStart is n1
    True
    >>> aInterval.noteEnd is n2
    True

    Reduce to less than an octave:

    >>> aInterval.simpleName
    'P1'
    
    Reduce to no more than an octave:

    >>> aInterval.semiSimpleName
    'P8'

    An interval can also be specified directly

    >>> aInterval = interval.Interval('m3')
    >>> aInterval
    <music21.interval.Interval m3>
    >>> aInterval = interval.Interval('M3')
    >>> aInterval
    <music21.interval.Interval M3>    
    
    >>> aInterval = interval.Interval('p5')
    >>> aInterval
    <music21.interval.Interval P5>
    >>> aInterval.isChromaticStep
    False
    >>> aInterval.isDiatonicStep
    False
    >>> aInterval.isStep
    False

    >>> aInterval = interval.Interval('half')
    >>> aInterval
    <music21.interval.Interval m2>
    >>> aInterval.isChromaticStep
    True
    >>> aInterval.isDiatonicStep
    True
    >>> aInterval.isStep
    True

    >>> aInterval = interval.Interval('-h')
    >>> aInterval
    <music21.interval.Interval m-2>
    >>> aInterval.directedName
    'm-2'
    >>> aInterval.name
    'm2'
    
    A single int is treated as a number of half-steps:
    
    >>> aInterval = interval.Interval(4)
    >>> aInterval
    <music21.interval.Interval M3>

    >>> aInterval = interval.Interval(7)
    >>> aInterval
    <music21.interval.Interval P5>
    
    If giving a starting note, an ending note has to be specified.
    
    >>> aInterval = interval.Interval(noteStart=n1, noteEnd=None)
    Traceback (most recent call last):
    music21.interval.IntervalException: either both the starting and the ending note must 
        be given or neither can be given.  You cannot have one without the other.

    An Interval can be constructed from a Diatonic and Chromatic Interval object (or just one)

    >>> diaInterval = interval.DiatonicInterval('major', 'third')
    >>> chrInterval = interval.ChromaticInterval(4)
    >>> fullInterval = interval.Interval(diatonic=diaInterval, chromatic=chrInterval)
    >>> fullInterval
    <music21.interval.Interval M3>

    >>> fullInterval = interval.Interval(diatonic=diaInterval)
    >>> fullInterval.semitones
    4
    >>> fullInterval = interval.Interval(chromatic=chrInterval)
    >>> fullInterval.diatonic.name
    'M3'
    >>> fullInterval.implicitDiatonic
    True

    Two Intervals are the same if their Chromatic and Diatonic intervals
    are the same.  N.B. that interval.Interval('a4') != 'a4' -- maybe it should...

    OMIT_FROM_DOCS
    
    >>> aInterval = interval.Interval('M2')
    >>> aInterval.isChromaticStep
    False
    >>> aInterval.isDiatonicStep
    True
    >>> aInterval.isStep
    True
    
    >>> aInterval = interval.Interval('dd3')
    >>> aInterval.isChromaticStep
    True
    >>> aInterval.isDiatonicStep
    False
    >>> aInterval.isStep
    True
    '''
#     requires either (1) a string ("P5" etc.) or    
#     (2) named arguments:
#     (2a) either both of
#        diatonic  = DiatonicInterval object
#        chromatic = ChromaticInterval object
#     (2b) or both of
#        _noteStart = Pitch (or Note) object
#        _noteEnd = Pitch (or Note) object
#     in which case it figures out the diatonic and chromatic intervals itself

    def __init__(self, *arguments, **keywords):
        IntervalBase.__init__(self)
        self.diatonic = None
        self.chromatic = None
        self.direction = None
        self.generic = None

        # these can be accessed through noteStart and noteEnd properties
        self._noteStart = None 
        self._noteEnd = None 
    
        self.type = "" # harmonic or melodic
        self.diatonicType = 0
        self.niceName = ""
        self.implicitDiatonic = False # is this basically a ChromaticInterval object in disguise?


        if len(arguments) == 1 and isinstance(arguments[0], six.string_types):
            # convert common string representations 
            dInterval, cInterval = _stringToDiatonicChromatic(arguments[0])
            self.diatonic = dInterval
            self.chromatic = cInterval

        # if we get a first argument that is a number, treat it as a chromatic
        # interval creation argument
        elif len(arguments) == 1 and common.isNum(arguments[0]):
            self.chromatic = ChromaticInterval(arguments[0])

        # permit pitches instead of Notes
        # this requires importing note, which is a bit circular, but necessary
        elif (len(arguments) == 2 
              and 'Pitch' in arguments[0].classes 
              and 'Pitch' in arguments[1].classes):
            from music21 import note
            self._noteStart = note.Note()
            self._noteStart.pitch = arguments[0]
            self._noteEnd = note.Note()
            self._noteEnd.pitch = arguments[1]

        elif (len(arguments) == 2 
              and hasattr(arguments[0], 'isNote') 
              and hasattr(arguments[1], 'isNote') 
              and arguments[0].isNote is True 
              and arguments[1].isNote is True):
            self._noteStart = arguments[0]
            self._noteEnd = arguments[1]
        else:
            if "diatonic" in keywords:
                self.diatonic = keywords['diatonic']
            if "chromatic" in keywords:
                self.chromatic = keywords['chromatic']                    
            if "noteStart" in keywords:
                self._noteStart = keywords['noteStart']
            if "noteEnd" in keywords:
                self._noteEnd = keywords['noteEnd']

        # this method will check for incorrectly defined attributes
        self.reinit()

    def reinit(self):
        '''
        Reinitialize the internal interval objects in case something has changed. 
        Called during __init__ to assign attributes.
        '''
        # catch case where only one Note is provided
        if ((self._noteStart is not None and self._noteEnd is None) or 
                (self._noteEnd is not None and self._noteStart is None)):
            raise IntervalException('either both the starting and the ending note must be ' +
                'given or neither can be given.  You cannot have one without the other.')

        if self._noteStart is not None and self._noteEnd is not None:
            genericInterval = notesToGeneric(self._noteStart, self._noteEnd)
            chromaticInterval = notesToChromatic(self._noteStart, self._noteEnd)
            diatonicInterval = intervalsToDiatonic(genericInterval, chromaticInterval)
            self.diatonic = diatonicInterval
            self.chromatic = chromaticInterval

        if self.chromatic is not None and self.diatonic is None:
            self.diatonic = self.chromatic.getDiatonic()
            self.implicitDiatonic = True

        if self.diatonic is not None and self.chromatic is None:
            self.chromatic = self.diatonic.getChromatic()            


        if self.chromatic is not None:
            self.direction = self.chromatic.direction
        elif self.diatonic is not None:
            self.direction = self.diatonic.generic.direction
        
        # both self.diatonic and self.chromatic can still both be None if an
        # empty Interval class is being created, such as in deepcopy
        if self.diatonic is not None:
            self.specifier = self.diatonic.specifier
            self.diatonicType = self.diatonic.specifier
            self.specificName = self.diatonic.specificName
            self.generic = self.diatonic.generic
    
            self.name = self.diatonic.name
            self.niceName = self.diatonic.niceName
            self.simpleName = self.diatonic.simpleName
            self.simpleNiceName = self.diatonic.simpleNiceName
            self.semiSimpleName = self.diatonic.semiSimpleName
            self.semiSimpleNiceName = self.diatonic.semiSimpleNiceName
            
            self.directedName = self.diatonic.directedName
            self.directedNiceName = self.diatonic.directedNiceName
            self.directedSimpleName = self.diatonic.directedSimpleName
            self.directedSimpleNiceName = self.diatonic.directedSimpleNiceName
    
            self.isDiatonicStep = self.diatonic.isDiatonicStep
        else:
            self.isDiatonicStep = False


        if self.chromatic is not None:   
            self.isChromaticStep = self.chromatic.isChromaticStep
            self.semitones = self.chromatic.semitones
        else:
            self.isChromaticStep = False

        self.isStep = self.isChromaticStep or self.isDiatonicStep

    def __repr__(self):
        from music21 import pitch
        shift = self._diatonicIntervalCentShift()
        if shift != 0:
            micro = pitch.Microtone(shift)
            return "<music21.interval.Interval %s %s>" % (self.directedName, micro)
        else:
            return "<music21.interval.Interval %s>" % self.directedName

    def isConsonant(self):
        '''
        returns True if the pitches are a major or minor third or sixth or perfect fifth or unison.

        These rules define all common-practice consonances (and earlier back to about 
        1300 all imperfect consonances)

        
        >>> i1 = interval.notesToInterval(note.Note('C'), note.Note('E'))
        >>> i1.isConsonant()
        True
        >>> i1 = interval.notesToInterval(note.Note('B-'), note.Note('C'))
        >>> i1.isConsonant()
        False
        ''' 
        if self.simpleName in ('P5', 'm3', 'M3', 'm6', 'M6', 'P1'):
            return True
        else:
            return False
        
    def __eq__(self, other):
        '''
        >>> a = interval.Interval('a4')
        >>> b = interval.Interval('d5')
        >>> c = interval.Interval('m3')
        >>> d = interval.Interval('d5')
        >>> a == b
        False
        >>> b == d
        True
        >>> a == c
        False
        >>> b in [a, c, d]
        True
        
        
        Now, of course, this makes sense:
        
        >>> a == 'hello'
        False
        
        
        But note well that this is also a False expression:
        
        
        >>> a == 'a4'
        False
        '''
        if other is None:
            return False
        elif not hasattr(other, 'diatonic') or not hasattr(other, 'chromatic'):
            return False

        if (self.diatonic == other.diatonic 
            and self.chromatic == other.chromatic):
            return True
        else:
            return False

    def _getComplement(self):
        return Interval(self.diatonic.mod7inversion)
    
    complement = property(_getComplement, 
        doc='''
        Return a new :class:`~music21.interval.Interval` object that is the 
        complement of this Interval.
        
        >>> aInterval = interval.Interval('M3')
        >>> bInterval = aInterval.complement
        >>> bInterval
        <music21.interval.Interval m6>

        >>> cInterval = interval.Interval('A2')
        >>> dInterval = cInterval.complement
        >>> dInterval
        <music21.interval.Interval d7>
        ''')


    def _getIntervalClass(self):
        return self.chromatic.intervalClass

    intervalClass = property(_getIntervalClass,
        doc = '''
        Return the interval class from the chromatic interval,
        that is, the lesser of the number of half-steps in the 
        simpleInterval or its complement.
        
        
        >>> aInterval = interval.Interval('M3')
        >>> aInterval.intervalClass
        4

        >>> bInterval = interval.Interval('m6')
        >>> bInterval.intervalClass
        4
        ''')



    def _getCents(self):
        return self.chromatic.cents

    cents = property(_getCents,
        doc = '''
        Return the cents from the chromatic interval, where 100 cents = a half-step

        
        >>> aInterval = interval.Interval('M3')
        >>> aInterval.cents
        400.0

        >>> n1 = note.Note("C4")
        >>> n2 = note.Note("D4")
        >>> n2.pitch.microtone = 30
        >>> microtoneInterval = interval.Interval(noteStart = n1, noteEnd = n2)
        >>> microtoneInterval.cents
        230.0
        ''')


    def _diatonicIntervalCentShift(self):
        '''
        Return the number of cents the diatonic 
        interval needs to be shifted to 
        correspond to microtonal value specified 
        in the chromatic interval.
        '''
        dCents = self.diatonic.cents
        cCents = self.chromatic.cents
        return cCents - dCents

    def transposePitch(self, 
                       p, 
                       reverse=False, 
                       maxAccidental=4):
        '''
        Given a :class:`~music21.pitch.Pitch` object, return a new, 
        transposed Pitch, that is transformed 
        according to this Interval. This is the main public interface to all 
        transposition routines found on higher-level objects. 

        The `maxAccidental` parameter sets an integer number of half step 
        alterations that will be accepted in the transposed pitch before it
        is simplified. For example, 
        a value of 2 will permit double sharps but not triple sharps.  The
        maxAccidental default is 4, because music21 does not support quintuple
        sharps/flats.  Set to None to try anyhow.
        
        
        >>> p1 = pitch.Pitch('A#4')
        >>> i = interval.Interval('m3')
        >>> p2 = i.transposePitch(p1)
        >>> p2
        <music21.pitch.Pitch C#5>
        >>> p2 = i.transposePitch(p1, reverse=True)
        >>> p2
        <music21.pitch.Pitch F##4>
        >>> i.transposePitch(p1, reverse=True, maxAccidental=1)
        <music21.pitch.Pitch G4>

        `Pitch` objects without octaves are transposed also into
        objects without octaves.  This might make them appear to be
        lower than the original even if transposed up:
        
        >>> anyA = pitch.Pitch('A')
        >>> anyC = i.transposePitch(anyA)
        >>> anyC
        <music21.pitch.Pitch C>
        >>> anyC.ps < anyA.ps  # !!
        True

        OMIT_FROM_DOCS
        TODO: More tests here, esp. on fundamental.
        
        
        >>> p1 = pitch.Pitch('C4')
        >>> i = interval.Interval(1)  # half-step, regardless of diatonic
        >>> p2 = i.transposePitch(p1)
        >>> p2
        <music21.pitch.Pitch C#4>
        >>> p3 = i.transposePitch(p2)
        >>> p3
        <music21.pitch.Pitch D4>
        
        '''
        if self.implicitDiatonic:
            # this will not preserve diatonic relationships
            pOut = self.chromatic.transposePitch(p)
        else:
            pOut = self._diatonicTransposePitch(p, reverse, maxAccidental)
        

        if p.fundamental is not None:
            # recursively call method
            pOut.fundamental = self.transposePitch(p.fundamental, 
                                                     reverse=reverse, 
                                                     maxAccidental=maxAccidental)
            if p.fundamental.octave is None:
                pOut.fundamental.octave = None
        
        return pOut
        
    def _diatonicTransposePitch(self, p, reverse, maxAccidental):
        '''
        abstracts out the diatonic aspects of transposing, so that implicitDiatonic and
        regular diatonic can use some of the same code.
        '''
        # NOTE: this is a performance critical method
        if p.octave is None:
            useImplicitOctave = True
        else:
            useImplicitOctave = False
        
        pitch1 = p
        pitch2 = copy.deepcopy(pitch1)
        oldDiatonicNum = pitch1.diatonicNoteNum
        #centsOrigin = pitch1.microtone.cents #unused!!
        distanceToMove = self.diatonic.generic.staffDistance

        if not reverse:
            newDiatonicNumber = (oldDiatonicNum + distanceToMove)
        else:
            newDiatonicNumber = (oldDiatonicNum - distanceToMove)

        newStep, newOctave = convertDiatonicNumberToStep(newDiatonicNumber)
        pitch2.step = newStep
        pitch2.octave = newOctave
        pitch2.accidental = None
        pitch2.microtone = None

        # have right note name but not accidental
        interval2 = notesToInterval(pitch1, pitch2)
        # halfStepsToFix already has any microtones
        if not reverse:
            halfStepsToFix = (self.chromatic.semitones -
                          interval2.chromatic.semitones)
        else:
            halfStepsToFix = (-self.chromatic.semitones -
                          interval2.chromatic.semitones)

        #environLocal.printDebug(['self', self, 'halfStepsToFix', halfStepsToFix, 
        #    'centsOrigin', centsOrigin, 'interval2', interval2])

        if halfStepsToFix != 0:
            while halfStepsToFix >= 12:
                halfStepsToFix = halfStepsToFix - 12
                pitch2.octave = pitch2.octave - 1

            # this will raise an exception if greater than 4        
            if (maxAccidental is not None and abs(halfStepsToFix) >   
                maxAccidental):
                # just create new pitch, directly setting the pitch space value
                #pitchAlt = copy.deepcopy(pitch2)
                #pitchAlt.ps = pitch2.ps + halfStepsToFix
                #environLocal.printDebug(
                #    'coercing pitch due to a transposition that requires an extreme ' + 
                #    'accidental: %s -> %s' % (pitch2, pitchAlt) )
                #pitch2 = pitchAlt
                pitch2.ps = pitch2.ps + halfStepsToFix
            else:
                pitch2.accidental = halfStepsToFix

            # inherit accidental display type etc. but not current status
            if pitch2.accidental is not None and pitch1.accidental is not None:
                pitch2.accidental.inheritDisplay(pitch1.accidental)
                pitch2.accidental.displayStatus = None # set accidental display to None

        if useImplicitOctave is True:
            pitch2.octave = None

        return pitch2


    def reverse(self):
        '''
        Return an reversed version of this interval. 
        If :class:`~music21.note.Note` objects are stored as
        `noteStart` and `noteEnd`, these notes are reversed. 

        
        >>> n1 = note.Note('c3')
        >>> n2 = note.Note('g3')
        >>> aInterval = interval.Interval(noteStart=n1, noteEnd=n2)
        >>> aInterval
        <music21.interval.Interval P5>
        >>> bInterval = aInterval.reverse()
        >>> bInterval
        <music21.interval.Interval P-5>
        >>> bInterval.noteStart is aInterval.noteEnd
        True
        
        >>> aInterval = interval.Interval('m3')
        >>> aInterval.reverse()
        <music21.interval.Interval m-3>
        '''
        if self._noteStart is not None and self._noteEnd is not None:
            return Interval(noteStart=self._noteEnd, noteEnd=self._noteStart)
        else:
            return Interval(diatonic=self.diatonic.reverse(),
                            chromatic=self.chromatic.reverse())

    def _setNoteStart(self, n):
        '''
        Assuming that this interval is defined, 
        we can set a new start note (_noteStart) and 
        automatically have the end note (_noteEnd).
        '''
        # this is based on the procedure found in transposePitch() and 
        # transposeNote() but offers a more object oriented approach
        self._noteStart = n
        pitch1 = n.pitch
        pitch2 = self.transposePitch(pitch1)
        self._noteEnd = copy.deepcopy(self._noteStart)
        self._noteEnd.pitch = pitch2

    def _getNoteStart(self):
        return self._noteStart

    noteStart = property(_getNoteStart, _setNoteStart, 
        doc = '''
        Assuming this Interval has been defined, set the start note to a new value; 
        this will adjust the value of the end note (`noteEnd`).
        
        
        >>> aInterval = interval.Interval('M3')
        >>> aInterval.noteStart = note.Note('c4')
        >>> aInterval.noteEnd.nameWithOctave
        'E4'

        >>> n1 = note.Note('c3')
        >>> n2 = note.Note('g#3')
        >>> aInterval = interval.Interval(n1, n2)
        >>> aInterval.name
        'A5'
        >>> aInterval.noteStart = note.Note('g4')
        >>> aInterval.noteEnd.nameWithOctave
        'D#5'

        >>> aInterval = interval.Interval('-M3')
        >>> aInterval.noteStart = note.Note('c4')
        >>> aInterval.noteEnd.nameWithOctave
        'A-3'

        >>> aInterval = interval.Interval('M-2')
        >>> aInterval.noteStart = note.Note('A#3')
        >>> aInterval.noteEnd.nameWithOctave
        'G#3'

        >>> aInterval = interval.Interval('h')
        >>> aInterval.directedName
        'm2'
        >>> aInterval.noteStart = note.Note('F#3')
        >>> aInterval.noteEnd.nameWithOctave
        'G3'
        ''')

    def _setNoteEnd(self, n):
        '''
        Assuming that this interval is defined, we can 
        set a new end note (_noteEnd) and automatically have the start note (_noteStart).
        '''
        # this is based on the procedure found in transposePitch() but offers
        # a more object oriented approach

        self._noteEnd = n
        pitch2 = n.pitch
        pitch1 = self.transposePitch(pitch2, reverse=True)
        self._noteStart = copy.deepcopy(self._noteEnd)
        self._noteStart.pitch = pitch1

    def _getNoteEnd(self):
        return self._noteEnd

    noteEnd = property(_getNoteEnd, _setNoteEnd, 
        doc = '''
        Assuming this Interval has been defined, set the 
        end note to a new value; this will adjust 
        the value of the start note (`noteStart`).

        
        >>> aInterval = interval.Interval('M3')
        >>> aInterval.noteEnd = note.Note('e4')
        >>> aInterval.noteStart.nameWithOctave
        'C4'

        >>> aInterval = interval.Interval('m2')
        >>> aInterval.noteEnd = note.Note('A#3')
        >>> aInterval.noteStart.nameWithOctave
        'G##3'

        >>> n1 = note.Note('g#3')
        >>> n2 = note.Note('c3')
        >>> aInterval = interval.Interval(n1, n2)
        >>> aInterval.directedName # downward augmented fifth
        'A-5'
        >>> aInterval.noteEnd = note.Note('c4')
        >>> aInterval.noteStart.nameWithOctave
        'G#4'

        >>> aInterval = interval.Interval('M3')
        >>> aInterval.noteEnd = note.Note('A-3')
        >>> aInterval.noteStart.nameWithOctave
        'F-3'

         ''')




#-------------------------------------------------------------------------------
def getWrittenHigherNote(note1, note2):
    '''
    Given two :class:`~music21.note.Note` or :class:`~music21.pitch.Pitch` objects, 
    this function returns the higher object based on diatonic note
    numbers. Returns the note higher in pitch if the diatonic number is
    the same, or the first note if pitch is also the same.

    
    >>> cis = pitch.Pitch("C#")
    >>> deses = pitch.Pitch("D--")
    >>> higher = interval.getWrittenHigherNote(cis, deses)
    >>> higher is deses
    True

    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d-3')
    >>> interval.getWrittenHigherNote(aNote, bNote)
    <music21.note.Note D->

    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> interval.getWrittenHigherNote(aNote, bNote)
    <music21.note.Note D-->
    '''
    
    num1 = note1.diatonicNoteNum
    num2 = note2.diatonicNoteNum
    if num1 > num2: 
        return note1
    elif num1 < num2: 
        return note2
    else: 
        return getAbsoluteHigherNote(note1, note2)

def getAbsoluteHigherNote(note1, note2):
    '''
    Given two :class:`~music21.note.Note` objects, 
    returns the higher note based on actual frequency.
    If both pitches are the same, returns the first note given.

    
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> interval.getAbsoluteHigherNote(aNote, bNote)
    <music21.note.Note C#>
    '''
    chromatic = notesToChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0: 
        return note2
    elif semitones < 0: 
        return note1
    else: 
        return note1

def getWrittenLowerNote(note1, note2):
    '''
    Given two :class:`~music21.note.Note` objects, 
    returns the lower note based on diatonic note
    number. Returns the note lower in pitch if the diatonic number is
    the same, or the first note if pitch is also the same.

    
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> interval.getWrittenLowerNote(aNote, bNote)
    <music21.note.Note C#>

    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d-3')
    >>> interval.getWrittenLowerNote(aNote, bNote)
    <music21.note.Note C#>
    '''
    num1 = note1.diatonicNoteNum
    num2 = note2.diatonicNoteNum
    if num1 < num2: 
        return note1
    elif num1 > num2: 
        return note2
    else: 
        return getAbsoluteLowerNote(note1, note2)

def getAbsoluteLowerNote(note1, note2):
    '''
    Given two :class:`~music21.note.Note` objects, returns 
    the lower note based on actual pitch.
    If both pitches are the same, returns the first note given.

    
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> interval.getAbsoluteLowerNote(aNote, bNote)
    <music21.note.Note D-->
    '''
    chromatic = notesToChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0: 
        return note1
    elif semitones < 0: 
        return note2
    else: 
        return note1

def transposePitch(pitch1, interval1):
    '''
    Given a :class:`~music21.pitch.Pitch` 
    and a :class:`~music21.interval.Interval` object (Not another class such
    as ChromaticInterval) or a string such as 'P5' or a number such as 6 (=tritone), 
    return a new Pitch object at the appropriate pitch level. 
    
    >>> aPitch = pitch.Pitch('C4')
    >>> aInterval = interval.Interval('P5')
    >>> bPitch = interval.transposePitch(aPitch, aInterval)
    >>> bPitch
    <music21.pitch.Pitch G4>
    >>> bInterval = interval.Interval('P-5')
    >>> cPitch = interval.transposePitch(aPitch, bInterval)
    >>> cPitch
    <music21.pitch.Pitch F3>
    
    Pitches with implicit octaves should work,
    
    >>> dPitch = pitch.Pitch('G')
    >>> ePitch = interval.transposePitch(dPitch, aInterval)
    >>> ePitch
    <music21.pitch.Pitch D>
    ''' 

    # check if interval1 is a string,
    # then convert it to interval object if necessary
    if isinstance(interval1, six.string_types) or isinstance(interval1, int):
        interval1 = Interval(interval1) 
    else:
        if not hasattr(interval1, 'transposePitch'):
            raise IntervalException(
                'interval must be a music21.interval.Interval object not {}'.format(
                                                            interval1.__class__.__name__))
    return interval1.transposePitch(pitch1)

def transposeNote(note1, intervalString):
    '''
    Given a :class:`~music21.note.Note` and 
    a interval string (such as 'P5') or an Interval object, 
    return a new Note object at the appropriate pitch level. 

    
    >>> aNote = note.Note('c4')
    >>> bNote = interval.transposeNote(aNote, 'p5')
    >>> bNote
    <music21.note.Note G>
    >>> bNote.pitch
    <music21.pitch.Pitch G4>

    >>> aNote = note.Note('f#4')
    >>> bNote = interval.transposeNote(aNote, 'm2')
    >>> bNote
    <music21.note.Note G>
    '''
    newPitch = transposePitch(note1.pitch, intervalString)
    newNote = copy.deepcopy(note1)
    newNote.pitch = newPitch
    return newNote


def notesToInterval(n1, n2 = None):  
    '''
    Given two :class:`~music21.note.Note` objects, returns an 
    :class:`~music21.interval.Interval` object. The same 
    functionality is available by calling the Interval class 
    with two Notes as arguments.
    
    Works equally well with :class:`~music21.pitch.Pitch` objects.


    N.B.: MOVE TO PRIVATE USE.  Use: inverval.Interval(noteStart=aNote, noteEnd=bNote) instead.
    Do not remove because used in interval.Interval()! 
    
    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g5')
    >>> aInterval = interval.notesToInterval(aNote, bNote)
    >>> aInterval
    <music21.interval.Interval P12>

    >>> bInterval = interval.Interval(noteStart=aNote, noteEnd=bNote)
    >>> aInterval.niceName == bInterval.niceName
    True

    >>> aPitch = pitch.Pitch('c#4')
    >>> bPitch = pitch.Pitch('f-5')
    >>> cInterval = interval.notesToInterval(aPitch, bPitch)
    >>> cInterval
    <music21.interval.Interval dd11>

    >>> cPitch = pitch.Pitch('e#4')
    >>> dPitch = pitch.Pitch('f-4')
    >>> dInterval = interval.notesToInterval(cPitch, dPitch)
    >>> dInterval
    <music21.interval.Interval dd2>

    >>> ePitch = pitch.Pitch('e##4')
    >>> fPitch = pitch.Pitch('f--4')
    >>> dInterval = interval.notesToInterval(ePitch, fPitch)
    >>> dInterval
    <music21.interval.Interval dddd2>

    >>> gPitch = pitch.Pitch('c--4')
    >>> hPitch = pitch.Pitch('c##4')
    >>> iInterval = interval.notesToInterval(gPitch, hPitch)
    >>> iInterval
    <music21.interval.Interval AAAA1>

    >>> interval.notesToInterval(pitch.Pitch('e##4'), pitch.Pitch('f--5'))
    <music21.interval.Interval dddd9>
    '''
    #note to self:  what's going on with the Note() representation in help?
    if n2 is None: 
        # this is not done in the constructor originally because of looping problems 
        # with tinyNotationNote
        # but also because we now support Pitches as well
        if hasattr(n1, 'pitch'):
            from music21 import note
            n2 = note.Note()
        else:
            from music21 import pitch
            n2 = pitch.Pitch() 
    gInt = notesToGeneric(n1, n2)
    cInt = notesToChromatic(n1, n2)
    intObj = intervalFromGenericAndChromatic(gInt, cInt)
    intObj._noteStart = n1  #use private so as not to trigger resetting behavior
    intObj._noteEnd = n2
    return intObj

def add(intervalList):
    '''
    Add a list of intervals and return the composite interval
    Intervals can be Interval objects or just strings.
    
    (Currently not particularly efficient for large lists...)
    
    >>> A2 = interval.Interval('A2')
    >>> P5 = interval.Interval('P5')
    
    >>> interval.add([A2, P5])
    <music21.interval.Interval A6>
    >>> interval.add([P5, "m2"])
    <music21.interval.Interval m6>
    >>> interval.add(["W","W","H","W","W","W","H"])
    <music21.interval.Interval P8>
    
    Direction does matter:
    
    >>> interval.add([P5, "P-4"])
    <music21.interval.Interval M2>
    '''
    from music21 import pitch
    if len(intervalList) == 0:
        raise IntervalException("Cannot add an empty set of intervals")
    
    n1 = pitch.Pitch("C4") # need octave to not be implicit...
    n2 = pitch.Pitch("C4")
    for i in intervalList:
        n2 = transposePitch(n2, i)
    return Interval(noteStart=n1, noteEnd=n2)
    

def subtract(intervalList):
    '''
    Starts with the first interval and subtracts the 
    following intervals from it:
    
    >>> interval.subtract(["P5","M3"])
    <music21.interval.Interval m3>
    >>> interval.subtract(["P4","d3"])
    <music21.interval.Interval A2>
    
    >>> m2Object = interval.Interval("m2")
    >>> interval.subtract(["M6","m2",m2Object])
    <music21.interval.Interval AA4>
    >>> interval.subtract(["P4", "M-2"])
    <music21.interval.Interval P5>
    >>> interval.subtract(["A2","A2"])
    <music21.interval.Interval P1>
    >>> interval.subtract(["A1","P1"])
    <music21.interval.Interval A1>
    
    >>> interval.subtract(["P8","P1"])
    <music21.interval.Interval P8>
    >>> interval.subtract(["P8","d2"])
    <music21.interval.Interval A7>
    >>> interval.subtract(["P8","A1"])
    <music21.interval.Interval d8>

    
    >>> a = interval.subtract(["P5","A5"])
    >>> a.niceName
    'Diminished Unison'
    >>> a.directedNiceName
    'Descending Diminished Unison'
    >>> a.chromatic.semitones
    -1    
    
    '''
    from music21 import pitch
    if len(intervalList) == 0:
        raise IntervalException("Cannot add an empty set of intervals")
    
    n1 = pitch.Pitch("C4")
    n2 = pitch.Pitch("C4")
    for i,intI in enumerate(intervalList):
        if i == 0:
            n2 = transposePitch(n2, intI)
        else:
            if not hasattr(intI, "chromatic"):
                intervalObj = Interval(intI)
            else:
                intervalObj = intI
            n2 = transposePitch(n2, intervalObj.reverse())
    #print n1.nameWithOctave, n2.nameWithOctave
    return Interval(noteStart=n1, noteEnd=n2)

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testFirst(self):       
        from music21.note import Note
        from music21.pitch import Accidental
        n1 = Note()
        n2 = Note()
        
        n1.step = "C"
        n1.octave = 4
        
        n2.step = "B"
        n2.octave = 5
        n2.accidental = Accidental("-")
        
        #int1 = interval.notesToInterval(n1, n2)   # returns music21.interval.Interval object
        int1  = Interval(noteStart = n1, noteEnd = n2)
        dInt1 = int1.diatonic # returns same as gInt1 -- just a different way of thinking of things
        gInt1 = dInt1.generic
    
        self.assertEqual(gInt1.isDiatonicStep, False)
        self.assertEqual(gInt1.isSkip, True)
        
        n1.accidental = Accidental("#")
        int1.reinit()
        
        cInt1 = notesToChromatic(n1,n2) # returns music21.interval.ChromaticInterval object
        cInt2 = int1.chromatic # returns same as cInt1 -- a different way of thinking of things
        self.assertEqual(cInt1.semitones, cInt2.semitones)
        
        self.assertEqual(int1.simpleNiceName, "Diminished Seventh")

        self.assertEqual(int1.directedSimpleNiceName, "Ascending Diminished Seventh")
        self.assertEqual(int1.name, "d14")
        self.assertEqual(int1.specifier, DIMINISHED)
        
        self.assertEqual(gInt1.directed, 14)
        self.assertEqual(gInt1.undirected, 14)
        self.assertEqual(gInt1.simpleDirected, 7)
        self.assertEqual(gInt1.simpleUndirected, 7)
        
        self.assertEqual(cInt1.semitones, 21)
        self.assertEqual(cInt1.undirected, 21)
        self.assertEqual(cInt1.mod12, 9)
        self.assertEqual(cInt1.intervalClass, 3)
        
        n4 = Note()
        n4.step = "D"
        n4.octave = 3
        n4.accidental = "-"
        
        ##n3 = interval.transposePitch(n4, "AA8")
        ##if n3.accidental is not None:
        ##    print n3.step, n3.accidental.name, n3.octave
        ##else:
        ##    print n3.step, n3.octave
        ##print n3.name
        ##print
     
        cI = ChromaticInterval (-14)
        self.assertEqual(cI.semitones, -14)
        self.assertEqual(cI.cents, -1400)
        self.assertEqual(cI.undirected, 14)
        self.assertEqual(cI.mod12, 10)
        self.assertEqual(cI.intervalClass, 2)
    
        lowB = Note()
        lowB.name = "B"
        highBb = Note()
        highBb.name = "B-"
        highBb.octave = 5
        dimOct = notesToInterval(lowB, highBb)
        self.assertEqual(dimOct.niceName, "Diminished Octave")
    
        noteA1 = Note()
        noteA1.name = "E-"
        noteA1.octave = 4
        noteA2 = Note()
        noteA2.name = "F#"
        noteA2.octave = 5
        intervalA1 = notesToInterval(noteA1, noteA2)
    
        noteA3 = Note()
        noteA3.name = "D"
        noteA3.octave = 1
    
        noteA4 = transposeNote(noteA3, intervalA1)
        self.assertEqual(noteA4.name, "E#")
        self.assertEqual(noteA4.octave, 2)
        
        interval1 = Interval("P-5")
        
        n5 = transposeNote(n4, interval1)
        n6 = transposeNote(n4, "P-5")
        self.assertEqual(n5.name, "G-")
        self.assertEqual(n6.name, n5.name)
        n7 = Note()
        n8 = transposeNote(n7, "P8")
        self.assertEqual(n8.name, "C")
        self.assertEqual(n8.octave, 5)

        ## same thing using newer syntax:
        
        interval1 = Interval("P-5")
        
        n5 = transposeNote(n4, interval1)
        n6 = transposeNote(n4, "P-5")
        self.assertEqual(n5.name, "G-")
        self.assertEqual(n6.name, n5.name)
        n7 = Note()
        n8 = transposeNote(n7, "P8")
        self.assertEqual(n8.name, "C")
        self.assertEqual(n8.octave, 5)

        
        n9 = transposeNote(n7, "m7")  ## should be B-
        self.assertEqual(n9.name, "B-")
        self.assertEqual(n9.octave, 4)
        n10 = transposeNote(n7, "dd-2")  ## should be B##
        self.assertEqual(n10.name, "B##")
        self.assertEqual(n10.octave, 3)
    
        ## test getWrittenHigherNote fuctions
        (nE, nEsharp, nFflat, nF1, nF2) = (Note(), Note(), Note(), Note(), Note())
        
        nE.name      = "E"
        nEsharp.name = "E#"
        nFflat.name  = "F-"
        nF1.name     = "F"
        nF2.name     = "F"
        
        higher1 = getWrittenHigherNote(nE, nEsharp)
        higher2 = getWrittenHigherNote(nEsharp, nFflat)
        higher3 = getWrittenHigherNote(nF1, nF2)
        
        self.assertEqual(higher1, nEsharp)
        self.assertEqual(higher2, nFflat)
        self.assertEqual(higher3, nF1)  ### in case of ties, first is returned
        
        higher4 = getAbsoluteHigherNote(nE, nEsharp)
        higher5 = getAbsoluteHigherNote(nEsharp, nFflat)
        higher6 = getAbsoluteHigherNote(nEsharp, nF1)
        higher7 = getAbsoluteHigherNote(nF1, nEsharp)
        
        self.assertEqual(higher4, nEsharp)
        self.assertEqual(higher5, nEsharp)
        self.assertEqual(higher6, nEsharp)
        self.assertEqual(higher7, nF1)
        
        lower1 = getWrittenLowerNote(nEsharp, nE)
        lower2 = getWrittenLowerNote(nFflat, nEsharp)
        lower3 = getWrittenLowerNote(nF1, nF2)
        
        self.assertEqual(lower1, nE)
        self.assertEqual(lower2, nEsharp)
        self.assertEqual(lower3, nF1)  ## still returns first.
        
        lower4 = getAbsoluteLowerNote(nEsharp, nE)
        lower5 = getAbsoluteLowerNote(nFflat, nEsharp)
        lower6 = getAbsoluteLowerNote(nEsharp, nF1)
        
        self.assertEqual(lower4, nE)
        self.assertEqual(lower5, nFflat)
        self.assertEqual(lower6, nEsharp)
    
        middleC = Note()
        lowerC  = Note()
        lowerC.octave = 3
        descendingOctave = notesToInterval(middleC, lowerC)
        self.assertEqual(descendingOctave.generic.simpleDirected, 1)  
        # no descending unisons ever
        self.assertEqual(descendingOctave.generic.semiSimpleDirected, -8)  
        # no descending unisons ever
        self.assertEqual(descendingOctave.directedName, "P-8")
        self.assertEqual(descendingOctave.directedSimpleName, "P1")
    
        lowerG  = Note()
        lowerG.name = "G"
        lowerG.octave = 3
        descendingFourth = notesToInterval(middleC, lowerG)
        self.assertEqual(descendingFourth.diatonic.directedNiceName, "Descending Perfect Fourth")
        self.assertEqual(descendingFourth.diatonic.directedSimpleName, "P-4")
        self.assertEqual(descendingFourth.diatonic.simpleName, "P4")
        self.assertEqual(descendingFourth.diatonic.mod7, "P5")
        
        perfectFifth = descendingFourth.complement
        self.assertEqual(perfectFifth.niceName, "Perfect Fifth")
        self.assertEqual(perfectFifth.diatonic.simpleName, "P5")
        self.assertEqual(perfectFifth.diatonic.mod7, "P5")
        self.assertEqual(perfectFifth.complement.niceName, "Perfect Fourth")


    def testCreateIntervalFromPitch(self):     
        from music21 import pitch  
        p1 = pitch.Pitch('c')
        p2 = pitch.Pitch('g')
        i = Interval(p1, p2)
        self.assertEqual(i.intervalClass, 5)


    def testTransposeImported(self):

        def collectAccidentalDisplayStatus(s):
            post = []
            for e in s.flat.notes:
                if e.pitch.accidental != None:
                    post.append(e.pitch.accidental.displayStatus)
                else: # mark as not having an accidental
                    post.append('x')
            return post

        from music21 import corpus
        s = corpus.parse('bach/bwv66.6')
        # this has accidentals in measures 2 and 6
        sSub = s.parts[3].measures(2,6)
        
        self.assertEqual(collectAccidentalDisplayStatus(sSub), 
                        ['x', False, 'x', 'x', True, False, 'x', False, False, False, 
                         False, False, False, 'x', 'x', 'x', False, False, False, 
                         'x', 'x', 'x', 'x', True, False])

        sTransposed = sSub.flat.transpose('p5')
        #sTransposed.show()

        self.assertEqual(collectAccidentalDisplayStatus(sTransposed), 
                        ['x', None, 'x', 'x', None, None, None, None, None, 
                         None, None, None, None, 'x', None, None, None, None, 
                         None, 'x', 'x', 'x', None, None, None])



    def testIntervalMicrotonesA(self):
        from music21 import interval, pitch

        i = interval.Interval('m3')
        self.assertEqual(i.chromatic.cents, 300)
        self.assertEqual(i.cents, 300.0)

        i = interval.Interval('p5')
        self.assertEqual(i.chromatic.cents, 700)
        self.assertEqual(i.cents, 700.0)

        i = interval.Interval(8)
        self.assertEqual(i.chromatic.cents, 800)
        self.assertEqual(i.cents, 800.0)

        i = interval.Interval(8.5)
        self.assertEqual(i.chromatic.cents, 850.0)
        self.assertEqual(i.cents, 850.0)


        i = interval.Interval(5.25) # a sharp p4
        self.assertEqual(i.cents, 525.0)
        # we can subtract the two to get an offset
        self.assertEqual(i.cents, 525.0)
        self.assertEqual(str(i), '<music21.interval.Interval P4 (+25c)>')
        self.assertEqual(i._diatonicIntervalCentShift(), 25)

        i = interval.Interval(4.75) # a flat p4
        self.assertEqual(str(i), '<music21.interval.Interval P4 (-25c)>')
        self.assertEqual(i._diatonicIntervalCentShift(), -25)

        i = interval.Interval(4.48) # a sharp M3
        self.assertEqual(str(i), '<music21.interval.Interval M3 (+48c)>')
        self.assertAlmostEqual(i._diatonicIntervalCentShift(), 48.0)

        i = interval.Interval(4.5) # a sharp M3
        self.assertEqual(str(i), '<music21.interval.Interval M3 (+50c)>')
        self.assertAlmostEqual(i._diatonicIntervalCentShift(), 50.0)


        i = interval.Interval(5.25) # a sharp p4
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F4(+25c)')

        i = interval.Interval(5.80) # a sharp p4
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F#4(-20c)')

        i = interval.Interval(6.00) # an exact Tritone
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F#4')


        i = interval.Interval(5) # a chromatic p4
        p1 = pitch.Pitch('c4')
        p1.microtone = 10 #c+20
        self.assertEqual(str(p1), 'C4(+10c)')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F4(+10c)')

        i = interval.Interval(7.20) # a sharp P5
        p1 = pitch.Pitch('c4')
        p1.microtone = -20 #c+20
        self.assertEqual(str(p1), 'C4(-20c)')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'G4')


        i = interval.Interval(7.20) # a sharp P5
        p1 = pitch.Pitch('c4')
        p1.microtone = 80 #c+20
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'G#4')


        i = interval.Interval(0.20) # a sharp unison
        p1 = pitch.Pitch('e4')
        p1.microtone = 10
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E~4(-20c)')


        i = interval.Interval(0.05) # a tiny bit sharp unison
        p1 = pitch.Pitch('e4')
        p1.microtone = 5 
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E4(+10c)')


        i = interval.Interval(12.05) # a tiny bit sharp octave
        p1 = pitch.Pitch('e4')
        p1.microtone = 5 
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E5(+10c)')


        i = interval.Interval(11.85) # a flat octave
        p1 = pitch.Pitch('e4')
        p1.microtone = 5 
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E5(-10c)')


        i = interval.Interval(11.85) # a flat octave
        p1 = pitch.Pitch('e4')
        p1.microtone = -20
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E`5(+15c)')



    def testIntervalMicrotonesB(self):
        from music21 import interval, note
        i = interval.notesToInterval(note.Note('c4'), note.Note('c#4'))
        self.assertEqual(str(i), '<music21.interval.Interval A1>')

        i = interval.notesToInterval(note.Note('c4'), note.Note('c~4'))
        self.assertEqual(str(i), '<music21.interval.Interval A1 (-50c)>')

    def testDescendingAugmentedUnison(self):
        from music21 import interval, note
        ns = note.Note("C4")
        ne = note.Note("C-4")
        i = interval.Interval(noteStart=ns, noteEnd=ne)
        directedNiceName = i.directedNiceName
        self.assertEqual(directedNiceName, "Descending Diminished Unison")

    def testTransposeWithChromaticInterval(self):
        from music21 import interval, note
        ns = note.Note("C4")
        i = interval.ChromaticInterval(5)
        n2 = ns.transpose(i)
        self.assertEqual(n2.nameWithOctave, "F4")

        ns = note.Note("B#3")
        i = interval.ChromaticInterval(5)
        n2 = ns.transpose(i)
        self.assertEqual(n2.nameWithOctave, "F4")

        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [notesToChromatic, intervalsToDiatonic, 
        intervalFromGenericAndChromatic, 
              Interval]



if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof


