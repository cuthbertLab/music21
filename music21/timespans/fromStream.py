# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespans/fromStream.py
# Purpose:      Tools for creating timespans from Streams
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for creating timespans (fast, manipulatable objects) from Streams
'''
from music21.base import Music21Object
from music21 import common
from music21.timespans import spans
from music21.timespans import trees


def listOfTreesByClass(inputStream,
                       currentParentage=None,
                       initialOffset=0.0,
                       flatten=False,
                       classLists=None,
                       useTimespans=False):
    r'''
    Recurses through `inputStream`, and constructs TimespanTrees for each
    encountered substream and PitchedTimespan for each encountered non-stream
    element.

    `classLists` should be a sequence of valid inputs for `isClassOrSubclass()`. One
    TimespanTree will be constructed for each element in `classLists`, in
    a single optimized pass through the `inputStream`.

    This is used internally by `streamToTimespanTree`.
    
    
    >>> score = timespans.makeExampleScore()
    
    Get everything in the score
    
    >>> treeList = timespans.fromStream.listOfTimespanTreesByClass(score)
    >>> treeList
    [<TimespanTree {2} (-inf to inf) <music21.stream.Score ...>>]    
    >>> for t in treeList[0]:
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
    (flattened) into a list of two timespans
    
    >>> classLists = ['Note', ('Clef', 'TimeSignature')]
    >>> treeList = timespans.fromStream.listOfTimespanTreesByClass(score, 
    ...                                            classLists=classLists, flatten=True)
    >>> treeList
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
    
    if useTimespans:
        treeClass = trees.TimespanTree
    else:
        treeClass = trees.ElementTree
    
    if classLists is None or len(classLists) == 0:
        outputTrees = [treeClass(origin=lastParentage)]
        classLists = []
    else:
        outputTrees = [treeClass(origin=lastParentage) for _ in classLists]
    # do this to avoid munging activeSites
    inputStreamElements = inputStream._elements[:] + inputStream._endElements
    for element in inputStreamElements:
        offset = element.getOffsetBySite(lastParentage) + initialOffset
        wasStream = False
        
        if element.isStream:
            localParentage = currentParentage + (element,)
            containedTrees = listOfTreesByClass(element,
                                                currentParentage=localParentage,
                                                initialOffset=offset,
                                                flatten=flatten,
                                                classLists=classLists,
                                                useTimespans=useTimespans)
            for outputTree, subTree in zip(outputTrees, containedTrees):
                if flatten is not False: # True or semiFlat
                    outputTree.insert(subTree[:])
                else:
                    outputTree.insert(subTree)
            wasStream = True
            
        if not wasStream or flatten == 'semiFlat':
            parentOffset = initialOffset
            parentEndTime = initialOffset + lastParentage.duration.quarterLength
            endTime = offset + element.duration.quarterLength
            
            for classBasedTree, classList in zip(outputTrees, classLists):
                if classList and not element.isClassOrSubclass(classList):
                    continue
                if useTimespans:
                    pitchedTimespan = spans.PitchedTimespan(element=element,
                                                        parentage=tuple(reversed(currentParentage)),
                                                        parentOffset=parentOffset,
                                                        parentEndTime=parentEndTime,
                                                        offset=offset,
                                                        endTime=endTime)
                    classBasedTree.insert(pitchedTimespan)
                else:
                    classBasedTree.insert(offset, element)

    return outputTrees


def listOfTimespanTreesByClass(inputStream,
                               currentParentage=None,
                               initialOffset=0,
                               flatten=False,
                               classLists=None):
    '''
    same as listOfTreesByClass but ensures that each element is wrapped in a PitchedTimespan
    
    To be removed... it's a temporary bridge gap...
    '''
    return listOfTreesByClass(inputStream,
                               currentParentage=currentParentage,
                               initialOffset=initialOffset,
                               flatten=flatten,
                               classLists=classLists,
                               useTimespans=True)

def convert(inputStream, flatten, classList):
    r'''
    Recurses through a score and constructs a
    :class:`~music21.timespans.TimespanTree`.  Use Stream.asTimespans() generally
    since that caches the TimespanTree.

    >>> score = corpus.parse('bwv66.6')
    >>> tree = timespans.fromStream.convert(score, flatten=True, classList=(note.Note, chord.Chord))
    >>> tree
    <TimespanTree {165} (0.0 to 36.0) <music21.stream.Score ...>>
    >>> for x in tree[:5]:
    ...     x
    ...
    <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>
    <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>
    <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
    <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
    <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>

    >>> tree = timespans.fromStream.convert(score, flatten=False, classList=())

    Each of these has 11 elements -- mainly the Measures

    >>> for x in tree:
    ...     x
    ...
    <PitchedTimespan (0.0 to 0.0) <music21.metadata.Metadata object at 0x...>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Soprano>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Alto>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Bass>>
    <PitchedTimespan (0.0 to 0.0) <music21.layout.StaffGroup ...>>

    >>> tenorElements = tree[3]
    >>> tenorElements
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>

    >>> tenorElements.origin
    <music21.stream.Part Tenor>

    >>> tenorElements.origin is score[3]
    True
    '''
    if classList is None:
        classList = Music21Object
    classLists = [classList]
    listOfTimespanTrees = listOfTimespanTreesByClass(inputStream, 
                                        initialOffset=0.0, 
                                        flatten=flatten, 
                                        classLists=classLists)
    return listOfTimespanTrees[0]

def flat(inputStream):
    '''
    Returns a timespan tree corresponding to a flat representation of the score.
    
    TODO: BUG: Why are these not flat offsets?
    
    >>> ex = timespans.makeExampleScore()
    >>> ts = timespans.fromStream.flat(ex)
    >>> ts
    <ElementTree {20} (0.0 to 2.0) <music21.stream.Score 0x104a94d68>>
    >>> ts[15], ts[15].offset
    (<music21.note.Note F>, 1.0)
    '''
    classLists = [Music21Object]
    listOfTimespanTrees = listOfTreesByClass(inputStream, 
                                        initialOffset=0.0, 
                                        flatten=True, 
                                        classLists=classLists)
    return listOfTimespanTrees[0]


if __name__ == '__main__':
    import music21
    music21.mainTest()