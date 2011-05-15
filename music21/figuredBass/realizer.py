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
from music21.figuredBass import part
from music21.figuredBass import notation

MIN_PITCH = pitch.Pitch('C1')
MAX_PITCH = pitch.Pitch('B5')

def figuredBassFromStreamPart(streamPart, partList = None, takeFromNotation = False):
    '''
    takes in a Stream part that has figures in the lyrics and
    returns a realizer.FiguredBass object
    
    >>> from music21 import *
    >>> s = tinyNotation.TinyNotationStream('C4 D8_6 E8_6 F4 G4_7 c1', '4/4')
    >>> fb = figuredBass.realizer.figuredBassFromStreamPart(s)
    >>> fb.realize()
    >>> fb.showRandomRealizations(20)
    '''
    if partList is None:
        part1 = part.Part(1,2)
        part2 = part.Part(2)
        part3 = part.Part(3)
        part4 = part.Part(4)
    
        partList = [part1, part2, part3, part4]
    
    sf = streamPart.flat
    sfn = sf.notes
    keyList = sf.getElementsByClass(key.KeySignature)
    if len(keyList) == 0:
        mykey = key.Key('C')
    else:
        mykey = keyList[0]

    tsList = sf.getElementsByClass(meter.TimeSignature)
    if len(tsList) == 0:
        ts = meter.TimeSignature('4/4')
    else:
        ts = tsList[0]
    
    fb = FiguredBass(partList, str(ts), mykey.tonic, mykey.mode)
    fb.addLyrics = False
    
    for n in sfn:
        if n.lyric != "" and n.lyric is not None:
            fb.addElement(n, n.lyric)
        else:
            fb.addElement(n)
    
    return fb

def addLyricsToBassNote(bassNote, notationString):
    n = notation.Notation(notationString)
    if len(n.figureStrings) == 0:
        return
    maxLength = 0
    for fs in n.figureStrings:
        if len(fs) > maxLength:
            maxLength = len(fs)
    for fs in n.figureStrings:
        spacesInFront = ''
        for space in range(maxLength - len(fs)):
            spacesInFront += ' '
        bassNote.addLyric(spacesInFront + fs, applyRaw = True)

class FiguredBass(object):
    def __init__(self, partList = None, timeSigString = '4/4', keyString = 'C', modeString = 'major'):
        '''
        
        '''
        if partList is None:
            part1 = part.Part(1,2)
            part2 = part.Part(2)
            part3 = part.Part(3)
            part4 = part.Part(4)

            partList = [part1, part2, part3, part4]

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
        self.fbScale = realizerScale.FiguredBassScale(keyString, modeString)
        self.fbParts = partList
        self.fbRules = rules.Rules()
        self.addNotationAsLyrics = True
        
        #Contains fb solutions
        self.isRealized = False
        self.allSegments = []
        self.lastSegment = None
        
    def addElement(self, bassNote, notationString = ''):
        if self.addNotationAsLyrics:
            addLyricsToBassNote(bassNote, notationString)
        self.bassNotes.append(bassNote)
        self.bassLine.append(bassNote)
        self.figuredBassList.append((bassNote, notationString))

    def realize(self):
        startTime = time.time()
        self.isRealized = False
        self.allSegments = []
        self.lastSegment = None
        
        (startBass, startNotationString) = self.figuredBassList[0]
        #print("Finding starting possibilities for: " + str((startBass.pitch, startNotationString)))
        a1 = segment.StartSegment(self.fbScale, self.fbParts, self.fbRules, startBass, startNotationString)
        self.allSegments.append(a1)
        self.lastSegment = a1
            
        for fbIndex in range(1, len(self.figuredBassList)):
            (nextBass, nextNotationString) = self.figuredBassList[fbIndex]
            #print("Finding all possibilities for: " + str((nextBass.pitch, nextNotationString)))
            c1 = segment.MiddleSegment(self.fbScale, self.fbParts, self.fbRules, self.lastSegment, nextBass, nextNotationString)
            self.allSegments.append(c1)
            self.lastSegment = c1
       
        #print("Trimming movements...")
        self.lastSegment.trimAllMovements()
        numRealizations = self.lastSegment.getNumSolutions()
        #if numRealizations <= 200000:
            #numberProgressions = self.getAllIndexProgressions()
            #print("Number of complete realizations, as calculated empirically: " + str(len(numberProgressions)) + ".")
        #print("Solving complete. Number of complete realizations, as calculated by path counting: " + str(numRealizations) + ".\n")
        endTime = time.time()
        minutesElapsed = int((endTime - startTime) / 60)
        secondsElapsed = round((endTime - startTime) % 60)
        print("Time elapsed: " + str(minutesElapsed) + " minutes " + str(secondsElapsed) + " seconds.")
        self.isRealized = True
      
    # METHODS FOR GENERATION OF INDEX PROGRESSIONS
    # --------------------------------------------
    def getAllIndexProgressions(self):
        if len(self.allSegments) <= 1:
            raise FiguredBassException("One segment or less not enough for progression generator..")
        currMovements = self.allSegments[0].nextMovements
        progressions = []
        for prevIndex in currMovements.keys():
            allNextIndices = currMovements[prevIndex]
            for nextIndex in allNextIndices:
                progressions.append([prevIndex, nextIndex])

        for mSegmentIndex in range(1, len(self.allSegments)-1):
            currMovements = self.allSegments[mSegmentIndex].nextMovements
            progLength = len(progressions)
            for progIndex in range(progLength):
                prog = progressions.pop(0)
                prevIndex = prog[-1]
                for nextIndex in currMovements[prevIndex]:
                    newProg = copy.copy(prog)
                    newProg.append(nextIndex)
                    progressions.append(newProg)
        
        return progressions
    
    def getRandomIndexProgression(self):
        if len(self.allSegments) <= 1:
            raise FiguredBassException("One segment or less not enough for progression generator.")
        indexProgression = []
        currMovements = self.allSegments[0].nextMovements
        prevChordIndex = random.sample(currMovements.keys(), 1)[0]
        indexProgression.append(prevChordIndex)

        for mSegmentIndex in range(0, len(self.allSegments)-1):
            currMovements = self.allSegments[mSegmentIndex].nextMovements
            nextChordIndex = random.sample(currMovements[prevChordIndex], 1)[0]
            indexProgression.append(nextChordIndex)
            prevChordIndex = nextChordIndex

        return indexProgression
        
    # METHODS FOR GENERATION OF POSSIBILITY PROGRESSIONS
    # --------------------------------------------------
    def indexToPossibilityProgression(self, indexProgression):
        possibilityProgression = []
        
        for segmentIndex in range(len(self.allSegments)):
            elementIndex = indexProgression[segmentIndex]
            possibilityProgression.append(self.allSegments[segmentIndex].possibilities[elementIndex])
            
        return possibilityProgression
   
    def getAllPossibilityProgressions(self):
        possibilityProgressions = []
        indexProgressions = self.getAllIndexProgressions()

        for indexProgression in indexProgressions:
            possibilityProgression = self.indexToPossibilityProgression(indexProgression)
            possibilityProgressions.append(possibilityProgression)
        
        return possibilityProgressions
    
    def getRandomPossibilityProgression(self):
        indexProgression = self.getRandomIndexProgression()
        possibilityProgression = self.indexToPossibilityProgression(indexProgression)
        return possibilityProgression

    # METHODS FOR MUSIC21.STREAM SCORE GENERATION FROM POSSILITY PROGRESSIONS
    # -----------------------------------------------------------------------
    def generateRealizationFromPossibilityProgression(self, possibilityProgression):
        '''
        Generates a solution as a stream.Score() given a chord progression
        
        bass line is taken from the figured bass object, but is checked against
        the Possibility progression for consistency.
        '''
        sol = stream.Score()
        rightHand = stream.Part()
        rightHand.append(copy.deepcopy(self.ts))
        rightHand.append(copy.deepcopy(self.ks))

        v0 = self.fbParts[0]
        
        for j in range(len(possibilityProgression)):
            givenPossib = possibilityProgression[j]
            bassNote = self.bassNotes[j]

            if givenPossib[v0] != bassNote.pitch:
                raise FiguredBassException("Chord progression possibility doesn't match up with bass line.")
        
            rhPitches = []
            for k in range(1, len(self.fbParts)):
                v1 = self.fbParts[k]
                rhPitches.append(copy.copy(givenPossib[v1]))
                             
            rhChord = chord.Chord(rhPitches)
            rhChord.quarterLength = bassNote.quarterLength
            rightHand.append(rhChord)
    
        sol.insert(0, rightHand)
        sol.insert(0, copy.deepcopy(self.bassLine))
        sol.append(bar.Barline('light-heavy'))

        return sol   

    def generateAllRealizations(self):
        allSols = stream.Score()
        part1 = stream.Part()
        part2 = stream.Part()
        allSols.insert(0, part1)
        allSols.insert(0, part2)
        possibilityProgressions = self.getAllPossibilityProgressions()
        for possibilityProgression in possibilityProgressions:
            sol = self.generateRealizationFromPossibilityProgression(possibilityProgression)
            for m in sol.parts[0]:
                part1.append(m)
            for m in sol.parts[1]:
                part2.append(m)
        
        return allSols

    def generateRandomRealization(self):
        '''
        Generates a random solution as a stream.Score()
        '''
        possibilityProgression = self.getRandomPossibilityProgression()
        return self.generateRealizationFromPossibilityProgression(possibilityProgression)
      
    def generateRandomRealizations(self, amountToShow = 20):
        if amountToShow > self.lastSegment.getNumSolutions():
            return self.generateAllRealizations()
        
        allSols = stream.Score()
        part1 = stream.Part()
        part2 = stream.Part()
        allSols.insert(0, part1)
        allSols.insert(0, part2)
        for solutionCounter in range(amountToShow):
            sol = self.generateRandomRealization()
            for m in sol.parts[0]:
                part1.append(m)
            for m in sol.parts[1]:
                part2.append(m)
            
        return allSols
    
    # METHODS FOR DISPLAY OF MUSIC21.STREAM SCORE GENERATION FROM POSSIBILITY PROGRESSIONS
    # ------------------------------------------------------------------------------------
    def showRandomRealization(self):
        self.generateRandomRealization().show()    
      
    def showAllRealizations(self, showAsText = False):
        if showAsText:
            self.generateAllRealizations().show('text')
        else:
            self.generateAllRealizations().show()
        
    def showRandomRealizations(self, amountToShow = 20, showAsText = False):
        if showAsText:        
            self.generateRandomRealizations(amountToShow).show('text')
        else:
            self.generateRandomRealizations(amountToShow).show()

    # METHOD FOR CONSOLE PRINTING OF POSSIBILITY PROGRESSION
    # ------------------------------------------------------
    def printpossibilityProgression(self, possibilityProgression):
        linesToPrint = []
        for p in self.partList:
            partLine = p.label + ":\n"
            for possib in possibilityProgression:
                partLine += str(possib[p.label]) + "\t"
            linesToPrint.append(partLine)
        linesToPrint.reverse()
        for partLine in linesToPrint:
            print partLine
        
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


