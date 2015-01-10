.. _usersGuide_02_note:
.. code:: python

    %load_ext music21.ipython21.ipExtension


.. parsed-literal::
   :class: ipython-result

    Exception reporting mode: Plain
    The music21.ipython21.ipExtension extension is already loaded. To reload it, use:
      %reload_ext music21.ipython21.ipExtension

User's Guide, Chapter 2: Notes
==============================

Notated music, by its very name, consists of a bunch of notes that are
put one after another or simultaneously on a staff. There are other
things, clefs, key signatures, slurs, etc. but the heart of music is the
notes; so to get anywhere in music21 you’ll need to know what the
toolkit thinks about notes and how to work with them.

Go ahead and start IDLE or type “python” at the command line (Terminal
on the Mac or “run: cmd” on Windows) and let’s get started.

Creating and working with Notes
-------------------------------

The music21 concept of a standard note is contained in the
:class:`~music21.note.Note` object, which is found in the ``note``
module.

**Read this if you're new to Python** *(others can skip ahead):* Notice
the difference between object names and module names. Modules, which can
contain one, many, or even zero objects, always begin with a lowercase
letter. Music21's objects always begin with a captial letter. So the
``Note`` object is found in the ``note`` module. The distinction between
uppercase and lowercase is crucial to Python: if you type the name of an
object with the wrong case it won't know what to do and won't give you
any help in distinguishing between them.

In the ``note`` module, there are other classes besides ``note.Note``.
The most important one is ``note.Rest``, which as you imagine represents
a rest. If we load music21 with the command:

.. code:: python

    from music21 import *

then you'll now be able to access the ``note`` module just by typing
``note`` at any command line.

>>> note # doctest: +SKIP
<module 'music21.note' from 'D:\music21files\music21\note.pyc'>
| If you get something like this you'll have access to the music21
``note`` module any time you type ``"note"``. The filename after "from
'D:\\music21files...'" will differ for you. It will show you where you
have music21 installed (if you ever forget where you have music21
installed, this is an easy way to figure it out).
| As long as it ends in ``note.pyc`` or ``note.py`` or something like
that you're fine.

If you want to know what else the ``note`` module contains besides the
Note and Rest objects you can type "``dir(note)``\ " to find out:

.. code:: python

    dir(note)


.. parsed-literal::
   :class: ipython-result

    ['EighthNote',
     'GeneralNote',
     'HalfNote',
     'Lyric',
     'LyricException',
     'NotRest',
     'NotRestException',
     'Note',
     'NoteException',
     'QuarterNote',
     'Rest',
     'SlottedObject',
     'SpacerRest',
     'Test',
     'TestExternal',
     'Unpitched',
     'WholeNote',
     '_DOC_ORDER',
     '_MOD',
     '__builtins__',
     '__doc__',
     '__file__',
     '__name__',
     '__package__',
     'base',
     'beam',
     'common',
     'copy',
     'duration',
     'editorial',
     'environLocal',
     'environment',
     'exceptions21',
     'expressions',
     'interval',
     'noteheadTypeNames',
     'pitch',
     'stemDirectionNames',
     'tie',
     'unittest',
     'volume']


Some of these Objects are just easier ways of making specific kinds of
Note objects (half notes, etc.). Others of them are things that we'll
get to later, like :class:`~music21.note.Lyric` objects. (By the way:
I'm highlighting the names of most objects so they become links to the
full documentation for the object. You can read it later when you're
curious, frustrated, or *Mad Men* is a re-run; you certainly don't need
to click them now).

(Advanced digression):

::

    If you're more of a Python guru and you're afraid of "polluting your namespace,"
    instead of typing "`from music21 import \*`" you can type:


.. code:: python

        import music21

::

    in which case instead of using the word `note`, you'll need to call it `music21.note`


    music21.note # doctest: +SKIP
    <module 'music21.note' from 'D:\music21files\music21\note.pyc'>

::

    If you are a Python guru, you already knew that.  Probably if you didn't already 
    know that, but you've heard about "polluting your namespace," you have a Python
    guru friend who has screamed, "Never use `import \*`!"  Trust me for now that
    this tutorial will be easier if you ignore your friend for a bit; by the end of
    it you'll know enough to be able to follow whatever advice seems most natural to
    you.


*(Back from the Python digression and especially the digression of the
digression):*

Okay, so now you now enough about modules and objects. Let's create a
``note.Note`` object. How about the F at the top of the treble clef
staff:

.. code:: python

    f = note.Note("F5")

We use the convention where middle-C is C4, the octave above it is C5,
etc.

Now you have a Note. Where is it? It's stored in the variable ``f``. You
can verify this just by typing ``f``:

.. code:: python

    f


.. parsed-literal::
   :class: ipython-result

    <music21.note.Note F>


And you can see that it's actually an F and actually in octave 5 by
requesting the ``.name`` and ``.octave`` attributes on the ``Note``
object, ``f``:

.. code:: python

    f.name


.. parsed-literal::
   :class: ipython-result

    'F'


.. code:: python

    f.octave


.. parsed-literal::
   :class: ipython-result

    5


Well, that didn't tell you anything you didn't know already! Let's look
at some other attributes that might tell you something you didn't know:

.. code:: python

    f.frequency


.. parsed-literal::
   :class: ipython-result

    698.456462866008


.. code:: python

    f.pitchClassString


.. parsed-literal::
   :class: ipython-result

    '5'


That's a bit better! So an f is about 698hz (if A4 = 440hz), and it is
pitch class 5 (where C = 0, C# and Db = 1, etc.).

A couple of things that you'll notice:

1. Your ``frequency`` probably has a bunch more numbers instead of
   ending with "...". Mine gives me "698.456462866008". In the docs,
   we'll sometimes write "..." instead of putting in all those numbers
   (or long strings); it's partly a way of saving space, and also
   because the length of a long number and even the last few digits will
   differ from computer to computer depending on whether it's 32-bit or
   64-bit, Mac or PC, number of sunspots last Autumn, etc. Since I don't
   know what computer you're using, don't worry if you get slightly
   different results.


2. There are single quotes around some of the output (like the ``'F'``
   in ``f.name``) and none around others (like the ``5`` in
   ``f.octave``). The quotes mean that that attribute is returning a
   String (a bunch of letters or numbers or simple symbols). The lack of
   quotes means that it's returning a number (either an integer or if
   there's a decimal point, a sneakingly decimal-like thingy called a
   ``float`` (or "floating-point number") which looks and acts just like
   a decimal, except when it doesn't, which is never when you'd expect.


*(The history and theory behind* ``floats`` *will be explained to you at
length by any computer scientist, usually when he or she is the only
thing standing between you and the bar at a party. Really, we shouldn't
be using them anymore, except for the fact that for our computers
they're so much faster to work with than decimals.)*

The difference between the string ``'5'`` and the number ``5`` is
essential to keep in mind. In Python (like most modern programming
languages) we use two equal signs (``==``) to ask if two things are
equal. So:

.. code:: python

    f.octave == 5


.. parsed-literal::
   :class: ipython-result

    True


That's what we'd expect. But try:

.. code:: python

    f.pitchClassString == 5


.. parsed-literal::
   :class: ipython-result

    False


That's because ``5 == '5'`` is ``False``. (There are some lovely
languages such as JavaScript and Perl where it's ``True``; Python's not
one of them. This has many disadvantages at first, but as you go on, you
might see this as an advantage). So to see if ``f.pitchClassString`` is
``'5'`` we need to make ``'5'`` a string by putting it in quotes:

.. code:: python

    f.pitchClassString == "5"


.. parsed-literal::
   :class: ipython-result

    True


In Python it doesn't matter if you put the ``5`` in single or double
quotes:

.. code:: python

    f.pitchClassString == '5'


.. parsed-literal::
   :class: ipython-result

    True


``pitchClassString`` tells you that you should expect a string, because
we've put it in the name. There's also a ``.pitchClass`` which returns a
number:

.. code:: python

    f.pitchClass


.. parsed-literal::
   :class: ipython-result

    5


These two ways of getting a pitch class are basically the same for the
note "F" (except that one's a string and the other is an integer) but
for a B-flat, which is ``.pitchClass`` 10 and ``.pitchClassString`` "A",
it makes a difference.

Let's go ahead and make that B-flat note. In ``music21``, sharps are "#"
as you might expect, but flats are "-". That's because it's otherwise
hard to tell the difference between the ``Note`` "b" (in this instance,
you can write it in upper or lower case) and the symbol "flat". So let's
make that B-flat note:

.. code:: python

    bflat = note.Note("B-2")

I've called the variable "``bflat``\ " here. You could call it
"``Bb``\ " if you want or "``b_flat``\ ", but not "``b-flat``\ " because
dashes aren't allowed in variable names:

.. code:: python

    b-flat = note.Note("B-2")

::

      File "<ipython-input-26-d519b3e88921>", line 1
        b-flat = note.Note("B-2")
    SyntaxError: can't assign to operator

Since this note has an accidental you can get it by using the
``.accidental`` property:

.. code:: python

    bflat.accidental


.. parsed-literal::
   :class: ipython-result

    <accidental flat>


Here we have something that isn't a number and doesn't have quotes
around it. That usually means that what ``.accidental`` returns is
another object -- in this case an :class:`~music21.pitch.Accidental`
object. As we saw above, objects have attributes (and other goodies
we'll get to in a second) and the ``Accidental`` object is no exception.
So let's make a new variable that will store ``bflat``'s accidental:

.. code:: python

    acc = bflat.accidental

We'll get to all the attributes of ``Accidental`` objects in a bit, but
here are two of them: ``.alter`` and ``.displayLocation``. You'll use
the first one quite a bit: it shows how many semitones this
``Accidental`` changes the ``Note``:

.. code:: python

    acc.alter


.. parsed-literal::
   :class: ipython-result

    -1.0


Since this ``Accidental`` is a flat, its ``.alter`` is a negative
number. Notice that it's also not an integer, but a float. That might
indicate that music21 supports things like quarter-tones, and in this
case you'd be right.

Look back at the two lines "``acc = bflat.accidental``\ " and
"``acc.alter``\ ". We set ``acc`` to be the value of ``bflat``'s
``.accidental`` attribute and then we get the value of that variable's
``.alter`` attribute. We could have skipped the first step altogether
and "chained" the two attributes together in one step:

.. code:: python

    bflat.accidental.alter


.. parsed-literal::
   :class: ipython-result

    -1.0


.. code:: python

    acc.displayLocation


.. parsed-literal::
   :class: ipython-result

    'normal'


Good to know that we've set a sensible default. If you want to have the
accidental display above the note, you'll have to set that yourself:

.. code:: python

    acc.displayLocation = 'above'

.. code:: python

    acc.displayLocation


.. parsed-literal::
   :class: ipython-result

    'above'


Our variable ``"acc"`` is the **exact** accidental that is attached to
the B-flat Note stored as ``bflat``. It's not a flat that's similar to
B-flat's flat, but the same one. (in computer-speak, ``acc`` is a
*reference* to ``.accidental``). So now if we look at the
``.displayLocation`` of ``bflat.accidental`` we see that it too is set
to the silly "above" position:

.. code:: python

    bflat.accidental.displayLocation


.. parsed-literal::
   :class: ipython-result

    'above'


Python is one of those cool computer languages where if an object
doesn't have a particular attribute but you think it should, you can add
it to the object (some people find that this makes objects messy, but I
don't mind it). For what I hope are obvious reasons, the ``Note`` object
does not have an attribute called "``wasWrittenByStockhausen``\ ". So if
you try to access it, you'll get an error:

.. code:: python

    bflat.wasWrittenByStockhausen


.. parsed-literal::
   :class: ipython-result

    Exception reporting mode: Plain

::

    Traceback (most recent call last):

      File "<ipython-input-39-b7de1a2ae80a>", line 2, in <module>
        bflat.wasWrittenByStockhausen

    AttributeError: 'Note' object has no attribute 'wasWrittenByStockhausen'

.. code:: python

    
