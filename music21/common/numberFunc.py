#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/numberFunc.py
# Purpose:      Utilities for working with numbers or number-like objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import math
import random
import unittest

from fractions import Fraction
from music21 import defaults

from music21.exceptions21 import Music21CommonException

from music21.ext import six

__all__ = ['ordinals', 'musicOrdinals',
           
           'cleanupFloat',
           'numToIntOrFloat', 
           
           'opFrac', 'mixedNumeral',
           'roundToHalfInteger', 'almostEquals',
           'addFloatPrecision', 'strTrimFloat', 
           'nearestMultiple',
           'standardDeviation',
           
           'dotMultiplier', 'decimalToTuplet',
           'unitNormalizeProportion', 'unitBoundaryProportion',
           'weightedSelection', 
           'euclidGCD', 'approximateGCD',
           'lcm',
           
           'contiguousList',
           
           'groupContiguousIntegers',
           
           'fromRoman', 'toRoman',
           'ordinalAbbreviation',
           ]

ordinals = ["Zeroth","First","Second","Third","Fourth","Fifth",
            "Sixth","Seventh","Eighth","Ninth","Tenth","Eleventh",
            "Twelfth","Thirteenth","Fourteenth","Fifteenth",
            "Sixteenth","Seventeenth","Eighteenth","Nineteenth",
            "Twentieth","Twenty-first","Twenty-second"]

musicOrdinals = ordinals[:]
musicOrdinals[1] = "Unison"
musicOrdinals[8] = "Octave"
musicOrdinals[15] = "Double-octave"
musicOrdinals[22] = "Triple-octave"




def cleanupFloat(floatNum, maxDenominator=defaults.limitOffsetDenominator):
    '''
    Cleans up a floating point number by converting
    it to a fractions.Fraction object limited to
    a denominator of maxDenominator


    >>> common.cleanupFloat(0.33333327824)
    0.333333333333...

    >>> common.cleanupFloat(0.142857)
    0.1428571428571...

    >>> common.cleanupFloat(1.5)
    1.5

    Fractions are passed through silently...
    
    >>> import fractions
    >>> common.cleanupFloat(fractions.Fraction(4, 3))
    Fraction(4, 3)

    '''
    if isinstance(floatNum, Fraction):
        return floatNum # do nothing to fractions
    else:
        f = Fraction(floatNum).limit_denominator(maxDenominator)
        return float(f)

#------------------------------------------------------------------------------
# Number methods...


def numToIntOrFloat(value):
    '''Given a number, return an integer if it is very close to an integer, otherwise, return a float.


    >>> common.numToIntOrFloat(1.0)
    1
    >>> common.numToIntOrFloat(1.00003)
    1.00003
    >>> common.numToIntOrFloat(1.5)
    1.5
    >>> common.numToIntOrFloat(1.0000000005)
    1
    
    :rtype: float
    '''
    intVal = int(round(value))
    if almostEquals(intVal, value, 1e-6):
        return intVal
    else: # source
        return value


DENOM_LIMIT = defaults.limitOffsetDenominator


def _preFracLimitDenominator(n, d):
    '''
    Copied from fractions.limit_denominator.  Their method
    requires creating three new Fraction instances to get one back. this doesn't create any
    call before Fraction...
    
    DENOM_LIMIT is hardcoded to defaults.limitOffsetDenominator for speed...
    
    returns a new n, d...
    
    >>> common.numberFunc._preFracLimitDenominator(100001, 300001)
    (1, 3)
    
    >>> from fractions import Fraction
    >>> Fraction(100000000001, 300000000001).limit_denominator(65535)
    Fraction(1, 3)
    >>> Fraction(100001, 300001).limit_denominator(65535)
    Fraction(1, 3)
    
    Timing differences are huge!

    t is timeit.timeit
    
    t('Fraction(*common.numberFunc._preFracLimitDenominator(*x.as_integer_ratio()))', 
       setup='x = 1000001/3000001.; from music21 import common;from fractions import Fraction', 
       number=100000)
    1.0814228057861328
    
    t('Fraction(x).limit_denominator(65535)', 
       setup='x = 1000001/3000001.; from fractions import Fraction', 
       number=100000)
    7.941488981246948
    
    Proof of working...
    
    >>> import random
    >>> myWay = lambda x: Fraction(*common.numberFunc._preFracLimitDenominator(*x.as_integer_ratio()))
    >>> theirWay = lambda x: Fraction(x).limit_denominator(65535)

    >>> for i in range(50):
    ...     x = random.random()
    ...     if myWay(x) != theirWay(x):
    ...         print("boo: %s, %s, %s" % (x, myWay(x), theirWay(x)))
    
    (n.b. -- nothing printed)
    
    '''
    nOrg = n
    dOrg = d
    if (d <= DENOM_LIMIT):
        return (n, d)
    p0, q0, p1, q1 = 0, 1, 1, 0
    while True:
        a = n//d
        q2 = q0+a*q1
        if q2 > DENOM_LIMIT:
            break
        p0, q0, p1, q1 = p1, q1, p0+a*p1, q2
        n, d = d, n-a*d

    k = (DENOM_LIMIT-q0)//q1
    bound1n = p0+k*p1
    bound1d = q0+k*q1
    bound2n = p1
    bound2d = q1
    #s = (0.0 + n)/d
    bound1minusS = (abs((bound1n * dOrg) - (nOrg * bound1d)), (dOrg * bound1d))
    bound2minusS = (abs((bound2n * dOrg) - (nOrg * bound2d)), (dOrg * bound2d))
    difference = (bound1minusS[0] * bound2minusS[1]) - (bound2minusS[0] * bound1minusS[1])
    if difference > 0:
        # bound1 is farther from zero than bound2; return bound2
        return (p1, q1)
    else:
        return (p0 + k*p1, q0 + k * q1)
    
    

def opFrac(num):
    '''
    opFrac -> optionally convert a number to a fraction or back.
    
    Important music21 2.x function for working with offsets and quarterLengths
    
    Takes in a number (or None) and converts it to a Fraction with denominator
    less than limitDenominator if it is not binary expressible; otherwise return a float.  
    Or if the Fraction can be converted back to a binary expressable
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
    >>> common.opFrac(1.0/3)
    Fraction(1, 3)
    >>> common.opFrac(1.0/4)
    0.25
    >>> f = Fraction(1,3)
    >>> common.opFrac(f + f + f)
    1.0
    >>> common.opFrac(0.123456789)
    Fraction(10, 81)
    >>> common.opFrac(None) is None
    True
    
    :type num: float
    '''
    # This is a performance critical operation, tuned to go as fast as possible.
    # hence redundancy -- first we check for type (no inheritance) and then we
    # repeat exact same test with inheritence. Note that the later examples are more verbose
    t = type(num)
    if t is float:
        # quick test of power of whether denominator is a power
        # of two, and thus representable exactly as a float: can it be
        # represented w/ a denominator less than DENOM_LIMIT?
        # this doesn't work:
        #    (denominator & (denominator-1)) != 0
        # which is a nice test, but denominator here is always a power of two...
        #unused_numerator, denominator = num.as_integer_ratio() # too slow
        ir = num.as_integer_ratio()
        if ir[1] > DENOM_LIMIT: # slightly faster[SIC!] than hardcoding 65535!
            return Fraction(*_preFracLimitDenominator(*ir)) # way faster!
            #return Fraction(*ir).limit_denominator(DENOM_LIMIT) # *ir instead of float -- this happens
                # internally in Fraction constructor, but is twice as fast...
        else:
            return num
    elif t is int:
        return num + 0.0 # 8x faster than float(num)
    elif t is Fraction:
        d = num._denominator # private access instead of property: 6x faster; may break later...
        if (d & (d-1)) == 0: # power of two...
            return num._numerator/(d + 0.0) # 50% faster than float(num)
        else:
            return num # leave fraction alone
    elif num is None:
        return None
    
    # class inheritance only check AFTER ifs...
    elif isinstance(num, int):
        return num + 0.0
    elif isinstance(num, float):
        ir = num.as_integer_ratio()
        if ir[1] > DENOM_LIMIT: # slightly faster than hardcoding 65535!
            return Fraction(*_preFracLimitDenominator(*ir)) # way faster!
        else:
            return num
        
    elif isinstance(num, Fraction):
        d = num._denominator # private access instead of property: 6x faster; may break later...
        if (d & (d-1)) == 0: # power of two...
            return num._numerator/(d + 0.0) # 50% faster than float(num)
        else:
            return num # leave fraction alone
    else:
        raise TypeError("Cannot convert num: %r" % num)
        


def mixedNumeral(expr, limitDenominator=defaults.limitOffsetDenominator):
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
    >>> common.mixedNumeral( Fraction(31,7) )
    '4 3/7'
    >>> common.mixedNumeral( Fraction(1,5) )
    '1/5'
    >>> common.mixedNumeral( Fraction(-1,5) )
    '-1/5'
    >>> common.mixedNumeral( Fraction(-31,7) )
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
        quotient = int(expr)
        remainderFrac = expr - quotient
        if (quotient < 0):
            remainderFrac *= -1
    
    if quotient:
        if remainderFrac:
            return '{} {}'.format(int(quotient), remainderFrac)
        else:
            return str(int(quotient))
    else:
        if remainderFrac != 0:
            return str(remainderFrac)
    return str(0)

def roundToHalfInteger(num):
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
    
    .25 rounds up:
    
    >>> common.roundToHalfInteger(0.25)
    0.5
    
    as does .75
    
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
    
    
    
    :rtype: float
    '''
    intVal, floatVal = divmod(num, 1.0)
    intVal = int(intVal)
    if floatVal < .25:
        floatVal = 0
    elif floatVal >= .25 and floatVal < .75 :
        floatVal = .5
    else:
        floatVal = 1
    return intVal + floatVal


def almostEquals(x, y = 0.0, grain=1e-7):
    '''
    almostEquals(x, y) -- returns True if x and y are within grain (default  0.0000001) of each other

    Allows comparisons between floats that are normally inconsistent.

    >>> common.almostEquals(1.000000001, 1)
    True
    >>> common.almostEquals(1.001, 1)
    False
    >>> common.almostEquals(1.001, 1, grain=0.1)
    True

    For very small grains, just compare Fractions without converting...

    :rtype: bool
    '''
    # for very small grains, just compare Fractions without converting...
    if (isinstance(x, Fraction) and isinstance(y, Fraction) and grain <= 5e-6):
        if x == y:
            return True
    
    if abs(x - y) < grain:
        return True
    return False


def addFloatPrecision(x, grain=1e-2):
    '''
    Given a value that suggests a floating point fraction, like .33,
    return a Fraction or float that provides greater specification, such as .333333333



    >>> import fractions
    >>> common.addFloatPrecision(.333)
    Fraction(1, 3)
    >>> common.addFloatPrecision(.33)
    Fraction(1, 3)
    >>> common.addFloatPrecision(.35) == fractions.Fraction(1, 3)
    False
    >>> common.addFloatPrecision(.2) == 0.2
    True
    >>> common.addFloatPrecision(.125)
    0.125
    >>> common.addFloatPrecision(1./7) == 1./7
    True
    
    :rtype: float
    '''
    if isinstance(x, six.string_types):
        x = float(x)

    values = (1/3., 2/3.,
              1/6., 5/6.)
    for v in values:
        if almostEquals(x, v, grain=grain):
            return opFrac(v)
    return x


def strTrimFloat(floatNum, maxNum = 4):
    '''
    returns a string from a float that is at most maxNum of
    decimial digits long, but never less than 1.
    
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
    # variables called "off" because originally designed for offsets
    offBuildString = r'%.' + str(maxNum) + 'f'
    off = offBuildString % floatNum
    offDecimal = off.index('.')
    offLen = len(off)
    for i in range(offLen - 1, offDecimal + 1, -1):
        if off[i] != '0':
            break
        else:
            offLen = offLen - 1
    off = off[0:offLen]
    return off


def nearestMultiple(n, unit):
    '''
    Given a positive value `n`, return the nearest multiple of the supplied `unit` as well as 
    the absolute difference (error) to seven significant digits and the signed difference.

    >>> print(common.nearestMultiple(.25, .25))
    (0.25, 0.0, 0.0)
    >>> print(common.nearestMultiple(.35, .25))
    (0.25, 0.1..., 0.1...)
    >>> print(common.nearestMultiple(.20, .25))
    (0.25, 0.05..., -0.05...)

    Note that this one also has an error of .1 but it's a positive error off of 0.5
    >>> print(common.nearestMultiple(.4, .25))
    (0.5, 0.1..., -0.1...)

    >>> common.nearestMultiple(.4, .25)[0]
    0.5
    >>> common.nearestMultiple(23404.001, .125)[0]
    23404.0
    >>> common.nearestMultiple(23404.134, .125)[0]
    23404.125
    
    Error is always positive, but signed difference can be negative.
    
    >>> common.nearestMultiple(23404 - 0.0625, .125)
    (23404.0, 0.0625, -0.0625)

    >>> common.nearestMultiple(.001, .125)[0]
    0.0

    >>> common.almostEquals(common.nearestMultiple(.25, (1/3.))[0], .33333333)
    True
    >>> common.almostEquals(common.nearestMultiple(.55, (1/3.))[0], .66666666)
    True
    >>> common.almostEquals(common.nearestMultiple(234.69, (1/3.))[0], 234.6666666)
    True
    >>> common.almostEquals(common.nearestMultiple(18.123, (1/6.))[0], 18.16666666)
    True


    >>> common.nearestMultiple(-0.5, 0.125)
    Traceback (most recent call last):
    ValueError: n (-0.5) is less than zero. Thus cannot find nearest multiple for a value less than the unit, 0.125


    :rtype: tuple(float)
    '''
    if n < 0:
        raise ValueError('n (%s) is less than zero. Thus cannot find nearest multiple for a value less than the unit, %s' % (n, unit))

    mult = math.floor(n / float(unit)) # can start with the floor
    halfUnit = unit / 2.0

    matchLow = unit * mult
    matchHigh = unit * (mult + 1)

    #print(['mult, halfUnit, matchLow, matchHigh', mult, halfUnit, matchLow, matchHigh])

    if matchLow >= n >= matchHigh:
        raise Exception('cannot place n between multiples: %s, %s', matchLow, matchHigh)

    if n >= matchLow and n < (matchLow + halfUnit):
        return matchLow, round(n - matchLow, 7), round(n - matchLow, 7)
    elif n >= (matchHigh - halfUnit) and n <= matchHigh:
        return matchHigh, round(matchHigh - n, 7), round(n - matchHigh, 7)


def standardDeviation(coll, bassel=False):
    '''Given a collection of values, return the standard deviation.

    >>> common.standardDeviation([2,4,4,4,5,5,7,9])
    2.0
    >>> common.standardDeviation([600, 470, 170, 430, 300])
    147.3227...
    >>> common.standardDeviation([4, 2, 5, 8, 6], bassel=True)
    2.23606...

    :rtype: float
    '''
    avg = sum(coll) / float(len(coll))
    diffColl = [math.pow(val-avg, 2) for val in coll]
    # with a sample standard deviation (not a whole population)
    # subtract 1 from the length
    # this is bassel's correction
    if bassel:
        return math.sqrt(sum(diffColl) / float(len(diffColl)-1))
    else:
        return math.sqrt(sum(diffColl) / float(len(diffColl)))


def dotMultiplier(dots):
    '''
    dotMultiplier(dots) returns how long to multiply the note length of a note in order to get the note length with n dots

    >>> common.dotMultiplier(1)
    Fraction(3, 2)
    >>> common.dotMultiplier(2)
    Fraction(7, 4)
    >>> common.dotMultiplier(3)
    Fraction(15, 8)
    
    :rtype: Fraction
    '''
    x = (((2**(dots+1.0))-1.0)/(2**dots))
    return Fraction(x)



def decimalToTuplet(decNum):
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

    >>> common.decimalToTuplet(.8)
    (4, 5)

    If decNum is <= 0, returns a ZeroDivisionError:

    >>> common.decimalToTuplet(-.02)
    Traceback (most recent call last):
    ZeroDivisionError: number must be greater than zero

    TODO: replace with fractions...
    
    :rtype: tuple(int)
    '''

    def findSimpleFraction(working):
        'Utility function.'
        for i in range(1,1000):
            for j in range(i,2*i):
                if almostEquals(working, (j+0.0)/i):
                    return (int(j), int(i))
        return (0,0)

    flipNumerator = False
    if decNum <= 0:
        raise ZeroDivisionError("number must be greater than zero")
    if decNum < 1:
        flipNumerator = True
        decNum = 1.0/decNum

    unused_remainder, multiplier = math.modf(decNum)
    working = decNum/multiplier

    (jy, iy) = findSimpleFraction(working)

    if iy == 0:
        raise Exception("No such luck")

    jy *= multiplier
    gcd = euclidGCD(int(jy), int(iy))
    jy = jy/gcd
    iy = iy/gcd

    if flipNumerator is False:
        return (int(jy), int(iy))
    else:
        return (int(iy), int(jy))




def unitNormalizeProportion(values):
    """Normalize values within the unit interval, where max is determined by the sum of the series.


    >>> common.unitNormalizeProportion([0,3,4])
    [0.0, 0.42857142857142855, 0.5714285714285714]
    >>> common.unitNormalizeProportion([1,1,1])
    [0.3333333..., 0.333333..., 0.333333...]


    On 32-bit computers this number is inexact.  On 64-bit it works fine.


    #>>> common.unitNormalizeProportion([.2, .6, .2])
    #[0.20000000000000001, 0.59999999999999998, 0.20000000000000001]


    :rtype: list(float)
    """
    # note: negative values should be shifted to positive region first
    summation = 0
    for x in values:
        if x < 0:
            raise ValueError('value members must be positive')
        summation += x
    unit = [] # weights on the unit interval; sum == 1
    for x in values:
        unit.append((x / float(summation)))
    return unit

def unitBoundaryProportion(series):
    """Take a series of parts with an implied sum, and create unit-interval boundaries proportional to the series components.


    >>> common.unitBoundaryProportion([1,1,2])
    [(0, 0.25), (0.25, 0.5), (0.5, 1.0)]
    >>> common.unitBoundaryProportion([8,1,1])
    [(0, 0.8...), (0.8..., 0.9...), (0.9..., 1.0)]


    :rtype: list(tuple(float))
    """
    unit = unitNormalizeProportion(series)
    bounds = []
    summation = 0
    for i in range(len(unit)):
        if i != len(unit) - 1: # not last
            bounds.append((summation, summation + unit[i]))
            summation += unit[i]
        else: # last, avoid rounding errors
            bounds.append((summation, 1.0))
    return bounds


def weightedSelection(values, weights, randomGenerator=None):
    '''
    Given a list of values and an equal-sized list of weights,
    return a randomly selected value using the weight.

    Example: sum -1 and 1 for 100 values; should be
    around 0 or at least between -30 and 30


    >>> -30 < sum([common.weightedSelection([-1, 1], [1,1]) for x in range(100)]) < 30
    True


    :rtype: int
    '''
    if randomGenerator is not None:
        q = randomGenerator() # must be in unit interval
    else: # use random uniform
        q = random.random()
    # normalize weights w/n unit interval
    boundaries = unitBoundaryProportion(weights)
    i = 0
    for i, (low, high) in enumerate(boundaries):
        if q >= low and q < high: # accepts both boundaries
            return values[i]
    # just in case we get the high boundary
    return values[i]


def euclidGCD(a, b):
    '''use Euclid\'s algorithm to find the GCD of a and b


    >>> common.euclidGCD(2,4)
    2
    >>> common.euclidGCD(20,8)
    4
    >>> common.euclidGCD(20,16)
    4
    
    :rtype: int
    '''
    if b == 0:
        return a
    else:
        return euclidGCD(b, a % b)


def approximateGCD(values, grain=1e-4):
    '''Given a list of values, find the lowest common divisor of floating point values.

    >>> common.approximateGCD([2.5,10, .25])
    0.25
    >>> common.approximateGCD([2.5,10])
    2.5
    >>> common.approximateGCD([2,10])
    2.0
    >>> common.approximateGCD([1.5, 5, 2, 7])
    0.5
    >>> common.approximateGCD([2,5,10])
    1.0
    >>> common.approximateGCD([2,5,10,.25])
    0.25
    >>> common.strTrimFloat(common.approximateGCD([1/3.,2/3.]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3.,2/3.,4]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3.,2/3.,5]))
    '0.3333'
    >>> common.strTrimFloat(common.approximateGCD([5/3.,2/3.,5/6.,3/6.]))
    '0.1667'

    :rtype: float
    '''
    lowest = float(min(values))

    # quick method: see if the smallest value is a common divisor of the rest
    count = 0
    for x in values:
        # lowest is already a float
        unused_int, floatingValue = divmod(x / lowest, 1.0)
        # if almost an even division
        if almostEquals(floatingValue, 0.0, grain=grain):
            count += 1
    if count == len(values):
        return lowest

    # assume that one of these divisions will match
    divisors = [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 11., 12., 13., 14., 15., 16.]
    divisions = [] # a list of lists, one for each entry
    uniqueDivisions = []
    for i in values:
        coll = []
        for d in divisors:
            v = i / d
            coll.append(v) # store all divisions
            if v not in uniqueDivisions:
                uniqueDivisions.append(v)
        divisions.append(coll)
    # find a unique divisor that is found in collected divisors
    commonUniqueDivisions = []
    for v in uniqueDivisions:
        count = 0
        for coll in divisions:
            for x in coll:
                # grain here is set low, mostly to catch triplets
                if almostEquals(x, v, grain=grain):
                    count += 1
                    break # exit the iteration of coll; only 1 match possible
        # store any division that is found in all values
        if count == len(divisions):
            commonUniqueDivisions.append(v)
    if len(commonUniqueDivisions) == 0:
        raise Exception('cannot find a common divisor')
    return max(commonUniqueDivisions)


def lcm(filterList):
    '''
    Find the least common multiple of a list of values

    >>> common.lcm([3,4,5])
    60
    >>> common.lcm([3,4])
    12
    >>> common.lcm([1,2])
    2
    >>> common.lcm([3,6])
    6
    
    :rtype: int
    '''
    def _lcm(a, b):
        """find lowest common multiple of a,b"""
        # // forcers integer style division (no remainder)
        return abs(a*b) // euclidGCD(a,b)

    # derived from
    # http://www.oreillynet.com/cs/user/view/cs_msg/41022
    lcmVal = 1
    for i in range(len(filterList)):
        lcmVal = _lcm(lcmVal, filterList[i])
    return lcmVal


def contiguousList(inputListOrTuple):
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
    
    :rtype: bool
    '''
    currentMaxVal = inputListOrTuple[0]
    for i in range(1, len(inputListOrTuple)):
        newVal = inputListOrTuple[i]
        if newVal != currentMaxVal + 1:
            return False
        currentMaxVal += 1
    return True

def groupContiguousIntegers(src):
    '''Given a list of integers, group contiguous values into sub lists


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
    while i < (len(src)-1):
        e = src[i]
        group.append(e)
        eNext = src[i+1]
        # if next is contiguous, add to grou
        if eNext != e + 1:
        # if not contiguous
            post.append(group)
            group = []
        # second to last elements; handle separately
        if i == len(src)-2:
            # need to handle next elements
            group.append(eNext)
            post.append(group)

        i += 1

    return post


def fromRoman(num):
    '''

    Convert a Roman numeral (upper or lower) to an int

    http://code.activestate.com/recipes/81611-roman-numerals/


    >>> common.fromRoman('ii')
    2
    >>> common.fromRoman('vii')
    7

    Works with both IIII and IV forms:
    
    >>> common.fromRoman('MCCCCLXXXIX')
    1489
    >>> common.fromRoman('MCDLXXXIX')
    1489


    Some people consider this an error, but you see it in medieval documents:

    >>> common.fromRoman('ic')
    99

    But things like this are never seen, and thus cause an error:

    >>> common.fromRoman('vx')
    Traceback (most recent call last):
    Music21CommonException: input contains an invalid subtraction element: vx

    :rtype: int
    '''
    inputRoman = num.upper()
    nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
    ints = [1000, 500, 100, 50,  10,  5,   1]
    places = []
    for c in inputRoman:
        if not c in nums:
            raise Music21CommonException("value is not a valid roman numeral: %s" % inputRoman)
    for i in range(len(inputRoman)):
        c = inputRoman[i]
        value = ints[nums.index(c)]
        # If the next place holds a larger number, this value is negative.
        try:
            nextvalue = ints[nums.index(inputRoman[i +1])]
            if nextvalue > value and value in [1, 10, 100]:
                value *= -1
            elif nextvalue > value:
                raise Music21CommonException("input contains an invalid subtraction element: %s" % num)
        except IndexError:
            # there is no next place.
            pass
        places.append(value)
    summation = 0
    for n in places:
        summation += n
    return summation
    # Easiest test for validity...
    #if int_to_roman(sum) == input:
    #   return sum
    #else:
    #   raise ValueError, 'input is not a valid roman numeral: %s' % input

def toRoman(num):
    '''

    Convert a number from 1 to 3999 to a roman numeral


    >>> common.toRoman(2)
    'II'
    >>> common.toRoman(7)
    'VII'
    >>> common.toRoman(1999)
    'MCMXCIX'

    >>> common.toRoman("hi")
    Traceback (most recent call last):
    TypeError: expected integer, got <... 'str'>
    
    :rtype: str
    '''
    if not isinstance(num, int):
        raise TypeError("expected integer, got %s" % type(num))
    if not 0 < num < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    result = ""
    for i in range(len(ints)):
        count = int(num/ ints[i])
        result += nums[i] * count
        num -= ints[i] * count
    return result


def ordinalAbbreviation(value, plural=False):
    '''Return the ordinal abbreviations for integers

    >>> common.ordinalAbbreviation(3)
    'rd'
    >>> common.ordinalAbbreviation(255)
    'th'
    >>> common.ordinalAbbreviation(255, plural=True)
    'ths'

    :rtype: str
    '''
    valueHundreths = value % 100
    if valueHundreths in [11, 12, 13]:
        post = 'th'
    else:
        valueMod = value % 10
        if valueMod == 1:
            post = 'st'
        elif valueMod in [0, 4, 5, 6, 7, 8, 9]:
            post = 'th'
        elif valueMod == 2:
            post = 'nd'
        elif valueMod == 3:
            post = 'rd'

    if post != 'st' and plural:
        post += 's'
    return post

class Test(unittest.TestCase):
    '''
    Tests not requiring file output.
    '''

    def runTest(self):
        pass

    def setUp(self):
        pass

    def testToRoman(self):
        for src, dst in [(1, 'I'), (3, 'III'), (5, 'V')]:
            self.assertEqual(dst, toRoman(src))

    def testWeightedSelection(self):

        #from music21 import environment
        #_MOD = "common.py"
        #environLocal = environment.Environment(_MOD)


        # test equal selection
        for j in range(10):
            x = 0
            for i in range(1000):
                # equal chance of -1, 1
                x += weightedSelection([-1, 1], [1,1])
            #environLocal.printDebug(['weightedSelection([-1, 1], [1,1])', x])
            self.assertTrue(-250 < x < 250)


        # test a strongly weighed boudnary
        for j in range(10):
            x = 0
            for i in range(1000):
                # 10,000 more chance of 0 than 1.
                x += weightedSelection([0, 1], [10000, 1])
            #environLocal.printDebug(['weightedSelection([0, 1], [10000,1])', x])
            self.assertTrue(0 <= x < 20)

        for j in range(10):
            x = 0
            for i in range(1000):
                # 10,000 times more likely 1 than 0.
                x += weightedSelection([0, 1], [1, 10000])
            #environLocal.printDebug(['weightedSelection([0, 1], [1, 10000])', x])
            self.assertTrue(900 <= x <= 1000)


        for unused_j in range(10):
            x = 0
            for i in range(1000):
                # no chance of anything but 0.
                x += weightedSelection([0, 1], [1, 0])
            #environLocal.printDebug(['weightedSelection([0, 1], [1, 0])', x])
            self.assertEqual(x, 0)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [fromRoman, toRoman]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


