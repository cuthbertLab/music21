'''Python script to find out certain statistics about the trecento cadences'''

import random
import doctest, unittest

import music21
from music21.trecento import cadencebook
from music21.trecento.cadencebook import *
from music21.tinyNotation import TinyNotationException

def test():
    countTimeSig()
    makePDFfromPieces()

def countTimeSig():
    ballataObj = BallataSheet()

    timeSigCounter = {}
    totalPieces = 0.0

    for trecentoWork in ballataObj:
        thisTime = str(trecentoWork.timeSigBegin).encode('ascii')
        thisTime = thisTime.strip() # remove leading and trailing whitespace
        if (thisTime == ""): pass
        else:
            totalPieces += 1
            if (thisTime in timeSigCounter):
                timeSigCounter[thisTime] += 1
            else:
                timeSigCounter[thisTime] = 1
                
    for thisKey in sorted(timeSigCounter.keys()):
        print(thisKey, ":", timeSigCounter[thisKey], str(int(timeSigCounter[thisKey]*100/totalPieces)) + "%")

def sortByPMFC(work1, work2):
    if work1.pmfcVol > work2.pmfcVol:
        return 1
    elif work1.pmfcVol < work2.pmfcVol:
        return -1
    else:
        if work1.pmfcPageStart > work2.pmfcPageStart:
            return 1
        elif work1.pmfcPageStart < work2.pmfcPageStart:
            return -1
        else:
            return 0        

def makePDFfromPieces(start = 1, finish = 2):
    ballataObj = BallataSheet()

    retrievedPieces = []
    for i in range(start, finish):  ## some random pieces
        try:
            randomPiece = ballataObj.makeWork( i ) #
            if randomPiece.incipitClass():
                retrievedPieces.append(randomPiece)
        except:
            raise Exception("Ugg " + str(i))

    lilyString = ""
    retrievedPieces.sort(sortByPMFC)
    for randomPiece in retrievedPieces:
        print(randomPiece.title.encode('utf-8'))
# skip skipping skip incipits
        randomIncipit = randomPiece.incipitClass()
        lilyString += randomIncipit.lily()
        randomCadA = randomPiece.cadenceAClass()
#        randomCadA.header = randomIncipit.header ## use its header however
        lilyString += randomCadA.lily()
        randomCadB1 = randomPiece.cadenceB1Class()
        if randomCadB1 is not None:
            lilyString += randomCadB1.lily()

        randomCadB2 = randomPiece.cadenceB2Class()
        if randomCadB2 is not None:
            lilyString += randomCadB2.lily()

    lS = lily.LilyString(lilyString)
    lS.showPDF()
#    lStr = lily.LilyString(lilyString)
#    print lStr.encode('utf-8')
#    lStr.writeTemp()
#    lStr.runThroughLily()

def makePDFfromPiecesWithCapua(start = 2, finish = 3):
    ballataObj = BallataSheet()

    retrievedPieces = []
    for i in range(start, finish):  ## some random pieces
        try:
            randomPiece = ballataObj.makeWork( i ) #
            if randomPiece.incipitClass():
                retrievedPieces.append(randomPiece)
        except:
            raise Exception("Ugg " + str(i))

    lilyString = ""
    retrievedPieces.sort(sortByPMFC)
    for randomPiece in retrievedPieces:
        print(randomPiece.title.encode('utf-8'))
# skip skipping skip incipits
        randomIncipit = randomPiece.incipitClass()
        for thisStream in randomIncipit.streams:
            capua.runRulesOnStream(thisStream)
        lilyString += randomIncipit.lily()
        
        randomCadA = randomPiece.cadenceAClass()
#        randomCadA.header = randomIncipit.header ## use its header however
        for thisStream in randomCadA.streams:
            capua.runRulesOnStream(thisStream)
        
        lilyString += randomCadA.lily()
        randomCadB1 = randomPiece.cadenceB1Class()
        if randomCadB1 is not None:
            for thisStream in randomCadB1.streams:
                capua.runRulesOnStream(thisStream)
            lilyString += randomCadB1.lily()

        randomCadB2 = randomPiece.cadenceB2Class()
        if randomCadB2 is not None:
            for thisStream in randomCadB2.streams:
                capua.runRulesOnStream(thisStream)
            lilyString += randomCadB2.lily()

    lS = lily.LilyString(lilyString)
    lS.showPDF()
#    lStr = lily.LilyString(lilyString)
#    print lStr.encode('utf-8')
#    lStr.writeTemp()
#    lStr.runThroughLily()



def checkValidity():
    ballataObj = BallataSheet()

    for i in range(1,378):
        randomPiece = ballataObj.makeWork(i) #random.randint(231, 312)
        try:
            incipitStreams = randomPiece.incipitStreams()
        except TinyNotationException, inst:
            raise Exception(randomPiece.title + " had problem " + inst.args)


# temporarily commenting out for adding standard test approach
# if (__name__ == "__main__"):
# #    countTimeSig()
#     makePDFfromPiecesWithCapua()


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":    
    makePDFfromPiecesWithCapua()
    #music21.mainTest(Test)


