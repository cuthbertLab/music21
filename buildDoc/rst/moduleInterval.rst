.. _moduleInterval:

music21.interval
================



Interval.py is a module for creating and manipulating interval objects.
Included classes are Interval, DiatonicInterval, GenericInterval, and ChromaticInterval.
There are also a number of useful lists included in the module.

Function convertDiatonicNumberToStep()
--------------------------------------

Utility conversion; does not process internals returns a tuple of Step and Octave 

>>> convertDiatonicNumberToStep(15)
('C', 2) 
>>> convertDiatonicNumberToStep(23)
('D', 3) 

Function convertStaffDistanceToInterval()
-----------------------------------------

convertStaffDistanceToInterval(staffDistance) -> intervalDistance Returns the interval number from the given staff distance. 

Function generateChromatic()
----------------------------

generateChromatic(Note, Note) -> ChromaticInterval Generates a ChromaticInterval from the two given notes. 

Function generateDiatonic()
---------------------------

generateDiatonic(GenericInterval, ChromaticInterval) -> DiatonicInterval Generates a DiatonicInterval from the given Generic and Chromatic intervals. 

Function generateGeneric()
--------------------------

generateGeneric(Note, Note) -> GenericInterval Generates a GenericInterval from the two given notes. 

>>> from music21 import note
>>> aNote = note.Note('c4')
>>> bNote = note.Note('g5')
>>> aInterval = generateGeneric(aNote, bNote)
>>> aInterval
<music21.interval.GenericInterval 12> 



Function generateInterval()
---------------------------

generateInterval(Note [,Note]) -> Interval Generates an interval from note1 to a generic note, or from note1 to note2.  The generic, chromatic, and diatonic parts of the interval are also generated. 

>>> from music21 import note
>>> aNote = note.Note('c4')
>>> bNote = note.Note('g5')
>>> aInterval = generateInterval(aNote, bNote)
>>> aInterval
<music21.interval.Interval P12> 



Function generateIntervalFromString()
-------------------------------------

generateIntervalFromString(string) -> Interval Generates an interval object based on the given string, such as "P5", "m3", "A2". 

>>> aInterval = generateIntervalFromString('P5')
>>> aInterval
<music21.interval.Interval P5> 
>>> aInterval = generateIntervalFromString('m3')
>>> aInterval
<music21.interval.Interval m3> 



Function generateNote()
-----------------------


Function generatePitch()
------------------------

generatePitch(Pitch1 (or Note1), Interval1) -> Pitch Generates a Pitch object at the specified interval from the specified Pitch. 

>>> from music21 import pitch
>>> aPitch = pitch.Pitch('C4')
>>> aInterval = generateIntervalFromString('P5')
>>> bPitch = generatePitch(aPitch, aInterval)
>>> bPitch
G4 
>>> bInterval = generateIntervalFromString('P-5')
>>> cPitch = generatePitch(aPitch, bInterval)
>>> cPitch
F3 

Function getAbsoluteHigherNote()
--------------------------------

Given two notes, returns the higher note based on actual pitch. If both pitches are the same, returns the first note given. 

Function getAbsoluteLowerNote()
-------------------------------

Given two notes, returns the lower note based on actual pitch. If both pitches are the same, returns the first note given. 

Function getSpecifier()
-----------------------

getSpecifier(GenericInterval, ChromaticInterval) -> specifier Returns the specifier (i.e. MAJOR, MINOR, etc...) of the diatonic interval defined by the given Generic and Chromatic intervals. 



Function getWrittenHigherNote()
-------------------------------

Given two notes, returns the higher note based on diatonic note numbers. Returns the note higher in pitch if the diatonic number is the same, or the first note if pitch is also the same. 

>>> from music21 import pitch
>>> cis = pitch.Pitch("C#")
>>> deses = pitch.Pitch("D--")
>>> higher = getWrittenHigherNote(cis, deses)
>>> higher is deses
True 

Function getWrittenLowerNote()
------------------------------

Given two notes, returns the lower note based on diatonic note number. Returns the note lower in pitch if the diatonic number is the same, or the first note if pitch is also the same. 

Class ChromaticInterval
-----------------------

Inherits from: base.Music21Object, object

Chromatic interval class -- thinks of everything in semitones chromInt = chromaticInterval (-14) attributes: semitones     # -14 undirected    # 14 mod12         # 10 intervalClass #  2 cents         # -1400 

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Class DiatonicInterval
----------------------

Inherits from: base.Music21Object, object


Attributes
~~~~~~~~~~

**contexts**

**groups**

**id**

**locations**

**name**

**specifier**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Class GenericInterval
---------------------

Inherits from: base.Music21Object, object

A generic interval is an interval such as Third, Seventh, Octave, Tenth. Constructor takes an int specifying the interval and direction: staffDistance: the number of lines or spaces apart; E.g. C4 to C4 = 0;  C4 to D4 = 1;  C4 to B3 = -1 

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**


Locally Defined

**complement()**

    generates a new GenericInterval object where descending 3rds are 6ths, etc. 

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Class Interval
--------------

Inherits from: base.Music21Object, object

requires either (1) a string ("P5" etc.) or (2) named arguments: (2a) either both of diatonic  = DiatonicInterval object chromatic = ChromaticInterval object (2b) or both of note1     = Pitch (or Note) object note2     = Pitch (or Note) object in which case it figures out the diatonic and chromatic intervals itself 

>>> from music21 import note
>>> n1 = note.Note('c3')
>>> n2 = note.Note('c5')
>>> a = Interval(note1=n1, note2=n2)
>>> a
<music21.interval.Interval P15> 

Attributes
~~~~~~~~~~

**contexts**

**groups**

**id**

**locations**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**


Locally Defined

**reinit()**

    Reinitialize the internal interval objects in case something has changed.  Called also during __init__ 

**note2()**


**note1()**


**getComplement()**


**generic()**


**direction()**


**diatonicType()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**diatonic()**


**chromatic()**


Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

**complement**



