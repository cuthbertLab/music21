# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         interval.py
# Purpose:      music21 classes for representing intervals
#
# Authors:      Michael Scott Asato Cuthbert
#               Jackie Rogoff
#               Amy Hailes
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2022 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module defines various types of interval objects.
Fundamental classes are :class:`~music21.interval.Interval`,
:class:`~music21.interval.GenericInterval`,
and :class:`~music21.interval.ChromaticInterval`.
'''
from __future__ import annotations

from fractions import Fraction

import abc
import copy
import enum
import math
import re
import unittest
import typing as t

from music21 import base
from music21 import common
from music21 import exceptions21

# from music21 import pitch  # SHOULD NOT, b/c of enharmonics
from music21.common.decorators import cacheMethod
from music21.common.types import StepName

from music21 import environment
environLocal = environment.Environment('interval')

# ------------------------------------------------------------------------------
# constants

STEPNAMES: t.Tuple[StepName, ...] = ('C', 'D', 'E', 'F', 'G', 'A', 'B')

class Direction(enum.IntEnum):
    DESCENDING = -1
    OBLIQUE = 0
    ASCENDING = 1


directionTerms = {Direction.DESCENDING: 'Descending',
                  Direction.OBLIQUE: 'Oblique',
                  Direction.ASCENDING: 'Ascending'}

# specifiers are derived from these two lists;
# perhaps better represented with a dictionary
# perhaps the first entry, below, should be None, like in prefixSpecs?

# constants provide the common numerical representation of an interval.
# This is not the number of semitone shifts.
niceSpecNames = ['ERROR', 'Perfect', 'Major', 'Minor', 'Augmented', 'Diminished',
                 'Doubly-Augmented', 'Doubly-Diminished', 'Triply-Augmented',
                 'Triply-Diminished', 'Quadruply-Augmented', 'Quadruply-Diminished']

prefixSpecs = ('ERROR', 'P', 'M', 'm', 'A', 'd', 'AA', 'dd', 'AAA', 'ddd', 'AAAA', 'dddd')

class Specifier(enum.IntEnum):
    '''
    An enumeration for "specifiers" such as Major, Minor, etc.
    that has some special properties.

    >>> from music21.interval import Specifier
    >>> Specifier.PERFECT
    <Specifier.PERFECT>

    Value numbers are arbitrary and just there for backwards compatibility
    with pre v.6 work:

    >>> Specifier.PERFECT.value
    1
    >>> Specifier.PERFECT.name
    'PERFECT'

    >>> str(Specifier.PERFECT)
    'P'
    >>> str(Specifier.MINOR)
    'm'
    >>> str(Specifier.DBLDIM)
    'dd'
    >>> Specifier.DBLDIM.niceName
    'Doubly-Diminished'
    '''
    PERFECT = 1
    MAJOR = 2
    MINOR = 3
    AUGMENTED = 4
    DIMINISHED = 5
    DBLAUG = 6
    DBLDIM = 7
    TRPAUG = 8
    TRPDIM = 9
    QUADAUG = 10
    QUADDIM = 11

    def __str__(self) -> str:
        # this should just be prefixSpecs[self.value] but pylint chokes
        # noinspection PyTypeChecker
        return str(prefixSpecs[int(self.value)])

    def __repr__(self):
        return f'<Specifier.{self.name}>'

    @property
    def niceName(self):
        # noinspection PyTypeChecker
        return niceSpecNames[int(self.value)]

    def inversion(self):
        '''
        Return a new specifier that inverts this Specifier.

        >>> interval.Specifier.MAJOR.inversion()
        <Specifier.MINOR>
        >>> interval.Specifier.DIMINISHED.inversion()
        <Specifier.AUGMENTED>
        >>> interval.Specifier.PERFECT.inversion()
        <Specifier.PERFECT>
        '''
        # noinspection PyTypeChecker
        v = int(self.value)
        inversions = [None, 1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10]
        return Specifier(inversions[v])

    def semitonesAbovePerfect(self):
        # noinspection PyShadowingNames
        '''
        Returns the number of semitones this specifier is above PERFECT

        >>> Specifier = interval.Specifier

        Augmented and Doubly-Augmented intervals are one and two semitones above
        perfect, respectively:

        >>> Specifier.AUGMENTED.semitonesAbovePerfect()
        1
        >>> Specifier.DBLAUG.semitonesAbovePerfect()
        2

        Diminished intervals are negative numbers of semitones above perfect:

        >>> Specifier.DIMINISHED.semitonesAbovePerfect()
        -1
        >>> Specifier.TRPDIM.semitonesAbovePerfect()
        -3

        Perfect is 0:

        >>> Specifier.PERFECT.semitonesAbovePerfect()
        0

        Major and minor cannot be compared to Perfect, so they raise an
        IntervalException

        >>> Specifier.MINOR.semitonesAbovePerfect()
        Traceback (most recent call last):
        music21.interval.IntervalException: <Specifier.MINOR> cannot be compared to Perfect
        '''
        semitonesAdjustPerfect = {  # offset from Perfect
            'P': 0,
            'A': 1,
            'AA': 2,
            'AAA': 3,
            'AAAA': 4,
            'd': -1,
            'dd': -2,
            'ddd': -3,
            'dddd': -4,
        }
        try:
            return semitonesAdjustPerfect[str(self)]
        except KeyError as ke:
            raise IntervalException(f'{self!r} cannot be compared to Perfect') from ke

    def semitonesAboveMajor(self):
        # noinspection PyShadowingNames
        '''
        Returns the number of semitones this specifier is above Major

        >>> Specifier = interval.Specifier

        Augmented and Doubly-Augmented intervals are one and two semitones above
        major, respectively:

        >>> Specifier.AUGMENTED.semitonesAboveMajor()
        1
        >>> Specifier.DBLAUG.semitonesAboveMajor()
        2

        Minor is below major, so it returns -1.

        >>> Specifier.MINOR.semitonesAboveMajor()
        -1


        Diminished intervals are below minor:

        >>> Specifier.DIMINISHED.semitonesAboveMajor()
        -2
        >>> Specifier.DBLDIM.semitonesAboveMajor()
        -3

        Major is 0:

        >>> Specifier.MAJOR.semitonesAboveMajor()
        0

        Perfect cannot be compared to Major, so it raises an
        IntervalException

        >>> Specifier.PERFECT.semitonesAboveMajor()
        Traceback (most recent call last):
        music21.interval.IntervalException: <Specifier.PERFECT> cannot be compared to Major
        '''
        semitonesAdjustImperf = {  # offset from Major
            'M': 0,
            'm': -1,
            'A': 1,
            'AA': 2,
            'AAA': 3,
            'AAAA': 4,
            'd': -2,
            'dd': -3,
            'ddd': -4,
            'dddd': -5,
        }
        try:
            return semitonesAdjustImperf[str(self)]
        except KeyError as ke:
            raise IntervalException(f'{self!r} cannot be compared to Major') from ke


# ordered list of perfect specifiers
perfSpecifiers = [
    Specifier.QUADDIM,
    Specifier.TRPDIM,
    Specifier.DBLDIM,
    Specifier.DIMINISHED,
    Specifier.PERFECT,
    Specifier.AUGMENTED,
    Specifier.DBLAUG,
    Specifier.TRPAUG,
    Specifier.QUADAUG,
]

perfOffset = 4  # that is, Perfect is third on the list.s

# why is this not called imperfSpecifiers?
specifiers = [
    Specifier.QUADDIM,
    Specifier.TRPDIM,
    Specifier.DBLDIM,
    Specifier.DIMINISHED,
    Specifier.MINOR,
    Specifier.MAJOR,
    Specifier.AUGMENTED,
    Specifier.DBLAUG,
    Specifier.TRPAUG,
    Specifier.QUADAUG,
]
majOffset = 5  # index of Major

# the following dictionaries provide half step shifts given key values
# either as integers (generic) or as strings (adjust perfect/imperfect)
# assuming Perfect or Major
semitonesGeneric = {
    1: 0,
    2: 2,
    3: 4,
    4: 5,
    5: 7,
    6: 9,
    7: 11
}


# index maps to a specifier + generic mapping
_P = Specifier.PERFECT
_m = Specifier.MINOR
_M = Specifier.MAJOR

SEMITONES_TO_SPEC_GENERIC = [
    (_P, 1), (_m, 2), (_M, 2), (_m, 3), (_M, 3), (_P, 4), (Specifier.DIMINISHED, 5),
    (_P, 5), (_m, 6), (_M, 6), (_m, 7), (_M, 7),
]

del _P
del _m
del _M


# ------------------------------------------------------------------------------
class IntervalException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------
# some utility functions

def _extractPitch(
    nOrP: t.Union['music21.note.Note', 'music21.pitch.Pitch']
) -> 'music21.pitch.Pitch':
    '''
    utility function to return either the object itself
    or the `.pitch` if it's a Note.

    >>> p = pitch.Pitch('D#4')
    >>> interval._extractPitch(p) is p
    True
    >>> nEflat = note.Note('E-4')
    >>> interval._extractPitch(nEflat) is nEflat.pitch
    True

    If given a Note, also sets the client of the Pitch to be the Note if not already done
    (for safety, since the Note will be discarded.)
    '''
    if hasattr(nOrP, 'classes') and 'Pitch' in nOrP.classes:
        return t.cast('music21.pitch.Pitch', nOrP)
    n = t.cast('music21.note.Note', nOrP)
    if n.pitch._client is not n:
        n.pitch._client = n  # safety -- remove when really secure
    return n.pitch


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


def convertDiatonicNumberToStep(dn: int) -> t.Tuple[StepName, int]:
    '''
    Convert a diatonic number to a step name (without accidental) and an octave integer.
    The lowest C on a Bösendorfer Imperial Grand is assigned 1 the D above it is 2,
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
    # note -- do not replace int(dn / 7) with dn // 7 -- gives wrong numbers for negative.
    if dn == 0:
        return 'B', -1
    elif dn > 0:
        octave = int((dn - 1) / 7.0)
        stepNumber = (dn - 1) - (octave * 7)
        return STEPNAMES[stepNumber], octave
    elif dn < 0:
        octave = int(dn / 7)
        stepNumber = (dn - 1) - (octave * 7)
        return STEPNAMES[stepNumber], (octave - 1)

def parseSpecifier(value: t.Union[str, int, Specifier]) -> Specifier:
    '''
    Given an integer or a string representing a "specifier" (major, minor,
    perfect, diminished, etc.), return the Specifier.

    >>> interval.parseSpecifier('p')
    <Specifier.PERFECT>
    >>> interval.parseSpecifier('P')
    <Specifier.PERFECT>
    >>> interval.parseSpecifier('M')
    <Specifier.MAJOR>
    >>> interval.parseSpecifier('major')
    <Specifier.MAJOR>
    >>> interval.parseSpecifier('m')
    <Specifier.MINOR>
    >>> interval.parseSpecifier('Augmented')
    <Specifier.AUGMENTED>
    >>> interval.parseSpecifier('a')
    <Specifier.AUGMENTED>

    This is not very useful, but there for completeness:

    >>> interval.parseSpecifier(interval.Specifier.MAJOR)
    <Specifier.MAJOR>

    This is the same as calling a Specifier by value:

    >>> interval.parseSpecifier(3)
    <Specifier.MINOR>

    Why? because...

    >>> interval.Specifier.MINOR.value
    3

    Unparsable strings raise an IntervalException:

    >>> interval.parseSpecifier('Zebra')
    Traceback (most recent call last):
    music21.interval.IntervalException: Cannot find a match for value: 'Zebra'

    Illegal intervals raise a ValueError:

    >>> interval.parseSpecifier(None)
    Traceback (most recent call last):
    ValueError: Value None must be int, str, or Specifier
    '''
    if isinstance(value, Specifier):
        return value
    if isinstance(value, int):
        return Specifier(value)
    if not isinstance(value, str):
        raise ValueError(f'Value {value!r} must be int, str, or Specifier')

    if value in prefixSpecs:
        return Specifier(prefixSpecs.index(value))

    # permit specifiers as prefixes without case; this will not distinguish
    # between m and M, but was taken care of in the line above
    if value.lower() in [x.lower() for x in prefixSpecs[1:]]:
        for i, prefix in enumerate(prefixSpecs):
            if prefix is None:
                continue
            if value.lower() == prefix.lower():
                return Specifier(i)

    if value.lower() in [x.lower() for x in niceSpecNames[1:]]:
        for i in range(1, len(niceSpecNames)):
            if value.lower() == niceSpecNames[i].lower():
                return Specifier(i)

    raise IntervalException(f'Cannot find a match for value: {value!r}')

def convertGeneric(value: t.Union[int, str]) -> int:
    '''
    Convert an interval specified in terms of its name (second, third)
    into an integer. If integers are passed, assume the are correct.

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
    music21.interval.IntervalException: Cannot get a direction from None.

    Strings are not the same as numbers...

    >>> interval.convertGeneric('1')
    Traceback (most recent call last):
    music21.interval.IntervalException: Cannot convert '1' to an interval.

    But this works:

    >>> interval.convertGeneric('1st')
    1
    '''
    post: int
    if isinstance(value, int):
        post = value
        directionScalar = Direction.ASCENDING  # may still be negative
    elif isinstance(value, str):
        value = value.strip().lower()

        # first, see if there is a direction term
        directionScalar = Direction.ASCENDING  # assume ascending
        for direction in [Direction.DESCENDING, Direction.ASCENDING]:
            if directionTerms[direction].lower() in value:
                directionScalar = direction  # assign numeric value
                value = value.replace(directionTerms[direction].lower(), '').strip()

        if value in common.numberTools.ordinalsToNumbers:
            post = common.numberTools.ordinalsToNumbers[value]
        else:
            raise IntervalException(f'Cannot convert {value!r} to an interval.')
    else:
        raise IntervalException(f'Cannot get a direction from {value}.')

    post = post * directionScalar
    return post


def convertSemitoneToSpecifierGenericMicrotone(
    count: t.Union[int, float]
) -> t.Tuple[Specifier, int, float]:
    '''
    Given a number of semitones (positive or negative),
    return a default diatonic specifier and cent offset.

    >>> interval.convertSemitoneToSpecifierGenericMicrotone(2.5)
    (<Specifier.MAJOR>, 2, 50.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(-2.5)
    (<Specifier.MINOR>, -3, 50.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(-2.25)
    (<Specifier.MAJOR>, -2, -25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(-1.0)
    (<Specifier.MINOR>, -2, 0.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(2.25)
    (<Specifier.MAJOR>, 2, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.0)
    (<Specifier.MINOR>, 2, 0.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.75)
    (<Specifier.MAJOR>, 2, -25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(1.9)
    (<Specifier.MAJOR>, 2, -10.0...)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(0.25)
    (<Specifier.PERFECT>, 1, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(12.25)
    (<Specifier.PERFECT>, 8, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(24.25)
    (<Specifier.PERFECT>, 15, 25.0)
    >>> interval.convertSemitoneToSpecifierGenericMicrotone(23.75)
    (<Specifier.PERFECT>, 15, -25.0)
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
    octave = abs(count) // 12  # let floor to int

    spec, generic = SEMITONES_TO_SPEC_GENERIC[size]

    return (spec, (generic + (octave * 7)) * dirScale, cents)


def convertSemitoneToSpecifierGeneric(count: t.Union[int, float]) -> t.Tuple[Specifier, int]:
    '''
    Given a number of semitones, return a default diatonic specifier, and
    a number that can be used as a GenericInterval

    >>> interval.convertSemitoneToSpecifierGeneric(0)
    (<Specifier.PERFECT>, 1)
    >>> interval.convertSemitoneToSpecifierGeneric(-2)
    (<Specifier.MAJOR>, -2)
    >>> interval.convertSemitoneToSpecifierGeneric(1)
    (<Specifier.MINOR>, 2)
    >>> interval.convertSemitoneToSpecifierGeneric(7)
    (<Specifier.PERFECT>, 5)
    >>> interval.convertSemitoneToSpecifierGeneric(11)
    (<Specifier.MAJOR>, 7)
    >>> interval.convertSemitoneToSpecifierGeneric(12)
    (<Specifier.PERFECT>, 8)
    >>> interval.convertSemitoneToSpecifierGeneric(13)
    (<Specifier.MINOR>, 9)
    >>> interval.convertSemitoneToSpecifierGeneric(-15)
    (<Specifier.MINOR>, -10)
    >>> interval.convertSemitoneToSpecifierGeneric(24)
    (<Specifier.PERFECT>, 15)

    Note that the tritone is given as diminished fifth, not augmented fourth:

    >>> interval.convertSemitoneToSpecifierGeneric(6)
    (<Specifier.DIMINISHED>, 5)

    Microtones are rounded here:

    >>> interval.convertSemitoneToSpecifierGeneric(0.4)
    (<Specifier.PERFECT>, 1)
    >>> interval.convertSemitoneToSpecifierGeneric(0.6)
    (<Specifier.MINOR>, 2)
    '''
    # strip off microtone
    return convertSemitoneToSpecifierGenericMicrotone(count)[:2]


_pythagorean_cache: t.Dict[str, t.Tuple['music21.pitch.Pitch', Fraction]] = {}


def intervalToPythagoreanRatio(intervalObj: Interval) -> Fraction:
    r'''
    Returns the interval ratio in pythagorean tuning, always as a Fraction object.

    >>> iList = [interval.Interval(name) for name in ('P4', 'P5', 'M7', 'm23')]
    >>> iList
    [<music21.interval.Interval P4>,
     <music21.interval.Interval P5>,
     <music21.interval.Interval M7>,
     <music21.interval.Interval m23>]

    >>> [interval.intervalToPythagoreanRatio(i) for i in iList]
    [Fraction(4, 3), Fraction(3, 2), Fraction(243, 128), Fraction(2048, 243)]

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

    end_pitch: Pitch
    ratio: Fraction

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
                f'Could not find a pythagorean ratio for {intervalObj}.')

        _pythagorean_cache[end_pitch_wanted.name] = end_pitch, ratio

    octaves = int((end_pitch_wanted.ps - end_pitch.ps) / 12)
    return ratio * Fraction(2, 1) ** octaves

# ------------------------------------------------------------------------------


class IntervalBase(base.Music21Object):
    '''
    General base class for inheritance.
    '''
    def transposeNote(self, note1: 'music21.note.Note') -> 'music21.note.Note':
        '''
        Uses self.transposePitch to do the same to a note.

        >>> n1 = note.Note('C#4', quarterLength=2.0)
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
    def transposePitch(self,
                       pitch1: 'music21.pitch.Pitch',
                       *,
                       inPlace: bool = False):
        '''
        IntervalBase does not know how to do this, so it must be overridden in
        derived classes.
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def reverse(self):
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

    >>> gi = interval.GenericInterval(8)
    >>> gi
    <music21.interval.GenericInterval 8>

    >>> third = interval.GenericInterval(3)
    >>> third.directed
    3
    >>> third.direction
    <Direction.ASCENDING: 1>
    >>> third.perfectable
    False
    >>> third.staffDistance
    2

    We can also specify intervals from strings:

    >>> third = interval.GenericInterval('Third')
    >>> third
    <music21.interval.GenericInterval 3>
    >>> third.directed
    3

    or like this:

    >>> thirdDown = interval.GenericInterval('Descending Third')
    >>> thirdDown
    <music21.interval.GenericInterval -3>
    >>> thirdDown.directed
    -3

    A lot of tools for working with large intervals

    >>> twelfthDown = interval.GenericInterval(-12)
    >>> twelfthDown.niceName
    'Twelfth'
    >>> twelfthDown.perfectable
    True
    >>> twelfthDown.staffDistance
    -11
    >>> twelfthDown.mod7
    4
    >>> twelfthDown.directed
    -12
    >>> twelfthDown.undirected
    12

    >>> complement12 = twelfthDown.complement()
    >>> complement12.niceName
    'Fourth'
    >>> complement12.staffDistance
    3


    Note this illegal interval:

    >>> zeroth = interval.GenericInterval(0)
    Traceback (most recent call last):
    music21.interval.IntervalException: The Zeroth is not an interval

    However, this is okay:

    >>> descendingUnison = interval.GenericInterval(-1)
    >>> descendingUnison.direction
    <Direction.DESCENDING: -1>
    >>> descendingUnison.directed
    -1
    >>> descendingUnison.undirected
    1

    This is because we don't yet know what type of unison this is: is it
    a Perfect Unison or an Augmented Unison (or Augmented Prime as some prefer)?
    Thus, the illegal check will be moved to a higher level Interval object.


    A second is a step:

    >>> second = interval.GenericInterval(2)
    >>> second.isDiatonicStep
    True
    >>> second.isStep
    True

    A third is not:

    >>> third = interval.GenericInterval(-3)
    >>> third.isDiatonicStep
    False
    >>> third.isStep
    False


    Intervals more than three octaves use numbers with abbreviations instead of names

    >>> threeOctaveSecond = interval.GenericInterval(23)
    >>> threeOctaveSecond.niceName
    '23rd'

    >>> threeOctaveThird = interval.GenericInterval(24)
    >>> threeOctaveThird.niceName
    '24th'
    >>> threeOctaveThird.isDiatonicStep
    False
    >>> threeOctaveThird.isStep
    False
    >>> threeOctaveThird.simpleNiceName
    'Third'

    Changed in v.6 -- large intervals get abbreviations
    '''
    def __init__(self,
                 value: t.Union[int, str] = 'Unison',
                 **keywords):
        super().__init__(**keywords)
        self._value: int = 1
        self.value = convertGeneric(value)

    def _reprInternal(self):
        return str(self.directed)

    def __eq__(self, other):
        '''
        True if value and direction are the same.

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

        >>> a == ''
        False
        >>> a is None
        False
        '''
        if not isinstance(other, type(self)):
            return False
        elif self.value == other.value:
            return True
        else:
            return False

    @property
    def value(self) -> int:
        '''
        The size of this interval as an integer.  Synonym for `self.directed`

        >>> interval.GenericInterval('Descending Sixth').value
        -6
        '''
        return self._value

    @value.setter
    def value(self, newValue: int):
        self.clearCache()
        if newValue == 0:
            raise IntervalException('The Zeroth is not an interval')
        self._value = newValue

    @property
    def directed(self) -> int:
        '''
        Synonym for `self.value`

        >>> sixthDown = interval.GenericInterval(-6)
        >>> sixthDown.directed
        -6
        >>> sixthDown.directed = 2
        >>> sixthDown.value
        2
        '''
        return self.value

    @directed.setter
    def directed(self, newValue: int):
        self.value = newValue

    @property
    def undirected(self) -> int:
        '''
        Returns the absolute value of `self.directed`.  Read-only

        >>> sixthDown = interval.GenericInterval(-6)
        >>> sixthDown.undirected
        6
        '''
        return abs(self.value)

    @property
    def direction(self) -> Direction:
        '''
        Returns a Direction Enum value for the direction of this interval:

        >>> interval.GenericInterval('Descending Fifth').direction
        <Direction.DESCENDING: -1>

        >>> interval.GenericInterval('Unison').direction
        <Direction.OBLIQUE: 0>

        >>> interval.GenericInterval(4).direction
        <Direction.ASCENDING: 1>
        '''
        d = self.directed
        if d == 1:
            return Direction.OBLIQUE
        elif d < 0:
            return Direction.DESCENDING
        else:
            return Direction.ASCENDING

    @property
    def isSkip(self) -> bool:
        '''
        Returns True if the undirected interval is bigger than a second.

        >>> interval.GenericInterval('Octave').isSkip
        True
        >>> interval.GenericInterval('Descending 2nd').isSkip
        False
        >>> interval.GenericInterval(1).isSkip
        False

        Note that Unisons are neither steps nor skips.
        '''
        return self.undirected > 2

    @property
    def isDiatonicStep(self) -> bool:
        '''
        Return True if this interval is a step (a second).
        A synonym for `isStep` for generic intervals.

        >>> interval.GenericInterval(-2).isDiatonicStep
        True
        >>> interval.GenericInterval(1).isDiatonicStep
        False
        >>> interval.GenericInterval(9).isDiatonicStep
        False

        Note that Unisons are neither steps nor skips.
        '''
        return self.undirected == 2

    @property
    def isStep(self) -> bool:
        '''
        Return True if this interval is a step (a second).
        A synonym for `isDiatonicStep` for generic intervals.

        >>> interval.GenericInterval(2).isStep
        True
        >>> interval.GenericInterval(1).isStep
        False
        >>> interval.GenericInterval(-9).isStep
        False
        '''
        return self.isDiatonicStep

    @property
    def isUnison(self) -> bool:
        '''
        Returns True if this interval is a Unison.

        Note that Unisons are neither steps nor skips.
        '''
        return self.undirected == 1

    @property
    def _simpleStepsAndOctaves(self) -> t.Tuple[int, int]:
        '''
        Returns simpleUndirectedSteps and undirectedOctaves.
        '''
        # unisons (even augmented) are neither steps nor skips.
        steps, octaves = math.modf(self.undirected / 7)
        steps = int(steps * 7 + 0.001)
        octaves = int(octaves)
        if steps == 0:
            octaves = octaves - 1
            steps = 7
        return steps, octaves

    @property
    def simpleUndirected(self) -> int:
        '''
        Return the undirected distance within an octave

        >>> interval.GenericInterval('Descending Ninth').simpleUndirected
        2
        >>> interval.GenericInterval(8).simpleUndirected
        1
        '''
        return self._simpleStepsAndOctaves[0]

    @property
    def semiSimpleUndirected(self) -> int:
        '''
        Same as simpleUndirected, but allows octaves and double octaves, etc.
        to remain 8, which is useful for a
        number of parallel octave vs. unison routines.

        >>> interval.GenericInterval('Descending Ninth').semiSimpleUndirected
        2
        >>> interval.GenericInterval(8).semiSimpleUndirected
        8
        >>> interval.GenericInterval(-15).semiSimpleUndirected
        8
        '''
        simpleUndirected = self.simpleUndirected
        if self.undirectedOctaves >= 1 and simpleUndirected == 1:
            return 8
        else:
            return simpleUndirected

    @property
    def undirectedOctaves(self) -> int:
        '''
        Returns the number of octaves (without direction) for an interval

        >>> interval.GenericInterval(5).undirectedOctaves
        0
        >>> interval.GenericInterval('Descending Ninth').undirectedOctaves
        1
        >>> interval.GenericInterval(8).undirectedOctaves
        1
        >>> interval.GenericInterval(-15).undirectedOctaves
        2
        '''
        return self._simpleStepsAndOctaves[1]

    @property
    def octaves(self) -> int:
        '''
        Return the number of octaves with direction.

        >>> interval.GenericInterval(5).octaves
        0
        >>> interval.GenericInterval('Descending Ninth').octaves
        -1
        >>> interval.GenericInterval(8).octaves
        1
        >>> interval.GenericInterval(-15).octaves
        -2
        '''
        undirectedOctaves = self.undirectedOctaves
        if self.direction == Direction.DESCENDING:
            return -1 * undirectedOctaves
        else:
            return undirectedOctaves

    @property
    def simpleDirected(self) -> int:
        '''
        Return the directed distance within an octave

        >>> interval.GenericInterval('Descending Ninth').simpleDirected
        -2
        >>> interval.GenericInterval(8).simpleDirected
        1
        >>> interval.GenericInterval(-8).simpleDirected
        1
        '''
        simpleUndirected = self.simpleUndirected
        if self.direction == Direction.DESCENDING and simpleUndirected > 1:
            return -1 * simpleUndirected
        else:
            return simpleUndirected

    @property
    def semiSimpleDirected(self) -> int:
        '''
        Return the same as semiSimpleUndirected but with descending intervals
        as a negative number

        >>> interval.GenericInterval('Descending Ninth').semiSimpleDirected
        -2
        >>> interval.GenericInterval(8).semiSimpleDirected
        8
        >>> interval.GenericInterval(-15).semiSimpleDirected
        -8
        >>> interval.GenericInterval(-8).semiSimpleDirected
        -8
        '''
        semiSimpleUndirected = self.semiSimpleUndirected
        if self.direction == Direction.DESCENDING and semiSimpleUndirected > 1:
            return -1 * semiSimpleUndirected
        else:
            return semiSimpleUndirected

    @property
    def perfectable(self) -> bool:
        '''
        Returns True if the interval might represent a perfect interval,
        that is, it is a Generic 4th, 5th, or unison/octave

        >>> interval.GenericInterval(4).perfectable
        True
        >>> interval.GenericInterval(-12).perfectable
        True
        >>> interval.GenericInterval(3).perfectable
        False
        '''
        return self.simpleUndirected in (1, 4, 5)

    def _nameFromInt(self, keyVal: int) -> str:
        try:
            return common.numberTools.musicOrdinals[keyVal]
        except IndexError:
            return str(keyVal) + common.numberTools.ordinalAbbreviation(keyVal)

    @property
    def niceName(self) -> str:
        '''
        Return the niceName as a string for this Interval

        >>> interval.GenericInterval(4).niceName
        'Fourth'
        >>> interval.GenericInterval(-12).niceName
        'Twelfth'
        >>> interval.GenericInterval(3).niceName
        'Third'

        Extremely large intervals get displayed as abbreviations

        >>> interval.GenericInterval(44).niceName
        '44th'

        Changed in v6: large numbers get the 'th' or 'rd' etc. suffix
        '''
        return self._nameFromInt(self.undirected)

    @property
    def simpleNiceName(self) -> str:
        '''
        Return the niceName as a string for this Interval's simple form

        >>> interval.GenericInterval(4).simpleNiceName
        'Fourth'
        >>> interval.GenericInterval(-12).simpleNiceName
        'Fifth'
        >>> interval.GenericInterval(8).simpleNiceName
        'Unison'
        '''
        return self._nameFromInt(self.simpleUndirected)


    @property
    def semiSimpleNiceName(self) -> str:
        '''
        Return the niceName as a string for this Interval's semiSimple form

        >>> interval.GenericInterval(4).semiSimpleNiceName
        'Fourth'
        >>> interval.GenericInterval(-12).semiSimpleNiceName
        'Fifth'
        >>> interval.GenericInterval(8).semiSimpleNiceName
        'Octave'
        '''
        return self._nameFromInt(self.semiSimpleUndirected)

    @property
    def staffDistance(self) -> int:
        '''
        Return the number of spaces/stafflines that this
        interval represents.  A unison is 0, an ascending second is 1,
        a descending third is -2, etc.

        Useful for interval arithmetic

        >>> interval.GenericInterval('Ascending Third').staffDistance
        2
        >>> interval.GenericInterval(-8).staffDistance
        -7
        >>> interval.GenericInterval(1).staffDistance
        0
        '''
        directed = self.directed
        if directed > 0:
            return directed - 1
        else:
            return directed + 1

    @property
    def mod7inversion(self) -> int:
        '''
        Return the inversion of this interval within an octave.
        For instance, seconds become sevenths, octaves become unisons,
        and vice-versa.

        All are undirected intervals.

        >>> interval.GenericInterval(4).mod7inversion
        5
        >>> interval.GenericInterval('Descending Octave').mod7inversion
        1
        >>> interval.GenericInterval(9).mod7inversion
        7
        '''
        return 9 - self.semiSimpleUndirected

    @property
    def mod7(self) -> int:
        '''
        Return this interval as a number 1-7, that is, within an octave,
        but unlike simpleDirected or simpleUndirected, turn descending
        seconds into sevenths, etc.  Used for calculating step names.

        For instance, going down a step from C, or GenericInterval(-2),
        would give a B, which is the same as GenericInterval(7) (not counting
        octaves), but going up a step from C, or GenericInterval(2) is D, which
        is the same as going up a 9th.

        >>> interval.GenericInterval(-2).mod7
        7
        >>> interval.GenericInterval(2).mod7
        2
        >>> interval.GenericInterval(9).mod7
        2
        >>> interval.GenericInterval('Unison').mod7
        1
        >>> interval.GenericInterval('Descending Octave').mod7
        1
        >>> interval.GenericInterval(15).mod7
        1

        See :meth:`music21.chord.Chord.semitonesFromChordStep` for a place
        this is used.
        '''
        if self.direction == Direction.DESCENDING:
            return self.mod7inversion
        else:
            return self.simpleDirected


    @cacheMethod
    def complement(self) -> GenericInterval:
        '''
        Returns a new GenericInterval object where 3rds are 6ths, etc.

        >>> third = interval.GenericInterval('Third')
        >>> third.complement()
        <music21.interval.GenericInterval 6>

        Note that currently direction is lost after a complement relationship:

        >>> fourth = interval.GenericInterval(-4)
        >>> fourthComp = fourth.complement()
        >>> fourthComp
        <music21.interval.GenericInterval 5>
        >>> fourthComp.directed
        5

        Called more than once, this may return the exact identical object:

        >>> fourthComp.complement() is fourthComp.complement()
        True
        '''
        return GenericInterval(self.mod7inversion)

    def reverse(self) -> GenericInterval:
        '''
        Returns a new GenericInterval object that is inverted.

        >>> aInterval = interval.GenericInterval('Third')
        >>> aInterval.reverse()
        <music21.interval.GenericInterval -3>

        >>> aInterval = interval.GenericInterval(-13)
        >>> aInterval.direction
        <Direction.DESCENDING: -1>
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

    def transposePitch(self, p: 'music21.pitch.Pitch', *, inPlace=False):
        '''
        transpose a pitch, retaining the accidental if any.

        >>> aPitch = pitch.Pitch('g4')
        >>> genericFifth = interval.GenericInterval(5)
        >>> bPitch = genericFifth.transposePitch(aPitch)
        >>> bPitch
        <music21.pitch.Pitch D5>

        If inPlace is True then applied to the current pitch:

        >>> gPitch = pitch.Pitch('g4')
        >>> genericFifth = interval.GenericInterval(5)
        >>> genericFifth.transposePitch(gPitch, inPlace=True)
        >>> gPitch
        <music21.pitch.Pitch D5>

        A generic interval transformation retains accidentals:

        >>> a2 = pitch.Pitch('B-')
        >>> cPitch = genericFifth.transposePitch(a2)
        >>> cPitch
        <music21.pitch.Pitch F->
        >>> a2.octave == cPitch.octave
        True

        Can be done inPlace as well, in which case, nothing is returned:

        >>> gSharp = pitch.Pitch('g#4')
        >>> genericFifth = interval.GenericInterval(5)
        >>> genericFifth.transposePitch(gSharp, inPlace=True)
        >>> gSharp
        <music21.pitch.Pitch D#5>
        '''
        if p.octave is None:
            useImplicitOctave = True
        else:
            useImplicitOctave = False
        pitchDNN = p.diatonicNoteNum

        if inPlace:
            newPitch = p
        else:
            newPitch = copy.deepcopy(p)

        newPitch.diatonicNoteNum = pitchDNN + self.staffDistance
        if useImplicitOctave is True:
            newPitch.octave = None

        if not inPlace:
            return newPitch

    def transposePitchKeyAware(
        self,
        p: 'music21.pitch.Pitch',
        k: t.Optional['music21.key.KeySignature'] = None,
        *,
        inPlace: bool = False
    ):
        '''
        Transposes a pitch while remaining aware of its key context,
        for modal transposition:

        If k is None, works the same as `.transposePitch`:

        >>> aPitch = pitch.Pitch('g4')
        >>> genericFifth = interval.GenericInterval(5)
        >>> bPitch = genericFifth.transposePitchKeyAware(aPitch, None)
        >>> bPitch
        <music21.pitch.Pitch D5>

        But if a key or keySignature (such as one from `.getContextByClass(key.KeySignature)`)
        is given, then the fun begins...

        >>> fis = pitch.Pitch('F#4')
        >>> e = pitch.Pitch('E')
        >>> gMaj = key.Key('G')
        >>> genericStep = interval.GenericInterval('second')
        >>> genericStep.transposePitchKeyAware(fis, gMaj)
        <music21.pitch.Pitch G4>
        >>> genericStep.transposePitchKeyAware(e, gMaj)
        <music21.pitch.Pitch F#>

        If a pitch already has an accidental that contradicts the current
        key, the difference between that pitch and the new key is applied
        to the new pitch:

        >>> fNat = pitch.Pitch('F4')
        >>> genericStep.transposePitchKeyAware(fNat, gMaj)
        <music21.pitch.Pitch G-4>

        inPlace should work:

        >>> genericStep.transposePitchKeyAware(fis, gMaj, inPlace=True)
        >>> fis
        <music21.pitch.Pitch G4>

        This is used for Stream.transpose when a GenericInterval is given:

        >>> s = converter.parse('tinyNotation: 4/4 d4 e f f# g1 a-4 g b- a c1')
        >>> s.measure(1).insert(0, key.Key('G'))
        >>> s.measure(3).insert(0, key.Key('c'))
        >>> s2 = s.transpose(interval.GenericInterval(2))
        >>> s2.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.key.Key of G major>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note F#>
            {2.0} <music21.note.Note G->
            {3.0} <music21.note.Note G>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.key.Key of c minor>
            {0.0} <music21.note.Note B->
            {1.0} <music21.note.Note A->
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note B>
        {12.0} <music21.stream.Measure 4 offset=12.0>
            {0.0} <music21.note.Note D>
            {4.0} <music21.bar.Barline type=final>

        Does not take into account harmonic or melodic minor.
        '''
        from music21 import pitch

        if k is None:
            return self.transposePitch(p, inPlace=inPlace)

        accidentalByStep = k.accidentalByStep(p.step)
        stepAlter = accidentalByStep.alter if accidentalByStep is not None else 0
        pAlter = p.accidental.alter if p.accidental is not None else 0
        offsetFromKey = pAlter - stepAlter

        newPitch = self.transposePitch(p, inPlace=inPlace)
        if inPlace is True:
            newPitch = p

        newAccidentalByStep = k.accidentalByStep(newPitch.step)
        newStepAlter = newAccidentalByStep.alter if newAccidentalByStep is not None else 0

        newPitchAlter = newStepAlter + offsetFromKey
        if newPitchAlter != 0:
            newPitch.accidental = pitch.Accidental(newPitchAlter)
        elif newPitch.accidental is not None:
            newPitch.accidental = None

        if inPlace is False:
            return newPitch

    def getDiatonic(self, specifier: t.Union[Specifier, str]) -> DiatonicInterval:
        '''
        Given a specifier, return a :class:`~music21.interval.DiatonicInterval` object.

        Specifier should be provided as an `interval.Specifier` enumeration or
        a string name, such as 'dd', 'M', or 'perfect'.

        >>> third = interval.GenericInterval('Third')
        >>> third.getDiatonic(interval.Specifier.MAJOR)
        <music21.interval.DiatonicInterval M3>
        >>> third.getDiatonic('minor')
        <music21.interval.DiatonicInterval m3>
        >>> third.getDiatonic('d')
        <music21.interval.DiatonicInterval d3>
        >>> third.getDiatonic(interval.Specifier.TRPAUG)
        <music21.interval.DiatonicInterval AAA3>

        Old in, specifier values are also allowed

        >>> third.getDiatonic(2)
        <music21.interval.DiatonicInterval M3>

        >>> fifth = interval.GenericInterval('fifth')
        >>> fifth.getDiatonic('perfect')
        <music21.interval.DiatonicInterval P5>

        >>> fifth.getDiatonic('major')
        Traceback (most recent call last):
        music21.interval.IntervalException: Cannot create a 'Major Fifth'
        '''
        return DiatonicInterval(specifier, self)


class DiatonicInterval(IntervalBase):
    '''
    A class representing a diatonic interval. Two required arguments are a string `specifier`
    (such as perfect, major, or minor) and `generic`, either an int
    of an interval size (such as 2, 2nd, or second) or a
    :class:`~music21.interval.GenericInterval` object.

    Two DiatonicIntervals are the same if their GenericIntervals
    are the same and their specifiers are the same and they should be
    if their directions are the same, but this is not checked yet.

    The `specifier` is an enumeration/Specifier object.

    The `generic` is an integer or GenericInterval instance.

    >>> unison = interval.DiatonicInterval(interval.Specifier.PERFECT, 1)
    >>> unison
    <music21.interval.DiatonicInterval P1>
    >>> unison.simpleName
    'P1'
    >>> unison.specifier
    <Specifier.PERFECT>
    >>> unison.generic
    <music21.interval.GenericInterval 1>
    >>> unison.direction
    <Direction.OBLIQUE: 0>

    The first value can be a string:

    >>> major3a = interval.DiatonicInterval('major', 3)
    >>> major3a.simpleName
    'M3'
    >>> major3a.niceName
    'Major Third'
    >>> major3a.semiSimpleName
    'M3'
    >>> major3a.directedSimpleName
    'M3'
    >>> major3a.mod7inversion
    'm6'

    Or the first attribute can be a string abbreviation
    (not case sensitive, except Major vs. minor):

    >>> major3b = interval.DiatonicInterval('M', 3)
    >>> major3b.niceName
    'Major Third'

    A string can be given for the second argument (generic interval):

    >>> major3c = interval.DiatonicInterval('major', 'third')
    >>> major3c.niceName
    'Major Third'

    >>> p8 = interval.DiatonicInterval('perfect', 'octave')
    >>> p8.niceName
    'Perfect Octave'

    >>> genericTenth = interval.GenericInterval(10)
    >>> minor10 = interval.DiatonicInterval('m', genericTenth)
    >>> minor10.mod7
    'm3'
    >>> minor10.isDiatonicStep
    False
    >>> minor10.isStep
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

    For Augmented Unisons, the diatonic interval is ascending while the `.generic` is oblique:

    >>> augAscending.direction
    <Direction.ASCENDING: 1>
    >>> augAscending.generic.direction
    <Direction.OBLIQUE: 0>

    >>> dimDescending = augAscending.reverse()
    >>> dimDescending
    <music21.interval.DiatonicInterval d1>
    >>> dimDescending.directedNiceName
    'Descending Diminished Unison'
    >>> dimDescending.direction
    <Direction.DESCENDING: -1>


    This raises an error:

    >>> interval.DiatonicInterval('Perfect', -1)
    Traceback (most recent call last):
    music21.interval.IntervalException: There is no such thing as a descending Perfect Unison
    '''
    _DOC_ATTR: t.Dict[str, str] = {
        'specifier': 'A :class:`~music21.interval.Specifier` enum representing '
                     + 'the Quality of the interval.',
        'generic': 'A :class:`~music21.interval.GenericInterval` enum representing '
                   + 'the general interval.',
    }

    def __init__(self,
                 specifier: t.Union[str, int] = 'P',
                 generic: t.Union[int, GenericInterval, str] = 1,
                 **keywords):
        super().__init__(**keywords)

        self.generic: GenericInterval
        self.specifier: Specifier

        if isinstance(generic, GenericInterval):
            self.generic = generic
        elif common.isNum(generic) or isinstance(generic, str):
            self.generic = GenericInterval(generic)
        else:  # pragma: no cover
            # too rare to cover.
            raise IntervalException(f'incorrect generic argument: {generic!r}')

        # translate strings, if provided, to integers
        # specifier here is the index number in the prefixSpecs list
        self.specifier = parseSpecifier(specifier)

        if ((self.specifier in (Specifier.MAJOR, Specifier.MINOR) and self.generic.perfectable)
                or (self.specifier == Specifier.PERFECT and not self.generic.perfectable)):
            raise IntervalException(
                f"Cannot create a '{self.specifier.niceName} {self.generic.niceName}'"
            )

        if self.specifier == Specifier.PERFECT and self.generic.value == -1:
            raise IntervalException('There is no such thing as a descending Perfect Unison')

    def _reprInternal(self) -> str:
        return self.name

    def __eq__(self, other):
        '''
        True if generic, specifier, and direction are the same.

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

        Intervals do not compare to strings:

        >>> e == 'd4'
        False
        '''
        if not hasattr(other, 'generic'):
            return False
        elif not hasattr(other, 'specifier'):
            return False

        # untested...
        # if self.direction != other.direction:
        #    return False
        if (self.generic == other.generic
            and self.specifier == other.specifier
                and self.direction == other.direction):
            return True
        else:
            return False

    @property
    def name(self) -> str:
        '''
        The name of the interval in abbreviated form without direction.

        >>> interval.DiatonicInterval('Perfect', 'Fourth').name
        'P4'
        >>> interval.DiatonicInterval(interval.Specifier.MAJOR, -6).name
        'M6'
        '''
        return str(self.specifier) + str(self.generic.undirected)

    @property
    def niceName(self) -> str:
        '''
        Return the full form of the name of a Diatonic interval

        >>> interval.DiatonicInterval('P', 4).niceName
        'Perfect Fourth'
        '''
        return self.specifier.niceName + ' ' + self.generic.niceName

    @property
    def specificName(self) -> str:
        '''
        Same as `.specifier.niceName` -- the nice name of the specifier alone

        >>> p12 = interval.DiatonicInterval('P', -12)
        >>> p12.specificName
        'Perfect'
        '''
        return self.specifier.niceName

    @property
    def simpleName(self) -> str:
        '''
        Return the name of a Diatonic interval removing octaves

        >>> interval.DiatonicInterval('Augmented', 'Twelfth').simpleName
        'A5'
        '''
        return str(self.specifier) + str(self.generic.simpleUndirected)

    @property
    def simpleNiceName(self) -> str:
        '''
        Return the full name of a Diatonic interval, simplifying octaves

        >>> interval.DiatonicInterval('d', 14).simpleNiceName
        'Diminished Seventh'
        '''
        return self.specifier.niceName + ' ' + self.generic.simpleNiceName

    @property
    def semiSimpleName(self) -> str:
        '''
        Return the name of a Diatonic interval removing octaves except that
        octaves (and double octaves) themselves are 8 instead of 1

        >>> interval.DiatonicInterval('Augmented', 'Twelfth').semiSimpleName
        'A5'
        >>> interval.DiatonicInterval('Diminished', 'Descending Octave').semiSimpleName
        'd8'
        '''
        return str(self.specifier) + str(self.generic.semiSimpleUndirected)

    @property
    def semiSimpleNiceName(self) -> str:
        '''
        Return the full name of a Diatonic interval removing octaves except that
        octaves (and double octaves) themselves are 8 instead of 1

        >>> interval.DiatonicInterval('Augmented', 'Twelfth').semiSimpleNiceName
        'Augmented Fifth'
        >>> interval.DiatonicInterval('Diminished', 'Descending Octave').semiSimpleNiceName
        'Diminished Octave'
        '''
        return self.specifier.niceName + ' ' + self.generic.semiSimpleNiceName

    @property
    def direction(self) -> Direction:
        '''
        The direction of the DiatonicInterval:

        >>> interval.DiatonicInterval('Augmented', 'Twelfth').direction
        <Direction.ASCENDING: 1>

        >>> interval.DiatonicInterval('M', -2).direction
        <Direction.DESCENDING: -1>

        >>> interval.DiatonicInterval('P', 1).direction
        <Direction.OBLIQUE: 0>

        In the absence of other evidence, assumes that augmented unisons are
        ascending and diminished unisons are descending:

        >>> interval.DiatonicInterval('d', 1).direction
        <Direction.DESCENDING: -1>

        >>> interval.DiatonicInterval('A', 1).direction
        <Direction.ASCENDING: 1>

        Note that in the case of non-perfect unisons/primes, the `.generic.direction`
        will be `OBLIQUE` while the diatonic direction may be ASCENDING, DESCENDING,
        or OBLIQUE.

        >>> interval.DiatonicInterval('A', 1).generic.direction
        <Direction.OBLIQUE: 0>

        '''
        if self.generic.undirected != 1:
            return self.generic.direction

        if self.specifier == Specifier.PERFECT:
            return self.generic.direction  # should be oblique

        # assume in the absence of other evidence,
        # that augmented unisons are ascending and dim are descending
        if perfSpecifiers.index(self.specifier) <= perfSpecifiers.index(Specifier.DIMINISHED):
            # orderedPerfSpecs is not the same as .value.
            return Direction.DESCENDING
        else:
            return Direction.ASCENDING

    @property
    def directedName(self) -> str:
        '''
        The name of the interval in abbreviated form with direction.

        >>> interval.DiatonicInterval('Minor', -6).directedName
        'm-6'
        '''
        return str(self.specifier) + str(self.generic.directed)

    @property
    def directedNiceName(self) -> str:
        '''
        The name of the interval in full form with direction.

        >>> interval.DiatonicInterval('P', 11).directedNiceName
        'Ascending Perfect Eleventh'
        >>> interval.DiatonicInterval('Diminished', 'Descending Octave').directedNiceName
        'Descending Diminished Octave'
        '''
        return directionTerms[self.direction] + ' ' + self.niceName

    @property
    def directedSimpleName(self) -> str:
        '''
        The name of the interval in abbreviated form with direction, reduced to one octave

        >>> interval.DiatonicInterval('Minor', -14).directedSimpleName
        'm-7'
        '''
        return str(self.specifier) + str(self.generic.simpleDirected)

    @property
    def directedSimpleNiceName(self) -> str:
        '''
        The name of the interval, reduced to within an octave, in full form with direction.

        >>> interval.DiatonicInterval('P', 11).directedNiceName
        'Ascending Perfect Eleventh'
        >>> interval.DiatonicInterval('Diminished', 'Descending Octave').directedNiceName
        'Descending Diminished Octave'
        '''
        return directionTerms[self.direction] + ' ' + self.simpleNiceName

    @property
    def directedSemiSimpleName(self) -> str:
        '''
        The name of the interval in abbreviated form with direction, reduced to one octave,
        except for octaves themselves

        >>> interval.DiatonicInterval('Minor', -14).directedSemiSimpleName
        'm-7'
        >>> interval.DiatonicInterval('P', 'Octave').directedSemiSimpleName
        'P8'
        '''
        return str(self.specifier) + str(self.generic.semiSimpleDirected)

    @property
    def directedSemiSimpleNiceName(self) -> str:
        '''
        The name of the interval in full form with direction.

        >>> interval.DiatonicInterval('P', 11).directedSemiSimpleNiceName
        'Ascending Perfect Fourth'
        >>> interval.DiatonicInterval('Diminished', 'Descending Octave').directedSemiSimpleNiceName
        'Descending Diminished Octave'
        '''
        return directionTerms[self.direction] + ' ' + self.semiSimpleNiceName


    @property
    def isStep(self) -> bool:
        '''
        Same as GenericInterval.isStep and .isDiatonicStep

        >>> interval.DiatonicInterval('M', 2).isStep
        True
        >>> interval.DiatonicInterval('P', 5).isStep
        False
        '''
        return self.generic.isStep

    @property
    def isDiatonicStep(self) -> bool:
        '''
        Same as GenericInterval.isDiatonicStep and .isStep

        >>> interval.DiatonicInterval('M', 2).isDiatonicStep
        True
        >>> interval.DiatonicInterval('P', 5).isDiatonicStep
        False
        '''
        return self.generic.isDiatonicStep

    @property
    def isSkip(self) -> bool:
        '''
        Same as GenericInterval.isSkip

        >>> interval.DiatonicInterval('M', 2).isSkip
        False
        >>> interval.DiatonicInterval('P', 5).isSkip
        True
        '''
        return self.generic.isSkip

    @property
    def perfectable(self) -> bool:
        '''
        Is the generic component of this interval able to be made perfect?
        That is, is this a type of unison, fourth, fifth, or octave (or larger
        component).

        Note that this does not ask if THIS interval is perfect.  A diminished
        fifth is not perfect, but as a fifth it is perfectable.

        An augmented seventh sounds like a perfect octave but no seventh can
        ever be perfect.

        >>> interval.DiatonicInterval('M', 2).perfectable
        False
        >>> interval.DiatonicInterval('P', 12).perfectable
        True
        >>> interval.DiatonicInterval('A', 12).perfectable
        True
        '''
        return self.generic.perfectable

    @property
    def mod7inversion(self) -> str:
        '''
        Return an inversion of the interval within an octave, losing
        direction.  Returns as a string.

        >>> interval.DiatonicInterval('M', 2).mod7inversion
        'm7'
        >>> interval.DiatonicInterval('A', 4).mod7inversion
        'd5'
        >>> interval.DiatonicInterval('P', 1).mod7inversion
        'P8'

        Everything is within an octave:

        >>> interval.DiatonicInterval('M', 9).mod7inversion
        'm7'

        Direction is lost:

        >>> interval.DiatonicInterval('d', -3).mod7inversion
        'A6'
        '''
        return str(self.specifier.inversion()) + str(self.generic.mod7inversion)


    @property
    def mod7(self) -> str:
        '''
        Return this interval as string of a specifier followed by a number 1-7,
        representing a diatonic interval within an octave,
        but unlike simpleDirected or simpleUndirected, turns descending
        seconds into sevenths, etc.

        For instance, going down a minor second from C
        would give a B, which is the same as going up a major seventh to B.

        This method gives a string representing a diatonic interval that
        will reach the same note as this DiatonicInterval but within an octave
        up from the basic note.

        >>> interval.DiatonicInterval('m', -2).mod7
        'M7'
        >>> interval.DiatonicInterval('m', 2).mod7
        'm2'
        >>> interval.DiatonicInterval('M', 9).mod7
        'M2'
        >>> interval.DiatonicInterval('Perfect', 'Unison').mod7
        'P1'
        >>> interval.DiatonicInterval('Perfect', 'Descending Octave').mod7
        'P1'
        >>> interval.DiatonicInterval(interval.Specifier.AUGMENTED, -4).mod7
        'd5'

        See :meth:`music21.chord.Chord.semitonesFromChordStep` for a place
        this is used.
        '''
        if self.direction == Direction.DESCENDING:
            return self.mod7inversion
        else:
            return self.simpleName



    # -------------------------------------------------------
    # methods

    def reverse(self) -> DiatonicInterval:
        '''
        Return a :class:`~music21.interval.DiatonicInterval` that is
        an inversion of this Interval.

        >>> aInterval = interval.DiatonicInterval('major', 3)
        >>> aInterval.reverse().directedName
        'M-3'

        >>> aInterval = interval.DiatonicInterval('augmented', 5)
        >>> aInterval.reverse().directedName
        'A-5'

        (Ascending) Augmented Unisons reverse to (Descending)
        Diminished Unisons and vice-versa

        >>> aug1 = interval.DiatonicInterval('augmented', 1)
        >>> aug1.direction
        <Direction.ASCENDING: 1>
        >>> aug1.directedName
        'A1'
        >>> dimUnison = aug1.reverse()
        >>> dimUnison.directedName
        'd1'
        >>> dimUnison.directedNiceName
        'Descending Diminished Unison'
        '''
        if self.generic.directed == 1:
            return DiatonicInterval(self.specifier.inversion(), 1)
        else:
            return DiatonicInterval(self.specifier,
                                    self.generic.reverse())

    def getChromatic(self) -> ChromaticInterval:
        '''
        Return a :class:`music21.interval.ChromaticInterval`
        based on the size of this Interval.

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

        octaveOffset = int(abs(self.generic.staffDistance) / 7)
        semitonesStart = semitonesGeneric[self.generic.simpleUndirected]

        if self.generic.perfectable:
            # dictionary of semitone distances from perfect
            semitonesAdjust = self.specifier.semitonesAbovePerfect()
        else:
            # dictionary of semitone distances from major
            semitonesAdjust = self.specifier.semitonesAboveMajor()

        semitones = (octaveOffset * 12) + semitonesStart + semitonesAdjust
        # want direction to be same as original direction
        if self.generic.direction == Direction.DESCENDING:
            semitones *= -1  # (automatically positive until this step)

        return ChromaticInterval(semitones)

    def transposePitch(self, p: 'music21.pitch.Pitch', *, inPlace=False):
        # noinspection PyShadowingNames
        '''
        Calls transposePitch from a full interval object.

        This is not particularly optimized since it
        requires creating both a ChromaticInterval
        object and a full Interval object. But it's here for completeness.

        >>> di = interval.DiatonicInterval('P', 11)
        >>> p = pitch.Pitch('C#4')
        >>> di.transposePitch(p)
        <music21.pitch.Pitch F#5>

        Previous pitch was unchanged.  inPlace=True changes that.

        >>> p
        <music21.pitch.Pitch C#4>
        >>> di.transposePitch(p, inPlace=True)
        >>> p
        <music21.pitch.Pitch F#5>


        Changed in v.6 -- added inPlace
        '''
        fullIntervalObject = Interval(diatonic=self, chromatic=self.getChromatic())
        return fullIntervalObject.transposePitch(p, inPlace=inPlace)

    @property
    def specifierAbbreviation(self) -> str:
        '''
        Returns the abbreviation for the specifier.

        >>> i = interval.Interval('M-10')
        >>> d = i.diatonic
        >>> d.specifierAbbreviation
        'M'
        '''
        return prefixSpecs[self.specifier]

    @property
    def cents(self) -> float:
        '''
        Return the number of cents in this interval.  Returns a float,
        always assuming an equal-tempered presentation.

        >>> i = interval.DiatonicInterval('minor', 'second')
        >>> i.niceName
        'Minor Second'
        >>> i.cents
        100.0
        '''
        c = self.getChromatic()
        if c:
            return c.cents
        else:
            return 0.0


class ChromaticInterval(IntervalBase):
    '''
    Chromatic interval class. Unlike a :class:`~music21.interval.DiatonicInterval`,
    this IntervalBase subclass treats interval spaces in half-steps.
    So Major 3rd and Diminished 4th are the same.

    Two ChromaticIntervals are equal if their size and direction are equal.

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

    def __init__(self, semitones: t.Union[int, float] = 0, **keywords):
        super().__init__(**keywords)

        if semitones == int(semitones):
            semitones = int(semitones)

        self.semitones: t.Union[int, float] = semitones

    def _reprInternal(self) -> str:
        return str(self.directed)

    def __eq__(self, other):
        '''
        True if number of semitones is the same.

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

        Intervals do not equal numbers:

        >>> interval.ChromaticInterval(7) == 7
        False
        '''
        if not hasattr(other, 'semitones'):
            return False

        if self.semitones == other.semitones:
            return True
        else:
            return False

    # -------------------------------------------------------
    # properties

    @property
    def cents(self) -> float:
        '''
        Return the number of cents in a ChromaticInterval:

        >>> dime = interval.ChromaticInterval(0.1)
        >>> dime.cents
        10.0
        '''
        return round(self.semitones * 100.0, 5)

    @property
    def directed(self) -> t.Union[int, float]:
        '''
        A synonym for `.semitones`

        >>> tritoneDown = interval.ChromaticInterval(-6)
        >>> tritoneDown.directed
        -6
        '''
        return self.semitones

    @property
    def undirected(self) -> t.Union[int, float]:
        '''
        The absolute value of the number of semitones:

        >>> tritoneDown = interval.ChromaticInterval(-6)
        >>> tritoneDown.undirected
        6
        '''
        return abs(self.semitones)

    @property
    def direction(self) -> Direction:
        '''
        Returns an enum of the direction:

        >>> interval.ChromaticInterval(-3).direction
        <Direction.DESCENDING: -1>

        note that the number can be helpful for multiplication:

        >>> interval.ChromaticInterval(-3).direction * 9
        -9
        '''
        if self.directed > 0:
            return Direction.ASCENDING
        if self.directed < 0:
            return Direction.DESCENDING

        return Direction.OBLIQUE

    @property
    def mod12(self) -> t.Union[int, float]:
        '''
        The number of semitones within an octave using modulo arithmatic.

        (see :meth:`~music21.interval.ChromaticInterval.simpleUndirected`
        for a similar method that puts musical
        intuition above mathematical intuition)

        >>> interval.ChromaticInterval(15).mod12
        3
        >>> interval.ChromaticInterval(-4).mod12
        8
        >>> interval.ChromaticInterval(-16).mod12
        8
        '''
        return self.semitones % 12

    @property
    def simpleUndirected(self) -> t.Union[int, float]:
        '''
        The number of semitones within an octave while ignoring direction.

        (see :meth:`~music21.interval.ChromaticInterval.mod12`
        for a similar method that puts mathematical
        intuition above musical intuition)

        >>> interval.ChromaticInterval(15).simpleUndirected
        3
        >>> interval.ChromaticInterval(-4).simpleUndirected
        4
        >>> interval.ChromaticInterval(-16).simpleUndirected
        4
        '''
        return self.undirected % 12

    @property
    def simpleDirected(self) -> t.Union[int, float]:
        '''
        The number of semitones within an octave while preserving direction.

        >>> interval.ChromaticInterval(15).simpleDirected
        3
        >>> interval.ChromaticInterval(-4).simpleDirected
        -4
        >>> interval.ChromaticInterval(-16).simpleDirected
        -4
        '''
        if self.direction == Direction.DESCENDING:
            return -1 * self.simpleUndirected
        else:
            return self.simpleUndirected

    @property
    def intervalClass(self) -> int:
        mod12 = int(self.mod12)
        if mod12 > 6:
            return 12 - mod12
        else:
            return mod12

    @property
    def isChromaticStep(self) -> bool:
        return self.undirected == 1

    @property
    def isStep(self) -> bool:
        return self.isChromaticStep


    # -------------------------------------------------------
    # methods

    def reverse(self) -> ChromaticInterval:
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

    def getDiatonic(self) -> DiatonicInterval:
        '''
        Given a ChromaticInterval, return a :class:`~music21.interval.DiatonicInterval`
        object of the same size.

        While there is more than one Generic Interval for any given chromatic
        interval, this is needed to permit easy chromatic specification of
        Interval objects.  Augmented or diminished intervals are never returned
        except for the interval of 6 which returns a diminished fifth, not
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
        # microtones get rounded here.
        specifier, generic = convertSemitoneToSpecifierGeneric(self.semitones)
        return DiatonicInterval(specifier, generic)

    def transposePitch(self, p: 'music21.pitch.Pitch', *, inPlace=False):
        # noinspection PyShadowingNames
        '''
        Given a :class:`~music21.pitch.Pitch` object, return a new,
        transposed Pitch, that is transformed
        according to this ChromaticInterval.

        Because :class:`~music21.interval.ChromaticInterval` object
        do not take into account diatonic spelling,
        the new Pitch is simplified to the most common intervals.  See
        :meth:`~music21.pitch.Pitch.simplifyEnharmonic` with ``mostCommon = True``
        to see the results.

        >>> tritone = interval.ChromaticInterval(6)
        >>> p = pitch.Pitch('E#4')
        >>> p2 = tritone.transposePitch(p)
        >>> p2
        <music21.pitch.Pitch B4>
        >>> p3 = tritone.transposePitch(p2)
        >>> p3
        <music21.pitch.Pitch F5>

        If no octave number is given then octaves "wrap around" and thus even
        after transposing upward, you could end up with a pitch that is
        displayed as lower than the original:

        >>> p4 = pitch.Pitch('B')
        >>> p4.ps
        71.0
        >>> p5 = tritone.transposePitch(p4)

        Since the octave on p4 was implicit, the ps here wraps around

        >>> p5.ps
        65.0

        Afterwards, spelling of the new pitch will always be inferred.

        >>> p4.spellingIsInferred
        False
        >>> p5.spellingIsInferred
        True

        Can be done inPlace as well:

        >>> p = pitch.Pitch('E#4')
        >>> tritone.transposePitch(p, inPlace=True)
        >>> p
        <music21.pitch.Pitch B4>
        >>> p.spellingIsInferred
        True

        Changed in v.6 -- added inPlace
        '''
        if p.octave is None:
            useImplicitOctave = True
        else:
            useImplicitOctave = False
        pps = p.ps

        if not inPlace:
            newPitch = copy.deepcopy(p)
        else:
            newPitch = p

        newPitch.ps = pps + self.semitones
        if useImplicitOctave is True:
            newPitch.octave = None

        if not inPlace:
            return newPitch


# ------------------------------------------------------------------------------
def _stringToDiatonicChromatic(
    value: str
) -> t.Tuple[DiatonicInterval, ChromaticInterval, bool]:
    '''
    A function for processing interval strings and returning
    diatonic and chromatic interval objects. Used by the Interval class, below.
    The last entry is a boolean indicating whether the diatonic interval is
    inferred (see 'half' and 'whole')

    >>> interval._stringToDiatonicChromatic('P5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>, False)
    >>> interval._stringToDiatonicChromatic('p5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>, False)
    >>> interval._stringToDiatonicChromatic('perfect5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>, False)
    >>> interval._stringToDiatonicChromatic('perfect fifth')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval 7>, False)

    >>> interval._stringToDiatonicChromatic('P-5')
    (<music21.interval.DiatonicInterval P5>, <music21.interval.ChromaticInterval -7>, False)
    >>> interval._stringToDiatonicChromatic('M3')
    (<music21.interval.DiatonicInterval M3>, <music21.interval.ChromaticInterval 4>, False)
    >>> interval._stringToDiatonicChromatic('m3')
    (<music21.interval.DiatonicInterval m3>, <music21.interval.ChromaticInterval 3>, False)

    >>> interval._stringToDiatonicChromatic('whole')
    (<music21.interval.DiatonicInterval M2>, <music21.interval.ChromaticInterval 2>, True)
    >>> interval._stringToDiatonicChromatic('half')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval 1>, True)
    >>> interval._stringToDiatonicChromatic('-h')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval -1>, True)

    >>> interval._stringToDiatonicChromatic('semitone')
    (<music21.interval.DiatonicInterval m2>, <music21.interval.ChromaticInterval 1>, True)
    '''
    # find direction
    inferred = False
    if '-' in value:
        value = value.replace('-', '')  # remove
        dirScale = -1
    else:
        dirScale = 1

    if 'descending' in value.lower():
        value = re.sub(r'descending\s*', '', value, flags=re.RegexFlag.IGNORECASE)
        dirScale = -1
    elif 'ascending' in value.lower():
        value = re.sub(r'ascending\\s*', '', value, flags=re.RegexFlag.IGNORECASE)

    # permit whole and half abbreviations
    if value.lower() in ('w', 'whole', 'tone'):
        value = 'M2'
        inferred = True
    elif value.lower() in ('h', 'half', 'semitone'):
        value = 'm2'
        inferred = True

    for i, ordinal in enumerate(common.musicOrdinals):
        if ordinal.lower() in value.lower():
            value = re.sub(fr'\s*{ordinal}\s*',
                           str(i),
                           value,
                           flags=re.RegexFlag.IGNORECASE
                           )

    # apply dir shift value here
    found, remain = common.getNumFromStr(value)
    try:
        genericNumber = int(found) * dirScale
    except ValueError as ve:
        raise IntervalException(
            f'Could not find an int in {found!r}, from {value!r}.'
        ) from ve
    # generic = int(value.lstrip('PMmAd')) * dirShift  # this will be a number
    specName = remain  # value.rstrip('-0123456789')

    gInterval = GenericInterval(genericNumber)
    dInterval = gInterval.getDiatonic(specName)
    return dInterval, dInterval.getChromatic(), inferred


def notesToGeneric(
    n1: t.Union['music21.pitch.Pitch', 'music21.note.Note'],
    n2: t.Union['music21.pitch.Pitch', 'music21.note.Note']
) -> GenericInterval:
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
    (p1, p2) = (_extractPitch(n1), _extractPitch(n2))

    staffDist = p2.diatonicNoteNum - p1.diatonicNoteNum
    genDist = convertStaffDistanceToInterval(staffDist)
    return GenericInterval(genDist)

def notesToChromatic(
    n1: t.Union['music21.pitch.Pitch', 'music21.note.Note'],
    n2: t.Union['music21.pitch.Pitch', 'music21.note.Note']
) -> ChromaticInterval:
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
    (p1, p2) = (_extractPitch(n1), _extractPitch(n2))
    return ChromaticInterval(p2.ps - p1.ps)


def _getSpecifierFromGenericChromatic(
    gInt: GenericInterval,
    cInt: ChromaticInterval
) -> Specifier:
    '''
    Given a :class:`~music21.interval.GenericInterval` and
    a :class:`~music21.interval.ChromaticInterval` object, return a specifier
    (i.e. Specifier.MAJOR, Specifier.MINOR, etc...).

    >>> aInterval = interval.GenericInterval('seventh')
    >>> bInterval = interval.ChromaticInterval(11)
    >>> interval._getSpecifierFromGenericChromatic(aInterval, bInterval)
    <Specifier.MAJOR>
    >>> interval.parseSpecifier('major')
    <Specifier.MAJOR>

    Absurdly altered interval:

    >>> cInterval = interval.GenericInterval('second')
    >>> dInterval = interval.ChromaticInterval(10)  # 8x augmented second
    >>> interval._getSpecifierFromGenericChromatic(cInterval, dInterval)
    Traceback (most recent call last):
    music21.interval.IntervalException: cannot get a specifier for a note with
        this many semitones off of Major: 8
    '''
    noteVals = (0, 2, 4, 5, 7, 9, 11)
    normalSemis = noteVals[gInt.simpleUndirected - 1] + 12 * gInt.undirectedOctaves

    if (gInt.direction != cInt.direction
            and gInt.direction != Direction.OBLIQUE and cInt.direction != Direction.OBLIQUE):
        # intervals like d2 and dd2 etc.
        # (the last test doesn't matter, since -1*0 == 0, but in theory it should be there)
        theseSemis = -1 * cInt.undirected
    elif gInt.undirected == 1:
        theseSemis = cInt.directed  # matters for unison
    else:
        # all normal intervals
        theseSemis = cInt.undirected
    # round out microtones
    # fix python3 rounding...
    if cInt.undirected > 0:
        roundingError = 0.0001
    else:
        roundingError = -0.0001

    semisRounded = int(round(theseSemis + roundingError))  # python3 rounding
    if gInt.perfectable:
        try:
            specifier = perfSpecifiers[perfOffset + semisRounded - normalSemis]
        except IndexError as ie:
            raise IntervalException(
                'cannot get a specifier for a note with this many semitones '
                + 'off of Perfect: ' + str(theseSemis - normalSemis)
            ) from ie
    else:
        try:
            specifier = specifiers[majOffset + semisRounded - normalSemis]
        except IndexError as ie:
            raise IntervalException(
                'cannot get a specifier for a note with this many semitones '
                + 'off of Major: ' + str(theseSemis - normalSemis)
            ) from ie

    return specifier


def intervalsToDiatonic(
    gInt: GenericInterval,
    cInt: ChromaticInterval
) -> DiatonicInterval:
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


def intervalFromGenericAndChromatic(
    gInt: t.Union[GenericInterval, int],
    cInt: t.Union[ChromaticInterval, int, float],
) -> Interval:
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
    gIntV: GenericInterval
    if not isinstance(gInt, GenericInterval):
        gIntV = GenericInterval(gInt)
    else:
        gIntV = gInt

    if not isinstance(cInt, ChromaticInterval):
        cIntV = ChromaticInterval(cInt)
    else:
        cIntV = cInt

    specifier = _getSpecifierFromGenericChromatic(gIntV, cIntV)
    dInt = DiatonicInterval(specifier, gIntV)
    return Interval(diatonic=dInt, chromatic=cIntV)


# ------------------------------------------------------------------------------

# store implicit diatonic if set from chromatic specification
# if implicit, turing transpose, set to simplifyEnharmonic


class Interval(IntervalBase):
    '''
    An Interval class that encapsulates both
    :class:`~music21.interval.ChromaticInterval` and
    :class:`~music21.interval.DiatonicInterval` objects all in one model.

    The interval is specified either as named arguments, a
    :class:`~music21.interval.DiatonicInterval` and
    a :class:`~music21.interval.ChromaticInterval`,
    or two :class:`~music21.note.Note` objects
    (or :class:`~music21.interval.Pitch` objects),
    from which both a ChromaticInterval and DiatonicInterval are derived.

    >>> p1 = pitch.Pitch('c3')
    >>> p2 = pitch.Pitch('c5')
    >>> aInterval = interval.Interval(pitchStart=p1, pitchEnd=p2)
    >>> aInterval
    <music21.interval.Interval P15>
    >>> aInterval.name
    'P15'
    >>> aInterval.pitchStart is p1
    True
    >>> aInterval.pitchEnd is p2
    True

    Reduce to less than an octave:

    >>> aInterval.simpleName
    'P1'

    Reduce to no more than an octave:

    >>> aInterval.semiSimpleName
    'P8'

    An interval can also be specified directly:

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

    Some ways of creating half-steps.

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

    If giving a starting pitch, an ending pitch has to be specified.

    >>> aInterval = interval.Interval(pitchStart=p1)
    Traceback (most recent call last):
    ValueError: either both the starting and the ending pitch (or note) must be given
        or neither can be given. You cannot have one without the other.

    An Interval can be constructed from a DiatonicInterval and ChromaticInterval
    object (or just one):

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
    are the same.

    >>> aInt = interval.Interval('P4')
    >>> bInt = interval.Interval(
    ...        diatonic=interval.DiatonicInterval('P', 4),
    ...        chromatic=interval.ChromaticInterval(5),
    ...        )
    >>> aInt == bInt
    True

    N.B. that interval.Interval('A4') != 'A4'

    >>> interval.Interval('A4') == 'A4'
    False

    More demonstrations using pitches:

    >>> aPitch = pitch.Pitch('c4')
    >>> bPitch = pitch.Pitch('g5')
    >>> aInterval = interval.Interval(aPitch, bPitch)
    >>> aInterval
    <music21.interval.Interval P12>
    >>> bInterval = interval.Interval(pitchStart=aPitch, pitchEnd=bPitch)
    >>> aInterval.niceName == bInterval.niceName
    True

    >>> aPitch = pitch.Pitch('c#4')
    >>> bPitch = pitch.Pitch('f-5')
    >>> cInterval = interval.Interval(aPitch, bPitch)
    >>> cInterval
    <music21.interval.Interval dd11>

    >>> cPitch = pitch.Pitch('e#4')
    >>> dPitch = pitch.Pitch('f-4')
    >>> dInterval = interval.Interval(cPitch, dPitch)
    >>> dInterval
    <music21.interval.Interval dd2>

    >>> ePitch = pitch.Pitch('e##4')
    >>> fPitch = pitch.Pitch('f--4')
    >>> dInterval = interval.Interval(ePitch, fPitch)
    >>> dInterval
    <music21.interval.Interval dddd2>

    >>> gPitch = pitch.Pitch('c--4')
    >>> hPitch = pitch.Pitch('c##4')
    >>> iInterval = interval.Interval(gPitch, hPitch)
    >>> iInterval
    <music21.interval.Interval AAAA1>

    >>> interval.Interval(pitch.Pitch('e##4'), pitch.Pitch('f--5'))
    <music21.interval.Interval dddd9>

    Changed in v8:

    * Pitches are emphasized over notes.

    * It is not possible to create an interval with a name and a pitchStart/noteStart
      and automatically get a pitchEnd/noteEnd in the process.  Set them later.

    * Incompatible keywords raise ValueError not IntervalException.

    * An empty instantiation gives a P1 interval.

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

    This is in OMIT... put changelog above.
    '''
    def __init__(self,
                 arg0: t.Union[str,
                               int,
                               float,
                               'music21.pitch.Pitch',
                               'music21.note.Note',
                               None] = None,
                 arg1: t.Union['music21.pitch.Pitch', 'music21.note.Note', None] = None,
                 /,
                 *,
                 diatonic: t.Optional[DiatonicInterval] = None,
                 chromatic: t.Optional[ChromaticInterval] = None,
                 pitchStart: t.Optional['music21.pitch.Pitch'] = None,
                 pitchEnd: t.Optional['music21.pitch.Pitch'] = None,
                 noteStart: t.Union['music21.note.Note', 'music21.pitch.Pitch', None] = None,
                 noteEnd: t.Union['music21.note.Note', 'music21.pitch.Pitch', None] = None,
                 name: t.Optional[str] = None,
                 **keywords):
        super().__init__(**keywords)

        # is this basically a ChromaticInterval object in disguise?
        self.implicitDiatonic: bool = False

        if arg1 is not None:
            if arg0 is None:
                raise ValueError('Cannot supply a second value without a first.')
            pitchEnd = _extractPitch(arg1)
        if arg0 is not None:
            # was bitten on "if arg0:" but interval.Interval(0) is important.
            if isinstance(arg0, str):
                name = arg0
            elif isinstance(arg0, (int, float)):
                chromatic = ChromaticInterval(arg0)
            else:
                pitchStart = _extractPitch(arg0)

        if ((noteStart and pitchStart)
                or (noteEnd and pitchEnd)):
            raise ValueError('Cannot instantiate an interval with both notes and pitches.')

        if noteStart:
            pitchStart = _extractPitch(noteStart)
        if noteEnd:
            pitchEnd = _extractPitch(noteEnd)

        if (pitchStart and not pitchEnd) or (pitchEnd and not pitchStart):
            raise ValueError(
                'either both the starting and the ending pitch (or note) must be '
                + 'given or neither can be given.  You cannot have one without the other.'
            )
        if pitchStart and pitchEnd:  # second check unnecessary except for typing
            genericInterval = notesToGeneric(pitchStart, pitchEnd)
            chromaticNew = notesToChromatic(pitchStart, pitchEnd)
            diatonicNew = intervalsToDiatonic(genericInterval, chromaticNew)
            if (chromatic or diatonic) and chromatic != chromaticNew:
                # it is okay for no diatonic match. Notes will pick this up.
                raise ValueError(
                    'Do not pass in pitches/notes and diatonic/chromatic '
                    + 'interval objects, unless they represent the same interval.'
                )
            chromatic = chromaticNew
            diatonic = diatonicNew

        if name:
            diatonicNew, chromaticNew, inferred = _stringToDiatonicChromatic(name)
            if (chromatic or diatonic) and (chromatic != chromaticNew or diatonic != diatonicNew):
                raise ValueError(
                    'Do not pass in a name and pitches/notes or diatonic/chromatic '
                    + 'interval objects, unless they represent the same interval.'
                )
            chromatic = chromaticNew
            diatonic = diatonicNew
            self.implicitDiatonic = inferred
        elif chromatic and not diatonic:
            diatonic = chromatic.getDiatonic()
            self.implicitDiatonic = True
        elif diatonic and not chromatic:
            chromatic = diatonic.getChromatic()
        elif not diatonic and not chromatic:
            diatonic = DiatonicInterval('P', 1)
            chromatic = ChromaticInterval(0)

        # both self.diatonic and self.chromatic can still both be None if an
        # empty Interval class is being created, such as in deepcopy
        if t.TYPE_CHECKING:
            assert diatonic is not None
            assert chromatic is not None

        self.diatonic: DiatonicInterval = diatonic
        self.chromatic: ChromaticInterval = chromatic

        # these can be accessed through pitchStart and pitchEnd properties
        self._pitchStart: t.Optional['music21.pitch.Pitch'] = pitchStart
        self._pitchEnd: t.Optional['music21.pitch.Pitch'] = pitchEnd

        self.intervalType: t.Literal['harmonic', 'melodic', ''] = ''

    def _reprInternal(self):
        from music21 import pitch
        try:
            shift = self._diatonicIntervalCentShift()
        except AttributeError:
            return ''

        if shift != 0:
            micro = pitch.Microtone(shift)
            return self.directedName + ' ' + str(micro)
        else:
            return self.directedName

    # -------------------------------------
    # special method
    def __eq__(self, other):
        '''
        True if .diatonic and .chromatic are equal.

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


    # -------------------------------------
    # properties

    @property
    def generic(self) -> GenericInterval:
        '''
        Returns the :class:`~music21.interval.GenericInterval` object
        associated with this Interval

        >>> interval.Interval('P5').generic
        <music21.interval.GenericInterval 5>
        '''
        return self.diatonic.generic

    @property
    def name(self) -> str:
        '''
        Return the simple name of the interval, ignoring direction:

        >>> interval.Interval('Descending Perfect Fourth').name
        'P4'
        '''
        return self.diatonic.name

    @property
    def niceName(self) -> str:
        '''
        >>> interval.Interval('m3').niceName
        'Minor Third'
        '''
        return self.diatonic.niceName

    @property
    def simpleName(self) -> str:
        return self.diatonic.simpleName

    @property
    def simpleNiceName(self) -> str:
        return self.diatonic.simpleNiceName

    @property
    def semiSimpleName(self) -> str:
        return self.diatonic.semiSimpleName

    @property
    def semiSimpleNiceName(self) -> str:
        return self.diatonic.semiSimpleNiceName

    @property
    def directedName(self) -> str:
        return self.diatonic.directedName

    @property
    def directedNiceName(self) -> str:
        return self.diatonic.directedNiceName

    @property
    def directedSimpleName(self) -> str:
        return self.diatonic.directedSimpleName

    @property
    def directedSimpleNiceName(self) -> str:
        return self.diatonic.directedSimpleNiceName

    @property
    def semitones(self) -> t.Union[int, float]:
        return self.chromatic.semitones

    @property
    def direction(self) -> t.Optional[Direction]:
        return self.chromatic.direction

    @property
    def specifier(self) -> t.Optional[Specifier]:
        return self.diatonic.specifier

    @property
    def specificName(self) -> str:
        return self.diatonic.specificName

    @property
    def isDiatonicStep(self) -> bool:
        return self.diatonic.isDiatonicStep

    @property
    def isChromaticStep(self) -> bool:
        return self.chromatic.isChromaticStep

    @property
    def isStep(self) -> bool:
        return self.isChromaticStep or self.isDiatonicStep

    @property
    def isSkip(self) -> bool:
        return self.diatonic.isSkip

    # -------------------------------------
    # methods
    def isConsonant(self) -> bool:
        '''
        returns True if the pitches are a major or
        minor third or sixth or perfect fifth or unison.

        These rules define all common-practice consonances
        (and earlier back to about 1300 all imperfect consonances)

        >>> i1 = interval.Interval(note.Note('C'), note.Note('E'))
        >>> i1.isConsonant()
        True
        >>> i1 = interval.Interval(note.Note('B-'), note.Note('C'))
        >>> i1.isConsonant()
        False
        '''
        if self.simpleName in ('P5', 'm3', 'M3', 'm6', 'M6', 'P1'):
            return True
        else:
            return False

    @property
    def complement(self) -> Interval:
        '''
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
        '''
        return Interval(self.diatonic.mod7inversion)

    @property
    def intervalClass(self) -> int:
        '''
        Return the interval class from the chromatic interval,
        that is, the lesser of the number of half-steps in the
        simpleInterval or its complement.

        >>> aInterval = interval.Interval('M3')
        >>> aInterval.intervalClass
        4

        >>> bInterval = interval.Interval('m6')
        >>> bInterval.intervalClass
        4

        Empty intervals return 0:

        >>> interval.Interval().intervalClass
        0

        Changed in v6.5 -- empty intervals return 0
        '''
        return self.chromatic.intervalClass

    @property
    def cents(self) -> float:
        '''
        Return the cents from the chromatic interval, where 100 cents = a half-step

        >>> aInterval = interval.Interval('M3')
        >>> aInterval.cents
        400.0

        >>> p1 = pitch.Pitch('C4')
        >>> p2 = pitch.Pitch('D4')
        >>> p2.microtone = 30
        >>> microtoneInterval = interval.Interval(pitchStart=p1, pitchEnd=p2)
        >>> microtoneInterval.cents
        230.0

        OMIT_FROM_DOCS

        >>> interval.Interval().cents
        0.0
        '''
        return self.chromatic.cents

    def _diatonicIntervalCentShift(self) -> float:
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
                       p: 'music21.pitch.Pitch',
                       *,
                       reverse=False,
                       maxAccidental: t.Optional[int] = 4,
                       inPlace=False):
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

        If inPlace is True then function is done in place and no pitch is returned.

        >>> p1 = pitch.Pitch('A4')
        >>> i = interval.Interval('m3')
        >>> i.transposePitch(p1, inPlace=True)
        >>> p1
        <music21.pitch.Pitch C5>

        Note that reverse=True is only there for historical reasons;
        it is the same as `i.reverse().transposePitch(x)` and that format
        will be much faster when calling many times.

        Changed in v.6 -- inPlace parameter added.  Reverse and maxAccidental
        changed to keyword only.

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
        if reverse:
            return self.reverse().transposePitch(p, maxAccidental=maxAccidental, inPlace=inPlace)

        if maxAccidental is None:
            maxAccidental = 99999

        if self.implicitDiatonic:
            # this will not preserve diatonic relationships
            pOut = self.chromatic.transposePitch(
                p,
                inPlace=inPlace,
            )
        else:
            pOut = self._diatonicTransposePitch(
                p,
                maxAccidental=maxAccidental,
                inPlace=inPlace
            )

        if p.fundamental is not None:
            # recursively call method
            pOut.fundamental = self.transposePitch(
                p.fundamental,
                maxAccidental=maxAccidental,
            )

            if p.fundamental.octave is None:
                pOut.fundamental.octave = None

        if not inPlace:
            return pOut

    def _diatonicTransposePitch(self,
                                p: 'music21.pitch.Pitch',
                                *,
                                maxAccidental: int,
                                inPlace: bool = False):
        '''
        abstracts out the diatonic aspects of transposing, so that implicitDiatonic and
        regular diatonic can use some of the same code.

        PRIVATE METHOD: Return p even if inPlace is True
        '''
        # NOTE: this is a performance critical method
        if p.octave is None:
            useImplicitOctave = True
        else:
            useImplicitOctave = False

        pitch1 = p
        pitch2 = copy.deepcopy(pitch1)
        oldDiatonicNum = pitch1.diatonicNoteNum
        # centsOrigin = pitch1.microtone.cents  # unused!!
        distanceToMove = self.diatonic.generic.staffDistance

        newDiatonicNumber = oldDiatonicNum + distanceToMove

        newStep, newOctave = convertDiatonicNumberToStep(newDiatonicNumber)
        pitch2.step = newStep
        pitch2.octave = newOctave
        pitch2.accidental = None
        # if this is not set to None then terrible things happen
        pitch2.microtone = None  # type: ignore

        # We have the right note name but not the right accidental
        interval2 = Interval(pitch1, pitch2)
        # halfStepsToFix already has any microtones
        halfStepsToFix = self.chromatic.semitones - interval2.chromatic.semitones

        # environLocal.printDebug(['self', self, 'halfStepsToFix', halfStepsToFix,
        #    'centsOrigin', centsOrigin, 'interval2', interval2])

        if halfStepsToFix != 0:
            while halfStepsToFix >= 12:  # small loop. faster than calculating.
                halfStepsToFix = halfStepsToFix - 12
                pitch2.octave = pitch2.octave - 1

            # this will raise an exception if greater than 4
            if abs(halfStepsToFix) > maxAccidental:
                # just create new pitch, directly setting the pitch space value
                # pitchAlt = copy.deepcopy(pitch2)
                # pitchAlt.ps = pitch2.ps + halfStepsToFix
                # environLocal.printDebug(
                #    'coercing pitch due to a transposition that requires an extreme ' +
                #    'accidental: %s -> %s' % (pitch2, pitchAlt) )
                # pitch2 = pitchAlt
                pitch2.ps = pitch2.ps + halfStepsToFix
            else:
                # cannot import Accidental here.
                pitch2.accidental = halfStepsToFix  # type:ignore

            # inherit accidental display type etc. but not current status
            if pitch2.accidental is not None and pitch1.accidental is not None:
                pitch2.accidental.inheritDisplay(pitch1.accidental)
                pitch2.accidental.displayStatus = None  # set accidental display to None

        if useImplicitOctave is True:
            pitch2.octave = None

        if not inPlace:
            return pitch2
        else:
            pitch1.name = pitch2.name
            pitch1.octave = pitch2.octave
            return pitch1  # do not return on inPlace for public methods

    def reverse(self):
        '''
        Return an reversed version of this interval.
        If :class:`~music21.pitch.Pitch` objects are stored as
        `pitchStart` and `pitchEnd`, these pitches are reversed.

        >>> p1 = pitch.Pitch('c3')
        >>> p2 = pitch.Pitch('g3')
        >>> intvP5 = interval.Interval(pitchStart=p1, pitchEnd=p2)
        >>> intvP5
        <music21.interval.Interval P5>
        >>> revInterval = intvP5.reverse()
        >>> revInterval
        <music21.interval.Interval P-5>
        >>> revInterval.pitchStart is intvP5.pitchEnd
        True

        >>> m3 = interval.Interval('m3')
        >>> m3.reverse()
        <music21.interval.Interval m-3>
        '''
        if self._pitchStart is not None and self._pitchEnd is not None:
            return Interval(noteStart=self._pitchEnd, noteEnd=self._pitchStart)
        else:
            return Interval(diatonic=self.diatonic.reverse(),
                            chromatic=self.chromatic.reverse())

    @property
    def pitchStart(self):
        '''
        Get the start pitch or set it a new value.
        Setting this will adjust the value of the end pitch (`pitchEnd`).

        >>> maj3 = interval.Interval('M3')
        >>> maj3.pitchStart = pitch.Pitch('c4')
        >>> maj3.pitchEnd.nameWithOctave
        'E4'

        >>> p1 = pitch.Pitch('c3')
        >>> p2 = pitch.Pitch('g#3')
        >>> a5 = interval.Interval(p1, p2)
        >>> a5.name
        'A5'

        >>> a5.pitchStart = pitch.Pitch('g4')
        >>> a5.pitchEnd.nameWithOctave
        'D#5'

        >>> descM3 = interval.Interval('-M3')
        >>> descM3.pitchStart = pitch.Pitch('c4')
        >>> descM3.pitchEnd.nameWithOctave
        'A-3'

        >>> descM2 = interval.Interval('M-2')
        >>> descM2.pitchStart = pitch.Pitch('A#3')
        >>> descM2.pitchEnd.nameWithOctave
        'G#3'

        Implicit diatonic intervals do not need to
        follow the diatonic directed name:

        >>> halfStep = interval.Interval('h')
        >>> halfStep.directedName
        'm2'
        >>> halfStep.implicitDiatonic
        True
        >>> halfStep.pitchStart = pitch.Pitch('F-3')
        >>> halfStep.pitchEnd.nameWithOctave
        'F3'
        '''
        return self._pitchStart

    @pitchStart.setter
    def pitchStart(self, p: 'music21.pitch.Pitch'):
        '''
        Assuming that this interval is defined,
        we can set a new start Pitch (_pitchStart) and
        automatically set the end Pitch (_pitchEnd).
        '''
        # this is based on the procedure found in transposePitch() and
        # transposeNote() but offers a more object-oriented approach
        pitch2 = self.transposePitch(p)
        self._pitchStart = p
        # prefer to copy the existing noteEnd if it exists, or noteStart if not
        self._pitchEnd = pitch2

    @property
    def pitchEnd(self):
        '''
        Set the
        end pitch to a new value; this will adjust
        the value of the start pitch (`pitchStart`).

        >>> aInterval = interval.Interval('M3')
        >>> aInterval.pitchEnd = pitch.Pitch('E4')
        >>> aInterval.pitchStart.nameWithOctave
        'C4'

        >>> aInterval = interval.Interval('m2')
        >>> aInterval.pitchEnd = pitch.Pitch('A#3')
        >>> aInterval.pitchStart.nameWithOctave
        'G##3'

        >>> p1 = pitch.Pitch('G#3')
        >>> p2 = pitch.Pitch('C3')
        >>> aInterval = interval.Interval(p1, p2)
        >>> aInterval.directedName  # downward augmented fifth
        'A-5'
        >>> aInterval.pitchEnd = pitch.Pitch('C4')
        >>> aInterval.pitchStart.nameWithOctave
        'G#4'

        >>> aInterval = interval.Interval('M3')
        >>> aInterval.pitchEnd = pitch.Pitch('A-3')
        >>> aInterval.pitchStart.nameWithOctave
        'F-3'
        '''
        return self._pitchEnd

    @pitchEnd.setter
    def pitchEnd(self, p: music21.pitch.Pitch):
        '''
        Assuming that this interval is defined, we can
        set a new end note (_pitchEnd) and automatically have the start pitch (_pitchStart).
        '''
        # this is based on the procedure found in transposePitch() but offers
        # a more object-oriented approach
        pitch1 = self.transposePitch(p, reverse=True)

        self._pitchEnd = p
        self._pitchStart = pitch1

    @property
    def noteStart(self) -> t.Optional[music21.note.Note]:
        '''
        Return or set the Note that pitchStart is attached to.  For
        backwards compatibility
        '''
        p = self.pitchStart
        if p and p._client:
            return p._client
        elif p:
            from music21 import note
            return note.Note(pitch=p)

    @noteStart.setter
    def noteStart(self, n: t.Optional[music21.note.Note]):
        if n:
            self.pitchStart = n.pitch
        else:
            self.pitchStart = None

    @property
    def noteEnd(self) -> t.Optional[music21.note.Note]:
        '''
        Return or set the Note that pitchEnd is attached to.  For
        backwards compatibility
        '''
        p = self.pitchEnd
        if p and p._client:
            return p._client
        elif p:
            from music21 import note
            return note.Note(pitch=p)

    @noteEnd.setter
    def noteEnd(self, n: t.Optional[music21.note.Note]):
        if n:
            self.pitchEnd = n.pitch
        else:
            self.pitchEnd = None


# ------------------------------------------------------------------------------
def getWrittenHigherNote(note1: t.Union['music21.note.Note', 'music21.pitch.Pitch'],
                         note2: t.Union['music21.note.Note', 'music21.pitch.Pitch']
                         ) -> t.Union['music21.note.Note', 'music21.pitch.Pitch']:
    '''
    Given two :class:`~music21.pitch.Pitch` or :class:`~music21.note.Note` objects,
    this function returns the higher element based on diatonic note
    numbers. If the diatonic numbers are
    the same, returns the sounding higher element,
    or the first element if that is also the same.

    >>> cis = pitch.Pitch('C#')
    >>> deses = pitch.Pitch('D--')
    >>> higher = interval.getWrittenHigherNote(cis, deses)
    >>> higher is deses
    True

    >>> aPitch = pitch.Pitch('c#3')
    >>> bPitch = pitch.Pitch('d-3')
    >>> interval.getWrittenHigherNote(aPitch, bPitch)
    <music21.pitch.Pitch D-3>

    >>> aNote = note.Note('c#3')
    >>> bNote = note.Note('c3')
    >>> interval.getWrittenHigherNote(aNote, bNote) is aNote
    True
    '''
    (p1, p2) = (_extractPitch(note1), _extractPitch(note2))

    num1 = p1.diatonicNoteNum
    num2 = p2.diatonicNoteNum
    if num1 > num2:
        return note1
    elif num1 < num2:
        return note2
    else:
        return getAbsoluteHigherNote(note1, note2)


def getAbsoluteHigherNote(note1: t.Union['music21.note.Note', 'music21.pitch.Pitch'],
                          note2: t.Union['music21.note.Note', 'music21.pitch.Pitch']
                          ) -> t.Union['music21.note.Note', 'music21.pitch.Pitch']:
    '''
    Given two :class:`~music21.pitch.Pitch` or :class:`~music21.note.Note` objects,
    returns the higher element based on sounding pitch.
    If both sounding pitches are the same, returns the first element given.

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


def getWrittenLowerNote(note1: t.Union['music21.note.Note', 'music21.pitch.Pitch'],
                        note2: t.Union['music21.note.Note', 'music21.pitch.Pitch']
                        ) -> t.Union['music21.note.Note', 'music21.pitch.Pitch']:
    '''
    Given two :class:`~music21.pitch.Pitch` or :class:`~music21.note.Note` objects,
    returns the lower element based on diatonic note
    number. If the diatonic number is
    the same returns the sounding lower element,
    or the first element if sounding pitch is also the same.

    >>> aNote = pitch.Pitch('c#3')
    >>> bNote = pitch.Pitch('d--3')
    >>> interval.getWrittenLowerNote(aNote, bNote)
    <music21.pitch.Pitch C#3>

    >>> aNote = pitch.Pitch('c#3')
    >>> bNote = pitch.Pitch('d-3')
    >>> interval.getWrittenLowerNote(aNote, bNote)
    <music21.pitch.Pitch C#3>
    '''
    (p1, p2) = (_extractPitch(note1), _extractPitch(note2))

    num1 = p1.diatonicNoteNum
    num2 = p2.diatonicNoteNum
    if num1 < num2:
        return note1
    elif num1 > num2:
        return note2
    else:
        return getAbsoluteLowerNote(note1, note2)


def getAbsoluteLowerNote(note1: t.Union['music21.note.Note', 'music21.pitch.Pitch'],
                         note2: t.Union['music21.note.Note', 'music21.pitch.Pitch']
                         ) -> t.Union['music21.note.Note', 'music21.pitch.Pitch']:
    '''
    Given two :class:`~music21.note.Note` or :class:`~music21.pitch.Pitch` objects, returns
    the lower element based on actual pitch.
    If both pitches are the same, returns the first element given.

    >>> aNote = pitch.Pitch('c#3')
    >>> bNote = pitch.Pitch('d--3')
    >>> interval.getAbsoluteLowerNote(aNote, bNote)
    <music21.pitch.Pitch D--3>
    '''
    chromatic = notesToChromatic(note1, note2)
    semitones = chromatic.semitones
    if semitones > 0:
        return note1
    elif semitones < 0:
        return note2
    else:
        return note1


def transposePitch(
    pitch1: 'music21.pitch.Pitch',
    interval1: t.Union[str, Interval],
    *,
    inPlace=False
) -> 'music21.pitch.Pitch':
    '''
    DEPRECATED: call `p.transpose(interval1)` directly

    Given a :class:`~music21.pitch.Pitch`
    and a :class:`~music21.interval.Interval` object (Not another class such
    as ChromaticInterval) or a string such as 'P5' or a number such as 6 (=tritone),
    return a new Pitch object at the appropriate pitch level.

    >>> aPitch = pitch.Pitch('C4')
    >>> P5 = interval.Interval('P5')
    >>> bPitch = interval.transposePitch(aPitch, P5)
    >>> bPitch
    <music21.pitch.Pitch G4>
    >>> bInterval = interval.Interval('P-5')
    >>> cPitch = interval.transposePitch(aPitch, bInterval)
    >>> cPitch
    <music21.pitch.Pitch F3>

    Pitches with implicit octaves should work,

    >>> dPitch = pitch.Pitch('G')
    >>> ePitch = interval.transposePitch(dPitch, P5)
    >>> ePitch
    <music21.pitch.Pitch D>

    Can be done inPlace as well

    >>> C4 = pitch.Pitch('C4')
    >>> interval.transposePitch(C4, P5, inPlace=True)
    >>> C4
    <music21.pitch.Pitch G4>

    Changed in v.6 -- added inPlace parameter
    '''

    # check if interval1 is a string,
    # then convert it to interval object if necessary
    if isinstance(interval1, (str, int)):
        interval1 = Interval(interval1)
    else:
        if not hasattr(interval1, 'transposePitch'):
            raise IntervalException(
                'interval must be a music21.interval.Interval object not {}'.format(
                    interval1.__class__.__name__))
    return interval1.transposePitch(pitch1, inPlace=inPlace)


def transposeNote(
        note1: 'music21.note.Note',
        intervalString: t.Union[str, Interval]) -> 'music21.note.Note':
    '''
    To be deprecated: call `n.transpose(intervalString)` directly.

    Given a :class:`~music21.note.Note` and
    an interval string (such as 'P5') or an Interval object,
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
    if not isinstance(intervalString, Interval):
        intv = Interval(intervalString)
    else:
        intv = intervalString

    newPitch = intv.transposePitch(note1.pitch)
    newNote = copy.deepcopy(note1)
    newNote.pitch = newPitch
    return newNote


def notesToInterval(n1, n2) -> Interval:
    '''
    Soon to be DEPRECATED: Call Interval Directly

    Given two :class:`~music21.note.Note` objects, returns an
    :class:`~music21.interval.Interval` object. The same
    functionality is available by calling the Interval class
    with two Notes as arguments.

    >>> aNote = note.Note('c4')
    >>> bNote = note.Note('g5')
    >>> aInterval = interval.notesToInterval(aNote, bNote)
    >>> aInterval
    <music21.interval.Interval P12>
    '''
    return Interval(noteStart=n1, noteEnd=n2)


def add(intervalList):
    '''
    Add a list of intervals and return the composite interval
    Intervals can be Interval objects or just strings.

    (Currently not particularly efficient for large lists...)

    >>> A2 = interval.Interval('A2')
    >>> P5 = interval.Interval('P5')

    >>> interval.add([A2, P5])
    <music21.interval.Interval A6>
    >>> interval.add([P5, 'm2'])
    <music21.interval.Interval m6>
    >>> interval.add(['W', 'W', 'H', 'W', 'W', 'W', 'H'])
    <music21.interval.Interval P8>

    Direction does matter:

    >>> interval.add([P5, 'P-4'])
    <music21.interval.Interval M2>
    '''
    from music21 import pitch
    if not intervalList:
        raise IntervalException('Cannot add an empty set of intervals')

    p1 = pitch.Pitch('C4')  # need octave to not be implicit...
    p2 = pitch.Pitch('C4')
    for i in intervalList:
        p2 = transposePitch(p2, i)
    return Interval(noteStart=p1, noteEnd=p2)


def subtract(intervalList):
    '''
    Starts with the first interval and subtracts the
    following intervals from it:

    >>> interval.subtract(['P5', 'M3'])
    <music21.interval.Interval m3>
    >>> interval.subtract(['P4', 'd3'])
    <music21.interval.Interval A2>

    >>> m2Object = interval.Interval('m2')
    >>> interval.subtract(['M6', 'm2', m2Object])
    <music21.interval.Interval AA4>
    >>> interval.subtract(['P4', 'M-2'])
    <music21.interval.Interval P5>
    >>> interval.subtract(['A2', 'A2'])
    <music21.interval.Interval P1>
    >>> interval.subtract(['A1', 'P1'])
    <music21.interval.Interval A1>

    >>> interval.subtract(['P8', 'P1'])
    <music21.interval.Interval P8>
    >>> interval.subtract(['P8', 'd2'])
    <music21.interval.Interval A7>
    >>> interval.subtract(['P8', 'A1'])
    <music21.interval.Interval d8>


    >>> a = interval.subtract(['P5', 'A5'])
    >>> a.niceName
    'Diminished Unison'
    >>> a.directedNiceName
    'Descending Diminished Unison'
    >>> a.chromatic.semitones
    -1

    '''
    from music21 import pitch
    if not intervalList:
        raise IntervalException('Cannot add an empty set of intervals')

    n1 = pitch.Pitch('C4')
    n2 = pitch.Pitch('C4')
    for i, intI in enumerate(intervalList):
        if i == 0:
            n2 = transposePitch(n2, intI)
        else:
            if not hasattr(intI, 'chromatic'):
                intervalObj = Interval(intI)
            else:
                intervalObj = intI
            n2 = transposePitch(n2, intervalObj.reverse())
    # print(n1.nameWithOctave, n2.nameWithOctave)
    return Interval(noteStart=n1, noteEnd=n2)

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testConstructorPitches(self):
        from music21 import interval
        from music21 import pitch
        p1 = pitch.Pitch('A4')
        p2 = pitch.Pitch('E5')
        intv = interval.Interval(p1, p2)
        self.assertEqual(intv.name, 'P5')
        self.assertIs(intv.pitchStart, p1)
        self.assertIs(intv.pitchEnd, p2)

        # same with keywords, but reversed
        intv = interval.Interval(pitchStart=p2, pitchEnd=p1)
        self.assertEqual(intv.name, 'P5')
        self.assertEqual(intv.directedName, 'P-5')
        self.assertIs(intv.pitchStart, p2)
        self.assertIs(intv.pitchEnd, p1)

    def testFirst(self):
        from music21.note import Note
        from music21.pitch import Accidental
        n1 = Note()
        n2 = Note()

        n1.step = 'C'
        n1.octave = 4

        n2.step = 'B'
        n2.octave = 5
        n2.pitch.accidental = Accidental('-')

        int0 = Interval(noteStart=n1, noteEnd=n2)
        dInt0 = int0.diatonic
        gInt0 = dInt0.generic

        self.assertFalse(gInt0.isDiatonicStep)
        self.assertTrue(gInt0.isSkip)

        n1.pitch.accidental = Accidental('#')
        int1 = Interval(noteStart=n1, noteEnd=n2)

        cInt1 = notesToChromatic(n1, n2)  # returns music21.interval.ChromaticInterval object
        cInt2 = int1.chromatic  # returns same as cInt1 -- a different way of thinking of things
        self.assertEqual(cInt1.semitones, cInt2.semitones)

        self.assertEqual(int1.simpleNiceName, 'Diminished Seventh')

        self.assertEqual(int1.directedSimpleNiceName, 'Ascending Diminished Seventh')
        self.assertEqual(int1.name, 'd14')
        self.assertEqual(int1.specifier, Specifier.DIMINISHED)

        # returns same as gInt1 -- just a different way of thinking of things
        dInt1 = int1.diatonic
        gInt1 = dInt1.generic

        self.assertEqual(gInt1.directed, 14)
        self.assertEqual(gInt1.undirected, 14)
        self.assertEqual(gInt1.simpleDirected, 7)
        self.assertEqual(gInt1.simpleUndirected, 7)

        self.assertEqual(cInt1.semitones, 21)
        self.assertEqual(cInt1.undirected, 21)
        self.assertEqual(cInt1.mod12, 9)
        self.assertEqual(cInt1.intervalClass, 3)

        n4 = Note()
        n4.step = 'D'
        n4.octave = 3
        n4.pitch.accidental = '-'

        # n3 = interval.transposePitch(n4, 'AA8')
        # if n3.pitch.accidental is not None:
        #    print(n3.step, n3.pitch.accidental.name, n3.octave)
        # else:
        #    print(n3.step, n3.octave)
        # print(n3.name)
        # print()

        cI = ChromaticInterval(-14)
        self.assertEqual(cI.semitones, -14)
        self.assertEqual(cI.cents, -1400)
        self.assertEqual(cI.undirected, 14)
        self.assertEqual(cI.mod12, 10)
        self.assertEqual(cI.intervalClass, 2)

        lowB = Note()
        lowB.name = 'B'
        highBb = Note()
        highBb.name = 'B-'
        highBb.octave = 5
        dimOct = Interval(lowB, highBb)
        self.assertEqual(dimOct.niceName, 'Diminished Octave')

        noteA1 = Note()
        noteA1.name = 'E-'
        noteA1.octave = 4
        noteA2 = Note()
        noteA2.name = 'F#'
        noteA2.octave = 5
        intervalA1 = Interval(noteA1, noteA2)

        noteA3 = Note()
        noteA3.name = 'D'
        noteA3.octave = 1

        noteA4 = transposeNote(noteA3, intervalA1)
        self.assertEqual(noteA4.name, 'E#')
        self.assertEqual(noteA4.octave, 2)

        interval1 = Interval('-P5')

        n5 = transposeNote(n4, interval1)
        n6 = transposeNote(n4, 'P-5')
        self.assertEqual(n5.name, 'G-')
        self.assertEqual(n6.name, n5.name)

        # same thing using newer syntax:

        interval1 = Interval('P-5')

        n5 = transposeNote(n4, interval1)
        self.assertEqual(n5.name, 'G-')
        n7 = Note()
        n8 = transposeNote(n7, 'P8')
        self.assertEqual(n8.name, 'C')
        self.assertEqual(n8.octave, 5)

        n9 = transposeNote(n7, 'm7')  # should be B-
        self.assertEqual(n9.name, 'B-')
        self.assertEqual(n9.octave, 4)
        n10 = transposeNote(n7, 'dd-2')  # should be B##
        self.assertEqual(n10.name, 'B##')
        self.assertEqual(n10.octave, 3)

        # test getWrittenHigherNote functions
        (nE, nESharp, nFFlat, nF1, nF2) = (Note(), Note(), Note(), Note(), Note())

        nE.name = 'E'
        nESharp.name = 'E#'
        nFFlat.name = 'F-'
        nF1.name = 'F'
        nF2.name = 'F'

        higher1 = getWrittenHigherNote(nE, nESharp)
        higher2 = getWrittenHigherNote(nESharp, nFFlat)
        higher3 = getWrittenHigherNote(nF1, nF2)

        self.assertEqual(higher1, nESharp)
        self.assertEqual(higher2, nFFlat)
        self.assertEqual(higher3, nF1)  # in case of ties, first is returned

        higher4 = getAbsoluteHigherNote(nE, nESharp)
        higher5 = getAbsoluteHigherNote(nESharp, nFFlat)
        higher6 = getAbsoluteHigherNote(nESharp, nF1)
        higher7 = getAbsoluteHigherNote(nF1, nESharp)

        self.assertEqual(higher4, nESharp)
        self.assertEqual(higher5, nESharp)
        self.assertEqual(higher6, nESharp)
        self.assertEqual(higher7, nF1)

        lower1 = getWrittenLowerNote(nESharp, nE)
        lower2 = getWrittenLowerNote(nFFlat, nESharp)
        lower3 = getWrittenLowerNote(nF1, nF2)

        self.assertEqual(lower1, nE)
        self.assertEqual(lower2, nESharp)
        self.assertEqual(lower3, nF1)  # still returns first.

        lower4 = getAbsoluteLowerNote(nESharp, nE)
        lower5 = getAbsoluteLowerNote(nFFlat, nESharp)
        lower6 = getAbsoluteLowerNote(nESharp, nF1)

        self.assertEqual(lower4, nE)
        self.assertEqual(lower5, nFFlat)
        self.assertEqual(lower6, nESharp)

        middleC = Note()
        lowerC = Note()
        lowerC.octave = 3
        descendingOctave = Interval(middleC, lowerC)
        self.assertEqual(descendingOctave.generic.simpleDirected, 1)
        # no descending unisons ever
        self.assertEqual(descendingOctave.generic.semiSimpleDirected, -8)
        # no descending unisons ever
        self.assertEqual(descendingOctave.directedName, 'P-8')
        self.assertEqual(descendingOctave.directedSimpleName, 'P1')

        lowerG = Note()
        lowerG.name = 'G'
        lowerG.octave = 3
        descendingFourth = Interval(middleC, lowerG)
        self.assertEqual(descendingFourth.diatonic.directedNiceName,
                         'Descending Perfect Fourth')
        self.assertEqual(descendingFourth.diatonic.directedSimpleName, 'P-4')
        self.assertEqual(descendingFourth.diatonic.simpleName, 'P4')
        self.assertEqual(descendingFourth.diatonic.mod7, 'P5')

        perfectFifth = descendingFourth.complement
        self.assertEqual(perfectFifth.niceName, 'Perfect Fifth')
        self.assertEqual(perfectFifth.diatonic.simpleName, 'P5')
        self.assertEqual(perfectFifth.diatonic.mod7, 'P5')
        self.assertEqual(perfectFifth.complement.niceName, 'Perfect Fourth')

    def testCreateIntervalFromPitch(self):
        from music21 import pitch
        p1 = pitch.Pitch('c')
        p2 = pitch.Pitch('g')
        i = Interval(p1, p2)
        self.assertEqual(i.intervalClass, 5)

    def testTransposeImported(self):

        def collectAccidentalDisplayStatus(s_inner):
            post = []
            for e in s_inner.flatten().notes:
                if e.pitch.accidental is not None:
                    post.append(e.pitch.accidental.displayStatus)
                else:  # mark as not having an accidental
                    post.append('x')
            return post

        from music21 import corpus
        s = corpus.parse('bach/bwv66.6')
        # this has accidentals in measures 2 and 6
        sSub = s.parts[3].measures(2, 6)

        self.assertEqual(collectAccidentalDisplayStatus(sSub),
                         ['x', False, 'x', 'x', True, False, 'x', False, False, False,
                          False, False, False, 'x', 'x', 'x', False, False, False,
                          'x', 'x', 'x', 'x', True, False])

        sTransposed = sSub.flatten().transpose('p5')
        # sTransposed.show()

        self.assertEqual(collectAccidentalDisplayStatus(sTransposed),
                         ['x', None, 'x', 'x', None, None, None, None, None,
                          None, None, None, None, 'x', None, None, None, None,
                          None, 'x', 'x', 'x', None, None, None])

    def testIntervalMicrotonesA(self):
        from music21 import interval
        from music21 import pitch

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

        i = interval.Interval(5.25)  # a sharp p4
        self.assertEqual(i.cents, 525.0)
        # we can subtract the two to get an offset
        self.assertEqual(i.cents, 525.0)
        self.assertEqual(str(i), '<music21.interval.Interval P4 (+25c)>')
        self.assertEqual(i._diatonicIntervalCentShift(), 25)

        i = interval.Interval(4.75)  # a flat p4
        self.assertEqual(str(i), '<music21.interval.Interval P4 (-25c)>')
        self.assertEqual(i._diatonicIntervalCentShift(), -25)

        i = interval.Interval(4.48)  # a sharp M3
        self.assertEqual(str(i), '<music21.interval.Interval M3 (+48c)>')
        self.assertAlmostEqual(i._diatonicIntervalCentShift(), 48.0)

        i = interval.Interval(4.5)  # a sharp M3
        self.assertEqual(str(i), '<music21.interval.Interval M3 (+50c)>')
        self.assertAlmostEqual(i._diatonicIntervalCentShift(), 50.0)

        i = interval.Interval(5.25)  # a sharp p4
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F4(+25c)')

        i = interval.Interval(5.80)  # a sharp p4
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F#4(-20c)')

        i = interval.Interval(6.00)  # an exact Tritone
        p1 = pitch.Pitch('c4')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F#4')

        i = interval.Interval(5)  # a chromatic p4
        p1 = pitch.Pitch('c4')
        p1.microtone = 10  # c+20
        self.assertEqual(str(p1), 'C4(+10c)')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'F4(+10c)')

        i = interval.Interval(7.20)  # a sharp P5
        p1 = pitch.Pitch('c4')
        p1.microtone = -20  # c+20
        self.assertEqual(str(p1), 'C4(-20c)')
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'G4')

        i = interval.Interval(7.20)  # a sharp P5
        p1 = pitch.Pitch('c4')
        p1.microtone = 80  # c+20
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'G#4')

        i = interval.Interval(0.20)  # a sharp unison
        p1 = pitch.Pitch('e4')
        p1.microtone = 10
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E~4(-20c)')

        i = interval.Interval(0.05)  # a tiny bit sharp unison
        p1 = pitch.Pitch('e4')
        p1.microtone = 5
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E4(+10c)')

        i = interval.Interval(12.05)  # a tiny bit sharp octave
        p1 = pitch.Pitch('e4')
        p1.microtone = 5
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E5(+10c)')

        i = interval.Interval(11.85)  # a flat octave
        p1 = pitch.Pitch('e4')
        p1.microtone = 5
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E5(-10c)')

        i = interval.Interval(11.85)  # a flat octave
        p1 = pitch.Pitch('e4')
        p1.microtone = -20
        p2 = i.transposePitch(p1)
        self.assertEqual(str(p2), 'E`5(+15c)')

    def testIntervalMicrotonesB(self):
        from music21 import interval
        from music21 import note
        i = interval.Interval(note.Note('c4'), note.Note('c#4'))
        self.assertEqual(str(i), '<music21.interval.Interval A1>')

        i = interval.Interval(note.Note('c4'), note.Note('c~4'))
        self.assertEqual(str(i), '<music21.interval.Interval A1 (-50c)>')

    def testDescendingAugmentedUnison(self):
        from music21 import interval
        from music21 import note
        ns = note.Note('C4')
        ne = note.Note('C-4')
        i = interval.Interval(noteStart=ns, noteEnd=ne)
        directedNiceName = i.directedNiceName
        self.assertEqual(directedNiceName, 'Descending Diminished Unison')

    def testTransposeWithChromaticInterval(self):
        from music21 import interval
        from music21 import note
        ns = note.Note('C4')
        i = interval.ChromaticInterval(5)
        n2 = ns.transpose(i)
        self.assertEqual(n2.nameWithOctave, 'F4')

        ns = note.Note('B#3')
        i = interval.ChromaticInterval(5)
        n2 = ns.transpose(i)
        self.assertEqual(n2.nameWithOctave, 'F4')

    def testTransposeImplicit(self):
        from music21 import interval
        from music21 import pitch
        p = pitch.Pitch('D#4')
        i = interval.Interval(0)
        self.assertTrue(i.implicitDiatonic)
        p2 = i.transposePitch(p)
        self.assertEqual(p.ps, p2.ps)
        self.assertNotEqual(p.name, p2.name)

    def testRepeatedTransposePitch(self):
        from music21 import interval
        from music21 import pitch
        p = pitch.Pitch('C1')
        intv = interval.Interval('P5')
        out = []
        for _ in range(33):
            out.append(p.nameWithOctave)
            intv.transposePitch(p, maxAccidental=None, inPlace=True)
        self.assertEqual(
            out,
            ['C1', 'G1', 'D2', 'A2', 'E3', 'B3', 'F#4',
             'C#5', 'G#5', 'D#6', 'A#6', 'E#7', 'B#7', 'F##8',
             'C##9', 'G##9', 'D##10', 'A##10', 'E##11', 'B##11', 'F###12',
             'C###13', 'G###13', 'D###14', 'A###14', 'E###15', 'B###15', 'F####16',
             'C####17', 'G####17', 'D####18', 'A####18', 'E####19',
             ]
        )
        with self.assertRaisesRegex(pitch.AccidentalException,
                                    '5.0 is not a supported accidental type'):
            intv.transposePitch(p, maxAccidental=None)
        p2 = intv.transposePitch(p)
        self.assertEqual(p2.nameWithOctave, 'B-20')


    def testIntervalWithOneNoteGiven(self):
        from music21 import interval
        from music21 import note
        noteC = note.Note('C4')
        with self.assertRaises(ValueError):
            i = interval.Interval(name='P4', noteStart=noteC)
        i = interval.Interval(name='P4')
        i.noteStart = noteC
        self.assertEqual(i.noteEnd.nameWithOctave, 'F4')
        noteF = i.noteEnd

        # giving noteStart and noteEnd and a name where the name does not match
        # the notes is an exception.
        with self.assertRaises(ValueError):
            interval.Interval(name='d5', noteStart=noteC, noteEnd=noteF)

        # same with chromatic only intervals
        with self.assertRaises(ValueError):
            interval.Interval(chromatic=interval.ChromaticInterval(6),
                              noteStart=noteC,
                              noteEnd=noteF)

        # but these should work
        i2 = interval.Interval(name='P4', noteStart=noteC, noteEnd=noteF)
        self.assertIs(i2.noteStart, noteC)
        self.assertIs(i2.noteEnd, noteF)
        self.assertEqual(i2.name, 'P4')
        self.assertEqual(i2.semitones, 5)

        i3 = interval.Interval(chromatic=interval.ChromaticInterval(5),
                               noteStart=noteC,
                               noteEnd=noteF)
        self.assertIs(i3.noteStart, noteC)
        self.assertIs(i3.noteEnd, noteF)
        self.assertEqual(i3.name, 'P4')
        self.assertEqual(i3.semitones, 5)


    def testEmptyIntervalProperties(self):
        '''
        As of v8, an empty Interval is equal to P1
        '''
        empty = DiatonicInterval()
        self.assertEqual(empty.cents, 0.0)

        empty = Interval()
        self.assertEqual(empty.cents, 0.0)
        self.assertEqual(empty.intervalClass, 0)
        self.assertEqual(empty.name, 'P1')


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [notesToChromatic, intervalsToDiatonic,
              intervalFromGenericAndChromatic,
              Interval]


if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)


