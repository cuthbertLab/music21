# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         graph/plots.py
# Purpose:      Classes for plotting music21 graphs based on Streams.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2012, 2017 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Object definitions for plotting :class:`~music21.stream.Stream` objects. 

The :class:`~music21.graph.plots.Plot` 
object subclasses provide reusable approaches to graphing data and structures in 
:class:`~music21.stream.Stream` objects.
'''
from __future__ import division, print_function, absolute_import

import math
import os
import random
import unittest

from music21 import common
from music21 import chord
from music21 import corpus
from music21 import converter
from music21 import dynamics
from music21 import features
from music21 import note
from music21 import pitch

from music21.graph import primitives
from music21.graph.utilities import (GraphException, PlotStreamException,
                                     accidentalLabelToUnicode)

from music21.analysis import correlate
from music21.analysis import discrete
from music21.analysis import elements as elementAnalysis
from music21.analysis import pitchAnalysis
from music21.analysis import reduction
from music21.analysis import windowed

from music21.ext import six
if six.PY2:
    # pylint: disable=redefined-builtin
    from music21.common import py3round as round

from music21 import environment
_MOD = 'graph/plots.py'
environLocal = environment.Environment(_MOD)    


#-------------------------------------------------------------------------------
# graphing utilities that operate on streams

class PlotStreamMixin(object):
    '''
    Approaches to plotting and graphing a Stream. A base class from which 
    Stream plotting Classes inherit.

    This class has a number of public attributes, but these are generally not intended 
    for direct user application. The `data` attribute, for example, exposes the 
    internal data format of this plotting routine for testing, but no effort is 
    made to make this data useful outside of the context of the Plot.
    '''
    # the following static parameters are used to for matching this
    # plot based on user-requested string aguments
    # a string representation of the type of graph
    format = 'genericPlotStream'
    # store a list of parameters that are graphed
    values = [] # this seems not good!

    def __init__(self, streamObj, flatten=True, *args, **keywords):
        '''
        Provide a Stream as an argument. If `flatten` is True, 
        the Stream will automatically be flattened.
        '''
        #if not isinstance(streamObj, music21.stream.Stream):
        if not hasattr(streamObj, 'elements'): # pragma: no cover
            raise PlotStreamException('non-stream provided as argument: %s' % streamObj)
        self.streamObj = streamObj
        self.flatten = flatten
        self.classFilterList = ['Note', 'Chord']
        
        self.data = None # store native data representation, useful for testing

        self.axisX = None
        self.axisY = None
        self.matchPitchCountForChords = False
        
    def run(self):
        self.extractData()
        self.setTicks('y', self.axisY.ticks())
        self.setTicks('x', self.axisX.ticks())
        self.setAxisLabel('y', self.axisY.axisLabel)
        self.setAxisLabel('x', self.axisX.axisLabel)
        
        self.process()

    #---------------------------------------------------------------------------
    def extractData(self):
        if self.axisX is None:
            raise PlotStreamException("Set axisX before calling extractData() via run()")
        if self.axisY is None:
            raise PlotStreamException("Set axisY before calling extractData() via run()")
        
        if self.flatten:
            sIter = self.streamObj.recurse()
        else:
            sIter = self.streamObj.iter
        
        if self.classFilterList:
            sIter.getElementsByClass(self.classFilterList)
        
        
        allXValues = []
        allYValues = []

        self.data = []

        for el in sIter:
            valuesX = []
            valuesY = []
            if 'Chord' not in el.classes:
                valuesX = self.axisX.extractOneElement(el)
                valuesY = self.axisY.extractOneElement(el)
            else:
                valuesX, valuesY = self._extractChordDataTwoAxis(el)
            
            self.postProcessElement(el, valuesX, valuesY)
            if valuesX is None:
                continue
            elif not common.isIterable(valuesX):
                valuesX = [valuesX]
            
            if valuesY is None:
                continue            
            elif not common.isIterable(valuesY):
                valuesY = [valuesY]
            
            allXValues.extend(valuesX)
            allYValues.extend(valuesY)
            self.data.extend(zip(valuesX, valuesY))

        self.axisX.setBoundariesFromData(valuesX)
        self.axisY.setBoundariesFromData(valuesY)
        self.postProcessData()
            
            
    def postProcessElement(self, el, *values):
        pass

    def postProcessData(self):
        pass
                
    #---------------------------------------------------------------------------
    @staticmethod
    def _extractChordDataOneAxis(ax, c):
        '''
        Look for Note-like attributes in a Chord. This is done by first 
        looking at the Chord, and then, if attributes are not found, looking at each pitch. 
        '''
        values = []
        value = None
        try:
            value = ax.extractOneElement(c)
        except AttributeError:
            pass # do not try others
        
        if value is not None:
            values.append(value)

        if not values: # still not set, get form chord
            for n in c:
                # try to get get values from note inside chords
                value = None
                try:
                    value = ax.extractOneElement(n)
                except AttributeError: # pragma: no cover
                    break # do not try others
 
                if value is not None:
                    values.append(value)
        return values

    def _extractChordDataTwoAxis(self, c):
        xValues = self._extractChordDataOneAxis(self.axisX, c)
        yValues = self._extractChordDataOneAxis(self.axisY, c)

        bundleGroups = []
        for thisAxis, values in [(self.axisX, xValues), (self.axisY, yValues)]:
            if not values:
                bundleGroups.append((thisAxis, values))

        for thisAxis, destValues in bundleGroups:
            for n in c:
                try:
                    target = thisAxis.extractOneElement(n)
                except AttributeError: # pragma: no cover
                    pass # must try others
                if target is not None:
                    destValues.append(target)

        #environLocal.printDebug(['after looking at Pitch:', 
        #    'xValues', xValues, 'yValues', yValues])

        # if we only have one attribute from the Chord, and many from the 
        # Pitches, need to make the number of data points equal by 
        # duplicating data
        if self.matchPitchCountForChords: 
            if len(xValues) == 1 and len(yValues) > 1:
                #environLocal.printDebug(['balancing x'])
                for i in range(len(yValues) - 1):
                    xValues.append(xValues[0])
            elif len(yValues) == 1 and len(xValues) > 1:
                #environLocal.printDebug(['balancing y'])
                for i in range(len(xValues) - 1):
                    yValues.append(yValues[0])

        return xValues, yValues

    #---------------------------------------------------------------------------
    @property
    def id(self):
        '''
        Each PlotStream has a unique id that consists of its format and a 
        string that defines the parameters that are graphed.
        '''
        return '%s-%s' % (self.format, '-'.join(self.values))

    

#-------------------------------------------------------------------------------

class PlotStream(primitives.Graph, PlotStreamMixin):
    def __init__(self, streamObj, *args, **keywords):
        from music21.graph import axis
        primitives.Graph.__init__(self, *args, **keywords)
        PlotStreamMixin.__init__(self, streamObj)

        self.axisX = axis.OffsetAxis(self, 'x')


#-------------------------------------------------------------------------------
# scatter plots

class PlotScatter(primitives.GraphScatter, PlotStreamMixin):
    def __init__(self, streamObj, *args, **keywords):
        from music21.graph import axis
        primitives.GraphScatter.__init__(self, *args, **keywords)
        PlotStreamMixin.__init__(self, streamObj)

        self.axisX = axis.QuarterLengthAxis(self, 'x')
        self.axisX.useLogScale = True

        self.axisY = axis.PitchSpaceAxis(self, 'y')

# class PlotScatter(PlotStream):
#     '''Base class for 2D Scatter plots.
#     '''
#     format = 'scatter'
#     
#     def __init__(self, streamObj, *args, **keywords):
#         super(PlotScatter, self).__init__(streamObj, *args, **keywords)
# 
#         if 'xLog' not in keywords:
#             self.xLog = True
#         else:
#             self.xLog = keywords['xLog']
# 
#         # sample values; customize in subclass
#         self.fy = lambda n: n.pitch.ps
#         self.fyTicks = self.ticksPitchSpaceUsage
# 
#         self.fx = lambda n: float(n.quarterLength)
#         self.fxTicks = self.ticksQuarterLength
# 
# 
#     def _extractData(self, xLog=False):
#         data = []
#         xValues = []
#         yValues = []
# 
#         if self.flatten:
#             sSrc = self.streamObj.flat
#         else:
#             sSrc = self.streamObj
# 
#         # get all unique values for both x and y
#         for noteObj in sSrc.getElementsByClass(note.Note):
#             x = self.fx(noteObj)
#             if xLog:
#                 x = self.remapQuarterLength(x)
#             y = self.fy(noteObj)
#             if x not in xValues:
#                 xValues.append(x)            
#             if y not in xValues:
#                 yValues.append(x)            
#         for chordObj in sSrc.getElementsByClass(chord.Chord):
#             xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
#                          chordObj, matchPitchCount=False)
#             for x in xSrc:
#                 if x not in xValues:
#                     xValues.append(x)            
#             for y in ySrc:
#                 if y not in xValues:
#                     yValues.append(y)     
# 
#         xValues.sort()
#         yValues.sort()
# 
#         # count the frequency of each item
#         for noteObj in sSrc.getElementsByClass(note.Note):
#             x = self.fx(noteObj)
#             if xLog:
#                 x = self.remapQuarterLength(x)
#             y = self.fy(noteObj)
#             data.append([x, y])
# 
#         for chordObj in sSrc.getElementsByClass(chord.Chord):
#             # here, need an x for every y, so match pitch count
#             xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
#                          chordObj, matchPitchCount=True)
#             #environLocal.printDebug(['xSrc', xSrc, 'ySrc', ySrc])
#             for i, x in enumerate(xSrc):
#                 y = ySrc[i]
#                 if xLog:
#                     x = self.remapQuarterLength(x)
#                 data.append([x, y])
# 
#         #environLocal.printDebug(['data', data])
# 
#         xVals = [x for x,y in data]
#         yVals = [y for x,y in data]
# 
#         xTicks = self.fxTicks(min(xVals), max(xVals), remap=xLog)
#         yTicks = self.fyTicks(min(yVals), max(yVals))
# 
#         return data, xTicks, yTicks


class PlotScatterPitchSpaceQuarterLength(PlotScatter):
    '''A scatter plot of pitch space and quarter length

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterPitchSpaceQuarterLength(s)
    >>> p.id
    'scatter-pitch-quarterLength'
    >>> p.process()

    .. image:: images/PlotScatterPitchSpaceQuarterLength.*
        :width: 600
    '''
    values = ('pitch', 'quarterLength')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterPitchSpaceQuarterLength, self).__init__(streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceUsage
        self.fx = lambda n: float(n.quarterLength)
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = primitives.GraphScatter(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch')
        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (6, 6)
        if 'title' not in keywords:
            self.graph.title = 'Pitch by Quarter Length Scatter'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.7


class PlotScatterPitchClassQuarterLength(PlotScatter):
    '''A scatter plot of pitch class and quarter length

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterPitchClassQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterPitchClassQuarterLength(s)
    >>> p.id
    'scatter-pitchClass-quarterLength'
    >>> p.process()

    .. image:: images/PlotScatterPitchClassQuarterLength.*
        :width: 600
    '''
    # string name used to access this class
    values = ('pitchClass', 'quarterLength')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterPitchClassQuarterLength, self).__init__(streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.pitchClass
        self.fyTicks = self.ticksPitchClassUsage

        self.fx = lambda n: float(n.quarterLength)
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = primitives.GraphScatter(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Class')
        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(remap=self.xLog))

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (6, 6)
        if 'title' not in keywords:
            self.graph.title = 'Pitch Class by Quarter Length Scatter'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.7


class PlotScatterPitchClassOffset(PlotScatter):
    '''A scatter plot of pitch class and offset

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterPitchClassOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterPitchClassOffset(s)
    >>> p.id
    'scatter-pitchClass-offset'
    >>> p.process()

    .. image:: images/PlotScatterPitchClassOffset.*
        :width: 600
    '''
    values = ('pitchClass', 'offset')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterPitchClassOffset, self).__init__(streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.pitchClass
        self.fyTicks = self.ticksPitchClassUsage

        self.fx = lambda n: float(n.offset)
        self.fxTicks = self.ticksOffset

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        self.graph = primitives.GraphScatter(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Class')
        self.graph.setAxisLabel('x', self._axisLabelMeasureOrOffset())

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (10, 5)
        if 'title' not in keywords:
            self.graph.title = 'Pitch Class by Offset Scatter'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.7


class PlotScatterPitchSpaceDynamicSymbol(PlotScatter):
    '''
    A graph of dynamics used by pitch space.
    
    >>> s = converter.parse('tinynotation: 4/4 C4 d E f', makeNotation=False) #_DOCS_HIDE
    >>> s.insert(0.0, dynamics.Dynamic('pp')) #_DOCS_HIDE
    >>> s.insert(2.0, dynamics.Dynamic('ff')) #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterPitchSpaceDynamicSymbol(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = converter.parse('/Desktop/schumann/opus41no1/movement2.xml')
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterPitchSpaceDynamicSymbol(s)
    >>> p.process()

    .. image:: images/PlotScatterPitchSpaceDynamicSymbol.*
        :width: 600
    '''
    # string name used to access this class
    values = ('pitchClass', 'dynamics')
    figureSizeDefault = (12, 6)
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterPitchSpaceDynamicSymbol, self).__init__(streamObj, *args, **keywords)

        self.fxTicks = self.ticksPitchSpaceUsage
        self.fyTicks = self.ticksDynamics

        # get data from correlate object
        am = correlate.ActivityMatch(self.streamObj)
        self.data  = am.pitchToDynamic(dataPoints=True)

        xVals = [x for x, unused_y in self.data]
        yVals = [y for unused_x, y in self.data]

        xTicks = self.fxTicks(min(xVals), max(xVals))
        # ticks dynamics takes no args
        yTicks = self.fyTicks(min(yVals), max(yVals))

        self.graph = primitives.GraphScatter(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Dynamics')
        self.graph.setAxisLabel('x', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = self.figureSizeDefault
        if 'title' not in keywords:
            self.graph.title = 'Pitch Class by Quarter Length Scatter'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.7
        # make smaller for axis display
        if 'tickFontSize' not in keywords:
            self.graph.tickFontSize = 7





class PlotHistogram(primitives.GraphHistogram, PlotStreamMixin):
    def __init__(self, streamObj, *args, **keywords):
        from music21.graph import axis

        primitives.GraphHistogram.__init__(self, *args, **keywords)
        PlotStreamMixin.__init__(self, streamObj)

        self.axisX = axis.OffsetAxis(self, 'x')

        
#-------------------------------------------------------------------------------
# histograms

class PlotHistogramOld(PlotStream):
    '''
    Base class for Stream plotting classes.

    Plots take a Stream as their arguments, Graphs take any data.

    '''
    format = 'histogram'

    def _extractData(self, dataValueLegit=True):
        data = {}
        dataTick = {}
        #countMin = 0 # could be the lowest value found
        countMax = 0

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        # first, collect all unique data values
        dataValues = []
        for noteObj in sSrc.getElementsByClass(note.Note):
            value = self.fx(noteObj)
            if value not in dataValues:
                dataValues.append(value)
                
        for chordObj in sSrc.getElementsByClass(chord.Chord):
            values = self._extractChordDataOneAxis(self.fx, chordObj)
            for value in values:
                if value not in dataValues:
                    dataValues.append(value)

        dataValues.sort()

        # second, count instances
        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                values = self._extractChordDataOneAxis(self.fx, obj)
                ticks = self._extractChordDataOneAxis(self.fxTick, obj)
            else: # simulate a list
                values = [self.fx(obj)]            
                ticks = [self.fxTick(obj)]            

            for i, value in enumerate(values):
                if not dataValueLegit: 
                    # get the index position, not the value
                    value = dataValues.index(value)
    
                if value not in data:
                    data[value] = 0
                    # this is the offset that is used to shift labels
                    # into bars; this only is 0.5 if x values are integers
                    dataTick[value+.4] = ticks[i]
                data[value] += 1
                if data[value] >= countMax:
                    countMax = data[value]

        data = list(data.items())
        data.sort()
        dataTick = list(dataTick.items())
        dataTick.sort()
        xTicks = dataTick
        # alway have min and max
        yTicks = []
        yTickStep = round(countMax / 8)
        if yTickStep <= 1:
            yTickStep = 2
        for y in range(0, countMax + 1, yTickStep):
            yTicks.append([y, '%s' % y])
        yTicks.sort()

        return data, xTicks, yTicks


class PlotHistogramPitchSpace(PlotHistogram):
    '''A histogram of pitch space.

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotHistogramPitchSpace(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotHistogramPitchSpace(s)
    >>> p.id
    'histogram-pitch'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHistogramPitchSpace.*
        :width: 600
    '''
    values = ('pitch',)
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHistogramPitchSpace, self).__init__(streamObj, *args, **keywords)

        self.fx = lambda n: n.pitch.midi
        self.fxTick = lambda n: n.nameWithOctave
        # replace with self.ticksPitchSpaceUsage

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        # filter xTicks to remove - in flat lables
        xTicks = self.makePitchLabelsUnicode(xTicks)

        self.graph = primitives.GraphHistogram(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (9, 6)
        if 'title' not in keywords:
            self.graph.title = 'Pitch Histogram'

        # make smaller for axis display
        if 'tickFontSize' not in keywords:
            self.graph.tickFontSize = 7



class PlotHistogramPitchClass(PlotHistogram):
    '''
    A histogram of pitch class
    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotHistogramPitchClass(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotHistogramPitchClass(s)
    >>> p.id
    'histogram-pitchClass'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600

    '''
    values = ('pitchClass',)
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHistogramPitchClass, self).__init__(streamObj, *args, **keywords)

        self.fx = lambda n: n.pitch.pitchClass
        self.fxTick = lambda n: n.name
        # replace with self.ticksPitchClassUsage

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        # filter xTicks to remove - in flat lables
        xTicks = self.makePitchLabelsUnicode(xTicks)

        self.graph = primitives.GraphHistogram(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Pitch Class')

        if 'title' not in keywords:
            self.graph.title = 'Pitch Class Histogram'




class PlotHistogramQuarterLength(PlotHistogram):
    '''A histogram of pitch class

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotHistogramQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotHistogramQuarterLength(s)
    >>> p.id
    'histogram-quarterLength'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHistogramQuarterLength.*
        :width: 600

    '''
    values = ('quarterLength',)
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHistogramQuarterLength, self).__init__(streamObj, *args, **keywords)

        self.fx = lambda n: float(n.quarterLength)
        self.fxTick = lambda n: float(n.quarterLength)

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData(dataValueLegit=False)

        self.graph = primitives.GraphHistogram(*args, **keywords)
        self.graph.data = self.data

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Quarter Length')

        if 'title' not in keywords:
            self.graph.title = 'Quarter Length Histogram'




#-------------------------------------------------------------------------------
# base class for multi-stream displays

class PlotMultiStream(object):
    '''
    Approaches to plotting and graphing multiple Streams. 
    A base class from which Stream plotting Classes inherit.
    '''
    # the following static parameters are used to for matching this
    # plot based on user-requested string aguments
    # a string representation of the type of graph
    format = ''
    # store a list of parameters that are graphed
    values = []

    def __init__(self, streamList, labelList=None, *args, **keywords):
        '''
        Provide a list of Streams as an argument. Optionally 
        provide an additional list of labels for each list. 
        
        If `flatten` is True, the Streams will automatically be flattened.
        '''
        if labelList is None:
            labelList = []

        self.streamList = []
        foundPaths = []
        for s in streamList:
            # could be corpus or file path
            if isinstance(s, six.string_types):
                foundPaths.append(os.path.basename(s))
                if os.path.exists(s):
                    s = converter.parse(s)
                else: # assume corpus
                    s = corpus.parse(s)
            # otherwise assume a parsed stream
            self.streamList.append(s)

        # use found paths if no labels are provided
        if not labelList and len(foundPaths) == len(streamList):
            self.labelList = foundPaths
        else:
            self.labelList = labelList

        self.data = None # store native data representation, useful for testing
        self.graph = None  # store instance of graph class here


    def process(self):
        '''
        This will process all data, as well as call 
        the callDoneAction() method. What happens when the callDoneAction() is 
        called is determined by the attribute `doneAction`; 
        options are 'show' (display immediately), 
        'write' (write the file to a supplied file path), 
        and None (do processing but do not write or show a graph).

        Subclass dependent data extracted is stored in the self.data attribute. 
        '''
        self.graph.process()

    def show(self): # pragma: no cover
        '''
        Call internal Graphs show() method independently of doneAction set and run with process()
        '''
        self.graph.show()

    def write(self, fp=None): # pragma: no cover
        '''
        Call internal Graphs write() method independently of doneAction set and run with process()
        '''
        self.graph.write(fp)





#-------------------------------------------------------------------------------
# color grids    

    



class PlotWindowedAnalysis(primitives.Graph, PlotStreamMixin):
    '''
    Base Plot for windowed analysis routines.
    ''' 
    format = 'colorGrid'
    def __init__(self, streamObj, processor=None, *args, **keywords):
        super(PlotWindowedAnalysis, self).__init__(streamObj, *args, **keywords)
        
        # store process for getting title
        self.processor = processor
        self.graphLegend = None

        if 'title' not in keywords:
            # pass to Graph instance
            keywords['title'] = 'Windowed Analysis'

        if 'minWindow' in keywords:
            self.minWindow = keywords['minWindow']
        else:
            self.minWindow = 1

        if 'maxWindow' in keywords:
            self.maxWindow = keywords['maxWindow']
        else: # max window of None gets larges
            self.maxWindow = None

        if 'windowStep' in keywords:
            self.windowStep = keywords['windowStep']
        else:
            self.windowStep = 'pow2'

        if 'windowType' in keywords:
            self.windowType = keywords['windowType']
        else:
            self.windowType = 'overlap'

        if 'compressLegend' in keywords:
            self.compressLegend = keywords['compressLegend']
        else:
            self.compressLegend = True

        self.createGraph(*args, **keywords)
        
    def createGraph(self, *args, **keywords):
        '''
        actually create the graph...
        '''
        # create a color grid
        self.graph = primitives.GraphColorGrid(*args, **keywords)
        # uses self.processor
        
        # data is a list of lists where the outer list represents one row
        # of the graph and the inner list represents the color of each cell
        data, yTicks = self._extractData()
        xTicks = self.ticksOffset(minMaxOnly=True)
        
        self.graph.data = data
        self.graph.setAxisLabel('y', 'Window Size\n(Quarter Lengths)')
        self.graph.setAxisLabel('x', 'Windows (%s Span)' % self._axisLabelMeasureOrOffset())
        self.graph.setTicks('y', yTicks)

        # replace offset values with 0 and 1, as proportional here
        if len(xTicks) == 2:
            xTicks = [(0, xTicks[0][1]), (1, xTicks[1][1])]
        else:
            environLocal.printDebug(['raw xTicks', xTicks])
            xTicks = []
        environLocal.printDebug(['xTicks', xTicks])
        self.graph.setTicks('x', xTicks)

        
    def _extractData(self):
        '''
        Extract data actually calls the processing routine. 
        
        Returns two element tuple of the data (colorMatrix) and the yTicks list
        '''
        wa = windowed.WindowedAnalysis(self.streamObj, self.processor)
        unused_solutionMatrix, colorMatrix, metaMatrix = wa.process(self.minWindow, 
                                                                    self.maxWindow, 
                                                                    self.windowStep, 
                                                                    windowType=self.windowType)
                
        # if more than 12 bars, reduce the number of ticks
        if len(metaMatrix) > 12:
            tickRange = range(0, len(metaMatrix), len(metaMatrix) // 12)
        else:
            tickRange = range(len(metaMatrix))

        environLocal.printDebug(['tickRange', tickRange])
        #environLocal.printDebug(['last start color', colorMatrix[-1][0]])
        

        # get dictionaries of meta data for each row
        pos = 0
        yTicks = []
        
        for y in tickRange: 
            thisWindowSize = metaMatrix[y]['windowSize']
            # pad three ticks for each needed
            yTicks.append([pos, '']) # pad first
            yTicks.append([pos + 1, str(thisWindowSize)])
            yTicks.append([pos + 2, '']) # pad last
            pos += 3

        return colorMatrix, yTicks
    
    def _getLegend(self):
        '''
        Returns a solution legend for a WindowedAnalysis
        '''
        title = (self.processor.name + 
                ' (%s)' % self.processor.solutionUnitString())
        graphLegend = primitives.GraphColorGridLegend(doneAction=self.graph.doneAction, 
                                           title=title)
        graphData = self.processor.solutionLegend(compress=self.compressLegend)
        graphLegend.data = graphData
        return graphLegend

    def process(self):
        '''
        Process method here overridden to provide legend.
        '''
        # call the process routine in the base graph
        self.graph.process()
        # create a new graph of the legend
        self.graphLegend = self._getLegend()
        self.graphLegend.process()

    def write(self, fp=None): # pragma: no cover
        '''
        Process method here overridden to provide legend.
        '''
        if fp is None:
            fp = environLocal.getTempFile('.png')

        directory, fn = os.path.split(fp)
        fpLegend = os.path.join(directory, 'legend-' + fn)
        # call the process routine in the base graph
        self.graph.write(fp)
        # create a new graph of the legend

        self.graphLegend = self._getLegend()
        self.graphLegend.process()
        self.graphLegend.write(fpLegend)

    
class PlotWindowedKrumhanslSchmuckler(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Krumhansl-Schmuckler analysis routine. 
    See :class:`~music21.analysis.discrete.KrumhanslSchmuckler` for more details.

    
    >>> s = corpus.parse('bach/bwv66.6')
    >>> p = graph.plots.PlotWindowedKrumhanslSchmuckler(s.parts[0], doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW p = graph.plots.PlotWindowedKrumhanslSchmuckler(s.parts[0])
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotWindowedKrumhanslSchmuckler.*
        :width: 600

    .. image:: images/legend-PlotWindowedKrumhanslSchmuckler.*

    '''
    values = discrete.KrumhanslSchmuckler.identifiers
    def __init__(self, streamObj, *args, **keywords):
        super(PlotWindowedKrumhanslSchmuckler, self).__init__(streamObj, 
            discrete.KrumhanslSchmuckler(streamObj), *args, **keywords)
    
class PlotWindowedKrumhanslKessler(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Krumhansl-Kessler 
    analysis routine. See :class:`~music21.analysis.discrete.KrumhanslKessler` for more details.
    '''
    values = discrete.KrumhanslKessler.identifiers
    def __init__(self, streamObj, *args, **keywords):
        super(PlotWindowedKrumhanslKessler, self).__init__(streamObj, 
            discrete.KrumhanslKessler(streamObj), *args, **keywords)

class PlotWindowedAardenEssen(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Aarden-Essen 
    analysis routine. 
    See :class:`~music21.analysis.discrete.AardenEssen` for more details.
    '''
    values = discrete.AardenEssen.identifiers
    def __init__(self, streamObj, *args, **keywords):
        super(PlotWindowedAardenEssen, self).__init__(streamObj, 
            discrete.AardenEssen(streamObj), *args, **keywords)

class PlotWindowedSimpleWeights(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Simple Weights analysis 
    routine. See :class:`~music21.analysis.discrete.SimpleWeights` for more details.
    '''
    values = discrete.SimpleWeights.identifiers
    def __init__(self, streamObj, *args, **keywords):
        super(PlotWindowedSimpleWeights, self).__init__(streamObj, 
            discrete.SimpleWeights(streamObj), *args, **keywords)

class PlotWindowedBellmanBudge(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Bellman-Budge analysis 
    routine. See :class:`~music21.analysis.discrete.BellmanBudge` for more details.
    '''
    values = discrete.BellmanBudge.identifiers
    def __init__(self, streamObj, *args, **keywords):
        super(PlotWindowedBellmanBudge, self).__init__(streamObj, 
            discrete.BellmanBudge(streamObj), *args, **keywords)

class PlotWindowedTemperleyKostkaPayne(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Temperley-Kostka-Payne 
    analysis routine. 
    See :class:`~music21.analysis.discrete.TemperleyKostkaPayne` for more details.
    '''
    values = discrete.TemperleyKostkaPayne.identifiers
    def __init__(self, streamObj, *args, **keywords):
        super(PlotWindowedTemperleyKostkaPayne, self).__init__(streamObj, 
            discrete.TemperleyKostkaPayne(streamObj), *args, **keywords)

    

class PlotWindowedAmbitus(PlotWindowedAnalysis):
    '''Stream plotting of basic pitch span. 

    
    >>> s = corpus.parse('bach/bwv66.6')
    >>> p = graph.plots.PlotWindowedAmbitus(s.parts[0], doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW p = graph.plots.PlotWindowedAmbitus(s.parts[0])
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotWindowedAmbitus.*
        :width: 600

    .. image:: images/legend-PlotWindowedAmbitus.*

    '''
    values = discrete.Ambitus.identifiers
    def __init__(self, streamObj, *args, **keywords):
        # provide the stream to both the window and processor in this case
        super(PlotWindowedAmbitus, self).__init__(streamObj, 
            discrete.Ambitus(streamObj), *args, **keywords)
        





#-------------------------------------------------------------------------------
# horizontal bar graphs

class PlotHorizontalBar(PlotStream):
    '''
    A graph of events, sorted by pitch, over time
    '''
    format = 'horizontalbar'
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHorizontalBar, self).__init__(streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceChromatic
        self.fxTicks = self.ticksOffset

    def _extractData(self):
        dataUnique = {}
        xValues = []
        # collect data
        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj
        for obj in sSrc.getElementsByClass((note.Note, chord.Chord)):
            if 'Chord' in obj.classes:
                values = self._extractChordDataOneAxis(self.fy, obj)
                valueObjPairs = [(v, obj) for v in values]
            else: # its a Note
                valueObjPairs = [(self.fy(obj), obj)]
            for v, objSub in valueObjPairs:
                # rounding to nearest quarter tone
                numericValue = common.roundToHalfInteger(v) #int(v)

                if numericValue not in dataUnique:
                    dataUnique[numericValue] = []
                # all work with offset
                start = objSub.offset
                # this is not the end, but instead the length
                end = objSub.quarterLength
                xValues.append(start)
                xValues.append(end)
                dataUnique[numericValue].append((start, end))
        # create final data list
        # get labels from ticks
        data = []
        # y ticks are auto-generated in lower-level routines
        # this is used just for creating labels
        yTicks = self.fyTicks(min(dataUnique.keys()),
                              max(dataUnique.keys()))

        for numericValue, label in yTicks:
            if numericValue in dataUnique:
                data.append([label, dataUnique[numericValue]])
            else:
                data.append([label, []])
        # use default args for now
        xTicks = self.fxTicks()
        # yTicks are returned, even though they are not used after this method
        return data, xTicks, yTicks


class PlotHorizontalBarPitchClassOffset(PlotHorizontalBar):
    '''A graph of events, sorted by pitch class, over time

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotHorizontalBarPitchClassOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotHorizontalBarPitchClassOffset(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHorizontalBarPitchClassOffset.*
        :width: 600

    '''
    values = ('pitchClass', 'offset', 'pianoroll')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHorizontalBarPitchClassOffset, self).__init__(streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.pitchClass
        self.fyTicks = self.ticksPitchClassUsage
        self.fxTicks = self.ticksOffset # this a method

        self.data, xTicks, unused_yTicks = self._extractData()

        #environLocal.printDebug(['PlotHorizontalBarPitchClassOffset', 
        #    'post processing xTicks', xTicks])

        self.graph = primitives.GraphHorizontalBar(*args, **keywords)
        self.graph.data = self.data

        # only need to add x ticks; y ticks added from data labels
        #environLocal.printDebug(['PlotHorizontalBarPitchClassOffset:', 
        #    'xTicks before setting to self.graph', xTicks])
        self.graph.setTicks('x', xTicks)  

        self.graph.setAxisLabel('x', self._axisLabelMeasureOrOffset())
        self.graph.setAxisLabel('y', 'Pitch Class')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (10, 4)
        if 'title' not in keywords:
            self.graph.title = 'Note Quarter Length and Offset by Pitch Class'


class PlotHorizontalBarPitchSpaceOffset(PlotHorizontalBar):
    '''A graph of events, sorted by pitch space, over time

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotHorizontalBarPitchSpaceOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotHorizontalBarPitchSpaceOffset(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600
    '''
    values = ('pitch', 'offset', 'pianoroll')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHorizontalBarPitchSpaceOffset, self).__init__(streamObj, *args, **keywords)
       
        self.fy = lambda n: n.pitch.ps
        self.fxTicks = self.ticksOffset

        if self.streamObj.isTwelveTone():
            self.fyTicks = self.ticksPitchSpaceUsage
        else:
            self.fyTicks = self.ticksPitchSpaceQuartertoneUsage

        self.data, xTicks, unused_yTicks = self._extractData()

        self.graph = primitives.GraphHorizontalBar(*args, **keywords)
        self.graph.data = self.data

        # only need to add x ticks; y ticks added from data labels
        self.graph.setTicks('x', xTicks)  

        if self.streamObj.recurse().getElementsByClass('Measure'):
            self.graph.setAxisLabel('x', 'Measure Number')
        else:
            self.graph.setAxisLabel('x', 'Offset')
        self.graph.setAxisLabel('y', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (10, 6)
        if 'title' not in keywords:
            self.graph.title = 'Note Quarter Length by Pitch'




#-------------------------------------------------------------------------------
class PlotHorizontalBarWeighted(PlotStream):
    '''A base class for plots of Scores with weighted (by height) horizontal bars. 
    Many different weighted segments can provide a 
    representation of a dynamic parameter of a Part.


    '''
    format = 'horizontalbarweighted'
    def __init__(self, streamObj, *args, **keywords):
        super(PlotHorizontalBarWeighted, self).__init__(streamObj, *args, **keywords)
        # will get Measure numbers if appropraite
        self.fxTicks = self.ticksOffset

        self.fillByMeasure = False
        if 'fillByMeasure' in keywords:
            self.fillByMeasure = keywords['fillByMeasure']
        self.segmentByTarget = True
        if 'segmentByTarget' in keywords:
            self.segmentByTarget = keywords['segmentByTarget']
        self.normalizeByPart = False
        if 'normalizeByPart' in keywords:
            self.normalizeByPart = keywords['normalizeByPart']
        self.partGroups = None
        if 'partGroups' in keywords:
            self.partGroups = keywords['partGroups']


    def _extractData(self):
        '''
        Extract the data from the Stream.
        '''
        if 'Score' not in self.streamObj.classes:
            raise GraphException('provided Stream must be Score')
        # parameters: x, span, heightScalar, color, alpha, yShift
        pr = reduction.PartReduction(self.streamObj, partGroups=self.partGroups, 
                fillByMeasure=self.fillByMeasure, 
                segmentByTarget=self.segmentByTarget, 
                normalizeByPart=self.normalizeByPart)
        pr.process()
        data = pr.getGraphHorizontalBarWeightedData()
        #environLocal.printDebug(['data', data])
        uniqueOffsets = []
        for unused_key, value in data:
            for dataList in value:
                start = dataList[0]
                dur = dataList[1]
                if start not in uniqueOffsets:
                    uniqueOffsets.append(start)
                if start+dur not in uniqueOffsets:
                    uniqueOffsets.append(start+dur)
        yTicks = []
        # use default args for now
        xTicks = self.fxTicks(min(uniqueOffsets), max(uniqueOffsets))
        # yTicks are returned, even though they are not used after this method
        return data, xTicks, yTicks


class PlotDolan(PlotHorizontalBarWeighted):
    '''
    A graph of the activity of a parameter of a part (or a group of parts) over time. 
    The default parameter graphed is Dynamics. Dynamics are assumed to extend activity 
    to the next change in dynamics.

    Numerous parameters can be configured based on functionality encoded in 
    the :class:`~music21.analysis.reduction.PartReduction` object.


    If the `fillByMeasure` parameter is True, and if measures are available, each part 
    will segment by Measure divisions, and look for the target activity only once per 
    Measure. If more than one target is found in the Measure, values will be averaged. 
    If `fillByMeasure` is False, the part will be segmented by each Note. 

    The `segmentByTarget` parameter is True, segments, which may be Notes or Measures, 
    will be divided if necessary to show changes that occur over the duration of the 
    segment by a target object. 

    If the `normalizeByPart` parameter is True, each part will be normalized within the 
    range only of that part. If False, all parts will be normalized by the max of all parts. 
    The default is True. 

    >>> s = corpus.parse('bwv66.6')
    >>> dyn = ['p', 'mf', 'f', 'ff', 'mp', 'fff', 'ppp']
    >>> i = 0
    >>> for p in s.parts:
    ...     for m in p.getElementsByClass('Measure'):
    ...         m.insert(0, dynamics.Dynamic(dyn[i % len(dyn)]))
    ...         i += 1
    ...
    >>> #_DOCS_SHOW s.plot('dolan', fillByMeasure=True, segmentByTarget=True)

    .. image:: images/PlotDolan.*
        :width: 600

    '''
    values = ('instrument',)
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotDolan, self).__init__(streamObj, *args, **keywords)

        #self.fy = lambda n: n.pitch.pitchClass
        #self.fyTicks = self.ticksPitchClassUsage
        self.fxTicks = self.ticksOffset # this is a method

        # must set part groups if not defined here
        self._getPartGroups()
        self.data, xTicks, unused_yTicks = self._extractData()

        self.graph = primitives.GraphHorizontalBarWeighted(*args, **keywords)
        self.graph.data = self.data

        # only need to add x ticks; y ticks added from data labels
        #environLocal.printDebug(['PlotHorizontalBarPitchClassOffset:', 
        #   'xTicks before setting to self.graph', xTicks])
        self.graph.setTicks('x', xTicks)  
        self.graph.setAxisLabel('x', self._axisLabelMeasureOrOffset())
        #self.graph.setAxisLabel('y', '')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (10, 4)
            
        if 'title' not in keywords:
            self.graph.title = 'Instrumentation'
            if self.streamObj.metadata is not None:
                if self.streamObj.metadata.title is not None:
                    self.graph.title = self.streamObj.metadata.title
        if 'hideYGrid' not in keywords:
            self.graph.hideYGrid = True


    def _getPartGroups(self):
        '''
        Examine the instruments in the Score and determine if there 
        is a good match for a default configuration of parts. 
        '''
        if self.partGroups is not None:
            return # keep what the user set

        instStream = self.streamObj.flat.getElementsByClass('Instrument')
        if not instStream:
            return # do not set anything
        
        if len(instStream) == 4 and self.streamObj.getElementById('Soprano') is not None:
            pgOrc = [
                {'name':'Soprano', 'color':'purple', 'match':['soprano', '0']},
                {'name':'Alto', 'color':'orange', 'match':['alto', '1']},
                {'name':'Tenor', 'color':'lightgreen', 'match':['tenor']},
                {'name':'Bass', 'color':'mediumblue', 'match':['bass']}, 
            ]
            self.partGroups = pgOrc
            
        elif len(instStream) == 4 and self.streamObj.getElementById('Viola') is not None:
            pgOrc = [
                {'name':'1st Violin', 'color':'purple', 'match':['1st violin', '0', 'violin 1']},
                {'name':'2nd Violin', 'color':'orange', 'match':['2nd violin', '1', 'violin 2']},
                {'name':'Viola', 'color':'lightgreen', 'match':['viola']},
                {'name':'Cello', 'color':'mediumblue', 'match':['cello', 'violoncello', "'cello"]}, 
            ]
            self.partGroups = pgOrc

        elif len(instStream) > 10:
            pgOrc = [
            {'name':'Timpani', 'color':'#5C3317', 'match':None},
            {'name':'Trumpet', 'color':'red', 'match':['tromba']},
            {'name':'Horns', 'color':'orange', 'match':['corno']},

            {'name':'Flute', 'color':'#C154C1', 'match':['flauto']}, 
            {'name':'Oboe', 'color':'blue', 'match':['oboe']}, 
            {'name':'Clarinet', 'color':'mediumblue', 'match':['clarinetto']}, 
            {'name':'Bassoon', 'color':'purple', 'match':['fagotto']}, 

            {'name':'Violin I', 'color':'lightgreen', 'match':['violino i']},
            {'name':'Violin II', 'color':'green', 'match':['violino ii']},
            {'name':'Viola', 'color':'forestgreen', 'match':None},
            {'name':'Violoncello & CB', 'color':'dark green', 
                'match':['violoncello', 'contrabasso']}, 
#            {'name':'CB', 'color':'#003000', 'match':['contrabasso']},
                    ]
            self.partGroups = pgOrc



#-------------------------------------------------------------------------------
# weighted scatter

class PlotScatterWeighted(PlotStream):

    format = 'scatterWeighted'
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterWeighted, self).__init__(streamObj, *args, **keywords)

        if 'xLog' not in keywords:
            self.xLog = True
        else:
            self.xLog = keywords['xLog']

        # specialize in sub-class
        self.fx = lambda n: float(n.quarterLength)
        self.fy = lambda n: n.pitch.midi
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchClassUsage

    def _extractData(self, xLog=True):
        '''
        If `xLog` is true, x values will be remapped using the remapQuarterLength() function.

        Ultimately, this will need to be madularized
        '''
        environLocal.printDebug([self, 'xLog', xLog])

        dataCount = {}
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
                                                           obj, matchPitchCount=False)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]
            for x in xSrc:
                if xLog:
                    x = self.remapQuarterLength(x)
                if x not in xValues:
                    xValues.append(x)
            for y in ySrc:
                if y not in yValues:
                    yValues.append(y)


        xValues.sort()
        yValues.sort()
        yMin = min(yValues)
        yMax = max(yValues)
        # create a count slot for all possibilities of x/y
        # y is the pitch axis; get all contiguous pirches
        for y, unused_label in self.fyTicks(yMin, yMax):
        #for y in yValues:
            dataCount[y] = [[x, 0] for x in xValues]

        maxCount = 0 # this is the max z value

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
                                                           obj, matchPitchCount=True)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]
            for i, x in enumerate(xSrc):
                y = ySrc[i]
                if xLog:
                    x = self.remapQuarterLength(x)
                indexToIncrement = xValues.index(x)
                # second position stores increment
                dataCount[y][indexToIncrement][1] += 1
                if dataCount[y][indexToIncrement][1] > maxCount:
                    maxCount = dataCount[y][indexToIncrement][1]


#         for noteObj in sSrc.getElementsByClass(note.Note):
#             x = self.fx(noteObj)
#             if xLog:
#                 x = self.remapQuarterLength(x)
#             indexToIncrement = xValues.index(x)
# 
#             # second position stores increment
#             dataCount[self.fy(noteObj)][indexToIncrement][1] += 1
#             if dataCount[self.fy(noteObj)][indexToIncrement][1] > maxCount:
#                 maxCount = dataCount[self.fy(noteObj)][indexToIncrement][1]

        xTicks = self.fxTicks(min(xValues), max(xValues), remap=xLog)
        # create final data list using fy ticks to get values
        data = []
        for y, unused_label in self.fyTicks(yMin, yMax):
            yIndex = y
            for x, z in dataCount[y]:
                data.append([x, yIndex, z])

        # only label y values that are defined
        yTicks = self.fyTicks(yMin, yMax)
        return data, xTicks, yTicks


class PlotScatterWeightedPitchSpaceQuarterLength(PlotScatterWeighted):
    '''A graph of event, sorted by pitch, over time

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterWeightedPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterWeightedPitchSpaceQuarterLength(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchSpaceQuarterLength.*
        :width: 600
    '''
    values = ('pitch', 'quarterLength')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterWeightedPitchSpaceQuarterLength, self).__init__(
                                                streamObj, *args, **keywords)

        self.fx = lambda n: float(n.quarterLength)
        self.fy = lambda n: n.pitch.midi
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchSpaceUsage

        self.data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = primitives.GraphScatterWeighted(*args, **keywords)
        self.graph.data = self.data

        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))
        self.graph.setAxisLabel('y', 'Pitch')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (7, 7)
        if 'title' not in keywords:
            self.graph.title = 'Count of Pitch and Quarter Length'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.8


class PlotScatterWeightedPitchClassQuarterLength(PlotScatterWeighted):
    '''A graph of event, sorted by pitch class, over time.

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterWeightedPitchClassQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterWeightedPitchClassQuarterLength(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchClassQuarterLength.*
        :width: 600

    '''
    values = ('pitchClass', 'quarterLength')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterWeightedPitchClassQuarterLength, self).__init__(
                                                            streamObj, *args, **keywords)

        self.fx = lambda n: float(n.quarterLength)
        self.fy = lambda n: n.pitch.pitchClass
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchClassUsage

        self.data, xTicks, yTicks = self._extractData(xLog = self.xLog)

        self.graph = primitives.GraphScatterWeighted(*args, **keywords)
        self.graph.data = self.data

        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))
        self.graph.setAxisLabel('y', 'Pitch Class')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (7, 7)
        if 'title' not in keywords:
            self.graph.title = 'Count of Pitch Class and Quarter Length'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.8



class PlotScatterWeightedPitchSpaceDynamicSymbol(PlotScatterWeighted):
    '''A graph of dynamics used by pitch space.

    >>> #_DOCS_SHOW s = converter.parse('/Desktop/schumann/opus41no1/movement2.xml')
    >>> s = converter.parse('tinynotation: 4/4 C4 d E f', makeNotation=False) #_DOCS_HIDE
    >>> s.insert(0.0, dynamics.Dynamic('pp')) #_DOCS_HIDE
    >>> s.insert(2.0, dynamics.Dynamic('ff')) #_DOCS_HIDE
    >>> p = graph.plots.PlotScatterWeightedPitchSpaceDynamicSymbol(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW p = graph.plots.PlotScatterWeightedPitchSpaceDynamicSymbol(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchSpaceDynamicSymbol.*
        :width: 600
        
    '''
    values = ('pitchClass', 'dynamicSymbol')
    
    def __init__(self, streamObj, *args, **keywords):
        super(PlotScatterWeightedPitchSpaceDynamicSymbol, self).__init__(
                                                streamObj, *args, **keywords)

        self.fxTicks = self.ticksPitchSpaceUsage
        self.fyTicks = self.ticksDynamics

        # get data from correlate object
        am = correlate.ActivityMatch(self.streamObj)
        self.data = am.pitchToDynamic(dataPoints=False)

        xVals = [x for x, unused_y, unused_z in self.data]
        yVals = [y for unused_x, y, unused_z in self.data]

        xTicks = self.fxTicks(min(xVals), max(xVals))
        # ticks dynamics takes no args
        yTicks = self.fyTicks(min(yVals), max(yVals))


        self.graph = primitives.GraphScatterWeighted(*args, **keywords)
        self.graph.data = self.data

        self.graph.setAxisLabel('x', 'Pitch')
        self.graph.setAxisLabel('y', 'Dynamics')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (10, 10)
        if 'title' not in keywords:
            self.graph.title = 'Count of Pitch Class and Quarter Length'
        if 'alpha' not in keywords:
            self.graph.alpha = 0.8
        # make smaller for axis display
        if 'tickFontSize' not in keywords:
            self.graph.tickFontSize = 7




class Plot3DBars(PlotStream):
    '''
    Base class for Stream plotting classes.
    '''
    format = '3dBars'

    def _extractData(self):
        # TODO: add support for chords
        data = {}
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
                         obj, matchPitchCount=False)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]
            for x in xSrc:
                if x not in xValues:
                    xValues.append(x)
            for y in ySrc:
                if y not in yValues:
                    yValues.append(y)

#         for noteObj in sSrc.getElementsByClass(note.Note):
#             x = self.fx(noteObj)
#             if x not in xValues:
#                 xValues.append(x)
#             y = self.fy(noteObj)
#             if y not in yValues:
#                 yValues.append(y)
        xValues.sort()
        yValues.sort()
        # prepare data dictionary; need to pack all values
        # need to provide spacings even for zero values
        #for y in range(yValues[0], yValues[-1]+1):
        # better to use actual y values
        for y, unused_label in self.fyTicks(min(yValues), max(yValues)):
        #for y in yValues:
            data[y] = [[x, 0] for x in xValues]
        #print _MOD, 'data keys', data.keys()

        maxCount = 0

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, 
                                                           self.fy, 
                                                           obj, 
                                                           matchPitchCount=True)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]

            for i, x in enumerate(xSrc):
                y = ySrc[i]
                indexToIncrement = xValues.index(x)
                # second position stores increment
                data[y][indexToIncrement][1] += 1
                if data[y][indexToIncrement][1] > maxCount:
                    maxCount = data[y][indexToIncrement][1]


#         for noteObj in sSrc.getElementsByClass(note.Note):
#             indexToIncrement = xValues.index(self.fx(noteObj))
#             # second position stores increment
#             #print _MOD, fy(noteObj), indexToIncrement
# 
#             data[self.fy(noteObj)][indexToIncrement][1] += 1
#             if data[self.fy(noteObj)][indexToIncrement][1] > maxCount:
#                 maxCount = data[self.fy(noteObj)][indexToIncrement][1]

        # setting of ticks does not yet work in matplotlib
        xTicks = [(40, 'test')]
        yTicks = self.fyTicks(min(yValues), max(yValues))
        zTicks = []
        return data, xTicks, yTicks, zTicks


class Plot3DBarsPitchSpaceQuarterLength(Plot3DBars):
    '''
    A scatter plot of pitch and quarter length
    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.plots.Plot3DBarsPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW from music21.musicxml import testFiles
    >>> #_DOCS_SHOW s = converter.parse(testFiles.mozartTrioK581Excerpt)
    >>> #_DOCS_SHOW p = graph.plots.Plot3DBarsPitchSpaceQuarterLength(s) 
    >>> p.id
    '3dBars-pitch-quarterLength'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/Plot3DBarsPitchSpaceQuarterLength.*
        :width: 600
    '''
    values = ('pitch', 'quarterLength')
    
    def __init__(self, streamObj, *args, **keywords):
        super(Plot3DBarsPitchSpaceQuarterLength, self).__init__(streamObj, *args, **keywords)

        self.fx = lambda n: float(n.quarterLength)
        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceUsage

        # will use self.fx and self.fxTick to extract data
        self.data, unused_xTicks, unused_yTicks, unused_zTicks = self._extractData()

        self.graph = primitives.Graph3DBars(*args, **keywords)
        self.graph.data = self.data

        #self.graph.setTicks('y', yTicks)
        #self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'MIDI Note Number')
        self.graph.setAxisLabel('x', 'Quarter Length')
        self.graph.setAxisLabel('z', '')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (6, 6)
        if 'title' not in keywords:
            self.graph.title = 'Pitch by Quarter Length Count'
        if 'barWidth' not in keywords:
            self.graph.barWidth = 0.1
        if 'alpha' not in keywords:
            self.graph.alpha = 0.5




#-------------------------------------------------------------------------------
# plot multi stream

class PlotFeatures(PlotMultiStream):
    '''
    Plots the output of a set of feature extractors.
    
    FeatureExtractors can be ids or classes. 
    '''
    format = 'features'

    def __init__(self, streamList, featureExtractors, labelList=None, *args, **keywords):
        if labelList is None:
            labelList = []
        
        super(PlotFeatures, self).__init__(streamList, labelList, *args, **keywords)

        self.featureExtractors = featureExtractors

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        self.graph = primitives.GraphGroupedVerticalBar(*args, **keywords)
        self.graph.grid = False
        self.graph.data = self.data

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)


        self.graph.xTickLabelRotation = 90
        self.graph.xTickLabelHorizontalAlignment = 'left'
        self.graph.xTickLabelVerticalAlignment = 'top'

        #self.graph.setAxisLabel('y', 'Count')
        #self.graph.setAxisLabel('x', 'Streams')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.figureSize = (10, 6)
        if 'title' not in keywords:
            self.graph.title = None


    def _extractData(self):
        if len(self.labelList) != len(self.streamList):
            labelList = [x+1 for x in range(len(self.streamList))]
        else:
            labelList = self.labelList

        feList = []
        for fe in self.featureExtractors:
            if isinstance(fe, six.string_types):
                post = features.extractorsById(fe)
                for sub in post:
                    feList.append(sub())
            else: # assume a class
                feList.append(fe())

        # store each stream in a data instance
        diList = []
        for s in self.streamList:
            di = features.DataInstance(s)
            diList.append(di)

        data = []
        for i, di in enumerate(diList):
            sub = {}
            for fe in feList:
                fe.data = di
                v = fe.extract().vector
                if len(v) == 1:
                    sub[fe.name] = v[0]
                # average all values?
                else:
                    sub[fe.name] = sum(v)/float(len(v))
            dataPoint = [labelList[i], sub]
            data.append(dataPoint)

        #environLocal.printDebug(['data', data])

        xTicks = []
        for x, label in enumerate(labelList):
            # first value needs to be center of bar
            # value of tick is the string entry
            xTicks.append([x+.5, '%s' % label])
        # alway have min and max
        yTicks = []
        return data, xTicks, yTicks

#------------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    

    def testPlotHorizontalBarPitchSpaceOffset(self):
        a = corpus.parse('bach/bwv57.8')
        # do not need to call flat version
        b = PlotHorizontalBarPitchSpaceOffset(a.parts[0], title='Bach (soprano voice)')
        b.process()
        

        b = PlotHorizontalBarPitchSpaceOffset(a, title='Bach (all parts)')
        b.process()
        



    def testPlotHorizontalBarPitchClassOffset(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHorizontalBarPitchClassOffset(a.parts[0], title='Bach (soprano voice)')
        b.process()
        

        a = corpus.parse('bach/bwv57.8')
        b = PlotHorizontalBarPitchClassOffset(a.parts[0].measures(3,6), 
                                              title='Bach (soprano voice, mm 3-6)')
        b.process()
        

    def testPlotScatterWeightedPitchSpaceQuarterLength(self):
        for xLog in [True, False]:
            a = corpus.parse('bach/bwv57.8')
            b = PlotScatterWeightedPitchSpaceQuarterLength(a.parts[0].flat,
                            title='Pitch Space Bach (soprano voice)',
                            xLog=xLog)
            b.process()
    
            a = corpus.parse('bach/bwv57.8')
            b = PlotScatterWeightedPitchClassQuarterLength(a.parts[0].flat,
                            title='Pitch Class Bach (soprano voice)',
                            xLog=xLog)
            b.process()


    def testPlotPitchSpace(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramPitchSpace(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()
        

    def testPlotPitchClass(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramPitchClass(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotQuarterLength(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramQuarterLength(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotScatterPitchSpaceQuarterLength(self):
        for xLog in [True, False]:

            a = corpus.parse('bach/bwv57.8')
            b = PlotScatterPitchSpaceQuarterLength(a.parts[0].flat, title='Bach (soprano voice)', 
                                                   xLog=xLog)
            b.process()
    
            b = PlotScatterPitchClassQuarterLength(a.parts[0].flat, title='Bach (soprano voice)', 
                                                   xLog=xLog)
            b.process()

    def testPlotScatterPitchClassOffset(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotScatterPitchClassOffset(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotScatterPitchSpaceDynamicSymbol(self):
        a = corpus.parse('schumann/opus41no1', 2)
        b = PlotScatterPitchSpaceDynamicSymbol(a.parts[0].flat, title='Schumann (soprano voice)')
        b.process()
        

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(a.parts[0].flat, 
                                                       title='Schumann (soprano voice)')
        b.process()
        



    def testPlot3DPitchSpaceQuarterLengthCount(self):
        a = corpus.parse('schoenberg/opus19', 6) # also tests Tuplets
        b = Plot3DBarsPitchSpaceQuarterLength(a.flat.stripTies(), title='Schoenberg pitch space')
        b.process()
        
    
    def writeAllPlots(self):
        '''
        Write a graphic file for all graphs, naming them after the appropriate class. 
        This is used to generate documentation samples.
        '''
        # TODO: need to add strip() ties here; but need stripTies on Score
        from music21.musicxml import testFiles 

        plotClasses = [
        # histograms
        (PlotHistogramPitchSpace, None, None), 
        (PlotHistogramPitchClass, None, None), 
        (PlotHistogramQuarterLength, None, None),
        # scatters
        (PlotScatterPitchSpaceQuarterLength, None, None), 
        (PlotScatterPitchClassQuarterLength, None, None), 
        (PlotScatterPitchClassOffset, None, None),
        (PlotScatterPitchSpaceDynamicSymbol, 
            corpus.getWork('schumann/opus41no1', 2), 'Schumann Opus 41 No 1'),

        # offset based horizontal
        (PlotHorizontalBarPitchSpaceOffset, None, None), 
        (PlotHorizontalBarPitchClassOffset, None, None),
        # weighted scatter
        (PlotScatterWeightedPitchSpaceQuarterLength, None, None), 
        (PlotScatterWeightedPitchClassQuarterLength, None, None),
        (PlotScatterWeightedPitchSpaceDynamicSymbol, 
            corpus.getWork('schumann/opus41no1', 2), 'Schumann Opus 41 No 1'),


        # 3d graphs
        (Plot3DBarsPitchSpaceQuarterLength, 
            testFiles.mozartTrioK581Excerpt, 'Mozart Trio K581 Excerpt'), # @UndefinedVariable

        (PlotWindowedKrumhanslSchmuckler, corpus.getWork('bach/bwv66.6.xml'), 'Bach BWV 66.6'),
        (PlotWindowedAmbitus, corpus.getWork('bach/bwv66.6.xml'), 'Bach BWV 66.6'),

        ]



        sDefault = corpus.parse('bach/bwv57.8')

        for plotClassName, work, titleStr in plotClasses:
            if work is None:
                s = sDefault

            else: # expecting data
                s = converter.parse(work)

            if titleStr is not None:
                obj = plotClassName(s, doneAction=None, title=titleStr)
            else:
                obj = plotClassName(s, doneAction=None)

            obj.process()
            fn = obj.__class__.__name__ + '.png'
            fp = os.path.join(environLocal.getRootTempDir(), fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)

    


class Test(unittest.TestCase):
   
    def runTest(self):
        pass
   

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)



    def testPlotPitchSpaceDurationCount(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotScatterWeightedPitchSpaceQuarterLength(a.parts[0].flat, doneAction=None,
                        title='Bach (soprano voice)')
        b.process()
        

    def testPlotPitchSpace(self):
        a = corpus.parse('bach')
        b = PlotHistogramPitchSpace(a.parts[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()
        

    def testPlotPitchClass(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramPitchClass(a.parts[0].flat, 
                                    doneAction=None, title='Bach (soprano voice)')
        b.process()
        

    def testPlotQuarterLength(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramQuarterLength(a.parts[0].flat, 
                                       doneAction=None, title='Bach (soprano voice)')
        b.process()
        

    def testPitchDuration(self):
        a = corpus.parse('schoenberg/opus19', 2)
        b = PlotScatterPitchSpaceDynamicSymbol(a.parts[0].flat, 
                                               doneAction=None, title='Schoenberg (piano)')
        b.process()
        

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(a.parts[0].flat, 
                                                       doneAction=None, title='Schoenberg (piano)')
        b.process()
        

        
    def testPlotWindowed(self, doneAction=None):
        if doneAction is not None: # pragma: no cover
            fp = random.choice(corpus.getBachChorales('.xml'))
            unused_directory, fn = os.path.split(fp)
            a = corpus.parse(fp)
            windowStep = 3 #'2'
            #windowStep = random.choice([1,2,4,8,16,32])
            #a.show()
        else:
            a = corpus.parse('bach/bwv66.6')
            fn = 'bach/bwv66.6'
            windowStep = 20 # set high to be fast

#         b = PlotWindowedAmbitus(a.parts, title='Bach Ambitus',
#             minWindow=1, maxWindow=8, windowStep=3,
#             doneAction=doneAction)
#         b.process()

        b = PlotWindowedKrumhanslSchmuckler(a, title=fn,
            minWindow=1, windowStep=windowStep, 
            doneAction=doneAction, dpi=300)
        b.process()
        

    def testPlotFeatures(self):
        streamList = ['bach/bwv66.6', 'schoenberg/opus19/movement2', 'corelli/opus3no1/1grave']
        feList = ['ql1', 'ql2', 'ql3']

        p = PlotFeatures(streamList, featureExtractors=feList, doneAction=None)
        p.process()


    
    def testPianoRollFromOpus(self):
        o = corpus.parse('josquin/laDeplorationDeLaMorteDeJohannesOckeghem')
        s = o.mergeScores()

        b = PlotHorizontalBarPitchClassOffset(s, doneAction=None)
        b.process()
        


    def testPlotChordsA(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        b = PlotHistogram(stream.Stream(), doneAction=None)
        c = chord.Chord(['b', 'c', 'd'])
        fx = lambda n: n.pitch.midi
        self.assertEqual(b._extractChordDataOneAxis(fx, c), [71, 60, 62])


        s = stream.Stream()
        s.append(chord.Chord(['b', 'c#', 'd']))
        s.append(note.Note('c3'))
        s.append(note.Note('c5'))
        b = PlotHistogramPitchSpace(s, doneAction=None)
        b.process()
        
        #b.write()
        self.assertEqual(b.data, [(48, 1), (61, 1), (62, 1), (71, 1), (72, 1)])

        s = stream.Stream()
        s.append(sc.getChord('e3', 'a3'))
        s.append(note.Note('c3'))
        b = PlotHistogramPitchClass(s, doneAction=None)
        b.process()
        
        #b.write()
        self.assertEqual(b.data, [(0, 1), (4, 1), (5, 1), (7, 1), (9, 1)])

        s = stream.Stream()
        s.append(sc.getChord('e3', 'a3', quarterLength=2))
        s.append(note.Note('c3', quarterLength=0.5))
        b = PlotHistogramQuarterLength(s, doneAction=None)
        b.process()
        
        #b.write()
        self.assertEqual(b.data, [(0, 1), (1, 1)])


        # test scatter plots


        b = PlotScatter(stream.Stream(), doneAction=None)
        c = chord.Chord(['b', 'c', 'd'], quarterLength=0.5)
        fx = lambda n: n.pitch.midi
        fy = lambda n: float(n.quarterLength)
        self.assertEqual(b._extractChordDataTwoAxis(fx, fy, c), ([71, 60, 62], [0.5]))
        c = chord.Chord(['b', 'c', 'd'], quarterLength=0.5)
        # matching the number of pitches for each data point may be needed
        self.assertEqual(b._extractChordDataTwoAxis(fx, fy, c, matchPitchCount=True), 
                         ([71, 60, 62], [0.5, 0.5, 0.5]) )

    def testPlotChordsA2(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        s.append(sc.getChord('b3', 'c5', quarterLength=1.5))
        s.append(note.Note('c3', quarterLength=2))
        b = PlotScatterPitchSpaceQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, [[2, 48], [0.5, 52], [0.5, 53], [0.5, 55], [0.5, 57], 
                                  [1.5, 59], [1.5, 60], [1.5, 62], [1.5, 64], [1.5, 65], 
                                  [1.5, 67], [1.5, 69], [1.5, 71], [1.5, 72]])
        #b.write()

    def testPlotChordsA3(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        s.append(sc.getChord('b3', 'c5', quarterLength=1.5))
        s.append(note.Note('c3', quarterLength=2))
        b = PlotScatterPitchClassQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, [[2, 0], [0.5, 4], [0.5, 5], [0.5, 7], [0.5, 9], [1.5, 11], 
                                  [1.5, 0], [1.5, 2], [1.5, 4], [1.5, 5], [1.5, 7], [1.5, 9], 
                                  [1.5, 11], [1.5, 0]] )
        #b.write()

    def testPlotChordsA4(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        s.append(note.Note('d3', quarterLength=2))
        self.assertEqual([e.offset for e in s], [0.0, 0.5, 2.5, 4.0])

        #s.show()
        b = PlotScatterPitchClassOffset(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [[0.5, 0], [4.0, 2], [0.0, 4], [0.0, 5], [0.0, 7], 
                                  [0.0, 9], [2.5, 11], [2.5, 0], [2.5, 2], [2.5, 4]] )
        #b.write()

    def testPlotChordsA5(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(dynamics.Dynamic('p'))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        #s.append(note.Note('d3', quarterLength=2))

        #s.show()
        b = PlotScatterPitchSpaceDynamicSymbol(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [[52, 8], [53, 8], [55, 8], [57, 8], [59, 8], [59, 5], 
                                  [60, 8], [60, 5], [62, 8], [62, 5], [64, 8], [64, 5]])
        #b.write()


    def testPlotChordsB(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))

        b = PlotHorizontalBarPitchClassOffset(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [['C', [(0.0, 1.0), (1.5, 1.5)]], ['', []], 
                                  ['D', [(1.5, 1.5)]], ['', []], ['E', [(1.0, 0.5), (1.5, 1.5)]],
                                   ['F', [(1.0, 0.5)]], ['', []], ['G', [(1.0, 0.5)]], 
                                   ['', []], ['A', [(1.0, 0.5)]], ['', []], ['B', [(1.5, 1.5)]]] )
        #b.write()


        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))

        b = PlotHorizontalBarPitchSpaceOffset(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [['C3', [(0.0, 1.0)]], ['', []], ['', []], ['', []], 
                                  ['E3', [(1.0, 0.5)]], ['F3', [(1.0, 0.5)]], ['', []], 
                                  ['G3', [(1.0, 0.5)]], ['', []], ['A3', [(1.0, 0.5)]], ['', []], 
                                  ['B3', [(1.5, 1.5)]], ['C4', [(1.5, 1.5)]], ['', []], 
                                  ['D4', [(1.5, 1.5)]], ['', []], ['E4', [(1.5, 1.5)]]] )
        #b.write()


        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = PlotScatterWeightedPitchSpaceQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data[0:7], [[0.5, 48, 0], [1.0, 48, 1], [1.5, 48, 0], 
                                       [3, 48, 0], [0.5, 49, 0], [1.0, 49, 0], [1.5, 49, 0]])
        #b.write()



        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = PlotScatterWeightedPitchClassQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data[0:8], [[0.5, 0, 0], [1.0, 0, 1], [1.5, 0, 1], 
                                       [3, 0, 3],   [0.5, 1, 0], [1.0, 1, 0], 
                                       [1.5, 1, 0], [3, 1, 0]])
        #b.write()

    def testPlotChordsB2(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        #s.append(note.Note('c3'))
        c = sc.getChord('e3', 'a3', quarterLength=0.5)
        self.assertEqual(repr(c), '<music21.chord.Chord E3 F3 G3 A3>')
        self.assertEqual([n.pitch.ps for n in c], [52.0, 53.0, 55.0, 57.0])
        s.append(c)
        #s.append(note.Note('c3', quarterLength=2))
        s.append(dynamics.Dynamic('mf'))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        s.append(dynamics.Dynamic('pp'))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(s, doneAction=None, xLog=False)
        b.process()
        
        self.maxDiff = 2048
        # TODO: Is this right? why are the old dynamics still active?
        self.assertEqual(b.data, [(52.0, 8, 1), (53.0, 8, 1), (55.0, 8, 1), (57.0, 8, 1), 
                                  (59.0, 8, 1), (59.0, 7, 1), (60.0, 8, 1), (60.0, 7, 1), 
                                  (62.0, 8, 1), (62.0, 7, 1), (64.0, 8, 1), (64.0, 7, 1), 
                                  (65.0, 7, 1), (65.0, 4, 2), 
                                  (67.0, 7, 1), (67.0, 4, 2), (69.0, 7, 1), (69.0, 4, 2), 
                                  (71.0, 7, 1), (71.0, 4, 2), (72.0, 7, 1), (72.0, 4, 3), # C x 3
                                  (74.0, 7, 1), (74.0, 4, 2), (76.0, 7, 1), (76.0, 4, 2), 
                                  (77.0, 7, 1), (77.0, 4, 2), (79.0, 7, 1), (79.0, 4, 2)])
        #b.write()

    def testPlotChordsB3(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')


        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3', 'a3', quarterLength=0.5))
        s.append(dynamics.Dynamic('mf'))
        s.append(sc.getChord('b3', 'e4', quarterLength=1.5))
        s.append(dynamics.Dynamic('pp'))
        s.append(sc.getChord('f4', 'g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = Plot3DBarsPitchSpaceQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data[48], [[0.5, 0], [1.0, 1], [1.5, 0], [3, 0]])
        #b.write()

    def testPlotDolanA(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotDolan(a, title='Bach', doneAction=None)
        b.process()
        
        #b.show()


    def xtestGraphVerticalBar(self): # pragma: no cover
        #streamList = corpus.parse('essenFolksong/han1')
        streamList = corpus.getBachChorales()[100:108]
        feList = ['m17', 'm18', 'm19', 'ql1']
        #labelList = [os.path.basename(fp) for fp in streamList]
        p = PlotFeatures(streamList, feList)
        p.process()


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [
        PlotHistogramPitchSpace, 
        PlotHistogramPitchClass, 
        PlotHistogramQuarterLength,
        # windowed
        PlotWindowedKrumhanslSchmuckler, 
        PlotWindowedAmbitus,
        # scatters
        PlotScatterPitchSpaceQuarterLength, 
        PlotScatterPitchClassQuarterLength, 
        PlotScatterPitchClassOffset,
        PlotScatterPitchSpaceDynamicSymbol,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, 
        PlotHorizontalBarPitchClassOffset,
        PlotDolan,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, 
        PlotScatterWeightedPitchClassQuarterLength,
        PlotScatterWeightedPitchSpaceDynamicSymbol,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
]


if __name__ == "__main__":
    bach = corpus.parse('bwv66.6')
    p = PlotScatter(bach)
    p.run()
    
    import music21
    music21.mainTest(Test) #, runTest='testPlot3DPitchSpaceQuarterLengthCount')


