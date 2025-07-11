# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         duration.py
# Purpose:      music21 classes for representing durations
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2024 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
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
from __future__ import annotations

from collections.abc import Iterable
import contextlib
import copy
import fractions
from functools import lru_cache
import io
from math import inf, isnan
import typing as t
import unittest

from music21 import common
from music21.common.objects import SlottedObjectMixin
from music21.common.numberTools import opFrac
from music21.common.types import OffsetQL, OffsetQLIn, DocOrder
from music21 import defaults
from music21 import environment
from music21 import exceptions21
from music21 import prebase


if t.TYPE_CHECKING:
    from music21 import base
    from music21 import note
    from music21 import stream

environLocal = environment.Environment('duration')

DENOM_LIMIT = defaults.limitOffsetDenominator

POSSIBLE_DOTS_IN_TUPLETS = (0, 1)

TupletType = t.Literal['start', 'stop', 'startStop', False, None]
TupletShowOptions = t.Literal['number', 'type', 'both', None]

class DurationException(exceptions21.Music21Exception):
    pass


class TupletException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------
# duration constants and reference


# N.B.: MusicXML uses long instead of longa
typeToDuration: dict[str, float] = {
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

typeFromNumDict: dict[float, str] = {
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
    2048.0: '2048th',  # if extended, update beam.beamableDurationTypes
    0.0: 'zero',
    0.5: 'breve',
    0.25: 'longa',
    0.125: 'maxima',
    0.0625: 'duplex-maxima',
}
typeFromNumDictKeys: list[float] = sorted(list(typeFromNumDict.keys()))

ordinalTypeFromNum: list[str] = [
    'duplex-maxima',
    'maxima',
    'longa',
    'breve',
    'whole',
    'half',
    'quarter',
    'eighth',
    '16th',
    '32nd',
    '64th',
    '128th',
    '256th',
    '512th',
    '1024th',
    '2048th',
]


defaultTupletNumerators: tuple[int, ...] = (3, 5, 7, 11, 13)

extendedTupletNumerators: tuple[int, ...] = (
    3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67,
    71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139,
    149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199,
)


class QuarterLengthConversion(t.NamedTuple):
    components: tuple[DurationTuple]
    tuplet: Tuplet|None


def unitSpec(durationObjectOrObjects):
    '''
    DEPRECATED and to be removed in v10.

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
    [(3.0, 'half', 1, None, None, None),
     (1.125, 'complex', 0, None, None, None),
     (Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')]
    '''
    if isinstance(durationObjectOrObjects, list):
        ret = []
        for dO in durationObjectOrObjects:
            ret.append(unitSpec(dO))
        return ret
    else:
        dO = durationObjectOrObjects
        if (not hasattr(dO, 'tuplets')) or dO.tuplets is None or not dO.tuplets:
            return (dO.quarterLength, dO.type, dO.dots, None, None, None)
        else:
            return (dO.quarterLength,
                    dO.type,
                    dO.dots,
                    dO.tuplets[0].numberNotesActual,
                    dO.tuplets[0].numberNotesNormal,
                    dO.tuplets[0].durationNormal.type)


def nextLargerType(durType: str) -> str:
    '''
    Given a type (such as 16th or quarter), return the next larger type.

    >>> duration.nextLargerType('16th')
    'eighth'

    >>> duration.nextLargerType('whole')
    'breve'

    >>> duration.nextLargerType('duplex-maxima')
    Traceback (most recent call last):
    music21.duration.DurationException: cannot get the next larger of duplex-maxima
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException(f'cannot get the next larger of {durType}')
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 0:
        raise DurationException(f'cannot get the next larger of {durType}')
    return ordinalTypeFromNum[thisOrdinal - 1]


def nextSmallerType(durType: str) -> str:
    '''
    Given a type (such as 16th or quarter), return the next smaller type.

    >>> duration.nextSmallerType('16th')
    '32nd'
    >>> duration.nextSmallerType('whole')
    'half'
    >>> duration.nextSmallerType('1024th')
    '2048th'
    >>> duration.nextSmallerType('2048th')
    Traceback (most recent call last):
    music21.duration.DurationException: cannot get the next smaller of 2048th
    '''
    if durType not in ordinalTypeFromNum:
        raise DurationException(f'cannot get the next smaller of {durType}')
    thisOrdinal = ordinalTypeFromNum.index(durType)
    if thisOrdinal == 15:
        raise DurationException(f'cannot get the next smaller of {durType}')
    return ordinalTypeFromNum[thisOrdinal + 1]


def quarterLengthToClosestType(qLen: OffsetQLIn) -> tuple[str, bool]:
    '''
    Returns a two-unit tuple consisting of

    1. The type string ("quarter") that is smaller than or equal to the
    quarterLength of provided.

    2. Boolean, True or False, whether the conversion was exact.

    >>> duration.quarterLengthToClosestType(0.5)
    ('eighth', True)
    >>> duration.quarterLengthToClosestType(0.75)
    ('eighth', False)
    >>> duration.quarterLengthToClosestType(1.8)
    ('quarter', False)

    Some extremely close types will return True for exact conversion:

    >>> duration.quarterLengthToClosestType(2.0000000000000001)
    ('half', True)

    Very long durations are fine:

    >>> duration.quarterLengthToClosestType(129.99)
    ('duplex-maxima', False)

    Durations smaller than 2048th note raise a DurationException

    >>> qL = duration.typeToDuration['2048th']
    >>> qL
    0.001953125

    >>> qL = qL * 0.75
    >>> duration.quarterLengthToClosestType(qL)
    Traceback (most recent call last):
    music21.duration.DurationException: Cannot return types smaller than 2048th;
        qLen was: 0.00146484375
    '''
    def raise_it(qLen_inner):
        return DurationException('Cannot return types smaller than 2048th; '
                                + f'qLen was: {qLen}')

    if not qLen:
        raise raise_it(qLen)

    noteLengthType: OffsetQL
    if isinstance(qLen, fractions.Fraction):
        noteLengthType = 4 / qLen  # divides right
    else:
        noteLengthType = opFrac(4 / qLen)

    # noteLengthType could be a Fraction, but not a problem
    if noteLengthType in typeFromNumDict:  # type: ignore[index]
        return (typeFromNumDict[noteLengthType], True)  # type: ignore[index]
    else:
        lowerBound = 4 / qLen
        upperBound = 8 / qLen
        for numDict in typeFromNumDictKeys:
            if numDict == 0:
                continue
            elif lowerBound < numDict < upperBound:
                return (typeFromNumDict[numDict], False)

        if qLen > 128:
            return ('duplex-maxima', False)

        raise raise_it(qLen)


def convertQuarterLengthToType(qLen: OffsetQLIn) -> str:
    '''
    Return a type if there exists a type that is exactly equal to the
    duration of the provided quarterLength. Similar to
    quarterLengthToClosestType() but this
    function only returns exact matches.

    >>> duration.convertQuarterLengthToType(2)
    'half'
    >>> duration.convertQuarterLengthToType(0.125)
    '32nd'
    >>> duration.convertQuarterLengthToType(0.33333)
    Traceback (most recent call last):
    music21.duration.DurationException: cannot convert quarterLength 0.33333 exactly to type
    '''
    if not qLen:
        return 'zero'
    durationType, match = quarterLengthToClosestType(qLen)
    if not match:
        raise DurationException(
            f'cannot convert quarterLength {qLen} exactly to type')
    return durationType

def dottedMatch(qLen: OffsetQLIn,
                maxDots=4
                ) -> tuple[int, str]|tuple[t.Literal[False], t.Literal[False]]:
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
    for dots in range(maxDots + 1):
        # assume qLen has n dots, so find its non-dotted length
        preDottedLength = qLen / common.dotMultiplier(dots)
        try:
            durType, match = quarterLengthToClosestType(preDottedLength)
        except DurationException:
            continue
        if match:
            return (dots, durType)
    return (False, False)


def quarterLengthToNonPowerOf2Tuplet(
    qLen: OffsetQLIn
) -> tuple[Tuplet, DurationTuple]:
    '''
    Slow, last chance function that returns a tuple of a single tuplet, probably with a non
    power of 2 denominator (such as 7:6) that represents the quarterLength and the
    DurationTuple that should be used to express the note.

    This could be a double-dotted note, but also a tuplet:

    >>> duration.quarterLengthToNonPowerOf2Tuplet(7)
    (<music21.duration.Tuplet 8/7/quarter>, DurationTuple(type='breve', dots=0, quarterLength=8.0))

    >>> duration.quarterLengthToNonPowerOf2Tuplet(7/16)
    (<music21.duration.Tuplet 8/7/64th>, DurationTuple(type='eighth', dots=0, quarterLength=0.5))

    >>> duration.quarterLengthToNonPowerOf2Tuplet(7/3)
    (<music21.duration.Tuplet 12/7/16th>, DurationTuple(type='whole', dots=0, quarterLength=4.0))

    And of course:

    >>> duration.quarterLengthToNonPowerOf2Tuplet(1)
    (<music21.duration.Tuplet 1/1/quarter>,
     DurationTuple(type='quarter', dots=0, quarterLength=1.0))
    '''
    qFrac = fractions.Fraction.from_float(1 / float(qLen)).limit_denominator(DENOM_LIMIT)
    qFracOrg = qFrac
    if qFrac.numerator < qFrac.denominator:
        while qFrac.numerator < qFrac.denominator:
            qFrac = qFrac * 2
    elif qFrac.numerator > qFrac.denominator * 2:
        while qFrac.numerator > qFrac.denominator * 2:
            qFrac = qFrac / 2
    # qFrac will always be expressed in lowest terms

    closestSmallerType, unused_match = quarterLengthToClosestType(qLen / qFrac.denominator)

    tupletDuration = Duration(type=closestSmallerType)

    representativeDuration = durationTupleFromQuarterLength(qFrac / qFracOrg)

    return (Tuplet(numberNotesActual=qFrac.numerator,
                   numberNotesNormal=qFrac.denominator,
                   durationActual=tupletDuration,
                   durationNormal=tupletDuration,
                   frozen=True,
                   ), representativeDuration)


def quarterLengthToTuplet(
    qLen: OffsetQLIn,
    maxToReturn: int = 4,
    tupletNumerators=defaultTupletNumerators
) -> list[Tuplet]:
    '''
    Returns a list of possible Tuplet objects for a
    given `qLen` (quarterLength). As there may be more than one
    possible solution, the `maxToReturn` integer specifies the
    maximum number of values returned.

    Searches for numerators specified in duration.defaultTupletNumerators
    (3, 5, 7, 11, 13). Does not return dotted tuplets, nor nested tuplets.

    Note that 4:3 tuplets won't be found, but will be found as dotted notes
    by dottedMatch.


    >>> duration.quarterLengthToTuplet(0.33333333)
    [<music21.duration.Tuplet 3/2/eighth>, <music21.duration.Tuplet 3/1/quarter>]

    >>> duration.quarterLengthToTuplet(0.20)
    [<music21.duration.Tuplet 5/4/16th>,
     <music21.duration.Tuplet 5/2/eighth>,
     <music21.duration.Tuplet 5/1/quarter>]


    By specifying only 1 `maxToReturn`, a single-length list containing the
    Tuplet with the smallest type will be returned.

    >>> duration.quarterLengthToTuplet(0.3333333, 1)
    [<music21.duration.Tuplet 3/2/eighth>]

    >>> tup = duration.quarterLengthToTuplet(0.3333333, 1)[0]
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
            qLenBase = opFrac(typeValue / i)
            # try multiples of the tuplet division, from 1 to max - 1
            for m in range(1, i):
                for numberOfDots in POSSIBLE_DOTS_IN_TUPLETS:
                    tupletMultiplier = common.dotMultiplier(numberOfDots)
                    qLenCandidate = opFrac(qLenBase * m * tupletMultiplier)
                    if qLenCandidate == qLen:
                        tupletDuration = durationTupleFromTypeDots(typeKey, numberOfDots)
                        newTuplet = Tuplet(numberNotesActual=i,
                                           numberNotesNormal=m,
                                           durationActual=tupletDuration,
                                           durationNormal=tupletDuration,
                                           frozen=True,
                                           )
                        post.append(newTuplet)
                        break
            # not looking for these matches will add tuple alternative
            # representations; this could be useful
            if len(post) >= maxToReturn:
                break
        if len(post) >= maxToReturn:
            break

    return post


@lru_cache(1024)
def quarterConversion(qLen: OffsetQLIn) -> QuarterLengthConversion:
    '''
    Returns a 2-element namedtuple of (components, tuplet)

    Components is a tuple of DurationTuples (normally one) that
    add up to the qLen when multiplied by the tuplet multiplier.

    Tuplet is a single :class:`~music21.duration.Tuplet` that adjusts all components.

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

    A triplet quarter note, lasting 0.6666 qLen
    Or, a quarter that is 1/3 of a half.
    Or, a quarter that is 2/3 of a quarter.

    >>> duration.quarterConversion(2/3)
    QuarterLengthConversion(components=(DurationTuple(type='quarter', dots=0, quarterLength=1.0),),
        tuplet=<music21.duration.Tuplet 3/2/quarter>)
    >>> tup = duration.quarterConversion(2/3).tuplet
    >>> tup
    <music21.duration.Tuplet 3/2/quarter>
    >>> tup.durationActual
    DurationTuple(type='quarter', dots=0, quarterLength=1.0)


    A triplet eighth note, where 3 eights are in the place of 2.
    Or, an eighth that is 1/3 of a quarter
    Or, an eighth that is 2/3 of eighth

    >>> duration.quarterConversion(1/3)
    QuarterLengthConversion(components=(DurationTuple(type='eighth', dots=0, quarterLength=0.5),),
        tuplet=<music21.duration.Tuplet 3/2/eighth>)

    A half that is 1/3 of a whole, or a triplet half note.
    Or, a half that is 2/3 of a half

    >>> duration.quarterConversion(4/3)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=0, quarterLength=2.0),),
        tuplet=<music21.duration.Tuplet 3/2/half>)

    >>> duration.quarterConversion(1/6)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),),
        tuplet=<music21.duration.Tuplet 3/2/16th>)


    A sixteenth that is 1/5 of a quarter
    Or, a sixteenth that is 4/5ths of a 16th

    >>> duration.quarterConversion(1/5)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),),
        tuplet=<music21.duration.Tuplet 5/4/16th>)


    A 16th that is  1/7th of a quarter
    Or, a 16th that is 4/7 of a 16th

    >>> duration.quarterConversion(1/7)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),),
        tuplet=<music21.duration.Tuplet 7/4/16th>)

    A 4/7ths of a whole note, or
    A quarter that is 4/7th of a quarter

    >>> duration.quarterConversion(4/7)
    QuarterLengthConversion(components=(DurationTuple(type='quarter', dots=0, quarterLength=1.0),),
                            tuplet=<music21.duration.Tuplet 7/4/quarter>)

    If a duration is not containable in a single unit, this method
    will break off the largest type that fits within this type
    and recurse, adding as many units as necessary.

    >>> duration.quarterConversion(2.5)
    QuarterLengthConversion(components=(DurationTuple(type='half', dots=0, quarterLength=2.0),
                                        DurationTuple(type='eighth', dots=0, quarterLength=0.5)),
                            tuplet=None)


    Since tuplets apply to the entire Duration (since v2), expect some odder tuplets for unusual
    values that should probably be split generally:

    >>> duration.quarterConversion(7/3)
    QuarterLengthConversion(components=(DurationTuple(type='whole', dots=0, quarterLength=4.0),),
        tuplet=<music21.duration.Tuplet 12/7/16th>)

    Note that because this method is cached, the tuplet returned will be reused, so
    it should generally be copied before assigning.

    >>> duration.quarterConversion(1/3).tuplet is duration.quarterConversion(1/3).tuplet
    True


    This is a very close approximation:

    >>> duration.quarterConversion(0.18333333333333)
    QuarterLengthConversion(components=(DurationTuple(type='16th', dots=0, quarterLength=0.25),),
        tuplet=<music21.duration.Tuplet 15/11/256th>)

    >>> duration.quarterConversion(0.0)
    QuarterLengthConversion(components=(DurationTuple(type='zero', dots=0, quarterLength=0.0),),
        tuplet=None)


    >>> duration.quarterConversion(99.0)
    QuarterLengthConversion(components=(DurationTuple(type='inexpressible',
                                                      dots=0,
                                                      quarterLength=99.0),),
                            tuplet=None)
    '''
    # this is a performance-critical operation that has been highly optimized for speed
    # rather than legibility or logic.  Most commonly anticipated events appear first
    # then less common/slower
    try:
        #
        if qLen > 0:
            qLenDict = 4 / qLen
        else:
            qLenDict = 0
        # hashes are awesome. will catch Fraction(1, 1), 1, 1.0 etc.
        durType = typeFromNumDict[qLenDict]  # type: ignore[index]
        dt = durationTupleFromTypeDots(durType, 0)
        return QuarterLengthConversion((dt,), None)
    except KeyError:
        pass

    # Trying to quickly check is not (False, False)
    # mypy wonders if maybe durType could be True
    dots, durType = dottedMatch(qLen)  # type: ignore[assignment]
    if durType is not False:
        dt = durationTupleFromTypeDots(durType, dots)
        return QuarterLengthConversion((dt,), None)

    if qLen == 0:
        dt = durationTupleFromTypeDots('zero', 0)
        return QuarterLengthConversion((dt,), None)

    # Tuplets
    qLen = opFrac(qLen)
    # try match to type, get next lowest for next part
    try:
        closestSmallerType, unused_match = quarterLengthToClosestType(qLen)
        nextLargerType(closestSmallerType)
    except DurationException:
        # too big or too small
        return QuarterLengthConversion((DurationTuple(type='inexpressible',
                                                      dots=0,
                                                      quarterLength=qLen),), None)

    tupleCandidates = quarterLengthToTuplet(qLen, 1)
    if tupleCandidates:
        # assume that the first tuplet candidate, using the smallest type, is best
        return QuarterLengthConversion(
            (tupleCandidates[0].durationActual,),
            tupleCandidates[0]
        )

    # now we're getting into some obscure cases.
    # is it built up of many small types?
    components = [durationTupleFromTypeDots(closestSmallerType, 0)]
    # remove the largest type out there and keep going.

    qLenRemainder = opFrac(qLen - typeToDuration[closestSmallerType])
    # cannot recursively call, because tuplets are not possible at this stage.
    # environLocal.warn(['starting remainder search for qLen:', qLen,
    #    'remainder: ', qLenRemainder, 'components: ', components])
    for i in range(8):  # max 8 iterations.
        # environLocal.warn(['qLenRemainder is:', qLenRemainder])
        dots, durType = dottedMatch(qLenRemainder)
        if durType is not False:  # match!
            dt = durationTupleFromTypeDots(durType, dots)
            components.append(dt)
            return QuarterLengthConversion(tuple(components), None)
        try:
            closestSmallerType, unused_match = quarterLengthToClosestType(qLenRemainder)
        except DurationException:
            break  # already reached 2048th notes.
        qLenRemainder = qLenRemainder - typeToDuration[closestSmallerType]
        dt = durationTupleFromTypeDots(closestSmallerType, 0)
        # environLocal.warn(['appending', dt, 'leaving ', qLenRemainder, ' of ', qLen])
        components.append(dt)

    # 8 tied components was not enough.
    # last resort: put one giant tuplet over it.
    try:
        tuplet, component = quarterLengthToNonPowerOf2Tuplet(qLen)
    except DurationException:
        # Failures include 1/72
        return QuarterLengthConversion((DurationTuple(type='inexpressible',
                                                      dots=0,
                                                      quarterLength=qLen),), None)
    tuplet.frozen = True
    return QuarterLengthConversion((component,), tuplet)


def convertTypeToQuarterLength(
    dType: str,
    dots: int = 0,
    tuplets: list[Tuplet]|None = None,
    dotGroups=None
) -> OffsetQL:
    # noinspection PyShadowingNames
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

    >>> tup = duration.Tuplet(numberNotesActual=5, numberNotesNormal=4)
    >>> duration.convertTypeToQuarterLength('quarter', 0, [tup])
    Fraction(4, 5)
    >>> duration.convertTypeToQuarterLength('quarter', 1, [tup])
    Fraction(6, 5)

    >>> tup = duration.Tuplet(numberNotesActual=3, numberNotesNormal=4)
    >>> duration.convertTypeToQuarterLength('quarter', 0, [tup])
    Fraction(4, 3)

    Also can handle those rare medieval dot groups
    (such as dotted-dotted half notes that take a full measure of 9/8.
    Conceptually, these are dotted-(dotted-half) notes.  See
    trecento.trecentoCadence for more information
    ).
    >>> duration.convertTypeToQuarterLength('half', dots=1, dotGroups=[1, 1])
    4.5

    Unknown values raise `DurationException`:

    >>> duration.convertTypeToQuarterLength('minim')
    Traceback (most recent call last):
    music21.duration.DurationException: no such type (minim) available for conversion
    '''
    if dType in typeToDuration:
        durationFromType = typeToDuration[dType]
    else:
        raise DurationException(
            f'no such type ({dType}) available for conversion')

    qtrLength: OffsetQL = durationFromType

    # weird medieval notational device; rarely used.
    if dotGroups is not None and len(dotGroups) > 1:
        for innerDots in dotGroups:
            if innerDots > 0:
                qtrLength *= common.dotMultiplier(innerDots)
    else:
        qtrLength *= common.dotMultiplier(dots)

    if tuplets is not None and tuplets:
        qtrLength = opFrac(qtrLength)
        for tup in tuplets:
            qtrLength = opFrac(qtrLength * tup.tupletMultiplier())
    return qtrLength


def convertTypeToNumber(dType: str) -> float:
    '''
    Convert a duration type string (`dType`) to a numerical scalar representation that shows
    how many of that duration type fits within a whole note.

    >>> duration.convertTypeToNumber('quarter')
    4.0
    >>> duration.convertTypeToNumber('half')
    2.0
    >>> duration.convertTypeToNumber('1024th')
    1024.0
    >>> duration.convertTypeToNumber('maxima')
    0.125

    These other types give these results:

    >>> duration.convertTypeToNumber('zero')
    0.0
    >>> duration.convertTypeToNumber('complex')
    Traceback (most recent call last):
    music21.duration.DurationException: Could not determine durationNumber from complex
    '''
    dTypeFound = None
    for num, typeName in typeFromNumDict.items():
        if dType == typeName:
            # dTypeFound = int(num)  # not all of these are integers
            dTypeFound = num
            break
    if dTypeFound is None:
        raise DurationException(f'Could not determine durationNumber from {dType}')
    return dTypeFound


# -----------------------------------------------------------------------------------
class DurationTuple(t.NamedTuple):
    type: str
    dots: int
    quarterLength: OffsetQL

    def augmentOrDiminish(self, amountToScale):
        return durationTupleFromQuarterLength(self.quarterLength * amountToScale)

    @property
    def ordinal(self):
        '''
        Converts type to an ordinal number where maxima = 1 and 1024th = 14;
        whole = 4 and quarter = 6.  Based on duration.ordinalTypeFromNum

        >>> a = duration.DurationTuple('whole', 0, 4.0)
        >>> a.ordinal
        4

        >>> b = duration.DurationTuple('maxima', 0, 32.0)
        >>> b.ordinal
        1

        >>> c = duration.DurationTuple('1024th', 0, 1/256)
        >>> c.ordinal
        14
        '''
        try:
            return ordinalTypeFromNum.index(self.type)
        except ValueError:
            raise DurationException(
                f'Could not determine durationNumber from {self.type}')


_durationTupleCacheTypeDots: dict[tuple[str, int], DurationTuple] = {}
_durationTupleCacheQuarterLength: dict[OffsetQL, DurationTuple] = {}


def durationTupleFromQuarterLength(ql=1.0) -> DurationTuple:
    '''
    Returns a DurationTuple for a given quarter length
    if the ql can be expressed as a type and number of dots
    (no tuplets, no complex duration, etc.).  If it can't be expressed,
    returns an "inexpressible" DurationTuple.

    >>> dt = duration.durationTupleFromQuarterLength(3.0)
    >>> dt
    DurationTuple(type='half', dots=1, quarterLength=3.0)

    If it's not possible, we return an "inexpressible" type:

    >>> dt = duration.durationTupleFromQuarterLength(2.5)
    >>> dt
    DurationTuple(type='inexpressible', dots=0, quarterLength=2.5)
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

    Also with keyword arguments.

    >>> dt = duration.durationTupleFromTypeDots(durType='zero', dots=0)
    >>> dt
    DurationTuple(type='zero', dots=0, quarterLength=0.0)

    Unknown values raise `DurationException`:

    >>> dt = duration.durationTupleFromTypeDots(durType='minim', dots=0)
    Traceback (most recent call last):
    music21.duration.DurationException: Unknown type: minim

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
        except (KeyError, IndexError) as e:
            raise DurationException(
                f'Unknown type: {durType}'
            ) from e
        nt = DurationTuple(durType, dots, ql)
        _durationTupleCacheTypeDots[tp] = nt
        return nt


# -------------------------------------------------------------------------------
class Tuplet(prebase.ProtoM21Object):
    '''
    A tuplet object is a representation of a musical tuplet (like a triplet).
    It expresses a ratio that modifies duration values and are stored in
    Duration objects in a "tuple" (immutable list; since there can be nested
    tuplets) in the duration's .tuplets property.

    The primary representation uses two pairs of note numbers and durations.

    The first pair of note numbers and durations describes the representation
    within the tuplet, or the value presented by the context. This is called
    "actual." In a standard 8th note triplet this would be 3, eighth, meaning
    that a complete collection of this tuplet will be visually represented as
    three eighth notes.  These
    attributes are `numberNotesActual`, `durationActual`.

    The second pair of note numbers and durations describes the space that
    would have been occupied in a normal context. This is called "normal." In a
    standard 8th note triplet this would be 2, eighth, meaning that a complete
    collection of notes under this tuplet will occupy the space of two eighth notes.
    These attributes are
    `numberNotesNormal`, `durationNormal`.

    If duration values are not provided then `durationActual` and `durationNormal` are
    left as None -- meaning that it is unspecified what the duration that completes the
    tuplet is.  And this tuplet just represents a Ratio.
    PRIOR TO v4 `durationActual` and `durationNormal` were assumed to be eighths.

    If only one duration, either `durationActual` or `durationNormal`, is
    provided, both are set to the same value.

    Note that this is a duration modifier, or a generator of ratios to scale
    quarterLength values in Duration objects.

    >>> myTup = duration.Tuplet(numberNotesActual=5, numberNotesNormal=4)
    >>> print(myTup.tupletMultiplier())
    4/5

    We know that it is 5 in the place of 4, but 5 what in the place of 4 what?

    >>> myTup.durationActual is None
    True
    >>> myTup
    <music21.duration.Tuplet 5/4>

    But we can change that:

    >>> myTup.setDurationType('eighth')
    >>> myTup.durationActual
    DurationTuple(type='eighth', dots=0, quarterLength=0.5)
    >>> myTup
    <music21.duration.Tuplet 5/4/eighth>


    In this case, the tupletMultiplier is a float because it can be expressed
    as a binary number:

    >>> myTup2 = duration.Tuplet(8, 5)
    >>> tm = myTup2.tupletMultiplier()
    >>> tm
    0.625

    Here, six sixteenth notes occupy the space of four sixteenth notes.

    >>> myTup2 = duration.Tuplet(6, 4, '16th')
    >>> print(myTup2.durationActual.type)
    16th
    >>> print(myTup2.durationNormal.type)
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
    music21.duration.TupletException: A frozen tuplet (or one attached to a duration)
        has immutable length.

    >>> myHalf = duration.Duration('half')
    >>> myHalf.appendTuplet(myTup2)
    >>> myTup2.tupletActual = [5, 4]
    Traceback (most recent call last):
    music21.duration.TupletException: A frozen tuplet (or one attached to a duration)
        has immutable length.

    Note that if you want to create a note with a simple Tuplet attached to it,
    you can just change the quarterLength of the note:

    >>> myNote = note.Note('C#4')
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
    def __init__(
        self,
        numberNotesActual: int = 3,
        numberNotesNormal: int = 2,
        durationActual: DurationTuple|Duration|str|tuple[str, int]|None = None,
        durationNormal: DurationTuple|Duration|str|tuple[str, int]|None = None,
        *,
        tupletId: int = 0,
        nestedLevel: int = 1,
        type: TupletType = None,  # pylint: disable=redefined-builtin
        bracket: t.Literal[True, False, 'slur'] = True,
        placement: t.Literal['above', 'below'] = 'above',
        tupletActualShow: TupletShowOptions = 'number',
        tupletNormalShow: TupletShowOptions = None,
        frozen: bool = False,
        **keywords
    ):
        self.frozen = False
        # environLocal.printDebug(['creating Tuplet instance'])

        self._durationNormal: DurationTuple|None = None
        self._durationActual: DurationTuple|None = None

        # necessary for some complex tuplets, interrupted, for instance
        self.tupletId = tupletId
        self.nestedLevel = nestedLevel

        # actual is the count of notes that happen in this space
        # this is not the previous/expected duration of notes that happen
        self.numberNotesActual: int = numberNotesActual

        if durationActual is not None and durationNormal is None:
            durationNormal = durationActual
        elif durationActual is None and durationNormal is not None:
            durationActual = durationNormal

        # this stores a durationTuple
        if durationActual is not None:
            if isinstance(durationActual, str):
                self.durationActual = durationTupleFromTypeDots(durationActual, 0)
            elif isinstance(durationActual, tuple):
                self.durationActual = durationTupleFromTypeDots(durationActual[0],
                                                                durationActual[1])
            else:
                # type ignore until https://github.com/python/mypy/issues/3004 resolved
                self.durationActual = durationActual  # type: ignore

        # # crashes mypy-0.982 -- fixed in 0.999 dev.
        # match durationActual:
        #     case None:
        #         pass
        #     case str(durAct):
        #         self.durationActual = durationTupleFromTypeDots(durAct, 0)
        #     case (str(durActType), int(dots)):
        #         self.durationActual = durationTupleFromTypeDots(durActType, dots)
        #     case _:
        #         # type ignore until https://github.com/python/mypy/issues/3004 resolved
        #         self.durationActual = durationActual  # type: ignore


        # normal is the space that would normally be occupied by the tuplet span
        self.numberNotesNormal: int = numberNotesNormal

        if durationNormal is not None:
            if isinstance(durationNormal, str):
                self.durationNormal = durationTupleFromTypeDots(durationNormal, 0)
            elif isinstance(durationNormal, tuple):
                self.durationNormal = durationTupleFromTypeDots(durationNormal[0],
                                                                durationNormal[1])
            else:
                # type ignore until https://github.com/python/mypy/issues/3004 resolved
                self.durationNormal = durationNormal  # type: ignore

        # # crashes mypy-0.982 -- fixed in 0.999 dev.
        # match durationNormal:
        #     case None:
        #         pass
        #     case str(durNor):
        #         self.durationNormal = durationTupleFromTypeDots(durNor, 0)
        #     case(str(durNorType), int(dots)):
        #         self.durationNormal = durationTupleFromTypeDots(durNorType, dots)
        #     case _:
        #         # type ignore until https://github.com/python/mypy/issues/3004 resolved
        #         self.durationNormal = durationNormal  # type: ignore

        # Type is 'start', 'stop', 'startStop', False or None: determines whether to start or stop
        # the bracket/group drawing
        # startStop is not used in musicxml, it will be encoded
        # as two notations (start + stop) in musicxml
        # type of None means undetermined,
        # False means definitely neither start nor stop (not yet used)
        self.type: TupletType = type
        # True or False or 'slur'
        self.bracket: t.Literal[True, False, 'slur'] = bracket
        # 'above' or 'below' (TODO: 'by-context')
        self.placement: t.Literal['above', 'below'] = placement
        # could be 'number', 'type', 'both', or None
        self.tupletActualShow: TupletShowOptions = tupletActualShow
        # for ratios. Options are same as above.
        self.tupletNormalShow: TupletShowOptions = tupletNormalShow

        # set frozen after all inits are done
        self.frozen = frozen
        # this attribute is not yet used anywhere
        # self.nestedInside = ''  # could be a tuplet object

    # MAGIC METHODS #

    def __eq__(self, other) -> bool:
        '''
        Two Tuplets are equal if their numbers are equal and durations are equal.

        Visual details (type, bracket, placement, tupletActualShow, etc.) do
        not matter.

        >>> triplet1 = duration.Tuplet(3, 2)
        >>> triplet2 = duration.Tuplet(3, 2)
        >>> triplet1 == triplet2
        True
        >>> quadruplet = duration.Tuplet(4, 3)
        >>> triplet1 == quadruplet
        False
        >>> triplet3 = duration.Tuplet(3, 2, 'half')
        >>> triplet1 == triplet3
        False
        '''
        if not isinstance(other, Tuplet):
            return NotImplemented
        for attr in ('numberNotesActual', 'numberNotesNormal',
                     'durationActual', 'durationNormal'):
            myAttr = getattr(self, attr, None)
            otherAttr = getattr(other, attr, None)
            if myAttr != otherAttr:
                return False
        return True


    # PRIVATE METHODS #

    def _reprInternal(self):
        base_rep = f'{self.numberNotesActual!r}/{self.numberNotesNormal!r}'
        if self.durationNormal is not None:
            base_rep += f'/{self.durationNormal.type}'
        return base_rep

    def _checkFrozen(self):
        if self.frozen is True:
            raise TupletException(
                'A frozen tuplet (or one attached to a duration) has immutable length.')

    # PUBLIC METHODS #
    def augmentOrDiminish(self, amountToScale: int|float):
        '''
        Given a number greater than zero,
        multiplies the current quarterLength of the
        duration by the number and resets the components
        for the duration (by default).  Or if inPlace is
        set to False, returns a new duration that has
        the new length.

        # TODO: add inPlace setting.

        >>> a = duration.Tuplet()
        >>> a.setRatio(6, 2)
        >>> a.tupletMultiplier()
        Fraction(1, 3)
        >>> a.setDurationType('eighth')
        >>> a.durationActual
        DurationTuple(type='eighth', dots=0, quarterLength=0.5)

        >>> c = a.augmentOrDiminish(0.5)
        >>> c.durationActual
        DurationTuple(type='16th', dots=0, quarterLength=0.25)

        >>> c.tupletMultiplier()
        Fraction(1, 3)

        Raises ValueError if `amountToScale` is negative.

        >>> a.augmentOrDiminish(-1)
        Traceback (most recent call last):
        ValueError: amountToScale must be greater than zero
        '''
        if not amountToScale > 0:
            raise ValueError('amountToScale must be greater than zero')
        # TODO: scale the triplet in the same manner as Durations

        post = copy.deepcopy(self)
        post.frozen = False

        # duration units scale
        if post.durationActual is not None:
            post.durationActual = (
                post.durationActual.augmentOrDiminish(  # type: ignore[attr-defined]
                    amountToScale)
            )
        if post.durationNormal is not None:
            post.durationNormal = (
                post.durationNormal.augmentOrDiminish(  # type: ignore[attr-defined]
                    amountToScale)
            )

        # ratios stay the same
        # self.numberNotesActual = actual
        # self.numberNotesNormal = normal
        return post

    def setDurationType(
        self,
        durType: str|int|float|fractions.Fraction,
        dots: int = 0,
    ) -> None:
        '''
        Set both durationActual and durationNormal from either a string type or
        a quarterLength.  optional dots can add dots to a string type (or I suppose
        a quarterLength.)

        >>> a = duration.Tuplet()
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.totalTupletLength()
        1.0
        >>> a.setDurationType('half')
        >>> a.durationNormal
        DurationTuple(type='half', dots=0, quarterLength=2.0)
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.totalTupletLength()
        4.0
        >>> a.setDurationType('half', dots=1)
        >>> a.durationNormal
        DurationTuple(type='half', dots=1, quarterLength=3.0)
        >>> a.totalTupletLength()
        6.0

        >>> a.setDurationType(2.0)
        >>> a.totalTupletLength()
        4.0
        >>> a.setDurationType(4.0)
        >>> a.totalTupletLength()
        8.0

        '''
        self._checkFrozen()
        if common.isNum(durType) and not isinstance(durType, str):
            durType = convertQuarterLengthToType(durType)

        self.durationActual = durationTupleFromTypeDots(durType, dots)
        self.durationNormal = durationTupleFromTypeDots(durType, dots)

    def setRatio(self, actual: int, normal: int) -> None:
        '''
        Set the ratio of actual divisions to represented in normal divisions.
        A triplet is 3 actual in the time of 2 normal.

        >>> a = duration.Tuplet()
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.setRatio(6, 2)
        >>> a.numberNotesActual
        6
        >>> a.numberNotesNormal
        2
        >>> a.tupletMultiplier()
        Fraction(1, 3)

        One way of expressing 6/4-ish triplets without numbers:

        >>> a = duration.Tuplet()
        >>> a.setRatio(3, 1)
        >>> a.durationActual = duration.durationTupleFromTypeDots('quarter', 0)
        >>> a.durationNormal = duration.durationTupleFromTypeDots('half', 0)
        >>> a.tupletMultiplier()
        Fraction(2, 3)
        >>> a.totalTupletLength()
        2.0
        '''
        self._checkFrozen()
        self.numberNotesActual = actual
        self.numberNotesNormal = normal

    def totalTupletLength(self) -> OffsetQL:
        '''
        The total duration in quarter length of the tuplet as defined,
        assuming that enough notes existed to fill all entire tuplet as defined.

        For instance, 3 quarters in the place of 2 quarters = 2.0
        5 half notes in the place of a 2 dotted half notes = 6.0
        (In the end it's only the denominator that matters)

        If durationActual or durationNormal are None, then they will be
        assumed to be eighth notes (for the basic 3:2 eighth-note triplet)

        >>> a = duration.Tuplet()
        >>> a.totalTupletLength()
        1.0

        >>> a.numberNotesActual = 3
        >>> a.numberNotesNormal = 2
        >>> a.setDurationType('half')
        >>> a.totalTupletLength()
        4.0

        Let's make it five halfs in the place of four:

        >>> a.setRatio(5, 4)
        >>> a.setDurationType('half')
        >>> a.totalTupletLength()
        8.0

        Now five halfs in the place of two whole notes (same thing):

        >>> a.setRatio(5, 2)
        >>> a.totalTupletLength()
        4.0
        >>> a.durationNormal = duration.durationTupleFromTypeDots('whole', 0)
        >>> a.totalTupletLength()
        8.0
        '''
        n = self.numberNotesNormal
        if self.durationNormal is not None:
            durationNormalQuarterLength = self.durationNormal.quarterLength
        else:
            durationNormalQuarterLength = 0.5  # eighth notes
        return opFrac(n * durationNormalQuarterLength)

    def tupletMultiplier(self) -> OffsetQL:
        '''
        Get a Fraction() by which to scale the duration that
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
        if self.durationActual is not None:
            lengthActual = self.durationActual.quarterLength
        else:
            lengthActual = 0.5  # default
        ttl = self.totalTupletLength()
        return opFrac(ttl / (lengthActual * self.numberNotesActual))

    # PUBLIC PROPERTIES #
    @property
    def durationActual(self) -> DurationTuple|None:
        '''
        durationActual is a DurationTuple that represents the notes that are
        actually present and counted in a tuplet.  For instance, in a 7
        dotted-eighth in the place of 2 double-dotted quarter notes tuplet,
        the duration actual would be this:

        >>> d = duration.Tuplet(7, 2)
        >>> print(d.durationActual)
        None
        >>> d.durationActual = duration.Duration('eighth', dots=1)

        Notice that the Duration object gets converted to a DurationTuple.

        >>> d.durationActual
        DurationTuple(type='eighth', dots=1, quarterLength=0.75)

        >>> d.durationActual = 'quarter'
        >>> d.durationActual
        DurationTuple(type='quarter', dots=0, quarterLength=1.0)
        '''
        return self._durationActual

    @durationActual.setter
    def durationActual(self, dA: DurationTuple|Duration|str|None):
        self._checkFrozen()

        if isinstance(dA, DurationTuple) or dA is None:
            self._durationActual = dA
        elif isinstance(dA, Duration):
            if len(dA.components) > 1:
                dA = copy.deepcopy(dA)
                dA.consolidate()
            self._durationActual = DurationTuple(dA.type, dA.dots, dA.quarterLength)
        elif isinstance(dA, str):
            self._durationActual = durationTupleFromTypeDots(dA, dots=0)

    @property
    def durationNormal(self) -> DurationTuple|None:
        '''
        durationNormal is a DurationTuple that represents the notes that
        would be present in the space normally (if there were no tuplets).  For instance, in a 7
        dotted-eighth in the place of 2 double-dotted quarter notes tuplet,
        the durationNormal would be:

        >>> d = duration.Tuplet(7, 2)
        >>> print(d.durationNormal)
        None
        >>> d.durationNormal = duration.Duration('quarter', dots=2)

        Notice that the Duration object gets converted to a DurationTuple:

        >>> d.durationNormal
        DurationTuple(type='quarter', dots=2, quarterLength=1.75)

        >>> d.durationNormal = 'half'
        >>> d.durationNormal
        DurationTuple(type='half', dots=0, quarterLength=2.0)
        '''
        return self._durationNormal

    @durationNormal.setter
    def durationNormal(self, dN: DurationTuple|Duration|str|None):
        self._checkFrozen()
        if isinstance(dN, DurationTuple) or dN is None:
            self._durationNormal = dN
        elif isinstance(dN, Duration):
            if len(dN.components) > 1:
                dN = copy.deepcopy(dN)
                dN.consolidate()
            self._durationNormal = DurationTuple(dN.type, dN.dots, dN.quarterLength)
        elif isinstance(dN, str):
            self._durationNormal = durationTupleFromTypeDots(dN, dots=0)

    @property
    def fullName(self):
        '''
        Return the most complete representation of this tuplet in a readable
        form.

        >>> tup = duration.Tuplet(numberNotesActual=5, numberNotesNormal=2)
        >>> tup.fullName
        'Quintuplet'

        >>> tup = duration.Tuplet(numberNotesActual=3, numberNotesNormal=2)
        >>> tup.fullName
        'Triplet'

        >>> tup = duration.Tuplet(numberNotesActual=17, numberNotesNormal=14)
        >>> tup.fullName
        'Tuplet of 17/14ths'
        '''
        # actual is what is presented to viewer
        numActual = self.numberNotesActual
        numNormal = self.numberNotesNormal
        # dur = self.durationActual

        if numActual == 3 and numNormal == 2:
            return 'Triplet'
        elif numActual == 5 and numNormal in (4, 2):
            return 'Quintuplet'
        elif numActual == 6 and numNormal == 4:
            return 'Sextuplet'
        elif numActual == 7 and numNormal == 4:
            return 'Septuplet'
        ordStr = common.ordinalAbbreviation(numNormal, plural=True)
        return f'Tuplet of {numActual}/{numNormal}{ordStr}'

    @property
    def tupletActual(self):
        '''
        Get or set a two element list of number notes actual and duration
        actual.
        '''
        return [self.numberNotesActual, self.durationActual]

    @tupletActual.setter
    def tupletActual(self, tupList):
        self._checkFrozen()
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
        self._checkFrozen()
        self.numberNotesNormal, self.durationNormal = tupList


# ------------------------------------------------------------------------------
class Duration(prebase.ProtoM21Object, SlottedObjectMixin):
    '''
    Durations are one of the most important objects in music21. A Duration
    represents a span of musical time measurable in terms of quarter notes (or
    in advanced usage other units). For instance, "57 quarter notes" or "dotted
    half tied to quintuplet sixteenth note" or simply "quarter note."

    A Duration object is made of one or more immutable DurationTuple objects stored on the
    `components` list. A Duration created by setting `quarterLength` sets the attribute
    :attr:`expressionIsInferred` to True, which indicates that callers
    (such as :meth:`~music21.stream.makeNotation.splitElementsToCompleteTuplets`)
    can express this Duration using another combination of components that sums to the
    `quarterLength`. Otherwise, `expressionIsInferred` is set to False, indicating that
    components are not allowed to mutate.

    Multiple DurationTuples in a single Duration may be used to express tied
    notes, or may be used to split duration across barlines or beam groups.
    Some Duration objects are not expressible as a single notation unit.

    Duration objects are not Music21Objects.

    If a single argument is passed to Duration() and it is a string, then it is
    assumed to be a type, such as 'half', 'eighth', or '16th', etc.  If that
    single argument is a number then it is assumed to be a quarterLength (2 for
    half notes, 0.5 for eighth notes, 0.75 for dotted eighth notes, 0.333333333
    for a triplet eighth, etc.).  If one or more named arguments are passed
    then the Duration() is configured according to those arguments.  Supported
    arguments are 'type', 'dots', 'quarterLength', or 'components'.

    Example 1: a triplet eighth configured by quarterLength:

    >>> d = duration.Duration(0.333333333)
    >>> d.type
    'eighth'

    >>> d.tuplets
    (<music21.duration.Tuplet 3/2/eighth>,)

    Example 2: A Duration made up of multiple
    :class:`music21.duration.DurationTuple` objects automatically configured by
    the specified quarterLength.

    >>> d2 = duration.Duration(0.625)
    >>> d2.type
    'complex'

    >>> d2.components
    (DurationTuple(type='eighth', dots=0, quarterLength=0.5),
     DurationTuple(type='32nd', dots=0, quarterLength=0.125))

    >>> d2.expressionIsInferred
    True

    Example 3: A Duration configured by keywords.

    >>> d3 = duration.Duration(type='half', dots=2)
    >>> d3.quarterLength
    3.5
    >>> d3.expressionIsInferred
    False
    '''

    # CLASS VARIABLES #

    isGrace = False  # grace is stored as separate class.

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
        'expressionIsInferred',
        'client',
    )

    _DOC_ATTR = {
        'expressionIsInferred': '''
             Boolean indicating whether this duration was created from a
             number rather than a type and thus can be changed to another
             expression.  For instance the duration of 0.5 is generally
             an eighth note, but in the middle of a triplet group might be
             better written as a dotted-eighth triplet.  If expressionIsInferred
             is True then `music21` can change it according to complex.  If
             False, then the type, dots, and tuplets are considered immutable.

             >>> d = duration.Duration(0.5)
             >>> d.expressionIsInferred
             True

             >>> d = duration.Duration('eighth')
             >>> d.expressionIsInferred
             False
             ''',
        'client': '''
            A duration's "client" is the object that holds this
            duration as a property.  It is informed whenever the duration changes.

            >>> n = note.Note('C#5', type='whole')
            >>> d = n.duration
            >>> d.client is n
            True
            ''',
    }

    # INITIALIZER #

    def __init__(self,
                 typeOrDuration: str|OffsetQLIn|DurationTuple|None = None,
                 /,
                 *,
                 type: str|None = None,  # pylint: disable=redefined-builtin
                 dots: int|None = 0,
                 quarterLength: OffsetQLIn|None = None,
                 durationTuple: DurationTuple|None = None,
                 components: Iterable[DurationTuple]|None = None,
                 client: base.Music21Object|None = None,
                 **keywords):
        # First positional argument is assumed to be type string or a quarterLength.
        # no need for super() on ProtoM21 or SlottedObjectMixin

        # store a reference to the object that has this duration object as a property
        # Will assign at end, so as not to informClient during creation.
        self.client: base.Music21Object|None = None

        self._componentsNeedUpdating = False
        self._quarterLengthNeedsUpdating = False
        self._typeNeedsUpdating = False

        self._unlinkedType: str|None = None
        self._dotGroups: tuple[int, ...] = (0,)
        self._tuplets: tuple['Tuplet', ...] = ()  # an empty tuple
        self._qtrLength: OffsetQL = 0.0

        # DurationTuples go here
        self._components: tuple[DurationTuple, ...] = ()

        # defer updating until necessary
        self._quarterLengthNeedsUpdating = False
        self._linked = True

        self.expressionIsInferred = False
        if typeOrDuration is not None:
            if isinstance(typeOrDuration, (int, float, fractions.Fraction)
                          ) and quarterLength is None:
                quarterLength = typeOrDuration
            elif isinstance(typeOrDuration, str) and type is None:
                type = typeOrDuration
            elif isinstance(typeOrDuration, DurationTuple) and durationTuple is None:
                durationTuple = typeOrDuration
            else:
                raise TypeError(
                    f'Cannot parse argument {typeOrDuration} or conflicts with keywords'
                )

        if durationTuple is not None:
            self.addDurationTuple(durationTuple, _skipInform=True)

        if components is not None:
            self.components = t.cast(tuple[DurationTuple, ...], components)
            # this is set in _setComponents
            # self._quarterLengthNeedsUpdating = True

        if type is not None:
            nt = durationTupleFromTypeDots(type, dots)
            self.addDurationTuple(nt, _skipInform=True)
        # permit as keyword so can be passed from notes
        elif quarterLength is not None:
            self.quarterLength = quarterLength
            self.expressionIsInferred = True

        # now assign the client so further changes are informed.
        self.client = client


    # SPECIAL METHODS #
    def __eq__(self, other):
        '''
        Two durations are the same if their type, dots, tuplets, and
        quarterLength are all the same.

        >>> aDur = duration.Duration('quarter')
        >>> bDur = duration.Duration('16th')
        >>> cDur = duration.Duration('16th')
        >>> aDur == bDur
        False
        >>> aDur != bDur
        True

        >>> cDur == bDur
        True

        >>> dDur = duration.Duration(0.0)
        >>> eDur = duration.Duration(0.0)
        >>> dDur == eDur
        True

        >>> tupDur1 = duration.Duration(2 / 3)
        >>> tupDur2 = duration.Duration(2 / 3)
        >>> tupDur1 == tupDur2
        True

        >>> graceDur1 = tupDur1.getGraceDuration()
        >>> graceDur1 == tupDur1
        False
        >>> graceDur2 = tupDur2.getGraceDuration()
        >>> graceDur1 == graceDur2
        True

        Link status must be the same:

        >>> tupDur1.linked = False
        >>> tupDur1 == tupDur2
        False
        '''
        if type(other) is not type(self):
            return False

        if self.isComplex != other.isComplex:
            return False
        if len(self.components) != len(other.components):
            return False

        if not self.components:
            return True

        if self.type != other.type:
            return False
        if self.dots != other.dots:
            return False
        if self.tuplets != other.tuplets:
            return False
        if self.quarterLength != other.quarterLength:
            return False
        if self.linked != other.linked:
            return False

        return True

    def _reprInternal(self):
        if self.linked is True:
            return str(self.quarterLength)
        else:
            return f'unlinked type:{self.type} quarterLength:{self.quarterLength}'

    def __deepcopy__(self, memo):
        '''
        Don't copy client when creating
        '''
        if self._componentsNeedUpdating:
            return common.defaultDeepcopy(self, memo, ignoreAttributes={'client'})

        if (len(self._components) == 1
                and self._dotGroups == (0,)
                and self._linked is True
                and not self._tuplets):  # 99% of notes
            # ignore all but components
            return self.__class__(durationTuple=self._components[0])
        elif (not self._components
              and self._dotGroups == (0,)
              and not self._tuplets
              and self._linked is True):
            # ignore all
            return self.__class__()
        else:
            return common.defaultDeepcopy(self, memo, ignoreAttributes={'client'})

    # PRIVATE METHODS #

    def _updateComponents(self):
        '''
        This method will re-construct components and thus is not good if the
        components are already configured as you like
        '''
        # this update will not be necessary
        self._quarterLengthNeedsUpdating = False
        if self.linked and self.expressionIsInferred:
            qlc = quarterConversion(self._qtrLength)
            self.components = tuple(qlc.components)
            if qlc.tuplet is not None:
                self.tuplets = (copy.deepcopy(qlc.tuplet),)
        self._componentsNeedUpdating = False

    # PUBLIC METHODS #
    def _getLinked(self) -> bool:
        '''
        Gets or sets the `.linked` property -- if linked (default) then type, dots, tuplets are
        always coherent with quarterLength.  If not, then they are separate.

        >>> d = duration.Duration(0.5)
        >>> d.linked
        True

        Linked durations change other values when one changes:

        >>> d.type = '16th'
        >>> d.quarterLength
        0.25

        Unlinked values do not:

        >>> d.linked = False
        >>> d.type = 'half'
        >>> d.quarterLength
        0.25
        '''
        return self._linked

    def _setLinked(self, value: bool):
        if value not in (True, False):
            raise TypeError(f'Linked can only be True or False, not {value}')
        if self._quarterLengthNeedsUpdating:
            self._updateQuarterLength()
        if value is False and self._linked is True:
            self._unlinkedType = self.type
        elif value is True and self._linked is False:
            self._quarterLengthNeedsUpdating = True
            self._componentsNeedUpdating = True

        self._linked = value

    linked = property(_getLinked, _setLinked)

    def addDurationTuple(self,
                         dur: DurationTuple|Duration|str|OffsetQLIn,
                         *,
                         _skipInform=False):
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
        if self._componentsNeedUpdating:
            self._updateComponents()

        if isinstance(dur, DurationTuple):
            if isnan(dur.quarterLength):
                raise ValueError('Invalid quarterLength for DurationTuple: nan')
            self._components = self._components + (dur,)
        elif isinstance(dur, Duration):  # it's a Duration object
            for c in dur.components:
                self._components = self._components + (c,)
        else:  # it's a number that may produce more than one component
            for c in Duration(dur).components:
                self._components = self._components + (c,)

        if self.linked:
            self._quarterLengthNeedsUpdating = True

        if not _skipInform:
            self.informClient()

    def appendTuplet(self, newTuplet: Tuplet) -> None:
        '''
        Adds a new Tuplet to a Duration, sets the Tuplet's .frozen state to True,
        and then informs the client (Note) that the duration has changed.

        >>> tup = duration.Tuplet(3, 2)
        >>> d = duration.Duration(1.0)
        >>> d.appendTuplet(tup)
        >>> d.quarterLength
        Fraction(2, 3)
        >>> t2 = duration.Tuplet(5, 4)
        >>> d.appendTuplet(t2)
        >>> d.quarterLength
        Fraction(8, 15)
        >>> tup.frozen
        True
        '''
        newTuplet.frozen = True
        self.tuplets = self._tuplets + (newTuplet,)

    def augmentOrDiminish(self, amountToScale, retainComponents=False):
        '''
        Given a number greater than zero, creates a new Duration object
        after
        multiplying the current quarterLength of the
        duration by the number and resets the components
        for the duration (by default).

        Returns a new duration that has
        the new length.

        >>> aDur = duration.Duration()
        >>> aDur.quarterLength = 1.5  # dotted quarter
        >>> cDur = aDur.augmentOrDiminish(2)
        >>> cDur.quarterLength
        3.0
        >>> cDur.type
        'half'
        >>> cDur.dots
        1

        `aDur` is not changed:

        >>> aDur
        <music21.duration.Duration 1.5>

        A complex duration that cannot be expressed as a single notehead (component)

        >>> bDur = duration.Duration()
        >>> bDur.quarterLength = 2.125  # requires components
        >>> bDur.quarterLength
        2.125
        >>> len(bDur.components)
        2
        >>> bDur.components
        (DurationTuple(type='half', dots=0, quarterLength=2.0),
         DurationTuple(type='32nd', dots=0, quarterLength=0.125))


        By default, when augmenting or diminishing, we will delete any
        unusual components or tuplets:

        >>> dDur = duration.Duration(1.5)
        >>> dDur.appendTuplet(duration.Tuplet(3, 2))
        >>> dDur
        <music21.duration.Duration 1.0>
        >>> dDur.dots
        1
        >>> dDur.tuplets
        (<music21.duration.Tuplet 3/2>,)

        >>> eDur = dDur.augmentOrDiminish(2)
        >>> eDur
        <music21.duration.Duration 2.0>
        >>> eDur.dots
        0
        >>> eDur.tuplets
        ()

        >>> eRetain = dDur.augmentOrDiminish(2, retainComponents=True)
        >>> eRetain
        <music21.duration.Duration 2.0>
        >>> eRetain.dots
        1
        >>> eRetain.tuplets
        (<music21.duration.Tuplet 3/2>,)

        >>> fDur = duration.Duration(1.0)
        >>> fDur.addDurationTuple(duration.DurationTuple('quarter', 0, 1.0))
        >>> fDur
        <music21.duration.Duration 2.0>
        >>> fDur.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0),
         DurationTuple(type='quarter', dots=0, quarterLength=1.0))

        >>> gDur = fDur.augmentOrDiminish(0.5)
        >>> gDur.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0),)

        >>> gRetain = fDur.augmentOrDiminish(0.5, retainComponents=True)
        >>> gRetain.components
        (DurationTuple(type='eighth', dots=0, quarterLength=0.5),
         DurationTuple(type='eighth', dots=0, quarterLength=0.5))

        Negative values raise ValueError:

        >>> fDur.augmentOrDiminish(-1)
        Traceback (most recent call last):
        ValueError: amountToScale must be greater than zero
        '''
        if not amountToScale > 0:
            raise ValueError('amountToScale must be greater than zero')

        post = copy.deepcopy(self)

        if retainComponents:
            newComponents = []
            for d in post.components:
                newComponents.append(d.augmentOrDiminish(amountToScale))
            post.components = newComponents
            self._typeNeedsUpdating = True
            self._quarterLengthNeedsUpdating = True
        else:
            post.tuplets = ()
            post.quarterLength = self.quarterLength * amountToScale

        return post

    def clear(self) -> None:
        '''
        Permit all components to be removed.
        This is needed for resetting to zero duration.

        >>> a = duration.Duration()
        >>> a.quarterLength = 6
        >>> a.type
        'whole'
        >>> a.components
        (DurationTuple(type='whole', dots=1, quarterLength=6.0),)

        >>> a.clear()

        >>> a.dots
        0
        >>> a.components
        ()
        >>> a.type
        'zero'
        >>> a.quarterLength
        0.0
        '''
        self._dotGroups = (0,)
        self._components = ()
        self._componentsNeedUpdating = False
        self._quarterLengthNeedsUpdating = True
        self.informClient()

    def componentIndexAtQtrPosition(self, quarterPosition):
        '''
        returns the index number of the duration component sounding at
        the given quarter position.

        Note that for 0 and the last value, the object is returned.


        >>> components = []
        >>> components.append(duration.Duration('quarter'))
        >>> components.append(duration.Duration('quarter'))
        >>> components.append(duration.Duration('quarter'))

        >>> a = duration.Duration()
        >>> a.components = components
        >>> a.quarterLength
        3.0
        >>> a.componentIndexAtQtrPosition(0.5)
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

        Currently sometimes returns the component itself.  Changing in v7.
        '''
        quarterPosition = opFrac(quarterPosition)

        if not self.components:
            raise DurationException(
                'Need components to run getComponentIndexAtQtrPosition')
        if quarterPosition > self.quarterLength:
            raise ValueError(
                'position is after the end of the duration')

        if quarterPosition < 0:
            # values might wrap around from the other side
            raise ValueError(
                'position is before the start of the duration')

        # it seems very odd that these return objects
        # while the method name suggests indices will be returned
        if quarterPosition == 0:
            return self.components[0]
        elif quarterPosition == self.quarterLength:
            return self.components[-1]

        currentPosition = 0.0
        for i, component in enumerate(self.components):
            currentPosition = opFrac(currentPosition + component.quarterLength)
            if currentPosition > quarterPosition:
                return i
        raise DurationException(
            'Could not match quarterLength within an index.')

    def componentStartTime(self, componentIndex: int) -> float:
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
        >>> a.componentStartTime(3)
        Traceback (most recent call last):
        IndexError: invalid component index value 3 submitted;
                    value must be an integer between 0 and 2
        '''
        if not (0 <= componentIndex < len(self.components)):
            raise IndexError(
                f'invalid component index value {componentIndex} '
                + f'submitted; value must be an integer between 0 and {len(self.components) - 1}')
        components = self.components[:componentIndex]
        return float(sum([c.quarterLength for c in components]))


    def consolidate(self):
        '''
        Given a Duration with multiple components, consolidate into a single
        Duration. This can only be based on quarterLength; this is
        destructive: information is lost from components.

        This cannot be done for all Durations, as DurationTuples cannot express all durations

        >>> a = duration.Duration(1)
        >>> a.addDurationTuple(duration.DurationTuple('half', 0, 2.0))
        >>> a.addDurationTuple(duration.DurationTuple('quarter', 0, 1.0))
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

        >>> a = duration.Duration(1)
        >>> a.addDurationTuple(duration.DurationTuple('half', 0, 2.0))
        >>> a.addDurationTuple(duration.DurationTuple('half', 0, 2.0))
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
        >>> a.components
        (DurationTuple(type='inexpressible', dots=0, quarterLength=5.0),)

        It gains a type!

        >>> a.type
        'inexpressible'

        For an 'inexpressible' duration, the opposite of consolidate is
        to set the duration's quarterLength to itself.  It won't necessarily
        return to the original components, but it will usually
        create something that can be notated.

        >>> a.quarterLength = a.quarterLength
        >>> a.type
        'complex'
        >>> a.components
        (DurationTuple(type='whole', dots=0, quarterLength=4.0),
         DurationTuple(type='quarter', dots=0, quarterLength=1.0))
        '''
        if len(self.components) == 1:
            pass  # nothing to be done
        else:
            dur = durationTupleFromQuarterLength(self.quarterLengthNoTuplets)
            # if quarter length is not notatable, will automatically unlink
            # some notations will not properly unlink, and raise an error
            self.components = [dur]

    def getGraceDuration(
        self,
        appoggiatura=False
    ) -> GraceDuration|AppoggiaturaDuration:
        # noinspection PyShadowingNames
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
        <music21.duration.GraceDuration unlinked type:complex quarterLength:0.0>
        >>> gd.quarterLength
        0.0
        >>> gd.components
        (DurationTuple(type='quarter', dots=0, quarterLength=0.0),
         DurationTuple(type='16th', dots=0, quarterLength=0.0))

        `d` is unchanged.

        >>> d.quarterLength
        1.25
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()

        # create grace duration
        gd: GraceDuration
        if appoggiatura is True:
            gd = AppoggiaturaDuration()
        else:
            gd = GraceDuration()

        newComponents = []
        new_type = self.type
        if new_type == 'zero':
            new_type = 'eighth'  # now that it is not a grace, it needs a type.

        for c in self.components:
            c_type = c.type
            if c_type == 'zero':
                c_type = 'eighth'
            newComponents.append(DurationTuple(c.type, c.dots, 0.0))
        gd.components = tuple(newComponents)  # set new components
        gd.linked = False
        gd.type = new_type
        gd.quarterLength = 0.0
        return gd

    def informClient(self) -> bool:
        '''
        A method that tells the client that something has changed.

        Call `informSites({'changedAttribute': 'duration', 'quarterLength': quarterLength})`
        on any call that changes the quarterLength, so that the client can make a change.

        Returns False if there was no need to inform the client (like nothing has changed)
        or if `.client` is None.  Otherwise returns True.
        '''
        if self._quarterLengthNeedsUpdating is True:
            old_qtrLength = self._qtrLength
            self._updateQuarterLength()
            if self._qtrLength == old_qtrLength:
                return False
        cl = self.client
        if cl is None:
            return False
        cl.informSites({'changedAttribute': 'duration',
                        'quarterLength': self._qtrLength})
        return True

    def sliceComponentAtPosition(self, quarterPosition):
        # noinspection PyShadowingNames
        '''
        Given a quarter position within a component, divide that
        component into two components.

        >>> d = duration.Duration()
        >>> d.clear()  # need to remove default
        >>> components = []

        >>> d.addDurationTuple(duration.Duration('quarter'))
        >>> d.addDurationTuple(duration.Duration('quarter'))
        >>> d.addDurationTuple(duration.Duration('quarter'))
        >>> d.quarterLength
        3.0
        >>> d.sliceComponentAtPosition(0.5)
        >>> d.quarterLength
        3.0
        >>> len(d.components)
        4
        >>> d.components[0].type
        'eighth'
        >>> d.components[1].type
        'eighth'
        >>> d.components[2].type
        'quarter'
        '''
        # this may return a Duration object; we are not sure
        sliceIndex = self.componentIndexAtQtrPosition(quarterPosition)

        # get durObj that qPos is within
        if common.isNum(sliceIndex):
            durObjSlice = self.components[sliceIndex]
        else:  # assume that we got an object
            durObjSlice = sliceIndex

        # this will not work if componentIndexAtQtrPosition returned an obj
        # get the start pos in ql of this dur obj
        durationStartTime = self.componentStartTime(sliceIndex)
        # find difference between desired split and start pos of this dur obj
        # this is the left side dur
        slicePoint = quarterPosition - durationStartTime
        # this is the right side dur
        remainder = durObjSlice.quarterLength - slicePoint

        if remainder == 0 or slicePoint == 0:  # nothing to be done
            # this might not be an error
            raise DurationException(
                'no slice is possible at this quarter position')

        d1 = durationTupleFromQuarterLength(slicePoint)
        d2 = durationTupleFromQuarterLength(remainder)

        components = self.components[:sliceIndex] + (d1, d2) + self._components[sliceIndex + 1:]
        self._components = components
        # lengths should be the same as it was before
        self._updateQuarterLength()

    def currentComponents(self):
        '''
        Advanced Method:

        returns the current components WITHOUT running the component updater.

        Needed by some internal methods.  Components are made on the fly.

        >>> d = duration.Duration(1.25)
        >>> d.currentComponents()
        ()

        Like in quantum physics, an observation affects the state:

        >>> d.type
        'complex'
        >>> d.currentComponents()
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0),
         DurationTuple(type='16th', dots=0, quarterLength=0.25))


        Generally, just look at `.components`

        >>> d = duration.Duration(1.25)
        >>> d.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0),
         DurationTuple(type='16th', dots=0, quarterLength=0.25))
        '''
        return self._components

    def splitDotGroups(self, *, inPlace=False):
        '''
        splits a dotGroup-duration (of 1 component) into a new duration of two
        components.  Returns a new duration

        Probably does not handle properly tuplets of dot-groups.
        Never seen one, so probably okay.

        >>> d1 = duration.Duration(type='half')
        >>> d1.dotGroups = (1, 1)
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
        >>> n2.duration.dotGroups = (1, 1)
        >>> n2.quarterLength
        2.25
        >>> #_DOCS_SHOW n2.show()  # generates a dotted-quarter tied to dotted-eighth
        >>> n2.duration.splitDotGroups(inPlace=True)
        >>> n2.duration.dotGroups
        (1,)
        >>> n2.duration.components
        (DurationTuple(type='quarter', dots=1, quarterLength=1.5),
         DurationTuple(type='eighth', dots=1, quarterLength=0.75))

        >>> n2 = note.Note()
        >>> n2.duration.type = 'quarter'
        >>> n2.duration.dotGroups = (1, 1, 1)
        >>> n2.quarterLength
        3.375
        >>> dSplit = n2.duration.splitDotGroups()
        >>> dSplit.quarterLength
        3.375
        >>> dSplit.components
        (DurationTuple(type='quarter', dots=1, quarterLength=1.5),
         DurationTuple(type='eighth', dots=1, quarterLength=0.75),
         DurationTuple(type='eighth', dots=1, quarterLength=0.75),
         DurationTuple(type='16th', dots=1, quarterLength=0.375))

        Does NOT handle tuplets etc.
        '''
        tupleType = self.type
        dg = self.dotGroups
        if not inPlace:
            d = copy.deepcopy(self)
        else:
            d = self

        d.clear()

        d.addDurationTuple(durationTupleFromTypeDots(tupleType, dg[0]))
        for i in range(1, len(dg)):
            for existingComponent in list(d.components):
                d.addDurationTuple(
                    durationTupleFromTypeDots(nextSmallerType(existingComponent.type),
                                              existingComponent.dots)
                )

        if not inPlace:
            return d

    def _updateQuarterLength(self):
        '''
        Look to components and determine quarter length.

        * Changed in v7: made private.  And faster
        '''
        if self.linked is False:
            return

        if self._dotGroups == (0,) and not self.tuplets and len(self.components) == 1:
            # make sure to do common tasks fast:
            self._qtrLength = self.components[0].quarterLength
        else:
            self._qtrLength = opFrac(self.quarterLengthNoTuplets * self.aggregateTupletMultiplier())
            for dots in self._dotGroups:
                if dots != 0:
                    self._qtrLength = opFrac(self._qtrLength * common.dotMultiplier(dots))

        self._quarterLengthNeedsUpdating = False

    # PUBLIC PROPERTIES #
    @property
    def components(self) -> tuple[DurationTuple, ...]:
        '''
        Returns or sets a tuple of the component DurationTuples of this
        Duration object

        >>> d = duration.Duration(1.0)
        >>> d.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0),)

        Tuplets do not have the tuplet in their components.

        >>> d = duration.Duration(1/3)
        >>> d.components
        (DurationTuple(type='eighth', dots=0, quarterLength=0.5),)


        With a complex duration it becomes clearer why multiple components are needed.
        Here is a duration that cannot be expressed as a single note.

        >>> d = duration.Duration(1.25)
        >>> d.type
        'complex'
        >>> d.components
        (DurationTuple(type='quarter', dots=0, quarterLength=1.0),
         DurationTuple(type='16th', dots=0, quarterLength=0.25))

        But it can be expressed another way and will output in that way in MusicXML
        and other readers:

        >>> component0 = duration.DurationTuple(type='eighth', dots=0, quarterLength=0.5)
        >>> component1 = duration.DurationTuple(type='eighth', dots=1, quarterLength=0.75)
        >>> d.components = [component0, component1]

        It is allowed but not advised to set components that do not add up
        to the current (pre-tuplet) quarterLength.  In which case the quarterLength
        will be adjusted:

        >>> d.components = [component0]
        >>> d
        <music21.duration.Duration 0.5>
        >>> d.type
        'eighth'
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        return self._components

    @components.setter
    def components(self, value: Iterable[DurationTuple]):
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
    def dotGroups(self) -> tuple[int, ...]:
        '''
        Dot groups are a convenience for transcribing medieval music.
        They represent dotted-dotted notes (written one above another).
        For instance a half note with dotGroups = (1, 1) represents a dotted half note that
        is itself dotted.  Worth 9 eighth notes (dotted-half tied to dotted-quarter).  It
        is not the same as a double-dotted half note, which is only worth 7 eighth notes.

        >>> a = duration.Duration()
        >>> a.type = 'half'
        >>> a.dotGroups
        (0,)
        >>> a.dots = 1

        >>> a.dotGroups = (1, 1)
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
    def dotGroups(self, value: tuple[int, ...]):
        if not isinstance(value, tuple):
            raise TypeError('only tuple dotGroups values can be used with this method.')
        # removes dots from all components
        componentsGenerator = (
            durationTupleFromTypeDots(component.type, 0) for component in self._components
        )
        self._components = tuple(componentsGenerator)

        self._dotGroups = value
        self._quarterLengthNeedsUpdating = True

    @property
    def dots(self) -> int:
        '''
        Returns or sets the number of dots in the Duration
        if it is a simple Duration.

        For returning only the number of dots on the first component is returned for
        complex durations. (Previously it could return None
        if it was not a simple duration which led to some
        terribly difficult to find errors.)

        >>> a = duration.Duration()
        >>> a.type = 'quarter'
        >>> a.dots = 1
        >>> a.quarterLength
        1.5
        >>> a.dots = 2
        >>> a.quarterLength
        1.75

        If a duration is complex then setting dots has the effect of
        setting the number of dots to `value` on every component.

        >>> DT = duration.durationTupleFromTypeDots
        >>> complexDuration = duration.Duration()
        >>> complexDuration.addDurationTuple(DT('half', 0))
        >>> complexDuration.addDurationTuple(DT('eighth', 2))
        >>> complexDuration.type
        'complex'
        >>> complexDuration.quarterLength
        2.875

        In a complex duration, the number of dots comes from the first component:

        >>> complexDuration.dots
        0

        But if set, applies to all components:

        >>> complexDuration.dots = 1
        >>> complexDuration.components
        (DurationTuple(type='half', dots=1, quarterLength=3.0),
         DurationTuple(type='eighth', dots=1, quarterLength=0.75))
        >>> complexDuration.quarterLength
        3.75

        Dots can go pretty high.

        >>> d = duration.Duration('half')
        >>> d.quarterLength
        2.0
        >>> d.dots = 5
        >>> d.quarterLength
        3.9375
        >>> d.dots = 10
        >>> d.quarterLength
        3.998046875

        Infinite dots gives an Easter egg:

        >>> from math import inf
        >>> d.type = 'half'
        >>> d.dots = inf
        >>> d.quarterLength
        4.0
        >>> d.dots
        0
        >>> d.type
        'whole'
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
    def dots(self, value: int):
        if self._componentsNeedUpdating:
            self._updateComponents()
        if not common.isNum(value):
            raise TypeError('only numeric dot values can be used with this method.')

        # easter egg
        if value == inf:
            self.type = nextLargerType(self.type)
            self.dots = 0
            return

        components = list(self._components)
        for i, dt in enumerate(self._components):
            components[i] = durationTupleFromTypeDots(dt.type, value)
        self._components = tuple(components)
        self._quarterLengthNeedsUpdating = True
        if self.linked is True:
            self.expressionIsInferred = False
        self.informClient()

    @property
    def fullName(self) -> str:
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
        'Quarter Septuplet (4/7 QL)'

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
            tupletStr = ''

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
                dotStr = f'{dots}-Times Dotted'
            else:
                dotStr = ''

            msg = []
            typeStr = c.type
            if dots >= 2 or (typeStr not in ('longa', 'maxima')):
                if dotStr is not None:
                    msg.append(f'{dotStr} ')
            else:
                if dots == 0:
                    msg.append('Imperfect ')
                elif dots == 1:
                    msg.append('Perfect ')
            if typeStr[0] in ('1', '2', '3', '5', '6'):
                pass  # do nothing with capitalization
            else:
                typeStr = typeStr.title()
            if typeStr.lower() == 'complex':
                pass
            else:
                msg.append(f'{typeStr} ')

            if tupletStr != '':
                msg.append(f'{tupletStr} ')
            if tupletStr != '' or dots >= 3 or typeStr.lower() == 'complex':
                qlStr = common.mixedNumeral(self.quarterLength)
                msg.append(f'({qlStr} QL)')
            totalMsg.append(''.join(msg).strip())

        if not self.components:
            totalMsg.append('Zero Duration ')

        outMsg = ''
        if len(totalMsg) > 1:
            outMsg = ' tied to '.join(totalMsg)
        else:
            outMsg = totalMsg[0]

        if len(self.components) != 1:
            qlStr = common.mixedNumeral(self.quarterLength)
            outMsg += f' ({qlStr} total QL)'

        return outMsg

    @property
    def isComplex(self) -> bool:
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
        >>> cDur.quarterLength = 0.25
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
    def ordinal(self) -> int|str|None:
        '''
        Get the ordinal value of the Duration, where whole is 4,
        half is 5, etc.

        >>> d = duration.Duration()
        >>> d.quarterLength = 2.0
        >>> d.ordinal
        5
        >>> d.type = '16th'
        >>> d.ordinal
        8

        Complex values have an ordinal of the string 'complex'.  This might
        change to NaN in a later version.

        >>> d.quarterLength = 2.5
        >>> d.ordinal
        'complex'

        Zero durations have an ordinal of None

        >>> d2 = duration.Duration(0.0)
        >>> print(d2.ordinal)
        None
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
    def quarterLengthNoTuplets(self) -> float:
        '''
        Returns the quarter length of the duration without taking into account triplets.

        Does not cache.

        >>> d = duration.Duration(1/3)
        >>> d.quarterLengthNoTuplets
        0.5
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()

        # tested, does return 0 if no components
        tot = 0.0
        for c in self._components:
            tot += c.quarterLength
        return tot

    def _getQuarterLength(self) -> OffsetQL:
        if self._quarterLengthNeedsUpdating:
            self._updateQuarterLength()
        return self._qtrLength

    def _setQuarterLength(self, value: OffsetQLIn):
        if self.linked is False:
            self._qtrLength = value
        elif (self._qtrLength != value
                or self._componentsNeedUpdating  # skip a type update for next type check
                or self.type == 'inexpressible'):
            value = opFrac(value)
            if value == 0.0 and self.linked is True:
                self.clear()
            self._qtrLength = value
            self.expressionIsInferred = True
            self._componentsNeedUpdating = True
            self._quarterLengthNeedsUpdating = False

            self.informClient()

    quarterLength = property(_getQuarterLength, _setQuarterLength, doc='''
        Returns the quarter note length or Sets the quarter note length to
        the specified value. May be expressed as a float or Fraction.

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

        Note that integer values of quarter lengths get
        silently converted to floats (internally opFracs):

        >>> b = duration.Duration()
        >>> b.quarterLength = 5
        >>> b.quarterLength
        5.0
        >>> b.type  # complex because 5qL cannot be expressed as a single note.
        'complex'

        Float values will be converted to fractions if they are inexpressible exactly
        as floats:

        >>> b = duration.Duration()
        >>> b.quarterLength = 1/3
        >>> b.quarterLength
        Fraction(1, 3)
        ''')

    @property
    def tuplets(self) -> tuple[Tuplet, ...]:
        '''
        Return a tuple of Tuplet objects.
        Setting tuplets will inform the client (Note) that the duration has changed.
        '''
        if self._componentsNeedUpdating:
            self._updateComponents()
        return self._tuplets

    @tuplets.setter
    def tuplets(self, tupletTuple: Iterable[Tuplet]):
        # environLocal.printDebug(['assigning tuplets in Duration', tupletTuple])
        self._tuplets = tuple(tupletTuple)
        self._quarterLengthNeedsUpdating = True
        self.informClient()

    def aggregateTupletMultiplier(self) -> OffsetQL:
        '''
        Returns the multiple of all the tuplet multipliers as an opFrac.

        This method is needed for MusicXML time-modification among other
        places.

        No tuplets:

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
        if not self.tuplets:
            # common cases should be fast.
            return 1.0

        currentMultiplier = 1.0
        for thisTuplet in self.tuplets:
            currentMultiplier *= thisTuplet.tupletMultiplier()
        return common.opFrac(currentMultiplier)

    # PUBLIC PROPERTIES #
    @property
    def type(self) -> str:
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
            if self._unlinkedType is None:  # pragma: no cover
                raise DurationException(
                    'linked property setter failed to set _unlinkedType, please open a bug report'
                )
            return self._unlinkedType
        elif len(self.components) == 1:
            return self.components[0].type
        elif len(self.components) > 1:
            return 'complex'
        else:  # there may be components and still a zero type
            return 'zero'

    @type.setter
    def type(self, value: str):
        # need to check that type is valid
        if value not in ordinalTypeFromNum and value not in ('inexpressible', 'complex'):
            raise ValueError(f'no such type exists: {value}')

        if self.linked is True:
            nt = durationTupleFromTypeDots(value, self.dots)
            self.components = (nt,)
            self._quarterLengthNeedsUpdating = True
            self.expressionIsInferred = False
            self.informClient()

        else:
            self._unlinkedType = value


class FrozenDuration(common.objects.FrozenObject, Duration):
    '''
    A FrozenDuration is one that must have all of its arguments specified
    at the time of construction.  After that, it is immutable, like a Tuple
    and thus can be shared across different objects (like in MeterTerminals)
    or used as a hash.

    >>> fd = duration.FrozenDuration(type='half', dots=2)
    >>> fd.quarterLength
    3.5
    >>> fd.dots = 1
    Traceback (most recent call last):
    TypeError: This FrozenDuration instance is immutable.

    FrozenDurations can be used as set/dict keys with stability.

    >>> {fd}
    {<music21.duration.FrozenDuration 3.5>}

    Copying a FrozenDuration returns the original, so it is super fast.

    >>> import copy
    >>> copy.deepcopy(fd) is fd
    True
    '''
    __slots__ = ()

    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self._updateComponents()
        self._updateQuarterLength()

    def __deepcopy__(self, memo=None):
        '''
        Immutable objects return themselves
        '''
        return self

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

    >>> gd = duration.GraceDuration(0.25)
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
    # be overridden to provide consistent behavior

    # CLASS VARIABLES #

    # TODO: What does 'amount of time' mean here?
    _DOC_ATTR: dict[str, str] = {
        'stealTimePrevious': '''
                Float number from 0.0 to 1.0, or None (default) for the proportion
                of the previous duration to steal from the previous note.''',
        'stealTimeFollowing': '''
                Float number from 0.0 to 1.0 or None (default) for the proportion
                of the following duration to steal from the following note.'''
    }

    isGrace = True

    __slots__ = (
        '_slash',
        'stealTimePrevious',
        'stealTimeFollowing',
        '_makeTime',
    )
    # INITIALIZER #

    def __init__(self,
                 typeOrDuration: str|OffsetQLIn|DurationTuple|None = None,
                 **keywords):
        super().__init__(typeOrDuration, **keywords)
        # update components to derive types; this sets ql, but this
        # will later be removed
        if self._componentsNeedUpdating:
            self._updateComponents()
        self.linked = False
        self.quarterLength = 0.0
        newComponents = []
        for c in self.components:
            newComponents.append(DurationTuple(c.type, c.dots, 0.0))
        self.components = tuple(newComponents)  # set new components

        # make time is encoded in musicxml as divisions; here it can
        # be encoded as a duration; but should it be the duration suggested by the grace?
        self._makeTime = False
        self._slash = None
        self.slash = True  # can be True, False, or None; make None go to True?
        # values are unit interval percentages
        self.stealTimePrevious: float|None = None
        self.stealTimeFollowing: float|None = None


    # PUBLIC PROPERTIES #
    @property
    def makeTime(self):
        '''
        True, False, or None (=unknown) whether the grace note should occupy time
        in performance. Default False. Currently not used in generated playback.

        TODO: allow a duration object or number for duration.
        '''
        return self._makeTime

    @makeTime.setter
    def makeTime(self, expr: t.Literal[True, False, None]):
        if expr not in (True, False, None):
            raise ValueError('expr must be True, False, or None')
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
        if expr not in (True, False, None):
            raise ValueError('expr must be True, False, or None')
        self._slash = bool(expr)


class AppoggiaturaDuration(GraceDuration):
    '''
    Renamed in v6 to correct spelling.
    '''
    # CLASS VARIABLES #

    __slots__ = ()

    # INITIALIZER #

    def __init__(self,
                 typeOrDuration: str|OffsetQLIn|DurationTuple|None = None,
                 **keywords):
        super().__init__(typeOrDuration, **keywords)
        self.slash = False  # can be True, False, or None; make None go to True?
        self.makeTime = True

# class AppoggiaturaStartDuration(Duration):
#     pass
#
# class AppoggiaturaStopDuration(Duration):
#     pass


class TupletFixer:
    '''
    The TupletFixer object takes in a flat stream and tries to fix the
    brackets and time modification values of the tuplet so that they
    reflect proper beaming, etc.  It does not alter the quarterLength
    of any notes.

    See :meth:`~music21.duration.TupletFixer.findTupletGroups` and
    :meth:`~music21.duration.TupletFixer.fixBrokenTupletDuration` for
    demonstrations.
    '''
    def __init__(self, streamIn: stream.Stream|None = None):
        self.streamIn: stream.Stream|None = streamIn
        self.allTupletGroups: list[list[note.GeneralNote]] = []

    def setStream(self, streamIn: stream.Stream) -> None:
        '''
        Define a stream to work on and reset all temporary variables.
        '''
        self.streamIn = streamIn
        self.allTupletGroups = []

    def findTupletGroups(self, incorporateGroupings: bool = False) -> list[list[note.GeneralNote]]:
        # noinspection PyShadowingNames
        '''
        Finds all tuplets in the stream and puts them into groups.

        If incorporateGroupings is True, then a tuplet.type="stop"
        ends a tuplet group even if the next note is a tuplet.

        This demonstration has three groups of tuplets, two sets of 8th note
        tuplets and one of 16ths:

        >>> c = converter.parse(
        ...    'tinynotation: 4/4 trip{c8 d e} f4 trip{c#8 d# e#} g8 trip{c-16 d- e-}',
        ...    makeNotation=False)
        >>> tf = duration.TupletFixer(c)  # no need to flatten this stream
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
        ...    n.pitch.ps = 60 + i
        ...    n.duration.quarterLength = 1/3
        ...    if i % 3 == 2:
        ...        n.duration.tuplets[0].type = 'stop'
        ...    s.append(n)
        >>> tf = duration.TupletFixer(s)
        >>> tupletGroups = tf.findTupletGroups(incorporateGroupings=True)
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
        if self.streamIn is None:
            raise ValueError('Call setStream(Stream) before running.')

        self.allTupletGroups = []
        currentTupletGroup: list[note.GeneralNote] = []
        tupletActive = False
        for n in self.streamIn.notesAndRests:
            if not n.duration.tuplets:  # most common case first
                if tupletActive is True:
                    self.allTupletGroups.append(currentTupletGroup)
                    currentTupletGroup = []
                    tupletActive = False
                continue
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

    def fixBrokenTupletDuration(self, tupletGroup: list[note.GeneralNote]) -> None:
        # noinspection PyShadowingNames
        r'''
        Tries to fix cases like triplet quarter followed by triplet
        eighth to be a coherent tuplet.

        Requires a tuplet group from `findTupletGroups()` or TupletFixer.allTupletGroups.
        Note: this works on a single tupletGroup while `findTupletGroups()`
        returns a list of groups.

        >>> s = stream.Stream()

        >>> n1 = note.Note('C')
        >>> n1.duration.quarterLength = 2/3
        >>> n1.duration.quarterLength
        Fraction(2, 3)
        >>> s.append(n1)
        >>> n2 = note.Note('D')
        >>> n2.duration.quarterLength = 1/3
        >>> n2.duration.quarterLength
        Fraction(1, 3)
        >>> s.append(n2)

        Here are the current tuplets for the two notes:

        >>> n1.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/quarter>
        >>> n2.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/eighth>

        Notice how the first note is waiting for 3 triplet quarters to
        complete itself.  But it could be 2/3 of a quarter note divided into
        eighth note triplets.  TupletFixer will work on this.

        It takes in a flattened stream, like this one:

        >>> tf = duration.TupletFixer(s)

        Find the tuplet groups.  Returning a list of one group, which has
        two notes in it:

        >>> tupletGroups = tf.findTupletGroups()
        >>> tupletGroups
        [[<music21.note.Note C>, <music21.note.Note D>]]

        Now fix that single group:

        >>> tg0 = tupletGroups[0]
        >>> [n.duration.tuplets[0].type for n in tg0]
        [None, None]

        >>> tf.fixBrokenTupletDuration(tg0)

        Now the first quarter-note triplet knows that its group
        will be complete after the next note:

        >>> n1.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/eighth>
        >>> n1.duration.quarterLength
        Fraction(2, 3)
        >>> n2.duration.tuplets[0]
        <music21.duration.Tuplet 3/2/eighth>

        Note that the tuplet type is not affected by this call:

        >>> [n.duration.tuplets[0].type for n in tg0]
        [None, None]

        To do that, call :func:`~music21.stream.makeNotation.makeTupletBrackets`
        on the flattened stream:

        >>> stream.makeNotation.makeTupletBrackets(s, inPlace=True)
        >>> [n.duration.tuplets[0].type for n in tg0]
        ['start', 'stop']


        More complex example, from a piece by Josquin:

        >>> humdrumExcerpt = '**kern *M3/1 3.c 6d 3e 3f 3d 3%2g 3e 3f#'
        >>> humdrumLines = '\n'.join(humdrumExcerpt.split())

        There is a side format of humdrum that the Josquin Research Project uses
        for long notes like the 3%2.

        >>> humdrum.spineParser.flavors['JRP'] = True

        Since Humdrum parsing is going to apply TupletFixer, we will temporarily
        disable it:

        >>> saved_fixed_broken = duration.TupletFixer.fixBrokenTupletDuration
        >>> duration.TupletFixer.fixBrokenTupletDuration = lambda x,y: None

        >>> s = converter.parse(humdrumLines, format='humdrum')

        >>> m1 = s.parts.first().measure(1)
        >>> m1.show('text', addEndTimes=True)
        {0.0 - 0.0} <music21.meter.TimeSignature 3/1>
        {0.0 - 2.0} <music21.note.Note C>
        {2.0 - 2.6667} <music21.note.Note D>
        {2.6667 - 4.0} <music21.note.Note E>
        {4.0 - 5.3333} <music21.note.Note F>
        {5.3333 - 6.6667} <music21.note.Note D>
        {6.6667 - 9.3333} <music21.note.Note G>
        {9.3333 - 10.6667} <music21.note.Note E>
        {10.6667 - 12.0} <music21.note.Note F#>

        >>> duration.TupletFixer.fixBrokenTupletDuration = saved_fixed_broken
        >>> tf = duration.TupletFixer(m1)
        >>> tupletGroups = tf.findTupletGroups(incorporateGroupings=True)
        >>> tupletGroups
        [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>],
         [<music21.note.Note F>, <music21.note.Note D>, <music21.note.Note G>,
          <music21.note.Note E>, <music21.note.Note F#>]]

        There's a problem with the last group: it contains 5 notes and the
        third note is twice as long as the others, so none of them form a coherent
        triplet.

        >>> [n.duration.tuplets[0] for n in tupletGroups[1]]
        [<music21.duration.Tuplet 3/2/half>, <music21.duration.Tuplet 3/2/half>,
         <music21.duration.Tuplet 3/2/whole>,
         <music21.duration.Tuplet 3/2/half>, <music21.duration.Tuplet 3/2/half>]
        >>> [n.duration.tuplets[0].type for n in tupletGroups[1]]
        ['start', None, None, None, 'stop']


        Fix the last broken tuplet group.

        >>> tf.fixBrokenTupletDuration(tupletGroups[1])
        >>> [n.duration.tuplets[0] for n in tupletGroups[1]]
        [<music21.duration.Tuplet 3/2/whole>, <music21.duration.Tuplet 3/2/whole>,
         <music21.duration.Tuplet 3/2/whole>,
         <music21.duration.Tuplet 3/2/whole>, <music21.duration.Tuplet 3/2/whole>]

        Note that the changes appear in the notes in the Stream as well.

        >>> m1.last().duration.tuplets[0]
        <music21.duration.Tuplet 3/2/whole>

        Again, TupletFixer is automatically called when parsing from Humdrum.
        (MusicXML specifies its tuplet groups explicitly.) But you may need it
        when building up a stream from scratch in your own projects.
        '''
        SMALL_SENTINEL = 1000
        LARGE_SENTINEL = -1

        if not tupletGroup:
            return
        firstTup = tupletGroup[0].duration.tuplets[0]
        totalTupletDuration = opFrac(firstTup.totalTupletLength())
        currentTupletDuration = 0.0
        smallestTupletTypeOrdinal: int = SMALL_SENTINEL
        largestTupletTypeOrdinal: int = LARGE_SENTINEL

        for n in tupletGroup:
            currentTupletDuration = opFrac(currentTupletDuration + n.duration.quarterLength)
            thisTup = n.duration.tuplets[0]
            tupDurationActual = thisTup.durationActual
            if t.TYPE_CHECKING:
                assert tupDurationActual is not None

            thisTupType = tupDurationActual.type
            thisTupTypeOrdinal = ordinalTypeFromNum.index(thisTupType)

            if smallestTupletTypeOrdinal == SMALL_SENTINEL:
                smallestTupletTypeOrdinal = thisTupTypeOrdinal
            elif thisTupTypeOrdinal > smallestTupletTypeOrdinal:
                smallestTupletTypeOrdinal = thisTupTypeOrdinal

            if largestTupletTypeOrdinal == LARGE_SENTINEL:
                largestTupletTypeOrdinal = thisTupTypeOrdinal
            elif thisTupTypeOrdinal < largestTupletTypeOrdinal:
                largestTupletTypeOrdinal = thisTupTypeOrdinal

        if currentTupletDuration == totalTupletDuration:
            return

        excessRatio = opFrac(currentTupletDuration / totalTupletDuration)
        inverseExcessRatio = opFrac(1 / excessRatio)

        if excessRatio == int(excessRatio):  # divide tuplets into smaller
            largestTupletType = ordinalTypeFromNum[largestTupletTypeOrdinal]

            for n in tupletGroup:
                normalDots = 0
                n.duration.tuplets[0].frozen = False  # bad
                if n.duration.tuplets[0].durationNormal is not None:
                    normalDots = n.duration.tuplets[0].durationNormal.dots
                n.duration.tuplets[0].durationNormal = durationTupleFromTypeDots(
                    largestTupletType, normalDots)
                actualDots = 0
                if n.duration.tuplets[0].durationActual is not None:
                    actualDots = n.duration.tuplets[0].durationActual.dots
                n.duration.tuplets[0].durationActual = durationTupleFromTypeDots(
                    largestTupletType, actualDots)
                n.duration.tuplets[0].frozen = True
                n.duration.informClient()

        elif inverseExcessRatio == int(inverseExcessRatio):  # redefine tuplets by GCD
            smallestTupletType = ordinalTypeFromNum[smallestTupletTypeOrdinal]
            for n in tupletGroup:
                normalDots = 0
                n.duration.tuplets[0].frozen = False  # bad
                if n.duration.tuplets[0].durationNormal is not None:
                    normalDots = n.duration.tuplets[0].durationNormal.dots
                # TODO: this should be frozen!
                durTuple = durationTupleFromTypeDots(smallestTupletType, normalDots)
                n.duration.tuplets[0].durationNormal = durTuple

                actualDots = 0
                if n.duration.tuplets[0].durationActual is not None:
                    actualDots = n.duration.tuplets[0].durationActual.dots
                durTuple = durationTupleFromTypeDots(smallestTupletType,
                                                     actualDots)
                n.duration.tuplets[0].durationActual = durTuple
                n.duration.tuplets[0].frozen = True
                n.duration.informClient()
        # else: pass

# -------------------------------------------------------------------------------


class TestExternal(unittest.TestCase):
    show = True

    def testSingle(self):
        from music21 import note
        a = Duration()
        a.quarterLength = 2.66666
        n = note.Note()
        n.duration = a
        if self.show:
            n.show()

    def testBasic(self):
        import random
        from music21 import stream
        from music21 import note

        a = stream.Stream()

        for i in range(30):
            ql = random.choice([1, 2, 3, 4, 5]) + random.choice([0, 0.25, 0.5, 0.75])
            # w/ random.choice([0, 0.33333, 0.666666] gets an error
            n = note.Note()
            b = Duration()
            b.quarterLength = ql
            n.duration = b
            a.append(n)

        if self.show:
            a.show()


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())

    def testTuple(self):
        # create a tuplet with 5 dotted eighths in the place of 3 double-dotted
        # eighths
        dur1 = Duration()
        dur1.type = 'eighth'
        dur1.dots = 1

        dur2 = Duration()
        dur2.type = 'eighth'
        dur2.dots = 2

        tup1 = Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur2]

        self.assertEqual(tup1.totalTupletLength(), 2.625)

        # create a new dotted quarter and apply the tuplet to it
        dur3 = Duration()
        dur3.type = 'quarter'
        dur3.dots = 1
        dur3.tuplets = (tup1,)
        self.assertEqual(dur3.quarterLength, fractions.Fraction(21, 20))

        # create a tuplet with 3 sixteenths in the place of 2 sixteenths
        tup2 = Tuplet()
        dur4 = Duration()
        dur4.type = '16th'
        tup2.tupletActual = [3, dur4]
        tup2.tupletNormal = [2, dur4]

        self.assertEqual(tup2.totalTupletLength(), 0.5)
        self.assertEqual(tup2.tupletMultiplier(), fractions.Fraction(2, 3))

        dur3.tuplets = (tup1, tup2)
        self.assertEqual(dur3.quarterLength, opFrac(7 / 10))

        myTuplet = Tuplet()
        self.assertEqual(myTuplet.tupletMultiplier(), opFrac(2 / 3))
        myTuplet.tupletActual = [5, durationTupleFromTypeDots('eighth', 0)]
        self.assertEqual(myTuplet.tupletMultiplier(), opFrac(2 / 5))

    def testTupletTypeComplete(self):
        '''
        Test setting of tuplet type when durations sum to expected completion
        '''
        # default tuplets group into threes when possible
        from music21 import note  # only Notes/Rests/Chords can have tuplets, not music21Objects
        from music21 import stream
        test, match = ([0.333333] * 3 + [0.1666666] * 6,
                       ['start', None, 'stop', 'start', None, 'stop', 'start', None, 'stop'])
        inputTuplets = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            inputTuplets.append(d)

        inputTupletStream = stream.Stream()
        for dur in inputTuplets:
            m21Obj = note.Note(duration=dur)
            inputTupletStream.append(m21Obj)

        stream.makeNotation.makeTupletBrackets(inputTupletStream, inPlace=True)
        output = []
        for d in inputTuplets:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)

    def testTupletTypeComplete2(self):
        from music21 import note
        from music21 import stream

        tup6 = Duration()
        tup6.quarterLength = 0.16666666
        tup6.tuplets[0].numberNotesActual = 6
        tup6.tuplets[0].numberNotesNormal = 4

        tup5 = Duration()
        tup5.quarterLength = 0.2  # default is 5 in the space of 4 16th

        inputTuplets = [
            copy.deepcopy(tup6), copy.deepcopy(tup6), copy.deepcopy(tup6),
            copy.deepcopy(tup6), copy.deepcopy(tup6), copy.deepcopy(tup6),
            copy.deepcopy(tup5), copy.deepcopy(tup5), copy.deepcopy(tup5),
            copy.deepcopy(tup5), copy.deepcopy(tup5),
        ]

        inputTupletStream = stream.Stream()
        for dur in inputTuplets:
            m21Obj = note.Note(duration=dur)
            inputTupletStream.append(m21Obj)

        match = ['start', None, None, None, None, 'stop',
                 'start', None, None, None, 'stop']

        stream.makeNotation.makeTupletBrackets(inputTupletStream, inPlace=True)
        output = []
        for d in inputTuplets:
            output.append(d.tuplets[0].type)
        self.assertEqual(output, match)

    def testTupletTypeIncomplete(self):
        '''
        Test setting of tuplet type when durations do not sum to expected
        completion.
        '''
        from music21 import note
        from music21 import stream
        # the current match results here are a good compromise
        # for a difficult situation.

        # this is close to 1/3 and 1/6 but not exact and that's part of the test.
        test, match = ([0.333333] * 2 + [0.1666666] * 5,
                       ['start', None, None, 'stop', 'start', None, 'stop']
                       )
        inputDurations = []
        for qLen in test:
            d = Duration()
            d.quarterLength = qLen
            inputDurations.append(d)

        inputTupletStream = stream.Stream()
        for dur in inputDurations:
            m21Obj = note.Note(duration=dur)
            inputTupletStream.append(m21Obj)

        stream.makeNotation.makeTupletBrackets(inputTupletStream, inPlace=True)
        output = []
        for d in inputDurations:
            output.append(d.tuplets[0].type)
        # environLocal.printDebug(['got', output])
        self.assertEqual(output, match)

    def testTupletTypeNested(self):
        '''
        Nested tuplets are not fully supported (TODO).
        '''
        from music21 import note
        from music21 import stream

        gapful = stream.Measure()
        half = note.Note(type='half')
        gapful.repeatAppend(half, 3)
        for n in gapful:
            n.duration.appendTuplet(Tuplet(3, 2))

        # create nested tuplet on middle note
        gapful.notes[1].duration.appendTuplet(Tuplet(2, 1))

        gapless = stream.Measure()
        for n in gapful:
            gapless.append(n)

        # Redirect stderr to suppress printed warning
        # TODO: change to python warnings
        file_like = io.StringIO()
        with contextlib.redirect_stderr(file_like):
            made = stream.makeNotation.makeTupletBrackets(gapless)

        self.assertEqual(
            [el.duration.tuplets[0].type for el in made],
            ['startStop', None, 'startStop'],  # was ['start', None, 'stop']
        )

    def testAugmentOrDiminish(self):

        # test halfs and doubles

        for ql, half, double in [(2, 1, 4), (0.5, 0.25, 1), (1.5, 0.75, 3),
                                 (2 / 3, 1 / 3, 4 / 3)]:

            d = Duration()
            d.quarterLength = ql
            a = d.augmentOrDiminish(0.5)
            self.assertEqual(a.quarterLength, opFrac(half), 5)

            b = d.augmentOrDiminish(2)
            self.assertEqual(b.quarterLength, opFrac(double), 5)

        # testing tuplets in duration units

        a = Duration()
        a.type = 'eighth'
        tup1 = Tuplet(3, 2, 'eighth')
        a.appendTuplet(tup1)
        self.assertEqual(a.quarterLength, opFrac(1 / 3))
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2 / 3))
        self.assertEqual(repr(a.tuplets[0].durationNormal),
                         "DurationTuple(type='eighth', dots=0, quarterLength=0.5)")

        b = a.augmentOrDiminish(2)
        self.assertEqual(b.quarterLength, opFrac(2 / 3))
        self.assertEqual(b.aggregateTupletMultiplier(), opFrac(2 / 3), 5)
        self.assertEqual(repr(b.tuplets[0].durationNormal),
                         "DurationTuple(type='quarter', dots=0, quarterLength=1.0)")

        c = b.augmentOrDiminish(0.25)
        self.assertEqual(c.aggregateTupletMultiplier(), opFrac(2 / 3), 5)
        self.assertEqual(repr(c.tuplets[0].durationNormal),
                         "DurationTuple(type='16th', dots=0, quarterLength=0.25)")

        # testing tuplets on Durations
        a = Duration()
        a.quarterLength = 1 / 3
        self.assertEqual(a.aggregateTupletMultiplier(), opFrac(2 / 3), 5)
        self.assertEqual(repr(a.tuplets[0].durationNormal),
                         "DurationTuple(type='eighth', dots=0, quarterLength=0.5)")

        b = a.augmentOrDiminish(2)
        self.assertEqual(b.aggregateTupletMultiplier(), opFrac(2 / 3), 5)
        self.assertEqual(repr(b.tuplets[0].durationNormal),
                         "DurationTuple(type='quarter', dots=0, quarterLength=1.0)")

        c = b.augmentOrDiminish(0.25)
        self.assertEqual(c.aggregateTupletMultiplier(), opFrac(2 / 3), 5)
        self.assertEqual(repr(c.tuplets[0].durationNormal),
                         "DurationTuple(type='16th', dots=0, quarterLength=0.25)")

    def testUnlinkedTypeA(self):
        from music21 import duration

        du = duration.Duration()
        du.linked = False
        du.quarterLength = 5.0
        du.type = 'quarter'
        self.assertEqual(du.quarterLength, 5.0)
        self.assertEqual(du.type, 'quarter')

        d = duration.Duration()
        self.assertTrue(d.linked)  # note set
        d.linked = False
        d.type = 'quarter'

        self.assertEqual(d.type, 'quarter')
        self.assertEqual(d.quarterLength, 0.0)  # note set
        self.assertFalse(d.linked)  # note set

        d.quarterLength = 20
        self.assertEqual(d.quarterLength, 20.0)
        self.assertFalse(d.linked)  # note set
        self.assertEqual(d.type, 'quarter')

        # can set type  and will remain unlinked
        d.type = '16th'
        self.assertEqual(d.type, '16th')
        self.assertEqual(d.quarterLength, 20.0)
        self.assertFalse(d.linked)  # note set

        # can set quarter length and will remain unlinked
        d.quarterLength = 0.0
        self.assertEqual(d.type, '16th')
        self.assertFalse(d.linked)  # note set

        # d = duration.Duration()
        # d.setTypeUnlinked('quarter')
        # self.assertEqual(d.type, 'quarter')
        # self.assertEqual(d.quarterLength, 0.0)  # note set
        # self.assertFalse(d.linked)  # note set
        #
        # d.setQuarterLengthUnlinked(20)
        # self.assertEqual(d.quarterLength, 20.0)
        # self.assertFalse(d.linked)  # note set


    def x_testStrangeMeasure(self):
        from music21 import corpus
        from music21 import stream
        j1 = corpus.parse('trecento/PMFC_06-Jacopo-03a')
        x = j1.parts[0].getElementsByClass(stream.Measure)[42]
        x._cache = {}
        print(x.duration)
        print(x.duration.components)

    def testSimpleSetQuarterLength(self):
        d = Duration()
        d.quarterLength = 1 / 3
        self.assertEqual(repr(d.quarterLength), 'Fraction(1, 3)')
        self.assertEqual(d._components, ())
        self.assertTrue(d._componentsNeedUpdating)
        self.assertEqual(str(d.components),
                         "(DurationTuple(type='eighth', dots=0, quarterLength=0.5),)")
        self.assertFalse(d._componentsNeedUpdating)
        self.assertFalse(d._quarterLengthNeedsUpdating)
        self.assertEqual(repr(d.quarterLength), 'Fraction(1, 3)')
        self.assertEqual(str(unitSpec(d)), "(Fraction(1, 3), 'eighth', 0, 3, 2, 'eighth')")

    def testTupletDurations(self):
        '''
        Test tuplet durations are assigned with proper duration

        This test was written while adding support for dotted tuplet notes
        '''
        # Before the fix, the duration was "Quarter Tuplet of 5/3rds (3/5 QL)"
        self.assertEqual(
            'Eighth Triplet (1/3 QL)',
            Duration(fractions.Fraction(1 / 3)).fullName
        )
        self.assertEqual(
            'Quarter Triplet (2/3 QL)',
            Duration(fractions.Fraction(2 / 3)).fullName
        )

        self.assertEqual(
            '16th Quintuplet (1/5 QL)',
            Duration(fractions.Fraction(1 / 5)).fullName
        )
        self.assertEqual(
            'Eighth Quintuplet (2/5 QL)',
            Duration(fractions.Fraction(2 / 5)).fullName
        )
        self.assertEqual(
            'Dotted Eighth Quintuplet (3/5 QL)',
            Duration(fractions.Fraction(3 / 5)).fullName
        )
        self.assertEqual(
            'Quarter Quintuplet (4/5 QL)',
            Duration(fractions.Fraction(4 / 5)).fullName
        )

        self.assertEqual(
            '16th Septuplet (1/7 QL)',
            Duration(fractions.Fraction(1 / 7)).fullName
        )
        self.assertEqual(
            'Eighth Septuplet (2/7 QL)',
            Duration(fractions.Fraction(2 / 7)).fullName
        )
        self.assertEqual(
            'Dotted Eighth Septuplet (3/7 QL)',
            Duration(fractions.Fraction(3 / 7)).fullName
        )
        self.assertEqual(
            'Quarter Septuplet (4/7 QL)',
            Duration(fractions.Fraction(4 / 7)).fullName
        )
        self.assertEqual(
            'Dotted Quarter Septuplet (6/7 QL)',
            Duration(fractions.Fraction(6 / 7)).fullName
        )

    def testTinyDuration(self):
        # e.g. delta from chordify: 1/9 - 1/8 = 1/72
        # exercises quarterLengthToNonPowerOf2Tuplet()
        d = Duration(1 / 72)
        self.assertEqual(d.type, 'inexpressible')

        # this failure happens earlier in quarterConversion()
        d = Duration(1 / 2049)
        self.assertEqual(d.type, 'inexpressible')

    def testExpressionIsInferred(self):
        d = Duration(0.5)
        self.assertEqual(d.expressionIsInferred, True)

        d.type = 'whole'
        self.assertEqual(d.expressionIsInferred, False)

        d.quarterLength = 0.25
        self.assertEqual(d.expressionIsInferred, True)

        d.dots = 1
        self.assertEqual(d.expressionIsInferred, False)

        d.appendTuplet(Tuplet(3, 2))
        # No change
        self.assertEqual(d.expressionIsInferred, False)

        d.linked = False
        d.quarterLength = 4
        d.dots = 1
        # No change, since this relationship between type
        # and quarterLength is usually accomplished in multiple
        # attribute assignments that could occur in any order
        self.assertEqual(d.expressionIsInferred, False)

    def testExceptions(self):
        '''
        These errors are user errors, so they raise generic exceptions
        so that catches for DurationException only get library calculation
        failures (e.g. bound checking).
        '''
        with self.assertRaises(TypeError):
            Duration('redundant type', type='eighth')
        dt = DurationTuple('quarter', 0, float('nan'))
        msg = 'Invalid quarterLength for DurationTuple: nan'
        with self.assertRaisesRegex(ValueError, msg):
            Duration(dt)
        # opFrac raises the ValueError for Duration(float('nan')), but
        # if opFrac ever changes still need to block creating duration
        # could cause infinite loop in makeMeasures() since nan != 0.0
        with self.assertRaises(ValueError):
            Duration(float('nan'))

        d = Duration(1 / 3)
        with self.assertRaises(TypeError):
            d.linked = 'do not link'
        with self.assertRaises(ValueError):
            d.componentIndexAtQtrPosition(400)
        with self.assertRaises(ValueError):
            d.componentIndexAtQtrPosition(-0.001)
        with self.assertRaises(TypeError):
            d.dotGroups = None
        with self.assertRaises(TypeError):
            d.dots = None
        with self.assertRaises(ValueError):
            d.type = 'custom'

        gd = GraceDuration()
        with self.assertRaises(ValueError):
            gd.makeTime = 'True'
        with self.assertRaises(ValueError):
            gd.slash = 'none'

    def testSmallRound(self):
        '''
        Test that some small rounding errors do not
        give division by zero errors anymore.
        '''
        # Up to 65536, off errors are considered intentional
        # and not floating point errors (users should
        # use midi quantization tools to get rounded matches)
        d = Duration(16384 / 65535)
        self.assertEqual(d.quarterLength, fractions.Fraction(16384, 65535))
        self.assertEqual(d.type, 'inexpressible')

        with self.assertRaises(DurationException):
            quarterLengthToClosestType(0)

        self.assertEqual(convertQuarterLengthToType(0), 'zero')
        self.assertEqual(quarterLengthToClosestType(16384 / 65535),
                         ('16th', False))
        self.assertEqual(dottedMatch(0), (False, False))

        # above denominators of 65536 (2**16), small deviations
        # are considered close enough to round to exact matches
        o = quarterConversion(65536 / (65536 * 2 - 1))
        self.assertIsInstance(o, QuarterLengthConversion)
        c = o.components
        self.assertEqual(len(c), 1)
        c0 = c[0]
        self.assertIsInstance(c0, DurationTuple)
        self.assertEqual(c0.quarterLength, 0.75)

        # strangely (and this behavior can/should change)
        # it is currently converted as a triplet DOTTED eighth note
        # rather than a normal eighth!
        self.assertEqual(c0.type, 'eighth')
        self.assertEqual(c0.dots, 1)
        self.assertTrue(o.tuplet)
        self.assertEqual(o.tuplet.tupletMultiplier(), fractions.Fraction(2, 3))


# -------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER: DocOrder = [
    Duration, Tuplet, GraceDuration, convertQuarterLengthToType, TupletFixer,
]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testAugmentOrDiminish')

