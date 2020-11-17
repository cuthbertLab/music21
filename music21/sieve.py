# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         sieve.py
# Purpose:      sieve operations, after Iannis Xenakis.
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2003, 2010 Christopher Ariza
#               Copyright © 2010-2012, 19 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
A comprehensive, object model of the Xenakis Sieve. :class:`music21.sieve.Sieve`
objects can be created from high-level string notations, and used to generate line segments
in various representation. Additional functionality is available through associated objects.

The :class:`music21.sieve.Sieve` class permits generation segments in four formats.


>>> a = sieve.Sieve('3@2|7@1')
>>> a.segment()
[1, 2, 5, 8, 11, 14, 15, 17, 20, 22, 23, 26, 29, 32, 35, 36, 38, 41, 43, 44,
 47, 50, 53, 56, 57, 59, 62, 64, 65, 68, 71, 74, 77, 78, 80, 83, 85, 86, 89, 92, 95, 98, 99]

>>> a.segment(segmentFormat='binary')
[0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1,
 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1,
 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1,
 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1]

>>> a.segment(segmentFormat='width')
[1, 3, 3, 3, 3, 1, 2, 3, 2, 1, 3, 3, 3, 3, 1, 2, 3, 2, 1, 3, 3, 3, 3, 1, 2, 3, 2,
 1, 3, 3, 3, 3, 1, 2, 3, 2, 1, 3, 3, 3, 3, 1]

>>> len(a.segment(segmentFormat='unit'))
43


A :class:`music21.sieve.CompressionSegment` can be used to derive a Sieve from a
ny sequence of integers.


>>> a = sieve.CompressionSegment([3, 4, 5, 6, 7, 8, 13, 19])
>>> str(a)
'6@1|7@6|8@5|9@4|10@3|11@8'


The :class:`music21.sieve.PitchSieve` class provides a quick generation of
:class:`music21.pitch.Pitch` lists from Sieves.

>>> a = sieve.PitchSieve('13@3|13@6|13@9', 'c1', 'c10', 'f#4')
>>> pitches = a()
>>> ', '.join([str(p) for p in pitches])
'F#1, A1, C2, G2, B-2, C#3, G#3, B3, D4, A4, C5, E-5, B-5, C#6, E6, B6, D7,
 F7, C8, E-8, F#8, C#9, E9, G9'

'''
from ast import literal_eval
import copy
import random
import string
import unittest
from typing import Union

from music21 import exceptions21
from music21 import pitch
from music21 import common
from music21 import interval

from music21 import environment
_MOD = 'sieve'
environLocal = environment.Environment(_MOD)


# ------------------------------------------------------------------------------
class UnitException(exceptions21.Music21Exception):
    pass


class ResidualException(exceptions21.Music21Exception):
    pass


class SieveException(exceptions21.Music21Exception):
    pass


class CompressionSegmentException(exceptions21.Music21Exception):
    pass


class PitchSieveException(exceptions21.Music21Exception):
    pass


LGROUP = '{'
RGROUP = '}'
AND = '&'
OR = '|'
XOR = '^'
BOUNDS = [LGROUP, RGROUP, AND, OR, XOR]
NEG = '-'
RESIDUAL = list(string.digits) + ['@']


# ------------------------------------------------------------------------------
# from
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117119
# David Eppstein, UC Irvine, 28 Feb 2002
# Alex Martelli
# other implementations
# http://c2.com/cgi-bin/wiki?SieveOfEratosthenesInManyProgrammingLanguages
# http://www.mycgiserver.com/~gpiancastelli/blog/archives/000042.html

def eratosthenes(firstCandidate=2):
    '''
    Yields the sequence of prime numbers via the Sieve of Eratosthenes.
    rather than creating a fixed list of a range (z) and crossing out
    multiples of sequential candidates, this algorithm stores primes under
    their next possible candidate, thus allowing the generation of primes
    in sequence without storing a complete range (z).

    create a dictionary. each entry in the dictionary is a key:item pair of
    the largest (key) largest multiple of this prime so far found : (item)
    the prime. the dictionary only has as many entries as found primes.

    if a candidate is not a key in the dictionary, it is not a multiple of
    any already-found prime; it is thus a prime. a new entry is added to the
    dictionary, with the square of the prime as the key. the square of the prime
    is the next possible multiple to be found.

    to use this generator, create an instance and then call the .next() method
    on the instance


    >>> a = sieve.eratosthenes()
    >>> next(a)
    2
    >>> next(a)
    3


    We can also specify a starting value for the sequence, skipping over
    initial primes smaller than this number:


    >>> a = sieve.eratosthenes(95)
    >>> next(a)
    97
    >>> next(a)
    101
    '''
    D = {}  # map composite integers to primes witnessing their compositeness
    # D stores largest composite: prime, pairs
    q = 2  # candidate, first integer to test for primality
    while True:
        # get item from dict by key; remove from dict
        # p is the prime, if already found
        # q is the candidate, the running integer list
        p = D.pop(q, None)  # returns item for key, None if not in dict
        # if candidate (q) is already in dict, not a prime
        if p is not None:  # key (prime candidate) in dictionary
            # update dictionary w/ the next multiple of this prime not already
            # in dictionary
            nextMult = p + q  # prime prime plus the candidate; next multiple
            while nextMult in D:  # incr x by p until it is a unique key
                nextMult = nextMult + p
            # re-store the prime under a key of the next multiple
            D[nextMult] = p  # x is now the next unique multiple to be found
        # candidate (q) not already in dictionary; q is prime
        else:  # value not in dictionary
            nextMult = q * q  # square is next multiple tt will be found
            D[nextMult] = q
            if q >= firstCandidate:
                yield q  # return prime
        q = q + 1  # incr. candidate


def rabinMiller(n):
    '''
    Returns True if an integer is likely prime or False if it is likely composite using the
    Rabin Miller primality test.

    See also here: http://www.4dsolutions.net/ocn/numeracy2.html


    >>> sieve.rabinMiller(234)
    False
    >>> sieve.rabinMiller(5)
    True
    >>> sieve.rabinMiller(4)
    False

    >>> sieve.rabinMiller(97 * 2)
    False

    >>> sieve.rabinMiller(6 ** 4 + 1)  # prime
    True

    >>> sieve.rabinMiller(123986234193)  # divisible by 3, runs fast
    False
    '''
    n = abs(n)
    if n in (2, 3):
        return True

    m = n % 6  # if n (except 2 and 3) mod 6 is not 1 or 5, then n isn't prime
    if m not in (1, 5):
        return False

    # primes up to 100;  2, 3 handled by mod 6
    primes = [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43,
               47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

    if n <= 100:
        if n in primes:
            return True  # must include 2, 3
        return False

    for prime in primes:
        if n % prime == 0:
            return False

    s, r = n - 1, 1
    while not s & 1:
        s >>= 1
        r = r + 1

    for i in range(10):  # random tests
        # calculate a^s mod n, where a is a random number
        y = pow(random.randint(1, n - 1), s, n)
        if y == 1:  # pragma: no cover
            continue  # n passed test, is composite
        # try values of j from 1 to r - 1
        for j in range(1, r):
            if y == n - 1:
                break  # if y = n - 1, n passed the test this time
            y = pow(y, 2, n)  # a^((2^j)*s) mod n
        else:  # pragma: no cover
            return False  # y never equaled n - 1, then n is composite
    # n passed all of the tests, it is very likely prime
    return True


# ------------------------------------------------------------------------------
# list processing and unit interval routines
# possible move to common.py if used elsewhere

def discreteBinaryPad(series, fixRange=None):
    '''
    Treat a sequence of integers as defining contiguous binary integers,
    where provided values are 1's and excluded values are zero.

    For instance, running [3, 10, 12] through this method gives a 1 for
    the first entry (signifying 3), 0s for the next six entries (signifying
    4-9), a 1 (for 10), a 0 (for 11), and a 1 (for 12).


    >>> sieve.discreteBinaryPad([3, 10, 12])
    [1, 0, 0, 0, 0, 0, 0, 1, 0, 1]

    >>> sieve.discreteBinaryPad([3, 4, 5])
    [1, 1, 1]

    '''
    # make sure these are ints
    for x in series:
        if not common.isNum(x):
            raise UnitException('non-integer value found')
    discrete = []
    if fixRange is not None:
        fixRange.sort()  # make sure sorted
        minVal = fixRange[0]
        maxVal = fixRange[-1]
    else:  # find max and min from values
        seriesAlt = list(copy.deepcopy(series))
        seriesAlt.sort()
        minVal = seriesAlt[0]
        maxVal = seriesAlt[-1]
    for x in range(minVal, maxVal + 1):
        if x in series:
            discrete.append(1)
        else:  # not in series
            discrete.append(0)
    return discrete


def unitNormRange(series, fixRange=None):
    '''
    Given a list of numbers, create a proportional spacing across the unit interval.

    The first entry will always be 0 and the last 1, other entries will be spaced
    according to their distance between these two units.  For instance, for 0, 3, 4
    the middle entry will be 0.75 since 3 is 3/4 of the distance between 0 and 4:


    >>> sieve.unitNormRange([0, 3, 4])
    [0.0, 0.75, 1.0]


    but for [1, 3, 4], it will be 0.666... because 3 is 2/3 of the distance between
    1 and 4


    >>> sieve.unitNormRange([1, 3, 4])
    [0.0, 0.666..., 1.0]


    '''
    if fixRange is not None:
        fixRange.sort()
        minFound = fixRange[0]
        maxFound = fixRange[-1]
    else:  # find maxFound and minFound from values
        minFound = min(series)
        maxFound = max(series)
    span = maxFound - minFound
    unit = []
    if len(series) > 1:
        for val in series:
            dif = val - minFound
            if common.isNum(dif):
                dif = float(dif)
            if span != 0:
                unit.append(dif / span)
            else:  # fill value if span is zero
                unit.append(0)
    else:  # if one element, return 0 (could be 1, or 0.5)
        unit.append(0)
    return unit


def unitNormEqual(parts):
    '''
    Given a certain number of parts, return a list unit-interval values
    between 0 and 1, with as many divisions as parts; 0 and 1 are always inclusive.

    >>> sieve.unitNormEqual(3)
    [0.0, 0.5, 1]

    If parts is 0 or 1, then a single entry of [0] is given:

    >>> sieve.unitNormEqual(1)
    [0]
    '''
    if parts <= 1:
        return [0]
    elif parts == 2:
        return [0, 1]
    else:
        unit = []
        step = 1 / (parts - 1)
        for y in range(parts - 1):  # one less value tn needed
            unit.append(y * step)
        unit.append(1)  # make last an integer, add manually
        return unit


def unitNormStep(step, a=0, b=1, normalized=True):
    '''
    Given a step size and an a/b min/max range, calculate number of parts
    to fill step through inclusive a,b, then return a unit interval list of values
    necessary to cover region.

    Note that returned values are by default normalized within the unit interval.


    >>> sieve.unitNormStep(0.5, 0, 1)
    [0.0, 0.5, 1]

    >>> sieve.unitNormStep(0.5, -1, 1)
    [0.0, 0.25, 0.5, 0.75, 1]

    >>> sieve.unitNormStep(0.5, -1, 1, normalized=False)
    [-1, -0.5, 0.0, 0.5, 1.0]

    >>> post = sieve.unitNormStep(0.25, 0, 20)
    >>> len(post)
    81
    >>> post = sieve.unitNormStep(0.25, 0, 20, normalized=False)
    >>> len(post)
    81

    '''
    if a == b:
        return []  # no range, return boundary

    if a < b:
        minVal = a
        maxVal = b
    else:
        minVal = b
        maxVal = a

    # find number of parts necessary
    count = 0  # will count last, so do not count min at beginning
    values = []
    x = minVal
    while x <= maxVal:
        values.append(x)  # do before incrementing
        x += step
        count += 1
    if normalized:
        return unitNormEqual(count)
    else:
        return values


# ------------------------------------------------------------------------------
# note: some of these methods are in common, though they are slightly different algorithms;
# need to test for compatibility

def _gcd(a, b):
    '''
    find the greatest common divisor of a,b
    i.e., greatest number that is a factor of both numbers using
    Euclid's algorithm


    >>> sieve._gcd(20, 30)
    10
    '''
    # alt implementation

    # while b != 0:
    #    a, b = b, a % b
    # return abs(a)

    # if a == 0 and b == 0:
    #    return 1
    # if b == 0:
    #    return a
    # if a == 0:
    #    return b
    # else:
    #    return _gcd(b, a % b)

    while b != 0:
        a, b = b, a % b
    return abs(a)


def _lcm(a, b):
    '''
    find lowest common multiple of a,b

    >>> sieve._lcm(30, 20)
    60
    '''
    # // forces integer style division (no remainder)
    return abs(a * b) // _gcd(a, b)


def _lcmRecurse(filterList):
    '''
    Given a list of values, find the LCM of all the values by iteratively
    looking doing an LCM comparison to the values in the list.

    >>> from music21 import sieve
    >>> sieve._lcmRecurse([2, 3])
    6
    >>> sieve._lcmRecurse([2, 3, 12])
    12
    >>> sieve._lcmRecurse([8, 10, 3])
    120
    '''
    # from
    # http://www.oreillynet.com/cs/user/view/cs_msg/41022
    lcmVal = 1
    # note: timing may not be necessary
    timer = common.Timer()
    timer.start()
    for i in range(len(filterList)):
        if timer() >= 60:
            environLocal.printDebug(['lcm timed out'])
            lcmVal = None
            break
        lcmVal = _lcm(lcmVal, filterList[i])
    return lcmVal


def _meziriac(c1, c2):
    # Bachet de Meziriac (1624)
    # in order for x and y to be two coprimes, it is necessary and sufficient
    # that there exist two relative whole numbers, e, g such that
    #       1 + (g * x) = e * y  or
    #            y' * x = (e' * y) + 1
    # where e and g come from the recursive equations
    #           (e * c2) % c1 == 1  and
    #           (g'* c1) % c2 == 1  ### this is version used here
    # while letting e, g' run through values 0, 1, 2, 3...
    # except if c1 == 1 and c2 == 1
    g = 0
    if c2 == 1:
        g = 1
    elif c1 == c2:
        g = 0  # if equal, causes infinite loop of 0
    else:
        while g < 10000:
            val = (g * c1) % c2
            if val == 1:
                break
            g = g + 1
    return g


# ------------------------------------------------------------------------------
class PrimeSegment:
    def __init__(self, start, length):
        '''
        A generator of prime number segments, given a start value
        and desired length of primes.

        >>> ps = sieve.PrimeSegment(3, 20)
        >>> ps()
        [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73]
        '''
        self.seg = []
        self.start = start
        self.length = length
        # fill the segment
        self._fillRange()

    def _fillRabinMiller(self, start, length, stop=None, direction='up'):
        '''
        scan all number in range and return a list of primes
        provide a max to force stoppage at  certain point before the
        maximum length
        direction determines which way things go.
        '''
        seg = []
        _oddBoundary = 4  # number above which only odd primes are found

        if start % 2 == 0 and start > _oddBoundary:  # if even
            if direction == 'up':
                n = start + 1
            else:  # if down
                n = start - 1
        else:
            n = start

        while 1:
            if rabinMiller(n):
                seg.append(n)
                if len(seg) >= length:
                    break
            if n == stop:
                break
            if n > _oddBoundary:  # after 5, no even primes
                if direction == 'up':
                    n = n + 2  # only test odd numbers
                else:
                    n = n - 2
            else:  # n is less than 5, add 1
                if direction == 'up':
                    n = n + 1  # must increment by 1
                else:
                    n = n - 1
        return seg

    def _fillRange(self):
        '''
        fill positive and negative range
        '''
        if self.start < 0:
            # create the negative portion of the segment
            segNeg = self._fillRabinMiller(abs(self.start), self.length, 0, 'down')
            segNeg = [-x for x in segNeg]  # make negative
            if len(segNeg) < self.length:
                segPos = self._fillRabinMiller(0, self.length - len(segNeg),
                                                         None, 'up')
                self.seg = segNeg + segPos
            else:  # add positive values
                self.seg = segNeg

        else:  # start from zero alone
            self.seg = self._fillRabinMiller(self.start, self.length, None, 'up')

    def __call__(self, segmentFormat=None):
        '''
        assumes that min and max values are derived from found primes
        means that primes will always be at boundaries
        '''
        z = [self.seg[0], self.seg[-1]]

        if segmentFormat in ('bin', 'binary'):
            return discreteBinaryPad(self.seg, z)
        elif segmentFormat == 'unit':
            return unitNormRange(self.seg, z)
        elif segmentFormat in ('wid', 'width'):
            wid = []
            for i in range(len(self.seg) - 1):
                wid.append((self.seg[i + 1] - self.seg[i]))
            return wid
        else:  # int, integer
            return self.seg


# ------------------------------------------------------------------------------
class Residual:
    '''
    object that represents a modulus and a start point
    each object stores a range of integers (self._z) from which sections are drawn
    this range of integers can be changed whenever the section os drawn

    >>> residual = sieve.Residual(3, 2)
    '''

    def __init__(self, m, shift=0, neg=0, z=None):
        # get a default range, can be changed later
        # is an actual range and not start/end points b/c when producing a not (-)
        # it is easy to remove the mod,n from the range
        if z is None:  # supply default if necessary
            z = list(range(100))
        self._z = z
        # print('residual init self._z', self._z)
        self._m = m
        if neg not in (0, 1):
            raise ResidualException('negative value must be 0, 1, or a Boolean')
        self._neg = neg  # negative, complement boolean
        if self._m == 0:  # 0 mode causes ZeroDivisionError
            self._shift = shift
        else:
            self._shift = shift % self._m  # do mod on shift
        self._segmentFormatOptions = ['int', 'bin', 'unit', 'wid']
        self._segmentFormat = 'int'

    # --------------------------------------------------------------------------
    # utility functions
    def setZ(self, z):
        '''
        z is the range of integers to use when generating a list
        '''
        self._z = z

    def setZRange(self, minInt, maxInt):
        '''
        z is the range of integers to use when generating a list
        convenience function that fixes max
        '''
        self._z = list(range(minInt, maxInt + 1))

    def setSegmentFormat(self, fmt):
        # fmt = drawer.strScrub(fmt, 'l')
        fmt = fmt.strip().lower()
        if fmt in self._segmentFormatOptions:
            raise ResidualException('format not in format options: %s' % fmt)
        self._segmentFormat = fmt

    # --------------------------------------------------------------------------
    def segment(self, n=0, z=None, segmentFormat=None):
        '''
        get a residual subset of this modulus at this n
        within the integer range provided by z
        format can be 'int' or 'bin', for integer or binary

        >>> a = sieve.Residual(3, 2)
        >>> a.segment(3)
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59,
         62, 65, 68, 71, 74, 77, 80, 83, 86, 89, 92, 95, 98]
        >>> a.segment(3, range(3, 15))
        [5, 8, 11, 14]
        '''
        if z is None:  # z is temporary; if none
            z = self._z  # assign to local
        if segmentFormat is None:
            segmentFormat = self._segmentFormat

        subset = []
        if self._m == 0:
            return subset  # empty

        n = (n + self._shift) % self._m  # check for n >= m

        for value in z:
            if n == value % self._m:
                subset.append(value)
        if self._neg:  # find opposite
            compSet = copy.deepcopy(z)
            for value in subset:
                compSet.remove(value)
            seg = compSet
        else:
            seg = subset

        if segmentFormat in ('bin', 'binary'):
            return discreteBinaryPad(seg, z)
        elif segmentFormat == 'unit':
            return unitNormRange(seg, z)
        elif segmentFormat in ('wid', 'width'):  # difference always equal to m
            wid = [self._m] * (len(seg) - 1)  # one shorter than segment
            return wid
        elif segmentFormat in ('int', 'integer'):  # int, integer
            return seg
        else:
            raise ResidualException('%s not a valid sieve segmentFormat string.' % segmentFormat)

    def period(self):
        '''
        period is M; obvious, but nice for completeness

        >>> a = sieve.Residual(3, 2)
        >>> a.period()
        3
        '''
        return self._m

    # --------------------------------------------------------------------------
    def copy(self):
        # TODO: replace with deepcopy method
        m = copy.copy(self._m)
        shift = copy.copy(self._shift)
        neg = copy.copy(self._neg)
        # provide ref, not copy, to z
        return Residual(m, shift, neg, self._z)

    def __call__(self, n=0, z=None, segmentFormat=None):
        '''
        calls self.segment(); uses _segmentFormat

        >>> a = sieve.Residual(3, 2)
        >>> a()
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47,
         50, 53, 56, 59, 62, 65, 68, 71, 74, 77, 80, 83, 86, 89, 92, 95, 98]
        '''
        # if z is None, uses self._z
        return self.segment(n, z, segmentFormat)

    def represent(self, style=None):
        '''
        does not show any logical operator but unary negation
        '''
        if style == 'classic':  # mathematical style
            if self._shift != 0:
                repStr = '%s(%s+%s)' % (self._m, 'n', self._shift)
            else:
                repStr = '%s(%s)' % (self._m, 'n')
            if self._neg:
                repStr = '-%s' % repStr
        else:  # do evaluatable type
            repStr = '%s@%s' % (self._m, self._shift)  # show w/ @
            if self._neg:
                repStr = '-%s' % repStr
        return repStr

    def __str__(self):
        '''
        str representation using M(n + shift) style notation

        >>> a = sieve.Residual(3, 2)
        >>> str(a)
        '3@2'
        '''
        return self.represent()  # default style

    def __eq__(self, other):
        '''
        ==, compare residual classes in terms of m and shift
        '''
        if other is None:
            return 0
        if (self._m == other._m
                and self._shift == other._shift
                and self._neg == other._neg):
            return 1
        else:
            return 0

    def __cmp__(self, other):
        '''
        allow comparison based on m and shift; if all equal look at neg

        Still being used internally even though __cmp__ is not used in Python 3
        '''
        # return neg if self < other, zero if self == other,
        # a positive integer if self > other.
        if self._m < other._m:
            return -1
        elif self._m > other._m:
            return 1
        # if equal compare shift
        elif self._m == other._m:
            if self._shift < other._shift:
                return -1
            elif self._shift > other._shift:
                return 1
            else:  # shifts are equal
                if self._neg != other._neg:
                    if self._neg == 1:  # its negative, then less
                        return -1
                    else:
                        return 1
                else:
                    return 0

    def __lt__(self, other):
        if self.__cmp__(other) == -1:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.__cmp__(other) == 1:
            return True
        else:
            return False

    def __neg__(self):
        '''
        unary neg operators; return neg object
        '''
        if self._neg:  # if 1
            neg = 0
        else:  # if 0
            neg = 1
        return Residual(self._m, self._shift, neg, self._z)

    def __and__(self, other):
        '''
        &, produces an intersection of two Residual classes
        returns a new Residual class
        cannot be done if R under complementation

        >>> a = sieve.Residual(3, 2)
        >>> b = sieve.Residual(5, 1)
        >>> c = a & b
        >>> str(c)
        '15@11'
        '''
        if other._neg or self._neg:
            raise ResidualException('complemented Residual objects cannot be intersected')
        m, n = self._cmpIntersection(self._m, other._m, self._shift, other._shift)
        # get the union of both z
        zSet = set(self._z) | set(other._z)
        z = list(zSet)
        # neg = 0  # most not be complemented
        return Residual(m, n, 0, z)

    def __or__(self, other):
        '''
        |, not sure if this can be implemented
        i.e., a union of two Residual classes can not be expressed as a single
        Residual, that is intersections can always be reduced, whereas unions
        cannot be reduced.
        '''
        pass

    # --------------------------------------------------------------------------

    def _cmpIntersection(self, m1, m2, n1, n2):
        '''
        compression by intersection
        find m,n such that the intersection of two Residual's can
        be reduced to one Residual. Xenakis p 273.
        '''
        d = _gcd(m1, m2)
        c1 = m1 // d  # not sure if we need floats here
        c2 = m2 // d
        n3 = 0
        m3 = 0
        if m1 != 0 and m2 != 0:
            n1 = n1 % m1
            n2 = n2 % m2
        else:  # one of the mods is equal to 0
            return n3, m3  # no intersection
        if d != 1 and ((n1 - n2) % d != 0):
            return n3, m3  # no intersection
        elif d != 1 and ((n1 - n2) % d == 0) and (n1 != n2) and (c1 == c2):
            m3 = d  # for real?
            n3 = n1
            return m3, n3
        else:  # d == 1, or ...
            m3 = c1 * c2 * d
            g = _meziriac(c1, c2)  # c1,c2 must be co-prime may produce a loop
            n3 = (n1 + (g * (n2 - n1) * c1)) % m3
            return m3, n3


# ------------------------------------------------------------------------------
class CompressionSegment:
    '''
    Utility to convert from a point sequence to sieve.

    A z range can be supplied to explicitly provide the complete sieve segment,
    both positive and negative values. all values in the z range not in the
    segment are interpreted as negative values. thus, there is an essential
    dependency on the z range and the realized sieve.

    No matter the size of the z range, there is a modulus at which one point
    in the segment can be found. As such, any segment can be reduced to, at a
    minimum, a residual for each point in the segment, each, for the supplied z,
    providing a segment with one point.

    The same segment can then have multiplied logical string representations,
    depending on the provided z.

    >>> a = sieve.CompressionSegment([3, 4, 5, 6, 7, 8, 13, 19])
    >>> str(a)
    '6@1|7@6|8@5|9@4|10@3|11@8'

    >>> b = sieve.CompressionSegment([0, 2, 4, 6, 8])
    >>> str(b)
    '2@0'

    >>> c = sieve.CompressionSegment([0, 2, 4, 5, 7, 9, 11, 12])
    >>> str(c)
    '5@2|5@4|6@5|7@0'
    '''

    def __init__(self, src, z=None):
        # The supplied list of values is only the positive values of a sieve segment
        # we do not know what the negative values are; we can assume they are between
        # the min and max of the list, but this may not be true in all cases.
        src = list(copy.deepcopy(src))
        src.sort()
        self._match = []  # already sorted from src

        for num in src:  # remove redundancies
            if num not in self._match:
                self._match.append(num)
        if len(self._match) <= 1:
            raise CompressionSegmentException('segment must have more than one element')
        self._zUpdate(z)  # sets self._z
        # max mod should always be the max of z; this is b/c at for any segment
        # if the mod == max of seg, at least one point can be found in the segment
        # mod is the step size, so only one step will happen in the sequence
        self._maxMod = len(self._z)  # set maximum mod tried
        # assign self._residuals and do analysis
        try:
            self._process()
        except AssertionError:
            raise CompressionSegmentException('no Residual classes found for this z range')

    def _zUpdate(self, z=None):
        # z must at least be a superset of match
        if z is not None:  # its a list
            if not self._subset(self._match, z):
                raise CompressionSegmentException(
                    'z range must be a superset of desired segment')

            self._z = z
            zMin, zMax = self._z[0], self._z[-1]
        # z is range from max to min, unless provided at init
        else:  # range from min, max; add 1 for range() to max
            zMin, zMax = self._match[0], self._match[-1]
            self._z = list(range(zMin, (zMax + 1)))

    # --------------------------------------------------------------------------
    def __call__(self):
        '''

        >>> a = sieve.CompressionSegment([3, 4, 5, 6, 7, 8])
        >>> b = a()
        >>> str(b[0])
        '1@0'
        '''
        return self._residuals

    def __str__(self):
        resStr = []
        if len(self._residuals) == 1:  # single union must have an or
            resStr = '%s' % str(self._residuals[0])
        else:
            for resObj in self._residuals:
                resStr.append(str(resObj))
            resStr = '|'.join(resStr)
        return resStr

    # --------------------------------------------------------------------------
    def _subset(self, sub, thisSet):
        '''
        True if sub is part of set; assumes no redundancies in each
        '''
        commonNum = 0
        for x in sub:
            if x in thisSet:
                commonNum = commonNum + 1
        if commonNum == len(sub):
            return 1
        else:
            return 0

    def _find(self, n, part, whole):
        '''
        given a point, and SieveSegment, find a modulus and shift that
        match.
        '''
        m = 1  # could start at one, but only pertains to the single case of 1@0
        while m < self._maxMod:  # search m for max
            obj = Residual(m, n, 0, self._z)
            seg = obj()  # n, z is set already
            # check first to see if it is a member of the part
            if self._subset(seg, part):
                return obj, seg
            elif self._subset(seg, whole):
                return obj, seg
            m = m + 1
            # a mod will always be found, at least 1 point; should never happen

        raise SieveException('a mod was not found less than {0}'.format(self._maxMod))

    def _process(self):
        '''
        take a copy of match; move through each value of this list as if it
        were n; for each n test each modulo (from 1 to len(z) + 1) to find a
        residual. when found (one will be found), keep it; remove the found
        segments from the match, and repeat.
        '''
        # process residuals
        self._residuals = []  # list of objects
        match = copy.copy(self._match)  # scratch to work on

        maxToRun = 10000
        while maxToRun:  # loop over whatever is left in the match copy
            maxToRun -= 1
            n = match[0]  # always get first item
            obj, seg = self._find(n, match, self._match)
            if obj is None:  # no residual found; should never happen
                raise CompressionSegmentException('_find() returned a None object')
            if obj not in self._residuals:  # b/c __eq__ defined
                self._residuals.append(obj)
                for x in seg:  # clean found values from match
                    if x in match:
                        match.remove(x)
            if not match:
                break
        self._residuals.sort()


# ------------------------------------------------------------------------------

# http://docs.python.org/lib/set-objects.html
# set object precedence is places & before |

# >>> a = set([3, 4])
# >>> b = set([4, 5])
# >>> c = set([3, 4, 5])
# >>> a & b & c
# Set([4])

# >>> a & b | c
# Set([3, 4, 5])

# >>> a & (b | c)
# Set([3, 4])
# >>> (a & b) | c
# Set([3, 4, 5])

# >>> b = sieve.SieveBound('2&4&8|5')
# <R0>&<R1>&<R2>|<R3>
# >>> str(b)
# '2&4&8|5'
# >>> b(0, range(20))
# [0, 5, 8, 10, 15, 16]
# >>> b = sieve.SieveBound('2&4&(8|5)')
# <R0>&<R1>&(<R2>|<R3>)
# >>> b(0, range(20))
# [0, 8, 16]
# >>> b = sieve.SieveBound('5|2&4&8')
# <R0>|<R1>&<R2>&<R3>
# >>> b(0, range(20))
# [0, 5, 8, 10, 15, 16]
# >>> b = sieve.SieveBound('(5|2)&4&8')
# (<R0>|<R1>)&<R2>&<R3>
# >>> b(0, range(20))
# [0, 8, 16]
# >>>

# precedence is -, &, |

class Sieve:
    '''
    Create a sieve segment from a sieve logical string of any complexity.

    >>> a = sieve.Sieve('3@11')
    >>> b = sieve.Sieve('2&4&8|5')
    >>> c = sieve.Sieve('(5|2)&4&8')
    '''

    def __init__(self, usrStr, z=None):
        # note: this z should only be used if usrStr is a str, and not a list
        if z is None and isinstance(usrStr, str):
            z = list(range(100))
        elif z is None and common.isListLike(usrStr):  # if a list
            pass
        self._z = z  # may be none; will be handled in self._load

        self._state = 'exp'  # default start state
        self._expType = None  # either 'simple' or 'complex'; set w/ load
        self._segmentFormat = 'int'
        self._segmentFormatOptions = ['int', 'bin', 'unit', 'wid']

        self._nonCompressible = False  # if current z provides a nullSeg; no compression
        # variables will re-initialize w/ dedicated methods
        self._resLib = {}  # store id and object
        self._resId = 0  # used to calculate residual ids

        # expanded, compressed form
        self._expTree = ''  # string that stores representation
        self._expPeriod = None  # only set if called
        self._cmpTree = ''  # string that stores representation
        self._cmpPeriod = None  # only set if called; may not be same as exp
        self._usrStr = usrStr  # store user string, may be None
        if self._usrStr is not None:
            self._load()

    # --------------------------------------------------------------------------
    def _load(self):
        if common.isListLike(self._usrStr):
            self._resClear()
            self._initLoadSegment(self._usrStr)  # z will be provided
            self._initCompression()
        # normal instance, or a manual load
        else:  # process usrStr
            self._resClear()
            self._initParse()
            self._initCompression()

    def _initCompression(self):
        # only negative that will show up is binary negative, not unary
        # some internal intersections may have a complemented residual class
        self._expType = 'complex'  # assume complex
        if (NEG in self._expTree
                or LGROUP in self._expTree
                or RGROUP in self._expTree
                or XOR in self._expTree):
            try:
                self._cmpSegment()  # will update self._nonCompressible
            except IndexError:  # case of z not providing a sufficient any segment
                self._nonCompressible = 1
        else:  # try intersection
            try:
                self._cmpIntersection()
                self._expType = 'simple'  # only if successful
            except TypeError:  # attempted intersection of complemented
                try:
                    self._cmpSegment()
                except IndexError:  # no segments available
                    self._nonCompressible = 1

        method = ''
        if self._nonCompressible:
            method = 'no compression possible'
        elif self._expType == 'complex':
            method = 'segment'
        elif self._expType == 'simple':
            method = 'intersection'
        return method

    def _initPeriod(self):
        '''
        Lazy period initialization, called only when needed from public period() method.
        '''
        mListExp = self._resPeriodList('exp')
        mListCmp = self._resPeriodList('cmp')
        # get lcm of expanded sieves
        lcmExp = _lcmRecurse(mListExp)
        if mListExp == mListCmp:
            self._expPeriod = lcmExp
            self._cmpPeriod = lcmExp
        else:  # calculate separately
            self._expPeriod = lcmExp
            self._cmpPeriod = _lcmRecurse(mListCmp)

    # --------------------------------------------------------------------------
    def expand(self):
        '''
        Set this Sieve to its expanded state.
        '''
        self._state = 'exp'

    def compress(self, z=None):
        '''
        Set this sieve to its compressed state.
        '''
        if z is not None and z != self._z:  # only process if z has changed
            self._z = z
            self._resClear('cmp')  # clear compressed residuals
            self._initCompression()  # may update self._nonCompressible
        if self._nonCompressible:  # do not changes set
            pass  # no compression available at this z
        else:
            self._state = 'cmp'

    # --------------------------------------------------------------------------

    def _getParameterData(self):
        '''
        Provides a dictionary data representation for exchange
        '''
        data = {
            'logStr': self.represent('exp'),
        }
        if self._z is None:  # get from residual classes, always one at
            data['z'] = self._resLib[self._resKeyStr(0)].z
        else:
            data['z'] = self._z
        return data

    # --------------------------------------------------------------------------
    # utility functions
    def setZ(self, z):
        '''
        Set the z as a list. The z is the range of integers to use when
        generating a sieve segment.
        '''
        self._z = z

    def setZRange(self, minInt, maxInt):
        '''
        Set the z as a min and max value. The z is the range of
        integers to use when generating a sieve segment.
        '''
        self._z = list(range(minInt, maxInt + 1))

    def setSegmentFormat(self, fmt):
        # fmt = drawer.strScrub(fmt, 'l')
        fmt = fmt.strip().lower()
        if fmt not in self._segmentFormatOptions:
            raise SieveException('cannot set to format: %s' % fmt)
        self._segmentFormat = fmt

    # --------------------------------------------------------------------------
    # operator overloading for sieves
    # problem: redundant parenthesis are not removed

    def __neg__(self):
        '''
        unary neg operators; return neg object.
        '''
        dataSelf = self._getParameterData()
        usrStr = '%s%s%s%s' % (NEG, LGROUP,
                                     dataSelf['logStr'], RGROUP)
        z = dataSelf['z']
        return Sieve(usrStr, z)

    def __and__(self, other):
        '''
        &, produces an intersection of two

        >>> a = sieve.Sieve('3@11')
        >>> b = sieve.Sieve('2&4&8|5')
        >>> c = sieve.Sieve('(5|2)&4&8')
        >>> d = a & b
        >>> str(d)
        '{2@0&4@0&8@0|5@0}&{3@2}'
        '''
        dataSelf = self._getParameterData()
        dataOther = other._getParameterData()
        usrStr = '%s%s%s%s%s%s%s' % (LGROUP, dataOther['logStr'],
                                     RGROUP, AND, LGROUP, dataSelf['logStr'], RGROUP)
        # take union of z
        zSet = set(dataSelf['z']) | set(dataOther['z'])
        z = list(zSet)
        return Sieve(usrStr, z)

    def __or__(self, other):
        '''
        |, produces a union

        >>> a = sieve.Sieve('3@11')
        >>> b = sieve.Sieve('2&4&8|5')
        >>> d = a | b
        >>> str(d)
        '{2@0&4@0&8@0|5@0}|{3@2}'
        '''
        dataSelf = self._getParameterData()
        dataOther = other._getParameterData()

        usrStr = '%s%s%s%s%s%s%s' % (LGROUP, dataOther['logStr'],
                                     RGROUP, OR, LGROUP, dataSelf['logStr'], RGROUP)
        # take union of z
        zSet = set(dataSelf['z']) | set(dataOther['z'])
        z = list(zSet)
        return Sieve(usrStr, z)

    def __xor__(self, other):
        '''
        ^, produces exclusive disjunction.
        '''
        dataSelf = self._getParameterData()
        dataOther = other._getParameterData()

        usrStr = '%s%s%s%s%s%s%s' % (LGROUP, dataOther['logStr'],
                                     RGROUP, XOR, LGROUP, dataSelf['logStr'], RGROUP)
        # take union of z
        zSet = set(dataSelf['z']) | set(dataOther['z'])
        z = list(zSet)
        return Sieve(usrStr, z)

    # --------------------------------------------------------------------------
    # string conversions
    def _parseResidual(self, usrStr):
        '''
        process an arg string for proper Residual creation
        valid syntax for Mod, shift pairs:
        all valid: MsubN, M@N, M,N, M
        if M is given alone, shift is assumed to be 0
        this method assumes that all brackets have been replaced with parentheses
        returns a dictionary of args suitable for creating a Residual class
        '''
        m = 0
        # if given a number, not a string
        if common.isNum(usrStr):
            return {'m': int(usrStr), 'n': 0, 'neg': 0}

        usrStr = usrStr.strip()
        if not usrStr:
            return None
        if usrStr.find('sub'):
            usrStr = usrStr.replace('sub', ',')
        if usrStr.find('@'):
            usrStr = usrStr.replace('@', ',')
        # remove any braces remain, remove
        # all parenthesis and brackets are converted to braces
        usrStr = usrStr.replace(LGROUP, '')
        usrStr = usrStr.replace(RGROUP, '')

        # check for not
        if usrStr[0] == '-':  # negative/complement
            neg = 1
            # strip to remove any leading white space
            usrStr = usrStr[1:].strip()
        else:
            neg = 0

        if not usrStr:
            return None

        try:
            # assume we have either an int (M), or a tuple (M,N)
            # better to remove the eval, but at least there are no globals or locals this way
            # waste of two {} dicts -- could be cached, but not worth it for now...
            args = literal_eval(usrStr)
        except (NameError, SyntaxError, TypeError):
            return None

        shift = 0
        if common.isNum(args):
            m = int(args)  # int is mod
            shift = 0    # 0 is given as default shift
        elif common.isListLike(args):  # may only be a list of one element
            m = args[0]  # first  is mod
            if len(args) > 1:
                shift = args[1]  # second is shift
            else:
                shift = 0
        # return a dictionary of args necessary to create Residual
        return {'m': m,
                'shift': shift,
                'neg': neg,
                }

    def _parseLogic(self, usrStr):
        '''
        provide synonyms for logical symbols
        intersection == and, &, *
        union        == or, |, +
        not          == not, -
        the native format for str representation uses only &, |, -
        this method converts all other string representations

        all brackets and braces are replaced with parenthesis
        parentheses are only used for the internal representation
        on string representation, braces are restored
        '''
        # if not a string but a number
        if common.isNum(usrStr):  # assume its a single modules
            usrStr = '%s@0' % int(usrStr)

        if usrStr.find('and') >= 0:  # replace with '&'
            usrStr = usrStr.replace('and', AND)
        if usrStr.find('*') >= 0:  # Xenakis notation'
            usrStr = usrStr.replace('*', AND)
        if usrStr.find('or') >= 0:
            usrStr = usrStr.replace('or', OR)
        if usrStr.find('+') >= 0:
            usrStr = usrStr.replace('+', OR)
        if usrStr.find('xor') >= 0:
            usrStr = usrStr.replace('^', OR)
        if usrStr.find('not') >= 0:
            usrStr = usrStr.replace('not', NEG)
        # all groupings converted to braces
        if usrStr.find('[') >= 0:  # replace brackets w/ parenthesis
            usrStr = usrStr.replace('[', LGROUP)
        if usrStr.find(']') >= 0:
            usrStr = usrStr.replace(']', RGROUP)
        if usrStr.find('(') >= 0:  # replace braces as well
            usrStr = usrStr.replace('(', LGROUP)
        if usrStr.find(')') >= 0:
            usrStr = usrStr.replace(')', RGROUP)
        # remove space
        usrStr = usrStr.replace(' ', '')
        return usrStr

    # --------------------------------------------------------------------------
    def _setInstantiateStr(self, valList):
        '''
        return string necessary to instantiate a set object.
        '''
        valList = list(valList)
        return 'set(%s)' % repr(valList).replace(' ', '')

    def _resKeyStr(self, resId):
        return '<R%i>' % resId

    def _resKeys(self, state):
        '''
        get residual keys based on library.
        '''
        if state not in ('cmp', 'exp'):
            raise SieveException("state must be 'cmp' or 'exp'")
        if state == 'cmp':
            libKeys = []
            for key in self._resLib:
                if key in self._cmpTree:
                    libKeys.append(key)
            return libKeys
        elif state == 'exp':
            libKeys = []
            for key in self._resLib:
                if key in self._expTree:
                    libKeys.append(key)
            return libKeys

    def _resPeriodList(self, state):
        '''
        For all residual classes, get the period, or the value of M,
        and return these in a list. Remove any redundant values and sort.
        '''
        mList = []
        for key in self._resKeys(state):
            p = self._resLib[key].period()
            if p not in mList:
                mList.append(p)
        mList.sort()
        return mList

    def _resCreate(self, resId, resStr):
        '''
        create a residual object, store in expResidualLib
        return a string id representation
        this uses self._z at initialization.
        '''
        resDict = self._parseResidual(''.join(resStr))
        if resDict is None:
            msg = 'cannot parse %s' % ''.join(resStr)
            raise SieveException('bad residual class notation: (%r)' % msg)
        resObj = Residual(resDict['m'], resDict['shift'],
                          resDict['neg'], self._z)

        self._resLib[self._resKeyStr(resId)] = resObj
        return self._resKeyStr(resId)

    def _resAssign(self, resId, resObj):
        self._resLib[self._resKeyStr(resId)] = resObj
        return self._resKeyStr(resId)

    def _resToSetStr(self, resId, n=0, z=None):
        '''
        this is where residuals are converted to set evaluating strings
        z should not be stored; should be a temporary value
        '''
        if z is None:  # if none given, give internal
            z = self._z
        # z is valid, gets default from residual class
        if not common.isListLike(z) and z is not None:
            raise SieveException('z must be a list of integers, not %r' % z)
        valList = self._resLib[resId](n, z)  # call residual object
        return self._setInstantiateStr(valList)

    def _resIdIncrement(self):
        '''
        increment the _resId.
        '''
        self._resId = self._resId + 1

    def _resResetId(self):
        '''
        reset self._resId to the next available number
        may need to re-label some residual classes if gaps develop
        ids should be contiguous integer sequence
        '''
        iVals = range(len(self._resLib.keys()))
        for i in iVals:
            testKey = self._resKeyStr(i)
            if testKey not in self._cmpTree and testKey not in self._expTree:
                raise SieveException('gap in residual keys')
        # set _resId to next available index, the length of the keys
        self._resId = len(self._resLib.keys())

    def _resClear(self, state=None):
        if state is None:  # clear all
            self._resLib = {}  # store id and object
            self._resId = 0
        elif state == 'cmp':
            cmpKeys = self._resKeys(state)
            for key in cmpKeys:
                del self._resLib[key]
            # reset id to reflect deleted classes
            self._resResetId()
        elif state == 'exp':
            raise SieveException('Expanded residual classes should never be cleared')

    # --------------------------------------------------------------------------
    # expansion methods

    def _initLoadSegment(self, usrData):
        '''
        load from a segments
        reload _resId.
        '''
        # clear first
        self._expTree = []  # string that stores representation
        # use dynamically generated z
        segObj = CompressionSegment(usrData, self._z)  # a list of values
        if self._z is None:  # non given at init, get from segObj
            self._z = segObj._z
        union = segObj()  # convert to residual classes
        for resObj in union:
            # store resKey in dict, store as string
            self._expTree.append(self._resAssign(self._resId, resObj))
            self._resIdIncrement()
        self._expTree = OR.join(self._expTree)

    def _initParse(self, z=None):
        '''
        process usrStr string into proper argument dictionaries for Residual
        '''
        # clear first
        self._resLib = {}  # store id and object
        self._resId = 0
        self._expTree = []  # string that stores representation
        # will remove all spaces
        logStr = self._parseLogic(copy.deepcopy(self._usrStr))  # logical string
        i = 0
        while 1:
            if i == len(logStr):
                break
            char = logStr[i]  # current char

            if i == 0:
                charPrevious = None  # first
            else:
                charPrevious = logStr[i - 1]
            if i == len(logStr) - 1:
                charNext = None  # last
            else:
                charNext = logStr[i + 1]

            # if a boundary symbol ({}&|) simply add to string
            if char in BOUNDS:
                self._expTree.append(char)
                i = i + 1

            # if NEG is last char this is always an error
            elif char == NEG and charNext is None:
                msg = 'negation cannot be used without operands'
                raise SieveException('badly formed logical string (a): (%s)' % msg)
            # attempting to use negating as a binary operators
            elif (char == NEG
                  and charPrevious is not None
                  and charPrevious in RESIDUAL):  # digit, or @ sign
                msg = 'negation cannot be used as a binary operator'
                raise SieveException('badly formed logical string (b): (%s)' % msg)
            # check if NEG is not followed by a digit;
            # special case of NEG; need to convert into a binary operator
            elif (char == NEG
                  and charNext is not None
                  and charNext == LGROUP):
                # if not first char, and the previous char is not an operator or
                # a delimiter, this is an error (binary negation)
                if (charPrevious is not None
                        and charPrevious not in (LGROUP, AND, OR, XOR)):
                    msg = 'negation must be of a group and isolated by delimiters'
                    raise SieveException('badly formed logical string (c): (%s)' % msg)

                self._expTree.append(char)
                i += 1

            # processing a normal residual class; only first
            # char can be negative
            # NEG, if present, will be followed by digits
            elif char in string.digits or char == NEG:
                resStr = []  # string just for this residual class
                subStart = copy.copy(i)
                subLen = 0
                # fist check for leading NEG
                if logStr[subStart + subLen] == NEG:
                    resStr.append(NEG)
                    subLen = subLen + 1
                while 1:
                    # if at the end of the logical string
                    if (subStart + subLen) == len(logStr):
                        break
                    subChar = logStr[subStart + subLen]
                    # neg is boundary, as already gathered above
                    if subChar in BOUNDS or subChar == NEG:
                        break  # do not increment
                    else:
                        resStr.append(subChar)
                        subLen = subLen + 1

                self._expTree.append(self._resCreate(self._resId, ''.join(resStr)))
                self._resIdIncrement()
                i = i + subLen
            else:  # some other char is in here
                i = i + 1
        # do some checks
        if not self._resLib:
            raise SieveException('no residual classes defined')
        self._expTree = ''.join(self._expTree)

    # --------------------------------------------------------------------------
    # compression methods

    def _cmpIntersection(self):
        '''
        an unbound sieve, intersection Residual
        '''
        self._cmpTree = []  # clear first
        logStr = copy.copy(self._expTree)  # create scratch copy
        # if not a string but a number
        orList = logStr.split(OR)
        intersection = 0
        for orGroup in orList:
            if orGroup == '':
                continue
            # need deal with mixed not operations in an and-group
            andList = orGroup.split(AND)
            # do intersections, reduce, and add
            if len(andList) == 1:
                intersection = self._resLib[andList[0]]
            else:
                for i in range(len(andList) - 1):  # one less than len
                    if i == 0:  # first, get first
                        # problem was here w/ and list value not being in _resLib
                        a = self._resLib[andList[i]]
                    else:
                        a = intersection
                    b = self._resLib[andList[i + 1]]  # get second
                    # this may raise an exception if not possible
                    intersection = a & b  # operator overloading
            # store resKey in dict, store as string
            self._cmpTree.append(self._resAssign(self._resId, intersection))
            self._resIdIncrement()
        self._cmpTree = OR.join(self._cmpTree)

    def _cmpSegment(self):
        '''
        a bound sieve, uss a newly created segment
        '''
        # clear first
        self._cmpTree = []
        # will use z if set elsewhere
        seg = self.segment('exp')
        if not seg:  # empty set
            raise IndexError('empty segment; segment compression not possible')

        segObj = CompressionSegment(seg, self._z)
        for resObj in segObj():
            self._cmpTree.append(self._resAssign(self._resId, resObj))
            self._resIdIncrement()
        self._cmpTree = OR.join(self._cmpTree)

    # --------------------------------------------------------------------------

    def segment(self, state=None, n=0, z=None, segmentFormat=None):
        '''
        Return a sieve segment in various formats.

        >>> a = sieve.Sieve('3@11')
        >>> a.segment('exp')
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47,
         50, 53, 56, 59, 62, 65, 68, 71, 74, 77, 80, 83, 86, 89, 92, 95, 98]

        >>> c = sieve.Sieve('(5|2)&4&8')
        >>> c.segment('cmp', segmentFormat='wid')
        [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
        '''
        if state is None:
            state = self._state
        if z is None:
            z = self._z
        if segmentFormat is None:
            segmentFormat = self._segmentFormat

        if state == 'exp':
            evalStr = copy.copy(self._expTree)
        elif state == 'cmp':
            evalStr = copy.copy(self._cmpTree)
        else:
            evalStr = ''
        keys = self._resKeys(state)

        # only NEG that remain are those applied to groups
        # replace all remain NEG in the formula w/ '1@1-'
        # as long as binary negation is evaluated before & and |, this will work
        # see http://docs.python.org/ref/summary.html
        # must do this before converting segments (where there will be neg numbers)

        resObj = Residual(1, 0, 0, z)  # create a temporary residual 1@!
        setStr = self._setInstantiateStr(resObj())  # get segment
        evalStr = evalStr.replace('-', ('%s-' % setStr))
        # replace residuals (this will add - as -numbers)
        for key in keys:
            evalStr = evalStr.replace(key, self._resToSetStr(key, n, z))

        # convert all braces to parenthesis
        evalStr = evalStr.replace(LGROUP, '(')
        evalStr = evalStr.replace(RGROUP, ')')

        # this may raise an exception if mal-formed
        try:
            # better to remove the eval, but at least there are no globals or locals this way
            # waste of two {} dicts -- could be cached, but not worth it for now...
            seg = eval(evalStr, {'__builtins__': {'set': set}}, {})  # pylint: disable=eval-used
            # print('---: ' + evalStr)
            # print('xxx: ' + repr(seg))
        except SyntaxError as se:
            raise SieveException(
                f'badly formed logical string ({evalStr})'
            ) from se

        seg = list(seg)
        seg.sort()
        if segmentFormat in ('bin', 'binary'):
            return discreteBinaryPad(seg, z)
        elif segmentFormat == 'unit':
            return unitNormRange(seg, z)
        elif segmentFormat in ('wid', 'width'):
            wid = []
            for i in range(len(seg) - 1):
                wid.append((seg[i + 1] - seg[i]))
            return wid
        else:  # int, integer
            return seg

    def period(self, state=None):
        '''
        Return the period of the sieve.

        >>> a = sieve.Sieve('3@11')
        >>> a.period()
        3
        >>> b = sieve.Sieve('2&4&8|5')
        >>> b.period()
        40
        >>> c = sieve.Sieve('(5|2)&4&8')
        >>> c.period()
        40
        '''
        # two periods are possible; if residuals are the same
        # for both exp and cmd, only one is calculated
        # period only calculated the fist time this method is called

        if state is None:
            state = self._state
        # check and see if exp has been set yet
        if self._expPeriod is None:
            self._initPeriod()
        if state == 'exp':
            return self._expPeriod
        elif state == 'cmp':
            return self._cmpPeriod

    def __call__(self, n=0, z=None, segmentFormat=None):
        return self.segment(self._state, n, z, segmentFormat)

    def collect(self, n, zMinimum, length, segmentFormat, zStep=100):
        '''
        Collect sieve segment points for the provided length and format.

        >>> a = sieve.Sieve('3@11')
        >>> a.collect(10, 100, 10, 'int')
        [102, 105, 108, 111, 114, 117, 120, 123, 126, 129]
        '''

        #  collect a segment to meet a desired length for the segment
        #  z must be extended automatically to continue to search from zMinimum
        #  zStep is the size of each z used to cycle through all z
        #  this seems to only work properly for float and integer sieves

        found = []
        p = zMinimum  # starting value
        zExtendCount = 0
        while zExtendCount < 10000:  # default max to break loops
            zMin = p
            zMax = p + zStep

            # must collect non width formats as integer values; then convert
            if segmentFormat in ('wid', 'width'):
                segmentPartial = self.segment(self._state, n,
                                              list(range(zMin, zMax)), segmentFormat)
            else:  # if a unit, need to start with integers
                segmentPartial = self.segment(self._state, n,
                                              list(range(zMin, zMax)), 'int')

            found = found + segmentPartial[:]
            p = p + zStep  # increment start value
            zExtendCount = zExtendCount + 1  # fail safe

            if len(found) >= length:
                break

        # trim any extra
        seg = found[:length]
        if len(seg) != length:
            raise SieveException('desired length of sieve segment cannot be found')

        # only width format comes out correct after concatenation
        # for unit and binary, derive new z based on min and max
        if segmentFormat == 'unit':
            # make z to minimum and max value found
            return unitNormRange(seg, range(seg[0], seg[-1] + 1))
        elif segmentFormat in ('bin', 'binary'):
            # make to minimum and max value found
            return discreteBinaryPad(seg, range(seg[0], seg[-1] + 1))
        else:
            return seg

    def represent(self, state=None, style=None):
        '''
        style of None is use for users; adds | to single residuals
        style abs (absolute) does not add | tos single residual class
        '''
        if state is None:
            state = self._state

        if state == 'exp':
            msg = copy.copy(self._expTree)
        elif state == 'cmp':
            msg = copy.copy(self._cmpTree)
        else:
            msg = ''

        # get keys for this library
        keys = self._resKeys(state)
        for key in keys:
            msg = msg.replace(key, self._resLib[key].represent(style))
        return msg

    def __str__(self):
        return self.represent()

# ------------------------------------------------------------------------------
# high level utility obj


class PitchSieve:
    '''
    Quick utility generator of :class:`music21.pitch.Pitch` lists
    from :class:`music21.sieve.Sieve` objects.

    >>> ps = sieve.PitchSieve('6@0', 'c4', 'c8')
    >>> [str(p) for p in ps()]
    ['C4', 'F#4', 'C5', 'F#5', 'C6', 'F#6', 'C7', 'F#7', 'C8']

    >>> a = sieve.PitchSieve('4@7')
    >>> [str(p) for p in a()]
    ['E-3', 'G3', 'B3', 'E-4', 'G4', 'B4']
    '''

    def __init__(self,
                 sieveString,
                 pitchLower=None,
                 pitchUpper=None,
                 pitchOrigin=None,
                 eld: Union[int, float] = 1):
        self.pitchLower = None  # 'c3'
        self.pitchUpper = None  # 'c5' -- default ps Range
        self.pitchOrigin = None  # pitchLower -- default
        self.sieveString = sieveString  # logical sieve string

        # should be in a try block
        self.sieveObject = Sieve(self.sieveString)

        if pitchLower is not None:
            self.pitchLower = pitch.Pitch(pitchLower)
        else:
            self.pitchLower = pitch.Pitch('c3')

        if pitchUpper is not None:
            self.pitchUpper = pitch.Pitch(pitchUpper)
        else:
            self.pitchUpper = pitch.Pitch('c5')

        if pitchOrigin is not None:
            self.pitchOrigin = pitch.Pitch(pitchOrigin)
        else:  # use pitchLower value
            self.pitchOrigin = copy.deepcopy(self.pitchLower)

        if eld is not None:
            self.eld = float(eld)
        else:
            self.eld = eld
        # environLocal.printDebug(['PitchSieve', eld])

    def __call__(self):
        # noinspection PyShadowingNames
        '''
        Return a sieve segment as a list of :class:`music21.pitch.Pitch` objects,
        mapped to the range between pitchLower and pitchUpper.

        >>> a = sieve.PitchSieve('4@7&5@4')
        >>> a()
        [<music21.pitch.Pitch G4>]

        >>> a = sieve.PitchSieve('13@3|13@6|13@9', 'c1', 'c10')
        >>> ', '.join([str(p) for p in a()])
        'E-1, F#1, A1, E2, G2, B-2, F3, G#3, B3, F#4, A4, C5, G5, B-5, C#6, G#6, B6,
         D7, A7, C8, E-8, B-8, C#9, E9, B9'

        >>> a = sieve.PitchSieve('3@0', 'c4', 'c5', 'c4', 0.5)
        >>> a.eld
        0.5

        The following is a microtonal pitch sieve; presently these are not
        displayed; true values are
        [0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0]

        >>> pitches = a()
        >>> ', '.join([str(p) for p in pitches])
        'C4, C#~4, E-4, E~4, F#4, G~4, A4, B`4, C5'

        True values: [0.5, 2.0, 3.5, 5.0, 6.5, 8.0, 9.5, 11.0]

        >>> a = sieve.PitchSieve('3@0', 'c4', 'c5', 'c#4', 0.5)
        >>> pitches = a()
        >>> ', '.join([str(p) for p in pitches])
        'C~4, D4, E`4, F4, F#~4, G#4, A~4, B4'
        '''
        minPS = self.pitchLower.ps
        maxPS = self.pitchUpper.ps
        z = list(range(int(minPS), int(maxPS + 1)))
        n = self.pitchOrigin.ps  # shift origin

        # get integer range
        if self.eld == 1:
            sieveSegIntegers = self.sieveObject(n, z)  # make value negative
            sieveSeg = []
            for psNum in sieveSegIntegers:
                p = pitch.Pitch()
                p.ps = psNum
                sieveSeg.append(p)
        else:  # microtonal eld
            # returns all possible values in this range
            valList = unitNormStep(self.eld, minPS, maxPS, normalized=False)
            # this z will not be shifted
            # need to get list of appropriate size
            z = list(range(len(valList)))
            # get a binary segment
            binSeg = self.sieveObject(n, z, 'bin')
            sieveSeg = []
            # when there is activity on the unitSeg, return the value
            for i in range(len(binSeg)):
                if binSeg[i] == 1:
                    p = pitch.Pitch()
                    p.ps = valList[i]
                    sieveSeg.append(p)
        return sieveSeg

    def getIntervalSequence(self):
        '''
        Return a list of Interval objects that defines the complete structure
        of this :class:`music21.sieve.Sieve`.

        >>> a = sieve.PitchSieve('3@0')
        >>> a.getIntervalSequence()
        [<music21.interval.Interval m3>]

        >>> a = sieve.PitchSieve('3@0|7@0')
        >>> a.sieveObject.segment()
        [0, 3, 6, 7, 9, 12, 14, 15, 18, 21, 24, 27, 28, 30, 33, 35, 36, 39, 42, 45, 48, 49,
         51, 54, 56, 57, 60, 63, 66, 69, 70, 72, 75, 77, 78, 81, 84, 87, 90, 91, 93, 96, 98, 99]
        >>> a.sieveObject.period()
        21
        >>> a.getIntervalSequence()
        [<music21.interval.Interval m3>, <music21.interval.Interval m3>,
         <music21.interval.Interval m2>, <music21.interval.Interval M2>,
         <music21.interval.Interval m3>, <music21.interval.Interval M2>,
         <music21.interval.Interval m2>, <music21.interval.Interval m3>,
         <music21.interval.Interval m3>]

        This is the PitchSieve for a major scale:

        >>> b = sieve.PitchSieve('(-3@2 & 4) | (-3@1 & 4@1) | (3@2 & 4@2) | (-3 & 4@3)')
        >>> b.getIntervalSequence()
        [<music21.interval.Interval M2>,
         <music21.interval.Interval M2>,
         <music21.interval.Interval m2>,
         <music21.interval.Interval M2>,
         <music21.interval.Interval M2>,
         <music21.interval.Interval M2>,
         <music21.interval.Interval m2>]
        '''
        # get a z for the complete period
#         try:
#             z = range(self.sieveObject.period() + 1)
#         except (OverflowError, MemoryError):
#             environLocal.printDebug('failed to generates a z with period:',
#                    self.sieveObject.period())
        p = self.sieveObject.period()
        if p < 999999999:
            z = list(range(p + 1))
        else:  # too big to get z as list of values
            z = None

        # get widths, then scale by eld
        # note that the shift here might not always be zero
        widthSegments = self.sieveObject(0, z, segmentFormat='wid')

        post = []
        # value = 0
        for i, width in enumerate(widthSegments):
            # environLocal.printDebug(['stepStart', stepStart, 'stepEnd', stepEnd])
            intervalObj = interval.Interval(width * self.eld)
            post.append(intervalObj)

        if not post:
            raise PitchSieveException('interval segment has no values')
        return post

        # integer steps have no eld
#         integerSteps = self.sieveObject(0, z, format='int')
#
#         post = []
#         for i, step in enumerate(integerSteps):
#             stepStart = step
#             if i < len(integerSteps) - 1:
#                 stepEnd = integerSteps[i + 1]
#             else:
#                 break
#             # environLocal.printDebug(['stepStart', stepStart, 'stepEnd', stepEnd])
#             intervalObj = interval.Interval(stepEnd-stepStart)
#             post.append(intervalObj)
#
#         if len(post) == 0:
#             raise PitchSieveException('interval segment has no values')
#         return post


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testDummy(self):
        self.assertEqual(True, True)

    def pitchOut(self, listIn):
        out = '['
        for p in listIn:
            out += str(p) + ', '
        out = out[0:len(out) - 2]
        out += ']'
        return out

    def testIntersection(self):
        a = Residual(3)
        testArgs = [(3, 6, 2, 5), (4, 6, 1, 3), (5, 4, 3, 2), ]
        for m1, m2, n1, n2 in testArgs:
            a = Residual(m1, n1)
            b = Residual(m2, n2)
            i = a & b           # do intersection

    def testSieveParse(self):
        testArgs = ['-5 | 4 & 4sub3 & 6 | 4 & 4',
                    '2 or 4 and 4 & 6 or 4 & 4',
                    3,
                    # '3 and 4 or not 3, 1 and 4, 1 or not 3 and 4, 2 or not 3, 2 and 4, 3',
                    (2, 4, 6, 8),
                    (1, 6, 11, 16, 17),
                    ]
        for arg in testArgs:
            # environLocal.printDebug(['testSieveParse', arg])
            testObj = Sieve(arg)
            dummy = testObj(0, list(range(30)))

    def testSievePitch(self):
        unused_testObj = PitchSieve('-5 | 4 & 4sub3 & 6', 'b3', 'f#4')
        testObj = PitchSieve('-5 | 4 & 4sub3 & 6')
        dummy = testObj.pitchLower, testObj.pitchUpper
        dummy = testObj()

    def testTimePoint(self):
        args = [(3, 6, 12),
                (0, 6, 12, 15, 18, 24, 30, 36, 42),
                (4, 6, 13),
                (2, 3, 4, 5, 8, 9, 10, 11, 14, 17, 19, 20, 23, 24, 26, 29, 31),
                #  (3, 23, 33, 47, 63, 70, 71, 93, 95, 119, 123, 143, 153, 167),
                (0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (-8, -6, -4, -2, 0, 2, 1),
                ]
        for src in args:
            obj = CompressionSegment(src)
            sObj = Sieve(str(obj))
            dummy = sObj()

    def testSieve(self):
        z = list(range(100))
        usrStr = '3@2 & 4@1 | 2@0 & 3@1 | 3@3 | -4@2'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '3@2&4@1|2@0&3@1|3@0|-4@2')

        usrStr = '-(3@2 & -4@1 & -(12@3 | 12@8) | (-2@0 & 3@1 | (3@3)))'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '-{3@2&-4@1&-{12@3|12@8}|{-2@0&3@1|{3@0}}}')

        # 'example from Flint, on Psapha'
        usrStr = ('[(8@0 | 8@1 | 8@7) & (5@1 | 5@3)] |   [(8@0 | 8@1 | 8@2) & 5@0] | '
                  '[8@3 & (5@0 | 5@1 | 5@2 | 5@3 | 5@4)] | '
                  '[8@4 & (5@0 | 5@1 | 5@2 | 5@3 | 5@4)] | '
                  '[(8@5 | 8@6) & (5@2 | 5@3 | 5@4)] | (8@1 & 5@2) | (8@6 & 5@1)')
        a = Sieve(usrStr, z)
        self.assertEqual(str(a),
                         '{{8@0|8@1|8@7}&{5@1|5@3}}|{{8@0|8@1|8@2}&5@0}|'
                         '{8@3&{5@0|5@1|5@2|5@3|5@4}}|{8@4&{5@0|5@1|5@2|5@3|5@4}}|'
                         '{{8@5|8@6}&{5@2|5@3|5@4}}|{8@1&5@2}|{8@6&5@1}')

        # 'major scale from FM, p197'
        usrStr = '(-3@2 & 4) | (-3@1 & 4@1) | (3@2 & 4@2) | (-3 & 4@3)'
        a = Sieve(usrStr, z)
        self.assertEqual(str(a), '{-3@2&4@0}|{-3@1&4@1}|{3@2&4@2}|{-3@0&4@3}')

        # 'nomos alpha sieve'
        usrStr = ('(-(13@3 | 13@5 | 13@7 | 13@9) & 11@2) | (-(11@4 | 11@8) & 13@9) | '
                  '(13@0 | 13@1 | 13@6)')
        a = Sieve(usrStr, z)
        self.assertEqual(str(a),
                         '{-{13@3|13@5|13@7|13@9}&11@2}|{-{11@4|11@8}&13@9}|{13@0|13@1|13@6}')

    def testPitchSieveA(self):
        from music21 import sieve

        s1 = sieve.PitchSieve('3@0|7@0', 'c2', 'c6')
        self.assertEqual(self.pitchOut(s1()),
                         '[C2, E-2, F#2, G2, A2, C3, D3, E-3, F#3, A3, C4, E-4, '
                         'E4, F#4, A4, B4, C5, E-5, F#5, A5, C6]')

        s1 = sieve.PitchSieve('3@0|7@0', 'c2', 'c6', eld=2)
        self.assertEqual(self.pitchOut(s1()),
                         '[C2, D2, F#2, C3, E3, F#3, C4, F#4, C5, F#5, G#5, C6]')

    def testPitchSieveB(self):
        from music21 import sieve

        # mircotonal elds
        s1 = sieve.PitchSieve('1@0', 'c2', 'c6', eld=0.5)
        self.assertEqual(self.pitchOut(s1()),
                         '[C2, C~2, C#2, C#~2, D2, D~2, E-2, E`2, E2, E~2, F2, F~2, F#2, '
                         'F#~2, G2, G~2, G#2, G#~2, A2, A~2, B-2, B`2, B2, B~2, C3, C~3, C#3, '
                         'C#~3, D3, D~3, E-3, E`3, E3, E~3, F3, F~3, F#3, F#~3, G3, G~3, G#3, '
                         'G#~3, A3, A~3, B-3, B`3, B3, B~3, C4, C~4, C#4, C#~4, D4, D~4, E-4, '
                         'E`4, E4, E~4, F4, F~4, F#4, F#~4, G4, G~4, G#4, G#~4, A4, A~4, B-4, '
                         'B`4, B4, B~4, C5, C~5, C#5, C#~5, D5, D~5, E-5, E`5, E5, E~5, F5, F~5, '
                         'F#5, F#~5, G5, G~5, G#5, G#~5, A5, A~5, B-5, B`5, B5, B~5, C6]')

        s1 = sieve.PitchSieve('3@0', 'c2', 'c6', eld=0.5)
        self.assertEqual(self.pitchOut(s1()),
                         '[C2, C#~2, E-2, E~2, F#2, G~2, A2, B`2, C3, C#~3, E-3, E~3, F#3, G~3, '
                         'A3, B`3, C4, C#~4, E-4, E~4, F#4, G~4, A4, B`4, C5, C#~5, E-5, E~5, F#5, '
                         'G~5, A5, B`5, C6]')

# sieve that breaks LCM
# >>> t = sieve.Sieve((3, 99, 123123, 2433, 2050))


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

