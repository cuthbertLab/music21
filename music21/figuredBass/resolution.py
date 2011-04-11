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
    
    If resolveV43toI6 = True, then the resolution will be to a first inversion tonic chord.
    If resolveV43toI6 = False, then the resolution will be to a root position tonic chord.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution.dominantSeventhToMajorTonic(possibA)
    {'A': E4, 'S': C5, 'B': C3, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution.dominantSeventhToMajorTonic(possibB)
    {'A': F3, 'S': A3, 'B': F3, 'T': F3}
    >>> possibC = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution.dominantSeventhToMajorTonic(possibC)
    {'A': A4, 'S': F5, 'B': F3, 'T': C4}
    >>> resolution.resolveV43toI6 = True
    >>> possibD = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution.dominantSeventhToMajorTonic(possibD, True)
    {'A': C5, 'S': F5, 'B': A3, 'T': C4}
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
    
    If resolveV43toi6 = True, then the resolution will be to a first inversion tonic chord.
    If resolveV43toi6 = False, then the resolution will be to a root position tonic chord.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    If inPlace = True, then pitches will be modified in place, and the input possibility will be returned.
    If inPlace = False, then a new possibility will be returned.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution.dominantSeventhToMinorTonic(possibA)
    {'A': E-4, 'S': C5, 'B': C3, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution.dominantSeventhToMinorTonic(possibB)
    {'A': F3, 'S': A-3, 'B': F3, 'T': F3}
    >>> possibC = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution.dominantSeventhToMinorTonic(possibC)
    {'A': A-4, 'S': F5, 'B': F3, 'T': C4}
    >>> possibD = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution.dominantSeventhToMinorTonic(possibD, True)
    {'A': C5, 'S': F5, 'B': A-3, 'T': C4}
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
                samplePitch.transpose('m2', True)
            else:
                samplePitch.transpose('-M2', True)
        elif samplePitch.name == seventhName:
            if inversion == 2 and resolveV43toI6:
                samplePitch.transpose('M2', True)
            else:
                samplePitch.transpose('-M2', True)
        
    return dpCopy

# DECEPTIVE RESOLUTIONS
def dominantSeventhToMajorSubmediant(dominantPossib, inPlace = False):
    '''
    Takes a possibility which contains pitches forming a dominant seventh chord and returns its
    proper resolution to the major submediant (VI) in root position as another possibility.
    
    A dominant possibility has to be in root position in order to properly resolve to its submediant.
    Therefore, a ResolutionException is raised if the possibility is not in root position.
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution.dominantSeventhToMajorSubmediant(possibA)
    {'A': E-4, 'S': C5, 'B': A-2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution.dominantSeventhToMajorSubmediant(possibB)
    {'A': F3, 'S': A-3, 'B': D-3, 'T': F3}
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
    proper resolution to the minor submediant (vi) in root position as another possibility.
    
    A dominant possibility has to be in root position in order to properly resolve to its submediant.
    Therefore, a ResolutionException is raised if the possibility is not in root position.

    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution.dominantSeventhToMinorSubmediant(possibA)
    {'A': E4, 'S': C5, 'B': A2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution.dominantSeventhToMinorSubmediant(possibB)
    {'A': F3, 'S': A3, 'B': D3, 'T': F3}
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
    
    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution.dominantSeventhToMajorSubdominant(possibA)
    {'A': F4, 'S': C5, 'B': A2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution.dominantSeventhToMajorSubdominant(possibB)
    {'A': F3, 'S': B-3, 'B': D3, 'T': F3}
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

    A ResolutionException is raised if the possibility does not spell out a dominant seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution.dominantSeventhToMinorSubdominant(possibA)
    {'A': F4, 'S': C5, 'B': A-2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution.dominantSeventhToMinorSubdominant(possibB)
    {'A': F3, 'S': B-3, 'B': D-3, 'T': F3}
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
    its proper resolution to the major tonic or either of its inversions as another possibility. 
    
    If doubledRoot = False, then the resolution will have its third doubled.
    If doubledRoot = True, then the resolution will have its root doubled.
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution.diminishedSeventhToMajorTonic(possibA)
    {'A': F#4, 'S': A4, 'B': D3, 'T': F#3}
    >>> resolution.diminishedSeventhToMajorTonic(possibA, True) # Alternate resolution, contains parallel fifths
    {'A': D4, 'S': A4, 'B': D3, 'T': F#3}
    >>> possibB = resolution.diminishedSeventhToMajorTonic(possibA, True)    
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
    its proper resolution to the minor tonic or either of its inversions as another possibility. 
    
    If doubledRoot = False, then the resolution will have its third doubled.
    If doubledRoot = True, then the resolution will have its root doubled.
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution.diminishedSeventhToMinorTonic(possibA)
    {'A': F4, 'S': A4, 'B': D3, 'T': F3}
    >>> resolution.diminishedSeventhToMinorTonic(possibA, True) # Alternate resolution, contains parallel fifths, but not parallel perfect fifths
    {'A': D4, 'S': A4, 'B': D3, 'T': F3}
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
    
    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution.diminishedSeventhToMajorSubdominant(possibA)
    {'A': D4, 'S': B4, 'B': D3, 'T': G3}
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

    A ResolutionException is raised if the possibility does not spell out a diminished seventh chord.

    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution.diminishedSeventhToMinorSubdominant(possibA)
    {'A': D4, 'S': B-4, 'B': D3, 'T': G3}
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

