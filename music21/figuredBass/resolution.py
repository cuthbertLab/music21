#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         resolution.py
# Purpose:      Defines standard resolutions for possibility instances
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import music21
import unittest

from music21 import chord
from music21 import note
from music21 import stream

'''
Resolution methods. Note that the methods are speed-enhanced, 
they assume that the possibilities provided correctly correspond
to them and may ask for more information that would be asked for
if designed to stand alone.
'''

def augmentedSixthToDominant(augSixthPossib, augSixthType):
    '''
    Italian augmented 6ths not currently supported.
    
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Bb2 = HashablePitch('B-2')
    >>> D4 = HashablePitch('D4')
    >>> E4 = HashablePitch('E4')
    >>> Es4 = HashablePitch('E#4')
    >>> F4 = HashablePitch('F4')
    >>> G4 = HashablePitch('G4')
    >>> Gs4 = HashablePitch('G#4')
    >>> iv6 = (G4, D4, D4, Bb2)
    >>> itAug6 = (Gs4, D4, D4, Bb2)
    >>> frAug6 = (Gs4, E4, D4, Bb2)
    >>> grAug6 = (Gs4, F4, D4, Bb2)
    >>> swAug6 = (Gs4, Es4, D4, Bb2)
    >>> resolution.augmentedSixthToDominant(frAug6, 1)
    (A4, E4, C#4, A2)
    >>> resolution.augmentedSixthToDominant(grAug6, 2)
    (A4, E4, C#4, A2)
    >>> resolution.augmentedSixthToDominant(swAug6, 3)
    (A4, E4, C#4, A2)
    '''
    #Type 0: Italian, type 1: French, type 2: German, type 3: Swiss
    augSixthChord = chord.Chord(augSixthPossib)
    augSixthChord.removeRedundantPitchNames()
    if augSixthType == 1 or augSixthType == 3:
        augSixthChord.root(augSixthChord.getChordStep(3))
    
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    tonic = augSixthChord.getChordStep(5)
    
    howToResolve = \
    [(lambda p: p.name == bass.name, '-m2'),
    (lambda p: p.name == root.name, 'm2'),
    (lambda p: p.name == tonic.name, '-m2'),
    (lambda p: augSixthType == 3, 'd1'),
    (lambda p: augSixthType == 2, '-m2')]

    return resolvePitches(augSixthPossib, howToResolve)

def augmentedSixthToMajorTonic(augSixthPossib, augSixthType):
    '''
    Italian augmented 6ths not currently supported.

    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Bb2 = HashablePitch('B-2')
    >>> D4 = HashablePitch('D4')
    >>> E4 = HashablePitch('E4')
    >>> Es4 = HashablePitch('E#4')
    >>> F4 = HashablePitch('F4')
    >>> G4 = HashablePitch('G4')
    >>> Gs4 = HashablePitch('G#4')
    >>> iv6 = (G4, D4, D4, Bb2)
    >>> itAug6 = (Gs4, D4, D4, Bb2)
    >>> frAug6 = (Gs4, E4, D4, Bb2)
    >>> grAug6 = (Gs4, F4, D4, Bb2)
    >>> swAug6 = (Gs4, Es4, D4, Bb2)
    >>> resolution.augmentedSixthToMajorTonic(frAug6, 1)
    (A4, F#4, D4, A2)
    >>> resolution.augmentedSixthToMajorTonic(grAug6, 2)
    (A4, F#4, D4, A2)    
    >>> resolution.augmentedSixthToMajorTonic(swAug6, 3)
    (A4, F#4, D4, A2)    
    '''
    augSixthChord = chord.Chord(augSixthPossib)
    augSixthChord.removeRedundantPitchNames()
    if augSixthType == 1 or augSixthType == 3:
        augSixthChord.root(augSixthChord.getChordStep(3))
    
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    tonic = augSixthChord.getChordStep(5)
    
    howToResolve = \
    [(lambda p: p.name == bass.name, '-m2'),
    (lambda p: p.name == root.name, 'm2'),
    (lambda p: p.name == tonic.name, 'P1'),
    (lambda p: augSixthType == 1, 'M2'),
    (lambda p: augSixthType == 2, 'A1'),
    (lambda p: augSixthType == 3, 'm2')]

    return resolvePitches(augSixthPossib, howToResolve)

def augmentedSixthToMinorTonic(augSixthPossib, augSixthType):
    '''
    Italian augmented 6ths not currently supported.

    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Bb2 = HashablePitch('B-2')
    >>> D4 = HashablePitch('D4')
    >>> E4 = HashablePitch('E4')
    >>> Es4 = HashablePitch('E#4')
    >>> F4 = HashablePitch('F4')
    >>> G4 = HashablePitch('G4')
    >>> Gs4 = HashablePitch('G#4')
    >>> iv6 = (G4, D4, D4, Bb2)
    >>> itAug6 = (Gs4, D4, D4, Bb2)
    >>> frAug6 = (Gs4, E4, D4, Bb2)
    >>> grAug6 = (Gs4, F4, D4, Bb2)
    >>> swAug6 = (Gs4, Es4, D4, Bb2)
    >>> resolution.augmentedSixthToMinorTonic(frAug6, 1)
    (A4, F4, D4, A2)
    >>> resolution.augmentedSixthToMinorTonic(grAug6, 2)
    (A4, F4, D4, A2)
    >>> resolution.augmentedSixthToMinorTonic(swAug6, 3)
    (A4, F4, D4, A2)    
    '''
    augSixthChord = chord.Chord(augSixthPossib)
    augSixthChord.removeRedundantPitchNames()
    if augSixthType == 1 or augSixthType == 3:
        augSixthChord.root(augSixthChord.getChordStep(3))
    
    bass = augSixthChord.bass()
    root = augSixthChord.root()
    tonic = augSixthChord.getChordStep(5)
    
    howToResolve = \
    [(lambda p: p.name == bass.name, '-m2'),
    (lambda p: p.name == root.name, 'm2'),
    (lambda p: p.name == tonic.name, 'P1'),
    (lambda p: augSixthType == 1, 'm2'),
    (lambda p: augSixthType == 3, 'd2')]
    
    return resolvePitches(augSixthPossib, howToResolve)

def dominantSeventhToMajorTonic(domPossib, resolveV43toI6 = False):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> G2 = HashablePitch('G2')
    >>> C3 = HashablePitch('C3')
    >>> E3 = HashablePitch('E3')
    >>> G3 = HashablePitch('G3')
    >>> Bb3 = HashablePitch('B-3')
    >>> B3 = HashablePitch('B3')
    >>> C4 = HashablePitch('C4')
    >>> F4 = HashablePitch('F4')
    >>> Bb4 = HashablePitch('B-4')
    >>> D5 = HashablePitch('D5')
    >>> E5 = HashablePitch('E5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMajorTonic(domPossibA1)
    >>> resPossibA1
    (C5, E4, C4, C3)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA1, resPossibA1)
    
    >>> domPossibA2 = (Bb3, G3, E3, C3)
    >>> resPossibA2 = resolution.dominantSeventhToMajorTonic(domPossibA2)
    >>> resPossibA2
    (A3, F3, F3, F3)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA2, resPossibA2)
    
    >>> domPossibA3 = (E5, Bb4, C4, G3)
    >>> resPossibA3a = resolution.dominantSeventhToMajorTonic(domPossibA3, False)
    >>> resPossibA3a
    (F5, A4, C4, F3)
    >>> resPossibA3b = resolution.dominantSeventhToMajorTonic(domPossibA3, True)
    >>> resPossibA3b    
    (F5, C5, C4, A3)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA3, resPossibA3a, domPossibA3, resPossibA3b)
    '''
    V7chord = chord.Chord(domPossib)   
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'M3').name
    fifthName = transpose(root,'P5').name
    seventhName = transpose(root,'m7').name
    
    howToResolve = \
    [(lambda p: p.name == rootName and p == bass, 'P4'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName and resolveV43toI6, 'M2'),
    (lambda p: p.name == fifthName, '-M2'),
    (lambda p: p.name == seventhName and resolveV43toI6, 'M2'),
    (lambda p: p.name == seventhName, '-m2')]
    
    return resolvePitches(domPossib, howToResolve)

def dominantSeventhToMinorTonic(domPossib, resolveV43toi6 = False):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> G2 = HashablePitch('G2')
    >>> C3 = HashablePitch('C3')
    >>> E3 = HashablePitch('E3')
    >>> G3 = HashablePitch('G3')
    >>> Bb3 = HashablePitch('B-3')
    >>> B3 = HashablePitch('B3')
    >>> C4 = HashablePitch('C4')
    >>> F4 = HashablePitch('F4')
    >>> Bb4 = HashablePitch('B-4')
    >>> D5 = HashablePitch('D5')
    >>> E5 = HashablePitch('E5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMinorTonic(domPossibA1)
    >>> resPossibA1
    (C5, E-4, C4, C3)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA1, resPossibA1)
    
    >>> domPossibA2 = (Bb3, G3, E3, C3)
    >>> resPossibA2 = resolution.dominantSeventhToMinorTonic(domPossibA2)
    >>> resPossibA2
    (A-3, F3, F3, F3)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA2, resPossibA2)
    
    >>> domPossibA3 = (E5, Bb4, C4, G3)
    >>> resPossibA3a = resolution.dominantSeventhToMinorTonic(domPossibA3, False)
    >>> resPossibA3a
    (F5, A-4, C4, F3)
    >>> resPossibA3b = resolution.dominantSeventhToMinorTonic(domPossibA3, True)
    >>> resPossibA3b
    (F5, C5, C4, A-3)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA3, resPossibA3a, domPossibA3, resPossibA3b)
    '''
    V7chord = chord.Chord(domPossib)   
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'M3').name
    fifthName = transpose(root,'P5').name
    seventhName = transpose(root,'m7').name

    howToResolve = \
    [(lambda p: p.name == rootName and p == bass, 'P4'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName and resolveV43toi6, 'm2'),
    (lambda p: p.name == fifthName, '-M2'),
    (lambda p: p.name == seventhName and resolveV43toi6, 'M2'),
    (lambda p: p.name == seventhName, '-M2')]
    
    return resolvePitches(domPossib, howToResolve)

def dominantSeventhToMajorSubmediant(domPossib):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> G2 = HashablePitch('G2')
    >>> B3 = HashablePitch('B3')
    >>> F4 = HashablePitch('F4')
    >>> D5 = HashablePitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMajorSubmediant(domPossibA1)
    >>> resPossibA1
    (C5, E-4, C4, A-2)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA1, resPossibA1)    
    '''
    V7chord = chord.Chord(domPossib)   
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'M3').name
    fifthName = transpose(root,'P5').name
    seventhName = transpose(root,'m7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'm2'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName, '-M2'),
    (lambda p: p.name == seventhName, '-M2')]
    
    return resolvePitches(domPossib, howToResolve)

def dominantSeventhToMinorSubmediant(domPossib):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> G2 = HashablePitch('G2')
    >>> B3 = HashablePitch('B3')
    >>> F4 = HashablePitch('F4')
    >>> D5 = HashablePitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMinorSubmediant(domPossibA1)
    >>> resPossibA1
    (C5, E4, C4, A2)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA1, resPossibA1)    
    '''
    V7chord = chord.Chord(domPossib)   
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'M3').name
    fifthName = transpose(root,'P5').name
    seventhName = transpose(root,'m7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'M2'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName, '-M2'),
    (lambda p: p.name == seventhName, '-m2')]
    
    return resolvePitches(domPossib, howToResolve)

def dominantSeventhToMajorSubdominant(domPossib):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> G2 = HashablePitch('G2')
    >>> B3 = HashablePitch('B3')
    >>> F4 = HashablePitch('F4')
    >>> D5 = HashablePitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMajorSubdominant(domPossibA1)
    >>> resPossibA1
    (C5, F4, C4, A2)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA1, resPossibA1)    
    '''
    V7chord = chord.Chord(domPossib)   
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'M3').name
    fifthName = transpose(root,'P5').name
    seventhName = transpose(root,'m7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'M2'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName, '-M2')]
        
    return resolvePitches(domPossib, howToResolve)

def dominantSeventhToMinorSubdominant(domPossib):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> G2 = HashablePitch('G2')
    >>> B3 = HashablePitch('B3')
    >>> F4 = HashablePitch('F4')
    >>> D5 = HashablePitch('D5')
    >>> domPossibA1 = (D5, F4, B3, G2)
    >>> resPossibA1 = resolution.dominantSeventhToMinorSubdominant(domPossibA1)
    >>> resPossibA1
    (C5, F4, C4, A-2)
    >>> #_DOCS_SHOW resolution.ShowResolutions(domPossibA1, resPossibA1)    
    '''
    V7chord = chord.Chord(domPossib)   
    root = V7chord.root()
    bass = V7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'M3').name
    fifthName = transpose(root,'P5').name
    seventhName = transpose(root,'m7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'm2'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName, '-M2')]
        
    return resolvePitches(domPossib, howToResolve)

def diminishedSeventhToMajorTonic(dimPossib, doubledRoot = False):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = HashablePitch('C#3')
    >>> G3 = HashablePitch('G3')
    >>> E4 = HashablePitch('E4')
    >>> Bb4 = HashablePitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibAa = resolution.diminishedSeventhToMajorTonic(dimPossibA, False)
    >>> resPossibAa
    (A4, F#4, F#3, D3)
    >>> resPossibAb = resolution.diminishedSeventhToMajorTonic(dimPossibA, True)
    >>> resPossibAb
    (A4, D4, F#3, D3)
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibAa, dimPossibA, resPossibAb)
    '''
    dim7chord = chord.Chord(dimPossib)
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'m3').name
    fifthName = transpose(root,'d5').name
    seventhName = transpose(root,'d7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'm2'),
    (lambda p: p.name == thirdName and doubledRoot, '-M2'),
    (lambda p: p.name == thirdName, 'M2'),
    (lambda p: p.name == fifthName, '-m2'),
    (lambda p: p.name == seventhName, '-m2')]
        
    return resolvePitches(dimPossib, howToResolve)
    
def diminishedSeventhToMinorTonic(dimPossib, doubledRoot = False):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = HashablePitch('C#3')
    >>> G3 = HashablePitch('G3')
    >>> E4 = HashablePitch('E4')
    >>> Bb4 = HashablePitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibAa = resolution.diminishedSeventhToMinorTonic(dimPossibA, False)
    >>> resPossibAa
    (A4, F4, F3, D3)
    >>> resPossibAb = resolution.diminishedSeventhToMinorTonic(dimPossibA, True)
    >>> resPossibAb
    (A4, D4, F3, D3)
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibAa, dimPossibA, resPossibAb)
    '''
    dim7chord = chord.Chord(dimPossib)
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'m3').name
    fifthName = transpose(root,'d5').name
    seventhName = transpose(root,'d7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'm2'),
    (lambda p: p.name == thirdName and doubledRoot, '-M2'),
    (lambda p: p.name == thirdName, 'm2'),
    (lambda p: p.name == fifthName, '-M2'),
    (lambda p: p.name == seventhName, '-m2')]
        
    return resolvePitches(dimPossib, howToResolve)

def diminishedSeventhToMajorSubdominant(dimPossib):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = HashablePitch('C#3')
    >>> G3 = HashablePitch('G3')
    >>> E4 = HashablePitch('E4')
    >>> Bb4 = HashablePitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibA = resolution.diminishedSeventhToMajorSubdominant(dimPossibA)
    >>> resPossibA
    (B4, D4, G3, D3)
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibA)
    '''
    dim7chord = chord.Chord(dimPossib)
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'m3').name
    fifthName = transpose(root,'d5').name
    seventhName = transpose(root,'d7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'm2'),
    (lambda p: p.name == thirdName, '-M2'),
    (lambda p: p.name == seventhName, 'A1')]
        
    return resolvePitches(dimPossib, howToResolve)

def diminishedSeventhToMinorSubdominant(dimPossib):
    '''
    >>> from music21.figuredBass.fbPitch import HashablePitch
    >>> from music21.figuredBass import resolution
    >>> Cs3 = HashablePitch('C#3')
    >>> G3 = HashablePitch('G3')
    >>> E4 = HashablePitch('E4')
    >>> Bb4 = HashablePitch('B-4')
    >>> dimPossibA = (Bb4, E4, G3, Cs3)
    >>> resPossibA = resolution.diminishedSeventhToMinorSubdominant(dimPossibA)
    >>> resPossibA
    (B-4, D4, G3, D3)
    >>> #_DOCS_SHOW resolution.showResolutions(dimPossibA, resPossibA)
    '''
    dim7chord = chord.Chord(dimPossib)
    root = dim7chord.root()
    bass = dim7chord.bass()
    rootName = root.name
    thirdName = transpose(root,'m3').name
    fifthName = transpose(root,'d5').name
    seventhName = transpose(root,'d7').name

    howToResolve = \
    [(lambda p: p.name == rootName, 'm2'),
    (lambda p: p.name == thirdName, '-M2')]
            
    return resolvePitches(dimPossib, howToResolve)

'''
transpositionsTable = {}
def transpose(samplePitch, intervalString):
    args = (samplePitch, intervalString)
    if transpositionsTable.has_key(args):
        return transpositionsTable[args]
    transposedPitch = samplePitch.transpose(intervalString)
    transpositionsTable[(samplePitch, intervalString)] = transposedPitch
    return transposedPitch
'''

def transpose(samplePitch, intervalString):
    return samplePitch.transpose(intervalString)

def resolvePitches(possibToResolve, howToResolve):
    howToResolve.append((lambda p: True, 'P1'))
    resPitches = []
    for samplePitch in possibToResolve:
        for (expression, intervalString) in howToResolve:
            if expression(samplePitch):
                resPitches.append(transpose(samplePitch, intervalString))
                break
        
    return tuple(resPitches)

def showResolutions(*allPossib):
    upperParts = stream.Part()
    bassLine = stream.Part()
    for possibA in allPossib:
        chordA = chord.Chord(possibA[0:-1])
        chordA.quarterLength = 2.0 
        bassA = note.Note(possibA[-1])
        bassA.quarterLength = 2.0
        upperParts.append(chordA)
        bassLine.append(bassA)
    score = stream.Score()
    score.insert(0, upperParts)
    score.insert(0, bassLine)
    score.show()
    

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