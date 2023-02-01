# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         windowed.py
# Purpose:      Framework for modular, windowed analysis
#
# Authors:      Jared Sadoian
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2010 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
This module describes classes for performing windowed and overlapping windowed analysis.
The :class:`music21.analysis.windowed.WindowedAnalysis` provides a reusable framework for
systematic overlapping window analysis at the starting at the level of the quarter note
and moving to the size of an entire :class:`music21.stream.Stream`.

Modular analysis procedures inherit from :class:`music21.analysis.discrete.DiscreteAnalysis`.
The :class:`music21.analysis.discrete.KrumhanslSchmuckler` (for algorithmic key detection)
and :class:`music21.analysis.discrete.Ambitus` (for pitch range analysis) classes provide examples.
'''
from __future__ import annotations

import unittest
import warnings

from music21 import exceptions21

from music21 import common
from music21 import environment
from music21 import meter
from music21 import stream

from music21.analysis.discrete import DiscreteAnalysisException

environLocal = environment.Environment('analysis.windowed')


# -----------------------------------------------------------------------------
class WindowedAnalysisException(exceptions21.Music21Exception):
    pass


# -----------------------------------------------------------------------------

class WindowedAnalysis:
    '''
    Create a WindowedAnalysis object.

    The provided `analysisProcessor` must provide a `process()` method that,
    when given a windowed Stream (a Measure) returns two element tuple containing
    (a) a data value (implementation dependent) and (b) a color code.
    '''

    def __init__(self, streamObj, analysisProcessor):
        self.processor = analysisProcessor
        # environLocal.printDebug(self.processor)
        if not isinstance(streamObj, stream.Stream):
            raise WindowedAnalysisException('non-stream provided as argument')
        if streamObj.hasPartLikeStreams():
            streamObj = streamObj.flatten()  # part-like substreams not supported.
        self._srcStream = streamObj
        # store a windowed Stream, partitioned into bars of 1/4
        self._windowedStream = self.getMinimumWindowStream()

    def getMinimumWindowStream(self, timeSignature='1/4'):
        '''
        Take the loaded stream and restructure it into measures of 1 quarter note duration.

        >>> s = corpus.parse('bach/bwv324')
        >>> p = analysis.discrete.Ambitus()

        Placing one part into analysis:

        >>> wa = analysis.windowed.WindowedAnalysis(s.parts[0], p)

        >>> post = wa.getMinimumWindowStream()
        >>> len(post.getElementsByClass(stream.Measure))
        42
        >>> post.getElementsByClass(stream.Measure).first()
        <music21.stream.Measure 1 offset=0.0>

        Time signature set to 1/4 time signature

        >>> post.getElementsByClass(stream.Measure).first().timeSignature
        <music21.meter.TimeSignature 1/4>

        leaves one note in this measure

        >>> len(post.getElementsByClass(stream.Measure)[1].notes)
        1

        Placing a score with parts into analysis will automatically flatten
        the stream.  So these two calls are equivalent:

        >>> wa1 = analysis.windowed.WindowedAnalysis(s, p)
        >>> wa2 = analysis.windowed.WindowedAnalysis(s.flatten(), p)

        '''
        # create a stream that contains just a 1/4 time signature; this is
        # the minimum window size (and partitioning will be done by measure)
        meterStream = stream.Stream()
        meterStream.insert(0, meter.TimeSignature(timeSignature))

        # makeTies() splits the durations into proper measure boundaries for
        # analysis; this means that a duration that spans multiple 1/4 measures
        # will be represented in each of those measures
        measured = self._srcStream.makeMeasures(meterStream=meterStream)
        # need to make sure we only have Measures here, as layout.StaffGroup
        # or similar objs may be retained
        measured.removeByNotOfClass('Measure')
        if not measured:  # pragma: no cover
            raise WindowedAnalysisException('Making measures failed')
        measured.makeTies(inPlace=True)
        return measured

    def analyze(self, windowSize, windowType='overlap'):
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
        >>> wa = analysis.windowed.WindowedAnalysis(s.flatten(), p)
        >>> len(wa._windowedStream)
        36
        >>> a, b = wa.analyze(1)
        >>> len(a), len(b)
        (36, 36)

        >>> a, b = wa.analyze(4)
        >>> len(a), len(b)
        (33, 33)

        >>> a, b = wa.analyze(1, windowType='noOverlap')
        >>> len(a), len(b)
        (37, 37)

        >>> a, b = wa.analyze(4, windowType='noOverlap')
        >>> len(a), len(b)
        (10, 10)

        >>> a, b = wa.analyze(1, windowType='adjacentAverage')
        >>> len(a), len(b)
        (36, 36)

        '''
        maxWindowCount = len(self._windowedStream)
        # assuming that this is sorted

        if windowType == 'overlap':
            windowCount = maxWindowCount - windowSize + 1
        elif windowType == 'noOverlap':
            windowCountFloat = maxWindowCount / windowSize + 1
            windowCount = int(windowCountFloat)
            if windowCountFloat != windowCount:
                warnings.warn(
                    'maxWindowCount is not divisible by windowSize, possibly undefined behavior'
                )
        elif windowType == 'adjacentAverage':
            windowCount = maxWindowCount
        else:
            raise exceptions21.Music21Exception(f'Unknown windowType: {windowType}')

        data = [0] * windowCount
        color = [0] * windowCount
        # how many windows in this row
        windowCountIndices = range(windowCount)

        if windowType == 'overlap':
            for i in windowCountIndices:
                current = stream.Stream()
                for j in range(i, i + windowSize):
                    # environLocal.printDebug(['self._windowedStream[j]', self._windowedStream[j]])
                    current.append(self._windowedStream[j])

                try:
                    data[i], color[i] = self.processor.process(current)
                except DiscreteAnalysisException:
                    # current might have no notes...all rests?
                    data[i], color[i] = (None, None, 0), '#ffffff'

        elif windowType == 'noOverlap':
            start = 0
            end = start + windowSize
            i = 0
            while True:
                if end >= len(self._windowedStream):
                    end = len(self._windowedStream)

                current = stream.Stream()
                for j in range(start, end):
                    current.append(self._windowedStream[j])

                try:
                    data[i], color[i] = self.processor.process(current)
                except DiscreteAnalysisException:
                    # current might have no notes...all rests?
                    data[i], color[i] = (None, None, 0), '#ffffff'

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
                for j in range(i, i + windowSize):
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
                try:
                    data[i], color[i] = self.processor.process(current)
                except DiscreteAnalysisException:
                    # current might have no notes...all rests?
                    data[i], color[i] = (None, None, 0), '#ffffff'

        return data, color


    def process(self,
                minWindow: int | None = 1,
                maxWindow: int | None = 1,
                windowStepSize: int | str = 1,
                windowType='overlap',
                includeTotalWindow=True):
        # noinspection PyShadowingNames
        '''
        Main method for windowed analysis across one or more window sizes.

        Calls :meth:`~music21.analysis.WindowedAnalysis.analyze` for
        the number of different window sizes to be analyzed.

        The `minWindow` and `maxWindow` set the range of window sizes in quarter lengths.
        The `windowStepSize` parameter determines the increment between these window sizes,
        in quarter lengths.

        If `minWindow` or `maxWindow` is None, the largest window size available will be set.

        If `includeTotalWindow` is True, the largest window size will always be added.


        >>> s = corpus.parse('bach/bwv324')
        >>> ksAnalyzer = analysis.discrete.KrumhanslSchmuckler()

        placing one part into analysis

        >>> sopr = s.parts[0]
        >>> wa = analysis.windowed.WindowedAnalysis(sopr, ksAnalyzer)
        >>> solutions, colors, meta = wa.process(1, 1, includeTotalWindow=False)
        >>> len(solutions)  # we only have one series of windows
        1

        >>> solutions, colors, meta = wa.process(1, 2, includeTotalWindow=False)
        >>> len(solutions)  # we have two series of windows
        2

        >>> solutions[1]
        [(<music21.pitch.Pitch B>, 'major', 0.6844...),
         (<music21.pitch.Pitch B>, 'minor', 0.8308...),
         (<music21.pitch.Pitch D>, 'major', 0.6844...),
         (<music21.pitch.Pitch B>, 'minor', 0.8308...),...]

        >>> colors[1]
        ['#ffb5ff', '#9b519b', '#ffd752', '#9b519b', ...]

        >>> meta
        [{'windowSize': 1}, {'windowSize': 2}]
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
        # store metadata about each row as a dictionary
        metaMatrix = []

        if isinstance(windowStepSize, int):
            windowSizes = list(range(minLength, maxLength + 1, windowStepSize))
        else:
            num, junk = common.getNumFromStr(windowStepSize)
            windowSizes = []
            x = minLength
            while True:
                windowSizes.append(x)
                x = x * round(int(num))
                if x > (maxLength * 0.75):
                    break

        if includeTotalWindow:
            totalWindow = len(self._windowedStream)
            if totalWindow not in windowSizes:
                windowSizes.append(totalWindow)

        for i in windowSizes:
            # environLocal.printDebug(['processing window:', i])
            # each of these results are lists, where len is based on
            solution, colorName = self.analyze(i, windowType=windowType)
            # store lists of results in a list of lists
            solutionMatrix.append(solution)
            colorMatrix.append(colorName)
            meta = {'windowSize': i}
            metaMatrix.append(meta)

        return solutionMatrix, colorMatrix, metaMatrix


# -----------------------------------------------------------------------------

class TestMockProcessor:

    def process(self, subStream):
        '''
        Simply count the number of notes found
        '''
        return len(subStream.flatten().notesAndRests), None


class Test(unittest.TestCase):
    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())

    def testBasic(self):
        from music21 import corpus
        from music21.analysis import discrete
        # get a procedure

        s = corpus.parse('bach/bwv324')

        for pClass in [discrete.KrumhanslSchmuckler, discrete.Ambitus]:
            p = pClass()

            # get windowing object, provide a stream for analysis as well as
            # the processor
            wa = WindowedAnalysis(s.flatten(), p)
            # do smallest and larges
            for i in list(range(1, 4)) + [None]:
                unused_x, unused_y, unused_z = wa.process(i, i)

    def testWindowing(self):
        '''
        Test that windows are doing what they are supposed to do
        '''
        p = TestMockProcessor()

        from music21 import note
        s1 = stream.Stream()
        s1.append(note.Note('C'))
        s1.append(note.Note('C'))

        s2 = stream.Stream()
        s2.append(note.Note('C'))
        s2.append(note.Note('D'))
        s2.append(note.Note('E'))
        s2.append(note.Note('F'))
        s2.append(note.Note('G'))
        s2.append(note.Note('A'))
        s2.append(note.Note('B'))
        s2.append(note.Note('C'))

        wa1 = WindowedAnalysis(s1, p)
        wa2 = WindowedAnalysis(s2, p)

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

        # window size of 1 gets 8 solutions
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
        from music21 import corpus
        from music21 import graph

        p = discrete.KrumhanslSchmuckler()
        s = corpus.parse('bach/bwv66.6')

        unused_wa = WindowedAnalysis(s.flatten(), p)

        plot = graph.plot.WindowedKey(s.flatten(), doneAction=None,
                                      windowStep=4, windowType='overlap')
        plot.run()
        # plot.write()


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [WindowedAnalysis]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
