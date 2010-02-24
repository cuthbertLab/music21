.. _moduleChord:

music21.chord
=============

Class Chord
-----------

Inherits from: note.NotRest (of module :ref:`moduleNote`), note.GeneralNote (of module :ref:`moduleNote`), base.Music21Object (of module :ref:`moduleBase`), object

Class for dealing with chords A Chord is an object composed of Notes. Create chords by creating notes: C = note.Note(), C.name = 'C' E = note.Note(), E.name = 'E' G = note.Note(), G.name = 'G' And then create a chord with notes: cmaj = Chord([C, E, G]) Chord has the ability to determine the root of a chord, as well as the bass note of a chord. In addition, Chord is capable of determining what type of chord a particular chord is, whether it is a triad or a seventh, major or minor, etc, as well as what inversion the chord is in. NOTE: For now, the examples used in documentation give chords made from notes that are not defined. In the future, it may be possible to define a chord without first creating notes, but for now note that notes that appear in chords are simply shorthand instead of creating notes for use in examples 



Attributes
~~~~~~~~~~

**articulations**

**beams**

**contexts**

**duration**

**editorial**

**groups**

**id**

**locations**

**lyrics**

**notations**

**tie**

Properties
~~~~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **priority**, **parent**, **offset**


Inherited from note.GeneralNote (of module :ref:`moduleNote`): **quarterLength**, **musicxml**, **lyric**, **color**


Locally Defined:

**primeFormString**

    Return a representation of the Chord as a prime-form set class string. 

**primeForm**

    Return a representation of the Chord as a prime-form list of pitch class integers. 

**pitches**

    TODO: presently, whenever pitches are accessed, it sets the _chordTablesAddressNeedsUpdating value to false this is b/c the pitches list can be accessed and appended to a better way to do this needs to be found 

**pitchedCommonName**

    Get the common name of the TN set class. Possible rename forteIndex 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.pitchedCommonName
    'C-minor triad' 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.pitchedCommonName
    'C-major triad' 

**pitchClasses**

    Return a pitch class representation ordered as the original chord. 

    >>> c1 = Chord(["D4", "A4", "F#5", "D6"])
    >>> c1.pitchClasses
    [2, 9, 6, 2] 

**pitchClassCardinality**

    Return the number of unique pitch classes 

    >>> c1 = Chord(["D4", "A4", "F#5", "D6"])
    >>> c1.pitchClassCardinality
    3 

**orderedPitchClasses**

    Return a pitch class representation ordered by pitch class and removing redundancies. This is a traditional pitch class set 

    >>> c1 = Chord(["D4", "A4", "F#5", "D6"])
    >>> c1.orderedPitchClasses
    [2, 6, 9] 

**normalFormString**

    

    >>> c1 = Chord(['f#', 'e-', 'g'])
    >>> c1.normalFormString
    '<034>' 

**normalForm**

    

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.normalForm
    [0, 3, 7] 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.normalForm
    [0, 4, 7] 

**mx**

    Returns a List of mxNotes Attributes of notes are merged from different locations: first from the duration objects, then from the pitch objects. Finally, GeneralNote attributes are added 

    >>> a = Chord()
    >>> a.quarterLength = 2
    >>> b = pitch.Pitch('A-')
    >>> c = pitch.Pitch('D-')
    >>> d = pitch.Pitch('E-')
    >>> e = a.pitches = [b, c, d]
    >>> len(e)
    3 
    >>> mxNoteList = a.mx
    >>> len(mxNoteList) # get three mxNotes
    3 
    >>> mxNoteList[0].get('chord')
    False 
    >>> mxNoteList[1].get('chord')
    True 
    >>> mxNoteList[2].get('chord')
    True 

**multisetCardinality**

    Return the number of pitch classes, regardless of redundancy. 

    >>> c1 = Chord(["D4", "A4", "F#5", "D6"])
    >>> c1.multisetCardinality
    4 

**lily**

    The name of the note as it would appear in Lilypond format. 

**isPrimeFormInversion**

    Get the Forte class index number. Possible rename forteIndex 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.isPrimeFormInversion
    False 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.isPrimeFormInversion
    True 

**intervalVectorString**

    

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.intervalVectorString
    '<001110>' 

**intervalVector**

    Get the Forte class index number. Possible rename forteIndex 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.intervalVector
    [0, 0, 1, 1, 1, 0] 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.intervalVector
    [0, 0, 1, 1, 1, 0] 

**hasZRelation**

    Get the Z-relation status 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.hasZRelation
    False 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.hasZRelation
    False 

**forteClassTnI**

    Return a forte class name under TnI classification 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.forteClassTnI
    '3-11' 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.forteClassTnI
    '3-11' 

**forteClassTn**

    Return a forte class name 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.forteClass
    '3-11A' 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.forteClass
    '3-11B' 

**forteClassNumber**

    Get the Forte class index number. Possible rename forteIndex 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.forteClassNumber
    11 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.forteClassNumber
    11 

**forteClass**

    Return a forte class name 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.forteClass
    '3-11A' 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.forteClass
    '3-11B' 

**commonName**

    Get the common name of the TN set class. Possible rename forteIndex 

    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.commonName
    ['minor triad'] 
    >>> c2 = Chord(['c', 'e', 'g'])
    >>> c2.commonName
    ['major triad'] 

**chordTablesAddress**

    

    >>> c = Chord(["C4", "E4", "G#4"])
    >>> c.chordTablesAddress
    (3, 12, 0) 

Methods
~~~~~~~


Inherited from base.Music21Object (of module :ref:`moduleBase`): **write()**, **show()**, **searchParent()**, **isClass()**, **id()**, **getOffsetBySite()**, **duration()**, **contexts()**, **addLocationAndParent()**


Inherited from note.GeneralNote (of module :ref:`moduleNote`): **splitAtDurations()**, **isChord()**, **compactNoteInfo()**, **clearDurations()**, **appendDuration()**, **addLyric()**


Inherited from note.NotRest (of module :ref:`moduleNote`): **splitNoteAtPoint()**


Locally Defined:

**sortFrequencyAscending()**

    Same as above, but uses a note's frequency to determine height; so that C# would be below D- in 1/4-comma meantone, equal in equal temperament, but below it in (most) just intonation types. 

**sortDiatonicAscending()**

    After talking with Daniel Jackson, let's try to make the chord object as immutable as possible, so we return a new Chord object with the notes arranged from lowest to highest The notes are sorted by Scale degree and then by Offset (so F## sorts below G-). Notes that are the identical pitch retain their order 

    >>> cMajUnsorted = Chord(['E4', 'C4', 'G4'])
    >>> cMajSorted = cMajUnsorted.sortDiatonicAscending()
    >>> cMajSorted.pitches[0].name
    'C' 

**sortChromaticAscending()**

    Same as sortAscending but notes are sorted by midi number, so F## sorts above G-. 

**sortAscending()**


**semiClosedPosition()**


**seekChordTablesAddress()**

    Utility method to return the address to the chord table. Table addresses are TN based three character codes: cardinaltiy, Forte index number, inversion Inversion is either 0 (for symmetrical) or -1/1 NOTE: time consuming, and only should be run when necessary. 

    >>> c1 = Chord(['c3'])
    >>> c1.orderedPitchClasses
    [0] 
    >>> c1.seekChordTablesAddress()
    (1, 1, 0) 
    >>> c1 = Chord(['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'b'])
    >>> c1.seekChordTablesAddress()
    (11, 1, 0) 
    >>> c1 = Chord(['c', 'e', 'g'])
    >>> c1.seekChordTablesAddress()
    (3, 11, -1) 
    >>> c1 = Chord(['c', 'e-', 'g'])
    >>> c1.seekChordTablesAddress()
    (3, 11, 1) 
    >>> c1 = Chord(['c', 'c#', 'd#', 'e', 'f#', 'g#', 'a#'])
    >>> c1.seekChordTablesAddress()
    (7, 34, 0) 
    >>> c1 = Chord(['c', 'c#', 'd'])
    >>> c1.seekChordTablesAddress()
    (3, 1, 0) 

**root()**

    Returns or sets the Root of the chord.  if not set, will run findRoot (q.v.) example: 

    >>> cmaj = Chord (['C', 'E', 'G'])
    >>> cmaj.root() # returns C
    C 

**numNotes()**

    Returns the number of notes in the chord 

**isTriad()**

    returns True or False "Contains vs. Is:" A dominant-seventh chord is NOT a triad. returns True if the chord contains at least one Third and one Fifth and all notes are equivalent to either of those notes. Only returns True if triad is spelled correctly. example: 

    >>> cchord = Chord (['C', 'E', 'G'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G'])
    >>> cchord.isTriad() # returns True
    True 
    >>> other.isTriad()
    False 

**isSeventh()**

    Returns True if chord contains at least one of each of Third, Fifth, and Seventh, and every note in the chord is a Third, Fifth, or Seventh, such that there are no repeated scale degrees (ex: E and E-). Else return false. example: 

    >>> cchord = Chord (['C', 'E', 'G', 'B'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G', 'B'])
    >>> cchord.isSeventh() # returns True
    True 
    >>> other.isSeventh() # returns False
    False 

**isRest()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isNote()**

    bool(x) -> bool Returns True when the argument x is true, False otherwise. The builtins True and False are the only two instances of the class bool. The class bool is a subclass of the class int, and cannot be subclassed. 

**isMinorTriad()**

    Returns True if chord is a Minor Triad, that is, if it contains only notes that are either in unison with the root, a minor third above the root, or a perfect fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E-', 'G'])
    >>> other = Chord (['C', 'E', 'G'])
    >>> cchord.isMinorTriad() # returns True
    True 
    >>> other.isMinorTriad() # returns False
    False 

**isMajorTriad()**

    Returns True if chord is a Major Triad, that is, if it contains only notes that are either in unison with the root, a major third above the root, or a perfect fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E', 'G'])
    >>> other = Chord (['C', 'G'])
    >>> cchord.isMajorTriad() # returns True
    True 
    >>> other.isMajorTriad() # returns False
    False 

**isHalfDiminishedSeventh()**

    Returns True if chord is a Half Diminished Seventh, that is, if it contains only notes that are either in unison with the root, a minor third above the root, a diminished fifth, or a major seventh above the root. Additionally, must contain at least one of each third, fifth, and seventh above the root. Chord must be spelled correctly. Otherwise returns false. 

    >>> c1 = Chord(['C4','E-4','G-4','B-4'])
    >>> c1.isHalfDiminishedSeventh()
    True 
    Incorrectly spelled chords are not considered half-diminished sevenths 
    >>> c2 = Chord(['C4','E-4','G-4','A#4'])
    >>> c2.isHalfDiminishedSeventh()
    False 
    Nor are incomplete chords 
    >>> c3 = Chord(['C4', 'G-4','B-4'])
    >>> c3.isHalfDiminishedSeventh()
    False 

**isFalseDiminishedSeventh()**

    Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord MAY BE SPELLED INCORRECTLY. Otherwise returns false. 

**isDominantSeventh()**

    Returns True if chord is a Dominant Seventh, that is, if it contains only notes that are either in unison with the root, a major third above the root, a perfect fifth, or a major seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

    >>> a = Chord(['b', 'g', 'd', 'f'])
    >>> a.isDominantSeventh()
    True 

**isDiminishedTriad()**

    Returns True if chord is a Diminished Triad, that is, if it contains only notes that are either in unison with the root, a minor third above the root, or a diminished fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

    >>> cchord = Chord (['C', 'E-', 'G-'])
    >>> other = Chord (['C', 'E-', 'F#'])
    >>> cchord.isDiminishedTriad() #returns True
    True 
    >>> other.isDiminishedTriad() #returns False
    False 

**isDiminishedSeventh()**

    Returns True if chord is a Diminished Seventh, that is, if it contains only notes that are either in unison with the root, a minor third above the root, a diminished fifth, or a minor seventh above the root. Additionally, must contain at least one of each third and fifth above the root. Chord must be spelled correctly. Otherwise returns false. 

    >>> a = Chord(['c', 'e-', 'g-', 'b--'])
    >>> a.isDiminishedSeventh()
    True 

**isAugmentedTriad()**

    Returns True if chord is an Augmented Triad, that is, if it contains only notes that are either in unison with the root, a major third above the root, or an augmented fifth above the root. Additionally, must contain at least one of each third and fifth above the root. Chord might NOT seem to have to be spelled correctly because incorrectly spelled Augmented Triads are usually augmented triads in some other inversion (e.g. C-E-Ab is a 2nd inversion aug triad; C-Fb-Ab is 1st inversion).  However, B#-Fb-Ab does return false as expeccted). Returns false if is not an augmented triad. 

    >>> import music21.chord
    >>> c = music21.chord.Chord(["C4", "E4", "G#4"])
    >>> c.isAugmentedTriad()
    True 
    >>> c = music21.chord.Chord(["C4", "E4", "G4"])
    >>> c.isAugmentedTriad()
    False 
    Other spellings will give other roots! 
    >>> c = music21.chord.Chord(["C4", "E4", "A-4"])
    >>> c.isAugmentedTriad()
    True 
    >>> c.root()
    A-4 
    >>> c = music21.chord.Chord(["C4", "F-4", "A-4"])
    >>> c.isAugmentedTriad()
    True 
    >>> c = music21.chord.Chord(["B#4", "F-4", "A-4"])
    >>> c.isAugmentedTriad()
    False 

**inversionName()**

    Returns an integer representing the common abbreviation for the inversion the chord is in. If chord is not in a common inversion, returns None. 

    >>> a = Chord(['g', 'b', 'd', 'f'])
    >>> a.inversionName()
    43 

**inversion()**

    returns an integer representing which standard inversion the chord is in. Chord does not have to be complete, but determines the inversion by looking at the relationship of the bass note to the root. 

    >>> a = Chord(['g', 'b', 'd', 'f'])
    >>> a.inversion()
    2 

**hasThird()**

    Shortcut for hasScaleX(3) 

**hasSpecificX()**

    Exactly like hasScaleX, except it returns the interval itself instead of the number of semitones. example: 

    >>> cmaj = Chord (['C', 'E', 'G'])
    >>> cmaj.hasScaleX(3) #will return the interval between C and E
    4 
    >>> cmaj.hasScaleX(5) #will return the interval between C and G
    7 
    >>> cmaj.hasScaleX(6) #will return False
    False 

**hasSeventh()**

    Shortcut for hasScaleX(7) 

**hasScaleX()**

    Each of these returns the number of semitones above the root that the third, fifth, etc., of the chord lies, if there exists one.  Or False if it does not exist. You can optionally specify a note.Note object to try as the root.  It does not change the Chord.root object.  We use these methods to figure out what the root of the triad is. Currently there is a bug that in the case of a triply diminished third (e.g., "c" => "e----"), this function will incorrectly claim no third exists.  Perhaps this be construed as a feature. In the case of chords such as C, E-, E, hasThird will return 3, not 4, nor a list object (3,4).  You probably do not want to be using tonal chord manipulation functions on chords such as these anyway. note.Note that in Chord, we're using "Scale" to mean a diatonic scale step. It will not tell you if a chord has a specific scale degree in another scale system.  That functionality might be added to scale.py someday. example: 

    >>> cchord = Chord (['C', 'E', 'E-', 'G'])
    >>> cchord.hasScaleX(3) #
    4 
    >>> cchord.hasScaleX(5) # will return 7
    7 
    >>> cchord.hasScaleX(6) # will return False
    False 

**hasRepeatedScaleX()**

    Returns True if scaleDeg above testRoot (or self.root()) has two or more different notes (such as E and E-) in it.  Otherwise returns false. example: 

    >>> cchord = Chord (['C', 'E', 'E-', 'G'])
    >>> cchord.hasRepeatedScaleX(3) # returns true
    True 

**hasFifth()**

    Shortcut for hasScaleX(5) 

**hasAnyRepeatedScale()**

    Returns True if for any scale degree there are two or more different notes (such as E and E-) in the chord. If there are no repeated scale degrees, return false. example: 

    >>> cchord = Chord (['C', 'E', 'E-', 'G'])
    >>> other = Chord (['C', 'E', 'F-', 'G'])
    >>> cchord.hasAnyRepeatedScale()
    True 
    >>> other.hasAnyRepeatedScale() # returns false (chromatically identical notes of different scale degrees do not count.
    False 

**findRoot()**

    Looks for the root by finding the note with the most 3rds above it Generally use root() instead, since if a chord doesn't know its root, root() will run findRoot() automatically. example: 

    >>> cmaj = Chord (['C', 'E', 'G'])
    >>> cmaj.findRoot() # returns C
    C 

**findBass()**

    Returns the lowest note in the chord The only time findBass should be called is by bass() when it is figuring out what the bass note of the chord is. Generally call bass() instead example: 

    >>> cmaj = Chord (['C4', 'E3', 'G4'])
    >>> cmaj.findBass() # returns E3
    E3 

**determineType()**

    returns an abbreviation for the type of chord it is. Add option to add inversion name to abbreviation? TODO: determine permanent designation abbreviation for every type of chord and inversion 

    >>> a = Chord(['a', 'c#', 'e'])
    >>> a.determineType()
    'Major Triad' 
    >>> a = Chord(['g', 'b', 'd', 'f'])
    >>> a.determineType()
    'Dominant Seventh' 

**containsTriad()**

    returns True or False if there is no triad above the root. "Contains vs. Is": A dominant-seventh chord contains a triad. example: 

    >>> cchord = Chord (['C', 'E', 'G'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G'])
    >>> cchord.containsTriad() #returns True
    True 
    >>> other.containsTriad() #returns True
    True 

**containsSeventh()**

    returns True if the chord contains at least one of each of Third, Fifth, and Seventh. raises an exception if the Root can't be determined 

    >>> cchord = Chord (['C', 'E', 'G', 'B'])
    >>> other = Chord (['C', 'D', 'E', 'F', 'G', 'B'])
    >>> cchord.containsSeventh() # returns True
    True 
    >>> other.containsSeventh() # returns True
    True 

**closedPosition()**

    returns a new Chord object with the same pitch classes, but now in closed position 

    >>> chord1 = Chord(["C#4", "G5", "E6"])
    >>> chord2 = chord1.closedPosition()
    >>> print chord2.lily.value
    <cis' e' g'>4 

**checkDurationSanity()**

    TO WRITE Checks to make sure all notes have the same duration Does not run automatically 

**canBeTonic()**

    

    

    >>> a = Chord(['g', 'b', 'd', 'f'])
    >>> a.canBeTonic()
    False 
    >>> a = Chord(['g', 'b', 'd'])
    >>> a.canBeTonic()
    True 

**canBeDominantV()**

    

    

    >>> a = Chord(['g', 'b', 'd', 'f'])
    >>> a.canBeDominantV()
    True 

**bass()**

    returns the bass note or sets it to note. Usually defined to the lowest note in the chord, but we want to be able to override this.  You might want an implied bass for instance...  v o9. example: 

    >>> cmaj = Chord(['C', 'E', 'G'])
    >>> cmaj.bass() # returns C
    C 

**areZRelations()**

    Check of chord other is also a z relations 

    >>> c1 = Chord(["C", "c#", "e", "f#"])
    >>> c2 = Chord(["C", "c#", "e-", "g"])
    >>> c3 = Chord(["C", "c#", "f#", "g"])
    >>> c1.areZRelations(c2)
    True 
    >>> c1.areZRelations(c3)
    False 


Class Duration
--------------

Inherits from: duration.DurationCommon (of module :ref:`moduleDuration`), object

Durations are one of the most important objects in music21.  A Duration represents a span of musical time measurable in terms of quarter notes (or in advanced usage other units).  For instance, "57 quarter notes" or "dotted half tied to quintuplet sixteenth note" or simply "quarter note" 

A Duration is made of one or more DurationUnits. Multiple DurationUnits in a single Duration may be used to express tied notes, or may be used to split duration across barlines or beam groups. Some Durations are not expressable as a single notation unit. 

Attributes
~~~~~~~~~~

**linkages**

Properties
~~~~~~~~~~


Locally Defined:

**type**

    Get the duration type. 

**tuplets**


**quarterLength**

    Can be the same as the base class. 

**mx**

    Returns a list of one or more musicxml.Note() objects with all rhythms and ties necessary. mxNote objects are incompletely specified, lacking full representation and information on pitch, etc. 

    >>> a = Duration()
    >>> a.quarterLength = 3
    >>> b = a.mx
    >>> len(b) == 1
    True 
    >>> isinstance(b[0], musicxmlMod.Note)
    True 
    >>> a = Duration()
    >>> a.quarterLength = .33333333
    >>> b = a.mx
    >>> len(b) == 1
    True 
    >>> isinstance(b[0], musicxmlMod.Note)
    True 

**musicxml**

    Return a complete MusicXML string with defaults. 

**lily**

    Simple lily duration: does not include tuplets These are taken care of in the lily processing in stream.Stream since lilypond requires tuplets to be in groups 

    

**isComplex**


**dots**

    Returns the number of dots in the Duration if it is a simple Duration.  Otherwise raises error. 

**components**


Methods
~~~~~~~


Inherited from duration.DurationCommon (of module :ref:`moduleDuration`): **aggregateTupletRatio()**


Locally Defined:

**write()**

    Write a file in the given format (default, musicxml) A None file path will result in temporary file 

**updateQuarterLength()**

    Look to components and determine quarter length. 

**sliceComponentAtPosition()**

    Given a quarter position within a component, divide that component into two components. 

    >>> a = Duration()
    >>> a.clear() # need to remove default
    >>> components = []
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
    >>> a.addDuration(Duration('quarter'))
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

**show()**

    This might need to return the file path. 

**fill()**

    Utility method for testing; a quick way to fill components. This will remove any exisiting values. 

**expand()**

    Make a duration notatable by partitioning it into smaller units (default qLenDiv = 4 (whole note)).  uses partitionQuarterLength 

**consolidate()**

    Given a Duration with multiple components, consolidate into a single Duration. This can only be based on quarterLength; this is destructive: information is lost from coponents. This cannot be done for all Durations. 

    >>> a = Duration()
    >>> a.fill(['quarter', 'half', 'quarter'])
    >>> a.quarterLength
    4.0 
    >>> len(a.components)
    3 
    >>> a.consolidate()
    >>> a.quarterLength
    4.0 
    >>> len(a.components)
    1 
    But it gains a type! 
    >>> a.type
    'whole' 

**componentStartTime()**

    For a valid component index value, this returns the quarter note offset at which that component would start. This does not handle fractional arguments. 

    >>> components = []
    >>> for x in [1,1,1]:
    ...    components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    >>> a.updateQuarterLength()
    >>> a.quarterLength
    3.0 
    >>> a.componentStartTime(0)
    0.0 
    >>> a.componentStartTime(1)
    1.0 

**componentIndexAtQtrPosition()**

    returns the index number of the duration component sounding at the given quarter position. Note that for 0 and the last value, the object is returned. 

    >>> components = []
    TODO: remove "for x in [1,1,1]" notation; it's confusing (Perl-like) 
    better is just to copy and paste three times.  Very easy to see what 
    is happening. 
    >>> for x in [1,1,1]:
    ...   components.append(Duration('quarter')) 
    >>> a = Duration()
    >>> a.components = components
    >>> a.updateQuarterLength()
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

**clear()**

    Permit all componets to be removed. (It is not clear yet if this is needed) 

    >>> a = Duration()
    >>> a.quarterLength = 4
    >>> a.type
    'whole' 
    >>> a.clear()
    >>> a.quarterLength
    0.0 
    >>> a.type
    'zero' 

**appendTuplet()**


**addDuration()**

    Add a DurationUnit or a Duration's components to this Duration. 

    >>> a = Duration('quarter')
    >>> b = Duration('quarter')
    >>> a.addDuration(b)
    >>> a.quarterLength
    2.0 
    >>> a.type
    'complex' 


Class LilyString
----------------

Inherits from: object


Attributes
~~~~~~~~~~

**value**

Properties
~~~~~~~~~~


Locally Defined:

**wrappedValue**

    returns a value that is wrapped with { } if it doesn't contain a score element so that it can run through lilypond 

Methods
~~~~~~~


Locally Defined:

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


