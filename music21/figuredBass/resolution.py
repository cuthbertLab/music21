#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         resolution.py
# Purpose:      Defines standard resolutions for possibility instances
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import music21
import copy 
import unittest

from music21 import chord
from music21 import pitch
from music21 import interval

from music21.figuredBass import possibility

#-------------------------------------------------------------------------------
# AUGMENTED SIXTH RESOLUTIONS

def augmentedSixthToDominant(augSixthPossib, inPlace = False):
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import resolution
    
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    
    The following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
    >>> iv6 = possibility.Possibility({p1: 'G4', p2: 'D4', p3: 'D4', p4: 'B-2'})
    >>> itAug6 = possibility.Possibility({p1: 'G#4', p2: 'D4', p3: 'D4', p4: 'B-2'})
    >>> frAug6 = possibility.Possibility({p1: 'G#4', p2: 'E4', p3: 'D4', p4: 'B-2'})
    >>> grAug6 = possibility.Possibility({p1: 'G#4', p2: 'F4', p3: 'D4', p4: 'B-2'})
    >>> iv6.isAugmentedSixth()
    False
    >>> itAug6.isItalianAugmentedSixth()
    True
    >>> frAug6.isFrenchAugmentedSixth()
    True
    >>> grAug6.isGermanAugmentedSixth()
    True
    
    
    "Swiss" or "Alsatian" augmented 6ths (that is a German 6th with #2 instead of b3)
    are not currently supported:
    >>> swissAug6 = possibility.Possibility({p1: 'G#4', p2: 'E#4', p3: 'D4', p4: 'B-2'})
    >>> swissAug6.isAugmentedSixth()
    True
    >>> swissAug6.isGermanAugmentedSixth()
    False
    
    
    
    
    It+6 to V not yet defined, because there are multiple equally valid solutions, not sure what to do.
    >>> print(resolution.augmentedSixthToDominant(frAug6))
    {1: A4, 2: E4, 3: C#4, 4: A2}
    >>> print(resolution.augmentedSixthToDominant(grAug6))
    {1: A4, 2: E4, 3: C#4, 4: A2}
    >>> resolution.augmentedSixthToDominant(iv6)
    Traceback (most recent call last):
    ResolutionException: Possibility does not form a correctly spelled augmented sixth chord.
    '''
    if not augSixthPossib.isAugmentedSixth():
        raise ResolutionException("Possibility does not form a correctly spelled augmented sixth chord.")

    isItalian = augSixthPossib.isItalianAugmentedSixth()
    isFrench = augSixthPossib.isFrenchAugmentedSixth()
    isGerman = augSixthPossib.isGermanAugmentedSixth()
    
    if inPlace:
        asCopy = augSixthPossib
    else:
        asCopy = copy.deepcopy(augSixthPossib)

    augSixthChord = asCopy.chordify()
    augSixthChord.removeRedundantPitchNames()
    if augSixthChord.inversion() == 2: # Fr+6
        augSixthChord.root(augSixthChord.getChordStep(3))
        
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    tonic = augSixthChord.getChordStep(5)
    for givenPart in asCopy.parts():
        givenPitch = asCopy[givenPart]
        givenPitchName = givenPitch.name
        if givenPitchName == bass.name:
            givenPitch.transpose('-m2', True)
        elif givenPitchName == root.name:
            givenPitch.transpose('m2', True)
        elif givenPitchName == tonic.name and not isItalian:
            givenPitch.transpose('-m2', True)
        else:
            if isFrench:
                givenPitch.transpose('P1', True)
            elif isGerman:
                givenPitch.transpose('-m2', True)
            elif isItalian:
                pass
        
    if inPlace == True:
        return None
    
    return asCopy

def augmentedSixthToMajorTonic(augSixthPossib, inPlace = False):
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import resolution
    
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    
    The following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
    >>> iv6 = possibility.Possibility({p1: 'G4', p2: 'D4', p3: 'D4', p4: 'B-2'})
    >>> itAug6 = possibility.Possibility({p1: 'G#4', p2: 'D4', p3: 'D4', p4: 'B-2'})
    >>> frAug6 = possibility.Possibility({p1: 'G#4', p2: 'E4', p3: 'D4', p4: 'B-2'})
    >>> grAug6 = possibility.Possibility({p1: 'G#4', p2: 'F4', p3: 'D4', p4: 'B-2'})
    >>> iv6.isAugmentedSixth()
    False
    >>> itAug6.isItalianAugmentedSixth()
    True
    >>> frAug6.isFrenchAugmentedSixth()
    True
    >>> grAug6.isGermanAugmentedSixth()
    True
    
    
    It+6 to V not yet defined, because there are multiple equally valid solutions, not sure what to do.    
    >>> print(resolution.augmentedSixthToMajorTonic(frAug6))
    {1: A4, 2: F#4, 3: D4, 4: A2}
    >>> print(resolution.augmentedSixthToMajorTonic(grAug6))
    {1: A4, 2: F#4, 3: D4, 4: A2}
    >>> resolution.augmentedSixthToMajorTonic(iv6)
    Traceback (most recent call last):
    ResolutionException: Possibility does not form a correctly spelled augmented sixth chord.
    '''
    if not augSixthPossib.isAugmentedSixth():
        raise ResolutionException("Possibility does not form a correctly spelled augmented sixth chord.")

    isItalian = augSixthPossib.isItalianAugmentedSixth()
    isFrench = augSixthPossib.isFrenchAugmentedSixth()
    isGerman = augSixthPossib.isGermanAugmentedSixth()
    
    if inPlace:
        asCopy = augSixthPossib
    else:
        asCopy = copy.deepcopy(augSixthPossib)

    augSixthChord = asCopy.chordify()
    augSixthChord.removeRedundantPitchNames()
    if augSixthChord.inversion() == 2: # Fr+6
        augSixthChord.root(augSixthChord.getChordStep(3))
        
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    tonic = augSixthChord.getChordStep(5)
    for givenPart in asCopy.parts():
        givenPitch = asCopy[givenPart]
        givenPitchName = givenPitch.name
        if givenPitchName == bass.name:
            givenPitch.transpose('-m2', True)
        elif givenPitchName == root.name:
            givenPitch.transpose('m2', True)
        elif givenPitchName == tonic.name:
            givenPitch.transpose('P1', True)
        else:
            if isFrench:
                givenPitch.transpose('M2', True)
            elif isGerman:
                givenPitch.transpose('A1', True)
            elif isItalian:
                pass

    if inPlace == True:
        return None
    
    return asCopy

def augmentedSixthToMinorTonic(augSixthPossib, inPlace = False):
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import part
    >>> from music21.figuredBass import resolution
    
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    
    The following examples were retrieved from Marjorie Merryman's The Music Theory Handbook.
    >>> iv6 = possibility.Possibility({p1: 'G4', p2: 'D4', p3: 'D4', p4: 'B-2'})
    >>> itAug6 = possibility.Possibility({p1: 'G#4', p2: 'D4', p3: 'D4', p4: 'B-2'})
    >>> frAug6 = possibility.Possibility({p1: 'G#4', p2: 'E4', p3: 'D4', p4: 'B-2'})
    >>> grAug6 = possibility.Possibility({p1: 'G#4', p2: 'F4', p3: 'D4', p4: 'B-2'})
    >>> iv6.isAugmentedSixth()
    False
    >>> itAug6.isItalianAugmentedSixth()
    True
    >>> frAug6.isFrenchAugmentedSixth()
    True
    >>> grAug6.isGermanAugmentedSixth()
    True
    
    
    It+6 to V not yet defined, because there are multiple equally valid solutions, not sure what to do.   
    >>> print(resolution.augmentedSixthToMinorTonic(frAug6))
    {1: A4, 2: F4, 3: D4, 4: A2}
    >>> print(resolution.augmentedSixthToMinorTonic(grAug6))
    {1: A4, 2: F4, 3: D4, 4: A2}
    >>> resolution.augmentedSixthToMajorTonic(iv6)
    Traceback (most recent call last):
    ResolutionException: Possibility does not form a correctly spelled augmented sixth chord.
    '''
    if not augSixthPossib.isAugmentedSixth():
        raise ResolutionException("Possibility does not form a correctly spelled augmented sixth chord.")

    isItalian = augSixthPossib.isItalianAugmentedSixth()
    isFrench = augSixthPossib.isFrenchAugmentedSixth()
    isGerman = augSixthPossib.isGermanAugmentedSixth()
    
    if inPlace:
        asCopy = augSixthPossib
    else:
        asCopy = copy.deepcopy(augSixthPossib)

    augSixthChord = asCopy.chordify()
    augSixthChord.removeRedundantPitchNames()
    if augSixthChord.inversion() == 2: # Fr+6
        augSixthChord.root(augSixthChord.getChordStep(3))
        
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    tonic = augSixthChord.getChordStep(5)
    for givenPart in asCopy.parts():
        givenPitch = asCopy[givenPart]
        givenPitchName = givenPitch.name
        if givenPitchName == bass.name:
            givenPitch.transpose('-m2', True)
        elif givenPitchName == root.name:
            givenPitch.transpose('m2', True)
        elif givenPitchName == tonic.name:
            givenPitch.transpose('P1', True)
        else:
            if isFrench:
                givenPitch.transpose('m2', True)
            elif isGerman:
                givenPitch.transpose('P1', True)
            elif isItalian:
                pass
    
    if inPlace == True:
        return None
    
    return asCopy

#Used Ex.76 (page 46) from 'The Basis of Harmony' by Frederick J. Horwood
#-------------------------------------------------------------------------------
# DOMINANT SEVENTH RESOLUTIONS

# STANDARD RESOLUTIONS
def dominantSeventhToMajorTonic(dominantPossib, resolveV43toI6 = False, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord, and returns its proper
    resolution to the major tonic (I), either in root position (5,3) or in first inversion (6,3) as 
    another possibility.
    
    Root position (7) and first inversion (6,5) dominant chords resolve to a root position (5,3) tonic chord.
    Third inversion (4,2) dominant chords resolve to a first inversion (6,3) tonic chord. Second inversion
    (4,3) dominant chords can resolve to either a root position or first inversion tonic chord.
    
    If resolveV43toI6 = True, then the resulting possibility will be a first inversion tonic chord.
    If resolveV43toI6 = False, then the resulting possibility will be a root position tonic chord.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.
    
    >>> from music21 import *
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'G2', p3: 'B3', p2: 'F4', p1: 'D5'})
    >>> resolutionA = resolution.dominantSeventhToMajorTonic(possibA)
    >>> resolutionA
    <music21.figuredBass.possibility Possibility: {1: C5, 2: E4, 3: C4, 4: C3}>
    >>> dominantChord = possibA.chordify()
    >>> resolutionChord = resolutionA.chordify()
    >>> score = stream.Part()
    >>> score.append(dominantChord)
    >>> score.append(resolutionChord)
    >>> #_DOCS_SHOW score.show()
        
    
    >>> possibB = possibility.Possibility({p4: 'C3', p3: 'E3', p2: 'G3', p1: 'B-3'})
    >>> resolution.dominantSeventhToMajorTonic(possibB)
    <music21.figuredBass.possibility Possibility: {1: A3, 2: F3, 3: F3, 4: F3}>
    >>> possibC = possibility.Possibility({p4: 'G3', p3: 'C4', p2: 'B-4', p1: 'E5'})
    >>> resolution.dominantSeventhToMajorTonic(possibC)
    <music21.figuredBass.possibility Possibility: {1: F5, 2: A4, 3: C4, 4: F3}>
    >>> resolution.dominantSeventhToMajorTonic(possibC, True)
    <music21.figuredBass.possibility Possibility: {1: F5, 2: C5, 3: C4, 4: A3}>
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.deepcopy(dominantPossib)
    
    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    
    root = V7chord.root()
    bass = V7chord.bass()
    inversion = V7chord.inversion()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            if isBass:
                samplePitch.transpose('P4', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            if inversion == 2 and resolveV43toI6:
                samplePitch.transpose('M2', True)
            else:
                samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            if inversion == 2 and resolveV43toI6:
                samplePitch.transpose('M2', True)
            else:
                samplePitch.transpose('-m2', True)
        
    return dpCopy

def dominantSeventhToMinorTonic(dominantPossib, resolveV43toi6 = False, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord, and returns its proper
    resolution to the minor tonic (i), either in root position (5,3) or in first inversion (6,3) as 
    another possibility.
    
    Root position (7) and first inversion (6,5) dominant chords resolve to a root position tonic chord.
    Third inversion (4,2) dominant chords resolve to a first inversion tonic chord. Second inversion
    (4,3) dominant chords can resolve to either a root position or first inversion tonic chord.
    
    If resolveV43toi6 = True, then the resulting possibility will be a first inversion tonic chord.
    If resolveV43toi6 = False, then the resulting possibility will be a root position tonic chord.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'G2', p3: 'B3', p2: 'F4', p1: 'D5'})
    >>> resolution.dominantSeventhToMinorTonic(possibA)
    <music21.figuredBass.possibility Possibility: {1: C5, 2: E-4, 3: C4, 4: C3}>
    >>> possibB = possibility.Possibility({p4: 'C3', p3: 'E3', p2: 'G3', p1: 'B-3'})
    >>> resolution.dominantSeventhToMinorTonic(possibB)
    <music21.figuredBass.possibility Possibility: {1: A-3, 2: F3, 3: F3, 4: F3}>
    >>> possibC = possibility.Possibility({p4: 'G3', p3: 'C4', p2: 'B-4', p1: 'E5'})
    >>> resolution.dominantSeventhToMinorTonic(possibC)
    <music21.figuredBass.possibility Possibility: {1: F5, 2: A-4, 3: C4, 4: F3}>
    >>> resolution.dominantSeventhToMinorTonic(possibC, True)
    <music21.figuredBass.possibility Possibility: {1: F5, 2: C5, 3: C4, 4: A-3}>
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.deepcopy(dominantPossib)

    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    
    root = V7chord.root()
    bass = V7chord.bass()
    inversion = V7chord.inversion()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            if isBass:
                samplePitch.transpose('P4', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            if inversion == 2 and resolveV43toi6:
                samplePitch.transpose('m2', True)
            else:
                samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            if inversion == 2 and resolveV43toi6:
                samplePitch.transpose('M2', True)
            else:
                samplePitch.transpose('-M2', True)
        
    return dpCopy

# DECEPTIVE RESOLUTIONS
def dominantSeventhToMajorSubmediant(dominantPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord and returns its
    proper resolution to the major submediant (VI) in root position (5,3) as another possibility.
    
    A dominant possibility has to be in root position (7) in order to properly resolve to its submediant.
    Therefore, a ResolutionException is raised if the possibility is not in root position.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'G2', p3: 'B3', p2: 'F4', p1: 'D5'})
    >>> resolution.dominantSeventhToMajorSubmediant(possibA)
    <music21.figuredBass.possibility Possibility: {1: C5, 2: E-4, 3: C4, 4: A-2}>
    >>> possibB = possibility.Possibility({p4: 'C3', p3: 'E3', p2: 'G3', p1: 'B-3'})
    >>> resolution.dominantSeventhToMajorSubmediant(possibB)
    <music21.figuredBass.possibility Possibility: {1: A-3, 2: F3, 3: F3, 4: D-3}>
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.deepcopy(dominantPossib)
    
    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    if not V7chord.inversion() == 0:
        raise ResolutionException("A proper deceptive resolution can only happen on the root position dominant seventh chord.")
    
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('-M2', True)
        
    return dpCopy

def dominantSeventhToMinorSubmediant(dominantPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord and returns its
    proper resolution to the minor submediant (vi) in root position (5,3) as another possibility.
    
    A dominant possibility has to be in root position (7) in order to properly resolve to its submediant.
    Therefore, a ResolutionException is raised if the possibility is not in root position.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'G2', p3: 'B3', p2: 'F4', p1: 'D5'})
    >>> resolution.dominantSeventhToMinorSubmediant(possibA)
    <music21.figuredBass.possibility Possibility: {1: C5, 2: E4, 3: C4, 4: A2}>
    >>> possibB = possibility.Possibility({p4: 'C3', p3: 'E3', p2: 'G3', p1: 'B-3'})
    >>> resolution.dominantSeventhToMinorSubmediant(possibB)
    <music21.figuredBass.possibility Possibility: {1: A3, 2: F3, 3: F3, 4: D3}>
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.deepcopy(dominantPossib)

    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    if not V7chord.inversion() == 0:
        raise ResolutionException("A proper deceptive resolution can only happen on the root position dominant seventh chord.")
    
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('M2', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('-m2', True)
        
    return dpCopy

# STATIONARY RESOLUTIONS
def dominantSeventhToMajorSubdominant(dominantPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord and returns its
    proper resolution to the major subdominant (IV) in first inversion (6,3) as another possibility.

    A dominant possibility has to be in root position (7) in order to properly resolve to the subdominant.
    Therefore, a ResolutionException is raised if the possibility is not in root position.

    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'G2', p3: 'B3', p2: 'F4', p1: 'D5'})
    >>> resolution.dominantSeventhToMajorSubdominant(possibA)
    <music21.figuredBass.possibility Possibility: {1: C5, 2: F4, 3: C4, 4: A2}>
    >>> possibB = possibility.Possibility({p4: 'C3', p3: 'E3', p2: 'G3', p1: 'B-3'})
    >>> resolution.dominantSeventhToMajorSubdominant(possibB)
    <music21.figuredBass.possibility Possibility: {1: B-3, 2: F3, 3: F3, 4: D3}>
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.deepcopy(dominantPossib)
    
    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    if not V7chord.inversion() == 0:
        raise ResolutionException("A proper stationary resolution can only happen on the root position dominant seventh chord.")

    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('M2', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        
    return dpCopy

def dominantSeventhToMinorSubdominant(dominantPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord and returns its
    proper resolution to the minor subdominant (iv) in first inversion (6,3) as another possibility.

    A dominant possibility has to be in root position (7) in order to properly resolve to the subdominant.
    Therefore, a ResolutionException is raised if the possibility is not in root position.

    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'G2', p3: 'B3', p2: 'F4', p1: 'D5'})
    >>> resolution.dominantSeventhToMinorSubdominant(possibA)
    <music21.figuredBass.possibility Possibility: {1: C5, 2: F4, 3: C4, 4: A-2}>
    >>> possibB = possibility.Possibility({p4: 'C3', p3: 'E3', p2: 'G3', p1: 'B-3'})
    >>> resolution.dominantSeventhToMinorSubdominant(possibB)
    <music21.figuredBass.possibility Possibility: {1: B-3, 2: F3, 3: F3, 4: D-3}>
    '''
    if inPlace:
        dpCopy = dominantPossib
    else:
        dpCopy = copy.deepcopy(dominantPossib)

    V7chord = dpCopy.chordify()
    if not V7chord.isDominantSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled dominant seventh chord.")
    if not V7chord.inversion() == 0:
        raise ResolutionException("A proper stationary resolution can only happen on the root position dominant seventh chord.")

    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('M3')).name
    fifthName = root.transpose(interval.Interval('P5')).name
    seventhName = root.transpose(interval.Interval('m7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        
    return dpCopy

#-------------------------------------------------------------------------------
# FULLY DIMINISHED SEVENTH RESOLUTIONS

# STANDARD RESOLUTIONS = Doubled 3rd
# ALTERNATE RESOLUTIONS  = Doubled root
def diminishedSeventhToMajorTonic(diminishedPossib, doubledRoot = False, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a diminished seventh chord, and returns 
    its proper resolution to the major tonic (I) in root position or either inversion as another possibility. 
    
    If doubledRoot = False, then the resolution will have its third doubled.
    If doubledRoot = True, then the resolution will have its root doubled, which involves a diminished fifth
    resolving to a perfect fifth
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'C#3', p3: 'G3', p2: 'E4', p1: 'B-4'})
    >>> resolution.diminishedSeventhToMajorTonic(possibA)
    <music21.figuredBass.possibility Possibility: {1: A4, 2: F#4, 3: F#3, 4: D3}>
    >>> resolution.diminishedSeventhToMajorTonic(possibA, True) # Alternate resolution
    <music21.figuredBass.possibility Possibility: {1: A4, 2: D4, 3: F#3, 4: D3}>
    '''
    if inPlace:
        dpCopy = diminishedPossib
    else:
        dpCopy = copy.deepcopy(diminishedPossib)
    
    dim7chord = dpCopy.chordify()
    if not dim7chord.isDiminishedSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled fully diminished seventh chord.")
    
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('m3')).name
    fifthName = root.transpose(interval.Interval('d5')).name
    seventhName = root.transpose(interval.Interval('d7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == thirdName:
            if doubledRoot:
                samplePitch.transpose('-M2', True)
            else:
                samplePitch.transpose('M2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-m2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('-m2', True)
        
    return dpCopy

def diminishedSeventhToMinorTonic(diminishedPossib, doubledRoot = False, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a diminished seventh chord, and returns 
    its proper resolution to the minor tonic (i) in root position or either inversion as another possibility. 
    
    If doubledRoot = False, then the resolution will have its third doubled.
    If doubledRoot = True, then the resolution will have its root doubled, which involves a diminished fifth
    resolving to a perfect fifth
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'C#3', p3: 'G3', p2: 'E4', p1: 'B-4'})
    >>> resolution.diminishedSeventhToMinorTonic(possibA)
    <music21.figuredBass.possibility Possibility: {1: A4, 2: F4, 3: F3, 4: D3}>
    >>> resolution.diminishedSeventhToMinorTonic(possibA, True) # Alternate resolution
    <music21.figuredBass.possibility Possibility: {1: A4, 2: D4, 3: F3, 4: D3}>
    '''
    if inPlace:
        dpCopy = diminishedPossib
    else:
        dpCopy = copy.deepcopy(diminishedPossib)
    
    dim7chord = dpCopy.chordify()
    if not dim7chord.isDiminishedSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled fully diminished seventh chord.")
    
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('m3')).name
    fifthName = root.transpose(interval.Interval('d5')).name
    seventhName = root.transpose(interval.Interval('d7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == thirdName:
            if doubledRoot:
                samplePitch.transpose('-M2', True)
            else:
                samplePitch.transpose('m2', True)
        elif samplePitch.name == fifthName:
            samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('-m2', True)
        
    return dpCopy

# SUBDOMINANT RESOLUTIONS
def diminishedSeventhToMajorSubdominant(diminishedPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a diminished seventh chord, and returns
    its resolution to the major subdominant (IV) in root position or either inversion as another possibility.
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'C#3', p3: 'G3', p2: 'E4', p1: 'B-4'})
    >>> resolution.diminishedSeventhToMajorSubdominant(possibA)
    <music21.figuredBass.possibility Possibility: {1: B4, 2: D4, 3: G3, 4: D3}>
    '''
    if inPlace:
        dpCopy = diminishedPossib
    else:
        dpCopy = copy.deepcopy(diminishedPossib)
    
    dim7chord = dpCopy.chordify()
    if not dim7chord.isDiminishedSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled fully diminished seventh chord.")
    
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('m3')).name
    fifthName = root.transpose(interval.Interval('d5')).name
    seventhName = root.transpose(interval.Interval('d7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            samplePitch.transpose('A1', True)
        
    return dpCopy

def diminishedSeventhToMinorSubdominant(diminishedPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a diminished seventh chord, and returns
    its resolution to the minor subdominant (iv) in root position or either inversion as another possibility.
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)

    >>> possibA = possibility.Possibility({p4: 'C#3', p3: 'G3', p2: 'E4', p1: 'B-4'})
    >>> resolution.diminishedSeventhToMinorSubdominant(possibA)
    <music21.figuredBass.possibility Possibility: {1: B-4, 2: D4, 3: G3, 4: D3}>
    '''
    if inPlace:
        dpCopy = diminishedPossib
    else:
        dpCopy = copy.deepcopy(diminishedPossib)
    
    dim7chord = dpCopy.chordify()
    if not dim7chord.isDiminishedSeventh():
        raise ResolutionException("Possibility does not form a correctly spelled fully diminished seventh chord.")
    
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = root.transpose(interval.Interval('m3')).name
    fifthName = root.transpose(interval.Interval('d5')).name
    seventhName = root.transpose(interval.Interval('d7')).name
    
    for vl in dpCopy.keys():
        samplePitch = dpCopy[vl]
        isBass = (samplePitch == bass)
        if samplePitch.name == rootName:
            samplePitch.transpose('m2', True)
        elif samplePitch.name == thirdName:
            samplePitch.transpose('-M2', True)
        
    return dpCopy

#-------------------------------------------------------------------------------
class ResolutionException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

