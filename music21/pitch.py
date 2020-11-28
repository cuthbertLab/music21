# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         pitch.py
# Purpose:      music21 classes for representing pitches
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Classes for representing and manipulating pitches, pitch-space, and accidentals.

Each :class:`~music21.note.Note` object has a `Pitch` object embedded in it.
Some of the methods below, such as `Pitch.name`, `Pitch.step`, etc. are
made available directly in the `Note` object, so they will seem familiar.
'''
import copy
import math
import itertools
import unittest
from collections import OrderedDict
from typing import List, Optional, Union, TypeVar, Tuple, Dict

from music21 import base
from music21 import common
from music21 import defaults
from music21 import exceptions21
from music21 import interval
from music21 import style
from music21 import prebase

from music21.common.objects import SlottedObjectMixin
from music21 import environment

_T = TypeVar('_T')

_MOD = 'pitch'
environLocal = environment.Environment(_MOD)

STEPREF = {
    'C': 0,
    'D': 2,
    'E': 4,
    'F': 5,
    'G': 7,
    'A': 9,
    'B': 11,
}
STEPNAMES = {'C', 'D', 'E', 'F', 'G', 'A', 'B'}  # set
STEP_TO_DNN_OFFSET = {'C': 0, 'D': 1, 'E': 2, 'F': 3, 'G': 4, 'A': 5, 'B': 6}


TWELFTH_ROOT_OF_TWO = 2.0 ** (1 / 12)

# how many significant digits to keep in pitch space resolution
# where 1 is a half step. this means that 4 significant digits of cents will be kept
PITCH_SPACE_SIG_DIGITS = 6

# basic accidental string and symbol definitions;
# additional symbolic and text-based alternatives
# are given in the set Accidental.set() method
MICROTONE_OPEN = '('
MICROTONE_CLOSE = ')'

accidentalNameToModifier = {
    'natural': '',
    'sharp': '#',
    'double-sharp': '##',
    'triple-sharp': '###',
    'quadruple-sharp': '####',
    'flat': '-',
    'double-flat': '--',
    'triple-flat': '---',
    'quadruple-flat': '----',
    'half-sharp': '~',
    'one-and-a-half-sharp': '#~',
    'half-flat': '`',
    'one-and-a-half-flat': '-`',
}

unicodeFromModifier = OrderedDict([
    ('####', chr(0x1d12a) + chr(0x1d12a)),
    ('###', '\u266f' + chr(0x1d12a)),
    ('##', chr(0x1d12a)),  # 1D12A  # note that this must be expressed as a surrogate pair
    ('#~', '\u266f' + chr(0x1d132)),  # 1D132
    ('#', '\u266f'),
    ('~', chr(0x1d132)),  # 1D132
    ('----', chr(0x1d12b) + chr(0x1d12b)),
    ('---', '\u266D'),
    ('--', chr(0x1d12b)),
    ('-`', '\u266D' + chr(0x1d132)),
    ('-', '\u266D'),
    ('`', chr(0x1d132)),  # 1D132; raised flat: 1D12C
    ('', '\u266e'),  # natural
])


# sort modifiers by length, from longest to shortest
def _sortModifiers():
    for i in (4, 3, 2, 1):
        ams = []
        for sym in accidentalNameToModifier.values():
            if len(sym) == i:
                ams.append(sym)
        return ams


accidentalModifiersSorted = _sortModifiers()


# ------------------------------------------------------------------------------
# utility functions

def _convertPitchClassToNumber(ps) -> int:
    '''
    Given a pitch class string
    return the pitch class representation.
    Ints are returned unchanged;

    >>> pitch._convertPitchClassToNumber(3)
    3
    >>> pitch._convertPitchClassToNumber('a')
    10
    >>> pitch._convertPitchClassToNumber('B')
    11
    >>> pitch._convertPitchClassToNumber('3')
    3
    '''
    if common.isNum(ps):
        return ps
    else:  # assume is is a string
        if ps in ('a', 'A'):
            return 10
        if ps in ('b', 'B'):
            return 11
        # maybe it is a string of an integer?
        return int(ps)


def convertPitchClassToStr(pc) -> str:
    '''
    Given a pitch class number, return a string.

    >>> pitch.convertPitchClassToStr(3)
    '3'
    >>> pitch.convertPitchClassToStr(10)
    'A'
    '''
    pc = pc % 12  # do just in case
    # replace 10 with A and 11 with B
    return '%X' % pc  # using hex conversion, good up to 15


def _convertPsToOct(ps: Union[int, float]) -> int:
    '''
    Utility conversion; does not process internals.
    Converts a midiNote number to an octave number.
    Assume C4 middle C, so 60 returns 4

    >>> [pitch._convertPsToOct(59), pitch._convertPsToOct(60), pitch._convertPsToOct(61)]
    [3, 4, 4]
    >>> [pitch._convertPsToOct(12), pitch._convertPsToOct(0), pitch._convertPsToOct(-12)]
    [0, -1, -2]
    >>> pitch._convertPsToOct(135)
    10

    Note that while this is basically a floor operation, we only treat 6 digits as significant
    (PITCH_SPACE_SIGNIFICANT_DIGITS)

    >>> pitch._convertPsToOct(71.999)
    4
    >>> pitch._convertPsToOct(71.99999999)
    5
    >>> pitch._convertPsToOct(72)
    5

    '''
    # environLocal.printDebug(['_convertPsToOct: input', ps])
    ps = round(ps, PITCH_SPACE_SIG_DIGITS)
    return int(math.floor(ps / 12.)) - 1


def _convertPsToStep(ps) -> Tuple[str, 'Accidental', 'Microtone', int]:
    '''
    Utility conversion; does not process internal representations.

    Takes in a pitch space floating-point value or a MIDI note number (Assume
    C4 middle C, so 60 returns 4).

    Returns a tuple of Step, an Accidental object, a Microtone object or
    None, and an int representing octave shift.

    >>> pitch._convertPsToStep(60)
    ('C', <accidental natural>, (+0c), 0)
    >>> pitch._convertPsToStep(66)
    ('F', <accidental sharp>, (+0c), 0)
    >>> pitch._convertPsToStep(67)
    ('G', <accidental natural>, (+0c), 0)
    >>> pitch._convertPsToStep(68)
    ('G', <accidental sharp>, (+0c), 0)
    >>> pitch._convertPsToStep(-2)
    ('B', <accidental flat>, (+0c), 0)

    >>> pitch._convertPsToStep(60.5)
    ('C', <accidental half-sharp>, (+0c), 0)
    >>> pitch._convertPsToStep(61.5)
    ('C', <accidental one-and-a-half-sharp>, (+0c), 0)
    >>> pitch._convertPsToStep(62)
    ('D', <accidental natural>, (+0c), 0)
    >>> pitch._convertPsToStep(62.5)
    ('D', <accidental half-sharp>, (+0c), 0)
    >>> pitch._convertPsToStep(135)
    ('E', <accidental flat>, (+0c), 0)
    >>> pitch._convertPsToStep(70)
    ('B', <accidental flat>, (+0c), 0)
    >>> pitch._convertPsToStep(70.5)
    ('B', <accidental half-flat>, (+0c), 0)

    >>> pitch._convertPsToStep(72.0)
    ('C', <accidental natural>, (+0c), 0)
    >>> pitch._convertPsToStep(71.9999999)
    ('C', <accidental natural>, (+0c), 0)


    >>> pitch._convertPsToStep(43.0)
    ('G', <accidental natural>, (+0c), 0)
    >>> pitch._convertPsToStep(42.999739)
    ('G', <accidental natural>, (-0c), 0)

    '''
    name = ''

    # rounding here is essential
    ps = round(ps, PITCH_SPACE_SIG_DIGITS)
    pcReal = ps % 12
    # micro here will be between 0 and 1
    pc, micro = divmod(pcReal, 1)

    # environLocal.printDebug(['_convertPsToStep(): post divmod',  'ps', repr(ps),
    #    'pcReal', repr(pcReal), 'pc', repr(pc), 'micro', repr(micro)])

    # if close enough to a quarter tone
    if round(micro, 1) == 0.5:
        # if can round to 0.5, than this is a quarter-tone accidental
        alter = 0.5
        # need to find microtonal alteration around this value
        # of alter is 0.5 and micro is 0.7 than  micro should be 0.2
        # of alter is 0.5 and micro is 0.4 than  micro should be -0.1
        micro = micro - alter

    # if greater than 0.5
    elif 0.25 < micro < 0.75:
        alter = 0.5
        micro = micro - alter
    # if closer to 1, than go to the higher alter and get negative micro
    elif 0.75 <= micro < 1:
        alter = 1
        micro = micro - alter
    # not greater than 0.25
    elif micro > 0:
        alter = 0
        # micro = micro  # no change necessary
    else:
        alter = 0
        micro = 0

    pc = int(pc)

    # environLocal.printDebug(['_convertPsToStep(): post', 'alter', alter,
    #    'micro', micro, 'pc', pc])

    octShift = 0
    # check for unnecessary enharmonics
    if pc in (4, 11) and alter == 1:
        acc = Accidental(0)
        pcName = (pc + 1) % 12
        # if a B, we are shifting out of this octave, and need to get
        # the above octave, which may not be represented in ps value
        if pc == 11:
            octShift = 1
    # its a natural; nothing to do
    elif pc in STEPREF.values():
        acc = Accidental(0 + alter)
        pcName = pc

    elif (pc - 1) in (0, 5, 7) and alter >= 1:  # is this going to be a C##, F##, G##?
        acc = Accidental(alter - 1)
        pcName = pc + 1
    # if we take the pc down a half-step, do we get a stepref (natural) value
    elif (pc - 1) in (0, 5, 7):  # c, f, g: can be sharped
        # then we need an accidental to accommodate; here, a sharp
        acc = Accidental(1 + alter)
        pcName = pc - 1

    elif (pc + 1) in (11, 4) and alter <= -1:  # is this going to be an E-- or B--?
        acc = Accidental(1 + alter)
        pcName = pc - 1
    # if we take the pc up a half-step, do we get a stepref (natural) value
    elif (pc + 1) in (11, 4):  # b, e: can be flattened
        # then we need an accidental to accommodate; here, a flat
        acc = Accidental(-1 + alter)
        pcName = pc + 1
    else:  # pragma: no cover
        raise PitchException('cannot match condition for pc: %s' % pc)

    for key, value in STEPREF.items():
        if pcName == value:
            name = key
            break

    # create a micro object always
    if micro != 0:
        # provide cents value; these are alter values
        micro = Microtone(micro * 100)
    else:
        micro = Microtone(0)

    return name, acc, micro, octShift


def _convertCentsToAlterAndCents(shift) -> Tuple[Union[int, float], float]:
    '''
    Given any floating point value, split into accidental and microtone components.

    >>> pitch._convertCentsToAlterAndCents(125)
    (1, 25.0)
    >>> pitch._convertCentsToAlterAndCents(-75)
    (-0.5, -25.0)
    >>> pitch._convertCentsToAlterAndCents(-125)
    (-1, -25.0)
    >>> pitch._convertCentsToAlterAndCents(-200)
    (-2, 0.0)
    >>> pitch._convertCentsToAlterAndCents(235)
    (2.5, -15.0)
    '''
    value = shift

    alterAdd = 0
    if value > 150:
        while value > 100:
            value -= 100
            alterAdd += 1
    elif value < -150:
        while value < 100:
            value += 100
            alterAdd -= 1

    if value < -75:
        alterShift = -1
        cents = value + 100
    elif -75 <= value < -25:
        alterShift = -0.5
        cents = value + 50
    elif -25 <= value <= 25:
        alterShift = 0
        cents = value
    elif 25 < value <= 75:
        alterShift = 0.5
        cents = value - 50
    elif value > 75:
        alterShift = 1
        cents = value - 100
    else:  # pragma: no cover
        raise Exception('value exceeded range: %s' % value)
    return alterShift + alterAdd, float(cents)


def _convertHarmonicToCents(value: Union[int, float]) -> int:
    r'''
    Given a harmonic number, return the total number shift in cents
    assuming 12 tone equal temperament.

    >>> pitch._convertHarmonicToCents(8)
    3600
    >>> [pitch._convertHarmonicToCents(x) for x in [5, 6, 7, 8]]
    [2786, 3102, 3369, 3600]
    >>> [pitch._convertHarmonicToCents(x) for x in [16, 17, 18, 19]]
    [4800, 4905, 5004, 5098]

    >>> [pitch._convertHarmonicToCents(x) for x in range(1, 33)]
    [0, 1200, 1902, 2400, 2786, 3102, 3369, 3600, 3804, 3986, 4151,
     4302, 4441, 4569, 4688, 4800, 4905, 5004, 5098, 5186, 5271, 5351,
     5428, 5502, 5573, 5641, 5706, 5769, 5830, 5888, 5945, 6000]


    Works with subHarmonics as well by specifying them as either 1/x or negative numbers.
    note that -2 is the first subharmonic, since -1 == 1:

    >>> [pitch._convertHarmonicToCents(1 / x) for x in [1, 2, 3, 4]]
    [0, -1200, -1902, -2400]
    >>> [pitch._convertHarmonicToCents(x) for x in [-1, -2, -3, -4]]
    [0, -1200, -1902, -2400]

    So the fifth subharmonic of the 7th harmonic,
    which is C2->C3->G3->C4->E4->G4->B\`4 --> B\`3->E\`3->B\`2->G-\`2

    >>> pitch._convertHarmonicToCents(7 / 5)
    583
    >>> pitch._convertHarmonicToCents(7.0) - pitch._convertHarmonicToCents(5.0)
    583
    '''
    if value < 0:  # subharmonics
        value = 1 / (abs(value))
    return round(1200 * math.log2(value))

# -----------------------------------------------------------------------------


def _dissonanceScore(pitches, smallPythagoreanRatio=True, accidentalPenalty=True, triadAward=True):
    r'''
    Calculates the 'dissonance' of a list of pitches based on three criteria:
    it is considered more consonant if 1. the numerator and denominator of the
    Pythagorean ratios of its containing intervals are small (`smallPythagoreanRatio`);
    2. it shows few double- or triple-accidentals (`accidentalPenalty`); 3. it shows
    thirds that can form some triad (`triadAward`)
    '''
    score_accidentals = 0.0
    score_ratio = 0.0
    score_triad = 0.0

    if not pitches:
        return 0.0

    if accidentalPenalty:
        # score_accidentals = accidentals per pitch
        accidentals = [abs(p.alter) for p in pitches]
        score_accidentals = sum(a if a > 1 else 0 for a in accidentals) / len(pitches)

    if smallPythagoreanRatio:
        # score_ratio = Pythagorean ratio complexity per pitch
        for p1, p2 in itertools.combinations(pitches, 2):
            # does not accept weird intervals, e.g. with semitones
            try:
                this_interval = interval.Interval(noteStart=p1, noteEnd=p2)
                ratio = interval.intervalToPythagoreanRatio(this_interval)
                penalty = (math.log(ratio.numerator * ratio.denominator / ratio)
                                        / 26.366694928034633)  # d2 is 1.0
                score_ratio += penalty
            except interval.IntervalException:
                return math.inf

        score_ratio = score_ratio / len(pitches)

    if triadAward:
        # score_triad = number of thirds per pitch (avoid double-base-thirds)
        triad_bases = []
        for p1, p2 in itertools.combinations(pitches, 2):
            this_interval = interval.Interval(noteStart=p1, noteEnd=p2)
            generic_interval_value = abs(this_interval.generic.value) % 8
            interval_semitones = this_interval.chromatic.semitones % 12
            if generic_interval_value == 3 and interval_semitones in (3, 4):
                triad_steps = (p1.step, p2.step)
                if triad_steps not in triad_bases:
                    score_triad -= 1.0
            elif generic_interval_value == 6 and interval_semitones in (8, 9):
                triad_steps = (p2.step, p1.step)
                if triad_steps not in triad_bases:
                    score_triad -= 1.0
        score_triad /= len(pitches)

    return (score_accidentals + score_ratio + score_triad) / int(smallPythagoreanRatio
                                                                 + accidentalPenalty + triadAward)


def _bruteForceEnharmonicsSearch(oldPitches, scoreFunc=_dissonanceScore):
    '''
    A brute-force way of simplifying -- useful if there are fewer than 5 pitches
    '''
    all_possible_pitches = [[p] + p.getAllCommonEnharmonics() for p in oldPitches[1:]]
    all_pitch_combinations = itertools.product(*all_possible_pitches)
    newPitches = min(all_pitch_combinations, key=lambda x: scoreFunc(oldPitches[:1] + list(x)))
    return oldPitches[:1] + list(newPitches)


def _greedyEnharmonicsSearch(oldPitches, scoreFunc=_dissonanceScore):
    newPitches = oldPitches[:1]
    for oldPitch in oldPitches[1:]:
        candidates = [oldPitch] + oldPitch.getAllCommonEnharmonics()
        newPitch = min(candidates, key=lambda x: scoreFunc(newPitches + [x]))
        newPitches.append(newPitch)
    return newPitches


def simplifyMultipleEnharmonics(pitches, criterion=_dissonanceScore, keyContext=None):
    r'''Tries to simplify the enharmonic spelling of a list of pitches, pitch-
    or pitch-class numbers according to a given criterion.

    A function can be passed as an argument to `criterion`, that is tried to be
    minimized in a greedy left-to-right fashion.

    >>> pitch.simplifyMultipleEnharmonics([11, 3, 6])
    [<music21.pitch.Pitch B>, <music21.pitch.Pitch D#>, <music21.pitch.Pitch F#>]

    >>> pitch.simplifyMultipleEnharmonics([3, 8, 0])
    [<music21.pitch.Pitch E->, <music21.pitch.Pitch A->, <music21.pitch.Pitch C>]

    >>> pitch.simplifyMultipleEnharmonics([pitch.Pitch('G3'),
    ...                                    pitch.Pitch('C-4'),
    ...                                    pitch.Pitch('D4')])
    [<music21.pitch.Pitch G3>, <music21.pitch.Pitch B3>, <music21.pitch.Pitch D4>]

    >>> pitch.simplifyMultipleEnharmonics([pitch.Pitch('A3'),
    ...                                    pitch.Pitch('B#3'),
    ...                                    pitch.Pitch('E4')])
    [<music21.pitch.Pitch A3>, <music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>]

    The attribute `keyContext` is for supplying a KeySignature or a Key
    which is used in the simplification:

    >>> pitch.simplifyMultipleEnharmonics([6, 10, 1], keyContext=key.Key('B'))
    [<music21.pitch.Pitch F#>, <music21.pitch.Pitch A#>, <music21.pitch.Pitch C#>]

    >>> pitch.simplifyMultipleEnharmonics([6, 10, 1], keyContext=key.Key('C-'))
    [<music21.pitch.Pitch G->, <music21.pitch.Pitch B->, <music21.pitch.Pitch D->]


    Note that if there's no key context, then we won't simplify everything (at least
    for now; this behavior may change, ).

    >>> pitch.simplifyMultipleEnharmonics([pitch.Pitch('D--3'),
    ...                                    pitch.Pitch('F-3'),
    ...                                    pitch.Pitch('A--3')])
    [<music21.pitch.Pitch D--3>, <music21.pitch.Pitch F-3>, <music21.pitch.Pitch A--3>]



    >>> pitch.simplifyMultipleEnharmonics([pitch.Pitch('D--3'),
    ...                                    pitch.Pitch('F-3'),
    ...                                    pitch.Pitch('A--3')],
    ...                                    keyContext=key.Key('C'))
    [<music21.pitch.Pitch C3>, <music21.pitch.Pitch E3>, <music21.pitch.Pitch G3>]
    '''

    oldPitches = [p if isinstance(p, Pitch) else Pitch(p) for p in pitches]

    if keyContext:
        oldPitches = [keyContext.asKey('major').tonic] + oldPitches
        remove_first = True
    else:
        remove_first = False

    if len(oldPitches) < 5:
        simplifiedPitches = _bruteForceEnharmonicsSearch(oldPitches, criterion)
    else:
        simplifiedPitches = _greedyEnharmonicsSearch(oldPitches, criterion)

    if remove_first:
        simplifiedPitches = simplifiedPitches[1:]

    return simplifiedPitches

# -----------------------------------------------------------------------------


class AccidentalException(exceptions21.Music21Exception):
    pass


class PitchException(exceptions21.Music21Exception):
    pass


class MicrotoneException(exceptions21.Music21Exception):
    pass


# -----------------------------------------------------------------------------


class Microtone(prebase.ProtoM21Object, SlottedObjectMixin):
    '''
    The Microtone object defines a pitch transformation above or below a
    standard Pitch and its Accidental.

    >>> m = pitch.Microtone(20)
    >>> m.cents
    20

    >>> m.alter
    0.2...

    >>> m
    (+20c)

    Microtones can be shifted according to the harmonic. Here we take the 3rd
    harmonic of the previous microtone


    >>> m.harmonicShift = 3
    >>> m.harmonicShift
    3
    >>> m
    (+20c+3rdH)

    >>> m.cents
    1922

    >>> m.alter
    19.2...

    Microtonal changes can be positive or negative.  Both Positive and negative
    numbers can optionally be placed in parentheses Negative numbers in
    parentheses still need the minus sign.

    >>> m = pitch.Microtone('(-33.333333)')
    >>> m
    (-33c)

    >>> m = pitch.Microtone('33.333333')
    >>> m
    (+33c)

    Note that we round the display of microtones to the nearest cent, but we
    keep the exact alteration in both .cents and .alter:

    >>> m.cents
    33.333...

    >>> m.alter
    0.3333...

    '''

    # CLASS VARIABLES #

    __slots__ = (
        '_centShift',
        '_harmonicShift',
    )

    # INITIALIZER #

    def __init__(self,
                 centsOrString: Union[str, int, float] = 0,
                 harmonicShift=1):
        self._centShift = 0
        self._harmonicShift = harmonicShift  # the first harmonic is the start

        if common.isNum(centsOrString):
            self._centShift = centsOrString  # specify harmonic in cents
        else:
            self._parseString(centsOrString)
        # need to additional store a reference to a position in a
        # another pitches overtone series?
        # such as: A4(+69c [7thH/C3])?

    # SPECIAL METHODS #
    def __deepcopy__(self, memo):
        if type(self) is Microtone:  # pylint: disable=unidiomatic-typecheck
            return Microtone(self._centShift, self._harmonicShift)
        else:  # pragma: no cover
            return common.defaultDeepcopy(self, memo)

    def __eq__(self, other):
        '''
        Compare cents (including harmonicShift)

        >>> m1 = pitch.Microtone(20)
        >>> m2 = pitch.Microtone(20)
        >>> m3 = pitch.Microtone(21)
        >>> m1 == m2
        True
        >>> m1 == m3
        False

        >>> m2.harmonicShift = 3
        >>> m1 == m2
        False

        Cannot compare True to a non-Microtone:

        >>> m1 == pitch.Accidental(1)
        False
        '''
        try:
            if other.cents == self.cents:
                return True
            return False
        except AttributeError:
            return False

    def __hash__(self):
        hashValues = (
            self._centShift,
            self._harmonicShift,
            type(self),
        )
        return hash(hashValues)

    def __repr__(self):
        '''
        Return a string representation.

        >>> m1 = pitch.Microtone(20)
        >>> repr(m1)
        '(+20c)'

        Basically the same as just doing, except with quotes

        >>> m1
        (+20c)

        '''
        # cent values may be of any resolution, but round to nearest int
        sub = ''

        if self._centShift >= 0:
            sub = '+%sc' % round(self._centShift)
        elif self._centShift < 0:
            sub = '%sc' % round(self._centShift)
            if sub == '0c':
                sub = '-0c'

        # only show a harmonic if present
        if self._harmonicShift != 1:
            sub += '+%s%sH' % (self._harmonicShift,
                               common.ordinalAbbreviation(self._harmonicShift))
        return '%s%s%s' % (MICROTONE_OPEN, sub, MICROTONE_CLOSE)

    # PRIVATE METHODS #

    def _parseString(self, value):
        '''
        Parse a string representation.
        '''
        # strip any delimiters
        value = value.replace(MICROTONE_OPEN, '')
        value = value.replace(MICROTONE_CLOSE, '')
        centValue = 0

        # need to look for and split off harmonic definitions
        if value[0] == '+' or value[0].isdigit():
            # positive cent representation
            num, unused_nonNum = common.getNumFromStr(value, numbers='0123456789.')
            if num == '':
                raise MicrotoneException('no numbers found in string value: %s' % value)
            centValue = float(num)
        elif value[0] == '-':
            num, unused_nonNum = common.getNumFromStr(value[1:], numbers='0123456789.')
            centValue = float(num) * -1
        self._centShift = centValue

    # PUBLIC PROPERTIES #

    @property
    def alter(self):
        '''
        Return the microtone value in accidental alter values.

        >>> pitch.Microtone(20).alter
        0.2
        '''
        return self.cents * 0.01

    @property
    def cents(self):
        '''
        Return the microtone value in cents.  This is not a settable property.
        To set the value in cents, simply use that value as a creation
        argument.

        >>> pitch.Microtone(20).cents
        20
        '''
        return _convertHarmonicToCents(self._harmonicShift) + self._centShift

    @property
    def harmonicShift(self):
        '''
        Set or get the harmonic shift, altering the microtone
        '''
        return self._harmonicShift

    @harmonicShift.setter
    def harmonicShift(self, value):
        self._harmonicShift = value


class Accidental(prebase.ProtoM21Object, style.StyleMixin):
    '''
    Accidental class, representing the symbolic and numerical representation of
    pitch deviation from a pitch name (e.g., G, B).

    Two accidentals are considered equal if their names are equal.

    Accidentals have three defining attributes: a name, a modifier, and an
    alter.  For microtonal specifications, the name and modifier are the same
    except in the case of half-sharp, half-flat, one-and-a-half-flat, and
    one-and-a-half-sharp.

    Accidentals up to quadruple-sharp and quadruple-flat are allowed.

    Natural-sharp etc. (for canceling a previous flat) are not yet supported officially.

    >>> a = pitch.Accidental('sharp')
    >>> a.name, a.alter, a.modifier
    ('sharp', 1.0, '#')
    >>> a.style.color = 'red'

    >>> import copy
    >>> b = copy.deepcopy(a)
    >>> b.style.color
    'red'
    '''
    _styleClass = style.TextStyle
    # CLASS VARIABLES #

    __slots__ = (
        '_alter',
        '_displayStatus',
        '_displayType',
        '_modifier',
        '_name',
        '_client',
        'displayLocation',
        'displaySize',
        'displayStyle',
    )

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['name', 'modifier', 'alter', 'set']

    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
        'displaySize': 'Size in display: "cue", "large", or a percentage.',
        'displayStyle': 'Style of display: "parentheses", "bracket", "both".',
        'displayLocation': 'Location of accidental: "normal", "above", "below".',
    }

    # INITIALIZER #

    def __init__(self, specifier: Union[int, str, float] = 'natural'):
        super().__init__()
        # managed by properties
        self._displayType = 'normal'  # always, never, unless-repeated, even-tied
        self._displayStatus = None  # None, True, False

        # not yet managed by properties: TODO
        self.displayStyle = 'normal'  # 'parentheses', 'bracket', 'both'
        self.displaySize = 'full'   # 'cue', 'large', or a percentage
        # 'normal', 'above' = ficta, 'below'
        # above and below could also be useful for gruppetti, etc.
        self.displayLocation = 'normal'

        # store a reference to the object that has this duration object as a property
        self._client: Optional['Pitch'] = None
        self._name = None
        self._modifier = ''
        self._alter = 0.0     # semitones to alter step
        # potentially can be a fraction... but not exponent...
        self.set(specifier)

    # SPECIAL METHODS #
    def _hashValues(self):
        return (
            self._alter,
            self._displayStatus,
            self._displayType,
            self._modifier,
            self._name,
            self.displayLocation,
            self.displaySize,
            self.displayStyle,
        )

    def __hash__(self):
        return hash(self._hashValues())

    def __deepcopy__(self, memo):
        if type(self) is Accidental:  # pylint: disable=unidiomatic-typecheck
            new = Accidental.__new__(Accidental)
            for s in self._getSlotsRecursive():
                setattr(new, s, getattr(self, s))
            return new
        else:  # pragma: no cover
            return common.defaultDeepcopy(self, memo)

    def __eq__(self, other):
        '''
        Equality. Needed for pitch comparisons.

        >>> a = pitch.Accidental('double-flat')
        >>> b = pitch.Accidental('double-flat')
        >>> c = pitch.Accidental('double-sharp')
        >>> a == b
        True

        >>> a == c
        False
        '''
        if other is None or not isinstance(other, Accidental):
            return False
        if self.name == other.name:
            return True
        else:
            return False

    def __ge__(self, other):
        '''
        Greater than or equal.  Based on the accidentals' alter function.

        >>> a = pitch.Accidental('sharp')
        >>> b = pitch.Accidental('flat')
        >>> a >= b
        True

        '''
        return self.__gt__(other) or self.__eq__(other)

    def __gt__(self, other):
        '''
        Greater than.  Based on the accidentals' alter function.

        >>> a = pitch.Accidental('sharp')
        >>> b = pitch.Accidental('flat')
        >>> a < b
        False

        >>> a > b
        True

        >>> a > 5
        False
        '''
        if other is None or not isinstance(other, Accidental):
            return False
        if self.alter > other.alter:
            return True
        else:
            return False

    def __le__(self, other):
        '''
        Less than or equal.  Based on the accidentals' alter function.

        >>> a = pitch.Accidental('sharp')
        >>> b = pitch.Accidental('flat')
        >>> c = pitch.Accidental('sharp')
        >>> a <= b
        False

        >>> a <= c
        True
        '''
        return self.__lt__(other) or self.__eq__(other)

    def __lt__(self, other):
        '''
        Less than. based on alter.

        >>> a = pitch.Accidental('natural')
        >>> b = pitch.Accidental('flat')
        >>> a > b
        True

        >>> a < b
        False

        >>> a < 5
        False
        '''
        if other is None or not isinstance(other, Accidental):
            return False
        if self.alter < other.alter:
            return True
        else:
            return False

    def __repr__(self):
        return '<accidental %s>' % self.name

    @classmethod
    def listNames(cls):
        '''
        Returns a list of accidental names that have any sort of
        semantic importance in music21.

        You may choose a name not from this list (1/7th-sharp) but
        if it's not on this list don't expect it to do anything for you.

        This is a class method, so you may call it directly on the class:

        Listed in alphabetical order. (TODO: maybe from lowest to highest
        or something implying importance?)

        >>> pitch.Accidental.listNames()
         ['double-flat', 'double-sharp', 'flat', 'half-flat',
          'half-sharp', 'natural', 'one-and-a-half-flat', 'one-and-a-half-sharp',
          'quadruple-flat', 'quadruple-sharp', 'sharp', 'triple-flat', 'triple-sharp']

        Or call on an instance of an accidental:

        >>> f = pitch.Accidental('flat')
        >>> f.listNames()
         ['double-flat', 'double-sharp', 'flat', 'half-flat', 'half-sharp', 'natural',
          'one-and-a-half-flat', 'one-and-a-half-sharp', 'quadruple-flat', 'quadruple-sharp',
          'sharp', 'triple-flat', 'triple-sharp']
        '''
        return sorted(accidentalNameToModifier.keys(), key=str.lower)

    # PUBLIC METHODS #

    def set(self, name, *, allowNonStandardValue=False):
        '''
        Change the type of the Accidental. Strings values, numbers, and Lilypond
        Abbreviations are all accepted.  All other values will change
        after setting.

        >>> a = pitch.Accidental()
        >>> a.set('sharp')
        >>> a.alter
        1.0

        >>> a = pitch.Accidental()
        >>> a.set(2)
        >>> a.modifier == '##'
        True

        >>> a = pitch.Accidental()
        >>> a.set(2.0)
        >>> a.modifier == '##'
        True

        >>> a = pitch.Accidental('--')
        >>> a.alter
        -2.0
        >>> a.set('half-sharp')
        >>> a.alter
        0.5
        >>> a.name
        'half-sharp'

        Setting an illegal name is generally an error:

        >>> a.set('flat-flat-up')
        Traceback (most recent call last):
        music21.pitch.AccidentalException: flat-flat-up is not a supported accidental type

        But if 'allowNonStandardValue' is True then other names (if strings) or alters (if numbers)
        are allowed:

        >>> a.set('quintuple-sharp', allowNonStandardValue=True)
        >>> a.set(5.0, allowNonStandardValue=True)
        >>> a.name
        'quintuple-sharp'
        >>> a.alter
        5.0

        This is the argument that .name and .alter use to allow non-standard names


        Changed in v. 5 -- added allowNonStandardValue
        '''
        if isinstance(name, str):
            name = name.lower()  # sometimes args get capitalized
        if name in ('natural', 'n', 0):
            self._name = 'natural'
            self._alter = 0.0
        elif name in ('sharp', accidentalNameToModifier['sharp'], 'is', 1):
            self._name = 'sharp'
            self._alter = 1.0
        elif name in ('double-sharp', accidentalNameToModifier['double-sharp'],
                      'isis', 2):
            self._name = 'double-sharp'
            self._alter = 2.0
        elif name in ('flat', accidentalNameToModifier['flat'], 'es', 'b', -1):
            self._name = 'flat'
            self._alter = -1.0
        elif name in ('double-flat', accidentalNameToModifier['double-flat'],
                      'eses', -2):
            self._name = 'double-flat'
            self._alter = -2.0

        elif name in ('half-sharp', accidentalNameToModifier['half-sharp'],
                      'quarter-sharp', 'ih', 'semisharp', 0.5):
            self._name = 'half-sharp'
            self._alter = 0.5
        elif name in ('one-and-a-half-sharp',
                      accidentalNameToModifier['one-and-a-half-sharp'],
                      'three-quarter-sharp', 'three-quarters-sharp', 'isih',
                      'sesquisharp', 1.5):
            self._name = 'one-and-a-half-sharp'
            self._alter = 1.5
        elif name in ('half-flat', accidentalNameToModifier['half-flat'],
                      'quarter-flat', 'eh', 'semiflat', -0.5):
            self._name = 'half-flat'
            self._alter = -0.5
        elif name in ('one-and-a-half-flat',
                      accidentalNameToModifier['one-and-a-half-flat'],
                      'three-quarter-flat', 'three-quarters-flat', 'eseh',
                      'sesquiflat', -1.5):
            self._name = 'one-and-a-half-flat'
            self._alter = -1.5
        elif name in ('triple-sharp', accidentalNameToModifier['triple-sharp'],
                      'isisis', 3):
            self._name = 'triple-sharp'
            self._alter = 3.0
        elif name in ('quadruple-sharp',
                      accidentalNameToModifier['quadruple-sharp'], 'isisisis', 4):
            self._name = 'quadruple-sharp'
            self._alter = 4.0
        elif name in ('triple-flat', accidentalNameToModifier['triple-flat'],
                      'eseses', -3):
            self._name = 'triple-flat'
            self._alter = -3.0
        elif name in ('quadruple-flat',
                      accidentalNameToModifier['quadruple-flat'], 'eseseses', -4):
            self._name = 'quadruple-flat'
            self._alter = -4.0
        else:
            if not allowNonStandardValue:
                raise AccidentalException('%s is not a supported accidental type' % name)

            if isinstance(name, str):
                self._name = name
                return
            elif isinstance(name, (int, float)):
                self._alter = name
                return
            else:  # pragma: no cover
                raise AccidentalException('%s is not a supported accidental type' % name)

        self._modifier = accidentalNameToModifier[self._name]
        if self._client is not None:
            self._client.informClient()


    def isTwelveTone(self):
        '''Return a boolean if this Accidental describes a twelve-tone pitch.


        >>> a = pitch.Accidental('~')
        >>> a.isTwelveTone()
        False

        >>> a = pitch.Accidental('###')
        >>> a.isTwelveTone()
        True

        '''
        if self.name in ('half-sharp', 'one-and-a-half-sharp',
                         'half-flat', 'one-and-a-half-flat'):
            return False
        return True

    # --------------------------------------------------------------------------
    def setAttributeIndependently(self, attribute, value):
        '''
        Set an attribute of 'name', 'alter', and 'modifier', independently
        from other attributes.

        >>> a = pitch.Accidental('natural')
        >>> a.setAttributeIndependently('alter', 1.0)
        >>> a.alter
        1.0
        >>> a.name
        'natural'

        >>> a.setAttributeIndependently('name', 'sori')
        >>> a.setAttributeIndependently('modifier', '$')
        >>> a.modifier
        '$'
        >>> a.name
        'sori'
        >>> a.alter
        1.0

        Only 'name', 'alter', and 'modifier' can be set independently:

        >>> a.setAttributeIndependently('color', 'red')
        Traceback (most recent call last):
        music21.pitch.AccidentalException: Cannot set attribute color independently of other parts.

        New in v.5 -- needed because .name, .alter, and .modifier run .set()
        '''
        if attribute not in ('name', 'alter', 'modifier'):
            raise AccidentalException(
                'Cannot set attribute {} independently of other parts.'.format(attribute))

        if attribute == 'alter':
            value = float(value)

        privateAttrName = '_' + attribute
        setattr(self, privateAttrName, value)
        if self._client is not None:
            self._client.informClient()

    # --------------------------------------------------------------------------
    def inheritDisplay(self, other):
        '''
        Given another Accidental object, inherit all the display properties
        of that object.

        This is needed when transposing Pitches: we need to retain accidental display properties.


        >>> a = pitch.Accidental('double-flat')
        >>> a.displayType = 'always'
        >>> b = pitch.Accidental('sharp')
        >>> b.inheritDisplay(a)
        >>> b.displayType
        'always'
        '''
        if other is not None:  # empty accidental attributes are None
            for attr in ('displayType', 'displayStatus',
                         'displayStyle', 'displaySize', 'displayLocation'):
                value = getattr(other, attr)
                setattr(self, attr, value)


    # -------------------------------------------------------------------------
    # PUBLIC PROPERTIES #

    @property
    def name(self) -> str:
        '''
        Get or set the name of the Accidental, like 'sharp' or 'double-flat'

        If the name is set to a standard name then it changes alter and modifier.

        If set to a non-standard name, then it does not change them:

        >>> a = pitch.Accidental()
        >>> a.name = 'flat'
        >>> a.alter
        -1.0
        >>> a.modifier
        '-'
        >>> a.name = 'flat-flat-up'
        >>> a.alter
        -1.0

        Changed in v. 5 -- changing the name here changes other values, conditionally
        '''
        return self._name

    @name.setter
    def name(self, value):
        self.set(value, allowNonStandardValue=True)

    @property
    def alter(self) -> float:
        '''
        Get or set the alter of the Accidental,
        or the semitone shift caused by the Accidental where 1.0
        is a shift up of one semitone, and -1.0 is the shift down of
        one semitone.

        >>> sharp = pitch.Accidental('sharp')
        >>> sharp.alter
        1.0

        >>> sharp.alter = -1

        After changing alter to a known other value, name changes:

        >>> sharp.name
        'flat'

        But changing it to an unusual value does not change the name:

        >>> notSoFlat = pitch.Accidental('flat')
        >>> notSoFlat.alter = -0.9
        >>> notSoFlat.name
        'flat'

        Changed in v. 5 -- changing the alter here changes other values, conditionally
        '''
        return self._alter

    @alter.setter
    def alter(self, value):
        # can alternatively call set()
        self.set(value, allowNonStandardValue=True)

    @property
    def modifier(self) -> str:
        '''
        Get or set the alter of the modifier, or the string symbol
        used to modify the pitch name, such as "#" or
        "-" for sharp and flat, respectively.  For a representation
        likely to be read by non-music21 users, see `.unicode`.

        >>> f = pitch.Accidental('flat')
        >>> f.modifier
        '-'
        >>> f.modifier = '#'
        >>> f.name
        'sharp'

        However, an unknown modifier does not change anything but is preserved:

        >>> f.modifier = '&'
        >>> f.modifier
        '&'
        >>> f.name
        'sharp'

        Changed in v. 5 -- changing the modifier here changes
        other values, conditionally
        '''
        return self._modifier

    @modifier.setter
    def modifier(self, value):
        try:
            self.set(value, allowNonStandardValue=False)
        except AccidentalException:
            self._modifier = value


    @property
    def displayType(self) -> str:
        '''
        Returns or sets the display type of the accidental

        "normal" (default) displays it if it is the first in measure,
        or is needed to contradict a previous accidental, etc.

        other valid terms:
        "always", "never", "unless-repeated" (show always unless
        the immediately preceding note is the same), "even-tied"
        (stronger than always: shows even if it is tied to the
        previous note)

        >>> a = pitch.Accidental('flat')
        >>> a.displayType = 'unless-repeated'
        >>> a.displayType
        'unless-repeated'
        >>> a.displayType = 'underwater'
        Traceback (most recent call last):
        music21.pitch.AccidentalException: Supplied display type is not supported: 'underwater'
        '''
        return self._displayType

    @displayType.setter
    def displayType(self, value: str):
        if value not in ('normal', 'always', 'never',
                         'unless-repeated', 'even-tied'):
            raise AccidentalException(f'Supplied display type is not supported: {value!r}')
        self._displayType = value

    @property
    def displayStatus(self):
        '''
        Determines if this Accidental is to be displayed;
        can be None (for not set), True, or False.

        While `.displayType` gives general rules about when this accidental
        should be displayed or not, `displayStatus` determines whether after
        applying those rules this accidental will be displayed.

        In general, a `displayStatus` of `None` means that no high-level
        processing of accidentals has happened.

        Can be set to True or False (or None) directly for contexts where
        the next program down the line cannot evaluate displayType.  See
        stream.makeAccidentals() for more information.

        Example:

        >>> n0 = note.Note('C#4')
        >>> n1 = note.Note('C#4')
        >>> print(n0.pitch.accidental.displayStatus)
        None
        >>> print(n1.pitch.accidental.displayStatus)
        None
        >>> s = stream.Stream()
        >>> s.append([n0, n1])
        >>> s.makeAccidentals(inPlace=True)
        >>> n0.pitch.accidental.displayStatus
        True
        >>> n1.pitch.accidental.displayStatus
        False

        >>> n1.pitch.accidental.displayStatus = 2
        Traceback (most recent call last):
        music21.pitch.AccidentalException: Supplied display status is not supported: 2
        '''
        return self._displayStatus

    @displayStatus.setter
    def displayStatus(self, value):
        if value not in (True, False, None):
            raise AccidentalException(f'Supplied display status is not supported: {value}')
        self._displayStatus = value

    @property
    def unicode(self):
        '''
        Return a unicode representation of this accidental
        or the best unicode representation if that is not possible.

        >>> flat = pitch.Accidental('flat')
        >>> flat.unicode
        '♭'

        Compare:

        >>> sharp = pitch.Accidental('sharp')
        >>> sharp.modifier
        '#'
        >>> sharp.unicode
        '♯'

        Some accidentals, such as double sharps, produce code points outside
        the 2-byte set (so called "astral plane" unicode) and thus cannot be
        used in every circumnstance.

        >>> sharp = pitch.Accidental('quadruple-flat')
        >>> sharp.unicode
        '𝄫𝄫'
        '''
        # all unicode musical symbols can be found here:
        # http://www.fileformat.info/info/unicode/block/musical_symbols/images.htm
        if self.modifier in unicodeFromModifier:
            return unicodeFromModifier[self.modifier]
        else:  # get our best representation  # pragma: no cover
            return self.modifier

    @property
    def fullName(self):
        '''Return the most complete representation of this Accidental.

        >>> a = pitch.Accidental('double-flat')
        >>> a.fullName
        'double-flat'

        Note that non-standard microtone names are converted to standard ones:

        >>> a = pitch.Accidental('quarter-flat')
        >>> a.fullName
        'half-flat'

        For now this is the same as `.name`.
        '''
        # keep lower case
        return self.name



# ------------------------------------------------------------------------------
# tried as SlottedObjectMixin -- made creation time slower! Not worth the restrictions
class Pitch(prebase.ProtoM21Object):
    '''
    A fundamental object that represents a single pitch.

    `Pitch` objects are most often created by passing in a note name
    (C, D, E, F, G, A, B), an optional accidental (one or more "#"s or "-"s,
    where "-" means flat), and an optional octave number:

    >>> highEflat = pitch.Pitch('E-6')
    >>> highEflat.name
    'E-'
    >>> highEflat.step
    'E'
    >>> highEflat.accidental
    <accidental flat>
    >>> highEflat.octave
    6

    The `.nameWithOctave` property gives back what we put in, `'E-6'`:

    >>> highEflat.nameWithOctave
    'E-6'


    `Pitch` objects represent themselves as the class name followed
    by the `.nameWithOctave`:

    >>> p1 = pitch.Pitch('a#4')
    >>> p1
    <music21.pitch.Pitch A#4>

    Printing a `pitch.Pitch` object or converting it
    to a string gives a more compact form:

    >>> print(p1)
    A#4
    >>> str(p1)
    'A#4'

    .. warning:: A `Pitch` without an accidental has a `.accidental` of None,
        not Natural.  This can lead to problems if you assume that every
        `Pitch` or `Note` has a `.accidental` that you can call `.alter`
        or something like that on:

        >>> c = pitch.Pitch('C4')
        >>> c.accidental is None
        True

        >>> alters = []
        >>> for pName in ['G#5', 'B-5', 'C6']:
        ...     p = pitch.Pitch(pName)
        ...     alters.append(p.accidental.alter)
        Traceback (most recent call last):
        AttributeError: 'NoneType' object has no attribute 'alter'
        >>> alters
        [1.0, -1.0]


    If a `Pitch` doesn't have an associated octave, then its
    `.octave` value is None.  This means that it represents
    any G#, regardless of octave.  Transposing this note up
    an octave doesn't change anything.

    >>> anyGSharp = pitch.Pitch('G#')
    >>> anyGSharp.octave is None
    True
    >>> print(anyGSharp.transpose('P8'))
    G#

    Sometimes we need an octave for a `Pitch` even if it's not
    specified.  For instance, we can't play an octave-less `Pitch`
    in MIDI or display it on a staff.  So there is an `.implicitOctave`
    tag to deal with these situations; by default it's always 4.

    >>> anyGSharp.implicitOctave
    4

    If a `Pitch` has its `.octave` explicitly set, then `.implicitOctave`
    always equals `.octave`.

    >>> highEflat.implicitOctave
    6


    If an integer or float >= 12 is passed to the constructor then it is
    used as the `.ps` attribute, which is for most common piano notes, the
    same as a MIDI number:

    >>> pitch.Pitch(65)
    <music21.pitch.Pitch F4>

    >>> pitch.Pitch(65.5).accidental
    <accidental half-sharp>


    A `pitch.Pitch` object can also be created using only a number
    from 0-11, that number is taken to be a `pitchClass`, where
    0 = C, 1 = C#/D-, etc. and no octave is set.

    >>> p2 = pitch.Pitch(3)
    >>> p2
    <music21.pitch.Pitch E->
    >>> p2.octave is None
    True

    Since in instantiating pitches from numbers,
    `pitch.Pitch(3)` could be either a D# or an E-flat,
    this `Pitch` object has an attribute called `.spellingIsInferred` that
    is set to `True`.  That means that when it is transposed or
    displayed, other functions or programs should feel free to substitute an
    enharmonically equivalent pitch in its place:

    >>> p2.spellingIsInferred
    True
    >>> p1.spellingIsInferred
    False

    As MIDI numbers < 12 are almost unheard of in actual music,
    there is unlikely to be confusion between
    a pitchClass instantiation and a MIDI number instantiation, but if one must be
    clear, use `midi=` in the constructor:

    >>> lowE = pitch.Pitch(midi=3)
    >>> lowE.name, lowE.octave
    ('E-', -1)


    Instead of using a single string or integer for creating the object, a succession
    of named keywords can be used instead:

    >>> p3 = pitch.Pitch(name='C', accidental='#', octave=7, microtone=-30)
    >>> p3.fullName
    'C-sharp in octave 7 (-30c)'

    The full list of supported key words are: `name`, `accidental` (which
    can be a string or an :class:`~music21.pitch.Accidental` object), `octave`,
    microtone (which can be a number or a :class:`~music21.pitch.Microtone` object),
    `pitchClass` (0-11), `fundamental` (another `Pitch` object representing the
    fundamental for this harmonic; `harmonic` is not yet supported, but should be),
    and `midi` or `ps` (two ways of specifying nearly the same thing, see below).

    Using keywords to create `Pitch` objects is especially important if
    extreme pitches might be found.  For instance, the first `Pitch` is B-double flat
    in octave 3, not B-flat in octave -3.  The second object creates that low `Pitch`
    properly:

    >>> p4 = pitch.Pitch('B--3')
    >>> p4.accidental
    <accidental double-flat>
    >>> p4.octave
    3

    >>> p5 = pitch.Pitch(step='B', accidental='-', octave=-3)
    >>> p5.accidental
    <accidental flat>
    >>> p5.octave
    -3

    Internally, pitches are represented by their
    scale step (`self.step`), their octave, and their
    accidental. `Pitch` objects use these three elements to figure out their
    pitch space representation (`self.ps`); altering any
    of the first three changes the pitch space (ps) representation.
    Similarly, altering the .ps representation
    alters the first three.

    >>> aSharp = pitch.Pitch('A#5')
    >>> aSharp.ps
    82.0

    >>> aSharp.octave = 4
    >>> aSharp.ps
    70.0

    >>> aSharp.ps = 60.0
    >>> aSharp.nameWithOctave
    'C4'

    Two Pitches are equal if they represent the same
    pitch and are spelled the same (enharmonics do not count).
    A Pitch is greater than another Pitch if its `.ps` is greater than
    the other.  Thus C##4 > D-4.

    >>> pitch.Pitch('C#5') == pitch.Pitch('C#5')
    True
    >>> pitch.Pitch('C#5') == pitch.Pitch('D-5')
    False
    >>> pitch.Pitch('C##5') > pitch.Pitch('D-5')
    True

    A consequence of comparing enharmonics for equality but .ps for comparisons
    is that a `Pitch` can be neither less than
    or greater than another `Pitch` without being equal:

    >>> pitch.Pitch('C#5') == pitch.Pitch('D-5')
    False
    >>> pitch.Pitch('C#5') > pitch.Pitch('D-5')
    False
    >>> pitch.Pitch('C#5') < pitch.Pitch('D-5')
    False

    To check for enharmonic equality, use the .ps attribute:

    >>> pitch.Pitch('C#5').ps == pitch.Pitch('D-5').ps
    True


    Advanced construction of pitch with keywords:

    >>> pitch.Pitch(name='D', accidental=pitch.Accidental('double-flat'))
    <music21.pitch.Pitch D-->
    >>> f = pitch.Pitch(pitchClass=5, octave=4,
    ...                 microtone=pitch.Microtone(30), fundamental=pitch.Pitch('B-2'))
    >>> f
    <music21.pitch.Pitch F4(+30c)>
    >>> f.fundamental
    <music21.pitch.Pitch B-2>

    If contradictory keyword attributes (like `name='E-', accidental='#'`) are passed in,
    behavior is not defined, but unlikely to make you happy.

    Pitches are ProtoM21Objects, so they retain some of the attributes there
    such as .classes and .groups, but they don't have Duration or Sites objects
    and cannot be put into Streams
    '''
    # define order to present names in documentation; use strings
    _DOC_ORDER = ['name', 'nameWithOctave', 'step', 'pitchClass', 'octave', 'midi', 'german',
                  'french', 'spanish', 'italian', 'dutch']
    # documentation for all attributes (not properties or methods)
    # _DOC_ATTR = {
    # }

    # constants shared by all classes
    _twelfth_root_of_two = TWELFTH_ROOT_OF_TWO

    _DOC_ATTR = {
        'spellingIsInferred': '''
            Returns True or False about whether enharmonic spelling
            Has been inferred on pitch creation or whether it has
            been specified directly.

            MIDI 61 is C# or D- equally.

            >>> p = pitch.Pitch('C4')
            >>> p.spellingIsInferred
            False
            >>> p.ps = 61
            >>> p.spellingIsInferred
            True
            >>> p.name
            'C#'
            >>> p.name = 'C#'
            >>> p.spellingIsInferred
            False

            This makes a difference in transposing.  For instance:

            >>> pInferred = pitch.Pitch(61)
            >>> pNotInferred = pitch.Pitch('C#4')
            >>> pInferred.nameWithOctave, pNotInferred.nameWithOctave
            ('C#4', 'C#4')
            >>> pInferred.spellingIsInferred, pNotInferred.spellingIsInferred
            (True, False)

            >>> inferredTransposed = pInferred.transpose('A1')
            >>> inferredTransposed.nameWithOctave
            'D4'
            >>> notInferredTransposed = pNotInferred.transpose('A1')
            >>> notInferredTransposed.nameWithOctave
            'C##4'

            An operation like diatonic transposition should retain the spelling is inferred
            for the resulting object

            >>> inferredTransposed.spellingIsInferred, notInferredTransposed.spellingIsInferred
            (True, False)

            But Chromatic transposition can change an object to inferred spelling:

            >>> p3 = notInferredTransposed.transpose(1)  # C## -> E- not to C###
            >>> p3.nameWithOctave
            'E-4'
            >>> p3.spellingIsInferred
            True
        ''',
    }

    def __init__(self,
                 name: Optional[Union[str, int]] = None,
                 **keywords):
        self._groups = None

        if isinstance(name, type(self)):
            name = name.nameWithOctave

        # super().__init__(**keywords)

        # this should not be set, as will be updated when needed
        self._step = defaults.pitchStep  # this is only the pitch step

        # keep an accidental object based on self._alter
        self._overridden_freq440 = None

        # store an Accidental and Microtone objects
        # note that creating an Accidental object is much more time consuming
        # than a microtone
        self._accidental = None
        self._microtone = None  # 5% of pitch creation time; it'll be created in a sec anyhow

        # CA, Q: should this remain an attribute or only refer to value in defaults?
        # MSC A: no, it's a useful attribute for cases such as scales where if there are
        #        no octaves we give a defaultOctave higher than the previous
        #        (MSC 12 years later: maybe Chris was right...)
        self.defaultOctave = defaults.pitchOctave
        self._octave = None

        # if True, accidental is not known; is determined algorithmically
        # likely due to pitch data from midi or pitch space/class numbers
        self.spellingIsInferred = False
        # the fundamental attribute stores an optional pitch
        # that defines the fundamental used to create this Pitch
        self.fundamental: Optional['Pitch'] = None

        # so that we can tell clients about changes in pitches.
        self._client: Optional['music21.note.Note'] = None

        # name combines step, octave, and accidental
        if name is not None:
            if isinstance(name, str):
                self.name = name  # set based on string
            else:  # is a number
                if name < 12:  # is a pitchClass
                    self.pitchClass = name
                else:  # is a midiNumber
                    self.pitchClass = name
                    self._octave = int(name / 12) - 1

        # override just about everything with keywords
        # necessary for ImmutablePitch objects
        if keywords:
            if 'name' in keywords:
                # noinspection PyArgumentList
                self.name = keywords['name']  # set based on string
            if 'step' in keywords:
                self.step = keywords['step']
            if 'octave' in keywords:
                self._octave = keywords['octave']
            if 'accidental' in keywords:
                if isinstance(keywords['accidental'], Accidental):
                    self.accidental = keywords['accidental']
                else:
                    self.accidental = Accidental(keywords['accidental'])
            if 'microtone' in keywords:
                mt = keywords['microtone']
                if isinstance(mt, Microtone):
                    self.microtone = mt
                else:
                    self.microtone = Microtone(mt)
            if 'pitchClass' in keywords:
                self.pitchClass = keywords['pitchClass']
            if 'fundamental' in keywords:
                self.fundamental = keywords['fundamental']
            if 'midi' in keywords:
                self.midi = keywords['midi']
            if 'ps' in keywords:
                self.ps = keywords['ps']

    def _reprInternal(self):
        return str(self)

    def __str__(self):
        name = self.nameWithOctave
        if self._microtone is not None and self._microtone.cents != 0:
            return name + repr(self._microtone)
        else:
            return name

    def __eq__(self, other):
        '''
        Do not accept enharmonic equivalence.

        >>> a = pitch.Pitch('c2')
        >>> a.octave
        2
        >>> b = pitch.Pitch('c#4')
        >>> b.octave
        4
        >>> a == b
        False
        >>> a != b
        True

        >>> c = 7
        >>> a == c
        False

        >>> a != c
        True

        >>> d = pitch.Pitch('d-4')
        >>> b == d
        False

        '''
        if other is None:
            return False
        elif not isinstance(other, Pitch):
            return False
        elif (self.octave == other.octave
              and self.step == other.step
              and self.accidental == other.accidental
              and self.microtone == other.microtone):
            return True
        else:
            return False

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        '''
        highly optimized -- it knows exactly what can only have a scalar value and
        just sets that directly, only running deepcopy on the other bits.

        And _client should NOT be deepcopied.
        '''
        if type(self) is Pitch:  # pylint: disable=unidiomatic-typecheck
            new = Pitch.__new__(Pitch)
            for k in self.__dict__:
                v = getattr(self, k, None)
                if k in ('_step', '_overridden_freq440', 'defaultOctave',
                         '_octave', 'spellingIsInferred', '_client'):
                    setattr(new, k, v)
                else:
                    setattr(new, k, copy.deepcopy(v, memo))
            return new
        else:  # pragma: no cover
            return common.defaultDeepcopy(self, memo)

    def __hash__(self):
        hashValues = (
            self.accidental,
            self.fundamental,
            self.spellingIsInferred,
            self.microtone,
            self.octave,
            self.step,
            type(self),
        )
        return hash(hashValues)

    def __lt__(self, other) -> bool:
        '''
        Accepts enharmonic equivalence. Based entirely on pitch space
        representation.

        >>> a = pitch.Pitch('c4')
        >>> b = pitch.Pitch('c#4')
        >>> a < b
        True
        '''
        if self.ps < other.ps:
            return True
        else:
            return False

    def __le__(self, other) -> bool:
        '''
        Less than or equal.  Based on the accidentals' alter function.
        Note that to be equal enharmonics must be the same. So two pitches can
        be neither lt or gt and not equal to each other!

        >>> a = pitch.Pitch('d4')
        >>> b = pitch.Pitch('d8')
        >>> c = pitch.Pitch('d4')
        >>> b <= a
        False
        >>> a <= b
        True
        >>> a <= c
        True

        >>> d = pitch.Pitch('c##4')
        >>> c >= d
        False
        >>> c <= d
        False

        Do not rely on this behavior -- it may be changed in a future version
        to create a total ordering.
        '''
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other) -> bool:
        '''
        Accepts enharmonic equivalence. Based entirely on pitch space
        representation.

        >>> a = pitch.Pitch('d4')
        >>> b = pitch.Pitch('d8')
        >>> a > b
        False
        '''
        if self.ps > other.ps:
            return True
        else:
            return False

    def __ge__(self, other) -> bool:
        '''
        Greater than or equal.  Based on the accidentals' alter function.
        Note that to be equal enharmonics must be the same. So two pitches can
        be neither lt or gt and not equal to each other!

        >>> a = pitch.Pitch('d4')
        >>> b = pitch.Pitch('d8')
        >>> c = pitch.Pitch('d4')
        >>> a >= b
        False
        >>> b >= a
        True
        >>> a >= c
        True
        >>> c >= a
        True

        >>> d = pitch.Pitch('c##4')
        >>> c >= d
        False
        >>> c <= d
        False

        Do not rely on this behavior -- it may be changed in a future version
        to create a total ordering.
        '''
        return self.__gt__(other) or self.__eq__(other)

    # --------------------------------------------------------------------------
    @property
    def groups(self) -> base.Groups:
        '''
        Similar to Groups on music21 object, returns or sets a Groups object.
        '''
        if self._groups is None:
            self._groups = base.Groups()
        return self._groups

    @groups.setter
    def groups(self, new: base.Groups):
        self._groups = new

    @property
    def accidental(self) -> Optional[Accidental]:
        '''
        Stores an optional accidental object contained within the
        Pitch object.  This might return None, which is different
        than a natural accidental:

        >>> a = pitch.Pitch('E-')
        >>> a.accidental.alter
        -1.0
        >>> a.accidental.modifier
        '-'

        >>> b = pitch.Pitch('C4')
        >>> b.accidental is None
        True
        >>> b.accidental = pitch.Accidental('natural')
        >>> b.accidental is None
        False
        >>> b.accidental
        <accidental natural>

        Deprecated usage allows setting accidental to
        a number or string.  Will be a warning in v.7 and removed in v.8.

        >>> b = pitch.Pitch('C4')
        >>> b.accidental = 1.5
        >>> print(b)
        C#4(+50c)
        >>> b.accidental = 1.65
        >>> print(b)
        C#~4(+15c)
        >>> b.accidental = 1.95
        >>> print(b)
        C##4(-5c)
        '''
        return self._accidental

    @accidental.setter
    def accidental(self, value: Union[str, int, float, Accidental]):
        if isinstance(value, str):
            self._accidental = Accidental(value)
        elif common.isNum(value):
            # check and add any microtones
            alter, cents = _convertCentsToAlterAndCents(value * 100.0)
            self._accidental = Accidental(alter)
            if abs(cents) > 0.01:
                self.microtone = cents
        else:  # assume an accidental object
            self._accidental = value

        self.informClient()

    @property
    def microtone(self) -> Optional[Microtone]:
        '''
        Returns or sets the microtone object contained within the
        Pitch object. Microtones must be supplied in cents.

        >>> p = pitch.Pitch('E-4')
        >>> p.microtone.cents == 0
        True
        >>> p.ps
        63.0
        >>> p.microtone = 33  # adjustment in cents
        >>> str(p)
        'E-4(+33c)'
        >>> (p.name, p.nameWithOctave)  # these representations are unchanged
        ('E-', 'E-4')
        >>> p.microtone = '(-12c'  # adjustment in cents
        >>> p
        <music21.pitch.Pitch E-4(-12c)>
        >>> p.microtone = pitch.Microtone(-30)
        >>> p
        <music21.pitch.Pitch E-4(-30c)>
        '''
        if self._microtone is None:
            self._microtone = Microtone()
        return self._microtone

    @microtone.setter
    def microtone(self, value):
        if isinstance(value, str) or common.isNum(value):
            self._microtone = Microtone(value)
        elif value is None:  # set to zero
            self._microtone = Microtone(0)
        elif isinstance(value, Microtone):
            self._microtone = value
        else:
            raise PitchException('Cannot get a microtone object from %s' % value)
        # look for microtones of 0 and set-back to None

    def isTwelveTone(self) -> bool:
        '''
        Return True if this Pitch is
        one of the twelve tones available on a piano
        keyboard. Returns False if it instead
        has a non-zero microtonal adjustment or
        has a quarter tone accidental.

        >>> p = pitch.Pitch('g4')
        >>> p.isTwelveTone()
        True
        >>> p.microtone = -20
        >>> p.isTwelveTone()
        False

        >>> p2 = pitch.Pitch('g~4')
        >>> p2.isTwelveTone()
        False
        '''
        if self.accidental is not None:
            if not self.accidental.isTwelveTone():
                return False
        if self._microtone is not None and self.microtone.cents != 0:
            return False
        return True

    def getCentShiftFromMidi(self) -> int:
        '''
        Get cent deviation of this pitch from MIDI pitch.

        >>> p = pitch.Pitch('c~4')
        >>> p.ps
        60.5
        >>> p.midi  # midi values automatically round up at 0.5
        61
        >>> p.getCentShiftFromMidi()
        -50
        >>> p.microtone = -25
        >>> p.ps
        60.25
        >>> p.midi
        60
        >>> p.getCentShiftFromMidi()
        25


        >>> p = pitch.Pitch('c#4')
        >>> p.microtone = -25
        >>> p.ps
        60.75
        >>> p.midi
        61
        >>> p.getCentShiftFromMidi()
        -25

        >>> p = pitch.Pitch('c#~4')
        >>> p.ps
        61.5
        >>> p.midi
        62
        >>> p.getCentShiftFromMidi()
        -50
        >>> p.microtone = -3
        >>> p.ps
        61.47
        >>> p.midi
        61
        >>> p.getCentShiftFromMidi()
        47
        >>> p.microtone = 3
        >>> p.ps
        61.53
        >>> p.midi
        62
        >>> p.accidental
        <accidental one-and-a-half-sharp>
        >>> p.getCentShiftFromMidi()
        -47

        >>> p = pitch.Pitch('c`4')  # quarter tone flat
        >>> p.getCentShiftFromMidi()
        -50
        >>> p.microtone = 3
        >>> p.getCentShiftFromMidi()
        -47

        Absurd octaves that MIDI can't handle will still give the right sounding pitch
        out of octave:

        >>> p = pitch.Pitch('c~4')
        >>> p.octave = 10
        >>> p.ps
        132.5
        >>> p.midi
        121
        >>> p.getCentShiftFromMidi()
        -50
        >>> p.octave = -1
        >>> p.getCentShiftFromMidi()
        -50
        >>> p.octave = -2
        >>> p.getCentShiftFromMidi()
        -50
        '''
        midiDistance = self.ps - self.midi

        # correct for absurd octaves
        while midiDistance < -11.0:
            midiDistance += 12.0
        while midiDistance > 11.0:
            midiDistance -= 12.0

        return round(midiDistance * 100)

    @property
    def alter(self) -> float:
        '''
        Get or set the number of half-steps shifted
        by this pitch, such as 1.0 for a sharp, -1.0 for a flat,
        0.0 for a natural, 2.0 for a double sharp, and
        and -0.5 for a quarter tone flat.

        Thus, the alter value combines the pitch change
        suggested by the Accidental and the Microtone combined.

        >>> p = pitch.Pitch('g#4')
        >>> p.alter
        1.0
        >>> p.microtone = -25  # in cents
        >>> p.alter
        0.75
        '''
        post = 0.0
        if self.accidental is not None:
            post += self.accidental.alter
        if self._microtone is not None:
            post += self.microtone.alter
        return post

    def convertQuarterTonesToMicrotones(self, *, inPlace=False):
        '''
        Convert any quarter tone Accidentals to Microtones.

        tilde is the symbol for half-sharp, so G#~ is G three-quarters sharp.

        >>> p = pitch.Pitch('G#~')
        >>> str(p), p.microtone
        ('G#~', (+0c))
        >>> p.convertQuarterTonesToMicrotones(inPlace=True)
        >>> p.ps
        68.5
        >>> str(p), p.microtone
        ('G#(+50c)', (+50c))

        >>> p = pitch.Pitch('A')
        >>> p.accidental = pitch.Accidental('half-flat')  # back-tick
        >>> str(p), p.microtone
        ('A`', (+0c))
        >>> x = p.convertQuarterTonesToMicrotones(inPlace=False)
        >>> str(x), x.microtone
        ('A(-50c)', (-50c))
        >>> str(p), p.microtone
        ('A`', (+0c))
        '''
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        if returnObj.accidental is not None:
            if returnObj.accidental.name == 'half-flat':
                returnObj.accidental = None
                returnObj.microtone = returnObj.microtone.cents - 50  # in cents

            elif returnObj.accidental.name == 'half-sharp':
                returnObj.accidental = None
                returnObj.microtone = returnObj.microtone.cents + 50  # in cents

            elif returnObj.accidental.name == 'one-and-a-half-sharp':
                returnObj.accidental = 1.0
                returnObj.microtone = returnObj.microtone.cents + 50  # in cents

            elif returnObj.accidental.name == 'one-and-a-half-flat':
                returnObj.accidental = -1.0
                returnObj.microtone = returnObj.microtone.cents - 50  # in cents

        if not inPlace:
            return returnObj

    def convertMicrotonesToQuarterTones(self, *, inPlace=False):
        '''
        Convert any Microtones available to quarter tones, if possible.

        >>> p = pitch.Pitch('g3')
        >>> p.microtone = 78
        >>> str(p)
        'G3(+78c)'
        >>> p.convertMicrotonesToQuarterTones(inPlace=True)
        >>> str(p)
        'G#3(-22c)'

        >>> p = pitch.Pitch('d#3')
        >>> p.microtone = 46
        >>> p
        <music21.pitch.Pitch D#3(+46c)>
        >>> p.convertMicrotonesToQuarterTones(inPlace=True)
        >>> p
        <music21.pitch.Pitch D#~3(-4c)>

        >>> p = pitch.Pitch('f#2')
        >>> p.microtone = -38
        >>> p.convertMicrotonesToQuarterTones(inPlace=True)
        >>> str(p)
        'F~2(+12c)'

        '''
        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        value = returnObj.microtone.cents
        alterShift, cents = _convertCentsToAlterAndCents(value)

        if returnObj.accidental is not None:
            returnObj.accidental = Accidental(
                returnObj.accidental.alter + alterShift)
        else:
            returnObj.accidental = Accidental(alterShift)
        returnObj.microtone = cents

        if not inPlace:
            return returnObj

    # --------------------------------------------------------------------------

    @property
    def ps(self):
        '''
        The ps property permits getting and setting
        a pitch space value, a floating point number
        representing pitch space, where 60.0 is C4, middle C,
        61.0 is C#4 or D-4, and floating point values are
        microtonal tunings (0.01 is equal to one cent), so
        a quarter-tone sharp above C5 is 72.5.

        Note that the choice of 60.0 for C4 makes it identical
        to the integer value of 60 for .midi, but .midi
        does not allow for microtones and is limited to 0-127
        while .ps allows for notes before midi 0 or above midi 127.

        >>> a = pitch.Pitch('C4')
        >>> a.ps
        60.0

        Changing the ps value for `a` will change the step and octave:

        >>> a.ps = 45
        >>> a
        <music21.pitch.Pitch A2>
        >>> a.ps
        45.0


        Notice that ps 61 represents both
        C# and D-flat.  Thus "spellingIsInferred"
        will be true after setting our pitch to 61:

        >>> a.ps = 61
        >>> a
        <music21.pitch.Pitch C#4>
        >>> a.ps
        61.0
        >>> a.spellingIsInferred
        True

        Microtonal accidentals and pure Microtones are allowed, as are extreme ranges:

        >>> b = pitch.Pitch('B9')
        >>> b.accidental = pitch.Accidental('half-flat')
        >>> b
        <music21.pitch.Pitch B`9>
        >>> b.ps
        130.5

        >>> p = pitch.Pitch('c4')
        >>> p.microtone = 20
        >>> print('%.1f' % p.ps)
        60.2

        Octaveless pitches use their .implicitOctave attributes:

        >>> d = pitch.Pitch('D#')
        >>> d.octave is None
        True
        >>> d.implicitOctave
        4
        >>> d.ps
        63.0

        >>> d.defaultOctave = 5
        >>> d.ps
        75.0

        Setting with microtones

        >>> p = pitch.Pitch()
        >>> p.ps = 61
        >>> p.ps
        61.0
        >>> p.spellingIsInferred
        True
        >>> p.ps = 61.5  # get a quarter tone
        >>> p
        <music21.pitch.Pitch C#~4>
        >>> p.ps = 61.7  # set a microtone
        >>> print(p)
        C#~4(+20c)
        >>> p.ps = 61.4  # set a microtone
        >>> print(p)
        C#~4(-10c)

        The property is called when self.step, self.octave
        or self.accidental are changed.

        Should be called when .defaultOctave is changed if octave is None,
        but isn't yet.
        '''
        step = self._step
        ps = float(((self.implicitOctave + 1) * 12) + STEPREF[step])
        if self.accidental is not None:
            ps = ps + self.accidental.alter
        if self._microtone is not None:
            ps = ps + self.microtone.alter
        return ps

    @ps.setter
    def ps(self, value):
        # can assign microtone here; will be either None or a Microtone object
        self.step, acc, self._microtone, octShift = _convertPsToStep(value)
        # replace a natural with a None
        if acc.name == 'natural':
            self.accidental = None
        else:
            self.accidental = acc
        self.octave = _convertPsToOct(value) + octShift

        # all ps settings must set implicit to True, as we do not know
        # what accidental this is
        self.spellingIsInferred = True

    @property
    def midi(self):
        '''
        Get or set a pitch value in MIDI.
        MIDI pitch values are like ps values (pitchSpace) rounded to
        the nearest integer; while the ps attribute will accommodate floats.

        >>> c = pitch.Pitch('C4')
        >>> c.midi
        60
        >>> c.midi =  23.5
        >>> c.midi
        24

        Note that like ps (pitchSpace), MIDI notes do not distinguish between
        sharps and flats, etc.

        >>> dSharp = pitch.Pitch('D#4')
        >>> dSharp.midi
        63
        >>> eFlat = pitch.Pitch('E-4')
        >>> eFlat.midi
        63

        Midi values are constrained to the space 0-127.  Higher or lower
        values will be transposed octaves to fit in this space.

        >>> veryHighFHalfFlat = pitch.Pitch('F')
        >>> veryHighFHalfFlat.octave = 12
        >>> veryHighFHalfFlat.accidental = pitch.Accidental('half-flat')
        >>> veryHighFHalfFlat
        <music21.pitch.Pitch F`12>
        >>> veryHighFHalfFlat.ps
        160.5
        >>> veryHighFHalfFlat.midi
        125
        >>> veryHighFHalfFlat.octave = 9
        >>> veryHighFHalfFlat.midi
        125

        >>> notAsHighNote = pitch.Pitch()
        >>> notAsHighNote.ps = veryHighFHalfFlat.midi
        >>> notAsHighNote
        <music21.pitch.Pitch F9>

        Note that the conversion of improper midi values to proper
        midi values is done before assigning .ps:

        >>> a = pitch.Pitch()
        >>> a.midi = -10
        >>> a.midi
        2
        >>> a.ps
        2.0
        >>> a.spellingIsInferred
        True

        More absurd octaves...

        >>> p = pitch.Pitch('c~4')
        >>> p.octave = -1
        >>> p.ps
        0.5
        >>> p.midi
        1
        >>> p.octave = -2
        >>> p.ps
        -11.5
        >>> p.midi
        1
        '''
        def schoolYardRounding(x):
            '''
            This is round "up" at 0.5 (regardless of negative or positive)

            Python 3 now uses rounding mechanisms so that odd numbers round one way, even another.
            But we needed a consistent direction for all half-sharps/flats to go,
            and now long after Python 2 is no longer supported, this behavior is grandfathered in.
            '''
            return math.floor(x + 0.5)

        roundedPS = schoolYardRounding(self.ps)
        if roundedPS > 127:
            value = (12 * 9) + (roundedPS % 12)
            if value < (127 - 12):
                value += 12
        elif roundedPS < 0:
            value = 0 + (roundedPS % 12)
        else:
            value = roundedPS
        return value

    @midi.setter
    def midi(self, value):
        '''
        midi values are constrained within the range of 0 to 127
        floating point values,
        '''
        value = round(value)
        if value > 127:
            value = (12 * 9) + (value % 12)  # highest oct plus modulus
            if value < (127 - 12):
                value += 12
        elif value < 0:
            value = 0 + (value % 12)  # lowest oct plus modulus
        self.ps = value

        # all midi settings must set implicit to True, as we do not know
        # what accidental this is
        self.spellingIsInferred = True

    @property
    def name(self) -> str:
        '''
        Gets or sets the name (pitch name with accidental but
        without octave) of the Pitch.

        >>> p = pitch.Pitch('D#5')
        >>> p.name
        'D#'

        >>> p.name = 'C#'
        >>> p.name
        'C#'

        >>> a = pitch.Pitch('G#')
        >>> a.name
        'G#'

        Does not simplify enharmonics

        >>> a = pitch.Pitch('B---')
        >>> a.name
        'B---'
        '''
        if self.accidental is not None:
            return self.step + self.accidental.modifier
        else:
            return self.step

    @name.setter
    def name(self, usrStr: str):
        '''
        Set name, which may be provided with or without octave values. C4 or D-3
        are both accepted.
        '''
        usrStr = usrStr.strip()
        # extract any numbers that may be octave designations
        octFound = []
        octNot = []

        for char in usrStr:
            if char in '0123456789':
                octFound.append(char)
            else:
                octNot.append(char)
        usrStr = ''.join(octNot)
        octFound = ''.join(octFound)
        # we have nothing but pitch specification
        if len(usrStr) == 1:
            self.step = usrStr
            self.accidental = None
        # assume everything following pitch is accidental specification
        elif len(usrStr) > 1:
            self.step = usrStr[0]
            self.accidental = Accidental(usrStr[1:])
        else:
            raise PitchException('Cannot make a name out of %s' % repr(usrStr))

        if octFound:  # bool('0') == True, so okay...
            octave = int(octFound)
            self.octave = octave

    @property
    def unicodeName(self) -> str:
        '''Name presently returns pitch name and accidental without octave.

        >>> a = pitch.Pitch('G#')
        >>> a.unicodeName
        'G♯'
        '''
        if self.accidental is not None:
            return self.step + self.accidental.unicode
        else:
            return self.step

    @property
    def nameWithOctave(self) -> str:
        '''
        Return or set the pitch name with an octave designation.
        If no octave as been set, no octave value is returned.


        >>> gSharp = pitch.Pitch('G#4')
        >>> gSharp.nameWithOctave
        'G#4'

        >>> dFlatFive = pitch.Pitch()
        >>> dFlatFive.step = 'D'
        >>> dFlatFive.accidental = pitch.Accidental('flat')
        >>> dFlatFive.octave = 5
        >>> dFlatFive.nameWithOctave
        'D-5'
        >>> dFlatFive.nameWithOctave = 'C#6'
        >>> dFlatFive.name
        'C#'
        >>> dFlatFive.octave
        6


        N.B. -- it's generally better to set the name and octave separately, especially
        since you may at some point encounter very low pitches such as "A octave -1", which
        will be interpreted as "A-flat, octave 1".  Our crude setting algorithm also does
        not support octaves above 9.

        >>> lowA = pitch.Pitch()
        >>> lowA.name = 'A'
        >>> lowA.octave = -1
        >>> lowA.nameWithOctave
        'A-1'
        >>> lowA.nameWithOctave = lowA.nameWithOctave
        >>> lowA.name
        'A-'
        >>> lowA.octave
        1

        Octave must be included in nameWithOctave or an exception is raised:

        >>> a = pitch.Pitch()
        >>> a.nameWithOctave = 'C#9'
        >>> a.nameWithOctave = 'C#'
        Traceback (most recent call last):
        music21.pitch.PitchException: Cannot set a nameWithOctave with 'C#'

        Set octave to None explicitly instead.
        '''
        if self.octave is None:
            return self.name
        else:
            return self.name + str(self.octave)

    @nameWithOctave.setter
    def nameWithOctave(self, value: str):
        try:
            lenVal = len(value)
            name = value[0:lenVal - 1]
            octave = int(value[-1])
            self.name = name
            self.octave = octave
        except:
            raise PitchException("Cannot set a nameWithOctave with '%s'" % value)

    @property
    def unicodeNameWithOctave(self) -> str:
        '''
        Return the pitch name with octave with unicode accidental symbols,
        if available.

        Read-only property.

        >>> p = pitch.Pitch('C#4')
        >>> p.unicodeNameWithOctave
        'C♯4'
        '''
        if self.octave is None:
            return self.unicodeName
        else:
            return self.unicodeName + str(self.octave)

    @property
    def fullName(self):
        '''
        Return the most complete representation of this Pitch,
        providing name, octave, accidental, and any
        microtonal adjustments.

        >>> p = pitch.Pitch('A-3')
        >>> p.microtone = 33.33
        >>> p.fullName
        'A-flat in octave 3 (+33c)'

        >>> p = pitch.Pitch('A`7')
        >>> p.fullName
        'A-half-flat in octave 7'
        '''
        name = '%s' % self._step

        if self.accidental is not None:
            name += '-%s' % self.accidental.fullName

        if self.octave is not None:
            name += ' in octave %s' % self.octave

        if self._microtone is not None and self.microtone.cents != 0:
            name += ' ' + repr(self._microtone)

        return name

    @property
    def step(self) -> str:
        '''
        The diatonic name of the note; i.e. does not give the
        accidental or octave.

        >>> a = pitch.Pitch('B-3')
        >>> a.step
        'B'

        Upper-case or lower-case names can be given to `.step` -- they
        will be converted to upper-case

        >>> b = pitch.Pitch()
        >>> b.step = 'c'
        >>> b.step
        'C'

        Changing the `.step` does not change the `.accidental` or
        `.octave`:

        >>> a = pitch.Pitch('F#5')
        >>> a.step = 'D'
        >>> a.nameWithOctave
        'D#5'

        Giving a value that includes an accidental raises a PitchException.
        Use .name instead to change that.

        >>> b = pitch.Pitch('E4')
        >>> b.step = 'B-'
        Traceback (most recent call last):
        music21.pitch.PitchException: Cannot make a step out of 'B-'

        This is okay though:

        >>> b.name = 'B-'

        Note that if spelling is inferred, setting the step does NOT
        give that enharmonic.  Perhaps it should, but best to make people use
        .getLowerEnharmonic or .getHigherEnharmonic instead.

        >>> b.ps = 60
        >>> b.nameWithOctave
        'C4'
        >>> b.spellingIsInferred
        True
        >>> b.step = 'B'
        >>> b.accidental is None  # maybe this should set to B#? But that could be screwy.
        True
        >>> b.spellingIsInferred
        False
        '''
        return self._step

    @step.setter
    def step(self, usrStr: str) -> None:
        '''
        This does not change octave or accidental, only step
        '''
        usrStr = usrStr.strip().upper()
        if len(usrStr) == 1 and usrStr in STEPNAMES:
            self._step = usrStr
            # when setting by step, we assume that the accidental intended
            self.spellingIsInferred = False
        else:
            raise PitchException("Cannot make a step out of '%s'" % usrStr)

    @property
    def pitchClass(self) -> int:
        '''
        Returns or sets the integer value for the pitch, 0-11, where C=0,
        C#=1, D=2...B=11. Can be set using integers (0-11) or 'A' or 'B'
        for 10 or 11.

        >>> a = pitch.Pitch('a3')
        >>> a.pitchClass
        9
        >>> dis = pitch.Pitch('d3')
        >>> dis.pitchClass
        2
        >>> dis.accidental = pitch.Accidental('#')
        >>> dis.pitchClass
        3

        If a string "A" or "B" is given to pitchClass, it is
        still returned as an int.

        >>> dis.pitchClass = 'A'
        >>> dis.pitchClass
        10
        >>> dis.name
        'B-'

        Extreme octaves will not affect pitchClass

        >>> dis.octave = -10
        >>> dis.pitchClass
        10

        In the past, certain microtones and/or octaves were returning pc 12!
        This is now fixed.

        >>> flattedC = pitch.Pitch('C4')
        >>> flattedC.microtone = -4
        >>> print(flattedC)
        C4(-4c)
        >>> flattedC.pitchClass
        0
        >>> print(flattedC.ps)
        59.96
        >>> flattedC.octave = -3
        >>> print(flattedC.ps)
        -24.04
        >>> flattedC.pitchClass
        0

        Note that the pitchClass of a microtonally altered pitch is the pitch class of
        the nearest pitch.  Python 3 uses the "round-to-even" method so C~4 (C half sharp 4)
        is pitchClass 0, since 60.5 rounds to 60.0

        >>> p = pitch.Pitch('C~4')
        >>> p.ps
        60.5
        >>> p.pitchClass
        0

        However, for backwards compatability, the MIDI number of a microtone
        is created by using "schoolyard" rounding which always rounds 0.5 upwards, which
        can cause some unusual behavior:

        >>> p.midi
        61
        >>> pitch.Pitch(midi=p.midi).pitchClass
        1


        This means that pitchClass + microtone is NOT a good way to estimate the frequency
        of a pitch.  For instance, if we take a pitch that is 90% of the way between pitchClass
        0 (C) and pitchClass 1 (C#/D-flat), this formula gives an inaccurate answer of 1.9, not
        0.9:

        >>> p = pitch.Pitch('C4')
        >>> p.microtone = 90
        >>> p
        <music21.pitch.Pitch C4(+90c)>
        >>> p.pitchClass + (p.microtone.cents / 100.0)
        1.9

        More examples of setting the pitchClass.

        >>> a = pitch.Pitch('a3')
        >>> a.pitchClass = 3
        >>> a
        <music21.pitch.Pitch E-3>
        >>> a.spellingIsInferred
        True
        >>> a.pitchClass = 'A'
        >>> a
        <music21.pitch.Pitch B-3>

        Changing pitchClass does not remove microtones.

        >>> a.microtone = 20
        >>> a.pitchClass = 1
        >>> a
        <music21.pitch.Pitch C#3(+20c)>
        '''
        pc = round(self.ps) % 12
        if pc == 12:
            pc = 0
        return pc

    @pitchClass.setter
    def pitchClass(self, value: Union[str, int]):
        # permit the submission of strings, like A an dB
        value = _convertPitchClassToNumber(value)
        # get step and accidental w/o octave
        (self._step, self._accidental, unused_microtone, unused_octShift) = _convertPsToStep(value)

        # do not know what accidental is
        self.spellingIsInferred = True

    @property
    def pitchClassString(self) -> str:
        '''
        Returns or sets a string representation of the pitch class,
        where integers greater than 10 are replaced by A and B,
        respectively. Can be used to set pitch class by a
        string representation as well (though this is also
        possible with :attr:`~music21.pitch.Pitch.pitchClass`.

        >>> a = pitch.Pitch('a#3')
        >>> a.pitchClass
        10
        >>> a.pitchClassString
        'A'

        We can set the pitchClassString as well:

        >>> a.pitchClassString = 'B'
        >>> a.pitchClass
        11
        '''
        return convertPitchClassToStr(self.pitchClass)

    @pitchClassString.setter
    def pitchClassString(self, v):
        self.pitchClass = v


    @property
    def octave(self) -> Optional[int]:
        '''
        Returns or sets the octave of the note.
        Setting the octave updates the pitchSpace attribute.

        >>> a = pitch.Pitch('g')
        >>> a.octave is None
        True
        >>> a.implicitOctave
        4
        >>> a.ps  ## will use implicitOctave
        67.0
        >>> a.name
        'G'

        >>> a.octave = 14
        >>> a.octave
        14
        >>> a.implicitOctave
        14
        >>> a.name
        'G'
        >>> a.ps
        187.0
        '''
        return self._octave

    @octave.setter
    def octave(self, value: Optional[Union[int, float]]):
        if value is not None:
            self._octave = int(value)
        else:
            self._octave = None

    @property
    def implicitOctave(self) -> int:
        '''
        Returns the octave of the Pitch, or defaultOctave if
        octave was never set. To set an octave, use .octave.
        Default octave is usually 4.

        >>> p = pitch.Pitch('C#')
        >>> p.octave is None
        True
        >>> p.implicitOctave
        4

        Cannot be set.  Instead just change the `.octave` of the pitch
        '''
        if self.octave is None:
            return self.defaultOctave
        else:
            return self.octave

    # noinspection SpellCheckingInspection
    @property
    def german(self) -> str:
        '''
        Read-only property. Returns a unicode string of the name
        of a Pitch in the German system
        (where B-flat = B, B = H, etc.)
        (Microtones and Quarter tones raise an error).  Note that
        Ases is used instead of the also acceptable Asas.

        >>> print(pitch.Pitch('B-').german)
        B
        >>> print(pitch.Pitch('B').german)
        H
        >>> print(pitch.Pitch('E-').german)
        Es
        >>> print(pitch.Pitch('C#').german)
        Cis
        >>> print(pitch.Pitch('A--').german)
        Ases
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.german
        Traceback (most recent call last):
        music21.pitch.PitchException:
            Es geht nicht "german" zu benutzen mit Microt...nen.  Schade!

        Note these rarely used pitches:

        >>> print(pitch.Pitch('B--').german)
        Heses
        >>> print(pitch.Pitch('B#').german)
        His
        '''
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        if tempAlter != int(tempAlter):
            raise PitchException('Es geht nicht "german" zu benutzen mit Microtönen.  Schade!')

        tempAlter = int(tempAlter)
        if tempStep == 'B':
            if tempAlter != -1:
                tempStep = 'H'
            else:
                tempAlter += 1
        if tempAlter == 0:
            return tempStep
        elif tempAlter > 0:
            tempName = tempStep + (tempAlter * 'is')
            return tempName
        else:  # flats
            if tempStep in ('C', 'D', 'F', 'G', 'H'):
                firstFlatName = 'es'
            else:  # A, E.  Bs should never occur...
                firstFlatName = u's'
            multipleFlats = abs(tempAlter) - 1
            tempName = tempStep + firstFlatName + (multipleFlats * 'es')
            return tempName

    # noinspection SpellCheckingInspection
    @property
    def italian(self) -> str:
        # noinspection SpellCheckingInspection
        '''
        Read-only attribute. Returns the name
        of a Pitch in the Italian system
        (F-sharp is fa diesis, C-flat is do bemolle, etc.)
        (Microtones and Quarter tones raise an error).


        >>> print(pitch.Pitch('B-').italian)
        si bemolle
        >>> print(pitch.Pitch('B').italian)
        si
        >>> print(pitch.Pitch('E-9').italian)
        mi bemolle
        >>> print(pitch.Pitch('C#').italian)
        do diesis
        >>> print(pitch.Pitch('A--4').italian)
        la doppio bemolle
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.italian
        Traceback (most recent call last):
        music21.pitch.PitchException: Non si puo usare `italian` con microtoni

        Note these rarely used pitches:

        >>> print(pitch.Pitch('E####').italian)
        mi quadruplo diesis
        >>> print(pitch.Pitch('D---').italian)
        re triplo bemolle
        '''
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step
        if tempAlter != int(tempAlter):
            raise PitchException('Non si puo usare `italian` con microtoni')

        tempAlter = int(tempAlter)

        cardinalityMap = {1: ' ', 2: ' doppio ', 3: ' triplo ', 4: ' quadruplo '}
        solfeggeMap = {'C': 'do', 'D': 're', 'E': 'mi', 'F': 'fa',
                       'G': 'sol', 'A': 'la', 'B': 'si'}

        if tempAlter == 0:
            return solfeggeMap[tempStep]
        elif tempAlter > 0:
            if tempAlter > 4:
                raise PitchException('Entirely too many sharps')
            return solfeggeMap[tempStep] + cardinalityMap[tempAlter] + 'diesis'
        else:  # flats
            tempAlter = tempAlter * -1
            if tempAlter > 4:
                raise PitchException('Entirely too many flats')
            return solfeggeMap[tempStep] + cardinalityMap[tempAlter] + 'bemolle'

    def _getSpanishCardinal(self) -> str:
        if self.accidental is None:
            return ''
        else:
            i = abs(self.accidental.alter)
            # already checked for microtones, etc.
            if i == 1:
                return ''
            elif i == 2:
                return ' doble'
            elif i == 3:
                return ' triple'
            elif i == 4:
                return ' cuádruple'

    def _getSpanishSolfege(self) -> str:
        p = self.step
        if p == 'A':
            return 'la'
        if p == 'B':
            return 'si'
        if p == 'C':
            return 'do'
        if p == 'D':
            return 're'
        if p == 'E':
            return 'mi'
        if p == 'F':
            return 'fa'
        if p == 'G':
            return 'sol'

    # noinspection SpellCheckingInspection
    @property
    def spanish(self) -> str:
        '''
        Read-only attribute. Returns the name
        of a Pitch in Spanish
        (Microtones and Quarter tones raise an error).

        >>> print(pitch.Pitch('B-').spanish)
        si bèmol
        >>> print(pitch.Pitch('E-').spanish)
        mi bèmol
        >>> print(pitch.Pitch('C#').spanish)
        do sostenido
        >>> print(pitch.Pitch('A--').spanish)
        la doble bèmol
        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.spanish
        Traceback (most recent call last):
        music21.pitch.PitchException: Unsupported accidental type.

        Note these rarely used pitches:

        >>> print(pitch.Pitch('B--').spanish)
        si doble bèmol
        >>> print(pitch.Pitch('B#').spanish)
        si sostenido
        '''
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        solfege = self._getSpanishSolfege()
        if tempAlter != int(tempAlter):
            raise PitchException('Unsupported accidental type.')

        if tempAlter == 0:
            return solfege
        elif abs(tempAlter) > 4:
            raise PitchException('Unsupported accidental type.')
        elif tempAlter in {-4, -3, -2, -1}:
            return solfege + self._getSpanishCardinal() + ' bèmol'
        elif tempAlter in {1, 2, 3, 4}:
            return solfege + self._getSpanishCardinal() + ' sostenido'

    # noinspection SpellCheckingInspection
    @property
    def french(self) -> str:
        '''
        Read-only attribute. Returns the name
        of a Pitch in the French system
        (where A = la, B = si, B-flat = si bémol, C-sharp = do dièse, etc.)
        (Microtones and Quarter tones raise an error).  Note that
        do is used instead of the also acceptable ut.

        >>> print(pitch.Pitch('B-').french)
        si bémol

        >>> print(pitch.Pitch('B').french)
        si

        >>> print(pitch.Pitch('E-').french)
        mi bémol

        >>> print(pitch.Pitch('C#').french)
        do dièse

        >>> print(pitch.Pitch('A--').french)
        la double bémol

        >>> p1 = pitch.Pitch('C')
        >>> p1.accidental = pitch.Accidental('half-sharp')
        >>> p1.french
        Traceback (most recent call last):
        music21.pitch.PitchException: On ne peut pas utiliser les microtones avec "french."
            Quelle Dommage!
        '''
        if self.accidental is not None:
            tempAlter = self.accidental.alter
        else:
            tempAlter = 0
        tempStep = self.step

        if tempAlter != int(tempAlter):
            raise PitchException(
                'On ne peut pas utiliser les microtones avec "french." Quelle Dommage!')

        if abs(tempAlter) > 4.0:
            raise PitchException(
                'On ne peut pas utiliser les altération avec puissance supérieure à quatre '
                + 'avec "french." Ça me fait une belle jambe!'
            )
        tempAlter = int(tempAlter)

        if tempStep == 'A':
            tempStep = 'la'
        if tempStep == 'B':
            tempStep = 'si'
        if tempStep == 'C':
            tempStep = 'do'
        if tempStep == 'D':
            tempStep = 'ré'
        if tempStep == 'E':
            tempStep = 'mi'
        if tempStep == 'F':
            tempStep = 'fa'
        if tempStep == 'G':
            tempStep = 'sol'

        if tempAlter == 0:
            return tempStep
        elif abs(tempAlter) == 1.0:
            tempNumberedStep = tempStep
        elif abs(tempAlter) == 2.0:
            tempNumberedStep = tempStep + ' double'
        elif abs(tempAlter) == 3.0:
            tempNumberedStep = tempStep + ' triple'
        elif abs(tempAlter) == 4.0:
            tempNumberedStep = tempStep + ' quadruple'
        else:
            raise PitchException('Cannot deal with tempStep: %s' % tempStep)

        if tempAlter / abs(tempAlter) == 1.0:  # sharps are positive
            tempName = tempNumberedStep + ' dièse'
            return tempName
        else:  # flats are negative
            tempName = tempNumberedStep + ' bémol'
            return tempName

    @property
    def frequency(self) -> float:
        '''
        The frequency property gets or sets the frequency of
        the pitch in hertz.

        If the frequency has not been overridden, then
        it is computed based on A440Hz and equal temperament

        >>> a = pitch.Pitch()
        >>> a.frequency = 440.0
        >>> a.frequency
        440.0
        >>> a.name
        'A'
        >>> a.octave
        4

        Microtones are captured if the frequency doesn't correspond to any standard note.

        >>> a.frequency = 450.0
        >>> a
        <music21.pitch.Pitch A~4(-11c)>
        '''
        return self.freq440

    @frequency.setter
    def frequency(self, value: Union[int, float]):
        self.freq440 = value

    # these methods may belong in in a temperament object
    # name of method and property could be more clear

    @property
    def freq440(self) -> float:
        '''
        Gets the frequency of the note as if it's in an equal temperament
        context where A4 = 440hz.  The same as .frequency so long
        as no other temperaments are currently being used.

        Since we don't have any other temperament objects at present,
        this is the same as .frequency always.

        >>> a = pitch.Pitch('A4')
        >>> a.freq440
        440.0
        '''
        if self._overridden_freq440:
            return self._overridden_freq440
        else:
            # works off of .ps values and thus will capture microtones
            A4offset = self.ps - 69
            return 440.0 * (self._twelfth_root_of_two ** A4offset)

    @freq440.setter
    def freq440(self, value: Union[int, float]):
        post = 12 * (math.log(value / 440.0) / math.log(2)) + 69
        # environLocal.printDebug(['convertFqToPs():', 'input', fq, 'output', repr(post)])
        # rounding here is essential
        p2 = round(post, PITCH_SPACE_SIG_DIGITS)

        self.ps = p2

    # --------------------------------------------------------------------------
    def getHarmonic(self, number):
        '''
        Return a Pitch object representing the harmonic found above this Pitch.

        >>> p = pitch.Pitch('a4')
        >>> print(p.getHarmonic(2))
        A5
        >>> print(p.getHarmonic(3))
        E6(+2c)
        >>> print(p.getHarmonic(4))
        A6
        >>> print(p.getHarmonic(5))
        C#7(-14c)
        >>> print(p.getHarmonic(6))
        E7(+2c)
        >>> print(p.getHarmonic(7))
        F#~7(+19c)
        >>> print(p.getHarmonic(8))
        A7

        >>> p2 = p.getHarmonic(2)
        >>> p2
        <music21.pitch.Pitch A5>
        >>> p2.fundamental
        <music21.pitch.Pitch A4>
        >>> p2.transpose('p5', inPlace=True)
        >>> p2
        <music21.pitch.Pitch E6>
        >>> p2.fundamental
        <music21.pitch.Pitch E5>

        Or we can iterate over a list of the next 8 odd harmonics:

        >>> allHarmonics = ''
        >>> for i in [9, 11, 13, 15, 17, 19, 21, 23]:
        ...     allHarmonics += ' ' + str(p.getHarmonic(i))
        >>> print(allHarmonics)
        B7(+4c) D~8(+1c) F~8(-9c) G#8(-12c) B-8(+5c) C9(-2c) C#~9(+21c) E`9(-22c)

        Microtonally adjusted notes also generate harmonics:

        >>> q = pitch.Pitch('C4')
        >>> q.microtone = 10
        >>> q.getHarmonic(2)
        <music21.pitch.Pitch C5(+10c)>
        >>> q.getHarmonic(3)
        <music21.pitch.Pitch G5(+12c)>

        The fundamental is stored with the harmonic.

        >>> h7 = pitch.Pitch('A4').getHarmonic(7)
        >>> print(h7)
        F#~7(+19c)
        >>> h7.fundamental
        <music21.pitch.Pitch A4>
        >>> h7.harmonicString()
        '7thH/A4'
        >>> h7.harmonicString('A3')
        '14thH/A3'

        >>> h2 = h7.getHarmonic(2)
        >>> h2
        <music21.pitch.Pitch F#~8(+19c)>
        >>> h2.fundamental
        <music21.pitch.Pitch F#~7(+19c)>
        >>> h2.fundamental.fundamental
        <music21.pitch.Pitch A4>
        >>> h2.transpose(-24, inPlace=True)
        >>> h2
        <music21.pitch.Pitch F#~6(+19c)>
        >>> h2.fundamental.fundamental
        <music21.pitch.Pitch A2>

        :rtype: music21.pitch.Pitch
        '''
        centShift = _convertHarmonicToCents(number)
        temp = copy.deepcopy(self)
        # if no change, just return what we start with
        if centShift == 0:
            return temp
        # add this pitch's microtones plus the necessary cent shift
        if self._microtone is not None:
            temp.microtone = temp.microtone.cents + centShift
        else:
            temp.microtone = centShift

        # environLocal.printDebug(['getHarmonic()', 'self', self,
        #   'self.frequency', self.frequency, 'centShift', centShift, 'temp', temp,
        #   'temp.frequency', temp.frequency, 'temp.microtone', temp.microtone])

        # possibly optimize this to use only two Pitch objects
        final = Pitch()
        # set with this frequency
        final.frequency = temp.frequency
        # store a copy as the fundamental
        final.fundamental = copy.deepcopy(self)

        # environLocal.printDebug(['getHarmonic()', 'final', final,
        #   'final.frequency', final.frequency])
        return final

    def harmonicFromFundamental(self,
                                fundamental: Union[str, 'Pitch']
                                ) -> Tuple[int, float]:
        # noinspection PyShadowingNames
        '''
        Given another Pitch as a fundamental, find the harmonic
        of that pitch that is equal to this Pitch.

        Returns a tuple of harmonic number and the number of cents that
        the first Pitch object would have to be shifted to be the exact
        harmonic of this fundamental.

        Microtones applied to the fundamental are irrelevant,
        as the fundamental may be microtonally shifted to find a match to this Pitch.

        Example: G4 is the third harmonic of C3, albeit 2 cents flatter than
        the true 3rd harmonic.


        >>> p = pitch.Pitch('g4')
        >>> f = pitch.Pitch('c3')
        >>> p.harmonicFromFundamental(f)
        (3, 2.0)
        >>> p.microtone = p.harmonicFromFundamental(f)[1]  # adjust microtone
        >>> int(f.getHarmonic(3).frequency) == int(p.frequency)
        True

        The shift from B-5 to the 7th harmonic of C3 is more substantial
        and likely to be noticed by the audience.  To make p the 7th harmonic
        it'd have to be lowered by 31 cents.  Note that the
        second argument is a float, but because the default rounding of
        music21 is to the nearest cent, the 0.0 is not a significant digit.
        I.e. it might be more like 31.3 cents.

        >>> p = pitch.Pitch('B-5')
        >>> f = pitch.Pitch('C3')
        >>> p.harmonicFromFundamental(f)
        (7, -31.0)
        '''

        if isinstance(fundamental, str):
            fundamental = Pitch(fundamental)
        # else assume a Pitch object
        # got through all harmonics and find the one closes to this ps value
        target = self

        if target.ps <= fundamental.ps:
            raise PitchException(
                'cannot find an equivalent harmonic for a fundamental '
                + '(%s) that is not above this Pitch (%s)' % (fundamental, self)
            )

        # up to the 32 harmonic
        found = []  # store a list
        for i in range(1, 32):
            # gather all until we are above the target
            p = fundamental.getHarmonic(i)
            found.append((i, p))
            if p.ps > target.ps:
                break

        # environLocal.printDebug(['harmonicFromFundamental():', 'fundamental', fundamental,
        #    'found', found])

        # it is either the last or the second to last
        if len(found) < 2:  # only 1
            harmonicMatch, match = found[0]
            if match.ps > target.ps:
                gap = match.ps - target.ps
            elif match.ps < target.ps:
                gap = target.ps - match.ps
            else:
                gap = 0
        else:
            harmonicLower, candidateLower = found[-2]
            harmonicHigher, candidateHigher = found[-1]

            distanceLower = target.ps - candidateLower.ps
            distanceHigher = candidateHigher.ps - target.ps

            # environLocal.printDebug(['harmonicFromFundamental():',
            #        'distanceLower', distanceLower, 'distanceHigher', distanceHigher,
            #        'target', target])

            if distanceLower <= distanceHigher:
                # pd = 'distanceLower (%s); distanceHigher (%s); distance lower ' +
                #      'is closer to target: %s'
                # environLocal.printDebug(['harmonicFromFundamental():',
                #                         pd  % (candidateLower, candidateHigher, target)])
                # the lower is closer, thus we need to raise gap
                match = candidateLower
                gap = -abs(distanceLower)
                harmonicMatch = harmonicLower
            else:
                # the higher is closer, thus we need to lower the gap
                match = candidateHigher
                gap = abs(distanceHigher)
                harmonicMatch = harmonicHigher

        gap = round(gap, PITCH_SPACE_SIG_DIGITS) * 100

        return harmonicMatch, gap

        # environLocal.printDebug(['harmonicFromFundamental():', 'match', match,
        #    'gap', gap, 'harmonicMatch', harmonicMatch])

        # # need to find gap, otherwise may get very small values
        # gap = round(gap, PITCH_SPACE_SIG_DIGITS)
        # # create a pitch with the appropriate gap as a Microtone
        # if fundamental.microtone is not None:
        #     # if the result is zero, .microtone will automatically
        #     # be set to None
        #     fundamental.microtone = fundamental.microtone.cents + (gap * 100)
        # else:
        #     if gap != 0:
        #         fundamental.microtone = gap * 100
        # return harmonicMatch, fundamental

    def harmonicString(self,
                       fundamental: Union[str, 'music21.pitch.Pitch', None] = None
                       ) -> str:
        '''
        Return a string representation of a harmonic equivalence.

        N.B. this has nothing to do with what string a string player
        would use to play the harmonic on.  (Perhaps should be
        renamed).


        >>> pitch.Pitch('g4').harmonicString('c3')
        '3rdH(-2c)/C3'

        >>> pitch.Pitch('c4').harmonicString('c3')
        '2ndH/C3'

        >>> p = pitch.Pitch('c4')
        >>> p.microtone = 20  # raise 20
        >>> p.harmonicString('c3')
        '2ndH(+20c)/C3'

        >>> p.microtone = -20  # lower 20
        >>> p.harmonicString('c3')
        '2ndH(-20c)/C3'

        >>> p = pitch.Pitch('c4')
        >>> f = pitch.Pitch('c3')
        >>> f.microtone = -20
        >>> p.harmonicString(f)
        '2ndH(+20c)/C3(-20c)'
        >>> f.microtone = +20
        >>> p.harmonicString(f)
        '2ndH(-20c)/C3(+20c)'

        >>> p = pitch.Pitch('A4')
        >>> p.microtone = 69
        >>> p.harmonicString('c2')
        '7thH/C2'

        >>> p = pitch.Pitch('A4')
        >>> p.harmonicString('c2')
        '7thH(-69c)/C2'
        '''
        if fundamental is None:
            if self.fundamental is None:
                raise PitchException('no fundamental is defined for this Pitch: '
                                     + 'provide one as an argument')
            fundamental = self.fundamental
        if isinstance(fundamental, str):
            fundamental = Pitch(fundamental)

        harmonic, cents = self.harmonicFromFundamental(fundamental)
        # need to invert cent shift, as we are suggesting a shifted harmonic
        microtone = Microtone(-cents)
        if cents == 0:
            return '%s%sH/%s' % (harmonic, common.ordinalAbbreviation(harmonic), fundamental)
        else:
            return '%s%sH%s/%s' % (harmonic, common.ordinalAbbreviation(harmonic),
                                   microtone, fundamental)

    def harmonicAndFundamentalFromPitch(
            self,
            target: Union[str, 'Pitch']
    ) -> Tuple[int, 'Pitch']:
        '''
        Given a Pitch that is a plausible target for a fundamental,
        return the harmonic number and a potentially shifted fundamental
        that describes this Pitch.


        >>> g4 = pitch.Pitch('g4')
        >>> g4.harmonicAndFundamentalFromPitch('c3')
        (3, <music21.pitch.Pitch C3(-2c)>)
        '''
        if isinstance(target, str):
            target = Pitch(target)
        else:  # make a copy
            target = copy.deepcopy(target)

        harmonic, cents = self.harmonicFromFundamental(target)
        # flip direction
        cents = -cents

        # create a pitch with the appropriate gap as a Microtone
        if target.microtone is not None:
            # if the result is zero, .microtone will automatically
            # be set to None
            target.microtone = target.microtone.cents + cents
        else:
            if cents != 0:
                target.microtone = cents
        return harmonic, target

    def harmonicAndFundamentalStringFromPitch(
            self,
            fundamental: Union[str, 'Pitch']
    ) -> str:
        '''
        Given a Pitch that is a plausible target for a fundamental,
        find the harmonic number and a potentially shifted fundamental
        that describes this Pitch. Return a string representation.

        >>> pitch.Pitch('g4').harmonicAndFundamentalStringFromPitch('c3')
        '3rdH/C3(-2c)'

        >>> pitch.Pitch('c4').harmonicAndFundamentalStringFromPitch('c3')
        '2ndH/C3'

        >>> p = pitch.Pitch('c4')
        >>> p.microtone = 20  # raise 20
        >>> p.harmonicAndFundamentalStringFromPitch('c3')
        '2ndH/C3(+20c)'

        >>> p.microtone = -20  # lower 20
        >>> p.harmonicAndFundamentalStringFromPitch('c3')
        '2ndH/C3(-20c)'

        >>> p = pitch.Pitch('c4')
        >>> f = pitch.Pitch('c3')
        >>> f.microtone = -20
        >>> p.harmonicAndFundamentalStringFromPitch(f)
        '2ndH/C3'
        >>> f.microtone = +20
        >>> p.harmonicAndFundamentalStringFromPitch(f)
        '2ndH/C3'

        >>> p = pitch.Pitch('A4')
        >>> p.microtone = 69
        >>> p.harmonicAndFundamentalStringFromPitch('c2')
        '7thH/C2'

        >>> p = pitch.Pitch('A4')
        >>> p.harmonicAndFundamentalStringFromPitch('c2')
        '7thH/C2(-69c)'

        :rtype: str
        '''
        harmonic, fundamental = self.harmonicAndFundamentalFromPitch(fundamental)
        return '%s%sH/%s' % (harmonic, common.ordinalAbbreviation(harmonic),
                             fundamental)

    # --------------------------------------------------------------------------

    def isEnharmonic(self, other):
        '''
        Return True if other is an enharmonic equivalent of self.


        >>> p1 = pitch.Pitch('C#3')
        >>> p2 = pitch.Pitch('D-3')
        >>> p3 = pitch.Pitch('D#3')
        >>> p1.isEnharmonic(p2)
        True
        >>> p2.isEnharmonic(p1)
        True
        >>> p3.isEnharmonic(p1)
        False

        Quarter tone enharmonics work as well:

        >>> pC = pitch.Pitch('C4')
        >>> pC.accidental = pitch.Accidental('one-and-a-half-sharp')
        >>> pC
        <music21.pitch.Pitch C#~4>
        >>> pD = pitch.Pitch('D4')
        >>> pD.accidental = pitch.Accidental('half-flat')
        >>> pD
        <music21.pitch.Pitch D`4>
        >>> pC.isEnharmonic(pD)
        True

        Notes in different ranges are not enharmonics:

        >>> pitch.Pitch('C#4').isEnharmonic( pitch.Pitch('D-5') )
        False

        However, different octaves can be the same range, because octave number
        is relative to the `step` (natural form) of the pitch.

        >>> pitch.Pitch('C4').isEnharmonic( pitch.Pitch('B#3') )
        True
        >>> pitch.Pitch('C4').isEnharmonic( pitch.Pitch('B#4') )
        False

        If either pitch is octaveless, then they a pitch in any octave will match:

        >>> pitch.Pitch('C#').isEnharmonic( pitch.Pitch('D-9') )
        True
        >>> pitch.Pitch('C#4').isEnharmonic( pitch.Pitch('D-') )
        True

        Microtonally altered pitches do not return True unless the microtones are the same:

        >>> pSharp = pitch.Pitch('C#4')
        >>> pSharp.microtone = 20
        >>> pFlat = pitch.Pitch('D-4')
        >>> pSharp.isEnharmonic(pFlat)
        False

        >>> pFlat.microtone = 20
        >>> pSharp.isEnharmonic(pFlat)
        True


        Extreme enharmonics seem to work great.

        >>> p4 = pitch.Pitch('B##3')
        >>> p5 = pitch.Pitch('D-4')
        >>> p4.isEnharmonic(p5)
        True

        :rtype: bool
        '''
        if other.octave is None or self.octave is None:
            if (other.ps - self.ps) % 12 == 0:
                return True
            return False
        # if pitch space are equal, these are enharmonics
        else:
            if other.ps == self.ps:
                return True
            return False

    # a cache so that interval objects can be reused...
    _transpositionIntervals: Dict[str, Optional[interval.Interval]] = {
        '-d2': None,
        'd2': None,
    }

    def _getEnharmonicHelper(self: _T,
                             inPlace: bool,
                             intervalString: str) -> _T:
        '''
        abstracts the code from `getHigherEnharmonic` and `getLowerEnharmonic`

        :rtype: music21.pitch.Pitch
        '''
        if self._transpositionIntervals[intervalString] is None:
            self._transpositionIntervals[intervalString] = interval.Interval(intervalString)
        intervalObj = self._transpositionIntervals[intervalString]
        octaveStored = self.octave  # may be None
        p = intervalObj.transposePitch(self, maxAccidental=None)
        if not inPlace:
            if octaveStored is None:
                p.octave = None
            return p
        else:
            self.step = p.step
            self.accidental = p.accidental
            if p.microtone is not None:
                self.microtone = p.microtone
            if octaveStored is None:
                self.octave = None
            else:
                self.octave = p.octave
            return None

    def getHigherEnharmonic(self: _T, *, inPlace=False) -> _T:
        '''
        Returns an enharmonic `Pitch` object that is a higher
        enharmonic.  That is, the `Pitch` a diminished-second above
        the current `Pitch`.

        >>> p1 = pitch.Pitch('C#3')
        >>> p2 = p1.getHigherEnharmonic()
        >>> print(p2)
        D-3

        We can also set it in place (in which case it returns None):

        >>> p1 = pitch.Pitch('C#3')
        >>> p1.getHigherEnharmonic(inPlace=True)
        >>> print(p1)
        D-3

        The method even works for certain CRAZY enharmonics

        >>> p3 = pitch.Pitch('D--3')
        >>> p4 = p3.getHigherEnharmonic()
        >>> print(p4)
        E----3

        But not for things that are just utterly insane:

        >>> p4.getHigherEnharmonic()
        Traceback (most recent call last):
        music21.pitch.AccidentalException: -5 is not a supported accidental type


        Note that half accidentals get converted to microtones:

        >>> pHalfSharp = pitch.Pitch('D~4')
        >>> p3QuartersFlat = pHalfSharp.getHigherEnharmonic()
        >>> print(p3QuartersFlat)
        E-4(-50c)

        (Same thing if done in place; prior bug)

        >>> pHalfSharp = pitch.Pitch('D~4')
        >>> pHalfSharp.getHigherEnharmonic(inPlace=True)
        >>> print(pHalfSharp)
        E-4(-50c)

        :rtype: music21.pitch.Pitch
        '''
        return self._getEnharmonicHelper(inPlace, 'd2')

    def getLowerEnharmonic(self: _T, *, inPlace=False) -> _T:
        '''
        returns a Pitch enharmonic that is a diminished second
        below the current note

        If `inPlace` is set to true, changes the current Pitch and returns None.

        >>> p1 = pitch.Pitch('E-')
        >>> p2 = p1.getLowerEnharmonic()
        >>> print(p2)
        D#


        The lower enharmonic can have a different octave than
        the original.

        >>> p1 = pitch.Pitch('C-3')
        >>> p2 = p1.getLowerEnharmonic()
        >>> print(p2)
        B2

        >>> p1 = pitch.Pitch('C#3')
        >>> p1.getLowerEnharmonic(inPlace=True)
        >>> print(p1)
        B##2

        :rtype: music21.pitch.Pitch
        '''
        return self._getEnharmonicHelper(inPlace, '-d2')

    def simplifyEnharmonic(self: _T, *, inPlace=False, mostCommon=False) -> _T:
        '''
        Returns a new Pitch (or sets the current one if inPlace is True)
        that is either the same as the current pitch or has fewer
        sharps or flats if possible.  For instance, E# returns F,
        while A# remains A# (i.e., does not take into account that B- is
        more common than A#).  Useful to call if you ever have an
        algorithm that might take your piece far into the realm of
        double or triple flats or sharps.

        If mostCommon is set to True, then the most commonly used
        enharmonic spelling is chosen (that is, the one that appears
        first in key signatures as you move away from C on the circle
        of fifths).  Thus G-flat becomes F#, A# becomes B-flat,
        D# becomes E-flat, D-flat becomes C#, G# and A-flat are left
        alone.

        >>> p1 = pitch.Pitch('B#5')
        >>> p1.simplifyEnharmonic().nameWithOctave
        'C6'

        >>> p2 = pitch.Pitch('A#2')
        >>> p2.simplifyEnharmonic(inPlace=True)
        >>> p2
        <music21.pitch.Pitch A#2>

        >>> p3 = pitch.Pitch('E--3')
        >>> p4 = p3.transpose(interval.Interval('-A5'))
        >>> p4.simplifyEnharmonic()
        <music21.pitch.Pitch F#2>

        Setting `mostCommon` = `True` simplifies enharmonics
        even further.

        >>> pList = [pitch.Pitch('A#4'), pitch.Pitch('B-4'),
        ...          pitch.Pitch('G-4'), pitch.Pitch('F#4')]
        >>> [str(p.simplifyEnharmonic(mostCommon=True)) for p in pList]
        ['B-4', 'B-4', 'F#4', 'F#4']

        Note that pitches with implicit octaves retain their implicit octaves.
        This might change the pitch space for B#s and C-s.

        >>> pList = [pitch.Pitch('B'), pitch.Pitch('C#'), pitch.Pitch('G'), pitch.Pitch('A--')]
        >>> [str(p.simplifyEnharmonic()) for p in pList]
        ['B', 'C#', 'G', 'G']

        >>> pList = [pitch.Pitch('C-'), pitch.Pitch('B#')]
        >>> [p.ps for p in pList]
        [59.0, 72.0]
        >>> [p.simplifyEnharmonic().ps for p in pList]
        [71.0, 60.0]

        :rtype: music21.pitch.Pitch
        '''

        if inPlace:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        if returnObj.accidental is not None:
            if (abs(returnObj.accidental.alter) < 2.0
                    and returnObj.name not in ('E#', 'B#', 'C-', 'F-')):
                pass
            else:
                # by resetting the pitch space value, we will get a simpler
                # enharmonic spelling
                saveOctave = self.octave
                returnObj.ps = self.ps
                if saveOctave is None:
                    returnObj.octave = None

        if mostCommon:
            if returnObj.name == 'D#':
                returnObj.step = 'E'
                returnObj.accidental = Accidental('flat')
            elif returnObj.name == 'A#':
                returnObj.step = 'B'
                returnObj.accidental = Accidental('flat')
            elif returnObj.name == 'G-':
                returnObj.step = 'F'
                returnObj.accidental = Accidental('sharp')
            elif returnObj.name == 'D-':
                returnObj.step = 'C'
                returnObj.accidental = Accidental('sharp')

        if inPlace:
            return None
        else:
            return returnObj

    def getEnharmonic(self: _T, *, inPlace=False) -> _T:
        '''
        Returns a new Pitch that is the(/an) enharmonic equivalent of this Pitch.
        Can be thought of as flipEnharmonic or something like that.

        N.B.: n1.name == getEnharmonic(getEnharmonic(n1)).name is not necessarily true.
        For instance:

            getEnharmonic(E##) => F#
            getEnharmonic(F#) => G-
            getEnharmonic(A--) => G
            getEnharmonic(G) => F##

        However, for all cases not involving double sharps or flats
        (and even many that do), getEnharmonic(getEnharmonic(n)) = n

        For the most ambiguous cases, it's good to know that these are the enharmonics:

               C <-> B#, D <-> C##, E <-> F-; F <-> E#, G <-> F##, A <-> B--, B <-> C-

        However, isEnharmonic() for A## and B certainly returns True.


        >>> p = pitch.Pitch('d#')
        >>> print(p.getEnharmonic())
        E-
        >>> p = pitch.Pitch('e-8')
        >>> print(p.getEnharmonic())
        D#8

        Other tests:

        >>> print(pitch.Pitch('c-3').getEnharmonic())
        B2
        >>> print(pitch.Pitch('e#2').getEnharmonic())
        F2
        >>> print(pitch.Pitch('f#2').getEnharmonic())
        G-2
        >>> print(pitch.Pitch('c##5').getEnharmonic())
        D5
        >>> print(pitch.Pitch('g3').getEnharmonic())
        F##3
        >>> print(pitch.Pitch('B7').getEnharmonic())
        C-8

        Octaveless Pitches remain octaveless:

        >>> p = pitch.Pitch('a-')
        >>> p.getEnharmonic()
        <music21.pitch.Pitch G#>
        >>> p = pitch.Pitch('B#')
        >>> p.getEnharmonic()
        <music21.pitch.Pitch C>


        Works with half-sharps, etc. but converts them to microtones:

        >>> p = pitch.Pitch('D~')
        >>> print(p.getEnharmonic())
        E-(-50c)
        '''
        if inPlace:
            post = self
        else:
            post = copy.deepcopy(self)

        if post.accidental is not None:
            if post.accidental.alter > 0:
                # we have a sharp, need to get the equivalent flat
                post.getHigherEnharmonic(inPlace=True)
            elif post.accidental.alter < 0:
                post.getLowerEnharmonic(inPlace=True)
            else:  # assume some direction, perhaps using a dictionary
                if self.step in ('C', 'D', 'G'):
                    post.getLowerEnharmonic(inPlace=True)
                else:
                    post.getHigherEnharmonic(inPlace=True)

        else:
            if self.step in ('C', 'D', 'G'):
                post.getLowerEnharmonic(inPlace=True)
            else:
                post.getHigherEnharmonic(inPlace=True)

        if inPlace:
            return None
        else:
            return post


    def informClient(self):
        '''
        if this pitch is attached to a note, then let it know that it has changed.
        '''
        if self._client is not None:
            self._client.pitchChanged()


    def getAllCommonEnharmonics(self: _T, alterLimit: int = 2) -> List[_T]:
        '''
        Return all common unique enharmonics for a pitch,
        or those that do not involve more than two accidentals.


        >>> p = pitch.Pitch('c#3')
        >>> p.getAllCommonEnharmonics()
        [<music21.pitch.Pitch D-3>, <music21.pitch.Pitch B##2>]

        "Higher" enharmonics are listed before "Lower":

        >>> p = pitch.Pitch('G4')
        >>> p.getAllCommonEnharmonics()
        [<music21.pitch.Pitch A--4>, <music21.pitch.Pitch F##4>]

        By setting `alterLimit` to a higher or lower number we
        can limit the maximum number of notes to return:

        >>> p = pitch.Pitch('G-6')
        >>> p.getAllCommonEnharmonics(alterLimit=1)
        [<music21.pitch.Pitch F#6>]

        If you set `alterLimit` to 3 or 4, you're stretching the name of
        the method; some of these are certainly not *common* enharmonics:

        >>> p = pitch.Pitch('G-6')
        >>> enharmonics = p.getAllCommonEnharmonics(alterLimit=3)
        >>> [str(enh) for enh in enharmonics]
        ['A---6', 'F#6', 'E##6']

        Music21 does not support accidentals beyond quadruple sharp/flat, so
        `alterLimit` = 4 is the most you can use. (Thank goodness!)
        '''
        post = []
        c = self.simplifyEnharmonic(inPlace=False)
        if c.name != self.name:
            post.append(c)
        # iterative scan upward
        c = self
        while True:
            try:
                c = c.getHigherEnharmonic(inPlace=False)
            except AccidentalException:
                break  # ran out of accidentals
            if c.accidental is not None:
                if abs(c.accidental.alter) > alterLimit:
                    break
            if c not in post:
                post.append(c)
            else:  # we are looping
                break
        # iterative scan downward
        c = self
        while True:
            try:
                c = c.getLowerEnharmonic(inPlace=False)
            except AccidentalException:
                break  # ran out of accidentals
            if c.accidental is not None:
                if abs(c.accidental.alter) > alterLimit:
                    break
            if c not in post:
                post.append(c)
            else:  # we are looping
                break
        return post

    # --------------------------------------------------------------------------
    @property
    def diatonicNoteNum(self) -> int:
        '''
        Returns (or takes) an integer that uniquely identifies the
        diatonic version of a note, that is ignoring accidentals.
        The number returned is the diatonic interval above C0 (the lowest C on
        a Bösendorfer Imperial Grand), so G0 = 5, C1 = 8, etc.
        Numbers can be negative for very low notes.

        C4 (middleC) = 29, C#4 = 29, C##4 = 29, D-4 = 30, D4 = 30, etc.


        >>> c = pitch.Pitch('c4')
        >>> c.diatonicNoteNum
        29

        Unlike MIDI numbers (or `.ps`), C and C# has the same `diatonicNoteNum`:

        >>> c = pitch.Pitch('c#4')
        >>> c.diatonicNoteNum
        29

        But D-double-flat has a different `diatonicNoteNum` than C.

        >>> d = pitch.Pitch('d--4')
        >>> d.accidental.name
        'double-flat'
        >>> d.diatonicNoteNum
        30


        >>> lowC = pitch.Pitch('c1')
        >>> lowC.diatonicNoteNum
        8

        >>> b = pitch.Pitch()
        >>> b.step = 'B'
        >>> b.octave = -1
        >>> b.diatonicNoteNum
        0

        An `implicitOctave` of 4 is used if octave is not set:

        >>> c = pitch.Pitch('C')
        >>> c.diatonicNoteNum
        29

        `diatonicNoteNum` can also be set.  Changing it
        does not change the Accidental associated with the `Pitch`.

        >>> lowDSharp = pitch.Pitch('C#7')  # start high !!!
        >>> lowDSharp.diatonicNoteNum = 9  # move low
        >>> lowDSharp.octave
        1
        >>> lowDSharp.name
        'D#'


        Negative diatonicNoteNums are possible,
        in case, like John Luther Adams, you want
        to notate the sounds of sub-sonic Earth rumblings.

        >>> lowLowA = pitch.Pitch('A')
        >>> lowLowA.octave = -1
        >>> lowLowA.diatonicNoteNum
        -1

        >>> lowLowLowD = pitch.Pitch('D')
        >>> lowLowLowD.octave = -3
        >>> lowLowLowD.diatonicNoteNum
        -19

        :rtype: int
        '''
        return STEP_TO_DNN_OFFSET[self.step] + 1 + (7 * self.implicitOctave)

    @diatonicNoteNum.setter
    def diatonicNoteNum(self, newNum: int):
        octave = int((newNum - 1) / 7)
        noteNameNum = newNum - 1 - (7 * octave)
        pitchList = ('C', 'D', 'E', 'F', 'G', 'A', 'B')
        noteName = pitchList[noteNameNum]
        self.octave = octave
        self.step = noteName

    def transpose(
        self: _T,
        value: Union['music21.interval.IntervalBase', str, int],
        *,
        inPlace=False
    ) -> _T:
        '''
        Transpose the pitch by the user-provided value.  If the value is an
        integer, the transposition is treated in half steps. If the value is a
        string, any Interval string specification can be provided.
        Alternatively, a :class:`music21.interval.Interval` object can be
        supplied.

        >>> aPitch = pitch.Pitch('g4')
        >>> bPitch = aPitch.transpose('m3')
        >>> bPitch
        <music21.pitch.Pitch B-4>
        >>> cPitch = bPitch.transpose(interval.GenericInterval(2))
        >>> cPitch
        <music21.pitch.Pitch C-5>


        An interval object can also be a certain number of semitones,
        in which case, the spelling of the resulting note (sharp or flat, etc.)
        is up to the system to choose.

        >>> aInterval = interval.Interval(-6)
        >>> bPitch = aPitch.transpose(aInterval)
        >>> bPitch
        <music21.pitch.Pitch C#4>


        Transpose fFlat down 5 semitones -- sort of like a Perfect 4th, but
        should be respelled:

        >>> fFlat = pitch.Pitch('F-4')
        >>> newPitch = fFlat.transpose(-5)
        >>> newPitch
        <music21.pitch.Pitch B3>


        >>> aPitch
        <music21.pitch.Pitch G4>

        >>> aPitch.transpose(aInterval, inPlace=True)
        >>> aPitch
        <music21.pitch.Pitch C#4>


        Implicit octaves remain implicit:

        >>> anyGSharp = pitch.Pitch('G#')
        >>> print(anyGSharp.transpose('P8'))
        G#
        >>> print(anyGSharp.transpose('P5'))
        D#


        If the accidental of a pitch is chosen by music21, not
        given by the user, then after transposing, music21 will
        simplify the spelling again:

        >>> pc6 = pitch.Pitch(6)
        >>> pc6
        <music21.pitch.Pitch F#>
        >>> pc6.spellingIsInferred
        True
        >>> pc6.transpose('-m2')
        <music21.pitch.Pitch F>



        OMIT_FROM_DOCS

        Test to make sure that extreme ranges work

        >>> dPitch = pitch.Pitch('D2')
        >>> lowC = dPitch.transpose('m-23')
        >>> lowC
        <music21.pitch.Pitch C#-1>


        >>> otherPitch = pitch.Pitch('D2')
        >>> otherPitch.transpose('m-23', inPlace=True)
        >>> print(otherPitch)
        C#-1
        '''
        # environLocal.printDebug(['Pitch.transpose()', value])
        if 'IntervalBase' in getattr(value, 'classes', []):
            intervalObj = value
        else:  # try to process
            intervalObj = interval.Interval(value)

        p = intervalObj.transposePitch(self)
        if not isinstance(value, int):
            p.spellingIsInferred = self.spellingIsInferred

        if p.spellingIsInferred is True:
            p.simplifyEnharmonic(inPlace=True, mostCommon=True)

        if not inPlace:
            return p
        else:
            # can setName with nameWithOctave to recreate all essential
            # pitch attributes
            # NOTE: in some cases this may not return exactly the proper config
            self.name = p.name
            if self.octave is not None:
                self.octave = p.octave
            # manually copy accidental object
            self.accidental = p.accidental
            # set fundamental
            self.fundamental = p.fundamental
            return None

    # --------------------------------------------------------------------------
    # utilities for pitch object manipulation

    def transposeBelowTarget(
        self: _T,
        target,
        *,
        minimize=False,
        inPlace=False
    ) -> _T:
        # noinspection PyShadowingNames
        '''
        Given a source Pitch, shift it down some number of octaves until it is below the
        target.

        If `minimize` is True, a pitch below the target will move up to the
        nearest octave.

        >>> higherG = pitch.Pitch('g5')
        >>> lowerG = higherG.transposeBelowTarget(pitch.Pitch('c#4'))
        >>> lowerG
        <music21.pitch.Pitch G3>
        >>> higherG
        <music21.pitch.Pitch G5>


        Prior to Music21 3.0 (August 1, 2016), the default for inPlace was True, now it is False.
        To change the pitch itself, set inPlace to True

        >>> p = pitch.Pitch('g5')
        >>> p.transposeBelowTarget(pitch.Pitch('c#4'), inPlace=True)
        >>> p
        <music21.pitch.Pitch G3>


        If already below the target, make no change:

        >>> pitch.Pitch('g#3').transposeBelowTarget(pitch.Pitch('c#6'))
        <music21.pitch.Pitch G#3>

        Below target includes being the same as the target

        >>> pitch.Pitch('g#8').transposeBelowTarget(pitch.Pitch('g#1'))
        <music21.pitch.Pitch G#1>


        This does nothing because it is already low enough...

        >>> pitch.Pitch('g#2').transposeBelowTarget(pitch.Pitch('f#8'))
        <music21.pitch.Pitch G#2>

        But with minimize=True, it will actually RAISE the pitch so it is the closest
        pitch to the target

        >>> target = pitch.Pitch('f#8')
        >>> pitch.Pitch('g#2').transposeBelowTarget(target, minimize=True)
        <music21.pitch.Pitch G#7>

        >>> pitch.Pitch('f#2').transposeBelowTarget(target, minimize=True)
        <music21.pitch.Pitch F#8>
        '''
        if inPlace:
            src = self
        else:
            src = copy.deepcopy(self)
        while True:
            # ref 20, min 10, lower ref
            # ref 5, min 10, do not lower
            if src.ps - target.ps <= 0:
                break
            # lower one octave
            src.octave -= 1
        # case where self is below target and minimize is True
        if minimize:
            while True:
                if target.ps - src.ps < 12:
                    break
                else:
                    src.octave += 1

        if not inPlace:
            return src

    def transposeAboveTarget(self, target, *, minimize=False, inPlace=False):
        '''
        Given a source Pitch, shift it up octaves until it is above the target.

        If `minimize` is True, a pitch above the target will move down to the
        nearest octave.

        >>> pitch.Pitch('d2').transposeAboveTarget(pitch.Pitch('e4'))
        <music21.pitch.Pitch D5>


        Prior to Music21 3.0 (August 1, 2016), the default for inPlace was True, now it is False.
        To change the pitch itself, set inPlace to True


        >>> p = pitch.Pitch('d2')
        >>> p.transposeAboveTarget(pitch.Pitch('e4'), inPlace=True)
        >>> p
        <music21.pitch.Pitch D5>


        If already above the target, make no change:

        >>> pitch.Pitch('d7').transposeAboveTarget(pitch.Pitch('e2'))
        <music21.pitch.Pitch D7>

        Accept the same pitch:

        >>> pitch.Pitch('d2').transposeAboveTarget(pitch.Pitch('d8'))
        <music21.pitch.Pitch D8>

        If minimize is True, we go the closest position:

        >>> pitch.Pitch('d#8').transposeAboveTarget(pitch.Pitch('d2'), minimize=True)
        <music21.pitch.Pitch D#2>

        >>> pitch.Pitch('d7').transposeAboveTarget(pitch.Pitch('e2'), minimize=True)
        <music21.pitch.Pitch D3>

        >>> pitch.Pitch('d0').transposeAboveTarget(pitch.Pitch('e2'), minimize=True)
        <music21.pitch.Pitch D3>

        :rtype: music21.pitch.Pitch
        '''
        if inPlace:
            src = self
        else:
            src = copy.deepcopy(self)
        # case where self is below target
        while True:
            # ref 20, max 10, do not raise ref
            # ref 5, max 10, raise ref to above max
            if src.ps - target.ps >= 0:
                break
            # raise one octave
            src.octave += 1
        # case where self is above target and minimize is True
        if minimize:
            while True:
                if src.ps - target.ps < 12:
                    break
                else:
                    src.octave -= 1

        if not inPlace:
            return src

    # --------------------------------------------------------------------------

    def _nameInKeySignature(self, alteredPitches):
        '''
        Determine if this pitch is in the collection of supplied altered
        pitches, derived from a KeySignature object

        >>> a = pitch.Pitch('c#')
        >>> b = pitch.Pitch('g#')
        >>> ks = key.KeySignature(2)
        >>> a._nameInKeySignature(ks.alteredPitches)
        True

        >>> b._nameInKeySignature(ks.alteredPitches)
        False
        '''
        for p in alteredPitches:  # all are altered tones, must have acc
            if p.step == self.step:  # A# to A or A# to A-, etc
                if p.accidental.name == self.accidental.name:
                    return True
        return False

    def _stepInKeySignature(self, alteredPitches):
        '''
        Determine if this pitch is in the collection of supplied altered
        pitches, derived from a KeySignature object

        >>> a = pitch.Pitch('c')
        >>> b = pitch.Pitch('g')
        >>> ks = key.KeySignature(2)
        >>> a._stepInKeySignature(ks.alteredPitches)
        True

        >>> b._stepInKeySignature(ks.alteredPitches)
        False

        '''
        for p in alteredPitches:  # all are altered tones, must have acc
            if p.step == self.step:  # A# to A or A# to A-, etc
                return True
        return False

    def updateAccidentalDisplay(
        self,
        pitchPast: Optional[List['Pitch']] = None,
        pitchPastMeasure: Optional[List['Pitch']] = None,
        alteredPitches: Optional[List['Pitch']] = None,
        cautionaryPitchClass: bool = True,
        cautionaryAll: bool = False,
        overrideStatus: bool = False,
        cautionaryNotImmediateRepeat: bool = True,
        lastNoteWasTied: bool = False,
    ):
        '''
        Given an ordered list of Pitch objects in `pitchPast`, determine if
        this pitch's Accidental object needs to be created or updated with a
        natural or other cautionary accidental.

        Changes to this Pitch object's Accidental object are made in-place.

        `pitchPast` is a list of pitches preceding this pitch in the same measure.
        If None, a new list will be made.

        `pitchPastMeasure` is a list of pitches preceding this pitch but in a
        previous measure. If None, a new list will be made.

        The `alteredPitches` list supplies pitches from a :class:`~music21.key.KeySignature`
        object using the :attr:`~music21.key.KeySignature.alteredPitches` property.
        If None, a new list will be made.

        If `cautionaryPitchClass` is True, comparisons to past accidentals are
        made regardless of register. That is, if a past sharp is found two
        octaves above a present natural, a natural sign is still displayed.
        Note that this has nothing to do with whether a sharp (not in the key
        signature) is found in a different octave from the same note in a
        different octave.  The sharp must always be displayed.

        If `overrideStatus` is True, this method will ignore any current
        `displayStatus` stetting found on the Accidental. By default this does
        not happen. If `displayStatus` is set to None, the Accidental's
        `displayStatus` is set.

        If `cautionaryNotImmediateRepeat` is True, cautionary accidentals will
        be displayed for an altered pitch even if that pitch had already been
        displayed as altered (unless it's an immediate repetition).

        If `lastNoteWasTied` is True then this note will be treated as
        immediately following a tie.

        >>> a = pitch.Pitch('a')
        >>> past = [pitch.Pitch('a#'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> a.updateAccidentalDisplay(past, cautionaryAll=True)
        >>> a.accidental, a.accidental.displayStatus
        (<accidental natural>, True)

        >>> b = pitch.Pitch('a')
        >>> past = [pitch.Pitch('a#'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> b.updateAccidentalDisplay(past)  # should add a natural
        >>> b.accidental, b.accidental.displayStatus
        (<accidental natural>, True)

        In this example, the method will not add a natural because the match is
        pitchSpace and our octave is different.

        >>> a4 = pitch.Pitch('a4')
        >>> past = [pitch.Pitch('a#3'), pitch.Pitch('c#'), pitch.Pitch('c')]
        >>> a4.updateAccidentalDisplay(past, cautionaryPitchClass=False)
        >>> a4.accidental is None
        True

        '''
        # N.B. -- this is a very complex method
        # do not alter it without significant testing.

        if pitchPast is None:
            pitchPast = []
        if pitchPastMeasure is None:
            pitchPastMeasure = []
        if alteredPitches is None:
            alteredPitches = []

        # TODO: this presently deals with chords as simply a list
        #    we might permit pitchPast to contain a list of pitches, to represent
        #    a simultaneity?

        # should we display accidental if no previous accidentals have been displayed
        # i.e. if it's the first instance of an accidental after a tie
        displayAccidentalIfNoPreviousAccidentals = False

        pitchPastAll = pitchPastMeasure + pitchPast

        if overrideStatus is False:  # go with what we have defined
            if self.accidental is None:
                pass  # no accidental defined; we may need to add one
            elif self.accidental.displayStatus is None:  # not set; need to set
                # configure based on displayStatus alone, continue w/ normal
                pass
            elif self.accidental.displayStatus in (True, False):
                return  # exit: already set, do not override

        if lastNoteWasTied is True:
            if self.accidental is not None:
                if self.accidental.displayType != 'even-tied':
                    self.accidental.displayStatus = False
                else:
                    self.accidental.displayStatus = True
                return
            else:
                return  # exit: nothing more to do

        # no pitches in past...
        if not pitchPastAll:
            # if we have no past, we always need to show the accidental,
            # unless this accidental is in the alteredPitches list
            if (self.accidental is not None
                    and self.accidental.displayStatus in (False, None)):
                if not self._nameInKeySignature(alteredPitches):
                    self.accidental.displayStatus = True
                else:
                    self.accidental.displayStatus = False

            # in case display set to True and in alteredPitches, makeFalse
            elif (self.accidental is not None
                  and self.accidental.displayStatus is True
                  and self._nameInKeySignature(alteredPitches)):
                self.accidental.displayStatus = False

            # if no accidental or natural but matches step in key sig
            # we need to show or add or an accidental
            elif ((self.accidental is None or self.accidental.name == 'natural')
                  and self._stepInKeySignature(alteredPitches)):
                if self.accidental is None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
            return  # do not search past

        # pitches in past... first search if last pitch in measure
        # at this octave contradicts this pitch.  if so then no matter what
        # we need an accidental.
        for i in reversed(range(len(pitchPast))):
            thisPPast = pitchPast[i]
            if thisPPast.step == self.step and thisPPast.octave == self.octave:
                if thisPPast.name != self.name:  # conflicting alters, need accidental and return
                    if self.accidental is None:
                        self.accidental = Accidental('natural')
                    self.accidental.displayStatus = True
                    return
                else:  # names are the same, skip this line of questioning
                    break
        # nope, no previous pitches in this octave and register, now more complex things...

        # here tied and always are treated the same; we assume that
        # making ties sets the displayStatus, and thus we would not be
        # overriding that display status here
        if (cautionaryAll is True
            or (self.accidental is not None
                and self.accidental.displayType in ('even-tied', 'always'))):
            # show all no matter
            if self.accidental is None:
                self.accidental = Accidental('natural')
            # show all accidentals, even if past encountered
            self.accidental.displayStatus = True
            return  # do not search past

        # store if a match was found and display set from past pitches
        setFromPitchPast = False

        if cautionaryPitchClass is True:  # warn no mater what octave; thus create new without oct
            pSelf = Pitch(self.name)
            pSelf.accidental = self.accidental
        else:
            pSelf = self

        # where does the line divide between in measure and out of measure
        outOfMeasureLength = len(pitchPastMeasure)

        # need to step through pitchPast in reverse
        # comparing this pitch to the past pitches; if we find a match
        # in terms of name, then decide what to do

        # are we only comparing a list of past pitches all of
        # which are the same as this one and in the same measure?
        # if so, set continuousRepeatsInMeasure to True
        # else, set to False
        continuousRepeatsInMeasure: bool

        # figure out if this pitch is in the measure (pPastInMeasure = True)
        # or not.
        for i in reversed(range(len(pitchPastAll))):

            # is the past pitch in the measure or out of the measure?
            pPastInMeasure: bool

            if i < outOfMeasureLength:
                pPastInMeasure = False
                continuousRepeatsInMeasure = False
            else:
                pPastInMeasure = True
                for j in range(i, len(pitchPastAll)):
                    # do we have a continuous stream of the same note leading up to this one...
                    if pitchPastAll[j].nameWithOctave != self.nameWithOctave:
                        continuousRepeatsInMeasure = False
                        break
                else:
                    continuousRepeatsInMeasure = True
            # if the pitch is the first of a measure, has an accidental,
            # it is not an altered key signature pitch,
            # and it is not a natural, it should always be set to display
            if (pPastInMeasure is False
                and self.accidental is not None
                    and not self._nameInKeySignature(alteredPitches)):
                self.accidental.displayStatus = True
                return  # do not search past

            # create Pitch objects for comparison; remove pitch space
            # information if we are only doing a pitch class comparison
            if cautionaryPitchClass is True:  # no octave; create new without oct
                pPast = Pitch(pitchPastAll[i].name)
                # must manually assign reference to the same accidentals
                # as name alone will not transfer display status
                pPast.accidental = pitchPastAll[i].accidental
            else:  # cautionary in terms of pitch space; must match exact
                pPast = pitchPastAll[i]

            # if we do not match steps (A and A#), we can continue
            if pPast.step != pSelf.step:
                continue

            # store whether these match at the same octave; needed for some
            # comparisons even if not matching pitchSpace
            if self.octave == pitchPastAll[i].octave:
                octaveMatch = True
            else:
                octaveMatch = False

            # repeats of the same pitch immediately following, in the same measure
            # where one previous pitch has displayStatus = True; don't display
            if (continuousRepeatsInMeasure is True
                    and pPast.accidental is not None
                    and pPast.accidental.displayStatus is True):
                # only needed if one has a natural and this does not
                if pSelf.accidental is not None:
                    self.accidental.displayStatus = False
                return

            # repeats of the same accidentally immediately following
            # if An to An or A# to A#: do not need unless repeats requested,
            # regardless of if 'unless-repeated' is set, this will catch
            # a repeated case

            elif (continuousRepeatsInMeasure is True
                  and pPast.accidental is not None
                  and pSelf.accidental is not None
                  and pPast.accidental.name == pSelf.accidental.name):

                # BUG! what about C#4 C#5 C#4 C#5 -- last C#4 and C#5
                #   should not show accidental if cautionaryNotImmediateRepeat is False

                # if not in the same octave, and not in the key sig, do show accidental
                if (self._nameInKeySignature(alteredPitches) is False
                    and (octaveMatch is False
                         or pPast.accidental.displayStatus is False)):
                    displayAccidentalIfNoPreviousAccidentals = True
                    continue
                else:
                    self.accidental.displayStatus = False
                    setFromPitchPast = True
                    break

            # if An to A: do not need another natural
            # yet, if we are against the key sig, then we need another natural if in another octave
            elif (pPast.accidental is not None
                  and pPast.accidental.name == 'natural'
                  and (pSelf.accidental is None
                       or pSelf.accidental.name == 'natural')):
                if continuousRepeatsInMeasure is True:  # an immediate repeat; do not show
                    # unless we are altering the key signature and in
                    # a different register
                    if (self._stepInKeySignature(alteredPitches) is True
                            and octaveMatch is False):
                        if self.accidental is None:
                            self.accidental = Accidental('natural')
                        self.accidental.displayStatus = True
                    else:
                        if self.accidental is not None:
                            self.accidental.displayStatus = False
                # if we match the step in a key signature and we want
                # cautionary not immediate repeated
                elif (self._stepInKeySignature(alteredPitches) is True
                      and cautionaryNotImmediateRepeat is True):
                    if self.accidental is None:
                        self.accidental = Accidental('natural')
                    self.accidental.displayStatus = True

                # cautionaryNotImmediateRepeat is False
                # but the previous note was not in this measure,
                # so do the previous step anyhow
                elif (self._stepInKeySignature(alteredPitches) is True
                      and cautionaryNotImmediateRepeat is False
                      and pPastInMeasure is False):
                    if self.accidental is None:
                        self.accidental = Accidental('natural')
                    self.accidental.displayStatus = True

                # other cases: already natural in past usage, do not need
                # natural again (and not in key sig)
                else:
                    if self.accidental is not None:
                        self.accidental.displayStatus = False
                setFromPitchPast = True
                break

            # if A# to A, or A- to A, but not A# to A#
            # we use step and octave though not necessarily a ps comparison
            elif (pPast.accidental is not None
                  and pPast.accidental.name != 'natural'
                  and (pSelf.accidental is None
                       or pSelf.accidental.displayStatus is False)):
                if octaveMatch is False and cautionaryPitchClass is False:
                    continue
                if self.accidental is None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
                setFromPitchPast = True
                break

            # if An or A to A#: need to make sure display is set
            elif ((pPast.accidental is None
                   or pPast.accidental.name == 'natural')
                  and pSelf.accidental is not None
                  and pSelf.accidental.name != 'natural'):
                self.accidental.displayStatus = True
                setFromPitchPast = True
                break

            # if A- or An to A#: need to make sure display is set
            elif (pPast.accidental is not None
                  and pSelf.accidental is not None
                  and pPast.accidental.name != pSelf.accidental.name):
                self.accidental.displayStatus = True
                setFromPitchPast = True
                break

            # going from a natural to an accidental, we should already be
            # showing the accidental, but just to check
            # if A to A#, or A to A-, but not A# to A
            elif pPast.accidental is None and pSelf.accidental is not None:
                self.accidental.displayStatus = True
                # environLocal.printDebug(['match previous no mark'])
                setFromPitchPast = True
                break

            # if A# to A# and not immediately repeated:
            # default is to show accidental
            # if cautionaryNotImmediateRepeat is False, will not be shown
            elif (continuousRepeatsInMeasure is False
                  and pPast.accidental is not None
                  and pSelf.accidental is not None
                  and pPast.accidental.name == pSelf.accidental.name
                  and octaveMatch is True):
                if (cautionaryNotImmediateRepeat is False
                        and pPast.accidental.displayStatus is not False):
                    # do not show (unless previous note's accidental wasn't displayed
                    # because of a tie or some other reason)
                    # result will be False, do not need to check altered tones
                    self.accidental.displayStatus = False
                    displayAccidentalIfNoPreviousAccidentals = False
                    setFromPitchPast = True
                    break
                elif pPast.accidental.displayStatus is False:
                    # in case of ties...
                    displayAccidentalIfNoPreviousAccidentals = True
                else:
                    if not self._nameInKeySignature(alteredPitches):
                        self.accidental.displayStatus = True
                    else:
                        self.accidental.displayStatus = False
                    setFromPitchPast = True
                    return

            else:
                pass

        # if we have no previous matches for this pitch and there is
        # an accidental: show, unless in alteredPitches
        # cases of displayAlways and related are matched above
        if displayAccidentalIfNoPreviousAccidentals is True:
            # not the first pitch of this nameWithOctave in the measure
            # but, because of ties, the first to be displayed
            if self._nameInKeySignature(alteredPitches) is False:
                if self.accidental is None:
                    self.accidental = Accidental('natural')
                self.accidental.displayStatus = True
            else:
                self.accidental.displayStatus = False
            # displayAccidentalIfNoPreviousAccidentals = False  # just to be sure
        elif not setFromPitchPast and self.accidental is not None:
            if not self._nameInKeySignature(alteredPitches):
                self.accidental.displayStatus = True
            else:
                self.accidental.displayStatus = False

        # if we have natural that alters the key sig, create a natural
        elif not setFromPitchPast and self.accidental is None:
            if self._stepInKeySignature(alteredPitches):
                self.accidental = Accidental('natural')
                self.accidental.displayStatus = True

    def getStringHarmonic(self, chordIn):
        # noinspection PyShadowingNames
        '''
        Given a chord, determines whether the chord constitutes a string
        harmonic and then returns a new chord with the proper sounding pitch
        added.

        >>> n1 = note.Note('d3')
        >>> n2 = note.Note('g3')
        >>> n2.notehead = 'diamond'
        >>> n2.noteheadFill = False
        >>> p1 = pitch.Pitch('d3')
        >>> harmChord = chord.Chord([n1, n2])
        >>> harmChord.quarterLength = 1
        >>> newChord = p1.getStringHarmonic(harmChord)
        >>> newChord.quarterLength = 1
        >>> pitchList = newChord.pitches
        >>> pitchList
        (<music21.pitch.Pitch D3>, <music21.pitch.Pitch G3>, <music21.pitch.Pitch D5>)

        otherwise returns False

        '''
        # Takes in a chord, finds the interval between the notes
        from music21 import note, chord

        pitchList = chordIn.pitches
        isStringHarmonic = False

        if chordIn.getNotehead(pitchList[1]) == 'diamond':
            isStringHarmonic = True

        if not isStringHarmonic:
            return False

        chordInt = interval.notesToChromatic(pitchList[0], pitchList[1])

        if chordInt.intervalClass == 12:
            soundingPitch = pitchList[0].getHarmonic(2)
        elif chordInt.intervalClass == 7:
            soundingPitch = pitchList[0].getHarmonic(3)
        elif chordInt.intervalClass == 5:
            soundingPitch = pitchList[0].getHarmonic(4)
        elif chordInt.intervalClass == 4:
            soundingPitch = pitchList[0].getHarmonic(5)
        elif chordInt.intervalClass == 3:
            soundingPitch = pitchList[0].getHarmonic(6)
        elif chordInt.intervalClass == 6:
            soundingPitch = pitchList[0].getHarmonic(7)
        elif chordInt.intervalClass == 8:
            soundingPitch = pitchList[0].getHarmonic(8)
        else:
            # make this give an error or something
            soundingPitch = pitchList[0]

        noteOut = note.Note(soundingPitch.nameWithOctave)
        noteOut.noteheadParenthesis = True
        noteOut.noteheadFill = True
        noteOut.stemDirection = 'noStem'

        note1 = note.Note(pitchList[0].nameWithOctave)
        note2 = note.Note(pitchList[1].nameWithOctave)
        note2.notehead = chordIn.getNotehead(pitchList[1])

        # TODO: make note small

        chordOut = chord.Chord([note1, note2, noteOut])

        return chordOut


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                copy.copy(obj)
                copy.deepcopy(obj)

        p1 = Pitch('C#3')
        p2 = copy.deepcopy(p1)
        self.assertIsNot(p1, p2)
        self.assertIsNot(p1.accidental, p2.accidental)

    def testRepr(self):
        from music21 import pitch
        p = pitch.Pitch('B#3')
        self.assertEqual(repr(p), '<music21.pitch.Pitch B#3>')

    def testOctave(self):
        b = Pitch('B#3')
        self.assertEqual(b.octave, 3)

    def testAccidentalImport(self):
        '''Test that we are getting the properly set accidentals
        '''
        from music21 import corpus
        s = corpus.parse('bwv438.xml')
        tenorMeasures = s.parts[2].getElementsByClass('Measure')
        pAltered = tenorMeasures[0].pitches[1]
        self.assertEqual(pAltered.accidental.name, 'flat')
        self.assertEqual(pAltered.accidental.displayType, 'normal')
        # in key signature, so should not be shown
        self.assertFalse(pAltered.accidental.displayStatus)

        altoM6 = s.parts[1].measure(6)
        pAltered = altoM6.pitches[2]
        self.assertEqual(pAltered.accidental.name, 'sharp')
        self.assertTrue(pAltered.accidental.displayStatus)

    def testUpdateAccidentalDisplaySimple(self):
        '''Test updating accidental display.
        '''

        past = [Pitch('a3#'), Pitch('c#'), Pitch('c')]

        a = Pitch('c')
        a.accidental = Accidental('natural')
        a.accidental.displayStatus = False  # hide
        self.assertEqual(a.name, 'C')
        self.assertFalse(a.accidental.displayStatus)

        a.updateAccidentalDisplay(past, overrideStatus=True)
        self.assertTrue(a.accidental.displayStatus)

        b = copy.deepcopy(a)
        self.assertTrue(b.accidental.displayStatus)
        self.assertEqual(b.accidental.name, 'natural')

    def testUpdateAccidentalDisplaySeries(self):
        '''Test updating accidental display.
        '''

        def proc(_pList, past):
            for p in _pList:
                p.updateAccidentalDisplay(past)
                past.append(p)

        def compare(past, _result):
            # environLocal.printDebug(['accidental compare'])
            for i in range(len(_result)):
                p = past[i]
                if p.accidental is None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = _result[i][0]
                targetDisplayStatus = _result[i][1]

                self.assertEqual(pName, targetName,
                                 'name error for %d: %s instead of desired %s' % (
                                     i, pName, targetName))
                self.assertEqual(pDisplayStatus, targetDisplayStatus,
                                 '%d: %s display: %s, target %s' % (
                                     i, p, pDisplayStatus, targetDisplayStatus))

        # alternating, in a sequence, same pitch space
        pList = [Pitch('a#3'), Pitch('a3'), Pitch('a#3'),
                 Pitch('a3'), Pitch('a#3')]
        result = [('sharp', True), ('natural', True), ('sharp', True),
                  ('natural', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # alternating, in a sequence, different pitch space
        pList = [Pitch('a#2'), Pitch('a6'), Pitch('a#1'),
                 Pitch('a5'), Pitch('a#3')]
        result = [('sharp', True), ('natural', True), ('sharp', True),
                  ('natural', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # alternating, after gaps
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a5'),
                 Pitch('a#5'), Pitch('g-3'), Pitch('a3')]
        result = [('flat', True), (None, None), ('natural', True),
                  ('sharp', True), ('flat', True), ('natural', True)]
        proc(pList, [])
        compare(pList, result)

        # repeats of the same: show at different registers
        pList = [Pitch('a-2'), Pitch('a-2'), Pitch('a-5'),
                 Pitch('a#5'), Pitch('a#3'), Pitch('a3'), Pitch('a2')]
        result = [('flat', True), ('flat', False), ('flat', True),
                  ('sharp', True), ('sharp', True), ('natural', True), ('natural', True)]
        proc(pList, [])
        compare(pList, result)

        # the always- 'unless-repeated' setting
        # first, with no modification, repeated accidentals are not shown
        pList = [Pitch('a-2'), Pitch('a#3'), Pitch('a#5')]
        result = [('flat', True), ('sharp', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # second, with status set to always
        pList = [Pitch('a-2'), Pitch('a#3'), Pitch('a#3')]
        pList[2].accidental.displayType = 'always'
        result = [('flat', True), ('sharp', True), ('sharp', True)]
        proc(pList, [])
        compare(pList, result)

        # status set to always
        pList = [Pitch('a2'), Pitch('a3'), Pitch('a5')]
        pList[2].accidental = Accidental('natural')
        pList[2].accidental.displayType = 'always'
        result = [(None, None), (None, None), ('natural', True)]
        proc(pList, [])
        compare(pList, result)

        # first use after other pitches in different register
        # note: this will force the display of the accidental
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a-5')]
        result = [('flat', True), (None, None), ('flat', True)]
        proc(pList, [])
        compare(pList, result)

        # first use after other pitches in different register
        # note: this will force the display of the accidental
        pList = [Pitch('a-2'), Pitch('g3'), Pitch('a-2')]
        # pairs of accidental, displayStatus
        result = [('flat', True), (None, None), ('flat', True)]
        proc(pList, [])
        compare(pList, result)

        # accidentals, first usage, not first pitch
        pList = [Pitch('a2'), Pitch('g#3'), Pitch('d-2')]
        result = [(None, None), ('sharp', True), ('flat', True)]
        proc(pList, [])
        compare(pList, result)

    def testUpdateAccidentalDisplaySeriesKeySignature(self):
        '''Test updating accidental display against a KeySignature
        '''
        from music21 import key

        def proc(_pList, past, alteredPitches):
            for p in _pList:
                p.updateAccidentalDisplay(past, alteredPitches=alteredPitches)
                past.append(p)

        def compare(past, _result):
            # environLocal.printDebug(['accidental compare'])
            for i in range(len(_result)):
                p = past[i]
                if p.accidental is None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = _result[i][0]
                targetDisplayStatus = _result[i][1]

                # environLocal.printDebug(['accidental test:', p, pName,
                #         pDisplayStatus, 'target:', targetName, targetDisplayStatus])
                self.assertEqual(pName, targetName)
                self.assertEqual(pDisplayStatus, targetDisplayStatus,
                                 '%d: %s display: %s, target %s' % (
                                     i, p, pDisplayStatus, targetDisplayStatus))

        # chromatic alteration of key
        pList = [Pitch('f#3'), Pitch('f#2'), Pitch('f3'),
                 Pitch('f#3'), Pitch('f#3'), Pitch('g3'), Pitch('f#3')]
        result = [('sharp', False), ('sharp', False), ('natural', True),
                  ('sharp', True), ('sharp', False), (None, None), ('sharp', False)]
        ks = key.KeySignature(1)  # f3
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # non initial scale tones
        pList = [Pitch('a3'), Pitch('b2'), Pitch('c#3'),
                 Pitch('f#3'), Pitch('g#3'), Pitch('f#3'), Pitch('a4')]
        result = [(None, None), (None, None), ('sharp', False),
                  ('sharp', False), ('sharp', False), ('sharp', False), (None, None)]
        ks = key.KeySignature(3)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # non initial scale tones with chromatic alteration
        pList = [Pitch('a3'), Pitch('c#3'), Pitch('g#3'),
                 Pitch('g3'), Pitch('c#4'), Pitch('g#4')]
        result = [(None, None), ('sharp', False), ('sharp', False),
                  ('natural', True), ('sharp', False), ('sharp', True)]
        ks = key.KeySignature(3)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # non initial scale tones with chromatic alteration
        pList = [Pitch('a3'), Pitch('c#3'), Pitch('g#3'),
                 Pitch('g3'), Pitch('c#4'), Pitch('g#4')]
        result = [(None, None), ('sharp', False), ('sharp', False),
                  ('natural', True), ('sharp', False), ('sharp', True)]
        ks = key.KeySignature(3)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # initial scale tones with chromatic alteration, repeated tones
        pList = [Pitch('f#3'), Pitch('f3'), Pitch('f#3'),
                 Pitch('g3'), Pitch('f#4'), Pitch('f#4')]
        result = [('sharp', False), ('natural', True), ('sharp', True),
                   (None, None), ('sharp', True), ('sharp', False)]
        # no 4 is a dicey affair; could go either way
        ks = key.KeySignature(1)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # initial scale tones with chromatic alteration, repeated tones
        pList = [Pitch('d3'), Pitch('e3'), Pitch('f#3'),
                 Pitch('g3'), Pitch('f4'), Pitch('g#4'),
                 Pitch('c#3'), Pitch('f#4'), Pitch('c#4')]
        result = [(None, None), (None, None), ('sharp', False),
                  (None, None), ('natural', True), ('sharp', True),
                  ('sharp', False), ('sharp', True), ('sharp', False)]
        ks = key.KeySignature(2)
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # altered tones outside of key
        pList = [Pitch('b3'), Pitch('a3'), Pitch('e3'),
                 Pitch('b-3'), Pitch('a-3'), Pitch('e-3'),
                 Pitch('b-3'), Pitch('a-3'), Pitch('e-3'),
                 Pitch('b-3'), Pitch('a-3'), Pitch('e-3')]
        result = [
            ('natural', True), ('natural', True), ('natural', True),
            ('flat', True), ('flat', True), ('flat', True),
            ('flat', False), ('flat', False), ('flat', False),
            ('flat', False), ('flat', False), ('flat', False),
        ]
        ks = key.KeySignature(-3)  # b-, e-, a-
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

        # naturals against the key signature are required for each and every use
        pList = [Pitch('b3'), Pitch('a3'), Pitch('e3'),
                 Pitch('b4'), Pitch('a-3'), Pitch('e-3'),
                 Pitch('b3'), Pitch('a3'), Pitch('e3')]
        result = [('natural', True), ('natural', True), ('natural', True),
                  ('natural', True), ('flat', True), ('flat', True),
                  ('natural', True), ('natural', True), ('natural', True)]
        ks = key.KeySignature(-3)  # b-, e-, a-
        proc(pList, [], ks.alteredPitches)
        compare(pList, result)

    def testUpdateAccidentalDisplayOctaves(self):
        '''
        test if octave display is working
        '''
        def proc1(_pList, _past):
            for p in _pList:
                p.updateAccidentalDisplay(_past, cautionaryPitchClass=True,
                                          cautionaryNotImmediateRepeat=False)
                _past.append(p)

        def proc2(_pList, _past):
            for p in _pList:
                p.updateAccidentalDisplay(_past, cautionaryPitchClass=False,
                                          cautionaryNotImmediateRepeat=False)
                _past.append(p)

        def compare(_past, _result):
            # environLocal.printDebug(['accidental compare'])
            for i in range(len(_result)):
                p = _past[i]
                if p.accidental is None:
                    pName = None
                    pDisplayStatus = None
                else:
                    pName = p.accidental.name
                    pDisplayStatus = p.accidental.displayStatus

                targetName = _result[i][0]
                targetDisplayStatus = _result[i][1]

                self.assertEqual(pName, targetName)
                self.assertEqual(
                    pDisplayStatus,
                    targetDisplayStatus,
                    '%d: %s display: %s, target %s' % (
                        i, p, pDisplayStatus, targetDisplayStatus
                    )
                )

        pList = [Pitch('c#3'), Pitch('c#4'), Pitch('c#3'),
                 Pitch('c#4')]
        result = [('sharp', True), ('sharp', True), ('sharp', False),
                  ('sharp', False)]
        proc1(pList, [])
        compare(pList, result)
        pList = [Pitch('c#3'), Pitch('c#4'), Pitch('c#3'),
                 Pitch('c#4')]
        proc2(pList, [])
        compare(pList, result)

        a4 = Pitch('a4')
        past = [Pitch('a#3'), Pitch('c#'), Pitch('c')]
        # will not add a natural because match is pitchSpace
        a4.updateAccidentalDisplay(past, cautionaryPitchClass=False)
        self.assertEqual(a4.accidental, None)

    def testAccidentalsCautionary(self):
        '''
        a nasty test provided by Jose Cabal-Ugaz about octave leaps,
        cautionaryNotImmediateRepeat=False
        and key signature conflicts.
        '''
        from music21 import converter, key
        bm = converter.parse("tinynotation: 4/4 fn1 fn1 e-8 e'-8 fn4 en4 e'n4").flat
        bm.insert(0, key.KeySignature(1))
        bm.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        assert(bm.flat.notes[0].pitch.accidental.name == 'natural')     # Fn
        assert(bm.flat.notes[0].pitch.accidental.displayStatus is True)
        assert(bm.flat.notes[1].pitch.accidental.name == 'natural')     # Fn
        assert(bm.flat.notes[1].pitch.accidental.displayStatus is True)
        assert(bm.flat.notes[2].pitch.accidental.name == 'flat')        # E-4
        assert(bm.flat.notes[2].pitch.accidental.displayStatus is True)
        assert(bm.flat.notes[3].pitch.accidental.name == 'flat')        # E-5
        assert(bm.flat.notes[3].pitch.accidental.displayStatus is True)
        assert(bm.flat.notes[4].pitch.accidental.name == 'natural')     # En4
        assert(bm.flat.notes[4].pitch.accidental.displayStatus is True)
        assert(bm.flat.notes[5].pitch.accidental.name == 'natural')     # En4
        assert(bm.flat.notes[5].pitch.accidental.displayStatus is True)

        assert(bm.flat.notes[6].pitch.accidental is not None)  # En5
        assert(bm.flat.notes[6].pitch.accidental.name == 'natural')
        assert(bm.flat.notes[6].pitch.accidental.displayStatus is True)

    def testPitchEquality(self):
        '''
        Test updating accidental display.
        '''
        data = [
            ('a', 'b', False), ('a', 'a', True), ('a#', 'a', False),
            ('a#', 'b-', False), ('a#', 'a-', False), ('a##', 'a#', False),
            ('a#4', 'a#4', True), ('a-3', 'a-4', False), ('a#3', 'a#4', False),
        ]
        for x, y, match in data:
            p1 = Pitch(x)
            p2 = Pitch(y)
            self.assertEqual(p1 == p2, match)
        # specific case of changing octave
        p1 = Pitch('a#')
        p2 = Pitch('a#')
        self.assertEqual(p1, p2)

        p1.octave = 4
        p2.octave = 3
        self.assertNotEqual(p1, p2)
        p1.octave = 4
        p2.octave = 4
        self.assertEqual(p1, p2)

    def testLowNotes(self):
        dPitch = Pitch('D2')
        lowC = dPitch.transpose('M-23')
        self.assertEqual(lowC.name, 'C')
        self.assertEqual(lowC.octave, -1)

    def testQuarterToneA(self):
        from music21 import stream, note, scale
        from music21.musicxml import m21ToXml

        p1 = Pitch('D#~')
        # environLocal.printDebug([p1, p1.accidental])
        self.assertEqual(str(p1), 'D#~')
        # test generation of raw musicxml output
        xmlOut = m21ToXml.GeneralObjectExporter().parse(p1).decode('utf-8')

        match = '<step>D</step><alter>1.5</alter><octave>4</octave>'
        xmlOut = xmlOut.replace(' ', '')
        xmlOut = xmlOut.replace('\n', '')
        self.assertNotEqual(xmlOut.find(match), -1)

        s = stream.Stream()
        for pStr in ['A~', 'A#~', 'A`', 'A-`']:
            p = Pitch(pStr)
            self.assertEqual(str(p), pStr)
            n = note.Note()
            n.pitch = p
            s.append(n)
        self.assertEqual(len(s), 4)
        match = [e.pitch.ps for e in s]
        self.assertEqual(match, [69.5, 70.5, 68.5, 67.5])

        s = stream.Stream()
        alterList = [None, 0.5, 1.5, -1.5, -0.5,
                     'half-sharp', 'one-and-a-half-sharp', 'half-flat', 'one-and-a-half-flat',
                     '~']
        sc = scale.MajorScale('c4')
        for x in range(1, 10):
            n = note.Note(sc.pitchFromDegree(x % sc.getDegreeMaxUnique()))
            n.quarterLength = 0.5
            n.pitch.accidental = Accidental(alterList[x])
            s.append(n)

        match = [str(n.pitch) for n in s.notes]
        self.assertEqual(match,
                         ['C~4', 'D#~4', 'E-`4', 'F`4', 'G~4', 'A#~4', 'B`4', 'C-`4', 'D~4'])

        match = [e.pitch.ps for e in s]
        self.assertEqual(match, [60.5, 63.5, 62.5, 64.5, 67.5, 70.5, 70.5, 58.5, 62.5])

    def testMicrotoneA(self):
        from music21 import pitch

        p = pitch.Pitch('a4')
        p.microtone = 25

        self.assertEqual(str(p), 'A4(+25c)')
        self.assertEqual(p.ps, 69.25)

        p.microtone = '-10'
        self.assertEqual(str(p), 'A4(-10c)')
        self.assertEqual(p.ps, 68.90)

        self.assertEqual(p.pitchClass, 9)

        p = p.transpose(12)
        self.assertEqual(str(p), 'A5(-10c)')
        self.assertEqual(p.ps, 80.90)

    def testMicrotoneB(self):
        from music21 import pitch

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(1)), 'C4')

        p = pitch.Pitch('c4')
        p.microtone = 20
        self.assertEqual(str(p), 'C4(+20c)')
        self.assertEqual(str(p.getHarmonic(1)), 'C4(+20c)')

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(2)), 'C5')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(3)), 'G5(+2c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(4)), 'C6')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(5)), 'E6(-14c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(6)), 'G6(+2c)')
        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(7)), 'A~6(+19c)')

        self.assertEqual(pitch.Pitch('g4').harmonicString('c3'), '3rdH(-2c)/C3')

        # self.assertEqual(str(_convertPsToStep(60.0)), "('C', <accidental natural>, None, 0)")

        self.assertEqual(str(pitch.Pitch('c4').getHarmonic(1)), 'C4')
        self.assertEqual(str(pitch.Pitch('c3').getHarmonic(2)), 'C4')
        self.assertEqual(str(pitch.Pitch('c2').getHarmonic(2)), 'C3')

        self.assertEqual(pitch.Pitch('c4').harmonicString('c3'), '2ndH/C3')

        f = pitch.Pitch('c3')
        f.microtone = -10
        self.assertEqual(str(f.getHarmonic(2)), 'C4(-10c)')

        p = pitch.Pitch('c4')
        f = pitch.Pitch('c3')
        f.microtone = -20
        # the third harmonic of c3 -20 is closer than the
        self.assertEqual(p.harmonicString(f), '2ndH(+20c)/C3(-20c)')

        f.microtone = +20
        self.assertEqual(p.harmonicString(f), '2ndH(-20c)/C3(+20c)')

        p1 = pitch.Pitch('c1')
        self.assertEqual(str(p1.getHarmonic(13)), 'G#~4(-9c)')

        p2 = pitch.Pitch('a1')
        self.assertEqual(str(p2.getHarmonic(13)), 'F~5(-9c)')

        self.assertEqual(str(p1.transpose('M6')), 'A1')
        # not sure if this is correct:
        # self.assertEqual(str(p1.getHarmonic(13).transpose('M6')), 'E##5(-9c)')

    def testMicrotoneC(self):
        from music21 import pitch

        match = []
        p = pitch.Pitch('C4')
        p.microtone = 5
        for i in range(11):
            match.append(str(p))
            p.microtone = p.microtone.cents - 1
        self.assertEqual(str(match),
                         "['C4(+5c)', 'C4(+4c)', 'C4(+3c)', 'C4(+2c)', 'C4(+1c)', "
                         + "'C4', 'C4(-1c)', 'C4(-2c)', 'C4(-3c)', 'C4(-4c)', 'C4(-5c)']")

    def testMicrotoneD(self):
        from music21 import pitch
        # the microtonal scale used by padberg
        f = [440, 458 + 1 / 3, 476 + 2 / 3, 495, 513 + 1 / 3,
             531 + 2 / 3, 550, 568 + 1 / 3,
             586 + 2 / 3, 605, 623 + 1 / 3, 641 + 2 / 3,
             660, 678 + 1 / 3, 696 + 2 / 3, 715,
             733 + 1 / 3, 751 + 2 / 3, 770, 788 + 1 / 3,
             806 + 2 / 3, 825, 843 + 1 / 3, 861 + 2 / 3]
        self.assertEqual(len(f), 24)
        pList = []
        for fq in f:
            p = pitch.Pitch()
            p.frequency = fq
            pList.append(str(p))
        self.assertTrue(
            common.whitespaceEqual(
                str(pList),
                '''
                ['A4', 'A~4(+21c)', 'B`4(-11c)', 'B4(+4c)', 'B~4(+17c)', 'C~5(-22c)',
                 'C#5(-14c)', 'C#~5(-7c)', 'D5(-2c)', 'D~5(+1c)', 'E-5(+3c)', 'E`5(+3c)',
                 'E5(+2c)', 'E~5(-1c)', 'F5(-4c)', 'F~5(-9c)', 'F#5(-16c)', 'F#~5(-23c)',
                 'F#~5(+19c)', 'G5(+10c)', 'G~5(-1c)', 'G#5(-12c)', 'G#~5(-24c)', 'G#~5(+14c)']''',
            ),
            str(pList)
        )


# ------------------------------------------------------------------------------
# define presented order in documentation


_DOC_ORDER = [Pitch, Accidental, Microtone]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
