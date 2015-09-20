# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         stream/iterator.py
# Purpose:      classes for walking through streams and filtering...
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
this class contains iterators and filters for walking through streams
'''
import collections
import copy
import unittest

from music21 import common

from music21.exceptions21 import Music21Exception, StreamException

#------------------------------------------------------------------------------

class StreamIterator(object):
    '''
    An Iterator object used to handle getting items from Streams.
    The :meth:`~music21.stream.Stream.__iter__` method
    returns this object, passing a reference to self.

    Note that this iterator automatically sets the active site of
    returned elements to the source Stream.

    Sets:

    * StreamIterator.srcStream -- the Stream iterated over
    * StreamIterator.index -- current index item
    * StreamIterator.streamLength -- the len() of srcStream
    * StreamIterator.srcStreamElements -- srcStream.elements
    * StreamIterator.cleanupOnStop -- should the StreamIterator delete the
      reference to srcStream and srcStreamElements when stopping? default
      True

    '''
    def __init__(self, srcStream, filters=None):
        self.srcStream = srcStream
        self.index = 0
        self.streamLength = len(self.srcStream)
        self.srcStreamElements = self.srcStream.elements
        self.cleanupOnStop = True

        if filters is None:
            filters = []
        elif not common.isIterable(filters):
            filters = [filters]
        elif isinstance(filters, tuple) or isinstance(filters, set):
            filters = list(filters) # mutable....
        
        self.filters = filters

    def __iter__(self):
        return self

    def __next__(self):
        # calling .elements here will sort if autoSort = True
        # thus, this does not need to sort or check autoSort status
        if self.index >= self.streamLength:
            self.stop()
        #environLocal.printDebug(['self.srcStream', self.srcStream, self.index, 'len(self.srcStream)', len(self.srcStream), 'len(self._endElements)', len(self.srcStream._endElements), 'len(self.srcStream._elements)', len(self.srcStream._elements), 'len(self.srcStream.elements)', len(self.srcStream.elements)])
        try:
            post = self.srcStreamElements[self.index]
        except IndexError:
            raise StreamException("Cannot get index %d from Stream %r, elements were %r" % (self.index, self.srcStream, self.srcStreamElements))
        # here, the activeSite of extracted element is being set to Stream
        # that is the source of the iteration
        post.activeSite = self.srcStream
        self.index += 1
        return post

    next = __next__ # python2
    
    def stop(self):
        '''
        stop iteration; and cleanup if need be.
        '''
        if self.cleanupOnStop is not False:
            del self.srcStream
            del self.srcStreamElements
            self.srcStream = None
            self.srcStreamElements = None
        raise StopIteration
    
    
    def __getitem__(self, k):
        '''
        if you are in the iterator, you should still be able to request other items...uses self.srcStream.__getitem__

        >>> s = stream.Stream()
        >>> s.insert(0, note.Note('F#'))
        >>> s.repeatAppend(note.Note('C'), 2)
        >>> sI = s.__iter__()
        >>> sI
        <music21.stream.StreamIterator object at 0x...>
        >>> sI.srcStream is s
        True

        >>> try:
        ...     while True:
        ...         n = sI.next()
        ...         printer = (repr(n), repr(sI[0]))
        ...         print(printer)
        ... except StopIteration:
        ...     pass
        ('<music21.note.Note F#>', '<music21.note.Note F#>')
        ('<music21.note.Note C>', '<music21.note.Note F#>')
        ('<music21.note.Note C>', '<music21.note.Note F#>')
        >>> sI.srcStream is None
        True

        Demo of cleanupOnStop = False

        >>> sI2 = s.__iter__()
        >>> sI2.cleanupOnStop = False
        >>> try:
        ...     while True:
        ...         n = sI2.next()
        ... except StopIteration:
        ...     pass
        >>> sI2.srcStream is s
        True

        '''
        return self.srcStream.__getitem__(k)

#------------------------------------------------------------------------------
class RecursiveIterator(StreamIterator):


    


class Test(unittest.TestCase):
    pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)