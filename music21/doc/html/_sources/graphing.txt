.. _graphing:



Graphing Utilities
======================================

Music21 can provide data graphs and plots of multiple musical attributes using high-level analysis tools.

Users can create their own custom graphing routines by extending or reworking existing Music21 models. 



Installing and Using matplotlib
-------------------------------

The powerful and flexible graphing routines of music21 are provided by the matplotlib and numpy libraries. They 
can be downloaded from the following URLs:

http://numpy.scipy.org
http://sourceforge.net/projects/matplotlib/files/

For instructions on getting them installed and running see the following URL:

http://matplotlib.sourceforge.net/users/installing.html

For more information about matplotlib with music21 see :ref:`advancedGraphing`.

Primitive Graphing Formats
-------------------------------

Music21 provides low-level access to basic graphing routines. 




Two-Dimensional Scatter Plot 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A two-dimensional scatter graph can be made from any list of *x*, *y* data pairs. 

The doneAction keyword argument determines what happens after the process() method is called. A 'show' value will immediately open the output format in platform- and backend-specific viewer. A 'write' value will write the output in backend-specific format using a music21-generated temporary file. 

A basic example follows::

    >>> from music21.analysis import graph
    >>> a = graph.Graph2DScatter(doneAction='show')
    >>> data = [(x, x*x) for x in range(50)]
    >>> a.setData(data)
    >>> a.process()

.. image:: images/graphingScatter-basic.*
    :width: 500

Numerous parameters can be specified through keyword arguments when creating a scatter plot. 

The 'alpha' keyword argument sets transparency, from 0 (transparent) to 1 (opaque).

The 'title' keyword argument sets the title of the graph.

The 'colors' keyword argument sets the colors of data points, specified as HTML color codes or matplotlib's single-letter abbreviations.

This example provides basic customization to a scatter graph::

    >>> from music21.analysis import graph
    >>> a = graph.Graph2DScatter(title='Exponential Graph', alpha=1, doneAction='show')
    >>> data = [(x, x*x) for x in range(50)]
    >>> a.setData(data)
    >>> a.process()

.. image:: images/graphingScatter-args.*
    :width: 500



Two-Dimensional Histogram
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A histogram provides a bar graph for measuring the count of single items. Data for this graph is provided as a list of *x*, *y* data pairs; however, unlike with a scatter plot, there can be only one definition for each *x* value. 

A basic example follows::

    >>> import random
    >>> from music21.analysis import graph
    >>> a = graph.Graph2DHistogram(doneAction='show')
    >>> data = [(x, random.choice(range(30))) for x in range(50)]
    >>> a.setData(data)
    >>> a.process()




Three-Dimensional Bar Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


A three dimensional graph made of numerous rows of bars can be used to plot three-dimensional data. Data for this graph is provided by a dictionary of key-value pairs, where values are equal-sized-lists of values. 

In addition to keyword arguments described for other graphs, this graph supports the following additional keyword arguments.

The 'barWidth' keyword argument sets the width of bars.

A basic example follows::

    >>> import random
    >>> from music21.analysis import graph
    >>> a = graph.Graph3DPolygonBars(doneAction='show') 
    >>> data = {1:[], 2:[], 3:[]}
    >>> for i in range(len(data.keys())):
    ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
    ...    data[data.keys()[i]] = q
    >>> a.setData(data) 
    >>> a.process()

.. image:: images/graphing3dbar-basic.*
    :width: 500

The following examples demonstrates basic customization with keyword arguments using the same data obtained above::


    >>> b = graph.Graph3DPolygonBars(title='Random Data', alpha=.8,\
        barWidth=.2, doneAction='show', colors=['b','r','g']) 
    >>> b.setData(data)
    >>> b.process()

.. image:: images/graphing3dbar-args.*
    :width: 500
















High Level Graphing Objects
-------------------------------

Music21 features high level graphing objects for common musical operations and analysis routines. 



The ActivityMatch Object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ActivityMatch object provides a way to examine, for a given parameter, what other parameters are active. 




The NoteAnalysis Object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The NoteAnalysis object permits graphing and correlating two parameters of a Note objects in a Stream.

The NoteAnalysis object provides graphing routines using the Graph2DHistogram object.

The following example demonstrates the default settings of the noteAttributeCount(), which correlate MIDI Note Number and Quarter Length of notes in a stream::

    >>> from music21 import corpus, converter
    >>> from music21.analysis import correlate
    >>> a = converter.parse(corpus.getWork('luca/gloria'))
    >>> b = correlate.NoteAnalysis(a.flat)
    >>> b.noteAttributeCount(colors=['#aa46ff'], barWidth=.1, alpha=.7)

.. image:: images/graphingNoteAnalysis-default.*
    :width: 500
