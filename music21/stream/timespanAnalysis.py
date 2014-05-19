# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespanAnalysis.py
# Purpose:      Tools for grouping notes and chords into a searchable tree
#               organized by start and stop offsets
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013-14 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------
'''
Tools for performing voice-leading analysis with timespans.
'''

import collections
import unittest

from music21 import chord
from music21 import environment
from music21 import pitch

environLocal = environment.Environment("stream.timespanAnalysis")


#------------------------------------------------------------------------------


class Horizontality(collections.Sequence):
    r'''
    A horizontality of consecutive elementTimespan objects.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_timespans',
        )

    ### INITIALIZER ###

    def __init__(self,
        timespans=None,
        ):
        assert isinstance(timespans, collections.Sequence)
        assert len(timespans)
        assert all(hasattr(x, 'startOffset') and hasattr(x, 'stopOffset')
            for x in timespans)
        self._timespans = tuple(timespans)

    ### SPECIAL METHODS ###

    def __getitem__(self, item):
        return self._timespans[item]

    def __len__(self):
        return len(self._timespans)

    def __repr__(self):
        pitch_strings = []
        for x in self:
            string = '({},)'.format(', '.join(
                y.nameWithOctave for y in x.pitches))
            pitch_strings.append(string)
        return '<{}: {}>'.format(
            type(self).__name__,
            ' '.join(pitch_strings),
            )

    ### PROPERTIES ###

    @property
    def hasPassingTone(self):
        r'''
        Is true if the horizontality contains a passing tone.
        '''
        if len(self) < 3:
            return False
        elif not all(len(x.pitches) for x in self):
            return False
        pitches = (
            self[0].pitches[0],
            self[1].pitches[0],
            self[2].pitches[0],
            )
        if pitches[0] < pitches[1] < pitches[2]:
            return True
        elif pitches[0] > pitches[1] > pitches[2]:
            return True
        return False

    @property
    def hasNeighborTone(self):
        r'''
        Is true if the horizontality contains a neighbor tone.
        '''
        if len(self) < 3:
            return False
        elif not all(len(x.pitches) for x in self):
            return False
        pitches = (
            self[0].pitches[0],
            self[1].pitches[0],
            self[2].pitches[0],
            )
        if pitches[0] == pitches[2]:
            if abs(pitches[1].ps - pitches[0].ps) < 3:
                return True
        return False


#------------------------------------------------------------------------------


class Verticality(object):
    r'''
    A collection of information about elements that are sounding at a given
    offset or just finished at that offset or are continuing from before, etc..


    Create a timespan-stream from a score:

    ::

        >>> score = corpus.parse('bwv66.6')
        >>> tree = stream.timespans.streamToTimespanCollection(score)


    Find the verticality at offset 6.5, or beat 2.5 of measure 2 (there's a one
    beat pickup)

    ::

        >>> verticality = tree.getVerticalityAt(6.5)
        >>> verticality
        <Verticality 6.5 {E3 D4 G#4 B4}>

    The representation of a verticality gives the pitches from lowest to
    highest (in sounding notes).


    A verticality knows its startOffset, but because elements might end at
    different times, it doesn't know its stopOffset

    ::

        >>> verticality.startOffset
        6.5
        >>> verticality.stopOffset
        Traceback (most recent call last):
        AttributeError: 'Verticality' object has no attribute 'stopOffset'

    However, we can find when the next verticality starts by looking at the
    nextVerticality

    ::

        >>> verticality.nextVerticality
        <Verticality 7.0 {A2 C#4 E4 A4}>
        >>> verticality.nextVerticality.startOffset
        7.0

    Or more simply:

    ::

        >>> verticality.nextStartOffset
        7.0

    (There is also a previousVerticality, but not a previousStartOffset)

    What we just demonstrated is actually very powerful: a Verticality keeps a
    record of exactly where it is in the timespanStream -- scores can be
    recreated with this information.

    Getting back to the task at hand, we can find all the elementTimespans (and
    from there the elements) that start at exactly 6.5.  There's one, it's a
    passing tone D in the tenor and it lastes from offset 6.5 to offset 7.0,
    with respect to the beginning of the score, not to the beginning of the
    measure.  That is to say, it's an eighth note

    ::

        >>> verticality.startTimespans
        (<ElementTimespan (6.5 to 7.0) <music21.note.Note D>>,)


    And we can get all the elementTimespans that were already sounding at the
    moment (that is to say, the non-passing tones):

    ::

        >>> verticality.overlapTimespans
        (<ElementTimespan (6.0 to 7.0) <music21.note.Note B>>,
         <ElementTimespan (6.0 to 7.0) <music21.note.Note G#>>,
         <ElementTimespan (6.0 to 7.0) <music21.note.Note E>>)

    And we can get all the things that stop right at this moment.  It's the E
    in the tenor preceding the passing tone D:

    ::

        >>> verticality.stopTimespans
        (<ElementTimespan (6.0 to 6.5) <music21.note.Note E>>,)

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_timespanStream',
        '_overlapTimespans',
        '_startTimespans',
        '_startOffset',
        '_stopTimespans',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        timespanStream=None,
        overlapTimespans=None,
        startTimespans=None,
        startOffset=None,
        stopTimespans=None,
        ):
        from music21.stream import timespans
        prototype = (timespans.TimespanCollection, type(None))
        assert isinstance(timespanStream, prototype)
        self._timespanStream = timespanStream
        self._startOffset = startOffset
        assert isinstance(startTimespans, tuple)
        assert isinstance(stopTimespans, (tuple, type(None)))
        assert isinstance(overlapTimespans, (tuple, type(None)))
        self._startTimespans = startTimespans
        self._stopTimespans = stopTimespans
        self._overlapTimespans = overlapTimespans

    ### SPECIAL METHODS ###

    def __repr__(self):
        sortedPitches = sorted(self.pitchSet)
        return '<{} {} {{{}}}>'.format(
            type(self).__name__,
            self.startOffset,
            ' '.join(x.nameWithOctave for x in sortedPitches)
            )

    ### PUBLIC PROPERTIES ###

    @property
    def bassTimespan(self):
        r'''
        Gets the bass timespan in this verticality.

        This is CURRENTLY the lowest PART not the lowest note necessarily.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

        ::

            >>> verticality.bassTimespan
            <ElementTimespan (1.0 to 2.0) <music21.note.Note F#>>

        '''
        pitches = sorted(self.pitchSet)
        lowestPitch = pitches[0]
        timespans = self.startTimespans + self.overlapTimespans
        bassTimespans = []
        for timespan in timespans:
            pitches = timespan.pitches
            if lowestPitch in pitches:
                bassTimespans.append(timespan)
        if bassTimespans:
            bassTimespans.sort(
                key=lambda x: x.part.getInstrument().partId,
                reverse=True,
                )
            return bassTimespans[0]
        return None

    @property
    def beatStrength(self):
        r'''
        Gets the beat strength of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.beatStrength
            1.0

        '''
        thisElementTimespan = self.startTimespans[0]
        if self.startOffset == 1.0:
            pass  # debugging; delete
        return thisElementTimespan.beatStrength

    @property
    def degreeOfOverlap(self):
        '''
        Counts the number of things sounding at this moment
        '''

        return len(self.startTimespans) + len(self.overlapTimespans)

    def toChord(self):
        '''
        creates a chord object from the verticality
        '''
        pitchSet = sorted(self.pitchSet)
        testChord = chord.Chord(pitchSet)
        return testChord

    @property
    def isConsonant(self):
        r'''
        Is true when the pitch set of a verticality is consonant.

        ::

                >>> score = corpus.parse('bwv66.6')
                >>> tree = stream.timespans.streamToTimespanCollection(score)
                >>> verticalities = list(tree.iterateVerticalities())
                >>> for verticality in verticalities[:10]:
                ...     print verticality, verticality.isConsonant
                ...
                <Verticality 0.0 {A3 E4 C#5}> True
                <Verticality 0.5 {G#3 B3 E4 B4}> True
                <Verticality 1.0 {F#3 C#4 F#4 A4}> True
                <Verticality 2.0 {G#3 B3 E4 B4}> True
                <Verticality 3.0 {A3 E4 C#5}> True
                <Verticality 4.0 {G#3 B3 E4 E5}> True
                <Verticality 5.0 {A3 E4 C#5}> True
                <Verticality 5.5 {C#3 E4 A4 C#5}> True
                <Verticality 6.0 {E3 E4 G#4 B4}> True
                <Verticality 6.5 {E3 D4 G#4 B4}> False

        '''
        return self.toChord().isConsonant()

    @property
    def measureNumber(self):
        r'''
        Gets the measure number of the verticality's starting elements.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(7.0)
            >>> verticality.measureNumber
            2

        '''
        return self.startTimespans[0].measureNumber

    @property
    def nextStartOffset(self):
        r'''
        Gets the next start-offset in the verticality's offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.nextStartOffset
            2.0

        '''
        tree = self._timespanStream
        if tree is None:
            return None
        startOffset = tree.getStartOffsetAfter(self.startOffset)
        return startOffset

    @property
    def nextVerticality(self):
        r'''
        Gets the next verticality after a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> print verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

        ::

            >>> nextVerticality = verticality.nextVerticality
            >>> print nextVerticality
            <Verticality 2.0 {G#3 B3 E4 B4}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        ::

            >>> tree.remove(nextVerticality.startTimespans)
            >>> verticality.nextVerticality
            <Verticality 3.0 {A3 E4 C#5}>

        '''
        tree = self._timespanStream
        if tree is None:
            return None
        startOffset = tree.getStartOffsetAfter(self.startOffset)
        if startOffset is None:
            return None
        return tree.getVerticalityAt(startOffset)

    @property
    def overlapTimespans(self):
        r'''
        Gets timespans overlapping the start offset of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(0.5)
            >>> verticality.overlapTimespans
            (<ElementTimespan (0.0 to 1.0) <music21.note.Note E>>,)

        '''
        return self._overlapTimespans

    @property
    def pitchSet(self):
        r'''
        Gets the pitch set of all elements in a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for pitch in sorted(verticality.pitchSet):
            ...     pitch
            ...
            <music21.pitch.Pitch F#3>
            <music21.pitch.Pitch C#4>
            <music21.pitch.Pitch F#4>
            <music21.pitch.Pitch A4>

        '''
        pitchSet = set()
        for elementTimespan in self.startTimespans:
            element = elementTimespan.element
            if hasattr(element, 'pitches'):
                pitches = [x.nameWithOctave for x in element.pitches]
                pitchSet.update(pitches)
        for elementTimespan in self.overlapTimespans:
            element = elementTimespan.element
            if hasattr(element, 'pitches'):
                pitches = [x.nameWithOctave for x in element.pitches]
                pitchSet.update(pitches)
        pitchSet = set([pitch.Pitch(x) for x in pitchSet])
        return pitchSet

    @property
    def pitchClassSet(self):
        r'''
        Gets the pitch-class set of all elements in a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for pitchClass in sorted(verticality.pitchClassSet):
            ...     pitchClass
            ...
            <music21.pitch.Pitch C#>
            <music21.pitch.Pitch F#>
            <music21.pitch.Pitch A>

        '''
        pitchClassSet = set()
        for currentPitch in self.pitchSet:
            pitchClass = pitch.Pitch(currentPitch.name)
            pitchClassSet.add(pitchClass)
        return pitchClassSet

    @property
    def previousVerticality(self):
        r'''
        Gets the previous verticality before a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> print verticality
            <Verticality 1.0 {F#3 C#4 F#4 A4}>

        ::

            >>> previousVerticality = verticality.previousVerticality
            >>> print previousVerticality
            <Verticality 0.5 {G#3 B3 E4 B4}>

        Verticality objects created by an offset-tree hold a reference back to
        that offset-tree. This means that they determine their next or previous
        verticality dynamically based on the state of the offset-tree only when
        asked. Because of this, it is safe to mutate the offset-tree by
        inserting or removing timespans while iterating over it.

        ::

            >>> tree.remove(previousVerticality.startTimespans)
            >>> verticality.previousVerticality
            <Verticality 0.0 {A3 E4 C#5}>

        '''
        tree = self._timespanStream
        if tree is None:
            return None
        startOffset = tree.getStartOffsetBefore(self.startOffset)
        if startOffset is None:
            return None
        return tree.getVerticalityAt(startOffset)

    @property
    def startOffset(self):
        r'''
        Gets the start offset of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.startOffset
            1.0

        '''
        return self._startOffset

    @property
    def startTimespans(self):
        r'''
        Gets the timespans starting at a verticality's start offset.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for timespan in verticality.startTimespans:
            ...     timespan
            ...
            <ElementTimespan (1.0 to 2.0) <music21.note.Note A>>
            <ElementTimespan (1.0 to 2.0) <music21.note.Note F#>>
            <ElementTimespan (1.0 to 2.0) <music21.note.Note C#>>
            <ElementTimespan (1.0 to 2.0) <music21.note.Note F#>>

        '''
        return self._startTimespans

    @property
    def stopTimespans(self):
        r'''
        Gets the timespans stopping at a verticality's start offset.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = stream.timespans.streamToTimespanCollection(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for timespan in verticality.stopTimespans:
            ...     timespan
            ...
            <ElementTimespan (0.0 to 1.0) <music21.note.Note E>>
            <ElementTimespan (0.5 to 1.0) <music21.note.Note B>>
            <ElementTimespan (0.5 to 1.0) <music21.note.Note B>>
            <ElementTimespan (0.5 to 1.0) <music21.note.Note G#>>

        '''
        return self._stopTimespans


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (
    )


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
