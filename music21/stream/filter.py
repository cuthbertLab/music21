# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         stream/filter.py
# Purpose:      classes for filtering iterators of  streams...
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

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
    '''
    derivationStr = 'streamFilter'
    
    def __init__(self):
        pass # store streamIterator?

    # commented out to make faster, but will be called if exists.
    #def reset(self):
    #    pass

    def _reprHead(self):
        '''
        returns a head that can be used with .format() to add additional
        elements.
        
        >>> stream.filter.StreamFilter()._reprHead()
        '<music21.stream.filter.StreamFilter {0}>'
        '''
        return '<{0}.{1} '.format(self.__module__, self.__class__.__name__) + '{0}>'

    
class IsFilter(StreamFilter):
    derivationStr = 'is'
    '''
    filter on items where x IS y
    
    >>> s = stream.Stream()
    >>> s.insert(0, key.KeySignature(-3))
    >>> n = note.Note('C#')
    >>> s.append(n)
    >>> s.append(note.Rest())
    >>> for el in s.iter.addFilter(stream.filter.IsFilter(n)):
    ...     print(el is n)
    True    

    multiple...

    >>> s = stream.Stream()
    >>> s.insert(0, key.KeySignature(-3))
    >>> n = note.Note('C#')
    >>> s.append(n)
    >>> r = note.Rest()
    >>> s.append(r)
    >>> for el in s.iter.addFilter(stream.filter.IsFilter([n, r])):
    ...     print(el)
    <music21.note.Note C#>
    <music21.note.Rest rest>

    '''
    def __init__(self, target):
        super(IsFilter, self).__init__()
        if not common.isListLike(target):
            target = (target,)

        self.target = target
        self.numToFind = len(target)
    
    def reset(self):
        self.numToFind = len(self.target)
    
    
    def __call__(self, item, iterator):
        if self.numToFind == 0:
            raise StopIteration
        
        if item in self.target:
            # would popping the item be faster?
            self.numToFind -= 1
            return True
        else:
            return False

class IsNotFilter(IsFilter):
    derivationStr = 'isNot'

    def __call__(self, item, iterator):
        return not super(IsNotFilter, self).__call__(item, iterator)


class IdFilter(StreamFilter):
    '''
    filters on ids. used by stream.getElementById.
    No corresponding iterator call.
    '''
    derivationStr = 'getElementById'

    def __init__(self, searchId):
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
    >>> s = stream.Stream()
    >>> s.append(note.Note('C'))
    >>> s.append(note.Rest())
    >>> s.append(note.Note('D'))
    >>> sI = s.__iter__()
    >>> sI
    <music21.stream.iterator.StreamIterator for Stream:0x104843828 @:0>
    >>> for x in sI:
    ...     print(x)
    <music21.note.Note C>
    <music21.note.Rest rest>
    <music21.note.Note D>

    >>> sI.filters.append(stream.filter.ClassFilter('Note'))
    >>> sI.filters
    [<music21.stream.filter.ClassFilter Note>]
    
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
    >>> sI = s.__iter__()

    >>> sI.filters.append(stream.filter.ClassNotFilter('Note'))
    >>> sI.filters
    [<music21.stream.filter.ClassNotFilter Note>]
    
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
    >>> GF = stream.filter.GroupFilter
    
    >>> for thisNote in s1.__iter__().addFilter(GF("trombone")):
    ...     print(thisNote.name)
    C
    D
    >>> for thisNote in s1.__iter__().addFilter(GF("tuba")):
    ...     print(thisNote.name)
    D
    E

    '''
    derivationStr = 'getElementsByGroup'
    
    def __init__(self, groupFilterList):
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
    '''
    derivationStr = 'getElementsByOffset'
    
    def __init__(self, offsetStart, offsetEnd=None,
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
        if elementEnd < self.offsetStart:  # anything that finishes before the span ends is definitely out
            return False

        if dur.quarterLength == 0:
            elementIsZeroLength = True
        else:
            elementIsZeroLength = False


        # all the simple cases done! Now need to filter out those that are border cases depending on settings

        if self.zeroLengthSearch is True and elementIsZeroLength is True:
            # zero Length Searches -- include all zeroLengthElements
            return True


        if self.mustFinishInSpan is True:
            if elementEnd > self.offsetEnd:
                #environLocal.warn([elementEnd, offsetEnd, e])
                return False
            if self.includeEndBoundary is False:
                # we include the end boundary if the search is zeroLength -- otherwise nothing can be retrieved
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
