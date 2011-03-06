import music21
import unittest

from music21 import pitch
from music21 import note

from music21.figuredBass import segment
from music21.figuredBass import realizerScale
from music21.figuredBass import rules
from music21.figuredBass import voice

class FiguredBass(object):
    def __init__(self, voiceList, timeSig, key, mode = 'major'):
        self.timeSig = timeSig
        self.key = key
        self.mode = mode
        self.scale = realizerScale.FiguredBassScale(key, mode)
        self.rules = rules.Rules()
        self.rules.topVoicesWithinOctave = False
        self.maxPitch = pitch.Pitch('B5')
        self.figuredBassList = []
        self.bassNotes = []
        self.fbInfo = segment.Information(self.scale, voiceList, self.rules)
        self.allSegments = []
        self.lastSegment = None
        
    def addElement(self, bassNote, notation = ''):
        self.bassNotes.append(bassNote)
        self.figuredBassList.append((bassNote, notation))

    def solve(self):
        (startBass, startNotation) = self.figuredBassList[0]
        print("Finding possible starting chords for: " + str((startBass.pitch, startNotation)))
        a1 = segment.AntecedentSegment(self.fbInfo, startBass, startNotation)
        self.allSegments.append(a1)
        self.lastSegment = a1
            
        for fbIndex in range(1, len(self.figuredBassList)):
            (nextBass, nextNotation) = self.figuredBassList[fbIndex]
            print("Finding all possibilities for: " + str((nextBass.pitch, nextNotation)))
            c1 = segment.ConsequentSegment(self.fbInfo, self.lastSegment, nextBass, nextNotation)
            self.allSegments.append(c1)
            self.lastSegment = c1
       
        print("Trimming movements...")
        self.lastSegment.trimAllMovements()
        numSolutions = self.lastSegment.getNumSolutions()
        print("Solving complete. Number of solutions: " + str(numSolutions))

    def getRandomRealizations(self):
        
        chordIndices = self.allMovements.keys()
        startIndices = self.allMovements[chordIndices[0]].keys()
        randomIndex = random.randint(0, len(startIndices) - 1)
        numberProgression = []
        prevChordIndex = startIndices[randomIndex]
        numberProgression.append(prevChordIndex)
        
        for chordIndex in chordIndices:
            nextIndices = self.allMovements[chordIndex][prevChordIndex]
            randomIndex = random.randint(0, len(nextIndices) - 1)
            nextChordIndex = nextIndices[randomIndex]
            numberProgression.append(nextChordIndex)
            prevChordIndex = nextChordIndex
        
        chordProgression = self._translateNumberProgression(numberProgression)
        return chordProgression 


        numberProgression = []
        for seg in self.allSegments:
            randomIndex = random.randint(0, len(nextIndices) - 1)
            
        
    def showRandomRealizations(self, numToShow):
        pass
    
    
class FiguredBassException(music21.Music21Exception):
    pass

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

    fb = FiguredBass(voiceList, '4/4', 'D', 'minor')
   
    n1 = note.Note('D3')
    n2 = note.Note('A3')
    n3 = note.Note('B-3')
    n4 = note.Note('F3')
    n5 = note.Note('G3')
    n6 = note.Note('A2')
    n7 = note.Note('D3')
    
    n7.quarterLength = 2.0
    
    fb.addElement(n1) #i
    fb.addElement(n2, '7,5,#3') #V7
    fb.addElement(n3) #VI
    fb.addElement(n4, '6') #i6
    fb.addElement(n5, '6') #ii6
    fb.addElement(n6, '7,5,#3') #V7
    fb.addElement(n7) #i
    
    fb.solve()
    #music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof


