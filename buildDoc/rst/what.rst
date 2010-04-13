.. _what:


What Is Music21?
======================================

Music21 is a Python-based toolkit for computer-aided musicology. 

Applications include computational musicology, music informations, musical example extraction and generation, music notation editing and scripting, and a wide variety of approaches to composition, both algorithmic and directly specified. 

Music21, while newly created from the ground up, leverages many approaches and traditions from previous software systems. See :ref:`about` for information on the authors and the background of this project.



Finding Solutions with Small Scripts
---------------------------------------

With music21, a collection specialized objects and tools are made available inside of Python. This is a Python extension library. With a script, a short collection Python code, you can easily find and display a solution to a wide range of musicological problems.

For some examples of these scripts, see :ref:`examples`.



Getting Musical Data
-----------------------------

Music21 is specialized for working with musical data represented symbolically: most commonly, this is a musical score or notation. This data can be obtained from a wide variety of sources.

If you use Finale or Sibelius, you can easily output scores or notation from these programs as MusicXML. Music21 can then import the MusicXML data. Additionally, there exist numerous on-line repositories of MusicXML data. See :ref:`overviewFormats` for links.

There are numerous additional symbolic music representations. Presently, music21 supports Humdrum and its Kern format. MIDI and additional formats will be forthcoming.



Visualizing Musical Data
-----------------------------

Music21 provides a wide variety of tools for visualizing musical data and output. Musical notation can be output in a variety of formats, and graphics can be created of musical data or events. For some examples, see :ref:`moduleGraph`.



Authoring and Transforming Musical Data
----------------------------------------

Music21 permits easily creating and transforming musical data. Say you want to re-arrange the measures of score, transpose a part, or replace every G# with a B: all these actions can be done easily with short Python scripts.



Learning music21
-----------------------------

To learn to use music21, some familiarity with Python is needed. Python is widely regarded as one of the easiest languages to learn, has clear and concise syntax, and is often taught as a first programing language. You do not need to be a seasoned programmer, or even have complete knowledge of Python. Just a little bit of Python and you will be able to get started with music21. You might skim the following chapters of Python documentation tutorial for a bit of guidance.

Starting the Python interpreter:
http://docs.python.org/tutorial/interpreter.html

Basic Python operations:
http://docs.python.org/tutorial/introduction.html

Basic Python loops and conditional statements:
http://docs.python.org/tutorial/controlflow.html

To install music21, view :ref:`install`. With some basic Python knowledge, start with :ref:`quickStart` for a rapid introduction to music21.

The :ref:`overviewNotes`, :ref:`overviewStreams`, :ref:`overviewFormats`, and :ref:`overviewPostTonal` chapters provide surveys of important features of key components of the music21 toolkit.

The main body of the documentation, however, is the module documentation. This provides detailed documentation and examples for every object, method, and function in music21. Surveying the module documentation and the example code will demonstrate much of music21 functionality. The module documentation will also be your primary reference when writing music21 scripts.






