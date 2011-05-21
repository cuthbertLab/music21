#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         realizer2.py
# Purpose:      music21 class which will find all valid solutions of a given figured bass
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21
import unittest
import random
import copy
import time
import datetime

from music21 import pitch
from music21 import note
from music21 import stream
from music21 import meter
from music21 import key
from music21 import chord
from music21 import bar

from music21.figuredBass import segment
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import part
from music21.figuredBass import notation

MIN_PITCH = pitch.Pitch('C1')
MAX_PITCH = pitch.Pitch('B5')

'''
The module realizer.py contains the FiguredBass class. Notes and notations 
from a figured bass are added to an instance of FiguredBass, after which 
resolve is called to find every complete resolution to the provided bass line.
'''

def figuredBassFromStream(streamPart, partList = None, takeFromNotation = False):
    '''
    Takes a music21.stream Part (or another music21.stream Stream subclass) 
    and returns a FiguredBass object whose bass notes have Notations taken 
    from the lyrics in the source stream. This method along with the solve 
    method provide the easiest way of converting from a notated version of 
    a figured bass (such as in a MusicXML file) to a realized version of the 
    same line.
    
    >>> from music21 import *
    >>> s = tinyNotation.TinyNotationStream('C4 D8_6 E8_6 F4 G4_7 c1', '4/4')
    >>> fb = figuredBass.realizer.figuredBassFromStream(s)
    >>> fb.realize()
    >>> #_DOCS_SHOW fb.showRandomRealizations(20)
    '''
    if partList is None:
        part1 = part.Part(1,2)
        part2 = part.Part(2)
        part3 = part.Part(3)
        part4 = part.Part(4)
    
        partList = [part1, part2, part3, part4]
    
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
    
    fb = FiguredBass(partList, str(ts), myKey.tonic, myKey.mode)
    fb.addNotationAsLyrics = False
    
    for n in sfn:
        if len(n.lyrics) > 0:
            annotationString = ", ".join([x.text for x in n.lyrics])
            fb.addElement(n, annotationString)
        else:
            fb.addElement(n)
    
    return fb

figuredBassFromStreamPart = figuredBassFromStream

def addLyricsToBassNote(bassNote, notationString):
    '''
    Takes in a bassNote and a corresponding notationString as arguments. 
    Adds the parsed notationString as lyrics to the bassNote, which is 
    useful when displaying the figured bass in external software.
    '''
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

class FiguredBass(object):
    def __init__(self, partList = None, timeSigString = '4/4', keyString = 'C', modeString = 'major'):
        '''
        Establishes a framework upon which to append notes by providing 
        details of the figured bass as arguments. First, one provides a 
        partList containing a list of Part instances. The next three 
        arguments are the time signature, key, and mode, all provided 
        as strings. The strings are converted to appropriate music21 
        objects before being stored.
        
        >>> from music21.figuredBass import realizer
        >>> from music21.figuredBass import part
        >>> from music21 import note
        >>> p1 = part.Part(1)
        >>> p2 = part.Part(2)
        >>> p3 = part.Part(3)
        >>> p4 = part.Part(4)
        >>> partList = [p1, p2, p3, p4]
        >>> fbLine2 = realizer.FiguredBass(partList, "3/4", "D", "major")
        
        Now that a FiguredBass object has been created, we can invoke
        other methods to append notes and figures of the corresponding 
        bass line, to realize the line, and then to generate and display
        complete realizations.
        
        >>> bassNote1 = note.Note("D3")
        >>> bassNote2 = note.Note("E3")
        >>> bassNote3 = note.Note("F#3")
        >>> fbLine2.addElement(bassNote1)        # I
        >>> fbLine2.addElement(bassNote2, "6")   # viio6
        >>> fbLine2.addElement(bassNote3, "6")   # I6
        >>> fbLine2.realize()
        >>> #_DOCS_SHOW fbLine2.timeElapsed.seconds
        >>> print "7" #_DOCS_HIDE
        7
        >>> fbLine2.getNumSolutions()
        171
        >>> #_DOCS_SHOW fbLine2.showRandomRealizations(10)
        >>> #_DOCS_SHOW fbLine2.showRandomRealization()
        '''
        if partList is None:
            part1 = part.Part(1,2)
            part2 = part.Part(2)
            part3 = part.Part(3)
            part4 = part.Part(4)

            partList = [part1, part2, part3, part4]

        self.keyString = keyString
        self.modeString = modeString
        self.timeSigString = timeSigString
        #Converted to music21 TimeSignature, KeySignature objects
        self.ts = meter.TimeSignature(self.timeSigString)
        _numSharps = key.pitchToSharps(self.keyString, self.modeString)
        self.ks = key.KeySignature(_numSharps)
        
        #fb bass notes, figures, bass line, other information
        self.figuredBassList = []
        self.bassNotes = []
        self.bassLine = stream.Part()
        self.bassLine.append(copy.deepcopy(self.ts))
        self.bassLine.append(copy.deepcopy(self.ks))
        self.maxPitch = MAX_PITCH
        self.fbScale = realizerScale.FiguredBassScale(keyString, modeString)
        partList.sort()
        self.fbParts = partList
        self.fbRules = rules.Rules()
        self.addNotationAsLyrics = True
        
        #Contains fb solutions
        self.isRealized = False
        self.keyboardStyleOutput = True
        
    def addElement(self, bassNote, notationString = ''):
        '''
        Takes as arguments a bassNote and a corresponding notationString. 
        It adds the elements as a tuple to a figuredBassList. Also, calls 
        addLyricsToBassNote. If no notationString is provided, the default 
        is an empty string. ("5, 3")
        '''
        if self.addNotationAsLyrics:
            addLyricsToBassNote(bassNote, notationString)
        self.bassNotes.append(bassNote)
        self.bassLine.append(bassNote)
        self.figuredBassList.append((bassNote, notationString))

    def realize(self):
        '''
        Initializes the realization of the inputted bassNote and notationString pairs. 
        Realization happens in the order in which each pair was provided. A StartSegment 
        is created for the first bassNote, and a MiddleSegment for each subsequent bassNote. 
        Then, trimAllMovements is called on the last MiddleSegment. If successful, an 
        isRealized flag is set to True.
        '''
        startTime = time.clock()
        self.isRealized = False
        self.allSegments = []
        self.lastSegment = None
        
        (startBass, startNotationString) = self.figuredBassList[0]
        a1 = segment.StartSegment(self.fbScale, self.fbParts, self.fbRules, startBass, startNotationString)
        self.allSegments.append(a1)
        self.lastSegment = a1
            
        for fbIndex in range(1, len(self.figuredBassList)):
            (nextBass, nextNotationString) = self.figuredBassList[fbIndex]
            c1 = segment.MiddleSegment(self.fbScale, self.fbParts, self.fbRules, self.lastSegment, nextBass, nextNotationString)
            self.allSegments.append(c1)
            self.lastSegment = c1
       
        self.lastSegment.trimAllMovements()
        self.isRealized = True
        endTime = time.clock()
        self.timeElapsed = datetime.timedelta(seconds = endTime - startTime)

    def getNumSolutions(self):
        return self.lastSegment.getNumSolutions()
        
    # METHODS FOR GENERATION OF INDEX PROGRESSIONS
    # --------------------------------------------
    '''
    There are methods used to retrieve index progressions. An index progression 
    is a list which represents a valid progression through a sequence of Segment 
    instances, with an index in the list representing the location of a Possibility 
    within a corresponding Segment's possibilities. Derived by iteration through 
    each Segment's nextMovements.
    '''
    def getAllIndexProgressions(self):
        '''
        Returns all the valid index progressions.
        '''
        if len(self.allSegments) <= 1:
            raise FiguredBassException("One segment or less not enough for progression generator..")
        currMovements = self.allSegments[0].nextMovements
        progressions = []
        for prevIndex in currMovements.keys():
            allNextIndices = currMovements[prevIndex]
            for nextIndex in allNextIndices:
                progressions.append([prevIndex, nextIndex])

        for mSegmentIndex in range(1, len(self.allSegments)-1):
            currMovements = self.allSegments[mSegmentIndex].nextMovements
            progLength = len(progressions)
            for progIndex in range(progLength):
                prog = progressions.pop(0)
                prevIndex = prog[-1]
                for nextIndex in currMovements[prevIndex]:
                    newProg = copy.copy(prog)
                    newProg.append(nextIndex)
                    progressions.append(newProg)
        
        return progressions
    
    def getRandomIndexProgression(self):
        '''
        Returns a random valid index progression.
        '''
        if len(self.allSegments) <= 1:
            raise FiguredBassException("One segment or less not enough for progression generator.")
        indexProgression = []
        currMovements = self.allSegments[0].nextMovements
        prevChordIndex = random.sample(currMovements.keys(), 1)[0]
        indexProgression.append(prevChordIndex)

        for mSegmentIndex in range(0, len(self.allSegments)-1):
            currMovements = self.allSegments[mSegmentIndex].nextMovements
            nextChordIndex = random.sample(currMovements[prevChordIndex], 1)[0]
            indexProgression.append(nextChordIndex)
            prevChordIndex = nextChordIndex

        return indexProgression
        
    # METHODS FOR GENERATION OF POSSIBILITY PROGRESSIONS
    # --------------------------------------------------
    '''
    There are subsequent methods for retrieving Possibility progressions. 
    A Possibility progression is a translation of an index progression 
    derived by correlating indices with the appropriate Segment's possibilities.
    '''
    def indexToPossibilityProgression(self, indexProgression):
        '''
        Takes as input a valid index progression and returns a valid Possibility progression.
        '''
        possibilityProgression = []
        
        for segmentIndex in range(len(self.allSegments)):
            elementIndex = indexProgression[segmentIndex]
            possibilityProgression.append(self.allSegments[segmentIndex].possibilities[elementIndex])
            
        return possibilityProgression
   
    def getAllPossibilityProgressions(self):
        '''
        Returns all the valid Possibility progressions.
        '''
        possibilityProgressions = []
        indexProgressions = self.getAllIndexProgressions()

        for indexProgression in indexProgressions:
            possibilityProgression = self.indexToPossibilityProgression(indexProgression)
            possibilityProgressions.append(possibilityProgression)
        
        return possibilityProgressions
    
    def getRandomPossibilityProgression(self):
        '''
        Returns a random valid Possibility progression.
        '''
        indexProgression = self.getRandomIndexProgression()
        possibilityProgression = self.indexToPossibilityProgression(indexProgression)
        return possibilityProgression

    # METHODS FOR MUSIC21.STREAM SCORE GENERATION FROM POSSILITY PROGRESSIONS
    # -----------------------------------------------------------------------
    '''
    The last of the methods compile the results for easy display to the user. 
    A solution is defined as a valid Possibility progression translated to a 
    music21.stream Score with two staves. The bottom staff contains the bass line, 
    while the top staff contains pitches of the upper parts as a music21.chord Chord. 
    There are methods for generation of solutions. Corresponding methods for display 
    call show on the results, which are then displayed in default external software, 
    such as MuseScore or Finale.
    '''
    def generateRealizationFromPossibilityProgression(self, possibilityProgression):
        '''
        Generates a solution as a stream.Score() given a chord progression
        
        bass line is taken from the figured bass object, but is checked against
        the Possibility progression for consistency.
        '''
        sol = stream.Score()
        
        if self.keyboardStyleOutput:
            rightHand = stream.Part()
            rightHand.append(copy.deepcopy(self.ts))
            rightHand.append(copy.deepcopy(self.ks))
    
            v0 = self.fbParts[0]
            
            for j in range(len(possibilityProgression)):
                givenPossib = possibilityProgression[j]
                bassNote = self.bassNotes[j]
    
                if givenPossib[v0] != bassNote.pitch:
                    raise FiguredBassException("Chord progression possibility doesn't match up with bass line.")
            
                rhPitches = []
                for k in range(1, len(self.fbParts)):
                    v1 = self.fbParts[k]
                    rhPitches.append(copy.copy(givenPossib[v1]))
                                 
                rhChord = chord.Chord(rhPitches)
                rhChord.quarterLength = bassNote.quarterLength
                rightHand.append(rhChord)
        
            sol.insert(0, rightHand)
        else: # Chorale-style output
            streamParts = []
            for k in range(len(self.fbParts) - 1):
                givenPart = stream.Part()
                givenPart.append(copy.deepcopy(self.ts))
                givenPart.append(copy.deepcopy(self.ks))
                streamParts.append(givenPart)
            
            p0 = self.fbParts[0]
            
            for j in range(len(possibilityProgression)):
                givenPossib = possibilityProgression[j]
                bassNote = self.bassNotes[j]
    
                if givenPossib[p0] != bassNote.pitch:
                    raise FiguredBassException("Chord progression possibility doesn't match up with bass line.")
            
                for k in range(1, len(self.fbParts)):
                    p1 = self.fbParts[k]
                    n1 = note.Note(givenPossib[p1])
                    n1.quarterLength = bassNote.quarterLength
                    streamParts[k-1].append(n1)
            
            streamParts.reverse()                 
            for k in range(len(self.fbParts) - 1):
                sol.insert(0, streamParts[k])
            
        sol.insert(0, copy.deepcopy(self.bassLine)) #Need to deepcopy the bass line every time, otherwise things get screwed up in display of solutions.
        return sol

    def generateAllRealizations(self):
        if self.isRealized is False:
            self.realize()
        
        allSols = stream.Score()
        if self.keyboardStyleOutput:
            part1 = stream.Part()
            part2 = stream.Part()
            allSols.insert(0, part1)
            allSols.insert(0, part2)
            possibilityProgressions = self.getAllPossibilityProgressions()
            for possibilityProgression in possibilityProgressions:
                sol = self.generateRealizationFromPossibilityProgression(possibilityProgression)
                for m in sol.parts[0]:
                    part1.append(m)
                for m in sol.parts[1]:
                    part2.append(m)
        else: # Chorale-style output
            streamParts = []
            for k in range(len(self.fbParts)):
                givenPart = stream.Part()
                allSols.insert(0, givenPart)
                streamParts.append(givenPart)
            
            possibilityProgressions = self.getAllPossibilityProgressions()
            for possibilityProgression in possibilityProgressions:
                sol = self.generateRealizationFromPossibilityProgression(possibilityProgression)
                for k in range(len(self.fbParts)):
                    streamParts[k].append(sol.parts[k].bestClef(True))
                    for m in sol.parts[k]:
                        streamParts[k].append(m)
                
        return allSols

    def generateRandomRealization(self):
        '''
        Generates a random solution as a stream.Score()
        '''
        if self.isRealized is False:
            self.realize()
        
        possibilityProgression = self.getRandomPossibilityProgression()
        return self.generateRealizationFromPossibilityProgression(possibilityProgression)
      
    def generateRandomRealizations(self, amountToShow = 20):
        if self.isRealized is False:
            self.realize()

        if amountToShow > self.lastSegment.getNumSolutions():
            return self.generateAllRealizations()
        allSols = stream.Score()
        if self.keyboardStyleOutput:
            part1 = stream.Part()
            part2 = stream.Part()
            allSols.insert(0, part1)
            allSols.insert(0, part2)
            for solutionCounter in range(amountToShow):
                sol = self.generateRandomRealization()
                for m in sol.parts[0]:
                    part1.append(m)
                for m in sol.parts[1]:
                    part2.append(m)
        else: # Chorale-style output
            streamParts = []
            for k in range(len(self.fbParts)):
                givenPart = stream.Part()
                allSols.insert(0, givenPart)
                streamParts.append(givenPart)

            for solutionCounter in range(amountToShow):
                sol = self.generateRandomRealization()
                for k in range(len(self.fbParts)):
                    streamParts[k].append(sol.parts[k].bestClef(True))
                    for m in sol.parts[k]:
                        streamParts[k].append(m)

        return allSols
    
    # METHODS FOR DISPLAY OF MUSIC21.STREAM SCORE GENERATION FROM POSSIBILITY PROGRESSIONS
    # ------------------------------------------------------------------------------------
    def showRandomRealization(self):
        self.generateRandomRealization().show()    
      
    def showAllRealizations(self, showAsText = False):
        if showAsText:
            self.generateAllRealizations().show('text')
        else:
            self.generateAllRealizations().show()
        
    def showRandomRealizations(self, amountToShow = 20, showAsText = False):
        if showAsText:        
            self.generateRandomRealizations(amountToShow).show('text')
        else:
            self.generateRandomRealizations(amountToShow).show()

    # METHOD FOR CONSOLE PRINTING OF POSSIBILITY PROGRESSION
    # ------------------------------------------------------
    def printpossibilityProgression(self, possibilityProgression):
        '''
        Takes in a Possibility progression as an argument and prints 
        it to the console. It is useful for debugging.
        '''
        linesToPrint = []
        for p in self.partList:
            partLine = p.label + ":\n"
            for possib in possibilityProgression:
                partLine += str(possib[p.label]) + "\t"
            linesToPrint.append(partLine)
        linesToPrint.reverse()
        for partLine in linesToPrint:
            print partLine
        
class FiguredBassException(music21.Music21Exception):
    pass

#------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


