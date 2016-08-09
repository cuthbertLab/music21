# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         omr/evaluators.py
# Purpose:      music21 module for evaluating correcting of output from OMR software
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014 Maura Church, Michael Scott Cuthbert, and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module takes two XML files and displays the number of measures that 
differ between the two before and after running the combined correction models
'''

from music21.omr import correctors
from music21 import converter

#import matplotlib.pyplot as plt
#import numpy as np
#from matplotlib.ticker import MultipleLocator, FormatStrFormatter

#import difflib

globalDebug = False

class OmrGroundTruthPair(object):
    '''
    Object for making comparisons between an OMR score and the GroundTruth
    
    Takes in a path to the OMR and a path to the groundTruth 
    (or a pair of music21.stream.Score objects).
    
    See below for examples.

    '''
    def __init__(self, omr=None, ground=None):
        self._overriddenDebug = None
        self.numberOfDifferences = None
        if hasattr(omr, 'filePath'):        
            self.omrPath = omr.filePath
            self.omrM21Score = omr
        else:
            self.omrPath = omr
            self.omrM21Score = None
            
        self.omrScore = self.getOmrScore()
            
        if hasattr(ground, 'filePath'):
            self.groundPath = ground.filePath
            self.groundM21Score = ground
        else:
            self.groundPath = ground
            self.groundM21Score = None
            
        self.groundScore = self.getGroundScore()
    
    @property
    def debug(self):
        if self._overriddenDebug is None:
            return globalDebug
        else:
            return self._overriddenDebug
        
    @debug.setter
    def debug(self, newDebug):
        self._overriddenDebug = newDebug
    
    def parseAll(self):
        '''
        Parse both scores.        
        '''
        self.omrScore = self.getOmrScore()
        self.groundScore = self.getGroundScore()
    
    def hashAll(self):
        '''
        store the Hashes for both scores.
        '''
        self.omrScore.getAllHashes()
        self.groundScore.getAllHashes()
    
    def getOmrScore(self):
        '''
        Returns a ScoreCorrector object of the OMR score. does NOT store it anywhere...
        
         >>> omrPath = omr.correctors.K525omrShortPath
         >>> ground = omr.correctors.K525groundTruthShortPath
         >>> omrGTP = omr.evaluators.OmrGroundTruthPair(omr=omrPath, ground=ground)
         >>> ssOMR = omrGTP.getOmrScore()
         >>> ssOMR
         <music21.omr.correctors.ScoreCorrector object at 0x...>
        '''
        if (self.debug is True):
            print('parsing OMR score')
            
        if (self.omrM21Score is None):
            self.omrM21Score = converter.parse(self.omrPath)

        return correctors.ScoreCorrector(self.omrM21Score)

    def getGroundScore(self):
        '''
        Returns a ScoreCorrector object of the Ground truth score
        
         >>> omrPath = omr.correctors.K525omrShortPath
         >>> ground = omr.correctors.K525groundTruthShortPath
         >>> omrGTP = omr.evaluators.OmrGroundTruthPair(omr=omrPath, ground=ground)
         >>> ssGT = omrGTP.getGroundScore()
         >>> ssGT
         <music21.omr.correctors.ScoreCorrector object at 0x...>
        '''
        if self.debug is True:
            print('parsing Ground Truth score')
        
        if (self.groundM21Score is None):
            self.groundM21Score = converter.parse(self.groundPath)
        
        return correctors.ScoreCorrector(self.groundM21Score)
#     
#        UNUSED
#     def getDifferencesBetweenAlignedScores(self):
#         '''
#         Returns the number of differences (int) between
#         two scores with aligned indices
#         '''
#         self.numberOfDifferences = 0        
#         aList = self.omrScore.getAllHashes()
#         bList = self.groundScore.getAllHashes()
#         for i in range(len(aList)):
#             for j in range(min(len(aList[i]), len(bList[i]))):
#                 a = aList[i][j]
#                 b = bList[i][j]
#                 s = difflib.SequenceMatcher(None, a, b) 
#                 ratio = s.ratio()
#                 measureErrors = (1-ratio) * len(a)
#                 self.numberOfDifferences += measureErrors
#         return self.numberOfDifferences
    
    def substCost(self, x, y):
        '''
        define the substitution cost for x and y (2 if x and y are unequal else 0)
        '''
        if x == y: 
            return 0
        else: 
            return 2
        
    def insertCost(self, x):
        '''
        define the insert cost for x and y (1)
        '''
        return 1
    
    def deleteCost(self, x):
        '''
        define the delete cost for x and y (1)
        '''
        return 1

    def minEditDist(self, target, source):
        '''
        Computes the min edit distance from target to source. Figure 3.25 
        '''
        n = len(target)
        m = len(source)
    
        distance = [[0 for i in range(m+1)] for j in range(n+1)]
    
        for i in range(1,n+1):
            distance[i][0] = distance[i-1][0] + self.insertCost(target[i-1])
    
        for j in range(1,m+1):
            distance[0][j] = distance[0][j-1] + self.deleteCost(source[j-1])
    
        for i in range(1,n+1):
            for j in range(1,m+1):
                distance[i][j] = min(distance[i-1][j] + 1,
                                     distance[i][j-1] + 1,
                                     distance[i-1][j-1] + self.substCost(source[j-1],target[i-1]))
        return distance[n][m]
    
    def getDifferences(self):
        '''
        Returns the total edit distance as an Int between
        the two scores
        
        This function is based on the James H. Martin's minimum edit distance,
        http://www.cs.colorado.edu/~martin/csci5832/edit-dist-blurb.html
        
        >>> omrPath = omr.correctors.K525omrShortPath
        >>> ground = omr.correctors.K525groundTruthShortPath
        >>> omrGTP = omr.evaluators.OmrGroundTruthPair(omr=omrPath, ground=ground)
        >>> differences = omrGTP.getDifferences()
        >>> differences
        32
        '''
        self.numberOfDifferences = 0        
        omrList = self.omrScore.getAllHashes()
        gtList = self.groundScore.getAllHashes()
        for partNum in range(len(omrList)):
            omrPart = omrList[partNum]
            gtPart = gtList[partNum]
            measureErrors = self.minEditDist(omrPart, gtPart)
            self.numberOfDifferences += measureErrors
        return self.numberOfDifferences


def evaluateCorrectingModel(omrPath, groundTruthPath, debug=None, 
                            originalDifferences=None, runOnePart=False):
    '''
    Get a dictionary showing the efficacy of the omr.correctors.ScoreCorrector on an OMR Score
    by comparing it to the GroundTruth.
    
    Set debug to True to see a lot of intermediary steps.
    
    >>> omrFilePath = omr.correctors.K525omrShortPath
    >>> groundTruthFilePath = omr.correctors.K525groundTruthShortPath
    >>> returnDict = omr.evaluators.evaluateCorrectingModel(omrFilePath, groundTruthFilePath)
    >>> for name in sorted(list(returnDict.keys())):
    ...     (name, returnDict[name])
    ('newEditDistance', 20)
    ('numberOfFlaggedMeasures', 13)
    ('originalEditDistance', 32)
    ('totalNumberOfMeasures', 84)
    '''
    if debug is None:
        debug = globalDebug
    # declare part number (0 indexed) if running single part
    pn = 1
      
    # get number of differences T
    omrGTP = OmrGroundTruthPair(omr=omrPath, ground=groundTruthPath)
    if debug:
        print("getting differences")
    if originalDifferences is None:
        numberOfDifferences = omrGTP.getDifferences()
    else:
        numberOfDifferences = originalDifferences
    if debug:
        print("Original edit distance", numberOfDifferences)
    
    myOmrScore = omrGTP.omrScore
    s = myOmrScore
    if debug:
        print('Running Horizontal Model (Prior-based-on-distance)')
        
    if runOnePart is True:
        scorePart = s.singleParts[pn]
        incorrectMeasureIndices = scorePart.getIncorrectMeasureIndices()
        if debug:
            print("Incorrect measure indices:", incorrectMeasureIndices)
            print("Hashed notes:", s.singleParts[pn].hashedNotes)
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
    if debug:
        print("for each entry in the array below, we have ")
        print("[flagged measure part, flagged measure index, source measure part, " + 
              "source measure index, source measure probability]")
        print("HORIZONTAL CORRECTING ARRAY", correctingArrayHorAllPart)
        print("**********************************")
        
        print('Running Vertical Model (Prior-based-on-Parts)')
        
    correctingArrayVertAllPart = s.runVerticalCorrectionModel()         
    
    if debug:
        print("for each entry in the array below, we have ")
        print("[flagged measure part, flagged measure index, source measure part," + 
              " source measure index, source measure probability]")
        print("VERTICAL CORRECTING MEASURES", correctingArrayVertAllPart)
        print("**********************************")

        print('Finding best from Horizontal and Vertical and replacing flagged ' + 
              'measures with source measures')
    priorScore = s.generateCorrectedScore(correctingArrayHorAllPart, correctingArrayVertAllPart)            

    if debug:
        print('done replacing flagged measures with source measures')
        print(priorScore)
    # get new number of differences
    newNumberOfDifferences = omrGTP.getDifferences()
    
    if debug:
        print("new edit distance", newNumberOfDifferences)
        print("number of flagged measures originally", numberOfIncorrectMeasures)
        print("total number of measures", numberOfTotalMeasures)
        s.score.show()
    
    returnDict = {}
    returnDict['originalEditDistance'] = numberOfDifferences
    returnDict['newEditDistance'] = newNumberOfDifferences
    returnDict['numberOfFlaggedMeasures'] = numberOfIncorrectMeasures
    returnDict['totalNumberOfMeasures'] = numberOfTotalMeasures

    return returnDict
  
def autoCorrelationBestMeasure(inputScore):
    '''
    Essentially it's the ratio of amount of rhythmic similarity within a piece, which
    gives an upper bound on what the omr.corrector.prior measure should be able to 
    achieve for the flagged measures. If a piece has low rhythmic similarity in general, then
    there's no way for a correct match to be found within the unflagged measures in the piece.
    
    Returns a tuple of the total number of NON-flagged measures and the total number
    of those measures that have a rhythmic match.
    
    Takes in a stream.Score.
    
    >>> c = converter.parse(omr.correctors.K525omrShortPath) # first 21 measures
    >>> totalUnflagged, totalUnflaggedWithMatches = omr.evaluators.autoCorrelationBestMeasure(c)
    >>> (totalUnflagged, totalUnflaggedWithMatches)
    (71, 64)
    >>> print( float(totalUnflaggedWithMatches) / totalUnflagged )
    0.901...
    
    
    Schoenberg has low autoCorrelation.
    
    >>> c = corpus.parse('schoenberg/opus19/movement6')
    >>> totalUnflagged, totalUnflaggedWithMatches = omr.evaluators.autoCorrelationBestMeasure(c)
    >>> (totalUnflagged, totalUnflaggedWithMatches)
    (18, 6)
    >>> print( float(totalUnflaggedWithMatches) / totalUnflagged )
    0.333...
    
    '''
    ss = correctors.ScoreCorrector(inputScore)
    allHashes = ss.getAllHashes()
    
    totalMeasures = 0
    totalMatches = 0
    
    singleParts = ss.singleParts
    
    for pNum, pHashArray in enumerate(allHashes):
        incorrectIndices = singleParts[pNum].getIncorrectMeasureIndices()
        for i, mHash in enumerate(pHashArray):
            if i in incorrectIndices:
                continue
            
            totalMeasures += 1
            match = False
            
            ## horizontal search...
            for j, nHash in enumerate(pHashArray):
                if i == j:
                    continue
                if mHash == nHash:
                    match = True
                    break
                
            ## vertical search...
            if match is False:
                for otherPNum in range(len(singleParts)):
                    if otherPNum == pNum:
                        continue
                    otherHash = allHashes[otherPNum][i]
                    if otherHash == mHash:
                        match = True
                        break 
                
            if match is True:
                totalMatches += 1
    return (totalMeasures, totalMatches)
  
if __name__ == '__main__':
    import music21
    music21.mainTest()

#     omrFilePath = '/Users/cuthbert/Desktop/SchubertOMR.xml'
#     groundTruthFilePath = '/Users/cuthbert/Dropbox/Vladimir_Myke/schubert unvoll all_fixed.xml'
#     
#     omrFilePath = correctors.K525omrFilePath
#     groundTruthFilePath = correctors.K525groundTruthFilePath
#     evaluateCorrectingModel(omrFilePath, groundTruthFilePath, debug = True)
# 
#     evaluateCorrectingModel(     # @UndefinedVariable
#          omrFilePath, groundTruthFilePath)
