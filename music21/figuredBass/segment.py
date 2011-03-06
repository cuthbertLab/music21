import music21
import unittest
import copy

from music21 import note

from music21.figuredBass import rules
from music21.figuredBass import possibility
from music21.figuredBass import realizerScale
from music21.figuredBass import voice

class Segment:
    def __init__(self, fbInformation, bassNote, notation = ''):
        self.bassNote = bassNote
        self.notation = notation
        self.fbScale = fbInformation.fbScale
        self.fbVoices = fbInformation.fbVoices
        self.fbRules = fbInformation.fbRules
        self.pitchesAboveBass = self.fbScale.getPitches(self.bassNote.pitch, self.notation)
        self.pitchNamesInChord = self.fbScale.getPitchNames(self.bassNote.pitch, self.notation)

    def solve(self):
        raise SegmentException("solve() is an abstract method.")
    
class AntecedentSegment(Segment):
    def __init__(self, fbInformation, bassNote, notation = ''):
        Segment.__init__(self, fbInformation, bassNote, notation)
        self.possibilities = self.solve()
    
    def solve(self):
        # Imitates _findPossibleStartingChords from realizer
        possibilities = []
        
        bassPossibility = possibility.Possibility()
        previousVoice = self.fbVoices[0]
        bassPossibility[previousVoice.label] = self.bassNote.pitch
        possibilities.append(bassPossibility)
        
        for voiceNumber in range(1, len(self.fbVoices)):
            oldLength = len(possibilities)
            currentVoice = self.fbVoices[voiceNumber]
            
            for oldPossibIndex in range(oldLength):
                oldPossib = possibilities.pop(0)
                pitchBelow = oldPossib[previousVoice.label]
                
                validPitches = self.pitchesAboveBass
                if self.fbRules.filterPitchesByRange:
                    validPitches = currentVoice.pitchesInRange(self.pitchesAboveBass)
                
                for validPitch in validPitches:
                    if (self.fbRules.allowVoiceCrossing) or not (validPitch < pitchBelow):
                        newPossib = copy.copy(oldPossib)
                        newPossib[currentVoice.label] = validPitch
                        possibilities.append(newPossib)
                
            previousVoice = currentVoice
        
        newPossibilities = []
        for possib in possibilities:
            if possib.isCorrectlyFormed(self.pitchNamesInChord, self.fbRules):
                newPossibilities.append(possib)
            possibilities = newPossibilities
        
        return possibilities
    
class ConsequentSegment(Segment):
    def __init__(self, fbInformation, prevSegment, bassNote, notation = ''):
        Segment.__init__(self, fbInformation, bassNote, notation)
        self.prevSegment = prevSegment
        self.allMovements = {}
        self.possibilities = self.solve()
    
    def solve(self):
        # Imitates _findNextPossibilities from realizer
        prevPossibilities = self.prevSegment.possibilities
        nextPossibilities = []

        prevPossibIndex = 0
        for prevPossib in prevPossibilities:
            nextPossibSubset = self.resolvePossibility(prevPossib)
            movements = []
            for nextPossib in nextPossibSubset:
                try:
                    movements.append(nextPossibilities.index(nextPossib))
                except ValueError:
                    nextPossibilities.append(nextPossib)
                    movements.append(len(nextPossibilities) - 1)
            self.allMovements[prevPossibIndex] = movements
            prevPossibIndex += 1
        
        return nextPossibilities

    def resolvePossibility(self, prevPossib):
        nextPossibilities = []
        
        bassPossibility = possibility.Possibility()
        previousVoice = self.fbVoices[0]
        bassPossibility[previousVoice.label] = self.bassNote.pitch
        nextPossibilities.append(bassPossibility)
        
        for voiceNumber in range(1, len(self.fbVoices)):
            oldLength = len(nextPossibilities)
            currentVoice = self.fbVoices[voiceNumber]
            
            for oldPossibIndex in range(oldLength):
                oldPossib = nextPossibilities.pop(0)
                pitchBelow = oldPossib[previousVoice.label]
                
                validPitches = self.pitchesAboveBass
                if self.fbRules.filterPitchesByRange:
                    validPitches = currentVoice.pitchesInRange(self.pitchesAboveBass)
                
                for validPitch in validPitches:
                    newPossib = copy.copy(oldPossib)
                    newPossib[currentVoice.label] = validPitch
                    if (self.fbRules.allowVoiceCrossing) or not (validPitch < pitchBelow):
                        if prevPossib.hasCorrectVoiceLeading(newPossib, self.fbRules):
                            nextPossibilities.append(newPossib)
                
            previousVoice = currentVoice
        
        correctPossibilities = []
        for possib in nextPossibilities:
            if possib.isCorrectlyFormed(self.pitchNamesInChord, self.fbRules):
                correctPossibilities.append(possib)
            nextPossibilities = correctPossibilities
        
        return nextPossibilities
        

class SegmentException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Information:
    def __init__(self, fbScale, fbVoices, fbRules = rules.Rules()):
        self.fbScale = fbScale
        self.fbVoices = fbVoices
        self.fbRules = fbRules
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    v1 = voice.Voice('Bass', voice.Range('E2', 'E4'))
    v2 = voice.Voice('Tenor', voice.Range('C3', 'A4'))
    v3 = voice.Voice('Alto', voice.Range('F3', 'G5'))
    v4 = voice.Voice('Soprano', voice.Range('C4', 'A5'))
    
    voiceList = [v1, v2, v3, v4]
    voiceList.sort()
    
    fbScale = realizerScale.FiguredBassScale('C')
    
    fbInfo = Information(fbScale, voiceList)
    s1 = AntecedentSegment(fbInfo, note.Note('C3'))
    s2 = ConsequentSegment(fbInfo, s1, note.Note('D3'), '6')
    
    print len(s1.possibilities)
    for result in s1.possibilities:
       print result
    
    print s2.allMovements
    print len(s2.possibilities)
    for result in s2.possibilities:
       print result

    #music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof