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


Examining a Score
-----------------------

Once music21 is installed, opening and examing a score and it elements is a good first step. Music21 comes with a corpus, a large collection freely distributable music stored in the MusicXML and humdrum formats. These files can be found in the music21/corpus directory. However, tools are provided for easy, direct access.

To import, or parse, a score stored in the corpus, use the :mod:`music21.corpus` module. We imported this above, but lets do it again and use the `parseWork` method to get some some music parsed.


    >>> from music21 import corpus
    >>> aScore = corpus.parseWork('bach/bwv7.7')




View Some Notation
-----------------------

After parsing, manipulationg, or creating music21 objects, viewing them as notation is 
a common way to share and evaluate what you have done.



