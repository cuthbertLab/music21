# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         search.serial.py
# Purpose:      music21 classes for serial searching
#
# Authors:      Carl Lian
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -------------------------------------------------
import copy
import unittest

from collections import Counter
from operator import attrgetter

from music21 import base
from music21 import common
from music21 import environment
from music21 import spanner
from music21 import stream
from music21.serial import pcToToneRow, ToneRow

environLocal = environment.Environment()

# ------- parsing functions for atonal music -------


class ContiguousSegmentOfNotes(base.Music21Object):
    '''
    Class whose instantiations represent contiguous segments of notes and chords appearing
    within a :class:`~music21.stream.Stream`. Generally speaking, these objects are instantiated
    internally, though it is possible
    for the user to create them as well.

    >>> s = stream.Stream()
    >>> p = stream.Part()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('d4')
    >>> p.append(n1)
    >>> p.append(n2)
    >>> p = p.makeMeasures()
    >>> s.insert(0, p)
    >>> cdContiguousSegment = search.serial.ContiguousSegmentOfNotes([n1, n2], s, 0)
    >>> cdContiguousSegment
    <music21.search.serial.ContiguousSegmentOfNotes ['C4', 'D4']>

    '''
    _DOC_ATTR = {
        'segment': 'The list of notes and chords in the contiguous segment.',
        'containerStream': '''
            The stream containing the contiguous segment -
            all contiguous segments must have a container stream.''',
        'partNumber': '''
            The part number in which the segment appears, or None
            (if the container stream has no parts). Note that this attribute is zero-indexed,
            so the top (e.g. soprano) part is labeled 0.''',
        'activeSegment': '''
            A list of pitch classes representing the way the contiguous
            segment of notes is being read as a sequence of single pitches. Set to None
            unless the container stream is being searched for segments or multisets
            (for example, using :func:`~music21.search.serial.findSegments`), in which case
            the representation depends on the segments or multisets being searched for.
            If there are no chords in the segment, this attribute will simply give the
            pitch classes of the notes in the segment.''',
        'matchedSegment': '''
            A list of pitch classes representing the segment to which
            the contiguous segment of notes is matched when segments or multisets are
            searched for (for example, using :func:`~music21.search.serial.findSegments`);
            otherwise set to None. Note that the contiguous segment will only be
            matched to one of the segments or multisets being searched for.'''
    }

    _DOC_ORDER = ['startMeasureNumber', 'startOffset', 'zeroCenteredTransformationsFromMatched',
                  'originalCenteredTransformationsFromMatched']

    def __init__(self, segment=None, containerStream=None, partNumber=0):
        super().__init__()
        self.segment = segment
        self.containerStream = containerStream
        self.partNumber = partNumber
        self.matchedSegment = None

    def _reprInternal(self):
        chordList = []
        for ch in self.segment:
            chordPitches = ' '.join(str(p) for p in ch.pitches)
            chordList.append(chordPitches)
        return str(chordList)

    @property
    def startMeasureNumber(self):
        '''The measure number on which the contiguous segment begins.'''
        if self.segment:
            return self.segment[0].measureNumber
        else:
            return None

    @property
    def startOffset(self):
        '''
        The offset of the beginning of the contiguous segment,
        with respect to the measure containing the first note.
        '''
        if self.segment:
            return self.segment[0].offset
        else:
            return None

    def getActiveMatchedRows(self):
        '''
        Returns two ToneRow objects, the activeSegment as ToneRow
        and the matchedSegment as ToneRow
        '''
        if isinstance(self.activeSegment, ToneRow):
            activeRow = self.activeSegment
        else:
            activeRow = pcToToneRow(self.activeSegment)

        if isinstance(self.matchedSegment, ToneRow):
            matchedRow = self.matchedSegment
        else:
            matchedRow = pcToToneRow(self.matchedSegment)
        return(activeRow, matchedRow)

    @property
    def zeroCenteredTransformationsFromMatched(self):
        '''
        The list of zero-centered transformations taking a segment being searched
        for to a found segment, for example, in
        :func:`~music21.search.serial.findTransformedSegments`.
        For an explanation of the zero-centered convention for serial transformations,
        see :meth:`music21.search.serial.ToneRow.zeroCenteredTransformation`.
        '''
        (activeRow, matchedRow) = self.getActiveMatchedRows()
        return matchedRow.findZeroCenteredTransformations(activeRow)

    @property
    def originalCenteredTransformationsFromMatched(self):
        '''The list of original-centered transformations taking a segment being
        searched for to a found segment, for example, in
        :func:`~music21.search.serial.findTransformedSegments`.
        For an explanation of the
        zero-centered convention for serial transformations, see
        :meth:`music21.search.serial.ToneRow.originalCenteredTransformation`.
        '''
        (activeRow, matchedRow) = self.getActiveMatchedRows()
        return matchedRow.findOriginalCenteredTransformations(activeRow)

    def readPitchClassesFromBottom(self):
        '''
        Returns the list of pitch classes in the segment, reading pitches within
        chords from bottom to top.

        >>> sc = stream.Score()
        >>> n1 = note.Note('d4')
        >>> n1.quarterLength = 1
        >>> Cmaj = chord.Chord(['c5', 'e4', 'g4'])
        >>> Cmaj.quarterLength = 1
        >>> sc.append(n1)
        >>> sc.append(Cmaj)
        >>> sc = sc.makeMeasures()
        >>> searcher = search.serial.ContiguousSegmentSearcher(sc)
        >>> segmentList = searcher.byLength(4)
        >>> csn = segmentList[0]
        >>> csn.readPitchClassesFromBottom()
        [2, 0, 4, 7]
        '''
        seg = self.segment
        pitchClasses = []
        for noteOrChord in seg:
            for p in noteOrChord.pitches:
                pitchClasses.append(p.pitchClass)
        return pitchClasses

    def getDistinctPitchClasses(self):
        '''
        Returns a list of distinct pitch classes in the segment, in order of appearance,
        where pitches in a chord are read from bottom to top.

        Does not sort or order.

        >>> sc = stream.Score()
        >>> n1 = note.Note('d4')
        >>> n1.quarterLength = 1
        >>> c = chord.Chord(['d4', 'e4', 'g4', 'd5'])
        >>> c.quarterLength = 1
        >>> sc.append(n1)
        >>> sc.append(c)
        >>> sc = sc.makeMeasures()
        >>> searcher = search.serial.ContiguousSegmentSearcher(sc)
        >>> segmentList = searcher.byLength(4)
        >>> csn = segmentList[0]
        >>> csn.getDistinctPitchClasses()
        [2, 4, 7]
        '''
        seg = self.segment
        pitchClasses = []
        for noteOrChord in seg:
            for p in noteOrChord.pitches:
                if p.pitchClass not in pitchClasses:
                    pitchClasses.append(p.pitchClass)
        return pitchClasses


class ContiguousSegmentSearcher:
    '''
    Class that when given a :class:`~music21.stream.Stream`
    and `.byLength()` is called, returns a
    :class:`~music21.search.serial.ContiguousSegmentOfNotes` objects
    where the desired number of notes in the segment is specified.

    The inputStream is a Score or Part or Opus containing one score..
    Furthermore, all notes must be contained within measures.

    The reps argument specifies how repeated pitch classes are dealt with.
    It may be set to 'skipConsecutive' (default), 'rowsOnly', 'includeAll', or 'ignoreAll'.
    These are explained in detail below.

    The includeChords argument specifies how chords are dealt with. When set to True (default),
    the pitches of all chords
    are read in order from bottom to top, and when set to False, all segments containing
    chords are ignored.

    The main subtleties of this function lie in how each reps setting works in
    conjunction with chords when
    includeChords is set to True, and how the lengths of the segments are measured.
    However, let us first examine what happens when includeChords
    is set to False, to get an idea of how the function works.

    To begin, we create a stream on which we will apply the function.

    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> s.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> s.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> s.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> s.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> s.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> s.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> s.append(n7)

    We can now try to apply this function:

    >>> searcher = search.serial.ContiguousSegmentSearcher(s, 'skipConsecutive', False)
    >>> contiguousList = searcher.byLength(3)
    >>> print(contiguousList)
    [<music21.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['A4', 'B4', 'C5']>]

    .. image:: images/serial-findTransposedSegments.png
       :width: 500

    We now can apply the function, and in doing so we examine in detail each of the reps settings.

    'skipConsecutive' means that whenever immediate repetitions of notes or chords occur,
    only the first instance of the note or chord is included in the segment.
    The durations of the repeated notes,
    do not have to be the same.

    >>> searcher = search.serial.ContiguousSegmentSearcher(s, includeChords=False)
    >>> searcher.reps = 'skipConsecutive'

    >>> skipConsecutiveList = searcher.byLength(3)
    >>> print(skipConsecutiveList)
    [<music21.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['A4', 'B4', 'C5']>]

    >>> [instance.segment for instance in skipConsecutiveList]
    [[<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>],
     [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>]]


    In order to be considered repetition, the spellings of the notes
    in question must be exactly the same:
    enharmonic equivalents are not checked and notes with the
    same pitch in different octaves are considered different.
    To illustrate this, see the example below, in which all three notes,
    with pitch class 0, are considered
    separately.

    >>> new = stream.Stream()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('c5')
    >>> n3 = note.Note('b#5')
    >>> new.append(n1)
    >>> new.append(n2)
    >>> new.append(n3)
    >>> new = new.makeMeasures()

    >>> searcherNew = search.serial.ContiguousSegmentSearcher(new,
    ...       reps='skipConsecutive', includeChords=False)
    >>> foundSegments = searcherNew.byLength(3)
    >>> [seg.segment for seg in foundSegments]
    [[<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note B#>]]


    'rowsOnly' searches only for tone rows, in which all pitch classes
    in the segment must be distinct. Below,
    we are looking for sequences three consecutive notes within the
    stream `s`, all of which have different pitch classes.
    There is only one such set of notes, and by calling the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes` we can
    determine its location (the measure number of its first note).

    We'll return to our original searcher, but make sure that it has measures now:

    >>> searcher = search.serial.ContiguousSegmentSearcher(s.makeMeasures(), includeChords=False)
    >>> searcher.reps = 'rowsOnly'
    >>> rowsOnlyList = searcher.byLength(3)
    >>> [(instance.segment, instance.startMeasureNumber) for instance in rowsOnlyList]
    [([<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>], 4)]

    'includeAll' disregards all repetitions, and simply gets all
    contiguous segments of the specified length (still subject
    to the includeChords setting).

    >>> searcher.reps = 'includeAll'
    >>> includeAllList = searcher.byLength(3)
    >>> for instance in includeAllList:
    ...     print(instance.segment, instance.startMeasureNumber, instance.startOffset)
    [<music21.note.Note G>, <music21.note.Note G>, <music21.note.Note A>] 3 0.0
    [<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>] 3 1.0
    [<music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>] 3 2.0
    [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>] 4 1.0

    Note that there only two total As appear in these segments, despite there being three
    :class:`~music21.note.Note` objects with the A4 as the pitch
    in the stream s; this is because only the first note of each set
    of tied notes is considered. This convention applies to this
    function and all parsing functions below.
    Also note that so far, neither of the first two notes n1, n2
    nor the major third n3 in `s` have been included in any of the
    returned contiguous segments. This is because for each of these,
    any instance of three consecutive notes or chords
    contains the chord n3. This phenomenon also applies to the next example below.

    Finally, when includeChords is set to False, 'ignoreAll' finds all
    contiguous segments containing exactly three distinct pitch
    classes within it. It is unique in that unlike the previous three
    reps settings, the segments returned in fact
    have more than the number of notes specified (3). Rather, they
    each have 3 distinct pitch classes, and some pitch classes
    may be repeated.

    >>> searcher.reps = 'ignoreAll'
    >>> ignoreAllList = searcher.byLength(3)
    >>> [instance.segment for instance in ignoreAllList]
    [[<music21.note.Note G>, <music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>,
      <music21.note.Note B>],
     [<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>],
     [<music21.note.Note A>, <music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>],
     [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>]]

    Let us now examine what happens in the default chord setting,
    in which includeChords is set to True.

    There are two points to remember when considering chords: the first is that all
    chords are read as sequences of single notes,
    from bottom to top. The second is that 'length' always applies to the total
    number of single pitches or pitch classes found
    in the segment, including within chords, and not to the number of notes or chords.
    However, as we will see, when we search
    for contiguous segments of length 4, the returned segments may not have exactly
    4 total notes (possibly existing
    as single notes or within chords), a natural point of confusion.

    Below is a new stream s0.

    >>> s0 = stream.Stream()
    >>> n1 = note.Note('d4')
    >>> maj2nd = chord.Chord(['f4', 'g4'])
    >>> bMaj1 = chord.Chord(['b4', 'd#5', 'f#5'])
    >>> bMaj2 = chord.Chord(['b4', 'd#5', 'f#5'])
    >>> n2 = note.Note('f#4')
    >>> n3 = note.Note('e4')
    >>> n4 = note.Note('a4')
    >>> s0.append([n1, maj2nd, bMaj1, bMaj2, n2, n3, n4])
    >>> s0 = s0.makeMeasures()
    >>> #_DOCS_SHOW s0.show()

    .. image:: images/serial-getContiguousSegmentsOfLength2.png
       :width: 500

    >>> searcher = search.serial.ContiguousSegmentSearcher(s0, 'skipConsecutive', True)
    >>> skipConsecutiveWithChords = searcher.byLength(4)
    >>> [seg.segment for seg in skipConsecutiveWithChords]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>,
      <music21.note.Note A>]]

    Let us look closely at the found segments. First, because reps
    was set to 'skipConsecutive', the second
    B major chord (bMaj2) is never considered, as the chord right
    before it is the same. As was mentioned before,
    not all of the segments found have exactly 4 notes total.
    This is because, for each segment, only a subset
    of the notes contained in the first and last elements are read. Given one of the
    found segments, it will always
    be possible to extract exactly four consecutive pitches from the notes and chords,
    reading in order, so that
    at least one pitch is taken from each of the first and last chords.

    In the first segment, there is one way to extract 4 consecutive pitches:
    we take the D in the first note, read
    the F and G (in that order) from the next chord, and finally,
    reading the last chord from bottom to top, the B
    from the B major chord. Note that no other reading of the segment
    is possible because the D from the first note
    must be used. The second segment in the returned list, on the other
    hand, can be read as a sequence of 4
    consecutive pitches in two ways, both equally valid. We can either take
    the top note of the first chord, and all three
    notes, in order, of the second chord, or both notes of the first chord
    and the bottom two notes of the second chord.

    >>> searcher.reps = 'rowsOnly'
    >>> rowsOnlyChords = searcher.byLength(4)
    >>> rowsOnlyChords
    [<music21.search.serial.ContiguousSegmentOfNotes ['D4', 'F4 G4', 'B4 D#5 F#5']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['F4 G4', 'B4 D#5 F#5']>]

    >>> [seg.segment for seg in rowsOnlyChords]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>]]

    When reps is set to 'rowsOnly', the segments returned are those such that
    each may be read as a sequence
    of 4 pitches, in the same manner as explained above with the 'skipConsecutive' setting,
    such that the sequence
    of 4 pitches constitutes a four-note tone row. Above, the first segment
    corresponds to the row [2, 5, 7, 11], and the
    second may be read as either [5, 7, 11, 3] or [7, 11, 3, 6]. Note that, for example,
    we could not include both
    the B-major chord and the F# that comes right after it in the same segment,
    because there would have to be two
    consecutive instances of the pitch class 6 (corresponding to F#). Similarly,
    we could not include both instances
    of the B-major chord, as, again, we would have a pitch class repeated in
    any resulting four-note row.

    >>> searcher.reps = 'includeAll'
    >>> includeAll = searcher.byLength(4)
    >>> [seg.segment for seg in includeAll]
    [[<music21.note.Note D>, <music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord F4 G4>, <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>, <music21.note.Note E>],
     [<music21.chord.Chord B4 D#5 F#5>, <music21.note.Note F#>,
      <music21.note.Note E>, <music21.note.Note A>]]

    Here, all segments from which sequences of four consecutive pitches can be extracted,
    again with at least
    one pitch coming from each of the first and last elements of the segments, are found.

    >>> searcher.reps = 'ignoreAll'
    >>> ignoreAll = searcher.byLength(4)
    >>> [seg.segment for seg in ignoreAll]
    [[<music21.note.Note D>,
      <music21.chord.Chord F4 G4>,
      <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord F4 G4>,
      <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord F4 G4>,
      <music21.chord.Chord B4 D#5 F#5>,
      <music21.chord.Chord B4 D#5 F#5>],
     [<music21.chord.Chord F4 G4>,
      <music21.chord.Chord B4 D#5 F#5>,
      <music21.chord.Chord B4 D#5 F#5>,
      <music21.note.Note F#>],
     [<music21.chord.Chord B4 D#5 F#5>,
      <music21.chord.Chord B4 D#5 F#5>,
      <music21.note.Note F#>,
      <music21.note.Note E>],
     [<music21.chord.Chord B4 D#5 F#5>,
      <music21.note.Note F#>,
      <music21.note.Note E>],
     [<music21.chord.Chord B4 D#5 F#5>,
      <music21.note.Note F#>,
      <music21.note.Note E>,
      <music21.note.Note A>]]

    When reps is set to 'ignoreAll', the pitch classes from each segment are read by taking,
    in order, the pitch classes
    in the order in which they first appear, where chords are again read from bottom to top.
    For example, in the last segment,
    the first three pitch classes are those in the first chord, from
    bottom to top: 11, 3, and 6. Then, the next pitch class
    appearing is 6, which is disregarded because it has already appeared.
    Finally, the pitch classes 4 and 9 appear in that order.
    There are thus five pitch classes in this segment, in the order [11, 3, 6, 4, 9].

    The segment can be read has having length 4 because four consecutive
    pitch classes, [3, 6, 4, 9], can be read from this sequence
    in such a way that the first pitch class of this subsequence is part of the
    first chord in the segment, and the last pitch class
    is that of the last note of the segment. More generally, in this setting the
    found segments are those which contain at least 4
    distinct pitch classes, but the top note of the first chord (or note), the
    bottom note of the last chord (or note),
    and all pitches of all notes and chords other than the first and last
    contain at most 4 distinct pitch classes.

    OMIT_FROM_DOCS

    >>> import copy
    >>> sc = stream.Score(id='outerScore')
    >>> p = stream.Part(id='toBeCloned')
    >>> n1 = note.Note('f4')
    >>> n2 = note.Note('e4')
    >>> c1 = chord.Chord(['c5', 'd5'])
    >>> c2 = chord.Chord(['c4', 'd4'])
    >>> p.append([n1, n2, c1, c2])
    >>> p = p.makeMeasures()
    >>> p1 = copy.deepcopy(p)
    >>> p1.id = 'clone1'
    >>> sc.insert(0.0, p1)
    >>> p2 = copy.deepcopy(p)
    >>> p2.id = 'clone2'
    >>> sc.insert(0.0, p2)
    >>> searcherNew = search.serial.ContiguousSegmentSearcher(sc, 'ignoreAll')
    >>> allSegments = searcherNew.byLength(3)
    >>> [seg.segment for seg in allSegments]
    [[<music21.note.Note F>, <music21.note.Note E>, <music21.chord.Chord C5 D5>],
     [<music21.note.Note E>, <music21.chord.Chord C5 D5>],
     [<music21.note.Note E>, <music21.chord.Chord C5 D5>, <music21.chord.Chord C4 D4>],
     [<music21.note.Note F>, <music21.note.Note E>, <music21.chord.Chord C5 D5>],
     [<music21.note.Note E>, <music21.chord.Chord C5 D5>],
     [<music21.note.Note E>, <music21.chord.Chord C5 D5>, <music21.chord.Chord C4 D4>]]
    '''

    def __init__(self, inputStream=None, reps='skipConsecutive', includeChords=True):
        self.stream = inputStream
        self.reps = reps
        self.includeChords = includeChords
        self.searchLength = 1
        self.currentNote = None
        self.partNumber = None
        self.chordList = []  # contains Chord or Note objects
        self.activeChordList = []  # can also be Note objects.
        self.totalLength = 0
        self.listOfContiguousSegments = []

        # for ignoreAll, this will reduce the number
        # of possibilities much faster if True
        self.trimToShortestLengthFast = False

    def getSearchBoundMethod(self):
        '''
        Return a search method based on the setting of reps (how to classify repetitions),
        and the includeChord setting.
        '''
        reps = self.reps
        if self.includeChords is False:
            if reps == 'skipConsecutive':
                return self.searchSkipConsecutiveExclude
            elif reps == 'rowsOnly':
                return self.searchRowsOnlyExclude
            elif reps == 'includeAll':
                return self.searchIncludeAllExclude
            elif reps == 'ignoreAll':
                return self.searchIgnoreAllExclude
        else:
            if reps == 'skipConsecutive':
                return self.searchSkipConsecutiveInclude
            elif reps == 'rowsOnly':
                return self.searchRowsOnlyInclude
            elif reps == 'includeAll':
                return self.searchIncludeAllInclude
            elif reps == 'ignoreAll':
                return self.searchIgnoreAllInclude

    def byLength(self, length):
        '''
        Run the current setting for reps and includeChords to find all segments
        of length `length`.
        '''
        self.searchLength = length
        self.listOfContiguousSegments = []
        hasParts = True
        partList = self.stream.recurse().getElementsByClass('Part')
        if not partList:
            partList = [self.stream]
            hasParts = False

        searchMethod = self.getSearchBoundMethod()

        self.listOfContiguousSegments = []
        for partNumber, partObj in enumerate(partList):
            if hasParts is False:
                partNumber = None  #

            self.chordList = []
            self.totalLength = 0  # counts each pitch within a chord once
            for n in partObj.recurse().notes:
                if n.tie is not None and n.tie.type != 'start':
                    continue
                searchMethod(n, partNumber)
        return self.listOfContiguousSegments

    def addActiveChords(self, partNumber):
        csn = ContiguousSegmentOfNotes(self.activeChordList,
                                       self.stream,
                                       partNumber)
        self.listOfContiguousSegments.append(csn)
        return csn

    def searchIncludeAllExclude(self, n, partNumber):
        if len(n.pitches) > 1:
            self.chordList = []
            return False

        chordList = self.chordList

        chordList.append(n)
        self.totalLength = self.totalLength + len(n.pitches)

        if len(chordList) == self.searchLength + 1:
            chordList.pop(0)

        if len(chordList) == self.searchLength:
            self.activeChordList = chordList[:]
            self.addActiveChords(partNumber)
            return True

        return False

    def searchIncludeAllInclude(self, n, partNumber):
        '''
        Returns the number added.
        '''
        numCSNAdded = 0

        chordList = self.chordList
        chordList.append(n)
        self.totalLength = self.totalLength + len(n.pitches)

        lengthOfActive = self.totalLength
        numChordsToDelete = 0

        for i in range(len(chordList)):
            activeChordList = chordList[i:]
            firstChordNumPitches = len(activeChordList[0].pitches)
            lastChordNumPitches = len(activeChordList[-1].pitches)
            if i:
                lengthOfActive -= len(chordList[i - 1].pitches)
            numPitchesMinusFirstLast = lengthOfActive - (firstChordNumPitches + lastChordNumPitches)
            if (lengthOfActive >= self.searchLength
                    and numPitchesMinusFirstLast <= self.searchLength - 2):
                self.activeChordList = activeChordList
                self.addActiveChords(partNumber)
                numCSNAdded += 1
            elif (lengthOfActive >= self.searchLength):
                numChordsToDelete += 1
            else:
                break

        for unused_counter in range(numChordsToDelete):
            removedChord = chordList.pop(0)
            self.totalLength -= len(removedChord.pitches)

        return numCSNAdded

    def searchSkipConsecutiveExclude(self, n, partNumber):
        chordList = self.chordList
        if chordList and chordList[-1].pitches == n.pitches:
            return False

        return self.searchIncludeAllExclude(n, partNumber)

    def searchSkipConsecutiveInclude(self, n, partNumber):
        chordList = self.chordList
        if chordList and chordList[-1].pitches == n.pitches:
            return False

        return self.searchIncludeAllInclude(n, partNumber)

    def searchIgnoreAllExclude(self, n, partNumber):
        if len(n.pitches) > 1:
            self.chordList = []
            return False

        numCSNAdded = 0
        numChordsToDelete = 0

        chordList = self.chordList
        chordList.append(n)

        for i in range(len(chordList)):
            activeChordList = chordList[i:]
            activePitches = []
            for thisChord in activeChordList:
                activePitches.extend(thisChord.pitches[:])
            uniqueActivePitchClasses = {p.pitchClass for p in activePitches}
            numUniqueActivePitchClasses = len(uniqueActivePitchClasses)
            if numUniqueActivePitchClasses == self.searchLength:
                self.activeChordList = activeChordList
                self.addActiveChords(partNumber)
                if self.trimToShortestLengthFast:
                    numChordsToDelete += 1
                numCSNAdded += 1
            elif numUniqueActivePitchClasses > self.searchLength:
                numChordsToDelete += 1

        for unused_counter in range(numChordsToDelete):
            removedChord = chordList.pop(0)
            self.totalLength -= len(removedChord.pitches)

        return numCSNAdded

    def searchIgnoreAllInclude(self, n, partNumber):
        numCSNAdded = 0
        numChordsToDelete = 0

        chordList = self.chordList
        chordList.append(n)
        for i in range(len(chordList)):
            self.activeChordList = activeChordList = chordList[i:]
            csn = self.addActiveChords(partNumber)
            rowSuperset = set(csn.readPitchClassesFromBottom())
            if len(rowSuperset) >= self.searchLength:
                middleSegment = ContiguousSegmentOfNotes(activeChordList[1:-1], None, None)
                middlePitchClassSet = set(middleSegment.readPitchClassesFromBottom())
                setToCheck = middlePitchClassSet.union([activeChordList[0].pitches[-1].pitchClass,
                                                        activeChordList[-1].pitches[0].pitchClass])
                if (len(setToCheck)) > self.searchLength:
                    self.listOfContiguousSegments.pop()
                    numChordsToDelete += 1
                elif self.trimToShortestLengthFast:
                    numChordsToDelete += 1

            else:
                self.listOfContiguousSegments.pop()
                break

        for unused_counter in range(numChordsToDelete):
            removedChord = chordList.pop(0)
            self.totalLength -= len(removedChord.pitches)

        return numCSNAdded

    def searchRowsOnlyExclude(self, n, partNumber):
        if len(n.pitches) > 1:
            self.chordList = []
            return False

        chordList = self.chordList

        if len(chordList) == self.searchLength:
            chordList.pop(0)

        if n.pitch.pitchClass not in [oldN.pitch.pitchClass for oldN in chordList]:
            chordList.append(n)
        else:
            self.chordList = chordList = [n]

        # all unique....
        if len(chordList) == self.searchLength:
            self.activeChordList = chordList[:]
            self.addActiveChords(partNumber)

    def searchRowsOnlyInclude(self, n, partNumber):
        chordList = self.chordList
        chordList.append(n)
        self.totalLength += len(n.pitches)
        lengthOfActive = self.totalLength
        numChordsToDelete = 0

        for i in range(len(chordList)):
            activeChordList = chordList[i:]
            firstChordNumPitches = len(activeChordList[0].pitches)
            lastChordNumPitches = len(activeChordList[-1].pitches)
            if i:
                lengthOfActive -= len(chordList[i - 1].pitches)

            numPitchesMinusFirstLast = lengthOfActive - (firstChordNumPitches + lastChordNumPitches)
            if (lengthOfActive >= self.searchLength
                    and numPitchesMinusFirstLast <= self.searchLength - 2):
                self.activeChordList = activeChordList
                csn = self.addActiveChords(partNumber)
                rowSuperset = csn.readPitchClassesFromBottom()
                lowerBound = max([0,
                                  len(rowSuperset)
                                    - self.searchLength
                                    - len(self.activeChordList[-1].pitches)
                                    + 1])
                upperBound = min([len(self.activeChordList[0].pitches),
                                  len(rowSuperset) - self.searchLength + 1])
                for j in range(lowerBound, upperBound):
                    if len(set(rowSuperset[j:j + self.searchLength])) == self.searchLength:
                        break
                else:
                    # was not a match, should not have been added,
                    # thus remove from listOfContiguousSegments
                    self.listOfContiguousSegments.pop()

            elif (lengthOfActive >= self.searchLength):
                numChordsToDelete += 1
            else:
                break

        for unused_counter in range(numChordsToDelete):
            removedChord = chordList.pop(0)
            self.totalLength -= len(removedChord.pitches)


class SegmentMatcher:
    '''
    Matches all the ContiguousSegmentsOfNotes (found by ContiguousSegmentSearcher)
    within a :class:`~music21.stream.Stream`
    to one or more segments of pitch classes.

    The inputStream is a :class:`~music21.stream.Stream`; as
    in :class:`~music21.search.serial.ContiguousSegmentSearcher`,
    the inputStream can contain at most one :class:`~music21.stream.Score` and
    its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes.
    The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the
    possible settings are the same as those in
    :class:`~music21.search.serial.ContiguousSegmentSearcher`.

    Returns a list of :class:`~music21.search.serial.ContiguousSegmentOfNotes`
    objects for which the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment`
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.


    >>> sc = stream.Score()
    >>> part = stream.Part()
    >>> sig = meter.TimeSignature('2/4')
    >>> part.append(sig)
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> part.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> part.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> part.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> part.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> part.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> part.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> part.append(n7)
    >>> newPart = part.makeMeasures()
    >>> newPart.makeTies(inPlace=True)
    >>> #_DOCS_SHOW newPart.show()

    .. image:: images/serial-findSegments.png
        :width: 500

    >>> sc.insert(0, newPart)

    >>> matcher = search.serial.SegmentMatcher(sc, includeChords=False)

    >>> GABandABC = matcher.find([[7, 9, 11], [9, 11, 0]])
    >>> print(GABandABC)
    [<music21.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['A4', 'B4', 'C5']>]

    >>> GABandABC[0].segment, GABandABC[1].segment
    ([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>],
     [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>])

    >>> GABandABC[0].startMeasureNumber, GABandABC[1].startMeasureNumber
    (5, 6)

    In case it is not clear, we can use
    the :attr:`~music21.search.serial.ContiguousSegmentsOfNotes.matchedSegment` property
    to determine, to which element of the original searchList the found
    contiguous segments were matched.

    >>> GABandABC[0].matchedSegment
    [7, 9, 11]
    >>> GABandABC[1].matchedSegment
    [9, 11, 0]

    One can also search for segments of different lengths, simultaneously.
    Below, 'B' refers to the
    pitch class 11, which only coincidentally is the same as that of the note B.

    >>> x = (matcher.find([[7, 9, 11], ['B', 0]]))
    >>> x
    [<music21.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['B4', 'C5']>]

    Below, we can see what happens when we include the chords and use ignoreAll

    >>> matcher = search.serial.SegmentMatcher(sc, reps='ignoreAll', includeChords=True)
    >>> [seg.segment for seg in matcher.find([[5, 7, 'B']])]
    [[<music21.note.Note F>, <music21.chord.Chord G4 B4>]]


    As expected, the pitch classes found segment are read
    in the order 5, 7, 11 ('B'), as the pitches
    in the chord are read from bottom to top.

    Consider the following other example with chords, which is somewhat more complex:

    >>> sc0 = stream.Score()
    >>> p0 = stream.Part()
    >>> c1 = chord.Chord(['c4', 'd4'])
    >>> c2 = chord.Chord(['e4', 'f4'])
    >>> p0.append(c1)
    >>> p0.append(c2)
    >>> p0 = p0.makeMeasures()
    >>> sc0.insert(0, p0)

    >>> matcher = search.serial.SegmentMatcher(sc0)
    >>> foundSegments = matcher.find([[0, 2, 4]])
    >>> len(foundSegments)
    1
    >>> seg = foundSegments[0]
    >>> seg.segment
    [<music21.chord.Chord C4 D4>, <music21.chord.Chord E4 F4>]
    >>> seg.activeSegment
    [0, 2, 4]

    If we are just searching for a single term, the list-of-lists can be
    given just as a list:

    >>> foundSegments = matcher.find([2, 4, 5])
    >>> len(foundSegments)
    1
    >>> seg = foundSegments[0]
    >>> seg.segment
    [<music21.chord.Chord C4 D4>, <music21.chord.Chord E4 F4>]
    >>> seg.activeSegment
    [2, 4, 5]

    In the two function calls, despite the fact that two different segments
    of pitch classes were searched for, the same
    :class:`~music21.search.serial.ContiguousSegmentOfNotes` object was found for each.
    This is because the found object can be read
    in two ways as a sequence of three pitch classes: either as [0, 2, 4], by
    taking the two notes of the first chord in order
    and the bottom note of the second, or as [2, 4, 5], by taking the top
    note of the first chord and the two notes of the second
    chord in order. Both times, the chords are read from bottom to top.

    >>> matcher = search.serial.SegmentMatcher(sc, includeChords=False)
    >>> foundSegments = matcher.find([[7, -3, 11], [9, 11, 0]])

    >>> for a in foundSegments:
    ...    print(a.matchedSegment)
    [7, -3, 11]
    [9, 11, 0]

    >>> len(foundSegments)
    2

    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> n3 = note.Note('g4')
    >>> c = chord.Chord(['b4', 'g5', 'a5'])
    >>> s.append(n1)
    >>> s.append(n2)
    >>> s.append(n3)
    >>> s.append(c)
    >>> s = s.makeMeasures()

    >>> matcher = search.serial.SegmentMatcher(s, 'ignoreAll')
    >>> foundSegments = matcher.find([4, -7, 7])

    >>> [seg.segment for seg in foundSegments]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]

    >>> foundSegments = matcher.find([7, 'B', 9])
    >>> [seg.segment for seg in foundSegments]
    [[<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]]
    '''
    includeMultisetDuplicates = False

    def __init__(self, inputStream, reps='skipConsecutive', includeChords=True):
        self.stream = inputStream
        self._reps = reps
        self._includeChords = includeChords
        self.searchedAlready = []
        self.matchedSegments = []
        self.currentSearchSegmentLength = 0
        self._contiguousSegmentsByLength = {}

    @property
    def reps(self):
        return self._reps

    @reps.setter
    def reps(self, newReps):
        self._reps = newReps
        self._contiguousSegmentsByLength = {}

    @property
    def includeChords(self):
        '''
        Returns or sets bool on whether chords should be included.

        Clears the segment cache when it is changed.
        '''
        return self._includeChords

    @includeChords.setter
    def includeChords(self, newChords):
        self._includeChords = newChords
        self._contiguousSegmentsByLength = {}

    def getContiguousSegmentsByLength(self, searchSegmentLength):
        '''
        Creates a ContiguousSegmentSearcher and finds all segments in
        self.stream based on the .reps and .includeChords settings and
        the searchSegmentLength

        If we are searching on lots of segments to match, then we could
        end up running this expensive routine multiple times, so we'll
        cache the answer for each length.

        If .reps or .includeChords is changed, then this will be obsolete,
        so cleared.
        '''
        if searchSegmentLength in self._contiguousSegmentsByLength:
            theseSegments = self._contiguousSegmentsByLength[searchSegmentLength]
        else:
            searcher = ContiguousSegmentSearcher(self.stream, self.reps, self.includeChords)
            theseSegments = searcher.byLength(searchSegmentLength)
            self._contiguousSegmentsByLength[searchSegmentLength] = theseSegments

        return theseSegments

    def find(self, searchList):
        if not searchList:
            return []
        elif not (common.isIterable(searchList[0])):
            # a single list instead of a list of lists:
            searchList = [searchList]

        self.matchedSegments = []
        self.searchedAlready = []
        self._contiguousSegmentsByLength = {}

        for unNormalizedCurrentSearchSegment in searchList:
            # normalize and check.
            if self.checkSearchedAlready(unNormalizedCurrentSearchSegment):
                continue
            currentSearchSegment = self.normalize(unNormalizedCurrentSearchSegment)

            searchSegmentLength = len(unNormalizedCurrentSearchSegment)
            theseSegments = self.getContiguousSegmentsByLength(searchSegmentLength)

            self.currentSearchSegmentLength = searchSegmentLength
            for thisSegment in theseSegments:
                if self.reps == 'ignoreAll':
                    self.findOneIgnoreAll(thisSegment,
                                          currentSearchSegment,
                                          unNormalizedCurrentSearchSegment)
                else:
                    self.findOneOtherReps(thisSegment,
                                          currentSearchSegment,
                                          unNormalizedCurrentSearchSegment)

        return self.matchedSegments

    def findOneIgnoreAll(self, thisSegment, searchSegment, unNormalizedCurrentSearchSegment=None):
        '''
        Checks whether thisSegment is a match for the searchSegment if 'ignoreAll' is the search
        term.

        If so adds it to self.matchedSegments.  Only matches once per segment
        '''
        if unNormalizedCurrentSearchSegment is None:
            unNormalizedCurrentSearchSegment = searchSegment

        length = self.currentSearchSegmentLength
        thisChordList = thisSegment.segment
        pitchClassList = thisSegment.getDistinctPitchClasses()
        lastStartPosition = len(pitchClassList) - len(searchSegment) + 1
        for i in range(lastStartPosition):
            pitchClassSubset = pitchClassList[i:i + length]
            subsetToCheck = self.normalize(pitchClassSubset)
            if not self.equalSubset(searchSegment, subsetToCheck):
                continue
            if pitchClassSubset[0] not in [p.pitchClass for p in thisChordList[0].pitches]:
                continue
            startSeg = thisChordList[:-1]
            startSegPitchClasses = ContiguousSegmentOfNotes(startSeg).readPitchClassesFromBottom()
            if self.includeMultisetDuplicates or pitchClassSubset[-1] not in startSegPitchClasses:
                thisSegment.activeSegment = subsetToCheck
                thisSegment.matchedSegment = list(unNormalizedCurrentSearchSegment)
                self.matchedSegments.append(thisSegment)
                break

    def findOneOtherReps(self, thisSegment, searchSegment, unNormalizedCurrentSearchSegment):
        '''
        Checks whether thisSegment is a match for the searchSegment if 'ignoreAll' is NOT the search
        term.

        If so adds it to self.matchedSegments.  Only matches once per segment
        '''
        if unNormalizedCurrentSearchSegment is None:
            unNormalizedCurrentSearchSegment = searchSegment
        length = self.currentSearchSegmentLength
        thisChordList = thisSegment.segment
        pitchClassList = thisSegment.readPitchClassesFromBottom()
        lowerBound = max([0,
                          len(pitchClassList) - length - len(thisChordList[-1].pitches) + 1])
        upperBound = min([len(thisChordList[0].pitches),
                          len(pitchClassList) + 1 - length])
        for i in range(lowerBound, upperBound):
            subsetToCheck = self.normalize(pitchClassList[i:i + length])
            if not self.equalSubset(searchSegment, subsetToCheck):
                continue
            thisSegment.activeSegment = subsetToCheck
            thisSegment.matchedSegment = list(unNormalizedCurrentSearchSegment)
            self.matchedSegments.append(thisSegment)
            break

    def checkSearchedAlready(self, unNormalizedSearchSegment):
        '''
        Check to see if we have searched this segment already.

        Called out to be subclassible by Transformed searchers.

        If yes, return True.

        If not, add to searchedAlready and return False

        >>> matcher = search.serial.SegmentMatcher(None)
        >>> matcher.checkSearchedAlready([4, 5, 6])
        False
        >>> matcher.checkSearchedAlready([1, 2, 3])
        False
        >>> matcher.checkSearchedAlready([4, 5, 6])
        True
        '''
        currentSearchSegment = self.normalize(unNormalizedSearchSegment)
        if currentSearchSegment in self.searchedAlready:
            return True
        self.searchedAlready.append(currentSearchSegment)
        return False

    @staticmethod
    def normalize(segment):
        '''
        Normalize an input segment for searching. For this class just changes
        letters to numbers, etc.

        Staticmethod:

        >>> search.serial.SegmentMatcher.normalize([3, 4, 5])
        [3, 4, 5]
        >>> search.serial.SegmentMatcher(None).normalize(['B', -24, '1'])
        [11, 0, 1]
        '''
        return pcToToneRow(segment).pitchClasses()

    def equalSubset(self, searchSegment, subsetToCheck):
        '''
        Returns True if these are equal in some way.

        Here's it's simple -- are they equal, but will be harder for other classes.
        '''
        return bool(searchSegment == subsetToCheck)


class TransposedSegmentMatcher(SegmentMatcher):
    '''
    Finds all instances of given contiguous segments of pitch classes, with transpositions,
    within a :class:`~music21.stream.Stream`.

    The inputStream is a :class:`~music21.stream.Stream`; as
    in :class:`~music21.search.serial.ContiguousSegmentSearcher`,
    the inputStream can contain at most one :class:`~music21.stream.Score` and
    its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes.
    The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings
    are the same as those in
    :class:`~music21.search.serial.ContiguousSegmentSearcher`

    Returns a list of :class:`~music21.search.serial.ContiguousSegmentOfNotes` objects
    for which some transposition of the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment` matches at
    least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.


    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> part.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> part.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> part.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> part.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> part.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> part.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> part.append(n7)
    >>> newPart = part.makeMeasures()
    >>> newPart.makeTies(inPlace=True)
    >>> #_DOCS_SHOW newPart.show()

    .. image:: images/serial-findTransposedSegments.png
        :width: 500

    First, note that it is impossible, using the 'ignoreAll' setting,
    to find segments, transposed or not,
    with repeated pitch classes.

    >>> matcher = search.serial.TransposedSegmentMatcher(newPart, 'ignoreAll')
    >>> matcher.find([0, 0])
    []

    A somewhat more interesting example is below.

    >>> matcher = search.serial.TransposedSegmentMatcher(newPart, 'rowsOnly',
    ...                                                            includeChords=False)
    >>> halfStepList = matcher.find([0, 1])
    >>> L = [step.segment for step in halfStepList]
    >>> print(L)
    [[<music21.note.Note E>, <music21.note.Note F>],
     [<music21.note.Note B>, <music21.note.Note C>]]
    >>> [step.startMeasureNumber for step in halfStepList]
    [1, 5]

    In addition to calling the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.startMeasureNumber`
    property
    to return the measure numbers on which the half steps start, one may also call the
    :attr:`~music21.base.Music21Object.measureNumber` property of the
    first :class:`~music21.note.Note` of each segment.

    >>> s = stream.Stream()
    >>> s.repeatAppend(newPart, 2)  # s has two parts, each of which is a copy of newPart.

    >>> sMatcher = search.serial.TransposedSegmentMatcher(s, includeChords=False)
    >>> wholeStepList = sMatcher.find([12, 2])
    >>> [(step.segment, step.startMeasureNumber, step.partNumber) for step in wholeStepList]
    [([<music21.note.Note G>, <music21.note.Note A>], 3, 0),
    ([<music21.note.Note A>, <music21.note.Note B>], 3, 0),
    ([<music21.note.Note G>, <music21.note.Note A>], 3, 1),
    ([<music21.note.Note A>, <music21.note.Note B>], 3, 1)]

    Including chords works similarly as in :class:`~music21.search.serial.findSegments`.

    >>> sMatcher = search.serial.TransposedSegmentMatcher(newPart, includeChords=True)
    >>> foundSegments = sMatcher.find([4, 6, 'A'])
    >>> [seg.segment for seg in foundSegments]
    [[<music21.note.Note F>, <music21.chord.Chord G4 B4>]]

    OMIT_FROM_DOCS

    >>> sMatcher = search.serial.TransposedSegmentMatcher(newPart, 'skipConsecutive',
    ...                         includeChords=False)
    >>> testSameSeg = sMatcher.find([(12, 13), (0, 1)])  # duplicates
    >>> len(testSameSeg)
    2
    >>> testSameSeg[0].matchedSegment
    [12, 13]
    >>> sMatcher = search.serial.TransposedSegmentMatcher(newPart, 'rowsOnly',
    ...                         includeChords=False)
    >>> sMatcher.find([9, 'A', 'B'])
    []

    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> n3 = note.Note('g4')
    >>> c = chord.Chord(['b4', 'g5', 'a5'])
    >>> s.append(n1)
    >>> s.append(n2)
    >>> s.append(n3)
    >>> s.append(c)
    >>> s = s.makeMeasures()
    >>> sMatcher = search.serial.TransposedSegmentMatcher(s, 'ignoreAll', includeChords=True)
    >>> sMatcher.find([3, 4, 6])
    [<music21.search.serial.ContiguousSegmentOfNotes ['E4', 'F4', 'G4']>]
    >>> sMatcher.find([4, 8, 6])
    [<music21.search.serial.ContiguousSegmentOfNotes ['G4', 'B4 G5 A5']>]
    '''

    @staticmethod
    def normalize(segment):
        '''
        Normalize an input segment for searching. For this class changes to intervals

        Staticmethod:

        >>> search.serial.TransposedSegmentMatcher.normalize([3, 4, 5])
        '11'
        >>> search.serial.TransposedSegmentMatcher.normalize(['12', 'B', 7])
        'E8'
        '''
        return pcToToneRow(segment).getIntervalsAsString()


class TransformedSegmentMatcher(SegmentMatcher):
    '''
    Finds all instances of given contiguous segments of pitch classes,
    with serial transformations,
    within a :class:`~music21.stream.Stream`.

    The inputStream is :class:`~music21.stream.Stream`; as
    in :class:`~music21.search.serial.ContiguousSegmentSearcher`,
    the inputStream can
    contain at most one :class:`~music21.stream.Score`
    and its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes.
    The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings
    are the same as those in
    :class:`~music21.search.serial.ContiguousSegmentSearcher`.

    The convention for serial
    transformations must be specified to either
    'zero' or 'original', as described in
    :meth:`~music21.search.serial.zeroCenteredTransformation` and
    :func:`~music21.search.serial.originalCenteredTransformation` - the default setting
    is 'original', as to relate found segments
    directly to the given segments, without first transposing the given segment to
    begin on the pitch class 0.

    Returns a list of :class:`~music21.search.serial.ContiguousSegmentOfNotes` objects
    for which some transformation of the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment` matches at
    least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.


    >>> n1 = note.Note('c#4')
    >>> n2 = note.Note('e4')
    >>> n3 = note.Note('d#4')
    >>> n4 = note.Note('f4')
    >>> n5 = note.Note('e4')
    >>> n6 = note.Note('g4')
    >>> noteList = [n1, n2, n3, n4, n5, n6]
    >>> part = stream.Part()
    >>> part.append(noteList)
    >>> part = part.makeMeasures()
    >>> #_DOCS_SHOW part.show()

    .. image:: images/serial-findTransformedSegments.png
        :width: 150


    >>> tsMatcher = search.serial.TransformedSegmentMatcher(part, 'rowsOnly',
    ...                 includeChords=False)
    >>> rowInstances = tsMatcher.find([2, 5, 4])

    >>> row = [2, 5, 4]
    >>> len(rowInstances)
    2
    >>> firstInstance = rowInstances[0]
    >>> firstInstance
    <music21.search.serial.ContiguousSegmentOfNotes ['C#4', 'E4', 'D#4']>

    >>> firstInstance.activeSegment, firstInstance.startMeasureNumber
    (<music21.serial.ToneRow 143>, 1)
    >>> firstInstance.activeSegment.pitchClasses()
    [1, 4, 3]
    >>> firstInstance.originalCenteredTransformationsFromMatched
    [('T', 11)]

    We have thus found that the first instance of the row [2, 5, 4] within our
    stream appears as a transposition
    down a semitone, beginning in measure 1. We can do a similar analysis on
    the other instance of the row.

    >>> secondInstance = rowInstances[1]
    >>> secondInstance.activeSegment.pitchClasses(), secondInstance.startMeasureNumber
    ([5, 4, 7], 1)
    >>> secondInstance.zeroCenteredTransformationsFromMatched
    [('RI', 7)]

    Let us give an example of this function used with chords included and reps set to 'ignoreAll'.

    >>> s = stream.Stream()
    >>> n1 = note.Note('e4')
    >>> n2 = note.Note('f4')
    >>> n3 = note.Note('g4')
    >>> c = chord.Chord(['b4', 'g5', 'a5'])
    >>> s.append(n1)
    >>> s.append(n2)
    >>> s.append(n3)
    >>> s.append(c)
    >>> s = s.makeMeasures()

    >>> tsMatcher = search.serial.TransformedSegmentMatcher(s, 'ignoreAll',
    ...                 includeChords=True)
    >>> found643 = tsMatcher.find([6, 4, 3])
    >>> [seg.segment for seg in found643]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]

    >>> found684 = tsMatcher.find([6, 8, 4])
    >>> for seg in found684:
    ...    print(seg.segment)
    [<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]
    [<music21.chord.Chord B4 G5 A5>]

    >>> [seg.activeSegment.pitchClasses() for seg in found684]
    [[7, 11, 9],
     [11, 7, 9]]

    >>> [seg.originalCenteredTransformationsFromMatched for seg in found684]
    [[('R', 3)],
     [('RI', 3)]]

    Pitch classes are extracted from segments in order of appearance, with
    pitches in chords being read from bottom to top.
    However, only the first instance of each pitch class is considered, as seen in the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment` calls.
    As long as the first and last pitch classes in the
    active segment first appear in the first and last elements of
    the found segment, respectively, the segment will be matched to the
    segment being searched for. To make this more clear, consider the
    following example in the same stream s:

    >>> tsMatcher = search.serial.TransformedSegmentMatcher(s, 'includeAll')
    >>> found = tsMatcher.find([4, 0, 4])
    >>> [(seg.segment, seg.activeSegment.pitchClasses()) for seg in found]
    [([<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>], [7, 11, 7])]

    Above, the pitch classes of the found segment are read in the order 7, 11, 7, 9.
    Because a subsequence of this, [7, 11, 7],
    is an inversion of the search segment, [4, 0, 4], and furthermore,
    the first 7 is part of the first note of the segment (G), and
    the last 7 is part of the last chord of the segment, the found segment is
    matched to the segment being searched for.

    OMIT_FROM_DOCS

    >>> s = stream.Stream()
    >>> s.repeatAppend(part, 2)
    >>> tsMatcher = search.serial.TransformedSegmentMatcher(s, includeChords=False)
    >>> testNegativePitchClass = tsMatcher.find([2, -7, 4])
    >>> len(testNegativePitchClass)
    4
    >>> testNegativePitchClass[0].matchedSegment
    [2, -7, 4]
    '''

    def checkSearchedAlready(self, unNormalizedSearchSegment):
        '''
        Here a segment is returned as searchedAlready if it is a transformation
        of a previous search segment.

        >>> transMatcher = search.serial.TransformedSegmentMatcher(None)
        >>> transMatcher.checkSearchedAlready([0, 1, 2])
        False
        >>> transMatcher.checkSearchedAlready([0, 1, 2])
        True
        >>> transMatcher.checkSearchedAlready([0, 1, 3])
        False
        >>> transMatcher.checkSearchedAlready([3, 5, 6])  # RI of 0, 1, 3
        True
        '''
        segmentRow = self.normalize(unNormalizedSearchSegment)
        for usedRow in self.searchedAlready:
            if self.getTransformations(segmentRow, usedRow):
                return True
        self.searchedAlready.append(segmentRow)
        return False

    @staticmethod
    def normalize(segment):
        '''
        Normalize an input segment for searching. For this class changes to intervals

        Staticmethod:

        >>> search.serial.TransformedSegmentMatcher.normalize([3, 4, 5])
        <music21.serial.ToneRow 345>
        >>> search.serial.TransformedSegmentMatcher.normalize(['12', 'B', 7])
        <music21.serial.ToneRow 0B7>
        '''
        return pcToToneRow(segment)

    @staticmethod
    def getTransformations(row1, row2):
        '''
        Returns a list of transformations that transform row1 into row2

        Staticmethod:

        >>> TSM = search.serial.TransformedSegmentMatcher

        >>> TSM.getTransformations(TSM.normalize([3, 4, 5]), TSM.normalize([4, 5, 6]))
        [('P', 3), ('RI', 5)]
        >>> TSM.getTransformations(TSM.normalize(['12', 'B', 7]), TSM.normalize([0, 1, 5]))
        [('I', 0)]
        '''
        return row2.findZeroCenteredTransformations(row1)

    def equalSubset(self, searchSegment, subsetToCheck):
        '''
        Returns True if these are equal in some way.

        If is case two rows are equal if they have a zeroCenteredTransformation of the other.

        >>> TSM = search.serial.TransformedSegmentMatcher(None)
        >>> TSM.equalSubset(TSM.normalize([3, 4, 5]), TSM.normalize([4, 5, 6]))
        True
        >>> TSM.equalSubset(TSM.normalize([0, 1, 2]), TSM.normalize([0, 1, 3]))
        False
        '''
        return bool(self.getTransformations(searchSegment, subsetToCheck))


class MultisetSegmentMatcher(SegmentMatcher):
    '''
    Finds all instances of given multisets of pitch classes
    within a :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, in which the order of the
    elements in the multiset does not matter, but multiple instances
    of the same thing (in this case, same pitch class) are treated as distinct elements.
    Thus, two multisets of pitch classes
    are considered to be equal if and only if the number of times any given
    pitch class appears in one multiset is the same as
    the number of times the pitch class appears in the other multiset.

    The inputStream is :class:`~music21.stream.Stream`; as
    in :class:`~music21.search.serial.ContiguousSegmentSearcher`,
    the inputStream can contain at most one :class:`~music21.stream.Score`
    its notes must be contained in measures. However, the inputStream may have
    multiple parts. The searchList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes.
    Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled;
    the possible settings are the same as those in
    :class:`~music21.search.serial.ContiguousSegmentSearcher`

    Returns a list of :class:`~music21.search.serial.ContiguousSegmentOfNotes`
    objects for the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment`,
    interpreted as a multiset,
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.


    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('e4')
    >>> n2.quarterLength = 4
    >>> n3 = note.Note('f4')
    >>> n3.quarterLength = 4
    >>> n4 = note.Note('e4')
    >>> n4.quarterLength = 4
    >>> n5 = note.Note('g4')
    >>> n5.quarterLength = 4
    >>> part.append(n1)
    >>> part.append(n2)
    >>> part.append(n3)
    >>> part.append(n4)
    >>> part.append(n5)
    >>> part.makeMeasures(inPlace=True)
    >>> part.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note E>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note E>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Note F>
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.note.Note E>
    {16.0} <music21.stream.Measure 5 offset=16.0>
        {0.0} <music21.note.Note G>
        {4.0} <music21.bar.Barline type=final>

    >>> #_DOCS_SHOW part.show()

    .. image:: images/serial-findMultisets.png
        :width: 150


    Find all instances of the multiset [5, 4, 4] in the part

    >>> MSS = search.serial.MultisetSegmentMatcher(part, 'includeAll', includeChords=False)
    >>> EEF = MSS.find([5, 4, 4])
    >>> EEF
    [<music21.search.serial.ContiguousSegmentOfNotes ['E4', 'E4', 'F4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['E4', 'F4', 'E4']>]
    >>> [(seg.activeSegment, seg.startMeasureNumber) for seg in EEF]
    [([4, 4, 5], 1), ([4, 5, 4], 2)]


    >>> MSS = search.serial.MultisetSegmentMatcher(part, 'ignoreAll')
    >>> EF = MSS.find([5, 4])
    >>> EF
    [<music21.search.serial.ContiguousSegmentOfNotes ['E4', 'E4', 'F4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['E4', 'F4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['E4', 'E4', 'F4', 'E4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['E4', 'F4', 'E4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['F4', 'E4']>]

    Consider the following examples, with chords.

    >>> sc0 = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('d4'))
    >>> part0.append(note.Note('e4'))
    >>> part0.append(chord.Chord(['f4', 'e5']))
    >>> part0 = part0.makeMeasures()
    >>> sc0.insert(0, part0)

    >>> MSS = search.serial.MultisetSegmentMatcher(sc0, 'ignoreAll')
    >>> CDE = MSS.find([0, 4, 2])

    >>> [seg.segment for seg in CDE]
    [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]]

    Also:

    >>> sc1 = stream.Score()
    >>> part1 = stream.Part()
    >>> part1.append(note.Note('c4'))
    >>> part1.append(note.Note('d4'))
    >>> part1.append(chord.Chord(['e4', 'f4']))
    >>> part1 = part1.makeMeasures()
    >>> sc1.insert(0, part1)
    >>> searcher = search.serial.ContiguousSegmentSearcher(sc1)
    >>> segmentList = searcher.byLength(3)
    >>> [seg.getDistinctPitchClasses() for seg in segmentList]
    [[0, 2, 4, 5], [2, 4, 5]]

    >>> MSS = search.serial.MultisetSegmentMatcher(sc1)
    >>> CDF = MSS.find([0, 2, 5])
    >>> CDF
    []

    OMIT_FROM_DOCS

    >>> import copy
    >>> s = stream.Score()
    >>> s.insert(0, copy.deepcopy(part))
    >>> s.insert(0, copy.deepcopy(part))
    >>> MSS = search.serial.MultisetSegmentMatcher(part, 'rowsOnly')
    >>> MSS.find([5, 4, 4])
    []
    >>> MSS = search.serial.MultisetSegmentMatcher(s, 'includeAll', includeChords=False)
    >>> testMultiple = MSS.find([[-7, 16, 4], [5, 4, 4]])  # test 5 4 4 twice
    >>> len(testMultiple)
    4
    >>> testMultiple[0].matchedSegment
    [-7, 16, 4]

    >>> sc = stream.Score()
    >>> part = stream.Part()
    >>> part.append(note.Note('c4'))
    >>> part.append(note.Note('d4'))
    >>> part.append(note.Note('e4'))
    >>> part.append(chord.Chord(['f4', 'e5']))
    >>> part = part.makeMeasures()
    >>> sc.insert(0, part)

    >>> MSS = search.serial.MultisetSegmentMatcher(sc, 'ignoreAll')
    >>> CDE = MSS.find([0, 4, 2])
    >>> CDE
    [<music21.search.serial.ContiguousSegmentOfNotes ['C4', 'D4', 'E4']>]
    '''
    includeMultisetDuplicates = True

    def equalSubset(self, searchSegment, subsetToCheck):
        '''
        Returns True if there are the same number of each pitchClass in searchSegment
        as in subsetToCheck
        '''
        searchSegmentCounter = Counter(searchSegment)
        subsetCounter = Counter(subsetToCheck)
        return bool(searchSegmentCounter == subsetCounter)


class TransposedMultisetMatcher(SegmentMatcher):
    '''
    Finds all instances of given multisets of pitch classes, with transpositions,
    within a :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, as described in
    :meth:`~music21.search.serial.findMultisets`.

    The inputStream is :class:`~music21.stream.Stream`; as
    in :class:`~music21.search.serial.ContiguousSegmentSearcher`,
    the inputStream can contain at most one :class:`~music21.stream.Score`
    and its notes must be contained in measures.
    The searchList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes.
    Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the
    possible settings are the same as those in
    :class:`~music21.search.serial.ContiguousSegmentSearcher`.

    Returns a list of :class:`~music21.search.serial.ContiguousSegmentOfNotes` objects
    for some transposition of the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment`,
    interpreted as a multiset,
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.


    >>> part = stream.Part()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('c#4')
    >>> n3 = note.Note('d4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('e-4')
    >>> n6 = note.Note('e4')
    >>> n7 = note.Note('d4')
    >>> for n in [n1, n2, n3, n4, n5, n6, n7]:
    ...    n.quarterLength = 2
    ...    part.repeatAppend(n, 2)
    >>> part = part.makeMeasures()
    >>> #_DOCS_SHOW part.show()

    .. image:: images/serial-findTransposedMultisets.png
        :width: 500

    >>> TMM = search.serial.TransposedMultisetMatcher(part, includeChords=False)
    >>> instanceList = TMM.find([[-9, -10, -11]])
    >>> for instance in instanceList:
    ...    (instance.activeSegment, instance.startMeasureNumber, instance.matchedSegment)
    ([0, 1, 2], 1, [-9, -10, -11])
    ([2, 4, 3], 3, [-9, -10, -11])
    ([3, 4, 2], 5, [-9, -10, -11])


    OMIT_FROM_DOCS


    >>> part2 = stream.Part()
    >>> n1 = chord.Chord(['c4', 'c5'])
    >>> n2 = chord.Chord(['c#4', 'c#5'])
    >>> n3 = chord.Chord(['d4', 'd5'])
    >>> n4 = chord.Chord(['e4', 'e5'])
    >>> n5 = chord.Chord(['e-4', 'e-5'])
    >>> n6 = chord.Chord(['e4', 'e5'])
    >>> n7 = chord.Chord(['d4', 'd5'])
    >>> for n in [n1, n2, n3, n4, n5, n6, n7]:
    ...    n.quarterLength = 1
    ...    part2.append(n)
    >>> part2 = part2.makeMeasures()

    >>> TMM = search.serial.TransposedMultisetMatcher(part2, 'ignoreAll')
    >>> instanceList2 = TMM.find([3, 2, 1])
    >>> [seg.segment for seg in instanceList2]
    [[<music21.chord.Chord C4 C5>, <music21.chord.Chord C#4 C#5>, <music21.chord.Chord D4 D5>],
     [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>],
     [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>,
      <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>],
     [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>,
      <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>],
     [<music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>,
      <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>],
     [<music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>]]
    >>> [seg.matchedSegment for seg in instanceList2]
    [[3, 2, 1], [3, 2, 1], [3, 2, 1],
     [3, 2, 1], [3, 2, 1], [3, 2, 1]]
    '''
    includeMultisetDuplicates = True

    def checkSearchedAlready(self, multiset):
        '''
        searched already uses counters...
        '''
        searchSegmentCounter = {}
        for i in range(12):
            searchSegmentCounter = Counter([(p + i) % 12 for p in multiset])
            if searchSegmentCounter in self.searchedAlready:
                return True
        self.searchedAlready.append(searchSegmentCounter)
        return False

    def equalSubset(self, searchSegment, subsetToCheck):
        '''
        Returns True if there are the same number of each pitchClass in searchSegment
        as in subsetToCheck
        '''
        subsetCounter = Counter(subsetToCheck)
        for i in range(12):
            searchSegmentCounter = Counter([(p + i) % 12 for p in searchSegment])
            if bool(searchSegmentCounter == subsetCounter):
                return True
        return False


class TransposedInvertedMultisetMatcher(TransposedMultisetMatcher):
    '''
    Finds all instances of given multisets of pitch classes, with
    transpositions and inversions, within a :class:`~music21.stream.Stream`.
    A multiset is a generalization of a set, as described in
    :meth:`~music21.search.serial.findMultisets`.

    The inputStream is :class:`~music21.stream.Stream`; as
    in :class:`~music21.search.serial.ContiguousSegmentSearcher`,
    it can contain at most one :class:`~music21.stream.Score`, and
    its notes must be contained in measures. The multisetList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. Note that the
    order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings
    are the same as those in
    :class:`~music21.search.serial.ContiguousSegmentSearcher`

    Returns a list of :class:`~music21.search.serial.ContiguousSegmentOfNotes`
    objects for some transposition or inversion of the
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.activeSegment`,
    interpreted as a multiset,
    matches at least one of the elements of the searchList,
    subject to the settings specified in reps and includeChords.


    >>> s = stream.Stream()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('e-4')
    >>> n3 = note.Note('g4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('c4')
    >>> for n in [n1, n2, n3, n4]:
    ...     n.quarterLength = 1
    ...     s.append(n)
    >>> n5.quarterLength = 4
    >>> s.append(n5)
    >>> s = s.makeMeasures()
    >>> #_DOCS_SHOW s.show()

    .. image:: images/serial-findTransposedAndInvertedMultisets.png
        :width: 150

    >>> transposedMatcher = search.serial.TransposedInvertedMultisetMatcher(s, 'ignoreAll',
    ...                                                               includeChords=False)
    >>> majOrMinTriads = transposedMatcher.find([0, 3, 7])
    >>> majOrMinTriads
    [<music21.search.serial.ContiguousSegmentOfNotes ['C4', 'E-4', 'G4']>,
     <music21.search.serial.ContiguousSegmentOfNotes ['G4', 'E4', 'C4']>]

    Note that if we search for both kinds, we should only find each once.

    >>> bothTriads = transposedMatcher.find([[0, 4, 7], [0, 3, 7]])
    >>> [(maj.segment, maj.startOffset) for maj in bothTriads]
    [([<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>], 0.0),
     ([<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 2.0)]

    In both these cases, the `[0, 4, 7]` search should have matched:

    >>> [maj.matchedSegment for maj in bothTriads]
    [[0, 4, 7], [0, 4, 7]]

    Note that when we search for both [0, 4, 7] and [0, 3, 7], which are related to each other
    by the composition of an inversion and a transposition, each
    found segment is only matched to one
    of the multisets in the searchList; thus each found segment appears
    still appears at most once in the returned list
    of contiguous segments. Accordingly, calling
    :attr:`~music21.search.serial.ContiguousSegmentOfNotes.matchedSegment`
    returns only one element of the searchList for each found segment.

    OMIT_FROM_DOCS

    >>> transposedMatcher = search.serial.TransposedInvertedMultisetMatcher(s, 'rowsOnly',
    ...                                                               includeChords=True)
    >>> majAndMinTriads = transposedMatcher.find([0, 4, 7])
    >>> [maj.segment for maj in majAndMinTriads]
     [[<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>],
      [<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>]]
    '''
    includeMultisetDuplicates = True

    def checkSearchedAlready(self, multiset):
        '''
        since the parent class adds to the list, we check inversions
        first and then return the parent class result
        '''
        for i in range(12):
            searchSegmentCounter = Counter([(-1 * (p + i)) % 12 for p in multiset])
            if searchSegmentCounter in self.searchedAlready:
                return True
        return super().checkSearchedAlready(multiset)

    def equalSubset(self, searchSegment, subsetToCheck):
        '''
        Returns True if there are the same number of each pitchClass in searchSegment
        as in subsetToCheck
        '''
        if super().equalSubset(searchSegment, subsetToCheck):
            return True

        subsetCounter = Counter(subsetToCheck)
        for i in range(12):
            searchSegmentCounter = Counter([(-1 * (p + i)) % 12 for p in searchSegment])
            if bool(searchSegmentCounter == subsetCounter):
                return True
        return False


def _labelGeneral(segmentsToLabel, inputStream, segmentDict, reps, includeChords,
                  labelTransformations=False):
    '''
    Helper function for all but one of the labelling functions below.
    Private because this should only be called
    in conjunction with one of the find(type of set of pitch classes) functions.
    '''
    parts = {}
    if not inputStream.getElementsByClass(stream.Score):
        bigContainer = inputStream
    else:
        bigContainer = inputStream.getElementsByClass(stream.Score)
    if not bigContainer.getElementsByClass(stream.Part):
        hasParts = False
    else:
        parts = bigContainer.getElementsByClass(stream.Part)
        hasParts = True

    segmentList = [segmentDict[label] for label in segmentDict]
    labelList = list(segmentDict)  # dicts are ordered as of Python 3.6 practically, 3.7 officially
    numSearchSegments = len(segmentList)
    numSegmentsToLabel = len(segmentsToLabel)
    reorderedSegmentsToLabel = sorted(segmentsToLabel, key=attrgetter(
        'partNumber', 'startMeasureNumber', 'startOffset'))

    for k in range(numSegmentsToLabel):
        foundSegment = reorderedSegmentsToLabel[k]
        lineLabel = spanner.Line(foundSegment.segment[0], foundSegment.segment[-1])
        if hasParts:
            parts[foundSegment.partNumber].insert(0, lineLabel)
        else:
            bigContainer.insert(0, lineLabel)

        rowToMatch = foundSegment.matchedSegment
        for searchSegmentIndex in range(numSearchSegments):
            if segmentList[searchSegmentIndex] != rowToMatch:
                continue

            label = labelList[searchSegmentIndex]
            firstNote = foundSegment.segment[0]

            # for labelTransformedSegments
            if labelTransformations is False:
                transformations = []
            elif labelTransformations == 'original':
                transformations = foundSegment.originalCenteredTransformationsFromMatched
            elif labelTransformations == 'zero':
                transformations = foundSegment.zeroCenteredTransformationsFromMatched
            else:
                transformations = []

            for trans in transformations:
                label = label + ' ,' + str(trans[0]) + str(trans[1])

            if label not in [lyr.text for lyr in firstNote.lyrics]:
                firstNote.addLyric(label)
            break

    return inputStream


def labelSegments(inputStream, segmentDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of segments of pitch classes in a
    :class:`~music21.stream.Stream`.

    The segmentDict is a dictionary whose keys are names of
    the segments to be searched for, and whose values are the segments of pitch classes.
    The values will be
    turned in to a segmentList, as in :func:`~music21.search.serial.findSegments`.
    All other settings are as in :func:`~music21.search.serial.findSegments` as well.

    Returns a deepcopy of the inputStream with a :class:`~music21.spanner.Line`
    connecting the first and last notes
    of each found segment, and the first note of each found segment labeled
    with a :class:`~music21.note.Lyric`,
    the label being the key corresponding to the segment of pitch classes.
    One should make sure not
    to call this function with too large of a segmentDict, as a note being contained
    in too many segments will result in some spanners not showing.

    >>> part = stream.Part()
    >>> sig = meter.TimeSignature('2/4')
    >>> part.append(sig)
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> part.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> part.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> part.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> part.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> part.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> part.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> part.append(n7)
    >>> newPart = part.makeMeasures()
    >>> newPart.makeTies(inPlace=True)

    We can then label the segment of pitch classes [7, 9, 11], which corresponds to a G,
    followed by an A,
    followed by a B. Let us call this segment "GAB".

    >>> labelGAB = search.serial.labelSegments(newPart, {'GAB':[7, 9, 11]},
    ...    includeChords=False)
    >>> #_DOCS_SHOW labelGAB.show()

    .. image:: images/serial-labelSegments.png
       :width: 500

    >>> len(labelGAB.getElementsByClass(spanner.Line))
    1
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = SegmentMatcher(streamCopy, reps, includeChords).find(segmentList)
    return _labelGeneral(segmentsToLabel, streamCopy, segmentDict, reps, includeChords)


def labelTransposedSegments(inputStream, segmentDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of segments of pitch classes,
    with transpositions, in a :class:`~music21.stream.Stream`.

    The segmentDict is a dictionary whose keys are names of the segments to be
    searched for, and whose values are the segments of pitch classes. The
    values will be turned in to a segmentList, as in
    :func:`~music21.search.serial.findTransposedSegments`.  All other settings are as
    in :func:`~music21.search.serial.findTransposedSegments` as well.

    Returns a deep copy of the inputStream with a
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found segment, and the first note of each found segment labeled with a
    :class:`~music21.note.Lyric`, the label being the key corresponding to the
    segment of pitch classes. One should make sure not to call this function
    with too large of a segmentDict, as a note being contained in too many
    segments will result in some spanners not showing.

    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 6
    >>> part.append(n1)
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 1
    >>> part.append(n2)
    >>> n3 = chord.Chord(['g4', 'b4'])
    >>> n3.quarterLength = 1
    >>> part.append(n3)
    >>> n4 = note.Note('g4')
    >>> n4.quarterLength = 1
    >>> part.repeatAppend(n4, 2)
    >>> n5 = note.Note('a4')
    >>> n5.quarterLength = 3
    >>> part.repeatAppend(n5, 2)
    >>> n6 = note.Note('b4')
    >>> n6.quarterLength = 1
    >>> part.append(n6)
    >>> n7 = note.Note('c5')
    >>> n7.quarterLength = 1
    >>> part.append(n7)
    >>> newPart = part.makeMeasures()
    >>> newPart.makeTies(inPlace=True)

    We have a soprano line; let us now form a bass line.

    >>> bass = stream.Part()
    >>> n8 = note.Note('c3')
    >>> n8.quarterLength = 4
    >>> bass.append(n8)
    >>> r1 = note.Rest()
    >>> r1.quarterLength = 4
    >>> bass.append(r1)
    >>> n9 = note.Note('b2')
    >>> n9.quarterLength = 4
    >>> bass.append(n9)
    >>> r2 = note.Rest()
    >>> r2.quarterLength = 4
    >>> bass.append(r2)
    >>> n10 = note.Note('c3')
    >>> n10.quarterLength = 4
    >>> bass.append(n10)
    >>> newBass = bass.makeMeasures()
    >>> sc = stream.Score()
    >>> import copy
    >>> sc.insert(0, copy.deepcopy(newPart))
    >>> sc.insert(0, copy.deepcopy(newBass))
    >>> labeledSC = search.serial.labelTransposedSegments(sc, {'half':[0, 1]}, 'rowsOnly')
    >>> #_DOCS_SHOW labeledSC.show()

    .. image:: images/serial-labelTransposedSegments.png
       :width: 500

    OMIT_FROM_DOCS

    >>> len(labeledSC.parts[0].getElementsByClass(spanner.Line))
    2
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = TransposedSegmentMatcher(streamCopy, reps, includeChords).find(segmentList)
    return _labelGeneral(segmentsToLabel, streamCopy, segmentDict, reps, includeChords)


def labelTransformedSegments(inputStream,
                             segmentDict,
                             reps='skipConsecutive',
                             includeChords=True,
                             convention='original'):
    '''
    Labels all instances of a given collection of segments of pitch classes,
    with transformations, in a :class:`~music21.stream.Stream`.

    The segmentDict is a dictionary whose keys are names of the segments to be
    searched for, and whose values are the segments of pitch classes. The
    values will be turned in to a segmentList, as in
    :func:`~music21.search.serial.findTransposedSegments`. The last argument specifies
    the convention ('zero' or 'original') used for naming serial
    transformations, as explained in
    :meth:`~music21.search.serial.ToneRow.zeroCenteredTransformation` and
    :meth:`~music21.search.serial.ToneRow.originalCenteredTransformation`.

    All other settings are as in :func:`~music21.search.serial.findTransposedSegments`
    as well.

    Returns a deep copy of the inputStream with a
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found segment, and the first note of each found segment labeled with a
    :class:`~music21.note.Lyric`, the label being the key corresponding to the
    segment of pitch classes. One should make sure not to call this function
    with too large of a segmentDict, as a note being contained in too many
    segments will result in some spanners not showing.

    >>> c1 = chord.Chord(['c#4', 'e4'])
    >>> c2 = chord.Chord(['d#4', 'f4'])
    >>> c3 = chord.Chord(['e4', 'g4'])
    >>> chordList = [c1, c2, c3]
    >>> part = stream.Part()
    >>> for c in chordList:
    ...    c.quarterLength = 4
    ...    part.append(c)
    >>> part = part.makeMeasures()
    >>> labeledPart = search.serial.labelTransformedSegments(part, {'row':[2, 5, 4]})
    >>> #_DOCS_SHOW labeledPart.show()

    .. image:: images/serial-labelTransformedSegments.png
       :width: 500

    Note: the spanners above were moved manually so that they can be more easily
    distinguished from one another.

    OMIT_FROM_DOCS

    >>> [len(n.lyrics) for n in labeledPart.flat.notes]
    [1, 1, 0]
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = TransformedSegmentMatcher(streamCopy, reps, includeChords).find(segmentList)
    return _labelGeneral(
        segmentsToLabel,
        streamCopy,
        segmentDict,
        reps,
        includeChords,
        labelTransformations=convention
    )


def labelMultisets(inputStream, multisetDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of multisets of pitch classes in a
    :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, as described in
    :meth:`~music21.search.serial.findMultisets`.

    The multisetDict is a dictionary whose keys are names of
    the multisets to be searched for, and whose
    values are the segments of pitch classes. The values will be
    turned in to a segmentList, as in :func:`~music21.search.serial.findMultisets`.
    All other settings are as in :func:`~music21.search.serial.findMultisets` as well.

    Returns a deep copy of the inputStream
    with a :class:`~music21.spanner.Line` connecting the first and last notes
    of each found multiset, and the first note of each found multiset
    labeled with a :class:`~music21.note.Lyric`,
    the label being the key corresponding to the segment of pitch classes. One should make sure not
    to call this function with too large of a segmentDict, as a note being contained
    in too many segments will result in some spanners not showing.

    At the present time a relatively large number of multisets are
    found using the 'ignoreAll' setting,
    particularly when there are many repetitions of pitch classes (immediate or otherwise).
    As a result, it is possible that at points in the stream
    there will be more than six spanners active
    simultaneously, which may result in some
    spanners not showing correctly in XML format, or not at all.


    >>> part = stream.Part()
    >>> n1 = note.Note('e4')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('e4')
    >>> n2.quarterLength = 4
    >>> n3 = note.Note('f4')
    >>> n3.quarterLength = 4
    >>> n4 = note.Note('e4')
    >>> n4.quarterLength = 4
    >>> part.append(n1)
    >>> part.append(n2)
    >>> part.append(n3)
    >>> part.append(n4)
    >>> part = part.makeMeasures()
    >>> labeledPart = search.serial.labelMultisets(part, {'EEF':[4, 5, 4]},
    ...                                     reps='includeAll', includeChords=False)
    >>> #_DOCS_SHOW labeledPart.show()

    .. image:: images/serial-labelMultisets.png
        :width: 500

    Note: the spanners above were moved manually so that they can
    be more easily distinguished from one another.

    OMIT_FROM_DOCS

    >>> [len(n.lyrics) for n in labeledPart.flat.notes]
    [1, 1, 0, 0]
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = MultisetSegmentMatcher(streamCopy, reps, includeChords).find(segmentList)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)


def labelTransposedMultisets(inputStream, multisetDict,
                             reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of multisets, with
    transpositions, of pitch classes in a :class:`~music21.stream.Stream`.

    A multiset is a generalization of a set, as described in
    :meth:`~music21.search.serial.findMultisets`.

    The multisetDict is a dictionary whose keys are names of the multisets to
    be searched for, and whose values are the segments of pitch classes. The
    values will be turned in to a segmentList, as in
    :func:`~music21.search.serial.findMultisets`.

    All other settings are as in
    :func:`~music21.search.serial.findTransposedMultisets` as well.

    Returns a deep copy of the inputStream with a
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found multiset, and the first note of each found multiset labeled with a
    :class:`~music21.note.Lyric`, the label being the key corresponding to the
    segment of pitch classes. One should make sure not to call this function
    with too large of a segmentDict, as a note being contained in too many
    segments will result in some spanners not showing.

    At the present time a relatively large number of multisets are found using
    the 'ignoreAll' setting, particularly when there are many repetitions of
    pitch classes (immediate or otherwise). As a result, it is possible that at
    points in the stream there will be more than six spanners active
    simultaneously, which may result in some spanners not showing correctly in
    XML format, or not at all.

    As a diversion, instead of using this tool on atonal music, let us do so on
    Bach.

    We can label all instances of three of the same pitch classes occurring in
    a row in one of the chorales.

    We learn the obvious - it appears that the alto section would be the most
    bored while performing this chorale.

    >>> bach = corpus.parse('bach/bwv57.8')
    >>> bachLabeled = search.serial.labelTransposedMultisets(bach,
    ...                                               {'x3': [0, 0, 0]},
    ...                                               reps='includeAll',
    ...                                               includeChords=False)
    >>> #_DOCS_SHOW bachLabeled.show()

    .. image:: images/serial-labelTransposedMultisets.png
        :width: 500

    Note: the spanners above were moved manually so that they can be more
    easily distinguished from one another.
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = TransposedMultisetMatcher(streamCopy, reps,
                                                includeChords).find(segmentList)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)


def labelTransposedAndInvertedMultisets(inputStream,
                                        multisetDict,
                                        reps='skipConsecutive',
                                        includeChords=True):
    '''
    Labels all instances of a given collection of multisets, with
    transpositions and inversions, of pitch classes in a
    :class:`~music21.stream.Stream`.

    A multiset is a generalization of a set, as described in
    :meth:`~music21.search.serial.findMultisets`.

    The multisetDict is a dictionary whose keys are names of the multisets to
    be searched for, and whose values are the segments of pitch classes. The
    values will be turned in to a segmentList, as in
    :func:`~music21.search.serial.findMultisets`.

    All other settings are as in
    :func:`~music21.search.serial.findTransposedMultisets` as well.

    Returns a deep copy of the inputStream with a
    :class:`~music21.spanner.Line` connecting the first and last notes of each
    found multiset, and the first note of each found multiset labeled with a
    :class:`~music21.note.Lyric`, the label being the key corresponding to the
    segment of pitch classes. One should make sure not to call this function
    with too large of a segmentDict, as a note being contained in too many
    segments will result in some spanners not showing.

    At the present time a relatively large number of multisets are found using
    the 'ignoreAll' setting, particularly when there are many repetitions of
    pitch classes (immediate or otherwise).

    As a result, it is possible that at points in the stream there will be more
    than six spanners active simultaneously, which may result in some spanners
    not showing correctly in XML format, or not at all.

    >>> s = stream.Stream()
    >>> n1 = note.Note('c4')
    >>> n2 = note.Note('e-4')
    >>> n3 = note.Note('g4')
    >>> n4 = note.Note('e4')
    >>> n5 = note.Note('c4')
    >>> for n in [n1, n2, n3, n4]:
    ...     n.quarterLength = 1
    ...     s.append(n)
    >>> n5.quarterLength = 4
    >>> s.append(n5)
    >>> s = s.makeMeasures()

    >>> l = search.serial.labelTransposedAndInvertedMultisets
    >>> #_DOCS_SHOW l(s, {'triad':[0, 4, 7]}, includeChords=False).show()

    .. image:: images/serial-labelTransposedAndInvertedMultisets.png
       :width: 500

    Note: the spanners above were moved manually so that they can be more
    easily distinguished from one another.
    '''

    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = TransposedInvertedMultisetMatcher(streamCopy, reps,
                                                        includeChords).find(segmentList)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)

# --------------------------------------------------------------------


class Test(unittest.TestCase):
    pass


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [
    'ContiguousSegmentSearcher',
    'ContiguousSegmentOfNotes',
    'SegmentMatcher',
    'TransposedSegmentMatcher',
    'TransformedSegmentMatcher',
    'MultisetSegmentMatcher',
    'TransposedMultisetMatcher',
    'TransposedInvertedMultisetMatcher',
    'labelSegments',
    'labelTransposedSegments',
    'labelTransformedSegments',
    'labelMultisets',
    'labelTransposedMultisets',
    'labelTransposedAndInvertedMultisets'
]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

