# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/core.py
# Purpose:      mixin class for the core elements of Streams
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
the Stream Core Mixin handles the core attributes of streams that
should be thought of almost as private values and not used except
by advanced programmers who need the highest speed in programming.

Nothing here promises to be stable.  The music21 team can make
any changes here for efficiency reasons while being considered
backwards compatible so long as the public methods that call this
remain stable.

All functions here will eventually begin with `.core`.
'''
import copy
from typing import List, Dict, Union, Tuple, Optional
from fractions import Fraction
import unittest

from music21.base import Music21Object
from music21.common.enums import OffsetSpecial
from music21.common.numberTools import opFrac
from music21 import spanner
from music21 import tree
from music21.exceptions21 import StreamException, ImmutableStreamException
from music21.stream.iterator import StreamIterator

# pylint: disable=attribute-defined-outside-init
class StreamCoreMixin:
    '''
    Core aspects of a Stream's behavior.  Any of these can change at any time.
    '''
    def __init__(self):
        # hugely important -- keeps track of where the _elements are
        # the _offsetDict is a dictionary where id(element) is the
        # index and the value is a tuple of offset and element.
        # offsets can be floats, Fractions, or a member of the enum OffsetSpecial
        self._offsetDict: Dict[int, Tuple[Union[float, Fraction, str], Music21Object]] = {}

        # self._elements stores Music21Object objects.
        self._elements: List[Music21Object] = []

        # self._endElements stores Music21Objects found at
        # the highestTime of this Stream.
        self._endElements: List[Music21Object] = []

        self.isSorted = True
        # should isFlat become readonly?
        self.isFlat = True  # does it have no embedded Streams

        # someday...
        # self._elementTree = tree.trees.ElementTree(source=self)

    def coreInsert(
        self,
        offset: Union[float, Fraction],
        element: Music21Object,
        *,
        ignoreSort=False,
        setActiveSite=True
    ):
        '''
        N.B. -- a "core" method, not to be used by general users.  Run .insert() instead.

        A faster way of inserting elements that does no checks,
        just insertion.

        Only be used in contexts that we know we have a proper, single Music21Object.
        Best for usage when taking objects in a known Stream and creating a new Stream

        When using this method, the caller is responsible for calling Stream.coreElementsChanged
        after all operations are completed.

        Do not mix coreInsert with coreAppend operations.

        Returns boolean if the Stream is now sorted.
        '''
        # environLocal.printDebug(['coreInsert', 'self', self,
        #    'offset', offset, 'element', element])
        # need to compare highest time before inserting the element in
        # the elements list
        storeSorted = False
        if not ignoreSort:
            # # if sorted and our insertion is > the highest time, then
            # # are still inserted
            # if self.isSorted is True and self.highestTime <= offset:
            #     storeSorted = True
            if self.isSorted is True:
                ht = self.highestTime
                if ht < offset:
                    storeSorted = True
                elif ht == offset:
                    if not self._elements:
                        storeSorted = True
                    else:
                        highestSortTuple = self._elements[-1].sortTuple()
                        thisSortTuple = list(element.sortTuple())
                        thisSortTuple[1] = offset
                        thisSortTuple = tuple(thisSortTuple)

                        if highestSortTuple < thisSortTuple:
                            storeSorted = True

        self.coreSetElementOffset(
            element,
            float(offset),  # why is this not opFrac?
            addElement=True,
            setActiveSite=setActiveSite
        )
        element.sites.add(self)
        # need to explicitly set the activeSite of the element
        # will be sorted later if necessary
        self._elements.append(element)
        # self._elementTree.insert(float(offset), element)
        return storeSorted

    def coreAppend(
        self,
        element: Music21Object,
        *,
        setActiveSite=True
    ):
        '''
        N.B. -- a "core" method, not to be used by general users.  Run .append() instead.

        Low level appending; like `coreInsert` does not error check,
        determine elements changed, or similar operations.

        When using this method, the caller is responsible for calling
        Stream.coreElementsChanged after all operations are completed.
        '''
        # NOTE: this is not called by append, as that is optimized
        # for looping multiple elements
        ht = self.highestTime
        self.coreSetElementOffset(element, ht, addElement=True)
        element.sites.add(self)
        # need to explicitly set the activeSite of the element
        if setActiveSite:
            self.coreSelfActiveSite(element)
        self._elements.append(element)

        # Make this faster
        # self._elementTree.insert(self.highestTime, element)
        # does not change sorted state
        self._setHighestTime(ht + element.duration.quarterLength)
    # --------------------------------------------------------------------------
    # adding and editing Elements and Streams -- all need to call coreElementsChanged
    # most will set isSorted to False

    def coreSetElementOffset(
        self,
        element: Music21Object,
        offset: Union[int, float, Fraction, str],
        *,
        addElement=False,
        setActiveSite=True
    ):
        '''
        Sets the Offset for an element, very quickly.
        Caller is responsible for calling :meth:`~music21.stream.core.coreElementsChanged`
        afterward.

        >>> s = stream.Stream()
        >>> s.id = 'Stream1'
        >>> n = note.Note('B-4')
        >>> s.insert(10, n)
        >>> n.offset
        10.0
        >>> s.coreSetElementOffset(n, 20.0)
        >>> n.offset
        20.0
        >>> n.getOffsetBySite(s)
        20.0
        '''
        # Note: not documenting 'highestTime' is on purpose, since can only be done for
        # elements already stored at end.  Infinite loop.
        try:
            offset = opFrac(offset)
        except TypeError:
            if offset not in OffsetSpecial:  # pragma: no cover
                raise StreamException(f'Cannot set offset to {offset!r} for {element}')

        idEl = id(element)
        if not addElement and idEl not in self._offsetDict:
            raise StreamException(
                f'Cannot set the offset for element {element}, not in Stream {self}.')
        self._offsetDict[idEl] = (offset, element)  # fast
        if setActiveSite:
            self.coreSelfActiveSite(element)

    def coreElementsChanged(
        self,
        *,
        updateIsFlat=True,
        clearIsSorted=True,
        memo=None,
        keepIndex=False,
    ):
        '''
        NB -- a "core" stream method that is not necessary for most users.

        This method is called automatically any time the elements in the Stream are changed.
        However, it may be called manually in case sites or other advanced features of an
        element have been modified.  It was previously a private method and for most users
        should still be treated as such.

        The various arguments permit optimizing the clearing of cached data in situations
        when completely dropping all cached data is excessive.

        >>> a = stream.Stream()
        >>> a.isFlat
        True

        Here we manipulate the private `._elements` storage (which generally shouldn't
        be done) using coreAppend and thus need to call `.coreElementsChanged` directly.

        >>> a.coreAppend(stream.Stream())
        >>> a.isFlat  # this is wrong.
        True

        >>> a.coreElementsChanged()
        >>> a.isFlat
        False
        '''
        # experimental
        if not self._mutable:
            raise ImmutableStreamException(
                'coreElementsChanged should not be triggered on an immutable stream'
            )

        if memo is None:
            memo = []

        if id(self) in memo:
            return
        memo.append(id(self))

        # WHY??? THIS SEEMS OVERKILL, esp. since the first call to .sort() in .flatten() will
        # invalidate it! TODO: Investigate if this is necessary and then remove if not necessary
        # should not need to do this...

        # if this Stream is a flat representation of something, and its
        # elements have changed, than we must clear the cache of that
        # ancestor so that subsequent calls get a new representation of this derivation;
        # we can do that by calling coreElementsChanged on
        # the derivation.origin
        if self._derivation is not None:
            sdm = self._derivation.method
            if sdm in ('flat', 'semiflat'):
                origin: 'music21.stream.Stream' = self._derivation.origin
                origin.clearCache()

        # may not always need to clear cache of all living sites, but may
        # always be a good idea since .flatten() has changed etc.
        # should not need to do derivation.origin sites.
        for livingSite in self.sites:
            livingSite.coreElementsChanged(memo=memo)

        # clear these attributes for setting later
        if clearIsSorted:
            self.isSorted = False

        if updateIsFlat:
            self.isFlat = True
            # do not need to look in _endElements
            for e in self._elements:
                # only need to find one case, and if so, no longer flat
                # fastest method here is isinstance()
                # if isinstance(e, Stream):
                if e.isStream:
                    self.isFlat = False
                    break
        # resetting the cache removes lowest and highest time storage
        # a slight performance optimization: not creating unless needed
        if self._cache:
            indexCache = None
            if keepIndex and 'index' in self._cache:
                indexCache = self._cache['index']
            # always clear cache when elements have changed
            # for instance, Duration will change.
            # noinspection PyAttributeOutsideInit
            self._cache = {}  # cannot call clearCache() because defined on Stream via Music21Object
            if keepIndex and indexCache is not None:
                self._cache['index'] = indexCache

    def coreCopyAsDerivation(self, methodName: str, *, recurse=True, deep=True):
        '''
        Make a copy of this stream with the proper derivation set.

        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> s.append(n)
        >>> s2 = s.coreCopyAsDerivation('exampleCopy')
        >>> s2.derivation.method
        'exampleCopy'
        >>> s2.derivation.origin is s
        True
        >>> s2[0].derivation.method
        'exampleCopy'
        '''
        if deep:
            post = copy.deepcopy(self)
        else:  # pragma: no cover
            post = copy.copy(self)
        post.derivation.method = methodName
        if recurse and deep:
            post.setDerivationMethod(methodName, recurse=True)
        return post

    def coreHasElementByMemoryLocation(self, objId: int) -> bool:
        '''
        NB -- a "core" stream method that is not necessary for most users. use hasElement(obj)

        Return True if an element object id, provided as an argument, is contained in this Stream.

        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> s.append(n1)
        >>> s.coreHasElementByMemoryLocation(id(n1))
        True
        >>> s.coreHasElementByMemoryLocation(id(n2))
        False
        '''
        if objId in self._offsetDict:
            return True

        for e in self._elements:
            if id(e) == objId:  # pragma: no cover
                return True
        for e in self._endElements:
            if id(e) == objId:  # pragma: no cover
                return True
        return False

    def coreGetElementByMemoryLocation(self, objId):
        '''
        NB -- a "core" stream method that is not necessary for most users.

        Low-level tool to get an element based only on the object id.

        This is not the same as getElementById, which refers to the id
        attribute which may be manually set and not unique.

        However, some implementations of python will reuse object locations, sometimes
        quickly, so don't keep these around.

        Used by spanner and variant.

        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> s.append(n1)
        >>> s.coreGetElementByMemoryLocation(id(n1)) is n1
        True
        >>> s.coreGetElementByMemoryLocation(id(n2)) is None
        True
        >>> b = bar.Barline()
        >>> s.storeAtEnd(b)
        >>> s.coreGetElementByMemoryLocation(id(b)) is b
        True
        '''
        # NOTE: this may be slightly faster than other approaches
        # as it does not sort.
        for e in self._elements:
            if id(e) == objId:
                return e
        for e in self._endElements:
            if id(e) == objId:
                return e
        return None

    # --------------------------------------------------------------------------
    def coreGuardBeforeAddElement(self, element, *, checkRedundancy=True):
        '''
        Before adding an element, this method performs
        important checks on that element.

        Used by:

          - :meth:`~music21.stream.Stream.insert`
          - :meth:`~music21.stream.Stream.append`
          - :meth:`~music21.stream.Stream.storeAtEnd`
          - `Stream.__init__()`

        Returns None or raises a StreamException

        >>> s = stream.Stream()
        >>> s.coreGuardBeforeAddElement(s)
        Traceback (most recent call last):
        music21.exceptions21.StreamException: this Stream cannot be contained within itself

        >>> s.append(s.iter())
        Traceback (most recent call last):
        music21.exceptions21.StreamException: cannot insert StreamIterator into a Stream
        Iterate over it instead (User's Guide chs. 6 and 26)

        >>> s.insert(4, 3.14159)
        Traceback (most recent call last):
        music21.exceptions21.StreamException: The object you tried to add to
        the Stream, 3.14159, is not a Music21Object.  Use an ElementWrapper
        object if this is what you intend.

        '''
        if element is self:  # cannot add this Stream into itself
            raise StreamException('this Stream cannot be contained within itself')
        if not isinstance(element, Music21Object):
            if isinstance(element, StreamIterator):
                raise StreamException(
                    'cannot insert StreamIterator into a Stream\n'
                    "Iterate over it instead (User's Guide chs. 6 and 26)")
            raise StreamException(
                f'The object you tried to add to the Stream, {element!r}, '
                + 'is not a Music21Object.  Use an ElementWrapper object '
                + 'if this is what you intend.')
        if checkRedundancy:
            # using id() here b/c we do not want to get __eq__ comparisons
            idElement = id(element)
            if idElement in self._offsetDict:
                # now go slow for safety -- maybe something is amiss in the index.
                # this should not happen, but we have slipped many times in not clearing out
                # old _offsetDict entries.
                for search_place in (self._elements, self._endElements):
                    for eInStream in search_place:
                        if eInStream is element:
                            raise StreamException(
                                f'the object ({element!r}, id()={id(element)} '
                                + f'is already found in this Stream ({self!r}, id()={id(self)})'
                            )
                # something was old... delete from _offsetDict
                # environLocal.warn('stale object')
                del self._offsetDict[idElement]  # pragma: no cover
        # if we do not purge locations here, we may have ids() for
        # Streams that no longer exist stored in the locations entry for element.
        # Note that dead locations are also purged from .sites during
        # all get() calls.
        element.purgeLocations()

    def coreStoreAtEnd(self, element, setActiveSite=True):
        '''
        NB -- this is a "core" method.  Use .storeAtEnd() instead.

        Core method for adding end elements.
        To be called by other methods.
        '''
        self.coreSetElementOffset(element, OffsetSpecial.AT_END, addElement=True)
        element.sites.add(self)
        # need to explicitly set the activeSite of the element
        if setActiveSite:
            self.coreSelfActiveSite(element)
        # self._elements.append(element)
        self._endElements.append(element)

    @property
    def spannerBundle(self):
        '''
        A low-level object for Spanner management. This is a read-only property.
        '''
        if 'spannerBundle' not in self._cache or self._cache['spannerBundle'] is None:
            spanners = self.recurse(classFilter=(spanner.Spanner,), restoreActiveSites=False)
            self._cache['spannerBundle'] = spanner.SpannerBundle(list(spanners))
        return self._cache['spannerBundle']

    def asTimespans(self, *, flatten=True, classList=None):
        r'''
        Convert stream to a :class:`~music21.tree.trees.TimespanTree` instance, a
        highly optimized data structure for searching through elements and
        offsets.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTimespans()
        >>> print(scoreTree)
        <TimespanTree {20} (0.0 to 8.0) <music21.stream.Score exampleScore>>
            <ElementTimespan (0.0 to 0.0) <music21.clef.BassClef>>
            <ElementTimespan (0.0 to 0.0) <music21.meter.TimeSignature 2/4>>
            <ElementTimespan (0.0 to 0.0) <music21.instrument.Instrument 'PartA: : '>>
            <ElementTimespan (0.0 to 0.0) <music21.clef.BassClef>>
            <ElementTimespan (0.0 to 0.0) <music21.meter.TimeSignature 2/4>>
            <ElementTimespan (0.0 to 0.0) <music21.instrument.Instrument 'PartB: : '>>
            <PitchedTimespan (0.0 to 1.0) <music21.note.Note C>>
            <PitchedTimespan (0.0 to 2.0) <music21.note.Note C#>>
            <PitchedTimespan (1.0 to 2.0) <music21.note.Note D>>
            <PitchedTimespan (2.0 to 3.0) <music21.note.Note E>>
            <PitchedTimespan (2.0 to 4.0) <music21.note.Note G#>>
            <PitchedTimespan (3.0 to 4.0) <music21.note.Note F>>
            <PitchedTimespan (4.0 to 5.0) <music21.note.Note G>>
            <PitchedTimespan (4.0 to 6.0) <music21.note.Note E#>>
            <PitchedTimespan (5.0 to 6.0) <music21.note.Note A>>
            <PitchedTimespan (6.0 to 7.0) <music21.note.Note B>>
            <PitchedTimespan (6.0 to 8.0) <music21.note.Note D#>>
            <PitchedTimespan (7.0 to 8.0) <music21.note.Note C>>
            <ElementTimespan (8.0 to 8.0) <music21.bar.Barline type=final>>
            <ElementTimespan (8.0 to 8.0) <music21.bar.Barline type=final>>
        '''
        hashedAttributes = hash((tuple(classList or ()), flatten))
        cacheKey = "timespanTree" + str(hashedAttributes)
        if cacheKey not in self._cache or self._cache[cacheKey] is None:
            hashedTimespanTree = tree.fromStream.asTimespans(self,
                                                             flatten=flatten,
                                                             classList=classList)
            self._cache[cacheKey] = hashedTimespanTree
        return self._cache[cacheKey]

    def coreSelfActiveSite(self, el):
        '''
        Set the activeSite of el to be self.

        Override for SpannerStorage, VariantStorage, which should never
        become the activeSite
        '''
        el.activeSite = self

    def asTree(self, *, flatten=False, classList=None, useTimespans=False, groupOffsets=False):
        '''
        Returns an elementTree of the score, using exact positioning.

        See tree.fromStream.asTree() for more details.

        >>> score = tree.makeExampleScore()
        >>> scoreTree = score.asTree(flatten=True)
        >>> scoreTree
        <ElementTree {20} (0.0 <0.-25...> to 8.0) <music21.stream.Score exampleScore>>
        '''
        hashedAttributes = hash((tuple(classList or ()),
                                  flatten,
                                  useTimespans,
                                  groupOffsets))
        cacheKey = "elementTree" + str(hashedAttributes)
        if cacheKey not in self._cache or self._cache[cacheKey] is None:
            hashedElementTree = tree.fromStream.asTree(self,
                                                       flatten=flatten,
                                                       classList=classList,
                                                       useTimespans=useTimespans,
                                                       groupOffsets=groupOffsets)
            self._cache[cacheKey] = hashedElementTree
        return self._cache[cacheKey]

    def coreGatherMissingSpanners(
        self,
        *,
        recurse=True,
        requireAllPresent=True,
        insert=True,
        constrainingSpannerBundle: Optional[spanner.SpannerBundle] = None
    ) -> Optional[List[spanner.Spanner]]:
        '''
        find all spanners that are referenced by elements in the
        (recursed if recurse=True) stream and either inserts them in the Stream
        (if insert is True) or returns them if insert is False.

        If requireAllPresent is True (default) then only those spanners whose complete
        spanned elements are in the Stream are returned.

        Because spanners are stored weakly in .sites this is only guaranteed to find
        the spanners in cases where the spanner is in another stream that is still active.

        Here's a little helper function since we'll make the same Stream several times,
        with two slurred notes, but without the slur itself.  Python's garbage collection
        will get rid of the slur if we do not prevent it

        >>> preventGarbageCollection = []
        >>> def getStream():
        ...    s = stream.Stream()
        ...    n = note.Note('C')
        ...    m = note.Note('D')
        ...    sl = spanner.Slur(n, m)
        ...    preventGarbageCollection.append(sl)
        ...    s.append([n, m])
        ...    return s

        Okay now we have a Stream with two slurred notes, but without the slur.
        `coreGatherMissingSpanners()` will put it in at the beginning.

        >>> s = getStream()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        >>> s.coreGatherMissingSpanners()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
        {1.0} <music21.note.Note D>

        Now, the same Stream, but insert is False, so it will return a list of
        Spanners that should be inserted, rather than inserting them.

        >>> s = getStream()
        >>> spList = s.coreGatherMissingSpanners(insert=False)
        >>> spList
        [<music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>]
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>


        Now we'll remove the second note so not all elements of the slur
        are present, which by default will not insert the Slur:

        >>> s = getStream()
        >>> s.remove(s[-1])
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        >>> s.coreGatherMissingSpanners()
        >>> s.show('text')
        {0.0} <music21.note.Note C>

        But with `requireAllPresent=False`, the spanner appears!

        >>> s.coreGatherMissingSpanners(requireAllPresent=False)
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>

        With `recurse=False`, then spanners are not gathered inside the inner
        stream:

        >>> t = stream.Part()
        >>> s = getStream()
        >>> t.insert(0, s)
        >>> t.coreGatherMissingSpanners(recurse=False)
        >>> t.show('text')
        {0.0} <music21.stream.Stream 0x104935b00>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>


        But the default acts with recursion:

        >>> t.coreGatherMissingSpanners()
        >>> t.show('text')
        {0.0} <music21.stream.Stream 0x104935b00>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>


        Spanners already in the stream are not put there again:

        >>> s = getStream()
        >>> sl = s.notes.first().getSpannerSites()[0]
        >>> sl
        <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
        >>> s.insert(0, sl)
        >>> s.coreGatherMissingSpanners()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
        {1.0} <music21.note.Note D>

        Also does not happen with recursion.

        >>> t = stream.Part()
        >>> s = getStream()
        >>> sl = s.notes.first().getSpannerSites()[0]
        >>> s.insert(0, sl)
        >>> t.insert(0, s)
        >>> t.coreGatherMissingSpanners()
        >>> t.show('text')
        {0.0} <music21.stream.Stream 0x104935b00>
            {0.0} <music21.note.Note C>
            {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
            {1.0} <music21.note.Note D>

        If `constrainingSpannerBundle` is set then only spanners also present in
        that spannerBundle are added.  This can be useful, for instance, in restoring
        spanners from an excerpt that might already have spanners removed.  In
        Jacob Tyler Walls's brilliant phrasing, it prevents regrowing zombie spanners
        that you thought you had killed.

        Here we will constrain only to spanners also present in another Stream:

        >>> s = getStream()
        >>> s2 = stream.Stream()
        >>> s.coreGatherMissingSpanners(constrainingSpannerBundle=s2.spannerBundle)
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>

        Now with the same constraint, but we will put the Slur into the other stream.

        >>> sl = s.notes.first().getSpannerSites()[0]
        >>> s2.insert(0, sl)
        >>> s.coreGatherMissingSpanners(constrainingSpannerBundle=s2.spannerBundle)
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
        {1.0} <music21.note.Note D>
        '''
        sb = self.spannerBundle
        if recurse is True:
            sIter = self.recurse()
        else:
            sIter = self.iter()

        collectList = []
        for el in list(sIter):
            for sp in el.getSpannerSites():
                if sp in sb:
                    continue
                if sp in collectList:
                    continue
                if constrainingSpannerBundle is not None and sp not in constrainingSpannerBundle:
                    continue
                if requireAllPresent:
                    allFound = True
                    for spannedElement in sp.getSpannedElements():
                        if spannedElement not in sIter:
                            allFound = False
                            break
                    if allFound is False:
                        continue
                collectList.append(sp)

        if insert is False:
            return collectList
        elif collectList:  # do not run elementsChanged if nothing here.
            for sp in collectList:
                self.coreInsert(0, sp)
            self.coreElementsChanged(updateIsFlat=False)

# timing before: Macbook Air 2012, i7
# In [3]: timeit('s = stream.Stream()', setup='from music21 import stream', number=100000)
# Out[3]: 1.6291376419831067

# after adding subclass -- actually faster, showing the rounding error:
# In [2]: timeit('s = stream.Stream()', setup='from music21 import stream', number=100000)
# Out[2]: 1.5247003990225494


class Test(unittest.TestCase):
    pass


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
