# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         roman.py
# Purpose:      music21 classes for doing Roman Numeral / Tonal analysis
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Music21 class for dealing with Roman Numeral analysis
'''
from __future__ import division, print_function

import unittest
import copy
import re

from collections import namedtuple

FigureTuple = namedtuple('FigureTuple', 'aboveBass alter prefix')
ChordFigureTuple = namedtuple('ChordFigureTuple', 'aboveBass alter prefix pitch')

from music21 import chord
from music21 import common
from music21 import exceptions21
from music21 import harmony
from music21 import interval
from music21 import key
from music21 import pitch
from music21 import scale

from music21.ext import six
from music21.figuredBass import notation as fbNotation

from music21 import environment
_MOD = 'roman.py'
environLocal = environment.Environment(_MOD)

# TODO: setting inversion should change the figure

#------------------------------------------------------------------------------


SHORTHAND_RE = re.compile(r'#*-*b*o*[1-9xyz]')
ENDWITHFLAT_RE = re.compile(r'[b\-]$')

# cache all Key/Scale objects created or passed in; re-use
# permits using internally scored pitch segments
_scaleCache = {}
_keyCache = {}

def _getKeyFromCache(keyStr):
    '''
    get a key from the cache if it is there; otherwise
    create a new key and put it in the cache and return it.

    :param keyStr: str
    :rtype: key.Key
    '''
    if keyStr in _keyCache:
        keyObj = _keyCache[keyStr]
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
    #'6b5bb3': 'o65',
    'b7b5b3': '/o7',
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
    '#viio': 39,
    'iio': 37,  # common in Minor
    'iio42': 36,
    'bII6': 35,  # Neapolitan
    'iio43': 32,
    'iio65': 31,
    '#vio': 28,
    '#vio6': 28,
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


#------------------------------------------------------------------------------


def expandShortHand(shorthand):
    '''
    Expands shorthand notation into a list with all figures expanded:

    >>> roman.expandShortHand("64")
    ['6', '4']

    >>> roman.expandShortHand("973")
    ['9', '7', '3']

    >>> roman.expandShortHand("11b3")
    ['11', 'b3']

    >>> roman.expandShortHand("b13#9-6")
    ['b13', '#9', '-6']

    >>> roman.expandShortHand("-")
    ['5', '-3']


    Slashes don't matter

    >>> roman.expandShortHand("6/4")
    ['6', '4']

    Note that this is not where abbreviations get expanded

    >>> roman.expandShortHand("7") # not 7, 5, 3
    ['7']

    >>> roman.expandShortHand("4/3") # not 6, 4, 3
    ['4', '3']

    Note that this is ['6'] not ['6', '3']:

    >>> roman.expandShortHand("6")
    ['6']


    Returns a list of expanded abbreviations.
    '''
    shorthand = shorthand.replace('/', '') # this line actually seems unnecessary...
    if ENDWITHFLAT_RE.match(shorthand):
        shorthand += "3"
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

    if inversionString and (inversionString.startswith('o') or inversionString.startswith('/o')):
        if qualityName == 'o':  # don't call viio7, viioo7.
            qualityName = ''

    seventhType = chordObj.semitonesFromChordStep(7)
    if seventhType and fifthType == 6: # there is a seventh and this is a diminished 5
        if seventhType == 10 and qualityName == 'o':
            qualityName = '/o'
        elif seventhType != 9:
            pass # do something for odd odd chords...
    #print (inversionString, fifthName)
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
    #seventh = chordObj.seventh
    for ft in sorted(chordFigureTuples,
                               key=lambda tup: (-1 * tup.aboveBass, tup.alter, tup.pitch.ps)):
        # (diatonicIntervalNum, alter, alterStr, pitchObj) = figureTuple
        prefix = ft.prefix
        
        if ft.aboveBass != 1 and ft.pitch is third:
            if chordObj.isMajorTriad() or chordObj.isMinorTriad():
                prefix = ''  # alterStr[1:]
            elif chordObj.isMinorTriad() and ft.alter > 0:
                prefix = ''  # alterStr[1:]
        elif (ft.aboveBass != 1
              and ft.pitch is fifth
              and chordObj.isDiminishedTriad()
                  or chordObj.isAugmentedTriad()
                  or chordObj.isMajorTriad()
                  or chordObj.isMinorTriad()):
            prefix = ''  # alterStr[1:]

        if ft.aboveBass == 1:
            if ft.alter != bassFigureAlter and prefix != '':
                # mark altered octaves as 8 not 1
                figureString = prefix + "8"
                if figureString not in allFigureStringList:
                    # filter duplicates and put at beginning
                    allFigureStringList.insert(0, figureString)
        else:
            figureString = prefix + str(ft.aboveBass)
            # filter out duplicates...
            if figureString not in allFigureStringList:
                allFigureStringList.append(figureString)

    allFigureString = ''.join(allFigureStringList)
    if allFigureString in figureShorthands:
        allFigureString = figureShorthands[allFigureString]

    # simplify common omissions from 7th chords
    if allFigureString in ['75', '73']:
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
            rootAlterationString = "b" * (-1 * alter)
        elif alter > 0:
            rootAlterationString = "#" * alter
        else:
            rootAlterationString = ''

    appendTuple = FigureTuple(aboveBass, alterDiff, rootAlterationString)
    return appendTuple


def identifyAsTonicOrDominant(inChord, inKey):
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
    if isinstance(inChord, list):
        inChord = chord.Chord(inChord)
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

    >>> ft5 = roman.FigureTuple(aboveBass=6, alter=-1, prefix='')
    >>> roman.correctRNAlterationForMinor(ft5, key.Key('c'))
    FigureTuple(aboveBass=6, alter=-1, prefix='b')

    >>> ft6 = roman.FigureTuple(aboveBass=6, alter=0, prefix='')
    >>> roman.correctRNAlterationForMinor(ft6, key.Key('c'))
    FigureTuple(aboveBass=6, alter=0, prefix='b')

    >>> ft7 = roman.FigureTuple(aboveBass=7, alter=1, prefix='#')
    >>> roman.correctRNAlterationForMinor(ft7, key.Key('c'))
    FigureTuple(aboveBass=7, alter=0, prefix='')

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
    ## more exotic:
    elif alter > 1.0:
        alter = alter - 1
        rootAlterationString = rootAlterationString[1:]
    elif alter < 0.0:
        rootAlterationString = 'b' + rootAlterationString

    return FigureTuple(figureTuple.aboveBass, alter, rootAlterationString)


def romanNumeralFromChord(chordObj,
                          keyObj=None,
                          preferSecondaryDominants=False):
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

    >>> for pitch in rn.pitches:
    ...     pitch
    ...
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
    ...     chord.Chord("A3 E-4 G-4"),
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
    <music21.roman.RomanNumeral #iii/o7 in d minor>


    Former bugs:

    Should be iii7

    >>> romanNumeral11 = roman.romanNumeralFromChord(
    ...     chord.Chord(['E4', 'G4', 'B4', 'D5']),
    ...     key.Key('C'),
    ...     )
    >>> romanNumeral11
    <music21.roman.RomanNumeral iii7 in C major>

    Should be vi/o7 # gave vio7

    >>> roman.romanNumeralFromChord(chord.Chord("A3 C4 E-4 G4"), key.Key('c'))
    <music21.roman.RomanNumeral vi/o7 in c minor>

    Should be vii/o7 # gave viio7

    >>> roman.romanNumeralFromChord(chord.Chord("A3 C4 E-4 G4"), key.Key('B-'))
    <music21.roman.RomanNumeral vii/o7 in B- major>


    Should be I#853

    >>> romanNumeral9 = roman.romanNumeralFromChord(
    ...     chord.Chord(['C4', 'E5', 'G5', 'C#6']),
    ...     key.Key('C'),
    ...     )
    >>> romanNumeral9
    <music21.roman.RomanNumeral I#853 in C major>


    Note that this should be III+642 gives III+#642 (# before 6 is unnecessary)

    # >>> roman.romanNumeralFromChord(chord.Chord("B3 D3 E-3 G3"), key.Key('c'))
    # <music21.roman.RomanNumeral III+642 in c minor>


    These two are debatable -- is the harmonic minor or the natural minor used as the basis?

    # >>> roman.romanNumeralFromChord(chord.Chord("F4 A4 C5 E-5"), key.Key('c'))
    # <music21.roman.RomanNumeral IVb753 in c minor>
    # <music21.roman.RomanNumeral IV75#3 in c minor>

    # >>> roman.romanNumeralFromChord(chord.Chord("F4 A4 C5 E5"), key.Key('c'))
    # <music21.roman.RomanNumeral IV7 in c minor>
    # <music21.roman.RomanNumeral IV#75#3 in c minor>
    '''
    #TODO: Make sure 9 works
    #stepAdjustments = {'minor' : {3: -1, 6: -1, 7: -1},
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
        rootkeyObj = _getKeyFromCache(root.name.upper())
    else:
        rootkeyObj = _getKeyFromCache(root.name.lower())

    if keyObj is None:
        keyObj = rootkeyObj

    ft = figureTupleSolo(root, keyObj, keyObj.tonic) # a FigureTuple
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
    
    try:
        rn = RomanNumeral(rnString, keyObj, updatePitches=False)
    except fbNotation.ModifierException as strerror:
        raise RomanNumeralException(
            'Could not parse {0} from chord {1} as an RN '
            'in key {2}: {3}'.format(rnString, chordObj, keyObj, strerror))

    # Is this linking them in an unsafe way?
    rn.pitches = chordObj.pitches
    return rn


#------------------------------------------------------------------------------


class RomanException(exceptions21.Music21Exception):
    pass


class RomanNumeralException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------


class RomanNumeral(harmony.Harmony):
    '''
    A RomanNumeral object is a specialized type of
    :class:`~music21.harmony.Harmony` object that stores the function and scale
    degree of a chord within a :class:`~music21.key.Key`.

    If no Key is given then it exists as a theoretical, keyless RomanNumeral;
    e.g., V in any key. but when realized, keyless RomanNumerals are
    treated as if they are in C major).

    >>> from music21 import roman
    >>> V = roman.RomanNumeral('V') # could also use 5
    >>> V.quality
    'major'

    >>> V.inversion()
    0

    >>> V.forteClass
    '3-11B'

    >>> V.scaleDegree
    5

    >>> for pitch in V.pitches:  # default key-- C Major
    ...     pitch
    ...
    <music21.pitch.Pitch G4>
    <music21.pitch.Pitch B4>
    <music21.pitch.Pitch D5>

    >>> neapolitan = roman.RomanNumeral('N6', 'c#') # could also use "bII6"
    >>> neapolitan.key
    <music21.key.Key of c# minor>

    >>> neapolitan.isMajorTriad()
    True

    >>> neapolitan.scaleDegreeWithAlteration
    (2, <accidental flat>)

    >>> for pitch in neapolitan.pitches:  # default octaves
    ...     pitch
    ...
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
    vii, viio, viio7, vii/o7 and vi, vio, vio7, vi/o7 refer to the sharpened scale
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

    Either of these is the same way of getting a minor iii in a minor key:

    >>> minoriii = roman.RomanNumeral('iii', em, caseMatters=True)
    >>> [str(p) for p in minoriii.pitches]
    ['G4', 'B-4', 'D5']

    >>> minoriiiB = roman.RomanNumeral('IIIb', em, caseMatters=False)
    >>> [str(p) for p in minoriiiB.pitches]
    ['G4', 'B-4', 'D5']

    Can also take a scale object, here we build a first-inversion chord
    on the raised-three degree of D-flat major, that is, F#-major (late
    Schubert would be proud...)

    >>> sharp3 = roman.RomanNumeral('#III6', scale.MajorScale('D-'))
    >>> sharp3.scaleDegreeWithAlteration
    (3, <accidental sharp>)

    >>> [str(p) for p in sharp3.pitches]
    ['A#4', 'C#5', 'F#5']

    >>> sharp3.figure
    '#III6'

    Figures can be changed and pitches will change.

    >>> sharp3.figure = "V"
    >>> [str(p) for p in sharp3.pitches]
    ['A-4', 'C5', 'E-5']

    >>> leadingToneSeventh = roman.RomanNumeral(
    ...     'viio', scale.MajorScale('F'))
    >>> [str(p) for p in leadingToneSeventh.pitches]
    ['E5', 'G5', 'B-5']

    A little modal mixture:

    >>> lessObviousDiminished = roman.RomanNumeral(
    ...     'vio', scale.MajorScale('c'))
    >>> for pitch in lessObviousDiminished.pitches:
    ...     pitch
    ...
    <music21.pitch.Pitch A4>
    <music21.pitch.Pitch C5>
    <music21.pitch.Pitch E-5>

    >>> diminished7th = roman.RomanNumeral(
    ...     'vio7', scale.MajorScale('c'))
    >>> for pitch in diminished7th.pitches:
    ...     pitch
    ...
    <music21.pitch.Pitch A4>
    <music21.pitch.Pitch C5>
    <music21.pitch.Pitch E-5>
    <music21.pitch.Pitch G-5>

    >>> diminished7th1stInv = roman.RomanNumeral(
    ...     'vio65', scale.MajorScale('c'))
    >>> for pitch in diminished7th1stInv.pitches:
    ...     pitch
    ...
    <music21.pitch.Pitch C4>
    <music21.pitch.Pitch E-4>
    <music21.pitch.Pitch G-4>
    <music21.pitch.Pitch A4>

    >>> halfDim7th2ndInv = roman.RomanNumeral(
    ...     'iv/o43', scale.MajorScale('F'))
    >>> for pitch in halfDim7th2ndInv.pitches:
    ...     pitch
    ...
    <music21.pitch.Pitch F-4>
    <music21.pitch.Pitch A-4>
    <music21.pitch.Pitch B-4>
    <music21.pitch.Pitch D-5>

    >>> alteredChordHalfDim3rdInv = roman.RomanNumeral(
    ...     'bii/o42', scale.MajorScale('F'))
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

    >>> openFifth = roman.RomanNumeral('V[no3]', key.Key('F'))
    >>> openFifth.pitches
    (<music21.pitch.Pitch C5>, <music21.pitch.Pitch G5>)

    Some theoretical traditions express a viio7 as a V9 chord with omitted
    root. Music21 allows that:

    >>> fiveOhNine = roman.RomanNumeral('V9[no1]', key.Key('g'))
    >>> [str(p) for p in fiveOhNine.pitches]
    ['F#5', 'A5', 'C6', 'E-6']

    Just for kicks (no worries if this is goobley-gook):

    >>> ots = scale.OctatonicScale("C2")
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



    OMIT_FROM_DOCS

    Things that were giving us trouble:

    >>> dminor = key.Key('d')
    >>> rn = roman.RomanNumeral('ii/o65', dminor)
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
    >>> [str(pitch) for pitch in r.pitches]
    ['G4']


    Accepts a keyword 'updatePitches' which is passed to harmony.Harmony. By default it
    is True, but can be set to False to initialize faster if pitches are not needed.

    >>> r = roman.RomanNumeral('vio', em, updatePitches=False)
    >>> r.pitches
    ()
    '''
    # TODO: document better! what is inherited and what is new?

    _alterationRegex = re.compile(r'^(b+|\-+|\#+)')
    _omittedStepsRegex = re.compile(r'(\[(no[1-9]+)+\]\s*)+')
    _bracketedAlterationRegex =  re.compile(r'\[(b+|\-+|\#+)(\d+)\]')
    _augmentedSixthRegex = re.compile(r'(It|Ger|Fr|Sw)')
    _romanNumeralAloneRegex = re.compile(r'(IV|I{1,3}|VI{0,2}|iv|i{1,3}|vi{0,2}|N)')
    _secondarySlashRegex = re.compile(r'(.*?)\/([\#a-np-zA-NP-Z].*)')

    _DOC_ATTR = {
        'scaleCardinality': '''
            Probably you should not need to change this, but stores how many
            notes are in the scale; defaults to 7 for diatonic, obviously.
            ''',
        'caseMatters': '''
            Boolean to determine whether the case (upper or lowercase) of the
            figure determines whether it is major or minor.  Defaults to True;
            not everything has been tested with False yet.
            ''',
        'pivotChord': '''
            Defaults to None; if not None, stores another interpretation of the
            same RN in a different key; stores a RomanNumeral object.
            ''',
        }

    ### INITIALIZER ###

    def __init__(self, figure=None, keyOrScale=None, caseMatters=True, **keywords):
        self.primaryFigure = None
        self.secondaryRomanNumeral = None
        self.secondaryRomanNumeralKey = None

        self.pivotChord = None
        self.caseMatters = caseMatters
        self.scaleCardinality = 7

        if isinstance(figure, int):
            self.caseMatters = False
            figure = common.toRoman(figure)

        # Store raw figure before calling setKeyOrScale:
        self._figure = figure
        # This is set when _setKeyOrScale() is called:
        self._scale = None
        self.scaleDegree = None
        self.frontAlterationString = None
        self.frontAlterationTransposeInterval = None
        self.frontAlterationAccidental = None
        self.romanNumeralAlone = None
        
        self.impliedQuality = None
        self.impliedScale = None
        self.useImpliedScale = False
        self.bracketedAlterations = None
        self.omittedSteps = []
        # do not update pitches...
        self._parsingComplete = False
        self.key = keyOrScale

        updatePitches = keywords.get('updatePitches', True)
        super(RomanNumeral, self).__init__(figure, updatePitches=updatePitches)

        self._correctBracketedPitches()
        self._parsingComplete = True
        self._functionalityScore = None
        # It is sometimes helpful to know if this is the first chord after a
        # key change.
        self.followsKeyChange = False

    ### SPECIAL METHODS ###

    def __repr__(self):
        if hasattr(self.key, 'tonic'):
            return '<music21.roman.RomanNumeral %s>' % (self.figureAndKey)
        else:
            return '<music21.roman.RomanNumeral %s>' % (self.figure)

    ### PRIVATE METHODS ###    
    def _parseFigure(self):
        '''
        Parse the .figure object into its component parts.

        Called from the superclass, Harmony.__init__()
        '''
        if not isinstance(self._figure, six.string_types):
            raise RomanException('got a non-string figure: {!r}'.format(self._figure))

        if not self.useImpliedScale:
            useScale = self._scale
        else:
            useScale = self.impliedScale

        (workingFigure, useScale) = self._correctForSecondaryRomanNumeral(useScale)
        self.primaryFigure = workingFigure
        
        workingFigure = self._parseOmittedSteps(workingFigure)
        workingFigure = self._parseBracketedAlterations(workingFigure)

        # Replace Neapolitan indication.
        workingFigure = re.sub('^N', 'bII', workingFigure)

        workingFigure = self._parseFrontAlterations(workingFigure)
        workingFigure, useScale = self._parseRNAloneAmidstAug6(workingFigure, useScale)
        workingFigure = self._setImpliedQualityFromString(workingFigure)

        self._fixMinorVIandVII(useScale)

        self.figuresWritten = workingFigure
        shfig = ','.join(expandShortHand(workingFigure))
        self.figuresNotationObj = fbNotation.Notation(shfig)

    def _setImpliedQualityFromString(self, workingFigure):
        # major, minor, augmented, or diminished (and half-diminished for 7ths)
        impliedQuality = ''
        #impliedQualitySymbol = ''
        if workingFigure.startswith('o'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'diminished'
            #impliedQualitySymbol = 'o'
        elif workingFigure.startswith('/o'):
            workingFigure = workingFigure[2:]
            impliedQuality = 'half-diminished'
            #impliedQualitySymbol = '/o'
        elif workingFigure.startswith('+'):
            workingFigure = workingFigure[1:]
            impliedQuality = 'augmented'
            #impliedQualitySymbol = '+'
        elif workingFigure.endswith('d7'):
            # this one is different
            workingFigure = workingFigure[:-2] + '7'
            impliedQuality = 'dominant-seventh'
            #impliedQualitySymbol = '(dom7)'
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
        if self.bracketedAlterations is None:
            return
        for (alterNotation, chordStep) in self.bracketedAlterations:
            alterNotation = re.sub('b', '-', alterNotation)
            alterPitch = self.getChordStep(chordStep)
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
        >>> " ".join([p.name for p in r.pitches])
        'C E- G'
        >>> r._matchAccidentalsToQuality('augmented')
        >>> " ".join([p.name for p in r.pitches])
        'C E G#'
        >>> r._matchAccidentalsToQuality('diminished')
        >>> " ".join([p.name for p in r.pitches])
        'C E- G-'
        >>> r.pitches = ['C4', 'E4', 'G4', 'B4']
        >>> r._matchAccidentalsToQuality('diminished')
        >>> " ".join([p.name for p in r.pitches])
        'C E- G- B--'

        This was a problem before...

        >>> r.pitches = ['C4', 'E4', 'G4', 'B#4']
        >>> r._matchAccidentalsToQuality('diminished')
        >>> " ".join([p.name for p in r.pitches])
        'C E- G- B--'
        '''
        correctSemitones = self._findSemitoneSizeForQuality(impliedQuality)
        chordStepsToExamine = (3, 5, 7)
        #newPitches = []
        for i in range(len(correctSemitones)):  # 3,5,7
            thisChordStep = chordStepsToExamine[i]
            thisCorrect = correctSemitones[i]
            thisSemis = self.semitonesFromChordStep(thisChordStep)
            if thisSemis is None:
                continue
            if thisSemis != thisCorrect:
                correctedSemis = thisCorrect - thisSemis
                if correctedSemis >= 6:
                    correctedSemis = -1* (12 - correctedSemis)
                elif correctedSemis <= -6:
                    correctedSemis += 12

                faultyPitch = self.getChordStep(thisChordStep)
                if faultyPitch is None:
                    raise RomanException(
                        "this is very odd... should have been caught in semitonesFromChordStep")
                if faultyPitch.accidental is None:
                    faultyPitch.accidental = pitch.Accidental(correctedSemis)
                else:
                    acc = faultyPitch.accidental
                    correctedSemis += acc.alter
                    if correctedSemis >= 6:
                        correctedSemis = -1* (12 - correctedSemis)
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
        >>> r = roman.RomanNumeral('I', k) # will not be used below...
        >>> r._correctForSecondaryRomanNumeral(k) # uses "I". nothing should change...
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
                self.caseMatters,
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

            ### TODO: this should use a KeyCache...
            ###   but lower priority since secondaries are relatively rare
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
        Remove omitted steps from a working figure and return the omitted parts,
        setting self.omittedSteps
        
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
            if self.bracketedAlterations is None:
                self.bracketedAlterations = []
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
        frontAlterationString = ''  # the b in bVI, or the # in #vii
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
        return workingFigure
    
    def _parseRNAloneAmidstAug6(self, workingFigure, useScale):
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
        '''
        romanNumeralAlone = ''
        if (not self._romanNumeralAloneRegex.match(workingFigure)
                and not self._augmentedSixthRegex.match(workingFigure)):
            raise RomanException('No roman numeral found in {!r}'.format(
                workingFigure))
        elif self._augmentedSixthRegex.match(workingFigure):
            if useScale.mode == 'major':
                useScale = key.Key(useScale.tonic, 'minor')
                self.impliedScale = useScale
                self.useImpliedScale = True
            rm = self._augmentedSixthRegex.match(workingFigure)
            romanNumeralAlone = rm.group(1)
            if (romanNumeralAlone in ('It', 'Ger')):
                self.scaleDegree = 4
            else:
                self.scaleDegree = 2
            workingFigure = self._augmentedSixthRegex.sub('', workingFigure)
            self.romanNumeralAlone = romanNumeralAlone
            if self.bracketedAlterations is None:
                self.bracketedAlterations = []

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
    
    def _fixMinorVIandVII(self, useScale):
        '''
        fix minor vi and vii to always be #vi and #vii if `.caseMatters`.
        
        >>> rn = roman.RomanNumeral()
        >>> rn.scaleDegree = 6
        >>> rn.impliedQuality = 'minor'
        >>> rn._fixMinorVIandVII(key.Key('c'))
        
        >>> rn.frontAlterationTransposeInterval
        <music21.interval.Interval A1>
        
        >>> rn.frontAlterationAccidental
        <accidental sharp>
        '''
        # Make vii always #vii and vi always #vi.
        if getattr(useScale, 'mode', None) != 'minor':
            return
        if not self.caseMatters:
            return
        if self.scaleDegree not in (6, 7):
            return
        if self.impliedQuality not in ('minor', 'diminished', 'half-diminished'):
            return
        
        fati = self.frontAlterationTransposeInterval
        if fati:        
            newFati = interval.add([fati, interval.Interval('A1')])
            self.frontAlterationTransposeInterval = newFati
            self.frontAlterationAccidental.alter = self.frontAlterationAccidental.alter + 1
        else:
            self.frontAlterationTransposeInterval = interval.Interval('A1')
            self.frontAlterationAccidental = pitch.Accidental(1)

    def _updatePitches(self):
        '''
        Utility function to update the pitches to the new figure etc.
        '''
        if self.secondaryRomanNumeralKey is not None:
            useScale = self.secondaryRomanNumeralKey
        elif not self.useImpliedScale:
            useScale = self._scale
        else:
            useScale = self.impliedScale

        # should be 7 but hey, octatonic scales, etc.
        #self.scaleCardinality = len(useScale.pitches) - 1
        if 'DiatonicScale' in useScale.classes:  # speed up simple case
            self.scaleCardinality = 7
        else:
            self.scaleCardinality = useScale.getDegreeMaxUnique()

        bassScaleDegree = self.bassScaleDegreeFromNotation(
            self.figuresNotationObj)
        bassPitch = useScale.pitchFromDegree(bassScaleDegree,
            direction=scale.DIRECTION_ASCENDING)
        pitches = [bassPitch]
        lastPitch = bassPitch
        numberNotes = len(self.figuresNotationObj.numbers)

        for j in range(numberNotes):
            i = numberNotes - j - 1
            thisscaleDegree = (bassScaleDegree
                                + self.figuresNotationObj.numbers[i]
                                - 1)
            newPitch = useScale.pitchFromDegree(thisscaleDegree,
                                                direction=scale.DIRECTION_ASCENDING)
            pitchName = self.figuresNotationObj.modifiers[i].modifyPitchName(newPitch.name)
            newnewPitch = pitch.Pitch(pitchName)
            newnewPitch.octave = newPitch.octave
            #if newnewPitch.midi < lastPitch.midi:
            # better to compare pitch space, as midi has limits and rounding
            if newnewPitch.ps < lastPitch.ps:
                newnewPitch.octave += 1
            pitches.append(newnewPitch)
            lastPitch = newnewPitch

        if self.frontAlterationTransposeInterval:
            newPitches = []
            for thisPitch in pitches:
                newPitch = thisPitch.transpose(self.frontAlterationTransposeInterval)
                newPitches.append(newPitch)
            self.pitches = newPitches
        else:
            self.pitches = pitches

        self._matchAccidentalsToQuality(self.impliedQuality)

        self.scaleOffset = self.frontAlterationTransposeInterval

        if self.omittedSteps:
            omittedPitches = []
            for thisCS in self.omittedSteps:
                # getChordStep may return False
                p = self.getChordStep(thisCS)
                if p not in [False, None]:
                    omittedPitches.append(p.name)

            newPitches = []
            for thisPitch in pitches:
                if thisPitch.name not in omittedPitches:
                    newPitches.append(thisPitch)
            self.pitches = newPitches

        if not self.pitches:
            raise RomanNumeralException(
                '_updatePitches() was unable to derive pitches from the '
                'figure: {0!r}'.format(self.figure))

    ### PUBLIC PROPERTIES ###

    @property
    def romanNumeral(self):
        '''
        Read-only property that returns either the romanNumeralAlone (e.g. just
        II) or the frontAlterationAccidental.modifier + romanNumeralAlone (e.g.
        #II)

        >>> from music21 import roman
        >>> rn = roman.RomanNumeral("#II7")
        >>> rn.romanNumeral
        '#II'

        '''
        if self.frontAlterationAccidental is None:
            return self.romanNumeralAlone
        else:
            return (self.frontAlterationAccidental.modifier +
                self.romanNumeralAlone)

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

        '''
        tonic = self.key.tonic
        if hasattr(tonic, 'name'):
            tonic = tonic.name
        mode = ''
        if hasattr(self.key, 'mode'):
            mode = " " + self.key.mode
        elif self.key.__class__.__name__ == 'MajorScale':
            mode = ' major'
        elif self.key.__class__.__name__ == 'MinorScale':
            mode = ' minor'
        else:
            pass
        if mode == ' minor':
            tonic = tonic.lower()
        elif mode == ' major':
            tonic = tonic.upper()
        return '%s in %s%s' % (self.figure, tonic, mode)

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
            return # skip...

        # try to get Scale or Key object from cache: this will offer
        # performance boost as Scale stores cached pitch segments
        if isinstance(keyOrScale, six.string_types):
            keyOrScale = _getKeyFromCache(keyOrScale)
        elif keyOrScale is not None:
            #environLocal.printDebug(['got keyOrScale', keyOrScale])
            try:
                keyClasses = keyOrScale.classes
            except:
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
                    'Cannot get a key from this object {0!r}, send only '
                    'Key or Scale objects'.format(keyOrScale))
        else:
            pass # None
            # cache object if passed directly
        self._scale = keyOrScale
        if (keyOrScale is None
                or (hasattr(keyOrScale, "isConcrete")
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
#            environLocal.printDebug([
#                'Roman.setKeyOrScale:',
#                'called w/ scale', self.key,
#                'figure', self.figure,
#                'pitches', self.pitches,
#                ])


#    def nextInversion(self):
#        '''
#        Invert the harmony one position, or place the next member after the
#        current bass as the bass:
#
#
#
#        >>> sc1 = scale.MajorScale('g4')
#        >>> h1 = scale.RomanNumeral(sc1, 5)
#        >>> h1.getPitches()
#        [D5, F#5, A5]
#
#        >>> h1.nextInversion()
#        >>> h1._bassMemberIndex
#        1
#
#        >>> h1.getPitches()
#        [F#5, A5, D6]
#
#        '''
#        self._bassMemberIndex = ((self._bassMemberIndex + 1) %
#            len(self._members))

    @property
    def scaleDegreeWithAlteration(self):
        '''
        Returns or sets a two element tuple of the scale degree and the
        accidental that alters the scale degree for things such as #ii or
        bV.

        Note that vi and vii in minor have a frontAlterationAccidental of
        <sharp> even if it is not preceded by a # sign.

        Has the same effect as setting .scaleDegree and
        .frontAlterationAccidental separately
        '''
        return (self.scaleDegree, self.frontAlterationAccidental)

    @scaleDegreeWithAlteration.setter
    def scaleDegreeWithAlteration(self, scaleDegree, alteration):
        self.scaleDegree = scaleDegree
        self.frontAlterationAccidental = alteration
        if self._parsingComplete:
            self._updatePitches()


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
        c = pitch.Pitch("C3")
        cDNN = c.diatonicNoteNum # always 22
        pitches = [c]
        for i in notationObject.numbers:
            distanceToMove = i - 1
            newDiatonicNumber = (cDNN + distanceToMove)

            newStep, newOctave = interval.convertDiatonicNumberToStep(
                newDiatonicNumber)
            newPitch = pitch.Pitch("C3")
            newPitch.step = newStep
            newPitch.octave = newOctave
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
            figures = self.figure.split('/') # error for half-diminished in secondary...
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


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

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
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                i = copy.copy(obj)
                j = copy.deepcopy(obj)
                self.assertTrue(i is not None)
                self.assertTrue(j is not None)

    def testFBN(self):
        fbn = fbNotation.Notation('6,3')
        V = RomanNumeral('V')
        sdb = V.bassScaleDegreeFromNotation(fbn)
        self.assertEqual(sdb, 7)

    def testFigure(self):
        r1 = RomanNumeral('V')
        self.assertEqual(r1.scaleOffset, None)
        self.assertEqual(r1.pitches, chord.Chord(["G4", "B4", "D5"]).pitches)
        r1 = RomanNumeral('bbVI6')
        self.assertEqual(r1.figuresWritten, "6")
        self.assertEqual(r1.scaleOffset.chromatic.semitones, -2)
        self.assertEqual(r1.scaleOffset.diatonic.directedNiceName,
            "Descending Doubly-Diminished Unison")
        cM = scale.MajorScale('C')
        r2 = RomanNumeral('ii', cM)
        self.assertTrue(r2 is not None)
        dminor = key.Key('d')
        rn = RomanNumeral('ii/o65', dminor)
        self.assertEqual(
            rn.pitches,
            chord.Chord(['G4', 'B-4', 'D5', 'E5']).pitches,
            )
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
            '(<music21.pitch.Pitch G4>, <music21.pitch.Pitch B4>, <music21.pitch.Pitch D-5>, ' +
            '<music21.pitch.Pitch F-5>, <music21.pitch.Pitch A5>)')

#    def xtestFirst(self):
#         # associating a harmony with a scale
#        sc1 = MajorScale('g4')
#        # define undefined
#        #rn3 = sc1.romanNumeral(3, figure="7")
#        h1 = RomanNumeral(sc1, 1)
#        h2 = RomanNumeral(sc1, 2)
#        h3 = RomanNumeral(sc1, 3)
#        h4 = RomanNumeral(sc1, 4)
#        h5 = RomanNumeral(sc1, 5)
#        # can get pitches or roman numerals
#        self.assertEqual(str(h1.pitches), '[G4, B4, D5]')
#        self.assertEqual(str(h2.pitches), '[A4, C5, E5]')
#        self.assertEqual(h2.romanNumeral, 'ii')
#        self.assertEqual(h5.romanNumeral, 'V')
#        # can get pitches from various ranges, invert, and get bass
#        h5.nextInversion()
#        self.assertEqual(str(h5.bass), 'F#5')
#        self.assertEqual(
#            str(h5.getPitches('c2', 'c6')),
#            '[F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]',
#            )
#        h5.nextInversion()
#        self.assertEqual(
#            str(h5.getPitches('c2', 'c6')),
#            '[A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]',
#            )
#        h5.nextInversion()
#        self.assertEqual(str(h5.bass), 'D5')
#        self.assertEqual(
#            str(h5.getPitches('c2', 'c6')),
#            '[D2, F#2, A2, D3, F#3, A3, D4, F#4, A4, D5, F#5, A5]',
#            )
#        sc1 = MajorScale('g4')
#        h2 = RomanNumeral(sc1, 2)
#        h2.makeSeventhChord()
#        self.assertEqual(
#            str(h2.getPitches('c4', 'c6')),
#            '[A4, C5, E5, G5, A5, C6]',
#            )
#        h2.makeNinthChord()
#        self.assertEqual(
#            str(h2.getPitches('c4', 'c6')),
#            '[A4, B4, C5, E5, G5, A5, B5, C6]',
#            )
#        h2.chord.show()

    def testYieldRemoveA(self):
        from music21 import stream, note
        #s = corpus.parse('madrigal.3.1.rntxt')
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
        #s2.show()
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
        #s3.show()
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
        c = chord.Chord("A3 E-4 G-4")
        k = key.Key('b-')
        rnDim7 = roman.romanNumeralFromChord(c, k)
        self.assertEqual(rnDim7.figure, 'viio7')

    def testAllFormsOfVII(self):
        from music21 import roman
        def p(c):
            return " ".join([x.nameWithOctave for x in c.pitches])

        k = key.Key('c')
        rn = roman.RomanNumeral("viio", k)
        self.assertEqual(p(rn), 'B4 D5 F5')
        rn = roman.RomanNumeral("viio6", k)
        self.assertEqual(p(rn), 'D4 F4 B4')
        rn = roman.RomanNumeral("viio64", k)
        self.assertEqual(p(rn), 'F4 B4 D5')

        rn = roman.RomanNumeral("vii", k)
        self.assertEqual(p(rn), 'B4 D5 F#5')
        rn = roman.RomanNumeral("vii6", k)
        self.assertEqual(p(rn), 'D4 F#4 B4')
        rn = roman.RomanNumeral("vii64", k)
        self.assertEqual(p(rn), 'F#4 B4 D5')

        rn = roman.RomanNumeral("viio7", k)
        self.assertEqual(p(rn), 'B4 D5 F5 A-5')
        rn = roman.RomanNumeral("viio65", k)
        self.assertEqual(p(rn), 'D4 F4 A-4 B4')
        rn = roman.RomanNumeral("viio43", k)
        self.assertEqual(p(rn), 'F4 A-4 B4 D5')
        rn = roman.RomanNumeral("viio42", k)
        self.assertEqual(p(rn), 'A-4 B4 D5 F5')

        rn = roman.RomanNumeral("vii/o7", k)
        self.assertEqual(p(rn), 'B4 D5 F5 A5')
        rn = roman.RomanNumeral("vii/o65", k)
        self.assertEqual(p(rn), 'D4 F4 A4 B4')
        rn = roman.RomanNumeral("vii/o43", k)
        self.assertEqual(p(rn), 'F4 A4 B4 D5')
        rn = roman.RomanNumeral("vii/o42", k)
        self.assertEqual(p(rn), 'A4 B4 D5 F5')

        rn = roman.RomanNumeral("VII", k)
        self.assertEqual(p(rn), 'B-4 D5 F5')
        rn = roman.RomanNumeral("VII6", k)
        self.assertEqual(p(rn), 'D4 F4 B-4')
        rn = roman.RomanNumeral("VII64", k)
        self.assertEqual(p(rn), 'F4 B-4 D5')

        rn = roman.RomanNumeral("bVII", k)
        self.assertEqual(p(rn), 'B--4 D-5 F-5')
        rn = roman.RomanNumeral("bVII6", k)
        self.assertEqual(p(rn), 'D-4 F-4 B--4')
        rn = roman.RomanNumeral("bVII64", k)
        self.assertEqual(p(rn), 'F-4 B--4 D-5')

        rn = roman.RomanNumeral("bvii", k)
        self.assertEqual(p(rn), 'B-4 D-5 F5')
        rn = roman.RomanNumeral("bvii6", k)
        self.assertEqual(p(rn), 'D-4 F4 B-4')
        rn = roman.RomanNumeral("bvii64", k)
        self.assertEqual(p(rn), 'F4 B-4 D-5')

        rn = roman.RomanNumeral("bviio", k)
        self.assertEqual(p(rn), 'B-4 D-5 F-5')
        rn = roman.RomanNumeral("bviio6", k)
        self.assertEqual(p(rn), 'D-4 F-4 B-4')
        rn = roman.RomanNumeral("bviio64", k)
        self.assertEqual(p(rn), 'F-4 B-4 D-5')

        rn = roman.RomanNumeral("#VII", k)
        self.assertEqual(p(rn), 'B4 D#5 F#5')
        rn = roman.RomanNumeral("#vii", k)
        self.assertEqual(p(rn), 'B#4 D#5 F##5')

        rn = roman.RomanNumeral("VII+", k)
        self.assertEqual(p(rn), 'B-4 D5 F#5')


    def testAllFormsOfVI(self):
        from music21 import roman
        def p(c):
            return " ".join([x.nameWithOctave for x in c.pitches])

        k = key.Key('c')
        rn = roman.RomanNumeral("vio", k)
        self.assertEqual(p(rn), 'A4 C5 E-5')
        rn = roman.RomanNumeral("vio6", k)
        self.assertEqual(p(rn), 'C4 E-4 A4')
        rn = roman.RomanNumeral("vio64", k)
        self.assertEqual(p(rn), 'E-4 A4 C5')

        rn = roman.RomanNumeral("vi", k)
        self.assertEqual(p(rn), 'A4 C5 E5')
        rn = roman.RomanNumeral("vi6", k)
        self.assertEqual(p(rn), 'C4 E4 A4')
        rn = roman.RomanNumeral("vi64", k)
        self.assertEqual(p(rn), 'E4 A4 C5')

        rn = roman.RomanNumeral("vio7", k)
        self.assertEqual(p(rn), 'A4 C5 E-5 G-5')
        rn = roman.RomanNumeral("vio65", k)
        self.assertEqual(p(rn), 'C4 E-4 G-4 A4')
        rn = roman.RomanNumeral("vio43", k)
        self.assertEqual(p(rn), 'E-4 G-4 A4 C5')
        rn = roman.RomanNumeral("vio42", k)
        self.assertEqual(p(rn), 'G-4 A4 C5 E-5')

        rn = roman.RomanNumeral("vi/o7", k)
        self.assertEqual(p(rn), 'A4 C5 E-5 G5')
        rn = roman.RomanNumeral("vi/o65", k)
        self.assertEqual(p(rn), 'C4 E-4 G4 A4')
        rn = roman.RomanNumeral("vi/o43", k)
        self.assertEqual(p(rn), 'E-4 G4 A4 C5')
        rn = roman.RomanNumeral("vi/o42", k)
        self.assertEqual(p(rn), 'G4 A4 C5 E-5')

        rn = roman.RomanNumeral("VI", k)
        self.assertEqual(p(rn), 'A-4 C5 E-5')
        rn = roman.RomanNumeral("VI6", k)
        self.assertEqual(p(rn), 'C4 E-4 A-4')
        rn = roman.RomanNumeral("VI64", k)
        self.assertEqual(p(rn), 'E-4 A-4 C5')

        rn = roman.RomanNumeral("bVI", k)
        self.assertEqual(p(rn), 'A--4 C-5 E--5')
        rn = roman.RomanNumeral("bVI6", k)
        self.assertEqual(p(rn), 'C-4 E--4 A--4')
        rn = roman.RomanNumeral("bVI64", k)
        self.assertEqual(p(rn), 'E--4 A--4 C-5')

        rn = roman.RomanNumeral("bvi", k)
        self.assertEqual(p(rn), 'A-4 C-5 E-5')
        rn = roman.RomanNumeral("bvi6", k)
        self.assertEqual(p(rn), 'C-4 E-4 A-4')
        rn = roman.RomanNumeral("bvi64", k)
        self.assertEqual(p(rn), 'E-4 A-4 C-5')

        rn = roman.RomanNumeral("bvio", k)
        self.assertEqual(p(rn), 'A-4 C-5 E--5')
        rn = roman.RomanNumeral("bvio6", k)
        self.assertEqual(p(rn), 'C-4 E--4 A-4')
        rn = roman.RomanNumeral("bvio64", k)
        self.assertEqual(p(rn), 'E--4 A-4 C-5')

        rn = roman.RomanNumeral("#VI", k)
        self.assertEqual(p(rn), 'A4 C#5 E5')
        rn = roman.RomanNumeral("#vi", k)
        self.assertEqual(p(rn), 'A#4 C#5 E#5')

        rn = roman.RomanNumeral("VI+", k)
        self.assertEqual(p(rn), 'A-4 C5 E5')

    def testAugmented(self):
        from music21 import roman
        def p(c):
            return " ".join([x.nameWithOctave for x in c.pitches])

        k = key.Key('a')

        rn = roman.RomanNumeral("It6", k)
        self.assertEqual(p(rn), 'F5 A5 D#6')
        rn = roman.RomanNumeral("Ger65", k)
        self.assertEqual(p(rn), 'F5 A5 C6 D#6')
        rn = roman.RomanNumeral("Ger6/5", k)
        self.assertEqual(p(rn), 'F5 A5 C6 D#6')
        rn = roman.RomanNumeral("Fr43", k)
        self.assertEqual(p(rn), 'F5 A5 B5 D#6')
        rn = roman.RomanNumeral("Fr4/3", k)
        self.assertEqual(p(rn), 'F5 A5 B5 D#6')
        rn = roman.RomanNumeral("Sw43", k)
        self.assertEqual(p(rn), 'F5 A5 B#5 D#6')

        kMaj = key.Key('A')
        rn = roman.RomanNumeral("It6", kMaj)
        self.assertEqual(p(rn), 'F5 A5 D#6')
        rn = roman.RomanNumeral("Ger65", kMaj)
        self.assertEqual(p(rn), 'F5 A5 C6 D#6')
        rn = roman.RomanNumeral("Ger6/5", kMaj)
        self.assertEqual(p(rn), 'F5 A5 C6 D#6')
        rn = roman.RomanNumeral("Fr43", kMaj)
        self.assertEqual(p(rn), 'F5 A5 B5 D#6')
        rn = roman.RomanNumeral("Fr4/3", kMaj)
        self.assertEqual(p(rn), 'F5 A5 B5 D#6')
        rn = roman.RomanNumeral("Sw43", kMaj)
        self.assertEqual(p(rn), 'F5 A5 B#5 D#6')


    def testIII7(self):
        c = chord.Chord(['E4', 'G4', 'B4', 'D5'])
        k = key.Key('C')
        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, 'iii7')

    def testHalfDimMinor(self):
        c = chord.Chord(['A3', 'C4', 'E-4', 'G4'])
        k = key.Key('c')
        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, 'vi/o7')

    def testHalfDimIII(self):
        c = chord.Chord(['F#3', 'A3', 'E4', 'C5'])
        k = key.Key('d')
        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, '#iii/o7')

    def testAugmentedOctave(self):
        c = chord.Chord(['C4', 'E5', 'G5', 'C#6'])
        k = key.Key('C')
        f = postFigureFromChordAndKey(c, k)
        self.assertEqual(f, '#853')

        rn = romanNumeralFromChord(c, k)
        self.assertEqual(rn.figure, 'I#853')


class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testFromChordify(self):
        from music21 import corpus
        b = corpus.parse('bwv103.6')
        c = b.chordify()
        ckey = b.analyze('key')
        figuresCache = {}
        for x in c.recurse():
            if 'Chord' in x.classes:
                rnc = romanNumeralFromChord(x, ckey)
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


if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, runTest='testAugmentedOctave')


#------------------------------------------------------------------------------


_DOC_ORDER = (
    RomanNumeral,
    )


#------------------------------------------------------------------------------
# eof
