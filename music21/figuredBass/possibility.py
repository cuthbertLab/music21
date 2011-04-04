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

from music21 import chord
from music21 import environment
from music21 import interval
from music21 import pitch
from music21 import voiceLeading

from music21.figuredBass import rules
from music21.figuredBass import voice

_MOD = "possibility.py"

class Possibility(dict):
    '''
    Extends the concept (but not the class) of a chord in music21 by allowing the labeling of voices 
    through the subclassing of the python dictionary. Named Possibility because it is intended to 
    encapsulate a possibility for a figured bass note/figure combination, but can be used in many other ways.
    '''
    # INITIALIZATION METHODS
    def __init__(self, *args):
        '''
        Creates a Possibility instance when you provide a python Dict, 
        where a voice label (key) corresponds to a music21 Pitch 
        or pitch string (value). Pitch strings are automatically converted to Pitch instances. 
        Assigning a voice label to anything else results in an error.
        
        >>> from music21 import pitch
        >>> from music21 import note
        >>> from music21.figuredBass import possibility
        
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': pitch.Pitch('G4'), 'T': pitch.Pitch('E4'), 'B': 'C3'})
        >>> p1
        {'A': G4, 'S': C5, 'B': C3, 'T': E4}
        >>> p2 = possibility.Possibility()
        >>> p2
        {}
        >>> p2['B'] = pitch.Pitch('C3')
        >>> p2['T'] = pitch.Pitch('E4')
        >>> p2['A'] = 'G4'
        >>> p2['S'] = 'C5'
        >>> p2
        {'A': G4, 'S': C5, 'B': C3, 'T': E4}    
        >>> p2['Tuba'] = note.Note('C3')
        Traceback (most recent call last):
        PossibilityException: Can't set ->Tuba<-: Can't convert -><music21.note.Note C><- to a music21 pitch.Pitch instance!
        >>> p2['Trombone'] = 'Special trombone pitch'
        Traceback (most recent call last):
        PossibilityException: Can't set ->Trombone<-: Can't convert ->Special trombone pitch<- to a music21 pitch.Pitch instance!
        '''
        try:
            for voiceLabel in args[0].keys():
                pitchValue = args[0][voiceLabel]
                if not isinstance(pitchValue, pitch.Pitch):
                    if type(pitchValue) == str:
                        try:
                            args[0][voiceLabel] = pitch.Pitch(pitchValue)
                        except pitch.PitchException:
                            raise PossibilityException("Cannot create Possibility: ->" + str(pitchValue) + "<- not a valid pitch or pitch string!")
                    else:
                        raise PossibilityException("Cannot create Possibility: ->" + str(pitchValue) + "<- not a valid pitch or pitch string!")
            dict.__init__(self, *args)
        except IndexError:
            dict.__init__(self, *args)
    
    def __setitem__(self, voiceLabel, pitchValue):
        '''
        Set a voice label to a music21 Pitch or pitch string. 
        Pitch strings are automatically converted to Pitch instances. 
        Assigning a voice label to anything else results in an error.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility()
        >>> p1['B'] = pitch.Pitch('C3')
        >>> p1['B']
        C3
        >>> p1['T'] = 'G3'
        >>> p1['T']
        G3
        >>> p1['A'] = 'Not a pitch or pitch string'
        Traceback (most recent call last):
        PossibilityException: Can't set ->A<-: Can't convert ->Not a pitch or pitch string<- to a music21 pitch.Pitch instance!
        '''
        newPitchValue = pitchValue
        if not isinstance(pitchValue, pitch.Pitch):
            if type(pitchValue) == str:
                try:
                    newPitchValue = pitch.Pitch(pitchValue)
                except pitch.PitchException:
                    raise PossibilityException("Can't set ->" + str(voiceLabel) + "<-: Can't convert ->" + str(pitchValue) + "<- to a music21 pitch.Pitch instance!")
            else:
                raise PossibilityException("Can't set ->" + str(voiceLabel) + "<-: Can't convert ->" + str(pitchValue) + "<- to a music21 pitch.Pitch instance!")
        dict.__setitem__(self, voiceLabel, newPitchValue)
    
    def numVoices(self):
        return len(self.keys())
    
    #def __str__(self):
    #    pass
    
    #def __repr__(self):
    #    pass
    
    # CHORD FORMATION RULES    
    def isIncomplete(self, pitchNamesToContain, verbose = False):
        '''
        Returns True if a possibility is incomplete, a.k.a. if it doesn't contain at least
        one of each pitch name provided.
        
        >>> from music21.figuredBass import possibility
        >>> pitchNames = ['C','E','G']
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p1.isIncomplete(pitchNames)
        False
        >>> p1['T'] = 'C4'
        >>> p1.isIncomplete(pitchNames) # Doesn't contain 'E'
        True
        '''
        pitchNamesContained = []
        for voiceLabel in self.keys():
            if self[voiceLabel].name not in pitchNamesContained:
                pitchNamesContained.append(self[voiceLabel].name)
        pitchNamesContained.sort()
        pitchNamesToContain.sort()
        if not cmp(pitchNamesContained, pitchNamesToContain):
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
        
        
        For instance, if topVoicesMaxIntervalSeparation is P8 then if this method returns
        true then all the notes of the implied chord except the bass can be played by
        most adult pianists.
        
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p1.topVoicesWithinLimit(interval.Interval('P8'))
        True
        >>> p1['T'] = 'E3'
        >>> p1.topVoicesWithinLimit(interval.Interval('P8')) # Tenor and Soprano more than an octave apart
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
    def parallelFifths(self, nextPossibility, verbose = False):
        '''
        Returns True if there are parallel fifths between prevPossibility (self) and nextPossibility.

        Ignores any voices which aren't shared between the two possibilities, but 
        raises an error if not enough voices are shared.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': 'G3', 'Bass': 'C3'})
        >>> p2 = possibility.Possibility({'Tenor': 'A3', 'Bass': 'D3'})
        >>> p1.parallelFifths(p2)
        True
        >>> p3 = {'Soprano': 'D5', 'Alto': 'B4'}
        >>> p1.parallelFifths(p3)
        Traceback (most recent call last):
        PossibilityException: Need at least two shared voices to check for parallel fifths.

        ''' 
        hasParallelFifth = False
        try:
            voiceQuartets = self.voiceQuartets(nextPossibility)
        except PossibilityException:
            raise PossibilityException("Need at least two shared voices to check for parallel fifths.")
        
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
        
    def parallelOctaves(self, nextPossibility, verbose = False):
        '''
        Returns True if there are parallel octaves between prevPossibility (self) and nextPossibility.

        Ignores any voices which aren't shared between the two possibilities, but 
        raises an error if not enough voices are shared.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': 'C4', 'Bass': 'C3'})
        >>> p2 = possibility.Possibility({'Tenor': 'D4', 'Bass': 'D3'})
        >>> p1.parallelOctaves(p2)
        True
        >>> p3 = {'Soprano': 'D5', 'Alto': 'B4'}
        >>> p1.parallelOctaves(p3)
        Traceback (most recent call last):
        PossibilityException: Need at least two shared voices to check for parallel octaves.
        '''        
        hasParallelOctave = False
        try:
            voiceQuartets = self.voiceQuartets(nextPossibility)
        except PossibilityException:
            raise PossibilityException("Need at least two shared voices to check for parallel octaves.")
        
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
        
    # HIDDEN INTERVAL RULES
    def hiddenFifth(self, nextPossibility, vlTop, vlBottom, verbose = False):
        '''
        Returns True if there is no hidden fifth in going from prevPossibility (self) to nextPossibility
        between the two voices specified as vlTop and vlBottom, which are usually the highest
        and lowest voice parts in the piece (since these are the only two voices where 
        hidden fifths are usually forbidden.

        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Soprano': 'E5', 'Bass': 'C3'})
        >>> p2 = possibility.Possibility({'Soprano': 'A5', 'Bass': 'D3'})
        >>> p1.hiddenFifth(p2, 'Soprano', 'Bass')
        True
        >>> p3 = possibility.Possibility({'Soprano': 'A#5', 'Bass': 'D3'})
        >>> p1.hiddenFifth(p3, 'Soprano', 'Bass')
        False
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
    
    def hiddenOctave(self, nextPossibility, vlTop, vlBottom, verbose = False):
        '''
        Returns True if there is no hidden fifth in going from prevPossibility (self) to nextPossibility.
        Asked to provide the voice labels (keys) of the top and bottom voices. 

        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Soprano': 'A5', 'Bass': 'C3'})
        >>> p2 = possibility.Possibility({'Soprano': 'D6', 'Bass': 'D3'})
        >>> p1.hiddenOctave(p2, 'Soprano', 'Bass')
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
    def voiceCrossing(self, orderedVoiceLabels, verbose = False):
        '''
        Returns True if Possibility (self) contains a voice crossing.
        Takes in an ordered list of voice labels, from lowest to highest,
        which correspond to keys in Possibility. 
        
        
        Raises an error if a voice label(s) in Possibility is not present in the 
        ordered list.

        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> orderedVoiceLabels = ['B', 'T', 'A', 'S'] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G5', 'T': 'E4'})
        >>> p1.voiceCrossing(orderedVoiceLabels) # Alto higher than Soprano  
        True
        >>> p2 = possibility.Possibility({'S': 'C5', 'T': 'E4', 'B': 'C4'})
        >>> p2.voiceCrossing(orderedVoiceLabels)
        False
        >>> p3 = possibility.Possibility({'X': 'C5', 'Y': 'E4', 'T': 'F4'})
        >>> p3.voiceCrossing(orderedVoiceLabels)
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
        Returns True if the pitch of each voice falls within its upper and lower
        ranges. 
        
        
        Takes in a list of Voice instances. Supplying a Range to a Voice is optional,
        and if omitted for a certain Voice then all pitches are presumed in range.
        
        
        Raises an error if a voice label(s) in Possibility doesn't correspond to Voice 
        instances in voiceList.
        
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
        >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
        >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
        >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'))
        >>> voiceList = [v1, v2, v3, v4]
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'B': 'C3'})
        >>> p1.pitchesWithinRange(voiceList)
        True
        >>> p2 = possibility.Possibility({'S': 'B3', 'T': 'E3', 'B': 'C3'})
        >>> p2.pitchesWithinRange(voiceList) #Soprano note too low
        False
        >>> p3 = possibility.Possibility({'X': 'C5', 'A': 'G4', 'B': 'F4'})
        >>> p3.pitchesWithinRange(voiceList) # Bass too high
        Traceback (most recent call last):
        PossibilityException: Voices with labels ['X'] not found in voiceList.
        '''
        pitchesInRange = True
        
        voiceLabels = extractVoiceLabels(voiceList)
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
    
    def voiceOverlap(self, nextPossibility, orderedVoiceLabels, verbose = False):
        '''
        Returns True if there is voice overlap between prevPossibility (self) and nextPossibility.
        Takes in a list of ordered voice labels, from lowest to highest.

        
        Ignores voices which aren't shared between the two, but raises an error if (1) There are
        voices shared between the two Possibility instances which correspond to voice labels not 
        found in the ordered list and (2) If less than two voices are shared between the two
        Possibility instances.
        
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> orderedVoiceLabels = ['B', 'T', 'A', 'S'] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C4'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'A': 'F4', 'B': 'D4'})
        >>> p1.voiceOverlap(p2, orderedVoiceLabels)
        False
        >>> p3 = possibility.Possibility({'S': 'F4', 'A': 'F4', 'Flute': 'C6'})
        >>> p1.voiceOverlap(p3, orderedVoiceLabels) # Voice overlap between alto/soprano, but no voice crossing
        True
        
        OMIT_FROM_DOCS
        >>> p4a = possibility.Possibility({'Trombone': 'F4', 'Tuba': 'F4', 'Flute': 'C6'})
        >>> p1.voiceOverlap(p4a, orderedVoiceLabels)
        Traceback (most recent call last):
        PossibilityException: No voices to check.        
        >>> p4b = possibility.Possibility({'Trombone': 'F4', 'Tuba': 'F4', 'S': 'C6'})
        >>> p1.voiceOverlap(p4b, orderedVoiceLabels)
        Traceback (most recent call last):
        PossibilityException: Need at least two voices to check for voice overlap.
        >>> p5 = possibility.Possibility({'Trombone': 'G4', 'A': 'F4', 'S': 'C6'})
        >>> p4b.voiceOverlap(p5, orderedVoiceLabels)
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
                        environRules.warn("Voice overlap between " + vl1 + " and " + vl2 + ".")
                    hasVoiceOverlap = True
                    if not verbose:
                        return hasVoiceOverlap
        
        return hasVoiceOverlap
    
    def voiceLeapsWithinLimits(self, nextPossibility, voiceList, verbose = False):
        '''
        Returns True if there are no illegal voice leaps present between prevPossibility (self) and nextPossibility.
        Takes in a list of Voice instances which supply the maximum interval jump allowed for each voice.
        The default max interval is a perfect octave. You can specify another max interval by inputting it as the
        third input of each voice.  In the example below, the Soprano is limited to stepwise motion.
        
        Ignores voices which aren't shared between the two Possibility instances, but raises an error if
        there are voices shared between the two that don't correspond to Voice instances in voiceList.
         
        >>> from music21.figuredBass import voice
        >>> from music21.figuredBass import possibility
        >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
        >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
        >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
        >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'), interval.Interval('M2'))
        >>> voiceList = [v1, v2, v3, v4]
        
        
        This example is True because all voices move by step.
        
        
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'A': 'F4', 'T': 'D4', 'B': 'D3'})
        >>> p1.voiceLeapsWithinLimits(p2, voiceList)
        True
        
        
        This example is False because the Soprano moves by 4th and is restricted 
        to stepwise motion.  The Alto also moves by 4th, but that's okay because
        the max interval (by default) is an Octave.
        
        
        >>> p3b = possibility.Possibility({'S':'G4', 'T': 'D4', 'Z': 'B3'})
        >>> p1.voiceLeapsWithinLimits(p3b, voiceList)
        False



        >>> p3a = possibility.Possibility({'W': 'G4', 'X': 'G4', 'Y': 'D4', 'Z': 'B3'})
        >>> p1.voiceLeapsWithinLimits(p3a, voiceList)
        Traceback (most recent call last):
        PossibilityException: No voices to check.
        '''
        leapsWithinLimits = True
        np = nextPossibility
        
        voiceLabelsCompared = []
        for vl in self.keys():
            if vl in np.keys():
                voiceLabelsCompared.append(vl)
                
        if len(voiceLabelsCompared) == 0:
            raise PossibilityException("No voices to check.")

        voiceLabels = extractVoiceLabels(voiceList)       
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
    def voicePairs(self, nextPossibility):
        '''
        Group pitches of prevPossibility (self) and nextPossibility which 
        correspond to the same voice together.
        Raises an error if the Possibility instances don't share at least
        one voice in common.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'B': 'C4'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'T': 'D4', 'B': 'D4'})
        >>> p1.voicePairs(p2)
        [(C5, B4, 'S'), (C4, D4, 'B')]
        >>> p3 = possibility.Possibility({'X': 'B4', 'Y': 'D4'})
        >>> p1.voicePairs(p3)
        Traceback (most recent call last):
        PossibilityException: No shared voices to group together.
        '''
        np = nextPossibility
        
        voicePairs = []
        for voiceLabel in self.keys():
            if voiceLabel in np.keys():
                voicePair = (self[voiceLabel], np[voiceLabel], voiceLabel)
                voicePairs.append(voicePair)
        
        if len(voicePairs) == 0:
            raise PossibilityException("No shared voices to group together.")
        
        return voicePairs
    
    def voiceQuartets(self, nextPossibility):
        '''
        Group all voice pairs of prevPossibility (self) and nextPossibility together.
        Raises an error if the Possibility instances don't have at least two voices in common.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'T': 'E4', 'B': 'C4'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'T': 'D4', 'B': 'D4'})
        >>> p1.voiceQuartets(p2)
        [(C5, B4, 'S', C4, D4, 'B'), (C5, B4, 'S', E4, D4, 'T'), (C4, D4, 'B', E4, D4, 'T')]
        >>> p3 = possibility.Possibility({'X': 'B4', 'Y': 'D4', 'B': 'D4'})
        >>> p1.voiceQuartets(p3)
        Traceback (most recent call last):
        PossibilityException: Need at least two shared voices to find voice quartets.
        '''            
        voicePairs = self.voicePairs(nextPossibility)        
        if len(voicePairs) == 1:
            raise PossibilityException("Need at least two shared voices to find voice quartets.")
        
        voiceQuartets = []
        
        for i in range(len(voicePairs)):
            for j in range(i+1,len(voicePairs)):
                voiceQuartets.append(voicePairs[i] + voicePairs[j])
        
        return voiceQuartets
    
    def chordify(self):
        '''
        Turns Possibility (self) into a music21 chord.Chord instance.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'T': 'E4', 'B': 'C4'})
        >>> p1.chordify()
        <music21.chord.Chord C4 E4 C5>
        >>> p2 = possibility.Possibility({'S': 'B4', 'T': 'D4', 'B': 'D4'})
        >>> p2.chordify()
        <music21.chord.Chord D4 D4 B4>
        '''
        
        pitchesInChord = []
        for vl in self.keys():
            pitchesInChord.append(self[vl])
        
        pitchesInChord.sort()
        return chord.Chord(pitchesInChord)
    
    def isDominantSeventh(self):
        '''
        Returns True if Possibility (self) is a Dominant Seventh. Possibility must be correctly spelled.
        
        >>> from music21.figuredBass import possibility
        >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
        >>> possibA.isDominantSeventh()
        True
        >>> possibB = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'B5'})
        >>> possibB.isDominantSeventh() # Missing fifth
        False
        '''
        dominantSeventh = self.chordify()
        if dominantSeventh.isDominantSeventh():
            return True
        else:
            return False
        
    def isDiminishedSeventh(self):
        '''
        Returns True if Possibility (self) is a (fully) Diminished Seventh. Possibility must be correctly spelled.
    
        >>> from music21.figuredBass import possibility
        >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
        >>> possibA.isDiminishedSeventh()
        True
        >>> possibB = possibility.Possibility({'B': 'C#3', 'T': 'E3', 'A': 'E4', 'S': 'B-4'})
        >>> possibB.isDiminishedSeventh() # Missing fifth
        False
        '''
        diminishedSeventh = self.chordify()
        if diminishedSeventh.isDiminishedSeventh():
            return True
        else:
            return False


def extractVoiceLabels(voiceList):
    '''
    Extract voice labels in order from a voice list, and then return them.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import voice
    >>> v1 = voice.Voice('B', voice.Range('E2', 'E4'))
    >>> v2 = voice.Voice('T', voice.Range('C3', 'A4'))
    >>> v3 = voice.Voice('A', voice.Range('F3', 'G5'))
    >>> v4 = voice.Voice('S', voice.Range('C4', 'A5'))
    >>> orderedVoiceList = [v1, v2, v3, v4]
    >>> possibility.extractVoiceLabels(orderedVoiceList)
    ['B', 'T', 'A', 'S']
    '''
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