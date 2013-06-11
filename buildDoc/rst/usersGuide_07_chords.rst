.. code:: python

    %load_ext music21.ipython21.ipExtension

User's Guide, Chapter 7: Chords
===============================


The most general way to create a ``Chord`` object is by passing in a
list of pitch names you want in the chord

.. code:: python

    from music21 import *

.. code:: python

    cMinor = chord.Chord(["C4","G4","E-5"])

``Note`` and ``Chord`` objects, since both are subclasses of the
``GeneralNote`` object share many features in common:

.. code:: python

    cMinor.duration.type = 'half'

.. code:: python

    cMinor.quarterLength


.. parsed-literal::

    2.0


But since a ``Chord`` contains many pitches, it does not have a
``.pitch`` attribute. Instead it has a ``.pitches`` attribute which
returns a list of pitches in the Chord.

.. code:: python

    cMinor.pitch

::

    ---------------------------------------------------------------------------
    AttributeError                            Traceback (most recent call last)
    <ipython-input-6-682233136f94> in <module>()
    ----> 1 cMinor.pitch
    
    AttributeError: 'Chord' object has no attribute 'pitch'
.. code:: python

    cMinor.pitches


.. parsed-literal::

    [<music21.pitch.Pitch C4>, <music21.pitch.Pitch G4>, <music21.pitch.Pitch E-5>]


Okay, but you already knew what pitches were in the ``Chord`` since you
just created it! What else can you do with it?

How about determining if it is a major or a minor triad?

.. code:: python

    cMinor.isMajorTriad()


.. parsed-literal::

    False


.. code:: python

    cMinor.isMinorTriad()


.. parsed-literal::

    True


You can also figure out if it is in inversion or not:

.. code:: python

    cMinor.inversion()


.. parsed-literal::

    0


Chords in root position have inversion of 0. But consider this other
chord:

.. code:: python

    cMajor = chord.Chord(["E3","C4","G4"])
    cMajor.inversion()


.. parsed-literal::

    1


With this chord, two other methods become important:

.. code:: python

    cMajor.root()


.. parsed-literal::

    <music21.pitch.Pitch C4>


.. code:: python

    cMajor.bass()


.. parsed-literal::

    <music21.pitch.Pitch E3>


You can find the third and fifth of the ``Chord`` with .third and
.fifth. Note that these properties do not have ``()`` after them. This
was a mistake in how we created ``music21`` and hopefully this will all
be consistent soon:

.. code:: python

    cMajor.third


.. parsed-literal::

    <music21.pitch.Pitch E3>


.. code:: python

    cMajor.fifth


.. parsed-literal::

    <music21.pitch.Pitch G4>


There is also a .seventh property, but it won't do anything here:

.. code:: python

    cMajor.seventh

The result of that is ``None`` which we can test like so...

.. code:: python

    cMajor.seventh is None


.. parsed-literal::

    True


Displaying Chords
-----------------


We can display the ``Chord`` object just like any ``Note`` (Don't worry
if this isn't working for you yet...we'll get this set up in Chapter 8)

.. code:: python

    cMinor.show()


.. image:: usersGuide_07_chords_files/_fig_12.png


.. code:: python

    cMajor.show()


.. image:: usersGuide_07_chords_files/_fig_14.png


These chords are a bit "spacey", so let's get ``c`` in
``.closedPosition``:

.. code:: python

    cClosed = cMinor.closedPosition()
    cClosed.show()


.. image:: usersGuide_07_chords_files/_fig_16.png


Notice that ``c`` is unchanged. The closed position chord is only
cClosed:

.. code:: python

    cMinor.show()


.. image:: usersGuide_07_chords_files/_fig_18.png


If we wanted to change the Chord object itself, we call
``.closedPosition(inPlace = True)`` which alters the original. Since the
original is altered, we don't need to put ``x = ...`` in front of it

.. code:: python

    cMajor.closedPosition(inPlace = True)

.. code:: python

    cMajor.show()


.. image:: usersGuide_07_chords_files/_fig_20.png


We can get the common name of each of these Chords:

.. code:: python

    cn1 = cMinor.commonName
    print cn1


.. parsed-literal::

    minor triad

.. code:: python

    print cMajor.commonName


.. parsed-literal::

    major triad

More complex chords have less common "commonNames". Here's one that the
American composer Elliott Carter liked a lot.

.. code:: python

    elliottCarterChord = chord.Chord(['C4','D-4','E4','F#4'])
    elliottCarterChord.commonName


.. parsed-literal::

    'all-interval tetrachord'


.. code:: python

    elliottCarterChord.show()


.. image:: usersGuide_07_chords_files/_fig_25.png


More ways of creating chords; Chords and Streams
------------------------------------------------


There are other ways of creating a Chord if you'd like. One way is from
a bunch of already created ``Note`` objects:

.. code:: python

    d = note.Note('D4')
    fSharp = note.Note('F#4')
    a = note.Note('A5')
    dMajor = chord.Chord([d, fSharp, a])
    
    dMajor.show()


.. image:: usersGuide_07_chords_files/_fig_27.png


Or we can pass a string with note names separated by spaces:

.. code:: python

    e7 = chord.Chord("E4 G#4 B4 D5")
    e7.show()


.. image:: usersGuide_07_chords_files/_fig_29.png


The octaves are optional, especially if everything is within an octave:

.. code:: python

    es = chord.Chord("E- G B-")
    es.show()


.. image:: usersGuide_07_chords_files/_fig_31.png


But you will definitely want them if a chord crosses the boundary of an
octave (between B and C). Unless you love 6-4 chords, this is probably
not what you want:

.. code:: python

    fMajor = chord.Chord("F A C")
    fMajor.show()


.. image:: usersGuide_07_chords_files/_fig_33.png


That chord is in second inversion, or 64:

.. code:: python

    print fMajor.inversion()
    print fMajor.inversionName()


.. parsed-literal::

    2
    64

In addition to .commonName, there are a few other "name" properties that
might be interesting:

.. code:: python

    fMajor.fullName


.. parsed-literal::

    'Chord {F | A | C} Quarter'


.. code:: python

    fMajor.pitchedCommonName


.. parsed-literal::

    'F-major triad'


Like ``Note`` objects, we can put ``Chord`` objects inside Streams:

.. code:: python

    stream1 = stream.Stream()
    stream1.append(cMinor)
    stream1.append(fMajor)
    stream1.append(es)
    stream1.show()


.. image:: usersGuide_07_chords_files/_fig_38.png


We can mix and match Notes, Rests, and Chords:

.. code:: python

    rest1 = note.Rest()
    rest1.quarterLength = 0.5
    noteASharp = note.Note('A#5')
    noteASharp.quarterLength = 1.5
    
    stream2 = stream.Stream()
    stream2.append(cMinor)
    stream2.append(rest1)
    stream2.append(noteASharp)
    stream2.show()


.. image:: usersGuide_07_chords_files/_fig_40.png


Post-tonal chords (in brief)
----------------------------


There are a lot of methods for dealing with post-tonal aspects of
chords. If you're not interested in twentieth century music, go ahead
and skip to the next chapter, but, here are some fun things.

The ``intervalVector`` of a chord is a list of the number of
``[semitones, whole-tones, minor-thirds/augmented-seconds, major-thirds, perfect fourths, and tritones]``
in the chord or inversion. A minor triad, for instance, has one minor
third (C to E-flat), one major third (E-flat to G), and one perfect
fourth (G to C above, since octave does not matter):

.. code:: python

    cMinor.intervalVector


.. parsed-literal::

    [0, 0, 1, 1, 1, 0]


A major triad has the same interval vector:

.. code:: python

    cMajor.intervalVector


.. parsed-literal::

    [0, 0, 1, 1, 1, 0]


The elliottCarterChord is unique in that it has an ``.intervalVector``
of all 1's:

.. code:: python

    elliottCarterChord.intervalVector


.. parsed-literal::

    [1, 1, 1, 1, 1, 1]


Well, it's almost unique: there is another chord with the same
``.intervalVector``. That Chord is called its Z-relation or Z-pair.

.. code:: python

    elliottCarterChord.hasZRelation


.. parsed-literal::

    True


.. code:: python

    otherECChord = elliottCarterChord.getZRelation()

.. code:: python

    otherECChord


.. parsed-literal::

    <music21.chord.Chord C C# E- G>


We can see it (our Lilypond output currently isn't putting the
accidental right here...it works fine in MusicXML...)

.. code:: python

    otherECChord.show()


.. image:: usersGuide_07_chords_files/_fig_47.png


.. code:: python

    otherECChord.intervalVector


.. parsed-literal::

    [1, 1, 1, 1, 1, 1]


The other post-tonal tools you might be interested in are given below.
We'll return to them in a later chapter:

.. code:: python

    print elliottCarterChord.primeForm
    print elliottCarterChord.normalForm
    print elliottCarterChord.forteClass


.. parsed-literal::

    [0, 1, 4, 6]
    [0, 1, 4, 6]
    4-15A

If you really only care about semitones, you can create a chord just
with the pitchClasses:

.. code:: python

    oddChord = chord.Chord([1, 3, 7, 9, 10])
    oddChord.show()


.. image:: usersGuide_07_chords_files/_fig_51.png


Though if you use pitchClasses above 11, then they are treated as MIDI
numbers, where 60 = MiddleC, 72 = C5, etc. Enharmonic spelling is chosen
automatically.

.. code:: python

    midiChordType = chord.Chord([60, 65, 70, 75])
    midiChordType.show()


.. image:: usersGuide_07_chords_files/_fig_53.png


Okay, so now you've learned the basics (and more!) of Notes and Chords,
the next chapter will cover configuring MusicXML and writing files.

.. code:: python

    # ignore this...
    from IPython.core.display import publish_html
    publish_html('<style>.prompt {display: None;}</style>')
