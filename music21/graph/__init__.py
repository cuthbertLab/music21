# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         graph.py
# Purpose:      Classes for graphing in matplotlib and/or other graphing tools.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2012, 2017 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Object definitions for graphing and plotting :class:`~music21.stream.Stream` objects. 

The :class:`~music21.graph.primatives.Graph` object subclasses abstract fundamental 
graphing archetypes using the matplotlib library. The :class:`~music21.graph.plots.Plot` 
object subclasses provide reusable approaches to graphing data and structures in 
:class:`~music21.stream.Stream` objects.

The most common way of using plotting functions is to call `.plot()` on a Stream. 
'''
from __future__ import division, print_function, absolute_import

__all__ = ['plots', 'primatives', 'utilities']

from music21 import common

from music21.graph import primatives
from music21.graph import plots
from music21.graph import utilities

import unittest


from music21 import environment
_MOD = 'graph.py'
environLocal = environment.Environment(_MOD)    



#-------------------------------------------------------------------------------
# public function
def getPlotsToMake(*args, **keywords):
    '''
    Given `format` and `values` provided as arguments or keywords, return a list of plot classes.
    
    no arguments = horizontalbar

    >>> graph.getPlotsToMake()
    [<class 'music21.graph.plots.PlotHorizontalBarPitchSpaceOffset'>]
    
    >>> graph.getPlotsToMake('windowed')
    [<class 'music21.graph.plots.PlotWindowedTemperleyKostkaPayne'>]
    '''
    plotClasses = [
        # histograms
        plots.PlotHistogramPitchSpace, 
        plots.PlotHistogramPitchClass, 
        plots.PlotHistogramQuarterLength,
        # scatters
        plots.PlotScatterPitchSpaceQuarterLength, 
        plots.PlotScatterPitchClassQuarterLength, 
        plots.PlotScatterPitchClassOffset,
        plots.PlotScatterPitchSpaceDynamicSymbol,
        # offset based horizontal
        plots.PlotHorizontalBarPitchSpaceOffset, 
        plots.PlotHorizontalBarPitchClassOffset,
        # weighted scatter
        plots.PlotScatterWeightedPitchSpaceQuarterLength, 
        plots.PlotScatterWeightedPitchClassQuarterLength,
        plots.PlotScatterWeightedPitchSpaceDynamicSymbol,
        # 3d graphs
        plots.Plot3DBarsPitchSpaceQuarterLength,
        # windowed plots
        plots.PlotWindowedKrumhanslSchmuckler,
        plots.PlotWindowedKrumhanslKessler,
        plots.PlotWindowedAardenEssen,
        plots.PlotWindowedSimpleWeights,
        plots.PlotWindowedBellmanBudge,
        plots.PlotWindowedTemperleyKostkaPayne,
        plots.PlotWindowedAmbitus,
        # instrumentation and part graphs
        plots.PlotDolan,
    ]

    showFormat = ''
    values = ()

    # can match by format
    if 'format' in keywords:
        showFormat = keywords['format']
    elif 'showFormat' in keywords:
        showFormat = keywords['showFormat']

    if 'values' in keywords:
        values = keywords['values'] # should be a tuple or list

    #environLocal.printDebug(['got args pre conversion', args])
    # if no args, use pianoroll
    foundClassName = None
    if (not args 
            and showFormat == '' 
            and not values):
        showFormat = 'horizontalbar'
        values = 'pitch'
    elif len(args) == 1:
        formatCandidate = utilities.userFormatsToFormat(args[0])
        #environLocal.printDebug(['formatCandidate', formatCandidate])
        match = False
        if formatCandidate in utilities.FORMATS:
            showFormat = formatCandidate
            values = 'pitch'
            match = True
        # if one arg, assume it is a histogram value
        if formatCandidate in utilities.VALUES:
            showFormat = 'histogram'
            values = (args[0],)
            match = True
        # permit directly matching the class name
        if not match:
            for className in plotClasses:
                if formatCandidate in str(className).lower():
                    match = True
                    foundClassName = className
                    break
    elif len(args) > 1:
        showFormat = utilities.userFormatsToFormat(args[0])
        values = args[1:] # get all remaining
    if not common.isListLike(values):
        values = (values,)
        
    # make it mutable
    values = list(values)

    #environLocal.printDebug(['got args post conversion', 'format', showFormat, 
    #    'values', values, 'foundClassName', foundClassName])

    # clean data and process synonyms
    # will return unaltered if no change
    showFormat = utilities.userFormatsToFormat(showFormat) 
    values = utilities.userValuesToValues(values)
    #environLocal.printDebug(['plotStream: format, values', showFormat , values])

    plotMake = []
    if showFormat.lower() == 'all':
        plotMake = plotClasses
    elif foundClassName is not None:
        plotMake = [foundClassName] # place in a list
    else:
        plotMakeCandidates = [] # store pairs of score, class
        for plotClassName in plotClasses:
            # try to match by complete class name
            if plotClassName.__name__.lower() == showFormat.lower():
                #environLocal.printDebug(['got plot class:', plotClassName])
                plotMake.append(plotClassName)

            # try direct match of format and values
            plotClassNameValues = [x.lower() for x in plotClassName.values]
            plotClassNameFormat = plotClassName.format.lower()
            if plotClassNameFormat != showFormat.lower():
                continue
            #environLocal.printDebug(['matching format', showFormat])
            # see if a matching set of values is specified
            # normally plots need to match all values 
            match = []
            for requestedValue in values:
                if requestedValue is None: 
                    continue
                if (requestedValue.lower() in plotClassNameValues
                        and requestedValue not in match):
                    # do not allow the same value to be requested
                    match.append(requestedValue)
            if len(match) == len(values):
                plotMake.append(plotClassName)
            else:
                sortTuple = (len(match), plotClassName)
                plotMakeCandidates.append(sortTuple)

        # if no matches, try something more drastic:
        if not plotMake and plotMakeCandidates:
            plotMakeCandidates.sort(key=lambda x: (x[0], x[1].__name__.lower()) )
            # last in list has highest score; second item is class
            plotMake.append(plotMakeCandidates[-1][1])

        elif not plotMake: # none to make and no candidates
            for plotClassName in plotClasses:
                # create a list of all possible identifiers
                plotClassIdentifiers = [plotClassName.format.lower()]
                plotClassIdentifiers += [x.lower() for x in plotClassName.values]
                # combine format and values args
                for requestedValue in [showFormat] + values:
                    if requestedValue.lower() in plotClassIdentifiers:
                        plotMake.append(plotClassName)
                        break
                if plotMake: # found a match
                    break
    #environLocal.printDebug(['plotMake', plotMake])
    return plotMake

def plotStream(streamObj, *args, **keywords):
    '''
    Given a stream and any keyword configuration arguments, create and display a plot.

    Note: plots require matplotib to be installed.

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
    subclass :attr:`~music21.analysis.discrete.DiscreteAnalysis.indentifiers` list 
    is added to the Plot's `values` list. 

    Available plots include the following:

    * :class:`~music21.graph.PlotHistogramPitchSpace`
    * :class:`~music21.graph.PlotHistogramPitchClass`
    * :class:`~music21.graph.PlotHistogramQuarterLength`
    * :class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`
    * :class:`~music21.graph.PlotScatterPitchClassQuarterLength`
    * :class:`~music21.graph.PlotScatterPitchClassOffset`
    * :class:`~music21.graph.PlotScatterPitchSpaceDynamicSymbol`
    * :class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`
    * :class:`~music21.graph.PlotHorizontalBarPitchClassOffset`
    * :class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`
    * :class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`
    * :class:`~music21.graph.PlotScatterWeightedPitchSpaceDynamicSymbol`
    * :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`
    * :class:`~music21.graph.PlotWindowedKrumhanslSchmuckler`
    * :class:`~music21.graph.PlotWindowedKrumhanslKessler`
    * :class:`~music21.graph.PlotWindowedAardenEssen`
    * :class:`~music21.graph.PlotWindowedSimpleWeights`
    * :class:`~music21.graph.PlotWindowedBellmanBudge`
    * :class:`~music21.graph.PlotWindowedTemperleyKostkaPayne`
    * :class:`~music21.graph.PlotWindowedAmbitus`
    * :class:`~music21.graph.PlotDolan`


    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('histogram', 'pitch', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('histogram', 'pitch')

    .. image:: images/PlotHistogramPitchSpace.*
        :width: 600


    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('pianoroll')

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600

    '''
    plotMake = getPlotsToMake(*args, **keywords)
    #environLocal.printDebug(['plotClassName found', plotMake])
    for plotClassName in plotMake:
        obj = plotClassName(streamObj, *args, **keywords)
        obj.process()

        

#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
   
    def runTest(self):
        pass
   
    def testAll(self):
        from music21 import corpus
        a = corpus.parse('bach/bwv57.8')
        plotStream(a.flat, 'all')





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
        #s.append(note.Note('c3', quarterLength=2))
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
            #s.plot(*args, doneAction='write')
            s.plot(*args, doneAction=None)
        

    def testGetPlotsToMakeA(self):
        post = getPlotsToMake(format='grid', values='krumhansl-schmuckler')
        self.assertEqual(post, [plots.PlotWindowedKrumhanslSchmuckler])
        post = getPlotsToMake(format='grid', values='aarden')
        self.assertEqual(post, [plots.PlotWindowedAardenEssen])
        post = getPlotsToMake(format='grid', values='simple')
        self.assertEqual(post, [plots.PlotWindowedSimpleWeights])
        post = getPlotsToMake(format='grid', values='bellman')
        self.assertEqual(post, [plots.PlotWindowedBellmanBudge])
        post = getPlotsToMake(format='grid', values='kostka')
        self.assertEqual(post, [plots.PlotWindowedTemperleyKostkaPayne])
        post = getPlotsToMake(format='grid', values='KrumhanslKessler')
        self.assertEqual(post, [plots.PlotWindowedKrumhanslKessler])


        # no args get pitch space piano roll
        post = getPlotsToMake()
        self.assertEqual(post, [plots.PlotHorizontalBarPitchSpaceOffset])

        # one arg gives a histogram of that parameters
        post = getPlotsToMake('duration')
        self.assertEqual(post, [plots.PlotHistogramQuarterLength])
        post = getPlotsToMake('quarterLength')
        self.assertEqual(post, [plots.PlotHistogramQuarterLength])
        post = getPlotsToMake('ps')
        self.assertEqual(post, [plots.PlotHistogramPitchSpace])
        post = getPlotsToMake('pitch')
        self.assertEqual(post, [plots.PlotHistogramPitchSpace])
        post = getPlotsToMake('pitchspace')
        self.assertEqual(post, [plots.PlotHistogramPitchSpace])
        post = getPlotsToMake('pc')
        self.assertEqual(post, [plots.PlotHistogramPitchClass])

        post = getPlotsToMake('scatter', 'ps')
        self.assertEqual(post, [plots.PlotScatterPitchSpaceQuarterLength])
        post = getPlotsToMake('scatter', 'ps', 'duration')
        self.assertEqual(post, [plots.PlotScatterPitchSpaceQuarterLength])

        post = getPlotsToMake('scatter', 'pc', 'offset')
        self.assertEqual(post, [plots.PlotScatterPitchClassOffset])


    def testGetPlotsToMakeB(self):
        post = getPlotsToMake('dolan')
        self.assertEqual(post, [plots.PlotDolan])
        post = getPlotsToMake(values='instrument')
        self.assertEqual(post, [plots.PlotDolan])
        post = getPlotsToMake(format='horizontalbarweighted')
        self.assertEqual(post, [plots.PlotDolan])

#     def testMeasureNumbersA(self):
#         from music21 import corpus, graph
#         s = corpus.parse('bwv66.6')
#         p = graph.PlotHorizontalBarPitchClassOffset(s)
#         #p.process()

#     def testHorizontalInstrumentationA(self):
#         s = corpus.parse('symphony94/02')
#         unused_g = PlotDolan(s, fillByMeasure=False, segmentByTarget=True, 
#             normalizeByPart = False, title='Haydn, Symphony No. 94 in G major, Movement II',
#             hideYGrid=True, hideXGrid=True, alpha=1, figureSize=[60,4], dpi=300, )

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


#------------------------------------------------------------------------------
_DOC_ORDER = [plotStream, getPlotsToMake]


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, runTest='testPlot3DPitchSpaceQuarterLengthCount')

#------------------------------------------------------------------------------
# eof
