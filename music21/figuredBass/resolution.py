#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         resolution.py
# Purpose:      Defines standard resolutions for chords
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import copy

from music21.figuredBass import realizerScale
from music21.figuredBass import notation
from music21 import pitch
from music21 import chord
from music21 import interval

#Used Ex.76 (page 46) from 'The Basis of Harmony' by Frederick J. Horwood
resolveV43toI6 = False
doubledRootInDimSeventhResolution = False

#Dominant seventh -> tonic (standard resolution)
def dominantSeventhToTonic(pitches, resolveTo='major', inPlace=False):
    '''
    Given a list of four pitches correctly spelling out a dominant seventh chord,
    returns its standard resolution to either the major tonic (I) or minor tonic(i).
    
    A dominant seventh chord in second inversion can either resolve to a root position
    tonic or a first inversion tonic. Indicate preference by modifying resolveV43toI6.
    
    >>> from music21.figuredBass import resolution as r
    >>> r.dominantSeventhToTonic(['C3', 'G3', 'E4', 'B-4'], 'minor')
    [F3, F3, F4, A-4]
    >>> r.dominantSeventhToTonic(['C3', 'G3', 'E4', 'B-4'], 'major')
    [F3, F3, F4, A4]
    >>> r.resolveV43toI6 = False
    >>> r.dominantSeventhToTonic(['G3', 'C4', 'B-4', 'E5'], 'minor') #Doubled root
    [F3, C4, A-4, F5]
    >>> r.resolveV43toI6 = True
    >>> r.dominantSeventhToTonic(['G3', 'C4', 'B-4', 'E5'], 'minor') #Doubled fifth
    [A-3, C4, C5, F5]
    '''
    #Standard resolution is as follows
    #Tritone resolves to M3/m6 if major, resolves to m3/M6 if minor
    #If chord in root position, root goes up to tonic. Else, stays the same.
    #Fifth of chord goes to tonic, can go to third when it's the bass (2nd inversion)

    c = chord.Chord(copy.deepcopy(pitches))

    if not c.isDominantSeventh():
        #TODO: Add support for root position V7 chords with missing fifth
        raise ResolutionException("Pitches do not form a correctly spelled dominant seventh chord.")
    if not len(pitches) == 4:
        raise ResolutionException("Not a four part chord. Can't resolve.")
    if not (resolveTo == 'major' or resolveTo == 'minor'):
        raise ResolutionException("Unsupported scale type. Only major or minor.")
    
    if not inPlace:
        pitches = copy.deepcopy(pitches)  #Make a copy of the list, can then resolve in place.
        
    for i in range(len(pitches)):
        pitches[i] = realizerScale.convertToPitch(pitches[i])
        pitches[i].order = i
    
    root = pitches[pitches.index(c.root())]
    third = pitches[pitches.index(c.third)]
    fifth = pitches[pitches.index(c.fifth)]
    seventh = pitches[pitches.index(c.seventh)]
    
    #Resolve the root (if necessary)
    if c.inversion() == 0:
        root.transpose('P4', True) #Root ascends (by leap) to tonic
    
    #Resolve the fifth
    if not (c.inversion() == 2) or not (resolveV43toI6):
        fifth.transpose('-M2', True) #2nd scale degree descends to tonic
    else:
        if resolveTo == 'major':
            fifth.transpose('M2', True) #2nd scale degree ascends to 3rd
        elif resolveTo == 'minor':
            fifth.transpose('m2', True) #2nd scale degree ascends to 3rd
    
    #Resolve the tritone:
    #Resolve the third
    third.transpose('m2', True) #Leading tone resolves to tonic
    
    #Resolve the seventh
    if resolveV43toI6 and c.inversion() == 2:
        seventh.transpose('M2', True) #4th scale degree ascends to 5th
    else:
        if resolveTo == 'major':
            seventh.transpose('-m2', True) #4th scale degree descends to 3rd
        elif resolveTo == 'minor':
            seventh.transpose('-M2', True) #4th scale degree descends to 3rd
   
    for i in range(len(pitches)):
        del pitches[i].order

    return pitches

#Dominant seventh -> submediant (deceptive resolution)
def dominantSeventhToSubmediant(pitches, resolveTo='major', inPlace=False):
    '''
    Given a list of four pitches correctly spelling out a dominant seventh chord in
    root position, returns its standard resolution to either the major submediant (VI)
    or the minor submediant (vi)

    >>> from music21.figuredBass import resolution as r
    >>> r.dominantSeventhToSubmediant(['C3', 'G3', 'E4', 'B-4'], 'major')
    [D-3, F3, F4, A-4]
    >>> r.dominantSeventhToSubmediant(['C3', 'G3', 'E4', 'B-4'], 'minor')
    [D3, F3, F4, A4]
    >>> r.dominantSeventhToSubmediant(['G3', 'C4', 'B-4', 'E5'], 'minor')
    Traceback (most recent call last):
    ResolutionException: A deceptive resolution can only happen on the root position V7.
    '''
    #Resolution is just like standard resolution except root moves to submediant instead of tonic
    c = chord.Chord(copy.deepcopy(pitches))

    if not c.isDominantSeventh():
        raise ResolutionException("Pitches do not form a correctly spelled dominant seventh chord.")
    if not len(pitches) == 4:
        raise ResolutionException("Not a four part chord. Can't resolve.")
    if not (resolveTo == 'major' or resolveTo == 'minor'):
        raise ResolutionException("Unsupported scale type. Only major or minor.")
    if not (c.inversion() == 0):
        raise ResolutionException("A deceptive resolution can only happen on the root position V7.")
    
    if not inPlace:
        pitches = copy.deepcopy(pitches)  #Make a copy of the list, can then resolve in place.
        
    for i in range(len(pitches)):
        pitches[i] = realizerScale.convertToPitch(pitches[i])
        pitches[i].order = i
    
    root = pitches[pitches.index(c.root())]
    third = pitches[pitches.index(c.third)]
    fifth = pitches[pitches.index(c.fifth)]
    seventh = pitches[pitches.index(c.seventh)]
    
    if resolveTo == 'major':
        root.transpose('m2', True)
    elif resolveTo == 'minor':
        root.transpose('M2', True)

    #Resolve the fifth
    fifth.transpose('-M2', True) #2nd scale degree descends to tonic

    #Resolve the tritone:
    #Resolve the third
    third.transpose('m2', True) #Leading tone resolves to tonic
    
    #Resolve the seventh
    if resolveTo == 'major':
        seventh.transpose('-M2', True) #4th scale degree descends to 3rd
    if resolveTo == 'minor':
        seventh.transpose('-m2', True) #4th scale degree descends to 3rd
   
    for i in range(len(pitches)):
        del pitches[i].order

    return pitches

#Dominant seventh -> subdominant (stationary resolution)
def dominantSeventhToSubdominant(pitches, resolveTo='major', inPlace=False):
    '''
    Given a list of four pitches correctly spelling out a dominant seventh chord in
    root position, returns its standard resolution to either the major subdominant (IV6)
    or the minor subdominant (iv6)

    >>> from music21.figuredBass import resolution as r
    >>> r.dominantSeventhToSubdominant(['C3', 'G3', 'E4', 'B-4'], 'major')
    [D3, F3, F4, B-4]
    >>> r.dominantSeventhToSubdominant(['C3', 'G3', 'E4', 'B-4'], 'minor')
    [D-3, F3, F4, B-4]
    >>> r.dominantSeventhToSubdominant(['G3', 'C4', 'B-4', 'E5'], 'minor')
    Traceback (most recent call last):
    ResolutionException: A stationary resolution can only happen on the root position V7.
    '''
    #Resolution is just like V7->submediant except the seventh remains stationary.
    c = chord.Chord(copy.deepcopy(pitches))

    if not c.isDominantSeventh():
        raise ResolutionException("Pitches do not form a correctly spelled dominant seventh chord.")
    if not len(pitches) == 4:
        raise ResolutionException("Not a four part chord. Can't resolve.")
    if not (resolveTo == 'major' or resolveTo == 'minor'):
        raise ResolutionException("Unsupported scale type. Only major or minor.")
    if not (c.inversion() == 0):
        raise ResolutionException("A stationary resolution can only happen on the root position V7.")
    
    if not inPlace:
        pitches = copy.deepcopy(pitches)  #Make a copy of the list, can then resolve in place.
        
    for i in range(len(pitches)):
        pitches[i] = realizerScale.convertToPitch(pitches[i])
        pitches[i].order = i
    
    root = pitches[pitches.index(c.root())]
    third = pitches[pitches.index(c.third)]
    fifth = pitches[pitches.index(c.fifth)]
    seventh = pitches[pitches.index(c.seventh)]
    
    if resolveTo == 'minor':
        root.transpose('m2', True)
    elif resolveTo == 'major':
        root.transpose('M2', True)

    #Resolve the fifth
    fifth.transpose('-M2', True) #2nd scale degree descends to tonic

    #Resolve the tritone:
    #Resolve the third
    third.transpose('m2', True) #Leading tone resolves to tonic
    
    #Seventh remains stationary.
       
    for i in range(len(pitches)):
        del pitches[i].order

    return pitches

#Diminished seventh -> tonic (standard resolution or alternate resolution)
#Standard resolution = doubled third
#Alternate resolution = doubled tonic
def diminishedSeventhToTonic(pitches, resolveTo='major', inPlace=False):
    '''
    Given a list of four pitches correctly spelling out a diminished seventh chord, 
    returns its standard resolution to either the major tonic (I) or the minor tonic (i).

    >>> from music21.figuredBass import resolution as r
    >>> r.doubledRootInDimSeventhResolution = False #Default
    >>> r.diminishedSeventhToTonic(['C#3', 'G3', 'E4', 'B-4'], 'minor')
    [D3, F3, F4, A4]
    >>> r.doubledRootInDimSeventhResolution = True #2nd scale degree descends to tonic instead
    >>> r.diminishedSeventhToTonic(['C#3', 'G3', 'E4', 'B-4'], 'minor')
    [D3, F3, D4, A4]
    >>> r.diminishedSeventhToTonic(['C#3', 'G3', 'E4', 'B-4'], 'major')
    [D3, F#3, D4, A4]
    '''
    c = chord.Chord(copy.deepcopy(pitches))

    if not c.isDiminishedSeventh():
        raise ResolutionException("Pitches do not form a correctly spelled diminished seventh chord.")
    if not len(pitches) == 4:
        raise ResolutionException("Not a four part chord. Can't resolve.")
    if not (resolveTo == 'major' or resolveTo == 'minor'):
        raise ResolutionException("Unsupported scale type. Only major or minor.")
    
    if not inPlace:
        pitches = copy.deepcopy(pitches)  #Make a copy of the list, can then resolve in place.
        
    for i in range(len(pitches)):
        pitches[i] = realizerScale.convertToPitch(pitches[i])
        pitches[i].order = i
    
    root = pitches[pitches.index(c.root())] #Scale degree 7
    third = pitches[pitches.index(c.third)] #Scale degree 2
    fifth = pitches[pitches.index(c.fifth)] #Scale degree 4
    seventh = pitches[pitches.index(c.seventh)] #Scale degree 6
    
    #If major, d7 resolves to M3/m3; if minor, d7 resolves to m3/M3
    
    #Resolve root (leading tone) -> goes to tonic.
    root.transpose('m2', True)
    
    #Resolve fifth, 4th scale degree descends to 3rd
    if resolveTo == 'major':
        fifth.transpose('-m2', True)
    elif resolveTo == 'minor':
        fifth.transpose('-M2', True)
        
    #Resolve third, 2nd scale degree ascends to 3rd
    if doubledRootInDimSeventhResolution:
        third.transpose('-M2', True)
    else:
        if resolveTo == 'major':
            third.transpose('M2', True)
        elif resolveTo == 'minor':
            third.transpose('m2', True)
    
    #Resolve seventh, flattened 6th scale degree (in major) descends by step to 5th
    seventh.transpose('-m2', True)
        
    for i in range(len(pitches)):
        del pitches[i].order

    return pitches

def diminishedSeventhToSubdominant(pitches, resolveTo='major', inPlace=False):
    '''
    Given a list of four pitches correctly spelling out a diminished seventh chord, 
    returns its standard resolution to either the major subdominant (IV) or the minor
    subdominant (iv).

    >>> from music21.figuredBass import resolution as r
    >>> r.doubledRootInDimSeventhResolution = False #Default
    >>> r.diminishedSeventhToSubdominant(['C#3', 'G3', 'E4', 'B-4'], 'minor') #inversion == 0
    [D3, G3, D4, B-4]
    >>> r.diminishedSeventhToSubdominant(['G3', 'C#4', 'E4', 'B-4'], 'minor') #inversion == 1
    [G3, D4, D4, B-4]
    >>> r.diminishedSeventhToSubdominant(['G3', 'C#4', 'E4', 'B-4'], 'major') #inversion == 1
    [G3, D4, D4, B4]
    '''
    c = chord.Chord(copy.deepcopy(pitches))

    if not c.isDiminishedSeventh():
        raise ResolutionException("Pitches do not form a correctly-spelled diminished-seventh chord.")
    if not len(pitches) == 4:
        raise ResolutionException("Not a four-part chord. Can't resolve.")
    if not (resolveTo == 'major' or resolveTo == 'minor'):
        raise ResolutionException("Unsupported scale type. Only major or minor.")
    
    if not inPlace:
        pitches = copy.deepcopy(pitches)  #Make a copy of the list, can then resolve in place.
        
    for i in range(len(pitches)):
        pitches[i] = realizerScale.convertToPitch(pitches[i])
        pitches[i].order = i
    
    root = pitches[pitches.index(c.root())] #Scale degree 7
    third = pitches[pitches.index(c.third)] #Scale degree 2
    fifth = pitches[pitches.index(c.fifth)] #Scale degree 4
    seventh = pitches[pitches.index(c.seventh)] #Scale degree 6

    #Scale degrees 7,2 resolve to tonic.
    root.transpose('m2', True)
    third.transpose('-M2', True)
    
    #Sixth scale degree moves up a step.
    if resolveTo == 'major':
        mSharp = notation.Modifier("+")
        mSharp.modifyPitch(seventh, True)
        
    for i in range(len(pitches)):
        del pitches[i].order

    return pitches

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

