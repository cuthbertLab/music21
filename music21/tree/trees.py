# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         tree/trees.py
# Purpose:      Subclasses of tree.core.AVLTree for different purposes
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-16 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for grouping elements, timespans, and especially
pitched elements into kinds of searchable tree organized by start and stop offsets
and other positions.
'''
from __future__ import division, print_function

import unittest
import weakref

from music21 import common
from music21 import exceptions21

from music21.sorting import SortTuple

from music21.tree import core
from music21.tree import node as nodeModule

from music21 import environment
environLocal = environment.Environment("tree.trees")

INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')

#------------------------------------------------------------------------------
class ElementTreeException(exceptions21.TreeException):
    pass

#------------------------------------------------------------------------------

class ElementTree(core.AVLTree):
    r'''
    A data structure for efficiently storing a score: flat or recursed or normal.
    
    This data structure has no connection to the XML ElementTree.
    
    This data structure stores ElementNodes: objects which implement both a
    `position` and `endTime` property. It provides fast lookups of such
    objects.
    
    >>> et = tree.trees.ElementTree()
    >>> et
    <ElementTree {0} (-inf to inf)>
    
    >>> s = stream.Stream()
    >>> for i in range(100):
    ...     n = note.Note()
    ...     n.duration.quarterLength = 2.0
    ...     s.insert(i * 2, n)

    >>> for n in s:
    ...     et.insert(n)
    >>> et
    <ElementTree {100} (0.0 <0.20...> to 200.0)>
    >>> et.rootNode
    <ElementNode: Start:126.0 <0.20...> Indices:(l:0 *63* r:100) Payload:<music21.note.Note C>>
    
    >>> n2 = s[-1]

    These operations are very fast...

    >>> et.index(n2, n2.sortTuple())
    99
    
    Get a position after a certain position:
    
    >>> st = s[40].sortTuple()
    >>> st
    SortTuple(atEnd=0, offset=80.0, priority=0, classSortOrder=20, isNotGrace=1, insertIndex=...)
    >>> st2 = et.getPositionAfter(st)
    >>> st2.shortRepr()
    '82.0 <0.20...>'
    >>> st2.offset
    82.0
    
    >>> st3 = et.getPositionAfter(5.0)
    >>> st3.offset
    6.0
    >>> et.getPositionAfter(4.0).offset
    6.0
    '''
    ### CLASS VARIABLES ###
    nodeClass = nodeModule.ElementNode

    __slots__ = (
        '_source',
        'parentTrees',
        )

    ### INITIALIZER ###

    def __init__(self, elements=None, source=None):
        super(ElementTree, self).__init__()
        self.parentTrees = weakref.WeakSet()
        self._source = None
        if elements and elements is not None:
            self.insert(elements)
            
        self.source = source
    
    ## Special Methods ##
    def __contains__(self, element):
        r'''
        Is true when the ElementTree contains the object within it
        
        If element.sortTuple(self.source) returns the right information, it's a fast
        O(log n) search. If not his is an O(n log n) operation in python not C, so slow.
        
        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> lastNote = score.flat.notes[-1]
        >>> lastNote in scoreTree
        True
        >>> n = note.Note("E--")
        >>> n in scoreTree
        False
        
        >>> s = stream.Stream(id='tinyStream')
        >>> s.insert(0, n)
        >>> st = s.asTree(flatten=False)
        >>> n in st
        True
        '''
        s = self.source
        sourcePosition = element.sortTuple(s)
        # might be wrong if element not in s or s is None
        
        nodeAtPosition = self.getNodeByPosition(sourcePosition)
        if nodeAtPosition is not None:
            if nodeAtPosition.payload is element:
                return True 
            
        # not found, do slow search.
        for pl in self:
            if pl is element:
                return True

        return False

    def __eq__(self, expr):
        r'''
        Two ElementTrees are equal only if they are the same object.
        
        >>> et1 = tree.trees.ElementTree()
        >>> et2 = tree.trees.ElementTree()
        >>> et3 = et1
        >>> et1 == et2
        False
        >>> et1 == et3
        True

        >>> et2 != et1
        True
        '''
        return self is expr

    def __getitem__(self, i):
        r'''
        Gets elements by integer index or slice.  This is pretty fast in computational time
        (O(log n)), but it's O(log n) in Python while normal list slicing is O(1) in C, so
        don't use trees for __getitem__ searching if you don't have to.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> scoreTree
        <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>

        >>> scoreTree[0]
        <music21.instrument.Instrument PartA: : >

        >>> scoreTree[-1]
        <music21.bar.Barline style=final>

        >>> scoreTree[2000] is None
        True
        
        Slices...

        >>> scoreTree[2:5]
        [<music21.clef.BassClef>, <music21.clef.BassClef>, <music21.meter.TimeSignature 2/4>]

        >>> scoreTree[-6:-3]
        [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note D#>]

        >>> scoreTree[-100:-200]
        []

        >>> for x in scoreTree[:]:
        ...     x
        <music21.instrument.Instrument PartA: : >
                ...
        <music21.bar.Barline style=final>

        These should all be the same as the flat version:
        
        >>> scoreFlat = score.flat
        >>> for i in (0, -1, 10):
        ...     if scoreFlat[i] is not scoreTree[i]:
        ...          print("false!")

        >>> for i, j in ((2, 5), (-6, -3)):
        ...     sfSlice = scoreFlat[i:j]
        ...     for n in range(i, j):
        ...         sliceOffset = n - i
        ...         if sfSlice[sliceOffset] is not scoreFlat[n]:
        ...             print("false!")
        '''
        try:
            nodeOrNodeList = self.getNodeByIndex(i)
        except IndexError:
            return None
        
        if nodeOrNodeList is None:
            return nodeOrNodeList
        elif not isinstance(nodeOrNodeList, list):
            return nodeOrNodeList.payload
        else:
            return [n.payload for n in nodeOrNodeList]

    def __hash__(self):
        return hash((type(self), id(self)))

    def __len__(self):
        r'''
        Gets the length of the ElementTree, i.e., the number of elements enclosed.
        This is a very very fast O(1).

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> len(scoreTree)
        20
        
        Works well on OffsetTrees also, which are more complex, because they can
        have multiple elements per Node.

        >>> offTree = tree.trees.OffsetTree()
        >>> len(offTree)
        0

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> noteList = [note.Note() for _ in tsList]
        >>> for i,n in enumerate(noteList):
        ...     n.offset, n.quarterLength = tsList[i]
        >>> offTree.insert(noteList)
        >>> len(offTree)
        10
        >>> len(offTree) == len(noteList)
        True

        >>> offTree.removeElements(noteList)
        >>> len(offTree)
        0
        '''
        if self.rootNode is None:
            return 0
        return self.rootNode.subtreeElementsStopIndex

    def __ne__(self, expr):
        return not self == expr

    def __repr__(self):
        o = self.source
        pos = self.lowestPosition()
        endt = self.endTime
        
        if hasattr(pos, 'shortRepr'):
            # sortTuple
            pos = pos.shortRepr()
        if hasattr(endt, 'shortRepr'):
            # sortTuple
            endt = endt.shortRepr()
            
        if o is None:
            return '<{} {{{}}} ({} to {})>'.format(
                type(self).__name__,
                len(self),
                pos,
                endt,
                )
        else:
            return '<{} {{{}}} ({} to {}) {!s}>'.format(
                type(self).__name__,
                len(self),
                pos,
                endt,
                repr(o),
                )

    def __setitem__(self, i, new):
        r'''
        Sets elements at index `i` to `new`, but keeping the old position
        of the element there. (This is different from OffsetTrees, where things can move around).

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> n = scoreTree[10]
        >>> n
        <music21.note.Note G#>
        >>> scoreTree.getNodeByIndex(10)
        <ElementNode: Start:2.0 <0.20...> Indices:(l:10 *10* r:11) 
            Payload:<music21.note.Note G#>>

        >>> scoreTree[10] = note.Note('F#')
        >>> scoreTree[10]
        <music21.note.Note F#>
        >>> scoreTree.getNodeByIndex(10)
        <ElementNode: Start:2.0 <0.20...> Indices:(l:10 *10* r:11) 
            Payload:<music21.note.Note F#>>

        
        >>> scoreTree[10:13]
        [<music21.note.Note F#>, <music21.note.Note F>, <music21.note.Note G>]
        >>> scoreTree[10:14:2] = [note.Note('E#'), note.Note('F-')]
        >>> scoreTree[10:13]
        [<music21.note.Note E#>, <music21.note.Note F>, <music21.note.Note F->]
        '''
        if isinstance(i, int):
            n = self.getNodeByIndex(i)
            if n is None: 
                message = 'Index must be less than {}'.format(len(self))
                raise TypeError(message)
            n.payload = new
        elif isinstance(i, slice):
            if not isinstance(new, list):
                message = 'If {} is a slice, then {} must be a list'.format(i, new)
                raise TypeError(message)
            sliceLen = (i.stop - i.start)/i.step
            if sliceLen != len(new):
                message = '{} is a slice of len {}, so {} cannot have len {}'.format(i, sliceLen,
                                                                                     new, len(new))
                raise TypeError(message)
            for j, sliceIter in enumerate(range(i.start, i.stop, i.step)):
                self[sliceIter] = new[j] # recursive.
        else:
            message = 'Indices must be ints or slices, got {}'.format(i)
            raise TypeError(message)

    def __str__(self):
        '''
        Print the whole contents of the tree.
        
        Slow: O(n log n) time, but it's just for debugging...
        
        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> print(scoreTree)
        <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>
            PartA: : 
            PartB: : 
            <music21.clef.BassClef>
            <music21.clef.BassClef>
            <music21.meter.TimeSignature 2/4>
            <music21.meter.TimeSignature 2/4>
            <music21.note.Note C>
            <music21.note.Note C#>
            <music21.note.Note D>
            <music21.note.Note E>
            <music21.note.Note G#>
            <music21.note.Note F>
            <music21.note.Note G>
            <music21.note.Note E#>
            <music21.note.Note A>
            <music21.note.Note B>
            <music21.note.Note D#>
            <music21.note.Note C>
            <music21.bar.Barline style=final>
            <music21.bar.Barline style=final>
        '''
        result = []
        result.append(repr(self))
        for x in self:
            subresult = str(x).splitlines()
            subresult = ['\t' + x for x in subresult]
            result.extend(subresult)
        result = '\n'.join(result)
        return result

    def __iter__(self):
        r'''
        Iterates through all the nodes in the offset tree and returns each node's payload
        
        Not an especially efficient way of using this beautiful tree object...

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> for x in scoreTree:
        ...     print(x)
        PartA: : 
        PartB: : 
        <music21.clef.BassClef>
        <music21.clef.BassClef>
        <music21.meter.TimeSignature 2/4>
        <music21.meter.TimeSignature 2/4>
        <music21.note.Note C>
        <music21.note.Note C#>
        ...

        '''
        for node in self.iterNodes():
            yield node.payload
            
    ### PRIVATE METHODS ###
    
    def _updateNodes(self, initialPosition=None, initialEndTime=None, visitedParents=None):
        '''
        runs updateIndices and updateEndTimes on the rootNode
        and if the offset or endTime of the tree differs from
        `initialPosition` or `initialEndTime` will run _updateParents()
        as well.
        
        Called by insert() and remove().
        '''
        if self.rootNode is not None:
            self.rootNode.updateIndices()
            self.rootNode.updateEndTimes()
        
        if (self.lowestPosition() != initialPosition
                or self.endTime != initialEndTime):
            self._updateParents(initialPosition, visitedParents=visitedParents)
    
    def _updateParents(self, oldPosition, visitedParents=None):
        '''
        Tells all parents that the position of this tree has
        changed.
        
        Not currently used.
        '''
        if visitedParents is None:
            visitedParents = set()
        for parent in self.parentTrees:
            if parent is None or parent in visitedParents:
                continue
            visitedParents.add(parent)
            parentPosition = parent.offset
            parent._removeElementAtPosition(self, oldPosition)
            parent._insertCore(self.offset, self)
            
            parent._updateNodes(parentPosition, visitedParents=visitedParents)

    def _removeElementAtPosition(self, element, position):
        '''
        removes an element or ElementTree from a position 
        (either its current .offset or its oldPosition) without updating
        the indices, endTimes, etc.  
        '''
        node = self.getNodeByPosition(position)
        if node is None:
            return

        if isinstance(node.payload, list):
            # OffsetTree
            if element in node.payload:
                node.payload.remove(element)
            if not node.payload:
                self.removeNode(position)
        else:
            if node.payload is element:
                node.payload = None
            if node.payload is None:
                self.removeNode(position)

    ### PUBLIC METHODS ###
    def getPositionFromElementUnsafe(self, el):
        '''
        A quick but dirty method for getting the likely position (or offset) of an element
        within the elementTree from the element itself.  Such as calling 
        
        el.getOffsetBySite(tree.source) or something like that.
        
        Pulled out for subclassing
        '''
        return el.sortTuple(self.source)
    
    def populateFromSortedList(self, listOfTuples):
        '''
        This method assumes that the current tree is empty (or will be wiped) and 
        that listOfTuples is a non-empty
        list where the first element is a unique position to insert,
        and the second is the complete payload for that node, and
        that the positions are strictly increasing in order.
        
        This is about an order of magnitude faster (3ms vs 21ms for 1000 items; 31 vs. 30ms for
        10,000 items) than running createNodeAtPosition() for each element in a list if it is
        already sorted.  Thus it should be used when converting a
        Stream where .isSorted is True into a tree.
        
        If any of the conditions is not true, expect to get a dangerously
        badly sorted tree that will be useless.
        
        >>> bFlat = corpus.parse('bwv66.6').flat
        >>> bFlat.isSorted
        True
        
        >>> listOfTuples = [(e.sortTuple(bFlat), e) for e in bFlat]
        >>> listOfTuples[10]
        (SortTuple(atEnd=0, offset=0.0, priority=0, ...), 
         <music21.key.Key of f# minor>)

        >>> t = tree.trees.ElementTree()
        >>> t.rootNode is None
        True
        >>> t.populateFromSortedList(listOfTuples)
        >>> t.rootNode
        <ElementNode: Start:15.0 <0.20...> Indices:(l:0 *97* r:195) 
            Payload:<music21.note.Note D#>>
        
        >>> n = t.rootNode
        >>> while n is not None:
        ...    print(n)
        ...    n = n.leftChild
        <ElementNode: Start:15.0 <0.20...> Indices:(l:0 *97* r:195) Payload:<music21.note.Note D#>>
        <ElementNode: Start:6.0 <0.20...>  Indices:(l:0 *48* r:97) Payload:<music21.note.Note B>>
        <ElementNode: Start:0.5 <0.20...>  Indices:(l:0 *24* r:48) Payload:<music21.note.Note G#>>
        <ElementNode: Start:0.0 <0.2...>   Indices:(l:0 *12* r:24) 
            Payload:<music21.key.Key of f# minor>>
        <ElementNode: Start:0.0 <0.0...>   Indices:(l:0 *6* r:12) Payload:<music21.clef.TrebleClef>>
        <ElementNode: Start:0.0 <0.-25...> Indices:(l:0 *3* r:6) 
            Payload:<music21.instrument.Instrument P3: Tenor: Instrument 3>>
        <ElementNode: Start:0.0 <0.-25...> Indices:(l:0 *1* r:3) 
            Payload:<music21.instrument.Instrument P1: Soprano: Instrument 1>>
        <ElementNode: Start:0.0 <0.-30...> Indices:(l:0 *0* r:1) 
            Payload:<music21.metadata.Metadata object at 0x104adbdd8>>

        >>> n = t.rootNode
        >>> while n is not None:
        ...    print(n)
        ...    n = n.rightChild
        <ElementNode: Start:15.0 <0.20...> Indices:(l:0 *97* r:195) 
            Payload:<music21.note.Note D#>>
        <ElementNode: Start:25.0 <0.20...> Indices:(l:98 *146* r:195) 
            Payload:<music21.note.Note F#>>
        <ElementNode: Start:32.0 <0.20...> Indices:(l:147 *171* r:195) 
            Payload:<music21.note.Note F#>>
        <ElementNode: Start:34.0 <0.20...> Indices:(l:172 *183* r:195) 
            Payload:<music21.note.Note D>>
        <ElementNode: Start:35.0 <0.20...> Indices:(l:184 *189* r:195) 
            Payload:<music21.note.Note A#>>
        <ElementNode: Start:36.0 <0.-5...> Indices:(l:190 *192* r:195) 
            Payload:<music21.bar.Barline style=final>>
        <ElementNode: Start:36.0 <0.-5...> Indices:(l:193 *194* r:195) 
            Payload:<music21.bar.Barline style=final>>
        '''
        def recurse(l, globalStartOffset):
            '''
            Divide and conquer.
            '''
            lenL = len(l)
            if lenL == 0:
                return None
            midpoint = lenL//2
            midtuple = l[midpoint]
            n = NodeClass(midtuple[0], midtuple[1])
            n.payloadElementIndex = globalStartOffset + midpoint
            n.subtreeElementsStartIndex = globalStartOffset
            n.subtreeElementsStopIndex = globalStartOffset + lenL
            n.leftChild = recurse(l[:midpoint], globalStartOffset)
            n.rightChild = recurse(l[midpoint + 1:], globalStartOffset + midpoint + 1)
            n.update()
            return n
        
        NodeClass = self.nodeClass
        self.rootNode = recurse(listOfTuples, 0)    
    
    def getNodeByIndex(self, i):
        '''
        Get a node whose element is at a particular index (not position).  Works with slices too
        
        See __getitem__ for caveats about speed...

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> scoreTree
        <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>

        >>> scoreTree.getNodeByIndex(0)
        <ElementNode: Start:0.0 <0.-25...> Indices:(l:0 *0* r:2) 
            Payload:<music21.instrument.Instrument PartA: : >>

        >>> scoreTree.getNodeByIndex(-1)
        <ElementNode: Start:End <0.-5...> Indices:(l:19 *19* r:20) 
            Payload:<music21.bar.Barline style=final>>

        >>> scoreTree.getNodeByIndex(slice(2, 5))
        [<ElementNode: Start:0.0 <0.0...> Indices:(l:0 *2* r:4) Payload:<music21.clef.BassClef>>, 
         <ElementNode: Start:0.0 <0.0...> Indices:(l:3 *3* r:4) Payload:<music21.clef.BassClef>>, 
         <ElementNode: Start:0.0 <0.4...> Indices:(l:0 *4* r:8) 
             Payload:<music21.meter.TimeSignature 2/4>>]

        >>> scoreTree.getNodeByIndex(slice(-6, -3))
        [<ElementNode: Start:5.0 <0.20...> Indices:(l:9 *14* r:20) Payload:<music21.note.Note A>>, 
         <ElementNode: Start:6.0 <0.20...> Indices:(l:15 *15* r:17) Payload:<music21.note.Note B>>, 
         <ElementNode: Start:6.0 <0.20...> Indices:(l:16 *16* r:17) Payload:<music21.note.Note D#>>]

        >>> scoreTree.getNodeByIndex(slice(-100, -200))
        []
        '''
        def recurseByIndex(node, index):
            '''
            Return the node element at a given index
            '''
            if node.payloadElementIndex == index:
                return node
            elif node.leftChild and index < node.payloadElementIndex:
                return recurseByIndex(node.leftChild, index)
            elif node.rightChild and node.payloadElementIndex <= index:
                return recurseByIndex(node.rightChild, index)

        def recurseBySlice(node, start, stop):
            '''
            Return a slice of the nodes (plural) whose indices are between start <= index < stop.
            '''
            result = []
            if node is None:
                return result
            if start < node.payloadElementIndex and node.leftChild:
                result.extend(recurseBySlice(node.leftChild, start, stop))
            if start <= node.payloadElementIndex < stop:
                result.append(node)
            if node.payloadElementIndex < stop and node.rightChild:
                result.extend(recurseBySlice(node.rightChild, start, stop))
            return result
        
        if isinstance(i, int):
            if self.rootNode is None:
                raise IndexError
            if i < 0:
                i = self.rootNode.subtreeElementsStopIndex + i
            if i < 0 or self.rootNode.subtreeElementsStopIndex <= i:
                raise IndexError
            return recurseByIndex(self.rootNode, i)
        elif isinstance(i, slice):
            if self.rootNode is None:
                return []
            indices = i.indices(self.rootNode.subtreeElementsStopIndex)
            start, stop = indices[0], indices[1]
            return recurseBySlice(self.rootNode, start, stop)
        else:
            raise TypeError('Indices must be integers or slices, got {}'.format(i))
    
    def iterNodes(self):
        '''
        Identical to the iterating on a core.AVLTree -- yields each node in order 

        Slow: O(n log n) time so don't make this your main thing.
        
        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> scoreTree
        <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>
        
        >>> for node in scoreTree.iterNodes():
        ...     print(node)
        <ElementNode: Start:0.0 <0.-25...> Indices:(l:0 *0* r:2) 
                Payload:<music21.instrument.Instrument PartA: : >>
        <ElementNode: Start:0.0 <0.-25...> Indices:(l:1 *1* r:2) 
                Payload:<music21.instrument.Instrument PartB: : >>
        <ElementNode: Start:0.0 <0.0...> Indices:(l:0 *2* r:4) Payload:<music21.clef.BassClef>>
        <ElementNode: Start:0.0 <0.0...> Indices:(l:3 *3* r:4) Payload:<music21.clef.BassClef>>
        <ElementNode: Start:0.0 <0.4...> Indices:(l:0 *4* r:8) 
                Payload:<music21.meter.TimeSignature 2/4>>
        <ElementNode: Start:0.0 <0.4...> Indices:(l:5 *5* r:6) 
                Payload:<music21.meter.TimeSignature 2/4>>
        <ElementNode: Start:0.0 <0.20...> Indices:(l:5 *6* r:8) Payload:<music21.note.Note C>>
        <ElementNode: Start:0.0 <0.20...> Indices:(l:7 *7* r:8) Payload:<music21.note.Note C#>>
        <ElementNode: Start:1.0 <0.20...> Indices:(l:0 *8* r:20) Payload:<music21.note.Note D>>
        <ElementNode: Start:2.0 <0.20...> Indices:(l:9 *9* r:11) Payload:<music21.note.Note E>>
            ...
        <ElementNode: Start:7.0 <0.20...> Indices:(l:15 *17* r:20) 
                Payload:<music21.note.Note C>>
        <ElementNode: Start:End <0.-5...> Indices:(l:18 *18* r:20) 
                Payload:<music21.bar.Barline style=final>>
        <ElementNode: Start:End <0.-5...> Indices:(l:19 *19* r:20) 
                Payload:<music21.bar.Barline style=final>>                
        '''
        # py 3 only
        # yield from super(ElementTree, self).__iter__()
        for n in super(ElementTree, self).__iter__():
            yield n

    def index(self, element, position=None):
        r'''
        Gets index of `element` in tree. position could be none.

        If the element is in the original score, then it should be very fast (O(log n))

        >>> score = tree.makeExampleScore()
        >>> scoreFlat = score.flat
        >>> n = scoreFlat.notes[-1]
        
        >>> flatTree = scoreFlat.asTree()
        >>> flatTree.index(n)
        17

        If it's not in the original stream, then it should be slower than doing 
        it on a stream (O (n log n)).
        
        >>> scoreTree = score.asTree(flatten=True)
        >>> n = score.flat.notes[-1]
        >>> scoreTree.index(n)
        17

        And if it's nowhere at all, you get a ValueError!

        >>> scoreTree.index(note.Note("F-"))
        Traceback (most recent call last):
        ValueError: <music21.note.Note F-> not in Tree at position 
            SortTuple(atEnd=0, offset=0.0, priority=0, ...).
        '''
        if position is None:
            position = self.getPositionFromElementUnsafe(element)
        node = self.getNodeByPosition(position)
        if node is None or node.payload is not element:
            for i, n in enumerate(self):
                if n is element:
                    return i
            
            raise ValueError('{} not in Tree at position {}.'.format(element, position))
        return node.payloadElementIndex

    def _getPositionsFromElements(self, elements):
        '''
        takes a list of elements and returns a list of positions.
        
        In an ElementTree, this will be a list of .sortTuple() calls.
        
        In an OffsetTree, this will be a list of .offset calls
        
        '''
        return [self.getPositionFromElementUnsafe(el) for el in elements]

    def insert(self, positionsOrElements, elements=None):
        r'''
        Inserts elements or `Timespans` into this tree.
        
        >>> n = note.Note()
        >>> ot = tree.trees.OffsetTree()
        >>> ot
        <OffsetTree {0} (-inf to inf)>
        >>> ot.insert(10.0, n)
        >>> ot
        <OffsetTree {1} (10.0 to 11.0)>
        
        >>> n2 = note.Note('D')
        >>> n2.offset = 20
        >>> n3 = note.Note('E')
        >>> n3.offset = 5
        >>> ot.insert([n2, n3])
        >>> ot
        <OffsetTree {3} (5.0 to 21.0)>
        '''
        initialPosition = self.lowestPosition()
        initialEndTime = self.endTime
        if elements is None:
            elements = positionsOrElements
            positions = None
        else:
            positions = positionsOrElements
            if not common.isListLike(positions) or hasattr(positions, 'shortRepr'):
                # is not a list and not a sortTuple...
                positions = [positions]
        
        if (not common.isListLike(elements)
                and not isinstance(elements, (set, frozenset))
                ): # not a list. a single element or timespan
            elements = [elements]
        if positions is None:
            positions = self._getPositionsFromElements(elements)
                
        for i, el in enumerate(elements):
            pos = positions[i]
            self._insertCore(pos, el)
        
        self._updateNodes(initialPosition, initialEndTime)

    def _insertCore(self, position, el):
        '''
        Inserts a single element at an offset, creating new nodes as necessary,
        but does not updateIndices or updateEndTimes or updateParents
        '''                
        self.createNodeAtPosition(position)
        node = self.getNodeByPosition(position)
        node.payload = el
        
    def highestPosition(self):
        r'''
        Gets the latest position in this tree.

        Keep as a property, because a similar property exists on streams.

        >>> score = corpus.parse('bwv66.6')
        >>> tsTree = score.asTimespans(classList=(note.Note,))
        >>> tsTree.highestPosition()
        35.0
        '''
        def recurse(node):
            if node.rightChild is not None:
                return recurse(node.rightChild)
            else:
                return node.position
            
        if self.rootNode is not None:
            return recurse(self.rootNode)
        else:
            return NEGATIVE_INFINITY

    def lowestPosition(self):
        r'''
        Gets the earliest position in this tree.

        >>> score = tree.makeExampleScore()
        >>> elTree = score.asTree()
        >>> elTree.lowestPosition().shortRepr()
        '0.0 <0.-20...>'

        >>> tsTree = score.asTimespans()
        >>> tsTree.lowestPosition()
        0.0
        '''
        def recurse(node):
            if node.leftChild is not None:
                return recurse(node.leftChild)
            return node.position
        
        if self.rootNode is not None:
            return recurse(self.rootNode)
        else:
            return NEGATIVE_INFINITY

    
    ### PROPERTIES ###
    @property
    def source(self):
        '''
        the original stream. (stored as a weakref but returned unwrapped)
        
        >>> example = tree.makeExampleScore()
        >>> eTree = example.asTree()
        >>> eTree.source is example
        True
        
        >>> s = stream.Stream()
        >>> eTree.source = s
        >>> eTree.source is s
        True
        '''
        return common.unwrapWeakref(self._source)
        
    @source.setter
    def source(self, expr):
        # uses weakrefs so that garbage collection on the stream cache is possible...
        self._source = common.wrapWeakref(expr)
    
    @property
    def endTime(self):
        r'''
        Gets the latest stop position in this element-tree.

        This is cast as a property so that it can be used like a TimeSpan in a TimeSpanTree

        >>> score = corpus.parse('bwv66.6')
        >>> tsTree = score.asTree()
        >>> tsTree.endTime
        36.0
        
        Returns infinity if no elements exist:
        
        >>> et = tree.trees.ElementTree()
        >>> et.endTime
        inf
        '''
        if self.rootNode is not None:
            return self.rootNode.endTimeHigh
        return INFINITY




#----------------------------------------------------------------
class OffsetTree(ElementTree):
    '''
    A tree representation where positions are offsets in the score
    and each node has a payload which is a list of elements at
    that offset (unsorted by sort order).
    '''
    __slots__ = ()

    nodeClass = nodeModule.OffsetNode

    ### SPECIAL METHODS ###
    def __init__(self, elements=None, source=None):
        super(OffsetTree, self).__init__(elements, source)


    def __contains__(self, element):
        r'''
        Is true when the ElementTree contains the object within it; 
        
        TRUE IF and ONLY if the
        .offset of the element matches the position in the tree -- thus it is very fast!

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True, groupOffsets=True)

        >>> score.flat[5] in scoreTree
        True

        Note that this way of finding an item won't work because the offset is different
        from the flat offset:
        
        >>> n = score.parts[0].measure(2).notes[1]
        >>> n
        <music21.note.Note F>
        >>> n.offset
        1.0
        >>> n in scoreTree
        False
        '''
        try:
            offset = element.offset
        except AttributeError:
            raise ElementTreeException('element must be a Music21Object, i.e., must have offset')
        candidates = self.elementsStartingAt(offset)
        if element in candidates:
            return True
        else:
            return False

    def __getitem__(self, i):
        r'''
        Gets elements by integer index or slice.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True, groupOffsets=True)
        
        >>> scoreTree[0]
        <music21.instrument.Instrument PartA: : >

        >>> scoreTree[-1]
        <music21.bar.Barline style=final>

        >>> scoreTree[2:5]
        [<music21.clef.BassClef>, <music21.clef.BassClef>, <music21.meter.TimeSignature 2/4>]

        >>> scoreTree[-6:-3]
        [<music21.note.Note A>, <music21.note.Note B>, <music21.note.Note D#>]

        >>> scoreTree[-100:-200]
        []
        '''
        def recurseByIndex(node, index):
            '''
            Return the payload element at a given index
            '''
            if node.payloadElementsStartIndex <= index < node.payloadElementsStopIndex:
                return node.payload[index - node.payloadElementsStartIndex]
            elif node.leftChild and index < node.payloadElementsStartIndex:
                return recurseByIndex(node.leftChild, index)
            elif node.rightChild and node.payloadElementsStopIndex <= index:
                return recurseByIndex(node.rightChild, index)

        def recurseBySlice(node, start, stop):
            '''
            Return a slice of the payload elements (plural) where start <= index < stop.
            '''
            result = []
            if node is None:
                return result
            if start < node.payloadElementsStartIndex and node.leftChild:
                result.extend(recurseBySlice(node.leftChild, start, stop))
            if start < node.payloadElementsStopIndex and node.payloadElementsStartIndex < stop:
                indexStart = start - node.payloadElementsStartIndex
                if indexStart < 0:
                    indexStart = 0
                indexStop = stop - node.payloadElementsStartIndex
                result.extend(node.payload[indexStart:indexStop])
            if node.payloadElementsStopIndex <= stop and node.rightChild:
                result.extend(recurseBySlice(node.rightChild, start, stop))
            return result
        
        if isinstance(i, int):
            if self.rootNode is None:
                raise IndexError
            if i < 0:
                i = self.rootNode.subtreeElementsStopIndex + i
            if i < 0 or self.rootNode.subtreeElementsStopIndex <= i:
                raise IndexError
            return recurseByIndex(self.rootNode, i)
        elif isinstance(i, slice):
            if self.rootNode is None:
                return []
            indices = i.indices(self.rootNode.subtreeElementsStopIndex)
            start, stop = indices[0], indices[1]
            return recurseBySlice(self.rootNode, start, stop)
        else:
            raise TypeError('Indices must be integers or slices, got {}'.format(i))

    def __setitem__(self, i, new):
        r'''
        Sets elements or timespans at index `i` to `new`.
        
        TODO: this should be a bit different for OffsetTrees, probably more like ElementTrees
         

        >>> tss = [
        ...     tree.spans.Timespan(0, 2),
        ...     tree.spans.Timespan(0, 9),
        ...     tree.spans.Timespan(1, 1),
        ...     ]
        >>> tsTree = tree.timespanTree.TimespanTree()
        >>> tsTree.insert(tss)
        >>> tsTree[0] = tree.spans.Timespan(-1, 6)
        >>> for x in tsTree:
        ...     x
        <Timespan -1.0 6.0>
        <Timespan 0.0 9.0>
        <Timespan 1.0 1.0>

        Note however, that calling __getitem__ after __setitem__ will not return
        what you just set if the timing is wrong.  This is different from the
        behavior on ElementTree which assumes that the new element wants to be
        at the old element's offset.
        
        >>> tsTree[2] = tree.spans.Timespan(-0.5, 4)
        >>> tsTree[2]
        <Timespan 0.0 9.0>
        >>> for x in tsTree:
        ...     x
        <Timespan -1.0 6.0>
        <Timespan -0.5 4.0>
        <Timespan 0.0 9.0>


        Works with slices too.

        >>> tsTree[1:] = [tree.spans.Timespan(10, 20)]
        >>> for x in tsTree:
        ...     x
        <Timespan -1.0 6.0>
        <Timespan 10.0 20.0>
        '''
        if isinstance(i, (int, slice)):
            old = self[i]
            self.removeTimespan(old)
            self.insert(new)
        else:
            message = 'Indices must be ints or slices, got {}'.format(i)
            raise TypeError(message)


    def __iter__(self):
        r'''
        Iterates through all the nodes in the offset tree and returns each thing
        in the payload.
        
        Not an especially efficient way of using this beautiful tree object...

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True, groupOffsets=True)
        >>> for x in scoreTree:
        ...     print(x)
        PartA: : 
        PartB: : 
        <music21.clef.BassClef>
        <music21.clef.BassClef>
        <music21.meter.TimeSignature 2/4>
        <music21.meter.TimeSignature 2/4>
        <music21.note.Note C>
        <music21.note.Note C#>
        ...

        '''
        for node in self.iterNodes():
            for el in node.payload:
                yield el


    #----------static methods ------------------------
    @staticmethod
    def elementEndTime(el, node):
        '''
        Use so that both OffsetTrees, which have elements which do not have a .endTime, and
        TimespanTrees, which have element that have an .endTime but not a duration, can
        use most of the same code.
        '''
        return node.position + el.duration.quarterLength

    #----------public methods ------------------------
    def getPositionFromElementUnsafe(self, el):
        '''
        A quick but dirty method for getting the likely position (or offset) of an element
        within the elementTree from the element itself.  Such as calling 
        
        el.getOffsetBySite(tree.source) or something like that.
        
        Pulled out for subclassing
        '''
        return el.offset

    def append(self, el):
        '''
        Add an element to the end, making certain speed savings.        
        '''
        initialPosition = self.lowestPosition() # will only change if is empty
        endTime = self.endTime
        if endTime == INFINITY:
            endTime = 0
        self._insertCore(endTime, el)        
        self._updateNodes(initialPosition, initialEndTime=None)


    @staticmethod
    def _insertCorePayloadSortKey(x):
        '''
        Payload sorting is done the old-fashioned way, because
        the number of elements at a single offset should be few enough that
        it is not a problem
        '''
        return x.sortTuple()[2:] # cut off atEnd and offset        

    def _insertCore(self, position, el):
        '''
        Inserts a single element at an offset, creating new nodes as necessary,
        but does not updateIndices or updateEndTimes or updateParents
        '''                
        self.createNodeAtPosition(position)
        node = self.getNodeByPosition(position)
        
        node.payload.append(el)
        node.payload.sort(key=self._insertCorePayloadSortKey)
    
    def copy(self):
        r'''
        Creates a new tree with the same payload as this tree.
        
        This is analogous to `dict.copy()`.  

        Much, much faster than creating a new tree; creating one
        with 3600 items took 500ms.  Creating the tree the first time
        was 40 seconds, so about an 80x speedup.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTimespans()
        >>> newTree = scoreTree.copy()
        >>> newTree
        <TimespanTree {20} (0.0 to 8.0) <music21.stream.Score exampleScore>>

        >>> scoreTree[16]
        <PitchedTimespan (6.0 to 8.0) <music21.note.Note D#>>
        >>> newTree[16]
        <PitchedTimespan (6.0 to 8.0) <music21.note.Note D#>>
        
        >>> scoreTree[16] is newTree[16]
        True
        '''
        newTree = type(self)()
        # this is just as efficient as ._insertCore, since it's given a list.
        newTree.insert([x for x in self])
        newTree.source = self.source
        newTree.parentTrees = self.parentTrees.copy()
        return newTree

    def elementsStartingAt(self, position):
        r'''
        Finds elements or timespans in this tree which start at `position`.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> for timespan in scoreTree.elementsStartingAt(0.5):
        ...     timespan
        ...
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note G#>>
        '''
        results = []
        node = self.getNodeByPosition(position)
        if node is not None:
            if isinstance(node.payload, list):
                results.extend(node.payload)
            elif node.payload is not None:
                results.append(node.payload)
        return tuple(results)

    def elementsStoppingAt(self, offset):
        r'''
        Finds elements in this OffsetTree which stop at `offset`.  Elements are ordered
        according to (start) offset.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTree(flatten=True, groupOffsets=True)
        >>> for el in scoreTree.elementsStoppingAt(0.5):
        ...     el
        <music21.note.Note C#>
        <music21.note.Note A>
        <music21.note.Note A>

        Works also on timespans for TimespanTrees:

        >>> scoreTree = score.asTimespans()
        >>> for el in scoreTree.elementsStoppingAt(0.5):
        ...     el
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
        '''
        def recurse(node, offset):
            result = []
            if node is not None: # could happen in an empty TimespanTree
                if node.endTimeLow <= offset <= node.endTimeHigh:
                    if node.leftChild is not None:
                        result.extend(recurse(node.leftChild, offset))
                    for el in node.payload:
                        if self.elementEndTime(el, node) == offset:
                            result.append(el)
                    if node.rightChild is not None:
                        result.extend(recurse(node.rightChild, offset))
            return result
        
        results = recurse(self.rootNode, offset)
        return tuple(results)

    def elementsOverlappingOffset(self, offset):
        r'''
        Finds elements in this ElementTree which overlap `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTree(flatten=True, groupOffsets=True)
        >>> for el in scoreTree.elementsOverlappingOffset(0.5):
        ...     el
        ...
        <music21.note.Note E>

        Works with Timespans in TimespanTrees as well.

        >>> scoreTree = score.asTimespans()
        >>> for el in scoreTree.elementsOverlappingOffset(0.5):
        ...     el
        ...
        <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>
        '''
        def recurse(node, offset):
            result = [] # collections.deque()
            if node is not None:
                if node.position < offset < node.endTimeHigh:
                    result.extend(recurse(node.leftChild, offset))
                    # This currently requires timespans not elements, and list payloads...
                    # TODO: Fix/disambiguate.
                    for el in node.payload:
                        if offset < self.elementEndTime(el, node):
                            result.append(el)
                    result.extend(recurse(node.rightChild, offset))
                elif offset <= node.position:
                    result.extend(recurse(node.leftChild, offset))
            return result
        results = recurse(self.rootNode, offset)
        #if len(results) > 0 and hasattr(results[0], 'element'):
        #    results.sort(key=lambda x: (x.offset, x.endTime, x.element.sortTuple()[1:]))
        #else:
        #results.sort(key=lambda x: (x.offset, x.endTime))
        return tuple(results)

    def removeElements(self, elements, offsets=None, runUpdate=True): 
        r'''
        Removes `elements` which can be Music21Objects or Timespans 
        (a single one or a list) from this Tree.
        
        Much safer (for non-timespans) if a list of offsets is used but it is optional
        
        If runUpdate is False then the tree will be left with incorrect indices and
        endTimes; but it can speed up operations where an element is going to be removed
        and then immediately replaced: i.e., where the position of an element has changed        
        '''
        initialPosition = self.lowestPosition()
        initialEndTime = self.endTime
        if hasattr(elements, 'offset'): # a music21 object or an PitchedTimespan
            elements = [elements]
        if offsets is not None and not common.isListLike(offsets):
            offsets = [offsets]
        
        if offsets is not None and len(elements) != len(offsets):
            raise ElementTreeException(
                "Number of elements and number of offsets must be the same")

        
        for i, el in enumerate(elements):
            if offsets is not None:
                self._removeElementAtPosition(el, offsets[i]) 
            else:
                self._removeElementAtPosition(el, el.offset)
        
        if runUpdate:
            self._updateNodes(initialPosition, initialEndTime)





    def allOffsets(self):
        r'''
        Gets all unique offsets of all timespans in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tsTree = score.asTimespans()
        >>> for offset in tsTree.allOffsets()[:10]:
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
                pos = node.position
                if isinstance(pos, SortTuple):
                    result.append(pos.offset)
                else:
                    result.append(pos)
                if node.rightChild is not None:
                    result.extend(recurse(node.rightChild))
            return result
        return tuple(recurse(self.rootNode))

    def allTimePoints(self):
        r'''
        Gets all unique offsets (both starting and stopping) of all elements/timespans
        in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> for offset in scoreTree.allTimePoints()[:10]:
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
                result.add(node.position)
                result.update(node.payloadEndTimes())
                if node.rightChild is not None:
                    result.update(recurse(node.rightChild))
            return result
        return tuple(sorted(recurse(self.rootNode)))

    def overlapTimePoints(self, includeStopPoints=False, returnVerticality=False):
        '''
        Gets all timepoints where some element is starting 
        (or if includeStopPoints is True, where some element is starting or stopping) 
        while some other element is still continuing onward.
        
        >>> score = corpus.parse('bwv66.6')
        >>> scoreOffsetTree = score.asTree(flatten=True, groupOffsets=True)
        >>> scoreOffsetTree.overlapTimePoints()
        [0.5, 5.5, 6.5, 10.5, 13.5, 14.5, 15.5...]
        
        if returnVerticality is True, then a mapping of timepoint to elements is returned.  
        How cool is that?

        >>> otp = scoreOffsetTree.overlapTimePoints(returnVerticality=True)
        >>> otp[0]
        {0.5: <Verticality 0.5 {G#3 B3 E4 B4}>}
        
        '''
        checkPoints = self.allOffsets() if includeStopPoints is False else self.allTimePoints()
        overlaps = []
        for cp in checkPoints:
            overlappingElements = self.elementsOverlappingOffset(cp)
            if len(overlappingElements) == 0:
                continue
            if returnVerticality is False:
                overlaps.append(cp)
            else:
                overlaps.append({cp: self.getVerticalityAt(cp)})
        return overlaps

    def getVerticalityAt(self, offset):
        r'''
        Gets the verticality in this offset-tree which starts at `offset`.

        >>> bach = corpus.parse('bwv66.6')
        >>> scoreTree = bach.asTimespans()
        >>> scoreTree.getVerticalityAt(2.5)
        <Verticality 2.5 {G#3 B3 E4 B4}>

        Verticalities outside the range still return a Verticality, but it might be empty...

        >>> scoreTree.getVerticalityAt(2000)
        <Verticality 2000 {}>
            
        Test that it still works if the tree is empty...
            
        >>> scoreTree = bach.asTimespans(classList=(instrument.Tuba,))
        >>> scoreTree
        <TimespanTree {0} (-inf to inf) <music21.stream.Score ...>>
        >>> scoreTree.getVerticalityAt(5.0)
        <Verticality 5.0 {}>           

        Returns a verticality.Verticality object.
        '''
        from music21.tree.verticality import Verticality
        
        startTimespans = self.elementsStartingAt(offset)
        stopTimespans = self.elementsStoppingAt(offset)
        overlapTimespans = self.elementsOverlappingOffset(offset)
        
        verticality = Verticality(
            overlapTimespans=overlapTimespans,
            startTimespans=startTimespans,
            offset=offset,
            stopTimespans=stopTimespans,
            timespanTree=self,
            )
        return verticality


    def simultaneityDict(self):
        '''
        Creates a dictionary of offsets that have more than one element starting at that time,
        where the keys are offset times and the values are lists of elements at that moment.
        
        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True, groupOffsets=True)
        >>> scoreTree
        <OffsetTree {20} (0.0 to 8.0) <music21.stream.Score exampleScore>>
        
        >>> sd = scoreTree.simultaneityDict()
        >>> len(sd)
        5
        >>> list(sorted(sd.keys()))
        [0.0, 2.0, 4.0, 6.0, 8.0] 
        >>> sd[0.0]
        [<music21.instrument.Instrument PartA: : >, 
         <music21.instrument.Instrument PartB: : >, 
         <music21.clef.BassClef>, 
         <music21.clef.BassClef>, 
         <music21.meter.TimeSignature 2/4>, 
         <music21.meter.TimeSignature 2/4>, 
         <music21.note.Note C>, 
         <music21.note.Note C#>]
        >>> sd[2.0]
        [<music21.note.Note E>, <music21.note.Note G#>]
        '''
        simultaneityDict = {}
        for node in self.iterNodes():
            pl = node.payload
            if len(pl) > 1:
                simultaneityDict[node.position] = pl[:]
        return simultaneityDict



#----------------------------------------------------------------
#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testGetPositionAfterOffset(self):
        '''
        test that get position after works with
        an offset when the tree is built on SortTuples.        
        '''
        from music21 import stream, note

        et = ElementTree()

        s = stream.Stream()
        for i in range(100):
            n = note.Note()
            n.duration.quarterLength = 2.0
            s.insert(i * 2, n)

        for n in s:
            et.insert(n)
        self.assertTrue(repr(et).startswith('<ElementTree {100} (0.0 <0.20'))
    
        n2 = s[-1]

        self.assertEqual(et.index(n2, n2.sortTuple()), 99)
    
        st3 = et.getPositionAfter(5.0)
        self.assertIsNotNone(st3)

#     def testBachDoctest(self):
#         from music21 import corpus, note, chord, tree
#         bach = corpus.parse('bwv66.6')
#         tree = tree.fromStream.asTimespans(bach, flatten=True, 
#                                               classList=(note.Note, chord.Chord))
#         for verticalities in tree.iterateVerticalitiesNwise(n=3):
#             print(verticalities)
#             if verticalities[-1].offset == 25:
#                 pass
#             horizontalities = tree.unwrapVerticalities(verticalities)
#             for unused_part, horizontality in horizontalities.items():
#                 if horizontality.hasNeighborTone:
#                     merged = horizontality[0].new(endTime=horizontality[2].endTime,)
#                     #tree.remove(horizontality[0])
#                     #tree.remove(horizontality[1])
#                     #tree.remove(horizontality[2])
#                     #tree.insert(merged)
#      
#     
#         newBach = tree.toStream.partwise(tree, templateStream=bach,)
#         newBach.parts[1].measure(7).show('text')
# #     {0.0} <music21.chord.Chord F#4>
# #     {1.5} <music21.chord.Chord F#3>
# #     {2.0} <music21.chord.Chord C#4>
# 


    def testElementsStoppingAt(self):
        '''
        this was reporting:
        
        <music21.note.Note G#>
        <music21.note.Note C#>
        <music21.note.Note A>
        <music21.note.Note A>
        
        G# was coming from an incorrect activeSite.  activeSite should not be used!       
        '''
        from music21 import corpus, stream, note
        s = stream.Stream()
        n0 = note.Note('A')
        n0.duration.quarterLength = 3.0
        s.insert(0, n0)
        n1 = note.Note('B')
        n1.duration.quarterLength = 2.0
        s.insert(1, n1)
        n2 = note.Note('C')
        n2.duration.quarterLength = 1.0
        s.insert(2, n2)
        # and one later to be sure that order is right
        n3 = note.Note('A#')
        n3.duration.quarterLength = 2.5
        s.insert(0.5, n3)
        
        st = s.asTree(groupOffsets=True)
        stList = st.elementsStoppingAt(3.0)
        self.assertEqual(len(stList), 4)
        self.assertEqual([n.name for n in stList],
                         ['A', 'A#', 'B', 'C'])
        # making the tree more complex doesnot change anything, I hope?
        for i in range(30):
            s.insert(0, note.Rest())
        for i in range(22):
            s.insert(10 + i, note.Rest())
        st = s.asTree(groupOffsets=True)
        stList = st.elementsStoppingAt(3.0)
        self.assertEqual(len(stList), 4)
        self.assertEqual([n.name for n in stList],
                         ['A', 'A#', 'B', 'C'])
        
        
        
        # real world example
        score = corpus.parse('bwv66.6')
        scoreTree = score.asTree(flatten=True, groupOffsets=True)
        elementList = scoreTree.elementsStoppingAt(0.5)
        self.assertEqual(len(elementList), 3)
        self.assertEqual(elementList[0].name, 'C#')
        self.assertEqual(elementList[1].name, 'A')
        self.assertEqual(elementList[2].name, 'A')
        
        
                        

#     def testBachDoctest(self):
#         from music21 import corpus, note, chord, tree
#         bach = corpus.parse('bwv66.6')
#         scoreTree = tree.fromStream.asTimespans(bach, flatten=True, 
#                                               classList=(note.Note, chord.Chord))
#         print(scoreTree)
#         for verticalities in scoreTree.iterateVerticalitiesNwise(n=3):
#             if verticalities[-1].offset == 25:
#                 pass
#             horizontalities = scoreTree.unwrapVerticalities(verticalities)
#             for unused_part, horizontality in horizontalities.items():
#                 if horizontality.hasNeighborTone:
#                     merged = horizontality[0].new(endTime=horizontality[2].endTime,)
#                     scoreTree.remove(horizontality[0])
#                     scoreTree.remove(horizontality[1])
#                     scoreTree.remove(horizontality[2])
#                     scoreTree.insert(merged)
#      
#     
#         newBach = tree.toStream.partwise(scoreTree, templateStream=bach,)
#         newBach.show()
#         newBach.parts[1].measure(7).show('text')
# #     {0.0} <music21.chord.Chord F#4>
# #     {1.5} <music21.chord.Chord F#3>
# #     {2.0} <music21.chord.Chord C#4>

#------------------------------------------------------------------------------


_DOC_ORDER = (
    ElementTree,
    OffsetTree,
    )


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, runTest='testElementsStoppingAt')
