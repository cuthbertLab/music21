#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         rules.py
# Purpose:      music21 class to define rules used in composition
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest

from music21 import voiceLeading
from music21 import environment
from music21 import pitch
from music21 import interval

_MOD = "rules.py"

class Rules:
    def __init__(self):
        self.environRules = environment.Environment(_MOD)
        self.verbose = False
        
        #Voicing Rules
        self.allowParallelFifths = False
        self.allowParallelOctaves = False
        self.allowVoiceCrossing = False
        self.bottomVoiceLeapOctaveLimit = 1.0
        self.topVoiceLeapOctaveLimit = 1.0

        #Chord rules
        self.allowIncompleteChords = False
        self.topThreeVoicesWithinOctave = True

        #Chord To Chord Rules
        self.allowHiddenFifths = False
        self.allowHiddenOctaves = False
        
    def checkChords(self, pitchListA, pitchListB):
        conformsToRules = True
        
        if not (len(pitchListA) == 4 or len(pitchListB) == 4):
            raise FiguredBassException("Not a chord with four voices")

        prevSoprano = pitchListA[0]
        nextSoprano = pitchListB[0]
        
        prevBass = pitchListA[3]
        nextBass = pitchListB[3]
        
        vlq = voiceLeading.VoiceLeadingQuartet(prevBass, nextBass, prevSoprano, nextSoprano)
        if not self.allowHiddenFifths:
            if vlq.hiddenFifth():
                if self.verbose:
                    self.environRules.warn("Hidden fifth!")
                conformsToRules = False
        if not self.allowHiddenOctaves:
            if vlq.hiddenOctave():
                if self.verbose:
                    self.environRules.warn("Hidden octave!")
                conformsToRules = False
         
        return conformsToRules
    
    #pitchList = [soprano, alto, tenor, bass]
    def checkChord(self, pitchList, pitchNamesInChord = None):
        conformsToRules = True
        
        if not len(pitchList) == 4:
            raise FiguredBassRulesException("Not a chord with four voices")
        
        if not self.allowIncompleteChords:
            if pitchNamesInChord == None:
                raise FiguredBassRulesException("Pitch names in chord not provided to analyze containment")
            pitchNames = []
            for givenPitch in pitchList:
                if givenPitch.name not in pitchNames:
                    pitchNames.append(givenPitch.name)
            for pitchName in pitchNamesInChord:
                if pitchName not in pitchNames:
                    if self.verbose:
                        self.environRules.warn("Incomplete Chord!")
                    conformsToRules = False
        if self.topThreeVoicesWithinOctave:
            soprano = pitchList[0]
            alto = pitchList[1]
            tenor = pitchList[2]
            
            if abs(interval.notesToGeneric(soprano, alto).value) > 8:
                if self.verbose == True:
                    self.environRules.warn("Soprano and alto greater than an octave apart!")
                conformsToRules = False
            if abs(interval.notesToGeneric(soprano, tenor).value) > 8:
                if self.verbose == True:
                    self.environRules.warn("Soprano and tenor greater than an octave apart!")
                conformsToRules = False
            if abs(interval.notesToGeneric(alto, tenor).value) > 8:
                if self.verbose == True:
                    self.environRules.warn("Alto and tenor greater than an octave apart!")
                conformsToRules = False
                
        return conformsToRules
            
                    
    def checkVoiceLeading(self, vlq):
        '''
        Takes in a VoiceLeadingQuartet and returns False if any voicing rules have
        been broken, although we can choose to relax the rules.
        
        If self.verbose = True, then warnings will be printed to the console everytime
        the VoiceLeadingQuartet violates a rule.
        
        Default voicing rules: 
        (a) No parallel (or antiparallel) fifths between the two voices, 
        (b) No parallel (or antiparallel) octaves between the two voices,
        (c) No voice crossings, as determined by frequency crossing (NOT written crossing)
        (d) No leaps of greater than an octave in either voice, as determined by absolute distance (NOT written distance)
        
        >>> from music21 import *
        >>> from music21.figuredBass import rules
        >>> rules = rules.Rules()
        >>> vlqA = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('G3'), pitch.Pitch('A3'))
        >>> rules.checkVoiceLeading(vlqA) #Parallel fifths = C->D, G->A
        False
        >>> vlqB = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('B3'), pitch.Pitch('G3'), pitch.Pitch('D3')) 
        >>> rules.checkVoiceLeading(vlqB) #Voice crossing = C->A, higher than the G above C
        False
        >>> vlqC = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('F3'), pitch.Pitch('G3')) 
        >>> rules.checkVoiceLeading(vlqC) #Parallel fourths
        True
        
        OMIT_FROM_DOCS
        >>> vlqD = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('C4'), pitch.Pitch('D4'))
        >>> rules.checkVoiceLeading(vlqD) #Parallel octaves = C3->D3, C4->D4
        False
        >>> vlqE = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('G4'), pitch.Pitch('E5'), pitch.Pitch('D5'))
        >>> rules.checkVoiceLeading(vlqE)
        False
        >>> vlqF = voiceLeading.VoiceLeadingQuartet(pitch.Pitch('C3'), pitch.Pitch('D3'), pitch.Pitch('E5'), pitch.Pitch('G6'))
        >>> rules.checkVoiceLeading(vlqF)
        False
        '''
        conformsToRules = True
        
        if not self.allowParallelFifths:
            if vlq.parallelFifth(): 
                if self.verbose:
                    self.environRules.warn("Parallel fifths!")
                conformsToRules = False
        if not self.allowParallelOctaves:
            if vlq.parallelOctave(): 
                if self.verbose:
                    self.environRules.warn("Parallel octaves!")
                conformsToRules = False
        if not self.allowVoiceCrossing:
            if vlq.voiceCrossing(): 
                if self.verbose:
                    self.environRules.warn("Voice crossing!")
                conformsToRules = False
        if abs(vlq.v1n1.ps - vlq.v1n2.ps) > (12.0 * self.bottomVoiceLeapOctaveLimit): 
            if self.verbose:
                self.environRules.warn("Greater than octave leap in bottom voice!")
            conformsToRules = False
        if abs(vlq.v2n1.ps - vlq.v2n2.ps) > (12.0 * self.topVoiceLeapOctaveLimit): 
            if self.verbose:
                self.environRules.warn("Greater than octave leap in top voice!")
            conformsToRules = False
        
        return conformsToRules


class FiguredBassRulesException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)  

#------------------------------------------------------------------------------
# eof
 
    