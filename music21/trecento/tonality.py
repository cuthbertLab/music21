'''
music21.trecento.tonality

These functions show how music21 can be used to analyze whether the idea
of tonal closure applies in the music of the Italian fourteenth century
by seeing how often the first note of the tenor (or the given voice stream
number) and the last note of that same voice are the same note.

The script also demonstrates the PNG generating abilities of the software, 
etc.

Note that when the tests are run they just check that the program does not
crash -- the numbers are not checked because the underlying data is changing
too often.
'''

import music21
import unittest
from re import match

from music21.note import Note
from music21 import interval
from music21.trecento import cadencebook
from music21 import lily
from music21.lily import lilyString
from music21.trecento import capua
from music21.trecento import polyphonicSnippet
from music21.common import defHash

ph = lambda h = {}: defHash(h, default = False)

class TonalityCounter(object):
    '''
    The TonalityCounter object takes a list of Trecento Works
    (defined in music21.trecento.cadencebook) and when run()
    is called, stores a set of information about the cadence
    tonalities of the works.

    streamNumber can be 0 (cantus), 1 (tenor, default), or 2
    (contratenor), or very rarely 3 (fourth voice).
    
    cadenceName can be "A" or "B" (which by default uses the
    second ending of cadence B if there are two endings) or
    an integer specifying which cadence to consult (-1 being
    the last one coded.  Useful for sacred music where we
    want the Amen no matter how many internal cadences there
    are).
    
    This example takes three ballata and how that all three of
    them cadence on a different note than they began on.  All
    three cadence on D despite beginning on C, A, and B (or B
    flat) repsectively.
    
    >>> from music21.trecento import cadencebook
    >>> threeBallata = cadencebook.BallataSheet()[15:18]
    >>> tc1 = TonalityCounter(threeBallata)
    >>> tc1.run() 
    >>> print tc1.output
                        Bench'amar    C    D
                    Bench'I' serva    A    D
              Checc' a tte piaccia    B    D
            A    D    1
            A diff    1
            B    D    1
            B diff    1
            C    D    1
            C diff    1
            D diff    0
            E diff    0
            F diff    0
            G diff    0
    Total Same    0 0.0%
    Total Diff    3 100.0%
    <BLANKLINE>
    '''
    
    def __init__(self, worksList, streamNumber = 1, cadenceName = "A"):
        self.worksList = worksList
        self.streamNumber = streamNumber
        self.cadenceName = cadenceName
        self.output = ""
        self.displayLily = ""
        self.storedDict = None
    
    def run(self):
        allLily = lily.LilyString()
        output = ""
        
        myDict = ph({'A': ph(), 'B': ph(), 'C': ph(), 'D': ph(), 'E': ph(), 'F': ph(), 'G': ph()})
        for thisWork in self.worksList:
            incip = thisWork.incipit
            
            if self.cadenceName == "A":
                cadence = thisWork.cadenceAClass()
            elif self.cadenceName == "B":
                cadence = thisWork.cadenceB2Class()
                if (cadence is None or cadence.streams is None or len(cadence.streams) <= self.streamNumber):
                    cadence = thisWork.cadenceB1Class()
            elif isinstance(self.cadenceName, int):
                try:
                    cadence = thisWork.snippets[self.cadenceName]
                except IndexError:
                    continue
            else:
                raise Exception("Cannot deal with cadence type %s" % self.cadenceName)
                    

            if (incip is None or incip.streams is None or len(incip.streams) <= self.streamNumber):
                continue
            if (cadence is None or cadence.streams is None or len(cadence.streams) <= self.streamNumber):
                continue

            try:           
                firstNote = incip.streams[self.streamNumber].pitches[0]                
                cadenceNote  = cadence.streams[self.streamNumber].pitches[-1]
            except IndexError:
                output += thisWork.title + "\n"
                continue
    
            myDict[firstNote.step][cadenceNote.step] += 1
            if firstNote.step == cadenceNote.step:
                allLily += incip.lily
                allLily += cadence.lily
            
            output += "%30s %4s %4s\n" % (thisWork.title[0:30], firstNote.name, cadenceNote.name)

        bigTotalSame = 0
        bigTotalDiff = 0
        for outKey in sorted(myDict.keys()):
            outKeyDiffTotal = 0
            for inKey in sorted(myDict[outKey].keys()):
                if outKey == inKey:
                    output += "**** "
                    bigTotalSame += myDict[outKey][inKey]
                else:
                    output += "     "
                    outKeyDiffTotal += myDict[outKey][inKey]
                    bigTotalDiff    += myDict[outKey][inKey] 
                output += "%4s %4s %4d\n" % (outKey, inKey, myDict[outKey][inKey])
            output += "     %4s diff %4d\n" % (outKey, outKeyDiffTotal)
        output += "Total Same %4d %3.1f%%\n" % (bigTotalSame, (bigTotalSame * 100.0)/(bigTotalSame + bigTotalDiff))
        output += "Total Diff %4d %3.1f%%\n" % (bigTotalDiff, (bigTotalDiff * 100.0)/(bigTotalSame + bigTotalDiff))
        self.storedDict = myDict
        self.displayLily = allLily
        self.output = output

def landiniTonality(show = True):
    '''
    generates information about the tonality of Landini's ballate using
    the tenor (streamNumber = 1) and the A cadence (which we would believe
    would end the piece)
    
    '''
    
    ballataObj  = cadencebook.BallataSheet()
    worksList = []
    for thisWork in ballataObj:
        if thisWork.composer == "Landini":
            worksList.append(thisWork)
    tCounter = TonalityCounter(worksList, streamNumber = 1, cadenceName = "A")
    tCounter.run()
    if show is True:
        print(tCounter.output)

def nonLandiniTonality(show = True):
    '''
    generates information about the tonality of not anonymous ballate 
    that are not by Francesco (Landini) using
    the tenor (streamNumber = 1) and the A cadence (which we would believe
    would end the piece)    
    '''

    ballataObj  = cadencebook.BallataSheet()
    worksList = []
    for thisWork in ballataObj:
        if thisWork.composer != "Landini" and thisWork.composer != ".":
            worksList.append(thisWork)
    tCounter = TonalityCounter(worksList, streamNumber = 1, cadenceName = "A")
    tCounter.run()
    if show is True:
        print(tCounter.output)

def anonBallataTonality(show = True):
    '''
    Gives a list of all anonymous ballate with their incipit tenor note and cadence tenor notes
    keeps track of how often they are the same and how often they are different.
    
    And then generates a PNG of the incipit and first cadence of all the ones that are the same.
    '''
    ballataObj  = cadencebook.BallataSheet()
    worksList = []
    for thisWork in ballataObj:
        if thisWork.composer == ".":
            worksList.append(thisWork)
    tCounter = TonalityCounter(worksList, streamNumber = 1, cadenceName = "A")
    tCounter.run()
    if show is True:
        print(tCounter.output)
        print("Generating Lilypond PNG of all pieces where the first note of the tenor is the same pitchclass as the last note of Cadence A")
        print("It might take a while, esp. on the first Lilypond run...")
        tCounter.displayLily.showPNG()

def sacredTonality(show = True):
    '''
    Gives a list of all sacred pieces by incipit tenor note and last cadence tenor note
    and then notices which are the same and which are different.

    note that we only have a very very few sacred pieces encoded at this point so
    the results are NOT statistically significant.

    And then generates a PNG of the incipit and cadence of all the ones that are the same.
    '''
    
    kyrieObj  = cadencebook.KyrieSheet()
    gloriaObj  = cadencebook.GloriaSheet()
    credoObj  = cadencebook.CredoSheet()
    sanctusObj  = cadencebook.SanctusSheet()
    agnusObj  = cadencebook.AgnusDeiSheet()
    worksList = [kyrieObj.makeWork(2),
                 gloriaObj.makeWork(2),
                 credoObj.makeWork(2),
                 sanctusObj.makeWork(2),
                 agnusObj.makeWork(2) ]

    tCounter = TonalityCounter(worksList, streamNumber = 1, cadenceName = -1)
    tCounter.run()
    if show is True:
        print(tCounter.output)
        tCounter.displayLily.showPNG()

def testAll(show = True, fast = False):
        landiniTonality(show)
        if fast is False:
            nonLandiniTonality(show)
            anonBallataTonality(show)
            sacredTonality(show)

class Test(unittest.TestCase):
    pass

    def runTest(self):
        testAll(show = False, fast = True)

class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        testAll(show = True, fast = False)
 
if __name__ == "__main__":
    music21.mainTest(Test)