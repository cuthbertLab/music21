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
import unittest
from music21 import chord
from music21 import instrument
from music21 import note
from music21 import stream


class Parentage(object):

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
        return self._element

    @property
    def measureNumber(self):
        return self.parentage[0].measureNumber

    @property
    def parentage(self):
        return self._parentage

    @property
    def partName(self):
        for x in self.parentage:
            if not isinstance(x, stream.Part):
                continue
            for y in x:
                if isinstance(y, instrument.Instrument):
                    return y.partName
        return None

    @property
    def startOffset(self):
        return self._startOffset

    @property
    def stopOffset(self):
        return self._stopOffset


class OffsetPair(collections.Sequence):

    ### CLASS VARIABLES ###

    __slots__ = (
        '_parentages',
        '_startOffset',
        '_stopOffset',
        )

    ### INITIALIZER ###

    def __init__(self, startOffset, stopOffset, parentages):
        self._startOffset = startOffset
        self._stopOffset = stopOffset
        self._parentages = tuple(parentages)

    ### SPECIAL METHODS ###

    def __getitem__(self, i):
        return self._parentages[i]

    def __len__(self):
        return len(self._parentages)

    def __repr__(self):
        return '<{} {}:{} [{}]>'.format(
            type(self).__name__,
            self.startOffset,
            self.stopOffset,
            len(self.parentages),
            )

    ### PUBLIC PROPERTIES ###

    @property
    def parentages(self):
        return self._parentages

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
        >>> for x in tree.findParentagesIntersectingOffset(34.5):
        ...     x.element, x.startOffset, x.stopOffset, x.partName
        ...
        (<music21.note.Note F#>, 34.0, 34.5, u'Soprano')
        (<music21.note.Note D>, 34.0, 35.0, u'Alto')
        (<music21.note.Note B>, 34.0, 35.0, u'Tenor')
        (<music21.note.Note B>, 34.0, 35.0, u'Bass')
        (<music21.note.Note E#>, 34.5, 35.0, u'Soprano')

    '''

    ### INITIALIZER ###

    def __init__(self, inputStream):
        assert isinstance(inputStream, stream.Score)
        offsetMap = self._buildOffsetMap(inputStream)
        offsetPairs = self._buildOffsetPairs(offsetMap)
        self._root = self._divideOffsetPairs(offsetPairs)

    ### SPECIAL METHODS ###

    def __getitem__(self, i):
        if isinstance(i, (int, float)):
            result = self.findParentagesStartingAtOffset(i)
            if result is not None:
                return result
            raise IndexError
        raise TypeError

    def __iter__(self):
        for x in self._root:
            yield x

    ### PRIVATE METHODS ###

    def _buildOffsetMap(self, inputStream):
        def recurse(inputStream, offsetMap, currentParentage):
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
                        if startOffset not in offsetMap:
                            offsetMap[startOffset] = []
                        parentage = Parentage(
                            element,
                            tuple(reversed(localParentage)),
                            startOffset=startOffset,
                            stopOffset=stopOffset,
                            )
                        offsetMap[startOffset].append(parentage)
                elif isinstance(x, stream.Stream):
                    localParentage = currentParentage + (x,)
                    recurse(x, offsetMap, localParentage)
        offsetMap = {}
        initialParentage = (inputStream,)
        recurse(inputStream, offsetMap, currentParentage=initialParentage)
        for offset, parentageList in offsetMap.iteritems():
            offsetMap[offset] = tuple(sorted(
                parentageList,
                key=lambda parentage: parentage.element.quarterLength,
                ))
        return offsetMap

    def _buildOffsetPairs(self, offsetMap):
        offsetPairs = []
        for startOffset, parentageList in sorted(offsetMap.iteritems()):
            for quarterLength, parentageList in itertools.groupby(
                parentageList,
                lambda parentage: parentage.element.quarterLength,
                ):
                stopOffset = startOffset + quarterLength
                offsetPair = OffsetPair(
                    startOffset,
                    stopOffset,
                    tuple(parentageList),
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

    def findParentagesStartingAtOffset(self, offset):
        r'''
        Find parentages starting at `offset`:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree(score)
            >>> for parentage in tree.findParentagesStartingAtOffset(0.5):
            ...     parentage.element
            ...
            <music21.note.Note B>
            <music21.note.Note B>
            <music21.note.Note G#>

        '''
        def recurse(node, offset):
            result = []
            for offsetPair in node.offsetPairs:
                if offsetPair.startOffset == offset:
                    result.append(offsetPair)
            if offset < node.centerOffset and node.leftNode:
                result.extend(recurse(node.leftNode, offset))
            if node.centerOffset < offset and node.rightNode:
                result.extend(recurse(node.rightNode, offset))
            return result
        offsetPairs = recurse(self._root, offset)
        result = []
        for offsetPair in offsetPairs:
            result.extend(offsetPair.parentages)
        return result

    def findParentagesStoppingAtOffset(self, offset):
        r'''
        Find parentages stopping at `offset`:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree(score)
            >>> for parentage in tree.findParentagesStoppingAtOffset(0.5):
            ...     parentage.element
            ...
            <music21.note.Note C#>
            <music21.note.Note A>
            <music21.note.Note A>

        '''
        def recurse(node, offset):
            result = []
            for offsetPair in node.offsetPairs:
                if offsetPair.stopOffset == offset:
                    result.append(offsetPair)
            if offset < node.centerOffset and node.leftNode:
                result.extend(recurse(node.leftNode, offset))
            if node.centerOffset < offset and node.rightNode:
                result.extend(recurse(node.rightNode, offset))
            return result
        offsetPairs = recurse(self._root, offset)
        result = []
        for offsetPair in offsetPairs:
            result.extend(offsetPair.parentages)
        return result

    def findParentagesOverlappingOffset(self, offset):
        r'''
        Find parentages overlapping `offset`:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree(score)
            >>> for parentage in tree.findParentagesOverlappingOffset(0.5):
            ...     parentage.element
            ...
            <music21.note.Note E>

        '''
        def recurse(node, offset):
            result = []
            for offsetPair in node.offsetPairs:
                if offsetPair.startOffset < offset < offsetPair.stopOffset:
                    result.append(offsetPair)
            if offset < node.centerOffset and node.leftNode:
                result.extend(recurse(node.leftNode, offset))
            if node.centerOffset < offset and node.rightNode:
                result.extend(recurse(node.rightNode, offset))
            return result
        offsetPairs = recurse(self._root, offset)
        result = []
        for offsetPair in offsetPairs:
            result.extend(offsetPair.parentages)
        return result

    def findParentagesIntersectingOffset(self, offset):
        r'''
        Find parentages intersecting `offset`:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree(score)
            >>> for parentage in tree.findParentagesIntersectingOffset(0.5):
            ...     parentage.element
            ...
            <music21.note.Note E>
            <music21.note.Note B>
            <music21.note.Note B>
            <music21.note.Note G#>
            <music21.note.Note C#>
            <music21.note.Note A>
            <music21.note.Note A>

        '''
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
            result.extend(offsetPair.parentages)
        return result

    def iterateVerticalities(self):
        r'''
        Iterate all vertical moments in the analyzed score:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree(score)
            >>> result = [x for x in tree.iterateVerticalities()]

        '''
        overlapParentages = set()
        startParentages = set()
        previousStartOffset = None
        for offsetPair in self:
            if offsetPair.startOffset != previousStartOffset:
                if previousStartOffset is not None:
                    yield previousStartOffset, startParentages, overlapParentages
                previousStartOffset = offsetPair.startOffset
                overlapParentages = set()
                startParentages = set()
            startParentages.update(offsetPair.parentages)
            overlapParentages.update(
                self.findParentagesOverlappingOffset(previousStartOffset))
        yield (
            previousStartOffset,
            tuple(startParentages),
            tuple(overlapParentages),
            )


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import music21
    music21.mainTest()
