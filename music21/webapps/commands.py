import unittest, doctest

import music21
import copy
from music21 import corpus
from music21 import key
from music21 import metadata
from music21.demos.theoryAnalysis import theoryAnalyzer


notes = ['c','c#','d','e-','e','f','f#','g','a-','a','b-','b']

#def generateIntervals(numIntervals):
#    for i in range(numIntervals):
#        startNoteIndex = random.randrange(0,len(notes))
#        interval

def userIdentified(dataList, lowLim, upperLim):
    '''return true if there exists a number in dataList for which the inequality lowLim <= number < upperLim
    
    >>> userIdentified([1,5.5,8], 2,3)
    False
    >>> userIdentified([1,5.5,8], 4,6)
    True
    '''
    dataList.sort()
    for index, offset in enumerate(dataList):
        print lowLim, offset, upperLim
        if lowLim <= offset and offset < upperLim:
            return True
    return False


def determineDissonantIdentificationAccuracy(scoreIn, offsetList, keyStr):
    score = scoreIn.sliceByGreatestDivisor(addTies=True)
    vsList = theoryAnalyzer.getVerticalSlices(score)
    user = len(offsetList)
    music21VS = 0
    both = 0
    romanFigureList = []
    pieceKey = key.Key("b")
    for (vsNum, vs) in enumerate(vsList[:-1]):
            currentVSOffset = vs.offset(leftAlign=False)
            #print currentVSOffset
            nextVSOffset = vsList[vsNum+1].offset(leftAlign=False)
            if not vs.isConsonant(): #music21 recognizes this as a dissonant vertical slice
                music21VS+=1
                if userIdentified(offsetList, currentVSOffset, nextVSOffset):
                    vs.color = '#00cc33' #the user also recognizes this as a dissonant vertical slice
                    both+=1
                    c = vs.getChord()
                    
                    romanFigureList.append(music21.roman.romanNumeralFromChord(c, pieceKey).figure)
                else:
                    vs.color = '#cc3300'  #the user did not recognize as a dissonant vertical slice
            else: #music21 did not recognize this as a dissonant vertical slice
                if userIdentified(offsetList, currentVSOffset, nextVSOffset):
                    vs.color = '#0033cc' #the user recognized it as a dissonant vertical slice
    #score.show()
    score.insert(metadata.Metadata())
    score.metadata.composer = 'Bach'
    score.metadata.movementName = 'Bach Chorale'
    
    analysisData = {'stream': score, 'numUserIdentified': user, 'numMusic21Identified':music21VS, 'numBothIdentified':both, 'accuracy': both*100.0/music21VS , 'romans': romanFigureList, 'key': key}
    return analysisData

def runPerceivedDissonanceAnalysis(scoreIn, offsetList, keyStr):
    print "RUNNING ANALYSIS"
    print offsetList
    #scoreIn = corpus.parse('bwv7.7')
    #offsetList = [i/10. for i in range(0,120,1)]
    withoutNHTScore = copy.deepcopy(scoreIn)
    theoryAnalyzer.removePassingTones(withoutNHTScore)
    theoryAnalyzer.removeNeighborTones(withoutNHTScore)
    withoutNHTScore.sliceByGreatestDivisor(addTies=True, inPlace=True)
    withoutNHTScore.stripTies(inPlace=True, matchByPitch=True, retainContainers=False)
    withoutNHTScore.analysisData['VerticalSlices'] = None
    vsList = theoryAnalyzer.getVerticalSlices(withoutNHTScore)
    dissonanceAnalysisDict = {'fullStreamData': determineDissonantIdentificationAccuracy(scoreIn, offsetList,key)}
    return dissonanceAnalysisDict

class Test(unittest.TestCase):

    def runTest(self):
        pass

class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def demo(self):  

        piece = corpus.parse('bwv7.7').measures(0,3)
        offsetList = [0.12833333333333333,0.18833333333333332,0.24833333333333332,0.30833333333333335,0.37166666666666665,0.43583333333333335,0.5,0.5716666666666667,0.6316666666666667,0.6883333333333334,0.7558333333333334,0.825,0.8758333333333334,0.94,1.005,1.0641666666666667,1.1283333333333334,1.1916666666666667,1.2558333333333331,1.3241666666666667,1.3916666666666666,1.4558333333333333,1.5241666666666667,1.5916666666666666,1.6683333333333332,1.7358333333333333,1.8041666666666667,1.8766666666666667,1.9483333333333333,2.02,2.091666666666667,2.1600000000000006,2.2283333333333335,2.2958333333333334,2.3641666666666667,2.4283333333333332,2.495833333333333,2.5683333333333334,2.64,2.7083333333333335,2.7716666666666665,2.8441666666666667,2.908333333333333,2.9725000000000006,3.04,3.111666666666667,3.1841666666666666,3.2558333333333334,3.3241666666666663,3.3958333333333335,3.464166666666667,3.535833333333333,3.6041666666666665,3.6766666666666667,3.7483333333333335,3.8241666666666663,3.8916666666666666,3.96,4.024166666666667,4.096666666666667,4.165,4.2316666666666665,4.3,4.36,4.435833333333333,4.504166666666666,4.5808333333333335,4.6483333333333325,4.711666666666667,4.7891666666666675,4.855833333333333,4.92,4.9975,5.064166666666667,5.133333333333334,5.195833333333334,5.276666666666666,5.344166666666666,5.4158333333333335,5.492499999999999,5.631666666666667,5.704166666666667,5.775833333333333,5.8516666666666675,5.92,5.991666666666666,6.055833333333333,6.131666666666667,6.2,6.284166666666667,6.3566666666666665,6.428333333333334,6.511666666666667,6.595833333333333,6.676666666666667,6.756666666666667,6.84,6.9158333333333335,7,7.068333333333333,7.151666666666666,7.224166666666667,7.315833333333333,7.404166666666667,7.484166666666667,7.555833333333333,7.635833333333333,7.708333333333333,7.7925,7.8725,7.948333333333333,8.02,8.108333333333333,8.18,8.268333333333333,8.344166666666666,8.428333333333333,8.5,8.58,8.655833333333334,8.728333333333333,8.804166666666667,8.868333333333334,8.948333333333334,9.020833333333334,9.088333333333333,9.151666666666667,9.224166666666667,9.3,9.364166666666666,9.44,9.508333333333333,9.571666666666667,9.636666666666667,9.704166666666667,9.784166666666666,9.855833333333333,9.924166666666666,10,10.0725,10.148333333333333,10.208333333333334,10.268333333333333,10.344166666666666,10.4125,10.48,10.551666666666666,10.621666666666666,10.704166666666667,10.844166666666666,10.92,11.004166666666666,11.075833333333334,11.1475,11.22,11.297499999999998,11.376666666666667,11.444166666666666,11.528333333333334,11.62,11.700833333333334,11.784166666666666,11.871666666666666,11.952500000000002,12.035833333333333,12.115833333333333,12.208333333333334,12.288333333333334,12.371666666666666,12.455833333333333,12.548333333333334,12.6275,12.704166666666667,12.7925,12.875833333333333,12.968333333333334]
        analysisResults = runPerceivedDissonanceAnalysis(piece, offsetList)
        #print analysisResults['fullStreamData']['stream'].musicxml   


if __name__ == "__main__":

    #music21.mainTest(Test)
    from music21.webapps import commands
    te = commands.TestExternal()
    te.demo()

