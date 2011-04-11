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
from music21 import chord
from music21 import scale
from music21 import environment

from music21.figuredBass import rules
from music21.figuredBass import possibility
from music21.figuredBass import realizerScale
from music21.figuredBass import voice
from music21.figuredBass import resolution
from music21.figuredBass import notation

_MOD = 'segment.py'

class Segment:
    def __init__(self, fbInformation, bassNote, notationString = ''):
        self.bassNote = bassNote
        self.notationString = notationString
        self.fbScale = fbInformation.fbScale
        self.fbVoices = fbInformation.fbVoices
        self.fbRules = fbInformation.fbRules
        self.pitchesAboveBass = self.fbScale.getPitches(self.bassNote.pitch, self.notationString)
        self.pitchNamesInChord = self.fbScale.getPitchNames(self.bassNote.pitch, self.notationString)
        self.nextMovements = {}
        self.nextSegment = None
        self.isDominantSeventh = chord.Chord(self.pitchesAboveBass).isDominantSeventh()
        self.isDiminishedSeventh = chord.Chord(self.pitchesAboveBass).isDiminishedSeventh()
        self.addLyricsToBassNote()

    def addLyricsToBassNote(self):
        n = notation.Notation(self.notationString)
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
            self.bassNote.addLyric(spacesInFront + fs)
    
    def correctPossibilities(self):
        raise SegmentException("Must specifically create StartSegment or MiddleSegment to call this method.")
    
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
    
    def correctSelfContainedPossibilities(self):
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
            # No incomplete possibilities
            if not self.fbRules.allowIncompletePossibilities:
                if possib.isIncomplete(self.pitchNamesInChord):
                    continue
            # Top voices within interval.Interval
            if not possib.topVoicesWithinLimit(self.fbRules.topVoicesMaxIntervalSeparation):
                continue
            # Pitches in each voice within range
            if self.fbRules.filterPitchesByRange:
                pitchesInRange = possib.pitchesWithinRange(self.fbVoices)
                if not pitchesInRange:
                    continue
            # No voice crossing
            if not self.fbRules.allowVoiceCrossing:
                hasVoiceCrossing = possib.voiceCrossing(possibility.extractVoiceLabels(self.fbVoices))
                if hasVoiceCrossing:
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
    
                
class StartSegment(Segment):
    def __init__(self, fbInformation, bassNote, notation = ''):
        Segment.__init__(self, fbInformation, bassNote, notation)
        self.correctPossibilities()

    def correctPossibilities(self):
        # Imitates _findPossibleStartingChords from realizer.py
        self.possibilities = self.correctSelfContainedPossibilities()
    
class MiddleSegment(Segment):
    def __init__(self, fbInformation, prevSegment, bassNote, notation = ''):
        Segment.__init__(self, fbInformation, bassNote, notation)
        self.prevSegment = prevSegment
        self.correctPossibilities()
    
    def correctPossibilities(self):
        if self.prevSegment.isDominantSeventh and self.fbRules.resolveDominantSeventhProperly:
            dominantPossibilities = self.prevSegment.possibilities
            resolutionPossibilities = []
            dominantPossibIndex = 0
            for dominantPossib in dominantPossibilities:
                movements = []
                resolutionPossib = self.resolveDominantSeventh(dominantPossib)
                try:
                    movements.append(resolutionPossibilities.index(resolutionPossib))
                except ValueError:
                    resolutionPossibilities.append(resolutionPossib)
                    movements.append(len(resolutionPossibilities) - 1)             
                self.prevSegment.nextMovements[dominantPossibIndex] = movements
                dominantPossibIndex += 1 
            self.prevSegment.nextSegment = self
            self.possibilities = resolutionPossibilities
        elif self.prevSegment.isDiminishedSeventh and self.fbRules.resolveDiminishedSeventhProperly:
            diminishedPossibilities = self.prevSegment.possibilities
            resolutionPossibilities = []
            diminishedPossibIndex = 0
            for diminishedPossib in diminishedPossibilities:
                movements = []
                resolutionPossib = self.resolveDiminishedSeventh(diminishedPossib)
                try:
                    movements.append(resolutionPossibilities.index(resolutionPossib))
                except ValueError:
                    resolutionPossibilities.append(resolutionPossib)
                    movements.append(len(resolutionPossibilities) - 1)             
                self.prevSegment.nextMovements[diminishedPossibIndex] = movements
                diminishedPossibIndex += 1
            self.prevSegment.nextSegment = self
            self.possibilities = resolutionPossibilities
        else:
            prevPossibilities = self.prevSegment.possibilities
            nextPossibilities = self.correctSelfContainedPossibilities()
            prevPossibIndex = 0
            for prevPossib in prevPossibilities:
                movements = []
                nextPossibIndex = 0
                for nextPossib in nextPossibilities:
                    if self.hasCorrectVoiceLeading(prevPossib, nextPossib):
                        movements.append(nextPossibIndex)
                    nextPossibIndex += 1
                self.prevSegment.nextMovements[prevPossibIndex] = movements
                prevPossibIndex += 1
            self.prevSegment.nextSegment = self
            self.possibilities = nextPossibilities
      
    def resolveDominantSeventh(self, dominantPossib):
        environRules = environment.Environment(_MOD)
        if not dominantPossib.isDominantSeventh():
            raise SegmentException("Possibility does not form a correctly spelled dominant seventh chord.")
        
        sc = scale.MajorScale()
        dominantScale = sc.derive(dominantPossib.chordify().pitches)
        minorScale = dominantScale.getParallelMinor()       
        
        tonic = dominantScale.getTonic()
        subdominant = dominantScale.pitchFromDegree(4)
        majSubmediant = dominantScale.pitchFromDegree(6)
        minSubmediant = minorScale.pitchFromDegree(6)
        
        resolutionChord = chord.Chord(self.pitchesAboveBass)
        
        if resolutionChord.root().name == tonic.name:
            if resolutionChord.isMajorTriad():
                environRules.warn("Dominant seventh resolution: V7->I in " + dominantScale.name)
                resolutionPossib = resolution.dominantSeventhToMajorTonic(dominantPossib, self.fbRules.resolveV43toI6)
            elif resolutionChord.isMinorTriad():
                environRules.warn("Dominant seventh resolution: V7->i in " + minorScale.name)
                resolutionPossib = resolution.dominantSeventhToMinorTonic(dominantPossib, self.fbRules.resolveV43toI6)
        elif resolutionChord.root().name == majSubmediant.name:
            if sampleChord.isMinorTriad():
                environRules.warn("Dominant seventh resolution: V7->vi in " + dominantScale.name)
                resolutionPossib = resolution.dominantSeventhToMinorSubmediant(dominantPossib) #Major scale
        elif resolutionChord.root().name == minSubmediant.name:
            if resolutionChord.isMajorTriad():
                environRules.warn("Dominant seventh resolution: V7->VI in " + minorScale.name)
                resolutionPossib = resolution.dominantSeventhToMajorSubmediant(dominantPossib) #Minor scale
        elif resolutionChord.root().name == subdominant.name:
            if resolutionChord.isMajorTriad():
                environRules.warn("Dominant seventh resolution: V7->IV in " + dominantScale.name)
                resolutionPossib = resolution.dominantSeventhToMajorSubdominant(dominantPossib)
            elif resolutionChord.isMinorTriad():
                environRules.warn("Dominant seventh resolution: V7->iv in " + minorScale.name)
                resolutionPossib = resolution.dominantSeventhToMinorSubdominant(dominantPossib)
        else:
            raise SegmentException("Dominant seventh resolution: No standard resolution available.")
        
        if not (resolutionChord.bass() == self.bassNote.pitch):
            raise SegmentException("Dominant seventh resolution: Bass note resolved improperly in figured bass.")
            
        return resolutionPossib

    def resolveDiminishedSeventh(self, diminishedPossib):
        environRules = environment.Environment(_MOD)       
        if not diminishedPossib.isDiminishedSeventh():
            raise SegmentException("Possibility does not form a correctly spelled diminished seventh chord.")
          
        diminishedChord = diminishedPossib.chordify()
        sc = scale.HarmonicMinorScale()
        diminishedScale = sc.deriveByDegree(7, diminishedChord.root())
        minorScale = diminishedScale.getParallelMinor()
        
        tonic = diminishedScale.getTonic()
        subdominant = diminishedScale.pitchFromDegree(4)

        resolutionChord = chord.Chord(self.pitchesAboveBass)
        
        if resolutionChord.root().name == tonic.name:
            if resolutionChord.isMajorTriad():
                environRules.warn("Diminished seventh resolution: vii7->I in " + diminishedScale.name)
                resolutionPossib = resolution.diminishedSeventhToMajorTonic(diminishedPossib, self.fbRules.doubledRootInDim7)
            elif resolutionChord.isMinorTriad():
                environRules.warn("Diminished seventh resolution: vii7->i in " + minorScale.name)
                resolutionPossib = resolution.diminishedSeventhToMinorTonic(diminishedPossib, self.fbRules.doubledRootInDim7)
        elif resolutionChord.root().name == subdominant.name:
             if resolutionChord.isMajorTriad():
                environRules.warn("Diminished seventh resolution: vii7->IV in " + diminishedScale.name)
                resolutionPossib = resolution.diminishedSeventhToMajorSubdominant(diminishedPossib)
             elif resolutionChord.isMinorTriad():
                environRules.warn("Diminished seventh resolution: vii7->iv in " + minorScale.name)
                resolutionPossib = resolution.diminishedSeventhToMinorSubdominant(diminishedPossib)
        else:
            raise SegmentException("Diminished seventh resolution: No standard resolution available.")

        if not (resolutionChord.bass() == self.bassNote.pitch):
            raise SegmentException("Diminished seventh resolution: Bass note resolved improperly in figured bass.")
            
        return resolutionPossib

    def hasCorrectVoiceLeading(self, prevPossib, nextPossib):
        vlTop = self.fbVoices[-1].label
        vlBottom = self.fbVoices[0].label
        # No hidden fifth
        if not self.fbRules.allowHiddenFifths:
            hasHiddenFifth = prevPossib.hiddenFifth(nextPossib, vlTop, vlBottom)
            if hasHiddenFifth:
                return False
        # No hidden octave
        if not self.fbRules.allowHiddenOctaves:
            hasHiddenOctave = prevPossib.hiddenOctave(nextPossib, vlTop, vlBottom)
            if hasHiddenOctave:
                return False
        
        leapsWithinLimits = prevPossib.voiceLeapsWithinLimits(nextPossib, self.fbVoices)
        # No voice leaps
        if not leapsWithinLimits:
            return False
        # No voice overlaps
        if not self.fbRules.allowVoiceOverlap:
            hasVoiceOverlap = prevPossib.voiceOverlap(nextPossib, possibility.extractVoiceLabels(self.fbVoices))
            if hasVoiceOverlap:
                return False

        # No parallel fifths
        if not self.fbRules.allowParallelFifths:
            hasParallelFifth = prevPossib.parallelFifths(nextPossib)
            if hasParallelFifth:
                return False
        # No parallel octaves
        if not self.fbRules.allowParallelOctaves:
            hasParallelOctave = prevPossib.parallelOctaves(nextPossib)
            if hasParallelOctave:
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