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



Getting and Accessing Objects from Streams
---------------------------------------------

Just as there are many ways to add objects to Streams, there are many ways to get a Stream's elements. Some of these approaches work like Python lists, using iteration or index numbers. Other approaches filters the Stream, selecting only the objects that match a certain class or tag. 




Visualizing Streams in Plots
---------------------------------------------

While the :meth:`~music21.stream.Stream.show` method provides valuable output a visual plot a Stream's elements is very useful. 





Nested and Flat Streams
-------------------------------------------------

Streams provide a way to structure and position music21 objects both hierarchically and temporally. Frequently, a Stream is placed within a Stream. 







