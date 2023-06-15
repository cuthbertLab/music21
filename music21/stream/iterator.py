# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/iterator.py
# Purpose:      Classes for walking through streams
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
this class contains iterators and filters for walking through streams

StreamIterators are explicitly allowed to access private methods on streams.
'''
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
import copy
import typing as t
from typing import overload  # PyCharm can't use alias
import unittest
import warnings

from music21 import common
from music21.common.classTools import tempAttribute, saveAttributes
from music21.common.enums import OffsetSpecial
from music21.common.types import M21ObjType, StreamType
from music21 import note
from music21.stream import filters
from music21 import prebase
from music21 import base   # just for typing. (but in a bound, so keep here)

from music21.sites import SitesException

if t.TYPE_CHECKING:
    from music21 import stream

T = t.TypeVar('T')
S = t.TypeVar('S')
ChangedM21ObjType = t.TypeVar('ChangedM21ObjType', bound=base.Music21Object)
StreamIteratorType = t.TypeVar('StreamIteratorType', bound='StreamIterator')

# pipe | version not passing mypy.
FilterType = t.Union[Callable[[t.Any, t.Optional[t.Any]], t.Any], filters.StreamFilter]


# -----------------------------------------------------------------------------
class StreamIteratorInefficientWarning(UserWarning):
    pass


class ActiveInformation(t.TypedDict, total=False):
    stream: stream.Stream | None
    elementIndex: int
    iterSection: t.Literal['_elements', '_endElements']
    sectionIndex: int
    lastYielded: base.Music21Object | None



# -----------------------------------------------------------------------------
class StreamIterator(prebase.ProtoM21Object, Sequence[M21ObjType]):
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
    * StreamIterator.elementIndex -- current index item
    * StreamIterator.streamLength -- length of elements.

    * StreamIterator.srcStreamElements -- srcStream._elements
    * StreamIterator.cleanupOnStop -- should the StreamIterator delete the
      reference to srcStream and srcStreamElements when stopping? default
      False
    * StreamIterator.activeInformation -- a dict that contains information
      about where we are in the parse.  Especially useful for recursive
      streams:

          * `stream` = the stream that is currently active,
          * `elementIndex` = where in `.elements` we are,
          * `iterSection` is `_elements` or `_endElements`,
          * `sectionIndex` is where we are in the iterSection, or -1 if
            we have not started.
          * `lastYielded` the element that was last returned by the iterator.
            (for OffsetIterators, contains the first element last returned)
          * (This dict is shared among all sub iterators.)

    Constructor keyword only arguments:

    * `filterList` is a list of stream.filters.Filter objects to apply

    * if `restoreActiveSites` is True (default) then on iterating, the activeSite is set
      to the Stream being iterated over.

    * if `ignoreSorting` is True (default is False) then the Stream is not sorted before
      iterating.  If the Stream is already sorted, then this value does not matter, and
      no time will be saved by setting to False.

    * For `activeInformation` see above.

    * Changed in v5.2: all arguments except srcStream are keyword only.
    * Changed in v8:
      - filterList must be a list or None, not a single filter.
      - StreamIterator inherits from typing.Sequence, hence index
      was moved to elementIndex.

    OMIT_FROM_DOCS

    Informative exception for user error:

    >>> s = stream.Stream()
    >>> sIter = stream.iterator.StreamIterator(s, filterList=[note.Note])
    Traceback (most recent call last):
    TypeError: filterList expects Filters or callables,
    not types themselves; got <class 'music21.note.Note'>

    THIS IS IN OMIT -- Add info above.
    '''
    def __init__(self,
                 srcStream: StreamType,
                 *,
                 # restrictClass: type[M21ObjType] = base.Music21Object,
                 filterList: list[FilterType] | None = None,
                 restoreActiveSites: bool = True,
                 activeInformation: ActiveInformation | None = None,
                 ignoreSorting: bool = False):
        if not ignoreSorting and srcStream.isSorted is False and srcStream.autoSort:
            srcStream.sort()
        self.srcStream: StreamType = srcStream
        self.elementIndex: int = 0

        # use .elements instead of ._elements/etc. so that it is sorted...
        self.srcStreamElements = t.cast(tuple[M21ObjType, ...], srcStream.elements)
        self.streamLength: int = len(self.srcStreamElements)

        # this information can help in speed later
        self.elementsLength: int = len(self.srcStream._elements)

        # where we are within a given section (_elements or _endElements)
        self.sectionIndex: int = -1
        self.iterSection: t.Literal['_elements', '_endElements'] = '_elements'

        self.cleanupOnStop: bool = False
        self.restoreActiveSites: bool = restoreActiveSites

        self.overrideDerivation: str | None = None

        if filterList is None:
            filterList = []
        for x in filterList:
            if isinstance(x, type):
                raise TypeError(
                    f'filterList expects Filters or callables, not types themselves; got {x}')
        # self.filters is a list of expressions that
        # return True or False for an element for
        # whether it should be yielded.
        self.filters: list[FilterType] = filterList
        self._len: int | None = None
        self._matchingElements: list[M21ObjType] | None = None
        # keep track of where we are in the parse.
        # esp important for recursive streams...
        if activeInformation is not None:
            self.activeInformation: ActiveInformation = activeInformation
        else:
            self.activeInformation = {}
            self.updateActiveInformation()

    def _reprInternal(self):
        streamClass = self.srcStream.__class__.__name__
        srcStreamId = self.srcStream.id
        if isinstance(srcStreamId, int):
            srcStreamId = hex(srcStreamId)

        if streamClass == 'Measure' and self.srcStream.number != 0:
            srcStreamId = 'm.' + str(self.srcStream.number)

        return f'for {streamClass}:{srcStreamId} @:{self.elementIndex}'

    def __iter__(self: StreamIteratorType) -> StreamIteratorType:
        self.reset()
        return self

    def __next__(self) -> M21ObjType:
        while self.elementIndex < self.streamLength:
            if self.elementIndex >= self.elementsLength:
                self.iterSection = '_endElements'
                self.sectionIndex = self.elementIndex - self.elementsLength
            else:
                self.sectionIndex = self.elementIndex

            try:
                e = self.srcStreamElements[self.elementIndex]
            except IndexError:
                # this may happen if the number of elements has changed
                self.elementIndex += 1
                continue

            self.elementIndex += 1
            if self.matchesFilters(e) is False:
                continue

            if self.restoreActiveSites is True:
                self.srcStream.coreSelfActiveSite(e)

            self.updateActiveInformation()
            self.activeInformation['lastYielded'] = e
            return e

        self.cleanup()
        raise StopIteration

    def __getattr__(self, attr):
        '''
        DEPRECATED in v8 -- will be removed in v9.

        In case an attribute is defined on Stream but not on a StreamIterator,
        create a Stream and then return that attribute.  This is NOT performance
        optimized -- calling this repeatedly will mean creating a lot of different
        streams.  However, it will prevent most code that worked on v2. from breaking
        on v3 and onwards.

        Deprecated in v8. The upgrade path is to just call `.stream()` on the iterator
        before accessing the attribute.

        >>> s = stream.Measure()
        >>> s.insert(0, note.Rest())
        >>> s.repeatAppend(note.Note('C'), 2)

        >>> s.definesExplicitSystemBreaks
        False

        >>> s.notes
        <music21.stream.iterator.StreamIterator for Measure:0x101c1a208 @:0>

        >>> import warnings  #_DOCS_HIDE
        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore') #_DOCS_HIDE
        ...      explicit = s.notes.definesExplicitSystemBreaks #_DOCS_HIDE
        >>> #_DOCS_SHOW explicit = s.notes.definesExplicitSystemBreaks
        >>> explicit
        False

        Works with methods as well:

        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore') #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>

        But remember that a new Stream is being created each time that an attribute
        only defined on a Stream is called, so for instance, so you can pop() forever,
        always getting the same element.

        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore') #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>
        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore') #_DOCS_HIDE
        ...      popC = s.notes.pop(0) #_DOCS_HIDE
        >>> #_DOCS_SHOW popC = s.notes.pop(0)
        >>> popC
        <music21.note.Note C>
        >>> with warnings.catch_warnings(): #_DOCS_HIDE
        ...      warnings.simplefilter('ignore') #_DOCS_HIDE
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

    @overload
    def __getitem__(self, k: int) -> M21ObjType:
        return self.matchingElements()[k]

    @overload
    def __getitem__(self, k: slice) -> list[M21ObjType]:
        return self.matchingElements()

    @overload
    def __getitem__(self, k: str) -> M21ObjType | None:
        return None

    def __getitem__(self, k: int | slice | str) -> M21ObjType | list[M21ObjType] | None:
        '''
        Iterators can request other items by index or slice.

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


        To request an element by id, put a '#' sign in front of the id,
        like in HTML DOM queries:

        >>> bach = corpus.parse('bwv66.6')
        >>> soprano = bach.recurse()['#Soprano']
        >>> soprano
        <music21.stream.Part Soprano>

        This behavior is often used to get an element from the Parts iterator:

        >>> bach.parts['#soprano']  # notice: case-insensitive retrieval
        <music21.stream.Part Soprano>

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
        >>> sI.srcStream is s  # set to an empty stream
        False
        >>> for n in sI:
        ...    printer = (repr(n), repr(sI[0]))
        ...    print(printer)

        (nothing is printed)

        * Changed in v8: for strings: prepend a '#' sign to get elements by id.
          The old behavior still works until v9.
          This is an attempt to unify __getitem__ behavior in
          StreamIterators and Streams.
        '''
        fe = self.matchingElements()
        if isinstance(k, str):
            if k.startswith('#'):
                # prepare for query selectors.
                k = k[1:]

            for el in fe:
                if isinstance(el.id, str) and el.id.lower() == k.lower():
                    return el
            raise KeyError(k)

        e = fe[k]
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
        lenMatching = len(self.matchingElements(restoreActiveSites=False))
        self._len = lenMatching
        self.reset()
        return lenMatching

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

        >>> bool(iterator.getElementsByClass(chord.Chord))
        False

        test false cache:

        >>> len(iterator.getElementsByClass(chord.Chord))
        0
        >>> bool(iterator.getElementsByClass(chord.Chord))
        False

        '''
        if self._len is not None:
            return bool(self._len)

        # do not change active site of first element in bool
        with tempAttribute(self, 'restoreActiveSites', False):
            for unused in self:
                return True

        return False

    def __contains__(self, item):
        '''
        Does the iterator contain `item`?  Needed for AbstractBaseClass
        '''
        return item in self.matchingElements(restoreActiveSites=False)

    def __reversed__(self):
        me = self.matchingElements()
        me.reverse()
        for item in me:
            yield item

    def clone(self: StreamIteratorType) -> StreamIteratorType:
        '''
        Returns a new copy of the same iterator.
        (a shallow copy of some things except activeInformation)
        '''
        out: StreamIteratorType = type(self)(
            self.srcStream,
            filterList=copy.copy(self.filters),
            restoreActiveSites=self.restoreActiveSites,
            activeInformation=copy.copy(self.activeInformation),
        )
        return out

    def first(self) -> M21ObjType | None:
        '''
        Efficiently return the first matching element, or None if no
        elements match.

        Does not require creating the whole list of matching elements.

        >>> s = converter.parse('tinyNotation: 3/4 D4 E2 F4 r2 G2 r4')
        >>> s.recurse().notes.first()
        <music21.note.Note D>
        >>> s[note.Rest].first()
        <music21.note.Rest half>

        If no elements match, returns None:

        >>> print(s[chord.Chord].first())
        None

        * New in v7.

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

    def last(self) -> M21ObjType | None:
        '''
        Returns the last matching element, or None if no elements match.

        Currently is not efficient (does not iterate backwards, for instance),
        but easier than checking for an IndexError.  Might be refactored later
        to iterate the stream backwards instead if it gets a lot of use.

        >>> s = converter.parse('tinyNotation: 3/4 D4 E2 F4 r2 G2 r4')
        >>> s.recurse().notes.last()
        <music21.note.Note G>
        >>> s[note.Rest].last()
        <music21.note.Rest quarter>

        * New in v7.

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
    def updateActiveInformation(self) -> None:
        '''
        Updates the (shared) activeInformation dictionary
        with information about where we are.

        Call before any element return.
        '''
        ai = self.activeInformation
        ai['stream'] = self.srcStream
        ai['elementIndex'] = self.elementIndex - 1
        ai['iterSection'] = self.iterSection
        ai['sectionIndex'] = self.sectionIndex
        ai['lastYielded'] = None

    def reset(self) -> None:
        '''
        reset prior to iteration
        '''
        self.elementIndex = 0
        self.iterSection = '_elements'
        self.updateActiveInformation()
        self.activeInformation['lastYielded'] = None
        for f in self.filters:
            if isinstance(f, filters.StreamFilter):
                f.reset()

    def resetCaches(self) -> None:
        '''
        reset any cached data. -- do not use this at
        the start of iteration since we might as well
        save this information. But do call it if
        the filter changes.
        '''
        self._len = None
        self._matchingElements = None

    def cleanup(self) -> None:
        '''
        stop iteration; and cleanup if need be.
        '''
        if self.cleanupOnStop:
            self.reset()

            # cleanupOnStop is rarely used, so we put in
            # a dummy stream so that srcStream does not need
            # to be x | None
            SrcStreamClass = self.srcStream.__class__

            del self.srcStream
            del self.srcStreamElements
            self.srcStream = SrcStreamClass()
            self.srcStreamElements = ()

    # ---------------------------------------------------------------
    # getting items

    def matchingElements(
        self,
        *,
        restoreActiveSites: bool = True
    ) -> list[M21ObjType]:
        '''
        Returns a list of elements that match the filter.

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
        [<music21.stream.filters.ClassFilter <class 'music21.note.NotRest'>>]

        >>> sI_notes.matchingElements()
        [<music21.note.Note C>, <music21.note.Note D>,
         <music21.note.Note E>, <music21.note.Note F>, <music21.note.Note G>,
         <music21.note.Note A>]

        If restoreActiveSites is False then the elements will not have
        their activeSites changed (callers should use it when they do not plan to actually
        expose the elements to users, such as in `__len__`).

        * New in v7: restoreActiveSites
        '''
        if self._matchingElements is not None:
            return self._matchingElements

        with saveAttributes(self, 'restoreActiveSites', 'elementIndex'):
            self.restoreActiveSites = restoreActiveSites
            # we iterate to set all activeSites
            me = [x for x in self]  # pylint: disable=unnecessary-comprehension
            self.reset()

        if restoreActiveSites == self.restoreActiveSites:
            # cache, if we are using the iterator default.
            self._matchingElements = me

        return me

    def matchesFilters(self, e: base.Music21Object) -> bool:
        '''
        returns False if any filter returns False, True otherwise.
        '''
        f: FilterType
        for f in self.filters:
            try:
                try:
                    if f(e, self) is False:
                        return False
                except TypeError:  # one element filters are acceptable.
                    if t.TYPE_CHECKING:
                        assert isinstance(f, filters.StreamFilter)
                    if f(e) is False:
                        return False
            except StopIteration:  # pylint: disable=try-except-raise
                raise  # clearer this way to see that this can happen...
        return True

    def _newBaseStream(self) -> stream.Stream:
        '''
        Returns a new stream.Stream.  The same thing as calling:

        >>> s = stream.Stream()

        This is used in places where returnStreamSubclass is False, so we
        cannot just call `type(StreamIterator.srcStream)()`

        >>> p = stream.Part()
        >>> pi = p.iter()
        >>> s = pi._newBaseStream()
        >>> s
        <music21.stream.Stream 0x1047eb2e8>
        '''
        from music21 import stream
        return stream.Stream()

    @overload
    def stream(self, returnStreamSubClass: t.Literal[False]) -> stream.Stream:
        # ignore this code -- just here until Astroid bug #1015 is fixed
        x: stream.Stream = self.streamObj
        return x

    @overload
    def stream(self, returnStreamSubClass: t.Literal[True] = True) -> StreamType:  # type: ignore
        # Astroid bug + new mypy 0.981 problem -- if type-var is a problem here, then
        # it should be in the non-overloaded function below.
        x: StreamType = self.streamObj
        return x

    def stream(self, returnStreamSubClass=True) -> stream.Stream | StreamType:
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

        >>> s2 = s.iter().getElementsByClass(note.Note).stream()
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

        >>> s4 = s.iter().getElementsByClass(bar.Barline).stream()
        >>> s4.show('t')
        {0.0} <music21.bar.Barline type=regular>


        Note that this routine can create Streams that have elements that the original
        stream did not, in the case of recursion:

        >>> bach = corpus.parse('bwv66.6')
        >>> bn = bach.flatten()[34]
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
        found: stream.Stream | StreamType
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
                if isinstance(f, filters.StreamFilter):
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
    def activeElementList(self) -> t.Literal['_elements', '_endElements']:
        '''
        Returns the element list (`_elements` or `_endElements`)
        for the current activeInformation.
        '''
        return getattr(self.activeInformation['stream'], self.activeInformation['iterSection'])

    # ------------------------------------------------------------

    def addFilter(
        self: StreamIteratorType,
        newFilter,
        *,
        returnClone=True
    ) -> StreamIteratorType:
        '''
        Return a new StreamIterator with an additional filter.
        Also resets caches -- so do not add filters any other way.

        If returnClone is False then adds without creating a new StreamIterator

        * Changed in v6: Encourage creating new StreamIterators: change
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

    def removeFilter(
        self: StreamIteratorType,
        oldFilter,
        *,
        returnClone=True
    ) -> StreamIteratorType:
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

    def getElementById(self, elementId: str) -> M21ObjType | None:
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

    # Replace all code in overload statements once
    # https://github.com/PyCQA/astroid/issues/1015
    # is fixed and deployed
    @overload
    def getElementsByClass(self,
                           classFilterList: str,
                           *,
                           returnClone: bool = True) -> StreamIterator[M21ObjType]:
        x: StreamIterator[M21ObjType] = self.__class__(self.streamObj)
        return x

    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[str],
                           *,
                           returnClone: bool = True) -> StreamIterator[M21ObjType]:
        x: StreamIterator[M21ObjType] = self.__class__(self.streamObj)
        return x

    # @overload
    # def getElementsByClass(self,
    #                        classFilterList: type,
    #                        *,
    #                        returnClone: bool = True) -> StreamIterator[M21ObjType]:
    #     # putting a non-music21 type into classFilterList, defaults to the previous type
    #     x: StreamIterator[M21ObjType] = self.__class__(self.streamObj)
    #     return x

    @overload
    def getElementsByClass(self,
                           classFilterList: type[ChangedM21ObjType],
                           *,
                           returnClone: bool = True) -> StreamIterator[ChangedM21ObjType]:
        x = t.cast(StreamIterator[ChangedM21ObjType], self.__class__(self.streamObj))
        return x

    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[type],
                           *,
                           returnClone: bool = True) -> StreamIterator[M21ObjType]:
        # putting multiple types into classFilterList, defaults to the previous type
        x: StreamIterator[M21ObjType] = self.__class__(self.streamObj)
        return x


    def getElementsByClass(
        self,
        classFilterList: t.Union[
            str,
            type[ChangedM21ObjType],
            Iterable[str],
            Iterable[type],
        ],
        *,
        returnClone: bool = True
    ) -> t.Union[StreamIterator[M21ObjType], StreamIterator[ChangedM21ObjType]]:
        '''
        Add a filter to the Iterator to remove all elements
        except those that match one
        or more classes in the `classFilterList`. A single class
        can also be used for the `classFilterList` parameter instead of a List.

        >>> s = stream.Stream(id='s1')
        >>> s.append(note.Note('C'))
        >>> r = note.Rest()
        >>> s.append(r)
        >>> s.append(note.Note('D'))
        >>> for el in s.iter().getElementsByClass(note.Rest):
        ...     print(el)
        <music21.note.Rest quarter>


        ActiveSite is restored...

        >>> s2 = stream.Stream(id='s2')
        >>> s2.insert(0, r)
        >>> r.activeSite.id
        's2'

        >>> for el in s.iter().getElementsByClass(note.Rest):
        ...     print(el.activeSite.id)
        s1


        Strings work in addition to classes, but your IDE will not know that
        `el` is a :class:`~music21.note.Rest` object.

        >>> for el in s.iter().getElementsByClass('Rest'):
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
          with `'high'` in el.groups.
        * Any other string is considered to be the type/class of the element.  So `Note`
          will find all Note elements.  Can be fully qualified like `music21.note.Note`
          or partially qualified like `note.Note`.

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

        * New in v7.
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
        self: StreamIteratorType,
        offsetStart,
        offsetEnd=None,
        *,
        includeEndBoundary=True,
        mustFinishInSpan=False,
        mustBeginInSpan=True,
        includeElementsThatEndAtStart=True,
        stopAfterEnd=True,
        returnClone=True,
    ) -> StreamIteratorType:
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

        This chart, like the examples below, demonstrates the various
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
         <music21.tempo.MetronomeMark Quarter=96 (playback only)>,
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

        >>> soprano = bwv66.parts['#Soprano']  # = getElementById('Soprano')
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

        * Changed in v5.5: all arguments changing behavior are keyword only.
        * New in v6.5: `stopAfterEnd` keyword.

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
        Returns all :class:`~music21.note.NotRest` objects

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
        return self.getElementsByClass(note.NotRest)

    @property
    def notesAndRests(self):
        '''
        Returns all :class:`~music21.note.GeneralNote` objects, including
        Rests and Unpitched elements.

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
        return self.getElementsByClass(note.GeneralNote)

    @property
    def parts(self):
        '''
        Adds a ClassFilter for Part objects
        '''
        from music21 import stream
        return self.getElementsByClass(stream.Part)

    @property
    def spanners(self):
        '''
        Adds a ClassFilter for Spanner objects
        '''
        from music21 import spanner
        return self.getElementsByClass(spanner.Spanner)

    @property
    def voices(self):
        '''
        Adds a ClassFilter for Voice objects
        '''
        from music21 import stream
        return self.getElementsByClass(stream.Voice)


# -----------------------------------------------------------------------------
class OffsetIterator(StreamIterator, Sequence[list[M21ObjType]]):
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

    >>> for groupedElements in stream.iterator.OffsetIterator(s).getElementsByClass(clef.Clef):
    ...     print(groupedElements)
    [<music21.clef.TrebleClef>]
    '''
    def __init__(self,
                 srcStream,
                 *,
                 # restrictClass: type[M21ObjType] = base.Music21Object,
                 filterList=None,
                 restoreActiveSites=True,
                 activeInformation=None,
                 ignoreSorting=False
                 ) -> None:
        super().__init__(srcStream,
                         # restrictClass=restrictClass,
                         filterList=filterList,
                         restoreActiveSites=restoreActiveSites,
                         activeInformation=activeInformation,
                         ignoreSorting=ignoreSorting,
                         )
        self.raiseStopIterationNext = False
        self.nextToYield: list[M21ObjType] = []
        self.nextOffsetToYield = None

    def __next__(self) -> list[M21ObjType]:  # type: ignore
        if self.raiseStopIterationNext:
            raise StopIteration

        retElementList: list[M21ObjType] = []
        # make sure that cleanup is not called during the loop...
        try:
            if self.nextToYield:
                retElementList = self.nextToYield
                retElOffset = self.nextOffsetToYield
            else:
                retEl = super().__next__()
                retElOffset = self.srcStream.elementOffset(retEl)
                retElementList = [retEl]

            while self.elementIndex <= self.streamLength:
                nextEl = super().__next__()
                nextElOffset = self.srcStream.elementOffset(nextEl)
                if nextElOffset == retElOffset:
                    retElementList.append(nextEl)
                else:
                    self.nextToYield = [nextEl]
                    self.nextOffsetToYield = nextElOffset
                    self.activeInformation['lastYielded'] = retElementList[0]
                    return retElementList

        except StopIteration:
            if retElementList:
                self.raiseStopIterationNext = True
                self.activeInformation['lastYielded'] = retElementList[0]
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

    # NOTE: these getElementsByClass are the same as the one in StreamIterator, but
    # for now it needs to be duplicated until changing a Generic's argument type
    # can be done with inheritance.
    # TODO: remove code and replace with ... when Astroid bug #1015 is fixed.

    @overload
    def getElementsByClass(self,
                           classFilterList: str,
                           *,
                           returnClone: bool = True) -> OffsetIterator[M21ObjType]:
        x: OffsetIterator[M21ObjType] = self.__class__(self.streamObj)
        return x

    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[str],
                           *,
                           returnClone: bool = True) -> OffsetIterator[M21ObjType]:
        x: OffsetIterator[M21ObjType] = self.__class__(self.streamObj)
        return x

    @overload
    def getElementsByClass(self,
                           classFilterList: type[ChangedM21ObjType],
                           *,
                           returnClone: bool = True) -> OffsetIterator[ChangedM21ObjType]:
        x = t.cast(OffsetIterator[ChangedM21ObjType], self.__class__(self.streamObj))
        return x

    # @overload
    # def getElementsByClass(self,
    #                        classFilterList: type,
    #                        *,
    #                        returnClone: bool = True) -> OffsetIterator[M21ObjType]:
    #     x: OffsetIterator[M21ObjType] = self.__class__(self.streamObj)
    #     return x


    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[type],
                           *,
                           returnClone: bool = True) -> OffsetIterator[M21ObjType]:
        x: OffsetIterator[M21ObjType] = self.__class__(self.streamObj)
        return x


    def getElementsByClass(self,
                           classFilterList: t.Union[
                               str,
                               type[ChangedM21ObjType],
                               Iterable[str],
                               Iterable[type],
                           ],
                           *,
                           returnClone: bool = True
                           ) -> t.Union[OffsetIterator[M21ObjType],
                                        OffsetIterator[ChangedM21ObjType]]:
        '''
        Identical to the same method in StreamIterator, but needs to be duplicated
        for now.
        '''
        return self.addFilter(filters.ClassFilter(classFilterList), returnClone=returnClone)



# -----------------------------------------------------------------------------
class RecursiveIterator(StreamIterator, Sequence[M21ObjType]):
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
    <music21.stream.Score bach/bwv66.6.mxl>
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
    <music21.stream.iterator.RecursiveIterator for Score:bach/bwv66.6.mxl @:0>

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
    def __init__(
        self,
        srcStream,
        *,
        # restrictClass: type[M21ObjType] = base.Music21Object,
        filterList=None,
        restoreActiveSites=True,
        activeInformation=None,
        streamsOnly=False,
        includeSelf=False,
        ignoreSorting=False
    ) -> None:  # , parentIterator=None):
        super().__init__(srcStream,
                         # restrictClass=restrictClass,
                         filterList=filterList,
                         restoreActiveSites=restoreActiveSites,
                         activeInformation=activeInformation,
                         ignoreSorting=ignoreSorting,
                         )
        self.returnSelf = includeSelf  # do I still need to return the self object?
        self.includeSelf = includeSelf
        self.ignoreSorting = ignoreSorting

        # within the list of parent/child recursive iterators, where does this start?
        self.iteratorStartOffsetInHierarchy = 0.0

        if streamsOnly is True:
            self.filters.append(filters.ClassFilter('Stream'))
        self.childRecursiveIterator: RecursiveIterator[t.Any] | None = None
        # not yet used.
        # self.parentIterator = None

    def __next__(self) -> M21ObjType:
        '''
        Get the next element of the stream under iteration.

        The same __iter__ as the superclass is used.
        '''
        while self.elementIndex < self.streamLength:
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
                self.activeInformation['elementIndex'] = -1
                self.activeInformation['lastYielded'] = self.srcStream
                self.returnSelf = False
                return t.cast(M21ObjType, self.srcStream)

            elif self.returnSelf is True:
                self.returnSelf = False

            if self.elementIndex >= self.elementsLength:
                self.iterSection = '_endElements'
                self.sectionIndex = self.elementIndex - self.elementsLength
            else:
                self.sectionIndex = self.elementIndex

            try:
                e = self.srcStreamElements[self.elementIndex]
            except IndexError:
                self.elementIndex += 1
                # this may happen if the number of elements has changed
                continue

            self.elementIndex += 1

            # in a recursive filter, the stream does not need to match the filter,
            # only the internal elements.
            if e.isStream:
                if t.TYPE_CHECKING:
                    assert isinstance(e, stream.Stream)

                childRecursiveIterator: RecursiveIterator[M21ObjType] = RecursiveIterator(
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

                childRecursiveIterator.iteratorStartOffsetInHierarchy = newStartOffset
                self.childRecursiveIterator = childRecursiveIterator
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
        super().reset()

    def matchingElements(self, *, restoreActiveSites=True):
        # saved parent iterator later?
        # will this work in mid-iteration? Test, or do not expose till then.
        with tempAttribute(self, 'childRecursiveIterator'):
            fe = super().matchingElements(restoreActiveSites=restoreActiveSites)
        return fe

    def iteratorStack(self) -> list[RecursiveIterator]:
        '''
        Returns a stack of RecursiveIterators at this point in the iteration.  Last is most recent.

        >>> b = corpus.parse('bwv66.6')
        >>> bRecurse = b.recurse()
        >>> i = 0
        >>> for _ in bRecurse:
        ...     i += 1
        ...     if i > 13:
        ...         break
        >>> bRecurse.iteratorStack()
        [<music21.stream.iterator.RecursiveIterator for Score:bach/bwv66.6.mxl @:2>,
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
        [<music21.stream.Score bach/bwv66.6.mxl>,
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

        * New in v4.
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
            self: StreamIteratorType,
            offsetStart,
            offsetEnd=None,
            *,
            includeEndBoundary=True,
            mustFinishInSpan=False,
            mustBeginInSpan=True,
            includeElementsThatEndAtStart=True) -> StreamIteratorType:
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
        ...           n.getContextByClass(stream.Part).id)
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

        * Changed in v5.5: all behavior changing options are keyword only.
        '''
        f = filters.OffsetHierarchyFilter(
            offsetStart,
            offsetEnd,
            includeEndBoundary=includeEndBoundary,
            mustFinishInSpan=mustFinishInSpan,
            mustBeginInSpan=mustBeginInSpan,
            includeElementsThatEndAtStart=includeElementsThatEndAtStart)
        return self.addFilter(f)

    @overload
    def getElementsByClass(self,
                           classFilterList: str,
                           *,
                           returnClone: bool = True) -> RecursiveIterator[M21ObjType]:
        x: RecursiveIterator[M21ObjType] = self.__class__(self.streamObj)
        return x  # dummy code  remove when Astroid #1015 is fixed.

    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[str],
                           *,
                           returnClone: bool = True) -> RecursiveIterator[M21ObjType]:
        x: RecursiveIterator[M21ObjType] = self.__class__(self.streamObj)
        return x  # dummy code

    @overload
    def getElementsByClass(self,
                           classFilterList: type[ChangedM21ObjType],
                           *,
                           returnClone: bool = True) -> RecursiveIterator[ChangedM21ObjType]:
        x = t.cast(RecursiveIterator[ChangedM21ObjType], self.__class__(self.streamObj))
        return x  # dummy code

    # @overload
    # def getElementsByClass(self,
    #                        classFilterList: type,
    #                        *,
    #                        returnClone: bool = True) -> RecursiveIterator[M21ObjType]:
    #     x: RecursiveIterator[M21ObjType] = self.__class__(self.streamObj)
    #     return x  # dummy code

    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[type],
                           *,
                           returnClone: bool = True) -> RecursiveIterator[M21ObjType]:
        x: RecursiveIterator[M21ObjType] = self.__class__(self.streamObj)
        return x  # dummy code


    def getElementsByClass(self,
                           classFilterList: t.Union[
                               str,
                               type[ChangedM21ObjType],
                               Iterable[str],
                               Iterable[type[ChangedM21ObjType]],
                           ],
                           *,
                           returnClone: bool = True
                           ) -> t.Union[RecursiveIterator[M21ObjType],
                                        RecursiveIterator[ChangedM21ObjType]]:
        out = super().getElementsByClass(classFilterList, returnClone=returnClone)
        if isinstance(classFilterList, type) and issubclass(classFilterList, base.Music21Object):
            return t.cast(RecursiveIterator[ChangedM21ObjType], out)
        else:
            return t.cast(RecursiveIterator[M21ObjType], out)


class Test(unittest.TestCase):
    def testSimpleClone(self):
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
        from music21 import stream
        s = stream.Stream()
        r = note.Rest()
        n = note.Note()
        s.append([r, n])
        sIter = s.iter()
        r0 = next(sIter)
        self.assertIs(r0, r)

        # adding a filter gives a new StreamIterator that restarts at 0
        sIter2 = sIter.notesAndRests  # this filter does nothing here.
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
