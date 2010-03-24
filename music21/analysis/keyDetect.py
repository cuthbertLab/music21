#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         keyDetectSketch.py
# Purpose:      Test module for future keyDetect functionality
#
# Authors:      Jared Sadoian
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest, random
import sys

import music21
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from music21 import common
from music21 import converter
from music21 import corpus
from music21 import pitch
from music21.pitch import Pitch
from pylab import *


from music21 import environment
_MOD = 'keyDetect.py'
environLocal = environment.Environment(_MOD)
#environLocal['directoryScratch'] = 'C:/Users/Jared/Desktop'
#environLocal.write()

#------------------------------------------------------------------------------

class KeyDetectException(Exception):
    pass


#------------------------------------------------------------------------------

class KeyDetect(object):
    
    def __init__(self, streamObj):
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyDetectException, 'non-stream provided as argument'
        self.streamObj = streamObj

    def setupKeyFinder(self, sStream, minWindow):
        names = [x.id for x in sStream]
    
        ''' Find part with max number of pitches
        '''
        max = 0
        for i in range(len(sStream)):
            check = len(sStream[i].pitches)
            if check > max:
                max = check
        
        solutionMatrix = [[0]*(max-minWindow)]*(len(sStream))

        for i in range(len(sStream)):
            print("-----WORKING ON PART ", names[i], "-----")
            part = sStream[i].pitches
            for j in range(minWindow, len(part)):
                print("-----window size ", j, "-----")
                solutionMatrix[i][j-10] = self.runKeyFinder(j, part)
            
        print solutionMatrix


    def runKeyFinder(self, windowSize, part):
        ''' Takes in windows size as argument to run key detection
        '''
    
        key = [0] * (len(part) - windowSize + 1)
    
        ''' Run key detection over all possible segments of a given window size
        '''
        if windowSize > len(part):
            windowSize = len(part)
        
        for i in range(len(part) - windowSize + 1):
            pitchClassDist = [0] * 12
            pcGroup = [n.pitchClass for n in part[(0 + i):windowSize + i]]
            ''' fill pitch class distribution table
            '''
            for j in pcGroup:
                pitchClassDist[j] = pitchClassDist[j] + 1
                #print("pass", i)
                #print pitchClassDist
                #print len(part)
            key[i] = self.keyDetect(pitchClassDist)
            #createDistributionGraph(pitchClassDist)

        return key

    def keyDetect(self, pcDistribution):    
        ''' Takes in a pitch class distribution and algorithmically detects
            probable keys using convoluteKey() and getLikelyKeys()
        '''
    
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        keyResults = self.convoluteKey(pcDistribution)   
        likelyKeys = self.getLikelyKeys(keyResults)

        #print "Key probabilities ordered by pitch class:", keyResults
        #print keySorted
        #print "Possible keys, from most likely to least likely", likelyKeys
    
        #print("Key of analyzed segment:", likelyKeys[0], "(runners up", likelyKeys[1], "and", likelyKeys[2], ")")
        return likelyKeys[0]


    def convoluteKey(self, pcDistribution, isMajor=True):
        ''' Takes in a pitch class distribution as a list and convolutes it
            over Sapp's given distribution for finding key, returning the result. 
        '''
        majorToneWeights = [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minorToneWeights = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        soln = [0] * 12
    
        if isMajor:
            toneWeights = majorToneWeights
        else:
            toneWeights = minorToneWeights
            
        for i in range(len(soln)):
            for j in range(len(pcDistribution)):
                soln[i] = soln[i] + (pcDistribution[(j + i) % 12] * toneWeights[j])
    
        #print soln  
    
        return soln

    def getLikelyKeys(self, keyResults):
        ''' Takes in a list of probably key results in points and returns a
            list of keys in letters, sorted from most likely to least likely
        '''
        likelyKeys = [0] * 12
        a = sorted(keyResults)
        a.reverse()
    
        for i in range(len(a)):
            likelyKeys[i] = Pitch(keyResults.index(a[i]))
    
        return likelyKeys


    def createDistributionGraph(self, pcDistribution):
        ''' Takes a distribution of pitch classes and creates a bar graph
        '''
        x = arange(12)
        ax = subplot(111)
        bar(x, pcDistribution)
    
        xticks(x + 0.4, ('C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B'))

        show()

    


#------------------------------------------------------------------------------

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testKeyDetect(self):
        sStream = corpus.parseWork('bach/bwv10.7')
        a = KeyDetect(sStream)
        a.setupKeyFinder(sStream, 4)
        


#------------------------------------------------------------------------------

if (__name__ == "__main__"):
    music21.mainTest(Test, TestExternal)
    
