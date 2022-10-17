# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/numberTools.py
# Purpose:      Utilities for working with numbers or number-like objects
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2022 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

from collections.abc import Iterable, Sequence, Collection
from fractions import Fraction
from functools import cache
import math
from math import isclose, gcd
import numbers
import random
import typing as t
import unittest

from music21 import defaults
from music21.common import deprecated
from music21.common.types import OffsetQLIn, OffsetQL

__all__ = [
    'ordinals', 'musicOrdinals', 'ordinalsToNumbers',
    'numToIntOrFloat',

    'opFrac', 'mixedNumeral',
    'roundToHalfInteger',
    'addFloatPrecision', 'strTrimFloat',
    'nearestMultiple',

    'dotMultiplier', 'decimalToTuplet',
    'unitNormalizeProportion', 'unitBoundaryProportion',
    'weightedSelection',
    'approximateGCD',

    'contiguousList',

    'groupContiguousIntegers',

    'fromRoman', 'toRoman',
    'ordinalAbbreviation',
]

ordinals = [
    'Zeroth', 'First', 'Second', 'Third', 'Fourth', 'Fifth',
    'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth', 'Eleventh',
    'Twelfth', 'Thirteenth', 'Fourteenth', 'Fifteenth',
    'Sixteenth', 'Seventeenth', 'Eighteenth', 'Nineteenth',
    'Twentieth', 'Twenty-first', 'Twenty-second',
]

musicOrdinals = ordinals[:]
musicOrdinals[1] = 'Unison'
musicOrdinals[8] = 'Octave'
musicOrdinals[15] = 'Double-octave'
musicOrdinals[22] = 'Triple-octave'


# -----------------------------------------------------------------------------
# Number methods...


def numToIntOrFloat(value: int | float) -> int | float:
    '''
    Given a number, return an integer if it is very close to an integer,
    otherwise, return a float.

    This routine is very important for conversion of
    :class:`~music21.pitch.Accidental` objects' `.alter`  attribute
    in musicXML must be 1 (not 1.0) for sharp and -1 (not -1.0) for flat,
    but allows for 0.5 for half-sharp.

    >>> common.numToIntOrFloat(1.0)
    1
    >>> common.numToIntOrFloat(1.00003)
    1.00003
    >>> common.numToIntOrFloat(1.5)
    1.5
    >>> common.numToIntOrFloat(1.0000000005)
    1
    >>> common.numToIntOrFloat(0.999999999)
    1

    >>> sharp = pitch.Accidental('sharp')
    >>> common.numToIntOrFloat(sharp.alter)
    1
    >>> halfFlat = pitch.Accidental('half-flat')
    >>> common.numToIntOrFloat(halfFlat.alter)
    -0.5

    Can also take in a string representing an int or float

    >>> common.numToIntOrFloat('1.0')
    1
    >>> common.numToIntOrFloat('1')
    1
    >>> common.numToIntOrFloat('1.25')
    1.25
    '''
    try:
        intVal = round(value)
    except (ValueError, TypeError):
        value = float(value)
        intVal = round(value)

    if isclose(intVal, value, abs_tol=1e-6):
        return intVal
    else:  # source
        return value


DENOM_LIMIT = defaults.limitOffsetDenominator

@cache
def _preFracLimitDenominator(n: int, d: int) -> tuple[int, int]:
    # noinspection PyShadowingNames
    '''
    Used in opFrac

    Copied from fractions.limit_denominator.  Their method
    requires creating three new Fraction instances to get one back.
    This doesn't create any call before Fraction...

    DENOM_LIMIT is hardcoded to defaults.limitOffsetDenominator for speed...

    returns a new n, d...

    >>> common.numberTools._preFracLimitDenominator(100001, 300001)
    (1, 3)

    >>> from fractions import Fraction
    >>> Fraction(100_000_000_001, 30_0000_000_001).limit_denominator(65535)
    Fraction(1, 3)
    >>> Fraction(100001, 300001).limit_denominator(65535)
    Fraction(1, 3)

    Timing differences are huge!

    t is timeit.timeit

    t('Fraction(*common.numberTools._preFracLimitDenominator(*x.as_integer_ratio()))',
       setup='x = 1000001/3000001.; from music21 import common;from fractions import Fraction',
       number=100000)
    1.0814228057861328

    t('Fraction(x).limit_denominator(65535)',
       setup='x = 1000001/3000001.; from fractions import Fraction',
       number=100000)
    7.941488981246948

    Proof of working...

    >>> import random
    >>> myWay = lambda x: Fraction(*common.numberTools._preFracLimitDenominator(
    ...     *x.as_integer_ratio()))
    >>> theirWay = lambda x: Fraction(x).limit_denominator(65535)

    >>> for _ in range(50):
    ...     x = random.random()
    ...     if myWay(x) != theirWay(x):
    ...         print(f'boo: {x}, {myWay(x)}, {theirWay(x)}')

    (n.b. -- nothing printed)
    '''
    if d <= DENOM_LIMIT:  # faster than hard-coding 65535
        return (n, d)
    nOrg = n
    dOrg = d
    p0, q0, p1, q1 = 0, 1, 1, 0
    while True:
        a = n // d
        q2 = q0 + a * q1
        if q2 > DENOM_LIMIT:
            break
        p0, q0, p1, q1 = p1, q1, p0 + a * p1, q2
        n, d = d, n - a * d

    k = (DENOM_LIMIT - q0) // q1
    bound1n = p0 + k * p1
    bound1d = q0 + k * q1
    bound2n = p1
    bound2d = q1
    # s = (0.0 + n)/d
    bound1minusS_n = abs((bound1n * dOrg) - (nOrg * bound1d))
    bound1minusS_d = dOrg * bound1d
    bound2minusS_n = abs((bound2n * dOrg) - (nOrg * bound2d))
    bound2minusS_d = dOrg * bound2d
    difference = (bound1minusS_n * bound2minusS_d) - (bound2minusS_n * bound1minusS_d)
    if difference >= 0:
        # bound1 is farther from zero than bound2; return bound2
        return (bound2n, bound2d)
    else:
        return (bound1n, bound1d)


# _KNOWN_PASSES is all values from whole to 64th notes with 0 or 1 dot
# the length of this set does determine the time to search.  A set with all values from maxima to
# 2048th notes + 1-2 dots was half the speed

_KNOWN_PASSES = frozenset([
    0.0625, 0.09375, 0.125, 0.1875,
    0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0
])

# no type checking due to accessing protected attributes (for speed)
@t.no_type_check
def opFrac(num: OffsetQLIn | None) -> OffsetQL | None:
    '''
    opFrac -> optionally convert a number to a fraction or back.

    Important music21 function for working with offsets and quarterLengths

    Takes in a number (or None) and converts it to a Fraction with denominator
    less than limitDenominator if it is not binary expressible; otherwise return a float.
    Or if the Fraction can be converted back to a binary expressible
    float then do so.

    This function should be called often to ensure that values being passed around are floats
    and ints wherever possible and fractions where needed.

    The naming of this method violates music21's general rule of no abbreviations, but it
    is important to make it short enough so that no one will be afraid of calling it often.
    It also doesn't have a setting for maxDenominator so that it will expand in
    Code Completion easily. That is to say, this function has been set up to be used, so please
    use it.

    This is a performance critical operation. Do not alter it in any way without running
    many timing tests.

    >>> from fractions import Fraction
    >>> defaults.limitOffsetDenominator
    65535
    >>> common.opFrac(3)
    3.0
    >>> common.opFrac(1/3)
    Fraction(1, 3)
    >>> common.opFrac(1/4)
    0.25
    >>> f = Fraction(1, 3)
    >>> common.opFrac(f + f + f)
    1.0
    >>> common.opFrac(0.123456789)
    Fraction(10, 81)
    >>> common.opFrac(None) is None
    True
    '''
    # This is a performance critical operation, tuned to go as fast as possible.
    # hence redundancy -- first we check for type (no inheritance) and then we
    # repeat exact same test with inheritance.
    #
    # Cannot use functools's Caching mechanisms on this because then it will
    # return the same Fraction object for all calls, which is a problem in case
    # anyone sets ._numeration or ._denominator directly on that object.
    #
    if num in _KNOWN_PASSES:
        return num + 0.0   # need the add, because ints and Fractions satisfy the "in"

    # Note that the later examples are more verbose
    numType = type(num)
    if numType is float:
        # quick test of power of whether denominator is a power
        # of two, and thus representable exactly as a float: can it be
        # represented w/ a denominator less than DENOM_LIMIT?
        # this doesn't work:
        #    (denominator & (denominator-1)) != 0
        # which is a nice test, but denominator here is always a power of two...
        # unused_numerator, denominator = num.as_integer_ratio()  # too slow
        ir = num.as_integer_ratio()
        if ir[1] > DENOM_LIMIT:  # slightly faster[SIC!] than hard coding 65535!
            # _preFracLimitDenominator uses a cache
            return Fraction(*_preFracLimitDenominator(*ir))  # way faster!
            # return Fraction(*ir).limit_denominator(DENOM_LIMIT) # *ir instead of float--can happen
            # internally in Fraction constructor, but is twice as fast...
        else:
            return num
    elif numType is int:  # if vs. elif is negligible time difference.
        return num + 0.0  # 8x faster than float(num)
    elif numType is Fraction:
        d = num._denominator  # private access instead of property: 6x faster; may break later...
        if (d & (d - 1)) == 0:  # power of two...
            return num._numerator / (d + 0.0)  # 50% faster than float(num)
        else:
            return num  # leave non-power of two fractions alone
    elif num is None:
        return None

    # class inheritance only check AFTER "type is" checks... this is redundant but highly optimized.
    elif isinstance(num, int):
        return num + 0.0
    elif isinstance(num, float):
        ir = num.as_integer_ratio()
        if ir[1] > DENOM_LIMIT:  # slightly faster than hard coding 65535!
            return Fraction(*_preFracLimitDenominator(*ir))  # way faster!
        else:
            return num

    elif isinstance(num, Fraction):
        d = num.denominator  # Use properties since it is a subclass
        if (d & (d - 1)) == 0:  # power of two...
            return num.numerator / (d + 0.0)  # 50% faster than float(num)
        else:
            return num  # leave fraction alone
    else:
        raise TypeError(f'Cannot convert num: {num}')


def mixedNumeral(expr: numbers.Real,
                 limitDenominator=defaults.limitOffsetDenominator):
    '''
    Returns a string representing a mixedNumeral form of a number

    >>> common.mixedNumeral(1.333333)
    '1 1/3'
    >>> common.mixedNumeral(0.333333)
    '1/3'
    >>> common.mixedNumeral(-1.333333)
    '-1 1/3'
    >>> common.mixedNumeral(-0.333333)
    '-1/3'

    >>> common.mixedNumeral(0)
    '0'
    >>> common.mixedNumeral(-0)
    '0'

    Works with Fraction objects too

    >>> from fractions import Fraction
    >>> common.mixedNumeral(Fraction(31, 7))
    '4 3/7'
    >>> common.mixedNumeral(Fraction(1, 5))
    '1/5'
    >>> common.mixedNumeral(Fraction(-1, 5))
    '-1/5'
    >>> common.mixedNumeral(Fraction(-4, 5))
    '-4/5'
    >>> common.mixedNumeral(Fraction(-31, 7))
    '-4 3/7'

    Denominator is limited by default but can be changed.

    >>> common.mixedNumeral(2.0000001)
    '2'
    >>> common.mixedNumeral(2.0000001, limitDenominator=10000000)
    '2 1/10000000'
    '''
    if not isinstance(expr, Fraction):
        quotient, remainder = divmod(float(expr), 1.)
        remainderFrac = Fraction(remainder).limit_denominator(limitDenominator)
        if quotient < -1:
            quotient += 1
            remainderFrac = 1 - remainderFrac
        elif quotient == -1:
            quotient = 0.0
            remainderFrac = remainderFrac - 1
    else:
        quotient = int(float(expr))
        remainderFrac = expr - quotient
        if quotient < 0:
            remainderFrac *= -1

    if quotient:
        if remainderFrac:
            return f'{int(quotient)} {remainderFrac}'
        else:
            return str(int(quotient))
    else:
        if remainderFrac != 0:
            return str(remainderFrac)
    return str(0)


def roundToHalfInteger(num: float | int) -> float | int:
    '''
    Given a floating-point number, round to the nearest half-integer. Returns int or float

    >>> common.roundToHalfInteger(1.2)
    1
    >>> common.roundToHalfInteger(1.35)
    1.5
    >>> common.roundToHalfInteger(1.8)
    2
    >>> common.roundToHalfInteger(1.6234)
    1.5

    0.25 rounds up:

    >>> common.roundToHalfInteger(0.25)
    0.5

    as does 0.75

    >>> common.roundToHalfInteger(0.75)
    1

    unlike python round function, does the same for 1.25 and 1.75

    >>> common.roundToHalfInteger(1.25)
    1.5
    >>> common.roundToHalfInteger(1.75)
    2

    negative numbers however, round up on the boundaries

    >>> common.roundToHalfInteger(-0.26)
    -0.5
    >>> common.roundToHalfInteger(-0.25)
    0
    '''
    intVal, floatVal = divmod(num, 1.0)
    intVal = int(intVal)
    if floatVal < 0.25:
        floatVal = 0
    elif 0.25 <= floatVal < 0.75:
        floatVal = 0.5
    else:
        floatVal = 1
    return intVal + floatVal


def addFloatPrecision(x, grain=1e-2) -> float | Fraction:
    '''
    Given a value that suggests a floating point fraction, like 0.33,
    return a Fraction or float that provides greater specification, such as Fraction(1, 3)

    >>> import fractions
    >>> common.addFloatPrecision(0.333)
    Fraction(1, 3)
    >>> common.addFloatPrecision(0.33)
    Fraction(1, 3)
    >>> common.addFloatPrecision(0.35) == fractions.Fraction(1, 3)
    False
    >>> common.addFloatPrecision(0.2) == 0.2
    True
    >>> common.addFloatPrecision(0.125)
    0.125
    >>> common.addFloatPrecision(1/7) == 1/7
    True
    '''
    if isinstance(x, str):
        x = float(x)

    values = (1 / 3, 2 / 3,
              1 / 6, 5 / 6)
    for v in values:
        if isclose(x, v, abs_tol=grain):
            return opFrac(v)
    return x


def strTrimFloat(floatNum: float, maxNum: int = 4) -> str:
    '''
    returns a string from a float that is at most maxNum of
    decimal digits long, but never less than 1.

    >>> common.strTrimFloat(42.3333333333)
    '42.3333'
    >>> common.strTrimFloat(42.3333333333, 2)
    '42.33'
    >>> common.strTrimFloat(6.66666666666666, 2)
    '6.67'
    >>> common.strTrimFloat(2.0)
    '2.0'
    >>> common.strTrimFloat(-5)
    '-5.0'
    '''
    # variables called 'off' because originally designed for offsets
    offBuildString = r'%.' + str(maxNum) + 'f'
    off = offBuildString % floatNum
    offDecimal = off.index('.')
    offLen = len(off)
    for index in range(offLen - 1, offDecimal + 1, -1):
        if off[index] != '0':
            break
        else:
            offLen = offLen - 1
    off = off[0:offLen]
    return off


def nearestMultiple(n: float, unit: float) -> tuple[float, float, float]:
    '''
    Given a positive value `n`, return the nearest multiple of the supplied `unit` as well as
    the absolute difference (error) to seven significant digits and the signed difference.

    >>> print(common.nearestMultiple(0.25, 0.25))
    (0.25, 0.0, 0.0)
    >>> print(common.nearestMultiple(0.35, 0.25))
    (0.25, 0.1..., 0.1...)
    >>> print(common.nearestMultiple(0.20, 0.25))
    (0.25, 0.05..., -0.05...)

    Note that this one also has an error of 0.1, but it's a positive error off of 0.5

    >>> print(common.nearestMultiple(0.4, 0.25))
    (0.5, 0.1..., -0.1...)

    >>> common.nearestMultiple(0.4, 0.25)[0]
    0.5
    >>> common.nearestMultiple(23404.001, 0.125)[0]
    23404.0
    >>> common.nearestMultiple(23404.134, 0.125)[0]
    23404.125

    Error is always positive, but signed difference can be negative.

    >>> common.nearestMultiple(23404 - 0.0625, 0.125)
    (23403.875, 0.0625, 0.0625)

    >>> common.nearestMultiple(0.001, 0.125)[0]
    0.0

    >>> from math import isclose
    >>> isclose(common.nearestMultiple(0.25, 1 / 3)[0], 0.33333333, abs_tol=1e-7)
    True
    >>> isclose(common.nearestMultiple(0.55, 1 / 3)[0], 0.66666666, abs_tol=1e-7)
    True
    >>> isclose(common.nearestMultiple(234.69, 1 / 3)[0], 234.6666666, abs_tol=1e-7)
    True
    >>> isclose(common.nearestMultiple(18.123, 1 / 6)[0], 18.16666666, abs_tol=1e-7)
    True

    >>> common.nearestMultiple(-0.5, 0.125)
    Traceback (most recent call last):
    ValueError: n (-0.5) is less than zero. Thus, cannot find the nearest
        multiple for a value less than the unit, 0.125
    '''
    if n < 0:
        raise ValueError(f'n ({n}) is less than zero. '
                         + 'Thus, cannot find the nearest multiple for a value '
                         + f'less than the unit, {unit}')

    mult = math.floor(n / unit)  # can start with the floor
    halfUnit = unit / 2.0

    matchLow = unit * mult
    matchHigh = unit * (mult + 1)

    # print(['mult, halfUnit, matchLow, matchHigh', mult, halfUnit, matchLow, matchHigh])

    if matchLow >= n >= matchHigh:
        raise Exception(f'cannot place n between multiples: {matchLow}, {matchHigh}')

    if matchLow <= n <= (matchLow + halfUnit):
        return matchLow, round(n - matchLow, 7), round(n - matchLow, 7)
    else:
        # elif n >= (matchHigh - halfUnit) and n <= matchHigh:
        return matchHigh, round(matchHigh - n, 7), round(n - matchHigh, 7)


_DOT_LOOKUP = (1.0, 1.5, 1.75, 1.875, 1.9375,
               1.96875, 1.984375, 1.9921875, 1.99609375)

def dotMultiplier(dots: int) -> float:
    '''
    dotMultiplier(dots) returns how long to multiply the note
    length of a note in order to get the note length with n dots

    Since dotMultiplier always returns a power of two in the denominator,
    the float will be exact.

    >>> from fractions import Fraction
    >>> Fraction(common.dotMultiplier(1))
    Fraction(3, 2)
    >>> Fraction(common.dotMultiplier(2))
    Fraction(7, 4)
    >>> Fraction(common.dotMultiplier(3))
    Fraction(15, 8)

    >>> common.dotMultiplier(0)
    1.0
    '''
    if dots < 9:
        return _DOT_LOOKUP[dots]

    return ((2 ** (dots + 1.0)) - 1.0) / (2 ** dots)


def decimalToTuplet(decNum: float) -> tuple[int, int]:
    '''
    For simple decimals (usually > 1), a quick way to figure out the
    fraction in lowest terms that gives a valid tuplet.

    No it does not work really fast.  No it does not return tuplets with
    denominators over 100.  Too bad, math geeks.  This is real life.  :-)

    returns (numerator, denominator)

    >>> common.decimalToTuplet(1.5)
    (3, 2)
    >>> common.decimalToTuplet(1.25)
    (5, 4)

    If decNum is < 1, the denominator will be greater than the numerator:

    >>> common.decimalToTuplet(0.8)
    (4, 5)

    If decNum is <= 0, returns a ZeroDivisionError:

    >>> common.decimalToTuplet(-.02)
    Traceback (most recent call last):
    ZeroDivisionError: number must be greater than zero
    '''
    def findSimpleFraction(inner_working):
        '''
        Utility function.
        '''
        for index in range(1, 1000):
            for j in range(index, index * 2):
                if isclose(inner_working, j / index, abs_tol=1e-7):
                    return (int(j), int(index))
        return (0, 0)

    flipNumerator = False
    if decNum <= 0:
        raise ZeroDivisionError('number must be greater than zero')
    if decNum < 1:
        flipNumerator = True
        decNum = 1 / decNum

    unused_remainder, multiplier = math.modf(decNum)
    working = decNum / multiplier

    (jy, iy) = findSimpleFraction(working)

    if iy == 0:
        raise Exception('No such luck')

    jy *= multiplier
    my_gcd = gcd(int(jy), int(iy))
    jy = jy / my_gcd
    iy = iy / my_gcd

    if flipNumerator is False:
        return (int(jy), int(iy))
    else:
        return (int(iy), int(jy))


def unitNormalizeProportion(values: Sequence[int | float]) -> list[float]:
    '''
    Normalize values within the unit interval, where max is determined by the sum of the series.

    >>> common.unitNormalizeProportion([0, 3, 4])
    [0.0, 0.42857142857142855, 0.5714285714285714]
    >>> common.unitNormalizeProportion([1, 1, 1])
    [0.3333333..., 0.333333..., 0.333333...]

    Works fine with a mix of ints and floats:

    >>> common.unitNormalizeProportion([1.0, 1, 1.0])
    [0.3333333..., 0.333333..., 0.333333...]


    On 32-bit computers this number may be inexact even for small floats.
    On 64-bit it works fine.  This is the 32-bit output for this result.

        common.unitNormalizeProportion([0.2, 0.6, 0.2])
        [0.20000000000000001, 0.59999999999999998, 0.20000000000000001]

    Negative values should be shifted to positive region first:

    >>> common.unitNormalizeProportion([0, -2, -8])
    Traceback (most recent call last):
    ValueError: value members must be positive
    '''
    summation = 0.0
    for x in values:
        if x < 0.0:
            raise ValueError('value members must be positive')
        summation += x
    unit = []  # weights on the unit interval; sum == 1
    for x in values:
        unit.append((x / summation))
    return unit


def unitBoundaryProportion(
    series: Sequence[int | float]
) -> list[tuple[int | float, float]]:
    '''
    Take a series of parts with an implied sum, and create
    unit-interval boundaries proportional to the series components.

    >>> common.unitBoundaryProportion([1, 1, 2])
    [(0.0, 0.25), (0.25, 0.5), (0.5, 1.0)]
    >>> common.unitBoundaryProportion([9, 1, 1])
    [(0.0, 0.8...), (0.8..., 0.9...), (0.9..., 1.0)]
    '''
    unit = unitNormalizeProportion(series)
    bounds = []
    summation = 0.0
    for index in range(len(unit)):
        if index != len(unit) - 1:  # not last
            bounds.append((summation, summation + unit[index]))
            summation += unit[index]
        else:  # last, avoid rounding errors
            bounds.append((summation, 1.0))
    return bounds


def weightedSelection(values: list[int],
                      weights: list[int | float],
                      randomGenerator=None) -> int:
    '''
    Given a list of values and an equal-sized list of weights,
    return a randomly selected value using the weight.

    Example: sum -1 and 1 for 100 values; should be
    around 0 or at least between -50 and 50 (99.99999% of the time)

    >>> -50 < sum([common.weightedSelection([-1, 1], [1, 1]) for x in range(100)]) < 50
    True
    '''
    # See http://www.wolframalpha.com/input/?i=Probability+of+76+or+more+heads+in+100+coin+tosses
    # for probability.  When it was -30 to 30, failed 1 in 500 times.
    if randomGenerator is not None:
        q = randomGenerator()  # must be in unit interval
    else:  # use random uniform
        q = random.random()
    # normalize weights w/n unit interval
    boundaries = unitBoundaryProportion(weights)
    index = 0
    for index, (low, high) in enumerate(boundaries):
        if low <= q < high:  # accepts both boundaries
            return values[index]
    # just in case we get the high boundary
    return values[index]


def approximateGCD(values: Collection[int | float], grain: float = 1e-4) -> float:
    '''
    Given a list of values, find the lowest common divisor of floating point values.

    >>> common.approximateGCD([2.5, 10, 0.25])
    0.25
    >>> common.approximateGCD([2.5, 10])
    2.5
    >>> common.approximateGCD([2, 10])
    2.0
    >>> common.approximateGCD([1.5, 5, 2, 7])
    0.5
    >>> common.approximateGCD([2, 5, 10])
    1.0
    >>> common.approximateGCD([2, 5, 10, 0.25])
    0.25
    >>> common.strTrimFloat(common.approximateGCD([1/3, 2/3]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3, 2/3, 4]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3, 2/3, 5]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3, 2/3, 5/6, 3/6]))
    '0.1667'
    '''
    lowest = float(min(values))

    # quick method: see if the smallest value is a common divisor of the rest
    count = 0
    for x in values:
        x_adjust = x / lowest
        floatingValue = x_adjust - int(x_adjust)
        # if almost an even division
        if isclose(floatingValue, 0.0, abs_tol=grain):
            count += 1
    if count == len(values):
        return lowest

    # assume that one of these divisions will match
    divisors = (1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13., 14., 15., 16.)
    divisions = []  # a list of lists, one for each entry
    uniqueDivisions = set()
    for index in values:
        coll = []
        for d in divisors:
            v = index / d
            coll.append(v)  # store all divisions
            uniqueDivisions.add(v)
        divisions.append(coll)
    # find a unique divisor that is found in collected divisors
    commonUniqueDivisions = []
    for v in uniqueDivisions:
        count = 0
        for coll in divisions:
            for x in coll:
                # grain here is set low, mostly to catch triplets
                if isclose(x, v, abs_tol=grain):
                    count += 1
                    break  # exit the iteration of coll; only 1 match possible
        # store any division that is found in all values
        if count == len(divisions):
            commonUniqueDivisions.append(v)
    if not commonUniqueDivisions:
        raise Exception('cannot find a common divisor')
    return max(commonUniqueDivisions)


@deprecated('v9', 'v10', 'Use math.lcm instead')
def lcm(filterList: Iterable[int]) -> int:
    '''
    Find the least common multiple of a list of values

    common.lcm([3, 4, 5])
    60
    common.lcm([3, 4])
    12
    common.lcm([1, 2])
    2
    common.lcm([3, 6])
    6

    Works with any iterable, like this set

    common.lcm({3, 5, 6})
    30

    Deprecated in v9 since Python 3.10 is the minimum version
    and math.lcm works in C and is faster
    '''
    def _lcm(a, b):
        '''
        find the least common multiple of a, b
        '''
        # // forces integer style division (no remainder)
        return abs(a * b) // gcd(a, b)

    # derived from
    # http://www.oreillynet.com/cs/user/view/cs_msg/41022
    lcmVal = 1
    for flValue in filterList:
        lcmVal = _lcm(lcmVal, flValue)
    return lcmVal


def contiguousList(inputListOrTuple) -> bool:
    '''
    returns bool True or False if a list containing ints
    contains only contiguous (increasing) values

    requires the list to be sorted first


    >>> l = [3, 4, 5, 6]
    >>> common.contiguousList(l)
    True
    >>> l.append(8)
    >>> common.contiguousList(l)
    False

    Sorting matters

    >>> l.append(7)
    >>> common.contiguousList(l)
    False
    >>> common.contiguousList(sorted(l))
    True
    '''
    currentMaxVal = inputListOrTuple[0]
    for index in range(1, len(inputListOrTuple)):
        newVal = inputListOrTuple[index]
        if newVal != currentMaxVal + 1:
            return False
        currentMaxVal += 1
    return True


def groupContiguousIntegers(src: list[int]) -> list[list[int]]:
    '''
    Given a list of integers, group contiguous values into sub lists

    >>> common.groupContiguousIntegers([3, 5, 6])
    [[3], [5, 6]]
    >>> common.groupContiguousIntegers([3, 4, 6])
    [[3, 4], [6]]
    >>> common.groupContiguousIntegers([3, 4, 6, 7])
    [[3, 4], [6, 7]]
    >>> common.groupContiguousIntegers([3, 4, 6, 7, 20])
    [[3, 4], [6, 7], [20]]
    >>> common.groupContiguousIntegers([3, 4, 5, 6, 7])
    [[3, 4, 5, 6, 7]]
    >>> common.groupContiguousIntegers([3])
    [[3]]
    >>> common.groupContiguousIntegers([3, 200])
    [[3], [200]]
    '''
    if len(src) <= 1:
        return [src]
    post = []
    group = []
    src.sort()
    i = 0
    while i < (len(src) - 1):
        e = src[i]
        group.append(e)
        eNext = src[i + 1]
        # if next is contiguous, add to group
        if eNext != e + 1:
            # if not contiguous
            post.append(group)
            group = []
        # second to last elements; handle separately
        if i == len(src) - 2:
            # need to handle next elements
            group.append(eNext)
            post.append(group)

        i += 1

    return post


# noinspection SpellCheckingInspection
def fromRoman(num: str, *, strictModern=False) -> int:
    '''

    Convert a Roman numeral (upper or lower) to an int

    https://code.activestate.com/recipes/81611-roman-numerals/


    >>> common.fromRoman('ii')
    2
    >>> common.fromRoman('vii')
    7

    Works with both IIII and IV forms:

    >>> common.fromRoman('MCCCCLXXXIX')
    1489
    >>> common.fromRoman('MCDLXXXIX')
    1489


    Some people consider this an error, but you see it in medieval and ancient roman documents:

    >>> common.fromRoman('ic')
    99

    unless strictModern is True

    >>> common.fromRoman('ic', strictModern=True)
    Traceback (most recent call last):
    ValueError: input contains an invalid subtraction element (modern interpretation): ic


    But things like this are never seen, and thus cause an error:

    >>> common.fromRoman('vx')
    Traceback (most recent call last):
    ValueError: input contains an invalid subtraction element: vx
    '''
    inputRoman = num.upper()
    subtractionValues = (1, 10, 100)
    nums = ('M', 'D', 'C', 'L', 'X', 'V', 'I')
    ints = (1000, 500, 100, 50, 10, 5, 1)
    places = []
    for c in inputRoman:
        if c not in nums:
            raise ValueError(f'value is not a valid roman numeral: {inputRoman}')

    for i in range(len(inputRoman)):
        c = inputRoman[i]
        value = ints[nums.index(c)]
        # If the next place holds a larger number, this value is negative.
        try:
            nextValue = ints[nums.index(inputRoman[i + 1])]
            if nextValue > value and value in subtractionValues:
                if strictModern and nextValue >= value * 10:
                    raise ValueError(
                        'input contains an invalid subtraction element '
                        + f'(modern interpretation): {num}')

                value *= -1
            elif nextValue > value:
                raise ValueError(
                    f'input contains an invalid subtraction element: {num}')
        except IndexError:
            # there is no next place.
            pass
        places.append(value)
    summation = 0
    for n in places:
        summation += n
    return summation


# noinspection SpellCheckingInspection
def toRoman(num: int) -> str:
    '''
    Convert a number from 1 to 3999 to a roman numeral

    >>> common.toRoman(2)
    'II'
    >>> common.toRoman(7)
    'VII'
    >>> common.toRoman(1999)
    'MCMXCIX'

    >>> common.toRoman('hi')
    Traceback (most recent call last):
    TypeError: expected integer, got <... 'str'>

    >>> common.toRoman(0)
    Traceback (most recent call last):
    ValueError: Argument must be between 1 and 3999
    '''
    if not isinstance(num, int):
        raise TypeError(f'expected integer, got {type(num)}')
    if not 0 < num < 4000:
        raise ValueError('Argument must be between 1 and 3999')
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = ''
    for i in range(len(ints)):
        count = int(num / ints[i])
        result += nums[i] * count
        num -= ints[i] * count
    return result


def ordinalAbbreviation(value: int, plural=False) -> str:
    '''
    Return the ordinal abbreviations for integers

    >>> common.ordinalAbbreviation(3)
    'rd'
    >>> common.ordinalAbbreviation(255)
    'th'
    >>> common.ordinalAbbreviation(255, plural=True)
    'ths'
    '''
    valueHundredths = value % 100
    if valueHundredths in (11, 12, 13):
        post = 'th'
    else:
        valueMod = value % 10
        if valueMod == 1:
            post = 'st'
        elif valueMod in (0, 4, 5, 6, 7, 8, 9):
            post = 'th'
        elif valueMod == 2:
            post = 'nd'
        elif valueMod == 3:
            post = 'rd'
        else:
            raise ValueError('Something really weird')  # pragma: no cover

    if post != 'st' and plural:
        post += 's'
    return post


ordinalsToNumbers = {}
for ordinal_index in range(len(ordinals)):
    ordinalName = ordinals[ordinal_index]
    ordinalNameLower = ordinalName.lower()
    ordinalsToNumbers[ordinalName] = ordinal_index
    ordinalsToNumbers[ordinalNameLower] = ordinal_index
    ordinalsToNumbers[str(ordinal_index) + ordinalAbbreviation(ordinal_index)] = ordinal_index

    musicOrdinalName = musicOrdinals[ordinal_index]
    if musicOrdinalName != ordinalName:
        musicOrdinalNameLower = musicOrdinalName.lower()
        ordinalsToNumbers[musicOrdinalName] = ordinal_index
        ordinalsToNumbers[musicOrdinalNameLower] = ordinal_index

del ordinal_index


class Test(unittest.TestCase):
    '''
    Tests not requiring file output.
    '''

    def setUp(self):
        pass

    def testToRoman(self):
        for src, dst in [(1, 'I'), (3, 'III'), (5, 'V')]:
            self.assertEqual(dst, toRoman(src))

    def testOrdinalsToNumbers(self):
        self.assertEqual(ordinalsToNumbers['unison'], 1)
        self.assertEqual(ordinalsToNumbers['Unison'], 1)
        self.assertEqual(ordinalsToNumbers['first'], 1)
        self.assertEqual(ordinalsToNumbers['First'], 1)
        self.assertEqual(ordinalsToNumbers['1st'], 1)
        self.assertEqual(ordinalsToNumbers['octave'], 8)
        self.assertEqual(ordinalsToNumbers['Octave'], 8)
        self.assertEqual(ordinalsToNumbers['eighth'], 8)
        self.assertEqual(ordinalsToNumbers['Eighth'], 8)
        self.assertEqual(ordinalsToNumbers['8th'], 8)

    def testWeightedSelection(self):
        # test equal selection
        for j in range(10):
            x = 0
            for i in range(1000):
                # equal chance of -1, 1
                x += weightedSelection([-1, 1], [1, 1])
            # environLocal.printDebug(['weightedSelection([-1, 1], [1, 1])', x])
            self.assertTrue(-250 < x < 250)

        # test a strongly weighed boundary
        for j in range(10):
            x = 0
            for i in range(1000):
                # 10000 more chance of 0 than 1.
                x += weightedSelection([0, 1], [10000, 1])
            # environLocal.printDebug(['weightedSelection([0, 1], [10000, 1])', x])
            self.assertTrue(0 <= x < 20)

        for j in range(10):
            x = 0
            for i in range(1000):
                # 10,000 times more likely 1 than 0.
                x += weightedSelection([0, 1], [1, 10000])
            # environLocal.printDebug(['weightedSelection([0, 1], [1, 10000])', x])
            self.assertTrue(900 <= x <= 1000)

        for unused_j in range(10):
            x = 0
            for i in range(1000):
                # no chance of anything but 0.
                x += weightedSelection([0, 1], [1, 0])
            # environLocal.printDebug(['weightedSelection([0, 1], [1, 0])', x])
            self.assertEqual(x, 0)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [fromRoman, toRoman]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
