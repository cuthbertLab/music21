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
import itertools
from music21 import chord
from music21 import note
from music21 import stream


class OffsetPair(collections.Sequence):

    ### CLASS VARIABLES ###

    __slots__ = (
        '_elements',
        '_startOffset',
        '_stopOffset',
        )

    ### INITIALIZER ###

    def __init__(self, startOffset, stopOffset, elements):
        self._startOffset = startOffset
        self._stopOffset = stopOffset
        self._elements = tuple(elements)

    ### SPECIAL METHODS ###

    def __getitem__(self, i):
        return self._elements[i]

    def __len__(self):
        return len(self._elements)

    def __repr__(self):
        return '<{} {}:{} [{}]>'.format(
            type(self).__name__,
            self.startOffset,
            self.stopOffset,
            len(self.elements),
            )

    ### PUBLIC PROPERTIES ###

    @property
    def elements(self):
        return self._elements

    @property
    def startOffset(self):
        return self._startOffset

    @property
    def stopOffset(self):
        return self._stopOffset


class OffsetNode(object):

    ### CLASS VARIABLES ###

    __slots__ = (
        '_centerOffset',
        '_leftNode',
        '_offsetPairs',
        '_rightNode',
        )

    ### INITIALIZER ###

    def __init__(self, centerOffset, offsetPairs, leftNode, rightNode):
        self._centerOffset = centerOffset
        self._offsetPairs = tuple(offsetPairs)
        self._leftNode = leftNode
        self._rightNode = rightNode

    ### SPECIAL METHODS ###

    def __iter__(self):
        if self.leftNode:
            for x in self.leftNode:
                yield x
        for x in self.offsetPairs:
            yield x
        if self.rightNode:
            for x in self.rightNode:
                yield x

    ### PUBLIC PROPERTIES ###

    @property
    def centerOffset(self):
        return self._centerOffset

    @property
    def leftNode(self):
        return self._leftNode

    @property
    def offsetPairs(self):
        return self._offsetPairs

    @property
    def rightNode(self):
        return self._rightNode


class OffsetTree(object):
    r'''
    A searchable offset tree for pitched elements in a score:

    ::

        >>> score = corpus.parse('bwv66.6')
        >>> tree = analysis.offsetTree.OffsetTree(score)
        >>> for x in tree.findByOffset(34.5):
        ...     x
        ...
        <music21.note.Note F#>
        <music21.note.Note D>
        <music21.note.Note B>
        <music21.note.Note B>
        <music21.note.Note E#>

    '''

    ### INITIALIZER ###

    def __init__(self, inputStream):
        assert isinstance(inputStream, stream.Score)
        offsetMap = self._buildOffsetMap(inputStream)
        offsetPairs = self._buildOffsetPairs(offsetMap)
        self._root = self._divideOffsetPairs(offsetPairs)

    ### SPECIAL METHODS ###

    def __iter__(self):
        for x in self._root:
            yield x

    ### PRIVATE METHODS ###

    def _buildOffsetMap(self, inputStream):
        offsetMap = {}

        def recurse(inputStream, offsetMap):
            for x in inputStream:
                if isinstance(x, stream.Measure):
                    for element in x:
                        if not isinstance(element, (
                            note.Note,
                            chord.Chord,
                            )):
                            continue
                        measureOffset = x.offset
                        elementOffset = element.offset
                        aggregateOffset = measureOffset + elementOffset
                        if aggregateOffset not in offsetMap:
                            offsetMap[aggregateOffset] = []
                        offsetMap[aggregateOffset].append(element)
                elif isinstance(x, stream.Stream):
                    recurse(x, offsetMap)

        recurse(inputStream, offsetMap)
        for offset, elementList in offsetMap.iteritems():
            offsetMap[offset] = \
                tuple(sorted(elementList, key=lambda x: x.quarterLength))
        return offsetMap

    def _buildOffsetPairs(self, offsetMap):
        offsetPairs = []
        for startOffset, elements in sorted(offsetMap.iteritems()):
            for quarterLength, elements in itertools.groupby(
                elements, lambda x: x.quarterLength):
                stopOffset = startOffset + quarterLength
                offsetPair = OffsetPair(
                    startOffset,
                    stopOffset,
                    tuple(elements),
                    )
                offsetPairs.append(offsetPair)
        return offsetPairs

    def _divideOffsetPairs(self, offsetPairs):
        if not offsetPairs:
            return None
        centerOffset = self._findCenterOffset(offsetPairs)
        centerOffsetPairs = []
        leftOffsetPairs = []
        rightOffsetPairs = []
        for offsetPair in offsetPairs:
            if offsetPair.stopOffset < centerOffset:
                leftOffsetPairs.append(offsetPair)
            elif centerOffset < offsetPair.startOffset:
                rightOffsetPairs.append(offsetPair)
            else:
                centerOffsetPairs.append(offsetPair)
        offsetNode = OffsetNode(
            centerOffset,
            centerOffsetPairs,
            self._divideOffsetPairs(leftOffsetPairs),
            self._divideOffsetPairs(rightOffsetPairs),
            )
        return offsetNode

    def _findCenterOffset(self, offsetPairs):
        sortedOffsetPairs = sorted(offsetPairs, key=lambda x: x.startOffset)
        length = len(sortedOffsetPairs)
        centerOffsetPair = sortedOffsetPairs[int(length / 2)]
        return centerOffsetPair.startOffset

    ### PUBLIC METHODS ###

    def findByOffset(self, offset):
        def recurse(node, offset):
            result = []
            for offsetPair in node.offsetPairs:
                if offsetPair.startOffset <= offset <= offsetPair.stopOffset:
                    result.append(offsetPair)
            if offset < node.centerOffset and node.leftNode:
                result.extend(recurse(node.leftNode, offset))
            if node.centerOffset < offset and node.rightNode:
                result.extend(recurse(node.rightNode, offset))
            return result
        offsetPairs = recurse(self._root, offset)
        result = []
        for offsetPair in offsetPairs:
            result.extend(offsetPair.elements)
        return result

    def findByOffsetRange(self, start, stop):
        pass
