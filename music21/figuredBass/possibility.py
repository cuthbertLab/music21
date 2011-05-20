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

from music21.figuredBass import part
from music21.figuredBass import realizerScale
from music21.figuredBass import rules

_MOD = "possibility.py"

class Possibility(dict):
    '''
    Extends the concept (but not the class) of a chord in music21 by allowing the labeling of parts 
    through the subclassing of the python dictionary. 
    
    Not intended to be used on its own, but rather to be used as a framework to encapsulate a "possibility"
    for a figured bass note/notation. The keys of Possibility are music21.figuredBass.part Part instances, 
    and the values are music21.pitch Pitch instances. 
    '''
    # INITIALIZATION METHODS
    # ----------------------
    def __init__(self, *args):
        '''
        Creates a Possibility instance when you provide a python dictionary,
        where keys are music21.figuredBass.part Part instances and values are
        music21.pitch Pitch instances or pitch strings. Pitch strings are
        converted to Pitch instances upon instantiation of Possibility.
        
        A PossibilityException is raised if a key provided is not a Part
        instance, or if a value is not a Pitch instance and can't be 
        converted to such.
                         
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        The four parts have a default range of A0->C8. The highest Part is 1 and the lowest Part is 4.
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)
        
        Pitch strings are provided as values to part1 and part4. They are automatically converted to Pitch instances.
        >>> p1 = possibility.Possibility({part1: 'C5', part2: pitch.Pitch('G4'), part3: pitch.Pitch('E4'), part4: 'C3'})
        >>> p1
        <music21.figuredBass.possibility Possibility: {1: C5, 2: G4, 3: E4, 4: C3}>

        Here, a string is being provided as a key. Only instances of Part can be provided as keys.
        >>> p2a = possibility.Possibility({part1: 'C5', 'part2String': pitch.Pitch('G4'), part3: pitch.Pitch('E4'), part4: 'C3'})
        Traceback (most recent call last):        
        PossibilityException: Cannot create Possibility: -> part2String <- not an instance of music21 figuredBass.Part!
        
        Here, an invalid pitch string was assigned to part2.
        >>> p2b = possibility.Possibility({part1: 'C5', part2: 'Not a pitch or pitch string', part3: pitch.Pitch('E4'), part4: 'C3'})
        Traceback (most recent call last):        
        PossibilityException: Cannot create Possibility: -> Not a pitch or pitch string <- not a valid music21 Pitch or pitch string!
        '''
        try:
            for givenPart in args[0].keys():
                if not isinstance(givenPart, part.Part):
                    raise PossibilityException("Cannot create Possibility: -> " + str(givenPart) + " <- not an instance of music21 figuredBass.Part!")
                pitchValue = args[0][givenPart]
                try:
                    args[0][givenPart] = realizerScale.convertToPitch(pitchValue)
                except:
                    raise PossibilityException("Cannot create Possibility: -> " + str(pitchValue) + " <- not a valid music21 Pitch or pitch string!")                
            dict.__init__(self, *args)
        except IndexError:
            dict.__init__(self, *args)
        
        self.environRules = environment.Environment(_MOD)       
    
    def __setitem__(self, givenPart, pitchValue):
        '''
        Sets a music21.figuredBass.part Part instance to a music21.pitch Pitch
        instance or pitch string. Pitch strings are automatically converted to
        Pitch instances.
        
        A PossibilityException is raised if a key is not a Part instance, or if 
        a value is not a Pitch instance and can't be converted to such.
         
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility() # Here, we create an empty Possibility.
        >>> p1
        <music21.figuredBass.possibility Possibility: {}>
        
        For part1, part2 we provide pitch strings. They are automatically turned into Pitch instances.
        >>> p1[part1] = 'C5'
        >>> p1[part2] = 'G4'
        >>> p1[part3] = pitch.Pitch('E4')
        >>> p1[part4] = pitch.Pitch('C3')
        >>> p1
        <music21.figuredBass.possibility Possibility: {1: C5, 2: G4, 3: E4, 4: C3}>
        
        Here, 'Flute' is a string and not an instance of Part.
        >>> p1['Flute'] = pitch.Pitch('C3')
        Traceback (most recent call last):
        PossibilityException: Cannot add part: -> Flute <- not an instance of music21 figuredBass.Part!
        
        Here, we create a flute Part, but it is assigned an invalid value.
        >>> flute = part.Part('Flute', 'C4', 'D7')
        >>> p1[flute] = 'Not a pitch or pitch string'
        Traceback (most recent call last):
        PossibilityException: Cannot set part Flute: -> Not a pitch or pitch string <- not a valid pitch or pitch string!
        >>> p1[flute] = 'F5'
        >>> p1
        <music21.figuredBass.possibility Possibility: {1: C5, 2: G4, 3: E4, 4: C3, 'Flute': F5}>
        '''
        if not isinstance(givenPart, part.Part):
            raise PossibilityException("Cannot add part: -> " + str(givenPart) + " <- not an instance of music21 figuredBass.Part!")
        try:
            pitchValue = realizerScale.convertToPitch(pitchValue)
        except:
            raise PossibilityException("Cannot set part " + str(givenPart.label) + ": -> " + str(pitchValue) + " <- not a valid pitch or pitch string!")                

        dict.__setitem__(self, givenPart, pitchValue)
    
    def numParts(self):
        '''
        Returns the number of Part instances. This number corresponds
        to the number of keys in the dictionary, and is equivalent to
        calling len(self.keys()).
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.numParts()
        4
        '''
        return len(self.keys())
    
    def parts(self):
        '''
        Returns a complete list of Part instances. This list corresponds
        to the list of all keys in the dictionary, and is equivalent to
        calling self.keys().

        The sort() method is called on the list before being returned.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> allParts = p1.parts()
        >>> allParts.sort()
        >>> allParts[0]
        <music21.figuredBass.part Part 4: A0->C8>
        >>> allParts[3]
        <music21.figuredBass.part Part 1: A0->C8>
        '''
        allParts = self.keys()
        allParts.sort()
        return allParts
    
    def lowestPart(self):
        '''
        Returns the lowest Part, according to comparison methods found in the Part
        class. Determined by calling sort() on the complete list of Part instances.
        
        Note that this may not be the part containing the lowest pitch, because of
        voice crossing.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.lowestPart()
        <music21.figuredBass.part Part 4: A0->C8>

        Here, the lowest pitch corresponds to part3, but the lowest Part is still part4.
        >>> p2 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E3', part4: 'C4'})
        >>> p2.lowestPitch()
        E3
        >>> p2.lowestPart()
        <music21.figuredBass.part Part 4: A0->C8>
        '''
        return self.parts()[0]
    
    def highestPart(self):
        '''
        Returns the highest Part, according to comparison methods found in the Part
        class. Determined by calling sort() on the complete list of Part instances.
        
        Note that this may not be the part containing the highest pitch, because of
        voice crossing.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.highestPart()
        <music21.figuredBass.part Part 1: A0->C8>
        
        Here, the highest pitch corresponds to part2, but the highest part is still part1.
        >>> p2 = possibility.Possibility({part1: 'G4', part2: 'C5', part3: 'E4', part4: 'C3'})
        >>> p2.highestPitch()
        C5
        >>> p2.highestPart()
        <music21.figuredBass.part Part 1: A0->C8>        
        '''
        return self.parts()[-1]
        
    def pitches(self):
        '''
        Returns a complete list of pitches. This list corresponds to 
        the list of all values in the dictionary, and is equivalent 
        to calling self.values().
        
        The sort() method is called on the list before being returned.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)
        
        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.pitches()
        [C3, E4, G4, C5]  
        '''
        allPitches = self.values()
        allPitches.sort()
        return allPitches
    
    def lowestPitch(self):
        '''
        Returns the lowest pitch. Determined by calling sort() on the complete list of pitches.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.lowestPitch()
        C3
        '''
        return self.pitches()[0]
    
    def highestPitch(self):
        '''
        Returns the highest pitch. Determined by calling sort() on the complete list of pitches.

        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.highestPitch()
        C5
        '''
        return self.pitches()[-1]

    def __str__(self):
        '''
        Returns a string representation of a Possibility. To keep the string short, 
        uses part labels rather than string representations of Part.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> str(p1)
        '{1: C5, 2: G4, 3: E4, 4: C3}'
        '''
        outputDict = {}
        for part in self.parts():
            outputDict[part.label] = self[part]
        
        return str(outputDict)
    
    def __repr__(self):
        '''
        Wraps a string with a music21.figuredBass.possibility Possibility designation.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1
        <music21.figuredBass.possibility Possibility: {1: C5, 2: G4, 3: E4, 4: C3}>
        '''
        return "<music21.figuredBass.possibility Possibility: " + str(self) + ">"
    
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
                 
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> pitchNames = ['C', 'E', 'G']
        >>> p1.isIncomplete(pitchNames)
        False
        >>> p1[part3] = 'C4'
        >>> p1.isIncomplete(pitchNames)
        True
        
        >>> p2 = possibility.Possibility({part1: 'B-5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p2.isIncomplete(pitchNames)
        Traceback (most recent call last):
        PossibilityException: {1: B-5, 2: G4, 3: E4, 4: C3} contains pitch classes not found in pitchNamesToContain.
        >>> pitchNames.append('B-')
        >>> p2.isIncomplete(pitchNames)
        False
        '''
        isIncomplete = False
        pitchNamesContained = []
        for part in self.keys():
            if self[part].name not in pitchNamesContained:
                pitchNamesContained.append(self[part].name)
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
            raise PossibilityException(str(self) + " contains pitch classes not found in pitchNamesToContain.")

        return isIncomplete
    
    def upperPartsWithinLimit(self, maxSemitoneSeparation = 12, verbose = False):
        '''
        Returns True if the pitches in the upper parts of a Possibility are found within 
        maxSemitoneSeparation of each other, inclusive. The upper parts are considered to 
        be all the elements in the sorted Part instance list excluding the first element.
                
        The default value of maxSemitoneSeparation is 12 semitones, enharmonically equivalent 
        to a perfect octave. If this method returns True for this default value, then all the
        notes in the upper parts (1,2,3) can be played by most adult pianists using just the
        right hand.
        
        If maxSemitoneSeparation = None, the method just returns True.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> p1.upperPartsWithinLimit()
        True
        >>> p1[part3] = 'E3'
        >>> p1.upperPartsWithinLimit() # part3 and part2, part1 now more than 12 semitones apart
        False
        '''
        upperPartsWithinLimit = True
        if maxSemitoneSeparation == None:
            return upperPartsWithinLimit
        
        upperParts = self.parts()[1:]
        
        for lowerPartIndex in range(len(upperParts)):
            lowerPart = upperParts[lowerPartIndex]
            lowerPitch = self[lowerPart]
            for higherPartIndex in range(lowerPartIndex + 1, len(upperParts)):
                higherPart = upperParts[higherPartIndex]
                higherPitch = self[higherPart]
                i1 = interval.notesToInterval(lowerPitch, higherPitch)
                if i1.chromatic.semitones > maxSemitoneSeparation:
                    if verbose:
                        self.environRules.warn(str(lowerPart.label) + " and " + str(higherPart.label) + " in " + str(self) + " are greater than " + str(maxSemitoneSeparation) + " semitones apart.")
                    upperPartsWithinLimit = False
                    if not verbose:
                        return upperPartsWithinLimit
        
        return upperPartsWithinLimit

    def pitchesWithinRange(self, verbose = False):
        '''
        Returns True if every pitch falls within the bounds of its range as specified
        by its part.
                
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> soprano = part.Part('Soprano', 2, 'C4','A5')
        >>> tenor = part.Part('Tenor', 12, 'C3','A4')
        >>> bass = part.Part('Bass', 12, 'E2','E4')

        >>> p1 = possibility.Possibility({soprano: 'C5', tenor: 'G4', bass: 'C3'})
        >>> p1.pitchesWithinRange()
        True
        >>> p2 = possibility.Possibility({soprano: 'B3', tenor: 'E3', bass: 'C3'})
        >>> p2.pitchesWithinRange() #Soprano pitch too low
        False
        '''
        pitchesInRange = True
        
        for part in self.parts():
            if not part.range.pitchInRange(self[part]):
                if verbose:
                    self.environRules.warn(str(part.label) + " in " + str(self) + " not within range.")
                pitchesInRange = False
                if not verbose:
                    return pitchesInRange
        
        return pitchesInRange
            
    def voiceCrossing(self, verbose = False):
        '''
        Returns True if there is voice crossing present between any two parts.
        The parts in increasing order must correspond to increasingly higher 
        pitches in order for there to be no voice crossing.

        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> p1 = possibility.Possibility({part1: 'C5', part2: 'G5', part3: 'E4'})
        >>> p1.voiceCrossing() # part2 higher than part4
        True
        >>> p2 = possibility.Possibility({part1: 'C5', part3: 'E4', part4: 'C4'})
        >>> p2.voiceCrossing()
        False
        '''
        hasVoiceCrossing = False
        
        partList = self.parts()
        
        for partAIndex in range(len(partList)):
            partA = partList[partAIndex]
            lowerPitch = self[partA]
            for partBIndex in range(partAIndex + 1, len(partList)):
                partB = partList[partBIndex]
                higherPitch = self[partB]
                if higherPitch < lowerPitch:
                    if verbose:
                        self.environRules.warn("Voice crossing between " + str(partA.label) + " and " + str(partB.label) + " in " + str(self) + ".")
                    hasVoiceCrossing = True
                    if not verbose:
                        return hasVoiceCrossing
                                
        return hasVoiceCrossing

    # CONSECUTIVE POSSIBILITY RULE-CHECKING METHODS
    # ---------------------------------------------
    def parallelFifths(self, possibB, verbose = False):
        '''
        Returns True if there are parallel fifths between any two shared parts of 
        possibA (self) and possibB, which comes directly after possibA.
        
        A PossibilityException is raised if less than two parts are shared between 
        possibA and possibB.

        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part3: 'G3', part4: 'C3'})
        >>> possibB = possibility.Possibility({part3: 'A3', part4: 'D3'})
        >>> possibA.parallelFifths(possibB)
        True
        
        Here, there are no shared parts between possibA and possibB.
        >>> possibB = possibility.Possibility({part1: 'D5', part2: 'B4'})
        >>> possibA.parallelFifths(possibB)
        Traceback (most recent call last):
        PossibilityException: No parallel fifths between: {3: G3, 4: C3} and {1: D5, 2: B4}: No shared parts.
        
        Here, there is only one shared part between possibA and possibB.
        >>> possibB = possibility.Possibility({part1: 'D5', part3: 'A3'})
        >>> possibA.parallelFifths(possibB)
        Traceback (most recent call last):
        PossibilityException: No parallel fifths between: {3: G3, 4: C3} and {1: D5, 3: A3}: Only one shared part.
        ''' 
        hasParallelFifth = False
        possibA = self
        try:
            pairsList = possibA.partPairs(possibB)
        except PossibilityException:
            raise PossibilityException("No parallel fifths between: " + str(possibA) + " and " + str(possibB) + ": No shared parts.")

        if len(pairsList) == 1:
            raise PossibilityException("No parallel fifths between: " + str(possibA) + " and " + str(possibB) + ": Only one shared part.")

        for pairIndex1 in range(len(pairsList)):
            (lowerPart, lowerPitchA, lowerPitchB) = pairsList[pairIndex1]
            for pairIndex2 in range(pairIndex1 +  1, len(pairsList)):
                (higherPart, higherPitchA, higherPitchB) = pairsList[pairIndex2]
                vlq = voiceLeading.VoiceLeadingQuartet(lowerPitchA, lowerPitchB, higherPitchA, higherPitchB)
                if vlq.parallelFifth():
                    if verbose:
                        self.environRules.warn("Parallel fifths between " + str(lowerPart.label) + " and " + str(higherPart.label) + " in " + str(self) + " and " + str(possibB) + ".")
                    hasParallelFifth = True
                    if not verbose:
                        return hasParallelFifth
        
        return hasParallelFifth

    def parallelOctaves(self, possibB, verbose = False):
        '''
        Returns True if there are parallel octaves between any two shared parts of 
        possibA (self) and possibB, which comes directly after possibA.

        A PossibilityException is raised if less than two parts are shared between 
        possibA and possibB.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part3: 'C4', part4: 'C3'})
        >>> possibB = possibility.Possibility({part3: 'D4', part4: 'D3'})
        >>> possibA.parallelOctaves(possibB)
        True
        
        Here, there are no shared parts between possibA and possibB.
        >>> possibB = possibility.Possibility({part1: 'D5', part2: 'D4'})
        >>> possibA.parallelOctaves(possibB) # No shared parts between p1 and p3
        Traceback (most recent call last):
        PossibilityException: No parallel octaves between: {3: C4, 4: C3} and {1: D5, 2: D4}: No shared parts.
        
        Here, there is only one shared part between possibA and possibB.
        >>> possibB = possibility.Possibility({part1: 'D5', part4: 'D3'})
        >>> possibA.parallelOctaves(possibB)
        Traceback (most recent call last):  
        PossibilityException: No parallel octaves between: {3: C4, 4: C3} and {1: D5, 4: D3}: Only one shared part.
        '''        
        hasParallelOctave = False
        possibA = self
        
        try:
            pairsList = possibA.partPairs(possibB)
        except PossibilityException:
            raise PossibilityException("No parallel octaves between: " + str(self) + " and " + str(possibB) + ": No shared parts.")

        if len(pairsList) == 1:
            raise PossibilityException("No parallel octaves between: " + str(self) + " and " + str(possibB) + ": Only one shared part.")

        for pairIndex1 in range(len(pairsList)):
            (lowerPart, lowerPitchA, lowerPitchB) = pairsList[pairIndex1]
            for pairIndex2 in range(pairIndex1 +  1, len(pairsList)):
                (higherPart, higherPitchA, higherPitchB) = pairsList[pairIndex2]
                vlq = voiceLeading.VoiceLeadingQuartet(lowerPitchA, lowerPitchB, higherPitchA, higherPitchB)
                if vlq.parallelOctave():
                    if verbose:
                        self.environRules.warn("Parallel octaves between " + str(lowerPart.label) + " and " + str(higherPart.label) + " in " + str(self) + " and " + str(possibB) + ".")
                    hasParallelOctave = True
                    if not verbose:
                        return hasParallelOctave
        
        return hasParallelOctave
        
    def hiddenFifth(self, possibB, verbose = False):
        '''
        Returns True if there is a hidden fifth between shared outer parts of 
        possibA (self) and possibB.
        
        A PossibilityException is raised if both outer parts are not shared
        between possibA and possibB.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part1: 'E5', part4: 'C3'})
        >>> possibB = possibility.Possibility({part1: 'A5', part4: 'D3'})
        >>> possibA.hiddenFifth(possibB)
        True
        >>> possibB = possibility.Possibility({part1: 'A#5', part4: 'D3'})
        >>> possibA.hiddenFifth(possibB)
        False
        
        Here, only the top part is shared.
        >>> possibB = possibility.Possibility({part1: 'A#5', part3: 'D3'})
        >>> possibA.hiddenFifth(possibB)
        Traceback (most recent call last):
        PossibilityException: No hidden fifth between: {1: E5, 4: C3} and {1: A#5, 3: D3}: No shared outer parts.
        '''
        hasHiddenFifth = False
        possibA = self
        
        uppermostA = possibA.highestPart()
        uppermostB = possibB.highestPart() 
        lowermostA = possibA.lowestPart()
        lowermostB = possibB.lowestPart()
        
        if not (uppermostA == uppermostB and lowermostA == lowermostB):
            raise PossibilityException("No hidden fifth between: " + str(self) + " and " + str(possibB) + ": No shared outer parts.")
        
        highestPitchA = possibA[uppermostA]
        highestPitchB = possibB[uppermostB]
        lowestPitchA = possibA[lowermostA]
        lowestPitchB = possibB[lowermostB]
        
        vlq = voiceLeading.VoiceLeadingQuartet(lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
        if vlq.hiddenFifth():
            hasHiddenFifth = True
            if verbose:
                self.environRules.warn("Hidden fifth between the outer parts " + str(uppermostA.label) + " and " + str(uppermostB.label) + " in " + str(self) + " and " + str(possibB) + ".")
            return hasHiddenFifth
            
        return hasHiddenFifth
    
    def hiddenOctave(self, possibB, verbose = False):
        '''
        Returns True if there is a hidden octave between shared outer parts of 
        possibA (self) and possibB.
        
        A PossibilityException is raised if both outer parts are not shared
        between possibA and possibB.

        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part1: 'A5', part4: 'C3'})
        >>> possibB = possibility.Possibility({part1: 'D6', part4: 'D3'})
        >>> possibA.hiddenOctave(possibB)
        True
        '''
        hasHiddenOctave = False
        possibA = self
        
        uppermostA = possibA.highestPart()
        uppermostB = possibB.highestPart() 
        lowermostA = possibA.lowestPart()
        lowermostB = possibB.lowestPart()
        
        if not (uppermostA == uppermostB and lowermostA == lowermostB):
            raise PossibilityException("No hidden octave between: " + str(self) + " and " + str(possibB) + ": No shared outer parts.")
        
        highestPitchA = possibA[uppermostA]
        highestPitchB = possibB[uppermostB]
        lowestPitchA = possibA[lowermostA]
        lowestPitchB = possibB[lowermostB]
        
        vlq = voiceLeading.VoiceLeadingQuartet(lowestPitchA, lowestPitchB, highestPitchA, highestPitchB)
        if vlq.hiddenOctave():
            hasHiddenOctave = True
            if verbose:
                self.environRules.warn("Hidden octave between the outer parts " + str(uppermostA.label) + " and " + str(uppermostB.label) + " in " + str(self) + " and " + str(possibB) + ".")
            return hasHiddenOctave
            
        return hasHiddenOctave

    def voiceOverlap(self, possibB, verbose = False):
        '''
        Returns True if there is voice overlap between any two shared parts of 
        possibA (self) and possibB.
        
        A PossibilityException is raised if less than two parts are 
        shared between possibA and possibB.
    
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C4'})
        >>> possibB = possibility.Possibility({part1: 'B4', part2: 'F4', part4: 'D4'})
        >>> possibA.voiceOverlap(possibB)
        False
        
        >>> possibB = possibility.Possibility({part1: 'F4', part2: 'F4'})
        >>> possibA.voiceOverlap(possibB) # Voice overlap between part2/part1, but no voice crossing
        True
        >>> possibA.voiceCrossing()
        False
        >>> possibB.voiceCrossing()
        False
        
        Here, possibA and possibB have no parts in common.    
        >>> possibA = possibB 
        >>> possibB = possibility.Possibility({part3: 'D4', part4: 'B4'})
        >>> possibA.voiceOverlap(possibB)
        Traceback (most recent call last):
        PossibilityException: No voice overlap between: {1: F4, 2: F4} and {3: D4, 4: B4}: No shared parts.
        
        Here, possibA and possibB have only one part in common.
        >>> possibB = possibility.Possibility({part1: 'G4', part4: 'B4'})
        >>> possibA.voiceOverlap(possibB)
        Traceback (most recent call last):
        PossibilityException: No voice overlap between: {1: F4, 2: F4} and {1: G4, 4: B4}: Only one shared part.
        '''
        hasVoiceOverlap = False
        possibA = self
        
        try:
            pairsList = possibA.partPairs(possibB)
        except PossibilityException:
            raise PossibilityException("No voice overlap between: " + str(possibA) + " and " + str(possibB) + ": No shared parts.")

        if len(pairsList) == 1:
            raise PossibilityException("No voice overlap between: " + str(possibA) + " and " + str(possibB) + ": Only one shared part.")

        for pairIndex1 in range(len(pairsList)):
            (lowerPart, lowerPitchA, lowerPitchB) = pairsList[pairIndex1]
            for pairIndex2 in range(pairIndex1 +  1, len(pairsList)):
                (higherPart, higherPitchA, higherPitchB) = pairsList[pairIndex2]
                if lowerPitchB > higherPitchA or higherPitchB < lowerPitchA:
                    if verbose:
                        self.environRules.warn("Voice overlap between " + str(lowerPart.label) + " and " + str(higherPart.label) + " in " + str(self) + " and " + str(possibB) + ".")
                    hasVoiceOverlap = True
                    if not verbose:
                        return hasVoiceOverlap
            
        return hasVoiceOverlap
    
    def partMovementsWithinLimits(self, possibB, verbose = False):
        '''
        Returns True if movements in each shared part between possibA and possibB
        are within each part's maxSeparation, in semitones. A maxSeparation can
        be provided to each part as the second parameter.
        
        The default maxSeparation in part.Part is 12 semitones, enharmonically 
        equivalent to a perfect octave.
                    
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1, 2)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)
        
        This example is True because all parts move by step.
        >>> possibA = possibility.Possibility({part1: 'C5', part2: 'G4', part3: 'E4', part4: 'C3'})
        >>> possibB = possibility.Possibility({part1: 'B4', part2: 'F4', part3: 'D4', part4: 'D3'})
        >>> possibA.partMovementsWithinLimits(possibB)
        True
        
        This example is False because part4 moves by 4th and is restricted to stepwise motion.
        >>> possibB = possibility.Possibility({part1:'G4', part3: 'D4', part4: 'D3'})
        >>> possibA.partMovementsWithinLimits(possibB)
        False
        '''
        leapsWithinLimits = True
        possibA = self

        for givenPart in possibA.parts():
            if givenPart not in possibB.parts():
                continue
            if givenPart.maxSeparation == None:
                continue
            v1n1 = possibA[givenPart]
            v1n2 = possibB[givenPart]
            i1 = interval.notesToInterval(v1n1, v1n2)
            if abs(i1.chromatic.semitones) > abs(givenPart.maxSeparation):
                if verbose:
                    self.environRules.warn("Part leap in " + str(givenPart.label) + " part.")
                leapsWithinLimits = False
                if not verbose:
                    return leapsWithinLimits

        return leapsWithinLimits
        
    # SINGLE POSSIBILITY HELPER METHODS
    # --------------
    def chordify(self, quarterLength = 1.0):
        '''
        Turns possibA (self) into a music21.chord Chord instance.
        
        The default quarterLength of the resulting Chord is 1.0,
        but another can be provided.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part1: 'C5', part3: 'E4', part4: 'C4'})
        >>> possibA.chordify()
        <music21.chord.Chord C4 E4 C5>
        
        Here, the chord lasts for two quarter lengths.
        >>> possibA = possibility.Possibility({part1: 'B4', part3: 'D4', part4: 'D4'})
        >>> chord2 = possibA.chordify(2.0)
        >>> chord2
        <music21.chord.Chord D4 D4 B4> 
        >>> chord2.quarterLength
        2.0
        '''
        c = chord.Chord(self.pitches())
        c.quarterLength = quarterLength
        return c
    
    def isDominantSeventh(self):
        '''
        Returns True if possibA (self) is a Dominant Seventh. Possibility must be correctly spelled.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part4: 'G2', part3: 'B3', part2: 'F4', part1: 'D5'})
        >>> possibA.isDominantSeventh()
        True
        
        Here, the Dominant Seventh is missing its fifth.
        >>> possibA = possibility.Possibility({part4: 'G2', part3: 'B3', part2: 'F4', part1: 'B5'})
        >>> possibA.isDominantSeventh()
        False
        '''
        possibAsChord = self.chordify()
        if possibAsChord.isDominantSeventh():
            return True
        else:
            return False
        
    def isDiminishedSeventh(self):
        '''
        Returns True if possibA (self) is a (fully) Diminished Seventh. Possibility must be correctly spelled.
    
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part4: 'C#3', part3: 'G3', part2: 'E4', part1: 'B-4'})
        >>> possibA.isDiminishedSeventh()
        True
        
        Here, the Diminished Seventh is missing its fifth. 
        >>> possibA = possibility.Possibility({part4: 'C#3', part3: 'E3', part2: 'E4', part1: 'B-4'})
        >>> possibA.isDiminishedSeventh()
        False
        '''
        possibAsChord = self.chordify()
        if possibAsChord.isDiminishedSeventh():
            return True
        else:
            return False

    def isAugmentedSixth(self):
        '''
        Returns True if the Possibility is an Italian, French, or German +6 chord.
        In other words, returns True if the following methods also return True:
        1) isItalianAugmentedSixth(augSixthPossib)
        2) isFrenchAugmentedSixth(augSixthPossib)
        3) isGermanAugmentedSixth(augSixthPossib)
        4) isSwissAugmentedSixth(augSixthPossib)
        
        
        Note that chords MUST be in first inversion to be true.
        
        
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)
        
        Some of the following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
        >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
        >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
        >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
        >>> itAug6.isAugmentedSixth()
        True
        >>> frAug6.isAugmentedSixth()
        True
        >>> grAug6.isAugmentedSixth()
        True
        >>> V7 = possibility.Possibility({p1: 'D5', p2: 'F4', p3: 'B3', p4: 'G2'})
        >>> V7.isAugmentedSixth()
        False
        >>> p1 = possibility.Possibility({p1: 'C3', p4: 'C5'})
        >>> p1.isAugmentedSixth()
        False
        '''
        c = self.chordify()
        return c.isAugmentedSixth()
    
    def isItalianAugmentedSixth(self):
        '''
        returns True if the possibility is a properly 
        spelled Italian augmented sixth with only the tonic doubled.


        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)
        
        Some of the following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
        >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
        >>> itAug6.isItalianAugmentedSixth()
        True
        >>> itAug6a = possibility.Possibility({p1: 'C5', p2: 'F4', p3: 'C4', p4: 'A-2'})
        >>> itAug6a.isItalianAugmentedSixth()
        False
        >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
        >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
        >>> frAug6.isItalianAugmentedSixth()
        False
        >>> grAug6.isItalianAugmentedSixth()
        False
    
        OMIT_FROM_DOCS
        >>> p5 = part.Part(5)

        ## two parts are doubled
        >>> itAug6b = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2', p5: 'F#5'})
        >>> itAug6b.isItalianAugmentedSixth()
        False
        >>> itAug6c = possibility.Possibility({p2: 'F#4', p3: 'C4', p4: 'A-2', p5: 'F#5'})
        >>> itAug6c.isItalianAugmentedSixth()
        False
        >>> itAug6d = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2', p5: 'C6'})    
        >>> itAug6d.isItalianAugmentedSixth()
        True
        '''
        return self.chordify().isItalianAugmentedSixth(restrictDoublings = True)
                
    
    def isFrenchAugmentedSixth(self):
        '''
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)
        
        The following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
        >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
        >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
        >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
        >>> frAug6.isFrenchAugmentedSixth()
        True
        >>> frAug6.isItalianAugmentedSixth()
        False
        >>> frAug6.isGermanAugmentedSixth()
        False
        '''
        return self.chordify().isFrenchAugmentedSixth()

    
    def isGermanAugmentedSixth(self):
        '''
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)
        
        The following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
        >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
        >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
        >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
        >>> grAug6.isGermanAugmentedSixth()
        True
        >>> grAug6.isItalianAugmentedSixth()
        False
        >>> grAug6.isFrenchAugmentedSixth()
        False
        '''
        return self.chordify().isGermanAugmentedSixth()

    def isSwissAugmentedSixth(self):
        '''        
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)

        
        The following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.


        >>> swissAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D#4', p4: 'A-2'})
        >>> swissAug6.isGermanAugmentedSixth()
        False
        >>> swissAug6.isSwissAugmentedSixth()
        True
        >>> swissAug6.isFrenchAugmentedSixth()
        False
        >>> swissAug6.isAugmentedSixth()
        True
        '''
        return self.chordify().isSwissAugmentedSixth()

        



    # CONSECUTIVE POSSIBILITY HELPER METHODS
    # --------------
    def partPairs(self, possibB):
        '''
        Group pitches of possibA (self) and possibB which 
        correspond to the same part together.
        
        Returns a list of tuples with each part's shared pitches
        from possibA (self) and possibB (next). Each tuple also
        includes the part.
        
        A PossibilityException is raised if the Possibility instances
        don't share at least one part.
        
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

        >>> possibA = possibility.Possibility({part1: 'C5', part4: 'C4'})
        >>> possibB = possibility.Possibility({part1: 'B4', part3: 'D4', part4: 'D4'})
        >>> pairsList = possibA.partPairs(possibB)
        >>> len(pairsList)
        2
        >>> pairsList[0]
        (<music21.figuredBass.part Part 4: A0->C8>, C4, D4)
        >>> pairsList[1]
        (<music21.figuredBass.part Part 1: A0->C8>, C5, B4)
        
        Here, there are no shared parts between possibA and possibB
        >>> possibB = possibility.Possibility({part3: 'B4', part2: 'D4'})
        >>> possibA.partPairs(possibB)
        Traceback (most recent call last):
        PossibilityException: No shared parts to group together.
        
        >>> possibA = possibility.Possibility({part3: 'G3', part4: 'C3'})
        >>> possibB = possibility.Possibility({part1: 'D5', part3: 'A3'})
        >>> possibA.partPairs(possibB)
        [(<music21.figuredBass.part Part 3: A0->C8>, G3, A3)]
        '''
        possibA = self
        
        partPairs = []
        for part in possibA.parts():
            if part in possibB.parts():
                partPair = (part, possibA[part], possibB[part])
                partPairs.append(partPair)
        
        if len(partPairs) == 0:
            raise PossibilityException("No shared parts to group together.")
        
        return partPairs
    

# EXTERNAL HELPER METHODS
# -----------------------
def extractPartLabels(partList):
    '''
    Extract part labels in order from a list of Part instances, and then return them.
    
        >>> from music21 import pitch
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        
        >>> part1 = part.Part(1)
        >>> part2 = part.Part(2)
        >>> part3 = part.Part(3)
        >>> part4 = part.Part(4)

    >>> partList = [part4, part3, part2, part1]        
    >>> possibility.extractPartLabels(partList)
    [4, 3, 2, 1]
    '''
    partLabels = []
    for part in partList:
        partLabels.append(part.label)
    
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