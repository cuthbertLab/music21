# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         analysis/neoRiemannian.py
# Purpose:      Neo-Riemannian Chord Transformations
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#               Mark Gotham
#
# Copyright:    Copyright © 2017-19 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module defines the L, P, and R objects and their
related transformations as called on a :class:`~music21.chord.Chord`,
according to Neo-Riemannian theory.
'''
import copy
import unittest

from music21 import exceptions21
from music21 import chord
from music21.analysis import enharmonics

from music21 import environment
_MOD = 'analysis.neoRiemannian'
environLocal = environment.Environment(_MOD)

# TODO: change doctests from passing on exceptions to raising them and trapping them.

# ------------------------------------------------------------------------------
class LRPException(exceptions21.Music21Exception):
    pass

def _simplerEnharmonics(c):
    '''
    Returns a copy of chord `c` with pitches simplified.

    Uses `:meth:music21.analysis.enharmonics.EnharmonicSimplifier.bestPitches`

    >>> c = chord.Chord('B# F- G')
    >>> c2 = analysis.neoRiemannian._simplerEnharmonics(c)
    >>> c2
    <music21.chord.Chord C E G>
    >>> c3 = analysis.neoRiemannian._simplerEnharmonics(c2)

    Returns a copy even if nothing has changed.

    >>> c2 is c3
    False
    '''
    pitchList = [p.nameWithOctave for p in c.pitches]
    es = enharmonics.EnharmonicSimplifier(pitchList)
    newPitches = es.bestPitches()
    newChord = copy.deepcopy(c)
    newChord.pitches = newPitches
    return newChord

def L(c, raiseException=True):
    '''
    L transforms a major or minor triad through the 'Leading-Tone exchange'.
    A C major chord, under L, will return an E minor chord, by transforming the root
    to its leading tone, B.

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = analysis.neoRiemannian.L(c1)
    >>> c2.pitches
    (<music21.pitch.Pitch B3>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G4>)

    Chords must be major or minor triads:

    >>> c3 = chord.Chord('C4 D4 E4')
    >>> analysis.neoRiemannian.L(c3)
    Traceback (most recent call last):
    music21.analysis.neoRiemannian.LRPException: Cannot perform L on this chord:
        not a major or minor triad

    If `raiseException` is `False` then the original chord is returned.

    >>> c4 = analysis.neoRiemannian.L(c3, raiseException=False)
    >>> c4 is c3
    True

    Accepts any music21 chord, with or without octave specified:

    >>> noOctaveChord = chord.Chord([0, 3, 7])
    >>> chordL = analysis.neoRiemannian.L(noOctaveChord)
    >>> chordL.pitches
    (<music21.pitch.Pitch C>, <music21.pitch.Pitch E->, <music21.pitch.Pitch A->)
    '''

    if c.isMajorTriad():
        transposeInterval = '-m2'
        changingPitch = c.root()
    elif c.isMinorTriad():
        transposeInterval = 'm2'
        changingPitch = c.fifth
    else:
        if raiseException is True:
            raise LRPException('Cannot perform L on this chord: not a major or minor triad')
        return c

    outChord = _singlePitchTransform(c, transposeInterval, changingPitch)
    outChord.quarterLength = c.quarterLength

    return outChord

def P(c, raiseException=True):
    '''
    P transforms a major or minor triad chord to its 'parallel':
    i.e. to the chord of the same diatonic name but opposite model.

    Example: A C major chord, under P, will return an C minor chord

    >>> c2 = chord.Chord('C4 E4 G4')
    >>> c3 = analysis.neoRiemannian.P(c2)
    >>> c3.pitches
    (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E-4>, <music21.pitch.Pitch G4>)

    See :func:`~music21.analysis.neoRiemannian.L` for further details about error handling.

    OMIT_FROM_DOCS

    >>> c3 = chord.Chord('C4 D4 E4')
    >>> analysis.neoRiemannian.P(c3)
    Traceback (most recent call last):
    music21.analysis.neoRiemannian.LRPException...
    '''
    if c.isMajorTriad():
        transposeInterval = '-A1'
        changingPitch = c.third
    elif c.isMinorTriad():
        transposeInterval = 'A1'
        changingPitch = c.third
    else:
        if raiseException is True:
            raise LRPException('Cannot perform P on this chord: not a Major or Minor triad')
        return c

    outChord = _singlePitchTransform(c, transposeInterval, changingPitch)
    outChord.quarterLength = c.quarterLength

    return outChord

def R(c, raiseException=True):
    '''
    R transforms a major or minor triad to its relative, i.e. if
    major, to its relative minor and if minor, to its relative major.

    Example 1: A C major chord, under R, will return an A minor chord

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = analysis.neoRiemannian.R(c1)
    >>> c2.pitches
    (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch A4>)

    See :func:`~music21.analysis.neoRiemannian.L` for further details about error handling.

    OMIT_FROM_DOCS

    >>> c3 = chord.Chord('C4 D4 E4')
    >>> analysis.neoRiemannian.R(c3)
    Traceback (most recent call last):
    music21.analysis.neoRiemannian.LRPException...
    '''
    if c.isMajorTriad():
        transposeInterval = 'M2'
        changingPitch = c.fifth
    elif c.isMinorTriad():
        transposeInterval = '-M2'
        changingPitch = c.root()
    else:
        if raiseException is True:
            raise LRPException('Cannot perform R on this chord: not a Major or Minor triad')
        return c

    outChord = _singlePitchTransform(c, transposeInterval, changingPitch)
    outChord.quarterLength = c.quarterLength

    return outChord

def _singlePitchTransform(c, transposeInterval, changingPitch):
    '''
    Performs a neoRiemannian transformation on c that involves transposing `changingPitch` by
    `transposeInterval`.
    '''
    changingPitchCopy = copy.deepcopy(changingPitch)
    newChord = copy.deepcopy(c)
    for i in range(len(newChord.pitches)):
        if changingPitchCopy.name == newChord.pitches[i].name:
            newChord.pitches[i].transpose(transposeInterval, inPlace=True)
    return chord.Chord(newChord.pitches)

# ------------------------------------------------------------------------------

def isNeoR(c1, c2, transforms='LRP'):
    '''
    Tests if two chords are related by a single L, P, R transformation,
    and returns that transform if so (otherwise, False).

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = chord.Chord('B3 E4 G4')
    >>> analysis.neoRiemannian.isNeoR(c1, c2)
    'L'

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = chord.Chord('C4 E-4 G4')
    >>> analysis.neoRiemannian.isNeoR(c1, c2)
    'P'

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = chord.Chord('C4 E4 A4')
    >>> analysis.neoRiemannian.isNeoR(c1, c2)
    'R'

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = chord.Chord('C-4 E-4 A-4')
    >>> analysis.neoRiemannian.isNeoR(c1, c2)
    False

    Option to limit to the search to only 1-2 transforms ('L', 'R', 'P', 'LR', 'LP', 'RP'). So:

    >>> c3 = chord.Chord('C4 E-4 G4')
    >>> analysis.neoRiemannian.isNeoR(c1, c3)
    'P'

    ... but not if P is excluded ...

    >>> analysis.neoRiemannian.isNeoR(c1, c3, transforms='LR')
    False
    '''

    c2NO = c2.normalOrder

    for i in transforms:
        if i == 'L':
            c = L(c1)
            if c.normalOrder == c2NO:
                return 'L'
        elif i == 'R':
            c = R(c1)
            if c.normalOrder == c2NO:
                return 'R'
        elif i == 'P':
            c = P(c1)
            if c.normalOrder == c2NO:
                return 'P'
        else:
            raise LRPException(f'{i} is not a NeoRiemannian transformation (L, R, or P)')

    return False  # If neither an exception, nor any of the called L, R, or P transforms

def isChromaticMediant(c1, c2):
    '''
    Tests if there is a chromatic mediant relation between two chords
    and returns the type if so (otherwise, False).

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = chord.Chord('A-3 C4 E-4')
    >>> analysis.neoRiemannian.isChromaticMediant(c1, c2)
    'LFM'

    >>> c3 = chord.Chord('C4 E4 G4')
    >>> c4 = chord.Chord('C-4 E-4 A-4')
    >>> analysis.neoRiemannian.isChromaticMediant(c3, c4)
    False
    '''

    transformList = ['UFM', 'USM', 'LFM', 'LSM']

    c2NO = c2.normalOrder

    for transform in transformList:
        thisChord = chromaticMediants(c1, transformation=transform)
        if thisChord.normalOrder == c2NO:
            return transform

    return False

# ------------------------------------------------------------------------------

def LRP_combinations(c,
                     transformationString,
                     raiseException=True,
                     leftOrdered=False,
                     simplifyEnharmonics=False,
                     eachOne=False):
    # noinspection SpellCheckingInspection
    '''
    LRP_combinations takes a major or minor triad, transforms it according to the
    list of L, R, and P transformations in the given transformationString, and
    returns the result in triad.
    Certain combinations, such as LPLPLP, are cyclical, and therefore
    will return a copy of the original chord if `simplifyEnharmonics` = `True` (see
    :func:`~music21.analysis.neoRiemannian.completeHexatonic`, below).

    `leftOrdered` allows a user to work with their preferred function notation (left or right
    orthography).

    By default, `leftOrdered` is False, so transformations progress towards the right.
    Thus 'LPR' will start by transforming the chord by L, then P, then R.

    If `leftOrdered` is True, the operations work in the opposite direction (right to left), so
    'LPR' indicates the result of the chord transformed by R, then P, then L.

    `simplifyEnharmonics` replaces multiple sharps and flats where they arise from
    combined transformations with the simpler enharmonic equivalent (e.g. C for D--).
    If simplifyEnharmonics is True, the resulting chord will be simplified
    to notes with at most 1 flat or 1 sharp, in their most common form.

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> c2 = analysis.neoRiemannian.LRP_combinations(c1, 'LP')
    >>> c2
    <music21.chord.Chord B3 E4 G#4>

    >>> c2b = analysis.neoRiemannian.LRP_combinations(c1, 'LP', leftOrdered=True)
    >>> c2b
    <music21.chord.Chord C4 E-4 A-4>

    >>> c3 = chord.Chord('C4 E4 G4 C5 E5')
    >>> c4 = analysis.neoRiemannian.LRP_combinations(c3, 'RLP')
    >>> c4
    <music21.chord.Chord C4 F4 A-4 C5 F5>

    >>> c5 = chord.Chord('B4 D#5 F#5')
    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5,
    ...                        'LPLPLP', leftOrdered=True, simplifyEnharmonics=True)
    >>> c6
    <music21.chord.Chord B4 D#5 F#5>
    >>> c5 = chord.Chord('C4 E4 G4')
    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 'LPLPLP', leftOrdered=True)
    >>> c6
    <music21.chord.Chord D--4 F-4 A--4>
    >>> c5 = chord.Chord('A-4 C4 E-5')
    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 'LPLPLP')
    >>> c6
    <music21.chord.Chord G#4 B#3 D#5>

    Optionally: return all of the chords creating by the given string in order.

    >>> c7 = chord.Chord('C4 E4 G4')
    >>> c8 = analysis.neoRiemannian.LRP_combinations(
    ...            c7, 'LPLPLP', simplifyEnharmonics=True, eachOne=True)
    >>> c8
    [<music21.chord.Chord B3 E4 G4>,
    <music21.chord.Chord B3 E4 G#4>,
    <music21.chord.Chord B3 D#4 G#4>,
    <music21.chord.Chord C4 E-4 A-4>,
    <music21.chord.Chord C4 E-4 G4>,
    <music21.chord.Chord C4 E4 G4>]

    On that particular case of LPLPLP, see more in
    :func:`~music21.analysis.neoRiemannian.completeHexatonic`.
    '''

    if c.forteClassTnI != '3-11':  # First to avoid doing anything else if fail
        if raiseException is True:
            raise LRPException(
                f'Cannot perform transformations on chord {c}: not a major or minor triad')
        return c

    if leftOrdered:
        transformationString = transformationString[::-1]

    chordList = []

    for i in transformationString:
        if i == 'L':
            c = L(c)
            if eachOne:
                chordList.append(copy.deepcopy(c))
        elif i == 'R':
            c = R(c)
            if eachOne:
                chordList.append(copy.deepcopy(c))
        elif i == 'P':
            c = P(c)
            if eachOne:
                chordList.append(copy.deepcopy(c))
        else:
            raise LRPException(f'{i} is not a NeoRiemannian transformation (L, R, or P)')

    if eachOne:
        if not simplifyEnharmonics:
            return chordList
        else:
            return [_simplerEnharmonics(x) for x in chordList]
    else:
        if not simplifyEnharmonics:
            return c
        else:
            return _simplerEnharmonics(c)

def completeHexatonic(c, simplifyEnharmonics=False, raiseException=True):
    '''
    completeHexatonic returns the list of six triads generated by the operation PLPLPL.
    This six-part operation cycles between major and minor triads, ultimately returning to the
    input triad (or its enharmonic equivalent).
    This functions returns those six triads, ending with the original triad.

    `simplifyEnharmonics` is False, by default, giving double flats at the end.

    >>> c1 = chord.Chord('C4 E4 G4')
    >>> analysis.neoRiemannian.completeHexatonic(c1)
    [<music21.chord.Chord C4 E-4 G4>,
     <music21.chord.Chord C4 E-4 A-4>,
     <music21.chord.Chord C-4 E-4 A-4>,
     <music21.chord.Chord C-4 F-4 A-4>,
     <music21.chord.Chord C-4 F-4 A--4>,
     <music21.chord.Chord D--4 F-4 A--4>]

    `simplifyEnharmonics` can be set to True in order to avoid this.

    >>> c2 = chord.Chord('C4 E4 G4')
    >>> analysis.neoRiemannian.completeHexatonic(c2, simplifyEnharmonics=True)
    [<music21.chord.Chord C4 E-4 G4>,
     <music21.chord.Chord C4 E-4 A-4>,
     <music21.chord.Chord B3 D#4 G#4>,
     <music21.chord.Chord B3 E4 G#4>,
     <music21.chord.Chord B3 E4 G4>,
     <music21.chord.Chord C4 E4 G4>]
    '''
    if c.forteClassTnI == '3-11':
        hexatonicList = []
        lastChord = c
        operations = [P, L, P, L, P, L]
        for operation in operations:
            lastChord = operation(lastChord)
            if simplifyEnharmonics:
                lastChord = _simplerEnharmonics(lastChord)
            hexatonicList.append(lastChord)
        return hexatonicList
    else:
        if raiseException is True:
            raise LRPException(
                'Cannot perform transformations on this chord: not a major or minor triad')

def hexatonicSystem(c):
    '''
    Returns a lowercase string representing the
    "hexatonic system" that the chord `c` belongs to
    as classified by Richard Cohn, "Maximally Smooth Cycles,
    Hexatonic Systems, and the Analysis of Late-Romantic
    Triadic Progressions," *Music Analysis*, 15.1 (1996), 9-40,
    at p. 17.  Possible values are 'northern', 'western', 'eastern', or 'southern'

    >>> cMaj = chord.Chord('C E G')
    >>> analysis.neoRiemannian.hexatonicSystem(cMaj)
    'northern'

    >>> gMin = chord.Chord('G B- D')
    >>> analysis.neoRiemannian.hexatonicSystem(gMin)
    'western'

    Each chord in the :func:`~music21.analysis.neoRiemannian.completeHexatonic` of that chord
    is in the same hexatonic system, by definition or tautology.

    >>> for ch in analysis.neoRiemannian.completeHexatonic(cMaj):
    ...     print(analysis.neoRiemannian.hexatonicSystem(ch))
    northern
    northern
    northern
    northern
    northern
    northern

    Note that the classification looks only at the
    pitch class of the root of the chord.  Seventh chords,
    diminished triads, etc. will also be classified.

    >>> dDom65 = chord.Chord('F#4 D5 A5 C6')
    >>> analysis.neoRiemannian.hexatonicSystem(dDom65)
    'southern'
    '''
    root = c.root()
    rootPC = root.pitchClass

    mappings = [({0, 4, 8}, 'northern'),
                ({1, 5, 9}, 'eastern'),
                ({2, 6, 10}, 'southern'),
                ({3, 7, 11}, 'western'),
                ]
    for pcSet, poleName in mappings:
        if rootPC in pcSet:
            return poleName

    raise LRPException('Odd pitch class that is not in 0 to 11!')  # pragma: no cover


# ------------------------------------------------------------------------------

# Some special of LPR combinations

def chromaticMediants(c, transformation='UFM'):
    '''
    Transforms a chord into the given chromatic mediant. Options:
    UFM = Upper Flat Mediant;
    USM = Upper Sharp Mediant;
    LFM = Lower Flat Mediant ;
    LSM = Lower Sharp Mediant;

    Each of these transformations
    is mode-preserving;
    involves root motion by a third;
    entails exactly one common-tone.

    >>> cMaj = chord.Chord('C5 E5 G5')
    >>> UFMcMaj = analysis.neoRiemannian.chromaticMediants(cMaj, transformation='UFM')
    >>> UFMcMaj.normalOrder
    [3, 7, 10]

    >>> USMcMaj = analysis.neoRiemannian.chromaticMediants(cMaj, transformation='USM')
    >>> USMcMaj.normalOrder
    [4, 8, 11]

    >>> LFMcMaj = analysis.neoRiemannian.chromaticMediants(cMaj, transformation='LFM')
    >>> [x.nameWithOctave for x in LFMcMaj.pitches]
    ['C5', 'E-5', 'A-5']

    >>> LSMcMaj = analysis.neoRiemannian.chromaticMediants(cMaj, transformation='LSM')
    >>> [x.nameWithOctave for x in LSMcMaj.pitches]
    ['C#5', 'E5', 'A5']

    Fine to call on a chord with multiple enharmonics,
    but will always simplify the output chromatic mediant.

    >>> cMajEnh = chord.Chord('D--5 F-5 A--5')
    >>> USM = analysis.neoRiemannian.chromaticMediants(cMaj, transformation='USM')
    >>> [x.nameWithOctave for x in USM.pitches]
    ['B4', 'E5', 'G#5']
    >>> USM.normalOrder == USMcMaj.normalOrder
    True
    '''

    options = ['UFM', 'USM', 'LFM', 'LSM']
    if transformation not in options:
        raise ValueError(f'Transformation must be one of {options}')

    transformationString = 'PR'  # Initialised for 'UFM'
    if transformation == 'USM':
        transformationString = 'LP'
    elif transformation == 'LFM':
        transformationString = 'PL'
    elif transformation == 'LSM':
        transformationString = 'RP'

    if c.isMinorTriad():
        LO = True
    elif c.isMajorTriad():
        LO = False
    else:
        raise ValueError('Chord must be major or minor')

    c = LRP_combinations(c, transformationString, leftOrdered=LO)

    return _simplerEnharmonics(c)

def disjunctMediants(c, upperOrLower='upper'):
    '''
    Transforms a chord into the upper or lower disjunct mediant.
    These transformations involve:
    root motion by a non-diatonic third;
    mode-change;
    no common-tones.

    >>> cMaj = chord.Chord('C5 E5 G5')
    >>> upr = analysis.neoRiemannian.disjunctMediants(cMaj, upperOrLower='upper')
    >>> [x.name for x in upr.pitches]
    ['B-', 'E-', 'G-']
    >>> lwr = analysis.neoRiemannian.disjunctMediants(cMaj, upperOrLower='lower')
    >>> [x.name for x in lwr.pitches]
    ['B', 'D#', 'G#']
    '''

    options = ['upper', 'lower']
    if upperOrLower not in options:
        raise ValueError(f'upperOrLower must be one of {options}')

    transformationString = 'PRP'  # Initialised for major upper and minor lower

    if c.isMajorTriad():
        if upperOrLower == 'lower':  # Change
            transformationString = 'PLP'
    elif c.isMinorTriad():
        if upperOrLower == 'upper':
            transformationString = 'PLP'
    else:
        raise ValueError('Chord must be major or minor')

    c = LRP_combinations(c, transformationString)

    return _simplerEnharmonics(c)

def S(c):
    '''
    Slide transform connecting major and minor triads with the third as the single common tone
    (i.e. with the major triad root a semi-tone below the minor). So:
    root motion by a semi-tone;
    mode-change;
    one common-tones.
    Slide is equivalent to 'LPR'.

    >>> cMaj = chord.Chord('C5 E5 G5')
    >>> slideUp = analysis.neoRiemannian.S(cMaj)
    >>> [x.name for x in slideUp.pitches]
    ['C#', 'E', 'G#']

    >>> aMin = chord.Chord('A4 C5 E5')
    >>> slideDown = analysis.neoRiemannian.S(aMin)
    >>> [x.name for x in slideDown.pitches]
    ['A-', 'C', 'E-']
    '''

    return LRP_combinations(c, 'LPR', simplifyEnharmonics=False)

def N(c):
    '''
    The 'Neberverwandt' ('fifth-change') transform connects
    a minor triad with its major dominant, and so also
    a major triad with its minor sub-dominant,
    with one common tone in each case.
    This is equivalent to 'RLP'.

    >>> cMaj = chord.Chord('C5 E5 G5')
    >>> n1 = analysis.neoRiemannian.N(cMaj)
    >>> [x.name for x in n1.pitches]
    ['C', 'F', 'A-']

    >>> aMin = chord.Chord('A4 C5 E5')
    >>> n2 = analysis.neoRiemannian.N(aMin)
    >>> [x.name for x in n2.pitches]
    ['G#', 'B', 'E']
    '''

    return LRP_combinations(c, 'RLP', simplifyEnharmonics=False)

# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def testNeoRiemannianTransformations(self):
        c2 = chord.Chord('C4 E-4 G4')
        c2_L = L(c2)
        c2_P = P(c2)
        self.assertEqual(str(c2_L), '<music21.chord.Chord C4 E-4 A-4>')
        self.assertIsInstance(c2_L, chord.Chord)
        self.assertEqual(str(c2_P), '<music21.chord.Chord C4 E4 G4>')

        c5 = chord.Chord('C4 E4 G4 C5 C5 G5')
        copyC5 = copy.deepcopy(c5)
        for i in range(4):
            c5 = L(c5)
        self.assertEqual(copyC5.pitches, c5.pitches)

        c5 = chord.Chord('C4 E4 G4 C5 E5 G5')
        copyC5 = copy.deepcopy(c5)
        for i in range(4):
            c5 = P(c5)
        self.assertEqual(copyC5.pitches, c5.pitches)

        c5 = chord.Chord('C4 E4 G4 C5 C5 G5')
        copyC5 = copy.deepcopy(c5)
        for i in range(4):
            c5 = R(c5)
        self.assertEqual(copyC5.pitches, c5.pitches)

    def testNeoRiemannianCombinations(self):
        c5 = chord.Chord('C4 E4 G4')
        c5_T = LRP_combinations(c5, 'LP')
        self.assertEqual(str(c5_T), '<music21.chord.Chord B3 E4 G#4>')

        c6 = chord.Chord('C4 E4 G4 C5 E5')
        c6_T = LRP_combinations(c6, 'RLP')
        self.assertEqual(str(c6_T), '<music21.chord.Chord C4 F4 A-4 C5 F5>')

        c7 = chord.Chord('C4 E4 G4 C5 E5')
        c7_T = LRP_combinations(c7, 'LP', leftOrdered=True)
        self.assertEqual(str(c7_T), '<music21.chord.Chord C4 E-4 A-4 C5 E-5>')

        c8 = chord.Chord('C-4 E-4 G-4')
        c8_T = LRP_combinations(c8, 'LP')
        self.assertEqual(str(c8_T), '<music21.chord.Chord B-3 E-4 G4>')

    def testIsNeoR(self):

        c1 = chord.Chord('C4 E4 G4')

        c2 = chord.Chord('B3 E4 G4')
        ans1 = isNeoR(c1, c2)
        self.assertEqual(ans1, 'L')

        c3 = chord.Chord('C4 E-4 G4')
        ans2 = isNeoR(c1, c3)
        self.assertEqual(ans2, 'P')
        # ... But not if P is excluded ...
        ans2 = isNeoR(c1, c3, transforms='LR')
        self.assertFalse(ans2)

        c4 = chord.Chord('C4 E4 A4')
        ans3 = isNeoR(c1, c4)
        self.assertEqual(ans3, 'R')

        c5 = chord.Chord('C4 E-4 A-4')
        ans4 = isChromaticMediant(c1, c5)
        self.assertEqual(ans4, 'LFM')

        c6 = chord.Chord('C-4 E-4 A-4')
        ans5 = isNeoR(c1, c6)
        ans6 = isChromaticMediant(c1, c6)
        self.assertFalse(ans5)
        self.assertFalse(ans6)  # disjunct mediants not currently included

        c7 = chord.Chord('C-4 E-4 G-4')
        c8 = chord.Chord('C-4 E--4 A--4')
        ans7 = isNeoR(c7, c8)
        ans8 = isChromaticMediant(c7, c8)
        self.assertFalse(ans7)
        self.assertEqual(ans8, 'LFM')

    def testMediants(self):

        c9 = chord.Chord('C5 E5 G5')
        c9a = chord.Chord('C#5 E#5 G#5')

        UFMcMaj = chromaticMediants(c9, transformation='UFM')
        self.assertEqual(UFMcMaj.normalOrder, [3, 7, 10])

        USMcMaj = chromaticMediants(c9, transformation='USM')
        self.assertEqual(USMcMaj.normalOrder, [4, 8, 11])

        LFMcMaj = chromaticMediants(c9, transformation='LFM')
        self.assertEqual([x.nameWithOctave for x in LFMcMaj.pitches], ['C5', 'E-5', 'A-5'])

        LSMcMaj = chromaticMediants(c9, transformation='LSM')
        self.assertEqual([x.nameWithOctave for x in LSMcMaj.pitches], ['C#5', 'E5', 'A5'])

        upChromatic = disjunctMediants(c9a, upperOrLower='upper')
        self.assertEqual([x.name for x in upChromatic.pitches], ['B', 'E', 'G'])

        downChromatic = disjunctMediants(c9a, upperOrLower='lower')
        self.assertEqual([x.nameWithOctave for x in downChromatic.pitches],
                         ['C5', 'E5', 'A5'])

    def testSnN(self):

        c10 = chord.Chord('C5 E5 G5')
        c11 = chord.Chord('A4 C5 E5')

        slideUp = S(c10)
        self.assertEqual([x.name for x in slideUp.pitches], ['C#', 'E', 'G#'])

        slideDown = S(c11)
        self.assertEqual([x.name for x in slideDown.pitches], ['A-', 'C', 'E-'])

        N1 = N(c10)
        self.assertEqual([x.name for x in N1.pitches], ['C', 'F', 'A-'])

        N2 = N(c11)
        self.assertEqual([x.name for x in N2.pitches], ['G#', 'B', 'E'])


# ------------------------------------------------------------------------------
_DOC_ORDER = [
    L, R, P, S, N, isNeoR,
    LRP_combinations, completeHexatonic, hexatonicSystem, LRPException,
    chromaticMediants, isChromaticMediant,
    disjunctMediants,
]


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
