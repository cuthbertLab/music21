#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      music21 class for doing the actual solving of a figured bass
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import copy
import random

from music21 import note

from music21.figuredBass import rules
from music21.figuredBass import possibility
from music21.figuredBass import realizerScale
from music21.figuredBass import voice

class Segment:
    def __init__(self, fbInformation, bassNote, notation = ''):
        self.bassNote = bassNote
        self.notation = notation
        self.fbScale = fbInformation.fbScale
        self.fbVoices = fbInformation.fbVoices
        self.fbRules = fbInformation.fbRules
        self.pitchesAboveBass = self.fbScale.getPitches(self.bassNote.pitch, self.notation)
        self.pitchNamesInChord = self.fbScale.getPitchNames(self.bassNote.pitch, self.notation)
        self.nextMovements = {}
        self.nextSegment = None

    def resolve(self):
        raise SegmentException("Must specifically create PreviousSegment or NextSegment to call this method.")
    
    def allPossibilities(self):
        possibilities = []
        
        bassPossibility = possibility.Possibility()
        previousVoice = self.fbVoices[0]
        bassPossibility[previousVoice.label] = self.bassNote.pitch
        possibilities.append(bassPossibility)
        
        for voiceNumber in range(1, len(self.fbVoices)):
            oldLength = len(possibilities)
            currentVoice = self.fbVoices[voiceNumber]
            for oldPossibIndex in range(oldLength):
                oldPossib = possibilities.pop(0)
                validPitches = self.pitchesAboveBass
                for validPitch in validPitches:
                    newPossib = copy.copy(oldPossib)
                    newPossib[currentVoice.label] = validPitch
                    possibilities.append(newPossib)
                
            previousVoice = currentVoice
        
        return possibilities
    
    def correctPossibilities(self):
        '''
        Default rules:
        (1) No incomplete possibilities
        (2) Top voices within interval.Interval
        (3) Pitches in each voice within range
        (4) No voice crossing
        '''
        allPossibilities = self.allPossibilities()
        
        newPossibilities = []
        for possib in allPossibilities:
            if not possib.correctlyFormed(self.pitchNamesInChord, self.fbRules):
                continue
            if not possib.correctTessitura(self.fbVoices, self.fbRules):
                continue
            newPossibilities.append(possib)
        
        return newPossibilities
    
    def trimAllMovements(self, eliminated = []):
        '''
        Trims all movements beginning at the segment it is
        called upon and moving backwards, stopping at the
        PreviousSection. Intended to be called by the last
        segment to trim the movements of a fbLine.
        '''
        for possibleIndex in self.nextMovements.keys():
            movements = self.nextMovements[possibleIndex]
            for eliminatedIndex in eliminated:
                if eliminatedIndex in movements:
                    movements.remove(eliminatedIndex)

        newlyEliminated = []
        for possibleIndex in self.nextMovements.keys():
            if len(self.nextMovements[possibleIndex]) == 0:
                del self.nextMovements[possibleIndex]
                newlyEliminated.append(possibleIndex)
        try:
            self.prevSegment.trimAllMovements(newlyEliminated)            
        except AttributeError:
            pass
        
    def getNumSolutions(self, pathList = {}):
        '''
        Obtains the number of solutions up to and including the given segment,
        by calculating the total number of paths, the sum of paths to each
        possibility in the given segment. Intended to be called by the last
        segment to return the total number of solutions to a fbLine, but could
        conceivably be used in other ways as well.
        '''
        newPathList = {}
        if len(pathList.keys()) == 0:
            for possibleIndex in self.nextMovements.keys():
                newPathList[possibleIndex] = len(self.nextMovements[possibleIndex])
        else:
            for prevIndex in self.nextMovements.keys():
                prevValue = 0
                for nextIndex in self.nextMovements[prevIndex]:
                    prevValue += pathList[nextIndex]
                newPathList[prevIndex] = prevValue
        
        try:
            return self.prevSegment.getNumSolutions(newPathList)
        except AttributeError:
            numSolutions = 0
            for possibleIndex in newPathList.keys():
                numSolutions += newPathList[possibleIndex]
            return numSolutions
    
                
class PreviousSegment(Segment):
    def __init__(self, fbInformation, bassNote, notation = ''):
        Segment.__init__(self, fbInformation, bassNote, notation)
        self.resolve()

    def resolve(self):
        # Imitates _findPossibleStartingChords from realizer.py
        self.possibilities = self.correctPossibilities()
    
class NextSegment(Segment):
    def __init__(self, fbInformation, prevSegment, bassNote, notation = ''):
        Segment.__init__(self, fbInformation, bassNote, notation)
        self.prevSegment = prevSegment
        self.resolve()
    
    def resolve(self):
        # Imitates _findNextPossibilities from realizer.py
        prevPossibilities = self.prevSegment.possibilities
        nextPossibilities = self.correctPossibilities()
            
        prevPossibIndex = 0
        for prevPossib in prevPossibilities:
            movements = []
            nextPossibIndex = 0
            for nextPossib in nextPossibilities:
                if self.checkVoiceLeading(prevPossib, nextPossib):
                    movements.append(nextPossibIndex)
                nextPossibIndex += 1
            self.prevSegment.nextMovements[prevPossibIndex] = movements
            prevPossibIndex += 1
        
        self.prevSegment.nextSegment = self
        self.possibilities = nextPossibilities

    def checkVoiceLeading(self, prevPossib, nextPossib):
        vlTop = self.fbVoices[-1].label
        vlBottom = self.fbVoices[0].label
        if not prevPossib.noHiddenIntervals(nextPossib, vlTop, vlBottom, self.fbRules):
            return False
        if not prevPossib.correctVoiceLeading2(nextPossib, self.fbVoices, self.fbRules):
            return False
        if not prevPossib.correctVoiceLeading(nextPossib, self.fbRules):
            return False
        
        return True
        
class SegmentException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Information:
    def __init__(self, fbScale, fbVoices, fbRules = rules.Rules()):
        self.fbScale = fbScale
        self.fbVoices = fbVoices
        self.fbRules = fbRules
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof