.. _overviewStreams:


Advanced Streams
==============================================

*(this file is just a collection of Stream topics that haven't
yet made it into the User's Guide...I'm working on it!)*



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
['Soprano', 'Alto', 'Tenor', 'Bass']
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
...     print(el)
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

