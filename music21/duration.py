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

::

    >>> d = duration.Duration()
    >>> d.quarterLength = 0.5
    >>> d.type
    'eighth'

::

    >>> d.type = 'whole'
    >>> d.quarterLength
    4.0

::

    >>> d.quarterLength = 0.166666666
    >>> d.type
    '16th'

::

    >>> d.tuplets[0].numberNotesActual
    3

::

    >>> d.tuplets[0].numberNotesNormal
    2

'''
from __future__ import print_function

import fractions
import unittest
import copy

from music21 import common
from music21 import defaults
from music21 import exceptions21
from music21.common import SlottedObject, opFrac
from music21 import environment

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

defaultTupletNumerators = [3, 5, 7, 11, 13]


def unitSpec(durationObjectOrObjects):
    '''
    A simple data representation of most Duration objects. Processes a single
    Duration or a List of Durations, returning a single or list of unitSpecs.

    A unitSpec is a tuple of qLen, durType, dots, tupleNumerator,
    tupletDenominator, and tupletType (assuming top and bottom tuplets are the
    same).

    This function does not deal with nested tuplets, etc.

    ::

        >>> aDur = duration.Duration()
        >>> aDur.quarterLength = 3
        >>> duration.unitSpec(aDur)
        (3.0, 'half', 1, None, None, None)

        >>> bDur = duration.Duration()
        >>> bDur.quarterLength = 1.125
        >>> duration.unitSpec(bDur)
        (1.125, 'complex', None, None, None, None)

        >>> cDur = duration.Duration()
        >>> cDur.quarterLength = 0.3333333
        >>> duration.unitSpec(cDur)
        (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')

        >>> duration.unitSpec([aDur, bDur, cDur])
        [(3.0, 'half', 1, None, None, None), (1.125, 'complex', None, None, None, None), (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')]
    '''
    if common.isListLike(durationObjectOrObjects):
        ret = []
        for dO in durationObjectOrObjects:
            if dO.tuplets is None or len(dO.tuplets) == 0:
                ret.append((dO.quarterLength, dO.type, dO.dots, None, None, None))
            else:
                ret.append((dO.quarterLength, dO.type, dO.dots, dO.tuplets[0].numberNotesActual, dO.tuplets[0].numberNotesNormal, dO.tuplets[0].durationNormal.type))
        return ret
    else:
        dO = durationObjectOrObjects
        if dO.tuplets is None or len(dO.tuplets) == 0:
            return (dO.quarterLength, dO.type, dO.dots, None, None, None)
        else:
            return (dO.quarterLength, dO.type, dO.dots, dO.tuplets[0].numberNotesActual, dO.tuplets[0].numberNotesNormal, dO.tuplets[0].durationNormal.type)

def nextLargerType(durType):
    '''
    Given a type (such as 16th or quarter), return the next larger type.

    ::

        >>> duration.nextLargerType("16th")
        'eighth'
        >>> duration.nextLargerType("whole")
        'breve'
        >>> duration.nextLargerType("duplex-maxima")
        'unexpressible'
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException("cannot get the next larger of %s" % durType)
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 0: # TODO: should this raise an exception?
        return 'unexpressible'
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
    'unexpressible'
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException("cannot get the next smaller of %s" % durType)
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 15: # TODO: should this raise an exception?
        return 'unexpressible'
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
    >>> duration.quarterLengthToClosestType(2.0000000000000001)
    ('half', True)
    '''
    if (isinstance(qLen, fractions.Fraction)):
        noteLengthType = 4 / qLen  # divides right...
    else:
        noteLengthType = opFrac(4.0/qLen)

    if noteLengthType in typeFromNumDict:
        return (typeFromNumDict[noteLengthType], True)
    else:
        lowerBound = 4.0 / qLen
        upperBound = 8.0 / qLen
        for numDict in sorted(list(typeFromNumDict.keys())):
            if numDict == 0:
                continue
            elif lowerBound < numDict and upperBound > numDict:
                return (typeFromNumDict[numDict], False)
        # CUTHBERT ATTEMPT AT FIX Feb 2011
        if qLen < 5e-5:
            return (None, False)
        raise DurationException("Cannot return types greater than double duplex-maxima, your length was %s : remove this when we are sure this works..." % qLen)



def convertQuarterLengthToType(qLen):
    '''Return a type if there exists a type that is exactly equal to the duration of the provided quarterLength. Similar to quarterLengthToClosestType() but this function only returns exact matches.


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
    '''Given a quarterLength, determine if there is a dotted
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


def quarterLengthToTuplet(qLen, maxToReturn=4):
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
        for i in defaultTupletNumerators:
            qLenBase = opFrac(typeValue / float(i))
            # try multiples of the tuplet division, from 1 to max-1
            for m in range(1, i):
                qLenCandidate = qLenBase * m
                # need to use a courser grain here
                if qLenCandidate == qLen:
                    tupletDuration = Duration(typeKey)
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

def quarterLengthToDurations(qLen, link=True):
    '''
    Returns a List of new Duration Units given a quarter length.

    For many simple quarterLengths, the list will have only a
    single element.  However, for more complex durations, the list
    could contain several durations (presumably to be tied to each other).

    (All quarterLengths can, technically, be notated as a single unit
    given a complex enough tuplet, but we don't like doing that).

    This is mainly a utility function. Much faster for many purposes
    is something like::

       d = duration.Duration()
       d.quarterLength = 251.231312

    and then let Duration automatically create Duration Components as necessary.

    These examples use unitSpec() to get a concise summary of the contents


    >>> duration.unitSpec(duration.quarterLengthToDurations(2))
    [(2.0, 'half', 0, None, None, None)]

    Dots are supported

    >>> duration.unitSpec(duration.quarterLengthToDurations(3))
    [(3.0, 'half', 1, None, None, None)]
    >>> duration.unitSpec(duration.quarterLengthToDurations(6.0))
    [(6.0, 'whole', 1, None, None, None)]

    Double and triple dotted half note.

    >>> duration.unitSpec(duration.quarterLengthToDurations(3.5))
    [(3.5, 'half', 2, None, None, None)]
    >>> duration.unitSpec(duration.quarterLengthToDurations(3.75))
    [(3.75, 'half', 3, None, None, None)]

    A triplet quarter note, lasting .6666 qLen
    Or, a quarter that is 1/3 of a half.
    Or, a quarter that is 2/3 of a quarter.

    >>> duration.unitSpec(duration.quarterLengthToDurations(2.0/3.0))
    [(Fraction(2, 3), 'quarter', 0, 3, 2, 'quarter')]

    A triplet eighth note, where 3 eights are in the place of 2.
    Or, an eighth that is 1/3 of a quarter
    Or, an eighth that is 2/3 of eighth

    >>> post = duration.unitSpec(duration.quarterLengthToDurations(1.0/3))
    >>> post[0]
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')

    A half that is 1/3 of a whole, or a triplet half note.
    Or, a half that is 2/3 of a half

    >>> duration.unitSpec(duration.quarterLengthToDurations(4.0/3.0))
    [(Fraction(4, 3), 'half', 0, 3, 2, 'half')]

    A sixteenth that is 1/5 of a quarter
    Or, a sixteenth that is 4/5ths of a 16th

    >>> duration.unitSpec(duration.quarterLengthToDurations(1.0/5.0))
    [(Fraction(1, 5), '16th', 0, 5, 4, '16th')]

    A 16th that is  1/7th of a quarter
    Or, a 16th that is 4/7 of a 16th

    >>> duration.unitSpec(duration.quarterLengthToDurations(1.0/7.0))
    [(Fraction(1, 7), '16th', 0, 7, 4, '16th')]

    A 4/7ths of a whole note, or
    A quarter that is 4/7th of of a quarter

    >>> duration.unitSpec(duration.quarterLengthToDurations(4.0/7.0))
    [(Fraction(4, 7), 'quarter', 0, 7, 4, 'quarter')]

    If a duration is not containable in a single unit, this method
    will break off the largest type that fits within this type
    and recurse, adding as my units as necessary.

    >>> duration.unitSpec(duration.quarterLengthToDurations(2.5))
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)]

    >>> duration.unitSpec(duration.quarterLengthToDurations(2.3333333))
    [(2.0, 'half', 0, None, None, None), (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')]


    >>> duration.unitSpec(duration.quarterLengthToDurations(1.0/6.0))
    [(Fraction(1, 6), '16th', 0, 3, 2, '16th')]
    
    This example doesn't fit exactly with an idea of a tuplet, so this method (perhaps incorrectly)
    tries to approximate it with power of two notes (TODO: balance tuplet complexity with number of
    duration units)
    
    >>> duration.quarterLengthToDurations(.18333333333333)
    [<music21.duration.DurationUnit 0.125>, <music21.duration.DurationUnit 0.03125>, <music21.duration.DurationUnit 0.015625>, <music21.duration.DurationUnit 0.0078125>]

    >>> duration.quarterLengthToDurations(0.0)
    [<music21.duration.ZeroDuration>]

    '''
    post = []
    qLen = opFrac(qLen)

    if qLen < 0:
        raise DurationException("qLen cannot be less than Zero.  Read Lewin, GMIT for more details...")

    ## CUTHBERT: TRIED INCREASING 0.0 to < 0.005 but did not help...
    elif qLen == 0:
        post.append(ZeroDuration()) # this is a DurationUnit subclass
        return post

    # try match to type, get next lowest
    typeFound, match = quarterLengthToClosestType(qLen)
    if match:
        post.append(DurationUnit(typeFound))
    else:
        if typeFound is None :
            raise DurationException('cannot find duration types near quarter length %s' % qLen)

    # try dots
    # using typeFound here is the largest type that is not greater than qLen
    if not match:
        dots, durType = dottedMatch(qLen)
        if durType is not False:
            dNew = DurationUnit(durType)
            dNew.dots = dots
            post.append(dNew)
            match = True

    typeNext = nextLargerType(typeFound)
    # try tuplets
    # using typeNext is the next type that is larger than then the qLen
    if not match:
        # just get the first candidate
        tupleCandidates = quarterLengthToTuplet(qLen, 1)
        if len(tupleCandidates) > 0:
            # assume that the first, using the smallest type, is best
            dNew = DurationUnit(typeNext)
            dNew.tuplets = (tupleCandidates[0],)
            post.append(dNew)
            match = True

    # if we do not have a match, remove the largest type not greater
    # and recursively apply
    if not match:
        post.append(DurationUnit(typeFound))
        qLenRemainder = qLen - typeToDuration[typeFound]
        if qLenRemainder < 0:
            raise DurationException('cannot reduce quarter length (%s)' % qLenRemainder)
        # trying a fixed minimum limit
        # this it do deal with common errors in processing
        if qLenRemainder > .004: # 1e-4 grain almostEquals -- TODO: FIX
            try:
                if len(post) > 6: # we probably have a problem
                    raise DurationException('duration exceeds 6 components, with %s qLen left' % (qLenRemainder))
                else:
                    post += quarterLengthToDurations(qLenRemainder)
            except RuntimeError: # if recursion exceeded
                msg = 'failed to find duration for qLen %s, qLenRemainder %s, post %s' % (qLen, qLenRemainder, post)
                raise DurationException(msg)
    if not link: # make unlink all
        for du in post:
            du.unlink()
    return post


def partitionQuarterLength(qLen, qLenDiv=4):
    '''
    Given a `qLen` (quarterLength) and a `qLenDiv`, that is, a base quarterLength to divide the `qLen` into
    (default = 4; i.e., into whole notes), returns a list of Durations that
    partition the given quarterLength so that there is no leftovers.

    This is a useful tool for partitioning a duration by Measures (i.e., take a long Duration and
    make it fit within several measures) or by beat groups.

    Here is a Little demonstration function that will show how we can use partitionQuarterLength:

    >>> def pql(qLen, qLenDiv):
    ...    partitionList = duration.partitionQuarterLength(qLen, qLenDiv)
    ...    for dur in partitionList:
    ...        print(duration.unitSpec(dur))


    Divide 2.5 quarters worth of time into eighth notes.
    >>> pql(2.5,.5)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)


    Divide 5 qLen into 2.5 qLen bundles (i.e., 5/8 time)
    >>> pql(5, 2.5)
    (2.0, 'half', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)
    (2.0, 'half', 0, None, None, None)
    (0.5, 'eighth', 0, None, None, None)


    Divide 5.25 qLen into dotted halves
    >>> pql(5.25,3)
    (3.0, 'half', 1, None, None, None)
    (2.0, 'half', 0, None, None, None)
    (0.25, '16th', 0, None, None, None)


    Divide 1.33333 qLen into triplet eighths:
    >>> pql(4.0/3.0, 1.0/3.0)
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')

    Divide 1.5 into triplet eighths, with a triplet 16th leftover.
    >>> pql(1.5, 1.0/3)
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')
    (Fraction(1, 6), '16th', 0, 3, 2, '16th')

    There is no problem if the division unit is larger then the source duration, it
    just will not be totally filled.
    >>> pql(1.5, 4)
    (1.5, 'quarter', 1, None, None, None)
    '''
    qLen = opFrac(qLen)
    qLenDiv = opFrac(qLenDiv)
    post = []

    while qLen >= qLenDiv:
        post += quarterLengthToDurations(qLenDiv)
        qLen = qLen - qLenDiv
        
    if qLen == 0:
        return post
    else:
        # leftovers...
        post += quarterLengthToDurations(qLen)
        return post


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

    if tuplets is not None and len(tuplets) > 0:
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


def updateTupletType(durationList):
    '''
    N.B. -- DEPRECATED -- call stream.makeNotation.makeTupletBrackets
    
    Given a list of Durations or DurationUnits,
    examine each Duration, and each component, and set Tuplet type to
    start or stop, as necessary.

    >>> a = duration.Duration(); a.quarterLength = 1.0/3
    >>> b = duration.Duration(); b.quarterLength = 1.0/3
    >>> c = duration.DurationUnit(); c.quarterLength = 1.0/3
    >>> d = duration.Duration(); d.quarterLength = 2
    >>> e = duration.Duration(); e.quarterLength = 1.0/3
    >>> f = duration.DurationUnit(); f.quarterLength = 1.0/3
    >>> g = duration.Duration(); g.quarterLength = 1.0/3

    >>> a.tuplets[0].type is None
    True
    >>> duration.updateTupletType([a, b, c, d, e, f, g])
    >>> a.tuplets[0].type == 'start'
    True
    >>> b.tuplets[0].type is None
    True
    >>> c.tuplets[0].type == 'stop'
    True
    >>> d.tuplets
    ()
    >>> e.tuplets[0].type == 'start'
    True
    >>> f.tuplets[0].type is None
    True
    >>> g.tuplets[0].type == 'stop'
    True

    A single duration with tuplet (automatically forces into a List):
    
    >>> dur = duration.Duration(1.0/3)
    >>> duration.updateTupletType([dur] )
    >>> dur.tuplets[0].type
    'startStop'     
    '''
    if isinstance(durationList, Duration): # if a Duration object alone
        durationList = [durationList] # put in list
    
    from music21 import stream
    stream.makeNotation.makeTupletBrackets(durationList, inPlace = True)


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

    ::

        >>> myTup = duration.Tuplet(numberNotesActual = 5, numberNotesNormal = 4)
        >>> print(myTup.tupletMultiplier())
        4/5


    In this case, the tupletMultiplier is a float because it can be expressed
    as a binary number:

    ::

        >>> myTup2 = duration.Tuplet(8, 5)
        >>> tm = myTup2.tupletMultiplier()
        >>> tm
        0.625

    ::

        >>> myTup2 = duration.Tuplet(6, 4, "16th")
        >>> print(myTup2.durationActual.type)
        16th

    ::

        >>> print(myTup2.tupletMultiplier())
        2/3

    Tuplets may be frozen, in which case they become immutable. Tuplets
    which are attached to Durations are automatically frozen.  Otherwise
    a tuplet could change without the attached duration knowing about it,
    which would be a real problem.

    ::

        >>> myTup.frozen = True
        >>> myTup.tupletActual = [3, 2]
        Traceback (most recent call last):
        ...
        TupletException: A frozen tuplet (or one attached to a duration) is immutable

    ::

        >>> myHalf = duration.Duration("half")
        >>> myHalf.appendTuplet(myTup2)
        >>> myTup2.tupletActual = [5, 4]
        Traceback (most recent call last):
        ...
        TupletException: A frozen tuplet (or one attached to a duration) is immutable

    Note that if you want to create a note with a simple Tuplet attached to it,
    you can just change the quarterLength of the note:

    ::

        >>> myNote = note.Note("C#4")
        >>> myNote.duration.quarterLength = 0.8
        >>> myNote.duration.quarterLength
        Fraction(4, 5)
        >>> myNote.duration.fullName
        'Quarter Quintuplet (4/5 QL)'

    ::

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

        # this previously stored a Duration, not a DurationUnit
        if 'durationActual' in keywords and keywords['durationActual'] != None:
            if isinstance(keywords['durationActual'], basestring):
                self.durationActual = DurationUnit(keywords['durationActual'])
            else:
                self.durationActual = keywords['durationActual']
        else:
            self.durationActual = DurationUnit("eighth")

        # normal is the space that would normally be occupied by the tuplet span
        if 'numberNotesNormal' in keywords:
            self.numberNotesNormal = keywords['numberNotesNormal']
        else:
            self.numberNotesNormal = 2

        # this previously stored a Duration, not a DurationUnit
        if 'durationNormal' in keywords and keywords['durationNormal'] != None:
            if isinstance(keywords['durationNormal'], basestring):
                self.durationNormal = DurationUnit(keywords['durationNormal'])
            else:
                self.durationNormal = keywords['durationNormal']
        else:
            self.durationNormal = DurationUnit("eighth")

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

    def augmentOrDiminish(self, amountToScale, inPlace=True):
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
        <music21.duration.DurationUnit 0.5>
        >>> a.augmentOrDiminish(.5)
        >>> a.durationActual
        <music21.duration.DurationUnit 0.25>
        >>> a.tupletMultiplier()
        Fraction(1, 3)
        '''
        if not amountToScale > 0:
            raise DurationException('amountToScale must be greater than zero')
        # TODO: scale the triplet in the same manner as Durations

        if inPlace:
            post = self
            self.frozen = False # have to unfreeze
        else:
            post = copy.deepcopy(self)

        # duration units scale
        post.durationActual.augmentOrDiminish(amountToScale, inPlace=True)
        post.durationNormal.augmentOrDiminish(amountToScale, inPlace=True)

        # ratios stay the same
        #self.numberNotesActual = actual
        #self.numberNotesNormal = normal

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
        # these used to be Duration; now using DurationUnits
        if self.frozen is True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        if common.isNum(durType):
            durType = convertQuarterLengthToType(durType)

        self.durationActual = DurationUnit(durType)
        self.durationNormal = DurationUnit(durType)

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
        >>> a.durationActual = duration.DurationUnit('quarter')
        >>> a.durationNormal = duration.DurationUnit('half')
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
        >>> a.durationActual = duration.Duration('half')
        >>> a.numberNotesNormal = 2
        >>> a.durationNormal = duration.Duration('half')
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
    def tupletActual(self, tupList=(3,2)):
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
    def tupletNormal(self, tupList=(3,2)):
        if self.frozen is True:
            raise TupletException("A frozen tuplet (or one attached to a duration) is immutable")
        self.numberNotesNormal, self.durationNormal = tupList


#-------------------------------------------------------------------------------


class DurationCommon(SlottedObject):
    '''
    A base class for both Duration and DurationUnit objects.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_componentsNeedUpdating',
        '_quarterLengthNeedsUpdating',
        '_typeNeedsUpdating',
        )

    ### INITIALIZER ###

    def __init__(self):
        self._componentsNeedUpdating = False
        self._quarterLengthNeedsUpdating = False
        self._typeNeedsUpdating = False

    ### SPECIAL METHODS ###

#    def __getstate__(self):
#        state = {}
#        slots = set()
#        for cls in self.__class__.mro():
#            slots.update(getattr(cls, '__slots__', ()))
#        for slot in slots:
#            state[slot] = getattr(self, slot, None)
#        return state
#
#    def __setstate__(self, state):
#        for slot, value in state.items():
#            setattr(self, slot, value)

    ### PUBLIC METHODS ###

    def aggregateTupletMultiplier(self):
        '''
        Returns the multiple of all the tuplet multipliers as an opFrac.

        This method is needed for MusicXML time-modification among other
        places.


        No tuplets...

        ::

            >>> complexDur = duration.Duration('eighth')
            >>> complexDur.aggregateTupletMultiplier()
            1.0
            
        With tuplets:
        
        ::
            
            >>> complexDur.appendTuplet(duration.Tuplet())
            >>> complexDur.aggregateTupletMultiplier()
            Fraction(2, 3)

        Nested tuplets are possible...

        ::

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
        return [x.__name__ for x in self.__class__.mro()]


#------------------------------------------------------------------------------


class DurationUnit(DurationCommon):
    '''
    A DurationUnit is a duration notation that (generally) can be notated with
    a single notation unit, such as one note head, without a tie.

    DurationUnits are not usually instantiated by users of music21, but are
    used within Duration objects to model the containment of numerous summed
    components.

    Like Durations, DurationUnits have the option of unlinking the
    quarterLength and its representation on the page. For instance, in 12/16,
    Brahms sometimes used a dotted half note to indicate the length of 11/16th
    of a note. (see Don Byrd's Extreme Notation webpage for more information).
    Since this duration can be expressed by a single graphical unit in Brahms's
    shorthand, it can be modeled by a single DurationUnit of unliked
    graphical/temporal representation.

    Additional types are needed beyond those in Duration::

        * 'zero' type for zero-length durations
        * 'unexpressible' type for anything that cannot
          be expressed as a single notation unit, and thus
          needs a full Duration object (such as 2.5 quarterLengths.)

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_dots',
        '_link',
        '_qtrLength',
        '_tuplets',
        '_type',
        )

    ### INITIALIZER ###

    def __init__(self, prototype='quarter'):
        DurationCommon.__init__(self)
        self._link = True  # default is True
        self._type = ""
        # dots can be a float for expressing Crumb dots (1/2 dots)
        # dots is a tuple for rarely used: dotted-dotted notes;
        #  e.g. dotted-dotted half in 9/8 expressed as 1,1
        self._dots = (0,)
        self._tuplets = ()  # an empty tuple
        if common.isNum(prototype):
            self._qtrLength = opFrac(prototype)
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = False
        else:
            if prototype not in typeToDuration:
                raise DurationException('type (%s) is not valid' % type)
            self.type = prototype
            self._qtrLength = 0.0
            self._typeNeedsUpdating = False
            self._quarterLengthNeedsUpdating = True

    ### SPECIAL METHODS ###

    def __eq__(self, other):
        '''
        Test equality. Note: this may not work with Tuplets until we
        define equality tests for tuplets.

        ::

            >>> aDur = duration.DurationUnit('quarter')
            >>> bDur = duration.DurationUnit('16th')
            >>> cDur = duration.DurationUnit('16th')
            >>> aDur == bDur
            False

        ::

            >>> cDur == bDur
            True

        '''
        if other is None or not isinstance(other, DurationCommon):
            return False
        if self.type == other.type:
            if self.dots == other.dots:
                if self.tuplets == other.tuplets:
                    if self.quarterLength == other.quarterLength:
                        return True
        return False

    def __ne__(self, other):
        '''
        Test not equality.

        ::

            >>> aDur = duration.DurationUnit('quarter')
            >>> bDur = duration.DurationUnit('16th')
            >>> cDur = duration.DurationUnit('16th')
            >>> aDur != bDur
            True

        ::

            >>> cDur != bDur
            False

        '''
        return not self.__eq__(other)

    def __repr__(self):
        '''
        Return a string representation.

        ::

            >>> aDur = duration.DurationUnit('quarter')
            >>> repr(aDur)
            '<music21.duration.DurationUnit 1.0>'

        '''
        qlr = self.quarterLength
        
        return '<music21.duration.DurationUnit %s>' % qlr

    ### PUBLIC METHODS ###

    def appendTuplet(self, newTuplet):
        newTuplet.frozen = True
        self._tuplets = self._tuplets + (newTuplet,)
        self._quarterLengthNeedsUpdating = True

    def augmentOrDiminish(self, amountToScale, inPlace=True):
        '''
        Given a number greater than zero, multiplies the current quarterLength
        of the duration by the number and resets the components for the
        duration (by default).  Or if inPlace is set to False, returns a new
        duration that has the new length.


        Note that the default for inPlace is the opposite of what it is for
        augmentOrDiminish on a Stream.  This is done purposely to reflect the
        most common usage.

        >>> bDur = duration.DurationUnit('16th')
        >>> bDur
        <music21.duration.DurationUnit 0.25>

        >>> bDur.augmentOrDiminish(2)
        >>> bDur.quarterLength
        0.5
        >>> bDur.type
        'eighth'
        >>> bDur
        <music21.duration.DurationUnit 0.5>

        >>> bDur.augmentOrDiminish(4)
        >>> bDur.type
        'half'
        >>> bDur
        <music21.duration.DurationUnit 2.0>

        >>> bDur.augmentOrDiminish(.125)
        >>> bDur.type
        '16th'
        >>> bDur
        <music21.duration.DurationUnit 0.25>

        >>> cDur = bDur.augmentOrDiminish(16, inPlace=False)
        >>> cDur, bDur
        (<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>)
        '''
        if not amountToScale > 0:
            raise DurationException('amountToScale must be greater than zero')

        if inPlace:
            post = self
        else:
            post = DurationUnit()
        # note: this is not yet necessary, as changes are configured
        # by quarterLength, and this process generates new tuplets
        # if alternative scaling methods are used for performance, this
        # method can be used.
#         for tup in post._tuplets:
#             tup.augmentOrDiminish(amountToScale, inPlace=True)
        # possible look for convenient optimizations for easy scaling
        # not sure if _link should be altered?
        post.quarterLength = self.quarterLength * amountToScale
        if not inPlace:
            return post
        else:
            return None

    def link(self):
        self._link = True

    def setTypeFromNum(self, typeNum):
        #numberFound = None
        if str(typeNum) in typeFromNumDict:
            self.type = typeFromNumDict[str(typeNum)]
        else:
            raise DurationException("cannot find number %s" % typeNum)

    def unlink(self):
        self._link = False

    def updateQuarterLength(self):
        '''
        Updates the quarterLength if _link is True. Called by
        self._getQuarterLength if _quarterLengthNeedsUpdating is set to True.

        To set quarterLength, use self.quarterLength.

        ::

            >>> bDur = duration.DurationUnit('16th')
            >>> bDur.quarterLength
            0.25

            >>> bDur.unlink()
            >>> bDur.quarterLength = 234
            >>> bDur.quarterLength
            234.0

            >>> bDur.type
            '16th'

            >>> bDur.link() # if linking is restored, type is used to get qLen
            >>> bDur.updateQuarterLength()
            >>> bDur.quarterLength
            0.25

        '''
        if self._link is True:
            self._qtrLength = convertTypeToQuarterLength(
                self.type,
                self.dots,
                self.tuplets,
                self.dotGroups,
                ) # add self.dotGroups
        self._quarterLengthNeedsUpdating = False

    def updateType(self):
        if self._link is True:
            # cant update both at same time
            self._quarterLengthNeedsUpdating = False
            tempDurations = quarterLengthToDurations(self.quarterLength)
            if len(tempDurations) > 1:
                self.type = 'unexpressible'
                self.dots = 0
                self.tuplets = ()
            else:
                self.type = tempDurations[0].type
                self.dots = tempDurations[0].dots
                self.tuplets = tempDurations[0].tuplets
        self._typeNeedsUpdating = False

    ### PUBLIC PROPERTIES ###

    @property
    def dotGroups(self):
        '''
        _dots is a list (so we can do weird things like dot groups)
        _getDotGroups lets you do the entire list (as a tuple)

        ::

            >>> d1 = duration.DurationUnit()
            >>> d1.type = 'half'
            >>> d1.dotGroups = [1, 1]  # dotted dotted half
            >>> d1.dots
            1

        ::

            >>> d1.dotGroups
            (1, 1)

        ::

            >>> d1.quarterLength
            4.5

        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return tuple(self._dots)

    @dotGroups.setter
    def dotGroups(self, listValue):
        '''
        Sets the number of dots in a dot group
        '''
        self._quarterLengthNeedsUpdating = True
        if common.isListLike(listValue):
            if not isinstance(listValue, list):
                self._dots = list(listValue)
            else:
                self._dots = listValue
        else:
            raise DurationException("number of dots must be a number")

    @property
    def dots(self):
        '''
        _dots is a list (so we can do weird things like dot groups)
        Normally we only want the first element.
        So that's what dots returns...

        ::

            >>> a = duration.DurationUnit()
            >>> a.dots # dots is zero before assignment
            0

        ::

            >>> a.type = 'quarter'
            >>> a.dots = 1
            >>> a.quarterLength
            1.5

        ::

            >>> a.dots = 2
            >>> a.quarterLength
            1.75

        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._dots[0]

    @dots.setter
    def dots(self, value):
        if value != self._dots[0]:
            self._quarterLengthNeedsUpdating = True
        if common.isNum(value):
            self._dots = (value,)
        else:
            raise DurationException("number of dots must be a number")

    @property
    def fullName(self):
        '''
        Return the most complete representation of this Duration, providing
        dots, type, tuplet, and quarter length representation.

        ::

            >>> d = duration.DurationUnit()
            >>> d.quarterLength = 1.5
            >>> d.fullName
            'Dotted Quarter'

        ::

            >>> d = duration.DurationUnit()
            >>> d.quarterLength = 1.75
            >>> d.fullName
            'Double Dotted Quarter'

        ::

            >>> d = duration.DurationUnit()
            >>> d.type = 'half'
            >>> d.fullName
            'Half'

        ::

            >>> d = duration.DurationUnit()
            >>> d.type = 'longa'
            >>> d.fullName
            'Imperfect Longa'

            >>> d.dots = 1
            >>> d.fullName
            'Perfect Longa'
        '''
        dots = self.dots
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
            dotStr = None

        tuplets = self.tuplets
        #environLocal.printDebug(['tuplets', tuplets])
        tupletStr = None
        if len(tuplets) > 0:
            tupletStr = []
            for tup in tuplets:
                tupletStr.append(tup.fullName)
            tupletStr = ' '.join(tupletStr)
            #environLocal.printDebug(['tupletStr', tupletStr, tuplets])

        msg = []
        # type added here
        typeStr = self.type
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

        if tupletStr is not None:
            msg.append('%s ' % tupletStr)
        # only add QL display if there are no dots or tuplets
        if tupletStr is not None or dots >= 3 or typeStr.lower() == 'complex':
            qlStr = common.mixedNumeral(self.quarterLength)
            msg.append('(%s QL)' % (qlStr))

        return ''.join(msg).strip() # avoid extra space

    @property
    def isLinked(self):
        '''
        Return a boolean describing this duration is linked or not.

        >>> d = duration.DurationUnit()
        >>> d.isLinked
        True

        >>> d.unlink()
        >>> d.isLinked
        False
        '''
        return self._link

    @property
    def ordinal(self):
        '''
        Converts type to an ordinal number where maxima = 1 and 1024th = 14;
        whole = 4 and quarter = 6.  Based on duration.ordinalTypeFromNum

        >>> a = duration.DurationUnit('whole')
        >>> a.ordinal
        4

        >>> b = duration.DurationUnit('maxima')
        >>> b.ordinal
        1

        >>> c = duration.DurationUnit('1024th')
        >>> c.ordinal
        14
        '''
        if self._typeNeedsUpdating:
            self.updateType()
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

    def _getQuarterLengthFloat(self):
        '''
        Property for getting or setting the quarterLength of a
        DurationUnit.

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.quarterLength
        3.0

        >>> a.type
        'half'

        >>> a.dots
        1

        >>> a.quarterLength = .5
        >>> a.type
        'eighth'

        >>> a.quarterLength = .75
        >>> a.type
        'eighth'

        >>> a.dots
        1

        >>> b = duration.DurationUnit()
        >>> b.quarterLength = 16
        >>> b.type
        'longa'
        '''
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        return float(self._qtrLength)
    
    def _getQuarterLengthRational(self):
        '''
        Property for getting or setting the quarterLength of a
        DurationUnit.

        This will return a float if it's binary representable, or a fraction if not...

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.quarterLength
        3.0
        >>> a.quarterLength = .75
        >>> a.quarterLength
        0.75
        >>> a.quarterLength = 2.0/3
        >>> a.type
        'quarter'
        >>> a.tuplets
        (<music21.duration.Tuplet 3/2/quarter>,)
        >>> a.quarterLength
        Fraction(2, 3)            
        '''
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        return self._qtrLength
        

    def _setQuarterLength(self, value):
        '''Set the quarter note length to the specified value.

        (We no longer unlink if quarterLength is greater than a longa)

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.type
        'half'
        >>> a.dots
        1

        >>> a.quarterLength = .5
        >>> a.type
        'eighth'

        >>> a.quarterLength = .75
        >>> a.type
        'eighth'
        >>> a.dots
        1

        >>> b = duration.DurationUnit()
        >>> b.quarterLength = 16
        >>> b.type
        'longa'

        >>> c = duration.DurationUnit()
        >>> c.quarterLength = 129
        >>> c.type
        Traceback (most recent call last):
            ...
        DurationException: Cannot return types greater than double duplex-maxima, your length was 129.0 : remove this when we are sure this works...
        '''
        if not common.isNum(value):
            raise DurationException(
            "not a valid quarter length (%s)" % value)
            
        if self._link:
            self._typeNeedsUpdating = True
        
        value = opFrac(value)
        self._qtrLength = value

    quarterLength      = property(_getQuarterLengthRational, _setQuarterLength)
    quarterLengthFloat = property(_getQuarterLengthFloat, _setQuarterLength)

    @property
    def tuplets(self):
        '''Return a tuple of Tuplet objects '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._tuplets

    @tuplets.setter
    def tuplets(self, value):
        '''Takes in a tuple of Tuplet objects
        '''
        if not isinstance(value, tuple):
            raise DurationException(
            "value submitted (%s) is not a tuple of tuplets" % value)
        if self._tuplets != value:
            self._quarterLengthNeedsUpdating = True
        # note that in some cases this methods seems to be called more
        # often than necessary
        #environLocal.printDebug(['assigning tuplets in DurationUnit',
        #                         value, id(value)])
        for thisTuplet in value:
            thisTuplet.frozen = True
        self._tuplets = value

    @property
    def type(self):
        '''
        Property for getting or setting the type of a DurationUnit.

        >>> a = duration.DurationUnit()
        >>> a.quarterLength = 3
        >>> a.type
        'half'

        >>> a.dots
        1

        >>> a.type = 'quarter'
        >>> a.quarterLength
        1.5

        >>> a.type = '16th'
        >>> a.quarterLength
        0.375
        '''
        if self._typeNeedsUpdating:
            self.updateType()
        return self._type

    @type.setter
    def type(self, value):
        if value not in typeToDuration:
            raise DurationException("no such type exists: %s" % value)
        if value != self._type:  # only update if different
            # link status will be checked in quarterLengthNeeds updating
            self._quarterLengthNeedsUpdating = True
        self._type = value


#-------------------------------------------------------------------------------


class ZeroDuration(DurationUnit):
    '''
    Represents any Music21 element that does not last any length of time.
    '''

    ### CLASS VARIABLES ###

    isGrace = False

    __slots__ = ()

    ### INITIALIZER ###

    def __init__(self):
        DurationUnit.__init__(self)
        self.unlink()
        self.type = 'zero'
        self.quarterLength = 0.0

    ### SPECIAL METHODS ###

    def __repr__(self):
        '''Return a string representation.

        >>> zDur = duration.ZeroDuration()
        >>> repr(zDur)
        '<music21.duration.ZeroDuration>'
        '''
        return '<music21.duration.ZeroDuration>'


#-------------------------------------------------------------------------------


class DurationException(exceptions21.Music21Exception):
    pass


class Duration(DurationCommon):
    '''
    Durations are one of the most important objects in music21. A Duration
    represents a span of musical time measurable in terms of quarter notes (or
    in advanced usage other units). For instance, "57 quarter notes" or "dotted
    half tied to quintuplet sixteenth note" or simply "quarter note."

    A Duration object is made of one or more DurationUnit objects stored on the
    `components` list.

    Multiple DurationUnits in a single Duration may be used to express tied
    notes, or may be used to split duration across barlines or beam groups.
    Some Duration objects are not expressible as a single notation unit.

    Duration objects are not Music21Objects. Duration objects share many
    properties and attributes with DurationUnit objects, but Duration is not a
    subclass of DurationUnit.

    If a single argument is passed to Duration() and it is a string, then it is
    assumed to be a type, such as 'half', 'eighth', or '16th', etc.  If that
    single argument is a number then it is assumed to be a quarterLength (2 for
    half notes, .5 for eighth notes, .75 for dotted eighth notes, .333333333
    for a triplet eighth, etc.).  If one or more named arguments are passed
    then the Duration() is configured according to those arguments.  Supported
    arguments are 'type', 'dots', or 'components' (a list of
    :class:`music21.duration.DurationUnit` objects),

    Example 1: a triplet eighth configured by quarterLength:

    >>> d = duration.Duration(.333333333)
    >>> d.type
    'eighth'

    >>> d.tuplets
    (<music21.duration.Tuplet 3/2/eighth>,)

    Example 2: A Duration made up of multiple
    :class:`music21.duration.DurationUnit` objects automatically configured by
    the specified quarterLength.

    >>> d2 = duration.Duration(.625)
    >>> d2.type
    'complex'

    >>> d2.components
    [<music21.duration.DurationUnit 0.5>, <music21.duration.DurationUnit 0.125>]

    Example 3: A Duration configured by keywords.

    >>> d3 = duration.Duration(type = 'half', dots = 2)
    >>> d3.quarterLength
    3.5
    '''

    ### CLASS VARIABLES ###

    isGrace = False

    __slots__ = (
        'linkage',
        '_cachedIsLinked',
        '_components',
        '_qtrLength',
        )

    ### INITIALIZER ###

    def __init__(self, *arguments, **keywords):
        '''
        First positional argument is assumed to be type string or a quarterLength.
        '''
        DurationCommon.__init__(self)
        self._quarterLengthNeedsUpdating = False
        self._qtrLength = 0.0
        # always have one DurationUnit object
        self._components = []
        # assume first arg is a duration type
        self._componentsNeedUpdating = False
        # defer updating until necessary
        self._quarterLengthNeedsUpdating = False
        self._cachedIsLinked = None  # store for access w/o looking at components
        if len(arguments) > 0:
            if common.isNum(arguments[0]):
                self.quarterLength = arguments[0]
            else:
                self.addDurationUnit(DurationUnit(arguments[0]))
        if 'dots' in keywords:
            storeDots = keywords['dots']
        else:
            storeDots = 0
        if "components" in keywords:
            self.components = keywords["components"]
            # this is set in _setComponents
            #self._quarterLengthNeedsUpdating = True
        if 'type' in keywords:
            du = DurationUnit(keywords['type'])
            if storeDots > 0:
                du.dots = storeDots
            self.addDurationUnit(du)
        # permit as keyword so can be passed from notes
        if 'quarterLength' in keywords:
            self.quarterLength = keywords['quarterLength']
        # linkage specifies the thing used to connect durations.
        # If undefined, nothing is used.  "tie" is the most common linkage
        # Other sorts of things could be
        # dotted-ties, arrows, none, etc. As of Sep. 2008 -- not used.
        if "linkage" in keywords:
            self.linkage = keywords["linkages"]
        else:
            self.linkage = None

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

        >>> dDur = duration.ZeroDuration()
        >>> eDur = duration.ZeroDuration()
        >>> dDur == eDur
        True
        '''
        if other is None or not isinstance(other, DurationCommon):
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
        if self.isLinked:
            return '<music21.duration.Duration %s>' % self.quarterLength
        else:
            return '<music21.duration.Duration unlinked type:%s quarterLength:%s>' % (self.type, self.quarterLength)

    ### PRIVATE METHODS ###

    def _updateComponents(self):
        '''
        This method will re-construct components and thus is not good if the
        components are already configured as you like
        '''
        # this update will not be necessary
        self._quarterLengthNeedsUpdating = False
        if self.isLinked:
            try:
                self.components = quarterLengthToDurations(self.quarterLength)
            except DurationException:
                print("problem updating components of note with quarterLength %s, chokes quarterLengthToDurations\n" % self.quarterLength)
                raise
        self._componentsNeedUpdating = False

    ### PUBLIC METHODS ###

    def addDurationUnit(self, dur, link=True):
        '''
        Add a DurationUnit or a Duration's components to this Duration.
        Does not simplify the Duration.  For instance, adding two
        quarter notes results in two tied quarter notes, not one half note.
        See `consolidate` below for more info on how to do that.

        >>> a = duration.Duration('quarter')
        >>> b = duration.Duration('quarter')
        >>> a.addDurationUnit(b)
        >>> a.quarterLength
        2.0
        >>> a.type
        'complex'
        '''
        if isinstance(dur, DurationUnit):
            if not link:
                dur.unlink()
            self.components.append(dur)
        elif isinstance(dur, Duration): # its a Duration object
            for c in dur.components:
                cNew = copy.deepcopy(c) # must copy as otherwise will unlink
                if not link:
                    cNew.unlink()
                self.components.append(cNew)
        else: # its a number that may produce more than one component
            for c in Duration(dur).components:
                if not link:
                    c.unlink()
                self.components.append(c)
        if link:
            self._quarterLengthNeedsUpdating = True

    def appendTuplet(self, newTuplet):
        self.tuplets = self.tuplets + (newTuplet,)

    def augmentOrDiminish(self, amountToScale,
        retainComponents=False, inPlace=True):
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
        >>> aDur.augmentOrDiminish(2)
        >>> aDur.quarterLength
        3.0
        >>> aDur.type
        'half'
        >>> aDur.dots
        1


        A complex duration that cannot be expressed as a single notehead (component)

        >>> bDur = duration.Duration()
        >>> bDur.quarterLength = 2.125 # requires components
        >>> bDur.quarterLength
        2.125
        >>> len(bDur.components)
        2
        >>> bDur.components
        [<music21.duration.DurationUnit 2.0>, <music21.duration.DurationUnit 0.125>]

        >>> cDur = bDur.augmentOrDiminish(2, retainComponents=True, inPlace=False)
        >>> cDur.quarterLength
        4.25
        >>> cDur.components[0].tuplets
        ()
        >>> cDur.components
        [<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>]

        >>> dDur = bDur.augmentOrDiminish(2, retainComponents=False, inPlace=False)
        >>> dDur.components
        [<music21.duration.DurationUnit 4.0>, <music21.duration.DurationUnit 0.25>]
        '''
        if not amountToScale > 0:
            raise DurationException('amountToScale must be greater than zero')

        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)

        if retainComponents:
            for d in post.components:
                d.augmentOrDiminish(amountToScale, inPlace=True)
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = True
        else:
            post.quarterLength = post.quarterLength * amountToScale

        if not inPlace:
            return post
        else:
            return None

    def clear(self):
        '''
        Permit all components to be removed.
        (It is not clear yet if this is needed: YES! for zero duration!)

        >>> a = duration.Duration()
        >>> a.quarterLength = 4
        >>> a.type
        'whole'
        >>> a.clear()
        >>> a.quarterLength
        0.0
        >>> a.type
        'zero'
        '''
        self.components = []
        self._quarterLengthNeedsUpdating = True

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
        >>> components.append(duration.Duration('quarter'))
        >>> components.append(duration.Duration('quarter'))
        >>> components.append(duration.Duration('quarter'))

        >>> a = duration.Duration()
        >>> a.components = components
        >>> a.updateQuarterLength()
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

        This cannot be done for all Durations, as DurationUnits cannot express all durations
        
        >>> a = duration.Duration()
        >>> a.fill(['quarter', 'half', 'quarter'])
        >>> a.quarterLength
        4.0
        >>> len(a.components)
        3
        >>> a.consolidate()
        >>> a.quarterLength
        4.0
        >>> len(a.components)
        1

        But it gains a type!

        >>> a.type
        'whole'
        '''
        if len(self.components) == 1:
            pass # nothing to be done
        else:
            dur = DurationUnit()
            # if quarter length is not notatable, will automatically unlink
            # some notations will not properly unlink, and raise an error
            dur.quarterLength = self.quarterLength
            self.components = [dur]

    def expand(self, qLenDiv=4):
        '''
        Make a duration notatable by partitioning it into smaller
        units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength
        '''
        self.components = partitionQuarterLength(
            self.quarterLength, qLenDiv)
        self._componentsNeedUpdating = False

    def fill(self, quarterLengthList=('quarter', 'half', 'quarter')):
        '''Utility method for testing; a quick way to fill components. This will
        remove any exisiting values.
        '''
        self.components = []
        for x in quarterLengthList:
            self.addDurationUnit(Duration(x))

    def getGraceDuration(self, appogiatura=False):
        '''
        Return a deepcopy of this Duration as a GraceDuration instance with the same types.

        >>> d = duration.Duration(1.25)
        >>> gd = d.getGraceDuration()
        >>> gd.quarterLength
        0.0
        >>> [(x.quarterLength, x.type) for x in gd.components]
        [(0.0, 'quarter'), (0.0, '16th')]
        >>> d.quarterLength
        1.25
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        # manually copy all components
        components = []
        for c in self.components:
            components.append(copy.deepcopy(c))
        # create grace duration
        if appogiatura:
            gd = AppogiaturaDuration()
        else:
            gd = GraceDuration()
        gd.components = components # set new components
        gd.unlink()
        gd.quarterLength = 0.0
        return gd

    def link(self):
        '''
        Set all components to be linked
        '''
        if len(self.components) >= 1:
            for c in self.components:
                c.link()
            self._cachedIsLinked = True
            # quarter length will be set based on component types
            self._quarterLengthNeedsUpdating = True
        else: # there may be components and still a zero type
            raise DurationException("zero DurationUnits in components: cannt link or unlink")

    def setQuarterLengthUnlinked(self, value):
        '''
        Set the quarter note length to the specified value.
        '''
        # quarter length is always obtained from _qtrLength, even when
        # not linked; yet a component must be present to provide a type
        
        self._qtrLength = value
        if len(self._components) == 0:
            if self._qtrLength == 0.0: # if not set create a default
                self._components.append(ZeroDuration())
            else:
                du = DurationUnit() # will get default quarter
                du.unlink()
                self._components.append(du)
        # keep components, simply unlink; quarter lengths stored will
        # not be included in this elements quater length
        else:
            for c in self._components:
                c.unlink()
        # reach ahead and set cached is linked: no need to check components
        self._cachedIsLinked = False

    def setTypeUnlinked(self, value):
        '''
        Make this Duration unlinked, and set the type. Quarter note length will not be adjusted.
        '''
        # need to check that type is valid
        if value not in ordinalTypeFromNum:
            raise DurationException("no such type exists: %s" % value)

        if len(self.components) == 1:
            # change the existing DurationUnit to the this type
            self.components[0].unlink()
            self.components[0].type = value
            #self._quarterLengthNeedsUpdating = True
        elif self.isComplex: # more than one component
            raise DurationException("cannot yet set type for a complex Duration")
        else: # permit creating a new comoponent
            # create a new duration unit; if link is True, will unlink
            self.addDurationUnit(DurationUnit(value), link=False) # updates
            #self._quarterLengthNeedsUpdating = True
        self._cachedIsLinked = False

    def sliceComponentAtPosition(self, quarterPosition):
        '''
        Given a quarter position within a component, divide that
        component into two components.

        >>> a = duration.Duration()
        >>> a.clear() # need to remove default
        >>> components = []

        >>> a.addDurationUnit(duration.Duration('quarter'))
        >>> a.addDurationUnit(duration.Duration('quarter'))
        >>> a.addDurationUnit(duration.Duration('quarter'))

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
            d1 = Duration()
            d1.quarterLength = slicePoint

            d2 = Duration()
            d2.quarterLength = remainder

            self.components[sliceIndex: (sliceIndex + 1)] = [d1, d2]
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
        >>> d1.dotGroups = [1,1]
        >>> d1.quarterLength
        4.5
        >>> d2 = d1.splitDotGroups()
        >>> d2.components
        [<music21.duration.DurationUnit 3.0>, <music21.duration.DurationUnit 1.5>]
        >>> d2.quarterLength
        4.5

        Here's how a system that does not support dotGroups can still display
        the notes accurately.  N.B. MusicXML does this automatically, so
        no need.

        >>> n1 = note.Note()
        >>> n1.duration = d1
        >>> n1.duration = n1.duration.splitDotGroups()
        >>> n1.duration.components
        [<music21.duration.DurationUnit 3.0>, <music21.duration.DurationUnit 1.5>]
        >>> s1 = stream.Stream()
        >>> s1.append(meter.TimeSignature('9/8'))
        >>> s1.append(n1)
        >>> #_DOCS_SHOW s1.show('lily.png')
        .. image:: images/duration_splitDotGroups.*

        >>> n2 = note.Note()
        >>> n2.duration.type = 'quarter'
        >>> n2.duration.dotGroups = [1,1]
        >>> n2.quarterLength
        2.25
        >>> #_DOCS_SHOW n2.show() # generates a dotted-quarter tied to dotted-eighth
        '''
        dG = self.dotGroups
        if len(dG) < 2:
            return copy.deepcopy(self)
        else:
            newDuration = copy.deepcopy(self)
            newDuration.dotGroups = [0]
            newDuration.components[0].dots = dG[0]
            for i in range(1, len(dG)):
                newComponent = copy.deepcopy(newDuration.components[i-1])
                newComponent.type = nextSmallerType(newDuration.components[i-1].type)
                newComponent.dots = dG[i]
                newDuration.components.append(newComponent)
            return newDuration

    def unlink(self):
        '''
        Unlink all components allowing the type, dots, etc., to not be the same as the
        normal representation in quarterLength units.
        '''
        if len(self._components) >= 1:
            for c in self._components: # these are Duration objects
                c.unlink()
            self._cachedIsLinked = False

    def updateQuarterLength(self):
        '''Look to components and determine quarter length.
        '''
        if self.isLinked:
            self._qtrLength = 0.0
            for dur in self.components:
                # if components quarterLength needs to be updated, it will
                # be updated when this property is called
                qlr = dur.quarterLength
                self._qtrLength = opFrac(self._qtrLength + qlr)
        self._quarterLengthNeedsUpdating = False

    ### PUBLIC PROPERTIES ###

    @property
    def components(self):
        if self._componentsNeedUpdating:
            self._updateComponents()
        return self._components

    @components.setter
    def components(self, value):
        # previously, self._componentsNeedUpdating was not set here
        # this needs to be set because if _componentsNeedUpdating is True
        # new components will be derived from quarterLength
        if self._components is not value:
            self._componentsNeedUpdating = False
            self._components = value
            # this is Ture b/c components are note the same
            self._quarterLengthNeedsUpdating = True
            # musst be cleared
            self._cachedIsLinked = None

    @property
    def dotGroups(self):
        '''
        See the explanation under :class:`~music21.duration.DurationUnit` about
        what dotGroups (medieval dotted-dotted notes are).  In a complex
        duration, only the dotGroups of the first component matter

        >>> from music21 import duration
        >>> a = duration.Duration()
        >>> a.type = 'half'
        >>> a.dotGroups = [1,1]
        >>> a.quarterLength
        4.5
        '''
        if self._componentsNeedUpdating is True:
            self._updateComponents()

        if len(self.components) == 1:
            return self.components[0].dotGroups
        elif len(self.components) > 1:
            return None
        else: # there must be 1 or more components
            raise DurationException("Cannot get dotGroups on an object with zero DurationUnits in its duration.components (will cause problems later even if dotGroups are ignored)")

    @dotGroups.setter
    def dotGroups(self, value):
        if not common.isListLike(value):
            raise DurationException('only list-like dotGroups values can be used with this method.')
        if len(self.components) == 1:
            self.components[0].dotGroups = value
            self._quarterLengthNeedsUpdating = True
        elif len(self.components) > 1:
            raise DurationException("setting dotGroups: Myke and Chris need to decide what that means")
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")

    @property
    def dots(self):
        '''
        Returns the number of dots in the Duration
        if it is a simple Duration.  Otherwise raises error.
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        if len(self.components) == 1:
            return self.components[0].dots
        elif len(self.components) > 1:
            return None
        else:  # there must be 1 or more components
            raise DurationException("Cannot get dots on an object with zero DurationUnits in its duration.components")

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
        if not common.isNum(value):
            raise DurationException('only numeric dot values can be used with this method.')
        if len(self.components) == 1:
            self.components[0].dots = value
            self._quarterLengthNeedsUpdating = True
        elif len(self.components) > 1:
            raise DurationException("setting type on Complex note: Myke and Chris need to decide what that means")
        else:  # there must be 1 or more components
            raise DurationException("Cannot set dots on an object with zero DurationUnits in its duration.components")

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

        >>> d.addDurationUnit(duration.DurationUnit(.3333333))
        >>> d.fullName
        'Quarter tied to 16th tied to Eighth Triplet (1/3 QL) (1 7/12 total QL)'

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
        if len(self.components) > 1:
            msg = []
            for part in self.components:
                msg.append(part.fullName)
            msg = ' tied to '.join(msg)
            qlStr = common.mixedNumeral(self.quarterLength)
            msg += ' (%s total QL)' % (qlStr)
            return msg
        if len(self.components) == 1:
            return self.components[0].fullName
        else: # zero components
            return 'Zero Duration (0 total QL)'

    @property
    def isComplex(self):
        '''
        Returns True if this Duration has more than one DurationUnit object on
        the `component` list.  That is to say if it's a single Duration that
        need multiple tied noteheads to represent.

        >>> aDur = duration.Duration()
        >>> aDur.quarterLength = 1.375
        >>> aDur.isComplex
        True

        >>> len(aDur.components)
        2

        >>> aDur.components
        [<music21.duration.DurationUnit 1.0>, <music21.duration.DurationUnit 0.375>]

        >>> bDur = duration.Duration()
        >>> bDur.quarterLength = 1.6666666
        >>> bDur.isComplex
        True

        >>> len(bDur.components)
        2

        >>> bDur.components
        [<music21.duration.DurationUnit 1.0>, <music21.duration.DurationUnit 2/3>]
            
        >>> cDur = duration.Duration()
        >>> cDur.quarterLength = .25
        >>> cDur.isComplex
        False

        >>> len(cDur.components)
        1
        '''
        if len(self.components) > 1:
            return True
#        for dur in self.components:
            #environLocal.printDebug(['dur in components', dur])
            # any one unlinked component means this is complex
            #if self._link is False:
            #    return True
        else: 
            return False

    @property
    def isLinked(self):
        '''
        Return a boolean describing this duration is linked or not.  The
        `isLinked` of the first component in a complex duration determines the
        link status for the entire Duration

        >>> d = duration.Duration(2.0)
        >>> d.type
        'half'

        >>> d.quarterLength
        2.0

        >>> d.isLinked
        True

        >>> d.unlink()
        >>> d.quarterLength = 4.0
        >>> d.type
        'half'

        >>> d.isLinked
        False
        '''
        # reset _cachedIsLinked to None when components have changed
        if self._cachedIsLinked is None:
            if len(self._components) > 0:
                # if there are components, determine linked status from them
                for c in self._components:
                    if c.isLinked:
                        self._cachedIsLinked = True
                        break
                    else:
                        self._cachedIsLinked = False
                        break
            else:  # there are no components, than it is linked (default)
                self._cachedIsLinked = True
        return self._cachedIsLinked

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

    
    def _getQuarterLengthFloat(self):
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        # this is set in updateQuarterLength
        #self._quarterLengthNeedsUpdating = False
        return float(self._qtrLength)

    def _getQuarterLengthRational(self):
        if self._quarterLengthNeedsUpdating:
            self.updateQuarterLength()
        # this is set in updateQuarterLength
        #self._quarterLengthNeedsUpdating = False
        return self._qtrLength


    def _setQuarterLength(self, value):
        if self._qtrLength != value:
            value = opFrac(value)
            if value == 0.0 and self.isLinked is True:
                self.clear()
            self._qtrLength = value
            self._componentsNeedUpdating = True
            self._quarterLengthNeedsUpdating = False

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
        When there are more than one component, each component may have its
        own tuplet.
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        if len(self.components) > 1:
            return None
        elif len(self.components) == 1:
            return self.components[0].tuplets
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")

    @tuplets.setter
    def tuplets(self, tupletTuple):
        #environLocal.printDebug(['assigning tuplets in Duration', tupletTuple])
        if len(self.components) > 1:
            raise DurationException("setting tuplets on Complex note: Myke and Chris need to decide what that means")
        elif len(self.components) == 1:
            for thisTuplet in tupletTuple:
                thisTuplet.frozen = True
            self.components[0].tuplets = tupletTuple
            self._quarterLengthNeedsUpdating = True
        else: # there must be 1 or more components
            raise DurationException("zero DurationUnits in components")

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
        if self._componentsNeedUpdating:
            self._updateComponents()
        if len(self.components) == 1:
            return self.components[0].type
        elif len(self.components) > 1:
            return 'complex'
        else: # there may be components and still a zero type
            return 'zero'
#            raise DurationException("zero DurationUnits in components")

    @type.setter
    def type(self, value):
        # need to check that type is valid
        if value not in ordinalTypeFromNum:
            raise DurationException("no such type exists: %s" % value)

        if len(self.components) == 1:
            # change the existing DurationUnit to the this type
            self.components[0].type = value
            self._quarterLengthNeedsUpdating = True
        elif self.isComplex: # more than one component
            raise DurationException("setting type on Complex note: Myke and Chris need to decide what that means")
            # what do we do if we already have multiple DurationUnits
        else: # permit creating a new comoponent
            # create a new duration unit
            self.addDurationUnit(DurationUnit(value)) # updates
            self._quarterLengthNeedsUpdating = True



class GraceDuration(Duration):
    '''
    A Duration that, no matter how it is created, always has a quarter length
    of zero.

    GraceDuration can be created with an implied quarter length and type; these
    values are used to configure the duration, but then may not be relevant
    after instantiation.

    ::

        >>> gd = duration.GraceDuration(type='half')
        >>> gd.quarterLength
        0.0

    ::

        >>> gd.type
        'half'

    ::

        >>> gd = duration.GraceDuration(.25)
        >>> gd.type
        '16th'

    ::

        >>> gd.quarterLength
        0.0

    ::

        >>> gd.isLinked
        False

    ::

        >>> gd = duration.GraceDuration(1.25)
        >>> gd.type
        'complex'

    ::

        >>> gd.quarterLength
        0.0

    ::

        >>> [(x.quarterLength, x.type) for x in gd.components]
        [(0.0, 'quarter'), (0.0, '16th')]

    '''

    # TODO: there are many properties/methods of Duration that must
    # be overridden to provide consisten behavior

    ### CLASS VARIABLES ###

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
        self.unlink()
        self.quarterLength = 0.0
        
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
        #self.unlink()
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

        >>> n1 = note.Note()
        >>> n1.duration.quarterLength = 2.0/3
        >>> n1.duration.quarterLength
        Fraction(2, 3)
        >>> s.append(n1)
        >>> n2 = note.Note()
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
        >>> tupletGroups = tf.findTupletGroups(incorporateGroupings = True)
        >>> tf.fixBrokenTupletDuration(tupletGroups[-1])
        >>> m1[-1].duration.tuplets[0]
        <music21.duration.Tuplet 3/2/whole>
        >>> m1[-1].duration.quarterLength
        Fraction(4, 3)
        '''
        if len(tupletGroup) == 0:
            return
        firstTup = tupletGroup[0].duration.tuplets[0]
        totalTupletDuration = firstTup.totalTupletLength()
        # TODO: Tuplets should all be as Fractions...
        currentTupletDuration = 0.0
        smallestTupletTypeOrdinal = None
        largestTupletTypeOrdinal = None

        for n in tupletGroup:
            currentTupletDuration += n.duration.quarterLength
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


        if round(currentTupletDuration, 7) == round(totalTupletDuration, 7):
            return
        else:
            excessRatio = round(currentTupletDuration / totalTupletDuration, 7)
            inverseExcessRatio = round(1.0/excessRatio, 7)

            if excessRatio == int(excessRatio): # divide tuplets into smaller
                largestTupletType = ordinalTypeFromNum[largestTupletTypeOrdinal]

                #print largestTupletTypeOrdinal, largestTupletType
                for n in tupletGroup:
                    n.duration.tuplets[0].durationNormal.type = largestTupletType
                    n.duration.tuplets[0].durationActual.type = largestTupletType

            elif inverseExcessRatio == int(inverseExcessRatio): # redefine tuplets by GCD
                smallestTupletType = ordinalTypeFromNum[smallestTupletTypeOrdinal]
                for n in tupletGroup:
                    n.duration.tuplets[0].durationNormal.type = smallestTupletType
                    n.duration.tuplets[0].durationActual.type = smallestTupletType
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

        self.assertAlmostEquals(dur3.quarterLength, 0.7)

        myTuplet = Tuplet()
        self.assertAlmostEquals(round(myTuplet.tupletMultiplier(), 3), 0.667)
        myTuplet.tupletActual = [5, DurationUnit('eighth')]
        self.assertAlmostEquals(myTuplet.tupletMultiplier(), 0.4)


    def testMxLoading(self):
        from music21.musicxml import fromMxObjects
        from music21 import musicxml
        a = musicxml.mxObjects.Note()
        a.setDefaults()
        m = musicxml.mxObjects.Measure()
        m.setDefaults()
        a.external['measure'] = m # assign measure for divisions ref
        a.external['divisions'] = m.external['divisions']
        c = fromMxObjects.mxToDuration(a)
        self.assertEqual(c.quarterLength, 1.0)

    def testTupletTypeComplete(self):
        '''
        Test setting of tuplet type when durations sum to expected completion
        '''
        # default tuplets group into threes when possible
        test, match = ([.333333] * 3 + [.1666666] * 6,
            ['start', None, 'stop', 'start', None, 'stop', 'start', None, 'stop'])
        inputTuplets = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            inputTuplets.append(d)
        updateTupletType(inputTuplets)
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

        updateTupletType(inputTuplets)
        output = []
        for d in inputTuplets:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)



    def testTupletTypeIncomplete(self):
        '''
        Test setting of tuplet type when durations do not sum to expected
        completion.
        '''

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
        updateTupletType(inputDurations)
        output = []
        for d in inputDurations:
            output.append(d.tuplets[0].type)
        #environLocal.printDebug(['got', output])
        self.assertEqual(output, match)


    def testAugmentOrDiminish(self):

        # test halfs and doubles

        for ql, half, double in [(2,1,4), (.5,.25,1), (1.5, .75, 3),
                                 (.6666666, .3333333, 1.3333333)]:

            d = Duration()
            d.quarterLength = ql
            a = d.augmentOrDiminish(.5, inPlace=False)
            self.assertAlmostEquals(a.quarterLength, half, 5)

            b = d.augmentOrDiminish(2, inPlace=False)
            self.assertAlmostEquals(b.quarterLength, double, 5)


        # testing tuplets in duration units

        a = DurationUnit()
        a.quarterLength = .3333333
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.))
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.5>')

        a.augmentOrDiminish(2)
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 1.0>')

        a.augmentOrDiminish(.25)
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.25>')


        # testing tuplets on Durations
        a = Duration()
        a.quarterLength = .3333333
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.5>')

        a.augmentOrDiminish(2)
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 1.0>')

        a.augmentOrDiminish(.25)
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2/3.), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal), '<music21.duration.Duration 0.25>')


    def testUnlinkedTypeA(self):
        from music21 import duration

        du = duration.DurationUnit()
        du.unlink()
        du.quarterLength = 5.0
        du.type = 'quarter'
        self.assertEqual(du.quarterLength, 5.0)
        self.assertEqual(du.type, 'quarter')
        #print du.type, du.quarterLength

        d = duration.Duration()
        self.assertEqual(d.isLinked, True) # note set
        d.setTypeUnlinked('quarter')
        self.assertEqual(d.type, 'quarter')
        self.assertEqual(d.quarterLength, 0.0) # note set
        self.assertEqual(d.isLinked, False) # note set

        d.setQuarterLengthUnlinked(20)
        self.assertEqual(d.quarterLength, 20.0)
        self.assertEqual(d.isLinked, False) # note set

        # can set type  and will remain unlinked
        d.type = '16th'
        self.assertEqual(d.type, '16th')
        self.assertEqual(d.quarterLength, 20.0)
        self.assertEqual(d.isLinked, False) # note set

        # can set quater length and will remain unlinked
        d.quarterLength = 0.0
        self.assertEqual(d.type, '16th')
        self.assertEqual(d.isLinked, False) # note set


#         d = duration.Duration()
#         d.setTypeUnlinked('quarter')
#         self.assertEqual(d.type, 'quarter')
#         self.assertEqual(d.quarterLength, 0.0) # note set
#         self.assertEqual(d.isLinked, False) # note set
#
#         d.setQuarterLengthUnlinked(20)
#         self.assertEqual(d.quarterLength, 20.0)
#         self.assertEqual(d.isLinked, False) # note set

    def xtestStrangeMeasure(self):
        from music21 import corpus
        j1 = corpus.parse('trecento/PMFC_06-Jacopo-03a')
        x = j1.parts[0].getElementsByClass('Measure')[42]
        x._cache = {}
        print(x.duration)
        print(x.duration.components)

    def testSimpleSetQuarterLength(self):
        d = Duration()
        d.quarterLength = 0.33333333333333
        self.assertEqual(repr(d.quarterLength), 'Fraction(1, 3)')
        self.assertEqual(d._components, [] )
        self.assertEqual(d._componentsNeedUpdating, True )
        self.assertEqual(str(d.components), '[<music21.duration.DurationUnit 1/3>]')
        self.assertEqual(d._componentsNeedUpdating, False )
        self.assertEqual(str(d._qtrLength), '1/3')
        self.assertTrue(d._quarterLengthNeedsUpdating)
        self.assertEqual(repr(d.quarterLength), 'Fraction(1, 3)')
        self.assertEqual(str(unitSpec(d)), "(Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')")

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Duration, Tuplet, DurationUnit, convertQuarterLengthToType, TupletFixer]

if __name__ == "__main__":
    import music21
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof


