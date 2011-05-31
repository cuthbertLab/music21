#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      music21 class representing a figured bass note and notation 
#                realization.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import collections
import itertools
import music21
import unittest

from music21 import chord
from music21 import environment
from music21 import key
from music21 import note
from music21 import pitch
from music21 import scale
from music21.figuredBass import fbPitch
from music21.figuredBass import possibility
from music21.figuredBass import resolution
from music21.figuredBass import rules

_MOD = 'segment.py'

class Segment:
    def __init__(self, fbScale, bassNote = note.Note('C3'), notationString = '', fbRules = rules.Rules()):
        self.fbScale = fbScale
        self.bassNote = bassNote
        self.pitchNamesInChord = self.fbScale.getPitchNames(self.bassNote.pitch, notationString)
        self.allPitchesAboveBass = getPitches(self.pitchNamesInChord, self.bassNote.pitch, fbRules.maxPitch)
        self.environRules = environment.Environment(_MOD)
        self.segmentChord = chord.Chord(self.allPitchesAboveBass)
        self.numParts = fbRules.numParts        
        self.compileAllRules(fbRules)

    def singlePossibilityRules(self, fbRules = rules.Rules()):
        '''
        (willRunOnlyIfTrue, methodToRun, isCorrectSoln, optionalArgs)
        '''
        singlePossibRules = \
        [(fbRules.forbidIncompletePossibilities, possibility.isIncomplete, False, [self.pitchNamesInChord]),
         (True, possibility.upperPartsWithinLimit, True, [fbRules.upperPartsMaxSemitoneSeparation]),
         (fbRules.forbidVoiceCrossing, possibility.voiceCrossing, False)]
        
        return singlePossibRules
    
    def consecutivePossibilityRules(self, fbRules = rules.Rules()):
        '''
        (willRunOnlyIfTrue, methodToRun, isCorrectSoln, optionalArgs)
        '''
        consecPossibRules = \
        [(fbRules._upperPartsRemainSame, possibility.upperPartsSame, True),
         (fbRules.forbidVoiceOverlap, possibility.voiceOverlap, False),
         (True, possibility.partMovementsWithinLimits, True, [fbRules.partMovementLimits]),
         (fbRules.forbidParallelFifths, possibility.parallelFifths, False),
         (fbRules.forbidParallelOctaves, possibility.parallelOctaves, False),
         (fbRules.forbidHiddenFifths, possibility.hiddenFifth, False),
         (fbRules.forbidHiddenOctaves, possibility.hiddenOctave, False)]
        
        return consecPossibRules
    
    def specialResolutionRules(self, fbRules = rules.Rules()):
        '''
        (willRunOnlyIfTrue, methodToRun, optionalArgs)
        '''
        isDominantSeventh = self.segmentChord.isDominantSeventh()
        isDiminishedSeventh = self.segmentChord.isDiminishedSeventh()
        isAugmentedSixth = self.segmentChord.isAugmentedSixth()

        specialResRules = \
        [(fbRules.resolveDominantSeventhProperly and isDominantSeventh, self.resolveDominantSeventhSegment),
         (fbRules.resolveDiminishedSeventhProperly and isDiminishedSeventh, self.resolveDiminishedSeventhSegment, [fbRules.doubledRootInDim7]),
         (fbRules.resolveAugmentedSixthProperly and isAugmentedSixth, self.resolveAugmentedSixthSegment)]
        
        return specialResRules
        
    def compileAllRules(self, fbRules = rules.Rules()):
        self.singlePossibilityRuleChecking = self.compileRules(self.singlePossibilityRules(fbRules))
        self.consecutivePossibilityRuleChecking = self.compileRules(self.consecutivePossibilityRules(fbRules))
        self.specialResolutionRuleChecking = self.compileRules(self.specialResolutionRules(fbRules), 3)
        return
    
    def compileRules(self, rulesList, maxLength = 4):
        ruleChecking = collections.defaultdict(list)
        for ruleIndex in range(len(rulesList)):
            args = []
            if len(rulesList[ruleIndex]) == maxLength:
                args = rulesList[ruleIndex][-1]
            if maxLength == 4:
                (shouldRunMethod, method, isCorrect) = rulesList[ruleIndex][0:3]
                ruleChecking[shouldRunMethod].append((method, isCorrect, args))
            elif maxLength == 3:
                (shouldRunMethod, method) = rulesList[ruleIndex][0:2]
                ruleChecking[shouldRunMethod].append((method, args))
        
        return ruleChecking
    
    def allSinglePossibilities(self):
        iterables = [self.allPitchesAboveBass] * (self.numParts - 1)
        iterables.append([fbPitch.HashablePitch(self.bassNote.pitch.nameWithOctave)])
        return itertools.product(*iterables)
    
    def allCorrectSinglePossibilities(self):
        allA = self.allSinglePossibilities()
        return itertools.ifilter(lambda possibA: self.isCorrectSinglePossibility(possibA), allA)
            
    def isCorrectSinglePossibility(self, possibA):
        for (method, isCorrect, args) in self.singlePossibilityRuleChecking[True]:
            if not (method(possibA, *args) == isCorrect):
                return False
        return True

    def allCorrectConsecutivePossibilities(self, segmentB):
        for (resolutionMethod, args) in self.specialResolutionRuleChecking[True]:
            return resolutionMethod(segmentB, *args)    
        return self.resolveOrdinarySegment(segmentB)
    
    def resolveOrdinarySegment(self, segmentB):
        correctA = self.allCorrectSinglePossibilities()
        correctB = segmentB.allCorrectSinglePossibilities()
        correctAB = itertools.product(correctA, correctB)
        return itertools.ifilter(lambda possibAB: self.isCorrectConsecutivePossibility(possibA = possibAB[0], possibB = possibAB[1]), correctAB)        
    
    def isCorrectConsecutivePossibility(self, possibA, possibB):
        for (method, isCorrect, args) in self.consecutivePossibilityRuleChecking[True]:
            if not (method(possibA, possibB, *args) == isCorrect):
                return False
        return True
    
    def resolveDominantSeventhSegment(self, segmentB):
        domChord = self.segmentChord
        dominantScale = scale.MajorScale().derive(domChord)
        minorScale = dominantScale.getParallelMinor()
        
        tonic = dominantScale.getTonic()
        subdominant = dominantScale.pitchFromDegree(4)
        majSubmediant = dominantScale.pitchFromDegree(6)
        minSubmediant = minorScale.pitchFromDegree(6)
        
        resChord = segmentB.segmentChord
        domInversion = (domChord.inversion() == 2)
        resInversion = (resChord.inversion())
        resolveV43toI6 = domInversion and resInversion == 1
        
        dominantResolutionMethods = \
        [(resChord.root().name == tonic.name and resChord.isMajorTriad(), resolution.dominantSeventhToMajorTonic, [resolveV43toI6]),
         (resChord.root().name == tonic.name and resChord.isMinorTriad(), resolution.dominantSeventhToMinorTonic, [resolveV43toI6]),
         (resChord.root().name == majSubmediant.name and resChord.isMinorTriad() and domInversion == 0, resolution.dominantSeventhToMinorSubmediant),
         (resChord.root().name == minSubmediant.name and resChord.isMajorTriad() and domInversion == 0, resolution.dominantSeventhToMajorSubmediant),
         (resChord.root().name == subdominant.name and resChord.isMajorTriad() and domInversion == 0, resolution.dominantSeventhToMajorSubdominant),
         (resChord.root().name == subdominant.name and resChord.isMinorTriad() and domInversion == 0, resolution.dominantSeventhToMinorSubdominant)]
        
        try:
            return self.resolveSpecialSegment(dominantResolutionMethods)
        except SegmentException:
            self.environRules.warn("Dominant seventh resolution: No proper resolution available. Executing ordinary resolution.")
            return self.resolveOrdinarySegment(segmentB)
    
    def resolveDiminishedSeventhSegment(self, segmentB, doubledRoot):
        dimChord = self.segmentChord
        dimScale = scale.HarmonicMinorScale().deriveByDegree(7, dimChord.root())
        minorScale = dimScale.getParallelMinor()
        
        tonic = dimScale.getTonic()
        subdominant = dimScale.pitchFromDegree(4)

        resChord = segmentB.segmentChord
        if dimChord.inversion() == 1: #Doubled root in context
            if resChord.inversion() == 0:
                doubledRoot = True
            elif resChord.inversion() == 1:
                doubledRoot = False

        diminishedResolutionMethods = \
        [(resChord.root().name == tonic.name and resChord.isMajorTriad(), resolution.diminishedSeventhToMajorTonic, [doubledRoot]),
         (resChord.root().name == tonic.name and resChord.isMinorTriad(), resolution.diminishedSeventhToMinorTonic, [doubledRoot]),
         (resChord.root().name == subdominant.name and resChord.isMajorTriad(), resolution.diminishedSeventhToMajorSubdominant),
         (resChord.root().name == subdominant.name and resChord.isMinorTriad(), resolution.diminishedSeventhToMinorSubdominant)]
        
        try:
            return self.resolveSpecialSegment(diminishedResolutionMethods)
        except SegmentException:
            self.environRules.warn("Diminished seventh resolution: No proper resolution available. Executing ordinary resolution.")
            return self.resolveOrdinarySegment(segmentB)

    def resolveAugmentedSixthSegment(self, segmentB):
        augSixthChord = self.segmentChord
        if augSixthChord.isItalianAugmentedSixth():
            self.environRules.warn("Augmented sixth resolution: It+6 resolution not yet supported. Executing ordinary resolution.")
            return self.resolveOrdinarySegment(segmentB)
        elif augSixthChord.isFrenchAugmentedSixth():
            augSixthType = 1
        elif augSixthChord.isGermanAugmentedSixth():
            augSixthType = 2
        elif augSixthChord.isSwissAugmentedSixth():
            augSixthType = 3
        else:
            self.environRules.warn("Augmented sixth resolution: Augmented sixth type not supported. Executing ordinary resolution.")
            return self.resolveOrdinarySegment(segmentB)

        tonic = resolution.transpose(augSixthChord.bass(), 'M3')
        majorScale = scale.MajorScale(tonic)
        minorScale = scale.MinorScale(tonic)
        resChord = segmentB.segmentChord

        augmentedSixthResolutionMethods = \
        [(resChord.inversion() == 2 and resChord.root().name == tonic.name and resChord.isMajorTriad(), resolution.augmentedSixthToMajorTonic, [augSixthType]),
         (resChord.inversion() == 2 and resChord.root().name == tonic.name and resChord.isMinorTriad(), resolution.augmentedSixthToMinorTonic, [augSixthType]),
         (majorScale.pitchFromDegree(5).name == resChord.bass().name and resChord.isMajorTriad(), resolution.augmentedSixthToDominant, [augSixthType])]
        
        try:
            return self.resolveSpecialSegment(augmentedSixthResolutionMethods)
        except SegmentException:
            self.environRules.warn("Augmented sixth resolution: No proper resolution available. Executing ordinary resolution.")
            return self.resolveOrdinarySegment(segmentB)
    
    def resolveSpecialSegment(self, specialResolutionMethods):
        resolutionMethodExecutor = self.compileRules(specialResolutionMethods, 3)
        for (resolutionMethod, args) in resolutionMethodExecutor[True]:
            iterables = []
            for arg in args:
                iterables.append(itertools.repeat(arg))
            resolutions = itertools.imap(resolutionMethod, self.allCorrectSinglePossibilities(), *iterables)
            return itertools.izip(self.allCorrectSinglePossibilities(), resolutions)
    
        raise SegmentException("No standard resolution available.")

class NonChordSegment(Segment):
    def __init__(self, fbScale, bassNote = note.Note('D3'), pitchNamesAboveBass = ['C', 'E', 'G'], fbRules = rules.Rules()):
        self.fbScale = fbScale
        self.bassNote = bassNote
        self.allPitchesAboveBass = getPitches(pitchNamesAboveBass, bassNote.pitch, fbRules.maxPitch)        
        self.pitchNamesInChord = pitchNamesAboveBass + [self.bassNote.pitch.name]
        self.compileAllRules(fbRules)
    
# HELPER METHODS
# --------------
def getPitches(pitchNames, bassPitch = pitch.Pitch('C3'), maxPitch = pitch.Pitch('C8')):
    iter1 = itertools.product(pitchNames, range(maxPitch.octave + 1))
    iter2 = itertools.imap(lambda x: fbPitch.HashablePitch(x[0] + str(x[1])), iter1)
    iter3 = itertools.ifilterfalse(lambda samplePitch: bassPitch > samplePitch, iter2)
    iter4 = itertools.ifilterfalse(lambda samplePitch: samplePitch > maxPitch, iter3)
    allPitches = list(iter4)
    allPitches.sort()
    return allPitches

class SegmentException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof