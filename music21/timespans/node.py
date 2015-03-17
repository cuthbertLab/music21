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
from music21 import common
from music21 import environment
environLocal = environment.Environment("timespans.node")

#------------------------------------------------------------------------------
class AVLNode(common.SlottedObject):
    r'''
    An AVL Tree Node, not specialized in any way, just contains offsets.

    This class is only used by TimespanTree, and should not be
    instantiated by hand. It stores a list of ElementTimespans, as well as
    various data which describes the internal structure of the tree.

    >>> offset = 1.0
    >>> node = timespans.node.AVLNode(offset)
    >>> node
    <Node: Start:1.0 Height:0 L:None R:None>
    >>> n2 = timespans.node.AVLNode(2.0)
    >>> node.rightChild = n2
    >>> node
    <Node: Start:1.0 Height:1 L:None R:0>
    
    Note that nodes cannot rebalance themselves, that's what a Tree is for.
    

    Please consult the Wikipedia entry on AVL trees
    (https://en.wikipedia.org/wiki/AVL_tree) for a very detailed
    description of how this datastructure works.    
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '__weakref__',
        'balance',
        'height',
        'offset',
        'payload',

        '_leftChild',
        '_rightChild',
        )

    _DOC_ATTR = {
    'balance': '''
        Returns the current state of the difference in heights of the two subtrees rooted on this node.

        This attribute is used to help balance the AVL tree.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>


        This tree has one more depth on the right than on the left

        >>> tree.rootNode.balance
        1


        The leftChild of the rootNote is perfectly balanced, while the rightChild is off by
        one (acceptable).

        >>> tree.rootNode.leftChild.balance
        0
        >>> tree.rootNode.rightChild.balance
        1


        The rightChild's children are also (acceptably) unbalanced:

        >>> tree.rootNode.rightChild.leftChild.balance
        0
        >>> tree.rootNode.rightChild.rightChild.balance
        1
        ''',
        
        
    'height': r'''
        The height of the subtree rooted on this node.

        This property is used to help balance the AVL tree.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree.rootNode.height
        3

        >>> tree.rootNode.rightChild.height
        2

        >>> tree.rootNode.rightChild.rightChild.height
        1

        >>> tree.rootNode.rightChild.rightChild.rightChild.height
        0
        ''',
        
    'offset': r'''
        The offset of this node.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree.rootNode.offset
        3.0

        >>> tree.rootNode.leftChild.offset
        1.0

        >>> tree.rootNode.rightChild.offset
        5.0
        ''',
    }
    
    ### INITIALIZER ###

    def __init__(self, offset):
        self.balance = 0
        self.height = 0        
        self.offset = offset
        self.payload = None

        self._leftChild = None
        self._rightChild = None


    ### SPECIAL METHODS ###

    def __repr__(self):
        lcHeight = None
        if self.leftChild:
            lcHeight = self.leftChild.height
        rcHeight = None
        if self.rightChild:
            rcHeight = self.rightChild.height
            
        return '<Node: Start:{} Height:{} L:{} R:{}>'.format(
            self.offset,
            self.height,
            lcHeight,
            rcHeight
            )

    ### PRIVATE METHODS ###

    def debug(self):
        '''
        Get a debug of the Node:
        
        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> rn = tree.rootNode        
        >>> print(rn.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>
        '''
        return '\n'.join(self.getDebugPieces())

    def getDebugPieces(self):
        r'''
        Return a list of the debugging information of the tree (used for debug):
        
        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> rn = tree.rootNode
        >>> rn.getDebugPieces()
        ['<Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>', 
        '\tL: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>',
        '\t\tL: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>', 
        '\t\tR: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>', 
        '\tR: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>', 
        '\t\tL: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>', 
        '\t\tR: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>', 
        '\t\t\tR: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>']        
        '''        
        result = []
        result.append(repr(self))
        if self.leftChild:
            subresult = self.leftChild.getDebugPieces()
            result.append('\tL: {}'.format(subresult[0]))
            result.extend('\t' + x for x in subresult[1:])
        if self.rightChild:
            subresult = self.rightChild.getDebugPieces()
            result.append('\tR: {}'.format(subresult[0]))
            result.extend('\t' + x for x in subresult[1:])
        return result

    def update(self):
        '''
        Updates the height and balance attributes of the nodes.
        
        Called automatically when the .leftChild or .rightChild are changed.
        
        Returns None
        '''        
        leftHeight = -1
        rightHeight = -1
        if self.leftChild is not None:
            leftHeight = self.leftChild.height
        if self.rightChild is not None:
            rightHeight = self.rightChild.height
        self.height = max(leftHeight, rightHeight) + 1
        self.balance = rightHeight - leftHeight

    ### PUBLIC PROPERTIES ###

    @property
    def leftChild(self):
        r'''
        The left child of this node.

        Setting the left child triggers a node update.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.leftChild.debug())
        <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
            L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
            R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
        '''
        return self._leftChild

    @leftChild.setter
    def leftChild(self, node):
        self._leftChild = node
        self.update()

    @property
    def rightChild(self):
        r'''
        The right child of this node.

        Setting the right child triggers a node update.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.rightChild.debug())
        <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
            L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
            R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.rightChild.rightChild.debug())
        <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
            R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.rightChild.rightChild.rightChild.debug())
        <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>
        '''
        return self._rightChild

    @rightChild.setter
    def rightChild(self, node):
        self._rightChild = node
        self.update()
        
#------------------------------------------------------------------------------
class TimespanTreeNode(AVLNode):
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
    
    >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
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
        'nodeStartIndex',
        'nodeStopIndex',
        'subtreeStartIndex',
        'subtreeStopIndex',
        )

    _DOC_ATTR = {
    'payload': r'''
        A list of Timespans starting at this node's start offset.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
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
        
    'nodeStartIndex': r'''
        The timespan start index (i.e., the first x where s[x] is found in this Node's payload) 
        of only those timespans stored in the payload of this node.
        ''',
        
    'nodeStopIndex': r'''
        The timespan stop index (i.e., the last x where s[x] is found in this Node's payload) 
        of only those timespans stored in the payload of this node.
        ''',
    'endTimeHigh': r'''
        The highest stop offset of any timespan in any node of the subtree
        rooted on this node.
        ''',
        
    'endTimeLow': r'''
        The lowest stop offset of any timespan in any node of the subtree
        rooted on this node.
        ''',               
        
    'subTreeStartIndex': r'''
        The lowest timespan start index of any timespan in any node of the
        subtree rooted on this node.
        ''',
        
    'subtreeStopIndex': r'''
        The highest timespan stop index of any timespan in any node of the
        subtree rooted on this node.
        ''',
    }
    
    ### INITIALIZER ###

    def __init__(self, offset):
        super(TimespanTreeNode, self).__init__(offset)
        self.payload = []
        self.nodeStartIndex = -1
        self.nodeStopIndex = -1
        
        self.endTimeHigh = None
        self.endTimeLow = None
        
        self.subtreeStartIndex = -1
        self.subtreeStopIndex = -1


    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<Node: Start:{} Indices:({}:{}:{}:{}) Length:{{{}}}>'.format(
            self.offset,
            self.subtreeStartIndex,
            self.nodeStartIndex,
            self.nodeStopIndex,
            self.subtreeStopIndex,
            len(self.payload),
            )




#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (TimespanTreeNode, AVLNode)


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
