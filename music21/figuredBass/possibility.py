#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         rules.py
# Purpose:      music21 class to define a possibility (possible resolution) for a note
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest

from music21 import pitch
from music21 import voiceLeading
from music21 import interval

from music21.figuredBass import rules

class Possibility(dict):
    def isCorrectlyFormed(self, pitchNamesToHave = None, fbRules = rules.Rules()):
        correctlyFormed = True
        
        if not fbRules.allowIncompletePossibilities:
            if pitchNamesToHave is None:
                raise PossibilityException("Pitch names to analyze completeness not provided.")
            if self.isIncomplete(pitchNamesToHave):
                correctlyFormed = False
        if fbRules.topVoicesWithinOctave:
            if not self.topVoicesWithinOctave():
                correctlyFormed = False
        
        return correctlyFormed
    
    def isIncomplete(self, pitchNamesToHave):
        '''
        A possibility is incomplete if it doesn't contain at least
        one of each pitch name.
        '''
        pitchNamesContained = []
        for voiceLabel in self.keys():
            if self[voiceLabel].name not in pitchNamesContained:
                pitchNamesContained.append(self[voiceLabel].name)
        pitchNamesContained.sort()
        pitchNamesToHave.sort()
        if not cmp(pitchNamesContained, pitchNamesToHave):
            return False
        return True
    
    def topVoicesWithinOctave(self):
        topVoicesWithinAnOctave = True
        pitchesContained = []
        for voiceLabel in self.keys():
            pitchesContained.append((self[voiceLabel], voiceLabel))
        pitchesContained.sort()
        
        for pitch1Index in range(1, len(pitchesContained)):
            for pitch2Index in range(pitch1Index, len(pitchesContained)):
                (pitch1, vl1) = pitchesContained[pitch1Index]
                (pitch2, vl2) = pitchesContained[pitch2Index]
                if abs(interval.notesToGeneric(pitch1, pitch2).value) > 8:
                    #print(vl1 + " and " + vl2 + " are greater than an octave apart.")
                    topVoicesWithinAnOctave = False
        
        return topVoicesWithinAnOctave

    def hasCorrectVoiceLeading(self, consequentPossibility, fbRules = rules.Rules()):
        '''
        Returns True if all voicing rules as specified in the rules object are followed
        in the progression of one possibility to another.
        This encompasses parallel fifths, parallel octaves, voice crossings, voice leaps,
        and hidden fifths/octaves when applicable.
        '''
        hasCorrectVoiceLeading = True
        voiceQuartets = self._findVoiceQuartets(consequentPossibility)

        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in voiceQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if not fbRules.allowParallelFifths:
                if vlq.parallelFifth():
                    hasCorrectVoiceLeading = False
            if not fbRules.allowParallelOctaves:
                if vlq.parallelOctave():
                    hasCorrectVoiceLeading = False
            if not fbRules.allowVoiceOverlap:
                if vlq.voiceOverlap():
                    #print("Voice Crossing between " + vl1 + " and " + vl2 + ".")
                    hasCorrectVoiceLeading = False
        
        voicePairs = self._findVoicePairs(consequentPossibility)        
        voicePairs.sort()

        (v0n1, v0n2, vl) = voicePairs[0]
        if abs(v0n1.ps - v0n2.ps) > (12.0 * fbRules.bottomVoiceLeapOctaveLimit):
            #print("Voice leap in " + vl + " voice.")
            hasCorrectVoiceLeading = False
            
        for voiceIndex in range(1, len(voicePairs)):
            (v1n1, v1n2, vl) = voicePairs[voiceIndex]
            if abs(v1n1.ps - v1n2.ps) > (12.0 * fbRules.topVoiceLeapOctaveLimit):
                #print("Voice leap in " + vl + " voice.")
                hasCorrectVoiceLeading = False
                    
        try:
            if not fbRules.allowHiddenFifths:
                hasHiddenFifth = self.containsHiddenFifth(consequentPossibility)
                if hasHiddenFifth:
                    hasCorrectVoiceLeading = False
            if not fbRules.allowHiddenOctaves:
                hasHiddenOctave = self.containsHiddenOctave(consequentPossibility)
                if hasHiddenOctave:
                    hasCorrectVoiceLeading = False
        except PossibilityException:
            if not len(consequentPossibility.keys()) == len(self.keys()):
                pass
            # fill in for other exceptions here, if necessary
        
        return hasCorrectVoiceLeading
    
    def containsHiddenFifth(self, consequentPossibility):
        cp = consequentPossibility
        hasHiddenFifth = False

        if not len(cp.keys()) == len(self.keys()):
            raise PossibilityException("All voices need to be present to find hidden fifth.")
        
        voicePairs = self._findVoicePairs(consequentPossibility)
        voicePairs.sort()
        vq = voicePairs[0] + voicePairs[-1] # Voice quartet
        vlq = voiceLeading.VoiceLeadingQuartet(vq[0], vq[1], vq[3], vq[4])
        
        if vlq.hiddenFifth():
            #print("Hidden fifths between " + vq[2] + " and " + vq[5] + ".")
            hasHiddenFifth = True
            
        return hasHiddenFifth
    
    def containsHiddenOctave(self, consequentPossibility):
        cp = consequentPossibility
        hasHiddenOctave = False

        if not len(cp.keys()) == len(self.keys()):
            raise PossibilityException("All voices need to be present to find hidden fifth.")
        
        voicePairs = self._findVoicePairs(consequentPossibility)        

        voicePairs.sort()
        vq = voicePairs[0] + voicePairs[-1] # Voice quartet
        vlq = voiceLeading.VoiceLeadingQuartet(vq[0], vq[1], vq[3], vq[4])
        
        if vlq.hiddenOctave():
            #print("Hidden octaves between " + vq[2] + " and " + vq[5] + ".")
            hasHiddenOctave = True
            
        return hasHiddenOctave

    def containsParallelFifths(self, consequentPossibility):
        hasParallelFifth = False
        voiceQuartets = self._findVoiceQuartets(consequentPossibility)
        
        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in voiceQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.parallelFifth():
                #print("Parallel fifths between " + vl1 + " and " + vl2 + ".")
                hasParallelFifth = True
        
        return hasParallelFifth
        
    def containsParallelOctaves(self, consequentPossibility):
        hasParallelOctave = False
        voiceQuartets = self._findVoiceQuartets(consequentPossibility)
        
        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in voiceQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.parallelOctave():
                #print("Parallel octaves between " + vl1 + " and " + vl2 + ".")
                hasParallelOctave = True
        
        return hasParallelOctave
    
    def containsVoiceOverlap(self, consequentPossibility):
        hasVoiceOverlap = False
        voiceQuartets = self._findVoiceQuartets(consequentPossibility)

        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in voiceQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.voiceOverlap():
                print("Voice Crossing between " + vl1 + " and " + vl2 + ".")
                hasVoiceOverlap = True
                
                
        return hasVoiceOverlap

    def _findVoicePairs(self, consequentPossibility):
        cp = consequentPossibility
        
        voicePairs = []
        for voiceLabel in cp.keys():
            voicePair = (self[voiceLabel], cp[voiceLabel], voiceLabel)
            voicePairs.append(voicePair)

        return voicePairs
    
    def _findVoiceQuartets(self, consequentPossibility):
        cp = consequentPossibility
        if len(cp.keys()) <= 1:
            raise PossibilityException("Not enough voices in consequent possibility for voice leading to apply.")
        for voiceLabel in cp.keys():
            if voiceLabel not in self.keys():
                raise PossibilityException("Voice label not shared among both self and consequent possibilities.")
            
        voicePairs = self._findVoicePairs(consequentPossibility)        
        voiceQuartets = []
        
        for i in range(len(voicePairs)):
            for j in range(i+1,len(voicePairs)):
                voiceQuartets.append(voicePairs[i] + voicePairs[j])
        
        return voiceQuartets
        

class PossibilityException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    p1 = Possibility({'Alto': pitch.Pitch('G4'), 'Soprano': pitch.Pitch('G4'), 'Bass': pitch.Pitch('C3'), 'Tenor': pitch.Pitch('E4')})
    p2 = Possibility({'Alto': pitch.Pitch('B4'), 'Soprano': pitch.Pitch('F4'), 'Bass': pitch.Pitch('D3'), 'Tenor': pitch.Pitch('D4')})
    print p1.containsVoiceOverlap(p2)
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof