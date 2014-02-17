# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         offsetTree.py
# Purpose:      Tools for grouping notes and chords into a searchable tree
#               organized by start and stop offsets
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------

import collections
import random
import unittest
from music21 import chord
from music21 import instrument
from music21 import note
from music21 import pitch
from music21 import stream


class Parentage(object):
    r'''
    The parentage hierarchy of an element in a score.

    ::

        >>> score = corpus.parse('bwv66.6')
        >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
        >>> verticality = tree.getVerticalityAt(1.0)
        >>> parentage = verticality.startTimespans[0]
        >>> parentage
        <Parentage 1.0:2.0 <music21.note.Note A>>

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_element',
        '_parentage',  # TODO: rename to ancestry?
        '_startOffset',
        '_stopOffset',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        element,
        parentage,
        startOffset=None,
        stopOffset=None,
        ):
        self._element = element
        assert len(parentage), parentage
        parentage = tuple(parentage)
        assert isinstance(parentage[0], stream.Measure), parentage[0]
        assert isinstance(parentage[-1], stream.Score), parentage[-1]
        self._parentage = parentage
        self._startOffset = startOffset
        self._stopOffset = stopOffset

    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<{} {}:{} {!r}>'.format(
            type(self).__name__,
            self.startOffset,
            self.stopOffset,
            self.element,
            )

    ### PUBLIC METHODS ###

    def mergeWith(self, parentage):
        assert isinstance(parentage, type(self))
        assert (self.stopOffset == parentage.startOffset) or \
            (parentage.stopOffset == self.startOffset)
        assert self.pitches == parentage.pitches
        if self.startOffset < parentage.startOffset:
            mergedParentage = self.new(stopOffset=parentage.stopOffset)
        else:
            mergedParentage = parentage.new(stopOffset=self.stopOffset)
        return mergedParentage

    def new(
        self,
        element=None,
        startOffset=None,
        stopOffset=None,
        ):
        element = element or self.element
        startOffset = startOffset or self.startOffset
        stopOffset = stopOffset or self.stopOffset
        return type(self)(
            element,
            self.parentage,
            startOffset=startOffset,
            stopOffset=stopOffset,
            )

    def splitAt(self, offset):
        r'''
        Split parentage at `offset`.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(0)
            >>> timespan = verticality.startTimespans[0]
            >>> timespan
            <Parentage 0.0:0.5 <music21.note.Note C#>>

        ::

            >>> for shard in timespan.splitAt(0.25):
            ...     shard
            ...
            <Parentage 0.0:0.25 <music21.note.Note C#>>
            <Parentage 0.25:0.5 <music21.note.Note C#>>

        ::

            >>> timespan.splitAt(1000)
            (<Parentage 0.0:0.5 <music21.note.Note C#>>,)

        '''

        if offset < self.startOffset or self.stopOffset < offset:
            return (self,)
        left = self.new(stopOffset=offset)
        right = self.new(startOffset=offset)
        return left, right

    ### PUBLIC PROPERTIES ###

    @property
    def element(self):
        r'''
        The parentage's element.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> parentage = verticality.startTimespans[0]
            >>> parentage.element
            <music21.note.Note A>

        '''
        return self._element

    @property
    def measureNumber(self):
        r'''
        The measure number of the measure containing the element.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> parentage = verticality.startTimespans[0]
            >>> parentage.measureNumber
            1

        '''
        return self.parentage[0].measureNumber

    @property
    def parentage(self):
        r'''
        The parentage hierarchy above the parentage's element.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> parentage = verticality.startTimespans[0]
            >>> for x in parentage.parentage:
            ...     x
            ...
            <music21.stream.Measure 1 offset=1.0>
            <music21.stream.Part Soprano>
            <music21.stream.Score ...>

        '''
        return self._parentage

    @property
    def part(self):
        for x in self.parentage:
            if not isinstance(x, stream.Part):
                continue
            return x
        return None

    @property
    def partName(self):
        r'''
        The part name of the part containing the parentage's element.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> parentage = verticality.startTimespans[0]
            >>> parentage.partName
            u'Soprano'

        '''
        part = self.part
        if part is None:
            return None
        for element in part:
            if isinstance(element, instrument.Instrument):
                return element.partName
        return None

    @property
    def pitches(self):
        r'''
        Gets the pitches of the element wrapped by this parentage.

        This treats notes as chords.
        '''
        result = []
        if hasattr(self.element, 'pitches'):
            result.extend(self.element.pitches)
        result.sort()
        return tuple(result)

    @property
    def startOffset(self):
        r'''
        The start offset of the parentage's element, relative to its containing
        score.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> parentage = verticality.startTimespans[0]
            >>> parentage.startOffset
            1.0

        '''
        return self._startOffset

    @property
    def stopOffset(self):
        r'''
        The stop offset of the parentage's element, relative to its containing
        score.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> parentage = verticality.startTimespans[0]
            >>> parentage.stopOffset
            2.0

        '''
        return self._stopOffset


class Horizontality(collections.Sequence):
    r'''
    A horizontality of consecutive parentage objects.
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


class Verticality(object):
    r'''
    A verticality of objects at a given start offset.

    ::

        >>> score = corpus.parse('bwv66.6')
        >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
        >>> verticality = tree.getVerticalityAt(1.0)
        >>> verticality
        <Verticality 1.0 {A4 C#4 F#3 F#4}>

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_offsetTree',
        '_overlapTimespans',
        '_startTimespans',
        '_startOffset',
        '_stopTimespans',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        offsetTree=None,
        overlapTimespans=None,
        startTimespans=None,
        startOffset=None,
        stopTimespans=None,
        ):
        assert isinstance(offsetTree, (OffsetTree, type(None)))
        self._offsetTree = offsetTree
        self._startOffset = startOffset
        assert isinstance(startTimespans, tuple)
        assert isinstance(stopTimespans, (tuple, type(None)))
        assert isinstance(overlapTimespans, (tuple, type(None)))
        self._startTimespans = startTimespans
        self._stopTimespans = stopTimespans
        self._overlapTimespans = overlapTimespans

    def __repr__(self):
        sortedPitches = sorted(self.pitchSet)
        return '<{} {} {{{}}}>'.format(
            type(self).__name__,
            self.startOffset,
            ' '.join(sorted(x.nameWithOctave for x in sortedPitches))
            )

    ### PUBLIC METHODS ###

    @staticmethod
    def pitchesAreConsonant(
        pitches,
        ):
        assert all(isinstance(x, pitch.Pitch) for x in pitches)
        pitchClassSet = sorted(pitch.Pitch(x.nameWithOctave)
            for x in pitches)
        testChord = chord.Chord(pitchClassSet)
        return testChord.isConsonant()

    ### PUBLIC PROPERTIES ###

    @property
    def beatStrength(self):
        r'''
        Gets the beat strength of a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.beatStrength
            1.0

        '''
        return self.startTimespans[0].element.beatStrength

    @property
    def isConsonant(self):
        r'''
        Is true when the pitch set of a verticality is consonant.

        ::

                >>> score = corpus.parse('bwv66.6')
                >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
                >>> verticalities = list(tree.iterateVerticalities())
                >>> for verticality in verticalities[:10]:
                ...     print verticality, verticality.isConsonant
                ...
                <Verticality 0.0 {A3 C#5 E4}> True
                <Verticality 0.5 {B3 B4 E4 G#3}> True
                <Verticality 1.0 {A4 C#4 F#3 F#4}> False
                <Verticality 2.0 {B3 B4 E4 G#3}> True
                <Verticality 3.0 {A3 C#5 E4}> True
                <Verticality 4.0 {B3 E4 E5 G#3}> True
                <Verticality 5.0 {A3 C#5 E4}> True
                <Verticality 5.5 {A4 C#3 C#5 E4}> True
                <Verticality 6.0 {B4 E3 E4 G#4}> True
                <Verticality 6.5 {B4 D4 E3 G#4}> False

        '''
        return self.pitchesAreConsonant(self.pitchClassSet)

    @property
    def measureNumber(self):
        r'''
        Gets the measure number of the verticality's starting elements.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(7.0)
            >>> verticality.measureNumber
            2

        '''
        return self.startTimespans[0].measureNumber

    @property
    def nextVerticality(self):
        r'''
        Gets the next verticality after a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.nextVerticality
            <Verticality 2.0 {B3 B4 E4 G#3}>

        '''
        tree = self._offsetTree
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
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(0.5)
            >>> verticality.overlapTimespans
            (<Parentage 0.0:1.0 <music21.note.Note E>>,)

        '''
        return self._overlapTimespans

    @property
    def pitchSet(self):
        r'''
        Gets the pitch set of all elements in a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
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
        for parentage in self.startTimespans:
            element = parentage.element
            pitches = [x.nameWithOctave for x in element.pitches]
            pitchSet.update(pitches)
        for parentage in self.overlapTimespans:
            element = parentage.element
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
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
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
            pitchClassSet.add(currentPitch.name)
        pitchClassSet = set([pitch.Pitch(x) for x in pitchClassSet])
        return pitchClassSet

    @property
    def previousVerticality(self):
        r'''
        Gets the previous verticality before a verticality.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> verticality.previousVerticality
            <Verticality 0.5 {B3 B4 E4 G#3}>

        '''
        tree = self._offsetTree
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
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
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
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for timespan in verticality.startTimespans:
            ...     timespan
            ...
            <Parentage 1.0:2.0 <music21.note.Note A>>
            <Parentage 1.0:2.0 <music21.note.Note F#>>
            <Parentage 1.0:2.0 <music21.note.Note C#>>
            <Parentage 1.0:2.0 <music21.note.Note F#>>

        '''
        return self._startTimespans

    @property
    def stopTimespans(self):
        r'''
        Gets the timespans stopping at a verticality's start offset.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> verticality = tree.getVerticalityAt(1.0)
            >>> for timespan in verticality.stopTimespans:
            ...     timespan
            ...
            <Parentage 0.0:1.0 <music21.note.Note E>>
            <Parentage 0.5:1.0 <music21.note.Note B>>
            <Parentage 0.5:1.0 <music21.note.Note B>>
            <Parentage 0.5:1.0 <music21.note.Note G#>>

        '''
        return self._stopTimespans


class OffsetTree(object):
    r'''
    An offset-tree.

    This datastructure stores timespans: objects which implement both a
    `startOffset` and `stopOffset` property. It provides fast lookups of such
    objects and can quickly locate vertical overlaps.

    While you can construct an offset-tree by hand, inserting timespans one at
    a time, the common use-case is to construct the offset-tree from an entire
    score at once:

    ::

        >>> score = corpus.parse('bwv66.6')
        >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
        >>> verticality = tree.getVerticalityAt(1.5)

    All offsets are assumed to be relative to the score's origin.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_root'
        )

    class OffsetTreeNode(object):
        r'''
        A node in an offset-tree.

        Not for public use.
        '''

        ### CLASS VARIABLES ###

        __slots__ = (
            '_balance',
            '_height',
            '_leftChild',
            '_rightChild',
            '_startOffset',
            '_earliestStopOffset',
            '_latestStopOffset',
            '_payload',
            )

        ### INITIALIZER ###

        def __init__(self, startOffset):
            self._balance = 0
            self._earliestStopOffset = None
            self._height = 0
            self._latestStopOffset = None
            self._leftChild = None
            self._payload = []
            self._rightChild = None
            self._startOffset = startOffset

        ### SPECIAL METHODS ###

        def __repr__(self):
            return '<{}: {} {}>'.format(
                type(self).__name__,
                self.startOffset,
                self.payload,
                )

        ### PRIVATE METHODS ###

        def _update(self):
            leftHeight = -1
            rightHeight = -1
            if self.leftChild is not None:
                leftHeight = self.leftChild.height
            if self.rightChild is not None:
                rightHeight = self.rightChild.height
            self._height = max(leftHeight, rightHeight) + 1
            self._balance = rightHeight - leftHeight
            return self.height

        ### PUBLIC PROPERTIES ###

        @property
        def balance(self):
            return self._balance

        @property
        def earliestStopOffset(self):
            return self._earliestStopOffset

        @property
        def height(self):
            return self._height

        @property
        def latestStopOffset(self):
            return self._latestStopOffset

        @property
        def leftChild(self):
            return self._leftChild

        @leftChild.setter
        def leftChild(self, node):
            self._leftChild = node
            self._update()

        @property
        def payload(self):
            return self._payload

        @property
        def rightChild(self):
            return self._rightChild

        @rightChild.setter
        def rightChild(self, node):
            self._rightChild = node
            self._update()

        @property
        def startOffset(self):
            return self._startOffset

    ### INITIALIZER ###

    def __init__(self, *timespans):
        self._root = None
        if len(timespans) == 1 and isinstance(timespans[0], type(self)):
            timespans = [x for x in timespans[0]]
        if timespans:
            self.insert(*timespans)

    ### SPECIAL METHODS ###

    def __iter__(self):
        def recurse(node):
            if node is not None:
                if node.leftChild is not None:
                    for timespan in recurse(node.leftChild):
                        yield timespan
                for timespan in node.payload:
                    yield timespan
                if node.rightChild is not None:
                    for timespan in recurse(node.rightChild):
                        yield timespan
        return recurse(self._root)

    ### PRIVATE METHODS ###

    def _insert(self, node, startOffset):
        if node is None:
            return OffsetTree.OffsetTreeNode(startOffset)
        if startOffset < node.startOffset:
            node.leftChild = self._insert(node.leftChild, startOffset)
        elif node.startOffset < startOffset:
            node.rightChild = self._insert(node.rightChild, startOffset)
        return self._rebalance(node)

    def _rebalance(self, node):
        if node is not None:
            if 1 < node.balance:
                if 0 <= node.rightChild.balance:
                    node = self._rotateRightRight(node)
                else:
                    node = self._rotateRightLeft(node)
            elif node.balance < -1:
                if node.leftChild.balance <= 0:
                    node = self._rotateLeftLeft(node)
                else:
                    node = self._rotateLeftRight(node)
            assert -1 <= node.balance <= 1
        return node

    def _remove(self, node, startOffset):
        if node is not None:
            if node.startOffset == startOffset:
                if node.leftChild and node.rightChild:
                    nextNode = node.rightChild
                    while nextNode.leftChild:
                        nextNode = nextNode.leftChild
                    node._startOffset = nextNode._startOffset
                    node._payload = nextNode._payload
                    node.rightChild = self._remove(
                        node.rightChild, nextNode.startOffset)
                else:
                    node = node.leftChild or node.rightChild
            elif startOffset < node.startOffset:
                node.leftChild = self._remove(node.leftChild, startOffset)
            elif node.startOffset < startOffset:
                node.rightChild = self._remove(node.rightChild, startOffset)
        return self._rebalance(node)

    def _rotateLeftLeft(self, node):
        nextNode = node.leftChild
        node.leftChild = nextNode.rightChild
        nextNode.rightChild = node
        return nextNode

    def _rotateLeftRight(self, node):
        node.leftChild = self._rotateRightRight(node.leftChild)
        nextNode = self._rotateLeftLeft(node)
        return nextNode

    def _rotateRightLeft(self, node):
        node.rightChild = self._rotateLeftLeft(node.rightChild)
        nextNode = self._rotateRightRight(node)
        return nextNode

    def _rotateRightRight(self, node):
        nextNode = node.rightChild
        node.rightChild = nextNode.leftChild
        nextNode.leftChild = node
        return nextNode

    def _search(self, node, startOffset):
        if node is not None:
            if node.startOffset == startOffset:
                return node
            elif node.leftChild and startOffset < node.startOffset:
                return self._search(node.leftChild, startOffset)
            elif node.rightChild and node.startOffset < startOffset:
                return self._search(node.rightChild, startOffset)
        return None

    def _updateOffsets(self, node):
        if node is None:
            return
        minimum = min(x.stopOffset for x in node.payload)
        maximum = max(x.stopOffset for x in node.payload)
        if node.leftChild:
            leftMinimum, leftMaximum = self._updateOffsets(node.leftChild)
            if leftMinimum < minimum:
                minimum = leftMinimum
            if maximum < leftMaximum:
                maximum = leftMaximum
        if node.rightChild:
            rightMinimum, rightMaximum = self._updateOffsets(node.rightChild)
            if rightMinimum < minimum:
                minimum = rightMinimum
            if maximum < rightMaximum:
                maximum = rightMaximum
        node._earliestStopOffset = minimum
        node._latestStopOffset = maximum
        return minimum, maximum

    ### PUBLIC METHODS ###

    def copy(self):
        r'''
        Creates a new offset-tree with the same timespans as this offset-tree.

        This is analogous to `dict.copy()`.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> newTree = tree.copy()

        '''
        return type(self)(self)

    @staticmethod
    def extractMeasuresAndMeasureOffsets(inputScore):
        r'''
        Extract a measure template from `inputScore`.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> result = tree.extractMeasuresAndMeasureOffsets(score)
            >>> result[0]
            <music21.stream.Score ...>

        ::

            >>> result[1]
            [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0, 36.0]

        '''
        from music21 import meter
        part = inputScore.parts[0]
        score = stream.Score()
        offsets = []
        for oldMeasure in part:
            if not isinstance(oldMeasure, stream.Measure):
                continue
            offsets.append(oldMeasure.offset)
            newMeasure = stream.Measure()
            if oldMeasure.timeSignature is not None:
                newTimeSignature = meter.TimeSignature(
                    oldMeasure.timeSignature.ratioString,
                    )
                newMeasure.insert(0, newTimeSignature)
            score.append(newMeasure)
            newMeasure.number = oldMeasure.number
            newMeasure.offset = oldMeasure.offset
            newMeasure.paddingLeft = oldMeasure.paddingLeft
            newMeasure.paddingRight = oldMeasure.paddingRight
        offsets.append(inputScore.duration.quarterLength)
        return score, offsets

    def findTimespansStartingAt(self, offset):
        r'''
        Finds timespans in this offset-tree which start at `offset`.
        '''
        results = []
        node = self._search(self._root, offset)
        if node is not None:
            results.extend(node.payload)
        return tuple(results)

    def findTimespansStoppingAt(self, offset):
        r'''
        Finds timespans in this offset-tree which stop at `offset`.
        '''
        def recurse(node, offset):
            result = []
            if node.earliestStopOffset <= offset <= node.latestStopOffset:
                for timespan in node.payload:
                    if timespan.stopOffset == offset:
                        result.append(timespan)
                if node.leftChild is not None:
                    result.extend(recurse(node.leftChild, offset))
                if node.rightChild is not None:
                    result.extend(recurse(node.rightChild, offset))
            return result
        results = recurse(self._root, offset)
        results.sort(key=lambda x: (x.startOffset, x.stopOffset))
        return tuple(results)

    def findTimespansOverlapping(self, offset):
        r'''
        Finds timespans in this offset-tree which overlap `offset`.
        '''
        def recurse(node, offset, indent=0):
            result = []
            if node is not None:
                if node.startOffset < offset < node.latestStopOffset:
                    result.extend(recurse(node.leftChild, offset, indent + 1))
                    for timespan in node.payload:
                        if offset < timespan.stopOffset:
                            result.append(timespan)
                    result.extend(recurse(node.rightChild, offset, indent + 1))
                elif offset <= node.startOffset:
                    result.extend(recurse(node.leftChild, offset, indent + 1))
            return result
        results = recurse(self._root, offset)
        results.sort(key=lambda x: (x.startOffset, x.stopOffset))
        return tuple(results)

    @staticmethod
    def fromScore(inputScore):
        r'''
        Creates a new offset-tree from `inputScore`, populated by Parentage
        timespans.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> timespans = list(tree)
            >>> for timespan in timespans[:10]:
            ...     timespan
            ...
            <Parentage 0.0:0.5 <music21.note.Note C#>>
            <Parentage 0.0:0.5 <music21.note.Note A>>
            <Parentage 0.0:0.5 <music21.note.Note A>>
            <Parentage 0.0:1.0 <music21.note.Note E>>
            <Parentage 0.5:1.0 <music21.note.Note B>>
            <Parentage 0.5:1.0 <music21.note.Note B>>
            <Parentage 0.5:1.0 <music21.note.Note G#>>
            <Parentage 1.0:2.0 <music21.note.Note A>>
            <Parentage 1.0:2.0 <music21.note.Note F#>>
            <Parentage 1.0:2.0 <music21.note.Note C#>>

        '''
        def recurse(inputStream, parentages, currentParentage):
            for x in inputStream:
                if isinstance(x, stream.Measure):
                    localParentage = currentParentage + (x,)
                    measureOffset = x.offset
                    for element in x:
                        if not isinstance(element, (
                            note.Note,
                            chord.Chord,
                            )):
                            continue
                        elementOffset = element.offset
                        startOffset = measureOffset + elementOffset
                        stopOffset = startOffset + element.quarterLength
                        parentage = Parentage(
                            element,
                            tuple(reversed(localParentage)),
                            startOffset=startOffset,
                            stopOffset=stopOffset,
                            )
                        parentages.append(parentage)
                elif isinstance(x, stream.Stream):
                    localParentage = currentParentage + (x,)
                    recurse(x, parentages, localParentage)
        assert isinstance(inputScore, stream.Score), inputScore
        parentages = []
        initialParentage = (inputScore,)
        recurse(inputScore, parentages, currentParentage=initialParentage)
        tree = OffsetTree()
        tree.insert(*parentages)
        return tree

    def getStartOffsetAfter(self, offset):
        r'''
        Gets start offset after `offset`.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.getStartOffsetAfter(0.5)
            1.0

        ::

            >>> tree.getStartOffsetAfter(35) is None
            True

        Returns none if no succeeding offset exists.
        '''
        def recurse(node, offset):
            if node is None:
                return None
            result = None
            if node.startOffset <= offset and node.rightChild:
                result = recurse(node.rightChild, offset)
            elif offset < node.startOffset:
                result = recurse(node.leftChild, offset) or node
            return result
        result = recurse(self._root, offset)
        if result is None:
            return None
        return result.startOffset

    def getStartOffsetBefore(self, offset):
        r'''
        Gets the start offset immediately preceding `offset` in this
        offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.getStartOffsetBefore(100)
            35.0

        ::

            >>> tree.getStartOffsetBefore(0) is None
            True

        Return none if no preceding offset exists.
        '''
        def recurse(node, offset):
            if node is None:
                return None
            result = None
            if node.startOffset < offset:
                result = recurse(node.rightChild, offset) or node
            elif offset <= node.startOffset and node.leftChild:
                result = recurse(node.leftChild, offset)
            return result
        result = recurse(self._root, offset)
        if result is None:
            return None
        return result.startOffset

    def getVerticalityAt(self, offset):
        r'''
        Gets the verticality in this offset-tree which starts at `offset`.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.getVerticalityAt(2.5)
            <Verticality 2.5 {B3 B4 E4 G#3}>

        Return verticality.
        '''
        startTimespans = self.findTimespansStartingAt(offset)
        stopTimespans = self.findTimespansStoppingAt(offset)
        overlapTimespans = self.findTimespansOverlapping(offset)
        verticality = Verticality(
            offsetTree=self,
            overlapTimespans=overlapTimespans,
            startTimespans=startTimespans,
            startOffset=offset,
            stopTimespans=stopTimespans,
            )
        return verticality

    def insert(self, *timespans):
        r'''
        Inserts `timespans` into this offset-tree.
        '''
        for timespan in timespans:
            assert hasattr(timespan, 'startOffset'), timespan
            assert hasattr(timespan, 'stopOffset'), timespan
            self._root = self._insert(self._root, timespan.startOffset)
            node = self._search(self._root, timespan.startOffset)
            node.payload.append(timespan)
            node.payload.sort(key=lambda x: x.stopOffset)
        self._updateOffsets(self._root)

    def iterateConsonanceBoundedVerticalities(self):
        r'''
        Iterates consonant-bounded verticality subsequences in this
        offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> for subsequence in tree.iterateConsonanceBoundedVerticalities():
            ...     print 'Subequence:'
            ...     for verticality in subsequence:
            ...         print '\t[{}] {}: {} [{}]'.format(
            ...             verticality.measureNumber,
            ...             verticality,
            ...             verticality.isConsonant,
            ...             verticality.beatStrength,
            ...             )
            ...
            Subequence:
                [0] <Verticality 0.5 {B3 B4 E4 G#3}>: True [0.125]
                [1] <Verticality 1.0 {A4 C#4 F#3 F#4}>: False [1.0]
                [1] <Verticality 2.0 {B3 B4 E4 G#3}>: True [0.25]
            Subequence:
                [2] <Verticality 6.0 {B4 E3 E4 G#4}>: True [0.25]
                [2] <Verticality 6.5 {B4 D4 E3 G#4}>: False [0.125]
                [2] <Verticality 7.0 {A2 A4 C#4 E4}>: True [0.5]
            Subequence:
                [2] <Verticality 8.0 {C#4 C#5 E#3 G#4}>: True [0.25]
                [3] <Verticality 9.0 {A4 C#4 F#3 F#4}>: False [1.0]
                [3] <Verticality 9.5 {B2 B4 D4 G#4}>: False [0.125]
                [3] <Verticality 10.0 {C#3 C#4 E#4 G#4}>: True [0.25]
            Subequence:
                [3] <Verticality 10.0 {C#3 C#4 E#4 G#4}>: True [0.25]
                [3] <Verticality 10.5 {B3 C#3 E#4 G#4}>: False [0.125]
                [3] <Verticality 11.0 {A3 C#4 F#2 F#4}>: False [0.5]
                [3] <Verticality 12.0 {A4 C#4 F#3 F#4}>: False [0.25]
                [4] <Verticality 13.0 {B3 B4 F#4 G#3}>: False [1.0]
                [4] <Verticality 13.5 {B3 B4 F#3 F#4}>: False [0.125]
                [4] <Verticality 14.0 {B3 B4 E4 G#3}>: True [0.25]
            Subequence:
                [4] <Verticality 14.0 {B3 B4 E4 G#3}>: True [0.25]
                [4] <Verticality 14.5 {A3 B3 B4 E4}>: False [0.125]
                [4] <Verticality 15.0 {B3 D#4 F#4}>: True [0.5]
            Subequence:
                [4] <Verticality 15.0 {B3 D#4 F#4}>: True [0.5]
                [4] <Verticality 15.5 {A3 B2 D#4 F#4}>: False [0.125]
                [4] <Verticality 16.0 {C#3 C#4 E4 G#3}>: True [0.25]
            Subequence:
                [4] <Verticality 16.0 {C#3 C#4 E4 G#3}>: True [0.25]
                [5] <Verticality 17.0 {A4 C#4 F#3}>: False [1.0]
                [5] <Verticality 17.5 {A4 D4 F#3 F#4}>: True [0.125]
            Subequence:
                [5] <Verticality 17.5 {A4 D4 F#3 F#4}>: True [0.125]
                [5] <Verticality 18.0 {B4 C#4 E4 G#3}>: False [0.25]
                [5] <Verticality 18.5 {B3 B4 E4 G#3}>: True [0.125]
            Subequence:
                [6] <Verticality 23.0 {C#4 C#5 E#3 G#4}>: True [0.5]
                [6] <Verticality 24.0 {A4 C#4 F#3 F#4}>: False [0.25]
                [7] <Verticality 25.0 {B2 D4 F#4 G#4}>: False [1.0]
                [7] <Verticality 25.5 {C#3 C#4 E#4 G#4}>: True [0.125]
            Subequence:
                [7] <Verticality 25.5 {C#3 C#4 E#4 G#4}>: True [0.125]
                [7] <Verticality 26.0 {C#4 D3 F#4}>: False [0.25]
                [7] <Verticality 26.5 {B3 D3 F#3 F#4}>: True [0.125]
            Subequence:
                [7] <Verticality 27.0 {C#3 C#4 E#3 G#4}>: True [0.5]
                [8] <Verticality 29.0 {A#2 C#4 F#3 F#4}>: False [1.0]
                [8] <Verticality 29.5 {A#2 D4 F#3 F#4}>: False [0.125]
                [8] <Verticality 30.0 {A#2 C#4 E4 F#4}>: False [0.25]
                [8] <Verticality 31.0 {B2 C#4 E4 F#4}>: False [0.5]
                [8] <Verticality 32.0 {B3 C#3 D4 F#4}>: False [0.25]
                [8] <Verticality 32.5 {A#3 C#3 C#4 F#4}>: False [0.125]
                [9] <Verticality 33.0 {B3 D3 F#4}>: True [1.0]
            Subequence:
                [9] <Verticality 33.0 {B3 D3 F#4}>: True [1.0]
                [9] <Verticality 33.5 {B3 C#4 D3 F#4}>: False [0.125]
                [9] <Verticality 34.0 {B2 B3 D4 F#4}>: True [0.25]

        '''
        iterator = self.iterateVerticalities()
        startingVerticality = iterator.next()
        while not startingVerticality.isConsonant:
            startingVerticality = iterator.next()
        verticalityBuffer = [startingVerticality]
        for verticality in iterator:
            verticalityBuffer.append(verticality)
            if verticality.isConsonant:
                if 2 < len(verticalityBuffer):
                    yield tuple(verticalityBuffer)
                verticalityBuffer = [verticality]

    def iterateVerticalities(
        self,
        reverse=False,
        ):
        r'''
        Iterates all vertical moments in this offset-tree.

        ..  note:: The offset-tree can be mutated while its verticalities are
            iterated over. Each verticality holds a reference back to the
            offset-tree and will ask for the start-offset after (or before) its
            own start offset in order to determine the next verticality to
            yield. If you mutate the tree by adding or deleting timespans, the
            next verticality will reflect those changes.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> iterator = tree.iterateVerticalities()
            >>> for _ in range(10):
            ...     iterator.next()
            ...
            <Verticality 0.0 {A3 C#5 E4}>
            <Verticality 0.5 {B3 B4 E4 G#3}>
            <Verticality 1.0 {A4 C#4 F#3 F#4}>
            <Verticality 2.0 {B3 B4 E4 G#3}>
            <Verticality 3.0 {A3 C#5 E4}>
            <Verticality 4.0 {B3 E4 E5 G#3}>
            <Verticality 5.0 {A3 C#5 E4}>
            <Verticality 5.5 {A4 C#3 C#5 E4}>
            <Verticality 6.0 {B4 E3 E4 G#4}>
            <Verticality 6.5 {B4 D4 E3 G#4}>

        Verticalities can also be iterated in reverse:

            >>> iterator = tree.iterateVerticalities(reverse=True)
            >>> for _ in range(10):
            ...     iterator.next()
            ...
            <Verticality 35.0 {A#3 C#4 F#3 F#4}>
            <Verticality 34.5 {B2 B3 D4 E#4}>
            <Verticality 34.0 {B2 B3 D4 F#4}>
            <Verticality 33.5 {B3 C#4 D3 F#4}>
            <Verticality 33.0 {B3 D3 F#4}>
            <Verticality 32.5 {A#3 C#3 C#4 F#4}>
            <Verticality 32.0 {B3 C#3 D4 F#4}>
            <Verticality 31.0 {B2 C#4 E4 F#4}>
            <Verticality 30.0 {A#2 C#4 E4 F#4}>
            <Verticality 29.5 {A#2 D4 F#3 F#4}>

        '''
        if reverse:
            startOffset = self.latestStartOffset
            verticality = self.getVerticalityAt(startOffset)
            yield verticality
            verticality = verticality.previousVerticality
            while verticality is not None:
                yield verticality
                verticality = verticality.previousVerticality
        else:
            startOffset = self.earliestStartOffset
            verticality = self.getVerticalityAt(startOffset)
            yield verticality
            verticality = verticality.nextVerticality
            while verticality is not None:
                yield verticality
                verticality = verticality.nextVerticality

    def iterateVerticalitiesNwise(
        self,
        n=3,
        reverse=False,
        ):
        r'''
        Iterates verticalities in groups of `n`.

        ..  note:: The offset-tree can be mutated while its verticalities are
            iterated over. Each verticality holds a reference back to the
            offset-tree and will ask for the start-offset after (or before) its
            own start offset in order to determine the next verticality to
            yield. If you mutate the tree by adding or deleting timespans, the
            next verticality will reflect those changes.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> iterator = tree.iterateVerticalitiesNwise(n=2)
            >>> for _ in range(4):
            ...     print iterator.next()
            ...
            (<Verticality 0.0 {A3 C#5 E4}>, <Verticality 0.5 {B3 B4 E4 G#3}>)
            (<Verticality 0.5 {B3 B4 E4 G#3}>, <Verticality 1.0 {A4 C#4 F#3 F#4}>)
            (<Verticality 1.0 {A4 C#4 F#3 F#4}>, <Verticality 2.0 {B3 B4 E4 G#3}>)
            (<Verticality 2.0 {B3 B4 E4 G#3}>, <Verticality 3.0 {A3 C#5 E4}>)

        Grouped verticalities can also be iterated in reverse:

        ::

            >>> iterator = tree.iterateVerticalitiesNwise(n=2, reverse=True)
            >>> for _ in range(4):
            ...     print iterator.next()
            ...
            (<Verticality 34.5 {B2 B3 D4 E#4}>, <Verticality 35.0 {A#3 C#4 F#3 F#4}>)
            (<Verticality 34.0 {B2 B3 D4 F#4}>, <Verticality 34.5 {B2 B3 D4 E#4}>)
            (<Verticality 33.5 {B3 C#4 D3 F#4}>, <Verticality 34.0 {B2 B3 D4 F#4}>)
            (<Verticality 33.0 {B3 D3 F#4}>, <Verticality 33.5 {B3 C#4 D3 F#4}>)

        '''
        n = int(n)
        assert 0 < n
        if reverse:
            for verticality in self.iterateVerticalities(reverse=True):
                verticalities = [verticality]
                while len(verticalities) < n:
                    nextVerticality = verticalities[-1].nextVerticality
                    if nextVerticality is None:
                        break
                    verticalities.append(nextVerticality)
                if len(verticalities) == n:
                    yield tuple(verticalities)
        else:
            for verticality in self.iterateVerticalities():
                verticalities = [verticality]
                while len(verticalities) < n:
                    previousVerticality = verticalities[-1].previousVerticality
                    if previousVerticality is None:
                        break
                    verticalities.append(previousVerticality)
                if len(verticalities) == n:
                    yield tuple(reversed(verticalities))

    def iterateVerticalitiesPairwise(self):
        #for verticality in self.iterateVerticalities():
        #    previousVerticality = verticality.previousVerticality
        #    if previousVerticality is not None:
        #        yield (previousVerticality, verticality)
        return self.iterateVerticaltiesNwise(n=2)

    @staticmethod
    def unwrapVerticalities(verticalities):
        r'''
        Unwraps a sequence of `Verticality` objects into a dictionary of
        `Part`:`Horizontality` key/value pairs.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> iterator = tree.iterateVerticalitiesNwise()
            >>> verticalities = iterator.next()
            >>> unwrapped = tree.unwrapVerticalities(verticalities)
            >>> for part in sorted(unwrapped,
            ...     key=lambda x: x.getInstrument().partName,
            ...     ):
            ...     print part
            ...     horizontality = unwrapped[part]
            ...     for timespan in horizontality:
            ...         print '\t', timespan
            ...
            <music21.stream.Part Alto>
                <Parentage 0.0:1.0 <music21.note.Note E>>
                <Parentage 1.0:2.0 <music21.note.Note F#>>
            <music21.stream.Part Bass>
                <Parentage 0.0:0.5 <music21.note.Note A>>
                <Parentage 0.5:1.0 <music21.note.Note G#>>
                <Parentage 1.0:2.0 <music21.note.Note F#>>
            <music21.stream.Part Soprano>
                <Parentage 0.0:0.5 <music21.note.Note C#>>
                <Parentage 0.5:1.0 <music21.note.Note B>>
                <Parentage 1.0:2.0 <music21.note.Note A>>
            <music21.stream.Part Tenor>
                <Parentage 0.0:0.5 <music21.note.Note A>>
                <Parentage 0.5:1.0 <music21.note.Note B>>
                <Parentage 1.0:2.0 <music21.note.Note C#>>

        '''
        unwrapped = {}
        for timespan in verticalities[0].overlapTimespans:
            if timespan.part not in unwrapped:
                unwrapped[timespan.part] = []
            unwrapped[timespan.part].append(timespan)
        for timespan in verticalities[0].startTimespans:
            if timespan.part not in unwrapped:
                unwrapped[timespan.part] = []
            unwrapped[timespan.part].append(timespan)
        for verticality in verticalities[1:]:
            for timespan in verticality.startTimespans:
                if timespan.part not in unwrapped:
                    unwrapped[timespan.part] = []
                unwrapped[timespan.part].append(timespan)
        for part, timespans in unwrapped.iteritems():
            unwrapped[part] = Horizontality(timespans=unwrapped[part])
        return unwrapped

    def remove(self, *timespans):
        r'''
        Removes `timespans` from this offset-tree.
        '''
        for timespan in timespans:
            assert hasattr(timespan, 'startOffset'), timespan
            assert hasattr(timespan, 'stopOffset'), timespan
            node = self._search(self._root, timespan.startOffset)
            if node is None:
                return
            if timespan in node.payload:
                node.payload.remove(timespan)
            if not node.payload:
                self._root = self._remove(self._root, timespan.startOffset)
        self._updateOffsets(self._root)

    def splitAt(self, *offsets):
        r'''
        Splits all timespans in this offset-tree at `offsets`, operating in
        place.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.findTimespansStartingAt(0.1)
            ()

        ::

            >>> for timespan in tree.findTimespansOverlapping(0.1):
            ...     timespan
            ...
            <Parentage 0.0:0.5 <music21.note.Note C#>>
            <Parentage 0.0:0.5 <music21.note.Note A>>
            <Parentage 0.0:0.5 <music21.note.Note A>>
            <Parentage 0.0:1.0 <music21.note.Note E>>

        ::

            >>> tree.splitAt(0.1)
            >>> for timespan in tree.findTimespansStartingAt(0.1):
            ...     timespan
            ...
            <Parentage 0.1:0.5 <music21.note.Note C#>>
            <Parentage 0.1:0.5 <music21.note.Note A>>
            <Parentage 0.1:0.5 <music21.note.Note A>>
            <Parentage 0.1:1.0 <music21.note.Note E>>

        ::

            >>> tree.findTimespansOverlapping(0.1)
            ()

        '''
        for offset in offsets:
            overlaps = self.findTimespansOverlapping(offset)
            if not overlaps:
                continue
            for overlap in overlaps:
                self.remove(overlap)
                shards = overlap.splitAt(offset)
                self.insert(*shards)

    def toChordifiedScore(self, templateScore=None):
        r'''
        Creates a score from the Parentage objects stored in this offset-tree.

        A "template" score may be used to provide measure and time-signature
        information.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> chordifiedScore = tree.toChordifiedScore(templateScore=score)
            >>> chordifiedScore.show('text')
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.chord.Chord A3 E4 C#5>
                {0.5} <music21.chord.Chord G#3 B3 E4 B4>
            {1.0} <music21.stream.Measure 1 offset=1.0>
                {0.0} <music21.chord.Chord F#3 C#4 F#4 A4>
                {1.0} <music21.chord.Chord G#3 B3 E4 B4>
                {2.0} <music21.chord.Chord A3 E4 C#5>
                {3.0} <music21.chord.Chord G#3 B3 E4 E5>
            {5.0} <music21.stream.Measure 2 offset=5.0>
                {0.0} <music21.chord.Chord A3 E4 C#5>
                {0.5} <music21.chord.Chord C#3 E4 A4 C#5>
                {1.0} <music21.chord.Chord E3 E4 G#4 B4>
                {1.5} <music21.chord.Chord E3 D4 G#4 B4>
                {2.0} <music21.chord.Chord A2 C#4 E4 A4>
                {3.0} <music21.chord.Chord E#3 C#4 G#4 C#5>
            {9.0} <music21.stream.Measure 3 offset=9.0>
                {0.0} <music21.chord.Chord F#3 C#4 F#4 A4>
                {0.5} <music21.chord.Chord B2 D4 G#4 B4>
                {1.0} <music21.chord.Chord C#3 C#4 E#4 G#4>
                {1.5} <music21.chord.Chord C#3 B3 E#4 G#4>
                {2.0} <music21.chord.Chord F#2 A3 C#4 F#4>
                {3.0} <music21.chord.Chord F#3 C#4 F#4 A4>
            {13.0} <music21.stream.Measure 4 offset=13.0>
                {0.0} <music21.chord.Chord G#3 B3 F#4 B4>
                {0.5} <music21.chord.Chord F#3 B3 F#4 B4>
                {1.0} <music21.chord.Chord G#3 B3 E4 B4>
                {1.5} <music21.chord.Chord A3 B3 E4 B4>
                {2.0} <music21.chord.Chord B3 D#4 F#4>
                {2.5} <music21.chord.Chord B2 A3 D#4 F#4>
                {3.0} <music21.chord.Chord C#3 G#3 C#4 E4>
            {17.0} <music21.stream.Measure 5 offset=17.0>
                {0.0} <music21.chord.Chord F#3 C#4 A4>
                {0.5} <music21.chord.Chord F#3 D4 F#4 A4>
                {1.0} <music21.chord.Chord G#3 C#4 E4 B4>
                {1.5} <music21.chord.Chord G#3 B3 E4 B4>
                {2.0} <music21.chord.Chord A3 E4 C#5>
                {3.0} <music21.chord.Chord A3 E4 A4 C#5>
            {21.0} <music21.stream.Measure 6 offset=21.0>
                {0.0} <music21.chord.Chord D4 F#4 A4>
                {1.0} <music21.chord.Chord B3 D4 F#4 B4>
                {2.0} <music21.chord.Chord E#3 C#4 G#4 C#5>
                {3.0} <music21.chord.Chord F#3 C#4 F#4 A4>
            {25.0} <music21.stream.Measure 7 offset=25.0>
                {0.0} <music21.chord.Chord B2 D4 F#4 G#4>
                {0.5} <music21.chord.Chord C#3 C#4 E#4 G#4>
                {1.0} <music21.chord.Chord D3 C#4 F#4>
                {1.5} <music21.chord.Chord D3 F#3 B3 F#4>
                {2.0} <music21.chord.Chord C#3 E#3 C#4 G#4>
            {29.0} <music21.stream.Measure 8 offset=29.0>
                {0.0} <music21.chord.Chord A#2 F#3 C#4 F#4>
                {0.5} <music21.chord.Chord A#2 F#3 D4 F#4>
                {1.0} <music21.chord.Chord A#2 C#4 E4 F#4>
                {2.0} <music21.chord.Chord B2 C#4 E4 F#4>
                {3.0} <music21.chord.Chord C#3 B3 D4 F#4>
                {3.5} <music21.chord.Chord C#3 A#3 C#4 F#4>
            {33.0} <music21.stream.Measure 9 offset=33.0>
                {0.0} <music21.chord.Chord D3 B3 F#4>
                {0.5} <music21.chord.Chord D3 B3 C#4 F#4>
                {1.0} <music21.chord.Chord B2 B3 D4 F#4>
                {1.5} <music21.chord.Chord B2 B3 D4 E#4>
                {2.0} <music21.chord.Chord F#3 A#3 C#4 F#4>

        '''
        if isinstance(templateScore, stream.Score):
            templateScore, templateOffsets = \
                self.extractMeasuresAndMeasureOffsets(templateScore)
            tree = self.copy()
            tree.splitAt(templateOffsets)
            measureIndex = 0
            allOffsets = tree.allOffsets + tuple(templateOffsets)
            allOffsets = sorted(set(allOffsets))
            for startOffset, stopOffset in zip(allOffsets, allOffsets[1:]):
                while templateOffsets[1] <= startOffset:
                    templateOffsets.pop(0)
                    measureIndex += 1
                verticality = self.getVerticalityAt(startOffset)
                quarterLength = stopOffset - startOffset
                if verticality.pitchSet:
                    element = chord.Chord(sorted(verticality.pitchSet))
                else:
                    element = note.Rest()
                element.duration.quarterLength = quarterLength
                templateScore[measureIndex].append(element)
            return templateScore
        else:
            allOffsets = self.allOffsets
            elements = []
            for startOffset, stopOffset in zip(allOffsets, allOffsets[1:]):
                verticality = self.getVerticalityAt(startOffset)
                quarterLength = stopOffset - startOffset
                if verticality.pitchSet:
                    element = chord.Chord(sorted(verticality.pitchSet))
                else:
                    element = note.Rest()
                element.duration.quarterLength = quarterLength
                elements.append(element)
            score = stream.Score()
            for element in elements:
                score.append(element)
            return score

    ### PUBLIC PROPERTIES ###

    @property
    def allOffsets(self):
        r'''
        Gets all unique offsets (both starting and stopping) of all timespans
        in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> for offset in tree.allOffsets[:10]:
            ...     offset
            ...
            0.0
            0.5
            1.0
            2.0
            3.0
            4.0
            5.0
            5.5
            6.0
            6.5

        '''
        def recurse(node):
            result = set()
            if node is not None:
                if node.leftChild is not None:
                    result.update(recurse(node.leftChild))
                result.add(node.startOffset)
                result.add(node.earliestStopOffset)
                result.add(node.latestStopOffset)
                if node.rightChild is not None:
                    result.update(recurse(node.rightChild))
            return result
        return tuple(sorted(recurse(self._root)))

    @property
    def allStartOffsets(self):
        r'''
        Gets all unique start offsets of all timespans in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> for offset in tree.allStartOffsets[:10]:
            ...     offset
            ...
            0.0
            0.5
            1.0
            2.0
            3.0
            4.0
            5.0
            5.5
            6.0
            6.5

        '''
        def recurse(node):
            result = []
            if node is not None:
                if node.leftChild is not None:
                    result.extend(recurse(node.leftChild))
                result.append(node.startOffset)
                if node.rightChild is not None:
                    result.extend(recurse(node.rightChild))
            return result
        return tuple(recurse(self._root))

    @property
    def allStopOffsets(self):
        r'''
        Gets all unique stop offsets of all timespans in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> for offset in tree.allStopOffsets[:10]:
            ...     offset
            ...
            0.5
            1.0
            2.0
            4.0
            5.5
            6.0
            7.0
            8.0
            9.5
            10.5

        '''
        def recurse(node):
            result = set()
            if node is not None:
                if node.leftChild is not None:
                    result.update(recurse(node.leftChild))
                result.add(node.earliestStopOffset)
                result.add(node.latestStopOffset)
                if node.rightChild is not None:
                    result.update(recurse(node.rightChild))
            return result
        return tuple(sorted(recurse(self._root)))

    @property
    def earliestStartOffset(self):
        r'''
        Gets the earlies start offset in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.earliestStartOffset
            0.0

        '''
        def recurse(node):
            if node.leftChild is not None:
                return recurse(node.leftChild)
            return node.startOffset
        return recurse(self._root)

    @property
    def earliestStopOffset(self):
        r'''
        Gets the earliest stop offset in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.earliestStopOffset
            0.5

        '''
        return self._root.earliestStopOffset

    @property
    def latestStartOffset(self):
        r'''
        Gets the lateset start offset in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.latestStartOffset
            35.0

        '''
        def recurse(node):
            if node.rightChild is not None:
                return recurse(node._rightChild)
            return node.startOffset
        return recurse(self._root)

    @property
    def latestStopOffset(self):
        r'''
        Gets the latest stop offset in this offset-tree.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.latestStopOffset
            36.0

        '''
        return self._root.latestStopOffset


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testOffsetTree(self):

        class Timespan(object):
            def __init__(self, startOffset, stopOffset):
                if startOffset < stopOffset:
                    self.startOffset = startOffset
                    self.stopOffset = stopOffset
                else:
                    self.startOffset = stopOffset
                    self.stopOffset = startOffset

            def __eq__(self, expr):
                if type(self) is type(expr):
                    if self.startOffset == expr.startOffset:
                        if self.stopOffset == expr.stopOffset:
                            return True
                return False

            def __repr__(self):
                return '<{} {} {}>'.format(
                    type(self).__name__,
                    self.startOffset,
                    self.stopOffset,
                    )

        for attempt in range(100):
            starts = range(100)
            stops = range(100)
            random.shuffle(starts)
            random.shuffle(stops)
            timespans = [Timespan(start, stop)
                for start, stop in zip(starts, stops)
                ]
            tree = OffsetTree()

            for i, timespan in enumerate(timespans):
                tree.insert(timespan)
                current_timespans_in_list = list(sorted(timespans[:i + 1],
                    key=lambda x: (x.startOffset, x.stopOffset)))
                current_timespans_in_tree = [x for x in tree]
                assert current_timespans_in_tree == current_timespans_in_list, \
                    (attempt, current_timespans_in_tree, current_timespans_in_list)
                assert tree._root.earliestStopOffset == \
                    min(x.stopOffset for x in current_timespans_in_list)
                assert tree._root.latestStopOffset == \
                    max(x.stopOffset for x in current_timespans_in_list)

            random.shuffle(timespans)
            while timespans:
                timespan = timespans.pop()
                current_timespans_in_list = sorted(timespans,
                    key=lambda x: (x.startOffset, x.stopOffset))
                tree.remove(timespan)
                current_timespans_in_tree = [x for x in tree]
                assert current_timespans_in_tree == current_timespans_in_list, \
                    (attempt, current_timespans_in_tree, current_timespans_in_list)
                if tree._root is not None:
                    assert tree._root.earliestStopOffset == \
                        min(x.stopOffset for x in current_timespans_in_list)
                    assert tree._root.latestStopOffset == \
                        max(x.stopOffset for x in current_timespans_in_list)


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
