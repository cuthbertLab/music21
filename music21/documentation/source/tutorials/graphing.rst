.. _graphing:



Graphing Utilities
======================================

Music21 can create graphs and plots of multiple musical attributes 
using high-level analysis tools.

Graphs are any sort of graphical display.  Plots are displays that
run on a Stream and report data found in a Stream.

Users can create their own custom graphing routines by extending or 
reworking existing music21 :class:`~music21.graph.Graph` and :class:`~music21.graph.PlotStream` classes. 

Alternatively, music21 has numerous pre-built Graph and Plot classes 
for quick access to common graphical views such as piano rolls, etc.

Installing and Using matplotlib
-------------------------------

The powerful and flexible graphing routines of music21 use the matplotlib and numpy libraries. 
They can be downloaded from the following URLs:

http://numpy.scipy.org
http://sourceforge.net/projects/matplotlib/files/

For instructions on getting them installed and running see the following URL:

http://matplotlib.sourceforge.net/users/installing.html

For more information about matplotlib with music21 see :ref:`advancedGraphing`.


Plotting Streams
-------------------------------------------------------

Music21 features numerous ways to display the data within a Stream. 

Complete documentation for these graphing objects can be found 
with the following classes: :class:`~music21.graph.PlotHistogramPitchSpace`, 
:class:`~music21.graph.PlotHistogramPitchClass`, :class:`~music21.graph.PlotHistogramQuarterLength`, 
:class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`, :class:`~music21.graph.PlotScatterPitchClassOffset`,  :class:`~music21.graph.PlotHorizontalBarPitchClassOffset`,
:class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`, 
:class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`, 
:class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`, :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`, :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`, 


The plotStream() Utility Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The graph.py module offers the :func:`~music21.graph.plotStream` function 
for easy access to graphing music21 Streams. This function requires a Stream 
as an argument and a number of additional arguments to specify the output of one or more plot types. 

Calling :func:`~music21.graph.plotStream` with no arguments creates a 
default graph, using :class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`, of a flat version of the Stream:

    >>> from music21 import corpus, graph
    >>> aStream = corpus.parse('bach/bwv57.8')
    >>> graph.plotStream(aStream)    # doctest: +SKIP


    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600


Calling :func:`~music21.graph.plotStream` with a Stream and the name of plot 
class will use that class to create a and display a graph. 


    >>> graph.plotStream(aStream, 'PlotHistogramPitchClass')  # doctest: +SKIP

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600

Alternatively, the type of desired graph can be given as the `format` keyword argument, 
and list of values desired can be given with the `values` keyword argument. If one or 
more plots are available that match the requested values, these will be displayed


    >>> graph.plotStream(aStream, format='scatterweighted') # doctest: +SKIP

    .. image:: images/PlotScatterWeightedPitchSpaceQuarterLength.*
        :width: 600

    >>> graph.plotStream(aStream, format='scatter', values=['pitch'])  # doctest: +SKIP

    .. image:: images/PlotScatterPitchSpaceQuarterLength.*
        :width: 600

Note that the exact same functionality of :func:`~music21.graph.plotStream` is available as the 
Stream :meth:`~music21.stream.Stream.plot` method.


    >>> aStream.plot(format='scatterweighted', values='pitchclass') # doctest: +SKIP

    .. image:: images/PlotScatterWeightedPitchClassQuarterLength.*
        :width: 600



Creating and Calling Plot Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphs can be created and/or written to a file by creating an instance of a plot class 
with the Stream as an argument. Once created, the object's :meth:`~music21.graph.Graph.process` method is called 
to obtain a result. The result is determined by the `doneAction` keyword argument.

    >>> from music21 import corpus, graph
    >>> aStream = corpus.parse('bach/bwv57.8')
    >>> aPlot = graph.PlotHistogramPitchClass(aStream)
    >>> aPlot.process()  # doctest: +SKIP

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600


The default `Action` is to call :meth:`~music21.graph.Graph.show` method the graph, which 
will write it as a temporary file and open the graph. To write a graph to 
a file, use the :meth:`~music21.graph.Graph.write` with a file path as the argument.


Analytical Graphing Objects
-------------------------------------------------------

Music21 features graphing objects that display the results of analysis.
Complete documentation for these graphing objects can be found with the 
following classes: :class:`~music21.graph.PlotWindowedKrumhanslSchmuckler`, 
:class:`~music21.graph.PlotWindowedKrumhanslKessler`, :class:`~music21.graph.PlotWindowedAardenEssen`, 
:class:`~music21.graph.PlotWindowedSimpleWeights`, :class:`~music21.graph.PlotWindowedBellmanBudge`,  :class:`~music21.graph.PlotWindowedTemperleyKostkaPayne`,
:class:`~music21.graph.PlotWindowedAmbitus`, :class:`~music21.graph.PlotDolan`

A basic example follows::

    >>> from music21 import *
    >>> haydn = converter.parse('haydn/symphony94/02') # doctest: +SKIP
    >>> plot = graph.PlotDolan(haydn) # doctest: +SKIP
    >>> plot.process() # doctest: +SKIP

.. image:: images/graphing-06.*
     :width: 600

:download:`See a larger version <images/graphing-bigDolan.png>`


The ActivityMatch Object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ActivityMatch object provides a way to examine, for a given parameter, 
what other parameters are active. 


Elementary Graphing Classes
-------------------------------

Music21 provides low-level access to basic graphing routines through 
classes for each graphing archetype.

Complete documentation for these graphing objects can be found with the 
following classes: :class:`~music21.graph.GraphHorizontalBar`, :class:`~music21.graph.GraphScatterWeighted`, 
:class:`~music21.graph.GraphScatter`, :class:`~music21.graph.GraphHistogram`, :class:`~music21.graph.Graph3DPolygonBars`.


Two-Dimensional Scatter Plot 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A two-dimensional scatter graph can be made from any list of *x*, *y* data pairs. 

The `doneAction` keyword argument determines what happens after 
the :meth:`~music21.graph.Graph.process` method is called. A 'show' value (the default) will 
immediately open the output format in platform- and backend-specific viewer. A `write` 
value will write the output in backend-specific format using a music21-generated temporary file. 

A basic example follows::

    >>> from music21 import *
    >>> a = graph.GraphScatter(title = 'Chromatic Scale', doneAction='show')
    >>> data = []
    >>> for midiNumber in range(36,120):
    ...     n = note.Note()
    ...     n.midi = midiNumber
    ...     frequency = n.pitch.frequency
    ...	    data.append( (midiNumber, int(frequency) ) )
    >>> a.setData(data)
    >>> a.process()  # doctest: +SKIP

.. image:: images/graphing-01.*
     :width: 700

Numerous parameters can be specified through keyword arguments when creating a scatter plot, and also attached to each point.

The 'alpha' keyword argument sets transparency, from 0 (transparent) to 1 (opaque).

The 'title' keyword argument sets the title of the graph.

The 'colors' keyword argument sets the colors of data points, specified as HTML 
color codes or matplotlib's single-letter abbreviations.

This example provides basic customization to a scatter graph::

    >>> from music21 import *
    >>> a = graph.GraphScatter(title = 'Color-coded chromatic scale showing C major', doneAction='show')
    >>> data = []
    >>> for midiNumber in range(36,120):
    ...	    n = note.Note()
    ...	    n.midi = midiNumber
    ...	    frequency = n.pitch.frequency
    ...	    if n.pitch.pitchClass in [0, 2, 4, 5, 7, 9, 11]:
    ...	        alpha = 1
    ...	        marker = 'o'
    ...	        color = 'white'
    ...	        markerSize = 10
    ...     else:
    ...	        alpha = 1
    ...	        marker = 'd'
    ...	        color = 'black'
    ...	        markerSize = 8
    ...	    data.append( (midiNumber, int(frequency), 
    ...                   {'color':color, 'alpha': alpha, 
    ...                     'marker': marker, 'markerSize':markerSize} ) )
    >>> a.setData(data)
    >>> a.setAxisLabel('x', 'midi number')
    >>> a.setAxisLabel('y', 'frequency')
    >>> a.process()  # doctest: +SKIP

.. image:: images/graphing-02.*
    :width: 700


Grouped Bar Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This graph allows you to plot multiple sets of data in parallel bar graphs. Data for this graph is provided
in a list of tuples of the form ``(dataLabel, {plotGroup: value, plotGroup2: value ... })``. The example below 
iterates through the Bach Chorale corpus using corpus.chorales.Iterator and stores the frequency at which
each part exhibits notes of each quarter length present. It displays the normalized frequency of each quarterLength
as four bars, each corresponding to an SATB part.

The example follows::

    >>> from music21 import *
    >>> sopranoDict, altoDict, tenorDict, bassDict, data, noteTotal = {}, {}, {}, {}, [], 0.0
    >>> for chorale in corpus.chorales.Iterator():
    ...     (soprano, alto, tenor, bass) = (chorale.getElementById('Soprano'), 
    ...                                     chorale.getElementById('Alto'), 
    ...                                     chorale.getElementById('Tenor'), 
    ...                                     chorale.getElementById('Bass'))
    ...     for (part, partDict) in [(soprano, sopranoDict), (alto, altoDict), (tenor, tenorDict), (bass, bassDict)]:
    ...         if part is not None:
    ...             part = part.flat.notes
    ...             for n in part:
    ...                 noteTotal += 1.0
    ...                 noteLength = n.duration.quarterLength
    ...                 if noteLength in partDict:
    ...                     partDict[noteLength] += 1
    ...                 else:
    ...                     partDict[noteLength] = 1
    >>> quarterLengths = list(set(list(sopranoDict.keys())
    ...                           + list(altoDict.keys())
    ...                           + list(tenorDict.keys())
    ...                           + list(bassDict.keys())))
    >>> for ql in quarterLengths:
    ...     values = []
    ...     for partDict in [sopranoDict, altoDict, tenorDict, bassDict]:     
    ...         if ql in partDict:
    ...             values.append(partDict[ql]/noteTotal)
    ...         else:
    ...             values.append(0.0)
    ...     data.append((ql, {'soprano': values[0], 'alto': values[1], 'tenor': values[2], 'bass': values[3]})) 
    >>> a = graph.GraphGroupedVerticalBar(title="Frequency of note durations in Bach's Chorales",
    ...                                   doneAction='show',
    ...                                   binWidth = 1,
    ...                                   colors = ['#605C7F', '#5c7f60', '#715c7f', '#3FEE32', '#01FFEE'],
    ...                                   roundDigits = 4)
    >>> a.setData(sorted(data, key = lambda datum: datum[0]))
    >>> a.setAxisLabel('x', 'Note duration in quarter lengths')
    >>> xtickValues = range(len(quarterLengths))
    >>> xtickLabels = sorted(quarterLengths)
    >>> a.axis['x']['ticks'] = (xtickValues, xtickLabels)
    >>> a.process() # doctest: +SKIP

.. image:: images/graphing-03.*
    :width: 600

:download:`See full-size graph <images/graphing-03.png>`

Three-Dimensional Bar Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A three dimensional graph made of numerous rows of bars can be used to graph 
three-dimensional data. Data for this graph is provided by a dictionary of 
key-value pairs, where values are equal-sized-lists of values. 

In addition to keyword arguments described for other graphs, this graph 
supports the following additional keyword arguments.

The `barWidth` keyword argument sets the width of bars.
The `useKeyValues` keyword argument determines whether or not the keys in the 
data dictionary are interpreted as numerical values or labels.
The `zeroFloor` keyword argument determines whether or not the vertical axis is sized to contain 0 or not.

A basic example follows::

    >>> import random
    >>> from music21 import graph
    >>> a = graph.Graph3DPolygonBars(doneAction='show') 
    >>> data = {1:[], 2:[], 3:[]}
    >>> for i in range(len(data.keys())):
    ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
    ...    data[list(data.keys())[i]] = q
    >>> a.setData(data) 
    >>> a.process()  # doctest: +SKIP

.. image:: images/graphing-04.*
    :width: 600


Here is an example from music. This graphs the 12 major scales next to each 
other in terms of frequency showing which notes are present
and which notes are not::

    >>> from music21 import *
    >>> data = {0:[], 1:[], 2:[], 3:[], 4:[], 5:[], 6:[], 7:[], 8:[], 9:[], 10:[], 11:[]}
    >>> majorScale = [0, 2, 4, 5, 7, 9, 11]
    >>> for pitchClass in range(12):
    ...     n = note.Note()
    ...     n.pitch.pitchClass = pitchClass
    ...     frequency = n.pitch.frequency
    ...     for scale in data.keys():
    ...         if (pitchClass - scale) % 12 in majorScale:
    ...             data[scale].append((pitchClass, frequency))
    >>> a = graph.Graph3DPolygonBars(title='The Twelve Major Scales',
    ...                             alpha=.8,
    ...                             barWidth=.2,
    ...                             doneAction='show',
    ...                             useKeyValues = True,
    ...                             zeroFloor = True,
    ...                             colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']) 
    >>> a.setData(data)
    >>> a.axis['x']['ticks'] = (range(12), ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b'])
    >>> a.axis['y']['ticks'] = (range(12), ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b'])
    >>> a.setAxisLabel('y', 'Root Notes')
    >>> a.setAxisLabel('x', 'Scale Degrees')
    >>> a.setAxisLabel('z', 'Frequency in Hz')
    >>> a.process()   # doctest: +SKIP

.. image:: images/graphing-05.*
    :width: 600

:download:`See full-size graph <images/graphing-05.jpg>`
