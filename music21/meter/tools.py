# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         meter.tools.py
# Purpose:      Tools for working with meter
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009-2022 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

import collections
import fractions
from functools import lru_cache
import math
import re
import typing as t

from music21 import common
from music21.common.enums import MeterDivision
from music21 import environment
from music21.exceptions21 import MeterException, Music21Exception, TimeSignatureException

environLocal = environment.Environment('meter.tools')

MeterTerminalTuple = collections.namedtuple('MeterTerminalTuple',
                                            ['numerator', 'denominator', 'division'])
NumDenom = tuple[int, int]
NumDenomTuple = tuple[NumDenom, ...]
MeterOptions = tuple[tuple[NumDenom, ...], ...]

validDenominators = [1, 2, 4, 8, 16, 32, 64, 128]  # in order
validDenominatorsSet = set(validDenominators)


@lru_cache(512)
def slashToTuple(value: str) -> MeterTerminalTuple:
    '''
    Returns a three-element MeterTerminalTuple of numerator, denominator, and optional
    division of the meter.

    >>> meter.tools.slashToTuple('3/8')
    MeterTerminalTuple(numerator=3, denominator=8, division=<MeterDivision.NONE>)
    >>> meter.tools.slashToTuple('7/32')
    MeterTerminalTuple(numerator=7, denominator=32, division=<MeterDivision.NONE>)
    >>> meter.tools.slashToTuple('slow 6/8')
    MeterTerminalTuple(numerator=6, denominator=8, division=<MeterDivision.SLOW>)
    '''
    # quick return:
    try:
        top, bottom = value.split('/')
        return MeterTerminalTuple(int(top), int(bottom), MeterDivision.NONE)
    except (ValueError, AttributeError, TypeError):
        pass

    # now the slow way.

    # split by numbers, include slash
    valueNumbers, valueChars = common.getNumFromStr(value,
                                                    numbers='0123456789/.')
    valueNumbers = valueNumbers.strip()  # remove whitespace
    valueChars = valueChars.strip()  # remove whitespace
    if 'slow' in valueChars.lower():
        division = MeterDivision.SLOW
    elif 'fast' in valueChars.lower():
        division = MeterDivision.FAST
    else:
        division = MeterDivision.NONE

    matches = re.match(r'(\d+)/(\d+)', valueNumbers)
    if matches is not None:
        n = int(matches.group(1))
        d = int(matches.group(2))
        return MeterTerminalTuple(n, d, division)

    raise MeterException(f'slashToTuple() cannot find two part fraction for {value}')


@lru_cache(512)
def slashCompoundToFraction(value: str) -> NumDenomTuple:
    '''
    Change a compount meter into a list of simple numberator, demoninator values

    >>> meter.tools.slashCompoundToFraction('3/8+2/8')
    ((3, 8), (2, 8))
    >>> meter.tools.slashCompoundToFraction('5/8')
    ((5, 8),)
    >>> meter.tools.slashCompoundToFraction('5/8+2/4+6/8')
    ((5, 8), (2, 4), (6, 8))

    * Changed in v7: new location and returns a tuple.
    '''
    post: list[NumDenom] = []
    value = value.strip()  # rem whitespace
    valueList = value.split('+')
    for part in valueList:
        try:
            m = slashToTuple(part)
            post.append((m.numerator, m.denominator))
        except MeterException:
            pass
    return tuple(post)


def separateSharedDenominators(valueSrc: str) -> list[tuple[tuple[int, ...], int, MeterDivision]]:
    '''
    Returns a tuple of tuples from a string where each element represents
    a set of meters that share an expressed denominator.  The first sub-element is a tuple
    of all the numerators sharing a denominator.  Normally there is one
    element in it.  The second sub-element is that shared denominator.

    For instance, '4/4' would be [((4,), 4)].

    '3/8+5/16' would be [((3,), 8), ((5,), 16)]

    However, '2+3+2/8' would be [((2, 3, 2), 8)] and '2+3+2/8+3/16' would be:
    [((2, 3, 2), 8), ((3,), 16)]

    However, there is a third part to each inner tuple, not shown above which
    specifies if the compound meter division is slow, fast, or unspecified.

    Raises ValueError if no denominator can be found.

    >>> ssd = meter.tools.separateSharedDenominators
    >>> ssd('4/4')
    [((4,), 4, <MeterDivision.NONE>)]

    >>> ssd('3/8 + 5/16')
    [((3,), 8, <MeterDivision.NONE>), ((5,), 16, <MeterDivision.NONE>)]

    >>> ssd('2+3+2/8')
    [((2, 3, 2), 8, <MeterDivision.NONE>)]

    Some denominators are shared and some are not:

    >>> ssd('2+3+2/8+3/16')
    [((2, 3, 2), 8, <MeterDivision.NONE>), ((3,), 16, <MeterDivision.NONE>)]

    This is a pretty absurd meter:

    >>> ssd('slow 6/8 + fast 9/8')
    [((6,), 8, <MeterDivision.SLOW>), ((9,), 8, <MeterDivision.FAST>)]

    Presumably a '/8' was left off below:

    >>> ssd('3/4+2+3')
    Traceback (most recent call last):
    ValueError: cannot match denominator to numerator in '3/4+2+3'

    This routine replaces 'slashToMixedFraction' from before; it presumes that
    in an expression like 2+3+2/8 + 3/4 that 2+3+2/8 represents one entity and
    that 3/4 represents another, and that 2/8, 3/8, 2/8 are sub-elements withing
    that first entity rather than being at the same level of division as 3/4.
    This was a backwards incompatible change in v9--previously all 4 components
    would have been considered at the same level--but presumably it will not
    affect many rhythmic analyses.
    '''
    parts: list[str] = valueSrc.split('+')
    out = []
    seeking_denominator: list[int] = []
    for part in parts:
        part = part.strip()
        if '/' in part:
            # normal case: a full signature.
            try:
                tup = slashToTuple(part)
            except MeterException as me:
                raise TimeSignatureException(
                    f'Cannot create time signature from "{valueSrc}"') from me
            if seeking_denominator:
                # others were waiting to find a denominator
                seeking_denominator.append(tup.numerator)
                current = (tuple(seeking_denominator), tup.denominator, tup.division)
                out.append(current)
                seeking_denominator = []
            else:  # normal case.
                out.append(((tup.numerator,), tup.denominator, tup.division))
        else:  # its just a numerator
            seeking_denominator.append(int(part))

    if seeking_denominator:
        raise ValueError(f'cannot match denominator to numerator in {valueSrc!r}')

    return out


@lru_cache(512)
def slashMixedToFraction(valueSrc: str) -> tuple[NumDenomTuple, bool]:
    '''
    Given a mixture if possible meter fraction representations, return a tuple
    of two elements: The first element is a tuple of pairs of numerator, denominators
    that are implied by the time signature.

    The second element is False if the value was a simple time signature (like 4/4)
    or a composite meter where all numerators had their own denominators.

    >>> meter.tools.slashMixedToFraction('4/4')
    (((4, 4),), False)

    >>> meter.tools.slashMixedToFraction('3/8+2/8')
    (((3, 8), (2, 8)), False)

    >>> meter.tools.slashMixedToFraction('3+2/8')
    (((3, 8), (2, 8)), True)

    >>> meter.tools.slashMixedToFraction('3+2+5/8')
    (((3, 8), (2, 8), (5, 8)), True)

    >>> meter.tools.slashMixedToFraction('3+2+5/8+3/4')
    (((3, 8), (2, 8), (5, 8), (3, 4)), True)

    >>> meter.tools.slashMixedToFraction('3+2+5/8+3/4+2+1+4/16')
    (((3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)), True)

    >>> meter.tools.slashMixedToFraction('3+2+5/8+3/4+2+1+4')
    Traceback (most recent call last):
    music21.exceptions21.MeterException: cannot match denominator to numerator in: 3+2+5/8+3/4+2+1+4

    Float values are not acceptable here.

    >>> meter.tools.slashMixedToFraction('3.0/4.0')
    Traceback (most recent call last):
    music21.exceptions21.TimeSignatureException: Cannot create time signature from "3.0/4.0"

    * Changed in v7: new location and returns a tuple as first value.
    '''
    # REFACTOR: TODO: record which parts have a shared denominator and which don't.
    pre: list[NumDenom | tuple[int, None]] = []
    post: list[NumDenom] = []
    denominatorIsShared = False
    value = valueSrc.strip()  # rem whitespace
    value = value.split('+')
    for part in value:
        if '/' in part:
            try:
                tup = slashToTuple(part)
            except MeterException as me:
                raise TimeSignatureException(
                    f'Cannot create time signature from "{valueSrc}"') from me
            pre.append((tup.numerator, tup.denominator))
        else:  # its just a numerator
            try:
                pre.append((int(part), None))
            except ValueError:
                raise Music21Exception(
                    'Cannot parse this file -- this error often comes '
                    + 'up if the musicxml pickled file is out of date after a change '
                    + 'in musicxml/__init__.py . '
                    + 'Clear your temp directory of .p and .p.gz files and try again...; '
                    + f'Time Signature: {valueSrc} ')

    # when encountering a missing denominator, find the first defined
    # and apply to all previous
    for i in range(len(pre)):
        if pre[i][1] is not None:  # there is a denominator
            intNum = pre[i][0]  # this is all for type checking
            intDenom = pre[i][1]
            if t.TYPE_CHECKING:
                assert isinstance(intNum, int) and isinstance(intDenom, int)
            post.append((intNum, intDenom))
        else:  # search ahead for next defined denominator
            denominatorIsShared = True
            match: int | None = None
            for j in range(i, len(pre)):  # this O(n^2) operation is easily simplified to O(n)
                if pre[j][1] is not None:
                    match = pre[j][1]
                    break
            if match is None:
                raise MeterException(f'cannot match denominator to numerator in: {valueSrc}')

            preBothAreInts = (pre[i][0], match)
            post.append(preBothAreInts)

    return tuple(post), denominatorIsShared


@lru_cache(512)
def fractionToSlashMixed(fList: NumDenomTuple) -> tuple[tuple[str, int], ...]:
    '''
    Given a tuple of fraction values, compact numerators by sum if denominators
    are the same

    >>> from music21.meter.tools import fractionToSlashMixed
    >>> fractionToSlashMixed(((3, 8), (2, 8), (5, 8), (3, 4), (2, 16), (1, 16), (4, 16)))
    (('3+2+5', 8), ('3', 4), ('2+1+4', 16))

    * Changed in v7: new location and returns a tuple.
    '''
    pre: list[tuple[list[int], int]] = []
    for i in range(len(fList)):
        n: int
        d: int
        n, d = fList[i]
        # look at previous fraction and determine if denominator is the same

        match = None
        search = list(range(len(pre)))
        search.reverse()  # go backwards
        for j in search:
            if pre[j][1] == d:
                match = j  # index to add numerator
                break
            else:
                break  # if not found in one less

        if match is None:
            pre.append(([n], d))
        else:  # append numerator
            pre[match][0].append(n)

    # create string representation
    post: list[tuple[str, int]] = []
    for part in pre:
        nStrList = [str(x) for x in part[0]]
        nStr = '+'.join(nStrList)
        dInt = part[1]
        post.append((nStr, dInt))

    return tuple(post)


@lru_cache(512)
def fractionSum(numDenomTuple: NumDenomTuple) -> NumDenom:
    '''
    Given a tuple of tuples of numerator and denominator,
    find the sum; does NOT reduce to its lowest terms.

    >>> from music21.meter.tools import fractionSum
    >>> fractionSum(((3, 8), (5, 8), (1, 8)))
    (9, 8)
    >>> fractionSum(((1, 6), (2, 3)))
    (5, 6)
    >>> fractionSum(((3, 4), (1, 2)))
    (5, 4)
    >>> fractionSum(((1, 13), (2, 17)))
    (43, 221)
    >>> fractionSum(())
    (0, 1)

    This method might seem like an easy place to optimize and simplify
    by just doing a fractions.Fraction() sum (I tried!), but not reducing to
    its lowest terms is a feature of this method. 3/8 + 3/8 = 6/8, not 3/4:

    >>> fractionSum(((3, 8), (3, 8)))
    (6, 8)
    '''
    nList = []
    dList = []
    dListUnique = set()

    for n, d in numDenomTuple:
        nList.append(n)
        dList.append(d)
        dListUnique.add(d)

    if len(dListUnique) == 1:
        n = sum(nList)
        d = next(iter(dListUnique))
        # Does not reduce to lowest terms...
        return (n, d)
    else:  # there might be a better way to do this
        d = 1
        d = math.lcm(*dListUnique)
        # after finding d, multiply each numerator
        nShift = []
        for i in range(len(nList)):
            nSrc = nList[i]
            dSrc = dList[i]
            scalar = d // dSrc
            nShift.append(nSrc * scalar)
        return (sum(nShift), d)



@lru_cache(512)
def proportionToFraction(value: float) -> NumDenom:
    '''
    Given a floating point proportional value between 0 and 1, return the
    best-fit slash-base fraction

    >>> from music21.meter.tools import proportionToFraction
    >>> proportionToFraction(0.5)
    (1, 2)
    >>> proportionToFraction(0.25)
    (1, 4)
    >>> proportionToFraction(0.75)
    (3, 4)
    >>> proportionToFraction(0.125)
    (1, 8)
    >>> proportionToFraction(0.375)
    (3, 8)
    >>> proportionToFraction(0.625)
    (5, 8)
    >>> proportionToFraction(0.333)
    (1, 3)
    >>> proportionToFraction(0.83333)
    (5, 6)
    '''
    f = fractions.Fraction(value).limit_denominator(16)
    return (f.numerator, f.denominator)


# -------------------------------------------------------------------------
# load common meter templates into this sequence
# no need to cache these -- getPartitionOptions is cached

def divisionOptionsFractionsUpward(n: int, d: int) -> tuple[NumDenom, ...]:
    '''
    This simply gets restatements of the same fraction in smaller units,
    up to the largest valid denominator.

    >>> meter.tools.divisionOptionsFractionsUpward(2, 4)
    ((4, 8), (8, 16), (16, 32), (32, 64), (64, 128))
    >>> meter.tools.divisionOptionsFractionsUpward(3, 4)
    ((6, 8), (12, 16), (24, 32), (48, 64), (96, 128))

    * Changed in v9: returns a tuple of NumDenom
    '''
    opts: list[NumDenom] = []
    # equivalent fractions upward
    if d < validDenominators[-1]:
        nMod = n * 2
        dMod = d * 2
        while True:
            if dMod > validDenominators[-1]:
                break
            opts.append((nMod, dMod))
            dMod = dMod * 2
            nMod = nMod * 2
    return tuple(opts)

def divisionOptionsFractionsDownward(n: int, d: int) -> tuple[NumDenom, ...]:
    '''
    Get restatements of the same fraction in larger units

    >>> meter.tools.divisionOptionsFractionsDownward(2, 4)
    ((1, 2),)
    >>> meter.tools.divisionOptionsFractionsDownward(12, 16)
    ((6, 8), (3, 4))

    * Changed in v9: returns a tuple of NumDenom
    '''
    opts: list[NumDenom] = []
    if d > validDenominators[0] and n % 2 == 0:
        nMod = n // 2
        dMod = d // 2
        while True:
            if dMod < validDenominators[0]:
                break
            opts.append((nMod, dMod))
            if nMod % 2 != 0:  # no longer even
                break
            dMod = dMod // 2
            nMod = nMod // 2
    return tuple(opts)


def divisionOptionsAdditiveMultiplesDownward(n: int, d: int) -> MeterOptions:
    '''
    >>> meter.tools.divisionOptionsAdditiveMultiplesDownward(1, 16)
    (((1, 32), (1, 32)),
     ((1, 64), (1, 64), (1, 64), (1, 64)),
     ((1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128)))

    '''
    opts: list[tuple[NumDenom, ...]] = []
    # this only takes n == 1
    if d < validDenominators[-1] and n == 1:
        i = 2
        dMod = d * 2
        while True:
            if dMod > validDenominators[-1]:
                break
            seq = [(n, dMod)] * i
            opts.append(tuple(seq))
            dMod = dMod * 2
            i *= 2
    return tuple(opts)


def divisionOptionsAdditiveMultiples(n: int, d: int) -> MeterOptions:
    '''
    Additive multiples with the same denominators.

    >>> meter.tools.divisionOptionsAdditiveMultiples(4, 16)
    (((2, 16), (2, 16)),)
    >>> meter.tools.divisionOptionsAdditiveMultiples(6, 4)
    (((3, 4), (3, 4)),)
    >>> meter.tools.divisionOptionsAdditiveMultiples(8, 8)
    (((4, 8), (4, 8)),
     ((2, 8), (2, 8), (2, 8), (2, 8)))
    '''
    opts: list[tuple[NumDenom, ...]] = []
    if n > 3 and n % 2 == 0:
        i = 2
        nMod = n // 2
        while True:
            if nMod <= 1:
                break
            seq = [(nMod, d)] * i
            opts.append(tuple(seq))
            nMod = nMod // 2
            i *= 2
    return tuple(opts)


def divisionOptionsAdditiveMultiplesEvenDivision(n: int, d: int) -> MeterOptions:
    '''
    >>> meter.tools.divisionOptionsAdditiveMultiplesEvenDivision(4, 16)
    (((1, 8), (1, 8)),)
    >>> meter.tools.divisionOptionsAdditiveMultiplesEvenDivision(4, 4)
    (((1, 2), (1, 2)),)
    >>> meter.tools.divisionOptionsAdditiveMultiplesEvenDivision(3, 4)
    ()
    '''
    opts: list[tuple[NumDenom, ...]] = []
    # divided additive multiples
    # if given 4/4, get 2/4+2/4
    if n % 2 == 0 and d // 2 >= 1:
        nMod = n // 2
        dMod = d // 2
        while True:
            if dMod < 1 or nMod <= 1:
                break
            seq = [(1, dMod)] * nMod
            opts.append(tuple(seq))
            if nMod % 2 != 0:  # if no longer even must stop
                break
            dMod = dMod // 2
            nMod = nMod // 2
    return tuple(opts)


def divisionOptionsAdditiveMultiplesUpward(n: int, d: int) -> MeterOptions:
    '''
    >>> meter.tools.divisionOptionsAdditiveMultiplesUpward(4, 16)
    (((1, 16), (1, 16), (1, 16), (1, 16)),
     ((1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32)),
     ((1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64),
      (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64)))
    >>> meter.tools.divisionOptionsAdditiveMultiplesUpward(3, 4)
    (((1, 4), (1, 4), (1, 4)),
     ((1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16),
      (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16)))
    '''
    opts: list[tuple[NumDenom, ...]] = []
    if n > 1 and d >= 1:
        dCurrent = d
        nCount = n
        if n > 16:  # go up to n if greater than 16
            nCountLimit = n
        else:
            nCountLimit = 16

        while True:
            # place practical limits on number of units to get
            if dCurrent > validDenominators[-1] or nCount > nCountLimit:
                break
            seq = [(1, dCurrent)] * nCount
            opts.append(tuple(seq))
            # double count, double denominator
            dCurrent *= 2
            nCount *= 2
    return tuple(opts)


@lru_cache(512)
def divisionOptionsAlgo(n: int, d: int) -> MeterOptions:
    '''
    This is a primitive approach to algorithmic division production.
    This can be extended.

    It is assumed that these values are provided in order of priority

    >>> meter.tools.divisionOptionsAlgo(4, 4)
    (((1, 4), (1, 4), (1, 4), (1, 4)),
     ((1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16),
      (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16)),
     ((1, 2), (1, 2)),
     ((4, 4),),
     ((2, 4), (2, 4)),
     ((2, 2),),
     ((1, 1),),
     ((8, 8),),
     ((16, 16),),
     ((32, 32),),
     ((64, 64),),
     ((128, 128),))

    >>> meter.tools.divisionOptionsAlgo(1, 4)
    (((1, 4),),
     ((1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16)),
     ((1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32)),
     ((1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64),
      (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64), (1, 64)),
     ((1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128),
      (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128),
      (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128),
      (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128), (1, 128)),
     ((2, 8),),
     ((4, 16),),
     ((8, 32),),
     ((16, 64),),
     ((32, 128),))

    >>> meter.tools.divisionOptionsAlgo(2, 2)
    (((1, 2), (1, 2)),
     ((1, 4), (1, 4), (1, 4), (1, 4)),
     ((1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16),
      (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16)),
     ((2, 2),),
     ((1, 1),),
     ((4, 4),),
     ((8, 8),),
     ((16, 16),),
     ((32, 32),),
     ((64, 64),),
     ((128, 128),))

    >>> meter.tools.divisionOptionsAlgo(3, 8)
    (((1, 8), (1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16)),
     ((1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32),
      (1, 32), (1, 32), (1, 32), (1, 32), (1, 32), (1, 32)),
     ((3, 8),),
     ((6, 16),),
     ((12, 32),),
     ((24, 64),),
     ((48, 128),))

    >>> meter.tools.divisionOptionsAlgo(6, 8)
    (((3, 8), (3, 8)),
     ((1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16),
      (1, 16), (1, 16), (1, 16), (1, 16), (1, 16), (1, 16)),
     ((1, 4), (1, 4), (1, 4)),
     ((6, 8),),
     ((3, 4),),
     ((12, 16),),
     ((24, 32),),
     ((48, 64),),
     ((96, 128),))

    >>> meter.tools.divisionOptionsAlgo(12, 8)
    (((3, 8), (3, 8), (3, 8), (3, 8)),
     ((1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8),
      (1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8)),
     ((1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)),
     ((1, 2), (1, 2), (1, 2)),
     ((12, 8),),
     ((6, 8), (6, 8)),
     ((6, 4),),
     ((3, 2),),
     ((24, 16),),
     ((48, 32),),
     ((96, 64),),
     ((192, 128),))

    >>> meter.tools.divisionOptionsAlgo(5, 8)
    (((2, 8), (3, 8)),
     ((3, 8), (2, 8)),
     ((1, 8), (1, 8), (1, 8), (1, 8), (1, 8)),
     ((1, 16), (1, 16), (1, 16), (1, 16), (1, 16),
      (1, 16), (1, 16), (1, 16), (1, 16), (1, 16)),
     ((5, 8),),
     ((10, 16),),
     ((20, 32),),
     ((40, 64),),
     ((80, 128),))

    >>> meter.tools.divisionOptionsAlgo(18, 4)
    (((3, 4), (3, 4), (3, 4), (3, 4), (3, 4), (3, 4)),
     ((1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4),
      (1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4),
      (1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4)),
     ((1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2)),
     ((18, 4),),
     ((9, 4), (9, 4)),
     ((4, 4), (4, 4), (4, 4), (4, 4)),
     ((2, 4), (2, 4), (2, 4), (2, 4), (2, 4), (2, 4), (2, 4), (2, 4)),
     ((9, 2),),
     ((36, 8),),
     ((72, 16),),
     ((144, 32),),
     ((288, 64),),
     ((576, 128),))

    >>> meter.tools.divisionOptionsAlgo(3, 128)
    (((1, 128), (1, 128), (1, 128)),
     ((3, 128),))
    '''
    opts: list[tuple[NumDenom, ...]] = []
    group: tuple[int, ...]

    # compound meters; 6, 9, 12, 15, 18
    # 9/4, 9/2, 6/2 are all considered compound without d>4
    # if n % 3 == 0 and n > 3 and d > 4:
    if n % 3 == 0 and n > 3:
        nMod = n / 3
        seq = [(3, d)] * (n // 3)
        opts.append(tuple(seq))
    # odd meters with common groupings
    elif n == 5:
        seq_tup = (((2, d), (3, d)),
                   ((3, d), (2, d)))
        opts.extend(seq_tup)
    elif n == 7:
        seq_tup = (((2, d), (2, d), (3, d)),
                   ((3, d), (2, d), (2, d)),
                   ((2, d), (3, d), (2, d)))
        opts.extend(seq_tup)
    # not really necessary but an example of a possibility
    elif n == 10:
        seq_tup = ((2, d), (2, d), (3, d), (3, d))
        opts.append(seq_tup)

    # simple additive options uses the minimum numerator of 1
    # given 3/4, get 1/4 three times
    opts.extend(divisionOptionsAdditiveMultiplesUpward(n, d))
    # divided additive multiples
    # if given 4/4, get 2/4+2/4
    opts.extend(divisionOptionsAdditiveMultiplesEvenDivision(n, d))
    # add src representation
    opts.append(((n, d),))
    # additive multiples with the same denominators
    # add to "opts" in-place
    opts.extend(divisionOptionsAdditiveMultiples(n, d))
    # additive multiples with smaller denominators
    # only doing this for numerators of 1 for now
    opts.extend(divisionOptionsAdditiveMultiplesDownward(n, d))
    # equivalent fractions downward
    opts.extend([(o,) for o in divisionOptionsFractionsDownward(n, d)])
    # equivalent fractions upward
    opts.extend([(o,) for o in divisionOptionsFractionsUpward(n, d)])
    return tuple(common.misc.unique(o for o in opts if o != ()))


@lru_cache(512)
def divisionOptionsPreset(n, d) -> MeterOptions:
    '''
    Provide fixed set of meter divisions that will not be easily
    obtained algorithmically.

    Currently, does nothing except to allow partitioning 5/8 as 2/8, 2/8, 1/8 as a possibility
    (sim for 5/16, etc.)

    >>> meter.tools.divisionOptionsPreset(5, 8)
    (((2, 8), (2, 8), (1, 8)), ((2, 8), (1, 8), (2, 8)))
    >>> meter.tools.divisionOptionsPreset(3, 4)
    ()

    >>> ms2 = meter.MeterSequence('5/32')
    >>> ms2.getPartitionOptions()
    (((2, 32), (3, 32)),
     ((3, 32), (2, 32)),
     ((1, 32), (1, 32), (1, 32), (1, 32), (1, 32)),
     ((1, 64), (1, 64), (1, 64), (1, 64), (1, 64),
      (1, 64), (1, 64), (1, 64), (1, 64), (1, 64)),
     ((5, 32),),
     ((10, 64),),
     ((20, 128),),
     ((2, 32), (2, 32), (1, 32)),
     ((2, 32), (1, 32), (2, 32)))
    '''
    if n != 5:
        return ()

    return (
        ((2, d), (2, d), (1, d)),
        ((2, d), (1, d), (2, d)),
    )



if __name__ == '__main__':
    import music21
    music21.mainTest()
