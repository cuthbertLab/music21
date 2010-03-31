.. _quickStart:


Quick Start: Getting Started with music21
=============================================

Here are some quick steps to get up and running quickly with music21. 





Download and Install
-----------------------


First, download and install music21. If you have installed other Python packages, do what you normally do (include using setuptools/easy_install or pip). 

Otherwise, please read the full instructions: :ref:`install`.



Starting Python and Importing Modules
-------------------------------------

Like all Python functionality, music21 can be run from a Python script (a .py file) or interactively from the Python intepreter. The Python interpreter is designated with the command prompt `>>>`.

On UNIX-based operating systems with a command line prompt (Terminal.app on Mac OS X), entering `python` will start the Python interpreter.

On Windows, starting the Python.exe applicatoin or IDLE.py will provide an interactive Python session.

Once you start Python, you can check to see if your music21 installation is correctly configured by trying to import a music21 module. A module is a Python file that offers reusuable resources. These are all found inside the music21 package, so often we will import a module from music21. To import the corpus module from music21, enter the following command.

    >>> from music21 import corpus
    >>>

Assuming this works, your music21 installation is complete and you can move. However, you may get the following error:

    >>> from music21 import corpus
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ImportError: No module named music21
    >>> 
    
If this happens, Python is not able to find the music21 package. Return and review the instructions in :ref:`install` or contact the music21 group for help:

http://groups.google.com/group/music21list


Examining a Score by Index and Measure
---------------------------------------

Once music21 is installed, opening and examing a score and it elements is a good first step. Music21 comes with a corpus, a large collection freely distributable music stored in the MusicXML and humdrum formats. These files can be found in the music21/corpus directory. However, tools are provided for easy, direct access.

To import, or parse, a score stored in the corpus, use the :mod:`music21.corpus` module. We imported this above, but lets do it again and use the `parseWork` method to get some some music parsed. This translates the file (a MusicXML or humdrum file) into music21 objects.

    >>> from music21 import corpus
    >>> aScore = corpus.parseWork('bach/bwv7.7')

The score is returned as music21 :class:`~music21.stream.Score`, which is as type (subclass) of music21 :class:`~music21.stream.Stream`. 

Once the score is parsed, we can view, transform, and manipulate its components in a variety of ways. If we want to output and view the entire score, we can use the :meth:`~music21.stream.Stream.show` method. Without any arguments, this method does two things. First, it writes a MusicXML file of the current Stream as temporary file or in the user-specified scratch directory. (This directory can be defined as part of the user's environment settings. See :ref:`environment` for complete details.) Second, it attempts to open this file with a user-specied helper application. Assuming you have an appropriate MusicXML reader (see :ref:`install`), and have set it to handle MusicXML files (see :ref:`environment`), the following output (excerpted) will be displayed. 


    >>> aScore.show()

.. image:: images/quickStart-01.*
    :width: 500

If we do not have a MusicXML reader handy, we can always show the components of a Stream in a text format, with the optional 'text' argument passed to the show method. Here is an excerpt of the output. 

    >>> aScore.show('text')
    {0.0} <music21.stream.Part object at 0x1b67cb0>
        {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.clef.TrebleClef object at 0x18e9310>
            {0.0} <music21.key.KeySignature of 2 sharps>
            {0.0} <music21.note.Note E>
            {0.5} <music21.note.Note F#>
        {4.0} <music21.stream.Measure 1 offset=4.0>
    ...


Once the score has been parsed, we can access its components in various ways. All Streams present their components in multiple ways. The components of a Score are usually :class:`~music21.stream.Part` objects, or specialized Streams that contain Measures. 

The components of a Stream can be accessed as a list of elements accessed by index values. Index values in Python, as common in many programming languages, count from zero. Using the Python len() method, We can see that the Score as four components, index numbers 0 through 3. 

    >>> len(aScore)
    4
    >>> aScore[0]
    <music21.stream.Part object at 0x1b67cb0>
    >>> aScore[1]
    <music21.stream.Part object at 0x19b40b0>

We can view one of these Parts by accessing the appropriate component and calling the show() method.

    >>> aScore[0].show()

.. image:: images/quickStart-02.*
    :width: 500


Again, we can view the componetns of the Part with the 'text' option for the show() method:

    >>> aScore[0].show('text')
    {0.0} <music21.instrument.Instrument P1: Soprano: Instrument 1>
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.clef.TrebleClef object at 0x18e9310>
        {0.0} <music21.key.KeySignature of 2 sharps>
        {0.0} <music21.note.Note E>
        {0.5} <music21.note.Note F#>
    {4.0} <music21.stream.Measure 1 offset=4.0>
    ...

Parts contain numerous components, including :class:`~music21.instrument.Instrument` objects. We can access the components of a Part by index, or directly access Measures from within a Part by using the :meth:`~music21.stream.Stream.getMeasureRange` method. In the following example, measures 2 through 4 are extracted from the Part as a new Stream (called select) and displayed with the show() method. 

    >>> select = aScore[0].getMeasureRange(2,4)
    >>> select.show()

.. image:: images/quickStart-03.*
    :width: 500

Measures contain numerous components, including :class:`~music21.clef.Clef`, :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`, :class:`~music21.note.Note`, and other objects. We can access the Notes of a Measure directly with the :attr:`~music21.stream.Stream.notes` property. This property returns a Stream of all Notes found in a given Measure. Like all Streams, the components can be accessed by index values starting from zero. To view the first note of the second measure (stored in the Stream select), we can do the following. 

    >>> select[0].notes[0].show()

.. image:: images/quickStart-04.*
    :width: 500




Examining a Score by Part Id
---------------------------------------

Alternatively, we can access components of a Stream by `id`, or string identifiers. Streams can get components by `id` by using the :meth:`~music21.stream.Stream.getElementById` method. 

    >>> aScore.getElementById('Soprano')
    <music21.stream.Part object at 0x1b67cb0>




Creating Notes and Measures
----------------------------

We can create notes and measures from scratch using music21. 


