# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         tree/core.py
# Purpose:      Core AVLTree object.  To be optimized the hell out of.
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-16 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
These are the lowest level tools for working with self-balancing AVL trees.

There's an overhead to creating an AVL tree, but for a large score it is
absolutely balanced by having O(log n) search times.
'''
from typing import Optional

from music21.exceptions21 import TreeException
from music21 import common

# -----------------------------------------------------------------------------


class AVLNode(common.SlottedObjectMixin):
    r'''
    An AVL Tree Node, not specialized in any way, just contains positions.

    >>> position = 1.0
    >>> node = tree.core.AVLNode(position)
    >>> node
    <AVLNode: Start:1.0 Height:0 L:None R:None>
    >>> n2 = tree.core.AVLNode(2.0)
    >>> node.rightChild = n2
    >>> node.update()
    >>> node
    <AVLNode: Start:1.0 Height:1 L:None R:0>

    Nodes can rebalance themselves, but they work best in a Tree...

    Please consult the Wikipedia entry on AVL trees
    (https://en.wikipedia.org/wiki/AVL_tree) for a very detailed
    description of how this data structure works.
    '''

    # CLASS VARIABLES #

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

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...                    classList=(note.Note, chord.Chord))
        >>> print(scoreTree.debug())
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
            R: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
                L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
                R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                    R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>


        This tree has one more depth on the right than on the left

        >>> scoreTree.rootNode.balance
        1


        The leftChild of the rootNote is perfectly balanced, while the rightChild is off by
        one (acceptable).

        >>> scoreTree.rootNode.leftChild.balance
        0
        >>> scoreTree.rootNode.rightChild.balance
        1


        The rightChild's children are also (acceptably) unbalanced:

        >>> scoreTree.rootNode.rightChild.leftChild.balance
        0
        >>> scoreTree.rootNode.rightChild.rightChild.balance
        1

        You should never see a balance other than 1, -1, or 0.  If you do then
        something has gone wrong.
        ''',


        'height': r'''
        The height of the subtree rooted on this node.

        This property is used to help balance the AVL tree.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...              classList=(note.Note, chord.Chord))
        >>> print(scoreTree.debug())
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
            R: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
                L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
                R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                    R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>

        >>> scoreTree.rootNode.height
        3

        >>> scoreTree.rootNode.rightChild.height
        2

        >>> scoreTree.rootNode.rightChild.rightChild.height
        1

        >>> scoreTree.rootNode.rightChild.rightChild.rightChild.height
        0

        Once you hit a height of zero, then the next child on either size should be None

        >>> print(scoreTree.rootNode.rightChild.rightChild.rightChild.rightChild)
        None
        ''',
        'payload': r'''
        The content of the node at this point.  Usually a Music21Object.
        ''',

        'position': r'''
        The position of this node -- this is often the same as the offset of
        the node in a containing score, but does not need to be. It could be the .sortTuple

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...            classList=(note.Note, chord.Chord))
        >>> print(scoreTree.rootNode.debug())
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
            R: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
                L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
                R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                    R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>

        >>> scoreTree.rootNode.position
        3.0

        >>> scoreTree.rootNode.leftChild.position
        1.0

        >>> scoreTree.rootNode.rightChild.position
        5.0
        ''',
        'leftChild': r'''
        The left child of this node.

        After setting the left child you need to do a node update. with node.update()

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...           classList=(note.Note, chord.Chord))
        >>> print(scoreTree.rootNode.debug())
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
            R: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
                L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
                R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                    R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>

        >>> print(scoreTree.rootNode.leftChild.debug())
        <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
            L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
            R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
        ''',
        'rightChild': r'''
        The right child of this node.

        After setting the right child you need to do a node update. with node.update()

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...             classList=(note.Note, chord.Chord))
        >>> print(scoreTree.rootNode.debug())
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
            R: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
                L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
                R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                    R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>

        >>> print(scoreTree.rootNode.rightChild.debug())
        <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
            L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
            R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>

        >>> print(scoreTree.rootNode.rightChild.rightChild.debug())
        <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
            R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>

        >>> print(scoreTree.rootNode.rightChild.rightChild.rightChild.debug())
        <OffsetNode 7.0 Indices:11,11,12,12 Length:1>
        '''

    }

    # INITIALIZER #

    def __init__(self, position, payload=None):
        self.position = position
        self.payload = payload

        self.balance = 0
        self.height = 0

        self.leftChild = None
        self.rightChild = None

    # SPECIAL METHODS #

    def __repr__(self):
        lcHeight = None
        if self.leftChild:
            lcHeight = self.leftChild.height
        rcHeight = None
        if self.rightChild:
            rcHeight = self.rightChild.height

        return '<{}: Start:{} Height:{} L:{} R:{}>'.format(
            self.__class__.__name__,
            self.position,
            self.height,
            lcHeight,
            rcHeight
        )

    # PRIVATE METHODS #
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

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...              classList=(note.Note, chord.Chord))
        >>> rn = scoreTree.rootNode
        >>> print(rn.debug())
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>
            R: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>
                L: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>
                R: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>
                    R: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>
        '''
        return '\n'.join(self._getDebugPieces())

    def _getDebugPieces(self):
        r'''
        Return a list of the debugging information of the tree (used for debug):

        Called recursively

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...            classList=(note.Note, chord.Chord))
        >>> rn = scoreTree.rootNode
        >>> rn._getDebugPieces()
        ['<OffsetNode 3.0 Indices:0,5,6,12 Length:1>',
        '\tL: <OffsetNode 1.0 Indices:0,2,3,5 Length:1>',
        '\t\tL: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>',
        '\t\tR: <OffsetNode 2.0 Indices:3,3,5,5 Length:2>',
        '\tR: <OffsetNode 5.0 Indices:6,8,9,12 Length:1>',
        '\t\tL: <OffsetNode 4.0 Indices:6,6,8,8 Length:2>',
        '\t\tR: <OffsetNode 6.0 Indices:9,9,11,12 Length:2>',
        '\t\t\tR: <OffsetNode 7.0 Indices:11,11,12,12 Length:1>']
        '''
        result = []
        result.append(repr(self))
        if self.leftChild:
            subResult = self.leftChild._getDebugPieces()
            result.append(f'\tL: {subResult[0]}')
            result.extend('\t' + x for x in subResult[1:])
        if self.rightChild:
            subResult = self.rightChild._getDebugPieces()
            result.append(f'\tR: {subResult[0]}')
            result.extend('\t' + x for x in subResult[1:])
        return result

    def update(self):
        '''
        Updates the height and balance attributes of the nodes.

        Must be called whenever .leftChild or .rightChild are changed.

        Used for the next balancing operation -- does not rebalance itself.

        Note that it only looks at its children's height and balance attributes
        not their children's. So if they are wrong, this will be too.

        Returns None

        We create a score with everything correct.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = tree.fromStream.asTimespans(score, flatten=True,
        ...             classList=(note.Note, chord.Chord))
        >>> n = scoreTree.rootNode
        >>> n
        <OffsetNode 3.0 Indices:0,5,6,12 Length:1>
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
            if node.rightChild.balance >= 0:
                node = node.rotateRightRight()
            else:
                node = node.rotateRightLeft()
        elif node.balance < -1:
            if node.leftChild.balance <= 0:
                node = node.rotateLeftLeft()
            else:
                node = node.rotateLeftRight()
        if node.balance < -1 or node.balance > 1:
            raise TreeException(
                'Somehow Nodes are still not balanced. node.balance %r must be between -1 and 1')

        return node


# ---------------------------------------------------------------------------

class AVLTree:
    r'''
    Data structure for working with tree.node.AVLNode objects.

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

        Note that this runs in O(n log n) time in Python, while iterating through
        a list runs in O(n) time in C, so this isn't something to do on real datasets.

        >>> nodePositions = [0, 2, 4, 6, 8, 10, 12]
        >>> avl = tree.core.AVLTree()
        >>> for np in nodePositions:
        ...     avl.createNodeAtPosition(np)
        >>> for x in avl:
        ...     x
        <AVLNode: Start:0 Height:0 L:None R:None>
        <AVLNode: Start:2 Height:1 L:0 R:0>
        <AVLNode: Start:4 Height:0 L:None R:None>
        <AVLNode: Start:6 Height:2 L:1 R:1>
        <AVLNode: Start:8 Height:0 L:None R:None>
        <AVLNode: Start:10 Height:1 L:0 R:0>
        <AVLNode: Start:12 Height:0 L:None R:None>

        Note: for this example to be stable, we can't shuffle the nodes, since there are
        numerous different possible configurations that meet the AVLTree constraints, some
        of height 2 and some of height 3
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

    def populateFromSortedList(self, listOfTuples):
        '''
        Populate this tree from a sorted list of two-tuples of (position, payload).

        This is about an order of magnitude faster (3ms vs 21ms for 1000 items;
        31 vs. 300ms for 10,000 items) than running createNodeAtPosition()
        for each element in a list if it is
        already sorted.  Thus it should be used when converting a
        Stream where .isSorted is True into a tree.

        This method assumes that the current tree is empty (or will be wiped) and
        that listOfTuples is a non-empty
        list where the first element is a unique position to insert,
        and the second is the complete payload for that node, and
        that the positions are strictly increasing in order.

        If any of the conditions is not true, expect to get a dangerously
        badly sorted tree that will be useless.

        >>> listOfTuples = [(i, str(i)) for i in range(1000)]
        >>> listOfTuples[10]
        (10, '10')
        >>> t = tree.core.AVLTree()
        >>> t.rootNode is None
        True
        >>> t.populateFromSortedList(listOfTuples)
        >>> t.rootNode
        <AVLNode: Start:500 Height:9 L:8 R:8>

        >>> n = t.rootNode
        >>> while n is not None:
        ...    print(n, repr(n.payload))
        ...    n = n.leftChild
        <AVLNode: Start:500 Height:9 L:8 R:8> '500'
        <AVLNode: Start:250 Height:8 L:7 R:7> '250'
        <AVLNode: Start:125 Height:7 L:6 R:6> '125'
        <AVLNode: Start:62 Height:6 L:5 R:5> '62'
        <AVLNode: Start:31 Height:5 L:4 R:4> '31'
        <AVLNode: Start:15 Height:4 L:3 R:3> '15'
        <AVLNode: Start:7 Height:3 L:2 R:2> '7'
        <AVLNode: Start:3 Height:2 L:1 R:1> '3'
        <AVLNode: Start:1 Height:1 L:0 R:0> '1'
        <AVLNode: Start:0 Height:0 L:None R:None> '0'
        '''
        def recurse(subListOfTuples) -> Optional[AVLNode]:
            '''
            Divide and conquer.
            '''
            if not subListOfTuples:
                return None
            midpoint = len(subListOfTuples) // 2
            midtuple = subListOfTuples[midpoint]
            n = NodeClass(midtuple[0], midtuple[1])
            n.leftChild = recurse(subListOfTuples[:midpoint])
            n.rightChild = recurse(subListOfTuples[midpoint + 1:])
            n.update()
            return n

        NodeClass = self.nodeClass
        self.rootNode = recurse(listOfTuples)

    def createNodeAtPosition(self, position):
        '''
        creates a new node at position and sets the rootNode
        appropriately

        >>> avl = tree.core.AVLTree()
        >>> avl.createNodeAtPosition(20)
        >>> avl.rootNode
        <AVLNode: Start:20 Height:0 L:None R:None>

        >>> avl.createNodeAtPosition(10)
        >>> avl.rootNode
        <AVLNode: Start:20 Height:1 L:0 R:None>

        >>> avl.createNodeAtPosition(5)
        >>> avl.rootNode
        <AVLNode: Start:10 Height:1 L:0 R:0>

        >>> avl.createNodeAtPosition(30)
        >>> avl.rootNode
        <AVLNode: Start:10 Height:2 L:0 R:1>
        >>> avl.rootNode.leftChild
        <AVLNode: Start:5 Height:0 L:None R:None>
        >>> avl.rootNode.rightChild
        <AVLNode: Start:20 Height:1 L:None R:0>

        >>> avl.rootNode.rightChild.rightChild
        <AVLNode: Start:30 Height:0 L:None R:None>
        '''
        def recurse(node, innerPosition):
            '''
            this recursively finds the right place for the new node
            and either creates a new node (if it is in the right place)
            or rebalances the nodes above it and tells those nodes how
            to set their new roots.
            '''
            if node is None:
                # if we get to the point where a node does not have a
                # left or right child, make a new node at this position...
                return self.nodeClass(innerPosition)

            if innerPosition < node.position:
                node.leftChild = recurse(node.leftChild, innerPosition)
                node.update()
            elif node.position < innerPosition:
                node.rightChild = recurse(node.rightChild, innerPosition)
                node.update()
            if node is not None:
                return node.rebalance()

        self.rootNode = recurse(self.rootNode, position)

    def debug(self):
        r'''
        Gets string representation of the node tree.

        Useful only for debugging its internal node structure.

        >>> tsList = [(0, 2), (0, 9), (1, 1), (2, 3), (3, 4),
        ...           (4, 9), (5, 6), (5, 8), (6, 8), (7, 7)]
        >>> tss = [tree.spans.Timespan(x, y) for x, y in tsList]
        >>> tsTree = tree.timespanTree.TimespanTree()
        >>> tsTree.insert(tss)

        >>> print(tsTree.debug())
        <OffsetNode 3.0 Indices:0,4,5,10 Length:1>
            L: <OffsetNode 1.0 Indices:0,2,3,4 Length:1>
                L: <OffsetNode 0.0 Indices:0,0,2,2 Length:2>
                R: <OffsetNode 2.0 Indices:3,3,4,4 Length:1>
            R: <OffsetNode 5.0 Indices:5,6,8,10 Length:2>
                L: <OffsetNode 4.0 Indices:5,5,6,6 Length:1>
                R: <OffsetNode 6.0 Indices:8,8,9,10 Length:1>
                    R: <OffsetNode 7.0 Indices:9,9,10,10 Length:1>
        '''
        if self.rootNode is not None:
            return self.rootNode.debug()
        return ''

    def getNodeByPosition(self, position):
        r'''
        Searches for a node whose position is `position` in the subtree
        rooted on `node`.

        Returns a Node object or None
        '''
        def recurse(innerPosition, node):
            if node is not None:
                if node.position == innerPosition:
                    return node
                elif node.leftChild and innerPosition < node.position:
                    return recurse(innerPosition, node.leftChild)
                elif node.rightChild and node.position < innerPosition:
                    return recurse(innerPosition, node.rightChild)
            return None

        return recurse(position, self.rootNode)

    def getNodeAfter(self, position):
        r'''
        Gets the first node after `position`.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTree(flatten=True)
        >>> node1 = scoreTree.getNodeAfter(0.5)
        >>> node1
        <ElementNode: Start:1.0 <0.20...> Indices:(l:0 *25* r:61) Payload:<music21.note.Note A>>
        >>> node2 = scoreTree.getNodeAfter(0.6)
        >>> node2 is node1
        True

        >>> endNode = scoreTree.getNodeAfter(9999)
        >>> endNode
        <ElementNode: Start:End <0.-5...> Indices:(l:188 *191* r:195)
               Payload:<music21.bar.Barline type=final>>

        >>> while endNode is not None:
        ...     print(endNode)
        ...     endNodePosition = endNode.position
        ...     endNode = scoreTree.getNodeAfter(endNodePosition)
        <ElementNode: Start:End <0.-5...> Indices:(l:188 *191* r:195)
            Payload:<music21.bar.Barline type=final>>
        <ElementNode: Start:End <0.-5...> Indices:(l:192 *192* r:193)
            Payload:<music21.bar.Barline type=final>>
        <ElementNode: Start:End <0.-5...> Indices:(l:192 *193* r:195)
            Payload:<music21.bar.Barline type=final>>
        <ElementNode: Start:End <0.-5...> Indices:(l:194 *194* r:195)
            Payload:<music21.bar.Barline type=final>>

        >>> note1 = score.flat.notes[30]

        Works with sortTuple positions as well...

        >>> st = note1.sortTuple()
        >>> st
        SortTuple(atEnd=0, offset=6.0, priority=0, classSortOrder=20, isNotGrace=1, insertIndex=...)

        >>> scoreTree.getNodeAfter(st)
        <ElementNode: Start:6.5 <0.20...> Indices:(l:51 *52* r:53)
            Payload:<music21.note.Note D>>
        '''
        def recurse(node, innerPosition):
            if node is None:
                return None
            inner_result = None
            if node.position <= innerPosition and node.rightChild:
                inner_result = recurse(node.rightChild, innerPosition)
            elif innerPosition < node.position:
                inner_result = recurse(node.leftChild, innerPosition) or node
            return inner_result

        result = recurse(self.rootNode, position)
        if result is None:
            return None
        return result

    def getPositionAfter(self, position):
        r'''
        Gets start position after `position`.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTree(flatten=True)
        >>> scoreTree.getPositionAfter(0.5).offset
        1.0

        Returns None if no succeeding position exists.

        >>> endPosition = scoreTree.getPositionAfter(9999)
        >>> while endPosition is not None:
        ...     print(endPosition)
        ...     endPosition = scoreTree.getPositionAfter(endPosition)
        SortTuple(atEnd=1, offset=36.0, priority=0, classSortOrder=-5, ...)
        SortTuple(atEnd=1, offset=36.0, priority=0, classSortOrder=-5, ...)
        SortTuple(atEnd=1, offset=36.0, priority=0, classSortOrder=-5, ...)
        SortTuple(atEnd=1, offset=36.0, priority=0, classSortOrder=-5, ...)

        Generally speaking, negative positions will usually return 0.0

        >>> scoreTree.getPositionAfter(-999).offset
        0.0

        Unless the Tree is empty in which case, None is returned:

        >>> at = tree.core.AVLTree()
        >>> at.getPositionAfter(-999) is None
        True
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
        >>> scoreTree = score.asTimespans()

        100 is beyond the end so it will get the last node in piece

        >>> scoreTree.getNodeBefore(100)
        <OffsetNode 36.0 Indices:191,191,195,195 Length:4>

        >>> scoreTree.getNodeBefore(0) is None
        True
        '''
        def recurse(node, innerPosition):
            if node is None:
                return None
            innerResult = None
            if node.position < innerPosition:
                innerResult = recurse(node.rightChild, innerPosition) or node
            elif innerPosition <= node.position and node.leftChild:
                innerResult = recurse(node.leftChild, innerPosition)
            return innerResult

        result = recurse(self.rootNode, position)
        if result is None:
            return None
        return result

    def getPositionBefore(self, position):
        r'''
        Gets the start position immediately preceding `position` in this
        position-tree.

        >>> score = corpus.parse('bwv66.6')
        >>> scoreTree = score.asTimespans()
        >>> scoreTree.getPositionBefore(100)
        36.0

        Return None if no preceding position exists.

        >>> scoreTree.getPositionBefore(0) is None
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

        >>> avl = tree.core.AVLTree()
        >>> avl.createNodeAtPosition(20)
        >>> avl.createNodeAtPosition(10)
        >>> avl.createNodeAtPosition(5)
        >>> avl.createNodeAtPosition(30)
        >>> avl.rootNode
        <AVLNode: Start:10 Height:2 L:0 R:1>

        Remove node at 30

        >>> avl.removeNode(30)
        >>> avl.rootNode
        <AVLNode: Start:10 Height:1 L:0 R:0>

        Removing a node eliminates its payload:

        >>> ten = avl.getNodeByPosition(10)
        >>> ten.payload = 'ten'
        >>> twenty = avl.getNodeByPosition(20)
        >>> twenty.payload = 'twenty'

        >>> avl.removeNode(10)
        >>> avl.rootNode
        <AVLNode: Start:20 Height:1 L:0 R:None>
        >>> avl.rootNode.payload
        'twenty'

        Removing a non-existent node does nothing.

        >>> avl.removeNode(9.5)
        >>> avl.rootNode
        <AVLNode: Start:20 Height:1 L:0 R:None>

        >>> for n in avl:
        ...     print(n, n.payload)
        <AVLNode: Start:5 Height:0 L:None R:None> None
        <AVLNode: Start:20 Height:1 L:0 R:None> twenty
        '''
        def recurseRemove(node, innerPosition):
            if node is not None:
                if node.position == innerPosition:
                    # got the right node!
                    if node.leftChild and node.rightChild:
                        nextNode = node.rightChild
                        while nextNode.leftChild:  # farthest left child of the right child.
                            nextNode = nextNode.leftChild
                        nextNode.moveAttributes(node)
                        node.rightChild = recurseRemove(node.rightChild, nextNode.position)
                        node.update()
                    else:
                        node = node.leftChild or node.rightChild
                elif node.position > innerPosition:
                    node.leftChild = recurseRemove(node.leftChild, innerPosition)
                    node.update()
                elif node.position < innerPosition:
                    node.rightChild = recurseRemove(node.rightChild, innerPosition)
                    node.update()
            if node is not None:
                return node.rebalance()

        self.rootNode = recurseRemove(self.rootNode, position)


# ------------------------------#
if __name__ == '__main__':
    import music21
    music21.mainTest()
