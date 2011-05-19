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

from music21 import chord
from music21 import environment
from music21 import note
from music21 import scale

from music21.figuredBass import notation
from music21.figuredBass import part
from music21.figuredBass import possibility
from music21.figuredBass import realizerScale
from music21.figuredBass import resolution
from music21.figuredBass import rules

_MOD = 'segment.py'

class Segment:
    '''
    A Segment is intended to correspond to a 1:1 realization of a bassNote and 
    notationString of a FiguredBass. A Segment provides all possible solutions 
    for a bassNote, taking into account the restrictions indicated in a provided 
    Rules object. 
    '''
    def __init__(self, fbScale, partList, fbRules, bassNote, notationString = ''):
        '''
        A Segment instance is created by providing a FiguredBassScale fbScale, 
        a list of Part instances partList, an instance of Rules fbRules, a 
        bassNote, and a notationString. Next, getPitches and getPitchNames are 
        called on fbScale, to retrieve first a list of all allowable pitches, 
        pitchesAboveBass, and second a list of allowable pitch classes, pitchNamesInChord.
        '''
        self.bassNote = bassNote
        self.notationString = notationString
        self.fbScale = fbScale
        self.partList = partList
        self.fbRules = fbRules
        self.pitchesAboveBass = self.fbScale.getPitches(self.bassNote.pitch, self.notationString)
        self.pitchNamesInChord = self.fbScale.getPitchNames(self.bassNote.pitch, self.notationString)
        self.nextMovements = {}
        self.nextSegment = None
        self.environRules = environment.Environment(_MOD)
    
    def allSinglePossibilities(self):
        '''
        Creates an initial list of Possibility instances, possibilities, using pitchesAboveBass and partList.
        '''
        possibilities = []
        
        bassPossibility = possibility.Possibility()
        self.partList.sort()
        previousVoice = self.partList[0]
        bassPossibility[previousVoice] = self.bassNote.pitch
        possibilities.append(bassPossibility)
        
        for partNumber in range(1, len(self.partList)):
            oldLength = len(possibilities)
            currentVoice = self.partList[partNumber]
            for oldPossibIndex in range(oldLength):
                oldPossib = possibilities.pop(0)
                validPitches = self.pitchesAboveBass
                for validPitch in validPitches:
                    newPossib = copy.copy(oldPossib)
                    newPossib[currentVoice] = validPitch
                    possibilities.append(newPossib)
                
            previousVoice = currentVoice

        return possibilities
    
    def correctSinglePossibilities(self, verbose = False):
        '''
        Uses the results of allSinglePossibilities to trim down the list in accordance 
        with stand-alone Possibility restrictions as specified in fbRules.
         
        Default values of fbRules:
        (1) No incomplete possibilities
        (2) Top parts within maxSemitoneSeparation
        (3) Pitches in each part within range
        (4) No voice crossing
        '''
        allPossibilities = self.allSinglePossibilities()
        
        newPossibilities = []
        for possibA in allPossibilities:
            correctPossib = True
            # No incomplete possibilities
            if not self.fbRules.allowIncompletePossibilities:
                if possibA.isIncomplete(self.pitchNamesInChord, verbose):
                    correctPossib = False
                    if not verbose:
                        continue
            # Top parts within maxSemitoneSeparation
            if not possibA.upperPartsWithinLimit(self.fbRules.upperPartsMaxSemitoneSeparation, verbose):
                correctPossib = False
                if not verbose:
                    continue
            # Pitches in each part within range
            if self.fbRules.filterPitchesByRange:
                pitchesInRange = possibA.pitchesWithinRange(verbose)
                if not pitchesInRange:
                    correctPossib = False
                    if not verbose:
                        continue
            # No part crossing
            if not self.fbRules.allowVoiceCrossing:
                hasVoiceCrossing = possibA.voiceCrossing(verbose)
                if hasVoiceCrossing:
                    correctPossib = False
                    if not verbose:
                        continue
            if correctPossib:
                newPossibilities.append(possibA)
        
    
        return newPossibilities
    
    def trimAllMovements(self, eliminated = []):
        '''
        Each Segment which has a nextSegment also defines a list of movements, 
        nextMovements. Keys for nextMovements are indices in the Segment's list 
        of possibilities. For a given key, a value is a list of indices in the 
        nextSegment's list of possibilities, representing acceptable movements 
        between the two. There may be movements in a string of Segment instances 
        which directly or indirectly lead nowhere. This method is designed to be 
        called on the last Segment, and eliminates any dead ends within a string 
        of Segment instances, important for solution retrieval.   
        
        >>> from music21.figuredBass import segment
        >>> from music21.figuredBass import possibility
        >>> from music21.figuredBass import part
        >>> from music21.figuredBass import rules
        >>> from music21.figuredBass import realizerScale
        >>> from music21 import note
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)
        >>> partList = [p1, p2, p3, p4]
        >>> fbScale = realizerScale.FiguredBassScale("D")
        >>> fbRules = rules.Rules()
        >>> bassA = note.Note("D3")
        >>> startSeg = segment.StartSegment(fbScale, partList, fbRules, bassA, "5, 3")
        >>> bassB = note.Note("E3")
        >>> midSeg1  = segment.MiddleSegment(fbScale, partList, fbRules,  startSeg, bassB, "6, 3")
        >>> bassC  = note.Note("F#3")
        >>> midSeg2 = segment.MiddleSegment(fbScale, partList, fbRules,  startSeg, bassC, "6, 3")
        >>> midSeg2.trimAllMovements()
        >>> midSeg2.getNumSolutions()
        92
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
        A recursive method which returns the number of solutions for a string 
        of Segment instances by calculating the total number of paths through 
        a string of Segment movements. More efficient than compiling a list of 
        all solutions and then taking its length. Intended to be called on the 
        last Segment.        
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
    '''
    StartSegment is intended to correspond to a bassNote which is not preceded by another in a FiguredBass.
    
    >>> from music21.figuredBass import segment
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import rules
    >>> from music21.figuredBass import realizerScale
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbScale = realizerScale.FiguredBassScale("D")
    >>> fbRules = rules.Rules()
    >>> bassNote = note.Note("D3")
    >>> startSeg = segment.StartSegment(fbScale, partList, fbRules, bassNote, "5, 3")
    >>> len(startSeg.possibilities) # Number of correctly formed possibilities
    21
    >>> startSeg.possibilities[0]
    <music21.figuredBass.possibility Possibility: {1: A3, 2: F#3, 3: D3, 4: D3}>
    '''
    def __init__(self, fbScale, partList, fbRules, bassNote, notationString = ''):
        '''
        Takes in arguments required for creation of a general Segment instance, and then 
        initializes one. From there, correctSinglePossibilities is called on this Segment 
        instance, which provides an initial list of correctly formed possibilities.
        '''
        Segment.__init__(self, fbScale, partList, fbRules, bassNote, notationString)
        self.possibilities = self.correctSinglePossibilities()
    
class MiddleSegment(Segment):
    '''
    MiddleSegment is intended to correspond to a bassNote which is preceded by another in a FiguredBass.
    
    >>> from music21.figuredBass import segment
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import rules
    >>> from music21.figuredBass import realizerScale
    >>> from music21 import note
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> partList = [p1, p2, p3, p4]
    >>> fbScale = realizerScale.FiguredBassScale("D")
    >>> fbRules = rules.Rules()
    >>> bassA = note.Note("D3")
    >>> startSeg = segment.StartSegment(fbScale, partList, fbRules, bassA, "5, 3")
    >>> bassB = note.Note("E3")
    >>> midSeg  = segment.MiddleSegment(fbScale, partList, fbRules,  startSeg, bassB, "6, 3")
    >>> len(midSeg.possibilities) # Number of correctly formed self-contained possibilities
    17
    >>> midSeg.possibilities[0]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: G3, 3: E3, 4: E3}>
    >>> startSeg.nextMovements[3]
    [0, 1, 2, 4]
    >>> startSeg.possibilities[3]
    <music21.figuredBass.possibility Possibility: {1: D4, 2: A3, 3: F#3, 4: D3}>
    >>> midSeg.possibilities[0]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: G3, 3: E3, 4: E3}>
    >>> midSeg.possibilities[1]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: G3, 3: G3, 4: E3}>
    >>> midSeg.possibilities[2]
    <music21.figuredBass.possibility Possibility: {1: C#4, 2: C#4, 3: G3, 4: E3}>
    >>> midSeg.possibilities[4]
    <music21.figuredBass.possibility Possibility: {1: G4, 2: C#4, 3: G3, 4: E3}>
    '''
    def __init__(self, fbScale, partList, fbRules, prevSegment, bassNote, notationString = ''):
        '''
        Takes in arguments required for creation of a general Segment instance, but takes 
        in one more argument: a previous Segment, containing the previous bassNote. It then 
        creates a general Segment instance, and then calls correctConsecutivePossibilities.
        '''
        Segment.__init__(self, fbScale, partList, fbRules, bassNote, notationString)
        self.prevSegment = prevSegment
        self.correctConsecutivePossibilities()
    
    def correctConsecutivePossibilities(self):
        '''
        Resolves MiddleSegment by calling other methods:
        1) resolveSpecial
        2) resolveAllConsecutivePossibilities
        '''
        try:
            self.resolveSpecialSegment()
        except UnresolvedSegmentException:
            self.resolveAllConsecutivePossibilities()
        
    def resolveSpecialSegment(self, verbose = False):
        isDominantSeventh = chord.Chord(self.prevSegment.pitchesAboveBass).isDominantSeventh()
        isDiminishedSeventh = chord.Chord(self.prevSegment.pitchesAboveBass).isDiminishedSeventh()
        isAugmentedSixth = (self.prevSegment.possibilities[0]).isAugmentedSixth()

        if isDominantSeventh and self.fbRules.resolveDominantSeventhProperly:
            resolve = self.resolveDominantSeventhPossibility
        elif isDiminishedSeventh and self.fbRules.resolveDiminishedSeventhProperly:        
            resolve = self.resolveDiminishedSeventhPossibility
        elif isAugmentedSixth and self.fbRules.resolveAugmentedSixthProperly:
            resolve = self.resolveAugmentedSixthPossibility
        else:
            raise UnresolvedSegmentException()

        prevPossibilities = self.prevSegment.possibilities
        self.prevSegment.nextMovements = {}        
        resolutionPossibilities = []
        prevPossibIndex = 0
        for prevPossib in prevPossibilities:
            movements = []
            resolutionPossib = resolve(prevPossib, verbose)
            try:
                movements.append(resolutionPossibilities.index(resolutionPossib))
            except ValueError:
                resolutionPossibilities.append(resolutionPossib)
                movements.append(len(resolutionPossibilities) - 1)             
            self.prevSegment.nextMovements[prevPossibIndex] = movements
            prevPossibIndex += 1 
        self.prevSegment.nextSegment = self
        self.possibilities = resolutionPossibilities

    def resolveAllConsecutivePossibilities(self):
        '''
        Called when a MiddleSegment requires no special resolution of possibilities from the previous Segment, 
        which happens if both of the special resolution methods throw an UnresolvedSegmentException. The method 
        finds a list of correctly formed possibilities for MiddleSegment by calling correctSinglePossibilities. 
        It then uses this list, nextPossibilities, along with the list of possibilities of the previous Segment, 
        prevPossibilities. For each element in prevPossibilities, possibA, iterates over each element in 
        nextPossibilities, possibB. For each combination of possibA and possibB, isCorrectConsecutivePossibility 
        is called. Every instance where the latter method returns True is recorded in a Python dictionary of movements, 
        nextMovements. Keys in nextMovements correspond to indices of possibA. Each value corresponds to a list 
        containing indices of possibB, those for which isCorrectConsecutivePossibility returns True.
        '''
        prevPossibilities = self.prevSegment.possibilities
        self.prevSegment.nextMovements = {}
        nextPossibilities = self.correctSinglePossibilities()
        prevPossibIndex = 0
        for possibA in prevPossibilities:
            movements = []
            nextPossibIndex = 0
            for possibB in nextPossibilities:
                if self.isCorrectConsecutivePossibility(possibA, possibB):
                    movements.append(nextPossibIndex)
                nextPossibIndex += 1
            self.prevSegment.nextMovements[prevPossibIndex] = movements
            prevPossibIndex += 1
        self.prevSegment.nextSegment = self
        self.possibilities = nextPossibilities
        return
    
    def resolveAugmentedSixthPossibility(self, augSixthPossib, verbose = False):
        '''
        Takes in a single Possibility which spells out an augmented sixth chord and attempts to return a
        Possibility which is resolved properly.
        '''
        if not augSixthPossib.isAugmentedSixth():
            raise SegmentException("Possibility does not form a correctly spelled augmented sixth chord.")
        
        if verbose:
            augSixthType = None
            if augSixthPossib.isItalianAugmentedSixth():
                augSixthType = "It+6"
            elif augSixthPossib.isFrenchAugmentedSixth():
                augSixthType = "Fr+6"
            elif augSixthPossib.isGermanAugmentedSixth():
                augSixthType = "Gr+6"
        
        augSixthChord = augSixthPossib.chordify()
        tonic = augSixthChord.bass().transpose('M3')
        majorScale = scale.MajorScale(tonic)
        minorScale = scale.MinorScale(tonic)
        
        resolutionChord = chord.Chord(self.pitchesAboveBass)
            
        if resolutionChord.inversion() == 2:
            if resolutionChord.root().name == tonic.name:
                if resolutionChord.isMajorTriad():
                    if verbose:
                        self.environRules.warn("Augmented sixth resolution: " + augSixthType + " to I64 in " + majorScale.name)
                    resolutionPossib = resolution.augmentedSixthToMajorTonic(augSixthPossib)
                elif resolutionChord.isMinorTriad():
                    if verbose:
                        self.environRules.warn("Augmented sixth resolution: " + augSixthType + " to i64 in " + minorScale.name)
                    resolutionPossib = resolution.augmentedSixthToMinorTonic(augSixthPossib)
        elif resolutionChord.isMajorTriad() and majorScale.pitchFromDegree(5).name == resolutionChord.bass().name:
            if verbose:
                        self.environRules.warn("Augmented sixth resolution: " + augSixthType + " to V in " + majorScale.name)
            resolutionPossib = resolution.augmentedSixthToDominant(augSixthPossib)
        else:
            raise SegmentException("Augmented sixth resolution: No standard resolution available.")
        
        if not (resolutionPossib.chordify().bass() == self.bassNote.pitch):
            raise SegmentException("Augmented sixth resolution: Bass note resolved improperly in figured bass.")
       
        return resolutionPossib
        
    def resolveDominantSeventhPossibility(self, dominantPossib, verbose = False):
        '''
        Takes in a single Possibility which spells out a dominant seventh chord and attempts to return 
        a Possibility which is resolved properly. An applicable dominant seventh resolution method in 
        resolution.py is used. The method chosen depends on the bassNote and pitchesAboveBass of 
        MiddleSegment. A SegmentException is raised if an applicable method cannot be chosen, if the 
        pitch of bassNote does not match the resolution Possibility, or if the input does not spell 
        out a dominant seventh. 
        '''
        if not dominantPossib.isDominantSeventh():
            raise SegmentException("Possibility does not form a correctly spelled dominant seventh chord.")
        
        dominantChord = dominantPossib.chordify()
        domInversionName = str(dominantChord.inversionName())
        sc = scale.MajorScale()
        dominantScale = sc.derive(dominantChord.pitches)
        minorScale = dominantScale.getParallelMinor()       
        
        tonic = dominantScale.getTonic()
        subdominant = dominantScale.pitchFromDegree(4)
        majSubmediant = dominantScale.pitchFromDegree(6)
        minSubmediant = minorScale.pitchFromDegree(6)
        
        resolutionChord = chord.Chord(self.pitchesAboveBass)
        resInversionName = str(resolutionChord.inversionName())
        if resInversionName == '53':
            resInversionName = ''
        
        if resolutionChord.root().name == tonic.name:
            resolveV43toI6 = False
            if dominantChord.inversion() == 2 and resolutionChord.inversion() == 1:
                resolveV43toI6 = True
            if resolutionChord.isMajorTriad():
                if verbose:
                    self.environRules.warn("Dominant seventh resolution: V" + domInversionName + "->I" + resInversionName + " in " + dominantScale.name)
                resolutionPossib = resolution.dominantSeventhToMajorTonic(dominantPossib, resolveV43toI6)
            elif resolutionChord.isMinorTriad():
                if verbose:
                    self.environRules.warn("Dominant seventh resolution: V" + domInversionName + "->I" + resInversionName + " in " + minorScale.name)
                resolutionPossib = resolution.dominantSeventhToMinorTonic(dominantPossib, resolveV43toI6)
        elif resolutionChord.root().name == majSubmediant.name:
            if sampleChord.isMinorTriad():
                if verbose:
                    self.environRules.warn("Dominant seventh resolution: V" + domInversionName + "->vi" + resInversionName + " in " + dominantScale.name)
                resolutionPossib = resolution.dominantSeventhToMinorSubmediant(dominantPossib) #Major scale
        elif resolutionChord.root().name == minSubmediant.name:
            if resolutionChord.isMajorTriad():
                if verbose:
                    self.environRules.warn("Dominant seventh resolution: V" + domInversionName + "->VI" + resInversionName + " in " + minorScale.name)
                resolutionPossib = resolution.dominantSeventhToMajorSubmediant(dominantPossib) #Minor scale
        elif resolutionChord.root().name == subdominant.name:
            if resolutionChord.isMajorTriad():
                if verbose:
                    self.environRules.warn("Dominant seventh resolution: V" + domInversionName + "->IV" + resInversionName + " in " + dominantScale.name)
                resolutionPossib = resolution.dominantSeventhToMajorSubdominant(dominantPossib)
            elif resolutionChord.isMinorTriad():
                if verbose:
                    self.environRules.warn("Dominant seventh resolution: V" + domInversionName + "->iv" + resInversionName + " in " + minorScale.name)
                resolutionPossib = resolution.dominantSeventhToMinorSubdominant(dominantPossib)
        else:
            raise SegmentException("Dominant seventh resolution: No proper resolution available.")
    
        if not (resolutionPossib.chordify().bass() == self.bassNote.pitch):
            raise SegmentException("Dominant seventh resolution: Bass note resolved improperly in figured bass.")
            
        return resolutionPossib

    def resolveDiminishedSeventhPossibility(self, diminishedPossib, verbose = False):
        '''
        Takes in a single Possibility which spells out a fully-diminished seventh chord and attempts to return 
        a Possibility which is resolved properly. See resolveDominantSeventhPossibility for more details.
        '''
        if not diminishedPossib.isDiminishedSeventh():
            raise SegmentException("Possibility does not form a correctly spelled diminished seventh chord.")
          
        diminishedChord = diminishedPossib.chordify()
        dimInversionName = str(diminishedChord.inversionName())
        sc = scale.HarmonicMinorScale()
        diminishedScale = sc.deriveByDegree(7, diminishedChord.root())
        minorScale = diminishedScale.getParallelMinor()
        
        tonic = diminishedScale.getTonic()
        subdominant = diminishedScale.pitchFromDegree(4)

        resolutionChord = chord.Chord(self.pitchesAboveBass)
        resInversionName = str(resolutionChord.inversionName())
        if resInversionName == '53':
            resInversionName = ''
        
        if resolutionChord.root().name == tonic.name:
            doubledRoot = self.fbRules.doubledRootInDim7
            if diminishedChord.inversion() == 1:
                if resolutionChord.inversion() == 0:
                    doubledRoot = True
                elif resolutionChord.inversion() == 1:
                    doubledRoot = False
            if resolutionChord.isMajorTriad():
                if verbose:
                    self.environRules.warn("Diminished seventh resolution: viio" + dimInversionName + "->I" + resInversionName + " in " + diminishedScale.name)
                resolutionPossib = resolution.diminishedSeventhToMajorTonic(diminishedPossib, doubledRoot)
            elif resolutionChord.isMinorTriad():
                if verbose:
                    self.environRules.warn("Diminished seventh resolution: viio" + dimInversionName + "->I" + resInversionName + " in " + minorScale.name)
                resolutionPossib = resolution.diminishedSeventhToMinorTonic(diminishedPossib, doubledRoot)
        elif resolutionChord.root().name == subdominant.name:
             if resolutionChord.isMajorTriad():
                if verbose:
                     self.environRules.warn("Diminished seventh resolution: viio" + dimInversionName + "->IV" + resInversionName + " in " + diminishedScale.name)
                resolutionPossib = resolution.diminishedSeventhToMajorSubdominant(diminishedPossib)
             elif resolutionChord.isMinorTriad():
                if verbose:
                     self.environRules.warn("Diminished seventh resolution: viio" + dimInversionName + "->IV" + resInversionName + " in " + minorScale.name)
                resolutionPossib = resolution.diminishedSeventhToMinorSubdominant(diminishedPossib)
        else:
            raise SegmentException("Diminished seventh resolution: No proper resolution available.")

        if not (resolutionChord.bass() == self.bassNote.pitch):
            raise SegmentException("Diminished seventh resolution: Bass note resolved improperly in figured bass.")
            
        return resolutionPossib

    def isCorrectConsecutivePossibility(self, possibA, possibB, verbose = False):
        '''
        Performs checks on two consecutive Possibility instances, possibA and possibB. 
        
        There are at most six checks performed:
        (1) hiddenFifth
        (2) hiddenOctave
        (3) partMovementsWithinLimits
        (4) voiceOverlap
        (5) parallelFifths
        (6) parallelOctaves
        
        If fbRules is set to its default values, then all six checks are performed. 
        The number of checks can be altered by modifying the corresponding flag(s) 
        in fbRules. The method returns False as soon as possibA and possibB fail an 
        applicable check. If possibA and possibB pass all applicable checks, the 
        method returns True.
        '''
        isCorrectPossib = True
        
        # No hidden fifth between shared outer parts
        if not self.fbRules.allowHiddenFifths:
            hasHiddenFifth = possibA.hiddenFifth(possibB, verbose)
            if hasHiddenFifth:
                isCorrectPossib = False
                if not verbose:
                    return isCorrectPossib
                
        # No hidden octave between shared outer parts
        if not self.fbRules.allowHiddenOctaves:
            hasHiddenOctave = possibA.hiddenOctave(possibB, verbose)
            if hasHiddenOctave:
                isCorrectPossib = False
                if not verbose:
                    return isCorrectPossib
        
        jumpsWithinLimits = possibA.partMovementsWithinLimits(possibB, verbose)
        # Movements in each part within corresponding maxSeparation
        if not jumpsWithinLimits:
            isCorrectPossib = False
            if not verbose:
                return isCorrectPossib
        # No part overlaps
        if not self.fbRules.allowVoiceOverlap:
            hasVoiceOverlap = possibA.voiceOverlap(possibB, verbose)
            if hasVoiceOverlap:
                isCorrectPossib = False
                if not verbose:
                    return isCorrectPossib

        # No parallel fifths
        if not self.fbRules.allowParallelFifths:
            hasParallelFifth = possibA.parallelFifths(possibB, verbose)
            if hasParallelFifth:
                isCorrectPossib = False
                if not verbose:
                    return isCorrectPossib
        # No parallel octaves
        if not self.fbRules.allowParallelOctaves:
            hasParallelOctave = possibA.parallelOctaves(possibB, verbose)
            if hasParallelOctave:
                isCorrectPossib = False
                if not verbose:
                    return isCorrectPossib
        
        return isCorrectPossib


class UnresolvedSegmentException(music21.Music21Exception):
    pass

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