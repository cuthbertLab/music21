#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         windowedAnalysis.py
# Purpose:      Framework for modular, windowed analysis, as well as individual
#               classes of analytical procedures
#
# Authors:      Jared Sadoian
# Authors:      Christopher Ariza
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
        '''Create a WindowedAnalysis object.

        The provided `analysisProcessor` must provide a `process()` method that, when given a windowed Stream (a Measure) returns two element tuple containing (a) a data value (implementation dependent) and (b) a color code. 
        '''
        self.processor = analysisProcessor
        #environLocal.printDebug(self.processor)
        if 'Stream' not in streamObj.classes:
            raise WindowedAnalysisException, 'non-stream provided as argument'

        self._srcStream = streamObj
        # store a windowed Stream, partitioned into bars of 1/4
        self._windowedStream = self._getMinimumWindowStream() 

    def _getMinimumWindowStream(self):
        ''' Take the loaded stream and restructure it into measures of 1 quarter note duration.

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324')
        >>> p = SadoianAmbitus()
        >>> # placing one part into analysis
        >>> wa = WindowedAnalysis(s.parts[0], p)

        >>> post = wa._getMinimumWindowStream()
        >>> len(post.measures)
        42
        >>> post.measures[0]
        <music21.stream.Measure 1 offset=0.0>
        >>> post.measures[0].timeSignature # set to 1/4 time signature
        <music21.meter.TimeSignature 1/4>
        >>> len(post.measures[1].notes) # one note in this measures 
        1
        '''
        # create a stream that contains just a 1/4 time signature; this is 
        # the minimum window size (and partitioning will be done by measure)
        meterStream = stream.Stream()
        meterStream.insert(0, meter.TimeSignature('1/4'))
        
        # makeTies() splits the durations into proper measure boundaries for 
        # analysis; this means that a duration that spans multiple 1/4 measures
        # will be represented in each of those measures
        return self._srcStream.makeMeasures(meterStream).makeTies(inPlace=True)


    def _analyze(self, windowSize):
        ''' Calls, for a given window size, an analysis method across all windows in the source Stream. Windows above size 1 are always overlapped, so if a window of size 2 is used, windows 1-2, then 2-3, then 3-4 are compared. If a window of size 3 is used, windows 1-3, then 2-4, then 3-5 are compared. 

        Windows are assumed to be partitioned by :class:`music21.stream.Measure` objects.

        Returns two lists for results, each equal in size to the length of minimum windows minus the window size plus one. If we have 20 1/4 windows, then the results lists will be of length 20 for window size 1, 19 for window size 2, 18 for window size 3, etc. 

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = SadoianAmbitus()
        >>> wa = WindowedAnalysis(s, p)
        >>> len(wa._windowedStream)
        39
        >>> a, b = wa._analyze(1)
        >>> len(a), len(b)
        (39, 39)

        >>> a, b = wa._analyze(4)
        >>> len(a), len(b)
        (36, 36)

        '''
        max = len(self._windowedStream.getElementsByClass('Measure'))
        data = [0] * (max - windowSize + 1)
        color = [0] * (max - windowSize + 1)               
        
        for i in range(max-windowSize + 1):
            # getting a range of Measures to be used as windows
            # for getMeasureRange(), collect is set to [] so that clefs, timesignatures, and other objects are not gathered. 

            # a flat representation removes all Streams, returning only 
            # Notes, Chords, etc.
            current = self._windowedStream.getMeasureRange(i, 
                      i+windowSize, collect=[]).flat
            # current is a Stream for analysis
            data[i], color[i] = self.processor.process(current)
             
        return data, color

        
    def process(self, minWindow=1, maxWindow=1, windowStepSize=1):

        ''' Main method for windowed analysis across one or more window size.

        Calls :meth:`~music21.analysis.WindowedAnalysis._analyze` for 
        the number of different window sizes to be analyzed.

        The `minWindow` and `maxWindow` set the range of window sizes in quarter lengths. The `windowStepSize` parameter determines the the increment between these window sizes, in quarter lengths. 

        If `minWindow` or `maxWindow` is None, the largest window size available will be set. 

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324')
        >>> p = KrumhanslSchmuckler()
        >>> # placing one part into analysis
        >>> wa = WindowedAnalysis(s[0], p)
        >>> x, y, z = wa.process(1, 1)
        >>> len(x) # we only have one series of windows
        1
        >>> x[0][0], y[0][0] # for each window, we get a solution and a color
        (('B', 'major', 0.6868258874056411), '#FF8000')

        >>> x, y, z = wa.process(1, 2)
        >>> len(x) # we have two series of windows
        2

        >>> x[0][0] # the data returned is processor dependent; here we get
        ('B', 'major', 0.6868258874056411)
        >>> y[0][0] # a color is returned for each matching data position
        '#FF8000'
        '''
        # names = [x.id for x in sStream]
                
        #max = len(sStream[0].measures)
        if maxWindow == None:
            max = len(self._windowedStream)
        else:
            max = maxWindow

        if minWindow == None:
            min = len(self._windowedStream)
        else:
            min = minWindow
        
        # need to create storage for the output of each row, or the processing
        # of all windows of a single size across the entire Stream
        solutionMatrix = [] 
        colorMatrix = [] 
        # store meta data about each row as a dictionary
        metaMatrix = [] 

        for i in range(min, max+1, windowStepSize):
            environLocal.printDebug(['processing window:', i])
            # each of these results are lists, where len is based on 
            soln, colorn = self._analyze(i) 
            # store lists of results in a list of lists
            solutionMatrix.append(soln)
            colorMatrix.append(colorn)
            meta = {'windowSize': i}
            metaMatrix.append(meta)
        
        return solutionMatrix, colorMatrix, metaMatrix



#------------------------------------------------------------------------------
class DiscreteAnalysisException(Exception):
    pass

class DiscreteAnalysis(object):
    ''' Parent class for analytical methods.

    Each analytical method returns a discrete numerical (or other) results as well as a color. Colors can be used in mapping output.

    Analytical methods may make use of a `referenceStream` to configure the processor on initialization. 
    '''
    def __init__(self, referenceStream=None):
        # store a reference stream if needed
        self._referenceStream = referenceStream

    def _rgbToHex(self, rgb):
        '''Utility conversion method
        '''
        return '#%02x%02x%02x' % rgb    

    def possibleResults(self):
        '''A list of pairs showing all discrete results and the assigned color.
        '''
        pass
    
    def solutionToColor(self, result):
        '''Given a analysis specific result, return the appropriate color. Must be able to handle None in the case that there is no result.
        '''
        pass
    
    def process(self, subStream):
        '''For a given Stream, apply the analysis to all components of this Stream.
        '''
        pass


    def getSolution(self, subStream):
        '''For a given Stream, apply the analysis and return the best solution.
        '''
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
        self._majorKeyColors = {'Eb':'#D60000',
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
        self._minorKeyColors = {'Eb':'#720000',
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
    

    def _getWeights(self, weightType='major'): 
        ''' Returns either the a weight key profile as described by Sapp and others
            
        >>> a = KrumhanslSchmuckler()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        if weightType == 'major':
            return [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        elif weightType == 'minor':
            return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)

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


    def _convoluteDistribution(self, pcDistribution, weightType='major'):
        ''' Takes in a pitch class distribution as a list and convolutes it
            over Sapp's given distribution for finding key, returning the result. 
        '''
        soln = [0] * 12
        
        toneWeights = self._getWeights(weightType)
                
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
        
        
    def _getDifference(self, keyResults, pcDistribution, weightType):
        ''' Takes in a list of numerical probably key results and returns the
            difference of the top two keys
        '''
            
        soln = [0]*12
        top = [0]*12
        bottomRight = [0]*12
        bottomLeft = [0]*12
            
        toneWeights = self._getWeights(weightType)

        profileAverage = float(sum(toneWeights))/len(toneWeights)
        histogramAverage = float(sum(pcDistribution))/len(pcDistribution) 
            
        for i in range(len(soln)):
            for j in range(len(toneWeights)):
                top[i] = top[i] + ((
                    toneWeights[(j - i) % 12]-profileAverage) * (
                    pcDistribution[j]-histogramAverage))

                bottomRight[i] = bottomRight[i] + ((
                    toneWeights[(j-i)%12]-profileAverage)**2)

                bottomLeft[i] = bottomLeft[i] + ((
                    pcDistribution[j]-histogramAverage)**2)

                if (bottomRight[i] == 0 or bottomLeft[i] == 0):
                    soln[i] = 0
                else:
                    soln[i] = float(top[i]) / ((bottomRight[i]*bottomLeft[i])**.5)
        return soln    

    def possibleResults(self):
        ''' TODO: returns a list of possible results for the creation of a legend
        '''
        pass
    
    def solutionToColor(self, solution):
        '''For a given solution, return the color. Use the stored color information in the __init__ method to assign a color for a given result.
        '''
        key = solution[0]
        modality = solution[1]
        if modality == "major":
            return self._majorKeyColors[str(key)]
        elif modality == "minor":
            return self._minorKeyColors[str(key)]
        
    
    def getSolution(self, sStream):
        ''' procedure to only return a text solution
        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = KrumhanslSchmuckler()
        >>> p.getSolution(s) # this seems correct
        ('F#', 'minor', 0.81547089257624916)

        >>> s = corpus.parseWork('bach/bwv57.8')
        >>> p = KrumhanslSchmuckler()
        >>> p.getSolution(s) # should be b- major
        ('A#', 'major', 0.89772788962941652)

        '''
        # always take a flat version here, otherwise likely to get nothing
        solution, color = self.process(sStream.flat)
        return solution
    
    
    def process(self, sStream):    
        ''' Takes in a Stream or sub-Stream and performs analysis on all contents of the Stream. A windowing system can be used to get partial results. 

        Returns two values, a data list and a color string.

        The data list contains a key (as a string), a mode (as a string), and a correlation value (degree of certainty)
        '''
    
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        pcDistribution = self._getPitchClassDistribution(sStream)
    
        keyResultsMajor = self._convoluteDistribution(pcDistribution,'major')
        differenceMajor = self._getDifference(keyResultsMajor, 
                         pcDistribution, 'major')
        likelyKeysMajor = self._getLikelyKeys(keyResultsMajor, differenceMajor)
        

        keyResultsMinor = self._convoluteDistribution(pcDistribution,'minor')   
        differenceMinor = self._getDifference(keyResultsMinor, 
                          pcDistribution, 'minor')
        likelyKeysMinor = self._getLikelyKeys(keyResultsMinor, differenceMinor)
        
        #find the largest correlation value to use to select major or minor as the resulting key
        if likelyKeysMajor[0][1] > likelyKeysMinor[0][1]:
            solution = (str(likelyKeysMajor[0][0]), "major", likelyKeysMajor[0][1])
        else:
            solution = (str(likelyKeysMinor[0][0]), "minor", likelyKeysMinor[0][1])
            
        color = self.solutionToColor(solution)
        return solution, color        
    



class SadoianAmbitus(DiscreteAnalysis):
    '''An basic analysis method for measuring register. 
    '''
    def __init__(self, referenceStream=None):
        DiscreteAnalysis.__init__(self, referenceStream=referenceStream)
        self.pitchSpanColors = {}
        self._generateColors()

    def _generateColors(self, numColors=None):
        '''Provide uniformly distributed colors across the entire range.
        '''
        if numColors == None:
            if self._referenceStream != None:
                # get total range for entire piece
                min, max = self._getPitchRanges(self._referenceStream)
            else:
                min, max = 0, 130 # a large default
        else: # create min max
            min, max = 0, numColors

        valueRange = max - min
        step = 0
        for i in range(min, max+1):
            val = int(round((255.0 / valueRange) * step))
            # store in dictionary the accepted values, not the step
            self.pitchSpanColors[i] = self._rgbToHex((val, val, val))
            step += 1

        #environLocal.printDebug([self.pitchSpanColors])
    
    def _getPitchSpan(self, subStream):
        '''For a given subStream, return a value in half-steps of the range

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = SadoianAmbitus()
        >>> p._getPitchSpan(s.parts[0].getElementsByClass('Measure')[3])
        (66, 71)
        >>> p._getPitchSpan(s.parts[0].getElementsByClass('Measure')[6])
        (69, 73)

        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p._getPitchSpan(s)
        (45, 108)
        '''
        
        if len(subStream.flat.notes) == 0:
            # need to handle case of no pitches
            return None

        # find the min and max pitch space value for all pitches
        psFound = []
        for n in subStream.flat.notes:
            pitches = []
            if 'Chord' in n.classes:
                pitches = n.pitches
            elif 'Note' in n.classes:
                pitches = [n.pitch]

            psFound += [p.ps for p in pitches]
        # use built-in functions
        return int(min(psFound)), int(max(psFound))

    
    def _getPitchRanges(self, subStream):
        '''For a given subStream, return the smallest difference between any two pitches and the largest difference between any two pitches. This is used to get the smallest and larges ambitus possible in a given work. 

        >>> from music21 import *
        >>> p = SadoianAmbitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p._getPitchSpan(s)
        (45, 108)
        >>> p._getPitchRanges(s)
        (26, 63)

        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p._getPitchRanges(s)
        (0, 34)
        '''
        psFound = []
        for n in subStream.flat.notes:
            pitches = []
            if 'Chord' in n.classes:
                pitches = n.pitches
            elif 'Note' in n.classes:
                pitches = [n.pitch]
            for p in pitches:
                psFound.append(p.ps)
        psFound.sort()
        psRange = []
        for i in range(len(psFound)-1):
            p1 = psFound[i]
            for j in range(i+1, len(psFound)):
                p2 = psFound[j]
                # p2 should always be equal or greater than p1
                psRange.append(p2-p1)

        return int(min(psRange)), int(max(psRange))


    def solutionToColor(self, result):
        '''
        >>> from music21 import *
        >>> p = SadoianAmbitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> min, max = p._getPitchSpan(s)
        >>> p.solutionToColor(max-min)
        '#7c7c7c'
        '''    
        # a result of None may be possible
        if result == None:
            return self._rgbToHex((0, 128, 0))

        return self.pitchSpanColors[result]
    
    
    def process(self, sStream):
        post = self._getPitchSpan(sStream)
        if post != None:
            soln = post[1] - post[0] # max-min
        else:
            soln = None
        color = self.solutionToColor(soln)
        
        return soln, color


    def getSolution(self, sStream):
        ''' procedure to only return a text solution
        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = SadoianAmbitus()
        >>> p.getSolution(s)
        34

        '''
        solution, color = self.process(sStream)
        return solution
    


#------------------------------------------------------------------------------

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()

