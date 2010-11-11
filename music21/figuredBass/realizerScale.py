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
import re 
import copy

from music21 import note
from music21 import pitch
from music21 import key
from music21 import interval
from music21.musedata import base40


inversionTable = {'': '5,3',
                  '5': '5,3',
                  '6': '6,3',
                  '6,4': '6,4',
                  '7': '7,5,3',
                  '6,5': '6,5,3',
                  '4,3': '6,4,3',
                  '4,2': '6,4,2'}


class FiguredBassScale:    
    def __init__(self, scaleValue, scaleMode = 'major'):
        '''
        Constructs a FiguredBassScale object, with a scaleValue (key) and a scaleMode (major is default).
        '''
        self._scaleValue = convertToPitch(scaleValue) #If scale value provided as string, convert to pitch
        self._scaleMode = scaleMode
        self._keySig = key.KeySignature(key.pitchToSharps(self._scaleValue,self._scaleMode))
        self._scale = self._constructScale()
        
    def _constructScale(self):
        '''
        Builds the list of pitch names found in the scale.
        '''
        noteList = [note.Note('A'), note.Note('B'), note.Note('C'),
                    note.Note('D'), note.Note('E'), note.Note('F'),
                    note.Note('G')]
        for i in range(len(noteList)):
            if (self._keySig.accidentalByStep(noteList[i].step)
                    != noteList[i].accidental):
                noteList[i].accidental = \
                    self._keySig.accidentalByStep(noteList[i].step)        
        indexStart = noteList.index(note.Note(self._scaleValue.name))
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
        return self._scaleValue

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
        return self._scaleMode
    
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
        return self._scale
    
    def getPitchNamesFromNotation(self, bassPitch, notationString = ''):
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
        >>> fbScale.getPitchNamesFromNotation('F', '6-,3-')
        ['F', 'A-', 'D-']
        >>> fbScale.getPitchNamesFromNotation(pitch.Pitch('C3'), '6,4,3')
        ['C', 'E', 'F', 'A']
        >>> fbScale.getPitchNamesFromNotation(pitch.Pitch('C3'), '6,4,3-')
        ['C', 'E-', 'F', 'A']
        >>> fbScale.getPitchNamesFromNotation('C#3', '7-,5,3')
        ['C#', 'E', 'G', 'B-']
        '''
        try:
            notationToUse = inversionTable[notationString]
            return self._pitchNameRetrievalFromStandardNotation(bassPitch, notationToUse)
        except KeyError:
            notationList = parseNotationString(notationString)
            pitchNameList = None
            if len(notationList) == 1:
                (intervalAboveBass, accidentalString) = notationList[0]
                if intervalAboveBass == 3 and accidentalString != None: #Root position chord, raise 3rd above bass
                    pitchNameList = self._getPitchNamesOnPitchInScale(bassPitch, 0, 3)
                    pitchNameList[1] = modifyPitchNameWithAccidentalString(pitchNameList[1], accidentalString)
                    return pitchNameList
            
            notationToUse = notationString
            #Assumption: All shortcut notation consists of maximum two elements.
            if not len(notationList) >= 3:
                newNotation = None
                if len(notationList) == 1:
                    intervalAboveBass = notationList[0][0]
                    newNotation = str(intervalAboveBass)
                elif len(notationList) == 2:
                    intervalAboveBassA = notationList[0][0]
                    intervalAboveBassB = notationList[1][0]
                    newNotation = str(intervalAboveBassA) + ',' + str(intervalAboveBassB)
                
                try:
                    newNotation = inversionTable[newNotation]
                    newNotationList = parseNotationString(newNotation)
                    for (intervalAboveBass, accidentalString) in notationList:
                        try:
                            location = newNotationList.index(((intervalAboveBass, None)))
                            newNotationList[location] = (intervalAboveBass, accidentalString)
                        except ValueError:
                            pass
                    newNotation = ''
                    for (intervalAboveBass, accidentalString) in newNotationList:
                        expression = None
                        if accidentalString == None:
                            expression = str(intervalAboveBass)
                        else:
                            expression = str(intervalAboveBass) + accidentalString
                        newNotation += expression + ','
                    notationToUse = newNotation[0:len(newNotation) - 1]
                except KeyError:
                    pass
            
            pitchNameList = self._pitchNameRetrievalFromStandardNotation(bassPitch, notationToUse)
            return pitchNameList

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

        return self._scale[scaleDegree - 1]
    
    
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
            return self._scale.index(pitchValue.name) + 1
        raise FiguredBassScaleException("Pitch not in scale of " + str(self.getScaleValue()) \
                             + " " + str(self.getScaleMode()) + "-> " + str(pitchValue.name))
   
    def getPitchesAboveBassPitchFromNotation(self, bassPitch, notationString = '', octaveLimit = 7):
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
        pitchNames = self.getPitchNamesFromNotation(bassPitch, notationString)
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
        if pitchValue.name in self._scale:
            inScale = True
        return inScale
   
    #A few private methods which are accessed by the public methods above
    def _pitchNameRetrievalFromStandardNotation(self, bassPitch, notationString):
        '''
        Given a bass pitch and a *full* figured bass notation, return the pitch names
        which comprise that chord.
        
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale._FiguredBassScale_pitchNameRetrievalFromStandardNotation('G3', '7,5,3')
        ['G', 'B', 'D', 'F']
        >>> fbScale._FiguredBassScale_pitchNameRetrievalFromStandardNotation('B3', '6,5,3')
        ['B', 'D', 'F', 'G']
        >>> fbScale._FiguredBassScale_pitchNameRetrievalFromStandardNotation('F3', '6-,3-') #N6 Chord
        ['F', 'A-', 'D-']
        >>> fbScale._FiguredBassScale_pitchNameRetrievalFromStandardNotation('C#3', '    7-,5, 3    ')
        ['C#', 'E', 'G', 'B-']
        '''
        bassPitch = convertToPitch(bassPitch)
        pitchNameList = []
        notationList = parseNotationString(notationString)
        try:
            bassSD = self.getScaleDegree(bassPitch)
        except FiguredBassScaleException:
            bassSD = self._getPseudoScaleDegree(bassPitch)
        pitchNameList.append(bassPitch.name)
        for (intervalAboveBass, accidentalString) in notationList:
            bassIndex = bassSD - 1
            pitchIndex = (bassIndex + intervalAboveBass - 1) % 7
            pitchName = self._scale[pitchIndex]
            if (accidentalString != None):
                pitchName = modifyPitchNameWithAccidentalString(pitchName, accidentalString)
            pitchNameList.insert(1, pitchName)
        return pitchNameList

    def _getPseudoScaleDegree(self, bassPitch):
        '''
        Given a bass pitch which is not in the scale, returns what the scale degree
        would be if it were.
        
        >>> from music21 import *
        >>> fbScale = FiguredBassScale('C')
        >>> fbScale._FiguredBassScale_getPseudoScaleDegree('C#')
        1
        >>> fbScale._FiguredBassScale_getPseudoScaleDegree('E-')
        3
        >>> fbScale._FiguredBassScale_getPseudoScaleDegree('G#')
        5
        '''
        bassPitchCopy = copy.deepcopy(bassPitch)
        bassPitchCopy = convertToPitch(bassPitchCopy)
        bassNote = note.Note(bassPitchCopy)
        if (self._keySig.accidentalByStep(bassNote.step)
                    != bassNote.accidental):
                bassNote.accidental = \
                    self._keySig.accidentalByStep(bassNote.step)
        return self.getScaleDegree(bassNote.pitch)


#A few helper methods
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
    Given a pitch name and a length 1 accidental string (such as a sharp or flat), 
    modify the pitch accordingly. Returns the modified pitch name.
    
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
        if (pitchToAlter.accidental.alter >= 2.0) \
        and ((accidentalString == "#") or (accidentalString == "+") or (accidentalString == "/")):
            raise FiguredBassScaleException("Base40 cannot raise " \
                                            + str(pitchToAlter.name) + " by a semitone")
        elif (pitchToAlter.accidental.alter <= -2.0) and (accidentalString == "-"):
            raise FiguredBassScaleException("Base40 cannot lower " \
                                            + str(pitchToAlter.name) + " by a semitone")
    
    pitchToAlter.octave = pitchToAlter.implicitOctave
    try:
        base40ToAlter = base40.pitchToBase40(pitchToAlter)
    except Base40Exception:
        raise FiguredBassScaleException("Invalid pitch name-> " + str(pitchNameToAlter))    
    if (accidentalString == "#") or (accidentalString == "+") or (accidentalString == "/"):
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

def parseNotationString(notationString):
    '''
    Given a notation string, returns a list of parsed elements.
    Each element is a tuple, consisting of the interval and the
    corresponding accidental string (None if there isn't any)
    
    >>> from music21 import *
    >>> parseNotationString('6#,5,3')
    [(6, '#'), (5, None), (3, None)]
    >>> parseNotationString('6-,3-')
    [(6, '-'), (3, '-')]
    '''
    pattern = '[,]'
    notations = re.split(pattern, notationString)
    translations = []
    patternA1 = '[#-nN/][1-7]' #example: -6
    patternA2 = '[1-7][#-nN+/]' #example: 6+
    patternB = '[1-7]' #example: 6
    patternC = '[#-N+]' #example: # (which implies #3)
    intervalAboveBass = None
    accidentalString = None
    for notation in notations:
        notation = notation.strip()
        if re.match(patternA1, notation) != None:
            intervalAboveBass = int(notation[1])
            accidentalString = notation[0]
        elif re.match(patternA2, notation) != None:
            intervalAboveBass = int(notation[0])
            accidentalString = notation[1]
        elif re.match(patternB, notation) != None:
            intervalAboveBass = int(notation[0])
            accidentalString = None
        elif re.match(patternC, notation) != None:
            intervalAboveBass = 3
            accidentalString = notation[0]
        translations.append((intervalAboveBass, accidentalString))
        
    return translations


class FiguredBassScaleException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)