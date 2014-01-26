.. _overviewMeters:


Overview: Meters, Time Signatures, and Processing Beams, Accents, and Beats
===========================================================================

Meters and time signatures are represented in music21 as groups of nested hierarchical structures. In many cases, the default configuration of a music21 :class:`~music21.meter.TimeSignature` object will do what you want. However, by configuring the fundamental component objects, the :class:`~music21.meter.MeterTerminal` and :class:`~music21.meter.MeterSequence` objects, a wide range of options are available.

The :class:`~music21.meter.TimeSignature` object additionally features numerous high-level methods to provide access to and configuration of display, beaming, beat, and accent information.

This overview will illustrate key features of music21's meter objects. For complete documentation of these objects, see :ref:`moduleMeter`. 

For a more formal discussion of these designs, see the paper "Modeling Beats, Accents, Beams, and Time Signatures Hierarchically with music21 Meter Objects" (Ariza and Cuthbert 2010), at the following URL: http://mit.edu/music21/papers/2010MeterObjects.pdf





Basic Time Signature 
-------------------------------------------------------

While the full structure and configuration options of TimeSignature objects will be discussed below, a few quick demonstrations will get you up and running quickly with the many common tasks.


Getting Time Signatures From Parts and Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In general, :class:`~music21.meter.TimeSignature` objects are found within :class:`~music21.stream.Measure` objects (a Stream subclass). However, in some cases :class:`~music21.meter.TimeSignature` objects can exist directly on a Stream. 

TimeSignature objects, as a subclass of the :class:`~music21.base.Music21Object`, have an offset and can be positioned anywhere on a Stream. When placed in a Measure, TimeSignature objects are often placed at the start, or zero offset position. The Measure property :attr:`~music21.stream.Measure.timeSignature` can be used to set or get a TimeSignature at the zero offset position. If a Measure does not have a TimeSignature, the :attr:`~music21.stream.Measure.timeSignature` property returns None.

In the following example, a score is parsed from the :ref:`moduleCorpus` module :func:`~music21.corpus.parse` function. The alto :class:`~music21.stream.Part` Stream is accessed by its identification string, 'Alto,' using the :meth:`~music21.stream.Stream.getElementById` method. We can produce notation output of this Part by calling the :meth:`~music21.base.Music21Object.show` method.

.. bwv57.8.xml 3/4
.. bwv127.5.xml : good eight note runs

>>> from music21 import *
>>> sSrc = corpus.parse('bach/bwv57.8.xml')
>>> sPart = sSrc.getElementById('Alto')
>>> sPart.show()  # doctest: +SKIP


.. image:: images/overviewMeters-09.*
    :width: 600


To examine the :class:`~music21.meter.TimeSignature` object active for this part, there are a few approaches. One method is to simply search for the class within all objects in the Part, or the flattened Part Stream representation. Remember that a Part is generally built of Measures, or Stream-embedded containers. To get all the elements in the Stream we can use the :attr:`~music21.stream.Stream.flat` property, and then search for a class with the :meth:`~music21.stream.Stream.getElementsByClass` method. This returns a new Stream containing all found classes. The first element in this Stream is the TimeSignature. 

>>> sPart.flat.getElementsByClass(meter.TimeSignature)[0]
<music21.meter.TimeSignature 3/4>

Alternatively, we can look at the first Measure in the Stream, and examine the :attr:`~music21.stream.Measure.timeSignature` property. Notice that the second Measure does not have a TimeSignature. 

>>> sPart.getElementsByClass('Measure')[0].timeSignature
<music21.meter.TimeSignature 3/4>
>>> sPart.getElementsByClass('Measure')[1].timeSignature == None
True



Setting a Time Signature in a Measure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can create a new TimeSignature object by providing a string representation of the meter. In most cases, intuitive string-based time signature representations will give you the expected results. Assigning a new TimeSignature object, however, simple associated it with a Measure: it will not automatically rebar or reposition notes within bars. For example, the same part examined above can be modified. Here, the first Measure's :attr:`~music21.stream.Measure.timeSignature` property is set to a new object. Note that, when viewing the Part, the time signature is changed even though the position of the notes in Measures is not changed.

>>> sPart.getElementsByClass('Measure')[0].timeSignature = meter.TimeSignature('5/4')
>>> sPart.show()   # doctest: +SKIP


.. image:: images/overviewMeters-10.*
    :width: 600




Rebaring with Changing Time Signatures 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To actually change the position of the notes, creating new Measures with new TimeSignatures, we need to rebar the music. The simplest way to do this is to get all the notes from a Part using the :attr:`~music21.stream.Stream.notesAndRests` property on a flat Stream representation. Then, by inserting a new TimeSignature at the start of this Stream using the :meth:`~music21.stream.Stream.insert` method, we can generate new notation with the show() method. Note that here we are not creating Measures directly; instead, we are assigning TimeSignature objects into a Stream of notes. When the show() method is called, Measures are created within a temporary Stream according to the relevant TimeSignature objects.

>>> sNew = sPart.flat.notesAndRests
>>> sNew.insert(0, meter.TimeSignature('2/4'))
>>> sNew.show()   # doctest: +SKIP

.. image:: images/overviewMeters-11.*
    :width: 600

The :attr:`~music21.stream.Stream.notesAndRests` property, while useful, only gathers Notes, Rests, or other subclasses of :class:`~music21.note.GeneralNote`. Notice that, in the above example, the :class:`~music21.key.KeySignature` and :class:`~music21.instrument.Insturment` objects, as apparent in the notation, have been removed.  

If we want to get all elements in the Stream except those that are a specific class, the :meth:`~music21.stream.Stream.getElementsNotOfClass` method can be used. In the example below, we gather all elements that are not TimeSignature objects, and then assign a new TimeSignature to the new Stream.

>>> sNew = sPart.flat.getElementsNotOfClass(meter.TimeSignature)
>>> sNew.insert(0, meter.TimeSignature('2/4'))
>>> sNew.show()    # doctest: +SKIP

.. image:: images/overviewMeters-16.*
    :width: 600

We can continue to add multiple TimeSignature objects to this Stream of Notes. First, we will replace the 2/4 bar previously added with a new TimeSignature, using the Stream :meth:`~music21.stream.Stream.replace` method. Then, we will insert a number of additional TimeSignature objects at offsets further into the Stream. Again, as this Stream has no Measures, temporary Measures are automatically created when calling the show() method.

>>> ts = sNew.getTimeSignatures()[0]
>>> ts
<music21.meter.TimeSignature 2/4>
>>> sNew.replace(ts, meter.TimeSignature('5/8'))
>>> sNew.insert(10, meter.TimeSignature('7/8'))
>>> sNew.insert(17, meter.TimeSignature('9/8'))
>>> sNew.insert(26, meter.TimeSignature('3/8'))
>>> sNew.show()   # doctest: +SKIP

.. image:: images/overviewMeters-12.*
    :width: 600

If we wanted to apply this sequence of TimeSignature objects to a complete score, we can extract all the TimeSignature objects from our new Stream with the :meth:`~music21.stream.Stream.getTimeSignatures` method.

>>> tsStream = sNew.getTimeSignatures()
>>> tsStream.show('t')
{0.0} <music21.meter.TimeSignature 5/8>
{10.0} <music21.meter.TimeSignature 7/8>
{17.0} <music21.meter.TimeSignature 9/8>
{26.0} <music21.meter.TimeSignature 3/8>

We can then iterate through the Part objects in the source Stream, get a flat representation of notes, and use the :meth:`~music21.stream.Stream.makeMeasures` method to create new Parts. The :meth:`~music21.stream.Stream.makeMeasures` method can take an optional Stream of TimeSignature objects that are used to configure the making of Measures. 

After Measure creation, Notes need to be split and extend with ties. the Stream :meth:`~music21.stream.Stream.makeTies` method can be used. These new Parts can be added to a new Stream and displayed. 

>>> sRebar = stream.Stream()
>>> for part in sSrc.getElementsByClass('Part'):
...     newPart = part.flat.getElementsNotOfClass('TimeSignature')
...     newPart = newPart.makeMeasures(tsStream)
...     newPart.makeTies(inPlace=True)
...     sRebar.insert(0, newPart)
... 
>>> sRebar.show()   # doctest: +SKIP

.. image:: images/overviewMeters-13.*
    :width: 600


Finding the Beat of a Note in a Measure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a Note is in a Measure, and that Measure or a preceding Measure has a TimeSignature, it is possible to find the beat, or the position of the Note in terms of the count of whole or fractional subdivisions of top-level beat partitions.

The Note :attr:`~music21.note.GeneralNote.beat` property will return, if available, a numerical representation of the beat, with a floating point value corresponding to the proportional position through the beat. The Note :attr:`~music21.note.GeneralNote.beatStr` property returns a string representation, replacing floating point values with fractions when available. 

>>> sSrc = corpus.parse('bach/bwv57.8.xml')
>>> sPart = sSrc.getElementById('Soprano')
>>> sPart.flat.notesAndRests[0]
<music21.note.Note B->
>>> sPart.flat.notesAndRests[4].beat
2.5
>>> sPart.flat.notesAndRests[4].beatStr
'2 1/2'

We can annotate each Note in the Part with the string returned by :attr:`~music21.note.GeneralNote.beatStr` using the Note :attr:`~music21.note.GeneralNote.addLyric` method. 

>>> for n in sPart.flat.notesAndRests:
...     n.addLyric(n.beatStr)
... 
>>> sPart.show()    # doctest: +SKIP

.. image:: images/overviewMeters-14.*
    :width: 600

If we change the TimeSignature in a Part, the beat counts will reflect this change. For example, if the Bass part of the same chorale is re-barred in 6/8, new, syncopated beat counts will be given.

>>> sPart = sSrc.getElementById('Alto')
>>> sPart = sPart.flat.getElementsNotOfClass(meter.TimeSignature)
>>> sMeasures = sPart.makeMeasures(meter.TimeSignature('6/8'))
>>> sMeasures.makeTies(inPlace=True)
>>> for n in sMeasures.flat.notesAndRests:
...     n.addLyric(n.beatStr)
... 
>>> sMeasures.show()   # doctest: +SKIP

.. image:: images/overviewMeters-15.*
    :width: 600


Objects for Organizing Hierarchical Partitions
-----------------------------------------------

Hierarchical metrical structures can be described as a type of fractional, space-preserving tree structure. With such a structure we partition and divide a single duration into one or more parts, where each part is a fraction of the whole. Each part can, in turn, be similarly divided. The objects for configuring this structure are the MeterTerminal and the MeterSequence objects.

MeterTerminal and the MeterSequence objects are for advanced configuration. For basic data access about common meters, see the discussion of TimeSignature, below. 


Creating and Editing MeterTerminal Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A MeterTerminal is a node of the metrical tree structure, defined as a duration expressed as a fraction of a whole note. Thus, 1/4 is 1 quarter length (QL) duration; 3/8 is 1.5 QL; 3/16 is 0.75 QL. For this model, denominators are limited to *n* = 2 :superscript:`x`, for *x* between 1 and 7 (e.g. 1/1 to 1/128).

MeterTerminals can additionally store a weight, or a numerical value that can be interpreted in a variety of different ways.

The following examples in the Python interpreter demonstrate creating a MeterTerminal and accessing the :attr:`~music21.meter.MeterTerminal.numerator` and :attr:`~music21.meter.MeterTerminal.denominator` attributes. The  :attr:`~music21.meter.MeterTerminal.duration` attribute stores a :class:`~music21.duration.Duration` object.

>>> from music21 import meter
>>> mt = meter.MeterTerminal('3/4')
>>> mt
<MeterTerminal 3/4>
>>> mt.numerator, mt.denominator
(3, 4)
>>> mt.duration.quarterLength
3.0

A MeterTerminal can be broken into an ordered sequence of MeterTerminal objects that sum to the same duration. This new object, to be discussed below, is the MeterSequence. A MeterTerminal can be broken into these duration-preserving components with the :meth:`~music21.meter.MeterTerminal.subdivide` method. An argument for subdivision can be given as a desired number of equal-valued components, a list of numerators assuming equal-denominators, or a list of string fraction representations. 

>>> mt.subdivide(3)
<MeterSequence {1/4+1/4+1/4}>
>>> mt.subdivide([3,3]) 
<MeterSequence {3/8+3/8}>
>>> mt.subdivide(['1/4','4/8'])  
<MeterSequence {1/4+4/8}>



Creating and Editing MeterSequence Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A MeterSequence object is a sub-class of a MeterTerminal. Like a MeterTerminal, a MeterSequence has a :attr:`~music21.meter.MeterSequence.numerator`, a :attr:`~music21.meter.MeterSequence.denominator`, and a :attr:`~music21.meter.MeterSequence.duration` attribute. A MeterSequence, however, can be a hierarchical tree or sub-tree, containing an ordered sequence of MeterTerminal and/or MeterSequence objects.

The ordered collection of MeterTerminal and/or MeterSequence objects can be accessed like Python lists. MeterSequence objects, like MeterTerminal objects, store a weight that by default is the sum of constituent weights. 

The :meth:`~music21.meter.MeterSequence.partition` and :meth:`~music21.meter.MeterTerminal.subdivide` methods can be used to configure the nested hierarchical structure. 

The :meth:`~music21.meter.MeterSequence.partition` method replaces existing MeterTerminal or MeterSequence objects in place with a new arrangement, specified as a desired number of equal-valued components, a list of numerators assuming equal-denominators, or a list of string fraction representations. 

The :meth:`~music21.meter.MeterTerminal.subdivide` method returns a new MeterSequence (leaving the source MeterSequence unchanged) with an arrangement of MeterTerminals as specified by an argument in the same form as for the :meth:`~music21.meter.MeterSequence.partition` method.

Note that MeterTerminal objects cannot be partitioned in place. A common way to convert a MeterTerminal into a MeterSequence is to reassign the returned MeterSequence from the :meth:`~music21.meter.MeterTerminal.subdivide` method to the position occupied by the MeterTerminal.

The following example creates and partitions a MeterSequence by re-assigning subdivisions to MeterTerminal objects. The use of Python list-like index access is also demonstrated. 


>>> ms = meter.MeterSequence('3/4')
>>> ms
<MeterSequence {3/4}>
>>> ms.partition([3,3]) 
>>> ms
<MeterSequence {3/8+3/8}>
>>> ms[0] 
<MeterTerminal 3/8>
>>> ms[0] = ms[0].subdivide([3,3]) 
>>> ms[0]
<MeterSequence {3/16+3/16}>
>>> ms
<MeterSequence {{3/16+3/16}+3/8}>
>>> ms[1] = ms[1].subdivide([1,1,1]) 
>>> ms[1][0]
<MeterTerminal 1/8>
>>> ms[1]
<MeterSequence {1/8+1/8+1/8}>
>>> ms
<MeterSequence {{3/16+3/16}+{1/8+1/8+1/8}}>


The resulting structure can be graphically displayed with the following diagram:


.. image:: images/overviewMeters-02.*
    :width: 300


Numerous MeterSequence attributes provide convenient ways to access information about, or new objects from, the nested tree structure. The :attr:`~music21.meter.MeterSequence.depth` attribute returns the depth count at any node within the tree structure; the :attr:`~music21.meter.MeterSequence.flat` property returns a new, flat MeterSequence constructed from all the lowest-level MeterTerminal objects (all leaf nodes). 


>>> ms.depth
2
>>> ms[0].depth
1
>>> ms.flat
<MeterSequence {3/16+3/16+1/8+1/8+1/8}>


Numerous methods provide ways to access levels (slices) of the hierarchical structure, or all nodes found at a desired hierarchical level. As all components preserve the duration of their container, all levels have the same total duration. The :meth:`~music21.meter.MeterSequence.getLevel` method returns, for a given depth, a new, flat MeterSequence. The :meth:`~music21.meter.MeterSequence.getLevelSpan` method returns, for a given depth, the time span of each node as a list of start and end values. 


>>> ms.getLevel(0)
<MeterSequence {3/8+3/8}>
>>> ms.getLevel(1)
<MeterSequence {3/16+3/16+1/8+1/8+1/8}>
>>> ms.getLevelSpan(1)
[(0.0, 0.75), (0.75, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0)]
>>> ms[1].getLevelSpan(1)
[(0.0, 0.5), (0.5, 1.0), (1.0, 1.5)]


Finally, numerous methods provide ways to find and access the 
relevant nodes (the MeterTerminal or MeterSequence objects) active 
given a quarter length position into the tree structure. 
The :meth:`~music21.meter.MeterSequence.offsetToIndex` method returns, 
for a given QL, the index of the active node. 
The :meth:`~music21.meter.MeterSequence.offsetToSpan` method returns, 
for a given QL, the span of the active node. 
The :meth:`~music21.meter.MeterSequence.offsetToDepth` method returns, 
for a given QL, the maximum depth at this position. 


>>> ms.offsetToIndex(2.5)
1
>>> ms.offsetToSpan(2.5)
(1.5, 3.0)
>>> ms.offsetToDepth(.5)
2
>>> ms[0].offsetToDepth(.5)
1
>>> ms.getLevel(1).offsetToSpan(.5)
(0, 0.75)






Advanced Time Signature Configuration
---------------------------------------------

The music21 :class:`~music21.meter.TimeSignature` object contains four parallel MeterSequence objects, each assigned to the attributes :attr:`~music21.meter.TimeSignature.displaySequence`, :attr:`~music21.meter.TimeSignature.beatSequence`, :attr:`~music21.meter.TimeSignature.beamSequence`, :attr:`~music21.meter.TimeSignature.accentSequence`. The following displays a graphical realization of these four MeterSequence objects. 


.. image:: images/overviewMeters-01.*
    :width: 400

The TimeSignature provides a model of all common hierarchical structures contained within a bar. Common meters are initialized with expected defaults; however, full MeterSequence customization is available.






Configuring Display
-------------------------------------

The TimeSignature :attr:`~music21.meter.TimeSignature.displaySequence` MeterSequence employs the highest-level partitions to configure the displayed time signature symbol. If more than one partition is given, those partitions will be interpreted as additive meter components. If partitions have a common denominator, a summed numerator (over a single denominator) can be displayed by setting the TimeSignature :attr:`~music21.meter.TimeSignature.summedNumerator` attribute to True. Lower-level subdivisions of the TimeSignature MeterSequence are not employed.

Note that a new MeterSequence instance can be assigned to the :attr:`~music21.meter.TimeSignature.displaySequence` attribute with a duration and/or partitioning completely independent from the :attr:`~music21.meter.TimeSignature.beatSequence`, :attr:`~music21.meter.TimeSignature.beamSequence`, and :attr:`~music21.meter.TimeSignature.accentSequence` MeterSequences.

The following example demonstrates setting the display MeterSequence for a TimeSignature.


>>> ts1 = meter.TimeSignature('5/8') # assumes two partitions
>>> ts1.displaySequence.partition(['3/16','1/8','5/16'])
>>> ts2 = meter.TimeSignature('5/8') # assumes two partitions
>>> ts2.displaySequence.partition(['2/8', '3/8'])
>>> ts2.summedNumerator = True
>>> s = stream.Stream()
>>> for ts in [ts1, ts2]:
...     m = stream.Measure()
...     m.timeSignature = ts
...     n = note.Note('b')
...     n.quarterLength = 0.5
...     m.repeatAppend(n, 5)
...     s.append(m)
...
>>> s.show()   # doctest: +SKIP


.. image:: images/overviewMeters-08.*
    :width: 400




Configuring Beam
-------------------------------------

The TimeSignature :attr:`~music21.meter.TimeSignature.beamSequence` MeterSequence employs the complete hierarchical structure to configure the single or multi-level beaming of a bar. The outer-most partitions can specify one or more top-level partitions. Lower-level partitions subdivide beam-groups, providing the appropriate beam-breaks when sufficiently small durations are employed. 

The :attr:`~music21.meter.TimeSignature.beamSequence` MeterSequence is generally used to create and configure :class:`~music21.note.Beams` objects stored in :class:`~music21.note.Note` objects. The TimeSignature :meth:`~music21.meter.TimeSignature.getBeams` method, given a list of :class:`~music21.duration.Duration` objects, returns a list of :class:`~music21.note.Beams` objects based on the TimeSignature  :attr:`~music21.meter.TimeSignature.beamSequence` MeterSequence.

Many users may find the Stream :meth:`~music21.stream.Stream.makeBeams` method the most convenient way to apply beams to a Measure or Stream of Note objects. This method returns a new Stream with created and configured Beams. 

The following example beams a bar of 3/4 in four different ways. The diversity and complexity of beaming is offered here to illustrate the flexibility of this model.


>>> ts1 = meter.TimeSignature('3/4') 
>>> ts1.beamSequence.partition(1)
>>> ts1.beamSequence[0] = ts1.beamSequence[0].subdivide(['3/8', '5/32', '4/32', '3/32'])
>>> ts2 = meter.TimeSignature('3/4') 
>>> ts2.beamSequence.partition(3)
>>> ts3 = meter.TimeSignature('3/4') 
>>> ts3.beamSequence.partition(3)
>>>
>>> for i in range(len(ts3.beamSequence)):
...     ts3.beamSequence[i] = ts3.beamSequence[i].subdivide(2)
... 
>>> ts4 = meter.TimeSignature('3/4') 
>>> ts4.beamSequence.partition(['3/8', '3/8'])
>>> for i in range(len(ts4.beamSequence)):
...     ts4.beamSequence[i] = ts4.beamSequence[i].subdivide(['6/32', '6/32'])
...     for j in range(len(ts4.beamSequence[i])):
...         ts4.beamSequence[i][j] = ts4.beamSequence[i][j].subdivide(2)
... 
>>> s = stream.Stream()
>>> for ts in [ts1, ts2, ts3, ts4]:
...     m = stream.Measure()
...     m.timeSignature = ts
...     n = note.Note('b')
...     n.quarterLength = 0.125
...     m.repeatAppend(n, 24)
...     s.append(m.makeBeams())
... 
>>> s.show()   # doctest: +SKIP


.. image:: images/overviewMeters-04.*
    :width: 400


The following is a fractional grid representation of the four beam partitions created. 

.. image:: images/overviewMeters-03.*
    :width: 300




Configuring Beat
-------------------------------------

The TimeSignature :attr:`~music21.meter.TimeSignature.beatSequence` MeterSequence employs the hierarchical structure to define the beats and beat divisions of a bar. The outer-most partitions can specify one ore more top level beats. Inner partitions can specify the beat division partitions. For most common meters, beats and beat divisions are pre-configured by default.

In the following example, a simple and a compound meter is created, and the default beat partitions are examined. The :meth:`~music21.meter.MeterSequence.getLevel` method can be used to show the beat and background beat partitions. The timeSignature :attr:`~music21.meter.TimeSignature.beatDuration`,  :attr:`~music21.meter.TimeSignature.beat`, and :attr:`~music21.meter.TimeSignature.beatCountName` properties can be used to return commonly needed beat information. The TimeSignature :attr:`~music21.meter.TimeSignature.beatDivisionCount`, and :attr:`~music21.meter.TimeSignature.beatDivisionCountName` properties can be used to return commonly needed beat division information. These descriptors can be combined to return a string representation of the TimeSignature classification with :attr:`~music21.meter.TimeSignature.classification` property.

>>> ts = meter.TimeSignature('3/4')
>>> ts.beatSequence.getLevel(0)
<MeterSequence {1/4+1/4+1/4}>
>>> ts.beatSequence.getLevel(1)
<MeterSequence {1/8+1/8+1/8+1/8+1/8+1/8}>
>>> ts.beatDuration
<music21.duration.Duration 1.0>
>>> ts.beatCount
3
>>> ts.beatCountName
'Triple'
>>> ts.beatDivisionCount
2
>>> ts.beatDivisionCountName
'Simple'
>>> ts.classification
'Simple Triple'

>>> ts = meter.TimeSignature('12/16')
>>> ts.beatSequence.getLevel(0)
<MeterSequence {3/16+3/16+3/16+3/16}>
>>> ts.beatSequence.getLevel(1)
<MeterSequence {1/16+1/16+1/16+1/16+1/16+1/16+1/16+1/16+1/16+1/16+1/16+1/16}>
>>> ts.beatDuration
<music21.duration.Duration 0.75>
>>> ts.beatCount
4
>>> ts.beatCountName
'Quadruple'
>>> ts.beatDivisionCount
3
>>> ts.beatDivisionCountName
'Compound'
>>> ts.classification
'Compound Quadruple'



Annotating Found Notes with Beat Count
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`~music21.meter.TimeSignature.getBeat` method returns the currently active beat given a quarter length position into the TimeSignature.

In the following example, all leading tones, or C#s, are collected into a new Stream and displayed with annotations for part, measure, and beat.


>>> from music21 import corpus, meter, stream
    
>>> score = corpus.parse('bach/bwv366.xml') 
>>> ts = score.flat.getElementsByClass('TimeSignature')[0]
>>> ts.beatSequence.partition(3)
>>> 
>>> found = stream.Stream()
>>> offsetQL = 0
>>> for part in score.parts:
...     found.insert(offsetQL, part.flat.getElementsByClass('Clef')[0])
...     for i in range(len(part.getElementsByClass('Measure'))):
...         m = part.getElementsByClass('Measure')[i]
...         for n in m.notesAndRests:
...             if n.name == 'C#': 
...                 n.addLyric('%s, m. %s' % (part.id[0], m.number))
...                 n.addLyric('beat %s' % ts.getBeat(n.offset))
...                 found.insert(offsetQL, n)
...                 offsetQL += 4
... 
>>> found.show('musicxml')   # doctest: +SKIP

.. image:: images/overviewMeters-06.*
    :width: 400




Using Beat Depth to Provide Metrical Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Another application of the :attr:`~music21.meter.TimeSignature.beatSequence` MeterSequence is to define the hierarchical depth active for a given note found within the TimeSignature. 

The :meth:`~music21.meter.TimeSignature.getBeatDepth` method, when set with the optional parameter `aligh` to "quantize", shows the number of hierarchical levels that start at or before that point. This value is described by Lerdahl and Jackendoff as metrical analysis.

In the following example, :attr:`~music21.meter.TimeSignature.beatSequence` MeterSequence is partitioned first into one subdivision, and then each subsequent subdivision into two, down to four layers of partitioning. 

The number of hierarchical levels, found with the :meth:`~music21.meter.TimeSignature.getBeatDepth` method, is appended to each note with the :meth:`~music21.note.Note.addLyric` method.


>>> from music21 import corpus, meter 
>>> score = corpus.parse('bach/bwv281.xml') 
>>> partBass = score.getElementById('Bass')
>>> ts = partBass.flat.getElementsByClass('TimeSignature')[0]
>>> ts.beatSequence.partition(1)
>>> for h in range(len(ts.beatSequence)):
...     ts.beatSequence[h] = ts.beatSequence[h].subdivide(2)
...     for i in range(len(ts.beatSequence[h])):
...         ts.beatSequence[h][i] = ts.beatSequence[h][i].subdivide(2)
...         for j in range(len(ts.beatSequence[h][i])):
...             ts.beatSequence[h][i][j] = ts.beatSequence[h][i][j].subdivide(2)
... 
>>> for m in partBass.getElementsByClass('Measure'):
...     for n in m.notesAndRests:
...         for i in range(ts.getBeatDepth(n.offset)):
...             n.addLyric('*')
... 
>>> partBass.getElementsByClass('Measure')[0:7].show()  # doctest: +SKIP


.. image:: images/overviewMeters-07.*
    :width: 400


Alternatively, this type of annotation can be applied to a Stream using the :func:`~music21.analysis.metrical.labelBeatDepth` function.







Configuring Accent
-------------------------------------

The TimeSignature :attr:`~music21.meter.TimeSignature.accentSequence` MeterSequence defines one or more levels of hierarchical accent levels, where quantitative accent value is encoded in MeterTerminal or MeterSequence with a number assigned to the :attr:`~music21.meter.MeterTerminal.weight` attribute.



Applying Articulations Based on Accent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :meth:`~music21.meter.TimeSignature.getAccentWeight` method returns the currently active accent weight given a quarter length position into the TimeSignature. Combined with the :meth:`~music21.meter.TimeSignature.getBeatProgress` method, Notes that start on particular beat can be isolated and examined. 

The following example extracts the Bass line of a Bach chorale in 3/4 and, after repartitioning the beat and accent attributes, applies accents to reflect a meter of 6/8.


>>> from music21 import corpus, meter, articulations 
>>> score = corpus.parse('bach/bwv366.xml')
>>> partBass = score.getElementById('Bass')
>>> ts = partBass.flat.getElementsByClass(meter.TimeSignature)[0]
>>> ts.beatSequence.partition(['3/8', '3/8'])
>>> ts.accentSequence.partition(['3/8', '3/8'])
>>> ts.setAccentWeight([1, .5])
>>> for m in partBass.getElementsByClass('Measure'):
...     lastBeat = None
...     for n in m.notesAndRests:
...         beat, progress = ts.getBeatProgress(n.offset)
...         if beat != lastBeat and progress == 0:
...             if n.tie != None and n.tie.type == 'stop':
...                 continue
...             if ts.getAccentWeight(n.offset) == 1:
...                 mark = articulations.StrongAccent()
...             elif ts.getAccentWeight(n.offset) == .5:
...                 mark = articulations.Accent()
...             n.articulations.append(mark)
...             lastBeat = beat
...         m = m.sorted
... 
>>> partBass.getElementsByClass('Measure')[0:8].show() # doctest: +SKIP


.. image:: images/overviewMeters-05.*
    :width: 400
