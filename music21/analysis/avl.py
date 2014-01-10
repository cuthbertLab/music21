# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         avl.py
# Purpose:      Implementation of an AVL tree
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------

import random
import unittest


class AVLNode(object):
    r'''
    A node in an AVL tree.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_balance',
        '_height',
        '_key',
        '_leftChild',
        '_rightChild',
        )

    ### INITIALIZER ###

    def __init__(self, key):
        self._balance = 0
        self._height = 0
        self._key = key
        self._leftChild = None
        self._rightChild = None

    ### SPECIAL METHODS ###

    def __repr__(self):
        return '<{}: {}>'.format(
            type(self).__name__,
            self.key,
            )

    ### PRIVATE METHODS ###

    def _update(self):
        leftHeight = -1
        rightHeight = -1
        if self.leftChild is not None:
            leftHeight = self.leftChild.height
        if self.rightChild is not None:
            rightHeight = self.rightChild.height
        self._height = max(leftHeight, rightHeight) + 1
        self._balance = rightHeight - leftHeight
        return self.height

    ### PUBLIC PROPERTIES ###

    @property
    def balance(self):
        return self._balance

    @property
    def height(self):
        return self._height

    @property
    def key(self):
        return self._key

    @property
    def leftChild(self):
        return self._leftChild

    @leftChild.setter
    def leftChild(self, node):
        self._leftChild = node
        self._update()

    @property
    def rightChild(self):
        return self._rightChild

    @rightChild.setter
    def rightChild(self, node):
        self._rightChild = node
        self._update()


class AVLTree(object):
    r'''
    An AVL tree.
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_root'
        )

    ### INITIALIZER ###

    def __init__(self):
        self._root = None

    ### SPECIAL METHODS ###

    def __iter__(self):
        def recurse(node):
            if node is not None:
                for child in recurse(node.leftChild):
                    yield child
                yield node
                for child in recurse(node.rightChild):
                    yield child
        return recurse(self.root)

    ### PRIVATE METHODS ###

    def _insert(self, node, key):
        if node is None:
            return AVLNode(key)
        if key < node.key:
            node.leftChild = self._insert(node.leftChild, key)
        elif node.key < key:
            node.rightChild = self._insert(node.rightChild, key)
        return self._rebalance(node)

    def _rebalance(self, node):
        if node is not None:
            if 1 < node.balance:
                if 0 <= node.rightChild.balance:
                    node = self._rotateRightRight(node)
                else:
                    node = self._rotateRightLeft(node)
            elif node.balance < -1:
                if node.leftChild.balance <= 0:
                    node = self._rotateLeftLeft(node)
                else:
                    node = self._rotateLeftRight(node)
            assert -1 <= node.balance <= 1
        return node

    def _remove(self, node, key):
        if node is not None:
            if node.key == key:
                if node.leftChild and node.rightChild:
                    nextNode = node.rightChild
                    while nextNode.leftChild:
                        nextNode = nextNode.leftChild
                    node._key = nextNode._key
                    node.rightChild = self._remove(
                        node.rightChild, nextNode.key)
                else:
                    node = node.leftChild or node.rightChild
            elif key < node.key:
                node.leftChild = self._remove(node.leftChild, key)
            elif node.key < key:
                node.rightChild = self._remove(node.rightChild, key)
        return self._rebalance(node)

    def _rotateLeftLeft(self, node):
        nextNode = node.leftChild
        node.leftChild = nextNode.rightChild
        nextNode.rightChild = node
        return nextNode

    def _rotateLeftRight(self, node):
        node.leftChild = self._rotateRightRight(node.leftChild)
        nextNode = self._rotateLeftLeft(node)
        return nextNode

    def _rotateRightLeft(self, node):
        node.rightChild = self._rotateLeftLeft(node.rightChild)
        nextNode = self._rotateRightRight(node)
        return nextNode

    def _rotateRightRight(self, node):
        nextNode = node.rightChild
        node.rightChild = nextNode.leftChild
        nextNode.leftChild = node
        return nextNode

    ### PUBLIC METHODS ###

    def insert(self, key):
        self._root = self._insert(self._root, key)

    def remove(self, key):
        self._root = self._remove(self._root, key)

    ### PUBLIC PROPERTIES ###

    @property
    def root(self):
        return self._root


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testAVLTree(self):
        for attempt in range(100):
            items = range(100)
            random.shuffle(items)
            tree = AVLTree()
            for i, item in enumerate(items):
                tree.insert(item)
                inorder = [node.key for node in tree]
                compare = list(sorted(items[:i + 1]))
                assert inorder == compare
            random.shuffle(items)
            while items:
                item = items.pop()
                tree.remove(item)
                inorder = [node.key for node in tree]
                compare = list(sorted(items[:i + 1]))
                assert inorder == compare


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)
