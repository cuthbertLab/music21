# -*- coding: utf-8 -*-
'''
Python script to find out certain statistics about the trecento cadences
'''

from __future__ import unicode_literals

import unittest
from music21.alpha import trecento

def countTimeSig():
    '''
    counts how many time signatures of each type appear
    '''
    ballataObj = trecento.cadencebook.BallataSheet()

    timeSigCounter = {}
    totalPieces = 0.0

    for trecentoWork in ballataObj:
        thisTime = trecentoWork.timeSigBegin
        thisTime = thisTime.strip() # remove leading and trailing whitespace
        if (thisTime == ""): 
            pass
        else:
            totalPieces += 1
            if (thisTime in timeSigCounter):
                timeSigCounter[thisTime] += 1
            else:
                timeSigCounter[thisTime] = 1
                
    for thisKey in sorted(timeSigCounter.keys()):
        print(thisKey, ":", timeSigCounter[thisKey], str(int(timeSigCounter[thisKey]*100/totalPieces)) + "%")

def sortByPMFC(work):
    '''
    Sort a work according to which one comes first in PMFC:

    >>> from music21.alpha.trecento.runTrecentoCadence import sortByPMFC
    
    >>> class Work(object):
    ...    def __init__(self, id):
    ...        self.id = id
    ...

    >>> work1 = Work(1)
    >>> work1.pmfcVol = 5
    >>> work1.pmfcPageStart = 20
    >>> work2 = Work(2)
    >>> work2.pmfcVol = 5
    >>> work2.pmfcPageStart = 10
    >>> work3 = Work(3)
    >>> work3.pmfcVol = 2
    >>> work3.pmfcPageStart = 50
    >>> works = [work1, work2, work3]
    >>> works.sort(key=sortByPMFC)
    >>> print([w.id for w in works])
    [3, 2, 1]
    '''
    return (work.pmfcVol, work.pmfcPageStart)

def makePDFfromPieces(start = 1, finish = 2):
    '''
    make a PDF from the pieces, in order of their PMFC volumes

    >>> #_DOCS_SHOW makePDFfromPieces(200, 209)
    '''
    from music21 import stream
    ballataObj = music21.trecento.cadencebook.BallataSheet()

    retrievedPieces = []
    for i in range(start, finish):  ## some random pieces
        randomPiece = ballataObj.makeWork( i ) #
        if randomPiece.incipit is not None:
            retrievedPieces.append(randomPiece)

    opus = stream.Opus()
    retrievedPieces.sort(key=sortByPMFC)
    for randomPiece in retrievedPieces:
        #print(randomPiece.title.encode('utf-8'))
        randomOpus = randomPiece.asOpus()
        for s in randomOpus.scores:
            opus.insert(0, s)
    
    opus.show('lily.pdf')
        
## skip skipping skip incipits
#        randomIncipit = randomPiece.incipitClass()
#        lilyString += randomIncipit.lily()
#        randomCadA = randomPiece.cadenceAClass()
##        randomCadA.header = randomIncipit.header ## use its header however
#        lilyString += randomCadA.lily()
#        randomCadB1 = randomPiece.cadenceB1Class()
#        if randomCadB1 is not None:
#            lilyString += randomCadB1.lily()
#
#        randomCadB2 = randomPiece.cadenceB2Class()
#        if randomCadB2 is not None:
#            lilyString += randomCadB2.lily()

#    lS = lily.lilyString.LilyString(lilyString)
#    lS.showPDF()
#    lStr = lily.LilyString(lilyString)
#    print(lStr.encode('utf-8'))
#    lStr.writeTemp()
#    lStr.runThroughLily()

def makePDFfromPiecesWithCapua(start = 2, finish = 3):
    ballataObj = music21.trecento.cadencebook.BallataSheet()

    retrievedPieces = []
    for i in range(start, finish):  ## some random pieces
        try:
            randomPiece = ballataObj.makeWork( i ) #
            if randomPiece.incipit:
                retrievedPieces.append(randomPiece)
        except:
            raise Exception("Ugg " + str(i))
    
#    lilyString = ""
#    retrievedPieces.sort(key=sortByPMFC)
#    for randomPiece in retrievedPieces:
#        print(randomPiece.title.encode('utf-8'))
## skip skipping skip incipits
#        randomIncipit = randomPiece.incipitClass()
#        for thisStream in randomIncipit.streams:
#            capua.runRulesOnStream(thisStream)
#        lilyString += randomIncipit.lily()
#        
#        randomCadA = randomPiece.cadenceAClass()
##        randomCadA.header = randomIncipit.header ## use its header however
#        for thisStream in randomCadA.streams:
#            capua.runRulesOnStream(thisStream)
#        
#        lilyString += randomCadA.lily()
#        randomCadB1 = randomPiece.cadenceB1Class()
#        if randomCadB1 is not None:
#            for thisStream in randomCadB1.streams:
#                capua.runRulesOnStream(thisStream)
#            lilyString += randomCadB1.lily()
#
#        randomCadB2 = randomPiece.cadenceB2Class()
#        if randomCadB2 is not None:
#            for thisStream in randomCadB2.streams:
#                capua.runRulesOnStream(thisStream)
#            lilyString += randomCadB2.lily()
#
#    lS = lily.lilyString.LilyString(lilyString)
#    lS.showPDF()



def checkValidity():
    ballataObj = music21.trecento.cadencebook.BallataSheet()

    for i in range(1,378):
        randomPiece = ballataObj.makeWork(i) #random.randint(231, 312)
        try:
            incipitStreams = randomPiece.incipitStreams()
        except music21.tinyNotation.TinyNotationException as inst:
            raise Exception(randomPiece.title + " had problem " + inst.args)


# temporarily commenting out for adding standard test approach
# if (__name__ == "__main__"):
# #    countTimeSig()
#     makePDFfromPiecesWithCapua()


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testA(self):
        self.assertEqual(5,5) ## something really wrong!??

if __name__ == "__main__":    
    #makePDFfromPiecesWithCapua()
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof
