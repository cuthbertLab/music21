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
from music21 import common
from music21 import chord
from music21 import note
from music21.timespans import spans
from music21.timespans import trees

def listOfTimespanTreesByClass(inputStream,
                               currentParentage=None,
                               initialOffset=0,
                               flatten=False,
                               classLists=None):
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
        
        if element.isStream:
            localParentage = currentParentage + (element,)
            containedTimespanTrees = listOfTimespanTreesByClass(element,
                                                                currentParentage=localParentage,
                                                                initialOffset=offset,
                                                                flatten=flatten,
                                                                classLists=classLists)
            for outputTimespanCollection, subTimespanCollection in zip(
                                    outputCollections, containedTimespanTrees):
                if flatten is not False: # True or semiFlat
                    outputTimespanCollection.insert(subTimespanCollection[:])
                else:
                    outputTimespanCollection.insert(subTimespanCollection)
            wasStream = True
            
        if not wasStream or flatten == 'semiFlat':
            parentOffset = initialOffset
            parentEndTime = initialOffset + lastParentage.duration.quarterLength
            endTime = offset + element.duration.quarterLength
            
            for classBasedTimespanCollection, classList in zip(outputCollections, classLists):
                if classList and not element.isClassOrSubclass(classList):
                    continue
                elementTimespan = spans.ElementTimespan(element=element,
                                                        parentage=tuple(reversed(currentParentage)),
                                                        parentOffset=parentOffset,
                                                        parentEndTime=parentEndTime,
                                                        offset=offset,
                                                        endTime=endTime)
                classBasedTimespanCollection.insert(elementTimespan)

    return outputCollections


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
    <ElementTimespan (0.0 to 0.5) <music21.note.Note C#>>
    <ElementTimespan (0.0 to 1.0) <music21.note.Note E>>
    <ElementTimespan (0.0 to 0.5) <music21.note.Note A>>
    <ElementTimespan (0.0 to 0.5) <music21.note.Note A>>
    <ElementTimespan (0.5 to 1.0) <music21.note.Note B>>

    >>> tree = timespans.fromStream.convert(score, flatten=False, classList=())

    Each of these has 11 elements -- mainly the Measures

    >>> for x in tree:
    ...     x
    ...
    <ElementTimespan (0.0 to 0.0) <music21.metadata.Metadata object at 0x...>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Soprano>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Alto>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Tenor>>
    <TimespanTree {11} (0.0 to 36.0) <music21.stream.Part Bass>>
    <ElementTimespan (0.0 to 0.0) <music21.layout.StaffGroup ...>>

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
                                        initialOffset=0.0, 
                                        flatten=flatten, 
                                        classLists=classLists)
    return listOfTimespanTrees[0]



if __name__ == '__main__':
    import music21
    music21.mainTest()