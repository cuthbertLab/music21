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
These are the lowest level tools for working with self-balancing AVL trees.

There's an overhead to creating an AVL tree, but for a large score it is
absolutely balanced by having O(log n) search times.
'''
from music21.exceptions21 import TimespanException

from music21 import common

#------------------------------------------------------------------------------
class AVLNode(common.SlottedObject):
    r'''
    An AVL Tree Node, not specialized in any way, just contains positions.

    >>> position = 1.0
    >>> node = timespans.core.AVLNode(position)
    >>> node
    <OffsetNode: Start:1.0 Height:0 L:None R:None>
    >>> n2 = timespans.core.AVLNode(2.0)
    >>> node.rightChild = n2
    >>> node.update()
    >>> node
    <OffsetNode: Start:1.0 Height:1 L:None R:0>
    
    Nodes can rebalance themselves, but they work best in a Tree...

    Please consult the Wikipedia entry on AVL trees
    (https://en.wikipedia.org/wiki/AVL_tree) for a very detailed
    description of how this datastructure works.    
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '__weakref__',
        'balance',
        'height',
        'position',
        'payload',

        'leftChild',
        'rightChild',
        )

    _DOC_ATTR = {
    'balance': '''
        Returns the current state of the difference in heights of the 
        two subtrees rooted on this node.

        This attribute is used to help balance the AVL tree.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...                    classList=(note.Note, chord.Chord))
        >>> print(tree.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>


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
        
        You should never see a balance other than 1, -1, or 0.  If you do then
        something has gone wrong.
        ''',
        
        
    'height': r'''
        The height of the subtree rooted on this node.

        This property is used to help balance the AVL tree.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...              classList=(note.Note, chord.Chord))
        >>> print(tree.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree.rootNode.height
        3

        >>> tree.rootNode.rightChild.height
        2

        >>> tree.rootNode.rightChild.rightChild.height
        1

        >>> tree.rootNode.rightChild.rightChild.rightChild.height
        0
        
        Once you hit a height of zero, then the next child on either size should be None
        
        >>> print(tree.rootNode.rightChild.rightChild.rightChild.rightChild)
        None
        ''',
        
    'position': r'''
        The position of this node -- this is often the same as the offset of
        the node in a containing score, but does not need to be. It could be the .sortTuple

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> tree.rootNode.position
        3.0

        >>> tree.rootNode.leftChild.position
        1.0

        >>> tree.rootNode.rightChild.position
        5.0
        ''',
    'leftChild': r'''
        The left child of this node.

        After setting the left child you need to do a node update. with node.update()

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...           classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.leftChild.debug())
        <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
            L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
            R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
        ''',
    'rightChild':   r'''
        The right child of this node.

        After setting the right child you need to do a node update. with node.update()

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...             classList=(note.Note, chord.Chord))
        >>> print(tree.rootNode.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.rightChild.debug())
        <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
            L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
            R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.rightChild.rightChild.debug())
        <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
            R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>

        >>> print(tree.rootNode.rightChild.rightChild.rightChild.debug())
        <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>
        '''

    }
    
    ### INITIALIZER ###

    def __init__(self, position, payload=None):
        self.position = position
        self.payload = payload

        self.balance = 0
        self.height = 0        

        self.leftChild = None
        self.rightChild = None


    ### SPECIAL METHODS ###

    def __repr__(self):
        lcHeight = None
        if self.leftChild:
            lcHeight = self.leftChild.height
        rcHeight = None
        if self.rightChild:
            rcHeight = self.rightChild.height
            
        return '<OffsetNode: Start:{} Height:{} L:{} R:{}>'.format(
            self.position,
            self.height,
            lcHeight,
            rcHeight
            )

    ### PRIVATE METHODS ###
    def moveAttributes(self, other):
        '''
        move attributes from this node to another in case "removal" actually
        means substituting one node for another in the tree.
        
        Subclass this in derived classes
        
        Do not copy anything about height, balance, left or right
        children, etc.  By default just moves position and payload.
        '''
        other.position = self.position
        other.payload = self.payload

    def debug(self):
        '''
        Get a debug of the Node:
        
        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...              classList=(note.Note, chord.Chord))
        >>> rn = tree.rootNode        
        >>> print(rn.debug())
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>
            R: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>
                L: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>
                R: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>
                    R: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>
        '''
        return '\n'.join(self._getDebugPieces())

    def _getDebugPieces(self):
        r'''
        Return a list of the debugging information of the tree (used for debug):
        
        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...            classList=(note.Note, chord.Chord))
        >>> rn = tree.rootNode
        >>> rn._getDebugPieces()
        ['<OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>', 
        '\tL: <OffsetNode: Start:1.0 Indices:(0:2:3:5) Length:{1}>',
        '\t\tL: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>', 
        '\t\tR: <OffsetNode: Start:2.0 Indices:(3:3:5:5) Length:{2}>', 
        '\tR: <OffsetNode: Start:5.0 Indices:(6:8:9:12) Length:{1}>', 
        '\t\tL: <OffsetNode: Start:4.0 Indices:(6:6:8:8) Length:{2}>', 
        '\t\tR: <OffsetNode: Start:6.0 Indices:(9:9:11:12) Length:{2}>', 
        '\t\t\tR: <OffsetNode: Start:7.0 Indices:(11:11:12:12) Length:{1}>']        
        '''        
        result = []
        result.append(repr(self))
        if self.leftChild:
            subresult = self.leftChild._getDebugPieces()
            result.append('\tL: {}'.format(subresult[0]))
            result.extend('\t' + x for x in subresult[1:])
        if self.rightChild:
            subresult = self.rightChild._getDebugPieces()
            result.append('\tR: {}'.format(subresult[0]))
            result.extend('\t' + x for x in subresult[1:])
        return result

    def update(self):
        '''
        Updates the height and balance attributes of the nodes.
        
        Must be called whenever .leftChild or .rightChild are changed.
        
        Used for the next balancing operation -- does not rebalance itself
        
        Returns None

        We create a score with everything correct.

        >>> score = timespans.makeExampleScore()
        >>> tree = timespans.fromStream.convert(score, flatten=True, 
        ...             classList=(note.Note, chord.Chord))
        >>> n = tree.rootNode
        >>> n
        <OffsetNode: Start:3.0 Indices:(0:5:6:12) Length:{1}>
        >>> n.height, n.balance
        (3, 1)
        
        Now let's screw up the height and balance
        
        >>> n.height = 100
        >>> n.balance = -2
        >>> n.height, n.balance
        (100, -2)
        
        But we can fix it with `.update()`
        
        >>> n.update()
        >>> n.height, n.balance
        (3, 1)
        
        Note that if we were to screw up the balance/height of one of the
        child notes of `n` then this would not fix that node's balance/height.
        This method assumes that children have the correct information and only
        updates the information for this node.

        '''        
        if self.leftChild is not None:
            leftHeight = self.leftChild.height
        else:
            leftHeight = -1
        
        if self.rightChild is not None:
            rightHeight = self.rightChild.height
        else:
            rightHeight = -1
        
        self.height = max(leftHeight, rightHeight) + 1
        self.balance = rightHeight - leftHeight

    def rotateLeftLeft(self):
        r'''
        Rotates a node left twice. 
        
        Makes this node the rightChild of
        the former leftChild and makes the former leftChild's rightChild
        be the leftChild of this node.

        Used during tree rebalancing.

        Returns the prior leftChild node as the new central node.
        '''
        nextNode = self.leftChild
        self.leftChild = nextNode.rightChild
        self.update()
        nextNode.rightChild = self
        nextNode.update()

        return nextNode

    def rotateLeftRight(self):
        r'''
        Rotates a node left, then right.

        Makes this note the rightChild of the former rightChild of the former leftChild node

        Used during tree rebalancing.

        Returns the former rightChild of the former leftChild node as the new central node.
        '''
        self.leftChild = self.leftChild.rotateRightRight()
        self.update()
        nextNode = self.rotateLeftLeft()
        return nextNode

    def rotateRightLeft(self):
        r'''
        Rotates a node right, then left.

        Makes this note the leftChild of the former leftChild of the former rightChild node

        Used during tree rebalancing.

        Returns the former leftChild of the former rightChild node as the new central node.
        '''
        self.rightChild = self.rightChild.rotateLeftLeft()
        self.update()
        nextNode = self.rotateRightRight()
        return nextNode

    def rotateRightRight(self):
        r'''
        Rotates a node right twice.

        Makes this node the leftChild of
        the former rightChild and makes the former rightChild's leftChild
        be the rightChild of this node.

        Used during tree rebalancing.

        Returns the prior rightChild node as the new central node.
        '''
        nextNode = self.rightChild
        self.rightChild = nextNode.leftChild
        self.update()
        nextNode.leftChild = self
        nextNode.update()
        return nextNode

    def rebalance(self):
        r'''
        Rebalances the subtree rooted on this node.

        Returns the new central node.
        '''
        node = self
        if node.balance > 1:
            if 0 <= node.rightChild.balance:
                node = node.rotateRightRight()
            else:
                node = node.rotateRightLeft()
        elif node.balance < -1:
            if node.leftChild.balance <= 0:
                node = node.rotateLeftLeft()
            else:
                node = node.rotateLeftRight()
        if node.balance < -1 or node.balance > 1:
            raise TimespanException(
                'Somehow Nodes are still not balanced. node.balance %r must be between -1 and 1')

        return node


#----------------------------------------------------------------------------

class AVLTree(object):
    r'''
    Data structure for working with timespans.node.AVLNode objects.
    
    To be subclassed in order to do anything useful with music21 objects.
    '''
    __slots__ = (
        '__weakref__',
        'rootNode',
        )
    nodeClass = AVLNode
    
    def __init__(self):
        self.rootNode = None

    def __iter__(self):
        r'''
        Iterates through all the nodes in the position tree in left to right order.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> import random
        >>> random.shuffle(tsList)
        >>> tss = [timespans.spans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> for x in tree:
        ...     x
        ...
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

    def createNodeAtPosition(self, position):
        '''
        creates a new node at position and sets the rootNode
        appropriately
        
        >>> avl = timespans.core.AVLTree()
        >>> avl.createNodeAtPosition(20)
        >>> avl.rootNode
        <OffsetNode: Start:20 Height:0 L:None R:None>        
        
        >>> avl.createNodeAtPosition(10)
        >>> avl.rootNode
        <OffsetNode: Start:20 Height:1 L:0 R:None>

        >>> avl.createNodeAtPosition(5)
        >>> avl.rootNode
        <OffsetNode: Start:10 Height:1 L:0 R:0>
        
        >>> avl.createNodeAtPosition(30)
        >>> avl.rootNode
        <OffsetNode: Start:10 Height:2 L:0 R:1>
        >>> avl.rootNode.leftChild
        <OffsetNode: Start:5 Height:0 L:None R:None>
        >>> avl.rootNode.rightChild
        <OffsetNode: Start:20 Height:1 L:None R:0>
        
        >>> avl.rootNode.rightChild.rightChild
        <OffsetNode: Start:30 Height:0 L:None R:None>
        '''
        def recurse(node, position):
            '''
            this recursively finds the right place for the new node
            and either creates a new node (if it is in the right place)
            or rebalances the nodes above it and tells those nodes how
            to set their new roots.
            '''
            if node is None:
                # if we get to the point where a node does not have a
                # left or right child, make a new node at this position...
                return self.nodeClass(position)
            
            if position < node.position:
                node.leftChild = recurse(node.leftChild, position)
                node.update()
            elif node.position < position:
                node.rightChild = recurse(node.rightChild, position)
                node.update()
            if node is not None:
                return node.rebalance()            
        
        self.rootNode = recurse(self.rootNode, position)


    def debug(self):
        r'''
        Gets string representation of the node tree.

        Useful only for debugging its internal node structure.

        >>> tsList = [(0,2), (0,9), (1,1), (2,3), (3,4), (4,9), (5,6), (5,8), (6,8), (7,7)]
        >>> tss = [timespans.spans.Timespan(x, y) for x, y in tsList]
        >>> tree = timespans.trees.TimespanTree()
        >>> tree.insert(tss)

        >>> print(tree.debug())
        <OffsetNode: Start:3.0 Indices:(0:4:5:10) Length:{1}>
            L: <OffsetNode: Start:1.0 Indices:(0:2:3:4) Length:{1}>
                L: <OffsetNode: Start:0.0 Indices:(0:0:2:2) Length:{2}>
                R: <OffsetNode: Start:2.0 Indices:(3:3:4:4) Length:{1}>
            R: <OffsetNode: Start:5.0 Indices:(5:6:8:10) Length:{2}>
                L: <OffsetNode: Start:4.0 Indices:(5:5:6:6) Length:{1}>
                R: <OffsetNode: Start:6.0 Indices:(8:8:9:10) Length:{1}>
                    R: <OffsetNode: Start:7.0 Indices:(9:9:10:10) Length:{1}>
        '''
        if self.rootNode is not None:
            return self.rootNode.debug()
        return ''    

    def getNodeByPosition(self, position):
        r'''
        Searches for a node whose position is `position` in the subtree
        rooted on `node`.

        Used internally by TimespanTree.

        Returns a Node object or None
        '''
        def recurse(position, node):
            if node is not None:
                if node.position == position:
                    return node
                elif node.leftChild and position < node.position:
                    return recurse(position, node.leftChild)
                elif node.rightChild and node.position < position:
                    return recurse(position, node.rightChild)
            return None
    
        return recurse(position, self.rootNode)


    def getNodeAfter(self, position):
        r'''
        Gets the first node after `position`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> n1 = tree.getNodeAfter(0.5)
        >>> n1
        <OffsetNode: Start:1.0 Indices:(25:25:29:29) Length:{4}>
        >>> n2 = tree.getNodeAfter(0.6)
        >>> n2 is n1
        True
        
        >>> tree.getNodeAfter(9999) is None
        True
        '''
        def recurse(node, position):
            if node is None:
                return None
            result = None
            if node.position <= position and node.rightChild:
                result = recurse(node.rightChild, position)
            elif position < node.position:
                result = recurse(node.leftChild, position) or node
            return result
        result = recurse(self.rootNode, position)
        if result is None:
            return None
        return result
    
    def getPositionAfter(self, position):
        r'''
        Gets start position after `position`.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.getPositionAfter(0.5)
        1.0

        Returns None if no succeeding position exists.

        >>> tree.getPositionAfter(36) is None
        True

        Generally speaking, negative positions will usually return 0.0

        >>> tree.getPositionAfter(-999)
        0.0
        '''
        node = self.getNodeAfter(position)
        if node:            
            return node.position
        else:
            return None

    def getNodeBefore(self, position):
        '''
        Finds the node immediately before position.
        
        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()

        100 is beyond the end so it will get the last node in piece
        
        >>> tree.getNodeBefore(100)
        <OffsetNode: Start:36.0 Indices:(191:191:195:195) Length:{4}>
        
        >>> tree.getNodeBefore(0) is None
        True
        '''
        def recurse(node, position):
            if node is None:
                return None
            result = None
            if node.position < position:
                result = recurse(node.rightChild, position) or node
            elif position <= node.position and node.leftChild:
                result = recurse(node.leftChild, position)
            return result
        
        result = recurse(self.rootNode, position)
        if result is None:
            return None
        return result
    
    def getPositionBefore(self, position):
        r'''
        Gets the start position immediately preceding `position` in this
        position-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> tree = score.asTimespans()
        >>> tree.getPositionBefore(100)
        36.0

        Return None if no preceding position exists.

        >>> tree.getPositionBefore(0) is None
        True
        '''
        node = self.getNodeBefore(position)
        if node is None:
            return None
        return node.position

    def removeNode(self, position):
        r'''
        Removes a node at `position` and rebalances the tree

        Used internally by TimespanTree.

        >>> avl = timespans.core.AVLTree()
        >>> avl.createNodeAtPosition(20)
        >>> avl.createNodeAtPosition(10)
        >>> avl.createNodeAtPosition(5)
        >>> avl.createNodeAtPosition(30)
        >>> avl.rootNode
        <OffsetNode: Start:10 Height:2 L:0 R:1>

        Remove node at 30

        >>> avl.removeNode(30)
        >>> avl.rootNode
        <OffsetNode: Start:10 Height:1 L:0 R:0>
        
        Removing a node eliminates its payload:
        
        >>> ten = avl.getNodeByPosition(10)
        >>> ten.payload = 'ten'
        >>> twenty = avl.getNodeByPosition(20)
        >>> twenty.payload = 'twenty'
        
        >>> avl.removeNode(10)
        >>> avl.rootNode
        <OffsetNode: Start:20 Height:1 L:0 R:None>
        >>> avl.rootNode.payload
        'twenty'
        
        Removing a non-existent node does nothing.
        
        >>> avl.removeNode(9.5)
        >>> avl.rootNode
        <OffsetNode: Start:20 Height:1 L:0 R:None>
        
        >>> for n in avl:
        ...     print(n, n.payload)
        <OffsetNode: Start:5 Height:0 L:None R:None> None
        <OffsetNode: Start:20 Height:1 L:0 R:None> twenty        
        '''
        def recurseRemove(node, position):
            if node is not None:
                if node.position == position:
                    ### got the right node!
                    if node.leftChild and node.rightChild:
                        nextNode = node.rightChild
                        while nextNode.leftChild: # farthest left child of the right child.
                            nextNode = nextNode.leftChild
                        nextNode.moveAttributes(node)
                        node.rightChild = recurseRemove(node.rightChild, nextNode.position)
                        node.update()
                    else:
                        node = node.leftChild or node.rightChild
                elif node.position > position:
                    node.leftChild = recurseRemove(node.leftChild, position)
                    node.update()
                elif node.position < position:
                    node.rightChild = recurseRemove(node.rightChild, position)
                    node.update()
            if node is not None:
                return node.rebalance()

        self.rootNode = recurseRemove(self.rootNode, position)

#-------------------------------#
if __name__ == '__main__':
    import music21
    music21.mainTest()

