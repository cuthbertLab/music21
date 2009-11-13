music21.pitch
=============



Classes and functions for creating and manipulating pitches, pitch-space, and accidentals.
Used extensively by note.py

Class Accidental
----------------

Accidental class. 

Public Attributes
~~~~~~~~~~~~~~~~~

+ alter
+ modifier
+ name

Public Methods
~~~~~~~~~~~~~~

**contexts()**

    No documentation.

**copy()**

    Return a shallow copy, or a linked reference to the source. 

**deepcopy()**

    Return a depp copy of an object with no reference to the source. 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> n.offset = duration.Duration("quarter")
    >>> n.groups.append("flute")
    >>> n.groups
    ['flute'] 
    >>> b = n.deepcopy()
    >>> b.offset = duration.Duration("half")
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

    No documentation.

**isClass()**

    returns bool depending on if the object is a particular class or not same as isinstance here, but different for Elements, where it checks to see if the embedded object is of a certain class.  Use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**lily()**

    No documentation.

**offset()**

    No documentation.

**parent()**

    No documentation.

**priority()**

    No documentation.

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

    No documentation.

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getLily()**

    No documentation.

**_getOffset()**

    No documentation.

**_getParent()**

    No documentation.

**_getPriority()**

    No documentation.

**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**

    No documentation.

**_parent()**

    No documentation.

**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**_setDuration()**

    Set the offset as a quarterNote length 

**_setLily()**

    No documentation.

**_setOffset()**

    Set the offset as a quarterNote length (N.B. offsets are quarterNote lengths, not Duration objects...) 

    >>> import note
    >>> import duration
    >>> a = Element(note.Note('A#'))
    >>> a.offset = 23.0
    >>> a.offset
    23.0 
    >>> a.offset = duration.Duration("whole")
    >>> a.offset
    4.0 

**_setParent()**

    No documentation.

**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 


Class AccidentalException
-------------------------

No documentation.

Public Methods
~~~~~~~~~~~~~~

**args()**

    No documentation.

**message()**

    No documentation.


Class Pitch
-----------

No documentation.

Public Methods
~~~~~~~~~~~~~~

**accidental()**

    

    >>> a = Pitch('D-2')
    >>> a.accidental.alter
    -1.0 

**contexts()**

    No documentation.

**copy()**

    Return a shallow copy, or a linked reference to the source. 

**deepcopy()**

    Return a depp copy of an object with no reference to the source. 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> n.offset = duration.Duration("quarter")
    >>> n.groups.append("flute")
    >>> n.groups
    ['flute'] 
    >>> b = n.deepcopy()
    >>> b.offset = duration.Duration("half")
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

    No documentation.

**implicitOctave()**

    returns the octave of the note, or defaultOctave if octave was never set 

**isClass()**

    returns bool depending on if the object is a particular class or not same as isinstance here, but different for Elements, where it checks to see if the embedded object is of a certain class.  Use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

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

**offset()**

    No documentation.

**parent()**

    No documentation.

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

**priority()**

    No documentation.

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

    No documentation.

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

    No documentation.

**_getImplicitOctave()**

    No documentation.

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

**_getOffset()**

    No documentation.

**_getParent()**

    No documentation.

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

**_getPriority()**

    No documentation.

**_getPs()**

    No documentation.

**_getStep()**

    

    >>> a = Pitch('C#3')
    >>> a._getStep()
    'C' 

**_getfreq440()**

    

    >>> a = Pitch('A4')
    >>> a.freq440
    440.0 

**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**

    No documentation.

**_parent()**

    No documentation.

**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

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

    No documentation.

**_setMusicXML()**

    

    

**_setName()**

    Set name, which may be provided with or without octave values. C4 or D-3 are both accepted. 

**_setOctave()**

    No documentation.

**_setOffset()**

    Set the offset as a quarterNote length (N.B. offsets are quarterNote lengths, not Duration objects...) 

    >>> import note
    >>> import duration
    >>> a = Element(note.Note('A#'))
    >>> a.offset = 23.0
    >>> a.offset
    23.0 
    >>> a.offset = duration.Duration("whole")
    >>> a.offset
    4.0 

**_setParent()**

    No documentation.

**_setPitchClass()**

    No documentation.

**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 

**_setPs()**

    No documentation.

**_setStep()**

    This does not change octave or accidental, only step 

**_setfreq440()**

    No documentation.

**_updatePitchSpace()**

    recalculates the pitchSpace number (called when self.step, self.octave or self.accidental are changed. 


Class PitchException
--------------------

No documentation.

Public Methods
~~~~~~~~~~~~~~

**args()**

    No documentation.

**message()**

    No documentation.


Class Test
----------

No documentation.

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _testMethodDoc
+ _testMethodName

Public Methods
~~~~~~~~~~~~~~

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

    No documentation.

**debug()**

    Run the test without collecting errors in a TestResult 

**defaultTestResult()**

    No documentation.

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

    No documentation.

**run()**

    No documentation.

**runTest()**

    No documentation.

**setUp()**

    Hook method for setting up the test fixture before exercising it. 

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testOctave()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


Class TestExternal
------------------

No documentation.

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _testMethodDoc
+ _testMethodName

Public Methods
~~~~~~~~~~~~~~

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

    No documentation.

**debug()**

    Run the test without collecting errors in a TestResult 

**defaultTestResult()**

    No documentation.

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

    No documentation.

**run()**

    No documentation.

**runTest()**

    No documentation.

**setUp()**

    Hook method for setting up the test fixture before exercising it. 

**shortDescription()**

    Returns a one-line description of the test, or None if no description has been provided. The default implementation of this method returns the first line of the specified test method's docstring. 

**tearDown()**

    Hook method for deconstructing the test fixture after testing it. 

**testBasic()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


