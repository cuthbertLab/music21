# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         roman.py
# Purpose:      music21 classes for doing Roman Numeral / Tonal analysis
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2024 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Music21 class for dealing with Roman Numeral analysis
'''
from __future__ import annotations

import copy
import enum
import re
import typing as t
import unittest

from collections import namedtuple

from music21 import chord
from music21 import common
from music21 import defaults
from music21 import environment
from music21 import exceptions21
from music21.figuredBass import notation as fbNotation
from music21 import harmony
from music21 import interval
from music21 import key
from music21 import note
from music21 import pitch
from music21 import scale

FigureTuple = namedtuple('FigureTuple', ['aboveBass', 'alter', 'prefix'])
ChordFigureTuple = namedtuple('ChordFigureTuple', ['aboveBass', 'alter', 'prefix', 'pitch'])

environLocal = environment.Environment('roman')

# TODO: setting inversion should change the figure

T = t.TypeVar('T', bound='RomanNumeral')

# -----------------------------------------------------------------------------


SHORTHAND_RE = re.compile(r'#*-*b*o*[1-9xyz]')
ENDWITHFLAT_RE = re.compile(r'[b\-]$')

# cache all Key/Scale objects created or passed in; re-use
# permits using internally scored pitch segments
_scaleCache: dict[str, scale.ConcreteScale] = {}
_keyCache: dict[str, key.Key] = {}

# create a single notation object for RN initialization, for type-checking,
# but it will always be replaced.
_NOTATION_SINGLETON = fbNotation.Notation()


# only some figures imply a root other than the bass (e.g. "54" does not)
FIGURES_IMPLYING_ROOT: tuple[tuple[int, ...], ...] = (
    # triads
    (6,), (6, 3), (6, 4),
    # seventh chords
    (6, 5, 3), (6, 5), (6, 4, 3), (4, 3), (6, 4, 2), (4, 2), (2,),
    # ninth chords
    (7, 6, 5, 3), (6, 5, 4, 3), (6, 4, 3, 2), (7, 5, 3, 2),
    # eleventh chords
    (9, 7, 6, 5, 3), (7, 6, 5, 4, 3), (9, 6, 5, 4, 3), (9, 7, 6, 4, 3), (7, 6, 5, 4, 2),
)


def _getKeyFromCache(keyStr: str) -> key.Key:
    '''
    get a key from the cache if it is there; otherwise
    create a new key and put it in the cache and return it.
    '''
    if keyStr in _keyCache:
        # adding copy.copy will at least prevent small errors at a cost of only 3 nanoseconds
        # of added time.  A deepcopy, unfortunately, take 2.8ms, which is longer than not
        # caching at all.  And not caching at all really slows down things like RomanText.
        # This at least will prevent what happens if `.key.mode` is changed
        keyObj = copy.copy(_keyCache[keyStr])
    else:
        keyObj = key.Key(keyStr)
        _keyCache[keyObj.tonicPitchNameWithCase] = keyObj
    return keyObj


# figure shorthands for all modes.
figureShorthands = {
    '53': '',
    '3': '',
    '63': '6',
    '753': '7',
    '75': '7',  # controversial perhaps
    '73': '7',  # controversial perhaps
    '9753': '9',
    '975': '9',  # controversial perhaps
    '953': '9',  # controversial perhaps
    '97': '9',  # controversial perhaps
    '95': '9',  # controversial perhaps
    '93': '9',  # controversial perhaps
    '653': '65',
    '6b53': '6b5',
    '643': '43',
    '642': '42',
    # '6b5bb3': 'o65',
    'bb7b5b3': 'o7',
    'b7b5b3': 'ø7',
    'bb7b53': 'o7',
    'b7b53': 'ø7',
}

figureShorthandsMode: dict[str, dict] = {
    'major': {
    },
    'minor': {
    }
}


# this is sort of a crock :-)  but it's very helpful.
functionalityScores: dict[str, int] = {
    'I': 100,
    'i': 90,
    'V7': 80,
    'V': 70,
    'V65': 68,
    'I6': 65,
    'V6': 63,
    'V43': 61,
    'I64': 60,
    'IV': 59,
    'i6': 58,
    'viio7': 57,
    'V42': 55,
    'viio65': 53,
    'viio6': 52,
    '#viio65': 51,
    'ii': 50,
    '#viio6': 49,
    'ii65': 48,
    'ii43': 47,
    'ii42': 46,
    'IV6': 45,
    'ii6': 43,
    'VI': 42,
    '#VI': 41,
    'vi': 40,
    'viio': 39,
    '#viio': 38,
    'iio': 37,  # common in Minor
    'iio42': 36,
    'bII6': 35,  # Neapolitan
    'It6': 34,
    'Ger65': 33,
    'iio43': 32,
    'iio65': 31,
    'Fr43': 30,
    '#vio': 28,
    '#vio6': 27,
    'III': 22,
    'Sw43': 21,
    'v': 20,
    'VII': 19,
    'VII7': 18,
    'IV65': 17,
    'IV7': 16,
    'iii': 15,
    'iii6': 12,
    'vi6': 10,
}


# -----------------------------------------------------------------------------


def expandShortHand(shorthand):
    '''
    Expands shorthand notation into a list with all figures expanded:

    >>> roman.expandShortHand('64')
    ['6', '4']
    >>> roman.expandShortHand('973')
    ['9', '7', '3']
    >>> roman.expandShortHand('11b3')
    ['11', 'b3']
    >>> roman.expandShortHand('b13#9-6')
    ['b13', '#9', '-6']
    >>> roman.expandShortHand('-')
    ['5', '-3']

    Slashes don't matter:

    >>> roman.expandShortHand('6/4')
    ['6', '4']

    Note that this is not where abbreviations get expanded:

    >>> roman.expandShortHand('')
    []
    >>> roman.expandShortHand('7')  # not 7, 5, 3
    ['7']
    >>> roman.expandShortHand('4/3')  # not 6, 4, 3
    ['4', '3']

    Note that this is ['6'] not ['6', '3']:

    >>> roman.expandShortHand('6')
    ['6']

    Returns a list of individual shorthands.
    '''
    shorthand = shorthand.replace('/', '')  # this line actually seems unnecessary.
    if ENDWITHFLAT_RE.match(shorthand):
        shorthand += '3'
    shorthand = re.sub('11', 'x', shorthand)
    shorthand = re.sub('13', 'y', shorthand)
    shorthand = re.sub('15', 'z', shorthand)
    shorthandGroups = SHORTHAND_RE.findall(shorthand)
    if len(shorthandGroups) == 1 and shorthandGroups[0].endswith('3'):
        shorthandGroups = ['5', shorthandGroups[0]]

    shGroupOut = []
    for sh in shorthandGroups:
        sh = re.sub('x', '11', sh)
        sh = re.sub('y', '13', sh)
        sh = re.sub('z', '15', sh)
        shGroupOut.append(sh)
    return shGroupOut


def correctSuffixForChordQuality(chordObj, inversionString):
    '''
    Correct a given inversionString suffix given a chord of various qualities.

    >>> c = chord.Chord('E3 C4 G4')
    >>> roman.correctSuffixForChordQuality(c, '6')
    '6'

    >>> c = chord.Chord('E3 C4 G-4')
    >>> roman.correctSuffixForChordQuality(c, '6')
    'o6'

    '''
    fifthType = chordObj.semitonesFromChordStep(5)
    if fifthType == 6:
        qualityName = 'o'
    elif fifthType == 8:
        qualityName = '+'
    else:
        qualityName = ''

    if inversionString and (inversionString.startswith('o')
                            or inversionString.startswith('°')
                            or inversionString.startswith('/o')
                            or inversionString.startswith('ø')):
        if qualityName == 'o':  # don't call viio7, viioo7.
            qualityName = ''

    seventhType = chordObj.semitonesFromChordStep(7)
    if seventhType and fifthType == 6:
        # there is a seventh and this is a diminished 5
        if seventhType == 10 and qualityName == 'o':
            qualityName = 'ø'
        elif seventhType != 9:
            pass  # do something for extremely odd chords built on diminished triad.
    # print(inversionString, fifthName)
    return qualityName + inversionString


def postFigureFromChordAndKey(chordObj, keyObj=None):
    '''
    (Note: this will become a private function by v10.)

    Returns the post-RN figure for a given chord in a given key.

    If keyObj is none, it uses the root as a major key:

    >>> roman.postFigureFromChordAndKey(
    ...     chord.Chord(['F#2', 'D3', 'A-3', 'C#4']),
    ...     key.Key('C'),
    ...     )
    'o6#5b3'

    The function substitutes shorthand (e.g., '6' not '63')

    >>> roman.postFigureFromChordAndKey(
    ...     chord.Chord(['E3', 'C4', 'G4']),
    ...     key.Key('C'),
    ...     )
    '6'

    >>> roman.postFigureFromChordAndKey(
    ...     chord.Chord(['E3', 'C4', 'G4', 'B-5']),
    ...     key.Key('F'),
    ...     )
    '65'

    >>> roman.postFigureFromChordAndKey(
    ...     chord.Chord(['E3', 'C4', 'G4', 'B-5']),
    ...     key.Key('C'),
    ...     )
    '6b5'

    We reduce common omissions from seventh chords to be '7' instead
    of '75', '73', etc.

    >>> roman.postFigureFromChordAndKey(
    ...     chord.Chord(['A3', 'E-4', 'G-4']),
    ...     key.Key('b-'),
    ...     )
    'o7'

    OMIT_FROM_DOCS

    Fails on German Augmented 6th chords in root position.  Calls them
    half-diminished chords.

    (This is in OMIT_FROM_etc.)
    '''
    if keyObj is None:
        keyObj = key.Key(chordObj.root())
    chordFigureTuples = figureTuples(chordObj, keyObj)
    bassFigureAlter = chordFigureTuples[0].alter

    allFigureStringList = []

    third = chordObj.third
    fifth = chordObj.fifth
    # seventh = chordObj.seventh

    chordCardinality = chordObj.pitchClassCardinality
    if chordCardinality != 3:
        chordObjIsStandardTriad = False
        isMajorTriad = False
        isMinorTriad = False
    else:
        isMajorTriad = chordObj.isMajorTriad()
        # short-circuit this expensive call if we know it's not going to be true.
        isMinorTriad = False if isMajorTriad else chordObj.isMinorTriad()
        chordObjIsStandardTriad = (
            isMajorTriad
            or isMinorTriad
            or chordObj.isDiminishedTriad()  # check most common first
            or chordObj.isAugmentedTriad()  # then least common.
        )

    for ft in sorted(chordFigureTuples,
                     key=lambda tup: (-1 * tup.aboveBass, tup.alter, tup.pitch.ps)):
        # (diatonicIntervalNum, alter, alterStr, pitchObj) = figureTuple
        prefix = ft.prefix

        if ft.aboveBass != 1 and ft.pitch is third:
            if isMajorTriad or isMinorTriad:
                prefix = ''  # alterStr[1:]
            # elif isMinorTriad and ft.alter > 0:
            #    prefix = ''  # alterStr[1:]
        elif (ft.aboveBass != 1
              and ft.pitch is fifth
              and chordObjIsStandardTriad):
            prefix = ''  # alterStr[1:]

        if ft.aboveBass == 1:
            if ft.alter != bassFigureAlter and prefix != '':
                # mark altered octaves as 8 not 1
                figureString = prefix + '8'
                if figureString not in allFigureStringList:
                    # filter duplicates and put at beginning
                    allFigureStringList.insert(0, figureString)
        else:
            figureString = prefix + str(ft.aboveBass)
            # filter out duplicates.
            if figureString not in allFigureStringList:
                allFigureStringList.append(figureString)

    allFigureString = ''.join(allFigureStringList)
    key_mode = keyObj.mode

    # first is not currently used.
    if key_mode in figureShorthandsMode and allFigureString in figureShorthandsMode[key_mode]:
        allFigureString = figureShorthandsMode[allFigureString]
    elif allFigureString in figureShorthands:
        allFigureString = figureShorthands[allFigureString]

    # simplify common omissions from 7th chords
    if allFigureString in ('75', '73'):
        allFigureString = '7'

    allFigureString = correctSuffixForChordQuality(chordObj, allFigureString)

    return allFigureString


def figureTuples(chordObject: chord.Chord, keyObject: key.Key) -> list[ChordFigureTuple]:
    '''
    (This will become a private function in v10)

    Return a set of tuplets for each pitch showing the presence of a note, its
    interval above the bass its alteration (float) from a step in the given
    key, an `alterationString`, and the pitch object.

    Note though that for roman numerals, the applicable key is almost always
    the root.

    For instance, in C major, F# D A- C# would be:

    >>> roman.figureTuples(
    ...     chord.Chord(['F#2', 'D3', 'A-3', 'C#4']),
    ...     key.Key('C'),
    ...     )
    [ChordFigureTuple(aboveBass=1, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch F#2>),
     ChordFigureTuple(aboveBass=6, alter=0.0, prefix='', pitch=<music21.pitch.Pitch D3>),
     ChordFigureTuple(aboveBass=3, alter=-1.0, prefix='b', pitch=<music21.pitch.Pitch A-3>),
     ChordFigureTuple(aboveBass=5, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch C#4>)]

    In c-minor, the A- is a normal note, so the prefix is '' not 'b'.  The natural minor is used
    exclusively.

    >>> roman.figureTuples(
    ...     chord.Chord(['F#2', 'D3', 'A-3', 'C#4']),
    ...     key.Key('c'),
    ...     )
    [ChordFigureTuple(aboveBass=1, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch F#2>),
     ChordFigureTuple(aboveBass=6, alter=0.0, prefix='', pitch=<music21.pitch.Pitch D3>),
     ChordFigureTuple(aboveBass=3, alter=0.0, prefix='', pitch=<music21.pitch.Pitch A-3>),
     ChordFigureTuple(aboveBass=5, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch C#4>)]

    A C dominant-seventh chord in c minor alters the bass but not the 7th degree

    >>> roman.figureTuples(
    ...     chord.Chord(['E3', 'C4', 'G4', 'B-5']),
    ...     key.Key('c'),
    ...     )
    [ChordFigureTuple(aboveBass=1, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch E3>),
     ChordFigureTuple(aboveBass=6, alter=0.0, prefix='', pitch=<music21.pitch.Pitch C4>),
     ChordFigureTuple(aboveBass=3, alter=0.0, prefix='', pitch=<music21.pitch.Pitch G4>),
     ChordFigureTuple(aboveBass=5, alter=0.0, prefix='', pitch=<music21.pitch.Pitch B-5>)]

    >>> roman.figureTuples(
    ...     chord.Chord(['C4', 'E4', 'G4', 'C#4']),
    ...     key.Key('C'),
    ...     )
    [ChordFigureTuple(aboveBass=1, alter=0.0, prefix='', pitch=<music21.pitch.Pitch C4>),
     ChordFigureTuple(aboveBass=3, alter=0.0, prefix='', pitch=<music21.pitch.Pitch E4>),
     ChordFigureTuple(aboveBass=5, alter=0.0, prefix='', pitch=<music21.pitch.Pitch G4>),
     ChordFigureTuple(aboveBass=1, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch C#4>)]
    '''
    result = []
    bass = chordObject.bass()
    for thisPitch in chordObject.pitches:
        shortTuple = figureTupleSolo(thisPitch, keyObject, bass)
        appendTuple = ChordFigureTuple(shortTuple.aboveBass,
                                       shortTuple.alter,
                                       shortTuple.prefix,
                                       thisPitch)
        result.append(appendTuple)
    return result


def figureTupleSolo(
    pitchObj: pitch.Pitch,
    keyObj: key.Key,
    bass: pitch.Pitch
) -> FigureTuple:
    '''
    Return a single tuple for a pitch and key showing the interval above
    the bass, its alteration from a step in the given key, an alteration
    string, and the pitch object.

    For instance, in C major, an A-3 above an F# bass would be:

    >>> roman.figureTupleSolo(
    ...     pitch.Pitch('A-3'),
    ...     key.Key('C'),
    ...     pitch.Pitch('F#2'),
    ...     )
    FigureTuple(aboveBass=3, alter=-1.0, prefix='b')

    These figures can be more complex in minor, so this is a good reference, showing
    that natural minor is always used.

    >>> c = key.Key('c')
    >>> c_as_bass = pitch.Pitch('C3')
    >>> for name in ('E--', 'E-', 'E', 'E#', 'A--', 'A-', 'A', 'A#', 'B--', 'B-', 'B', 'B#'):
    ...     ft = roman.figureTupleSolo(pitch.Pitch(name + '4'), c, c_as_bass)
    ...     print(f'{name:4s} {ft}')
    E--  FigureTuple(aboveBass=3, alter=-1.0, prefix='b')
    E-   FigureTuple(aboveBass=3, alter=0.0, prefix='')
    E    FigureTuple(aboveBass=3, alter=1.0, prefix='#')
    E#   FigureTuple(aboveBass=3, alter=2.0, prefix='##')
    A--  FigureTuple(aboveBass=6, alter=-1.0, prefix='b')
    A-   FigureTuple(aboveBass=6, alter=0.0, prefix='')
    A    FigureTuple(aboveBass=6, alter=1.0, prefix='#')
    A#   FigureTuple(aboveBass=6, alter=2.0, prefix='##')
    B--  FigureTuple(aboveBass=7, alter=-1.0, prefix='b')
    B-   FigureTuple(aboveBass=7, alter=0.0, prefix='')
    B    FigureTuple(aboveBass=7, alter=1.0, prefix='#')
    B#   FigureTuple(aboveBass=7, alter=2.0, prefix='##')

    Returns a namedtuple called a FigureTuple.
    '''
    unused_scaleStep, scaleAccidental = keyObj.getScaleDegreeAndAccidentalFromPitch(pitchObj)

    thisInterval = interval.Interval(bass, pitchObj)
    aboveBass = thisInterval.diatonic.generic.mod7
    if scaleAccidental is None:
        rootAlterationString = ''
        alterDiff = 0.0
    else:
        alterDiff = scaleAccidental.alter
        alter = int(alterDiff)
        if alter < 0:
            rootAlterationString = 'b' * (-1 * alter)
        elif alter > 0:
            rootAlterationString = '#' * alter
        else:
            rootAlterationString = ''

    appendTuple = FigureTuple(aboveBass, alterDiff, rootAlterationString)
    return appendTuple


def identifyAsTonicOrDominant(
    inChord: list|tuple|chord.Chord,
    inKey: key.Key
) -> str|t.Literal[False]:
    '''
    Returns the roman numeral string expression (either tonic or dominant) that
    best matches the inChord. Useful when you know inChord is either tonic or
    dominant, but only two pitches are provided in the chord. If neither tonic
    nor dominant is possibly correct, False is returned

    >>> roman.identifyAsTonicOrDominant(['B2', 'F5'], key.Key('C'))
    'V65'

    >>> roman.identifyAsTonicOrDominant(['B3', 'G4'], key.Key('g'))
    'i6'

    >>> roman.identifyAsTonicOrDominant(['C3', 'B-4'], key.Key('f'))
    'V7'

    Notice that this -- with B-natural is also identified as V7 because
    it is returning the roman numeral root and the inversion name, not yet
    checking for correctness.

    >>> roman.identifyAsTonicOrDominant(['C3', 'B4'], key.Key('f'))
    'V7'

    >>> roman.identifyAsTonicOrDominant(['D3'], key.Key('f'))
    False
    '''
    if isinstance(inChord, (list, tuple)):
        inChord = chord.Chord(inChord)
    elif not isinstance(inChord, chord.Chord):
        raise ValueError('inChord must be a Chord or a list of strings')  # pragma: no cover

    pitchNameList = []
    for x in inChord.pitches:
        pitchNameList.append(x.name)
    oneRoot = inKey.pitchFromDegree(1)
    fiveRoot = inKey.pitchFromDegree(5)
    oneChordIdentified = False
    fiveChordIdentified = False
    if oneRoot.name in pitchNameList:
        oneChordIdentified = True
    elif fiveRoot.name in pitchNameList:
        fiveChordIdentified = True
    else:
        oneRomanChord = RomanNumeral('I7', inKey).pitches
        fiveRomanChord = RomanNumeral('V7', inKey).pitches

        onePitchNameList = []
        for x in oneRomanChord:
            onePitchNameList.append(x.name)

        fivePitchNameList = []
        for x in fiveRomanChord:
            fivePitchNameList.append(x.name)

        oneMatches = len(set(onePitchNameList) & set(pitchNameList))
        fiveMatches = len(set(fivePitchNameList) & set(pitchNameList))
        if oneMatches > fiveMatches:
            oneChordIdentified = True
        elif oneMatches < fiveMatches:
            fiveChordIdentified = True
        else:  # both oneMatches and fiveMatches == 0
            return False

    if oneChordIdentified:
        rootScaleDeg = common.toRoman(1)
        if inKey.mode == 'minor':
            rootScaleDeg = rootScaleDeg.lower()
        else:
            rootScaleDeg = rootScaleDeg.upper()
        inChord.root(oneRoot)
    elif fiveChordIdentified:
        rootScaleDeg = common.toRoman(5)
        inChord.root(fiveRoot)
    else:
        return False

    return rootScaleDeg + romanInversionName(inChord)


def romanInversionName(inChord: chord.Chord, inv: int|None = None) -> str:
    '''
    Extremely similar to Chord's inversionName() method, but returns string
    values and allows incomplete triads.

    >>> roman.romanInversionName(chord.Chord('E4 G4 C5'))
    '6'

    >>> roman.romanInversionName(chord.Chord('G4 B4 C5 E5'))
    '43'

    Manually set the inversion to see what would happen.

    >>> roman.romanInversionName(chord.Chord('C5 E5 G5'), inv=2)
    '64'

    >>> roman.romanInversionName(chord.Chord('C5 E5 G5'), inv=0)
    ''

    Uncommon/unusual chords return an empty string

    >>> roman.romanInversionName(chord.Chord('C5 C#4'))
    ''

    Does not return ninth or eleventh chord figures.
    '''
    # TODO: add ninth and eleventh chord figures.

    if inv is None:
        inv = inChord.inversion()

    if inChord.isSeventh() or inChord.seventh is not None:
        if inv == 0:
            return '7'
        elif inv == 1:
            return '65'
        elif inv == 2:
            return '43'
        elif inv == 3:
            return '42'
        else:
            return ''
    elif (inChord.isTriad()
            or inChord.isIncompleteMajorTriad()
            or inChord.isIncompleteMinorTriad()):
        if inv == 0:
            return ''  # not 53
        elif inv == 1:
            return '6'
        elif inv == 2:
            return '64'
        else:
            return ''
    else:
        return ''


def correctRNAlterationForMinor(
    figureTuple: FigureTuple,
    keyObj: key.Key
) -> FigureTuple:
    '''
    (This will become a private function in version 10)

    Takes in a FigureTuple and a Key object and returns the same or a
    new FigureTuple correcting for the fact that, for instance, Ab in c minor
    is VI not vi.  Works properly only if the note is the root of the chord.

    Used in RomanNumeralFromChord

    These return new FigureTuple objects

    >>> ft5 = roman.FigureTuple(aboveBass=6, alter=-1, prefix='')
    >>> ft5a = roman.correctRNAlterationForMinor(ft5, key.Key('c'))
    >>> ft5a
    FigureTuple(aboveBass=6, alter=-1, prefix='b')
    >>> ft5a is ft5
    False

    >>> ft6 = roman.FigureTuple(aboveBass=6, alter=0, prefix='')
    >>> roman.correctRNAlterationForMinor(ft6, key.Key('c'))
    FigureTuple(aboveBass=6, alter=0, prefix='b')

    >>> ft7 = roman.FigureTuple(aboveBass=7, alter=1, prefix='#')
    >>> roman.correctRNAlterationForMinor(ft7, key.Key('c'))
    FigureTuple(aboveBass=7, alter=0, prefix='')

    Does nothing for major and passes in the original Figure Tuple unchanged:

    >>> ft1 = roman.FigureTuple(aboveBass=6, alter=-1, prefix='b')
    >>> ft2 = roman.correctRNAlterationForMinor(ft1, key.Key('C'))
    >>> ft2
    FigureTuple(aboveBass=6, alter=-1, prefix='b')
    >>> ft1 is ft2
    True

    Does nothing for steps other than 6 or 7:

    >>> ft3 = roman.FigureTuple(aboveBass=4, alter=-1, prefix='b')
    >>> ft4 = roman.correctRNAlterationForMinor(ft3, key.Key('c'))
    >>> ft4
    FigureTuple(aboveBass=4, alter=-1, prefix='b')
    >>> ft3 is ft4
    True
    '''
    if keyObj.mode != 'minor':
        return figureTuple
    if figureTuple.aboveBass not in (6, 7):
        return figureTuple

    alter = figureTuple.alter
    rootAlterationString = figureTuple.prefix

    if alter == 1.0:
        alter = 0
        rootAlterationString = ''
    elif alter == 0.0:
        alter = 0  # NB! does not change!
        rootAlterationString = 'b'
    # more exotic:
    elif alter > 1.0:
        alter = alter - 1
        rootAlterationString = rootAlterationString[1:]
    elif alter < 0.0:
        rootAlterationString = 'b' + rootAlterationString

    return FigureTuple(figureTuple.aboveBass, alter, rootAlterationString)


def romanNumeralFromChord(
    chordObj: chord.Chord,
    keyObj: key.Key|str|None = None,
    preferSecondaryDominants: bool = False,
) -> RomanNumeral:
    # noinspection PyShadowingNames
    '''
    Takes a chord object and returns an appropriate chord name.  If keyObj is
    omitted, the root of the chord is considered the key (if the chord has a
    major third, it's major; otherwise it's minor).

    >>> rn = roman.romanNumeralFromChord(
    ...     chord.Chord(['E-3', 'C4', 'G-6']),
    ...     key.Key('g#'),
    ...     )
    >>> rn
    <music21.roman.RomanNumeral bivo6 in g# minor>

    The pitches remain the same with the same octaves:

    >>> for p in rn.pitches:
    ...     p
    <music21.pitch.Pitch E-3>
    <music21.pitch.Pitch C4>
    <music21.pitch.Pitch G-6>

    >>> romanNumeral2 = roman.romanNumeralFromChord(
    ...     chord.Chord(['E3', 'C4', 'G4', 'B-4', 'E5', 'G5']),
    ...     key.Key('F'),
    ...     )
    >>> romanNumeral2
    <music21.roman.RomanNumeral V65 in F major>

    Note that vi and vii in minor, by default, signifies what you might think of
    alternatively as #vi and #vii:

    >>> romanNumeral3 = roman.romanNumeralFromChord(
    ...     chord.Chord(['A4', 'C5', 'E-5']),
    ...     key.Key('c'),
    ...     )
    >>> romanNumeral3
    <music21.roman.RomanNumeral vio in c minor>

    >>> romanNumeral4 = roman.romanNumeralFromChord(
    ...     chord.Chord(['A-4', 'C5', 'E-5']),
    ...     key.Key('c'),
    ...     )
    >>> romanNumeral4
    <music21.roman.RomanNumeral bVI in c minor>
    >>> romanNumeral4.sixthMinor
    <Minor67Default.CAUTIONARY: 2>

    >>> romanNumeral5 = roman.romanNumeralFromChord(
    ...     chord.Chord(['B4', 'D5', 'F5']),
    ...     key.Key('c'),
    ...     )
    >>> romanNumeral5
    <music21.roman.RomanNumeral viio in c minor>

    >>> romanNumeral6 = roman.romanNumeralFromChord(
    ...     chord.Chord(['B-4', 'D5', 'F5']),
    ...     key.Key('c'),
    ...     )
    >>> romanNumeral6
    <music21.roman.RomanNumeral bVII in c minor>

    Diminished and half-diminished seventh chords can omit the third and still
    be diminished: (n.b. we also demonstrate that chords can be created from a
    string):

    >>> romanNumeralDim7 = roman.romanNumeralFromChord(
    ...     chord.Chord('A3 E-4 G-4'),
    ...     key.Key('b-'),
    ...     )
    >>> romanNumeralDim7
    <music21.roman.RomanNumeral viio7 in b- minor>

    For reference, odder notes:

    >>> romanNumeral7 = roman.romanNumeralFromChord(
    ...     chord.Chord(['A--4', 'C-5', 'E--5']),
    ...     key.Key('c'),
    ...     )
    >>> romanNumeral7
    <music21.roman.RomanNumeral bbVI in c minor>

    >>> romanNumeral8 = roman.romanNumeralFromChord(
    ...     chord.Chord(['A#4', 'C#5', 'E#5']),
    ...     key.Key('c'),
    ...     )
    >>> romanNumeral8
    <music21.roman.RomanNumeral #vi in c minor>

    >>> romanNumeral10 = roman.romanNumeralFromChord(
    ...     chord.Chord(['F#3', 'A3', 'E4', 'C5']),
    ...     key.Key('d'),
    ...     )
    >>> romanNumeral10
    <music21.roman.RomanNumeral #iiiø7 in d minor>


    Augmented 6ths without key context

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 C#5'),
    ...     )
    <music21.roman.RomanNumeral It6 in g minor>

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 B-4 C#5'),
    ...     )
    <music21.roman.RomanNumeral Ger65 in g minor>

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 A4 C#5'),
    ...     )
    <music21.roman.RomanNumeral Fr43 in g minor>

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 A#4 C#5'),
    ...     )
    <music21.roman.RomanNumeral Sw43 in g minor>

    With correct key context:

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 C#5'),
    ...     key.Key('G')
    ...     )
    <music21.roman.RomanNumeral It6 in G major>

    With incorrect key context does not find an augmented 6th chord:

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 C#5'),
    ...     key.Key('C')
    ...     )
    <music21.roman.RomanNumeral #io6b3 in C major>

    Empty chords, including :class:`~music21.harmony.NoChord` objects, give empty RomanNumerals:

    >>> roman.romanNumeralFromChord(harmony.NoChord())
    <music21.roman.RomanNumeral>

    Augmented 6th chords in other inversions do not currently find correct roman numerals

    * Changed in v7: i7 is given for a tonic or subdominant minor-seventh chord in major:

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('C4 E-4 G4 B-4'),
    ...     key.Key('C'))
    <music21.roman.RomanNumeral i7 in C major>

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 B-4 C5'),
    ...     key.Key('G'))
    <music21.roman.RomanNumeral iv65 in G major>

    minor-Major chords are written with a [#7] modifier afterwards:

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('C4 E-4 G4 B4'),
    ...     key.Key('C'))
    <music21.roman.RomanNumeral i7[#7] in C major>
    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E-4 G4 B4 C5'),
    ...     key.Key('C'))
    <music21.roman.RomanNumeral i65[#7] in C major>

    Former bugs that are now fixed:

    >>> romanNumeral11 = roman.romanNumeralFromChord(
    ...     chord.Chord(['E4', 'G4', 'B4', 'D5']),
    ...     key.Key('C'),
    ...     )
    >>> romanNumeral11
    <music21.roman.RomanNumeral iii7 in C major>

    >>> roman.romanNumeralFromChord(chord.Chord('A3 C4 E-4 G4'), key.Key('c'))
    <music21.roman.RomanNumeral viø7 in c minor>

    >>> roman.romanNumeralFromChord(chord.Chord('A3 C4 E-4 G4'), key.Key('B-'))
    <music21.roman.RomanNumeral viiø7 in B- major>

    >>> romanNumeral9 = roman.romanNumeralFromChord(
    ...     chord.Chord(['C4', 'E5', 'G5', 'C#6']),
    ...     key.Key('C'),
    ...     )
    >>> romanNumeral9
    <music21.roman.RomanNumeral I#853 in C major>

    Not an augmented 6th:

    >>> roman.romanNumeralFromChord(
    ...     chord.Chord('E4 G4 B-4 C#5')
    ...     )
    <music21.roman.RomanNumeral io6b5b3 in c# minor>


    The preferSecondaryDominants option defaults to False, but if set to True,
    then certain rare figures are swapped with their
    more common secondary dominant equivalent to produce
    Roman numerals like 'V/V' instead of 'II'.

    This has no effect on most chords.
    A change is triggered if and only if:

    * the chord is a major triad or dominant seventh

    * the chord is not diatonic to the primary key (i.e., chromatically altered)

    * the root of secondary key is diatonic to the primary key.

    So first without setting preferSecondaryDominants:

    >>> cd = chord.Chord('D F# A')
    >>> rn = roman.romanNumeralFromChord(cd, 'C')
    >>> rn.figure
    'II'

    And now with preferSecondaryDominants=True:

    >>> rn = roman.romanNumeralFromChord(cd, 'C', preferSecondaryDominants=True)
    >>> rn.figure
    'V/V'

    Dominant sevenths must be spelt correctly
    (see conditions at :meth:`~music21.chord.Chord.isDominantSeventh`).

    So let's try D dominant seventh in various contexts.

    >>> cd = chord.Chord('F#4 A4 C5 D5')

    In G major this still comes out without recourse to a secondary,
    whether preferSecondaryDominants is True or False.

    >>> rn = roman.romanNumeralFromChord(cd, 'G')
    >>> rn.figure
    'V65'

    >>> rn = roman.romanNumeralFromChord(cd, 'G', preferSecondaryDominants=True)
    >>> rn.figure
    'V65'

    In C major it does come through as a secondary

    >>> rn = roman.romanNumeralFromChord(cd, 'C', preferSecondaryDominants=True)
    >>> rn.figure
    'V65/V'

    "German Augmented sixth" chords are left intact, without change.
    This is thanks to the constraints on
    spelling and on the root of the secondary degree.

    >>> cd = chord.Chord('Ab4 C5 Eb5 F#5')
    >>> rn = roman.romanNumeralFromChord(cd, 'C', preferSecondaryDominants=True)
    >>> rn.figure
    'Ger65'

    Let's check that with a dominant seventh spelling and minor key context:

    >>> cd = chord.Chord('Ab4 C5 Eb5 Gb5')
    >>> rn = roman.romanNumeralFromChord(cd, 'c', preferSecondaryDominants=True)
    >>> rn.figure
    'bVIb753'

    So that's a context in which the root is diatonic,
    but the possible secondary root is not.
    Now let's do the opposite case with a root that is not diatonic
    and a secondary that is.

    >>> cd = chord.Chord('Ab4 C5 Eb5 Gb5')
    >>> rn = roman.romanNumeralFromChord(cd, 'c', preferSecondaryDominants=True)
    >>> rn.figure
    'bVIb753'

    Watch out, because there are still a lot of chords that
    preferSecondaryDominants will alter.
    This is deliberate: this option defaults to false
    so it does not run unless a user specifically initiates it
    and actively wants to make modifications.
    Power users could create more specific conditions in which to call it,
    e.g., before/after specific chords,
    and they can only do so if it errs on the side of more changes.

    For example, in minor, 'I' will be mapped to 'V/iv'.

    >>> cd = chord.Chord('F4 A4 C5')
    >>> rn = roman.romanNumeralFromChord(cd, 'f')
    >>> rn.figure
    'I'

    >>> cd = chord.Chord('F4 A4 C5')
    >>> rn = roman.romanNumeralFromChord(cd, 'f', preferSecondaryDominants=True)
    >>> rn.figure
    'V/iv'

    This might be appropriate in the middle of a progression like
    i, V/iv, iv.
    By contrast, it's probably not wanted for a tierce de picardie at the end
    iv6, V, I.
    This kind of context-sensitivity is not currently included.

    OMIT_FROM_DOCS

    Note that this should be III+642 gives III+#642 (# before 6 is unnecessary)

    # >>> roman.romanNumeralFromChord(chord.Chord('B3 D3 E-3 G3'), key.Key('c'))
    # <music21.roman.RomanNumeral III+642 in c minor>


    These two are debatable -- is the harmonic minor or the natural minor used as the basis?

    # >>> roman.romanNumeralFromChord(chord.Chord('F4 A4 C5 E-5'), key.Key('c'))
    # <music21.roman.RomanNumeral IVb753 in c minor>
    # <music21.roman.RomanNumeral IV75#3 in c minor>

    # >>> roman.romanNumeralFromChord(chord.Chord('F4 A4 C5 E5'), key.Key('c'))
    # <music21.roman.RomanNumeral IV7 in c minor>
    # <music21.roman.RomanNumeral IV#75#3 in c minor>

    (This is in OMIT_FROM_etc.)
    '''

    # use these when we know the key. (But don't we need to know the mode too?)
    aug6subs = {
        '#ivo6b3': 'It6',
        '#ivob64': 'It64',  # minor only
        '#ivobb64': 'It64',  # major only
        '#ivob5b3': 'It53',  # minor only
        '#ivob5bb3': 'It53',  # major only

        'IIø#643': 'Fr43',
        'IIø75#3': 'Fr7',  # in minor
        'IIø7b5#3': 'Fr7',  # in major
        'IIø6#42': 'Fr42',  # in minor
        'IIøb6#42': 'Fr42',  # in major
        'IIø65': 'Fr65',  # in minor seems wrong
        'IIø65b3': 'Fr65',  # in major

        '#ii64b3': 'Sw43',
        '#iiø7': 'Sw7',  # minor; is wrong
        '#iib7bb53': 'Sw7',  # major
        '#iib642': 'Sw42',  # minor
        '#iibb642': 'Sw42',  # major
        '#ii6b5b3': 'Sw65',  # minor
        '#ii6b5bb3': 'Sw65',  # major

        '#ivo6b5b3': 'Ger65',  # in minor
        '#ivo6bb5b3': 'Ger65',  # in major
        '#ivob64b3': 'Ger43',  # in minor
        '#ivobb64bb3': 'Ger43',  # in major
        '#ivob6b42': 'Ger42',  # in minor
        '#ivob6bb42': 'Ger42',  # in major
        '#ivø7': 'Ger7',  # in minor -- seems wrong
        '#ivobb7b5bb3': 'Ger7',  # in major
    }
    aug6NoKeyObjectSubs = {
        'io6b3': 'It6',
        'iob64': 'It64',
        'iob5b3': 'It53',

        'Iø64b3': 'Fr43',
        'Iøb7b53': 'Fr7',
        'Iøb642': 'Fr42',
        'Iø6b5b3': 'Fr65',

        'i64b3': 'Sw43',
        'ib7bb53': 'Sw7',
        'ibb642': 'Sw42',
        'i6b5bb3': 'Sw65',

        'io6b5b3': 'Ger65',
        # Ger7 = iø7 -- is wrong
        'iob64b3': 'Ger43',
        'iob6b42': 'Ger42',
    }
    minorSeventhSubs = {
        'b75b3': '7',
        '6b5': '65',
        'b64b3': '43',
        '6b42': '42',
    }
    minorMajorSeventhSubs = {
        '75b3': '7[#7]',  # major key root
        '65': '65[#7]',  # major key 1st inversion
        'b643': '43[#7]',  # major key second inversion
        '6b42': '42[#7]',  # major key form of 3rd inversion mM7...
        '#753': '#7',  # root position in minor key
        '6#53': '65[#7]',  # minor key 1st inversion
        '64#3': '43[#7]',  # minor key 2nd inversion
        '42': '42[#7]',  # minor key form of 3rd inversion mM7...
    }

    noKeyGiven = (keyObj is None)

    if not chordObj.pitches:
        return RomanNumeral()

    # TODO: Make sure 9 works
    # stepAdjustments = {'minor' : {3: -1, 6: -1, 7: -1},
    #                   'diminished' : {3: -1, 5: -1, 6: -1, 7: -2},
    #                   'half-diminished': {3: -1, 5: -1, 6: -1, 7: -1},
    #                   'augmented': {5: 1},
    #                   }
    root = chordObj.root()
    thirdType = chordObj.semitonesFromChordStep(3)
    if thirdType == 4:
        isMajorThird = True
    else:
        isMajorThird = False


    if keyObj is None:
        if isMajorThird:
            rootKeyObj = _getKeyFromCache(root.name.upper())
        else:
            rootKeyObj = _getKeyFromCache(root.name.lower())
        keyObj = rootKeyObj
    elif isinstance(keyObj, str):
        keyObj = key.Key(keyObj)

    ft = figureTupleSolo(root, keyObj, keyObj.tonic)  # a FigureTuple
    ft = correctRNAlterationForMinor(ft, keyObj)

    if ft.alter == 0:
        tonicPitch = keyObj.tonic
    else:
        # Altered scale degrees, such as #V require a different hypothetical
        # tonic:

        # not worth caching yet -- 150 microseconds; we're trying to lower milliseconds
        transposeInterval = interval.intervalFromGenericAndChromatic(
            interval.GenericInterval(1),
            interval.ChromaticInterval(ft.alter))
        tonicPitch = transposeInterval.transposePitch(keyObj.tonic)

    if keyObj.mode == 'major':
        tonicPitchName = tonicPitch.name.upper()
    else:
        tonicPitchName = tonicPitch.name.lower()

    alteredKeyObj = _getKeyFromCache(tonicPitchName)

    stepRoman = common.toRoman(ft.aboveBass)
    if isMajorThird:
        pass
    elif not isMajorThird:
        stepRoman = stepRoman.lower()
    inversionString = postFigureFromChordAndKey(chordObj, alteredKeyObj)

    rnString = ft.prefix + stepRoman + inversionString

    if (not isMajorThird
            and inversionString in minorSeventhSubs
            # only do expensive call in case it might be possible
            and chordObj.isSeventhOfType((0, 3, 7, 10))):
        rnString = ft.prefix + stepRoman + minorSeventhSubs[inversionString]
    elif (not isMajorThird
              and inversionString in minorMajorSeventhSubs
              and chordObj.isSeventhOfType((0, 3, 7, 11))):
        rnString = ft.prefix + stepRoman + minorMajorSeventhSubs[inversionString]

    elif (not noKeyGiven
          and rnString in aug6subs
          and chordObj.isAugmentedSixth(permitAnyInversion=True)):
        rnString = aug6subs[rnString]
    elif (noKeyGiven
          and rnString in aug6NoKeyObjectSubs
          and chordObj.isAugmentedSixth(permitAnyInversion=True)):
        rnString = aug6NoKeyObjectSubs[rnString]
        nationalityStart = rnString[:2]  # nb: Ger = Ge
        if nationalityStart in ('It', 'Ge'):
            fifth = chordObj.fifth
            if t.TYPE_CHECKING:
                assert fifth is not None
            keyObj = _getKeyFromCache(fifth.name.lower())
        elif nationalityStart in ('Fr', 'Sw'):
            seventh = chordObj.seventh
            if t.TYPE_CHECKING:
                assert seventh is not None
            keyObj = _getKeyFromCache(seventh.name.lower())

    if (
        preferSecondaryDominants
        and stepRoman != 'V'  # ignore if already "primary" dominant
        and (chordObj.isDominantSeventh() or chordObj.isMajorTriad())
    ):
        possibleSecondaryTonic = chordObj.root().transpose('P4').name
        degree = keyObj.getScaleDegreeFromPitch(possibleSecondaryTonic)
        if degree:  # None if not in chord
            secondaryAsRoman = RomanNumeral(degree,
                                            keyObj,
                                            preferSecondaryDominants=False
                                            ).romanNumeralAlone
            primaryFigure = romanNumeralFromChord(chordObj,
                                                  key.Key(possibleSecondaryTonic),
                                                  preferSecondaryDominants=False
                                                  ).figure
            rnString = f'{primaryFigure}/{secondaryAsRoman}'

    try:
        rn = RomanNumeral(rnString, keyObj, updatePitches=False,
            # correctRNAlterationForMinor() adds cautionary
            sixthMinor=Minor67Default.CAUTIONARY, seventhMinor=Minor67Default.CAUTIONARY)
    except fbNotation.ModifierException as strerror:
        raise RomanNumeralException(
            'Could not parse {0} from chord {1} as an RN '
            'in key {2}: {3}'.format(rnString, chordObj, keyObj, strerror))  # pragma: no cover

    # Is this linking them in an unsafe way?
    rn.pitches = chordObj.pitches
    return rn


class Minor67Default(enum.Enum):
    '''
    Enumeration that can be passed into :class:`~music21.roman.RomanNumeral`'s
    keyword arguments `sixthMinor` and `seventhMinor` to define how Roman numerals
    on the sixth and seventh scale degrees are parsed in minor.

    Here is a little helper function that creates the chord in c-minor with the given
    `sixthMinor` interpretation in order to show how Minor67Default affects the
    interpretation of `vi`.

    >>> vi = lambda sixChord, quality: ' '.join(p.name for p in roman.RomanNumeral(
    ...                                            sixChord,
    ...                                            'c',
    ...                                            sixthMinor=quality).pitches)

    The default for new chords is `QUALITY`, which means that the chord quality
    (major, minor, diminished) determines what note is the root, lowered ^6
    or raised ^6:

    >>> vi('vi', roman.Minor67Default.QUALITY)
    'A C E'
    >>> vi('VI', roman.Minor67Default.QUALITY)
    'A- C E-'

    The enumeration `FLAT` means that lowered ^6 is used for the root no matter what.
    (Note that `FLAT` does not mean that the root will have a flat sign on it,
    for instance, in f-sharp minor, lowered ^6 is D natural. and in a-sharp minor,
    lowered ^6 is F#.)

    >>> vi('vi', roman.Minor67Default.FLAT)
    'A- C- E-'
    >>> vi('VI', roman.Minor67Default.FLAT)
    'A- C E-'

    Conversely, `SHARP` implies that raised ^6 is used no matter what.

    >>> vi('vi', roman.Minor67Default.SHARP)
    'A C E'
    >>> vi('VI', roman.Minor67Default.SHARP)
    'A C# E'

    Since `FLAT` assumes lowered ^6 whether the chord is major or minor (or anything else),
    to get a raised ^6 with the `FLAT` enumeration add a sharp before the name:

    >>> vi('#vi', roman.Minor67Default.FLAT)
    'A C E'

    Likewise, with `SHARP`, a flat sign is needed to get lowered ^6:

    >>> vi('bVI', roman.Minor67Default.SHARP)
    'A- C E-'

    The enumeration of `CAUTIONARY` is identical to `QUALITY` except that it
    ignores the `#` in #vi and the `b` in bVI, allowing users to write these
    chords in two different way.  `CAUTIONARY` is recommended in the case where
    users from different systems of training are working together, and no
    exotic chords (such as major triads on raised ^6) are used.

    >>> vi('#vi', roman.Minor67Default.CAUTIONARY)
    'A C E'
    >>> vi('vi', roman.Minor67Default.CAUTIONARY)
    'A C E'
    >>> vi('bVI', roman.Minor67Default.CAUTIONARY)
    'A- C E-'
    >>> vi('VI', roman.Minor67Default.CAUTIONARY)
    'A- C E-'

    Whereas `QUALITY` follows a strict interpretation of what preceeding sharp and flat
    signs mean.  With `QUALITY`, since vi is already sharpened, #vi raises it even more.
    And since VI is already flattened, bVI lowers it even further:

    >>> vi('vi', roman.Minor67Default.QUALITY)
    'A C E'
    >>> vi('#vi', roman.Minor67Default.QUALITY)
    'A# C# E#'
    >>> vi('VI', roman.Minor67Default.QUALITY)
    'A- C E-'
    >>> vi('bVI', roman.Minor67Default.QUALITY)
    'A-- C- E--'

    If you are using the `CAUTIONARY` enum, these odd chords can still be created, but
    an additional sharp or flat should be used.

    >>> vi('##vi', roman.Minor67Default.CAUTIONARY)
    'A# C# E#'
    >>> vi('bbVI', roman.Minor67Default.CAUTIONARY)
    'A-- C- E--'

    For other odd chords that are contrary to the standard minor interpretation
    in the "wrong" direction, the interpretation is the same as `QUALITY`.

    For instance, here is a major triad on raised ^6 (what might be generally
    conceived of as V/ii), in the `QUALITY` and `CAUTIONARY` systems:

    >>> vi('#VI', roman.Minor67Default.QUALITY)
    'A C# E'
    >>> vi('#VI', roman.Minor67Default.CAUTIONARY)
    'A C# E'

    And a minor triad on lowered ^6.

    >>> vi('bvi', roman.Minor67Default.QUALITY)
    'A- C- E-'
    >>> vi('bvi', roman.Minor67Default.CAUTIONARY)
    'A- C- E-'

    All these examples use ^6, but the same concepts apply to ^7 using
    `seventhMinor` instead.

    This enumeration applies to secondary chords built on ^6 or ^7:

    >>> vi('V/vi', roman.Minor67Default.QUALITY)
    'E G# B'
    >>> vi('V/VI', roman.Minor67Default.QUALITY)
    'E- G B-'

    >>> vi('V/vi', roman.Minor67Default.FLAT)
    'E- G B-'
    >>> vi('V/VI', roman.Minor67Default.FLAT)
    'E- G B-'

    * Changed in v8: previously `sixthMinor` and `seventhMinor` did
      not carry over to secondary roman numerals.
    '''
    QUALITY = 1
    CAUTIONARY = 2
    SHARP = 3
    FLAT = 4


# -----------------------------------------------------------------------------

# Delete RomanException in v10
class RomanException(exceptions21.Music21Exception):
    '''
    RomanException will be removed in v10.  Catch RomanNumeralException instead.
    '''


class RomanNumeralException(ValueError, RomanException):
    pass


# -----------------------------------------------------------------------------


class RomanNumeral(harmony.Harmony):
    '''
    A RomanNumeral object is a specialized type of
    :class:`~music21.harmony.Harmony` object that stores the function and scale
    degree of a chord within a :class:`~music21.key.Key`.

    >>> ivInE = roman.RomanNumeral('IV', key.Key('E'))
    >>> ivInE.pitches
    (<music21.pitch.Pitch A4>, <music21.pitch.Pitch C#5>, <music21.pitch.Pitch E5>)

    Octaves assigned are arbitrary (generally C-4 or above) and just exist
    to keep the pitches properly sorted.

    Major and minor are written with capital and lowercase numerals respectively.
    Inversions and seventh-, ninth-, etc. chords are specified by putting the
    figured bass symbols directly after the chord.  Keys can be specified with
    Key objects or (less efficiently) a string.

    Dominant-seventh chord in c minor.

    >>> roman.RomanNumeral('V7', 'c').pitches
    (<music21.pitch.Pitch G4>, <music21.pitch.Pitch B4>,
     <music21.pitch.Pitch D5>, <music21.pitch.Pitch F5>)

    Minor chord on the fifth scale degree, in second inversion:

    >>> roman.RomanNumeral('v64', 'c').pitches
    (<music21.pitch.Pitch D4>, <music21.pitch.Pitch G4>, <music21.pitch.Pitch B-4>)


    If no Key is given then it exists as a theoretical, keyless RomanNumeral;
    e.g., V in any key.  But when realized, keyless RomanNumerals are
    treated as if they are in C major.

    >>> V = roman.RomanNumeral('V')
    >>> V.quality
    'major'

    >>> V.inversion()
    0

    >>> V.forteClass
    '3-11B'

    >>> V.scaleDegree
    5

    Default key is C Major

    >>> for p in V.pitches:
    ...     p
    <music21.pitch.Pitch G4>
    <music21.pitch.Pitch B4>
    <music21.pitch.Pitch D5>

    Neapolitan chords can be written as 'N6', 'bII6', or simply 'N'

    >>> neapolitan = roman.RomanNumeral('N6', 'c#')
    >>> neapolitan.key
    <music21.key.Key of c# minor>

    >>> neapolitan.isMajorTriad()
    True

    >>> neapolitan.scaleDegreeWithAlteration
    (2, <music21.pitch.Accidental flat>)

    >>> for p in neapolitan.pitches:
    ...     p
    <music21.pitch.Pitch F#4>
    <music21.pitch.Pitch A4>
    <music21.pitch.Pitch D5>

    >>> neapolitan2 = roman.RomanNumeral('bII6', 'g#')
    >>> [str(p) for p in neapolitan2.pitches]
    ['C#5', 'E5', 'A5']

    >>> neapolitan2.scaleDegree
    2

    Here's another dominant seventh chord in minor:

    >>> em = key.Key('e')
    >>> dominantV = roman.RomanNumeral('V7', em)
    >>> [str(p) for p in dominantV.pitches]
    ['B4', 'D#5', 'F#5', 'A5']

    Now using the older terminology where the case does not determine the
    quality, it becomes a minor-seventh chord:

    >>> minorV = roman.RomanNumeral('V43', em, caseMatters=False)
    >>> [str(p) for p in minorV.pitches]
    ['F#4', 'A4', 'B4', 'D5']

    (We will do this `str(p) for p in` thing enough that let's make a helper function:)

    >>> def cp(rn_in):  # cp = chord pitches
    ...     return [str(p) for p in rn_in.pitches]
    >>> cp(minorV)
    ['F#4', 'A4', 'B4', 'D5']

    In minor -- VII and VI are assumed to refer to the flattened scale degree, while
    vii, viio, viio7, viiø7 and vi, vio, vio7, and viø7 all refer to the sharpened scale
    degree.  To get a minor triad on lowered 6 for instance, you will need to use 'bvi'
    while to get a major triad on raised 6, use '#VI'.

    The actual rule is that if the chord implies minor, diminished, or half-diminished,
    an implied "#" is read before the figure.  Anything else does not add the sharp.
    The lowered (natural minor) is the assumed basic chord.

    >>> majorFlatSeven = roman.RomanNumeral('VII', em)
    >>> cp(majorFlatSeven)
    ['D5', 'F#5', 'A5']

    >>> minorSharpSeven = roman.RomanNumeral('vii', em)
    >>> cp(minorSharpSeven)
    ['D#5', 'F#5', 'A#5']

    >>> majorFlatSix = roman.RomanNumeral('VI', em)
    >>> cp(majorFlatSix)
    ['C5', 'E5', 'G5']

    >>> minorSharpSix = roman.RomanNumeral('vi', em)
    >>> cp(minorSharpSix)
    ['C#5', 'E5', 'G#5']


    These rules can be changed by passing in a `sixthMinor` or `seventhMinor` parameter set to
    a member of :class:`music21.roman.Minor67Default`:

    >>> majorSharpSeven = roman.RomanNumeral('VII', em, seventhMinor=roman.Minor67Default.SHARP)
    >>> cp(majorSharpSeven)
    ['D#5', 'F##5', 'A#5']

    For instance, if you prefer a harmonic minor context where VI (or vi) always refers
    to the lowered 6 and viio (or VII) always refers to the raised 7, send along
    `sixthMinor=roman.Minor67Default.FLAT` and `seventhMinor=roman.Minor67Default.SHARP`

    >>> dimHarmonicSeven = roman.RomanNumeral('viio', em, seventhMinor=roman.Minor67Default.SHARP)
    >>> cp(dimHarmonicSeven)
    ['D#5', 'F#5', 'A5']

    >>> majHarmonicSeven = roman.RomanNumeral('bVII', em, seventhMinor=roman.Minor67Default.SHARP)
    >>> cp(majHarmonicSeven)
    ['D5', 'F#5', 'A5']


    >>> majHarmonicSix = roman.RomanNumeral('VI', em, sixthMinor=roman.Minor67Default.FLAT)
    >>> cp(majHarmonicSix)
    ['C5', 'E5', 'G5']
    >>> minHarmonicSix = roman.RomanNumeral('#vi', em, sixthMinor=roman.Minor67Default.FLAT)
    >>> cp(minHarmonicSix)
    ['C#5', 'E5', 'G#5']

    See the docs for :class:`~music21.roman.Minor67Default` for more information on
    configuring sixth and seventh interpretation in minor
    along with the useful `CAUTIONARY` setting where CAUTIONARY sharp and flat accidentals
    are allowed but not required.

    Either of these is the same way of getting a minor iii in a minor key:

    >>> minoriii = roman.RomanNumeral('iii', em, caseMatters=True)
    >>> cp(minoriii)
    ['G4', 'B-4', 'D5']

    >>> minoriiiB = roman.RomanNumeral('IIIb', em, caseMatters=False)
    >>> cp(minoriiiB)
    ['G4', 'B-4', 'D5']

    `caseMatters=False` will prevent `sixthMinor` or `seventhMinor` from having effect.

    >>> vii = roman.RomanNumeral('viio', 'a', caseMatters=False,
    ...                           seventhMinor=roman.Minor67Default.QUALITY)
    >>> cp(vii)
    ['G5', 'B-5', 'D-6']

    Can also take a scale object, here we build a first-inversion chord
    on the raised-three degree of D-flat major, that is, F#-major (late
    Schubert would be proud.)

    >>> sharp3 = roman.RomanNumeral('#III6', scale.MajorScale('D-'))
    >>> sharp3.scaleDegreeWithAlteration
    (3, <music21.pitch.Accidental sharp>)

    >>> cp(sharp3)
    ['A#4', 'C#5', 'F#5']

    >>> sharp3.figure
    '#III6'

    Figures can be changed and pitches will change. (Caution: there are still some bugs on this
    for extreme edge cases).

    >>> sharp3.figure = 'V'
    >>> cp(sharp3)
    ['A-4', 'C5', 'E-5']

    A diminished chord is specified with an `o` (the letter-O) or `°` symbol:

    >>> leadingToneSeventh = roman.RomanNumeral(
    ...     'viio', scale.MajorScale('F'))
    >>> cp(leadingToneSeventh)
    ['E5', 'G5', 'B-5']
    >>> cp(roman.RomanNumeral('vii°7', 'F'))
    ['E5', 'G5', 'B-5', 'D-6']

    Note in the above example we passed in a Scale object not a Key.  This can be used
    in the theoretical case of applying roman numerals in 7-note scales that are not
    major or minor.  (see the documentation for the
    :attr:`~music21.roman.RomanNumeral.scaleCardinality` attribute for scales other than
    7-note scales).

    Half-diminished seventh chords can be written with either `ø` or `/o` symbol:

    >>> cp(roman.RomanNumeral('viiø7', 'F'))
    ['E5', 'G5', 'B-5', 'D6']
    >>> cp(roman.RomanNumeral('vii/o7', 'F'))
    ['E5', 'G5', 'B-5', 'D6']

    RomanNumeral objects can also be created with an int (number)
    for the scale degree:

    >>> majorKeyObj = key.Key('C')
    >>> roman.RomanNumeral(1, majorKeyObj)
    <music21.roman.RomanNumeral I in C major>

    >>> minorKeyObj = key.Key('c')
    >>> roman.RomanNumeral(1, minorKeyObj)
    <music21.roman.RomanNumeral i in c minor>

    A little modal mixture:

    >>> lessObviousDiminished = roman.RomanNumeral(
    ...     'vio', scale.MajorScale('c'))
    >>> for p in lessObviousDiminished.pitches:
    ...     p
    <music21.pitch.Pitch A4>
    <music21.pitch.Pitch C5>
    <music21.pitch.Pitch E-5>

    >>> diminished7th = roman.RomanNumeral(
    ...     'vio7', scale.MajorScale('c'))
    >>> for p in diminished7th.pitches:
    ...     p
    <music21.pitch.Pitch A4>
    <music21.pitch.Pitch C5>
    <music21.pitch.Pitch E-5>
    <music21.pitch.Pitch G-5>

    >>> diminished7th1stInv = roman.RomanNumeral(
    ...     'vio65', scale.MajorScale('c'))
    >>> for p in diminished7th1stInv.pitches:
    ...     p
    <music21.pitch.Pitch C4>
    <music21.pitch.Pitch E-4>
    <music21.pitch.Pitch G-4>
    <music21.pitch.Pitch A4>

    >>> halfDim7th2ndInv = roman.RomanNumeral(
    ...     'ivø43', scale.MajorScale('F'))
    >>> for p in halfDim7th2ndInv.pitches:
    ...     p
    <music21.pitch.Pitch F-4>
    <music21.pitch.Pitch A-4>
    <music21.pitch.Pitch B-4>
    <music21.pitch.Pitch D-5>

    >>> alteredChordHalfDim3rdInv = roman.RomanNumeral(
    ...     'biiø42', scale.MajorScale('F'))
    >>> cp(alteredChordHalfDim3rdInv)
    ['F-4', 'G-4', 'B--4', 'D--5']

    >>> alteredChordHalfDim3rdInv.intervalVector
    [0, 1, 2, 1, 1, 1]

    >>> alteredChordHalfDim3rdInv.commonName
    'half-diminished seventh chord'

    >>> alteredChordHalfDim3rdInv.romanNumeral
    'bii'

    >>> alteredChordHalfDim3rdInv.romanNumeralAlone
    'ii'

    Tones may be omitted by putting the number in a bracketed [noX] clause.
    These numbers refer to the note above the root, not above the bass:

    >>> openFifth = roman.RomanNumeral('V[no3]', key.Key('F'))
    >>> openFifth.pitches
    (<music21.pitch.Pitch C5>, <music21.pitch.Pitch G5>)
    >>> openFifthInv = roman.RomanNumeral('V64[no3]', key.Key('F'))
    >>> openFifthInv.pitches
    (<music21.pitch.Pitch G4>, <music21.pitch.Pitch C5>)

    Some theoretical traditions express a viio7 as a V9 chord with omitted
    root. Music21 allows that:

    >>> fiveOhNine = roman.RomanNumeral('V9[no1]', key.Key('g'))
    >>> cp(fiveOhNine)
    ['F#5', 'A5', 'C6', 'E-6']

    Putting [no] or [add] should never change the root

    >>> fiveOhNine.root()
    <music21.pitch.Pitch D5>

    Tones may be added by putting a number (with an optional accidental) in
    a bracketed [addX] clause:

    >>> susChord = roman.RomanNumeral('I[add4][no3]', key.Key('C'))
    >>> susChord.pitches
    (<music21.pitch.Pitch C4>, <music21.pitch.Pitch F4>, <music21.pitch.Pitch G4>)
    >>> susChord.root()
    <music21.pitch.Pitch C4>

    Figures such as 'V54' give the same result:

    >>> anotherSus = roman.RomanNumeral('V54', key.Key('C'))
    >>> anotherSus.pitches
    (<music21.pitch.Pitch G4>, <music21.pitch.Pitch C5>, <music21.pitch.Pitch D5>)

    Putting it all together:

    >>> weirdChord = roman.RomanNumeral('V65[no5][add#6][b3]', key.Key('C'))
    >>> cp(weirdChord)
    ['B-4', 'E#5', 'F5', 'G5']
    >>> weirdChord.root()
    <music21.pitch.Pitch G5>

    Other scales besides major and minor can be used.
    Just for kicks (no worries if this is goobley-gook):

    >>> ots = scale.OctatonicScale('C2')
    >>> rn_I9 = roman.RomanNumeral('I9', ots, caseMatters=False)
    >>> cp(rn_I9)
    ['C2', 'E-2', 'G-2', 'A2', 'C3']

    >>> romanNumeral2 = roman.RomanNumeral(
    ...     'V7#5b3', ots, caseMatters=False)
    >>> cp(romanNumeral2)
    ['G-2', 'A-2', 'C#3', 'E-3']

    >>> rn_minor_64_secondary = roman.RomanNumeral('v64/V', key.Key('e'))
    >>> rn_minor_64_secondary
    <music21.roman.RomanNumeral v64/V in e minor>

    >>> rn_minor_64_secondary.figure
    'v64/V'

    >>> cp(rn_minor_64_secondary)
    ['C#5', 'F#5', 'A5']

    >>> rn_minor_64_secondary.secondaryRomanNumeral
    <music21.roman.RomanNumeral V in e minor>

    Dominant 7ths can be specified by the character 'd' followed by the figure
    indicating the inversion of the chord:

    >>> r = roman.RomanNumeral('bVIId7', key.Key('B-'))
    >>> r.figure
    'bVIId7'

    >>> cp(r)
    ['A-5', 'C6', 'E-6', 'G-6']

    >>> r = roman.RomanNumeral('VId42')
    >>> r.figure
    'VId42'

    >>> r.key = key.Key('B-')
    >>> cp(r)
    ['F5', 'G5', 'B5', 'D6']

    >>> r = roman.RomanNumeral('IVd43', key.Key('B-'))
    >>> r.figure
    'IVd43'

    >>> cp(r)
    ['B-4', 'D-5', 'E-5', 'G5']

    >>> r2 = roman.RomanNumeral('V42/V7/vi', key.Key('C'))
    >>> cp(r2)
    ['A4', 'B4', 'D#5', 'F#5']

    >>> r2.secondaryRomanNumeral
    <music21.roman.RomanNumeral V7/vi in C major>

    >>> r2.secondaryRomanNumeral.secondaryRomanNumeral
    <music21.roman.RomanNumeral vi in C major>


    The I64 chord can also be specified as Cad64, which
    simply parses as I64:

    >>> r = roman.RomanNumeral('Cad64', key.Key('C'))
    >>> r
    <music21.roman.RomanNumeral Cad64 in C major>
    >>> cp(r)
    ['G4', 'C5', 'E5']

    >>> r = roman.RomanNumeral('Cad64', key.Key('c'))
    >>> r
    <music21.roman.RomanNumeral Cad64 in c minor>
    >>> cp(r)
    ['G4', 'C5', 'E-5']

    Works also for secondary romans:

    >>> r = roman.RomanNumeral('Cad64/V', key.Key('c'))
    >>> r
    <music21.roman.RomanNumeral Cad64/V in c minor>
    >>> cp(r)
    ['D5', 'G5', 'B5']


    In a major context, i7 and iv7 and their inversions are treated as minor-7th
    chords:

    >>> r = roman.RomanNumeral('i7', 'C')
    >>> r
    <music21.roman.RomanNumeral i7 in C major>
    >>> cp(r)
    ['C4', 'E-4', 'G4', 'B-4']

    >>> r = roman.RomanNumeral('iv42', 'C')
    >>> cp(r)
    ['E-4', 'F4', 'A-4', 'C5']

    For a minor-Major 7th chord in major, write it as i[add7] or i7[#7] or another inversion:

    >>> minorMajor = roman.RomanNumeral('i[add7]', 'C')
    >>> minorMajor
    <music21.roman.RomanNumeral i[add7] in C major>
    >>> cp(minorMajor)
    ['C4', 'E-4', 'G4', 'B4']
    >>> cp(roman.RomanNumeral('i7[#7]', 'C'))
    ['C4', 'E-4', 'G4', 'B4']

    Note that this is not the same as i#7, which gives a rather unusual chord in major.

    >>> cp(roman.RomanNumeral('i#7', 'C'))
    ['C4', 'E-4', 'G4', 'B#4']

    In minor, it's just fine.  I mean, just as fine:

    >>> cp(roman.RomanNumeral('i#7', 'c'))
    ['C4', 'E-4', 'G4', 'B4']


    >>> cp(roman.RomanNumeral('i42[#7]', 'C'))
    ['B4', 'C5', 'E-5', 'G5']

    As noted above, Minor-Major 7th chords in minor have a different form in root position:

    >>> cp(roman.RomanNumeral('i#7', 'c'))
    ['C4', 'E-4', 'G4', 'B4']

    (these are both the same)

    >>> cp(roman.RomanNumeral('i#753', 'c'))
    ['C4', 'E-4', 'G4', 'B4']
    >>> cp(roman.RomanNumeral('i7[#7]', 'c'))
    ['C4', 'E-4', 'G4', 'B4']


    Other inversions are the same as with major keys:

    >>> cp(roman.RomanNumeral('i65[#7]', 'c'))
    ['E-4', 'G4', 'B4', 'C5']
    >>> cp(roman.RomanNumeral('i43[#7]', 'c'))
    ['G4', 'B4', 'C5', 'E-5']



    The RomanNumeral constructor accepts a keyword 'updatePitches' which is
    passed to harmony.Harmony. By default, it
    is `True`, but can be set to `False` to initialize faster if pitches are not needed.

    >>> r = roman.RomanNumeral('vio', em, updatePitches=False)
    >>> r.pitches
    ()

    **Equality**

    Two RomanNumerals compare equal if their `NotRest` components
    (noteheads, beams, expressions, articulations, etc.) are equal
    and if their figures and keys are equal:

    >>> c1 = chord.Chord('C4 E4 G4 C5')
    >>> c2 = chord.Chord('C3 E4 G4')
    >>> rn1 = roman.romanNumeralFromChord(c1, 'C')
    >>> rn2 = roman.romanNumeralFromChord(c2, 'C')
    >>> rn1 == rn2
    True
    >>> rn1.duration.type = 'half'
    >>> rn1 == rn2
    False
    >>> rn3 = roman.RomanNumeral('I', 'd')
    >>> rn2 == rn3
    False
    >>> rn3.key = key.Key('C')
    >>> rn2 == rn3
    True
    >>> rn4 = roman.RomanNumeral('ii', 'C')
    >>> rn2 == rn4
    False
    >>> rn4.figure = 'I'
    >>> rn2 == rn4
    True

    >>> rn5 = roman.RomanNumeral('bII6', 'c')
    >>> rn6 = roman.RomanNumeral('bII6', 'c')
    >>> rn5 == rn6
    True
    >>> rn7 = roman.RomanNumeral('N6', 'c')
    >>> rn5 == rn7
    False


    * Changed in v6.5: caseMatters is keyword only. It along with sixthMinor and
      seventhMinor are now the only allowable keywords to pass in.
    * Changed in v7: RomanNumeral.romanNumeral will always give a "b" for a flattened
      degree (i.e., '-II' becomes 'bII') as this is what people expect in looking at
      the figure.

    * Changed in v7.3: figures that are not normally used to indicate inversion
      such as V54 (a suspension) no longer give strange inversions.

    * Changed in v8: Figures are now validated as alphanumeric or containing one of
      the following symbols (after the example "V"):

    >>> specialCharacterFigure = roman.RomanNumeral('V#+-/[]')
    >>> specialCharacterFigure
    <music21.roman.RomanNumeral V#+-/[]>

    And degree symbols (`°`) convert to `o`:

    >>> dimSeventh = roman.RomanNumeral('vii°7', 'c')
    >>> dimSeventh
    <music21.roman.RomanNumeral viio7 in c minor>

    Otherwise, an invalid figure raises `RomanNumeralException`:

    >>> roman.RomanNumeral("V64==53")
    Traceback (most recent call last):
    music21.roman.RomanNumeralException: Invalid figure: V64==53

    OMIT_FROM_DOCS

    Things that were giving us trouble:

    >>> dminor = key.Key('d')
    >>> rn = roman.RomanNumeral('iiø65', dminor)
    >>> cp(rn)
    ['G4', 'B-4', 'D5', 'E5']

    >>> rn.romanNumeral
    'ii'

    >>> rn3 = roman.RomanNumeral('III', dminor)
    >>> cp(rn3)
    ['F4', 'A4', 'C5']

    Should be the same as above no matter when the key is set:

    >>> r = roman.RomanNumeral('VId7', key.Key('B-'))
    >>> cp(r)
    ['G5', 'B5', 'D6', 'F6']

    >>> r.key = key.Key('B-')
    >>> cp(r)
    ['G5', 'B5', 'D6', 'F6']

    This was getting B-flat.

    >>> r = roman.RomanNumeral('VId7')
    >>> r.key = key.Key('B-')
    >>> cp(r)
    ['G5', 'B5', 'D6', 'F6']

    >>> r = roman.RomanNumeral('IVd6/5')
    >>> r.key = key.Key('Eb')
    >>> cp(r)
    ['C5', 'E-5', 'G-5', 'A-5']

    >>> r = roman.RomanNumeral('vio', em)
    >>> cp(r)
    ['C#5', 'E5', 'G5']

    We can omit an arbitrary number of steps:

    >>> r = roman.RomanNumeral('Vd7[no3no5no7]', key.Key('C'))
    >>> cp(r)
    ['G4']

    Was setting a root of D5:

    >>> r = roman.RomanNumeral('V754', key.Key('C'))
    >>> cp(r)
    ['G4', 'C5', 'D5', 'F5']

    A symbol that looks like the degree symbol but isn't:

    >>> roman.RomanNumeral('viiº')
    <music21.roman.RomanNumeral viio>

    (NOTE: all this is omitted -- look at OMIT_FROM_DOCS above)
    '''
    equalityAttributes = ('figure', 'key')

    # TODO: document better! what is inherited and what is new?
    _alterationRegex = re.compile(r'^(b+|-+|#+)')
    _omittedStepsRegex = re.compile(r'(\[(no[1-9]+)+]\s*)+')
    _addedStepsRegex = re.compile(r'\[add(b*|-*|#*)(\d+)+]\s*')
    _bracketedAlterationRegex = re.compile(r'\[(b+|-+|#+)(\d+)]')
    _augmentedSixthRegex = re.compile(r'(It|Ger|Fr|Sw)\+?')
    _romanNumeralAloneRegex = re.compile(r'(IV|I{1,3}|VI{0,2}|iv|i{1,3}|vi{0,2}|N)')
    _secondarySlashRegex = re.compile(r'(.*?)/([#a-np-zA-NP-Z].*)')
    _aug6defaultInversions = {'It': '6', 'Fr': '43', 'Ger': '65', 'Sw': '43'}
    _slashedAug6Inv = re.compile(r'(\d)/(\d)')

    _DOC_ATTR: dict[str, str] = {
        'addedSteps': '''
            Returns a list of the added steps, each as a tuple of
            modifier as a string (which might be empty) and a chord factor as an int.

            >>> rn = roman.RomanNumeral('V7[addb6]', 'C')
            >>> rn.addedSteps
            [('-', 6)]
            >>> rn.pitches
            (<music21.pitch.Pitch G4>,
             <music21.pitch.Pitch B4>,
             <music21.pitch.Pitch D5>,
             <music21.pitch.Pitch E-5>,
             <music21.pitch.Pitch F5>)

            You can add multiple added steps:

            >>> strange = roman.RomanNumeral('V7[addb6][add#6][add-8]')
            >>> strange.addedSteps
            [('-', 6), ('#', 6), ('-', 8)]
            >>> ' '.join([p.nameWithOctave for p in strange.pitches])
            'G4 B4 D5 E-5 E#5 F5 G-5'

            NOTE: The modifier name is currently changed from 'b' to '-', but
            this might change in a future version to match `bracketedAlteration`.
            ''',
        'bracketedAlterations': '''
            Returns a list of the bracketed alterations, each as a tuple of
            modifier as a string and a chord factor as an int.

            >>> rn = roman.RomanNumeral('V7[b5]')
            >>> rn.bracketedAlterations
            [('b', 5)]
            >>> rn.pitches
            (<music21.pitch.Pitch G4>,
             <music21.pitch.Pitch B4>,
             <music21.pitch.Pitch D-5>,
             <music21.pitch.Pitch F5>)

            NOTE: The bracketed alteration name is currently left as 'b', but
            this might change in a future version to match `addedSteps`.

            The difference between a bracketed alteration and just
            putting b5 in is that, a bracketed alteration changes
            notes already present in a chord and does not imply that
            the normally present notes would be missing.  Here, the
            presence of 7 and b5 means that no 3rd should appear.

            >>> rn2 = roman.RomanNumeral('V7b5')
            >>> rn2.bracketedAlterations
            []
            >>> len(rn2.pitches)
            3
            >>> [p.name for p in rn2.pitches]
            ['G', 'D-', 'F']

            * Changed in v6.5: always returns a list, even if it is empty.
            ''',
        'caseMatters': '''
            Boolean to determine whether the case (upper or lowercase) of the
            figure determines whether it is major or minor.  Defaults to True;
            not everything has been tested with False yet.

            >>> roman.RomanNumeral('viiø7', 'd').caseMatters
            True
            ''',
        'figuresWritten': '''
            Returns a string containing any figured-bass figures as passed in:

            >>> roman.RomanNumeral('V65').figuresWritten
            '65'
            >>> roman.RomanNumeral('V').figuresWritten
            ''
            >>> roman.RomanNumeral('Fr43', 'c').figuresWritten
            '43'
            >>> roman.RomanNumeral('I7#5b3').figuresWritten
            '7#5b3'

            Note that the `o` and `ø` symbols are quality designations and not
            figures:

            >>> roman.RomanNumeral('viio6').figuresWritten
            '6'
            >>> roman.RomanNumeral('viiø7').figuresWritten
            '7'
            ''',
        'figuresNotationObj': '''
            Returns a :class:`~music21.figuredBass.notation.Notation` object
            that represents the figures in a RomanNumeral

            >>> rn = roman.RomanNumeral('V65')
            >>> notationObj = rn.figuresNotationObj
            >>> notationObj
            <music21.figuredBass.notation.Notation 6,5>
            >>> notationObj.numbers
            (6, 5, 3)

            >>> rn = roman.RomanNumeral('Ib75#3')
            >>> notationObj = rn.figuresNotationObj
            >>> notationObj.numbers
            (7, 5, 3)
            >>> notationObj.modifiers
            (<music21.figuredBass.notation.Modifier b flat>,
             <music21.figuredBass.notation.Modifier None None>,
             <music21.figuredBass.notation.Modifier # sharp>)
            ''',
        'frontAlterationAccidental': '''
            An optional :class:`~music21.pitch.Accidental` object
            representing the chromatic alteration of a RomanNumeral, if any

            >>> roman.RomanNumeral('bII43/vi', 'C').frontAlterationAccidental
            <music21.pitch.Accidental flat>

            >>> roman.RomanNumeral('##IV').frontAlterationAccidental
            <music21.pitch.Accidental double-sharp>

            For most roman numerals this will be None:

            >>> roman.RomanNumeral('V', 'f#').frontAlterationAccidental

            Changing this value will not change existing pitches.

            * Changed in v6.5: always returns a string, never None
            ''',
        'frontAlterationString': '''
            A string representing the chromatic alteration of a RomanNumeral, if any

            >>> roman.RomanNumeral('bII43/vi', 'C').frontAlterationString
            'b'
            >>> roman.RomanNumeral('V', 'f#').frontAlterationString
            ''

            Changing this value will not change existing pitches.

            * Changed in v6.5: always returns a string, never None
            ''',
        'frontAlterationTransposeInterval': '''
            An optional :class:`~music21.interval.Interval` object
            representing the transposition of a chromatically altered chord from
            the normal scale degree:

            >>> sharpFour = roman.RomanNumeral('#IV', 'C')
            >>> sharpFour.frontAlterationTransposeInterval
            <music21.interval.Interval A1>
            >>> sharpFour.frontAlterationTransposeInterval.niceName
            'Augmented Unison'

            Flats, as in this Neapolitan (bII6) chord, are given as diminished unisons:

            >>> roman.RomanNumeral('N6', 'C').frontAlterationTransposeInterval
            <music21.interval.Interval d1>

            Most RomanNumerals will have None and not a perfect unison for this value
            (this is for the speed of creating objects)

            >>> intv = roman.RomanNumeral('V', 'e-').frontAlterationTransposeInterval
            >>> intv is None
            True

            Changing this value will not change existing pitches.
            ''',
        'impliedQuality': '''
            The quality of the chord implied by the figure:

            >>> roman.RomanNumeral('V', 'C').impliedQuality
            'major'
            >>> roman.RomanNumeral('ii65', 'C').impliedQuality
            'minor'
            >>> roman.RomanNumeral('viio7', 'C').impliedQuality
            'diminished'

            The impliedQuality can differ from the actual quality
            if there are not enough notes to satisfy the implied quality,
            as in this half-diminished chord on vii which does not also
            have a seventh:

            >>> incorrectSeventh = roman.RomanNumeral('vii/o', 'C')
            >>> incorrectSeventh.impliedQuality
            'half-diminished'
            >>> incorrectSeventh.quality
            'diminished'

            >>> powerChordMinor = roman.RomanNumeral('v[no3]', 'C')
            >>> powerChordMinor.impliedQuality
            'minor'
            >>> powerChordMinor.quality
            'other'

            If case does not matter then an empty quality is implied:

            >>> roman.RomanNumeral('II', 'C', caseMatters=False).impliedQuality
            ''

            ''',
        'impliedScale': '''
            If no key or scale is passed in as the second object, then
            impliedScale will be set to C major:

            >>> roman.RomanNumeral('V').impliedScale
            <music21.scale.MajorScale C major>

            Otherwise this will be empty:

            >>> roman.RomanNumeral('V', key.Key('D')).impliedScale
            ''',
        'omittedSteps': '''
            A list of integers showing chord factors that have been
            specifically omitted:

            >>> emptyNinth = roman.RomanNumeral('V9[no7][no5]', 'C')
            >>> emptyNinth.omittedSteps
            [7, 5]
            >>> emptyNinth.pitches
            (<music21.pitch.Pitch G4>,
             <music21.pitch.Pitch B4>,
             <music21.pitch.Pitch A5>)

            Usually an empty list:

            >>> roman.RomanNumeral('IV6').omittedSteps
            []
            ''',
        'pivotChord': '''
            Defaults to None; if not None, stores another interpretation of the
            same RN in a different key; stores a RomanNumeral object.

            While not enforced, for consistency the pivotChord should be
            the new interpretation going forward (to the right on the staff)

            >>> rn = roman.RomanNumeral('V7/IV', 'C')
            >>> rn.pivotChord is None
            True
            >>> rn.pivotChord = roman.RomanNumeral('V7', 'F')
            ''',
        'primaryFigure': '''
            A string representing everything before the slash
            in a RomanNumeral with applied chords.  In other roman numerals
            it is the same as `figure`:

            >>> rn = roman.RomanNumeral('bII43/vi', 'C')
            >>> rn.primaryFigure
            'bII43'

            >>> rnSimple = roman.RomanNumeral('V6', 'a')
            >>> rnSimple.primaryFigure
            'V6'

            Changing this value will not change existing pitches.
            ''',
        'romanNumeralAlone': '''
            Returns a string of just the roman numeral part (I-VII or i-vii) of
            the figure:

            >>> roman.RomanNumeral('V6').romanNumeralAlone
            'V'

            Chromatic alterations and secondary numerals are omitted:

            >>> rn = roman.RomanNumeral('#II7/vi', 'C')
            >>> rn.romanNumeralAlone
            'II'

            Neapolitan chords are changed to 'II':

            >>> roman.RomanNumeral('N6').romanNumeralAlone
            'II'

            Currently augmented-sixth chords return the "national" base.  But this
            behavior may change in future versions:

            >>> roman.RomanNumeral('It6').romanNumeralAlone
            'It'
            >>> roman.RomanNumeral('Ger65').romanNumeralAlone
            'Ger'

            This will be controversial in some circles, but it's based on a root in
            isolation, and does not imply tonic quality:

            >>> roman.RomanNumeral('Cad64').romanNumeralAlone
            'I'
            ''',
        'scaleCardinality': '''
            Stores how many notes are in the scale; defaults to 7 for diatonic, obviously.

            >>> roman.RomanNumeral('IV', 'a').scaleCardinality
            7

            Probably you should not need to change this.  And most code is untested
            with other cardinalities.  But it is (in theory) possible to create
            roman numerals on octatonic scales, etc.

            Changing this value will not change existing pitches.
            ''',
        'scaleDegree': '''
            An int representing what degree of the scale the figure
            (or primary figure in the case of secondary/applied numerals)
            is on.  Discounts any front alterations:

            >>> roman.RomanNumeral('vi', 'E').scaleDegree
            6

            Note that this is 2, not 1.5 or 6 or 6.5 or something like that:

            >>> roman.RomanNumeral('bII43/vi', 'C').scaleDegree
            2

            Empty RomanNumeral objects have the special scaleDegree of 0:

            >>> roman.RomanNumeral().scaleDegree
            0

            Changing this value will not change existing pitches.

            * Changed in v6.5: empty RomanNumeral objects get scaleDegree 0, not None.
            ''',
        'secondaryRomanNumeral': '''
            An optional roman.RomanNumeral object that represents the part
            after the slash in a secondary/applied RomanNumeral object.  For instance,
            in the roman numeral, `C: V7/vi`, the `secondaryRomanNumeral` would be
            the roman numeral `C: vi`.  The key of the `secondaryRomanNumeral`
            is the key of the original RomanNumeral.  In cases such as
            V/V/V, the `secondaryRomanNumeral` can itself have a
            `secondaryRomanNumeral`.

            >>> rn = roman.RomanNumeral('V7/vi', 'C')
            >>> rn.secondaryRomanNumeral
            <music21.roman.RomanNumeral vi in C major>
            ''',
        'secondaryRomanNumeralKey': '''
            An optional key.Key object for secondary/applied RomanNumeral that
            represents the key that the part of the figure *before* the slash
            will be interpreted in.  For instance in the roman numeral,
            `C: V7/vi`, the `secondaryRomanNumeralKey` would be `a minor`, since
            the vi (submediant) refers to an a-minor triad, and thus the `V7`
            part is to be read as the dominant seventh in `a minor`.

            >>> rn = roman.RomanNumeral('V7/vi', 'C')
            >>> rn.secondaryRomanNumeralKey
            <music21.key.Key of a minor>
            ''',
        'seventhMinor': '''
            How should vii, viio,  and VII be parsed in minor?
            Defaults to Minor67Default.QUALITY.

            This value should be passed into the constructor initially.
            Changing it after construction will not change the pitches.
            ''',
        'sixthMinor': '''
            How should vi, vio and VI be parsed in minor?
            Defaults to Minor67Default.QUALITY.

            This value should be passed into the constructor initially.
            Changing it after construction will not change the pitches.
            ''',
        'useImpliedScale': '''
            A boolean indicating whether an implied scale is being used:

            >>> roman.RomanNumeral('V').useImpliedScale
            True
            >>> roman.RomanNumeral('V', 'A').useImpliedScale
            False
            ''',
    }

    # INITIALIZER #

    def __init__(
        self,
        figure: str|int = '',
        keyOrScale: key.Key|scale.ConcreteScale|str|None = None,
        *,
        caseMatters=True,
        updatePitches=True,
        sixthMinor=Minor67Default.QUALITY,
        seventhMinor=Minor67Default.QUALITY,
        **keywords,
    ):
        self.primaryFigure: str = ''
        self.secondaryRomanNumeral: RomanNumeral|None = None
        self.secondaryRomanNumeralKey: key.Key|None = None

        self.pivotChord: RomanNumeral|None = None
        self.caseMatters: bool = caseMatters
        self.scaleCardinality: int = 7

        if isinstance(figure, int):
            figure = common.toRoman(figure)
            if self.caseMatters:
                mode = ''
                if isinstance(keyOrScale, key.Key):
                    mode = keyOrScale.mode
                elif isinstance(keyOrScale, scale.DiatonicScale):
                    mode = keyOrScale.type
                elif isinstance(keyOrScale, str) and keyOrScale:
                    mode = 'major' if keyOrScale[0].isupper() else 'minor'
                if (
                    (mode == 'major' and figure in ('II', 'III', 'VI', 'VII'))
                    or (mode == 'minor' and figure in ('I', 'II', 'IV', 'V'))
                ):
                    figure = figure.lower()

        # immediately fix low-preference figures
        if isinstance(figure, str):
            figure = re.sub(r'(?<!\d)0', 'o', figure)  # viio7 (but don't alter 10.)
            figure = figure.replace('º', 'o')
            figure = figure.replace('°', 'o')
            # /o is just a shorthand for ø -- so it should not be stored.
            figure = figure.replace('/o', 'ø')
        else:
            raise TypeError(f'Expected str or int: got {type(figure)}')
        # end immediate fixes

        if not all(char.isalnum() or char in '#°+-/[]' for char in figure):
            # V, b, ø, no, etc. already covered by isalnum()
            raise RomanNumeralException(f'Invalid figure: {figure}')

        # Store raw figure before calling setKeyOrScale:
        self._figure = figure
        # This is set when _setKeyOrScale() is called:
        self._scale = None
        self.scaleDegree: int = 0
        self.frontAlterationString: str = ''
        self.frontAlterationTransposeInterval: interval.Interval|None = None
        self.frontAlterationAccidental: pitch.Accidental|None = None
        self.romanNumeralAlone: str = ''
        self.figuresWritten: str = ''
        self.figuresNotationObj: fbNotation.Notation = _NOTATION_SINGLETON
        if not figure:
            self.figuresNotationObj = fbNotation.Notation()  # do not allow changing singleton

        self.impliedQuality: str = ''

        self.impliedScale: scale.ConcreteScale|None = None
        self.useImpliedScale: bool = False
        self.bracketedAlterations: list[tuple[str, int]] = []
        self.omittedSteps: list[int] = []
        self.addedSteps: list[tuple[str, int]] = []
        # do not update pitches.
        self._parsingComplete = False
        self.key = keyOrScale
        self.sixthMinor = sixthMinor
        self.seventhMinor = seventhMinor

        super().__init__(figure, updatePitches=updatePitches, **keywords)
        self.writeAsChord = True  # override from Harmony/ChordSymbol
        self._parsingComplete = True
        self._functionalityScore: int|None = None
        self.followsKeyChange: bool = False

    def __eq__(self, other):
        '''
        Compare equality, just based on NotRest and on figure and key
        '''
        # NotRest == will be used, but the equality attributes of RomanNumeral
        # will be picked up as well.
        return note.NotRest.__eq__(self, other)

    def __hash__(self):
        return id(self) >> 4

    def _reprInternal(self):
        if hasattr(self.key, 'tonic'):
            return str(self.figureAndKey)
        else:
            return self.figure

    # PRIVATE METHODS #
    def _parseFigure(self):
        '''
        Parse the .figure object into its component parts.

        Called from the superclass, Harmony.__init__()
        '''
        if not isinstance(self._figure, str):  # pragma: no cover
            raise RomanNumeralException(f'got a non-string figure: {self._figure!r}')

        if self.useImpliedScale:
            useScale = self.impliedScale
        else:
            useScale = self._scale

        (workingFigure, useScale) = self._correctForSecondaryRomanNumeral(useScale)

        if workingFigure == 'Cad64':
            # since useScale can be a scale, it might not have a mode
            if hasattr(useScale, 'mode') and useScale.mode == 'minor':
                workingFigure = 'i64'
            else:
                workingFigure = 'I64'

        self.primaryFigure = workingFigure

        workingFigure = self._parseOmittedSteps(workingFigure)
        workingFigure = self._parseAddedSteps(workingFigure)
        workingFigure = self._parseBracketedAlterations(workingFigure)

        # Replace Neapolitan indication.
        workingFigure = re.sub('^N6', 'bII6', workingFigure)
        workingFigure = re.sub('^N53', 'bII', workingFigure)  # Root position must be explicit
        workingFigure = re.sub('^N', 'bII6', workingFigure)  # First inversion assumed otherwise

        workingFigure = self._parseFrontAlterations(workingFigure)
        workingFigure, useScale = self._parseRNAloneAmidstAug6(workingFigure, useScale)
        workingFigure = self._setImpliedQualityFromString(workingFigure)
        workingFigure = self._adjustMinorVIandVIIByQuality(workingFigure, useScale)

        self.figuresWritten = workingFigure
        shFig = ','.join(expandShortHand(workingFigure))
        self.figuresNotationObj = fbNotation.Notation(shFig)

    def _setImpliedQualityFromString(self, workingFigure: str) -> str:
        # major, minor, augmented, or diminished (and half-diminished for 7ths)
        impliedQuality = ''
        # impliedQualitySymbol = ''
        if workingFigure.startswith('o') or workingFigure.startswith('°'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'diminished'
            # impliedQualitySymbol = 'o'
        elif workingFigure.startswith('/o'):
            workingFigure = workingFigure[2:]
            impliedQuality = 'half-diminished'
            # impliedQualitySymbol = 'ø'
        elif workingFigure.startswith('ø'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'half-diminished'
            # impliedQualitySymbol = 'ø'
        elif workingFigure.startswith('+'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'augmented'
            # impliedQualitySymbol = '+'
        elif 'd' in workingFigure:
            m = re.match(r'(?P<leading>.*)d(?P<figure>7|6/?5|4/?3|4/?2|2)$', workingFigure)
            if m is None:
                raise RomanNumeralException(
                    f'Cannot make a dominant-seventh chord out of {workingFigure}. '
                    "Figure should be in ('7', '65', '43', '42', '2').")
            # this one is different
            workingFigure = m.group('leading') + m.group('figure')
            impliedQuality = 'dominant-seventh'
            # impliedQualitySymbol = '(dom7)'
        elif self.caseMatters and self.romanNumeralAlone.upper() == self.romanNumeralAlone:
            impliedQuality = 'major'
        elif self.caseMatters and self.romanNumeralAlone.lower() == self.romanNumeralAlone:
            impliedQuality = 'minor'
        self.impliedQuality = impliedQuality
        return workingFigure

    def _correctBracketedPitches(self) -> None:
        # correct bracketed figures
        if not self.bracketedAlterations:
            return
        for (alterNotation, chordStep) in self.bracketedAlterations:
            alterNotation = re.sub('b', '-', alterNotation)
            try:
                alterPitch = self.getChordStep(chordStep)
            except chord.ChordException:
                continue  # can happen for instance in It6 with updatePitches=False
            if alterPitch is not None:
                newAccidental = pitch.Accidental(alterNotation)
                if alterPitch.accidental is None:
                    alterPitch.accidental = newAccidental
                else:
                    alterPitch.accidental.set(alterPitch.accidental.alter + newAccidental.alter)

    def _findSemitoneSizeForQuality(self, impliedQuality: str) -> tuple[int, ...]:
        '''
        Given an implied quality, return the number of semitones that should be included.

        Relies entirely on impliedQuality. Note that in the case of 'diminished'
        it could be either diminished triad or diminished seventh. We return for diminished
        seventh since a missing chordStep for the 7th degree doesn't affect the processing.

        Returns a tuple of 2 or 3 length showing the number of
        semitones for third, fifth, [seventh]
        or the empty tuple () if not found.

        >>> r = roman.RomanNumeral()
        >>> r._findSemitoneSizeForQuality('major')
        (4, 7)
        >>> r._findSemitoneSizeForQuality('minor')
        (3, 7)
        >>> r._findSemitoneSizeForQuality('half-diminished')
        (3, 6, 10)
        >>> r._findSemitoneSizeForQuality('augmented')
        (4, 8)
        >>> r._findSemitoneSizeForQuality('dominant-seventh')
        (4, 7, 10)
        >>> r._findSemitoneSizeForQuality('not-a-quality')
        ()
        >>> r._findSemitoneSizeForQuality('diminished')
        (3, 6, 9)

        OMIT_FROM_DOCS

        This one is not currently used.

        >>> r._findSemitoneSizeForQuality('minor-seventh')
        (3, 7, 10)

        (This is in OMIT_FROM_etc.)
        '''
        correctSemitones: tuple[int, ...]
        if impliedQuality == 'major':
            correctSemitones = (4, 7)
        elif impliedQuality == 'minor':
            correctSemitones = (3, 7)
        elif impliedQuality == 'diminished':
            correctSemitones = (3, 6, 9)
        elif impliedQuality == 'half-diminished':
            correctSemitones = (3, 6, 10)
        elif impliedQuality == 'augmented':
            correctSemitones = (4, 8)
        elif impliedQuality == 'minor-seventh':
            correctSemitones = (3, 7, 10)
        elif impliedQuality == 'dominant-seventh':
            correctSemitones = (4, 7, 10)
        else:
            correctSemitones = ()

        return correctSemitones

    def _matchAccidentalsToQuality(self, impliedQuality: str) -> None:
        '''
        Fixes notes that should be out of the scale
        based on what the chord "impliedQuality" (major, minor, augmented,
        diminished) by changing their accidental.

        An intermediary step in parsing figures.

        >>> r = roman.RomanNumeral()
        >>> r.pitches = ['C4', 'E4', 'G4']
        >>> r._matchAccidentalsToQuality('minor')
        >>> ' '.join([p.name for p in r.pitches])
        'C E- G'
        >>> r._matchAccidentalsToQuality('augmented')
        >>> ' '.join([p.name for p in r.pitches])
        'C E G#'
        >>> r._matchAccidentalsToQuality('diminished')
        >>> ' '.join([p.name for p in r.pitches])
        'C E- G-'
        >>> r.pitches = ['C4', 'E4', 'G4', 'B4']
        >>> r._matchAccidentalsToQuality('diminished')
        >>> ' '.join([p.name for p in r.pitches])
        'C E- G- B--'

        This was a problem before:

        >>> r.pitches = ['C4', 'E4', 'G4', 'B#4']
        >>> r._matchAccidentalsToQuality('diminished')
        >>> ' '.join([p.name for p in r.pitches])
        'C E- G- B--'
        '''
        def correctFaultyPitch(faultyPitch: pitch.Pitch, inner_correctedSemis: int):
            if inner_correctedSemis >= 6:
                inner_correctedSemis = -1 * (12 - inner_correctedSemis)
            elif inner_correctedSemis <= -6:
                inner_correctedSemis += 12

            if faultyPitch.accidental is None:
                faultyPitch.accidental = pitch.Accidental(inner_correctedSemis)
            else:
                acc = faultyPitch.accidental
                inner_correctedSemis += int(acc.alter)  # no quarter tones here.
                if inner_correctedSemis >= 6:
                    inner_correctedSemis = -1 * (12 - inner_correctedSemis)
                elif inner_correctedSemis <= -6:
                    inner_correctedSemis += 12

                acc.set(inner_correctedSemis)

        def shouldSkipThisChordStep(chordStep: int) -> bool:
            '''
            Skip adjusting chordSteps with explicit accidentals.

            For a figure like V7b5, make sure not to correct the b5 back,
            even though the implied quality requires a Perfect 5th.
            '''
            for figure in self.figuresNotationObj.figures:
                if (figure.number == chordStep
                        and figure.modifier.accidental is not None
                        and figure.modifier.accidental.alter != 0):
                    return True
            return False


        correctSemitones = self._findSemitoneSizeForQuality(impliedQuality)
        chordStepsToExamine = (3, 5, 7)
        # newPitches = []

        for thisChordStep, thisCorrect in zip(chordStepsToExamine, correctSemitones):
            if shouldSkipThisChordStep(thisChordStep):
                continue
            thisSemis = self.semitonesFromChordStep(thisChordStep)
            if thisSemis is None:  # no chord step
                continue
            if thisSemis == thisCorrect:  # nothing to do
                continue

            correctedSemis = thisCorrect - thisSemis
            chordStepNotNone = self.getChordStep(thisChordStep)
            if t.TYPE_CHECKING:
                assert chordStepNotNone is not None
            correctFaultyPitch(chordStepNotNone, correctedSemis)

        if len(correctSemitones) == 2 and len(self.figuresNotationObj.figures) >= 3:
            # special cases for chords whose 7th does not necessarily match the scale.
            if self.impliedQuality == 'minor' and self.semitonesFromChordStep(7) == 11:
                # i7 or iv7 chord or their inversions, in a major context.
                # check first that this isn't on purpose
                if not shouldSkipThisChordStep(7):
                    correctFaultyPitch(self.seventh, -1)


    def _correctForSecondaryRomanNumeral(
        self,
        useScale: key.Key|scale.ConcreteScale,
        figure: str|None = None
    ) -> tuple[str, key.Key|scale.ConcreteScale]:
        '''
        Creates .secondaryRomanNumeral object and .secondaryRomanNumeralKey Key object
        inside the RomanNumeral object (recursively in case of V/V/V/V etc.) and returns
        the figure and scale that should be used instead of figure for further working.

        Returns a tuple of (newFigure, newScale).
        In case there is no secondary slash, returns the original figure and the original scale.

        If figure is None, uses newFigure.

        >>> k = key.Key('C')
        >>> r = roman.RomanNumeral('I', k)  # will not be used below
        >>> r._correctForSecondaryRomanNumeral(k)  # uses 'I'. nothing should change
        ('I', <music21.key.Key of C major>)
        >>> r.secondaryRomanNumeral is None
        True
        >>> r.secondaryRomanNumeralKey is None
        True
        >>> r._correctForSecondaryRomanNumeral(k, 'V/V')
        ('V', <music21.key.Key of G major>)
        >>> r._correctForSecondaryRomanNumeral(k, 'V65/IV')
        ('V65', <music21.key.Key of F major>)
        >>> r._correctForSecondaryRomanNumeral(k, 'viio/bVII')
        ('viio', <music21.key.Key of B- major>)

        >>> r._correctForSecondaryRomanNumeral(k, 'V9/vi')
        ('V9', <music21.key.Key of a minor>)
        >>> r.secondaryRomanNumeral
        <music21.roman.RomanNumeral vi in C major>
        >>> r.secondaryRomanNumeralKey
        <music21.key.Key of a minor>

        Recursive:

        >>> r._correctForSecondaryRomanNumeral(k, 'V7/V/V')
        ('V7', <music21.key.Key of D major>)
        >>> r.secondaryRomanNumeral
        <music21.roman.RomanNumeral V/V in C major>
        >>> r.secondaryRomanNumeralKey
        <music21.key.Key of D major>
        >>> r.secondaryRomanNumeral.secondaryRomanNumeral
        <music21.roman.RomanNumeral V in C major>
        >>> r.secondaryRomanNumeral.secondaryRomanNumeralKey
        <music21.key.Key of G major>
        '''
        if figure is None:
            figure = self._figure
        if figure is not None:  # typing
            match = self._secondarySlashRegex.match(figure)
        else:
            match = None
        if match:
            primaryFigure = match.group(1)
            secondaryFigure = match.group(2)
            secondaryRomanNumeral = RomanNumeral(
                secondaryFigure,
                useScale,
                caseMatters=self.caseMatters,
                sixthMinor=self.sixthMinor,
                seventhMinor=self.seventhMinor,
            )
            self.secondaryRomanNumeral = secondaryRomanNumeral
            if secondaryRomanNumeral.quality == 'minor':
                secondaryMode = 'minor'
            elif secondaryRomanNumeral.quality == 'major':
                secondaryMode = 'major'
            elif secondaryRomanNumeral.semitonesFromChordStep(3) == 3:
                secondaryMode = 'minor'
            else:
                secondaryMode = 'major'

            # TODO: this should use a KeyCache
            # but lower priority since secondaries are relatively rare
            self.secondaryRomanNumeralKey = key.Key(
                secondaryRomanNumeral.root().name,
                secondaryMode,
            )
            useScale = self.secondaryRomanNumeralKey
            workingFigure = primaryFigure
        else:
            workingFigure = figure

        return (workingFigure, useScale)

    def _parseOmittedSteps(self, workingFigure: str) -> str:
        '''
        Remove omitted steps from a working figure and return the remaining figure,
        setting self.omittedSteps to the omitted parts

        >>> rn = roman.RomanNumeral()
        >>> rn._parseOmittedSteps('7[no5][no3]')
        '7'
        >>> rn.omittedSteps
        [5, 3]

        All omitted are mod 7:

        >>> rn = roman.RomanNumeral()
        >>> rn._parseOmittedSteps('13[no11][no9][no7]b3')
        '13b3'
        >>> rn.omittedSteps
        [4, 2, 7]

        '''
        omittedSteps = []
        match = self._omittedStepsRegex.search(workingFigure)
        if match:
            group = match.group()
            group = group.replace(' ', '')
            group = group.replace('][', '')
            omittedSteps = [(int(x) % 7 or 7) for x in group[1:-1].split('no') if x]
            # environLocal.printDebug(self.figure + ' omitting: ' + str(omittedSteps))
            workingFigure = self._omittedStepsRegex.sub('', workingFigure)
        self.omittedSteps = omittedSteps
        return workingFigure

    def _parseAddedSteps(self, workingFigure: str) -> str:
        '''
        Remove added steps from a working figure and return the remaining figure,
        setting self.addedSteps to a list of tuples of alteration and number

        >>> rn = roman.RomanNumeral()
        >>> rn._parseAddedSteps('7[add6][add#2]')
        '7'
        >>> rn.addedSteps
        [('', 6), ('#', 2)]

        All added are not mod 7.  Flat "b" becomes "-"

        >>> rn = roman.RomanNumeral()
        >>> rn._parseAddedSteps('13[addbb11]b3')
        '13b3'
        >>> rn.addedSteps
        [('--', 11)]
        '''
        addedSteps = []
        matches = self._addedStepsRegex.finditer(workingFigure)
        for m in matches:
            matchAlteration = m.group(1).replace('b', '-')
            matchDegree = m.group(2)
            addTuple = (matchAlteration, int(matchDegree))
            addedSteps.append(addTuple)
            # environLocal.printDebug(self.figure + ' omitting: ' + str(omittedSteps))
        workingFigure = self._addedStepsRegex.sub('', workingFigure)
        self.addedSteps = addedSteps
        return workingFigure

    def _parseBracketedAlterations(self, workingFigure: str) -> str:
        '''
        remove bracketed alterations from a figure and store them in `.bracketedAlterations`

        >>> rn = roman.RomanNumeral()
        >>> rn._parseBracketedAlterations('7[#5][b3]')
        '7'
        >>> rn.bracketedAlterations
        [('#', 5), ('b', 3)]

        '''
        matches = self._bracketedAlterationRegex.finditer(workingFigure)
        for m in matches:
            matchAlteration = m.group(1)
            matchDegree = int(m.group(2))
            newTuple = (matchAlteration, matchDegree)
            self.bracketedAlterations.append(newTuple)
        workingFigure = self._bracketedAlterationRegex.sub('', workingFigure)
        return workingFigure

    def _parseFrontAlterations(self, workingFigure: str) -> str:
        '''
        removes front alterations from a workingFigure and sets
        `.frontAlterationString`, `.frontAlterationTransposeInterval`
        and `.frontAlterationAccidental`.

        >>> rn = roman.RomanNumeral()
        >>> print(rn.frontAlterationTransposeInterval)
        None

        >>> rn._parseFrontAlterations('bVI')
        'VI'
        >>> rn.frontAlterationString
        'b'
        >>> rn.frontAlterationTransposeInterval
        <music21.interval.Interval d1>
        >>> rn.frontAlterationAccidental
        <music21.pitch.Accidental flat>
        '''
        frontAlterationString = ''  # the b in bVI, or the '#' in #vii
        frontAlterationTransposeInterval = None
        frontAlterationAccidental = None
        match = self._alterationRegex.match(workingFigure)
        if match:
            group = match.group()
            alteration = len(group)
            if group[0] in ('b', '-'):
                alteration *= -1  # else sharp
            frontAlterationTransposeInterval = interval.intervalFromGenericAndChromatic(
                interval.GenericInterval(1),
                interval.ChromaticInterval(alteration),
            )
            frontAlterationAccidental = pitch.Accidental(alteration)
            frontAlterationString = group
            workingFigure = self._alterationRegex.sub('', workingFigure)
        self.frontAlterationString = frontAlterationString
        self.frontAlterationTransposeInterval = frontAlterationTransposeInterval
        self.frontAlterationAccidental = frontAlterationAccidental

        return workingFigure

    def _parseRNAloneAmidstAug6(
        self,
        workingFigure: str,
        useScale: key.Key|scale.ConcreteScale,
    ) -> tuple[str, key.Key|scale.ConcreteScale]:
        # noinspection PyShadowingNames
        '''
        Sets and removes from workingFigure the roman numeral alone, possibly
        changing the useScale in the case of augmented sixths.

        Returns the remains of the figure alone with the scale to be used

        >>> useScale = key.Key('C')
        >>> rn = roman.RomanNumeral()
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('V7', useScale)
        >>> workingFig
        '7'
        >>> outScale is useScale
        True
        >>> rn.romanNumeralAlone
        'V'

        >>> rn = roman.RomanNumeral()
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('Ger65', useScale)
        >>> workingFig
        '65'
        >>> rn.scaleDegreeWithAlteration
        (4, <music21.pitch.Accidental sharp>)


        Working figures might be changed to defaults:

        >>> rn = roman.RomanNumeral()
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('Fr+6', useScale)
        >>> workingFig
        '43'
        >>> outScale
        <music21.key.Key of c minor>
        >>> rn.scaleDegree
        2

        >>> rn = roman.RomanNumeral()
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('It6', scale.MajorScale('C'))
        >>> outScale
        <music21.key.Key of c minor>
        '''
        romanNormalMatch = self._romanNumeralAloneRegex.match(workingFigure)
        aug6Match = self._augmentedSixthRegex.match(workingFigure)  # 250ns not worth short-circuit

        if not romanNormalMatch and not aug6Match:  # pragma: no cover
            raise RomanNumeralException(f'No roman numeral found in {workingFigure!r}')

        if aug6Match:
            # NB -- could be Key or Scale
            if ((isinstance(useScale, key.Key) and useScale.mode == 'major')
                    or (isinstance(useScale, scale.DiatonicScale)
                        and useScale.type == 'major'
                        and useScale.tonic is not None)):
                useScale = key.Key(useScale.tonic, 'minor')  # type: ignore  # just said not None
                self.impliedScale = useScale
                self.useImpliedScale = True

                # Set secondary key, if any, to minor
                if self.secondaryRomanNumeralKey is not None:
                    secondary_tonic = self.secondaryRomanNumeralKey.tonic
                    self.secondaryRomanNumeralKey = key.Key(secondary_tonic, 'minor')

            aug6type: t.Literal['It', 'Ger', 'Fr', 'Sw'] = aug6Match.group(1)  # type: ignore

            if aug6type in ('It', 'Ger'):
                self.scaleDegree = 4
                self.frontAlterationAccidental = pitch.Accidental('sharp')
            elif aug6type == 'Fr':
                self.scaleDegree = 2
            elif aug6type == 'Sw':
                self.scaleDegree = 2
                self.frontAlterationAccidental = pitch.Accidental('sharp')

            workingFigure = self._augmentedSixthRegex.sub('', workingFigure)
            workingFigure = self._slashedAug6Inv.sub(r'\1\2', workingFigure)

            if not workingFigure or not workingFigure[0].isdigit():
                # Ger was passed in instead of Ger65, etc.
                workingFigure = self._aug6defaultInversions[aug6type] + workingFigure
            elif (workingFigure
                  and aug6type != 'It'
                  and workingFigure[0] == '6'
                  and (len(workingFigure) < 2
                        or not workingFigure[1].isdigit())):
                # Fr6 => Fr43
                workingFigure = self._aug6defaultInversions[aug6type] + workingFigure[1:]

            self.romanNumeralAlone = aug6type
            if aug6type != 'Fr':
                fixTuple = ('#', 1)
                self.bracketedAlterations.append(fixTuple)
            if aug6type in ('Fr', 'Sw'):
                fixTuple = ('#', 3)
                self.bracketedAlterations.append(fixTuple)
        else:
            if t.TYPE_CHECKING:
                assert romanNormalMatch is not None
            romanNumeralAlone = romanNormalMatch.group(1)
            self.scaleDegree = common.fromRoman(romanNumeralAlone)
            workingFigure = self._romanNumeralAloneRegex.sub('', workingFigure)
            self.romanNumeralAlone = romanNumeralAlone

        return workingFigure, useScale

    def adjustMinorVIandVIIByQuality(
        self,
        useScale: key.Key|scale.ConcreteScale
    ) -> None:
        '''
        Fix minor vi and vii to always be #vi and #vii if `.caseMatters`.

        >>> rn = roman.RomanNumeral()
        >>> rn.scaleDegree = 6
        >>> rn.impliedQuality = 'minor'
        >>> rn.adjustMinorVIandVIIByQuality(key.Key('c'))
        >>> rn.frontAlterationTransposeInterval
        <music21.interval.Interval A1>

        >>> rn.frontAlterationAccidental
        <music21.pitch.Accidental sharp>


        >>> rn = roman.RomanNumeral()
        >>> rn.scaleDegree = 6
        >>> rn.impliedQuality = 'major'
        >>> rn.adjustMinorVIandVIIByQuality(key.Key('c'))
        >>> rn.frontAlterationTransposeInterval is None
        True
        >>> rn.frontAlterationAccidental is None
        True

        * Changed in v6.4: public function became hook to private function having the actual guts
        '''
        unused_workingFigure = self._adjustMinorVIandVIIByQuality('', useScale)

    def _adjustMinorVIandVIIByQuality(
        self,
        workingFigure: str,
        useScale: key.Key|scale.ConcreteScale
    ) -> str:
        '''
        Fix minor vi and vii to always be #vi and #vii if `.caseMatters`.

        Altering `workingFigure` became necessary to handle these chromatic figures:
        https://github.com/cuthbertLab/music21/issues/437

        >>> rn = roman.RomanNumeral('viio#6', 'a')
        >>> ' '.join([p.name for p in rn.pitches])
        'B D G#'
        >>> rn = roman.RomanNumeral('viio6#4', 'a')
        >>> ' '.join([p.name for p in rn.pitches])
        'D G# B'
        >>> rn = roman.RomanNumeral('viio4#2', 'a')
        >>> ' '.join([p.name for p in rn.pitches])
        'F G# B D'
        >>> rn = roman.RomanNumeral('viio#853', 'a')
        >>> ' '.join([p.name for p in rn.pitches])
        'G# B D'
        >>> rn = roman.RomanNumeral('viio##853', 'a')
        >>> ' '.join([p.name for p in rn.pitches])
        'G# B D G##'

        * Changed in v6.4: Made private when `workingFigure`
          was added to the signature and returned.
        '''
        def sharpen(wFig: str) -> str:
            changeFrontAlteration(interval.Interval('A1'), 1)
            # If root is in the figure, lower the root to avoid double-sharpening
            if '##' in wFig:
                wFig = wFig.replace('##8', '#8')
            elif '#2' in wFig:
                wFig = wFig.replace('#2', '2')
            elif '#4' in wFig:
                wFig = wFig.replace('#4', '4')
            elif '#6' in wFig:
                wFig = wFig.replace('#6', '6')
            else:
                wFig = wFig.replace('#8', '')
            return wFig

        # def flatten():
        #    changeFrontAlteration(interval.Interval('-A1'), -1)

        def changeFrontAlteration(intV: interval.Interval, alter: int):
            # fati = front alteration transpose interval
            fati = self.frontAlterationTransposeInterval
            if fati:
                newFati = interval.add([fati, intV])
                self.frontAlterationTransposeInterval = newFati
                if self.frontAlterationAccidental is None:  # pragma: no check
                    raise TypeError(
                        'Cannot have a RN with frontAlterationTransposeInterval and no accidental'
                    )
                self.frontAlterationAccidental.alter += alter
                if self.frontAlterationAccidental.alter == 0:
                    self.frontAlterationTransposeInterval = None
                    self.frontAlterationAccidental = None
            else:
                self.frontAlterationTransposeInterval = intV
                self.frontAlterationAccidental = pitch.Accidental(alter)

        # Make vii always #vii and vi always #vi.
        if getattr(useScale, 'mode', None) != 'minor':
            return workingFigure
        if self.scaleDegree not in (6, 7):
            return workingFigure
        if not self.caseMatters:
            return workingFigure

        # THIS IS WHERE sixthMinor and seventhMinor goes
        if self.scaleDegree == 6:
            minorDefault = self.sixthMinor
        else:
            minorDefault = self.seventhMinor

        if minorDefault == Minor67Default.FLAT:
            # default of flat does not need anything.
            return workingFigure

        normallyRaised = self.impliedQuality in ('minor', 'diminished', 'half-diminished')

        if minorDefault == Minor67Default.SHARP:
            return sharpen(workingFigure)
        elif minorDefault == Minor67Default.QUALITY:
            if not normallyRaised:
                return workingFigure
            else:
                return sharpen(workingFigure)
        else:  # CAUTIONARY
            if not self.frontAlterationAccidental or self.frontAlterationAccidental.alter == 0:
                # same as QUALITY in this case
                if not normallyRaised:
                    return workingFigure
                else:
                    return sharpen(workingFigure)

            # adjust accidentals for CAUTIONARY status
            frontAlter = self.frontAlterationAccidental.alter
            if frontAlter >= 1 and normallyRaised:
                # CAUTIONARY accidental that is needed for parsing.
                return workingFigure
            elif frontAlter <= -1:
                return sharpen(workingFigure)
            else:
                return workingFigure

    def _updatePitches(self) -> None:
        '''
        Utility function to update the pitches to the new figure etc.
        '''
        useScale: key.Key|scale.ConcreteScale
        if self.secondaryRomanNumeralKey is not None:
            useScale = self.secondaryRomanNumeralKey
        elif self.useImpliedScale and self.impliedScale is not None:
            useScale = self.impliedScale
        else:
            useScale = self.key

        # should be 7 but hey, octatonic scales, etc.
        # self.scaleCardinality = len(useScale.pitches) - 1
        if 'DiatonicScale' in useScale.classes:  # speed up simple case
            self.scaleCardinality = 7
        else:
            self.scaleCardinality = useScale.getDegreeMaxUnique()

        bassScaleDegree = self.bassScaleDegreeFromNotation(self.figuresNotationObj)
        bassPitch = useScale.pitchFromDegree(bassScaleDegree, direction=scale.Direction.ASCENDING)
        pitches: list[pitch.Pitch] = [bassPitch]
        lastPitch = bassPitch
        numberNotes = len(self.figuresNotationObj.numbers)

        for j in range(numberNotes):
            i = numberNotes - j - 1
            thisScaleDegree = (bassScaleDegree
                                + self.figuresNotationObj.numbers[i]
                                - 1)
            newPitch = useScale.pitchFromDegree(thisScaleDegree,
                                                direction=scale.Direction.ASCENDING)
            pitchName = self.figuresNotationObj.modifiers[i].modifyPitchName(newPitch.name)
            newNewPitch = pitch.Pitch(pitchName)
            if newPitch.octave is not None:
                newNewPitch.octave = newPitch.octave
            else:
                newNewPitch.octave = defaults.pitchOctave
            if newNewPitch.ps < lastPitch.ps:
                newNewPitch.octave += 1  # type: ignore
            pitches.append(newNewPitch)
            lastPitch = newNewPitch

        if (self.frontAlterationTransposeInterval
                and self.frontAlterationTransposeInterval.semitones != 0):
            chord_map = chord.tools.allChordSteps(chord.Chord(pitches))
            non_alter = (
                chord_map.get(7, None),
                chord_map.get(2, None),  # 9th
                chord_map.get(4, None),  # 11th
                chord_map.get(6, None),  # 13th
            )
            for thisPitch in pitches:
                if thisPitch not in non_alter:
                    self.frontAlterationTransposeInterval.transposePitch(thisPitch, inPlace=True)
        self.pitches = tuple(pitches)  # unnecessary tuple; mypy properties different typing bug

        if self.figuresNotationObj.numbers not in FIGURES_IMPLYING_ROOT:
            # Avoid deriving a nonsense root later
            self.root(self.bass())

        self._matchAccidentalsToQuality(self.impliedQuality)

        # run this before omittedSteps and added steps so that
        # they don't change the sense of root.
        self._correctBracketedPitches()
        if self.omittedSteps or self.addedSteps:
            # set the root manually so that these alterations don't change the root.
            self.root(self.root())

        if self.omittedSteps:
            omittedPitches = []
            for thisCS in self.omittedSteps:
                p = self.getChordStep(thisCS)
                if p is not None:
                    omittedPitches.append(p.name)

            newPitches = []
            for thisPitch in self.pitches:
                if thisPitch.name not in omittedPitches:
                    newPitches.append(thisPitch)
            self.pitches = tuple(newPitches)

        if self.addedSteps:
            for addAccidental, stepNumber in self.addedSteps:
                if '-' in addAccidental:
                    alteration = addAccidental.count('-') * -1
                else:
                    alteration = addAccidental.count('#')
                thisScaleDegree = (self.scaleDegree + stepNumber - 1)
                addedPitch = useScale.pitchFromDegree(thisScaleDegree,
                                                      direction=scale.Direction.ASCENDING)
                if addedPitch.accidental is not None:
                    addedPitch.accidental.alter += alteration
                else:
                    addedPitch.accidental = pitch.Accidental(alteration)

                while addedPitch.ps < bassPitch.ps:
                    addedPitch.octave += 1

                if (addedPitch.ps == bassPitch.ps
                        and addedPitch.diatonicNoteNum < bassPitch.diatonicNoteNum):
                    # RN('IV[add#7]', 'C') would otherwise result
                    # in E#4 as bass, not E#5 as highest note.
                    addedPitch.octave += 1

                if addedPitch not in self.pitches:
                    self.add(addedPitch)

        if not self.pitches:
            raise RomanNumeralException(
                f'_updatePitches() was unable to derive pitches from the figure: {self.figure!r}'
            )  # pragma: no cover

    def transpose(self: T, value, *, inPlace=False) -> T|None:
        '''
        Overrides :meth:`~music21.harmony.Harmony.transpose` so that `key`
        attribute is transposed as well.

        >>> rn = roman.RomanNumeral('I', 'C')
        >>> rn
        <music21.roman.RomanNumeral I in C major>
        >>> rn.transpose(4)
        <music21.roman.RomanNumeral I in E major>
        >>> rn.transpose(-4, inPlace=True)
        >>> rn
        <music21.roman.RomanNumeral I in A- major>
        '''
        post = super().transpose(value, inPlace=inPlace)
        if not inPlace:
            post.key = self.key.transpose(value, inPlace=False)
            return post
        else:
            self.key = self.key.transpose(value, inPlace=False)
            return None


    # PUBLIC PROPERTIES #

    @property
    def romanNumeral(self) -> str:
        '''
        Read-only property that returns either the romanNumeralAlone (e.g. just
        II) or the frontAlterationAccidental.modifier (with 'b' for '-') + romanNumeralAlone
        (e.g. #II, bII)

        >>> rn = roman.RomanNumeral('#II7')
        >>> rn.romanNumeral
        '#II'

        >>> rn = roman.RomanNumeral('Ger+6')
        >>> rn.romanNumeral
        'Ger'

        >>> rn = roman.RomanNumeral('bbII/V')
        >>> rn.romanNumeral
        'bbII'
        >>> rn = roman.RomanNumeral('--II/V')
        >>> rn.romanNumeral
        'bbII'

        OMIT_FROM_DOCS

        >>> rn.romanNumeral = 'V'
        Traceback (most recent call last):
        ValueError: Cannot set romanNumeral property of RomanNumeral objects

        (This is in OMIT_FROM_etc.)
        '''
        if self.romanNumeralAlone in ('Ger', 'Sw', 'It', 'Fr'):
            return self.romanNumeralAlone
        if self.frontAlterationAccidental is None:
            return self.romanNumeralAlone

        return (self.frontAlterationAccidental.modifier.replace('-', 'b')
                + self.romanNumeralAlone)

    @romanNumeral.setter
    def romanNumeral(self, value: str):
        raise ValueError('Cannot set romanNumeral property of RomanNumeral objects')

    @property
    def figure(self) -> str:
        '''
        Gets or sets the entire figure (the whole enchilada).
        (these docs are overridden below)
        '''
        return self._figure or ''

    @figure.setter
    def figure(self, newFigure: str):
        self._figure = newFigure
        if self._parsingComplete:
            self.bracketedAlterations = []
            self._parseFigure()
            self._updatePitches()

    @property
    def figureAndKey(self) -> str:
        '''
        Returns the figure and the key and mode as a string

        >>> rn = roman.RomanNumeral('V65/V', 'e')
        >>> rn.figureAndKey
        'V65/V in e minor'

        Without a key, it is the same as figure:

        >>> roman.RomanNumeral('V7').figureAndKey
        'V7'
        '''
        if self.key is None:
            return self.figure

        mode = ''
        tonic = self.key.tonic

        if hasattr(tonic, 'name'):
            tonic = tonic.name
        if hasattr(self.key, 'mode'):
            mode = ' ' + self.key.mode
        elif self.key.__class__.__name__ == 'MajorScale':
            mode = ' major'
        elif self.key.__class__.__name__ == 'MinorScale':
            mode = ' minor'

        if mode == ' minor':
            tonic = tonic.lower()
        elif mode == ' major':
            tonic = tonic.upper()
        return f'{self.figure} in {tonic}{mode}'

    @property
    def key(self):
        '''
        Gets or Sets the current Key (or Scale object) for a given
        RomanNumeral object.

        If a new key is set, then the pitches will probably change:

        >>> r1 = roman.RomanNumeral('V')

        (No key means an implicit C-major)

        >>> r1.key is None
        True

        >>> [str(p) for p in r1.pitches]
        ['G4', 'B4', 'D5']

        Change to A major

        >>> r1.key = key.Key('A')
        >>> [str(p) for p in r1.pitches]
        ['E5', 'G#5', 'B5']

        >>> r1
        <music21.roman.RomanNumeral V in A major>

        >>> r1.key
        <music21.key.Key of A major>

        >>> r1.key = key.Key('e')
        >>> [str(p) for p in r1.pitches]
        ['B4', 'D#5', 'F#5']

        >>> r1
        <music21.roman.RomanNumeral V in e minor>
        '''
        return self._scale

    @key.setter
    def key(self, keyOrScale):
        '''
        Provide a new key or scale, and re-configure the RN with the
        existing figure.
        '''
        if keyOrScale == self._scale and keyOrScale is not None:
            return  # skip

        # try to get Scale or Key object from cache: this will offer
        # performance boost as Scale stores cached pitch segments
        if isinstance(keyOrScale, str):
            keyOrScale = _getKeyFromCache(keyOrScale)
        elif keyOrScale is not None:
            # environLocal.printDebug(['got keyOrScale', keyOrScale])
            try:
                keyClasses = keyOrScale.classes
            except:  # pragma: no cover
                raise RomanNumeralException(
                    'Cannot call classes on object {0!r}, send only Key '
                    'or Scale Music21Objects'.format(keyOrScale))
            if 'Key' in keyClasses:
                # good to go
                if keyOrScale.tonicPitchNameWithCase not in _keyCache:
                    # store for later
                    _keyCache[keyOrScale.tonicPitchNameWithCase] = keyOrScale
            elif 'Scale' in keyClasses:
                # Need unique 'hash' for each scale. Names is not enough as there are
                # multiple scales with the same name but different pitches.
                scaleHash = keyOrScale.name
                if getattr(keyOrScale, 'isConcrete', False):
                    scaleHash += '_'.join(
                        [p.nameWithOctave for p in keyOrScale.pitches]
                    )
                if scaleHash in _scaleCache:
                    keyOrScale = _scaleCache[scaleHash]
                else:
                    _scaleCache[scaleHash] = keyOrScale
            else:
                raise RomanNumeralException(
                    f'Cannot get a key from this object {keyOrScale!r}, send only '
                    + 'Key or Scale objects')  # pragma: no cover

        else:
            pass  # None
            # cache object if passed directly
        self._scale = keyOrScale
        if (keyOrScale is None
                or (hasattr(keyOrScale, 'isConcrete')
                    and not keyOrScale.isConcrete)):
            self.useImpliedScale = True
            if self._scale is not None:
                self.impliedScale = self._scale.derive(1, 'C')
            else:
                self.impliedScale = scale.MajorScale('C')
        else:
            self.useImpliedScale = False
        # need to permit object creation with no arguments, thus
        # self._figure can be None
        if self._parsingComplete:
            self._updatePitches()
            # environLocal.printDebug([
            #     'Roman.setKeyOrScale:',
            #     'called w/ scale', self.key,
            #     'figure', self.figure,
            #     'pitches', self.pitches,
            #     ])

    @property
    def scaleDegreeWithAlteration(self) -> tuple[int, pitch.Accidental|None]:
        '''
        Returns a two element tuple of the scale degree and the
        accidental that alters the scale degree for things such as #ii or
        bV.

        Note that vi and vii in minor have a frontAlterationAccidental of
        <sharp> even if it is not preceded by a `#` sign.

        Has the same effect as setting .scaleDegree and
        .frontAlterationAccidental separately

        >>> v = roman.RomanNumeral('V', 'C')
        >>> v.scaleDegreeWithAlteration
        (5, None)

        >>> neapolitan = roman.RomanNumeral('N6', 'c#')
        >>> neapolitan.scaleDegreeWithAlteration
        (2, <music21.pitch.Accidental flat>)
        '''
        return self.scaleDegree, self.frontAlterationAccidental

    def bassScaleDegreeFromNotation(
        self,
        notationObject: fbNotation.Notation|None = None
    ) -> int:
        '''
        Given a notationObject from
        :class:`music21.figuredBass.notation.Notation`
        return the scaleDegree of the bass.

        >>> fbn = figuredBass.notation.Notation('6,3')
        >>> V = roman.RomanNumeral('V')
        >>> V.bassScaleDegreeFromNotation(fbn)
        7

        >>> fbn2 = figuredBass.notation.Notation('#6,4')
        >>> vi = roman.RomanNumeral('vi')
        >>> vi.bassScaleDegreeFromNotation(fbn2)
        3

        Can figure it out directly from an existing RomanNumeral:

        >>> ii65 = roman.RomanNumeral('ii65', 'C')
        >>> ii65.bassScaleDegreeFromNotation()
        4

        Simple test:

        >>> I = roman.RomanNumeral('I')
        >>> I.bassScaleDegreeFromNotation()
        1

        Figures that do not imply a bass like 54 just return the instance
        :attr:`scaleDegree`:

        >>> V = roman.RomanNumeral('V54')
        >>> V.bassScaleDegreeFromNotation()
        5
        '''
        # A bit slow (6 seconds for 1000 operations, but not the bottleneck)
        if notationObject is None:
            notationObject = self.figuresNotationObj
        c = pitch.Pitch('C3')
        cDNN = 22  # cDNN = c.diatonicNoteNum  # always 22
        pitches = [c]
        if notationObject.numbers not in FIGURES_IMPLYING_ROOT:
            return self.scaleDegree
        for i in notationObject.numbers:
            distanceToMove = i - 1
            newDiatonicNumber = (cDNN + distanceToMove)

            newStep, newOctave = interval.convertDiatonicNumberToStep(
                newDiatonicNumber)
            newPitch = pitch.Pitch(f'{newStep}{newOctave}')
            pitches.append(newPitch)

        tempChord = chord.Chord(pitches)
        rootDNN = tempChord.root().diatonicNoteNum
        staffDistanceFromBassToRoot = rootDNN - cDNN
        bassSD = ((self.scaleDegree - staffDistanceFromBassToRoot) %
                  self.scaleCardinality)
        if bassSD == 0:
            bassSD = self.scaleCardinality
        return bassSD

    @property
    def functionalityScore(self) -> int:
        '''
        Return or set a number from 1 to 100 representing the relative
        functionality of this RN.figure (possibly given the mode, etc.).

        Numbers are ordinal, not cardinal.

        >>> rn1 = roman.RomanNumeral('V7')
        >>> rn1.functionalityScore
        80

        >>> rn2 = roman.RomanNumeral('vi6')
        >>> rn2.functionalityScore
        10

        >>> rn2.functionalityScore = 99
        >>> rn2.functionalityScore
        99

        For secondary dominants, the functionality scores are multiplied, reducing
        all but the first by 1/100th:

        >>> rn3 = roman.RomanNumeral('V')
        >>> rn3.functionalityScore
        70

        >>> rn4 = roman.RomanNumeral('vi')
        >>> rn4.functionalityScore
        40

        >>> rn5 = roman.RomanNumeral('V/vi')
        >>> rn5.functionalityScore
        28
        '''
        if self._functionalityScore is not None:
            return self._functionalityScore

        if self.secondaryRomanNumeral:
            figures = self.figure.split('/')  # error for half-diminished in secondary
            score = 100.0
            for f in figures:
                try:
                    scorePart = functionalityScores[f] / 100
                except KeyError:
                    scorePart = 0
                score *= scorePart
            return int(score)

        try:
            score = functionalityScores[self.figure]
        except KeyError:
            score = 0
        return score

    @functionalityScore.setter
    def functionalityScore(self, value: int):
        self._functionalityScore = value

    def isNeapolitan(self,
                     require1stInversion: bool = True):
        '''
        Music21's Chord class contains methods for identifying chords of a particular type,
        such as :meth:`~music21.chord.Chord.isAugmentedSixth`.

        Some similar chord types are defined not only by the structure of a chord but
        by its relation to a key.
        The Neapolitan sixth is a notable example.
        A chord is a Neapolitan sixth if it is a major triad, in first inversion, and
        (here's the key-dependent part) rooted on the flattened second scale degree.

        >>> chd = chord.Chord(['F4', 'Ab4', 'Db5'])
        >>> rn = roman.romanNumeralFromChord(chd, 'C')
        >>> rn.isNeapolitan()
        True

        As this is key-dependent, changing the key changes the outcome.

        >>> rn = roman.romanNumeralFromChord(chd, 'Db')
        >>> rn.isNeapolitan()
        False

        The 'N', 'N6' and 'N53' shorthand forms are accepted.

        >>> rn = roman.RomanNumeral('N')
        >>> rn.isNeapolitan()
        True

        >>> rn = roman.RomanNumeral('N6')
        >>> rn.isNeapolitan()
        True

        Requiring first inversion is optional.

        >>> rn = roman.RomanNumeral('bII')
        >>> rn.isNeapolitan(require1stInversion=False)
        True

        >>> rn = roman.RomanNumeral('N53')
        >>> rn.isNeapolitan(require1stInversion=False)
        True

        '''
        if self.scaleDegree != 2:
            return False
        if not self.frontAlterationAccidental:
            return False
        if self.frontAlterationAccidental.name != 'flat':
            return False
        if self.quality != 'major':
            return False
        if require1stInversion and self.inversion() != 1:
            return False
        return True

    def isMixture(self,
                  evaluateSecondaryNumeral: bool = False):
        '''
        Checks if a RomanNumeral is an instance of 'modal mixture' in which the chord is
        not diatonic in the key specified, but
        would be in the parallel (German: variant) major / minor
        and can therefore be thought of as a 'mixture' of major and minor modes, or
        as a 'borrowing' from the one to the other.

        Examples include "i" in major or "I" in minor (*sic*).

        Specifically, this method returns True for all and only the following cases in any
        inversion:

        Major context (example of C major):

        * scale degree 1 and triad quality minor (minor tonic chord, c);

        * scale degree 2 and triad quality diminished (covers both iio and iiø7);

        * scale degree b3 and triad quality major (Eb);

        * scale degree 4 and triad quality minor (f);

        * scale degree 5 and triad quality minor (g, NB: potentially controversial);

        * scale degree b6 and triad quality major (Ab);

        * scale degree b7 and triad quality major (Bb); and

        * scale degree 7, and it is a diminished seventh (specifically b-d-f-ab).

        Minor context (example of c minor):

        * scale degree 1 and triad quality major (major tonic chord, C);

        * scale degree 2 and triad quality minor (d, not diminished);

        * scale degree #3 and triad quality minor (e);

        * scale degree 4 and triad quality major (F);

        * scale degree #6 and triad quality minor (a); and

        * scale degree 7, and it is a half-diminished seventh (specifically b-d-f-a).

        This list is broadly consistent with (and limited to) borrowing between the major and
        natural minor, except for excluding V (G-B-D) and viio (B-D-F) in minor.
        There are several borderline caes and this in-/exclusion is all open to debate, of course.
        The choices here reflect this method's primarily goal to aid anthologizing and
        pointing to clear cases of mixture in common practice Classical music.
        At least in that context, V and viio are not generally regarded as mixure.

        By way of example usage, here are both major and minor versions of the
        tonic and subdominant triads in the major context.

        >>> roman.RomanNumeral('I', 'D-').isMixture()
        False

        >>> roman.RomanNumeral('i', 'D-').isMixture()
        True

        >>> roman.RomanNumeral('IV', 'F').isMixture()
        False

        >>> roman.RomanNumeral('iv', 'F').isMixture()
        True

        For any cases extending beyond triad/seventh chords, major/minor keys,
        and the like, this method simply returns False.

        So when the mode is not major or minor (including when it's undefined), that's False.

        >>> rn = roman.RomanNumeral('iv', 'C')
        >>> rn.key.mode
        'major'

        >>> rn.isMixture()
        True

        >>> rn.key.mode = 'hypomixolydian'
        >>> rn.isMixture()
        False

        A scale for a key never returns True for mixture.

        >>> rn = roman.RomanNumeral('i', scale.MajorScale('D'))  # mode undefined
        >>> rn.isMixture()
        False

        Likewise, anything that's not a triad or seventh will return False:

        >>> rn = roman.romanNumeralFromChord(chord.Chord("C D E"))
        >>> rn.isMixture()
        False

        Note that Augmented sixth chords do count as sevenths but never indicate modal mixture
        (not least because those augmented sixths are the same in both major and minor).

        >>> rn = roman.RomanNumeral('Ger65')
        >>> rn.isSeventh()
        True

        >>> rn.isMixture()
        False

        False is also returned for any case in which the triad quality is not
        diminished, minor, or major:

        >>> rn = roman.RomanNumeral('bIII+')
        >>> rn.quality
        'augmented'

        >>> rn.isMixture()
        False

        (That specific example of bIII+ in major is a borderline case that
        arguably ought to be included and may be added later without a deprecation cycle.)

        Naturally, really extended usages such as scale degrees beyond 7 (in the
        Octatonic mode, for instance) also return False.

        The evaluateSecondaryNumeral parameter allows users to choose whether to consider
        secondary Roman numerals (like V/vi) or to ignore them.
        When considered, exactly the same rules apply but recasting the comparison on
        the secondaryRomanNumeral.
        This is an extended usage that is open to debate and liable to change.

        >>> roman.RomanNumeral('V/bVI', 'E-').isMixture()
        False

        >>> roman.RomanNumeral('V/bVI', 'E-').isMixture(evaluateSecondaryNumeral=True)
        True

        In case of secondary numeral chains, read the last one for mixture.

        >>> roman.RomanNumeral('V/V/bVI', 'E-').isMixture(evaluateSecondaryNumeral=True)
        True

        OMIT_FROM_DOCS

        Test that the 'C' key has not had its mode permanently changed with the
        hypomixolydian change above:

        >>> roman.RomanNumeral('iv', 'C').key.mode
        'major'

        (This is in OMIT_FROM_etc.)
        '''

        if evaluateSecondaryNumeral and self.secondaryRomanNumeral:
            return self.secondaryRomanNumeral.isMixture(evaluateSecondaryNumeral=True)

        if (not self.isTriad) and (not self.isSeventh):
            return False

        if not self.key or not isinstance(self.key, key.Key):
            return False

        mode = self.key.mode
        if mode not in ('major', 'minor'):
            return False

        scaleDegree = self.scaleDegree
        if scaleDegree not in range(1, 8):
            return False

        quality = self.quality
        if quality not in ('diminished', 'minor', 'major'):
            return False

        if self.frontAlterationAccidental:
            frontAccidentalName = self.frontAlterationAccidental.name
        else:
            frontAccidentalName = 'natural'

        majorKeyMixtures = {
            (1, 'minor', 'natural'),
            (2, 'diminished', 'natural'),
            (3, 'major', 'flat'),
            # (3, 'augmented', 'flat'),  # Potential candidate
            (4, 'minor', 'natural'),
            (5, 'minor', 'natural'),  # Potentially controversial
            (6, 'major', 'flat'),
            (7, 'major', 'flat'),  # Note diminished 7th handled separately
        }

        minorKeyMixtures = {
            (1, 'major', 'natural'),
            (2, 'minor', 'natural'),
            (3, 'minor', 'sharp'),
            (4, 'major', 'natural'),
            # 5 N/A
            (6, 'minor', 'sharp'),
            # (6, 'diminished', 'sharp'),  # Potential candidate
            # 7 half-diminished handled separately
        }

        if mode == 'major':
            if (scaleDegree, quality, frontAccidentalName) in majorKeyMixtures:
                return True
            elif (scaleDegree == 7) and (self.isDiminishedSeventh()):
                return True
        elif mode == 'minor':
            if (scaleDegree, quality, frontAccidentalName) in minorKeyMixtures:
                return True
            elif (scaleDegree == 7) and (self.isHalfDiminishedSeventh()):
                return True

        return False


# Override the documentation for a property
RomanNumeral.figure.__doc__ = '''
    Gives a string representation of the roman numeral, which
    is usually the same as what you passed in as a string:

    >>> roman.RomanNumeral('bVII65/V', 'C').figure
    'bVII65/V'

    There are a few exceptions.  If the RomanNumeral is initialized
    with an int, then it is converted to a string:

    >>> roman.RomanNumeral(2).figure
    'II'

    A `0` used for `o` in a diminished seventh chord is converted to `o`,
    and the `/o` form of half-diminished is converted to `ø`:

    >>> roman.RomanNumeral('vii07').figure
    'viio7'
    >>> roman.RomanNumeral('vii/o7').figure
    'viiø7'

    Changing this value will not change existing pitches.

    * Changed in v6.5: empty RomanNumerals now have figure of '' not None
    '''


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())


    def testFBN(self):
        fbn = fbNotation.Notation('6,3')
        V = RomanNumeral('V')
        sdb = V.bassScaleDegreeFromNotation(fbn)
        self.assertEqual(sdb, 7)

    def testFigure(self):
        r1 = RomanNumeral('V')
        self.assertEqual(r1.frontAlterationTransposeInterval, None)
        self.assertEqual(r1.pitches, chord.Chord(['G4', 'B4', 'D5']).pitches)
        r1 = RomanNumeral('bbVI6')
        self.assertEqual(r1.figuresWritten, '6')
        self.assertEqual(r1.frontAlterationTransposeInterval.chromatic.semitones, -2)
        self.assertEqual(r1.frontAlterationTransposeInterval.diatonic.directedNiceName,
                         'Descending Doubly-Diminished Unison')
        cM = scale.MajorScale('C')
        r2 = RomanNumeral('ii', cM)
        self.assertIsNotNone(r2)

        dminor = key.Key('d')
        rn = RomanNumeral('ii/o65', dminor)
        self.assertEqual(
            rn.pitches,
            chord.Chord(['G4', 'B-4', 'D5', 'E5']).pitches,
        )
        rnRealSlash = RomanNumeral('iiø65', dminor)
        self.assertEqual(rn, rnRealSlash)

        rnOmit = RomanNumeral('V[no3]', dminor)
        self.assertEqual(rnOmit.pitches, chord.Chord(['A4', 'E5']).pitches)
        rnOmit = RomanNumeral('V[no5]', dminor)
        self.assertEqual(rnOmit.pitches, chord.Chord(['A4', 'C#5']).pitches)
        rnOmit = RomanNumeral('V[no3no5]', dminor)
        self.assertEqual(rnOmit.pitches, chord.Chord(['A4']).pitches)
        rnOmit = RomanNumeral('V13[no11]', key.Key('C'))
        self.assertEqual(rnOmit.pitches, chord.Chord('G4 B4 D5 F5 A5 E5').pitches)

    def testBracketedAlterations(self):
        r1 = RomanNumeral('V9[b7][b5]')
        self.assertEqual(str(r1.bracketedAlterations), "[('b', 7), ('b', 5)]")
        self.assertEqual(str(r1.pitches),
                         '(<music21.pitch.Pitch G4>, <music21.pitch.Pitch B4>, '
                         + '<music21.pitch.Pitch D-5>, '
                         + '<music21.pitch.Pitch F-5>, <music21.pitch.Pitch A5>)')


    def testYieldRemoveA(self):
        from music21 import stream
        # s = corpus.parse('madrigal.3.1.rntxt')
        m = stream.Measure()
        m.append(key.KeySignature(4))
        m.append(note.Note())
        p = stream.Part()
        p.append(m)
        s = stream.Score()
        s.append(p)
        targetCount = 1
        self.assertEqual(
            len(s['KeySignature']),
            targetCount,
        )
        # through sequential iteration
        s1 = copy.deepcopy(s)
        for p in s1.parts:
            for m in p.getElementsByClass(stream.Measure):
                for e in m.getElementsByClass(key.KeySignature):
                    m.remove(e)
        self.assertEqual(len(s1.flatten().getElementsByClass(key.KeySignature)), 0)
        s2 = copy.deepcopy(s)
        self.assertEqual(
            len(s2.flatten().getElementsByClass(key.KeySignature)),
            targetCount,
        )
        for e in s2.flatten().getElementsByClass(key.KeySignature):
            for site in e.sites.get():
                if site is not None:
                    site.remove(e)
        # s2.show()
        # yield elements and containers
        s3 = copy.deepcopy(s)
        self.assertEqual(
            len(s3.flatten().getElementsByClass(key.KeySignature)),
            targetCount,
        )
        for e in s3.recurse(streamsOnly=True):
            if isinstance(e, key.KeySignature):
                # all active sites are None because of deep-copying
                if e.activeSite is not None:
                    e.activeSite.remove(e)
        # s3.show()
        # yield containers
        s4 = copy.deepcopy(s)
        self.assertEqual(
            len(s4.flatten().getElementsByClass(key.KeySignature)),
            targetCount,
        )
        # do not remove in iteration.
        for c in list(s4.recurse(streamsOnly=False)):
            if isinstance(c, stream.Stream):
                for e in c.getElementsByClass(key.KeySignature):
                    c.remove(e)

    def testScaleDegreesA(self):
        from music21 import roman
        k = key.Key('f#')  # 3-sharps minor
        rn = roman.RomanNumeral('V', k)
        self.assertEqual(str(rn.key), 'f# minor')
        self.assertEqual(
            str(rn.pitches),
            '(<music21.pitch.Pitch C#5>, '
            '<music21.pitch.Pitch E#5>, '
            '<music21.pitch.Pitch G#5>)',
        )
        self.assertEqual(
            str(rn.scaleDegrees),
            '[(5, None), (7, <music21.pitch.Accidental sharp>), (2, None)]',
        )

    def testNeapolitanAndHalfDiminished(self):
        from music21 import roman
        alteredChordHalfDim3rdInv = roman.RomanNumeral(
            'bii/o42', scale.MajorScale('F'))
        self.assertEqual(
            [str(p) for p in alteredChordHalfDim3rdInv.pitches],
            ['F-4', 'G-4', 'B--4', 'D--5'],
        )
        iv = alteredChordHalfDim3rdInv.intervalVector
        self.assertEqual([0, 1, 2, 1, 1, 1], iv)
        cn = alteredChordHalfDim3rdInv.commonName
        self.assertEqual(cn, 'half-diminished seventh chord')

    def testOmittedFifth(self):
        from music21 import roman
        c = chord.Chord('A3 E-4 G-4')
        k = key.Key('b-')
        rnDim7 = roman.romanNumeralFromChord(c, k)
        self.assertEqual(rnDim7.figure, 'viio7')

    def testAllFormsOfVII(self):
        from music21 import roman

        def p(c):
            return ' '.join([x.nameWithOctave for x in c.pitches])

        k = key.Key('c')
        rn = roman.RomanNumeral('viio', k)
        self.assertEqual(p(rn), 'B4 D5 F5')
        rn = roman.RomanNumeral('viio6', k)
        self.assertEqual(p(rn), 'D4 F4 B4')
        rn = roman.RomanNumeral('viio64', k)
        self.assertEqual(p(rn), 'F4 B4 D5')

        rn = roman.RomanNumeral('vii', k)
        self.assertEqual(p(rn), 'B4 D5 F#5')
        rn = roman.RomanNumeral('vii6', k)
        self.assertEqual(p(rn), 'D4 F#4 B4')
        rn = roman.RomanNumeral('vii64', k)
        self.assertEqual(p(rn), 'F#4 B4 D5')

        rn = roman.RomanNumeral('viio7', k)
        self.assertEqual(p(rn), 'B4 D5 F5 A-5')
        rn = roman.RomanNumeral('viio65', k)
        self.assertEqual(p(rn), 'D4 F4 A-4 B4')
        rn = roman.RomanNumeral('viio43', k)
        self.assertEqual(p(rn), 'F4 A-4 B4 D5')
        rn = roman.RomanNumeral('viio42', k)
        self.assertEqual(p(rn), 'A-4 B4 D5 F5')

        rn = roman.RomanNumeral('vii/o7', k)
        self.assertEqual(p(rn), 'B4 D5 F5 A5')
        # noinspection SpellCheckingInspection
        rn = roman.RomanNumeral('viiø65', k)
        self.assertEqual(p(rn), 'D4 F4 A4 B4')
        # noinspection SpellCheckingInspection
        rn = roman.RomanNumeral('viiø43', k)
        self.assertEqual(p(rn), 'F4 A4 B4 D5')
        rn = roman.RomanNumeral('vii/o42', k)
        self.assertEqual(p(rn), 'A4 B4 D5 F5')

        rn = roman.RomanNumeral('VII', k)
        self.assertEqual(p(rn), 'B-4 D5 F5')
        rn = roman.RomanNumeral('VII6', k)
        self.assertEqual(p(rn), 'D4 F4 B-4')
        rn = roman.RomanNumeral('VII64', k)
        self.assertEqual(p(rn), 'F4 B-4 D5')

        rn = roman.RomanNumeral('bVII', k)
        self.assertEqual(p(rn), 'B--4 D-5 F-5')
        rn = roman.RomanNumeral('bVII6', k)
        self.assertEqual(p(rn), 'D-4 F-4 B--4')
        rn = roman.RomanNumeral('bVII64', k)
        self.assertEqual(p(rn), 'F-4 B--4 D-5')

        rn = roman.RomanNumeral('bvii', k)
        self.assertEqual(p(rn), 'B-4 D-5 F5')
        rn = roman.RomanNumeral('bvii6', k)
        self.assertEqual(p(rn), 'D-4 F4 B-4')
        rn = roman.RomanNumeral('bvii64', k)
        self.assertEqual(p(rn), 'F4 B-4 D-5')

        rn = roman.RomanNumeral('bviio', k)
        self.assertEqual(p(rn), 'B-4 D-5 F-5')
        rn = roman.RomanNumeral('bviio6', k)
        self.assertEqual(p(rn), 'D-4 F-4 B-4')
        rn = roman.RomanNumeral('bviio64', k)
        self.assertEqual(p(rn), 'F-4 B-4 D-5')

        rn = roman.RomanNumeral('#VII', k)
        self.assertEqual(p(rn), 'B4 D#5 F#5')
        rn = roman.RomanNumeral('#vii', k)
        self.assertEqual(p(rn), 'B#4 D#5 F##5')

        rn = roman.RomanNumeral('VII+', k)
        self.assertEqual(p(rn), 'B-4 D5 F#5')

    def testAllFormsOfVI(self):
        from music21 import roman

        def p(c):
            return ' '.join([x.nameWithOctave for x in c.pitches])

        k = key.Key('c')
        rn = roman.RomanNumeral('vio', k)
        self.assertEqual(p(rn), 'A4 C5 E-5')
        rn = roman.RomanNumeral('vio6', k)
        self.assertEqual(p(rn), 'C4 E-4 A4')
        rn = roman.RomanNumeral('vio64', k)
        self.assertEqual(p(rn), 'E-4 A4 C5')

        rn = roman.RomanNumeral('vi', k)
        self.assertEqual(p(rn), 'A4 C5 E5')
        rn = roman.RomanNumeral('vi6', k)
        self.assertEqual(p(rn), 'C4 E4 A4')
        rn = roman.RomanNumeral('vi64', k)
        self.assertEqual(p(rn), 'E4 A4 C5')

        rn = roman.RomanNumeral('vio7', k)
        self.assertEqual(p(rn), 'A4 C5 E-5 G-5')
        rn = roman.RomanNumeral('vio65', k)
        self.assertEqual(p(rn), 'C4 E-4 G-4 A4')
        rn = roman.RomanNumeral('vio43', k)
        self.assertEqual(p(rn), 'E-4 G-4 A4 C5')
        rn = roman.RomanNumeral('vio42', k)
        self.assertEqual(p(rn), 'G-4 A4 C5 E-5')

        rn = roman.RomanNumeral('viø7', k)
        self.assertEqual(p(rn), 'A4 C5 E-5 G5')
        rn = roman.RomanNumeral('vi/o65', k)
        self.assertEqual(p(rn), 'C4 E-4 G4 A4')
        rn = roman.RomanNumeral('vi/o43', k)
        self.assertEqual(p(rn), 'E-4 G4 A4 C5')
        rn = roman.RomanNumeral('viø42', k)
        self.assertEqual(p(rn), 'G4 A4 C5 E-5')

        rn = roman.RomanNumeral('VI', k)
        self.assertEqual(p(rn), 'A-4 C5 E-5')
        rn = roman.RomanNumeral('VI6', k)
        self.assertEqual(p(rn), 'C4 E-4 A-4')
        rn = roman.RomanNumeral('VI64', k)
        self.assertEqual(p(rn), 'E-4 A-4 C5')

        rn = roman.RomanNumeral('bVI', k)
        self.assertEqual(p(rn), 'A--4 C-5 E--5')
        rn = roman.RomanNumeral('bVI6', k)
        self.assertEqual(p(rn), 'C-4 E--4 A--4')
        rn = roman.RomanNumeral('bVI64', k)
        self.assertEqual(p(rn), 'E--4 A--4 C-5')

        rn = roman.RomanNumeral('bvi', k)
        self.assertEqual(p(rn), 'A-4 C-5 E-5')
        rn = roman.RomanNumeral('bvi6', k)
        self.assertEqual(p(rn), 'C-4 E-4 A-4')
        rn = roman.RomanNumeral('bvi64', k)
        self.assertEqual(p(rn), 'E-4 A-4 C-5')

        rn = roman.RomanNumeral('bvio', k)
        self.assertEqual(p(rn), 'A-4 C-5 E--5')
        rn = roman.RomanNumeral('bvio6', k)
        self.assertEqual(p(rn), 'C-4 E--4 A-4')
        rn = roman.RomanNumeral('bvio64', k)
        self.assertEqual(p(rn), 'E--4 A-4 C-5')

        rn = roman.RomanNumeral('#VI', k)
        self.assertEqual(p(rn), 'A4 C#5 E5')
        rn = roman.RomanNumeral('#vi', k)
        self.assertEqual(p(rn), 'A#4 C#5 E#5')

        rn = roman.RomanNumeral('VI+', k)
        self.assertEqual(p(rn), 'A-4 C5 E5')

    def testAugmented(self):
        from music21 import roman

        def p(c):
            return ' '.join([x.nameWithOctave for x in c.pitches])

        def test_numeral(country, figure_list, result, key_in='a'):
            for figure in figure_list:
                for with_plus in ('', '+'):
                    for kStr in (key_in, key_in.upper()):
                        key_obj = key.Key(kStr)
                        rn_str = country + with_plus + figure
                        rn = roman.RomanNumeral(rn_str, key_obj)
                        self.assertEqual(p(rn), result)


        test_numeral('It', ['6', ''], 'F5 A5 D#6')
        test_numeral('Ger', ['', '6', '65', '6/5'], 'F5 A5 C6 D#6')
        test_numeral('Fr', ['', '6', '43', '4/3'], 'F5 A5 B5 D#6')
        test_numeral('Sw', ['', '6', '43', '4/3'], 'F5 A5 B#5 D#6')

        # these I worked out in C, not A ...  :-)
        test_numeral('It', ['53'], 'F#4 A-4 C5', 'C')
        test_numeral('It', ['64'], 'C4 F#4 A-4', 'C')
        test_numeral('Ger', ['7'], 'F#4 A-4 C5 E-5', 'C')
        test_numeral('Ger', ['43'], 'C4 E-4 F#4 A-4', 'C')
        test_numeral('Ger', ['42'], 'E-4 F#4 A-4 C5', 'C')
        test_numeral('Fr', ['7'], 'D4 F#4 A-4 C5', 'C')
        test_numeral('Fr', ['65'], 'F#4 A-4 C5 D5', 'C')
        test_numeral('Fr', ['42'], 'C4 D4 F#4 A-4', 'C')
        test_numeral('Sw', ['7'], 'D#4 F#4 A-4 C5', 'C')
        test_numeral('Sw', ['65'], 'F#4 A-4 C5 D#5', 'C')
        test_numeral('Sw', ['42'], 'C4 D#4 F#4 A-4', 'C')

    def test_augmented_round_trip(self):
        # only testing properly spelled forms for input, since output will
        # always be properly spelled
        augTests = [
            'It6', 'It64', 'It53',
            'Ger65', 'Ger43', 'Ger42', 'Ger7',
            'Fr43', 'Fr7', 'Fr42', 'Fr65',
            'Sw43', 'Sw7', 'Sw42', 'Sw65',
        ]

        c_minor = key.Key('c')
        c_major = key.Key('C')

        for aug6 in augTests:
            rn = RomanNumeral(aug6, c_minor)
            ch = chord.Chord(rn.pitches)
            # without key
            rn_out = romanNumeralFromChord(ch)
            if aug6 not in ('Ger7', 'Fr7'):
                # TODO(msc): fix these -- currently giving iø7 and Iø7 respectively
                self.assertEqual(rn.figure, rn_out.figure, f'{aug6}: {rn_out}')
                self.assertEqual(rn_out.key.tonicPitchNameWithCase, 'c')

            # with key
            rn_out = romanNumeralFromChord(ch, c_minor)
            self.assertEqual(rn.figure, rn_out.figure, f'{aug6}: {rn_out}')

            rn_out = romanNumeralFromChord(ch, c_major)
            self.assertEqual(rn.figure, rn_out.figure, f'{aug6}: {rn_out}')

    def testSetFigureAgain(self):
        '''
        Setting the figure again doesn't double the alterations
        '''
        ger = RomanNumeral('Ger7')
        pitches_before = ger.pitches
        ger.figure = 'Ger7'
        self.assertEqual(ger.pitches, pitches_before)

        sharp_four = RomanNumeral('#IV')
        pitches_before = sharp_four.pitches
        sharp_four.figure = '#IV'
        self.assertEqual(sharp_four.pitches, pitches_before)

    def testZeroForDiminished(self):
        from music21 import roman
        rn = roman.RomanNumeral('vii07', 'c')
        self.assertEqual([p.name for p in rn.pitches], ['B', 'D', 'F', 'A-'])
        rn = roman.RomanNumeral('vii/07', 'c')
        self.assertEqual([p.name for p in rn.pitches], ['B', 'D', 'F', 'A'])
        # However, when there is a '10' somewhere in the figure, don't replace
        #   the 0 (this occurs in DCML corpora)
        rn = roman.RomanNumeral('V7[add10]', 'c')
        self.assertEqual([p.name for p in rn.pitches], ['G', 'B-', 'B', 'D', 'F'])

    def testIII7(self):
        c = chord.Chord(['E4', 'G4', 'B4', 'D5'])
        k = key.Key('C')
        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, 'iii7')

    def testHalfDimMinor(self):
        c = chord.Chord(['A3', 'C4', 'E-4', 'G4'])
        k = key.Key('c')
        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, 'viø7')

    def testHalfDimIII(self):
        c = chord.Chord(['F#3', 'A3', 'E4', 'C5'])
        k = key.Key('d')
        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, '#iiiø7')

    def testAugmentedOctave(self):
        c = chord.Chord(['C4', 'E5', 'G5', 'C#6'])
        k = key.Key('C')
        f = postFigureFromChordAndKey(c, k)
        self.assertEqual(f, '#853')

        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, 'I#853')

    def testSecondaryAugmentedSixth(self):
        rn = RomanNumeral('Ger65/IV', 'C')
        self.assertEqual([p.name for p in rn.pitches], ['D-', 'F', 'A-', 'B'])

    def testV7b5(self):
        rn = RomanNumeral('V7b5', 'C')
        self.assertEqual([p.name for p in rn.pitches], ['G', 'D-', 'F'])

    def testNo5(self):
        rn = RomanNumeral('viio[no5]', 'a')
        self.assertEqual([p.name for p in rn.pitches], ['G#', 'B'])

        rn = RomanNumeral('vii[no5]', 'a')
        self.assertEqual([p.name for p in rn.pitches], ['G#', 'B'])

    def testNeapolitan(self):
        # False:
        falseFigures = ('III',  # Not II
                        'II',  # II but not bII (no frontAlterationAccidental)
                        '#II',  # rn.frontAlterationAccidental != flat
                        'bII',  # bII but not bII6 and default requires first inv
                        'bii6',  # quality != major
                        '#I',  # Enharmonics do not count
                        )
        for fig in falseFigures:
            with self.subTest(figure=fig):
                rn = RomanNumeral(fig, 'a')
                self.assertFalse(rn.isNeapolitan())

        # True:
        trueFigures = ('bII6',
                       'N6',  # Maps to bII6
                       'N'  # NB: also maps to bII6
                       )
        for fig in trueFigures:
            with self.subTest(figure=fig):
                rn = RomanNumeral(fig, 'a')
                self.assertTrue(rn.isNeapolitan())

        # Root position (conditionally true)
        rootPosition = ('N53',  # NB: explicit 53 required
                        'bII',
                        )

        for fig in rootPosition:
            with self.subTest(figure=fig):
                rn = RomanNumeral(fig, 'a')
                self.assertFalse(rn.isNeapolitan())
                self.assertTrue(rn.isNeapolitan(require1stInversion=False))

    def testMixture(self):
        for fig in ['i', 'iio', 'bIII', 'iv', 'v', 'bVI', 'bVII', 'viio7']:
            # True, major key:
            self.assertTrue(RomanNumeral(fig, 'A').isMixture())
            # False, minor key:
            self.assertFalse(RomanNumeral(fig, 'a').isMixture())

        for fig in ['I', 'ii', '#iii', 'IV', 'vi', 'viiø7']:  # NB not #vi
            # False, major key:
            self.assertFalse(RomanNumeral(fig, 'A').isMixture())
            # True, minor key:
            self.assertTrue(RomanNumeral(fig, 'a').isMixture())

    def testMinorTonic7InMajor(self):
        rn = RomanNumeral('i7', 'C')
        pitchStrings = [p.name for p in rn.pitches]
        self.assertEqual(pitchStrings, ['C', 'E-', 'G', 'B-'])
        for k in (key.Key('C'), key.Key('c')):
            ch1 = chord.Chord('C4 E-4 G4 B-4')
            rn2 = romanNumeralFromChord(ch1, k)
            self.assertEqual(rn2.figure, 'i7')
            ch = chord.Chord('E-4 G4 B-4 C5')
            rn = romanNumeralFromChord(ch, k)
            self.assertEqual(rn.figure, 'i65')

        for k in (key.Key('G'), key.Key('g')):
            ch = chord.Chord('G4 B-4 C5 E-5')
            rn = romanNumeralFromChord(ch, k)
            self.assertEqual(rn.figure, 'iv43')
            ch = chord.Chord('B-4 C5 E-5 G5')
            rn = romanNumeralFromChord(ch, k)
            self.assertEqual(rn.figure, 'iv42')

    def testMinorMajor7InMajor(self):
        def new_fig_equals_old_figure(rn_in, k='C'):
            p_old = [p.name for p in rn_in.pitches]
            rn_new = RomanNumeral(rn_in.figure, k)
            p_new = [p.name for p in rn_new.pitches]
            # order matters, octave does not
            self.assertEqual(p_old, p_new, f'{p_old} not equal {p_new} for {rn_in}')

        rn = RomanNumeral('i7[#7]', 'C')
        pitchStrings = [p.name for p in rn.pitches]
        self.assertEqual(pitchStrings, ['C', 'E-', 'G', 'B'])
        ch1 = chord.Chord('C4 E-4 G4 B4')
        rn1 = romanNumeralFromChord(ch1, 'C')
        self.assertEqual(rn1.figure, 'i7[#7]')
        new_fig_equals_old_figure(rn1)
        ch2 = chord.Chord('E-4 G4 B4 C5')
        rn2 = romanNumeralFromChord(ch2, 'C')
        self.assertEqual(rn2.figure, 'i65[#7]')
        new_fig_equals_old_figure(rn2)

        ch3 = chord.Chord('G4 B4 C5 E-5')
        rn3 = romanNumeralFromChord(ch3, 'G')
        self.assertEqual(rn3.figure, 'iv43[#7]')
        new_fig_equals_old_figure(rn3, 'G')
        ch4 = chord.Chord('B4 C5 E-5 G5')
        rn4 = romanNumeralFromChord(ch4, 'G')
        self.assertEqual(rn4.figure, 'iv42[#7]')
        new_fig_equals_old_figure(rn4, 'G')

        # in minor these are more normal #7:
        rn1 = romanNumeralFromChord(ch1, 'c')
        self.assertEqual(rn1.figure, 'i#7')
        new_fig_equals_old_figure(rn1, 'c')
        rn2 = romanNumeralFromChord(ch2, 'c')
        self.assertEqual(rn2.figure, 'i65[#7]')
        new_fig_equals_old_figure(rn2, 'c')

        ch3 = chord.Chord('G4 B4 C5 E-5')
        rn3 = romanNumeralFromChord(ch3, 'g')
        self.assertEqual(rn3.figure, 'iv43[#7]')
        new_fig_equals_old_figure(rn3, 'g')
        # except third-inversion
        ch4 = chord.Chord('B4 C5 E-5 G5')
        rn4 = romanNumeralFromChord(ch4, 'g')
        self.assertEqual(rn4.figure, 'iv42[#7]')
        new_fig_equals_old_figure(rn4, 'g')

    def test_addedPitch_sharp7(self):
        '''
        Fixes issue #1369
        '''
        rn = RomanNumeral('IV[add#7]', 'C')
        self.assertEqual(rn.bass().nameWithOctave, 'F4')
        self.assertEqual([p.nameWithOctave for p in rn.pitches],
                         ['F4', 'A4', 'C5', 'E#5'])

    def test_sevenths_on_alteration(self):
        rn = RomanNumeral('bII7', 'c')
        self.assertEqual(rn.seventh.name, 'C')
        rn = RomanNumeral('bII65', 'c')
        self.assertEqual(rn.seventh.name, 'C')

        # make sure that it works around octave breaks too.
        rn = RomanNumeral('bII65', 'b')
        self.assertEqual(rn.seventh.name, 'B')

        rn = RomanNumeral('bVII7', 'c', seventhMinor=Minor67Default.CAUTIONARY)
        self.assertEqual(rn.seventh.name, 'A-')
        rn = RomanNumeral('bVII7', 'C', seventhMinor=Minor67Default.CAUTIONARY)
        self.assertEqual(rn.seventh.name, 'A')

    def test_int_figure_case_matters(self):
        '''
        Fix for https://github.com/cuthbertLab/music21/issues/1450
        '''
        minorKeyObj = key.Key('c')
        rn = RomanNumeral(2, minorKeyObj)
        self.assertEqual(rn.figure, 'ii')
        rn = RomanNumeral(2, minorKeyObj, caseMatters=False)
        self.assertEqual(rn.figure, 'II')

        rn = RomanNumeral(4, 'c')
        self.assertEqual(rn.figure, 'iv')

        rn = RomanNumeral(6, scale.MajorScale('c'))
        self.assertEqual(rn.figure, 'vi')

        # Major still works
        rn = RomanNumeral(4, 'C')
        self.assertEqual(rn.figure, 'IV')

    def test_scale_caching(self):
        mcs = scale.ConcreteScale('c', pitches=('C', 'D', 'E', 'F', 'G', 'A', 'B'))
        rn = mcs.romanNumeral('IV7')
        self.assertEqual([p.unicodeName for p in rn.pitches], ['F', 'A', 'C', 'E'])
        mcs = scale.ConcreteScale('c', pitches=('C', 'D', 'E-', 'F', 'G', 'A', 'B'))
        rn = mcs.romanNumeral('IV7')
        self.assertEqual([p.unicodeName for p in rn.pitches], ['F', 'A', 'C', 'E♭'])


class TestExternal(unittest.TestCase):
    show = True

    def testFromChordify(self):
        from music21 import corpus
        b = corpus.parse('bwv103.6')
        c = b.chordify()
        cKey = b.analyze('key')
        figuresCache = {}
        for x in c.recurse():
            if isinstance(x, chord.Chord):
                rnc = romanNumeralFromChord(x, cKey)
                figure = rnc.figure
                if figure not in figuresCache:
                    figuresCache[figure] = 1
                else:
                    figuresCache[figure] += 1
                x.lyric = figure

        if self.show:
            sortedList = sorted(figuresCache, key=figuresCache.get, reverse=True)
            for thisFigure in sortedList:
                print(thisFigure, figuresCache[thisFigure])

        b.insert(0, c)
        if self.show:
            b.show()


# -----------------------------------------------------------------------------
_DOC_ORDER = [
    RomanNumeral,
]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testV7b5')
