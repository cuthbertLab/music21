.. _overviewPostTonal:


Overview: Post-Tonal Tools
=============================================

The music21 toolkit features many tools for analyzing and creating music within a post-tonal context. A Chord can be identified as a Forte class, a list of pitch class can be used to create a 12-tone matrix, and many other anaystical tools are available. 

For complete documentation on post-tonal tools, see the many methods in :class:`~music21.chord.Chord` as well as the objects in :ref:`moduleSerial` such as :class:`~music21.serial.TwelveToneMatrix`, :class:`~music21.serial.TwelveToneRow`, and the many twelve tone rows defined in :attr:`~music21.serial.vienneseRows`.


Pitches as Pitch Classes
--------------------------

Any music21 :class:`~music21.pitch.Pitch`, or a  :class:`~music21.note.Note` containing Pitch, can be expressed as pitch class integer using the :attr:`~music21.pitch.Pitch.pitchClass` and :attr:`~music21.pitch.Pitch.pitchClassString` properties. 

In the following example, the :func:`~music21.corpus.base.parseWork` function is used to create a :class:`~music21.stream.Score` object. The :attr:`~music21.base.Music21Object.id` attribute of each contained :class:`~music21.stream.Part` is presented in a list. 

>>> from music21 import corpus
>>> aScore = corpus.parseWork('beethoven/opus59no2', 3)
>>> [e.id for e in aScore]
[u'Violin I.', u'Violin II.', u'Viola.', u'Violoncello.']

We can view the fourth and fifth measures of the violin Part by obtaining the part from the Stream with :meth:`~music21.stream.Stream.getElementById` method. Next, we can extract the desired measures with :meth:`~music21.stream.Stream.getMeasureRange`. Calling the :meth:`~music21.stream.Stream.show` method will, assuming correct setup of your environment, open a display of the extracted measures. (See :ref:`quickStart` for basic configuraton information; see :ref:`envrionment` for complete information on configuring your :class:`music21.environment.Environment`.). 

>>> vlnPart = aScore.getElementById('Violin I.')
>>> mRange = vlnPart.getMeasureRange(4,7)
>>> mRange.show()

.. image:: images/overviewPostTonal-01.*
    :width: 500



Chords as Forte Set Classes
----------------------------

Any music21 Chord can be interpreted as a Force Set class. 



Interval Vectors
----------------------------

All music21 Chords can provide access to the associated interval vectors.



Twelve-Tone Matrices and Processing
-------------------------------------

Any music21 Chord can be interpreted as a Force Set class. 



