# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         graph.py
# Purpose:      Classes for graphing in matplotlib and/or other graphing tools.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2012, 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Object definitions for graphing and plotting :class:`~music21.stream.Stream` objects.

The :class:`~music21.graph.primitives.Graph` object subclasses primitive, abstract fundamental
graphing archetypes using the matplotlib library. The :class:`~music21.graph.plot.PlotStream`
object subclasses provide reusable approaches to graphing data and structures in
:class:`~music21.stream.Stream` objects.

The most common way of using plotting functions is to call `.plot()` on a Stream.
'''
__all__ = [
    'axis', 'findPlot', 'plot', 'primitives', 'utilities',
    'plotStream',
]

import unittest

from music21 import common

from music21.graph import axis
from music21.graph import findPlot
from music21.graph import plot
from music21.graph import primitives
from music21.graph import utilities

from music21 import environment
_MOD = 'graph'
environLocal = environment.Environment(_MOD)


def plotStream(
    streamObj,
    graphFormat=None,
    xValue=None,
    yValue=None,
    zValue=None,
    **keywords,
):
    '''
    Given a stream and any keyword configuration arguments, create and display a plot.

    Note: plots require matplotlib to be installed.

    Plot methods can be specified as additional arguments or by keyword.
    Two keyword arguments can be given: `format` and `values`.
    If positional arguments are given, the first is taken as `format`
    and the rest are collected as `values`. If `format` is the class
    name, that class is collected. Additionally, every
    :class:`~music21.graph.PlotStream` subclass defines one `format`
    string and a list of `values` strings. The `format` parameter
    defines the type of Graph (e.g. scatter, histogram, colorGrid). The
    `values` list defines what values are graphed
    (e.g. quarterLength, pitch, pitchClass).

    If a user provides a `format` and one or more `values` strings, a plot with
    the corresponding profile, if found, will be generated. If not, the first
    Plot to match any of the defined specifiers will be created.

    In the case of :class:`~music21.graph.PlotWindowedAnalysis` subclasses,
    the :class:`~music21.analysis.discrete.DiscreteAnalysis`
    subclass :attr:`~music21.analysis.discrete.DiscreteAnalysis.identifiers` list
    is added to the Plot's `values` list.

    Available plots include the following:

    * :class:`~music21.graph.plot.HistogramPitchSpace`
    * :class:`~music21.graph.plot.HistogramPitchClass`
    * :class:`~music21.graph.plot.HistogramQuarterLength`
    * :class:`~music21.graph.plot.ScatterPitchSpaceQuarterLength`
    * :class:`~music21.graph.plot.ScatterPitchClassQuarterLength`
    * :class:`~music21.graph.plot.ScatterPitchClassOffset`
    * :class:`~music21.graph.plot.ScatterPitchSpaceDynamicSymbol`
    * :class:`~music21.graph.plot.HorizontalBarPitchSpaceOffset`
    * :class:`~music21.graph.plot.HorizontalBarPitchClassOffset`
    * :class:`~music21.graph.plot.ScatterWeightedPitchSpaceQuarterLength`
    * :class:`~music21.graph.plot.ScatterWeightedPitchClassQuarterLength`
    * :class:`~music21.graph.plot.ScatterWeightedPitchSpaceDynamicSymbol`
    * :class:`~music21.graph.plot.Plot3DBarsPitchSpaceQuarterLength`
    * :class:`~music21.graph.plot.WindowedKey`
    * :class:`~music21.graph.plot.WindowedAmbitus`
    * :class:`~music21.graph.plot.Dolan`


    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('histogram', 'pitch', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('histogram', 'pitch')

    .. image:: images/HistogramPitchSpace.*
        :width: 600


    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('pianoroll')

    .. image:: images/HorizontalBarPitchSpaceOffset.*
        :width: 600

    '''
    plotMake = findPlot.getPlotsToMake(graphFormat, xValue, yValue, zValue)
    # environLocal.printDebug(['plotClassName found', plotMake])
    for plotInfo in plotMake:
        if not common.isIterable(plotInfo):
            plotClassName = plotInfo
            plotDict = None
        else:
            plotClassName, plotDict = plotInfo
        obj = plotClassName(streamObj, **keywords)
        if plotDict:
            for axisName, axisClass in plotDict.items():
                attrName = 'axis' + axisName.upper()
                setattr(obj, attrName, axisClass(obj, axisName))
        obj.run()


# ------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):  # pragma: no cover

    def testAll(self):
        from music21 import corpus, dynamics
        a = corpus.parse('bach/bwv57.8')
        a.parts[0].insert(0, dynamics.Dynamic('mf'))
        a.parts[0].insert(10, dynamics.Dynamic('f'))
        plotStream(a, 'all')


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import copy
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)

    def testAll(self):
        from music21 import corpus
        a = corpus.parse('bach/bwv57.8')
        plotStream(a.flat, doneAction=None)

    def testPlotChordsC(self):
        from music21 import dynamics, note, stream, scale

        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        s.append(note.Note('c4'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        # s.append(note.Note('c3', quarterLength=2))
        s.append(dynamics.Dynamic('mf'))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        s.append(dynamics.Dynamic('pp'))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        for args in [
            ('histogram', 'pitch'),
            ('histogram', 'pitchclass'),
            ('histogram', 'quarterlength'),
            ('scatter', 'pitch', 'quarterlength'),
            ('scatter', 'pitchspace', 'offset'),
            ('scatter', 'pitch', 'offset'),
            ('scatter', 'dynamics'),
            ('bar', 'pitch'),
            ('bar', 'pc'),
            ('weighted', 'pc', 'duration'),
            ('weighted', 'dynamics'),
        ]:
            # s.plot(*args, doneAction='write')
            s.plot(*args, doneAction=None)

    def testHorizontalInstrumentationB(self):
        from music21 import corpus, dynamics
        s = corpus.parse('bwv66.6')
        dyn = ['p', 'mf', 'f', 'ff', 'mp', 'fff', 'ppp']
        i = 0
        for p in s.parts:
            for m in p.getElementsByClass('Measure'):
                m.insert(0, dynamics.Dynamic(dyn[i % len(dyn)]))
                i += 1
        s.plot('dolan', fillByMeasure=True, segmentByTarget=True, doneAction=None)


# -----------------------------------------------------------------------------
_DOC_ORDER = [plotStream]


# -----------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testPlot3DPitchSpaceQuarterLengthCount')

