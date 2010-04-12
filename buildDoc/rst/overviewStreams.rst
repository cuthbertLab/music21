.. _overviewStreams:


Overview: Streams, Scores, Parts, and Measures
==============================================

The :class:`~music21.stream.Stream` object and its many subclasses offer the fundamental container of music21 objects. As a container like a Python list (or an array in some languages), a Stream can be used to hold objects. These objects can be ordered in more than one way, or treated as an unordered collection. Objects stored in a Stream can be spaced in time; each stored object can have an offset from the beginning of the Stream. Streams, further, can store and offset other Streams, permitting a wide variety of nested, ordered, and timed structures.

Commonly used subclasses of Streams include the :class:`~music21.stream.Score`, :class:`~music21.stream.Part`, and :class:`~music21.stream.Measure`. As should be clear, any time we want to collect and contain a group of music21 objects, we do so in a Stream. Streams can, of course, be used for less conventional organizational structures. We frequently will build and pass around temporary Streams, as doing so gives us access to wide variety of tools for extracting, processing, and manipulating objects on the Stream. 

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

There is more than one way to place this Note in the Stream. A convenient way is with the Stream method :meth:`~music21.stream.Stream.append`. This is related to, but very different from, the `append()` method of Python lists. After using append, there are a number of ways to confirm that our Note is on the Stream. We can use the Python `len()` function to return the number of elements on the Stream. Alternatively, we can use the :meth:`~music21.stream.Stream.show` method with the 'text' or (assuming correct setup of your environment) the 'musicxml' argument to return explicit notations. (See :ref:`quickStart` for basic configuraton information; see :ref:`environment` for complete information on configuring your :class:`~music21.environment.Environment`.)

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

Similarly, the :attr:`~music21.stream.Stream.pitches` property returns all Pitch objects. Pitch objects, however, are not subclasses of :class:`~music21.base.Music21Object`; they do not have Duration objects or offsets, and are thus are returned in a Python list.

>>> listOut = s.pitches
>>> len(listOut)
9
>>> listOut
[E4, F#, D#5, D#5, D#5, D#5, D#5, D#5, B5]

Gathering elements from a Stream based a single offset or an offset range permits treating the elements as part of timed sequence of events that can be be cut and sliced. 

The :meth:`~music21.stream.Stream.getElementsByOffset` returns a Stream of all elements that fall either at a single offset or within a range of two offsets provided as an argument. In both cases a Stream is returned.

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




Accessing Stream Elements by Group and Identifiers
-----------------------------------------------------------

All :class:`~music21.base.Music21Object` subclasses have attributes for `id` and `group`. 





Nested and Flat Streams
-------------------------------------------------

Streams provide a way to structure and position music21 objects both hierarchically and temporally. Frequently, a Stream is placed within a Stream. 







Visualizing Streams in Plots
---------------------------------------------

While the :meth:`~music21.stream.Stream.show` method provides valuable output a visual plot a Stream's elements is very useful. 





