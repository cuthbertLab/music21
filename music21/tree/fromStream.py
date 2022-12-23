# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         timespans/fromStream.py
# Purpose:      Tools for creating timespans from Streams
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-22 Michael Scott Asato Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Tools for creating timespans (fast, manipulable objects) from Streams
'''
from __future__ import annotations

from collections.abc import Sequence
import typing as t
import unittest

from music21.base import Music21Object
from music21.common.types import M21ObjType, StreamType
from music21 import common
from music21 import note
from music21.tree import spans
from music21.tree import timespanTree
from music21.tree import trees

if t.TYPE_CHECKING:
    from music21 import stream


def listOfTreesByClass(
    inputStream: StreamType,
    *,
    classLists: Sequence[Sequence[type[M21ObjType]]] = (),
    currentParentage: tuple[stream.Stream, ...] | None = None,
    initialOffset: float = 0.0,
    flatten: bool | str = False,
    useTimespans: bool = False
) -> list[trees.OffsetTree | timespanTree.TimespanTree]:
    # noinspection PyShadowingNames
    r'''
    To be DEPRECATED in v8: this is no faster than calling streamToTimespanTree
    multiple times with different classLists.

    Recurses through `inputStream`, and constructs TimespanTrees for each
    encountered substream and PitchedTimespan for each encountered non-stream
    element.

    `classLists` should be a sequence of elements contained in `classSet`. One
    TimespanTree will be constructed for each element in `classLists`, in
    a single optimized pass through the `inputStream`.

    This is used internally by `streamToTimespanTree`.


    >>> score = tree.makeExampleScore()

    Get everything in the score

    >>> treeList = tree.fromStream.listOfTreesByClass(score, useTimespans=True)
    >>> treeList
    [<TimespanTree {2} (-inf to inf) <music21.stream.Score ...>>]
    >>> tl0 = treeList[0]
    >>> for t in tl0:
    ...     print(t)
    <TimespanTree {4} (-inf to inf) <music21.stream.Part ...>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 1 offset=0.0>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 2 offset=2.0>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 3 offset=4.0>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 4 offset=6.0>>
    <TimespanTree {4} (-inf to inf) <music21.stream.Part ...>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 1 offset=0.0>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 2 offset=2.0>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 3 offset=4.0>>
        <TimespanTree {0} (-inf to inf) <music21.stream.Measure 4 offset=6.0>>

    Now filter the Notes and the Clefs & TimeSignatures of the score
    (flattened) into a list of two TimespanTrees

    >>> classLists = ((note.Note,), (clef.Clef, meter.TimeSignature))
    >>> treeList = tree.fromStream.listOfTreesByClass(score, useTimespans=True,
    ...                                               classLists=classLists, flatten=True)
    >>> treeList
    [<TimespanTree {12} (0.0 to 8.0) <music21.stream.Score ...>>,
     <TimespanTree {4} (0.0 to 0.0) <music21.stream.Score ...>>]

    * Changed in v8: it is now a stickler that classLists must be sequences of sequences,
        such as tuples of tuples.
    '''
    from music21 import stream

    if currentParentage is None:
        currentParentage = (inputStream,)

    lastParentage = currentParentage[-1]

    treeClass: type[trees.OffsetTree]
    if useTimespans:
        treeClass = timespanTree.TimespanTree
    else:
        treeClass = trees.OffsetTree

    if not classLists:  # always get at least one
        outputTrees = [treeClass(source=lastParentage)]
    else:
        outputTrees = [treeClass(source=lastParentage) for _ in classLists]
    # do this to avoid munging activeSites
    inputStreamElements = inputStream._elements[:] + inputStream._endElements
    for element in inputStreamElements:
        offset = lastParentage.elementOffset(element) + initialOffset
        wasStream = False

        if element.isStream:
            element = t.cast('music21.stream.Stream', element)
            localParentage = currentParentage + (element,)
            containedTrees = listOfTreesByClass(element,
                                                currentParentage=localParentage,
                                                initialOffset=offset,
                                                flatten=flatten,
                                                classLists=classLists,
                                                useTimespans=useTimespans)
            for outputTree, subTree in zip(outputTrees, containedTrees):
                if flatten is not False:  # True or semiFlat
                    outputTree.insert(subTree[:])
                else:
                    outputTree.insert(subTree.lowestPosition(), subTree)
            wasStream = True

        if not wasStream or flatten == 'semiFlat':
            parentOffset = initialOffset
            parentEndTime = initialOffset + lastParentage.duration.quarterLength
            endTime = offset + element.duration.quarterLength

            for classBasedTree, classList in zip(outputTrees, classLists):
                if classList and element.classSet.isdisjoint(classList):
                    continue
                if useTimespans:
                    spanClass: type[spans.ElementTimespan]
                    if isinstance(element, (note.NotRest, stream.Stream)):
                        spanClass = spans.PitchedTimespan
                    else:
                        spanClass = spans.ElementTimespan
                    elementTimespan = spanClass(element=element,
                                                parentage=tuple(reversed(currentParentage)),
                                                parentOffset=parentOffset,
                                                parentEndTime=parentEndTime,
                                                offset=offset,
                                                endTime=endTime)
                    classBasedTree.insert(elementTimespan)
                else:
                    classBasedTree.insert(offset, element)

    return outputTrees


def asTree(
    inputStream: StreamType,
    *,
    flatten: t.Literal['semiFlat'] | bool = False,
    classList: Sequence[type] | None = None,
    useTimespans: bool = False,
    groupOffsets: bool = False
) -> trees.OffsetTree | trees.ElementTree | timespanTree.TimespanTree:
    '''
    Converts a Stream and constructs an :class:`~music21.tree.trees.ElementTree` based on this.

    Use Stream.asTree() generally since that caches the ElementTree.

    >>> score = tree.makeExampleScore()
    >>> elementTree = tree.fromStream.asTree(score)
    >>> elementTree
    <ElementTree {2} (0.0 <0.-20...> to 8.0) <music21.stream.Score exampleScore>>
    >>> for x in elementTree.iterNodes():
    ...     x
    <ElementNode: Start:0.0 <0.-20...> Indices:(l:0 *0* r:1) Payload:<music21.stream.Part ...>>
    <ElementNode: Start:0.0 <0.-20...> Indices:(l:0 *1* r:2) Payload:<music21.stream.Part ...>>

    >>> etFlat = tree.fromStream.asTree(score, flatten=True)
    >>> etFlat
    <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>

    The elementTree's classSortOrder has changed to -25 to match the lowest positioned element
    in the score, which is an Instrument object (classSortOrder=-25)

    >>> for x in etFlat.iterNodes():
    ...     x
    <ElementNode: Start:0.0 <0.-25...> Indices:(l:0 *0* r:2)
        Payload:<music21.instrument.Instrument 'PartA: : '>>
    <ElementNode: Start:0.0 <0.-25...> Indices:(l:1 *1* r:2)
        Payload:<music21.instrument.Instrument 'PartB: : '>>
    <ElementNode: Start:0.0 <0.0...> Indices:(l:0 *2* r:4) Payload:<music21.clef.BassClef>>
    <ElementNode: Start:0.0 <0.0...> Indices:(l:3 *3* r:4) Payload:<music21.clef.BassClef>>
    ...
    <ElementNode: Start:0.0 <0.20...> Indices:(l:5 *6* r:8) Payload:<music21.note.Note C>>
    <ElementNode: Start:0.0 <0.20...> Indices:(l:7 *7* r:8) Payload:<music21.note.Note C#>>
    <ElementNode: Start:1.0 <0.20...> Indices:(l:0 *8* r:20) Payload:<music21.note.Note D>>
    ...
    <ElementNode: Start:7.0 <0.20...> Indices:(l:15 *17* r:20) Payload:<music21.note.Note C>>
    <ElementNode: Start:End <0.-5...> Indices:(l:18 *18* r:20)
        Payload:<music21.bar.Barline type=final>>
    <ElementNode: Start:End <0.-5...> Indices:(l:19 *19* r:20)
        Payload:<music21.bar.Barline type=final>>

    >>> etFlat.getPositionAfter(0.5)
    SortTuple(atEnd=0, offset=1.0, priority=0, classSortOrder=20, isNotGrace=1, insertIndex=...)

    >>> etFlatNotes = tree.fromStream.asTree(score, flatten=True, classList=(note.Note,))
    >>> etFlatNotes
    <ElementTree {12} (0.0 <0.20...> to 8.0) <music21.stream.Score exampleScore>>

    '''
    def recurseGetTreeByClass(
            innerStream,
            currentParentage,
            initialOffset,
            inner_outputTree=None):
        lastParentage = currentParentage[-1]

        if inner_outputTree is None:
            inner_outputTree = treeClass(source=lastParentage)

        # do this to avoid munging activeSites
        innerStreamElements = innerStream._elements[:] + innerStream._endElements
        parentEndTime = initialOffset + lastParentage.duration.quarterLength

        for element in innerStreamElements:
            flatOffset = common.opFrac(lastParentage.elementOffset(element) + initialOffset)

            if element.isStream and flatten is not False:  # True or 'semiFlat'
                localParentage = currentParentage + (element,)
                recurseGetTreeByClass(element,  # put the elements into the current tree...
                                      currentParentage=localParentage,
                                      initialOffset=flatOffset,
                                      inner_outputTree=inner_outputTree)
                if flatten != 'semiFlat':
                    continue  # do not insert the stream itself unless we are doing semiflat

            if classList and element.classSet.isdisjoint(classList):
                continue

            endTime = flatOffset + element.duration.quarterLength

            if useTimespans:
                pitchedTimespan = spans.PitchedTimespan(
                    element=element,
                    parentage=tuple(reversed(currentParentage)),
                    parentOffset=initialOffset,
                    parentEndTime=parentEndTime,
                    offset=flatOffset,
                    endTime=endTime)
                inner_outputTree.insert(pitchedTimespan)
            elif groupOffsets is False:
                # for sortTuples
                position = element.sortTuple(lastParentage)
                flatPosition = position.modify(offset=flatOffset)
                inner_outputTree.insert(flatPosition, element)
            else:
                inner_outputTree.insert(flatOffset, element)

        return inner_outputTree

    # first time through...
    treeClass: type[trees.ElementTree]

    if useTimespans:
        treeClass = timespanTree.TimespanTree
    elif groupOffsets is False:
        treeClass = trees.ElementTree
    else:
        treeClass = trees.OffsetTree

    # this lets us use the much faster populateFromSortedList -- the one-time
    # sort in C is faster than the node implementation.
    if not inputStream.isSorted and inputStream.autoSort:
        inputStream.sort()

    # check to see if we can shortcut and make a Tree very fast from a sorted list.
    if (inputStream.isSorted
            and groupOffsets is False  # currently we can't populate for an OffsetTree*
            and (inputStream.isFlat or flatten is False)):
        outputTree: trees.OffsetTree | trees.ElementTree = treeClass(source=inputStream)
        return makeFastShallowTreeFromSortedStream(inputStream,
                                                   outputTree=outputTree,
                                                   classList=classList)
    else:
        return recurseGetTreeByClass(inputStream,
                                     currentParentage=(inputStream,),
                                     initialOffset=0.0)

def makeFastShallowTreeFromSortedStream(
    inputStream: stream.Stream,
    *,
    outputTree: trees.OffsetTree | trees.ElementTree,
    classList: Sequence[type] | None = None,
) -> trees.OffsetTree | trees.ElementTree:
    '''
    Use populateFromSortedList to quickly make a tree from a stream.

    This only works if the stream is flat (or we are not flattening) and
    sorts have already been run, and we are not making an OffsetTree.

    Returns the same outputTree that was put in, only with elements in it.
    '''
    inputStreamElements = inputStream._elements[:] + inputStream._endElements
    # Can use tree.populateFromSortedList and speed up by an order of magnitude
    if classList is None:
        elementTupleList = [(e.sortTuple(inputStream), e) for e in inputStreamElements]
    else:
        elementTupleList = [(e.sortTuple(inputStream), e) for e in inputStreamElements
                            if not e.classSet.isdisjoint(classList)]
    outputTree.populateFromSortedList(elementTupleList)
    if outputTree.rootNode is not None:
        outputTree.rootNode.updateEndTimes()
    return outputTree


def asTimespans(
    inputStream,
    *,
    flatten: str | bool = False,
    classList: Sequence[type[Music21Object]] | None = None
) -> timespanTree.TimespanTree:
    r'''
    Recurses through a score and constructs a
    :class:`~music21.tree.trees.TimespanTree`.  Use Stream.asTimespans() generally
    since that caches the TimespanTree.

    >>> score = corpus.parse('bwv66.6')
    >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
    ...                                         classList=(note.Note, chord.Chord))
    >>> scoreTree
    <TimespanTree {165} (0.0 to 36.0) <music21.stream.Score ...>>
    >>> for x in scoreTree[:5]:
    ...     x
    ...
    <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>
    <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
    <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
    <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>
    <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>

    >>> scoreTree = tree.fromStream.asTimespans(score, flatten=False, classList=())

    Each of these has 11 elements -- mainly the Measures

    >>> for x in scoreTree:
    ...     x
    ...
    <ElementTimespan (0.0 to 0.0) <music21.metadata.Metadata object at 0x...>>
    <ElementTimespan (0.0 to 0.0) <music21.layout.StaffGroup ...>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Soprano>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Alto>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Bass>>

    >>> tenorElements = scoreTree[4]
    >>> tenorElements
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>

    >>> tenorElements.source
    <music21.stream.Part Tenor>

    >>> tenorElements.source is score[3]
    True
    '''
    classLists: list[Sequence[type[Music21Object]]]
    if classList is None:
        classLists = [[Music21Object]]
    else:
        classLists = [classList]
    listOfTimespanTrees = listOfTreesByClass(inputStream,
                                             initialOffset=0.0,
                                             flatten=flatten,
                                             classLists=classLists,
                                             useTimespans=True)
    timespanTreeFirst = listOfTimespanTrees[0]
    if t.TYPE_CHECKING:
        assert isinstance(timespanTreeFirst, timespanTree.TimespanTree)
    return timespanTreeFirst


# --------------------
class Test(unittest.TestCase):

    def testFastPopulate(self):
        '''
        tests that the isSorted speed up trick ends up producing identical results.
        '''
        from music21 import corpus
        sf = corpus.parse('bwv66.6').flatten()
        sfTree = sf.asTree()
        # print(sfTree)

        sf.isSorted = False
        sf._cache = {}
        sfTreeSlow = sf.asTree()
        for i in range(len(sf)):
            fastI = sfTree[i]
            slowI = sfTreeSlow[i]
            self.assertIs(fastI, slowI)

    def testAutoSortExample(self):
        from music21.tree import makeExampleScore
        sc = makeExampleScore()
        sc.sort()
        scTree = asTree(sc)
        self.assertEqual(scTree.endTime, 8.0)
        # print(repr(scTree))


# --------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testAutoSortExample')
