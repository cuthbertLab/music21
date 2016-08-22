# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         tonality.py
# Purpose:      Methods for exploring tonality in the Trecento
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2007, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
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
import unittest
from collections import defaultdict

from music21.alpha.trecento import cadencebook

class TonalityCounter(object):
    '''
    The TonalityCounter object takes a list of Trecento Works
    (defined in music21.trecento.cadencebook) and when run()
    is called, stores a set of information about the cadence
    tonalities of the works.


    streamName can be "C" (cantus), "T" (tenor, default), or "Ct"
    (contratenor), or very rarely "4" (fourth voice).
    
    
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
    
    
    >>> from music21.alpha.trecento import cadencebook
    >>> threeBallata = cadencebook.BallataSheet()[15:18]
    >>> tc1 = alpha.trecento.tonality.TonalityCounter(threeBallata)
    >>> tc1.run() 
    >>> print(tc1.output)
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
    
    def __init__(self, worksList, streamName = "T", cadenceName = "A"):
        self.worksList = worksList
        self.streamName = streamName
        self.cadenceName = cadenceName
        self.output = ""
        self.displayStream = None
        self.storedDict = None
    
    def run(self):
        from music21 import stream
        output = ""
        streamName = self.streamName
        allScores = stream.Opus()
        
        myDict = {'A': defaultdict(lambda:False), 'B': defaultdict(lambda:False), 
                  'C': defaultdict(lambda:False), 'D': defaultdict(lambda:False), 
                  'E': defaultdict(lambda:False), 'F': defaultdict(lambda:False), 
                  'G': defaultdict(lambda:False)}
        for thisWork in self.worksList:
            incip = thisWork.incipit
            
            if self.cadenceName == "A":
                cadence = thisWork.cadenceA
            elif self.cadenceName == "B":
                cadence = thisWork.cadenceBclos
                try:
                    if (cadence is None or cadence.parts[streamName] is None):
                        cadence = thisWork.cadenceB
                except KeyError:
                    cadence = thisWork.cadenceB
            elif isinstance(self.cadenceName, int):
                try:
                    cadence = thisWork.snippets[self.cadenceName]
                except IndexError:
                    continue
            else:
                raise Exception("Cannot deal with cadence type %s" % self.cadenceName)
            
            if incip is None or cadence is None:
                continue
            try:
                incipSN = incip.parts[streamName]
                cadenceSN = cadence.parts[streamName]
            except KeyError:
                continue
            
            try:           
                firstNote = incipSN.pitches[0]                
                cadenceNote  = cadenceSN.pitches[-1]
            except IndexError:
                output += thisWork.title + "\n"
                continue
    
            myDict[firstNote.step][cadenceNote.step] += 1
            if firstNote.step == cadenceNote.step:
                allScores.insert(0, incip)
                allScores.insert(0, cadence)
            output += "%30s %4s %4s\n" % (thisWork.title[0:30], firstNote.name, cadenceNote.name)

        bigTotalSame = 0
        bigTotalDiff = 0
        for outKey in sorted(myDict):
            outKeyDiffTotal = 0
            for inKey in sorted(myDict[outKey]):
                if outKey == inKey:
                    output += "**** "
                    bigTotalSame += myDict[outKey][inKey]
                else:
                    output += "     "
                    outKeyDiffTotal += myDict[outKey][inKey]
                    bigTotalDiff    += myDict[outKey][inKey] 
                output += "%4s %4s %4d\n" % (outKey, inKey, myDict[outKey][inKey])
            output += "     %4s diff %4d\n" % (outKey, outKeyDiffTotal)
        output += "Total Same %4d %3.1f%%\n" % (bigTotalSame, 
            (bigTotalSame * 100.0) / (bigTotalSame + bigTotalDiff))
        output += "Total Diff %4d %3.1f%%\n" % (bigTotalDiff, 
            (bigTotalDiff * 100.0) / (bigTotalSame + bigTotalDiff))
        self.storedDict = myDict
        self.displayStream = allScores
        self.output = output

def landiniTonality(show = True):
    '''
    generates information about the tonality of Landini's ballate using
    the tenor (streamName = "T") and the A cadence (which we would believe
    would end the piece)
    
    '''
    
    ballataObj  = cadencebook.BallataSheet()
    worksList = []
    for thisWork in ballataObj:
        if thisWork.composer == "Landini":
            worksList.append(thisWork)
    tCounter = TonalityCounter(worksList, streamName = "T", cadenceName = "A")
    tCounter.run()
    if show is True:
        print(tCounter.output)

def nonLandiniTonality(show = True):
    '''
    generates information about the tonality of not anonymous ballate 
    that are not by Francesco (Landini) using
    the tenor (streamName = "T") and the A cadence (which we would believe
    would end the piece)
    
    
    >>> #_DOCS_SHOW trecento.tonality.nonLandiniTonality(show = True)
    
    
    Prints something like this::
    
    
                     Deduto sey a quel    C    F
                      A pianger l'ochi    C    D
                  Con dogliosi martire    E    D
              De[h], vogliateme oldire    C    G
                Madonna, io me ramento    C    D
                          Or tolta pur    F    A
                    I' senti' matutino    G    C
                         Ad ogne vento    C    C
                  ...
                  etc...
                  ...
                Donna, perche mi veggi    G    D
             Lasso! grav' è 'l partire    F    F
                          La vaga luce    G    F
                Lena virtù et sperança    F    D
                         Ma' ria avere    C    F
                    Non c'è rimasa fe'    G    D
                        Or sie che può    G    D
                       Perchè vendetta    F    D
                  Perch'i' non sep(p)i    G    D
                 Poc' [h]anno di mirar    F    D
                 S'amor in cor gentile    F    C
                    Se per virtù amor,    C    G
                       Sofrir m'estuet    A    C
                     Una cosa di veder    G    D
                  Vago et benigno amor    G    D
                         L'adorno viso    C    G
                       Già molte volte    G    C
                  O me! al cor dolente    D    D
                Benchè lontan mi trovi    A    D
                   Dicovi per certança    G    G
               Ferito già d'un amoroso    A    D
                      Movit' a pietade    D    D
                       Non voler donna    A    D
              Sol mi trafig(g)e 'l cor    C    C
                 Se le lagrime antique    F    F
        ****    A    A    1
                A    C    3
                A    D   15
                A diff   18
                B    F    1
                B diff    1
                C    A    1
        ****    C    C   10
                C    D    4
                C    F    2
                C    G    4
                C diff   11
                D    A    1
                D    C    6
        ****    D    D   16
                D    F    4
                D    G   10
                D diff   21
                E    C    2
                E    D    1
                E    F    1
                E diff    4
                F    A    2
                F    B    1
                F    C    3
                F    D    8
        ****    F    F   11
                F    G    4
                F diff   18
                G    A    1
                G    B    1
                G    C   12
                G    D   15
                G    E    1
                G    F    1
        ****    G    G   11
                G diff   31
        Total Same   49 32.0%
        Total Diff  104 68.0%

    
    '''

    ballataObj  = cadencebook.BallataSheet()
    worksList = []
    for thisWork in ballataObj:
        if show:
            print(thisWork.title)
        if thisWork.composer != "Landini" and thisWork.composer != ".":
            worksList.append(thisWork)
    tCounter = TonalityCounter(worksList, streamName = "T", cadenceName = "A")
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
    tCounter = TonalityCounter(worksList, streamName = "T", cadenceName = "A")
    tCounter.run()
    if show is True:
        print(tCounter.output)
        print("Generating Lilypond PNG of all pieces where the first note of " + 
              "the tenor is the same pitchclass as the last note of Cadence A")
        print("It might take a while, esp. on the first Lilypond run...")
        tCounter.displayStream.show('lily.png')

def sacredTonality(show = True):
    '''
    Gives a list of all sacred pieces by incipit tenor note and last cadence tenor note
    and then notices which are the same and which are different.


    note that we only have a very very few sacred pieces encoded at this point so
    the results are NOT statistically significant, but it's very fast for testing.

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

    tCounter = TonalityCounter(worksList, streamName = "T", cadenceName = -1)
    tCounter.run()
    if show is True:
        print(tCounter.output)
        tCounter.displayStream.show('lily.png')

def testAll(show = True, fast = False):
    sacredTonality(show)
    if fast is False:
        nonLandiniTonality(show)
        anonBallataTonality(show)
        landiniTonality(show)            

class Test(unittest.TestCase):
    pass

    def runTest(self):
        testAll(show = False, fast = True)

class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        testAll(show = True, fast = False)
 
if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #External)


#------------------------------------------------------------------------------
# eof

