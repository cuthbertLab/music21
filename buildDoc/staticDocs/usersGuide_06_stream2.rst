.. _usersGuide_06_stream2:

User's Guide, Chapter 6: Streams (II): Hierarchies, Recursion, and Flattening
==============================================================================
We ended :ref:`Chapter 4 usersGuide_04_stream1` with a :class:`~music21.stream.Stream` that was
contained within another `Stream` object.  The only way to find out what was in the contained
Stream that we demonstrated so far was the :meth:`~music21.base.Music21Object.show` method
using the `('text')` argument:

>>> biggerStream.show('text') # doctest: +SKIP
{0.0} <music21.note.Note D#>
{1.0} <music21.stream.Stream some notes>
	{0.0} <music21.note.Note C>
	{2.0} <music21.note.Note F#>
	{3.0} <music21.note.Note B->





Recursion in Streams
----------------------

Flattening a Stream
-------------------

 
