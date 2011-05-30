#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizer.py
# Purpose:      music21 class to define a figured bass line, consisting of notes
#                and figures in a given key.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import collections
import copy
import itertools
import music21
import random
import unittest

from music21 import chord
from music21 import clef
from music21 import key
from music21 import meter
from music21 import note
from music21 import stream
from music21.figuredBass import notation
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import segment

def figuredBassFromStream(streamPart):
    '''
    Takes a music21.stream Part (or another music21.stream Stream subclass) 
    and returns a FiguredBass object whose bass notes have Notations taken 
    from the lyrics in the source stream. This method along with the solve 
    method provide the easiest way of converting from a notated version of 
    a figured bass (such as in a MusicXML file) to a realized version of the 
    same line.
    
    >>> from music21 import tinyNotation
    >>> from music21.figuredBass import realizer
    >>> s = tinyNotation.TinyNotationStream('C4 D8_6 E8_6 F4 G4_7 C1', '4/4')
    >>> fb = realizer.figuredBassFromStream(s)
    >>> fbRules = rules.Rules()
    >>> fbRules.partMovementLimits = [(1,4)] #Soprano pitch movements limited to 4 semitones (M3) 
    >>> fbRealization = fb.realize(fbRules)
    >>> fbRealization.getNumSolutions()
    127
    >>> #_DOCS_SHOW fbRealization.generateRandomRealizations(20).show()
    '''
    sf = streamPart.flat
    sfn = sf.notes
    
    keyList = sf.getElementsByClass(key.Key)
    myKey = None
    if len(keyList) == 0:
        keyList = sf.getElementsByClass(key.KeySignature)
        if len(keyList) == 0:
            myKey = key.Key('C')
        else:
            if keyList[0].pitchAndMode[1] is None:
                mode = 'major'
            else:
                mode = keyList[0].pitchAndMode[1]
            myKey = key.Key(keyList[0].pitchAndMode[0], mode)
    else:
        myKey = keyList[0]

    tsList = sf.getElementsByClass(meter.TimeSignature)
    if len(tsList) == 0:
        ts = meter.TimeSignature('4/4')
    else:
        ts = tsList[0]
    
    fb = FiguredBassLine(myKey, ts)
    fb.addNotationAsLyrics = False
    
    for n in sfn:
        if len(n.lyrics) > 0:
            annotationString = ", ".join([x.text for x in n.lyrics])
            fb.addElement(n, annotationString)
        else:
            fb.addElement(n)
    
    return fb

figuredBassFromStreamPart = figuredBassFromStream

def addLyricsToBassNote(bassNote, notationString):
    '''
    Takes in a bassNote and a corresponding notationString as arguments. 
    Adds the parsed notationString as lyrics to the bassNote, which is 
    useful when displaying the figured bass in external software.
    '''
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

class FiguredBassLine(object):
    '''
    '''
    def __init__(self, inKey = key.Key('C'), inTime = meter.TimeSignature('4/4')):
        self.inKey = inKey
        self.inTime = inTime
        self.fbScale = realizerScale.FiguredBassScale(inKey.pitchFromDegree(1), inKey.mode)
        self.fbList = []
        self.addNotationAsLyrics = True
    
    def addElement(self, bassNote, notationString = ''):
        self.fbList.append((bassNote, notationString))
        if self.addNotationAsLyrics:
            addLyricsToBassNote(bassNote, notationString)
    
    def generateBassLine(self):
        bassLine = stream.Part()
        bassLine.append(copy.deepcopy(self.inTime))
        bassLine.append(key.KeySignature(self.inKey.sharps))

        bassLine.append(clef.BassClef())
        for (bassNote, notationString) in self.fbList:
            bassLine.append(bassNote)
            
        return bassLine
    
    def realize(self, fbRules = rules.Rules()):
        segmentList = []
        for (bassNote, notationString) in self.fbList:
            correspondingSegment = segment.Segment(self.fbScale, bassNote, notationString, fbRules)
            segmentList.append(correspondingSegment)

        for segmentIndex in range(len(segmentList) - 1):
            segmentA = segmentList[segmentIndex]
            segmentB = segmentList[segmentIndex + 1]
            correctAB = segmentA.allCorrectConsecutivePossibilities(segmentB)
            segmentA.movements = collections.defaultdict(list)
            listAB = list(correctAB)
            for (possibA, possibB) in listAB:
                segmentA.movements[possibA].append(possibB)

        self.trimAllMovements(segmentList)
        return Realization(segmentList, self.inKey, self.inTime)
        
    def trimAllMovements(self, segmentList):
        segmentList.reverse()
        for segmentIndex in range(1, len(segmentList) - 1):
            movementsAB = segmentList[segmentIndex + 1].movements
            movementsBC = segmentList[segmentIndex].movements
            eliminated = []
            for (possibB, possibCList) in movementsBC.items():
                if len(possibCList) == 0:
                    del movementsBC[possibB]
            for (possibA, possibBList) in movementsAB.items():
                movementsAB[possibA] = list(itertools.ifilter(lambda possibB: movementsBC.has_key(possibB), possibBList))
                
        for (possibA, possibBList) in movementsAB.items():
            if len(possibBList) == 0:
                del movementsAB[possibA]
                
        segmentList.reverse()
        return True


class Realization(object):
    def __init__(self, segmentList, inKey, inTime):
        self.segmentList = segmentList
        self.inKey = inKey
        self.inTime = inTime
        self.keySig = key.KeySignature(self.inKey.sharps)
        self.keyboardStyleOutput = True

    def getNumSolutions(self):
        self.segmentList.reverse()
        pathList = {}
        for segmentIndex in range(1, len(self.segmentList)):
            segmentA = self.segmentList[segmentIndex]
            newPathList = {}
            if len(pathList.keys()) == 0:
                for possibA in segmentA.movements.keys():
                    newPathList[possibA] = len(segmentA.movements[possibA])
            else:
                for possibA in segmentA.movements.keys():
                    prevValue = 0
                    for possibB in segmentA.movements[possibA]:
                        prevValue += pathList[possibB]
                    newPathList[possibA] = prevValue
            pathList = newPathList

        numSolutions = 0
        for possibA in pathList.keys():
            numSolutions += pathList[possibA]  
        self.segmentList.reverse()
        return numSolutions
    
    def getAllPossibilityProgressions(self):
        '''
        Returns all the valid possibility progressions.
        '''
        currMovements = self.segmentList[0].movements
        progressions = []
        for possibA in currMovements.keys():
            possibBList = currMovements[possibA]
            for possibB in possibBList:
                progressions.append([possibA, possibB])

        for segmentIndex in range(1, len(self.segmentList)-1):
            currMovements = self.segmentList[segmentIndex].movements
            for progIndex in range(len(progressions)):
                prog = progressions.pop(0)
                possibB = prog[-1]
                for possibC in currMovements[possibB]:
                    newProg = copy.copy(prog)
                    newProg.append(possibC)
                    progressions.append(newProg)
        
        return progressions
    
    def getRandomPossibilityProgression(self):
        '''
        Returns a random valid possibility progression.
        '''
        progression = []
        currMovements = self.segmentList[0].movements
        prevPossib = random.sample(currMovements.keys(), 1)[0]
        progression.append(prevPossib)
        
        for segmentIndex in range(0, len(self.segmentList)-1):
            currMovements = self.segmentList[segmentIndex].movements
            nextPossib = random.sample(currMovements[prevPossib], 1)[0]
            progression.append(nextPossib)
            prevPossib = nextPossib

        return progression

    def generateRealizationFromPossibilityProgression(self, possibilityProgression):
        '''
        Generates a solution as a stream.Score() given a possibility progression.        
        '''
        sol = stream.Score()
        
        bassLine = stream.Part()
        bassLine.append(copy.deepcopy(self.inTime))
        bassLine.append(copy.deepcopy(self.keySig))
        
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            sol.insert(0, rightHand)
            rightHand.append(copy.deepcopy(self.inTime))
            rightHand.append(copy.deepcopy(self.keySig))
    
            for segmentIndex in range(len(self.segmentList)):
                possibA = possibilityProgression[segmentIndex]
                bassNote = self.segmentList[segmentIndex].bassNote
                bassLine.append(copy.deepcopy(bassNote))  
                rhPitches = possibA[0:-1]                           
                rhChord = chord.Chord(rhPitches)
                rhChord.quarterLength = bassNote.quarterLength
                rightHand.append(rhChord)
            rightHand.insert(0, clef.TrebleClef()) 
        else: # Chorale-style output
            upperParts = []
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                sol.insert(0, fbPart)
                fbPart.append(copy.deepcopy(self.inTime))
                fbPart.append(copy.deepcopy(self.keySig))
                upperParts.append(fbPart)

            for segmentIndex in range(len(self.segmentList)):
                possibA = possibilityProgression[segmentIndex]
                bassNote = self.segmentList[segmentIndex].bassNote
                bassLine.append(copy.deepcopy(bassNote))  

                for partNumber in range(len(possibA) - 1):
                    n1 = note.Note(possibA[partNumber])
                    n1.quarterLength = bassNote.quarterLength
                    upperParts[partNumber].append(n1)
                    
            for upperPart in upperParts:
                upperPart.insert(0, upperPart.bestClef(True)) 
                              
        bassLine.insert(0, clef.BassClef())             
        sol.insert(0, bassLine)
        return sol

    def generateAllRealizations(self):
        allSols = stream.Score()
        bassLine = stream.Part()
        possibilityProgressions = self.getAllPossibilityProgressions()
        if len(possibilityProgressions) == 0:
            raise FiguredBassLineException("zero realizations")
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            allSols.insert(0, rightHand)
            
            for possibilityProgression in possibilityProgressions:
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                rightHand.append(copy.deepcopy(self.inTime))
                rightHand.append(copy.deepcopy(self.keySig))
                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))  
                    rhPitches = possibA[0:-1]                           
                    rhChord = chord.Chord(rhPitches)
                    rhChord.quarterLength = bassNote.quarterLength
                    rightHand.append(rhChord)
                rightHand.insert(0, clef.TrebleClef())
        else: # Chorale-style output
            upperParts = []
            possibilityProgression = self.getRandomPossibilityProgression()
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                allSols.insert(0, fbPart)
                upperParts.append(fbPart)
                
            for possibilityProgression in possibilityProgressions:
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                for upperPart in upperParts:
                    upperPart.append(copy.deepcopy(self.inTime))
                    upperPart.append(copy.deepcopy(self.keySig))

                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))
                    for partNumber in range(len(possibA) - 1):
                        n1 = note.Note(possibA[partNumber])
                        n1.quarterLength = bassNote.quarterLength
                        upperParts[partNumber].append(n1)
                        
                for upperPart in upperParts:
                    upperPart.insert(0, upperPart.bestClef(True)) 
  
        bassLine.insert(0, clef.BassClef())
        allSols.insert(0, bassLine)
        return allSols        

    def generateRandomRealization(self):
        '''
        Generates a random solution as a stream.Score()
        '''
        return self.generateRandomRealizations(1)

    def generateRandomRealizations(self, amountToShow = 20):
        if amountToShow > self.getNumSolutions():
            return self.generateAllRealizations()
        allSols = stream.Score()
        bassLine = stream.Part()
        
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            allSols.insert(0, rightHand)
            
            for solutionCounter in range(amountToShow):
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                rightHand.append(copy.deepcopy(self.inTime))
                rightHand.append(copy.deepcopy(self.keySig))
                possibilityProgression = self.getRandomPossibilityProgression()
                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))  
                    rhPitches = possibA[0:-1]                           
                    rhChord = chord.Chord(rhPitches)
                    rhChord.quarterLength = bassNote.quarterLength
                    rightHand.append(rhChord)
                rightHand.insert(0, clef.TrebleClef()) 
        else: # Chorale-style output
            upperParts = []
            possibilityProgression = self.getRandomPossibilityProgression()
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                allSols.insert(0, fbPart)
                upperParts.append(fbPart)
                
            for solutionCounter in range(amountToShow):
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                for upperPart in upperParts:
                    upperPart.append(copy.deepcopy(self.inTime))
                    upperPart.append(copy.deepcopy(self.keySig))

                possibilityProgression = self.getRandomPossibilityProgression()
                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))
                    for partNumber in range(len(possibA) - 1):
                        n1 = note.Note(possibA[partNumber])
                        n1.quarterLength = bassNote.quarterLength
                        upperParts[partNumber].append(n1)
                        
                for upperPart in upperParts:
                    upperPart.insert(0, upperPart.bestClef(True)) 
  
        bassLine.insert(0, clef.BassClef())
        allSols.insert(0, bassLine)
        return allSols        

         
class FiguredBassLineException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof