# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         search/segment.py
# Purpose:      music21 classes for searching via segment matching
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2018 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
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
   (but then PyPy probably won't work)

'''
import copy
import difflib
import json
import math
import pathlib
import random

from collections import OrderedDict
from functools import partial

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import environment

_MOD = 'search.segment'
environLocal = environment.Environment(_MOD)


# noinspection SpellCheckingInspection
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
    # print(totalLength, numberOfSegments, segmentStarts)

    segmentList = []
    measureList = []

    for segmentStart in segmentStarts:
        segmentStart += random.randint(-1 * jitter, jitter)
        segmentStart = max(0, segmentStart)
        segmentStart = min(segmentStart, totalLength - 1)

        segmentEnd = min(segmentStart + segmentLengths, totalLength)
        currentSegment = outputStr[segmentStart:segmentEnd]
        measureTuple = (measures[segmentStart], measures[segmentEnd - 1])

        segmentList.append(currentSegment)
        measureList.append(measureTuple)
    return (segmentList, measureList)


# noinspection SpellCheckingInspection
def indexScoreParts(scoreFile, *args, **keywords):
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
            part, *args, **keywords)
        indexedList.append({
            'segmentList': segmentList,
            'measureList': measureList,
        })
    return indexedList


def _indexSingleMulticore(filePath, *args, **keywords):
    '''
    Index one path in the context of multicore.
    '''
    keywords2 = copy.copy(keywords)
    if 'failFast' in keywords2:
        del(keywords2['failFast'])

    if not isinstance(filePath, pathlib.Path):
        filePath = pathlib.Path(filePath)

    shortFp = filePath.name

    try:
        indexOutput = indexOnePath(filePath, *args, **keywords2)
    except Exception as e:  # pylint: disable=broad-except
        if 'failFast' not in keywords or keywords['failFast'] is False:
            print(f'Failed on parse/index for, {filePath}: {e}')
            indexOutput = ''
        else:
            raise e
    return(shortFp, indexOutput, filePath)


def _giveUpdatesMulticore(numRun, totalRun, latestOutput):
    print(f'Indexed {latestOutput[0]} ({numRun}/{totalRun})')


# noinspection SpellCheckingInspection
def indexScoreFilePaths(scoreFilePaths,
                        giveUpdates=False,
                        *args,
                        runMulticore=True,
                        **keywords):
    '''
    Returns a dictionary of the lists from indexScoreParts for each score in
    scoreFilePaths

    >>> #_DOCS_SHOW searchResults = corpus.search('bwv190')
    >>> searchResults = corpus.corpora.CoreCorpus().search('bwv190') #_DOCS_HIDE
    >>> fpsNamesOnly = sorted([searchResult.sourcePath for searchResult in searchResults])
    >>> len(fpsNamesOnly)
    2

    >>> scoreDict = search.segment.indexScoreFilePaths(fpsNamesOnly)
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

    indexFunc = partial(_indexSingleMulticore, *args, **keywords)

    for i in range(len(scoreFilePaths)):
        if not isinstance(scoreFilePaths[i], pathlib.Path):
            scoreFilePaths[i] = pathlib.Path(scoreFilePaths[i])

    if runMulticore:
        rpListUnOrdered = common.runParallel(
            scoreFilePaths,
            indexFunc,
            updateFunction=updateFunction)
    else:
        rpListUnOrdered = common.runNonParallel(
            scoreFilePaths,
            indexFunc,
            updateFunction=updateFunction)

    # ensure that orderedDict is sorted by original scoreFiles
    rpDict = {}
    for outShortName, outData, originalPathlib in rpListUnOrdered:
        rpDict[originalPathlib] = (outShortName, outData)

    rpList = []
    for p in scoreFilePaths:
        rpList.append(rpDict[p])

    scoreDict = OrderedDict(rpList)

    return scoreDict


def indexOnePath(filePath, *args, **keywords):
    '''
    Index a single path.  Returns a scoreDictEntry
    '''
    if not isinstance(filePath, pathlib.Path):
        filePath = pathlib.Path(filePath)

    if not filePath.is_absolute():
        scoreObj = corpus.parse(filePath)
    else:
        scoreObj = converter.parse(filePath)

    scoreDictEntry = indexScoreParts(scoreObj, *args, **keywords)
    return scoreDictEntry


def saveScoreDict(scoreDict, filePath=None):
    '''
    Save the score dict from indexScoreFilePaths as a .json file for quickly
    reloading

    Returns the filepath (assumes you'll probably be using a temporary file)
    as a pathlib.Path()
    '''
    if filePath is None:
        filePath = environLocal.getTempFile('.json')
    elif isinstance(filePath, (str, bytes)):
        filePath = pathlib.Path(filePath)

    with filePath.open('wb') as f:
        json.dump(scoreDict, f)

    return filePath


def loadScoreDict(filePath):
    '''
    Load the scoreDictionary from filePath.
    '''
    if not isinstance(filePath, pathlib.Path):
        filePath = pathlib.Path(filePath)

    with filePath.open('b') as f:
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
            from Levenshtein import StringMatcher as pyLevenshtein
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
    >>> for p in ('bwv197.5.mxl', 'bwv190.7.mxl', 'bwv197.10.mxl'):
    ...     #_DOCS_SHOW source = corpus.search(p)[0].sourcePath
    ...     source = corpus.corpora.CoreCorpus().search(p)[0].sourcePath #_DOCS_HIDE
    ...     filePaths.append(source)
    >>> scoreDict = search.segment.indexScoreFilePaths(filePaths)
    >>> scoreSim = search.segment.scoreSimilarity(scoreDict, forceDifflib=True) #_DOCS_HIDE
    >>> #_DOCS_SHOW scoreSim = search.segment.scoreSimilarity(scoreDict)
    >>> len(scoreSim)
    496

    Returns a list of tuples of first score name, first score voice number, first score
    measure number, second score name, second score voice number, second score
    measure number, and similarity score (0 to 1).

    >>> for result in scoreSim[133:137]:
    ...     result
    ('bwv197.5.mxl', 1, 1, (4, 10), 'bwv190.7.mxl', 3, 4, (22, 30), 0.13...)
    ('bwv197.5.mxl', 1, 1, (4, 10), 'bwv197.10.mxl', 0, 0, (0, 8), 0.2)
    ('bwv197.5.mxl', 1, 1, (4, 10), 'bwv197.10.mxl', 1, 0, (0, 7), 0.266...)
    ('bwv197.5.mxl', 1, 1, (4, 10), 'bwv197.10.mxl', 1, 1, (4, 9), 0.307...)
    '''
    similarityScores = []
    scoreIndex = 0
    totalScores = len(scoreDict)
    scoreDictKeys = list(scoreDict.keys())
    pNum = None
    segmentNumber = None

    def doOneSegment(thisSegment):
        dl = getDifflibOrPyLev(thisSegment, forceDifflib=forceDifflib)
        # dl = difflib.SequenceMatcher(None, '', thisSegment)
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
            print(f'Comparing {thisScoreKey} ({scoreIndex}/{totalScores})')
        for pNum in range(len(thisScore)):
            for segmentNumber, thisSegmentOuter in enumerate(thisScore[pNum]['segmentList']):
                if len(thisSegmentOuter) < minimumLength:
                    continue
                thisMeasureNumber = thisScore[pNum]['measureList'][segmentNumber]
                doOneSegment(thisSegmentOuter)

    # import pprint
    # pprint.pprint(similarityScores)
    return similarityScores


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == '__main__':
    import music21
    music21.mainTest()

