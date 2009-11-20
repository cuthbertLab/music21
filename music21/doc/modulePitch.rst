music21.pitch
=============



Classes and functions for creating and manipulating pitches, pitch-space, and accidentals.
Used extensively by note.py

Function convertDiatonicNumberToStep()
--------------------------------------

Utility conversion; does not process internals returns a tuple of Step and Octave 

>>> convertDiatonicNumberToStep(15)
('C', 2) 
>>> convertDiatonicNumberToStep(23)
('D', 3) 

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

Function convertPsToOct()
-------------------------

Utility conversion; does not process internals. Assume C4 middle C, so 60 returns 4 

>>> [convertPsToOct(59), convertPsToOct(60), convertPsToOct(61)]
[3, 4, 4] 
>>> [convertPsToOct(12), convertPsToOct(0), convertPsToOct(-12)]
[0, -1, -2] 

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

Accidental class. 

Attributes
~~~~~~~~~~

+ alter
+ modifier
+ name

Methods
~~~~~~~

**contexts()**


**copy()**

    Return a shallow copy, or a linked reference to the source. 

**deepcopy()**

    Return a deep copy of an object with no reference to the source. The parent is not deep copied! 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> n.offset = 1.0 #duration.Duration("quarter")
    >>> n.groups.append("flute")
    >>> n.groups
    ['flute'] 
    >>> b = n.deepcopy()
    >>> b.offset = 2.0 #duration.Duration("half")
    >>> n is b
    False 
    >>> n.accidental = "-"
    >>> b.name
    'A' 
    >>> n.offset
    1.0 
    >>> b.offset
    2.0 
    >>> n.groups[0] = "bassoon"
    >>> ("flute" in n.groups, "flute" in b.groups)
    (False, True) 

**duration()**

    Gets the DurationObject of the object or None 

    

**id()**


**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**lily()**


**parent()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

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

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getLily()**


**_getParent()**


**_overriddenLily()**


**_parent()**


**_setDuration()**

    Set the offset as a quarterNote length 

**_setLily()**


**_setParent()**



Class AccidentalException
-------------------------


Methods
~~~~~~~

**args()**


**message()**



Class Pitch
-----------


Methods
~~~~~~~

**accidental()**

    

    >>> a = Pitch('D-2')
    >>> a.accidental.alter
    -1.0 

**contexts()**


**copy()**

    Return a shallow copy, or a linked reference to the source. 

**deepcopy()**

    Return a deep copy of an object with no reference to the source. The parent is not deep copied! 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> n.offset = 1.0 #duration.Duration("quarter")
    >>> n.groups.append("flute")
    >>> n.groups
    ['flute'] 
    >>> b = n.deepcopy()
    >>> b.offset = 2.0 #duration.Duration("half")
    >>> n is b
    False 
    >>> n.accidental = "-"
    >>> b.name
    'A' 
    >>> n.offset
    1.0 
    >>> b.offset
    2.0 
    >>> n.groups[0] = "bassoon"
    >>> ("flute" in n.groups, "flute" in b.groups)
    (False, True) 

**diatonicNoteNum()**

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

**duration()**

    Gets the DurationObject of the object or None 

    

**freq440()**

    

    >>> a = Pitch('A4')
    >>> a.freq440
    440.0 

**frequency()**

    The frequency property gets or sets the frequency of the pitch in hertz. If the frequency has not been overridden, then it is computed based on A440Hz and equal temperament 

**id()**


**implicitOctave()**

    returns the octave of the note, or defaultOctave if octave was never set 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**midi()**

    midi is ps (pitchSpace) as a rounded int; ps can accomodate floats 

**musicxml()**

    Provide a complete MusicXM: representation. Presently, this is based on 

**mx()**

    returns a musicxml.Note() object 

    >>> a = Pitch('g#4')
    >>> c = a.mx
    >>> c.get('pitch').get('step')
    'G' 

**name()**

    Name presently returns pitch name and accidental without octave. Perhaps better named getNameClass 

    >>> a = Pitch('G#')
    >>> a.name
    'G#' 

**nameWithOctave()**

    Returns pitch name with octave Perhaps better default action for getName 

    >>> a = Pitch('G#4')
    >>> a.nameWithOctave
    'G#4' 

**octave()**

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

**parent()**


**pitchClass()**

    

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

**ps()**

    pitchSpace attribute 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**step()**

    

    >>> a = Pitch('C#3')
    >>> a._getStep()
    'C' 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getAccidental()**

    

    >>> a = Pitch('D-2')
    >>> a.accidental.alter
    -1.0 

**_getDiatonicNoteNum()**

    Returns an int that uniquely identifies the note, ignoring accidentals. The number returned is the diatonic interval above C0 (the lowest C on a Boesendorfer Imperial Grand), so G0 = 5, C1 = 8, etc. Numbers can be negative for very low notes. C4 (middleC) = 29, C#4 = 29, C##4 = 29, D-4 = 30, D4 = 30, etc. 

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

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getFrequency()**


**_getImplicitOctave()**


**_getMX()**

    returns a musicxml.Note() object 

    >>> a = Pitch('g#4')
    >>> c = a.mx
    >>> c.get('pitch').get('step')
    'G' 

**_getMidi()**

    

    >>> a = Pitch('C3')
    >>> a.midi
    48 
    >>> a = Pitch('C#2')
    >>> a.midi
    37 
    >>> a = Pitch('B4')
    >>> a.midi
    71 

**_getMusicXML()**

    Provide a complete MusicXM: representation. Presently, this is based on 

**_getName()**

    Name presently returns pitch name and accidental without octave. Perhaps better named getNameClass 

    >>> a = Pitch('G#')
    >>> a.name
    'G#' 

**_getNameWithOctave()**

    Returns pitch name with octave Perhaps better default action for getName 

    >>> a = Pitch('G#4')
    >>> a.nameWithOctave
    'G#4' 

**_getOctave()**

    This is _octave, not implicitOctave 

**_getParent()**


**_getPitchClass()**

    

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

**_getPs()**


**_getStep()**

    

    >>> a = Pitch('C#3')
    >>> a._getStep()
    'C' 

**_getfreq440()**

    

    >>> a = Pitch('A4')
    >>> a.freq440
    440.0 

**_overriddenLily()**


**_parent()**


**_setAccidental()**

    

    >>> a = Pitch('E')
    >>> a.ps  # here this is an int
    64 
    >>> a.accidental = '#'
    >>> a.ps  # here this is a float
    65.0 

**_setDuration()**

    Set the offset as a quarterNote length 

**_setFrequency()**

    

    >>> a = Pitch()
    >>> a.frequency = 440.0
    >>> a.frequency
    440.0 
    >>> a.name
    'A' 
    >>> a.octave
    4 

**_setMX()**

    Given a MusicXML Note object, set this Ptich object to its values. 

    >>> b = musicxml.Pitch()
    >>> b.set('octave', 3)
    >>> b.set('step', 'E')
    >>> b.set('alter', -1)
    >>> c = musicxml.Note()
    >>> c.set('pitch', b)
    >>> a = Pitch('g#4')
    >>> a.mx = c
    >>> print a
    E-3 

**_setMidi()**


**_setMusicXML()**

    

    

**_setName()**

    Set name, which may be provided with or without octave values. C4 or D-3 are both accepted. 

**_setOctave()**


**_setParent()**


**_setPitchClass()**


**_setPs()**


**_setStep()**

    This does not change octave or accidental, only step 

**_setfreq440()**


**_updatePitchSpace()**

    recalculates the pitchSpace number (called when self.step, self.octave or self.accidental are changed. 


Class PitchException
--------------------


Methods
~~~~~~~

**args()**


**message()**



Class TestExternal
------------------


Methods
~~~~~~~

**assertAlmostEqual()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertAlmostEquals()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertEqual()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**assertEquals()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**assertFalse()**

    Fail the test if the expression is true. 

**assertNotAlmostEqual()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertNotAlmostEquals()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**assertNotEqual()**

    Fail if the two objects are equal as determined by the '==' operator. 

**assertNotEquals()**

    Fail if the two objects are equal as determined by the '==' operator. 

**assertRaises()**

    Fail unless an exception of class excClass is thrown by callableObj when invoked with arguments args and keyword arguments kwargs. If a different type of exception is thrown, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception. 

**assertTrue()**

    Fail the test unless the expression is true. 

**assert_()**

    Fail the test unless the expression is true. 

**countTestCases()**


**debug()**

    Run the test without collecting errors in a TestResult 

**defaultTestResult()**


**fail()**

    Fail immediately, with the given message. 

**failIf()**

    Fail the test if the expression is true. 

**failIfAlmostEqual()**

    Fail if the two objects are equal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**failIfEqual()**

    Fail if the two objects are equal as determined by the '==' operator. 

**failUnless()**

    Fail the test unless the expression is true. 

**failUnlessAlmostEqual()**

    Fail if the two objects are unequal as determined by their difference rounded to the given number of decimal places (default 7) and comparing to zero. Note that decimal places (from zero) are usually not the same as significant digits (measured from the most signficant digit). 

**failUnlessEqual()**

    Fail if the two objects are unequal as determined by the '==' operator. 

**failUnlessRaises()**

    Fail unless an exception of class excClass is thrown by callableObj when invoked with arguments args and keyword arguments kwargs. If a different type of exception is thrown, it will not be caught, and the test case will be deemed to have suffered an error, exactly as for an unexpected exception. 

**failureException()**

    Assertion failed. 

**id()**


**run()**


**runTest()**


**setUp()**

    Hook method for setting up the test fixture before exercising it. 

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testSingle()**


Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


