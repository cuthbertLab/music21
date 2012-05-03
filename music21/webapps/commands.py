import unittest, doctest

import music21
import copy
from music21 import corpus
from music21 import key
from music21 import metadata
from music21.demos.theoryAnalysis import theoryAnalyzer


notes = ['c','c#','d','e-','e','f','f#','g','a-','a','b-','b']

def runPerceivedDissonanceAnalysis(scoreIn, offsetList, keyStr=None):
    '''
    Perceived Dissonances: Demo app for NEMCOG meeting, April 28 2012

    webapp for determining the accuracy of aural identification of dissonances
    the user listens to a piece of music and clicks when they think they hear a dissonance. this
    information is then passed to this method, which compares the score to the list of offsets corresponding
    to when the user clicked. Music21 then identifies the dissonant vertical slices, and outputs results as a
    dictionary including the score, colored by vertical slices of interest as below:
    
    Green: both music21 and the user identified as dissonant
    Blue: only the user identified as dissonant
    Red: only music21 identified as dissonant
    
    This example runs two analysis, the first is a comparison with the unmodified score and user's offsets, the second
    with the passing tones and neighbor tones of the score removed. Results are returned as nested dictionaries of the
    following form:
    {fullScore , nonharmonicTonesRemovedScore}
    each of which is a dictionary containing these keys:
    {'stream', 'numUserIdentified', 'numMusic21Identified', 'numBothIdentified', 'accuracy', 'romans', 'key'}


    >>> piece = corpus.parse('bwv7.7').measures(0,3)
    >>> offsetList = [1.1916666666666667,2.3641666666666667,3.6041666666666665,4.5808333333333335,\
                      6.131666666666667,8.804166666666667,10.148333333333333,11.700833333333334]
    >>> analysisDict = runPerceivedDissonanceAnalysis(piece, offsetList)
    >>> a = analysisDict['fullScore']
    >>> a['numMusic21Identified']
    7
    >>> a['numBothIdentified']
    3
    >>> a['numUserIdentified']
    8
    >>> a['romans']
    ['v43', 'iio65', 'bVIIb73']
    >>> b = analysisDict['nonharmonicTonesRemovedScore']
    >>> b['numMusic21Identified']
    5
    >>> b['numBothIdentified']
    2
    >>> b['accuracy']
    40.0 
   
    '''
    withoutNonharmonictonesScore = copy.deepcopy(scoreIn)
    theoryAnalyzer.removePassingTones(withoutNonharmonictonesScore)
    theoryAnalyzer.removeNeighborTones(withoutNonharmonictonesScore)
    withoutNonharmonictonesScore.sliceByGreatestDivisor(addTies=True, inPlace=True)
    withoutNonharmonictonesScore.stripTies(inPlace=True, matchByPitch=True, retainContainers=False)
    dissonanceAnalysisDict = {'fullScore': determineDissonantIdentificationAccuracy(scoreIn, offsetList,keyStr), \
                              'nonharmonicTonesRemovedScore':determineDissonantIdentificationAccuracy(withoutNonharmonictonesScore, offsetList,keyStr)}
    return dissonanceAnalysisDict


def _withinRange(dataList, lowLim, upperLim):
    '''helper function: returns true if there exists a number in dataList 
    for which the inequality lowLim <= number < upperLim
    
    >>> _withinRange([1,5.5,8], 2,3)
    False
    >>> _withinRange([1,5.5,8], 4,6)
    True
    '''
    dataList.sort()
    for index, offset in enumerate(dataList):
        if lowLim <= offset and offset < upperLim:
            return True
    return False

def determineDissonantIdentificationAccuracy(scoreIn, offsetList, keyStr=None):
    '''
    runs comparison on score to identify dissonances, then compares to the user's offsetList of identified
    dissonances. The score is colored according to the results, and appropriate information is returned
    as a dictionary. See runPerceivedDissonanceAnalysis for full details and an example.
    '''

    score = scoreIn.sliceByGreatestDivisor(addTies=True)
    vsList = theoryAnalyzer.getVerticalSlices(score)
    user = len(offsetList)
    music21VS = 0
    both = 0
    romanFigureList = []
    if keyStr == None:
        pieceKey = scoreIn.analyze('key')
    else:
        pieceKey = key.Key(keyStr)
    for (vsNum, vs) in enumerate(vsList):
            currentVSOffset = vs.offset(leftAlign=False)
            if vsNum + 1 == len(vsList):
                nextVSOffset = scoreIn.highestTime
            else:
                nextVSOffset = vsList[vsNum+1].offset(leftAlign=False)
            if not vs.isConsonant(): #music21 recognizes this as a dissonant vertical slice
                music21VS+=1
                if _withinRange(offsetList, currentVSOffset, nextVSOffset):
                    vs.color = '#00cc33' #the user also recognizes this as a dissonant vertical slice GREEn
                    both+=1
                    c = vs.getChord()
                    romanFigureList.append(music21.roman.romanNumeralFromChord(c, pieceKey).figure)
                else:
                    vs.color = '#cc3300'  #the user did not recognize as a dissonant vertical slice RED
            else: #music21 did not recognize this as a dissonant vertical slice
                if _withinRange(offsetList, currentVSOffset, nextVSOffset):
                    vs.color = '#0033cc' #the user recognized it as a dissonant vertical slice BLUE
    
    score.insert(metadata.Metadata())
    score.metadata.composer = scoreIn.metadata.composer
    score.metadata.movementName = scoreIn.metadata.movementName
    #score.show()
    analysisData = {'stream': score, 'numUserIdentified': user, 'numMusic21Identified':music21VS, 'numBothIdentified':both, 'accuracy': both*100.0/music21VS , 'romans': romanFigureList, 'key': pieceKey}
    return analysisData




class Test(unittest.TestCase):

    def runTest(self):
        pass




if __name__ == "__main__":

    music21.mainTest(Test)


