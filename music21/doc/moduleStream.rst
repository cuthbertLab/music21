music21.stream
==============

Class Element
-------------

An element wraps an object so that the same object can be positioned multiple times within a stream. also can be used so that non-music21 objects can be included in a Stream. Calls to Elements automatically call the embedded object 

Public Attributes
~~~~~~~~~~~~~~~~~

+ contexts
+ groups
+ obj

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _unlinkedDuration

Public Methods
~~~~~~~~~~~~~~

**contexts()**

    No documentation.

**copy()**

    Makes a copy of this element with a reference to the SAME object but with unlinked offset, id, priority and a cloned Groups object 

    >>> import note
    >>> import duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.copy()
    >>> b.offset = duration.Duration("half")

    

**deepcopy()**

    similar to copy but also does a deepcopy of the object as well. (name is all lowercase to go with copy.deepcopy convention) 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.deepcopy()
    >>> b.offset = duration.Duration("half")
    >>> a.obj is b.obj
    False 
    >>> a.obj.accidental = "-"
    >>> b.obj.name
    'A' 
    >>> a.offset
    1.0 
    >>> b.offset
    2.0 
    >>> a.groups[0] = "bassoon"
    >>> ("flute" in a.groups, "flute" in b.groups)
    (False, True) 

**duration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    >>> import note
    >>> el1 = Element()
    >>> n = note.Note('F#')
    >>> n.quarterLength = 2
    >>> n.duration.quarterLength
    2.0 
    >>> el1.obj = n
    >>> el1.duration.quarterLength
    2.0 
    ADVANCED FEATURE TO SET DURATION OF ELEMENTS SEPARATELY 
    >>> import music21.key
    >>> ks1 = Element(music21.key.KeySignature())
    >>> ks1.obj.duration
    Traceback (most recent call last): 
    AttributeError: 'KeySignature' object has no attribute 'duration' 
    >>> import duration
    >>> ks1.duration = duration.Duration("whole")
    >>> ks1.duration.quarterLength
    4.0 
    >>> ks1.obj.duration  # still not defined
    Traceback (most recent call last): 
    AttributeError: 'KeySignature' object has no attribute 'duration' 

**id()**

    No documentation.

**isClass()**

    Returns true if the object embedded is a particular class. Used by getElementsByClass in Stream 

    >>> import note
    >>> a = Element(None)
    >>> a.isClass(note.Note)
    False 
    >>> a.isClass(types.NoneType)
    True 
    >>> b = Element(note.Note('A4'))
    >>> b.isClass(note.Note)
    True 
    >>> b.isClass(types.NoneType)
    False 

**isTwin()**

    a weaker form of equality.  a.isTwin(b) is true if a and b store either the same object OR objects that are equal and a.groups == b.groups and a.id == b.id (or both are none) and duration are equal. but does not require position, priority, or parent to be the same In other words, is essentially the same object in a different context 

    >>> import note
    >>> aE = Element(obj = note.Note("A-"))
    >>> aE.id = "aflat-Note"
    >>> aE.groups.append("out-of-range")
    >>> aE.offset = 4.0
    >>> aE.priority = 4
    >>> bE = aE.copy()
    >>> aE is bE
    False 
    >>> aE == bE
    True 
    >>> aE.isTwin(bE)
    True 
    >>> bE.offset = 14.0
    >>> bE.priority = -4
    >>> aE == bE
    False 
    >>> aE.isTwin(bE)
    True 

**offset()**

    No documentation.

**parent()**

    No documentation.

**priority()**

    No documentation.

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_duration()**

    No documentation.

**_getDuration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    >>> import note
    >>> el1 = Element()
    >>> n = note.Note('F#')
    >>> n.quarterLength = 2
    >>> n.duration.quarterLength
    2.0 
    >>> el1.obj = n
    >>> el1.duration.quarterLength
    2.0 
    ADVANCED FEATURE TO SET DURATION OF ELEMENTS SEPARATELY 
    >>> import music21.key
    >>> ks1 = Element(music21.key.KeySignature())
    >>> ks1.obj.duration
    Traceback (most recent call last): 
    AttributeError: 'KeySignature' object has no attribute 'duration' 
    >>> import duration
    >>> ks1.duration = duration.Duration("whole")
    >>> ks1.duration.quarterLength
    4.0 
    >>> ks1.obj.duration  # still not defined
    Traceback (most recent call last): 
    AttributeError: 'KeySignature' object has no attribute 'duration' 

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


Class Measure
-------------

No documentation.

Public Attributes
~~~~~~~~~~~~~~~~~

+ contexts
+ filled
+ groups
+ internalbarlines
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ leftbarline
+ measureNumber
+ measureNumberSuffix
+ obj
+ rightbarline
+ timeDependentDirections
+ timeDependentDirectionsTime
+ timeIndependentDirections
+ timeSignature
+ timeSignatureIsNew

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _cache
+ _elements
+ _index
+ _unlinkedDuration

Public Methods
~~~~~~~~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note('A-'), range(30))
    >>> a.repeatCopy(note.Rest(), range(30, 60))
    >>> a.addGroupForElements('flute')
    >>> a[0].groups
    ['flute'] 
    >>> a.addGroupForElements('quietTime', note.Rest)
    >>> a[0].groups
    ['flute'] 
    >>> a[50].groups
    ['flute', 'quietTime'] 
    >>> a[1].groups.append('quietTime') # set one note to it
    >>> a[1].step = "B"
    >>> b = a.getElementsByGroup('quietTime')
    >>> len(b)
    31 
    >>> c = b.getElementsByClass(note.Note)
    >>> len(c)
    1 
    >>> c[0].name
    'B-' 

    

**addLeftBarline()**

    No documentation.

**addNext()**

    Add an objects or Elements (including other Streams) to the Stream (or multiple if passed a list) with offset equal to the highestTime (that is the latest "release" of an object) plus any offset in the Element or Stream to be added.  If that offset is zero (or a bare object is added) then this object will directly after the last Element ends. runs fast for multiple addition and will preserve isSorted if True 

    >>> a = Stream()
    >>> notes = []
    >>> for x in range(0,3):
    ...     n = note.Note('G#') 
    ...     n.duration.quarterLength = 3 
    ...     notes.append(n) 
    >>> a.addNext(notes[0])
    >>> a.highestOffset, a.highestTime
    (0.0, 3.0) 
    >>> a.addNext(notes[1])
    >>> a.highestOffset, a.highestTime
    (3.0, 6.0) 
    >>> a.addNext(notes[2])
    >>> a.highestOffset, a.highestTime
    (6.0, 9.0) 
    >>> notes2 = []
    >>> # since notes are not embedded in Elements here, their offset
    >>> # changes when added to a stream!
    >>> for x in range(0,3):
    ...     n = notes[x].deepcopy() 
    ...     n.offset = 0 
    ...     notes2.append(n) 
    >>> a.addNext(notes2) # add em all again
    >>> a.highestOffset, a.highestTime
    (15.0, 18.0) 
    >>> a.isSequence()
    True 

**addRepeat()**

    No documentation.

**addRightBarline()**

    No documentation.

**addTimeDependentDirection()**

    No documentation.

**append()**

    Add a (sub)Stream, Element, or object (wrapped into a default element) to the element Stream. 

    >>> a = Stream()
    >>> a.append(None)
    >>> a.append(music21.note.Note('G#'))
    >>> len(a)
    2 
    QUESTION: should this also add an entry to the parent and context 
    attributes (if any) in the object? 

**bestClef()**

    Cheat method: returns the clef that is the best fit for the sequence 

    >>> a = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(60,72)) 
    ...    a.append(n) 
    >>> b = a.bestClef()
    >>> b.line
    2 
    >>> b.sign
    'G' 
    >>> c = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(35,55)) 
    ...    c.append(n) 
    >>> d = c.bestClef()
    >>> d.line
    4 
    >>> d.sign
    'F' 

**contexts()**

    No documentation.

**copy()**

    Makes a copy of this element with a reference to the SAME object but with unlinked offset, id, priority and a cloned Groups object 

    >>> import note
    >>> import duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.copy()
    >>> b.offset = duration.Duration("half")

    

**deepcopy()**

    similar to copy but also does a deepcopy of the object as well. (name is all lowercase to go with copy.deepcopy convention) 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.deepcopy()
    >>> b.offset = duration.Duration("half")
    >>> a.obj is b.obj
    False 
    >>> a.obj.accidental = "-"
    >>> b.obj.name
    'A' 
    >>> a.offset
    1.0 
    >>> b.offset
    2.0 
    >>> a.groups[0] = "bassoon"
    >>> ("flute" in a.groups, "flute" in b.groups)
    (False, True) 

**duration()**

    Returns the total duration of the Stream, from the beginning of the stream until the end of the final element. May be set independently by supplying a Duration object. 

    >>> a = Stream()
    >>> q = note.QuarterNote()
    >>> a.repeatCopy(q, [0,1,2,3])
    >>> a.highestOffset
    3.0 
    >>> a.highestTime
    4.0 
    >>> a.duration.quarterLength
    4.0 
    >>> # Advanced usage: overriding the duration
    >>> newDuration = duration.Duration("half")
    >>> newDuration.quarterLength
    2.0 
    >>> a.duration = newDuration
    >>> a.duration.quarterLength
    2.0 
    >>> a.highestTime # unchanged
    4.0 

**elements()**

    No documentation.

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where all no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q)
    5 
    >>> len(q.flat)
    25 
    >>> q.flat[24].offset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**getElementsByClass()**

    return a list of all Elements that match the className 

    >>> a = Stream()
    >>> a.fillNone(10) # adds Elements with obj == None
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     a.append(n) 
    >>> found = a.getElementsByClass(note.Note)
    >>> len(found)
    4 
    >>> found[0].pitch.accidental.name
    'sharp' 
    >>> b = Stream()
    >>> b.repeatCopy(None, range(10))
    >>> a.append(b)
    >>> # here, it gets elements from within a stream
    >>> # this probably should not do this, as it is one layer lower
    >>> found = a.getElementsByClass(types.NoneType)
    >>> len(found)
    10 
    >>> c = Stream()
    >>> c.append(note.Note('A-'))
    >>> d = Stream()
    >>> d.repeatCopy(None, range(10))
    >>> c.append(d)
    >>> a.append(c)
    >>> found = a.getElementsByClass(types.NoneType)
    >>> len(found) # if recursive, should get 20
    10 
    >>> found = a.flat.getElementsByClass(types.NoneType)
    >>> len(found)  # this is not the right answer
    30 

**getElementsByGroup()**

    No documentation.

**getElementsById()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

**getElementsByOffset()**

    Return a list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(10)) # adds Elements with obj == None
    >>> b = a.getElementsByOffset(4,6)
    >>> len(b)
    3 
    >>> b = a.getElementsByOffset(4,5.5)
    >>> len(b)
    2 
    >>> a = Stream()
    >>> n = note.Note('G')
    >>> n.quarterLength = .5
    >>> a.repeatCopy(n, range(8))
    >>> b = Stream()
    >>> b.repeatCopy(a, [0, 3, 6])
    >>> c = b.getElementsByOffset(2,6.9)
    >>> len(c)
    2 
    >>> c = b.flat.getElementsByOffset(2,6.9)
    >>> len(c)
    10 

**getGroups()**

    Get a dictionary for each groupId and the count of instances. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> a.repeatCopy(n, range(30))
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getNotes()**

    No documentation.

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements taht have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('quarter') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> d = a.getOverlaps(True, False)
    >>> len(d)
    0 
    >>> d = a.getOverlaps(True, True) # including coincident boundaries
    >>> len(d)
    1 
    >>> len(d[0])
    4 
    >>> a = Stream()
    >>> for x in [0,0,0,0,13,13,13]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('half') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> d = a.getOverlaps()
    >>> len(d[0])
    4 
    >>> len(d[13])
    3 
    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     e = Element(n) 
    ...     e.offset = x * 1 
    ...     a.append(e) 
    ... 
    >>> # default is to not include coincident boundaries
    >>> d = a.getOverlaps()
    >>> len(d[0])
    7 

**getSimultaneous()**

    Find and return any elements that start at the same time. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 0 
    ...     a.append(n) 
    ... 
    >>> b = a.getSimultaneous()
    >>> len(b[0]) == 4
    True 
    >>> c = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**highestOffset()**

    Get start time of element with the highest offset in the Stream 

    >>> a = Stream()
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.highestOffset
    12.0 

    

**highestTime()**

    returns the max(el.offset + el.duration.quarterLength) over all elements, usually representing the last "release" in the Stream. The duration of a Stream is usually equal to the highestTime expressed as a Duration object, but can be set separately.  See below. 

**id()**

    No documentation.

**insertAtOffset()**

    Append an object with a given offset. Wrap in an Element and set offset time. 

    >>> a = Stream()
    >>> a.insertAtOffset(None, 32)
    >>> a._getHighestOffset()
    32.0 

**isClass()**

    Returns true if the Stream or Stream Subclass is a particular class or subclasses that class. Used by getElementsByClass in Stream 

    >>> a = Stream()
    >>> a.isClass(note.Note)
    False 
    >>> a.isClass(Stream)
    True 
    >>> b = Measure()
    >>> b.isClass(Measure)
    True 
    >>> b.isClass(Stream)
    True 

**isGapless()**

    No documentation.

**isSequence()**

    A stream is a sequence if it has no overlaps. TODO: check that co-incident boundaries are properly handled 

    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     e = Element(n) 
    ...     e.offset = x * 1 
    ...     a.append(e) 
    ... 
    >>> a.isSequence()
    False 

**isTwin()**

    a weaker form of equality.  a.isTwin(b) is true if a and b store either the same object OR objects that are equal and a.groups == b.groups and a.id == b.id (or both are none) and duration are equal. but does not require position, priority, or parent to be the same In other words, is essentially the same object in a different context 

    >>> import note
    >>> aE = Element(obj = note.Note("A-"))
    >>> aE.id = "aflat-Note"
    >>> aE.groups.append("out-of-range")
    >>> aE.offset = 4.0
    >>> aE.priority = 4
    >>> bE = aE.copy()
    >>> aE is bE
    False 
    >>> aE == bE
    True 
    >>> aE.isTwin(bE)
    True 
    >>> bE.offset = 14.0
    >>> bE.priority = -4
    >>> aE == bE
    False 
    >>> aE.isTwin(bE)
    True 

**lily()**

    Returns the stream translated into Lilypond format. 

**measureNumberWithSuffix()**

    No documentation.

**mx()**

    This does not work yet, but something like this could work 

    

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**offset()**

    No documentation.

**parent()**

    No documentation.

**priority()**

    No documentation.

**recurseRepr()**

    No documentation.

**repeatCopy()**

    Given an object, create many copies at the possitioins specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatCopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**

    No documentation.

**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note('A-'), range(30))
    >>> a.repeatCopy(note.Note('E-'), range(30, 60))
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.getElementsById()
    >>> len(ref)
    1 
    >>> ref['flute']
    60 
    >>> b = Stream()
    >>> b.repeatCopy(None, range(30))
    >>> b.repeatCopy(note.Note('E-'), range(30, 60))
    >>> b.setIdForElements('flute', note.Note)
    >>> a[0].id
    'flute' 
    >>> ref = b.getElementsById()
    >>> ref['flute']
    30 

    

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**sorted()**

    returns a new Stream where all the elements are sorted according to offset time if this stream is not flat, then only the highest elements are sorted.  To sort all, run myStream.flat.sorted ## TODO: CLEF ORDER RULES, etc. 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> farRight = note.Note("E")
    >>> farRight.priority = 5
    >>> farRight.offset = 2.0
    >>> y.append(farRight)
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; ' 
    >>> z = y.sorted
    >>> g = ""
    >>> for myElement in z:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> z[2].name, z[3].name
    ('C#', 'E') 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_consolidateLayering()**

    Given elementsSorted and a map of equal lenght with lists of index values that meet a given condition (overlap or simultaneities), organize into a dictionary by the relevant or first offset 

**_durSpanOverlap()**

    Compare two durSpans and find overlaps; optionally, includ coincident boundaries. a and b are sorted to permit any ordering. If an element ends at 3.0 and another starts at 3.0, this may or may not be considered an overlap. The includeCoincidentEnds parameter determines this behaviour, where ending and starting 3.0 being a type of overlap is set by the includeCoincidentBoundaries being True. 

    >>> a = Stream()
    >>> a._durSpanOverlap([0, 10], [11, 12], False)
    False 
    >>> a._durSpanOverlap([11, 12], [0, 10], False)
    False 
    >>> a._durSpanOverlap([0, 3], [3, 6], False)
    False 
    >>> a._durSpanOverlap([0, 3], [3, 6], True)
    True 

**_duration()**

    No documentation.

**_elementsChanged()**

    call anytime _elements is changed -- should only be called by this package... 

**_findLayering()**

    Find any elements in an elementsSorted list that have simultaneities or durations that cause overlaps. Returns two lists. Each list contains a list for each element in elementsSorted. If that elements has overalps or simultaneities, all index values that match are included in that list. See testOverlaps, in unit tests, for examples. 

    

    

**_getDurSpan()**

    Given elementsSorted, create a lost of parallel values that represent dur spans, or start and end times. Assume durations of None imply 0 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(5))
    >>> a._getDurSpan(a.flat)
    [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0)] 

**_getDuration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    

**_getElements()**

    No documentation.

**_getFlat()**

    returns a new Stream where all no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q)
    5 
    >>> len(q.flat)
    25 
    >>> q.flat[24].offset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**_getFlatOrSemiFlat()**

    No documentation.

**_getHighestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.highestOffset
    40.0 
    >>> q.flat.highestOffset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.flat.highestOffset
    444.0 

**_getHighestTime()**

    

    >>> n = note.Note('A-')
    >>> n.quarterLength = 3
    >>> p = Stream()
    >>> p.repeatCopy(n, range(5))
    >>> p.highestTime # 4 + 3
    7.0 
    >>> q = Stream()
    >>> q.repeatCopy(p, [20, 0, 10, 30, 40]) # insert out of order
    >>> len(q.flat)
    25 
    >>> q.highestTime # this works b/c the component Stream has an dur
    47.0 
    >>> q.flat.highestTime # 44 + 3
    47.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.highestTime
    447.0 
    >>> r.flat.highestTime
    447.0 
    >>> q.flat.highestOffset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.flat.highestOffset
    444.0 

**_getIsGapless()**

    No documentation.

**_getLily()**

    Returns the stream translated into Lilypond format. 

**_getMX()**

    This does not work yet, but something like this could work 

    

**_getOffset()**

    No documentation.

**_getParent()**

    No documentation.

**_getPriority()**

    No documentation.

**_getSemiFlat()**

    No documentation.

**_getSorted()**

    returns a new Stream where all the elements are sorted according to offset time if this stream is not flat, then only the highest elements are sorted.  To sort all, run myStream.flat.sorted ## TODO: CLEF ORDER RULES, etc. 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> farRight = note.Note("E")
    >>> farRight.priority = 5
    >>> farRight.offset = 2.0
    >>> y.append(farRight)
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; ' 
    >>> z = y.sorted
    >>> g = ""
    >>> for myElement in z:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> z[2].name, z[3].name
    ('C#', 'E') 

**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**

    No documentation.

**_parent()**

    No documentation.

**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**_setDuration()**

    Set the total duration of the Stream independently of the highestTime of the stream.  Useful to define the scope of the stream as independent of its constituted elements. If set to None, then the default behavior of computing automatically from highestTime is reestablished. 

**_setElements()**

    

    >>> a = Stream()
    >>> a.repeatCopy(None, range(10))
    >>> b = Stream()
    >>> b.repeatCopy(None, range(10))
    >>> b.offset = 6
    >>> c = Stream()
    >>> c.repeatCopy(None, range(10))
    >>> c.offset = 12
    >>> b.append(c)
    >>> b.isFlat
    False 
    >>> a.isFlat
    True 
    >>> a.elements = b.elements
    >>> a.isFlat
    False 

**_setLily()**

    Sets the Lilypond output for the stream. Overrides what is obtained from get_lily. 

**_setMX()**

    

    

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


Class Score
-----------

Handle importing a musicXML score 

Public Attributes
~~~~~~~~~~~~~~~~~

+ contexts
+ groups
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ obj

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _cache
+ _elements
+ _index
+ _unlinkedDuration

Public Methods
~~~~~~~~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note('A-'), range(30))
    >>> a.repeatCopy(note.Rest(), range(30, 60))
    >>> a.addGroupForElements('flute')
    >>> a[0].groups
    ['flute'] 
    >>> a.addGroupForElements('quietTime', note.Rest)
    >>> a[0].groups
    ['flute'] 
    >>> a[50].groups
    ['flute', 'quietTime'] 
    >>> a[1].groups.append('quietTime') # set one note to it
    >>> a[1].step = "B"
    >>> b = a.getElementsByGroup('quietTime')
    >>> len(b)
    31 
    >>> c = b.getElementsByClass(note.Note)
    >>> len(c)
    1 
    >>> c[0].name
    'B-' 

    

**addNext()**

    Add an objects or Elements (including other Streams) to the Stream (or multiple if passed a list) with offset equal to the highestTime (that is the latest "release" of an object) plus any offset in the Element or Stream to be added.  If that offset is zero (or a bare object is added) then this object will directly after the last Element ends. runs fast for multiple addition and will preserve isSorted if True 

    >>> a = Stream()
    >>> notes = []
    >>> for x in range(0,3):
    ...     n = note.Note('G#') 
    ...     n.duration.quarterLength = 3 
    ...     notes.append(n) 
    >>> a.addNext(notes[0])
    >>> a.highestOffset, a.highestTime
    (0.0, 3.0) 
    >>> a.addNext(notes[1])
    >>> a.highestOffset, a.highestTime
    (3.0, 6.0) 
    >>> a.addNext(notes[2])
    >>> a.highestOffset, a.highestTime
    (6.0, 9.0) 
    >>> notes2 = []
    >>> # since notes are not embedded in Elements here, their offset
    >>> # changes when added to a stream!
    >>> for x in range(0,3):
    ...     n = notes[x].deepcopy() 
    ...     n.offset = 0 
    ...     notes2.append(n) 
    >>> a.addNext(notes2) # add em all again
    >>> a.highestOffset, a.highestTime
    (15.0, 18.0) 
    >>> a.isSequence()
    True 

**append()**

    Add a (sub)Stream, Element, or object (wrapped into a default element) to the element Stream. 

    >>> a = Stream()
    >>> a.append(None)
    >>> a.append(music21.note.Note('G#'))
    >>> len(a)
    2 
    QUESTION: should this also add an entry to the parent and context 
    attributes (if any) in the object? 

**bestClef()**

    Cheat method: returns the clef that is the best fit for the sequence 

    >>> a = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(60,72)) 
    ...    a.append(n) 
    >>> b = a.bestClef()
    >>> b.line
    2 
    >>> b.sign
    'G' 
    >>> c = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(35,55)) 
    ...    c.append(n) 
    >>> d = c.bestClef()
    >>> d.line
    4 
    >>> d.sign
    'F' 

**contexts()**

    No documentation.

**copy()**

    Makes a copy of this element with a reference to the SAME object but with unlinked offset, id, priority and a cloned Groups object 

    >>> import note
    >>> import duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.copy()
    >>> b.offset = duration.Duration("half")

    

**deepcopy()**

    similar to copy but also does a deepcopy of the object as well. (name is all lowercase to go with copy.deepcopy convention) 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.deepcopy()
    >>> b.offset = duration.Duration("half")
    >>> a.obj is b.obj
    False 
    >>> a.obj.accidental = "-"
    >>> b.obj.name
    'A' 
    >>> a.offset
    1.0 
    >>> b.offset
    2.0 
    >>> a.groups[0] = "bassoon"
    >>> ("flute" in a.groups, "flute" in b.groups)
    (False, True) 

**duration()**

    Returns the total duration of the Stream, from the beginning of the stream until the end of the final element. May be set independently by supplying a Duration object. 

    >>> a = Stream()
    >>> q = note.QuarterNote()
    >>> a.repeatCopy(q, [0,1,2,3])
    >>> a.highestOffset
    3.0 
    >>> a.highestTime
    4.0 
    >>> a.duration.quarterLength
    4.0 
    >>> # Advanced usage: overriding the duration
    >>> newDuration = duration.Duration("half")
    >>> newDuration.quarterLength
    2.0 
    >>> a.duration = newDuration
    >>> a.duration.quarterLength
    2.0 
    >>> a.highestTime # unchanged
    4.0 

**elements()**

    No documentation.

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where all no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q)
    5 
    >>> len(q.flat)
    25 
    >>> q.flat[24].offset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**getElementsByClass()**

    return a list of all Elements that match the className 

    >>> a = Stream()
    >>> a.fillNone(10) # adds Elements with obj == None
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     a.append(n) 
    >>> found = a.getElementsByClass(note.Note)
    >>> len(found)
    4 
    >>> found[0].pitch.accidental.name
    'sharp' 
    >>> b = Stream()
    >>> b.repeatCopy(None, range(10))
    >>> a.append(b)
    >>> # here, it gets elements from within a stream
    >>> # this probably should not do this, as it is one layer lower
    >>> found = a.getElementsByClass(types.NoneType)
    >>> len(found)
    10 
    >>> c = Stream()
    >>> c.append(note.Note('A-'))
    >>> d = Stream()
    >>> d.repeatCopy(None, range(10))
    >>> c.append(d)
    >>> a.append(c)
    >>> found = a.getElementsByClass(types.NoneType)
    >>> len(found) # if recursive, should get 20
    10 
    >>> found = a.flat.getElementsByClass(types.NoneType)
    >>> len(found)  # this is not the right answer
    30 

**getElementsByGroup()**

    No documentation.

**getElementsById()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

**getElementsByOffset()**

    Return a list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(10)) # adds Elements with obj == None
    >>> b = a.getElementsByOffset(4,6)
    >>> len(b)
    3 
    >>> b = a.getElementsByOffset(4,5.5)
    >>> len(b)
    2 
    >>> a = Stream()
    >>> n = note.Note('G')
    >>> n.quarterLength = .5
    >>> a.repeatCopy(n, range(8))
    >>> b = Stream()
    >>> b.repeatCopy(a, [0, 3, 6])
    >>> c = b.getElementsByOffset(2,6.9)
    >>> len(c)
    2 
    >>> c = b.flat.getElementsByOffset(2,6.9)
    >>> len(c)
    10 

**getGroups()**

    Get a dictionary for each groupId and the count of instances. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> a.repeatCopy(n, range(30))
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getNotes()**

    No documentation.

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements taht have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('quarter') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> d = a.getOverlaps(True, False)
    >>> len(d)
    0 
    >>> d = a.getOverlaps(True, True) # including coincident boundaries
    >>> len(d)
    1 
    >>> len(d[0])
    4 
    >>> a = Stream()
    >>> for x in [0,0,0,0,13,13,13]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('half') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> d = a.getOverlaps()
    >>> len(d[0])
    4 
    >>> len(d[13])
    3 
    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     e = Element(n) 
    ...     e.offset = x * 1 
    ...     a.append(e) 
    ... 
    >>> # default is to not include coincident boundaries
    >>> d = a.getOverlaps()
    >>> len(d[0])
    7 

**getSimultaneous()**

    Find and return any elements that start at the same time. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 0 
    ...     a.append(n) 
    ... 
    >>> b = a.getSimultaneous()
    >>> len(b[0]) == 4
    True 
    >>> c = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**highestOffset()**

    Get start time of element with the highest offset in the Stream 

    >>> a = Stream()
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.highestOffset
    12.0 

    

**highestTime()**

    returns the max(el.offset + el.duration.quarterLength) over all elements, usually representing the last "release" in the Stream. The duration of a Stream is usually equal to the highestTime expressed as a Duration object, but can be set separately.  See below. 

**id()**

    No documentation.

**insertAtOffset()**

    Append an object with a given offset. Wrap in an Element and set offset time. 

    >>> a = Stream()
    >>> a.insertAtOffset(None, 32)
    >>> a._getHighestOffset()
    32.0 

**isClass()**

    Returns true if the Stream or Stream Subclass is a particular class or subclasses that class. Used by getElementsByClass in Stream 

    >>> a = Stream()
    >>> a.isClass(note.Note)
    False 
    >>> a.isClass(Stream)
    True 
    >>> b = Measure()
    >>> b.isClass(Measure)
    True 
    >>> b.isClass(Stream)
    True 

**isGapless()**

    No documentation.

**isSequence()**

    A stream is a sequence if it has no overlaps. TODO: check that co-incident boundaries are properly handled 

    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     e = Element(n) 
    ...     e.offset = x * 1 
    ...     a.append(e) 
    ... 
    >>> a.isSequence()
    False 

**isTwin()**

    a weaker form of equality.  a.isTwin(b) is true if a and b store either the same object OR objects that are equal and a.groups == b.groups and a.id == b.id (or both are none) and duration are equal. but does not require position, priority, or parent to be the same In other words, is essentially the same object in a different context 

    >>> import note
    >>> aE = Element(obj = note.Note("A-"))
    >>> aE.id = "aflat-Note"
    >>> aE.groups.append("out-of-range")
    >>> aE.offset = 4.0
    >>> aE.priority = 4
    >>> bE = aE.copy()
    >>> aE is bE
    False 
    >>> aE == bE
    True 
    >>> aE.isTwin(bE)
    True 
    >>> bE.offset = 14.0
    >>> bE.priority = -4
    >>> aE == bE
    False 
    >>> aE.isTwin(bE)
    True 

**lily()**

    Returns the stream translated into Lilypond format. 

**mx()**

    This does not work yet, but something like this could work 

    

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**offset()**

    No documentation.

**parent()**

    No documentation.

**priority()**

    No documentation.

**recurseRepr()**

    No documentation.

**repeatCopy()**

    Given an object, create many copies at the possitioins specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatCopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**

    No documentation.

**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note('A-'), range(30))
    >>> a.repeatCopy(note.Note('E-'), range(30, 60))
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.getElementsById()
    >>> len(ref)
    1 
    >>> ref['flute']
    60 
    >>> b = Stream()
    >>> b.repeatCopy(None, range(30))
    >>> b.repeatCopy(note.Note('E-'), range(30, 60))
    >>> b.setIdForElements('flute', note.Note)
    >>> a[0].id
    'flute' 
    >>> ref = b.getElementsById()
    >>> ref['flute']
    30 

    

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**sorted()**

    returns a new Stream where all the elements are sorted according to offset time if this stream is not flat, then only the highest elements are sorted.  To sort all, run myStream.flat.sorted ## TODO: CLEF ORDER RULES, etc. 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> farRight = note.Note("E")
    >>> farRight.priority = 5
    >>> farRight.offset = 2.0
    >>> y.append(farRight)
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; ' 
    >>> z = y.sorted
    >>> g = ""
    >>> for myElement in z:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> z[2].name, z[3].name
    ('C#', 'E') 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_consolidateLayering()**

    Given elementsSorted and a map of equal lenght with lists of index values that meet a given condition (overlap or simultaneities), organize into a dictionary by the relevant or first offset 

**_durSpanOverlap()**

    Compare two durSpans and find overlaps; optionally, includ coincident boundaries. a and b are sorted to permit any ordering. If an element ends at 3.0 and another starts at 3.0, this may or may not be considered an overlap. The includeCoincidentEnds parameter determines this behaviour, where ending and starting 3.0 being a type of overlap is set by the includeCoincidentBoundaries being True. 

    >>> a = Stream()
    >>> a._durSpanOverlap([0, 10], [11, 12], False)
    False 
    >>> a._durSpanOverlap([11, 12], [0, 10], False)
    False 
    >>> a._durSpanOverlap([0, 3], [3, 6], False)
    False 
    >>> a._durSpanOverlap([0, 3], [3, 6], True)
    True 

**_duration()**

    No documentation.

**_elementsChanged()**

    call anytime _elements is changed -- should only be called by this package... 

**_findLayering()**

    Find any elements in an elementsSorted list that have simultaneities or durations that cause overlaps. Returns two lists. Each list contains a list for each element in elementsSorted. If that elements has overalps or simultaneities, all index values that match are included in that list. See testOverlaps, in unit tests, for examples. 

    

    

**_getDurSpan()**

    Given elementsSorted, create a lost of parallel values that represent dur spans, or start and end times. Assume durations of None imply 0 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(5))
    >>> a._getDurSpan(a.flat)
    [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0)] 

**_getDuration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    

**_getElements()**

    No documentation.

**_getFlat()**

    returns a new Stream where all no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q)
    5 
    >>> len(q.flat)
    25 
    >>> q.flat[24].offset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**_getFlatOrSemiFlat()**

    No documentation.

**_getHighestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.highestOffset
    40.0 
    >>> q.flat.highestOffset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.flat.highestOffset
    444.0 

**_getHighestTime()**

    

    >>> n = note.Note('A-')
    >>> n.quarterLength = 3
    >>> p = Stream()
    >>> p.repeatCopy(n, range(5))
    >>> p.highestTime # 4 + 3
    7.0 
    >>> q = Stream()
    >>> q.repeatCopy(p, [20, 0, 10, 30, 40]) # insert out of order
    >>> len(q.flat)
    25 
    >>> q.highestTime # this works b/c the component Stream has an dur
    47.0 
    >>> q.flat.highestTime # 44 + 3
    47.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.highestTime
    447.0 
    >>> r.flat.highestTime
    447.0 
    >>> q.flat.highestOffset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.flat.highestOffset
    444.0 

**_getIsGapless()**

    No documentation.

**_getLily()**

    Returns the stream translated into Lilypond format. 

**_getMX()**

    This does not work yet, but something like this could work 

    

**_getOffset()**

    No documentation.

**_getParent()**

    No documentation.

**_getPriority()**

    No documentation.

**_getSemiFlat()**

    No documentation.

**_getSorted()**

    returns a new Stream where all the elements are sorted according to offset time if this stream is not flat, then only the highest elements are sorted.  To sort all, run myStream.flat.sorted ## TODO: CLEF ORDER RULES, etc. 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> farRight = note.Note("E")
    >>> farRight.priority = 5
    >>> farRight.offset = 2.0
    >>> y.append(farRight)
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; ' 
    >>> z = y.sorted
    >>> g = ""
    >>> for myElement in z:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> z[2].name, z[3].name
    ('C#', 'E') 

**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**

    No documentation.

**_parent()**

    No documentation.

**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**_setDuration()**

    Set the total duration of the Stream independently of the highestTime of the stream.  Useful to define the scope of the stream as independent of its constituted elements. If set to None, then the default behavior of computing automatically from highestTime is reestablished. 

**_setElements()**

    

    >>> a = Stream()
    >>> a.repeatCopy(None, range(10))
    >>> b = Stream()
    >>> b.repeatCopy(None, range(10))
    >>> b.offset = 6
    >>> c = Stream()
    >>> c.repeatCopy(None, range(10))
    >>> c.offset = 12
    >>> b.append(c)
    >>> b.isFlat
    False 
    >>> a.isFlat
    True 
    >>> a.elements = b.elements
    >>> a.isFlat
    False 

**_setLily()**

    Sets the Lilypond output for the stream. Overrides what is obtained from get_lily. 

**_setMX()**

    

    

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


Class Stream
------------

This is basic unit for timed Elements. In many cases these timed Elements will be of the same class of things; notes, clefs, etc. This is not required. Like the base class, Element, Streams have offsets, priority, id, and groups they also have an elements attribute which returns a list of elements; the obj attribute returns the same list (Stream-aware applications should ask for ElementOrStream.elements first and then look for .obj if the ElementOrStream does not have an element attribute). The Stream has a duration that can either be explicitly set or it is the release time of the chronologically last element in the Stream (that is, the highest onset plus duration of any element in the Stream). Streams may be embedded within other Streams. TODO: Get Stream Duration working -- should be the total length of the Stream. -- see the ._getDuration() and ._setDuration() methods 

Public Attributes
~~~~~~~~~~~~~~~~~

+ contexts
+ groups
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ obj

Private Attributes
~~~~~~~~~~~~~~~~~~

+ _cache
+ _elements
+ _index
+ _unlinkedDuration

Public Methods
~~~~~~~~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note('A-'), range(30))
    >>> a.repeatCopy(note.Rest(), range(30, 60))
    >>> a.addGroupForElements('flute')
    >>> a[0].groups
    ['flute'] 
    >>> a.addGroupForElements('quietTime', note.Rest)
    >>> a[0].groups
    ['flute'] 
    >>> a[50].groups
    ['flute', 'quietTime'] 
    >>> a[1].groups.append('quietTime') # set one note to it
    >>> a[1].step = "B"
    >>> b = a.getElementsByGroup('quietTime')
    >>> len(b)
    31 
    >>> c = b.getElementsByClass(note.Note)
    >>> len(c)
    1 
    >>> c[0].name
    'B-' 

    

**addNext()**

    Add an objects or Elements (including other Streams) to the Stream (or multiple if passed a list) with offset equal to the highestTime (that is the latest "release" of an object) plus any offset in the Element or Stream to be added.  If that offset is zero (or a bare object is added) then this object will directly after the last Element ends. runs fast for multiple addition and will preserve isSorted if True 

    >>> a = Stream()
    >>> notes = []
    >>> for x in range(0,3):
    ...     n = note.Note('G#') 
    ...     n.duration.quarterLength = 3 
    ...     notes.append(n) 
    >>> a.addNext(notes[0])
    >>> a.highestOffset, a.highestTime
    (0.0, 3.0) 
    >>> a.addNext(notes[1])
    >>> a.highestOffset, a.highestTime
    (3.0, 6.0) 
    >>> a.addNext(notes[2])
    >>> a.highestOffset, a.highestTime
    (6.0, 9.0) 
    >>> notes2 = []
    >>> # since notes are not embedded in Elements here, their offset
    >>> # changes when added to a stream!
    >>> for x in range(0,3):
    ...     n = notes[x].deepcopy() 
    ...     n.offset = 0 
    ...     notes2.append(n) 
    >>> a.addNext(notes2) # add em all again
    >>> a.highestOffset, a.highestTime
    (15.0, 18.0) 
    >>> a.isSequence()
    True 

**append()**

    Add a (sub)Stream, Element, or object (wrapped into a default element) to the element Stream. 

    >>> a = Stream()
    >>> a.append(None)
    >>> a.append(music21.note.Note('G#'))
    >>> len(a)
    2 
    QUESTION: should this also add an entry to the parent and context 
    attributes (if any) in the object? 

**bestClef()**

    Cheat method: returns the clef that is the best fit for the sequence 

    >>> a = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(60,72)) 
    ...    a.append(n) 
    >>> b = a.bestClef()
    >>> b.line
    2 
    >>> b.sign
    'G' 
    >>> c = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(35,55)) 
    ...    c.append(n) 
    >>> d = c.bestClef()
    >>> d.line
    4 
    >>> d.sign
    'F' 

**contexts()**

    No documentation.

**copy()**

    Makes a copy of this element with a reference to the SAME object but with unlinked offset, id, priority and a cloned Groups object 

    >>> import note
    >>> import duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.copy()
    >>> b.offset = duration.Duration("half")

    

**deepcopy()**

    similar to copy but also does a deepcopy of the object as well. (name is all lowercase to go with copy.deepcopy convention) 

    >>> from music21 import note, duration
    >>> n = note.Note('A')
    >>> a = Element(obj = n)
    >>> a.offset = duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.deepcopy()
    >>> b.offset = duration.Duration("half")
    >>> a.obj is b.obj
    False 
    >>> a.obj.accidental = "-"
    >>> b.obj.name
    'A' 
    >>> a.offset
    1.0 
    >>> b.offset
    2.0 
    >>> a.groups[0] = "bassoon"
    >>> ("flute" in a.groups, "flute" in b.groups)
    (False, True) 

**duration()**

    Returns the total duration of the Stream, from the beginning of the stream until the end of the final element. May be set independently by supplying a Duration object. 

    >>> a = Stream()
    >>> q = note.QuarterNote()
    >>> a.repeatCopy(q, [0,1,2,3])
    >>> a.highestOffset
    3.0 
    >>> a.highestTime
    4.0 
    >>> a.duration.quarterLength
    4.0 
    >>> # Advanced usage: overriding the duration
    >>> newDuration = duration.Duration("half")
    >>> newDuration.quarterLength
    2.0 
    >>> a.duration = newDuration
    >>> a.duration.quarterLength
    2.0 
    >>> a.highestTime # unchanged
    4.0 

**elements()**

    No documentation.

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where all no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q)
    5 
    >>> len(q.flat)
    25 
    >>> q.flat[24].offset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**getElementsByClass()**

    return a list of all Elements that match the className 

    >>> a = Stream()
    >>> a.fillNone(10) # adds Elements with obj == None
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     a.append(n) 
    >>> found = a.getElementsByClass(note.Note)
    >>> len(found)
    4 
    >>> found[0].pitch.accidental.name
    'sharp' 
    >>> b = Stream()
    >>> b.repeatCopy(None, range(10))
    >>> a.append(b)
    >>> # here, it gets elements from within a stream
    >>> # this probably should not do this, as it is one layer lower
    >>> found = a.getElementsByClass(types.NoneType)
    >>> len(found)
    10 
    >>> c = Stream()
    >>> c.append(note.Note('A-'))
    >>> d = Stream()
    >>> d.repeatCopy(None, range(10))
    >>> c.append(d)
    >>> a.append(c)
    >>> found = a.getElementsByClass(types.NoneType)
    >>> len(found) # if recursive, should get 20
    10 
    >>> found = a.flat.getElementsByClass(types.NoneType)
    >>> len(found)  # this is not the right answer
    30 

**getElementsByGroup()**

    No documentation.

**getElementsById()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

**getElementsByOffset()**

    Return a list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(10)) # adds Elements with obj == None
    >>> b = a.getElementsByOffset(4,6)
    >>> len(b)
    3 
    >>> b = a.getElementsByOffset(4,5.5)
    >>> len(b)
    2 
    >>> a = Stream()
    >>> n = note.Note('G')
    >>> n.quarterLength = .5
    >>> a.repeatCopy(n, range(8))
    >>> b = Stream()
    >>> b.repeatCopy(a, [0, 3, 6])
    >>> c = b.getElementsByOffset(2,6.9)
    >>> len(c)
    2 
    >>> c = b.flat.getElementsByOffset(2,6.9)
    >>> len(c)
    10 

**getGroups()**

    Get a dictionary for each groupId and the count of instances. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> a.repeatCopy(n, range(30))
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getNotes()**

    No documentation.

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements taht have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('quarter') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> d = a.getOverlaps(True, False)
    >>> len(d)
    0 
    >>> d = a.getOverlaps(True, True) # including coincident boundaries
    >>> len(d)
    1 
    >>> len(d[0])
    4 
    >>> a = Stream()
    >>> for x in [0,0,0,0,13,13,13]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('half') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> d = a.getOverlaps()
    >>> len(d[0])
    4 
    >>> len(d[13])
    3 
    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     e = Element(n) 
    ...     e.offset = x * 1 
    ...     a.append(e) 
    ... 
    >>> # default is to not include coincident boundaries
    >>> d = a.getOverlaps()
    >>> len(d[0])
    7 

**getSimultaneous()**

    Find and return any elements that start at the same time. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 0 
    ...     a.append(n) 
    ... 
    >>> b = a.getSimultaneous()
    >>> len(b[0]) == 4
    True 
    >>> c = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**highestOffset()**

    Get start time of element with the highest offset in the Stream 

    >>> a = Stream()
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.highestOffset
    12.0 

    

**highestTime()**

    returns the max(el.offset + el.duration.quarterLength) over all elements, usually representing the last "release" in the Stream. The duration of a Stream is usually equal to the highestTime expressed as a Duration object, but can be set separately.  See below. 

**id()**

    No documentation.

**insertAtOffset()**

    Append an object with a given offset. Wrap in an Element and set offset time. 

    >>> a = Stream()
    >>> a.insertAtOffset(None, 32)
    >>> a._getHighestOffset()
    32.0 

**isClass()**

    Returns true if the Stream or Stream Subclass is a particular class or subclasses that class. Used by getElementsByClass in Stream 

    >>> a = Stream()
    >>> a.isClass(note.Note)
    False 
    >>> a.isClass(Stream)
    True 
    >>> b = Measure()
    >>> b.isClass(Measure)
    True 
    >>> b.isClass(Stream)
    True 

**isGapless()**

    No documentation.

**isSequence()**

    A stream is a sequence if it has no overlaps. TODO: check that co-incident boundaries are properly handled 

    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     e = Element(n) 
    ...     e.offset = x * 1 
    ...     a.append(e) 
    ... 
    >>> a.isSequence()
    False 

**isTwin()**

    a weaker form of equality.  a.isTwin(b) is true if a and b store either the same object OR objects that are equal and a.groups == b.groups and a.id == b.id (or both are none) and duration are equal. but does not require position, priority, or parent to be the same In other words, is essentially the same object in a different context 

    >>> import note
    >>> aE = Element(obj = note.Note("A-"))
    >>> aE.id = "aflat-Note"
    >>> aE.groups.append("out-of-range")
    >>> aE.offset = 4.0
    >>> aE.priority = 4
    >>> bE = aE.copy()
    >>> aE is bE
    False 
    >>> aE == bE
    True 
    >>> aE.isTwin(bE)
    True 
    >>> bE.offset = 14.0
    >>> bE.priority = -4
    >>> aE == bE
    False 
    >>> aE.isTwin(bE)
    True 

**lily()**

    Returns the stream translated into Lilypond format. 

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**offset()**

    No documentation.

**parent()**

    No documentation.

**priority()**

    No documentation.

**recurseRepr()**

    No documentation.

**repeatCopy()**

    Given an object, create many copies at the possitioins specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatCopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**

    No documentation.

**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note('A-'), range(30))
    >>> a.repeatCopy(note.Note('E-'), range(30, 60))
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.getElementsById()
    >>> len(ref)
    1 
    >>> ref['flute']
    60 
    >>> b = Stream()
    >>> b.repeatCopy(None, range(30))
    >>> b.repeatCopy(note.Note('E-'), range(30, 60))
    >>> b.setIdForElements('flute', note.Note)
    >>> a[0].id
    'flute' 
    >>> ref = b.getElementsById()
    >>> ref['flute']
    30 

    

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**sorted()**

    returns a new Stream where all the elements are sorted according to offset time if this stream is not flat, then only the highest elements are sorted.  To sort all, run myStream.flat.sorted ## TODO: CLEF ORDER RULES, etc. 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> farRight = note.Note("E")
    >>> farRight.priority = 5
    >>> farRight.offset = 2.0
    >>> y.append(farRight)
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; ' 
    >>> z = y.sorted
    >>> g = ""
    >>> for myElement in z:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> z[2].name, z[3].name
    ('C#', 'E') 

**write()**

    Write a file. A None file path will result in temporary file 

Private Methods
~~~~~~~~~~~~~~~

**_consolidateLayering()**

    Given elementsSorted and a map of equal lenght with lists of index values that meet a given condition (overlap or simultaneities), organize into a dictionary by the relevant or first offset 

**_durSpanOverlap()**

    Compare two durSpans and find overlaps; optionally, includ coincident boundaries. a and b are sorted to permit any ordering. If an element ends at 3.0 and another starts at 3.0, this may or may not be considered an overlap. The includeCoincidentEnds parameter determines this behaviour, where ending and starting 3.0 being a type of overlap is set by the includeCoincidentBoundaries being True. 

    >>> a = Stream()
    >>> a._durSpanOverlap([0, 10], [11, 12], False)
    False 
    >>> a._durSpanOverlap([11, 12], [0, 10], False)
    False 
    >>> a._durSpanOverlap([0, 3], [3, 6], False)
    False 
    >>> a._durSpanOverlap([0, 3], [3, 6], True)
    True 

**_duration()**

    No documentation.

**_elementsChanged()**

    call anytime _elements is changed -- should only be called by this package... 

**_findLayering()**

    Find any elements in an elementsSorted list that have simultaneities or durations that cause overlaps. Returns two lists. Each list contains a list for each element in elementsSorted. If that elements has overalps or simultaneities, all index values that match are included in that list. See testOverlaps, in unit tests, for examples. 

    

    

**_getDurSpan()**

    Given elementsSorted, create a lost of parallel values that represent dur spans, or start and end times. Assume durations of None imply 0 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(5))
    >>> a._getDurSpan(a.flat)
    [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0)] 

**_getDuration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    

**_getElements()**

    No documentation.

**_getFlat()**

    returns a new Stream where all no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q)
    5 
    >>> len(q.flat)
    25 
    >>> q.flat[24].offset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**_getFlatOrSemiFlat()**

    No documentation.

**_getHighestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.highestOffset
    40.0 
    >>> q.flat.highestOffset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.flat.highestOffset
    444.0 

**_getHighestTime()**

    

    >>> n = note.Note('A-')
    >>> n.quarterLength = 3
    >>> p = Stream()
    >>> p.repeatCopy(n, range(5))
    >>> p.highestTime # 4 + 3
    7.0 
    >>> q = Stream()
    >>> q.repeatCopy(p, [20, 0, 10, 30, 40]) # insert out of order
    >>> len(q.flat)
    25 
    >>> q.highestTime # this works b/c the component Stream has an dur
    47.0 
    >>> q.flat.highestTime # 44 + 3
    47.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.highestTime
    447.0 
    >>> r.flat.highestTime
    447.0 
    >>> q.flat.highestOffset
    44.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(0, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.highestOffset
    400.0 
    >>> r.flat.highestOffset
    444.0 

**_getIsGapless()**

    No documentation.

**_getLily()**

    Returns the stream translated into Lilypond format. 

**_getOffset()**

    No documentation.

**_getParent()**

    No documentation.

**_getPriority()**

    No documentation.

**_getSemiFlat()**

    No documentation.

**_getSorted()**

    returns a new Stream where all the elements are sorted according to offset time if this stream is not flat, then only the highest elements are sorted.  To sort all, run myStream.flat.sorted ## TODO: CLEF ORDER RULES, etc. 

    >>> s = Stream()
    >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
    >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
    >>> s.isSorted
    False 
    >>> g = ""
    >>> for myElement in s:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; ' 
    >>> y = s.sorted
    >>> y.isSorted
    True 
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> farRight = note.Note("E")
    >>> farRight.priority = 5
    >>> farRight.offset = 2.0
    >>> y.append(farRight)
    >>> g = ""
    >>> for myElement in y:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; ' 
    >>> z = y.sorted
    >>> g = ""
    >>> for myElement in z:
    ...    g += "%s: %s; " % (myElement.offset, myElement.name) 
    >>> g
    '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; ' 
    >>> z[2].name, z[3].name
    ('C#', 'E') 

**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**

    No documentation.

**_parent()**

    No documentation.

**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**_setDuration()**

    Set the total duration of the Stream independently of the highestTime of the stream.  Useful to define the scope of the stream as independent of its constituted elements. If set to None, then the default behavior of computing automatically from highestTime is reestablished. 

**_setElements()**

    

    >>> a = Stream()
    >>> a.repeatCopy(None, range(10))
    >>> b = Stream()
    >>> b.repeatCopy(None, range(10))
    >>> b.offset = 6
    >>> c = Stream()
    >>> c.repeatCopy(None, range(10))
    >>> c.offset = 12
    >>> b.append(c)
    >>> b.isFlat
    False 
    >>> a.isFlat
    True 
    >>> a.elements = b.elements
    >>> a.isFlat
    False 

**_setLily()**

    Sets the Lilypond output for the stream. Overrides what is obtained from get_lily. 

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


Class StreamException
---------------------

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

**testAdd()**

    No documentation.

**testEquality()**

    No documentation.

**testLilySemiComplex()**

    No documentation.

**testLilySimple()**

    No documentation.

**testOverlaps()**

    No documentation.

**testSort()**

    No documentation.

**testStreamDuration()**

    No documentation.

**testStreamRecursion()**

    No documentation.

**testStreamSortRecursion()**

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

**testLilySemiComplex()**

    No documentation.

**testLilySimple()**

    No documentation.

Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


