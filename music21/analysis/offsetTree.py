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


class Verticality(object):

    ### CLASS VARIABLES ###

    __slots__ = (
        '_overlapTimespans',
        '_startTimespans',
        '_startOffset',
        '_stopTimespans',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        overlapTimespans=None,
        startTimespans=None,
        startOffset=None,
        stopTimespans=None,
        ):
        self._startOffset = startOffset
        assert isinstance(startTimespans, tuple)
        assert isinstance(stopTimespans, (tuple, type(None)))
        assert isinstance(overlapTimespans, (tuple, type(None)))
        self._startTimespans = startTimespans
        self._stopTimespans = stopTimespans
        self._overlapTimespans = overlapTimespans

    ### PUBLIC PROPERTIES ###

    @property
    def startOffset(self):
        return self._startOffset

    @property
    def startTimespans(self):
        return self._startTimespans

    @property
    def stopTimespans(self):
        return self._stopTimespans

    @property
    def overlapTimespans(self):
        return self._overlapParentage

    @property
    def beatStrength(self):
        return self.startTimespans[0].element.beatStrength

    @property
    def pitchClassSet(self):
        pitchClassSet = set()
        for parentage in self.startParentage:
            element = parentage.element
            pitchClassSet.update([x.name for x in element.pitches])
        return pitchClassSet


class OffsetTreeNode(object):
    r'''
    A node in an offset tree.
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


class OffsetTree(object):
    r'''
    An offset tree.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_root'
        )

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
            return OffsetTreeNode(startOffset)
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

    def iterateVerticalities(self):
        r'''
        Iterate all vertical moments in the analyzed score:

        ::

            >>> score = corpus.parse('bwv66.6')
            >>> tree = analysis.offsetTree.OffsetTree.fromScore(score)
            >>> result = [x for x in tree.iterateVerticalities()]

        '''
        for startOffset in self.allStartOffsets:
            startTimespans = self.findTimespansStartingAt(startOffset)
            stopTimespans = self.findTimespansStoppingAt(startOffset)
            overlapTimespans = self.findTimespansOverlapping(startOffset)
            verticality = Verticality(
                overlapTimespans=overlapTimespans,
                startTimespans=startTimespans,
                startOffset=startOffset,
                stopTimespans=stopTimespans,
                )
            yield verticality

    ### PUBLIC PROPERTIES ###

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
