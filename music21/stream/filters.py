# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         stream/filter.py
# Purpose:      classes for filtering iterators of  streams...
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2017 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The filter module contains :class:`~music21.stream.filters.StreamFilter` objects
which are used by :class:`~music21.stream.iterator.StreamIterator` objects to
decide whether or not a given element matches the list of elements that are being
filtered.  Filters are used by methods on streams such as
:meth:`~music21.stream.Stream.getElementsByClass` to filter elements by classes.
'''

#import inspect
import unittest
from music21 import common
from music21.common import opFrac

#------------------------------------------------------------------------------

class StreamFilter(object):
    '''
    A filter is an object that when called returns True or False
    about whether an element in the stream matches the filter.

    A lambda expression: `lambda el, iterator: True if EXP else False` can also be
    used as a very simple filter.

    Filters can also raise StopIteration if no other elements in this Stream
    can possibly fit.

    The `StreamFilter` object does nothing in itself but subclasses are crucial
    in filtering out elements according to different properties.

    Each subclass of `StreamFilter` should set its `.derivationStr` which is
    a string that determines which a derived Stream based on this filter should be called

    >>> sf = stream.filters.StreamFilter()
    >>> sf
    <music21.stream.filters.StreamFilter object at 0x1051de828>
    >>> sf.derivationStr
    'streamFilter'

    StreamFilters also have these two properties which help in certain debug operations

    >>> 'StreamFilter' in sf.classSet
    True
    >>> sf.classes
    ('StreamFilter', 'object')

    '''
    derivationStr = 'streamFilter'

    def __init__(self):
        pass # store streamIterator?

    # commented out to make faster, but will be called if exists.
    #def reset(self):
    #    pass

    #---------------------------------------------------------------
    # ProtoM21Object things...
    @property
    def classSet(self):
        '''
        this is not cached -- it should be if we end up using it a lot...
        '''
        return common.classTools.getClassSet(self)

    @property
    def classes(self):
        return tuple([x.__name__ for x in self.__class__.mro()])


    def _reprHead(self):
        '''
        returns a head that can be used with .format() to add additional
        elements.

        >>> stream.filters.StreamFilter()._reprHead()
        '<music21.stream.filters.StreamFilter {0}>'
        '''
        return '<{0}.{1} '.format(self.__module__, self.__class__.__name__) + '{0}>'

    def __call__(self, item, iterator):
        return True

class IsFilter(StreamFilter):
    '''
    filter on items where x IS y

    >>> s = stream.Stream()
    >>> s.insert(0, key.KeySignature(-3))
    >>> n = note.Note('C#')
    >>> s.append(n)
    >>> s.append(note.Rest())
    >>> isFilter = stream.filters.IsFilter(n)
    >>> isFilter.derivationStr
    'is'
    >>> isFilter.target
    (<music21.note.Note C#>,)
    >>> isFilter.numToFind
    1

    `.numToFind` is used so that once all elements are found, the iterator can short circuit.


    >>> for el in s.iter.addFilter(isFilter):
    ...     print(el is n)
    True

    Multiple elements can also be passed into the isFilter:

    >>> s = stream.Stream()
    >>> s.insert(0, key.KeySignature(-3))
    >>> n = note.Note('C#')
    >>> s.append(n)
    >>> r = note.Rest()
    >>> s.append(r)
    >>> isFilter2 = stream.filters.IsFilter([n, r])
    >>> isFilter2.numToFind
    2

    >>> for el in s.iter.addFilter(isFilter2):
    ...     print(el)
    <music21.note.Note C#>
    <music21.note.Rest rest>

    '''
    derivationStr = 'is'

    def __init__(self, target=()):
        super(IsFilter, self).__init__()
        if not common.isListLike(target):
            target = (target,)

        self.target = target
        self.numToFind = len(target)

    def reset(self):
        self.numToFind = len(self.target)

    def __call__(self, item, iterator):
        if self.numToFind == 0: # short circuit -- we already have
            raise StopIteration

        if item in self.target:
            # would popping the item be faster? No: then can't use for IsNotFilter
            self.numToFind -= 1
            return True
        else:
            return False

class IsNotFilter(IsFilter):
    '''
    Filter out everything but an item or list of items:

    >>> s = stream.Stream()
    >>> s.insert(0, key.KeySignature(-3))
    >>> n = note.Note('C#')
    >>> s.append(n)
    >>> s.append(note.Rest())
    >>> for el in s.iter.addFilter(stream.filters.IsNotFilter(n)):
    ...     el
    <music21.key.KeySignature of 3 flats>
    <music21.note.Rest rest>

    test that resetting works...

    >>> for el in s.iter.addFilter(stream.filters.IsNotFilter(n)):
    ...     el
    <music21.key.KeySignature of 3 flats>
    <music21.note.Rest rest>


    multiple...

    >>> s = stream.Stream()
    >>> s.insert(0, key.KeySignature(-3))
    >>> n = note.Note('C#')
    >>> s.append(n)
    >>> r = note.Rest()
    >>> s.append(r)
    >>> for el in s.iter.addFilter(stream.filters.IsNotFilter([n, r])):
    ...     print(el)
    <music21.key.KeySignature of 3 flats>
    '''
    derivationStr = 'isNot'

    def __init__(self, target=()):
        super(IsNotFilter, self).__init__(target)
        self.numToFind = float('inf') # there can always be more to find

    def reset(self):
        pass # do nothing: inf - 1 = inf

    def __call__(self, item, iterator):
        return not super(IsNotFilter, self).__call__(item, iterator)


class IdFilter(StreamFilter):
    '''
    filters on ids. used by stream.getElementById.
    No corresponding iterator call.

    Only a single Id can be passed in.  Always returns a single item.

    '''
    derivationStr = 'getElementById'

    def __init__(self, searchId=None):
        super(IdFilter, self).__init__()
        try:
            searchIdLower = searchId.lower()
        except AttributeError: # not a string
            searchIdLower = searchId
        self.searchId = searchIdLower

    def __call__(self, item, iterator):
        if item.id == self.searchId:
            return True
        else:
            try:
                return item.id.lower() == self.searchId
            except AttributeError: # item.id is not a string
                pass
            return False

class ClassFilter(StreamFilter):
    '''
    ClassFilter is used by .getElementsByClass() to
    find elements belonging to a class or a list of classes.

    >>> s = stream.Stream()
    >>> s.append(note.Note('C'))
    >>> s.append(note.Rest())
    >>> s.append(note.Note('D'))
    >>> sI = iter(s)
    >>> sI
    <music21.stream.iterator.StreamIterator for Stream:0x104843828 @:0>
    >>> for x in sI:
    ...     print(x)
    <music21.note.Note C>
    <music21.note.Rest rest>
    <music21.note.Note D>

    >>> sI.filters.append(stream.filters.ClassFilter('Note'))
    >>> sI.filters
    [<music21.stream.filters.ClassFilter Note>]

    >>> for x in sI:
    ...     print(x)
    <music21.note.Note C>
    <music21.note.Note D>

    '''
    derivationStr = 'getElementsByClass'

    def __init__(self, classList=()):
        super(ClassFilter, self).__init__()

        if not common.isListLike(classList):
            classList = (classList,)

        self.classList = classList

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return False
        if self.classList != other.classList:
            return False
        return True

    def __call__(self, item, iterator):
        return item.isClassOrSubclass(self.classList)

    def __repr__(self):
        if len(self.classList) == 1:
            return self._reprHead().format(str(self.classList[0]))
        else:
            return self._reprHead().format(str(self.classList))


class ClassNotFilter(ClassFilter):
    '''
    Returns elements not of the class.

    >>> s = stream.Stream()
    >>> s.append(note.Note('C'))
    >>> s.append(note.Rest())
    >>> s.append(note.Note('D'))
    >>> sI = iter(s)

    >>> sI.filters.append(stream.filters.ClassNotFilter('Note'))
    >>> sI.filters
    [<music21.stream.filters.ClassNotFilter Note>]

    >>> for x in sI:
    ...     print(x)
    <music21.note.Rest rest>
    '''
    derivationStr = 'getElementsNotOfClass'

    def __call__(self, item, iterator):
        return not item.isClassOrSubclass(self.classList)


class GroupFilter(StreamFilter):
    '''
    Returns elements with a certain group.

    >>> n1 = note.Note("C")
    >>> n1.groups.append('trombone')
    >>> n2 = note.Note("D")
    >>> n2.groups.append('trombone')
    >>> n2.groups.append('tuba')
    >>> n3 = note.Note("E")
    >>> n3.groups.append('tuba')
    >>> s1 = stream.Stream()
    >>> s1.append(n1)
    >>> s1.append(n2)
    >>> s1.append(n3)
    >>> GF = stream.filters.GroupFilter

    >>> for thisNote in iter(s1).addFilter(GF("trombone")):
    ...     print(thisNote.name)
    C
    D
    >>> for thisNote in iter(s1).addFilter(GF("tuba")):
    ...     print(thisNote.name)
    D
    E

    '''
    derivationStr = 'getElementsByGroup'

    def __init__(self, groupFilterList=()):
        super(GroupFilter, self).__init__()

        if not common.isListLike(groupFilterList):
            groupFilterList = [groupFilterList]
        self.groupFilterList = groupFilterList

    def __call__(self, item, iterator):
        eGroups = item.groups
        for groupName in self.groupFilterList:
            if groupName in eGroups:
                return True
        return False

class OffsetFilter(StreamFilter):
    '''
    see iterator.getElementsByOffset()

    Finds elements that match a given offset range.
    '''
    derivationStr = 'getElementsByOffset'

    def __init__(self, offsetStart=0.0, offsetEnd=None,
                    includeEndBoundary=True, mustFinishInSpan=False,
                    mustBeginInSpan=True, includeElementsThatEndAtStart=True):
        super(OffsetFilter, self).__init__()

        self.offsetStart = opFrac(offsetStart)
        if offsetEnd is None:
            self.offsetEnd = offsetStart
            self.zeroLengthSearch = True
        else:
            self.offsetEnd = opFrac(offsetEnd)
            if offsetEnd > offsetStart:
                self.zeroLengthSearch = False
            else:
                self.zeroLengthSearch = True

        self.mustFinishInSpan = mustFinishInSpan
        self.mustBeginInSpan = mustBeginInSpan
        self.includeEndBoundary = includeEndBoundary
        self.includeElementsThatEndAtStart = includeElementsThatEndAtStart


    def __call__(self, e, iterator):
        dur = e.duration
        s = iterator.srcStream
        if s is e:
            return False
        offset = s.elementOffset(e)

        #offset = common.cleanupFloat(offset)

        if offset > self.offsetEnd:  # anything that ends after the span is definitely out
            if s.isSorted:
                # if sorted, optimize by breaking after exceeding offsetEnd
                # eventually we could do a binary search to speed up...
                raise StopIteration
            else:
                return False

        elementEnd = opFrac(offset + dur.quarterLength)
        if elementEnd < self.offsetStart:
            # anything that finishes before the span ends is definitely out
            return False

        if dur.quarterLength == 0:
            elementIsZeroLength = True
        else:
            elementIsZeroLength = False


        # all the simple cases done! Now need to filter out those that
        # are border cases depending on settings

        if self.zeroLengthSearch is True and elementIsZeroLength is True:
            # zero Length Searches -- include all zeroLengthElements
            return True


        if self.mustFinishInSpan is True:
            if elementEnd > self.offsetEnd:
                #environLocal.warn([elementEnd, offsetEnd, e])
                return False
            if self.includeEndBoundary is False:
                # we include the end boundary if the search is zeroLength --
                # otherwise nothing can be retrieved
                if elementEnd == self.offsetEnd:
                    return False

        if self.mustBeginInSpan is True:
            if offset < self.offsetStart:
                return False
            if self.includeEndBoundary is False:
                if offset >= self.offsetEnd:
                    # >= is unnecessary, should just be ==, but better safe than sorry
                    return False

        if self.mustBeginInSpan is False:
            if elementIsZeroLength is False:
                if elementEnd == self.offsetEnd and self.zeroLengthSearch is True:
                    return False
        if self.includeEndBoundary is False:
            if offset >= self.offsetEnd:
                return False

        if self.includeElementsThatEndAtStart is False and elementEnd == self.offsetStart:
            return False

        return True


class Test(unittest.TestCase):
    pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
