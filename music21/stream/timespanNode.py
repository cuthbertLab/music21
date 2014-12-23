# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespanNode.py
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

This is an implementation detail of the TimespanCollection class.
'''

import unittest
from music21 import environment
environLocal = environment.Environment("stream.timespanNode")


#------------------------------------------------------------------------------


class TimespanCollectionNode(object):
    r'''
    A node in an TimespanCollection.

    This class is only used by TimespanCollection, and should not be
    instantiated by hand. It stores a list of ElementTimespans, as well as
    various data which describes the internal structure of the tree.

        >>> startOffset = 1.0
        >>> node = stream.timespanNode.TimespanCollectionNode(startOffset)
        >>> node
        <Node: Start:1.0 Indices:(-1:-1:-1:-1) Length:{0}>

    Please consult the Wikipedia entry on AVL trees
    (https://en.wikipedia.org/wiki/AVL_tree) for a very detailed
    description of how this datastructure works.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '__weakref__',
        'balance',
        'height',
        'payload',
        'nodeStartIndex',
        'nodeStopIndex',
        'startOffset',
        'stopOffsetHigh',
        'stopOffsetLow',
        'subtreeStartIndex',
        'subtreeStopIndex',

        '_leftChild',
        '_rightChild',
        )

    _DOC_ATTR = {
    'balance': '''
        Gets the difference in heights of the two subtrees rooted on this node.

        This attribute is used to help balance the AVL tree.

        >>> score = stream.timespans.makeExampleScore()
        >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree._debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>


        This tree has one more depth on the right than on the left

        >>> tree._rootNode.balance
        1


        The leftChild of the rootNote is perfectly balanced, while the rightChild is off by
        one (acceptable).


        >>> tree._rootNode.leftChild.balance
        0

        >>> tree._rootNode.rightChild.balance
        1


        The rightChild's children are also (acceptably) unbalanced:
        

        >>> tree._rootNode.rightChild.leftChild.balance
        0

        >>> tree._rootNode.rightChild.rightChild.balance
        1''',
        
        
        'height':         r'''
        The height of the subtree rooted on this node.

        This property is used to help balance the AVL tree.

        >>> score = stream.timespans.makeExampleScore()
        >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree._debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree._rootNode.height
        3

        >>> tree._rootNode.rightChild.height
        2

        >>> tree._rootNode.rightChild.rightChild.height
        1

        >>> tree._rootNode.rightChild.rightChild.rightChild.height
        0
        ''',
        
        'payload': r'''
        A list of Timespans starting at this node's start offset.

        Timespans are sorted by their _SortTuple, if they contain an element,
        and otherwise by their stop offset.

        ::

            >>> score = stream.timespans.makeExampleScore()
            >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
            >>> print(tree._rootNode.debug())
            <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
                L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                    L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                    R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
                R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                    L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                    R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                        R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        ::

            >>> tree._rootNode.payload
            [<ElementTimespan (3.0 to 4.0) <music21.note.Note F>>]

        ::

            >>> tree._rootNode.leftChild.payload
            [<ElementTimespan (1.0 to 2.0) <music21.note.Note D>>]

        ::

            >>> for x in tree._rootNode.leftChild.rightChild.payload:
            ...     x
            ...
            <ElementTimespan (2.0 to 3.0) <music21.note.Note E>>
            <ElementTimespan (2.0 to 4.0) <music21.note.Note G>>

        ::

            >>> tree._rootNode.rightChild.payload
            [<ElementTimespan (5.0 to 6.0) <music21.note.Note A>>]

        ''',
        
        'nodeStartIndex':         r'''
        The timespan start index of only those timespans stored in this
        node.
        ''',
        
        'nodeStopIndex':        r'''
        The timespan stop index of only those timespans stored in this
        node.
        ''',
        
        'startOffset':        r'''
        The start offset of this node.

        >>> score = stream.timespans.makeExampleScore()
        >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree._rootNode.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree._rootNode.startOffset
        3.0

        >>> tree._rootNode.leftChild.startOffset
        1.0

        >>> tree._rootNode.rightChild.startOffset
        5.0

        ''',

        'stopOffsetHigh':        r'''
        The highest stop offset of any timespan in any node nof the subtree
        rooted on this node.
        ''',
        
        'stopOffsetLow':        r'''
        The lowest stop offset of any timespan in any node of the subtree
        rooted on this node.
        ''',               
        
        'subTreeStartIndex':        r'''
        The lowest timespan start index of any timespan in any node of the
        subtree rooted on this node.
        ''',
        
        'subtreeStopIndex':         r'''
        The highest timespan stop index of any timespan in any node of the
        subtree rooted on this node.
        ''',


    }
    
    ### INITIALIZER ###

    def __init__(self, startOffset):
        self.balance = 0
        self.height = 0
        self.payload = []
        self.nodeStartIndex = -1
        self.nodeStopIndex = -1
        self.startOffset = startOffset
        self.stopOffsetHigh = None
        self.stopOffsetLow = None
        self.subtreeStartIndex = -1
        self.subtreeStopIndex = -1

        self._leftChild = None
        self._rightChild = None


    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<Node: Start:{} Indices:({}:{}:{}:{}) Length:{{{}}}>'.format(
            self.startOffset,
            self.subtreeStartIndex,
            self.nodeStartIndex,
            self.nodeStopIndex,
            self.subtreeStopIndex,
            len(self.payload),
            )

    ### PRIVATE METHODS ###

    def debug(self):
        '''
        Get a debug of the Node:
        
        >>> score = stream.timespans.makeExampleScore()
        >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> rn = tree._rootNode
        >>> rn
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
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
        Return a list of the debugging information of the tree (used for _debug):
        >>> score = stream.timespans.makeExampleScore()
        >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> rn = tree._rootNode
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

        >>> score = stream.timespans.makeExampleScore()
        >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
        >>> print(tree._rootNode.debug())
        <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree._rootNode.leftChild.debug())
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

        ::

            >>> score = stream.timespans.makeExampleScore()
            >>> tree = stream.timespans.streamToTimespanCollection(score, flatten=True, classList=(note.Note, chord.Chord))
            >>> print(tree._rootNode.debug())
            <Node: Start:3.0 Indices:(0:5:6:12) Length:{1}>
                L: <Node: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                    L: <Node: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                    R: <Node: Start:2.0 Indices:(3:3:5:5) Length:{2}>
                R: <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                    L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                    R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                        R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        ::

            >>> print(tree._rootNode.rightChild.debug())
            <Node: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <Node: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        ::

            >>> print(tree._rootNode.rightChild.rightChild.debug())
            <Node: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                R: <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        ::

            >>> print(tree._rootNode.rightChild.rightChild.rightChild.debug())
            <Node: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        '''
        return self._rightChild

    @rightChild.setter
    def rightChild(self, node):
        self._rightChild = node
        self.update()

#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------


_DOC_ORDER = (
    )


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
