.. _modulePitch:

music21.pitch
=============



Classes and functions for creating and manipulating pitches, pitch-space, and accidentals.
Used extensively by note.py

Function convertFqToPs()
------------------------

Utility conversion; does not process internals. Assumes A4 = 440 Hz 

>>> convertFqToPs(440)
69.0 
>>> convertFqToPs(261.62556530059862)
60.0 

Function convertPsToFq()
------------------------

Utility conversion; does not process internals. NOT CURRENTLY USED: since freq440 had its own conversion methods, and wanted the numbers to be EXACTLY the same either way Assumes A4 = 440 Hz 

>>> convertPsToFq(69)
440.0 
>>> convertPsToFq(60)
261.62556530059862 
>>> convertPsToFq(2)
9.1770239974189884 
>>> convertPsToFq(135)
19912.126958213179 

Function convertPsToOct()
-------------------------

Utility conversion; does not process internals. Assume C4 middle C, so 60 returns 4 

>>> [convertPsToOct(59), convertPsToOct(60), convertPsToOct(61)]
[3, 4, 4] 
>>> [convertPsToOct(12), convertPsToOct(0), convertPsToOct(-12)]
[0, -1, -2] 
>>> convertPsToOct(135)
10 

Function convertPsToStep()
--------------------------

Utility conversion; does not process internals. Takes in a midiNote number (Assume C4 middle C, so 60 returns 4) Returns a tuple of Step name and either a natural or a sharp 

>>> convertPsToStep(60)
('C', <accidental natural>) 
>>> convertPsToStep(66)
('F', <accidental sharp>) 
>>> convertPsToStep(67)
('G', <accidental natural>) 
>>> convertPsToStep(68)
('G', <accidental sharp>) 
>>> convertPsToStep(-2)
('A', <accidental sharp>) 
>>> convertPsToStep(60.5)
('C', <accidental half-sharp>) 
>>> convertPsToStep(61.5)
('C', <accidental one-and-a-half-sharp>) 
>>> convertPsToStep(62)
('D', <accidental natural>) 
>>> convertPsToStep(62.5)
('D', <accidental half-sharp>) 
>>> convertPsToStep(135)
('D', <accidental sharp>) 

Function convertStepToPs()
--------------------------

Utility conversion; does not process internals. 

>>> convertStepToPs('c', 4, 1)
61 
>>> convertStepToPs('d', 2, -2)
36 
>>> convertStepToPs('b', 3, 3)
62 

Class Accidental
----------------

Inherits from: base.Music21Object (of module :ref:`moduleBase`), object

Accidental class. 

Attributes
~~~~~~~~~~

**alter**

**modifier**

**name**

Properties
~~~~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **priority**, **parent**, **offset**, **duration**


Locally Defined:

**mx**

    From music21 to MusicXML 

    >>> a = Accidental()
    >>> a.set('half-sharp')
    >>> a.alter == .5
    True 
    >>> mxAccidental = a.mx
    >>> mxAccidental.get('content')
    'quarter-sharp' 

**lily**


Methods
~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **write()**, **show()**, **searchParent()**, **isClass()**, **id()**, **getOffsetBySite()**, **contexts()**, **addLocationAndParent()**


Locally Defined:

**set()**

    Provide a value to the Accidental. Strings values, numbers, and Lilypond Abbreviations are all accepted. 

    >>> a = Accidental()
    >>> a.set('sharp')
    >>> a.alter == 1
    True 
    >>> a = Accidental()
    >>> a.set(2)
    >>> a.modifier == "##"
    True 
    >>> a = Accidental()
    >>> a.set(2.0)
    >>> a.modifier == "##"
    True 
    >>> a = Accidental('--')
    >>> a.alter
    -2.0 


Class Pitch
-----------

Inherits from: base.Music21Object (of module :ref:`moduleBase`), object


Attributes
~~~~~~~~~~

**contexts**

**defaultOctave**

**groups**

**id**

**locations**

Properties
~~~~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **priority**, **parent**, **offset**, **duration**


Locally Defined:

**step**

    

    >>> a = Pitch('C#3')
    >>> a._getStep()
    'C' 

**ps**

    pitchSpace attribute 

**pitchClass**

    

    >>> a = Pitch('a3')
    >>> a._getPitchClass()
    9 
    >>> dis = Pitch('d3')
    >>> dis.pitchClass
    2 
    >>> dis.accidental = Accidental("#")
    >>> dis.pitchClass
    3 
    >>> dis.pitchClass = 11
    >>> dis.pitchClass
    11 
    >>> dis.name
    'B' 

**octave**

    returns or sets the octave of the note.  Setting the octave updates the pitchSpace attribute. 

    >>> a = Pitch('g')
    >>> a.octave is None
    True 
    >>> a.implicitOctave
    4 
    >>> a.ps  ## will use implicitOctave
    67 
    >>> a.name
    'G' 
    >>> a.octave = 14
    >>> a.implicitOctave
    14 
    >>> a.name
    'G' 
    >>> a.ps
    187 

**nameWithOctave**

    Returns pitch name with octave Perhaps better default action for getName 

    >>> a = Pitch('G#4')
    >>> a.nameWithOctave
    'G#4' 

**name**

    Name presently returns pitch name and accidental without octave. Perhaps better named getNameClass 

    >>> a = Pitch('G#')
    >>> a.name
    'G#' 

**mx**

    returns a musicxml.Note() object 

    >>> a = Pitch('g#4')
    >>> c = a.mx
    >>> c.get('pitch').get('step')
    'G' 

**musicxml**

    Provide a complete MusicXM: representation. Presently, this is based on 

**midi**

    midi is ps (pitchSpace) as a rounded int; ps can accomodate floats 

**implicitOctave**

    returns the octave of the note, or defaultOctave if octave was never set 

**frequency**

    The frequency property gets or sets the frequency of the pitch in hertz. If the frequency has not been overridden, then it is computed based on A440Hz and equal temperament 

**freq440**

    

    >>> a = Pitch('A4')
    >>> a.freq440
    440.0 

**diatonicNoteNum**

    Read-only property. Returns an int that uniquely identifies the note, ignoring accidentals. The number returned is the diatonic interval above C0 (the lowest C on a Boesendorfer Imperial Grand), so G0 = 5, C1 = 8, etc. Numbers can be negative for very low notes. C4 (middleC) = 29, C#4 = 29, C##4 = 29, D-4 = 30, D4 = 30, etc. 

    >>> c = Pitch('c4')
    >>> c.diatonicNoteNum
    29 
    >>> c = Pitch('c#4')
    >>> c.diatonicNoteNum
    29 
    >>> d = Pitch('d--4')
    >>> d.accidental.name
    'double-flat' 
    >>> d.diatonicNoteNum
    30 
    >>> b = Pitch()
    >>> b.step = "B"
    >>> b.octave = -1
    >>> b.diatonicNoteNum
    0 
    >>> c = Pitch("C")
    >>> c.diatonicNoteNum  #implicitOctave
    29 

**accidental**

    

    >>> a = Pitch('D-2')
    >>> a.accidental.alter
    -1.0 

Methods
~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **write()**, **show()**, **searchParent()**, **isClass()**, **id()**, **getOffsetBySite()**, **contexts()**, **addLocationAndParent()**


