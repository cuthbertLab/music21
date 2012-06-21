# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         awsutility.py
# Purpose:      methods for use by mrjob to deploy on amazon web services
#
# Authors:      Beth Hadley
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import music21
from music21 import *
from music21 import features
from music21.features import jSymbolic
from music21.features import native
from music21 import corpus
from music21 import common

#def generateCompleteCorpusFileList():
#    '''
#    utility for generating a text file containing all corpus file names
#    '''
#    def skip(path):
#        for skipString in ['.svn','.py','theoryExercises','demos','license.txt']:
#            if skipString in path:
#                return True
#        return False
#    
#    pathList = []
#    i=0
#    for path in corpus.getCorePaths():
#        if not skip(path):
#            pathList.append( path.replace('/home/bhadley/music21Workspace/music21baseubuntu/trunk/music21/corpus/',''))
#            i+=1
#    print 'Total number of files: ' + str(i)
#    #Total number of files: 2203
#    outFile = open('corpusPaths.txt','w')
#    
#    for x in pathList:
#        outFile.write("%s\n" % x)

def md5OfCorpusFile(fileDir, scoreNumber=None):
    '''
    returns the md5 hash of the text file contents. the file must be the full
    name of the corpus file
    
    >>> from music21 import *
    >>> a = md5OfCorpusFile('bach/bwv431.mxl')
    >>> a
    '3b8c4b8db4288c43efde44ddcdb4d8d2'
    
    >>> s = corpus.parse('bwv431')
    >>> b = md5OfCorpusFile(s.corpusFilepath)
    >>> b
    '3b8c4b8db4288c43efde44ddcdb4d8d2'
    >>> a == b
    True
    
    >>> md5OfCorpusFile('airdsAirs/book3.abc','413')
    'c1666c19d63fc0940f111008e2269f75.413'
    '''
    
    corpusFP = common.getCorpusFilePath()
    fileIn = open(corpusFP+'/'+fileDir,'r')
    md5 = common.getMd5 ( fileIn.read() )
    if scoreNumber:
        return md5 + '.' + scoreNumber
    else:
        return md5

def unbundleOpus(opusStream):
    '''
    unbundles the opusStream into seperate scores, and returns a list of tuples, the
    score and the md5hash (for the entire contents of the opus), a '.', and the score 
    number it corresponds to
    
    >>> from music21 import *
    >>> s = corpus.parse('book1')
    >>> unbundleOpus(s)[15:17]
    [(<music21.stream.Score ...>, '1ae57f04a11981d502dc93e230f3466b.16'), (<music21.stream.Score ...>, '1ae57f04a11981d502dc93e230f3466b.17')]
    '''

    results = []
    corpusFilepath = opusStream.corpusFilepath
    md5hash = md5OfCorpusFile(corpusFilepath)
    for num in opusStream.getNumbers():
        st = opusStream.getScoreByNumber(num)
        corpus.base._addCorpusFilepath(st, corpusFilepath)
        results.append ( (st, (md5hash+'.'+num) ) ) 
    return results

def getStreamAndmd5(corpusFilepath):
    '''
    returns a list of all the corpus,md5hash pairs associated with this file, typically
    this is just a list of one tuple but if the file path contains an opus file, these
    are parsed into tuples with :meth:`music21.demos.bhadley.aws.unbundleOpus` and the list is returned
    
    >>> from music21 import *
    >>> getStreamAndmd5('airdsAirs/book3.abc')[12:14]
    [(<music21.stream.Score ...>, 'c1666c19d63fc0940f111008e2269f75.413'), (<music21.stream.Score ...>, 'c1666c19d63fc0940f111008e2269f75.414')]
    >>> getStreamAndmd5('bach/bwv412.mxl')
    [(<music21.stream.Score ...>, 'f9d5807477e61f03b66c99ce825a3b5f')]

    '''
    s = corpus.parse(corpusFilepath)
    if s.isClassOrSubclass(['Opus']):
        return unbundleOpus(s)
    else:
        return [(s,md5OfCorpusFile(corpusFilepath))]

def getFeatureData(corpusFilepath):
    '''
    returns a dictionary output with the key an md5 hash, and value a 
    tuple with corpusFilepath, jsymbolic vectors, and native vectors
    
    >>> from music21 import *
    >>> getFeatureData('bach/bwv412.mxl')
    {'f9d5807477e61f03b66c99ce825a3b5f': ('bach/bwv412.mxl', [[0.5333333333333333, 0.7333333333333334, 1.0, 0.08888888888888889, 0.1, 0.13333333333333333, 0.0, 0.08888888888888889, 0.044444444444444446, 0.011111111111111112, 0.0, 0.0, 0.044444444444444446, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.044], [2], [1], [0.36], [0.7333333333333334], [3], [0.308], [0.192], [0.264], [0.624], [0.068], [0.032], [0.0], [0.016], [0.4306930693069307], [16.857142857142858], [16.25], [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0.24015748031496062, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0.008116349656727672], [4], [1.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0], [12], [0.45112781954887216], [1.25], [0.125], [0.0], [0.31382978723404253], [0.152270800088294], [0.4338235294117647], [0.19062981398873327], [120.0], [4, 4], [0], [0], [0], [0], [4], [4.0], [0.0], [0.10236220472440945], [0.19291338582677164], [0.8461538461538461], [0.7755102040816326], [5], [7], [1], [34], [12], [39], [0.484375], [58.5], [0.2440944881889764], [0.6850393700787402], [0.07086614173228346], [2], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.038461538461538464, 0.0, 0.0, 0.038461538461538464, 0.038461538461538464, 0.19230769230769232, 0.038461538461538464, 0.19230769230769232, 0.2692307692307693, 0.0, 0.42307692307692313, 0.038461538461538464, 0.42307692307692313, 0.19230769230769232, 0.07692307692307693, 0.2692307692307693, 0.15384615384615385, 0.34615384615384615, 0.0, 0.5, 0.5384615384615385, 0.038461538461538464, 0.5, 0.0, 1.0, 0.19230769230769232, 0.2692307692307693, 0.7692307692307693, 0.19230769230769232, 0.8461538461538463, 0.0, 0.7692307692307693, 0.5, 0.038461538461538464, 0.19230769230769232, 0.07692307692307693, 0.42307692307692313, 0.038461538461538464, 0.07692307692307693, 0.07692307692307693, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.5918367346938775, 0.061224489795918366, 0.9999999999999999, 0.22448979591836732, 0.22448979591836732, 0.6122448979591836, 0.2040816326530612, 0.7346938775510203, 0.02040816326530612, 0.7755102040816326, 0.6938775510204082, 0.04081632653061224], [0.5918367346938775, 0.7346938775510203, 0.9999999999999999, 0.7755102040816326, 0.22448979591836732, 0.04081632653061224, 0.2040816326530612, 0.061224489795918366, 0.02040816326530612, 0.22448979591836732, 0.6938775510204082, 0.6122448979591836], [1]], [[1], [1.1567724603998282], [6], [1.0], [0.531496062992126], [2.25], [39], [13], [0.10869565217391304], [0.5434782608695652], [0.40217391304347827], [0.15217391304347827], [0.11956521739130435], [0.043478260869565216], [0.5869565217391305], [0.0], [0.0], [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0], [0], [0]])}
    '''
    data = getStreamAndmd5(corpusFilepath)
    dict = {}
    for dataList in data:
        streamObj, md5hash = dataList
        jsymbolicVectors = features.base.alljSymbolicVectors(streamObj)
        nativeVectors = features.base.allNativeVectors(streamObj)
        dict[md5hash] = (streamObj.corpusFilepath, jsymbolicVectors, nativeVectors )
    return dict


class Test(unittest.TestCase):
    def runTest(self):
        pass

        
if __name__ == "__main__":
    music21.mainTest(Test)

