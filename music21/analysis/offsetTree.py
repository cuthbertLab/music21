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
        '_parentage',
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
        assert len(parentage)
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

    def new(
        self,
        startOffset=None,
        stopOffset=None,
        ):
        startOffset = startOffset or self.startOffset
        stopOffset = stopOffset or self.stopOffset
        return type(self)(
            self.element,
            self.parentage,
            startOffset=startOffset,
            stopOffset=stopOffset,
            )

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
        for x in self.parentage:
            if not isinstance(x, stream.Part):
                continue
            for y in x:
                if isinstance(y, instrument.Instrument):
                    return y.partName
        return None

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
                >>> for verticality in tree.iterateVerticalities():
                ...     print verticality, verticality.isConsonant
                ...
                <Verticality 0.0 {A3 C#5 E4}> True
                <Verticality 0.5 {B3 B4 E4 G#3}> True
                <Verticality 1.0 {A4 C#4 F#3 F#4}> True
                <Verticality 2.0 {B3 B4 E4 G#3}> True
                <Verticality 3.0 {A3 C#5 E4}> True
                <Verticality 4.0 {B3 E4 E5 G#3}> True
                <Verticality 5.0 {A3 C#5 E4}> True
                <Verticality 5.5 {A4 C#3 C#5 E4}> True
                <Verticality 6.0 {B4 E3 E4 G#4}> True
                <Verticality 6.5 {B4 D4 E3 G#4}> True
                <Verticality 7.0 {A2 A4 C#4 E4}> True
                <Verticality 8.0 {C#4 C#5 E#3 G#4}> True
                <Verticality 9.0 {A4 C#4 F#3 F#4}> True
                <Verticality 9.5 {B2 B4 D4 G#4}> True
                <Verticality 10.0 {C#3 C#4 E#4 G#4}> True
                <Verticality 10.5 {B3 C#3 E#4 G#4}> True
                <Verticality 11.0 {A3 C#4 F#2 F#4}> True
                <Verticality 12.0 {A4 C#4 F#3 F#4}> True
                <Verticality 13.0 {B3 B4 F#4 G#3}> False
                <Verticality 13.5 {B3 B4 F#3 F#4}> False
                <Verticality 14.0 {B3 B4 E4 G#3}> True
                <Verticality 14.5 {A3 B3 B4 E4}> False
                <Verticality 15.0 {B3 D#4 F#4}> True
                <Verticality 15.5 {A3 B2 D#4 F#4}> True
                <Verticality 16.0 {C#3 C#4 E4 G#3}> True
                <Verticality 17.0 {A4 C#4 F#3}> True
                <Verticality 17.5 {A4 D4 F#3 F#4}> True
                <Verticality 18.0 {B4 C#4 E4 G#3}> True
                <Verticality 18.5 {B3 B4 E4 G#3}> True
                <Verticality 19.0 {A3 C#5 E4}> True
                <Verticality 20.0 {A3 A4 C#5 E4}> True
                <Verticality 21.0 {A4 D4 F#4}> True
                <Verticality 22.0 {B3 B4 D4 F#4}> True
                <Verticality 23.0 {C#4 C#5 E#3 G#4}> True
                <Verticality 24.0 {A4 C#4 F#3 F#4}> True
                <Verticality 25.0 {B2 D4 F#4 G#4}> True
                <Verticality 25.5 {C#3 C#4 E#4 G#4}> True
                <Verticality 26.0 {C#4 D3 F#4}> False
                <Verticality 26.5 {B3 D3 F#3 F#4}> True
                <Verticality 27.0 {C#3 C#4 E#3 G#4}> True
                <Verticality 29.0 {A#2 C#4 F#3 F#4}> True
                <Verticality 29.5 {A#2 D4 F#3 F#4}> True
                <Verticality 30.0 {A#2 C#4 E4 F#4}> True
                <Verticality 31.0 {B2 C#4 E4 F#4}> False
                <Verticality 32.0 {B3 C#3 D4 F#4}> False
                <Verticality 32.5 {A#3 C#3 C#4 F#4}> True
                <Verticality 33.0 {B3 D3 F#4}> True
                <Verticality 33.5 {B3 C#4 D3 F#4}> False
                <Verticality 34.0 {B2 B3 D4 F#4}> True
                <Verticality 34.5 {B2 B3 D4 E#4}> False
                <Verticality 35.0 {A#3 C#4 F#3 F#4}> True

        '''
        newChord = chord.Chord(sorted(self.pitchSet))
        if newChord.isTriad():
            return True
        elif newChord.isSeventh():
            return True
        elif newChord.isConsonant():
            return True
        return False

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
    An offset tree.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_root'
        )

    class OffsetTreeNode(object):
        r'''
        A node in an offset tree.

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

    def __init__(self):
        self._root = None

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

    def insert(self, *timespans):
        for timespan in timespans:
            assert hasattr(timespan, 'startOffset')
            assert hasattr(timespan, 'stopOffset')
            self._root = self._insert(self._root, timespan.startOffset)
            node = self._search(self._root, timespan.startOffset)
            node.payload.append(timespan)
            node.payload.sort(key=lambda x: x.stopOffset)
        self._updateOffsets(self._root)

    def remove(self, *timespans):
        for timespan in timespans:
            assert hasattr(timespan, 'startOffset')
            assert hasattr(timespan, 'stopOffset')
            node = self._search(self._root, timespan.startOffset)
            if node is None:
                return
            if timespan in node.payload:
                node.payload.remove(timespan)
            if not node.payload:
                self._root = self._remove(self._root, timespan.startOffset)
        self._updateOffsets(self._root)

    def findTimespansStartingAt(self, offset):
        results = []
        node = self._search(self._root, offset)
        if node is not None:
            results.extend(node.payload)
        return tuple(results)

    def findTimespansStoppingAt(self, offset):
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
        def recurse(node, offset, indent=0):
            result = []
            #indent_string = '\t' * indent
            #print '{}SEARCHING: {}'.format(indent_string, node)
            if node is not None:
                if node.startOffset < offset < node.latestStopOffset:
                    #print '{}\tSTART < OFFSET < LATEST STOP'.format(
                    #    indent_string)
                    result.extend(recurse(node.leftChild, offset, indent + 1))
                    for timespan in node.payload:
                        if offset < timespan.stopOffset:
                            result.append(timespan)
                            #print '{}\t\tADDING: {}'.format(
                            #    indent_string, timespan)
                        #else:
                            #print '{}\t\tSKIPPING: {}'.format(
                            #    indent_string, timespan)
                    result.extend(recurse(node.rightChild, offset, indent + 1))
                elif offset <= node.startOffset:
                    #print '{}\tOFFSET < START'.format(indent_string)
                    result.extend(recurse(node.leftChild, offset, indent + 1))
                #else:
                    #print '{}\tNOPE'.format(indent_string)
            return result
        results = recurse(self._root, offset)
        results.sort(key=lambda x: (x.startOffset, x.stopOffset))
        return tuple(results)

    @staticmethod
    def fromScore(inputScore):
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
        assert isinstance(inputScore, stream.Score)
        parentages = []
        initialParentage = (inputScore,)
        recurse(inputScore, parentages, currentParentage=initialParentage)
        tree = OffsetTree()
        tree.insert(*parentages)
        return tree

    def getStartOffsetAfter(self, offset):
        r'''
        Get start offset after `offset`.

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> tree.getStartOffsetAfter(0.5)
            1.0

        ::

            >>> tree.getStartOffsetAfter(35) is None
            True

        Return none if no succeeding offset exists.
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
        Get start offset before `offset`.

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
        Get verticality in offset tree at `offset`.

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

    def iterateConsonanceBoundedVerticalities(self):
        r'''
        Iterates consonant-bounded verticality subsequences in tree.

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
                [3] <Verticality 12.0 {A4 C#4 F#3 F#4}>: True [0.25]
                [4] <Verticality 13.0 {B3 B4 F#4 G#3}>: False [1.0]
                [4] <Verticality 13.5 {B3 B4 F#3 F#4}>: False [0.125]
                [4] <Verticality 14.0 {B3 B4 E4 G#3}>: True [0.25]
            Subequence:
                [4] <Verticality 14.0 {B3 B4 E4 G#3}>: True [0.25]
                [4] <Verticality 14.5 {A3 B3 B4 E4}>: False [0.125]
                [4] <Verticality 15.0 {B3 D#4 F#4}>: True [0.5]
            Subequence:
                [7] <Verticality 25.5 {C#3 C#4 E#4 G#4}>: True [0.125]
                [7] <Verticality 26.0 {C#4 D3 F#4}>: False [0.25]
                [7] <Verticality 26.5 {B3 D3 F#3 F#4}>: True [0.125]
            Subequence:
                [8] <Verticality 30.0 {A#2 C#4 E4 F#4}>: True [0.25]
                [8] <Verticality 31.0 {B2 C#4 E4 F#4}>: False [0.5]
                [8] <Verticality 32.0 {B3 C#3 D4 F#4}>: False [0.25]
                [8] <Verticality 32.5 {A#3 C#3 C#4 F#4}>: True [0.125]
            Subequence:
                [9] <Verticality 33.0 {B3 D3 F#4}>: True [1.0]
                [9] <Verticality 33.5 {B3 C#4 D3 F#4}>: False [0.125]
                [9] <Verticality 34.0 {B2 B3 D4 F#4}>: True [0.25]
            Subequence:
                [9] <Verticality 34.0 {B2 B3 D4 F#4}>: True [0.25]
                [9] <Verticality 34.5 {B2 B3 D4 E#4}>: False [0.125]
                [9] <Verticality 35.0 {A#3 C#4 F#3 F#4}>: True [0.5]

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

    def iterateVerticalities(self):
        r'''
        Iterate all vertical moments in the analyzed score:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> for x in tree.iterateVerticalities():
            ...     x
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
            <Verticality 7.0 {A2 A4 C#4 E4}>
            <Verticality 8.0 {C#4 C#5 E#3 G#4}>
            <Verticality 9.0 {A4 C#4 F#3 F#4}>
            <Verticality 9.5 {B2 B4 D4 G#4}>
            <Verticality 10.0 {C#3 C#4 E#4 G#4}>
            <Verticality 10.5 {B3 C#3 E#4 G#4}>
            <Verticality 11.0 {A3 C#4 F#2 F#4}>
            <Verticality 12.0 {A4 C#4 F#3 F#4}>
            <Verticality 13.0 {B3 B4 F#4 G#3}>
            <Verticality 13.5 {B3 B4 F#3 F#4}>
            <Verticality 14.0 {B3 B4 E4 G#3}>
            <Verticality 14.5 {A3 B3 B4 E4}>
            <Verticality 15.0 {B3 D#4 F#4}>
            <Verticality 15.5 {A3 B2 D#4 F#4}>
            <Verticality 16.0 {C#3 C#4 E4 G#3}>
            <Verticality 17.0 {A4 C#4 F#3}>
            <Verticality 17.5 {A4 D4 F#3 F#4}>
            <Verticality 18.0 {B4 C#4 E4 G#3}>
            <Verticality 18.5 {B3 B4 E4 G#3}>
            <Verticality 19.0 {A3 C#5 E4}>
            <Verticality 20.0 {A3 A4 C#5 E4}>
            <Verticality 21.0 {A4 D4 F#4}>
            <Verticality 22.0 {B3 B4 D4 F#4}>
            <Verticality 23.0 {C#4 C#5 E#3 G#4}>
            <Verticality 24.0 {A4 C#4 F#3 F#4}>
            <Verticality 25.0 {B2 D4 F#4 G#4}>
            <Verticality 25.5 {C#3 C#4 E#4 G#4}>
            <Verticality 26.0 {C#4 D3 F#4}>
            <Verticality 26.5 {B3 D3 F#3 F#4}>
            <Verticality 27.0 {C#3 C#4 E#3 G#4}>
            <Verticality 29.0 {A#2 C#4 F#3 F#4}>
            <Verticality 29.5 {A#2 D4 F#3 F#4}>
            <Verticality 30.0 {A#2 C#4 E4 F#4}>
            <Verticality 31.0 {B2 C#4 E4 F#4}>
            <Verticality 32.0 {B3 C#3 D4 F#4}>
            <Verticality 32.5 {A#3 C#3 C#4 F#4}>
            <Verticality 33.0 {B3 D3 F#4}>
            <Verticality 33.5 {B3 C#4 D3 F#4}>
            <Verticality 34.0 {B2 B3 D4 F#4}>
            <Verticality 34.5 {B2 B3 D4 E#4}>
            <Verticality 35.0 {A#3 C#4 F#3 F#4}>

        '''
        for startOffset in self.allStartOffsets:
            yield self.getVerticalityAt(startOffset)

    def iterateVerticalitiesNwise(self, n=3, unwrapParts=False):
        verticalityBuffer = []
        for verticality in self.iterateVerticalities():
            verticalityBuffer.append(verticality)
            if len(verticalityBuffer) < n:
                continue
            result = tuple(verticalityBuffer)
            if unwrapParts:
                unwrapped = {}
                for timespan in result[0].overlapTimespans:
                    if timespan.partName not in unwrapped:
                        unwrapped[timespan.partName] = []
                    unwrapped[timespan.partName].append(timespan)
                for timespan in result[0].startTimespans:
                    if timespan.partName not in unwrapped:
                        unwrapped[timespan.partName] = []
                    unwrapped[timespan.partName].append(timespan)
                for verticality in result[1:]:
                    for timespan in verticality.startTimespans:
                        if timespan.partName not in unwrapped:
                            unwrapped[timespan.partName] = []
                        unwrapped[timespan.partName].append(timespan)
                result = unwrapped
            yield result
            verticalityBuffer.pop(0)

    def toChordifiedScore(self):
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

    ### PUBLIC PROPERTIES ###

    @property
    def allOffsets(self):
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
