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

def isAugmentedSixth(augSixthPossib):
    '''
    Returns True if the Possibility is an Italian, French, or German +6 chord.
    In other words, returns True if the following methods also return True:
    1) isItalianAugmentedSixth(augSixthPossib)
    2) isFrenchAugmentedSixth(augSixthPossib)
    3) isGermanAugmentedSixth(augSixthPossib)
    
    >>> from music21 import interval
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
    >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
    >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
    >>> resolution.isAugmentedSixth(itAug6)
    True
    >>> resolution.isAugmentedSixth(frAug6)
    True
    >>> resolution.isAugmentedSixth(grAug6)
    True
    >>> V7 = possibility.Possibility({p1: 'D5', p2: 'F4', p3: 'B3', p4: 'G2'})
    >>> resolution.isAugmentedSixth(V7)
    False
    '''

    if isItalianAugmentedSixth(augSixthPossib):
        return True
    elif isFrenchAugmentedSixth(augSixthPossib):
        return True
    elif isGermanAugmentedSixth(augSixthPossib):
        return True
    
    return False

def isItalianAugmentedSixth(augSixthPossib):
    '''
    >>> from music21 import interval
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
    >>> resolution.isItalianAugmentedSixth(itAug6)
    True
    >>> itAug6a = possibility.Possibility({p1: 'C5', p2: 'F4', p3: 'C4', p4: 'A-2'})
    >>> resolution.isItalianAugmentedSixth(itAug6a)
    False
    >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
    >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
    >>> resolution.isItalianAugmentedSixth(frAug6)
    False
    >>> resolution.isItalianAugmentedSixth(grAug6)
    False

    OMIT_FROM_DOCS
    >>> p5 = part.Part(5)
    >>> itAug6b = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2', p5: 'F#5'})
    >>> resolution.isItalianAugmentedSixth(itAug6b)
    True
    >>> itAug6c = possibility.Possibility({p2: 'F#4', p3: 'C4', p4: 'A-2', p5: 'F#5'})
    >>> resolution.isItalianAugmentedSixth(itAug6c)
    False
    >>> itAug6d = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2', p5: 'A2'})    
    >>> resolution.isItalianAugmentedSixth(itAug6d)
    False
    '''
    ### It+6 => Minor sixth scale step in bass, tonic, raised 4th + doubling of tonic note.
    augSixthChord = augSixthPossib.chordify()
    augSixthChord.removeRedundantPitchNames()
    
    ### Chord must be in first inversion.
    if not augSixthChord.inversion() == 1:
        return False
    
    ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    augSixthInterval = interval.Interval(bass, root)
    if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
        return False
        
    ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if 
    ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
    tonic = augSixthChord.getChordStep(5)
    majThirdInterval = interval.Interval(bass, tonic)
    if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
        return False
    
    ### No other pitches may be present that aren't the m6 scale step, raised 4th, or tonic.
    for samplePitch in augSixthChord.pitches:
        if not (samplePitch == bass or samplePitch == root or samplePitch == tonic):
            return False
    
    ### Tonic must be doubled.
    for samplePitch in augSixthPossib.pitches():
        if (not samplePitch == tonic) and (samplePitch.name == tonic.name):
            return True
        
    return False

def isFrenchAugmentedSixth(augSixthPossib):
    '''
    >>> from music21 import interval
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
    >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
    >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
    >>> resolution.isFrenchAugmentedSixth(frAug6)
    True
    >>> resolution.isItalianAugmentedSixth(frAug6)
    False
    >>> resolution.isGermanAugmentedSixth(frAug6)
    False
    '''
    ### Fr+6 => Minor sixth scale step in bass, tonic, raised 4th + second scale degree.
    augSixthChord = augSixthPossib.chordify()
    augSixthChord.removeRedundantPitchNames()
    
    ### The findRoot() method of music21.chord Chord determines the root based on the note with
    ### the most thirds above it. However, under this definition, a french augmented sixth chord
    ### resembles a second inversion chord, not the first inversion subdominant chord it is based
    ### upon. We fix this by adjusting the root. First, however, we check to see if the chord is
    ### in second inversion to begin with, otherwise its not a Fr+6 chord. This is to avoid 
    ### ChordException errors.
    if not augSixthChord.inversion() == 2:
        return False    
    augSixthChord.root(augSixthChord.getChordStep(3))

    ### Chord must be in first inversion.    
    if not augSixthChord.inversion() == 1:
        return False
        
    ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    augSixthInterval = interval.Interval(bass, root)
    if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
        return False
        
    ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if 
    ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
    tonic = augSixthChord.getChordStep(5)
    majThirdInterval = interval.Interval(bass, tonic)
    if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
        return False

    ### The sixth of the chord must be the supertonic. The sixth of the chord is the supertonic if and only if
    ### there is a A4 (simple or compound) between the bass (m6 scale step) and the sixth of the chord.
    supertonic = augSixthChord.getChordStep(6)
    augFourthInterval = interval.Interval(bass, supertonic)
    if not (augFourthInterval.diatonic.specificName == 'Augmented' and augFourthInterval.generic.simpleDirected == 4):
        return False
    
    ### No other pitches may be present that aren't the m6 scale step, raised 4th, tonic, or supertonic.
    for samplePitch in augSixthChord.pitches:
        if not (samplePitch == bass or samplePitch == root or samplePitch == tonic or samplePitch == supertonic):
            return False

    return True

def isGermanAugmentedSixth(augSixthPossib):
    '''
    >>> from music21 import interval
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> from music21.figuredBass import part
    >>> p1 = part.Part(1)
    >>> p2 = part.Part(2)
    >>> p3 = part.Part(3)
    >>> p4 = part.Part(4)
    >>> itAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'C4', p4: 'A-2'})
    >>> frAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'D4', p4: 'A-2'})
    >>> grAug6 = possibility.Possibility({p1: 'C5', p2: 'F#4', p3: 'E-4', p4: 'A-2'})
    >>> resolution.isGermanAugmentedSixth(grAug6)
    True
    >>> resolution.isItalianAugmentedSixth(grAug6)
    False
    >>> resolution.isFrenchAugmentedSixth(grAug6)
    False
    '''
    augSixthChord = augSixthPossib.chordify()
    augSixthChord.removeRedundantPitchNames()

    ### Chord must be in first inversion.
    if not augSixthChord.inversion() == 1:
        return False
        
    ### Augmented sixth interval (simple or compound) must be present between bass and raised 4th (root of chord)
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    augSixthInterval = interval.Interval(bass, root)
    if not (augSixthInterval.diatonic.specificName == 'Augmented' and augSixthInterval.generic.simpleDirected == 6):
        return False
        
    ### The fifth of the chord must be the tonic. The fifth of the chord is the tonic if and only if 
    ### there is a M3 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
    tonic = augSixthChord.getChordStep(5)
    majThirdInterval = interval.Interval(bass, tonic)
    if not (majThirdInterval.diatonic.specificName == 'Major' and majThirdInterval.generic.simpleDirected == 3):
        return False

    ### The seventh of the chord must be the mediant. The seventh of the chord is the mediant if and only if
    ### there is a P5 (simple or compound) between the bass (m6 scale step) and the fifth of the chord.
    mediant = augSixthChord.getChordStep(7)
    perfectFifthInterval = interval.Interval(bass, mediant)
    if not (perfectFifthInterval.diatonic.specificName == 'Perfect' and perfectFifthInterval.generic.simpleDirected == 5):
        return False

    return True
    
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

