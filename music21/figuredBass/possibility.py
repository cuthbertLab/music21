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
    '''
    Defines a possibility, essentially a chord that could correspond to a figure/bass note pair
    in figured bass, as a python dictionary, where the voice names are keys and pitches are values. 
    Extends the dictionary object through methods that can perform rule checks on a possibility or
    sequence of two possibilities.
    '''
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
        >>> fbRules.topVoiceLeapIntervalLimit = interval.Interval('P8') # Default is None
        >>> fbRules.bottomVoiceLeapIntervalLimit = interval.Interval('P8') # Default is None
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
            if abs(i1.chromatic.semitones) > abs(i0.chromatic.semitones):
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
        if abs(i1.chromatic.semitones) > abs(i0.chromatic.semitones):
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
    def correctTessitura(self, orderedVoiceList, fbRules = rules.Rules(), verbose = False):
        '''
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
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'B': pitch.Pitch('C4')})
        >>> p1.correctTessitura(sortedVoiceList, fbRules)
        True
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B5'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('F4')})
        >>> p2.correctTessitura(sortedVoiceList, fbRules)           
        False    
        '''
        hasCorrectTessitura = True
        orderedVoiceLabels = self.extractVoiceLabels(orderedVoiceList)
        
        if not fbRules.allowVoiceCrossing:
            hasVoiceCrossing = self.containsVoiceCrossing(orderedVoiceLabels, verbose)
            if hasVoiceCrossing:
                hasCorrectTessitura = False
            if not verbose:
                return hasCorrectTessitura
        if fbRules.filterPitchesByRange:
            pitchesInRange = self.pitchesWithinRange(orderedVoiceList, verbose)
            if not pitchesInRange:
                hasCorrectTessitura = False
            if not verbose:
                return hasCorrectTessitura
        
        return hasCorrectTessitura  

    def containsVoiceCrossing(self, orderedVoiceLabels, verbose = False):
        '''
        Returns True if voice crossing is present in self. Takes in an
        ordered list of voice labels which correspond to those in self.
        Raises an error if a voice label in self is not present in the 
        sorted list of voice labels.
                
        >>> from music21 import pitch
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> orderedVoiceLabels = ['B', 'T', 'A', 'S'] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G5'), 'T': pitch.Pitch('E4')})
        >>> p1.containsVoiceCrossing(orderedVoiceLabels) # Alto higher than Soprano  
        True
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('C5'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2.containsVoiceCrossing(orderedVoiceLabels)
        False
        >>> p3 = possibility.Possibility({'X': pitch.Pitch('C5'), 'Y': pitch.Pitch('E4'), 'T': pitch.Pitch('F4')})
        >>> p3.containsVoiceCrossing(orderedVoiceLabels)
        Traceback (most recent call last):
        PossibilityException: Voice labels ['Y', 'X'] not found in orderedVoiceLabels.
        '''
        hasVoiceCrossing = False
        
        voicesNotCompared = []       
        for vl in self.keys():
            if vl not in orderedVoiceLabels:
                voicesNotCompared.append(vl)
                
        if not(len(voicesNotCompared) == 0):
            raise PossibilityException("Voice labels " + str(voicesNotCompared) + " not found in orderedVoiceLabels.")
        
        for i in range(len(orderedVoiceLabels)):
            v0 = orderedVoiceLabels[i]
            if not v0 in self.keys():
                continue
            lowerPitch = self[v0]
            for j in range(i+1, len(orderedVoiceLabels)):
                v1 = orderedVoiceLabels[j]
                if not v1 in self.keys():
                    continue
                higherPitch = self[v1]
                if higherPitch < lowerPitch:
                    if verbose:
                        environRules = environment.Environment(_MOD)
                        environRules.warn("Voice crossing between " + v0 + " and " + v1 + ".")
                    hasVoiceCrossing = True
                    if not verbose:
                        return hasVoiceCrossing
        
        return hasVoiceCrossing
    
    def pitchesWithinRange(self, voiceList, verbose = False):
        '''
        Returns true if all pitches in self fall within the upper and lower ranges
        of their respective voices. Raises an error if there are voice labels in 
        self that don't correspond to voices in voiceList.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
        >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
        >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
        >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'))
        >>> voiceList = [v1, v2, v3, v4]
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'B': pitch.Pitch('C3')})
        >>> p1.pitchesWithinRange(voiceList)
        True
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B3'), 'T': pitch.Pitch('E3'), 'B': pitch.Pitch('C3')})
        >>> p2.pitchesWithinRange(voiceList) #Soprano note too low
        False
        >>> p3 = possibility.Possibility({'X': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'B': pitch.Pitch('F4')})
        >>> p3.pitchesWithinRange(voiceList) # Bass too high
        Traceback (most recent call last):
        PossibilityException: Voices with labels ['X'] not found in voiceList.
        '''
        pitchesInRange = True
        
        voiceLabels = self.extractVoiceLabels(voiceList)
        voicesNotCompared = []       
        for vl in self.keys():
            if vl not in voiceLabels:
                voicesNotCompared.append(vl)

        if not(len(voicesNotCompared) == 0):
            raise PossibilityException("Voices with labels " + str(voicesNotCompared) + " not found in voiceList.")              
        
        for givenVoice in voiceList:
            if not givenVoice.label in self.keys():
                continue
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
       
    def containsVoiceOverlap(self, nextPossibility, orderedVoiceLabels, verbose = False):
        '''
        Returns True if voice overlap is present between self and next possibility. 
        Also takes an ordered list of voice labels as an argument.
        
        Raises an error if there are voice labels shared between self and next possibility
        which can't be found in orderedVoiceLabels. Ignores voices which aren't shared
        between the two, but raises an error if no voices are shared.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B')
        >>> v2 = voice.Voice('T')
        >>> v3 = voice.Voice('A')
        >>> v4 = voice.Voice('S')
        >>> orderedVoiceLabels = ['B', 'T', 'A', 'S'] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C4')})
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B4'), 'A': pitch.Pitch('F4'), 'B': pitch.Pitch('D4')})
        >>> p1.containsVoiceOverlap(p2, orderedVoiceLabels)
        False
        >>> p3 = possibility.Possibility({'S': pitch.Pitch('F4'), 'A': pitch.Pitch('F4'), 'Flute': pitch.Pitch('C6')})
        >>> p1.containsVoiceOverlap(p3, orderedVoiceLabels) # Voice overlap between alto/soprano, but no voice crossing
        True
        
        OMIT_FROM_DOCS
        >>> p4a = possibility.Possibility({'Trombone': pitch.Pitch('F4'), 'Tuba': pitch.Pitch('F4'), 'Flute': pitch.Pitch('C6')})
        >>> p1.containsVoiceOverlap(p4a, orderedVoiceLabels)
        Traceback (most recent call last):
        PossibilityException: No voices to check.        
        >>> p4b = possibility.Possibility({'Trombone': pitch.Pitch('F4'), 'Tuba': pitch.Pitch('F4'), 'S': pitch.Pitch('C6')})
        >>> p1.containsVoiceOverlap(p4b, orderedVoiceLabels)
        Traceback (most recent call last):
        PossibilityException: Need at least two voices to check for voice overlap.
        >>> p5 = possibility.Possibility({'Trombone': pitch.Pitch('G4'), 'A': pitch.Pitch('F4'), 'S': pitch.Pitch('C6')})
        >>> p4b.containsVoiceOverlap(p5, orderedVoiceLabels)
        Traceback (most recent call last):
        PossibilityException: Voice labels ['Trombone'] not found in orderedVoiceLabels. 
        '''
        hasVoiceOverlap = False
        np = nextPossibility
    
        voiceLabelsCompared = []
        for vl in self.keys():
            if vl in np.keys():
                voiceLabelsCompared.append(vl)
                
        if len(voiceLabelsCompared) == 0:
            raise PossibilityException("No voices to check.")
        elif len(voiceLabelsCompared) == 1:
            raise PossibilityException("Need at least two voices to check for voice overlap.")

        voicesNotCompared = []
        for vl in voiceLabelsCompared:
            if vl not in orderedVoiceLabels:
                voicesNotCompared.append(vl)
        
        if not(len(voicesNotCompared) == 0):
            raise PossibilityException("Voice labels " + str(voicesNotCompared) + " not found in orderedVoiceLabels.")

        for i in range(len(orderedVoiceLabels)):
            vl1 = orderedVoiceLabels[i]
            if not vl1 in voiceLabelsCompared:
                continue
            lowerPitch0 = self[vl1]
            lowerPitch1 = np[vl1]
            for j in range(i+1, len(orderedVoiceLabels)):
                vl2 = orderedVoiceLabels[j]
                if not vl2 in voiceLabelsCompared:
                    continue
                higherPitch0 = self[vl2]
                higherPitch1 = np[vl2]
                if lowerPitch1 > higherPitch0 or higherPitch1 < lowerPitch0:
                    if verbose:
                        environRules = environment.Environment(_MOD)
                        environRules.warn("Voice overlap between " + v0.label + " and " + v1.label + ".")
                    hasVoiceOverlap = True
                    if not verbose:
                        return hasVoiceOverlap
        
        return hasVoiceOverlap
    
    def voiceLeapsWithinLimits(self, nextPossibility, voiceList, verbose = False):
        '''
        Checks if voice leaps occur in each voice that is shared among self 
        and next possibility, where a voice leap is defined as a jump greater 
        than maxIntervalLeap as specified in a Voice object. The default 
        maxIntervalLeap for voices is a perfect octave. 
    
        Raises an error if there are voice labels shared between self and next possibility
        which don't correspond to voices in voiceList. Ignores voices which aren't shared
        between the two, but raises an error if no voices are shared.
         
        >>> from music21 import pitch
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
        >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
        >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
        >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'), interval.Interval('M2'))
        >>> voiceList = [v1, v2, v3, v4]
        >>> p1 = possibility.Possibility({'S': pitch.Pitch('C5'), 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': pitch.Pitch('C3')})
        >>> p2 = possibility.Possibility({'S': pitch.Pitch('B4'), 'A': pitch.Pitch('F4'), 'T': pitch.Pitch('D4'), 'B': pitch.Pitch('D3')})
        >>> p1.voiceLeapsWithinLimits(p2, voiceList)
        True
        >>> p3a = possibility.Possibility({'W': pitch.Pitch('G4'), 'X': pitch.Pitch('G4'), 'Y': pitch.Pitch('D4'), 'Z': pitch.Pitch('B3')})
        >>> p1.voiceLeapsWithinLimits(p3a, voiceList)
        Traceback (most recent call last):
        PossibilityException: No voices to check.
        >>> p3b = possibility.Possibility({'S': pitch.Pitch('G4'), 'T': pitch.Pitch('D4'), 'Z': pitch.Pitch('B3')})
        >>> p1.voiceLeapsWithinLimits(p3b, voiceList)
        False
        '''
        leapsWithinLimits = True
        np = nextPossibility
        
        voiceLabelsCompared = []
        for vl in self.keys():
            if vl in np.keys():
                voiceLabelsCompared.append(vl)
                
        if len(voiceLabelsCompared) == 0:
            raise PossibilityException("No voices to check.")

        voiceLabels = self.extractVoiceLabels(voiceList)       
        voicesNotCompared = []
        for vl in voiceLabelsCompared:
            if vl not in voiceLabels:
                voicesNotCompared.append(vl)
        
        if not(len(voicesNotCompared) == 0):
            raise PossibilityException("Voices with labels " + str(voicesNotCompared) + " not found in voiceList.")              

        for givenVoice in voiceList:
            if not givenVoice.label in voiceLabelsCompared:
                continue
            v1n1 = self[givenVoice.label]
            v1n2 = np[givenVoice.label]
            i1 = interval.notesToInterval(v1n1, v1n2)
            if abs(i1.chromatic.semitones) > abs(givenVoice.maxIntervalLeap.chromatic.semitones):
                if verbose:
                    environRules = environment.Environment(_MOD)
                    environRules.warn("Voice leap in " + givenVoice.label + " voice.")
                leapsWithinLimits = False
                if not verbose:
                    return leapsWithinLimits

        return leapsWithinLimits
        
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
    
    def extractVoiceLabels(self, voiceList):
        voiceLabels = []
        for v in voiceList:
            voiceLabels.append(v.label)
        
        return voiceLabels
        

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