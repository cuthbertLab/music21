# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         LRP.py
# Purpose:      Neo-Riemannian Chord Transformations
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#
# Copyright:    Copyright � 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines the L, P, and R objects as called on a chord.Chord. 
'''

from music21 import *
import copy

class LRPException(exceptions21.Music21Exception):
    pass

def L(c, raiseException=False):
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
            
        
def test():
    c2 = chord.Chord('C4 E-4 G4')
    c2_L = L(c2)
    c2_P = P(c2)
    assert(str(c2_L) == "<music21.chord.Chord C4 E-4 A-4>") 
    assert(str(c2_P) == "<music21.chord.Chord C4 E4 G4>") 
    
    
    c5 = chord.Chord('C4 E4 G4 C5 C5 G5')
    copyC5 = copy.deepcopy(c5)
    for i in range(20):
        c5 = L(c5)
    assert(copyC5.pitches == c5.pitches)
    
    c5 = chord.Chord('C4 E4 G4 C5 E5 G5')
    copyC5 = copy.deepcopy(c5)
    for i in range(20):
        c5 = P(c5)
    assert(copyC5.pitches == c5.pitches)
    
    c5 = chord.Chord('C4 E4 G4 C5 C5 G5')
    copyC5 = copy.deepcopy(c5)
    for i in range(20):
        c5 = R(c5)
    assert(copyC5.pitches == c5.pitches)
    

if __name__ == "__main__":
    test()
    import music21
    music21.mainTest()