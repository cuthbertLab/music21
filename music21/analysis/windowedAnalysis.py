#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         keyAnalysis.py
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
from music21 import meter
from music21 import stream
from music21.note import Note
from music21.pitch import Pitch
from music21.stream import Stream
from pylab import *


from music21 import environment
_MOD = 'keyAnalysis.py'
environLocal = environment.Environment(_MOD)
#environLocal['directoryScratch'] = 'C:/Users/Jared/Desktop'
#environLocal.write()

#------------------------------------------------------------------------------
# utility functions


#def findLongestPart(sStream):
#    ''' temporary function to find the longest part (based on the number
#        of pitches) in a parsed work.
#    '''
#    max = 0
#    for i in range(len(sStream)):
#        check = len(sStream[i].pitches)
#        if check > max:
#            max = check
#    return max
    
    


#------------------------------------------------------------------------------

class KeyAnalysisException(Exception):
    pass


#------------------------------------------------------------------------------

class WindowedAnalysis(object):
    def __init__(self, streamObj):
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyAnalysisException, 'non-stream provided as argument'
        self.streamObj = streamObj

    def _getWindow(self, sStream):
        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('1/4'))
        
        return sStream.makeMeasures(meterStream).makeTies()
        
    def process(self, sStream, minWindow):
        # names = [x.id for x in sStream]
        
        windowedStream = self.getWindow(sStream)
        
        #max = len(sStream[0].measures)
        max = len(windowedStream)
        
        solutionMatrix = [0]*(max-minWindow+1)
        
        print("-----WORKING... window-----")
        for i in range(minWindow, max+1):
            print(i)
            solutionMatrix[i-minWindow] = self.windowKeyAnalysis(i, windowedStream) 
        
        
        return solutionMatrix


    def windowKeyAnalysis(self, windowSize, windowedStream):
        
        max = len(windowedStream.measures)
        key = [0] * (max - windowSize + 1)                
        
        for i in range(max-windowSize + 1):    
            key[i] = self.processWindow(windowedStream, i, windowSize)
             
        return key


#------------------------------------------------------------------------------

class DiscreteAnalysis(object):
    def __init__(self, streamObj):
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyAnalysisException, 'non-stream provided as argument'
    def possibleResults(self):
        pass
    
    def resultsToColor(self, result):
        pass
    
    def process(self, subStream):
        pass


#------------------------------------------------------------------------------    

class PitchAnalysis(object):
    
    def __init__(self, streamObj):
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyAnalysisException, 'non-stream provided as argument'
        self.streamObj = streamObj
    
    def doPitchAnalysis(self, sStream, module):
        pass


#------------------------------------------------------------------------------

class KrumhanslSchmuckler(DiscreteAnalysis):
    
    def __init__(self, streamObj):
        DiscreteAnalysis.init(self, streamObj)
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyAnalysisException, 'non-stream provided as argument'
        self.streamObj = streamObj
    
    def _getWeights(self, isMajor): 
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


    def _getPitchClassDistribution(self, work, start, windowSize):
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


    def _convoluteDistribution(self, pcDistribution, isMajor=True):
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
                soln[i] = soln[i] + (toneWeights[(j - i) % 12] * pcDistribution[j])
            
        return soln  
    
    def _getLikelyKeys(self, keyResults, differences):
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
        
        
    def _getDifference(self, keyResults, pcDistribution, isMajor=True):
        ''' Takes in a list of numerical probably key results and returns the
            difference of the top two keys
        '''
            
        soln = [0]*12
        top = [0]*12
        bottomRight = [0]*12
        bottomLeft = [0]*12
            
        if isMajor:
            toneWeights = self.getWeights(True)
        else:
            toneWeights = self.getWeights(False)
            
        profileAverage = float(sum(toneWeights))/len(toneWeights)
        histogramAverage = float(sum(pcDistribution))/len(pcDistribution) 
            
        for i in range(len(soln)):
            for j in range(len(toneWeights)):
                top[i] = top[i] + ((toneWeights[(j - i) % 12]-profileAverage) * (pcDistribution[j]-histogramAverage))
                bottomRight[i] = bottomRight[i] + ((toneWeights[(j-i)%12]-profileAverage)**2)
                bottomLeft[i] = bottomLeft[i] + ((pcDistribution[j]-histogramAverage)**2)
                if (bottomRight[i] == 0 or bottomLeft[i] == 0):
                    soln[i] = 0
                else:
                    soln[i] = float(top[i]) / ((bottomRight[i]*bottomLeft[i])**.5)
                
        return soln    
        
    def possibleResults(self):
        pass
    
    def resultsToColor(self, key, modality):
        majorKeyColors = {'Eb':'#D60000',
                 'E':'#FF0000',
                 'E#':'#FF2B00',
                 'Bb':'#FF5600',
                 'B':'#FF8000',
                 'B#':'#FFAB00',
                 'Fb':'#FFFD600',
                 'F':'#FFFF00',
                 'F#':'#AAFF00',
                 'Cb':'#55FF00',
                 'C':'#00FF00',
                 'C#':'#00AA55',
                 'Gb':'#0055AA',
                 'G':'#0000FF',
                 'G#':'#2B00FF',
                 'Db':'#5600FF',
                 'D':'#8000FF',
                 'D#':'#AB00FF',
                 'Ab':'#D600FF',
                 'A':'#FF00FF',
                 'A#':'#FF55FF'}
        minorKeyColors = {'Eb':'#720000',
                 'E':'#9b0000',
                 'E#':'#9b0000',
                 'Bb':'#9b0000',
                 'B':'#9b2400',
                 'B#':'#9b4700',
                 'Fb':'#9b7200',
                 'F':'#9b9b00',
                 'F#':'#469b00',
                 'Cb':'#009b00',
                 'C':'#009b00',
                 'C#':'#004600',
                 'Gb':'#000046',
                 'G':'#00009B',
                 'G#':'#00009B',
                 'Db':'#00009b',
                 'D':'#24009b',
                 'D#':'#47009b',
                 'Ab':'#72009b',
                 'A':'#9b009b',
                 'A#':'#9b009b'}

        if modality == "Major":
            return majorKeyColors[str(key)]
        else:
            return minorKeyColors[str(key)]
 
    
    def processWindow(self, windowedStream, i, windowSize):    
        ''' Takes in a pitch class distribution and algorithmically detects
            probable keys using convoluteDistribution() and getLikelyKeys()
        '''
    
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        pcDistribution = self.getPitchClassDistribution(windowedStream, i, windowSize)
    
        keyResultsMajor = self.convoluteDistribution(pcDistribution, True)
        differenceMajor = self.getDifference(keyResultsMajor, pcDistribution, True)
        likelyKeysMajor = self.getLikelyKeys(keyResultsMajor, differenceMajor)
        
        keyResultsMinor = self.convoluteDistribution(pcDistribution, False)   
        differenceMinor = self.getDifference(keyResultsMinor, pcDistribution, False)
        likelyKeysMinor = self.getLikelyKeys(keyResultsMinor, differenceMinor)
        

        ''' find the largest correlation value to use to select major or minor as the resulting key
        '''
        if likelyKeysMajor[0][1] > likelyKeysMinor[0][1]:
            likelyKey = (str(likelyKeysMajor[0][0]), "Major", likelyKeysMajor[0][1])
        else:
            likelyKey = (str(likelyKeysMinor[0][0]), "Minor", likelyKeysMinor[0][1])
        
        return likelyKey        
    
    
class SadoianAmbitus(DiscreteAnalysis):
    
    def __init__(self, streamObj):
        DiscreteAnalysis.init(self, streamObj)
        if not isinstance(streamObj, music21.stream.Stream):
            raise KeyAnalysisException, 'non-stream provided as argument'
        self.streamObj = streamObj
        
    def resultsToColor(self, result):
        pass
    
    def process(self, subStream):
        pass


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
        a = KeyAnalysis(sStream)
        a.runWindowedAnalysis(sStream, 1)
    '''    


#------------------------------------------------------------------------------

if (__name__ == "__main__"):
    import doctest
    doctest.testmod()
    music21.mainTest(Test, TestExternal)
    
