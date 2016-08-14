# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         windowed.py
# Purpose:      Framework for modular, windowed analysis
#
# Authors:      Jared Sadoian
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2010 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module describes classes for performing windowed and overlapping windowed analysis. 
The :class:`music21.analysis.windowed.WindowedAnalysis` provides a reusable framework for 
systematic overlapping window analysis at the starting at the level of the quarter note 
and moving to the size of an entire :class:`music21.stream.Stream`.

Modular analysis procedures inherit from :class:`music21.analysis.discrete.DiscreteAnalysis`. 
The :class:`music21.analysis.discrete.KrumhanslSchmuckler` (for algorithmic key detection) 
and :class:`music21.analysis.discrete.Ambitus` (for pitch range analysis) classes provide examples.
'''
import unittest

from music21 import exceptions21

from music21 import common
from music21 import meter
from music21 import stream 


from music21 import environment
_MOD = 'windowed.py'
environLocal = environment.Environment(_MOD)


#------------------------------------------------------------------------------
class WindowedAnalysisException(exceptions21.Music21Exception):
    pass


#------------------------------------------------------------------------------

class WindowedAnalysis(object):
    def __init__(self, streamObj, analysisProcessor):
        '''Create a WindowedAnalysis object.

        The provided `analysisProcessor` must provide a `process()` method that, 
        when given a windowed Stream (a Measure) returns two element tuple containing 
        (a) a data value (implementation dependent) and (b) a color code. 
        '''
        self.processor = analysisProcessor
        #environLocal.printDebug(self.processor)
        if 'Stream' not in streamObj.classes:
            raise WindowedAnalysisException('non-stream provided as argument')
        self._srcStream = streamObj
        # store a windowed Stream, partitioned into bars of 1/4
        self._windowedStream = self._getMinimumWindowStream() 

    def _getMinimumWindowStream(self, timeSignature='1/4'):
        ''' Take the loaded stream and restructure it into measures of 1 quarter note duration.

        
        >>> s = corpus.parse('bach/bwv324')
        >>> p = analysis.discrete.Ambitus()
        >>> # placing one part into analysis
        >>> wa = analysis.windowed.WindowedAnalysis(s.parts[0], p)

        >>> post = wa._getMinimumWindowStream()
        >>> len(post.getElementsByClass('Measure'))
        42
        >>> post.getElementsByClass('Measure')[0]
        <music21.stream.Measure 1 offset=0.0>
        >>> post.getElementsByClass('Measure')[0].timeSignature # set to 1/4 time signature
        <music21.meter.TimeSignature 1/4>
        >>> len(post.getElementsByClass('Measure')[1].notes) # one note in this measures 
        1
        '''
        # create a stream that contains just a 1/4 time signature; this is 
        # the minimum window size (and partitioning will be done by measure)
        meterStream = stream.Stream()
        meterStream.insert(0, meter.TimeSignature(timeSignature))
        
        # makeTies() splits the durations into proper measure boundaries for 
        # analysis; this means that a duration that spans multiple 1/4 measures
        # will be represented in each of those measures
        measured = self._srcStream.makeMeasures(meterStream)
        # need to make sure we only have Measures here, as layout.StaffGroup
        # or similar objs may be retained
        measured.removeByNotOfClass('Measure')
        measured.makeTies(inPlace=True)
        return measured


    def _analyze(self, windowSize, windowType='overlap'):
        '''
        Calls, for a given window size, an analysis method across all windows in the source Stream. 

        If windowType is "overlap", windows above size 1 are always overlapped, so if a window 
        of size 2 is used, windows 1-2, then 2-3, then 3-4 are compared. If a window of size 3 
        is used, windows 1-3, then 2-4, then 3-5 are compared. 

        Windows are assumed to be partitioned by :class:`music21.stream.Measure` objects.

        Returns two lists for results, each equal in size to the length of minimum windows 
        minus the window size plus one. If we have 20 1/4 windows, then the results lists 
        will be of length 20 for window size 1, 19 for window size 2, 18 for window size 3, etc. 

        
        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.Ambitus()
        >>> wa = analysis.windowed.WindowedAnalysis(s, p)
        >>> len(wa._windowedStream)
        36
        >>> a, b = wa._analyze(1)
        >>> len(a), len(b)
        (36, 36)

        >>> a, b = wa._analyze(4)
        >>> len(a), len(b)
        (33, 33)

        '''
        maxWindowCount = len(self._windowedStream)
        # assuming that this is sorted

        if windowType == 'overlap':
            windowCount = maxWindowCount - windowSize + 1

        elif windowType == 'noOverlap':
            windowCount = (maxWindowCount / windowSize) + 1

        elif windowType == 'adjacentAverage':
            windowCount = maxWindowCount

        data = [0] * windowCount
        color = [0] * windowCount
        # how many windows in this row
        windowCountIndices = range(windowCount)
        
        if windowType == 'overlap':
            for i in windowCountIndices:
                current = stream.Stream()
                for j in range(i, i+windowSize):
                    #environLocal.printDebug(['self._windowedStream[j]', self._windowedStream[j]])
                    current.append(self._windowedStream[j])
                data[i], color[i] = self.processor.process(current)

        elif windowType == 'noOverlap':
            start = 0
            end = start+windowSize
            i = 0
            while True:
                if end >= len(self._windowedStream):
                    end = len(self._windowedStream)

                current = stream.Stream()
                for j in range(start, end):
                    current.append(self._windowedStream[j])
                data[i], color[i] = self.processor.process(current)

                start = end
                end = start + windowSize
                i += 1
                if i >= windowCount:
                    break
       
        elif windowType == 'adjacentAverage':
            # first get overlapping windows
            overlapped = []
            for i in range(maxWindowCount - windowSize + 1):
                current = stream.Stream()
                # store indices of min windows that participate
                participants = [] 
                for j in range(i, i+windowSize):
                    current.append(self._windowedStream[j])
                    participants.append(j)
                overlapped.append([current, participants])

            # then distribute to each of maxWindowCount
            for i in range(maxWindowCount):
                # get all participants, combine into a single 
                current = stream.Stream()
                for dataStream, participants in overlapped:
                    if i in participants:
                        for m in dataStream:
                            current.append(m)
                data[i], color[i] = self.processor.process(current)

        return data, color

        
    def process(self, minWindow=1, maxWindow=1, windowStepSize=1, 
                windowType='overlap', includeTotalWindow=True):

        ''' Main method for windowed analysis across one or more window size.

        Calls :meth:`~music21.analysis.WindowedAnalysis._analyze` for 
        the number of different window sizes to be analyzed.

        The `minWindow` and `maxWindow` set the range of window sizes in quarter lengths. 
        The `windowStepSize` parameter determines the increment between these window sizes, 
        in quarter lengths. 

        If `minWindow` or `maxWindow` is None, the largest window size available will be set. 

        If `includeTotalWindow` is True, the largest window size will always be added. 

        
        >>> s = corpus.parse('bach/bwv324')
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> # placing one part into analysis
        >>> wa = analysis.windowed.WindowedAnalysis(s.parts[0], p)
        >>> x, y, z = wa.process(1, 1, includeTotalWindow=False)
        >>> len(x) # we only have one series of windows
        1

        >>> y[0][0].startswith('#') # for each window, we get a solution and a color
        True
        >>> x[0][0][0] 
        <music21.pitch.Pitch B>

        >>> x, y, z = wa.process(1, 2, includeTotalWindow=False)
        >>> len(x) # we have two series of windows
        2

        >>> x[0][0] # the data returned is processor dependent; here we get
        (<music21.pitch.Pitch B>, 'major', 0.6868258874056411)
        >>> y[0][0].startswith('#') # a color is returned for each matching data position
        True
        '''
        if maxWindow is None:
            maxLength = len(self._windowedStream)
        else:
            maxLength = maxWindow

        if minWindow is None:
            minLength = len(self._windowedStream)
        else:
            minLength = minWindow
        
        if windowType is None:
            windowType = 'overlap'
        elif windowType.lower() in ['overlap']:
            windowType = 'overlap'
        elif windowType.lower() in ['nooverlap', 'nonoverlapping']:
            windowType = 'noOverlap'
        elif windowType.lower() in ['adjacentaverage']:
            windowType = 'adjacentAverage'

        # need to create storage for the output of each row, or the processing
        # of all windows of a single size across the entire Stream
        solutionMatrix = [] 
        colorMatrix = [] 
        # store meta data about each row as a dictionary
        metaMatrix = [] 

        if common.isNum(windowStepSize):
            windowSizes = list(range(minLength, maxLength+1, windowStepSize))
        else:
            num, junk = common.getNumFromStr(windowStepSize)
            windowSizes = []
            x = minLength
            while True:
                windowSizes.append(x)
                x = x * int(round(float(num)))
                if x > (maxLength * .75):
                    break

        if includeTotalWindow:
            totalWindow = len(self._windowedStream)
            if totalWindow not in windowSizes:
                windowSizes.append(totalWindow)

        for i in windowSizes:
            #environLocal.printDebug(['processing window:', i])
            # each of these results are lists, where len is based on 
            soln, colorn = self._analyze(i, windowType=windowType) 
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
        return len(subStream.flat.notesAndRests), None
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import corpus
        from music21.analysis import discrete
        # get a procedure 
        
        s = corpus.parse('bach/bwv324')

        for pClass in [discrete.KrumhanslSchmuckler, discrete.Ambitus]:
            p = pClass()

            # get windowing object, provide a stream for analysis as well as 
            # the processor
            wa = WindowedAnalysis(s, p)
            # do smallest and larges
            for i in list(range(1, 4)) + [None]:
                unused_x, unused_y, unused_z = wa.process(i, i)
    

    def testWindowing(self):
        '''Test that windows are doing what they are supposed to do 
        '''
        p = TestMockProcesor()

        from music21 import note
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
        a, unused_b, unused_c = wa1.process(1, 1, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 2) 
        self.assertEqual(a[0][0], 1)
        self.assertEqual(a[0][1], 1)

        # window size of 2 gets 1 solution
        a, unused_b, unused_c = wa1.process(2, 2, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 1)
        # two items in this window
        self.assertEqual(a[0][0], 2)


        # window size of 1 gets 8 solutiions
        a, unused_b, unused_c = wa2.process(1, 1, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 8)
        self.assertEqual(a[0][0], 1)
        self.assertEqual(a[0][1], 1)

        # window size of 2 gets 7 solutions
        a, unused_b, unused_c = wa2.process(2, 2, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 7)

        # window size of 7 gets 2 solutions
        a, unused_b, unused_c = wa2.process(7, 7, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 2)

        # window size of 8 gets 1 solutions
        a, unused_b, unused_c = wa2.process(8, 8, 1, includeTotalWindow=False)
        self.assertEqual(len(a[0]), 1)



    def testVariableWindowing(self):
        from music21.analysis import discrete
        from music21 import corpus, graph
        
        p = discrete.KrumhanslSchmuckler()
        s = corpus.parse('bach/bwv66.6')

        unused_wa = WindowedAnalysis(s, p)


        plot = graph.PlotWindowedKrumhanslSchmuckler(s, doneAction=None,
            windowStep=4, windowType='overlap')
        plot.process()
        #plot.write()

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [WindowedAnalysis]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof



