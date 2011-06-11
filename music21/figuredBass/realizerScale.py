#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizerScale.py
# Purpose:      music21 class for conveniently representing the concept of
#                a figured bass scale
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy
import itertools
import music21
import unittest

from music21 import note
from music21 import pitch
from music21 import key
from music21 import scale
from music21.figuredBass import notation

scaleModes = {'major' : scale.MajorScale,
              'minor' : scale.MinorScale,
              'dorian' : scale.DorianScale,
              'phrygian' : scale.PhrygianScale,
              'hypophrygian' : scale.HypophrygianScale}

#-------------------------------------------------------------------------------

class FiguredBassScale(object):
    _DOC_ATTR = {'realizerScale': 'A :class:`~music21.scale.Scale` based on the desired value and mode.',
                 'keySig': 'A :class:`~music21.key.KeySignature` corresponding to the scale value and mode.'}
    
    def __init__(self, scaleValue = 'C', scaleMode = 'major'):
        '''
        Acts as a wrapper for :class:`~music21.scale.Scale`. Used to represent the
        concept of a figured bass scale, with a scale value and mode.
        
        
        Accepted scale types: major, minor, dorian, phrygian, and hypophrygian.
        A FiguredBassScale is raised if an invalid scale type is provided.
        
        >>> from music21.figuredBass import realizerScale
        >>> fbScale = realizerScale.FiguredBassScale()
        >>> fbScale.realizerScale
        <music21.scale.MajorScale C major>
        >>> fbScale.keySig
        <music21.key.KeySignature of no sharps or flats>
        '''
        try:
            foo = scaleModes[scaleMode]
            self.realizerScale = foo(scaleValue)
            self.keySig = key.KeySignature(key.pitchToSharps(scaleValue, scaleMode))
        except KeyError:
            raise FiguredBassScaleException("Unsupported scale type-> " + scaleMode)
    
    def getPitchNames(self, bassPitch, notationString = None):
        '''        
        Takes a bassPitch and notationString and returns a list of corresponding
        pitch names based on the scale value and mode above and inclusive of the 
        bassPitch name. 

        >>> from music21.figuredBass import realizerScale
        >>> fbScale = realizerScale.FiguredBassScale()
        >>> fbScale.getPitchNames('D3', '6')
        ['D', 'F', 'B']
        >>> fbScale.getPitchNames('G3')
        ['G', 'B', 'D']
        >>> fbScale.getPitchNames('B3', '6,#5')
        ['B', 'D', 'F#', 'G']
        >>> fbScale.getPitchNames('C#3', '-7') # Fully diminished seventh chord
        ['C#', 'E', 'G', 'B-']
        '''
        bassPitch = convertToPitch(bassPitch) #Convert string to pitch (if necessary)
        bassSD = self.realizerScale.getScaleDegreeFromPitch(bassPitch)
        nt = notation.Notation(notationString)
        
        if bassSD == None:
            bassPitchCopy = copy.deepcopy(bassPitch)
            bassNote = note.Note(bassPitchCopy)
            if (self.keySig.accidentalByStep(bassNote.step)
                    != bassNote.accidental):
                bassNote.accidental = \
                    self.keySig.accidentalByStep(bassNote.step)
            bassSD = self.realizerScale.getScaleDegreeFromPitch(bassNote.pitch)

        pitchNames = []
        for i in range(len(nt.numbers)):
            pitchSD = (bassSD + nt.numbers[i] - 1) % 7
            samplePitch = self.realizerScale.pitchFromDegree(pitchSD)
            pitchName = nt.modifiers[i].modifyPitchName(samplePitch.name)
            pitchNames.append(pitchName)

        pitchNames.append(bassPitch.name)
        pitchNames.reverse()
        return pitchNames
    
    def getSamplePitches(self, bassPitch, notationString = None):
        '''
        Returns all pitches for a bassPitch and notationString within
        an octave of the bassPitch, inclusive of the bassPitch but
        exclusive at the upper bound. In other words, this method 
        returns the most compact complete chord implied by the bassPitch
        and its figures.
        
        >>> from music21.figuredBass import realizerScale
        >>> fbScale = realizerScale.FiguredBassScale()
        >>> fbScale.getSamplePitches('D3', '6') # First inversion triad
        [D3, F3, B3]
        >>> fbScale.getSamplePitches('G3') # Root position triad
        [G3, B3, D4]
        >>> fbScale.getSamplePitches('B3', '6,5') # First inversion seventh chord
        [B3, D4, F4, G4]
        >>> fbScale.getSamplePitches('F3', '-6,-') # Neapolitan chord
        [F3, A-3, D-4]
        >>> fbScale.getSamplePitches('C5', '4,3') # Second inversion seventh chord
        [C5, E5, F5, A5]
        >>> fbScale.getSamplePitches('C#3', '-7') # Fully diminished seventh chord
        [C#3, E3, G3, B-3]
        '''
        bassPitch = convertToPitch(bassPitch) #Convert string to pitch (if necessary)
        maxPitch = bassPitch.transpose('d8')
        
        samplePitches = self.getPitches(bassPitch, notationString, maxPitch)
        return samplePitches
        
    def getPitches(self, bassPitch, notationString = None, maxPitch=pitch.Pitch('B5')):
        '''
        Takes in a bassPitch, a notationString, and a maxPitch representing the highest
        possible pitch that can be returned. Returns a sorted list of pitches which
        correspond to the pitches of each specific pitch name found through getPitchNames
        that fall between the bassPitch and the maxPitch, inclusive of both.

        >>> from music21.figuredBass import realizerScale
        >>> fbScale = realizerScale.FiguredBassScale()
        >>> fbScale.getPitches('C3') # Root position triad
        [C3, E3, G3, C4, E4, G4, C5, E5, G5]
        >>> fbScale.getPitches('D3', '6') # First inversion triad
        [D3, F3, B3, D4, F4, B4, D5, F5, B5]
        >>> fbScale.getPitches(pitch.Pitch('G3'), '7', 'F4') # Root position seventh chord
        [G3, B3, D4, F4]
        '''
        bassPitch = convertToPitch(bassPitch)
        maxPitch = convertToPitch(maxPitch)
        pitchNames = self.getPitchNames(bassPitch, notationString)
        iter1 = itertools.product(pitchNames, range(maxPitch.octave + 1))
        iter2 = itertools.imap(lambda x: pitch.Pitch(x[0] + str(x[1])), iter1)
        iter3 = itertools.ifilterfalse(lambda samplePitch: bassPitch > samplePitch, iter2)
        iter4 = itertools.ifilterfalse(lambda samplePitch: samplePitch > maxPitch, iter3)
        allPitches = list(iter4)
        allPitches.sort()
        return allPitches
    
    def __repr__(self):
        return "<music21.figuredBass.realizerScale FiguredBassScale>"
    
    
class FiguredBassScaleException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------

# Helper Methods
def convertToPitch(pitchString):
    '''
    Converts a pitchString to a :class:`~music21.pitch.Pitch`, only if necessary.
    
    >>> from music21.figuredBass import realizerScale
    >>> pitchString = 'C5'
    >>> realizerScale.convertToPitch(pitchString)
    C5
    >>> realizerScale.convertToPitch(pitch.Pitch('E4')) # does nothing
    E4
    '''
    if isinstance(pitchString, pitch.Pitch):
        return pitchString
    
    if isinstance(pitchString, str):
        try:
            return pitch.Pitch(pitchString)
        except:
            raise ValueError("Cannot convert string " + pitchString + " to a music21 Pitch.")
    
    raise TypeError("Cannot convert " + pitchString + " to a music21 Pitch.")


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof