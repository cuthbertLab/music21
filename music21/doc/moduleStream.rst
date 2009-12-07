music21.stream
==============

Function recurseRepr()
----------------------


Class Measure
-------------

Inherits from: stream.Stream, base.Music21Object, object

A representation of a Measure organized as a Stream. All properties of a Measure that are Music21 objects are found as part of the Stream's elements. 

Attributes
~~~~~~~~~~

**clefIsNew**

**contexts**

**filled**

**flattenedRepresentationOf**

**groups**

**isFlat**

**isSorted**

**leftbarline**

**locations**

**measureNumber**

**measureNumberSuffix**

**rightbarline**

**timeSignatureIsNew**

Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**id()**

**getOffsetBySite()**

**deepcopy()**

**copy()**

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**splitByClass()**

**shiftElements()**

**repeatCopy()**

**repeatAddNext()**

**recurseRepr()**

**pop()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtOffset()**

**insert()**

**index()**

**groupElementsByOffset()**

**getTimeSignatures()**

**getSimultaneous()**

**getPitches()**

**getOverlaps()**

**getNotes()**

**getMeasures()**

**getInstrument()**

**getGroups()**

**getElementsByOffset()**

**getElementsByGroup()**

**getElementsByClass()**

**getElementById()**

**getElementBeforeOffset()**

**getElementBeforeElement()**

**getElementAtOrBefore()**

**getElementAtOrAfter()**

**getElementAfterOffset()**

**getElementAfterElement()**

**findGaps()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addNext()**

**addGroupForElements()**


Locally Defined

**measureNumberWithSuffix()**


**addTimeDependentDirection()**


**addRightBarline()**


**addRepeat()**


**addLeftBarline()**


Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from stream.Stream

**sorted**

**semiFlat**

**pitches**

**notes**

**mx**

**musicxml**

**measures**

**lowestOffset**

**lily**

**isGapless**

**highestTime**

**highestOffset**

**flat**

**elements**


Locally Defined

**timeSignature**

    

    >>> a = Measure()
    >>> a.timeSignature = meter.TimeSignature('2/4')
    >>> a.timeSignature.numerator, a.timeSignature.denominator
    (2, 4) 

**clef**

    

    >>> a = Measure()
    >>> a.clef = clef.TrebleClef()
    >>> a.clef.sign    # clef is an element
    'G' 


Class Part
----------

Inherits from: stream.Stream, base.Music21Object, object

A stream subclass for containing parts. 

Attributes
~~~~~~~~~~

**contexts**

**flattenedRepresentationOf**

**groups**

**isFlat**

**isSorted**

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

**deepcopy()**

**copy()**

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**splitByClass()**

**shiftElements()**

**repeatCopy()**

**repeatAddNext()**

**recurseRepr()**

**pop()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtOffset()**

**insert()**

**index()**

**groupElementsByOffset()**

**getTimeSignatures()**

**getSimultaneous()**

**getPitches()**

**getOverlaps()**

**getNotes()**

**getMeasures()**

**getInstrument()**

**getGroups()**

**getElementsByOffset()**

**getElementsByGroup()**

**getElementsByClass()**

**getElementById()**

**getElementBeforeOffset()**

**getElementBeforeElement()**

**getElementAtOrBefore()**

**getElementAtOrAfter()**

**getElementAfterOffset()**

**getElementAfterElement()**

**findGaps()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addNext()**

**addGroupForElements()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from stream.Stream

**sorted**

**semiFlat**

**pitches**

**notes**

**mx**

**musicxml**

**measures**

**lowestOffset**

**lily**

**isGapless**

**highestTime**

**highestOffset**

**flat**

**elements**


Class Score
-----------

Inherits from: stream.Stream, base.Music21Object, object

A Stream subclass for handling multi-part music. 

Attributes
~~~~~~~~~~

**contexts**

**flattenedRepresentationOf**

**groups**

**isFlat**

**isSorted**

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

**deepcopy()**

**copy()**

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**splitByClass()**

**shiftElements()**

**repeatCopy()**

**repeatAddNext()**

**recurseRepr()**

**pop()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtOffset()**

**insert()**

**index()**

**groupElementsByOffset()**

**getTimeSignatures()**

**getSimultaneous()**

**getPitches()**

**getOverlaps()**

**getNotes()**

**getMeasures()**

**getInstrument()**

**getGroups()**

**getElementsByOffset()**

**getElementsByGroup()**

**getElementsByClass()**

**getElementById()**

**getElementBeforeOffset()**

**getElementBeforeElement()**

**getElementAtOrBefore()**

**getElementAtOrAfter()**

**getElementAfterOffset()**

**getElementAfterElement()**

**findGaps()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addNext()**

**addGroupForElements()**

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Inherited from stream.Stream

**sorted**

**semiFlat**

**pitches**

**notes**

**mx**

**musicxml**

**measures**

**lowestOffset**

**lily**

**isGapless**

**highestTime**

**highestOffset**

**flat**

**elements**


Class Stream
------------

Inherits from: base.Music21Object, object

This is basic container for Music21Objects that occur at certain times. Like the base class, Music21Object, Streams have offsets, priority, id, and groups they also have an elements attribute which returns a list of elements; The Stream has a duration that is usually the release time of the chronologically last element in the Stream (that is, the highest onset plus duration of any element in the Stream). However, it can either explicitly set in which case we say that the duration is unlinked Streams may be embedded within other Streams. TODO: Get Stream Duration working -- should be the total length of the Stream. -- see the ._getDuration() and ._setDuration() methods 

Attributes
~~~~~~~~~~

**contexts**

**flattenedRepresentationOf**

**groups**

**isFlat**

**isSorted**

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

**deepcopy()**

**copy()**

**contexts()**


Locally Defined

**transferOffsetToElements()**

    Transfer the offset of this stream to all internal elements; then set the offset of this stream to zero. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note("C"), range(0,10))
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

**splitByClass()**

    Given a stream, get all objects specified by objName and then form two new streams.  Fx should be a lambda or other function on elements. All elements where fx returns True go in the first stream. All other elements are put in the second stream. 

    >>> a = Stream()
    >>> for x in range(30,81):
    ...     n = note.Note() 
    ...     n.midi = x 
    ...     a.append(n) 
    >>> fx = lambda n: n.midi > 60
    >>> b, c = a.splitByClass(note.Note, fx)
    >>> len(b)
    20 
    >>> len(c)
    31 

**shiftElements()**

    Add offset value to every offset of contained Elements. TODO: add a class filter to set what is shifted 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note("C"), range(0,10))
    >>> a.shiftElements(30)
    >>> a.lowestOffset
    30.0 
    >>> a.shiftElements(-10)
    >>> a.lowestOffset
    20.0 

**repeatCopy()**

    Given an object, create many DEEPcopies at the positions specified by the offset list: 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatCopy(n, [0, 2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11, 12])
    >>> len(a)
    13 
    >>> a[10].offset
    10.0 

**repeatAddNext()**

    Given an object and a number, run addNext that many times on the object. numberOfTimes should of course be a positive integer. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.type = "whole"
    >>> a.repeatAddNext(n, 10)
    >>> a.duration.quarterLength
    40.0 
    >>> a[9].offset
    36.0 

**recurseRepr()**


**pop()**

    return the matched object from the list. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note("C"), range(10))
    >>> junk = a.pop(0)
    >>> len(a)
    9 

**makeTies()**

    Given a stream containing measures, examine each element in the stream if the elements duration extends beyond the measures bound, create a tied  entity. Edits the current stream in-place. TODO: take a list of clases to act as filter on what elements are tied. configure ".previous" and ".next" attributes 

    >>> d = Stream()
    >>> n = note.Note()
    >>> n.quarterLength = 12
    >>> d.repeatAddNext(n, 10)
    >>> d.repeatCopy(n, [x+.5 for x in range(10)])
    >>> #x = d.makeMeasures()
    >>> #x = x.makeTies()

    

**makeRests()**

    Given a streamObj with an Element with an offset not equal to zero, fill with one Rest preeceding this offset. If refStream is provided, use this to get min and max offsets. Rests will be added to fill all time defined within refStream. TODO: rename fillRests() or something else 

    >>> a = Stream()
    >>> a.insertAtOffset(20, note.Note())
    >>> len(a)
    1 
    >>> a.lowestOffset
    20.0 
    >>> b = a.makeRests()
    >>> len(b)
    2 
    >>> b.lowestOffset
    0.0 

**makeMeasures()**

    Take a stream and partition all elements into measures based on one or more TimeSignature defined within the stream. If no TimeSignatures are defined, a default is used. This creates a new stream with Measures, though objects are not copied from self stream. If a meterStream is provided, this is used instead of the meterStream found in the Stream. If a refStream is provided, this is used to provide max offset values, necessary to fill empty rests and similar. 

    >>> a = Stream()
    >>> a.repeatAddNext(note.Rest(), 3)
    >>> b = a.makeMeasures()
    >>> c = meter.TimeSignature('3/4')
    >>> a.insertAtOffset(0.0, c)
    >>> x = a.makeMeasures()
    TODO: Test something here... 
    >>> d = Stream()
    >>> n = note.Note()
    >>> d.repeatAddNext(n, 10)
    >>> d.repeatCopy(n, [x+.5 for x in range(10)])
    >>> x = d.makeMeasures()

**makeBeams()**

    Return a new measure with beams applied to all notes. if inPlace is false, this creates a new, independent copy of the source. TODO: inPlace==False does not work in many cases 

    >>> aMeasure = Measure()
    >>> aMeasure.timeSignature = meter.TimeSignature('4/4')
    >>> aNote = note.Note()
    >>> aNote.quarterLength = .25
    >>> aMeasure.repeatAddNext(aNote,16)
    >>> bMeasure = aMeasure.makeBeams()

**isSequence()**

    A stream is a sequence if it has no overlaps. TODO: check that co-incident boundaries are properly handled 

    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> a.isSequence()
    False 

**insertAtOffset()**

    Append an object with a given offset. Wrap in an Element and set offset time. 

    >>> a = Stream()
    >>> a.insertAtOffset(32, note.Note("B-"))
    >>> a._getHighestOffset()
    32.0 

**insert()**

    Insert in elements by index position. 

    >>> a = Stream()
    >>> a.repeatAddNext(note.Note('A-'), 30)
    >>> a[0].name == 'A-'
    True 
    >>> a.insert(0, note.Note('B'))
    >>> a[0].name == 'B'
    True 

**index()**

    return the index for the specified object 

    >>> a = Stream()
    >>> fSharp = note.Note("F#")
    >>> a.repeatCopy(note.Note("A#"), range(10))
    >>> a.addNext(fSharp)
    >>> a.index(fSharp)
    10 

**groupElementsByOffset()**

    returns a List of lists in which each entry in the main list is a list of elements occurring at the same time. list is ordered by offset (since we need to sort the list anyhow in order to group the elements), so there is no need to call stream.sorted before running this, but it can't hurt. it is DEFINITELY a feature that this method does not find elements within substreams that have the same absolute offset.  See Score.lily for how this is useful.  For the other behavior, call Stream.flat first. 

**getTimeSignatures()**

    Collect all time signatures in this stream. If no TimeSignature objects are defined, get a default Note: this could be a method of Stream. 

    >>> a = Stream()
    >>> b = meter.TimeSignature('3/4')
    >>> a.append(b)
    >>> a.repeatCopy(note.Note("C#"), range(10))
    >>> c = a.getTimeSignatures()
    >>> len(c) == 1
    True 

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

**getPitches()**

    Return all pitches found in any element in the stream as a list (since Pitches have no duration, it's a list not a stream) 

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements that have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeNoneDur. This example demonstrates end-joing overlaps: there are four quarter notes each following each other. Whether or not these count as overalps is determined by the includeCoincidentBoundaries parameter. 

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
    ...     n.offset = x * 1 
    ...     a.append(n) 
    ... 
    >>> # default is to not include coincident boundaries
    >>> d = a.getOverlaps()
    >>> len(d[0])
    7 

**getNotes()**

    Return all Note, Chord, Rest, etc. objects in a Stream() 

**getMeasures()**

    Return all Measure objects in a Stream() 

**getInstrument()**

    Search this stream or parent streams for instruments, otherwise return a default 

    >>> a = Stream()
    >>> b = a.getInstrument()

**getGroups()**

    Get a dictionary for each groupId and the count of instances. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> a.repeatAddNext(n, 30)
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getElementsByOffset()**

    Return a Stream/list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not. The time range is taken as the context for the flat representation. The includeCoincidentBoundaries option determines if an end boundary match is included. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Note("C"), range(10))
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
    # TODO: Fix 
    >>> ### CANNOT FLATTEN IF EMBEDDED --
    >>> ### c = b.flat.getElementsByOffset(2,6.9)
    >>> ###len(c)
    ###10 

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

**getElementsByClass()**

    Return a list of all Elements that match the className. Note that, as this appends Elements to a new Stream, whatever former parent relationship the Element had is lost. The Element's parent is set to the new stream that contains it. 

    >>> a = Stream()
    >>> a.repeatCopy(note.Rest(), range(10))
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
    >>> b.repeatCopy(note.Rest(), range(15))
    >>> a.append(b)
    >>> # here, it gets elements from within a stream
    >>> # this probably should not do this, as it is one layer lower
    >>> found = a.getElementsByClass(note.Rest)
    >>> len(found)
    10 
    >>> found = a.flat.getElementsByClass(note.Rest)
    >>> len(found)
    25 

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

**getElementBeforeOffset()**

    Get element before a provided offset TODO: write this 

**getElementBeforeElement()**

    given an element, get the element before TODO: write this 

**getElementAtOrBefore()**

    Given an offset, find the element at this offset, or with the offset less than and nearest to. Return one element or None if no elements are at or preceded by this offset. TODO: inlcude sort order for concurrent matches? 

    >>> a = Stream()
    >>> x = music21.Music21Object()
    >>> x.id = 'x'
    >>> y = music21.Music21Object()
    >>> y.id = 'y'
    >>> z = music21.Music21Object()
    >>> z.id = 'z'
    >>> a.insertAtOffset(20, x)
    >>> a.insertAtOffset(10, y)
    >>> a.insertAtOffset( 0, z)
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

    

**getElementAtOrAfter()**

    Given an offset, find the element at this offset, or with the offset greater than and nearest to. TODO: write this 

**getElementAfterOffset()**

    Get element after a provided offset TODO: write this 

**getElementAfterElement()**

    given an element, get the element next TODO: write this 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

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
    '{5.0} <music21.note.Note C>\n{6.0} <music21.note.Note B->\n{8.0} <music21.note.Note C>\n' 

**extendDuration()**

    Given a stream and an object name, go through stream and find each object. The time between adjacent objects is then assigned to the duration of each object. The last duration of the last object is assigned to the end of the stream. 

    >>> import music21.dynamics
    >>> stream1 = Stream()
    >>> n = note.QuarterNote()
    >>> n.duration.quarterLength
    1.0 
    >>> stream1.repeatCopy(n, [0, 10, 20, 30, 40])
    >>> dyn = music21.dynamics.Dynamic('ff')
    >>> stream1.insertAtOffset(15, dyn)
    >>> sort1 = stream1.sorted
    >>> sort1[-1].offset # offset of last element
    40.0 
    >>> sort1.duration.quarterLength # total duration
    41.0 
    >>> len(sort1)
    6 
    >>> stream2 = sort1.flat.extendDuration(note.GeneralNote)
    >>> len(stream2)
    6 
    >>> stream2[0].duration.quarterLength
    10.0 
    >>> stream2[1].duration.quarterLength # all note durs are 10
    10.0 
    >>> stream2[-1].duration.quarterLength # or extend to end of stream
    1.0 
    >>> stream2.duration.quarterLength
    41.0 
    >>> stream2[-1].offset
    40.0 
    TODO: Chris; what file is testFiles.ALL[2]?? 
    #        >>> from music21.musicxml import testFiles 
    #        >>> from music21 import converter 
    #        >>> mxString = testFiles.ALL[2] # has dynamics 
    #        >>> a = converter.parse(mxString) 
    #        >>> b = a.flat.extendDuration(dynamics.Dynamic) 

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

**append()**

    Add a (sub)Stream, Music21Object, or object (wrapped into a default element) to the Stream at the stored offset of the object, or at 0.0. For adding to the last open location of the stream, use addNext. Adds an entry in Locations as well. 

    >>> a = Stream()
    >>> a.append(music21.Music21Object())
    >>> a.append(music21.note.Note('G#'))
    >>> len(a)
    2 

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
    ...     n = note.Note("A-") 
    ...     n.duration.quarterLength = 3 
    ...     n.offset = 0 
    ...     notes2.append(n) 
    >>> a.addNext(notes2) # add em all again
    >>> a.highestOffset, a.highestTime
    (15.0, 18.0) 
    >>> a.isSequence()
    True 
    Add a note that already has an offset set 
    >>> n3 = note.Note("B-")
    >>> n3.offset = 1
    >>> n3.duration.quarterLength = 3
    >>> a.addNext(n3)
    >>> a.highestOffset, a.highestTime
    (19.0, 22.0) 

    

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatAddNext(note.Note('A-'), 30)
    >>> a.repeatAddNext(note.Rest(), 30)
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

    

Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**duration**


Locally Defined

**sorted**

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

**semiFlat**


**pitches**

    Return all pitches found in any element in the stream as a list (since Pitches have no duration, it's a list not a stream) 

**notes**

    Return all Note, Chord, Rest, etc. objects in a Stream() 

**mx**

    Create and return a musicxml score. 

    >>> a = note.Note()
    >>> b = Measure()
    >>> b.append(a)
    >>> c = Stream()
    >>> c.append(b)
    >>> mxScore = c.mx

**musicxml**

    Provide a complete MusicXM: representation. 

**measures**

    Return all Measure objects in a Stream() 

**lowestOffset**

    Get start time of element with the lowest offset in the Stream 

    >>> a = Stream()
    >>> a.lowestOffset
    0.0 
    >>> for x in range(3,5):
    ...     e = note.Note('G#') 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.lowestOffset
    9.0 

    

**lily**

    Returns the stream translated into Lilypond format. 

**isGapless**


**highestTime**

    returns the max(el.offset + el.duration.quarterLength) over all elements, usually representing the last "release" in the Stream. The duration of a Stream is usually equal to the highestTime expressed as a Duration object, but can be set separately.  See below. 

**highestOffset**

    Get start time of element with the highest offset in the Stream 

    >>> a = Stream()
    >>> for x in [3, 4]:
    ...     e = note.Note('G#') 
    ...     e.offset = x * 3 
    ...     a.append(e) 
    ... 
    >>> a.highestOffset
    12.0 

    

**flat**

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
    >>> q = Stream()
    >>> for i in range(5):
    ...   p = Stream() 
    ...   p.repeatCopy(music21.Music21Object(), range(5)) 
    ...   q.insertAtOffset(i * 10, p) 
    >>> len(q)
    5 
    >>> qf = q.flat
    >>> len(qf)
    25 
    >>> qf[24].offset
    44.0 

    
    >>> r = Stream()
    >>> for j in range(5):
    ...   q = Stream() 
    ...   for i in range(5): 
    ...      p = Stream() 
    ...      p.repeatCopy(music21.Music21Object(), range(5)) 
    ...      q.insertAtOffset(i * 10, p) 
    ...   r.insertAtOffset(j * 100, q) 
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**elements**



