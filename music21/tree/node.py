# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespans/node.py
# Purpose:      Internal data structures for timespan collections
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-14 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Internal data structures for timespan collections.

This is an implementation detail of the TimespanTree class.
'''

import unittest
from music21.tree import core
from music21.base import Music21Object
from music21.sorting import SortTuple
#------------------------------------------------------------------------------
class ElementNode(core.AVLNode):
    r'''
    A node containing an element, which is aware of the element's
    endTime and index within a stream, as well as the endTimes and indices of the
    elements to the left and right of it. 

    TODO: Specific ElementNode tests and docs.
    '''
    ### CLASS VARIABLES ###

    __slots__ = (
        'endTimeHigh',
        'endTimeLow',
        'payloadElementIndex',
        'subtreeElementsStartIndex',
        'subtreeElementsStopIndex',
        )

    _DOC_ATTR = {
    'payload': r'''
        The content of the node at this point.  Usually a Music21Object.
        ''',
        
    'payloadElementIndex': r'''
        The index in a stream of the element stored in the payload of this node.
        ''',

    'endTimeHigh': r'''
        The highest endTime of any node in the subtree rooted on this node.
        ''',
        
    'endTimeLow': r'''
        The lowest endTime of any node in the subtree rooted on this node.
        ''',               
        
    'subtreeElementsStartIndex': r'''
        The lowest element index of an element in the payload of any node of the
        subtree rooted on this node.
        ''',
        
    'subtreeElementsStopIndex': r'''
        The highest element index of an element in the payload of any node of the
        subtree rooted on this node.
        ''',
    }
    
    ### INITIALIZER ###

    def __init__(self, offset):
        super(ElementNode, self).__init__(offset)
        self.payload = None
        self.payloadElementIndex = -1
        
        self.endTimeHigh = None
        self.endTimeLow = None
        
        self.subtreeElementsStartIndex = -1
        self.subtreeElementsStopIndex = -1


    ### SPECIAL METHODS ###

    def __repr__(self):
        pos = self.position
        if hasattr(pos, 'shortRepr'):
            pos = pos.shortRepr()
        return '<ElementNode: Start:{} Indices:(l:{} *{}* r:{}) Payload:{!r}>'.format(
            pos,
            self.subtreeElementsStartIndex,
            self.payloadElementIndex,
            self.subtreeElementsStopIndex,
            self.payload,
            )

    def updateIndices(self, parentStopIndex=None):
        r'''
        Updates the payloadElementIndex, and the subtreeElementsStartIndex and 
        subtreeElementsStopIndex (and does so for all child nodes) by traversing 
        the tree structure.
        
        Updates cached indices which keep
        track of the index of the element stored at each node, and of the
        minimum and maximum indices of the subtrees rooted at each node.

        Called on rootNode of a tree that uses ElementNodes, such as ElementTree

        Returns None.
        '''
        if self.leftChild is not None:
            self.leftChild.updateIndices(parentStopIndex=parentStopIndex)
            self.payloadElementIndex = self.leftChild.subtreeElementsStopIndex
            self.subtreeElementsStartIndex = self.leftChild.subtreeElementsStartIndex
        elif parentStopIndex is None:
            self.payloadElementIndex = 0
            self.subtreeElementsStartIndex = 0
        else:
            self.payloadElementIndex = parentStopIndex
            self.subtreeElementsStartIndex = parentStopIndex
        
        if self.payload is None:
            payloadLen = 0
        else:
            payloadLen = 1 
        self.subtreeElementsStopIndex = self.payloadElementIndex + payloadLen
        if self.rightChild is not None:
            self.rightChild.updateIndices(parentStopIndex=self.subtreeElementsStopIndex)
            self.subtreeElementsStopIndex = self.rightChild.subtreeElementsStopIndex

    def updateEndTimes(self):
        r'''
        Traverses the tree structure and updates cached maximum and minimum
        endTime values for the subtrees rooted at each node.

        Used internally by ElementTree.

        Returns None.
        '''
        pos = self.position
        if isinstance(pos, SortTuple):
            pos = pos.offset
            
        try:
            endTimeLow = self.payload.endTime
            endTimeHigh = endTimeLow
        except AttributeError: # elements do not have endTimes. do NOT mix elements and timespans.
            endTimeLow = pos + self.payload.duration.quarterLength
            endTimeHigh = endTimeLow

        leftChild = self.leftChild
        if leftChild:
            leftChild.updateEndTimes()
            if leftChild.endTimeLow < endTimeLow:
                endTimeLow = leftChild.endTimeLow
            if endTimeHigh < leftChild.endTimeHigh:
                endTimeHigh = leftChild.endTimeHigh
        
        rightChild = self.rightChild
        if rightChild:
            rightChild.updateEndTimes()
            if rightChild.endTimeLow < endTimeLow:
                endTimeLow = rightChild.endTimeLow
            if endTimeHigh < rightChild.endTimeHigh:
                endTimeHigh = rightChild.endTimeHigh
        self.endTimeLow = endTimeLow
        self.endTimeHigh = endTimeHigh

#------------------------------------------------------------------------------
class OffsetNode(ElementNode):
    r'''
    A node representing zero, one, or more elements or timespans at an offset.

    Here's an example of what it means and does:
    
    >>> score = tree.makeExampleScore()
    >>> sf = score.flat
    >>> sf.show('text', addEndTimes=True)
    {0.0 - 0.0} <music21.instrument.Instrument PartA: : >
    {0.0 - 0.0} <music21.instrument.Instrument PartB: : >
    {0.0 - 0.0} <music21.clef.BassClef>
    {0.0 - 0.0} <music21.clef.BassClef>
    {0.0 - 0.0} <music21.meter.TimeSignature 2/4>
    {0.0 - 0.0} <music21.meter.TimeSignature 2/4>
    {0.0 - 1.0} <music21.note.Note C>
    {0.0 - 2.0} <music21.note.Note C#>
    {1.0 - 2.0} <music21.note.Note D>
    {2.0 - 3.0} <music21.note.Note E>
    {2.0 - 4.0} <music21.note.Note G#>
    {3.0 - 4.0} <music21.note.Note F>
    {4.0 - 5.0} <music21.note.Note G>
    {4.0 - 6.0} <music21.note.Note E#>
    {5.0 - 6.0} <music21.note.Note A>
    {6.0 - 7.0} <music21.note.Note B>
    {6.0 - 8.0} <music21.note.Note D#>
    {7.0 - 8.0} <music21.note.Note C>
    {8.0 - 8.0} <music21.bar.Barline style=final>
    {8.0 - 8.0} <music21.bar.Barline style=final>
    
    >>> scoreTree = tree.fromStream.convert(sf, flatten=False, classList=None)
    >>> rn = scoreTree.rootNode
    
    The RootNode here represents the starting position of the Note F at 3.0; It is the center
    of the elements in the flat Stream.  Its index is 5 (that is, it's the sixth note in the
    element list) and its offset is 3.0
    
    >>> rn
    <OffsetNode: Start:3.0 Indices:(0:11:12:20) Length:{1}>
    >>> sf[11]
    <music21.note.Note F>
    >>> sf[11].offset
    3.0

    Thus, the indices of 0:5:6:12 indicate that the left-side of the node handles indices
    from >= 0 to < 5; and the right-side of the node handles indices >= 6 and < 12, and this node
    handles indices >= 5 and < 6.
    
    The `Length: {1}` indicates that there is exactly one element at this location, that is,
    the F.
    
    The "payload" of the node, is just that note wrapped in a list wrapped in an PitchedTimespan:
    
    >>> rn.payload
    [<PitchedTimespan (3.0 to 4.0) <music21.note.Note F>>]
    >>> rn.payload[0].element
    <music21.note.Note F>
    >>> rn.payload[0].element is sf[11]
    True
    
    
    We can look at the leftChild of the root node to get some more interesting cases:
    
    >>> left = rn.leftChild
    >>> left
    <OffsetNode: Start:1.0 Indices:(0:8:9:11) Length:{1}>
    
    In the leftNode of the leftNode of the rootNode there are eight elements: 
    metadata and both notes that begin on offset 0.0:

    >>> leftLeft = left.leftChild
    >>> leftLeft
    <OffsetNode: Start:0.0 Indices:(0:0:8:8) Length:{8}>
    
    >>> leftLeft.payload
    [<PitchedTimespan (0.0 to 0.0) <music21.instrument.Instrument PartA: : >>, 
     <PitchedTimespan (0.0 to 0.0) <music21.instrument.Instrument PartB: : >>, 
     <PitchedTimespan (0.0 to 0.0) <music21.clef.BassClef>>, 
     <PitchedTimespan (0.0 to 0.0) <music21.clef.BassClef>>, 
     <PitchedTimespan (0.0 to 0.0) <music21.meter.TimeSignature 2/4>>, 
     <PitchedTimespan (0.0 to 0.0) <music21.meter.TimeSignature 2/4>>, 
     <PitchedTimespan (0.0 to 1.0) <music21.note.Note C>>, 
     <PitchedTimespan (0.0 to 2.0) <music21.note.Note C#>>]
    
    The Indices:(0:0:8:8) indicates that `leftLeft` has neither left nor right children
    
    >>> leftLeft.leftChild is None
    True
    >>> leftLeft.rightChild is None
    True
    
    What makes an OffsetNode more interesting than other AWL Nodes is that it is aware of
    the fact that it might have objects that end at different times, such as the zero-length
    metadata and the 2.0 length half note
    
    >>> leftLeft.endTimeLow
    0.0
    >>> leftLeft.endTimeHigh
    2.0   
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        'endTimeHigh',
        'endTimeLow',
        'payloadElementsStartIndex',
        'payloadElementsStopIndex',
        'subtreeElementsStartIndex',
        'subtreeElementsStopIndex',
        )

    _DOC_ATTR = {
    'payload': r'''
        The contents of the node at this point.  Usually a list of PitchedTimespans.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.convert(score, flatten=True, 
        ...                  classList=(note.Note, chord.Chord))
        >>> print(scoreTree.rootNode.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> scoreTree.rootNode.payload
        [<PitchedTimespan (3.0 to 4.0) <music21.note.Note F>>]

        >>> scoreTree.rootNode.leftChild.payload
        [<PitchedTimespan (1.0 to 2.0) <music21.note.Note D>>]

        >>> for x in scoreTree.rootNode.leftChild.rightChild.payload:
        ...     x
        ...
        <PitchedTimespan (2.0 to 3.0) <music21.note.Note E>>
        <PitchedTimespan (2.0 to 4.0) <music21.note.Note G#>>

        >>> scoreTree.rootNode.rightChild.payload
        [<PitchedTimespan (5.0 to 6.0) <music21.note.Note A>>]
        ''',
        
    'payloadElementsStartIndex': r'''
        The timespan start index (i.e., the first x where s[x] is found in this Node's payload) 
        of only those timespans stored in the payload of this node.
        ''',
        
    'payloadElementsStopIndex': r'''
        The timespan stop index (i.e., the last x where s[x] is found in this Node's payload) 
        of only those timespans stored in the payload of this node.
        ''',
    'endTimeHigh': r'''
        The highest endTime of any node in the subtree rooted on this node.
        ''',
        
    'endTimeLow': r'''
        The lowest endTime of any node in the subtree rooted on this node.
        ''',               
        
    'subtreeElementsStartIndex': r'''
        The lowest element index of an element in the payload of any node of the
        subtree rooted on this node.
        ''',
        
    'subtreeElementsStopIndex': r'''
        The highest element index of an element in the payload of any node of the
        subtree rooted on this node.
        ''',
    }
    
    ### INITIALIZER ###

    def __init__(self, offset):
        super(OffsetNode, self).__init__(offset)
        self.payload = []
        self.payloadElementsStartIndex = -1
        self.payloadElementsStopIndex = -1

    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<OffsetNode: Start:{} Indices:({}:{}:{}:{}) Length:{{{}}}>'.format(
            self.position,
            self.subtreeElementsStartIndex,
            self.payloadElementsStartIndex,
            self.payloadElementsStopIndex,
            self.subtreeElementsStopIndex,
            len(self.payload),
            )

    ### PUBLIC METHODS ###

    def updateIndices(self, parentStopIndex=None):
        r'''
        Updates the payloadElementsStartIndex, the paylodElementsStopIndex 
        and the subtreeElementsStartIndex and 
        subtreeElementsStopIndex (and does so for all child nodes) by traversing 
        the tree structure.
        
        Updates cached indices which keep
        track of the index of the element stored at each node, and of the
        minimum and maximum indices of the subtrees rooted at each node.

        Called on rootNode of a tree that uses OffsetNodes, such as OffsetTree
        or TimespanTree

        Returns None.
        '''
        if self.leftChild is not None:
            self.leftChild.updateIndices(parentStopIndex=parentStopIndex)
            self.payloadElementsStartIndex = self.leftChild.subtreeElementsStopIndex
            self.subtreeElementsStartIndex = self.leftChild.subtreeElementsStartIndex
        elif parentStopIndex is None:
            self.payloadElementsStartIndex = 0
            self.subtreeElementsStartIndex = 0
        else:
            self.payloadElementsStartIndex = parentStopIndex
            self.subtreeElementsStartIndex = parentStopIndex
        self.payloadElementsStopIndex = self.payloadElementsStartIndex + len(self.payload)
        self.subtreeElementsStopIndex = self.payloadElementsStopIndex
        if self.rightChild is not None:
            self.rightChild.updateIndices(parentStopIndex=self.payloadElementsStopIndex)
            self.subtreeElementsStopIndex = self.rightChild.subtreeElementsStopIndex

    def updateEndTimes(self):
        r'''
        Traverses the tree structure and updates cached maximum and minimum
        endTime values for the subtrees rooted at each node.

        Used internally by OffsetTree.

        Returns None
        '''
        try:
            endTimeLow = min(x.endTime for x in self.payload)
            endTimeHigh = max(x.endTime for x in self.payload)
        except AttributeError: # elements do not have endTimes. do NOT mix elements and timespans.
            endTimeLow = self.position + min(x.duration.quarterLength for x in self.payload)
            endTimeHigh = self.position + max(x.duration.quarterLength for x in self.payload)            
        
        leftChild = self.leftChild
        if leftChild:
            leftChild.updateEndTimes()
            if leftChild.endTimeLow < endTimeLow:
                endTimeLow = leftChild.endTimeLow
            if endTimeHigh < leftChild.endTimeHigh:
                endTimeHigh = leftChild.endTimeHigh
                
        rightChild = self.rightChild
        if rightChild:
            rightChild.updateEndTimes()
            if rightChild.endTimeLow < endTimeLow:
                endTimeLow = rightChild.endTimeLow
            if endTimeHigh < rightChild.endTimeHigh:
                endTimeHigh = rightChild.endTimeHigh
        self.endTimeLow = endTimeLow
        self.endTimeHigh = endTimeHigh




    def payloadEndTimes(self):
        '''
        returns a (potentially unsorted) list of all the end times for all TimeSpans or
        Elements in the payload.  Does not trust el.endTime because it might refer to a
        different offset.  Rather, it takes the position and adds it to the 
        duration.quarterLength.
        
        >>> offsetNode = tree.node.OffsetNode(40)
        >>> n = note.Note()
        >>> offsetNode.payload.append(n)
        >>> ts = tree.spans.Timespan(40, 44)
        >>> offsetNode.payload.append(ts)
        >>> offsetNode.payloadEndTimes()
        [41.0, 44.0]
        '''
        outEndTimes = []
        for tsOrEl in self.payload:
            if isinstance(tsOrEl, Music21Object):
                outEndTimes.append(self.position + tsOrEl.duration.quarterLength)
            else:
                outEndTimes.append(tsOrEl.endTime)
        return outEndTimes

#------------------------------------------------------------------------------



class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (ElementNode,)


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
