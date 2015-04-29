.. _quickStart:


Quick Start: Getting Started with music21
=============================================

Here are some quick steps to get up and running quickly with music21. 





Download and Install
-----------------------


First, download and install music21. Read the full instructions at: :ref:`install`.



Starting Python and Importing Modules
-------------------------------------

Like all Python functionality, music21 can be run from a Python 
script (a .py file) or interactively from the Python interpreter. The 
Python interpreter is designated with the command prompt `>>>`.

On UNIX-based operating systems with a command line prompt 
(Terminal.app on Mac OS X), entering `python` will start the 
Python interpreter.

On Windows, starting IDLE from the start menu will provide an 
interactive Python session.

Once you start Python, you can check to see if your music21 
installation is correctly configured by trying to import a music21 module. 
A module is a Python file that offers reusable resources. 
These are all found inside the music21 package, so often we will 
import a module (or all of them) from music21. To import the 
:mod:`music21.corpus` module 
from music21, enter the following command.

>>> from music21 import corpus
>>>

Assuming this works, your music21 installation is complete and you can move on. However, you may get the following error:

>>> from music21 import corpus   # doctest: +SKIP  
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: No module named music21
>>> 
    
If this happens, Python is not able to find the music21 package. 
Return and review the instructions in :ref:`install` or contact 
the music21 group for help:

http://groups.google.com/group/music21list




Examining a Score
---------------------------------------

Once music21 is installed, opening and examining a score and it elements is a good first step. Music21 comes with a corpus, a large collection freely distributable music stored in the MusicXML and humdrum formats. These files can be found in the music21/corpus directory. However, tools are provided for easy, direct access.

To import, or parse, a score stored in the corpus, use the :mod:`music21.corpus` module. (To see a complete listing of works in the corpus, see :ref:`referenceCorpus`.) We imported this module above, but here, lets import all music21 modules with the catch-all import statement `from music21 import *`. We will often use this import statement to quickly import all modules for easy access. 

We will the use the :func:`~music21.corpus.parseWork` method to translate the file (a MusicXML or humdrum file) into music21 objects.

>>> from music21 import *
>>> sBach = corpus.parse('bach/bwv7.7')

The score is returned as a music21 :class:`~music21.stream.Score`, which is a type (subclass) of a music21 :class:`~music21.stream.Stream`. 

Once the score is parsed, we can view, transform, and manipulate its 
components in a variety of ways. If we want to output and view the 
entire score, we can use the :meth:`~music21.stream.Stream.show` method. 

Without any arguments, this method does two things. First, it 
writes a MusicXML file (the default output format) of the current Stream as a temporary file or in the user-specified scratch directory. (This directory can be defined as part of the user's Environment settings. See :ref:`environment` for complete details.) Second, it attempts to open this file with a 
user-specified helper application. 

For a MusicXML file, an application that can load and display a MusicXML file as notation, or a MusicXML reader, is very useful. See :ref:`install` for information on "Additional Software Components," or download and install MuseScore or Finale Reader immediately:

http://www.musescore.org

http://www.finalemusic.com/Reader

After installing an appropriate MusicXML reader, the generated file can be examined and opened. For music21 to automatically open MusicXML files, you may need to set a music21 `musicxmlPath` preference in Environment (see :ref:`environment`). Once the MusicXML file has been opened, the following output (excerpted) will be displayed. 

>>> sBach.show()   # doctest: +SKIP

.. image:: images/quickStart-01.*
    :width: 600

If we do not have a MusicXML reader handy, we can always show 
the components of a Stream in a text format, with the optional 
'text' argument passed to the show method. Here is an excerpt of the output. 

>>> sBach.show('text')      # doctest: +SKIP
{0.0} <music21.stream.Part object at 0x2a85d70>
    {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.clef.TrebleClef object at 0x2ca7e50>
        {0.0} <music21.key.KeySignature of 2 sharps>
        {0.0} <music21.note.Note E>
        {0.5} <music21.note.Note F#>
    {1.0} <music21.stream.Measure 1 offset=1.0>
...


Once the score has been parsed, we can access its components, as with all Streams, in multiple ways. A Score often, but not always, includes :class:`~music21.stream.Part` objects (specialized Streams that contain Measures) and a :class:`~music21.metadata.Metadata` object.

The components of a Stream can be accessed as a list of elements accessed by index values. Index values in Python, as common in many programming languages, count from zero. Using the Python len() method, We can see that the Score as six components, index numbers 0 through 4. 

>>> len(sBach)
6
>>> sBach[0]
<music21.metadata.Metadata object at ...>
>>> sBach[1]
<music21.stream.Part Soprano>

Components of a Stream subclass, filtered by class type, are made available through property names. For example, all of the Part objects of this Score can be accessed with the :attr:`~music21.stream.Score.parts` property.

>>> len(sBach.parts)
4

We can view one of these Parts by accessing the appropriate component and calling the show() method.

>>> sBach.parts[0].show()  # doctest: +SKIP

.. image:: images/quickStart-02.*
    :width: 600


Again, we can view the components of the Part with the 'text' option for the show() method:

>>> sBach[0].show('text')  # doctest: +SKIP
{0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
{0.0} <music21.stream.Measure 0 offset=0.0>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.clef.TrebleClef object at 0x18e9310>
    {0.0} <music21.key.KeySignature of 2 sharps>
    {0.0} <music21.note.Note E>
    {0.5} <music21.note.Note F#>
{4.0} <music21.stream.Measure 1 offset=4.0>
...

Parts contain numerous components, including :class:`~music21.instrument.Instrument` objects. We can access the components of a Part by index, or directly access Measures from within a Part by using the :meth:`~music21.stream.Stream.measures` method. In the following example, measures 2 through 4 are extracted from the Part as a new Stream (called select) and displayed with the show() method. 

>>> select = sBach.parts[0].measures(2,4)
>>> select.show()  # doctest: +SKIP

.. image:: images/quickStart-03.*
    :width: 600

Measures contain numerous components, including :class:`~music21.clef.Clef`, 
:class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`, 
:class:`~music21.note.Note`, and other objects. 
We can access the Notes of a Measure directly with the 
:attr:`~music21.stream.Stream.notes` property. This property returns a Stream 
of all Notes and Chords found in a given Measure (but not Rests). Like all 
Streams, the components can be accessed by index values starting from zero. 
To view the first note of the second measure (stored in the Stream select), 
we can do the following. 

>>> select[0].notes[0].show()  # doctest: +SKIP

.. image:: images/quickStart-04.*
    :width: 600




Examining a Score by Part Id
---------------------------------------

Alternatively, we can access components of a Stream by `id`, or string identifiers. Streams can get components by `id` by using the :meth:`~music21.stream.Stream.getElementById` method. For example, we can first look at all `id` attributes of all Score elements, and then select one. 

>>> [part.id for part in sBach.parts]
[u'Soprano', u'Alto', u'Tenor', u'Bass']
>>> sBach.getElementById('Soprano')
<music21.stream.Part Soprano>




Creating Notes, Measures, Parts, and Scores
-------------------------------------------

We can create notes and measures from scratch using music21. Nearly every common music component has a Class that does what you expect (and a lot more). 

If we wanted to re-create a few measures form a popular counterpoint text, we can create Notes and add them to Measures. We can then add Measures to Parts, and then Parts to Scores. At each step along, we can call the show() method to check our progress. In the first stage, we will create the bottom Part, and do this explicitly, one object at a time.

>>> from music21 import *
>>> n1 = note.Note('e4')
>>> n1.duration.type = 'whole'
>>> n2 = note.Note('d4')
>>> n2.duration.type = 'whole'
>>> m1 = stream.Measure()
>>> m2 = stream.Measure()
>>> m1.append(n1)
>>> m2.append(n2)
>>> partLower = stream.Part()
>>> partLower.append(m1)
>>> partLower.append(m2)
>>> partLower.show()  # doctest: +SKIP

.. image:: images/quickStart-05.*
    :width: 600

We might automate this procedure by using Python's loop control structure and nested data structure of lists within lists. We can store the desired pitches and duration in a list, grouped by measure, and then iterate through them to create Measures and Notes.

>>> data1 = [('g4', 'quarter'), ('a4', 'quarter'), ('b4', 'quarter'), ('c#5', 'quarter')]
>>> data2 = [('d5', 'whole')]
>>> data = [data1, data2]
>>> partUpper = stream.Part()
>>> for mData in data:
...     m = stream.Measure()
...     for pitchName, durType in mData:
...         n = note.Note(pitchName)
...         n.duration.type = durType
...         m.append(n)
...     partUpper.append(m)
... 
>>> partUpper.show()  # doctest: +SKIP

.. image:: images/quickStart-06.*
    :width: 600

Finally, we can add both Part objects to a Score object. To display both parts simultaneously, we need to use the :meth:`~music21.stream.Stream.insert` method, adding each Part at the 0 position of the Score.

>>> sCadence = stream.Score()
>>> sCadence.insert(0, partUpper)
>>> sCadence.insert(0, partLower)
>>> sCadence.show()  # doctest: +SKIP

.. image:: images/quickStart-07.*
    :width: 600



Next Steps
-----------------------------

The following chapters provide introductions to key components of music21. Proceeding through :ref:`usersGuide_02_notes`, :ref:`overviewStreams`, :ref:`overviewFormats`, and :ref:`overviewPostTonal` provide an excellent introduction to the music21 toolkit.
