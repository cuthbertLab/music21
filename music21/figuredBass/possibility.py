#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         possibility.py
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
from music21 import environment

from music21.figuredBass import rules
from music21.figuredBass import voice

_MOD = "possibility.py"

class Possibility(dict):
    # CHORD FORMATION RULES
    def correctlyFormed(self, pitchNamesToHave = None, fbRules = rules.Rules(), verbose = False):
        # Imitates checkChord() from rules.py, but one calls the method on the Possibility object,
        # rather than providing the pitches as an argument and calling a Rules object.
        '''
        >>> from music21 import *
        >>> from music21.figuredBass import rules
        >>> from music21.figuredBass import possibility
        >>> fbRules = rules.Rules()
        >>> pitchNames = ['C','E','G']
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C3')})
        >>> p1.correctlyFormed(pitchNames, fbRules)
        True
        >>> p1['T'] = pitch.Pitch('C3')
        >>> p1.correctlyFormed(pitchNames, fbRules)
        False
        '''
        correctlyFormed = True
        
        if not fbRules.allowIncompletePossibilities:
            if pitchNamesToHave is None:
                raise PossibilityException("Pitch names to analyze completeness not provided.")
            if self.incomplete(pitchNamesToHave, verbose):
                correctlyFormed = False
                if not verbose:
                    return correctlyFormed
        if not self.topVoicesWithinLimit(fbRules.topVoicesMaxIntervalSeparation, verbose):
            correctlyFormed = False
            if not verbose:
                return correctlyFormed
        
        return correctlyFormed
    
    def incomplete(self, pitchNamesToHave, verbose = False):
        '''
        A possibility is incomplete if it doesn't contain at least
        one of each pitch name.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> pitchNames = ['C','E','G']
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C3')})
        >>> p1.incomplete(pitchNames)
        False
        >>> p1['T'] = pitch.Pitch('C4')
        >>> p1.incomplete(pitchNames)
        True
        '''
        pitchNamesContained = []
        for voiceLabel in self.keys():
            if self[voiceLabel].name not in pitchNamesContained:
                pitchNamesContained.append(self[voiceLabel].name)
        pitchNamesContained.sort()
        pitchNamesToHave.sort()
        if not cmp(pitchNamesContained, pitchNamesToHave):
            return False
        else:
            if verbose:
                environRules = environment.Environment(_MOD)
                environRules.warn("Incomplete Chord!")
            return True
    
    def topVoicesWithinLimit(self, topVoicesMaxIntervalSeparation = None, verbose = False):
        '''
        Returns True if upper voices are found within topVoicesMaxIntervalSeparation of each other, a.k.a.
        if the upper voices are found within that many semitones of each other.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C3')})
        >>> p1.topVoicesWithinLimit(interval.Interval('P8'))
        True
        >>> p1['T'] = pitch.Pitch('E3')
        >>> p1.topVoicesWithinLimit(interval.Interval('P8'))
        False
        '''
        topVoicesWithinLimit = True
        if topVoicesMaxIntervalSeparation == None:
            return topVoicesWithinLimit
        pitchesContained = []
        for voiceLabel in self.keys():
            pitchesContained.append((self[voiceLabel], voiceLabel))
        pitchesContained.sort()
        i0 = topVoicesMaxIntervalSeparation
        
        for pitch1Index in range(1, len(pitchesContained)):
            for pitch2Index in range(pitch1Index, len(pitchesContained)):
                (pitch1, vl1) = pitchesContained[pitch1Index]
                (pitch2, vl2) = pitchesContained[pitch2Index]
                i1 = interval.notesToInterval(pitch1, pitch2)
                if i1.chromatic.semitones > i0.chromatic.semitones:
                    if verbose:
                        environRules = environment.Environment(_MOD)
                        environRules.warn(vl1 + " and " + vl2 + " are greater than " + topVoicesMaxIntervalSeparation.semiSimpleName + " apart.")
                    topVoicesWithinLimit = False
                    if not verbose:
                        return topVoicesWithinLimit
        
        return topVoicesWithinLimit

    # VOICE LEADING RULES
    def correctVoiceLeading(self, nextPossibility, fbRules = rules.Rules(), verbose = False):
        # Imitates checkVoiceLeading() from rules.py, BUT it has the added advantage
        # of being able to be used for 2 -> n voices.
        '''
        Returns True if all voicing rules as specified in the rules object are followed
        in the progression of one possibility to another. This encompasses parallel fifths, 
        parallel octaves, and voice leaps.
        
        Note that the next possibility need not have all the voices of the previous
        possibility. What matters is that all the voices in the next possibility
        be found in the previous possibility. For example, having {'S','A','T','B'} as 
        a previous possibility and then having {'T','B'} as the next possibility
        is OK. The method will then check the voice leading of only 'T' and 'B'.
        
        >>> from music21 import *
        >>> from music21.figuredBass import rules
        >>> from music21.figuredBass import possibility
        >>> fbRules = rules.Rules()
        >>> p1 = possibility.Possibility({'Tenor': pitch.Pitch('G3'), 'Bass': pitch.Pitch('C3'), 'Soprano': pitch.Pitch('C5')})
        >>> p2 = possibility.Possibility({'Tenor': pitch.Pitch('A3'), 'Bass': pitch.Pitch('D3')})
        >>> p1.correctVoiceLeading(p2, fbRules)
        False
        >>> p1['Tenor'] = pitch.Pitch('C4')
        >>> p2['Tenor'] = pitch.Pitch('D4')
        >>> p1.correctVoiceLeading(p2, fbRules)
        False
        >>> p1['Tenor'] = pitch.Pitch('F3')
        >>> p2['Tenor'] = pitch.Pitch('G3')
        >>> p1.correctVoiceLeading(p2, fbRules)
        True
        >>> p2['Bass'] = pitch.Pitch('C5')
        >>> p1.correctVoiceLeading(p2, fbRules)
        False
        '''
        hasCorrectVoiceLeading = True

        if not fbRules.allowParallelFifths:
            hasParallelFifth = self.containsParallelFifths(nextPossibility, verbose)
            if hasParallelFifth:
                hasCorrectVoiceLeading = False
                if not verbose:
                    return hasCorrectVoiceLeading
        if not fbRules.allowParallelOctaves:
            hasParallelOctave = self.containsParallelOctaves(nextPossibility, verbose)
            if hasParallelOctave:
                hasCorrectVoiceLeading = False
                if not verbose:
                    return hasCorrectVoiceLeading

        botWithinLimit = self.topVoiceLeapsWithinLimit(nextPossibility, fbRules.topVoiceLeapIntervalLimit, verbose)
        if not botWithinLimit:
            hasCorrectVoiceLeading = False
            if not verbose:
                return hasCorrectVoiceLeading
        topWithinLimit = self.bottomVoiceLeapWithinLimit(nextPossibility, fbRules.bottomVoiceLeapIntervalLimit, verbose)
        if not topWithinLimit:
            hasCorrectVoiceLeading = False
            if not verbose:
                return hasCorrectVoiceLeading

        return hasCorrectVoiceLeading

    def containsParallelFifths(self, nextPossibility, verbose = False):
        '''
        Checks for parallel fifths between self and a next possibility.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': pitch.Pitch('G3'), 'Bass': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'Tenor': pitch.Pitch('A3'), 'Bass': pitch.Pitch('D3')})
        >>> p1.containsParallelFifths(p2)
        True
        ''' 
        hasParallelFifth = False
        voiceQuartets = self.findVoiceQuartets(nextPossibility)
        
        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in voiceQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.parallelFifth():
                if verbose:
                    environRules = environment.Environment(_MOD)
                    environRules.warn("Parallel fifths between " + vl1 + " and " + vl2 + ".")
                hasParallelFifth = True
                if not verbose:
                    return hasParallelFifth
        
        return hasParallelFifth
        
    def containsParallelOctaves(self, nextPossibility, verbose = False):
        '''
        Checks for parallel octaves between self and a next possibility.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': pitch.Pitch('C4'), 'Bass': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'Tenor': pitch.Pitch('D4'), 'Bass': pitch.Pitch('D3')})
        >>> p1.containsParallelOctaves(p2)
        True
        '''        
        hasParallelOctave = False
        voiceQuartets = self.findVoiceQuartets(nextPossibility)
        
        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in voiceQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.parallelOctave():
                if verbose:
                    environRules = environment.Environment(_MOD)
                    environRules.warn("Parallel octaves between " + vl1 + " and " + vl2 + ".")
                hasParallelOctave = True
                if not verbose:
                    return hasParallelOctave
        
        return hasParallelOctave
    
    def topVoiceLeapsWithinLimit(self, nextPossibility, topVoiceLeapIntervalLimit = None, verbose = False):
        '''
        Returns True if there is no voice leap in any of the upper voices, a.k.a. the number of semitones difference
        in the previous and next pitches of any of the upper voices is not greater than topVoiceLeapIntervalLimit.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Soprano': pitch.Pitch('C5'), 'Tenor': pitch.Pitch('C4'), 'Bass': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'Soprano': pitch.Pitch('B4'), 'Tenor': pitch.Pitch('D4'), 'Bass': pitch.Pitch('D3')})
        >>> p1.topVoiceLeapsWithinLimit(p2, interval.Interval('P5'))
        True
        >>> p2['Tenor'] = pitch.Pitch('B4')
        >>> p1.topVoiceLeapsWithinLimit(p2, interval.Interval('P5'))
        False
        '''

        withinLimit = True
        if topVoiceLeapIntervalLimit == None:
            return withinLimit
        i0 = topVoiceLeapIntervalLimit

        voicePairs = self.findVoicePairs(nextPossibility)        
        voicePairs.sort()
        
        for voiceIndex in range(1, len(voicePairs)):
            (v1n1, v1n2, vl) = voicePairs[voiceIndex]
            i1 = interval.notesToInterval(v1n1, v1n2)
            if i1.chromatic.semitones > i0.chromatic.semitones:
                if verbose:
                    environRules = environment.Environment(_MOD)
                    environRules.warn("Voice leap in " + vl + " voice.")
                withinLimit = False
                if not verbose:
                    return withinLimit
                
        return withinLimit
        
    def bottomVoiceLeapWithinLimit(self, nextPossibility, bottomVoiceLeapIntervalLimit = None, verbose = False):
        '''
        Returns True if there is no voice leap in the lowest voice, a.k.a. the number of semitones difference
        in the previous and next pitches of the lowest voice is not greater than bottomVoiceLeapIntervalLimit.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': pitch.Pitch('C4'), 'Bass': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'Tenor': pitch.Pitch('D4'), 'Bass': pitch.Pitch('D3')})
        >>> p1.bottomVoiceLeapWithinLimit(p2, interval.Interval('P8'))
        True
        >>> p2['Bass'] = pitch.Pitch('D4')
        >>> p1.bottomVoiceLeapWithinLimit(p2, interval.Interval('P8'))
        False
        '''
        withinLimit = True
        if bottomVoiceLeapIntervalLimit == None:
            return withinLimit
        i0 = bottomVoiceLeapIntervalLimit
        
        voicePairs = self.findVoicePairs(nextPossibility)        
        voicePairs.sort()

        (v0n1, v0n2, vl) = voicePairs[0]
        i1 = interval.notesToInterval(v0n1, v0n2)
        if i1.chromatic.semitones > i0.chromatic.semitones:
            if verbose:
                environRules = environment.Environment(_MOD)
                environRules.warn("Voice leap in " + vl + " voice.")
            withinLimit = False
            
        return withinLimit
    
    # HIDDEN INTERVAL RULES
    def noHiddenIntervals(self, nextPossibility, vlTop, vlBottom, fbRules = rules.Rules(), verbose = False):
        # Imitates checkChords() from rules.py for checking of hidden fifths/hidden octave, BUT has the
        # advantage of being able to be used for 2->n voices.
        '''
        Checks for hidden fifths and octaves between self and a next possibility, as specified in fbRules. 
        To remove ambiguities, asked to provide the dictionary key of the top voice and the key of the bottom voice.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import rules
        >>> fbRules = rules.Rules()
        >>> p1 = possibility.Possibility({'Soprano': pitch.Pitch('E5'), 'Bass': pitch.Pitch('C3'), 'Tenor': pitch.Pitch('G4')})
        >>> p2 = possibility.Possibility({'Soprano': pitch.Pitch('A5'), 'Bass': pitch.Pitch('D3'), 'Tenor': pitch.Pitch('F4')})
        >>> p1.noHiddenIntervals(p2, 'Soprano', 'Bass', fbRules)
        False
        >>> p1['Soprano'] = pitch.Pitch('A5')
        >>> p2['Soprano'] = pitch.Pitch('D6')
        >>> p1.noHiddenIntervals(p2, 'Soprano', 'Bass', fbRules)
        False
        '''
        hasNoHiddenIntervals = True
        
        if not fbRules.allowHiddenFifths:
            hasHiddenFifth = self.containsHiddenFifth(nextPossibility, vlTop, vlBottom, verbose)
            if hasHiddenFifth:
                hasNoHiddenIntervals = False
                if not verbose:
                    return hasNoHiddenIntervals
        if not fbRules.allowHiddenOctaves:
            hasHiddenOctave = self.containsHiddenOctave(nextPossibility, vlTop, vlBottom, verbose)
            if hasHiddenOctave:
                hasNoHiddenIntervals = False
                if not verbose:
                    return hasNoHiddenIntervals
        
        return hasNoHiddenIntervals
        
    def containsHiddenFifth(self, nextPossibility, vlTop, vlBottom, verbose = False):
        '''
        Checks for hidden fifths between self and a next possibility. To remove ambiguities,
        asked to provide the dictionary key of the top voice and the key of the bottom voice.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Soprano': pitch.Pitch('E5'), 'Bass': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'Soprano': pitch.Pitch('A5'), 'Bass': pitch.Pitch('D3')})
        >>> p1.containsHiddenFifth(p2, 'Soprano', 'Bass')
        True
        '''
        cp = nextPossibility
        hasHiddenFifth = False

        vlq = voiceLeading.VoiceLeadingQuartet(self[vlBottom], cp[vlBottom], self[vlTop], cp[vlTop])
        
        if vlq.hiddenFifth():
            if verbose:
                environRules = environment.Environment(_MOD)
                environRules.warn("Hidden fifths between " + vlTop + " and " + vlBottom + ".")
            hasHiddenFifth = True
            if not verbose:
                return hasHiddenFifth
            
        return hasHiddenFifth
    
    def containsHiddenOctave(self, nextPossibility, vlTop, vlBottom, verbose = False):
        '''
        Checks for hidden octaves between self and a next possibility. To remove ambiguities,
        asked to provide the dictionary key of the top voice and the key of the bottom voice.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Soprano': pitch.Pitch('A5'), 'Bass': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'Soprano': pitch.Pitch('D6'), 'Bass': pitch.Pitch('D3')})
        >>> p1.containsHiddenOctave(p2, 'Soprano', 'Bass')
        True
        '''
        cp = nextPossibility
        hasHiddenOctave = False

        vlq = voiceLeading.VoiceLeadingQuartet(self[vlBottom], cp[vlBottom], self[vlTop], cp[vlTop])
                
        if vlq.hiddenOctave():
            if verbose:
                environRules = environment.Environment(_MOD)
                environRules.warn("Hidden octaves between " + vlTop + " and " + vlBottom + ".")
            hasHiddenOctave = True
            if not verbose:
                return hasHiddenOctave
            
        return hasHiddenOctave

    # TESSITURA RULES
    def correctTessitura(self, nextPossibility, sortedVoiceList, fbRules = rules.Rules(), verbose = False):
        '''
        Returns true if possibilities have correct tessitura, meaning no voice overlaps,
        no voice crossing, and pitches within ranges as specified by fbRules.
        
        >>> from music21 import *
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import rules
        >>> fbRules = rules.Rules()
        >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
        >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
        >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
        >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'))
        >>> sortedVoiceList = [v1, v2, v3, v4]
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B4'), 'A': pitch.Pitch('F4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D4')})
        >>> p1.correctTessitura(p2, sortedVoiceList, fbRules)
        True
        >>> p3 = possibility.Possibility({'S': pitch.Pitch('F4'), 'A': pitch.Pitch('F4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D4')})       
        >>> p1.correctTessitura(p3, sortedVoiceList, fbRules)
        False
        '''
        hasCorrectTessitura = True
        cp = nextPossibility
        
        if not fbRules.allowVoiceOverlap:
            hasVoiceOverlap = self.containsVoiceOverlap(cp, sortedVoiceList, verbose)
            if hasVoiceOverlap:
                hasCorrectTessitura = False
            if not verbose:
                return hasCorrectTessitura
        if not fbRules.allowVoiceCrossing:
            hasVoiceCrossing = self.containsVoiceCrossing(sortedVoiceList, verbose)
            if hasVoiceCrossing:
                hasCorrectTessitura = False
            if not verbose:
                return hasCorrectTessitura
        if not fbRules.filterPitchesByRange:
            pitchesInRange = self.pitchesWithinRange(sortedVoiceList, verbose)
            if not pitchesInRange:
                hasCorrectTessitura = False
            if not verbose:
                return hasCorrectTessitura            
        
        return hasCorrectTessitura
                
    def containsVoiceOverlap(self, nextPossibility, sortedVoiceList, verbose = False):
        '''
        Returns True if voice overlap is present between self and next possibility. 
        Also takes a sorted list of Voice objects as an argument.
        
        >>> from music21 import *
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B')
        >>> v2 = voice.Voice('T')
        >>> v3 = voice.Voice('A')
        >>> v4 = voice.Voice('S')
        >>> sortedVoiceList = [v1, v2, v3, v4] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B4'), 'A': pitch.Pitch('F4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D4')})
        >>> p1.containsVoiceOverlap(p2, sortedVoiceList)
        False
        >>> p3 = possibility.Possibility({'S': pitch.Pitch('F4'), 'A': pitch.Pitch('F4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D4')})
        >>> p1.containsVoiceOverlap(p3, sortedVoiceList) # Voice overlap, but no voice crossing
        True
        >>> p3.containsVoiceCrossing(sortedVoiceList)
        False
        '''
        hasVoiceOverlap = False
        cp = nextPossibility
        
        for i in range(len(sortedVoiceList)):
            v0 = sortedVoiceList[i]
            lowerPitch0 = self[v0.label]
            lowerPitch1 = cp[v0.label]
            for j in range(i+1, len(sortedVoiceList)):
                v1 = sortedVoiceList[j]
                higherPitch0 = self[v1.label]
                higherPitch1 = cp[v1.label]
                if lowerPitch1 > higherPitch0 or higherPitch1 < lowerPitch0:
                    if verbose:
                        environRules = environment.Environment(_MOD)
                        environRules.warn("Voice overlap between " + v0.label + " and " + v1.label + ".")
                    hasVoiceOverlap = True
                    if not verbose:
                        return hasVoiceOverlap
        
        return hasVoiceOverlap
    
    def containsVoiceCrossing(self, sortedVoiceList, verbose = False):
        '''
        Returns True if voice crossing is present in self. Takes a sorted list
        of Voice objects as an argument.
        
        >>> from music21 import *
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B')
        >>> v2 = voice.Voice('T')
        >>> v3 = voice.Voice('A')
        >>> v4 = voice.Voice('S')
        >>> sortedVoiceList = [v1, v2, v3, v4] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G5'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p1.containsVoiceCrossing(sortedVoiceList) # Alto higher than Soprano  
        True
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2.containsVoiceCrossing(sortedVoiceList)
        False
        '''
        hasVoiceCrossing = False
        
        for i in range(len(sortedVoiceList)):
            v0 = sortedVoiceList[i]
            lowerPitch = self[v0.label]
            for j in range(i+1, len(sortedVoiceList)):
                v1 = sortedVoiceList[j]
                higherPitch = self[v1.label]
                if higherPitch < lowerPitch:
                    if verbose:
                        environRules = environment.Environment(_MOD)
                        environRules.warn("Voice crossing between " + v0.label + " and " + v1.label + ".")
                    hasVoiceCrossing = True
                    if not verbose:
                        return hasVoiceCrossing
        
        return hasVoiceCrossing
    
    def pitchesWithinRange(self, voiceList, verbose = False):
        '''
        Returns true if all pitches in self fall within the upper and lower ranges
        of their respective voices.
        
        >>> from music21 import *
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
        >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
        >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
        >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'))
        >>> voiceList = [v1, v2, v3, v4]
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C3')})
        >>> p1.pitchesWithinRange(voiceList)
        True
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B3'), 'A': pitch.Pitch('G3'), 'T': pitch.Pitch('E3'), 'B': pitch.Pitch('C3')})
        >>> p2.pitchesWithinRange(voiceList) #Soprano note too low
        False
        '''
        pitchesInRange = True
        
        for givenVoice in voiceList:
            pitchList = [self[givenVoice.label]]
            try:
                givenVoice.pitchesInRange(pitchList)
            except voice.RangeException:
                if verbose:
                    environRules = environment.Environment(_MOD)
                    environRules.warn("Pitch in " + givenVoice.label + " voice not within range.")
                pitchesInRange = False
                if not verbose:
                    return pitchesInRange
        
        return pitchesInRange

    # HELPER METHODS
    def findVoicePairs(self, nextPossibility):
        '''
        Group the previous and next pitches of every voice together.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D4')})
        >>> p1.findVoicePairs(p2)
        [(C5, B4, 'S'), (C4, D4, 'B'), (E4, D4, 'T')]
        '''
        cp = nextPossibility
        
        voicePairs = []
        for voiceLabel in cp.keys():
            if voiceLabel not in self.keys():
                raise PossibilityException("Key not shared among both self and next possibilities.")
            voicePair = (self[voiceLabel], cp[voiceLabel], voiceLabel)
            voicePairs.append(voicePair)

        return voicePairs
    
    def findVoiceQuartets(self, nextPossibility):
        '''
        Group the previous and next pitches of one voice with those of another.
        
        >>> from music21 import *
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D4')})
        >>> p1.findVoiceQuartets(p2)
        [(C5, B4, 'S', C4, D4, 'B'), (C5, B4, 'S', E4, D4, 'T'), (C4, D4, 'B', E4, D4, 'T')]
        '''
        cp = nextPossibility
        if len(cp.keys()) <= 1:
            raise PossibilityException("Not enough voices provided in next possibility.")
        for voiceLabel in cp.keys():
            if voiceLabel not in self.keys():
                raise PossibilityException("Key not shared among both self and next possibilities.")
            
        voicePairs = self.findVoicePairs(nextPossibility)        
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
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof