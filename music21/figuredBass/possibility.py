# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         possibility.py
# Purpose:      music21 class to define rule checking methods for a possibility
#                represented as a tuple.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
A possibility is a tuple with pitches, and is intended to encapsulate a possible
solution to a :class:`~music21.figuredBass.segment.Segment`. Unlike a :class:`~music21.chord.Chord`,
the ordering of a possibility does matter. The assumption throughout fbRealizer 
is that a possibility is always in order from highest part to lowest part, and 
the last element of each possibility is the bass.


.. note:: fbRealizer supports voice crossing, so the order of pitches from lowest
    to highest may not correspond to the ordering of parts.


Here, a possibility is created. G5 is in the highest part, and C4 is the bass. The highest
part contains the highest Pitch, and the lowest part contains the lowest Pitch. No voice
crossing is present.


>>> from music21 import pitch
>>> G5 = pitch.Pitch('G5')
>>> C5 = pitch.Pitch('C5')
>>> E4 = pitch.Pitch('E4')
>>> C4 = pitch.Pitch('C4')
>>> p1 = (G5, C5, E4, C4)


Here, another possibility is created with the same pitches, but this time, with voice crossing present.
C5 is in the highest part, but the highest Pitch G5 is in the second highest part.


>>> p2 = (C5, G5, E4, C4) 


The methods in this module are applied to possibilities, and fall into three main categories:


1) Single Possibility Methods. These methods are applied in finding correct possibilities in
:meth:`~music21.figuredBass.segment.Segment.allCorrectSinglePossibilities`.


2) Consecutive Possibility Methods. These methods are applied to (possibA, possibB) pairs
in :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`,
possibA being any correct possibility in segmentA and possibB being any correct possibility
in segmentB.


3) Special Resolution Methods. These methods are applied in :meth:`~music21.figuredBass.segment.Segment.allCorrectConsecutivePossibilities`
as applicable if the pitch names of a Segment correctly spell out an augmented sixth, dominant
seventh, or diminished seventh chord. They are located in :mod:`~music21.figuredBass.resolution`.


The application of these methods is controlled by corresponding instance variables in a 
:class:`~music21.figuredBass.rules.Rules` object provided to a Segment.



.. note:: The number of parts and maxPitch are universal for a :class:`~music21.figuredBass.realizer.FiguredBassLine`.
'''
import unittest

from music21 import chord
from music21 import exceptions21
from music21 import interval
from music21 import pitch
from music21 import voiceLeading
from music21.ext import six

izip = six.moves.zip # @UndefinedVariable

# SINGLE POSSIBILITY RULE-CHECKING METHODS
# ----------------------------------------
def voiceCrossing(possibA):
    '''
    Returns True if there is voice crossing present between any two parts
    in possibA. The parts from lowest part to highest part (right to left)
    must correspond to increasingly higher pitches in order for there to 
    be no voice crossing. Comparisons between pitches are done using pitch
    comparison methods, which are based on pitch space values 
    (see :class:`~music21.pitch.Pitch`).
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = pitch.Pitch('C4')
    >>> E4 = pitch.Pitch('E4')
    >>> C5 = pitch.Pitch('C5')
    >>> G5 = pitch.Pitch('G5')
    >>> possibA1 = (C5, G5, E4)
    >>> possibility.voiceCrossing(possibA1) # G5 > C5
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
    For a Segment, pitchNamesToContain is :attr:`~music21.figuredBass.segment.Segment.pitchNamesInChord`.
    
    
    If possibA contains excessive pitch names, a PossibilityException is
    raised, although this is not a concern with the current implementation 
    of fbRealizer.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = pitch.Pitch('C3')
    >>> E4 = pitch.Pitch('E4')
    >>> G4 = pitch.Pitch('G4')
    >>> C5 = pitch.Pitch('C5')
    >>> Bb5 = pitch.Pitch('B-5')
    >>> possibA1 = (C5, G4, E4, C3)
    >>> pitchNamesA1 = ['C', 'E', 'G', 'B-']
    >>> possibility.isIncomplete(possibA1, pitchNamesA1) # Missing B-
    True
    >>> pitchNamesA2 = ['C', 'E', 'G']
    >>> possibility.isIncomplete(possibA1, pitchNamesA2)
    False
    ''' 
    isIncompleteV = False
    pitchNamesContained = []
    for givenPitch in possibA:
        if givenPitch.name not in pitchNamesContained:
            pitchNamesContained.append(givenPitch.name)
    for pitchName in pitchNamesToContain:
        if pitchName not in pitchNamesContained:
            isIncompleteV = True
    if not isIncompleteV and (len(pitchNamesContained) > len(pitchNamesToContain)):
        isIncompleteV = False
        #raise PossibilityException(str(possibA) + " contains pitch names not found in pitchNamesToContain.")

    return isIncompleteV

def upperPartsWithinLimit(possibA, maxSemitoneSeparation = 12):
    '''
    Returns True if the pitches in the upper parts of possibA
    are found within maxSemitoneSeparation of each other. The 
    upper parts of possibA are all the pitches except the last.
    
    The default value of maxSemitoneSeparation is 12 semitones,
    enharmonically equivalent to a perfect octave. If this method
    returns True for this default value, then all the notes in 
    the upper parts can be played by most adult pianists using
    just the right hand. 
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = pitch.Pitch('C3')
    >>> E3 = pitch.Pitch('E3')
    >>> E4 = pitch.Pitch('E4')
    >>> G4 = pitch.Pitch('G4')
    >>> C5 = pitch.Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C3)
    >>> possibility.upperPartsWithinLimit(possibA1)
    True
    

    Here, C5 and E3 are separated by almost two octaves.
    
    
    >>> possibA2 = (C5, G4, E3, C3)
    >>> possibility.upperPartsWithinLimit(possibA2)
    False
    '''
    upperPartsWithinLimit = True # pylint: disable=redefined-outer-name
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

def pitchesWithinLimit(possibA, maxPitch = pitch.Pitch('B5')):
    '''
    Returns True if all pitches in possibA are less than or equal to
    the maxPitch provided. Comparisons between pitches are done using pitch
    comparison methods, which are based on pitch space values 
    (see :class:`~music21.pitch.Pitch`).
    
    
    Used in :class:`~music21.figuredBass.segment.Segment` to filter
    resolutions of special Segments which can have pitches exceeeding
    the universal maxPitch of a :class:`~music21.figuredBass.realizer.FiguredBassLine`.
    
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21 import pitch
    >>> G2 = pitch.Pitch('G2')
    >>> D4 = pitch.Pitch('D4')
    >>> F5 = pitch.Pitch('F5')
    >>> B5 = pitch.Pitch('B5')
    >>> domPossib = (B5, F5, D4, G2)
    >>> possibility.pitchesWithinLimit(domPossib)
    True
    >>> resPossib = resolution.dominantSeventhToMajorTonic(domPossib)
    >>> resPossib # Contains C6 > B5
    (<music21.pitch.Pitch C6>, <music21.pitch.Pitch E5>, <music21.pitch.Pitch C4>, <music21.pitch.Pitch C3>)
    >>> possibility.pitchesWithinLimit(resPossib)
    False 
    '''
    for givenPitch in possibA:
        if givenPitch > maxPitch:
            return False
        
    return True

def limitPartToPitch(possibA, partPitchLimits=None):
    '''
    Takes in a dict, partPitchLimits containing (partNumber, partPitch) pairs, each
    of which limits a part in possibA to a certain :class:`~music21.pitch.Pitch`.
    Returns True if all limits are followed in possibA, False otherwise.
    
    >>> from music21.figuredBass import possibility
    >>> from music21 import pitch
    >>> C4 = pitch.Pitch('C4')
    >>> E4 = pitch.Pitch('E4')
    >>> G4 = pitch.Pitch('G4')
    >>> C5 = pitch.Pitch('C5')
    >>> G5 = pitch.Pitch('G5')
    >>> sopranoPitch = pitch.Pitch('G5')
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibility.limitPartToPitch(possibA1, {1: sopranoPitch})
    False
    >>> possibA2 = (G5, G4, E4, C4)
    >>> possibility.limitPartToPitch(possibA2, {1: sopranoPitch})
    True
    '''
    if partPitchLimits is None:
        partPitchLimits = {}
    for (partNumber, partPitch) in partPitchLimits.items():
        if not (possibA[partNumber - 1] == partPitch):
            return False

    return True


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
 
 
    If pitchA1 and pitchA2 in possibA are separated by
    a simple interval of a perfect fifth, and they move
    to a pitchB1 and pitchB2 in possibB also separated
    by the simple interval of a perfect fifth, then this
    constitutes parallel fifths between these two parts.
 

    If the method returns False, then no two shared parts
    have parallel fifths. The method returns True as soon
    as two shared parts with parallel fifths are found.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = pitch.Pitch('C3')
    >>> D3 = pitch.Pitch('D3')
    >>> G3 = pitch.Pitch('G3')
    >>> A3 = pitch.Pitch('A3')
    >>> A4 = pitch.Pitch('A4')
    >>> B4 = pitch.Pitch('B4')
    
    
    Here, the bass moves from C3 to D3 and the tenor moves 
    from G3 to A3. The interval between C3 and G3, as well 
    as between D3 and A3, is a perfect fifth. These two
    parts, and therefore the two possibilities, have 
    parallel fifths.
        
    
    >>> possibA1 = (B4, G3, C3)
    >>> possibB1 = (A4, A3, D3)
    >>> possibility.parallelFifths(possibA1, possibB1)
    True


    
    Now, the tenor moves instead to F3. The interval between
    D3 and F3 is a minor third. The bass and tenor parts 
    don't form parallel fifths. The soprano part forms parallel
    fifths with neither the bass nor tenor parts. The
    two possibilities, therefore, have no parallel fifths.
    
    
    >>> F3 = pitch.Pitch('F3')
    >>> possibA2 = (B4, G3, C3)
    >>> possibB2 = (A4, F3, D3)
    >>> possibility.parallelFifths(possibA2, possibB2)
    False
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
            if pitchQuartet in parallelFifthsTable:
                hasParallelFifths = parallelFifthsTable[pitchQuartet]
                if hasParallelFifths:
                    return hasParallelFifths
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.parallelFifth():
                hasParallelFifths = True
            parallelFifthsTable[pitchQuartet] = hasParallelFifths
            if hasParallelFifths: 
                return hasParallelFifths
    
    return hasParallelFifths
    
def parallelOctaves(possibA, possibB):
    '''
    Returns True if there are parallel octaves between any
    two shared parts of possibA and possibB.
 
 
    If pitchA1 and pitchA2 in possibA are separated by
    a simple interval of a perfect octave, and they move
    to a pitchB1 and pitchB2 in possibB also separated
    by the simple interval of a perfect octave, then this
    constitutes parallel octaves between these two parts.
 

    If the method returns False, then no two shared parts
    have parallel octaves. The method returns True as soon
    as two shared parts with parallel octaves are found.

    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = pitch.Pitch('C3')
    >>> D3 = pitch.Pitch('D3')
    >>> G3 = pitch.Pitch('G3')
    >>> A3 = pitch.Pitch('A3')
    >>> C4 = pitch.Pitch('C4')
    >>> D4 = pitch.Pitch('D4')
    

    Here, the soprano moves from C4 to D4 and the bass moves
    from C3 to D3. The interval between C3 and C4, as well as
    between D3 and D4, is a parallel octave. The two parts,
    and therefore the two possibilities, have parallel octaves.
    
    
    >>> possibA1 = (C4, G3, C3)
    >>> possibB1 = (D4, A3, D3)
    >>> possibility.parallelOctaves(possibA1, possibB1)
    True


    Now, the soprano moves down to B3. The interval between
    D3 and B3 is a major sixth. The soprano and bass parts 
    no longer have parallel octaves. The tenor part forms
    a parallel octave with neither the bass nor soprano,
    so the two possibilities do not have parallel octaves.
    (Notice, however, the parallel fifth between the bass
    and tenor!)
     
     
    >>> B3 = pitch.Pitch('B3')
    >>> possibA2 = (C4, G3, C3)
    >>> possibB2 = (B3, A3, D3)
    >>> possibility.parallelOctaves(possibA2, possibB2)
    False
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
            if pitchQuartet in parallelOctavesTable:
                hasParallelOctaves = parallelOctavesTable[pitchQuartet]
                if hasParallelOctaves:
                    return hasParallelOctaves
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.parallelOctave():
                hasParallelOctaves = True
            parallelOctavesTable[pitchQuartet] = hasParallelOctaves
            if hasParallelOctaves:
                return hasParallelOctaves
    
    return hasParallelOctaves

def hiddenFifth(possibA, possibB):
    '''
    Returns True if there is a hidden fifth between shared outer parts
    of possibA and possibB. The outer parts here are the first and last
    elements of each possibility.
    
    
    If sopranoPitchA and bassPitchA in possibA move to a sopranoPitchB
    and bassPitchB in possibB in similar motion, and the simple interval 
    between sopranoPitchB and bassPitchB is that of a perfect fifth, 
    then this constitutes a hidden octave between the two possibilities.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = pitch.Pitch('C3')
    >>> D3 = pitch.Pitch('D3')
    >>> E3 = pitch.Pitch('E3')
    >>> F3 = pitch.Pitch('F3')
    >>> E5 = pitch.Pitch('E5')
    >>> A5 = pitch.Pitch('A5')
    
    
    Here, the bass part moves up from C3 to D3 and the soprano part moves
    up from E5 to A5. The simple interval between D3 and A5 is a perfect
    fifth. Therefore, there is a hidden fifth between the two possibilities.
    
    
    >>> possibA1 = (E5, E3, C3)
    >>> possibB1 = (A5, F3, D3)
    >>> possibility.hiddenFifth(possibA1, possibB1)
    True
    
    
    Here, the soprano and bass parts also move in similar motion, but the 
    simple interval between D3 and Ab5 is a diminished fifth. Consequently, 
    there is no hidden fifth.
    

    >>> Ab5 = pitch.Pitch('A-5')   
    >>> possibA2 = (E5, E3, C3)
    >>> possibB2 = (Ab5, F3, D3)
    >>> possibility.hiddenFifth(possibA2, possibB2)
    False
    
    
    Now, we have the soprano and bass parts again moving to A5 and D3, whose 
    simple interval is a perfect fifth. However, the bass moves up while the 
    soprano moves down. Therefore, there is no hidden fifth.
    
    
    >>> E6 = pitch.Pitch('E6')
    >>> possibA3 = (E6, E3, C3)
    >>> possibB3 = (A5, F3, D3)
    >>> possibility.hiddenFifth(possibA3, possibB3)
    False
    '''
    hasHiddenFifth = False
    pairsList = partPairs(possibA, possibB)
    (highestPitchA, highestPitchB) = pairsList[0]
    (lowestPitchA, lowestPitchB) = pairsList[-1]

    if abs(highestPitchB.ps - lowestPitchB.ps) % 12 == 7:
        #Very high probability of hidden fifth, but still not certain.
        pitchQuartet = (lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
        if pitchQuartet in hiddenFifthsTable:
            hasHiddenFifth = hiddenFifthsTable[pitchQuartet]
            return hasHiddenFifth
        vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
        if vlq.hiddenFifth():
            hasHiddenFifth = True
        hiddenFifthsTable[pitchQuartet] = hasHiddenFifth
        
    return hasHiddenFifth

def hiddenOctave(possibA, possibB):
    '''
    Returns True if there is a hidden octave between shared outer parts
    of possibA and possibB. The outer parts here are the first and last
    elements of each possibility.
    
    
    If sopranoPitchA and bassPitchA in possibA move to a sopranoPitchB
    and bassPitchB in possibB in similar motion, and the simple interval 
    between sopranoPitchB and bassPitchB is that of a perfect octave, 
    then this constitutes a hidden octave between the two possibilities.

    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C3 = pitch.Pitch('C3')
    >>> D3 = pitch.Pitch('D3')
    >>> E3 = pitch.Pitch('E3')
    >>> F3 = pitch.Pitch('F3')
    >>> A5 = pitch.Pitch('A5')
    >>> D6 = pitch.Pitch('D6')
    

    Here, the bass part moves up from C3 to D3 and the soprano part moves
    up from A5 to D6. The simple interval between D3 and D6 is a perfect 
    octave. Therefore, there is a hidden octave between the two possibilities.
    
    
    >>> possibA1 = (A5, E3, C3)
    >>> possibB1 = (D6, F3, D3) #Perfect octave between soprano and bass.
    >>> possibility.hiddenOctave(possibA1, possibB1)
    True
    
    
    Here, the bass part moves up from C3 to D3 but the soprano part moves
    down from A6 to D6. There is no hidden octave since the parts move in
    contrary motion. 
    
    
    >>> A6 = pitch.Pitch('A6')
    >>> possibA2 = (A6, E3, C3)
    >>> possibB2 = (D6, F3, D3)
    >>> possibility.hiddenOctave(possibA2, possibB2)
    False
    '''
    hasHiddenOctave = False
    pairsList = partPairs(possibA, possibB)
    (highestPitchA, highestPitchB) = pairsList[0]
    (lowestPitchA, lowestPitchB) = pairsList[-1]

    if abs(highestPitchB.ps - lowestPitchB.ps) % 12 == 0:
        #Very high probability of hidden octave, but still not certain.
        pitchQuartet = (lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
        if pitchQuartet in hiddenOctavesTable:
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
    
    
    Voice overlap can occur in two ways:
    
    
    1) If a pitch in a lower part in possibB is higher than a pitch in
    a higher part in possibA. This case is demonstrated below.
    
    
    2) If a pitch in a higher part in possibB is lower than a pitch in
    a lower part in possibA. 


        .. image:: images/figuredBass/fbPossib_voiceOverlap.*
            :width: 75

    
    In the above example, possibA has G4 in the bass and B4 in the soprano.
    If the bass moves up to C5 in possibB, that would constitute voice overlap
    because the bass in possibB would be higher than the soprano in possibA.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = pitch.Pitch('C4')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> C5 = pitch.Pitch('C5')
    
    
    Here, case #2 is demonstrated. There is overlap between the soprano and 
    alto parts, because F4 in the soprano in possibB1 is lower than the G4
    in the alto in possibA1. Note that neither possibility has to have voice
    crossing for voice overlap to occur, as shown.
    
    
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (F4, F4, D4, D4)
    >>> possibility.voiceOverlap(possibA1, possibB1)
    True
    >>> possibility.voiceCrossing(possibA1)
    False
    >>> possibility.voiceCrossing(possibB1)
    False
    
    
    Here is the same example as above, except the soprano of the second
    possibility is now B4, which does not overlap the G4 of the first.
    Now, there is no voice overlap.
    
    
    >>> B4 = pitch.Pitch('B4')   
    >>> possibA2 = (C5, G4, E4, C4)
    >>> possibB2 = (B4, F4, D4, D4)
    >>> possibility.voiceOverlap(possibA2, possibB2)   
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

def partMovementsWithinLimits(possibA, possibB, partMovementLimits=None):
    '''
    Returns True if all movements between shared parts of possibA and possibB
    are within limits, as specified by list partMovementLimits, which consists of
    (partNumber, maxSeparation) tuples. 
    
    
    * partNumber: Specified from 1 to n, where 1 is the soprano or highest part and n is the bass or lowest part.
    
    
    * maxSeparation: For a given part, the maximum separation to allow between a pitch in possibA and a corresponding pitch in possibB, in semitones.  
    
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = pitch.Pitch('C4')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> A4 = pitch.Pitch('A4')
    >>> B4 = pitch.Pitch('B4')
    >>> C5 = pitch.Pitch('C5')
    
    
    Here, we limit the soprano part to motion of two semitones, enharmonically equivalent to a major second. 
    Moving from C5 to B4 is allowed because it constitutes stepwise motion, but moving to A4 is not allowed 
    because the distance between A4 and C5 is three semitones.
    
    
    >>> partMovementLimits = [(1, 2)]
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, F4, D4, D4)
    >>> possibility.partMovementsWithinLimits(possibA1, possibB1, partMovementLimits)
    True
    >>> possibB2 = (A4, F4, D4, D4)
    >>> possibility.partMovementsWithinLimits(possibA1, possibB2, partMovementLimits)
    False
    '''
    if partMovementLimits is None:
        partMovementLimits = []
    withinLimits = True
    for (partNumber, maxSeparation) in partMovementLimits:
        pitchA = possibA[partNumber - 1]
        pitchB = possibB[partNumber - 1]
        if abs(pitchB.ps - pitchA.ps) > maxSeparation:
            withinLimits = False
            return withinLimits

    return withinLimits

def upperPartsSame(possibA, possibB):
    '''
    Returns True if the upper parts are the same.
    False otherwise.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = pitch.Pitch('C4')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> B4 = pitch.Pitch('B4')
    >>> C5 = pitch.Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, F4, D4, D4)
    >>> possibB2 = (C5, G4, E4, D4)
    >>> possibility.upperPartsSame(possibA1, possibB1)
    False
    >>> possibility.upperPartsSame(possibA1, possibB2)
    True
    '''
    pairsList = partPairs(possibA, possibB)
    
    for (pitchA, pitchB) in pairsList[0:-1]:
        if not (pitchA == pitchB):
            return False
        
    return True

def partsSame(possibA, possibB, partsToCheck = None):
    '''
    Takes in partsToCheck, a list of part numbers. Checks if pitches at those part numbers of
    possibA and possibB are equal, determined by pitch space.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = pitch.Pitch('C4')
    >>> E4 = pitch.Pitch('E4')
    >>> G4 = pitch.Pitch('G4')
    >>> B4 = pitch.Pitch('B4')
    >>> C5 = pitch.Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, G4, E4, C4)
    >>> possibility.partsSame(possibA1, possibB1, [2,3,4])
    True
    '''
    if partsToCheck == None:
        return True
    
    pairsList = partPairs(possibA, possibB)
    
    for partIndex in partsToCheck:
        (pitchA, pitchB) = pairsList[partIndex - 1]
        if not (pitchA == pitchB):
            return False
    
    return True

def couldBeItalianA6Resolution(possibA, possibB, threePartChordInfo = None, restrictDoublings = True):
    '''
    Speed-enhanced but designed to stand alone. Returns True if possibA is an Italian A6 chord 
    and possibB could possibly be an acceptable resolution. If restrictDoublings is set to True,
    only the tonic can be doubled. Setting restrictDoublings to False opens up the chance
    that the root or the third can be doubled. Controlled in the :class:`~music21.figuredBass.rules.Rules`
    object by :attr:`~music21.figuredBass.rules.Rules.restrictDoublingsInItalianA6Resolution`.    
    
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> A2 = pitch.Pitch('A2')
    >>> Bb2 = pitch.Pitch('B-2')
    >>> Cs4 = pitch.Pitch('C#4')    
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> Fs4 = pitch.Pitch('F#4')
    >>> Gs4 = pitch.Pitch('G#4')
    >>> A4 = pitch.Pitch('A4')
    >>> possibA1 = (Gs4, D4, D4, Bb2)
    >>> possibB1 = (A4, Cs4, E4, A2)
    >>> possibB2 = (A4, E4, Cs4, A2)
    >>> possibB3 = (A4, D4, Fs4, A2)
    >>> possibility.couldBeItalianA6Resolution(possibA1, possibB1)
    True
    >>> possibility.couldBeItalianA6Resolution(possibA1, possibB1)
    True
    >>> possibility.couldBeItalianA6Resolution(possibA1, possibB3)
    True


    A PossibilityException is raised if possibA is not an Italian A6 chord, but this only
    applies only if threePartChordInfo = None, because otherwise the chord information is 
    coming from :class:`~music21.figuredBass.segment.Segment` and the fact that possibA is 
    an It+6 chord is assumed.
    
    
    >>> possibA2 = (Gs4, E4, D4, Bb2)
    >>> possibB2 = (A4, E4, Cs4, A2)
    >>> possibility.couldBeItalianA6Resolution(possibA2, possibB2)
    Traceback (most recent call last):
    PossibilityException: possibA does not spell out an It+6 chord.
    
    
    The method is called "couldBeItalianA6Resolution" as opposed
    to "isItalianA6Resolution" because it is designed to work in
    tandem with :meth:`~music21.figuredBass.possibility.parallelOctaves`
    and :meth:`~music21.figuredBass.possibility.isIncomplete` in
    a Segment. Consider the following examples with possibA1 above as the
    augmented sixth chord to resolve.
    
    
    >>> possibA1 = (Gs4, D4, D4, Bb2)
    >>> possibB4 = (A4, D4, D4, A2) # No 3rd
    >>> possibB5 = (A4, Cs4, Cs4, A2) # No 5th
    >>> possibility.couldBeItalianA6Resolution(possibA1, possibB4)
    True
    >>> possibility.couldBeItalianA6Resolution(possibA1, possibB5)  # parallel octaves
    True
    
    
    >>> possibA3 = (Gs4, Gs4, D4, Bb2)
    >>> possibB6 = (A4, A4, Cs4, A2)
    >>> possibility.couldBeItalianA6Resolution(possibA3, possibB6, restrictDoublings = True)
    False
    >>> possibility.couldBeItalianA6Resolution(possibA3, possibB6, restrictDoublings = False)
    True
    '''
    if threePartChordInfo == None:
        augSixthChord = chord.Chord(possibA)
        if not augSixthChord.isItalianAugmentedSixth():
            raise PossibilityException("possibA does not spell out an It+6 chord.")
        bass = augSixthChord.bass()
        root = augSixthChord.root()
        third = augSixthChord.getChordStep(3)
        fifth = augSixthChord.getChordStep(5)
        threePartChordInfo = [bass, root, third, fifth]
            
    allowedIntervalNames = ['M3','m3','M2','m-2']
    rootResolved = False
    [bass, root, third, fifth] = threePartChordInfo
    for pitchIndex in range(len(possibA)):
        pitchA = possibA[pitchIndex]
        pitchB = possibB[pitchIndex]
        if pitchA.name == fifth.name:
            if pitchA == pitchB:
                continue
            if abs(pitchA.ps - pitchB.ps) > 4.0:
                return False
            tt = interval.Interval(pitchA, pitchB)
            if not tt.directedSimpleName in allowedIntervalNames:
                return False
        elif pitchA.name == bass.name and pitchA == bass:
            if not (pitchA.ps - pitchB.ps) == 1.0:
                return False
            i = interval.Interval(pitchA, pitchB)
            if not i.directedName == 'm-2':
                return False
        elif pitchA.name == root.name:
            if rootResolved == True and restrictDoublings:
                # there can't be more than one root
                return False
            if not (pitchB.ps - pitchA.ps) == 1.0:
                return False
            i = interval.Interval(pitchA, pitchB)
            if not i.directedName == 'm2':
                return False
            rootResolved = True
        elif pitchA.name == third.name:
            if restrictDoublings:
                # there can't be more than one third, which is in the bass.
                return False
            if not (pitchA.ps - pitchB.ps) == 1.0:
                return False
            i = interval.Interval(pitchA, pitchB)
            if not i.directedName == 'm-2':
                return False

#     # Part 1: Check if possibA is A6 chord, and if it is properly formed.
#     bass = possibA[-1]
#     root = None
#     rootIndex = 0
#     for pitchA in possibA[0:-1]:
#         if not (pitchA.ps - bass.ps) % 12 == 10:
#             rootIndex += 1
#             continue
#         br = interval.Interval(bass, pitchA)
#         isAugmentedSixth = (br.directedSimpleName == 'A6')
#         if isAugmentedSixth:
#             root = pitchA
#             break
#     tonic = bass.transpose('M3')
#     #Restrict doublings, It+6
#     for pitchIndex in range(len(possibA) - 1):
#         if pitchIndex == rootIndex:
#             continue
#         pitchA = possibA[pitchIndex]
#         if not pitchA.name == tonic.name:
#             return False
# 
#     #Part 2: If possibA is Italian A6 chord, check that it resolves properly in possibB.
#     fifth = root.transpose('m2')
#     pairsList = partPairs(possibA, possibB)
#     (bassA, bassB) = pairsList[-1]
#     (rootA, rootB) = pairsList[rootIndex]
#     if not (bassB.name == fifth.name and rootB.name == fifth.name):
#         return False
#     if not (bassB.ps - bassA.ps == -1.0 and rootB.ps - rootA.ps == 1.0):
#         return False
#     allowedIntervalNames = ['M3','m3','M2','m-2']
#     for pitchIndex in range(len(pairsList) - 1):
#         if pitchIndex == rootIndex:
#             continue
#         (tonicA, tonicB) = pairsList[pitchIndex]
#         if tonicA == tonicB:
#             continue
#         tt = interval.Interval(tonicA, tonicB)
#         if not tt.directedSimpleName in allowedIntervalNames:
#             return False
    
    return True

# HELPER METHODS
# --------------
def partPairs(possibA, possibB):
    '''
    Groups together pitches of possibA and possibB which correspond to the same part,
    constituting a shared part.

    >>> from music21 import pitch
    >>> from music21.figuredBass import possibility
    >>> C4 = pitch.Pitch('C4')
    >>> D4 = pitch.Pitch('D4')
    >>> E4 = pitch.Pitch('E4')
    >>> F4 = pitch.Pitch('F4')
    >>> G4 = pitch.Pitch('G4')
    >>> B4 = pitch.Pitch('B4')
    >>> C5 = pitch.Pitch('C5')
    >>> possibA1 = (C5, G4, E4, C4)
    >>> possibB1 = (B4, F4, D4, D4)
    >>> possibility.partPairs(possibA1, possibA1)
    [(<music21.pitch.Pitch C5>, <music21.pitch.Pitch C5>), 
     (<music21.pitch.Pitch G4>, <music21.pitch.Pitch G4>), 
     (<music21.pitch.Pitch E4>, <music21.pitch.Pitch E4>), 
     (<music21.pitch.Pitch C4>, <music21.pitch.Pitch C4>)]
    >>> possibility.partPairs(possibA1, possibB1)
    [(<music21.pitch.Pitch C5>, <music21.pitch.Pitch B4>), 
     (<music21.pitch.Pitch G4>, <music21.pitch.Pitch F4>), 
     (<music21.pitch.Pitch E4>, <music21.pitch.Pitch D4>), 
     (<music21.pitch.Pitch C4>, <music21.pitch.Pitch D4>)]

    '''
    return list(izip(possibA, possibB))

# apply a function to one pitch of possibA at a time
# apply a function to two pitches of possibA at a time
# apply a function to one partPair of possibA, possibB at a time
# apply a function to two partPairs of possibA, possibB at a time
# use an iterator that fails when the first false is returned




singlePossibilityMethods = [voiceCrossing, isIncomplete, upperPartsWithinLimit, pitchesWithinLimit]
#singlePossibilityMethods.sort(None, lambda x: x.__name__)
consequentPossibilityMethods = [parallelFifths, parallelOctaves, hiddenFifth, hiddenOctave, voiceOverlap, 
                                  partMovementsWithinLimits, upperPartsSame, couldBeItalianA6Resolution]
#consequentPossibilityMethods.sort(None, lambda x: x.__name__)

_DOC_ORDER = singlePossibilityMethods + [partPairs] + consequentPossibilityMethods


class PossibilityException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
