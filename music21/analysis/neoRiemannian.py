# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         analysis/neoRiemannian.py
# Purpose:      Neo-Riemannian Chord Transformations
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
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

from music21 import environment
_MOD = "analysis.neoRiemannian"
environLocal = environment.Environment(_MOD)

# TODO: change doctests from passing on exceptions to raising them and trapping them.

#-------------------------------------------------------------------------------
class LRPException(exceptions21.Music21Exception):
    pass

def L(c, raiseException=False):
    '''
    L is a function that takes a major or minor triad and returns a chord that 
    is the L transformation. L transforms a chord to its Leading-Tone exchange. 
    
    Example 1: A C major chord, under P, will return an E minor chord
    
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
    
    
def P(c, raiseException=False):
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
    

def R(c, raiseException=False):
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
                     raiseException=False, 
                     leftOrdered=False, 
                     simplifyEnharmonic=False):
    '''
    LRP_combinations is a function that takes a major or minor triad and a transformationString
    and returns a transformed triad, using the L, R, and P transformations. 
    Certain combinations, such
    as LPLPLP, are cyclical, and therefore will return the original chord 
    if simplifyEnharmonic = True.
    
    leftOrdered allows a user to work with the function notation that they prefer. 
    leftOrdered = False, the default, will mean that a transformationString that reads 
    "LPRLPR" will start by transforming the chord by L, then P,
    then R, etc. Conversely, if leftOrdered = True (set by user), then "LPRLPR" will start by
    transforming the chord by R, then P, then L--by reading the transformations left to right. 
    
    simplifyEnharmonic allows a user to determine if they want the transformation to return
    the actual results of such combined transformations, 
    which may include multiple sharps and flats.
    
    If simplifyEnharmonic is True, the resulting chord will be simplified 
    to notes with at most 1 flat
    or 1 sharp, in their most common form. 
    
    >>> c1 = chord.Chord("C4 E4 G4")
    >>> c2 = analysis.neoRiemannian.LRP_combinations(c1, 'LP')
    >>> c2
    <music21.chord.Chord B3 E4 G#4>
    
    >>> c3 = chord.Chord("C4 E4 G4 C5 E5")
    >>> c4 = analysis.neoRiemannian.LRP_combinations(c3, 'RLP')
    >>> c4
    <music21.chord.Chord C4 F4 A-4 C5 F5>
    '''
    
#    >>> c5 = chord.Chord("B4 D#5 F#5")
#    >>> c6 = LRP_combinations(c5, 'LPLPLP', leftOrdered = True, simplifyEnharmonic = True)
#    >>> c6
#    <music21.chord.Chord B4 D#5 F#5>
#        >>> c5 = chord.Chord("C4 E4 G4 C5 E5")
#    >>> c6 = LRP_combinations(c5, 'LPLPLP', leftOrdered = True)
#    >>> c6
#    <music21.chord.Chord C4 E4 G4 C5 E5>
#    >>> c5 = chord.Chord("A-4 C4 E-5")
#    >>> c6 = analysis.neoRiemannian.LRP_combinations(c5, 'LPLPLP')
#    >>> c6
#    <music21.chord.Chord A-4 C4 E-5>
    
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
            if simplifyEnharmonic is False:
                return c
            else:
                for i in range(len(c.pitches)):
                    c.pitches[i].simplifyEnharmonic(inPlace=True, mostCommon=True)
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
            if simplifyEnharmonic is False:
                return c
            else:
                for i in range(len(c.pitches)):
                    c.pitches[i].simplifyEnharmonic(inPlace=True, mostCommon=True)
                return c
            
    else:
        if raiseException is True:
            raise LRPException(
                'Cannot perform transformations on this chord: not a Major or Minor triad')
        return c
    
    # TODO: Fix enharmonic problem
    # create method, chord.simplifyEnharmonic() that will take the c.root() 
    # [call it correctlySpelled or simplifySpelling or something]
    # and simplify it--how do we make sure it take the right one?
    # Conflict between G# and A-. Then build triads from there using pitch.flipEnharmonic()
    # have to make sure it is a minor or major triad
    # any possible way to peek at the original chord and use information from that to help?
    
    # Have a group of chords that are the "problematic" chords. REALLY funky chords
    # make sure it works absolutely right for major, minor, augmented, diminished triad
    # getEnharmonic on the pitches. 
    
    # problem with augmented: we'll always have a diminished fourth no matter how we spell it
    # problem with diminished: we'll have an augmented fourth
            
    # scale.deriveRanked: gives us the closest scale and how many of our notes are in that scale
    # scale.deriveAll: comparison by pitchClass, not name
    # check each of the pitches, if they're not in the scale, then flip the enharmonic
    
    # can also use isTriad and incorrectlySpelled
    
    # first figure out what scale you're simplifying into, then simplify it. 
    # Optional parameter to take the scale/key
    # to simplify into, and then we can skip the step of having to find the key. 
    
def completeHexatonic(c):
    '''
    
    >>> c1 = chord.Chord("C4 E4 G4")
    >>> analysis.neoRiemannian.completeHexatonic(c1)
    [<music21.chord.Chord C4 E-4 G4>, 
     <music21.chord.Chord C4 E-4 A-4>, 
     <music21.chord.Chord C-4 E-4 A-4>, 
     <music21.chord.Chord C-4 F-4 A-4>, 
     <music21.chord.Chord C-4 F-4 A--4>]
    '''
    #TODO: more documentation
    if c.isMajorTriad() or c.isMinorTriad():
        hexatonic_1 = P(c)
        hexatonic_2 = L(hexatonic_1)
        hexatonic_3 = P(hexatonic_2)
        hexatonic_4 = L(hexatonic_3)
        hexatonic_5 = P(hexatonic_4)
        hexatonicList = [hexatonic_1, hexatonic_2, hexatonic_3, hexatonic_4, hexatonic_5]
    return hexatonicList
            
# correct spellings
# all cycles
# what if you start on a not-even-member of the cycle?

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
        c7_T = LRP_combinations(c7, 'LP', leftOrdered=True)
        self.assertEqual(str(c7_T), "<music21.chord.Chord C4 E-4 A-4 C5 E-5>") 
        
        
    
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

