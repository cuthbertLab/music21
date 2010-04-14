.. _overviewNotes:


Overview: Pitches, Durations, Notes, and Chords
=======================================================

For represented notated music, the :class:`~music21.note.Note` object is a critical tool. Note and :class:`~music21.chord.Chord` objects are both subclasses of :class:`~music21.base.Music21Object`, and share many features. Both are built, in part, from :class:`~music21.pitch.Pitch` and :class:`~music21.duration.Duration` objects.

This overview will illustrate key features of music21's Pitch, Duration, Note, and Chord objects. For complete documentation of these objects, see :ref:`modulePitch`, :ref:`moduleDuration`, :ref:`moduleNote`, and :ref:`moduleChord`.




Creating and Editing Pitches
----------------------------------

To create a Pitch object, simply call the class with a note name. A name (such as *B*) can be provided with optional symbols for sharp or flat (*#* or *-* respectively). An octave designation can optionally be provided (where middle C is C4).

>>> from music21 import pitch
>>> p1 = pitch.Pitch('b-4')

There are numerous ways of expressing pitch. Many are available as properties from the Pitch object. The following example demonstrates many of these properties. 

>>> p1.octave
4
>>> p1.pitchClass
10
>>> p1.name
'B-'
>>> p1.nameWithOctave
'B-4'
>>> p1.midi
70

Some of these parameters are settable. By setting a parameter in the appropriate format, the Pitch object is changed to reflect the new value. 

>>> p1.name = 'd#'
>>> p1.octave = 3
>>> p1
D#2

Accidentals are represented with an :class:`~music21.pitch.Accidental` object on the :attr:`~music21.pitch.Pitch.accidental` attribute of Pitch.

>>> p1.accidental
<accidental sharp>
>>> p1.accidental.alter
-1.0

Pitches, like many objects, can be transposed by an interval specified in any format permitted by the :class:`~music21.interval.Interval` object. Common string presentation are acceptable. The :meth:`~music21.pitch.Pitch.transpose` method returns a new Pitch object, leaving the original unchanged. 

>>> p2 = p1.transpose('M7')
>>> p2
C##4

As with nearly all music21 objects, we can call the :class:`~music21.base.Music21Object.show` method to display this Pitch in notation.

>>> p1.show()

.. image:: images/overviewNotes-01.*
    :width: 600





Creating and Editing Durations
----------------------------------

Duration objects are ubiquitous in music21. Nearly all objects have, or can have, a Duration. A Duration can represent any time span, either quantized to common whole number ratios or otherwise. A Duration may represent a single notated entity (such as dotted quarter note) or tied aggregation of durations (such as a half note tied to a sixteenth note).

To create Duration, call the class with an optional duration value, expressed either as a string (such as "quarter" or "half") or with a number (a value in Quarter Lengths). The following example creates a half note duration and a dotted quarter note duration.

>>> from music21 import Duration
>>> d1 = duration.Duration('half')
>>> d2 = duration.Duration(1.5)

As with pitch, there are many ways of expressing duration. Many are available as properties from the Duration object. The :attr:`~music21.duration.Duration.quarterLength` property expresses the duration in Quarter Lengths, a common unit throughout music21. The following example demonstrates many of these properties. 

>>> d1.quarterLength
2.0
>>> d2.dots
1
>>> d2.type
'quarter'
>>> d2.quarterLength
1.5

Some of the Duration parameters are settable. In the following example the :attr:`~music21.duration.Duration.quarterLength` property is set to a new value. All corresponding parameters are updated when necessary.

>>> d1.quarterLength = 2.25
>>> d1.type
'complex'

The :class:`~music21.base.Music21Object.show` method can be used to display the Duration with a default pitch value. 

>>> d1.show()

.. image:: images/overviewNotes-02.*
    :width: 600





Creating and Editing Notes
---------------------------

Note objects contain, as key components, a Pitch and a Duration instance. Notes contain additional parameters and functionality. We can create a Note in the same way we do a Pitch, by providing an initial Pitch value.

>>> from music21 import note
>>> n1 = note.Note('e-5')

Numerous Pitch and Duration attributes are made available as attributes of Note. For example:

>>> n1.name
'E-'
>>> n1.pitchClass
3
>>> n1.midi
75
>>> n1.quarterLength
1.0


Notes can store numerous lines of text as lyrics or other notations on the :attr:`~music21.note.Note.lyric` property. While this value can be set directly, the :meth:`~music21.note.GeneralNote.addLyric` method permits adding multiple notations to a single Note sequential;y. In the following example three Note attributes are added to the Note as annotations.

>>> n1.addLyric(n1.name)
>>> n1.addLyric(n1.pitchClass)
>>> n1.addLyric('QL: %s' % n1.quarterLength)

As should be clear, we can alway check our work with the :class:`~music21.base.Music21Object.show` method.

>>> n1.show()

.. image:: images/overviewNotes-03.*
    :width: 600

As with the Duration object, we can edit the :attr:`~music21.note.Note.quarterLength` property to quickly change the Note's Duration. 

>>> n1.quarterLength = 6.25
>>> n1.show()

.. image:: images/overviewNotes-04.*
    :width: 600


As is clear, a Note may be tied to another. If so, a :class:`~music21.note.Tie` object will be found on the :attr:`~music21.note.Note.tie` attribute. 




Creating and Editing Chords
------------------------------

Note and Chord objects, as both subclasses of the :class:`~music21.note.GeneralNote` object, share many features. Both contain a Duration object. A Note has only one Pitch; a Chord, however, contains a list one or more Pitch objects accessed via the :attr:`~music21.chord.Chord.pitches` property. The Chord object additional has numerous analytic methods (such as :meth:`~music21.chord.Chord.isDiminishedSeventh`) as well as a variety of post-tanal tools (such as :attr:`~music21.chord.Chord.forteClass`; see :ref:`overviewPostTonal`).

A Chord can be created with a list of Pitch objects or strings identical to those used for creating Pitches. Additional, pitch class integers can be provided. 

>>> from music21 import chord
>>> c1 = chord.Chord(['a#3', 'g4', 'f#5'])
>>> c1.pitches
[A#3, G4, F#5]

Like with a Note, Duration object properties can be configured from properties on Chord. For example, the Quarter Length of the Chord can be accessed from the :attr:`~music21.chord.Chord.quarterLength` property. The :class:`~music21.base.Music21Object.show` method can be used to display the results.

>>> c1.quarterLength = 1 + 1/3.
>>> c1.show()

.. image:: images/overviewNotes-05.*
    :width: 600
    

A Chord, like a Note and Pitch, can be transposed by an interval specified in any format permitted by the :class:`~music21.interval.Interval` object. The :meth:`~music21.chord.Chord.transpose` method returns a new Chord instance. 

>>> c2 = c1.transpose('m2')
>>> c2.show()

.. image:: images/overviewNotes-06.*
    :width: 600


Finally, a Chord, like a Note, can have one or my lyrics. The :meth:`~music21.note.GeneralNote.addLyric` method functions the same as it does for Note. In the following example, a text annotation of the Forte set class name is added to the Chord.


>>> c2.addLyric(c2.forteClass)
>>> c2.show()
 
.. image:: images/overviewNotes-07.*
    :width: 600
