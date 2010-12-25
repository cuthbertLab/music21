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

scaleTypes = {'major' : scale.MajorScale,
              'minor' : scale.MinorScale,
              'dorian' : scale.DorianScale,
              'phrygian' : scale.PhrygianScale,
              'hypophrygian' : scale.HypophrygianScale}

MAX_PITCH = pitch.Pitch('B7')

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
        >>> fbScale.getPitchNames('B3', '6,5')
        ['B', 'D', 'F', 'G']
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
        print pitchNames
        return pitchNames
 
    def getPitches(self, bassPitch, notationString = '', maxPitch=MAX_PITCH):
        '''
        Given a bass pitch and a corresponding notation string,
        returns a list of corresponding pitches, located at the
        specified intervals above the bassPitch according to said
        notation.

        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale.getPitches('C3') #Root position triad
        [C3, C4, C5, C6, C7, E3, E4, E5, E6, E7, G3, G4, G5, G6, G7]
        >>> fbScale.getPitches('D3', '6') #First inversion triad
        [D3, D4, D5, D6, D7, F3, F4, F5, F6, F7, B3, B4, B5, B6, B7]
        >>> fbScale.getPitches(pitch.Pitch('G3'), '7', 'F5') #Root position seventh chord
        [G3, G4, B3, B4, D4, D5, F4, F5]
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
        bassPs = bassPitch.ps
        maxPs = maxPitch.ps
        for givenPitch in allPitches:
            givenPitchPs = givenPitch.ps
            if givenPitchPs >= bassPs and givenPitchPs <= maxPs:
                pitchesAboveNote.append(givenPitch)
        
        return pitchesAboveNote
    
    
class FiguredBassScaleException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------

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

