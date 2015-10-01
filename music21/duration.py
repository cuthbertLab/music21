# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         duration.py
# Purpose:      music21 classes for representing durations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
The duration module contains  :class:`~music21.duration.Duration` objects
(among other objects and functions).  Duration objects are a fundamental
component of :class:`~music21.note.Note` and all Music21Objects, such as
:class:`~music21.meter.TimeSignature` objects.


Containers such as :class:`~music21.stream.Stream` and
:class:`~music21.stream.Score` also have durations which are equal to the
position of the ending of the last object in the Stream.


Music21 Durations are almost always measured in Quarter Notes, so an eighth
note has a duration of 0.5.  Different Duration-like objects support objects
such as grace notes which take no duration on the page, have a short (but real)
duration when played, and have a duration-type representation when performed.

Example usage:

>>> d = duration.Duration()
>>> d.quarterLength = 0.5
>>> d.type
'eighth'

>>> d.type = 'whole'
>>> d.quarterLength
4.0

>>> d.quarterLength = 0.166666666
>>> d.type
'16th'

>>> d.tuplets[0].numberNotesActual
3

>>> d.tuplets[0].numberNotesNormal
2
'''
from __future__ import print_function, division

import fractions
import unittest
import copy

from music21 import common
from music21 import defaults
from music21 import exceptions21
from music21.common import SlottedObject, opFrac
from music21 import environment

from collections import namedtuple




try:
    basestring # @UndefinedVariable
except NameError:
    basestring = str # @ReservedAssignment


_MOD = "duration.py"
environLocal = environment.Environment(_MOD)

DENOM_LIMIT = defaults.limitOffsetDenominator

#-------------------------------------------------------------------------------
# duration constants and reference

# N.B.: MusicXML uses long instead of longa
typeToDuration = {
    'duplex-maxima': 64.0,
    'maxima': 32.0,
    'longa': 16.0,
    'breve': 8.0,
    'whole': 4.0,
    'half': 2.0,
    'quarter': 1.0,
    'eighth': 0.5,
    '16th': 0.25,
    '32nd': 0.125,
    '64th': 0.0625,
    '128th': 0.03125,
    '256th': 0.015625,
    '512th': 0.015625 / 2.0,
    '1024th': 0.015625 / 4.0,
    '2048th': 0.015625 / 8.0,
    'zero': 0.0,
    }

typeFromNumDict = {
    1.0: 'whole',
    2.0: 'half',
    4.0: 'quarter',
    8.0: 'eighth',
    16.0: '16th',
    32.0: '32nd',
    64.0: '64th',
    128.0: '128th',
    256.0: '256th',
    512.0: '512th',
    1024.0: '1024th',
    2048.0: '2048th',
    0.0: 'zero',
    0.5: 'breve',
    0.25: 'longa',
    0.125: 'maxima',
    0.0625: 'duplex-maxima',
    }
typeFromNumDictKeys = sorted(list(typeFromNumDict.keys()))

ordinalTypeFromNum = [
    "duplex-maxima",
    "maxima",
    "longa",
    "breve",
    "whole",
    "half",
    "quarter",
    "eighth",
    "16th",
    "32nd",
    "64th",
    "128th",
    "256th",
    "512th",
    "1024th",
    "2048th",
    ]

defaultTupletNumerators = (3, 5, 7, 11, 13)
extendedTupletNumerators = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199)


def unitSpec(durationObjectOrObjects):
    '''
    A simple data representation of most Duration objects. Processes a single
    Duration or a List of Durations, returning a single or list of unitSpecs.

    A unitSpec is a tuple of qLen, durType, dots, tupleNumerator,
    tupletDenominator, and tupletType (assuming top and bottom tuplets are the
    same).

    This function does not deal with nested tuplets, etc.

    >>> aDur = duration.Duration()
    >>> aDur.quarterLength = 3
    >>> duration.unitSpec(aDur)
    (3.0, 'half', 1, None, None, None)

    >>> bDur = duration.Duration()
    >>> bDur.quarterLength = 1.125
    >>> duration.unitSpec(bDur)
    (1.125, 'complex', 0, None, None, None)

    >>> cDur = duration.Duration()
    >>> cDur.quarterLength = 0.3333333
    >>> duration.unitSpec(cDur)
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')

    >>> duration.unitSpec([aDur, bDur, cDur])
    [(3.0, 'half', 1, None, None, None), (1.125, 'complex', 0, None, None, None), (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')]
    '''
    if isinstance(durationObjectOrObjects, list):
        ret = []
        for dO in durationObjectOrObjects:
            ret.append(unitSpec(dO))
        return ret
    else:
        dO = durationObjectOrObjects
        if not(hasattr(dO, 'tuplets')) or dO.tuplets is None or len(dO.tuplets) == 0:
            return (dO.quarterLength, dO.type, dO.dots, None, None, None)
        else:
            return (dO.quarterLength, dO.type, dO.dots, dO.tuplets[0].numberNotesActual, dO.tuplets[0].numberNotesNormal, dO.tuplets[0].durationNormal.type)

def nextLargerType(durType):
    '''
    Given a type (such as 16th or quarter), return the next larger type.

    >>> duration.nextLargerType("16th")
    'eighth'
    >>> duration.nextLargerType("whole")
    'breve'
    >>> duration.nextLargerType("duplex-maxima")
    Traceback (most recent call last):
    DurationException: cannot get the next larger of duplex-maxima
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException("cannot get the next larger of %s" % durType)
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 0: 
        raise DurationException("cannot get the next larger of %s" % durType)
    else:
        return ordinalTypeFromNum[thisOrdinal - 1]


def nextSmallerType(durType):
    '''
    Given a type (such as 16th or quarter), return the next smaller type.


    >>> duration.nextSmallerType("16th")
    '32nd'
    >>> duration.nextSmallerType("whole")
    'half'
    >>> duration.nextSmallerType("1024th")
    '2048th'
    >>> duration.nextSmallerType("2048th")
    Traceback (most recent call last):
    DurationException: cannot get the next smaller of 2048th
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException("cannot get the next smaller of %s" % durType)
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 15: 
        raise DurationException("cannot get the next smaller of %s" % durType)
    else:
        return ordinalTypeFromNum[thisOrdinal + 1]



def quarterLengthToClosestType(qLen):
    '''
    Returns a two-unit tuple consisting of

    1. The type string ("quarter") that is smaller than or equal to the quarterLength of provided.

    2. Boolean, True or False, whether the conversion was exact.

    >>> duration.quarterLengthToClosestType(.5)
    ('eighth', True)
    >>> duration.quarterLengthToClosestType(.75)
    ('eighth', False)
    >>> duration.quarterLengthToClosestType(1.8)
    ('quarter', False)
    
    Some very very close types will return True for exact conversion...
    
    >>> duration.quarterLengthToClosestType(2.0000000000000001)
    ('half', True)

    Very big durations... are fine:

    >>> duration.quarterLengthToClosestType(129.99)
    ('duplex-maxima', False)

    Durations smaller than 2048th note raise a DurationException
    
    >>> qL = duration.typeToDuration['2048th']
    >>> qL
    0.001953125
    >>> qL = qL * .75
    >>> duration.quarterLengthToClosestType(qL)
    Traceback (most recent call last):
    DurationException: Cannot return types smaller than 2048th; qLen was: 0.00146484375
    '''
    if (isinstance(qLen, fractions.Fraction)):
        noteLengthType = 4 / qLen  # divides right...
    else:
        noteLengthType = opFrac(4.0/qLen)

    if noteLengthType in typeFromNumDict:
        return (typeFromNumDict[noteLengthType], True)
    else:
        lowerBound = 4 / qLen
        upperBound = 8 / qLen
        for numDict in typeFromNumDictKeys:
            if numDict == 0:
                continue
            elif lowerBound < numDict and upperBound > numDict:
                return (typeFromNumDict[numDict], False)
            
        if qLen > 128:
            return ('duplex-maxima', False)
        
        raise DurationException("Cannot return types smaller than 2048th; qLen was: {0}".format(qLen))



def convertQuarterLengthToType(qLen):
    '''
    Return a type if there exists a type that is exactly equal to the 
    duration of the provided quarterLength. Similar to quarterLengthToClosestType() but this 
    function only returns exact matches.


    >>> duration.convertQuarterLengthToType(2)
    'half'
    >>> duration.convertQuarterLengthToType(0.125)
    '32nd'
    >>> duration.convertQuarterLengthToType(0.33333)
    Traceback (most recent call last):
    DurationException: cannot convert quarterLength 0.33333 exactly to type
    '''
    dtype, match = quarterLengthToClosestType(qLen)
    if match is False:
        raise DurationException("cannot convert quarterLength %s exactly to type" % qLen)
    else:
        return dtype

def dottedMatch(qLen, maxDots=4):
    '''
    Given a quarterLength, determine if there is a dotted
    (or non-dotted) type that exactly matches. Returns a pair of
    (numDots, type) or (False, False) if no exact matches are found.

    Returns a maximum of four dots by default.

    >>> duration.dottedMatch(3.0)
    (1, 'half')
    >>> duration.dottedMatch(1.75)
    (2, 'quarter')

    This value is not equal to any dotted note length

    >>> duration.dottedMatch(1.6)
    (False, False)

    maxDots can be lowered for certain searches

    >>> duration.dottedMatch(1.875)
    (3, 'quarter')
    >>> duration.dottedMatch(1.875, 2)
    (False, False)

    >>> duration.dottedMatch(0.00001, 2)
    (False, False)

    '''
    for dots in range(0, maxDots + 1):
        ## assume qLen has n dots, so find its non-dotted length
        preDottedLength = (qLen + 0.0) / common.dotMultiplier(dots)
        try:
            durType, match = quarterLengthToClosestType(preDottedLength)
        except DurationException:
            continue
        if match is True:
            return (dots, durType)
    return (False, False)


def quarterLengthToNonPowerOf2Tuplet(qLen):
    '''
    Slow, last chance function that returns a tuple of a single tuplet, probably with a non
    power of 2 denominator (such as 7:6) that represents the quarterLength and the 
    DurationTuple that should be used to express the note.
    
    This could be a double dotted note, but also a tuplet...

    >>> duration.quarterLengthToNonPowerOf2Tuplet(7)
    (<music21.duration.Tuplet 8/7/quarter>, DurationTuple(type='breve', dots=0, quarterLength=8.0))
    
    >>> duration.quarterLengthToNonPowerOf2Tuplet(7.0/16)
    (<music21.duration.Tuplet 8/7/64th>, DurationTuple(type='eighth', dots=0, quarterLength=0.5))
    
    >>> duration.quarterLengthToNonPowerOf2Tuplet(7.0/3)
    (<music21.duration.Tuplet 12/7/16th>, DurationTuple(type='whole', dots=0, quarterLength=4.0))
        
    And of course...

    >>> duration.quarterLengthToNonPowerOf2Tuplet(1)
    (<music21.duration.Tuplet 1/1/quarter>, DurationTuple(type='quarter', dots=0, quarterLength=1.0))
    '''    
    qFrac = fractions.Fraction.from_float(1/float(qLen)).limit_denominator(DENOM_LIMIT)
    qFracOrg = qFrac
    if qFrac.numerator < qFrac.denominator:
        while qFrac.numerator < qFrac.denominator:
            qFrac = qFrac * 2
    elif qFrac.numerator > qFrac.denominator*2:
        while qFrac.numerator > qFrac.denominator*2:
            qFrac = qFrac / 2
    # qFrac will always be in lowest terms

    # TODO: DurationTuple
    closestSmallerType, unused_match = quarterLengthToClosestType(qLen/qFrac.denominator)

    tupletDuration = Duration(type=closestSmallerType)

    representativeDuration = durationTupleFromQuarterLength(qFrac/qFracOrg)
            
    return (Tuplet(numberNotesActual=qFrac.numerator,
                  numberNotesNormal=qFrac.denominator,
           durationActual = tupletDuration,
           durationNormal = tupletDuration,
    ), representativeDuration)


def quarterLengthToTuplet(qLen, 
                          maxToReturn=4, 
                          tupletNumerators=defaultTupletNumerators):
    '''
    Returns a list of possible Tuplet objects for a
    given `qLen` (quarterLength). As there may be more than one
    possible solution, the `maxToReturn` integer specifies the
    maximum number of values returned.

    Searches for numerators specified in duration.defaultTupletNumerators
    (3, 5, 7, 11, 13). Does not return dotted tuplets, nor nested tuplets.

    Note that 4:3 tuplets won't be found, but will be found as dotted notes
    by dottedMatch.


    >>> duration.quarterLengthToTuplet(.33333333)
    [<music21.duration.Tuplet 3/2/eighth>, <music21.duration.Tuplet 3/1/quarter>]

    >>> duration.quarterLengthToTuplet(.20)
    [<music21.duration.Tuplet 5/4/16th>, <music21.duration.Tuplet 5/2/eighth>, <music21.duration.Tuplet 5/1/quarter>]


    By specifying only 1 `maxToReturn`, the a single-length list containing the Tuplet with the smallest type will be returned.

    >>> duration.quarterLengthToTuplet(.3333333, 1)
    [<music21.duration.Tuplet 3/2/eighth>]

    >>> tup = duration.quarterLengthToTuplet(.3333333, 1)[0]
    >>> tup.tupletMultiplier()
    Fraction(2, 3)
    '''
    post = []
    # type, qLen pairs
    durationToType = []
    for key, value in typeToDuration.items():
        durationToType.append((value, key))
    durationToType.sort()
    qLen = opFrac(qLen)

    for typeValue, typeKey in durationToType:
        # try tuplets
        for i in tupletNumerators:
            qLenBase = opFrac(typeValue / float(i))
            # try multiples of the tuplet division, from 1 to max-1
            for m in range(1, i):
                qLenCandidate = qLenBase * m
                if qLenCandidate == qLen:
                    tupletDuration = durationTupleFromTypeDots(typeKey, 0)
                    newTuplet = Tuplet(numberNotesActual=i,
                                       numberNotesNormal=m,
                                       durationActual=tupletDuration,
                                       durationNormal=tupletDuration,)
                    post.append(newTuplet)
                    break
        # not looking for these matches will add tuple alternative
        # representations; this could be useful
            if len(post) >= maxToReturn: 
                break
        if len(post) >= maxToReturn: 
            break
    
    return post

QuarterLengthConversion = namedtuple('QuarterLengthConversion', 'components tuplet')

def quarterConversion(qLen):
    '''
    Returns a 2-element namedtuple of (components, tuplet)
    
    Components is a tuple of DurationTuples (normally one) that add up to the qLen when multiplied by...
    
    Tuplet is a single :class:`~music21.duration.Tuplet` that adjusts all of the components.
    
    (All quarterLengths can, technically, be notated as a single unit
    given a complex enough tuplet, as a last resort will look up to 199 as a tuplet type).



    >>> duration.quarterConversion(2)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=0, quarterLength=2.0),), 
        tuplet=None)

    >>> duration.quarterConversion(0.5)
    QuarterLengthConversion(components=(DurationTuple(type='eighth', dots=0, quarterLength=0.5),), 
        tuplet=None)



    Dots are supported

    >>> duration.quarterConversion(3)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=1, quarterLength=3.0),), 
        tuplet=None)

    >>> duration.quarterConversion(6.0)
    QuarterLengthConversion(components=(DurationTuple(type='whole', dots=1, quarterLength=6.0),), 
        tuplet=None)

    Double and triple dotted half note.

    >>> duration.quarterConversion(3.5)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=2, quarterLength=3.5),), 
        tuplet=None)

    >>> duration.quarterConversion(3.75)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=3, quarterLength=3.75),), 
        tuplet=None)

    A triplet quarter note, lasting .6666 qLen
    Or, a quarter that is 1/3 of a half.
    Or, a quarter that is 2/3 of a quarter.

    >>> duration.quarterConversion(2.0/3.0)
    QuarterLengthConversion(components=(DurationTuple(type='quarter', dots=0, quarterLength=1.0),), 
        tuplet=<music21.duration.Tuplet 3/2/quarter>)
    >>> t = duration.quarterConversion(2.0/3.0).tuplet
    >>> t
    <music21.duration.Tuplet 3/2/quarter>
    >>> t.durationActual
    DurationTuple(type='quarter', dots=0, quarterLength=1.0)    
    

    A triplet eighth note, where 3 eights are in the place of 2.
    Or, an eighth that is 1/3 of a quarter
    Or, an eighth that is 2/3 of eighth

    >>> duration.quarterConversion(1.0/3)
    QuarterLengthConversion(components=(DurationTuple(type='eighth', dots=0, quarterLength=0.5),), 
        tuplet=<music21.duration.Tuplet 3/2/eighth>)

    A half that is 1/3 of a whole, or a triplet half note.
    Or, a half that is 2/3 of a half

    >>> duration.quarterConversion(4.0/3.0)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=0, quarterLength=2.0),), 
        tuplet=<music21.duration.Tuplet 3/2/half>)

    >>> duration.quarterConversion(1.0/6.0)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),), 
        tuplet=<music21.duration.Tuplet 3/2/16th>)


    A sixteenth that is 1/5 of a quarter
    Or, a sixteenth that is 4/5ths of a 16th

    >>> duration.quarterConversion(1.0/5.0)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),), 
        tuplet=<music21.duration.Tuplet 5/4/16th>)
        

    A 16th that is  1/7th of a quarter
    Or, a 16th that is 4/7 of a 16th

    >>> duration.quarterConversion(1.0/7.0)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),), 
        tuplet=<music21.duration.Tuplet 7/4/16th>)

    A 4/7ths of a whole note, or
    A quarter that is 4/7th of of a quarter

    >>> duration.quarterConversion(4.0/7.0)
    QuarterLengthConversion(components=(DurationTuple(type='quarter', dots=0, quarterLength=1.0),), 
                            tuplet=<music21.duration.Tuplet 7/4/quarter>)

    If a duration is not containable in a single unit, this method
    will break off the largest type that fits within this type
    and recurse, adding as my units as necessary.

    >>> duration.quarterConversion(2.5)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=0, quarterLength=2.0), 
                                        DurationTuple(type='eighth', dots=0, quarterLength=0.5)), 
                            tuplet=None)


    Since tuplets now apply to the entire Duration, expect some odder tuplets for unusual
    values that should probably be split generally...

    >>> duration.quarterConversion(7.0/3)
    QuarterLengthConversion(components=(DurationTuple(type='whole', dots=0, quarterLength=4.0),), 
        tuplet=<music21.duration.Tuplet 12/7/16th>)

    
    This is a very close approximation:

    
    >>> duration.quarterConversion(.18333333333333)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),), 
        tuplet=<music21.duration.Tuplet 15/11/256th>)

    >>> duration.quarterConversion(0.0)
    QuarterLengthConversion(components=(DurationTuple(type='zero', dots=0, quarterLength=0.0),), 
        tuplet=None)

    '''
    # this is a performance-critical operation that has been highly optimized for speed
    # rather than legibility or logic.  Most commonly anticipated events appear first
    # then less common/slower    
    try:
        #
        if qLen > 0:
            qLenDict = 4/qLen
        else:
            qLenDict = 0
        durType = typeFromNumDict[qLenDict] # hashes are awesome. will catch Fraction(1,1), 1, 1.0 etc.
        dt = durationTupleFromTypeDots(durType, 0)
        return QuarterLengthConversion((dt,), None)
    except KeyError:
        pass
    
    dots, durType = dottedMatch(qLen)
    if durType is not False:
        dt = durationTupleFromTypeDots(durType, dots)
        return QuarterLengthConversion((dt,), None)
        
    if qLen == 0:
        dt = durationTupleFromTypeDots('zero', 0)
        return QuarterLengthConversion((dt,), None)

    
    # Tuplets...
    qLen = opFrac(qLen)
    # try match to type, get next lowest for next part...
    closestSmallerType, unused_match = quarterLengthToClosestType(qLen)
    typeNext = nextLargerType(closestSmallerType)
    tupleCandidates = quarterLengthToTuplet(qLen, 1)
    if tupleCandidates:
        # assume that the first tuplet candidate, using the smallest type, is best
        dt = durationTupleFromTypeDots(typeNext)
        return QuarterLengthConversion((dt,), tupleCandidates[0])
    
    # now we're getting into some obscure cases.
    # is it built up of many small types? 
    components = [durationTupleFromTypeDots(closestSmallerType, 0)]
    # remove the largest type out there and keep going.
    
    qLenRemainder = opFrac(qLen - typeToDuration[closestSmallerType])
    # cannot recursively call, because tuplets are not possible at this stage.
    #environLocal.warn(['starting remainder search for qLen:', qLen, 'remainder: ', qLenRemainder, 'components: ', components])
    for i in range(8): # max 8 iterations.
        #environLocal.warn(['qlenRemainder is:', qLenRemainder])
        dots, durType = dottedMatch(qLenRemainder)
        if durType is not False: # match!
            dt = durationTupleFromTypeDots(durType, dots)
            components.append(dt)
            return QuarterLengthConversion(tuple(components), None)
        try:
            closestSmallerType, unused_match = quarterLengthToClosestType(qLenRemainder)
        except DurationException:
            break # already reached 2048th notes.
        qLenRemainder = qLenRemainder - typeToDuration[closestSmallerType]
        dt = durationTupleFromTypeDots(closestSmallerType, 0)
        #environLocal.warn(['appending', dt, 'leaving ', qLenRemainder, ' of ', qLen])
        components.append(dt)
        
    # 8 tied components was not enough.
    # last resort: put one giant tuplet over it.
    tuplet, component = quarterLengthToNonPowerOf2Tuplet(qLen)
    return QuarterLengthConversion((component,), tuplet)


def partitionQuarterLength(qLen, qLenDiv=4):
    '''
    UNUSED now that .expand() is gone.  REMOVE.
    
    Given a `qLen` (quarterLength) and a `qLenDiv`, that is, a base quarterLength to divide the `qLen` into
    (default = 4; i.e., into whole notes), returns a list of DurationsUnits that
    partition the given quarterLength so that there is no leftovers along with a tupletList that
    applies to each of them.

    This is a useful tool for partitioning a duration by Measures (i.e., take a long Duration and
    make it fit within several measures) or by beat groups.

    Here is a Little demonstration function that will show how we can use partitionQuarterLength:

    >>> def pql(qLen, qLenDiv):
    ...    partitionList, tuplet = duration.partitionQuarterLength(qLen, qLenDiv)
    ...    for dur in partitionList:
    ...        print(dur)
    ...    print(tuplet)
    
    Divide 2.5 quarters worth of time into eighth notes.
    
    >>> duration.partitionQuarterLength(2.5, 0.5)
    ([DurationTuple(type='eighth', dots=0, quarterLength=0.5), 
      DurationTuple(type='eighth', dots=0, quarterLength=0.5), 
      DurationTuple(type='eighth', dots=0, quarterLength=0.5), 
      DurationTuple(type='eighth', dots=0, quarterLength=0.5), 
      DurationTuple(type='eighth', dots=0, quarterLength=0.5)],
      [None, None, None, None, None])
    
    
    >>> pql(2.5, 0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    [None, None, None, None, None]


    Divide 5 qLen into 2.5 qLen bundles (i.e., 5/8 time)
    >>> pql(5.0, 2.5)
    DurationTuple(type='half', dots=0, quarterLength=2.0)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='half', dots=0, quarterLength=2.0)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    [None, None, None, None]


    Divide 5.25 qLen into dotted halves
    >>> pql(5.25, 3)
    DurationTuple(type='half', dots=1, quarterLength=3.0)
    DurationTuple(type='half', dots=0, quarterLength=2.0)
    DurationTuple(type='16th', dots=0, quarterLength=0.25)
    [None, None, None]

    Divide 1.33333 qLen into triplet eighths:
    >>> pql(4.0/3.0, 1.0/3.0)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    [<music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/eighth>]

    Divide 1.5 into triplet eighths, with a triplet 16th leftover.
    >>> pql(1.5, 1.0/3)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    DurationTuple(type='16th', dots=0, quarterLength=0.25)
    [<music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/eighth>, 
    <music21.duration.Tuplet 3/2/16th>]
     
    There is no problem if the division unit is larger then the source duration, it
    just will not be totally filled.
    >>> pql(1.5, 4)
    DurationTuple(type='quarter', dots=1, quarterLength=1.5)
    [None]

    '''
    qLen = opFrac(qLen)
    qLenDiv = opFrac(qLenDiv)
    post = []
    tupletsList = []

    # TODO: Tuplets.
    while qLen >= qLenDiv:
        qConversion = quarterConversion(qLenDiv)
        post += list(qConversion.components)
        tupletsList += [qConversion.tuplet] * len(qConversion.components)
        
        qLen = qLen - qLenDiv
        
    if qLen != 0:
        # leftovers...
        qConversion = quarterConversion(qLen)
        post += list(qConversion.components)
        tupletsList += [qConversion.tuplet] * len(qConversion.components)

    return(post, tupletsList)


def convertTypeToQuarterLength(dType, dots=0, tuplets=None, dotGroups=None):
    '''
    Given a rhythm type (`dType`), number of dots (`dots`), an optional list of
    Tuplet objects (`tuplets`), and a (very) optional list of
    Medieval dot groups (`dotGroups`), return the equivalent quarter length.

    >>> duration.convertTypeToQuarterLength('whole')
    4.0
    >>> duration.convertTypeToQuarterLength('16th')
    0.25
    >>> duration.convertTypeToQuarterLength('quarter', 2)
    1.75


    >>> tup = duration.Tuplet(numberNotesActual = 5, numberNotesNormal = 4)
    >>> duration.convertTypeToQuarterLength('quarter', 0, [tup])
    Fraction(4, 5)

    >>> tup = duration.Tuplet(numberNotesActual = 3, numberNotesNormal = 4)
    >>> duration.convertTypeToQuarterLength('quarter', 0, [tup])
    Fraction(4, 3)

    Also can handle those rare medieval dot groups
    (such as dotted-dotted half notes that take a full measure of 9/8.
    Conceptually, these are dotted-(dotted-half) notes.  See
    trecento.trecentoCadence for more information
    ).
    >>> duration.convertTypeToQuarterLength('half', dots = 1, dotGroups = [1,1])
    4.5
    '''
    if dType in typeToDuration:
        durationFromType = typeToDuration[dType]
    else:
        raise DurationException(
        "no such type (%s) avaliable for conversion" % dType)

    qtrLength = durationFromType

    # weird medieval notational device; rarely used.
    if dotGroups is not None and len(dotGroups) > 1:
        for dots in dotGroups:
            if dots > 0:
                qtrLength *= common.dotMultiplier(dots)
    else:
        qtrLength *= common.dotMultiplier(dots)

    if tuplets is not None and tuplets:
        qtrLength = opFrac(qtrLength)
        for tup in tuplets:
            qtrLength = opFrac(qtrLength * tup.tupletMultiplier())
    return qtrLength


def convertTypeToNumber(dType):
    '''Convert a duration type string (`dType`) to a numerical scalar representation that shows
    how many of that duration type fits within a whole note.

    >>> duration.convertTypeToNumber('quarter')
    4.0
    >>> duration.convertTypeToNumber('half')
    2.0
    >>> duration.convertTypeToNumber('1024th')
    1024.0
    >>> duration.convertTypeToNumber('maxima')
    0.125
    '''
    dTypeFound = None
    for num, typeName in typeFromNumDict.items():
        if dType == typeName:
            #dTypeFound = int(num) # not all of these are integers
            dTypeFound = num
            break
    if dTypeFound is None:
        raise DurationException("Could not determine durationNumber from %s"
        % dTypeFound)
    else:
        return dTypeFound


#-------------------------------------------------------------------------------


class TupletException(exceptions21.Music21Exception):
    pass


class Tuplet(object):
    '''
    A tuplet object is a representation of a musical tuplet (like a triplet).
    It expresses a ratio that modifies duration values and are stored in
    Duration objects in a "tuple" (immutable list; since there can be nested
    tuplets) in the duration's .tuplets property.

    The primary representation uses two pairs of note numbers and durations.

    The first pair of note numbers and durations describes the representation
    within the tuplet, or the value presented by the context. This is called
    "actual." In a standard 8th note triplet this would be 3, eighth.
    Attributes are `numberNotesActual`, `durationActual`.

    The second pair of note numbers and durations describes the space that
    would have been occupied in a normal context. This is called "normal." In a
    standard 8th note triplet this would be 2, eighth. Attributes are
    `numberNotesNormal`, `durationNormal`.

    If duration values are not provided, the `durationActual` and
    `durationNormal` are assumed to be eighths.

    If only one duration, either `durationActual` or `durationNormal`, is
    provided, both are set to the same value.

    Note that this is a duration modifier, or a generator of ratios to scale
    quarterLength values in Duration objects.

    >>> myTup = duration.Tuplet(numberNotesActual = 5, numberNotesNormal = 4)
    >>> print(myTup.tupletMultiplier())
    4/5


    In this case, the tupletMultiplier is a float because it can be expressed
    as a binary number:

    >>> myTup2 = duration.Tuplet(8, 5)
    >>> tm = myTup2.tupletMultiplier()
    >>> tm
    0.625

    >>> myTup2 = duration.Tuplet(6, 4, "16th")
    >>> print(myTup2.durationActual.type)
    16th

    >>> print(myTup2.tupletMultiplier())
    2/3

    Tuplets may be frozen, in which case they become immutable. Tuplets
    which are attached to Durations are automatically frozen.  Otherwise
    a tuplet could change without the attached duration knowing about it,
    which would be a real problem.

    >>> myTup.frozen = True
    >>> myTup.tupletActual = [3, 2]
    Traceback (most recent call last):
    TupletException: A frozen tuplet (or one attached to a duration) is immutable

    >>> myHalf = duration.Duration("half")
    >>> myHalf.appendTuplet(myTup2)
    >>> myTup2.tupletActual = [5, 4]
    Traceback (most recent call last):
    TupletException: A frozen tuplet (or one attached to a duration) is immutable

    Note that if you want to create a note with a simple Tuplet attached to it,
    you can just change the quarterLength of the note:

    >>> myNote = note.Note("C#4")
    >>> myNote.duration.quarterLength = 0.8
    >>> myNote.duration.quarterLength
    Fraction(4, 5)
    >>> myNote.duration.fullName
    'Quarter Quintuplet (4/5 QL)'

    >>> myNote.duration.tuplets
    (<music21.duration.Tuplet 5/4/quarter>,)
    
    OMIT_FROM_DOCS
    We should also have a tupletGroup spanner.

    object that groups note objects into larger groups.
    # TODO: use __setattr__ to freeze all properties, and make a metaclass
    # exceptions: tuplet type, tuplet id: things that don't affect length
    '''

    ### CLASS VARIABLES ###

    frozen = False

    ### INITIALIZER ###

    def __init__(self, *arguments, **keywords):
        #environLocal.printDebug(['creating Tuplet instance'])

        # necessary for some complex tuplets, interrupted, for instance

        if len(arguments) == 3:
            keywords['numberNotesActual'] = arguments[0]
            keywords['numberNotesNormal'] = arguments[1]
            keywords['durationActual'] = arguments[2]
            keywords['durationNormal'] = arguments[2]
        elif len(arguments) == 2:
            keywords['numberNotesActual'] = arguments[0]
            keywords['numberNotesNormal'] = arguments[1]

        if 'tupletId' in keywords:
            self.tupletId = keywords['tupletId']
        else:
            self.tupletId = 0

        if 'nestedLevel' in keywords:
            self.nestedLevel = keywords['nestedLevel']
        else:
            self.nestedLevel = 1

        # actual is the count of notes that happen in this space
        # this is not the previous/expected duration of notes that happen
        if 'numberNotesActual' in keywords:
            self.numberNotesActual = keywords['numberNotesActual']
        else:
            self.numberNotesActual = 3

        # this stores a durationTuple
        if 'durationActual' in keywords and keywords['durationActual'] != None:
            if isinstance(keywords['durationActual'], basestring):
                self.durationActual = durationTupleFromTypeDots(keywords['durationActual'], 0)
            elif common.isIterable(keywords['durationActual']):
                self.durationActual = durationTupleFromTypeDots(keywords['durationActual'][0], keywords['durationActual'][1])
            else:
                self.durationActual = keywords['durationActual']
        else:
            self.durationActual = durationTupleFromTypeDots("eighth", 0)

        # normal is the space that would normally be occupied by the tuplet span
        if 'numberNotesNormal' in keywords:
            self.numberNotesNormal = keywords['numberNotesNormal']
        else:
            self.numberNotesNormal = 2


        if 'durationNormal' in keywords and keywords['durationNormal'] != None:
            if isinstance(keywords['durationNormal'], basestring):
                self.durationNormal = durationTupleFromTypeDots(keywords['durationNormal'], 0)
            elif common.isIterable(keywords['durationNormal']):
                self.durationNormal = durationTupleFromTypeDots(keywords['durationNormal'][0],keywords['durationNormal'][1])
            else:
                self.durationNormal = keywords['durationNormal']
        else:
            self.durationNormal = durationTupleFromTypeDots("eighth", 0)

        # Type is start, stop, or startStop: determines whether to start or stop
        # the bracket/group drawing
        # startStop is not used in musicxml, it will be encoded
        # as two notations (start + stop) in musicxml
        self.type = None
        self.bracket = True # true or false
        self.placement = "above" # above or below
        self.tupletActualShow = "number" # could be "number","type", or "none"
        self.tupletNormalShow = None # for ratios?

        # this attribute is not yet used anywhere
        #self.nestedInside = ""  # could be a tuplet object

    ### SPECIAL METHODS ###

    def __repr__(self):
        return ("<music21.duration.Tuplet %d/%d/%s>" % (self.numberNotesActual, self.numberNotesNormal, self.durationNormal.type))

    ### PUBLIC METHODS ###

    def augmentOrDiminish(self, amountToScale):
        '''
        Given a number greater than zero,
        multiplies the current quarterLength of the
        duration by the number and resets the components
        for the duration (by default).  Or if inPlace is
        set to False, returns a new duration that has
        the new length.

        Note that the default for inPlace is the opposite
        of what it is for augmentOrDiminish on a Stream.
        This is done purposely to reflect the most common
        usage.

        >>> a = duration.Tuplet()
        >>> a.setRatio(6,2)
        >>> a.tupletMultiplier()
        Fraction(1, 3)
        >>> a.durationActual
        DurationTuple(type='eighth', dots=0, quarterLength=0.5)

        >>> c = a.augmentOrDiminish(.5)
        >>> c.durationActual
        DurationTuple(type='16th', dots=0, quarterLength=0.25)

        >>> c.tupletMultiplier()
        Fraction(1, 3)
        '''
        if not amountToScale > 0:
            raise DurationException('amountToScale must be greater than zero')
        # TODO: scale the triplet in the same manner as Durations

        post = copy.deepcopy(self)
        post.frozen = False

        # duration units scale
        post.durationActual = post.durationActual.augmentOrDiminish(amountToScale)
        post.durationNormal = post.durationNormal.augmentOrDiminish(amountToScale)

        # ratios stay the same
        #self.numberNotesActual = actual
        #self.numberNotesNormal = normal
        return post

    def setDurationType(self, durType):
        '''Set the Duration for both actual and normal.

        A type string or quarter length can be given.


        >>> a = duration.Tuplet()
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.totalTupletLength()
        1.0
        >>> a.setDurationType('half')
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.totalTupletLength()
        4.0

        >>> a.setDurationType(2)
        >>> a.totalTupletLength()
        4.0
        >>> a.setDurationType(4)
        >>> a.totalTupletLength()
        8.0
        '''
        if self.frozen is True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        if common.isNum(durType):
            durType = convertQuarterLengthToType(durType)

        self.durationActual = durationTupleFromTypeDots(durType, self.durationActual.dots)
        self.durationNormal = durationTupleFromTypeDots(durType, self.durationActual.dots)

    def setRatio(self, actual, normal):
        '''Set the ratio of actual divisions to represented in normal divisions.
        A triplet is 3 actual in the time of 2 normal.

        >>> a = duration.Tuplet()
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.setRatio(6,2)
        >>> a.tupletMultiplier()
        Fraction(1, 3)

        One way of expressing 6/4-ish triplets without numbers:
        >>> a = duration.Tuplet()
        >>> a.setRatio(3,1)
        >>> a.durationActual = duration.durationTupleFromTypeDots('quarter', 0)
        >>> a.durationNormal = duration.durationTupleFromTypeDots('half', 0)
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.totalTupletLength()
        2.0
        '''
        if self.frozen is True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")

        self.numberNotesActual = actual
        self.numberNotesNormal = normal

    def totalTupletLength(self):
        '''
        The total duration in quarter length of the tuplet as defined, assuming that
        enough notes existed to fill all entire tuplet as defined.

        For instance, 3 quarters in the place of 2 quarters = 2.0
        5 half notes in the place of a 2 dotted half notes = 6.0
        (In the end it's only the denominator that matters)


        >>> a = duration.Tuplet()
        >>> a.totalTupletLength()
        1.0
        >>> a.numberNotesActual = 3
        >>> a.durationActual = duration.durationTupleFromTypeDots('half', 0)
        >>> a.numberNotesNormal = 2
        >>> a.durationNormal = duration.durationTupleFromTypeDots('half', 0)
        >>> a.totalTupletLength()
        4.0
        >>> a.setRatio(5,4)
        >>> a.totalTupletLength()
        8.0
        >>> a.setRatio(5,2)
        >>> a.totalTupletLength()
        4.0
        '''
        n = self.numberNotesNormal
        return opFrac(n * self.durationNormal.quarterLength)

    def tupletMultiplier(self):
        '''Get a Fraction() by which to scale the duration that
        this Tuplet is associated with.

        >>> myTuplet = duration.Tuplet()
        >>> myTuplet.tupletMultiplier()
        Fraction(2, 3)
        >>> myTuplet.tupletActual = [5, duration.Duration('eighth')]
        >>> myTuplet.numberNotesActual
        5
        >>> myTuplet.durationActual.type
        'eighth'
        >>> print(myTuplet.tupletMultiplier())
        2/5
        >>> myTuplet.numberNotesNormal = 4
        >>> print(myTuplet.tupletMultiplier())
        4/5
        
        '''
        lengthActual = self.durationActual.quarterLength
        return opFrac(self.totalTupletLength() / (
                lengthActual * self.numberNotesActual))

    ### PUBLIC PROPERTIES ###

    @property
    def fullName(self):
        '''
        Return the most complete representation of this tuplet in a readable
        form.

        >>> t = duration.Tuplet(numberNotesActual = 5, numberNotesNormal = 2)
        >>> t.fullName
        'Quintuplet'

        >>> t = duration.Tuplet(numberNotesActual = 3, numberNotesNormal = 2)
        >>> t.fullName
        'Triplet'

        >>> t = duration.Tuplet(numberNotesActual = 17, numberNotesNormal = 14)
        >>> t.fullName
        'Tuplet of 17/14ths'

        '''
        # actual is what is presented to viewer
        numActual = self.numberNotesActual
        numNormal = self.numberNotesNormal
        #dur = self.durationActual

        if numActual == 3 and numNormal == 2:
            return 'Triplet'
        elif numActual == 5 and numNormal in (4, 2):
            return 'Quintuplet'
        elif numActual == 6 and numNormal == 4:
            return 'Sextuplet'
        ordStr = common.ordinalAbbreviation(numNormal, plural=True)
        return 'Tuplet of %s/%s%s' % (numActual, numNormal, ordStr)

    @property
    def tupletActual(self):
        '''
        Get or set a two element list of number notes actual and duration
        actual.
        '''
        return [self.numberNotesActual, self.durationActual]

    @tupletActual.setter
    def tupletActual(self, tupList):
        if self.frozen is True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        self.numberNotesActual, self.durationActual = tupList

    @property
    def tupletNormal(self):
        '''
        Get or set a two element list of number notes actual and duration
        normal.
        '''
        return self.numberNotesNormal, self.durationNormal

    @tupletNormal.setter
    def tupletNormal(self, tupList):
        if self.frozen is True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        self.numberNotesNormal, self.durationNormal = tupList


#------------------------------------------------------------------------------------
DurationTuple = namedtuple('DurationTuple', 'type dots quarterLength')

def _augmentOrDiminishTuple(self, amountToScale):
    return durationTupleFromQuarterLength(self.quarterLength * amountToScale)
DurationTuple.augmentOrDiminish = _augmentOrDiminishTuple
del _augmentOrDiminishTuple

def _durtationTupleOrdinal(self):
    '''
    Converts type to an ordinal number where maxima = 1 and 1024th = 14;
    whole = 4 and quarter = 6.  Based on duration.ordinalTypeFromNum

    >>> a = duration.DurationTuple('whole', 0, 4.0)
    >>> a.ordinal
    4

    >>> b = duration.DurationTuple('maxima', 0, 32.0)
    >>> b.ordinal
    1

    >>> c = duration.DurationTuple('1024th', 0, 1.0/256)
    >>> c.ordinal
    14
    '''
    ordinalFound = None
    for i in range(len(ordinalTypeFromNum)):
        if self.type == ordinalTypeFromNum[i]:
            ordinalFound = i
            break
    if ordinalFound is None:
        raise DurationException(
            "Could not determine durationNumber from %s" % ordinalFound)
    else:
        return ordinalFound

DurationTuple.ordinal = property(_durtationTupleOrdinal)

_durationTupleCacheTypeDots = {}
_durationTupleCacheQuarterLength = {}

#------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------


class DurationException(exceptions21.Music21Exception):
    pass


class Duration(SlottedObject):
    '''
    Durations are one of the most important objects in music21. A Duration
    represents a span of musical time measurable in terms of quarter notes (or
    in advanced usage other units). For instance, "57 quarter notes" or "dotted
    half tied to quintuplet sixteenth note" or simply "quarter note."

    A Duration object is made of one or more immutable DurationTuple objects stored on the
    `components` list.

    Multiple DurationTuples in a single Duration may be used to express tied
    notes, or may be used to split duration across barlines or beam groups.
    Some Duration objects are not expressible as a single notation unit.

    Duration objects are not Music21Objects.

    If a single argument is passed to Duration() and it is a string, then it is
    assumed to be a type, such as 'half', 'eighth', or '16th', etc.  If that
    single argument is a number then it is assumed to be a quarterLength (2 for
    half notes, .5 for eighth notes, .75 for dotted eighth notes, .333333333
    for a triplet eighth, etc.).  If one or more named arguments are passed
    then the Duration() is configured according to those arguments.  Supported
    arguments are 'type', 'dots', 'quarterLength', or 'components'.

    Example 1: a triplet eighth configured by quarterLength:

    >>> d = duration.Duration(.333333333)
    >>> d.type
    'eighth'

    >>> d.tuplets
    (<music21.duration.Tuplet 3/2/eighth>,)

    Example 2: A Duration made up of multiple
    :class:`music21.duration.DurationTuple` objects automatically configured by
    the specified quarterLength.

    >>> d2 = duration.Duration(.625)
    >>> d2.type
    'complex'

    >>> d2.components
    (DurationTuple(type='eighth', dots=0, quarterLength=0.5), 
     DurationTuple(type='32nd', dots=0, quarterLength=0.125))

    Example 3: A Duration configured by keywords.

    >>> d3 = duration.Duration(type='half', dots=2)
    >>> d3.quarterLength
    3.5
    '''

    ### CLASS VARIABLES ###

    isGrace = False

    __slots__ = (
        '_linked',
        '_components',
        '_qtrLength',
        '_tuplets',
        '_componentsNeedUpdating',
        '_quarterLengthNeedsUpdating',
        '_typeNeedsUpdating',
        '_unlinkedType',
        '_dotGroups',
        
        '_client'
        )

    ### INITIALIZER ###

    def __init__(self, *arguments, **keywords):
        '''
        First positional argument is assumed to be type string or a quarterLength.
        '''
        # store a reference to the object that has this duration object as a property
        self._client = None

        self._componentsNeedUpdating = False
        self._quarterLengthNeedsUpdating = False
        self._typeNeedsUpdating = False

        self._unlinkedType = None
        self._dotGroups = (0,)
        self._tuplets = ()  # an empty tuple
        self._qtrLength = 0.0
        # DurationTuples go here
        self._components = []
        # defer updating until necessary
        self._quarterLengthNeedsUpdating = False
        self._linked = True  
        for a in arguments:
            if common.isNum(a) and 'quarterLength' not in keywords:
                keywords['quarterLength'] = a
            elif common.isStr(a) and 'type' not in keywords:
                keywords['type'] = a
            elif isinstance(a, DurationTuple):
                self.addDurationTuple(a)
            else:
                raise DurationException("Cannot parse argument {0}".format(a))

        
        if 'durationTuple' in keywords:
            self.addDurationTuple(keywords['durationTuple'])
        
        if 'dots' in keywords and keywords['dots'] is not None:
            storeDots = int(keywords['dots'])
        else:
            storeDots = 0
            
        if "components" in keywords:
            self.components = keywords["components"]
            # this is set in _setComponents
            #self._quarterLengthNeedsUpdating = True
        if 'type' in keywords:
            nt = durationTupleFromTypeDots(keywords['type'], storeDots)
            self.addDurationTuple(nt)
        # permit as keyword so can be passed from notes
        elif 'quarterLength' in keywords:
            self.quarterLength = keywords['quarterLength']
            
        if 'client' in keywords:
            self.client = keywords['client']

    ### SPECIAL METHODS ###

    def __eq__(self, other):
        '''
        Test equality. Note: this may not work with Tuplets until we
        define equality tests for tuplets.

        >>> aDur = duration.Duration('quarter')
        >>> bDur = duration.Duration('16th')
        >>> cDur = duration.Duration('16th')
        >>> aDur == bDur
        False

        >>> cDur == bDur
        True

        >>> dDur = duration.Duration(0.0)
        >>> eDur = duration.Duration(0.0)
        >>> dDur == eDur
        True
        '''
        if other is None or not isinstance(other, Duration):
            return False

        if self.isComplex == other.isComplex:
            if len(self.components) == len(other.components):
                if len(self.components) == 0:
                    return True
                elif self.type == other.type:
                    if self.dots == other.dots:
                        if self.tuplets == other.tuplets:
                            if self.quarterLength == other.quarterLength:
                                return True
        return False

    def __ne__(self, other):
        '''Test not equality.

        >>> aDur = duration.Duration('quarter')
        >>> bDur = duration.Duration('16th')
        >>> cDur = duration.Duration('16th')
        >>> aDur != bDur
        True

        >>> cDur != bDur
        False
        '''
        return not self.__eq__(other)

    def __repr__(self):
        if self.linked is True:
            return '<{0}.{1} {2}>'.format(self.__module__, self.__class__.__name__, self.quarterLength)
        else:
            return '<{0}.{1} unlinked type:{2} quarterLength:{3}>'.format(
                        self.__module__, self.__class__.__name__, self.type, self.quarterLength)

    ## unwrap weakref for pickling
    def __deepcopy__(self, memo):
        '''
        Do some very fast creations...
        '''
        if (self._componentsNeedUpdating is False and 
                len(self._components) == 1 and
                self._dotGroups == (0,) and 
                self._linked is True and 
                len(self._tuplets) == 0): ## 99% of notes...
            # ignore all but components
            return self.__class__(durationTuple=self._components[0])
        elif (self._componentsNeedUpdating is False and
                len(self._components) == 0 and
                self._dotGroups == (0,) and 
                len(self._tuplets) == 0 and
                self._linked is True):
            # ignore all
            return self.__class__()
        else:
            return common.defaultDeepcopy(self, memo)


    def __getstate__(self):
        self._client = common.unwrapWeakref(self._client)
        return SlottedObject.__getstate__(self)

    def __setstate__(self, state):
        SlottedObject.__setstate__(self, state)
        self._client = common.wrapWeakref(self._client)

    
    
    def _getClient(self):
        return common.unwrapWeakref(self._client)

    def _setClient(self, newClient):
        self._client = common.wrapWeakref(newClient)

    client = property(_getClient, _setClient, doc='''
        A duration's "client" is the object that holds this
        duration as a property.  It is informed whenever the duration changes.
    ''')

    ### PRIVATE METHODS ###

    def _updateComponents(self):
        '''
        This method will re-construct components and thus is not good if the
        components are already configured as you like
        '''
        # this update will not be necessary
        self._quarterLengthNeedsUpdating = False
        if self.linked is True:
            try:
                qlc = quarterConversion(self._qtrLength)
                self.components = list(qlc.components)
                if qlc.tuplet is not None:
                    self.tuplets = (qlc.tuplet,)
            except DurationException:                
                environLocal.printDebug("problem updating components of note with quarterLength %s, chokes quarterLengthToDurations\n" % self.quarterLength)
                raise
        self._componentsNeedUpdating = False

    ### PUBLIC METHODS ###
    def _getLinked(self):
        '''
        Gets or sets the Linked property -- if linked (default) then type, dots, tuplets are
        always coherent with quarterLength.  If not, then they are separate.
        '''
        return self._linked
    
    def _setLinked(self, value):
        if value not in (True, False):
            raise DurationException("Linked can only be True or False, not {0}".format(value))
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        if value is False:
            self._unlinkedType = self.type
        self._linked = value

    linked = property(_getLinked, _setLinked)
        

    def addDurationTuple(self, dur):
        '''
        Add a DurationTuple or a Duration's components to this Duration.
        Does not simplify the Duration.  For instance, adding two
        quarter notes results in two tied quarter notes, not one half note.
        See `consolidate` below for more info on how to do that.

        >>> a = duration.Duration('quarter')
        >>> b = duration.durationTupleFromTypeDots('quarter', 0)
        >>> a.addDurationTuple(b)
        >>> a.quarterLength
        2.0
        >>> a.type
        'complex'
        '''
        if isinstance(dur, DurationTuple):
            self._components.append(dur)
        elif isinstance(dur, Duration): # its a Duration object
            for c in dur.components:
                self._components.append(c)
        else: # its a number that may produce more than one component
            for c in Duration(dur).components:
                self._components.append(c)
                
        if self.linked:
            self._quarterLengthNeedsUpdating = True

        self.informClient()


    def appendTuplet(self, newTuplet):
        newTuplet.frozen = True
        self.tuplets = self.tuplets + (newTuplet,)
        self.informClient()


    def augmentOrDiminish(self, amountToScale, retainComponents=False):
        '''
        Given a number greater than zero,
        multiplies the current quarterLength of the
        duration by the number and resets the components
        for the duration (by default).  Or if inPlace is
        set to False, returns a new duration that has
        the new length.

        Note that the default for inPlace is the opposite
        of what it is for augmentOrDiminish on a Stream.
        This is done purposely to reflect the most common
        usage.

        >>> aDur = duration.Duration()
        >>> aDur.quarterLength = 1.5 # dotted quarter
        >>> cDur = aDur.augmentOrDiminish(2)
        >>> cDur.quarterLength
        3.0
        >>> cDur.type
        'half'
        >>> cDur.dots
        1


        A complex duration that cannot be expressed as a single notehead (component)

        >>> bDur = duration.Duration()
        >>> bDur.quarterLength = 2.125 # requires components
        >>> bDur.quarterLength
        2.125
        >>> len(bDur.components)
        2
        >>> bDur.components
        (DurationTuple(type='half', dots=0, quarterLength=2.0), 
         DurationTuple(type='32nd', dots=0, quarterLength=0.125))

        >>> cDur = bDur.augmentOrDiminish(2, retainComponents=True)
        >>> cDur.quarterLength
        4.25
        >>> cDur.tuplets
        ()
        >>> cDur.components
        (DurationTuple(type='whole', dots=0, quarterLength=4.0), 
         DurationTuple(type='16th', dots=0, quarterLength=0.25))


        >>> dDur = bDur.augmentOrDiminish(2, retainComponents=False)
        >>> dDur.components
        (DurationTuple(type='whole', dots=0, quarterLength=4.0), 
         DurationTuple(type='16th', dots=0, quarterLength=0.25))
        '''
        if not amountToScale > 0:
            raise DurationException('amountToScale must be greater than zero')

        post = copy.deepcopy(self)

        if retainComponents:
            newComponents = []
            for d in post.components:
                newComponents.append(d.augmentOrDiminish(amountToScale))
            post.components = newComponents
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = True
        else:
            post.quarterLength = post.quarterLength * amountToScale

        return post

    def clear(self):
        '''
        Permit all components to be removed.
        (It is not clear yet if this is needed: YES! for zero duration!)

        >>> a = duration.Duration()
        >>> a.quarterLength = 4
        >>> a.type
        'whole'
        >>> a.components
        (DurationTuple(type='whole', dots=0, quarterLength=4.0),)

        >>> a.clear()

        >>> a.components
        ()
        >>> a.type
        'zero'
        >>> a.quarterLength
        0.0
        '''
        self._components = []
        self._componentsNeedUpdating = False
        self._quarterLengthNeedsUpdating = True
        self.informClient()

    def componentIndexAtQtrPosition(self, quarterPosition):
        '''returns the index number of the duration component sounding at
        the given quarter position.

        Note that for 0 and the last value, the object is returned.


        >>> components = []
        >>> components.append(duration.Duration('quarter'))
        >>> components.append(duration.Duration('quarter'))
        >>> components.append(duration.Duration('quarter'))

        >>> a = duration.Duration()
        >>> a.components = components
        >>> a.updateQuarterLength()
        >>> a.quarterLength
        3.0
        >>> a.componentIndexAtQtrPosition(.5)
        0
        >>> a.componentIndexAtQtrPosition(1.5)
        1
        >>> a.componentIndexAtQtrPosition(2.5)
        2


        this is odd behavior:

        e.g. given d1, d2, d3 as 3 quarter notes and
        self.components = [d1, d2, d3]

        then

        self.componentIndexAtQtrPosition(1.5) == d2
        self.componentIndexAtQtrPosition(2.0) == d3
        self.componentIndexAtQtrPosition(2.5) == d3
        '''

#         if self._expansionNeeded:
#             self.expand()
#             self._expansionNeeded = False
        quarterPosition = opFrac(quarterPosition)

        if self.components == []:
            raise DurationException(
                "Need components to run getComponentIndexAtQtrPosition")
        elif quarterPosition > self.quarterLength:
            raise DurationException(
                "position is after the end of the duration")

        elif quarterPosition < 0:
            # values might wrap around from the other side
            raise DurationException(
                "position is before the start of the duration")

        # it seems very odd that thes return objects
        # while the method name suggests indices will be returned
        if quarterPosition == 0:
            return self.components[0]
        elif quarterPosition == self.quarterLength:
            return self.components[-1]

        currentPosition = 0.0
        indexFound = None
        for i in range(len(self.components)):
            currentPosition = opFrac(currentPosition + self.components[i].quarterLength)
            if currentPosition > quarterPosition:
                indexFound = i
                break
        if indexFound is None:
            raise DurationException(
                "Could not match quarter length within an index.")
        else:
            return indexFound

    def componentStartTime(self, componentIndex):
        '''
        For a valid component index value, this returns the quarter note offset
        at which that component would start.

        This does not handle fractional arguments.

        >>> components = []
        >>> qdt = duration.DurationTuple('quarter', 0, 1.0)
        >>> components.append(qdt)
        >>> components.append(qdt)
        >>> components.append(qdt)

        >>> a = duration.Duration()
        >>> a.components = components
        >>> a.quarterLength
        3.0
        >>> a.componentStartTime(0)
        0.0
        >>> a.componentStartTime(1)
        1.0
        '''
        if componentIndex not in range(len(self.components)):
            raise DurationException(('invalid component index value (%s) ' + \
                'submitted; value must be integers between 0 and %s') % (
                componentIndex, len(self.components) - 1))

        currentPosition = 0.0
        for i in range(componentIndex):
            currentPosition += self.components[i].quarterLength
        return currentPosition

    def consolidate(self):
        '''
        Given a Duration with multiple components, consolidate into a single
        Duration. This can only be based on quarterLength; this is
        destructive: information is lost from components.

        This cannot be done for all Durations, as DurationTuples cannot express all durations
        
        >>> a = duration.Duration()
        >>> a.fill(['quarter', 'half', 'quarter'])
        >>> a.quarterLength
        4.0
        >>> len(a.components)
        3
        >>> a.type
        'complex'
        
        After consolidate:
        
        >>> a.consolidate()
        >>> a.quarterLength
        4.0
        >>> len(a.components)
        1

        It gains a type!

        >>> a.type
        'whole'



        If the type cannot be expressed then the type is inexpressible


        >>> a = duration.Duration()
        >>> a.fill(['quarter', 'half', 'half'])
        >>> a.quarterLength
        5.0
        >>> len(a.components)
        3
        >>> a.type
        'complex'
        
        After consolidate:
        
        >>> a.consolidate()
        >>> a.quarterLength
        5.0
        >>> len(a.components)
        1

        It gains a type!

        >>> a.type
        'inexpressible'


        '''
        if len(self.components) == 1:
            pass # nothing to be done
        else:
            dur = durationTupleFromQuarterLength(self.quarterLengthNoTuplets)
            # if quarter length is not notatable, will automatically unlink
            # some notations will not properly unlink, and raise an error
            self.components = [dur]



    def fill(self, quarterLengthList=('quarter', 'half', 'quarter')):
        '''Utility method for testing; a quick way to fill components. This will
        remove any exisiting values.
        '''
        self.components = []
        for x in quarterLengthList:
            self.addDurationTuple(Duration(x))
        self.informClient()
            

    def getGraceDuration(self, appogiatura=False):
        '''
        Return a deepcopy of this Duration as a GraceDuration instance with the same types.

        >>> d = duration.Duration(1.25)
        >>> d
        <music21.duration.Duration 1.25>
        >>> d.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0), 
         DurationTuple(type='16th', dots=0, quarterLength=0.25))

        >>> gd = d.getGraceDuration()
        >>> gd
        <music21.duration.GraceDuration unlinked type:zero quarterLength:0.0>
        >>> gd.quarterLength
        0.0
        >>> gd.components
        (DurationTuple(type='quarter', dots=0, quarterLength=0.0), 
         DurationTuple(type='16th', dots=0, quarterLength=0.0))

        D is unchanged.

        >>> d.quarterLength
        1.25
        
        
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()

        # create grace duration
        if appogiatura is True:
            gd = AppogiaturaDuration()
        else:
            gd = GraceDuration()
            
        newComponents = []
        for c in self.components:
            newComponents.append(DurationTuple(c.type, c.dots, 0.0))
        gd.components = newComponents # set new components
        gd.linked = False
        gd.quarterLength = 0.0        
        return gd


    def informClient(self):
        '''
        call durationChanged(quarterLength) on any call that changes
        the quarterLength
        
        returns False if there was no need to inform or if client
        was not set.  Otherwise returns True
        '''
        if self._quarterLengthNeedsUpdating is True:
            old_qtrLength = self._qtrLength
            self.updateQuarterLength()
            if self._qtrLength == old_qtrLength:
                return False
        cl = self.client
        if cl is None:
            return False
        cl.durationChanged(self._qtrLength)
        return True
            

    def sliceComponentAtPosition(self, quarterPosition):
        '''
        Given a quarter position within a component, divide that
        component into two components.

        >>> a = duration.Duration()
        >>> a.clear() # need to remove default
        >>> components = []

        >>> a.addDurationTuple(duration.Duration('quarter'))
        >>> a.addDurationTuple(duration.Duration('quarter'))
        >>> a.addDurationTuple(duration.Duration('quarter'))
        >>> a.quarterLength
        3.0
        >>> a.sliceComponentAtPosition(.5)
        >>> a.quarterLength
        3.0
        >>> len(a.components)
        4
        >>> a.components[0].type
        'eighth'
        >>> a.components[1].type
        'eighth'
        >>> a.components[2].type
        'quarter'
        '''

        # this may return a Duration object; we are not sure
        sliceIndex = self.componentIndexAtQtrPosition(quarterPosition)

        # get durObj that qPos is within
        if common.isNum(sliceIndex):
            durObjSlice = self.components[sliceIndex]
        else: # assume that we got an object
            durObjSlice = sliceIndex

        # this will not work if componentIndexAtQtrPosition returned an obj
        # get the start pos in ql of this dur obj
        durationStartTime = self.componentStartTime(sliceIndex)
        # find difference between desired split and start pos of this dur obj
        # this is the left side dur
        slicePoint = quarterPosition - durationStartTime
        # this is the right side dur
        remainder = durObjSlice.quarterLength - slicePoint

        if remainder == 0 or slicePoint == 0: # nothing to be done
            # this might not be an error
            raise DurationException(
            "no slice is possible at this quarter position")
        else:
            d1 = durationTupleFromQuarterLength(slicePoint)
            d2 = durationTupleFromQuarterLength(remainder)

            self._components[sliceIndex: (sliceIndex + 1)] = [d1, d2]
            # lengths should be the same as it was before
            self.updateQuarterLength()

    def currentComponents(self):
        '''
        Advanced Method:
        
        returns the current components WITHOUT running the component updater.
        
        Needed by some internal methods.
        
        >>> d = duration.Duration()
        >>> d.currentComponents()
        []
        '''
        return self._components

    def splitDotGroups(self):
        '''
        splits a dotGroup-duration (of 1 component) into a new duration of two
        components.  Returns a new duration

        Probably does not handle properly tuplets of dot-groups.
        Never seen one, so probably okay.

        >>> d1 = duration.Duration(type = 'half')
        >>> d1.dotGroups = (1,1)
        >>> d1.quarterLength
        4.5
        >>> d2 = d1.splitDotGroups()
        >>> d2.components
        (DurationTuple(type='half', dots=1, quarterLength=3.0), 
         DurationTuple(type='quarter', dots=1, quarterLength=1.5))
        
        >>> d2.quarterLength
        4.5

        Here's how a system that does not support dotGroups can still display
        the notes accurately.  N.B. MusicXML does this automatically, so
        no need.

        >>> n1 = note.Note()
        >>> n1.duration = d1
        >>> n1.duration = n1.duration.splitDotGroups()
        >>> n1.duration.components
        (DurationTuple(type='half', dots=1, quarterLength=3.0), 
         DurationTuple(type='quarter', dots=1, quarterLength=1.5))
        
        >>> s1 = stream.Stream()
        >>> s1.append(meter.TimeSignature('9/8'))
        >>> s1.append(n1)
        >>> #_DOCS_SHOW s1.show('lily.png')
        .. image:: images/duration_splitDotGroups.*

        >>> n2 = note.Note()
        >>> n2.duration.type = 'quarter'
        >>> n2.duration.dotGroups = (1,1)
        >>> n2.quarterLength
        2.25
        >>> #_DOCS_SHOW n2.show() # generates a dotted-quarter tied to dotted-eighth

        Does NOT handle tuplets etc.
        '''
        d = Duration()
        d.addDurationTuple(durationTupleFromTypeDots(self.type,1))
        d.addDurationTuple(durationTupleFromTypeDots(nextSmallerType(self.type),1))
        
        return d
#         dG = self.dotGroups
#         if len(dG) < 2:
#             return copy.deepcopy(self)
#         else:
#             newDuration = copy.deepcopy(self)
#             newDuration.dotGroups = [0]
#             newDuration.components[0].dots = dG[0]
#             for i in range(1, len(dG)):
#                 newComponent = copy.deepcopy(newDuration.components[i-1])
#                 newComponent.type = nextSmallerType(newDuration.components[i-1].type)
#                 newComponent.dots = dG[i]
#                 newDuration.components.append(newComponent)
#             return newDuration


    def updateQuarterLength(self):
        '''
        Look to components and determine quarter length.
        '''        
        if self.linked is True:
            self._qtrLength = opFrac(self.quarterLengthNoTuplets * self.aggregateTupletMultiplier())
            if self._dotGroups != (0,):
                for dots in self._dotGroups:
                    if dots > 0:
                        self._qtrLength *= common.dotMultiplier(dots)

        self._quarterLengthNeedsUpdating = False



    ### PUBLIC PROPERTIES ###

    @property
    def components(self):
        if self._componentsNeedUpdating:
            self._updateComponents()
        return tuple(self._components)

    @components.setter
    def components(self, value):
        # previously, self._componentsNeedUpdating was not set here
        # this needs to be set because if _componentsNeedUpdating is True
        # new components will be derived from quarterLength
        if self._components is not value:
            self._componentsNeedUpdating = False
            self.clear()
            for v in value:
                self.addDurationTuple(v)
            # this is True b/c components are not the same
            self._quarterLengthNeedsUpdating = True
            # must be cleared

    @property
    def dotGroups(self):
        '''
        Dot groups are medieval dotted-dotted notes (written one above another).
        For instance a half note with dotGroups = (1,1) represents a dotted half note that
        is itself dotted.  Worth 9 eighth notes (dotted-half tied to dotted-quarter).  It
        is not the same as a double-dotted half note, which is only worth 7 eighth notes.
        

        >>> from music21 import duration
        >>> a = duration.Duration()
        >>> a.type = 'half'
        >>> a.dotGroups
        (0,)
        >>> a.dots = 1
        

        >>> a.dotGroups = (1,1)
        >>> a.quarterLength
        4.5
        '''
        if self.dots == 0:
            return self._dotGroups
        elif self.dots != 0 and self._dotGroups == (0,):
            return (self.dots,)
        else:
            return self._dotGroups

    @dotGroups.setter
    def dotGroups(self, value):
        if not isinstance(value, tuple):
            raise DurationException('only tuple dotGroups values can be used with this method.')
        # removes dots from all components...
        for i in range(len(self._components)):
            self._components[i] = durationTupleFromTypeDots(self._components[i].type, 0)
        
        self._dotGroups = value
        self._quarterLengthNeedsUpdating = True

    @property
    def dots(self):
        '''
        Returns the number of dots in the Duration
        if it is a simple Duration.  Otherwise returns the number of dots on the first component

        Previously it could return None if it was not a simple duration which led to some
        terribly difficult to find errors.
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        if len(self.components) == 1:
            return self.components[0].dots
        elif len(self.components) > 1:
            return self.components[0].dots
        else:  # there must be 1 or more components
            return 0
            
    @dots.setter
    def dots(self, value):
        '''
        Set dots if a number, as first element

        >>> a = duration.Duration()
        >>> a.type = 'quarter'
        >>> a.dots = 1
        >>> a.quarterLength
        1.5
        >>> a.dots = 2
        >>> a.quarterLength
        1.75
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        if not common.isNum(value):
            raise DurationException('only numeric dot values can be used with this method.')
        if len(self._components) == 1:
            self._components[0] = durationTupleFromTypeDots(self.components[0].type, value)
            self._quarterLengthNeedsUpdating = True
            self.informClient()
        elif len(self._components) > 1:
            raise DurationException("setting type on Complex note: Myke and Chris need to decide what that means")
        else:  # there must be 1 or more components
            raise DurationException("Cannot set dots on an object with zero DurationTuples in its duration.components")

    @property
    def fullName(self):
        '''
        Return the most complete representation of this Duration, providing
        dots, type, tuplet, and quarter length representation.

        >>> d = duration.Duration(quarterLength=1.5)
        >>> d.fullName
        'Dotted Quarter'

        >>> d = duration.Duration(type='half')
        >>> d.fullName
        'Half'

        >>> d = duration.Duration(quarterLength=1.25)
        >>> d.fullName
        'Quarter tied to 16th (1 1/4 total QL)'

        >>> d = duration.Duration(quarterLength=0.333333)
        >>> d.fullName
        'Eighth Triplet (1/3 QL)'

        >>> d = duration.Duration(quarterLength=0.666666)
        >>> d.fullName
        'Quarter Triplet (2/3 QL)'

        >>> d = duration.Duration(quarterLength=0.571428)
        >>> d.fullName
        'Quarter Tuplet of 7/4ths (4/7 QL)'

        >>> d = duration.Duration(quarterLength=0)
        >>> d.fullName
        'Zero Duration (0 total QL)'
        '''
        totalMsg = []
        if self.tuplets:
            tupletStrList = []
            for tup in self.tuplets:
                tupletStrList.append(tup.fullName)
            tupletStr = ' '.join(tupletStrList)
        else:
            tupletStr = ""
        
        for c in self.components:
            dots = c.dots
            if dots == 1:
                dotStr = 'Dotted'
            elif dots == 2:
                dotStr = 'Double Dotted'
            elif dots == 3:
                dotStr = 'Triple Dotted'
            elif dots == 4:
                dotStr = 'Quadruple Dotted'
            elif dots > 4:
                dotStr = ('%d-Times Dotted' % dots)
            else:
                dotStr = ""
            
            msg = []
            typeStr = c.type
            if dots >= 2 or (typeStr != 'longa' and typeStr != 'maxima'):
                if dotStr is not None:
                    msg.append('%s ' % dotStr)
            else:
                if dots == 0:
                    msg.append('Imperfect ')
                elif dots == 1:
                    msg.append('Perfect ')
            if typeStr[0] in ('1', '2', '3', '5', '6'):
                pass # do nothing with capitalization
            else:
                typeStr = typeStr.title()
            if typeStr.lower() == 'complex':
                pass
            else:
                msg.append('%s ' % typeStr)
                
            if tupletStr != "":
                msg.append('%s ' % tupletStr)
            if tupletStr != "" or dots >= 3 or typeStr.lower() == 'complex':
                qlStr = common.mixedNumeral(self.quarterLength)
                msg.append('(%s QL)' % (qlStr))
            totalMsg.append("".join(msg).strip())
        
        if len(self.components) == 0:
            totalMsg.append('Zero Duration ')
        
        outMsg = ""
        if len(totalMsg) > 1:
            outMsg = ' tied to '.join(totalMsg)
        else:
            outMsg = totalMsg[0]
        
        if len(self.components) != 1:
            qlStr = common.mixedNumeral(self.quarterLength)
            outMsg += ' (%s total QL)' % (qlStr)

        return outMsg

    @property
    def isComplex(self):
        '''
        Returns True if this Duration has more than one DurationTuple object on
        the `component` list.  That is to say if it's a single Duration that
        need multiple tied noteheads to represent.

        >>> aDur = duration.Duration()
        >>> aDur.quarterLength = 1.375
        >>> aDur.isComplex
        True

        >>> len(aDur.components)
        2

        >>> aDur.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0), 
         DurationTuple(type='16th', dots=1, quarterLength=0.375))
            
        >>> cDur = duration.Duration()
        >>> cDur.quarterLength = .25
        >>> cDur.isComplex
        False

        >>> len(cDur.components)
        1
        '''
        if len(self.components) > 1:
            return True
        else: 
            return False


    @property
    def ordinal(self):
        '''
        Get the ordinal value of the Duration.

        >>> d = duration.Duration()
        >>> d.quarterLength = 2.0
        >>> d.ordinal
        5
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()

        if len(self.components) > 1:
            return 'complex'
        elif len(self.components) == 1:
            return self.components[0].ordinal
        else:
            return None

    
    @property
    def quarterLengthNoTuplets(self):
        '''
        Returns the quarter length of the duration without taking into account triplets.
        
        Does not cache...
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        
        # tested, does return 0 if no components
        return sum([c.quarterLength for c in self._components])
    
    
    def _getQuarterLengthFloat(self):
        return float(self._getQuarterLengthRational())

    def _getQuarterLengthRational(self):
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        # this is set in updateQuarterLength
        #self._quarterLengthNeedsUpdating = False
        return self._qtrLength


    def _setQuarterLength(self, value):
        if self.linked is False:
            self._qtrLength = value
        elif self._qtrLength != value:
            value = opFrac(value)
            if value == 0.0 and self.linked is True:
                self.clear()
            self._qtrLength = value
            self._componentsNeedUpdating = True
            self._quarterLengthNeedsUpdating = False
            
            self.informClient()

    quarterLength      = property(_getQuarterLengthRational, _setQuarterLength)
    quarterLengthFloat = property(_getQuarterLengthFloat, _setQuarterLength,
                             doc='''
        Returns the quarter note length or Sets the quarter note length to
        the specified value.

        Currently (if the value is different from what is already stored)
        this wipes out any existing components, not preserving their type.
        So if you've set up Duration(1.5) as 3-eighth notes, setting
        Duration to 1.75 will NOT dot the last eighth note, but instead
        give you a single double-dotted half note.

        >>> a = duration.Duration()
        >>> a.quarterLength = 3.5
        >>> a.quarterLength
        3.5

        >>> for thisUnit in a.components:
        ...    print(duration.unitSpec(thisUnit))
        (3.5, 'half', 2, None, None, None)
            
        >>> a.quarterLength = 2.5
        >>> a.quarterLength
        2.5

        >>> for thisUnit in a.components:
        ...    print(duration.unitSpec(thisUnit))
        (2.0, 'half', 0, None, None, None)
        (0.5, 'eighth', 0, None, None, None)

        Note that integer values of quarter lengths get silently converted to floats (internally
        opFracs):

        >>> b = duration.Duration()
        >>> b.quarterLength = 5
        >>> b.quarterLength
        5.0
        >>> b.type  # complex because 5qL cannot be expressed as a single note.
        'complex'
        ''')

    @property
    def tuplets(self):
        '''
        return a tuple of Tuplet objects
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        return self._tuplets

    @tuplets.setter
    def tuplets(self, tupletTuple):
        #environLocal.printDebug(['assigning tuplets in Duration', tupletTuple])
        self._tuplets = tuple(tupletTuple)
        self._quarterLengthNeedsUpdating = True

    def aggregateTupletMultiplier(self):
        '''
        Returns the multiple of all the tuplet multipliers as an opFrac.

        This method is needed for MusicXML time-modification among other
        places.


        No tuplets...

        >>> complexDur = duration.Duration('eighth')
        >>> complexDur.aggregateTupletMultiplier()
        1.0
            
        With tuplets:
        
        >>> complexDur.appendTuplet(duration.Tuplet())
        >>> complexDur.aggregateTupletMultiplier()
        Fraction(2, 3)

        Nested tuplets are possible...

        >>> tup2 = duration.Tuplet()
        >>> tup2.setRatio(5, 4)
        >>> complexDur.appendTuplet(tup2)
        >>> complexDur.aggregateTupletMultiplier()
        Fraction(8, 15)
        '''
        currentMultiplier = 1
        for thisTuplet in self.tuplets:
            currentMultiplier *= thisTuplet.tupletMultiplier()
        return common.opFrac(currentMultiplier)
    
    ### PUBLIC PROPERTIES ###

    @property
    def classes(self):
        '''
        Returns a list containing the names (strings, not objects) of classes
        that this object belongs to -- starting with the object's class name
        and going up the mro() for the object.  Very similar to Perl's @ISA
        array.  See music21.Music21Object.classes for more details.
        '''
        return tuple([x.__name__ for x in self.__class__.mro()])
        # TODO: inherit from a protom21object...


    @property
    def type(self):
        '''
        Get or set the type of the Duration.

        >>> a = duration.Duration()
        >>> a.type = 'half'
        >>> a.quarterLength
        2.0

        >>> a.type= '16th'
        >>> a.quarterLength
        0.25
        '''
        if self.linked is False:
            return self._unlinkedType
        elif len(self.components) == 1:
            return self.components[0].type
        elif len(self.components) > 1:
            return 'complex'
        else: # there may be components and still a zero type
            return 'zero'

    @type.setter
    def type(self, value):
        # need to check that type is valid
        if value not in ordinalTypeFromNum and value not in ('inexpressible', 'complex'):
            raise DurationException("no such type exists: %s" % value)
        
        if self.linked is True:
            nt = durationTupleFromTypeDots(value, self.dots)
            self.components = [nt]
            self._quarterLengthNeedsUpdating = True
            self.informClient()

        else:
            self._unlinkedType = value

def durationTupleFromQuarterLength(ql=1.0):
    '''
    Returns a DurationTuple for a given quarter length
    if the ql can be expressed as a type and number of dots
    (no tuplets, no complex duration, etc.).  If it can't be expressed,
    returns an "inexpressible" DurationTuple.
    '''
    try:
        return _durationTupleCacheQuarterLength[ql]
    except KeyError:
        ql = opFrac(ql)
        dots, durType = dottedMatch(ql) 
        if durType is not False:
            nt = DurationTuple(durType, dots, ql)
            _durationTupleCacheQuarterLength[ql] = nt
            return nt
        else:
            return DurationTuple('inexpressible', 0, ql)
        
            

def durationTupleFromTypeDots(durType='quarter', dots=0):
    '''
    Returns a DurationTuple (which knows its quarterLength) for
    a given type and dots (no tuplets)
    
    >>> dt = duration.durationTupleFromTypeDots('quarter', 0)
    >>> dt
    DurationTuple(type='quarter', dots=0, quarterLength=1.0)
    >>> dt2 = duration.durationTupleFromTypeDots('quarter', 0)
    >>> dt is dt2
    True

    >>> dt = duration.durationTupleFromTypeDots('zero', 0)
    >>> dt
    DurationTuple(type='zero', dots=0, quarterLength=0.0)

    
    OMIT_FROM_DOCS
    
    >>> dt in duration._durationTupleCacheTypeDots.values()
    True
    '''
    tp = (durType, dots)
    try:
        return _durationTupleCacheTypeDots[tp]
    except KeyError:
        try:
            ql = typeToDuration[durType] * common.dotMultiplier(dots)
        except IndexError:
            raise DurationException("Unknown type: {0}".format(durType))
        nt = DurationTuple(durType, dots, ql)
        _durationTupleCacheTypeDots[tp] = nt
        return nt

class GraceDuration(Duration):
    '''
    A Duration that, no matter how it is created, always has a quarter length
    of zero.

    GraceDuration can be created with an implied quarter length and type; these
    values are used to configure the duration, but then may not be relevant
    after instantiation.

    >>> gd = duration.GraceDuration(type='half')
    >>> gd.quarterLength
    0.0

    >>> gd.type
    'half'

    >>> gd = duration.GraceDuration(.25)
    >>> gd.type
    '16th'

    >>> gd.quarterLength
    0.0

    >>> gd.linked
    False

    >>> gd = duration.GraceDuration(1.25)
    >>> gd.type
    'complex'

    >>> gd.quarterLength
    0.0

    >>> [(x.quarterLength, x.type) for x in gd.components]
    [(0.0, 'quarter'), (0.0, '16th')]
    '''

    # TODO: there are many properties/methods of Duration that must
    # be overridden to provide consisten behavior

    ### CLASS VARIABLES ###

    # TODO: What does "amount of time" mean here?
    _DOC_ATTR = {
        'stealTimePrevious': 'Number from 0 to 1 or None (default) for the amount of time to steal from the previous note.',         
        'stealTimeFollowing': 'Number from 0 to 1 or None (default) for the amount of time to steal from the following note.'         
        }
    

    isGrace = True

    __slots__ = (
        '_slash',
        'stealTimePrevious',
        'stealTimeFollowing',
        '_makeTime',
        )
    ### INITIALIZER ###

    def __init__(self, *arguments, **keywords):
        Duration.__init__(self, *arguments, **keywords)
        # update components to derive types; this sets ql, but this
        # will later be removed
        if self._componentsNeedUpdating:
            self._updateComponents()
        self.linked = False
        self.quarterLength = 0.0
        newComponents = []
        for c in self.components:
            newComponents.append(DurationTuple(c.type, c.dots, 0.0))
        self.components = newComponents # set new components
        
        
        self._makeTime = None
        self._slash = None
        self.slash = True # can be True, False, or None; make None go to True?
        # values are unit interval percentages
        self.stealTimePrevious = None
        self.stealTimeFollowing = None
        # make time is encoded in musicxml as divisions; here it can
        # by a duration; but should it be the duration suggested by the grace?
        self.makeTime = False

    ### PUBLIC PROPERTIES ###

    @property
    def makeTime(self):
        '''
        True, False, or None (=unknown) whether the grace note should occupy time
        in performance. Default False. Currently not used in generated playback.

        TODO: allow a duration object or number for duration.
        '''
        return self._makeTime

    @makeTime.setter
    def makeTime(self, expr):
        assert expr in (True, False, None)
        self._makeTime = bool(expr)

    @property
    def slash(self):
        '''
        True, False, or None (=unknown) whether the grace note should have a slash
        through it. Default True.
        '''

        return self._slash

    @slash.setter
    def slash(self, expr):
        assert expr in (True, False, None)
        self._slash = bool(expr)


class AppogiaturaDuration(GraceDuration):

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### INITIALIZER ###

    def __init__(self, *arguments, **keywords):
        GraceDuration.__init__(self, *arguments, **keywords)
        self.slash = False # can be True, False, or None; make None go to True?
        self.makeTime = True

# class AppogiaturaStartDuration(Duration):
#     pass
#
# class AppogiaturaStopDuration(Duration):
#     pass


class TupletFixer(object):
    '''
    The TupletFixer object takes in a flat stream and tries to fix the
    brackets and time modification values of the tuplet so that they
    reflect proper beaming, etc.  It does not alter the quarterLength
    of any notes.
    '''
    def __init__(self, streamIn = None):
        self.streamIn = streamIn
        
        self.allTupletGroups = None
        self.currentTupletNotes = None
        self.currentTupletDefinition = None
        self.totalTupletDuration = None
        self.currentTupletDuration = None

        self._resetValues()

    def setStream(self, streamIn):
        '''
        Define a stream to work on and reset all temporary variables.
        '''
        self.streamIn = streamIn
        self._resetValues()

    def _resetValues(self):
        self.allTupletGroups = []
        self.currentTupletNotes = []
        self.currentTupletDefinition = None
        self.totalTupletDuration = None
        self.currentTupletDuration = None

    def findTupletGroups(self, incorporateGroupings = False):
        '''
        Finds all tuplets in the stream and puts them into groups.

        If incorporateGroupings is True, then a tuplet.type="stop"
        ends a tuplet group even if the next note is a tuplet.


        This demonstration has three groups of tuplets, two sets of 8th note tuplets and one of 16ths:


        >>> c = converter.parse('tinynotation: 4/4 trip{c8 d e} f4 trip{c#8 d# e#} g8 trip{c-16 d- e-}', makeNotation=False)
        >>> tf = duration.TupletFixer(c) # no need to flatten this stream
        >>> tupletGroups = tf.findTupletGroups()
        >>> tupletGroups
        [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>],
         [<music21.note.Note C#>, <music21.note.Note D#>, <music21.note.Note E#>],
         [<music21.note.Note C->, <music21.note.Note D->, <music21.note.Note E->]]

        These groups are stored in TupletFixer.allTupletGroups:

        >>> tupletGroups is tf.allTupletGroups
        True


        Demonstration with incorporateGroupings:


        >>> s = stream.Stream()
        >>> for i in range(9):
        ...    n = note.Note()
        ...    n.ps = 60 + i
        ...    n.duration.quarterLength = 1.0/3
        ...    if i % 3 == 2:
        ...        n.duration.tuplets[0].type = 'stop'
        ...    s.append(n)
        >>> tf = duration.TupletFixer(s)
        >>> tupletGroups = tf.findTupletGroups(incorporateGroupings = True)
        >>> tupletGroups
        [[<music21.note.Note C>, <music21.note.Note C#>, <music21.note.Note D>],
         [<music21.note.Note E->, <music21.note.Note E>, <music21.note.Note F>],
         [<music21.note.Note F#>, <music21.note.Note G>, <music21.note.Note G#>]]

        Without incorporateGroupings we just get one big set of tuplets

        >>> tupletGroups = tf.findTupletGroups()
        >>> len(tupletGroups)
        1
        >>> len(tupletGroups[0])
        9
        '''
        self.allTupletGroups = []
        currentTupletGroup = []
        tupletActive = False
        for n in self.streamIn.notesAndRests:
            if len(n.duration.tuplets) == 0: # most common case first
                if tupletActive is True:
                    self.allTupletGroups.append(currentTupletGroup)
                    currentTupletGroup = []
                    tupletActive = False
                continue
            else:
                if tupletActive is False:
                    tupletActive = True
                currentTupletGroup.append(n)
                if incorporateGroupings and n.duration.tuplets[0].type == 'stop':
                    self.allTupletGroups.append(currentTupletGroup)
                    currentTupletGroup = []
                    tupletActive = False
        if tupletActive:
            self.allTupletGroups.append(currentTupletGroup)

        return self.allTupletGroups

    def fixBrokenTupletDuration(self, tupletGroup):
        r'''
        tries to fix cases like triplet quarter followed by triplet
        eighth to be a coherent tuplet.

        requires a tuplet group from findTupletGroups() or TupletFixer.allTupletGroups

        >>> s = stream.Stream()

        >>> n1 = note.Note('C')
        >>> n1.duration.quarterLength = 2.0/3
        >>> n1.duration.quarterLength
        Fraction(2, 3)
        >>> s.append(n1)
        >>> n2 = note.Note('D')
        >>> n2.duration.quarterLength = 1.0/3
        >>> n2.duration.quarterLength
        Fraction(1, 3)
        >>> s.append(n2)

        >>> n1.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/quarter>
        >>> n2.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/eighth>

        >>> tf = duration.TupletFixer(s) # no need to flatten this stream
        >>> tupletGroups = tf.findTupletGroups()
        >>> tupletGroups
        [[<music21.note.Note C>, <music21.note.Note D>]]
        >>> tf.fixBrokenTupletDuration(tupletGroups[0])

        >>> n1.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/eighth>
        >>> n1.duration.quarterLength
        Fraction(2, 3)
        >>> n2.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/eighth>

        More complex example, from a piece by Josquin:

        >>> humdr = "**kern *M3/1 3.c 6d 3e 3f 3d 3%2g 3e 3f#"
        >>> humdrLines = '\n'.join(humdr.split())
        >>> humdrum.spineParser.flavors['JRP'] = True
        >>> s = converter.parse(humdrLines, format='humdrum')

        >>> m1 = s.parts[0].measure(1)
        >>> tf = duration.TupletFixer(m1)
        >>> tupletGroups = tf.findTupletGroups(incorporateGroupings=True)
        >>> tf.fixBrokenTupletDuration(tupletGroups[-1])
        >>> m1[-1].duration.tuplets[0]
        <music21.duration.Tuplet 3/2/whole>
        >>> m1[-1].duration.quarterLength
        Fraction(4, 3)
        '''
        if len(tupletGroup) == 0:
            return
        firstTup = tupletGroup[0].duration.tuplets[0]
        totalTupletDuration = opFrac(firstTup.totalTupletLength())
        currentTupletDuration = 0.0
        smallestTupletTypeOrdinal = None
        largestTupletTypeOrdinal = None

        for n in tupletGroup:
            currentTupletDuration = opFrac(currentTupletDuration + n.duration.quarterLength)
            thisTup = n.duration.tuplets[0]
            thisTupType = thisTup.durationActual.type
            thisTupTypeOrdinal = ordinalTypeFromNum.index(thisTupType)

            if smallestTupletTypeOrdinal is None:
                smallestTupletTypeOrdinal = thisTupTypeOrdinal
            elif thisTupTypeOrdinal > smallestTupletTypeOrdinal:
                smallestTupletTypeOrdinal = thisTupTypeOrdinal

            if largestTupletTypeOrdinal is None:
                largestTupletTypeOrdinal = thisTupTypeOrdinal
            elif thisTupTypeOrdinal < largestTupletTypeOrdinal:
                largestTupletTypeOrdinal = thisTupTypeOrdinal


        if currentTupletDuration == totalTupletDuration:
            return
        else:
            excessRatio = opFrac(currentTupletDuration / totalTupletDuration)
            inverseExcessRatio = opFrac(1.0/excessRatio)

            if excessRatio == int(excessRatio): # divide tuplets into smaller
                largestTupletType = ordinalTypeFromNum[largestTupletTypeOrdinal]

                #print largestTupletTypeOrdinal, largestTupletType
                for n in tupletGroup:
                    n.duration.tuplets[0].durationNormal = durationTupleFromTypeDots(
                                    largestTupletType, n.duration.tuplets[0].durationNormal.dots)
                    n.duration.tuplets[0].durationActual = durationTupleFromTypeDots(
                                    largestTupletType, n.duration.tuplets[0].durationActual.dots)
                 

            elif inverseExcessRatio == int(inverseExcessRatio): # redefine tuplets by GCD
                smallestTupletType = ordinalTypeFromNum[smallestTupletTypeOrdinal]
                for n in tupletGroup:
                    # TODO: this should be frozen!
                    durt = durationTupleFromTypeDots(smallestTupletType, n.duration.tuplets[0].durationNormal.dots)
                    n.duration.tuplets[0].durationNormal = durt
                    durt = durationTupleFromTypeDots(smallestTupletType, n.duration.tuplets[0].durationActual.dots)
                    n.duration.tuplets[0].durationActual = durt
            else:
                pass
                # print "Crazy!", currentTupletDuration, totalTupletDuration, excess



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass


    def testSingle(self):
        from music21 import note
        a = Duration()
        a.quarterLength = 2.66666
        n = note.Note()
        n.duration = a
        n.show()

    def testBasic(self):
        import random
        from music21 import stream
        from music21 import note

        a = stream.Stream()

        for i in range(30):
            ql = random.choice([1, 2, 3, 4, 5]) + random.choice([0, .25, .5, .75])
            # w/ random.choice([0,.33333,.666666] gets an error
            n = note.Note()
            b = Duration()
            b.quarterLength = ql
            n.duration = b
            a.append(n)

        a.show()




class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)


    def testTuple(self):
#         note1 = Note()
#         note1.duration.type = "quarter"

        # create a tuplet with 5 dotted eighths in the place of 3 double-dotted
        #eighths
        dur1 = Duration()
        dur1.type = "eighth"
        dur1.dots = 1

        dur2 = Duration()
        dur2.type = "eighth"
        dur2.dots = 2

        tup1 = Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur2]

        #print "For 5 dotted eighths in the place of 3 double-dotted eighths"
        #print "Total tuplet length is",
        self.assertEqual(tup1.totalTupletLength(), 2.625)
        #print tup1.totalTupletLength(), # 2.625
        #print "quarter notes.\nEach note is",
        #print "times as long as it would normally be."

        ### create a new dotted quarter and apply the tuplet to it
        dur3 = Duration()
        dur3.type = "quarter"
        dur3.dots = 1
        dur3.tuplets = (tup1,)
        #print "So a tuplet-dotted-quarter's length is",
        self.assertEqual(dur3.quarterLength, fractions.Fraction(21, 20))

        # print "quarter notes"

        # create a tuplet with 3 sixteenths in the place of 2 sixteenths
        tup2 = Tuplet()
        dur4 = Duration()
        dur4.type = "16th"
        tup2.tupletActual = [3, dur4]
        tup2.tupletNormal = [2, dur4]

#         print "\nTup2:\nTotal tuplet length is",
#         print tup2.totalTupletLength(),
#         print "quarter notes.\nEach note is",
#         print tup2.tupletMultiplier(),
#         print "times as long as it would normally be."

        self.assertEqual(tup2.totalTupletLength(), 0.5)
        self.assertEqual(tup2.tupletMultiplier(), fractions.Fraction(2,3))

        dur3.tuplets = (tup1, tup2)
#         print "So a tuplet-dotted-quarter's length under both tuplets is",
#         print dur3.getQuarterLength(),
#         print "quarter notes"

        self.assertEqual(dur3.quarterLength, opFrac(7/10.0))

        myTuplet = Tuplet()
        self.assertEqual(myTuplet.tupletMultiplier(), opFrac(2/3.0))
        myTuplet.tupletActual = [5, durationTupleFromTypeDots('eighth',0)]
        self.assertEqual(myTuplet.tupletMultiplier(), opFrac(2/5.0))


    def testTupletTypeComplete(self):
        '''
        Test setting of tuplet type when durations sum to expected completion
        '''
        # default tuplets group into threes when possible
        from music21 import stream
        test, match = ([.333333] * 3 + [.1666666] * 6,
            ['start', None, 'stop', 'start', None, 'stop', 'start', None, 'stop'])
        inputTuplets = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            inputTuplets.append(d)
            
        stream.makeNotation.makeTupletBrackets(inputTuplets, inPlace=True)  
        output = []
        for d in inputTuplets:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)


        tup6 = Duration()
        tup6.quarterLength = .16666666
        tup6.tuplets[0].numberNotesActual = 6
        tup6.tuplets[0].numberNotesNormal = 4

        tup5 = Duration()
        tup5.quarterLength = .2 # default is 5 in the space of 4 16th

        inputTuplets = [copy.deepcopy(tup6), copy.deepcopy(tup6), copy.deepcopy(tup6),
        copy.deepcopy(tup6), copy.deepcopy(tup6), copy.deepcopy(tup6),
        copy.deepcopy(tup5), copy.deepcopy(tup5), copy.deepcopy(tup5),
        copy.deepcopy(tup5), copy.deepcopy(tup5)]

        match = ['start', None, None, None, None, 'stop',
                 'start', None, None, None, 'stop']

        stream.makeNotation.makeTupletBrackets(inputTuplets, inPlace=True)  
        output = []
        for d in inputTuplets:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)



    def testTupletTypeIncomplete(self):
        '''
        Test setting of tuplet type when durations do not sum to expected
        completion.
        '''
        from music21 import stream
        # the current match results here are a good compromise
        # for a difficult situation.
        test, match = ([.333333] * 2 + [.1666666] * 5,
            ['start', None, None, 'stop', 'start', None, 'stop']
            )
        inputDurations = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            inputDurations.append(d)
        stream.makeNotation.makeTupletBrackets(inputDurations, inPlace=True)
        output = []
        for d in inputDurations:
            output.append(d.tuplets[0].type)
        #environLocal.printDebug(['got', output])
        self.assertEqual(output, match)


    def testAugmentOrDiminish(self):

        # test halfs and doubles

        for ql, half, double in [(2,1,4), (.5,.25,1), (1.5, .75, 3),
                                 (2/3., 1/3., 4/3.)]:

            d = Duration()
            d.quarterLength = ql
            a = d.augmentOrDiminish(.5)
            self.assertEqual(a.quarterLength, opFrac(half), 5)

            b = d.augmentOrDiminish(2)
            self.assertEqual(b.quarterLength, opFrac(double), 5)


        # testing tuplets in duration units

        a = Duration()
        a.quarterLength = 1/3.0
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.))
        self.assertEqual(repr(a.tuplets[0].durationNormal), "DurationTuple(type='eighth', dots=0, quarterLength=0.5)")

        b = a.augmentOrDiminish(2)
        self.assertEqual(b.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(b.tuplets[0].durationNormal), "DurationTuple(type='quarter', dots=0, quarterLength=1.0)")

        c = b.augmentOrDiminish(.25)
        self.assertEqual(c.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(c.tuplets[0].durationNormal), "DurationTuple(type='16th', dots=0, quarterLength=0.25)")


        # testing tuplets on Durations
        a = Duration()
        a.quarterLength = 1/3.0
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), "DurationTuple(type='eighth', dots=0, quarterLength=0.5)")

        b = a.augmentOrDiminish(2)
        self.assertEqual(b.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(b.tuplets[0].durationNormal), "DurationTuple(type='quarter', dots=0, quarterLength=1.0)")

        c = b.augmentOrDiminish(.25)
        self.assertEqual(c.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(c.tuplets[0].durationNormal), "DurationTuple(type='16th', dots=0, quarterLength=0.25)")


    def testUnlinkedTypeA(self):
        from music21 import duration

        du = duration.Duration()
        du.linked = False
        du.quarterLength = 5.0
        du.type = 'quarter'
        self.assertEqual(du.quarterLength, 5.0)
        self.assertEqual(du.type, 'quarter')
        #print du.type, du.quarterLength

        d = duration.Duration()
        self.assertEqual(d.linked, True) # note set
        d.linked = False
        d.type = 'quarter'

        self.assertEqual(d.type, 'quarter')
        self.assertEqual(d.quarterLength, 0.0) # note set
        self.assertEqual(d.linked, False) # note set

        d.quarterLength = 20
        self.assertEqual(d.quarterLength, 20.0)
        self.assertEqual(d.linked, False) # note set
        self.assertEqual(d.type, 'quarter')

        # can set type  and will remain unlinked
        d.type = '16th'
        self.assertEqual(d.type, '16th')
        self.assertEqual(d.quarterLength, 20.0)
        self.assertEqual(d.linked, False) # note set

        # can set quarter length and will remain unlinked
        d.quarterLength = 0.0
        self.assertEqual(d.type, '16th')
        self.assertEqual(d.linked, False) # note set


#         d = duration.Duration()
#         d.setTypeUnlinked('quarter')
#         self.assertEqual(d.type, 'quarter')
#         self.assertEqual(d.quarterLength, 0.0) # note set
#         self.assertEqual(d.linked, False) # note set
#
#         d.setQuarterLengthUnlinked(20)
#         self.assertEqual(d.quarterLength, 20.0)
#         self.assertEqual(d.linked, False) # note set

    def xtestStrangeMeasure(self):
        from music21 import corpus
        j1 = corpus.parse('trecento/PMFC_06-Jacopo-03a')
        x = j1.parts[0].getElementsByClass('Measure')[42]
        x._cache = {}
        print(x.duration)
        print(x.duration.components)

    def testSimpleSetQuarterLength(self):
        d = Duration()
        d.quarterLength = 1/3.0
        self.assertEqual(repr(d.quarterLength), 'Fraction(1, 3)')
        self.assertEqual(d._components, [] )
        self.assertEqual(d._componentsNeedUpdating, True )
        self.assertEqual(str(d.components), 
                         "(DurationTuple(type='eighth', dots=0, quarterLength=0.5),)")
        self.assertEqual(d._componentsNeedUpdating, False)
        self.assertTrue(d._quarterLengthNeedsUpdating)
        self.assertEqual(repr(d.quarterLength), 'Fraction(1, 3)')
        self.assertEqual(str(unitSpec(d)), "(Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')")

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Duration, Tuplet, convertQuarterLengthToType, TupletFixer]

if __name__ == "__main__":
    import music21
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof


