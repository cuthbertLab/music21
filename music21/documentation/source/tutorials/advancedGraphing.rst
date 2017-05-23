.. _advancedGraphing:



Advanced Graphing Topics
========================

The music21 tools for graphing and visualizing data are meant to be simple and intuitive to use. 
However, you may occasionally need some of the more advanced configuration topics described below.

Some of the work here is out of date -- so be careful with it!


Customizing Data Points
------------------------

Numerous parameters can be specified through keyword arguments when creating a scatter plot, and also attached to each point.

The 'alpha' keyword argument sets transparency, from 0 (transparent) to 1 (opaque).

The 'title' keyword argument sets the title of the graph.

The 'colors' keyword argument sets the colors of data points, specified as HTML 
color codes or matplotlib's single-letter abbreviations.

This example provides basic customization to a scatter graph::

    >>> from music21 import *
    >>> a = graph.primitives.GraphScatter(title = 'Color-coded chromatic scale showing C major', doneAction='show')
    >>> data = []
    >>> for midiNumber in range(36,120):
    ...	    n = note.Note()
    ...	    n.pitch.midi = midiNumber
    ...	    frequency = n.pitch.frequency
    ...	    if n.pitch.pitchClass in [0, 2, 4, 5, 7, 9, 11]:
    ...	        alpha = 1
    ...	        marker = 'o'
    ...	        color = 'white'
    ...	        markersize = 10
    ...     else:
    ...	        alpha = 1
    ...	        marker = 'd'
    ...	        color = 'black'
    ...	        markersize = 8
    ...	    data.append( (midiNumber, int(frequency), 
    ...                   {'color':color, 'alpha': alpha, 
    ...                     'marker': marker, 'markersize':markersize} ) )
    >>> a.data = data
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
    >>> a = graph.primitives.GraphGroupedVerticalBar(title="Frequency of note durations in Bach's Chorales",
    ...                                   doneAction='show',
    ...                                   binWidth = 1,
    ...                                   colors = ['#605C7F', '#5c7f60', '#715c7f', '#3FEE32', '#01FFEE'],
    ...                                   roundDigits = 4)
    >>> a.data = sorted(data, key=lambda datum: datum[0])
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
    >>> a = graph.primitives.Graph3DBars(doneAction='show') 
    >>> data = {1:[], 2:[], 3:[]}
    >>> for i in range(len(data.keys())):
    ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
    ...    data[list(data.keys())[i]] = q
    >>> a.data = data
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
    >>> a = graph.primitives.Graph3DBars(title='The Twelve Major Scales',
    ...                             alpha=.8,
    ...                             barWidth=.2,
    ...                             doneAction='show',
    ...                             useKeyValues = True,
    ...                             zeroFloor = True,
    ...                             colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']) 
    >>> a.data = data
    >>> a.axis['x']['ticks'] = (range(12), ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b'])
    >>> a.axis['y']['ticks'] = (range(12), ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b'])
    >>> a.setAxisLabel('y', 'Root Notes')
    >>> a.setAxisLabel('x', 'Scale Degrees')
    >>> a.setAxisLabel('z', 'Frequency in Hz')
    >>> a.process()   # doctest: +SKIP

.. image:: images/graphing-05.*
    :width: 600

:download:`See full-size graph <images/graphing-05.jpg>`



Selecting the matplotlib Backend
------------------------------------------------

Most people will graph music21 data using matplotlib's default system for rendering and displaying
images (called the backend).  That default system is the TkAgg backend.  
But for embedding music21 in other graphical user interfaces you may want to choose another backend.
See the following discussion for more information.

  http://matplotlib.sourceforge.net/faq/installing_faq.html#what-is-a-backend
