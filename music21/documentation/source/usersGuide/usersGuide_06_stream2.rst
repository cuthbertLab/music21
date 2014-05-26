.. _usersGuide_06_stream2:
.. code:: python


User's Guide, Chapter 6: Streams (II): Hierarchies, Recursion, and Flattening
=============================================================================

We ended Chapter 4 (:ref:`usersGuide_04_stream1`) with a
:class:`~music21.stream.Stream` that was contained within another
``Stream`` object. Let's recreate that class:

.. code:: python

    from music21 import *
    
    note1 = note.Note("C4")
    note1.duration.type = 'half'
    note2 = note.Note("F#4")
    note3 = note.Note("B-2")
    
    stream1 = stream.Stream()
    stream1.id = 'some notes'
    stream1.append(note1)
    stream1.append(note2)
    stream1.append(note3)
    
    biggerStream = stream.Stream()
    note2 = note.Note("D#5")
    biggerStream.insert(0, note2)
    biggerStream.append(stream1)

The only way to find out what was in the contained Stream that we
demonstrated so far was the :meth:`~music21.base.Music21Object.show`
method using the ``('text')`` argument.

.. code:: python

    biggerStream.show('text')


.. parsed-literal::
   :class: ipython-result

    {0.0} <music21.note.Note D#>
    {1.0} <music21.stream.Stream some notes>
        {0.0} <music21.note.Note C>
        {2.0} <music21.note.Note F#>
        {3.0} <music21.note.Note B->

As Chapter 4 noted, there's

Recursion in Streams
--------------------

Flattening a Stream
-------------------

.. code:: python

    
