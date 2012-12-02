# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         neoRiemannian.py
# Purpose:      Neo-Riemannian Chord Transformations
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#
# Copyright:    Copyright � 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines the L, P, and R objects and their related transformations as called on a chord.Chord. 
'''
import unittest

from music21 import exceptions21
from music21 import chord
import copy

from music21 import environment
_MOD = "analysis.neoRiemannian"
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class LRPException(exceptions21.Music21Exception):
    pass

class leftOrdered:
    pass

def L(c, raiseException=False):
    #TODO: Figure out how to get analysis.neoRiemannian to work
    
    '''
    L is a function that takes a major or minor triad and returns a chord that is the L transformation. L transforms a chord to its Leading-Tone exchange. 
    
    Example 1: A C major chord, under P, will return an E minor chord
    
    >>> from music21 import *
    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = L(c1)
    >>> c2.pitches
    [<music21.pitch.Pitch B3>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch G4>]
    
    >>> try:
    ...     c3 = chord.Chord("C4 D4 E4")
    ...     c4 = L(c3, raiseException=True)
    ... except LRPException:
    ...     pass
    
    '''
    if c.isMajorTriad() == True:
        transposeInterval = "-m2"
        changingPitch = c.root()
    elif c.isMinorTriad() == True:
        transposeInterval = "m2"
        changingPitch = c.fifth
    else:
        if raiseException is True:
            raise LRPException('Cannot perform R on this chord: not a Major or Minor triad')
        return c

    return LRP_transform(c, transposeInterval, changingPitch)
    
def P(c, raiseException=False):
    '''
    P is a function that takes a major or minor triad and returns a chord that is the P transformation. P transforms a chord to its parallel, 
    i.e. to the chord of the same diatonic name but opposite model.
    
    Example 1: A C major chord, under P, will return an C minor chord
    
    >>> from music21 import *
    >>> c2 = chord.Chord("C4 E4 G4")
    >>> c3 = P(c2)
    >>> c3.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch E-4>, <music21.pitch.Pitch G4>]
    
    >>> try:
    ...     c3 = chord.Chord("C4 D4 E4")
    ...     c4 = P(c3, raiseException=True)
    ... except LRPException:
    ...     pass
    
    '''
    if c.isMajorTriad() == True:
        transposeInterval = "-A1"
        changingPitch = c.third
    elif c.isMinorTriad() == True:
        transposeInterval = "A1"
        changingPitch = c.third
    else:
        if raiseException is True:
            raise LRPException('Cannot perform R on this chord: not a Major or Minor triad')
        return c

    return LRP_transform(c, transposeInterval, changingPitch)
    
def R(c, raiseException=False):
    '''
    R is a function that takes a major or minor triad and returns a chord that is the R transformation. R transforms a chord to its relative, 
    i.e. if major, to its relative minor and if minor, to its relative major.
    
    Example 1: A C major chord, under R, will return an A minor chord
    
    >>> from music21 import *
    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = R(c1)
    >>> c2.pitches
    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch E4>, <music21.pitch.Pitch A4>]
    
    >>> try:
    ...     c3 = chord.Chord("C4 D4 E4")
    ...     c4 = R(c3, raiseException=True)
    ... except LRPException:
    ...     pass
    
    '''
    if c.isMajorTriad() == True:
        transposeInterval = "M2"
        changingPitch = c.fifth
    elif c.isMinorTriad() == True:
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

def LRP_combinations(c, transformationString, raiseException = False, leftOrdered = False):
    
    '''
    LRP_combinations is a function that takes a major or minor triad and a transformationString
    and returns a transformed triad, using the L, R, and P transformations. Certain combinations, such
    as LPLPLP, are cyclical, and therefore will return the original chord. leftOrdered allows a user
    to work with the function notation that they prefer. leftOrdered = False, the default, will mean
    that a transformationString that reads "LPRLPR" will start by transforming the chord by L, then P,
    then R, etc. Conversely, if leftOrdered = True (set by user), then "LPRLPR" will start by
    transforming the chord by R, then P, then L--by reading the transformations left to right. 
    
    >>> from music21 import *
    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = LRP_combinations(c1, 'LP')
    >>> c2
    <music21.chord.Chord B3 E4 G#4>
    
    >>> c3 = chord.Chord("C4 E4 G4 C5 E5")
    >>> c4 = LRP_combinations(c3, 'RLP')
    >>> c4
    <music21.chord.Chord C4 F4 A-4 C5 F5>
    
    >>> c5 = chord.Chord("C4 E4 G4 C5 E5")
    >>> c6 = LRP_combinations(c5, 'LPLPLP', leftOrdered = True)
    >>> c6
    <music21.chord.Chord C4 E4 G4 C5 E5>
    '''
#    >>> c5 = chord.Chord("A-4 C4 E-5")
#    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 'LPLPLP')
#    >>> c6
#    <music21.chord.Chord A-4 C4 E-5>
    
    if c.isMajorTriad() == True or c.isMinorTriad() == True:
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
            for i in range(len(c.pitches)):
                c.pitches[i].simplifyEnharmonic(inPlace = True, mostCommon=True)
            return c
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
            for i in range(len(c.pitches)):
                c.pitches[i].simplifyEnharmonic(inPlace = True, mostCommon = True)
            return c
            
    else:
        if raiseException is True:
            raise LRPException('Cannot perform transformations on this chord: not a Major or Minor triad')
        return c
            
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def testNeoRiemannianTransformations(self):
        c2 = chord.Chord('C4 E-4 G4')
        c2_L = L(c2)
        c2_P = P(c2)
        self.assertEqual(str(c2_L), "<music21.chord.Chord C4 E-4 A-4>") 
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
        c7_T = LRP_combinations(c7, 'LP', leftOrdered = True)
        self.assertEqual(str(c7_T), "<music21.chord.Chord C4 E-4 A-4 C5 E-5>") 
        
        c8 = chord.Chord('C4 E-4 G4 C5 E-5')
        c8_T = LRP_combinations(c8, 'LPLPLP', leftOrdered = True)
        self.assertEqual(str(c8_T), "<music21.chord.Chord C4 E-4 G4 C5 E-5>") 
        
    
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)