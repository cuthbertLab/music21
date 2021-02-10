# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         search/base.py
# Purpose:      music21 classes for searching within files
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2013, 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
base classes for searching scores.

See User's Guide, Chapter 43: Searching in and Among Scores for details.
'''
import copy
import difflib
import math
import unittest
from collections import namedtuple

from more_itertools import windowed

from music21 import base as m21Base
from music21 import exceptions21
from music21 import duration
from music21.stream import filters

__all__ = [
    'Wildcard', 'WildcardDuration', 'SearchMatch', 'StreamSearcher',
    'streamSearchBase', 'rhythmicSearch', 'noteNameSearch', 'noteNameRhythmicSearch',
    'approximateNoteSearch', 'approximateNoteSearchNoRhythm', 'approximateNoteSearchOnlyRhythm',
    'approximateNoteSearchWeighted',
    'translateStreamToString',
    'translateDiatonicStreamToString', 'translateIntervalsAndSpeed',
    'translateStreamToStringNoRhythm', 'translateStreamToStringOnlyRhythm',
    'translateNoteToByte',
    'translateNoteWithDurationToBytes',
    'translateNoteTieToByte',
    'translateDurationToBytes',
    'mostCommonMeasureRhythms',
    'SearchException',
]


class WildcardDuration(duration.Duration):
    '''
    a wildcard duration (it might define a duration
    in itself, but the methods here will see that it
    is a wildcard of some sort)

    No difference from any other duration.
    '''
    pass


class Wildcard(m21Base.Music21Object):
    '''
    An object that may have some properties defined, but others not that
    matches a single object in a music21 stream.  Equivalent to the
    regular expression "."


    >>> wc1 = search.Wildcard()
    >>> wc1.pitch = pitch.Pitch('C')
    >>> st1 = stream.Stream()
    >>> st1.append(note.Note('D', type='half'))
    >>> st1.append(wc1)
    '''

    def __init__(self):
        super().__init__()
        self.duration = WildcardDuration()


class SearchMatch(namedtuple('SearchMatch', 'elStart els index iterator')):
    '''
    A lightweight object representing the match (if any) for a search.  Derived from namedtuple
    '''
    __slots__ = ()
    _DOC_ATTR = {'elStart': '''The first element that matches the list.''',
                 'els': '''A tuple of all the matching elements.''',
                 'index': '''The index in the iterator at which the first element can be found''',
                 'iterator': '''The iterator which produced these elements.''',
                 }

    def __repr__(self):
        return 'SearchMatch(elStart={0}, els=len({1}), index={2}, iterator=[...])'.format(
            repr(self.elStart), len(self.els), repr(self.index))


class StreamSearcher:
    '''
    An object that can search through streams for a set of elements
    or notes or something of that sort.

    Create a basic Stream first:

    >>> thisStream = converter.parse('tinynotation: 3/4 c4. d8 e4 g4. a8 f4. c4. d4')
    >>> thisStream.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.5} <music21.note.Note D>
        {2.0} <music21.note.Note E>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.note.Note G>
        {1.5} <music21.note.Note A>
        {2.0} <music21.note.Note F>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.5} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        {3.0} <music21.bar.Barline type=final>

    Let's create something to search for:

    >>> c = note.Note('C', quarterLength=1.5)
    >>> d = note.Note('D', quarterLength=0.5)
    >>> searchList = [c, d]


    Now create a StreamSearcher:

    >>> ss = search.StreamSearcher(thisStream, searchList)

    `searchList` could also be a Stream in itself.

    Let's configure it for recursive search and to filter so only notes are there:

    >>> ss.recurse = True
    >>> ss.filterNotes = True  # or `.filterNotesAndRests`

    Alternatively, we could have passed in a StreamIterator instead of `thisStream`.

    Now let's configure the algorithms:

    >>> ss.algorithms
    [<...StreamSearcher.wildcardAlgorithm...>]

    Wildcard search is a default algorithm that lets you use wildcards.
    I suggest you leave it in place and add to the algorithms list.  We can add the
    `rhythmAlgorithm` to it:

    >>> ss.algorithms.append(search.StreamSearcher.rhythmAlgorithm)
    >>> ss.algorithms
    [<...StreamSearcher.wildcardAlgorithm...>,
     <...StreamSearcher.rhythmAlgorithm...>]


    Now run it:

    >>> results = ss.run()
    >>> results
    [SearchMatch(elStart=<music21.note.Note C>, els=len(2), index=0, iterator=[...]),
     SearchMatch(elStart=<music21.note.Note G>, els=len(2), index=3, iterator=[...])]

    >>> results[0].elStart.measureNumber
    1
    >>> results[1].elStart.measureNumber
    2


    Wildcards can be useful:

    >>> searchStream2 = stream.Stream()
    >>> searchStream2.append(note.Note(quarterLength=0.5))
    >>> searchStream2.append(search.Wildcard())
    >>> searchStream2.append(note.Note(quarterLength=1.5))

    >>> ss.searchList = searchStream2
    >>> results = ss.run()
    >>> results
    [SearchMatch(elStart=<music21.note.Note D>, els=len(3), index=1, iterator=[...]),
     SearchMatch(elStart=<music21.note.Note A>, els=len(3), index=4, iterator=[...])]
    >>> results[0].els
    (<music21.note.Note D>, <music21.note.Note E>, <music21.note.Note G>)
    >>> [n.duration.quarterLength for n in results[0].els]
    [0.5, 1.0, 1.5]


    OMIT_FROM_DOCS

    >>> emptyS = stream.Stream()
    >>> ss.searchList = emptyS
    >>> ss.run()
    Traceback (most recent call last):
    music21.search.base.SearchException: the search Stream or list cannot be empty

    why doesn't this work?  thisStream[found].expressions.append(expressions.TextExpression('*'))
    '''

    def __init__(self, streamSearch=None, searchList=None):
        self.streamSearch = streamSearch
        self.searchList = searchList
        self.recurse = False
        self.filterNotes = False
        self.filterNotesAndRests = False

        self.algorithms = [StreamSearcher.wildcardAlgorithm]

        self.activeIterator = None

    def run(self):
        if 'StreamIterator' in self.streamSearch.classes:
            thisStreamIterator = self.streamSearch
        else:
            if self.recurse:
                thisStreamIterator = self.streamSearch.recurse()
            else:
                thisStreamIterator = self.streamSearch.iter

            if self.filterNotesAndRests:
                thisStreamIterator = thisStreamIterator.addFilter(
                    filters.ClassFilter('GeneralNote')
                )
            elif self.filterNotes:
                thisStreamIterator = thisStreamIterator.addFilter(
                    filters.ClassFilter(['Note', 'Chord'])
                )

        self.activeIterator = thisStreamIterator

        streamIteratorEls = list(thisStreamIterator)
        streamLength = len(streamIteratorEls)
        searchLength = len(self.searchList)

        if searchLength == 0:
            raise SearchException('the search Stream or list cannot be empty')

        foundEls = []
        if searchLength > streamLength:
            return foundEls

        for startPosition, streamEls in enumerate(windowed(streamIteratorEls, searchLength)):
            result = None
            for j in range(searchLength):
                streamEl = streamEls[j]
                searchEl = self.searchList[j]
                for thisAlgorithm in self.algorithms:
                    result = thisAlgorithm(self, streamEl, searchEl)
                    if result is not None:  # break on True or False
                        break
                if result is False:
                    break
                if result is True:
                    result = None

            if result is not False:
                sm = SearchMatch(streamEls[0], streamEls, startPosition, self.activeIterator)
                foundEls.append(sm)

        return foundEls

    def wildcardAlgorithm(self, streamEl, searchEl):
        '''
        An algorithm that supports Wildcards -- added by default to the search function.
        '''
        if Wildcard in searchEl.classSet:
            return True
        else:
            return None

    def rhythmAlgorithm(self, streamEl, searchEl):
        if 'WildcardDuration' in searchEl.duration.classes:
            return True
        if searchEl.duration.quarterLength != streamEl.duration.quarterLength:
            return False
        return None

    def noteNameAlgorithm(self, streamEl, searchEl):
        if not hasattr(searchEl, 'name'):
            return False
        if not hasattr(streamEl, 'name'):
            return False
        if searchEl.name != streamEl.name:
            return False
        return None


def streamSearchBase(thisStreamOrIterator, searchList, algorithm=None):
    '''
    A basic search function that is used by other search mechanisms,
    which takes in a stream or StreamIterator and a searchList or stream
    and an algorithm to run on each pair of elements to determine if they match.


    '''
    if algorithm is None:
        raise SearchException('algorithm must be a function not None')

    result = None
    if 'StreamIterator' in thisStreamOrIterator.classes:
        thisStreamIterator = thisStreamOrIterator
    else:
        thisStreamIterator = thisStreamOrIterator.recurse()

    streamIteratorEls = list(thisStreamIterator)
    streamLength = len(streamIteratorEls)
    searchLength = len(searchList)
    if searchLength == 0:
        raise SearchException('the search Stream or list cannot be empty')

    foundEls = []
    if searchLength > streamLength:
        return foundEls

    for startPosition, streamEls in enumerate(windowed(streamIteratorEls, searchLength)):
        for j in range(searchLength):
            streamEl = streamEls[j]
            searchEl = searchList[j]
            result = algorithm(streamEl, searchEl)
            if not result:
                break
        if result:
            foundEls.append(startPosition)
    return foundEls


def rhythmicSearch(thisStreamOrIterator, searchList):
    '''
    Takes two streams -- the first is the stream to be searched and the second
    is a stream of elements whose rhythms must match the first.  Returns a list
    of indices which begin a successful search.

    searches are made based on quarterLength.
    thus an dotted sixteenth-note and a quadruplet (4:3) eighth
    will match each other.

    Example 1: First we will set up a simple stream for searching:

    >>> thisStream = converter.parse('tinynotation: 3/4 c4. d8 e4 g4. a8 f4. c4. r4')
    >>> thisStream.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.5} <music21.note.Note D>
        {2.0} <music21.note.Note E>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.note.Note G>
        {1.5} <music21.note.Note A>
        {2.0} <music21.note.Note F>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.5} <music21.note.Note C>
        {2.0} <music21.note.Rest rest>
        {3.0} <music21.bar.Barline type=final>

    Now we will search for all dotted-quarter/eighth elements in the Stream:

    >>> thisStreamIter = thisStream.recurse().notes

    >>> searchStream1 = stream.Stream()
    >>> searchStream1.append(note.Note(quarterLength=1.5))
    >>> searchStream1.append(note.Note(quarterLength=0.5))

    >>> l = search.rhythmicSearch(thisStreamIter, searchStream1)
    >>> l
    [0, 3]
    >>> stream.Stream(thisStreamIter[3:5]).show('text')
    {0.0} <music21.note.Note G>
    {1.5} <music21.note.Note A>



    Slightly more advanced search: we will look for any instances of eighth,
    followed by a note (or other element) of any length, followed by a dotted quarter
    note.  Again, we will find two instances; this time we will tag them both with
    a TextExpression of "*" and then show the original stream:


    >>> searchStream2 = stream.Stream()
    >>> searchStream2.append(note.Note(quarterLength=0.5))
    >>> searchStream2.append(search.Wildcard())
    >>> searchStream2.append(note.Note(quarterLength=1.5))
    >>> l = search.rhythmicSearch(thisStreamIter, searchStream2)
    >>> l
    [1, 4]
    >>> for found in l:
    ...     thisStreamIter[found].lyric = '*'
    >>> #_DOCS_SHOW thisStream.show()


    .. image:: images/searchRhythmic1.*
        :width: 221

    Now we can test the search on a real dataset and show the types
    of preparation that are needed to make it most likely a success.
    We will look through the first movement of Corelli Trio Sonata op. 3 no. 1 (F major)
    looking to see how much more common the first search term (dotted-quarter, eighth)
    is than the second (eighth, anything, dotted-quarter).  In fact, my hypothesis
    was wrong, and the second term is actually more common than the first! (n.b. rests
    are being counted here as well as notes)


    >>> grave = corpus.parse('corelli/opus3no1/1grave')
    >>> term1results = []
    >>> term2results = []
    >>> for p in grave.parts:
    ...    pf = p.flat.stripTies().notesAndRests  # consider tied notes as one long note
    ...    temp1 = search.rhythmicSearch(pf, searchStream1)
    ...    temp2 = search.rhythmicSearch(pf, searchStream2)
    ...    for found in temp1:
    ...        term1results.append(found)
    ...    for found in temp2:
    ...        term2results.append(found)
    >>> term1results
    [0, 7, 13, 21, 42, 57, 64, 66, 0, 5, 7, 19, 21, 40, 46, 63, 0, 8, 31, 61, 69, 71, 73, 97]
    >>> term2results
    [5, 29, 95]
    >>> float(len(term1results)) / len(term2results)
    8.0
    '''
    def rhythmAlgorithm(streamEl, searchEl):
        if 'WildcardDuration' in searchEl.duration.classes:
            return True
        if searchEl.duration.quarterLength != streamEl.duration.quarterLength:
            return False
        return True

    return streamSearchBase(thisStreamOrIterator, searchList, algorithm=rhythmAlgorithm)


def noteNameSearch(thisStreamOrIterator, searchList):
    '''
    >>> thisStream = converter.parse('tinynotation: 3/4 c4 d8 e c d e f c D E c c4 d# e')
    >>> searchList = [note.Note('C'), note.Note('D'), note.Note('E')]
    >>> thisStreamIter = thisStream.recurse().notes

    >>> search.noteNameSearch(thisStreamIter, searchList)
    [0, 3, 7]
    >>> searchList2 = [note.Note('C'), search.Wildcard(), note.Note('E')]
    >>> search.noteNameSearch(thisStreamIter, searchList2)
    [0, 3, 7, 11]
    '''
    def noteNameAlgorithm(streamEl, searchEl):
        if 'Wildcard' in searchEl.classes:
            return True
        if not hasattr(searchEl, 'name'):
            return False
        if not hasattr(streamEl, 'name'):
            return False

        if searchEl.name != streamEl.name:
            return False
        return True

    return streamSearchBase(thisStreamOrIterator, searchList, algorithm=noteNameAlgorithm)


def noteNameRhythmicSearch(thisStreamOrIterator, searchList):
    # noinspection PyShadowingNames
    '''
    >>> thisStream = converter.parse('tinynotation: 3/4 c4 d8 e c d e f c D E c c4 d# e')
    >>> searchList = [note.Note('C'), note.Note('D'), note.Note('E')]
    >>> for n in searchList:
    ...     n.duration.type = 'eighth'
    >>> thisStreamIter = thisStream.recurse().notes

    >>> search.noteNameRhythmicSearch(thisStreamIter, searchList)
    [3, 7]

    >>> searchList[0].duration = search.WildcardDuration()
    >>> search.noteNameRhythmicSearch(thisStreamIter, searchList)
    [0, 3, 7]
    '''
    def noteNameRhythmAlgorithm(streamEl, searchEl):
        if 'Wildcard' in searchEl.classes:
            return True
        if not hasattr(searchEl, 'name'):
            return False
        if not hasattr(streamEl, 'name'):
            return False

        if searchEl.name != streamEl.name:
            return False

        if 'WildcardDuration' in searchEl.duration.classes:
            return True
        if searchEl.duration.quarterLength != streamEl.duration.quarterLength:
            return False

        return True

    return streamSearchBase(thisStreamOrIterator, searchList, algorithm=noteNameRhythmAlgorithm)


def approximateNoteSearch(thisStream, otherStreams):
    # noinspection PyShadowingNames
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)

    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 d#2 f A a' G b")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c8 d16 e32 FF32 a'8 b-8")
    >>> o3.id = 'o3'
    >>> l = search.approximateNoteSearch(s, [o1, o2, o3])
    >>> for i in l:
    ...    print('%s %r' % (i.id, i.matchProbability))
    o1 0.666666...
    o3 0.333333...
    o2 0.083333...
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests
    thisStreamStr = translateStreamToString(n)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests
        thatStreamStr = translateStreamToString(sn)
        ratio = difflib.SequenceMatcher(isJunk, thisStreamStr, thatStreamStr).ratio()
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key=lambda x: 1 - x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


def approximateNoteSearchNoRhythm(thisStream, otherStreams):
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)

    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 d#2 f A a' G b")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c4 d e GG CCC r")
    >>> o3.id = 'o3'
    >>> l = search.approximateNoteSearchNoRhythm(s, [o1, o2, o3])
    >>> for i in l:
    ...    print('%s %r' % (i.id, i.matchProbability))
    o1 0.83333333...
    o3 0.5
    o2 0.1666666...
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests.stream()
    thisStreamStr = translateStreamToStringNoRhythm(n)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests.stream()
        thatStreamStr = translateStreamToStringNoRhythm(sn)
        ratio = difflib.SequenceMatcher(isJunk, thisStreamStr, thatStreamStr).ratio()
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key=lambda x: 1 - x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


def approximateNoteSearchOnlyRhythm(thisStream, otherStreams):
    # noinspection PyShadowingNames
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)

    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 d#2 f A a' G b")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c4 d e GG CCC r")
    >>> o3.id = 'o3'
    >>> l = search.approximateNoteSearchOnlyRhythm(s, [o1, o2, o3])
    >>> for i in l:
    ...    print('%s %r' % (i.id, i.matchProbability))
    o1 0.5
    o3 0.33...
    o2 0.0
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests.stream()
    thisStreamStr = translateStreamToStringOnlyRhythm(n)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests.stream()
        thatStreamStr = translateStreamToStringOnlyRhythm(sn)
        ratio = difflib.SequenceMatcher(isJunk, thisStreamStr, thatStreamStr).ratio()
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key=lambda x: 1 - x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


def approximateNoteSearchWeighted(thisStream, otherStreams):
    # noinspection PyShadowingNames
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)

    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG2 a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 AAA4 AAA8 AAA16 AAA16 AAA4 AAA4")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c8 d16 e32 FF32 a'8 b-8")
    >>> o3.id = 'o3'
    >>> o4 = converter.parse("tinynotation: 4/4 c1 d1 e1 FF1 a'1 b-1")
    >>> o4.id = 'o4'
    >>> l = search.approximateNoteSearchWeighted(s, [o1, o2, o3, o4])
    >>> for i in l:
    ...    print('%s %r' % (i.id, i.matchProbability))
    o3 0.83333...
    o1 0.75
    o4 0.75
    o2 0.25
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests.stream()
    thisStreamStrPitches = translateStreamToStringNoRhythm(n)
    thisStreamStrDuration = translateStreamToStringOnlyRhythm(n)
    # print('notes',thisStreamStrPitches)
    # print('rhythm',thisStreamStrDuration)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests
        thatStreamStrPitches = translateStreamToStringNoRhythm(sn)
        thatStreamStrDuration = translateStreamToStringOnlyRhythm(sn)
        # print('notes2',thisStreamStrPitches)
        # print('rhythm2',thisStreamStrDuration)
        ratioPitches = difflib.SequenceMatcher(isJunk,
                                               thisStreamStrPitches,
                                               thatStreamStrPitches).ratio()
        ratioDuration = difflib.SequenceMatcher(isJunk,
                                                thisStreamStrDuration,
                                                thatStreamStrDuration).ratio()
        ratio = (3 * ratioPitches + ratioDuration) / 4.0
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key=lambda x: 1 - x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


# noinspection SpellCheckingInspection
def translateStreamToString(inputStreamOrIterator, returnMeasures=False):
    '''
    takes a stream (or streamIterator) of notesAndRests only and returns
    a string for searching on.

    >>> s = converter.parse("tinynotation: 3/4 c4 d8 r16 FF8. a'8 b-2.")
    >>> sn = s.flat.notesAndRests
    >>> streamString = search.translateStreamToString(sn)
    >>> print(streamString)
    <P>F<)KQFF_
    >>> len(streamString)
    12
    '''
    b = ''
    measures = []
    for n in inputStreamOrIterator:
        b += translateNoteWithDurationToBytes(n)
        if returnMeasures:
            measures.append(n.measureNumber)
    if returnMeasures is False:
        return b
    else:
        return (b, measures)


def translateDiatonicStreamToString(inputStreamOrIterator, returnMeasures=False):
    # noinspection SpellCheckingInspection, PyShadowingNames
    r'''
    Translates a Stream or StreamIterator of Notes and Rests only into a string,
    encoding only the .step (no accidental or octave) and whether
    the note is slower, faster, or the same speed as the previous
    note.

    Skips all but the first note of tie. Skips multiple rests in a row

    Each note gets one byte:

    A-G = note of same length as previous
    H-N = note of longer length than previous
    O-U = note of shorter length than previous
    Z = rest


    >>> s = converter.parse("tinynotation: 3/4 c4 d8~ d16 r16 FF8 F#8 a'8 b-2.")
    >>> streamString = search.translateDiatonicStreamToString(s.recurse().notesAndRests)
    >>> print(streamString)
    CRZFFAI
    >>> len(streamString)
    7

    If returnMeasures is True, returns an array of measureNumbers where each entry represents
    the measure number of the measure of the object at that character position :

    >>> streamString2, measures = search.translateDiatonicStreamToString(s.recurse().notesAndRests,
    ...                                    returnMeasures=True)
    >>> streamString == streamString2
    True
    >>> measures
    [1, 1, 1, 1, 1, 2, 2]
    '''
    b = []
    measures = []
    previousRest = False
    previousTie = False
    previousQL = None
    for n in inputStreamOrIterator:
        mNum = None
        if returnMeasures:
            mNum = n.measureNumber

        if n.isRest:
            if previousRest is True:
                continue
            else:
                previousRest = True
                b.append('Z')
                measures.append(mNum)
                continue
        else:
            previousRest = False
        if previousTie is True:
            if n.tie is None or n.tie.type == 'stop':
                previousTie = False
            continue
        elif n.tie is not None:
            previousTie = True
        ql = n.duration.quarterLength
        if previousQL is None or previousQL == ql:
            ascShift = 0
        elif previousQL > ql:
            ascShift = 14
        else:
            ascShift = 7
        previousQL = ql
        newName = chr(ord(n.pitches[0].step) + ascShift)
        measures.append(mNum)
        b.append(newName)

    joined = ''.join(b)
    if returnMeasures is False:
        return joined
    else:
        return (joined, measures)


def translateIntervalsAndSpeed(inputStream, returnMeasures=False):
    # noinspection PyShadowingNames
    r'''
    Translates a Stream (not StreamIterator) of Notes and Rests only into a string,
    encoding only the chromatic distance from the last note and whether
    the note is slower, faster, or the same speed as the previous
    note.

    Skips all but the first note of tie. Skips multiple rests in a row

    Each note gets one byte and encodes up from -13 to 13 (all notes > octave are 13 or -13)


    >>> s = converter.parse("tinynotation: 3/4 c4 d8~ d16 r16 F8 F#8 F8 a'8 b-2")
    >>> sn = s.flat.notesAndRests.stream()
    >>> streamString = search.translateIntervalsAndSpeed(sn)
    >>> print(streamString)
    Ib RHJ<9
    >>> print([ord(x) for x in streamString])
    [73, 98, 32, 82, 72, 74, 60, 57]
    >>> len(streamString)
    8

    If returnMeasures is True, returns a triplet of whether the last note
    was a rest, whether the last note was tied, what the last quarterLength was, and what the
    last pitches' midi number was

    which can be fed back into this algorithm:

    >>> streamString2, measures = search.translateIntervalsAndSpeed(sn, returnMeasures=True)
    >>> streamString == streamString2
    True
    >>> measures
    [1, 1, 1, 1, 1, 2, 2, 2]
    '''
    b = []
    measures = []

    previousRest = False
    previousTie = False
    previousQL = None
    previousMidi = 60
    for n in inputStream:
        if n.isNote:
            previousMidi = n.pitches[0].midi
            break

    for n in inputStream:
        mNum = None
        if returnMeasures:
            mNum = n.measureNumber
        if n.isRest:
            if previousRest is True:
                continue
            else:
                previousRest = True
                b.append(' ')
                measures.append(mNum)
                continue
        else:
            previousRest = False
        if previousTie is True:
            if n.tie is None or n.tie.type == 'stop':
                previousTie = False
            continue
        elif n.tie is not None:
            previousTie = True
        ql = n.duration.quarterLength
        if previousQL is None or previousQL == ql:
            ascShift = 27 + 14
        elif previousQL > ql:
            ascShift = 27 * 2 + 14
        else:
            ascShift = 14
        previousQL = ql
        pitchDifference = previousMidi - n.pitches[0].midi
        if pitchDifference > 13:
            pitchDifference = 13
        elif pitchDifference < -13:
            pitchDifference = -13
        previousMidi = n.pitches[0].midi
        newName = chr(32 + pitchDifference + ascShift)
        measures.append(mNum)
        b.append(newName)

    joined = ''.join(b)
    if returnMeasures is False:
        return joined
    else:
        return (joined, measures)


def translateStreamToStringNoRhythm(inputStream, returnMeasures=False):
    '''
    takes a stream or streamIterator of notesAndRests only and returns
    a string for searching on, using translateNoteToByte.

    >>> s = converter.parse("tinynotation: 4/4 c4 d e FF a'2 b-2")
    >>> sn = s.flat.notesAndRests
    >>> search.translateStreamToStringNoRhythm(sn)
    '<>@)QF'

    With returnMeasures, will return a tuple of bytes and a list of measure numbers:

    >>> search.translateStreamToStringNoRhythm(sn, returnMeasures=True)
    ('<>@)QF', [1, 1, 1, 1, 2, 2])
    '''
    b = ''
    measures = []
    for n in inputStream:
        b += translateNoteToByte(n)
        if returnMeasures:
            measures.append(n.measureNumber)
    if returnMeasures:
        return (b, measures)
    else:
        return b


def translateStreamToStringOnlyRhythm(inputStream, returnMeasures=False):
    '''
    takes a stream or streamIterator of notesAndRests only and returns
    a string for searching on.

    >>> s = converter.parse("tinynotation: 3/4 c4 d8 e16 FF8. a'8 b-2.")
    >>> sn = s.flat.notesAndRests
    >>> streamString = search.translateStreamToStringOnlyRhythm(sn)
    >>> print(streamString)
    PF<KF_
    >>> len(streamString)
    6
    '''
    b = ''
    measures = []
    for n in inputStream:
        b += translateDurationToBytes(n)
        if returnMeasures:
            measures.append(n.measureNumber)
    if returnMeasures:
        return (b, measures)
    else:
        return b


def translateNoteToByte(n):
    '''
    takes a note.Note object and translates it to a single byte representation.

    currently returns the chr() for the note's midi number. or chr(127) for rests


    >>> n = note.Note('C4')
    >>> b = search.translateNoteToByte(n)
    >>> b
    '<'
    >>> ord(b)
    60
    >>> ord(b) == n.pitch.midi
    True

    Chords are currently just searched on the first Note (or treated as a Rest if None)
    '''
    if n.isRest:
        return chr(127)
    elif n.isChord:
        if n.pitches:
            return chr(n.pitches[0].midi)
        else:
            return chr(127)
    else:
        return chr(n.pitch.midi)


def translateNoteWithDurationToBytes(n, includeTieByte=True):
    # noinspection PyShadowingNames
    '''
    takes a note.Note object and translates it to a three-byte representation.

    currently returns the chr() for the note's midi number. or chr(127) for rests
    followed by the log of the quarter length (fitted to 1-127, see
    :func:`~music21.search.base.translateDurationToBytes`)
    followed by 's', 'c', or 'e' if includeTieByte is True and there is a tie.

    >>> n = note.Note('C4')
    >>> n.duration.quarterLength = 3  # dotted half
    >>> trans = search.translateNoteWithDurationToBytes(n)
    >>> trans
    '<_'
    >>> (2**(ord(trans[1])/10.0))/256  # approximately 3
    2.828...

    >>> n.tie = tie.Tie('stop')
    >>> trans = search.translateNoteWithDurationToBytes(n)
    >>> trans
    '<_e'

    >>> trans = search.translateNoteWithDurationToBytes(n, includeTieByte=False)
    >>> trans
    '<_'
    '''
    firstByte = translateNoteToByte(n)
    secondByte = translateDurationToBytes(n)
    thirdByte = translateNoteTieToByte(n)
    if includeTieByte is True:
        return firstByte + secondByte + thirdByte
    else:
        return firstByte + secondByte


def translateNoteTieToByte(n):
    '''
    takes a note.Note object and returns a one-byte representation
    of its tie status.
    's' if start tie, 'e' if stop tie, 'c' if continue tie, and '' if no tie


    >>> n = note.Note('E')
    >>> search.translateNoteTieToByte(n)
    ''

    >>> n.tie = tie.Tie('start')
    >>> search.translateNoteTieToByte(n)
    's'

    >>> n.tie.type = 'continue'
    >>> search.translateNoteTieToByte(n)
    'c'

    >>> n.tie.type = 'stop'
    >>> search.translateNoteTieToByte(n)
    'e'
    '''
    if n.tie is None:
        return ''
    elif n.tie.type == 'start':
        return 's'
    elif n.tie.type == 'continue':
        return 'c'
    elif n.tie.type == 'stop':
        return 'e'
    else:
        return ''


def translateDurationToBytes(n):
    '''
    takes a note.Note object and translates it to a two-byte representation

    currently returns the chr() for the note's midi number. or chr(127) for rests
    followed by the log of the quarter length (fitted to 1-127, see formula below)

    >>> n = note.Note('C4')
    >>> n.duration.quarterLength = 3  # dotted half
    >>> trans = search.translateDurationToBytes(n)
    >>> trans
    '_'
    >>> (2 ** (ord(trans[0]) / 10)) / 256  # approximately 3
    2.828...

    '''
    duration1to127 = 1
    if n.duration.quarterLength:
        duration1to127 = int(math.log2(n.duration.quarterLength * 256) * 10)
        duration1to127 = max(min(duration1to127, 127), 1)
    secondByte = chr(duration1to127)
    return secondByte


# -------------------

def mostCommonMeasureRhythms(streamIn, transposeDiatonic=False):
    '''
    returns a sorted list of dictionaries
    of the most common rhythms in a stream where
    each dictionary contains:

    number: the number of times a rhythm appears
    rhythm: the rhythm found (with the pitches of the first instance of the rhythm transposed to C5)
    measures: a list of measures containing the rhythm
    rhythmString: a string representation of the rhythm (see translateStreamToStringOnlyRhythm)


    >>> bach = corpus.parse('bwv1.6')
    >>> sortedRhythms = search.mostCommonMeasureRhythms(bach)
    >>> for in_dict in sortedRhythms[0:3]:
    ...     print('no: %s %s %s' % (in_dict['number'], 'rhythmString:', in_dict['rhythmString']))
    ...     print('bars: %r' % ([(m.number,
    ...                               str(m.getContextByClass('Part').id))
    ...                            for m in in_dict['measures']]))
    ...     in_dict['rhythm'].show('text')
    ...     print('-----')
    no: 34 rhythmString: PPPP
    bars: [(1, 'Soprano'), (1, 'Alto'), (1, 'Tenor'), (1, 'Bass'), (2, ...), ..., (19, 'Soprano')]
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note A>
    {2.0} <music21.note.Note F>
    {3.0} <music21.note.Note C>
    -----
    no: 7 rhythmString: ZZ
    bars: [(13, 'Soprano'), (13, 'Alto'), ..., (14, 'Bass')]
    {0.0} <music21.note.Note C>
    {2.0} <music21.note.Note A>
    -----
    no: 6 rhythmString: ZPP
    bars: [(6, 'Soprano'), (6, 'Bass'), ..., (18, 'Tenor')]
    {0.0} <music21.note.Note C>
    {2.0} <music21.note.Note B->
    {3.0} <music21.note.Note B->
    -----
    '''
    returnDicts = []
    distanceToTranspose = 0

    for thisMeasure in streamIn.semiFlat.getElementsByClass('Measure'):
        rhythmString = translateStreamToStringOnlyRhythm(thisMeasure.notesAndRests)
        rhythmFound = False
        for entry in returnDicts:
            if entry['rhythmString'] == rhythmString:
                rhythmFound = True
                entry['number'] += 1
                entry['measures'].append(thisMeasure)
                break
        if rhythmFound is False:
            newDict = {
                'number': 1,
                'rhythmString': rhythmString,
            }
            measureNotes = thisMeasure.notes
            foundNote = False
            for i in range(len(measureNotes)):
                if 'Note' in measureNotes[i].classes:
                    distanceToTranspose = 72 - measureNotes[0].pitch.ps
                    foundNote = True
                    break
            if foundNote:
                thisMeasureCopy = copy.deepcopy(thisMeasure)
                for n in thisMeasureCopy.notes:
                    # TODO: Transpose Diatonic
                    n.transpose(distanceToTranspose, inPlace=True)
                newDict['rhythm'] = thisMeasureCopy
            else:
                newDict['rhythm'] = thisMeasure
            newDict['measures'] = [thisMeasure]
            returnDicts.append(newDict)

    sortedDicts = sorted(returnDicts, key=lambda k: k['number'], reverse=True)
    return sortedDicts


class SearchException(exceptions21.Music21Exception):
    pass


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''
        Test copying all objects defined in this module
        '''
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(obj) and not isinstance(obj, types.FunctionType):
                i = copy.copy(obj)
                j = copy.deepcopy(obj)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [
    'StreamSearcher',
    'Wildcard',
    'WildcardDuration',
]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

