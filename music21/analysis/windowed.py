#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         windowed.py
# Purpose:      Framework for modular, windowed analysis
#
# Authors:      Jared Sadoian
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module describes classes for performing windowed and overlapping windowed analysis. The :class:`music21.analysis.windowed.WindowedAnalysis` provides a reusable framework for systematic overlapping window analysis at the starting at the level of the quarter note and moving to the size of an entire :class:`music21.stream.Stream`.

Modular analysis procedures inherit from :class:`music21.analysis.discrete.DiscreteAnalysis`. The :class:`music21.analysis.discrete.KrumhanslSchmuckler` (for algorithmic key detection) and :class:`music21.analysis.discrete.SadoianAmbitus` (for pitch range analysis) classes provide examples.
'''


import unittest, doctest, random
import sys
import math

import music21

from music21 import meter
from music21.pitch import Pitch
from music21 import stream 


from music21 import environment
_MOD = 'windowed.py'
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

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv324')
        >>> p = analysis.discrete.SadoianAmbitus()
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

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = analysis.discrete.SadoianAmbitus()
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
        # assuming that this is sorted
        mStream = self._windowedStream #.getElementsByClass('Measure')
        max = len(mStream)
        data = [0] * (max - windowSize + 1)
        color = [0] * (max - windowSize + 1)               
        
        for i in range(max-windowSize + 1):
            # getting a range of Measures to be used as windows
            # for getMeasureRange(), collect is set to [] so that clefs, timesignatures, and other objects are not gathered. 

            #environLocal.printDebug(['_analyzes(), i:', i, 'i+windowSize:', i+windowSize])
            # a flat representation removes all Streams
            current = stream.Stream()
            for j in range(i, i+windowSize):
                #environLocal.printDebug(['_analyzes(), j', j])
                current.append(mStream[j])
            current = current.flat.notes

            # using getMeasureRange() is problematic
#             current = self._windowedStream.getMeasureRange(i, 
#                       i+windowSize, collect=[]).flat

            # current is a Stream for analysis
            data[i], color[i] = self.processor.process(current)
             
        return data, color

        
    def process(self, minWindow=1, maxWindow=1, windowStepSize=1, 
                includeTotalWindow=True):

        ''' Main method for windowed analysis across one or more window size.

        Calls :meth:`~music21.analysis.WindowedAnalysis._analyze` for 
        the number of different window sizes to be analyzed.

        The `minWindow` and `maxWindow` set the range of window sizes in quarter lengths. The `windowStepSize` parameter determines the the increment between these window sizes, in quarter lengths. 

        If `minWindow` or `maxWindow` is None, the largest window size available will be set. 

        If `includeTotalWindow` is True, the largest window size will always be added. 

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv324')
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> # placing one part into analysis
        >>> wa = WindowedAnalysis(s[0], p)
        >>> x, y, z = wa.process(1, 1, includeTotalWindow=False)
        >>> len(x) # we only have one series of windows
        1

        >>> y[0][0].startswith('#') # for each window, we get a solution and a color
        True
        >>> x[0][0][0] 
        'B'

        >>> x, y, z = wa.process(1, 2, includeTotalWindow=False)
        >>> len(x) # we have two series of windows
        2

        >>> x[0][0] # the data returned is processor dependent; here we get
        ('B', 'major', 0.6868258874056411)
        >>> y[0][0].startswith('#') # a color is returned for each matching data position
        True
        '''
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

        windowSizes = range(min, max+1, windowStepSize)
        if includeTotalWindow:
            totalWindow = len(self._windowedStream)
            if totalWindow not in windowSizes:
                windowSizes.append(totalWindow)

        for i in windowSizes:
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
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

class TestMockProcesor(object):
    
    def process(self, subStream):
        '''Simply count the number of notes found
        '''
        return len(subStream.notes), None
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import corpus
        from music21.analysis import discrete
        # get a procedure 
        
        s = corpus.parseWork('bach/bwv324')

        for pClass in [discrete.KrumhanslSchmuckler, discrete.SadoianAmbitus]:
            p = pClass()

            # get windowing object, provide a stream for analysis as well as 
            # the processor
            wa = WindowedAnalysis(s, p)
            # do smallest and larges
            for i in range(1, 4) + [None]:
                x, y, z = wa.process(i, i)
    

    def testWindowing(self):
        '''Test that windows are doing what they are supposed to do 
        '''
        p = TestMockProcesor()

        from music21 import stream, note
        s1 = stream.Stream()
        s1.append(note.Note('c'))
        s1.append(note.Note('c'))

        s2 = stream.Stream()
        s2.append(note.Note('c'))
        s2.append(note.Note('d'))
        s2.append(note.Note('e'))
        s2.append(note.Note('f'))
        s2.append(note.Note('g'))
        s2.append(note.Note('a'))
        s2.append(note.Note('b'))
        s2.append(note.Note('c'))

        wa1= WindowedAnalysis(s1, p)
        wa2= WindowedAnalysis(s2, p)

        # windows partitioned at quarter length
        self.assertEqual(len(wa1._windowedStream), 2)
        self.assertEqual(len(wa2._windowedStream), 8)


        # window size of 1 gets 2 solutions
        a, b, c = wa1.process(1, 1, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 2) 
        self.assertEqual(a[0][0], 1)
        self.assertEqual(a[0][1], 1)

        # window size of 2 gets 1 solution
        a, b, c = wa1.process(2, 2, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 1)
        # two items in this window
        self.assertEqual(a[0][0], 2)


        # window size of 1 gets 8 solutiions
        a, b, c = wa2.process(1, 1, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 8)
        self.assertEqual(a[0][0], 1)
        self.assertEqual(a[0][1], 1)

        # window size of 2 gets 7 solutions
        a, b, c = wa2.process(2, 2, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 7)

        # window size of 7 gets 2 solutions
        a, b, c = wa2.process(7, 7, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 2)

        # window size of 8 gets 1 solutions
        a, b, c = wa2.process(8, 8, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 1)


#------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()

        a.testWindowing()