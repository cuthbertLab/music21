# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         roman.py
# Purpose:      music21 classes for doing Roman Numeral / Tonal analysis
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Music21 class for dealing with Roman Numeral analysis
'''
import enum
import unittest
import copy
import re
from typing import Union, Optional, List, Tuple

from collections import namedtuple

from music21 import environment
from music21.figuredBass import notation as fbNotation
from music21 import scale
from music21 import pitch
from music21 import key
from music21 import note
from music21 import interval
from music21 import harmony
from music21 import exceptions21
from music21 import common
from music21 import chord

FigureTuple = namedtuple('FigureTuple', 'aboveBass alter prefix')
ChordFigureTuple = namedtuple('ChordFigureTuple', 'aboveBass alter prefix pitch')


_MOD = 'roman'
environLocal = environment.Environment(_MOD)

# TODO: setting inversion should change the figure

# -----------------------------------------------------------------------------


SHORTHAND_RE = re.compile(r'#*-*b*o*[1-9xyz]')
ENDWITHFLAT_RE = re.compile(r'[b\-]$')

# cache all Key/Scale objects created or passed in; re-use
# permits using internally scored pitch segments
_scaleCache = {}
_keyCache = {}

# create a single notation object for RN initialization, for type-checking,
# but it will always be replaced.
_NOTATION_SINGLETON = fbNotation.Notation()


def _getKeyFromCache(keyStr: str) -> key.Key:
    '''
    get a key from the cache if it is there; otherwise
    create a new key and put it in the cache and return it.
    '''
    if keyStr in _keyCache:
        # adding copy.copy will at least prevent small errors at a cost of only 3 nano-seconds
        # of added time.  A deepcopy, unfortunately, take 2.8ms, which is longer than not
        # caching at all.  And not caching at all really slows down things like RomanText.
        # This at least will prevent what happens if `.key.mode` is changed
        keyObj = copy.copy(_keyCache[keyStr])
    else:
        keyObj = key.Key(keyStr)
        _keyCache[keyObj.tonicPitchNameWithCase] = keyObj
    return keyObj


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
    'bb7b5b3': 'o7',
    'bb7b53': 'o7',
    # '6b5bb3': 'o65',
    'b7b5b3': 'ø7',
}

functionalityScores = {
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
    'iio43': 32,
    'iio65': 31,
    '#vio': 28,
    '#vio6': 27,
    'III': 22,
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


    Slashes don't matter

    >>> roman.expandShortHand('6/4')
    ['6', '4']

    Note that this is not where abbreviations get expanded

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
            pass  # do something for odd odd chords built on diminished triad.
    # print(inversionString, fifthName)
    return qualityName + inversionString


def postFigureFromChordAndKey(chordObj, keyObj=None):
    '''
    Returns the post RN figure for a given chord in a given key.

    If keyObj is none, it uses the root as a major key:

    >>> from music21 import roman
    >>> roman.postFigureFromChordAndKey(
    ...     chord.Chord(['F#2', 'D3', 'A-3', 'C#4']),
    ...     key.Key('C'),
    ...     )
    'o6#5b3'

    The method substitutes shorthand (e.g., '6' not '63')

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

    Returns string.
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
        isMinorTriad = chordObj.isMinorTriad()
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
    if allFigureString in figureShorthands:
        allFigureString = figureShorthands[allFigureString]

    # simplify common omissions from 7th chords
    if allFigureString in ('75', '73'):
        allFigureString = '7'

    allFigureString = correctSuffixForChordQuality(chordObj, allFigureString)

    return allFigureString


def figureTuples(chordObject, keyObject):
    '''
    Return a set of tuplets for each pitch showing the presence of a note, its
    interval above the bass its alteration (float) from a step in the given
    key, an `alterationString`, and the pitch object.

    Note though that for roman numerals, the applicable key is almost always
    the root.

    For instance, in C major, F# D A- C# would be:

    >>> from music21 import roman
    >>> roman.figureTuples(
    ...     chord.Chord(['F#2', 'D3', 'A-3', 'C#4']),
    ...     key.Key('C'),
    ...     )
    [ChordFigureTuple(aboveBass=1, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch F#2>),
     ChordFigureTuple(aboveBass=6, alter=0.0, prefix='', pitch=<music21.pitch.Pitch D3>),
     ChordFigureTuple(aboveBass=3, alter=-1.0, prefix='b', pitch=<music21.pitch.Pitch A-3>),
     ChordFigureTuple(aboveBass=5, alter=1.0, prefix='#', pitch=<music21.pitch.Pitch C#4>)]

    >>> roman.figureTuples(
    ...     chord.Chord(['E3', 'C4', 'G4', 'B-5']),
    ...     key.Key('C'),
    ...     )
    [ChordFigureTuple(aboveBass=1, alter=0.0, prefix='', pitch=<music21.pitch.Pitch E3>),
     ChordFigureTuple(aboveBass=6, alter=0.0, prefix='', pitch=<music21.pitch.Pitch C4>),
     ChordFigureTuple(aboveBass=3, alter=0.0, prefix='', pitch=<music21.pitch.Pitch G4>),
     ChordFigureTuple(aboveBass=5, alter=-1.0, prefix='b', pitch=<music21.pitch.Pitch B-5>)]

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


def figureTupleSolo(pitchObj, keyObj, bass):
    '''
    Return a single tuple for a pitch and key showing the interval above
    the bass, its alteration from a step in the given key, an alteration
    string, and the pitch object.

    For instance, in C major, an A-3 above an F# bass would be:

    >>> from music21 import roman
    >>> roman.figureTupleSolo(
    ...     pitch.Pitch('A-3'),
    ...     key.Key('C'),
    ...     pitch.Pitch('F#2'),
    ...     )
    FigureTuple(aboveBass=3, alter=-1.0, prefix='b')

    Returns a namedtuple called a FigureTuple.
    '''
    unused_scaleStep, scaleAccidental = keyObj.getScaleDegreeAndAccidentalFromPitch(pitchObj)

    thisInterval = interval.notesToInterval(bass, pitchObj)
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
    inChord: Union[list, tuple, chord.Chord],
    inKey: key.Key
) -> Union[str, bool]:
    '''
    Returns the roman numeral string expression (either tonic or dominant) that
    best matches the inChord. Useful when you know inChord is either tonic or
    dominant, but only two pitches are provided in the chord. If neither tonic
    nor dominant is possibly correct, False is returned

    >>> from music21 import roman
    >>> roman.identifyAsTonicOrDominant(['B2', 'F5'], key.Key('C'))
    'V65'

    >>> roman.identifyAsTonicOrDominant(['B3', 'G4'], key.Key('g'))
    'i6'

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
        if oneMatches > fiveMatches and oneMatches > 0:
            oneChordIdentified = True
        elif oneMatches < fiveMatches and fiveMatches > 0:
            fiveChordIdentified = True
        else:
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


def romanInversionName(inChord, inv=None):
    '''
    Extremely similar to Chord's inversionName() method, but returns string
    values and allows incomplete triads
    '''
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


def correctRNAlterationForMinor(figureTuple, keyObj):
    '''
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




    >>> ft1 = roman.FigureTuple(aboveBass=6, alter=-1, prefix='b')

    Does nothing for major:

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


def romanNumeralFromChord(chordObj,
                          keyObj: Union[key.Key, str] = None,
                          preferSecondaryDominants=False):
    # noinspection PyShadowingNames
    '''
    Takes a chord object and returns an appropriate chord name.  If keyObj is
    omitted, the root of the chord is considered the key (if the chord has a
    major third, it's major; otherwise it's minor).  preferSecondaryDominants does not currently
    do anything.

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

    Note that vi and vii in minor signifies what you might think of
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
    '''
    aug6subs = {
        '#ivo6b3': 'It6',
        'IIø#643': 'Fr43',
        '#ii64b3': 'Sw43',
        '#ivo6bb5b3': 'Ger65',
    }
    aug6NoKeyObjectSubs = {
        'io6b3': 'It6',
        'Iø64b3': 'Fr43',
        'i64b3': 'Sw43',
        'io6b5b3': 'Ger65',
    }

    noKeyGiven = (keyObj is None)

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

    if isMajorThird:
        rootKeyObj = _getKeyFromCache(root.name.upper())
    else:
        rootKeyObj = _getKeyFromCache(root.name.lower())

    if keyObj is None:
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

    if not noKeyGiven and rnString in aug6subs and chordObj.isAugmentedSixth():
        rnString = aug6subs[rnString]
    elif noKeyGiven and rnString in aug6NoKeyObjectSubs and chordObj.isAugmentedSixth():
        rnString = aug6NoKeyObjectSubs[rnString]
        if rnString in ('It6', 'Ger65'):
            keyObj = _getKeyFromCache(chordObj.fifth.name.lower())
        elif rnString in ('Fr43', 'Sw43'):
            keyObj = _getKeyFromCache(chordObj.seventh.name.lower())

    try:
        rn = RomanNumeral(rnString, keyObj, updatePitches=False)
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

    Showing how `sixthMinor` affects the interpretation of `vi`:

    >>> vi = lambda sixChord, quality: ' '.join(p.name for p in roman.RomanNumeral(
    ...                                   sixChord, 'c',
    ...                                   sixthMinor=quality).pitches)
    >>> vi('vi', roman.Minor67Default.QUALITY)
    'A C E'
    >>> vi('vi', roman.Minor67Default.FLAT)
    'A- C- E-'
    >>> vi('vi', roman.Minor67Default.SHARP)
    'A C E'

    >>> vi('VI', roman.Minor67Default.QUALITY)
    'A- C E-'
    >>> vi('VI', roman.Minor67Default.FLAT)
    'A- C E-'
    >>> vi('VI', roman.Minor67Default.SHARP)
    'A C# E'

    For FLAT assumes lowered ^6 no matter what, while SHARP assumes raised
    ^6 no matter what.  So #vi is needed in FLAT and bVI is needed in SHARP

    >>> vi('#vi', roman.Minor67Default.FLAT)
    'A C E'
    >>> vi('bVI', roman.Minor67Default.SHARP)
    'A- C E-'


    CAUTIONARY ignores the `#` in #vi and the `b` in bVI:

    >>> vi('#vi', roman.Minor67Default.CAUTIONARY)
    'A C E'
    >>> vi('vi', roman.Minor67Default.CAUTIONARY)
    'A C E'
    >>> vi('bVI', roman.Minor67Default.CAUTIONARY)
    'A- C E-'
    >>> vi('VI', roman.Minor67Default.CAUTIONARY)
    'A- C E-'

    Whereas QUALITY is closer to what a computer would produce, since vi is already
    sharpened, #vi raises it even more.  And since VI is already flattened, bVI lowers
    it even further:

    >>> vi('vi', roman.Minor67Default.QUALITY)
    'A C E'
    >>> vi('#vi', roman.Minor67Default.QUALITY)
    'A# C# E#'
    >>> vi('VI', roman.Minor67Default.QUALITY)
    'A- C E-'
    >>> vi('bVI', roman.Minor67Default.QUALITY)
    'A-- C- E--'

    To get these odd chords with CAUTIONARY, add another sharp or flat.

    >>> vi('##vi', roman.Minor67Default.CAUTIONARY)
    'A# C# E#'
    >>> vi('bbVI', roman.Minor67Default.CAUTIONARY)
    'A-- C- E--'


    For other odd chords that are contrary to the standard minor interpretation
    in the "wrong" direction, the interpretation is the same as `QUALITY`

    a major triad on raised 6?

    >>> vi('#VI', roman.Minor67Default.QUALITY)
    'A C# E'
    >>> vi('#VI', roman.Minor67Default.CAUTIONARY)
    'A C# E'

    a minor triad on lowered 6?

    >>> vi('bvi', roman.Minor67Default.QUALITY)
    'A- C- E-'
    >>> vi('bvi', roman.Minor67Default.CAUTIONARY)
    'A- C- E-'
    '''
    QUALITY = 1
    CAUTIONARY = 2
    SHARP = 3
    FLAT = 4


# -----------------------------------------------------------------------------


class RomanException(exceptions21.Music21Exception):
    pass


class RomanNumeralException(exceptions21.Music21Exception):
    pass


# -----------------------------------------------------------------------------


class RomanNumeral(harmony.Harmony):
    '''
    A RomanNumeral object is a specialized type of
    :class:`~music21.harmony.Harmony` object that stores the function and scale
    degree of a chord within a :class:`~music21.key.Key`.

    If no Key is given then it exists as a theoretical, keyless RomanNumeral;
    e.g., V in any key. but when realized, keyless RomanNumerals are
    treated as if they are in C major).

    >>> from music21 import roman
    >>> V = roman.RomanNumeral('V')  # could also use 5
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

    >>> neapolitan = roman.RomanNumeral('N6', 'c#')  # could also use 'bII6'
    >>> neapolitan.key
    <music21.key.Key of c# minor>

    >>> neapolitan.isMajorTriad()
    True

    >>> neapolitan.scaleDegreeWithAlteration
    (2, <accidental flat>)

    >>> for p in neapolitan.pitches:  # default octaves
    ...     p
    <music21.pitch.Pitch F#4>
    <music21.pitch.Pitch A4>
    <music21.pitch.Pitch D5>

    >>> neapolitan2 = roman.RomanNumeral('bII6', 'g#')
    >>> [str(p) for p in neapolitan2.pitches]
    ['C#5', 'E5', 'A5']

    >>> neapolitan2.scaleDegree
    2

    >>> em = key.Key('e')
    >>> dominantV = roman.RomanNumeral('V7', em)
    >>> [str(p) for p in dominantV.pitches]
    ['B4', 'D#5', 'F#5', 'A5']

    >>> minorV = roman.RomanNumeral('V43', em, caseMatters=False)
    >>> [str(p) for p in minorV.pitches]
    ['F#4', 'A4', 'B4', 'D5']


    In minor -- VII and VI are assumed to refer to the flattened scale degree.
    vii, viio, viio7, viiø7 and vi, vio, vio7, viø7 refer to the sharpened scale
    degree.  To get a minor triad on lowered 6 for instance, you will need to use 'bvi'
    while to get a major triad on raised 6, use '#VI'.

    The actual rule is that if the chord implies minor, diminished, or half-diminished,
    an implied "#" is read before the figure.  Anything else does not add the sharp.
    The lowered (natural minor) is the assumed basic chord.

    >>> majorFlatSeven = roman.RomanNumeral('VII', em)
    >>> [str(p) for p in majorFlatSeven.pitches]
    ['D5', 'F#5', 'A5']

    >>> minorSharpSeven = roman.RomanNumeral('vii', em)
    >>> [str(p) for p in minorSharpSeven.pitches]
    ['D#5', 'F#5', 'A#5']

    >>> majorFlatSix = roman.RomanNumeral('VI', em)
    >>> [str(p) for p in majorFlatSix.pitches]
    ['C5', 'E5', 'G5']

    >>> minorSharpSix = roman.RomanNumeral('vi', em)
    >>> [str(p) for p in minorSharpSix.pitches]
    ['C#5', 'E5', 'G#5']


    These rules can be changed by passing in a `sixthMinor` or `seventhMinor` parameter set to
    a member of :class:`music21.roman.Minor67Default`:

    >>> majorSharpSeven = roman.RomanNumeral('VII', em, seventhMinor=roman.Minor67Default.SHARP)
    >>> [str(p) for p in majorSharpSeven.pitches]
    ['D#5', 'F##5', 'A#5']

    For instance, if you prefer a harmonic minor context where VI (or vi) always refers
    to the lowered 6 and viio (or VII) always refers to the raised 7, send along
    `sixthMinor=roman.Minor67Default.FLAT` and `seventhMinor=roman.Minor67Default.SHARP`

    >>> dimHarmonicSeven = roman.RomanNumeral('viio', em, seventhMinor=roman.Minor67Default.SHARP)
    >>> [str(p) for p in dimHarmonicSeven.pitches]
    ['D#5', 'F#5', 'A5']

    >>> majHarmonicSeven = roman.RomanNumeral('bVII', em, seventhMinor=roman.Minor67Default.SHARP)
    >>> [str(p) for p in majHarmonicSeven.pitches]
    ['D5', 'F#5', 'A5']


    >>> majHarmonicSix = roman.RomanNumeral('VI', em, sixthMinor=roman.Minor67Default.FLAT)
    >>> [str(p) for p in majHarmonicSix.pitches]
    ['C5', 'E5', 'G5']
    >>> minHarmonicSix = roman.RomanNumeral('#vi', em, sixthMinor=roman.Minor67Default.FLAT)
    >>> [str(p) for p in minHarmonicSix.pitches]
    ['C#5', 'E5', 'G#5']


    See the docs for :class:`~music21.roman.Minor67Default`
    for more information on configuring sixth and seventh interpretation in minor
    along with the useful `CAUTIONARY` setting where CAUTIONARY sharp and flat accidentals
    are allowed but not required.


    Either of these is the same way of getting a minor iii in a minor key:

    >>> minoriii = roman.RomanNumeral('iii', em, caseMatters=True)
    >>> [str(p) for p in minoriii.pitches]
    ['G4', 'B-4', 'D5']

    >>> minoriiiB = roman.RomanNumeral('IIIb', em, caseMatters=False)
    >>> [str(p) for p in minoriiiB.pitches]
    ['G4', 'B-4', 'D5']

    `caseMatters=False` will prevent `sixthMinor` or `seventhMinor` from having effect.
    >>> vii = roman.RomanNumeral('viio', 'a', caseMatters=False,
    ...                           seventhMinor=roman.Minor67Default.QUALITY)
    >>> [str(p) for p in vii.pitches]
    ['G5', 'B-5', 'D-6']

    Can also take a scale object, here we build a first-inversion chord
    on the raised-three degree of D-flat major, that is, F#-major (late
    Schubert would be proud.)

    >>> sharp3 = roman.RomanNumeral('#III6', scale.MajorScale('D-'))
    >>> sharp3.scaleDegreeWithAlteration
    (3, <accidental sharp>)

    >>> [str(p) for p in sharp3.pitches]
    ['A#4', 'C#5', 'F#5']

    >>> sharp3.figure
    '#III6'

    Figures can be changed and pitches will change.

    >>> sharp3.figure = 'V'
    >>> [str(p) for p in sharp3.pitches]
    ['A-4', 'C5', 'E-5']

    >>> leadingToneSeventh = roman.RomanNumeral(
    ...     'viio', scale.MajorScale('F'))
    >>> [str(p) for p in leadingToneSeventh.pitches]
    ['E5', 'G5', 'B-5']

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
    >>> [str(p) for p in alteredChordHalfDim3rdInv.pitches]
    ['F-4', 'G-4', 'B--4', 'D--5']

    >>> alteredChordHalfDim3rdInv.intervalVector
    [0, 1, 2, 1, 1, 1]

    >>> alteredChordHalfDim3rdInv.commonName
    'half-diminished seventh chord'

    >>> alteredChordHalfDim3rdInv.romanNumeral
    '-ii'

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
    >>> [str(p) for p in fiveOhNine.pitches]
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

    Putting it all together:

    >>> weirdChord = roman.RomanNumeral('V65[no5][add#6][b3]', key.Key('C'))
    >>> [str(p) for p in weirdChord.pitches]
    ['B-4', 'E#5', 'F5', 'G5']
    >>> weirdChord.root()
    <music21.pitch.Pitch G5>

    Other scales besides major and minor can be used.
    Just for kicks (no worries if this is goobley-gook):

    >>> ots = scale.OctatonicScale('C2')
    >>> romanNumeral = roman.RomanNumeral('I9', ots, caseMatters=False)
    >>> [str(p) for p in romanNumeral.pitches]
    ['C2', 'E-2', 'G-2', 'A2', 'C3']

    >>> romanNumeral2 = roman.RomanNumeral(
    ...     'V7#5b3', ots, caseMatters=False)
    >>> [str(p) for p in romanNumeral2.pitches]
    ['G-2', 'A-2', 'C#3', 'E-3']

    >>> romanNumeral = roman.RomanNumeral('v64/V', key.Key('e'))
    >>> romanNumeral
    <music21.roman.RomanNumeral v64/V in e minor>

    >>> romanNumeral.figure
    'v64/V'

    >>> [str(p) for p in romanNumeral.pitches]
    ['C#5', 'F#5', 'A5']

    >>> romanNumeral.secondaryRomanNumeral
    <music21.roman.RomanNumeral V in e minor>

    Dominant 7ths can be specified by putting d7 at end:

    >>> r = roman.RomanNumeral('bVIId7', key.Key('B-'))
    >>> r.figure
    'bVIId7'

    >>> [str(p) for p in r.pitches]
    ['A-5', 'C6', 'E-6', 'G-6']

    >>> r = roman.RomanNumeral('VId7')
    >>> r.figure
    'VId7'

    >>> r.key = key.Key('B-')
    >>> [str(p) for p in r.pitches]
    ['G5', 'B5', 'D6', 'F6']

    >>> r2 = roman.RomanNumeral('V42/V7/vi', key.Key('C'))
    >>> [str(p) for p in r2.pitches]
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
    >>> [str(p) for p in r.pitches]
    ['G4', 'C5', 'E5']

    >>> r = roman.RomanNumeral('Cad64', key.Key('c'))
    >>> r
    <music21.roman.RomanNumeral Cad64 in c minor>
    >>> [str(p) for p in r.pitches]
    ['G4', 'C5', 'E-5']

    Works also for secondary romans:

    >>> r = roman.RomanNumeral('Cad64/V', key.Key('c'))
    >>> r
    <music21.roman.RomanNumeral Cad64/V in c minor>
    >>> [str(p) for p in r.pitches]
    ['D5', 'G5', 'B5']


    The RomanNumeral constructor accepts a keyword 'updatePitches' which is
    passed to harmony.Harmony. By default it
    is True, but can be set to False to initialize faster if pitches are not needed.

    >>> r = roman.RomanNumeral('vio', em, updatePitches=False)
    >>> r.pitches
    ()


    OMIT_FROM_DOCS

    Things that were giving us trouble:

    >>> dminor = key.Key('d')
    >>> rn = roman.RomanNumeral('iiø65', dminor)
    >>> [str(p) for p in rn.pitches]
    ['G4', 'B-4', 'D5', 'E5']

    >>> rn.romanNumeral
    'ii'

    >>> rn3 = roman.RomanNumeral('III', dminor)
    >>> [str(p) for p in rn3.pitches]
    ['F4', 'A4', 'C5']

    Should be the same as above no matter when the key is set:

    >>> r = roman.RomanNumeral('VId7', key.Key('B-'))
    >>> [str(p) for p in r.pitches]
    ['G5', 'B5', 'D6', 'F6']

    >>> r.key = key.Key('B-')
    >>> [str(p) for p in r.pitches]
    ['G5', 'B5', 'D6', 'F6']

    This was getting B-flat.

    >>> r = roman.RomanNumeral('VId7')
    >>> r.key = key.Key('B-')
    >>> [str(p) for p in r.pitches]
    ['G5', 'B5', 'D6', 'F6']

    >>> r = roman.RomanNumeral('vio', em)
    >>> [str(p) for p in r.pitches]
    ['C#5', 'E5', 'G5']

    We can omit an arbitrary number of steps:

    >>> r = roman.RomanNumeral('Vd7[no3no5no7]', key.Key('C'))
    >>> [str(p) for p in r.pitches]
    ['G4']


    Equality:

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

    Changed in v6.5 -- caseMatters is keyword only. It along with sixthMinor and
    seventhMinor are now the only allowable keywords to pass in.
    '''
    # TODO: document better! what is inherited and what is new?

    _alterationRegex = re.compile(r'^(b+|-+|#+)')
    _omittedStepsRegex = re.compile(r'(\[(no[1-9]+)+]\s*)+')
    _addedStepsRegex = re.compile(r'\[add(b*|-*|#*)(\d+)+]\s*')
    _bracketedAlterationRegex = re.compile(r'\[(b+|-+|#+)(\d+)]')
    _augmentedSixthRegex = re.compile(r'(It|Ger|Fr|Sw)')
    _romanNumeralAloneRegex = re.compile(r'(IV|I{1,3}|VI{0,2}|iv|i{1,3}|vi{0,2}|N)')
    _secondarySlashRegex = re.compile(r'(.*?)/([#a-np-zA-NP-Z].*)')

    _DOC_ATTR = {
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

            Changed in v6.5 -- always returns a list, even if it is empty.
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
            (<modifier b <accidental flat>>,
             <modifier None None>,
             <modifier # <accidental sharp>>)
            ''',
        'frontAlterationAccidental': '''
            An optional :class:`~music21.pitch.Accidental` object
            representing the chromatic alteration of a RomanNumeral, if any

            >>> roman.RomanNumeral('bII43/vi', 'C').frontAlterationAccidental
            <accidental flat>

            >>> roman.RomanNumeral('##IV').frontAlterationAccidental
            <accidental double-sharp>

            For most roman numerals this will be None:

            >>> roman.RomanNumeral('V', 'f#').frontAlterationAccidental

            Changing this value will not change existing pitches.

            Changed in v6.5 -- always returns a string, never None
            ''',
        'frontAlterationString': '''
            A string representing the chromatic alteration of a RomanNumeral, if any

            >>> roman.RomanNumeral('bII43/vi', 'C').frontAlterationString
            'b'
            >>> roman.RomanNumeral('V', 'f#').frontAlterationString
            ''

            Changing this value will not change existing pitches.

            Changed in v6.5 -- always returns a string, never None
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

            N.B. the deprecated property `.scaleOffset` is identical
            to `.frontAlterationTransposeInterval` and will be removed in v7
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

            Changed in v6.5 -- empty RomanNumeral objects get scaleDegree 0, not None.
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
        figure: Union[str, int] = '',
        keyOrScale=None,
        *,
        caseMatters=True,
        updatePitches=True,
        sixthMinor=Minor67Default.QUALITY,
        seventhMinor=Minor67Default.QUALITY,
    ):
        self.primaryFigure: str = ''
        self.secondaryRomanNumeral: Optional['RomanNumeral'] = None
        self.secondaryRomanNumeralKey: Optional['key.Key'] = None

        self.pivotChord: Optional['RomanNumeral'] = None
        self.caseMatters: bool = caseMatters
        self.scaleCardinality: int = 7

        if isinstance(figure, int):
            self.caseMatters = False
            figure = common.toRoman(figure)

        # immediately fix low-preference figures
        if isinstance(figure, str):
            figure = figure.replace('0', 'o')  # viio7

        if isinstance(figure, str):
            # /o is just a shorthand for ø -- so it should not be stored.
            figure = figure.replace('/o', 'ø')

        # end immediate fixes


        # Store raw figure before calling setKeyOrScale:
        self._figure = figure
        # This is set when _setKeyOrScale() is called:
        self._scale = None
        self.scaleDegree: int = 0
        self.frontAlterationString: str = ''
        self.frontAlterationTransposeInterval: Optional[interval.Interval] = None
        self.frontAlterationAccidental: Optional[pitch.Accidental] = None
        self.romanNumeralAlone: str = ''
        self.figuresWritten: str = ''
        self.figuresNotationObj: fbNotation.Notation = _NOTATION_SINGLETON
        if not figure:
            self.figuresNotationObj = fbNotation.Notation()  # do not allow changing singleton

        self.impliedQuality: str = ''

        # scaleOffset is completely redundant with frontAlterationTransposeInterval
        # and will be removed in v7.0.
        self.scaleOffset: Optional[interval.Interval] = None

        self.impliedScale: Optional[scale.Scale] = None
        self.useImpliedScale: bool = False
        self.bracketedAlterations: List[Tuple[str, int]] = []
        self.omittedSteps: List[int] = []
        self.addedSteps: List[Tuple[str, int]] = []
        # do not update pitches.
        self._parsingComplete = False
        self.key = keyOrScale
        self.sixthMinor = sixthMinor
        self.seventhMinor = seventhMinor

        super().__init__(figure, updatePitches=updatePitches)
        self._parsingComplete = True
        self._functionalityScore = None

        # It is sometimes helpful to know if this is the first chord after a
        # key change.  This has been moved to Editorial immediately, and will
        # be REMOVED in v7
        self.followsKeyChange = False
        self.editorial.followsKeyChange = False

    # SPECIAL METHODS #

    def _reprInternal(self):
        if hasattr(self.key, 'tonic'):
            return str(self.figureAndKey)
        else:
            return self.figure

    def __eq__(self, other: 'RomanNumeral') -> bool:
        '''
        Compare equality, just based on NotRest and on figure and key
        '''
        if not note.NotRest.__eq__(self, other):
            return False
        if self.key != other.key:
            return False
        if self.figure != other.figure:
            return False
        return True

    # PRIVATE METHODS #
    def _parseFigure(self):
        '''
        Parse the .figure object into its component parts.

        Called from the superclass, Harmony.__init__()
        '''
        if not isinstance(self._figure, str):  # pragma: no cover
            raise RomanException(f'got a non-string figure: {self._figure!r}')

        if not self.useImpliedScale:
            useScale = self._scale
        else:
            useScale = self.impliedScale

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
        workingFigure = re.sub('^N', 'bII6', workingFigure)

        workingFigure = self._parseFrontAlterations(workingFigure)
        workingFigure, useScale = self._parseRNAloneAmidstAug6(workingFigure, useScale)
        workingFigure = self._setImpliedQualityFromString(workingFigure)
        workingFigure = self._adjustMinorVIandVIIByQuality(workingFigure, useScale)

        self.figuresWritten = workingFigure
        shFig = ','.join(expandShortHand(workingFigure))
        self.figuresNotationObj = fbNotation.Notation(shFig)

    def _setImpliedQualityFromString(self, workingFigure):
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
        elif workingFigure.endswith('d7'):
            # this one is different
            workingFigure = workingFigure[:-2] + '7'
            impliedQuality = 'dominant-seventh'
            # impliedQualitySymbol = '(dom7)'
        elif (self.caseMatters
              and self.romanNumeralAlone.upper() == self.romanNumeralAlone):
            impliedQuality = 'major'
        elif (self.caseMatters
              and self.romanNumeralAlone.lower() == self.romanNumeralAlone):
            impliedQuality = 'minor'
        self.impliedQuality = impliedQuality
        return workingFigure

    def _correctBracketedPitches(self):
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

    def _findSemitoneSizeForQuality(self, impliedQuality):
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
        '''
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
        elif impliedQuality == 'dominant-seventh':
            correctSemitones = (4, 7, 10)
        else:
            correctSemitones = ()

        return correctSemitones

    def _matchAccidentalsToQuality(self, impliedQuality):
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
        correctSemitones = self._findSemitoneSizeForQuality(impliedQuality)
        chordStepsToExamine = (3, 5, 7)
        # newPitches = []
        for i in range(len(correctSemitones)):  # 3,5,7
            thisChordStep = chordStepsToExamine[i]
            skipThisChordStep = False
            for figure in self.figuresNotationObj.figures:
                if (figure.number == thisChordStep
                        and figure.modifier.accidental is not None
                        and figure.modifier.accidental.alter != 0):
                    # for a figure like V7b5, make sure not to correct the b5 back,
                    # even though the implied quality requires a Perfect 5th.
                    skipThisChordStep = True

            if skipThisChordStep:
                continue
            thisCorrect = correctSemitones[i]
            thisSemis = self.semitonesFromChordStep(thisChordStep)
            if thisSemis is None:
                continue
            if thisSemis == thisCorrect:
                continue

            correctedSemis = thisCorrect - thisSemis
            if correctedSemis >= 6:
                correctedSemis = -1 * (12 - correctedSemis)
            elif correctedSemis <= -6:
                correctedSemis += 12

            faultyPitch = self.getChordStep(thisChordStep)
            if faultyPitch is None:  # pragma: no cover
                raise RomanException(
                    'this is very odd... should have been caught in semitonesFromChordStep')
            if faultyPitch.accidental is None:
                faultyPitch.accidental = pitch.Accidental(correctedSemis)
            else:
                acc = faultyPitch.accidental
                correctedSemis += acc.alter
                if correctedSemis >= 6:
                    correctedSemis = -1 * (12 - correctedSemis)
                elif correctedSemis <= -6:
                    correctedSemis += 12

                acc.set(correctedSemis)

    def _correctForSecondaryRomanNumeral(self, useScale, figure=None):
        '''
        Creates .secondaryRomanNumeral object and .secondaryRomanNumeralKey Key object
        inside the RomanNumeral object (recursively in case of V/V/V/V etc.) and returns
        the figure and scale that should be used instead of figure for further working.

        Returns a tuple of (newFigure, newScale).
        In case there is no secondary slash, returns the original figure and the original scale.

        If figure is None, uses newFigure.

        >>> k = key.Key('C')
        >>> r = roman.RomanNumeral('I', k)  # will not be used below...
        >>> r._correctForSecondaryRomanNumeral(k)  # uses 'I'. nothing should change...
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

        Recursive...

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
        match = self._secondarySlashRegex.match(figure)
        if match:
            primaryFigure = match.group(1)
            secondaryFigure = match.group(2)
            secondaryRomanNumeral = RomanNumeral(
                secondaryFigure,
                useScale,
                caseMatters=self.caseMatters,
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

            # TODO: this should use a KeyCache...
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

    def _parseOmittedSteps(self, workingFigure):
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

    def _parseAddedSteps(self, workingFigure):
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

    def _parseBracketedAlterations(self, workingFigure):
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

    def _parseFrontAlterations(self, workingFigure):
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
        <accidental flat>
        '''
        frontAlterationString = ''  # the b in bVI, or the '#' in #vii
        frontAlterationTransposeInterval = None
        frontAlterationAccidental = None
        match = self._alterationRegex.match(workingFigure)
        if match:
            group = match.group()
            alteration = len(group)
            if group[0] in ('b', '-'):
                alteration *= -1  # else sharp...
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

        # Remove this in v7.
        self.scaleOffset = self.frontAlterationTransposeInterval
        return workingFigure

    def _parseRNAloneAmidstAug6(self, workingFigure, useScale):
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
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('Fr+6', useScale)
        >>> workingFig
        '+6'
        >>> outScale
        <music21.key.Key of c minor>
        >>> rn.scaleDegree
        2

        >>> rn = roman.RomanNumeral()
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('Ger65', useScale)
        >>> rn.scaleDegreeWithAlteration
        (4, <accidental sharp>)

        >>> rn = roman.RomanNumeral()
        >>> workingFig, outScale = rn._parseRNAloneAmidstAug6('It6', scale.MajorScale('C'))
        >>> outScale
        <music21.key.Key of c minor>
        '''
        if (not self._romanNumeralAloneRegex.match(workingFigure)
                and not self._augmentedSixthRegex.match(workingFigure)):
            raise RomanException(f'No roman numeral found in {workingFigure!r}')  # pragma: no cover

        if self._augmentedSixthRegex.match(workingFigure):
            # NB -- could be Key or Scale
            if (('Key' in useScale.classes and useScale.mode == 'major')
                    or ('DiatonicScale' in useScale.classes and useScale.type == 'major')):
                useScale = key.Key(useScale.tonic, 'minor')
                self.impliedScale = useScale
                self.useImpliedScale = True
                # Set secondary key to minor, if any
                if self.secondaryRomanNumeralKey is not None:
                    self.secondaryRomanNumeralKey = key.Key(
                        self.secondaryRomanNumeralKey.tonic, 'minor')
            rm = self._augmentedSixthRegex.match(workingFigure)
            romanNumeralAlone = rm.group(1)
            if romanNumeralAlone in ('It', 'Ger'):
                self.scaleDegree = 4
                self.frontAlterationAccidental = pitch.Accidental('sharp')
            elif romanNumeralAlone in ('Fr',):
                self.scaleDegree = 2
            elif romanNumeralAlone in ('Sw',):
                self.scaleDegree = 2
                self.frontAlterationAccidental = pitch.Accidental('sharp')

            workingFigure = self._augmentedSixthRegex.sub('', workingFigure)
            self.romanNumeralAlone = romanNumeralAlone
            if romanNumeralAlone != 'Fr':
                fixTuple = ('#', 1)
                self.bracketedAlterations.append(fixTuple)
            if romanNumeralAlone in ('Fr', 'Sw'):
                fixTuple = ('#', 3)
                self.bracketedAlterations.append(fixTuple)
        else:
            rm = self._romanNumeralAloneRegex.match(workingFigure)
            romanNumeralAlone = rm.group(1)
            self.scaleDegree = common.fromRoman(romanNumeralAlone)
            workingFigure = self._romanNumeralAloneRegex.sub('', workingFigure)
            self.romanNumeralAlone = romanNumeralAlone

        return workingFigure, useScale

    def adjustMinorVIandVIIByQuality(self, useScale):
        '''
        Fix minor vi and vii to always be #vi and #vii if `.caseMatters`.

        >>> rn = roman.RomanNumeral()
        >>> rn.scaleDegree = 6
        >>> rn.impliedQuality = 'minor'
        >>> rn.adjustMinorVIandVIIByQuality(key.Key('c'))
        >>> rn.frontAlterationTransposeInterval
        <music21.interval.Interval A1>

        >>> rn.frontAlterationAccidental
        <accidental sharp>


        >>> rn = roman.RomanNumeral()
        >>> rn.scaleDegree = 6
        >>> rn.impliedQuality = 'major'
        >>> rn.adjustMinorVIandVIIByQuality(key.Key('c'))
        >>> rn.frontAlterationTransposeInterval is None
        True
        >>> rn.frontAlterationAccidental is None
        True

        Changed in v.6.4: public function became hook to private function having the actual guts
        '''
        unused_workingFigure = self._adjustMinorVIandVIIByQuality('', useScale)

    def _adjustMinorVIandVIIByQuality(self, workingFigure, useScale) -> str:
        '''
        Fix minor vi and vii to always be #vi and #vii if `.caseMatters`.

        Made private in v.6.4 when `workingFigure` was added to the signature
        and returned.

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
        '''
        def sharpen(wFig):
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

        def changeFrontAlteration(intV, alter):
            # fati = front alteration transpose interval
            fati = self.frontAlterationTransposeInterval
            if fati:
                newFati = interval.add([fati, intV])
                self.frontAlterationTransposeInterval = newFati
                self.frontAlterationAccidental.alter = self.frontAlterationAccidental.alter + alter
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

        # THIS IS WHERE sixthMinor and seventhMinor goes...
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

    def _updatePitches(self):
        '''
        Utility function to update the pitches to the new figure etc.
        '''
        if self.secondaryRomanNumeralKey is not None:
            useScale = self.secondaryRomanNumeralKey
        elif not self.useImpliedScale:
            useScale = self.key
        else:
            useScale = self.impliedScale

        # should be 7 but hey, octatonic scales, etc.
        # self.scaleCardinality = len(useScale.pitches) - 1
        if 'DiatonicScale' in useScale.classes:  # speed up simple case
            self.scaleCardinality = 7
        else:
            self.scaleCardinality = useScale.getDegreeMaxUnique()

        bassScaleDegree = self.bassScaleDegreeFromNotation(self.figuresNotationObj)
        bassPitch = useScale.pitchFromDegree(bassScaleDegree, direction=scale.DIRECTION_ASCENDING)
        pitches = [bassPitch]
        lastPitch = bassPitch
        numberNotes = len(self.figuresNotationObj.numbers)

        for j in range(numberNotes):
            i = numberNotes - j - 1
            thisScaleDegree = (bassScaleDegree
                                + self.figuresNotationObj.numbers[i]
                                - 1)
            newPitch = useScale.pitchFromDegree(thisScaleDegree,
                                                direction=scale.DIRECTION_ASCENDING)
            pitchName = self.figuresNotationObj.modifiers[i].modifyPitchName(newPitch.name)
            newNewPitch = pitch.Pitch(pitchName)
            newNewPitch.octave = newPitch.octave
            if newNewPitch.ps < lastPitch.ps:
                newNewPitch.octave += 1
            pitches.append(newNewPitch)
            lastPitch = newNewPitch

        if self.frontAlterationTransposeInterval:
            newPitches = []
            for thisPitch in pitches:
                newPitch = thisPitch.transpose(self.frontAlterationTransposeInterval)
                newPitches.append(newPitch)
            self.pitches = newPitches
        else:
            self.pitches = pitches

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
                # getChordStep may return False
                p = self.getChordStep(thisCS)
                if p not in (False, None):
                    omittedPitches.append(p.name)

            newPitches = []
            for thisPitch in self.pitches:
                if thisPitch.name not in omittedPitches:
                    newPitches.append(thisPitch)
            self.pitches = newPitches

        if self.addedSteps:
            for addAccidental, stepNumber in self.addedSteps:
                if '-' in addAccidental:
                    alteration = addAccidental.count('-') * -1
                else:
                    alteration = addAccidental.count('#')
                thisScaleDegree = (self.scaleDegree + stepNumber - 1)
                addedPitch = useScale.pitchFromDegree(thisScaleDegree,
                                                      direction=scale.DIRECTION_ASCENDING)
                if addedPitch.accidental is not None:
                    addedPitch.accidental.alter += alteration
                else:
                    addedPitch.accidental = pitch.Accidental(alteration)

                while addedPitch.ps < bassPitch.ps:
                    addedPitch.octave += 1

                if addedPitch not in self.pitches:
                    self.add(addedPitch)

        if not self.pitches:
            raise RomanNumeralException(
                f'_updatePitches() was unable to derive pitches from the figure: {self.figure!r}'
            )  # pragma: no cover


    # PUBLIC PROPERTIES #

    @property
    def romanNumeral(self):
        '''
        Read-only property that returns either the romanNumeralAlone (e.g. just
        II) or the frontAlterationAccidental.modifier + romanNumeralAlone (e.g. #II)

        >>> from music21 import roman
        >>> rn = roman.RomanNumeral('#II7')
        >>> rn.romanNumeral
        '#II'

        '''
        if self.frontAlterationAccidental is None:
            return self.romanNumeralAlone
        else:
            return (self.frontAlterationAccidental.modifier
                    + self.romanNumeralAlone)

    @property
    def figure(self):
        '''
        Gets or sets the entire figure (the whole enchilada).
        '''
        return self._figure

    @figure.setter
    def figure(self, newFigure):
        self._figure = newFigure
        if self._parsingComplete:
            self._parseFigure()
            self._updatePitches()

    @property
    def figureAndKey(self):
        '''
        Returns the figure and the key and mode as a string

        >>> from music21 import roman
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

        >>> from music21 import roman
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
            return  # skip...

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
                # good to go...
                if keyOrScale.tonicPitchNameWithCase not in _keyCache:
                    # store for later
                    _keyCache[keyOrScale.tonicPitchNameWithCase] = keyOrScale
            elif 'Scale' in keyClasses:
                if keyOrScale.name in _scaleCache:
                    # use stored scale as already has cache
                    keyOrScale = _scaleCache[keyOrScale.name]
                else:
                    _scaleCache[keyOrScale.name] = keyOrScale
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
    def scaleDegreeWithAlteration(self):
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
        (2, <accidental flat>)
        '''
        return self.scaleDegree, self.frontAlterationAccidental

    def bassScaleDegreeFromNotation(self, notationObject=None):
        '''
        Given a notationObject from
        :class:`music21.figuredBass.notation.Notation`
        return the scaleDegree of the bass.

        >>> from music21 import figuredBass, roman
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


        A bit slow (6 seconds for 1000 operations, but not the bottleneck)
        '''
        if notationObject is None:
            notationObject = self.figuresNotationObj
        c = pitch.Pitch('C3')
        cDNN = 22  # cDNN = c.diatonicNoteNum  # always 22
        pitches = [c]
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
            bassSD = 7
        return bassSD

    @property
    def functionalityScore(self):
        '''
        Return or set a number from 1 to 100 representing the relative
        functionality of this RN.figure (possibly given the mode, etc.).

        Numbers are ordinal, not cardinal.

        >>> from music21 import roman
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
            figures = self.figure.split('/')  # error for half-diminished in secondary...
            score = 100
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
    def functionalityScore(self, value):
        self._functionalityScore = value

    def isNeapolitan(self,
                     require1stInversion: bool = True):
        '''
        Music21's Chord module offers methods for identifying chords of a particular type,
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

        The 'N6' shorthand is accepted.

        >>> rn = roman.RomanNumeral('N6')
        >>> rn.isNeapolitan()
        True

        Requiring first inversion is optional.

        >>> rn = roman.RomanNumeral('bII')
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
        would be would be in the parallel (German: variant) major / minor
        and can therefore be thought of as a 'mixture' of major and minor modes, or
        as a 'borrowing' from the one to the other.

        Examples include i in major or I in minor (*sic*).

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

        * scale degree 7 and it's a diminished seventh specifically (b-d-f-ab).

        Minor context (example of c minor):

        * scale degree 1 and triad quality major (major tonic chord, C);

        * scale degree 2 and triad quality minor (d, not diminished);

        * scale degree #3 and triad quality minor (e);

        * scale degree 4 and triad quality major (F);

        * scale degree #6 and triad quality minor (a); and

        * scale degree 7 and it's a half diminished seventh specifically (b-d-f-a).

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
        arguably ought to be included and may be added in future.)

        Naturally, really extended usages such as scale degrees beyond 7 (in the
        Octatonic mode, for instance) also return False.

        The evaluateSecondaryNumeral parameter allows users to chose whether to consider
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

    Changed in v6.5 -- empty RomanNumerals now have figure of '' not None
    '''


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module.
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)
                self.assertIsNotNone(i)
                self.assertIsNotNone(j)

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
            len(s.flat.getElementsByClass('KeySignature')),
            targetCount,
        )
        # through sequential iteration
        s1 = copy.deepcopy(s)
        for p in s1.parts:
            for m in p.getElementsByClass('Measure'):
                for e in m.getElementsByClass('KeySignature'):
                    m.remove(e)
        self.assertEqual(len(s1.flat.getElementsByClass('KeySignature')), 0)
        s2 = copy.deepcopy(s)
        self.assertEqual(
            len(s2.flat.getElementsByClass('KeySignature')),
            targetCount,
        )
        for e in s2.flat.getElementsByClass('KeySignature'):
            for site in e.sites.get():
                if site is not None:
                    site.remove(e)
        # s2.show()
        # yield elements and containers
        s3 = copy.deepcopy(s)
        self.assertEqual(
            len(s3.flat.getElementsByClass('KeySignature')),
            targetCount,
        )
        for e in s3.recurse(streamsOnly=True):
            if 'KeySignature' in e.classes:
                # all active sites are None because of deep-copying
                if e.activeSite is not None:
                    e.activeSite.remove(e)
        # s3.show()
        # yield containers
        s4 = copy.deepcopy(s)
        self.assertEqual(
            len(s4.flat.getElementsByClass('KeySignature')),
            targetCount,
        )
        # do not remove in iteration.
        for c in list(s4.recurse(streamsOnly=False)):
            if 'Stream' in c.classes:
                for e in c.getElementsByClass('KeySignature'):
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
            '[(5, None), (7, <accidental sharp>), (2, None)]',
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

        for kStr in ('a', 'A'):
            k = key.Key(kStr)

            rn = roman.RomanNumeral('It6', k)
            self.assertEqual(p(rn), 'F5 A5 D#6')
            rn = roman.RomanNumeral('Ger65', k)
            self.assertEqual(p(rn), 'F5 A5 C6 D#6')
            rn = roman.RomanNumeral('Ger6/5', k)
            self.assertEqual(p(rn), 'F5 A5 C6 D#6')
            rn = roman.RomanNumeral('Fr43', k)
            self.assertEqual(p(rn), 'F5 A5 B5 D#6')
            rn = roman.RomanNumeral('Fr4/3', k)
            self.assertEqual(p(rn), 'F5 A5 B5 D#6')
            rn = roman.RomanNumeral('Sw43', k)
            self.assertEqual(p(rn), 'F5 A5 B#5 D#6')

    def testZeroForDiminished(self):
        from music21 import roman
        rn = roman.RomanNumeral('vii07', 'c')
        self.assertEqual([p.name for p in rn.pitches], ['B', 'D', 'F', 'A-'])
        rn = roman.RomanNumeral('vii/07', 'c')
        self.assertEqual([p.name for p in rn.pitches], ['B', 'D', 'F', 'A'])

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
        rn = RomanNumeral('III', 'a')  # Not II
        self.assertFalse(rn.isNeapolitan())
        rn = RomanNumeral('II', 'a')  # II but not bII (no frontAlterationAccidental)
        self.assertFalse(rn.isNeapolitan())
        rn = RomanNumeral('#II', 'a')  # rn.frontAlterationAccidental != flat
        self.assertFalse(rn.isNeapolitan())
        rn = RomanNumeral('bII', 'a')  # bII but not bII6 and default requires first inv
        self.assertFalse(rn.isNeapolitan())
        rn = RomanNumeral('bii6', 'a')  # quality != major
        self.assertFalse(rn.isNeapolitan())
        rn = RomanNumeral('#I', 'a')  # Enharmonics do not count
        self.assertFalse(rn.isNeapolitan())

        # True:
        rn = RomanNumeral('bII', 'a')  # bII but not bII6 and set requirement for first inv
        self.assertTrue(rn.isNeapolitan(require1stInversion=False))
        rn = RomanNumeral('bII6', 'a')
        self.assertTrue(rn.isNeapolitan())

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


class TestExternal(unittest.TestCase):  # pragma: no cover

    def testFromChordify(self):
        from music21 import corpus
        b = corpus.parse('bwv103.6')
        c = b.chordify()
        cKey = b.analyze('key')
        figuresCache = {}
        for x in c.recurse():
            if 'Chord' in x.classes:
                rnc = romanNumeralFromChord(x, cKey)
                figure = rnc.figure
                if figure not in figuresCache:
                    figuresCache[figure] = 1
                else:
                    figuresCache[figure] += 1
                x.lyric = figure

        sortedList = sorted(figuresCache, key=figuresCache.get, reverse=True)
        for thisFigure in sortedList:
            print(thisFigure, figuresCache[thisFigure])

        b.insert(0, c)
        b.show()


# -----------------------------------------------------------------------------
_DOC_ORDER = [
    RomanNumeral,
]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testV7b5')
