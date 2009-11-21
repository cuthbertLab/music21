music21.note
============



Classes and functions for creating and manipulating notes, ties, and durations.
Pitch-specific functions are in music21.pitch, but obviously are of great importance here too.

Function factory()
------------------

convenience method to get Notes 

Function noteFromDiatonicNumber()
---------------------------------


Function sendNoteInfo()
-----------------------

Debugging method to print information about a music21 note called by trecento.trecentoCadence, among other places 

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



Class Beam
----------

An object representation of a beam, where each beam objects exists for each horizontal line in a total beam structure for one note. 

Attributes
~~~~~~~~~~

+ direction
+ independentAngle
+ number
+ type

Methods
~~~~~~~

**mx()**

    Returns a Beams object 

    >>> a = Beam()
    >>> a.type = 'start'
    >>> a.number = 1
    >>> b = a.mx
    >>> b.get('charData')
    'begin' 
    >>> b.get('number')
    1 
    >>> a.type = 'partial'
    >>> a.direction = 'left'
    >>> b = a.mx
    >>> b.get('charData')
    'backward hook' 

Private Methods
~~~~~~~~~~~~~~~

**_getMX()**

    Returns a Beams object 

    >>> a = Beam()
    >>> a.type = 'start'
    >>> a.number = 1
    >>> b = a.mx
    >>> b.get('charData')
    'begin' 
    >>> b.get('number')
    1 
    >>> a.type = 'partial'
    >>> a.direction = 'left'
    >>> b = a.mx
    >>> b.get('charData')
    'backward hook' 

**_setMX()**

    given a list of mxBeam objects, set beamsList 

    >>> mxBeam = musicxmlMod.Beam()
    >>> mxBeam.set('charData', 'begin')
    >>> a = Beam()
    >>> a.mx = mxBeam
    >>> a.type
    'start' 


Class BeamException
-------------------


Methods
~~~~~~~

**args()**


**message()**



Class Beams
-----------

A group of beams applied to a single note that represents the partial beam structure of many notes beamed together. 

Attributes
~~~~~~~~~~

+ beamsList
+ feathered

Methods
~~~~~~~

**addNext()**


**fill()**

    Clear an fill the beams list as commonly needed for various durations do not set type or direction 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> len(a)
    2 
    >>> a.fill('32nd')
    >>> len(a)
    3 

**getByNumber()**

    Set an internal beam object by number, or rhythmic symbol level 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.getByNumber(2).type
    'start' 

**getNumbers()**

    Retrun a lost of all defind numbers 

    >>> a = Beams()
    >>> a.fill('32nd')
    >>> a.getNumbers()
    [1, 2, 3] 

**getTypes()**

    Retur a lost of all types 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.getTypes()
    ['start', 'start'] 

**mx()**

    Returns a list of mxBeam objects 

**setAll()**

    Convenience method to set all beam objects within Beams 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.getTypes()
    ['start', 'start'] 

    

**setByNumber()**

    Set an internal beam object by number, or rhythmic symbol level 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.setByNumber(1, 'continue')
    >>> a.beamsList[0].type
    'continue' 
    >>> a.setByNumber(2, 'stop')
    >>> a.beamsList[1].type
    'stop' 
    >>> a.setByNumber(2, 'partial-right')
    >>> a.beamsList[1].type
    'partial' 
    >>> a.beamsList[1].direction
    'right' 

Private Methods
~~~~~~~~~~~~~~~

**_getMX()**

    Returns a list of mxBeam objects 

**_setMX()**

    given a list of mxBeam objects, set beamsList 

    >>> mxBeamList = []
    >>> a = Beams()
    >>> a.mx = mxBeamList


Class EighthNote
----------------


Attributes
~~~~~~~~~~

+ articulations
+ beams
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ pitch
+ tie

Methods
~~~~~~~

**accidental()**


**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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

    see Pitch.diatonicNoteNum 

**duration()**

    Gets the DurationObject of the object or None 

    

**freq440()**


**frequency()**


**id()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lily()**

    The name of the note as it would appear in Lilypond format. 

**lyric()**


**midi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**midiNote()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**name()**


**nameWithOctave()**


**octave()**


**parent()**


**pitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**setAccidental()**


**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**step()**


**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getAccidental()**


**_getColor()**


**_getDiatonicNoteNum()**

    see Pitch.diatonicNoteNum 

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getFreq440()**


**_getFrequency()**


**_getLily()**

    The name of the note as it would appear in Lilypond format. 

**_getLyric()**


**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMidi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getName()**


**_getNameWithOctave()**


**_getOctave()**


**_getParent()**


**_getPitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_getStep()**


**_overriddenLily()**


**_parent()**


**_preDurationLily()**

    Method to return all the lilypond information that appears before the duration number. Is the same for simple and complex notes. 

**_setAccidental()**

    Adds an accidental to the Note, given as an Accidental object. Also alters the name of the note 

    >>> a = Note()
    >>> a.step = "D"
    >>> a.name
    'D' 
    >>> b = Accidental("sharp")
    >>> a.setAccidental(b)
    >>> a.name
    'D#' 

**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setFreq440()**


**_setFrequency()**


**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMX()**

    Given an mxNote, fill the necessary parameters 

**_setMidi()**


**_setMusicXML()**


**_setName()**


**_setOctave()**


**_setParent()**


**_setPitchClass()**


**_setQuarterLength()**


**_setStep()**



Class GeneralNote
-----------------

A GeneralNote object is the parent object for the Note, Rest, Unpitched, and SimpleNote, etc. objects It contains duration, notations, editorial, and tie fields. 

Attributes
~~~~~~~~~~

+ articulations
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ tie

Methods
~~~~~~~

**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**lyric()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**parent()**


**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getColor()**


**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getLyric()**


**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getParent()**


**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_overriddenLily()**


**_parent()**


**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMusicXML()**


**_setParent()**


**_setQuarterLength()**



Class HalfNote
--------------


Attributes
~~~~~~~~~~

+ articulations
+ beams
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ pitch
+ tie

Methods
~~~~~~~

**accidental()**


**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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

    see Pitch.diatonicNoteNum 

**duration()**

    Gets the DurationObject of the object or None 

    

**freq440()**


**frequency()**


**id()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lily()**

    The name of the note as it would appear in Lilypond format. 

**lyric()**


**midi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**midiNote()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**name()**


**nameWithOctave()**


**octave()**


**parent()**


**pitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**setAccidental()**


**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**step()**


**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getAccidental()**


**_getColor()**


**_getDiatonicNoteNum()**

    see Pitch.diatonicNoteNum 

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getFreq440()**


**_getFrequency()**


**_getLily()**

    The name of the note as it would appear in Lilypond format. 

**_getLyric()**


**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMidi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getName()**


**_getNameWithOctave()**


**_getOctave()**


**_getParent()**


**_getPitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_getStep()**


**_overriddenLily()**


**_parent()**


**_preDurationLily()**

    Method to return all the lilypond information that appears before the duration number. Is the same for simple and complex notes. 

**_setAccidental()**

    Adds an accidental to the Note, given as an Accidental object. Also alters the name of the note 

    >>> a = Note()
    >>> a.step = "D"
    >>> a.name
    'D' 
    >>> b = Accidental("sharp")
    >>> a.setAccidental(b)
    >>> a.name
    'D#' 

**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setFreq440()**


**_setFrequency()**


**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMX()**

    Given an mxNote, fill the necessary parameters 

**_setMidi()**


**_setMusicXML()**


**_setName()**


**_setOctave()**


**_setParent()**


**_setPitchClass()**


**_setQuarterLength()**


**_setStep()**



Class LilyString
----------------


Attributes
~~~~~~~~~~

+ value

Methods
~~~~~~~

**addMidi()**

    override this in subclasses, such as LilyScore 

**checkForMidi()**


**checkForMidiAndAdd()**


**createPDF()**


**midiWrapped()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**playMIDIfile()**


**quickHeader()**

    Returns a quick and dirty lilyPond header for the stream 

**runThroughLily()**


**savePNG()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**showImageDirect()**

    borrowed from and modified from the excellent PIL image library, but needed some changes to the NT handling 

**showPDF()**


**showPNG()**

    Take the LilyString, run it through LilyPond, and then show it as a PNG file. On Windows, the PNG file will not be deleted, so you  will need to clean out TEMP every once in a while 

**showPNGandPlayMIDI()**


**wrapForMidi()**


**wrappedValue()**

    returns a value that is wrapped with { } if it doesn't contain a score element so that it can run through lilypond 

**writeTemp()**


Private Methods
~~~~~~~~~~~~~~~

**_getWrappedValue()**

    returns a value that is wrapped with { } if it doesn't contain a score element so that it can run through lilypond 


Class Lyric
-----------


Attributes
~~~~~~~~~~

+ number
+ syllabic
+ text

Methods
~~~~~~~

**mx()**

    Returns an mxLyric 

    >>> a = Lyric()
    >>> a.text = 'hello'
    >>> mxLyric = a.mx
    >>> mxLyric.get('text')
    'hello' 

Private Methods
~~~~~~~~~~~~~~~

**_getMX()**

    Returns an mxLyric 

    >>> a = Lyric()
    >>> a.text = 'hello'
    >>> mxLyric = a.mx
    >>> mxLyric.get('text')
    'hello' 

**_setMX()**

    Given an mxLyric, fill the necessary parameters 

    >>> mxLyric = musicxml.Lyric()
    >>> mxLyric.set('text', 'hello')
    >>> a = Lyric()
    >>> a.mx = mxLyric
    >>> a.text
    'hello' 


Class LyricException
--------------------


Methods
~~~~~~~

**args()**


**message()**



Class Note
----------

Note class for notes (not rests or unpitched elements) that can be represented by one or more notational units A Note knows both its total duration and how to express itself as a set of tied notes of different lengths. For instance, a note of 2.5 quarters in length could be half tied to eighth or dotted quarter tied to quarter. A ComplexNote will eventually be smart enough that if given a duration in quarters it will try to figure out a way to express itself as best it can if it needs to be represented on page.  It does not know this now. 

Attributes
~~~~~~~~~~

+ articulations
+ beams
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ pitch
+ tie

Methods
~~~~~~~

**accidental()**


**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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

    see Pitch.diatonicNoteNum 

**duration()**

    Gets the DurationObject of the object or None 

    

**freq440()**


**frequency()**


**id()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lily()**

    The name of the note as it would appear in Lilypond format. 

**lyric()**


**midi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**midiNote()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**name()**


**nameWithOctave()**


**octave()**


**parent()**


**pitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**setAccidental()**


**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**step()**


**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getAccidental()**


**_getColor()**


**_getDiatonicNoteNum()**

    see Pitch.diatonicNoteNum 

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getFreq440()**


**_getFrequency()**


**_getLily()**

    The name of the note as it would appear in Lilypond format. 

**_getLyric()**


**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMidi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getName()**


**_getNameWithOctave()**


**_getOctave()**


**_getParent()**


**_getPitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_getStep()**


**_overriddenLily()**


**_parent()**


**_preDurationLily()**

    Method to return all the lilypond information that appears before the duration number. Is the same for simple and complex notes. 

**_setAccidental()**

    Adds an accidental to the Note, given as an Accidental object. Also alters the name of the note 

    >>> a = Note()
    >>> a.step = "D"
    >>> a.name
    'D' 
    >>> b = Accidental("sharp")
    >>> a.setAccidental(b)
    >>> a.name
    'D#' 

**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setFreq440()**


**_setFrequency()**


**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMX()**

    Given an mxNote, fill the necessary parameters 

**_setMidi()**


**_setMusicXML()**


**_setName()**


**_setOctave()**


**_setParent()**


**_setPitchClass()**


**_setQuarterLength()**


**_setStep()**



Class NoteException
-------------------


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


Class QuarterNote
-----------------


Attributes
~~~~~~~~~~

+ articulations
+ beams
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ pitch
+ tie

Methods
~~~~~~~

**accidental()**


**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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

    see Pitch.diatonicNoteNum 

**duration()**

    Gets the DurationObject of the object or None 

    

**freq440()**


**frequency()**


**id()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lily()**

    The name of the note as it would appear in Lilypond format. 

**lyric()**


**midi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**midiNote()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**name()**


**nameWithOctave()**


**octave()**


**parent()**


**pitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**setAccidental()**


**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**step()**


**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getAccidental()**


**_getColor()**


**_getDiatonicNoteNum()**

    see Pitch.diatonicNoteNum 

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getFreq440()**


**_getFrequency()**


**_getLily()**

    The name of the note as it would appear in Lilypond format. 

**_getLyric()**


**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMidi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getName()**


**_getNameWithOctave()**


**_getOctave()**


**_getParent()**


**_getPitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_getStep()**


**_overriddenLily()**


**_parent()**


**_preDurationLily()**

    Method to return all the lilypond information that appears before the duration number. Is the same for simple and complex notes. 

**_setAccidental()**

    Adds an accidental to the Note, given as an Accidental object. Also alters the name of the note 

    >>> a = Note()
    >>> a.step = "D"
    >>> a.name
    'D' 
    >>> b = Accidental("sharp")
    >>> a.setAccidental(b)
    >>> a.name
    'D#' 

**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setFreq440()**


**_setFrequency()**


**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMX()**

    Given an mxNote, fill the necessary parameters 

**_setMidi()**


**_setMusicXML()**


**_setName()**


**_setOctave()**


**_setParent()**


**_setPitchClass()**


**_setQuarterLength()**


**_setStep()**



Class Rest
----------

General rest class 

Attributes
~~~~~~~~~~

+ articulations
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ tie

Methods
~~~~~~~

**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lily()**

    The name of the rest as it would appear in Lilypond format. 

    >>> r1 = Rest()
    >>> r1.duration.type = "half"
    >>> r1.lily
    'r2' 

**lyric()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**parent()**


**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getColor()**


**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getLyric()**


**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getParent()**


**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_lilyName()**

    The name of the rest as it would appear in Lilypond format. 

    >>> r1 = Rest()
    >>> r1.duration.type = "half"
    >>> r1.lily
    'r2' 

**_overriddenLily()**


**_parent()**


**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMX()**

    Given an mxNote, fille the necessary parameters 

**_setMusicXML()**


**_setParent()**


**_setQuarterLength()**



Class TestExternal
------------------

These are tests that open windows and rely on external software 

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

**testBasic()**


**testSingle()**

    Need to test direct meter creation w/o stream 

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


Class Tie
---------

Object added to notes that are tied to other notes note1.tie = Tie("start") note1.tieStyle = "normal" # could be dotted or dashed print note1.tie.type # prints start Differences from MusicXML: notes do not need to know if they are tied from a previous note.  i.e., you can tie n1 to n2 just with a tie start on n1.  However, if you want proper musicXML output you need a tie stop on n2 one tie with "continue" implies tied from and tied to optional (to know what notes are next:) .to = note()   # not implimented yet, b/c of garbage coll. .from = note() (question: should notes be able to be tied to multiple notes for the case where a single note is tied both voices of a two-note-head unison?) 

Attributes
~~~~~~~~~~

+ contexts
+ groups
+ type

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

**parent()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getParent()**


**_overriddenLily()**


**_parent()**


**_setDuration()**

    Set the offset as a quarterNote length 

**_setParent()**



Class Unpitched
---------------

General class of unpitched objects which appear at different places on the staff.  Examples: percussion notation 

Attributes
~~~~~~~~~~

+ articulations
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ tie

Methods
~~~~~~~

**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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

**displayOctave()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**duration()**

    Gets the DurationObject of the object or None 

    

**id()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lyric()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**parent()**


**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getColor()**


**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getLyric()**


**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getParent()**


**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_overriddenLily()**


**_parent()**


**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMusicXML()**


**_setParent()**


**_setQuarterLength()**



Class WholeNote
---------------


Attributes
~~~~~~~~~~

+ articulations
+ beams
+ contexts
+ editorial
+ groups
+ lyrics
+ notations
+ pitch
+ tie

Methods
~~~~~~~

**accidental()**


**appendDuration()**

    Sets the duration of the note to the supplied duration.Duration object 

    >>> a = Note()
    >>> a.duration.clear() # remove default
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 

    

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**


**color()**


**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

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

    see Pitch.diatonicNoteNum 

**duration()**

    Gets the DurationObject of the object or None 

    

**freq440()**


**frequency()**


**id()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**lily()**

    The name of the note as it would appear in Lilypond format. 

**lyric()**


**midi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**midiNote()**


**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**name()**


**nameWithOctave()**


**octave()**


**parent()**


**pitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**reinit()**


**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**setAccidental()**


**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**splitAtDurations()**

    Takes a Note and returns a list of notes with only a single duration.Duration each. 

    >>> a = Note()
    >>> a.duration.clear() # remove defaults
    >>> a.appendDuration(duration.Duration('half'))
    >>> a.duration.quarterLength
    2.0 
    >>> a.appendDuration(duration.Duration('whole'))
    >>> a.duration.quarterLength
    6.0 
    >>> b = a.splitAtDurations()
    >>> b[0].pitch == b[1].pitch
    True 
    >>> b[0].duration.type
    'half' 
    >>> b[1].duration.type
    'whole' 

**splitNoteAtPoint()**

    Split a Note into two Notes. 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> b, c = a.splitNoteAtPoint(3)
    >>> b.duration.type
    'half' 
    >>> b.duration.dots
    1 
    >>> b.duration.quarterLength
    3.0 
    >>> c.duration.type
    'quarter' 
    >>> c.duration.dots
    0 
    >>> c.duration.quarterLength
    1.0 

**step()**


**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**


**_getAccidental()**


**_getColor()**


**_getDiatonicNoteNum()**

    see Pitch.diatonicNoteNum 

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getFreq440()**


**_getFrequency()**


**_getLily()**

    The name of the note as it would appear in Lilypond format. 

**_getLyric()**


**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMidi()**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getName()**


**_getNameWithOctave()**


**_getOctave()**


**_getParent()**


**_getPitchClass()**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**_getStep()**


**_overriddenLily()**


**_parent()**


**_preDurationLily()**

    Method to return all the lilypond information that appears before the duration number. Is the same for simple and complex notes. 

**_setAccidental()**

    Adds an accidental to the Note, given as an Accidental object. Also alters the name of the note 

    >>> a = Note()
    >>> a.step = "D"
    >>> a.name
    'D' 
    >>> b = Accidental("sharp")
    >>> a.setAccidental(b)
    >>> a.name
    'D#' 

**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: because Lilypond supports "blue", "red" etc., as does CSS; musicxml also supports alpha 

    >>> a = GeneralNote()
    >>> a.duration.type = 'whole'
    >>> a.color = '#235409'
    >>> a.color
    '#235409' 
    >>> a.editorial.color
    '#235409' 

    

**_setDuration()**

    Set the offset as a quarterNote length 

**_setFreq440()**


**_setFrequency()**


**_setLyric()**

    should check data here 

    >>> a = GeneralNote()
    >>> a.lyric = 'test'
    >>> a.lyric
    'test' 

**_setMX()**

    Given an mxNote, fill the necessary parameters 

**_setMidi()**


**_setMusicXML()**


**_setName()**


**_setOctave()**


**_setParent()**


**_setPitchClass()**


**_setQuarterLength()**


**_setStep()**



