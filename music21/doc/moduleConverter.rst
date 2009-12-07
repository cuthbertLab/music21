music21.converter
=================



Public interface for importing file formats into music21.

Function parse()
----------------

Determine if the file is a file path or a string 

Function parseData()
--------------------


Function parseFile()
--------------------


Class Converter
---------------

Inherits from: object

Not a subclass, but a wrapper for different converter objects based on format. 

Methods
~~~~~~~


Locally Defined

**parseFile()**


**parseData()**

    need to look at data and determine if it is xml or humdrum 

Properties
~~~~~~~~~~


Locally Defined

**stream**



Class ConverterHumdrum
----------------------

Inherits from: object


Attributes
~~~~~~~~~~

**stream**

Methods
~~~~~~~


Locally Defined

**parseFile()**

    Open from file path 

**parseData()**

    Open from a string 


Class ConverterMusicXML
-----------------------

Inherits from: object


Methods
~~~~~~~


Locally Defined

**parseFile()**

    Open from file path; check to see if there is a pickled version available and up to date; if so, open that, otherwise open source. 

**parseData()**

    Open from a string 

**load()**

    Load all parts. This determines the order parts are found in the stream 

**getPartNames()**


Properties
~~~~~~~~~~


Locally Defined

**stream**



Class PickleFilter
------------------

Inherits from: object

Before opening a file path, this class can check if there is an up to date version pickled and stored in the scratch directory. If the user has not specified a scratch directory, a pickle path will not be created. 

Methods
~~~~~~~


Locally Defined

**status()**



