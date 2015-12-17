# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         awsutility.py
# Purpose:      methods for use by mrjob to deploy on amazon web services
#
# Authors:      Beth Hadley
#
# Copyright:    Copyright © 2011 The music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest
import music21
import os
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
    
    >>> from music21.demos.bhadley.mrjobaws.awsutility import md5OfCorpusFile
    
    >>> a = md5OfCorpusFile('bach/bwv431.mxl')
    >>> a
    '3b8c4b8db4288c43efde44ddcdb4d8d2'
    
    >>> s = corpus.parse('bwv431')
    >>> s.corpusFilepath
    'bach/bwv431.mxl'
    
    >>> b = md5OfCorpusFile(s.corpusFilepath)
    >>> b
    '3b8c4b8db4288c43efde44ddcdb4d8d2'

    >>> a == b
    True
    
    >>> md5OfCorpusFile('airdsAirs/book3.abc','413')
    'c1666c19d63fc0940f111008e2269f75.413'
    '''
    
    corpusFP = common.getCorpusFilePath()
    fileIn = open(corpusFP + os.sep + fileDir,'rb')
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
    
    
    >>> #_DOCS_SHOW s = corpus.parse('book1') 
    >>> #_DOCS_SHOW unbundleOpus(s)[15:17] 
    [(<music21.stream.Score ...>, 
     '1ae57f04a11981d502dc93e230f3466b.16'), 
     (<music21.stream.Score ...>, 
     '1ae57f04a11981d502dc93e230f3466b.17')]
    '''

    results = []
    corpusFilepath = opusStream.corpusFilepath
    md5hash = md5OfCorpusFile(corpusFilepath)
    for num in opusStream.getNumbers():
        st = opusStream.getScoreByNumber(num)
        corpus._addCorpusFilepath(st, corpusFilepath)
        results.append ( (st, (md5hash+'.'+num) ) ) 
    return results

def getStreamAndmd5(corpusFilepath):
    '''
    returns a list of all the corpus,md5hash pairs associated with this file, typically
    this is just a list of one tuple but if the file path contains an opus file, these
    are parsed into tuples with :meth:`music21.demos.bhadley.aws.unbundleOpus` and the list is returned
    
    >>> from music21.demos.bhadley.mrjobaws.awsutility import getStreamAndmd5
    
    >>> #_DOCS_SHOW getStreamAndmd5('airdsAirs/book3.abc')[12:14] 
    [(<music21.stream.Score ...>, 'c1666c19d63fc0940f111008e2269f75.413'), (<music21.stream.Score ...>, 'c1666c19d63fc0940f111008e2269f75.414')]
    >>> getStreamAndmd5('bach/bwv412.mxl') 
    [(<music21.stream.Score ...>, 'f9d5807477e61f03b66c99ce825a3b5f')]

    '''
    s = corpus.parse(corpusFilepath)
    if s.isClassOrSubclass(['Opus']):
        return unbundleOpus(s)
    else:
        return [(s,md5OfCorpusFile(corpusFilepath))]

class Test(unittest.TestCase):
    def runTest(self):
        pass

        
if __name__ == "__main__":
    music21.mainTest(Test)
    
