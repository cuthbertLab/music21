#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         examples.py
# Purpose:      music21 class which allows running of test cases
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import copy
import music21
import unittest

from music21 import key
from music21 import interval
from music21 import meter
from music21 import stream

from music21.figuredBass import realizer
from music21.figuredBass import rules
from music21 import tinyNotation

def exampleA():
    '''
    This was one of my (Jose Cabal-Ugaz) 21M.302 assignments.
    The figured bass was composed by Charles Shadle.

    >>> from music21.figuredBass import examples
    >>> from music21.figuredBass import rules
    >>> fbLine = examples.exampleA()
    >>> #_DOCS_SHOW fbLine.generateBassLine().show()
    >>> fbRules = rules.Rules()
    >>> fbRules.partMovementLimits = [(1,2),(2,12),(3,12)]
    >>> fbRealization1 = fbLine.realize(fbRules)
    >>> fbRealization1.getNumSolutions()
    360
    >>> #_DOCS_SHOW fbRealization1.generateRandomRealization().show()
    >>> fbRules.upperPartsMaxSemitoneSeparation = None
    >>> fbRealization2 = fbLine.realize(fbRules)
    >>> fbRealization2.keyboardStyleOutput = False
    >>> fbRealization2.getNumSolutions()
    3713168
    >>> #_DOCS_SHOW fbRealization2.generateRandomRealization().show()
    '''
    s = tinyNotation.TinyNotationStream("C2 D2_6 E2_6 F2_6 C#2_b7,5,3 D2 BB2_#6,5,3 C2_6 AA#2_7,5,#3 BB1_6,4 BB2_7,#5,#3 E1.", "3/2")
    return realizer.figuredBassFromStream(s)

def exampleB():
    '''
    Retrieved from page 114 of 'The Music Theory Handbook' by Marjorie Merryman.
    '''
    s = tinyNotation.TinyNotationStream("D4 A4_7,5,#3 B-4 F4_6 G4_6 AA4_7,5,#3 D2", "4/4")
    s.insert(0, key.Key('d'))
    return realizer.figuredBassFromStream(s)
        
def exampleC():
    '''
    Retrieved from page 114 of 'The Music Theory Handbook' by Marjorie Merryman.
    '''
    s = tinyNotation.TinyNotationStream("FF#4 GG#4_#6 AA4_6 FF#4 BB4_6,5 C#4_7,5,#3 F#2", "4/4")
    s.insert(0, key.Key('f#'))
    return realizer.figuredBassFromStream(s)

def exampleD():
    '''
    Another one of my (Jose Cabal-Ugaz) assignments from 21M.302.
    This figured bass was composed by Charles Shadle.
    
    >>> from music21.figuredBass import examples
    >>> from music21.figuredBass import rules
    >>> fbLine = examples.exampleD()
    >>> #_DOCS_SHOW fbLine.generateBassLine().show()
    >>> fbRules = rules.Rules()
    >>> fbRules.partMovementLimits = [(1,2),(2,12),(3,12)]
    >>> fbRealization1 = fbLine.realize(fbRules)
    >>> fbRealization1.getNumSolutions()
    1560
    >>> #_DOCS_SHOW fbRealization1.generateRandomRealization().show()
    >>> fbRules.forbidVoiceOverlap = False
    >>> fbRealization2 = fbLine.realize(fbRules)
    >>> fbRealization2.getNumSolutions()
    109006
    >>> #_DOCS_SHOW fbRealization2.generateRandomRealization().show()
    >>> fbRules.forbidVoiceOverlap = True
    >>> fbRules.upperPartsMaxSemitoneSeparation = 99
    >>> fbRealization3 = fbLine.realize(fbRules)
    >>> fbRealization3.getNumSolutions()
    29629539
    >>> fbRealization3.keyboardStyleOutput = False
    >>> #_DOCS_SHOW fbRealization3.generateRandomRealization().show()
    '''
    s = tinyNotation.TinyNotationStream("BB4 C#4_#6 D4_6 E2 E#4_7,5,#3 F#2_6,4 F#4_5,#3 G2 E4_6 F#2_6,4 E4_#4,2 D2_6 EE4_7,5,#3 AA2.", "3/4")
    s.insert(0, key.Key('b'))
    return realizer.figuredBassFromStream(s)

def V43ResolutionExample():
    s = tinyNotation.TinyNotationStream("D2 E2_4,3 D2 E2_4,3 F#1_6", "4/4")
    s.insert(0, key.Key('D'))
    return realizer.figuredBassFromStream(s)

def viio65ResolutionExample():
    s = tinyNotation.TinyNotationStream("D2 E2_6,b5 D2 E2_6,b5 F#1_6", "4/4")
    s.insert(0, key.Key('D'))
    return realizer.figuredBassFromStream(s)

def augmentedSixthRealizationExample():
    s = tinyNotation.TinyNotationStream("D4 BB-4_8,6,3 AA2_# D4 BB-4_8,#6,3 AA2_# D4 BB-4_#6,4,3 AA2_# D4 BB-4_#6,5,3 AA2_# D4 BB-4_#6,5,3 AA2_6,4", "4/4")
    s.insert(0, key.Key('d'))
    return realizer.figuredBassFromStream(s)
    
def twelveBarBlues():
    fb = realizer.FiguredBassLine(key.Key('B-'), meter.TimeSignature('4/4'))
    s = tinyNotation.TinyNotationStream("BB-1 E-1 BB-1 BB-1_7 E-1 E-1 BB-1 BB-1_7 F1_7 G1_6 BB-1 BB-1")
    s.insert(0, key.Key('B-'))
    return realizer.figuredBassFromStream(s)

# -----------------------------------------------------------------
# METHODS FOR GENERATION OF BLUES VAMPS
def generateBoogieVamp(sampleScore):
    '''
    Turns whole notes in bass line to blues boogie woogie bass line.
    Run this on a solution to twelveBarBlues()
    
    >>> from music21.figuredBass import examples
    >>> from music21.figuredBass import rules
    >>> bluesLine = examples.twelveBarBlues()
    >>> #_DOCS_SHOW bluesLine.generateBassLine().show()
    >>> fbRules = rules.Rules()
    >>> fbRules.partMovementLimits = [(1,4),(2,12),(3,12)]
    >>> fbRules.forbidVoiceOverlap = False
    >>> blRealization = bluesLine.realize(fbRules)
    >>> blRealization.getNumSolutions()
    2224978
    >>> sampleScore = blRealization.generateRandomRealization()
    >>> #_DOCS_SHOW examples.generateBoogieVamp(sampleScore).show()
    '''
    boogieBassLine = tinyNotation.TinyNotationStream("BB-8. D16 F8. G16 A-8. G16 F8. D16")

    newBassLine = stream.Part()
    newBassLine.append(sampleScore[1][0]) #Time signature
    newBassLine.append(sampleScore[1][1]) #Key signature

    for n in sampleScore[1].notes:
        i = interval.notesToInterval(boogieBassLine[0], n)
        tp = boogieBassLine.transpose(i)
        for lyr in n.lyrics:
            tp.notes[0].addLyric(lyr.text)
        for m in tp.notes:
            newBassLine.append(m)
    
    newScore = stream.Score()
    newScore.insert(0, sampleScore[0])
    newScore.insert(newBassLine)
    
    return newScore

def generateTripletBlues(sampleScore): #12/8
    tripletBassLine = tinyNotation.TinyNotationStream("BB-4 BB-8 D4 D8 F4 F8 A-8 G8 F8")

    newBassLine = stream.Part()
    for n in sampleScore[1].notes:
        i = interval.notesToInterval(tripletBassLine[0], n)
        tp = tripletBassLine.transpose(i)
        for lyr in n.lyrics:
            tp.notes[0].addLyric(lyr.text)
        for m in tp.notes:
            newBassLine.append(m)
    
    newTopLine = stream.Part()
    for sampleChord in sampleScore[0].notes:
        sampleChordCopy = copy.deepcopy(sampleChord)
        sampleChordCopy.quarterLength = 6.0
        newTopLine.append(sampleChordCopy)
        
    newScore = stream.Score()
    newScore.append(meter.TimeSignature("12/8")) #Time signature
    newScore.append(sampleScore[1][1]) #Key signature
    newScore.insert(0, newTopLine)
    newScore.insert(0, newBassLine)
    return newScore

def generateBluesVamp(sampleScore, topLineChordLengths = [1.0, 1.0, 1.0, 1.0]):
    newTopLine = stream.Part()
    newTopLine.append(sampleScore[0][0]) #Time signature
    newTopLine.append(sampleScore[0][1]) #Key signature
    
    for sampleChord in sampleScore[0].notes:
        for chordLength in topLineChordLengths:
            newChord = copy.deepcopy(sampleChord)
            newChord.quarterLength = chordLength
            newTopLine.append(newChord)
            
    newScore = stream.Score()
    newScore.insert(0, newTopLine)
    newScore.insert(0, sampleScore[1])

    return newScore

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof