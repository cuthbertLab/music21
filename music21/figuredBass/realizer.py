#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizer.py
# Purpose:      music21 class to define a figured bass line, consisting of notes
#                and figures in a given key.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project    
# License:      LGPL
#-------------------------------------------------------------------------------

import collections
import copy
import itertools
import music21
import random
import unittest
import warnings

from music21 import chord
from music21 import clef
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
from music21.figuredBass import notation
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import segment

def figuredBassFromStream(streamPart):
    '''
    Takes a :class:`~music21.stream.Part` (or another :class:`~music21.stream.Stream` subclass) 
    and returns a :class:`~music21.figuredBass.realizer.FiguredBassLine` object whose bass notes 
    have notations taken from the lyrics in the source stream. This method along with the
    :meth:`~music21.figuredBass.realizer.FiguredBassLine.realize` method provide the easiest 
    way of converting from a notated version of a figured bass (such as in a MusicXML file) to 
    a realized version of the same line.
    
    
    .. note:: This example corresponds to example 1b in "fbREALIZER: AUTOMATIC FIGURED BASS REALIZATION FOR 
    MUSIC INFORMATION RETRIEVAL IN music21," which was submitted for consideration for the 12th International 
    Society for Music Information Retrieval Conference (`ISMIR 2011 <http://ismir2011.ismir.net/>`_).
        
    >>> from music21 import tinyNotation
    >>> from music21.figuredBass import realizer
    >>> s = tinyNotation.TinyNotationStream('C4 D8_6 E8_6 F4 G4_7 c1', '4/4')
    >>> fb = realizer.figuredBassFromStream(s)
    >>> fbRules = rules.Rules()
    >>> fbRules.partMovementLimits = [(1,2),(2,12),(3,12)]
    >>> fbRealization = fb.realize(fbRules)
    >>> fbRealization.getNumSolutions()
    13
    >>> #_DOCS_SHOW fbRealization.generateRandomRealizations(8).show()
    
    .. image:: images/fbRealizer_fbStreamPart.*
        :width: 700
    '''
    sf = streamPart.flat
    sfn = sf.notes
    
    keyList = sf.getElementsByClass(key.Key)
    myKey = None
    if len(keyList) == 0:
        keyList = sf.getElementsByClass(key.KeySignature)
        if len(keyList) == 0:
            myKey = key.Key('C')
        else:
            if keyList[0].pitchAndMode[1] is None:
                mode = 'major'
            else:
                mode = keyList[0].pitchAndMode[1]
            myKey = key.Key(keyList[0].pitchAndMode[0], mode)
    else:
        myKey = keyList[0]

    tsList = sf.getElementsByClass(meter.TimeSignature)
    if len(tsList) == 0:
        ts = meter.TimeSignature('4/4')
    else:
        ts = tsList[0]
    
    fb = FiguredBassLine(myKey, ts)
    
    for n in sfn:
        if len(n.lyrics) > 0:
            annotationString = ", ".join([x.text for x in n.lyrics])
            fb.addElement(n, annotationString)
        else:
            fb.addElement(n)
    
    return fb

def figuredBassFromStreamPart(streamPart):
    '''
    Deprecated. Use :meth:`~music21.figuredBass.realizer.figuredBassFromStream` instead.
    '''
    warnings.warn("The method figuredBassFromStreamPart() is deprecated. Use figuredBassFromStream().", DeprecationWarning)
    return figuredBassFromStream(streamPart)
    
def addLyricsToBassNote(bassNote, notationString):
    '''
    Takes in a bassNote and a corresponding notationString as arguments. 
    Adds the parsed notationString as lyrics to the bassNote, which is 
    useful when displaying the figured bass in external software.
    
    >>> from music21.figuredBass import realizer
    >>> from music21 import note
    >>> n1 = note.Note('G3')
    >>> realizer.addLyricsToBassNote(n1, "6,4")
    >>> n1.lyrics[0].text
    '6'
    >>> n1.lyrics[1].text
    '4'
    >>> #_DOCS_SHOW n1.show()
    
    .. image:: images/fbRealizer_lyrics.*
        :width: 150
    '''
    bassNote.lyrics = []
    n = notation.Notation(notationString)
    if len(n.figureStrings) == 0:
        return
    maxLength = 0
    for fs in n.figureStrings:
        if len(fs) > maxLength:
            maxLength = len(fs)
    for fs in n.figureStrings:
        spacesInFront = ''
        for space in range(maxLength - len(fs)):
            spacesInFront += ' '
        bassNote.addLyric(spacesInFront + fs, applyRaw = True)

_DOC_ORDER = [figuredBassFromStream, figuredBassFromStreamPart, addLyricsToBassNote]

class FiguredBassLine(object):
    def __init__(self, inKey = key.Key('C'), inTime = meter.TimeSignature('4/4')):
        '''
        >>> from music21.figuredBass import realizer
        >>> from music21 import key
        >>> from music21 import meter
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        '''
        self.inKey = inKey
        self.inTime = inTime
        self.fbScale = realizerScale.FiguredBassScale(inKey.pitchFromDegree(1), inKey.mode)
        self.fbList = []
        self.addNotationAsLyrics = True
    
    def addElement(self, bassNote, notationString = ''):
        '''
        >>> from music21.figuredBass import realizer
        >>> from music21 import key
        >>> from music21 import meter
        >>> from music21 import note
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        >>> fbLine.addElement(note.Note('B2'))
        >>> fbLine.addElement(note.Note('C#3'), "6")
        >>> fbLine.addElement(note.Note('D#3'), "6")
        >>> fbLine.fbList
        [(<music21.note.Note B>, ''), (<music21.note.Note C#>, '6'), (<music21.note.Note D#>, '6')]
        '''
        self.fbList.append((bassNote, notationString))
        if self.addNotationAsLyrics:
            addLyricsToBassNote(bassNote, notationString)
    
    def generateBassLine(self):
        '''
        >>> from music21.figuredBass import realizer
        >>> from music21 import key
        >>> from music21 import meter
        >>> from music21 import note
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        >>> fbLine.addElement(note.Note('B2'))
        >>> fbLine.addElement(note.Note('C#3'), "6")
        >>> fbLine.addElement(note.Note('D#3'), "6")
        >>> #_DOCS_SHOW fbLine.generateBassLine().show()
        '''
        bassLine = stream.Part()
        bassLine.append(copy.deepcopy(self.inTime))
        bassLine.append(key.KeySignature(self.inKey.sharps))

        bassLine.append(clef.BassClef())
        for (bassNote, notationString) in self.fbList:
            bassLine.append(bassNote)
            
        return bassLine
    
    def realize(self, fbRules = rules.Rules(), numParts = 4, maxPitch = pitch.Pitch('B5')):
        '''
        >>> from music21.figuredBass import realizer
        >>> from music21.figuredBass import rules
        >>> from music21 import key
        >>> from music21 import meter
        >>> from music21 import note
        >>> fbLine = realizer.FiguredBassLine(key.Key('B'), meter.TimeSignature('3/4'))
        >>> fbLine.addElement(note.Note('B2'))
        >>> fbLine.addElement(note.Note('C#3'), "6")
        >>> fbLine.addElement(note.Note('D#3'), "6")
        >>> fbRules = rules.Rules()
        >>> fbLine.realize(fbRules).getNumSolutions()
        208
        >>> fbRules.forbidVoiceOverlap = False
        >>> fbLine.realize(fbRules).getNumSolutions()
        7908
        '''
        segmentList = []
        for (bassNote, notationString) in self.fbList:
            correspondingSegment = segment.Segment(bassNote, notationString, self.fbScale, fbRules, numParts, maxPitch)
            segmentList.append(correspondingSegment)

        for segmentIndex in range(len(segmentList) - 1):
            segmentA = segmentList[segmentIndex]
            segmentB = segmentList[segmentIndex + 1]
            correctAB = segmentA.allCorrectConsecutivePossibilities(segmentB)
            segmentA.movements = collections.defaultdict(list)
            listAB = list(correctAB)
            for (possibA, possibB) in listAB:
                segmentA.movements[possibA].append(possibB)

        self.trimAllMovements(segmentList)
        return Realization(segmentList, self.inKey, self.inTime)

    def generateRandomRealization(self):         
        '''
        Generates a random realization of a figured bass as a music21.stream Score, 
        with the default rules set and a soprano line limited to stepwise motion.
        
        This method exists for backwards compatibility. Instead, use the realize()
        method which returns a Resolution. Then, call generateRandomRealization() on
        the Resolution.
        '''
        warnings.warn("The method generateRandomRealization() is deprecated. Use realize() instead and call generateRandomRealization() on the result.", DeprecationWarning)
        fbRules = rules.Rules()
        fbRules.partMovementLimits = [(1,2),(2,12),(3,12)]        
        return self.realize(fbRules).generateRandomRealization()

    def showRandomRealization(self):         
        '''
        Displays a random realization of a figured bass as a musicxml in external software, 
        with the default rules set and a soprano line limited to stepwise motion.
        
        This method exists for backwards compatibility. Instead, use the realize()
        method which returns a Resolution. Then, call generateRandomRealization().show()
        on the Resolution.
        '''
        warnings.warn("The method showRandomRealization() is deprecated. Use realize() instead and call generateRandomRealization().show() on the result.", DeprecationWarning)
        fbRules = rules.Rules()
        fbRules.partMovementLimits = [(1,2),(2,12),(3,12)]
        return self.realize(fbRules).generateRandomRealization().show()
            
    def showAllRealizations(self):
        '''
        Displays all realizations of a figured bass as a musicxml in external software, 
        with the default rules set and a soprano line limited to stepwise motion.
        
        This method exists for backwards compatibility. Instead, use the realize()
        method which returns a Resolution. Then, call generateAllRealizations().show()
        on the Resolution.
        
        fbRules = rules.Rules()
        fbRules.partMovementLimits = [(1,2),(2,12),(3,12)
        '''
        warnings.warn("The method showAllRealizations() is deprecated. Use realize() instead and call generateAllRealizations().show() on the result.", DeprecationWarning)
        fbRules = rules.Rules()
        fbRules.partMovementLimits = [(1,2),(2,12),(3,12)]
        return self.realize(fbRules).generateAllRealizations().show()
    
    def trimAllMovements(self, segmentList):
        segmentList.reverse()
        for segmentIndex in range(1, len(segmentList) - 1):
            movementsAB = segmentList[segmentIndex + 1].movements
            movementsBC = segmentList[segmentIndex].movements
            eliminated = []
            for (possibB, possibCList) in movementsBC.items():
                if len(possibCList) == 0:
                    del movementsBC[possibB]
            for (possibA, possibBList) in movementsAB.items():
                movementsAB[possibA] = list(itertools.ifilter(lambda possibB: movementsBC.has_key(possibB), possibBList))
                
        for (possibA, possibBList) in movementsAB.items():
            if len(possibBList) == 0:
                del movementsAB[possibA]
                
        segmentList.reverse()
        return True

#FiguredBass = FiguredBassLine

class Realization(object):
    _DOC_ORDER = ['getNumSolutions', 'generateRandomRealization', 'generateRandomRealizations', 'generateAllRealizations',
                  'getAllPossibilityProgressions', 'getRandomPossibilityProgression', 'generateRealizationFromPossibilityProgression']
    def __init__(self, segmentList, inKey, inTime):
        '''
        Returned by :class:`~music21.figuredBass.realizer.FiguredBassLine` after calling
        :meth:`~music21.figuredBass.realizer.FiguredBassLine.realize`. Allows for the 
        retrieval of unique realizations as a :class:`~music21.stream.Score`.
        '''
        self.segmentList = segmentList
        self.inKey = inKey
        self.inTime = inTime
        self.keySig = key.KeySignature(self.inKey.sharps)
        self.keyboardStyleOutput = True

    def getNumSolutions(self):
        '''
        Returns the number of unique realizations for a Realization by calculating
        the total number of paths through a string of Segment movements. This is 
        faster and more efficient than compiling each unique realization into a 
        list, adding it to a master list, and then taking the length of the master list. 
        '''
        self.segmentList.reverse()
        pathList = {}
        for segmentIndex in range(1, len(self.segmentList)):
            segmentA = self.segmentList[segmentIndex]
            newPathList = {}
            if len(pathList.keys()) == 0:
                for possibA in segmentA.movements.keys():
                    newPathList[possibA] = len(segmentA.movements[possibA])
            else:
                for possibA in segmentA.movements.keys():
                    prevValue = 0
                    for possibB in segmentA.movements[possibA]:
                        prevValue += pathList[possibB]
                    newPathList[possibA] = prevValue
            pathList = newPathList

        numSolutions = 0
        for possibA in pathList.keys():
            numSolutions += pathList[possibA]  
        self.segmentList.reverse()
        return numSolutions
    
    def getAllPossibilityProgressions(self):
        '''
        Compiles each unique possibility progression, a valid progression through
        a string of Segment instances, adding it to a master list. Returns the 
        master list.

        
        .. warning:: This method is unoptimized, and may take a prohibitive amount
        of time for a Realization which has more than hundreds of thousands of
        unique realizations.
        '''
        currMovements = self.segmentList[0].movements
        progressions = []
        for possibA in currMovements.keys():
            possibBList = currMovements[possibA]
            for possibB in possibBList:
                progressions.append([possibA, possibB])

        for segmentIndex in range(1, len(self.segmentList)-1):
            currMovements = self.segmentList[segmentIndex].movements
            for progIndex in range(len(progressions)):
                prog = progressions.pop(0)
                possibB = prog[-1]
                for possibC in currMovements[possibB]:
                    newProg = copy.copy(prog)
                    newProg.append(possibC)
                    progressions.append(newProg)
        
        return progressions
    
    def getRandomPossibilityProgression(self):
        '''
        Returns a random unique possibility progression, a valid progression
        through a string of Segment instances.
        '''
        progression = []
        currMovements = self.segmentList[0].movements
        prevPossib = random.sample(currMovements.keys(), 1)[0]
        progression.append(prevPossib)
        
        for segmentIndex in range(0, len(self.segmentList)-1):
            currMovements = self.segmentList[segmentIndex].movements
            nextPossib = random.sample(currMovements[prevPossib], 1)[0]
            progression.append(nextPossib)
            prevPossib = nextPossib

        return progression

    def generateRealizationFromPossibilityProgression(self, possibilityProgression):
        '''
        Generates a solution as a stream.Score() given a possibility progression.        
        '''
        sol = stream.Score()
        
        bassLine = stream.Part()
        bassLine.append(copy.deepcopy(self.inTime))
        bassLine.append(copy.deepcopy(self.keySig))
        
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            sol.insert(0, rightHand)
            rightHand.append(copy.deepcopy(self.inTime))
            rightHand.append(copy.deepcopy(self.keySig))
    
            for segmentIndex in range(len(self.segmentList)):
                possibA = possibilityProgression[segmentIndex]
                bassNote = self.segmentList[segmentIndex].bassNote
                bassLine.append(copy.deepcopy(bassNote))  
                rhPitches = possibA[0:-1]                           
                rhChord = chord.Chord(rhPitches)
                rhChord.quarterLength = bassNote.quarterLength
                rightHand.append(rhChord)
            rightHand.insert(0, clef.TrebleClef()) 
        else: # Chorale-style output
            upperParts = []
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                sol.insert(0, fbPart)
                fbPart.append(copy.deepcopy(self.inTime))
                fbPart.append(copy.deepcopy(self.keySig))
                upperParts.append(fbPart)

            for segmentIndex in range(len(self.segmentList)):
                possibA = possibilityProgression[segmentIndex]
                bassNote = self.segmentList[segmentIndex].bassNote
                bassLine.append(copy.deepcopy(bassNote))  

                for partNumber in range(len(possibA) - 1):
                    n1 = note.Note(possibA[partNumber])
                    n1.quarterLength = bassNote.quarterLength
                    upperParts[partNumber].append(n1)
                    
            for upperPart in upperParts:
                upperPart.insert(0, upperPart.bestClef(True)) 
                              
        bassLine.insert(0, clef.BassClef())             
        sol.insert(0, bassLine)
        return sol

    def generateAllRealizations(self):
        '''
        Generates all realizations as a :class:`~music21.stream.Score`.
        
        
        .. warning:: This method is unoptimized, and may take a prohibitive amount
        of time for a Realization which has more than tens of unique realizations.
        '''
        allSols = stream.Score()
        bassLine = stream.Part()
        possibilityProgressions = self.getAllPossibilityProgressions()
        if len(possibilityProgressions) == 0:
            raise FiguredBassLineException("zero realizations")
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            allSols.insert(0, rightHand)
            
            for possibilityProgression in possibilityProgressions:
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                rightHand.append(copy.deepcopy(self.inTime))
                rightHand.append(copy.deepcopy(self.keySig))
                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))  
                    rhPitches = possibA[0:-1]                           
                    rhChord = chord.Chord(rhPitches)
                    rhChord.quarterLength = bassNote.quarterLength
                    rightHand.append(rhChord)
                rightHand.insert(0, clef.TrebleClef())
        else: # Chorale-style output
            upperParts = []
            possibilityProgression = self.getRandomPossibilityProgression()
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                allSols.insert(0, fbPart)
                upperParts.append(fbPart)
                
            for possibilityProgression in possibilityProgressions:
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                for upperPart in upperParts:
                    upperPart.append(copy.deepcopy(self.inTime))
                    upperPart.append(copy.deepcopy(self.keySig))

                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))
                    for partNumber in range(len(possibA) - 1):
                        n1 = note.Note(possibA[partNumber])
                        n1.quarterLength = bassNote.quarterLength
                        upperParts[partNumber].append(n1)
                        
                for upperPart in upperParts:
                    upperPart.insert(0, upperPart.bestClef(True)) 
  
        bassLine.insert(0, clef.BassClef())
        allSols.insert(0, bassLine)
        return allSols        

    def generateRandomRealization(self):
        '''
        Generates a random realization as a :class:`~music21.stream.Score`.
        '''
        return self.generateRandomRealizations(1)

    def generateRandomRealizations(self, amountToShow = 20):
        '''
        Generates *amountToShow* realizations as a :class:`~music21.stream.Score`.
        

        .. warning:: This method is unoptimized, and may take a prohibitive amount
        of time if amountToShow is in the hundreds.
        '''
        if amountToShow > self.getNumSolutions():
            return self.generateAllRealizations()
        allSols = stream.Score()
        bassLine = stream.Part()
        
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            allSols.insert(0, rightHand)
            
            for solutionCounter in range(amountToShow):
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                rightHand.append(copy.deepcopy(self.inTime))
                rightHand.append(copy.deepcopy(self.keySig))
                possibilityProgression = self.getRandomPossibilityProgression()
                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))  
                    rhPitches = possibA[0:-1]                           
                    rhChord = chord.Chord(rhPitches)
                    rhChord.quarterLength = bassNote.quarterLength
                    rightHand.append(rhChord)
                rightHand.insert(0, clef.TrebleClef()) 
        else: # Chorale-style output
            upperParts = []
            possibilityProgression = self.getRandomPossibilityProgression()
            for partNumber in range(len(possibilityProgression[0]) - 1):
                fbPart = stream.Part()
                allSols.insert(0, fbPart)
                upperParts.append(fbPart)
                
            for solutionCounter in range(amountToShow):
                bassLine.append(copy.deepcopy(self.inTime))
                bassLine.append(copy.deepcopy(self.keySig))
                for upperPart in upperParts:
                    upperPart.append(copy.deepcopy(self.inTime))
                    upperPart.append(copy.deepcopy(self.keySig))

                possibilityProgression = self.getRandomPossibilityProgression()
                for segmentIndex in range(len(self.segmentList)):
                    possibA = possibilityProgression[segmentIndex]
                    bassNote = self.segmentList[segmentIndex].bassNote
                    bassLine.append(copy.deepcopy(bassNote))
                    for partNumber in range(len(possibA) - 1):
                        n1 = note.Note(possibA[partNumber])
                        n1.quarterLength = bassNote.quarterLength
                        upperParts[partNumber].append(n1)
                        
                for upperPart in upperParts:
                    upperPart.insert(0, upperPart.bestClef(True)) 
  
        bassLine.insert(0, clef.BassClef())
        allSols.insert(0, bassLine)
        return allSols        

         
class FiguredBassLineException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof