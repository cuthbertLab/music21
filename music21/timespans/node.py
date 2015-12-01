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
from music21.timespans import core
        
#------------------------------------------------------------------------------
class TimespanTreeNode(core.AVLNode):
    r'''
    A node in an TimespanTree.

    Here's an example of what it means and does:
    
    >>> score = timespans.makeExampleScore()
    >>> sfn = score.flat.notes
    >>> sfn.show('text', addEndTimes=True)
    {0.0 - 1.0} <music21.note.Note C>
    {0.0 - 2.0} <music21.note.Note C>
    {1.0 - 2.0} <music21.note.Note D>
    {2.0 - 3.0} <music21.note.Note E>
    {2.0 - 4.0} <music21.note.Note G>
    {3.0 - 4.0} <music21.note.Note F>
    {4.0 - 5.0} <music21.note.Note G>
    {4.0 - 6.0} <music21.note.Note E>
    {5.0 - 6.0} <music21.note.Note A>
    {6.0 - 7.0} <music21.note.Note B>
    {6.0 - 8.0} <music21.note.Note D>
    {7.0 - 8.0} <music21.note.Note C>
    
    >>> tree = timespans.fromStream.convert(score, flatten=True, 
    ...              classList=(note.Note, chord.Chord))
    >>> rn = tree.rootNode
    
    The RootNode here represents the starting position of the Note F at 3.0; It is the center
    of the elements in the flat Stream.  Its index is 5 (that is, it's the sixth note in the
    element list) and its offset is 3.0
    
    >>> rn
    <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
    >>> sfn[5]
    <music21.note.Note F>
    >>> sfn[5].offset
    3.0

    Thus, the indices of 0:5:6:12 indicate that the left-side of the node handles indices
    from >= 0 to < 5; and the right-side of the node handles indices >= 6 and < 12, and this node
    handles indices >= 5 and < 6.
    
    The `Length: {1}` indicates that there is exactly one element at this location, that is,
    the F.
    
    The "payload" of the node, is just that note wrapped in a list wrapped in an ElementTimeSpan:
    
    >>> rn.payload
    [<ElementTimespan (3.0 to 4.0) <music21.note.Note F>>]
    >>> rn.payload[0].element
    <music21.note.Note F>
    >>> rn.payload[0].element is sfn[5]
    True
    
    
    We can look at the leftChild of the root node to get some more interesting cases:
    
    >>> left = rn.leftChild
    >>> left
    <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
    >>> leftLeft = left.leftChild
    >>> leftLeft
    <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
    
    In the leftNode of the leftNode of the rootNode there are two elements: both notes that
    begin on offset 0.0:
    
    >>> leftLeft.payload
    [<ElementTimespan (0.0 to 1.0) <music21.note.Note C>>, 
     <ElementTimespan (0.0 to 2.0) <music21.note.Note C>>]
    
    The Indices:(0:0:2:2) indicates that `leftLeft` has neither left nor right children
    >>> leftLeft.leftChild is None
    True
    >>> leftLeft.rightChild is None
    True
    
    What makes a TimespanNode more interesting than other AWL Nodes is that it is aware of
    the fact that it might have objects that end at different times:
    
    >>> leftLeft.endTimeLow
    1.0
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
        The contents of the node at this point.  Usually ElementTimespans.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...                  classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree.rootNode.payload
        [<ElementTimespan (3.0 to 4.0) <music21.note.Note F>>]

        >>> tree.rootNode.leftChild.payload
        [<ElementTimespan (1.0 to 2.0) <music21.note.Note D>>]

        >>> for x in tree.rootNode.leftChild.rightChild.payload:
        ...     x
        ...
        <ElementTimespan (2.0 to 3.0) <music21.note.Note E>>
        <ElementTimespan (2.0 to 4.0) <music21.note.Note G>>

        >>> tree.rootNode.rightChild.payload
        [<ElementTimespan (5.0 to 6.0) <music21.note.Note A>>]
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
        super(TimespanTreeNode, self).__init__(offset)
        self.payload = []
        self.payloadElementsStartIndex = -1
        self.payloadElementsStopIndex = -1
        
        self.endTimeHigh = None
        self.endTimeLow = None
        
        self.subtreeElementsStartIndex = -1
        self.subtreeElementsStopIndex = -1


    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<Node: Start:{} Indices:({}:{}:{}:{}) Length:{{{}}}>'.format(
            self.position,
            self.subtreeElementsStartIndex,
            self.payloadElementsStartIndex,
            self.payloadElementsStopIndex,
            self.subtreeElementsStopIndex,
            len(self.payload),
            )




#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (TimespanTreeNode,)


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
