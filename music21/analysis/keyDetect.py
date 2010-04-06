#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         keyDetect.py
# Purpose:      
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
from music21 import note
from music21.note import Note
from music21.pitch import Pitch
from pylab import *


from music21 import environment
_MOD = 'keyDetect.py'
environLocal = environment.Environment(_MOD)
#environLocal['directoryScratch'] = 'C:/Users/Jared/Desktop'
#environLocal.write()

#------------------------------------------------------------------------------
# utility functions

def getWeights(isMajor): 
    ''' Returns either the major or minor key profile as described by Sapp
        
    >>> getWeights(True)
    [6.3499999999999996, 2.3300000000000001, 3.48, 2.3300000000000001, 4.3799999999999999, 4.0899999999999999, 2.52, 5.1900000000000004, 2.3900000000000001, 3.6600000000000001, 2.29, 2.8799999999999999]
    >>> getWeights(False)
    [6.3300000000000001, 2.6800000000000002, 3.52, 5.3799999999999999, 2.6000000000000001, 3.5299999999999998, 2.54, 4.75, 3.98, 2.6899999999999999, 3.3399999999999999, 3.1699999999999999]
        
    '''
        
    if isMajor:
        return [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    else:
        return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]    


def getPitchClassDistribution(work, start, windowSize):
    current = work.getMeasureRange(start, start+windowSize).flat
    pcDist = [0]*12
    
    for n in current.notes:        
        if not n.isRest:
            length = n.quarterLength
            if n.isChord:
                for m in n.pitchClasses:
                    pcDist[m] = pcDist[m] + (1 * length)
            else:
                pcDist[n.pitchClass] = pcDist[n.pitchClass] + (1 * length)
    
    return pcDist


def convoluteDistribution(pcDistribution, isMajor=True):
    ''' Takes in a pitch class distribution as a list and convolutes it
        over Sapp's given distribution for finding key, returning the result. 
    '''
    soln = [0] * 12
    
    if isMajor:
        toneWeights = getWeights(True)
    else:
        toneWeights = getWeights(False)
            
    for i in range(len(soln)):
        for j in range(len(pcDistribution)):
            soln[i] = soln[i] + (toneWeights[(j - i) % 12] * pcDistribution[j])
        
    return soln  


def findLongestPart(sStream):
    ''' temporary function to find the longest part (based on the number
        of pitches) in a parsed work.
    '''
    max = 0
    for i in range(len(sStream)):
        check = len(sStream[i].pitches)
        if check > max:
            max = check
    return max
    
    
def getLikelyKeys(keyResults, differences):
    ''' Takes in a list of probably key results in points and returns a
        list of keys in letters, sorted from most likely to least likely
    '''
    likelyKeys = [0] * 12
    a = sorted(keyResults)
    a.reverse()
    
    ''' Return pairs, the pitch class and the correlation value, in order by point value
    '''
    for i in range(len(a)):
        likelyKeys[i] = (Pitch(keyResults.index(a[i])), differences[keyResults.index(a[i])])
    
    return likelyKeys
    
    
def getDifference(keyResults, pcDistribution, isMajor=True):
#def getDifference(self, pcDistribution, isMajor=True):
    ''' Takes in a list of numerical probably key results and returns the
        difference of the top two keys
    '''
        
    soln = [0]*12
    top = [0]*12
    bottomRight = [0]*12
    bottomLeft = [0]*12
        
    #a = sorted(keyResults)
    #a.reverse()
        
    if isMajor:
        toneWeights = getWeights(True)
    else:
        toneWeights = getWeights(False)
        
    profileAverage = float(sum(toneWeights))/len(toneWeights)
    histogramAverage = float(sum(pcDistribution))/len(pcDistribution) 
        
    for i in range(len(soln)):
        for j in range(len(toneWeights)):
            #print "BLAH"
            top[i] = top[i] + ((toneWeights[(j - i) % 12]-profileAverage) * (pcDistribution[j]-histogramAverage))
            #print top[i]
            bottomRight[i] = bottomRight[i] + ((toneWeights[(j-i)%12]-profileAverage)**2)
            #print bottomRight[i]
            bottomLeft[i] = bottomLeft[i] + ((pcDistribution[j]-histogramAverage)**2)
            #print bottomLeft[i]
            soln[i] = float(top[i]) / ((bottomRight[i]*bottomLeft[i])**.5)
            #print soln[i]
        
    #print soln
    return soln

#------------------------------------------------------------------------------

class KeyDetectException(Exception):
    pass


#------------------------------------------------------------------------------

class KeyDetect(object):
    
    def __init__(self, streamObj):
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyDetectException, 'non-stream provided as argument'
        self.streamObj = streamObj


    def runKeyDetect(self, sStream, minWindow):
        # names = [x.id for x in sStream]
        
        max = len(sStream[0].measures)
        
        solutionMatrix = [0]*(max-minWindow+1)
        
        print("-----WORKING... window-----")
        for i in range(minWindow, max+1):
            print(i)
            solutionMatrix[i-minWindow] = self.windowKeyDetect(i, sStream) 
        
        
        print solutionMatrix


    def windowKeyDetect(self, windowSize, work):
        
        max = len(work[0].measures)
        key = [0] * (max - windowSize + 1)                
        
        for i in range(max-windowSize + 1):    
            key[i] = self.singleKeyDetect(getPitchClassDistribution(work, i, windowSize))
             
        return key
 
    
    def singleKeyDetect(self, pcDistribution):    
        ''' Takes in a pitch class distribution and algorithmically detects
            probable keys using convoluteDistribution() and getLikelyKeys()
        '''
    
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        keyResultsMajor = convoluteDistribution(pcDistribution, True)
        differenceMajor = getDifference(keyResultsMajor, pcDistribution, True)
        likelyKeysMajor = getLikelyKeys(keyResultsMajor, differenceMajor)
        
        
        keyResultsMinor = convoluteDistribution(pcDistribution, False)   
        differenceMinor = getDifference(keyResultsMinor, pcDistribution, False)
        likelyKeysMinor = getLikelyKeys(keyResultsMinor, differenceMinor)
        

        ''' find the largest correlation value to use for a key
        '''
        if likelyKeysMajor[0][1] > likelyKeysMinor[0][1]:
            likelyKey = (likelyKeysMajor[0][0], "Major", likelyKeysMajor[0][1])
        else:
            likelyKey = (likelyKeysMinor[0][0], "Minor", likelyKeysMinor[0][1])
        
        '''
        print keyResultsMajor
        print likelyKeysMajor
        print differenceMajor
        
        print keyResultsMinor
        print likelyKeysMinor
        print differenceMinor
        
        print likelyKey
        '''
        
        return likelyKey


#------------------------------------------------------------------------------

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    '''
    def testKeyDetect(self):
        sStream = corpus.parseWork('schubert/d576-2')
        #sStream = corpus.parseWork('bach/bwv17.7')
        a = KeyDetect(sStream)
        a.runKeyDetect(sStream, 1)
    '''    


#------------------------------------------------------------------------------

if (__name__ == "__main__"):
    import doctest
    doctest.testmod()
    music21.mainTest(Test, TestExternal)
    
