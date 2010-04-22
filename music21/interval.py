#-------------------------------------------------------------------------------
# Name:         interval.py
# Purpose:      music21 classes for representing intervals
#
# Authors:      Michael Scott Cuthbert
#               Jackie Rogoff
#               Amy Hailes 
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
"""Interval.py is a module for creating and manipulating interval objects.
Included classes are Interval, DiatonicInterval, GenericInterval, and ChromaticInterval.

There are also a number of useful lists included in the module.

"""

import copy
import math
import unittest, doctest

import music21
from music21 import common 

#from music21 import pitch # SHOULD NOT, b/c of enharmonics

from music21 import environment
_MOD = "interval.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
# constants

STEPNAMES = ['C','D','E','F','G','A','B']

DESCENDING = -1
OBLIQUE    = 0
ASCENDING  = 1
directionTerms = {DESCENDING:"Descending", 
                  OBLIQUE:"Oblique", 
                  ASCENDING:"Ascending"}

# specifiers are derived from these two lists; 
# perhaps better represented with a dictionary
# perhaps the first entry, below, should be None, like in prefixSpecs?
niceSpecNames = ['ERROR', 'Perfect', 'Major', 'Minor', 'Augmented', 'Diminished', 'Doubly-Augmented', 'Doubly-Diminished', 'Triply-Augmented', 'Triply-Diminished']
prefixSpecs = [None, 'P', 'M', 'm', 'A', 'd', 'AA', 'dd', 'AAA', 'ddd']

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

# ordered list of perfect specifiers
orderedPerfSpecs = ['ddd', 'dd', 'd', 'P', 'A', 'AA', 'AAA']
perfSpecifiers = [TRPDIM, DBLDIM, DIMINISHED, PERFECT, 
                  AUGMENTED, DBLAUG, TRPAUG]
perfOffset = 3 # that is, Perfect is third on the list.s

# ordered list of imperfect specifiers
orderedImperfSpecs = ['ddd', 'dd', 'd', 'm', 'M', 'A', 'AA', 'AAA']
# why is this not called imperfSpecifiers?
specifiers = [TRPDIM, DBLDIM, DIMINISHED, MINOR, MAJOR, 
              AUGMENTED, DBLAUG, TRPAUG]
majOffset  = 4 # index of Major

# the following dictionaries provide half step shifts given key values
# either as integers (generic) or as strings (adjust perfect/imprefect)
#assuming Perfect or Major
semitonesGeneric = {1:0, 2:2, 3:4, 4:5, 5:7, 6:9, 7:11} 
semitonesAdjustPerfect = {"P":0, "A":1, "AA":2, "AAA":3, 
                          "d":-1, "dd":-2, "ddd":-3} #offset from Perfect
semitonesAdjustImperf = {"M":0, "m":-1, "A":1, "AA":2, "AAA":3, 
                         "d":-2, "dd":-3, "ddd":-4} #offset from Major


#-------------------------------------------------------------------------------
class IntervalException(Exception):
    pass


#-------------------------------------------------------------------------------
# some utility functions



def convertStaffDistanceToInterval(staffDist):
    '''Returns the interval number from the given staff distance.

    >>> convertStaffDistanceToInterval(3)
    4
    >>> convertStaffDistanceToInterval(7)
    8
    '''
    if staffDist == 0:
        return 1
    elif staffDist > 0:
        return staffDist + 1
    else:
        return staffDist - 1


def convertDiatonicNumberToStep(dn):
    '''Convert a diatonic number to a step name and a octave integer. 

    >>> convertDiatonicNumberToStep(15)
    ('C', 2)
    >>> convertDiatonicNumberToStep(23)
    ('D', 3)
    >>> convertDiatonicNumberToStep(0)
    ('C', 0)
    >>> convertDiatonicNumberToStep(1)
    ('C', 0)
    >>> convertDiatonicNumberToStep(2)
    ('D', 0)
    >>> convertDiatonicNumberToStep(3)
    ('E', 0)
    >>> convertDiatonicNumberToStep(4)
    ('F', 0)
    >>> convertDiatonicNumberToStep(5)
    ('G', 0)
    '''
    remainder, octave = math.modf((dn-1)/7.0)
    # what is .001 doing here?
    return STEPNAMES[int((remainder*7)+.001)], int(octave)


def convertSpecifier(specifier):
    '''Given an integer or a string, return the integer for the appropriate specifier. This permits specifiers to specified in a flexible manner.

    >>> convertSpecifier(3)
    (3, 'm')
    >>> convertSpecifier('p')
    (1, 'P')
    >>> convertSpecifier('P')
    (1, 'P')
    >>> convertSpecifier('M')
    (2, 'M')
    >>> convertSpecifier('major')
    (2, 'M')
    >>> convertSpecifier('m')
    (3, 'm')
    >>> convertSpecifier('Augmented')
    (4, 'A')
    >>> convertSpecifier('a')
    (4, 'A')
    >>> convertSpecifier(None)
    (None, None)
    '''
    post = None
    postStr = None
    if common.isNum(specifier):
        post = specifier
    # check string matches
    if common.isStr(specifier):
        if specifier in prefixSpecs:
            post = prefixSpecs.index(specifier)
        # permit specifiers as prefixes without case; this will not distinguish
        # between m and M, but was taken care of in the line above
        elif specifier.lower() in [x.lower() for x in prefixSpecs[1:]]:    
            for i in range(len(prefixSpecs)):
                if prefixSpecs[i] == None: continue
                if specifier.lower() == prefixSpecs[i].lower():
                    post = i
                    break

        elif specifier.lower() in [x.lower() for x in niceSpecNames[1:]]:    
            for i in range(len(niceSpecNames)):
                if niceSpecNames[i] == None: continue
                if specifier.lower() == niceSpecNames[i].lower():
                    post = i
                    break
    # if no match or None, None will be returned
    if post != None:
        postStr = prefixSpecs[post]
    return post, postStr


def convertGeneric(value):
    '''Convert an interval specified in terms of its name (second, third) into an integer. If integers are passed, assume the are correct.

    >>> convertGeneric(3)
    3
    >>> convertGeneric('third')
    3
    >>> convertGeneric('3rd')
    3
    >>> convertGeneric('octave')
    8
    >>> convertGeneric('twelfth')
    12
    >>> convertGeneric('descending twelfth')
    -12
    >>> convertGeneric(12)
    12
    >>> convertGeneric(-12)
    -12
    '''
    post = None
    if common.isNum(value):
        post = value
        directionScalar = 1 # may still be negative

    elif common.isStr(value):
        # first, see if there is a direction term
        directionScalar = ASCENDING # assume ascending
        for dir in [DESCENDING, ASCENDING]:
            if directionTerms[dir].lower() in value.lower():
                directionScalar = dir # assign numeric value
                # strip direction
                value = value.lower()
                value = value.replace(directionTerms[dir].lower(), '')
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
    if post != None:
        post = post * directionScalar
    return post


def convertSemitoneToSpecifierGeneric(count):
    '''Given a number of semitones, return a default diatonic specifier.

    >>> convertSemitoneToSpecifierGeneric(0)
    ('P', 1)
    >>> convertSemitoneToSpecifierGeneric(-2)
    ('M', -2)
    >>> convertSemitoneToSpecifierGeneric(1)
    ('m', 2)
    >>> convertSemitoneToSpecifierGeneric(7)
    ('P', 5)
    >>> convertSemitoneToSpecifierGeneric(11)
    ('M', 7)
    >>> convertSemitoneToSpecifierGeneric(12)
    ('P', 8)
    >>> convertSemitoneToSpecifierGeneric(13)
    ('m', 9)
    >>> convertSemitoneToSpecifierGeneric(-15)
    ('m', -10)
    >>> convertSemitoneToSpecifierGeneric(24)
    ('P', 15)
    '''
    if count < 0: 
        dirScale = -1
    else:
        dirScale = 1
    # use mod 13 here to get 12th value
    size = abs(count) % 12
    oct = abs(count) // 12 # let floor to int 

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

    return spec, (generic+(oct*7)) * dirScale
    


#-------------------------------------------------------------------------------
class GenericInterval(music21.Music21Object):
    '''
    A GenericInterval is an interval such as Third, Seventh, Octave, or Tenth.
    Constructor takes an integer or string specifying the interval and direction. 

    The interval is not specified in half-steps, but in numeric values derived from interval names: a Third is 3; a Seventh is 7, etc. String values for interval names ('3rd' or 'third') are accepted.
    
    staffDistance: the number of lines or spaces apart;  
        E.g. C4 to C4 = 0;  C4 to D4 = 1;  C4 to B3 = -1
    '''
    
    def __init__(self, value):
        '''
        >>> aInterval = GenericInterval(3)
        >>> aInterval.direction
        1
        >>> aInterval.perfectable
        False
        >>> aInterval.staffDistance
        2

        >>> aInterval = GenericInterval('Third')
        >>> aInterval.staffDistance
        2

        >>> aInterval = GenericInterval(-12)
        >>> aInterval.perfectable
        True
        >>> aInterval.staffDistance
        -11
        >>> aInterval.mod7
        4
        >>> bInterval = aInterval.complement()
        >>> bInterval.staffDistance
        3

        >>> aInterval = GenericInterval('descending twelfth')
        >>> aInterval.perfectable
        True
        >>> aInterval.staffDistance
        -11

        >>> aInterval = GenericInterval(0)
        Traceback (most recent call last):
        IntervalException: The Zeroth is not an interval

        '''
        music21.Music21Object.__init__(self)

        self.value = convertGeneric(value)
        self.directed = self.value
        self.undirected = abs(self.value)

        if self.directed == 1:
            self.direction = OBLIQUE
        elif self.directed == -1:
            raise IntervalException("Descending P1s not allowed")
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

        if self.undirected == 2: self.isStep = True
        else: self.isStep = False
        
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
        
        self.niceName = common.musicOrdinals[self.undirected]
        self.simpleNiceName = common.musicOrdinals[self.simpleUndirected]
        self.semiSimpleNiceName = common.musicOrdinals[self.semiSimpleUndirected]

        if self.directed == 1:
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
            self.mod7 = self.mod7inversion  ## see chord.hasScaleX for usage...
        else:
            self.mod7 = self.simpleDirected

    def __int__(self):
        return self.directed

    def __repr__(self):
        return "<music21.interval.GenericInterval %s>" % self.directed

    def complement(self):
        '''Returns a new GenericInterval object where descending 3rds are 6ths, etc.

        >>> aInterval = GenericInterval('Third')
        >>> aInterval.complement()
        <music21.interval.GenericInterval 6>
        '''
        return GenericInterval(self.mod7inversion)

    def reverse(self):
        '''Returns a new GenericInterval object that is inverted. 

        >>> aInterval = GenericInterval('Third')
        >>> aInterval.reverse()
        <music21.interval.GenericInterval -3>

        >>> aInterval = GenericInterval(-13)
        >>> aInterval.direction
        -1
        >>> aInterval.reverse()
        <music21.interval.GenericInterval 13>
        '''
        return GenericInterval(self.undirected * (-1 * self.direction))


    def getDiatonic(self, specifier):
        '''Given a specifier, return a :class:`~music21.interval.DiatonicInterval` object. 

        Specifier should be provided as a string name, such as 'dd', 'M', or 'perfect'.

        >>> aInterval = GenericInterval('Third')
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

        >>> bInterval = GenericInterval('fifth')
        >>> bInterval.getDiatonic('perfect')
        <music21.interval.DiatonicInterval P5>
        '''             
        return DiatonicInterval(specifier, self)


class DiatonicInterval(music21.Music21Object):
    '''A class representing a diatonic interval. Two required arguments are a `specifier` (such as perfect, major, or minor) and a `generic`, an interval size (such as 2, 2nd, or second). 

    A DiatonicInterval contains and encapsulates a :class:`~music21.interval.GenericInterval`

    '''
    _DOC_ATTR = {
    'name': 'The name of the interval in abbreviated form without direction.',
    'niceName': 'The name of the interval in full form.',
    'directedName': 'The name of the interval in abbreviated form with direction.',
    'directedNiceName': 'The name of the interval in full form with direction.',
    }

    def __init__(self, specifier, generic):
        '''
        The `specifier` is an integer specifying a value in the `prefixSpecs` and `niceSpecNames` lists. 

        The `generic` is an integer or GenericInterval instance.

        >>> aInterval = DiatonicInterval(1, 1)
        >>> aInterval.simpleName
        'P1'
        >>> aInterval = DiatonicInterval('p', 1)
        >>> aInterval.simpleName
        'P1'
        >>> aInterval = DiatonicInterval('major', 3)
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

        >>> aInterval = DiatonicInterval('major', 'third')
        >>> aInterval.niceName
        'Major Third'

        >>> aInterval = DiatonicInterval('perfect', 'octave')
        >>> aInterval.niceName
        'Perfect Octave'

        >>> aInterval = DiatonicInterval('minor', 10)
        >>> aInterval.mod7
        'm3'

        '''
        music21.Music21Object.__init__(self)

        if specifier is not None and generic is not None:
            if common.isNum(generic) or common.isStr(generic):
                self.generic = GenericInterval(generic)
            elif isinstance(generic, GenericInterval): 
                self.generic = generic
            else:
                raise IntervalException('incorrect generic argument: %s' % generic)

        self.name = ""
        # translate strings, if provided, to integers
        # specifier here is the index number in the prefixSpecs list
        self.specifier, specifierStr = convertSpecifier(specifier)
        if self.specifier != None:
            self.name = (prefixSpecs[self.specifier] +
                        str(self.generic.undirected))

            self.niceName = (niceSpecNames[self.specifier] + " " +
                             self.generic.niceName)

            self.directedName = (prefixSpecs[self.specifier] +
                                 str(self.generic.directed))

            self.directedNiceName = (directionTerms[self.generic.direction] + 
                                    " " + self.niceName)

            self.simpleName = (prefixSpecs[self.specifier] +
                              str(self.generic.simpleUndirected))

            self.simpleNiceName = (niceSpecNames[self.specifier] + " " +
                                  self.generic.simpleNiceName)

            self.semiSimpleName = (prefixSpecs[self.specifier] +
                                 str(self.generic.semiSimpleUndirected))

            self.semiSimpleNiceName = (niceSpecNames[self.specifier] + " " + 
                                    self.generic.semiSimpleNiceName)

            self.directedSimpleName = (prefixSpecs[self.specifier] +
                                     str(self.generic.simpleDirected))

            self.directedSimpleNiceName = (directionTerms[
                self.generic.direction] + " " + self.simpleNiceName)

            self.specificName = niceSpecNames[self.specifier]
            self.prefectable = self.generic.perfectable

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
            if self.generic.direction == DESCENDING:
                self.mod7 = self.mod7inversion
            else:
                self.mod7 = self.simpleName

    def __repr__(self):
        return "<music21.interval.DiatonicInterval %s>" % self.name


    def reverse(self):
        '''Return a DiatonicInterval that is an inversion of this Interval.

        >>> aInterval = DiatonicInterval('major', 3)
        >>> aInterval.reverse().directedName
        'M-3'

        >>> aInterval = DiatonicInterval('augmented', 5)
        >>> aInterval.reverse().directedName
        'A-5'
        '''
        # self.invertedOrderedSpecifier gives a complement, not an inversion?
        return DiatonicInterval(self.specifier, 
                                self.generic.reverse())


    def getChromatic(self):
        '''Return a Chromatic interval based on the size of this Interval.

        >>> aInterval = DiatonicInterval('major', 'third')
        >>> aInterval.niceName
        'Major Third'
        >>> aInterval.getChromatic()
        <music21.interval.ChromaticInterval 4>

        >>> aInterval = DiatonicInterval('augmented', -5)
        >>> aInterval.niceName
        'Augmented Fifth'
        >>> aInterval.getChromatic()
        <music21.interval.ChromaticInterval -8>

        >>> aInterval = DiatonicInterval('minor', 'second')
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


class ChromaticInterval(music21.Music21Object):
    '''Chromatic interval class. Unlike a Diatonic interval, this Interval class treats interval spaces in half-steps. 

    '''
    def __init__(self, value):
        '''
        >>> aInterval = ChromaticInterval(-14)
        >>> aInterval.semitones
        -14
        >>> aInterval.undirected
        14
        >>> aInterval.mod12
        10
        >>> aInterval.intervalClass
        2
        '''
        music21.Music21Object.__init__(self)

        self.semitones = value
        self.cents = value * 100
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

    def __repr__(self):
        return "<music21.interval.ChromaticInterval %s>" % self.directed

    def reverse(self):
        '''Return an inverted interval, that is, reversing the direction.

        >>> aInterval = ChromaticInterval(-14)
        >>> aInterval.reverse()
        <music21.interval.ChromaticInterval 14>

        >>> aInterval = ChromaticInterval(3)
        >>> aInterval.reverse()
        <music21.interval.ChromaticInterval -3>
        '''
        return ChromaticInterval(self.undirected * (-1 * self.direction))

    def getDiatonic(self):
        '''Given a Chromatic interval, return a Diatonic interval object. 
        
        While there is more than one Generic Interval for any given chromatic interval, this is needed to to permit easy chromatic specification of Interval objects.

        >>> aInterval = ChromaticInterval(5)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval P4>

        >>> aInterval = ChromaticInterval(7)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval P5>

        >>> aInterval = ChromaticInterval(11)
        >>> aInterval.getDiatonic()
        <music21.interval.DiatonicInterval M7>

        '''
        specifier, generic = convertSemitoneToSpecifierGeneric(self.semitones)
        return DiatonicInterval(specifier, generic)
    

#-------------------------------------------------------------------------------
def _stringToDiatonicChromatic(value):
    '''A function for processing interval strings and returning diatonic and chromatic interval objects. Used by the Interval class, below. 

    >>> _stringToDiatonicChromatic('P5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>)
    >>> _stringToDiatonicChromatic('p5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>)
    >>> _stringToDiatonicChromatic('perfect5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>)

    >>> _stringToDiatonicChromatic('P-5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval -7>)
    >>> _stringToDiatonicChromatic('M3')
    (<music21.interval.DiatonicInterval M3>, <music21.interval.ChromaticInterval 4>)
    >>> _stringToDiatonicChromatic('m3')
    (<music21.interval.DiatonicInterval m3>, <music21.interval.ChromaticInterval 3>)

    >>> _stringToDiatonicChromatic('whole')
    (<music21.interval.DiatonicInterval M2>, <music21.interval.ChromaticInterval 2>)
    >>> _stringToDiatonicChromatic('half')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval 1>)
    >>> _stringToDiatonicChromatic('-h')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval -1>)

    >>> _stringToDiatonicChromatic('semitone')
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
    '''Given two :class:`~music21.note.Note` objects, returns a :class:`~music21.interval.GenericInterval` object.
    
    >>> from music21 import note
    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g5')
    >>> aInterval = notesToGeneric(aNote, bNote)
    >>> aInterval
    <music21.interval.GenericInterval 12>

    '''
    # TODO: rename notesToGeneric
    staffDist = n2.diatonicNoteNum - n1.diatonicNoteNum
    genDist = convertStaffDistanceToInterval(staffDist)
    return GenericInterval(genDist)

def notesToChromatic(n1, n2):
    '''Given two :class:`~music21.note.Note` objects, returns a :class:`~music21.interval.ChromaticInterval` object.
    
    >>> from music21 import note
    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g#5')
    >>> notesToChromatic(aNote, bNote)
    <music21.interval.ChromaticInterval 20>
    '''
    # TODO: rename notesToChromatic
    return ChromaticInterval(n2.midi - n1.midi)


def _getSpecifierFromGenericChromatic(gInt, cInt):
    '''Given a :class:`~music21.interval.GenericInterval` and a :class:`~music21.interval.ChromaticInterval` object, return a specifier (i.e. MAJOR, MINOR, etc...).
    
    >>> aInterval = GenericInterval('seventh')
    >>> bInterval = ChromaticInterval(11)
    >>> _getSpecifierFromGenericChromatic(aInterval, bInterval)
    2
    >>> convertSpecifier('major')
    (2, 'M')
    '''
    noteVals = [None, 0, 2, 4, 5, 7, 9, 11]
    normalSemis = noteVals[gInt.simpleUndirected] + 12 * gInt.undirectedOctaves
    theseSemis  = cInt.undirected
    if gInt.perfectable:
        specifier = perfSpecifiers[perfOffset + theseSemis - normalSemis]
    else:
        specifier = specifiers[majOffset + theseSemis - normalSemis]
    return specifier    

    
def intervalsToDiatonic(gInt, cInt):
    '''Given a :class:`~music21.interval.GenericInterval` and a :class:`~music21.interval.ChromaticInterval` object, return a :class:`~music21.interval.DiatonicInterval`.    

    >>> aInterval = GenericInterval('descending fifth')
    >>> bInterval = ChromaticInterval(-7)
    >>> cInterval = intervalsToDiatonic(aInterval, bInterval)
    >>> cInterval
    <music21.interval.DiatonicInterval P5>
    '''

    # TODO: rename intervalsToDiatonic
    specifier = _getSpecifierFromGenericChromatic(gInt, cInt)
    return DiatonicInterval(specifier, gInt)
    



#-------------------------------------------------------------------------------
class Interval(music21.Music21Object):
    '''An Interval class that encapsulates both a chromatic and diatonic intervals all in one model. 

     The interval is specified either as named arguments, a :class:`~music21.interval.DiatonicInterval` and a :class:`~music21.interval.ChromaticInterval`, or two :class:`~music21.note.Note` objects, from which both a ChromaticInterval and DiatonicInterval are derived. 

    >>> from music21 import note
    >>> n1 = note.Note('c3')
    >>> n2 = note.Note('c5')
    >>> aInterval = Interval(noteStart=n1, noteEnd=n2)
    >>> aInterval
    <music21.interval.Interval P15>
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

    diatonic = None
    chromatic = None
    direction = None
    generic = None

    # these can be accessed through noteStart and noteEnd properties
    _noteStart = None 
    _noteEnd = None 

    type = "" # harmonic or melodic
    diatonicType = 0
    niceName = ""

    def __init__(self, *arguments, **keywords):
        '''
        >>> from music21 import note
        >>> n1 = note.Note('c3')
        >>> n2 = note.Note('g3')
        >>> aInterval = Interval(noteStart=n1, noteEnd=n2)
        >>> aInterval
        <music21.interval.Interval P5>

        >>> aInterval = Interval(noteStart=n1, noteEnd=None)
        Traceback (most recent call last):
        IntervalException: two or zero Note classes must be defined

        >>> aInterval = DiatonicInterval('major', 'third')
        >>> bInterval = ChromaticInterval(4)
        >>> cInterval = Interval(diatonic=aInterval, chromatic=bInterval)
        >>> cInterval
        <music21.interval.Interval M3>

        >>> cInterval = Interval(diatonic=aInterval, chromatic=None)
        Traceback (most recent call last):
        IntervalException: either both or zero diatonic and chromatic classes must be defined

        >>> aInterval = Interval('m3')
        >>> aInterval
        <music21.interval.Interval m3>
        >>> aInterval = Interval('M3')
        >>> aInterval
        <music21.interval.Interval M3>
        >>> aInterval = Interval('p5')
        >>> aInterval
        <music21.interval.Interval P5>

        >>> aInterval = Interval('half')
        >>> aInterval
        <music21.interval.Interval m2>

        >>> aInterval = Interval('-h')
        >>> aInterval
        <music21.interval.Interval m-2>
        
        >>> aInterval = Interval(3)
        >>> aInterval
        <music21.interval.Interval m3>

        >>> aInterval = Interval(7)
        >>> aInterval
        <music21.interval.Interval P5>

        '''
        music21.Music21Object.__init__(self)
        if len(arguments) == 1 and common.isStr(arguments[0]):
            # convert common string representations 
            dInterval, cInterval = _stringToDiatonicChromatic(arguments[0])
            self.diatonic = dInterval
            self.chromatic = cInterval

        # if we get a first argument that is a number, treat it as a chromatic
        # interval creation argument
        elif len(arguments) == 1 and common.isNum(arguments[0]):
            self.chromatic = ChromaticInterval(arguments[0])
            self.diatonic = self.chromatic.getDiatonic()

        elif (len(arguments) == 2 and arguments[0].isNote == True and 
            arguments[1].isNote == True):
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
        '''Reinitialize the internal interval objects in case something has changed. Called during __init__ to assign attributes.
        '''
        # catch case where only one Note is provided
        if (self._noteStart != None and self._noteEnd == None or 
            self._noteEnd != None and self._noteStart == None):
            raise IntervalException('two or zero Note classes must be defined')

        if self._noteStart is not None and self._noteEnd is not None:
            genericInterval = notesToGeneric(self._noteStart, self._noteEnd)
            chromaticInterval = notesToChromatic(self._noteStart, self._noteEnd)
            diatonicInterval = intervalsToDiatonic(genericInterval, chromaticInterval)
            self.diatonic = diatonicInterval
            self.chromatic = chromaticInterval

        # check for error of only one type being defined
        if (self.chromatic != None and self.diatonic == None or 
            self.diatonic != None and self.chromatic == None):
            raise IntervalException('either both or zero diatonic and chromatic classes must be defined')

        if self.chromatic != None:
            self.direction = self.chromatic.direction
        elif self.diatonic != None:
            self.direction = self.diatonic.generic.direction
            
        if self.diatonic != None:
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

    def __repr__(self):
        return "<music21.interval.Interval %s>" % self.directedName

    def _getComplement(self):
        return Interval(self.diatonic.mod7inversion)
    
    complement = property(_getComplement, 
        doc='''Return a new Interval object that is the complement of this Interval.

        >>> aInterval = Interval('M3')
        >>> bInterval = aInterval.complement
        >>> bInterval
        <music21.interval.Interval m6>
        ''')


    def _getIntervalClass(self):
        return self.chromatic.intervalClass

    intervalClass = property(_getIntervalClass,
        doc = '''Return the interval class from the chromatic interval.

        >>> aInterval = Interval('M3')
        >>> aInterval.intervalClass
        4
        ''')


    def transposePitch(self, p, reverse=False):
        '''Given a Pitch, return a new, transposed Pitch, that is transformed according to this Interval.

        >>> from music21 import pitch
        >>> p1 = pitch.Pitch('a#')
        >>> i = Interval('m3')
        >>> p2 = i.transposePitch(p1)
        >>> p2
        C#5
        >>> p2 = i.transposePitch(p1, reverse=True)
        >>> p2
        F##4

        '''
        pitch1 = p
        pitch2 = copy.deepcopy(pitch1)

        if not reverse:
            newDiatonicNumber = (pitch1.diatonicNoteNum +
                             self.diatonic.generic.staffDistance)
        else:
            newDiatonicNumber = (pitch1.diatonicNoteNum -
                             self.diatonic.generic.staffDistance)

        newStep, newOctave = convertDiatonicNumberToStep(newDiatonicNumber)
        pitch2.step = newStep
        pitch2.octave = newOctave
        pitch2.accidental = None

        # have right note name but not accidental
        interval2 = notesToInterval(pitch1, pitch2)    

        if not reverse:
            halfStepsToFix = (self.chromatic.semitones -
                          interval2.chromatic.semitones)
        else:
            halfStepsToFix = (-self.chromatic.semitones -
                          interval2.chromatic.semitones)

        if halfStepsToFix != 0:
            pitch2.accidental = halfStepsToFix
            # inherit accidental display properties
            pitch2.inheritDisplay(pitch1)
        return pitch2


    def reverse(self):
        '''Return an reversed version of this interval. If given Notes, these notes are reversed. 

        >>> from music21 import note
        >>> n1 = note.Note('c3')
        >>> n2 = note.Note('g3')
        >>> aInterval = Interval(noteStart=n1, noteEnd=n2)
        >>> aInterval
        <music21.interval.Interval P5>
        >>> bInterval = aInterval.reverse()
        >>> bInterval
        <music21.interval.Interval P-5>
        >>> bInterval.noteStart == aInterval.noteEnd
        True
        
        >>> aInterval = Interval('m3')
        >>> aInterval.reverse()
        <music21.interval.Interval m-3>
        '''
        if self._noteStart != None and self._noteEnd != None:
            return Interval(noteStart=self._noteEnd, noteEnd=self._noteStart)
        else:
            return Interval(diatonic=self.diatonic.reverse(),
                            chromatic=self.chromatic.reverse())


    def _setNoteStart(self, n):
        '''Assuming that this interval is defined, we can set a new start note (_noteStart) and automatically have the end note (_noteEnd).
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
        doc = '''Assuming this Interval has been defined, set the start note (_noteStart) to a new value; this will adjust the value of the end note (_noteEnd).
        
        >>> from music21 import note
        >>> aInterval = Interval('M3')
        >>> aInterval.noteStart = note.Note('c4')
        >>> aInterval.noteEnd.nameWithOctave
        'E4'

        >>> n1 = note.Note('c3')
        >>> n2 = note.Note('g#3')
        >>> aInterval = Interval(n1, n2)
        >>> aInterval.name
        'A5'
        >>> aInterval.noteStart = note.Note('g4')
        >>> aInterval.noteEnd.nameWithOctave
        'D#5'

        >>> aInterval = Interval('-M3')
        >>> aInterval.noteStart = note.Note('c4')
        >>> aInterval.noteEnd.nameWithOctave
        'A-3'

        >>> aInterval = Interval('M-2')
        >>> aInterval.noteStart = note.Note('A#3')
        >>> aInterval.noteEnd.nameWithOctave
        'G#3'

        >>> aInterval = Interval('h')
        >>> aInterval.directedName
        'm2'
        >>> aInterval.noteStart = note.Note('F#3')
        >>> aInterval.noteEnd.nameWithOctave
        'G3'

        ''')

    def _setNoteEnd(self, n):
        '''Assuming that this interval is defined, we can set a new end note (_noteEnd) and automatically have the start note (_noteStart).
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
        doc = '''Assuming this Interval has been defined, set the end note (_noteEnd) to a new value; this will adjust the value of the start note (_noteStart).

        >>> from music21 import note
        >>> aInterval = Interval('M3')
        >>> aInterval.noteEnd = note.Note('e4')
        >>> aInterval.noteStart.nameWithOctave
        'C4'

        >>> aInterval = Interval('m2')
        >>> aInterval.noteEnd = note.Note('A#3')
        >>> aInterval.noteStart.nameWithOctave
        'G##3'

        >>> n1 = note.Note('g#3')
        >>> n2 = note.Note('c3')
        >>> aInterval = Interval(n1, n2)
        >>> aInterval.directedName # downward augmented fifth
        'A-5'
        >>> aInterval.noteEnd = note.Note('c4')
        >>> aInterval.noteStart.nameWithOctave
        'G#4'

        >>> aInterval = Interval('M3')
        >>> aInterval.noteEnd = note.Note('A-3')
        >>> aInterval.noteStart.nameWithOctave
        'F-3'

         ''')




#-------------------------------------------------------------------------------
def getWrittenHigherNote(note1, note2):
    '''Given two :class:`~music21.note.Note` or :class:`~music21.pitch.Pitch` objects, this function returns the higher object based on diatonic note
    numbers. Returns the note higher in pitch if the diatonic number is
    the same, or the first note if pitch is also the same.

    >>> from music21 import pitch
    >>> cis = pitch.Pitch("C#")
    >>> deses = pitch.Pitch("D--")
    >>> higher = getWrittenHigherNote(cis, deses)
    >>> higher is deses
    True

    >>> from music21 import note
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d-3')
    >>> getWrittenHigherNote(aNote, bNote)
    <music21.note.Note D->

    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> getWrittenHigherNote(aNote, bNote)
    <music21.note.Note D-->
    '''
    
    num1 = note1.diatonicNoteNum
    num2 = note2.diatonicNoteNum
    if num1 > num2: return note1
    elif num1 < num2: return note2
    else: return getAbsoluteHigherNote(note1, note2)

def getAbsoluteHigherNote(note1, note2):
    '''Given two :class:`~music21.note.Note` objects, returns the higher note based on actual pitch.
    If both pitches are the same, returns the first note given.

    >>> from music21 import note
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> getAbsoluteHigherNote(aNote, bNote)
    <music21.note.Note C#>

    '''
    chromatic = notesToChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0: return note2
    elif semitones < 0: return note1
    else: return note1

def getWrittenLowerNote(note1, note2):
    '''Given two :class:`~music21.note.Note` objects, returns the lower note based on diatonic note
    number. Returns the note lower in pitch if the diatonic number is
    the same, or the first note if pitch is also the same.

    >>> from music21 import note
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> getWrittenLowerNote(aNote, bNote)
    <music21.note.Note C#>

    >>> from music21 import note
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d-3')
    >>> getWrittenLowerNote(aNote, bNote)
    <music21.note.Note C#>
    '''
    num1 = note1.diatonicNoteNum
    num2 = note2.diatonicNoteNum
    if num1 < num2: return note1
    elif num1 > num2: return note2
    else: return getAbsoluteLowerNote(note1, note2)

def getAbsoluteLowerNote(note1, note2):
    '''Given two :class:`~music21.note.Note` objects, returns the lower note based on actual pitch.
    If both pitches are the same, returns the first note given.

    >>> from music21 import note
    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('d--3')
    >>> getAbsoluteLowerNote(aNote, bNote)
    <music21.note.Note D-->
    '''
    chromatic = notesToChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0: return note1
    elif semitones < 0: return note2
    else: return note1

def transposePitch(pitch1, interval1):
    '''Given a :class:`~music21.pitch.Pitch` and a :class:`~music21.interval.Interval` object, return a new Pitch object at the appropriate pitch level. 

    >>> from music21 import pitch
    >>> aPitch = pitch.Pitch('C4')
    >>> aInterval = Interval('P5')
    >>> bPitch = transposePitch(aPitch, aInterval)
    >>> bPitch
    G4
    >>> bInterval = stringToInterval('P-5')
    >>> cPitch = transposePitch(aPitch, bInterval)
    >>> cPitch
    F3
    ''' 
    # TODO: rename transposePitch

    # check if interval1 is a string,
    # then convert it to interval object if necessary
    if common.isStr(interval1):
        #print interval1, "same name"
        interval1 = stringToInterval(interval1) 
        #print interval1.name, " int name" # del me
    else:
        pass # assuming it is an interval object
        #raise IntervalException('numeric intervals not yet defined')
        
    newDiatonicNumber = (pitch1.diatonicNoteNum +
                         interval1.diatonic.generic.staffDistance)
    pitch2 = copy.deepcopy(pitch1)
    newStep, newOctave = convertDiatonicNumberToStep(newDiatonicNumber)
    pitch2.step = newStep
    pitch2.octave = newOctave
    pitch2.accidental = None
    # at this point note2 has the right note name (step), but possibly
    # the wrong accidental.  We fix that below
    interval2 = notesToInterval(pitch1, pitch2)    
    halfStepsToFix = (interval1.chromatic.semitones -
                      interval2.chromatic.semitones)
    pitch2.accidental = halfStepsToFix
    return pitch2

def transposeNote(note1, intervalString):
    '''Given a :class:`~music21.note.Note` and a interval string (such as 'P5') or an Interval object, return a new Note object at the appropriate pitch level. 

    >>> from music21 import note
    >>> aNote = note.Note('c4')
    >>> bNote = transposeNote(aNote, 'p5')
    >>> bNote
    <music21.note.Note G>

    >>> aNote = note.Note('f#4')
    >>> bNote = transposeNote(aNote, 'm2')
    >>> bNote
    <music21.note.Note G>

    '''

    newPitch = transposePitch(note1, intervalString)
    newNote = copy.deepcopy(note1)
    newNote.pitch = newPitch
    return newNote


def notesToInterval(n1, n2 = None):  
    '''Given two :class:`~music21.note.Note` objects, returns an :class:`~music21.interval.Interval` object. The same functionality is available by calling the Interval class with two Notes as arguments.

    >>> from music21 import note
    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g5')
    >>> aInterval = notesToInterval(aNote, bNote)
    >>> aInterval
    <music21.interval.Interval P12>

    >>> bInterval = Interval(noteStart=aNote, noteEnd=bNote)
    >>> aInterval.niceName == bInterval.niceName
    True
    '''
    # TODO: possibly remove: not clear how this offers any better functionality
    # than just creating an Interval class?

    #note to self:  what's going on with the Note() representation in help?
    if n2 is None: 
        n2 = music21.note.Note() 
        # this is not done in the constructor because of looping problems with tinyNotationNote
    gInt = notesToGeneric(n1, n2)
    cInt = notesToChromatic(n1, n2)
    dInt = intervalsToDiatonic(gInt, cInt)
    intObj = Interval(diatonic = dInt, chromatic = cInt,
                    note1 = n1, note2 = n2)
    return intObj

def stringToInterval(string):
    '''Given an interval string (such as "P5", "m3", "A2") return a :class:`~music21.interval.Interval` object.

    >>> aInterval = stringToInterval('P5')
    >>> aInterval
    <music21.interval.Interval P5>
    >>> aInterval = stringToInterval('m3')
    >>> aInterval
    <music21.interval.Interval m3>
    '''
    # TODO: rename intervalFromString
    # TODO: possibly remove: exact same functionality is available directly
    # from Interval instance

#     dInterval, cInterval = _stringToDiatonicChromatic(string)
#     allInterval = Interval(diatonic = dInterval, chromatic = cInterval)
#     return allInterval
        
    return Interval(string)



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testFirst(self):       
        from music21 import pitch
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
        dInt1 = int1.diatonic   # returns same as gInt1 -- just a different way of thinking of things
        gInt1 = dInt1.generic
    
        ## TODO: rewrite all assertion code using self.assertEqual etc.
        self.assertEqual(gInt1.isStep, False)
        self.assertEqual(gInt1.isSkip, True)
        
        n1.accidental = Accidental("#")
        int1.reinit()
        
        cInt1 = notesToChromatic(n1,n2) # returns music21.interval.ChromaticInterval object
        cInt2 = int1.chromatic        # returns same as cInt1 -- just a different way of thinking of things
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
    
        noteA4 = transposePitch(noteA3, intervalA1)
        self.assertEqual(noteA4.name, "E#")
        self.assertEqual(noteA4.octave, 2)
        
        interval1 = stringToInterval("P-5")
        
        n5 = transposePitch(n4, interval1)
        n6 = transposePitch(n4, "P-5")
        self.assertEqual(n5.name, "G-")
        self.assertEqual(n6.name, n5.name)
        n7 = Note()
        n8 = transposePitch(n7, "P8")
        self.assertEqual(n8.name, "C")
        self.assertEqual(n8.octave, 5)

        ## same thing using newer syntax:
        
        interval1 = Interval("P-5")
        
        n5 = transposePitch(n4, interval1)
        n6 = transposePitch(n4, "P-5")
        self.assertEqual(n5.name, "G-")
        self.assertEqual(n6.name, n5.name)
        n7 = Note()
        n8 = transposePitch(n7, "P8")
        self.assertEqual(n8.name, "C")
        self.assertEqual(n8.octave, 5)

        
        n9 = transposePitch(n7, "m7")  ## should be B-
        self.assertEqual(n9.name, "B-")
        self.assertEqual(n9.octave, 4)
        n10 = transposePitch(n7, "dd-2")  ## should be B##
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
        self.assertEqual(descendingOctave.generic.simpleDirected, 1)  # no descending unisons ever
        self.assertEqual(descendingOctave.generic.semiSimpleDirected, -8)  # no descending unisons ever
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




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [notesToChromatic, intervalsToDiatonic, notesToInterval, Interval]


if __name__ == "__main__":
    music21.mainTest(Test)