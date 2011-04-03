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

from music21.figuredBass import segment
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import voice

class FiguredBass(object):
    def __init__(self, voiceList, timeSig, key, mode = 'major'):
        '''
        '''
        self.timeSig = timeSig
        self.key = key
        self.mode = mode
        self.maxPitch = pitch.Pitch('B5')
        self.figuredBassList = []
        self.bassNotes = []
        self.fbInfo = segment.Information(realizerScale.FiguredBassScale(key, mode), voiceList, rules.Rules())
        self.allSegments = []
        self.lastSegment = None
        
    def addElement(self, bassNote, notation = ''):
        self.bassNotes.append(bassNote)
        self.figuredBassList.append((bassNote, notation))

    def solve(self):
        startTime = time.time()
        (startBass, startNotation) = self.figuredBassList[0]
        print("Finding starting possibilities for: " + str((startBass.pitch, startNotation)))
        a1 = segment.StartSegment(self.fbInfo, startBass, startNotation)
        self.allSegments.append(a1)
        self.lastSegment = a1
            
        for fbIndex in range(1, len(self.figuredBassList)):
            (nextBass, nextNotation) = self.figuredBassList[fbIndex]
            print("Finding all possibilities for: " + str((nextBass.pitch, nextNotation)))
            c1 = segment.MiddleSegment(self.fbInfo, self.lastSegment, nextBass, nextNotation)
            self.allSegments.append(c1)
            self.lastSegment = c1
       
        print("Trimming movements...")
        self.lastSegment.trimAllMovements()
        numSolutions = self.lastSegment.getNumSolutions()
        if numSolutions <= 200000:
            numberProgressions = self.calculateAllNumberProgressions()
            print("Number of solutions, as calculated empirically: " + str(len(numberProgressions)) + ".")
        print("Solving complete. Number of solutions, as calculated by path counting: " + str(numSolutions) + ".\n")
        endTime = time.time()
        minutesElapsed = int((endTime - startTime) / 60)
        secondsElapsed = round((endTime - startTime) % 60)
        print("Time elapsed: " + str(minutesElapsed) + " minutes " + str(secondsElapsed) + " seconds.")
                
    def calculateAllNumberProgressions(self):
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

    def showRandomSolutions(self, amountToShow = 20):
        s = self.generateRandomSolutions(amountToShow)
        s.show()
        
    def generateRandomSolutions(self, amountToShow = 20):
        # TODO: If amountToShow > self.lastSegment.getNumSolutions(), then should return all solutions and that's it.
        # Also, if self.lastSegment.getNumSolutions() == 0, then should either raise an exception or just return without 
        # going into the for loop and print a warning to the user.
        bassLine = stream.Part()
        rightHand = stream.Part()
        s = stream.Score()
        ts = meter.TimeSignature(self.timeSig)
        numSharps = key.pitchToSharps(self.key, self.mode)
        ks = key.KeySignature(numSharps)
        s.insert(0, ts)
        s.insert(0, ks)
        
        for i in range(amountToShow):
            print("\nProgression #" + str(i + 1))
            chordProg = self.getRandomChordProgression()
            for j in range(len(self.bassNotes)):
                givenChord = chordProg[j]
                
                bassNote = copy.deepcopy(self.bassNotes[j])
                rhPitches = []
                
                for k in range(1, len(self.fbInfo.fbVoices)):
                    v1 = self.fbInfo.fbVoices[k]
                    rhPitches.append(copy.deepcopy(givenChord[v1.label]))
                                 
                rhChord = chord.Chord(rhPitches)
                rhChord.quarterLength = bassNote.quarterLength
                
                bassLine.append(bassNote)
                rightHand.append(rhChord)
                
            
            rest1 = note.Rest()
            rest1.quarterLength = ts.totalLength
            rest2 = note.Rest()
            rest2.quarterLength = ts.totalLength
            bassLine.append(rest1)
            rightHand.append(rest2)

            self.printChordProgression(chordProg)
        
        s.insert(0, rightHand)
        s.insert(0, bassLine)
        
        return s

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


