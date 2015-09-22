# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         search/segment.py
# Purpose:      music21 classes for searching via segment matching
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
tools for segmenting -- that is, dividing up a score into small, possibly overlapping
sections -- for searching across pieces for similarity.

Speed notes:
   
   this module is definitely a case where running PyPy rather than cPython will
   give you a 3-5x speedup.  
   
   If you really want to do lots of comparisons, the `scoreSimilarity` method will
   use pyLevenshtein if it is installed from http://code.google.com/p/pylevenshtein/ .
   You will need to compile it by running **sudo python setup.py install** on Mac or
   Unix (compilation is much more difficult on Windows; sorry). The ratios are very 
   slightly different, but the speedup is between 10 and 100x!

'''
from music21 import converter
from music21 import corpus
from music21 import environment

_MOD = 'search.segment.py'
environLocal = environment.Environment(_MOD)
import copy
import os
import math
import json
import difflib
from collections import OrderedDict

def translateMonophonicPartToSegments(
    inputStream,
    segmentLengths = 30,
    overlap = 12,
    algorithm = None,
    ):
    '''
    Translates a monophonic part with measures to a set of segments of length
    `segmentLengths` (measured in number of notes) with an overlap of `overlap` notes 
    using a conversion algorithm of `algorithm` (default: search.translateStreamToStringNoRhythm). 
    Returns two lists, a list of segments, and a list of measure
    numbers that match the segments.
    
    If algorithm is None then a default algorithm of music21.search.translateStreamToStringNoRhythm
    is used

    >>> from music21 import *
    >>> luca = corpus.parse('luca/gloria')
    >>> lucaCantus = luca.parts[0]
    >>> segments, measureLists = search.segment.translateMonophonicPartToSegments(lucaCantus)
    >>> segments[0:2]
    ['HJHEAAEHHCE@JHGECA@A>@A><A@AAE', '@A>@A><A@AAEEECGHJHGH@CAE@FECA']


    Segment zero begins at measure 1.  Segment 1 begins at measure 7:

    >>> measureLists[0:2]
    [1, 7]

    >>> segments, measureLists = search.segment.translateMonophonicPartToSegments(
    ...     lucaCantus, 
    ...     algorithm=search.translateDiatonicStreamToString)
    >>> segments[0:2]
    ['CRJOMTHCQNALRQPAGFEFDLFDCFEMOO', 'EFDLFDCFEMOOONPJDCBJSNTHLBOGFE']

    >>> measureLists[0:2]
    [1, 7]

    '''
    from music21 import search
    if algorithm is None:
        algorithm = search.translateStreamToStringNoRhythm
    
    segmentList = []
    measureSegmentList = []
    measureList = []
    
    totalLength = 0
    previousTuple = (False, False, None) # lastRest, lastTied, lastQL
    for m in inputStream.getElementsByClass('Measure'):
        mNotes = m.flat.getElementsByClass('Note')
        if algorithm == search.translateDiatonicStreamToString:
            algorithmOutput, previousTuple = algorithm(mNotes, previousTuple[0], previousTuple[1], previousTuple[2], returnLastTuple=True)
        else: # not all algorithms can take two streams...
            algorithmOutput = algorithm(mNotes) 
        
        mDict = {'measureNumber': m.number, 
                 'data': algorithmOutput, 
                 'dataLength': len(algorithmOutput), 
                 'startPosition': totalLength}
        totalLength += len(algorithmOutput)
        measureSegmentList.append(mDict)

    numberOfSegments = int(math.ceil((totalLength+0.0)/(segmentLengths-overlap)))
    segmentStarts = [i*(segmentLengths-overlap) for i in range(numberOfSegments)]
    #print totalLength, numberOfSegments, segmentStarts
    
    for segmentStart in segmentStarts:
        segmentEnd = segmentStart + segmentLengths
        currentSegment = ""
        startMeasure = None
        lengthLeft = segmentLengths
        for mDict in measureSegmentList:
            if mDict['startPosition'] + mDict['dataLength'] < segmentStart:
                continue
            elif mDict['startPosition'] >= segmentEnd:
                break
            if startMeasure is None:
                startMeasure = mDict['measureNumber']
            currentData = mDict['data']
            lenCurrentData = mDict['dataLength']
            if mDict['startPosition'] < segmentStart:
                trimFromFront = segmentStart - mDict['startPosition']
                currentDataTrimmed = currentData[trimFromFront:]
                lengthLeft = lengthLeft - len(currentDataTrimmed)
                currentSegment += currentDataTrimmed
            elif lengthLeft < lenCurrentData:
                currentDataTrimmed = currentData[0:lengthLeft]
                currentSegment += currentDataTrimmed
                lengthLeft = lengthLeft - len(currentDataTrimmed) # shouldn't matter...
            else:
                lengthLeft = lengthLeft - lenCurrentData
                currentSegment += currentData      
        segmentList.append(currentSegment)
        measureList.append(startMeasure)
    return (segmentList, measureList)

def indexScoreParts(scoreFile, *args, **kwds):
    r'''
    Creates segment and measure lists for each part of a score
    Returns list of dictionaries of segment and measure lists
    
    
    >>> bach = corpus.parse('bwv66.6')
    >>> scoreList = search.segment.indexScoreParts(bach)
    >>> scoreList[1]['segmentList'][0]
    '@B@@@@ED@DBDA=BB@?==B@@EBBDBBA'
    >>> scoreList[1]['measureList'][0:3]
    [0, 4, 8]
    '''
    scoreFileParts = scoreFile.parts
    indexedList = []
    for part in scoreFileParts:
        segmentList, measureList = translateMonophonicPartToSegments(
            part, *args, **kwds)
        indexedList.append({
            'segmentList': segmentList, 
            'measureList': measureList,
            })
    return indexedList


def indexScoreFilePaths(
    scoreFilePaths,
    giveUpdates=False,
    *args,
    **kwds
    ):
    '''
    Returns a dictionary of the lists from indexScoreParts for each score in
    scoreFilePaths
    
    >>> searchResults = corpus.search('bwv19')
    >>> fpsNamesOnly = sorted([searchResult.sourcePath
    ...     for searchResult in searchResults])
    >>> len(fpsNamesOnly)
    9

    >>> scoreDict = search.segment.indexScoreFilePaths(fpsNamesOnly[2:5])
    >>> len(scoreDict['bwv190.7.mxl'])
    4

    >>> scoreDict['bwv190.7.mxl'][0]['measureList']
    [0, 5, 11, 17, 22, 27]

    >>> scoreDict['bwv190.7.mxl'][0]['segmentList'][0]
    'NNJLNOLLLJJIJLLLLNJJJIJLLJNNJL'
    
    '''
    scoreDict = OrderedDict()
    scoreIndex = 0
    totalScores = len(scoreFilePaths)
    for filePath in scoreFilePaths:
        shortfp = filePath.split(os.sep)[-1]
        if giveUpdates is True:
            print("Indexing %s (%d/%d)" % (
                shortfp, scoreIndex, totalScores))
        scoreIndex += 1
        if 'failFast' not in kwds or kwds['failFast'] is False:        
            try:
                scoreDict[shortfp] = indexOnePath(filePath, *args, **kwds)
            except Exception as e: # pylint: disable=broad-except
                print("Failed on parse for, %s: %s" % (filePath, str(e)))
        else:
            kwds2 = copy.copy(kwds)
            del(kwds2['failFast'])
            scoreDict[shortfp] = indexOnePath(filePath, *args, **kwds2)
            
    return scoreDict


def indexOnePath(filePath, *args, **kwds):
    if not os.path.isabs(filePath):
        scoreObj = corpus.parse(filePath)
    else:
        scoreObj = converter.parse(filePath)
    scoreDictEntry = indexScoreParts(scoreObj, *args, **kwds)
    return scoreDictEntry

def saveScoreDict(scoreDict, filePath=None):
    '''
    Save the score dict from indexScoreFilePaths as a .json file for quickly
    reloading

    Returns the filepath (assumes you'll probably be using a temporary file)
    '''
    if filePath is None:
        filePath = environLocal.getTempFile('.json')
    with open(filePath, 'wb') as f:
        json.dump(scoreDict, f)
    return filePath


def loadScoreDict(filePath):
    '''
    Load the scoreDictionary from filePath
    '''
    with open(filePath) as f:
        scoreDict = json.load(f)
    return scoreDict


def getDifflibOrPyLev(
    seq2=None, 
    junk=None, 
    forceDifflib=False,
    ):
    '''
    Returns either a difflib.SequenceMatcher or pyLevenshtein
    StringMatcher.StringMatcher object depending on what is installed.
    
    If forceDifflib is True then use difflib even if pyLevenshtein is installed:
    '''
    if forceDifflib is True:
        smObject = difflib.SequenceMatcher(junk, '', seq2)
    else:
        try:
            import StringMatcher as pyLevenshtein 
            smObject = pyLevenshtein.StringMatcher(junk, '', seq2)
        except ImportError:
            smObject = difflib.SequenceMatcher(junk, '', seq2)
    return smObject


def scoreSimilarity(
    scoreDict, 
    minimumLength=20, 
    giveUpdates=False, 
    includeReverse=False,
    forceDifflib=False,
    ):
    r'''
    Find the level of similarity between each pair of segments in a scoreDict.
    
    This takes twice as long as it should because it does not cache the
    pairwise similarity.
    
    >>> filePaths = []
    >>> filePaths.append(corpus.search('bwv197.5.mxl')[0].sourcePath)
    >>> filePaths.append(corpus.search('bwv190.7.mxl')[0].sourcePath)
    >>> filePaths.append(corpus.search('bwv197.10.mxl')[0].sourcePath)
    >>> scoreDict = search.segment.indexScoreFilePaths(filePaths)
    >>> scoreSim = search.segment.scoreSimilarity(scoreDict, forceDifflib=True) #_DOCS_HIDE
    >>> #_DOCS_SHOW scoreSim = search.segment.scoreSimilarity(scoreDict)
    >>> len(scoreSim)
    671
    
    Returns a list of tuples of first score name, first score voice number, first score
    measure number, second score name, second score voice number, second score
    measure number, and similarity score (0 to 1).
    
    >>> for result in scoreSim[64:68]:
    ...     result
    ...
    (...'bwv197.5.mxl', 0, 1, 4, ...'bwv197.10.mxl', 3, 1, 4, 0.0)
    (...'bwv197.5.mxl', 0, 1, 4, ...'bwv197.10.mxl', 3, 2, 9, 0.0)
    (...'bwv197.5.mxl', 0, 2, 9, ...'bwv190.7.mxl', 0, 0, 0, 0.07547...)
    (...'bwv197.5.mxl', 0, 2, 9, ...'bwv190.7.mxl', 0, 1, 5, 0.07547...)
        
    '''
    similarityScores = []
    scoreIndex = 0
    totalScores = len(scoreDict)
    scoreDictKeys = list(scoreDict.keys())
    for thisScoreNumber in range(totalScores):
        thisScoreKey = scoreDictKeys[thisScoreNumber]
        thisScore = scoreDict[thisScoreKey]
        scoreIndex += 1 
        if giveUpdates is True:
            print("Comparing {0} ({1}/{2})".format(
                thisScoreKey, scoreIndex, totalScores))
        for pNum in range(len(thisScore)):
            for segmentNumber, thisSegment in enumerate(thisScore[pNum]['segmentList']):
                if len(thisSegment) < minimumLength:
                    continue
                thisMeasureNumber = thisScore[pNum]['measureList'][segmentNumber]
                dl = getDifflibOrPyLev(thisSegment, forceDifflib = forceDifflib)
                #dl = difflib.SequenceMatcher(None, '', thisSegment)
                for thatScoreNumber in range(scoreIndex, totalScores):
                    thatScoreKey = scoreDictKeys[thatScoreNumber]
                    thatScore = scoreDict[thatScoreKey]
                    for pNum2 in range(len(thatScore)):
                        for thatSegmentNumber, thatSegment in enumerate(thatScore[pNum2]['segmentList']):
                            if len(thatSegment) < minimumLength:
                                continue
                            dl.set_seq1(thatSegment)
                            ratio = dl.ratio()
                            thatMeasureNumber = thatScore[pNum2]['measureList'][thatSegmentNumber]
                            similarityTuple = (
                                thisScoreKey, 
                                pNum, 
                                segmentNumber, 
                                thisMeasureNumber, 
                                thatScoreKey, 
                                pNum2, 
                                thatSegmentNumber, 
                                thatMeasureNumber, 
                                ratio,
                                )
                            similarityScores.append(similarityTuple)
                            if includeReverse is True:
                                similarityTupleReversed = (
                                    thatScoreKey, 
                                    pNum2, 
                                    thatSegmentNumber, 
                                    thatMeasureNumber, 
                                    thisScoreKey, 
                                    pNum, 
                                    segmentNumber, 
                                    thisMeasureNumber, 
                                    ratio,
                                    )
                                similarityScores.append(similarityTupleReversed)

    #import pprint
    #pprint.pprint(similarityScores)
    return similarityScores
    
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof


