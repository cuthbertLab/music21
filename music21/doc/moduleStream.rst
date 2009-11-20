music21.stream
==============

Function extendDuration()
-------------------------

Given a stream and an object name, go through stream and find each object. The time between adjacent objects is then assigned to the duration of each object. The last duration of the last object is assigned to the end of the stream. 

>>> import music21.dynamics
>>> stream1 = Stream()
>>> n = note.QuarterNote()
>>> n.duration.quarterLength
1.0 
>>> stream1.repeatDeepcopy(n, [0, 10, 20, 30, 40])
>>> dyn = Element(music21.dynamics.Dynamic('ff'))
>>> dyn.offset = 15.0
>>> stream1.append(dyn)
>>> sort1 = stream1.sorted
>>> sort1.duration.quarterLength
41.0 
>>> len(sort1)
6 
>>> sort1[-1].offset
40.0 
>>> stream2 = extendDuration(sort1.flat, note.GeneralNote)
>>> len(stream2)
6 
>>> stream2[0].duration.quarterLength
10.0 
>>> stream2[-1].duration.quarterLength
1.0 
>>> stream2.duration.quarterLength
41.0 
>>> stream2[-1].offset
40.0 
#>>> stream2[1].duration.quarterLength 
#1.0  ## TODO: FIX Error: gets 10.0 



Function makeBeams()
--------------------

Given a stream containing measures, create beams based on TimeSignature objects. Edits the current stream in-place. 

>>> d = Stream()
>>> n = note.Note()
>>> n.quarterLength = .25
>>> d.repeatAdd(n, 16)
>>> x = makeMeasures(d)
>>> y = makeBeams(x)



Function makeMeasures()
-----------------------

Take a stream of and partition all elements into measures based on one or more TimeSignautre defined within the stream. If no TimeSignatures are defined, a default is used. If a meterStream is provided, this is used instead of the meterStream found in the Stream. If a refStream is provided, this is used to provide max offset values, necessary to fill empty rests and similar. TODO: this can simply be a method of Stream? 

>>> a = Stream()
>>> a.fillNone(3)
>>> b = makeMeasures(a)
>>> c = meter.TimeSignature('3/4')
>>> a.insertAtOffset(c, 0)
>>> x = makeMeasures(a)
>>> d = Stream()
>>> n = note.Note()
>>> d.repeatAdd(n, 10)
>>> d.repeatDeepcopy(n, [x+.5 for x in range(10)])
>>> x = makeMeasures(d)

Function makeRests()
--------------------

Given a streamObj with an Element with an offset not equal to zero, fill with one Rest preeceding this offset. If refStream is provided, use this to get min and max offsets. 

TODO: rename fillRests() or something else 

>>> a = Stream()
>>> a.insertAtOffset(None, 20)
>>> len(a)
1 
>>> a.lowestOffset
20.0 
>>> b = makeRests(a)
>>> len(b)
2 
>>> b.lowestOffset
0.0 

Function makeTies()
-------------------

Given a stream containing measures, examine each element in the stream if the elements duration extends beyond the measures bound, create a tied entity. Edits the current stream in-place. TODO: this can simply be a method of Stream TODO: take a list of clases to act as filter on what elements are tied. configure ".previous" and ".next" attributes 

>>> d = Stream()
>>> n = note.Note()
>>> n.quarterLength = 12
>>> d.repeatAdd(n, 10)
>>> d.repeatCopy(n, [x+.5 for x in range(10)])
>>> x = makeMeasures(d)
>>> x = makeTies(x)



Function recurseRepr()
----------------------


Function splitByClass()
-----------------------

Given a stream, get all objects specified by objName and then form two new streams, where fx returns 1/True for the first stream and other values for the second stream. Probably better named SplitByClass or similar. 

>>> a = Stream()
>>> for x in range(30,81):
...     n = note.Note() 
...     n.midi = x 
...     a.append(n) 
>>> fx = lambda n: n.midi > 60
>>> b, c = splitByClass(a, note.Note, fx)
>>> len(b)
20 
>>> len(c)
31 

Class Element
-------------

An element wraps an object so that the same object can be positioned within a stream. The object is always available as element.obj -- however, calls to the Element will call In addition to the properties that all Music21Objects have, Elements also have: (5) offset   : a float or duration specifying the distance from the start of the surrounding container (if any) (6) contexts : a list of references or weakreferences for current contexts of the object (for searching after parent) (7) priority : int representing the position of an object among all objects at the same offset. 

Attributes
~~~~~~~~~~

+ obj

Methods
~~~~~~~

**copy()**

    Makes a copy of this element with a reference to the SAME object but with unlinked offset, priority and a cloned Groups object 

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
    >>> a.offset = 1.0 # duration.Duration("quarter")
    >>> a.groups.append("flute")
    >>> b = a.deepcopy()
    >>> b.offset = 2.0 # duration.Duration("half")
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
    >>> n.quarterLength = 2.0
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

**getId()**


**id()**


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

**obj()**


**offset()**


**priority()**


**setId()**


Private Methods
~~~~~~~~~~~~~~~

**_getDuration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    >>> import note
    >>> el1 = Element()
    >>> n = note.Note('F#')
    >>> n.quarterLength = 2.0
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


**_getPriority()**


**_id()**


**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

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
    >>> a.offset = 4.0 # duration.Duration("whole")
    >>> a.offset
    4.0 

**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 

**_unlinkedDuration()**



Class Measure
-------------


Attributes
~~~~~~~~~~

+ clefIsNew
+ contexts
+ filled
+ groups
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ leftbarline
+ measureNumber
+ measureNumberSuffix
+ obj
+ rightbarline
+ timeSignature
+ timeSignatureIsNew

Methods
~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Rest(), 30)
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


**addRightBarline()**


**addTimeDependentDirection()**


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

    Cheat method: returns the clef that is the best fit for the sequence Perhaps rename 'getClef'; providing best clef if not clef is defined in this stream; otherwise, return a stream of clefs with offsets 

    

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

**clef()**


**contexts()**


**copy()**

    Return a shallow copy, or a linked reference to the source. 

**countId()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

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


**extractContext()**

    extracts elements around the given element within (before) quarter notes and (after) quarter notes (default 4) TODO: maxBefore -- maximum number of elements to return before; etc. 

    >>> from music21 import note
    >>> qn = note.QuarterNote()
    >>> qtrStream = Stream()
    >>> qtrStream.repeatCopy(qn, [0, 1, 2, 3, 4, 5])
    >>> hn = note.HalfNote()
    >>> hn.name = "B-"
    >>> qtrStream.addNext(hn)
    >>> qtrStream.repeatCopy(qn, [8, 9, 10, 11])
    >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
    >>> recurseRepr(hnStream)
    '{5.0} <Element offset=5.0 obj="<music21.note.Note C>">\n{6.0} <Element offset=6.0 obj="<music21.note.Note B->">\n{8.0} <Element offset=8.0 obj="<music21.note.Note C>">\n' 

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

**getElementAfterElement()**

    given an element, get the element next TODO: write this 

**getElementAfterOffset()**

    Get element after a provided offset TODO: write this 

**getElementAtOrAfter()**

    Given an offset, find the element at this offset, or with the offset greater than and nearest to. TODO: write this 

**getElementAtOrBefore()**

    Given an offset, find the element at this offset, or with the offset less than and nearest to. Return one element or None if no elements are at or preceded by this offset. TODO: inlcude sort order for concurrent matches? 

    >>> a = Stream()
    >>> x = Element()
    >>> x.id = 'x'
    >>> y = Element()
    >>> y.id = 'y'
    >>> z = Element()
    >>> z.id = 'z'
    >>> a.insertAtOffset(x, 20)
    >>> a.insertAtOffset(y, 10)
    >>> a.insertAtOffset(z, 0)
    >>> b = a.getElementAtOrBefore(21)
    >>> b.offset, b.id
    (20.0, 'x') 
    >>> b = a.getElementAtOrBefore(19)
    >>> b.offset, b.id
    (10.0, 'y') 
    >>> b = a.getElementAtOrBefore(0)
    >>> b.offset, b.id
    (0.0, 'z') 
    >>> b = a.getElementAtOrBefore(0.1)
    >>> b.offset, b.id
    (0.0, 'z') 

    

**getElementBeforeElement()**

    given an element, get the element before TODO: write this 

**getElementBeforeOffset()**

    Get element before a provided offset TODO: write this 

**getElementById()**

    Returns the first encountered Element for a given id. Return None if no match 

    >>> e = 'test'
    >>> a = Stream()
    >>> a.append(e)
    >>> a[0].id = 'green'
    >>> None == a.getElementById(3)
    True 
    >>> a.getElementById('green').id
    'green' 

**getElementsByClass()**

    Return a list of all Elements that match the className. Note that, as this appends Elements to a new Stream, whatever former parent relationship the Element had is lost. The Eleemnts parents is set to the new stream that contains it. This can be avoided by unpacking the Element, which returns a list. 

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

    # TODO: group comparisons are not YET case insensitive. 

    >>> from music21 import note
    >>> n1 = note.Note("C")
    >>> n1.groups.append('trombone')
    >>> n2 = note.Note("D")
    >>> n2.groups.append('trombone')
    >>> n2.groups.append('tuba')
    >>> n3 = note.Note("E")
    >>> n3.groups.append('tuba')
    >>> s1 = Stream()
    >>> s1.addNext(n1)
    >>> s1.addNext(n2)
    >>> s1.addNext(n3)
    >>> tboneSubStream = s1.getElementsByGroup("trombone")
    >>> for thisNote in tboneSubStream:
    ...     print thisNote.name 
    C 
    D 
    >>> tubaSubStream = s1.getElementsByGroup("tuba")
    >>> for thisNote in tubaSubStream:
    ...     print thisNote.name 
    D 
    E 

**getElementsByOffset()**

    Return a Stream/list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included. 

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
    >>> a.repeatAdd(n, 30)
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getInstrument()**

    Search this stream or parent streams for instruments, otherwise return a default TODO: Rename: getInstruments, and return a Stream of instruments 

    >>> a = Stream()
    >>> b = a.getInstrument()

**getMeasures()**

    Return all Measure objects in a Stream 

**getNotes()**

    Return all Note objects in a Stream() 

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements that have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.duration = duration.Duration('whole') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**getTimeSignatures()**

    Collect all time signatures in this stream. If no TimeSignature objects are defined, get a default Note: this could be a method of Stream. 

    >>> a = Stream()
    >>> b = meter.TimeSignature('3/4')
    >>> a.append(b)
    >>> a.fillNone(10)
    >>> c = a.getTimeSignatures()
    >>> len(c) == 1
    True 

**groupElementsByOffset()**

    returns a List of lists in which each entry in the main list is a list of elements occuring at the same time. list is ordered by offset (since we need to sort the list anyhow in order to group the elements), so there is no need to call stream.sorted before running this, but it can't hurt. it is DEFINITELY a feature that this method does not find elements within substreams that have the same absolute offset.  See Score.lily for how this is useful.  For the other behavior, call Stream.flat first. 

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


**insert()**

    Insert in elements by index position. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a[0].name == 'A-'
    True 
    >>> a.insert(0, note.Note('B'))
    >>> a[0].name == 'B'
    True 

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

**lily()**

    Returns the stream translated into Lilypond format. 

**lowestOffset()**

    Get start time of element with the lowest offset in the Stream 

    >>> a = Stream()
    >>> a.lowestOffset
    0.0 
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.lowestOffset
    9.0 

    

**measureNumberWithSuffix()**


**measures()**

    Return all Measure objects in a Stream 

**musicxml()**

    Provide a complete MusicXML: representation. 

**mx()**

    Return a musicxml Measure, populated with notes, chords, rests and a musixcml Attributes, populated with time, meter, key, etc 

    >>> a = Element(note.Note())
    >>> a.obj.quarterLength = 4
    >>> b = Measure()
    >>> b.insertAtOffset(a, 0)
    >>> len(b) # has a clef object in the stream
    2 
    >>> mxMeasure = b.mx
    >>> len(mxMeasure)
    1 

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**notes()**

    Return all Note objects in a Stream() 

**offset()**


**parent()**


**priority()**


**recurseRepr()**


**repeatAdd()**

    Given an object and a number, run addNext that many times on the object. numberOfTimes should of course be a positive integer. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.type = "whole"
    >>> a.repeatAdd(n, 10)
    >>> a.duration.quarterLength
    40.0 
    >>> a[9].offset
    36.0 

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

**repeatDeepcopy()**

    Given an object, create many DeepCopies at the positions specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatDeepcopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 
    >>> a[10].step = "D"
    >>> a[10].step
    'D' 
    >>> a[11].step
    'G' 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**


**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Note('E-'), 30)
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.countId()
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
    >>> ref = b.countId()
    >>> ref['flute']
    30 

    

**shiftElements()**

    Add offset value to every offset of contained Elements. TODO: add a class filter to set what is shifted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.shiftElements(30)
    >>> a.lowestOffset
    30.0 
    >>> a.shiftElements(-10)
    >>> a.lowestOffset
    20.0 

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
    >>> farRight = Element(note.Note("E"))
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

**transferOffsetToElements()**

    Transfer the offset of this stream to all internal elements; then set the offset of this stream to zero. 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.offset = 30
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    30.0 
    >>> a.offset
    0.0 
    >>> a.offset = 20
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    50.0 

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


**_elementsChanged()**

    Call anytime _elements is changed. Called by methods that add or change elemens. 

    >>> a = Stream()
    >>> a.isFlat
    True 
    >>> a._elements.append(Stream())
    >>> a._elementsChanged()
    >>> a.isFlat
    False 

**_findLayering()**

    Find any elements in an elementsSorted list that have simultaneities or durations that cause overlaps. Returns two lists. Each list contains a list for each element in elementsSorted. If that elements has overalps or simultaneities, all index values that match are included in that list. See testOverlaps, in unit tests, for examples. 

    

    

**_getClef()**


**_getDurSpan()**

    Given elementsSorted, create a lost of parallel values that represent dur spans, or start and end times. Assume durations of None imply 0 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(5))
    >>> a._getDurSpan(a.flat)
    [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0)] 

**_getDuration()**

    Gets the duration of the Element (if separately set), but normal returns the duration of the component object if available, otherwise returns None. 

    

**_getElements()**


**_getFlat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

    The largest offset plus duration. 

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


**_getLily()**

    Returns the stream translated into Lilypond format. 

**_getLowestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.lowestOffset
    0.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(97, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.lowestOffset
    97.0 

**_getMX()**

    Return a musicxml Measure, populated with notes, chords, rests and a musixcml Attributes, populated with time, meter, key, etc 

    >>> a = Element(note.Note())
    >>> a.obj.quarterLength = 4
    >>> b = Measure()
    >>> b.insertAtOffset(a, 0)
    >>> len(b) # has a clef object in the stream
    2 
    >>> mxMeasure = b.mx
    >>> len(mxMeasure)
    1 

**_getMXPart()**

    If there are Measures within this stream, use them to create and return an MX Part and ScorePart. meterStream can be provided to provide a template within which these events are positioned; this is necessary for handling cases where one part is shorter than another. 

**_getMusicXML()**

    Provide a complete MusicXML: representation. 

**_getMxDynamics()**

    Given an mxDirection, return a dynamics if present, otherwise, None This should be moved into musicxml.py, as a method of mxDirection 

**_getOffset()**


**_getParent()**


**_getPriority()**


**_getSemiFlat()**


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
    >>> farRight = Element(note.Note("E"))
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

**_id()**


**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**


**_parent()**


**_priority()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

**_setClef()**


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

    Given an mxMeasure, create a music21 measure 

**_setMXPart()**

    Load a part given an mxScore and a part name. 

**_setMusicXML()**

    

    

**_setOffset()**

    Set the offset as a quarterNote length (N.B. offsets are quarterNote lengths, not Duration objects...) 

    >>> import note
    >>> import duration
    >>> a = Element(note.Note('A#'))
    >>> a.offset = 23.0
    >>> a.offset
    23.0 
    >>> a.offset = 4.0 # duration.Duration("whole")
    >>> a.offset
    4.0 

**_setParent()**


**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 

**_unlinkedDuration()**



Class Part
----------

A stream subclass for containing parts. 

Attributes
~~~~~~~~~~

+ contexts
+ groups
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ obj

Methods
~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Rest(), 30)
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

    Cheat method: returns the clef that is the best fit for the sequence Perhaps rename 'getClef'; providing best clef if not clef is defined in this stream; otherwise, return a stream of clefs with offsets 

    

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


**copy()**

    Return a shallow copy, or a linked reference to the source. 

**countId()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

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


**extractContext()**

    extracts elements around the given element within (before) quarter notes and (after) quarter notes (default 4) TODO: maxBefore -- maximum number of elements to return before; etc. 

    >>> from music21 import note
    >>> qn = note.QuarterNote()
    >>> qtrStream = Stream()
    >>> qtrStream.repeatCopy(qn, [0, 1, 2, 3, 4, 5])
    >>> hn = note.HalfNote()
    >>> hn.name = "B-"
    >>> qtrStream.addNext(hn)
    >>> qtrStream.repeatCopy(qn, [8, 9, 10, 11])
    >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
    >>> recurseRepr(hnStream)
    '{5.0} <Element offset=5.0 obj="<music21.note.Note C>">\n{6.0} <Element offset=6.0 obj="<music21.note.Note B->">\n{8.0} <Element offset=8.0 obj="<music21.note.Note C>">\n' 

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

**getElementAfterElement()**

    given an element, get the element next TODO: write this 

**getElementAfterOffset()**

    Get element after a provided offset TODO: write this 

**getElementAtOrAfter()**

    Given an offset, find the element at this offset, or with the offset greater than and nearest to. TODO: write this 

**getElementAtOrBefore()**

    Given an offset, find the element at this offset, or with the offset less than and nearest to. Return one element or None if no elements are at or preceded by this offset. TODO: inlcude sort order for concurrent matches? 

    >>> a = Stream()
    >>> x = Element()
    >>> x.id = 'x'
    >>> y = Element()
    >>> y.id = 'y'
    >>> z = Element()
    >>> z.id = 'z'
    >>> a.insertAtOffset(x, 20)
    >>> a.insertAtOffset(y, 10)
    >>> a.insertAtOffset(z, 0)
    >>> b = a.getElementAtOrBefore(21)
    >>> b.offset, b.id
    (20.0, 'x') 
    >>> b = a.getElementAtOrBefore(19)
    >>> b.offset, b.id
    (10.0, 'y') 
    >>> b = a.getElementAtOrBefore(0)
    >>> b.offset, b.id
    (0.0, 'z') 
    >>> b = a.getElementAtOrBefore(0.1)
    >>> b.offset, b.id
    (0.0, 'z') 

    

**getElementBeforeElement()**

    given an element, get the element before TODO: write this 

**getElementBeforeOffset()**

    Get element before a provided offset TODO: write this 

**getElementById()**

    Returns the first encountered Element for a given id. Return None if no match 

    >>> e = 'test'
    >>> a = Stream()
    >>> a.append(e)
    >>> a[0].id = 'green'
    >>> None == a.getElementById(3)
    True 
    >>> a.getElementById('green').id
    'green' 

**getElementsByClass()**

    Return a list of all Elements that match the className. Note that, as this appends Elements to a new Stream, whatever former parent relationship the Element had is lost. The Eleemnts parents is set to the new stream that contains it. This can be avoided by unpacking the Element, which returns a list. 

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

    # TODO: group comparisons are not YET case insensitive. 

    >>> from music21 import note
    >>> n1 = note.Note("C")
    >>> n1.groups.append('trombone')
    >>> n2 = note.Note("D")
    >>> n2.groups.append('trombone')
    >>> n2.groups.append('tuba')
    >>> n3 = note.Note("E")
    >>> n3.groups.append('tuba')
    >>> s1 = Stream()
    >>> s1.addNext(n1)
    >>> s1.addNext(n2)
    >>> s1.addNext(n3)
    >>> tboneSubStream = s1.getElementsByGroup("trombone")
    >>> for thisNote in tboneSubStream:
    ...     print thisNote.name 
    C 
    D 
    >>> tubaSubStream = s1.getElementsByGroup("tuba")
    >>> for thisNote in tubaSubStream:
    ...     print thisNote.name 
    D 
    E 

**getElementsByOffset()**

    Return a Stream/list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included. 

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
    >>> a.repeatAdd(n, 30)
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getInstrument()**

    Search this stream or parent streams for instruments, otherwise return a default TODO: Rename: getInstruments, and return a Stream of instruments 

    >>> a = Stream()
    >>> b = a.getInstrument()

**getMeasures()**

    Return all Measure objects in a Stream 

**getNotes()**

    Return all Note objects in a Stream() 

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements that have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.duration = duration.Duration('whole') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**getTimeSignatures()**

    Collect all time signatures in this stream. If no TimeSignature objects are defined, get a default Note: this could be a method of Stream. 

    >>> a = Stream()
    >>> b = meter.TimeSignature('3/4')
    >>> a.append(b)
    >>> a.fillNone(10)
    >>> c = a.getTimeSignatures()
    >>> len(c) == 1
    True 

**groupElementsByOffset()**

    returns a List of lists in which each entry in the main list is a list of elements occuring at the same time. list is ordered by offset (since we need to sort the list anyhow in order to group the elements), so there is no need to call stream.sorted before running this, but it can't hurt. it is DEFINITELY a feature that this method does not find elements within substreams that have the same absolute offset.  See Score.lily for how this is useful.  For the other behavior, call Stream.flat first. 

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


**insert()**

    Insert in elements by index position. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a[0].name == 'A-'
    True 
    >>> a.insert(0, note.Note('B'))
    >>> a[0].name == 'B'
    True 

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

**lily()**


**lowestOffset()**

    Get start time of element with the lowest offset in the Stream 

    >>> a = Stream()
    >>> a.lowestOffset
    0.0 
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.lowestOffset
    9.0 

    

**measures()**

    Return all Measure objects in a Stream 

**musicxml()**

    Provide a complete MusicXM: representation. 

**mx()**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**notes()**

    Return all Note objects in a Stream() 

**offset()**


**parent()**


**priority()**


**recurseRepr()**


**repeatAdd()**

    Given an object and a number, run addNext that many times on the object. numberOfTimes should of course be a positive integer. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.type = "whole"
    >>> a.repeatAdd(n, 10)
    >>> a.duration.quarterLength
    40.0 
    >>> a[9].offset
    36.0 

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

**repeatDeepcopy()**

    Given an object, create many DeepCopies at the positions specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatDeepcopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 
    >>> a[10].step = "D"
    >>> a[10].step
    'D' 
    >>> a[11].step
    'G' 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**


**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Note('E-'), 30)
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.countId()
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
    >>> ref = b.countId()
    >>> ref['flute']
    30 

    

**shiftElements()**

    Add offset value to every offset of contained Elements. TODO: add a class filter to set what is shifted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.shiftElements(30)
    >>> a.lowestOffset
    30.0 
    >>> a.shiftElements(-10)
    >>> a.lowestOffset
    20.0 

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
    >>> farRight = Element(note.Note("E"))
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

**transferOffsetToElements()**

    Transfer the offset of this stream to all internal elements; then set the offset of this stream to zero. 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.offset = 30
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    30.0 
    >>> a.offset
    0.0 
    >>> a.offset = 20
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    50.0 

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


**_elementsChanged()**

    Call anytime _elements is changed. Called by methods that add or change elemens. 

    >>> a = Stream()
    >>> a.isFlat
    True 
    >>> a._elements.append(Stream())
    >>> a._elementsChanged()
    >>> a.isFlat
    False 

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


**_getFlat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

    The largest offset plus duration. 

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


**_getLily()**


**_getLowestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.lowestOffset
    0.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(97, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.lowestOffset
    97.0 

**_getMX()**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**_getMXPart()**

    If there are Measures within this stream, use them to create and return an MX Part and ScorePart. meterStream can be provided to provide a template within which these events are positioned; this is necessary for handling cases where one part is shorter than another. 

**_getMusicXML()**

    Provide a complete MusicXM: representation. 

**_getOffset()**


**_getParent()**


**_getPriority()**


**_getSemiFlat()**


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
    >>> farRight = Element(note.Note("E"))
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

**_id()**


**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**


**_parent()**


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

    Given an mxScore, build into this stream 

**_setMXPart()**

    Load a part given an mxScore and a part name. 

**_setMusicXML()**

    

    

**_setOffset()**

    Set the offset as a quarterNote length (N.B. offsets are quarterNote lengths, not Duration objects...) 

    >>> import note
    >>> import duration
    >>> a = Element(note.Note('A#'))
    >>> a.offset = 23.0
    >>> a.offset
    23.0 
    >>> a.offset = 4.0 # duration.Duration("whole")
    >>> a.offset
    4.0 

**_setParent()**


**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 

**_unlinkedDuration()**



Class Score
-----------

A Stream subclass for handling multi-part music. 

Attributes
~~~~~~~~~~

+ contexts
+ groups
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ obj

Methods
~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Rest(), 30)
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

    Cheat method: returns the clef that is the best fit for the sequence Perhaps rename 'getClef'; providing best clef if not clef is defined in this stream; otherwise, return a stream of clefs with offsets 

    

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


**copy()**

    Return a shallow copy, or a linked reference to the source. 

**countId()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

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


**extractContext()**

    extracts elements around the given element within (before) quarter notes and (after) quarter notes (default 4) TODO: maxBefore -- maximum number of elements to return before; etc. 

    >>> from music21 import note
    >>> qn = note.QuarterNote()
    >>> qtrStream = Stream()
    >>> qtrStream.repeatCopy(qn, [0, 1, 2, 3, 4, 5])
    >>> hn = note.HalfNote()
    >>> hn.name = "B-"
    >>> qtrStream.addNext(hn)
    >>> qtrStream.repeatCopy(qn, [8, 9, 10, 11])
    >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
    >>> recurseRepr(hnStream)
    '{5.0} <Element offset=5.0 obj="<music21.note.Note C>">\n{6.0} <Element offset=6.0 obj="<music21.note.Note B->">\n{8.0} <Element offset=8.0 obj="<music21.note.Note C>">\n' 

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

**getElementAfterElement()**

    given an element, get the element next TODO: write this 

**getElementAfterOffset()**

    Get element after a provided offset TODO: write this 

**getElementAtOrAfter()**

    Given an offset, find the element at this offset, or with the offset greater than and nearest to. TODO: write this 

**getElementAtOrBefore()**

    Given an offset, find the element at this offset, or with the offset less than and nearest to. Return one element or None if no elements are at or preceded by this offset. TODO: inlcude sort order for concurrent matches? 

    >>> a = Stream()
    >>> x = Element()
    >>> x.id = 'x'
    >>> y = Element()
    >>> y.id = 'y'
    >>> z = Element()
    >>> z.id = 'z'
    >>> a.insertAtOffset(x, 20)
    >>> a.insertAtOffset(y, 10)
    >>> a.insertAtOffset(z, 0)
    >>> b = a.getElementAtOrBefore(21)
    >>> b.offset, b.id
    (20.0, 'x') 
    >>> b = a.getElementAtOrBefore(19)
    >>> b.offset, b.id
    (10.0, 'y') 
    >>> b = a.getElementAtOrBefore(0)
    >>> b.offset, b.id
    (0.0, 'z') 
    >>> b = a.getElementAtOrBefore(0.1)
    >>> b.offset, b.id
    (0.0, 'z') 

    

**getElementBeforeElement()**

    given an element, get the element before TODO: write this 

**getElementBeforeOffset()**

    Get element before a provided offset TODO: write this 

**getElementById()**

    Returns the first encountered Element for a given id. Return None if no match 

    >>> e = 'test'
    >>> a = Stream()
    >>> a.append(e)
    >>> a[0].id = 'green'
    >>> None == a.getElementById(3)
    True 
    >>> a.getElementById('green').id
    'green' 

**getElementsByClass()**

    Return a list of all Elements that match the className. Note that, as this appends Elements to a new Stream, whatever former parent relationship the Element had is lost. The Eleemnts parents is set to the new stream that contains it. This can be avoided by unpacking the Element, which returns a list. 

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

    # TODO: group comparisons are not YET case insensitive. 

    >>> from music21 import note
    >>> n1 = note.Note("C")
    >>> n1.groups.append('trombone')
    >>> n2 = note.Note("D")
    >>> n2.groups.append('trombone')
    >>> n2.groups.append('tuba')
    >>> n3 = note.Note("E")
    >>> n3.groups.append('tuba')
    >>> s1 = Stream()
    >>> s1.addNext(n1)
    >>> s1.addNext(n2)
    >>> s1.addNext(n3)
    >>> tboneSubStream = s1.getElementsByGroup("trombone")
    >>> for thisNote in tboneSubStream:
    ...     print thisNote.name 
    C 
    D 
    >>> tubaSubStream = s1.getElementsByGroup("tuba")
    >>> for thisNote in tubaSubStream:
    ...     print thisNote.name 
    D 
    E 

**getElementsByOffset()**

    Return a Stream/list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included. 

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
    >>> a.repeatAdd(n, 30)
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getInstrument()**

    Search this stream or parent streams for instruments, otherwise return a default TODO: Rename: getInstruments, and return a Stream of instruments 

    >>> a = Stream()
    >>> b = a.getInstrument()

**getMeasures()**

    Return all Measure objects in a Stream 

**getNotes()**

    Return all Note objects in a Stream() 

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements that have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.duration = duration.Duration('whole') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**getTimeSignatures()**

    Collect all time signatures in this stream. If no TimeSignature objects are defined, get a default Note: this could be a method of Stream. 

    >>> a = Stream()
    >>> b = meter.TimeSignature('3/4')
    >>> a.append(b)
    >>> a.fillNone(10)
    >>> c = a.getTimeSignatures()
    >>> len(c) == 1
    True 

**groupElementsByOffset()**

    returns a List of lists in which each entry in the main list is a list of elements occuring at the same time. list is ordered by offset (since we need to sort the list anyhow in order to group the elements), so there is no need to call stream.sorted before running this, but it can't hurt. it is DEFINITELY a feature that this method does not find elements within substreams that have the same absolute offset.  See Score.lily for how this is useful.  For the other behavior, call Stream.flat first. 

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


**insert()**

    Insert in elements by index position. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a[0].name == 'A-'
    True 
    >>> a.insert(0, note.Note('B'))
    >>> a[0].name == 'B'
    True 

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

**lily()**

    returns the lily code for a score. 

**lowestOffset()**

    Get start time of element with the lowest offset in the Stream 

    >>> a = Stream()
    >>> a.lowestOffset
    0.0 
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.lowestOffset
    9.0 

    

**measures()**

    Return all Measure objects in a Stream 

**musicxml()**

    Provide a complete MusicXM: representation. 

**mx()**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**notes()**

    Return all Note objects in a Stream() 

**offset()**


**parent()**


**priority()**


**recurseRepr()**


**repeatAdd()**

    Given an object and a number, run addNext that many times on the object. numberOfTimes should of course be a positive integer. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.type = "whole"
    >>> a.repeatAdd(n, 10)
    >>> a.duration.quarterLength
    40.0 
    >>> a[9].offset
    36.0 

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

**repeatDeepcopy()**

    Given an object, create many DeepCopies at the positions specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatDeepcopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 
    >>> a[10].step = "D"
    >>> a[10].step
    'D' 
    >>> a[11].step
    'G' 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**


**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Note('E-'), 30)
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.countId()
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
    >>> ref = b.countId()
    >>> ref['flute']
    30 

    

**shiftElements()**

    Add offset value to every offset of contained Elements. TODO: add a class filter to set what is shifted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.shiftElements(30)
    >>> a.lowestOffset
    30.0 
    >>> a.shiftElements(-10)
    >>> a.lowestOffset
    20.0 

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
    >>> farRight = Element(note.Note("E"))
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

**transferOffsetToElements()**

    Transfer the offset of this stream to all internal elements; then set the offset of this stream to zero. 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.offset = 30
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    30.0 
    >>> a.offset
    0.0 
    >>> a.offset = 20
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    50.0 

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


**_elementsChanged()**

    Call anytime _elements is changed. Called by methods that add or change elemens. 

    >>> a = Stream()
    >>> a.isFlat
    True 
    >>> a._elements.append(Stream())
    >>> a._elementsChanged()
    >>> a.isFlat
    False 

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


**_getFlat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

    The largest offset plus duration. 

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


**_getLily()**

    returns the lily code for a score. 

**_getLowestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.lowestOffset
    0.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(97, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.lowestOffset
    97.0 

**_getMX()**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**_getMXPart()**

    If there are Measures within this stream, use them to create and return an MX Part and ScorePart. meterStream can be provided to provide a template within which these events are positioned; this is necessary for handling cases where one part is shorter than another. 

**_getMusicXML()**

    Provide a complete MusicXM: representation. 

**_getOffset()**


**_getParent()**


**_getPriority()**


**_getSemiFlat()**


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
    >>> farRight = Element(note.Note("E"))
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

**_id()**


**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**


**_parent()**


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

    Given an mxScore, build into this stream 

**_setMXPart()**

    Load a part given an mxScore and a part name. 

**_setMusicXML()**

    

    

**_setOffset()**

    Set the offset as a quarterNote length (N.B. offsets are quarterNote lengths, not Duration objects...) 

    >>> import note
    >>> import duration
    >>> a = Element(note.Note('A#'))
    >>> a.offset = 23.0
    >>> a.offset
    23.0 
    >>> a.offset = 4.0 # duration.Duration("whole")
    >>> a.offset
    4.0 

**_setParent()**


**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 

**_unlinkedDuration()**



Class Stream
------------

This is basic unit for timed Elements. In many cases these timed Elements will be of the same class of things; notes, clefs, etc. This is not required. Like the base class, Element, Streams have offsets, priority, id, and groups they also have an elements attribute which returns a list of elements; the obj attribute returns the same list (Stream-aware applications should ask for ElementOrStream.elements first and then look for .obj if the ElementOrStream does not have an element attribute). The Stream has a duration that can either be explicitly set or it is the release time of the chronologically last element in the Stream (that is, the highest onset plus duration of any element in the Stream). Streams may be embedded within other Streams. TODO: Get Stream Duration working -- should be the total length of the Stream. -- see the ._getDuration() and ._setDuration() methods 

Attributes
~~~~~~~~~~

+ contexts
+ groups
+ isFlat
+ isFlattenedRepresentation
+ isSorted
+ obj

Methods
~~~~~~~

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Rest(), 30)
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

    Cheat method: returns the clef that is the best fit for the sequence Perhaps rename 'getClef'; providing best clef if not clef is defined in this stream; otherwise, return a stream of clefs with offsets 

    

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


**copy()**

    Return a shallow copy, or a linked reference to the source. 

**countId()**

    Get all componenent Elements id as dictionary of id:count entries. Alternative name: getElementIdByClass() 

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


**extractContext()**

    extracts elements around the given element within (before) quarter notes and (after) quarter notes (default 4) TODO: maxBefore -- maximum number of elements to return before; etc. 

    >>> from music21 import note
    >>> qn = note.QuarterNote()
    >>> qtrStream = Stream()
    >>> qtrStream.repeatCopy(qn, [0, 1, 2, 3, 4, 5])
    >>> hn = note.HalfNote()
    >>> hn.name = "B-"
    >>> qtrStream.addNext(hn)
    >>> qtrStream.repeatCopy(qn, [8, 9, 10, 11])
    >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
    >>> recurseRepr(hnStream)
    '{5.0} <Element offset=5.0 obj="<music21.note.Note C>">\n{6.0} <Element offset=6.0 obj="<music21.note.Note B->">\n{8.0} <Element offset=8.0 obj="<music21.note.Note C>">\n' 

**fillNone()**

    For use in testing. fills a None object at every int offset between 0 and number 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**flat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

**getElementAfterElement()**

    given an element, get the element next TODO: write this 

**getElementAfterOffset()**

    Get element after a provided offset TODO: write this 

**getElementAtOrAfter()**

    Given an offset, find the element at this offset, or with the offset greater than and nearest to. TODO: write this 

**getElementAtOrBefore()**

    Given an offset, find the element at this offset, or with the offset less than and nearest to. Return one element or None if no elements are at or preceded by this offset. TODO: inlcude sort order for concurrent matches? 

    >>> a = Stream()
    >>> x = Element()
    >>> x.id = 'x'
    >>> y = Element()
    >>> y.id = 'y'
    >>> z = Element()
    >>> z.id = 'z'
    >>> a.insertAtOffset(x, 20)
    >>> a.insertAtOffset(y, 10)
    >>> a.insertAtOffset(z, 0)
    >>> b = a.getElementAtOrBefore(21)
    >>> b.offset, b.id
    (20.0, 'x') 
    >>> b = a.getElementAtOrBefore(19)
    >>> b.offset, b.id
    (10.0, 'y') 
    >>> b = a.getElementAtOrBefore(0)
    >>> b.offset, b.id
    (0.0, 'z') 
    >>> b = a.getElementAtOrBefore(0.1)
    >>> b.offset, b.id
    (0.0, 'z') 

    

**getElementBeforeElement()**

    given an element, get the element before TODO: write this 

**getElementBeforeOffset()**

    Get element before a provided offset TODO: write this 

**getElementById()**

    Returns the first encountered Element for a given id. Return None if no match 

    >>> e = 'test'
    >>> a = Stream()
    >>> a.append(e)
    >>> a[0].id = 'green'
    >>> None == a.getElementById(3)
    True 
    >>> a.getElementById('green').id
    'green' 

**getElementsByClass()**

    Return a list of all Elements that match the className. Note that, as this appends Elements to a new Stream, whatever former parent relationship the Element had is lost. The Eleemnts parents is set to the new stream that contains it. This can be avoided by unpacking the Element, which returns a list. 

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

    # TODO: group comparisons are not YET case insensitive. 

    >>> from music21 import note
    >>> n1 = note.Note("C")
    >>> n1.groups.append('trombone')
    >>> n2 = note.Note("D")
    >>> n2.groups.append('trombone')
    >>> n2.groups.append('tuba')
    >>> n3 = note.Note("E")
    >>> n3.groups.append('tuba')
    >>> s1 = Stream()
    >>> s1.addNext(n1)
    >>> s1.addNext(n2)
    >>> s1.addNext(n3)
    >>> tboneSubStream = s1.getElementsByGroup("trombone")
    >>> for thisNote in tboneSubStream:
    ...     print thisNote.name 
    C 
    D 
    >>> tubaSubStream = s1.getElementsByGroup("tuba")
    >>> for thisNote in tubaSubStream:
    ...     print thisNote.name 
    D 
    E 

**getElementsByOffset()**

    Return a Stream/list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included. 

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
    >>> a.repeatAdd(n, 30)
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getInstrument()**

    Search this stream or parent streams for instruments, otherwise return a default TODO: Rename: getInstruments, and return a Stream of instruments 

    >>> a = Stream()
    >>> b = a.getInstrument()

**getMeasures()**

    Return all Measure objects in a Stream 

**getNotes()**

    Return all Note objects in a Stream() 

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements that have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.duration = duration.Duration('whole') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
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
    ...     n = Element(note.Note('G#')) 
    ...     n.offset = x * 3 
    ...     c.append(n) 
    ... 
    >>> d = c.getSimultaneous()
    >>> len(d) == 0
    True 

**getTimeSignatures()**

    Collect all time signatures in this stream. If no TimeSignature objects are defined, get a default Note: this could be a method of Stream. 

    >>> a = Stream()
    >>> b = meter.TimeSignature('3/4')
    >>> a.append(b)
    >>> a.fillNone(10)
    >>> c = a.getTimeSignatures()
    >>> len(c) == 1
    True 

**groupElementsByOffset()**

    returns a List of lists in which each entry in the main list is a list of elements occuring at the same time. list is ordered by offset (since we need to sort the list anyhow in order to group the elements), so there is no need to call stream.sorted before running this, but it can't hurt. it is DEFINITELY a feature that this method does not find elements within substreams that have the same absolute offset.  See Score.lily for how this is useful.  For the other behavior, call Stream.flat first. 

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


**insert()**

    Insert in elements by index position. 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a[0].name == 'A-'
    True 
    >>> a.insert(0, note.Note('B'))
    >>> a[0].name == 'B'
    True 

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

**lily()**

    Returns the stream translated into Lilypond format. 

**lowestOffset()**

    Get start time of element with the lowest offset in the Stream 

    >>> a = Stream()
    >>> a.lowestOffset
    0.0 
    >>> for x in range(3,5):
    ...     e = Element(note.Note('G#')) 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.lowestOffset
    9.0 

    

**measures()**

    Return all Measure objects in a Stream 

**musicxml()**

    Provide a complete MusicXM: representation. 

**mx()**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**next()**

    Method for treating this object as an iterator Returns each element in order.  For sort order run x.sorted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(6))
    >>> b = []
    >>> for x in a:
    ...     b.append(x.offset) # get just offset 
    >>> b
    [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] 

**notes()**

    Return all Note objects in a Stream() 

**offset()**


**parent()**


**priority()**


**recurseRepr()**


**repeatAdd()**

    Given an object and a number, run addNext that many times on the object. numberOfTimes should of course be a positive integer. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.type = "whole"
    >>> a.repeatAdd(n, 10)
    >>> a.duration.quarterLength
    40.0 
    >>> a[9].offset
    36.0 

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

**repeatDeepcopy()**

    Given an object, create many DeepCopies at the positions specified by the offset list 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatDeepcopy(n, range(30))
    >>> len(a)
    30 
    >>> a[10].offset
    10.0 
    >>> a[10].step = "D"
    >>> a[10].step
    'D' 
    >>> a[11].step
    'G' 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encounted match is returned, or None if no match. 

**semiFlat()**


**setIdForElements()**

    Set all componenent Elements to the given id. Do not change the id of the Stream 

    >>> a = Stream()
    >>> a.repeatAdd(note.Note('A-'), 30)
    >>> a.repeatAdd(note.Note('E-'), 30)
    >>> a.setIdForElements('flute')
    >>> a[0].id
    'flute' 
    >>> ref = a.countId()
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
    >>> ref = b.countId()
    >>> ref['flute']
    30 

    

**shiftElements()**

    Add offset value to every offset of contained Elements. TODO: add a class filter to set what is shifted 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.shiftElements(30)
    >>> a.lowestOffset
    30.0 
    >>> a.shiftElements(-10)
    >>> a.lowestOffset
    20.0 

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
    >>> farRight = Element(note.Note("E"))
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

**transferOffsetToElements()**

    Transfer the offset of this stream to all internal elements; then set the offset of this stream to zero. 

    >>> a = Stream()
    >>> a.repeatCopy(None, range(0,10))
    >>> a.offset = 30
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    30.0 
    >>> a.offset
    0.0 
    >>> a.offset = 20
    >>> a.transferOffsetToElements()
    >>> a.lowestOffset
    50.0 

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


**_elementsChanged()**

    Call anytime _elements is changed. Called by methods that add or change elemens. 

    >>> a = Stream()
    >>> a.isFlat
    True 
    >>> a._elements.append(Stream())
    >>> a._elementsChanged()
    >>> a.isFlat
    False 

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


**_getFlat()**

    returns a new Stream where no elements nest within other elements 

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
    >>> p.repeatCopy(music21.Music21Object(), range(5))
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

    The largest offset plus duration. 

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


**_getLily()**

    Returns the stream translated into Lilypond format. 

**_getLowestOffset()**

    

    >>> p = Stream()
    >>> p.repeatCopy(None, range(5))
    >>> q = Stream()
    >>> q.repeatCopy(p, range(0,50,10))
    >>> len(q.flat)
    25 
    >>> q.lowestOffset
    0.0 
    >>> r = Stream()
    >>> r.repeatCopy(q, range(97, 500, 100))
    >>> len(r.flat)
    125 
    >>> r.lowestOffset
    97.0 

**_getMX()**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**_getMXPart()**

    If there are Measures within this stream, use them to create and return an MX Part and ScorePart. meterStream can be provided to provide a template within which these events are positioned; this is necessary for handling cases where one part is shorter than another. 

**_getMusicXML()**

    Provide a complete MusicXM: representation. 

**_getOffset()**


**_getParent()**


**_getPriority()**


**_getSemiFlat()**


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
    >>> farRight = Element(note.Note("E"))
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

**_id()**


**_offset()**

    float(x) -> floating point number Convert a string or number to a floating point number, if possible. 

**_overriddenLily()**


**_parent()**


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

    Given an mxScore, build into this stream 

**_setMXPart()**

    Load a part given an mxScore and a part name. 

**_setMusicXML()**

    

    

**_setOffset()**

    Set the offset as a quarterNote length (N.B. offsets are quarterNote lengths, not Duration objects...) 

    >>> import note
    >>> import duration
    >>> a = Element(note.Note('A#'))
    >>> a.offset = 23.0
    >>> a.offset
    23.0 
    >>> a.offset = 4.0 # duration.Duration("whole")
    >>> a.offset
    4.0 

**_setParent()**


**_setPriority()**

    value is an int. Priority specifies the order of processing from left (LOWEST #) to right (HIGHEST #) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second). Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements. In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score. 

    >>> a = Element()
    >>> a.priority = 3
    >>> a.priority = 'high'
    Traceback (most recent call last): 
    ElementException: priority values must be integers. 

**_unlinkedDuration()**



Class StreamException
---------------------


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

**testBeamsPartial()**

    This demonstrates a partial beam; a beam that is not connected between more than one note. 

**testBeamsStream()**

    A test of beams applied to different time signatures. 

**testCanons()**

    A test of creating a canon with shifted presentations of a source melody. This demonstrates the addition of rests. 

    

**testLilySemiComplex()**


**testLilySimple()**


**testMXOutput()**

    A simple test of adding notes to measures in a stream. 

**testMultipartMeasures()**

    This demonstrates obtaining slices from a stream and layering them into individual parts. TODO: this shoudl show instruments 

**testMultipartStreams()**

    Test the creation of multi-part streams by simply having streams within streams. 

    

**testMxMeasures()**

    A test of the automatic partitioning of notes in a measure and the creation of ties. 

**testScoreLily()**


Private Methods
~~~~~~~~~~~~~~~

**_exc_info()**

    Return a version of sys.exc_info() with the traceback frame minimised; usually the top level of the traceback frame is not needed. 


