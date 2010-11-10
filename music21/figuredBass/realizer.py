#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizer.py
# Purpose:      music21 class which will find all valid solutions of a given figured bass
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import random

from music21 import figuredBassScale
from music21 import pitch
from music21 import voiceLeading
from music21 import note
from music21 import stream
from music21 import meter


def realizeFiguredBass(figuredBassList, scaleValue, scaleMode = 'major'):
    sopranoLine = stream.Part()
    altoLine = stream.Part()
    tenorLine = stream.Part()
    bassLine = stream.Part()
    
    fbScale = figuredBassScale.FiguredBassScale(scaleValue, scaleMode)
    (firstBassNote, firstNotation) = figuredBassList.pop(0)
        
    startPossibilities = getStartingPitches(fbScale, firstBassNote.pitch, firstNotation)
    #startPossibilities = [[pitch.Pitch('E5'), pitch.Pitch('G4'), pitch.Pitch('C4'), pitch.Pitch('C3')]]
    allPossibilities = [startPossibilities]
    allPossibleMovements = []
    prevPossibilities = startPossibilities
    
    
    for (nextBassNote, nextNotation) in figuredBassList:
        nextBass = nextBassNote.pitch
        (nextPossibilities, nextMovements) = getNextPossibilities(fbScale, prevPossibilities, nextBass, nextNotation)
        #print nextPossibilities
        #print nextMovements
        allPossibilities.append(nextPossibilities)
        allPossibleMovements.append(nextMovements)
        #print len(nextPossibilities)
        prevPossibilities = nextPossibilities
    
    allNumberProgressions = translateMovementsToNumberProgressions(allPossibleMovements)
    print "Number of possible progressions: " + str(len(allNumberProgressions))
    print 
    
    for i in range(20):
        chordProgressionIndex = random.randint(0, len(allNumberProgressions)-1)
        chordProgression = translateNumberProgressionToChordProgression(allPossibilities, allNumberProgressions[chordProgressionIndex])
        print "Progression #"  + str(i+1)
        printChordProgression(chordProgression)
        for chord in chordProgression:
            sopranoLine.append(note.Note(chord[0]))
            altoLine.append(note.Note(chord[1]))
            tenorLine.append(note.Note(chord[2]))
            bassLine.append(note.Note(chord[3]))
        sopranoLine.append(note.Rest())
        altoLine.append(note.Rest())
        tenorLine.append(note.Rest())
        bassLine.append(note.Rest())


    #printChordProgression(allChordProgressions[0])
        
    score = stream.Score()
    score.insert(0, meter.TimeSignature('6/4'))
    score.insert(0, sopranoLine)
    score.insert(0, altoLine)
    score.insert(0, tenorLine)
    score.insert(0, bassLine)
    score.show()
    #sopranoLine.show()
    return score


def translateNumberProgressionToChordProgression(allPossibilities, numberProgression):
    chords = []
    for i in range(len(allPossibilities)):
        index = numberProgression[i]
        chords.append(allPossibilities[i][index])
    
    return chords


def printChordProgression(chordProgression):
    sopranoLine = ""
    altoLine = ""
    tenorLine = ""
    bassLine = ""
    for chord in chordProgression:
        sopranoLine += str(chord[0]) + "    "
        altoLine += str(chord[1]) + "    "
        tenorLine += str(chord[2]) + "    "
        bassLine += str(chord[3]) + "    "
        
    print sopranoLine
    print altoLine
    print tenorLine
    print bassLine
    print


def translateMovementsToNumberProgressions(allPossibleMovements):
    initialProgressions = []
    for i in range(len(allPossibleMovements[0])):
        for j in range(len(allPossibleMovements[0][i])):
            initialProgressions.append([i, allPossibleMovements[0][i][j]])
    
    prevProgressions = initialProgressions
    nextProgressions = []
    for i in range(1, len(allPossibleMovements)):
        lastIndex = len(prevProgressions[0]) - 1
        for j in range(len(prevProgressions)):
            lastNumber = prevProgressions[j][lastIndex]
            for k in range(len(allPossibleMovements[i][lastNumber])):
                nextProgressions.append(prevProgressions[j] + [allPossibleMovements[i][lastNumber][k]])
        prevProgressions = nextProgressions
        nextProgressions = []
    
    return prevProgressions 
            

def getStartingPitches(fbScale, firstBass, firstNotation, octaveLimit=5):
    possibilities = []
    pitchList = fbScale.getPitchesAboveBassPitchFromNotation(firstBass, firstNotation, octaveLimit)
    pitchList = sortPitchListByDistanceToPitch(firstBass, pitchList)
    
    #soprano > alto > tenor > bass
    for i in range(len(pitchList)):
        firstTenor = pitchList[i]
        for j in range(i+1, len(pitchList)):
            firstAlto = pitchList[j]
            for k in range(j+1, len(pitchList)):
                firstSoprano = pitchList[k]
                possibilities.append([firstSoprano, firstAlto, firstTenor, firstBass])
    
    newPossibilities = []
    for firstPitches in possibilities:
        if not isStartingRuleBreaker(fbScale, firstPitches, firstNotation):
            newPossibilities.append(firstPitches)
    
    return newPossibilities
    

def isStartingRuleBreaker(fbScale, firstPitches, firstNotation):
    if not(len(firstPitches) == 4):
        raise FiguredBassException("A figured bass sequence consists of four voices")
    firstSoprano = firstPitches[0]
    firstAlto = firstPitches[1]
    firstTenor = firstPitches[2]
    firstBass = firstPitches[3]
    
    sopranoPs = firstSoprano.ps
    altoPs = firstAlto.ps
    tenorPs = firstTenor.ps
    bassPs = firstBass.ps
    
    sopranoAltoMaxSep = 1.0 #Maximum separation between Soprano and Alto (in octaves)
    altoTenorMaxSep = 1.0 #Maximum separation between Alto and Tenor (in octaves)
    tenorBassMaxSep = 1.5 #Maximum separation between Tenor and Bass (in octaves)
    
    if abs(sopranoPs - altoPs) > sopranoAltoMaxSep * 12.0:
        return True
    if abs(altoPs - tenorPs) > altoTenorMaxSep * 12.0:
        return True
    if abs(tenorPs - bassPs) > tenorBassMaxSep * 12.0:
        return True

    #Only complete chords
    pitchNames = [firstSoprano.name, firstAlto.name, firstTenor.name, firstBass.name]
    pitchNamesInChord = fbScale.getPitchNamesFromNotation(firstBass, firstNotation)

    for pitchName in pitchNamesInChord:
        if pitchName not in pitchNames:
            return True
    
    return False


def getNextPossibilities(fbScale, prevPossibilities, nextBass, nextNotation = '-'):
    allPossibilities = []
    allMovements = []
    for prevPitches in prevPossibilities:
        nextPossibilities = findNextPitches(fbScale, prevPitches, nextBass, nextNotation)
        movements = []
        for nextPitches in nextPossibilities:
            if not isExtendedRuleBreaker(fbScale, prevPitches, nextPitches, nextNotation):
                try:
                    movements.append(allPossibilities.index(nextPitches))
                except ValueError:
                    allPossibilities.append(nextPitches)
                    movements.append(len(allPossibilities) - 1)
        #movements.sort()
        allMovements.append(movements)
    return (allPossibilities, allMovements)


def findNextPitches(fbScale, prevPitches, nextBass, nextNotation='-', octaveLimit=5):
    '''
    Given a scale, a set of previous pitches, a bass pitch and its notation,
    return all sets of possibilities for the next pitches.
    
    prevPitches = [prevSoprano, prevAlto, prevTenor, prevBass]
    Each set of possibilities is free of parallel fifths, parallel octaves,
    voice crossings, and leaps of greater than an octave with respect to the 
    previous pitches.
    
    >>> from music21 import *
    >>> fbScale = figuredBassScale.FiguredBassScale('C')
    >>> prevSoprano = pitch.Pitch('E4')
    >>> prevAlto = pitch.Pitch('C4')
    >>> prevTenor = pitch.Pitch('G3')
    >>> prevBass = pitch.Pitch('C3')
    >>> prevPitches = [prevSoprano, prevAlto, prevTenor, prevBass]
    >>> nextBass = pitch.Pitch('D3')
    >>> nextNotation = '6'
    >>> findNextPitches(fbScale, prevPitches, nextBass, nextNotation)[0:3]
    [[F4, B3, F3, D3], [D4, B3, F3, D3], [B4, B3, F3, D3]]
    >>> len(findNextPitches(fbScale, prevPitches, nextBass, nextNotation))
    12
    '''
    nextBass = __convertToPitch(nextBass)
    for voiceIndex in range(len(prevPitches)):
        prevPitches[voiceIndex] = __convertToPitch(prevPitches[voiceIndex])
        
    possibilities = []
    
    if not(len(prevPitches) == 4):
        raise FiguredBassException("A figured bass sequence consists of four voices")
    prevSoprano = prevPitches[0]
    prevAlto = prevPitches[1]
    prevTenor = prevPitches[2]
    prevBass = prevPitches[3]
    
    pitchList = fbScale.getPitchesAboveBassPitchFromNotation(nextBass, nextNotation, octaveLimit)
    bassPair = (prevBass, nextBass)
    tenorList = possiblePitches([bassPair], prevTenor, pitchList)
    
    for nextTenor in tenorList:
        tenorPair = (prevTenor, nextTenor)
        altoList = possiblePitches([bassPair, tenorPair], prevAlto, pitchList)
        for nextAlto in altoList:
            altoPair = (prevAlto, nextAlto)
            sopranoList = possiblePitches([bassPair, tenorPair, altoPair], prevSoprano, pitchList)
            for nextSoprano in sopranoList:
                nextPitches = [nextSoprano, nextAlto, nextTenor, nextBass]
                possibilities.append(nextPitches)
        
    return possibilities
    
    
def possiblePitches(voicePairs, pitchB1, pitchList):
    '''
    Provided a list of voice pairs (pitches in the same voice),
    see which pitches in list of possible pitches a new pitch 
    can actually move to, given voicing rules set about in the
    method isAbsoluteRuleBreaker. 
    
    >>> from music21 import *
    >>> voicePairA = (pitch.Pitch('C3'), pitch.Pitch('D3'))
    >>> voicePairB = (pitch.Pitch('G3'), pitch.Pitch('B3'))
    >>> pitchList = [pitch.Pitch('F3'), pitch.Pitch('B3'), pitch.Pitch('D4'), pitch.Pitch('F4'), pitch.Pitch('B4')]
    >>> possiblePitches([voicePairA, voicePairB], pitch.Pitch('C4'), pitchList) #voice crossing (C4->F3), parallel octaves (C4->D4)
    [B3, F4, B4]
    >>> voicePairC1 = (pitch.Pitch('C4'), pitch.Pitch('F4'))
    >>> possiblePitches([voicePairA, voicePairB, voicePairC1], pitch.Pitch('E4'), pitchList) #voice crossing (C4->F4, F4 higher than E4)
    []
    >>> voicePairC2 = (pitch.Pitch('C4'), pitch.Pitch('B3'))
    >>> possiblePitches([voicePairA, voicePairB, voicePairC2], pitch.Pitch('E4'), pitchList) #voice crossing (E4->F3, E4->B3)
    [F4, D4, B4]
    '''
    possibilities = []
    pitchList = sortPitchListByDistanceToPitch(pitchB1, pitchList)
    for pitchB2 in pitchList:
        isGood = True
        for (pitchA1, pitchA2) in voicePairs:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if isAbsoluteRuleBreaker(vlq):
                isGood = False
                break
        if isGood:
            possibilities.append(pitchB2)
    
    return possibilities
                

def isAbsoluteRuleBreaker(vlq, verbose=False):
    '''
    Takes in a VoiceLeadingQuartet and returns True if any voicing rules have
    been broken, although we can choose to relax the rules.
    
    Default voicing rules: 
    (a) No parallel (or antiparallel) fifths between the two voices, 
    (b) No parallel (or antiparallel) octaves between the two voices,
    (c) No voice crossings, as determined by frequency crossing (NOT written crossing)
    (d) No leaps of greater than an octave in either voice, as determined by absolute distance (NOT written distance)
    
    >>> from music21 import *
    >>> vlqA = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('G3'), pitch.Pitch('A3'))
    >>> isAbsoluteRuleBreaker(vlqA, True) #Parallel fifths = C->D, G->A
    Parallel fifths!
    True
    >>> vlqB = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('B3'), pitch.Pitch('G3'), pitch.Pitch('D3')) 
    >>> isAbsoluteRuleBreaker(vlqB, True) #Voice crossing = C->A, higher than the G above C
    Voice crossing!
    True
    >>> vlqC = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('F3'), pitch.Pitch('G3')) 
    >>> isAbsoluteRuleBreaker(vlqC, True) #Parallel fourths
    False
    
    OMIT_FROM_DOCS
    >>> vlqD = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('C4'), pitch.Pitch('D4'))
    >>> isAbsoluteRuleBreaker(vlqD, True) #Parallel octaves = C3->D3, C4->D4
    Parallel octaves!
    True
    >>> vlqE = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('G4'), pitch.Pitch('E5'), pitch.Pitch('D5'))
    >>> isAbsoluteRuleBreaker(vlqE, True)
    Greater than octave leap in bottom voice!
    True
    >>> vlqF = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('E5'), pitch.Pitch('G6'))
    >>> isAbsoluteRuleBreaker(vlqF, True)
    Greater than octave leap in top voice!
    True
    '''
    allowParallelFifths = False
    allowParallelOctaves = False
    allowVoiceCrossing = False
    allowMultiOctaveLeapsInBottomVoice = False
    allowMultiOctaveLeapsInTopVoice = False
    
    if vlq.parallelFifth(): 
        if not allowParallelFifths:
            if verbose:
                print "Parallel fifths!"
            return True
    if vlq.parallelOctave(): 
        if not allowParallelOctaves:
            if verbose:
                print "Parallel octaves!"
            return True
    if vlq.voiceCrossing(): 
        if not allowVoiceCrossing:
            if verbose:
                print "Voice crossing!"
            return True
    if abs(vlq.v1n1.ps - vlq.v1n2.ps) > 12.0: 
        if not allowMultiOctaveLeapsInBottomVoice:
            if verbose:            
                print "Greater than octave leap in bottom voice!"
            return True
    if abs(vlq.v2n1.ps - vlq.v2n2.ps) > 12.0: 
        if not allowMultiOctaveLeapsInTopVoice:
            if verbose:
                print "Greater than octave leap in top voice!"
            return True
    
    return False


def isExtendedRuleBreaker(fbScale, prevPitches, nextPitches, nextNotation, verbose = False):
    '''
    
    '''
    allowHiddenFifths = False
    allowHiddenOctaves = False
    allowIncompleteChords = False
    
    if not (len(prevPitches) == 4 or len(nextPitches) == 4):
        raise FiguredBassException("A figured bass chord consists of four voices")
    
    prevSoprano = prevPitches[0]
    prevBass = prevPitches[3]
    
    nextSoprano = nextPitches[0]
    nextAlto = nextPitches[1]
    nextTenor = nextPitches[2]
    nextBass = nextPitches[3]
    
    
    vlq = voiceLeading.VoiceLeadingQuartet(prevBass, nextBass, prevSoprano, nextSoprano)
    if vlq.hiddenFifth():
        if not allowHiddenFifths:
            if verbose:
                "Hidden fifth!"
            return True
    if vlq.hiddenOctave():
        if not allowHiddenOctaves:
            if verbose:
                "Hidden octave!"
            return True


    pitchNames = [nextSoprano.name, nextAlto.name, nextTenor.name, nextBass.name]
    pitchNamesInChord = fbScale.getPitchNamesFromNotation(nextBass, nextNotation)
    for pitchName in pitchNamesInChord:
        if pitchName not in pitchNames:
            if not allowIncompleteChords:
                if verbose:
                    "Chord #2 is incomplete!"
                return True

    #Leading tone resolves to tonic (7th scale degree, a HALF STEP down from the tonic)
    #The III chord in minor doesn't have a raised leading tone, and the seventh scale
    #degree doesn't have to resolve to the tonic.

    #Top three voices within an octave?
    

    return False


def sortPitchListByDistanceToPitch(pitchZero, pitchList):
    '''
    Given a reference pitch, order a given list of pitches in terms of their
    actual distance (not written distance) as determined by their pitch space
    number. Ties are broken alphabetically, then numerically.
    
    >>> from music21 import *
    >>> pitchZero = pitch.Pitch('C5')
    >>> pitchList = [pitch.Pitch('C6'), pitch.Pitch('G4'), pitch.Pitch('C4'), pitch.Pitch('C3'), pitch.Pitch('E5')]
    >>> sortPitchListByDistanceToPitch(pitchZero, pitchList)
    [E5, G4, C4, C6, C3]
    '''
    pitchZero = __convertToPitch(pitchZero)
    pitchZeroPs = pitchZero.ps
    newList = []
    for pitchOne in pitchList:
        pitchOne = __convertToPitch(pitchOne)
        pitchOnePs = pitchOne.ps
        distance = abs(pitchOnePs - pitchZeroPs)
        newList.append((distance, pitchOne))
    newList.sort()
    sortedList = []
    for (distance, pitchOne) in newList:
        sortedList.append(pitchOne)
    return sortedList


def __convertToPitch(pitchValue):
    '''
    Converts a pitch string to a music21 pitch, only if necessary.
    '''
    if type(pitchValue) == str:
        pitchValue = pitch.Pitch(pitchValue)
    return pitchValue


class FiguredBassException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    figuredBassList = [(note.Note('A2'), '-'),(note.Note('E3'), '#'),(note.Note('A2'), '-')]
    realizeFiguredBass(figuredBassList, 'A', 'minor') 
    
    #figuredBassList = [(note.Note('C3'), '-'), (note.Note('F3'), '6'), (note.Note('G3'), '6/4'), \
    #                   (note.Note('F3'), '4/2'), (note.Note('E3'), '6')]
    #realizeFiguredBass(figuredBassList, 'C', 'major') 
    music21.mainTest(Test)