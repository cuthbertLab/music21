# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespans/fromStream.py
# Purpose:      Tools for creating timespans from Streams
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-16 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for creating timespans (fast, manipulatable objects) from Streams
'''
import unittest

from music21.base import Music21Object
from music21 import common
from music21.tree import spans
from music21.tree import timespanTree
from music21.tree import trees

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
    
    >>> classLists = ['Note', ('Clef', 'TimeSignature')]
    >>> treeList = tree.fromStream.listOfTreesByClass(score, useTimespans=True,
    ...                                            classLists=classLists, flatten=True)
    >>> treeList
    [<TimespanTree {12} (0.0 to 8.0) <music21.stream.Score ...>>, 
     <TimespanTree {4} (0.0 to 0.0) <music21.stream.Score ...>>]
    '''
    if currentParentage is None:
        currentParentage = (inputStream,)
        ## fix non-tuple classLists -- first call only...
        if classLists:
            for i, cl in enumerate(classLists):
                if not common.isIterable(cl):
                    classLists[i] = (cl,)

            
    lastParentage = currentParentage[-1]
    
    if useTimespans:
        treeClass = timespanTree.TimespanTree
    else:
        treeClass = trees.OffsetTree
    
    if classLists is None or len(classLists) == 0:
        outputTrees = [treeClass(source=lastParentage)]
        classLists = []
    else:
        outputTrees = [treeClass(source=lastParentage) for _ in classLists]
    # do this to avoid munging activeSites
    inputStreamElements = inputStream._elements[:] + inputStream._endElements
    for element in inputStreamElements:
        offset = lastParentage.elementOffset(element) + initialOffset
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
                    outputTree.insert(subTree.lowestPosition(), subTree)
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


def asTree(inputStream, flatten=False, classList=None, useTimespans=False, groupOffsets=False):
    '''
    Converts a Stream and constructs an :class:`~music21.tree.trees.ElementTree` based on this.
    
    Use Stream.asTree() generally since that caches the ElementTree.

    >>> score = tree.makeExampleScore()
    >>> elementTree = tree.fromStream.asTree(score)
    >>> elementTree
    <ElementTree {2} (0.0 <0.-20...> to 8.0) <music21.stream.Score exampleScore>>
    >>> for x in elementTree.iterNodes():
    ...     x
    <ElementNode: Start:0.0 <0.-20...> Indices:(l:0 *0* r:2) Payload:<music21.stream.Part ...>>
    <ElementNode: Start:0.0 <0.-20...> Indices:(l:1 *1* r:2) Payload:<music21.stream.Part ...>>
    
    >>> etFlat = tree.fromStream.asTree(score, flatten=True)
    >>> etFlat
    <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>

    The elementTree's classSortOrder has changed to -25 to match the lowest positioned element
    in the score, which is an Instrument object (classSortOrder=-25)

    >>> for x in etFlat.iterNodes():
    ...     x
    <ElementNode: Start:0.0 <0.-25...> Indices:(l:0 *0* r:2) 
        Payload:<music21.instrument.Instrument PartA: : >>
    <ElementNode: Start:0.0 <0.-25...> Indices:(l:1 *1* r:2) 
        Payload:<music21.instrument.Instrument PartB: : >>
    <ElementNode: Start:0.0 <0.0...> Indices:(l:0 *2* r:4) Payload:<music21.clef.BassClef>>
    <ElementNode: Start:0.0 <0.0...> Indices:(l:3 *3* r:4) Payload:<music21.clef.BassClef>>
    ...
    <ElementNode: Start:0.0 <0.20...> Indices:(l:5 *6* r:8) Payload:<music21.note.Note C>>
    <ElementNode: Start:0.0 <0.20...> Indices:(l:7 *7* r:8) Payload:<music21.note.Note C#>>
    <ElementNode: Start:1.0 <0.20...> Indices:(l:0 *8* r:20) Payload:<music21.note.Note D>>
    ...
    <ElementNode: Start:7.0 <0.20...> Indices:(l:15 *17* r:20) Payload:<music21.note.Note C>>
    <ElementNode: Start:End <0.-5...> Indices:(l:18 *18* r:20) 
        Payload:<music21.bar.Barline style=final>>
    <ElementNode: Start:End <0.-5...> Indices:(l:19 *19* r:20) 
        Payload:<music21.bar.Barline style=final>>
    
    >>> etFlat.getPositionAfter(0.5)
    SortTuple(atEnd=0, offset=1.0, priority=0, classSortOrder=20, isNotGrace=1, insertIndex=...)
    
    >>> etFlatNotes = tree.fromStream.asTree(score, flatten=True, classList=[note.Note])
    >>> etFlatNotes
    <ElementTree {12} (0.0 <0.20...> to 8.0) <music21.stream.Score exampleScore>>
    
    '''
    def recurseGetTreeByClass(inputStream,
                       currentParentage,
                       initialOffset,
                       outputTree=None):
        lastParentage = currentParentage[-1]
        
        if outputTree is None:
            outputTree = treeClass(source=lastParentage)

        # do this to avoid munging activeSites
        inputStreamElements = inputStream._elements[:] + inputStream._endElements
        parentEndTime = initialOffset + lastParentage.duration.quarterLength            
            
            
        for element in inputStreamElements:
            flatOffset = common.opFrac(lastParentage.elementOffset(element) + initialOffset)
            
            if element.isStream and flatten is not False: # True or "semiFlat"
                localParentage = currentParentage + (element,)
                recurseGetTreeByClass(element, # put the elements into the current tree...
                                      currentParentage=localParentage,
                                      initialOffset=flatOffset,
                                      outputTree=outputTree)
                if flatten != 'semiFlat':
                    continue  # do not insert the stream itself unless we are doing semiflat
                
            if classList and not element.isClassOrSubclass(classList):
                continue

            endTime = flatOffset + element.duration.quarterLength            
            
            if useTimespans:
                pitchedTimespan = spans.PitchedTimespan(element=element,
                                                    parentage=tuple(reversed(currentParentage)),
                                                    parentOffset=initialOffset,
                                                    parentEndTime=parentEndTime,
                                                    offset=flatOffset,
                                                    endTime=endTime)
                outputTree.insert(pitchedTimespan)
            elif groupOffsets is False:
                # for sortTuples
                position = element.sortTuple(lastParentage)
                flatPosition = position.modify(offset=flatOffset) 
                outputTree.insert(flatPosition, element)                    
            else:
                outputTree.insert(flatOffset, element)
    
        return outputTree


    # first time through...
    if useTimespans:
        treeClass = timespanTree.TimespanTree
    elif groupOffsets is False:
        treeClass = trees.ElementTree
    else:
        treeClass = trees.OffsetTree

    # check to see if we can shortcut and make a Tree very fast from a sorted list.
    if (inputStream.isSorted
            and groupOffsets is False  # currently we can't populate for an OffsetTree*
            and (inputStream.isFlat or flatten is False)):
        outputTree = treeClass(source=inputStream)
        inputStreamElements = inputStream._elements[:] + inputStream._endElements
        # Can use tree.populateFromSortedList and speed up by an order of magnitude
        if classList is None:
            elementTupleList = [(e.sortTuple(inputStream), e) for e in inputStreamElements]
        else:
            elementTupleList = [(e.sortTuple(inputStream), e) for e in inputStreamElements 
                                    if e.isClassOrSubclass(classList)]
        outputTree.populateFromSortedList(elementTupleList)
        return outputTree
        # * to make this work for an OffsetTree, we'd need to use .groupElementsByOffset
        #   first to make it so that the midpoint of the list is also the rootnode, etc.  
        
    else:    
        return recurseGetTreeByClass(inputStream,
                                     currentParentage=(inputStream,),
                                     initialOffset=0.0)  
    
def asTimespans(inputStream, flatten, classList):
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
    <PitchedTimespan (0.0 to 0.0) <music21.metadata.Metadata object at 0x...>>
    <PitchedTimespan (0.0 to 0.0) <music21.layout.StaffGroup ...>>
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
    if classList is None:
        classList = Music21Object
    classLists = [classList]
    listOfTimespanTrees = listOfTreesByClass(inputStream, 
                                        initialOffset=0.0, 
                                        flatten=flatten, 
                                        classLists=classLists,
                                        useTimespans=True)
    return listOfTimespanTrees[0]


#---------------------
class Test(unittest.TestCase):
    
    def testFastPopulate(self):
        '''
        tests that the isSorted speed up trick ends up producing identical results.
        '''
        from music21 import corpus
        sf = corpus.parse('bwv66.6').flat
        sfTree = sf.asTree()
        #print(sfTree)

        sf.isSorted = False
        sf._cache = {}
        sfTreeSlow = sf.asTree()
        for i in range(len(sf)):
            fasti = sfTree[i]
            slowi = sfTreeSlow[i]
            self.assertIs(fasti, slowi)

#     def xtestExampleScoreAsTimespans(self):
#         from music21 import tree
#         score = tree.makeExampleScore()
#         treeList = tree.fromStream.listOfTreesByClass(score, useTimespans=True)
#         tl0 = treeList[0]

        
#---------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test) #, runTest='testExampleScoreAsTimespans')
