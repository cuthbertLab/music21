# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         stream/iterator.py
# Purpose:      classes for walking through streams...
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
this class contains iterators and filters for walking through streams

StreamIterators are explicitly allowed to access private methods on streams.
'''
import unittest

from music21 import common
from music21.stream import filter
from music21.exceptions21 import StreamException

#------------------------------------------------------------------------------
class StreamIteratorException(StreamException):
    pass

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
    * StreamIterator.streamLength -- length of elements.
    
    * StreamIterator.srcStreamElements -- srcStream._elements
    * StreamIterator.cleanupOnStop -- should the StreamIterator delete the
      reference to srcStream and srcStreamElements when stopping? default
      False
    * StreamIterator.activeInformation -- a dict that contains information
      about where we are in the parse.  Especially useful for recursive
      streams. 'stream' = the stream that is currently active, 'index'
      where in `.elements` we are, `iterSection` is `_elements` or `_endElements`,
      and `sectionIndex` is where we are in the iterSection, or -1 if
      we have not started. This dict is shared among all sub iterators.

    '''
    def __init__(self, 
                 srcStream, 
                 filters=None, 
                 restoreActiveSites=True,
                 activeInformation=None):

        self.srcStream = srcStream
        self.index = 0
        
        # use .elements instead of ._elements/etc. so that it is sorted...
        self.srcStreamElements = srcStream.elements
        self.streamLength = len(self.srcStreamElements)
        
        # this information can help a 
        self.elementsLength = len(self.srcStream._elements)
        self.sectionIndex = -1
        self.iterSection = '_elements'
        
        self.cleanupOnStop = False
        self.restoreActiveSites = restoreActiveSites

        if filters is None:
            filters = []
        elif not common.isIterable(filters):
            filters = [filters]
        elif isinstance(filters, tuple) or isinstance(filters, set):
            filters = list(filters) # mutable....
        # self.filters is a list of expressions that
        # return True or False for an element for
        # whether it should be yielded.
        self.filters = filters
        self._len = None
        self._matchingElements = None

        # keep track of where we are in the parse. 
        # esp important for recursive streams...
        if activeInformation is not None:
            self.activeInformation = activeInformation
        else:
            self.activeInformation = {}
            self.updateActiveInformation()

    def __repr__(self):
        streamClass = self.srcStream.__class__.__name__
        srcStreamId = self.srcStream.id
        try:
            srcStreamId = hex(srcStreamId)
        except TypeError:
            pass

        if streamClass == 'Measure' and self.srcStream.number != 0:
            srcStreamId = 'm.' + str(self.srcStream.number)
        
        return '<{0}.{1} for {2}:{3} @:{4}>'.format(
                    self.__module__, self.__class__.__name__,
                    streamClass,
                    srcStreamId,
                    self.index
                )

    def __iter__(self):
        self.reset()
        return self
        
        
    def __next__(self):
        while self.index < self.streamLength:                    
            if self.index >= self.elementsLength:
                self.iterSection = '_endElements'
                self.sectionIndex = self.index - self.elementsLength
            else:
                self.sectionIndex = self.index
            
            self.index += 1 # increment early in case of an error.
            
            
            
            try:
                e = self.srcStreamElements[self.index - 1]
            except IndexError:
                # this may happen in the number of elements has changed
                continue
    
            if self.matchesFilters(e) is False:
                continue
            
            if self.restoreActiveSites is True:
                e.activeSite = self.srcStream
    
            self.updateActiveInformation()
            return e

        self.cleanup()
        raise StopIteration
        
    next = __next__

    def __len__(self):
        '''
        returns the length of the elements that
        match the filter set.
        
        >>> s = converter.parse('tinynotation: 3/4 c4 d e f g a', makeNotation=False)
        >>> len(s)
        7
        >>> len(s.iter)
        7
        >>> len(s.iter.notes)
        6
        >>> [n.name for n in s.iter.notes]
        ['C', 'D', 'E', 'F', 'G', 'A']
        '''
        if self._len is not None:
            return self._len
        self._len = len(self.matchingElements())
        self.reset()
        return self._len


    #----------------------------------------------------------------
    # start and stop
    
    def updateActiveInformation(self):
        '''
        Updates the (shared) activeInformation dictionary
        with information about
        where we are.
        
        Call before any element return
        '''
        ai = self.activeInformation
        ai['stream'] = self.srcStream
        ai['index'] = self.index - 1
        ai['iterSection'] = self.iterSection
        ai['sectionIndex'] = self.sectionIndex

    def reset(self):
        '''
        reset prior to iteration
        '''
        self.index = 0
        self.iterSection = '_elements'
        self.updateActiveInformation()
        for f in self.filters:
            if hasattr(f, 'reset'):
                f.reset()


    def resetCaches(self):
        '''
        reset any cached data. -- do not use this at
        the start of iteration since we might as well
        save this information. But do call it if 
        the filter changes.
        '''
        self._len = None
        self._matchingElements = None
    
    def cleanup(self):
        '''
        stop iteration; and cleanup if need be.
        '''
        if self.cleanupOnStop is not False:
            self.reset()

            del self.srcStream
            del self.srcStreamElements
            self.srcStream = None
            self.srcStreamElements = ()

    #----------------------------------------------------------------
    # getting items


    def matchingElements(self):
        '''
        returns a list of elements that match the filter.
        
        This sort of defeats the point of using a generator, so only used if 
        it's requested by __len__ or __getitem__ etc.
        
        Subclasses should override to cache anything they need saved (index, 
        recursion objects, etc.)
        
        activeSite will not be set.  
        
        Cached for speed.
        
        >>> s = converter.parse('tinynotation: 3/4 c4 d e f g a', makeNotation=False)
        >>> s.id = 'tn3/4'
        >>> sI = s.iter
        >>> sI
        <music21.stream.iterator.StreamIterator for Part:tn3/4 @:0>

        >>> sI.matchingElements()
        [<music21.meter.TimeSignature 3/4>, <music21.note.Note C>, <music21.note.Note D>, 
         <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>, 
         <music21.note.Note A>]

        >>> sI.notes
        <music21.stream.iterator.StreamIterator for Part:tn3/4 @:0>
        >>> sI.notes is sI
        True

        >>> sI.matchingElements()
        [<music21.note.Note C>, <music21.note.Note D>, 
         <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>, 
         <music21.note.Note A>]
        '''
        if self._matchingElements is not None:
            return self._matchingElements
        
        savedIndex = self.index
        savedRestoreActiveSites = self.restoreActiveSites
        self.restoreActiveSites = True
        
        me = [x for x in self]
        
        self.reset()
        
        self.index = savedIndex
        self.restoreActiveSites = savedRestoreActiveSites        
        self._matchingElements = me

        return me


    def matchesFilters(self, e):
        '''
        returns False if any filter returns False, True otherwise.
        '''
        for f in self.filters:
            try:
                if f(e, self) is False:
                    return False
            except StopIteration:
                raise
        return True



    
    def __getitem__(self, k):
        '''
        if you are in the iterator, you should still be able to request other items...
        uses self.srcStream.__getitem__

        >>> s = stream.Stream()
        >>> s.insert(0, note.Note('F#'))
        >>> s.repeatAppend(note.Note('C'), 2)
        >>> sI = s.iter
        >>> sI
        <music21.stream.iterator.StreamIterator for Stream:0x104743be0 @:0>

        >>> sI.srcStream is s
        True

        >>> for n in sI:
        ...    printer = (repr(n), repr(sI[0]))
        ...    print(printer)
        ('<music21.note.Note F#>', '<music21.note.Note F#>')
        ('<music21.note.Note C>', '<music21.note.Note F#>')
        ('<music21.note.Note C>', '<music21.note.Note F#>')
        >>> sI.srcStream is s
        True
        
        Filters, such as "notes" apply.
        
        >>> s.insert(0, clef.TrebleClef())
        >>> s[0]
        <music21.clef.TrebleClef>
        >>> s.iter.notes[0]
        <music21.note.Note F#>

        Demo of cleanupOnStop = True

        >>> sI.cleanupOnStop = True
        >>> for n in sI:
        ...    printer = (repr(n), repr(sI[0]))
        ...    print(printer)
        ('<music21.note.Note F#>', '<music21.note.Note F#>')
        ('<music21.note.Note C>', '<music21.note.Note F#>')
        ('<music21.note.Note C>', '<music21.note.Note F#>')
        >>> sI.srcStream is None
        True
        >>> for n in sI:
        ...    printer = (repr(n), repr(sI[0]))
        ...    print(printer)

        (nothing is printed)
        '''
        fe = self.matchingElements()
        e = fe[k]

        return e
        
    
    def _newBaseStream(self):
        '''
        since we can't import "Stream" here, we will
        look in srcStream.__class__.mro() for the Stream
        object to import.
        
        
        >>> p = stream.Part()
        >>> pi = p.iter
        >>> s = pi._newBaseStream()
        >>> s
        <music21.stream.Stream 0x1047eb2e8>
        
        >>> pi.srcStream = note.Note()
        >>> pi._newBaseStream()
        Traceback (most recent call last):
        StreamIteratorException: ...
        '''
        StreamBase = None
        for x in self.srcStream.__class__.mro():
            if x.__name__ == 'Stream':
                StreamBase = x
                break

        try:
            return StreamBase()
        except TypeError: # 'NoneType' object is not callable.
            raise StreamIteratorException(
                    "You've given a 'stream' that is not a stream! {0}".format(self.srcStream)) 
    
    def stream(self, returnStreamSubClass=True):
        '''
        return a new stream from this iterator.
        
        Does nothing except copy if there are no filters, but a drop in
        replacement for the old .getElementsByClass() etc. if it does.
        
        In other words:
        
        `s.getElementsByClass()` == `s.iter.getElementsByClass().stream()`
        
        >>> s = stream.Part()
        >>> s.insert(0, note.Note('C'))
        >>> s.append(note.Rest())
        >>> s.append(note.Note('D'))
        >>> b = bar.Barline()
        >>> s.storeAtEnd(b)
        
        >>> s2 = s.iter.getElementsByClass('Note').stream()
        >>> s2.show('t')
        {0.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        >>> s2.derivation.method
        'getElementsByClass'
        >>> s2
        <music21.stream.Part ...>
        
        >>> s3 = s.iter.stream()
        >>> s3.show('t')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Rest rest>
        {2.0} <music21.note.Note D>
        {3.0} <music21.bar.Barline style=regular>
        
        >>> s3.elementOffset(b, stringReturns=True)
        'highestTime'
        
        >>> s4 = s.iter.getElementsByClass('Barline').stream()
        >>> s4.show('t')
        {0.0} <music21.bar.Barline style=regular>
        
        OMIT_FROM_DOCS
        
        >>> s4._endElements[0] is b
        True
        '''
        ss = self.srcStream

        if returnStreamSubClass is True:
            try:
                found = ss.__class__()
            except TypeError:
                found = self._newBaseStream()
        else:
            found = self._newBaseStream()
            
        found.mergeAttributes(ss)
        found.derivation.origin = ss
        derivationMethods = []
        for f in self.filters:
            derivationMethods.append(f.derivationStr)
        found.derivation.method = '.'.join(derivationMethods)
        
        fe = self.matchingElements()
        for e in fe:
            o = ss.elementOffset(e, stringReturns=True)
            if not isinstance(o, str):                
                found._insertCore(o, e, ignoreSort=True)
            else:
                if o == 'highestTime':
                    found._storeAtEndCore(e)
                else:
                    # TODO: something different...
                    found._storeAtEndCore(e)

        # if this stream was sorted, the resultant stream is sorted        
        if len(fe) > 0:
            found.elementsChanged(clearIsSorted=False)
        
        return found
    
    @property
    def activeElementList(self):
        '''
        returns the element list ('_elements' or '_endElements')
        for the current activeInformation
        '''
        return getattr(self.activeInformation['stream'], self.activeInformation['iterSection'])
    
    
    #-------------------------------------------------------------
    def addFilter(self, newFilter):
        '''
        adds a filter to the list.
        
        resets caches -- do not add filters any other way
        
        # TODO: support remove filter.
        '''
        if newFilter not in self.filters:
            self.filters.append(newFilter)
            
        self.resetCaches()
        return self
    
    def removeFilter(self, oldFilter):
        if oldFilter in self.filters:
            self.filters.pop(self.filters.index(oldFilter))
    
        self.resetCaches()
        return self
    
    
    
    
    def getElementsByClass(self, classFilterList):
        '''
        Add a filter to the Iterator to remove all elements
        except those that match one
        or more classes in the `classFilterList`. A single class
        can also used for the `classFilterList` parameter instead of a List.

        >>> s = stream.Stream(id="s1")
        >>> s.append(note.Note('C'))
        >>> r = note.Rest()
        >>> s.append(r)
        >>> s.append(note.Note('D'))
        >>> for el in s.iter.getElementsByClass('Rest'):
        ...     print(el)
        <music21.note.Rest rest>
                
        
        ActiveSite is restored...
        
        >>> s2 = stream.Stream(id="s2")
        >>> s2.insert(0, r)
        >>> r.activeSite.id
        's2'

        >>> for el in s.iter.getElementsByClass('Rest'):
        ...     print(el.activeSite.id)
        s1   
        
        
        Classes work in addition to strings...
        
        >>> for el in s.iter.getElementsByClass(note.Rest):
        ...     print(el)
        <music21.note.Rest rest>
        
        '''
        self.addFilter(filter.ClassFilter(classFilterList))
        return self

    def getElementsNotOfClass(self, classFilterList):
        '''
        Adds a filter, removing all Elements that do not
        match the one or more classes in the `classFilterList`.

        In lieu of a list, a single class can be used as the `classFilterList` parameter.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Rest(), list(range(10)))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = list(a.iter.getElementsNotOfClass(note.Note))
        >>> len(found)
        10

        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), list(range(15)))
        >>> a.insert(b)
        >>> # here, it gets elements from within a stream
        >>> # this probably should not do this, as it is one layer lower
        >>> found = list(a.flat.iter.getElementsNotOfClass(note.Rest))
        >>> len(found)
        4
        >>> found = list(a.flat.iter.getElementsNotOfClass(note.Note))
        >>> len(found)
        25
        '''
        self.addFilter(filter.ClassNotFilter(classFilterList))
        return self
        
    def getElementsByGroup(self, groupFilterList):
        '''
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
        
        >>> tboneSubStream = s1.iter.getElementsByGroup("trombone")
        >>> for thisNote in tboneSubStream:
        ...     print(thisNote.name)
        C
        D
        >>> tubaSubStream = s1.iter.getElementsByGroup("tuba")
        >>> for thisNote in tubaSubStream:
        ...     print(thisNote.name)
        D
        E
        '''        
        self.addFilter(filter.GroupFilter(groupFilterList))
        return self


    def getElementsByOffset(self, offsetStart, offsetEnd=None,
                    includeEndBoundary=True, mustFinishInSpan=False,
                    mustBeginInSpan=True, includeElementsThatEndAtStart=True):
        '''
        Adds a filter keeping only Music21Objects that
        are found at a certain offset or within a certain
        offset time range (given the start and optional stop values).


        There are several attributes that govern how this range is
        determined:


        If `mustFinishInSpan` is True then an event that begins
        between offsetStart and offsetEnd but which ends after offsetEnd
        will not be included.  The default is False.


        For instance, a half note at offset 2.0 will be found in
        getElementsByOffset(1.5, 2.5) or getElementsByOffset(1.5, 2.5,
        mustFinishInSpan = False) but not by getElementsByOffset(1.5, 2.5,
        mustFinishInSpan = True).

        The `includeEndBoundary` option determines if an element
        begun just at the offsetEnd should be included.  For instance,
        the half note at offset 2.0 above would be found by
        getElementsByOffset(0, 2.0) or by getElementsByOffset(0, 2.0,
        includeEndBoundary = True) but not by getElementsByOffset(0, 2.0,
        includeEndBoundary = False).

        Setting includeEndBoundary to False at the same time as
        mustFinishInSpan is set to True is probably NOT what you want to do
        unless you want to find things like clefs at the end of the region
        to display as courtesy clefs.

        The `mustBeginInSpan` option determines whether notes or other
        objects that do not begin in the region but are still sounding
        at the beginning of the region are excluded.  The default is
        True -- that is, these notes will not be included.
        For instance the half note at offset 2.0 from above would not be found by
        getElementsByOffset(3.0, 3.5) or getElementsByOffset(3.0, 3.5,
        mustBeginInSpan = True) but it would be found by
        getElementsByOffset(3.0, 3.5, mustBeginInSpan = False)

        Setting includeElementsThatEndAtStart to False is useful for zeroLength
        searches that set mustBeginInSpan == False to not catch notes that were
        playing before the search but that end just before the end of the search type.
        See the code for allPlayingWhileSounding for a demonstration.

        This chart, and the examples below, demonstrate the various
        features of getElementsByOffset.  It is one of the most complex
        methods of music21 but also one of the most powerful, so it
        is worth learning at least the basics.

            .. image:: images/getElementsByOffset.*
                :width: 600




        >>> st1 = stream.Stream()
        >>> n0 = note.Note("C")
        >>> n0.duration.type = "half"
        >>> n0.offset = 0
        >>> st1.insert(n0)
        >>> n2 = note.Note("D")
        >>> n2.duration.type = "half"
        >>> n2.offset = 2
        >>> st1.insert(n2)
        >>> out1 = list(st1.iter.getElementsByOffset(2))
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = list(st1.iter.getElementsByOffset(1, 3))
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = list(st1.iter.getElementsByOffset(1, 3, mustFinishInSpan=True))
        >>> len(out3)
        0
        >>> out4 = list(st1.iter.getElementsByOffset(1, 2))
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = list(st1.iter.getElementsByOffset(1, 2, includeEndBoundary=False))
        >>> len(out5)
        0
        >>> out6 = list(st1.iter.getElementsByOffset(1, 2, includeEndBoundary=False, mustBeginInSpan=False))
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = list(st1.iter.getElementsByOffset(1, 3, mustBeginInSpan=False))
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']
        
        
        Note, that elements that end at the start offset are included if mustBeginInSpan is False
        
        >>> out8 = list(st1.iter.getElementsByOffset(2, 4, mustBeginInSpan=False))
        >>> len(out8)
        2
        >>> [el.step for el in out8]
        ['C', 'D']

        To change this behavior set includeElementsThatEndAtStart=False

        >>> out9 = list(st1.iter.getElementsByOffset(2, 4, mustBeginInSpan=False, includeElementsThatEndAtStart=False))
        >>> len(out9)
        1
        >>> [el.step for el in out9]
        ['D']



        >>> a = stream.Stream(id='a')
        >>> n = note.Note('G')
        >>> n.quarterLength = .5
        >>> a.repeatInsert(n, list(range(8)))
        >>> b = stream.Stream(id='b')
        >>> b.repeatInsert(a, [0, 3, 6])
        >>> c = list(b.iter.getElementsByOffset(2, 6.9))
        >>> len(c)
        2
        >>> c = list(b.flat.iter.getElementsByOffset(2, 6.9))
        >>> len(c)
        10


        Testing multiple zero-length elements with mustBeginInSpan:

        >>> c = clef.TrebleClef()
        >>> ts = meter.TimeSignature('4/4')
        >>> ks = key.KeySignature(2)
        >>> s = stream.Stream()
        >>> s.insert(0.0, c)
        >>> s.insert(0.0, ts)
        >>> s.insert(0.0, ks)
        >>> len(list(s.iter.getElementsByOffset(0.0, mustBeginInSpan=True)))
        3
        >>> len(list(s.iter.getElementsByOffset(0.0, mustBeginInSpan=False)))
        3

        OMIT_FROM_DOCS
        
        Same test as above, but with floats
        
        >>> out1 = list(st1.iter.getElementsByOffset(2.0))
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = list(st1.iter.getElementsByOffset(1.0, 3.0))
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = list(st1.iter.getElementsByOffset(1.0, 3.0, mustFinishInSpan=True))
        >>> len(out3)
        0
        >>> out3b = list(st1.iter.getElementsByOffset(0.0, 3.001, mustFinishInSpan=True))
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'
        >>> out3b = list(st1.iter.getElementsByOffset(1.0, 3.001, mustFinishInSpan=True, mustBeginInSpan=False))
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'


        >>> out4 = list(st1.iter.getElementsByOffset(1.0, 2.0))
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = list(st1.iter.getElementsByOffset(1.0, 2.0, includeEndBoundary=False))
        >>> len(out5)
        0
        >>> out6 = list(st1.iter.getElementsByOffset(1.0, 2.0, includeEndBoundary=False, mustBeginInSpan=False))
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = list(st1.iter.getElementsByOffset(1.0, 3.0, mustBeginInSpan=False))
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']

        :rtype: StreamIterator
        '''        
        self.addFilter(filter.OffsetFilter(offsetStart, offsetEnd, includeEndBoundary,
                                           mustFinishInSpan, mustBeginInSpan,
                                           includeElementsThatEndAtStart))
        return self
    
    #-------------------------------------------------------------
    
    @property
    def notes(self):
        '''
        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> s.append(note.Rest())
        >>> s.append(note.Note('D'))
        >>> for el in s.iter.notes:
        ...     print(el)
        <music21.note.Note C>
        <music21.note.Note D>
        '''
        self.addFilter(filter.ClassFilter('NotRest'))
        return self

    @property
    def notesAndRests(self):
        '''
        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.append(note.Note('C'))
        >>> s.append(note.Rest())
        >>> s.append(note.Note('D'))
        >>> for el in s.iter.notesAndRests:
        ...     print(el)
        <music21.note.Note C>
        <music21.note.Rest rest>
        <music21.note.Note D>
        
        
        chained filters... (this makes no sense since notes is a subset of notesAndRests
        
        
        >>> for el in s.iter.notesAndRests.notes:
        ...     print(el)
        <music21.note.Note C>
        <music21.note.Note D>        
        '''
        self.addFilter(filter.ClassFilter('GeneralNote'))
        return self


#------------------------------------------------------------------------------
class RecursiveIterator(StreamIterator):
    '''
    >>> b = corpus.parse('bwv66.6')
    >>> ri = stream.iterator.RecursiveIterator(b, streamsOnly=True)
    >>> for x in ri:
    ...     print(x)
    <music21.stream.Part Soprano>
    <music21.stream.Measure 0 offset=0.0>
    <music21.stream.Measure 1 offset=1.0>
    <music21.stream.Measure 2 offset=5.0>
    ...
    <music21.stream.Part Alto>
    <music21.stream.Measure 0 offset=0.0>
    ...
    <music21.stream.Part Tenor>
    ...
    <music21.stream.Part Bass>
    ...
    
    But this is how you'll actually use it:
    
    >>> for x in b.recurse(streamsOnly=True):
    ...     print(x)
    <music21.stream.Score 0x10484fd68>
    <music21.stream.Part Soprano>
    <music21.stream.Measure 0 offset=0.0>
    <music21.stream.Measure 1 offset=1.0>
    <music21.stream.Measure 2 offset=5.0>
    ...
    <music21.stream.Part Alto>
    <music21.stream.Measure 0 offset=0.0>
    ...
    <music21.stream.Part Tenor>
    ...
    <music21.stream.Part Bass>
    ...
    
    >>> hasExpressions = lambda el, i: True if (hasattr(el, 'expressions') and len(el.expressions) > 0) else False
    >>> expressive = b.recurse().addFilter(hasExpressions)
    >>> expressive
    <music21.stream.iterator.RecursiveIterator for Score:0x10487f550 @:0>
    
    >>> for el in expressive:
    ...     printer = (el, el.expressions)
    ...     print(printer)
    (<music21.note.Note C#>, [<music21.expressions.Fermata>])
    (<music21.note.Note A>, [<music21.expressions.Fermata>])
    (<music21.note.Note F#>, [<music21.expressions.Fermata>])
    (<music21.note.Note C#>, [<music21.expressions.Fermata>])
    (<music21.note.Note G#>, [<music21.expressions.Fermata>])
    (<music21.note.Note F#>, [<music21.expressions.Fermata>])
    
    >>> len(expressive)
    6
    >>> expressive[-1].measureNumber
    9
    
    '''
    def __init__(self, 
                 srcStream, 
                 filters=None, 
                 restoreActiveSites=True, 
                 activeInformation=None,
                 streamsOnly=False, # to be removed
                 includeSelf=False, # to be removed
                 ): #, parentIterator=None):
        super(RecursiveIterator, self).__init__(srcStream, 
                                                filters, 
                                                restoreActiveSites,
                                                activeInformation=activeInformation)
        self.returnSelf = includeSelf
        self.includeSelf = includeSelf
        if streamsOnly is True:
            self.filters.append(filter.ClassFilter('Stream'))
        self.recursiveIterator = None
        # not yet used.
        #self.parentIterator = None

    def reset(self):
        '''
        reset prior to iteration
        '''
        self.returnSelf = self.includeSelf
        super(RecursiveIterator, self).reset()
    
    def __next__(self):

        while self.index < self.streamLength:
            # wrap this in a while loop instead of 
            # returning self.__next__() because
            # in a long score with a miserly filter
            # it is possible to exceed maximum recursion
            # depth
            if self.recursiveIterator is not None:
                try:
                    return self.recursiveIterator.next()
                except StopIteration:
                    #self.recursiveIterator.parentIterator = None
                    self.recursiveIterator = None
                    
            if self.returnSelf is True and self.matchesFilters(self.srcStream):
                self.activeInformation['stream'] = None
                self.activeInformation['index'] = -1
                self.returnSelf = False
                return self.srcStream
            elif self.returnSelf is True:
                self.returnSelf = False
                

            if self.index >= self.elementsLength:
                self.iterSection = '_endElements'
                self.sectionIndex = self.index - self.elementsLength
            else:
                self.sectionIndex = self.index
            
            self.index += 1 # increment early in case of an error in the next try.
        
            try:
                e = self.srcStreamElements[self.index - 1]
            except IndexError:
                # this may happen in the number of elements has changed
                continue
    
            # in a recursive filter, the stream does not need to match the filter,
            # only the internal elements.
            if e.isStream:
                self.recursiveIterator = RecursiveIterator(
                                            srcStream=e,
                                            restoreActiveSites=self.restoreActiveSites,
                                            filters=self.filters, # shared list...
                                            activeInformation=self.activeInformation, # shared dict
                                            includeSelf=False, # always for inner streams
                                            #parentIterator=self
                                            )
            if self.matchesFilters(e) is False:
                continue          
            
            if self.restoreActiveSites is True:
                e.activeSite = self.srcStream
    

            self.updateActiveInformation()
            return e

        ### the last element can still set a recursive iterator, so make sure we handle it.
        if self.recursiveIterator is not None:
            try:
                return self.recursiveIterator.next()
            except StopIteration:
                #self.recursiveIterator.parentIterator = None
                self.recursiveIterator = None
        
        
        self.cleanup()
        raise StopIteration
        
    next = __next__

    def matchingElements(self):
        # saved parent iterator later?
        # will this work in mid-iteration? Test, or do not expose till then.
        savedRecursiveIterator = self.recursiveIterator
        fe = super(RecursiveIterator, self).matchingElements()
        self.recursiveIterator = savedRecursiveIterator
        return fe

    def iteratorStack(self):
        '''
        Returns a stack of Streams at this point in the iteration.  Last is most recent.
        
        >>> b = corpus.parse('bwv66.6')
        >>> bRecurse = b.recurse()
        >>> i = 0
        >>> for x in bRecurse:
        ...     i += 1
        ...     if i > 12:
        ...         break
        >>> bRecurse.iteratorStack()
        [<music21.stream.iterator.RecursiveIterator for Score:0x10475cdd8 @:2>, 
         <music21.stream.iterator.RecursiveIterator for Part:Soprano @:3>, 
         <music21.stream.iterator.RecursiveIterator for Measure:m.1 @:2>]
        '''
        iterStack = [self]
        x = self
        while x.recursiveIterator is not None:
            x = x.recursiveIterator
            iterStack.append(x)
        return iterStack

    def streamStack(self):
        '''
        Returns a stack of Streams at this point.  Last is most recent.
        
        >>> b = corpus.parse('bwv66.6')
        >>> bRecurse = b.recurse()
        >>> i = 0
        >>> for x in bRecurse:
        ...     i += 1
        ...     if i > 12:
        ...         break
        >>> bRecurse.streamStack()
        [<music21.stream.Score 0x1049a0710>, 
         <music21.stream.Part Soprano>, 
         <music21.stream.Measure 1 offset=1.0>]
        '''
        return [i.srcStream for i in self.iteratorStack()]

class Test(unittest.TestCase):
    pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
