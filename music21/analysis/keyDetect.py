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
    
    
    def getWeights(self, isMajor): 
        
        if isMajor:
            return [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        else:
            return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    
        
    def findLongestPart(self, sStream):
        ''' temporary function to find the longest part (based on the number
            of pitches) in a parsed work.
        '''
        max = 0
        for i in range(len(sStream)):
            check = len(sStream[i].pitches)
            if check > max:
                max = check
        return max
    
    
    def getLikelyKeys(self, keyResults):
        ''' Takes in a list of probably key results in points and returns a
            list of keys in letters, sorted from most likely to least likely
        '''
        likelyKeys = [0] * 12
        a = sorted(keyResults)
        a.reverse()
    
        ''' Return pairs, the pitch class and the point value, in order by point value
        '''
        for i in range(len(a)):
            likelyKeys[i] = (Pitch(keyResults.index(a[i])), a[i])
    
        return likelyKeys
    
    
    def getDifference(self, keyResults, pcDistribution, isMajor=True):
        pass
    
    def getDifferenceDebug(self, keyResults, pcDistribution, isMajor=True):
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
            toneWeights = self.getWeights(True)
        else:
            toneWeights = self.getWeights(False)
        
        profileAverage = float(sum(toneWeights))/len(toneWeights)
        histogramAverage = float(sum(pcDistribution))/len(pcDistribution) 
        
        for i in range(len(soln)):
            for j in range(len(toneWeights)):
                #print "BLAH"
                top[i] = top[i] + ((toneWeights[(j + i) % 12]-profileAverage) * (pcDistribution[j]-histogramAverage))
                #print top[i]
                bottomRight[i] = bottomRight[i] + ((toneWeights[(j+i)%12]-profileAverage)**2)
                #print bottomRight[i]
                bottomLeft[i] = bottomLeft[i] + ((pcDistribution[j]-histogramAverage)**2)
                #print bottomLeft[i]
                soln[i] = float(top[i]) / ((bottomRight[i]*bottomLeft[i])**.5)
                #print soln[i]
        
        print soln
        return soln


    def convoluteDistribution(self, pcDistribution, isMajor=True):
        ''' Takes in a pitch class distribution as a list and convolutes it
            over Sapp's given distribution for finding key, returning the result. 
        '''
        soln = [0] * 12
    
        if isMajor:
            toneWeights = self.getWeights(True)
        else:
            toneWeights = self.getWeights(False)
            
        for i in range(len(soln)):
            for j in range(len(pcDistribution)):
                soln[i] = soln[i] + (toneWeights[(j + i) % 12] * pcDistribution[j])
    
        #print soln  
    
        return soln        


    def runKeyDetect(self, sStream, minWindow):
        # names = [x.id for x in sStream]
    
        ''' key analysis by pitches
        max = self.findLongestPart(sStream)
        
        solutionMatrix = [[0]*(max-minWindow)]*(len(sStream))

        for i in range(len(sStream)):
            print("-----WORKING ON PART ", names[i], "-----")
            part = sStream[i].pitches
            for j in range(minWindow, len(part)):
                print("-----window size ", j, "-----")
                solutionMatrix[i][j-minWindow] = self.windowKeyDetect(j, part) 
        '''
        
        ''' key analysis by measure
        '''
        
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
        
        ''' fill pitch class distribution
        '''
        
        for i in range(max-windowSize + 1):
            current = work.getMeasureRange(i, i+windowSize).pitchAttributeCount('pitchClass')
            pcDist = [0] * 12
            for j in range(12):
                if current.get(j) == None:
                    pcDist[j] = 0
                else:
                    pcDist[j] = current.get(j)
            
            key[i] = self.singleKeyDetect(pcDist)
             
        return key
            
        
    
#===============================================================================
#    def windowKeyDetect(self, windowSize, part):
#        ''' Takes in windows size as argument to run key detection
#        '''
#    
#        key = [0] * (len(part) - windowSize + 1)
#    
#        ''' Run key detection over all possible contiguous windows of a
#            given window size (by pitches)
#            
#        if windowSize > len(part):
#            windowSize = len(part)
#        
#        for i in range(len(part) - windowSize + 1):
#            pitchClassDist = [0] * 12
#            pcGroup = [n.pitchClass for n in part[(0 + i):windowSize + i]]
#            
#            for j in pcGroup:
#                pitchClassDist[j] = pitchClassDist[j] + 1
#                #print("pass", i)
#                #print pitchClassDist
#                #print len(part)
#                
#            key[i] = self.singleKeyDetect(pitchClassDist)
#            #createDistributionGraph(pitchClassDist)
#        '''
#        
# 
#        return key
#===============================================================================

    def singleKeyDetect(self, pcDistribution):    
        ''' Takes in a pitch class distribution and algorithmically detects
            probable keys using convoluteDistribution() and getLikelyKeys()
        '''
    
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        keyResultsMajor = self.convoluteDistribution(pcDistribution, True)
        likelyKeysMajor = self.getLikelyKeys(keyResultsMajor)
        differenceMajor = self.getDifference(keyResultsMajor, pcDistribution, True)
        
        keyResultsMinor = self.convoluteDistribution(pcDistribution, False)   
        likelyKeysMinor = self.getLikelyKeys(keyResultsMinor)
        differenceMinor = self.getDifference(keyResultsMinor, pcDistribution, False)

        if likelyKeysMajor[0][1] > likelyKeysMinor[0][1]:
            likelyKey = (likelyKeysMajor[0][0], "Major")
        else:
            likelyKey = (likelyKeysMinor[0][0], "Minor")
        
        #print "Key probabilities ordered by pitch class:", keyResults
        #print keySorted
        #print "Possible keys, from most likely to least likely", likelyKeys
    
        #print("Key of analyzed segment:", likelyKeys[0], "(runners up", likelyKeys[1], "and", likelyKeys[2], ")")
        #return [likelyKeys[0], likelyKeys[1], difference]
        
        return likelyKey


    def createDistributionGraph(self, pcDistribution):
        ''' Takes a distribution of pitch classes and creates a bar graph
        '''
        x = arange(12)
        ax = subplot(111)
        bar(x, pcDistribution)
    
        xticks(x + 0.4, ('C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B'))

        show()

    
class MajorMinor(object):
    pass

#------------------------------------------------------------------------------

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testKeyDetect(self):
        sStream = corpus.parseWork('schubert/d576')
        a = KeyDetect(sStream)
        a.runKeyDetect(sStream, 1)
        


#------------------------------------------------------------------------------

if (__name__ == "__main__"):
    music21.mainTest(Test, TestExternal)
    
