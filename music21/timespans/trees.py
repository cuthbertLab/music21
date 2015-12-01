# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespans/trees.py
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
'''

import collections
import random
import unittest
import weakref

from music21 import common
from music21 import exceptions21

from music21.timespans import spans, core
from music21.timespans import node as nodeModule

from music21.exceptions21 import TimespanException
from music21 import environment
environLocal = environment.Environment("timespans")

INFINITY = float('inf')
NEGATIVE_INFINITY = float('-inf')

#-------------------------------#

class ElementTree(core.AVLTree):
    r'''
    A data structure for efficiently storing a score: flat or recursed or normal.
    
    This data structure stores TimespanNodes: objects which implement both a
    `offset` and `endTime` property. It provides fast lookups of such
    objects and can quickly locate vertical overlaps.

    >>> et = timespans.trees.ElementTree()
    >>> et
    <ElementTree {0} (-inf to inf)>
    
    >>> for i in range(100):
    ...     n = note.Note()
    ...     et.insert(float(i), n)
    >>> et
    <ElementTree {100} (0.0 to 100.0)>
    
    >>> n2 = note.Note('D#')
    >>> et.insert(101.0, n2)
    
    These operations are very fast...

    >>> et.index(n2, 101.0)
    100
    >>> et.getPositionAfter(100.5)
    101.0

    '''
    ### CLASS VARIABLES ###
    nodeClass = nodeModule.ElementNode

    __slots__ = (
        '_origin',
        'parentTrees',
        )

    ### INITIALIZER ###

    def __init__(self, elements=None, origin=None):
        super(ElementTree, self).__init__()
        self.parentTrees = weakref.WeakSet()
        self._origin = None
        if elements and elements is not None:
            self.insert(elements)
            
        self.origin = origin
    
    ## Special Methods ##
    def __contains__(self, element):
        r'''
        Is true when the ElementTree contains the object within it; if and only if the
        .offset of the element matches the position in the tree.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [timespans.spans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> tss[0] in tree
        True

        >>> timespans.spans.Timespan(-200, 1000) in tree
        False
        
        The exact Timespan object does not have to be in the tree, just one with the same offset
        and endTime:
        
        >>> tsDuplicate = timespans.spans.Timespan(0, 2)
        >>> tsDuplicate in tree
        True
        '''
        try:
            offset = element.offset
        except AttributeError:
            raise TimespanTreeException('element must be a Music21Object, i.e., must have offset')
        candidates = self.elementsStartingAt(offset)
        if element in candidates:
            return True
        else:
            return False

    def __eq__(self, expr):
        r'''
        Two ElementTrees are equal only if their ids are equal.
        
        (TODO: make it true only if the two have exactly identical elements 
        unless this interferes with hashing. Use "is" for this)
        '''
        return id(self) == id(expr)

    def __getitem__(self, i):
        r'''
        Gets elements by integer index or slice.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [timespans.spans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> tree[0]
        <Timespan 0.0 2.0>

        >>> tree[-1]
        <Timespan 7.0 7.0>

        >>> tree[2:5]
        [<Timespan 1.0 1.0>, <Timespan 2.0 3.0>, <Timespan 3.0 4.0>]

        >>> tree[-6:-3]
        [<Timespan 3.0 4.0>, <Timespan 4.0 9.0>, <Timespan 5.0 6.0>]

        >>> tree[-100:-200]
        []

        >>> for x in tree[:]:
        ...     x
        <Timespan 0.0 2.0>
        ...
        <Timespan 7.0 7.0>
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

    def __hash__(self):
        return hash((type(self), id(self)))

    def __iter__(self):
        r'''
        Iterates through all the nodes in the offset tree and returns each thing
        in the payload.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [timespans.spans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> for x in tree:
        ...     x
        <Timespan 0.0 2.0>
        <Timespan 0.0 9.0>
        <Timespan 1.0 1.0>
        <Timespan 2.0 3.0>
        <Timespan 3.0 4.0>
        <Timespan 4.0 9.0>
        <Timespan 5.0 6.0>
        <Timespan 5.0 8.0>
        <Timespan 6.0 8.0>
        <Timespan 7.0 7.0>
        '''
        for n in super(ElementTree, self).__iter__():
            for el in n.payload:
                yield el

    def __len__(self):
        r'''
        Gets the length of the ElementTree collection, i.e., the number of elements enclosed.

        >>> tree = timespans.trees.ElementTree()
        >>> len(tree)
        0

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [note.Note() for _ in tsList]
        >>> for i,n in enumerate(tss):
        ...     n.offset, n.quarterLength = tsList[i]
        >>> tree.insert(tss)
        >>> len(tree)
        10
        >>> len(tree) == len(tss)
        True

        >>> tree.remove(tss)
        >>> len(tree)
        0
        '''
        if self.rootNode is None:
            return 0
        return self.rootNode.subtreeElementsStopIndex

    def __ne__(self, expr):
        return not self == expr

    def __repr__(self):
        o = self.origin
        if o is None:
            return '<{} {{{}}} ({!r} to {!r})>'.format(
                type(self).__name__,
                len(self),
                self.offset,
                self.endTime,
                )
        else:
            return '<{} {{{}}} ({!r} to {!r}) {!s}>'.format(
                type(self).__name__,
                len(self),
                self.offset,
                self.endTime,
                repr(o),
                )

    def __setitem__(self, i, new):
        r'''
        Sets timespans at index `i` to `new`.

        >>> tss = [
        ...     timespans.spans.Timespan(0, 2),
        ...     timespans.spans.Timespan(0, 9),
        ...     timespans.spans.Timespan(1, 1),
        ...     ]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)
        >>> tree[0] = timespans.spans.Timespan(-1, 6)
        >>> for x in tree:
        ...     x
        <Timespan -1.0 6.0>
        <Timespan 0.0 9.0>
        <Timespan 1.0 1.0>

        Works with slices too.

        >>> tree[1:] = [timespans.spans.Timespan(10, 20)]
        >>> for x in tree:
        ...     x
        <Timespan -1.0 6.0>
        <Timespan 10.0 20.0>
        '''
        if isinstance(i, (int, slice)):
            old = self[i]
            self.remove(old)
            self.insert(new)
        else:
            message = 'Indices must be ints or slices, got {}'.format(i)
            raise TypeError(message)

    def __str__(self):
        result = []
        result.append(repr(self))
        for x in self:
            subresult = str(x).splitlines()
            subresult = ['\t' + x for x in subresult]
            result.extend(subresult)
        result = '\n'.join(result)
        return result

    ### PRIVATE METHODS ###
    def _updateIndices(self, node):
        r'''
        Traverses the tree structure and updates cached indices which keep
        track of the index of the elements stored at each node, and of the
        maximum and minimum indices of the subtrees rooted at each node.

        Indices keep track of the order of the elements in the Payload, not the
        order of nodes.

        Used internally by ElementTree.

        Returns None.
        '''
        def recurseUpdateIndices(node, parentStopIndex=None):
            if node is None:
                return
            if node.leftChild is not None:
                recurseUpdateIndices(
                    node.leftChild,
                    parentStopIndex=parentStopIndex,
                    )
                node.payloadElementsStartIndex = node.leftChild.subtreeElementsStopIndex
                node.subtreeElementsStartIndex = node.leftChild.subtreeElementsStartIndex
            elif parentStopIndex is None:
                node.payloadElementsStartIndex = 0
                node.subtreeElementsStartIndex = 0
            else:
                node.payloadElementsStartIndex = parentStopIndex
                node.subtreeElementsStartIndex = parentStopIndex
            node.payloadElementsStopIndex = node.payloadElementsStartIndex + len(node.payload)
            node.subtreeElementsStopIndex = node.payloadElementsStopIndex
            if node.rightChild is not None:
                recurseUpdateIndices(
                    node.rightChild,
                    parentStopIndex=node.payloadElementsStopIndex,
                    )
                node.subtreeElementsStopIndex = node.rightChild.subtreeElementsStopIndex
        recurseUpdateIndices(node)

    def _updateEndTimes(self, node):
        r'''
        Traverses the tree structure and updates cached maximum and minimum
        endTime values for the subtrees rooted at each node.

        Used internally by TimespanTree.

        Returns a node.
        '''
        if node is None:
            return
        try:
            endTimeLow = min(x.endTime for x in node.payload)
            endTimeHigh = max(x.endTime for x in node.payload)
        except AttributeError: # elements do not have endTimes. do NOT mix elements and timespans.
            endTimeLow = node.position + min(x.duration.quarterLength for x in node.payload)
            endTimeHigh = node.position + max(x.duration.quarterLength for x in node.payload)            
        if node.leftChild:
            leftChild = self._updateEndTimes(node.leftChild)
            if leftChild.endTimeLow < endTimeLow:
                endTimeLow = leftChild.endTimeLow
            if endTimeHigh < leftChild.endTimeHigh:
                endTimeHigh = leftChild.endTimeHigh
        if node.rightChild:
            rightChild = self._updateEndTimes(node.rightChild)
            if rightChild.endTimeLow < endTimeLow:
                endTimeLow = rightChild.endTimeLow
            if endTimeHigh < rightChild.endTimeHigh:
                endTimeHigh = rightChild.endTimeHigh
        node.endTimeLow = endTimeLow
        node.endTimeHigh = endTimeHigh
        return node

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
            parent._removeElement(self, oldPosition=oldPosition)
            parent._insertCore(self.offset, self)
            parent._updateIndices(parent.rootNode)
            parent._updateEndTimes(parent.rootNode)
            parent._updateParents(parentPosition, visitedParents=visitedParents)

    def _removeElement(self, element, oldPosition=None):
        '''
        removes an element or ElementTree from a position 
        (either its current .offset or its oldPosition) without updating
        the indices, endTimes, etc.  
        '''
        if oldPosition is not None:
            position = oldPosition
        else:
            position = element.offset

        node = self.getNodeByPosition(position)
        if node is None:
            return
        if element in node.payload:
            node.payload.remove(element)
        if not node.payload:
            self.removeNode(position)

        if isinstance(element, ElementTree): # represents an embedded Stream
            for pt in element.parentTrees:
                pt.remove(self)

    ### PUBLIC METHODS ###

    def copy(self):
        r'''
        Creates a new offset-tree with the same payload as this offset-tree.
        
        This is analogous to `dict.copy()`.  

        >>> score = timespans.makeExampleScore()
        >>> tree = score.asTimespans()
        >>> newTree = tree.copy()
        >>> newTree
        <TimespanTree {12} (0.0 to 8.0)>

        >>> tree[4]
        <PitchedTimespan (2.0 to 4.0) <music21.note.Note G>>
        >>> newTree[4]
        <PitchedTimespan (2.0 to 4.0) <music21.note.Note G>>
        
        >>> tree[4] is newTree[4]
        True
        '''
        newTree = type(self)()
        # this is just as efficient as ._insertCore, since it's given a list.
        newTree.insert([x for x in self])
        return newTree

    def elementsStartingAt(self, offset):
        r'''
        Finds timespans in this offset-tree which start at `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for timespan in tree.elementsStartingAt(0.5):
        ...     timespan
        ...
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note G#>>
        '''
        results = []
        node = self.getNodeByPosition(offset)
        if node is not None:
            results.extend(node.payload)
        return tuple(results)

    def elementsStoppingAt(self, offset):
        r'''
        Finds timespans in this offset-tree which stop at `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for timespan in tree.elementsStoppingAt(0.5):
        ...     timespan
        ...
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
        '''
        def recurse(node, offset):
            result = []
            if node is not None: # could happen in an empty TimespanTree
                if node.endTimeLow <= offset <= node.endTimeHigh:
                    for timespan in node.payload:
                        if timespan.endTime == offset:
                            result.append(timespan)
                    if node.leftChild is not None:
                        result.extend(recurse(node.leftChild, offset))
                    if node.rightChild is not None:
                        result.extend(recurse(node.rightChild, offset))
            return result
        
        results = recurse(self.rootNode, offset)
        results.sort(key=lambda x: (x.offset, x.endTime))
        return tuple(results)

    def elementsOverlappingOffset(self, offset):
        r'''
        Finds elements or timespans in this ElementTree which overlap `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for el in tree.elementsOverlappingOffset(0.5):
        ...     el
        ...
        <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>
        '''
        def recurse(node, offset, indent=0):
            result = []
            if node is not None:
                if node.position < offset < node.endTimeHigh:
                    result.extend(recurse(node.leftChild, offset, indent + 1))
                    for timespan in node.payload:
                        if offset < timespan.endTime:
                            result.append(timespan)
                    result.extend(recurse(node.rightChild, offset, indent + 1))
                elif offset <= node.position:
                    result.extend(recurse(node.leftChild, offset, indent + 1))
            return result
        results = recurse(self.rootNode, offset)
        #if len(results) > 0 and hasattr(results[0], 'element'):
        #    results.sort(key=lambda x: (x.offset, x.endTime, x.element.sortTuple()[1:]))
        #else:
        results.sort(key=lambda x: (x.offset, x.endTime))
        return tuple(results)

    def index(self, element, offset=None):
        r'''
        Gets index of `timespan` in tree.
        
        Since timespans do not have .sites, there is only one offset to deal with...

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> ts = [timespans.spans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(ts)

        >>> for timespan in ts:
        ...     print("%r %d" % (timespan, tree.index(timespan)))
        ...
        <Timespan 0.0 2.0> 0
        <Timespan 0.0 9.0> 1
        <Timespan 1.0 1.0> 2
        <Timespan 2.0 3.0> 3
        <Timespan 3.0 4.0> 4
        <Timespan 4.0 9.0> 5
        <Timespan 5.0 6.0> 6
        <Timespan 5.0 8.0> 7
        <Timespan 6.0 8.0> 8
        <Timespan 7.0 7.0> 9

        >>> tree.index(timespans.spans.Timespan(-100, 100))
        Traceback (most recent call last):
        ValueError: <Timespan -100.0 100.0> not in Tree at offset -100.0.
        '''
        if offset is None:
            offset = element.offset
        node = self.getNodeByPosition(offset)
        if node is None or element not in node.payload:
            raise ValueError('{} not in Tree at offset {}.'.format(element, offset))
        index = node.payload.index(element) + node.payloadElementsStartIndex
        return index

    def remove(self, elements, offsets=None, runUpdate=True): 
        r'''
        Removes `elements` which can be Music21Objects or Timespans 
        (a single one or a list) from this Tree.
        
        Much safer (for non-timespans) if a list of offsets is used but it is optional
        
        If runUpdate is False then the tree will be left with incorrect indices and
        endTimes; but it can speed up operations where an element is going to be removed
        and then immediately replaced: i.e., where the position of an element has changed        
        '''
        initialPosition = self.offset
        initialEndTime = self.endTime
        if hasattr(elements, 'offset'): # a music21 object or an PitchedTimespan
            elements = [elements]
        if offsets is not None and not common.isListLike(offsets):
            offsets = [offsets]
        
        if offsets is not None and len(elements) != len(offsets):
            raise TimespanTreeException(
                "Number of elements and number of offsets must be the same")

        
        for i, el in enumerate(elements):
            if offsets is not None:
                self._removeElement(el, offsets[i]) 
            else:
                self._removeElement(el)
        
        if runUpdate:
            self._updateIndices(self.rootNode)
            self._updateEndTimes(self.rootNode)
            if (self.offset != initialPosition or
                    self.endTime != initialEndTime):
                self._updateParents(initialPosition)

    def insert(self, offsetsOrElements, elements=None):
        r'''
        Inserts elements or `timespans` into this offset-tree.
        
        >>> n = note.Note()
        >>> et = timespans.trees.ElementTree()
        >>> et.insert(10.0, n)
        >>> et
        <ElementTree {1} (10.0 to 11.0)>
        
        >>> n2 = note.Note('D')
        >>> n2.offset = 20
        >>> n3 = note.Note('E')
        >>> n3.offset = 5
        >>> et.insert([n2, n3])
        >>> et
        <ElementTree {3} (5.0 to 21.0)>
        '''
        initialPosition = self.offset
        initialEndTime = self.endTime
        if elements is None:
            elements = offsetsOrElements
            offsets = None
        else:
            offsets = offsetsOrElements
            if not common.isListLike(offsets):
                offsets = [offsets]
        
        if (not common.isListLike(elements) and
                not isinstance(elements, (set, frozenset))
                ): # not a list. a single element or timespan
            elements = [elements]
        if offsets is None:
            offsets = [el.offset for el in elements]
                
        
        for i, el in enumerate(elements):
            self._insertCore(offsets[i], el)
        self._updateIndices(self.rootNode)
        self._updateEndTimes(self.rootNode)
        if (self.offset != initialPosition or 
                self.endTime != initialEndTime):
            self._updateParents(initialPosition)

    def _insertCore(self, offset, el):
        '''
        Inserts a single element at an offset, creating new nodes as necessary,
        but does not updateIndices or updateEndTimes or updateParents
        '''
        def key(x):
            try:
                return x.sortTuple()[2:] # cut off atEnd and offset
            except AttributeError:
                if hasattr(x, 'element'):
                    return x.element.sortTuple()[2:]
                elif isinstance(x, TimespanTree) and x.origin is not None:
                    return x.origin.sortTuple()[2:]
                else:
                    return x.endTime  # PitchedTimespan with no Element!
                
        self.createNodeAtPosition(offset)
        node = self.getNodeByPosition(offset)
        node.payload.append(el)
        node.payload.sort(key=key)
        if isinstance(el, TimespanTree):
            el.parentTrees.add(self)

    def append(self, el):
        initialPosition = self.offset # will only change if is empty
        endTime = self.latestEndTime
        if endTime == INFINITY:
            endTime = 0
        self._insertCore(endTime, el)
        self._updateIndices(self.rootNode)
        self._updateEndTimes(self.rootNode)
        self._updateParents(initialPosition)

    ### PROPERTIES ###
    @property
    def offset(self):
        return self.lowestOffset

    @property
    def endTime(self):
        return self.latestEndTime

    @property
    def origin(self):
        '''
        the original stream. (stored as a weakref)
        '''
        return common.unwrapWeakref(self._origin)
        
    @origin.setter
    def origin(self, expr):
        # uses weakrefs so that garbage collection on the stream cache is possible...
        self._origin = common.wrapWeakref(expr)


    @property
    def lowestOffset(self):
        r'''
        Gets the earliest start offset in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.lowestOffset
        0.0
        '''
        def recurse(node):
            if node.leftChild is not None:
                return recurse(node.leftChild)
            return node.position
        if self.rootNode is not None:
            return recurse(self.rootNode)
        return NEGATIVE_INFINITY

    @property
    def earliestEndTime(self):
        r'''
        Gets the earliest stop offset in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.earliestEndTime
        0.5
        '''
        if self.rootNode is not None:
            return self.rootNode.endTimeLow
        return INFINITY

    @property
    def highestOffset(self):
        r'''
        Gets the latest start offset in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.highestOffset
        35.0
        '''
        def recurse(node):
            if node.rightChild is not None:
                return recurse(node.rightChild)
            return node.position
        if self.rootNode is not None:
            return recurse(self.rootNode)
        return NEGATIVE_INFINITY

    @property
    def latestEndTime(self):
        r'''
        Gets the latest stop offset in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.latestEndTime
        36.0
        '''
        if self.rootNode is not None:
            return self.rootNode.endTimeHigh
        return INFINITY


    @property
    def allOffsets(self):
        r'''
        Gets all unique offsets of all timespans in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for offset in tree.allOffsets[:10]:
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
                result.append(node.position)
                if node.rightChild is not None:
                    result.extend(recurse(node.rightChild))
            return result
        return tuple(recurse(self.rootNode))

    @property
    def allTimePoints(self):
        r'''
        Gets all unique offsets (both starting and stopping) of all elements/timespans
        in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for offset in tree.allTimePoints[:10]:
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
                result.add(node.endTimeLow)
                result.add(node.endTimeHigh)
                if node.rightChild is not None:
                    result.update(recurse(node.rightChild))
            return result
        return tuple(sorted(recurse(self.rootNode)))

    @property
    def allEndTimes(self):
        r'''
        Gets all unique stop offsets of all timespans in this offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for offset in tree.allEndTimes[:10]:
        ...     offset
        ...
        0.5
        1.0
        2.0
        4.0
        5.5
        6.0
        7.0
        8.0
        9.5
        10.5
        '''
        def recurse(node):
            result = set()
            if node is not None:
                if node.leftChild is not None:
                    result.update(recurse(node.leftChild))
                result.add(node.endTimeLow)
                result.add(node.endTimeHigh)
                if node.rightChild is not None:
                    result.update(recurse(node.rightChild))
            return result
        return tuple(sorted(recurse(self.rootNode)))

#----------------------------------------------------------------

class TimespanTree(ElementTree):
    r'''
    A data structure for efficiently slicing a score for pitches.

    While you can construct an TimespanTree by hand, inserting timespans one at
    a time, the common use-case is to construct the offset-tree from an entire
    score at once:

    >>> bach = corpus.parse('bwv66.6')
    >>> tree = timespans.fromStream.convert(bach, flatten=True, 
    ...            classList=(note.Note, chord.Chord))
    >>> print(tree.getVerticalityAt(17.0))
    <Verticality 17.0 {F#3 C#4 A4}>

    All offsets are assumed to be relative to the score's origin if flatten is True

    Example: How many moments in Bach are consonant and how many are dissonant:

    >>> totalConsonances = 0
    >>> totalDissonances = 0
    >>> for v in tree.iterateVerticalities():
    ...     if v.toChord().isConsonant():
    ...        totalConsonances += 1
    ...     else:
    ...        totalDissonances += 1
    >>> (totalConsonances, totalDissonances)
    (34, 17)

    So 1/3 of the vertical moments in Bach are dissonant!  But is this an
    accurate perception? Let's sum up the total consonant duration vs.
    dissonant duration.

    Do it again pairwise to figure out the length (actually this won't include
    the last element)

    >>> totalConsonanceDuration = 0
    >>> totalDissonanceDuration = 0
    >>> iterator = tree.iterateVerticalitiesNwise(n=2)
    >>> for verticality1, verticality2 in iterator:
    ...     offset1 = verticality1.offset
    ...     offset2 = verticality2.offset
    ...     quarterLength = offset2 - offset1
    ...     if verticality1.toChord().isConsonant():
    ...        totalConsonanceDuration += quarterLength
    ...     else:
    ...        totalDissonanceDuration += quarterLength
    >>> (totalConsonanceDuration, totalDissonanceDuration)
    (25.5, 9.5)

    Remove neighbor tones from the Bach chorale.  (It's actually quite viscous
    in its pruning...)
 
    Here in Alto, measure 7, there's a neighbor tone E#.
 
    >>> bach.parts['Alto'].measure(7).show('text')
    {0.0} <music21.note.Note F#>
    {0.5} <music21.note.Note E#>
    {1.0} <music21.note.Note F#>
    {1.5} <music21.note.Note F#>
    {2.0} <music21.note.Note C#>
 
    We'll get rid of it and a lot of other neighbor tones.
 
    >>> for verticalities in tree.iterateVerticalitiesNwise(n=3):
    ...     horizontalities = tree.unwrapVerticalities(verticalities)
    ...     for unused_part, horizontality in horizontalities.items():
    ...         if horizontality.hasNeighborTone:
    ...             merged = horizontality[0].new(
    ...                endTime=horizontality[2].endTime,
    ...             ) # merged is a new PitchedTimespan
    ...             tree.remove(horizontality[0])
    ...             tree.remove(horizontality[1])
    ...             tree.remove(horizontality[2])
    ...             tree.insert(merged)
     
     
    >>> newBach = timespans.toStream.partwise(
    ...     tree,
    ...     templateStream=bach,
    ...     )
    >>> newBach.parts[1].measure(7).show('text')
    {0.0} <music21.chord.Chord F#4>
    {1.5} <music21.chord.Chord F#3>
    {2.0} <music21.chord.Chord C#4>
 
    The second F# is an octave lower, so it wouldn't get merged even if
    adjacent notes were fused together (which they're not).
    
    
    TODO: newBach.parts['Alto'].measure(7).show('text') should work.
    KeyError: 'provided key (Alto) does not match any id or group'

    ..  note::

        TimespanTree is an implementation of an extended AVL tree. AVL
        trees are a type of binary tree, like Red-Black trees. AVL trees are
        very efficient at insertion when the objects being inserted are already
        sorted - which is usually the case with data extracted from a score.
        TimespanTree is an extended AVL tree because each node in the
        tree keeps track of not just the start offsets of PitchedTimespans
        stored at that node, but also the earliest and latest stop offset of
        all PitchedTimespans stores at both that node and all nodes which are
        children of that node. This lets us quickly located PitchedTimespans
        which overlap offsets or which are contained within ranges of offsets.
        This also means that the contents of a TimespanTree are always
        sorted.

    OMIT_FROM_DOCS
    

    TODO: Doc examples for all functions, including privates.
    '''
    __slots__ = ()
    ### PUBLIC METHODS ###
    def __init__(self, elements=None, origin=None):
        super(TimespanTree, self).__init__(elements, origin=origin)
    
    
    def findNextPitchedTimespanInSameStreamByClass(self, pitchedTimespan, classList=None):
        r'''
        Finds next element timespan in the same stream class as `PitchedTimespan`.
        
        Default classList is (stream.Part, )

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> timespan = tree[0]
        >>> timespan
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>

        >>> timespan.part
        <music21.stream.Part Soprano>

        >>> timespan = tree.findNextPitchedTimespanInSameStreamByClass(timespan)
        >>> timespan
        <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>

        >>> timespan.part
        <music21.stream.Part Soprano>

        >>> timespan = tree.findNextPitchedTimespanInSameStreamByClass(timespan)
        >>> timespan
        <PitchedTimespan (1.0 to 2.0) <music21.note.Note A>>

        >>> timespan.part
        <music21.stream.Part Soprano>
        '''
        if not isinstance(pitchedTimespan, spans.PitchedTimespan):
            message = 'PitchedTimespan {!r}, must be an PitchedTimespan'.format(pitchedTimespan)
            raise TimespanTreeException(message)
        verticality = self.getVerticalityAt(pitchedTimespan.offset)
        while verticality is not None:
            verticality = verticality.nextVerticality
            if verticality is None:
                return None
            for nextPitchedTimespan in verticality.startTimespans:
                if (nextPitchedTimespan.getParentageByClass(classList) is 
                        pitchedTimespan.getParentageByClass(classList)):
                    return nextPitchedTimespan

    def findPreviousPitchedTimespanInSameStreamByClass(self, pitchedTimespan, classList=None):
        r'''
        Finds next element timespan in the same Part/Measure, etc. (specify in classList) as 
        the `pitchedTimespan`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> timespan = tree[-1]
        >>> timespan
        <PitchedTimespan (35.0 to 36.0) <music21.note.Note F#>>

        >>> timespan.part
        <music21.stream.Part Bass>

        >>> timespan = tree.findPreviousPitchedTimespanInSameStreamByClass(timespan)
        >>> timespan
        <PitchedTimespan (34.0 to 35.0) <music21.note.Note B>>

        >>> timespan.part
        <music21.stream.Part Bass>

        >>> timespan = tree.findPreviousPitchedTimespanInSameStreamByClass(timespan)
        >>> timespan
        <PitchedTimespan (33.0 to 34.0) <music21.note.Note D>>

        >>> timespan.part
        <music21.stream.Part Bass>
        '''
        if not isinstance(pitchedTimespan, spans.PitchedTimespan):
            message = 'PitchedTimespan {!r}, must be an PitchedTimespan'.format(
                pitchedTimespan)
            raise TimespanTreeException(message)
        verticality = self.getVerticalityAt(pitchedTimespan.offset)
        while verticality is not None:
            verticality = verticality.previousVerticality
            if verticality is None:
                return None
            for previousPitchedTimespan in verticality.startTimespans:
                if (previousPitchedTimespan.getParentageByClass(classList) is 
                        pitchedTimespan.getParentageByClass(classList)):
                    return previousPitchedTimespan

    def getVerticalityAt(self, offset):
        r'''
        Gets the verticality in this offset-tree which starts at `offset`.

        >>> bach = corpus.parse('bwv66.6')
        >>> tree = bach.asTimespans()
        >>> tree.getVerticalityAt(2.5)
        <Verticality 2.5 {G#3 B3 E4 B4}>

        Verticalities outside the range still return a Verticality, but it might be empty...

        >>> tree.getVerticalityAt(2000)
        <Verticality 2000 {}>
            
        Test that it still works if the tree is empty...
            
        >>> tree = bach.asTimespans(classList=(instrument.Tuba,))
        >>> tree
        <TimespanTree {0} (-inf to inf) <music21.stream.Score ...>>
        >>> tree.getVerticalityAt(5.0)
        <Verticality 5.0 {}>           

        Returns a verticality.Verticality object.
        '''
        from music21.timespans.verticality import Verticality
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

    def getVerticalityAtOrBefore(self, offset):
        r'''
        Gets the verticality in this offset-tree which starts at `offset`.

        If the found verticality has no start timespans, the function returns
        the next previous verticality with start timespans.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.getVerticalityAtOrBefore(0.125)
        <Verticality 0.0 {A3 E4 C#5}>

        >>> tree.getVerticalityAtOrBefore(0.)
        <Verticality 0.0 {A3 E4 C#5}>
        '''
        verticality = self.getVerticalityAt(offset)
        if not verticality.startTimespans:
            verticality = verticality.previousVerticality
        return verticality
    
    def iterateConsonanceBoundedVerticalities(self):
        r'''
        Iterates consonant-bounded verticality subsequences in this
        offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> for subsequence in tree.iterateConsonanceBoundedVerticalities():
        ...     print('Subequence:')
        ...     for verticality in subsequence:
        ...         print('\t[{}] {}: {} [{}]'.format(
        ...             verticality.measureNumber,
        ...             verticality,
        ...             verticality.isConsonant,
        ...             verticality.beatStrength,
        ...             ))
        ...
        Subequence:
            [2] <Verticality 6.0 {E3 E4 G#4 B4}>: True [0.25]
            [2] <Verticality 6.5 {E3 D4 G#4 B4}>: False [0.125]
            [2] <Verticality 7.0 {A2 C#4 E4 A4}>: True [0.5]
        Subequence:
            [3] <Verticality 9.0 {F#3 C#4 F#4 A4}>: True [1.0]
            [3] <Verticality 9.5 {B2 D4 G#4 B4}>: False [0.125]
            [3] <Verticality 10.0 {C#3 C#4 E#4 G#4}>: True [0.25]
        Subequence:
            [3] <Verticality 10.0 {C#3 C#4 E#4 G#4}>: True [0.25]
            [3] <Verticality 10.5 {C#3 B3 E#4 G#4}>: False [0.125]
            [3] <Verticality 11.0 {F#2 A3 C#4 F#4}>: True [0.5]
        Subequence:
            [3] <Verticality 12.0 {F#3 C#4 F#4 A4}>: True [0.25]
            [4] <Verticality 13.0 {G#3 B3 F#4 B4}>: False [1.0]
            [4] <Verticality 13.5 {F#3 B3 F#4 B4}>: False [0.125]
            [4] <Verticality 14.0 {G#3 B3 E4 B4}>: True [0.25]
        Subequence:
            [4] <Verticality 14.0 {G#3 B3 E4 B4}>: True [0.25]
            [4] <Verticality 14.5 {A3 B3 E4 B4}>: False [0.125]
            [4] <Verticality 15.0 {B3 D#4 F#4}>: True [0.5]
        Subequence:
            [4] <Verticality 15.0 {B3 D#4 F#4}>: True [0.5]
            [4] <Verticality 15.5 {B2 A3 D#4 F#4}>: False [0.125]
            [4] <Verticality 16.0 {C#3 G#3 C#4 E4}>: True [0.25]
        Subequence:
            [5] <Verticality 17.5 {F#3 D4 F#4 A4}>: True [0.125]
            [5] <Verticality 18.0 {G#3 C#4 E4 B4}>: False [0.25]
            [5] <Verticality 18.5 {G#3 B3 E4 B4}>: True [0.125]
        Subequence:
            [6] <Verticality 24.0 {F#3 C#4 F#4 A4}>: True [0.25]
            [7] <Verticality 25.0 {B2 D4 F#4 G#4}>: False [1.0]
            [7] <Verticality 25.5 {C#3 C#4 E#4 G#4}>: True [0.125]
        Subequence:
            [7] <Verticality 25.5 {C#3 C#4 E#4 G#4}>: True [0.125]
            [7] <Verticality 26.0 {D3 C#4 F#4}>: False [0.25]
            [7] <Verticality 26.5 {D3 F#3 B3 F#4}>: True [0.125]
        Subequence:
            [8] <Verticality 29.0 {A#2 F#3 C#4 F#4}>: True [1.0]
            [8] <Verticality 29.5 {A#2 F#3 D4 F#4}>: False [0.125]
            [8] <Verticality 30.0 {A#2 C#4 E4 F#4}>: False [0.25]
            [8] <Verticality 31.0 {B2 C#4 E4 F#4}>: False [0.5]
            [8] <Verticality 32.0 {C#3 B3 D4 F#4}>: False [0.25]
            [8] <Verticality 32.5 {C#3 A#3 C#4 F#4}>: False [0.125]
            [9] <Verticality 33.0 {D3 B3 F#4}>: True [1.0]
        Subequence:
            [9] <Verticality 33.0 {D3 B3 F#4}>: True [1.0]
            [9] <Verticality 33.5 {D3 B3 C#4 F#4}>: False [0.125]
            [9] <Verticality 34.0 {B2 B3 D4 F#4}>: True [0.25]
        Subequence:
            [9] <Verticality 34.0 {B2 B3 D4 F#4}>: True [0.25]
            [9] <Verticality 34.5 {B2 B3 D4 E#4}>: False [0.125]
            [9] <Verticality 35.0 {F#3 A#3 C#4 F#4}>: True [0.5]
        '''
        iterator = self.iterateVerticalities()
        startingVerticality = next(iterator)
        while not startingVerticality.isConsonant:
            startingVerticality = next(iterator)
        verticalityBuffer = [startingVerticality]
        for verticality in iterator:
            verticalityBuffer.append(verticality)
            if verticality.isConsonant:
                if 2 < len(verticalityBuffer):
                    yield tuple(verticalityBuffer)
                verticalityBuffer = [verticality]

    def iterateVerticalities(
        self,
        reverse=False,
        ):
        r'''
        Iterates all vertical moments in this offset-tree.

        ..  note:: The offset-tree can be mutated while its verticalities are
            iterated over. Each verticality holds a reference back to the
            offset-tree and will ask for the start-offset after (or before) its
            own start offset in order to determine the next verticality to
            yield. If you mutate the tree by adding or deleting timespans, the
            next verticality will reflect those changes.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> iterator = tree.iterateVerticalities()
        >>> for _ in range(10):
        ...     next(iterator)
        ...
        <Verticality 0.0 {A3 E4 C#5}>
        <Verticality 0.5 {G#3 B3 E4 B4}>
        <Verticality 1.0 {F#3 C#4 F#4 A4}>
        <Verticality 2.0 {G#3 B3 E4 B4}>
        <Verticality 3.0 {A3 E4 C#5}>
        <Verticality 4.0 {G#3 B3 E4 E5}>
        <Verticality 5.0 {A3 E4 C#5}>
        <Verticality 5.5 {C#3 E4 A4 C#5}>
        <Verticality 6.0 {E3 E4 G#4 B4}>
        <Verticality 6.5 {E3 D4 G#4 B4}>

        Verticalities can also be iterated in reverse:

        >>> iterator = tree.iterateVerticalities(reverse=True)
        >>> for _ in range(10):
        ...     next(iterator)
        ...
        <Verticality 35.0 {F#3 A#3 C#4 F#4}>
        <Verticality 34.5 {B2 B3 D4 E#4}>
        <Verticality 34.0 {B2 B3 D4 F#4}>
        <Verticality 33.5 {D3 B3 C#4 F#4}>
        <Verticality 33.0 {D3 B3 F#4}>
        <Verticality 32.5 {C#3 A#3 C#4 F#4}>
        <Verticality 32.0 {C#3 B3 D4 F#4}>
        <Verticality 31.0 {B2 C#4 E4 F#4}>
        <Verticality 30.0 {A#2 C#4 E4 F#4}>
        <Verticality 29.5 {A#2 F#3 D4 F#4}>
        '''
        if reverse:
            offset = self.highestOffset
            verticality = self.getVerticalityAt(offset)
            yield verticality
            verticality = verticality.previousVerticality
            while verticality is not None:
                yield verticality
                verticality = verticality.previousVerticality
        else:
            offset = self.lowestOffset
            verticality = self.getVerticalityAt(offset)
            yield verticality
            verticality = verticality.nextVerticality
            while verticality is not None:
                yield verticality
                verticality = verticality.nextVerticality

    def iterateVerticalitiesNwise(
        self, n=3, reverse=False,):
        r'''
        Iterates verticalities in groups of length `n`.

        ..  note:: The offset-tree can be mutated while its verticalities are
            iterated over. Each verticality holds a reference back to the
            offset-tree and will ask for the start-offset after (or before) its
            own start offset in order to determine the next verticality to
            yield. If you mutate the tree by adding or deleting timespans, the
            next verticality will reflect those changes.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> iterator = tree.iterateVerticalitiesNwise(n=2)
        >>> for _ in range(4):
        ...     print(next(iterator))
        ...
        <VerticalitySequence: [
            <Verticality 0.0 {A3 E4 C#5}>,
            <Verticality 0.5 {G#3 B3 E4 B4}>
            ]>
        <VerticalitySequence: [
            <Verticality 0.5 {G#3 B3 E4 B4}>,
            <Verticality 1.0 {F#3 C#4 F#4 A4}>
            ]>
        <VerticalitySequence: [
            <Verticality 1.0 {F#3 C#4 F#4 A4}>,
            <Verticality 2.0 {G#3 B3 E4 B4}>
            ]>
        <VerticalitySequence: [
            <Verticality 2.0 {G#3 B3 E4 B4}>,
            <Verticality 3.0 {A3 E4 C#5}>
            ]>

        Grouped verticalities can also be iterated in reverse:

        >>> iterator = tree.iterateVerticalitiesNwise(n=2, reverse=True)
        >>> for _ in range(4):
        ...     print(next(iterator))
        ...
        <VerticalitySequence: [
            <Verticality 34.5 {B2 B3 D4 E#4}>,
            <Verticality 35.0 {F#3 A#3 C#4 F#4}>
            ]>
        <VerticalitySequence: [
            <Verticality 34.0 {B2 B3 D4 F#4}>,
            <Verticality 34.5 {B2 B3 D4 E#4}>
            ]>
        <VerticalitySequence: [
            <Verticality 33.5 {D3 B3 C#4 F#4}>,
            <Verticality 34.0 {B2 B3 D4 F#4}>
            ]>
        <VerticalitySequence: [
            <Verticality 33.0 {D3 B3 F#4}>,
            <Verticality 33.5 {D3 B3 C#4 F#4}>
            ]>
        '''
        from music21.timespans.verticality import VerticalitySequence 
        n = int(n)
        if (n<=0):
            message = "The number of verticalities in the group must be at "
            message += "least one. Got {}".format(n)
            raise TimespanException(message)
        if reverse:
            for v in self.iterateVerticalities(reverse=True):
                verticalities = [v]
                while len(verticalities) < n:
                    nextVerticality = verticalities[-1].nextVerticality
                    if nextVerticality is None:
                        break
                    verticalities.append(nextVerticality)
                if len(verticalities) == n:
                    yield VerticalitySequence(verticalities)
        else:
            for v in self.iterateVerticalities():
                verticalities = [v]
                while len(verticalities) < n:
                    previousVerticality = verticalities[-1].previousVerticality
                    if previousVerticality is None:
                        break
                    verticalities.append(previousVerticality)
                if len(verticalities) == n:
                    yield VerticalitySequence(reversed(verticalities))

    def splitAt(self, offsets):
        r'''
        Splits all timespans in this offset-tree at `offsets`, operating in
        place.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.elementsStartingAt(0.1)
        ()

        >>> for timespan in tree.elementsOverlappingOffset(0.1):
        ...     print("%r, %s" % (timespan, timespan.part.id))
        ...
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>, Soprano
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>, Tenor
        <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>, Bass
        <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>, Alto

        >>> tree.splitAt(0.1)
        >>> for timespan in tree.elementsStartingAt(0.1):
        ...     print("%r, %s" % (timespan, timespan.part.id))
        ...
        <PitchedTimespan (0.1 to 0.5) <music21.note.Note C#>>, Soprano
        <PitchedTimespan (0.1 to 1.0) <music21.note.Note E>>, Alto
        <PitchedTimespan (0.1 to 0.5) <music21.note.Note A>>, Tenor
        <PitchedTimespan (0.1 to 0.5) <music21.note.Note A>>, Bass

        >>> tree.elementsOverlappingOffset(0.1)
        ()
        '''
        if not isinstance(offsets, collections.Iterable):
            offsets = [offsets]
        for offset in offsets:
            overlaps = self.elementsOverlappingOffset(offset)
            if not overlaps:
                continue
            for overlap in overlaps:
                self.remove(overlap)
                shards = overlap.splitAt(offset)
                self.insert(shards)

    def toPartwiseTimespanTrees(self):
        '''
        Returns a dictionary of TimespanTrees where each entry
        is indexed by a Part object (TODO: Don't use mutable objects as hash keys!)
        and each key is a TimeSpan tree containing only element timespans belonging
        to that part.
        
        Used by reduceChords.  May disappear.
        '''
        partwiseTimespanTrees = {}
        for part in self.allParts:
            partwiseTimespanTrees[part] = TimespanTree()
        for timespan in self:
            partwiseTimespanTree = partwiseTimespanTrees[timespan.part]
            partwiseTimespanTree.insert(timespan)
        return partwiseTimespanTrees

    @staticmethod
    def unwrapVerticalities(verticalities):
        r'''
        Unwraps a sequence of `Verticality` objects into a dictionary of
        `Part`:`Horizontality` key/value pairs.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> iterator = tree.iterateVerticalitiesNwise()
        >>> verticalities = next(iterator)
        >>> unwrapped = tree.unwrapVerticalities(verticalities)
        >>> for part in sorted(unwrapped,
        ...     key=lambda x: x.partName,
        ...     ):
        ...     print(part)
        ...     horizontality = unwrapped[part]
        ...     for timespan in horizontality:
        ...         print('\t%r' % timespan)
        ...
        <music21.stream.Part Alto>
            <PitchedTimespan (0.0 to 1.0) <music21.note.Note E>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note F#>>
        <music21.stream.Part Bass>
            <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
            <PitchedTimespan (0.5 to 1.0) <music21.note.Note G#>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note F#>>
        <music21.stream.Part Soprano>
            <PitchedTimespan (0.0 to 0.5) <music21.note.Note C#>>
            <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note A>>
        <music21.stream.Part Tenor>
            <PitchedTimespan (0.0 to 0.5) <music21.note.Note A>>
            <PitchedTimespan (0.5 to 1.0) <music21.note.Note B>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note C#>>
        '''
        from music21.timespans.verticality import VerticalitySequence 
        sequence = VerticalitySequence(verticalities)
        unwrapped = sequence.unwrap()
        return unwrapped

    ### PUBLIC PROPERTIES ###


    @property
    def allParts(self):
        parts = set()
        for timespan in self:
            parts.add(timespan.part)
        parts = sorted(parts, key=lambda x: x.getInstrument().partId)
        return parts



    @property
    def maximumOverlap(self):
        '''
        The maximum number of timespans overlapping at any given moment in this
        timespan collection.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.maximumOverlap
        4

        Returns None if there is no verticality here.
        '''
        overlap = None
        for v in self.iterateVerticalities():
            degreeOfOverlap = len(v.startTimespans) + len(v.overlapTimespans)
            if overlap is None:
                overlap = degreeOfOverlap
            elif overlap < degreeOfOverlap:
                overlap = degreeOfOverlap
        return overlap

    @property
    def minimumOverlap(self):
        '''
        The minimum number of timespans overlapping at any given moment in this
        timespan collection.

        In a tree created from a monophonic stream, the minimumOverlap will
        probably be either zero or one.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = timespans.fromStream.convert(
        ...     score, flatten=False, classList=(note.Note, chord.Chord))
        >>> tree[0].minimumOverlap
        1
        
        Returns None if there is no verticality here.
        '''
        overlap = None
        for v in self.iterateVerticalities():
            degreeOfOverlap = len(v.startTimespans) + len(v.overlapTimespans)
            if overlap is None:
                overlap = degreeOfOverlap
            elif degreeOfOverlap < overlap:
                overlap = degreeOfOverlap
        return overlap


    @property
    def element(self):
        '''
        defined so a TimespanTree can be used like an PitchedTimespan
        
        TODO: Look at subclassing or at least deriving from a common base...
        '''
        return common.unwrapWeakref(self._origin)
        
    @element.setter
    def element(self, expr):
        self._origin = common.wrapWeakref(expr)





#------------------------------------------------------------------------------

class TimespanTreeException(exceptions21.TimespanException):
    pass


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass
    
#     def testBachDoctest(self):
#         from music21 import corpus, note, chord, timespans
#         bach = corpus.parse('bwv66.6')
#         tree = timespans.fromStream.convert(bach, flatten=True, 
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
#         newBach = timespans.toStream.partwise(tree, templateStream=bach,)
#         newBach.parts[1].measure(7).show('text')
# #     {0.0} <music21.chord.Chord F#4>
# #     {1.5} <music21.chord.Chord F#3>
# #     {2.0} <music21.chord.Chord C#4>
# #         
    def testTimespanTree(self):
        from music21.timespans.spans import Timespan
        for attempt in range(100):
            starts = list(range(20))
            stops = list(range(20))
            random.shuffle(starts)
            random.shuffle(stops)
            tss = []
            for start, stop in zip(starts, stops):
                if start <= stop:
                    tss.append(Timespan(start, stop))
                else:
                    tss.append(Timespan(stop, start))
            tree = TimespanTree()

            for i, timespan in enumerate(tss):
                tree.insert(timespan)
                currentTimespansInList = list(sorted(tss[:i + 1],
                    key=lambda x: (x.offset, x.endTime)))
                currentTimespansInTree = [x for x in tree]
                currentPosition = min(
                    x.offset for x in currentTimespansInList)
                currentEndTime = max(
                    x.endTime for x in currentTimespansInList)
                
                self.assertEqual(currentTimespansInTree, 
                                 currentTimespansInList, 
                                 (attempt, currentTimespansInTree, currentTimespansInList))
                self.assertEqual(tree.rootNode.endTimeLow, 
                                 min(x.endTime for x in currentTimespansInList))
                self.assertEqual(tree.rootNode.endTimeHigh,
                                 max(x.endTime for x in currentTimespansInList))
                self.assertEqual(tree.offset, currentPosition)
                self.assertEqual(tree.endTime, currentEndTime)
                for i in range(len(currentTimespansInTree)):
                    self.assertEqual(currentTimespansInList[i], currentTimespansInTree[i])

            random.shuffle(tss)
            while tss:
                timespan = tss.pop()
                currentTimespansInList = sorted(tss,
                    key=lambda x: (x.offset, x.endTime))
                tree.remove(timespan)
                currentTimespansInTree = [x for x in tree]
                self.assertEqual(currentTimespansInTree, 
                                 currentTimespansInList, 
                                 (attempt, currentTimespansInTree, currentTimespansInList))
                if tree.rootNode is not None:
                    currentPosition = min(
                        x.offset for x in currentTimespansInList)
                    currentEndTime = max(
                        x.endTime for x in currentTimespansInList)
                    self.assertEqual(tree.rootNode.endTimeLow, 
                                     min(x.endTime for x in currentTimespansInList))
                    self.assertEqual(tree.rootNode.endTimeHigh,
                                     max(x.endTime for x in currentTimespansInList))
                    self.assertEqual(tree.offset, currentPosition)
                    self.assertEqual(tree.endTime, currentEndTime)

                    for i in range(len(currentTimespansInTree)):
                        self.assertEqual(currentTimespansInList[i], currentTimespansInTree[i])
                        

#     def testBachDoctest(self):
#         from music21 import corpus, note, chord, timespans
#         bach = corpus.parse('bwv66.6')
#         tree = timespans.fromStream.convert(bach, flatten=True, 
#                                               classList=(note.Note, chord.Chord))
#         print(tree)
#         for verticalities in tree.iterateVerticalitiesNwise(n=3):
#             if verticalities[-1].offset == 25:
#                 pass
#             horizontalities = tree.unwrapVerticalities(verticalities)
#             for unused_part, horizontality in horizontalities.items():
#                 if horizontality.hasNeighborTone:
#                     merged = horizontality[0].new(endTime=horizontality[2].endTime,)
#                     tree.remove(horizontality[0])
#                     tree.remove(horizontality[1])
#                     tree.remove(horizontality[2])
#                     tree.insert(merged)
#      
#     
#         newBach = timespans.toStream.partwise(tree, templateStream=bach,)
#         newBach.show()
#         newBach.parts[1].measure(7).show('text')
# #     {0.0} <music21.chord.Chord F#4>
# #     {1.5} <music21.chord.Chord F#3>
# #     {2.0} <music21.chord.Chord C#4>

#------------------------------------------------------------------------------


_DOC_ORDER = (
    ElementTree,
    TimespanTree,
    )


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
