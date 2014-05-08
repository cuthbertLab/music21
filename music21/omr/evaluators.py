'''
@author: Maura Church, April 2014
'''

'''
This module takes two XML files and displays the number of measures that 
differ between the two before and after running the combined correction models
'''
import os

from music21.omr import correctors

#import matplotlib.pyplot as plt
#import numpy as np
#from matplotlib.ticker import MultipleLocator, FormatStrFormatter

def runMain(omrPath, groundTruthPath, originalDifferences = None, runOnePart=False):  
    # declare part number (0 indexed) if running single part
    pn = 1
      
    # get number of differences T
    omrGTP = correctors.OmrGroundTruthPair(omr=omrPath, ground=groundTruthPath)
    print "getting differences"
    if originalDifferences is None:
        numberOfDifferences = omrGTP.getDifferences()
    else:
        numberOfDifferences = originalDifferences
    print "orig diff", numberOfDifferences
    
    myOmrScore = omrGTP.omrScore
    s = myOmrScore
    print 'RUNNING HORIZONTAL MODEL'
    if runOnePart is True:
        scorePart = s.singleParts[pn]
        incorrectMeasureIndices = scorePart.getIncorrectMeasureIndices()
        print incorrectMeasureIndices
        print s.singleParts[pn].hashedNotes
        scorePart.runHorizontalCorrectionModel()    
    else:
        correctingArrayHorAllPart = []
        numberOfIncorrectMeasures = 0
        numberOfTotalMeasures = 0
        for temppn in range(len(s.singleParts)):
            scorePart = s.singleParts[temppn]
            incorrectMeasureIndices = scorePart.getIncorrectMeasureIndices()
            numberOfIncorrectMeasures += len(incorrectMeasureIndices)
            correctingArrayHorOnePart = scorePart.runHorizontalCorrectionModel()
            correctingArrayHorAllPart.append(correctingArrayHorOnePart)
            numberOfTotalMeasures += len(s.singleParts[temppn].hashedNotes)
    print "for each entry in the below array, we have [flagged measure part, flagged measure index, source measure part, source measure index, source measure probability]"
    print "HORIZONTAL CORRECTING ARRAY", correctingArrayHorAllPart
    print "**********************************"
    
    print 'RUNNING VERTICAL MODEL'
    correctingArrayVertAllPart = s.runVerticalCorrectionModel()         
    print "for each entry in the below array, we have [flagged measure part, flagged measure index, source measure part, source measure index, source measure probability]"
    print "VERTICAL CORRECTING MEASURES", correctingArrayVertAllPart
    print "**********************************"
    print 'replacing flagged measures with source measures'
    s.generateCorrectedScore(correctingArrayHorAllPart,correctingArrayVertAllPart)            
    print 'done replacing flagged measures with source measures'
     
    # get new number of differences
    newNumberOfDifferences = omrGTP.getDifferences()
    print "new difference in scores", newNumberOfDifferences
    print "number of incorrect measures", numberOfIncorrectMeasures
    print "total number of measures", numberOfTotalMeasures
  
def autoCorrelationBestMeasure(inputScore):
    '''
    Returns a tuple of the total number of NON-flagged measures and the total number
    of those measures that have a rhythmic match.
    
    Essentially it's the ratio of amount of rhythmic similarity within a piece, which
    gives an upper bound on what the omr.corrector.prior measure should be able to 
    achieve for the flagged measures. If a piece has low rhythmic similarity in general, then
    there's no way for a correct match to be found within the unflagged measures in the piece.
    
    takes in a stream.Score
    
    >>> c = converter.parse(omr.correctors.K525omrShortPath)
    >>> totalUnflagged, totalUnflaggedWithMatches = omr.evaluators.autoCorrelationBestMeasure(c)
    >>> totalUnflagged
    71
    >>> totalUnflaggedWithMatches
    55
    >>> print( float(totalUnflaggedWithMatches) / totalUnflagged )
    0.77...
    
    '''
    ss = correctors.SingleScore(inputScore)
    allHashes = ss.getAllHashes()
    
    totalMeasures = 0
    totalMatches = 0
    for pNum, pHashArray in enumerate(allHashes):
        incorrectIndices = ss.singleParts[pNum].getIncorrectMeasureIndices()
        for i, mHash in enumerate(pHashArray):
            if i in incorrectIndices:
                continue
            
            totalMeasures += 1
            match = False
            for j, nHash in enumerate(pHashArray):
                if i == j:
                    continue
                if mHash == nHash:
                    match = True
                    break
            if match is True:
                totalMatches += 1
    return (totalMeasures, totalMatches)
  
if __name__ == '__main__':
    import music21
    music21.mainTest()
    
    omrFilePath = correctors.pathName + os.sep + 'k525OMRMvt1.xml'
    groundTruthFilePath = correctors.pathName + os.sep + 'k525GTMvt1.xml'
    #omrFilePath = '/Users/cuthbert/Desktop/SchubertOMR.xml'
    #groundTruthFilePath = '/Users/cuthbert/Dropbox/Vladimir_Myke/schubert unvoll all_fixed.xml'
    
    runMain(omrFilePath,     groundTruthFilePath)



