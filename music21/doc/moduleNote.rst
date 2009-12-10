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

Inherits from: base.Music21Object, object

Accidental class. 

Attributes
~~~~~~~~~~

**alter**

**modifier**

**name**

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


Locally Defined

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

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

**lily**



Class Beam
----------

Inherits from: object

An object representation of a beam, where each beam objects exists for each horizontal line in a total beam structure for one note. 

Attributes
~~~~~~~~~~

**direction**

**independentAngle**

**number**

**type**

Properties
~~~~~~~~~~


Locally Defined

**mx**

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


Class Beams
-----------

Inherits from: object

A group of beams applied to a single note that represents the partial beam structure of many notes beamed together. 

Attributes
~~~~~~~~~~

**beamsList**

**feathered**

Methods
~~~~~~~


Locally Defined

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

**setAll()**

    Convenience method to set all beam objects within Beams 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.getTypes()
    ['start', 'start'] 

    

**getTypes()**

    Retur a lost of all types 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.getTypes()
    ['start', 'start'] 

**getNumbers()**

    Retrun a lost of all defind numbers 

    >>> a = Beams()
    >>> a.fill('32nd')
    >>> a.getNumbers()
    [1, 2, 3] 

**getByNumber()**

    Set an internal beam object by number, or rhythmic symbol level 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> a.setAll('start')
    >>> a.getByNumber(2).type
    'start' 

**fill()**

    Clear an fill the beams list as commonly needed for various durations do not set type or direction 

    >>> a = Beams()
    >>> a.fill('16th')
    >>> len(a)
    2 
    >>> a.fill('32nd')
    >>> len(a)
    3 

**addNext()**


Properties
~~~~~~~~~~


Locally Defined

**mx**

    Returns a list of mxBeam objects 


Class EighthNote
----------------

Inherits from: note.Note, note.GeneralNote, base.Music21Object, object


Attributes
~~~~~~~~~~

**articulations**

**beams**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**pitch**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Inherited from note.Note

**setAccidental()**

**midiNote()**

**isUnpitched()**

**isRest()**

**isNote()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Inherited from note.Note

**step**

**pitchClass**

**octave**

**nameWithOctave**

**name**

**mx**

**midi**

**lily**

**frequency**

**freq440**

**diatonicNoteNum**

**accidental**


Class GeneralNote
-----------------

Inherits from: base.Music21Object, object

A GeneralNote object is the parent object for the Note, Rest, Unpitched, and SimpleNote, etc. objects It contains duration, notations, editorial, and tie fields. 

Attributes
~~~~~~~~~~

**articulations**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**tie**

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


Locally Defined

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

**reinit()**


**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

**clone()**


**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

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

    

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

**quarterLength**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2.0
    >>> n.quarterLength
    2.0 

**musicxml**

    This must call _getMX to get basic mxNote objects 

**lyric**


**color**



Class HalfNote
--------------

Inherits from: note.Note, note.GeneralNote, base.Music21Object, object


Attributes
~~~~~~~~~~

**articulations**

**beams**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**pitch**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Inherited from note.Note

**setAccidental()**

**midiNote()**

**isUnpitched()**

**isRest()**

**isNote()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Inherited from note.Note

**step**

**pitchClass**

**octave**

**nameWithOctave**

**name**

**mx**

**midi**

**lily**

**frequency**

**freq440**

**diatonicNoteNum**

**accidental**


Class LilyString
----------------

Inherits from: object


Attributes
~~~~~~~~~~

**value**

Methods
~~~~~~~


Locally Defined

**writeTemp()**


**wrapForMidi()**


**showPNGandPlayMIDI()**


**showPNG()**

    Take the LilyString, run it through LilyPond, and then show it as a PNG file. On Windows, the PNG file will not be deleted, so you  will need to clean out TEMP every once in a while 

**showPDF()**


**showImageDirect()**

    borrowed from and modified from the excellent PIL image library, but needed some changes to the NT handling 

**savePNG()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**runThroughLily()**


**quickHeader()**

    Returns a quick and dirty lilyPond header for the stream 

**playMIDIfile()**


**midiWrapped()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**createPDF()**


**checkForMidiAndAdd()**


**checkForMidi()**


**addMidi()**

    override this in subclasses, such as LilyScore 

Properties
~~~~~~~~~~


Locally Defined

**wrappedValue**

    returns a value that is wrapped with { } if it doesn't contain a score element so that it can run through lilypond 


Class Lyric
-----------

Inherits from: object


Attributes
~~~~~~~~~~

**number**

**syllabic**

**text**

Properties
~~~~~~~~~~


Locally Defined

**mx**

    Returns an mxLyric 

    >>> a = Lyric()
    >>> a.text = 'hello'
    >>> mxLyric = a.mx
    >>> mxLyric.get('text')
    'hello' 


Class Note
----------

Inherits from: note.GeneralNote, base.Music21Object, object

Note class for notes (not rests or unpitched elements) that can be represented by one or more notational units A Note knows both its total duration and how to express itself as a set of tied notes of different lengths. For instance, a note of 2.5 quarters in length could be half tied to eighth or dotted quarter tied to quarter. A ComplexNote will eventually be smart enough that if given a duration in quarters it will try to figure out a way to express itself as best it can if it needs to be represented on page.  It does not know this now. 

Attributes
~~~~~~~~~~

**articulations**

**beams**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**pitch**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Locally Defined

**setAccidental()**


**midiNote()**


**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Locally Defined

**step**


**pitchClass**

    Return pitch class 

    >>> d = Note()
    >>> d.pitch = Pitch('d-4')
    >>> d.pitchClass
    1 
    >>>

**octave**


**nameWithOctave**


**name**


**mx**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**midi**

    Returns the note's midi number. C4 (middle C) = 60, C#4 = 61, D-4 = 61, D4 = 62; A4 = 69 

    >>> a = Note()
    >>> a.pitch = Pitch('d-4')
    >>> a.midi
    61 

**lily**

    The name of the note as it would appear in Lilypond format. 

**frequency**


**freq440**


**diatonicNoteNum**

    see Pitch.diatonicNoteNum 

**accidental**



Class Pitch
-----------

Inherits from: base.Music21Object, object


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

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

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


Class QuarterNote
-----------------

Inherits from: note.Note, note.GeneralNote, base.Music21Object, object


Attributes
~~~~~~~~~~

**articulations**

**beams**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**pitch**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Inherited from note.Note

**setAccidental()**

**midiNote()**

**isUnpitched()**

**isRest()**

**isNote()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Inherited from note.Note

**step**

**pitchClass**

**octave**

**nameWithOctave**

**name**

**mx**

**midi**

**lily**

**frequency**

**freq440**

**diatonicNoteNum**

**accidental**


Class Rest
----------

Inherits from: note.GeneralNote, base.Music21Object, object

General rest class 

Attributes
~~~~~~~~~~

**articulations**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Locally Defined

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Locally Defined

**mx**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**lily**

    The name of the rest as it would appear in Lilypond format. 

    >>> r1 = Rest()
    >>> r1.duration.type = "half"
    >>> r1.lily
    'r2' 


Class Tie
---------

Inherits from: base.Music21Object, object

Object added to notes that are tied to other notes note1.tie = Tie("start") note1.tieStyle = "normal" # could be dotted or dashed print note1.tie.type # prints start Differences from MusicXML: notes do not need to know if they are tied from a previous note.  i.e., you can tie n1 to n2 just with a tie start on n1.  However, if you want proper musicXML output you need a tie stop on n2 one tie with "continue" implies tied from and tied to optional (to know what notes are next:) .to = note()   # not implimented yet, b/c of garbage coll. .from = note() (question: should notes be able to be tied to multiple notes for the case where a single note is tied both voices of a two-note-head unison?) 

Attributes
~~~~~~~~~~

**contexts**

**groups**

**locations**

**type**

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

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Class Unpitched
---------------

Inherits from: note.GeneralNote, base.Music21Object, object

General class of unpitched objects which appear at different places on the staff.  Examples: percussion notation 

Attributes
~~~~~~~~~~

**articulations**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Locally Defined

**isUnpitched()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**displayOctave()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Class WholeNote
---------------

Inherits from: note.Note, note.GeneralNote, base.Music21Object, object


Attributes
~~~~~~~~~~

**articulations**

**beams**

**contexts**

**editorial**

**groups**

**locations**

**lyrics**

**notations**

**pitch**

**tie**

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


Inherited from note.GeneralNote

**splitNoteAtPoint()**

**splitAtDurations()**

**reinit()**

**isChord()**

**compactNoteInfo()**

**clone()**

**clearDurations()**

**appendDuration()**


Inherited from note.Note

**setAccidental()**

**midiNote()**

**isUnpitched()**

**isRest()**

**isNote()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from note.GeneralNote

**quarterLength**

**musicxml**

**lyric**

**color**


Inherited from note.Note

**step**

**pitchClass**

**octave**

**nameWithOctave**

**name**

**mx**

**midi**

**lily**

**frequency**

**freq440**

**diatonicNoteNum**

**accidental**


