#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         resolution2.py
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution2.dominantSeventhToMajorTonic(possibA)
    {'A': E4, 'S': C5, 'B': C3, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution2.dominantSeventhToMajorTonic(possibB)
    {'A': F3, 'S': A3, 'B': F3, 'T': F3}
    >>> possibC = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution2.dominantSeventhToMajorTonic(possibC)
    {'A': A4, 'S': F5, 'B': F3, 'T': C4}
    >>> resolution2.resolveV43toI6 = True
    >>> possibD = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution2.dominantSeventhToMajorTonic(possibD, True)
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

def dominantSeventhToMinorTonic(dominantPossib, resolveV43toI6 = False, inPlace = False):
    '''
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution2.dominantSeventhToMinorTonic(possibA)
    {'A': E-4, 'S': C5, 'B': C3, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution2.dominantSeventhToMinorTonic(possibB)
    {'A': F3, 'S': A-3, 'B': F3, 'T': F3}
    >>> possibC = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution2.dominantSeventhToMinorTonic(possibC)
    {'A': A-4, 'S': F5, 'B': F3, 'T': C4}
    >>> possibD = possibility.Possibility({'B': 'G3', 'T': 'C4', 'A': 'B-4', 'S': 'E5'})
    >>> resolution2.dominantSeventhToMinorTonic(possibD, True)
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution2.dominantSeventhToMajorSubmediant(possibA)
    {'A': E-4, 'S': C5, 'B': A-2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution2.dominantSeventhToMajorSubmediant(possibB)
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution2.dominantSeventhToMinorSubmediant(possibA)
    {'A': E4, 'S': C5, 'B': A2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution2.dominantSeventhToMinorSubmediant(possibB)
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution2.dominantSeventhToMajorSubdominant(possibA)
    {'A': F4, 'S': C5, 'B': A2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution2.dominantSeventhToMajorSubdominant(possibB)
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'G2', 'T': 'B3', 'A': 'F4', 'S': 'D5'})
    >>> resolution2.dominantSeventhToMinorSubdominant(possibA)
    {'A': F4, 'S': C5, 'B': A-2, 'T': C4}
    >>> possibB = possibility.Possibility({'B': 'C3', 'T': 'E3', 'A': 'G3', 'S': 'B-3'})
    >>> resolution2.dominantSeventhToMinorSubdominant(possibB)
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution2.diminishedSeventhToMajorTonic(possibA)
    {'A': F#4, 'S': A4, 'B': D3, 'T': F#3}
    >>> resolution2.diminishedSeventhToMajorTonic(possibA, True) # Alternate resolution, contains parallel fifths
    {'A': D4, 'S': A4, 'B': D3, 'T': F#3}
    >>> possibB = resolution2.diminishedSeventhToMajorTonic(possibA, True)    
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
    Takes a possibility which contains pitches forming a diminished seventh chord, and
    returns its proper resolution to the minor tonic or either of its inversions as another possibility. 
    
    If doubledRoot = False, then the resolution will have its third doubled.
    If doubledRoot = True, then the resolution will have its root doubled.
    
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution2.diminishedSeventhToMinorTonic(possibA)
    {'A': F4, 'S': A4, 'B': D3, 'T': F3}
    >>> resolution2.diminishedSeventhToMinorTonic(possibA, True) # Alternate resolution, contains parallel fifths, but not parallel perfect fifths
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution2.diminishedSeventhToMajorSubdominant(possibA)
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
    >>> from music21.figuredBass import possibility
    >>> from music21.figuredBass import resolution2
    >>> possibA = possibility.Possibility({'B': 'C#3', 'T': 'G3', 'A': 'E4', 'S': 'B-4'})
    >>> resolution2.diminishedSeventhToMinorSubdominant(possibA)
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

