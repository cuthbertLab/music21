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
from music21.figuredBass import part

_MOD = "possibility.py"

class Possibility(dict):
    '''
    Extends the concept (but not the class) of a chord in music21 by allowing the labeling of parts 
    through the subclassing of the python dictionary. Named Possibility because it is intended to 
    encapsulate a possibility for a figured bass note/figure combination, but can be used in many other ways.
    '''
    # INITIALIZATION METHODS
    # ----------------------
    def __init__(self, *args):
        '''
        Creates a Possibility instance when you provide a python Dict, 
        where a part label (key) corresponds to a music21 Pitch 
        or pitch string (value). Pitch strings are automatically converted to Pitch instances. 
        Assigning a part label to anything else results in an error.
        
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
            for partLabel in args[0].keys():
                pitchValue = args[0][partLabel]
                if not isinstance(pitchValue, pitch.Pitch):
                    if type(pitchValue) == str:
                        try:
                            args[0][partLabel] = pitch.Pitch(pitchValue)
                        except pitch.PitchException:
                            raise PossibilityException("Cannot create Possibility: ->" + str(pitchValue) + "<- not a valid pitch or pitch string!")
                    else:
                        raise PossibilityException("Cannot create Possibility: ->" + str(pitchValue) + "<- not a valid pitch or pitch string!")
            dict.__init__(self, *args)
        except IndexError:
            dict.__init__(self, *args)
        
        self.environRules = environment.Environment(_MOD)       
    
    def __setitem__(self, partLabel, pitchValue):
        '''
        Set a part label to a music21 Pitch or pitch string. 
        Pitch strings are automatically converted to Pitch instances. 
        Assigning a part label to anything else results in an error.
        
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
                    raise PossibilityException("Can't set ->" + str(partLabel) + "<-: Can't convert ->" + str(pitchValue) + "<- to a music21 pitch.Pitch instance!")
            else:
                raise PossibilityException("Can't set ->" + str(partLabel) + "<-: Can't convert ->" + str(pitchValue) + "<- to a music21 pitch.Pitch instance!")
        dict.__setitem__(self, partLabel, newPitchValue)
    
    def numParts(self):
        return len(self.keys())
    
    #def __str__(self):
    #    pass
    
    #def __repr__(self):
    #    pass
    
    # SINGLE POSSIBILITY RULE-CHECKING METHODS
    # ----------------------------------------
    def isIncomplete(self, pitchNamesToContain, verbose = False):
        '''
        Returns True if a Possibility is incomplete, a.k.a. if it doesn't contain at least
        one instance of each pitch class derived from the names provided.
        
        If the Possibility contains an instance of each pitch class, but also contains other
        pitch classes not found in pitchNamesToContain, a PossibilityException is raised.
        
        If a Possibility contains exactly the number of pitch classes as pitchNamesToContain, 
        the method returns False.
                 
        >>> from music21.figuredBass import possibility
        >>> pitchNames = ['C','E','G']
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p1.isIncomplete(pitchNames)
        False
        >>> p1['T'] = 'C4'
        >>> p1.isIncomplete(pitchNames) # Doesn't contain 'E'
        True
        >>> p2 = possibility.Possibility({'S': 'B-5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p2.isIncomplete(pitchNames)
        Traceback (most recent call last):
        PossibilityException: Possibility contains pitch classes not found in pitchNamesToContain.
        >>> pitchNames.append('B-')
        >>> p2.isIncomplete(pitchNames)
        False
        '''
        isIncomplete = False
        pitchNamesContained = []
        for partLabel in self.keys():
            if self[partLabel].name not in pitchNamesContained:
                pitchNamesContained.append(self[partLabel].name)
        for pitchName in pitchNamesToContain:
            if pitchName not in pitchNamesContained:
                isIncomplete = True
                if verbose:
                    self.environRules.warn("Pitch class " + pitchName + " not in " + str(self) + ".")
                else:
                    return isIncomplete
        if not isIncomplete and (len(pitchNamesContained) > len(pitchNamesToContain)):
            if verbose:
                for pitchName in pitchNamesContained:
                    if pitchName not in pitchNamesToContain:
                        self.environRules.warn("Pitch class " + pitchName + " in " + str(self) + " not among pitchNamesToContain.")         
            raise PossibilityException("Possibility contains pitch classes not found in pitchNamesToContain.")

        return isIncomplete
    
    def upperPartsWithinLimit(self, maxSemitoneSeparation = 12, verbose = False):
        '''
        Returns True if the pitches in the upper parts of a Possibility are found within
        maxSemitoneSeparation of each other, inclusive. The upper parts include all the 
        (part label, pitch) pairs except that which contains the root of the implied chord. 
        The labels are not factored into this consideration, only pitches.
                
        The default value of maxSemitoneSeparation is 12 semitones, enharmonically equivalent to
        a perfect octave. If this method returns True for this default value, then all the notes
        of the implied chord except the bass can be played by most adult pianists.        
                
        If maxSemitoneSeparation = None, the method just returns True.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p1.upperPartsWithinLimit()
        True
        >>> p1['T'] = 'E3'
        >>> p1.upperPartsWithinLimit() # Tenor and Soprano, Alto more than 12 semitones apart
        False
        '''
        upperPartsWithinLimit = True
        if maxSemitoneSeparation == None:
            return upperPartsWithinLimit
        pitchesContained = []
        for partLabel in self.keys():
            pitchesContained.append((self[partLabel], partLabel))
        pitchesContained.sort()
        
        for pitch1Index in range(1, len(pitchesContained)):
            for pitch2Index in range(pitch1Index, len(pitchesContained)):
                (pitch1, vl1) = pitchesContained[pitch1Index]
                (pitch2, vl2) = pitchesContained[pitch2Index]
                i1 = interval.notesToInterval(pitch1, pitch2)
                if i1.chromatic.semitones > maxSemitoneSeparation:
                    if verbose:
                        self.environRules.warn(vl1 + " and " + vl2 + " in " + str(self) + " are greater than " + str(maxSemitoneSeparation) + " semitones apart.")
                    upperPartsWithinLimit = False
                    if not verbose:
                        return upperPartsWithinLimit
        
        return upperPartsWithinLimit

    def pitchesWithinSoundingRange(self, partList, verbose = False):
        '''
        Takes in a list of Part objects, partList. Each pitch in Possibility corresponds to a 
        Part in partList by means of its dictionary key which also serves as a Part label. 

        Returns True if every pitch in Possibility falls within the bounds of its SoundingRange, 
        inclusive.         
        
        A PossibilityException is raised if there are pitches in Possibility which don't have 
        associated Part objects in partList. It is, however, okay to provide more Part objects
        than is necessary.
                
        >>> from music21.figuredBass import part
        >>> from music21.figuredBass import possibility
        >>> p1 = part.Part('B','E2','E4')
        >>> p2 = part.Part('T','C3','A4')
        >>> p3 = part.Part('A','F3','G5')
        >>> p4 = part.Part('S','C4','A5')
        >>> partList = [p1, p2, p3, p4]        
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'B': 'C3'})
        >>> p1.pitchesWithinSoundingRange(partList)
        True
        >>> p2 = possibility.Possibility({'S': 'B3', 'T': 'E3', 'B': 'C3'})
        >>> p2.pitchesWithinSoundingRange(partList) #Soprano note too low
        False
        >>> p3 = possibility.Possibility({'X': 'C5', 'A': 'G4', 'B': 'F4'})
        >>> p3.pitchesWithinSoundingRange(partList) # Bass too high
        Traceback (most recent call last):
        PossibilityException: Parts with labels ['X'] not found in partList.
        '''
        pitchesInSoundingRange = True
        
        partLabels = extractPartLabels(partList)
        partsNotCompared = []       
        for vl in self.keys():
            if vl not in partLabels:
                partsNotCompared.append(vl)

        if not(len(partsNotCompared) == 0):
            raise PossibilityException("Parts with labels " + str(partsNotCompared) + " not found in partList.")              
        
        for givenPart in partList:
            if not givenPart.label in self.keys():
                continue
            pitchList = [self[givenPart.label]]
            try:
                givenPart.pitchesInSoundingRange(pitchList)
            except part.RangeException:
                if verbose:
                    self.environRules.warn("Pitch in " + givenPart.label + " part not within range.")
                pitchesInSoundingRange = False
                if not verbose:
                    return pitchesInSoundingRange

        return pitchesInSoundingRange

    def voiceCrossing(self, partList, verbose = False):
        '''
        Takes in a list of Part objects, partList. Each pitch in Possibility corresponds to a 
        Part in partList by means of its dictionary key which also serves as a Part label. 
    
        Returns True if there is voice crossing present between any two pitches in Possibility. 
        The order of Part objects is determined by calling sort() on partList. They do not 
        have to be provided in order.    
        
        A PossibilityException is raised if there are pitches in Possibility which don't have 
        associated Part objects in partList. It is, however, okay to provide more Part objects
        than is necessary.

        >>> from music21.figuredBass import part
        >>> from music21.figuredBass import possibility
        >>> p1 = part.Part('B','E2','E4')
        >>> p2 = part.Part('T','C3','A4')
        >>> p3 = part.Part('A','F3','G5')
        >>> p4 = part.Part('S','C4','A5')
        >>> partList = [p4, p2, p1, p3]
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G5', 'T': 'E4'})
        >>> p1.voiceCrossing(partList) # Alto higher than Soprano  
        True
        >>> p2 = possibility.Possibility({'S': 'C5', 'T': 'E4', 'B': 'C4'})
        >>> p2.voiceCrossing(partList)
        False
        >>> p3 = possibility.Possibility({'X': 'C5', 'Y': 'E4', 'T': 'F4'})
        >>> p3.voiceCrossing(partList)
        Traceback (most recent call last):
        PossibilityException: Part labels ['Y', 'X'] not found in orderedPartLabels.
        '''
        hasVoiceCrossing = False
        
        partList.sort()
        partLabels = extractPartLabels(partList)
        partsNotCompared = []       
        for vl in self.keys():
            if vl not in partLabels:
                partsNotCompared.append(vl)
                
        if not(len(partsNotCompared) == 0):
            raise PossibilityException("Parts with labels " + str(partsNotCompared) + " not found in partList.")              
        
        for i in range(len(partLabels)):
            v0 = partLabels[i]
            if not v0 in self.keys():
                continue
            lowerPitch = self[v0]
            for j in range(i+1, len(partLabels)):
                v1 = partLabels[j]
                if not v1 in self.keys():
                    continue
                higherPitch = self[v1]
                if higherPitch < lowerPitch:
                    if verbose:
                        self.environRules.warn("Voice crossing between " + v0 + " and " + v1 + " in " + str(self) + ".")
                    hasVoiceCrossing = True
                    if not verbose:
                        return hasVoiceCrossing
        
        return hasVoiceCrossing

    # CONSECUTIVE POSSIBILITY RULE-CHECKING METHODS
    # ---------------------------------------------
    def parallelFifths(self, nextPossibility, verbose = False):
        '''
        Returns True if there are parallel fifths between prevPossibility (self) and nextPossibility.

        Ignores any parts which aren't shared between the two possibilities, but 
        raises an error if not enough parts are shared.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': 'G3', 'Bass': 'C3'})
        >>> p2 = possibility.Possibility({'Tenor': 'A3', 'Bass': 'D3'})
        >>> p1.parallelFifths(p2)
        True
        >>> p3 = {'Soprano': 'D5', 'Alto': 'B4'}
        >>> p1.parallelFifths(p3)
        Traceback (most recent call last):
        PossibilityException: Need at least two shared parts to check for parallel fifths.

        ''' 
        hasParallelFifth = False
        try:
            partQuartets = self.partQuartets(nextPossibility)
        except PossibilityException:
            raise PossibilityException("Need at least two shared parts to check for parallel fifths.")
        
        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in partQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.parallelFifth():
                if verbose:
                    self.environRules.warn("Parallel fifths between " + vl1 + " and " + vl2 + ".")
                hasParallelFifth = True
                if not verbose:
                    return hasParallelFifth
        
        return hasParallelFifth
        
    def parallelOctaves(self, nextPossibility, verbose = False):
        '''
        Returns True if there are parallel octaves between prevPossibility (self) and nextPossibility.

        Ignores any parts which aren't shared between the two possibilities, but 
        raises an error if not enough parts are shared.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'Tenor': 'C4', 'Bass': 'C3'})
        >>> p2 = possibility.Possibility({'Tenor': 'D4', 'Bass': 'D3'})
        >>> p1.parallelOctaves(p2)
        True
        >>> p3 = {'Soprano': 'D5', 'Alto': 'B4'}
        >>> p1.parallelOctaves(p3)
        Traceback (most recent call last):
        PossibilityException: Need at least two shared parts to check for parallel octaves.
        '''        
        hasParallelOctave = False
        try:
            partQuartets = self.partQuartets(nextPossibility)
        except PossibilityException:
            raise PossibilityException("Need at least two shared parts to check for parallel octaves.")
        
        for (pitchA1, pitchA2, vl1, pitchB1, pitchB2, vl2) in partQuartets:
            vlq = voiceLeading.VoiceLeadingQuartet(pitchA1, pitchA2, pitchB1, pitchB2)
            if vlq.parallelOctave():
                if verbose:
                    self.environRules.warn("Parallel octaves between " + vl1 + " and " + vl2 + ".")
                hasParallelOctave = True
                if not verbose:
                    return hasParallelOctave
        
        return hasParallelOctave
        
    def hiddenFifth(self, nextPossibility, vlTop, vlBottom, verbose = False):
        '''
        Returns True if there is no hidden fifth in going from prevPossibility (self) to nextPossibility
        between the two parts specified as vlTop and vlBottom, which are usually the highest
        and lowest part parts in the piece (since these are the only two parts where 
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
                self.environRules.warn("Hidden fifths between " + vlTop + " and " + vlBottom + ".")
            hasHiddenFifth = True
            if not verbose:
                return hasHiddenFifth
            
        return hasHiddenFifth
    
    def hiddenOctave(self, nextPossibility, vlTop, vlBottom, verbose = False):
        '''
        Returns True if there is no hidden fifth in going from prevPossibility (self) to nextPossibility.
        Asked to provide the part labels (keys) of the top and bottom parts. 

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
                self.environRules.warn("Hidden octaves between " + vlTop + " and " + vlBottom + ".")
            hasHiddenOctave = True
            if not verbose:
                return hasHiddenOctave
            
        return hasHiddenOctave

    def voiceOverlap(self, nextPossibility, orderedPartLabels, verbose = False):
        '''
        Returns True if there is voice overlap between prevPossibility (self) and nextPossibility.
        Takes in a list of ordered part (voice) labels, from lowest to highest.

        
        Ignores parts which aren't shared between the two, but raises an error if (1) There are
        parts shared between the two Possibility instances which correspond to part labels not 
        found in the ordered list and (2) If less than two parts are shared between the two
        Possibility instances.
        
        >>> from music21.figuredBass import part
        >>> from music21.figuredBass import possibility
        >>> orderedPartLabels = ['B', 'T', 'A', 'S'] #From lowest to highest
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C4'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'A': 'F4', 'B': 'D4'})
        >>> p1.voiceOverlap(p2, orderedPartLabels)
        False
        >>> p3 = possibility.Possibility({'S': 'F4', 'A': 'F4', 'Flute': 'C6'})
        >>> p1.voiceOverlap(p3, orderedPartLabels) # Part overlap between alto/soprano, but no part crossing
        True
        
        OMIT_FROM_DOCS
        >>> p4a = possibility.Possibility({'Trombone': 'F4', 'Tuba': 'F4', 'Flute': 'C6'})
        >>> p1.voiceOverlap(p4a, orderedPartLabels)
        Traceback (most recent call last):
        PossibilityException: No parts to check.        
        >>> p4b = possibility.Possibility({'Trombone': 'F4', 'Tuba': 'F4', 'S': 'C6'})
        >>> p1.voiceOverlap(p4b, orderedPartLabels)
        Traceback (most recent call last):
        PossibilityException: Need at least two parts to check for part overlap.
        >>> p5 = possibility.Possibility({'Trombone': 'G4', 'A': 'F4', 'S': 'C6'})
        >>> p4b.voiceOverlap(p5, orderedPartLabels)
        Traceback (most recent call last):
        PossibilityException: Part labels ['Trombone'] not found in orderedPartLabels. 
        '''
        hasVoiceOverlap = False
        np = nextPossibility
    
        partLabelsCompared = []
        for vl in self.keys():
            if vl in np.keys():
                partLabelsCompared.append(vl)
                
        if len(partLabelsCompared) == 0:
            raise PossibilityException("No parts to check.")
        elif len(partLabelsCompared) == 1:
            raise PossibilityException("Need at least two parts to check for part overlap.")

        partsNotCompared = []
        for vl in partLabelsCompared:
            if vl not in orderedPartLabels:
                partsNotCompared.append(vl)
        
        if not(len(partsNotCompared) == 0):
            raise PossibilityException("Part labels " + str(partsNotCompared) + " not found in orderedPartLabels.")

        for i in range(len(orderedPartLabels)):
            vl1 = orderedPartLabels[i]
            if not vl1 in partLabelsCompared:
                continue
            lowerPitch0 = self[vl1]
            lowerPitch1 = np[vl1]
            for j in range(i+1, len(orderedPartLabels)):
                vl2 = orderedPartLabels[j]
                if not vl2 in partLabelsCompared:
                    continue
                higherPitch0 = self[vl2]
                higherPitch1 = np[vl2]
                if lowerPitch1 > higherPitch0 or higherPitch1 < lowerPitch0:
                    if verbose:
                        self.environRules.warn("Part overlap between " + vl1 + " and " + vl2 + ".")
                    hasVoiceOverlap = True
                    if not verbose:
                        return hasVoiceOverlap
        
        return hasVoiceOverlap
    
    def partMovementsWithinLimits(self, nextPossibility, partList, verbose = False):
        '''
        Returns True if there are no illegal voice leaps present between prevPossibility (self) and nextPossibility.
        Takes in a list of Part instances which supply the maximum interval jump allowed for each part.
        The default max interval is a perfect octave. You can specify another max interval by inputting it as the
        third input of each part.  In the example below, the Soprano is limited to stepwise motion.
        
        Ignores parts which aren't shared between the two Possibility instances, but raises an error if
        there are parts shared between the two that don't correspond to Part instances in partList.
         
        >>> from music21.figuredBass import part
        >>> from music21.figuredBass import possibility
        >>> p1 = part.Part('B','E2','E4')
        >>> p2 = part.Part('T','C3','A4')
        >>> p3 = part.Part('A','F3','G5')
        >>> p4 = part.Part('S','C4','A5')
        >>> p4.maxSeparation = interval.Interval('M2')
        >>> partList = [p1, p2, p3, p4]        
        
        
        This example is True because all parts move by step.
        
        
        >>> p1 = possibility.Possibility({'S': 'C5', 'A': 'G4', 'T': 'E4', 'B': 'C3'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'A': 'F4', 'T': 'D4', 'B': 'D3'})
        >>> p1.partMovementsWithinLimits(p2, partList)
        True
        
        
        This example is False because the Soprano moves by 4th and is restricted 
        to stepwise motion.  The Alto also moves by 4th, but that's okay because
        the max interval (by default) is an Octave.
        
        
        >>> p3b = possibility.Possibility({'S':'G4', 'T': 'D4', 'Z': 'B3'})
        >>> p1.partMovementsWithinLimits(p3b, partList)
        False



        >>> p3a = possibility.Possibility({'W': 'G4', 'X': 'G4', 'Y': 'D4', 'Z': 'B3'})
        >>> p1.partMovementsWithinLimits(p3a, partList)
        Traceback (most recent call last):
        PossibilityException: No parts to check.
        '''
        leapsWithinLimits = True
        np = nextPossibility
        
        partLabelsCompared = []
        for vl in self.keys():
            if vl in np.keys():
                partLabelsCompared.append(vl)
                
        if len(partLabelsCompared) == 0:
            raise PossibilityException("No parts to check.")

        partLabels = extractPartLabels(partList)       
        partsNotCompared = []
        for vl in partLabelsCompared:
            if vl not in partLabels:
                partsNotCompared.append(vl)
        
        if not(len(partsNotCompared) == 0):
            raise PossibilityException("Parts with labels " + str(partsNotCompared) + " not found in partList.")              

        for givenPart in partList:
            if not givenPart.label in partLabelsCompared:
                continue
            v1n1 = self[givenPart.label]
            v1n2 = np[givenPart.label]
            i1 = interval.notesToInterval(v1n1, v1n2)
            if abs(i1.chromatic.semitones) > abs(givenPart.maxSeparation.chromatic.semitones):
                if verbose:
                    self.environRules.warn("Part leap in " + givenPart.label + " part.")
                leapsWithinLimits = False
                if not verbose:
                    return leapsWithinLimits

        return leapsWithinLimits
        
    # SINGLE POSSIBILITY HELPER METHODS
    # --------------
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
        c = chord.Chord(pitchesInChord)
        c.quarterLength = 1
        return c
    
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
 
    # CONSECUTIVE POSSIBILITY HELPER METHODS
    # --------------
    def partPairs(self, nextPossibility):
        '''
        Group pitches of prevPossibility (self) and nextPossibility which 
        correspond to the same part together.
        Raises an error if the Possibility instances don't share at least
        one part.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'B': 'C4'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'T': 'D4', 'B': 'D4'})
        >>> p1.partPairs(p2)
        [(C5, B4, 'S'), (C4, D4, 'B')]
        >>> p3 = possibility.Possibility({'X': 'B4', 'Y': 'D4'})
        >>> p1.partPairs(p3)
        Traceback (most recent call last):
        PossibilityException: No shared parts to group together.
        '''
        np = nextPossibility
        
        partPairs = []
        for partLabel in self.keys():
            if partLabel in np.keys():
                partPair = (self[partLabel], np[partLabel], partLabel)
                partPairs.append(partPair)
        
        if len(partPairs) == 0:
            raise PossibilityException("No shared parts to group together.")
        
        return partPairs
    
    def partQuartets(self, nextPossibility):
        '''
        Group all part pairs of prevPossibility (self) and nextPossibility together.
        Raises an error if the Possibility instances don't have at least two parts in common.
        
        >>> from music21.figuredBass import possibility
        >>> p1 = possibility.Possibility({'S': 'C5', 'T': 'E4', 'B': 'C4'})
        >>> p2 = possibility.Possibility({'S': 'B4', 'T': 'D4', 'B': 'D4'})
        >>> p1.partQuartets(p2)
        [(C5, B4, 'S', C4, D4, 'B'), (C5, B4, 'S', E4, D4, 'T'), (C4, D4, 'B', E4, D4, 'T')]
        >>> p3 = possibility.Possibility({'X': 'B4', 'Y': 'D4', 'B': 'D4'})
        >>> p1.partQuartets(p3)
        Traceback (most recent call last):
        PossibilityException: Need at least two shared parts to find part quartets.
        '''            
        partPairs = self.partPairs(nextPossibility)        
        if len(partPairs) == 1:
            raise PossibilityException("Need at least two shared parts to find part quartets.")
        
        partQuartets = []
        
        for i in range(len(partPairs)):
            for j in range(i+1,len(partPairs)):
                partQuartets.append(partPairs[i] + partPairs[j])
        
        return partQuartets
    

# EXTERNAL HELPER METHODS
# -----------------------
def extractPartLabels(partList):
    '''
    Extract part labels in order from a part list, and then return them.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> p1 = part.Part('B','E2','E4')
    >>> p2 = part.Part('T','C3','A4')
    >>> p3 = part.Part('A','F3','G5')
    >>> p4 = part.Part('S','C4','A5')
    >>> partList = [p1, p2, p3, p4]        
    >>> possibility.extractPartLabels(partList)
    ['B', 'T', 'A', 'S']
    '''
    partLabels = []
    for v in partList:
        partLabels.append(v.label)
    
    return partLabels
    

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