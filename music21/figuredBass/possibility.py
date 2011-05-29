#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         possibility.py
# Purpose:      music21 class to define rule checking methods for a possibility
#                represented as a tuple.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import itertools
import music21
import unittest

from music21 import voiceLeading

'''
For other classes in fbRealizer, a possibility is a tuple, represented as follows:
(B3, F3, D3, D3)
The possibility is always in order from highest part to lowest part, although not
necessarily from highest pitch to lowest pitch, because voice crossing is supported.

The highest part by convention is 1, the lowest is the length of the possibility, 
which in the above case is 4.
'''
# SINGLE POSSIBILITY RULE-CHECKING METHODS
# ----------------------------------------
def voiceCrossing(possibA):
    '''
    Returns True if there is voice crossing present between any two parts 
    in possibA. The parts in decreasing order must correspond to decreasingly 
    lower pitches in order for there to be no voice crossing.
    
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = Pitch('C4')
    >>> E4 = Pitch('E4')
    >>> C5 = Pitch('C5')
    >>> G5 = Pitch('G5')
    >>> possibA1 = (C5, G5, E4)
    >>> possibility.voiceCrossing(possibA1)
    True
    >>> possibA2 = (C5, E4, C4)
    >>> possibility.voiceCrossing(possibA2)
    False 
    '''
    hasVoiceCrossing = False
    for part1Index in range(len(possibA)):
        higherPitch = possibA[part1Index]
        for part2Index in range(part1Index + 1, len(possibA)):
            lowerPitch = possibA[part2Index]
            if higherPitch < lowerPitch:
                hasVoiceCrossing = True
                return hasVoiceCrossing

    return hasVoiceCrossing    
    
def isIncomplete(possibA, pitchNamesToContain):
    '''
    Returns True if possibA is incomplete, if it doesn't contain at least
    one of every pitch name in pitchNamesToContain.
    
    If possibA contains excessive pitch names, a PossibilityException is
    raised.
    
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = Pitch('C3')
    >>> E4 = Pitch('E4')
    >>> G4 = Pitch('G4')
    >>> C5 = Pitch('C5')
    >>> Bb5 = Pitch('B-5')
    >>> pitchNamesA1 = ['C', 'E', 'G']
    >>> possibA1 = (C5, G4, E4, C3)
    >>> possibility.isIncomplete(possibA1, pitchNamesA1)
    False
    >>> possibA2 = (Bb5, G4, E4, C3)
    >>> possibility.isIncomplete(possibA2, pitchNamesA1)
    Traceback (most recent call last):
    PossibilityException: (B-5, G4, E4, C3) contains pitch names not found in pitchNamesToContain.
    >>> pitchNamesA2 = ['C', 'E', 'G', 'B-']
    >>> possibility.isIncomplete(possibA2, pitchNamesA2)
    False
    >>> possibility.isIncomplete(possibA1, pitchNamesA2)
    True
    ''' 
    isIncomplete = False
    pitchNamesContained = []
    for givenPitch in possibA:
        if givenPitch.name not in pitchNamesContained:
            pitchNamesContained.append(givenPitch.name)
    for pitchName in pitchNamesToContain:
        if pitchName not in pitchNamesContained:
            isIncomplete = True
    if not isIncomplete and (len(pitchNamesContained) > len(pitchNamesToContain)):
        raise PossibilityException(str(possibA) + " contains pitch names not found in pitchNamesToContain.")

    return isIncomplete

def upperPartsWithinLimit(possibA, maxSemitoneSeparation = 12):
    '''
    Returns True if the pitches in the upper parts of possibA
    are found within maxSemitoneSeparation of each other. The 
    upper parts of possibA are all the pitches except the last.
    
    The default value of maxSemitoneSeparation is 12 semitones,
    chromatically equivalent to a perfect octave. If this method
    returns True for this default value, then all the notes in 
    the upper parts can be played by most adult pianists using
    just the right hand. 
    
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = Pitch('C3')
    >>> E3 = Pitch('E3')
    >>> E4 = Pitch('E4')
    >>> G4 = Pitch('G4')
    >>> C5 = Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C3)
    >>> possibility.upperPartsWithinLimit(possibA1)
    True
    >>> possibA2 = (C5, G4, E3, C3)
    >>> possibility.upperPartsWithinLimit(possibA2)
    False
    '''
    upperPartsWithinLimit = True
    if maxSemitoneSeparation == None:
        return upperPartsWithinLimit
    
    upperParts = possibA[0:len(possibA)-1]
    for part1Index in range(len(upperParts)):
        higherPitch = upperParts[part1Index]
        for part2Index in range(part1Index + 1, len(upperParts)):
            lowerPitch = upperParts[part2Index]
            if abs(higherPitch.ps - lowerPitch.ps) > maxSemitoneSeparation:
                upperPartsWithinLimit = False
                return upperPartsWithinLimit
    
    return upperPartsWithinLimit

# CONSECUTIVE POSSIBILITY RULE-CHECKING METHODS
# ---------------------------------------------
#Speedup tables
parallelFifthsTable = {}
parallelOctavesTable = {}
hiddenFifthsTable = {}
hiddenOctavesTable = {}

def parallelFifths(possibA, possibB):
    '''
    Returns True if there are parallel fifths between any
    two shared parts of possibA and possibB.
 
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = Pitch('C3')
    >>> D3 = Pitch('D3')
    >>> G3 = Pitch('G3')
    >>> A3 = Pitch('A3')
    >>> possibA1 = (G3, C3)
    >>> possibB1 = (A3, D3)
    >>> possibility.parallelFifths(possibA1, possibB1)
    True
    '''
    hasParallelFifths = False
    pairsList = partPairs(possibA, possibB)
    
    for pair1Index in range(len(pairsList)):
        (higherPitchA, higherPitchB) = pairsList[pair1Index]
        for pair2Index in range(pair1Index +  1, len(pairsList)):
            (lowerPitchA, lowerPitchB) = pairsList[pair2Index]
            if not abs(higherPitchA.ps - lowerPitchA.ps) % 12 == 7:
                continue
            if not abs(higherPitchB.ps - lowerPitchB.ps) % 12 == 7:
                continue
            #Very high probability of ||5, but still not certain.
            pitchQuartet = (lowerPitchA, lowerPitchB, higherPitchA, higherPitchB)
            if parallelFifthsTable.has_key(pitchQuartet):
                hasParallelFifths = parallelFifthsTable[pitchQuartet]
                return hasParallelFifths
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.parallelFifth():
                hasParallelFifths = True
            parallelFifthsTable[pitchQuartet] = hasParallelFifths    
            return hasParallelFifths
    
    return hasParallelFifths
    
def parallelOctaves(possibA, possibB):
    '''
    Returns True if there are parallel octaves bewteen any two
    shared parts of possibA and possibB.
    
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = Pitch('C3')
    >>> D3 = Pitch('D3')
    >>> G3 = Pitch('G3')
    >>> A3 = Pitch('A3')
    >>> C4 = Pitch('C4')
    >>> D4 = Pitch('D4')
    >>> possibA1 = (G3, C3)
    >>> possibB1 = (A3, D3)
    >>> possibility.parallelOctaves(possibA1, possibB1)
    False
    >>> possibA2 = (C4, C3)
    >>> possibB2 = (D4, D3)
    >>> possibility.parallelOctaves(possibA2, possibB2)
    True
    '''
    hasParallelOctaves = False
    pairsList = partPairs(possibA, possibB)
    
    for pair1Index in range(len(pairsList)):
        (higherPitchA, higherPitchB) = pairsList[pair1Index]
        for pair2Index in range(pair1Index +  1, len(pairsList)):
            (lowerPitchA, lowerPitchB) = pairsList[pair2Index]
            if not abs(higherPitchA.ps - lowerPitchA.ps) % 12 == 0:
                continue
            if not abs(higherPitchB.ps - lowerPitchB.ps) % 12 == 0:
                continue
            #Very high probability of ||8, but still not certain.
            pitchQuartet = (lowerPitchA, lowerPitchB, higherPitchA, higherPitchB)
            if parallelOctavesTable.has_key(pitchQuartet):
                hasParallelOctaves = parallelOctavesTable[pitchQuartet]
                return hasParallelOctaves
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.parallelOctave():
                hasParallelOctaves = True
            parallelOctavesTable[pitchQuartet] = hasParallelOctaves
            return hasParallelOctaves
    
    return hasParallelOctaves

def hiddenFifth(possibA, possibB):
    '''
    Returns True if there is a hidden fifth between shared outer parts
    of possibA and possibB. The outer parts are the first and last
    elements of each possibility.
    
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = Pitch('C3')
    >>> D3 = Pitch('D3')
    >>> E5 = Pitch('E5')
    >>> A5 = Pitch('A5')
    >>> Ab5 = Pitch('A-5')
    >>> possibA1 = (E5, C3)
    >>> possibB1 = (A5, D3)
    >>> possibility.hiddenFifth(possibA1, possibB1)
    True
    >>> possibB2 = (Ab5, D3)
    >>> possibility.hiddenFifth(possibA1, possibB2)
    False
    '''
    hasHiddenFifth = False
    pairsList = partPairs(possibA, possibB)
    (highestPitchA, highestPitchB) = pairsList[0]
    (lowestPitchA, lowestPitchB) = pairsList[-1]

    if abs(highestPitchB.ps - lowestPitchB.ps) % 12 == 7:
        #Very high probability of hidden fifth, but still not certain.
        pitchQuartet = (lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
        if hiddenFifthsTable.has_key(pitchQuartet):
            hasHiddenFifth = hiddenFifthsTable[pitchQuartet]
            return hasHiddenFifth
        vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
        if vlq.hiddenFifth():
            hasHiddenFifth = True
        hiddenFifthsTable[pitchQuartet] = hasHiddenFifth
        
    return hasHiddenFifth

def hiddenOctave(possibA, possibB):
    '''
    Returns True if there is a hidden octave between shared outer 
    parts of possibA and possibB. The outer parts are the first 
    and last elements of each possibility.

    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = Pitch('C3')
    >>> D3 = Pitch('D3')
    >>> A5 = Pitch('A5')
    >>> D6 = Pitch('D6')
    >>> possibA1 = (A5, C3)
    >>> possibB1 = (D6, D3)
    >>> possibility.hiddenOctave(possibA1, possibB1)
    True
    '''
    hasHiddenOctave = False
    pairsList = partPairs(possibA, possibB)
    (highestPitchA, highestPitchB) = pairsList[0]
    (lowestPitchA, lowestPitchB) = pairsList[-1]

    if abs(highestPitchB.ps - lowestPitchB.ps) % 12 == 0:
        #Very high probability of hidden octave, but still not certain.
        pitchQuartet = (lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
        if hiddenOctavesTable.has_key(pitchQuartet):
            hasHiddenOctave = hiddenOctavesTable[pitchQuartet]
            return hasHiddenOctave
        vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
        if vlq.hiddenOctave():
            hasHiddenOctave = True
        hiddenOctavesTable[pitchQuartet] = hasHiddenOctave
    
    return hasHiddenOctave

def voiceOverlap(possibA, possibB):
    '''
    Returns True if there is voice overlap between any two shared parts
    of possibA and possibB.
    
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = Pitch('C4')
    >>> D4 = Pitch('D4')
    >>> E4 = Pitch('E4')
    >>> F4 = Pitch('F4')
    >>> G4 = Pitch('G4')
    >>> B4 = Pitch('B4')
    >>> C5 = Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, F4, D4, D4)
    >>> possibility.voiceOverlap(possibA1, possibB1)
    False
    >>> possibB2 = (F4, F4, D4, D4)
    >>> possibility.voiceOverlap(possibA1, possibB2)
    True
    >>> possibility.voiceCrossing(possibA1)
    False
    >>> possibility.voiceCrossing(possibB2)
    False
    '''
    hasVoiceOverlap = False
    pairsList = partPairs(possibA, possibB)
    
    for pair1Index in range(len(pairsList)):
        (higherPitchA, higherPitchB) = pairsList[pair1Index]
        for pair2Index in range(pair1Index +  1, len(pairsList)):
            (lowerPitchA, lowerPitchB) = pairsList[pair2Index]
            if lowerPitchB > higherPitchA or higherPitchB < lowerPitchA:
                hasVoiceOverlap = True
                return hasVoiceOverlap
            
    return hasVoiceOverlap

def partMovementsWithinLimits(possibA, possibB, partMovementLimits = []):
    '''
    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = Pitch('C4')
    >>> D4 = Pitch('D4')
    >>> E4 = Pitch('E4')
    >>> F4 = Pitch('F4')
    >>> G4 = Pitch('G4')
    >>> A4 = Pitch('A4')
    >>> B4 = Pitch('B4')
    >>> C5 = Pitch('C5')
    >>> partMovementLimits = [(1, 2)]
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, F4, D4, D4)
    >>> possibility.partMovementsWithinLimits(possibA1, possibB1, partMovementLimits)
    True
    >>> possibB2 = (A4, F4, D4, D4)
    >>> possibility.partMovementsWithinLimits(possibA1, possibB2, partMovementLimits)
    False
    '''
    withinLimits = True
    for (partNumber, maxSeparation) in partMovementLimits:
        pitchA = possibA[partNumber - 1]
        pitchB = possibB[partNumber - 1]
        if abs(pitchB.ps - pitchA.ps) > maxSeparation:
            withinLimits = False
            return withinLimits

    return withinLimits
    
# HELPER METHODS
# --------------
def partPairs(possibA, possibB):
    '''
    Groups together pitches of possibA and possibB which correspond to the same part.

    >>> from music21.pitch import Pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = Pitch('C4')
    >>> D4 = Pitch('D4')
    >>> E4 = Pitch('E4')
    >>> F4 = Pitch('F4')
    >>> G4 = Pitch('G4')
    >>> B4 = Pitch('B4')
    >>> C5 = Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, F4, D4, D4)
    >>> possibility.partPairs(possibA1, possibA1)
    [(C5, C5), (G4, G4), (E4, E4), (C4, C4)]
    >>> possibility.partPairs(possibA1, possibB1)
    [(C5, B4), (G4, F4), (E4, D4), (C4, D4)]
    '''
    return list(itertools.izip(possibA, possibB))


class PossibilityException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof