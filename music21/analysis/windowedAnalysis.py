#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         windowedAnalysis.py
# Purpose:      Framework for modular, windowed analysis, as well as individual
#               classes of analytical procedures
#
# Authors:      Jared Sadoian
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest, random
import sys
import math

import music21

from music21 import meter
from music21.pitch import Pitch
from music21 import stream 


from music21 import environment
_MOD = 'windowedAnalysis.py'
environLocal = environment.Environment(_MOD)

#------------------------------------------------------------------------------

class WindowedAnalysisException(Exception):
    pass


#------------------------------------------------------------------------------

class WindowedAnalysis(object):
    def __init__(self, streamObj, analysisProcessor):
        self.processor = analysisProcessor
        #environLocal.printDebug(self.processor)
        if not isinstance(streamObj, music21.stream.Stream):
            raise WindowedAnalysisException, 'non-stream provided as argument'
        self.streamObj = streamObj

    def _prepWindow(self):
        ''' Take the loaded stream and restructure it into measures of 1 quarter note duration

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324')
        >>> p = SadoianAmbitus()
        >>> # placing one part into analysis
        >>> wa = WindowedAnalysis(s[0], p)
        >>> post = wa._prepWindow()
        >>> len(post.measures)
        42
        >>> len(post.measures[0])
        6
        >>> len(post.measures[1])
        1
        '''
        meterStream = stream.Stream()
        meterStream.insert(0, meter.TimeSignature('1/4'))
        
        # makeTies() splits the durations into proper measure boundaries for analysis
        return self.streamObj.makeMeasures(meterStream).makeTies(inPlace=True)


    def _singleWindowAnalysis(self, windowSize, windowedStream):
        ''' Handles calling single window analysis method for each window of a particular window size. 

        Windows are assumed to be partitioned by :class:`music21.stream.Measure` objects.
        '''
        max = len(windowedStream.measures)
        data = [0] * (max - windowSize + 1)
        color = [0] * (max - windowSize + 1)               
        
        for i in range(max-windowSize + 1):
            # getting a range of Measures to be used as windows
            # collect is set to [] so that clefs, timesignatures, and other
            # objects are not gathered. 
            # a flat representation removes all Streams, returning only 
            # Notes, Chords, etc.
            current = windowedStream.getMeasureRange(i, 
                      i+windowSize, collect=[]).flat
            # current is a Stream for analysis
            data[i], color[i] = self.processor.process(current)
             
        return data, color

        
    def process(self, minWindow=1, maxWindow=1, windowStepSize=1,
        rawData=False):
        ''' Main function call to start windowed analysis routine. Calls :meth:`~music21.WindowedAnalysis.GeneralNote._singleWindowAnalysis` for the number of different window sizes to be analyzed.

        The `minWindow` and `maxWindow` set the range of window sizes in quarter lengths. The `windowStepSize` parameter determines the the increment between these window sizes, in quarter lengths. 

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324')
        >>> p = KrumhanslSchmuckler()
        >>> # placing one part into analysis
        >>> wa = WindowedAnalysis(s[0], p)
        >>> x, y = wa.process(1, 1)
        >>> len(x) # we only have one series of windows
        1
        >>> x, y = wa.process(1, 2)
        >>> len(x) # we have two series of windows
        2
        >>> x[0][0] # the data returned is processor dependent; here we get
        ('B', 'Major', 0.6868258874056411)
        >>> y[0][0] # a color is returned for each matching data position
        '#FF8000'
        '''
        # names = [x.id for x in sStream]
        
        windowedStream = self._prepWindow()
        
        #max = len(sStream[0].measures)
        if maxWindow < 1:
            max = len(windowedStream)
        else:
            max = maxWindow
        
        #array set to the size of the expected resulting set
        solutionSize = (max-minWindow+1) / windowStepSize

        # create empty arrays for storage
        solutionMatrix = [0] * solutionSize
        color = [0] * solutionSize
        for i in range(minWindow, max+1, windowStepSize):
            # where to add data in the solution vectors
            pos = (i-minWindow)/windowStepSize

            environLocal.printDebug(['processing window:', i, 
                                     'storing data:', pos])

            soln, colorn = self._singleWindowAnalysis(i, windowedStream) 
            if pos >= solutionSize:
                environLocal.printDebug(['cannot fit data; position, solutionSize', pos, solutionSize])
            else:
                solutionMatrix[pos] = soln
                color[pos] = colorn
        
        return solutionMatrix, color


    


#------------------------------------------------------------------------------

class DiscreteAnalysis(object):
    ''' Parent class for single analytical methods
    '''
    def __init__(self):
        pass
    
    def possibleResults(self):
        pass
    
    def resultsToColor(self, result):
        pass
    
    def process(self, subStream):
        pass

#------------------------------------------------------------------------------

class KrumhanslSchmuckler(DiscreteAnalysis):
    ''' Implementation of the Krumhansl-Schmuckler key determination algorithm
    '''
    def __init__(self):
        DiscreteAnalysis.__init__(self)
        
        # store color grid information to associate particular keys to colors
        
        # note: these colors were manually selected to optimize distinguishing
        # characteristics. do not change without good reason
        self.majorKeyColors = {'Eb':'#D60000',
                 'E':'#FF0000',
                 'E#':'#FF2B00',
                 'B-':'#FF5600',
                 'B':'#FF8000',
                 'B#':'#FFAB00',
                 'F-':'#FFFD600',
                 'F':'#FFFF00',
                 'F#':'#AAFF00',
                 'C-':'#55FF00',
                 'C':'#00FF00',
                 'C#':'#00AA55',
                 'G-':'#0055AA',
                 'G':'#0000FF',
                 'G#':'#2B00FF',
                 'D-':'#5600FF',
                 'D':'#8000FF',
                 'D#':'#AB00FF',
                 'A-':'#D600FF',
                 'A':'#FF00FF',
                 'A#':'#FF55FF'}
        self.minorKeyColors = {'Eb':'#720000',
                 'E':'#9b0000',
                 'E#':'#9b0000',
                 'B-':'#9b0000',
                 'B':'#9b2400',
                 'B#':'#9b4700',
                 'F-':'#9b7200',
                 'F':'#9b9b00',
                 'F#':'#469b00',
                 'C-':'#009b00',
                 'C':'#009b00',
                 'C#':'#004600',
                 'G-':'#000046',
                 'G':'#00009B',
                 'G#':'#00009B',
                 'D-':'#00009b',
                 'D':'#24009b',
                 'D#':'#47009b',
                 'A-':'#72009b',
                 'A':'#9b009b',
                 'A#':'#9b009b'}
    
    def _getWeights(self, isMajor): 
        ''' Returns either the major or minor key profile as described by Sapp
            
        >>> a = KrumhanslSchmuckler()
        >>> a._getWeights(True)
        [6.3499999999999996, 2.3300000000000001, 3.48, 2.3300000000000001, 4.3799999999999999, 4.0899999999999999, 2.52, 5.1900000000000004, 2.3900000000000001, 3.6600000000000001, 2.29, 2.8799999999999999]
        >>> a._getWeights(False)
        [6.3300000000000001, 2.6800000000000002, 3.52, 5.3799999999999999, 2.6000000000000001, 3.5299999999999998, 2.54, 4.75, 3.98, 2.6899999999999999, 3.3399999999999999, 3.1699999999999999]
            
        '''
        
        if isMajor:
            return [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        else:
            return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]    


    def _getPitchClassDistribution(self, streamObj):
        '''Given a flat Stream, obtain a pitch class distribution. The value of each pitch class is scaled by its duration in quarter lengths.

        >>> from music21 import note, stream, chord
        >>> a = KrumhanslSchmuckler()
        >>> s = stream.Stream()
        >>> n1 = note.Note('c')
        >>> n1.quarterLength = 3
        >>> n2 = note.Note('f#')
        >>> n2.quarterLength = 2
        >>> s.append(n1)
        >>> s.append(n2)
        >>> a._getPitchClassDistribution(s)
        [3, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
        >>> c1 = chord.Chord(['d', 'e', 'b-'])
        >>> c1.quarterLength = 1.5
        >>> s.append(c1)
        >>> a._getPitchClassDistribution(s)
        [3, 0, 1.5, 0, 1.5, 0, 2, 0, 0, 0, 1.5, 0]
        '''
        pcDist = [0]*12
        
        for n in streamObj.notes:        
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
            toneWeights = self._getWeights(True)
        else:
            toneWeights = self._getWeights(False)
                
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
        
        #Return pairs, the pitch class and the correlation value, in order by point value
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
            toneWeights = self._getWeights(True)
        else:
            toneWeights = self._getWeights(False)
            
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
        ''' TODO: returns a list of possible results for the creation of a legend
        '''
        pass
    
    def resultsToColor(self, key, modality):
        ''' use the stored color information in the __init__ method to assign a color for a given result
        '''
        if modality == "Major":
            return self.majorKeyColors[str(key)]
        else:
            return self.minorKeyColors[str(key)]
        
    
    def getResult(self, sStream):
        ''' procedure to only return a text solution
        '''
        soln = self.process(sStream)
        return soln[0]
    
    
    def process(self, sStream):    
        ''' Takes in a Stream and algorithmically detects
            probable keys using convoluteDistribution() and getLikelyKeys()
        '''
    
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        pcDistribution = self._getPitchClassDistribution(sStream)
    
        keyResultsMajor = self._convoluteDistribution(pcDistribution, True)
        differenceMajor = self._getDifference(keyResultsMajor, 
                         pcDistribution, True)
        likelyKeysMajor = self._getLikelyKeys(keyResultsMajor, differenceMajor)
        
        keyResultsMinor = self._convoluteDistribution(pcDistribution, False)   
        differenceMinor = self._getDifference(keyResultsMinor, 
                          pcDistribution, False)
        likelyKeysMinor = self._getLikelyKeys(keyResultsMinor, differenceMinor)
        
        #find the largest correlation value to use to select major or minor as the resulting key
        if likelyKeysMajor[0][1] > likelyKeysMinor[0][1]:
            likelyKey = (str(likelyKeysMajor[0][0]), "Major", likelyKeysMajor[0][1])
        else:
            likelyKey = (str(likelyKeysMinor[0][0]), "Minor", likelyKeysMinor[0][1])
            
        color = self.resultsToColor(likelyKey[0], likelyKey[1])
        return likelyKey, color        
    




class SadoianAmbitus(DiscreteAnalysis):
    '''An basic analysis method for measuring register. 
    '''
    def __init__(self):
        DiscreteAnalysis.__init__(self)
        self.pitchSpanColors = {}
        self._generateColors(130)


    def _rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % rgb    
    
    def _generateColors(self, numColors):
        
        for i in range(numColors):
            val = 0
            val = (255.0/numColors)*i
            self.pitchSpanColors[i] = self._rgb_to_hex((val, val, val))
            
    
    def _getPitchSpan(self, work):
        soln = 0
        max = 0
        min = 10000000000
        
        for n in work.notes:        
            if not n.isRest:
                if n.isChord:
                    for m in n.pitches:
                        if m.ps > max:
                            max = m.ps
                        elif m.ps < min:
                            min = m.ps
                else:
                    if n.ps > max:
                        max = n.ps
                    elif n.ps < min:
                        min = n.ps
        
        return (max - min)

    
    def resultsToColor(self, result):
        return self.pitchSpanColors[result]
    
    
    def process(self, sStream):
        soln = self._getPitchSpan(sStream)
        color = self.resultsToColor(soln)
        
        return soln, color


#------------------------------------------------------------------------------

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------

if (__name__ == "__main__"):
    import doctest
    doctest.testmod()
    music21.mainTest(Test, TestExternal)
    
