# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         checker.py
# Purpose:      music21 class which can parse a stream of parts and check your homework
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import collections
import copy
import unittest

from music21 import stream
from music21 import voiceLeading
from music21.common import opFrac
from music21.figuredBass import possibility

#-------------------------------------------------------------------------------
# Parsing scores into voice leading momemnts (a.k.a. harmonies) 

def getVoiceLeadingMoments(music21Stream):
    '''
    Takes in a :class:`~music21.stream.Stream` and returns a :class:`~music21.stream.Score`
    of the :class:`~music21.stream.Stream` broken up into its voice leading moments.
    
    >>> #_DOCS_SHOW score = corpus.parse("corelli/opus3no1/1grave").measures(1,3)
    >>> #_DOCS_SHOW score.show()
    
    .. image:: images/figuredBass/corelli_grave.*
            :width: 700


    >>> from music21.figuredBass import checker
    >>> score = corpus.parse('bwv66.6') #_DOCS_HIDE
    >>> vlMoments = checker.getVoiceLeadingMoments(score)
    >>> #_DOCS_SHOW vlMoments.show()

    .. image:: images/figuredBass/corelli_vlm.*
            :width: 700
    '''
    allHarmonies = extractHarmonies(music21Stream)
    allParts = music21Stream.getElementsByClass('Part').stream()
    newParts = [allParts[i].flat.getElementsNotOfClass('GeneralNote').stream() 
                for i in range(len(allParts))]
    paddingLeft = allParts[0].getElementsByClass('Measure')[0].paddingLeft
    for (offsets, notes) in sorted(allHarmonies.items()):
        (initOffset, endTime) = offsets
        for genNoteIndex in range(len(notes)):
            music21GeneralNote = notes[genNoteIndex]
            newGeneralNote = copy.deepcopy(music21GeneralNote)
            newGeneralNote.quarterLength = endTime - initOffset
            newGeneralNote.tie = None
            newParts[genNoteIndex].insert(initOffset + paddingLeft, newGeneralNote)
    for givenPart in newParts:
        givenPart.makeNotation(inPlace=True, cautionaryNotImmediateRepeat=False)
        if paddingLeft != 0.0:
            givenPart[0].padAsAnacrusis()
            for m in givenPart:
                m.number -= 1
    newScore = stream.Score(newParts)
    return newScore
    
def extractHarmonies(music21Stream):
    '''
    Takes in a :class:`~music21.stream.Stream` and returns a dictionary whose values
    are the voice leading moments of the :class:`~music21.stream.Stream` and whose
    keys are (offset, endTime) pairs delimiting their duration. The voice leading
    moments are spelled out from the first or highest :class:`~music21.stream.Part`
    to the lowest one. 

    >>> from music21 import corpus
    >>> score = corpus.parse("corelli/opus3no1/1grave").measures(1,3)
    >>> #_DOCS_SHOW score.show()
    
    .. image:: images/figuredBass/corelli_grave.*
            :width: 700


    >>> from music21.figuredBass import checker
    >>> allHarmonies = checker.extractHarmonies(score)
    >>> for (offsets, notes) in sorted(allHarmonies.items()):
    ...    print("{0!s:15}[{1!s:23}{2!s:23}{3!s:22}]".format(offsets, notes[0], notes[1], notes[2]))
    (0.0, 1.5)     [<music21.note.Note C>  <music21.note.Note A>  <music21.note.Note F> ]
    (1.5, 2.0)     [<music21.note.Note C>  <music21.note.Note A>  <music21.note.Note F> ]
    (2.0, 3.0)     [<music21.note.Note B-> <music21.note.Note G>  <music21.note.Note G> ]
    (3.0, 3.5)     [<music21.note.Note A>  <music21.note.Note F>  <music21.note.Note A> ]
    (3.5, 4.0)     [<music21.note.Note A>  <music21.note.Note F>  <music21.note.Note B->]
    (4.0, 6.0)     [<music21.note.Note G>  <music21.note.Note E>  <music21.note.Note C> ]
    (6.0, 6.5)     [<music21.note.Note A>  <music21.note.Note F>  <music21.note.Note A> ]
    (6.5, 7.0)     [<music21.note.Note B-> <music21.note.Note F>  <music21.note.Note A> ]
    (7.0, 7.5)     [<music21.note.Note C>  <music21.note.Note F>  <music21.note.Note A> ]
    (7.5, 8.0)     [<music21.note.Note C>  <music21.note.Note E>  <music21.note.Note A> ]
    (8.0, 8.5)     [<music21.note.Note C>  <music21.note.Note D>  <music21.note.Note B->]
    (8.5, 9.0)     [<music21.note.Note F>  <music21.note.Note D>  <music21.note.Note B->]
    (9.0, 9.5)     [<music21.note.Note B-> <music21.note.Note D>  <music21.note.Note B->]
    (9.5, 10.0)    [<music21.note.Note B-> <music21.note.Note G>  <music21.note.Note B->]
    (10.0, 10.5)   [<music21.note.Note B-> <music21.note.Note E>  <music21.note.Note C> ]
    (10.5, 11.0)   [<music21.note.Note B-> <music21.note.Note C>  <music21.note.Note C> ]
    (11.0, 11.5)   [<music21.note.Note A>  <music21.note.Note F>  <music21.note.Note D> ]
    (11.5, 12.0)   [<music21.note.Note A>  <music21.note.Note F>  <music21.note.Note A> ]
    '''
    allParts = music21Stream.getElementsByClass('Part')
    if len(allParts) < 2:
        raise Exception()
    allHarmonies = createOffsetMapping(allParts[0])
    for music21Part in allParts[1:]:
        allHarmonies = correlateHarmonies(allHarmonies, music21Part)
    return allHarmonies

def createOffsetMapping(music21Part):
    '''
    Creates an initial offset mapping of a :class:`~music21.stream.Part`.
    
    >>> from music21 import corpus
    >>> from music21.figuredBass import checker
    >>> score = corpus.parse("corelli/opus3no1/1grave").measures(1,3)   
    >>> v0 = score[0]
    >>> offsetMapping = checker.createOffsetMapping(v0)
    >>> for (offsets, notes) in sorted(offsetMapping.items()):
    ...    print("{0!s:15}[{1!s:22}]".format(offsets, notes[0]))
    (0.0, 1.5)     [<music21.note.Note C> ]
    (1.5, 2.0)     [<music21.note.Note C> ]
    (2.0, 3.0)     [<music21.note.Note B->]
    (3.0, 4.0)     [<music21.note.Note A> ]
    (4.0, 6.0)     [<music21.note.Note G> ]
    (6.0, 6.5)     [<music21.note.Note A> ]
    (6.5, 7.0)     [<music21.note.Note B->]
    (7.0, 8.0)     [<music21.note.Note C> ]
    (8.0, 8.5)     [<music21.note.Note C> ]
    (8.5, 9.0)     [<music21.note.Note F> ]
    (9.0, 11.0)    [<music21.note.Note B->]
    (11.0, 12.0)   [<music21.note.Note A> ]
    '''
    currentMapping = collections.defaultdict(list)
    for music21GeneralNote in music21Part.flat.getElementsByClass('GeneralNote'):
        initOffset = music21GeneralNote.offset
        endTime = initOffset + music21GeneralNote.quarterLength
        currentMapping[(initOffset, endTime)].append(music21GeneralNote)
    return currentMapping

def correlateHarmonies(currentMapping, music21Part):
    '''
    Adds a new :class:`~music21.stream.Part` to an existing offset mapping.
    
    >>> from music21 import corpus
    >>> from music21.figuredBass import checker
    >>> score = corpus.parse("corelli/opus3no1/1grave").measures(1,3)   
    >>> v0 = score[0]
    >>> offsetMapping = checker.createOffsetMapping(v0)    
    >>> v1 = score[1]
    >>> newMapping = checker.correlateHarmonies(offsetMapping, v1)
    >>> for (offsets, notes) in sorted(newMapping.items()):
    ...    print("{0!s:15}[{1!s:23}{2!s:21}]".format(offsets, notes[0], notes[1]))
    (0.0, 1.5)     [<music21.note.Note C>  <music21.note.Note A>]
    (1.5, 2.0)     [<music21.note.Note C>  <music21.note.Note A>]
    (2.0, 3.0)     [<music21.note.Note B-> <music21.note.Note G>]
    (3.0, 4.0)     [<music21.note.Note A>  <music21.note.Note F>]
    (4.0, 6.0)     [<music21.note.Note G>  <music21.note.Note E>]
    (6.0, 6.5)     [<music21.note.Note A>  <music21.note.Note F>]
    (6.5, 7.0)     [<music21.note.Note B-> <music21.note.Note F>]
    (7.0, 7.5)     [<music21.note.Note C>  <music21.note.Note F>]
    (7.5, 8.0)     [<music21.note.Note C>  <music21.note.Note E>]
    (8.0, 8.5)     [<music21.note.Note C>  <music21.note.Note D>]
    (8.5, 9.0)     [<music21.note.Note F>  <music21.note.Note D>]
    (9.0, 9.5)     [<music21.note.Note B-> <music21.note.Note D>]
    (9.5, 10.0)    [<music21.note.Note B-> <music21.note.Note G>]
    (10.0, 10.5)   [<music21.note.Note B-> <music21.note.Note E>]
    (10.5, 11.0)   [<music21.note.Note B-> <music21.note.Note C>]
    (11.0, 12.0)   [<music21.note.Note A>  <music21.note.Note F>]    
    '''
    newMapping = {}
    
    for offsets in sorted(currentMapping.keys()):
        (initOffset, endTime) = offsets
        notesInRange = music21Part.flat.iter.getElementsByClass('GeneralNote').getElementsByOffset(
                            initOffset, offsetEnd=endTime, 
                            includeEndBoundary=False, mustFinishInSpan=False, 
                            mustBeginInSpan=False, includeElementsThatEndAtStart=False)
        allNotesSoFar = currentMapping[offsets]
        for music21GeneralNote in notesInRange:
            newInitOffset = initOffset
            newEndTime = endTime
            if not music21GeneralNote.offset < initOffset:
                newInitOffset = music21GeneralNote.offset
            if not music21GeneralNote.offset + music21GeneralNote.quarterLength > endTime:
                newEndTime = opFrac(music21GeneralNote.offset + music21GeneralNote.quarterLength)
            allNotesCopy = copy.copy(allNotesSoFar)
            allNotesCopy.append(music21GeneralNote)
            newMapping[(newInitOffset, newEndTime)] = allNotesCopy
    
    return newMapping

#-------------------------------------------------------------------------------
# Generic methods for checking for composition rule violations in streams

def checkSinglePossibilities(music21Stream, functionToApply, color="#FF0000", debug=False):
    '''    
    Takes in a :class:`~music21.stream.Score` and a functionToApply which takes in a possibility
    instance, a tuple with pitches or rests comprising a vertical sonority. Changes the color of
    notes in the :class:`~music21.stream.Score` which comprise rule violations as determined by
    functionToApply. 
    

    .. note:: Colored notes are NOT supported in Finale. 

    >>> from music21 import corpus
    >>> music21Stream = corpus.parse("corelli/opus3no1/1grave").measures(1,6)
    >>> #_DOCS_SHOW music21Stream.show()

    .. image:: images/figuredBass/corelli_grave2.*
            :width: 700


    >>> from music21.figuredBass import checker
    >>> functionToApply = checker.voiceCrossing
    >>> checker.checkSinglePossibilities(music21Stream, functionToApply, debug = True)
    Function To Apply: voiceCrossing
    (Offset, End Time):      Part Numbers:
    (16.0, 16.5)             (1, 2)
    (16.5, 17.0)             (1, 2)
    
    Voice Crossing is present in the fifth measure between the first and second voices,
    and the notes in question are highlighted in the music21Stream.
    

    >>> #_DOCS_SHOW music21Stream.show()

    .. image:: images/figuredBass/corelli_voiceCrossing.*
            :width: 700
    '''
    if debug is True:
        debugInfo = []
        debugInfo.append("Function To Apply: " + functionToApply.__name__)
        debugInfo.append("{0!s:25}{1!s}".format("(Offset, End Time):", "Part Numbers:"))
    
    allHarmonies = sorted(list(extractHarmonies(music21Stream).items()))
    allParts = [p.flat for p in music21Stream.getElementsByClass('Part')]
    for (offsets, notes) in allHarmonies:
        vlm = [generalNoteToPitch(n) for n in notes]
        vlm_violations = functionToApply(vlm)
        initOffset = offsets[0]
        for partNumberTuple in vlm_violations:
            for partNumber in partNumberTuple:
                if color is not None:
                    noteA = allParts[partNumber - 1].iter.getElementsByOffset(
                                                            initOffset, 
                                                            initOffset, 
                                                            mustBeginInSpan=False)[0]
                    noteA.color = color
            if debug is True:
                debugInfo.append("{0!s:25}{1!s}".format(offsets, partNumberTuple))

    if debug is True:
        if len(debugInfo) == 2:
            debugInfo.append("No violations to report.")
        for lineInfo in debugInfo:
            print(lineInfo)

def checkConsecutivePossibilities(music21Stream, functionToApply, color="#FF0000", debug=False):
    '''
    Takes in a :class:`~music21.stream.Score` and a functionToApply which takes in two consecutive 
    possibility instances, each a tuple with pitches or rests comprising a vertical sonority. 
    Changes the color of notes in the :class:`~music21.stream.Score` which comprise rule violations 
    as determined by functionToApply. 
    

    .. note:: Colored notes are NOT supported in Finale. 

    >>> from music21 import corpus
    >>> music21Stream = corpus.parse('theoryExercises/checker_demo.xml')
    >>> #_DOCS_SHOW music21Stream.show()
    
    .. image:: images/figuredBass/checker_demo.*
            :width: 700


    >>> from music21.figuredBass import checker
    >>> functionToApply = checker.parallelOctaves    
    >>> checker.checkConsecutivePossibilities(music21Stream, functionToApply, debug=True)
    Function To Apply: parallelOctaves
    (Offset A, End Time A):  (Offset B, End Time B):  Part Numbers:
    (1.0, 2.0)               (2.0, 3.0)               (2, 4)
    (2.0, 3.0)               (3.0, 5.0)               (2, 4)
    (8.0, 9.0)               (9.0, 11.0)              (1, 3)
    
    Parallel octaves can be found in the first measure, between the first two measures,
    and between the third and the fourth measure. The notes in question are highlighted
    in the music21Stream, as shown below.

    
    >>> #_DOCS_SHOW music21Stream.show()

    .. image:: images/figuredBass/checker_parallelOctaves.*
            :width: 700
    '''
    if debug is True:
        debugInfo = []
        debugInfo.append("Function To Apply: " + functionToApply.__name__)
        debugInfo.append("{0!s:25}{1!s:25}{2!s}".format(
                        "(Offset A, End Time A):", "(Offset B, End Time B):", "Part Numbers:"))

    allHarmonies = sorted(extractHarmonies(music21Stream).items())
    allParts = [p.flat for p in music21Stream.getElementsByClass('Part')]    
    (previousOffsets, previousNotes) = allHarmonies[0]
    vlmA = [generalNoteToPitch(n) for n in previousNotes]
    initOffsetA = previousOffsets[0]
    
    for (offsets, notes) in allHarmonies[1:]:
        vlmB = [generalNoteToPitch(n) for n in notes]
        initOffsetB = offsets[0]
        vlm_violations = functionToApply(vlmA, vlmB)
        for partNumberTuple in vlm_violations:
            for partNumber in partNumberTuple:
                if color is not None:
                    noteA = allParts[partNumber - 1].iter.getElementsByOffset(
                                initOffsetA, initOffsetA, mustBeginInSpan=False)[0]
                    noteB = allParts[partNumber - 1].iter.getElementsByOffset(
                                initOffsetB, initOffsetB, mustBeginInSpan=False)[0]
                    noteA.color = color
                    noteB.color = color
            if debug is True:
                debugInfo.append("{0!s:25}{1!s:25}{2!s}".format(previousOffsets, 
                                                                offsets, 
                                                                partNumberTuple))
        # Current vlm becomes previous
        previousOffsets = offsets
        vlmA = vlmB
        initOffsetA = initOffsetB

    if debug is True:
        if len(debugInfo) == 2:
            debugInfo.append("No violations to report.")
        for lineInfo in debugInfo:
            print(lineInfo)

#-------------------------------------------------------------------------------
# Single Possibility Rule-Checking Methods
  
# Takes in a possibility, returns (partNumberA, partNumberB) which
# represent two voices which form a voice crossing.
def voiceCrossing(possibA):
    '''
    Returns a list of (partNumberA, partNumberB) pairs, each representing
    two voices which form a voice crossing. The parts from lowest part to 
    highest part (right to left) must correspond to increasingly higher 
    pitches in order for there to be no voice crossing. Comparisons between 
    pitches are done using pitch comparison methods, which are based on pitch 
    space values (see :class:`~music21.pitch.Pitch`).
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import checker
    >>> C4 = pitch.Pitch('C4')
    >>> E4 = pitch.Pitch('E4')
    >>> C5 = pitch.Pitch('C5')
    >>> G5 = pitch.Pitch('G5')
    >>> possibA1 = (C5, G5, E4)
    >>> checker.voiceCrossing(possibA1) # G5 > C5
    [(1, 2)]
    >>> possibA2 = (C5, E4, C4)
    >>> checker.voiceCrossing(possibA2)
    []
    '''
    partViolations = []
    for part1Index in range(len(possibA)):
        try:
            higherPitch = possibA[part1Index]
            higherPitch.ps # pylint: disable=pointless-statement
        except AttributeError:
            continue
        for part2Index in range(part1Index + 1, len(possibA)):
            try:
                lowerPitch = possibA[part2Index]
                lowerPitch.ps # pylint: disable=pointless-statement
            except AttributeError:
                continue
            if higherPitch < lowerPitch:
                partViolations.append((part1Index + 1, part2Index + 1))
    return partViolations

#-------------------------------------------------------------------------------
# Consecutive Possibility Rule-Checking Methods

parallelFifthsTable = {}
hiddenFifthsTable = {}
parallelOctavesTable = {}
hiddenOctavesTable = {}

def parallelFifths(possibA, possibB):
    '''
    Returns a list of (partNumberA, partNumberB) pairs, each representing
    two voices which form parallel fifths.
 
 
    If pitchA1 and pitchA2 in possibA are separated by
    a simple interval of a perfect fifth, and they move
    to a pitchB1 and pitchB2 in possibB also separated
    by the simple interval of a perfect fifth, then this
    constitutes parallel fifths between these two parts.
 
    >>> from music21 import pitch
    >>> from music21.figuredBass import checker
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
    >>> checker.parallelFifths(possibA1, possibB1)
    [(2, 3)]


    
    Now, the tenor moves instead to F3. The interval between
    D3 and F3 is a minor third. The bass and tenor parts 
    don't form parallel fifths. The soprano part forms parallel
    fifths with neither the bass nor tenor parts. The
    two possibilities, therefore, have no parallel fifths.
    
    
    >>> F3 = pitch.Pitch('F3')
    >>> possibA2 = (B4, G3, C3)
    >>> possibB2 = (A4, F3, D3)
    >>> checker.parallelFifths(possibA2, possibB2)
    []
    '''
    pairsList = possibility.partPairs(possibA, possibB)
    partViolations = []
    
    for pair1Index in range(len(pairsList)):
        (higherPitchA, higherPitchB) = pairsList[pair1Index]
        for pair2Index in range(pair1Index + 1, len(pairsList)):
            (lowerPitchA, lowerPitchB) = pairsList[pair2Index]
            try:
                if not abs(higherPitchA.ps - lowerPitchA.ps) % 12 == 7:
                    continue
                if not abs(higherPitchB.ps - lowerPitchB.ps) % 12 == 7:
                    continue
            except AttributeError:
                continue
            #Very high probability of ||5, but still not certain.
            pitchQuartet = (lowerPitchA, lowerPitchB, higherPitchA, higherPitchB)
            if pitchQuartet in parallelFifthsTable:
                hasParallelFifths = parallelFifthsTable[pitchQuartet]
                if hasParallelFifths: 
                    partViolations.append((pair1Index + 1, pair2Index + 1))
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.parallelFifth():
                partViolations.append((pair1Index + 1, pair2Index + 1))
                parallelFifthsTable[pitchQuartet] = True
            parallelFifthsTable[pitchQuartet] = False

    return partViolations

def hiddenFifth(possibA, possibB):
    '''
    Returns a list with a (highestPart, lowestPart) pair which represents
    a hidden fifth between shared outer parts of possibA and possibB. The
    outer parts here are the first and last elements of each possibility. 
        
    
    If sopranoPitchA and bassPitchA in possibA move to a sopranoPitchB
    and bassPitchB in possibB in similar motion, and the simple interval 
    between sopranoPitchB and bassPitchB is that of a perfect fifth, 
    then this constitutes a hidden octave between the two possibilities.
    
    >>> from music21 import pitch
    >>> from music21.figuredBass import checker
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
    >>> checker.hiddenFifth(possibA1, possibB1)
    [(1, 3)]
    
    
    Here, the soprano and bass parts also move in similar motion, but the 
    simple interval between D3 and Ab5 is a diminished fifth. Consequently, 
    there is no hidden fifth.
    

    >>> Ab5 = pitch.Pitch('A-5')   
    >>> possibA2 = (E5, E3, C3)
    >>> possibB2 = (Ab5, F3, D3)
    >>> checker.hiddenFifth(possibA2, possibB2)
    []
    
    
    Now, we have the soprano and bass parts again moving to A5 and D3, whose 
    simple interval is a perfect fifth. However, the bass moves up while the 
    soprano moves down. Therefore, there is no hidden fifth.
    
    
    >>> E6 = pitch.Pitch('E6')
    >>> possibA3 = (E6, E3, C3)
    >>> possibB3 = (A5, F3, D3)
    >>> checker.hiddenFifth(possibA3, possibB3)
    []
    '''
    partViolations = []
    pairsList = possibility.partPairs(possibA, possibB)
    (highestPitchA, highestPitchB) = pairsList[0]
    (lowestPitchA, lowestPitchB) = pairsList[-1]

    try:
        if abs(highestPitchB.ps - lowestPitchB.ps) % 12 == 7:
            #Very high probability of hidden fifth, but still not certain.
            pitchQuartet = (lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
            if pitchQuartet in hiddenFifthsTable:
                hasHiddenFifth = hiddenFifthsTable[pitchQuartet]
                if hasHiddenFifth:
                    partViolations.append((1, len(possibB)))
                return partViolations
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.hiddenFifth():
                partViolations.append((1, len(possibB)))
                hiddenFifthsTable[pitchQuartet] = True
            hiddenFifthsTable[pitchQuartet] = False
            return partViolations
    except AttributeError:
        pass
    
    return partViolations

def parallelOctaves(possibA, possibB):
    '''
    Returns a list of (partNumberA, partNumberB) pairs, each representing
    two voices which form parallel octaves.
 
 
    If pitchA1 and pitchA2 in possibA are separated by
    a simple interval of a perfect octave, and they move
    to a pitchB1 and pitchB2 in possibB also separated
    by the simple interval of a perfect octave, then this
    constitutes parallel octaves between these two parts.

    >>> from music21 import pitch
    >>> from music21.figuredBass import checker
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
    >>> checker.parallelOctaves(possibA1, possibB1)
    [(1, 3)]


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
    >>> checker.parallelOctaves(possibA2, possibB2)
    []
    '''
    pairsList = possibility.partPairs(possibA, possibB)
    partViolations = []
    
    for pair1Index in range(len(pairsList)):
        (higherPitchA, higherPitchB) = pairsList[pair1Index]
        for pair2Index in range(pair1Index + 1, len(pairsList)):
            (lowerPitchA, lowerPitchB) = pairsList[pair2Index]
            try:
                if not abs(higherPitchA.ps - lowerPitchA.ps) % 12 == 0:
                    continue
                if not abs(higherPitchB.ps - lowerPitchB.ps) % 12 == 0:
                    continue
            except AttributeError:
                continue
            #Very high probability of ||8, but still not certain.
            pitchQuartet = (lowerPitchA, lowerPitchB, higherPitchA, higherPitchB)
            if pitchQuartet in parallelOctavesTable:
                hasParallelOctaves = parallelOctavesTable[pitchQuartet]
                if hasParallelOctaves: 
                    partViolations.append((pair1Index + 1, pair2Index + 1))
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.parallelOctave():
                partViolations.append((pair1Index + 1, pair2Index + 1))
                parallelOctavesTable[pitchQuartet] = True
            parallelOctavesTable[pitchQuartet] = False

    return partViolations

def hiddenOctave(possibA, possibB):
    '''
    Returns a list with a (highestPart, lowestPart) pair which represents
    a hidden octave between shared outer parts of possibA and possibB. The
    outer parts here are the first and last elements of each possibility. 
    
    
    If sopranoPitchA and bassPitchA in possibA move to a sopranoPitchB
    and bassPitchB in possibB in similar motion, and the simple interval 
    between sopranoPitchB and bassPitchB is that of a perfect octave, 
    then this constitutes a hidden octave between the two possibilities.

    >>> from music21 import pitch
    >>> from music21.figuredBass import checker
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
    >>> checker.hiddenOctave(possibA1, possibB1)
    [(1, 3)]
    
    
    Here, the bass part moves up from C3 to D3 but the soprano part moves
    down from A6 to D6. There is no hidden octave since the parts move in
    contrary motion. 
    
    
    >>> A6 = pitch.Pitch('A6')
    >>> possibA2 = (A6, E3, C3)
    >>> possibB2 = (D6, F3, D3)
    >>> checker.hiddenOctave(possibA2, possibB2)
    []
    '''
    partViolations = []
    pairsList = possibility.partPairs(possibA, possibB)
    (highestPitchA, highestPitchB) = pairsList[0]
    (lowestPitchA, lowestPitchB) = pairsList[-1]

    try:
        if abs(highestPitchB.ps - lowestPitchB.ps) % 12 == 0:
            #Very high probability of hidden octave, but still not certain.
            pitchQuartet = (lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
            if pitchQuartet in hiddenOctavesTable:
                hasHiddenOctave = hiddenOctavesTable[pitchQuartet]
                if hasHiddenOctave:
                    partViolations.append((1, len(possibB)))
                return partViolations
            vlq = voiceLeading.VoiceLeadingQuartet(*pitchQuartet)
            if vlq.hiddenOctave():
                partViolations.append((1, len(possibB)))
                hiddenOctavesTable[pitchQuartet] = True
            hiddenOctavesTable[pitchQuartet] = False
            return partViolations
    except AttributeError:
        pass
    
    return partViolations

#------------------------------------------------------------------------------
# Helper Methods

def generalNoteToPitch(music21GeneralNote):
    '''
    Takes a :class:`~music21.note.GeneralNote`. If it is a :class:`~music21.note.Note`,
    returns its pitch. Otherwise, returns the string "RT", a rest placeholder.
    
    >>> from music21 import note
    >>> from music21 import chord
    >>> n1 = note.Note('G5')
    >>> c1 = chord.Chord(['C3','E3','G3'])
    >>> from music21.figuredBass import checker
    >>> checker.generalNoteToPitch(n1)
    <music21.pitch.Pitch G5>
    >>> checker.generalNoteToPitch(c1)
    'RT'
    '''
    if music21GeneralNote.isNote:
        return music21GeneralNote.pitch
    else:
        return "RT"

_DOC_ORDER = [extractHarmonies, getVoiceLeadingMoments, 
              checkConsecutivePossibilities, checkSinglePossibilities]
#------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
