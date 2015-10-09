# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         timespans/core.py
# Purpose:      Core AVLTree object.  To be optimized the hell out of.
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

from music21.timespans import node as nodeModule
from music21.exceptions21 import TimespanException

class AVLTree(object):
    r'''
    Data structure for working with timespans.node.AVLNode objects.
    
    To be subclassed in order to do anything useful with music21 objects.
    '''
    __slots__ = (
        '__weakref__',
        'rootNode',
        )
    nodeClass = nodeModule.AVLNode
    
    def __init__(self):
        self.rootNode = None

    def __iter__(self):
        r'''
        Iterates through all the nodes in the offset tree.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [timespans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> for x in tree:
        ...     x
        ...
        <Timespan 0 2>
        <Timespan 0 9>
        <Timespan 1 1>
        <Timespan 2 3>
        <Timespan 3 4>
        <Timespan 4 9>
        <Timespan 5 6>
        <Timespan 5 8>
        <Timespan 6 8>
        <Timespan 7 7>
        '''
        def recurse(node):
            if node is not None:
                if node.leftChild is not None:
                    for n in recurse(node.leftChild):
                        yield n
                yield node
                if node.rightChild is not None:
                    for n in recurse(node.rightChild):
                        yield n
                        
        return recurse(self.rootNode)


    def _insertNode(self, node, offset):
        r'''
        Inserts a node at `offset` in the subtree rooted on `node`.

        Used internally by TimespanTree.

        Returns a node which should be set to the new rootNode
        
        Note that if a node already exists at that place, nothing happens.
        
        
        >>> avl = timespans.core.AVLTree()
        >>> avl.rootNode = avl._insertNode(avl.rootNode, 20)
        >>> avl.rootNode
        <Node: Start:20 Height:0 L:None R:None>        
        
        >>> avl.rootNode = avl._insertNode(avl.rootNode, 10)
        >>> avl.rootNode
        <Node: Start:20 Height:1 L:0 R:None>

        >>> avl.rootNode = avl._insertNode(avl.rootNode, 5)
        >>> avl.rootNode
        <Node: Start:10 Height:1 L:0 R:0>
        
        >>> avl.rootNode = avl._insertNode(avl.rootNode, 30)
        >>> avl.rootNode
        <Node: Start:10 Height:2 L:0 R:1>
        >>> avl.rootNode.leftChild
        <Node: Start:5 Height:0 L:None R:None>
        >>> avl.rootNode.rightChild
        <Node: Start:20 Height:1 L:None R:0>
        
        >>> avl.rootNode.rightChild.rightChild
        <Node: Start:30 Height:0 L:None R:None>

        '''
        if node is None:
            # if we get to the point where a node does not have a
            # left or right child, make a new node at this offset...
            return self.nodeClass(offset)
        
        if offset < node.offset:
            node.leftChild = self._insertNode(node.leftChild, offset)
            node.update()
        elif node.offset < offset:
            node.rightChild = self._insertNode(node.rightChild, offset)
            node.update()
        return self._rebalance(node)


    def debug(self):
        r'''
        Gets string representation of the timespan collection.

        Useful only for debugging its internal node structure.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [timespans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> print(tree.debug())
        <Node: Start:3 Indices:(0:4:5:10) Length:{1}>
            L: <Node: Start:1 Indices:(0:2:3:4) Length:{1}>
                L: <Node: Start:0 Indices:(0:0:2:2) Length:{2}>
                R: <Node: Start:2 Indices:(3:3:4:4) Length:{1}>
            R: <Node: Start:5 Indices:(5:6:8:10) Length:{2}>
                L: <Node: Start:4 Indices:(5:5:6:6) Length:{1}>
                R: <Node: Start:6 Indices:(8:8:9:10) Length:{1}>
                    R: <Node: Start:7 Indices:(9:9:10:10) Length:{1}>
        '''
        if self.rootNode is not None:
            return self.rootNode.debug()
        return ''

    def _rebalance(self, node):
        r'''
        Rebalances the subtree rooted on`node`.

        Returns the original node.
        '''
        if node is not None:
            if node.balance > 1:
                if 0 <= node.rightChild.balance:
                    node = self._rotateRightRight(node)
                else:
                    node = self._rotateRightLeft(node)
            elif node.balance < -1:
                if node.leftChild.balance <= 0:
                    node = self._rotateLeftLeft(node)
                else:
                    node = self._rotateLeftRight(node)
            if node.balance < -1 or node.balance > 1:
                raise TimespanException('Somehow Nodes are still not balanced. node.balance %r must be between -1 and 1')
        return node
    
    def _rotateLeftLeft(self, node):
        r'''
        Rotates a node left twice.

        Used internally by TimespanTree during tree rebalancing.

        Returns a node.
        '''
        nextNode = node.leftChild
        node.leftChild = nextNode.rightChild
        node.update()
        nextNode.rightChild = node
        nextNode.update()

        return nextNode

    def _rotateLeftRight(self, node):
        r'''
        Rotates a node right twice.

        Used internally by TimespanTree during tree rebalancing.

        Returns a node.
        '''
        node.leftChild = self._rotateRightRight(node.leftChild)
        node.update()
        nextNode = self._rotateLeftLeft(node)
        return nextNode

    def _rotateRightLeft(self, node):
        r'''
        Rotates a node right, then left.

        Used internally by TimespanTree during tree rebalancing.

        Returns a node.
        '''
        node.rightChild = self._rotateLeftLeft(node.rightChild)
        node.update()
        nextNode = self._rotateRightRight(node)
        return nextNode

    def _rotateRightRight(self, node):
        r'''
        Rotates a node left, then right.

        Used internally by TimespanTree during tree rebalancing.

        Returns a node.
        '''
        nextNode = node.rightChild
        node.rightChild = nextNode.leftChild
        node.update()
        nextNode.leftChild = node
        nextNode.update()
        return nextNode

    def getNodeByOffset(self, offset, node=None):
        r'''
        Searches for a node whose offset is `offset` in the subtree
        rooted on `node`.

        Used internally by TimespanTree.

        Returns a Node object or None
        '''
        if node is not None:
            if node.offset == offset:
                return node
            elif node.leftChild and offset < node.offset:
                return self.getNodeByOffset(offset, node.leftChild)
            elif node.rightChild and node.offset < offset:
                return self.getNodeByOffset(offset, node.rightChild)
        return None

    def _getNodeAfter(self, offset):
        r'''
        Gets the first node after `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> n1 = tree._getNodeAfter(0.5)
        >>> n1
        <Node: Start:1.0 Indices:(7:7:11:11) Length:{4}>
        >>> n2 = tree._getNodeAfter(0.6)
        >>> n2 is n1
        True
        '''
        def recurse(node, offset):
            if node is None:
                return None
            result = None
            if node.offset <= offset and node.rightChild:
                result = recurse(node.rightChild, offset)
            elif offset < node.offset:
                result = recurse(node.leftChild, offset) or node
            return result
        result = recurse(self.rootNode, offset)
        if result is None:
            return None
        return result
    
    def getOffsetAfter(self, offset):
        r'''
        Gets start offset after `offset`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.getOffsetAfter(0.5)
        1.0

        Returns None if no succeeding offset exists.

        >>> tree.getOffsetAfter(35) is None
        True

        Generally speaking, negative offsets will usually return 0.0

        >>> tree.getOffsetAfter(-999)
        0.0
        '''
        node = self._getNodeAfter(offset)
        if node:            
            return node.offset
        else:
            return None

    def _getNodeBefore(self, offset):
        '''
        Finds the node immediately before offset.
        
        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree._getNodeBefore(100)  # last node in piece
        <Node: Start:35.0 Indices:(161:161:165:165) Length:{4}>
        '''
        
        def recurse(node, offset):
            if node is None:
                return None
            result = None
            if node.offset < offset:
                result = recurse(node.rightChild, offset) or node
            elif offset <= node.offset and node.leftChild:
                result = recurse(node.leftChild, offset)
            return result
        result = recurse(self.rootNode, offset)
        if result is None:
            return None
        return result
    
    def getOffsetBefore(self, offset):
        r'''
        Gets the start offset immediately preceding `offset` in this
        offset-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.getOffsetBefore(100)
        35.0

        Return None if no preceding offset exists.

        >>> tree.getOffsetBefore(0) is None
        True
        '''
        node = self._getNodeBefore(offset)
        if node is None:
            return None
        return node.offset

    def _remove(self, node, offset):
        r'''
        Removes a node at `offset` in the subtree rooted on `node`.

        Used internally by TimespanTree.

        Returns a node which represents the new rootNote.
        '''
        if node is not None:
            if node.offset == offset:
                ### got the right node!
                if node.leftChild and node.rightChild:
                    nextNode = node.rightChild
                    while nextNode.leftChild: # farthest left child of the right child.
                        nextNode = nextNode.leftChild
                    node.offset = nextNode.offset
                    node.payload = nextNode.payload
                    node.rightChild = self._remove(node.rightChild, nextNode.offset)
                    node.update()
                else:
                    node = node.leftChild or node.rightChild
            elif node.offset > offset:
                node.leftChild = self._remove(node.leftChild, offset)
                node.update()
            elif node.offset < offset:
                node.rightChild = self._remove(node.rightChild, offset)
                node.update()
        return self._rebalance(node)

#-------------------------------#
if __name__ == '__main__':
    import music21
    music21.mainTest()