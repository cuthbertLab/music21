.. _overviewStreams:


Overview: Streams, Scores, Parts, and Measures
==============================================

The :class:`~music21.stream.Stream` object and its subclasses (Score, 
Part, Measure) are the fundamental containers for music21 objects such
as :class:`~music21.note.Note`, :class:`~music21.chord.Chord`, 
:class:`~music21.clef.Clef`, :class:`~music21.meter.TimeSignature` objects. 

A container is like a Python list 
(or an array in some languages).  

Objects stored in a Stream are generally spaced in time; each stored object has 
an offset usually representing how many quarter notes it lies from the beginning 
of the Stream.  For instance in a 4/4 measure of two half notes, the first note
will be at offset 0.0, and the second at offset 2.0. 

Streams, further, can store other Streams, permitting a wide variety of nested, 
ordered, and timed structures.  These stored streams also have offsets.  So if
we put two 4/4 Measure objects (subclasses of Stream) into a Part (also a 
type of Stream), then the first measure will be at offset 0.0 and the second
measure will be at offset 4.0.  

Commonly used subclasses of Streams include the :class:`~music21.stream.Score`, 
:class:`~music21.stream.Part`, and :class:`~music21.stream.Measure`. It is 
important to grasp that any time we want to collect and contain a group of 
music21 objects, we put them into a Stream. Streams can also be used for 
less conventional organizational structures. We frequently will build and pass 
around short-lived, temporary Streams, since doing this opens up a wide variety 
of tools for extracting, processing, and manipulating objects on the Stream. 
For instance, if you are looking at only notes on beat 2 of any measure, you'll
probably want to put them into a Stream as well.

A critical feature of music21's design that distinguishes it from other 
music analysis frameworks is that one music21 object can be 
simultaneously stored (or, more accurately, referenced) in more than one Stream. 
For examples, we might have numerous :class:`~music21.stream.Measure` Streams 
contained in a :class:`~music21.stream.Part` Stream. If we extract a region of 
this Part (using the :meth:`~music21.stream.Stream.measures` method), we get a 
new Stream containing the specified Measures and the contained notes. We have 
not actually created new 
notes within these extracted measures; the output Stream simply has references 
to the 
same objects. Changes made to Notes in this output Stream will be simultaneously 
reflected in Notes in the source Part.   There is one limitation though:
the same object should not appear twice in one hierarchical structure of Streams.
For instance, you should not put a note object in both measure 3 and measure 5
of the same piece -- it can appear in measure 3 of one piece and measure 5 of
another piece. (For instance, if you wanted to track a particular note's context
in an original version of a score and an arrangement). Most users will never
need to worry about these details: just know that this feature lets music21
do some things that no other software package can do.


Enough about what Streams are.  The rest of this overview will show you what
you can do with them. (For complete 
documentation on Streams, see :ref:`moduleStream`.)



Appending and Inserting Objects into Streams
---------------------------------------------

Streams structure and position music21 objects.  These objects 
are structured hierarchically (for instance in a Measure in a Part
in a Score) and temporally (e.g., at offset 4 in a Measure).

Objects stored in Streams are called elements and must be some type
of :class:`~music21.base.Music21Object` (don't worry, almost everything 
in music21 is a Music21Object, such as Note, Chord, TimeSignature, etc.).  

(If you want to put an object that's not a Music21Object in a Stream, 
put it in an :class:`~music21.base.ElementWrapper`.) 

Streams store their objects internally on a list called 
:attr:`~music21.stream.Stream.elements`, though you'll rarely need to 
deal with this directly. 

The most common use of Streams is as places to store Notes. For an 
introduction to what you can do with Notes, see :ref:`usersGuide_02_notes`; 
and for complete documentation on Notes, see :ref:`moduleNote`.

Notes, like all Music21Objects, have a .duration property (which is a 
:class:`~music21.duration.Duration` object) that describes how long they
are and what they should look like on page. Though the span of a 
Duration can mean many things (the number of seconds it lasts; the number
of inches in a graphic notation score), by default, and by far the most
common use is as quarter lengths (QLs), that is the number of number of 
quarter notes they last.  A quarter note has duration 1.0, a whole has 4.0,
a dotted eighth 0.75, and a triplet-16th 0.166667 (approximately). 

As we mentioned earlier, when placed in a Stream, Notes and other 
elements also have an **offset** (stored in .offset) 
that describes their position from the beginning of the stream. 
These offset values are also given in QLs. 

To begin, lets create a Stream and a Note. We will set the 
:class:`~music21.pitch.Pitch` object to E above middle C, and set the 
:class:`~music21.duration.Duration` object to represent a half-note (2 QLs).

>>> from music21 import *
>>> s = stream.Stream()
>>> n1 = note.Note()
>>> n1.pitch.name = 'E4'
>>> n1.duration.type = 'half'
>>> n1.duration.quarterLength
2.0

Now we'll put the quarter note in the Stream.
There is more than one way to do this. A convenient way is with the Stream 
method :meth:`~music21.stream.Stream.append` which puts it at the end of the Stream. 
This is related to, but more powerful than, the `append()` method of Python lists. 

>>> s.append(n1)


After putting the note in the stream, there are a number of ways to confirm that 
our Note is actually in the Stream. We can use the Python `len()` function to tell us
the number of elements on the Stream. 


>>> len(s)
1


Alternatively, we can use the :meth:`~music21.stream.Stream.show` method 
called as show('text') to see what is in the Stream and what its offset 
is (here 0.0, since we put it at the end of an empty stream). 

>>> s.show('text')
{0.0} <music21.note.Note E>

If you've setup your environment properly, then calling show with the 
'musicxml' 
argument should open up Finale Reader, or Sibelius, or 
MuseScore or some music notation
software and display the notes below.

>>> s.show('musicxml')    # doctest: +SKIP

.. image:: images/overviewStreams-01.*
    :width: 600

Every element on a Stream has an offset in that Stream (and possibly 
other Streams). In the last example, no offset was given with the 
:meth:`~music21.stream.Stream.append` method. This method automatically 
gets an offset for newly-appended objects based on the objects that 
are already on the Stream. Specifically, the object with the highest 
offset and combined duration. Generally, this is the next available 
offset after all current elements have sounded. Whenever we append, 
we are adding to the end. 

If we add another Note with :meth:`~music21.stream.Stream.append`, 
its offset will automatically be set to the end of the previously added Note.

Let's create a second note, called n2.  This time we will set the
pitch name of the note at the moment of creation as F# above middle C.
Then we will set its quarter length to 0.5, or an eighth note.  Notice
also that last time we called n1.duration.quarterLength and this time
just n2.quarterLength -- they're exactly the same thing.  The latter is
just a shortcut to the former, since we use quarterLength so often.


>>> n2 = note.Note('f#4')
>>> n2.quarterLength = 0.5
>>> s.append(n2)


Now we see that there are two notes in the Stream

>>> len(s)
2

We also can see that n2 was placed at offset 2.0, i.e. just
after the end of n1, which was a half note.

>>> n2.offset
2.0


Now when we view the stream, either with show('text') or show('musicxml')
we'll see two notes.  (N.B. you can usually call show('musicxml') just as
show() since musicxml is generally the default).


>>> s.show('text')
{0.0} <music21.note.Note E>
{2.0} <music21.note.Note F#>

>>> s.show('musicxml')   # doctest: +SKIP

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

>>> s.show('musicxml')   # doctest: +SKIP

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

>>> s.show('musicxml')    # doctest: +SKIP

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
<music21.stream.Stream ...>
>>> s[3:6].show('text')
{2.75} <music21.note.Note D#>
{3.0} <music21.note.Note D#>
{3.25} <music21.note.Note D#>
>>> s[-1]
<music21.note.Note B>

While full list-like functionality of the Stream is not provided, some additional methods familiar to users of Python lists are also available. The Stream :meth:`~music21.stream.Stream.index` method can be used to get the first-encountered index of a supplied object. Given an index, an element from the Stream can be removed with the :meth:`~music21.stream.Stream.pop` method. 

>>> s.index(n2)
1
>>> s.index(r1)
8
>>> s.index(n3) 
Traceback (most recent call last):
...
StreamException: cannot find object (<music21.note.Note D#>) in Stream


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

A number of properties available with Stream instances make getting specific object classes from a Stream easier. The :attr:`~music21.stream.Stream.notesAndRests` property returns more than just Note objects; all subclasses of :class:`~music21.note.GeneralNote` and :class:`~music21.chord.Chord` are returned in a Stream. This property is very useful for stripping Note-like objects from notational elements such as :class:`~music21.meter.TimeSignature` and :class:`~music21.meter.Clef` objects. 

>>> sOut = s.notesAndRests
>>> len(sOut) == len(s)
True

Similarly, the :attr:`~music21.stream.Stream.pitches` property returns all Pitch objects. Pitch objects, however, are not subclasses of :class:`~music21.base.Music21Object`; they do not have Duration objects or offsets, and are thus returned in a Python list.

>>> listOut = s.pitches
>>> len(listOut)
9

Let's print the name of each pitch here:

>>> [str(p) for p in listOut]
['E4', 'F#4', 'D#5', 'D#5', 'D#5', 'D#5', 'D#5', 'D#5', 'B5']

Gathering elements from a Stream based a single offset or an offset range permits treating the elements as part of timed sequence of events that can be cut and sliced. 

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

A common arrangement of nested Streams is a 
:class:`~music21.stream.Score` Stream containing one or more 
:class:`~music21.stream.Part` Streams, each Part Stream in turn containing one 
or more :class:`~music21.stream.Measure` Streams. 

Such an arrangement of Stream objects is the common way musical scores are represented in music21. For example, importing a four-part chorale by J. S. Bach will provide a Score object with four Part Streams, each Part containing multiple Measure objects. Music21 comes with a :ref:`moduleCorpus` module that provides access to a large collection of scores, including all the Bach chorales. We can parse the score from the corpus with the :func:`~music21.corpus.parse` function. 

>>> from music21 import *
>>> sBach = corpus.parse('bach/bwv57.8')

We can access and examine elements at each level of this Score by using standard Python syntax 
for lists within lists. Thus, we can see the length of each component: 
first the Score which has five elements, a :class:`~music21.metadata.Metadata` object and four parts.
Then we find the length of first Part at index one which indicates 19 objects (18 of them are measures).  
Then within that part we find an object (a Measure) at index 1. All of these subprograms can
be accessed from looking within the same score object `sBach`.

>>> len(sBach)
6
>>> len(sBach[1])
19
>>> len(sBach[1][1])
6

But how did we know that index [1] would be a Part and index [1][1] would
be a measure?  As writers of the tutorial, we know this piece well enough
to know that.  But as we noted above, more than just Measures might be 
stored in a Part object
(such as :class:`~music21.instrument.Instrument` objects), 
and more than just Note and Rest objects might be stored in a Measure 
(such as :class:`~music21.meter.TimeSignature` 
and :class:`~music21.key.KeySignature` objects). We it's much safer 
to filter Stream and Stream subclasses by 
the class we seek. To repeat the count and select specific classes, 
we can use the :meth:`~music21.stream.Stream.getElementsByClass` method. 

Notice how the counts deviate from the examples above.


>>> from music21 import *
>>> len(sBach.getElementsByClass(stream.Part))
4
>>> len(sBach.getElementsByClass(stream.Part)[0].getElementsByClass(stream.Measure))
18
>>> len(sBach.getElementsByClass(stream.Part)[0].getElementsByClass(stream.Measure)[1].getElementsByClass(note.Note))
3

The :meth:`~music21.stream.Stream.getElementsByClass` method can also take a
string representation of the last section of the class name, thus we could've rewritten
the code above as:


>>> from music21 import *
>>> len(sBach.getElementsByClass('Part'))
4
>>> len(sBach.getElementsByClass('Part')[0].getElementsByClass('Measure'))
18
>>> len(sBach.getElementsByClass('Part')[0].getElementsByClass('Measure')[1].getElementsByClass('Note'))
3


This way of doing things is a bit faster to code, but a little less safe.  Suppose,
for instance there were objects of type stream.Measure and tape.Measure; the latter
way of writing the code would get both of them.  (But this ambiguity is rare enough
that it's safe enough to use the strings in most code.)


There are some convenience properties you should know about.  Calling .parts is the
same as .getElementsByClass(stream.Part) and calling .notes is the same as
.getElementsByClass([note.Note, note.Chord]).  Notice that the last example also shows
that you can give more than one class to getElementsByClass by passing in a list of
classes.   Note also that when using .parts or .notes, you do not write the () after
the name.  Also be aware that .notes does not include rests.  For that, we have a
method called .notesAndRests.


The index position of a Measure is often not the same as the Measure number.  For instance,
most pieces that don't have pickup measures begin with measure 1, not zero.  Sometimes there are measure
discontinuities within a piece (e.g., some people number first and second endings with the same
measure number).
For that reason, gathering Measures is best accomplished not with getElementsByClass(stream.Measure)
but instead with either 
the :meth:`~music21.stream.Stream.measures` method (returning a Stream of Parts or Measures) 
or the :meth:`~music21.stream.Stream.measure` method (returning a single Measure).  What is great
about these methods is that they can work on a whole score and not just a single part.

In the following examples a single Measure from each part is appended to a new Stream.

>>> sNew = stream.Stream()
>>> sNew.append(sBach.parts[0].measure(3))
>>> sNew.append(sBach.parts[1].measure(5))
>>> sNew.append(sBach.parts[2].measure(7))
>>> sNew.append(sBach.parts[3].measure(9))
>>> sNew.show()    # doctest: +SKIP

.. image:: images/overviewStreams-05.*
    :width: 600


.. TODO: Accessing Components of Parts and Measures
.. have a section on getting attributes form Parts and Measures
.. can show how to use .number, .timeSignature attributes of Measure



Flattening Hierarchical Streams
-------------------------------------------------

While nested Streams offer expressive flexibility, it is often useful to be able to flatten all Stream and Stream subclasses into a single Stream containing only the elements that are not Stream subclasses. The  :attr:`~music21.stream.Stream.flat` property provides immediate access to such a flat representation of a Stream. For example, doing a similar count of components, such as that show above, we see that we cannot get to all of the Note objects of a complete Score until we flatten its Part and Measure objects by accessing the `flat` attribute. 

>>> len(sBach.getElementsByClass(note.Note))
0
>>> len(sBach.flat.getElementsByClass(note.Note))
213

Element offsets are always relative to the Stream that contains them. For example, a Measure, when placed in a Stream, might have an offset of 16. This offset describes the position of the Measure in the Stream. Components of this Measure, such as Notes, have offset values relative only to their container, the Measure. The first Note of this Measure, then, has an offset of 0. In the following example we find that the offset of measure eight (using the :meth:`~music21.base.Music21Object.getOffsetBySite` method) is 21; the offset of the second Note in this Measure (index 1), however, is 1.

.. NOTE: intentionally skipping a discussion of objects having offsets stored
.. for multiple sites here; see below

>>> m = sBach.parts[0].getElementsByClass('Measure')[7]
>>> m.getOffsetBySite(sBach.parts[0])
21.0
>>> n = sBach.parts[0].measure(8).notes[1]
>>> n
<music21.note.Note B->
>>> n.getOffsetBySite(m)
1.0

Flattening a structure of nested Streams will set new, shifted offsets for each of the elements on the Stream, reflecting their appropriate position in the context of the Stream from which the `flat` property was accessed. For example, if a flat version of the first part of the Bach chorale is obtained, the note defined above has the appropriate offset of 22 (the Measure offset of 21 plus the Note offset within this Measure of 1). 

>>> pFlat = sBach.parts[0].flat
>>> indexN = pFlat.index(n)
>>> pFlat[indexN]
<music21.note.Note B->
>>> pFlat[indexN].offset
22.0

As an aside, it is important to recognize that the offset of the Note has not been edited; instead, a Note, as all Music21Objects, can store multiple pairs of sites and offsets. Music21Objects retain an offset relative to all Stream or Stream subclasses they are contained within, even if just in passing.




Accessing Stream Elements by Id and Group
-----------------------------------------------------------

All :class:`~music21.base.Music21Object` subclasses, such as 
:class:`~music21.note.Note` and :class:`~music21.stream.Stream`, 
have attributes for :attr:`~music21.base.Music21Object.id` 
and :attr:`~music21.base.Music21Object.group`. 

The `id` attribute is commonly used to 
distinguish Part objects in a Score, but may have other applications. 
The :meth:`~music21.stream.Stream.getElementById` method can be used 
to access elements of a Stream by `id`. As an example, after examining 
all of the `id` attributes of the Score, a new Score can be created, 
rearranging the order of the Parts by using the 
:meth:`~music21.stream.Stream.insert` method with an offset of zero.

>>> [part.id for part in sBach.parts]
[u'Soprano', u'Alto', u'Tenor', u'Bass']
>>> sNew = stream.Score()
>>> sNew.insert(0, sBach.getElementById('Bass'))
>>> sNew.insert(0, sBach.getElementById('Tenor'))
>>> sNew.insert(0, sBach.getElementById('Alto'))
>>> sNew.insert(0, sBach.getElementById('Soprano'))
>>> sNew.show()   # doctest: +SKIP

.. image:: images/overviewStreams-06.*
    :width: 600



Visualizing Streams in Plots
---------------------------------------------

While the :meth:`~music21.stream.Stream.show` method provides common
musical views of a Stream, a visual plot a Stream's elements is very 
useful. Sometimes called a piano roll, we might graph the pitch of a 
Note over its position in a Measure (or offset if no Measures are 
defined). The :meth:`~music21.stream.Stream.plot` method permits us to 
create a plot of any Stream or Stream subclass (note that the additional
package matplotlib needs to be installed to run graphs, see :ref:`installAdditional`
for more information). There are a large variety 
of plots: see :ref:`moduleGraph` for a complete list. There are a number 
of ways to get the desired plot; one, as demonstrated below, is to provide 
the name of the plot as a string. We can also add a keyword argument for 
the title of the plot (and configure many other features).


>>> sBach.getElementById('Soprano').plot('PlotHorizontalBarPitchSpaceOffset', title='Soprano')   # doctest: +SKIP

.. image:: images/overviewStreams-07.*
    :width: 600

Advanced Topic: Ordering Streams
================================
As list-like objects, Streams hold objects in a particular order. 
These objects are usually ordered by their musical position in
the score according to their offset in quarter notes.  Objects with
the same offset are ordered by what class they are a part of.  For instance,
you'd expect that if you have a TimeSignature, Note, Clef, and KeySignature
at offset 0.0 in a piece that if you iterate through a Stream in order, 
you'd get the Clef, KeySignature, TimeSignature, and Note in that order (which
is the order they appear in a Score).  Music21 automatically sorts the classes
in that order.  Classes have an attribute called "classSortOrder" that defines
the order in which they should appear.  Classes with lower classSortOrder come
first as this example indicates:

>>> [obj.classSortOrder for obj in [clef.Clef, key.KeySignature, meter.TimeSignature, note.Note]]
[0, 2, 4, 20]

N.B. that classSortOrder can be obtained either from the class definition (`clef.Clef.classSortOrder`)
or from an instance of that class (`c = clef.Clef() ; c.classSortOrder`):

>>> c = clef.TrebleClef()
>>> k = key.KeySignature(2) # 2 sharps
>>> triple = meter.TimeSignature('3/8')
>>> n = note.Note("F#5")
>>> [obj.classSortOrder for obj in [c, k, triple, n]]
[0, 2, 4, 20]

Thus, all new Music21Object classes should define classSortOrder somewhere.
It can be any integer (or even a floating point number).  

If it is important that objects in at the same offset have a particular order,
you can set the order by setting the `.priority` attribute of each object.
The default is zero.  If two objects have the same priority then the classSortOrder
is used as a secondary comparison.  The following example creates a second note
and specifies that the first note comes before the TimeSignature, but the second comes
after:

>>> n2 = note.Note("D5")
>>> n.priority = 0
>>> triple.priority = 1
>>> n2.priority = 2

Now let's put all our objects in a Stream 
at offset 0.0 in a random order and see what order the objects come out
when we iterate over the Stream:

>>> s = stream.Stream()
>>> s.insert(0.0, n2)
>>> s.insert(0.0, k)
>>> s.insert(0.0, c)
>>> s.insert(0.0, triple)
>>> s.insert(0.0, n)
>>> for el in s:
...     print el
<music21.clef.TrebleClef>
<music21.key.KeySignature of 2 sharps>
<music21.note.Note F#>
<music21.meter.TimeSignature 3/8>
<music21.note.Note D>

This is the order we hoped for.

There is one more way that elements in a Stream can be returned, for advanced
uses only.  Each Stream has an `autoSort` property.  By default it is On.  But
if you turn it off, then elements are returned in the order they are added
regardless of offset, priority, or classSortOrder.  Here is an example of that:

>>> messyStream = stream.Stream()
>>> messyStream.autoSort = False
>>> messyStream.insert(4.0, note.Note("C#"))
>>> n1 = note.Note("D#")
>>> n2 = note.Note("E")
>>> n1.priority = 20
>>> n2.priority = 0 # should come before n1 if at same offset
>>> messyStream.insert(2.0, n1)
>>> messyStream.insert(2.0, n2)
>>> messyStream.show('text')
{4.0} <music21.note.Note C#>
{2.0} <music21.note.Note D#>
{2.0} <music21.note.Note E>

the setting `autoSort = False` can speed up some operations if you already know
that all the notes are in order.  Inside the stream.py module you'll see some
even faster operations such as `_insertCore()` and `_appendCore()` which are
even faster and which we use when translating from one format to another.  After
running an `_insertCore()` operation, the Stream is in an unusuable state until
`_elementsChanged()` is run, which lets the Stream ruminate over its new state
as if a normal `insert()` or `append()` operation has been done.  Mixing
`_insertCore()` and `_appendCore()` commands without running `_elementsChanged()`
is likely to have disasterous consequences.  Use one or the other.

However, append does work well with `autoSort = False`, as this example demonstrates:

>>> messyStream.append(note.Note("F"))
>>> messyStream.show('text')
{4.0} <music21.note.Note C#>
{2.0} <music21.note.Note D#>
{2.0} <music21.note.Note E>
{5.0} <music21.note.Note F> 

If you want to get back to the sorted state, just turn `autoSort = True`:

>>> messyStream.autoSort = True
>>> messyStream.show('text')
{2.0} <music21.note.Note E>
{2.0} <music21.note.Note D#>
{4.0} <music21.note.Note C#>
{5.0} <music21.note.Note F>

Note that this is a destructive operation.  Turning `autoSort` back to
`False` won't get you back the earlier order:

>>> messyStream.autoSort = False
>>> messyStream.show('text')
{2.0} <music21.note.Note E>
{2.0} <music21.note.Note D#>
{4.0} <music21.note.Note C#>
{5.0} <music21.note.Note F>

