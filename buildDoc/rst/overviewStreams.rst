.. _overviewStreams:


Overview: Streams, Scores, Parts, and Measures
==============================================

The :class:`~music21.stream.Stream` object and its many subclasses offer the fundamental container of music21 objects. As a container like a Python list (or an array in some languages), a Stream can be used to hold objects. These objects can be ordered in more than one way, or treated as an unordered collection. Objects stored in a Stream can be spaced in time; each stored object can have an offset from the beginning of the Stream. Streams, further, can store and offset other Streams, permitting a wide variety of nested, ordered, and timed structures.

Commonly used subclasses of Streams include the :class:`~music21.stream.Score`, :class:`~music21.stream.Part`, and :class:`~music21.stream.Measure`. As should be clear, any time we want to collect and contain a group of music21 objects, we do so in a Stream. Streams can, of course, be used for less conventional organizational structures. We frequently will build and pass around temporary Streams, as doing so gives us access to a wide variety of tools for extracting, processing, and manipulating objects on the Stream. 

A critical feature of music21's design is that one music21 object can be simultaneously stored (or, more accurately, referenced) in more than one Stream. For examples, we might have numerous :class:`~music21.stream.Measure` Streams contained in a :class:`~music21.stream.Part` Stream. If we extract a region of this Part (using the :meth:`~music21.stream.Stream.getMeasureRange` method), we get a new Stream containing the specified Measures. We have not actually created new Measures or their components; the output Stream simply has references to the same objects. Changes made to Measures in this output Stream will be simultaneously reflected in Measures in the source Part. 

This overview will illustrate key features of music21's Stream. For complete documentation on Streams, see :ref:`moduleStream`.



Appending and Inserting Objects into Streams
---------------------------------------------

Streams provide a way to structure and position music21 objects both hierarchically (as Streams nested within Streams) and temporally (as objects and Streams placed in time). Objects stored on lists are called elements, and must be either a :class:`~music21.base.Music21Object` or an object contained within a :class:`~music21.base.ElementWrapper`. Streams store their objects internally on a list called :attr:`~music21.stream.Stream.elements`, though direct manipulation of this list is rarely needed. 

The most common application of Streams is as a place to store Notes. For an introduction to Notes, see :ref:`overviewNotes`; for complete documentation on Notes, see :ref:`moduleNote`.

Notes, like all Muisc21Objects, have a Duration object that describes the time span they occupy. The span of a Duration can be described in many ways, but a convenient measure is quarter lengths (QLs), or the number of whole or fractional quarter note durations. Notes, when placed in a Stream, also have an offset that describes their position. These offset values are also given in QLs. 

To begin, lets create an instance of a Stream and an instance of a Note. We can set the :class:`~music21.pitch.Pitch` object to represent an E, and we can set the :class:`~music21.duration.Duration` object to represent a half-note (2 QLs).

>>> from music21 import note, stream
>>> s = stream.Stream()
>>> n1 = note.Note()
>>> n1.pitch.name = 'E4'
>>> n1.duration.type = 'half'
>>> n1.quarterLength
2.0

There is more than one way to place this Note in the Stream. A convenient way is with the Stream method :meth:`~music21.stream.Stream.append`. This is related to, but very different from, the `append()` method of Python lists. After using append, there are a number of ways to confirm that our Note is on the Stream. We can use the Python `len()` function to return the number of elements on the Stream. Alternatively, we can use the :meth:`~music21.stream.Stream.show` method with the 'text' or (assuming correct setup of your environment) the 'musicxml' argument to return explicit notations. (See :ref:`quickStart` for basic configuration information; see :ref:`environment` for complete information on configuring your :class:`~music21.environment.Environment`.)

>>> s.append(n1)
>>> len(s)
1
>>> s.show('text')
{0.0} <music21.note.Note E>

>>> s.show('musicxml')

.. image:: images/overviewStreams-01.*
    :width: 600

Every element on a Stream has an offset in that Stream (and possibly other Streams). In the last example, no offset was given with the :meth:`~music21.stream.Stream.append` method. This method automatically gets an offset for newly-appended objects based on the objects that are already on the Stream. Specifically, the object with the highest offset and combined duration. Generally, this is the next available offset after all current elements have sounded. Whenever we append, we are adding to the end. 

If we add another Note with :meth:`~music21.stream.Stream.append`, its offset will automatically be set to the end of the previously added Note.

>>> n2 = note.Note('f#') # we can supply a note name as an initial argument
>>> n2.quarterLength = .5 # we can access some Duration attributes from Note
>>> s.append(n2)
>>> len(s)
2
>>> n2.offset # we can examine the Note's current offset
2.0
>>> s.show('text')
{0.0} <music21.note.Note E>
{2.0} <music21.note.Note F#>

>>> s.show('musicxml')

.. image:: images/overviewStreams-02.*
    :width: 600


In addition to viewing the length of the Stream and the output provided by the :meth:`~music21.stream.Stream.show` method, we can examine other properties of the Stream. Each Stream can return a Duration object, representing the Duration of the entire Stream. Similarly, we can look at the Stream's :attr:`~music21.stream.Stream.highestTime` property, which returns the QL value of the element with the largest combined offset and Duration. The :attr:`~music21.stream.Stream.lowestOffset` property returns the minimum of all offsets for all elements on the Stream.

>>> s.duration.quarterLength
2.5
>>> s.highestTime
2.5
>>> s.lowestOffset
0.0


We can add a number of independent, unique copies of the same Note with the Stream method :meth:`~music21.stream.Stream.repeatAppend`. This creates independent copies (using Python's `copy.deepcopy` function) of the supplied object, not references. The user must supply an object to be copied and the number of times that object is to be repeatedly placed. 


>>> n3 = note.Note('d#5') # octave values can be included in creation arguments
>>> n3.quarterLength = .25 # a sixteenth note
>>> s.repeatAppend(n3, 6)
>>> len(s)
8
>>> s.highestTime
4.0
>>> s.show('text')
{0.0} <music21.note.Note E>
{2.0} <music21.note.Note F#>
{2.5} <music21.note.Note D#>
{2.75} <music21.note.Note D#>
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
{3.5} <music21.note.Note D#>
{3.75} <music21.note.Note D#>

>>> s.show('musicxml')

.. image:: images/overviewStreams-03.*
    :width: 600


As shown above, :meth:`~music21.stream.Stream.append` and :meth:`~music21.stream.Stream.repeatAppend`, automatically determine offset times for elements. To explicitly set the offset of an element when adding it to a Stream, the :meth:`~music21.stream.Stream.insert` method can be used. This method, given an offset, will place an object in the Stream at that offset.

>>> r1 = note.Rest()
>>> r1.quarterLength = .5
>>> n4 = note.Note('b5')
>>> n4.quarterLength = 1.5
>>> s.insert(4, r1)
>>> s.insert(4.5, n4)
>>> s.show('text')
{0.0} <music21.note.Note E>
{2.0} <music21.note.Note F#>
{2.5} <music21.note.Note D#>
{2.75} <music21.note.Note D#>
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
{3.5} <music21.note.Note D#>
{3.75} <music21.note.Note D#>
{4.0} <music21.note.Rest rest>
{4.5} <music21.note.Note B>

>>> s.show('musicxml')

.. image:: images/overviewStreams-04.*
    :width: 600



Accessing Stream Elements by Iteration and Index
-------------------------------------------------

Just as there are many ways to add objects to Streams, there are many ways to get a Stream's elements. Some of these approaches work like Python lists, using iteration or index numbers. Other approaches filter the Stream, selecting only the objects that match a certain class or tag. 

In many situations we will want to iterate over the elements in a Stream. This can be done just like any other Python list-like object:

>>> for e in s:
...     print(e)
... 
<music21.note.Note E>
<music21.note.Note F#>
<music21.note.Note D#>
<music21.note.Note D#>
<music21.note.Note D#>
<music21.note.Note D#>
<music21.note.Note D#>
<music21.note.Note D#>
<music21.note.Rest rest>
<music21.note.Note B>

Elements in Streams can also be accessed by index values, integers counting from zero and specifying the ordered positions of elements in a Stream. Importantly, the ordered position is not always the same as the offset position. Multiple elements can exist in a Stream at the same offset, and the offset values are not always in the order of index values. 

The syntax for accessing elements by index is the same as accessing items by index in Python. Similarly, we can take slices of Streams, returning a new Stream, as we would from Python lists. As with Python lists, the last boundary of a slice (e.g. 6 in [3:6]) is not included in the slice. 

>>> s[3]
<music21.note.Note D#>
>>> s[3:6]
<music21.stream.Stream object at 0x18fdef0>
>>> s[3:6].show('text')
{2.75} <music21.note.Note D#>
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
>>> s[-1]
<music21.note.Note B>

While full list-like functionality of the Stream is not yet provided, some additional methods familiar to users of Python lists are also available. The Stream :meth:`~music21.stream.Stream.index` method can be used to get the first-encountered index of a supplied object. Given an index, an element from the Stream can be removed with the :meth:`~music21.stream.Stream.pop` method. 

>>> s.index(n2)
1
>>> s.index(r1)
8
>>> s.index(n3)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/ariza/_x/src/music21/music21/stream.py", line 362, in index
    match = i
ValueError: Could not find object in index


The index for `n3` cannot be obtained because the :meth:`~music21.stream.Stream.repeatAppend` method makes independent copies (deep copies) of the object provided as an argument. Thus, only copies of `n3`, not references to `n3`, are stored on the Stream. There are, of course, other ways to find these Notes. 



Accessing Stream Elements by Class and Offset
-----------------------------------------------------------

We often need to gather elements form a Stream based on criteria other than the index position of the element. We can gather elements based on the class (object type) of the element, but offset range, or by specific identifiers attached to the element. As before, gathering elements from a Stream will often return a new Stream with references to the collected elements.

Gathering elements from a Stream based on the class of the element provides a way to filter the Stream for desired types of objects. The :meth:`~music21.stream.Stream.getElementsByClass` method returns a Stream of elements that are instances or subclasses of the provided classes. The example below gathers all :class:`~music21.note.Note` objects and then all :class:`~music21.note.Rest` objects.

>>> sOut = s.getElementsByClass(note.Note)
>>> sOut.show('text')
{0.0} <music21.note.Note E>
{2.0} <music21.note.Note F#>
{2.5} <music21.note.Note D#>
{2.75} <music21.note.Note D#>
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
{3.5} <music21.note.Note D#>
{3.75} <music21.note.Note D#>
{4.5} <music21.note.Note B>

>>> sOut = s.getElementsByClass(note.Rest)
>>> sOut.show('text')
{4.0} <music21.note.Rest rest>

A number of properties available with Stream instances make getting specific object classes from a Stream easier. The :attr:`~music21.stream.Stream.notes` property returns more than just Note objects; all subclasses of :class:`~music21.note.GeneralNote` and :class:`~music21.chord.Chord` are returned in a Stream. This property is very useful for stripping Note-like objects from notational elements such as :class:`~music21.meter.TimeSignature` and :class:`~music21.meter.Clef` objects. 

>>> sOut = s.notes
>>> len(sOut) == len(s)
True

Similarly, the :attr:`~music21.stream.Stream.pitches` property returns all Pitch objects. Pitch objects, however, are not subclasses of :class:`~music21.base.Music21Object`; they do not have Duration objects or offsets, and are thus returned in a Python list.

>>> listOut = s.pitches
>>> len(listOut)
9
>>> listOut
[E4, F#, D#5, D#5, D#5, D#5, D#5, D#5, B5]

Gathering elements from a Stream based a single offset or an offset range permits treating the elements as part of timed sequence of events that can be be cut and sliced. 

The :meth:`~music21.stream.Stream.getElementsByOffset` method returns a Stream of all elements that fall either at a single offset or within a range of two offsets provided as an argument. In both cases a Stream is returned.

>>> sOut = s.getElementsByOffset(3)
>>> len(sOut)
1
>>> sOut[0]
<music21.note.Note D#>

>>> sOut = s.getElementsByOffset(3, 4)
>>> len(sOut)
5
>>> sOut.show('text')
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
{3.5} <music21.note.Note D#>
{3.75} <music21.note.Note D#>
{4.0} <music21.note.Rest rest>

In the last example, Note and Rest objects are returned within the offset range. If wanted to only gather the Note objects found in this range, we could first use the :meth:`~music21.stream.Stream.getElementsByOffset` and then use the :meth:`~music21.stream.Stream.getElementsByClass` method. As both methods return Streams, chained method calls are possible and idiomatic.

>>> sOut = s.getElementsByOffset(3, 4).getElementsByClass(note.Note)
>>> sOut.show('text')
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
{3.5} <music21.note.Note D#>
{3.75} <music21.note.Note D#>

Numerous additional methods permit gathering elements by offset values and positions. See :meth:`~music21.stream.Stream.getElementAtOrBefore` and  :meth:`~music21.stream.Stream.getElementAfterElement` for more examples.




Accessing Scores, Parts, Measures, and Notes
-------------------------------------------------

Streams provide a way to structure and position music21 objects both hierarchically and temporally. A Stream, or a Stream subclass such as :class:`~music21.stream.Measure`, can be placed within another Stream. 

As shown in :ref:`quickStart`, a common arrangement of nested Streams is a :class:`~music21.stream.Score` Stream containing one or more :class:`~music21.stream.Part` Streams, each Part Stream in turn containing one or more :class:`~music21.stream.Measure` Streams. 

Such an arrangement of Stream objects is the common way musical scores are represented in music21. For example, importing a four-part chorale by J. S. Bach will provide a Score object with four Part Streams, each Part containing multiple Measure objects. Music21 comes with a :ref:`moduleCorpus.base` module that provides access to a large collection of scores, including all the Bach chorales. We can parse the score from the corpus with the :func:`~music21.corpus.base.parseWork` function. 

>>> from music21 import corpus
>>> sBach = corpus.parseWork('bach/bwv57.8')

We can access and examine elements at each level of this Score by using standard Python syntax for lists within lists. Thus, we can see the length of each component: first the Score, then the Part at index zero, and then the object (a Measure) at index two, all from accessing the same name `sBach`.

>>> len(sBach)
4
>>> len(sBach[0])
19
>>> len(sBach[0][1])
6

Note that more than just Measures might be stored in a Part (such as :class:`~music21.instrument.Instrument` objects), and more than just Notes might be stored in a Measure (such as :class:`~music21.meter.TimeSignature` and :class:`~music21.key.KeySignature` objects). We thus frequently need to filter Stream and Stream subclasses by the class we seek. To repeat the count and select specific classes, we can use the :meth:`~music21.stream.Stream.getElementsByClass` method. Notice how the counts deviate from the examples above.


>>> from music21 import stream, meter, key, note
>>> len(sBach.getElementsByClass(stream.Part))
4
>>> len(sBach[0].getElementsByClass(stream.Measure))
18
>>> len(sBach[0][1].getElementsByClass(note.Note))
3

The index position of a Measure may not be the same as the Measure number. For that reason, gathering Measures is best accomplished with either the :meth:`~music21.stream.Stream.getMeasureRange` method (returning a Stream of Parts or Measures) or the :meth:`~music21.stream.Stream.getMeasure` method (returning a single Measure). In the following examples a single Measure from each part is appended to a new Stream.

>>> sNew = stream.Stream()
>>> sNew.append(sBach[0].getMeasure(3))
>>> sNew.append(sBach[1].getMeasure(5))
>>> sNew.append(sBach[2].getMeasure(7))
>>> sNew.append(sBach[3].getMeasure(9))
>>> sNew.show()

.. image:: images/overviewStreams-05.*
    :width: 600


.. TODO: Accessing Components of Parts and Measures
.. have a section on getting attributes form Parts and Measures
.. can show how to use .measureNumber, .timeSignature attributes of Measure



Flattening Hierarchical Streams
-------------------------------------------------

While nested Streams offer expressive flexibility, it is often useful to be able to flatten all Stream and Stream subclasses into a single Stream containing only the elements that are not Stream subclasses. The  :attr:`~music21.stream.Stream.flat` property provides immediate access to such a flat representation of a Stream. For example, doing a similar count of components, such as that show above, we see that we cannot get to all of the Note objects of a complete Score until we flatten its Part and Measure objects by accessing the `flat` attribute. 

>>> len(sBach.getElementsByClass(note.Note))
0
>>> len(sBach.flat.getElementsByClass(note.Note))
213

Element offsets are always relative to the Stream that contains them. For example, a Measure, when placed in a Stream, might have an offset of 16. This offset describes the position of the Measure in the Stream. Components of this Measure, such as Notes, have offset values relative only to their container, the Measure. The first Note of this Measure, then, has an offset of 0. In the following example we find the offset of the measure eight (using the :meth:`~music21.base.Music21Object.getOffsetBySite` method) is 21; the offset of the second Note in this Measure (index 1), however, is 1.

.. NOTE: intentionally skipping a discussion of objects having offsets stored
.. for multiple sites here; see below

>>> m = sBach[0].getMeasure(8)
>>> m.getOffsetBySite(sBach[0])
21.0
>>> n = sBach[0].getMeasure(8).notes[0]
>>> n
<music21.note.Note B->
>>> n.getOffsetBySite(m)
1.0

Flattening a structure of nested Streams will set new, shifted offsets for each of the elements on the Stream, reflecting their appropriate position in the context of the Stream from which the `flat` property was accessed. For example, if a flat version of the first part of the Bach chorale is obtained, the note defined above has the appropriate offset of 22 (the Measure offset of 21 plus the Note offset within this Measure of 1). 

>>> pFlat = sBach[0].flat
>>> pFlat[pFlat.index(n)]
<music21.note.Note B->
>>> pFlat[pFlat.index(n)].offset
22.0

As an aside, it is important to recognize that the offset of the Note has not been edited; instead, a Note, as all Music21Objects, can store multiple pairs of sites and offsets. Music21Objects retain an offset relative to all Stream or Stream subclasses they are contained within, even if just in passing.




Accessing Stream Elements by Group and Identifiers
-----------------------------------------------------------

All :class:`~music21.base.Music21Object` subclasses, such as :class:`~music21.note.Note` and :class:`~music21.stream.Stream`, have attributes for :attr:`~music21.base.Music21Object.id` and :attr:`~music21.base.Music21Object.group`. 

As shown in :ref:`quickStart`, the `id` attribute is commonly used to distinguish Part objects in a Score, but may have other applications. The :meth:`~music21.stream.Stream.getElementById` method can be used to access elements of a Stream by `id`. As an example, after examining all of the `id` attributes of the Score, a new Score can be created, rearranging the order of the Parts by using the :meth:`~music21.stream.Stream.insert` method with an offset of zero.

>>> [part.id for part in sBach]
[u'Soprano', u'Alto', u'Tenor', u'Bass']
>>> sNew = stream.Score()
>>> sNew.insert(0, sBach.getElementById('Bass'))
>>> sNew.insert(0, sBach.getElementById('Tenor'))
>>> sNew.insert(0, sBach.getElementById('Alto'))
>>> sNew.insert(0, sBach.getElementById('Soprano'))
>>> sNew.show()

.. image:: images/overviewStreams-06.*
    :width: 600



Visualizing Streams in Plots
---------------------------------------------

While the :meth:`~music21.stream.Stream.show` method provides a valuable view of a Stream, a visual plot a Stream's elements is very useful. Sometimes called a piano roll, we might graph the pitch of a Note over its position in a Measure (or offset if no Measures are defined). The :meth:`~music21.stream.Stream.plot` method permits us to create a plot of any Stream or Stream subclass. There are a large variety of plots: see :ref:`moduleGraph` for a complete list. There are a number of ways to get the desired plot; one, as demonstrated below, is to provide the name of the plot as a string. We can also add a keyword argument for the title of the plot (and configure many other features).


>>> sBach.getElementById('Soprano').plot('PlotHorizontalBarPitchSpaceOffset', title='Soprano')

.. image:: images/overviewStreams-07.*
    :width: 600







