# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         alpha.search.serial.py
# Purpose:      music21 classes for serial searching
#
# Authors:      Carl Lian
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#--------------------------------------------------
import copy
import unittest
from operator import attrgetter

from music21 import base, note, spanner, stream
from music21 import environment
environLocal = environment.Environment()

from music21.serial import pcToToneRow, SerialException
# ------- parsing functions for atonal music -------

def _checkMultisetEquivalence(multiset1, multiset2):
    '''
    Boolean describing if two multisets of pitch classes are the same.   
    
    >>> alpha.search.serial._checkMultisetEquivalence([3, 4, 5], [3, 3, 4, 5])
    False
    >>> alpha.search.serial._checkMultisetEquivalence([10, 'A', -7], [-2, 5, -2])
    True
    '''    
    if len(multiset1) != len(multiset2):
        return False
    else:
        
        row1 = pcToToneRow(multiset1)
        multiset1 = row1.pitchClasses()
        
        row2 = pcToToneRow(multiset2)
        multiset2 = row2.pitchClasses()
        
        uniqueelements = set(multiset1)
        tempsame = True
        for i in uniqueelements:
            if tempsame == True:
                if multiset1.count(i) != multiset2.count(i):
                    tempsame = False
        return tempsame


class ContiguousSegmentOfNotes(base.Music21Object):
    '''
    Class whose instantiations represent contiguous segments of notes and chords appearing
    within a :class:`~music21.stream.Stream`. Generally speaking, these objects are instantiated 
    internally, though it is possible
    for the user to create them as well. 
    '''
    matchedSegment = None
    
    _DOC_ATTR = {
    'segment': 'The list of notes and chords in the contiguous segment.',
    'containerStream': '''The stream containing the contiguous segment - 
        all contiguous segments must have a container stream.''',
    'partNumber': '''The part number in which the segment appears, or None 
        (if the container stream has no parts). Note that this attribute is zero-indexed, 
        so the top (e.g. soprano) part is labeled 0.''',
    'activeSegment': '''A list of pitch classes representing the way the contiguous 
        segment of notes is being read as a sequence of single pitches. Set to None 
        unless the container stream is being searched for segments or multisets 
        (for example, using :func:`~music21.alpha.search.serial.findSegments`), in which case 
        the representation depends on the segments or multisets being searched for. 
        If there are no chords in the segment, this attribute will simply give the 
        pitch classes of the notes in the segment.''',
    'matchedSegment': '''A list of pitch classes representing the segment to which 
        the contiguous segment of notes is matched when segments or multisets are 
        searched for (for example, using :func:`~music21.alpha.search.serial.findSegments`); 
        otherwise set to None. Note that the contiguous segment will only be 
        matched to one of the segments or multisets being searched for.'''
    }
    
    _DOC_ORDER = ['startMeasureNumber', 'startOffset', 'zeroCenteredTransformationsFromMatched', 
                  'originalCenteredTransformationsFromMatched']

    def __init__(self, segment=None, containerStream=None, partNumber=0):
        '''
        >>> s = stream.Stream()
        >>> p = stream.Part()
        >>> n1 = note.Note('c4')
        >>> n2 = note.Note('d4')
        >>> p.append(n1)
        >>> p.append(n2)
        >>> p = p.makeMeasures()
        >>> s.insert(0, p)
        >>> CD_ContiguousSegment = alpha.search.serial.ContiguousSegmentOfNotes([n1, n2], s, 0)
        '''
        base.Music21Object.__init__(self)        
        self.segment = segment
        self.containerStream = containerStream
        self.partNumber = partNumber
        
    def __repr__(self):
        chordList = []
        for ch in self.segment:
            chordPitches = ' '.join(str(p) for p in ch.pitches)
            chordList.append(chordPitches)
        return '<music21.alpha.search.serial.ContiguousSegmentOfNotes {}>'.format(chordList)
        
    @property
    def startMeasureNumber(self):
        '''The measure number on which the contiguous segment begins.'''
        if (len(self.segment)):
            return self.segment[0].measureNumber
        else:
            return None
    
    @property
    def startOffset(self):
        '''
        The offset of the beginning of the contiguous segment, 
        with respect to the measure containing the first note.        
        '''
        if (len(self.segment)):
            return self.segment[0].offset
        else:
            return None
    
    @property
    def zeroCenteredTransformationsFromMatched(self):
        '''
        The list of zero-centered transformations taking a segment being searched 
        for to a found segment, for example, in 
        :func:`~music21.alpha.search.serial.findTransformedSegments`. 
        For an explanation of the zero-centered convention for serial transformations, 
        see :meth:`music21.alpha.search.serial.ToneRow.zeroCenteredTransformation`.
        '''
        activeRow = pcToToneRow(self.activeSegment)
        matchedRow = pcToToneRow(self.matchedSegment)
        return matchedRow.findZeroCenteredTransformations(activeRow)
    
    @property
    def originalCenteredTransformationsFromMatched(self):
        '''The list of original-centered transformations taking a segment being 
        searched for to a found segment, for example, in 
        :func:`~music21.alpha.search.serial.findTransformedSegments`. 
        For an explanation of the 
        zero-centered convention for serial transformations, see 
        :meth:`music21.alpha.search.serial.ToneRow.originalCenteredTransformation`.'''        
        activeRow = pcToToneRow(self.activeSegment)
        matchedRow = pcToToneRow(self.matchedSegment)
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
        >>> searcher = alpha.search.serial.ContiguousSegmentSearcher(sc)
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
        >>> searcher = alpha.search.serial.ContiguousSegmentSearcher(sc)
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

 
 
class ContiguousSegmentSearcher(object):
    '''
    Class that when given a :class:`~music21.stream.Stream`
    and `.byLength()` is called, returns a
    :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` objects 
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
    
    >>> searcher = alpha.search.serial.ContiguousSegmentSearcher(s, 'skipConsecutive', False)
    >>> contiglist = searcher.byLength(3)
    >>> print(contiglist)
    []

    On our first attempt, no contiguous segments of notes were found above 
    because the inputStream has no measures -
    hence we replace s with s.makeNotation().

    >>> s = s.makeNotation()

    .. image:: images/serial-findTransposedSegments.png
       :width: 500

    We now can apply the function, and in doing so we examine in detail each of the reps settings.
    
    'skipConsecutive' means that whenever immediate repetitions of notes or chords occur, 
    only the first instance of the note or chord is included in the segment. 
    The durations of the repeated notes,
    do not have to be the same.
    
    >>> searcher = alpha.search.serial.ContiguousSegmentSearcher(s, includeChords=False)
    >>> searcher.reps = 'skipConsecutive'

    >>> skipConsecutiveList = searcher.byLength(3)
    >>> print(skipConsecutiveList)
    [<music21.alpha.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>, 
     <music21.alpha.search.serial.ContiguousSegmentOfNotes ['A4', 'B4', 'C5']>]
     
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

    >>> searcherNew = alpha.search.serial.ContiguousSegmentSearcher(new, 
    ...       reps='skipConsecutive', includeChords=False)
    >>> foundSegs = searcherNew.byLength(3)
    >>> [seg.segment for seg in foundSegs]
    [[<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note B#>]]

    
    'rowsOnly' searches only for tone rows, in which all pitch classes 
    in the segment must be distinct. Below,
    we are looking for sequences three consecutive notes within the 
    stream `s`, all of which have different pitch classes.
    There is only one such set of notes, and by calling the 
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` we can
    determine its location (the measure number of its first note).  

    We'll return to our original searcher:

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
    >>> bmaj1 = chord.Chord(['b4', 'd#5', 'f#5'])
    >>> bmaj2 = chord.Chord(['b4', 'd#5', 'f#5'])
    >>> n2 = note.Note('f#4')
    >>> n3 = note.Note('e4')
    >>> n4 = note.Note('a4')
    >>> s0.append([n1, maj2nd, bmaj1, bmaj2, n2, n3, n4])
    >>> s0 = s0.makeMeasures()
    >>> #_DOCS_SHOW s0.show()
    
    .. image:: images/serial-getContiguousSegmentsOfLength2.png
       :width: 500
    
    >>> searcher = alpha.search.serial.ContiguousSegmentSearcher(s0, 'skipConsecutive', True)
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
    B major chord (bmaj2) is never considered, as the chord right 
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
    [<music21.alpha.search.serial.ContiguousSegmentOfNotes ['D4', 'F4 G4', 'B4 D#5 F#5']>,
     <music21.alpha.search.serial.ContiguousSegmentOfNotes ['F4 G4', 'B4 D#5 F#5']>]
    
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
    >>> searcherNew = alpha.search.serial.ContiguousSegmentSearcher(sc, 'ignoreAll')
    >>> allSegs = searcherNew.byLength(3)
    >>> [seg.segment for seg in allSegs]
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
        self.chordList = [] # contains Chord or Note objects
        self.activeChordList = [] # can also be Note objects.
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
        if len(partList) == 0:
            partList = [self.stream]
            hasParts = False
          
        searchMethod = self.getSearchBoundMethod()   
         
        self.listOfContiguousSegments = []
        for partNumber, partObj in enumerate(partList):
            measures = partObj.getElementsByClass(stream.Measure)
            if hasParts is False:
                partNumber = None  # 
                 
            self.chordList = []
            self.totalLength = 0 # counts each pitch within a chord once
            for n in measures.recurse().notes:
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
        self.lengthOfActive = self.totalLength
        
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
            uniqueActivePitchClasses = set([p.pitchClass for p in activePitches])
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

class SegmentMatcher(object):
    '''
    Matches all the ContiguousSegmentsOfNotes (found by ContiguousSegmentSearcher)
    within a :class:`~music21.stream.Stream`
    to one or more segments of pitch classes.

    The inputStream is a :class:`~music21.stream.Stream`; as 
    in :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`, 
    the inputStream can contain at most one :class:`~music21.stream.Score` and
    its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes. 
    The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the 
    possible settings are the same as those in
    :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`.
    
    Returns a list of :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` 
    objects for which the
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment` 
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
    >>> newpart = part.makeMeasures()
    >>> newpart.makeTies()
    >>> #_DOCS_SHOW newpart.show()
    
    .. image:: images/serial-findSegments.png
        :width: 500
    
    >>> sc.insert(0, newpart)

    >>> matcher = alpha.search.serial.SegmentMatcher(sc, includeChords=False)
    >>> GABandABC = matcher.find([[7, 9, 11], [9, 11, 0]])
    >>> print(GABandABC)
    [<music21.alpha.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>, 
     <music21.alpha.search.serial.ContiguousSegmentOfNotes ['A4', 'B4', 'C5']>]

    >>> GABandABC[0].segment, GABandABC[1].segment
    ([<music21.note.Note G>, <music21.note.Note A>, <music21.note.Note B>], 
     [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note C>])
    
    >>> GABandABC[0].startMeasureNumber, GABandABC[1].startMeasureNumber
    (5, 6)
    
    In case it is not clear, we can use 
    the :attr:`~music21.alpha.search.serial.ContiguousSegmentsOfNotes.matchedSegment` property
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
    [<music21.alpha.search.serial.ContiguousSegmentOfNotes ['G4', 'A4', 'B4']>, 
     <music21.alpha.search.serial.ContiguousSegmentOfNotes ['B4', 'C5']>]
    
    Below, we can see what happens when we include the chords and use ignoreAll
    
    >>> matcher = alpha.search.serial.SegmentMatcher(sc, reps='ignoreAll', includeChords=True)
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

    >>> matcher = alpha.search.serial.SegmentMatcher(sc0)
    >>> foundSegments = matcher.find([[0, 2, 4]])
    >>> len(foundSegments)
    1
    >>> seg = foundSegments[0]
    >>> seg.segment
    [<music21.chord.Chord C4 D4>, <music21.chord.Chord E4 F4>]
    >>> seg.activeSegment
    [0, 2, 4]

    >>> foundSegments = matcher.find([[2, 4, 5]])
    >>> len(foundSegments)
    1
    >>> seg = foundSegments[0]
    >>> seg.segment
    [<music21.chord.Chord C4 D4>, <music21.chord.Chord E4 F4>]
    >>> seg.activeSegment
    [2, 4, 5]
    
    In the two function calls, despite the fact that two different segments 
    of pitch classes were searched for, the same
    :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` object was found for each. 
    This is because the found object can be read
    in two ways as a sequence of three pitch classes: either as [0, 2, 4], by 
    taking the two notes of the first chord in order
    and the bottom note of the second, or as [2, 4, 5], by taking the top 
    note of the first chord and the two notes of the second
    chord in order. Both times, the chords are read from bottom to top.
    
    >>> matcher = alpha.search.serial.SegmentMatcher(sc, includeChords=False)
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

    >>> matcher = alpha.search.serial.SegmentMatcher(s, 'ignoreAll')
    >>> foundSegs = matcher.find([[4, -7, 7]])

    >>> [seg.segment for seg in foundSegs]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]
    
    >>> foundSegs = matcher.find([[7, 'B', 9]])
    >>> [seg.segment for seg in foundSegs]
    [[<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]]
    '''
    def __init__(self, inputStream, reps='skipConsecutive', includeChords=True):
        self.stream = inputStream
        self.reps = reps
        self.includeChords = includeChords
        self.searchedAlready = []
        self.matchedSegments = []
        self.currentSearchSegmentLength = 0
        
    def find(self, searchList):
        self.matchedSegments = []
        self.searchedAlready = []
        self.contiguousSegmentsByLength = {}
        
        for unNormalizedCurrentSearchSegment in searchList:
            currentSearchSegment = self.normalize(unNormalizedCurrentSearchSegment)
            if self.isAlreadySearched(currentSearchSegment):
                continue
            self.searchedAlready.append(currentSearchSegment)
            searchSegmentLength = len(currentSearchSegment)
            if searchSegmentLength in self.contiguousSegmentsByLength:
                theseSegments = self.contiguousSegmentsByLength[searchSegmentLength]
            else:
                searcher = ContiguousSegmentSearcher(self.stream, self.reps, self.includeChords)
                theseSegments = searcher.byLength(searchSegmentLength)
                self.contiguousSegmentsByLength[searchSegmentLength] = theseSegments
                
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
            subsetToCheck = pitchClassList[i:i + length]
            if searchSegment != subsetToCheck:
                continue
            if subsetToCheck[0] not in [p.pitchClass for p in thisChordList[0].pitches]:
                continue
            startSeg = thisChordList[:-1]
            startSegPitchClasses = ContiguousSegmentOfNotes(startSeg).readPitchClassesFromBottom()
            if subsetToCheck[-1] not in startSegPitchClasses:
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
        pitchClassList = thisSegment.getDistinctPitchClasses()
        lowerBound = max([0,
                          len(pitchClassList) - length - len(thisChordList[-1].pitches) + 1])
        upperBound = min([len(thisChordList[0].pitches),
                          len(pitchClassList) + 1 - length])
        for i in range(lowerBound, upperBound):
            subsetToCheck = pitchClassList[i:i + length]
            if subsetToCheck != searchSegment:
                continue
            thisSegment.activeSegment = subsetToCheck
            thisSegment.matchedSegment = list(unNormalizedCurrentSearchSegment)
            self.matchedSegments.append(thisSegment)
            break
                
                
    def isAlreadySearched(self, currentSearchSegment):
        '''
        Returns bool on wheterh this segment has already been found.
        '''
        searchRow = pcToToneRow(currentSearchSegment)
        for alreadySearchedSegment in self.searchedAlready:
            alreadySearchedRow = pcToToneRow(alreadySearchedSegment)
            if searchRow.isSameRow(alreadySearchedRow):
                return True
        return False
    
    @staticmethod
    def normalize(segment):
        '''
        Normalize an input segment for searching.  By default just changes
        letters to numbers, etc.
        
        Staticmethod:
        
        >>> alpha.search.serial.SegmentMatcher.normalize([3, 4, 5])
        [3, 4, 5]
        >>> alpha.search.serial.SegmentMatcher(None).normalize(['B', -24, '1'])
        [11, 0, 1]
        '''
        return pcToToneRow(segment).pitchClasses()
        
    
def findSegments(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    # deprecated; to be removed
    # pylint: disable=line-too-long,duplicate-code
    
    numsegs = len(searchList)
    segs = []
    doneAlready = []
    contigdict = {}
    
    for k in range(numsegs):
        currentSearchSegment = searchList[k]
        currentSearchSegmentCopy = list(currentSearchSegment)
        used = False
        searchRow = pcToToneRow(currentSearchSegment)
        currentSearchSegment = searchRow.pitchClasses()
        for usedsegment in doneAlready:
            if used == False:
                used = searchRow.isSameRow(pcToToneRow(usedsegment))
        if used == False:
            doneAlready.append(currentSearchSegment)
            length = len(currentSearchSegment)
            if length in contigdict:
                contig = contigdict[length]
            else:
                searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                contig = searcher.byLength(length)
                contigdict[length] = contig        
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(len(pitchList) - len(currentSearchSegment) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+length]
                            if currentSearchSegment == subsetToCheck:
                                if subsetToCheck[0] in [p.pitchClass for p in segment[0].pitches]:
                                    startseg = segment[0:len(segment)-1]
                                    if subsetToCheck[-1] not in ContiguousSegmentOfNotes(startseg, None, None).readPitchClassesFromBottom():
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = currentSearchSegmentCopy
                                        segs.append(contiguousseg)
                                            
                else:
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    segment = contiguousseg.segment
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            if subsetToCheck == currentSearchSegment:
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = currentSearchSegmentCopy
                                segs.append(contiguousseg)
        
    return segs

def findTransposedSegments(inputStream, searchList, reps='skipConsecutive', includeChords=True):    
    '''
    Finds all instances of given contiguous segments of pitch classes, with transpositions, 
    within a :class:`~music21.stream.Stream`.
    
    The inputStream is a :class:`~music21.stream.Stream`; as 
    in :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`, 
    the inputStream can contain at most one :class:`~music21.stream.Score` and
    its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes. 
    The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings 
    are the same as those in
    :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`    
    
    Returns a list of :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` objects 
    for which some transposition of the
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment` matches at 
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
    >>> newpart = part.makeMeasures()
    >>> newpart.makeTies()
    >>> #_DOCS_SHOW newpart.show()
    
    .. image:: images/serial-findTransposedSegments.png
        :width: 500
        
    First, note that it is impossible, using the 'ignoreAll' setting, 
    to find segments, transposed or not,
    with repeated pitch classes.
    
    >>> alpha.search.serial.findTransposedSegments(newpart, [[0, 0]], 'ignoreAll')
    []
    
    A somewhat more interesting example is below.
    
    >>> halfStepList = alpha.search.serial.findTransposedSegments(
    ...                           newpart, [[0, 1]], 'rowsOnly', includeChords=False)
    >>> L = [step.segment for step in halfStepList]
    >>> print(L)
    [[<music21.note.Note E>, <music21.note.Note F>], 
     [<music21.note.Note B>, <music21.note.Note C>]]
    >>> [step.startMeasureNumber for step in halfStepList]
    [1, 5]
    
    In addition to calling the 
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.startMeasureNumber` 
    property
    to return the measure numbers on which the half steps start, one may also call the
    :attr:`~music21.base.Music21Object.measureNumber` property of the 
    first :class:`~music21.note.Note` of each segment.
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(newpart, 2) #s has two parts, each of which is a copy of newpart.
    >>> wholeStepList = alpha.search.serial.findTransposedSegments(s, [[12, 2]], 
    ...    includeChords=False)
    >>> [(step.segment, step.startMeasureNumber, step.partNumber) for step in wholeStepList]
    [([<music21.note.Note G>, <music21.note.Note A>], 3, 0), 
    ([<music21.note.Note A>, <music21.note.Note B>], 3, 0), 
    ([<music21.note.Note G>, <music21.note.Note A>], 3, 1), 
    ([<music21.note.Note A>, <music21.note.Note B>], 3, 1)]
    
    Including chords works similarly as in :class:`~music21.alpha.search.serial.findSegments`.
    
    >>> [seg.segment for seg in alpha.search.serial.findTransposedSegments(newpart, [[4, 6, 'A']])]
    [[<music21.note.Note F>, <music21.chord.Chord G4 B4>]]
    
    OMIT_FROM_DOCS
    
    >>> testSameSeg = alpha.search.serial.findTransposedSegments(newpart, 
    ...                                             [[12, 13], [0, 1]], 
    ...                                             'skipConsecutive', 
    ...                                             includeChords=False)
    >>> len(testSameSeg)
    2
    >>> testSameSeg[0].matchedSegment
    [12, 13]
    >>> alpha.search.serial.findTransposedSegments(newpart, [[9, 'A', 'B']], 
    ...    'rowsOnly', includeChords=False)
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
    >>> [seg.segment for seg in alpha.search.serial.findTransposedSegments(s, [[3, 4, 6]], 
    ...    'ignoreAll')]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]
    >>> [seg.segment for seg in alpha.search.serial.findTransposedSegments(s, [[4, 8, 6]], 
    ...    'ignoreAll')]
    [[<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]]
    
    '''
    # pylint: disable=line-too-long,duplicate-code
    
    numsegs = len(searchList)
    segs = []
    doneAlready = []
    contigdict = {}

    for k in range(numsegs):
        currentSearchSegment = searchList[k]
        row = pcToToneRow([n for n in currentSearchSegment])
        intervals = row.getIntervalsAsString()
        if intervals not in doneAlready:
            doneAlready.append(intervals)
            length = len(currentSearchSegment)
            if length in contigdict:
                contig = contigdict[length]
            else:
                searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                contig = searcher.byLength(length)
                contigdict[length] = contig
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(len(pitchList) - len(currentSearchSegment) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+length]
                            subsetToCheckAsRow = pcToToneRow(subsetToCheck)
                            if row.getIntervalsAsString() == subsetToCheckAsRow.getIntervalsAsString():
                                if subsetToCheck[0] in [p.pitchClass for p in segment[0].pitches]:
                                    startseg = segment[0:len(segment)-1]
                                    if subsetToCheck[-1] not in ContiguousSegmentOfNotes(startseg, None, None).readPitchClassesFromBottom():
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = currentSearchSegment
                                        segs.append(contiguousseg)
                else:
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    segment = contiguousseg.segment
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            if intervals == pcToToneRow(pitchList).getIntervalsAsString():
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = currentSearchSegment
                                segs.append(contiguousseg)
    return segs

def findTransformedSegments(inputStream, searchList, 
                            reps='skipConsecutive', includeChords=True):
    '''
    Finds all instances of given contiguous segments of pitch classes, 
    with serial transformations,
    within a :class:`~music21.stream.Stream`.
    
    The inputStream is :class:`~music21.stream.Stream`; as 
    in :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`,
    the inputStream can 
    contain at most one :class:`~music21.stream.Score` 
    and its notes must be contained in measures. The searchList is a list of contiguous segments to
    be searched for, each segment being given as a list of pitch classes. 
    The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings 
    are the same as those in
    :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`. 
    
    The convention for serial 
    transformations must be specified to either
    'zero' or 'original', as described in 
    :meth:`~music21.alpha.search.serial.zeroCenteredTransformation` and
    :func:`~music21.alpha.search.serial.originalCenteredTransformation` - the default setting 
    is 'original', as to relate found segments
    directly to the given segments, without first transposing the given segment to 
    begin on the pitch class 0.
    
    Returns a list of :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` objects 
    for which some transformation of the
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment` matches at 
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
    
    >>> row = [2, 5, 4]    
    >>> rowInstances = alpha.search.serial.findTransformedSegments(part, [row], 
    ...    'rowsOnly', includeChords=False)
    >>> len(rowInstances)
    2
    >>> firstInstance = rowInstances[0]
    >>> firstInstance
    <music21.alpha.search.serial.ContiguousSegmentOfNotes ['C#4', 'E4', 'D#4']>
    
    >>> firstInstance.activeSegment, firstInstance.startMeasureNumber
    ([1, 4, 3], 1)
    >>> firstInstance.originalCenteredTransformationsFromMatched
    [('T', 11)]
    
    We have thus found that the first instance of the row [2, 5, 4] within our 
    stream appears as a transposition
    down a semitone, beginning in measure 1. We can do a similar analysis on 
    the other instance of the row.
    
    >>> secondInstance = rowInstances[1]
    >>> secondInstance.activeSegment, secondInstance.startMeasureNumber
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
    
    >>> found643 = alpha.search.serial.findTransformedSegments(s, [[6, 4, 3]], 'ignoreAll')
    >>> [seg.segment for seg in found643]
    [[<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>]]
    
    >>> found = alpha.search.serial.findTransformedSegments(s, [[6, 8, 4]], 'ignoreAll')
    >>> for seg in found:
    ...    print(seg.segment)
    [<music21.note.Note G>, <music21.chord.Chord B4 G5 A5>]
    [<music21.chord.Chord B4 G5 A5>]
    
    >>> [seg.activeSegment for seg in found]
    [[7, 11, 9], 
     [11, 7, 9]]
    >>> [seg.originalCenteredTransformationsFromMatched for seg in found]
    [[('R', 3)], 
     [('RI', 3)]]
    
    Pitch classes are extracted from segments in order of appearance, with 
    pitches in chords being read from bottom to top.
    However, only the first instance of each pitch class is considered, as seen in the
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment` calls. 
    As long as the first and last pitch classes in the
    active segment first appear in the first and last elements of 
    the found segment, respectively, the segment will be matched to the
    segment being searched for. To make this more clear, consider the 
    following example in the same stream s:
    
    >>> found = alpha.search.serial.findTransformedSegments(s, [[4, 0, 4]], 'includeAll')
    >>> [(seg.segment, seg.activeSegment) for seg in found]
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
    >>> testNegativePitchClass = alpha.search.serial.findTransformedSegments(s, [[2, -7, 4]], 
    ...                                    includeChords=False)
    >>> len(testNegativePitchClass)
    4
    >>> testNegativePitchClass[0].matchedSegment
    [2, -7, 4]
    '''
    numsegs = len(searchList)
    segs = []
    doneAlready = []
    contigdict = {}
    
    for k in range(numsegs):
        currentSearchSegment = searchList[k]
        row = pcToToneRow(currentSearchSegment)
        used = False
        for usedrow in doneAlready:
            if used == False:
                if row.findZeroCenteredTransformations(pcToToneRow(usedrow)) != []:
                    used = True
        if used == False:
            doneAlready.append(currentSearchSegment)
            length = len(currentSearchSegment)
            if length in contigdict:
                contig = contigdict[length]
            else:
                searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                contig = searcher.byLength(length)
                contigdict[length] = contig    
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(len(pitchList) - len(currentSearchSegment) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+length]
                            subsetToCheckAsRow = pcToToneRow(subsetToCheck)
                            transformations = row.findZeroCenteredTransformations(
                                                                            subsetToCheckAsRow)
                            if transformations != []:
                                if subsetToCheck[0] in [p.pitchClass for p in segment[0].pitches]:
                                    startseg = segment[0:len(segment)-1]
                                    if subsetToCheck[-1] not in ContiguousSegmentOfNotes(
                                                startseg, None, None).readPitchClassesFromBottom():
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = currentSearchSegment
                                        segs.append(contiguousseg)
                else:
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            contiguoussegrow = pcToToneRow(subsetToCheck)
                            transformations = row.findZeroCenteredTransformations(contiguoussegrow)
                            if transformations != []:
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = currentSearchSegment
                                segs.append(contiguousseg)
    return segs

def findMultisets(inputStream, searchList, reps='skipConsecutive', includeChords=True):
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
    in :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`,
    the inputStream can contain at most one :class:`~music21.stream.Score`
    its notes must be contained in measures. However, the inputStream may have
    multiple parts. The searchList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. 
    Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; 
    the possible settings are the same as those in
    :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`    
    
    Returns a list of :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` 
    objects for the
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment`, 
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
    >>> part.append(n1)
    >>> part.append(n2)
    >>> part.append(n3)
    >>> part.append(n4)
    >>> part.makeMeasures(inPlace = True)
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
        {4.0} <music21.bar.Barline style=final>
            
    >>> #_DOCS_SHOW part.show()
    
    .. image:: images/serial-findMultisets.png
        :width: 150
    
    
    Find all instances of the multiset [5,4,4] in the part
    
    >>> EEF = alpha.search.serial.findMultisets(part, [[5, 4, 4]], 'includeAll', 
    ...    includeChords=False)
    >>> [(seg.activeSegment, seg.startMeasureNumber) for seg in EEF]
    [([4, 4, 5], 1), ([4, 5, 4], 2)]
    >>> EF = alpha.search.serial.findMultisets(part, [[4, 5]], 'ignoreAll')
    >>> [seg.segment for seg in EF]
    [[<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>], 
    [<music21.note.Note E>, <music21.note.Note F>], 
    [<music21.note.Note E>, <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 
    [<music21.note.Note E>, <music21.note.Note F>, <music21.note.Note E>], 
    [<music21.note.Note F>, <music21.note.Note E>]]    
    
    Consider the following examples, with chords.
    
    >>> sc0 = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('d4'))
    >>> part0.append(note.Note('e4'))
    >>> part0.append(chord.Chord(['f4', 'e5']))
    >>> part0 = part0.makeMeasures()
    >>> sc0.insert(0, part0)
    >>> [seg.segment for seg in alpha.search.serial.findMultisets(sc0, [[0, 2, 4]], 'ignoreAll')]
    [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]]
    
    Also:
    
    >>> sc1 = stream.Score()
    >>> part1 = stream.Part()
    >>> part1.append(note.Note('c4'))
    >>> part1.append(note.Note('d4'))
    >>> part1.append(chord.Chord(['e4', 'f4']))
    >>> part1 = part1.makeMeasures()
    >>> sc1.insert(0, part1)
    >>> searcher = alpha.search.serial.ContiguousSegmentSearcher(sc1)
    >>> segmentList = searcher.byLength(3)
    >>> [seg.getDistinctPitchClasses() for seg in segmentList]
    [[0, 2, 4, 5], [2, 4, 5]]
    >>> alpha.search.serial.findMultisets(sc1, [[0, 2, 5]])
    []
    
    OMIT_FROM_DOCS
    
    >>> s = stream.Stream()
    >>> s.repeatAppend(part, 2)
    >>> alpha.search.serial.findMultisets(part, [[5, 4, 4]], 'rowsOnly')
    []
    >>> testMultiple = alpha.search.serial.findMultisets(s, [[-7, 16, 4], [5, 4, 4]], 
    ...                                    'includeAll', includeChords=False)
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
    >>> [seg.segment for seg in alpha.search.serial.findMultisets(sc, [[0, 2, 4]], 'ignoreAll')]
    [[<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]]
    '''
    # pylint: disable=line-too-long,duplicate-code
    numMultisets = len(searchList)
    multisets = []
    doneAlready = []
    contigdict = {}
    
    for k in range(numMultisets):
        multiset = searchList[k]
        length = len(multiset)
        used = False
        for usedset in doneAlready:
            if used == False:
                if _checkMultisetEquivalence(usedset, multiset) == True:
                    used = True
        if used == False:
            doneAlready.append(multiset)
            length = len(multiset)
            if length in contigdict:
                contig = contigdict[length]
            else:
                searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                contig = searcher.byLength(length)
                contigdict[length] = contig
            for contiguousseg in contig:
                if reps == 'ignoreAll':
                    segment = contiguousseg.segment
                    pitchList = contiguousseg.getDistinctPitchClasses()
                    matched = False
                    for i in range(len(pitchList) - len(multiset) + 1):
                        if matched == False:
                            subsetToCheck = pitchList[i:i+len(multiset)]
                            if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                if len(segment) == 1:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = multiset
                                    multisets.append(contiguousseg)
                                else:
                                    multiset = pcToToneRow(multiset).pitchClasses()
                                    if segment[0].pitches[-1].pitchClass in multiset:
                                        if segment[-1].pitches[0].pitchClass in multiset:
                                            middleSegment = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                            # environLocal.warn("" + str(middleSegment.startMeasureNumber))
                                            listOfPitchClasses = middleSegment.readPitchClassesFromBottom()
                                            doneAddingFirst = False
                                            firstChordPitches = segment[0].pitches
                                            for j in range(1, len(firstChordPitches) + 1):
                                                if doneAddingFirst == False:
                                                    if firstChordPitches[-j].pitchClass in multiset:
                                                        listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                    else:
                                                        doneAddingFirst = True
                                            doneAddingLast = False
                                            lastChordPitches = segment[-1].pitches
                                            for k in range(len(lastChordPitches)):
                                                if doneAddingLast == False:
                                                    if lastChordPitches[k].pitchClass in multiset:
                                                        listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                    else:
                                                        doneAddingLast = True
                                            if set(listOfPitchClasses) == set(multiset):
                                                matched = True
                                                contiguousseg.activeSegment = subsetToCheck
                                                contiguousseg.matchedSegment = multiset
                                                multisets.append(contiguousseg)
                else:
                    pitchList = contiguousseg.readPitchClassesFromBottom()
                    segment = contiguousseg.segment
                    matched = False
                    lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                    upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                    for j in range(lowerBound, upperBound + 1):
                        if matched == False:
                            subsetToCheck = pitchList[j:j+length]
                            if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                matched = True
                                contiguousseg.activeSegment = subsetToCheck
                                contiguousseg.matchedSegment = multiset
                                multisets.append(contiguousseg)
    return multisets

def findTransposedMultisets(inputStream, searchList, reps='skipConsecutive', includeChords=True):
    '''
    Finds all instances of given multisets of pitch classes, with transpositions, 
    within a :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, as described in 
    :meth:`~music21.alpha.search.serial.findMultisets`.

    The inputStream is :class:`~music21.stream.Stream`; as 
    in :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`,
    the inputStream can contain at most one :class:`~music21.stream.Score` 
    and its notes must be contained in measures. 
    The searchList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. 
    Note that the order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the 
    possible settings are the same as those in
    :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`.
    
    Returns a list of :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` objects 
    for some transposition of the 
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment`, 
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
    
    >>> instanceList = alpha.search.serial.findTransposedMultisets(part, [[-9, -10, -11]], 
    ...    includeChords=False)
    >>> for instance in instanceList:
    ...    (instance.activeSegment, instance.startMeasureNumber, instance.matchedSegment)
    ([2, 4, 3], 3, [-9, -10, -11])
    ([3, 4, 2], 5, [-9, -10, -11])
    ([0, 1, 2], 1, [-9, -10, -11])
    
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
    >>> instanceList2 = alpha.search.serial.findTransposedMultisets(part2, [[-9, -10, -11]], 
    ...    'ignoreAll')
    >>> [seg.segment for seg in instanceList2]
    [[<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>], 
     [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, 
      <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>], 
     [<music21.chord.Chord D4 D5>, <music21.chord.Chord E4 E5>, 
      <music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>], 
     [<music21.chord.Chord E4 E5>, <music21.chord.Chord E-4 E-5>, 
      <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>], 
     [<music21.chord.Chord E-4 E-5>, <music21.chord.Chord E4 E5>, <music21.chord.Chord D4 D5>], 
     [<music21.chord.Chord C4 C5>, <music21.chord.Chord C#4 C#5>, <music21.chord.Chord D4 D5>]]
    >>> [seg.matchedSegment for seg in instanceList2]
    [[-9, -10, -11], [-9, -10, -11], [-9, -10, -11], 
     [-9, -10, -11], [-9, -10, -11], [-9, -10, -11]]
    '''
    # pylint: disable=line-too-long,duplicate-code
    numMultisets = len(searchList)
    multisets = []
    doneAlready = []
    contigdict = {}
    
    for k in range(numMultisets):
        baseMultiset = searchList[k]
        baseMultisetPitchClasses = pcToToneRow(baseMultiset).pitchClasses()
        for l in range(12):
            multiset = [(l + x) % 12 for x in baseMultisetPitchClasses]
            length = len(multiset)
            used = False
            for usedset in doneAlready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                doneAlready.append(multiset)
                length = len(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                    contig = searcher.byLength(length)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if reps == 'ignoreAll':
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.getDistinctPitchClasses()
                        matched = False
                        for i in range(len(pitchList) - len(multiset) + 1):
                            if matched == False:
                                subsetToCheck = pitchList[i:i+len(multiset)]
                                if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                    if len(segment) == 1:
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = baseMultiset
                                        multisets.append(contiguousseg)
                                    else:
                                        multiset = pcToToneRow(multiset).pitchClasses()
                                        if segment[0].pitches[-1].pitchClass in multiset:
                                            if segment[-1].pitches[0].pitchClass in multiset:
                                                middleSegment = ContiguousSegmentOfNotes(
                                                    list(segment[1:len(segment)-1]), None, None)
                                                listOfPitchClasses = middleSegment.readPitchClassesFromBottom()
                                                doneAddingFirst = False
                                                firstChordPitches = segment[0].pitches
                                                for j in range(1, len(firstChordPitches) + 1):
                                                    if doneAddingFirst == False:
                                                        if firstChordPitches[-j].pitchClass in multiset:
                                                            listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                        else:
                                                            doneAddingFirst = True
                                                doneAddingLast = False
                                                lastChordPitches = segment[-1].pitches
                                                for k in range(len(lastChordPitches)):
                                                    if doneAddingLast == False:
                                                        if lastChordPitches[k].pitchClass in multiset:
                                                            listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                        else:
                                                            doneAddingLast = True
                                                if set(listOfPitchClasses) == set(multiset):
                                                    matched = True
                                                    contiguousseg.activeSegment = subsetToCheck
                                                    contiguousseg.matchedSegment = baseMultiset
                                                    multisets.append(contiguousseg)
                    else:
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.readPitchClassesFromBottom()
                        matched = False
                        lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                        upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                        for j in range(lowerBound, upperBound + 1):
                            if matched == False:
                                subsetToCheck = pitchList[j:j+length]
                                if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = baseMultiset
                                    multisets.append(contiguousseg)
                                    
    return multisets

def findTransposedAndInvertedMultisets(inputStream, searchList, 
                                       reps='skipConsecutive', includeChords=True):
    
    '''
    Finds all instances of given multisets of pitch classes, with 
    transpositions and inversions, within a :class:`~music21.stream.Stream`. 
    A multiset is a generalization of a set, as described in 
    :meth:`~music21.alpha.search.serial.findMultisets`.

    The inputStream is :class:`~music21.stream.Stream`; as 
    in :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`,
    it can contain at most one :class:`~music21.stream.Score`, and
    its notes must be contained in measures. The multisetList is a list of multisets to
    be searched for, each multiset being given as a list of pitch classes. Note that the 
    order of pitch classes given in a multiset
    does not matter. The reps and includeChords settings specify how
    repeated pitches and chords, respectively, are handled; the possible settings 
    are the same as those in
    :class:`~music21.alpha.search.serial.ContiguousSegmentSearcher`    
    
    Returns a list of :class:`~music21.alpha.search.serial.ContiguousSegmentOfNotes` 
    objects for some transposition or inversion of the 
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.activeSegment`, 
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
        
    >>> majTriads = alpha.search.serial.findTransposedAndInvertedMultisets(s, [[0, 4, 7], 
    ...                                                    [0, 3, 7]], 
    ...                                                    'ignoreAll', includeChords=False)
    >>> [(maj.segment, maj.startOffset) for maj in majTriads]
    [([<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 2.0), 
    ([<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>], 0.0)]
    >>> [maj.matchedSegment for maj in majTriads]
    [[0, 4, 7], [0, 4, 7]]
        
    Note that when we search for both [0, 4, 7] and [0, 3, 7], which are related to each other
    by the composition of an inversion and a transposition, each 
    found segment is only matched to one
    of the multisets in the searchList; thus each found segment appears 
    still appears at most once in the returned list
    of contiguous segments. Accordingly, calling 
    :attr:`~music21.alpha.search.serial.ContiguousSegmentOfNotes.matchedSegment`
    returns only one element of the searchList for each found segment.
    
    OMIT_FROM_DOCS
    
    >>> majAndMinTriads = alpha.search.serial.findTransposedAndInvertedMultisets(s, [[0, 4, 7]], 
    ...                        'rowsOnly', includeChords=True)
    >>> [maj.segment for maj in majAndMinTriads]
    [[<music21.note.Note G>, <music21.note.Note E>, <music21.note.Note C>], 
    [<music21.note.Note C>, <music21.note.Note E->, <music21.note.Note G>]]
    
    '''
    # pylint: disable=line-too-long,duplicate-code
    
    numMultisets = len(searchList)
    multisets = []
    doneAlready = []
    contigdict = {}
    
    for k in range(numMultisets):
        baseMultiset = searchList[k]
        baseMultisetPitchClasses = pcToToneRow(baseMultiset).pitchClasses()
        baseMultisetInversion = pcToToneRow(baseMultiset).zeroCenteredTransformation('I', 0
                                                                        ).pitchClasses()
        for l in range(12):
            multiset = [(l + x) % 12 for x in baseMultisetPitchClasses]
            length = len(multiset)
            used = False
            for usedset in doneAlready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                doneAlready.append(multiset)
                length = len(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                    contig = searcher.byLength(length)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if reps == 'ignoreAll':
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.getDistinctPitchClasses()
                        matched = False
                        for i in range(len(pitchList) - len(multiset) + 1):
                            if matched == False:
                                subsetToCheck = pitchList[i:i+len(multiset)]
                                if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                    if len(segment) == 1:
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = baseMultiset
                                        multisets.append(contiguousseg)
                                    else:
                                        multiset = pcToToneRow(multiset).pitchClasses()
                                        if segment[0].pitches[-1].pitchClass in multiset:
                                            if segment[-1].pitches[0].pitchClass in multiset:
                                                middleSegment = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                                listOfPitchClasses = middleSegment.readPitchClassesFromBottom()
                                                doneAddingFirst = False
                                                firstChordPitches = segment[0].pitches
                                                for j in range(1, len(firstChordPitches) + 1):
                                                    if doneAddingFirst == False:
                                                        if firstChordPitches[-j].pitchClass in multiset:
                                                            listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                        else:
                                                            doneAddingFirst = True
                                                doneAddingLast = False
                                                lastChordPitches = segment[-1].pitches
                                                for k in range(len(lastChordPitches)):
                                                    if doneAddingLast == False:
                                                        if lastChordPitches[k].pitchClass in multiset:
                                                            listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                        else:
                                                            doneAddingLast = True
                                                if set(listOfPitchClasses) == set(multiset):
                                                    matched = True
                                                    contiguousseg.activeSegment = subsetToCheck
                                                    contiguousseg.matchedSegment = baseMultiset
                                                    multisets.append(contiguousseg)
                    else:
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.readPitchClassesFromBottom()
                        matched = False
                        lowerBound = max([0, len(pitchList) - length - len(segment[-1].pitches) + 1])
                        upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                        for j in range(lowerBound, upperBound + 1):
                            if matched == False:
                                subsetToCheck = pitchList[j:j+length]
                                if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = baseMultiset
                                    multisets.append(contiguousseg)
        for l in range(12):
            multiset = [(l + x) % 12 for x in baseMultisetInversion]
            length = len(multiset)
            used = False
            for usedset in doneAlready:
                if used == False:
                    if _checkMultisetEquivalence(usedset, multiset) == True:
                        used = True
            if used == False:
                doneAlready.append(multiset)
                length = len(multiset)
                if length in contigdict:
                    contig = contigdict[length]
                else:
                    searcher = ContiguousSegmentSearcher(inputStream, reps, includeChords)
                    contig = searcher.byLength(length)
                    contigdict[length] = contig
                for contiguousseg in contig:
                    if reps == 'ignoreAll':
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.getDistinctPitchClasses()
    #                    if len(set([p.pitchClass for p in segment[0].pitches]) and set(multiset)) != 0:
    #                        if len(set([p.pitchClass for p in segment[-1].pitches]) and set(multiset)) != 0:
                        matched = False
                        for i in range(len(pitchList) - len(multiset) + 1):
                            if matched == False:
                                subsetToCheck = pitchList[i:i+len(multiset)]
                                if _checkMultisetEquivalence(multiset, subsetToCheck) == True:
                                    if len(segment) == 1:
                                        matched = True
                                        contiguousseg.activeSegment = subsetToCheck
                                        contiguousseg.matchedSegment = baseMultiset
                                        multisets.append(contiguousseg)
                                    else:
                                        multiset = pcToToneRow(multiset).pitchClasses()
                                        if segment[0].pitches[-1].pitchClass in multiset:
                                            if segment[-1].pitches[0].pitchClass in multiset:
                                                middleSegment = ContiguousSegmentOfNotes(list(segment[1:len(segment)-1]), None, None)
                                                listOfPitchClasses = middleSegment.readPitchClassesFromBottom()
                                                doneAddingFirst = False
                                                firstChordPitches = segment[0].pitches
                                                for j in range(1, len(firstChordPitches) + 1):
                                                    if doneAddingFirst == False:
                                                        if firstChordPitches[-j].pitchClass in multiset:
                                                            listOfPitchClasses.append(firstChordPitches[-j].pitchClass)
                                                        else:
                                                            doneAddingFirst = True
                                                doneAddingLast = False
                                                lastChordPitches = segment[-1].pitches
                                                for k in range(len(lastChordPitches)):
                                                    if doneAddingLast == False:
                                                        if lastChordPitches[k].pitchClass in multiset:
                                                            listOfPitchClasses.append(lastChordPitches[k].pitchClass)
                                                        else:
                                                            doneAddingLast = True
                                                if set(listOfPitchClasses) == set(multiset):
                                                    matched = True
                                                    contiguousseg.activeSegment = subsetToCheck
                                                    contiguousseg.matchedSegment = baseMultiset
                                                    multisets.append(contiguousseg)
                    else:
                        segment = contiguousseg.segment
                        pitchList = contiguousseg.readPitchClassesFromBottom()
                        matched = False
                        lowerBound = max([0, 
                                          len(pitchList) - length - len(segment[-1].pitches) + 1])
                        upperBound = min([len(segment[0].pitches) - 1, len(pitchList) - length])
                        for j in range(lowerBound, upperBound + 1):
                            if matched == False:
                                subsetToCheck = pitchList[j:j+length]
                                if _checkMultisetEquivalence(subsetToCheck, multiset) == True:
                                    matched = True
                                    contiguousseg.activeSegment = subsetToCheck
                                    contiguousseg.matchedSegment = baseMultiset
                                    multisets.append(contiguousseg)
    return multisets


     

def _labelGeneral(segmentsToLabel, inputStream, segmentDict, reps, includeChords):
    '''
    Helper function for all but one of the labelling functions below. 
    Private because this should only be called
    in conjunction with one of the find(type of set of pitch classes) functions.
    '''    
    if len(inputStream.getElementsByClass(stream.Score)) == 0:
        bigContainer = inputStream
    else:
        bigContainer = inputStream.getElementsByClass(stream.Score)
    if len(bigContainer.getElementsByClass(stream.Part)) == 0:
        hasParts = False
    else:
        parts = bigContainer.getElementsByClass(stream.Part)
        hasParts = True
        
    segmentList = [segmentDict[label] for label in segmentDict]
    labelList = [label for label in segmentDict]
    numSearchSegments = len(segmentList)
    numSegmentsToLabel = len(segmentsToLabel)
    reorderedSegmentsToLabel = sorted(segmentsToLabel, key=attrgetter(
                                                'partNumber', 'startMeasureNumber', 'startOffset'))
    
    for k in range (0, numSegmentsToLabel):
        foundSegment = reorderedSegmentsToLabel[k]          
        linelabel = spanner.Line(foundSegment.segment[0], foundSegment.segment[-1])
        if hasParts == True:
            parts[foundSegment.partNumber].insert(0, linelabel)
        else:
            bigContainer.insert(0, linelabel)
        
        foundLabel = False
        rowToMatch = foundSegment.matchedSegment
        for l in range(numSearchSegments):
            if foundLabel == False:
                if segmentList[l] == rowToMatch:
                    foundLabel = True
                    label = labelList[l]
                    firstnote = foundSegment.segment[0]
                    if label not in [lyr.text for lyr in firstnote.lyrics]:
                        firstnote.addLyric(label)
                    
    return inputStream
    




def labelSegments(inputStream, segmentDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of segments of pitch classes in a
    :class:`~music21.stream.Stream`.
    
    The segmentDict is a dictionary whose keys are names of 
    the segments to be searched for, and whose values are the segments of pitch classes. 
    The values will be
    turned in to a segmentList, as in :func:`~music21.alpha.search.serial.findSegments`.
    All other settings are as in :func:`~music21.alpha.search.serial.findSegments` as well.
    
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
    >>> newpart = part.makeMeasures()
    >>> newpart.makeTies()
    
    We can then label the segment of pitch classes [7, 9, 11], which corresponds to a G, 
    followed by an A,
    followed by a B. Let us call this segment "GAB".
    
    >>> labelGAB = alpha.search.serial.labelSegments(newpart, {'GAB':[7, 9, 11]}, 
    ...    includeChords=False)
    >>> #_DOCS_SHOW labelGAB.show()
    
    .. image:: images/serial-labelSegments.png
       :width: 500
    
    >>> len(labelGAB.getElementsByClass(spanner.Line))
    1
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = findSegments(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, segmentDict, reps, includeChords)
        


def labelTransposedSegments(inputStream, segmentDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of segments of pitch classes,
    with transpositions, in a :class:`~music21.stream.Stream`.
    
    The segmentDict is a dictionary whose keys are names of the segments to be
    searched for, and whose values are the segments of pitch classes. The
    values will be turned in to a segmentList, as in
    :func:`~music21.alpha.search.serial.findTransposedSegments`.  All other settings are as
    in :func:`~music21.alpha.search.serial.findTransposedSegments` as well.
    
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
    >>> newpart = part.makeMeasures()
    >>> newpart.makeTies()

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
    >>> newbass = bass.makeMeasures()
    >>> sc = stream.Score()
    >>> import copy
    >>> sc.insert(0, copy.deepcopy(newpart))
    >>> sc.insert(0, copy.deepcopy(newbass))
    >>> labeledsc = alpha.search.serial.labelTransposedSegments(sc, {'half':[0, 1]}, 'rowsOnly')
    >>> #_DOCS_SHOW labeledsc.show()

    .. image:: images/serial-labelTransposedSegments.png
       :width: 500
        
    OMIT_FROM_DOCS
    
    >>> len(labeledsc.parts[0].getElementsByClass(spanner.Line))
    2    
    '''
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [segmentDict[label] for label in segmentDict]
    segmentsToLabel = findTransposedSegments(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, segmentDict, reps, includeChords)



def labelTransformedSegments(inputStream, segmentDict, reps='skipConsecutive', 
                             includeChords=True, convention='original'):    
    '''
    Labels all instances of a given collection of segments of pitch classes,
    with transformations, in a :class:`~music21.stream.Stream`.
    
    The segmentDict is a dictionary whose keys are names of the segments to be 
    searched for, and whose values are the segments of pitch classes. The 
    values will be turned in to a segmentList, as in 
    :func:`~music21.alpha.search.serial.findTransposedSegments`. The last argument specifies
    the convention ('zero' or 'original') used for naming serial 
    transformations, as explained in 
    :meth:`~music21.alpha.search.serial.ToneRow.zeroCenteredTransformation` and
    :meth:`~music21.alpha.search.serial.ToneRow.originalCenteredTransformation`.

    All other settings are as in :func:`~music21.alpha.search.serial.findTransposedSegments`
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
    >>> labeledPart = alpha.search.serial.labelTransformedSegments(part, {'row':[2, 5, 4]})
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
    
    #this doesn't call _labelGeneral because each segment is also labeled with the transformations.
    if len(streamCopy.getElementsByClass(stream.Score)) == 0:
        bigContainer = streamCopy
    else:
        bigContainer = streamCopy.getElementsByClass(stream.Score)
    if len(bigContainer.getElementsByClass(stream.Part)) == 0:
        hasParts = False
    else:
        parts = bigContainer.getElementsByClass(stream.Part)
        hasParts = True
        
    segmentList = [segmentDict[label] for label in segmentDict]
    labelList = [label for label in segmentDict]
    numSearchSegments = len(segmentList)
    segmentsToLabel = findTransformedSegments(streamCopy, segmentList, reps, includeChords)
    numSegmentsToLabel = len(segmentsToLabel)
    reorderedSegmentsToLabel = sorted(segmentsToLabel, key = attrgetter(
                                            'partNumber', 'startMeasureNumber', 'startOffset'))
    
    for k in range (0, numSegmentsToLabel):
        foundSegment = reorderedSegmentsToLabel[k]          
        linelabel = spanner.Line(foundSegment.segment[0], foundSegment.segment[-1])
        if hasParts == True:
            parts[foundSegment.partNumber].insert(0, linelabel)
        else:
            bigContainer.insert(0, linelabel)
        
        foundLabel = False
        rowToMatch = foundSegment.matchedSegment
        for l in range(numSearchSegments):
            if foundLabel == False:
                if segmentList[l] == rowToMatch:
                    foundLabel = True
                    label = labelList[l]
                    firstnote = foundSegment.segment[0]
                    if convention == 'original':
                        transformations = foundSegment.originalCenteredTransformationsFromMatched
                    elif convention == 'zero':
                        transformations = foundSegment.zeroCenteredTransformationsFromMatched
                    else:
                        raise SerialException("Invalid convention - choose 'zero' or 'original'.")
                    for trans in transformations:
                        label = label + ' ,' + str(trans[0]) + str(trans[1])
                    if label not in [lyr.text for lyr in firstnote.lyrics]:
                        firstnote.addLyric(label)
                    
    return streamCopy

            


def labelMultisets(inputStream, multisetDict, reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of multisets of pitch classes in a
    :class:`~music21.stream.Stream`. A multiset
    is a generalization of a set, as described in 
    :meth:`~music21.alpha.search.serial.findMultisets`.
    
    The multisetDict is a dictionary whose keys are names of 
    the multisets to be searched for, and whose 
    values are the segments of pitch classes. The values will be
    turned in to a segmentList, as in :func:`~music21.alpha.search.serial.findMultisets`.
    All other settings are as in :func:`~music21.alpha.search.serial.findMultisets` as well.
    
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
    >>> labeledPart = alpha.search.serial.labelMultisets(part, {'EEF':[4, 5, 4]}, 
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
    segmentsToLabel = findMultisets(streamCopy, segmentList, reps, includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)    
    


def labelTransposedMultisets(inputStream, multisetDict, 
                             reps='skipConsecutive', includeChords=True):
    '''
    Labels all instances of a given collection of multisets, with 
    transpositions, of pitch classes in a :class:`~music21.stream.Stream`.

    A multiset is a generalization of a set, as described in 
    :meth:`~music21.alpha.search.serial.findMultisets`.
    
    The multisetDict is a dictionary whose keys are names of the multisets to 
    be searched for, and whose values are the segments of pitch classes. The 
    values will be turned in to a segmentList, as in 
    :func:`~music21.alpha.search.serial.findMultisets`.

    All other settings are as in 
    :func:`~music21.alpha.search.serial.findTransposedMultisets` as well.
    
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
    >>> bachLabeled = alpha.search.serial.labelTransposedMultisets(bach, 
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
    segmentsToLabel = findTransposedMultisets(streamCopy, segmentList, reps, includeChords)
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
    :meth:`~music21.alpha.search.serial.findMultisets`.
    
    The multisetDict is a dictionary whose keys are names of the multisets to
    be searched for, and whose values are the segments of pitch classes. The 
    values will be turned in to a segmentList, as in 
    :func:`~music21.alpha.search.serial.findMultisets`.

    All other settings are as in 
    :func:`~music21.alpha.search.serial.findTransposedMultisets` as well.
    
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
    
    >>> l = alpha.search.serial.labelTransposedAndInvertedMultisets
    >>> #_DOCS_SHOW l(s, {'triad':[0, 4, 7]}, includeChords=False).show()
        
    .. image:: images/serial-labelTransposedAndInvertedMultisets.png
       :width: 500
    
    Note: the spanners above were moved manually so that they can be more 
    easily distinguished from one another.
    '''
    
    
    streamCopy = copy.deepcopy(inputStream)
    segmentList = [multisetDict[label] for label in multisetDict]
    segmentsToLabel = findTransposedAndInvertedMultisets(streamCopy, 
                                                         segmentList, 
                                                         reps, 
                                                         includeChords)
    return _labelGeneral(segmentsToLabel, streamCopy, multisetDict, reps, includeChords)   
      
#---------------------------------------------------------------------            
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCarlCode(self):
        part = stream.Part()
        n1 = note.Note('e4')
        n1.quarterLength = 4
        n2 = note.Note('e4')
        n2.quarterLength = 4
        n3 = note.Note('f4')
        n3.quarterLength = 4
        n4 = note.Note('e4')
        n4.quarterLength = 4
        part.append(n1)
        part.append(n2)
        part.append(n3)
        part.append(n4)
        part.makeMeasures(inPlace = True)
        EEF = findMultisets(part, [[5, 4, 4]], 'includeAll', includeChords=False)
        unused = [(seg.activeSegment, seg.startMeasureNumber) for seg in EEF]
        # TODO: Test this?

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [
              'ContiguousSegmentSearcher',
              'findSegments', 'labelSegments',
              'findTransposedSegments', 'labelTransposedSegments',
              'findTransformedSegments', 'labelTransformedSegments',
              'findMultisets', 'labelMultisets',
              'findTransposedMultisets', 'labelTransposedMultisets',
              'findTransposedAndInvertedMultisets', 'labelTransposedAndInvertedMultisets'
              ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
