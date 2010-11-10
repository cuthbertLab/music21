#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizerScale.py
# Purpose:      music21 class for conveniently representing the scale of a figured bass
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest

from music21 import note
from music21 import pitch
from music21 import key
from music21 import interval
from music21.musedata import base40

'''
Features to add:
- Increased recognition of figured bass notation
'''


inversionTable = {'-': (0,3),
                  '6': (1,3),
                  '6/4': (2,3),
                  '7': (0,4),
                  '6/5': (1,4),
                  '4/3': (2,4),
                  '4/2': (3,4)}


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


def modifyPitchNameWithAccidentalString(pitchNameToAlter, accidentalString):
    '''
    Given a pitch, and an accidental string, modify the pitch accordingly.
    Returns the modified pitch.
    
    >>> from music21 import *
    >>> modifyPitchNameWithAccidentalString('C#', 'N')
    'C'
    >>> modifyPitchNameWithAccidentalString('C-', 'N')
    'C'
    >>> modifyPitchNameWithAccidentalString('C', '#')
    'C#'
    >>> modifyPitchNameWithAccidentalString('C-', '+')
    'C'
    >>> modifyPitchNameWithAccidentalString('C', '-')
    'C-'
    
    OMIT_FROM_DOCS 
    This method has been implemented using the base40 system. The method
    will return an error in the extreme cases where base40 cannot be used.    
    '''
    pitchToAlter = convertToPitch(pitchNameToAlter)
    if pitchToAlter.accidental != None:
        if (pitchToAlter.accidental.alter >= 2.0) and ((accidentalString == "#") or (accidentalString == "+") or (accidentalString == "\\")):
            raise FiguredBassScaleException("Base40 cannot raise " + str(pitchToAlter.name) + " by a semitone")
        elif (pitchToAlter.accidental.alter <= -2.0) and (accidentalString == "-"):
            raise FiguredBassScaleException("Base40 cannot lower " + str(pitchToAlter.name) + " by a semitone")
    
    pitchToAlter.octave = pitchToAlter.implicitOctave
    
    base40ToAlter = base40.pitchToBase40(pitchToAlter)
            
    if (accidentalString == "#") or (accidentalString == "+") or (accidentalString == "\\"):
        newPitch = base40.base40ToPitch(base40ToAlter + 1)                
    elif accidentalString == "-":
        newPitch = base40.base40ToPitch(base40ToAlter - 1)        
    elif accidentalString == "N":
        basePitch = pitchToAlter
        basePitch.accidental = None
        base40RootPitch = base40.pitchToBase40(basePitch)
        if base40RootPitch > base40ToAlter:
            newPitch = base40.base40ToPitch(base40ToAlter + 1) #Raise by semitone
        elif base40RootPitch < base40ToAlter:
            newPitch = base40.base40ToPitch(base40ToAlter - 1) #Lower by semitone
    else:
        raise FiguredBassScaleException("Invalid accidental string: " + accidentalString)
    
    return newPitch.name



class FiguredBassScale:
    
    def __init__(self, scaleValue, scaleMode = 'major'):
        '''
        Constructs a FiguredBassScale object, with a scaleValue (key) and a scaleMode (major is default).
        '''
        self.__scaleValue = convertToPitch(scaleValue) #If scale value provided as string, convert to pitch
        self.__scaleMode = scaleMode
        self.__keySig = key.KeySignature(key.pitchToSharps(self.__scaleValue,self.__scaleMode))
        self.__scale = self.__constructScale()
        

    def __constructScale(self):
        '''
        Builds the list of pitch names found in the scale.
        '''
        noteList = [note.Note('A'), note.Note('B'), note.Note('C'),
                    note.Note('D'), note.Note('E'), note.Note('F'),
                    note.Note('G')]
        for i in range(len(noteList)):
            if (self.__keySig.accidentalByStep(noteList[i].step)
                    != noteList[i].accidental):
                noteList[i].accidental = \
                    self.__keySig.accidentalByStep(noteList[i].step)        
        indexStart = noteList.index(note.Note(self.__scaleValue.name))
        newNoteList = [] #List of notes in correct order
        for i in range(indexStart,indexStart+8):
            newNoteList.append(noteList[i%7].name)
        return newNoteList


    def getScaleValue(self):
        '''
        Returns the key of the scale as a pitch.
        
        >>> fbScale1 = FiguredBassScale('C')
        >>> fbScale1.getScaleValue()
        C
        >>> fbScale2 = FiguredBassScale('F', 'minor')
        >>> fbScale2.getScaleValue()
        F
        '''
        return self.__scaleValue


    def getScaleMode(self):
        '''
        Returns the mode of the scale.
        
        >>> fbScale1 = FiguredBassScale('C')
        >>> fbScale1.getScaleMode()
        'major'
        >>> fbScale2 = FiguredBassScale('F', 'minor')
        >>> fbScale2.getScaleMode()
        'minor'
        >>> fbScale3 = FiguredBassScale('G', 'mixolydian')
        >>> fbScale3.getScaleMode()
        'mixolydian'
        >>> fbScale4 = FiguredBassScale('e', 'dorian')
        >>> fbScale4.getScaleMode()
        'dorian'
        '''
        return self.__scaleMode
    
    
    def getScale(self):
        '''
        Returns a list of pitch names in the scale.
        
        >>> fbScale1 = FiguredBassScale('C')
        >>> fbScale1.getScale()
        ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C']
        >>> fbScale2 = FiguredBassScale('F')
        >>> fbScale2.getScale()
        ['F', 'G', 'A', 'B-', 'C', 'D', 'E', 'F']
        '''
        return self.__scale
    
    
    def getPitchNamesFromNotation(self, bassPitch, notation='-'):
        '''
        Given a bass pitch and its corresponding notation, returns
        a list of applicable pitch names. If there is no notation,
        that need not be explicitly indicated.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale.getPitchNamesFromNotation(pitch.Pitch('D3'), '6')
        ['D', 'F', 'B']
        >>> fbScale.getPitchNamesFromNotation('G3')
        ['G', 'B', 'D']
        >>> fbScale.getPitchNamesFromNotation('G', '7')
        ['G', 'B', 'D', 'F']
        >>> fbScale.getPitchNamesFromNotation(pitch.Pitch('D3'), '5/3#/1')
        Traceback (most recent call last):
        FiguredBassScaleException: Notation not defined yet-> 5/3#/1
        '''
        bassPitch = convertToPitch(bassPitch)
        try:
            (inversion, numNotes) = inversionTable[notation]
            return self.__getPitchNamesOnPitchInScale(bassPitch, inversion, numNotes)
        except KeyError:
            return self.__getSpecialPitchNames(bassPitch, notation)
            
            
    def __getSpecialPitchNames(self, bassPitch, notation):
        if len(notation) == 1:
            pitchNames = self.__getPitchNamesOnPitchInScale(bassPitch, 0, 3)
            thirdAboveBass = pitchNames[1] #Here we have a pitch name, but pitch is what were dealing with below?
            pitchNames[1] = modifyPitchNameWithAccidentalString(thirdAboveBass, notation)
            return pitchNames

        raise FiguredBassScaleException("Notation not defined yet-> " + notation)
    
    
        
    def getPitchNameOnScaleDegree(self, scaleDegree):
        '''
        Given a scale degree, returns a pitch name at that location.
        A valid scale degree lies between 1 and 7 inclusive.
        
        >>> fbScale = FiguredBassScale('D')
        >>> fbScale.getPitchNameOnScaleDegree(3)
        'F#'
        >>> fbScale.getPitchNameOnScaleDegree(7)
        'C#'
        >>> fbScale.getPitchNameOnScaleDegree(10)
        Traceback (most recent call last):
        FiguredBassScaleException: Scale degree out of bounds-> 10
        '''
        if scaleDegree <= 0 or scaleDegree > 7:
            raise FiguredBassScaleException("Scale degree out of bounds-> " + str(scaleDegree))

        return self.__scale[scaleDegree - 1]
    
    
    def getScaleDegree(self, pitchValue):
        '''
        Given a pitch, returns a corresponding scale degree if it's
        present in the scale. Otherwise, raises an exception.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('A', 'minor')
        >>> fbScale.getScaleDegree(pitch.Pitch('G'))
        7
        >>> fbScale.getScaleDegree(pitch.Pitch('D3'))
        4
        >>> fbScale.getScaleDegree(pitch.Pitch('G#2'))
        Traceback (most recent call last):
        FiguredBassScaleException: Pitch not in scale of A minor-> G#
        '''
        pitchValue = convertToPitch(pitchValue)
        if self.isInScale(pitchValue.name):
            return self.__scale.index(pitchValue.name) + 1
        raise FiguredBassScaleException("Pitch not in scale of " + str(self.getScaleValue()) \
                             + " " + str(self.getScaleMode()) + "-> " + str(pitchValue.name))
    
    
    def getPitchesAboveBassPitchFromNotation(self, bassPitch, notation='-', octaveLimit=7):
        '''
        Given a bass pitch and its corresponding notation, returns all the
        pitches above it, inclusive of the bass pitch, that correspond to 
        the associated pitch names.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale.getPitchesAboveBassPitchFromNotation('C3')
        [C3, C4, C5, C6, C7, E3, E4, E5, E6, E7, G3, G4, G5, G6, G7]
        >>> fbScale.getPitchesAboveBassPitchFromNotation('D3', '6')
        [D3, D4, D5, D6, D7, F3, F4, F5, F6, F7, B3, B4, B5, B6, B7]
        >>> fbScale.getPitchesAboveBassPitchFromNotation(pitch.Pitch('G3'), '7')
        [G3, G4, G5, G6, G7, B3, B4, B5, B6, B7, D4, D5, D6, D7, F4, F5, F6, F7]
        '''
        bassPitch = convertToPitch(bassPitch)
        pitchNames = self.getPitchNamesFromNotation(bassPitch, notation)
        allPitches = []
        for pitchName in pitchNames:
            for i in range(1, octaveLimit + 1):
                allPitches.append(pitch.Pitch(pitchName + str(i)))
    
        pitchesAboveNote = []
        bassPs = bassPitch.ps
        for givenPitch in allPitches:
            givenPitchPs = givenPitch.ps
            if givenPitchPs >= bassPs:
                pitchesAboveNote.append(givenPitch)
        
        return pitchesAboveNote


    def isInScale(self, pitchValue):
        '''
        Given a pitch, returns True if present in scale and
        False otherwise.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('G')
        >>> fbScale.isInScale('F')
        False
        >>> fbScale.isInScale(pitch.Pitch('A3'))
        True
        '''
        pitchValue = convertToPitch(pitchValue)
        inScale = False
        if pitchValue.name in self.__scale:
            inScale = True
        return inScale
    
    
    def __getPitchNamesOnPitchInScale(self, bassPitch, inversion=0, numNotes=3):
        '''
        OMIT_FROM_DOCS
        Given a bassPitch, an inversion, and a number of notes, find the pitch
        names which correspond to the bassPitch. Raises an exception if pitch is
        not in scale.
        
        This method is hidden from the user because since this is a figured bass
        scale class, it forces the user to retrieve pitch names indirectly using
        notation rather than directly using inversion and number of notes, where
        there is more possibility for user error.
        
        This method, however, could be made public.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('F')
        >>> fbScale._FiguredBassScale__getPitchNamesOnPitchInScale('B-', 1, 3) #Dammit python, that method was private!
        ['B-', 'D', 'G']
        >>> fbScale._FiguredBassScale__getPitchNamesOnPitchInScale('B', 1, 3)
        Traceback (most recent call last):
        FiguredBassScaleException: Pitch not in scale of F major-> B
        >>> fbScale._FiguredBassScale__getPitchNamesOnPitchInScale('C', 3, 3)
        Traceback (most recent call last):
        FiguredBassScaleException: Invalid inversion for number of notes-> 3
        '''
        pitchValue = convertToPitch(bassPitch) #Redundancy
        scaleDegree = self.getScaleDegree(bassPitch)
        if inversion >= numNotes:
            raise FiguredBassScaleException("Invalid inversion for number of notes-> " + str(inversion))
        scaleDegree -= inversion * 2
        while (scaleDegree <= 0):
            scaleDegree += 7
        currIndex = scaleDegree - 1
        pitchNames = []
        for i in range(numNotes):
            pitchNames.append(self.__scale[currIndex%7])
            currIndex += 2
        rootPitchName = pitchNames[inversion]
        while (pitchNames[0] != rootPitchName):
            tempPitchName = pitchNames.pop(0)
            pitchNames.append(tempPitchName)
        return pitchNames
                

class FiguredBassScaleException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)