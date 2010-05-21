.. _graphing:



Graphing Utilities
======================================

Music21 can provide data graphs and plots of multiple musical attributes using high-level analysis tools.

Users can create their own custom graphing routines by extending or reworking existing music21 :class:`~music21.graph.Graph` and :class:`~music21.graph.PlotStream` classes. 

Alternatively, music21 provides numerous pre-built plot classes to provide quick access to numerous graphical views.







Installing and Using matplotlib
-------------------------------

The powerful and flexible graphing routines of music21 are provided by the matplotlib and numpy libraries. They can be downloaded from the following URLs:

http://numpy.scipy.org
http://sourceforge.net/projects/matplotlib/files/

For instructions on getting them installed and running see the following URL:

http://matplotlib.sourceforge.net/users/installing.html

For more information about matplotlib with music21 see :ref:`advancedGraphing`.







Graphing Streams
-------------------------------------------------------

Music21 features numerous ways to display the data within a Stream. 

Complete documentation for these graphing objects can be found with the following classes: :class:`~music21.graph.PlotHistogramPitchSpace`, :class:`~music21.graph.PlotHistogramPitchClass`, :class:`~music21.graph.PlotHistogramQuarterLength`, :class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`, :class:`~music21.graph.PlotScatterPitchClassOffset`,  :class:`~music21.graph.PlotHorizontalBarPitchClassOffset`,
:class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`, :class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`, :class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`, :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`, :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`, 


The plotStream() Utility Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The graph.py module offers the :func:`~music21.graph.plotStream` function for easy access to graphing music21 Streams. This function requires a Stream as an argument and a number of additional arguments to specify the output of one or more plot types. 

Calling :func:`~music21.graph.plotStream` with no arguments creates a default graph, using :class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`, of a flat version of the Stream:

    >>> from music21 import corpus, graph
    >>> aStream = corpus.parseWork('bach/bwv57.8')
    >>> graph.plotStream(aStream)


    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600


Calling :func:`~music21.graph.plotStream` with a Stream and the name of plot class will use that class to create a and display a graph. 


    >>> graph.plotStream(aStream, 'PlotHistogramPitchClass')

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600

Alternatively, the type of desired graph can be given as the `format` keyword argument, and list of values desired can be given with the `values` keyword argument. If one or more plots are available that match the requested values, these will be displayed


    >>> graph.plotStream(aStream, format='scatterweighted')

    .. image:: images/PlotScatterWeightedPitchSpaceQuarterLength.*
        :width: 600

    >>> graph.plotStream(aStream, format='scatter', values=['pitch'])

    .. image:: images/PlotScatterPitchSpaceQuarterLength.*
        :width: 600

Note that the exact same functionality of :func:`~music21.graph.plotStream` is available as the Stream :meth:`~music21.stream.Stream.plot` method.


    >>> aStream.plot(format='scatterweighted', values='pitchclass')

    .. image:: images/PlotScatterWeightedPitchClassQuarterLength.*
        :width: 600



Creating and Calling Plot Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graphs can be created and/or written to a file by creating an instance of a plot class with the Stream as an argument. Once created, the object's :meth:`~music21.graph.Graph.process` method is called to obtain a result. The result is determined by the `doneAction` keyword argument.

    >>> from music21 import corpus, graph
    >>> aStream = corpus.parseWork('bach/bwv57.8')
    >>> aPlot = graph.PlotHistogramPitchClass(aStream)
    >>> aPlot.process()

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600


The default Action` is to call :meth:`~music21.graph.Graph.show` method the graph, which will write it as a temporary file and open the graph. To write a graph to a file, the :meth:`~music21.graph.Graph.write`, given a file path, can be used.








Analytical Graphing Objects
-------------------------------------------------------

Music21 features graphing objects that display the results of analysis


The ActivityMatch Object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ActivityMatch object provides a way to examine, for a given parameter, what other parameters are active. 















Elementary Graphing Classes
-------------------------------

Music21 provides low-level access to basic graphing routines through classes for each graphing archetype

Complete documentation for these graphing objects can be found with the following classes: :class:`~music21.graph.GraphHorizontalBar`, :class:`~music21.graph.GraphScatterWeighted`, :class:`~music21.graph.GraphScatter`, :class:`~music21.graph.GraphHistogram`, :class:`~music21.graph.Graph3DPolygonBars`.


Two-Dimensional Scatter Plot 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A two-dimensional scatter graph can be made from any list of *x*, *y* data pairs. 

The `doneAction` keyword argument determines what happens after the :meth:`~music21.graph.Graph.process` method is called. A 'show' value (the default) will immediately open the output format in platform- and backend-specific viewer. A 'write' value will write the output in backend-specific format using a music21-generated temporary file. 

A basic example follows::

    >>> from music21 import graph
    >>> a = graph.GraphScatter(doneAction='show')
    >>> data = [(x, x*x) for x in range(50)]
    >>> a.setData(data)
    >>> a.process()

.. image:: images/graphing-01.*
    :width: 600

Numerous parameters can be specified through keyword arguments when creating a scatter plot. 

The 'alpha' keyword argument sets transparency, from 0 (transparent) to 1 (opaque).

The 'title' keyword argument sets the title of the graph.

The 'colors' keyword argument sets the colors of data points, specified as HTML color codes or matplotlib's single-letter abbreviations.

This example provides basic customization to a scatter graph::

    >>> from music21 import graph
    >>> a = graph.GraphScatter(title='Exponential Graph', alpha=1, doneAction='show')
    >>> data = [(x, x*x) for x in range(50)]
    >>> a.setData(data)
    >>> a.process()

.. image:: images/graphing-02.*
    :width: 600



Two-Dimensional Histogram
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A histogram provides a bar graph for measuring the count of single items. Data for this graph is provided as a list of *x*, *y* data pairs; however, unlike with a scatter plot, there can be only one definition for each *x* value. 

A basic example follows::

    >>> import random
    >>> from music21 import graph
    >>> a = graph.GraphHistogram(doneAction='show')
    >>> data = [(x, random.choice(range(30))) for x in range(50)]
    >>> a.setData(data)
    >>> a.process()

.. image:: images/graphing-03.*
    :width: 600



Three-Dimensional Bar Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A three dimensional graph made of numerous rows of bars can be used to plot three-dimensional data. Data for this graph is provided by a dictionary of key-value pairs, where values are equal-sized-lists of values. 

In addition to keyword arguments described for other graphs, this graph supports the following additional keyword arguments.

The `barWidth` keyword argument sets the width of bars.

A basic example follows::

    >>> import random
    >>> from music21 import graph
    >>> a = graph.Graph3DPolygonBars(doneAction='show') 
    >>> data = {1:[], 2:[], 3:[]}
    >>> for i in range(len(data.keys())):
    ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
    ...    data[data.keys()[i]] = q
    >>> a.setData(data) 
    >>> a.process()

.. image:: images/graphing-04.*
    :width: 600


The following example demonstrates basic customization with keyword arguments using the same data obtained above::

    >>> b = graph.Graph3DPolygonBars(title='Random Data', alpha=.8,\
        barWidth=.2, doneAction='show', colors=['b','r','g']) 
    >>> b.setData(data)
    >>> b.process()

.. image:: images/graphing-05.*
    :width: 600








