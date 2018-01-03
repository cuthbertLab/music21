# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         analysis/neoRiemannian.py
# Purpose:      Neo-Riemannian Chord Transformations
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#               Mark Gotham
#
# Copyright:    Copyright © 2017 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines the L, P, and R objects and their
related transformations as called on a chord.Chord, according to Neo-Riemannian theory.
'''
import copy
import unittest

from music21 import exceptions21
from music21 import chord
from music21.analysis import enharmonics

from music21 import environment
_MOD = "analysis.neoRiemannian"
environLocal = environment.Environment(_MOD)

# TODO: change doctests from passing on exceptions to raising them and trapping them.

#-------------------------------------------------------------------------------
class LRPException(exceptions21.Music21Exception):
    pass

def simplerEnharmonics(c):
    pitchList = [p.nameWithOctave for p in c.pitches]
    es = enharmonics.EnharmonicSimplifier(pitchList)
    newPitches = es.bestPitches()
    newChord = copy.deepcopy(c)
    newChord.pitches = newPitches
    return newChord

def L(c, raiseException=True):
    '''
    L is a function that takes a major or minor triad and returns a chord that
    is the L transformation. L transforms a chord to its Leading-Tone exchange.

    Example 1: A C major chord, under L, will return an E minor chord

    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = analysis.neoRiemannian.L(c1)
    >>> c2.pitches
    (<music21.pitch.Pitch B3>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G4>)

    >>> try:
    ...     c3 = chord.Chord("C4 D4 E4")
    ...     c4 = analysis.neoRiemannian.L(c3, raiseException=True)
    ... except analysis.neoRiemannian.LRPException:
    ...     pass

    '''
    if c.isMajorTriad():
        transposeInterval = "-m2"
        changingPitch = c.root()
    elif c.isMinorTriad():
        transposeInterval = "m2"
        changingPitch = c.fifth
    else:
        if raiseException is True:
            raise LRPException('Cannot perform L on this chord: not a Major or Minor triad')
        return c

    return LRP_transform(c, transposeInterval, changingPitch)


def P(c, raiseException=True):
    '''
    P is a function that takes a major or minor triad and returns a chord that
    is the P transformation. P transforms a chord to its parallel, i.e. to the
    chord of the same diatonic name but opposite model.

    Example 1: A C major chord, under P, will return an C minor chord

    >>> c2 = chord.Chord("C4 E4 G4")
    >>> c3 = analysis.neoRiemannian.P(c2)
    >>> c3.pitches
    (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E-4>, <music21.pitch.Pitch G4>)

    >>> try:
    ...     c3 = chord.Chord("C4 D4 E4")
    ...     c4 = analysis.neoRiemannian.P(c3, raiseException=True)
    ... except analysis.neoRiemannian.LRPException:
    ...     pass

    '''
    if c.isMajorTriad():
        transposeInterval = "-A1"
        changingPitch = c.third
    elif c.isMinorTriad() :
        transposeInterval = "A1"
        changingPitch = c.third
    else:
        if raiseException is True:
            raise LRPException('Cannot perform P on this chord: not a Major or Minor triad')
        return c
    return LRP_transform(c, transposeInterval, changingPitch)


def R(c, raiseException=True):
    '''
    R is a function that takes a major or minor triad and returns a chord that
    is the R transformation. R transforms a chord to its relative, i.e. if
    major, to its relative minor and if minor, to its relative major.

    Example 1: A C major chord, under R, will return an A minor chord

    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = analysis.neoRiemannian.R(c1)
    >>> c2.pitches
    (<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch A4>)

    >>> try:
    ...     c3 = chord.Chord("C4 D4 E4")
    ...     c4 = analysis.neoRiemannian.R(c3, raiseException=True)
    ... except analysis.neoRiemannian.LRPException:
    ...     pass

    '''
    if c.isMajorTriad():
        transposeInterval = "M2"
        changingPitch = c.fifth
    elif c.isMinorTriad() :
        transposeInterval = "-M2"
        changingPitch = c.root()
    else:
        if raiseException is True:
            raise LRPException('Cannot perform R on this chord: not a Major or Minor triad')
        return c

    return LRP_transform(c, transposeInterval, changingPitch)

def LRP_transform(c, transposeInterval, changingPitch):
    changingPitchCopy = copy.deepcopy(changingPitch)
    newChord = copy.deepcopy(c)
    for i in range (len(newChord.pitches)):
        if changingPitchCopy.name == newChord.pitches[i].name:
            newChord.pitches[i].transpose(transposeInterval, inPlace=True)
    return chord.Chord(newChord.pitches)

def LRP_combinations(c,
                     transformationString,
                     raiseException=True,
                     leftOrdered=False,
                     simplifyEnharmonics=False):
    '''
    LRP_combinations takes a major or minor triad, tranforms it according to the
    list of L, R, and P transformations in the given transformationString, and
    returns the result in triad.
    Certain combinations, such as LPLPLP, are cyclical, and therefore
    will return the original chord if simplifyEnharmonics = True (see completeHexatonic, below).

    leftOrdered allows a user to work with their preferred function notation.
    leftOrdered = False, the default, reads the transformationString from left to right,
    so "LPR" will start by transforming the chord by L, then P, then R.
    leftOrdered = True (set by user) works in the opposite direction (right to left), so
    "LPR" starts with R, then P, then L.

    simplifyEnharmonics returns results removing multiple sharps and flats where
    they arise from combined transformations.
    If simplifyEnharmonics is True, the resulting chord will be simplified
    to notes with at most 1 flat or 1 sharp, in their most common form.

    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = analysis.neoRiemannian.LRP_combinations(c1, 'LP')
    >>> c2
    <music21.chord.Chord B3 E4 G#4>

    >>> c3 = chord.Chord("C4 E4 G4 C5 E5")
    >>> c4 = analysis.neoRiemannian.LRP_combinations(c3, 'RLP')
    >>> c4
    <music21.chord.Chord C4 F4 A-4 C5 F5>

    >>> c5 = chord.Chord("B4 D#5 F#5")
    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 
    ...                        'LPLPLP', leftOrdered=True, simplifyEnharmonics=True)
    >>> c6
    <music21.chord.Chord B4 D#5 F#5>
    >>> c5 = chord.Chord("C4 E4 G4")
    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 'LPLPLP', leftOrdered=True)
    >>> c6
    <music21.chord.Chord D--4 F-4 A--4>
    >>> c5 = chord.Chord("A-4 C4 E-5")
    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 'LPLPLP')
    >>> c6
    <music21.chord.Chord G#4 B#3 D#5>
    '''

    if c.isMajorTriad()  or c.isMinorTriad():
        if leftOrdered is False:
            for i in transformationString:
                if i == 'L':
                    c = L(c)
                elif i == 'R':
                    c = R(c)
                elif i == 'P':
                    c = P(c)
                else:
                    raise LRPException('This is not a NeoRiemannian transformation, L, R, or P')
            if simplifyEnharmonics is False:
                return c
            else:
                return simplerEnharmonics(c)
                ## Previously:
                # newPitches = pitch.simplifyMultipleEnharmonics(c.pitches, keyContext=key.Key('C'))
        elif leftOrdered is True:
            transformationStringReversed = transformationString[::-1]
            for i in transformationStringReversed:
                if i == 'L':
                    c = L(c)
                elif i == 'R':
                    c = R(c)
                elif i == "P":
                    c = P(c)
                else:
                    raise LRPException('This is not a NeoRiemannian transformation, L, R, or P')
            if simplifyEnharmonics is False:
                return c
            else:
                return simplerEnharmonics(c)

    else:
        if raiseException is True:
            raise LRPException(
                'Cannot perform transformations on this chord: not a Major or Minor triad')
        return c

def completeHexatonic(c, simplifyEnharmonics=False, raiseException=True):
    '''
    completeHexatonic returns the list of six triads generated by the operation PLPLPL.
    This six-part operation cycles between major and minor triads, ultimately returning to the
    input triad (or its enharmonic equivalent).
    This functions returns those six triads, ending with the original triad.
    simplifyEnharmonics=False, by default, giving double flats;
    simplifyEnharmonics can be set to True in order to avoid this.

    >>> c1 = chord.Chord("C4 E4 G4")
    >>> analysis.neoRiemannian.completeHexatonic(c1)
    [<music21.chord.Chord C4 E-4 G4>,
     <music21.chord.Chord C4 E-4 A-4>,
     <music21.chord.Chord C-4 E-4 A-4>,
     <music21.chord.Chord C-4 F-4 A-4>,
     <music21.chord.Chord C-4 F-4 A--4>,
     <music21.chord.Chord D--4 F-4 A--4>]

    Or with  simplifyEnharmonics=True
     
    >>> c2 = chord.Chord("C4 E4 G4")
    >>> analysis.neoRiemannian.completeHexatonic(c2, simplifyEnharmonics=True)
    [<music21.chord.Chord C4 E-4 G4>,
     <music21.chord.Chord C4 E-4 A-4>,
     <music21.chord.Chord B3 D#4 G#4>,
     <music21.chord.Chord B3 E4 G#4>,
     <music21.chord.Chord B3 E4 G4>,
     <music21.chord.Chord C4 E4 G4>]
    '''
    if c.isMajorTriad() or c.isMinorTriad():
        hexatonicList = []
        lastChord = c
        operations = [P, L, P, L, P, L]
        for operation in operations:
            lastChord = operation(lastChord)
            if simplifyEnharmonics:
                lastChord = simplerEnharmonics(lastChord)
            hexatonicList.append(lastChord)
        return hexatonicList
    else:
        if raiseException is True:
            raise LRPException(
                'Cannot perform transformations on this chord: not a Major or Minor triad')

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testNeoRiemannianTransformations(self):
        c2 = chord.Chord('C4 E-4 G4')
        c2_L = L(c2)
        c2_P = P(c2)
        self.assertEqual(str(c2_L), "<music21.chord.Chord C4 E-4 A-4>")
        self.assertIsInstance(c2_L, chord.Chord)
        self.assertEqual(str(c2_P), "<music21.chord.Chord C4 E4 G4>")

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
        self.assertEqual(str(c5_T), "<music21.chord.Chord B3 E4 G#4>")

        c6 = chord.Chord('C4 E4 G4 C5 E5')
        c6_T = LRP_combinations(c6, 'RLP')
        self.assertEqual(str(c6_T), "<music21.chord.Chord C4 F4 A-4 C5 F5>")

        c7 = chord.Chord('C4 E4 G4 C5 E5')
        c7_T = LRP_combinations(c7, 'LP', leftOrdered=True)
        self.assertEqual(str(c7_T), "<music21.chord.Chord C4 E-4 A-4 C5 E-5>")

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
