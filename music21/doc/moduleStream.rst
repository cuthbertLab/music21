music21.stream
==============

Function deepcopy()
-------------------

Deep copy operation on arbitrary Python objects. See the module's __doc__ string for more info. 

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

**keyIsNew**

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addGroupForElements()**


Locally Defined

**setRightBarline()**


**setLeftBarline()**


**measureNumberWithSuffix()**


**addTimeDependentDirection()**


**addRepeat()**


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

**key**

    

    >>> a = Measure()
    >>> a.key = key.KeySignature(0)
    >>> a.key.sharps
    0 

**clef**

    

    >>> a = Measure()
    >>> a.clef = clef.TrebleClef()
    >>> a.clef.sign    # clef is an element
    'G' 


Class Page
----------

Inherits from: stream.Stream, base.Music21Object, object

Totally optional: designation that all the music in this Stream belongs on a single notated page 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addGroupForElements()**


Locally Defined

**pageNumber()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

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


Class Part
----------

Inherits from: stream.Stream, base.Music21Object, object

A Stream subclass for designating music that is considered a single part. May be enclosed in a staff (for instance, 2nd and 3rd trombone on a single staff), may enclose staves (piano treble and piano bass), or may not enclose or be enclosed by a staff (in which case, it assumes that this part fits on one staff and shares it with no other part 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

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


Class Performer
---------------

Inherits from: stream.Stream, base.Music21Object, object

A Stream subclass for designating music to be performed by a single Performer.  Should only be used when a single performer performs on multiple parts.  E.g. Bass Drum and Triangle on separate staves performed by one player. a Part + changes of Instrument is fine for designating most cases where a player changes instrument in a piece.  A part plus staves with individual instrument changes could also be a way of designating music that is performed by a single performer (see, for instance the Piano doubling Celesta part in Lukas Foss's Time Cycle).  The Performer Stream-subclass could be useful for analyses of, for instance, how 5 percussionists chose to play a piece originally designated for 4 (or 6) percussionists in the score. 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

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

A Stream subclass for handling multi-part music. Absolutely optional (the largest containing Stream in a piece could be a generic Stream, or a Part, or a Staff).  And Scores can be embedded in other Scores (in fact, our original thought was to call this class a Fragment because of this possibility of continuous embedding), but we figure that many people will like calling the largest container a Score and that this will become a standard. 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

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


Class Staff
-----------

Inherits from: stream.Stream, base.Music21Object, object

A Stream subclass for designating music on a single staff 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addGroupForElements()**


Locally Defined

**staffLines()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

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

**contexts()**


Locally Defined

**transferOffsetToElements()**

    Transfer the offset of this stream to all internal elements; then set the offset of this stream to zero. 

    >>> a = Stream()
    >>> a.repeatInsert(note.Note("C"), range(0,10))
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

**stripTies()**

    Find all notes that are tied; remove all tied notes, then make the first of the tied notes have a duration equal to that of all tied constituents. Lastly, remove the formerly-tied notes. Presently, this only works if tied notes are sequentual; ultimately this will need to look at .to and .from attributes (if they exist) In some cases (under makeMeasures()) a continuation note will not have a Tie object with a stop attribute set. In that case, we need to look for sequential notes with matching pitches. The matchByPitch option can be used to use this technique. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.quarterLength = 6
    >>> a.append(n)
    >>> m = a.makeMeasures()
    >>> m = m.makeTies()
    >>> len(m.flat.notes)
    2 
    >>>

**splitByClass()**

    Given a stream, get all objects specified by objName and then form two new streams.  Fx should be a lambda or other function on elements. All elements where fx returns True go in the first stream. All other elements are put in the second stream. 

    >>> stream1 = Stream()
    >>> for x in range(30,81):
    ...     n = note.Note() 
    ...     n.offset = x 
    ...     n.midi = x 
    ...     stream1.insert(n) 
    >>> fx = lambda n: n.midi > 60
    >>> b, c = stream1.splitByClass(note.Note, fx)
    >>> len(b)
    20 
    >>> len(c)
    31 

**shiftElements()**

    Add offset value to every offset of contained Elements. 

    >>> a = Stream()
    >>> a.repeatInsert(note.Note("C"), range(0,10))
    >>> a.shiftElements(30)
    >>> a.lowestOffset
    30.0 
    >>> a.shiftElements(-10)
    >>> a.lowestOffset
    20.0 

**repeatInsert()**

    Given an object, create many DEEPcopies at the positions specified by the offset list: 

    >>> a = Stream()
    >>> n = note.Note('G-')
    >>> n.quarterLength = 1
    >>> a.repeatInsert(n, [0, 2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11, 12])
    >>> len(a)
    13 
    >>> a[10].offset
    10.0 

**repeatAppend()**

    Given an object and a number, run append that many times on a deepcopy of the object. numberOfTimes should of course be a positive integer. 

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.type = "whole"
    >>> a.repeatAppend(n, 10)
    >>> a.duration.quarterLength
    40.0 
    >>> a[9].offset
    36.0 

**pop()**

    return the matched object from the list. 

    >>> a = Stream()
    >>> a.repeatInsert(note.Note("C"), range(10))
    >>> junk = a.pop(0)
    >>> len(a)
    9 

**melodicIntervals()**

    returns a Stream of intervals between Notes (and by default, Chords) that follow each other in a stream. the offset of the Interval is the offset of the beginning of the interval (if two notes are adjacent, then it is equal to the offset of the second note) see Stream.findConsecutiveNotes for a discussion of what consecutive notes mean, and which keywords are allowed. The interval between a Note and a Chord (or between two chords) is the interval between pitches[0]. For more complex interval calculations, run findConsecutiveNotes and then use generateInterval returns None of there are not at least two elements found by findConsecutiveNotes See Test.testMelodicIntervals() for usage details. 

    

**makeTies()**

    Given a stream containing measures, examine each element in the stream if the elements duration extends beyond the measures bound, create a tied  entity. Edits the current stream in-place by default.  This can be changed by setting the inPlace keyword to false TODO: take a list of clases to act as filter on what elements are tied. configure ".previous" and ".next" attributes 

    >>> d = Stream()
    >>> n = note.Note()
    >>> n.quarterLength = 12
    >>> d.repeatAppend(n, 10)
    >>> d.repeatInsert(n, [x+.5 for x in range(10)])
    >>> x = d.makeMeasures()
    >>> x = x.makeTies()

    

**makeRests()**

    Given a streamObj with an  with an offset not equal to zero, fill with one Rest preeceding this offset. If refStream is provided, use this to get min and max offsets. Rests will be added to fill all time defined within refStream. TODO: rename fillRests() or something else.  CHRIS: I Don't Understand what refStream does for this method! 

    >>> a = Stream()
    >>> a.insert(20, note.Note())
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

    Take a stream and partition all elements into measures based on one or more TimeSignature defined within the stream. If no TimeSignatures are defined, a default is used. This always creates a new stream with Measures, though objects are not copied from self stream. If a meterStream is provided, this is used instead of the meterStream found in the Stream. If a refStream is provided, this is used to provide max offset values, necessary to fill empty rests and similar. 

    >>> a = Stream()
    >>> a.repeatAppend(note.Rest(), 3)
    >>> b = a.makeMeasures()
    >>> c = meter.TimeSignature('3/4')
    >>> a.insert(0.0, c)
    >>> x = a.makeMeasures()
    TODO: Test something here... 
    >>> d = Stream()
    >>> n = note.Note()
    >>> d.repeatAppend(n, 10)
    >>> d.repeatInsert(n, [x+.5 for x in range(10)])
    >>> x = d.makeMeasures()

**makeBeams()**

    Return a new measure with beams applied to all notes. if inPlace is false, this creates a new, independent copy of the source. In the process of making Beams, this method also updates tuplet types. this is destructive and thus changes an attribute of Durations in Notes. TODO: inPlace=False does not work in many cases 

    >>> aMeasure = Measure()
    >>> aMeasure.timeSignature = meter.TimeSignature('4/4')
    >>> aNote = note.Note()
    >>> aNote.quarterLength = .25
    >>> aMeasure.repeatAppend(aNote,16)
    >>> bMeasure = aMeasure.makeBeams()

**isSequence()**

    A stream is a sequence if it has no overlaps. TODO: check that co-incident boundaries are properly handled 

    >>> a = Stream()
    >>> for x in [0,0,0,0,3,3,3]:
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('whole') 
    ...     n.offset = x * 1 
    ...     a.insert(n) 
    ... 
    >>> a.isSequence()
    False 

**insertAtNativeOffset()**

    inserts the item at the offset that was defined before the item was inserted into a stream (that is item.getOffsetBySite(None); in fact, the entire code is self.insert(item.getOffsetBySite(None), item) 

    >>> n1 = note.Note("F-")
    >>> n1.offset = 20.0
    >>> stream1 = Stream()
    >>> stream1.append(n1)
    >>> n1.getOffsetBySite(stream1)
    0.0 
    >>> n1.offset
    0.0 
    >>> stream2 = Stream()
    >>> stream2.insertAtNativeOffset(n1)
    >>> stream2[0].offset
    20.0 
    >>> n1.getOffsetBySite(stream2)
    20.0 

**insertAtIndex()**

    Insert in elements by index position. 

    >>> a = Stream()
    >>> a.repeatAppend(note.Note('A-'), 30)
    >>> a[0].name == 'A-'
    True 
    >>> a.insertAtIndex(0, note.Note('B'))
    >>> a[0].name == 'B'
    True 

**insert()**

    Inserts an item(s) at the given offset(s) Has three forms: in the two argument form, inserts an element at the given offset: 

    >>> st1 = Stream()
    >>> st1.insert(32, note.Note("B-"))
    >>> st1._getHighestOffset()
    32.0 
    In the single argument form with an object, inserts the element at its stored offset: 
    >>> n1 = note.Note("C#")
    >>> n1.offset = 30.0
    >>> st1 = Stream()
    >>> st1.insert(n1)
    >>> st2 = Stream()
    >>> st2.insert(40.0, n1)
    >>> n1.getOffsetBySite(st1)
    30.0 
    In single argument form list a list of alternating offsets and items, inserts the items 
    at the specified offsets: 
    >>> n1 = note.Note("G")
    >>> n2 = note.Note("F#")
    >>> st3 = Stream()
    >>> st3.insert([1.0, n1, 2.0, n2])
    >>> n1.getOffsetBySite(st3)
    1.0 
    >>> n2.getOffsetBySite(st3)
    2.0 
    >>> len(st3)
    2 

**index()**

    return the index for the specified object 

    >>> a = Stream()
    >>> fSharp = note.Note("F#")
    >>> a.repeatInsert(note.Note("A#"), range(10))
    >>> a.append(fSharp)
    >>> a.index(fSharp)
    10 

**groupElementsByOffset()**

    returns a List of lists in which each entry in the main list is a list of elements occurring at the same time. list is ordered by offset (since we need to sort the list anyhow in order to group the elements), so there is no need to call stream.sorted before running this, but it can't hurt. it is DEFINITELY a feature that this method does not find elements within substreams that have the same absolute offset.  See Score.lily for how this is useful.  For the other behavior, call Stream.flat first. 

**getTimeSignatures()**

    Collect all time signatures in this stream. If no TimeSignature objects are defined, get a default Note: this could be a method of Stream. 

    >>> a = Stream()
    >>> b = meter.TimeSignature('3/4')
    >>> a.insert(b)
    >>> a.repeatInsert(note.Note("C#"), range(10))
    >>> c = a.getTimeSignatures()
    >>> len(c) == 1
    True 

**getSimultaneous()**

    Find and return any elements that start at the same time. 

    >>> stream1 = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 0 
    ...     stream1.insert(n) 
    ... 
    >>> b = stream1.getSimultaneous()
    >>> len(b[0]) == 4
    True 
    >>> stream2 = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     stream2.insert(n) 
    ... 
    >>> d = stream2.getSimultaneous()
    >>> len(d) == 0
    True 

**getPitches()**

    Return all pitches found in any element in the stream as a List (since Pitches have no duration, it's a list not a stream) 

**getOverlaps()**

    Find any elements that overlap. Overlaping might include elements that have no duration but that are simultaneous. Whether elements with None durations are included is determined by includeDurationless. CHRIS: What does this return? and how can someone use this? This example demonstrates end-joing overlaps: there are four quarter notes each following each other. Whether or not these count as overlaps is determined by the includeEndBoundary parameter. 

    >>> a = Stream()
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.duration = duration.Duration('quarter') 
    ...     n.offset = x * 1 
    ...     a.insert(n) 
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
    ...     n.offset = x 
    ...     a.insert(n) 
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
    ...     n.offset = x 
    ...     a.insert(n) 
    ... 
    >>> # default is to not include coincident boundaries
    >>> d = a.getOverlaps()
    >>> len(d[0])
    7 

**getNotes()**

    Return all Note, Chord, Rest, etc. objects in a Stream() as a new Stream 

    >>> s1 = Stream()
    >>> c = chord.Chord(['a', 'b'])
    >>> s1.append(c)
    >>> s2 = s1.getNotes()
    >>> len(s2) == 1
    True 

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
    >>> a.repeatAppend(n, 30)
    >>> a.addGroupForElements('P1')
    >>> a.getGroups()
    {'P1': 30} 
    >>> a[12].groups.append('green')
    >>> a.getGroups()
    {'P1': 30, 'green': 1} 

**getElementsByOffset()**

    Return a Stream of all Elements that are found at a certain offset or within a certain offset time range, specified as start and stop values. If mustFinishInSpan is True than an event that begins between offsetStart and offsetEnd but which ends after offsetEnd will not be included.  For instance, a half note at offset 2.0 will be found in: The includeEndBoundary option determines if an element begun just at offsetEnd should be included.  Setting includeEndBoundary to False at the same time as mustFinishInSpan is set to True is probably NOT what you ever want to do. Setting mustBeginInSpan to False is a good way of finding 

    >>> st1 = Stream()
    >>> n0 = note.Note("C")
    >>> n0.duration.type = "half"
    >>> n0.offset = 0
    >>> st1.insert(n0)
    >>> n2 = note.Note("D")
    >>> n2.duration.type = "half"
    >>> n2.offset = 2
    >>> st1.insert(n2)
    >>> out1 = st1.getElementsByOffset(2)
    >>> len(out1)
    1 
    >>> out1[0].step
    'D' 
    >>> out2 = st1.getElementsByOffset(1, 3)
    >>> len(out2)
    1 
    >>> out2[0].step
    'D' 
    >>> out3 = st1.getElementsByOffset(1, 3, mustFinishInSpan = True)
    >>> len(out3)
    0 
    >>> out4 = st1.getElementsByOffset(1, 2)
    >>> len(out4)
    1 
    >>> out4[0].step
    'D' 
    >>> out5 = st1.getElementsByOffset(1, 2, includeEndBoundary = False)
    >>> len(out5)
    0 
    >>> out6 = st1.getElementsByOffset(1, 2, includeEndBoundary = False, mustBeginInSpan = False)
    >>> len(out6)
    1 
    >>> out6[0].step
    'C' 
    >>> out7 = st1.getElementsByOffset(1, 3, mustBeginInSpan = False)
    >>> len(out7)
    2 
    >>> [el.step for el in out7]
    ['C', 'D'] 
    >>> a = Stream()
    >>> n = note.Note('G')
    >>> n.quarterLength = .5
    >>> a.repeatInsert(n, range(8))
    >>> b = Stream()
    >>> b.repeatInsert(a, [0, 3, 6])
    >>> c = b.getElementsByOffset(2,6.9)
    >>> len(c)
    2 
    >>> c = b.flat.getElementsByOffset(2,6.9)
    >>> len(c)
    10 

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
    >>> s1.append(n1)
    >>> s1.append(n2)
    >>> s1.append(n3)
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

    Return a list of all Elements that match the className. Note that, as this appends Elements to a new Stream, whatever former parent relationship the ElementWrapper had is lost. The ElementWrapper's parent is set to the new stream that contains it. 

    >>> a = Stream()
    >>> a.repeatInsert(note.Rest(), range(10))
    >>> for x in range(4):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3 
    ...     a.insert(n) 
    >>> found = a.getElementsByClass(note.Note)
    >>> len(found)
    4 
    >>> found[0].pitch.accidental.name
    'sharp' 
    >>> b = Stream()
    >>> b.repeatInsert(note.Rest(), range(15))
    >>> a.insert(b)
    >>> # here, it gets elements from within a stream
    >>> # this probably should not do this, as it is one layer lower
    >>> found = a.getElementsByClass(note.Rest)
    >>> len(found)
    10 
    >>> found = a.flat.getElementsByClass(note.Rest)
    >>> len(found)
    25 

**getElementById()**

    Returns the first encountered element for a given id. Return None if no match 

    >>> e = 'test'
    >>> a = Stream()
    >>> a.insert(0, e)
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

    Given an offset, find the element at this offset, or with the offset less than and nearest to. Return one element or None if no elements are at or preceded by this offset. TODO: include sort order for concurrent matches? 

    >>> a = Stream()
    >>> x = music21.Music21Object()
    >>> x.id = 'x'
    >>> y = music21.Music21Object()
    >>> y.id = 'y'
    >>> z = music21.Music21Object()
    >>> z.id = 'z'
    >>> a.insert(20, x)
    >>> a.insert(10, y)
    >>> a.insert( 0, z)
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

    given an element, get the next element.  If classList is specified, check to make sure that the element is an instance of the class list 

    >>> st1 = Stream()
    >>> n1 = note.Note()
    >>> n2 = note.Note()
    >>> r3 = note.Rest()
    >>> st1.append(n1)
    >>> st1.append(n2)
    >>> st1.append(r3)
    >>> t2 = st1.getElementAfterElement(n1)
    >>> t2 is n2
    True 
    >>> t3 = st1.getElementAfterElement(t2)
    >>> t3 is r3
    True 
    >>> t4 = st1.getElementAfterElement(t3)
    >>> t4
    >>> st1.getElementAfterElement("hi")
    Traceback (most recent call last): 
    StreamException: ... 
    >>> t5 = st1.getElementAfterElement(n1, [note.Rest])
    >>> t5 is r3
    True 
    >>> t6 = st1.getElementAfterElement(n1, [note.Rest, note.Note])
    >>> t6 is n2
    True 

**findGaps()**

    returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream or (2) None if there are no gaps. N.B. there may be gaps in the flattened representation of the stream but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless 

**findConsecutiveNotes()**

    Returns a list of consecutive *pitched* Notes in a Stream.  A single "None" is placed in the list at any point there is a discontinuity (such as if there is a rest between two pitches). How to determine consecutive pitches is a little tricky and there are many options. skipUnison uses the midi-note value (.ps) to determine unisons, so enharmonic transitions (F# -> Gb) are also skipped if skipUnisons is true.  We believe that this is the most common usage.  However, because of this, you cannot completely be sure that the x.findConsecutiveNotes() - x.findConsecutiveNotes(skipUnisons = True) will give you the number of P1s in the piece, because there could be d2's in there as well. N.B. for chords, currently, only the first pitch is tested for unison.  this is a bug TODO: FIX See Test.testFindConsecutiveNotes() for usage details. (**keywords is there so that other methods that pass along dicts to findConsecutiveNotes don't have to remove their own args; this method is used in melodicIntervals.) 

**extractContext()**

    extracts elements around the given element within (before) quarter notes and (after) quarter notes (default 4) TODO: maxBefore -- maximum number of elements to return before; etc. 

    >>> from music21 import note
    >>> qn = note.QuarterNote()
    >>> qtrStream = Stream()
    >>> qtrStream.repeatInsert(qn, [0, 1, 2, 3, 4, 5])
    >>> hn = note.HalfNote()
    >>> hn.name = "B-"
    >>> qtrStream.append(hn)
    >>> qtrStream.repeatInsert(qn, [8, 9, 10, 11])
    >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
    >>> hnStream._reprText()
    '{5.0} <music21.note.Note C>\n{6.0} <music21.note.Note B->\n{8.0} <music21.note.Note C>' 

**extendDuration()**

    Given a stream and an object name, go through stream and find each object. The time between adjacent objects is then assigned to the duration of each object. The last duration of the last object is assigned to the end of the stream. 

    >>> import music21.dynamics
    >>> stream1 = Stream()
    >>> n = note.QuarterNote()
    >>> n.duration.quarterLength
    1.0 
    >>> stream1.repeatInsert(n, [0, 10, 20, 30, 40])
    >>> dyn = music21.dynamics.Dynamic('ff')
    >>> stream1.insert(15, dyn)
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

    Returns the clef that is the best fit for notes and chords found in thisStream. Perhaps rename 'getClef'; providing best clef if not clef is defined in this stream; otherwise, return a stream of clefs with offsets 

    

    >>> a = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(60,72)) 
    ...    a.insert(n) 
    >>> b = a.bestClef()
    >>> b.line
    2 
    >>> b.sign
    'G' 
    >>> c = Stream()
    >>> for x in range(30):
    ...    n = note.Note() 
    ...    n.midi = random.choice(range(35,55)) 
    ...    c.insert(n) 
    >>> d = c.bestClef()
    >>> d.line
    4 
    >>> d.sign
    'F' 

**append()**

    Add Music21Objects (including other Streams) to the Stream (or multiple if passed a list) with offset equal to the highestTime (that is the latest "release" of an object), that is, directly after the last element ends. if the objects are not Music21Objects, they are wrapped in ElementWrappers runs fast for multiple addition and will preserve isSorted if True 

    >>> a = Stream()
    >>> notes = []
    >>> for x in range(0,3):
    ...     n = note.Note('G#') 
    ...     n.duration.quarterLength = 3 
    ...     notes.append(n) 
    >>> a.append(notes[0])
    >>> a.highestOffset, a.highestTime
    (0.0, 3.0) 
    >>> a.append(notes[1])
    >>> a.highestOffset, a.highestTime
    (3.0, 6.0) 
    >>> a.append(notes[2])
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
    >>> a.append(notes2) # add em all again
    >>> a.highestOffset, a.highestTime
    (15.0, 18.0) 
    >>> a.isSequence()
    True 
    Add a note that already has an offset set -- does nothing different! 
    >>> n3 = note.Note("B-")
    >>> n3.offset = 1
    >>> n3.duration.quarterLength = 3
    >>> a.append(n3)
    >>> a.highestOffset, a.highestTime
    (18.0, 21.0) 

    

**addGroupForElements()**

    Add the group to the groups attribute of all elements. if classFilter is set then only those elements whose objects belong to a certain class (or for Streams which are themselves of a certain class) are set. 

    >>> a = Stream()
    >>> a.repeatAppend(note.Note('A-'), 30)
    >>> a.repeatAppend(note.Rest(), 30)
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
    >>> s.repeatInsert(note.Note("C#"), [0, 2, 4])
    >>> s.repeatInsert(note.Note("D-"), [1, 3, 5])
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
    >>> y.insert(farRight)
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

    Return all pitches found in any element in the stream as a List (since Pitches have no duration, it's a list not a stream) 

**notes**

    Return all Note, Chord, Rest, etc. objects in a Stream() as a new Stream 

    >>> s1 = Stream()
    >>> c = chord.Chord(['a', 'b'])
    >>> s1.append(c)
    >>> s2 = s1.getNotes()
    >>> len(s2) == 1
    True 

**mx**

    Create and return a musicxml score. 

    >>> n1 = note.Note()
    >>> measure1 = Measure()
    >>> measure1.insert(n1)
    >>> str1 = Stream()
    >>> str1.insert(measure1)
    >>> mxScore = str1.mx

**musicxml**

    Provide a complete MusicXM: representation. 

**measures**

    Return all Measure objects in a Stream() 

**lowestOffset**

    Get start time of element with the lowest offset in the Stream 

    >>> stream1 = Stream()
    >>> stream1.lowestOffset
    0.0 
    >>> for x in range(3,5):
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3.0 
    ...     stream1.insert(n) 
    ... 
    >>> stream1.lowestOffset
    9.0 

    

**lily**

    Returns the stream translated into Lilypond format. 

**isGapless**


**highestTime**

    returns the max(el.offset + el.duration.quarterLength) over all elements, usually representing the last "release" in the Stream. The duration of a Stream is usually equal to the highestTime expressed as a Duration object, but can be set separately.  See below. 

**highestOffset**

    Get start time of element with the highest offset in the Stream 

    >>> stream1 = Stream()
    >>> for x in [3, 4]:
    ...     n = note.Note('G#') 
    ...     n.offset = x * 3.0 
    ...     stream1.insert(n) 
    >>> stream1.highestOffset
    12.0 

    

**flat**

    returns a new Stream where no elements nest within other elements 

    >>> s = Stream()
    >>> s.repeatInsert(note.Note("C#"), [0, 2, 4])
    >>> s.repeatInsert(note.Note("D-"), [1, 3, 5])
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
    ...   p.repeatInsert(music21.Music21Object(), range(5)) 
    ...   q.insert(i * 10, p) 
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
    ...      p.repeatInsert(music21.Music21Object(), range(5)) 
    ...      q.insert(i * 10, p) 
    ...   r.insert(j * 100, q) 
    >>> len(r)
    5 
    >>> len(r.flat)
    125 
    >>> r.flat[124].offset
    444.0 

**elements**



Class System
------------

Inherits from: stream.Stream, base.Music21Object, object

Totally optional: designation that all the music in this Stream belongs in a single system. 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

**addGroupForElements()**


Locally Defined

**systemNumber()**

    int(x[, base]) -> integer Convert a string or number to an integer, if possible.  A floating point argument will be truncated towards zero (this does not include a string representation of a floating point number!)  When converting a string, use the optional base.  It is an error to supply a base when converting a non-string.  If base is zero, the proper base is guessed based on the string content.  If the argument is outside the integer range a long object will be returned instead. 

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


Class Voice
-----------

Inherits from: stream.Stream, base.Music21Object, object

A Stream subclass for declaring that all the music in the stream belongs to a certain "voice" for analysis or display purposes. Note that both Finale's Layers and Voices as concepts are considered Voices here. 

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

**contexts()**


Inherited from stream.Stream

**transferOffsetToElements()**

**stripTies()**

**splitByClass()**

**shiftElements()**

**repeatInsert()**

**repeatAppend()**

**pop()**

**melodicIntervals()**

**makeTies()**

**makeRests()**

**makeMeasures()**

**makeBeams()**

**isSequence()**

**insertAtNativeOffset()**

**insertAtIndex()**

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

**findConsecutiveNotes()**

**extractContext()**

**extendDuration()**

**bestClef()**

**append()**

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


