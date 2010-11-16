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
import copy

from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.pitch import Pitch
from music21 import pitch
from music21 import voiceLeading
from music21 import note
from music21 import stream
from music21 import meter
from music21 import environment
from music21 import chord
from music21 import key


class FiguredBass:
    def __init__(self, timeSig, key, mode = 'major'):
        self.timeSig = timeSig
        self.key = key
        self.mode = mode
        self.scale = realizerScale.FiguredBassScale(key, mode)
        self.rules = rules.Rules()
        self.octaveLimit = 5
        self.figuredBassList = []
        self.allChords = None
        self.allMovements = None
        self.bassNotes = []
    
    def addElement(self, bassNote, notation = ''):
        self.bassNotes.append(bassNote)
        self.figuredBassList.append((bassNote.pitch, notation))
    
    def solve(self):
        (firstBass, firstNotation) = self.figuredBassList[0]
        print("Finding possible starting chords for: " + str((firstBass, firstNotation)))
        startingChords = self._findPossibleStartingChords(firstBass, firstNotation)
        self.allChords = {}
        self.allMovements = {}
        self.allChords[0] = startingChords
        
        for chordIndex in range(1, len(self.figuredBassList)):
            (nextBass, nextNotation) = self.figuredBassList[chordIndex]
            prevChords = self.allChords[chordIndex - 1]
            print("Finding all possibilities for: " + str((nextBass, nextNotation)))
            (nextChords, prevMovements) = self._findNextPossibilities(prevChords, nextBass, nextNotation)
            self.allChords[chordIndex] = nextChords
            self.allMovements[chordIndex - 1] = prevMovements
        
        print("Trimming movements...")
        self._trimAllMovements()
        print("Solving complete.")
    
    def _trimAllMovements(self):
        chordIndices = self.allMovements.keys()
        chordIndices.sort()
        chordIndices.reverse()
        
        for chordIndex in chordIndices:
            try:
                previousMovements = self.allMovements[chordIndex - 1] 
                currentMovements = self.allMovements[chordIndex]
                eliminated = []
                for possibleIndex in currentMovements.keys():
                    if len(currentMovements[possibleIndex]) == 0:
                        del currentMovements[possibleIndex]
                        eliminated.append(possibleIndex)
                for possibleIndex in previousMovements.keys():
                    movements = previousMovements[possibleIndex]
                    for eliminatedIndex in eliminated:
                        if eliminatedIndex in movements:
                            movements.remove(eliminatedIndex)
            except KeyError:
                if chordIndex == 0:
                    currentMovements = self.allMovements[chordIndex]
                    for possibleIndex in currentMovements.keys():
                        if len(currentMovements[possibleIndex]) == 0:
                            del currentMovements[possibleIndex]
                else:
                    raise FiguredBassException("Error trimming all movements.")
        
             
    def showRandomSolutions(self, amount):
        bassLine = stream.Part()
        rightHand = stream.Part()
        s = stream.Part()
        ts = meter.TimeSignature(self.timeSig)
        s.insert(0, ts)
        numSharps = key.pitchToSharps(self.key, self.mode)
        ks = key.KeySignature(numSharps)
        bassLine.append(ks)
        rightHand.append(ks)
        
        for i in range(amount):
            print("\nProgression #" + str(i + 1))
            chordProg = self.getRandomChordProgression()
            for j in range(len(self.bassNotes)):
                givenChord = chordProg[j]
                
                bassNote = copy.deepcopy(self.bassNotes[j])                
                rhChord = chord.Chord([givenChord[0], givenChord[1], givenChord[2]])
                
                rhChord.quarterLength = bassNote.quarterLength
                
                bassLine.append(bassNote)
                rightHand.append(rhChord)
            
            rest1 = note.Rest()
            rest1.quarterLength = ts.totalLength
            rest2 = note.Rest()
            rest2.quarterLength = ts.totalLength
            bassLine.append(rest1)
            rightHand.append(rest2)

            printChordProgression(chordProg)
        
        s.insert(0, rightHand)
        s.insert(0, bassLine)
        
        s.show()
        
    def getRandomChordProgression(self):
        chordIndices = self.allMovements.keys()
        startIndices = self.allMovements[chordIndices[0]].keys()
        randomIndex = random.randint(0, len(startIndices) - 1)
        numberProgression = []
        prevChordIndex = startIndices[randomIndex]
        numberProgression.append(prevChordIndex)
        
        for chordIndex in chordIndices:
            nextIndices = self.allMovements[chordIndex][prevChordIndex]
            randomIndex = random.randint(0, len(nextIndices) - 1)
            nextChordIndex = nextIndices[randomIndex]
            numberProgression.append(nextChordIndex)
            prevChordIndex = nextChordIndex
        
        chordProgression = self._translateNumberProgression(numberProgression)
        return chordProgression 
           
    def _translateNumberProgression(self, numberProgression):
        chords = []
        for chordIndex in self.allChords:
            elementIndex = numberProgression[chordIndex]
            chords.append(self.allChords[chordIndex][elementIndex])
            
        return chords

    def getNumSolutions(self):
        pass
    
    def findSolutionsWithConstraint(self, voicePart, pitchList):
        pass
    
    def _findPossibleStartingChords(self, firstBass, firstNotation = ''):
        '''
        OMIT_FROM_DOCS
        >>> from music21 import *
        >>> from music21.figuredBass import realizer
        >>> fb = realizer.FiguredBass('3/2', 'A', 'minor')
        >>> fb.octaveLimit = 3
        >>> fb._findPossibleStartingChords(Pitch('A2'), '')
        [[E3, C3, A2, A2], [E3, C3, C3, A2], [E3, E3, C3, A2], [A3, E3, C3, A2]]
        '''
        possibilities = []
        pitchesAboveBass = self.scale.getPitchesAboveBassPitchFromNotation(firstBass, firstNotation, self.octaveLimit)
        sortedPitchesAboveBass = sortPitchListByDistanceToPitch(firstBass, pitchesAboveBass)
        
        #soprano >= alto >= tenor >= bass
        for i in range(len(sortedPitchesAboveBass)):
            firstTenor = sortedPitchesAboveBass[i]
            for j in range(i, len(sortedPitchesAboveBass)):
                firstAlto = sortedPitchesAboveBass[j]
                for k in range(j, len(sortedPitchesAboveBass)):
                    firstSoprano = sortedPitchesAboveBass[k]
                    possibilities.append([firstSoprano, firstAlto, firstTenor, firstBass])
        
        pitchNamesInChord = self.scale.getPitchNamesFromNotation(firstBass, firstNotation)
        allowedPossibilities = []
        
        for startingChord in possibilities:
            ruleCheckA = self.rules.checkChord(startingChord, pitchNamesInChord)
            if ruleCheckA:
                allowedPossibilities.append(startingChord)
            
        return allowedPossibilities

    def _findNextPossibilities(self, prevChords, nextBass, nextNotation = ''):
        '''
        >>> fb = FiguredBass('3/2', 'C')
        >>> prevChords = [[Pitch('C4'), Pitch('G3'), Pitch('E3'), Pitch('C3')]]
        >>> nextBass = pitch.Pitch('D3')
        >>> nextNotation = '6'
        >>> fb.rules.verbose = False
        >>> fb._findNextPossibilities(prevChords, nextBass, nextNotation)
        ([[B3, F3, D3, D3], [B3, F3, F3, D3], [F4, B3, F3, D3], [B3, B3, F3, D3]], {0: [0, 1, 2, 3]})
        '''
        nextChords = []
        prevMovements = {}
        potentialPitchList = self.scale.getPitchesAboveBassPitchFromNotation(nextBass, nextNotation, self.octaveLimit)
        pitchesInNextChord = self.scale.getPitchNamesFromNotation(nextBass, nextNotation)
        prevChordIndex = 0
        for prevChord in prevChords:
            nextPossibilities = allChordsToMoveTo(prevChord, potentialPitchList, nextBass, self.rules)
            movements = []
            for nextChord in nextPossibilities:
                ruleCheckA = self.rules.checkChord(nextChord, pitchesInNextChord)
                ruleCheckB = self.rules.checkChords(prevChord, nextChord)
                if ruleCheckA and ruleCheckB:
                    try:
                        movements.append(nextChords.index(nextChord))
                    except ValueError:
                        nextChords.append(nextChord)
                        movements.append(len(nextChords) - 1)
            prevMovements[prevChordIndex] = movements
            prevChordIndex += 1
            
        return (nextChords, prevMovements)
    
        
#Helper Methods
def pitchesToMoveTo(voicePairs, newPitchA, potentialPitchList, rules = None):
    '''
    This method finds solutions to a particular voice-leading problem given some constraints.
    
    It starts with two lists, L and M, and a single pitch P.
    
    L is a list of tuples where each tuple consists of two pitches that represent
    the motion of a single voice (for instance if C3 moves to D3 at the same time G4 moves
    to F4 then L = [ (Pitch('C3'), Pitch('D3')), (Pitch('G4'), Pitch('F4')) ]
    
    P is the Pitch that another voice (not one of the ones in L) starts on.
    
    M is a list of Pitches that the voice of P might possibly move to.
    
    This method returns a list that is a subset of M where if P moved to any of these
    Pitches none of our voice-leading constraints would be broken.  Does not check harmony

    So given L above, if P is C4 and M is [C4, B-3, A3, D4] then this method would
    return [C4, A3]

    Takes a rules.Rules() object that is used to check the voiceleading.
    
        
    >>> from music21 import *
    >>> from music21.figuredBass import rules
    >>> defaultRules = rules.Rules()
    >>> bassPitches = (pitch.Pitch('C3'), pitch.Pitch('D3'))
    >>> tenorPitchA = pitch.Pitch('G3')
    >>> potentialTenorPitchB = [pitch.Pitch('A3'), pitch.Pitch('F3'), pitch.Pitch('B3'), pitch.Pitch('D4')]
    >>> pitchesToMoveTo([bassPitches], tenorPitchA, potentialTenorPitchB, defaultRules) # Moving to A3 == Parallel fifths
    [F3, B3, D4]
    >>> tenorPitchA = pitch.Pitch('C4')
    >>> pitchesToMoveTo([bassPitches], tenorPitchA, potentialTenorPitchB, defaultRules) # Moving to D4 == Parallel octaves
    [A3, F3, B3]
    >>> pitchesToMoveTo([bassPitches], tenorPitchA, potentialTenorPitchB)
    [A3, F3, B3, D4]
    '''
    newPitchList = []
    if rules == None:
        return potentialPitchList
    for newPitchB in potentialPitchList:
        isGood = True
        for (pitchA, pitchB) in voicePairs:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA, pitchB, newPitchA, newPitchB)
            if not rules.checkVoiceLeading(vlq):
                isGood = False
                break
        if isGood:
            newPitchList.append(newPitchB)
            
    return newPitchList

def allChordsToMoveTo(prevChord, potentialPitchList, nextBass = None, rules = None):
    '''
    >>> from music21 import *
    >>> defaultRules = rules.Rules()
    >>> prevBass = pitch.Pitch('C3')
    >>> prevTenor = pitch.Pitch('E3')
    >>> prevAlto = pitch.Pitch('G3')
    >>> prevChord = [prevAlto, prevTenor, prevBass] #SATB assumed
    >>> potentialPitchList = [Pitch('D3'), Pitch('F3'), Pitch('B3')]
    >>> nextBass = pitch.Pitch('D3')
    >>> allChordsToMoveTo(prevChord, potentialPitchList, nextBass, defaultRules)
    [[F3, D3, D3], [B3, D3, D3], [F3, F3, D3], [B3, F3, D3]]
    '''
    prevChord.reverse()
    allChords = []
    voicePairDict = {}
    for voiceIndex in range(len(prevChord)):
        voicePairDict[voiceIndex] = []
    pitchList = {}
    if not nextBass == None:
        bassPair = (prevChord[0], nextBass)
        voicePairDict[0].append([bassPair])
    else:
        for givenPitch in potentialPitchList:
            bassPair = (prevChord[0], givenPitch)
            voicePairDict[0].append([bassPair])
    
    for voiceIndex in range(1, len(prevChord)):
        for prevVoicePairList in voicePairDict[voiceIndex - 1]:
            prevPitch = prevChord[voiceIndex]
            nextPitchList = pitchesToMoveTo(prevVoicePairList, prevChord[voiceIndex], potentialPitchList, rules)
            for nextPitch in nextPitchList:
                nextVoicePair = (prevPitch, nextPitch)
                voicePairDict[voiceIndex].append(prevVoicePairList + [nextVoicePair])
    
    for voicePairList in voicePairDict[len(prevChord) - 1]:
        potentialChord = []
        for (prevPitch, nextPitch) in voicePairList:
            potentialChord.append(nextPitch)
        potentialChord.reverse()
        allChords.append(potentialChord)
    
    prevChord.reverse() #Undo the initial reverse
    
    return allChords
        
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
    pitchZero = realizerScale.convertToPitch(pitchZero)
    pitchZeroPs = pitchZero.ps
    newList = []
    for pitchOne in pitchList:
        pitchOne = realizerScale.convertToPitch(pitchOne)
        pitchOnePs = pitchOne.ps
        distance = abs(pitchOnePs - pitchZeroPs)
        newList.append((distance, pitchOne))
    newList.sort()
    sortedList = []
    for (distance, pitchOne) in newList:
        sortedList.append(pitchOne)
    return sortedList

def printChordProgression(chordProgression):
    sopranoLine = ""
    altoLine = ""
    tenorLine = ""
    bassLine = ""
    for chord in chordProgression:
        sopranoNote = chord[0]
        sopranoLine += str(chord[0]) + "\t"
        altoLine += str(chord[1]) + "\t"
        tenorLine += str(chord[2]) + "\t"
        bassLine += str(chord[3]) + "\t"
    
    print(sopranoLine)
    print(altoLine)
    print(tenorLine)
    print(bassLine)
    
    
class FiguredBassException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

