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
# pylint: disable=attribute-defined-outside-init

import unittest

from music21 import spanner
from music21 import tree
from music21.exceptions21 import StreamException, ImmutableStreamException


class StreamCoreMixin:
    def __init__(self):
        # hugely important -- keeps track of where the _elements are
        # the _offsetDict is a dictionary where id(element) is the
        # index and the index and the offset is the value.
        self._offsetDict = {}
        # self._elements stores Music21Object objects.
        self._elements = []

        # self._endElements stores Music21Objects found at
        # the highestTime of this Stream.
        self._endElements = []

        self.isSorted = True
        # v4!
        # self._elementTree = tree.trees.ElementTree(source=self)

    def coreInsert(self, offset, element,
                   *,
                   ignoreSort=False, setActiveSite=True
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

        self.setElementOffset(element, float(offset), addElement=True, setActiveSite=setActiveSite)
        element.sites.add(self)
        # need to explicitly set the activeSite of the element
        # will be sorted later if necessary
        self._elements.append(element)
        # self._elementTree.insert(float(offset), element)
        return storeSorted

    def coreAppend(self, element, setActiveSite=True):
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
        self.setElementOffset(element, ht, addElement=True)
        element.sites.add(self)
        # need to explicitly set the activeSite of the element
        if setActiveSite:
            self.coreSelfActiveSite(element)
        self._elements.append(element)

        # Make this faster
        # self._elementTree.insert(self.highestTime, element)
        # does not change sorted state
        if element.duration is not None:
            self._setHighestTime(ht + element.duration.quarterLength)
    # --------------------------------------------------------------------------
    # adding and editing Elements and Streams -- all need to call coreElementsChanged
    # most will set isSorted to False

    def coreElementsChanged(
            self,
            *,
            updateIsFlat=True,
            clearIsSorted=True,
            memo=None,
            keepIndex=False):
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
        be done) and thus need to call `.coreElementsChanged` directly.

        >>> a._elements.append(stream.Stream())
        >>> a.isFlat  # this is wrong.
        True

        >>> a.coreElementsChanged()
        >>> a.isFlat
        False
        '''
        # experimental
        if not self._mutable:
            raise ImmutableStreamException(
                '_coreElementsChanged should not be triggered on an immutable stream'
            )

        if memo is None:
            memo = []
        memo.append(id(self))

        # WHY??? THIS SEEMS OVERKILL, esp. since the first call to .sort() in .flat will
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
                origin = self._derivation.origin
                if sdm in origin._cache and origin._cache[sdm] is self:
                    del origin._cache[sdm]

        # may not always need to clear cache of all living sites, but may
        # always be a good idea since .flat has changed etc.
        # should not need to do derivation.origin sites.
        for livingSite in self.sites:
            livingSite.coreElementsChanged()

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
            self._cache = {}
            if keepIndex and indexCache is not None:
                self._cache['index'] = indexCache

    def coreHasElementByMemoryLocation(self, objId):
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
        Before adding an element, this method provides
        important checks to that element.

        Used by both insert() and append()

        Returns None or raises a StreamException

        >>> s = stream.Stream()
        >>> s.coreGuardBeforeAddElement(s)
        Traceback (most recent call last):
        music21.exceptions21.StreamException: this Stream cannot be contained within itself
        '''
        # using id() here b/c we do not want to get __eq__ comparisons
        if element is self:  # cannot add this Stream into itself
            raise StreamException('this Stream cannot be contained within itself')
        if checkRedundancy:
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
        self.setElementOffset(element, 'highestTime', addElement=True)
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
            sf = self.flat
            sp = sf.spanners.stream()
            self._cache['spannerBundle'] = spanner.SpannerBundle(sp)
        return self._cache['spannerBundle']

    def asTimespans(self, classList=None, flatten=True):
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

    def asTree(self, flatten=False, classList=None, useTimespans=False, groupOffsets=False):
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

    def coreGatherMissingSpanners(self, recurse=True, requireAllPresent=True, insert=True):
        '''
        find all spanners that are referenced by elements in the
        (recursed if recurse=True) stream and either inserts them in the Stream
        (if insert is True) or returns them if insert is False.

        If requireAllPresent is True (default) then only those spanners whose complete
        spanned elements are in the Stream are returned.

        Because spanners are stored weakly in .sites this is only guaranteed to find
        the spanners in cases where the spanner is in another stream that is still active.

        Here's a little helper function since we'll make the same Stream several times:

        >>> def getStream():
        ...    s = stream.Stream()
        ...    n = note.Note('C')
        ...    m = note.Note('D')
        ...    sl = spanner.Slur(n, m)
        ...    n.bogusAttributeNotWeakref = sl  # prevent garbage collecting sl
        ...    s.append([n, m])
        ...    return s



        >>> s = getStream()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        >>> s.coreGatherMissingSpanners()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
        {1.0} <music21.note.Note D>

        Insert is False:

        >>> s = getStream()
        >>> spList = s.coreGatherMissingSpanners(insert=False)
        >>> spList
        [<music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>]
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>

        Not all elements are present:

        >>> s = getStream()
        >>> s.remove(s[-1])
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        >>> s.coreGatherMissingSpanners()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        >>> s.coreGatherMissingSpanners(requireAllPresent=False)
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>

        Test recursion:

        >>> t = stream.Part()
        >>> s = getStream()
        >>> t.insert(0, s)
        >>> t.coreGatherMissingSpanners(recurse=False)
        >>> t.show('text')
        {0.0} <music21.stream.Stream 0x104935b00>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>

        Default: with recursion:

        >>> t.coreGatherMissingSpanners()
        >>> t.show('text')
        {0.0} <music21.stream.Stream 0x104935b00>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>


        Make sure that spanners already in the stream are not put there twice:

        >>> s = getStream()
        >>> sl = s[0].getSpannerSites()[0]
        >>> s.insert(0, sl)
        >>> s.coreGatherMissingSpanners()
        >>> s.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
        {1.0} <music21.note.Note D>

        And with recursion?

        >>> t = stream.Part()
        >>> s = getStream()
        >>> sl = s[0].getSpannerSites()[0]
        >>> s.insert(0, sl)
        >>> t.insert(0, s)
        >>> t.coreGatherMissingSpanners()
        >>> t.show('text')
        {0.0} <music21.stream.Stream 0x104935b00>
            {0.0} <music21.note.Note C>
            {0.0} <music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>
            {1.0} <music21.note.Note D>
        '''
        sb = self.spannerBundle
        if recurse is True:
            sIter = self.recurse()
        else:
            sIter = self.iter

        collectList = []
        for el in list(sIter):
            for sp in el.getSpannerSites():
                if sp in sb:
                    continue
                if sp in collectList:
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
        else:
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
