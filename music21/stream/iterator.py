# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/iterator.py
# Purpose:      classes for walking through streams...
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2016 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
this class contains iterators and filters for walking through streams

StreamIterators are explicitly allowed to access private methods on streams.
'''
import copy
from typing import TypeVar, List, Union, Callable, Optional, Dict
import unittest
import warnings

from music21 import common
from music21.common.classTools import tempAttribute, saveAttributes
from music21.common.enums import OffsetSpecial
from music21.exceptions21 import StreamException
from music21.stream import filters
from music21 import prebase
from music21 import base   # just for typing.

from music21.sites import SitesException


_SIter = TypeVar('_SIter')
FilterType = Union[Callable, filters.StreamFilter]

# -----------------------------------------------------------------------------


class StreamIteratorException(StreamException):
    pass


class StreamIteratorInefficientWarning(PendingDeprecationWarning):
    pass

# -----------------------------------------------------------------------------


class StreamIterator(prebase.ProtoM21Object):
    '''
    An Iterator object used to handle getting items from Streams.
    The :meth:`~music21.stream.Stream.__iter__` method
    returns this object, passing a reference to self.

    Note that this iterator automatically sets the active site of
    returned elements to the source Stream.

    There is one property to know about: .overrideDerivation which overrides the set
    derivation of the class when .stream() is called

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

    Constructor keyword only arguments:

    * `filterList` is a list of stream.filters.Filter objects to apply

    * if `restoreActiveSites` is True (default) then on iterating, the activeSite is set
      to the Stream being iterated over.

    * if `ignoreSorting` is True (default is False) then the Stream is not sorted before
      iterating.  If the Stream is already sorted, then this value does not matter, and
      no time will be saved by setting to False.

    * For `activeInformation` see above.

    Changed in v.5.2 -- all arguments except srcStream are keyword only.

    OMIT_FROM_DOCS

    Informative exception for user error:

    >>> s = stream.Stream()
    >>> sIter = stream.iterator.StreamIterator(s, filterList=[note.Note])
    Traceback (most recent call last):
    TypeError: filterList expects Filters or callables,
    not types themselves; got <class 'music21.note.Note'>
    '''
    def __init__(self,
                 srcStream: 'music21.stream.Stream',
                 *,
                 filterList: Union[List[FilterType], FilterType, None] = None,
                 restoreActiveSites: bool = True,
                 activeInformation: Optional[Dict] = None,
                 ignoreSorting: bool = False):
        if not ignoreSorting and srcStream.isSorted is False and srcStream.autoSort:
            srcStream.sort()
        self.srcStream: 'music21.stream.Stream' = srcStream
        self.index: int = 0

        # use .elements instead of ._elements/etc. so that it is sorted...
        self.srcStreamElements = srcStream.elements
        self.streamLength = len(self.srcStreamElements)

        # this information can help in speed later
        self.elementsLength = len(self.srcStream._elements)
        self.sectionIndex = -1  # where we are within a given section (_elements or _endElements)
        self.iterSection = '_elements'

        self.cleanupOnStop = False
        self.restoreActiveSites: bool = restoreActiveSites

        self.overrideDerivation = None

        if filterList is None:
            filterList = []
        elif not common.isIterable(filterList):
            filterList = [filterList]
        elif isinstance(filterList, (set, tuple)):
            filterList = list(filterList)  # mutable....
        for x in filterList:
            if isinstance(x, type):
                raise TypeError(
                    f'filterList expects Filters or callables, not types themselves; got {x}')
        # self.filters is a list of expressions that
        # return True or False for an element for
        # whether it should be yielded.
        self.filters: List[FilterType] = filterList
        self._len = None
        self._matchingElements = None

        # keep track of where we are in the parse.
        # esp important for recursive streams...
        if activeInformation is not None:
            self.activeInformation = activeInformation
        else:
            self.activeInformation = {}  # in Py3.8 make a TypedDict
            self.updateActiveInformation()

    def _reprInternal(self):
        streamClass = self.srcStream.__class__.__name__
        srcStreamId = self.srcStream.id
        try:
            srcStreamId = hex(srcStreamId)
        except TypeError:
            pass

        if streamClass == 'Measure' and self.srcStream.number != 0:
            srcStreamId = 'm.' + str(self.srcStream.number)

        return f'for {streamClass}:{srcStreamId} @:{self.index}'

    def __call__(self) -> _SIter:
        '''
        Temporary workaround to support both prior usage of `.iter`
        and new recommended usage of `.iter()`.
        During the period where `.iter` is still supported, even calling `.iter()`
        (recommended) will retrieve the property `.iter` and necessitate
        this workaround.

        Returns `self` without any changes.

        TODO: manage and emit DeprecationWarnings in v.8
        TODO: remove in v.9
        '''
        return self

    def __iter__(self):
        self.reset()
        return self

    def __next__(self) -> base.Music21Object:
        while self.index < self.streamLength:
            if self.index >= self.elementsLength:
                self.iterSection = '_endElements'
                self.sectionIndex = self.index - self.elementsLength
            else:
                self.sectionIndex = self.index

            try:
                e = self.srcStreamElements[self.index]
            except IndexError:
                # this may happen if the number of elements has changed
                self.index += 1
                continue

            self.index += 1
            if self.matchesFilters(e) is False:
                continue

            if self.restoreActiveSites is True:
                self.srcStream.coreSelfActiveSite(e)

            self.updateActiveInformation()
            return e

        self.cleanup()
        raise StopIteration

    def __getattr__(self, attr):
        '''
        In case an attribute is defined on Stream but not on a StreamIterator,
        create a Stream and then return that attribute.  This is NOT performance
        optimized -- calling this repeatedly will mean creating a lot of different
        streams.  However, it will prevent most code that worked on v.2. from breaking
        on v.3 and onwards.

        >>> s = stream.Measure()
        >>> s.insert(0, note.Rest())
        >>> s.repeatAppend(note.Note('C'), 2)

        >>> s.definesExplicitSystemBreaks
        False

        >>> s.notes
        <music21.stream.iterator.StreamIterator for Measure:0x101c1a208 @:0>

        >>> import warnings  #_DOCS_HIDE
        >>> SIIW = stream.iterator.StreamIteratorInefficientWarning #_DOCS_HIDE
        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore', SIIW) #_DOCS_HIDE
        ...      explicit = s.notes.definesExplicitSystemBreaks #_DOCS_HIDE
        >>> #_DOCS_SHOW explicit = s.notes.definesExplicitSystemBreaks
        >>> explicit
        False

        Works with methods as well:

        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore', SIIW) #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>

        But remember that a new Stream is being created each time that an attribute
        only defined on a Stream is called, so for instance, so you can pop() forever,
        always getting the same element.

        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore', SIIW) #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>
        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore', SIIW) #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>
        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore', SIIW) #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>

        If run with -w, this call will send a StreamIteratorInefficientWarning to stderr
        reminding developers that this is not an efficient call, and .stream() should be
        called (and probably cached) explicitly.

        Failures are explicitly given as coming from the StreamIterator object.

        >>> s.asdf
        Traceback (most recent call last):
        AttributeError: 'Measure' object has no attribute 'asdf'
        >>> s.notes.asdf
        Traceback (most recent call last):
        AttributeError: 'StreamIterator' object has no attribute 'asdf'

        OMIT_FROM_DOCS

        srcStream is accessible, but not with "__getattr__", which joblib uses

        >>> s.notes.srcStream is s
        True
        >>> s.notes.__getattr__('srcStream') is None
        True
        '''
        # Prevent infinite loop in feature extractor task serialization
        # TODO: investigate if this can be removed once iter becomes iter()
        if attr == 'srcStream':
            return None

        if not hasattr(self.srcStream, attr):
            # original stream did not have the attribute, so new won't; but raise on iterator.
            raise AttributeError(f'{self.__class__.__name__!r} object has no attribute {attr!r}')

        warnings.warn(
            attr + ' is not defined on StreamIterators. Call .stream() first for efficiency',
            StreamIteratorInefficientWarning,
            stacklevel=2)

        sOut = self.stream()
        return getattr(sOut, attr)

    def __getitem__(self, k):
        '''
        if you are in the iterator, you should still be able to request other items...
        uses self.srcStream.__getitem__

        >>> s = stream.Stream()
        >>> s.insert(0, note.Note('F#'))
        >>> s.repeatAppend(note.Note('C'), 2)
        >>> sI = s.iter()
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

        Slices work:

        >>> nSlice = sI[1:]
        >>> for n in nSlice:
        ...     print(n)
        <music21.note.Note C>
        <music21.note.Note C>

        Filters, such as "notes" apply.

        >>> s.insert(0, clef.TrebleClef())
        >>> s[0]
        <music21.clef.TrebleClef>
        >>> s.iter().notes[0]
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
        try:
            e = fe[k]
        except TypeError:
            e = None
            for el in fe:
                if el.id.lower() == k.lower():
                    e = el
                    break
        # TODO: Slices and everything else in Stream __getitem__ ; in fact, merge...
        return e

    def __len__(self) -> int:
        '''
        returns the length of the elements that
        match the filter set.

        >>> s = converter.parse('tinynotation: 3/4 c4 d e f g a', makeNotation=False)
        >>> len(s)
        7
        >>> len(s.iter())
        7
        >>> len(s.iter().notes)
        6
        >>> [n.name for n in s.iter().notes]
        ['C', 'D', 'E', 'F', 'G', 'A']
        '''
        if self._len is not None:
            return self._len
        self._len = len(self.matchingElements(restoreActiveSites=False))
        self.reset()
        return self._len

    def __bool__(self) -> bool:
        '''
        return True if anything matches the filter
        otherwise, return False

        >>> s = converter.parse('tinyNotation: 2/4 c4 r4')
        >>> bool(s)
        True
        >>> iterator = s.recurse()
        >>> bool(iterator)
        True
        >>> bool(iterator.notesAndRests)
        True
        >>> bool(iterator.notes)
        True

        test cache

        >>> len(iterator.notes)
        1
        >>> bool(iterator.notes)
        True
        >>> bool(iterator.notes)
        True

        >>> iterator = s.recurse()
        >>> bool(iterator)
        True
        >>> bool(iterator)
        True
        >>> bool(iterator)
        True

        >>> bool(iterator.getElementsByClass('Chord'))
        False

        test false cache:

        >>> len(iterator.getElementsByClass('Chord'))
        0
        >>> bool(iterator.getElementsByClass('Chord'))
        False

        '''
        if self._len is not None:
            return bool(self._len)

        # do not change active site of first element in bool
        with tempAttribute(self, 'restoreActiveSites', False):
            for unused in self:
                return True

        return False

    def clone(self: _SIter) -> _SIter:
        '''
        Returns a new copy of the same iterator.
        (a shallow copy of some things except activeInformation)
        '''
        out: _SIter = type(self)(
            self.srcStream,
            filterList=copy.copy(self.filters),
            restoreActiveSites=self.restoreActiveSites,
            activeInformation=copy.copy(self.activeInformation),
        )
        return out

    def first(self) -> Optional[base.Music21Object]:
        '''
        Efficiently return the first matching element, or None if no
        elements match.

        Does not require creating the whole list of matching elements.

        >>> s = converter.parse('tinyNotation: 3/4 D4 E2 F4 r2 G2 r4')
        >>> s.recurse().notes.first()
        <music21.note.Note D>
        >>> s.recurse().getElementsByClass('Rest').first()
        <music21.note.Rest half>

        If no elements match, returns None:

        >>> print(s.recurse().getElementsByClass('Chord').first())
        None

        New in v7.

        OMIT_FROM_DOCS

        Ensure that next continues after the first note running:

        >>> notes = s.recurse().notes
        >>> notes.first()
        <music21.note.Note D>
        >>> next(notes)
        <music21.note.Note E>

        Now reset on new iteration:

        >>> for n in notes:
        ...     print(n)
        <music21.note.Note D>
        <music21.note.Note E>
        ...

        An Empty stream:

        >>> s = stream.Stream()
        >>> s.iter().notes.first() is None
        True
        '''
        iter(self)
        try:
            return next(self)
        except StopIteration:
            return None

    def last(self) -> Optional[base.Music21Object]:
        '''
        Returns the last matching element, or None if no elements match.

        Currently is not efficient (does not iterate backwards, for instance),
        but easier than checking for an IndexError.  Might be refactored later
        to iterate the stream backwards instead if it gets a lot of use.

        >>> s = converter.parse('tinyNotation: 3/4 D4 E2 F4 r2 G2 r4')
        >>> s.recurse().notes.last()
        <music21.note.Note G>
        >>> s.recurse().getElementsByClass('Rest').last()
        <music21.note.Rest quarter>

        New in v7.

        OMIT_FROM_DOCS

        Check on empty Stream:

        >>> s2 = stream.Stream()
        >>> s2.iter().notes.last() is None
        True

        Next has a different feature from first(), will start again from beginning.
        This behavior may change.

        >>> notes = s.recurse().notes
        >>> notes.last()
        <music21.note.Note G>
        >>> next(notes)
        <music21.note.Note D>
        '''
        fe = self.matchingElements()
        if not fe:
            return None
        return fe[-1]

    # ---------------------------------------------------------------
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

    # ---------------------------------------------------------------
    # getting items

    def matchingElements(self, *, restoreActiveSites: bool = True):
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
        >>> sI = s.iter()
        >>> sI
        <music21.stream.iterator.StreamIterator for Part:tn3/4 @:0>

        >>> sI.matchingElements()
        [<music21.meter.TimeSignature 3/4>, <music21.note.Note C>, <music21.note.Note D>,
         <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>,
         <music21.note.Note A>]

        >>> sI_notes = sI.notes
        >>> sI_notes
        <music21.stream.iterator.StreamIterator for Part:tn3/4 @:0>

        Adding a filter to the Stream iterator returns a new Stream iterator; it
        does not change the original.

        >>> sI_notes is sI
        False

        >>> sI.filters
        []

        >>> sI_notes.filters
        [<music21.stream.filters.ClassFilter NotRest>]

        >>> sI_notes.matchingElements()
        [<music21.note.Note C>, <music21.note.Note D>,
         <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>,
         <music21.note.Note A>]

        If restoreActiveSites is False then the elements will not have
        their activeSites changed (callers should use it when they do not plan to actually
        expose the elements to users, such as in `__len__`).

        Added in v7. -- restoreActiveSites
        '''
        if self._matchingElements is not None:
            return self._matchingElements

        with saveAttributes(self, 'restoreActiveSites', 'index'):
            self.restoreActiveSites = restoreActiveSites
            me = [x for x in self]  # pylint: disable=unnecessary-comprehension
            self.reset()

        if restoreActiveSites == self.restoreActiveSites:
            # cache, if we are using the iterator default.
            self._matchingElements = me

        return me

    def matchesFilters(self, e):
        '''
        returns False if any filter returns False, True otherwise.
        '''
        for f in self.filters:
            f: Union[Callable, filters.StreamFilter]
            try:
                try:
                    if f(e, self) is False:
                        return False
                except TypeError:  # one element filters are acceptable.
                    f: Callable
                    if f(e) is False:
                        return False
            except StopIteration:  # pylint: disable=try-except-raise
                raise  # clearer this way to see that this can happen...
        return True

    def _newBaseStream(self):
        '''
        Returns a new stream.Stream.  The same thing as calling:

        >>> s = stream.Stream()

        So why does this exist?  Since we can't import "music21.stream" here,
        we will look in `srcStream.__class__.mro()` for the Stream
        object to import.

        This is used in places where returnStreamSubclass is False, so we
        cannot just call `type(StreamIterator.srcStream)()`

        >>> p = stream.Part()
        >>> pi = p.iter()
        >>> s = pi._newBaseStream()
        >>> s
        <music21.stream.Stream 0x1047eb2e8>

        >>> pi.srcStream = note.Note()
        >>> pi._newBaseStream()
        Traceback (most recent call last):
        music21.stream.iterator.StreamIteratorException: ...
        '''
        StreamBase = None
        for x in self.srcStream.__class__.mro():
            if x.__name__ == 'Stream':
                StreamBase = x
                break

        try:
            return StreamBase()
        except TypeError:  # 'NoneType' object is not callable.
            raise StreamIteratorException(
                f"You've given a 'stream' that is not a stream! {self.srcStream}")

    def stream(self, returnStreamSubClass=True):
        '''
        return a new stream from this iterator.

        Does nothing except copy if there are no filters, but a drop in
        replacement for the old .getElementsByClass() etc. if it does.

        In other words:

        `s.getElementsByClass()` == `s.iter().getElementsByClass().stream()`

        >>> s = stream.Part()
        >>> s.insert(0, note.Note('C'))
        >>> s.append(note.Rest())
        >>> s.append(note.Note('D'))
        >>> b = bar.Barline()
        >>> s.storeAtEnd(b)

        >>> s2 = s.iter().getElementsByClass('Note').stream()
        >>> s2.show('t')
        {0.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        >>> s2.derivation.method
        'getElementsByClass'
        >>> s2
        <music21.stream.Part ...>

        >>> s3 = s.iter().stream()
        >>> s3.show('t')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Rest quarter>
        {2.0} <music21.note.Note D>
        {3.0} <music21.bar.Barline type=regular>

        >>> s3.elementOffset(b, returnSpecial=True)
        <OffsetSpecial.AT_END>

        >>> s4 = s.iter().getElementsByClass('Barline').stream()
        >>> s4.show('t')
        {0.0} <music21.bar.Barline type=regular>


        Note that this routine can create Streams that have elements that the original
        stream did not, in the case of recursion:

        >>> bach = corpus.parse('bwv66.6')
        >>> bn = bach.flatten()[30]
        >>> bn
        <music21.note.Note E>

        >>> bn in bach
        False
        >>> bfn = bach.recurse().notes.stream()
        >>> bn in bfn
        True
        >>> bn.getOffsetBySite(bfn)
        2.0
        >>> bn.getOffsetInHierarchy(bach)
        2.0

        OMIT_FROM_DOCS

        >>> s4._endElements[0] is b
        True
        '''
        ss = self.srcStream

        # if this stream was sorted, the resultant stream is sorted
        clearIsSorted = False

        if returnStreamSubClass is True:
            try:
                found = ss.__class__()
            except TypeError:
                found = self._newBaseStream()
        else:
            found = self._newBaseStream()

        found.mergeAttributes(ss)
        found.derivation.origin = ss
        if self.overrideDerivation is not None:
            found.derivation.method = self.overrideDerivation
        else:
            derivationMethods = []
            for f in self.filters:
                if hasattr(f, 'derivationStr'):
                    dStr = f.derivationStr
                else:
                    dStr = f.__name__  # function; lambda returns <lambda>
                derivationMethods.append(dStr)
            found.derivation.method = '.'.join(derivationMethods)

        fe = self.matchingElements()
        for e in fe:
            try:
                o = ss.elementOffset(e, returnSpecial=True)
            except SitesException:
                # this can happen in the case of, s.recurse().notes.stream() -- need to do new
                # stream...
                o = e.getOffsetInHierarchy(ss)
                clearIsSorted = True  # now the stream is probably not sorted...

            if not isinstance(o, str):
                found.coreInsert(o, e, ignoreSort=True)
            else:
                if o == OffsetSpecial.AT_END:
                    found.coreStoreAtEnd(e)
                else:
                    # TODO: something different...
                    found.coreStoreAtEnd(e)

        if fe:
            found.coreElementsChanged(clearIsSorted=clearIsSorted)

        return found

    @property
    def activeElementList(self):
        '''
        returns the element list ('_elements' or '_endElements')
        for the current activeInformation
        '''
        return getattr(self.activeInformation['stream'], self.activeInformation['iterSection'])

    # ------------------------------------------------------------

    def addFilter(self: _SIter, newFilter, *, returnClone=True) -> _SIter:
        '''
        Return a new StreamIterator with an additional filter.
        Also resets caches -- so do not add filters any other way.

        If returnClone is False then adds without creating a new StreamIterator

        Changed in v.6 -- Encourage creating new StreamIterators: change
        default to return a new StreamIterator.
        '''
        if returnClone:
            out = self.clone()
        else:
            out = self

        out.resetCaches()
        for f in out.filters:
            if newFilter == f:
                return out
        out.filters.append(newFilter)

        return out

    def removeFilter(self: _SIter, oldFilter, *, returnClone=True) -> _SIter:
        '''
        Return a new StreamIterator where oldFilter is removed.
        '''
        if returnClone:
            out = self.clone()
        else:
            out = self

        out.resetCaches()
        if oldFilter in out.filters:
            out.filters.pop(out.filters.index(oldFilter))

        return out

    def getElementById(self, elementId):
        '''
        Returns a single element (or None) that matches elementId.

        If chaining filters, this should be the last one, as it returns an element

        >>> s = stream.Stream(id='s1')
        >>> s.append(note.Note('C'))
        >>> r = note.Rest()
        >>> r.id = 'restId'
        >>> s.append(r)
        >>> r2 = s.recurse().getElementById('restId')
        >>> r2 is r
        True
        >>> r2.id
        'restId'
        '''
        out = self.addFilter(filters.IdFilter(elementId))
        for e in out:
            return e
        return None

    def getElementsByClass(self, classFilterList, *, returnClone=True):
        '''
        Add a filter to the Iterator to remove all elements
        except those that match one
        or more classes in the `classFilterList`. A single class
        can also used for the `classFilterList` parameter instead of a List.

        >>> s = stream.Stream(id='s1')
        >>> s.append(note.Note('C'))
        >>> r = note.Rest()
        >>> s.append(r)
        >>> s.append(note.Note('D'))
        >>> for el in s.iter().getElementsByClass('Rest'):
        ...     print(el)
        <music21.note.Rest quarter>


        ActiveSite is restored...

        >>> s2 = stream.Stream(id='s2')
        >>> s2.insert(0, r)
        >>> r.activeSite.id
        's2'

        >>> for el in s.iter().getElementsByClass('Rest'):
        ...     print(el.activeSite.id)
        s1


        Classes work in addition to strings...

        >>> for el in s.iter().getElementsByClass(note.Rest):
        ...     print(el)
        <music21.note.Rest quarter>

        '''
        return self.addFilter(filters.ClassFilter(classFilterList), returnClone=returnClone)

    def getElementsByQuerySelector(self, querySelector: str, *, returnClone=True):
        '''
        First implementation of a query selector, similar to CSS QuerySelectors used in
        HTML DOM:

        * A leading `#` indicates the id of an element, so '#hello' will find elements
          with `el.id=='hello'` (should only be one)
        * A leading `.` indicates the group of an element, so '.high' will find elements
          with `'high' in el.groups`
        * Any other string is considered to be the type/class of the element.  So `Note`
          will find all Note elements.  Can be fully qualified like `note.Note`

        Eventually, more complex query selectors will be implemented.  This is just a start.

        Setting up an example:

        >>> s = converter.parse('tinyNotation: 4/4 GG4 AA4 BB4 r4 C4 D4 E4 F4 r1')
        >>> s[note.Note].last().id = 'last'
        >>> for n in s[note.Note]:
        ...     if n.octave == 3:
        ...         n.groups.append('tenor')

        >>> list(s.recurse().getElementsByQuerySelector('.tenor'))
        [<music21.note.Note C>,
         <music21.note.Note D>,
         <music21.note.Note E>,
         <music21.note.Note F>]

        >>> list(s.recurse().getElementsByQuerySelector('Rest'))
        [<music21.note.Rest quarter>,
         <music21.note.Rest whole>]

        Note that unlike with stream slices, the querySelector does not do anything special
        for id searches.  `.first()` will need to be called to find the element (if any)

        >>> s.recurse().getElementsByQuerySelector('#last').first()
        <music21.note.Note F>

        New in v.7
        '''
        if querySelector.startswith('#'):
            return self.addFilter(filters.IdFilter(querySelector[1:]), returnClone=returnClone)
        if querySelector.startswith('.'):
            return self.addFilter(filters.GroupFilter(querySelector[1:]), returnClone=returnClone)
        return self.addFilter(filters.ClassFilter(querySelector), returnClone=returnClone)


    def getElementsNotOfClass(self, classFilterList, *, returnClone=True):
        '''
        Adds a filter, removing all Elements that do not
        match the one or more classes in the `classFilterList`.

        In lieu of a list, a single class can be used as the `classFilterList` parameter.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Rest(), range(10))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.iter().getElementsNotOfClass(note.Note)
        >>> len(found)
        10
        >>> found = a.iter().getElementsNotOfClass('Rest')
        >>> len(found)
        4
        >>> found = a.iter().getElementsNotOfClass(['Note', 'Rest'])
        >>> len(found)
        0

        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), range(15))
        >>> a.insert(b)

        >>> found = a.recurse().getElementsNotOfClass([note.Rest, 'Stream'])
        >>> len(found)
        4
        >>> found = a.recurse().getElementsNotOfClass([note.Note, 'Stream'])
        >>> len(found)
        25
        '''
        return self.addFilter(filters.ClassNotFilter(classFilterList), returnClone=returnClone)

    def getElementsByGroup(self, groupFilterList, *, returnClone=True):
        '''
        >>> n1 = note.Note('C')
        >>> n1.groups.append('trombone')
        >>> n2 = note.Note('D')
        >>> n2.groups.append('trombone')
        >>> n2.groups.append('tuba')
        >>> n3 = note.Note('E')
        >>> n3.groups.append('tuba')
        >>> s1 = stream.Stream()
        >>> s1.append(n1)
        >>> s1.append(n2)
        >>> s1.append(n3)

        >>> tboneSubStream = s1.iter().getElementsByGroup('trombone')
        >>> for thisNote in tboneSubStream:
        ...     print(thisNote.name)
        C
        D
        >>> tubaSubStream = s1.iter().getElementsByGroup('tuba')
        >>> for thisNote in tubaSubStream:
        ...     print(thisNote.name)
        D
        E
        '''
        return self.addFilter(filters.GroupFilter(groupFilterList), returnClone=returnClone)

    def getElementsByOffset(
        self,
        offsetStart,
        offsetEnd=None,
        *,
        includeEndBoundary=True,
        mustFinishInSpan=False,
        mustBeginInSpan=True,
        includeElementsThatEndAtStart=True,
        stopAfterEnd=True,
        returnClone=True,
    ) -> 'StreamIterator':
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
        >>> n0 = note.Note('C')
        >>> n0.duration.type = 'half'
        >>> n0.offset = 0
        >>> st1.insert(n0)
        >>> n2 = note.Note('D')
        >>> n2.duration.type = 'half'
        >>> n2.offset = 2
        >>> st1.insert(n2)
        >>> out1 = list(st1.iter().getElementsByOffset(2))
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = list(st1.iter().getElementsByOffset(1, 3))
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = list(st1.iter().getElementsByOffset(1, 3, mustFinishInSpan=True))
        >>> len(out3)
        0
        >>> out4 = list(st1.iter().getElementsByOffset(1, 2))
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = list(st1.iter().getElementsByOffset(1, 2, includeEndBoundary=False))
        >>> len(out5)
        0
        >>> out6 = list(st1.iter().getElementsByOffset(1, 2, includeEndBoundary=False,
        ...                                          mustBeginInSpan=False))
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = list(st1.iter().getElementsByOffset(1, 3, mustBeginInSpan=False))
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']

        Note, that elements that end at the start offset are included if mustBeginInSpan is False

        >>> out8 = list(st1.iter().getElementsByOffset(2, 4, mustBeginInSpan=False))
        >>> len(out8)
        2
        >>> [el.step for el in out8]
        ['C', 'D']

        To change this behavior set includeElementsThatEndAtStart=False

        >>> out9 = list(st1.iter().getElementsByOffset(2, 4, mustBeginInSpan=False,
        ...                                          includeElementsThatEndAtStart=False))
        >>> len(out9)
        1
        >>> [el.step for el in out9]
        ['D']

        >>> a = stream.Stream(id='a')
        >>> n = note.Note('G')
        >>> n.quarterLength = 0.5
        >>> a.repeatInsert(n, list(range(8)))
        >>> b = stream.Stream(id='b')
        >>> b.repeatInsert(a, [0, 3, 6])
        >>> c = list(b.iter().getElementsByOffset(2, 6.9))
        >>> len(c)
        2
        >>> c = list(b.flatten().iter().getElementsByOffset(2, 6.9))
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
        >>> len(list(s.iter().getElementsByOffset(0.0, mustBeginInSpan=True)))
        3
        >>> len(list(s.iter().getElementsByOffset(0.0, mustBeginInSpan=False)))
        3

        On a :class:`~music21.stream.iterator.RecursiveIterator`,
        `.getElementsByOffset(0.0)`, will get everything
        at the start of the piece, which is useful:

        >>> bwv66 = corpus.parse('bwv66.6')
        >>> list(bwv66.recurse().getElementsByOffset(0.0))
        [<music21.metadata.Metadata object at 0x10a32f490>,
         <music21.stream.Part Soprano>,
         <music21.instrument.Instrument 'P1: Soprano: Instrument 1'>,
         <music21.stream.Measure 0 offset=0.0>,
         <music21.clef.TrebleClef>,
         <music21.key.Key of f# minor>,
         <music21.meter.TimeSignature 4/4>,
         <music21.note.Note C#>,
         <music21.stream.Part Alto>,
         ...
         <music21.note.Note E>,
         <music21.stream.Part Tenor>,
         ...]

        However, any other offset passed to `getElementsByOffset` on a
        `RecursiveIterator` without additional arguments, is unlikely to be useful,
        because the iterator ends as soon as it encounters an element
        with an offset beyond the `offsetEnd` point.  For instance,
        calling `.getElementsByOffset(1.0).notes` on a :class:`~music21.stream.Part`,
        in bwv66.6 only gets the note that appears at offset 1.0 of a measure that begins
        or includes offset 1.0.
        (Fortunately, this piece begins with a one-beat pickup, so there is such a note):

        >>> soprano = bwv66.parts['Soprano']
        >>> for el in soprano.recurse().getElementsByOffset(1.0):
        ...     print(el, el.offset, el.getOffsetInHierarchy(bwv66), el.activeSite)
        <music21.stream.Measure 1 offset=1.0> 1.0 1.0 <music21.stream.Part Soprano>
        <music21.note.Note B> 1.0 2.0 <music21.stream.Measure 1 offset=1.0>


        RecursiveIterators will probably want to use
        :meth:`~music21.stream.iterator.RecursiveIterator.getElementsByOffsetInHierarchy`
        instead.  Or to get all elements with a particular local offset, such as everything
        on the third quarter note of a measure, use the `stopAfterEnd=False` keyword,
        which lets the iteration continue to search for elements even after encountering
        some within Streams whose offsets are greater than the end element.

        >>> len(soprano.recurse().getElementsByOffset(2.0, stopAfterEnd=False))
        9

        Changed in v5.5 -- all arguments changing behavior are keyword only.
        Added in v6.5 -- `stopAfterEnd` keyword.

        OMIT_FROM_DOCS

        Same test as above, but with floats

        >>> out1 = list(st1.iter().getElementsByOffset(2.0))
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = list(st1.iter().getElementsByOffset(1.0, 3.0))
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = list(st1.iter().getElementsByOffset(1.0, 3.0, mustFinishInSpan=True))
        >>> len(out3)
        0
        >>> out3b = list(st1.iter().getElementsByOffset(0.0, 3.001, mustFinishInSpan=True))
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'
        >>> out3b = list(st1.iter().getElementsByOffset(1.0, 3.001, mustFinishInSpan=True,
        ...                                           mustBeginInSpan=False))
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'

        >>> out4 = list(st1.iter().getElementsByOffset(1.0, 2.0))
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = list(st1.iter().getElementsByOffset(1.0, 2.0, includeEndBoundary=False))
        >>> len(out5)
        0
        >>> out6 = list(st1.iter().getElementsByOffset(1.0, 2.0, includeEndBoundary=False,
        ...                                          mustBeginInSpan=False))
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = list(st1.iter().getElementsByOffset(1.0, 3.0, mustBeginInSpan=False))
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']
        '''
        return self.addFilter(
            filters.OffsetFilter(
                offsetStart,
                offsetEnd,
                includeEndBoundary=includeEndBoundary,
                mustFinishInSpan=mustFinishInSpan,
                mustBeginInSpan=mustBeginInSpan,
                includeElementsThatEndAtStart=includeElementsThatEndAtStart,
                stopAfterEnd=stopAfterEnd,
            ),
            returnClone=returnClone
        )

    # ------------------------------------------------------------
    # properties -- historical...

    @property
    def notes(self):
        '''
        Returns all NotRest objects

        (will sometime become simply Note and Chord objects...)

        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> s.append(note.Rest())
        >>> s.append(note.Note('D'))
        >>> for el in s.iter().notes:
        ...     print(el)
        <music21.note.Note C>
        <music21.note.Note D>
        '''
        return self.addFilter(filters.ClassFilter('NotRest'))

    @property
    def notesAndRests(self):
        '''
        Returns all GeneralNote objects

        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.append(note.Note('C'))
        >>> s.append(note.Rest())
        >>> s.append(note.Note('D'))
        >>> for el in s.iter().notesAndRests:
        ...     print(el)
        <music21.note.Note C>
        <music21.note.Rest quarter>
        <music21.note.Note D>

        chained filters... (this makes no sense since notes is a subset of notesAndRests)

        >>> for el in s.iter().notesAndRests.notes:
        ...     print(el)
        <music21.note.Note C>
        <music21.note.Note D>
        '''
        return self.addFilter(filters.ClassFilter('GeneralNote'))

    @property
    def parts(self):
        '''
        Adds a ClassFilter for Part objects
        '''
        return self.addFilter(filters.ClassFilter('Part'))

    @property
    def spanners(self):
        '''
        Adds a ClassFilter for Spanner objects
        '''
        return self.addFilter(filters.ClassFilter('Spanner'))

    @property
    def variants(self):
        '''
        Deprecated in version 7

        Adds a ClassFilter for Variant
        '''
        return self.addFilter(filters.ClassFilter('Variant'))

    @property
    def voices(self):
        '''
        Adds a ClassFilter for Voice objects
        '''
        return self.addFilter(filters.ClassFilter('Voice'))


# -----------------------------------------------------------------------------
class OffsetIterator(StreamIterator):
    '''
    An iterator that with each iteration returns a list of elements
    that are at the same offset (or all at end)

    >>> s = stream.Stream()
    >>> s.insert(0, note.Note('C'))
    >>> s.insert(0, note.Note('D'))
    >>> s.insert(1, note.Note('E'))
    >>> s.insert(2, note.Note('F'))
    >>> s.insert(2, note.Note('G'))
    >>> s.storeAtEnd(bar.Repeat('end'))
    >>> s.storeAtEnd(clef.TrebleClef())

    >>> oIter = stream.iterator.OffsetIterator(s)
    >>> for groupedElements in oIter:
    ...     print(groupedElements)
    [<music21.note.Note C>, <music21.note.Note D>]
    [<music21.note.Note E>]
    [<music21.note.Note F>, <music21.note.Note G>]
    [<music21.bar.Repeat direction=end>, <music21.clef.TrebleClef>]

    Does it work again?

    >>> for groupedElements2 in oIter:
    ...     print(groupedElements2)
    [<music21.note.Note C>, <music21.note.Note D>]
    [<music21.note.Note E>]
    [<music21.note.Note F>, <music21.note.Note G>]
    [<music21.bar.Repeat direction=end>, <music21.clef.TrebleClef>]


    >>> for groupedElements in oIter.notes:
    ...     print(groupedElements)
    [<music21.note.Note C>, <music21.note.Note D>]
    [<music21.note.Note E>]
    [<music21.note.Note F>, <music21.note.Note G>]

    >>> for groupedElements in stream.iterator.OffsetIterator(s).getElementsByClass('Clef'):
    ...     print(groupedElements)
    [<music21.clef.TrebleClef>]
    '''

    def __init__(self,
                 srcStream,
                 *,
                 filterList=None,
                 restoreActiveSites=True,
                 activeInformation=None,
                 ignoreSorting=False
                 ):
        super().__init__(srcStream,
                         filterList=filterList,
                         restoreActiveSites=restoreActiveSites,
                         activeInformation=activeInformation,
                         ignoreSorting=ignoreSorting,
                         )
        self.raiseStopIterationNext = False
        self.nextToYield = []
        self.nextOffsetToYield = None

    def __next__(self) -> List[base.Music21Object]:
        if self.raiseStopIterationNext:
            raise StopIteration

        retElementList = None
        # make sure that cleanup is not called during the loop...
        try:
            if self.nextToYield:
                retElementList = self.nextToYield
                retElOffset = self.nextOffsetToYield
            else:
                retEl = super().__next__()
                retElOffset = self.srcStream.elementOffset(retEl)
                retElementList = [retEl]

            while self.index <= self.streamLength:
                nextEl = super().__next__()
                nextElOffset = self.srcStream.elementOffset(nextEl)
                if nextElOffset == retElOffset:
                    retElementList.append(nextEl)
                else:
                    self.nextToYield = [nextEl]
                    self.nextOffsetToYield = nextElOffset
                    return retElementList

        except StopIteration:
            if retElementList:
                self.raiseStopIterationNext = True
                return retElementList
            else:
                raise StopIteration

    def reset(self):
        '''
        runs before iteration
        '''
        super().reset()
        self.nextToYield = []
        self.nextOffsetToYield = None
        self.raiseStopIterationNext = False


# -----------------------------------------------------------------------------
class RecursiveIterator(StreamIterator):
    '''
    One of the most powerful iterators in music21.  Generally not called
    directly, but created by being invoked on a stream with `Stream.recurse()`

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

    >>> for x in b.recurse(streamsOnly=True, includeSelf=True):
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

    >>> hasExpressions = lambda el, i: True if (hasattr(el, 'expressions')
    ...       and el.expressions) else False
    >>> expressive = b.recurse().addFilter(hasExpressions)
    >>> expressive
    <music21.stream.iterator.RecursiveIterator for Score:0x10487f550 @:0>

    >>> for el in expressive:
    ...     print(el, el.expressions)
    <music21.note.Note C#> [<music21.expressions.Fermata>]
    <music21.note.Note A> [<music21.expressions.Fermata>]
    <music21.note.Note F#> [<music21.expressions.Fermata>]
    <music21.note.Note C#> [<music21.expressions.Fermata>]
    <music21.note.Note G#> [<music21.expressions.Fermata>]
    <music21.note.Note F#> [<music21.expressions.Fermata>]

    >>> len(expressive)
    6
    >>> expressive[-1].measureNumber
    9
    >>> bool(expressive)
    True
    '''

    def __init__(self,
                 srcStream,
                 *,
                 filterList=None,
                 restoreActiveSites=True,
                 activeInformation=None,
                 streamsOnly=False,
                 includeSelf=False,
                 ignoreSorting=False
                 ):  # , parentIterator=None):
        super().__init__(srcStream,
                         filterList=filterList,
                         restoreActiveSites=restoreActiveSites,
                         activeInformation=activeInformation,
                         ignoreSorting=ignoreSorting,
                         )
        if 'lastYielded' not in self.activeInformation:
            self.activeInformation['lastYielded'] = None

        self.returnSelf = includeSelf
        self.includeSelf = includeSelf
        self.ignoreSorting = ignoreSorting

        # within the list of parent/child recursive iterators, where does this start?
        self.iteratorStartOffsetInHierarchy = 0.0

        if streamsOnly is True:
            self.filters.append(filters.ClassFilter('Stream'))
        self.childRecursiveIterator = None
        # not yet used.
        # self.parentIterator = None

    def __next__(self) -> base.Music21Object:
        '''
        Get the next element of the stream under iteration.

        The same __iter__ as the superclass is used.
        '''
        while self.index < self.streamLength:
            # wrap this in a while loop instead of
            # returning self.__next__() because
            # in a long score with a miserly filter
            # it is possible to exceed maximum recursion
            # depth
            if self.childRecursiveIterator is not None:
                try:
                    return next(self.childRecursiveIterator)
                except StopIteration:
                    # self.childRecursiveIterator.parentIterator = None
                    self.childRecursiveIterator = None

            if self.returnSelf is True and self.matchesFilters(self.srcStream):
                self.activeInformation['stream'] = None
                self.activeInformation['index'] = -1
                self.activeInformation['lastYielded'] = self.srcStream
                self.returnSelf = False
                return self.srcStream

            elif self.returnSelf is True:
                self.returnSelf = False

            if self.index >= self.elementsLength:
                self.iterSection = '_endElements'
                self.sectionIndex = self.index - self.elementsLength
            else:
                self.sectionIndex = self.index

            try:
                e = self.srcStreamElements[self.index]
            except IndexError:
                self.index += 1
                # this may happen if the number of elements has changed
                continue

            self.index += 1

            # in a recursive filter, the stream does not need to match the filter,
            # only the internal elements.
            if e.isStream:
                self.childRecursiveIterator = RecursiveIterator(
                    srcStream=e,
                    restoreActiveSites=self.restoreActiveSites,
                    filterList=self.filters,  # shared list...
                    activeInformation=self.activeInformation,  # shared dict
                    includeSelf=False,  # always for inner streams
                    ignoreSorting=self.ignoreSorting,
                    # parentIterator=self,
                )
                newStartOffset = (self.iteratorStartOffsetInHierarchy
                                  + self.srcStream.elementOffset(e))
                self.childRecursiveIterator.iteratorStartOffsetInHierarchy = newStartOffset
            if self.matchesFilters(e) is False:
                continue

            if self.restoreActiveSites is True:
                self.srcStream.coreSelfActiveSite(e)

            self.updateActiveInformation()
            self.activeInformation['lastYielded'] = e
            return e

        # the last element can still set a recursive iterator, so make sure we handle it.
        if self.childRecursiveIterator is not None:
            try:
                return next(self.childRecursiveIterator)
            except StopIteration:
                # self.childRecursiveIterator.parentIterator = None
                self.childRecursiveIterator = None

        self.activeInformation['lastYielded'] = None  # always clean this up, no matter what...
        self.cleanup()
        raise StopIteration

    def reset(self):
        '''
        reset prior to iteration
        '''
        self.returnSelf = self.includeSelf
        self.childRecursiveIterator = None
        self.activeInformation['lastYielded'] = None
        super().reset()

    def matchingElements(self, *, restoreActiveSites=True):
        # saved parent iterator later?
        # will this work in mid-iteration? Test, or do not expose till then.
        with tempAttribute(self, 'childRecursiveIterator'):
            fe = super().matchingElements(restoreActiveSites=restoreActiveSites)
        return fe

    def iteratorStack(self):
        '''
        Returns a stack of RecursiveIterators at this point in the iteration.  Last is most recent.

        >>> b = corpus.parse('bwv66.6')
        >>> bRecurse = b.recurse()
        >>> i = 0
        >>> for _ in bRecurse:
        ...     i += 1
        ...     if i > 12:
        ...         break
        >>> bRecurse.iteratorStack()
        [<music21.stream.iterator.RecursiveIterator for Score:0x10475cdd8 @:2>,
         <music21.stream.iterator.RecursiveIterator for Part:Soprano @:3>,
         <music21.stream.iterator.RecursiveIterator for Measure:m.1 @:3>]
        '''
        iterStack = [self]
        x = self
        while x.childRecursiveIterator is not None:
            x = x.childRecursiveIterator
            iterStack.append(x)
        return iterStack

    def streamStack(self):
        '''
        Returns a stack of Streams at this point.  Last is most recent.

        However, the current element may be the same as the last element in the stack

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

    def currentHierarchyOffset(self):
        '''
        Called on the current iterator, returns the current offset in the hierarchy.
        Or None if we are not currently iterating.

        >>> b = corpus.parse('bwv66.6')
        >>> bRecurse = b.recurse().notes
        >>> print(bRecurse.currentHierarchyOffset())
        None
        >>> for n in bRecurse:
        ...     print(n.measureNumber, bRecurse.currentHierarchyOffset(), n)
        0 0.0 <music21.note.Note C#>
        0 0.5 <music21.note.Note B>
        1 1.0 <music21.note.Note A>
        1 2.0 <music21.note.Note B>
        1 3.0 <music21.note.Note C#>
        1 4.0 <music21.note.Note E>
        2 5.0 <music21.note.Note C#>
        ...
        9 34.5 <music21.note.Note E#>
        9 35.0 <music21.note.Note F#>
        0 0.0 <music21.note.Note E>
        1 1.0 <music21.note.Note F#>
        ...

        After iteration completes, the figure is reset to None:

        >>> print(bRecurse.currentHierarchyOffset())
        None

        The offsets are with respect to the position inside the stream
        being iterated, so for instance, this will not change the output from above:

        >>> o = stream.Opus()
        >>> o.insert(20.0, b)
        >>> bRecurse = b.recurse().notes
        >>> for n in bRecurse:
        ...     print(n.measureNumber, bRecurse.currentHierarchyOffset(), n)
        0 0.0 <music21.note.Note C#>
        ...

        But of course, this will add 20.0 to all numbers:

        >>> oRecurse = o.recurse().notes
        >>> for n in oRecurse:
        ...     print(n.measureNumber, oRecurse.currentHierarchyOffset(), n)
        0 20.0 <music21.note.Note C#>
        ...

        New in v.4
        '''
        lastYield = self.activeInformation['lastYielded']
        if lastYield is None:
            return None

        iteratorStack = self.iteratorStack()
        newestIterator = iteratorStack[-1]
        lastStream = newestIterator.srcStream
        lastStartOffset = newestIterator.iteratorStartOffsetInHierarchy

        if lastYield is lastStream:
            return common.opFrac(lastStartOffset)
        else:
            return common.opFrac(lastStartOffset + lastStream.elementOffset(lastYield))
            # will still return numbers even if _endElements

    def getElementsByOffsetInHierarchy(
            self,
            offsetStart,
            offsetEnd=None,
            *,
            includeEndBoundary=True,
            mustFinishInSpan=False,
            mustBeginInSpan=True,
            includeElementsThatEndAtStart=True) -> 'StreamIterator':
        '''
        Adds a filter keeping only Music21Objects that
        are found at a certain offset or within a certain
        offset time range (given the `offsetStart` and optional `offsetEnd` values) from
        the beginning of the hierarchy.

        >>> b = corpus.parse('bwv66.6')
        >>> for n in b.recurse().getElementsByOffsetInHierarchy(8, 9.5).notes:
        ...     print(n,
        ...           n.getOffsetInHierarchy(b),
        ...           n.measureNumber,
        ...           n.getContextByClass('Part').id)
        <music21.note.Note C#> 8.0 2 Soprano
        <music21.note.Note A> 9.0 3 Soprano
        <music21.note.Note B> 9.5 3 Soprano
        <music21.note.Note G#> 8.0 2 Alto
        <music21.note.Note F#> 9.0 3 Alto
        <music21.note.Note G#> 9.5 3 Alto
        <music21.note.Note C#> 8.0 2 Tenor
        <music21.note.Note C#> 9.0 3 Tenor
        <music21.note.Note D> 9.5 3 Tenor
        <music21.note.Note E#> 8.0 2 Bass
        <music21.note.Note F#> 9.0 3 Bass
        <music21.note.Note B> 9.5 3 Bass

        Changed in v5.5 -- all behavior changing options are keyword only.
        '''
        f = filters.OffsetHierarchyFilter(
            offsetStart,
            offsetEnd,
            includeEndBoundary=includeEndBoundary,
            mustFinishInSpan=mustFinishInSpan,
            mustBeginInSpan=mustBeginInSpan,
            includeElementsThatEndAtStart=includeElementsThatEndAtStart)
        return self.addFilter(f)


class Test(unittest.TestCase):
    def testSimpleClone(self):
        from music21 import note
        from music21 import stream
        s = stream.Stream()
        r = note.Rest()
        n = note.Note()
        s.append([r, n])
        all_s = list(s.iter())
        self.assertEqual(len(all_s), 2)
        self.assertIs(all_s[0], r)
        self.assertIs(all_s[1], n)
        s_notes = list(s.iter().notes)
        self.assertEqual(len(s_notes), 1)
        self.assertIs(s_notes[0], n)

    def testAddingFiltersMidIteration(self):
        from music21 import note
        from music21 import stream
        s = stream.Stream()
        r = note.Rest()
        n = note.Note()
        s.append([r, n])
        sIter = s.iter()
        r0 = next(sIter)
        self.assertIs(r0, r)

        # adding a filter gives a new StreamIterator that restarts at 0
        sIter2 = sIter.getElementsByClass('GeneralNote')  # this filter does nothing here.
        obj0 = next(sIter2)
        self.assertIs(obj0, r)

        # original StreamIterator should be at its original spot, so this should
        # move to next element
        n0 = next(sIter)
        self.assertIs(n0, n)

    def testRecursiveActiveSites(self):
        from music21 import converter
        s = converter.parse('tinyNotation: 4/4 c1 c4 d=id2 e f')
        rec = s.recurse()
        n = rec.getElementById('id2')
        self.assertEqual(n.activeSite.number, 2)

    def testCurrentHierarchyOffsetReset(self):
        from music21 import note
        from music21 import stream
        p = stream.Part()
        m = stream.Measure()
        m.append(note.Note('D'))
        m.append(note.Note('E'))
        p.insert(0, note.Note('C'))
        p.append(m)
        pRecurse = p.recurse(includeSelf=True)
        allOffsets = []
        for unused in pRecurse:
            allOffsets.append(pRecurse.currentHierarchyOffset())
        self.assertListEqual(allOffsets, [0.0, 0.0, 1.0, 1.0, 2.0])
        currentOffset = pRecurse.currentHierarchyOffset()
        self.assertIsNone(currentOffset)

    def testAddingFiltersMidRecursiveIteration(self):
        from music21 import note
        from music21 import stream
        from music21.stream.iterator import RecursiveIterator as ImportedRecursiveIterator
        m = stream.Measure()
        r = note.Rest()
        n = note.Note()
        m.append([r, n])
        p = stream.Part()
        p.append(m)

        sc = stream.Score()
        sc.append(p)

        sIter = sc.recurse()
        p0 = next(sIter)
        self.assertIs(p0, p)

        child = sIter.childRecursiveIterator
        self.assertIsInstance(child, ImportedRecursiveIterator)




_DOC_ORDER = [StreamIterator, RecursiveIterator, OffsetIterator]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testCurrentHierarchyOffsetReset')
