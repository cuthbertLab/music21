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
   slightly different, but the speedup is between 10 and 100x! (but then PyPy probably won't work)

'''
from __future__ import print_function, division

import copy
import difflib
import json
import math
import os
import random

from collections import OrderedDict
from functools import partial

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import environment

_MOD = 'search.segment.py'
environLocal = environment.Environment(_MOD)


def translateMonophonicPartToSegments(
    inputStream,
    segmentLengths=30,
    overlap=12,
    algorithm=None,
    jitter=0,
    ):
    '''
    Translates a monophonic part with measures to a set of segments of length
    `segmentLengths` (measured in number of notes) with an overlap of `overlap` notes 
    using a conversion algorithm of `algorithm` (default: search.translateStreamToStringNoRhythm). 
    Returns two lists, a list of segments, and a list of tuples of measure start and end
    numbers that match the segments.
    
    If algorithm is None then a default algorithm of music21.search.translateStreamToStringNoRhythm
    is used

    >>> from music21 import *
    >>> luca = corpus.parse('luca/gloria')
    >>> lucaCantus = luca.parts[0]
    >>> segments, measureLists = search.segment.translateMonophonicPartToSegments(lucaCantus)
    >>> segments[0:2]
    ['HJHEAAEHHCE@JHGECA@A>@A><A@AAE', '@A>@A><A@AAEEECGHJHGH@CAE@FECA']


    Segment zero begins at measure 1 and ends in m. 12.  Segment 1 spans m.7 - m.18:

    >>> measureLists[0:2]
    [(1, 12), (7, 18)]

    >>> segments, measureLists = search.segment.translateMonophonicPartToSegments(
    ...     lucaCantus, 
    ...     algorithm=search.translateDiatonicStreamToString)
    >>> segments[0:2]
    ['CRJOMTHCQNALRQPAGFEFDLFDCFEMOO', 'EFDLFDCFEMOOONPJDCBJSNTHLBOGFE']

    >>> measureLists[0:2]
    [(1, 12), (7, 18)]

    '''
    from music21 import search
    if algorithm is None:
        algorithm = search.translateStreamToStringNoRhythm
        
    nStream = inputStream.recurse().notes.stream()
    outputStr, measures = algorithm(nStream, returnMeasures=True) 
    totalLength = len(outputStr)


    numberOfSegments = int(math.ceil((totalLength + 0.0) / (segmentLengths - overlap)))
    segmentStarts = [i * (segmentLengths - overlap) for i in range(numberOfSegments)]
    #print(totalLength, numberOfSegments, segmentStarts)

    segmentList = []
    measureList = []
    
    for segmentStart in segmentStarts:
        segmentStart += random.randint(-1 * jitter, jitter)
        segmentStart = max(0, segmentStart)
        segmentStart = min(segmentStart, totalLength - 1)
        
        segmentEnd = min(segmentStart + segmentLengths, totalLength)
        currentSegment = outputStr[segmentStart:segmentEnd]
        measureTuple = (measures[segmentStart],  measures[segmentEnd - 1])

        segmentList.append(currentSegment)
        measureList.append(measureTuple)
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
    [(0, 7), (4, 9), (8, 9)]
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


def _indexSingleMulticore(filePath, *args, **kwds):
    kwds2 = copy.copy(kwds)
    if 'failFast' in kwds2:
        del(kwds2['failFast'])

    shortfp = filePath.split(os.sep)[-1]
    try:
        indexOutput = indexOnePath(filePath, *args, **kwds2)
    except Exception as e: # pylint: disable=broad-except
        if 'failFast' not in kwds or kwds['failFast'] is False:
            print("Failed on parse/index for, %s: %s" % (filePath, str(e)))
            indexOutput = ""
        else:
            raise(e)
    return(shortfp, indexOutput)

def _giveUpdatesMulticore(numRun, totalRun, latestOutput):
    for o in latestOutput:
        print("Indexed %s (%d/%d)" % (
            o[0], numRun, totalRun))
    

def indexScoreFilePaths(scoreFilePaths,
                        giveUpdates=False,
                        *args,
                        **kwds):
    '''
    Returns a dictionary of the lists from indexScoreParts for each score in
    scoreFilePaths
    
    >>> searchResults = corpus.search('bwv19')
    >>> fpsNamesOnly = sorted([searchResult.sourcePath for searchResult in searchResults])
    >>> len(fpsNamesOnly)
    9

    >>> scoreDict = search.segment.indexScoreFilePaths(fpsNamesOnly[2:5])
    >>> len(scoreDict['bwv190.7.mxl'])
    4

    >>> scoreDict['bwv190.7.mxl'][0]['measureList']
    [(0, 9), (6, 15), (11, 20), (17, 25), (22, 31), (27, 32)]

    >>> scoreDict['bwv190.7.mxl'][0]['segmentList'][0]
    'NNJLNOLLLJJIJLLLLNJJJIJLLJNNJL'
    
    '''
    if giveUpdates is True:
        updateFunction = _giveUpdatesMulticore
    else:
        updateFunction = None
    
    indexFunc = partial(_indexSingleMulticore, *args, **kwds)

    rpList = common.runParallel(scoreFilePaths, indexFunc, updateFunction)
    scoreDict = OrderedDict(rpList)

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
    (...'bwv197.5.mxl', 0, 1, (5, 11), ...'bwv197.10.mxl', 3, 1, (5, 12), 0.0)
    (...'bwv197.5.mxl', 0, 1, (5, 11), ...'bwv197.10.mxl', 3, 2, (9, 14), 0.0)
    (...'bwv197.5.mxl', 0, 2, (9, 14), ...'bwv190.7.mxl', 0, 0, (0, 9), 0.07547...)
    (...'bwv197.5.mxl', 0, 2, (9, 14), ...'bwv190.7.mxl', 0, 1, (6, 15), 0.07547...)
    '''
    similarityScores = []
    scoreIndex = 0
    totalScores = len(scoreDict)
    scoreDictKeys = list(scoreDict.keys())
    pNum = None
    segmentNumber = None
    
    def doOneSegment(thisSegment):
        dl = getDifflibOrPyLev(thisSegment, forceDifflib=forceDifflib)
        #dl = difflib.SequenceMatcher(None, '', thisSegment)
        for thatScoreNumber in range(scoreIndex, totalScores):
            thatScoreKey = scoreDictKeys[thatScoreNumber]
            thatScore = scoreDict[thatScoreKey]
            for pNum2 in range(len(thatScore)):
                for thatSegmentNumber, thatSegment in enumerate(
                                                    thatScore[pNum2]['segmentList']):
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
                    if not includeReverse:
                        continue
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
                doOneSegment(thisSegment)

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
