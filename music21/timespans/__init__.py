# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespans/__init__.py
# Purpose:      Tools for grouping notes and chords into a searchable tree
#               organized by start and stop offsets
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for grouping notes and chords into a searchable tree
organized by start and stop offsets.

This is a lower-level tool that for now at least normal music21
users won't need to worry about.
'''
__all__ = ['trees', 'spans', 'analysis', 'node', 'verticality']


import random
import unittest
import weakref

from music21 import chord
from music21 import common
from music21 import exceptions21
from music21 import note

from music21.ext import six

from music21.timespans import trees 
from music21.timespans import spans 
from music21.timespans import analysis 
from music21.timespans import node 
from music21.timespans import verticality 

from music21.exceptions21 import TimespanException
from music21 import environment
environLocal = environment.Environment("timespans")


#------------------------------------------------------------------------------

# TODO: Test with scores with Voices: cpebach/h186
# TODO: Make simple example score to use in all internals docstrings
def makeExampleScore():
    r'''
    Makes example score for use in stream-to-timespan conversion docs.

    >>> score = timespans.makeExampleScore()
    >>> score.show('text')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.instrument.Instrument PartA: : >
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note F>
        {4.0} <music21.stream.Measure 3 offset=4.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
        {6.0} <music21.stream.Measure 4 offset=6.0>
            {0.0} <music21.note.Note B>
            {1.0} <music21.note.Note C>
            {2.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.instrument.Instrument PartB: : >
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note G>
        {4.0} <music21.stream.Measure 3 offset=4.0>
            {0.0} <music21.note.Note E>
        {6.0} <music21.stream.Measure 4 offset=6.0>
            {0.0} <music21.note.Note D>
            {2.0} <music21.bar.Barline style=final>

    '''
    from music21 import converter
    from music21 import stream
    streamA = converter.parse('tinynotation: 2/4 C4 D E F G A B C')
    streamB = converter.parse('tinynotation: 2/4 C2 G E D')
    streamA.makeMeasures(inPlace=True)
    streamB.makeMeasures(inPlace=True)
    partA = stream.Part()
    for x in streamA:
        partA.append(x)
    instrumentA = partA.getInstrument()
    instrumentA.partId = 'PartA'
    partA.insert(0, instrumentA)
    partB = stream.Part()
    for x in streamB:
        partB.append(x)
    instrumentB = partB.getInstrument()
    instrumentB.partId = 'PartB'
    partB.insert(0, instrumentB)
    score = stream.Score()
    score.insert(0, partA)
    score.insert(0, partB)
    return score


def listOfTimespanTreesByClass(
    inputStream,
    currentParentage=None,
    initialOffset=0,
    flatten=False,
    classLists=None,
    ):
    r'''
    Recurses through `inputStream`, and constructs TimespanTrees for each
    encountered substream and ElementTimespans for each encountered non-stream
    element.

    `classLists` should be a sequence of valid inputs for `isClassOrSubclass()`. One
    TimespanTree will be constructed for each element in `classLists`, in
    a single optimized pass through the `inputStream`.

    This is used internally by `streamToTimespanTree`.
    
    
    >>> score = timespans.makeExampleScore()
    
    Get everything in the score
    
    >>> trees = timespans.listOfTimespanTreesByClass(score)
    >>> trees
    [<TimespanTree {2} (-inf to inf) <music21.stream.Score ...>>]    
    >>> for t in trees[0]:
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
    
    Now filter the Notes and the Clefs & TimeSignatures of the score (flattened) into a list of two timespans
    
    >>> classLists = ['Note', ('Clef', 'TimeSignature')]
    >>> trees = timespans.listOfTimespanTreesByClass(score, classLists=classLists, flatten=True)
    >>> trees
    [<TimespanTree {12} (0.0 to 8.0) <music21.stream.Score ...>>, 
     <TimespanTree {4} (0.0 to 0.0) <music21.stream.Score ...>>]
    '''
    if currentParentage is None:
        currentParentage = (inputStream,)
        ## fix non-tuple classLists -- first call only...
        if classLists:
            for i in range(len(classLists)):
                cl = classLists[i]
                if not common.isIterable(cl):
                    classLists[i] = (cl,)

            
    lastParentage = currentParentage[-1]
    if classLists is None or len(classLists) == 0:
        outputCollections = [trees.TimespanTree(source=lastParentage)]
        classLists = []
    else:
        outputCollections = [
            trees.TimespanTree(source=lastParentage) for _ in classLists
            ]
    # do this to avoid munging activeSites
    inputStreamElements = inputStream._elements[:] + inputStream._endElements
    for element in inputStreamElements:
        offset = element.getOffsetBySite(lastParentage) + initialOffset
        wasStream = False
        
        if element.isStream and \
                not element.isSpanner and \
                not element.isVariant:
            localParentage = currentParentage + (element,)
            containedTimespanTrees = listOfTimespanTreesByClass(
                element,
                currentParentage=localParentage,
                initialOffset=offset,
                flatten=flatten,
                classLists=classLists,
                )
            for outputTSC, subTSC in zip(outputCollections, containedTimespanTrees):
                if flatten is not False: # True or semiFlat
                    outputTSC.insert(subTSC[:])
                else:
                    outputTSC.insert(subTSC)
            wasStream = True
            
        if not wasStream or flatten == 'semiFlat':
            parentOffset = initialOffset
            parentEndTime  = initialOffset + lastParentage.duration.quarterLength
            endTime        = offset + element.duration.quarterLength
            
            for classBasedTSC, classList in zip(outputCollections, classLists):
                if classList and not element.isClassOrSubclass(classList):
                    continue
                elementTimespan = spans.ElementTimespan(
                    element=element,
                    parentage=tuple(reversed(currentParentage)),
                    parentOffset=parentOffset,
                    parentEndTime=parentEndTime,
                    offset=offset,
                    endTime=endTime,
                    )
                classBasedTSC.insert(elementTimespan)
    return outputCollections


def streamToTimespanTree(
    inputStream,
    flatten,
    classList,
    ):
    r'''
    Recurses through a score and constructs a
    :class:`~music21.timespans.TimespanTree`.  Use Stream.asTimespans() generally
    since that caches the TimespanTree.

    >>> score = corpus.parse('bwv66.6')
    >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
    >>> tree
    <TimespanTree {165} (0.0 to 36.0) <music21.stream.Score ...>>
    >>> for x in tree[:5]:
    ...     x
    ...
    <ElementTimespan (0.0 to 0.5) <music21.note.Note C#>>
    <ElementTimespan (0.0 to 1.0) <music21.note.Note E>>
    <ElementTimespan (0.0 to 0.5) <music21.note.Note A>>
    <ElementTimespan (0.0 to 0.5) <music21.note.Note A>>
    <ElementTimespan (0.5 to 1.0) <music21.note.Note B>>

    >>> tree = timespans.streamToTimespanTree(
    ...     score,
    ...     flatten=False,
    ...     classList=(),
    ...     )

    Each of these has 11 elements -- mainly the Measures

    TODO: Fix -- why is StaffGroup between Soprano and Alto?

    >>> for x in tree:
    ...     x
    ...
    <ElementTimespan (0.0 to 0.0) <music21.metadata.Metadata object at 0x...>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Soprano>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Alto>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Bass>>
    <ElementTimespan (0.0 to 0.0) <music21.layout.StaffGroup <music21.stream.Part Soprano><music21.stream.Part Alto><music21.stream.Part Tenor><music21.stream.Part Bass>>>

    >>> tenorElements = tree[3]
    >>> tenorElements
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>

    >>> tenorElements.source
    <music21.stream.Part Tenor>

    >>> tenorElements.source is score[3]
    True
    '''
    if classList is None:
        classList = (note.Note, chord.Chord)
    classLists = [classList]
    listOfTimespanTrees = listOfTimespanTreesByClass(inputStream, 
                                        initialOffset=0., 
                                        flatten=flatten, 
                                        classLists=classLists)
    return listOfTimespanTrees[0]


def timespansToChordifiedStream(timespans, templateStream=None):
    r'''
    Creates a score from the ElementTimespan objects stored in this
    offset-tree.

    A "template" score may be used to provide measure and time-signature
    information.

    >>> score = corpus.parse('bwv66.6')
    >>> tree = score.asTimespans()
    >>> chordifiedScore = timespans.timespansToChordifiedStream(
    ...     tree, templateStream=score)
    >>> chordifiedScore.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.KeySignature of 3 sharps, mode minor>
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
        {0.0} <music21.layout.SystemLayout>
        {0.0} <music21.chord.Chord F#3 C#4 F#4 A4>
        {0.5} <music21.chord.Chord B2 D4 G#4 B4>
        {1.0} <music21.chord.Chord C#3 C#4 E#4 G#4>
        {1.5} <music21.chord.Chord C#3 B3 E#4 G#4>
        {2.0} <music21.chord.Chord F#2 A3 C#4 F#4>
        {3.0} <music21.chord.Chord F#3 C#4 F#4 A4>
    ...
    '''
    from music21 import stream
    if not isinstance(timespans, trees.TimespanTree):
        raise trees.TimespanTreeException('Needs a TimespanTree to run')
    if isinstance(templateStream, stream.Stream):
        templateOffsets = sorted(templateStream.measureOffsetMap())
        templateOffsets.append(templateStream.duration.quarterLength)
        if hasattr(templateStream, 'parts') and templateStream.iter.parts:
            outputStream = templateStream.iter.parts[0].measureTemplate(
                fillWithRests=False)
        else:
            outputStream = templateStream.measureTemplate(
                fillWithRests=False)
        timespans = timespans.copy()
        timespans.splitAt(templateOffsets)
        measureIndex = 0
        allTimePoints = timespans.allTimePoints + tuple(templateOffsets)
        allTimePoints = sorted(set(allTimePoints))
        for offset, endTime in zip(allTimePoints, allTimePoints[1:]):
            while templateOffsets[1] <= offset:
                templateOffsets.pop(0)
                measureIndex += 1
            vert = timespans.getVerticalityAt(offset)
            quarterLength = endTime - offset
            if (quarterLength < 0):
                raise TimespanException("Something is wrong with the verticality %r its endTime %f is less than its offset %f" % 
                                         (vert, endTime, offset))
            element = vert.makeElement(quarterLength)
            outputStream[measureIndex].append(element)
        return outputStream
    else:
        allTimePoints = timespans.allTimePoints
        elements = []
        for offset, endTime in zip(allTimePoints, allTimePoints[1:]):
            vert = timespans.getVerticalityAt(offset)
            quarterLength = endTime - offset
            if (quarterLength < 0):
                raise TimespanException("Something is wrong with the verticality %r, its endTime %f is less than its offset %f" % (vert, endTime, offset))
            element = vert.makeElement(quarterLength)
            elements.append(element)
        outputStream = stream.Score()
        for element in elements:
            outputStream.append(element)
        return outputStream


def timespansToPartwiseStream(timespans, templateStream=None):
    '''
    todo docs
    '''
    from music21 import stream
    treeMapping = timespans.toPartwiseTimespanTrees()
    outputScore = stream.Score()
    for part in templateStream.parts:
        partwiseTimespans = treeMapping.get(part, None)
        if partwiseTimespans is None:
            continue
        outputPart = timespansToChordifiedStream(partwiseTimespans, part)
        outputScore.append(outputPart)
    return outputScore


#------------------------------------------------------------------------------


class Timespan(object):
    r'''
    A span of time, with a start offset and stop offset.

    Useful for demonstrating various properties of the timespan-collection class
    family.

    >>> timespan = timespans.Timespan(-1.5, 3.25)
    >>> print(timespan)
    <Timespan -1.5 3.25>
    '''

    def __init__(self, offset=float('-inf'), endTime=float('inf')):
        offset, endTime = sorted((offset, endTime))
        self.offset = offset
        self.endTime = endTime

    def __eq__(self, expr):
        if type(self) is type(expr):
            if self.offset == expr.offset:
                if self.endTime == expr.endTime:
                    return True
        return False

    def __repr__(self):
        return '<{} {} {}>'.format(
            type(self).__name__,
            self.offset,
            self.endTime,
            )




#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass
#------------------------------------------------------------------------------


_DOC_ORDER = ()


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
