music21.chord
=============

Class Chord
-----------

Class for dealing with chords A Chord is an object composed of Notes. Create chords by creating notes: C = note.Note(), C.name = 'C' E = note.Note(), E.name = 'E' G = note.Note(), G.name = 'G' And then create a chord with notes: cmaj = Chord([C, E, G]) Chord has the ability to determine the root of a chord, as well as the bass note of a chord. In addition, Chord is capable of determining what type of chord a particular chord is, whether it is a triad or a seventh, major or minor, etc, as well as what inversion the chord is in. NOTE: For now, the examples used in documentation give chords made from notes that are not defined. In the future, it may be possible to define a chord without first creating notes, but for now note that notes that appear in chords are simply shorthand instead of creating notes for use in examples 



Public Attributes
~~~~~~~~~~~~~~~~~

+ articulations
+ contexts
+ duration
+ editorial
+ groups
+ lyrics
+ notations
+ pitches
+ tie

Public Methods
~~~~~~~~~~~~~~

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

    

**bass()**

    returns the bass note or sets it to note. Usually defined to the lowest note in the chord, but we want to be able to override this.  You might want an implied bass for instance...  v o9. example: 

    >>> cmaj = Chord(['C', 'E', 'G'])
    >>> cmaj.bass() # returns C
    C 

**canBeDominantV()**

    No documentation.

**canBeTonic()**

    No documentation.

**checkDurationSanity()**

    TO WRITE Checks to make sure all notes have the same duration Does not run automatically 

**clearDurations()**

    clears all the durations stored in the note. After performing this, it's probably not wise to print the note until at least one duration.Duration is added 

**clone()**

    No documentation.

**color()**

    No documentation.

**compactNoteInfo()**

    nice debugging info tool -- returns information about a note E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet) 

**containsSeventh()**

    returns True if the chord contains at least one of each of Third, Fifth, and Seventh. raises an exception if the Root can't be determined example: 

    >>> cchord = Chord (['C', 'E', 'G', 'B'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G', 'B'])
    >>> cchord.containsSeventh() # returns True
    True 
    >>> other.containsSeventh() # returns True
    True 

**containsTriad()**

    returns True or False if there is no triad above the root. "Contains vs. Is": A dominant-seventh chord contains a triad. example: 

    >>> cchord = Chord (['C', 'E', 'G'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G'])
    >>> cchord.containsTriad() #returns True
    True 
    >>> other.containsTriad() #returns True
    True 

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

**determineType()**

    returns an abbreviation for the type of chord it is. Add option to add inversion name to abbreviation? TODO: determine permanent designation abbreviation for every type of chord and inversion 

**duration()**

    Duration of the chord can be defined here OR it should return the duration of the first note of the chord 

**findBass()**

    Returns the lowest note in the chord The only time findBass should be called is by bass() when it is figuring out what the bass note of the chord is. Generally call bass() instead example: 

    >>> cmaj = Chord (['C4', 'E3', 'G4'])
    >>> cmaj.findBass() # returns E3
    E3 

**findRoot()**

    Looks for the root by finding the note with the most 3rds above it Generally use root() instead, since if a chord doesn't know its root, root() will run findRoot() automatically. example: 

    >>> cmaj = Chord (['C', 'E', 'G'])
    >>> cmaj.findRoot() # returns C
    C 

**hasAnyRepeatedScale()**

    Returns True if for any scale degree there are two or more different notes (such as E and E-) in the chord. If there are no repeated scale degrees, return false. example: 

    >>> cchord = Chord (['C', 'E', 'E-', 'G'])
    >>> other = Chord (['C', 'E', 'F-', 'G'])
    >>> cchord.hasAnyRepeatedScale()
    True 
    >>> other.hasAnyRepeatedScale() # returns false (chromatically identical notes of different scale degrees do not count.
    False 

**hasFifth()**

    Shortcut for hasScaleX(5) 

**hasRepeatedScaleX()**

    Returns True if scaleDeg above testRoot (or self.root()) has two or more different notes (such as E and E-) in it.  Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E', 'E-', 'G'])
    >>> cchord.hasRepeatedScaleX(3) # returns true
    True 

**hasScaleX()**

    Each of these returns the number of semitones above the root that the third, fifth, etc., of the chord lies, if there exists one.  Or False if it does not exist. You can optionally specify a note.Note object to try as the root.  It does not change the Chord.root object.  We use these methods to figure out what the root of the triad is. Currently there is a bug that in the case of a triply diminished third (e.g., "c" => "e----"), this function will incorrectly claim no third exists.  Perhaps this be construed as a feature. In the case of chords such as C, E-, E, hasThird will return 3, not 4, nor a list object (3,4).  You probably do not want to be using tonal chord manipulation functions on chords such as these anyway. note.Note that in Chord, we're using "Scale" to mean a diatonic scale step. It will not tell you if a chord has a specific scale degree in another scale system.  That functionality might be added to scale.py someday. example: 

    >>> cchord = Chord (['C', 'E', 'E-', 'G'])
    >>> cchord.hasScaleX(3) #
    4 
    >>> cchord.hasScaleX(5) # will return 7
    7 
    >>> cchord.hasScaleX(6) # will return False
    False 

**hasSeventh()**

    Shortcut for hasScaleX(7) 

**hasSpecificX()**

    Exactly like hasScaleX, except it returns the interval itself instead of the number of semitones. example: 

    >>> cmaj = Chord (['C', 'E', 'G'])
    >>> cmaj.hasScaleX(3) #will return the interval between C and E
    4 
    >>> cmaj.hasScaleX(5) #will return the interval between C and G
    7 
    >>> cmaj.hasScaleX(6) #will return False
    False 

**hasThird()**

    Shortcut for hasScaleX(3) 

**id()**

    No documentation.

**inversion()**

    returns an integer representing which standard inversion the chord is in. Chord does not have to be complete, but determines the inversion by looking at the relationship of the bass note to the root. 

**inversionName()**

    Returns an integer representing the common abbreviation for the inversion the chord is in. If chord is not in a common inversion, returns null. 

**isAugmentedTriad()**

    Returns True if chord is a Diminished Triad, that is, if it contains only notes that are either in unison with the root, a major third above the root, or an augmented fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

**isChord()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isClass()**

    returns bool depending on if the object is a particular class or not same as isinstance here, but different for Elements, where it checks to see if the embedded object is of a certain class.  Use it throughout music21 and only use isinstance if you really want to see if something is an Element or not. 

**isDiminishedSeventh()**

    Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

**isDiminishedTriad()**

    Returns True if chord is a Diminished Triad, that is, if it contains only notes that are either in unison with the root, a minor third above the root, or a diminished fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E-', 'G-'])
    >>> other = Chord (['C', 'E-', 'F#'])
    >>> cchord.isDiminishedTriad() #returns True
    True 
    >>> other.isDiminishedTriad() #returns False
    False 

**isDominantSeventh()**

    Returns True if chord is a Dominant Seventh, that is, if it contains only notes that are either in unison with the root, a major third above the root, a perfect fifth, or a major seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

**isFalseDiminishedSeventh()**

    Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord may be spelled incorrectly. Otherwise returns false. 

**isHalfDiminishedSeventh()**

    Returns True if chord is a Half Diminished Seventh, that is, if it contains only notes that are either in unison with the root, a minor third above the root, a diminished fifth, or a major seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

**isMajorTriad()**

    Returns True if chord is a Major Triad, that is, if it contains only notes that are either in unison with the root, a major third above the root, or a perfect fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E', 'G'])
    >>> other = Chord (['C', 'G'])
    >>> cchord.isMajorTriad() # returns True
    True 
    >>> other.isMajorTriad() # returns False
    False 

**isMinorTriad()**

    Returns True if chord is a Minor Triad, that is, if it contains only notes that are either in unison with the root, a minor third above the root, or a perfect fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E-', 'G'])
    >>> other = Chord (['C', 'E', 'G'])
    >>> cchord.isMinorTriad() # returns True
    True 
    >>> other.isMinorTriad() # returns False
    False 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isSeventh()**

    Returns True if chord contains at least one of each of Third, Fifth, and Seventh, and every note in the chord is a Third, Fifth, or Seventh, such that there are no repeated scale degrees (ex: E and E-). Else return false. example: 

    >>> cchord = Chord (['C', 'E', 'G', 'B'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G', 'B'])
    >>> cchord.isSeventh() # returns True
    True 
    >>> other.isSeventh() # returns False
    False 

**isTriad()**

    returns True or False "Contains vs. Is:" A dominant-seventh chord is NOT a triad. returns True if the chord contains at least one Third and one Fifth and all notes are equivalent to either of those notes. Only returns True if triad is spelled correctly. example: 

    >>> cchord = Chord (['C', 'E', 'G'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G'])
    >>> cchord.isTriad() # returns True
    True 
    >>> other.isTriad()
    False 

**lily()**

    The name of the note as it would appear in Lilypond format. 

**lyric()**

    No documentation.

**musicxml()**

    This must call _getMX to get basic mxNote objects 

**mx()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**numNotes()**

    Returns the number of notes in the chord 

**offset()**

    No documentation.

**parent()**

    No documentation.

**priority()**

    No documentation.

**quarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2
    >>> n.quarterLength
    2.0 

**reinit()**

    No documentation.

**root()**

    Returns or sets the Root of the chord.  if not set, will run findRoot (q.v.) example: 

    >>> cmaj = Chord (['C', 'E', 'G'])
    >>> cmaj.root() # returns C
    C 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    This might need to return the file path. 

**sortAscending()**

    After talking with Daniel Jackson, let's try to make the chord object immutable here, so we return a new Chord object with the notes arranged from lowest to highest The notes are sorted by Scale degree and then by Offset (so F## sorts below G-). Notes that are the identical pitch retain their order 

**sortChromaticAscending()**

    Same as sortAscending but notes are sorted by midi number, so F## sorts above G-. 

**sortFrequencyAscending()**

    Same as above, but uses a note's frequency to determine height; so that C# would be below D- in 1/4-comma meantone, equal in equal temperament, but below it in (most) just intonation types. 

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

    Write a file. A None file path will result in temporary file TODO: Discussion: I would like if at all possible to have the output formats moved out of the modules and into a format.XXXXX module.  That way someone could write an entirely new format without needing to muck around with our code. Some formats that we probably would not write ourselves but which I can see someone else really wanting to write include: kern, braille (see MTO 15.3), ascii, etc.  It would be easier for these users to code .write() methods for each of the formats there. 

    

Private Methods
~~~~~~~~~~~~~~~

**_bass()**

    No documentation.

**_duration()**

    No documentation.

**_getColor()**

    No documentation.

**_getDuration()**

    Gets the DurationObject of the object or None 

    

**_getLily()**

    The name of the note as it would appear in Lilypond format. 

**_getLyric()**

    No documentation.

**_getMX()**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

**_getMusicXML()**

    This must call _getMX to get basic mxNote objects 

**_getOffset()**

    No documentation.

**_getParent()**

    No documentation.

**_getPriority()**

    No documentation.

**_getQuarterLength()**

    Return quarter length 

    >>> n = Note()
    >>> n.quarterLength = 2
    >>> n.quarterLength
    2.0 

**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**

    No documentation.

**_parent()**

    No documentation.

**_preDurationLily()**

    Method to return all the lilypond information that appears before the duration number.  Note that _getLily is the same as with notes but not yet subclassed... 

**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**_root()**

    No documentation.

**_setColor()**

    should check data here uses this re: #[\dA-F]{6}([\dA-F][\dA-F])? No: 

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

    Given an a list of mxNotes, fille the necessary parameters 

**_setMusicXML()**

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

**_setQuarterLength()**

    No documentation.


Class ChordException
--------------------

No documentation.

Public Methods
~~~~~~~~~~~~~~

**args()**

    No documentation.

**message()**

    No documentation.


Class Duration
--------------

A Duration is made of one or more DurationUnits. Multiple Duration units may be used to express tied notes, or may be used to split duration accross barlines or beam groups. Some Durations are not expressable as a single notation unit. 

Public Attributes
~~~~~~~~~~~~~~~~~

+ components
+ durationToType
+ linkages
+ ordinalTypeFromNum
+ typeFromNumDict
+ typeToDuration

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _qtrLength
+ _quarterLengthNeedsUpdating

Public Methods
~~~~~~~~~~~~~~

**addDuration()**

    Add either a DurationUnit or a Duration object to this Duration. Adding a Duration always assumes that the Duration is tied. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)

**clear()**

    Permit all componets to be removed. It is not clear yet if this is needed. 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> # a.type

**clone()**

    print here 

**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    >>> for x in [1,1,1]: components.append(Duration('quarter'))
    ... 
    >>> a = Duration()
    >>> a.components = components
    >>> a._updateQuarterLength()
    >>> a.quarterLength
    3.0 
    >>> a.componentIndexAtQtrPosition(.5)
    0 
    >>> a.componentIndexAtQtrPosition(1.5)
    1 
    >>> a.componentIndexAtQtrPosition(2.5)
    2 
    this is odd behavior: 
    e.g. given d1, d2, d3 as 3 quarter notes and 
    self.components = [d1, d2, d3] 
    then 
    self.componentIndexAtQtrPosition(1.5) == d2 
    self.componentIndexAtQtrPosition(2.0) == d3 
    self.componentIndexAtQtrPosition(2.5) == d3 

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

    >>> components = []
    >>> for x in [1,1,1]: components.append(Duration('quarter'))
    ... 
    >>> a = Duration()
    >>> a.components = components
    >>> a._updateQuarterLength()
    >>> a.quarterLength
    3.0 
    >>> a.componentStartTime(0)
    0.0 
    >>> a.componentStartTime(1)
    1.0 

**consolidate()**

    Given a Duration with multiple comoponents, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

    >>> a = Duration()
    >>> a._fill(['quarter', 'half', 'quarter'])
    >>> a.quarterLength
    4.0 
    >>> len(a.components)
    3 
    >>> a.consolidate()
    >>> a.quarterLength
    4.0 
    >>> len(a.components)
    1 

**convertNumberToType()**

    Convert a number ( 4 = quarter; 8 = eighth), etc. to type. 

    >>> a = DurationCommon()
    >>> a.convertNumberToType(4)
    'quarter' 
    >>> a.convertNumberToType(32)
    '32nd' 

**convertQuarterLengthToDuration()**

    Given a an arbitrary quarter length, convert it into a the parameters necessary to instantiate a DurationUnit object. Note: this now uses quarterLengthToUnitSpec(); this method remains for backward compatibility; but can be replaced 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToDuration(3)
    ('half', [1], []) 
    >>> a.convertQuarterLengthToDuration(1)
    ('quarter', [0], []) 
    >>> a.convertQuarterLengthToDuration(.75)
    ('eighth', [1], []) 
    >>> a.convertQuarterLengthToDuration(.125)
    ('32nd', [0], []) 
    >>> post = a.convertQuarterLengthToDuration(.33333)
    >>> post[0] == 'eighth'
    True 
    >>> post[1] == [0]
    True 
    >>> isinstance(post[2][0], Tuplet)
    True 

**convertQuarterLengthToType()**

    Convert quarter lengths to types. This cannot handle quarter lengths of 3 or .75 

    >>> a = DurationCommon()
    >>> a.convertQuarterLengthToType(2)
    'half' 
    >>> a.convertQuarterLengthToType(0.125)
    '32nd' 

**convertTypeToNumber()**

    Convert duration type to 

    >>> a = DurationCommon()
    >>> a.convertTypeToNumber('quarter')
    4 
    >>> a.convertTypeToNumber('half')
    2 

**convertTypeToOrdinal()**

    Convert type to an ordinal number based on self.ordinalTypeFromNum 

    >>> a = DurationCommon()
    >>> a.convertTypeToOrdinal('whole')
    4 
    >>> a.convertTypeToOrdinal('maxima')
    1 
    >>> a.convertTypeToOrdinal('1024th')
    14 

**convertTypeToQuarterLength()**

    Given a rhythm type, convert it to a quarter length, given a lost of dots and tuplets. 

    >>> a = DurationCommon()
    >>> a.convertTypeToQuarterLength('whole')
    4.0 
    >>> a.convertTypeToQuarterLength('16th')
    0.25 
    >>> a.convertTypeToQuarterLength('quarter', [2])
    1.75 

**dots()**

    Return dots as a list Assume we only want the first element. 

**expand()**

    Make a duration notatable. Provide a unit of division. 

**isComplex()**

    No documentation.

**lily()**

    Simple lily duration: does not include tuplets NOTE: not sure if this works properly; does not seem to include ties 

**musicxml()**

    Return a complete MusicXML string with defaults. 

**mx()**

    Returns a list of one or more musicxml.Note() objects with all rhythms and ties necessary. mxNote objects are incompletely specified, lacking full representation and information on pitch, etc. TODO: tuplets, notations, ties 

    >>> a = Duration()
    >>> a.quarterLength = 3
    >>> b = a.mx
    >>> len(b) == 1
    True 
    >>> isinstance(b[0], musicxmlMod.Note)
    True 

**ordinalNumFromType()**

    for backward compatibility; replace with property ordinal 

**partitionToUnitSpec()**

    Given any qLen, partition into one or more quarterLengthUnits based on a specified qLenDiv Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType Dividing 2.5 qLen into eighth notes. 

    >>> a = DurationCommon()
    >>> a.partitionToUnitSpec(2.5,.5)
    ([(0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5 qLen into 2.5 qLen bundles 
    >>> a.partitionToUnitSpec(5,2.5)
    ([(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None), (2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)], True) 
    Dividing 5.25 qLen into dotted halves 
    >>> a.partitionToUnitSpec(5.25,3)
    ([(3, 'half', 1, None, None, None), (2.0, 'half', 0, None, None, None), (0.25, '16th', 0, None, None, None)], False) 

    
    Dividing 1.33333 qLen into triplet eighths: 
    >>> a.partitionToUnitSpec(1.33333333333333,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth')], True) 

    
    Dividing 1.5 into triplet eighths 
    >>> a.partitionToUnitSpec(1.5,.33333333333333)
    ([(0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.33333333333332998, 'eighth', 0, 3, 2, 'eighth'), (0.16666666666668023, '16th', 0, 3, 2, '16th')], False) 

    
    No problem if the division unit is larger then the source duration. 
    >>> a.partitionToUnitSpec(1.5, 4)
    ([(1.5, 'quarter', 1, None, None, None)], False) 

    

**quarterLength()**

    Can be the same as the base class. 

**quarterLengthToDotCandidate()**

    Given a qLen and type that is less than but not greater than qLen, determine if one or more dots match. TODO: Find and return dotgroups, perhaps based on optional flag 

    >>> a = DurationCommon()
    >>> a.quarterLengthToDotCandidate(3, 'half')
    (1, True) 

**quarterLengthToTupletCandidate()**

    Return one or more possible tuplets for a given qLen. 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTupletCandidate(.33333333)
    [[3, 2, 'eighth'], [3, 1, 'quarter']] 
    By specifying only 1 count, the tuple with the smallest type will be 
    returned. 
    >>> a.quarterLengthToTupletCandidate(.3333333, 1)
    [[3, 2, 'eighth']] 

    
    >>> a.quarterLengthToTupletCandidate(.20)
    [[5, 4, '16th'], [5, 2, 'eighth'], [5, 1, 'quarter']] 
    #ARIZA: would this be more portable if it returned a list of 
    # Tuplet objects instead 
    # this would work fine, but is harder to test in the short term, 
    # b/c the object parameters have be examined. 

**quarterLengthToTypeCandidate()**

    Return the type for a given quarterLength, otherwise return the type that is the largest that is not greater than this qLen 

    >>> a = DurationCommon()
    >>> a.quarterLengthToTypeCandidate(.5)
    ('eighth', None, True) 
    >>> a.quarterLengthToTypeCandidate(.75)
    ('eighth', 'quarter', False) 
    >>> a.quarterLengthToTypeCandidate(1.75)
    ('quarter', 'half', False) 

**quarterLengthToUnitSpec()**

    Given a quarterLength, determine if it can be notated as a single unit, or if it needs to be divided into multiple units. (n.b. all quarterLengths can, technically, be notated as a single unit given a complex enough tuplet, but we do not use that). Returns lists of: qLen, durType, dots, tupleDiv, tupletMult, tupletType 

    >>> a = DurationCommon()
    >>> a.quarterLengthToUnitSpec(2)
    [(2, 'half', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3)
    [(3, 'half', 1, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(6.0)
    [(6.0, 'whole', 1, None, None, None)] 
    Double and triple dotted half note. 
    >>> a.quarterLengthToUnitSpec(3.5)
    [(3.5, 'half', 2, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(3.75)
    [(3.75, 'half', 3, None, None, None)] 
    A triplet quarter note, lasting .6666 qLen 
    Or, a quarter that is 1/3 of a half. 
    Or, a quarter that is 2/3 of a quarter. 
    >>> a.quarterLengthToUnitSpec(.6666666666)
    [(0.66666666659999996, 'quarter', 0, 3, 2, 'quarter')] 
    A triplet eighth note, where 3 eights are in the place of 2. 
    Or, an eighth that is 1/3 of a quarter 
    Or, an eighth that is 2/3 of eighth 
    >>> post = a.quarterLengthToUnitSpec(.3333333)
    >>> common.almostEquals(post[0][0], .3333333)
    True 
    >>> post[0][1:]
    ('eighth', 0, 3, 2, 'eighth') 
    A half that is 1/3 of a whole, or a triplet half note. 
    Or, a half that is 2/3 of a half 
    >>> a.quarterLengthToUnitSpec(1.3333333)
    [(1.3333333000000001, 'half', 0, 3, 2, 'half')] 
    A sixteenth that is 1/5 of a quarter 
    Or, a sixteenth that is 4/5ths of a 16th 
    >>> a.quarterLengthToUnitSpec(.200000000)
    [(0.20000000000000001, '16th', 0, 5, 4, '16th')] 
    A 16th that is  1/7th of a quarter 
    Or, a 16th that is 4/7 of a 16th 
    >>> a.quarterLengthToUnitSpec(0.14285714285714285)
    [(0.14285714285714285, '16th', 0, 7, 4, '16th')] 
    A 4/7ths of a whole note, or 
    A quarter that is 4/7th of of a quarter 
    >>> a.quarterLengthToUnitSpec(0.5714285714285714)
    [(0.5714285714285714, 'quarter', 0, 7, 4, 'quarter')] 
    If a duration is not containable in a single unit, the method 
    will break off the largest type that fits within this type 
    and recurse, adding as my units as necessary. 
    >>> a.quarterLengthToUnitSpec(2.5)
    [(2.0, 'half', 0, None, None, None), (0.5, 'eighth', 0, None, None, None)] 
    >>> a.quarterLengthToUnitSpec(2.3333333)
    [(2.0, 'half', 0, None, None, None), (0.33333330000000005, 'eighth', 0, 3, 2, 'eighth')] 
    >>> a.quarterLengthToUnitSpec(0.166666666667)
    [(0.166666666667, '16th', 0, 3, 2, '16th')] 

    

**setTypeFromNum()**

    No documentation.

**show()**

    This might need to return the file path. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> for x in [1,1,1]: a.addDuration(Duration('quarter'))
    ... 
    >>> a.quarterLength
    3.0 
    >>> a.sliceComponentAtPosition(.5)
    >>> a.quarterLength
    3.0 
    >>> len(a.components)
    4 
    >>> a.components[0].type
    'eighth' 
    >>> a.components[1].type
    'eighth' 
    >>> a.components[2].type
    'quarter' 

**tuplets()**

    Return dots as a list 

**type()**

    Get the duration type. 

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**_getDots()**

    Return dots as a list Assume we only want the first element. 

**_getLily()**

    Simple lily duration: does not include tuplets NOTE: not sure if this works properly; does not seem to include ties 

**_getMX()**

    Returns a list of one or more musicxml.Note() objects with all rhythms and ties necessary. mxNote objects are incompletely specified, lacking full representation and information on pitch, etc. TODO: tuplets, notations, ties 

    >>> a = Duration()
    >>> a.quarterLength = 3
    >>> b = a.mx
    >>> len(b) == 1
    True 
    >>> isinstance(b[0], musicxmlMod.Note)
    True 

**_getMusicXML()**

    Return a complete MusicXML string with defaults. 

**_getQuarterLength()**

    Can be the same as the base class. 

**_getTuplets()**

    Return dots as a list 

**_getType()**

    Get the duration type. 

**_isComplex()**

    No documentation.

**_setDots()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'
    >>> a._setDots(1)
    >>> a.quarterLength
    1.5 
    >>> a._setDots(2)
    >>> a.quarterLength
    1.75 

**_setMX()**

    Given a lost of one or more MusicXML Note objects, read in and create Durations mxNote must have a defined _measure attribute that is a reference to the MusicXML Measure that contains it 

**_setMusicXML()**

    

    

**_setQuarterLength()**

    Set the quarter note length to the specified value. What do we do with existing quarter notes? Additional types are needed: 'zero' type for zero durations 'unexpressable' type for anything that needs a Duration 

    >>> a = Duration()
    >>> a.quarterLength = 3.5
    >>> a.quarterLength
    3.5 
    >>> a.quarterLength = 1.75
    >>> a.quarterLength
    1.75 

**_setTuplets()**

    Set dots if a number, as first element Having this as a method permits error checking. 

    >>> a = Duration()
    >>> a.type = 'quarter'

**_setType()**

    Set the type length to the specified value. 

    >>> a = Duration()
    >>> a.type = 'half'
    >>> a.quarterLength
    2.0 
    >>> a.type= '16th'
    >>> a.quarterLength
    0.25 

**_updateQuarterLength()**

    Look to components and determine quarter length. 


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

**testConstruction()**

    No documentation.

**testDurations()**

    No documentation.

**testLily()**

    No documentation.

**testShortCuts()**

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


