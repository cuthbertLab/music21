#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizer2.py
# Purpose:      music21 class which will find all valid solutions of a given figured bass
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import random
import copy
import time

from music21 import pitch
from music21 import note
from music21 import stream
from music21 import meter
from music21 import key
from music21 import chord
from music21 import bar

from music21.figuredBass import segment
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import voice
from music21.figuredBass import notation

MAX_PITCH = pitch.Pitch('B5')

class FiguredBass(object):
    def __init__(self, voiceList, timeSigString = '4/4', keyString = 'C', modeString = 'major'):
        '''
        '''
        self.keyString = keyString
        self.modeString = modeString
        self.timeSigString = timeSigString
        #Converted to music21 TimeSignature, KeySignature objects
        self.ts = meter.TimeSignature(self.timeSigString)
        _numSharps = key.pitchToSharps(self.keyString, self.modeString)
        self.ks = key.KeySignature(_numSharps)
        
        #fb bass notes, figures, bass line, other information
        self.figuredBassList = []
        self.bassNotes = []
        self.bassLine = stream.Part()
        self.bassLine.append(copy.deepcopy(self.ts))
        self.bassLine.append(copy.deepcopy(self.ks))
        self.maxPitch = MAX_PITCH
        self.fbInfo = segment.Information(realizerScale.FiguredBassScale(keyString, modeString), voiceList, rules.Rules())
        
        #Contains fb solutions
        self.allSegments = []
        self.lastSegment = None
        
    def addElement(self, bassNote, notationString = ''):
        self.bassNotes.append(bassNote)
        self.bassLine.append(bassNote)
        self.figuredBassList.append((bassNote, notationString))

    def solve(self):
        startTime = time.time()
        (startBass, startNotationString) = self.figuredBassList[0]
        print("Finding starting possibilities for: " + str((startBass.pitch, startNotationString)))
        a1 = segment.StartSegment(self.fbInfo, startBass, startNotationString)
        self.allSegments.append(a1)
        self.lastSegment = a1
            
        for fbIndex in range(1, len(self.figuredBassList)):
            (nextBass, nextNotationString) = self.figuredBassList[fbIndex]
            print("Finding all possibilities for: " + str((nextBass.pitch, nextNotationString)))
            c1 = segment.MiddleSegment(self.fbInfo, self.lastSegment, nextBass, nextNotationString)
            self.allSegments.append(c1)
            self.lastSegment = c1
       
        print("Trimming movements...")
        self.lastSegment.trimAllMovements()
        numSolutions = self.lastSegment.getNumSolutions()
        if numSolutions <= 200000:
            numberProgressions = self.getAllNumberProgressions()
            print("Number of solutions, as calculated empirically: " + str(len(numberProgressions)) + ".")
        print("Solving complete. Number of solutions, as calculated by path counting: " + str(numSolutions) + ".\n")
        endTime = time.time()
        minutesElapsed = int((endTime - startTime) / 60)
        secondsElapsed = round((endTime - startTime) % 60)
        print("Time elapsed: " + str(minutesElapsed) + " minutes " + str(secondsElapsed) + " seconds.")
                
    def getAllNumberProgressions(self):
        if len(self.allSegments) <= 1:
            raise FiguredBassException("One segment or less not enough for progression generator..")
        currMovements = self.allSegments[0].nextMovements
        progressions = []
        for prevIndex in currMovements.keys():
            allNextIndices = currMovements[prevIndex]
            for nextIndex in allNextIndices:
                progressions.append([prevIndex, nextIndex])

        for cSegmentIndex in range(1, len(self.allSegments)-1):
            currMovements = self.allSegments[cSegmentIndex].nextMovements
            progLength = len(progressions)
            for progIndex in range(progLength):
                prog = progressions.pop(0)
                prevIndex = prog[-1]
                for nextIndex in currMovements[prevIndex]:
                    newProg = copy.copy(prog)
                    newProg.append(nextIndex)
                    progressions.append(newProg)
        
        return progressions

    def numberToChordProgression(self, numberProgression):
        chords = []
        for segmentIndex in range(len(self.allSegments)):
            elementIndex = numberProgression[segmentIndex]
            chords.append(self.allSegments[segmentIndex].possibilities[elementIndex])
            
        return chords
   
    def getAllChordProgressions(self):
        chordProgressions = []
        numberProgressions = self.getAllNumberProgressions()

        for numberProgression in numberProgressions:
            chordProgression = self.numberToChordProgression(numberProgression)
            chordProgressions.append(chordProgression)
        
        return chordProgressions
    
    def getRandomChordProgression(self):
        if len(self.allSegments) <= 1:
            raise FiguredBassException("One segment or less not enough for progression generator.")
        numberProgression = []
        currMovements = self.allSegments[0].nextMovements
        prevChordIndex = random.sample(currMovements.keys(), 1)[0]
        numberProgression.append(prevChordIndex)

        for cSegmentIndex in range(0, len(self.allSegments)-1):
            currMovements = self.allSegments[cSegmentIndex].nextMovements
            nextChordIndex = random.sample(currMovements[prevChordIndex], 1)[0]
            numberProgression.append(nextChordIndex)
            prevChordIndex = nextChordIndex

        chordProgression = self.numberToChordProgression(numberProgression)
        return chordProgression

    def showRandomSolution(self):
        self.generateRandomSolution().show()
        
    def generateRandomSolution(self):
        '''
        Generates a random solution as a stream.Score()
        '''
        chordProgression = self.getRandomChordProgression()
        return self.generateSolutionFromChordProgression(chordProgression)
        
    def generateSolutionFromChordProgression(self, chordProgression):
        '''
        Generates a solution as a stream.Score() given a chord progression
        
        bass line is taken from the figured bass object, but is checked against
        the chord progression for consistency.
        '''
        sol = stream.Score()
        rightHand = stream.Part()
        rightHand.append(copy.deepcopy(self.ts))
        rightHand.append(copy.deepcopy(self.ks))

        v0 = self.fbInfo.fbVoices[0]
        
        for j in range(len(chordProgression)):
            givenPossib = chordProgression[j]
            bassNote = self.bassNotes[j]

            if givenPossib[v0.label] != bassNote.pitch:
                raise FiguredBassException("Chord progression possibility doesn't match up with bass line.")
        
            rhPitches = []
            for k in range(1, len(self.fbInfo.fbVoices)):
                v1 = self.fbInfo.fbVoices[k]
                rhPitches.append(copy.copy(givenPossib[v1.label]))
                             
            rhChord = chord.Chord(rhPitches)
            rhChord.quarterLength = bassNote.quarterLength
            rightHand.append(rhChord)
    
        sol.insert(0, rightHand)
        sol.insert(0, copy.deepcopy(self.bassLine))
        sol.append(bar.Barline('light-heavy'))

        return sol
      
    def showAllSolutions(self, showAsText = False):
        if showAsText:
            self.generateAllSolutions().show('text')
        else:
            self.generateAllSolutions().show()
        
    def showRandomSolutions(self, amountToShow = 20, showAsText = False):
        if showAsText:        
            self.generateRandomSolutions(amountToShow).show('text')
        else:
            self.generateRandomSolutions(amountToShow).show()
    
    def generateAllSolutions(self):
        allSols = stream.Score()
        part1 = stream.Part()
        part2 = stream.Part()
        allSols.insert(0, part1)
        allSols.insert(0, part2)
        chordProgressions = self.getAllChordProgressions()
        for chordProgression in chordProgressions:
            sol = self.generateSolutionFromChordProgression(chordProgression)
            for m in sol.parts[0]:
                part1.append(m)
            for m in sol.parts[1]:
                part2.append(m)
        
        return allSols
    
    def generateRandomSolutions(self, amountToShow = 20):
        if amountToShow > self.lastSegment.getNumSolutions():
            return self.generateAllSolutions()
        
        allSols = stream.Score()
        part1 = stream.Part()
        part2 = stream.Part()
        allSols.insert(0, part1)
        allSols.insert(0, part2)
        for solutionCounter in range(amountToShow):
            sol = self.generateRandomSolution()
            for m in sol.parts[0]:
                part1.append(m)
            for m in sol.parts[1]:
                part2.append(m)
            
        return allSols
        
    def printChordProgression(self, chordProgression):
        linesToPrint = []
        for v in self.fbInfo.fbVoices:
            voiceLine = v.label + ":\n"
            for chord in chordProgression:
                voiceLine += str(chord[v.label]) + "\t"
            linesToPrint.append(voiceLine)
        linesToPrint.reverse()
        for voiceLine in linesToPrint:
            print voiceLine
        
class FiguredBassException(music21.Music21Exception):
    pass

#------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


