#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizerScale.py
# Purpose:      music21 class for conveniently representing the concept of
#                a figured bass scale
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import copy

from music21 import note
from music21 import pitch
from music21 import key
from music21 import scale
from music21.figuredBass import notation

MAX_PITCH = pitch.Pitch('B5')

scaleTypes = {'major' : scale.MajorScale,
              'minor' : scale.MinorScale,
              'dorian' : scale.DorianScale,
              'phrygian' : scale.PhrygianScale,
              'hypophrygian' : scale.HypophrygianScale}

class FiguredBassScale:
    def __init__(self, scaleValue, scaleType = 'major'):
        '''
        Used to represent the concept of a figured bass scale, with a
        scale value (key) and a scale type (major is default).
        
        Other scale types: minor, dorian, phrygian, hypophrygian
        
        An exception is raised if an invalid scale type is provided.
        '''
        try:
            foo = scaleTypes[scaleType]
            self.realizerScale = foo(scaleValue)
            self.keySig = key.KeySignature(key.pitchToSharps(scaleValue, scaleType))
        except KeyError:
            raise FiguredBassScaleException("Unsupported scale type-> " + scaleType)
    
    def getPitchNames(self, bassPitch, notationString=''):
        '''
        Given a bass pitch and a corresponding notation string,
        returns a list of corresponding pitch names.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale.getPitchNames('D3', '6')
        ['D', 'F', 'B']
        >>> fbScale.getPitchNames('G3')
        ['G', 'B', 'D']
        >>> fbScale.getPitchNames('B3', '6,#5')
        ['B', 'D', 'F#', 'G']
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
            pitchSD = bassSD + nt.numbers[i] - 1
            samplePitch = self.realizerScale.pitchFromDegree(pitchSD)
            pitchName = nt.modifiers[i].modifyPitchName(samplePitch.name)
            pitchNames.append(pitchName)

        pitchNames.append(bassPitch.name)
        pitchNames.reverse()
        return pitchNames
    
    def getSamplePitches(self, bassPitch, notationString = ''):
        '''
        Given a bass pitch and a corresponding notation string,
        returns a list of corresponding pitches within the octave
        above the bass pitch.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale.getSamplePitches('D3', '6') #First inversion triad
        [D3, F3, B3]
        >>> fbScale.getSamplePitches('G3') #Root position triad
        [G3, B3, D4]
        >>> fbScale.getSamplePitches('B3', '6,5') #First inversion seventh chord
        [B3, D4, F4, G4]
        >>> fbScale.getSamplePitches('F3', '-6,-') #Neapolitan chord
        [F3, A-3, D-4]
        >>> fbScale.getSamplePitches('C5', '4,3') #Second inversion seventh chord
        [C5, E5, F5, A5]
        >>> fbScale.getSamplePitches('C#3', '-7') #Fully diminished seventh chord
        [C#3, E3, G3, B-3]
        '''
        bassPitch = convertToPitch(bassPitch) #Convert string to pitch (if necessary)
        maxPitch = copy.deepcopy(bassPitch)
        maxPitch.transpose('d8', True)
        
        samplePitches = self.getPitches(bassPitch, notationString, maxPitch)
        samplePitches.sort()
        return samplePitches
        
    def getPitches(self, bassPitch, notationString = '', maxPitch=MAX_PITCH):
        '''
        Given a bass pitch and a corresponding notation string,
        returns a list of corresponding pitches, located at the
        specified intervals above the bassPitch according to said
        notation.

        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale.getPitches('C3') #Root position triad
        [C3, E3, G3, C4, E4, G4, C5, E5, G5]
        >>> fbScale.getPitches('D3', '6') #First inversion triad
        [D3, F3, B3, D4, F4, B4, D5, F5, B5]
        >>> fbScale.getPitches(pitch.Pitch('G3'), '7', 'F4') #Root position seventh chord
        [G3, B3, D4, F4]
        '''
        bassPitch = convertToPitch(bassPitch)
        maxPitch = convertToPitch(maxPitch)
        
        nt = notation.Notation(notationString)
        pitchNames = self.getPitchNames(bassPitch, notationString)
        octaveLimit = maxPitch.octave
        allPitches = []
        for pitchName in pitchNames:
            for i in range(1, octaveLimit + 1):
                allPitches.append(pitch.Pitch(pitchName + str(i)))
    
        pitchesAboveNote = []
        for givenPitch in allPitches:
            if not (givenPitch < bassPitch) and not (givenPitch > maxPitch):
                pitchesAboveNote.append(givenPitch)
        
        pitchesAboveNote.sort()
        return pitchesAboveNote
    
    
class FiguredBassScaleException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------

# Helper Methods
def convertToPitch(pitchString):
    '''
    Converts a pitch string to a music21 pitch, only if necessary.
    
    >>> from music21 import *
    >>> pitchString = 'C5'
    >>> convertToPitch(pitchString)
    C5
    >>> convertToPitch(pitch.Pitch('E4')) #does nothing
    E4
    '''
    pitchValue = pitchString
    if type(pitchString) == str:
        pitchValue = pitch.Pitch(pitchString)
    return pitchValue

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

