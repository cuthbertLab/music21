# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/base.py
# Purpose:      base classes for dealing with groups of positioned objects
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#               Josiah Wolf Oberholtzer
#               Evan Lynch
#
# Copyright:    Copyright © 2008-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The :class:`~music21.stream.Stream` and its subclasses
(which are themselves subclasses of the :class:`~music21.base.Music21Object`)
are the fundamental containers of offset-positioned notation and
musical elements in music21. Common Stream subclasses, such
as the :class:`~music21.stream.Measure`, :class:`~music21.stream.Part`
and :class:`~music21.stream.Score` objects, are also in this module.
'''
from __future__ import annotations

from collections import deque, namedtuple, OrderedDict
from collections.abc import Collection, Iterable, Sequence
import copy
from fractions import Fraction
import itertools
import math
from math import isclose
import os
import pathlib
import types
import typing as t
from typing import overload  # pycharm bug disallows alias
import unittest
import warnings

from music21 import base
from music21 import bar
from music21 import common
from music21.common.enums import GatherSpanners, OffsetSpecial
from music21.common.numberTools import opFrac
from music21.common.types import StreamType, M21ObjType, OffsetQL, OffsetQLSpecial
from music21 import clef
from music21 import chord
from music21 import defaults
from music21 import derivation
from music21 import duration
from music21 import environment
from music21 import exceptions21
from music21 import interval
from music21 import instrument
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import tie
from music21 import repeat
from music21 import sites
from music21 import style
from music21 import tempo

from music21.stream import core
from music21.stream import makeNotation
from music21.stream import streamStatus
from music21.stream import iterator
from music21.stream import filters
from music21.stream.enums import GivenElementsBehavior, RecursionType, ShowNumber


if t.TYPE_CHECKING:
    from music21 import spanner


environLocal = environment.Environment('stream')

StreamException = exceptions21.StreamException
ImmutableStreamException = exceptions21.ImmutableStreamException

T = t.TypeVar('T')
# we sometimes need to return a different type.
ChangedM21ObjType = t.TypeVar('ChangedM21ObjType', bound=base.Music21Object)
RecursiveLyricList = note.Lyric | None | list['RecursiveLyricList']

BestQuantizationMatch = namedtuple(
    'BestQuantizationMatch',
    ['remainingGap', 'error', 'tick', 'match', 'signedError', 'divisor']
)

class StreamDeprecationWarning(UserWarning):
    # Do not subclass Deprecation warning, because these
    # warnings need to be passed to users...
    pass


# -----------------------------------------------------------------------------
# Metaclass
OffsetMap = namedtuple('OffsetMap', ['element', 'offset', 'endTime', 'voiceIndex'])


# -----------------------------------------------------------------------------
class Stream(core.StreamCore, t.Generic[M21ObjType]):
    '''
    This is the fundamental container for Music21Objects;
    objects may be ordered and/or placed in time based on
    offsets from the start of this container.

    As a subclass of Music21Object, Streams have offsets,
    priority, id, and groups.

    Streams may be embedded within other Streams. As each
    Stream can have its own offset, when Streams are
    embedded the offset of an element is relatively only
    to its parent Stream. The :meth:`~music21.stream.Stream.flatten`
    and method provides access to a flat version of all
    embedded Streams, with offsets relative to the
    top-level Stream.

    The Stream :attr:`~music21.stream.Stream.elements` attribute
    returns the contents of the Stream as a list. Direct access
    to, and manipulation of, the elements list is not recommended.
    Instead, use the host of high-level methods available.

    The Stream, like all Music21Objects, has a
    :class:`music21.duration.Duration` that is usually the
    "release" time of the chronologically last element in the Stream
    (that is, the highest onset plus the duration of
    any element in the Stream).
    The duration, however, can be "unlinked" and explicitly
    set independent of the Stream's contents.

    The first element passed to the Stream is an optional single
    Music21Object or a list, tuple, or other Stream of Music21Objects
    which is used to populate the Stream by inserting each object at
    its :attr:`~music21.base.Music21Object.offset`
    property. One special case is when every such object, such as a newly created
    one, has no offset. Then, so long as the entire list is not composed of
    non-Measure Stream subclasses representing synchrony like Parts or Voices,
    each element is appended, creating a sequence of elements in time,
    rather than synchrony.

    Other arguments and keywords are ignored, but are
    allowed so that subclassing the Stream is easier.

    >>> s1 = stream.Stream()
    >>> s1.append(note.Note('C#4', type='half'))
    >>> s1.append(note.Note('D5', type='quarter'))
    >>> s1.duration.quarterLength
    3.0
    >>> for thisNote in s1.notes:
    ...     print(thisNote.octave)
    ...
    4
    5

    This is a demonstration of creating a Stream with other elements,
    including embedded Streams (in this case, :class:`music21.stream.Part`,
    a Stream subclass):

    >>> c1 = clef.TrebleClef()
    >>> c1.offset = 0.0
    >>> c1.priority = -1
    >>> n1 = note.Note('E-6', type='eighth')
    >>> n1.offset = 1.0
    >>> p1 = stream.Part()
    >>> p1.offset = 0.0
    >>> p1.id = 'embeddedPart'
    >>> p1.append(note.Rest())  # quarter rest
    >>> s2 = stream.Stream([c1, n1, p1])
    >>> s2.duration.quarterLength
    1.5
    >>> s2.show('text')
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.stream.Part embeddedPart>
        {0.0} <music21.note.Rest quarter>
    {1.0} <music21.note.Note E->

    * New in v7: providing a single element now works:

    >>> s = stream.Stream(meter.TimeSignature())
    >>> s.first()
    <music21.meter.TimeSignature 4/4>

    Providing a list of objects or Measures or Scores (but not other Stream
    subclasses such as Parts or Voices) positions sequentially, i.e. appends, if they
    all have offset 0.0 currently:

    >>> s2 = stream.Measure([note.Note(), note.Note(), bar.Barline()])
    >>> s2.show('text')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C>
    {2.0} <music21.bar.Barline type=regular>

    A list of measures will thus each be appended:

    >>> m1 = stream.Measure(n1, number=1)
    >>> m2 = stream.Measure(note.Rest(), number=2)
    >>> s3 = stream.Part([m1, m2])
    >>> s3.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {1.0} <music21.note.Note E->
    {1.5} <music21.stream.Measure 2 offset=1.5>
        {0.0} <music21.note.Rest quarter>

    Here, every element is a Stream that's not a Measure (or Score), so it
    will be inserted at 0.0, rather than appending:

    >>> s4 = stream.Score([stream.PartStaff(n1), stream.PartStaff(note.Rest())])
    >>> s4.show('text')
    {0.0} <music21.stream.PartStaff 0x...>
        {1.0} <music21.note.Note E->
    {0.0} <music21.stream.PartStaff 0x...>
        {0.0} <music21.note.Rest quarter>

    Create nested streams in one fell swoop:

    >>> s5 = stream.Score(stream.Part(stream.Measure(chord.Chord('C2 A2'))))
    >>> s5.show('text')
    {0.0} <music21.stream.Part 0x...>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.chord.Chord C2 A2>

    This behavior can be modified by the `givenElementsBehavior` keyword to go against the norm
    of 'OFFSETS':

    >>> from music21.stream.enums import GivenElementsBehavior
    >>> s6 = stream.Stream([note.Note('C'), note.Note('D')],
    ...                    givenElementsBehavior=GivenElementsBehavior.INSERT)
    >>> s6.show('text')  # all notes at offset 0.0
    {0.0} <music21.note.Note C>
    {0.0} <music21.note.Note D>

    >>> p1 = stream.Part(stream.Measure(note.Note('C')), id='p1')
    >>> p2 = stream.Part(stream.Measure(note.Note('D')), id='p2')
    >>> s7 = stream.Score([p1, p2],
    ...                   givenElementsBehavior=GivenElementsBehavior.APPEND)
    >>> s7.show('text')  # parts following each other (not recommended)
    {0.0} <music21.stream.Part p1>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note C>
    {1.0} <music21.stream.Part p2>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note D>

    For developers of subclasses, please note that because of how Streams
    are copied, there cannot be
    required parameters (i.e., without defaults) in initialization.
    For instance, this would not
    be allowed, because craziness and givenElements are required::

        class CrazyStream(Stream):
            def __init__(self, givenElements, craziness, **keywords):
                ...

    * New in v7: smart appending
    * New in v8: givenElementsBehavior keyword configures the smart appending.
    '''
    # this static attributes offer a performance boost over other
    # forms of checking class
    isStream = True
    isMeasure = False
    classSortOrder: int | float = -20
    recursionType: RecursionType = RecursionType.ELEMENTS_FIRST

    _styleClass = style.StreamStyle

    # define order of presenting names in documentation; use strings
    _DOC_ORDER = ['append', 'insert', 'storeAtEnd', 'insertAndShift',
                  'recurse', 'flat',
                  'notes', 'pitches',
                  'transpose',
                  'augmentOrDiminish', 'scaleOffsets', 'scaleDurations']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR: dict[str, str] = {
        'recursionType': '''
            Class variable:

            RecursionType Enum of (ELEMENTS_FIRST (default), FLATTEN, ELEMENTS_ONLY)
            that decides whether the stream likely holds relevant
            contexts for the elements in it.

            Define this for a stream class, not an individual object.

            see :meth:`~music21.base.Music21Object.contextSites`
            ''',
        'isSorted': '''
            Boolean describing whether the Stream is sorted or not.
            ''',
        'autoSort': '''
            Boolean describing whether the Stream is automatically sorted by
            offset whenever necessary.
            ''',
        'isFlat': '''
            Boolean describing whether this Stream contains embedded
            sub-Streams or Stream subclasses (not flat).
            ''',
        'definesExplicitSystemBreaks': '''
            Boolean that says whether all system breaks in the piece are
            explicitly defined.  Only used on musicxml output (maps to the
            musicxml <supports attribute="new-system"> tag) and only if this is
            the outermost Stream being shown
            ''',
        'definesExplicitPageBreaks': '''
            Boolean that says whether all page breaks in the piece are
            explicitly defined.  Only used on musicxml output (maps to the
            musicxml <supports attribute="new-page"> tag) and only if this is
            the outermost Stream being shown.
            ''',
        # 'restrictClass': '''
        #     All elements in the stream are required to be of this class
        #     or a subclass of that class.  Currently not enforced.  Used
        #     for type-checking.
        #     ''',
    }
    def __init__(self,
                 givenElements: t.Union[None,
                                        base.Music21Object,
                                        Sequence[base.Music21Object]] = None,
                 *,
                 givenElementsBehavior: GivenElementsBehavior = GivenElementsBehavior.OFFSETS,
                 **keywords):
        # restrictClass: type[M21ObjType] = base.Music21Object,
        super().__init__(**keywords)

        # TEMPORARY variable for v9 to deprecate the flat property. -- remove in v10
        self._created_via_deprecated_flat = False

        self.streamStatus = streamStatus.StreamStatus(self)
        self._unlinkedDuration = None

        self.autoSort = True

        # # all elements in the stream need to be of this class.
        # self.restrictClass = restrictClass

        # these should become part of style or something else...
        self.definesExplicitSystemBreaks = False
        self.definesExplicitPageBreaks = False

        # property for transposition status;
        self._atSoundingPitch: bool | t.Literal['unknown'] = 'unknown'

        # experimental
        self._mutable = True

        if givenElements is None:
            return

        if isinstance(givenElements, base.Music21Object):
            givenElements = t.cast(list[base.Music21Object], [givenElements])

        # Append rather than insert if every offset is 0.0
        # but not if every element is a stream subclass other than a Measure or Score
        # (i.e. Part or Voice generally, but even Opus theoretically)
        # because these classes usually represent synchrony
        appendBool = True
        if givenElementsBehavior == GivenElementsBehavior.OFFSETS:
            try:
                appendBool = all(e.offset == 0.0 for e in givenElements)
            except AttributeError:
                pass  # appropriate failure will be raised by coreGuardBeforeAddElement()
            if appendBool and all(
                    (e.isStream and e.classSet.isdisjoint((Measure, Score)))
                    for e in givenElements):
                appendBool = False
        elif givenElementsBehavior == GivenElementsBehavior.INSERT:
            appendBool = False
        else:
            appendBool = True

        for e in givenElements:
            self.coreGuardBeforeAddElement(e)
            if appendBool:
                self.coreAppend(e)
            else:
                self.coreInsert(e.offset, e)

        self.coreElementsChanged()

    def __eq__(self, other):
        '''
        No two streams are ever equal unless they are the same Stream
        '''
        return self is other

    def __hash__(self) -> int:
        return id(self) >> 4

    def _reprInternal(self) -> str:
        if self.id is not None:
            if self.id != id(self) and str(self.id) != str(id(self)):
                return str(self.id)
            elif isinstance(self.id, int):
                return hex(self.id)
            else:  # pragma: no cover
                return ''
        else:  # pragma: no cover
            return ''

    def write(self, fmt=None, fp=None, **keywords):
        # ...    --- see base.py calls .write(
        if self.isSorted is False and self.autoSort:  # pragma: no cover
            self.sort()
        return super().write(fmt=fmt, fp=fp, **keywords)

    def show(self, fmt=None, app=None, **keywords):
        # ...    --- see base.py calls .write(
        if self.isSorted is False and self.autoSort:
            self.sort()
        return super().show(fmt=fmt, app=app, **keywords)

    # --------------------------------------------------------------------------
    # sequence like operations

    def __len__(self) -> int:
        '''
        Get the total number of elements in the Stream.
        This method does not recurse into and count elements in contained Streams.

        >>> import copy
        >>> a = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> len(a)
        4

        >>> b = stream.Stream()
        >>> for x in range(4):
        ...     b.insert(copy.deepcopy(a))  # append streams
        >>> len(b)
        4
        >>> len(b.flatten())
        16

        Includes end elements:

        >>> b.storeAtEnd(bar.Barline('double'))
        >>> len(b)
        5
        '''
        return len(self._elements) + len(self._endElements)

    def __iter__(self) -> iterator.StreamIterator[M21ObjType]:
        '''
        The Stream iterator, used in all for
        loops and similar iteration routines. This method returns the
        specialized :class:`music21.stream.StreamIterator` class, which
        adds necessary Stream-specific features.
        '''
        # temporary for v9 -- remove in v10
        if self._created_via_deprecated_flat:
            warnings.warn('.flat is deprecated.  Call .flatten() instead',
                          exceptions21.Music21DeprecationWarning,
                          stacklevel=3)
            self._created_via_deprecated_flat = False

        return t.cast(iterator.StreamIterator[M21ObjType],
                      iterator.StreamIterator(self))

    def iter(self) -> iterator.StreamIterator[M21ObjType]:
        '''
        The Stream iterator, used in all for
        loops and similar iteration routines. This method returns the
        specialized :class:`music21.stream.StreamIterator` class, which
        adds necessary Stream-specific features.

        Generally you don't need this, just iterate over a stream, but it is necessary
        to add custom filters to an iterative search before iterating.
        '''
        # Pycharm wasn't inferring typing correctly with `return iter(self)`.
        return self.__iter__()  # pylint: disable=unnecessary-dunder-call

    @overload
    def __getitem__(self, k: str) -> iterator.RecursiveIterator[M21ObjType]:
        # Remove this code and replace with ... once Astroid #1015 is fixed.
        x: iterator.RecursiveIterator[M21ObjType] = self.recurse()
        return x

    @overload
    def __getitem__(self, k: int) -> M21ObjType:
        return self[k]  # dummy code

    @overload
    def __getitem__(self, k: slice) -> list[M21ObjType]:
        return list(self.elements)  # dummy code

    @overload
    def __getitem__(
        self,
        k: type[ChangedM21ObjType]
    ) -> iterator.RecursiveIterator[ChangedM21ObjType]:
        x = t.cast(iterator.RecursiveIterator[ChangedM21ObjType], self.recurse())
        return x  # dummy code

    @overload
    def __getitem__(
        self,
        k: type  # getting something that is a subclass of something that is not a m21 object
    ) -> iterator.RecursiveIterator[M21ObjType]:
        x = t.cast(iterator.RecursiveIterator[M21ObjType], self.recurse())
        return x  # dummy code


    @overload
    def __getitem__(
        self,
        k: Collection[type]
    ) -> iterator.RecursiveIterator[M21ObjType]:
        # Remove this code and replace with ... once Astroid #1015 is fixed.
        x: iterator.RecursiveIterator[M21ObjType] = self.recurse()
        return x


    def __getitem__(self,
                    k: t.Union[str,
                               int,
                               slice,
                               type[ChangedM21ObjType],
                               Collection[type]]
                    ) -> t.Union[iterator.RecursiveIterator[M21ObjType],
                                 iterator.RecursiveIterator[ChangedM21ObjType],
                                 M21ObjType,
                                 list[M21ObjType]]:
        '''
        Get a Music21Object from the Stream using a variety of keys or indices.

        If an int is given, the Music21Object at the index is returned, as if it were a list
        or tuple:

        >>> c = note.Note('C')
        >>> d = note.Note('D')
        >>> e = note.Note('E')
        >>> r1 = note.Rest()
        >>> f = note.Note('F')
        >>> g = note.Note('G')
        >>> r2 = note.Rest()
        >>> a = note.Note('A')
        >>> s = stream.Stream([c, d, e, r1, f, g, r2, a])

        >>> s[0]
        <music21.note.Note C>
        >>> s[-1]
        <music21.note.Note A>

        Out of range notes raise an IndexError:

        >>> s[99]
        Traceback (most recent call last):
        IndexError: attempting to access index 99 while elements is of size 8

        If a slice of indices is given, a list of elements is returned, as if the Stream
        were a list or Tuple.

        >>> subslice = s[2:5]
        >>> subslice
        [<music21.note.Note E>, <music21.note.Rest quarter>, <music21.note.Note F>]
        >>> len(subslice)
        3
        >>> s[1].offset
        1.0
        >>> subslice[1].offset
        3.0


        If a class is given, then a :class:`~music21.stream.iterator.RecursiveIterator`
        of elements matching the requested class is returned, similar
        to `Stream().recurse().getElementsByClass()`.

        >>> len(s)
        8
        >>> len(s[note.Rest])
        2
        >>> len(s[note.Note])
        6

        >>> for n in s[note.Note]:
        ...     print(n.name, end=' ')
        C D E F G A

        Note that this iterator is recursive: it will find elements inside of streams
        within this stream:

        >>> c_sharp = note.Note('C#')
        >>> v = stream.Voice()
        >>> v.insert(0, c_sharp)
        >>> s.insert(0.5, v)
        >>> len(s[note.Note])
        7

        When using a single Music21 class in this way, your type checker will
        be able to infer that the only objects in any loop are in fact `note.Note`
        objects, and catch programming errors before running.

        Multiple classes can be provided, separated by commas. Any element matching
        any of the requested classes will be matched.

        >>> len(s[note.Note, note.Rest])
        9

        >>> for note_or_rest in s[note.Note, note.Rest]:
        ...     if isinstance(note_or_rest, note.Note):
        ...         print(note_or_rest.name, end=' ')
        ...     else:
        ...         print('Rest', end=' ')
        C C# D E Rest F G Rest A

        The actual object returned by `s[module.Class]` is a
        :class:`~music21.stream.iterator.RecursiveIterator` and has all the functions
        available on it:

        >>> s[note.Note]
        <...>

        If no elements of the class are found, no error is raised in version 7:

        >>> list(s[layout.StaffLayout])
        []


        If the key is a string, it is treated as a `querySelector` as defined in
        :meth:`~music21.stream.iterator.getElementsByQuerySelector`, namely that bare strings
        are treated as class names, strings beginning with `#` are id-queries, and strings
        beginning with `.` are group queries.

        We can set some ids and groups for demonstrating.

        >>> a.id = 'last_a'
        >>> c.groups.append('ghost')
        >>> e.groups.append('ghost')

        '.ghost', because it begins with `.`, is treated as a class name and
        returns a `RecursiveIterator`:

        >>> for n in s['.ghost']:
        ...     print(n.name, end=' ')
        C E

        A query selector with a `#` returns the single element matching that
        element or returns None if there is no match:

        >>> s['#last_a']
        <music21.note.Note A>

        >>> s['#nothing'] is None
        True

        Any other query raises a TypeError:

        >>> s[0.5]
        Traceback (most recent call last):
        TypeError: Streams can get items by int, slice, class, class iterable, or string query;
           got <class 'float'>

        * Changed in v7:
          - out of range indexes now raise an IndexError, not StreamException
          - strings ('music21.note.Note', '#id', '.group') are now treated like a query selector.
          - slices with negative indices now supported
          - Unsupported types now raise TypeError
          - Class and Group searches now return a recursive `StreamIterator` rather than a `Stream`
          - Slice searches now return a list of elements rather than a `Stream`

        * Changed in v8:
          - for strings: only fully-qualified names such as "music21.note.Note" or
          partially-qualified names such as "note.Note" are
          supported as class names.  Better to use a literal type or explicitly call
          .recurse().getElementsByClass to get the earlier behavior.  Old behavior
          still works until v9.  This is an attempt to unify __getitem__ behavior in
          StreamIterators and Streams.
          - allowed iterables of qualified class names, e.g. `[note.Note, note.Rest]`

        '''
        # need to sort if not sorted, as this call may rely on index positions
        if not self.isSorted and self.autoSort:
            self.sort()  # will set isSorted to True

        if isinstance(k, int):
            match = None
            # handle easy and most common case first
            if 0 <= k < len(self._elements):
                match = self._elements[k]
            # if using negative indices, or trying to access end elements,
            # then need to use .elements property
            else:
                try:
                    match = self.elements[k]
                except IndexError:
                    raise IndexError(
                        f'attempting to access index {k} '
                        + f'while elements is of size {len(self.elements)}'
                    )
            # setting active site as cautionary measure
            self.coreSelfActiveSite(match)
            return t.cast(M21ObjType, match)

        elif isinstance(k, slice):  # get a slice of index values
            # manually inserting elements is critical to setting the element
            # locations
            searchElements: list[base.Music21Object] = self._elements
            if (k.start is not None and k.start < 0) or (k.stop is not None and k.stop < 0):
                # Must use .elements property to incorporate end elements
                searchElements = list(self.elements)

            return t.cast(M21ObjType, searchElements[k])

        elif isinstance(k, type):
            if issubclass(k, base.Music21Object):
                return self.recurse().getElementsByClass(k)
            else:
                # this is explicitly NOT true, but we're pretending
                # it is a Music21Object for now, because the only things returnable
                # from getElementsByClass are Music21Objects that also inherit from k.
                m21Type = t.cast(type[M21ObjType], k)  # type: ignore
                return self.recurse().getElementsByClass(m21Type)

        elif common.isIterable(k) and all(isinstance(maybe_type, type) for maybe_type in k):
            return self.recurse().getElementsByClass(k)

        elif isinstance(k, str):
            querySelectorIterator = self.recurse().getElementsByQuerySelector(k)
            if '#' in k:
                # an id anywhere in the query selector should return only one element
                return querySelectorIterator.first()
            else:
                return querySelectorIterator

        raise TypeError(
            'Streams can get items by int, slice, class, class iterable, or string query; '
            f'got {type(k)}'
        )

    def first(self) -> M21ObjType | None:
        '''
        Return the first element of a Stream.  (Added for compatibility with StreamIterator)
        Or None if the Stream is empty.

        Unlike s.iter().first(), which is a significant performance gain, s.first() is the
        same speed as s[0], except for not raising an IndexError.

        >>> nC = note.Note('C4')
        >>> nD = note.Note('D4')
        >>> s = stream.Stream()
        >>> s.append([nC, nD])
        >>> s.first()
        <music21.note.Note C>

        >>> empty = stream.Stream()
        >>> print(empty.first())
        None

        * New in v7.
        '''
        try:
            return self[0]
        except IndexError:
            return None

    def last(self) -> M21ObjType | None:
        '''
        Return the last element of a Stream.  (Added for compatibility with StreamIterator)
        Or None if the Stream is empty.

        s.last() is the same speed as s[-1], except for not raising an IndexError.

        >>> nC = note.Note('C4')
        >>> nD = note.Note('D4')
        >>> s = stream.Stream()
        >>> s.append([nC, nD])
        >>> s.last()
        <music21.note.Note D>

        >>> empty = stream.Stream()
        >>> print(empty.last())
        None

        * New in v7.
        '''
        try:
            return self[-1]
        except IndexError:
            return None

    def __contains__(self, el):
        '''
        Returns True if `el` is in the stream (compared with Identity) and False otherwise.

        >>> nC = note.Note('C4')
        >>> nD = note.Note('D4')
        >>> s = stream.Stream()
        >>> s.append(nC)
        >>> nC in s
        True
        >>> nD in s
        False

        Note that we match on actual `id()` equality (`x is y`) and not on
        `==` equality.

        >>> nC2 = note.Note('C4')
        >>> nC == nC2
        True
        >>> nC2 in s
        False

        To get the latter, compare on `.elements` which uses Python's
        default `__contains__` for tuples.

        >>> nC2 in s.elements
        True
        '''
        return (any(sEl is el for sEl in self._elements)
                or any(sEl is el for sEl in self._endElements))

    @property
    def elements(self) -> tuple[M21ObjType, ...]:
        '''
        .elements is a Tuple representing the elements contained in the Stream.

        Directly getting, setting, and manipulating this Tuple is
        reserved for advanced usage. Instead, use the
        provided high-level methods.  The elements retrieved here may not
        have this stream as an activeSite, therefore they might not be properly ordered.

        In other words:  Don't use unless you really know what you're doing.
        Treat a Stream like a list!

        See how these are equivalent:

        >>> m = stream.Measure([note.Note('F4'), note.Note('G4')])
        >>> m.elements
        (<music21.note.Note F>, <music21.note.Note G>)
        >>> tuple(m)
        (<music21.note.Note F>, <music21.note.Note G>)

        When setting .elements, a list of Music21Objects can be provided, or a complete Stream.
        If a complete Stream is provided, elements are extracted
        from that Stream. This has the advantage of transferring
        offset correctly and getting elements stored at the end.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note('C'), list(range(10)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note('D'), list(range(10)))
        >>> b.offset = 6
        >>> c = stream.Stream()
        >>> c.repeatInsert(note.Note('E'), list(range(10)))
        >>> c.offset = 12
        >>> b.insert(c)
        >>> b.isFlat
        False

        >>> a.isFlat
        True

        Assigning from a Stream works well, and is actually much safer than assigning
        from `.elements` of the other Stream, since the active sites may have changed
        of that stream's elements in the meantime.

        >>> a.elements = b
        >>> a.isFlat
        False

        >>> len(a.recurse().notes) == len(b.recurse().notes) == 20
        True

        There is one good use for .elements as opposed to treating a Stream like a list,
        and that is that `in` for Streams compares on object identity, i.e.,
        id(a) == id(b) [this is for historical reasons], while since `.elements`
        is a tuple.  Recall our measure with the notes F4 and G4 above.

        >>> other_g = note.Note('G4')

        This new G can't be found in m, because it is not physically in the Measure

        >>> other_g in m
        False

        But it is *equal* to something in the Measure:

        >>> other_g in m.elements
        True

        But again, this could be done simply with:

        >>> other_g in tuple(m)
        True

        One reason to use `.elements` is to iterate quickly without setting
        activeSite:

        >>> n = note.Note()
        >>> m1 = stream.Measure([n])
        >>> m2 = stream.Measure([n])
        >>> n.activeSite is m2
        True
        >>> for el in m1.elements:
        ...     pass
        >>> n.activeSite is m2
        True
        >>> for el in m1:
        ...     pass
        >>> n.activeSite is m1
        True
        '''
        # combines _elements and _endElements into one.
        if 'elements' not in self._cache or self._cache['elements'] is None:
            # this list concatenation may take time; thus, only do when
            # coreElementsChanged has been called
            if not self.isSorted and self.autoSort:
                self.sort()  # will set isSorted to True
            self._cache['elements'] = t.cast(list[M21ObjType], self._elements + self._endElements)
        return tuple(self._cache['elements'])

    @elements.setter
    def elements(self, value: Stream | Iterable[base.Music21Object]):
        '''
        Sets this stream's elements to the elements in another stream (just give
        the stream, not the stream's .elements), or to a list of elements.

        Safe:

        newStream.elements = oldStream

        Unsafe:

        newStream.elements = oldStream.elements

        Why?

        The activeSites of some elements may have changed between retrieving
        and setting (esp. if a lot else has happened in the meantime). Where
        are we going to get the new stream's elements' offsets from? why
        from their active sites! So don't do this!
        '''
        self._offsetDict: dict[int, tuple[OffsetQLSpecial, base.Music21Object]] = {}
        if isinstance(value, Stream):
            # set from a Stream. Best way to do it
            self._elements: list[base.Music21Object] = list(value._elements)  # copy list.
            for e in self._elements:
                self.coreSetElementOffset(e, value.elementOffset(e), addElement=True)
                e.sites.add(self)
                self.coreSelfActiveSite(e)
            self._endElements: list[base.Music21Object] = list(value._endElements)
            for e in self._endElements:
                self.coreSetElementOffset(e,
                                      value.elementOffset(e, returnSpecial=True),
                                      addElement=True)
                e.sites.add(self)
                self.coreSelfActiveSite(e)
        else:
            # replace the complete elements list
            self._elements = list(value)
            self._endElements = []
            for e in self._elements:
                self.coreSetElementOffset(e, e.offset, addElement=True)
                e.sites.add(self)
                self.coreSelfActiveSite(e)
        self.coreElementsChanged()

    def __setitem__(self, k, value):
        '''
        Insert an item at a currently filled index position,
        as represented in the elements list.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note('C'), list(range(10)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note('C'), list(range(10)))
        >>> b.offset = 6
        >>> c = stream.Stream()
        >>> c.repeatInsert(note.Note('C'), list(range(10)))
        >>> c.offset = 12
        >>> b.insert(c)
        >>> a.isFlat
        True
        >>> a[3] = b
        >>> a.isFlat
        False
        '''
        # remove old value at this position
        oldValue = self._elements[k]
        del self._offsetDict[id(oldValue)]
        oldValue.sites.remove(self)
        oldValue.activeSite = None

        # assign in new position
        self._elements[k] = value
        self.coreSetElementOffset(value, value.offset, addElement=True)
        self.coreSelfActiveSite(value)
        # must get native offset

        value.sites.add(self)
        if isinstance(value, Stream):
            # know that this is now not flat
            self.coreElementsChanged(updateIsFlat=False)  # set manually
            self.isFlat = False
        else:
            # cannot be sure if this is flat, as we do not know if
            # we replaced a Stream at this index
            self.coreElementsChanged()

    def __delitem__(self, k):
        '''
        Delete element at an index position. Index positions are based
        on positions in self.elements.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note('C'), list(range(10)))
        >>> del a[0]
        >>> len(a)
        9
        '''
        del self._elements[k]
        self.coreElementsChanged()

    def __add__(self: StreamType, other: 'Stream') -> StreamType:
        '''
        Add, or concatenate, two Streams.

        Presently, this does not manipulate the offsets of the incoming elements
        to actually be at the end of the Stream. This may be a problem that
        makes this method not so useful?

        >>> a = stream.Part()
        >>> a.repeatInsert(note.Note('C'), [0, 1])
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note('G'), [0, 1, 2])
        >>> c = a + b
        >>> c.pitches  # autoSort is True, thus a sorted version results
        [<music21.pitch.Pitch C>,
         <music21.pitch.Pitch G>,
         <music21.pitch.Pitch C>,
         <music21.pitch.Pitch G>,
         <music21.pitch.Pitch G>]
        >>> len(c.notes)
        5

        The autoSort of the first stream becomes the autoSort of the
        destination.  The class of the first becomes the class of the destination.

        >>> a.autoSort = False
        >>> d = a + b
        >>> [str(p) for p in d.pitches]
        ['C', 'C', 'G', 'G', 'G']
        >>> d.__class__.__name__
        'Part'

        Works with Streams with Store at end, which does put both at the end.

        >>> a.autoSort = True
        >>> a.storeAtEnd(bar.Barline('final'))
        >>> b.storeAtEnd(clef.TrebleClef())
        >>> f = a + b
        >>> f.show('text')
        {0.0} <music21.note.Note C>
        {0.0} <music21.note.Note G>
        {1.0} <music21.note.Note C>
        {1.0} <music21.note.Note G>
        {2.0} <music21.note.Note G>
        {3.0} <music21.bar.Barline type=final>
        {3.0} <music21.clef.TrebleClef>
        '''
        if other is None or not isinstance(other, Stream):
            raise TypeError('cannot concatenate a Stream with a non-Stream')

        s = self.cloneEmpty(derivationMethod='__add__')
        # may want to keep activeSite of source Stream?
        # s.elements = self._elements + other._elements
        # need to iterate over elements and re-assign to create new locations
        for e in self._elements:
            s.insert(self.elementOffset(e), e)
        for e in other._elements:
            s.insert(other.elementOffset(e), e)

        for e in self._endElements:
            s.storeAtEnd(e)
        for e in other._endElements:
            s.storeAtEnd(e)

        # s.coreElementsChanged()
        return s

    def __bool__(self):
        '''
        As a container class, Streams return True if they are non-empty
        and False if they are empty:

        >>> def testBool(s):
        ...    if s:
        ...        return True
        ...    else:
        ...        return False

        >>> s = stream.Stream()
        >>> testBool(s)
        False
        >>> s.append(note.Note())
        >>> testBool(s)
        True
        >>> s.append(note.Note())
        >>> testBool(s)
        True

        >>> s = stream.Stream()
        >>> s.storeAtEnd(bar.Barline('final'))
        >>> testBool(s)
        True
        '''
        if self._elements:  # blindingly faster than if len(self._elements) > 0
            return True    # and even about 5x faster than if any(self._elements)
        if self._endElements:
            return True
        return False

    # ------------------------------
    @property
    def clef(self) -> clef.Clef | None:
        '''
        Finds or sets a :class:`~music21.clef.Clef` at offset 0.0 in the Stream
        (generally a Measure):

        >>> m = stream.Measure()
        >>> m.number = 10
        >>> m.clef = clef.TrebleClef()
        >>> thisTrebleClef = m.clef
        >>> thisTrebleClef.sign
        'G'
        >>> thisTrebleClef.getOffsetBySite(m)
        0.0

        Setting the clef for the measure a second time removes the previous clef
        from the measure and replaces it with the new one:

        >>> m.clef = clef.BassClef()
        >>> m.clef.sign
        'F'

        And the TrebleClef is no longer in the measure:

        >>> thisTrebleClef.getOffsetBySite(m)
        Traceback (most recent call last):
        music21.sites.SitesException: an entry for this object <music21.clef.TrebleClef> is not
              stored in stream <music21.stream.Measure 10 offset=0.0>

        The `.clef` appears in a `.show()` or other call
        just like any other element

        >>> m.append(note.Note('D#', type='whole'))
        >>> m.show('text')
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.note.Note D#>
        '''
        clefList = self.getElementsByClass(clef.Clef).getElementsByOffset(0)
        # casting to list added 20microseconds...
        return clefList.first()

    @clef.setter
    def clef(self, clefObj: clef.Clef | None):
        # if clef is None; remove object?
        oldClef = self.clef
        if oldClef is not None:
            # environLocal.printDebug(['removing clef', oldClef])
            junk = self.pop(self.index(oldClef))
        if clefObj is None:
            # all that is needed is to remove the old clef
            # there is no new clef - suppresses the clef of a stream
            return
        self.insert(0.0, clefObj)

    @property
    def timeSignature(self) -> meter.TimeSignature | None:
        '''
        Gets or sets the timeSignature at offset 0.0 of the Stream (generally a Measure)

        >>> m1 = stream.Measure(number=1)
        >>> m1.timeSignature = meter.TimeSignature('2/4')
        >>> m1.timeSignature.numerator, m1.timeSignature.denominator
        (2, 4)
        >>> m1.show('text')
        {0.0} <music21.meter.TimeSignature 2/4>

        Setting timeSignature to None removes any TimeSignature at offset 0.0:

        >>> m1.timeSignature = None
        >>> m1.elements
        ()


        Only the time signature at offset 0 is found:

        >>> m2 = stream.Measure(number=2)
        >>> m2.insert(0.0, meter.TimeSignature('5/4'))
        >>> m2.insert(2.0, meter.TimeSignature('7/4'))
        >>> ts = m2.timeSignature
        >>> ts.numerator, ts.denominator
        (5, 4)

        >>> m2.timeSignature = meter.TimeSignature('2/8')
        >>> m2.timeSignature
        <music21.meter.TimeSignature 2/8>

        After setting a new `.timeSignature`, the old one is no longer in the Stream:

        >>> ts in m2
        False

        This property is not recursive, so a Part will not have the time signature of
        the measure within it:

        >>> p = stream.Part()
        >>> p.append(m2)
        >>> p.timeSignature is None
        True
        '''
        # there could be more than one
        tsList = self.getElementsByClass(meter.TimeSignature).getElementsByOffset(0)
        # environLocal.printDebug([
        #    'matched Measure classes of type TimeSignature', tsList, len(tsList)])
        # only return timeSignatures at offset = 0.0
        return tsList.first()

    @timeSignature.setter
    def timeSignature(self, tsObj: meter.TimeSignature | None):
        oldTimeSignature = self.timeSignature
        if oldTimeSignature is not None:
            # environLocal.printDebug(['removing ts', oldTimeSignature])
            junk = self.pop(self.index(oldTimeSignature))
        if tsObj is None:
            # all that is needed is to remove the old time signature
            # there is no new time signature - suppresses the time signature of a stream
            return
        self.insert(0, tsObj)

    @property
    def keySignature(self) -> key.KeySignature | None:
        '''
        Find or set a Key or KeySignature at offset 0.0 of a stream.

        >>> a = stream.Measure()
        >>> a.keySignature = key.KeySignature(-2)
        >>> ks = a.keySignature
        >>> ks.sharps
        -2
        >>> a.show('text')
        {0.0} <music21.key.KeySignature of 2 flats>

        A key.Key object can be used instead of key.KeySignature,
        since the former derives from the latter.

        >>> a.keySignature = key.Key('E', 'major')
        >>> for k in a:
        ...     print(k.offset, repr(k))
        0.0 <music21.key.Key of E major>

        Notice that setting a new key signature replaces any previous ones:

        >>> len(a.getElementsByClass(key.KeySignature))
        1

        `.keySignature` can be set to None:

        >>> a.keySignature = None
        >>> a.keySignature is None
        True
        '''
        try:
            return next(self.iter().getElementsByClass(key.KeySignature).getElementsByOffset(0))
        except StopIteration:
            return None

    @keySignature.setter
    def keySignature(self, keyObj: key.KeySignature | None):
        '''
        >>> a = stream.Measure()
        >>> a.keySignature = key.KeySignature(6)
        >>> a.keySignature.sharps
        6
        '''
        oldKey = self.keySignature
        if oldKey is not None:
            # environLocal.printDebug(['removing key', oldKey])
            junk = self.pop(self.index(oldKey))
        if keyObj is None:
            # all that is needed is to remove the old key signature
            # there is no new key signature - suppresses the key signature of a stream
            return
        self.insert(0, keyObj)

    @property
    def staffLines(self) -> int:
        '''
        Returns the number of staffLines for the Stream, as defined by
        the first StaffLayout object found at offset 0 that defines staffLines

        >>> m = stream.Measure()
        >>> m.staffLines
        5
        >>> m.staffLines = 4
        >>> m.staffLines
        4
        >>> m.show('text')
        {0.0} <music21.layout.StaffLayout distance None, staffNumber None,
                  staffSize None, staffLines 4>

        >>> staffLayout = m.getElementsByClass(layout.StaffLayout).first()
        >>> staffLayout.staffLines = 1
        >>> m.staffLines
        1

        >>> p = stream.Part()
        >>> p.insert(0, m)
        >>> p.staffLines
        1

        >>> p2 = stream.Part()
        >>> m0 = stream.Measure()
        >>> m0.insert(0, note.Note(type='whole'))
        >>> p2.append(m0)
        >>> p2.append(m)
        >>> p2.staffLines
        5

        OMIT_FROM_DOCS

        Check that staffLayout is altered by staffLayout setter:

        >>> m.staffLines = 2
        >>> staffLayout.staffLines
        2
        '''
        from music21 import layout

        staffLayouts = self[layout.StaffLayout]
        sl: layout.StaffLayout
        # test.
        for sl in staffLayouts:
            if sl.getOffsetInHierarchy(self) > 0:
                break
            if sl.staffLines is not None:
                return sl.staffLines
        return 5

    @staffLines.setter
    def staffLines(self, newStaffLines: int):
        from music21 import layout
        staffLayouts: iterator.RecursiveIterator[layout.StaffLayout] = (
            self
            .recurse()
            .getElementsByOffset(0.0)
            .getElementsByClass(layout.StaffLayout)
        )
        firstLayout = staffLayouts.first()
        if not firstLayout:
            sl: layout.StaffLayout = layout.StaffLayout(staffLines=newStaffLines)
            self.insert(0.0, sl)
        else:
            firstLayout.staffLines = newStaffLines

    def clear(self) -> None:
        '''
        Remove all elements in a stream.

        >>> m = stream.Measure(number=3)
        >>> m.append(note.Note('C'))
        >>> m.storeAtEnd(bar.Barline('final'))
        >>> len(m)
        2
        >>> m.clear()
        >>> len(m)
        0

        Does not remove any other attributes

        >>> m.number
        3
        '''
        self.elements = ()

    def cloneEmpty(self: StreamType, derivationMethod: str | None = None) -> StreamType:
        '''
        Create a Stream that is identical to this one except that the elements are empty
        and set derivation.

        >>> p = stream.Part()
        >>> p.autoSort = False
        >>> p.id = 'hi'
        >>> p.insert(0, note.Note())
        >>> q = p.cloneEmpty(derivationMethod='demo')
        >>> q.autoSort
        False
        >>> q
        <music21.stream.Part hi>
        >>> q.derivation.origin is p
        True
        >>> q.derivation.method
        'demo'
        >>> len(q)
        0
        '''
        returnObj: StreamType = self.__class__()
        returnObj.derivation.client = returnObj
        returnObj.derivation.origin = self
        if derivationMethod is not None:
            returnObj.derivation.method = derivationMethod
        returnObj.mergeAttributes(self)  # get groups, optional id
        return returnObj

    def mergeAttributes(self, other: base.Music21Object):
        '''
        Merge relevant attributes from the Other stream into this one.

        >>> s = stream.Stream()
        >>> s.append(note.Note())
        >>> s.autoSort = False
        >>> s.id = 'hi'
        >>> s2 = stream.Stream()
        >>> s2.mergeAttributes(s)
        >>> s2.autoSort
        False
        >>> s2
        <music21.stream.Stream hi>
        >>> len(s2)
        0
        '''
        super().mergeAttributes(other)
        if not isinstance(other, Stream):
            return

        for attr in ('autoSort', 'isSorted', 'definesExplicitSystemBreaks',
                     'definesExplicitPageBreaks', '_atSoundingPitch', '_mutable'):
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

    def hasElement(self, obj):
        '''
        Return True if an element, provided as an argument, is contained in
        this Stream.

        This method is based on object equivalence, not parameter equivalence
        of different objects.

        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> s.append(n1)
        >>> s.hasElement(n1)
        True
        '''
        objId = id(obj)
        return self.coreHasElementByMemoryLocation(objId)

    def hasElementOfClass(self, className, forceFlat=False):
        '''
        Given a single class name as string,
        return True or False if an element with the
        specified class is found.

        Only a single class name can be given.

        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('5/8'))
        >>> s.append(note.Note('d-2'))
        >>> s.insert(dynamics.Dynamic('fff'))
        >>> s.hasElementOfClass(meter.TimeSignature)
        True
        >>> s.hasElementOfClass('Measure')
        False

        To be deprecated in v8 -- to be removed in v9, use:

        >>> bool(s.getElementsByClass(meter.TimeSignature))
        True
        >>> bool(s.getElementsByClass(stream.Measure))
        False

        forceFlat does nothing, while getElementsByClass can be done on recurse()
        '''
        # environLocal.printDebug(['calling hasElementOfClass()', className])
        for e in self.elements:
            if className in e.classSet:
                return True
        return False

    def mergeElements(self, other, classFilterList=None):
        '''
        Given another Stream, store references of each element
        in the other Stream in this Stream. This does not make
        copies of any elements, but simply stores all of them in this Stream.

        Optionally, provide a list of classes to include with the `classFilter` list.

        This method provides functionality like a shallow copy,
        but manages locations properly, only copies elements,
        and permits filtering by class type.


        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> n1 = note.Note('f#')
        >>> n2 = note.Note('g')
        >>> s1.append(n1)
        >>> s1.append(n2)
        >>> s2.mergeElements(s1)
        >>> len(s2)
        2
        >>> s1[0] is s2[0]
        True
        >>> s1[1] is s2[1]
        True

        >>> viola = instrument.Viola()
        >>> trumpet = instrument.Trumpet()
        >>> s1.insert(0, viola)
        >>> s1.insert(0, trumpet)
        >>> s2.mergeElements(s1, classFilterList=('BrassInstrument',))
        >>> len(s2)
        3
        >>> viola in s2
        False
        '''
        if classFilterList is not None:
            classFilterSet = set(classFilterList)
        else:
            classFilterSet = None

        for e in other._elements:
            # self.insert(other.offset, e)
            if classFilterList is not None:
                if classFilterSet.intersection(e.classSet):
                    self.coreInsert(other.elementOffset(e), e)
            else:
                self.coreInsert(other.elementOffset(e), e)

            # for c in classFilterList:
            #     if c in e.classes:
            #         match = True
            #         break
            #
            # if len(classFilterList) == 0 or match:
            #     self.insert(e.getOffsetBySite(other), e)

        for e in other._endElements:
            if classFilterList is not None:
                if classFilterSet.intersection(e.classSet):
                    self.coreStoreAtEnd(e)
            else:
                self.coreStoreAtEnd(e)

            # match = False
            # for c in classFilterList:
            #     if c in e.classes:
            #         match = True
            #         break
            # if len(classFilterList) == 0 or match:
            #     self.storeAtEnd(e)
        self.coreElementsChanged()

    def index(self, el: base.Music21Object) -> int:
        '''
        Return the first matched index for
        the specified object.

        Raises a StreamException if the object cannot
        be found.

        >>> s = stream.Stream()
        >>> n1 = note.Note('G')
        >>> n2 = note.Note('A')

        >>> s.insert(0.0, n1)
        >>> s.insert(5.0, n2)
        >>> len(s)
        2
        >>> s.index(n1)
        0
        >>> s.index(n2)
        1

        Note that this is done via Object identity, so another identical
        G won't be found in the stream.

        >>> n3 = note.Note('G')
        >>> s.index(n3)
        Traceback (most recent call last):
        music21.exceptions21.StreamException: cannot find object (<music21.note.Note G>) in Stream

        To find the index of something equal to the object in the stream, cast the
        stream to a tuple or list first:

        >>> tuple(s).index(n3)
        0

        '''
        if not self.isSorted and self.autoSort:
            self.sort()  # will set isSorted to True

        if 'index' in self._cache and self._cache['index'] is not None:
            try:
                return self._cache['index'][id(el)]
            except KeyError:
                pass  # not in cache
        else:
            self._cache['index'] = {}

        objId = id(el)

        count = 0

        for e in self._elements:
            if e is el:
                self._cache['index'][objId] = count
                return count
            count += 1
        for e in self._endElements:
            if e is el:
                self._cache['index'][objId] = count
                return count  # this is the index
            count += 1  # cumulative indices
        raise StreamException(f'cannot find object ({el}) in Stream')

    def remove(self,
               targetOrList: base.Music21Object | Sequence[base.Music21Object],
               *,
               shiftOffsets=False,
               recurse=False):
        # noinspection PyShadowingNames
        '''
        Remove an object from this Stream. Additionally, this Stream is
        removed from the object's sites in :class:`~music21.sites.Sites`.

        If a list of objects is passed, they will all be removed.
        If shiftOffsets is True, then offsets will be
        corrected after object removal. It is more efficient to pass
        a list of objects than to call remove on
        each object individually if shiftOffsets is True.

        >>> import copy
        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')

        Copies of an object are not the same as the object

        >>> n3 = copy.deepcopy(n2)
        >>> s.insert(10, n1)
        >>> s.insert(5, n2)
        >>> s.remove(n1)
        >>> len(s)
        1
        >>> s.insert(20, n3)
        >>> s.remove(n3)
        >>> [e for e in s] == [n2]
        True

        No error is raised if the target is not found.

        >>> s.remove(n3)

        >>> s2 = stream.Stream()
        >>> c = clef.TrebleClef()
        >>> n1, n2, n3, n4 = note.Note('a'), note.Note('b'), note.Note('c'), note.Note('d')
        >>> n5, n6, n7, n8 = note.Note('e'), note.Note('f'), note.Note('g'), note.Note('a')
        >>> s2.insert(0.0, c)
        >>> s2.append([n1, n2, n3, n4, n5, n6, n7, n8])
        >>> s2.remove(n1, shiftOffsets=True)
        >>> s2.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        {3.0} <music21.note.Note E>
        {4.0} <music21.note.Note F>
        {5.0} <music21.note.Note G>
        {6.0} <music21.note.Note A>

        >>> s2.remove([n3, n6, n4], shiftOffsets=True)
        >>> s2.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Note E>
        {2.0} <music21.note.Note G>
        {3.0} <music21.note.Note A>

        With the recurse=True parameter, we can remove elements deeply nested.
        However, shiftOffsets
        does not work with recurse=True yet.

        >>> p1 = stream.Part()
        >>> m1 = stream.Measure(number=1)
        >>> c = clef.BassClef()
        >>> m1.insert(0, c)
        >>> m1.append(note.Note(type='whole'))
        >>> p1.append(m1)
        >>> m2 = stream.Measure(number=2)
        >>> n2 = note.Note('D', type='half')
        >>> m2.append(n2)
        >>> n3 = note.Note(type='half')
        >>> m2.append(n3)
        >>> p1.append(m2)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.note.Note C>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note D>
            {2.0} <music21.note.Note C>

        Without recurse=True:

        >>> p1.remove(n2)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.note.Note C>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note D>
            {2.0} <music21.note.Note C>

        With recurse=True:

        >>> p1.remove(n2, recurse=True)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.note.Note C>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {2.0} <music21.note.Note C>

        With recurse=True and a list to remove:

        >>> p1.remove([c, n3], recurse=True)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.note.Note C>
        {4.0} <music21.stream.Measure 2 offset=4.0>
        <BLANKLINE>


        Can also remove elements stored at end:

        >>> streamWithBarline = stream.Stream(note.Note())
        >>> barline = bar.Barline('final')
        >>> streamWithBarline.storeAtEnd(barline)
        >>> barline in streamWithBarline
        True
        >>> streamWithBarline.remove(barline)
        >>> barline in streamWithBarline
        False

        * Changed in v5.3: firstMatchOnly removed -- impossible to have element
          in stream twice.  recurse and shiftOffsets changed to keywordOnly arguments
        '''
        # experimental
        if self._mutable is False:  # pragma: no cover
            raise ImmutableStreamException('Cannot remove from an immutable stream')
        # TODO: Next to clean up... a doozy -- filter out all the different options.

        # TODO: Add an option to renumber measures
        # TODO: Shift offsets if recurse is True
        if shiftOffsets is True and recurse is True:  # pragma: no cover
            raise StreamException(
                'Cannot do both shiftOffsets and recurse search at the same time...yet')

        targetList: list[base.Music21Object]
        if not common.isListLike(targetOrList):
            if t.TYPE_CHECKING:
                assert isinstance(targetOrList, base.Music21Object)
            targetList = [targetOrList]
        elif isinstance(targetOrList, Sequence) and len(targetOrList) > 1:
            if t.TYPE_CHECKING:
                assert not isinstance(targetOrList, base.Music21Object)
            try:
                targetList = list(sorted(targetOrList, key=self.elementOffset))
            except sites.SitesException:
                # will not be found if recursing, it's not such a big deal...
                targetList = list(targetOrList)
        else:
            if t.TYPE_CHECKING:
                assert not isinstance(targetOrList, base.Music21Object)
            targetList = list(targetOrList)

        shiftDur = 0.0  # for shiftOffsets

        for i, target in enumerate(targetList):
            try:
                indexInStream = self.index(target)
            except StreamException as se:
                if not isinstance(target, base.Music21Object):
                    raise TypeError(f'{target} is not a Music21Object; got {type(target)}') from se
                if recurse is True:
                    for s in self.recurse(streamsOnly=True):
                        try:
                            indexInStream = s.index(target)
                            s.remove(target)
                            break
                        except (StreamException, sites.SitesException):
                            continue
                # recursion matched or didn't or wasn't run. either way no need for rest...
                continue

            # Anything that messes with ._elements or ._endElements should be in core.py
            # TODO: move it...
            matchedEndElement = False
            baseElementCount = len(self._elements)
            matchOffset = 0.0  # to avoid possibility of undefined

            if indexInStream < baseElementCount:
                match = self._elements.pop(indexInStream)
            else:
                match = self._endElements.pop(indexInStream - baseElementCount)
                matchedEndElement = True

            if match is not None:
                if shiftOffsets is True:
                    matchOffset = self.elementOffset(match)

                try:
                    del self._offsetDict[id(match)]
                except KeyError:  # pragma: no cover
                    pass
                self.coreElementsChanged(clearIsSorted=False)
                match.sites.remove(self)
                match.activeSite = None

            if shiftOffsets is True and matchedEndElement is False:
                matchDuration = match.duration.quarterLength
                shiftedRegionStart = matchOffset + matchDuration
                if (i + 1) < len(targetList):
                    shiftedRegionEnd = self.elementOffset(targetList[i + 1])
                else:
                    shiftedRegionEnd = self.duration.quarterLength

                shiftDur += matchDuration
                if shiftDur != 0.0:
                    # can this be done with recurse???
                    for e in self.getElementsByOffset(shiftedRegionStart,
                                                      shiftedRegionEnd,
                                                      includeEndBoundary=False,
                                                      mustFinishInSpan=False,
                                                      mustBeginInSpan=True):

                        elementOffset = self.elementOffset(e)
                        self.coreSetElementOffset(e, elementOffset - shiftDur)
            # if renumberMeasures is True and matchedEndElement is False:
            #     pass  # This should maybe just call a function renumberMeasures
        self.coreElementsChanged(clearIsSorted=False)

    def pop(self, index: int | None = None) -> base.Music21Object:
        '''
        Return and remove the object found at the
        user-specified index value. Index values are
        those found in `elements` and are not necessary offset order.

        >>> a = stream.Stream()
        >>> for i in range(12):  # notes C, C#, etc. to B
        ...     a.append(note.Note(i))
        >>> a.pop(0)
        <music21.note.Note C>
        >>> len(a)
        11

        If nothing is given, then it pops the last thing from the stream.

        >>> a.pop()
        <music21.note.Note B>
        >>> len(a)
        10
        '''
        eLen = len(self._elements)
        # if less than base length, it is in _elements
        if index is None:
            if self._endElements:
                post = self._endElements.pop()
            else:
                post = self._elements.pop()
        elif index < eLen:
            post = self._elements.pop(index)
        else:  # it is in the _endElements
            post = self._endElements.pop(index - eLen)

        self.coreElementsChanged(clearIsSorted=False)

        try:
            del self._offsetDict[id(post)]
        except KeyError:  # pragma: no cover
            pass

        post.sites.remove(self)
        post.activeSite = None
        return post

    def _removeIteration(self, streamIterator):
        '''
        helper method to remove different kinds of elements.
        '''
        popDict = {'_elements': [],
                   '_endElements': []
                   }
        for unused_el in streamIterator:
            ai = streamIterator.activeInformation
            popDict[ai['iterSection']].append(ai['sectionIndex'])

        # do not pop while iterating...

        for section in popDict:
            sectionList = getattr(self, section)  # self._elements or self._endElements
            popList = popDict[section]
            for popIndex in reversed(popList):
                # Note: repeated pops do not seem to be O(n) in Python.
                removeElement = sectionList.pop(popIndex)
                try:
                    del self._offsetDict[id(removeElement)]
                except KeyError:  # pragma: no cover
                    pass

                # TODO: to make recursive, store a tuple of active sites and index
                removeElement.sites.remove(self)
                removeElement.activeSite = None

        # call elements changed once; sorted arrangement has not changed
        self.coreElementsChanged(clearIsSorted=False)

    def removeByClass(self, classFilterList) -> None:
        '''
        Remove all elements from the Stream
        based on one or more classes given
        in a list.

        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.repeatAppend(note.Note('C'), 8)
        >>> len(s)
        9
        >>> s.removeByClass('GeneralNote')
        >>> len(s)
        1
        >>> len(s.notes)
        0

        Test that removing from end elements works.

        >>> s = stream.Measure()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.repeatAppend(note.Note('C'), 4)
        >>> s.rightBarline = bar.Barline('final')
        >>> len(s)
        6
        >>> s.removeByClass('Barline')
        >>> len(s)
        5
        '''
        elFilter = self.iter().getElementsByClass(classFilterList)
        self._removeIteration(elFilter)

    def removeByNotOfClass(self, classFilterList):
        '''
        Remove all elements not of the specified
        class or subclass in the Stream in place.

        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.repeatAppend(note.Note('C'), 8)
        >>> len(s)
        9
        >>> s.removeByNotOfClass(meter.TimeSignature)
        >>> len(s)
        1
        >>> len(s.notes)
        0
        '''
        elFilter = self.iter().getElementsNotOfClass(classFilterList)
        return self._removeIteration(elFilter)

    # pylint: disable=no-member
    def _deepcopySubclassable(self: StreamType,
                              memo: dict[int, t.Any] | None = None,
                              *,
                              ignoreAttributes=None,
                              ) -> StreamType:
        # NOTE: this is a performance critical operation
        defaultIgnoreSet = {
            '_offsetDict', '_elements', '_endElements',
        }
        if ignoreAttributes is None:
            ignoreAttributes = defaultIgnoreSet
        else:  # pragma: no cover
            ignoreAttributes = ignoreAttributes | defaultIgnoreSet

        # PyCharm seems to think that this is a StreamCore
        # noinspection PyTypeChecker
        new: StreamType = super()._deepcopySubclassable(memo, ignoreAttributes=ignoreAttributes)

        # new._offsetDict will get filled when ._elements is copied.
        newOffsetDict: dict[int, tuple[OffsetQLSpecial, base.Music21Object]] = {}
        new._offsetDict = newOffsetDict
        new._elements = []
        new._endElements = []

        # streamStatus's deepcopy is smart enough to ignore client.  set new
        new.streamStatus.client = new

        # must manually add elements to new Stream
        for e in self._elements:
            # environLocal.printDebug(['deepcopy()', e, 'old', old, 'id(old)', id(old),
            #     'new', new, 'id(new)', id(new), 'old.hasElement(e)', old.hasElement(e),
            #     'e.activeSite', e.activeSite, 'e.getSites()', e.getSites(), 'e.getSiteIds()',
            #     e.getSiteIds()], format='block')
            #
            # this will work for all with __deepcopy___
            # get the old offset from the activeSite Stream
            # user here to provide new offset
            #
            # new.insert(e.getOffsetBySite(old), newElement,
            #            ignoreSort=True)
            offset = self.elementOffset(e)
            if not e.isStream:
                # noinspection PyArgumentList
                newElement = copy.deepcopy(e, memo)
            else:
                # this prevents needing to make multiple replacements of spanner bundles
                # apparently that was at some point a HUGE slowdown.  not 100% sure if
                # it is still a problem or why.
                newElement = e._deepcopySubclassable(memo)

            # ## TEST on copying!!!!
            # if isinstance(newElement, note.Note):
            #     newElement.pitch.ps += 2.0
            new.coreInsert(offset, newElement, ignoreSort=True)

        # must manually add elements to
        for e in self._endElements:
            # this will work for all with __deepcopy___
            # get the old offset from the activeSite Stream
            # user here to provide new offset

            # noinspection PyArgumentList
            new.coreStoreAtEnd(copy.deepcopy(e, memo))

        new.coreElementsChanged()

        return new

    def __deepcopy__(self: StreamType, memo=None) -> StreamType:
        '''
        Deepcopy the stream from copy.deepcopy()
        '''
        new = self._deepcopySubclassable(memo)
        # see custom _deepcopySubclassable for why this is here rather than there.
        if new._elements:  # pylint: disable:no-member
            self._replaceSpannerBundleForDeepcopy(new)

        return new

    def _replaceSpannerBundleForDeepcopy(self, new):
        # perform the spanner bundle replacement on the outer stream.
        # caching this is CRUCIAL! using new.spannerBundle every time below added
        # 40% to the test suite time!
        newSpannerBundle = new.spannerBundle
        # only proceed if there are spanners, otherwise creating semiFlat
        if not newSpannerBundle:
            return
        # iterate over complete semi-flat (need containers); find
        # all new/old pairs
        for e in new.recurse(includeSelf=False):
            # update based on id of old object, and ref to new object
            if 'music21.spanner.Spanner' in e.classSet:
                continue
            if e.derivation.method != '__deepcopy__':
                continue

            origin = e.derivation.origin
            if origin is None:  # pragma: no cover
                continue  # should not happen...

            if origin.sites.hasSpannerSite():
                # environLocal.printDebug(['Stream.__deepcopy__', 'replacing component to', e])
                # this will clear and replace the proper locations on
                # the SpannerStorage Stream
                newSpannerBundle.replaceSpannedElement(origin, e)

                # need to remove the old SpannerStorage Stream from this element;
                # however, all we have here is the new Spanner and new elements
                # this must be done here, not when originally copying
                e.purgeOrphans(excludeStorageStreams=False)

    def setElementOffset(
        self,
        element: base.Music21Object,
        offset: int | float | Fraction | OffsetSpecial,
    ):
        '''
        Sets the Offset for an element that is already in a given stream.

        Set up a note in two different streams at two different offsets:

        >>> n = note.Note('B-4')
        >>> s = stream.Stream(id='Stream1')
        >>> s.insert(10, n)
        >>> n.offset
        10.0
        >>> n.activeSite.id
        'Stream1'

        >>> s2 = stream.Stream(id='Stream2')
        >>> s2.insert(30, n)
        >>> n.activeSite.id
        'Stream2'

        Now change the note's offset in Stream1:

        >>> s.setElementOffset(n, 20.0)

        This call has the effect of switching the `activeSite` of `n` to `s`.

        >>> n.activeSite.id
        'Stream1'
        >>> n.offset
        20.0
        >>> n.getOffsetBySite(s)
        20.0

        If the element is not in the Stream, raises a StreamException:

        >>> n2 = note.Note('D')
        >>> s.setElementOffset(n2, 30.0)
        Traceback (most recent call last):
        music21.exceptions21.StreamException: Cannot set the offset for element
            <music21.note.Note D>, not in Stream <music21.stream.Stream Stream1>.

        * Changed in v5.5: also sets .activeSite for the element
        * Changed in v6.7: also runs coreElementsChanged()
        * Changed in v7: addElement is removed;
          see :meth:`~music21.stream.core.StreamCoreMixin.coreSetElementOffset`
        '''
        self.coreSetElementOffset(element,
                                  offset,
                                  )
        # might change sorting, but not flatness.  Maybe other things can be False too.
        self.coreElementsChanged(updateIsFlat=False)

    def elementOffset(self, element, returnSpecial=False):
        '''
        Return the offset as an opFrac (float or Fraction) from the offsetMap.
        highly optimized for speed.

        >>> m = stream.Measure(number=1)
        >>> m.append(note.Note('C'))
        >>> d = note.Note('D')
        >>> m.append(d)
        >>> m.elementOffset(d)
        1.0

        If returnSpecial is True then returns like OffsetSpecial.AT_END are allowed.

        >>> b = bar.Barline()
        >>> m.storeAtEnd(b)
        >>> m.elementOffset(b)
        2.0
        >>> m.elementOffset(b, returnSpecial=True)
        <OffsetSpecial.AT_END>

        Unlike element.getOffsetBySite(self), this method will NOT follow derivation chains
        and in fact will raise a sites.SitesException

        >>> import copy
        >>> p = stream.Part(id='sPart')
        >>> p.insert(20, m)
        >>> m.getOffsetBySite(p)
        20.0
        >>> p.elementOffset(m)
        20.0

        >>> mCopy = copy.deepcopy(m)
        >>> mCopy.number = 10
        >>> mCopy.derivation
        <Derivation of <music21.stream.Measure 10 offset=0.0> from
            <music21.stream.Measure 1 offset=20.0> via '__deepcopy__'>
        >>> mCopy.getOffsetBySite(p)
        20.0
        >>> p.elementOffset(mCopy)
        Traceback (most recent call last):
        music21.sites.SitesException: an entry for this object 0x... is not stored in
            stream <music21.stream.Part sPart>

        Performance note: because it will not follow derivation chains, and does
        not need to unwrap a weakref, this method
        should usually be about 3x faster than element.getOffsetBySite(self) --
        currently 600ns instead of 1.5 microseconds.
        '''
        try:
            # 2.3 million times found in TestStream
            o = self._offsetDict[id(element)][0]
            # if returnedElement is not element:  # stale reference...
            #    o = None  #  0 in TestStream -- not worth testing
        except KeyError:  # 445k - 442,443 = 3k in TestStream
            for idElement in self._offsetDict:  # slower search
                o, returnedElement = self._offsetDict[idElement]
                if element is returnedElement:
                    # MSC 2021 -- it is possible this no longer ever happens,
                    #    currently uncovered in Coverage.
                    break
            else:
                raise base.SitesException(
                    f'an entry for this object 0x{id(element):x} is not stored in stream {self}')

        # OffsetSpecial.__contains__() is more expensive, so try to fail fast
        if isinstance(o, str) and returnSpecial is False and o in OffsetSpecial:
            try:
                return getattr(self, o)
            except AttributeError:  # pragma: no cover
                raise base.SitesException(
                    'attempted to retrieve a bound offset with a string '
                    + f'attribute that is not supported: {o}')
        else:
            return o

    def insert(self,
               offsetOrItemOrList,
               itemOrNone=None,
               *,
               ignoreSort=False,
               setActiveSite=True
               ):
        '''
        Inserts an item(s) at the given offset(s).

        If `ignoreSort` is True then the inserting does not
        change whether the Stream is sorted or not (much faster if you're
        going to be inserting dozens
        of items that don't change the sort status)

        The `setActiveSite` parameter should nearly always be True; only for
        advanced Stream manipulation would you not change
        the activeSite after inserting an element.

        Has three forms: in the two argument form, inserts an
        element at the given offset:

        >>> st1 = stream.Stream()
        >>> st1.insert(32, note.Note('B-'))
        >>> st1.highestOffset
        32.0

        In the single argument form with an object, inserts the element at its
        stored offset:

        >>> n1 = note.Note('C#')
        >>> n1.offset = 30.0
        >>> st1 = stream.Stream()
        >>> st1.insert(n1)
        >>> st2 = stream.Stream()
        >>> st2.insert(40.0, n1)
        >>> n1.getOffsetBySite(st1)
        30.0

        In single argument form with a list, the list should
        contain pairs that alternate
        offsets and items; the method then, obviously, inserts the items
        at the specified offsets.

        Note: This functionality will be deprecated in v9 and replaced
        with a list of tuples of [(offset, element), (offset, element)]
        and removed in v10

        >>> n1 = note.Note('G')
        >>> n2 = note.Note('F#')
        >>> st3 = stream.Stream()
        >>> st3.insert([1.0, n1, 2.0, n2])
        >>> n1.getOffsetBySite(st3)
        1.0
        >>> n2.getOffsetBySite(st3)
        2.0
        >>> len(st3)
        2

        Raises an error if offset is not a number

        >>> stream.Stream().insert('l', note.Note('B'))
        Traceback (most recent call last):
        music21.exceptions21.StreamException: Offset 'l' must be a number.

        ...or if the object is not a music21 object (or a list of them)

        >>> stream.Stream().insert(3.3, 'hello')
        Traceback (most recent call last):
        music21.exceptions21.StreamException: The object you tried to add
            to the Stream, 'hello', is not a Music21Object.
            Use an ElementWrapper object if this is what you intend.

        The error message is slightly different in the one-element form:

        >>> stream.Stream().insert('hello')
        Traceback (most recent call last):
        music21.exceptions21.StreamException: Cannot insert item 'hello' to
            stream -- is it a music21 object?
        '''
        # environLocal.printDebug(['self', self, 'offsetOrItemOrList',
        #              offsetOrItemOrList, 'itemOrNone', itemOrNone,
        #             'ignoreSort', ignoreSort, 'setActiveSite', setActiveSite])
        # normal approach: provide offset and item
        if itemOrNone is not None:
            offset = offsetOrItemOrList
            item = itemOrNone
        elif itemOrNone is None and isinstance(offsetOrItemOrList, list):
            i = 0
            while i < len(offsetOrItemOrList):
                offset = offsetOrItemOrList[i]
                item = offsetOrItemOrList[i + 1]
                # recursively calling insert() here
                self.insert(offset, item, ignoreSort=ignoreSort)
                i += 2
            return
        # assume first arg is item, and that offset is local offset of object
        else:
            item = offsetOrItemOrList
            # offset = item.offset
            # this is equivalent to:
            try:
                activeSite = item.activeSite
                offset = item.getOffsetBySite(activeSite)
            except AttributeError:
                raise StreamException(f'Cannot insert item {item!r} to stream '
                                      + '-- is it a music21 object?')

        # if not common.isNum(offset):
        try:  # using float conversion instead of isNum for performance
            offset = float(offset)
        except (ValueError, TypeError):
            raise StreamException(f'Offset {offset!r} must be a number.')

        element = item

        # checks if element is self, among other checks
        self.coreGuardBeforeAddElement(element)
        # main insert procedure here

        storeSorted = self.coreInsert(offset,
                                      element,
                                      ignoreSort=ignoreSort,
                                      setActiveSite=setActiveSite)
        updateIsFlat = False
        if element.isStream:
            updateIsFlat = True
        self.coreElementsChanged(updateIsFlat=updateIsFlat)
        if ignoreSort is False:
            self.isSorted = storeSorted

    def insertIntoNoteOrChord(self, offset, noteOrChord, chordsOnly=False):
        # noinspection PyShadowingNames
        '''
        Insert a Note or Chord into an offset position in this Stream.
        If there is another Note or Chord in this position,
        create a new Note or Chord that combines the pitches of the
        inserted chord. If there is a Rest in this position,
        the Rest is replaced by the Note or Chord. The duration of the
        previously-found chord will remain the same in the new Chord.

        >>> n1 = note.Note('D4')
        >>> n1.duration.quarterLength = 2.0
        >>> r1 = note.Rest()
        >>> r1.duration.quarterLength = 2.0
        >>> c1 = chord.Chord(['C4', 'E4'])
        >>> s = stream.Stream()
        >>> s.append(n1)
        >>> s.append(r1)
        >>> s.append(c1)
        >>> s.show('text')
        {0.0} <music21.note.Note D>
        {2.0} <music21.note.Rest half>
        {4.0} <music21.chord.Chord C4 E4>

        Save the original Streams for later

        >>> import copy
        >>> s2 = copy.deepcopy(s)
        >>> s3 = copy.deepcopy(s)
        >>> s4 = copy.deepcopy(s)

        Notice that the duration of the inserted element is not taken into
        consideration and the original element is not broken up,
        as it would be in chordify().  But Chords and Notes are created...

        >>> for i in [0.0, 2.0, 4.0]:
        ...     s.insertIntoNoteOrChord(i, note.Note('F#4'))
        >>> s.show('text')
        {0.0} <music21.chord.Chord D4 F#4>
        {2.0} <music21.note.Note F#>
        {4.0} <music21.chord.Chord C4 E4 F#4>

        if chordsOnly is set to True then no notes are returned, only chords, but
        untouched notes are left alone:

        >>> s2.insert(5.0, note.Note('E##4'))
        >>> for i in [0.0, 2.0, 4.0]:
        ...     s2.insertIntoNoteOrChord(i, note.Note('F#4'), chordsOnly=True)
        >>> s2.show('text')
        {0.0} <music21.chord.Chord D4 F#4>
        {2.0} <music21.chord.Chord F#4>
        {4.0} <music21.chord.Chord C4 E4 F#4>
        {5.0} <music21.note.Note E##>

        A chord inserted on top of a note always changes the note into a chord:

        >>> s2.insertIntoNoteOrChord(5.0, chord.Chord('F#4 G-4'))
        >>> s2.show('text')
        {0.0} <music21.chord.Chord D4 F#4>
        {2.0} <music21.chord.Chord F#4>
        {4.0} <music21.chord.Chord C4 E4 F#4>
        {5.0} <music21.chord.Chord E##4 F#4 G-4>

        Chords can also be inserted into rests:

        >>> s3.getElementsByOffset(2.0).first()
        <music21.note.Rest half>
        >>> s3.insertIntoNoteOrChord(2.0, chord.Chord('C4 E4 G#4'))
        >>> s3.show('text')
        {0.0} <music21.note.Note D>
        {2.0} <music21.chord.Chord C4 E4 G#4>
        {4.0} <music21.chord.Chord C4 E4>

        Despite the variable name, a rest could be inserted into a noteOrChord.
        It does nothing to existing notes or chords, and just adds a new rest
        afterwards.

        >>> s4.show('text', addEndTimes=True)
        {0.0 - 2.0} <music21.note.Note D>
        {2.0 - 4.0} <music21.note.Rest half>
        {4.0 - 5.0} <music21.chord.Chord C4 E4>

        >>> for i in [0.0, 4.0, 6.0]:  # skipping 2.0 for now
        ...     r = note.Rest(type='quarter')
        ...     s4.insertIntoNoteOrChord(i, r)
        >>> r2 = note.Rest(type='quarter')
        >>> s4.insertIntoNoteOrChord(2.0, r)
        >>> s4.show('text', addEndTimes=True)
        {0.0 - 2.0} <music21.note.Note D>
        {2.0 - 4.0} <music21.note.Rest half>
        {4.0 - 5.0} <music21.chord.Chord C4 E4>
        {6.0 - 7.0} <music21.note.Rest quarter>

        Notice that (1) the original duration and not the new duration is used, unless
        there is no element at that place, and (2) if an element is put into a place where
        no existing element was found, then it will be found in the new Stream, but if it
        is placed on top of an existing element, the original element or a new copy will remain:

        >>> r in s4
        True
        >>> r2 in s4
        False

        If a Stream has more than one note, chord, or rest at that position,
        currently an error is raised.  This may change later:

        >>> s5 = stream.Stream()
        >>> s5.insert(0, note.Note('C##4'))
        >>> s5.insert(0, note.Note('E--4'))
        >>> s5.insertIntoNoteOrChord(0, note.Note('D4'))
        Traceback (most recent call last):
        music21.exceptions21.StreamException: more than one element found at the specified offset
        '''
        # could use duration of Note to get end offset span
        targets = list(
            self.getElementsByOffset(
                offset,
                offset + noteOrChord.quarterLength,  # set end to dur of supplied
                includeEndBoundary=False,
                mustFinishInSpan=False,
                mustBeginInSpan=True
            ).notesAndRests
        )
        removeTarget = None
        # environLocal.printDebug(['insertIntoNoteOrChord', [e for e in targets]])
        if len(targets) == 1:
            pitches = []      # avoid an undefined variable warning...
            components = []   # ditto

            target = targets[0]  # assume first
            removeTarget = target
            if isinstance(target, note.Rest):
                if isinstance(noteOrChord, note.Note):
                    pitches = [noteOrChord.pitch]
                    components = [noteOrChord]
                elif isinstance(noteOrChord, chord.Chord):
                    pitches = list(noteOrChord.pitches)
                    components = list(noteOrChord)
            if isinstance(target, note.Note):
                # if a note, make it into a chord
                if isinstance(noteOrChord, note.Note):
                    pitches = [target.pitch, noteOrChord.pitch]
                    components = [target, noteOrChord]
                elif isinstance(noteOrChord, chord.Chord):
                    pitches = [target.pitch] + list(noteOrChord.pitches)
                    components = [target] + list(noteOrChord)
                else:
                    pitches = [target.pitch]
                    components = [target]
            if isinstance(target, chord.Chord):
                # if a chord, make it into a chord
                if isinstance(noteOrChord, note.Note):
                    pitches = list(target.pitches) + [noteOrChord.pitch]
                    components = list(target) + [noteOrChord]
                elif isinstance(noteOrChord, chord.Chord):
                    pitches = list(target.pitches) + list(noteOrChord.pitches)
                    components = list(target) + list(noteOrChord)
                else:
                    pitches = list(target.pitches)
                    components = list(target)

            if len(pitches) > 1 or chordsOnly is True:
                finalTarget = chord.Chord(pitches)
            elif len(pitches) == 1:
                finalTarget = note.Note(pitches[0])
            else:
                finalTarget = note.Rest()

            finalTarget.expressions = target.expressions
            finalTarget.articulations = target.articulations
            finalTarget.duration = target.duration
            # append lyrics list
            if hasattr(target, 'lyrics'):
                for ly in target.lyrics:
                    if ly.text not in ('', None):
                        finalTarget.addLyric(ly.text)
            # finalTarget.lyrics = target.lyrics
            if hasattr(finalTarget, 'stemDirection') and hasattr(target, 'stemDirection'):
                finalTarget.stemDirection = target.stemDirection
            if hasattr(finalTarget, 'noteheadFill') and hasattr(target, 'noteheadFill'):
                finalTarget.noteheadFill = target.noteheadFill

            # fill component details
            if isinstance(finalTarget, chord.Chord):
                for i, n in enumerate(finalTarget):
                    nPrevious = components[i]
                    n.noteheadFill = nPrevious.noteheadFill

        elif len(targets) > 1:
            raise StreamException('more than one element found at the specified offset')
        else:
            finalTarget = noteOrChord

        if removeTarget is not None:
            self.remove(removeTarget)
        # insert normally, nothing to handle
        self.insert(offset, finalTarget, ignoreSort=False, setActiveSite=True)

    def append(self, others):
        '''
        Add a Music21Object (including another Stream) to the end of the current Stream.

        If given a list, will append each element in order after the previous one.

        The "end" of the stream is determined by the `highestTime` property
        (that is the latest "release" of an object, or directly after the last
        element ends).

        Runs fast for multiple addition and will preserve isSorted if True

        >>> a = stream.Stream()
        >>> notes = []
        >>> for x in range(3):
        ...     n = note.Note('G#')
        ...     n.duration.quarterLength = 3
        ...     notes.append(n)
        >>> a.append(notes[0])
        >>> a.highestOffset, a.highestTime
        (0.0, 3.0)
        >>> a.append(notes[1])
        >>> a.highestOffset, a.highestTime
        (3.0, 6.0)
        >>> a.append(notes[2])
        >>> a.highestOffset, a.highestTime
        (6.0, 9.0)
        >>> notes2 = []

        Notes' naive offsets will
        change when they are added to a stream.

        >>> for x in range(3):
        ...     n = note.Note('A-')
        ...     n.duration.quarterLength = 3
        ...     n.offset = 0
        ...     notes2.append(n)
        >>> a.append(notes2)  # add em all again
        >>> a.highestOffset, a.highestTime
        (15.0, 18.0)
        >>> a.isSequence()
        True

        Adding a note that already has an offset set does nothing different
        from above! That is, it is still added to the end of the Stream:

        >>> n3 = note.Note('B-')
        >>> n3.offset = 1
        >>> n3.duration.quarterLength = 3
        >>> a.append(n3)
        >>> a.highestOffset, a.highestTime
        (18.0, 21.0)
        >>> n3.getOffsetBySite(a)
        18.0

        Prior to v5.7 there was a bug where appending a `Clef` after a `KeySignature`
        or a `Measure` after a `KeySignature`, etc. would not cause sorting to be re-run.
        This bug is now fixed.

        >>> s = stream.Stream()
        >>> s.append([meter.TimeSignature('4/4'),
        ...           clef.TrebleClef()])
        >>> s.elements[0]
        <music21.clef.TrebleClef>
        >>> s.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>

        >>> s.append(metadata.Metadata(composer='Cage'))
        >>> s.show('text')
        {0.0} <music21.metadata.Metadata object at 0x11ca356a0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        '''
        # store and increment the highest time for insert offset
        highestTime = self.highestTime
        if not common.isListLike(others):
            # back into a list for list processing if single
            others = [others]

        clearIsSorted = False
        if self._elements:
            lastElement = self._elements[-1]
        else:
            lastElement = None

        updateIsFlat = False
        for e in others:
            self.coreGuardBeforeAddElement(e)
            if e.isStream:  # any on that is a Stream req update
                updateIsFlat = True
            # add this Stream as a location for the new elements, with
            # the offset set to the current highestTime
            self.coreSetElementOffset(e, highestTime, addElement=True)
            e.sites.add(self)
            # need to explicitly set the activeSite of the element
            self.coreSelfActiveSite(e)
            self._elements.append(e)

            if e.duration.quarterLength != 0:
                # environLocal.printDebug(['incrementing highest time',
                #                         'e.duration.quarterLength',
                #                          e.duration.quarterLength])
                highestTime += e.duration.quarterLength
            if lastElement is not None and not lastElement.duration.quarterLength:
                if (e.priority < lastElement.priority
                        or e.classSortOrder < lastElement.classSortOrder):
                    clearIsSorted = True
            lastElement = e

        # does not normally change sorted state
        if clearIsSorted:
            storeSorted = False
        else:
            storeSorted = self.isSorted

        # we cannot keep the index cache here b/c we might
        self.coreElementsChanged(updateIsFlat=updateIsFlat)
        self.isSorted = storeSorted
        self._setHighestTime(opFrac(highestTime))  # call after to store in cache

    def storeAtEnd(self, itemOrList, ignoreSort=False):
        '''
        Inserts an item or items at the end of the Stream,
        stored in the special box (called _endElements).

        This method is useful for putting things such as
        right bar lines or courtesy clefs that should always
        be at the end of a Stream no matter what else is appended
        to it.

        As sorting is done only by priority and class,
        it cannot avoid setting isSorted to False.

        >>> s = stream.Stream()
        >>> b = bar.Repeat()
        >>> s.storeAtEnd(b)
        >>> b in s
        True
        >>> s.elementOffset(b)
        0.0
        >>> s.elementOffset(b, returnSpecial=True)
        <OffsetSpecial.AT_END>

        Only elements of zero duration can be stored.  Otherwise, a
        `StreamException` is raised.
        '''
        if isinstance(itemOrList, list):
            for item in itemOrList:
                # recursively calling insert() here
                self.storeAtEnd(item, ignoreSort=ignoreSort)
            return
        else:
            item = itemOrList

        element = item
        # checks if element is self, among other checks
        self.coreGuardBeforeAddElement(element)

        # cannot support elements with Durations in the highest time list
        if element.duration.quarterLength != 0:
            raise StreamException('cannot insert an object with a non-zero '
                                  + 'Duration into the highest time elements list')

        self.coreStoreAtEnd(element)
        # Streams cannot reside in end elements, thus do not update is flat
        self.coreElementsChanged(updateIsFlat=False)

    # --------------------------------------------------------------------------
    # all the following call either insert() or append()

    def insertAndShift(self, offsetOrItemOrList, itemOrNone=None):
        '''
        Insert an item at a specified or native offset,
        and shift any elements found in the Stream to start at
        the end of the added elements.

        This presently does not shift elements that have durations
        that extend into the lowest insert position.

        >>> st1 = stream.Stream()
        >>> st1.insertAndShift(32, note.Note('B'))
        >>> st1.highestOffset
        32.0
        >>> st1.insertAndShift(32, note.Note('C'))
        >>> st1.highestOffset
        33.0
        >>> st1.show('text', addEndTimes=True)
        {32.0 - 33.0} <music21.note.Note C>
        {33.0 - 34.0} <music21.note.Note B>

        Let's insert an item at the beginning, note that
        since the C and B are not affected, they do not shift.

        >>> st1.insertAndShift(0, note.Note('D'))
        >>> st1.show('text', addEndTimes=True)
        {0.0 - 1.0} <music21.note.Note D>
        {32.0 - 33.0} <music21.note.Note C>
        {33.0 - 34.0} <music21.note.Note B>

        But if we insert something again at the beginning of the stream,
        everything after the first shifted note begins shifting, so the
        C and the B shift even though there is a gap there.  Normally
        there's no gaps in a stream, so this will not be a factor:

        >>> st1.insertAndShift(0, note.Note('E'))
        >>> st1.show('text', addEndTimes=True)
        {0.0 - 1.0} <music21.note.Note E>
        {1.0 - 2.0} <music21.note.Note D>
        {33.0 - 34.0} <music21.note.Note C>
        {34.0 - 35.0} <music21.note.Note B>

        In the single argument form with an object, inserts the element at its stored offset:

        >>> n1 = note.Note('C#')
        >>> n1.offset = 30.0
        >>> n2 = note.Note('D#')
        >>> n2.offset = 30.0
        >>> st1 = stream.Stream()
        >>> st1.insertAndShift(n1)
        >>> st1.insertAndShift(n2)  # will shift offset of n1
        >>> n1.getOffsetBySite(st1)
        31.0
        >>> n2.getOffsetBySite(st1)
        30.0
        >>> st1.show('text', addEndTimes=True)
        {30.0 - 31.0} <music21.note.Note D#>
        {31.0 - 32.0} <music21.note.Note C#>

        >>> st2 = stream.Stream()
        >>> st2.insertAndShift(40.0, n1)
        >>> st2.insertAndShift(40.0, n2)
        >>> n1.getOffsetBySite(st2)
        41.0

        In single argument form with a list, the list should contain pairs that alternate
        offsets and items; the method then, obviously, inserts the items
        at the specified offsets:

        >>> n1 = note.Note('G-')
        >>> n2 = note.Note('F-')
        >>> st3 = stream.Stream()
        >>> st3.insertAndShift([1.0, n1, 2.0, n2])
        >>> n1.getOffsetBySite(st3)
        1.0
        >>> n2.getOffsetBySite(st3)
        2.0
        >>> len(st3)
        2
        >>> st3.show('text', addEndTimes=True)
        {1.0 - 2.0} <music21.note.Note G->
        {2.0 - 3.0} <music21.note.Note F->

        N.B. -- using this method on a list assumes that you'll be inserting
        contiguous objects; you can't shift things that are separated, as this
        following FAILED example shows.

        >>> n1 = note.Note('G', type='half')
        >>> st4 = stream.Stream()
        >>> st4.repeatAppend(n1, 3)
        >>> st4.insertAndShift([2.0, note.Note('e'), 4.0, note.Note('f')])
        >>> st4.show('text')
        {0.0} <music21.note.Note G>
        {2.0} <music21.note.Note E>
        {4.0} <music21.note.Note F>
        {5.0} <music21.note.Note G>
        {7.0} <music21.note.Note G>

        As an FYI, there is no removeAndShift() function, so the opposite of
        insertAndShift(el) is remove(el, shiftOffsets=True).
        '''
        # need to find the highest time after the insert
        if itemOrNone is not None:  # we have an offset and an element
            insertObject = itemOrNone
            qL = insertObject.duration.quarterLength
            offset = offsetOrItemOrList
            lowestOffsetInsert = offset
            highestTimeInsert = offset + qL
        elif itemOrNone is None and isinstance(offsetOrItemOrList, list):
            # need to find which has the highest endtime (combined offset and dur)
            insertList = offsetOrItemOrList
            highestTimeInsert = 0.0
            lowestOffsetInsert = None
            i = 0
            while i < len(insertList):
                o = insertList[i]
                e = insertList[i + 1]
                qL = e.duration.quarterLength
                if o + qL > highestTimeInsert:
                    highestTimeInsert = o + qL
                if lowestOffsetInsert is None or o < lowestOffsetInsert:
                    lowestOffsetInsert = o
                i += 2
        else:  # using native offset
            # if hasattr(offsetOrItemOrList, 'duration'):
            insertObject = offsetOrItemOrList
            qL = insertObject.duration.quarterLength
            # should this be getOffsetBySite(None)?
            highestTimeInsert = insertObject.offset + qL
            lowestOffsetInsert = insertObject.offset

        # this shift is the additional time to move due to the duration
        # of the newly inserted elements

        # environLocal.printDebug(['insertAndShift()',
        #                         'adding one or more elements',
        #                         'lowestOffsetInsert', lowestOffsetInsert,
        #                         'highestTimeInsert', highestTimeInsert])

        # are not assuming that elements are ordered
        # use getElementAtOrAfter() in the future
        lowestElementToShift = None
        lowestGap = None
        for e in self._elements:
            o = self.elementOffset(e)
            # gap is distance from offset to insert point; tells if shift is
            # necessary
            gap = o - lowestOffsetInsert
            if gap < 0:  # no shifting necessary
                continue
            # only process elements whose offsets are after the lowest insert
            if lowestGap is None or gap < lowestGap:
                lowestGap = gap
                lowestElementToShift = e

        if lowestElementToShift is not None:
            lowestOffsetToShift = self.elementOffset(lowestElementToShift)
            shiftPos = highestTimeInsert - lowestOffsetToShift
        else:
            shiftPos = 0

        if shiftPos <= 0:
            pass  # no need to move any objects
        # See stream.tests.Test.testInsertAndShiftNoDuration
        #      clef insertion at offset 3 which gives shiftPos < 0
        else:
            # need to move all the elements already in this stream
            for e in self._elements:
                o = self.elementOffset(e)
                # gap is distance from offset to insert point; tells if shift is
                # necessary
                gap = o - lowestOffsetInsert
                # only process elements whose offsets are after the lowest insert
                if gap >= 0.0:
                    # environLocal.printDebug(['insertAndShift()', e, 'offset', o,
                    #                         'gap:', gap, 'shiftDur:', shiftDur,
                    #                         'shiftPos:', shiftPos, 'o+shiftDur', o+shiftDur,
                    #                         'o+shiftPos', o+shiftPos])

                    # need original offset, shiftDur, plus the distance from the start
                    self.coreSetElementOffset(e, o + shiftPos)
        # after shifting all the necessary elements, append new ones
        # these will not be in order
        self.coreElementsChanged()
        self.insert(offsetOrItemOrList, itemOrNone)

    # --------------------------------------------------------------------------
    # searching and replacing routines

    def setDerivationMethod(self,
                            derivationMethod: str,
                            recurse=False) -> None:
        '''
        Sets the .derivation.method for each element in the Stream
        if it has a .derivation object.

        >>> import copy
        >>> s = converter.parse('tinyNotation: 2/4 c2 d e f')
        >>> s2 = copy.deepcopy(s)
        >>> s2.recurse().notes[-1].derivation
        <Derivation of <music21.note.Note F> from <music21.note.Note F> via '__deepcopy__'>
        >>> s2.setDerivationMethod('exampleCopy', recurse=True)
        >>> s2.recurse().notes[-1].derivation
        <Derivation of <music21.note.Note F> from <music21.note.Note F> via 'exampleCopy'>

        Without recurse:

        >>> s = converter.parse('tinyNotation: 2/4 c2 d e f')
        >>> s2 = copy.deepcopy(s)
        >>> s2.setDerivationMethod('exampleCopy')
        >>> s2.recurse().notes[-1].derivation
        <Derivation of <music21.note.Note F> from <music21.note.Note F> via '__deepcopy__'>
        '''
        if not recurse:
            sIter = self.iter()
        else:
            sIter = self.recurse()

        for el in sIter:
            if el.derivation is not None:
                el.derivation.method = derivationMethod

    def replace(self,
                target: base.Music21Object,
                replacement: base.Music21Object,
                *,
                recurse: bool = False,
                allDerived: bool = True) -> None:
        '''
        Given a `target` object, replace it with
        the supplied `replacement` object.

        Does nothing if target cannot be found. Raises StreamException if replacement
        is already in the stream.

        If `allDerived` is True (as it is by default), all sites (stream) that
        this stream derives from and also
        have a reference for the replacement will be similarly changed.
        This is useful for altering both a flat and nested representation.

        >>> cSharp = note.Note('C#4')
        >>> s = stream.Stream()
        >>> s.insert(0, cSharp)
        >>> dFlat = note.Note('D-4')
        >>> s.replace(cSharp, dFlat)
        >>> s.show('t')
        {0.0} <music21.note.Note D->

        If allDerived is True then all streams that this stream comes from get changed
        (but not non-derived streams)

        >>> otherStream = stream.Stream()
        >>> otherStream.insert(0, dFlat)
        >>> f = note.Note('F4')
        >>> sf = s.flatten()
        >>> sf is not s
        True
        >>> sf.replace(dFlat, f, allDerived=True)
        >>> sf[0] is f
        True
        >>> s[0] is f
        True
        >>> otherStream[0] is dFlat
        True

        Note that it does not work the other way: if we made the replacement on `s`
        then `sf`, the flattened representation, would not be changed, since `s`
        does not derive from `sf` but vice-versa.

        With `recurse=True`, a stream can replace an element that is
        further down in the hierarchy.  First let's set up a
        nested score:

        >>> s = stream.Score()
        >>> p = stream.Part(id='part1')
        >>> s.append(p)
        >>> m = stream.Measure()
        >>> p.append(m)
        >>> cSharp = note.Note('C#4')
        >>> m.append(cSharp)
        >>> s.show('text')
        {0.0} <music21.stream.Part part1>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.note.Note C#>

        Now make a deep-nested replacement

        >>> dFlat = note.Note('D-4')
        >>> s.replace(cSharp, dFlat, recurse=True)
        >>> s.show('text')
        {0.0} <music21.stream.Part part1>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.note.Note D->

        * Changed by v5: `allTargetSites` renamed to `allDerived` -- only
          searches in derivation chain.
        * Changed in v5.3: `firstMatchOnly` removed -- impossible to have element
          in stream twice.  `recurse` and `shiftOffsets` changed to keywordOnly arguments
        * Changed in v6: recurse works
        * Changed in v7: raises `StreamException` if replacement is already in the stream.
        '''
        def replaceDerived(startSite=self):
            if not allDerived:
                return
            for derivedSite in startSite.derivation.chain():
                for subsite in derivedSite.recurse(streamsOnly=True, includeSelf=True):
                    if subsite in target.sites:
                        subsite.replace(target,
                                        replacement,
                                        recurse=recurse,
                                        allDerived=False)

        try:
            i = self.index(replacement)
        except StreamException:
            # good. now continue.
            pass
        else:
            raise StreamException(f'{replacement} already in {self}')

        try:
            i = self.index(target)
        except StreamException:
            if recurse:
                container = self.containerInHierarchy(target, setActiveSite=False)
                if container is not None:
                    container.replace(target, replacement, allDerived=allDerived)
                replaceDerived()
                if container is not None:
                    replaceDerived(startSite=container)
            return  # do nothing if no match

        eLen = len(self._elements)
        if i < eLen:
            target = self._elements[i]  # target may have been obj id; re-classing
            self._elements[i] = replacement
            # place the replacement at the old objects offset for this site
            self.coreSetElementOffset(replacement, self.elementOffset(target), addElement=True)
            replacement.sites.add(self)
        else:
            # target may have been obj id; reassign
            target = self._endElements[i - eLen]
            self._endElements[i - eLen] = replacement

            # noinspection PyTypeChecker
            self.coreSetElementOffset(replacement, OffsetSpecial.AT_END, addElement=True)
            replacement.sites.add(self)

        target.sites.remove(self)
        target.activeSite = None
        if id(target) in self._offsetDict:
            del self._offsetDict[id(target)]

        updateIsFlat = False
        if replacement.isStream:
            updateIsFlat = True
        # elements have changed: sort order may change b/c have diff classes
        self.coreElementsChanged(updateIsFlat=updateIsFlat)

        replaceDerived()

    def splitAtDurations(self, *, recurse=False) -> base._SplitTuple:
        '''
        Overrides base method :meth:`~music21.base.Music21Object.splitAtDurations`
        so that once each element in the stream having a complex duration is split
        into similar, shorter elements representing each duration component,
        the original element is actually replaced in the stream where it was found
        with those new elements.

        Returns a 1-tuple containing itself, for consistency with the superclass method.

        >>> s = stream.Stream()
        >>> s.insert(note.Note(quarterLength=5.0))
        >>> post = s.splitAtDurations()
        >>> post
        (<music21.stream.Stream 0x10955ceb0>,)
        >>> [n.duration for n in s]
        [<music21.duration.Duration 4.0>, <music21.duration.Duration 1.0>]

        Unless `recurse=True`, notes in substreams will not be found.

        >>> s2 = stream.Score()
        >>> p = stream.Part([note.Note(quarterLength=5)])
        >>> s2.append(p)
        >>> s2.splitAtDurations()
        (<music21.stream.Score 0x10d12f100>,)
        >>> [n.duration for n in s2.recurse().notes]
        [<music21.duration.Duration 5.0>]
        >>> s2.splitAtDurations(recurse=True)
        (<music21.stream.Score 0x10d12f100>,)
        >>> [n.duration for n in s2.recurse().notes]
        [<music21.duration.Duration 4.0>, <music21.duration.Duration 1.0>]

        `recurse=True` should not be necessary to find elements in streams
        without substreams, such as a loose Voice:

        >>> v = stream.Voice([note.Note(quarterLength=5.5)], id=1)
        >>> v.splitAtDurations()
        (<music21.stream.Voice 1>,)
        >>> [n.duration for n in v.notes]
        [<music21.duration.Duration 4.0>, <music21.duration.Duration 1.5>]

        But a Voice in a Measure (most common) will not be found without `recurse`:

        >>> m = stream.Measure()
        >>> v2 = stream.Voice([note.Note(quarterLength=5.25)])
        >>> m.insert(v2)
        >>> m.splitAtDurations()
        (<music21.stream.Measure 0 offset=0.0>,)
        >>> [n.duration for n in m.recurse().notes]
        [<music21.duration.Duration 5.25>]

        For any spanner containing the element being removed, the first or last of the
        replacing components replaces the removed element
        (according to whether it was first or last in the spanner.)

        >>> s3 = stream.Stream()
        >>> n1 = note.Note(quarterLength=5)
        >>> n2 = note.Note(quarterLength=5)
        >>> s3.append([n1, n2])
        >>> s3.insert(0, spanner.Slur([n1, n2]))
        >>> post = s3.splitAtDurations()
        >>> s3.spanners.first().getFirst() is n1
        False
        >>> s3.spanners.first().getFirst().duration
        <music21.duration.Duration 4.0>
        >>> s3.spanners.first().getLast().duration
        <music21.duration.Duration 1.0>

        Does not act on rests where `.fullMeasure` is True or 'always',
        nor when `.fullMeasure` is 'auto' and the duration equals the `.barDuration`.
        This is because full measure rests are usually represented
        as a single whole rest regardless of their duration.

        >>> r = note.Rest(quarterLength=5.0)
        >>> r.fullMeasure = 'auto'
        >>> v = stream.Voice(r)
        >>> m = stream.Measure(v)
        >>> result = m.splitAtDurations(recurse=True)
        >>> list(result[0][note.Rest])
        [<music21.note.Rest 5ql>]

        Here is a rest that doesn't fill the measure:

        >>> m.insert(0, meter.TimeSignature('6/4'))
        >>> result = m.splitAtDurations(recurse=True)
        >>> list(result[0][note.Rest])
        [<music21.note.Rest whole>, <music21.note.Rest quarter>]

        But by calling it a full-measure rest, we won't try to split it:

        >>> r2 = note.Rest(quarterLength=5.0)
        >>> r2.fullMeasure = True
        >>> m2 = stream.Measure(r2)
        >>> m2.insert(0, meter.TimeSignature('6/4'))
        >>> result = m2.splitAtDurations()
        >>> list(result[0][note.Rest])
        [<music21.note.Rest 5ql>]
        '''

        def processContainer(container: Stream):
            for complexObj in container.getElementsNotOfClass(['Stream', 'Variant', 'Spanner']):
                if complexObj.duration.type != 'complex':
                    continue
                if isinstance(complexObj, note.Rest) and complexObj.fullMeasure in (True, 'always'):
                    continue
                if isinstance(complexObj, note.Rest) and complexObj.fullMeasure == 'auto':
                    if (isinstance(container, Measure)
                            and (complexObj.duration == container.barDuration)):
                        continue
                    elif ('Voice' in container.classes
                          and container.activeSite
                          and container.activeSite.isMeasure
                          and complexObj.duration == container.activeSite.barDuration
                          ):
                        continue

                insertPoint = complexObj.offset
                objList = complexObj.splitAtDurations()

                container.replace(complexObj, objList[0])
                insertPoint += objList[0].quarterLength

                for subsequent in objList[1:]:
                    container.insert(insertPoint, subsequent)
                    insertPoint += subsequent.quarterLength

                # Replace elements in spanners
                for sp in complexObj.getSpannerSites():
                    if sp.getFirst() is complexObj:
                        sp.replaceSpannedElement(complexObj, objList[0])
                    if sp.getLast() is complexObj:
                        sp.replaceSpannedElement(complexObj, objList[-1])

                container.streamStatus.beams = False

        # Handle "loose" objects in self (usually just Measure or Voice)
        processContainer(self)
        # Handle inner streams
        if recurse:
            for innerStream in self.recurse(
                    includeSelf=False, streamsOnly=True, restoreActiveSites=True):
                processContainer(innerStream)

        return base._SplitTuple((self,))

    def splitAtQuarterLength(self,
                             quarterLength,
                             *,
                             retainOrigin=True,
                             addTies=True,
                             displayTiedAccidentals=False,
                             searchContext=True):
        '''
        This method overrides the method on Music21Object to provide
        similar functionality for Streams.

        Most arguments are passed to Music21Object.splitAtQuarterLength.

        * Changed in v7: all but quarterLength are keyword only
        '''
        quarterLength = opFrac(quarterLength)
        if retainOrigin:
            sLeft = self
        else:
            sLeft = self.coreCopyAsDerivation('splitAtQuarterLength')
        # create empty container for right-hand side
        sRight = self.__class__()

        # if this is a Measure or Part, transfer clefs, ts, and key
        if sLeft.isMeasure:
            timeSignatures = sLeft.getTimeSignatures(
                searchContext=searchContext,
                returnDefault=False,
            )
            if timeSignatures:
                sRight.keySignature = copy.deepcopy(timeSignatures[0])
            if searchContext:
                keySignatures = sLeft.getContextByClass(key.KeySignature)
                if keySignatures is not None:
                    keySignatures = [keySignatures]
            else:
                keySignatures = sLeft.getElementsByClass(key.KeySignature)
            if keySignatures:
                sRight.keySignature = copy.deepcopy(keySignatures[0])
            endClef = sLeft.getContextByClass(clef.Clef)
            if endClef is not None:
                sRight.clef = copy.deepcopy(endClef)

        if quarterLength > sLeft.highestTime:  # nothing to do
            return sLeft, sRight

        # use quarterLength as start time
        targets = sLeft.getElementsByOffset(
            quarterLength,
            sLeft.highestTime,
            includeEndBoundary=True,
            mustFinishInSpan=False,
            includeElementsThatEndAtStart=False,
            mustBeginInSpan=False
        )

        targetSplit = []
        targetMove = []
        # find all those that need to split v. those that need to be moved
        for target in targets:
            # if target starts before the boundary, it needs to be split
            if sLeft.elementOffset(target) < quarterLength:
                targetSplit.append(target)
            else:
                targetMove.append(target)

        # environLocal.printDebug(['split', targetSplit, 'move', targetMove])

        for target in targetSplit:
            # must retain original, as a deepcopy, if necessary, has
            # already been made

            # the split point needs to be relative to this element's start
            qlSplit = quarterLength - sLeft.elementOffset(target)
            unused_eLeft, eRight = target.splitAtQuarterLength(
                qlSplit,
                retainOrigin=True,
                addTies=addTies,
                displayTiedAccidentals=displayTiedAccidentals)
            # do not need to insert eLeft, as already positioned and
            # altered in-place above
            # it is assumed that anything cut will start at zero
            sRight.insert(0, eRight)

        for target in targetMove:
            sRight.insert(target.getOffsetBySite(sLeft) - quarterLength, target)
            sLeft.remove(target)

        return sLeft, sRight

    # --------------------------------------------------------------------------
    def recurseRepr(self,
                    *,
                    prefixSpaces=0,
                    addBreaks=True,
                    addIndent=True,
                    addEndTimes=False,
                    useMixedNumerals=False) -> str:
        '''
        Used by .show('text') to display a stream's contents with offsets.

        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> s3 = stream.Stream()
        >>> n1 = note.Note()
        >>> s3.append(n1)
        >>> s2.append(s3)
        >>> s1.append(s2)
        >>> post = s1.recurseRepr(addBreaks=False, addIndent=False)
        >>> post
        '{0.0} <music21.stream.Stream ...> / {0.0} <...> / {0.0} <music21.note.Note C>'

        Made public in v7.  Always calls on self.
        '''
        def singleElement(in_element,
                          in_indent,
                          ) -> str:
            offGet = in_element.getOffsetBySite(self)
            if useMixedNumerals:
                off = common.mixedNumeral(offGet)
            else:
                off = common.strTrimFloat(offGet)
            if addEndTimes is False:
                return in_indent + '{' + off + '} ' + repr(in_element)
            else:
                ql = offGet + in_element.duration.quarterLength
                if useMixedNumerals:
                    qlStr = common.mixedNumeral(ql)
                else:
                    qlStr = common.strTrimFloat(ql)
                return in_indent + '{' + off + ' - ' + qlStr + '} ' + repr(in_element)

        msg = []
        insertSpaces = 4
        for element in self:
            if addIndent:
                indent = ' ' * prefixSpaces
            else:
                indent = ''

            if isinstance(element, Stream):
                msg.append(singleElement(element, indent))
                msg.append(
                    element.recurseRepr(prefixSpaces=prefixSpaces + insertSpaces,
                                        addBreaks=addBreaks,
                                        addIndent=addIndent,
                                        addEndTimes=addEndTimes,
                                        useMixedNumerals=useMixedNumerals)
                )
            else:
                msg.append(singleElement(element, indent))

        if addBreaks:
            msgStr = '\n'.join(msg)
        else:  # use slashes with spaces
            msgStr = ' / '.join(msg)
        return msgStr

    def _reprText(self, *, addEndTimes=False, useMixedNumerals=False, **keywords) -> str:
        '''
        Return a text representation. This method can be overridden by
        subclasses to provide alternative text representations.

        This is used by .show('text')
        '''
        return self.recurseRepr(addEndTimes=addEndTimes,
                                useMixedNumerals=useMixedNumerals)

    def _reprTextLine(self, *, addEndTimes=False, useMixedNumerals=False) -> str:
        '''
        Return a text representation without line breaks.
        This method can be overridden by subclasses to
        provide alternative text representations.
        '''
        return self.recurseRepr(addEndTimes=addEndTimes,
                                useMixedNumerals=useMixedNumerals,
                                addBreaks=False,
                                addIndent=False)

    # --------------------------------------------------------------------------
    # display methods; in the same manner as show() and write()

    def plot(self,
             plotFormat: str | None = None,
             xValue: str | None = None,
             yValue: str | None = None,
             zValue: str | None = None,
             *,
             returnInNotebook: bool = False,
             **keywords):
        '''
        Given a method and keyword configuration arguments, create and display a plot.

        Note: plot() requires the Python package matplotlib to be installed.

        For details on arguments this function takes, see
        :ref:`User's Guide, Chapter 22: Graphing <usersGuide_22_graphing>`.

        >>> s = corpus.parse('demos/two-parts.xml') #_DOCS_HIDE
        >>> thePlot = s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
        >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
        >>> #_DOCS_SHOW thePlot = s.plot('pianoroll')

        .. image:: images/HorizontalBarPitchSpaceOffset.*
            :width: 600

        By default, a plot is returned in normal Python environments, but not
        in Jupyter notebook/JupyterLab/Google Colab.  The
        keyword `returnInNotebook` if True returns a plot no matter what.

        Changed in v9: Changed default for return in notebook, and added
          `returnInNotebook` keyword based on changes to recent Jupyter and
          similar releases.
        '''
        # import is here to avoid import of matplotlib problems
        from music21 import graph
        # first ordered arg can be method type
        out = graph.plotStream(
            self,
            plotFormat,
            xValue=xValue,
            yValue=yValue,
            zValue=zValue,
            **keywords
        )
        if returnInNotebook or not common.runningInNotebook():
            return out
        out.run()
        return None


    def analyze(self, method: str, **keywords):
        '''
        Runs a particular analytical method on the contents of the
        stream to find its ambitus (range) or key.

        *  ambitus -- runs :class:`~music21.analysis.discrete.Ambitus`
        *  key -- runs :class:`~music21.analysis.discrete.KrumhanslSchmuckler`

        Some of these methods can take additional arguments.  For details on
        these arguments, see
        :func:`~music21.analysis.discrete.analyzeStream`.

        Example:

        >>> s = corpus.parse('bach/bwv66.6')
        >>> s.analyze('ambitus')
        <music21.interval.Interval m21>
        >>> s.analyze('key')
        <music21.key.Key of f# minor>

        Example: music21 allows you to automatically run an
        analysis to get the key of a piece or excerpt not
        based on the key signature but instead on the
        frequency with which some notes are used as opposed
        to others (first described by Carol Krumhansl).  For
        instance, a piece with mostly Cs and Gs, some Fs,
        and Ds, but fewer G#s, C#s, etc. is more likely to
        be in the key of C major than in D-flat major
        (or A minor, etc.).  You can easily get this analysis
        from a stream by running:

        >>> myStream = corpus.parse('luca/gloria')
        >>> analyzedKey = myStream.analyze('key')
        >>> analyzedKey
        <music21.key.Key of F major>

        analyzedKey is a :class:`~music21.key.Key`
        object with a few extra parameters.
        correlationCoefficient shows how well this key fits the
        profile of a piece in that key:

        >>> analyzedKey.correlationCoefficient
        0.86715...

        `alternateInterpretations` is a list of the other
        possible interpretations sorted from most likely to least:

        >>> analyzedKey.alternateInterpretations
        [<music21.key.Key of d minor>,
         <music21.key.Key of C major>,
         <music21.key.Key of g minor>,
         ...]

        Each of these can be examined in turn to see its correlation coefficient:

        >>> analyzedKey.alternateInterpretations[1].correlationCoefficient
        0.788528...
        >>> analyzedKey.alternateInterpretations[22].correlationCoefficient
        -0.86728...
        '''

        from music21.analysis import discrete
        # pass this stream to the analysis procedure
        return discrete.analyzeStream(self, method, **keywords)

    # --------------------------------------------------------------------------
    # methods that act on individual elements without requiring
    # coreElementsChanged to fire
    def addGroupForElements(self,
                            group: str,
                            classFilter=None,
                            *,
                            recurse=False,
                            setActiveSite=True):
        '''
        Add the group to the groups attribute of all elements.
        if `classFilter` is set then only those elements whose objects
        belong to a certain class (or for Streams which are themselves of
        a certain class) are set.

        >>> a = stream.Stream()
        >>> a.repeatAppend(note.Note('A-'), 30)
        >>> a.repeatAppend(note.Rest(), 30)
        >>> a.addGroupForElements('flute')
        >>> a[0].groups
        ['flute']
        >>> a.addGroupForElements('quietTime', note.Rest)
        >>> a[0].groups
        ['flute']
        >>> a[50].groups
        ['flute', 'quietTime']
        >>> a[1].groups.append('quietTime')  # set one note to it
        >>> a[1].step = 'B'
        >>> b = a.getElementsByGroup('quietTime')
        >>> len(b)
        31
        >>> c = b.getElementsByClass(note.Note)
        >>> len(c)
        1
        >>> c[0].name
        'B-'

        If recurse is True then all sub-elements will get the group:

        >>> s = converter.parse('tinyNotation: 4/4 c4 d e f g a b- b')
        >>> s.addGroupForElements('scaleNote', 'Note')
        >>> s.recurse().notes[3].groups
        []
        >>> s.addGroupForElements('scaleNote', 'Note', recurse=True)
        >>> s.recurse().notes[3].groups
        ['scaleNote']

        No group will be added more than once:

        >>> s.addGroupForElements('scaleNote', 'Note', recurse=True)
        >>> s.recurse().notes[3].groups
        ['scaleNote']

        * New in v6.7.1: recurse
        '''
        sIterator = self.iter() if not recurse else self.recurse()
        if classFilter is not None:
            sIterator = sIterator.addFilter(filters.ClassFilter(classFilter))
        sIterator.restoreActiveSites = not setActiveSite
        for el in sIterator:
            if group not in el.groups:
                el.groups.append(group)

    # --------------------------------------------------------------------------
    # getElementsByX(self): anything that returns a collection of Elements
    #  formerly always returned a Stream; turning to Iterators in September 2015

    @overload
    def getElementsByClass(self,
                           classFilterList: str | Iterable[str]
                           ) -> iterator.StreamIterator[M21ObjType]:
        # Remove all dummy code once Astroid #1015 is fixed
        x: iterator.StreamIterator[M21ObjType] = self.iter()
        return x  # dummy code

    @overload
    def getElementsByClass(self,
                           classFilterList: type[ChangedM21ObjType]
                           ) -> iterator.StreamIterator[ChangedM21ObjType]:
        x: iterator.StreamIterator[ChangedM21ObjType] = (
            self.iter().getElementsByClass(classFilterList)
        )
        return x  # dummy code

    @overload
    def getElementsByClass(self,
                           classFilterList: Iterable[type[ChangedM21ObjType]]
                           ) -> iterator.StreamIterator[M21ObjType]:
        x: iterator.StreamIterator[M21ObjType] = self.iter()
        return x  # dummy code

    def getElementsByClass(self,
                           classFilterList: t.Union[
                               str,
                               Iterable[str],
                               type[ChangedM21ObjType],
                               Iterable[type[ChangedM21ObjType]],
                           ],
                           ) -> t.Union[iterator.StreamIterator[M21ObjType],
                                        iterator.StreamIterator[ChangedM21ObjType]]:
        '''
        Return a StreamIterator that will iterate over Elements that match one
        or more classes in the `classFilterList`. A single class
        can also be used for the `classFilterList` parameter instead of a List.

        >>> a = stream.Score()
        >>> a.repeatInsert(note.Rest(), list(range(10)))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.getElementsByClass(note.Note)
        >>> found
        <music21.stream.iterator.StreamIterator for Score:0x118d20710 @:0>

        >>> len(found)
        4
        >>> found[0].pitch.accidental.name
        'sharp'

        >>> foundStream = found.stream()
        >>> isinstance(foundStream, stream.Score)
        True


        Notice that we do not find elements that are in
        sub-streams of the main Stream.  We'll add 15 more rests
        in a sub-stream, and they won't be found:

        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), list(range(15)))
        >>> a.insert(b)
        >>> found = a.getElementsByClass(note.Rest)
        >>> len(found)
        10

        To find them either (1) use `.flatten()` to get at everything:

        >>> found = a.flatten().getElementsByClass(note.Rest)
        >>> len(found)
        25

        Or, (2) recurse over the main stream and call .getElementsByClass
        on each one.  Notice that the first subStream is actually the outermost
        Stream:

        >>> totalFound = 0
        >>> for subStream in a.recurse(streamsOnly=True, includeSelf=True):
        ...     found = subStream.getElementsByClass(note.Rest)
        ...     totalFound += len(found)
        >>> totalFound
        25

        The class name of the Stream created is the same as the original:

        >>> found = a.getElementsByClass(note.Note).stream()
        >>> found.__class__.__name__
        'Score'

        ...except if `returnStreamSubClass` is False, which makes the method
        return a generic Stream:

        >>> found = a.getElementsByClass(note.Rest).stream(returnStreamSubClass=False)
        >>> found.__class__.__name__
        'Stream'


        Make a list from a StreamIterator:

        >>> foundList = list(a.recurse().getElementsByClass(note.Rest))
        >>> len(foundList)
        25
        '''
        return self.iter().getElementsByClass(classFilterList)

    def getElementsNotOfClass(self, classFilterList) -> iterator.StreamIterator:
        '''
        Return a list of all Elements that do not
        match the one or more classes in the `classFilterList`.

        In lieu of a list, a single class can be used as the `classFilterList` parameter.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Rest(), list(range(10)))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.getElementsNotOfClass(note.Note)
        >>> len(found)
        10

        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), list(range(15)))
        >>> a.insert(b)

        Here, it gets elements from within a stream
        this probably should not do this, as it is one layer lower

        >>> found = a.flatten().getElementsNotOfClass(note.Rest)
        >>> len(found)
        4
        >>> found = a.flatten().getElementsNotOfClass(note.Note)
        >>> len(found)
        25
        '''
        return self.iter().getElementsNotOfClass(classFilterList, returnClone=False)

    def getElementsByGroup(self, groupFilterList) -> iterator.StreamIterator:
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
        >>> tboneSubStream = s1.getElementsByGroup('trombone')
        >>> for thisNote in tboneSubStream:
        ...     print(thisNote.name)
        C
        D
        >>> tubaSubStream = s1.getElementsByGroup('tuba')
        >>> for thisNote in tubaSubStream:
        ...     print(thisNote.name)
        D
        E

        OMIT_FROM_DOCS
        # TODO: group comparisons are not YET case insensitive.
        '''
        return self.iter().getElementsByGroup(groupFilterList, returnClone=False)

    def getElementById(self, elementId) -> base.Music21Object | None:
        '''
        Returns the first encountered element for a given id. Return None
        if no match. Note: this uses the id attribute stored on elements,
        which may not be the same as id(e).

        >>> a = stream.Stream()
        >>> ew = note.Note()
        >>> a.insert(0, ew)
        >>> a[0].id = 'green'
        >>> None == a.getElementById(3)
        True
        >>> a.getElementById('green').id
        'green'
        >>> a.getElementById('Green').id  # case does not matter
        'green'

        Getting an element by getElementById changes its activeSite

        >>> b = stream.Stream()
        >>> b.append(ew)
        >>> ew.activeSite is b
        True
        >>> ew2 = a.getElementById('green')
        >>> ew2 is ew
        True
        >>> ew2.activeSite is a
        True
        >>> ew.activeSite is a
        True

        * Changed in v7: remove classFilter.
        '''
        sIterator = self.iter().addFilter(filters.IdFilter(elementId))
        for e in sIterator:
            return e
        return None

    def getElementsByOffset(
        self,
        offsetStart,
        offsetEnd=None,
        *,
        includeEndBoundary=True,
        mustFinishInSpan=False,
        mustBeginInSpan=True,
        includeElementsThatEndAtStart=True,
        classList=None
    ) -> iterator.StreamIterator:
        '''
        Returns a StreamIterator containing all Music21Objects that
        are found at a certain offset or within a certain
        offset time range (given the `offsetStart` and (optional) `offsetEnd` values).

        There are several attributes that govern how this range is
        determined:


        If `mustFinishInSpan` is True then an event that begins
        between offsetStart and offsetEnd but which ends after offsetEnd
        will not be included.  The default is False.


        For instance, a half note at offset 2.0 will be found in
        getElementsByOffset(1.5, 2.5) or getElementsByOffset(1.5, 2.5,
        mustFinishInSpan=False) but not by getElementsByOffset(1.5, 2.5,
        mustFinishInSpan=True).

        The `includeEndBoundary` option determines if an element
        begun just at the offsetEnd should be included.  For instance,
        the half note at offset 2.0 above would be found by
        getElementsByOffset(0, 2.0) or by getElementsByOffset(0, 2.0,
        includeEndBoundary=True) but not by getElementsByOffset(0, 2.0,
        includeEndBoundary=False).

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
        mustBeginInSpan=True) but it would be found by
        getElementsByOffset(3.0, 3.5, mustBeginInSpan=False)

        Setting includeElementsThatEndAtStart to False is useful for zeroLength
        searches that set mustBeginInSpan == False to not catch notes that were
        playing before the search but that end just before the end of the search type.
        This setting is *ignored* for zero-length searches.
        See the code for allPlayingWhileSounding for a demonstration.

        This chart and the examples below demonstrate the various
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
        >>> out1 = st1.getElementsByOffset(2)
        >>> len(out1)
        1
        >>> out1[0].step
        'D'

        >>> out2 = st1.getElementsByOffset(1, 3)
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = st1.getElementsByOffset(1, 3, mustFinishInSpan=True)
        >>> len(out3)
        0
        >>> out4 = st1.getElementsByOffset(1, 2)
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = st1.getElementsByOffset(1, 2, includeEndBoundary=False)
        >>> len(out5)
        0
        >>> out6 = st1.getElementsByOffset(1, 2, includeEndBoundary=False, mustBeginInSpan=False)
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = st1.getElementsByOffset(1, 3, mustBeginInSpan=False)
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']


        Note, that elements that end at the start offset are included if mustBeginInSpan is False

        >>> out8 = st1.getElementsByOffset(2, 4, mustBeginInSpan=False)
        >>> len(out8)
        2
        >>> [el.step for el in out8]
        ['C', 'D']

        To change this behavior set includeElementsThatEndAtStart=False

        >>> out9 = st1.getElementsByOffset(2, 4,
        ...                     mustBeginInSpan=False, includeElementsThatEndAtStart=False)
        >>> len(out9)
        1
        >>> [el.step for el in out9]
        ['D']


        Note how zeroLengthSearches implicitly set includeElementsThatEndAtStart=False.
        These two are the same:

        >>> out1 = st1.getElementsByOffset(2, mustBeginInSpan=False)
        >>> out2 = st1.getElementsByOffset(2, 2, mustBeginInSpan=False)
        >>> len(out1) == len(out2) == 1
        True
        >>> out1[0] is out2[0] is n2
        True

        But this is different:

        >>> out3 = st1.getElementsByOffset(2, 2.1, mustBeginInSpan=False)
        >>> len(out3)
        2
        >>> out3[0] is n0
        True

        Explicitly setting includeElementsThatEndAtStart=False does not get the
        first note:

        >>> out4 = st1.getElementsByOffset(2, 2.1, mustBeginInSpan=False,
        ...                                includeElementsThatEndAtStart=False)
        >>> len(out4)
        1
        >>> out4[0] is n2
        True



        Testing multiple zero-length elements with mustBeginInSpan:

        >>> tc = clef.TrebleClef()
        >>> ts = meter.TimeSignature('4/4')
        >>> ks = key.KeySignature(2)
        >>> s = stream.Stream()
        >>> s.insert(0.0, tc)
        >>> s.insert(0.0, ts)
        >>> s.insert(0.0, ks)
        >>> len(s.getElementsByOffset(0.0, mustBeginInSpan=True))
        3
        >>> len(s.getElementsByOffset(0.0, mustBeginInSpan=False))
        3

        OMIT_FROM_DOCS

        >>> a = stream.Stream()
        >>> n = note.Note('G')
        >>> n.quarterLength = 0.5
        >>> a.repeatInsert(n, list(range(8)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(a, [0, 3, 6])
        >>> c = b.getElementsByOffset(2, 6.9)
        >>> len(c)
        2
        >>> c = b.flatten().getElementsByOffset(2, 6.9)
        >>> len(c)
        10


        Same test as above, but with floats

        >>> out1 = st1.getElementsByOffset(2.0)
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = st1.getElementsByOffset(1.0, 3.0)
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = st1.getElementsByOffset(1.0, 3.0, mustFinishInSpan=True)
        >>> len(out3)
        0
        >>> out3b = st1.getElementsByOffset(0.0, 3.001, mustFinishInSpan=True)
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'
        >>> out3b = st1.getElementsByOffset(1.0, 3.001,
        ...                                 mustFinishInSpan=True, mustBeginInSpan=False)
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'


        >>> out4 = st1.getElementsByOffset(1.0, 2.0)
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = st1.getElementsByOffset(1.0, 2.0, includeEndBoundary=False)
        >>> len(out5)
        0
        >>> out6 = st1.getElementsByOffset(1.0, 2.0,
        ...                                includeEndBoundary=False, mustBeginInSpan=False)
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = st1.getElementsByOffset(1.0, 3.0, mustBeginInSpan=False)
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']

        * Changed in v5.5: all arguments changing behavior are keyword only.
        '''
        sIterator = self.iter().getElementsByOffset(
            offsetStart=offsetStart,
            offsetEnd=offsetEnd,
            includeEndBoundary=includeEndBoundary,
            mustFinishInSpan=mustFinishInSpan,
            mustBeginInSpan=mustBeginInSpan,
            includeElementsThatEndAtStart=includeElementsThatEndAtStart)
        if classList is not None:
            sIterator = sIterator.getElementsByClass(classList)
        return sIterator

    def getElementAtOrBefore(self, offset, classList=None) -> base.Music21Object | None:
        # noinspection PyShadowingNames
        '''
        Given an offset, find the element at this offset,
        or with the offset less than and nearest to.

        Return one element or None if no elements are at or preceded by this
        offset.

        If the `classList` parameter is used, it should be a
        list of class names or strings, and only objects that
        are instances of
        these classes or subclasses of these classes will be returned.

        >>> stream1 = stream.Stream()
        >>> x = note.Note('D4')
        >>> x.id = 'x'
        >>> y = note.Note('E4')
        >>> y.id = 'y'
        >>> z = note.Rest()
        >>> z.id = 'z'

        >>> stream1.insert(20, x)
        >>> stream1.insert(10, y)
        >>> stream1.insert( 0, z)

        >>> b = stream1.getElementAtOrBefore(21)
        >>> b.offset, b.id
        (20.0, 'x')

        >>> b = stream1.getElementAtOrBefore(19)
        >>> b.offset, b.id
        (10.0, 'y')

        >>> b = stream1.getElementAtOrBefore(0)
        >>> b.offset, b.id
        (0.0, 'z')
        >>> b = stream1.getElementAtOrBefore(0.1)
        >>> b.offset, b.id
        (0.0, 'z')


        You can give a list of acceptable classes to return, and non-matching
        elements will be ignored

        >>> c = stream1.getElementAtOrBefore(100, [clef.TrebleClef, note.Rest])
        >>> c.offset, c.id
        (0.0, 'z')

        Getting an object via getElementAtOrBefore sets the activeSite
        for that object to the Stream, and thus sets its offset

        >>> stream2 = stream.Stream()
        >>> stream2.insert(100.5, x)
        >>> x.offset
        100.5
        >>> d = stream1.getElementAtOrBefore(20)
        >>> d is x
        True
        >>> x.activeSite is stream1
        True
        >>> x.offset
        20.0


        If no element is before the offset, returns None

        >>> s = stream.Stream()
        >>> s.insert(10, note.Note('E'))
        >>> print(s.getElementAtOrBefore(9))
        None

        The sort order of returned items is the reverse
        of the normal sort order, so that, for instance,
        if there's a clef and a note at offset 20,
        getting the object before offset 21 will give
        you the note, and not the clef, since clefs
        sort before notes:

        >>> clef1 = clef.BassClef()
        >>> stream1.insert(20, clef1)
        >>> e = stream1.getElementAtOrBefore(21)
        >>> e
        <music21.note.Note D>
        '''
        # NOTE: this is a performance critical method

        # TODO: switch to trees
        candidates = []
        offset = opFrac(offset)
        nearestTrailSpan = offset  # start with max time

        sIterator = self.iter()
        if classList:
            sIterator = sIterator.getElementsByClass(classList)

        # need both _elements and _endElements
        for e in sIterator:
            span = opFrac(offset - self.elementOffset(e))
            # environLocal.printDebug(['e span check', span, 'offset', offset,
            #   'e.offset', e.offset, 'self.elementOffset(e)', self.elementOffset(e), 'e', e])
            if span < 0:
                continue
            elif span == 0:
                candidates.append((span, e))
                nearestTrailSpan = span
            else:
                # do this comparison because may be out of order
                if span <= nearestTrailSpan:
                    candidates.append((span, e))
                    nearestTrailSpan = span
        # environLocal.printDebug(['getElementAtOrBefore(), e candidates', candidates])
        if candidates:
            candidates.sort(key=lambda x: (-1 * x[0], x[1].sortTuple()))
            # TODO: this sort has side effects -- see ICMC2011 -- sorting clef vs. note, etc.
            self.coreSelfActiveSite(candidates[-1][1])
            return candidates[-1][1]
        else:
            return None

    def getElementBeforeOffset(self, offset, classList=None) -> base.Music21Object | None:
        '''
        Get element before (and not at) a provided offset.

        If the `classList` parameter is used, it should be a
        list of class names or strings, and only objects that
        are instances of
        these classes or subclasses of these classes will be returned.

        >>> stream1 = stream.Stream()
        >>> x = note.Note('D4')
        >>> x.id = 'x'
        >>> y = note.Note('E4')
        >>> y.id = 'y'
        >>> z = note.Rest()
        >>> z.id = 'z'
        >>> stream1.insert(20, x)
        >>> stream1.insert(10, y)
        >>> stream1.insert( 0, z)

        >>> b = stream1.getElementBeforeOffset(21)
        >>> b.offset, b.id
        (20.0, 'x')
        >>> b = stream1.getElementBeforeOffset(20)
        >>> b.offset, b.id
        (10.0, 'y')

        >>> b = stream1.getElementBeforeOffset(10)
        >>> b.offset, b.id
        (0.0, 'z')

        >>> b = stream1.getElementBeforeOffset(0)
        >>> b is None
        True
        >>> b = stream1.getElementBeforeOffset(0.1)
        >>> b.offset, b.id
        (0.0, 'z')

        >>> w = note.Note('F4')
        >>> w.id = 'w'
        >>> stream1.insert( 0, w)

        This should get w because it was inserted last.

        >>> b = stream1.getElementBeforeOffset(0.1)
        >>> b.offset, b.id
        (0.0, 'w')

        But if we give it a lower priority than z then z will appear first.

        >>> w.priority = z.priority - 1
        >>> b = stream1.getElementBeforeOffset(0.1)
        >>> b.offset, b.id
        (0.0, 'z')
        '''
        # NOTE: this is a performance critical method
        candidates = []
        offset = opFrac(offset)
        nearestTrailSpan = offset  # start with max time

        sIterator = self.iter()
        if classList:
            sIterator = sIterator.getElementsByClass(classList)

        for e in sIterator:
            span = opFrac(offset - self.elementOffset(e))
            # environLocal.printDebug(['e span check', span, 'offset', offset,
            #     'e.offset', e.offset, 'self.elementOffset(e)', self.elementOffset(e), 'e', e])
            # by forcing <= here, we are sure to get offsets not at zero
            if span <= 0:  # the e is after this offset
                continue
            else:  # do this comparison because may be out of order
                if span <= nearestTrailSpan:
                    candidates.append((span, e))
                    nearestTrailSpan = span
        # environLocal.printDebug(['getElementBeforeOffset(), e candidates', candidates])
        if candidates:
            candidates.sort(key=lambda x: (-1 * x[0], x[1].sortTuple()))
            self.coreSelfActiveSite(candidates[-1][1])
            return candidates[-1][1]
        else:
            return None

    # def getElementAfterOffset(self, offset, classList=None):
    #    '''
    #    Get element after a provided offset
    #
    #    TODO: write this
    #    '''
    #    raise TypeError('not yet implemented')
    #
    #
    # def getElementBeforeElement(self, element, classList=None):
    #    '''
    #    given an element, get the element before
    #
    #    TODO: write this
    #    '''
    #    raise TypeError('not yet implemented')

    def getElementAfterElement(self, element, classList=None):
        '''
        Given an element, get the next element.  If classList is specified,
        check to make sure that the element is an instance of the class list

        >>> st1 = stream.Stream()
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> r3 = note.Rest()
        >>> st1.append([n1, n2, r3])
        >>> t2 = st1.getElementAfterElement(n1)
        >>> t2 is n2
        True
        >>> t3 = st1.getElementAfterElement(t2)
        >>> t3 is r3
        True
        >>> t4 = st1.getElementAfterElement(t3)
        >>> t4

        >>> t5 = st1.getElementAfterElement(n1, [note.Rest])
        >>> t5
        <music21.note.Rest quarter>
        >>> t5 is r3
        True
        >>> t6 = st1.getElementAfterElement(n1, [note.Rest, note.Note])
        >>> t6 is n2
        True

        >>> t7 = st1.getElementAfterElement(r3)
        >>> t7 is None
        True


        If the element is not in the stream, it will raise a StreamException:

        >>> st1.getElementAfterElement(note.Note('C#'))
        Traceback (most recent call last):
        music21.exceptions21.StreamException:
            cannot find object (<music21.note.Note C#>) in Stream

        '''
        if classList is not None:
            classSet = set(classList)
        else:
            classSet = None

        # index() ultimately does an autoSort check, so no check here or
        # sorting is necessary
        # also, this will raise a StreamException if element is not in the Stream
        elPos = self.index(element)

        # store once as a property call concatenates
        elements = self.elements
        if classList is None:
            if elPos == len(elements) - 1:
                return None
            else:
                e = elements[elPos + 1]
                self.coreSelfActiveSite(e)
                return e
        else:
            for i in range(elPos + 1, len(elements)):
                if classList is None or classSet.intersection(elements[i].classSet):
                    e = elements[i]
                    self.coreSelfActiveSite(e)
                    return e

    # ----------------------------------------------------
    # end .getElement filters

    # -------------------------------------------------------------------------
    # routines for obtaining specific types of elements from a Stream
    # _getNotes and _getPitches are found with the interval routines
    def _getMeasureNumberListByStartEnd(
        self,
        numberStart: int | str,
        numberEnd: int | str,
        *,
        indicesNotNumbers: bool
    ) -> list[Measure]:
        def hasMeasureNumberInformation(measureIterator: iterator.StreamIterator[Measure]) -> bool:
            '''
            Many people create streams where every number is zero.
            This will check for that as quickly as possible.
            '''
            for m in measureIterator:
                try:
                    mNumber = int(m.number)
                except ValueError:  # pragma: no cover
                    # should never happen.
                    raise StreamException(f'found problematic measure for numbering: {m}')
                if mNumber != 0:
                    return True
            return False

        mStreamIter: iterator.StreamIterator[Measure] = self.getElementsByClass(Measure)

        # FIND THE CORRECT ORIGINAL MEASURE OBJECTS
        # for indicesNotNumbers, this is simple...
        if indicesNotNumbers:
            if not isinstance(numberStart, int) or not isinstance(numberEnd, (int, types.NoneType)):
                raise ValueError(
                    'numberStart and numberEnd must be integers with indicesNotNumbers=True'
                )
            # noinspection PyTypeChecker
            return t.cast(list[Measure], list(mStreamIter[numberStart:numberEnd]))

        hasUniqueMeasureNumbers = hasMeasureNumberInformation(mStreamIter)

        # unused...
        # originalNumberStart = numberStart
        # originalNumberEnd = numberEnd
        startSuffix = None
        endSuffix = None
        if isinstance(numberStart, str):
            numberStart, startSuffixTemp = common.getNumFromStr(numberStart)
            if startSuffixTemp:
                startSuffix = startSuffixTemp
            numberStart = int(numberStart)

        if isinstance(numberEnd, str):
            numberEnd, endSuffixTemp = common.getNumFromStr(numberEnd)
            if endSuffixTemp:
                endSuffix = endSuffixTemp
            numberEnd = int(numberEnd)

        matches: list[Measure]
        if numberEnd is not None:
            matchingMeasureNumbers = set(range(numberStart, numberEnd + 1))

            if hasUniqueMeasureNumbers:
                matches = [m for m in mStreamIter if m.number in matchingMeasureNumbers]
            else:
                matches = [m for i, m in enumerate(mStreamIter)
                                if i + 1 in matchingMeasureNumbers]
        else:
            if hasUniqueMeasureNumbers:
                matches = [m for m in mStreamIter if m.number >= numberStart]
            else:
                matches = [m for i, m in enumerate(mStreamIter)
                                    if i + 1 >= numberStart]

        if startSuffix is not None:
            oldMatches = matches
            matches = []
            for m in oldMatches:
                if m.number != numberStart:
                    matches.append(m)
                elif not m.numberSuffix:
                    matches.append(m)
                elif m.numberSuffix >= startSuffix:
                    matches.append(m)

        if endSuffix is not None:
            oldMatches = matches
            matches = []
            for m in oldMatches:
                if m.number != numberEnd:
                    matches.append(m)
                elif not m.numberSuffix:
                    matches.append(m)
                elif m.numberSuffix <= endSuffix:
                    matches.append(m)
        return matches

    def measures(
        self,
        numberStart,
        numberEnd,
        *,
        collect=('Clef', 'TimeSignature', 'Instrument', 'KeySignature'),
        gatherSpanners=GatherSpanners.ALL,
        indicesNotNumbers=False
    ) -> Stream[Measure]:
        '''
        Get a region of Measures based on a start and end Measure number
        where the boundary numbers are both included.

        That is, a request for measures 4 through 10 will return 7 Measures, numbers 4 through 10.

        Additionally, any number of associated classes can be gathered from the context
        and put into the measure.  By default, we collect the Clef, TimeSignature, KeySignature,
        and Instrument so that there is enough context to perform.  (See getContextByClass()
        and .previous() for definitions of the context)

        While all elements in the source are the original elements in the extracted region,
        new Measure objects are created and returned.

        >>> bachIn = corpus.parse('bach/bwv66.6')
        >>> bachExcerpt = bachIn.parts[0].measures(1, 3)
        >>> len(bachExcerpt.getElementsByClass(stream.Measure))
        3

        Because bwv66.6 has a pickup measure, and we requested to start at measure 1,
        this is NOT true:

        >>> firstExcerptMeasure = bachExcerpt.getElementsByClass(stream.Measure).first()
        >>> firstBachMeasure = bachIn.parts[0].getElementsByClass(stream.Measure).first()
        >>> firstExcerptMeasure is firstBachMeasure
        False
        >>> firstBachMeasure.number
        0
        >>> firstExcerptMeasure.number
        1

        To get all measures from the beginning, go ahead and always request measure 0 to x,
        there will be no error if there is not a pickup measure.

        >>> bachExcerpt = bachIn.parts[0].measures(0, 3)
        >>> excerptNote = bachExcerpt.getElementsByClass(stream.Measure).first().notes.first()
        >>> originalNote = bachIn.parts[0].recurse().notes[0]
        >>> excerptNote is originalNote
        True

        if `indicesNotNumbers` is True, then it ignores defined measureNumbers and
        uses 0-indexed measure objects and half-open range.  For instance, if you have a piece
        that goes "m1, m2, m3, m4, ..." (like a standard piece without pickups, then
        `.measures(1, 3, indicesNotNumbers=True)` would return measures 2 and 3, because
        it is interpreted as the slice from object with index 1, which is measure 2 (m1 has
        an index of 0) up to but NOT including the object with index 3, which is measure 4.
        IndicesNotNumbers is like a Python-slice.

        >>> bachExcerpt2 = bachIn.parts[0].measures(0, 2, indicesNotNumbers=True)
        >>> for m in bachExcerpt2.getElementsByClass(stream.Measure):
        ...     print(m)
        ...     print(m.number)
        <music21.stream.Measure 0 offset=0.0>
        0
        <music21.stream.Measure 1 offset=1.0>
        1

        If `numberEnd=None` then it is interpreted as the last measure of the stream:

        >>> bachExcerpt3 = bachIn.parts[0].measures(7, None)
        >>> for m in bachExcerpt3.getElementsByClass(stream.Measure):
        ...     print(m)
        <music21.stream.Measure 7 offset=0.0>
        <music21.stream.Measure 8 offset=4.0>
        <music21.stream.Measure 9 offset=8.0>

        Note that the offsets in the new stream are shifted so that the first measure
        in the excerpt begins at 0.0

        The measure elements are the same objects as the original:

        >>> lastExcerptMeasure = bachExcerpt3.getElementsByClass(stream.Measure).last()
        >>> lastOriginalMeasure = bachIn.parts[0].getElementsByClass(stream.Measure).last()
        >>> lastExcerptMeasure is lastOriginalMeasure
        True

        At the beginning of the Stream returned, before the measures will be some additional
        objects so that the context is properly preserved:

        >>> for thing in bachExcerpt3:
        ...     print(thing)
        P1: Soprano: Instrument 1
        <music21.clef.TrebleClef>
        f# minor
        <music21.meter.TimeSignature 4/4>
        <music21.stream.Measure 7 offset=0.0>
        <music21.stream.Measure 8 offset=4.0>
        <music21.stream.Measure 9 offset=8.0>

        Collecting gets the most recent element in the context of the stream:

        >>> bachIn.parts[0].insert(10, key.Key('D-'))
        >>> bachExcerpt4 = bachIn.parts[0].measures(7, None)
        >>> for thing in bachExcerpt4:
        ...     print(thing)
        P1: Soprano: Instrument 1
        <music21.clef.TrebleClef>
        D- major
        ...

        What is collected is determined by the "collect" iterable.  To collect nothing
        send an empty list:

        >>> bachExcerpt5 = bachIn.parts[0].measures(8, None, collect=[])
        >>> for thing in bachExcerpt5:
        ...     print(thing)
        <music21.stream.Measure 8 offset=0.0>
        <music21.stream.Measure 9 offset=4.0>

        If a stream has measure suffixes, then Streams having that suffix or no suffix
        are returned.

        >>> p = stream.Part()
        >>> mSuffix3 = stream.Measure(number=3)
        >>> mSuffix4 = stream.Measure(number=4)
        >>> mSuffix4a = stream.Measure(number=4)
        >>> mSuffix4a.numberSuffix = 'a'
        >>> mSuffix4b = stream.Measure(number=4)
        >>> mSuffix4b.numberSuffix = 'b'
        >>> mSuffix5 = stream.Measure(number=5)
        >>> mSuffix5a = stream.Measure(number=5)
        >>> mSuffix5a.numberSuffix = 'a'
        >>> mSuffix6 = stream.Measure(number=6)
        >>> p.append([mSuffix3, mSuffix4, mSuffix4a, mSuffix4b, mSuffix5, mSuffix5a, mSuffix6])
        >>> suffixExcerpt = p.measures('4b', 6)
        >>> suffixExcerpt.show('text')
        {0.0} <music21.stream.Measure 4 offset=0.0>
        <BLANKLINE>
        {0.0} <music21.stream.Measure 4b offset=0.0>
        <BLANKLINE>
        {0.0} <music21.stream.Measure 5 offset=0.0>
        <BLANKLINE>
        {0.0} <music21.stream.Measure 5a offset=0.0>
        <BLANKLINE>
        {0.0} <music21.stream.Measure 6 offset=0.0>
        <BLANKLINE>
        >>> suffixExcerpt2 = p.measures(3, '4a')
        >>> suffixExcerpt2.show('text')
        {0.0} <music21.stream.Measure 3 offset=0.0>
        <BLANKLINE>
        {0.0} <music21.stream.Measure 4 offset=0.0>
        <BLANKLINE>
        {0.0} <music21.stream.Measure 4a offset=0.0>
        <BLANKLINE>

        GatherSpanners can change the output:

        >>> from music21.common.enums import GatherSpanners
        >>> beachIn = corpus.parse('beach')
        >>> beachExcerpt = beachIn.measures(3, 4, gatherSpanners=GatherSpanners.ALL)
        >>> len(beachExcerpt.spannerBundle)
        8
        >>> len(beachIn.spannerBundle)
        93

        * Changed in v7: does not create measures automatically.
        * Changed in v7: If `gatherSpanners` is True or GatherSpanners.ALL (default),
          then just the spanners pertaining to the requested measure region
          are provided, rather than the entire bundle from the source.

        OMIT_FROM_DOCS

        Ensure that layout.StaffGroup objects are present:

        >>> for sp in beachExcerpt.spannerBundle.getByClass('StaffGroup'):
        ...    print(sp)
        <music21.layout.StaffGroup <music21.stream.PartStaff P5-Staff1><... P5-Staff2>>
        <music21.layout.StaffGroup <music21.stream.Part Soprano I><...Alto II>>

        This is in OMIT
        '''
        startMeasure: Measure | None

        returnObj = t.cast(Stream[Measure], self.cloneEmpty(derivationMethod='measures'))
        srcObj = self

        matches = self._getMeasureNumberListByStartEnd(
            numberStart,
            numberEnd,
            indicesNotNumbers=indicesNotNumbers
        )

        startOffset: OffsetQL
        if not matches:
            startMeasure = None
            startOffset = 0.0  # does not matter; could be any number...
        else:
            startMeasure = matches[0]
            startOffset = startMeasure.getOffsetBySite(srcObj)

        for className in collect:
            # first, see if it is in this Measure
            if (startMeasure is None
                    or startMeasure.recurse().getElementsByClass(className).getElementsByOffset(0)):
                continue

            # placing missing objects in outer container, not Measure
            found = startMeasure.getContextByClass(className)
            if found is not None:
                if startMeasure is not None:
                    found.priority = startMeasure.priority - 1
                    # TODO: This should not change global priority on found, but
                    #   instead priority, like offset, should be a per-site attribute
                returnObj.coreInsert(0, found)

        for m in matches:
            mOffset = m.getOffsetBySite(srcObj) - startOffset
            returnObj.coreInsert(mOffset, m)

        # used coreInsert
        returnObj.coreElementsChanged()

        if gatherSpanners:  # True, GatherSpanners.ALL, or GatherSpanners.COMPLETE_ONLY
            requireAllPresent = (gatherSpanners is GatherSpanners.COMPLETE_ONLY)
            returnObj.coreGatherMissingSpanners(
                requireAllPresent=requireAllPresent,
                constrainingSpannerBundle=self.spannerBundle,
            )

        # environLocal.printDebug(['len(returnObj.flatten())', len(returnObj.flatten())])
        return returnObj

    # this is generic Stream.measure, also used by Parts
    def measure(self,
                measureNumber,
                *,
                collect=('Clef', 'TimeSignature', 'Instrument', 'KeySignature'),
                indicesNotNumbers=False) -> Measure | None:
        '''
        Given a measure number, return a single
        :class:`~music21.stream.Measure` object if the Measure number exists, otherwise return None.

        This method is distinguished from :meth:`~music21.stream.Stream.measures`
        in that this method returns a single Measure object, not a Stream containing
        one or more Measure objects.

        >>> a = corpus.parse('bach/bwv324.xml')
        >>> a.parts[0].measure(3)
        <music21.stream.Measure 3 offset=8.0>

        See :meth:`~music21.stream.Stream.measures` for an explanation of collect and
        indicesNotNumbers

        To get the last measure of a piece, use -1 as a measureNumber -- this will turn
        on indicesNotNumbers if it is off:

        >>> a.parts[0].measure(-1)
        <music21.stream.Measure 9 offset=38.0>

        Getting a non-existent measure will return None:

        >>> print(a.parts[0].measure(99))
        None

        OMIT_FROM_DOCS

        >>> sf = a.parts[0].flatten()
        >>> sf.measure(2) is None
        True
        '''
        if not isinstance(measureNumber, str) and measureNumber < 0:
            indicesNotNumbers = True

        startMeasureNumber = measureNumber
        endMeasureNumber = measureNumber
        if indicesNotNumbers:
            endMeasureNumber += 1
            if startMeasureNumber == -1:
                endMeasureNumber = None

        matchingMeasures = self._getMeasureNumberListByStartEnd(
            startMeasureNumber,
            endMeasureNumber,
            indicesNotNumbers=indicesNotNumbers
        )
        if matchingMeasures:
            m = matchingMeasures[0]
            self.coreSelfActiveSite(m)  # not needed?
            return m
        return None

    def template(self,
                 *,
                 fillWithRests=True,
                 removeClasses=None,
                 retainVoices=True,
                 ):
        '''
        Return a new Stream based on this one, but without the notes and other elements
        but keeping instruments, clefs, keys, etc.

        Classes to remove are specified in `removeClasses`.

        If this Stream contains measures, return a new Stream
        with new Measures populated with the same characteristics of those found in this Stream.

        >>> b = corpus.parse('bwv66.6')
        >>> sopr = b.parts[0]
        >>> soprEmpty = sopr.template()
        >>> soprEmpty.show('text')
        {0.0} <music21.instrument.Instrument 'P1: Soprano: Instrument 1'>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.tempo.MetronomeMark Quarter=96 (playback only)>
            {0.0} <music21.key.Key of f# minor>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Rest quarter>
        {1.0} <music21.stream.Measure 1 offset=1.0>
            {0.0} <music21.note.Rest whole>
        {5.0} <music21.stream.Measure 2 offset=5.0>
            {0.0} <music21.note.Rest whole>
        {9.0} <music21.stream.Measure 3 offset=9.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.note.Rest whole>
        {13.0} <music21.stream.Measure 4 offset=13.0>
        ...


        Really make empty with `fillWithRests=False`

        >>> alto = b.parts[1]
        >>> altoEmpty = alto.template(fillWithRests=False)
        >>> altoEmpty.show('text')
        {0.0} <music21.instrument.Instrument 'P2: Alto: Instrument 2'>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.tempo.MetronomeMark Quarter=96 (playback only)>
            {0.0} <music21.key.Key of f# minor>
            {0.0} <music21.meter.TimeSignature 4/4>
        {1.0} <music21.stream.Measure 1 offset=1.0>
        <BLANKLINE>
        {5.0} <music21.stream.Measure 2 offset=5.0>
        <BLANKLINE>
        {9.0} <music21.stream.Measure 3 offset=9.0>
            {0.0} <music21.layout.SystemLayout>
        ...


        `removeClasses` can be a list or set of classes to remove.  By default it is
        ['GeneralNote', 'Dynamic', 'Expression']

        >>> tenor = b.parts[2]
        >>> tenorNoClefsSignatures = tenor.template(fillWithRests=False,
        ...       removeClasses=['Clef', 'KeySignature', 'TimeSignature', 'Instrument'])
        >>> tenorNoClefsSignatures.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.tempo.MetronomeMark Quarter=96 (playback only)>
            {0.0} <music21.note.Note A>
            {0.5} <music21.note.Note B>
        {1.0} <music21.stream.Measure 1 offset=1.0>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {5.0} <music21.stream.Measure 2 offset=5.0>
        ...

        Setting removeClasses to True removes everything that is not a Stream:

        >>> bass = b.parts[3]
        >>> bassEmpty = bass.template(fillWithRests=False, removeClasses=True)
        >>> bassEmpty.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
        <BLANKLINE>
        {1.0} <music21.stream.Measure 1 offset=1.0>
        <BLANKLINE>
        {5.0} <music21.stream.Measure 2 offset=5.0>
        <BLANKLINE>
        {9.0} <music21.stream.Measure 3 offset=9.0>
        <BLANKLINE>
        {13.0} <music21.stream.Measure 4 offset=13.0>
        <BLANKLINE>
        ...

        On the whole score:

        >>> b.template().show('text')
        {0.0} <music21.metadata.Metadata object at 0x106151940>
        {0.0} <music21.stream.Part Soprano>
            {0.0} <music21.instrument.Instrument 'P1: Soprano: Instrument 1'>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.tempo.MetronomeMark Quarter=96 (playback only)>
                {0.0} <music21.key.Key of f# minor>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Rest quarter>
            {1.0} <music21.stream.Measure 1 offset=1.0>
                {0.0} <music21.note.Rest whole>
                ...
            {33.0} <music21.stream.Measure 9 offset=33.0>
                {0.0} <music21.note.Rest dotted-half>
                {3.0} <music21.bar.Barline type=final>
        {0.0} <music21.stream.Part Alto>
            {0.0} <music21.instrument.Instrument 'P2: Alto: Instrument 2'>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.tempo.MetronomeMark Quarter=96 (playback only)>
                {0.0} <music21.key.Key of f# minor>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Rest quarter>
            {1.0} <music21.stream.Measure 1 offset=1.0>
                {0.0} <music21.note.Rest whole>
            ...
            {33.0} <music21.stream.Measure 9 offset=33.0>
                {0.0} <music21.note.Rest dotted-half>
                {3.0} <music21.bar.Barline type=final>
        {0.0} <music21.layout.StaffGroup ...>


        If `retainVoices` is False (default True) then Voice streams are treated
        differently from all other Streams and are removed.  All elements in the
        voice are removed even if they do not match the `classList`:

        >>> p = stream.Part(id='part0')
        >>> m1 = stream.Measure(number=1)
        >>> v1 = stream.Voice(id='voice1')
        >>> v1.insert(0, note.Note('E', quarterLength=4.0))
        >>> v2 = stream.Voice(id='voice2')
        >>> v2.insert(0, note.Note('G', quarterLength=2.0))
        >>> m1.insert(0, v1)
        >>> m1.insert(0, v2)
        >>> m2 = stream.Measure(number=2)
        >>> m2.insert(0, note.Note('D', quarterLength=4.0))
        >>> p.append([m1, m2])
        >>> pt = p.template(retainVoices=False)
        >>> pt.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.note.Rest whole>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Rest whole>
        >>> pt[0][0].quarterLength
        4.0

        Developer note -- if you just want a copy of a Score with new
        Part and Measure objects, but you don't care that the notes, etc.
        inside are the same objects as the original (i.e., you do not
        plan to manipulate them, or you want the manipulations to
        return to the original objects), using .template() is several
        times faster than a deepcopy of the stream (about 4x faster
        on bwv66.6)

        * Changed in v7: all arguments are keyword only.
        '''
        out = self.cloneEmpty(derivationMethod='template')
        if removeClasses is None:
            removeClasses = {'GeneralNote', 'Dynamic', 'Expression'}
        elif common.isIterable(removeClasses):
            removeClasses = set(removeClasses)

        restInfo = {'offset': None, 'endTime': None}

        def optionalAddRest():
            # six.PY3  nonlocal currentRest  would remove the need for restInfo struct
            if not fillWithRests:
                return
            if restInfo['offset'] is None:
                return

            restQL = restInfo['endTime'] - restInfo['offset']
            restObj = note.Rest(quarterLength=restQL)
            out.coreInsert(restInfo['offset'], restObj)
            restInfo['offset'] = None
            restInfo['endTime'] = None

        for el in self:
            elOffset = self.elementOffset(el, returnSpecial=True)
            if el.isStream and (retainVoices or ('Voice' not in el.classes)):
                optionalAddRest()
                outEl = el.template(fillWithRests=fillWithRests,
                                    removeClasses=removeClasses,
                                    retainVoices=retainVoices)
                if elOffset != OffsetSpecial.AT_END:
                    out.coreInsert(elOffset, outEl)
                else:  # pragma: no cover
                    # should not have streams stored at end.
                    out.coreStoreAtEnd(outEl)

            elif (removeClasses is True
                    or el.classSet.intersection(removeClasses)
                    or (not retainVoices and 'Voice' in el.classes)):
                # remove this element
                if fillWithRests and el.duration.quarterLength:
                    endTime = elOffset + el.duration.quarterLength
                    if restInfo['offset'] is None:
                        restInfo['offset'] = elOffset
                        restInfo['endTime'] = endTime
                    elif endTime > restInfo['endTime']:
                        restInfo['endTime'] = endTime
            else:
                optionalAddRest()
                elNew = copy.deepcopy(el)
                if elOffset != OffsetSpecial.AT_END:
                    out.coreInsert(elOffset, elNew)
                else:
                    out.coreStoreAtEnd(elNew)

        # Replace old measures in spanners with new measures
        # Example: out is a Part, out.spannerBundle has RepeatBrackets spanning measures
        for oldM, newM in zip(
            self.getElementsByClass(Measure),
            out.getElementsByClass(Measure),
            strict=True
        ):
            out.spannerBundle.replaceSpannedElement(oldM, newM)

        optionalAddRest()
        out.coreElementsChanged()

        return out

    def measureOffsetMap(
        self,
        classFilterList: list[t.Type] | list[str] | tuple[t.Type] | tuple[str] = ('Measure',)
    ) -> OrderedDict[float | Fraction, list[Measure]]:
        '''
        If this Stream contains Measures, returns an OrderedDict
        whose keys are the offsets of the start of each measure
        and whose values are a list of references
        to the :class:`~music21.stream.Measure` objects that start
        at that offset.

        Even in normal music there may be more than
        one Measure starting at each offset because each
        :class:`~music21.stream.Part` might define its own Measure.
        However, you are unlikely to encounter such things unless you
        run Score.flatten(retainContainers=True).

        The offsets are always measured relative to the
        calling Stream (self).

        You can specify a `classFilterList` argument as a list of classes
        to find instead of Measures.  But the default will of course
        find Measure objects.

        Example 1: This Bach chorale is in 4/4 without a pickup, so
        as expected, measures are found every 4 offsets, until the
        weird recitation in m. 7 which in our edition lasts 10 beats
        and thus causes a gap in measureOffsetMap from 24.0 to 34.0.

        .. image:: images/streamMeasureOffsetMapBWV324.*
            :width: 572


        >>> chorale = corpus.parse('bach/bwv324.xml')
        >>> alto = chorale.parts['#alto']
        >>> altoMeasures = alto.measureOffsetMap()
        >>> altoMeasures
        OrderedDict([(0.0, [<music21.stream.Measure 1 offset=0.0>]),
                     (4.0, [<music21.stream.Measure 2 offset=4.0>]),
                     (8.0, [<music21.stream.Measure 3 offset=8.0>]),
                     ...
                     (38.0, [<music21.stream.Measure 9 offset=38.0>])])
        >>> list(altoMeasures.keys())
        [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 34.0, 38.0]

        altoMeasures is a dictionary of the measures
        that are found in the alto part, so we can get
        the measure beginning on offset 4.0 (measure 2)
        and display it (though it's the only measure
        found at offset 4.0, there might be others as
        in example 2, so we need to call altoMeasures[4.0][0]
        to get this measure.):

        >>> altoMeasures[4.0]
        [<music21.stream.Measure 2 offset=4.0>]
        >>> altoMeasures[4.0][0].show('text')
        {0.0} <music21.note.Note D>
        {1.0} <music21.note.Note D#>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F#>

        Example 2: How to get all the measures from all parts (not the
        most efficient way, but it works!):

        >>> mom = chorale.measureOffsetMap()
        >>> mom
        OrderedDict([(0.0, [<music21.stream.Measure 1 offset=0.0>,
                            <music21.stream.Measure 1 offset=0.0>,
                            <music21.stream.Measure 1 offset=0.0>,
                            <music21.stream.Measure 1 offset=0.0>]),
                      (4.0, [<music21.stream.Measure 2 offset=4.0>,
                             ...])])
        >>> for measure_obj in mom[8.0]:
        ...     print(measure_obj, measure_obj.getContextByClass(stream.Part).id)
        <music21.stream.Measure 3 offset=8.0> Soprano
        <music21.stream.Measure 3 offset=8.0> Alto
        <music21.stream.Measure 3 offset=8.0> Tenor
        <music21.stream.Measure 3 offset=8.0> Bass

        Changed in v9: classFilterList must be a list or tuple of strings or Music21Objects

        OMIT_FROM_DOCS

        see important examples in testMeasureOffsetMap() and
        testMeasureOffsetMapPostTie()
        '''
        # environLocal.printDebug(['calling measure offsetMap()'])

        # environLocal.printDebug([classFilterList])
        offsetMap: dict[float | Fraction, list[Measure]] = {}
        # first, try to get measures
        # this works best of this is a Part or Score
        if Measure in classFilterList or 'Measure' in classFilterList:
            for m in self.getElementsByClass(Measure):
                offset = self.elementOffset(m)
                if offset not in offsetMap:
                    offsetMap[offset] = []
                # there may be more than one measure at the same offset
                offsetMap[offset].append(m)

        # try other classes
        for className in classFilterList:
            if className in (Measure, 'Measure'):  # do not redo
                continue
            for e in self.getElementsByClass(className):
                # environLocal.printDebug(['calling measure offsetMap(); e:', e])
                # NOTE: if this is done on Notes, this can take an extremely
                # long time to process
                # 'reverse' here is a reverse sort, where the oldest objects
                # are returned first
                maybe_m = e.getContextByClass(Measure)  # , sortByCreationTime='reverse')
                if maybe_m is None:  # pragma: no cover
                    # hard to think of a time this would happen...But...
                    continue
                m = maybe_m
                # assuming that the offset returns the proper offset context
                # this is, the current offset may not be the stream that
                # contains this Measure; its current activeSite
                offset = m.offset
                if offset not in offsetMap:
                    offsetMap[offset] = []
                if m not in offsetMap[offset]:
                    offsetMap[offset].append(m)

        orderedOffsetMap = OrderedDict(sorted(offsetMap.items(), key=lambda o: o[0]))
        return orderedOffsetMap

    def _getFinalBarline(self):
        # if we have part-like streams, process each part
        if self.hasPartLikeStreams():
            post = []
            for p in self.getElementsByClass('Stream'):
                post.append(p._getFinalBarline())
            return post  # a list of barlines
        # core routines for a single Stream
        else:
            if self.hasMeasures():
                return self.getElementsByClass(Measure).last().rightBarline
            elif hasattr(self, 'rightBarline'):
                return self.rightBarline
            else:
                return None

    def _setFinalBarline(self, value):
        # if we have part-like streams, process each part
        if self.hasPartLikeStreams():
            if not common.isListLike(value):
                value = [value]
            for i, p in enumerate(self.getElementsByClass('Stream')):
                # set final barline w/ mod iteration of value list
                bl = value[i % len(value)]
                # environLocal.printDebug(['enumerating measures', i, p, 'setting barline', bl])
                p._setFinalBarline(bl)
            return

        # core routines for a single Stream
        if self.hasMeasures():
            self.getElementsByClass(Measure).last().rightBarline = value
        elif hasattr(self, 'rightBarline'):
            self.rightBarline = value  # pylint: disable=attribute-defined-outside-init
        # do nothing for other streams

    finalBarline = property(_getFinalBarline, _setFinalBarline, doc='''
        Get or set the final barline of this Stream's Measures,
        if and only if there are Measures defined as elements in this Stream.
        This method will not create Measures if none exist.

        >>> p = stream.Part()
        >>> m1 = stream.Measure()
        >>> m1.rightBarline = bar.Barline('double')
        >>> p.append(m1)
        >>> p.finalBarline
        <music21.bar.Barline type=double>
        >>> m2 = stream.Measure()
        >>> m2.rightBarline = bar.Barline('final')
        >>> p.append(m2)
        >>> p.finalBarline
        <music21.bar.Barline type=final>

        This property also works on Scores that contain one or more Parts.
        In that case a list of barlines can be used to set the final barline.

        >>> s = corpus.parse('bwv66.6')
        >>> s.finalBarline
        [<music21.bar.Barline type=final>,
         <music21.bar.Barline type=final>,
         <music21.bar.Barline type=final>,
         <music21.bar.Barline type=final>]

        >>> s.finalBarline = 'none'
        >>> s.finalBarline
        [<music21.bar.Barline type=none>,
         <music21.bar.Barline type=none>,
         <music21.bar.Barline type=none>,
         <music21.bar.Barline type=none>]


        Getting or setting a final barline on a Measure (or another Stream
        with a rightBarline attribute) is the same as getting or setting the rightBarline.

        >>> m = stream.Measure()
        >>> m.finalBarline is None
        True
        >>> m.finalBarline = 'final'
        >>> m.finalBarline
        <music21.bar.Barline type=final>
        >>> m.rightBarline
        <music21.bar.Barline type=final>

        Getting on a generic Stream, Voice, or Opus always returns a barline of None,
        and setting on a generic Stream, Voice, or Opus always returns None:

        >>> s = stream.Stream()
        >>> s.finalBarline is None
        True
        >>> s.finalBarline = 'final'
        >>> s.finalBarline is None
        True

        * Changed in v6.3: does not raise an exception if queried or set on a measure-less stream.
          Previously raised a StreamException
        ''')

    @property
    def voices(self):
        '''
        Return all :class:`~music21.stream.Voices` objects
        in an iterator

        >>> s = stream.Stream()
        >>> s.insert(0, stream.Voice())
        >>> s.insert(0, stream.Voice())
        >>> len(s.voices)
        2
        '''
        return self.getElementsByClass('Voice')

    @property
    def spanners(self) -> iterator.StreamIterator[spanner.Spanner]:
        '''
        Return all :class:`~music21.spanner.Spanner` objects
        (things such as Slurs, long trills, or anything that
        connects many objects)
        in an Iterator

        >>> s = stream.Stream()
        >>> s.insert(0, spanner.Slur())
        >>> s.insert(0, spanner.Slur())
        >>> len(s.spanners)
        2
        '''
        from music21 import spanner
        return self.getElementsByClass(spanner.Spanner)

    # --------------------------------------------------------------------------
    # handling transposition values and status

    @property
    def atSoundingPitch(self) -> bool | t.Literal['unknown']:
        '''
        Get or set the atSoundingPitch status, that is whether the
        score is at concert pitch or may have transposing instruments
        that will not sound as notated.

        Valid values are True, False, and 'unknown'.

        Note that setting "atSoundingPitch" does not actually transpose the notes. See
        `toSoundingPitch()` for that information.

        >>> s = stream.Stream()
        >>> s.atSoundingPitch = True
        >>> s.atSoundingPitch = False
        >>> s.atSoundingPitch = 'unknown'
        >>> s.atSoundingPitch
        'unknown'
        >>> s.atSoundingPitch = 'junk'
        Traceback (most recent call last):
        music21.exceptions21.StreamException: not a valid at sounding pitch value: junk
        '''
        return self._atSoundingPitch

    @atSoundingPitch.setter
    def atSoundingPitch(self, value: bool | t.Literal['unknown']):
        if value in [True, False, 'unknown']:
            self._atSoundingPitch = value
        else:
            raise StreamException(f'not a valid at sounding pitch value: {value}')

    @overload
    def _transposeByInstrument(
        self: StreamType,
        *,
        reverse: bool = False,
        transposeKeySignature: bool = True,
        preserveAccidentalDisplay: bool = False,
        inPlace: t.Literal[True],
    ) -> None:
        pass

    @overload
    def _transposeByInstrument(
        self: StreamType,
        *,
        reverse: bool = False,
        transposeKeySignature: bool = True,
        preserveAccidentalDisplay: bool = False,
        inPlace: t.Literal[False] = False,
    ) -> StreamType:
        pass

    def _transposeByInstrument(
        self: StreamType,
        *,
        reverse: bool = False,
        transposeKeySignature: bool = True,
        preserveAccidentalDisplay: bool = False,
        inPlace: bool = False,
    ) -> StreamType | None:
        '''
        Transpose the Stream according to each instrument's transposition.

        If reverse is False, the transposition will happen in the direction
        opposite of what is specified by the Instrument. for instance,
        for changing a concert score to a transposed score or for
        extracting parts.

        TODO: Fill out -- expose publicly?
        '''
        if not inPlace:  # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        instrument_stream = returnObj.getInstruments(recurse=True)
        instrument_map: dict[instrument.Instrument, OffsetQL] = {}
        for inst in instrument_stream:
            # keep track of original durations of each instrument
            instrument_map[inst] = inst.duration.quarterLength
            # this loses the expression of duration, but should be fine for instruments.

        instrument_stream.duration = returnObj.duration
        # inPlace=False here because we are only doing calculations
        # toWrittenPitch() shouldn't be inserting extra instruments
        instrument_stream = instrument_stream.extendDuration('Instrument', inPlace=False)

        # store class filter list for transposition
        classFilterList: tuple[type[music21.Music21Object], ...]
        if transposeKeySignature:
            classFilterList = (note.Note, chord.Chord, key.KeySignature)
        else:
            classFilterList = (note.Note, chord.Chord)

        displayStatusesAreSet: bool = self.haveAccidentalsBeenMade()

        for inst in instrument_stream:
            if inst.transposition is None:
                continue
            start = inst.offset
            end = start + inst.quarterLength
            focus: Stream = returnObj.flatten().getElementsByOffset(
                start,
                end,
                includeEndBoundary=False,
                mustFinishInSpan=False,
                mustBeginInSpan=True).stream()
            trans = inst.transposition
            if reverse:
                trans = trans.reverse()

            if preserveAccidentalDisplay and displayStatusesAreSet:
                with makeNotation.saveAccidentalDisplayStatus(focus):
                    focus.transpose(trans, inPlace=True, classFilterList=classFilterList)
            else:
                focus.transpose(trans, inPlace=True, classFilterList=classFilterList)

        # restore original durations
        for inst, original_ql in instrument_map.items():
            inst.duration.quarterLength = original_ql

        return returnObj

    def _treatAtSoundingPitch(self) -> bool | str:
        '''
        `atSoundingPitch` might be True, False, or 'unknown'. Given that
        setting the property does not automatically synchronize the corresponding
        property on contained or containing streams, any time a method relying on the
        value of `atSoundingPitch` such as :meth:`toSoundingPitch` visits a stream,
        it will need to resolve 'unknown' values or even possibly conflicting values.

        If this stream's `.atSoundingPitch` is 'unknown', this helper method searches
        this stream's sites until a True or False
        value for `.atSoundingPitch` is found, since it is possible a user only manipulated
        the value on the top-level stream.

        Then, contained streams are searched to verify that they do not contain
        conflicting values (i.e. .atSoundingPitch = True when the container has
        .atSoundingPitch = False). Conflicting values are resolved by converting
        the inner streams to written or sounding pitch as necessary to match this
        stream's value.
        '''
        at_sounding = self.atSoundingPitch
        if self.atSoundingPitch == 'unknown':
            for contextTuple in self.contextSites():
                # follow derivations to find one something in a derived hierarchy
                # where soundingPitch might be defined.
                site = contextTuple.site
                if site.isStream and site.atSoundingPitch != 'unknown':
                    at_sounding = site.atSoundingPitch
                    break
            else:
                return 'unknown'

        for substream in self.recurse(streamsOnly=True, includeSelf=False):
            if substream.atSoundingPitch == 'unknown':
                continue
            if substream.atSoundingPitch is False and at_sounding is True:
                substream.toSoundingPitch(inPlace=True)
            elif substream.atSoundingPitch is True and at_sounding is False:
                substream.toWrittenPitch(inPlace=True)

        return at_sounding

    def toSoundingPitch(
        self,
        *,
        preserveAccidentalDisplay: bool = False,
        inPlace=False
    ):
        # noinspection PyShadowingNames
        '''
        If not at sounding pitch, transpose all Pitch
        elements to sounding pitch. The atSoundingPitch property
        is used to determine if transposition is necessary.

        Affected by the presence of Instruments and by Ottava spanners

        >>> sc = stream.Score()
        >>> p = stream.Part(id='barisax')
        >>> p.append(instrument.BaritoneSaxophone())
        >>> m = stream.Measure(number=1)
        >>> m.append(note.Note('A4'))
        >>> p.append(m)
        >>> sc.append(p)
        >>> sc.atSoundingPitch = False

        >>> scSounding = sc.toSoundingPitch()
        >>> scSounding.show('text')
        {0.0} <music21.stream.Part barisax>
            {0.0} <music21.instrument.BaritoneSaxophone 'Baritone Saxophone'>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note C>

        >>> scSounding.atSoundingPitch
        True
        >>> scSounding.parts[0].atSoundingPitch
        True
        >>> scSounding.recurse().notes[0].nameWithOctave
        'C3'

        If 'atSoundingPitch' is unknown for this Stream and all of its parent Streams
        then no transposition will take place, and atSoundingPitch will remain unknown
        (this used to raise an exception):

        >>> s = stream.Score()
        >>> p = stream.Part(id='partEmpty')
        >>> s.insert(0.0, p)
        >>> p.toSoundingPitch()
        <music21.stream.Part partEmpty>
        >>> s.atSoundingPitch = False
        >>> sp = p.toSoundingPitch()
        >>> sp
        <music21.stream.Part partEmpty>
        >>> sp.atSoundingPitch
        'unknown'
        >>> sp.derivation.origin is p
        True

        * Changed in v2.0.10: inPlace is False
        * Changed in v5: returns None if inPlace=True
        * Changed in v9: no transposition instead of exception if atSoundingPitch is 'unknown'
        '''
        from music21 import spanner

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('toSoundingPitch')
        else:
            returnObj = self

        if returnObj.hasPartLikeStreams() or 'Opus' in returnObj.classSet:
            for partLike in returnObj.getElementsByClass(Stream):
                # call on each part
                partLike.toSoundingPitch(
                    inPlace=True,
                    preserveAccidentalDisplay=preserveAccidentalDisplay
                )
            returnObj.atSoundingPitch = True
            return returnObj if not inPlace else None

        at_sounding = returnObj._treatAtSoundingPitch()

        if at_sounding is False:
            # transposition defined on instrument goes from written to sounding
            returnObj._transposeByInstrument(
                reverse=False,
                preserveAccidentalDisplay=preserveAccidentalDisplay,
                inPlace=True
            )
            for container in returnObj.recurse(streamsOnly=True, includeSelf=True):
                container.atSoundingPitch = True

        for ottava in returnObj[spanner.Ottava]:
            ottava.performTransposition()

        if not inPlace:
            return returnObj  # the Stream or None

    def toWrittenPitch(
        self,
        *,
        ottavasToSounding: bool = False,
        preserveAccidentalDisplay: bool = False,
        inPlace: bool = False
    ):
        '''
        If not at written pitch, transpose all Pitch elements to
        written pitch. The atSoundingPitch property is used to
        determine if transposition is necessary.  Note that if
        ottavasToSounding is True, any notes/chords within
        an Ottava will _then_ be transposed to sounding Pitch (this
        is useful for the MusicXML writer, since MusicXML likes
        all pitches to be written pitches, except for those in
        ottavas, which should be transposed to written (by instrument)
        and then transposed to sounding (by ottava).

        >>> sc = stream.Score()
        >>> p = stream.Part(id='baritoneSax')
        >>> p.append(instrument.BaritoneSaxophone())
        >>> m = stream.Measure(number=1)
        >>> m.append(note.Note('C3'))
        >>> p.append(m)
        >>> sc.append(p)
        >>> sc.atSoundingPitch = True
        >>> scWritten = sc.toWrittenPitch()
        >>> scWritten.show('text')
        {0.0} <music21.stream.Part baritoneSax>
            {0.0} <music21.instrument.BaritoneSaxophone 'Baritone Saxophone'>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note A>
        >>> scWritten.atSoundingPitch
        False
        >>> scWritten.parts[0].atSoundingPitch
        False
        >>> scWritten.recurse().notes[0].nameWithOctave
        'A4'

        * Changed in v3: `inPlace` defaults to `False`
        * Changed in v5 returns `None` if `inPlace=True`
        * Changed in v9: no transposition instead of exception if atSoundingPitch is 'unknown'
        '''
        from music21 import spanner

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('toWrittenPitch')
        else:
            returnObj = self

        if returnObj.hasPartLikeStreams() or 'Opus' in returnObj.classes:
            for partLike in returnObj.getElementsByClass('Stream'):
                # call on each part
                if t.TYPE_CHECKING:
                    assert isinstance(partLike, Stream)
                partLike.toWrittenPitch(
                    inPlace=True,
                    ottavasToSounding=ottavasToSounding,
                    preserveAccidentalDisplay=preserveAccidentalDisplay
                )
            returnObj.atSoundingPitch = False
        else:
            at_sounding = returnObj._treatAtSoundingPitch()
            if at_sounding is True:
                # need to reverse to go to written
                returnObj._transposeByInstrument(
                    reverse=True,
                    preserveAccidentalDisplay=preserveAccidentalDisplay,
                    inPlace=True
                )
                for container in returnObj.recurse(streamsOnly=True, includeSelf=True):
                    container.atSoundingPitch = False

        if ottavasToSounding:
            for ottava in returnObj[spanner.Ottava]:
                ottava.performTransposition()
        else:
            for ottava in returnObj[spanner.Ottava]:
                ottava.undoTransposition()

        if not inPlace:
            return returnObj

    # --------------------------------------------------------------------------
    def getTimeSignatures(self, *,
                          searchContext=True,
                          returnDefault=True,
                          recurse=True,
                          sortByCreationTime=True):
        '''
        Collect all :class:`~music21.meter.TimeSignature` objects in this stream.
        If no TimeSignature objects are defined, get a default (4/4 or whatever
        is defined in the defaults.py file).

        >>> s = stream.Part(id='changingMeter')
        >>> s.repeatInsert(note.Note('C#'), list(range(11)))

        >>> threeFour = meter.TimeSignature('3/4')
        >>> s.insert(0.0, threeFour)
        >>> twoTwo = meter.TimeSignature('2/2')
        >>> s.insert(3.0, twoTwo)
        >>> tsStream = s.getTimeSignatures()
        >>> tsStream.derivation.method
        'getTimeSignatures'

        >>> tsStream
        <music21.stream.Part changingMeter>
        >>> tsStream.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {3.0} <music21.meter.TimeSignature 2/2>

        The contents of the time signature stream are the original, not copies
        of the original:

        >>> tsStream[0] is threeFour
        True

        Many time signatures are found within measures, so this method will find
        them also and place them at the appropriate point within the overall Stream.

        N.B. if there are different time signatures for different parts, this method
        will not distinguish which parts use which time signatures.

        >>> sm = s.makeMeasures()
        >>> sm.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note C#>
            {2.0} <music21.note.Note C#>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.meter.TimeSignature 2/2>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note C#>
            {2.0} <music21.note.Note C#>
            {3.0} <music21.note.Note C#>
        {7.0} <music21.stream.Measure 3 offset=7.0>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note C#>
            {2.0} <music21.note.Note C#>
            {3.0} <music21.note.Note C#>
            {4.0} <music21.bar.Barline type=final>

        >>> tsStream2 = sm.getTimeSignatures()
        >>> tsStream2.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {3.0} <music21.meter.TimeSignature 2/2>

        If you do not want this recursion, set recurse=False

        >>> len(sm.getTimeSignatures(recurse=False, returnDefault=False))
        0

        We set returnDefault=False here, because otherwise a default time signature
        of 4/4 is returned:

        >>> sm.getTimeSignatures(recurse=False)[0]
        <music21.meter.TimeSignature 4/4>

        Note that a measure without any time signature can still find a context TimeSignature
        with this method so long as searchContext is True (as by default):

        >>> m3 = sm.measure(3)
        >>> m3.show('text')
        {0.0} <music21.note.Note C#>
        {1.0} <music21.note.Note C#>
        {2.0} <music21.note.Note C#>
        {3.0} <music21.note.Note C#>
        {4.0} <music21.bar.Barline type=final>

        >>> m3.getTimeSignatures()[0]
        <music21.meter.TimeSignature 2/2>

        The oldest context for the measure will be used unless sortByCreationTime is False, in which
        case the typical order of context searching will be used.

        >>> p2 = stream.Part()
        >>> p2.insert(0, meter.TimeSignature('1/1'))
        >>> p2.append(m3)
        >>> m3.getTimeSignatures()[0]
        <music21.meter.TimeSignature 2/2>

        If searchContext is False then the default will be returned (which is somewhat
        acceptable here, since there are 4 quarter notes in the measure) but not generally correct:

        >>> m3.getTimeSignatures(searchContext=False)[0]
        <music21.meter.TimeSignature 4/4>


        * Changed in v8: time signatures within recursed streams are found by default.
          Added recurse. Removed option for recurse=False and still getting the
          first time signature in the first measure.  This was wholly inconsistent.
        '''
        # even if this is a Measure, the TimeSignature in the Stream will be
        # found
        if recurse:
            post = self[meter.TimeSignature].stream()
        else:
            post = self.getElementsByClass(meter.TimeSignature).stream()
        post.derivation.method = 'getTimeSignatures'

        # search activeSite Streams through contexts
        if not post and searchContext:
            # sort by time to search the most recent objects
            obj = self.getContextByClass('TimeSignature', sortByCreationTime=sortByCreationTime)
            # obj = self.previous(meter.TimeSignature)
            # environLocal.printDebug(['getTimeSignatures(): searching contexts: results', obj])
            if obj is not None:
                post.append(obj)

        # get a default and/or place default at zero if nothing at zero
        if returnDefault:
            if not post or post[0].offset > 0.0:
                ts = meter.TimeSignature('%s/%s' % (defaults.meterNumerator,
                                                    defaults.meterDenominatorBeatType))
                post.insert(0, ts)
        # environLocal.printDebug(['getTimeSignatures(): final result:', post[0]])
        return post

    def getInstruments(self,
                       *,
                       searchActiveSite=True,
                       returnDefault=True,
                       recurse=True) -> Stream[instrument.Instrument]:
        '''
        Search this stream (and, by default, its subStreams) or activeSite streams for
        :class:`~music21.instrument.Instrument` objects, and return a new stream
        containing them.

        >>> m1 = stream.Measure([meter.TimeSignature('4/4'),
        ...                      instrument.Clarinet(),
        ...                      note.Note('C5', type='whole')])
        >>> m2 = stream.Measure([instrument.BassClarinet(),
        ...                      note.Note('C3', type='whole')])
        >>> p = stream.Part([m1, m2])
        >>> instruments = p.getInstruments()
        >>> instruments
        <music21.stream.Part 0x112ac26e0>

        >>> instruments.show('text')
        {0.0} <music21.instrument.Clarinet 'Clarinet'>
        {4.0} <music21.instrument.BassClarinet 'Bass clarinet'>

        If there are no instruments, returns a Stream containing a single default `Instrument`,
        unless returnDefault is False.

        >>> p = stream.Part()
        >>> m = stream.Measure([note.Note()])
        >>> p.insert(0, m)
        >>> instrumentStream = p.getInstruments(returnDefault=True)
        >>> defaultInst = instrumentStream.first()
        >>> defaultInst
        <music21.instrument.Instrument ': '>

        Insert an instrument into the Part (not the Measure):

        >>> p.insert(0, instrument.Koto())

        Searching the measure will find this instrument only if the measure's activeSite is
        searched, as it is by default:

        >>> searchedActiveSite = p.measure(1).getInstruments()
        >>> searchedActiveSite.first()
        <music21.instrument.Koto 'Koto'>

        >>> searchedNaive = p.measure(1).getInstruments(searchActiveSite=False, returnDefault=False)
        >>> len(searchedNaive)
        0

        * Changed in v8: recurse is True by default.
        '''
        instObj: instrument.Instrument | None = None

        if not recurse:
            sIter = self.iter()
        else:
            sIter = self.recurse()

        post = t.cast(Stream[instrument.Instrument],
                      sIter.getElementsByClass(instrument.Instrument).stream()
                      )

        if post:
            # environLocal.printDebug(['found local instrument:', post[0]])
            instObj = post.first()
        else:
            if searchActiveSite:
                # if isinstance(self.activeSite, Stream) and self.activeSite != self:
                if (self.activeSite is not None
                    and self.activeSite.isStream
                        and self.activeSite is not self):
                    # environLocal.printDebug(['searching activeSite Stream',
                    #    self, self.activeSite])
                    instObj = self.activeSite.getInstrument(
                        searchActiveSite=searchActiveSite,
                        returnDefault=False)
                    if instObj is not None:
                        post.insert(0, instObj)

        # if still not defined, get default
        if returnDefault and instObj is None:
            from music21.instrument import Instrument
            instObj = Instrument()
            # instObj.partId = defaults.partId  # give a default id
            # TODO: should this be changed to None? MSC 2015-12
            instObj.partName = defaults.partName  # give a default id
            post.insert(0, instObj)

        # returns a Stream
        return post

    def getInstrument(self,
                      *,
                      searchActiveSite=True,
                      returnDefault=True,
                      recurse=False) -> instrument.Instrument | None:
        '''
        Return the first Instrument found in this Stream, or None.

        >>> s = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.insert(instrument.Violin())
        >>> m1p1 = stream.Measure()
        >>> m1p1.append(note.Note('g'))
        >>> p1.append(m1p1)

        >>> p2 = stream.Part()
        >>> p2.insert(instrument.Viola())
        >>> m1p2 = stream.Measure()
        >>> m1p2.append(note.Note('f#'))
        >>> p2.append(m1p2)

        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> p1.getInstrument(returnDefault=False).instrumentName
        'Violin'
        >>> p2.getInstrument(returnDefault=False).instrumentName
        'Viola'

        * Changed in v7: added `recurse` (default False)
        '''
        post: Stream[instrument.Instrument] = self.getInstruments(
            searchActiveSite=searchActiveSite,
            returnDefault=returnDefault,
            recurse=recurse
        )
        return post.first()

    def invertDiatonic(self, inversionNote=note.Note('C4'), *, inPlace=False):
        '''
        inverts a stream diatonically around the given note (by default, middle C)

        For pieces where the key signature
        does not change throughout the piece it is MUCH faster than
        for pieces where the key signature changes.

        Here in this test, we put Ciconia's Quod Jactatur (a single voice
        piece that should have a canon solution: see trecento.quodJactatur)
        into 3 flats (instead of its original 1 flat) in measure 1, but
        into 5 sharps in measure 2 and then invert around F4, creating
        a new piece.

        >>> qj = corpus.parse('ciconia/quod_jactatur').parts[0].measures(1, 2)
        >>> qj.id = 'measureExcerpt'

        >>> qj.show('text')
        {0.0} <music21.instrument.Piano 'P1: MusicXML Part: Grand Piano'>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.clef.Treble8vbClef>
            {0.0} <music21.tempo.MetronomeMark Quarter=120 (playback only)>
            {0.0} <music21.key.Key of F major>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C>
            {1.5} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note E>
            {0.5} <music21.note.Note D>
            {1.0} <music21.note.Note C>
            {1.5} <music21.note.Note D>

        >>> qjFlat = qj.flatten()
        >>> k1 = qjFlat.getElementsByClass(key.KeySignature).first()
        >>> k3flats = key.KeySignature(-3)
        >>> qjFlat.replace(k1, k3flats, allDerived=True)
        >>> qj.getElementsByClass(stream.Measure)[1].insert(0, key.KeySignature(5))

        >>> qj2 = qj.invertDiatonic(note.Note('F4'), inPlace=False)
        >>> qj2.show('text')
        {0.0} <music21.instrument.Piano 'P1: MusicXML Part: Grand Piano'>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.clef.Treble8vbClef>
            {0.0} <music21.tempo.MetronomeMark Quarter=120 (playback only)>
            {0.0} <music21.key.KeySignature of 3 flats>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note B->
            {1.5} <music21.note.Note A->
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.key.KeySignature of 5 sharps>
            {0.0} <music21.note.Note G#>
            {0.5} <music21.note.Note A#>
            {1.0} <music21.note.Note B>
            {1.5} <music21.note.Note A#>

        * Changed in v5: inPlace is False by default.
        '''
        if inPlace:
            returnStream = self
        else:
            returnStream = self.coreCopyAsDerivation('invertDiatonic')

        keySigSearch = returnStream.recurse().getElementsByClass(key.KeySignature)

        quickSearch = True
        if not keySigSearch:
            ourKey = key.Key('C')
        elif len(keySigSearch) == 1:
            ourKey = keySigSearch[0]
        else:
            ourKey = None  # for might be undefined warning
            quickSearch = False

        inversionDNN = inversionNote.pitch.diatonicNoteNum
        for n in returnStream[note.NotRest]:
            n.pitch.diatonicNoteNum = (2 * inversionDNN) - n.pitch.diatonicNoteNum
            if quickSearch:  # use previously found
                n.pitch.accidental = ourKey.accidentalByStep(n.pitch.step)
            else:  # use context search
                ksActive = n.getContextByClass(key.KeySignature)
                n.pitch.accidental = ksActive.accidentalByStep(n.pitch.step)

            if n.pitch.accidental is not None:
                n.pitch.accidental.displayStatus = None

        if not inPlace:
            return returnStream

    # -------------------------------------------------------------------------
    # offset manipulation

    def shiftElements(self, offset, startOffset=None, endOffset=None, classFilterList=None):
        '''
        Add the given offset value to every offset of
        the objects found in the Stream. Objects that are
        specifically placed at the end of the Stream via
        .storeAtEnd() (such as right barlines) are
        not affected.

        If startOffset is given then elements before
        that offset will not be shifted.  If endOffset is given
        then all elements at or after this offset will be not be shifted.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note('C'), list(range(10)))
        >>> a.shiftElements(30)
        >>> a.lowestOffset
        30.0
        >>> a.shiftElements(-10)
        >>> a.lowestOffset
        20.0

        Use shiftElements to move elements after a change in
        duration:

        >>> st2 = stream.Stream()
        >>> st2.insert(0, note.Note('D4', type='whole'))
        >>> st2.repeatInsert(note.Note('C4'), list(range(4, 8)))
        >>> st2.show('text')
        {0.0} <music21.note.Note D>
        {4.0} <music21.note.Note C>
        {5.0} <music21.note.Note C>
        {6.0} <music21.note.Note C>
        {7.0} <music21.note.Note C>

        Now make the first note a dotted whole note and shift the rest by two quarters...

        >>> firstNote = st2[0]
        >>> firstNoteOldQL = firstNote.quarterLength
        >>> firstNote.duration.dots = 1
        >>> firstNoteNewQL = firstNote.quarterLength
        >>> shiftAmount = firstNoteNewQL - firstNoteOldQL
        >>> shiftAmount
        2.0

        >>> st2.shiftElements(shiftAmount, startOffset=4.0)
        >>> st2.show('text')
        {0.0} <music21.note.Note D>
        {6.0} <music21.note.Note C>
        {7.0} <music21.note.Note C>
        {8.0} <music21.note.Note C>
        {9.0} <music21.note.Note C>

        A class filter list may be given.  It must be an iterable.

        >>> st2.insert(7.5, key.Key('F'))
        >>> st2.shiftElements(2/3, startOffset=6.0, endOffset=8.0,
        ...                   classFilterList=[note.Note])
        >>> st2.show('text')
        {0.0} <music21.note.Note D>
        {6.6667} <music21.note.Note C>
        {7.5} <music21.key.Key of F major>
        {7.6667} <music21.note.Note C>
        {8.0} <music21.note.Note C>
        {9.0} <music21.note.Note C>
        '''
        # only want _elements, do not want _endElements
        for e in self._elements:

            if startOffset is not None and self.elementOffset(e) < startOffset:
                continue
            if endOffset is not None and self.elementOffset(e) >= endOffset:
                continue
            if classFilterList is not None and e.classSet.isdisjoint(classFilterList):
                continue

            self.coreSetElementOffset(e, opFrac(self.elementOffset(e) + offset))

        self.coreElementsChanged()

    def transferOffsetToElements(self):
        '''
        Transfer the offset of this stream to all
        internal elements; then set
        the offset of this stream to zero.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note('C'), list(range(10)))
        >>> a.offset = 30
        >>> a.transferOffsetToElements()
        >>> a.lowestOffset
        30.0
        >>> a.offset
        0.0
        >>> a.offset = 20
        >>> a.transferOffsetToElements()
        >>> a.lowestOffset
        50.0
        '''
        self.shiftElements(self.offset)
        self.offset = 0.0

    # -------------------------------------------------------------------------
    # utilities for creating large numbers of elements

    def repeatAppend(self, item, numberOfTimes):
        '''
        Given an object and a number, run append that many times on
        a deepcopy of the object.
        numberOfTimes should of course be a positive integer.

        >>> a = stream.Stream()
        >>> n = note.Note('D--')
        >>> n.duration.type = 'whole'
        >>> a.repeatAppend(n, 10)
        >>> a.show('text')
        {0.0} <music21.note.Note D-->
        {4.0} <music21.note.Note D-->
        {8.0} <music21.note.Note D-->
        {12.0} <music21.note.Note D-->
        ...
        {36.0} <music21.note.Note D-->

        >>> a.duration.quarterLength
        40.0
        >>> a[9].offset
        36.0
        '''
        try:
            unused = item.isStream
            element = item
        # if not isinstance(item, music21.Music21Object):
        except AttributeError:
            # element = music21.ElementWrapper(item)
            raise StreamException('to put a non Music21Object in a stream, '
                                  + 'create a music21.ElementWrapper for the item')
        # # if not an element, embed
        # if not isinstance(item, music21.Music21Object):
        #     element = music21.ElementWrapper(item)
        # else:
        #     element = item

        for unused_i in range(numberOfTimes):
            self.append(copy.deepcopy(element))

    def repeatInsert(self, item, offsets):
        '''
        Given an object, create a deep copy of each object at
        each position specified by the offset list:

        >>> a = stream.Stream()
        >>> n = note.Note('G-')
        >>> n.quarterLength = 1

        >>> a.repeatInsert(n, [0, 2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11, 12])
        >>> len(a)
        13
        >>> a[10].offset
        10.0
        '''
        if not common.isIterable(offsets):
            raise StreamException(f'must provide an iterable of offsets, not {offsets}')

        try:
            unused = item.isStream
            element = item
        # if not isinstance(item, music21.Music21Object):
        except AttributeError:
            # if not an element, embed
            # element = music21.ElementWrapper(item)
            raise StreamException('to put a non Music21Object in a stream, '
                                  + 'create a music21.ElementWrapper for the item')
        # if not isinstance(item, music21.Music21Object):
        #     # if not an element, embed
        #     element = music21.ElementWrapper(item)
        # else:
        #     element = item

        for offset in offsets:
            elementCopy = copy.deepcopy(element)
            self.coreInsert(offset, elementCopy)
        self.coreElementsChanged()

    def extractContext(self, searchElement, before=4.0, after=4.0,
                       maxBefore=None, maxAfter=None):
        '''
        Extracts elements around the given element within (before)
        quarter notes and (after) quarter notes (default 4), and
        returns a new Stream.

        >>> qn = note.Note(type='quarter')
        >>> qtrStream = stream.Stream()
        >>> qtrStream.repeatInsert(qn, [0, 1, 2, 3, 4, 5])
        >>> hn = note.Note(type='half')
        >>> hn.name = 'B-'
        >>> qtrStream.append(hn)
        >>> qtrStream.repeatInsert(qn, [8, 9, 10, 11])
        >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
        >>> hnStream.show('text')
        {5.0} <music21.note.Note C>
        {6.0} <music21.note.Note B->
        {8.0} <music21.note.Note C>

        * Changed in v7: forceOutputClass removed.

        OMIT_FROM_DOCS
        TODO: maxBefore -- maximum number of elements to return before; etc.
        TODO: use .template to get new Stream

        NOTE: RENAME: this probably should be renamed, as we use Context in a special way.
        Perhaps better is extractNeighbors?

        '''
        display = self.cloneEmpty('extractContext')

        found = None
        foundOffset = 0
        foundEnd = 0
        elements = self.elements
        for i in range(len(elements)):
            b = elements[i]
            if b.id == searchElement.id:
                found = i
                foundOffset = self.elementOffset(elements[i])
                foundEnd = foundOffset + elements[i].duration.quarterLength
            elif b is searchElement:
                found = i
                foundOffset = self.elementOffset(elements[i])
                foundEnd = foundOffset + elements[i].duration.quarterLength
        if found is None:
            raise StreamException('Could not find the element in the stream')

        # handle _elements and _endElements independently
        for e in self._elements:
            o = self.elementOffset(e)
            if foundOffset - before <= o < foundEnd + after:
                display.coreInsert(o, e)

        for e in self._endElements:
            o = self.elementOffset(e)
            if foundOffset - before <= o < foundEnd + after:
                display.coreStoreAtEnd(e)
        display.coreElementsChanged()
        return display

    # --------------------------------------------------------------------------
    # transformations of self that return a new Stream

    def _uniqueOffsetsAndEndTimes(self, offsetsOnly=False, endTimesOnly=False):
        '''
        Get a list of all offsets and endtimes
        of notes and rests in this stream.

        Helper method for makeChords and Chordify
        run on .flatten().notesAndRests


        >>> s = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.insert(4, note.Note('C#'))
        >>> p1.insert(5.3, note.Rest())
        >>> p2 = stream.Part()
        >>> p2.insert(2.12, note.Note('D-', type='half'))
        >>> p2.insert(5.5, note.Rest())
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)

        We will get a mix of float and fractions.Fraction() objects

        >>> [str(o) for o in s.flatten()._uniqueOffsetsAndEndTimes()]
        ['53/25', '4.0', '103/25', '5.0', '53/10', '5.5', '63/10', '6.5']

        Limit what is returned:

        >>> [str(o) for o in s.flatten()._uniqueOffsetsAndEndTimes(offsetsOnly=True)]
        ['53/25', '4.0', '53/10', '5.5']
        >>> [str(o) for o in s.flatten()._uniqueOffsetsAndEndTimes(endTimesOnly=True)]
        ['103/25', '5.0', '63/10', '6.5']

        And this is useless...  :-)

        >>> s.flatten()._uniqueOffsetsAndEndTimes(offsetsOnly=True, endTimesOnly=True)
        []

        '''
        offsetDictValues = self._offsetDict.values()
        if endTimesOnly:
            offsets = set()
        else:
            offsets = {opFrac(v[0]) for v in offsetDictValues}

        if offsetsOnly:
            endTimes = set()
        else:
            endTimes = {opFrac(v[0] + v[1].duration.quarterLength)
                            for v in offsetDictValues}
        return sorted(offsets.union(endTimes))

    def chordify(
        self,
        *,
        addTies=True,
        addPartIdAsGroup=False,
        removeRedundantPitches=True,
        toSoundingPitch=True,
        copyPitches=True,
    ):
        # noinspection PyShadowingNames
        '''
        Create a chordal reduction of polyphonic music, where each
        change to a new pitch results in a new chord. If a Score or
        Part of Measures is provided, a Stream of Measures will be
        returned. If a flat Stream of notes, or a Score of such
        Streams is provided, no Measures will be returned.

        If using chordify with chord symbols, ensure that the ChordSymbol objects
        have durations (by default, the duration of a ChordSymbol object is 0, unlike
        a Chord object). If Harmony objects are not provided a duration, they
        will not be included in the chordified output pitches but may appear as chord symbols
        in notation on the score. To realize the chord symbol durations on a score, call
        :meth:`music21.harmony.realizeChordSymbolDurations` and pass in the score.

        This functionality works by splitting all Durations in
        all parts, or if there are multiple parts by all unique offsets. All
        simultaneous durations are then gathered into single chords.

        If `addPartIdAsGroup` is True, all elements found in the
        Stream will have their source Part id added to the
        element's pitches' Group.  These groups names are useful
        for partially "de-chordifying" the output.  If the element chordifies to
        a :class:`~music21.chord.Chord` object, then the group will be found in each
        :class:`~music21.pitch.Pitch` element's .groups in Chord.pitches.  If the
        element chordifies to a single :class:`~music21.note.Note` then .pitch.groups
        will hold the group name.

        The `addTies` parameter currently does not work for pitches in Chords.

        If `toSoundingPitch` is True, all parts that define one or
        more transpositions will be transposed to sounding pitch before chordification.
        True by default.

        >>> s = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.id = 'part1'
        >>> p1.insert(4, note.Note('C#4'))
        >>> p1.insert(5.3, note.Rest())
        >>> p2 = stream.Part()
        >>> p2.id = 'part2'
        >>> p2.insert(2.12, note.Note('D-4', type='half'))
        >>> p2.insert(5.5, note.Rest())
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> s.show('text', addEndTimes=True)
        {0.0 - 6.3} <music21.stream.Part part1>
            {4.0 - 5.0} <music21.note.Note C#>
            {5.3 - 6.3} <music21.note.Rest quarter>
        {0.0 - 6.5} <music21.stream.Part part2>
            {2.12 - 4.12} <music21.note.Note D->
            {5.5 - 6.5} <music21.note.Rest quarter>

        >>> cc = s.chordify()

        >>> cc[3]
        <music21.chord.Chord C#4>
        >>> cc[3].duration.quarterLength
        Fraction(22, 25)

        >>> cc.show('text', addEndTimes=True)
        {0.0 - 2.12} <music21.note.Rest 53/25ql>
        {2.12 - 4.0} <music21.chord.Chord D-4>
        {4.0 - 4.12} <music21.chord.Chord C#4 D-4>
        {4.12 - 5.0} <music21.chord.Chord C#4>
        {5.0 - 6.5} <music21.note.Rest dotted-quarter>

        Here's how addPartIdAsGroup works:

        >>> cc2 = s.chordify(addPartIdAsGroup=True)
        >>> cSharpDFlatChord = cc2[2]
        >>> for p in cSharpDFlatChord.pitches:
        ...     (str(p), p.groups)
        ('C#4', ['part1'])
        ('D-4', ['part2'])

        >>> s = stream.Stream()
        >>> p1 = stream.Part()
        >>> p1.insert(0, harmony.ChordSymbol('Cm', quarterLength=4.0))
        >>> p1.insert(2, note.Note('C2'))
        >>> p1.insert(4, harmony.ChordSymbol('D', quarterLength=4.0))
        >>> p1.insert(7, note.Note('A2'))
        >>> s.insert(0, p1)
        >>> s.chordify().show('text')
        {0.0} <music21.chord.Chord C3 E-3 G3>
        {2.0} <music21.chord.Chord C2 C3 E-3 G3>
        {3.0} <music21.chord.Chord C3 E-3 G3>
        {4.0} <music21.chord.Chord D3 F#3 A3>
        {7.0} <music21.chord.Chord A2 D3 F#3 A3>

        Note that :class:`~music21.harmony.ChordSymbol` objects can also be chordified:

        >>> s = stream.Stream()
        >>> p2 = stream.Part()
        >>> p1 = stream.Part()
        >>> p2.insert(0, harmony.ChordSymbol('Cm', quarterLength=4.0))
        >>> p1.insert(2, note.Note('C2'))
        >>> p2.insert(4, harmony.ChordSymbol('D', quarterLength=4.0))
        >>> p1.insert(7, note.Note('A2'))
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> s.chordify().show('text')
        {0.0} <music21.chord.Chord C3 E-3 G3>
        {2.0} <music21.chord.Chord C2 C3 E-3 G3>
        {3.0} <music21.chord.Chord C3 E-3 G3>
        {4.0} <music21.chord.Chord D3 F#3 A3>
        {7.0} <music21.chord.Chord A2 D3 F#3 A3>

        If addPartIdAsGroup is True, and there are redundant pitches,
        ensure that the merged pitch has both groups

        >>> s = stream.Score()
        >>> p0 = stream.Part(id='p0')
        >>> p0.insert(0, note.Note('C4'))
        >>> p1 = stream.Part(id='p1')
        >>> p1.insert(0, note.Note('C4'))
        >>> s.insert(0, p0)
        >>> s.insert(0, p1)
        >>> s1 = s.chordify(addPartIdAsGroup=True)
        >>> c = s1.recurse().notes[0]
        >>> c
        <music21.chord.Chord C4>
        >>> c.pitches[0].groups
        ['p0', 'p1']

        With copyPitches = False, then the original pitches are retained, which
        together with removeRedundantPitches=False can be a powerful tool for
        working back to the original score:

        >>> n00 = note.Note('C4')
        >>> n01 = note.Note('E4')
        >>> n10 = note.Note('E4', type='half')
        >>> p0 = stream.Part(id='p0')
        >>> p1 = stream.Part(id='p1')
        >>> p0.append([n00, n01])
        >>> p1.append(n10)
        >>> s = stream.Score()
        >>> s.insert(0, p0)
        >>> s.insert(0, p1)
        >>> ss = s.chordify(removeRedundantPitches=False, copyPitches=False, addPartIdAsGroup=True)
        >>> ss.show('text')
        {0.0} <music21.chord.Chord C4 E4>
        {1.0} <music21.chord.Chord E4 E4>

        >>> c1 = ss.recurse().notes[1]
        >>> for p in c1.pitches:
        ...     if 'p0' in p.groups:
        ...         p.step = 'G'  # make a complete triad
        >>> n01
        <music21.note.Note G>

        * Changed in v5:
          - Runs a little faster for small scores and run a TON faster for big scores
          running in O(n) time not O(n^2)
          - no longer supported: displayTiedAccidentals=False,
        * Changed in v6.3: Added copyPitches

        OMIT_FROM_DOCS

        Test that chordifying works on a single stream.

        >>> f2 = stream.Score()
        >>> f2.insert(0, metadata.Metadata())
        >>> f2.insert(0, note.Note('C4'))
        >>> f2.insert(0, note.Note('D#4'))
        >>> c = f2.chordify()
        >>> cn = c.notes
        >>> cn[0].pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch D#4>)
        '''
        def chordifyOneMeasure(templateInner, streamToChordify):
            '''
            streamToChordify is either a Measure or a Score=MeasureSlice
            '''
            timespanTree = streamToChordify.asTimespans(classList=(note.GeneralNote,))
            allTimePoints = timespanTree.allTimePoints()
            if 0 not in allTimePoints:
                allTimePoints = (0,) + allTimePoints

            for offset, endTime in zip(allTimePoints, allTimePoints[1:]):
                if isclose(offset, endTime, abs_tol=1e-7):
                    continue
                vert = timespanTree.getVerticalityAt(offset)
                quarterLength = endTime - offset
                if quarterLength < 0:  # pragma: no cover
                    environLocal.warn(
                        'Something is wrong with the verticality '
                        + f'in stream {templateInner!r}: {vert!r} '
                        + f'its endTime {endTime} is less than its offset {offset}'
                    )

                chordOrRest = vert.makeElement(quarterLength,
                                               addTies=addTies,
                                               addPartIdAsGroup=addPartIdAsGroup,
                                               removeRedundantPitches=removeRedundantPitches,
                                               copyPitches=copyPitches,
                                               )

                templateInner.coreInsert(opFrac(offset), chordOrRest)
            templateInner.coreElementsChanged()
            consolidateRests(templateInner)

        def consolidateRests(templateInner):
            consecutiveRests = []
            for el in list(templateInner.notesAndRests):
                if not isinstance(el, note.Rest):
                    removeConsecutiveRests(templateInner, consecutiveRests)
                    consecutiveRests = []
                else:
                    consecutiveRests.append(el)
            removeConsecutiveRests(templateInner, consecutiveRests)

        def removeConsecutiveRests(templateInner, consecutiveRests):
            if len(consecutiveRests) < 2:
                return
            totalDuration = sum(r.duration.quarterLength for r in consecutiveRests)
            startOffset = templateInner.elementOffset(consecutiveRests[0])
            for r in consecutiveRests:
                templateInner.remove(r)
            rNew = note.Rest()
            rNew.duration.quarterLength = totalDuration
            templateInner.insert(startOffset, rNew)

        # --------------------------------------
        if toSoundingPitch:
            # environLocal.printDebug(['at sounding pitch', allParts[0].atSoundingPitch])
            if (self.hasPartLikeStreams()
                     and self.getElementsByClass('Stream').first().atSoundingPitch is False):
                workObj = self.toSoundingPitch(inPlace=False)
            elif self.atSoundingPitch is False:
                workObj = self.toSoundingPitch(inPlace=False)
            else:
                workObj = self
        else:
            workObj = self

        if self.hasPartLikeStreams():
            # use the measure boundaries of the first Part as a template.
            templateStream = workObj.getElementsByClass(Stream).first()
        else:
            templateStream = workObj

        template = templateStream.template(fillWithRests=False,
                                           removeClasses=('GeneralNote',),
                                           retainVoices=False)

        if template.hasMeasures():
            measureIterator = template.getElementsByClass(Measure)
            for i, templateMeasure in enumerate(measureIterator):
                # measurePart is likely a Score (MeasureSlice), not a measure
                measurePart = workObj.measure(i, collect=(), indicesNotNumbers=True)
                if measurePart is not None:
                    chordifyOneMeasure(templateMeasure, measurePart)
                else:
                    environLocal.warn(f'Malformed Part object, {workObj}, at measure index {i}')
        else:
            chordifyOneMeasure(template, workObj)

        # accidental displayStatus needs to change.
        for p in template.pitches:
            if p.accidental is not None and p.accidental.displayType != 'even-tied':
                p.accidental.displayStatus = None

        if (hasattr(workObj, 'metadata')
                and workObj.metadata is not None
                and workObj.hasPartLikeStreams() is True):
            template.insert(0, copy.deepcopy(workObj.metadata))

        return template

    def splitByClass(self, classObj, fx):
        # noinspection PyShadowingNames
        '''
        Given a stream, get all objects of type classObj and divide them into
        two new streams depending on the results of fx.
        Fx should be a lambda or other function on elements.
        All elements where fx returns "True" go in the first stream.
        All other elements are put in the second stream.

        If classObj is None then all elements are returned.  ClassObj
        can also be a list of classes.

        In this example, we will create 50 notes from midi note 30 (two
        octaves and a tritone below middle C) to midi note 80 (an octave
        and a minor sixth above middle C) and add them to a Stream.
        We then create a lambda function to split between those notes
        below middle C (midi note 60) and those above
        (google "lambda functions in Python" for more information on
        what these powerful tools are).


        >>> stream1 = stream.Stream()
        >>> for x in range(30, 81):
        ...     n = note.Note()
        ...     n.pitch.midi = x
        ...     stream1.append(n)
        >>> fx = lambda n: n.pitch.midi < 60
        >>> b, c = stream1.splitByClass(note.Note, fx)

        Stream b now contains all the notes below middle C,
        that is, 30 notes, beginning with F#1 and ending with B3
        while Stream c has the 21 notes from C4 to A-5:

        >>> len(b)
        30
        >>> (b[0].nameWithOctave, b[-1].nameWithOctave)
        ('F#1', 'B3')
        >>> len(c)
        21
        >>> (c[0].nameWithOctave, c[-1].nameWithOctave)
        ('C4', 'G#5')
        '''
        a = self.cloneEmpty(derivationMethod='splitByClass')
        b = self.cloneEmpty(derivationMethod='splitByClass')
        if classObj is not None:
            found = self.getElementsByClass(classObj).stream()
        else:
            found = self
        for e in found:
            if fx(e):
                a.coreInsert(found.elementOffset(e), e)  # provide an offset here
            else:
                b.coreInsert(found.elementOffset(e), e)
        for e in found._endElements:
            if fx(e):
                # a.storeAtEnd(e)
                a.coreStoreAtEnd(e)
            else:
                # b.storeAtEnd(e)
                b.coreStoreAtEnd(e)
        a.coreElementsChanged()
        b.coreElementsChanged()
        return a, b

    def offsetMap(self, srcObj=None):
        '''
        Returns a list where each element is a NamedTuple
        consisting of the 'offset' of each element in a stream, the
        'endTime' (that is, the offset plus the duration) and the
        'element' itself.  Also contains a 'voiceIndex' entry which
        contains the voice number of the element, or None if there
        are no voices.

        >>> n1 = note.Note(type='quarter')
        >>> c1 = clef.AltoClef()
        >>> n2 = note.Note(type='half')
        >>> s1 = stream.Stream()
        >>> s1.append([n1, c1, n2])
        >>> om = s1.offsetMap()
        >>> om[2].offset
        1.0
        >>> om[2].endTime
        3.0
        >>> om[2].element is n2
        True
        >>> om[2].voiceIndex


        Needed for makeMeasures and a few other places.

        The Stream source of elements is self by default,
        unless a `srcObj` is provided.  (this will be removed in v.8)


        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 8)
        >>> for om in s.offsetMap():
        ...     om
        OffsetMap(element=<music21.note.Note C>, offset=0.0, endTime=1.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=1.0, endTime=2.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=2.0, endTime=3.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=3.0, endTime=4.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=4.0, endTime=5.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=5.0, endTime=6.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=6.0, endTime=7.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=7.0, endTime=8.0, voiceIndex=None)
        '''
        if srcObj is None:
            srcObj = self
        # assume that flat/sorted options will be set before processing
        offsetMap = []  # list of start, start+dur, element
        if srcObj.hasVoices():
            groups = []
            for i, v in enumerate(srcObj.voices):
                groups.append((v.flatten(), i))
            elsNotOfVoice = srcObj.getElementsNotOfClass('Voice')
            if elsNotOfVoice:
                groups.insert(0, (elsNotOfVoice.stream(), None))
        else:  # create a single collection
            groups = [(srcObj, None)]
        # environLocal.printDebug(['offsetMap', groups])
        for group, voiceIndex in groups:
            for e in group._elements:
                # do not include barlines
                if isinstance(e, bar.Barline):
                    continue
                dur = e.duration.quarterLength
                offset = group.elementOffset(e)
                endTime = opFrac(offset + dur)
                # NOTE: used to make a copy.copy of elements here;
                # this is not necessary b/c making deepcopy of entire Stream
                thisOffsetMap = OffsetMap(e, offset, endTime, voiceIndex)
                # environLocal.printDebug(['offsetMap: thisOffsetMap', thisOffsetMap])
                offsetMap.append(thisOffsetMap)
                # offsetMap.append((offset, offset + dur, e, voiceIndex))
                # offsetMap.append([offset, offset + dur, copy.copy(e)])
        return offsetMap

    def makeMeasures(
        self,
        meterStream=None,
        refStreamOrTimeRange=None,
        searchContext=False,
        innerBarline=None,
        finalBarline='final',
        bestClef=False,
        inPlace=False,
    ):
        '''
        Return a new stream (or if inPlace=True change in place) this
        Stream so that it has internal measures.

        For more details, see :py:func:`~music21.stream.makeNotation.makeMeasures`.
        '''
        return makeNotation.makeMeasures(
            self,
            meterStream=meterStream,
            refStreamOrTimeRange=refStreamOrTimeRange,
            searchContext=searchContext,
            innerBarline=innerBarline,
            finalBarline=finalBarline,
            bestClef=bestClef,
            inPlace=inPlace,
        )

    def makeRests(
        self,
        refStreamOrTimeRange=None,
        fillGaps=False,
        timeRangeFromBarDuration=False,
        inPlace=False,
        hideRests=False,
    ):
        '''
        Calls :py:func:`~music21.stream.makeNotation.makeRests`.

        * Changed in v7, inPlace=False by default.
        '''
        return makeNotation.makeRests(
            self,
            refStreamOrTimeRange=refStreamOrTimeRange,
            fillGaps=fillGaps,
            timeRangeFromBarDuration=timeRangeFromBarDuration,
            inPlace=inPlace,
            hideRests=hideRests,
        )

    def makeTies(self,
                 meterStream=None,
                 inPlace=False,
                 displayTiedAccidentals=False,
                 classFilterList=(note.GeneralNote,),
                 ):
        '''
        Calls :py:func:`~music21.stream.makeNotation.makeTies`.

        * Changed in v4: inPlace=False by default.
        * New in v.7: `classFilterList`.
        '''
        return makeNotation.makeTies(
            self,
            meterStream=meterStream,
            inPlace=inPlace,
            displayTiedAccidentals=displayTiedAccidentals,
            classFilterList=classFilterList,
        )

    def makeBeams(self, *, inPlace=False, setStemDirections=True, failOnNoTimeSignature=False):
        '''
        Return a new Stream, or modify the Stream in place, with beams applied to all
        notes.

        See :py:func:`~music21.stream.makeNotation.makeBeams`.

        * New in v6.7: setStemDirections.
        * New in v7: failOnNoTimeSignature raises StreamException if no TimeSignature
          exists in the stream context from which to make measures.
        '''
        return makeNotation.makeBeams(
            self,
            inPlace=inPlace,
            setStemDirections=setStemDirections,
            failOnNoTimeSignature=failOnNoTimeSignature,
        )

    def makeAccidentals(
        self,
        *,
        pitchPast: list[pitch.Pitch] | None = None,
        pitchPastMeasure: list[pitch.Pitch] | None = None,
        otherSimultaneousPitches: list[pitch.Pitch] | None = None,
        useKeySignature: bool | key.KeySignature = True,
        alteredPitches: list[pitch.Pitch] | None = None,
        searchKeySignatureByContext: bool = False,
        cautionaryPitchClass: bool = True,
        cautionaryAll: bool = False,
        inPlace: bool = False,
        overrideStatus: bool = False,
        cautionaryNotImmediateRepeat: bool = True,
        tiePitchSet: set[str] | None = None
    ):
        '''
        A method to set and provide accidentals given various conditions and contexts.

        `pitchPast` is a list of pitches preceding this pitch in this measure.

        `pitchPastMeasure` is a list of pitches preceding this pitch but in a previous measure.

        `otherSimultaneousPitches` is a list of other pitches in this simultaneity, for use
        when `cautionaryPitchClass` is True.

        If `useKeySignature` is True, a :class:`~music21.key.KeySignature` will be searched
        for in this Stream or this Stream's defined contexts. An alternative KeySignature
        can be supplied with this object and used for temporary pitch processing.

        If `alteredPitches` is a list of modified pitches (Pitches with Accidentals) that
        can be directly supplied to Accidental processing. These are the same values obtained
        from a :class:`music21.key.KeySignature` object using the
        :attr:`~music21.key.KeySignature.alteredPitches` property.

        If `cautionaryPitchClass` is True, comparisons to past accidentals are made regardless
        of register. That is, if a past sharp is found two octaves above a present natural,
        a natural sign is still displayed.

        If `cautionaryAll` is True, all accidentals are shown.

        If `overrideStatus` is True, this method will ignore any current `displayStatus` setting
        found on the Accidental. By default this does not happen. If `displayStatus` is set to
        None, the Accidental's `displayStatus` is set.

        If `cautionaryNotImmediateRepeat` is True, cautionary accidentals will be displayed for
        an altered pitch even if that pitch had already been displayed as altered.

        If `tiePitchSet` is not None it should be a set of `.nameWithOctave` strings
        to determine whether following accidentals should be shown because the last
        note of the same pitch had a start or continue tie.

        If `searchKeySignatureByContext` is True then keySignatures from the context of the
        stream will be used if none found.

        The :meth:`~music21.pitch.Pitch.updateAccidentalDisplay` method is used to determine if
        an accidental is necessary.

        This will assume that the complete Stream is the context of evaluation. For smaller context
        ranges, call this on Measure objects.

        If `inPlace` is True, this is done in-place; if `inPlace` is False,
        this returns a modified deep copy.

        * Changed in v6: does not return anything if inPlace is True.
        * Changed in v7: default inPlace is False
        * Changed in v8: altered unisons/octaves in Chords now supply clarifying naturals.

        All arguments are keyword only.
        '''
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('makeAccidentals')
        else:
            returnObj = self

        # need to reset these lists unless values explicitly provided
        if pitchPast is None:
            pitchPast = []
        if pitchPastMeasure is None:
            pitchPastMeasure = []
        # see if there is any key signatures to add to altered pitches
        if alteredPitches is None:
            alteredPitches = []
        addAlteredPitches: list[pitch.Pitch] = []
        if isinstance(useKeySignature, key.KeySignature):
            addAlteredPitches = useKeySignature.alteredPitches
        elif useKeySignature is True:  # get from defined contexts
            # will search local, then activeSite
            ksIter: t.Union[
                list[key.KeySignature],
                iterator.StreamIterator[key.KeySignature],
                None,
            ] = None
            if searchKeySignatureByContext:
                ks = self.getContextByClass(key.KeySignature)
                if ks is not None:
                    ksIter = [ks]
            else:
                ksIter = self.getElementsByClass(key.KeySignature)

            if ksIter:
                # assume we want the first found; in some cases it is possible
                # that this may not be true
                addAlteredPitches = ksIter[0].alteredPitches
        alteredPitches += addAlteredPitches
        # environLocal.printDebug(['processing makeAccidentals() with alteredPitches:',
        #   alteredPitches])

        # need to move through notes in order
        # recurse to capture notes in substreams: https://github.com/cuthbertLab/music21/issues/577
        noteIterator = returnObj.recurse().notesAndRests

        # environLocal.printDebug(['alteredPitches', alteredPitches])
        # environLocal.printDebug(['pitchPast', pitchPast])

        if tiePitchSet is None:
            tiePitchSet = set()

        last_measure: Measure | None = None

        for e in noteIterator:
            if e.activeSite is not None and e.activeSite.isMeasure:
                if last_measure is not None and e.activeSite is not last_measure:
                    # New measure encountered: move pitchPast to
                    # pitchPastMeasure and clear pitchPast
                    pitchPastMeasure = pitchPast[:]
                    pitchPast = []
                last_measure = e.activeSite
            if isinstance(e, note.Note):
                if e.pitch.nameWithOctave in tiePitchSet:
                    lastNoteWasTied = True
                else:
                    lastNoteWasTied = False

                e.pitch.updateAccidentalDisplay(
                    pitchPast=pitchPast,
                    pitchPastMeasure=pitchPastMeasure,
                    alteredPitches=alteredPitches,
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll,
                    overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                    lastNoteWasTied=lastNoteWasTied)
                pitchPast.append(e.pitch)

                tiePitchSet.clear()
                if e.tie is not None and e.tie.type != 'stop':
                    tiePitchSet.add(e.pitch.nameWithOctave)

                # handle this note's ornaments' ornamentalPitches
                makeNotation.makeOrnamentalAccidentals(
                    e,
                    pitchPast=pitchPast,
                    pitchPastMeasure=pitchPastMeasure,
                    alteredPitches=alteredPitches,
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll,
                    overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat)

            elif isinstance(e, chord.Chord):
                # when reading a chord, this will apply an accidental
                # if pitches in the chord suggest an accidental
                seenPitchNames = set()

                for n in list(e):
                    p = n.pitch
                    if p.nameWithOctave in tiePitchSet:
                        lastNoteWasTied = True
                    else:
                        lastNoteWasTied = False

                    otherSimultaneousPitches = [other for other in e.pitches if other is not p]

                    p.updateAccidentalDisplay(
                        pitchPast=pitchPast,
                        pitchPastMeasure=pitchPastMeasure,
                        otherSimultaneousPitches=otherSimultaneousPitches,
                        alteredPitches=alteredPitches,
                        cautionaryPitchClass=cautionaryPitchClass,
                        cautionaryAll=cautionaryAll,
                        overrideStatus=overrideStatus,
                        cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                        lastNoteWasTied=lastNoteWasTied)

                    if n.tie is not None and n.tie.type != 'stop':
                        seenPitchNames.add(p.nameWithOctave)

                    # handle this note-in-chord's ornaments' ornamentalPitches
                    makeNotation.makeOrnamentalAccidentals(
                        n,
                        pitchPast=pitchPast,
                        pitchPastMeasure=pitchPastMeasure,
                        alteredPitches=alteredPitches,
                        cautionaryPitchClass=cautionaryPitchClass,
                        cautionaryAll=cautionaryAll,
                        overrideStatus=overrideStatus,
                        cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat)

                tiePitchSet.clear()
                for pName in seenPitchNames:
                    tiePitchSet.add(pName)

                pitchPast += e.pitches

                # handle this chord's ornaments' ornamentalPitches
                makeNotation.makeOrnamentalAccidentals(
                    e,
                    pitchPast=pitchPast,
                    pitchPastMeasure=pitchPastMeasure,
                    alteredPitches=alteredPitches,
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll,
                    overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat)

            else:
                tiePitchSet.clear()

        returnObj.streamStatus.accidentals = True

        if not inPlace:
            return returnObj

    def haveAccidentalsBeenMade(self):
        # could be called: hasAccidentalDisplayStatusSet
        '''
        If Accidentals.displayStatus is None for all
        contained pitches, it as assumed that accidentals
        have not been set for display and/or makeAccidentals
        has not been run. If any Accidental has displayStatus
        other than None, this method returns True, regardless
        of if makeAccidentals has actually been run.
        '''
        return self.streamStatus.accidentals

    def makeNotation(self: StreamType,
                     *,
                     meterStream=None,
                     refStreamOrTimeRange=None,
                     inPlace=False,
                     bestClef=False,
                     pitchPast: list[pitch.Pitch] | None = None,
                     pitchPastMeasure: list[pitch.Pitch] | None = None,
                     useKeySignature: bool | key.KeySignature = True,
                     alteredPitches: list[pitch.Pitch] | None = None,
                     cautionaryPitchClass: bool = True,
                     cautionaryAll: bool = False,
                     overrideStatus: bool = False,
                     cautionaryNotImmediateRepeat: bool = True,
                     tiePitchSet: set[str] | None = None
                     ):
        '''
        This method calls a sequence of Stream methods on this Stream to prepare
        notation, including creating voices for overlapped regions, Measures
        if necessary, creating ties, beams, accidentals, and tuplet brackets.

        If `inPlace` is True, this is done in-place.
        if `inPlace` is False, this returns a modified deep copy.

        The following additional parameters are documented on
        :meth:`~music21.stream.base.makeAccidentals`::

            pitchPast
            pitchPastMeasure
            useKeySignature
            alteredPitches
            cautionaryPitchClass
            cautionaryAll
            overrideStatus
            cautionaryNotImmediateRepeat
            tiePitchSet


        >>> s = stream.Stream()
        >>> n = note.Note('g')
        >>> n.quarterLength = 1.5
        >>> s.repeatAppend(n, 10)
        >>> sMeasures = s.makeNotation()
        >>> len(sMeasures.getElementsByClass(stream.Measure))
        4
        >>> sMeasures.getElementsByClass(stream.Measure).last().rightBarline.type
        'final'

        * Changed in v7: `inPlace=True` returns `None`.
        '''
        # determine what is the object to work on first
        returnStream: StreamType | Stream[t.Any]
        if inPlace:
            returnStream = self
        else:
            returnStream = self.coreCopyAsDerivation('makeNotation')

        # if 'finalBarline' in subroutineKeywords:
        #     lastBarlineType = subroutineKeywords['finalBarline']
        # else:
        #     lastBarlineType = 'final'

        # retrieve necessary spanners; insert only if making a copy
        returnStream.coreGatherMissingSpanners(
            insert=not inPlace,
            # definitely do NOT put a constrainingSpannerBundle constraint
        )
        # only use inPlace arg on first usage
        if not returnStream.hasMeasures():
            # only try to make voices if no Measures are defined
            returnStream.makeVoices(inPlace=True, fillGaps=True)
            # if this is not inPlace, it will return a newStream; if
            # inPlace, this returns None
            # use inPlace=True, as already established above
            returnStream.makeMeasures(
                meterStream=meterStream,
                refStreamOrTimeRange=refStreamOrTimeRange,
                inPlace=True,
                bestClef=bestClef)

            if not returnStream.hasMeasures():
                raise StreamException(
                    f'no measures found in stream with {len(self)} elements')

        # for now, calling makeAccidentals once per measures
        # pitches from last measure are passed
        # this needs to be called before makeTies
        # note that this functionality is also placed in Part
        if not returnStream.streamStatus.accidentals:
            makeNotation.makeAccidentalsInMeasureStream(
                returnStream,
                pitchPast=pitchPast,
                pitchPastMeasure=pitchPastMeasure,
                useKeySignature=useKeySignature,
                alteredPitches=alteredPitches,
                cautionaryPitchClass=cautionaryPitchClass,
                cautionaryAll=cautionaryAll,
                overrideStatus=overrideStatus,
                cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                tiePitchSet=tiePitchSet)

        makeNotation.makeTies(returnStream, meterStream=meterStream, inPlace=True)

        for m in returnStream.getElementsByClass(Measure):
            makeNotation.splitElementsToCompleteTuplets(m, recurse=True, addTies=True)
            makeNotation.consolidateCompletedTuplets(m, recurse=True, onlyIfTied=True)

        if not returnStream.streamStatus.beams:
            try:
                makeNotation.makeBeams(returnStream, inPlace=True)
            except meter.MeterException as me:
                warnings.warn(str(me))

        # note: this needs to be after makeBeams, as placing this before
        # makeBeams was causing the duration's tuplet to lose its type setting
        # check for tuplet brackets one measure at a time
        # this means that they will never extend beyond one measure
        for m in returnStream.getElementsByClass(Measure):
            if not m.streamStatus.tuplets:
                makeNotation.makeTupletBrackets(m, inPlace=True)

        if not inPlace:
            return returnStream

    def extendDuration(self, objClass, *, inPlace=False):
        '''
        Given a Stream and an object class name, go through the Stream
        and find each instance of the desired object. The time between
        adjacent objects is then assigned to the duration of each object.
        The last duration of the last object is assigned to extend to the
        end of the Stream.

        If `inPlace` is True, this is done in-place; if `inPlace` is
        False, this returns a modified deep copy.

        >>> stream1 = stream.Stream()
        >>> n = note.Note(type='quarter')
        >>> n.duration.quarterLength
        1.0
        >>> stream1.repeatInsert(n, [0, 10, 20, 30, 40])

        >>> dyn = dynamics.Dynamic('ff')
        >>> stream1.insert(15, dyn)
        >>> stream1[-1].offset  # offset of last element
        40.0
        >>> stream1.duration.quarterLength  # total duration
        41.0
        >>> len(stream1)
        6

        >>> stream2 = stream1.flatten().extendDuration(note.GeneralNote, inPlace=False)
        >>> len(stream2)
        6
        >>> stream2[0].duration.quarterLength
        10.0

        The Dynamic does not affect the second note:

        >>> stream2[1].offset
        10.0
        >>> stream2[1].duration.quarterLength
        10.0

        >>> stream2[-1].duration.quarterLength  # or extend to end of stream
        1.0
        >>> stream2.duration.quarterLength
        41.0
        >>> stream2[-1].offset
        40.0
        '''

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('extendDuration')
        else:
            returnObj = self

        qLenTotal = returnObj.duration.quarterLength
        elements = list(returnObj.getElementsByClass(objClass))

        for i in range(len(elements) - 1):
            span = returnObj.elementOffset(elements[i + 1]) - returnObj.elementOffset(elements[i])
            elements[i].duration.quarterLength = span

        # handle last element
        if elements:
            elements[-1].duration.quarterLength = (qLenTotal
                                                   - returnObj.elementOffset(elements[-1]))
        if not inPlace:
            return returnObj

    @overload
    def stripTies(
        self: StreamType,
        *,
        inPlace: t.Literal[True],
        matchByPitch: bool = True,
    ) -> None:
        return None

    @overload
    def stripTies(
        self: StreamType,
        *,
        inPlace: t.Literal[False] = False,
        matchByPitch: bool = True,
    ) -> StreamType:
        return self

    def stripTies(
        self: StreamType,
        *,
        inPlace: bool = False,
        matchByPitch: bool = True,
    ) -> StreamType | None:
        # noinspection PyShadowingNames
        '''
        Find all notes that are tied; remove all tied notes,
        then make the first of the tied notes have a duration
        equal to that of all tied constituents. Lastly,
        remove the formerly-tied notes.

        This method can be used on Stream and Stream subclasses.
        When used on a stream containing Part-like substreams, as with many scores,
        :class:`~music21.stream.Part`, :class:`~music21.stream.Measure`, and other
        Stream subclasses are retained.

        `inPlace` controls whether the input stream is modified or whether a deep copy
        is made. (New in v7, to conform to the rest of music21, `inPlace=True` returns `None`.)

        Presently, this only works if tied notes are sequential in the same voice; ultimately
        this will need to look at .to and .from attributes (if they exist)

        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 6
        >>> a.append(n)
        >>> m = a.makeMeasures()
        >>> m.makeTies(inPlace=True)
        >>> len(m.flatten().notes)
        2

        >>> m = m.stripTies()
        >>> len(m.flatten().notes)
        1

        In cases where notes are manipulated after initial tie creation,
        some chord members might lack ties. This will not prevent merging the tied notes
        if all the pitches match, and `matchByPitch=True` (default):

        >>> c1 = chord.Chord('C4 E4')
        >>> c1.tie = tie.Tie('start')

        >>> c2 = chord.Chord('C4 E4')
        >>> c2.tie = tie.Tie('stop')

        >>> m = stream.Measure()
        >>> m.append([c1, c2])

        >>> c1.add(note.Note('G4'))
        >>> c2.add(note.Note('G4'))

        >>> c2.notes[-1].tie is None
        True

        >>> strippedPitchMatching = m.stripTies()
        >>> len(strippedPitchMatching.flatten().notes)
        1

        This can be prevented with `matchByPitch=False`, in which case every note,
        including each chord member, must have "stop" and/or "continue" tie types,
        which was not the case above:

        >>> strippedMixedTieTypes = m.stripTies(matchByPitch=False)
        >>> len(strippedMixedTieTypes.flatten().notes)
        2

        >>> c2.notes[0].tie = tie.Tie('stop')
        >>> c2.notes[1].tie = tie.Tie('stop')
        >>> c2.notes[2].tie = tie.Tie('stop')
        >>> strippedUniformTieTypes = m.stripTies(matchByPitch=False)
        >>> len(strippedUniformTieTypes.flatten().notes)
        1

        Notice the matching happens even after altering the pitches:

        >>> c3 = c2.transpose(6)
        >>> otherM = stream.Measure([c1, c3])
        >>> strippedTransposed = otherM.stripTies(matchByPitch=False)
        >>> len(strippedTransposed.flatten().notes)
        1

        When `matchByPitch` is True (as it is by default) the following
        behavior defined regarding chords with a tie type "continue":

        >>> c1.notes[0].tie = tie.Tie('continue')
        >>> c1.notes[1].tie = tie.Tie('start')
        >>> c1.notes[2].tie = tie.Tie('start')

        Continue is accepted here as an ersatz-start:

        >>> stripped1 = m.stripTies(matchByPitch=True)
        >>> len(stripped1.flatten().notes)
        1

        But prepend an element so that it's considered as a tie continuation:

        >>> c0 = chord.Chord('C4 E4 G4')
        >>> c0.tie = tie.Tie('start')
        >>> m2 = stream.Measure()
        >>> m2.append([c0, c1, c2])

        Now the mixed tie types on c1 will only be connected to c2
        on the permissive option (`matchByPitch=True`):

        >>> stripped2 = m2.stripTies(matchByPitch=True)
        >>> stripped2.elements
        (<music21.chord.Chord C4 E4 G4>,)

        >>> stripped3 = m2.stripTies(matchByPitch=False)
        >>> stripped3.elements
        (<music21.chord.Chord C4 E4 G4>,
         <music21.chord.Chord C4 E4 G4>,
         <music21.chord.Chord C4 E4 G4>)

        Now correct the tie types on c1 and try the strict option:

        >>> c1.notes[0].tie = tie.Tie('continue')
        >>> c1.notes[1].tie = tie.Tie('continue')
        >>> c1.notes[2].tie = tie.Tie('continue')
        >>> stripped4 = m2.stripTies(matchByPitch=False)
        >>> stripped4.elements
        (<music21.chord.Chord C4 E4 G4>,)

        Now replace the first element with just a single C4 note.
        The following chords will be merged with each other, but not with the single
        note, even on `matchByPitch=False`.
        (`matchByPitch=False` is permissive about pitch but strict about cardinality.)

        >>> newC = note.Note('C4')
        >>> newC.tie = tie.Tie('start')
        >>> m2.replace(c0, newC)
        >>> stripped5 = m2.stripTies(matchByPitch=False)
        >>> stripped5.elements
        (<music21.note.Note C>, <music21.chord.Chord C4 E4 G4>)

        * Changed in v7: `matchByPitch` defaults True
        '''
        # environLocal.printDebug(['calling stripTies'])
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('stripTies')
        else:
            returnObj = self

        # Clear existing beaming because notes may be deleted at any level of hierarchy
        returnObj.streamStatus.beams = False

        if returnObj.hasPartLikeStreams():
            # part-like does not necessarily mean that the next level down is a stream.Part
            # object or that this is a stream.Score object, so do not substitute
            # returnObj.parts for this...
            for p in returnObj.getElementsByClass(Stream):
                # already copied if necessary; edit in place
                p.stripTies(inPlace=True, matchByPitch=matchByPitch)
            if not inPlace:
                return returnObj
            else:
                return None

        if returnObj.hasVoices():
            for v in returnObj.voices:
                # already copied if necessary; edit in place
                v.stripTies(inPlace=True, matchByPitch=matchByPitch)
            if not inPlace:
                return returnObj
            else:
                return None

        # need to just get .notesAndRests with a nonzero duration,
        # as there may be other objects in the Measure
        # that come before the first Note, such as a SystemLayout object
        # or there could be ChordSymbols with zero (unrealized) durations
        f = returnObj.flatten()
        notes_and_rests: StreamType = f.notesAndRests.addFilter(
            lambda el, _iterator: el.quarterLength > 0
        ).stream()

        posConnected = []  # temporary storage for index of tied notes
        posDelete = []  # store deletions to be processed later

        def updateEndMatch(nInner) -> bool:
            '''
            updateEndMatch based on nList, iLast, matchByPitch, etc.
            '''
            # 2 cases before matchByPitch=False returns early.

            # Case 1: nInner is not a chord, and it has a stop tie
            # can't trust chords, which only tell if SOME member has a tie
            # matchByPitch does not matter here
            # https://github.com/cuthbertLab/music21/issues/502
            if (hasattr(nInner, 'tie')
                    and not isinstance(nInner, chord.Chord)
                    and nInner.tie is not None
                    and nInner.tie.type == 'stop'):
                return True
            # Case 2: matchByPitch=False and all chord members have a stop tie
            # and checking cardinality passes (don't match chords to single notes)
            if (not matchByPitch
                    and isinstance(nInner, chord.Chord)
                    and isinstance(nLast, chord.Chord)
                    and None not in [inner_p.tie for inner_p in nInner.notes]
                    and {inner_p.tie.type for inner_p in nInner.notes} == {'stop'}  # type: ignore
                    and len(nLast.pitches) == len(nInner.pitches)):
                return True

            # Now, matchByPitch
            # if we cannot find a stop tie, see if last note was connected
            # and this and the last note are the same pitch; this assumes
            # that connected and same pitch value is tied; this is not
            # frequently the case
            elif not matchByPitch:
                return False

            # find out if the last index is in position connected
            # if the pitches are the same for each note
            if (nLast is not None
                    and iLast in posConnected
                    and hasattr(nLast, 'pitch')
                    and hasattr(nInner, 'pitch')
                    # before doing pitch comparison, need to
                    # make sure we're not comparing a Note to a Chord
                    and not isinstance(nLast, chord.Chord)
                    and not isinstance(nInner, chord.Chord)
                    and nLast.pitch == nInner.pitch):
                return True
            # looking for two chords of equal size
            if (nLast is not None
                    and not isinstance(nInner, note.Note)
                    and iLast in posConnected
                    and hasattr(nLast, 'pitches')
                    and hasattr(nInner, 'pitches')):
                if len(nLast.pitches) != len(nInner.pitches):
                    return False

                for pitchIndex in range(len(nLast.pitches)):
                    # check to see that each is the same pitch, but
                    # allow for `accidental is None` == `Accidental('natural')`
                    pLast = nLast.pitches[pitchIndex]
                    pInner = nInner.pitches[pitchIndex]
                    if pLast.step != pInner.step or not pLast.isEnharmonic(pInner):
                        return False
                return True

            return False

        def allTiesAreContinue(nr: note.NotRest) -> bool:
            if nr.tie is None:  # pragma: no cover
                return False
            if nr.tie.type != 'continue':
                return False
            # check every chord member, since tie type "continue" on a chord
            # only indicates that SOME member is tie-continue.
            if isinstance(nr, chord.Chord):
                for innerN in nr.notes:
                    if innerN.tie is None:
                        return False
                    if innerN.tie.type != 'continue':
                        return False
            return True

        for i in range(len(notes_and_rests)):
            endMatch = None  # can be True, False, or None
            n = notes_and_rests[i]
            if i > 0:  # get i and n for the previous value
                iLast = i - 1
                nLast = notes_and_rests[iLast]
            else:
                iLast = None
                nLast = None

            # See if we have a tie, and it has started.
            # A start typed tie may not be a true start tie
            if (hasattr(n, 'tie')
                    and n.tie is not None
                    and n.tie.type == 'start'):
                # find a true start, add to known connected positions
                if iLast is None or iLast not in posConnected:
                    posConnected = [i]  # reset list with start
                # find a continuation: the last note was a tie
                # start and this note is a tie start (this may happen)
                elif iLast in posConnected:
                    posConnected.append(i)
                # a connection has been started or continued, so no endMatch
                endMatch = False

            # A "continue" may or may not imply a connection
            elif (hasattr(n, 'tie')
                    and n.tie is not None
                    and n.tie.type == 'continue'):
                # is this actually a start?
                if not posConnected:
                    posConnected.append(i)
                    endMatch = False
                elif matchByPitch:
                    # try to match pitch against nLast
                    # updateEndMatch() checks for equal cardinality
                    tempEndMatch = updateEndMatch(n)
                    if tempEndMatch:
                        posConnected.append(i)
                        # ... and keep going.
                        endMatch = False
                    else:
                        # clear list and populate with this element
                        posConnected = [i]
                        endMatch = False
                elif allTiesAreContinue(n):
                    # uniform-continue suffices if not matchByPitch
                    # but still need to check cardinality
                    if isinstance(nLast, note.NotRest) and (len(nLast.pitches) != len(n.pitches)):
                        # different sizes: clear list and populate with this element
                        # since allTiesAreContinue, it is okay to treat as ersatz-start
                        posConnected = [i]
                    else:
                        posConnected.append(i)
                    # either way, this was not a stop
                    endMatch = False
                else:
                    # only SOME ties on this chord are "continue": reject
                    posConnected = []
                    endMatch = False

            # establish end condition
            if endMatch is None:  # not yet set, not a start or continue
                endMatch = updateEndMatch(n)

            # process end condition
            if endMatch:
                posConnected.append(i)  # add this last position
                if len(posConnected) < 2:
                    # an open tie, not connected to anything
                    # should be an error; presently, just skipping
                    # raise StreamException('cannot consolidate ties when only one tie is present',
                    #    notes[posConnected[0]])
                    # environLocal.printDebug(
                    #   ['cannot consolidate ties when only one tie is present',
                    #     notes[posConnected[0]]])
                    posConnected = []
                    continue

                # get sum of durations for all notes
                # do not include first; will add to later; do not delete
                durSum = 0
                for q in posConnected[1:]:  # all but the first
                    durSum += notes_and_rests[q].quarterLength
                    posDelete.append(q)  # store for deleting later
                # dur sum should always be greater than zero
                if durSum == 0:
                    raise StreamException('aggregated ties have a zero duration sum')
                # change the duration of the first note to be self + sum
                # of all others
                changing_note = t.cast(note.GeneralNote, notes_and_rests[posConnected[0]])

                qLen = changing_note.quarterLength
                if not changing_note.duration.linked:
                    # obscure bug found from some inexact musicxml files.
                    changing_note.duration.linked = True
                changing_note.quarterLength = opFrac(qLen + durSum)

                # set tie to None on first note
                changing_note.tie = None

                # let the site know that we've changed duration.
                changing_note.informSites()

                # replace removed elements in spanners
                for sp in f.spanners:
                    for index in posConnected[1:]:
                        if notes_and_rests[index] in sp:
                            sp.replaceSpannedElement(
                                notes_and_rests[index],
                                changing_note
                            )

                posConnected = []  # reset to empty

        # all results have been processed
        posDelete.reverse()  # start from highest and go down

        for i in posDelete:
            # environLocal.printDebug(['removing note', notes[i]])
            # get the obj ref
            nTarget = notes_and_rests[i]
            # Recurse rather than depend on the containers being Measures
            # https://github.com/cuthbertLab/music21/issues/266
            returnObj.remove(nTarget, recurse=True)

        if not inPlace:
            return returnObj

    def extendTies(self, ignoreRests=False, pitchAttr='nameWithOctave'):
        '''
        Connect any adjacent pitch space values that are the
        same with a Tie. Adjacent pitches can be Chords, Notes, or Voices.

        If `ignoreRests` is True, rests that occur between events will not be
        considered in matching pitches.

        The `pitchAttr` determines the pitch attribute that is
        used for comparison. Any valid pitch attribute name can be used.
        '''
        def _getNextElements(srcStream, currentIndex, targetOffset):
            # need to find next event that start at the appropriate offset
            if currentIndex == len(srcStream) - 1:  # assume flat
                # environLocal.printDebug(['_getNextElements: nothing to process',
                # currentIndex, len(srcStream.notes) ])
                return []  # nothing left
            # iterate over all possible elements
            if ignoreRests:
                # need to find the offset of the first thing that is not rest
                for j in range(currentIndex + 1, len(srcStream._elements)):
                    el = srcStream._elements[j]
                    if isinstance(el, note.NotRest):
                        # change target offset to this position
                        targetOffset = srcStream._elements[j].getOffsetBySite(
                            srcStream)
                        break
            match = srcStream.getElementsByOffset(targetOffset)
            # filter matched elements
            post = []
            for matchEl in match:
                if isinstance(matchEl, note.NotRest):
                    post.append(matchEl)
            return post

        # take all flat elements; this will remove all voices; just use offset
        # position
        # do not need to worry about ._endElements
        srcFlat = self.flatten().notes.stream()
        for i, e in enumerate(srcFlat):
            pSrc = []
            if isinstance(e, note.Note):
                pSrc = [e]
            elif isinstance(e, chord.Chord):
                pSrc = list(e)  # get components
            else:
                continue
            # environLocal.printDebug(['examining', i, e])
            connections = _getNextElements(srcFlat, i,
                                           e.getOffsetBySite(srcFlat) + e.duration.quarterLength)
            # environLocal.printDebug(['possible connections', connections])

            for p, m in itertools.product(pSrc, connections):
                # for each p, see if there is match in the next position
                # for each element, look for a pitch to match
                mSrc = []
                if isinstance(m, note.Note):
                    mSrc = [m]
                elif isinstance(m, chord.Chord):
                    mSrc = list(m)  # get components
                # final note comparison
                for q in mSrc:
                    if getattr(q.pitch, pitchAttr) == getattr(p.pitch, pitchAttr):
                        # create a tie from p to q
                        if p.tie is None:
                            p.tie = tie.Tie('start')
                        elif p.tie.type == 'stop':
                            p.tie.type = 'continue'
                        # if dst tie exists, assume it connects
                        q.tie = tie.Tie('stop')
                        break  # can only have one match from p to q

    # --------------------------------------------------------------------------

    def sort(self, force=False):
        '''
        Sort this Stream in place by offset, then priority, then
        standard class sort order (e.g., Clefs before KeySignatures before
        TimeSignatures).

        Note that Streams automatically sort themselves unless
        autoSort is set to False (as in the example below)

        If `force` is True, a sort will be attempted regardless of any other parameters.


        >>> n1 = note.Note('A')
        >>> n2 = note.Note('B')
        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.insert(100, n2)
        >>> s.insert(0, n1)  # now a has a lower offset by higher index
        >>> [n.name for n in s]
        ['B', 'A']
        >>> s[0].name
        'B'
        >>> s.sort()
        >>> s[0].name
        'A'
        >>> [n.name for n in s]
        ['A', 'B']
        '''
        # trust if this is sorted: do not sort again
        # experimental
        if (not self.isSorted and self._mutable) or force:
            self._elements.sort(key=lambda x: x.sortTuple(self))
            self._endElements.sort(key=lambda x: x.sortTuple(self))

            # as sorting changes order, elements have changed;
            # need to clear cache, but flat status is the same
            self.coreElementsChanged(
                updateIsFlat=False,
                clearIsSorted=False,
                keepIndex=False,  # this is False by default, but just to be sure for later
            )
            self.isSorted = True
            # environLocal.printDebug(['_elements', self._elements])

    def sorted(self):
        # noinspection PyShadowingNames
        '''
        (TL;DR: you probably do not need to call this method unless you have turned `.autoSort` to
        off.)

        Returns a new Stream where all the elements are sorted according to offset time, then
        priority, then classSortOrder (so that, for instance, a Clef at offset 0 appears before
        a Note at offset 0).

        If this Stream is not flat, then only the elements directly in the stream itself are sorted.
        To sort all, run myStream.flatten().sorted().

        For instance, here is an unsorted Stream:

        >>> s = stream.Stream()
        >>> s.autoSort = False  # if True, sorting is automatic
        >>> s.insert(1, note.Note('D'))
        >>> s.insert(0, note.Note('C'))
        >>> s.show('text')
        {1.0} <music21.note.Note D>
        {0.0} <music21.note.Note C>


        But a sorted version of the Stream puts the C first:

        >>> s.sorted().show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>

        While the original stream remains unsorted:

        >>> s.show('text')
        {1.0} <music21.note.Note D>
        {0.0} <music21.note.Note C>


        OMIT_FROM_DOCS

        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.repeatInsert(note.Note('C#'), [0, 2, 4])
        >>> s.repeatInsert(note.Note('D-'), [1, 3, 5])
        >>> s.isSorted
        False
        >>> g = ''
        >>> for myElement in s:
        ...    g += '%s: %s; ' % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; '
        >>> y = s.sorted()
        >>> y.isSorted
        True
        >>> g = ''
        >>> for myElement in y:
        ...    g += '%s: %s; ' % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; '
        >>> farRight = note.Note('E')
        >>> farRight.priority = 5
        >>> farRight.offset = 2.0
        >>> y.insert(farRight)
        >>> g = ''
        >>> for myElement in y:
        ...    g += '%s: %s; ' % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; '
        >>> z = y.sorted()
        >>> g = ''
        >>> for myElement in z:
        ...    g += '%s: %s; ' % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; '
        >>> z[2].name, z[3].name
        ('C#', 'E')

        * Changed in v7: made into a method, not a property.
        '''
        cache_sorted = self._cache.get('sorted')
        if cache_sorted is not None:
            return cache_sorted
        shallowElements = copy.copy(self._elements)  # already a copy
        shallowEndElements = copy.copy(self._endElements)  # already a copy
        s = copy.copy(self)
        # assign directly to _elements, as we do not need to call
        # coreElementsChanged()
        s._elements = shallowElements
        s._endElements = shallowEndElements

        for e in shallowElements + shallowEndElements:
            s.coreSetElementOffset(e, self.elementOffset(e), addElement=True)
            e.sites.add(s)
            # need to explicitly set activeSite
            s.coreSelfActiveSite(e)
        # now just sort this stream in place; this will update the
        # isSorted attribute and sort only if not already sorted
        s.sort()
        self._cache['sorted'] = s
        return s

    def flatten(self: StreamType, retainContainers=False) -> StreamType:
        '''
        A very important method that returns a new Stream
        that has all sub-containers "flattened" within it,
        that is, it returns a new Stream where no elements nest within
        other elements.

        Here is a simple example of the usefulness of .flatten().  We
        will create a Score with two Parts in it, each with two Notes:

        >>> sc = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.id = 'part1'
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> p1.append(n1)
        >>> p1.append(n2)

        >>> p2 = stream.Part()
        >>> p2.id = 'part2'
        >>> n3 = note.Note('E4')
        >>> n4 = note.Note('F4')
        >>> p2.append(n3)
        >>> p2.append(n4)

        >>> sc.insert(0, p1)
        >>> sc.insert(0, p2)

        When we look at sc, we will see only the two parts:

        >>> sc.elements
        (<music21.stream.Part part1>, <music21.stream.Part part2>)

        We can get at the notes by using the indices of the
        stream to get the parts and then looking at the .elements
        there:

        >>> sc[0].elements
        (<music21.note.Note C>, <music21.note.Note D>)

        >>> sc.getElementById('part2').elements
        (<music21.note.Note E>, <music21.note.Note F>)

        ...but if we want to get all the notes, storing their
        offsets related to the beginning of the containing stream,
        one way
        is via calling .flatten() on sc and looking at the elements
        there:

        >>> sc.flatten().elements
        (<music21.note.Note C>, <music21.note.Note E>,
         <music21.note.Note D>, <music21.note.Note F>)

        Flattening a stream is a great way to get at all the notes in
        a larger piece.  For instance if we load a four-part
        Bach chorale into music21 from the integrated corpus, it
        will appear at first that there are no notes in the piece:

        >>> bwv66 = corpus.parse('bach/bwv66.6')
        >>> len(bwv66.notes)
        0

        This is because all the notes in the piece lie within :class:`music21.stream.Measure`
        objects and those measures lie within :class:`music21.stream.Part`
        objects.  It'd be a pain to navigate all the way through all those
        objects just to count notes.  Fortunately we can get a Stream of
        all the notes in the piece with .flatten().notes and then use the
        length of that Stream to count notes:

        >>> bwv66flat = bwv66.flatten()
        >>> len(bwv66flat.notes)
        165

        When, as is commonly the case, we want to find all the notes,
        but do not care to have offsets related to the origin of the stream,
        then `.recurse()` is a more efficient way of working:

        >>> len(bwv66.recurse().notes)
        165

        If `retainContainers=True` then a "semiFlat" version of the stream
        is returned where Streams are also included in the output stream.

        In general, you will not need to use this because `.recurse()` is
        more efficient and does not lead to problems of the same
        object appearing in the hierarchy more than once.

        >>> n1 = note.Note('C5')
        >>> m1 = stream.Measure([n1], number='1a')
        >>> p1 = stream.Part([m1])
        >>> p1.id = 'part1'

        >>> n2 = note.Note('D5')
        >>> m2 = stream.Measure([n2], number='1b')
        >>> p2 = stream.Part([m2])
        >>> p2.id = 'part2'

        >>> sc = stream.Score([p1, p2])

        `sf` will be the "semi-flattened" version of the score.

        >>> sf = sc.flatten(retainContainers=True)
        >>> sf.elements
        (<music21.stream.Part part1>,
         <music21.stream.Measure 1a offset=0.0>,
         <music21.stream.Part part2>,
         <music21.stream.Measure 1b offset=0.0>,
         <music21.note.Note C>,
         <music21.note.Note D>)
        >>> sf[0]
        <music21.stream.Part part1>

        Notice that these all return the same object:

        >>> sf[0][0][0]
        <music21.note.Note C>
        >>> sf[1][0]
        <music21.note.Note C>
        >>> sf[4]
        <music21.note.Note C>

        Unless it is important to get iterate in order from
        front of score to back of the score, you are generally better off using recurse
        instead of `.flatten(retainContainers=True)`, with `.getOffsetInHierarchy()`
        to figure out where in the score each element lies.

        For instance, this is how we can iterate using recurse():

        >>> for el in sc.recurse():
        ...     print(el)
        <music21.stream.Part part1>
        <music21.stream.Measure 1a offset=0.0>
        <music21.note.Note C>
        <music21.stream.Part part2>
        <music21.stream.Measure 1b offset=0.0>
        <music21.note.Note D>

        If you look back to our simple example of four notes above,
        you can see that the E (the first note in part2) comes before the D
        (the second note of part1).  This is because the flat stream
        is automatically sorted like all streams are by default.  The
        next example shows how to change this behavior.

        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.repeatInsert(note.Note('C#'), [0, 2, 4])
        >>> s.repeatInsert(note.Note('D-'), [1, 3, 5])
        >>> s.isSorted
        False

        >>> g = ''
        >>> for myElement in s:
        ...    g += '%s: %s; ' % (myElement.offset, myElement.name)
        ...

        >>> g
        '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; '

        >>> y = s.sorted()
        >>> y.isSorted
        True

        >>> g = ''
        >>> for myElement in y:
        ...    g += '%s: %s; ' % (myElement.offset, myElement.name)
        ...

        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; '

        >>> q = stream.Stream()
        >>> for i in range(5):
        ...     p = stream.Stream()
        ...     p.repeatInsert(base.Music21Object(), [0, 1, 2, 3, 4])
        ...     q.insert(i * 10, p)
        ...

        >>> len(q)
        5

        >>> qf = q.flatten()
        >>> len(qf)
        25
        >>> qf[24].offset
        44.0

        Note that combining `.flatten(retainContainers=True)` with pure `.flatten()`
        can lead to unstable Streams where the same object appears more than once,
        in violation of a `music21` lookup rule.

        >>> sc.flatten(retainContainers=True).flatten().elements
        (<music21.note.Note C>,
         <music21.note.Note C>,
         <music21.note.Note C>,
         <music21.note.Note D>,
         <music21.note.Note D>,
         <music21.note.Note D>)

        OMIT_FROM_DOCS

        >>> r = stream.Stream()
        >>> for j in range(5):
        ...   q = stream.Stream()
        ...   for i in range(5):
        ...      p = stream.Stream()
        ...      p.repeatInsert(base.Music21Object(), [0, 1, 2, 3, 4])
        ...      q.insert(i * 10, p)
        ...   r.insert(j * 100, q)

        >>> len(r)
        5

        >>> len(r.flatten())
        125

        >>> r.flatten()[124].offset
        444.0
        '''
        # environLocal.printDebug(['flatten(): self', self,
        #  'self.activeSite', self.activeSite])
        if retainContainers:
            method = 'semiFlat'
        else:
            method = 'flat'

        cached_version = self._cache.get(method)
        if cached_version is not None:
            return cached_version

        # this copy will have a shared sites object
        # note that copy.copy() in some cases seems to not cause secondary
        # problems that self.__class__() does
        sNew = copy.copy(self)

        if sNew.id != id(sNew):
            sOldId = sNew.id
            if isinstance(sOldId, int) and sOldId > defaults.minIdNumberToConsiderMemoryLocation:
                sOldId = hex(sOldId)

            newId = str(sOldId) + '_' + method
            sNew.id = newId

        sNew._derivation = derivation.Derivation(sNew)
        sNew._derivation.origin = self
        sNew.derivation.method = method
        # storing .elements in here necessitates
        # create a new, independent cache instance in the flat representation
        sNew._cache = {}
        sNew._offsetDict = {}
        sNew._elements = []
        sNew._endElements = []
        sNew.coreElementsChanged()

        ri: iterator.RecursiveIterator[M21ObjType] = iterator.RecursiveIterator(
            self,
            restoreActiveSites=False,
            includeSelf=False,
            ignoreSorting=True,
        )

        for e in ri:
            if e.isStream and not retainContainers:
                continue
            sNew.coreInsert(ri.currentHierarchyOffset(),
                             e,
                             setActiveSite=False)
        if not retainContainers:
            sNew.isFlat = True

        if self.autoSort is True:
            sNew.sort()  # sort it immediately so that cache is not invalidated
        else:
            sNew.coreElementsChanged()
        # here, we store the source stream from which this stream was derived
        self._cache[method] = sNew

        return sNew

    @property
    def flat(self):
        '''
        Deprecated: use `.flatten()` instead

        A property that returns the same flattened representation as `.flatten()`
        as of music21 v7.

        See :meth:`~music21.stream.base.Stream.flatten()` for documentation.
        '''
        flatStream = self.flatten(retainContainers=False)
        flatStream._created_via_deprecated_flat = True
        return flatStream

    @overload
    def recurse(self,
                *,
                streamsOnly: t.Literal[False] = False,
                restoreActiveSites=True,
                classFilter=(),
                includeSelf=None) -> iterator.RecursiveIterator[M21ObjType]:
        return t.cast(iterator.RecursiveIterator[M21ObjType], iterator.RecursiveIterator(self))

    @overload
    def recurse(self,
                *,
                streamsOnly: t.Literal[True],
                restoreActiveSites=True,
                classFilter=(),
                includeSelf=None) -> iterator.RecursiveIterator[Stream]:
        return t.cast(iterator.RecursiveIterator[Stream],
                      iterator.RecursiveIterator(self).getElementsByClass(Stream))

    def recurse(self,
                *,
                streamsOnly: bool = False,
                restoreActiveSites: bool = True,
                classFilter: tuple = (),
                includeSelf=None) -> t.Union[iterator.RecursiveIterator[M21ObjType],
                                             iterator.RecursiveIterator[Stream]]:
        '''
        `.recurse()` is a fundamental method of music21 for getting into
        elements contained in a Score, Part, or Measure, where elements such as
        notes are contained in sub-Stream elements.

        Returns an iterator that iterates over a list of Music21Objects
        contained in the Stream, starting with self's elements (unless
        includeSelf=True in which case, it starts with the element itself),
        and whenever finding a Stream subclass in self,
        that Stream subclass's elements.

        Here's an example. Let's create a simple score.

        >>> s = stream.Score(id='mainScore')
        >>> p0 = stream.Part(id='part0')
        >>> p1 = stream.Part(id='part1')

        >>> m01 = stream.Measure(number=1)
        >>> m01.append(note.Note('C', type='whole'))
        >>> m02 = stream.Measure(number=2)
        >>> m02.append(note.Note('D', type='whole'))
        >>> m11 = stream.Measure(number=1)
        >>> m11.append(note.Note('E', type='whole'))
        >>> m12 = stream.Measure(number=2)
        >>> m12.append(note.Note('F', type='whole'))

        >>> p0.append([m01, m02])
        >>> p1.append([m11, m12])

        >>> s.insert(0, p0)
        >>> s.insert(0, p1)
        >>> s.show('text')
        {0.0} <music21.stream.Part part0>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note C>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note D>
        {0.0} <music21.stream.Part part1>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note E>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note F>

        Now we could assign the `.recurse()` method to something,
        but that won't have much effect:

        >>> sRecurse = s.recurse()
        >>> sRecurse
        <music21.stream.iterator.RecursiveIterator for Score:mainScore @:0>

        So, that's not how we use `.recurse()`.  Instead, use it in a `for` loop:

        >>> for el in s.recurse():
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.stream.Part part0>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part0>)
        (<music21.note.Note C>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part0>)
        (<music21.note.Note D>, 0.0, <music21.stream.Measure 2 offset=4.0>)
        (<music21.stream.Part part1>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part1>)
        (<music21.note.Note E>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part1>)
        (<music21.note.Note F>, 0.0, <music21.stream.Measure 2 offset=4.0>)

        If we specify `includeSelf=True` then the original stream is also iterated:

        >>> for el in s.recurse(includeSelf=True):
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.stream.Score mainScore>, 0.0, None)
        (<music21.stream.Part part0>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part0>)
        (<music21.note.Note C>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        ...

        Notice that like calling `.show('text')`, the offsets are relative to their containers.

        Compare the difference between putting `.recurse().notes` and `.flatten().notes`:

        >>> for el in s.recurse().notes:
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.note.Note C>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.note.Note D>, 0.0, <music21.stream.Measure 2 offset=4.0>)
        (<music21.note.Note E>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.note.Note F>, 0.0, <music21.stream.Measure 2 offset=4.0>)

        >>> for el in s.flatten().notes:
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.note.Note C>, 0.0, <music21.stream.Score mainScore_flat>)
        (<music21.note.Note E>, 0.0, <music21.stream.Score mainScore_flat>)
        (<music21.note.Note D>, 4.0, <music21.stream.Score mainScore_flat>)
        (<music21.note.Note F>, 4.0, <music21.stream.Score mainScore_flat>)

        If you don't need correct offsets or activeSites, set `restoreActiveSites` to `False`.
        Then the last offset/activeSite will be used.  It's a bit of a speedup, but leads to some
        bad code, so use it only in highly optimized situations.

        We'll also test using multiple classes here... the Stream given is the same as the
        s.flatten().notes stream.

        >>> for el in s.recurse(classFilter=('Note', 'Rest'), restoreActiveSites=False):
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.note.Note C>, 0.0, <music21.stream.Score mainScore_flat>)
        (<music21.note.Note D>, 4.0, <music21.stream.Score mainScore_flat>)
        (<music21.note.Note E>, 0.0, <music21.stream.Score mainScore_flat>)
        (<music21.note.Note F>, 4.0, <music21.stream.Score mainScore_flat>)

        So, this is pretty unreliable so don't use it unless the tiny speedup is worth it.

        The other two attributes are pretty self-explanatory: `streamsOnly` will put only Streams
        in, while `includeSelf` will add the initial stream from recursion.  If the inclusion or
        exclusion of `self` is important to you, put it in explicitly.

        >>> for el in s.recurse(includeSelf=False, streamsOnly=True):
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.stream.Part part0>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part0>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part0>)
        (<music21.stream.Part part1>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part1>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part1>)

        .. warning::

            Remember that like all iterators, it is dangerous to alter
            the components of the Stream being iterated over during iteration.
            if you need to edit while recursing, list(s.recurse()) is safer.

        * Changed in v5.5: All attributes are keyword only.
        * Changed in v8: removed parameter `skipSelf`.  Use `includeSelf` instead.
        '''
        ri: iterator.RecursiveIterator[M21ObjType] = iterator.RecursiveIterator(
            self,
            streamsOnly=streamsOnly,
            restoreActiveSites=restoreActiveSites,
            includeSelf=includeSelf
        )
        if classFilter:
            ri = ri.getElementsByClass(classFilter)

        if t.TYPE_CHECKING and streamsOnly:
            return t.cast(iterator.RecursiveIterator[Stream], ri)
        return ri

    def containerInHierarchy(
        self,
        el: base.Music21Object,
        *,
        setActiveSite=True
    ) -> Stream | None:
        '''
        Returns the container in a hierarchy that this element belongs to.

        For instance, assume a Note (n) is in a Measure (m1) which is in a Part, in a Score (s1),
        and the Note is also in another hierarchy (say, a chordified version of a Score, s2).
        if s1.containerInHierarchy(n) is called, it will return m1,
        the Measure that contains the note.

        Unless `setActiveSite` is False, n's activeSite will be set to m1, and
        its `.offset` will be the offset in `m1`.

        >>> s1 = stream.Score(id='s1')
        >>> p1 = stream.Part()
        >>> m1 = stream.Measure(id='m1')
        >>> n = note.Note('D')
        >>> m1.append(n)
        >>> p1.append(m1)
        >>> s1.insert(0, p1)
        >>> s2 = stream.Stream(id='s2')
        >>> s2.append(n)
        >>> n.activeSite.id
        's2'
        >>> s1.containerInHierarchy(n).id
        'm1'
        >>> n.activeSite.id
        'm1'
        >>> n.activeSite = s2
        >>> s1.containerInHierarchy(n, setActiveSite=False).id
        'm1'
        >>> n.activeSite.id
        's2'

        If the element cannot be found in the hierarchy then None is returned.

        >>> s3 = stream.Stream()
        >>> s3.containerInHierarchy(n) is None
        True
        '''
        elSites = el.sites
        for s in self.recurse(includeSelf=True, streamsOnly=True, restoreActiveSites=False):
            if s in elSites:
                if setActiveSite:
                    s.coreSelfActiveSite(el)
                return s
        return None

    def makeImmutable(self):
        '''
        Clean this Stream: for self and all elements, purge all dead locations
        and remove all non-contained sites. Further, restore all active sites.
        '''
        if self._mutable is not False:
            self.sort()  # must sort before making immutable
        for e in self.recurse(streamsOnly=True, includeSelf=False):
            # e.purgeLocations(rescanIsDead=True)
            # NOTE: calling this method was having the side effect of removing
            # sites from locations when a Note was both in a Stream and in
            # an Interval
            if e.isStream:
                e.sort()  # sort before making immutable
                e._mutable = False
        self._mutable = False

    def makeMutable(self, recurse=True):
        self._mutable = True
        if recurse:
            for e in self.recurse(streamsOnly=True):
                # do not recurse, as will get all Stream
                e.makeMutable(recurse=False)
        self.coreElementsChanged()

    # --------------------------------------------------------------------------
    # duration and offset methods and properties

    @property
    def highestOffset(self):
        '''
        Get start time of element with the highest offset in the Stream.
        Note the difference between this property and highestTime
        which gets the end time of the highestOffset

        >>> stream1 = stream.Stream()
        >>> for offset in [0, 4, 8]:
        ...     n = note.Note('G#', type='whole')
        ...     stream1.insert(offset, n)
        >>> stream1.highestOffset
        8.0
        >>> stream1.highestTime
        12.0
        '''
        # TODO: Perfect timespans candidate
        if 'HighestOffset' in self._cache and self._cache['HighestOffset'] is not None:
            pass  # return cache unaltered
        elif not self._elements:
            self._cache['HighestOffset'] = 0.0
        elif self.isSorted is True:
            eLast = self._elements[-1]
            self._cache['HighestOffset'] = self.elementOffset(eLast)
        else:  # iterate through all elements
            highestOffsetSoFar = None
            for e in self._elements:
                candidateOffset = self.elementOffset(e)
                if highestOffsetSoFar is None or candidateOffset > highestOffsetSoFar:
                    highestOffsetSoFar = candidateOffset

            if highestOffsetSoFar is not None:
                self._cache['HighestOffset'] = float(highestOffsetSoFar)
            else:
                self._cache['HighestOffset'] = None
        return self._cache['HighestOffset']

    def _setHighestTime(self, value):
        '''
        For internal use only.
        '''
        self._cache['HighestTime'] = value

    @property
    def highestTime(self):
        '''
        Returns the maximum of all Element offsets plus their Duration
        in quarter lengths. This value usually represents the last
        "release" in the Stream.

        Stream.duration is normally equal to the highestTime
        expressed as a Duration object, but it can be set separately
        for advanced operations.

        Example: Insert a dotted half note at position 0 and see where
        it cuts off:

        >>> p1 = stream.Stream()
        >>> p1.highestTime
        0.0

        >>> n = note.Note('A-')
        >>> n.quarterLength = 3
        >>> p1.insert(0, n)
        >>> p1.highestTime
        3.0

        Now insert in the same stream, the dotted half note
        at positions 1, 2, 3, 4 and see when the final note cuts off:

        >>> p1.repeatInsert(n, [1, 2, 3, 4])
        >>> p1.highestTime
        7.0

        Another example.

        >>> n = note.Note('C#')
        >>> n.quarterLength = 3

        >>> q = stream.Stream()
        >>> for i in [20, 0, 10, 30, 40]:
        ...    p = stream.Stream()
        ...    p.repeatInsert(n, [0, 1, 2, 3, 4])
        ...    q.insert(i, p)  # insert out of order
        >>> len(q.flatten())
        25
        >>> q.highestTime  # this works b/c the component Stream has a duration
        47.0
        >>> r = q.flatten()

        * Changed in v6.5: highestTime can return a Fraction.

        OMIT_FROM_DOCS

        Make sure that the cache really is empty
        >>> 'HighestTime' in r._cache
        False
        >>> r.highestTime  # 44 + 3
        47.0

        Can highestTime be a fraction?

        >>> n = note.Note('D')
        >>> n.duration.quarterLength = 1/3
        >>> n.duration.quarterLength
        Fraction(1, 3)

        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> s.append(n)
        >>> s.highestTime
        Fraction(4, 3)
        '''
        # TODO(msc) -- why is cache 'HighestTime' and not 'highestTime'?
        # environLocal.printDebug(['_getHighestTime', 'isSorted', self.isSorted, self])

        # remove cache -- durations might change...
        if 'HighestTime' in self._cache and self._cache['HighestTime'] is not None:
            pass  # return cache unaltered
        elif not self._elements:
            # _endElements does not matter here, since ql > 0 on endElements not allowed.
            self._cache['HighestTime'] = 0.0
            return 0.0
        else:
            highestTimeSoFar = 0.0
            # TODO: optimize for a faster way of doing this.
            #     but cannot simply look at the last element even if isSorted
            #     because what if the penultimate
            #     element, with a
            #     lower offset has a longer duration than the last?
            #     Take the case where a whole note appears a 0.0, but a
            #     textExpression (ql=0) at 0.25 --
            #     isSorted would be true, but highestTime should be 4.0 not 0.25
            for e in self._elements:
                candidateOffset = (self.elementOffset(e)
                                   + e.duration.quarterLength)
                if candidateOffset > highestTimeSoFar:
                    highestTimeSoFar = candidateOffset
            self._cache['HighestTime'] = opFrac(highestTimeSoFar)
        return self._cache['HighestTime']

    @property
    def lowestOffset(self):
        '''
        Get the start time of the Element with the lowest offset in the Stream.

        >>> stream1 = stream.Stream()
        >>> for x in range(3, 5):
        ...     n = note.Note('G#')
        ...     stream1.insert(x, n)
        ...
        >>> stream1.lowestOffset
        3.0


        If the Stream is empty, then the lowest offset is 0.0:


        >>> stream2 = stream.Stream()
        >>> stream2.lowestOffset
        0.0



        >>> p = stream.Stream()
        >>> p.repeatInsert(note.Note('D5'), [0, 1, 2, 3, 4])
        >>> q = stream.Stream()
        >>> q.repeatInsert(p, list(range(0, 50, 10)))
        >>> len(q.flatten())
        25
        >>> q.lowestOffset
        0.0
        >>> r = stream.Stream()
        >>> r.repeatInsert(q, list(range(97, 500, 100)))
        >>> len(r.flatten())
        125
        >>> r.lowestOffset
        97.0
        '''
        if 'lowestOffset' in self._cache and self._cache['LowestOffset'] is not None:
            pass  # return cache unaltered
        elif not self._elements:
            self._cache['LowestOffset'] = 0.0
        elif self.isSorted is True:
            eFirst = self._elements[0]
            self._cache['LowestOffset'] = self.elementOffset(eFirst)
        else:  # iterate through all elements
            minOffsetSoFar = None
            for e in self._elements:
                candidateOffset = self.elementOffset(e)
                if minOffsetSoFar is None or candidateOffset < minOffsetSoFar:
                    minOffsetSoFar = candidateOffset
            self._cache['LowestOffset'] = minOffsetSoFar

            # environLocal.printDebug(['_getLowestOffset: iterated elements', min])

        return self._cache['LowestOffset']

    def _getDuration(self):
        '''
        Gets the duration of the whole stream (generally the highestTime, but can be set
        independently).
        '''
        if self._unlinkedDuration is not None:
            return self._unlinkedDuration
        elif 'Duration' in self._cache and self._cache['Duration'] is not None:
            # environLocal.printDebug(['returning cached duration'])
            return self._cache['Duration']
        else:
            # environLocal.printDebug(['creating new duration based on highest time'])
            self._cache['Duration'] = duration.Duration(quarterLength=self.highestTime)
            return self._cache['Duration']

    def _setDuration(self, durationObj):
        '''
        Set the total duration of the Stream independently of the highestTime
        of the stream.  Useful to define the scope of the stream as independent
        of its constituted elements.

        If set to None, then the default behavior of computing automatically from
        highestTime is reestablished.
        '''
        if isinstance(durationObj, duration.Duration):
            self._unlinkedDuration = durationObj
        elif durationObj is None:
            self._unlinkedDuration = None
        else:  # need to permit Duration object assignment here
            raise StreamException(f'this must be a Duration object, not {durationObj}')

    @property
    def duration(self) -> 'music21.duration.Duration':
        '''
        Returns the total duration of the Stream, from the beginning of the
        stream until the end of the final element.
        May be set independently by supplying a Duration object.

        >>> a = stream.Stream()
        >>> q = note.Note(type='quarter')
        >>> a.repeatInsert(q, [0, 1, 2, 3])
        >>> a.highestOffset
        3.0
        >>> a.highestTime
        4.0
        >>> a.duration
        <music21.duration.Duration 4.0>
        >>> a.duration.quarterLength
        4.0

        Advanced usage: override the duration from what is set:

        >>> newDuration = duration.Duration('half')
        >>> newDuration.quarterLength
        2.0

        >>> a.duration = newDuration
        >>> a.duration.quarterLength
        2.0

        Restore normal behavior by setting duration to None:

        >>> a.duration = None
        >>> a.duration
        <music21.duration.Duration 4.0>

        Note that the highestTime for the stream is the same
        whether duration is overridden or not:

        >>> a.highestTime
        4.0
        '''
        return self._getDuration()

    @duration.setter
    def duration(self, value: 'music21.duration.Duration'):
        self._setDuration(value)

    def _setSeconds(self, value):
        pass

    def _getSeconds(self):
        getTempoFromContext = False
        # need to find all tempo indications and the number of quarter lengths
        # under each
        tiStream = self.getElementsByClass(tempo.TempoIndication)
        offsetMetronomeMarkPairs = []

        if not tiStream:
            getTempoFromContext = True
        else:
            for ti in tiStream:
                o = self.elementOffset(ti)
                # get the desired metronome mark from any of ti classes
                mm = ti.getSoundingMetronomeMark()
                offsetMetronomeMarkPairs.append([o, mm])

        for i, (o, mm) in enumerate(offsetMetronomeMarkPairs):
            if i == 0 and o > 0.0:
                getTempoFromContext = True
            break  # just need first

        if getTempoFromContext:
            ti = self.getContextByClass('TempoIndication')
            if ti is None:
                if self.highestTime != 0.0:
                    return float('nan')
                else:
                    return 0.0
            # insert at zero offset position, even though coming from
            # outside this stream
            mm = ti.getSoundingMetronomeMark()
            offsetMetronomeMarkPairs = [[0.0, mm]] + offsetMetronomeMarkPairs
        sec = 0.0
        for i, (o, mm) in enumerate(offsetMetronomeMarkPairs):
            # handle only one mm right away
            if len(offsetMetronomeMarkPairs) == 1:
                sec += mm.durationToSeconds(self.highestTime)
                break
            oStart, mmStart = o, mm
            # if not the last ti, get the next by index to get the offset
            if i < len(offsetMetronomeMarkPairs) - 1:
                # cases of two or more remain
                oEnd, unused_mmEnd = offsetMetronomeMarkPairs[i + 1]
            else:  # at the last
                oEnd = self.highestTime
            sec += mmStart.durationToSeconds(oEnd - oStart)

        return sec

    seconds = property(_getSeconds, _setSeconds, doc='''
        Get or set the duration of this Stream in seconds, assuming that
        this object contains a :class:`~music21.tempo.MetronomeMark` or
        :class:`~music21.tempo.MetricModulation`.

        >>> s = corpus.parse('bwv66.6')  # piece without a tempo
        >>> sFlat = s.flatten()
        >>> t = tempo.MetronomeMark('adagio')
        >>> sFlat.insert(0, t)
        >>> sFlat.seconds
        38.57142857...
        >>> tFast = tempo.MetronomeMark('allegro')
        >>> sFlat.replace(t, tFast)
        >>> sFlat.seconds
        16.363...

        Setting seconds on streams is not supported.  Ideally it would instead
        scale all elements to fit, but this is a long way off.

        If a stream does not have a tempo-indication in it then the property
        returns 0.0 if an empty Stream (or self.highestTime is 0.0) or 'nan'
        if there are non-zero duration objects in the stream:

        >>> s = stream.Stream()
        >>> s.seconds
        0.0
        >>> s.insert(0, clef.TrebleClef())
        >>> s.seconds
        0.0
        >>> s.append(note.Note(type='half'))
        >>> s.seconds
        nan
        >>> import math
        >>> math.isnan(s.seconds)
        True

        * Changed in v6.3: return nan rather than raising an exception.  Do not
          attempt to change seconds on a stream, as it did not do what you would expect.
        ''')

    def metronomeMarkBoundaries(self, srcObj=None):
        '''
        Return a list of offset start, offset end,
        MetronomeMark triples for all TempoIndication objects found
        in this Stream or a Stream provided by srcObj.

        If no MetronomeMarks are found, or an initial region does not
        have a MetronomeMark, a mark of quarter equal to 120 is provided as default.

        Note that if other TempoIndication objects are defined,
        they will be converted to MetronomeMarks and returned here


        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 8)
        >>> s.insert([6, tempo.MetronomeMark(number=240)])
        >>> s.metronomeMarkBoundaries()
        [(0.0, 6.0, <music21.tempo.MetronomeMark animato Quarter=120>),
         (6.0, 8.0, <music21.tempo.MetronomeMark Quarter=240>)]
        '''
        if srcObj is None:
            srcObj = self
        # get all tempo indications from the flat Stream;
        # using flat here may not always be desirable
        # may want to do a recursive upward search as well
        srcFlat = srcObj.flatten()
        tiStream = srcFlat.getElementsByClass(tempo.TempoIndication)
        mmBoundaries = []  # a  list of (start, end, mm)

        # not sure if this should be taken from the flat representation
        highestTime = srcFlat.highestTime
        lowestOffset = srcFlat.lowestOffset

        # if no tempo
        if not tiStream:
            mmDefault = tempo.MetronomeMark(number=120)  # a default
            mmBoundaries.append((lowestOffset, highestTime, mmDefault))
        # if just one tempo
        elif len(tiStream) == 1:
            # get offset from flat source
            o = tiStream[0].getOffsetBySite(srcFlat)
            mm = tiStream[0].getSoundingMetronomeMark()
            if o > lowestOffset:
                mmDefault = tempo.MetronomeMark(number=120)  # a default
                mmBoundaries.append((lowestOffset, o, mmDefault))
                mmBoundaries.append((o, highestTime, mm))
            else:
                mmBoundaries.append((lowestOffset, highestTime, mm))
        # one or more tempi
        else:
            offsetPairs = []
            for ti in tiStream:
                o = ti.getOffsetBySite(srcFlat)
                offsetPairs.append([o, ti.getSoundingMetronomeMark()])
            # fill boundaries
            # if lowest region not defined, supply as default
            if offsetPairs[0][0] > lowestOffset:
                mmDefault = tempo.MetronomeMark(number=120)  # a default
                mmBoundaries.append((lowestOffset, offsetPairs[0][0],
                                     mmDefault))
                mmBoundaries.append((offsetPairs[0][0], offsetPairs[1][0],
                                     offsetPairs[0][1]))
            else:  # just add the first range
                mmBoundaries.append((offsetPairs[0][0], offsetPairs[1][0],
                                     offsetPairs[0][1]))
            # add any remaining ranges, starting from the second; if last,
            # use the highest time as the boundary
            for i, (o, mm) in enumerate(offsetPairs):
                if i == 0:
                    continue  # already added first
                elif i == len(offsetPairs) - 1:  # last index
                    mmBoundaries.append((offsetPairs[i][0], highestTime,
                                         offsetPairs[i][1]))
                else:  # add with next boundary
                    mmBoundaries.append((offsetPairs[i][0], offsetPairs[i + 1][0],
                                         offsetPairs[i][1]))

        # environLocal.printDebug(['self.metronomeMarkBoundaries()',
        # 'got mmBoundaries:', mmBoundaries])
        return mmBoundaries

    def _accumulatedSeconds(self, mmBoundaries, oStart, oEnd):
        '''
        Given MetronomeMark boundaries, for any pair of offsets,
        determine the realized duration in seconds.
        '''
        # assume tt mmBoundaries are in order
        totalSeconds = 0.0
        activeStart = oStart
        activeEnd = None
        for s, e, mm in mmBoundaries:
            if s <= activeStart < e:
                # find time in this region
                if oEnd < e:  # if end within this region
                    activeEnd = oEnd
                else:  # if end after this region
                    activeEnd = e
                # environLocal.printDebug(['activeStart', activeStart,
                # 'activeEnd', activeEnd, 's, e, mm', s, e, mm])
                totalSeconds += mm.durationToSeconds(activeEnd - activeStart)
            else:
                continue
            if activeEnd == oEnd:
                break
            else:  # continue on
                activeStart = activeEnd
        return totalSeconds

    def _getSecondsMap(self, srcObj=None):
        '''
        Return a list of dictionaries for all elements in this Stream,
        where each dictionary defines the real-time characteristics of
        the stored events. This will attempt to find
        all :class:`~music21.tempo.TempoIndication` subclasses and use these
        values to realize tempi. If no initial tempo is found,
        a tempo of 120 BPM will be provided.
        '''
        if srcObj is None:
            srcObj = self
        mmBoundaries = self.metronomeMarkBoundaries(srcObj=srcObj)

        # not sure if this should be taken from the flat representation
        lowestOffset = srcObj.lowestOffset

        secondsMap = []  # list of start, start+dur, element
        if srcObj.hasVoices():
            groups = []
            for i, v in enumerate(srcObj.voices):
                groups.append((v.flatten(), i))
        else:  # create a single collection
            groups = [(srcObj, None)]

        # get accumulated time over many possible tempo changes for
        # start/end offset
        for group, voiceIndex in groups:
            for e in group:
                if isinstance(e, bar.Barline):
                    continue
                dur = e.duration.quarterLength
                offset = round(e.getOffsetBySite(group), 8)
                # calculate all time regions given this offset

                # all stored values are seconds
                # noinspection PyDictCreation
                secondsDict = {}
                secondsDict['offsetSeconds'] = srcObj._accumulatedSeconds(
                    mmBoundaries, lowestOffset, offset)
                secondsDict['durationSeconds'] = srcObj._accumulatedSeconds(
                    mmBoundaries, offset, offset + dur)
                secondsDict['endTimeSeconds'] = (secondsDict['offsetSeconds']
                                                 + secondsDict['durationSeconds'])
                secondsDict['element'] = e
                secondsDict['voiceIndex'] = voiceIndex
                secondsMap.append(secondsDict)
        return secondsMap

    # do not make a property decorator since _getSecondsMap takes arguments
    secondsMap = property(_getSecondsMap, doc='''
        Returns a list where each element is a dictionary
        consisting of the 'offsetSeconds' in seconds of each element in a Stream,
        the 'duration' in seconds, the 'endTimeSeconds' in seconds (that is, the offset
        plus the duration), and the 'element' itself. Also contains a 'voiceIndex' entry which
        contains the voice number of the element, or None if there
        are no voices.


        >>> mm1 = tempo.MetronomeMark(number=120)
        >>> n1 = note.Note(type='quarter')
        >>> c1 = clef.AltoClef()
        >>> n2 = note.Note(type='half')
        >>> s1 = stream.Stream()
        >>> s1.append([mm1, n1, c1, n2])
        >>> om = s1.secondsMap
        >>> om[3]['offsetSeconds']
        0.5
        >>> om[3]['endTimeSeconds']
        1.5
        >>> om[3]['element'] is n2
        True
        >>> om[3]['voiceIndex']
    ''')

    # --------------------------------------------------------------------------
    # Metadata access

    def _getMetadata(self) -> metadata.Metadata | None:
        '''
        >>> a = stream.Stream()
        >>> a.metadata = metadata.Metadata()
        '''
        mdList = self.getElementsByClass(metadata.Metadata)
        # only return metadata that has an offset = 0.0
        mdList = mdList.getElementsByOffset(0)
        return mdList.first()

    def _setMetadata(self, metadataObj: metadata.Metadata | None) -> None:
        '''
        >>> a = stream.Stream()
        >>> a.metadata = metadata.Metadata()
        '''
        oldMetadata = self._getMetadata()
        if oldMetadata is not None:
            # environLocal.printDebug(['removing old metadata', oldMetadata])
            junk = self.pop(self.index(oldMetadata))

        if metadataObj is not None and isinstance(metadataObj, metadata.Metadata):
            self.insert(0, metadataObj)

    metadata = property(_getMetadata, _setMetadata,
                        doc='''
        Get or set the :class:`~music21.metadata.Metadata` object
        found at the beginning (offset 0) of this Stream.

        >>> s = stream.Stream()
        >>> s.metadata = metadata.Metadata()
        >>> s.metadata.composer = 'frank'
        >>> s.metadata.composer
        'frank'

        May also return None if nothing is there.
        ''')

    # --------------------------------------------------------------------------
    # these methods override the behavior inherited from base.py

    def _getMeasureOffset(self):
        # this normally returns the offset of this object in its container
        # for now, simply return the offset for the activeSite
        return self.getOffsetBySite(self.activeSite)

    @property
    def beat(self):
        '''
        beat returns None for a Stream.
        '''
        # this normally returns the beat within a measure; here, it could
        # be beats from the beginning?
        return None

    @property
    def beatStr(self):
        '''
        unlike other Music21Objects, streams always have beatStr (beat string) of None

        May change to '' soon.
        '''
        return None

    @property
    def beatDuration(self):
        '''
        unlike other Music21Objects, streams always have beatDuration of None
        '''
        # this returns the duration of the active beat
        return None

    @property
    def beatStrength(self):
        '''
        unlike other Music21Objects, streams always have beatStrength of None
        '''
        # this returns the accent weight of the active beat
        return None

    def beatAndMeasureFromOffset(self, searchOffset, fixZeros=True):
        '''
        Returns a two-element tuple of the beat and the Measure object (or the first one
        if there are several at the same offset; unlikely but possible) for a given
        offset from the start of this Stream (that contains measures).

        Recursively searches for measures.  Note that this method assumes that all parts
        have measures of consistent length.  If that's not the case, this
        method can be called on the relevant part.

        This algorithm should work even for weird time signatures such as 2+3+2/8.


        >>> bach = corpus.parse('bach/bwv1.6')
        >>> bach.parts[0].measure(2).getContextByClass(meter.TimeSignature)
        <music21.meter.TimeSignature 4/4>
        >>> returnTuples = []
        >>> for offset in [0.0, 1.0, 2.0, 5.0, 5.5]:
        ...     returnTuples.append(bach.beatAndMeasureFromOffset(offset))
        >>> returnTuples
        [(4.0, <music21.stream.Measure 0 offset=0.0>),
         (1.0, <music21.stream.Measure 1 offset=1.0>),
         (2.0, <music21.stream.Measure 1 offset=1.0>),
         (1.0, <music21.stream.Measure 2 offset=5.0>),
         (1.5, <music21.stream.Measure 2 offset=5.0>)]

        To get just the measureNumber and beat, use a transformation like this:
        >>> [(beat, measureObj.number) for beat, measureObj in returnTuples]
        [(4.0, 0), (1.0, 1), (2.0, 1), (1.0, 2), (1.5, 2)]

        Adapted from contributed code by Dmitri Tymoczko.  With thanks to DT.
        '''
        myStream = self
        if not myStream.hasMeasures():
            if myStream.hasPartLikeStreams():
                foundPart = False
                for subStream in myStream:
                    if not subStream.isStream:
                        continue
                    if subStream.hasMeasures():
                        foundPart = True
                        myStream = subStream
                        break
                if not foundPart:
                    raise StreamException('beatAndMeasureFromOffset: could not find any parts!')
                    # was return False
            else:
                if not myStream.hasMeasures():
                    raise StreamException('beatAndMeasureFromOffset: could not find any measures!')
                    # return False
        # Now we get the measure containing our offset.
        # In most cases this second part of the code does the job.
        myMeas = myStream.getElementAtOrBefore(searchOffset, classList=['Measure'])
        if myMeas is None:
            raise StreamException('beatAndMeasureFromOffset: no measure at that offset.')
        ts1 = myMeas.timeSignature
        if ts1 is None:
            ts1 = myMeas.getContextByClass(meter.TimeSignature)

        if ts1 is None:
            raise StreamException(
                'beatAndMeasureFromOffset: could not find a time signature for that place.')
        try:
            myBeat = ts1.getBeatProportion(searchOffset - myMeas.offset)
        except:
            raise StreamException(
                'beatAndMeasureFromOffset: offset is beyond the end of the piece')
        foundMeasureNumber = myMeas.number
        # deal with second half of partial measures...

        # Now we deal with the problem case, where we have the second half of a partial measure.
        # These are
        # treated as unnumbered measures (or measures with suffix 'X') by notation programs,
        # even though they are
        # logically part of the previous measure.
        # The variable padBeats will represent extra beats we add to the front
        # of our partial measure
        numSuffix = myMeas.numberSuffix
        if numSuffix == '':
            numSuffix = None

        if numSuffix is not None or (fixZeros and foundMeasureNumber == 0):
            prevMeas = myStream.getElementBeforeOffset(myMeas.offset, classList=['Measure'])
            if prevMeas:
                ts2 = prevMeas.getContextByClass(meter.TimeSignature)
                if not ts2:
                    raise StreamException(
                        'beatAndMeasureFromOffset: partial measure found, '
                        + 'but could not find a time signature for the preceding measure')
                # foundMeasureNumber = prevMeas.number

                # need this for chorales 197 and 280, where we
                # have a full-length measure followed by a pickup in
                # a new time signature
                if prevMeas.highestTime == ts2.barDuration.quarterLength:
                    padBeats = ts2.beatCount
                else:
                    padBeats = ts2.getBeatProportion(prevMeas.highestTime) - 1
                return (myBeat + padBeats, prevMeas)
            else:
                # partial measure at start of piece
                padBeats = ts1.getBeatProportion(
                    ts1.barDuration.quarterLength - myMeas.duration.quarterLength) - 1
                return (myBeat + padBeats, myMeas)
        else:
            return (myBeat, myMeas)

    # --------------------------------------------------------------------------
    # transformations

    def transpose(
        self,
        value: str | int | 'music21.interval.IntervalBase',
        /,
        *,
        inPlace=False,
        recurse=True,
        classFilterList=None
    ):
        # noinspection PyShadowingNames
        '''
        Transpose all specified classes in the
        Stream by the
        user-provided value. If the value is an integer, the
        transposition is treated in half steps. If the value is
        a string, any Interval string specification can be
        provided.

        returns a new Stream by default, but if the
        optional "inPlace" key is set to True then
        it modifies pitches in place.

        TODO: for generic interval set accidental by key signature.

        >>> aInterval = interval.Interval('d5')

        >>> aStream = corpus.parse('bach/bwv324.xml')
        >>> part = aStream.parts[0]
        >>> [str(p) for p in aStream.parts[0].pitches[:10]]
        ['B4', 'D5', 'B4', 'B4', 'B4', 'B4', 'C5', 'B4', 'A4', 'A4']

        >>> bStream = aStream.parts[0].flatten().transpose('d5')
        >>> [str(p) for p in bStream.pitches[:10]]
        ['F5', 'A-5', 'F5', 'F5', 'F5', 'F5', 'G-5', 'F5', 'E-5', 'E-5']

        Test that aStream hasn't been changed:

        >>> [str(p) for p in aStream.parts[0].pitches[:10]]
        ['B4', 'D5', 'B4', 'B4', 'B4', 'B4', 'C5', 'B4', 'A4', 'A4']

        >>> cStream = bStream.flatten().transpose('a4')
        >>> [str(p) for p in cStream.pitches[:10]]
        ['B5', 'D6', 'B5', 'B5', 'B5', 'B5', 'C6', 'B5', 'A5', 'A5']

        >>> cStream.flatten().transpose(aInterval, inPlace=True)
        >>> [str(p) for p in cStream.pitches[:10]]
        ['F6', 'A-6', 'F6', 'F6', 'F6', 'F6', 'G-6', 'F6', 'E-6', 'E-6']

        * Changed in v8: first value is position only, all other values are keyword only
        '''
        # only change the copy
        if not inPlace:
            post = self.coreCopyAsDerivation('transpose')
        else:
            post = self

        intv: interval.Interval | interval.GenericInterval
        if isinstance(value, (int, str)):
            intv = interval.Interval(value)
        elif isinstance(value, interval.ChromaticInterval):
            intv = interval.Interval(chromatic=value)
        elif isinstance(value, interval.DiatonicInterval):
            intv = interval.Interval(diatonic=value)
        else:
            if t.TYPE_CHECKING:
                assert isinstance(value, (interval.GenericInterval, interval.Interval))
            intv = value

        # for p in post.pitches:  # includes chords
        #     # do inplace transpositions on the deepcopy
        #     p.transpose(value, inPlace=True)
        #
        # for e in post.getElementsByClass(classFilterList=classFilterList):
        #     e.transpose(value, inPlace=True)

        # this will get all elements at this level and downward.
        sIterator: iterator.StreamIterator
        if recurse is True:
            sIterator = post.recurse()
        else:
            sIterator = post.iter()

        if classFilterList:
            sIterator = sIterator.addFilter(filters.ClassFilter(classFilterList))

        for e in sIterator:
            if e.isStream:
                continue
            if hasattr(e, 'transpose'):
                if isinstance(intv, interval.GenericInterval):
                    # do not transpose KeySignatures w/ Generic Intervals
                    if not isinstance(e, key.KeySignature) and hasattr(e, 'pitches'):
                        k = e.getContextByClass(key.KeySignature)
                        p: pitch.Pitch
                        for p in e.pitches:  # type: ignore
                            intv.transposePitchKeyAware(p, k, inPlace=True)
                else:
                    e.transpose(intv, inPlace=True)

        if not inPlace:
            return post
        else:
            return None

    def scaleOffsets(self, amountToScale, *, anchorZero='lowest',
                     anchorZeroRecurse=None, inPlace=False):
        '''
        Scale all offsets by a multiplication factor given
        in `amountToScale`. Durations are not altered.

        To augment or diminish a Stream,
        see the :meth:`~music21.stream.Stream.augmentOrDiminish` method.

        The `anchorZero` parameter determines if and/or where
        the zero offset is established for the set of
        offsets in this Stream before processing.
        Offsets are shifted to make either the lower
        or upper values the new zero; then offsets are scaled;
        then the shifts are removed. Accepted values are None
        (no offset shifting), "lowest", or "highest".

        The `anchorZeroRecurse` parameter determines the
        anchorZero for all embedded Streams, and Streams
        embedded within those Streams. If the lowest offset
        in an embedded Stream is non-zero, setting this value
        to None will allow the space between the start of that
        Stream and the first element to be scaled. If the
        lowest offset in an embedded Stream is non-zero,
        setting this value to 'lowest' will not alter the
        space between the start of that Stream and the first
        element to be scaled.

        To shift all the elements in a Stream, see the
        :meth:`~music21.stream.Stream.shiftElements` method.

        * Changed in v5: inPlace is default False, and anchorZero, anchorZeroRecurse
          and inPlace are keyword only arguments.
        '''
        # if we have offsets at 0, 2, 4
        # we scale by 2, getting offsets at 0, 4, 8

        # compare to an example with offsets at 10, 12, 14
        # we scale by 2; if we do not anchor at lower, we get 20, 24, 28
        # if we anchor, we get 10, 14, 18

        if not amountToScale > 0:
            raise StreamException('amountToScale must be greater than zero')

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('scaleOffsets')
        else:
            returnObj = self

        # first, get the offset shift requested
        if anchorZero in ['lowest']:
            offsetShift = Fraction(returnObj.lowestOffset)
        elif anchorZero in ['highest']:
            offsetShift = Fraction(returnObj.highestOffset)
        elif anchorZero in [None]:
            offsetShift = Fraction(0, 1)
        else:
            raise StreamException(f'an anchorZero value of {anchorZero} is not accepted')

        for e in returnObj._elements:

            # subtract the offset shift (and lowestOffset of 80 becomes 0)
            # then apply the amountToScale
            o = (returnObj.elementOffset(e) - offsetShift) * amountToScale
            # after scaling, return the shift taken away
            o += offsetShift

            # environLocal.printDebug(['changing offset', o, scalar, offsetShift])

            returnObj.coreSetElementOffset(e, o)
            # need to look for embedded Streams, and call this method
            # on them, with inPlace , as already copied if
            # inPlace is != True
            # if hasattr(e, 'elements'):  # recurse time:
            if e.isStream:
                e.scaleOffsets(amountToScale,
                               anchorZero=anchorZeroRecurse,
                               anchorZeroRecurse=anchorZeroRecurse,
                               inPlace=True)

        returnObj.coreElementsChanged()
        if not inPlace:
            return returnObj

    def scaleDurations(self, amountToScale, *, inPlace=False):
        '''
        Scale all durations by a provided scalar. Offsets are not modified.

        To augment or diminish a Stream, see the
        :meth:`~music21.stream.Stream.augmentOrDiminish` method.

        We do not retain durations in any circumstance;
        if inPlace=False, two deepcopies of each duration are done.
        '''
        if not amountToScale > 0:
            raise StreamException('amountToScale must be greater than zero')

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('scaleDurations')
        else:
            returnObj = self

        for e in returnObj.recurse().getElementsNotOfClass('Stream'):
            e.duration = e.duration.augmentOrDiminish(amountToScale)

        if inPlace is not True:
            return returnObj

    def augmentOrDiminish(self, amountToScale, *, inPlace=False):
        '''
        Given a number greater than zero,
        multiplies the current quarterLength of the
        duration of each element by this number
        as well as their offset and returns a new Stream.
        Or if `inPlace` is
        set to True, modifies the durations of each
        element within the stream.


        A number of 0.5 will halve the durations and relative
        offset positions; a number of 2 will double the
        durations and relative offset positions.



        Note that the default for inPlace is the opposite
        of what it is for augmentOrDiminish on a Duration.
        This is done purposely to reflect the most common
        usage.



        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> s.repeatAppend(n, 10)
        >>> s.highestOffset, s.highestTime
        (9.0, 10.0)
        >>> s1 = s.augmentOrDiminish(2)
        >>> s1.highestOffset, s1.highestTime
        (18.0, 20.0)
        >>> s1 = s.augmentOrDiminish(0.5)
        >>> s1.highestOffset, s1.highestTime
        (4.5, 5.0)
        '''
        if not amountToScale > 0:
            raise StreamException('amountToScale must be greater than zero')
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('augmentOrDiminish')
        else:
            returnObj = self

        # inPlace is True as a copy has already been made if nec
        returnObj.scaleOffsets(amountToScale=amountToScale, anchorZero='lowest',
                               anchorZeroRecurse=None, inPlace=True)
        returnObj.scaleDurations(amountToScale=amountToScale, inPlace=True)

        # do not need to call elements changed, as called in sub methods
        return returnObj

    def quantize(
        self,
        quarterLengthDivisors: Iterable[int] = (),
        processOffsets: bool = True,
        processDurations: bool = True,
        inPlace: bool = False,
        recurse: bool = False,
    ):
        # noinspection PyShadowingNames
        '''
        Quantize time values in this Stream by snapping offsets
        and/or durations to the nearest multiple of a quarter length value
        given as one or more divisors of 1 quarter length. The quantized
        value found closest to a divisor multiple will be used.

        The `quarterLengthDivisors` provides a flexible way to provide quantization
        settings. For example, (2,) will snap all events to eighth note grid.
        (4, 3) will snap events to sixteenth notes and eighth note triplets,
        whichever is closer. (4, 6) will snap events to sixteenth notes and
        sixteenth note triplets.  If quarterLengthDivisors is not specified then
        defaults.quantizationQuarterLengthDivisors is used.  The default is (4, 3).

        `processOffsets` determines whether the Offsets are quantized.

        `processDurations` determines whether the Durations are quantized.

        Both are set to True by default.  Setting both to False does nothing to the Stream.

        if `inPlace` is True, then the quantization is done on the Stream itself.  If False
        (default) then a new quantized Stream of the same class is returned.

        If `recurse` is True, then all substreams are also quantized.
        If False (default), then only the highest level of the Stream is quantized.

        * Changed in v7:
           - `recurse` defaults False
           - look-ahead approach to choosing divisors to avoid gaps when processing durations

        >>> n = note.Note()
        >>> n.quarterLength = 0.49
        >>> s = stream.Stream()
        >>> s.repeatInsert(n, [0.1, 0.49, 0.9])
        >>> nShort = note.Note()
        >>> nShort.quarterLength = 0.26
        >>> s.repeatInsert(nShort, [1.49, 1.76])

        >>> s.quantize((4,), processOffsets=True, processDurations=True, inPlace=True)
        >>> [e.offset for e in s]
        [0.0, 0.5, 1.0, 1.5, 1.75]
        >>> [e.duration.quarterLength for e in s]
        [0.5, 0.5, 0.5, 0.25, 0.25]

        The error in quantization is set in the editorial attribute for the note in
        two places `.offsetQuantizationError` and `.quarterLengthQuantizationError`

        >>> [e.editorial.offsetQuantizationError for e in s.notes]
        [0.1, -0.01, -0.1, -0.01, 0.01]
        >>> [e.editorial.quarterLengthQuantizationError for e in s.notes]
        [-0.01, -0.01, -0.01, 0.01, 0.01]

        with default quarterLengthDivisors...

        >>> s = stream.Stream()
        >>> s.repeatInsert(n, [0.1, 0.49, 0.9])
        >>> nShort = note.Note()
        >>> nShort.quarterLength = 0.26
        >>> s.repeatInsert(nShort, [1.49, 1.76])
        >>> quantized = s.quantize(processOffsets=True, processDurations=True, inPlace=False)
        >>> [e.offset for e in quantized]
        [0.0, 0.5, 1.0, 1.5, 1.75]
        >>> [e.duration.quarterLength for e in quantized]
        [0.5, 0.5, 0.5, 0.25, 0.25]

        Set `recurse=True` to quantize elements in substreams such as parts, measures, voices:

        >>> myPart = converter.parse('tinynotation: c32 d32 e32 f32')
        >>> myPart.quantize(inPlace=True)
        >>> [e.offset for e in myPart.measure(1).notes]  # no change!
        [0.0, 0.125, 0.25, 0.375]

        >>> myPart.quantize(inPlace=True, recurse=True)
        >>> [e.offset for e in myPart.measure(1).notes]
        [0.0, 0.0, 0.25, Fraction(1, 3)]

        * New in v7: if both `processDurations` and `processOffsets` are True, then
          the next note's quantized offset is taken into account when quantizing the
          duration of the current note. This is to prevent unnecessary gaps from applying
          different quantization units to adjacent notes:

        >>> s2 = stream.Stream()
        >>> nOddLength = note.Note(quarterLength=0.385)
        >>> s2.repeatInsert(nOddLength, [0, 0.5, 1, 1.5])
        >>> s2.show('t', addEndTimes=True)
            {0.0 - 0.385} <music21.note.Note C>
            {0.5 - 0.885} <music21.note.Note C>
            {1.0 - 1.385} <music21.note.Note C>
            {1.5 - 1.885} <music21.note.Note C>

        Before v.7, this would have yielded four triplet-eighths (separated by 1/6 QL rests):

        >>> s2.quantize(processOffsets=True, processDurations=True, inPlace=True)
        >>> s2.show('text', addEndTimes=True)
            {0.0 - 0.5} <music21.note.Note C>
            {0.5 - 1.0} <music21.note.Note C>
            {1.0 - 1.5} <music21.note.Note C>
            {1.5 - 1.8333} <music21.note.Note C>

        OMIT_FROM_DOCS

        Test changing defaults, running, and changing back...

        >>> dd = defaults.quantizationQuarterLengthDivisors
        >>> defaults.quantizationQuarterLengthDivisors = (3,)

        >>> u = s.quantize(processOffsets=True, processDurations=True, inPlace=False)
        >>> [e.offset for e in u]
        [0.0, Fraction(1, 3), 1.0, Fraction(4, 3), Fraction(5, 3)]
        >>> [e.duration.quarterLength for e in u]
        [Fraction(1, 3), Fraction(1, 3), Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)]

        Original unchanged because inPlace=False:

        >>> [e.offset for e in s]
        [Fraction(1, 10), Fraction(49, 100), Fraction(9, 10), Fraction(149, 100), Fraction(44, 25)]

        >>> defaults.quantizationQuarterLengthDivisors = dd
        >>> v = s.quantize(processOffsets=True, processDurations=True, inPlace=False)
        >>> [e.offset for e in v]
        [0.0, 0.5, 1.0, 1.5, 1.75]
        >>> [e.duration.quarterLength for e in v]
        [0.5, 0.5, 0.5, 0.25, 0.25]
        '''
        if not quarterLengthDivisors:
            quarterLengthDivisors = defaults.quantizationQuarterLengthDivisors

        # this presently is not trying to avoid overlaps that
        # result from quantization; this may be necessary

        def bestMatch(
            target,
            divisors,
            zeroAllowed=True,
            gapToFill=0.0
        ) -> BestQuantizationMatch:
            found: list[BestQuantizationMatch] = []
            for div in divisors:
                tick = 1 / div  # divisor expressed as QL, e.g. 0.25
                match, error, signedErrorInner = common.nearestMultiple(target, tick)
                if not zeroAllowed and match == 0.0:
                    match = tick
                    signedErrorInner = round(target - match, 7)
                    error = abs(signedErrorInner)
                if gapToFill % tick == 0:
                    remainingGap = 0.0
                else:
                    remainingGap = max(gapToFill - match, 0.0)
                # Sort by remainingGap, then unsigned error, then tick
                found.append(
                    BestQuantizationMatch(
                        remainingGap, error, tick, match, signedErrorInner, div))
            # get smallest remainingGap, error, tick
            bestMatchTuple = min(found)
            return bestMatchTuple

        def findNextElementNotCoincident(
            useStream: Stream,
            startIndex: int,
            startOffset: OffsetQL,
        ) -> tuple[base.Music21Object | None, BestQuantizationMatch | None]:
            for next_el in useStream._elements[startIndex:]:
                next_offset = useStream.elementOffset(next_el)
                look_ahead_result = bestMatch(float(next_offset), quarterLengthDivisors)
                if look_ahead_result.match > startOffset:
                    return next_el, look_ahead_result
            return None, None

        if inPlace is False:
            returnStream = self.coreCopyAsDerivation('quantize')
        else:
            returnStream = self

        useStreams = [returnStream]
        if recurse is True:
            useStreams = list(returnStream.recurse(streamsOnly=True, includeSelf=True))

        for useStream in useStreams:
            # coreSetElementOffset() will immediately set isSorted = False,
            # but we need to know if the stream was originally sorted to know
            # if it's worth "looking ahead" to the next offset. If a stream
            # is unsorted originally, this "looking ahead" could become O(n^2).
            originallySorted = useStream.isSorted
            rests_lacking_durations: list[note.Rest] = []
            for i, e in enumerate(useStream._elements):
                if processOffsets:
                    o = useStream.elementOffset(e)
                    sign = 1
                    if o < 0:
                        sign = -1
                        o = -1 * o
                    o_matchTuple = bestMatch(float(o), quarterLengthDivisors)
                    o = o_matchTuple.match * sign
                    useStream.coreSetElementOffset(e, o)
                    if hasattr(e, 'editorial') and o_matchTuple.signedError != 0:
                        e.editorial.offsetQuantizationError = o_matchTuple.signedError * sign
                if processDurations:
                    ql = e.duration.quarterLength
                    ql = max(ql, 0)  # negative ql possible in buggy MIDI files?
                    zeroAllowed = not isinstance(e, note.NotRest) or e.duration.isGrace
                    if processOffsets and originallySorted:
                        next_element, look_ahead_result = (
                            findNextElementNotCoincident(
                                useStream=useStream, startIndex=i + 1, startOffset=o))
                        if next_element is not None and look_ahead_result is not None:
                            gapToFill = opFrac(look_ahead_result.match - e.offset)
                            d_matchTuple = bestMatch(
                                float(ql), quarterLengthDivisors, zeroAllowed, gapToFill)
                        else:
                            d_matchTuple = bestMatch(float(ql), quarterLengthDivisors, zeroAllowed)
                    else:
                        d_matchTuple = bestMatch(float(ql), quarterLengthDivisors, zeroAllowed)
                    if d_matchTuple.match == 0 and isinstance(e, note.Rest):
                        rests_lacking_durations.append(e)
                    else:
                        e.duration.quarterLength = d_matchTuple.match
                        if hasattr(e, 'editorial') and d_matchTuple.signedError != 0:
                            e.editorial.quarterLengthQuantizationError = d_matchTuple.signedError

            # end for e in ._elements
            # ran coreSetElementOffset
            useStream.coreElementsChanged(updateIsFlat=False)

            useStream.remove(rests_lacking_durations)

        if inPlace is False:
            return returnStream

    def expandRepeats(self: StreamType, copySpanners: bool = True) -> StreamType:
        '''
        Expand this Stream with repeats. Nested repeats
        given with :class:`~music21.bar.Repeat` objects, or
        repeats and sections designated with
        :class:`~music21.repeat.RepeatExpression` objects, are all expanded.

        This method always returns a new Stream, with
        deepcopies of all contained elements at all levels.

        Uses the :class:`~music21.repeat.Expander` object in the `repeat` module.
        '''
        # TODO: needs DOC TEST
        if not self.hasMeasures():
            raise StreamException(
                'cannot process repeats on Stream that does not contain measures'
            )

        ex = repeat.Expander(self)
        post = ex.process()

        # copy all non-repeats
        # do not copy repeat brackets
        for e in self.getElementsNotOfClass(Measure):
            if 'RepeatBracket' not in e.classes:
                eNew = copy.deepcopy(e)  # assume that this is needed
                post.insert(self.elementOffset(e), eNew)

        # all elements at this level and in measures have been copied; now we
        # need to reconnect spanners
        if copySpanners:
            # environLocal.printDebug(['Stream.expandRepeats', 'copying spanners'])
            # spannerBundle = spanner.SpannerBundle(list(post.flatten().spanners))
            spannerBundle = post.spannerBundle
            # iterate over complete tree (need containers); find
            # all new/old pairs
            for e in post.recurse():
                # update based on last id, new object
                if e.sites.hasSpannerSite():
                    origin = e.derivation.origin
                    if (origin is not None
                            and e.derivation.method == '__deepcopy__'):
                        spannerBundle.replaceSpannedElement(origin, e)

        return post

    # --------------------------------------------------------------------------
    # slicing and recasting a note as many notes

    def sliceByQuarterLengths(self, quarterLengthList, *, target=None,
                              addTies=True, inPlace=False):
        '''
        Slice all :class:`~music21.duration.Duration` objects on all Notes and Rests
        of this Stream.
        Duration are sliced according to values provided in `quarterLengthList` list.
        If the sum of these values is less than the Duration, the values are accumulated
        in a loop to try to fill the Duration. If a match cannot be found, an
        Exception is raised.

        If `target` is None, the entire Stream is processed. Otherwise, only the element
        specified is manipulated.

        '''
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('sliceByQuarterLengths')
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass(Measure):
                m.sliceByQuarterLengths(quarterLengthList,
                                        target=target, addTies=addTies, inPlace=True)
            returnObj.coreElementsChanged()
            return returnObj  # exit

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass(Part):
                p.sliceByQuarterLengths(quarterLengthList,
                                        target=target, addTies=addTies, inPlace=True)
            returnObj.coreElementsChanged()
            return returnObj  # exit

        if not common.isListLike(quarterLengthList):
            quarterLengthList = [quarterLengthList]

        if target is not None:
            # get the element out of return obj
            # need to use self.index to get index value
            eToProcess = [returnObj[self.index(target)]]
        else:  # get elements list from Stream
            eToProcess = returnObj.notesAndRests

        for e in eToProcess:
            # if qlList values are greater than the found duration, skip
            if opFrac(sum(quarterLengthList)) > e.quarterLength:
                continue
            elif not opFrac(sum(quarterLengthList)) == e.quarterLength:
                # try to map a list that is of sufficient duration
                qlProcess = []
                i = 0
                while True:
                    qlProcess.append(
                        quarterLengthList[i % len(quarterLengthList)])
                    i += 1
                    sumQL = opFrac(sum(qlProcess))
                    if sumQL >= e.quarterLength:
                        break
            else:
                qlProcess = quarterLengthList

            # environLocal.printDebug(['got qlProcess', qlProcess,
            # 'for element', e, e.quarterLength])

            if not opFrac(sum(qlProcess)) == e.quarterLength:
                raise StreamException(
                    'cannot map quarterLength list into element Duration: %s, %s' % (
                        sum(qlProcess), e.quarterLength))

            post = e.splitByQuarterLengths(qlProcess, addTies=addTies)
            # remove e from the source
            oInsert = e.getOffsetBySite(returnObj)
            returnObj.remove(e)
            for eNew in post:
                returnObj.coreInsert(oInsert, eNew)
                oInsert = opFrac(oInsert + eNew.quarterLength)

        returnObj.coreElementsChanged()

        if not inPlace:
            return returnObj

    def sliceByGreatestDivisor(self, *, addTies=True, inPlace=False):
        '''
        Slice all :class:`~music21.duration.Duration` objects on all Notes and Rests of this Stream.
        Duration are sliced according to the approximate GCD found in all durations.
        '''
        # when operating on a Stream, this should take all durations found
        # and use the approximateGCD to get a min duration; then, call sliceByQuarterLengths

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('sliceByGreatestDivisor')
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass(Measure):
                m.sliceByGreatestDivisor(addTies=addTies, inPlace=True)
            return returnObj  # exit

        uniqueQuarterLengths = set()
        for e in returnObj.notesAndRests:
            if e.quarterLength not in uniqueQuarterLengths:
                uniqueQuarterLengths.add(e.quarterLength)

        # environLocal.printDebug(['unique quarter lengths', uniqueQuarterLengths])

        # will raise an exception if no gcd can be found
        divisor = common.approximateGCD(uniqueQuarterLengths)

        # process in place b/c a copy, if necessary, has already been made
        returnObj.sliceByQuarterLengths(quarterLengthList=[divisor],
                                        target=None, addTies=addTies, inPlace=True)

        if not inPlace:
            return returnObj

    def sliceAtOffsets(
        self,
        offsetList,
        target=None,
        addTies=True,
        inPlace=False,
        displayTiedAccidentals=False
    ):
        # noinspection PyShadowingNames
        '''
        Given a list of quarter lengths, slice and optionally tie all
        Music21Objects crossing these points.

        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.duration.type = 'whole'
        >>> s.append(n)
        >>> post = s.sliceAtOffsets([1, 2, 3], inPlace=True)
        >>> [(e.offset, e.quarterLength) for e in s]
        [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0)]
        '''
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('sliceAtOffsets')
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass(Measure):
                # offset values are not relative to measure; need to
                # shift by each measure's offset
                offsetListLocal = [o - m.getOffsetBySite(returnObj) for o in offsetList]
                m.sliceAtOffsets(offsetList=offsetListLocal,
                                 addTies=addTies,
                                 inPlace=True,
                                 displayTiedAccidentals=displayTiedAccidentals)
            return returnObj  # exit

        if returnObj.hasPartLikeStreams():
            # part-like requires getting Streams, not Parts
            for p in returnObj.getElementsByClass(Stream):
                offsetListLocal = [o - p.getOffsetBySite(returnObj) for o in offsetList]
                p.sliceAtOffsets(offsetList=offsetListLocal,
                                 addTies=addTies,
                                 inPlace=True,
                                 displayTiedAccidentals=displayTiedAccidentals)
            return returnObj  # exit

        # list of start, start+dur, element, all in abs offset time
        offsetMap = returnObj.offsetMap()

        offsetList = [opFrac(o) for o in offsetList]

        for ob in offsetMap:
            # if target is defined, only modify that object
            e, oStart, oEnd, unused_voiceCount = ob
            if target is not None and id(e) != id(target):
                continue

            cutPoints = []
            oStart = opFrac(oStart)
            oEnd = opFrac(oEnd)

            for o in offsetList:
                if oStart < o < oEnd:
                    cutPoints.append(o)
            # environLocal.printDebug(['cutPoints', cutPoints, 'oStart', oStart, 'oEnd', oEnd])
            if cutPoints:
                # remove old
                # eProc = returnObj.remove(e)
                eNext = e
                oStartNext = oStart
                for o in cutPoints:
                    oCut = o - oStartNext
                    unused_eComplete, eNext = eNext.splitAtQuarterLength(
                        oCut,
                        retainOrigin=True,
                        addTies=addTies,
                        displayTiedAccidentals=displayTiedAccidentals
                    )
                    # only need to insert eNext, as eComplete was modified
                    # in place due to retainOrigin option
                    # insert at o, not oCut (duration into element)
                    returnObj.coreInsert(o, eNext)
                    oStartNext = o
        returnObj.coreElementsChanged()
        if inPlace is False:
            return returnObj

    def sliceByBeat(self,
                    target=None,
                    addTies=True,
                    inPlace=False,
                    displayTiedAccidentals=False):
        '''
        Slice all elements in the Stream that have a Duration at
        the offsets determined to be the beat from the local TimeSignature.

        * Changed in v7: return None if inPlace is True
        '''

        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('sliceByBeat')
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass(Measure):
                m.sliceByBeat(target=target,
                              addTies=addTies,
                              inPlace=True,
                              displayTiedAccidentals=displayTiedAccidentals)
            return returnObj  # exit

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass(Part):
                p.sliceByBeat(target=target,
                              addTies=addTies,
                              inPlace=True,
                              displayTiedAccidentals=displayTiedAccidentals)
            return returnObj  # exit

        # this will return a default
        # using this method to work on Stream, not just Measures
        tsStream = returnObj.getTimeSignatures(returnDefault=True)

        if not tsStream:
            raise StreamException('no time signature was found')

        if len(tsStream) > 1:
            raise StreamException('not yet implemented: slice by changing time signatures')

        offsetList = tsStream[0].getBeatOffsets()
        returnObj.sliceAtOffsets(offsetList,
                                 target=target,
                                 addTies=addTies,
                                 inPlace=True,
                                 displayTiedAccidentals=displayTiedAccidentals)

        if not inPlace:
            return returnObj

    # --------------------------------------------------------------------------
    # get boolean information from the Stream

    def hasMeasures(self):
        '''
        Return a boolean value showing if this Stream contains Measures.

        >>> p = stream.Part()
        >>> p.repeatAppend(note.Note(), 8)
        >>> p.hasMeasures()
        False
        >>> p.makeMeasures(inPlace=True)
        >>> len(p.getElementsByClass(stream.Measure))
        2
        >>> p.hasMeasures()
        True

        Only returns True if the immediate Stream has measures, not if there are nested measures:

        >>> sc = stream.Score()
        >>> sc.append(p)
        >>> sc.hasMeasures()
        False
        '''
        if 'hasMeasures' not in self._cache or self._cache['hasMeasures'] is None:
            post = False
            # do not need to look in endElements
            for obj in self._elements:
                # if obj is a Part, we have multi-parts
                if isinstance(obj, Measure):
                    post = True
                    break  # only need one
            self._cache['hasMeasures'] = post
        return self._cache['hasMeasures']

    def hasVoices(self):
        '''
        Return a boolean value showing if this Stream contains Voices
        '''
        if 'hasVoices' not in self._cache or self._cache['hasVoices'] is None:
            post = False
            # do not need to look in endElements
            for obj in self._elements:
                # if obj is a Part, we have multi-parts
                if 'Voice' in obj.classes:
                    post = True
                    break  # only need one
            self._cache['hasVoices'] = post
        return self._cache['hasVoices']

    def hasPartLikeStreams(self):
        '''
        Return a boolean value showing if this Stream contains any Parts,
        or Part-like sub-Streams.

        Part-like sub-streams are Streams that contain Measures or Notes.
        And where no sub-stream begins at an offset besides zero.

        >>> s = stream.Score()
        >>> s.hasPartLikeStreams()
        False
        >>> p1 = stream.Part()
        >>> p1.repeatAppend(note.Note(), 8)
        >>> s.insert(0, p1)
        >>> s.hasPartLikeStreams()
        True

        A stream that has a measure in it is not a part-like stream.

        >>> s = stream.Score()
        >>> m1 = stream.Measure()
        >>> m1.repeatAppend(note.Note(), 4)
        >>> s.append(m1)
        >>> s.hasPartLikeStreams()
        False


        A stream with a single generic Stream substream at the beginning has part-like Streams...

        >>> s = stream.Score()
        >>> m1 = stream.Stream()
        >>> m1.repeatAppend(note.Note(), 4)
        >>> s.append(m1)
        >>> s.hasPartLikeStreams()
        True


        Adding another though makes it not part-like.

        >>> m2 = stream.Stream()
        >>> m2.repeatAppend(note.Note(), 4)
        >>> s.append(m2)
        >>> s.hasPartLikeStreams()
        False

        Flat objects do not have part-like Streams:

        >>> sf = s.flatten()
        >>> sf.hasPartLikeStreams()
        False
        '''
        if 'hasPartLikeStreams' not in self._cache or self._cache['hasPartLikeStreams'] is None:
            multiPart = False
            if not self.isFlat:  # if flat, does not have parts!
                # do not need to look in endElements
                for obj in self.getElementsByClass(Stream):
                    # if obj is a Part, we have multi-parts
                    if isinstance(obj, Part):
                        multiPart = True
                        break

                    elif isinstance(obj, (Measure, Voice)):
                        multiPart = False
                        break

                    elif obj.offset != 0.0:
                        multiPart = False
                        break

                    # if components are streams of Notes or Measures,
                    # then assume this is like a Part
                    elif (obj.getElementsByClass(Measure)
                          or obj.notesAndRests):
                        multiPart = True
            self._cache['hasPartLikeStreams'] = multiPart
        return self._cache['hasPartLikeStreams']

    def isTwelveTone(self):
        '''
        Return true if this Stream only employs twelve-tone equal-tempered pitch values.


        >>> s = stream.Stream()
        >>> s.append(note.Note('G#4'))
        >>> s.isTwelveTone()
        True
        >>> s.append(note.Note('G~4'))
        >>> s.isTwelveTone()
        False
        '''
        for p in self.pitches:
            if not p.isTwelveTone():
                return False
        return True

    def isWellFormedNotation(self) -> bool:
        # noinspection PyShadowingNames
        '''
        Return True if, given the context of this Stream or Stream subclass,
        contains what appears to be well-formed notation. This often means
        the formation of Measures, or a Score that contains Part with Measures.


        >>> s = corpus.parse('bwv66.6')
        >>> s.isWellFormedNotation()
        True
        >>> s.parts[0].isWellFormedNotation()
        True
        >>> s.parts[0].getElementsByClass(stream.Measure).first().isWellFormedNotation()
        True

        >>> s2 = stream.Score()
        >>> m = stream.Measure()
        >>> s2.append(m)
        >>> s2.isWellFormedNotation()
        False

        >>> o = stream.Opus([s])
        >>> o.isWellFormedNotation()
        True
        >>> o2 = stream.Opus([s2])
        >>> o2.isWellFormedNotation()
        False

        Only Measures and Voices are allowed to contain notes and rests directly:

        >>> m.isWellFormedNotation()
        True
        >>> s2.append(note.Rest())
        >>> s2.isWellFormedNotation()
        False
        '''
        def allSubstreamsHaveMeasures(testStream):
            return all(s.hasMeasures() for s in testStream.getElementsByClass(Stream))

        # if a measure or voice, we assume we are well-formed
        if isinstance(self, (Measure, Voice)):
            return True
        # all other Stream classes are not well-formed if they have "loose" notes
        elif self.notesAndRests:
            return False
        elif isinstance(self, Part):
            if self.hasMeasures():
                return True
        elif isinstance(self, Opus):
            return all(allSubstreamsHaveMeasures(s) for s in self.scores)
        elif self.hasPartLikeStreams():
            return allSubstreamsHaveMeasures(self)
        # all other conditions are not well-formed notation
        return False

    # --------------------------------------------------------------------------
    @property
    def notesAndRests(self) -> iterator.StreamIterator[note.GeneralNote]:
        '''
        The notesAndRests property of a Stream returns a `StreamIterator`
        that consists only of the :class:`~music21.note.GeneralNote` objects found in
        the stream.  The new Stream will contain
        mostly notes and rests (including
        :class:`~music21.note.Note`,
        :class:`~music21.chord.Chord`,
        :class:`~music21.note.Rest`) but also their subclasses, such as
        `Harmony` objects (`ChordSymbols`, `FiguredBass`), etc.


        >>> s1 = stream.Stream()
        >>> k1 = key.KeySignature(0)  # key of C
        >>> n1 = note.Note('B')
        >>> r1 = note.Rest()
        >>> c1 = chord.Chord(['A', 'B-'])
        >>> s1.append([k1, n1, r1, c1])
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of no sharps or flats>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Rest quarter>
        {2.0} <music21.chord.Chord A B->

        `.notesAndRests` removes the `KeySignature` object but keeps the `Rest`.

        >>> notes1 = s1.notesAndRests.stream()
        >>> notes1.show('text')
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Rest quarter>
        {2.0} <music21.chord.Chord A B->

        The same caveats about `Stream` classes and `.flatten()` in `.notes` apply here.
        '''
        noteIterator: iterator.StreamIterator[note.GeneralNote] = (
            self.getElementsByClass(note.GeneralNote)
        )
        noteIterator.overrideDerivation = 'notesAndRests'
        return noteIterator

    @property
    def notes(self) -> iterator.StreamIterator[note.NotRest]:
        '''
        The `.notes` property of a Stream returns an iterator
        that consists only of the notes (that is,
        :class:`~music21.note.Note`,
        :class:`~music21.chord.Chord`, etc.) found
        in the stream. This excludes :class:`~music21.note.Rest` objects.

        >>> p1 = stream.Part()
        >>> k1 = key.KeySignature(0)  # key of C
        >>> n1 = note.Note('B')
        >>> r1 = note.Rest()
        >>> c1 = chord.Chord(['A', 'B-'])
        >>> p1.append([k1, n1, r1, c1])
        >>> p1.show('text')
        {0.0} <music21.key.KeySignature of no sharps or flats>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Rest quarter>
        {2.0} <music21.chord.Chord A B->

        >>> noteStream = p1.notes.stream()
        >>> noteStream.show('text')
        {0.0} <music21.note.Note B>
        {2.0} <music21.chord.Chord A B->

        Notice that `.notes` returns a :class:`~music21.stream.iterator.StreamIterator` object

        >>> p1.notes
        <music21.stream.iterator.StreamIterator for Part:0x105b56128 @:0>

        Let's add a measure to `p1`:

        >>> m1 = stream.Measure()
        >>> n2 = note.Note('D')
        >>> m1.insert(0, n2)
        >>> p1.append(m1)

        Now note that `n2` is *not* found in `p1.notes`

        >>> p1.notes.stream().show('text')
        {0.0} <music21.note.Note B>
        {2.0} <music21.chord.Chord A B->

        We need to call `p1.flatten().notes` to find it:

        >>> p1.flatten().notes.stream().show('text')
        {0.0} <music21.note.Note B>
        {2.0} <music21.chord.Chord A B->
        {3.0} <music21.note.Note D>

        (Technical note: All elements of class NotRest are being found
        right now.  This will eventually change to also filter out
        Unpitched objects, so that all elements returned by
        `.notes` have a `.pitches` attribute.
        '''
        noteIterator: iterator.StreamIterator[note.NotRest] = self.getElementsByClass(note.NotRest)
        noteIterator.overrideDerivation = 'notes'
        return noteIterator

    @property
    def pitches(self) -> list[pitch.Pitch]:
        '''
        Returns all :class:`~music21.pitch.Pitch` objects found in any
        element in the Stream as a Python List. Elements such as
        Streams, and Chords will have their Pitch objects accumulated as
        well. For that reason, a flat representation is not required.

        Note that this does not include any ornamental pitches implied
        by any ornaments on those Notes and Chords.  To get those, use
        the makeNotation.ornamentalPitches(s) method.

        Pitch objects are returned in a List, not a Stream.  This usage
        differs from the .notes property, but makes sense since Pitch
        objects usually have by default a Duration of zero. This is an important difference
        between them and :class:`music21.note.Note` objects.

        key.Key objects are subclasses of Scales, which DO have a .pitches list, but
        they are specifically exempt from looking for pitches, since that is unlikely
        what someone wants here.

        N.B., TODO: This may turn to an Iterator soon.

        >>> a = corpus.parse('bach/bwv324.xml')
        >>> partOnePitches = a.parts[0].pitches
        >>> len(partOnePitches)
        25
        >>> partOnePitches[0]
        <music21.pitch.Pitch B4>
        >>> [str(p) for p in partOnePitches[0:10]]
        ['B4', 'D5', 'B4', 'B4', 'B4', 'B4', 'C5', 'B4', 'A4', 'A4']


        Note that the pitches returned above are
        objects, not text:

        >>> partOnePitches[0].octave
        4

        Since all elements with a `.pitches` list are returned and streams themselves have
        `.pitches` properties (the docs you are reading now), pitches from embedded streams
        are also returned.  Flattening a stream is not necessary.  Whether this is a
        feature or a bug is in the eye of the beholder.

        >>> len(a.pitches)
        104

        Chords get their pitches found as well:

        >>> c = chord.Chord(['C4', 'E4', 'G4'])
        >>> n = note.Note('F#4')
        >>> m = stream.Measure()
        >>> m.append(n)
        >>> m.append(c)
        >>> m.pitches
        [<music21.pitch.Pitch F#4>, <music21.pitch.Pitch C4>,
         <music21.pitch.Pitch E4>, <music21.pitch.Pitch G4>]
        '''
        post = []
        for e in self.elements:
            if isinstance(e, key.Key):
                continue  # has .pitches but should not be added
            # both GeneralNotes and Stream have a pitches properties; this just
            # causes a recursive pitch gathering
            elif isinstance(e, (note.GeneralNote, Stream)):
                post.extend(list(e.pitches))
        return post

    # --------------------------------------------------------------------------
    # interval routines
    @overload
    def findConsecutiveNotes(
        self,
        *,
        skipRests: bool = False,
        skipChords: t.Literal[False] = False,
        skipUnisons: bool = False,
        skipOctaves: bool = False,
        skipGaps: bool = False,
        getOverlaps: bool = False,
        noNone: t.Literal[True],
        **keywords
    ) -> list[note.NotRest]:
        return []

    @overload
    def findConsecutiveNotes(
        self,
        *,
        skipRests: bool = False,
        skipChords: t.Literal[True],
        skipUnisons: bool = False,
        skipOctaves: bool = False,
        skipGaps: bool = False,
        getOverlaps: bool = False,
        noNone: t.Literal[True],
        **keywords
    ) -> list[note.Note]:
        return []

    @overload
    def findConsecutiveNotes(
        self,
        *,
        skipRests: bool = False,
        skipChords: bool = False,
        skipUnisons: bool = False,
        skipOctaves: bool = False,
        skipGaps: bool = False,
        getOverlaps: bool = False,
        noNone: t.Literal[False] = False,
        **keywords
    ) -> list[note.NotRest | None]:
        return []

    def findConsecutiveNotes(
        self,
        *,
        skipRests: bool = False,
        skipChords: bool = False,
        skipUnisons: bool = False,
        skipOctaves: bool = False,
        skipGaps: bool = False,
        getOverlaps: bool = False,
        noNone: bool = False,
        **keywords
    ) -> t.Union[
            list[note.NotRest | None],
            list[note.NotRest],
            list[note.Note],
    ]:
        r'''
        Returns a list of consecutive *pitched* Notes in a Stream.

        A single "None" is placed in the list
        at any point there is a discontinuity (such as if there is a
        rest between two pitches), unless the `noNone` parameter is True.

        How to determine consecutive pitches is a little tricky and there are many options:

        * The `skipUnisons` parameter uses the midi-note value (.ps) to determine unisons,
          so enharmonic transitions (F# -> Gb) are
          also skipped if `skipUnisons` is true.  We believe that this is the most common usage.
        * However, because
          of this, you cannot completely be sure that the
          x.findConsecutiveNotes() - x.findConsecutiveNotes(skipUnisons=True)
          will give you the number of P1s in the piece, because there could be
          d2's in there as well.

        See test.TestStream.testFindConsecutiveNotes() for usage details.

        This example is adapted from the tutorials/Examples page.

        >>> s = converter.parse("tinynotation: 4/4 f8 d'8~ d'8 d'8~ d'4 b'-8 a'-8 a-8")
        >>> m = s.measure(1)
        >>> m.findConsecutiveNotes(skipUnisons=True, skipOctaves=True,
        ...                        skipRests=True, noNone=True)
        [<music21.note.Note F>, <music21.note.Note D>,
         <music21.note.Note B->, <music21.note.Note A->]

        >>> m.findConsecutiveNotes(skipUnisons=False,
        ...                        skipRests=True, noNone=True)
        [<music21.note.Note F>, <music21.note.Note D>,
         <music21.note.Note D>, <music21.note.Note D>, <music21.note.Note D>,
         <music21.note.Note B->, <music21.note.Note A->]

        * Changed in v7:

          * now finds notes in Voices without requiring `getOverlaps=True`
            and iterates over Parts rather than flattening.

          * If `noNone=False`, inserts `None`
            when backing up to scan a subsequent voice or part.

        * Changed in v8: all parameters are keyword only.


        OMIT_FROM_DOCS

        N.B. for chords, currently, only the first pitch is tested for unison.
        this is a bug TODO: FIX

        (\*\*keywords is there so that other methods that pass along dicts to
        findConsecutiveNotes don't have to remove
        their own args; this method is used in melodicIntervals.)

        this is omitted -- add docs above.
        '''
        if self.isSorted is False and self.autoSort:
            self.sort()
        returnList: list[note.NotRest | None] = []
        lastStart: OffsetQL = 0.0
        lastEnd: OffsetQL = 0.0
        lastContainerEnd: OffsetQL = 0.0
        lastWasNone = False
        lastPitches: tuple[pitch.Pitch, ...] = ()
        if skipOctaves is True:
            skipUnisons = True  # implied

        for container in self.recurse(streamsOnly=True, includeSelf=True):
            if (container.offset < lastContainerEnd
                    and container.getElementsByClass(note.GeneralNote)
                    and noNone is False):
                returnList.append(None)
                lastWasNone = True
                lastPitches = ()

            lastStart = 0.0
            lastEnd = 0.0

            # NB: NOT a recursive search
            # do not want to capture Measure containing only Voices,
            # Part containing only Measures, etc.
            if container.getElementsByClass(note.GeneralNote):
                lastContainerEnd = container.highestTime

            # Filter out all but notes and rests and chords, etc.
            for e in container.getElementsByClass(note.GeneralNote):
                if (lastWasNone is False
                        and skipGaps is False
                        and e.offset > lastEnd):
                    if not noNone:
                        returnList.append(None)
                        lastWasNone = True
                if isinstance(e, note.Note):
                    if not (skipUnisons is False
                           or len(lastPitches) != 1
                           or e.pitch.pitchClass != lastPitches[0].pitchClass
                           or (skipOctaves is False
                                and e.pitch.ps != lastPitches[0].ps)):
                        continue
                    if getOverlaps is False and e.offset < lastEnd:
                        continue

                    returnList.append(e)
                    if e.offset < lastEnd:  # is an overlap...
                        continue

                    lastStart = e.offset
                    lastEnd = opFrac(lastStart + e.duration.quarterLength)
                    lastWasNone = False
                    lastPitches = e.pitches

                # if we have a chord
                elif isinstance(e, chord.Chord) and len(e.pitches) > 1:
                    if skipChords is True:
                        if lastWasNone is False and not noNone:
                            returnList.append(None)
                            lastWasNone = True
                            lastPitches = ()
                    # if we have a chord
                    elif (not (skipUnisons is True
                                and len(lastPitches) == len(e.pitches)
                                and (p.ps for p in e.pitches) == (p.ps for p in lastPitches)
                               )
                          and (getOverlaps is True or e.offset >= lastEnd)):
                        returnList.append(e)
                        if e.offset < lastEnd:  # is an overlap...
                            continue

                        lastStart = e.offset
                        lastEnd = opFrac(lastStart + e.duration.quarterLength)
                        lastPitches = e.pitches
                        lastWasNone = False

                elif (skipRests is False
                      and isinstance(e, note.Rest)
                      and lastWasNone is False):
                    if noNone is False:
                        returnList.append(None)
                        lastWasNone = True
                        lastPitches = ()
                elif skipRests is True and isinstance(e, note.Rest):
                    lastEnd = opFrac(e.offset + e.duration.quarterLength)

        if lastWasNone is True:
            returnList.pop()  # removes the last-added element
        return returnList

    def melodicIntervals(self, **skipKeywords):
        '''
        Returns a Stream of :class:`~music21.interval.Interval` objects
        between Notes (and by default, Chords) that follow each other in a stream.
        the offset of the Interval is the offset of the beginning of the interval
        (if two notes are adjacent, then this offset is equal to the offset of
        the second note, but if skipRests is set to True or there is a gap
        in the Stream, then these two numbers
        will be different).

        See :meth:`~music21.stream.Stream.findConsecutiveNotes` in this class for
        a discussion of what is meant by default for "consecutive notes", and
        which keywords such as skipChords, skipRests, skipUnisons, etc. can be
        used to change that behavior.

        The interval between a Note and a Chord (or between two chords) is the
        interval to the first pitch of the Chord (pitches[0]) which is usually the lowest.
        For more complex interval calculations,
        run :meth:`~music21.stream.Stream.findConsecutiveNotes` and then calculate
        your own intervals directly.

        Returns an empty Stream if there are not at least two elements found by
        findConsecutiveNotes.

        >>> s1 = converter.parse("tinynotation: 3/4 c4 d' r b b'", makeNotation=False)
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/streamMelodicIntervals1.*
            :width: 246

        >>> intervalStream1 = s1.melodicIntervals()
        >>> intervalStream1.show('text')
        {1.0} <music21.interval.Interval M9>
        {4.0} <music21.interval.Interval P8>

        >>> M9 = intervalStream1[0]
        >>> M9.noteStart.nameWithOctave, M9.noteEnd.nameWithOctave
        ('C4', 'D5')

        Using the skip attributes from :meth:`~music21.stream.Stream.findConsecutiveNotes`,
        we can alter which intervals are reported:

        >>> intervalStream2 = s1.melodicIntervals(skipRests=True, skipOctaves=True)
        >>> intervalStream2.show('text')
        {1.0} <music21.interval.Interval M9>
        {2.0} <music21.interval.Interval m-3>

        >>> m3 = intervalStream2[1]
        >>> m3.directedNiceName
        'Descending Minor Third'
        '''
        returnList = self.findConsecutiveNotes(**skipKeywords)
        if len(returnList) < 2:
            return self.cloneEmpty(derivationMethod='melodicIntervals')

        returnStream = self.cloneEmpty(derivationMethod='melodicIntervals')
        for i in range(len(returnList) - 1):
            firstNote = returnList[i]
            secondNote = returnList[i + 1]
            # returnList could contain None to represent a rest
            if firstNote is None or secondNote is None:
                continue
            # Protect against empty chords
            if not (firstNote.pitches and secondNote.pitches):
                continue
            if chord.Chord in firstNote.classSet:
                noteStart = firstNote.notes[0]
            else:
                noteStart = firstNote
            if chord.Chord in secondNote.classSet:
                noteEnd = secondNote.notes[0]
            else:
                noteEnd = secondNote
            # Prefer Note objects over Pitch objects so that noteStart is set correctly
            returnInterval = interval.Interval(noteStart, noteEnd)
            returnInterval.offset = opFrac(firstNote.offset + firstNote.quarterLength)
            returnInterval.duration = duration.Duration(opFrac(
                secondNote.offset - returnInterval.offset))
            returnStream.insert(returnInterval)

        return returnStream

    # --------------------------------------------------------------------------
    def _getDurSpan(self, flatStream) -> list[tuple[OffsetQL, OffsetQL]]:
        '''
        Given a flat stream, create a list of the start and end
        times (as a tuple pair) of all elements in the Stream.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note(type='half'), [0, 1, 2, 3, 4])
        >>> a._getDurSpan(a.flatten())
        [(0.0, 2.0), (1.0, 3.0), (2.0, 4.0), (3.0, 5.0), (4.0, 6.0)]
        '''
        post = []
        for e in flatStream:
            dur = e.duration.quarterLength
            durSpan = (e.offset, opFrac(e.offset + dur))
            post.append(durSpan)
        # assume this is already sorted
        # index found here will be the same as elementsSorted
        return post

    def _durSpanOverlap(self, a, b, includeEndBoundary=False):
        '''
        Compare two durSpans and find overlaps; optionally,
        include coincident boundaries. a and b are sorted to permit any ordering.

        If an element ends at 3.0 and another starts at 3.0, this may or may not
        be considered an overlap. The includeCoincidentEnds parameter determines
        this behaviour, where ending and starting 3.0 being a type of overlap
        is set by the includeEndBoundary being True.


        >>> sc = stream.Stream()
        >>> sc._durSpanOverlap((0, 5), (4, 12), False)
        True
        >>> sc._durSpanOverlap((0, 10), (11, 12), False)
        False
        >>> sc._durSpanOverlap((11, 12), (0, 10), False)
        False
        >>> sc._durSpanOverlap((0, 3), (3, 6), False)
        False
        >>> sc._durSpanOverlap((0, 3), (3, 6), True)
        True
        '''
        durSpans = [a, b]
        # sorting will ensure that leading numbers are ordered from low to high
        durSpans.sort()
        found = False

        if includeEndBoundary:
            # if the start of "b" is before the end of "a"
            if durSpans[1][0] <= durSpans[0][1]:
                found = True
        else:  # do not include coincident boundaries
            if durSpans[1][0] < durSpans[0][1]:
                found = True
        return found

    def _findLayering(self) -> list[list[int]]:
        '''
        Find any elements in an elementsSorted list that have
        durations that cause overlaps.

        Returns a list of lists that has elements with overlaps,
        all index values that match are included in that list.

        See testOverlaps, in unit tests, for examples.

        Used in getOverlaps inside makeVoices.
        '''
        flatStream = self.flatten()
        if flatStream.isSorted is False:
            flatStream = flatStream.sorted()
        # these may not be sorted
        durSpanSorted = self._getDurSpan(flatStream)
        # According to the above comment, the spans may not be sorted.
        # So we sort them to be sure, but keep track of their original indices
        durSpanSortedIndex: list[tuple[int, OffsetQL]] = t.cast(
            list[tuple[int, OffsetQL]],
            list(enumerate(durSpanSorted))
        )
        durSpanSortedIndex.sort()

        # create a list with an entry for each element
        # in each entry, provide indices of all other elements that overlap
        overlapMap: list[list[int]] = [[] for dummy in range(len(durSpanSorted))]

        for i in range(len(durSpanSortedIndex)):
            src = durSpanSortedIndex[i]
            for j in range(i + 1, len(durSpanSortedIndex)):
                dst = durSpanSortedIndex[j]
                if self._durSpanOverlap(src[1], dst[1]):
                    overlapMap[src[0]].append(dst[0])
                    overlapMap[dst[0]].append(src[0])
                else:
                    break

        # Preserve exact same behaviour as earlier code.
        # It is unclear if anything depends on the individual lists being sorted.
        for ls in overlapMap:
            ls.sort()
        return overlapMap

    def _consolidateLayering(self, layeringMap):
        '''
        Given a stream of flat elements and a map of equal length with lists of
        index values that meet a given condition (overlap or simultaneities),
        organize into a dictionary by the relevant or first offset
        '''
        flatStream = self.flatten()
        if flatStream.isSorted is False:
            flatStream = flatStream.sorted()

        if len(layeringMap) != len(flatStream):
            raise StreamException('layeringMap must be the same length as flatStream')

        post = {}
        for i in range(len(layeringMap)):
            indices = layeringMap[i]
            if not indices:
                continue

            srcElementObj = flatStream[i]
            srcOffset = srcElementObj.offset
            dstOffset = None
            # check indices
            for j in indices:  # indices of other elements that overlap
                elementObj = flatStream[j]
                # Check if this object has been stored anywhere yet.
                # If so, use the offset of where it was stored before
                # to store the src element below
                store = True
                for k in post:
                    # this comparison needs to be based on object id, not
                    # matching equality
                    if id(elementObj) in [id(e) for e in post[k]]:
                        # if elementObj in post[key]:
                        store = False
                        dstOffset = k
                        break
                if dstOffset is None:
                    dstOffset = srcOffset
                if store:
                    if dstOffset not in post:
                        post[dstOffset] = []  # create dictionary entry
                    post[dstOffset].append(elementObj)

            # check if this object has been stored anywhere yet
            store = True
            for k in post:
                if id(srcElementObj) in [id(e) for e in post[k]]:
                    # if srcElementObj in post[key]:
                    store = False
                    break
            # dst offset may have been set when looking at indices
            if store:
                if dstOffset is None:
                    dstOffset = srcOffset
                if dstOffset not in post:
                    post[dstOffset] = []  # create dictionary entry
                post[dstOffset].append(srcElementObj)
        return post

    def findGaps(self):
        # noinspection PyShadowingNames
        '''
        Returns either (1) a Stream containing empty Music21Objects
        whose offsets and durations
        are the length of gaps in the Stream
        or (2) None if there are no gaps.

        N.B. there may be gaps in the flattened representation of the stream
        but not in the unflattened.  Hence why "isSequence" calls self.flatten().isGapless

        >>> s = stream.Stream()
        >>> s.insert(1.0, note.Note('E', type='half'))
        >>> s.insert(5.0, note.Note('F', type='whole'))
        >>> s.storeAtEnd(bar.Barline('final'))
        >>> gapStream = s.findGaps()
        >>> gapStream.show('text', addEndTimes=True)
        {0.0 - 1.0} <music21.note.Rest quarter>
        {3.0 - 5.0} <music21.note.Rest half>

        Returns None if not gaps:

        >>> s2 = stream.Stream()
        >>> s2.append(note.Note('G'))
        >>> s2.findGaps() is None
        True

        * Changed in v7: gapStream is filled with rests instead of Music21Objects
        '''
        if 'findGaps' in self._cache and self._cache['findGaps'] is not None:
            if self._cache['findGaps'] is False:
                # We are using False to represent the None that would be
                # returned by calling findGaps() on a gapless stream, because
                # None is music21's convention for forcing cache misses.
                return None
            return self._cache['findGaps']

        gapStream = self.cloneEmpty(derivationMethod='findGaps')

        highestCurrentEndTime = 0.0
        for e in self:
            eOffset = self.elementOffset(e, returnSpecial=True)
            if eOffset == OffsetSpecial.AT_END:
                break
            if eOffset > highestCurrentEndTime:
                gapElement = note.Rest()
                gapQuarterLength = opFrac(eOffset - highestCurrentEndTime)
                gapElement.duration.quarterLength = gapQuarterLength
                gapStream.insert(highestCurrentEndTime, gapElement, ignoreSort=True)
            eDur = e.duration.quarterLength
            highestCurrentEndTime = opFrac(max(highestCurrentEndTime, eOffset + eDur))

        # TODO: Is this even necessary, we do insert the elements in sorted order
        #     and the stream is empty at the start
        gapStream.sort()

        if not gapStream:
            self._cache['findGaps'] = False
            return None
        else:
            self._cache['findGaps'] = gapStream
            return gapStream

    @property
    def isGapless(self) -> bool:
        '''
        Returns True if there are no gaps between the lowest offset and the highest time.
        Otherwise returns False

        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> s.append(note.Note('D'))
        >>> s.isGapless
        True
        >>> s.insert(10.0, note.Note('E'))
        >>> s.isGapless
        False

        OMIT_FROM_DOCS

        Test cache:

        >>> s.isGapless
        False
        '''
        if 'isGapless' in self._cache and self._cache['isGapless'] is not None:
            return self._cache['isGapless']
        else:
            if self.findGaps() is None:
                self._cache['isGapless'] = True
                return True
            else:
                self._cache['isGapless'] = False
                return False

    def getOverlaps(self):
        '''
        Find any elements that overlap. Overlapping might include elements
        that have zero-length duration simultaneous.

        This method returns a dictionary, where keys
        are the start time of the first overlap and
        value are a list of all objects included in
        that overlap group.

        This example demonstrates that end-joining overlaps do not count.

        >>> a = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('quarter')
        ...     n.offset = x * 1
        ...     a.insert(n)
        ...
        >>> d = a.getOverlaps()
        >>> len(d)
        0

        Notes starting at the same time overlap:

        >>> a = stream.Stream()
        >>> for x in [0, 0, 0, 0, 13, 13, 13]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('half')
        ...     n.offset = x
        ...     a.insert(n)
        ...
        >>> d = a.getOverlaps()
        >>> len(d[0])
        4
        >>> len(d[13])
        3
        >>> a = stream.Stream()
        >>> for x in [0, 0, 0, 0, 3, 3, 3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     n.offset = x
        ...     a.insert(n)
        ...

        Default is to not include coincident boundaries

        >>> d = a.getOverlaps()
        >>> len(d[0])
        7

        '''
        overlapMap = self._findLayering()
        # environLocal.printDebug(['overlapMap', overlapMap])

        return self._consolidateLayering(overlapMap)

    def isSequence(self) -> bool:
        '''
        A stream is a sequence if it has no overlaps.

        >>> a = stream.Stream()
        >>> for x in [0, 0, 0, 0, 3, 3, 3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     n.offset = x * 1
        ...     a.insert(n)
        ...
        >>> a.isSequence()
        False

        OMIT_FROM_DOCS

        TODO: check that co-incident boundaries are properly handled

        >>> a = stream.Stream()
        >>> for x in [0, 4, 8.0]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     a.append(n)
        ...
        >>> a.isSequence()
        True
        '''
        overlapMap = self._findLayering()
        post = True
        for indexList in overlapMap:
            if indexList:
                post = False
                break
        return post

    # --------------------------------------------------------------------------
    # routines for dealing with relationships to other streams.
    # Formerly in twoStreams.py

    def simultaneousAttacks(self, stream2):
        '''
        returns an ordered list of offsets where elements are started (attacked)
        at the same time in both self and stream2.

        In this example, we create one stream of Qtr, Half, Qtr, and one of Half, Qtr, Qtr.
        There are simultaneous attacks at offset 0.0 (the beginning) and at offset 3.0,
        but not at 1.0 or 2.0:


        >>> st1 = stream.Stream()
        >>> st2 = stream.Stream()
        >>> st1.append([note.Note(type='quarter'),
        ...             note.Note(type='half'),
        ...             note.Note(type='quarter')])
        >>> st2.append([note.Note(type='half'),
        ...             note.Note(type='quarter'),
        ...             note.Note(type='quarter')])
        >>> print(st1.simultaneousAttacks(st2))
        [0.0, 3.0]
        '''
        stream1Offsets = iterator.OffsetIterator(self)
        stream2Offsets = iterator.OffsetIterator(stream2)

        returnKey = {}

        for thisList in stream1Offsets:
            thisOffset = self.elementOffset(thisList[0])
            returnKey[thisOffset] = 1

        for thatList in stream2Offsets:
            thatOffset = thatList[0].getOffsetBySite(stream2)
            if thatOffset in returnKey:
                returnKey[thatOffset] += 1

        returnList = []
        for foundOffset in sorted(returnKey):
            if returnKey[foundOffset] >= 2:
                returnList.append(foundOffset)
        return returnList

        # this method was supposed to be faster, but actually 2000 times slower on op133

        # sOuter = Stream()
        # for e in self:
        #     sOuter.coreInsert(e.offset, e)
        # for e in stream2:
        #     sOuter.coreInsert(e.offset, e)
        # sOuter.coreElementsChanged(updateIsFlat=False)
        # sOuterTree = sOuter.asTree(flatten=False, groupOffsets=True)
        # return sorted(sOuterTree.simultaneityDict().keys())

    def attachIntervalsBetweenStreams(self, cmpStream):
        # noinspection PyShadowingNames
        '''
        For each element in self, creates an interval.Interval object in the element's
        editorial that is the interval between it and the element in cmpStream that
        is sounding at the moment the element in srcStream is attacked.

        Remember that if you are comparing two streams with measures, etc.,
        you'll need to flatten each stream as follows:

        >>> #_DOCS_SHOW stream1.flatten().attachIntervalsBetweenStreams(stream2.flatten())

        Example usage:

        >>> s1 = converter.parse('tinynotation: 7/4 C4 d8 e f# g A2 d2', makeNotation=False)
        >>> s2 = converter.parse('tinynotation: 7/4 g4 e8 d c4   a2 r2', makeNotation=False)
        >>> s1.attachIntervalsBetweenStreams(s2)
        >>> for n in s1.notes:
        ...     if n.editorial.harmonicInterval is None:
        ...         print('None')  # if other voice had a rest...
        ...     else:
        ...         print(n.editorial.harmonicInterval.directedName)
        P12
        M2
        M-2
        A-4
        P-5
        P8
        None
        '''
        # TODO: this can be replaced by two different O(n) iterators, without
        #   an O(n*2) lookup.
        for n in self.getElementsByClass(note.Note):
            # clear any previous result
            n.editorial.harmonicInterval = None
            # get simultaneous elements from other stream
            simultEls = cmpStream.getElementsByOffset(self.elementOffset(n),
                                                      mustBeginInSpan=False,
                                                      mustFinishInSpan=False)
            for simultNote in simultEls.getElementsByClass(note.Note):
                interval1 = None
                try:
                    interval1 = interval.Interval(n, simultNote)
                    interval1.intervalType = 'harmonic'
                    n.editorial.harmonicInterval = interval1
                except exceptions21.Music21Exception:
                    pass
                if interval1 is not None:
                    break  # inner loop

    def attachMelodicIntervals(self):
        '''
        For each element in self, creates an interval.Interval object in the element's
        editorial that is the interval between it and the previous element in the stream. Thus,
        the first element will have a value of None.

        DEPRECATED sometime soon.  A replacement to come presently.

        >>> s1 = converter.parse('tinyNotation: 7/4 C4 d8 e f# g A2 d2', makeNotation=False)
        >>> s1.attachMelodicIntervals()
        >>> for n in s1.notes:
        ...     if n.editorial.melodicInterval is None:
        ...         print('None')
        ...     else:
        ...         print(n.editorial.melodicInterval.directedName)
        None
        M9
        M2
        M2
        m2
        m-7
        P4

        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> s.append(note.Note('D'))
        >>> s.append(note.Rest(quarterLength=4.0))
        >>> s.append(note.Note('D'))
        >>> s.attachMelodicIntervals()
        >>> for n in s.notes:
        ...     if n.editorial.melodicInterval is None:
        ...         print('None')  # if other voice had a rest...
        ...     else:
        ...         print(n.editorial.melodicInterval.directedName)
        None
        M2
        P1
        '''

        notes = self.notes.stream()
        currentObject = notes[0]
        previousObject = None
        while currentObject is not None:
            if (previousObject is not None
                    and isinstance(currentObject, note.Note)
                    and isinstance(previousObject, note.Note)):
                melodicInterval = interval.Interval(previousObject, currentObject)
                melodicInterval.intervalType = 'melodic'
                currentObject.editorial.melodicInterval = melodicInterval
            previousObject = currentObject
            currentObject = currentObject.next()

    def playingWhenAttacked(self, el, elStream=None):
        '''
        Given an element (from another Stream) returns the single element
        in this Stream that is sounding while the given element starts.

        If there are multiple elements sounding at the moment it is
        attacked, the method returns the first element of the same class
        as this element, if any. If no element
        is of the same class, then the first element encountered is
        returned. For more complex usages, use allPlayingWhileSounding.

        Returns None if no elements fit the bill.

        The optional elStream is the stream in which el is found.
        If provided, el's offset
        in that Stream is used.  Otherwise, the current offset in
        el is used.  It is just
        in case you are paranoid that el.offset might not be what
        you want, because of some fancy manipulation of
        el.activeSite

        >>> n1 = note.Note('G#')
        >>> n2 = note.Note('D#')
        >>> s1 = stream.Stream()
        >>> s1.insert(20.0, n1)
        >>> s1.insert(21.0, n2)

        >>> n3 = note.Note('C#')
        >>> s2 = stream.Stream()
        >>> s2.insert(20.0, n3)
        >>> s1.playingWhenAttacked(n3)
        <music21.note.Note G#>

        >>> n3.setOffsetBySite(s2, 20.5)
        >>> s1.playingWhenAttacked(n3)
        <music21.note.Note G#>

        >>> n3.setOffsetBySite(s2, 21.0)
        >>> n3.offset
        21.0
        >>> s1.playingWhenAttacked(n3)
        <music21.note.Note D#>

        If there is more than one item at the same time in the other stream
        then the first item matching the same class is returned, even if
        another element has a closer offset.

        >>> n3.setOffsetBySite(s2, 20.5)
        >>> s1.insert(20.5, clef.BassClef())
        >>> s1.playingWhenAttacked(n3)
        <music21.note.Note G#>
        >>> fc = clef.FClef()  # superclass of BassClef
        >>> s2.insert(20.5, fc)
        >>> s1.playingWhenAttacked(fc)
        <music21.clef.BassClef>

        But since clefs have zero duration, moving the FClef ever so slightly
        will find the note instead

        >>> fc.setOffsetBySite(s2, 20.6)
        >>> s1.playingWhenAttacked(fc)
        <music21.note.Note G#>


        Optionally, specify the site to get the offset from:

        >>> n3.setOffsetBySite(s2, 21.0)
        >>> n3.setOffsetBySite(None, 100)
        >>> n3.activeSite = None
        >>> s1.playingWhenAttacked(n3) is None
        True
        >>> s1.playingWhenAttacked(n3, s2).name
        'D#'
        '''
        if elStream is not None:  # a bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset

        otherElements = self.getElementsByOffset(elOffset, mustBeginInSpan=False)
        if not otherElements:
            return None
        elif len(otherElements) == 1:
            return otherElements[0]
        else:
            for thisEl in otherElements:
                if isinstance(thisEl, el.__class__):
                    return thisEl
            return otherElements[0]

    def allPlayingWhileSounding(self, el, elStream=None):
        '''
        Returns a new Stream of elements in this stream that sound
        at the same time as `el`, an element presumably in another Stream.

        The offset of this new Stream is set to el's offset, while the
        offset of elements within the Stream are adjusted relative to
        their position with respect to the start of el.  Thus, a note
        that is sounding already when el begins would have a negative
        offset.  The duration of otherStream is forced
        to be the length of el -- thus a note sustained after el ends
        may have a release time beyond that of the duration of the Stream.

        As above, elStream is an optional Stream to look up el's offset in.  Use
        this to work on an element in another part.

        The method always returns a Stream, but it might be an empty Stream.

        OMIT_FROM_DOCS
        TODO: write: requireClass:
        Takes as an optional parameter "requireClass".  If this parameter
        is boolean True then only elements
        of the same class as el are added to the new Stream.  If requireClass
        is list, it is used like
        classList in elsewhere in stream to provide a list of classes that the
        el must be a part of.

        '''
        if elStream is not None:  # a bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset
        elEnd = elOffset + el.quarterLength

        if elEnd != elOffset:  # i.e. not zero length
            otherElements = self.getElementsByOffset(
                elOffset,
                elEnd,
                mustBeginInSpan=False,
                includeEndBoundary=False,
                includeElementsThatEndAtStart=False).stream()
        else:
            otherElements = self.getElementsByOffset(elOffset,
                                                     mustBeginInSpan=False).stream()

        otherElements.offset = elOffset
        otherElements.quarterLength = el.quarterLength
        for thisEl in otherElements:
            thisEl.offset = thisEl.offset - elOffset

        return otherElements

    # --------------------------------------------------------------------------
    # voice processing routines

    def makeVoices(self, *, inPlace=False, fillGaps=True):
        '''
        If this Stream has overlapping Notes or Chords, this method will isolate
        all overlaps in unique Voices, and place those Voices in the Stream.

        >>> s = stream.Stream()
        >>> s.insert(0, note.Note('C4', quarterLength=4))
        >>> s.repeatInsert(note.Note('b-4', quarterLength=0.5), [x * 0.5 for x in list(range(8))])
        >>> s.makeVoices(inPlace=True)
        >>> len(s.voices)
        2
        >>> [n.pitch for n in s.voices[0].notes]
        [<music21.pitch.Pitch C4>]
        >>> [str(n.pitch) for n in s.voices[1].notes]
        ['B-4', 'B-4', 'B-4', 'B-4', 'B-4', 'B-4', 'B-4', 'B-4']

        * Changed in v7: if `fillGaps=True` and called on an incomplete measure,
          makes trailing rests in voices. This scenario occurs when parsing MIDI.
        '''
        # this method may not always
        # produce the optimal voice assignment based on context (register
        # chord formation, etc
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('makeVoices')
        else:
            returnObj = self
        # must be sorted
        if not returnObj.isSorted:
            returnObj.sort()
        olDict = returnObj.notes.stream().getOverlaps()
        # environLocal.printDebug(['makeVoices(): olDict', olDict])
        # find the max necessary voices by finding the max number
        # of elements in each group; these may not all be necessary
        maxVoiceCount = 1
        for group in olDict.values():
            if len(group) > maxVoiceCount:
                maxVoiceCount = len(group)
        if maxVoiceCount == 1:  # nothing to do here
            if not inPlace:
                return returnObj
            return None

        # store all voices in a list
        voices = []
        for dummy in range(maxVoiceCount):
            voices.append(Voice())  # add voice classes

        # iterate through all elements; if not in an overlap, place in
        # voice 1, otherwise, distribute
        for e in returnObj.notes:
            o = e.getOffsetBySite(returnObj)
            # cannot match here by offset, as olDict keys are representative
            # of the first overlapped offset, not all contained offsets
            # if o not in olDict:  # place in a first voices
            #    voices[0].insert(o, e)
            # find a voice to place in
            # as elements are sorted, can use the highest time
            # else:
            for v in voices:
                if v.highestTime <= o:
                    v.insert(o, e)
                    break
            # remove from source
            returnObj.remove(e)
        # remove any unused voices (possible if overlap group has sus)
        for v in voices:
            if v:  # skip empty voices
                returnObj.insert(0, v)
        if fillGaps:
            returnObj.makeRests(fillGaps=True,
                                inPlace=True,
                                timeRangeFromBarDuration=True,
                                )
        # remove rests in returnObj
        returnObj.removeByClass('Rest')
        # elements changed will already have been called
        if not inPlace:
            return returnObj

    def _maxVoiceCount(self, *, countById=False) -> int | tuple[int, list[str]]:
        '''
        Returns the maximum number of voices in a part.  Used by voicesToParts.
        Minimum returned is 1.  If `countById` is True, returns a tuple of
        (maxVoiceCount, voiceIdList)

        >>> import copy

        >>> p0 = stream.Part()
        >>> p0._maxVoiceCount()
        1
        >>> v0 = stream.Voice(id='v0')
        >>> p0.insert(0, v0)
        >>> p0._maxVoiceCount()
        1
        >>> v1 = stream.Voice(id='v1')
        >>> p0.insert(0, v1)
        >>> p0._maxVoiceCount()
        2

        >>> p1 = stream.Part()
        >>> m1 = stream.Measure(number=1)
        >>> p1.insert(0, m1)
        >>> p1._maxVoiceCount()
        1
        >>> m1.insert(0, v0)
        >>> p1._maxVoiceCount()
        1
        >>> m1.insert(0, v1)
        >>> p1._maxVoiceCount()
        2
        >>> m2 = stream.Measure(number=2)
        >>> p1.append(m2)
        >>> p1._maxVoiceCount()
        2
        >>> v01 = copy.copy(v0)
        >>> v11 = stream.Voice(id='v11')
        >>> m2.insert(0, v01)
        >>> m2.insert(0, v11)
        >>> p1._maxVoiceCount()
        2
        >>> v2 = stream.Voice(id='v2')
        >>> m2.insert(0, v2)
        >>> p1._maxVoiceCount()
        3

        If `countById` is True then different voice ids create different parts.

        >>> mvc, vIds = p1._maxVoiceCount(countById=True)
        >>> mvc
        4
        >>> vIds
        ['v0', 'v1', 'v11', 'v2']

        >>> v01.id = 'v01'
        >>> mvc, vIds = p1._maxVoiceCount(countById=True)
        >>> mvc
        5
        >>> vIds
        ['v0', 'v1', 'v01', 'v11', 'v2']
        '''
        voiceCount = 1
        voiceIds = []

        if self.hasMeasures():
            for m in self.getElementsByClass(Measure):
                mVoices = m.voices
                mVCount = len(mVoices)
                if not countById:
                    voiceCount = max(mVCount, voiceCount)
                else:
                    for v in mVoices:
                        if v.id not in voiceIds:
                            voiceIds.append(v.id)

        elif self.hasVoices():
            voices = self.voices
            if not countById:
                voiceCount = len(voices)
            else:
                voiceIds = [v.id for v in voices]
        else:  # if no measure or voices, get one part
            voiceCount = 1

        voiceCount = max(voiceCount, len(voiceIds))

        if not countById:
            return voiceCount
        else:
            return voiceCount, voiceIds

    def voicesToParts(self, *, separateById=False):
        # noinspection PyShadowingNames
        '''
        If this Stream defines one or more voices,
        extract each into a Part, returning a Score.

        If this Stream has no voices, return the Stream as a Part within a Score.

        >>> c = corpus.parse('demos/two-voices')
        >>> c.show('t')
        {0.0} <music21.text.TextBox 'Music21 Fr...'>
        {0.0} <music21.text.TextBox 'Music21'>
        {0.0} <music21.metadata.Metadata object at 0x109ce1630>
        {0.0} <music21.stream.Part Piano>
            {0.0} <music21.instrument.Instrument 'P1: Piano: '>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.layout.PageLayout>
                {0.0} <music21.layout.SystemLayout>
                ...
                {0.0} <music21.clef.BassClef>
                {0.0} <music21.key.Key of D major>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.stream.Voice 3>
                    {0.0} <music21.note.Note E>
                    ...
                    {3.0} <music21.note.Rest quarter>
                {0.0} <music21.stream.Voice 4>
                    {0.0} <music21.note.Note F#>
                    ...
                    {3.5} <music21.note.Note B>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.stream.Voice 3>
                    {0.0} <music21.note.Note E>
                    ...
                    {3.0} <music21.note.Rest quarter>
                {0.0} <music21.stream.Voice 4>
                    {0.0} <music21.note.Note E>
                    ...
                    {3.5} <music21.note.Note A>
            {8.0} <music21.stream.Measure 3 offset=8.0>
                {0.0} <music21.note.Rest whole>
                {4.0} <music21.bar.Barline type=final>
        {0.0} <music21.layout.ScoreLayout>

        >>> ce = c.voicesToParts()
        >>> ce.show('t')
        {0.0} <music21.stream.Part Piano-v0>
            {0.0} <music21.instrument.Instrument 'P1: Piano: '>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.TrebleClef>
                {0.0} <music21.key.Key of D major>
                {0.0} <music21.meter.TimeSignature 4/4>
                {0.0} <music21.note.Note E>
                ...
                {3.0} <music21.note.Rest quarter>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note E>
                ...
                {3.0} <music21.note.Rest quarter>
            {8.0} <music21.stream.Measure 3 offset=8.0>
                {0.0} <music21.note.Rest whole>
                {4.0} <music21.bar.Barline type=final>
        {0.0} <music21.stream.Part Piano-v1>
            {0.0} <music21.instrument.Instrument 'P1: Piano: '>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.clef.BassClef>
                {0.0} <music21.key.Key of D major>
                ...
                {3.5} <music21.note.Note B>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note E>
                ...
                {3.5} <music21.note.Note A>
            {8.0} <music21.stream.Measure 3 offset=8.0>
                {0.0} <music21.bar.Barline type=final>
        <BLANKLINE>

        If `separateById` is True then all voices with the same id
        will be connected to the same Part, regardless of order
        they appear in the measure.

        Compare the previous output:

        >>> p0pitches = ce.parts[0].pitches
        >>> p1pitches = ce.parts[1].pitches
        >>> ' '.join([p.nameWithOctave for p in p0pitches])
        'E4 D#4 D#4 E4 F#4 E4 B3 B3 E4 E4'
        >>> ' '.join([p.nameWithOctave for p in p1pitches])
        'F#2 F#3 E3 E2 D#2 D#3 B2 B3 E2 E3 D3 D2 C#2 C#3 A2 A3'

        Swap voice ids in first measure:

        >>> m0 = c.parts[0].getElementsByClass(stream.Measure).first()
        >>> m0.voices[0].id, m0.voices[1].id
        ('3', '4')
        >>> m0.voices[0].id = '4'
        >>> m0.voices[1].id = '3'

        Now run voicesToParts with `separateById=True`

        >>> ce = c.voicesToParts(separateById=True)
        >>> p0pitches = ce.parts[0].pitches
        >>> p1pitches = ce.parts[1].pitches
        >>> ' '.join([p.nameWithOctave for p in p0pitches])
        'E4 D#4 D#4 E4 F#4 E2 E3 D3 D2 C#2 C#3 A2 A3'
        >>> ' '.join([p.nameWithOctave for p in p1pitches])
        'F#2 F#3 E3 E2 D#2 D#3 B2 B3 E4 B3 B3 E4 E4'

        Note that the second and subsequent measure's pitches were changed
        not the first, because separateById aligns the voices according to
        order first encountered, not by sorting the Ids.
        '''
        s = Score()
        # s.metadata = self.metadata

        # if this is a Score, call this recursively on each Part, then
        # add all parts to one Score
        if self.hasPartLikeStreams():
            # part-like does not necessarily mean .parts
            for p in self.getElementsByClass(Stream):
                sSub = p.voicesToParts(separateById=separateById)
                for pSub in sSub:
                    s.insert(0, pSub)
            return s

        # need to find maximum voice count
        mvcReturn = self._maxVoiceCount(countById=separateById)
        if not separateById:
            partCount = mvcReturn
            voiceIds = []
        else:
            partCount, voiceIds = mvcReturn

        # environLocal.printDebug(['voicesToParts(): got partCount', partCount])

        # create parts, naming ids by voice id?
        partDict = {}

        for i in range(partCount):
            p = Part()
            s.insert(0, p)
            if not separateById:
                p.id = str(self.id) + '-v' + str(i)
                partDict[i] = p
            else:
                voiceId = voiceIds[i]
                p.id = str(self.id) + '-' + str(voiceId)
                partDict[voiceId] = p

        def doOneMeasureWithVoices(mInner):
            '''
            This is the main routine for dealing with the most common
            and most difficult voice set.
            '''
            mActive = Measure()
            mActive.mergeAttributes(mInner)  # get groups, optional id
            # merge everything except Voices; this will get
            # clefs
            mActive.mergeElements(
                mInner,
                classFilterList=(
                    'Barline', 'TimeSignature', 'Clef', 'KeySignature',
                )
            )

            # vIndexInner = 0 should not be necessary, but pylint warns on loop variables
            # that could possibly be undefined used out of the loop.
            vIndexInner = 0

            seenIdsThisMeasure = set()
            for vIndexInner, vInner in enumerate(mInner.voices):
                # TODO(msc): fix bugs if same voice id appears twice in same measure

                # make an independent copy
                mNewInner = copy.deepcopy(mActive)
                # merge all elements from the voice
                mNewInner.mergeElements(vInner)
                # insert in the appropriate part
                vId = vInner.id
                if not separateById:
                    pInner = partDict[vIndexInner]
                else:
                    seenIdsThisMeasure.add(vId)
                    pInner = partDict[vId]
                pInner.insert(self.elementOffset(mInner), mNewInner)

            # vIndexInner is now the number of voices - 1.  Fill empty voices
            if not separateById:
                for emptyIndex in range(vIndexInner + 1, partCount):
                    pInner = partDict[emptyIndex]
                    pInner.insert(self.elementOffset(mInner), copy.deepcopy(mActive))
            else:
                for voiceIdInner in partDict:
                    if voiceIdInner in seenIdsThisMeasure:
                        continue
                    pInner = partDict[voiceIdInner]
                    pInner.insert(self.elementOffset(mInner), copy.deepcopy(mActive))

        # Place references to any instruments from the original part into the new parts
        for p in s.parts:
            p.mergeElements(self, classFilterList=('Instrument',))

        if self.hasMeasures():
            for m in self.getElementsByClass(Measure):
                if m.hasVoices():
                    doOneMeasureWithVoices(m)
                # if a measure does not have voices, simply populate
                # with elements and append
                else:
                    mNew = Measure()
                    mNew.mergeAttributes(m)  # get groups, optional id
                    # get all elements
                    mNew.mergeElements(m)
                    # always place in top-part
                    s.parts[0].insert(self.elementOffset(m), mNew)
                    for i in range(1, partCount):
                        mEmpty = Measure()
                        mEmpty.mergeAttributes(m)
                        # Propagate bar, meter, key elements to lower parts
                        mEmpty.mergeElements(m, classFilterList=('Barline',
                                            'TimeSignature', 'KeySignature'))
                        s.parts[i].insert(self.elementOffset(m), mEmpty)
        # if part has no measures but has voices, contents of each voice go into the part
        elif self.hasVoices():
            for vIndex, v in enumerate(self.voices):
                s.parts[vIndex].mergeElements(v)
        # if just a Stream of elements, add to a part
        else:
            s.parts[0].mergeElements(self)

        # there is no way to assure proper clef information, so using
        # the best clef here is desirable.
        for p in s.parts:
            # only add clef if measures are defined; otherwise, assume
            # the best clef will be assigned later
            if p.hasMeasures():
                # place in first measure
                p.getElementsByClass(Measure).first().clef = clef.bestClef(p, recurse=True)
        return s

    def explode(self):
        '''
        Create a multiple Part representation from a single polyphonic Part.

        Currently just runs :meth:`~music21.stream.Stream.voicesToParts`
        but that will change as part explosion develops, and this
        method will use our best available quick method for part
        extraction.
        '''
        return self.voicesToParts()

    def flattenUnnecessaryVoices(self, *, force=False, inPlace=False):
        '''
        If this Stream defines one or more internal voices, do the following:

        * If there is more than one voice, and a voice has no elements,
          remove that voice.
        * If there is only one voice left that has elements, place those
          elements in the parent Stream.
        * If `force` is True, even if there is more than one Voice left,
          all voices will be flattened.

        This leaves a stream where all voices appear when another appears in
        the same measure.

        More demonstrations of `recurse=True`:

        >>> s = stream.Stream(note.Note())
        >>> s.insert(0, note.Note())
        >>> s.insert(0, note.Note())
        >>> s.makeVoices(inPlace=True)
        >>> len(s.voices)
        3

        >>> s.remove(s.voices[1].notes[0], recurse=True)
        >>> s.remove(s.voices[2].notes[0], recurse=True)
        >>> voicesFlattened = s.flattenUnnecessaryVoices()
        >>> len(voicesFlattened.voices)
        0

        * Changed in v5: inPlace is default False and a keyword only arg.
        '''
        if not self.voices:
            return None  # do not make copy; return immediately

        if not inPlace:  # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # collect voices for removal and for flattening
        remove = []
        flatten = []
        for v in returnObj.voices:
            if not v:  # might add other criteria
                remove.append(v)
            else:
                flatten.append(v)

        for v in remove:
            returnObj.remove(v)

        if len(flatten) == 1 or force:  # always flatten 1
            for v in flatten:  # usually one unless force
                # get offset of voice in returnObj
                shiftOffset = v.getOffsetBySite(returnObj)
                for e in v.elements:
                    # insert shift + offset w/ voice
                    returnObj.coreInsert(shiftOffset + e.getOffsetBySite(v), e)
                returnObj.remove(v)
            returnObj.coreElementsChanged()

        if not inPlace:
            return returnObj
        else:
            return None

    # --------------------------------------------------------------------------
    # Lyric control
    # might be overwritten in base.splitAtDurations, but covered with a check
    # pylint: disable=method-hidden
    def lyrics(
        self,
        ignoreBarlines: bool = True,
        recurse: bool = False,
        skipTies: bool = False,
    ) -> dict[int, list[RecursiveLyricList]]:
        # noinspection PyShadowingNames
        '''
        Returns a dict of lists of lyric objects (with the keys being
        the lyric numbers) found in self. Each list will have an element for each
        note in the stream (which may be a note.Lyric() or None).
        By default, this method automatically
        recurses through measures, but not other container streams.


        >>> s = converter.parse('tinynotation: 4/4 a4 b c d   e f g a', makeNotation=False)
        >>> someLyrics = ['this', 'is', 'a', 'list', 'of', 'eight', 'lyric', 'words']
        >>> for n, lyric in zip(s.notes, someLyrics):
        ...     n.lyric = lyric


        >>> s.lyrics()
        {1: [<music21.note.Lyric number=1 syllabic=single text='this'>, ...,
             <music21.note.Lyric number=1 syllabic=single text='words'>]}

        >>> s.notes[3].lyric = None
        >>> s.lyrics()[1]
        [<music21.note.Lyric number=1 syllabic=single text='this'>, ..., None, ...,
         <music21.note.Lyric number=1 syllabic=single text='words'>]

        If ignoreBarlines is True, it will behave as if the elements in measures are all
        in a flattened stream (note that this is not stream.flatten()
        as it does not copy the elements)
        together without measure containers. This means that even if recurse is
        False, lyrics() will still essentially recurse through measures.

        >>> s.makeMeasures(inPlace=True)
        >>> s.lyrics()[1]
        [<music21.note.Lyric number=1 syllabic=single text='this'>, ..., None, ...,
         <music21.note.Lyric number=1 syllabic=single text='words'>]

        >>> list(s.lyrics(ignoreBarlines=False).keys())
        []

        If recurse is True, this method will recurse through all container streams and
        build a nested list structure mirroring the hierarchy of the stream.
        Note that if ignoreBarlines is True, measure structure will not be reflected
        in the hierarchy, although if ignoreBarlines is False, it will.

        Note that streams which do not contain any instance of a lyric number will not
        appear anywhere in the final list (not as a [] or otherwise).

        >>> scr = stream.Score(s)

        >>> scr.lyrics(ignoreBarlines=False, recurse=True)[1]
        [[[<music21.note.Lyric number=1 syllabic=single text='this'>, <...'is'>, <...'a'>, None],
          [<...'of'>, <...'eight'>, <...'lyric'>, <...'words'>]]]

        Notice that the measures are nested in the part which is nested in the score.

        >>> scr.lyrics(ignoreBarlines=True, recurse=True)[1]
        [[<music21.note.Lyric number=1 syllabic=single text='this'>, <...'is'>, <...'a'>, None,
          <...'of'>, <...'eight'>, <...'lyric'>, <...'words'>]]

        Notice that this time, the measure structure is ignored.

        >>> list(scr.lyrics(ignoreBarlines=True, recurse=False).keys())
        []

        '''
        returnLists: dict[int, list[RecursiveLyricList]] = {}
        numNotes = 0

        # --------------------

        # noinspection PyShadowingNames
        def appendLyricsFromNote(
            n: note.NotRest,
            inner_returnLists: dict[int, list[RecursiveLyricList]],
            numNonesToAppend: int
        ):
            if not n.lyrics:
                for k in inner_returnLists:
                    inner_returnLists[k].append(None)
                return

            addLyricNums = []
            for ly in n.lyrics:
                if ly.number not in inner_returnLists:
                    inner_returnLists[ly.number] = [None for dummy in range(numNonesToAppend)]
                inner_returnLists[ly.number].append(ly)
                addLyricNums.append(ly.number)
            for k in inner_returnLists:
                if k not in addLyricNums:
                    inner_returnLists[k].append(None)

        # -----------------------
        # TODO: use new recurse
        for e in self:
            if ignoreBarlines is True and isinstance(e, Measure):
                m = e
                for n in m.notes:
                    if skipTies is True:
                        if n.tie is None or n.tie.type == 'start':
                            appendLyricsFromNote(n, returnLists, numNotes)
                            numNotes += 1
                        else:
                            pass  # do nothing if end tie and skipTies is True
                    else:
                        appendLyricsFromNote(n, returnLists, numNotes)
                        numNotes += 1

            elif recurse is True and isinstance(e, Stream):
                sublists = e.lyrics(ignoreBarlines=ignoreBarlines, recurse=True, skipTies=skipTies)
                for k in sublists:
                    if k not in returnLists:
                        returnLists[k] = []
                    returnLists[k].append(sublists[k])
            elif isinstance(e, note.NotRest):
                if skipTies is True:
                    if e.tie is None or e.tie.type == 'start':
                        appendLyricsFromNote(e, returnLists, numNotes)
                        numNotes += 1
                    else:
                        pass  # do nothing if end tie and skipTies is True
                else:
                    appendLyricsFromNote(e, returnLists, numNotes)
                    numNotes += 1
            else:
                # e is a stream
                # (could be a measure if ignoreBarlines is False) and recurse is False
                pass  # do nothing

        return returnLists


    # ---- Variant Activation Methods
    def activateVariants(self, group=None, *, matchBySpan=True, inPlace=False):
        '''
        For any :class:`~music21.variant.Variant` objects defined in this Stream
        (or selected by matching the `group` parameter),
        replace elements defined in the Variant with those in the calling Stream.
        Elements replaced will be gathered into a new Variant
        given the group 'default'. If a variant is activated with
        .replacementDuration different from its length, the appropriate elements
        in the stream will have their offsets shifted, and measure numbering
        will be fixed. If matchBySpan is True, variants with lengthType
        'replacement' will replace all the elements in the
        replacement region of comparable class. If matchBySpan is False,
        elements will be swapped in when a match is found between an element
        in the variant and an element in the replacement region of the string.

        >>> sStr   = 'd4 e4 f4 g4   a2 b-4 a4    g4 a8 g8 f4 e4    d2 a2              '
        >>> v1Str  = '              a2. b-8 a8 '
        >>> v2Str1 = '                                             d4 f4 a2 '
        >>> v2Str2 = '                                                      d4 f4 AA2 '

        >>> sStr += "d4 e4 f4 g4    a2 b-4 a4    g4 a8 b-8 c'4 c4    f1"

        >>> s = converter.parse('tinynotation: 4/4 ' + sStr, makeNotation=False)
        >>> s.makeMeasures(inPlace=True)  # maybe not necessary?
        >>> v1stream = converter.parse('tinynotation: 4/4 ' + v1Str, makeNotation=False)
        >>> v2stream1 = converter.parse('tinynotation: 4/4 ' + v2Str1, makeNotation=False)
        >>> v2stream2 = converter.parse('tinynotation: 4/4 ' + v2Str2, makeNotation=False)


        >>> v1 = variant.Variant()
        >>> v1measure = stream.Measure()
        >>> v1.insert(0.0, v1measure)
        >>> for e in v1stream.notesAndRests:
        ...    v1measure.insert(e.offset, e)

        >>> v2 = variant.Variant()
        >>> v2.replacementDuration = 4.0
        >>> v2measure1 = stream.Measure()
        >>> v2measure2 = stream.Measure()
        >>> v2.insert(0.0, v2measure1)
        >>> v2.insert(4.0, v2measure2)
        >>> for e in v2stream1.notesAndRests:
        ...    v2measure1.insert(e.offset, e)
        >>> for e in v2stream2.notesAndRests:
        ...    v2measure2.insert(e.offset, e)

        >>> v3 = variant.Variant()
        >>> v3.replacementDuration = 4.0
        >>> v1.groups = ['docVariants']
        >>> v2.groups = ['docVariants']
        >>> v3.groups = ['docVariants']

        >>> s.insert(4.0, v1)   # replacement variant
        >>> s.insert(12.0, v2)  # insertion variant (2 bars replace 1 bar)
        >>> s.insert(20.0, v3)  # deletion variant (0 bars replace 1 bar)
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {12.0} <music21.variant.Variant object of length 8.0>
        {12.0} <music21.stream.Measure 4 offset=12.0>
            {0.0} <music21.note.Note D>
            {2.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 5 offset=16.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {20.0} <music21.variant.Variant object of length 0.0>
        {20.0} <music21.stream.Measure 6 offset=20.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {24.0} <music21.stream.Measure 7 offset=24.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note B->
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note C>
        {28.0} <music21.stream.Measure 8 offset=28.0>
            {0.0} <music21.note.Note F>
            {4.0} <music21.bar.Barline type=final>

        >>> docVariant = s.activateVariants('docVariants')

        >>> #_DOCS_SHOW s.show()

        .. image:: images/stream_activateVariants1.*
            :width: 600

        >>> #_DOCS_SHOW docVariant.show()

        .. image:: images/stream_activateVariants2.*
            :width: 600

        >>> docVariant.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {3.0} <music21.note.Note B->
            {3.5} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {12.0} <music21.variant.Variant object of length 4.0>
        {12.0} <music21.stream.Measure 4 offset=12.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note F>
            {2.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 5 offset=16.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note F>
            {2.0} <music21.note.Note A>
        {20.0} <music21.stream.Measure 6 offset=20.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {24.0} <music21.variant.Variant object of length 4.0>
        {24.0} <music21.stream.Measure 7 offset=24.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note B->
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note C>
        {28.0} <music21.stream.Measure 8 offset=28.0>
            {0.0} <music21.note.Note F>
            {4.0} <music21.bar.Barline type=final>

        After a variant group has been activated, the regions it replaced are
        stored as variants with the group 'default'.
        It should be noted that this means .activateVariants should rarely if
        ever be used on a stream which is returned
        by activateVariants because the group information is lost.

        >>> defaultVariant = docVariant.activateVariants('default')
        >>> #_DOCS_SHOW defaultVariant.show()

        .. image:: images/stream_activateVariants3.*
            :width: 600

        >>> defaultVariant.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {12.0} <music21.variant.Variant object of length 8.0>
        {12.0} <music21.stream.Measure 4 offset=12.0>
            {0.0} <music21.note.Note D>
            {2.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 5 offset=16.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {20.0} <music21.variant.Variant object of length 0.0>
        {20.0} <music21.stream.Measure 6 offset=20.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {24.0} <music21.stream.Measure 7 offset=24.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note B->
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note C>
        {28.0} <music21.stream.Measure 8 offset=28.0>
            {0.0} <music21.note.Note F>
            {4.0} <music21.bar.Barline type=final>
        '''
        from music21 import variant
        if not inPlace:  # make a copy if inPlace is False
            returnObj = self.coreCopyAsDerivation('activateVariants')
        else:
            returnObj = self

        # Define Lists to cache variants
        elongationVariants = []
        deletionVariants = []

        # Loop through all variants, deal with replacement variants and
        # save insertion and deletion for later.
        for v in returnObj.getElementsByClass(variant.Variant):
            if group is not None and group not in v.groups:
                continue  # skip those that are not part of this group

            lengthType = v.lengthType

            # save insertions to perform last
            if lengthType == 'elongation':
                elongationVariants.append(v)
            # save deletions to perform after replacements
            elif lengthType == 'deletion':
                deletionVariants.append(v)
            # Deal with cases in which variant is the same length as what it replaces first.
            elif lengthType == 'replacement':
                returnObj._insertReplacementVariant(v, matchBySpan)

        # Now deal with deletions before insertion variants.
        # For keeping track of which measure numbers have been removed
        deletedMeasures = []
        # For keeping track of where new measures without measure numbers have been inserted,
        # will be a list of tuples (measureNumberPrior, [List, of, inserted, measures])
        insertedMeasures = []
        # For keeping track of the sections that are deleted
        # (so the offset gap can be closed later)
        deletedRegionsForRemoval = []
        for v in deletionVariants:
            (deletedRegion, vDeletedMeasures, vInsertedMeasuresTuple
             ) = returnObj._insertDeletionVariant(v, matchBySpan)  # deletes and inserts
            deletedRegionsForRemoval.append(deletedRegion)  # Saves the deleted region
            deletedMeasures.extend(vDeletedMeasures)  # Saves the deleted measure numbers
            # saves the inserted numberless measures (this will be empty unless there are
            # more bars in the variant than in the replacement region, which is unlikely
            # for a deletion variant).
            insertedMeasures.append(vInsertedMeasuresTuple)

        # Squeeze out the gaps that were saved.
        returnObj._removeOrExpandGaps(deletedRegionsForRemoval, isRemove=True, inPlace=True)

        # Before we can deal with insertions, we have to expand the stream to make space.
        insertionRegionsForExpansion = []  # For saving the insertion regions
        # go through all elongation variants to find the insertion regions.
        for v in elongationVariants:
            lengthDifference = v.replacementDuration - v.containedHighestTime
            insertionStart = v.getOffsetBySite(returnObj) + v.replacementDuration
            # Saves the information for each gap to be expanded
            insertionRegionsForExpansion.append((insertionStart, -1 * lengthDifference, [v]))

        # Expands the appropriate gaps in the stream.
        returnObj._removeOrExpandGaps(insertionRegionsForExpansion, isRemove=False, inPlace=True)
        # Now deal with elongation variants properly
        for v in elongationVariants:
            (vInsertedMeasuresTuple, vDeletedMeasures
             ) = returnObj._insertInsertionVariant(v, matchBySpan)  # deletes and inserts
            insertedMeasures.append(vInsertedMeasuresTuple)
            # Saves the numberless inserted measures
            # Saves deleted measures if any (it is unlikely that there will be unless
            # there are fewer measures in the variant than the replacement region,
            # which is unlikely for an elongation variant)
            deletedMeasures.extend(vDeletedMeasures)

        # Now fix measure numbers given the saved information
        returnObj._fixMeasureNumbers(deletedMeasures, insertedMeasures)

        # have to clear cached variants, as they are no longer the same
        returnObj.coreElementsChanged()

        if not inPlace:
            return returnObj
        else:
            return None

    def _insertReplacementVariant(self, v, matchBySpan=True):
        # noinspection PyShadowingNames
        '''
        Helper function for activateVariants. Activates variants which are the same size there the
        region they replace.

        >>> v = variant.Variant()
        >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'),
        ...                  ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
        >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
        >>> variantData = [variantDataM1, variantDataM2]
        >>> for d in variantData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    v.append(m)
        >>> v.groups = ['paris']
        >>> v.replacementDuration = 8.0

        >>> s = stream.Stream()
        >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
        >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'),
        ...                 ('a', 'quarter'), ('b', 'quarter')]
        >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
        >>> for d in streamData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    s.append(m)
        >>> s.insert(4.0, v)

        >>> deletedMeasures, insertedMeasuresTuple = s._insertReplacementVariant(v)
        >>> deletedMeasures
        []
        >>> insertedMeasuresTuple
        (0, [])
        >>> s.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 8.0>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
        {12.0} <music21.stream.Measure 0 offset=12.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>
        '''
        from music21 import variant

        removed = variant.Variant()  # replacement variant
        removed.groups = ['default']  # for now, default
        vStart = self.elementOffset(v)
        # this method matches and removes on an individual basis
        if not matchBySpan:
            targetsMatched = 0
            for e in v.elements:  # get components in the Variant
                # get target offset relative to Stream
                oInStream = vStart + e.getOffsetBySite(v.containedSite)
                # get all elements at this offset, force a class match
                targets = self.getElementsByOffset(oInStream).getElementsByClass(e.classes[0])
                # only replace if we match the start
                if targets:
                    targetsMatched += 1
                    # always assume we just want the first one?
                    targetToReplace = targets[0]
                    # environLocal.printDebug(['matchBySpan', matchBySpan,
                    #     'found target to replace:', targetToReplace])
                    # remove the target, place in removed Variant
                    removed.append(targetToReplace)
                    self.remove(targetToReplace)
                    # extract the variant component and insert into place
                    self.insert(oInStream, e)

                    if getattr(targetToReplace, 'isMeasure', False):
                        e.number = targetToReplace.number
            # only remove old and add removed if we matched
            if targetsMatched > 0:
                # remove the original variant
                self.remove(v)
                # place newly contained elements in position
                self.insert(vStart, removed)

        # matching by span means that we remove all elements with the
        # span defined by the variant
        else:
            deletedMeasures = deque()
            insertedMeasures = []
            highestNumber = None

            targets = v.replacedElements(self)

            # this will always remove elements before inserting
            for e in targets:
                # need to get time relative to variant container's position
                oInVariant = self.elementOffset(e) - vStart
                removed.insert(oInVariant, e)
                # environLocal.printDebug(
                #     ['matchBySpan', matchBySpan, 'activateVariants', 'removing', e])
                self.remove(e)
                if isinstance(e, Measure):
                    # Save deleted measure numbers.
                    deletedMeasures.append(e.number)

            for e in v.elements:
                oInStream = vStart + e.getOffsetBySite(v.containedSite)
                self.insert(oInStream, e)
                if isinstance(e, Measure):
                    if deletedMeasures:  # If there measure numbers left to use, use them.
                        # Assign the next highest deleted measure number
                        e.number = deletedMeasures.popleft()
                        # Save the highest number used so far (for use in the case
                        # that there are extra measures with no numbers at the end)
                        highestNumber = e.number

                    else:
                        e.number = 0
                        # If no measure numbers left, add this
                        # numberless measure to insertedMeasures
                        insertedMeasures.append(e)
            # remove the source variant
            self.remove(v)
            # place newly contained elements in position
            self.insert(vStart, removed)

            # If deletedMeasures != [], then there were more deleted measures than
            # inserted and the remaining numbers in deletedMeasures are those that were removed.
            return (list(deletedMeasures),
                    (highestNumber, insertedMeasures))
            # In the case that the variant and stream are in the same time-signature,
            # this should return []

    def _insertDeletionVariant(self, v, matchBySpan=True):
        # noinspection PyShadowingNames
        '''
        Helper function for activateVariants used for inserting variants that are shorter than
        the region they replace. Inserts elements in the variant and deletes elements in the
        replaced region but does not close gaps.

        Returns a tuple describing the region where elements were removed, the
        gap is left behind to be dealt with by _removeOrExpandGaps.
        Tuple is of form (startOffset, lengthOfDeletedRegion, []). The empty list is
        expected by _removeOrExpandGaps
        and describes the list of elements which should be exempted from shifting
        for a particular gap. In the
        case of deletion, no elements need be exempted.

        >>> v = variant.Variant()
        >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'),
        ...                  ('a', 'quarter'),('b', 'quarter')]
        >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'),
        ...                  ('e', 'quarter'), ('e', 'quarter')]
        >>> variantData = [variantDataM1, variantDataM2]
        >>> for d in variantData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    v.append(m)
        >>> v.groups = ['paris']
        >>> v.replacementDuration = 12.0

        >>> s = stream.Stream()
        >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
        >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'),
        ...                 ('a', 'quarter'), ('b', 'quarter')]
        >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
        >>> for d in streamData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    s.append(m)
        >>> s.insert(4.0, v)


        >>> deletedRegion, deletedMeasures, insertedMeasuresTuple = s._insertDeletionVariant(v)
        >>> deletedRegion
        (12.0, 4.0, [])
        >>> deletedMeasures
        [0]
        >>> insertedMeasuresTuple
        (0, [])
        >>> s.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 12.0>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>

        '''
        from music21 import variant

        deletedMeasures = deque()  # For keeping track of what measure numbers are deleted
        # length of the deleted region
        lengthDifference = v.replacementDuration - v.containedHighestTime

        removed = variant.Variant()  # what group should this have?
        removed.groups = ['default']  # for now, default
        removed.replacementDuration = v.containedHighestTime

        vStart = self.elementOffset(v)
        deletionStart = vStart + v.containedHighestTime

        targets = v.replacedElements(self)

        # this will always remove elements before inserting
        for e in targets:
            if isinstance(e, Measure):  # if a measure is deleted, save its number
                deletedMeasures.append(e.number)
            oInVariant = self.elementOffset(e) - vStart
            removed.insert(oInVariant, e)
            self.remove(e)

        # Next put in the elements from the variant
        highestNumber = None
        insertedMeasures = []
        for e in v.elements:
            if isinstance(e, Measure):
                # If there are deleted numbers still saved, assign this measure the
                # next highest and remove it from the list.
                if deletedMeasures:
                    e.number = deletedMeasures.popleft()
                    # Save the highest number assigned so far. If there are numberless
                    # inserted measures at the end, this will name where to begin numbering.
                    highestNumber = e.number
                else:
                    e.number = 0
                    # If there are no deleted numbers left (unlikely)
                    # save the inserted measures for renumbering later.
                    insertedMeasures.append(e)

            oInStream = vStart + e.getOffsetBySite(v.containedSite)
            self.insert(oInStream, e)

        # remove the source variant
        self.remove(v)
        # place newly contained elements in position
        self.insert(vStart, removed)

        # each variant leaves a gap, this saves the required information about those gaps
        # In most cases, inserted measures should be [].
        return (
            (deletionStart, lengthDifference, []),
            list(deletedMeasures),
            (highestNumber, insertedMeasures)
        )

    def _insertInsertionVariant(self, v, matchBySpan=True):
        # noinspection PyShadowingNames
        '''
        Helper function for activateVariants. _removeOrExpandGaps must be called on the
        expanded regions before this function,
        or it will not work properly.


        >>> v = variant.Variant()
        >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'),
        ...                  ('a', 'quarter'),('b', 'quarter')]
        >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'),
        ...                  ('e', 'quarter'), ('e', 'quarter')]
        >>> variantData = [variantDataM1, variantDataM2]
        >>> for d in variantData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    v.append(m)
        >>> v.groups = ['paris']
        >>> v.replacementDuration = 4.0

        >>> s = stream.Stream()
        >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
        >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'),
        ...                 ('a', 'quarter'), ('b', 'quarter')]
        >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
        >>> for d in streamData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    s.append(m)
        >>> s.insert(4.0, v)

        >>> insertionRegionsForExpansion = [(8.0, 4.0, [v])]
        >>> s._removeOrExpandGaps(insertionRegionsForExpansion, isRemove=False, inPlace=True)

        >>> insertedMeasuresTuple, deletedMeasures = s._insertInsertionVariant(v)
        >>> measurePrior, insertedMeasures = insertedMeasuresTuple
        >>> measurePrior
        0
        >>> len(insertedMeasures)
        1

        >>> s.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
        {12.0} <music21.stream.Measure 0 offset=12.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 0 offset=16.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>

        '''
        from music21 import variant

        deletedMeasures = deque()
        removed = variant.Variant()  # what group should this have?
        removed.groups = ['default']  # for now, default
        removed.replacementDuration = v.containedHighestTime
        vStart = self.elementOffset(v)

        # First deal with the elements in the overlapping section (limit by class)
        targets = v.replacedElements(self)

        # this will always remove elements before inserting
        for e in targets:
            if isinstance(e, Measure):  # Save deleted measure numbers.
                deletedMeasures.append(e.number)
            oInVariant = self.elementOffset(e) - vStart
            removed.insert(oInVariant, e)
            self.remove(e)

        # Next put in the elements from the variant
        highestMeasure = None
        insertedMeasures = []
        for e in v.elements:
            if isinstance(e, Measure):
                # If there are deleted measure numbers left, assign the next
                # inserted measure the next highest number and remove it.
                if deletedMeasures:
                    e.number = deletedMeasures.popleft()
                    highestMeasure = e.number
                    # Save the highest number assigned so far,
                    # so we know where to begin numbering new measures.
                else:
                    e.number = 0
                    insertedMeasures.append(e)
                    # If there are no deleted measures, we have begun inserting as yet
                    # unnumbered measures, save which those are.
            oInStream = vStart + e.getOffsetBySite(v.containedSite)
            self.insert(oInStream, e)

        if highestMeasure is None:
            # If the highestMeasure is None (which will occur if the variant is
            # a strict insertion and replaces no measures),
            # we need to choose the highest measure number prior to the variant.
            measuresToCheck = self.getElementsByOffset(0.0,
                                                       self.elementOffset(v),
                                                       includeEndBoundary=True,
                                                       mustFinishInSpan=False,
                                                       mustBeginInSpan=True,
                                                       ).getElementsByClass(Measure)
            highestMeasure = 0
            for m in measuresToCheck:
                if highestMeasure is None or m.number > highestMeasure:
                    highestMeasure = m.number

        # remove the source variant
        self.remove(v)
        # place newly contained elements in position
        self.insert(vStart, removed)

        return (highestMeasure, insertedMeasures), deletedMeasures

    def _removeOrExpandGaps(self, listOffsetDurExemption,
                            isRemove=True, inPlace=False):
        '''
        Helper for activateVariants. Takes a list of tuples in the form
        (startOffset, duration, [list, of, exempt, objects]). If isRemove is True,
        gaps with duration will be closed at each startOffset.
        Exempt objects are useful for gap-expansion with variants. The gap must push all objects
        that occur after the insertion ahead, but the variant object
        itself should not be moved except by other gaps. This is poorly written
        and should be re-written, but it is difficult to describe.

        >>> s = stream.Stream()
        >>> s.insert(5.0, note.Note('a'))
        >>> s.insert(10.0, note.Note('b'))
        >>> s.insert(11.0, note.Note('c'))
        >>> s.insert(12.0, note.Note('d'))
        >>> s.insert(13.0, note.Note('e'))
        >>> s.insert(20.0, note.Note('f'))
        >>> n = note.Note('g')
        >>> s.insert(15.0, n)

        >>> sGapsRemoved = s._removeOrExpandGaps(
        ...             [(0.0, 5.0, []), (6.0, 4.0, []), (14.0, 6.0, [n])], isRemove=True)
        >>> sGapsRemoved.show('text')
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
        {2.0} <music21.note.Note C>
        {3.0} <music21.note.Note D>
        {4.0} <music21.note.Note E>
        {5.0} <music21.note.Note F>
        {15.0} <music21.note.Note G>

        >>> sGapsExpanded = s._removeOrExpandGaps(
        ...            [(0.0, 5.0, []), (11.0, 5.0, []), (14.0, 1.0, [n])], isRemove=False)
        >>> sGapsExpanded.show('text')
        {10.0} <music21.note.Note A>
        {15.0} <music21.note.Note B>
        {21.0} <music21.note.Note C>
        {22.0} <music21.note.Note D>
        {23.0} <music21.note.Note E>
        {25.0} <music21.note.Note G>
        {31.0} <music21.note.Note F>
        '''
        if inPlace is True:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        returnObjDuration = returnObj.duration.quarterLength

        # If any classes should be exempt from gap closing or expanding, this deals with those.
        if isRemove is True:
            shiftDur = 0.0
            listSorted = sorted(listOffsetDurExemption, key=lambda target: target[0])
            for i, durTuple in enumerate(listSorted):
                startOffset, durationAmount, exemptObjects = durTuple
                exemptObjectSet = set(id(e) for e in exemptObjects)  # use set id, not == checking
                if i + 1 < len(listSorted):
                    endOffset = listSorted[i + 1][0]
                    includeEnd = False
                else:
                    endOffset = returnObjDuration
                    includeEnd = True

                shiftDur = shiftDur + durationAmount
                for e in returnObj.getElementsByOffset(startOffset + durationAmount,
                                                       endOffset,
                                                       includeEndBoundary=includeEnd,
                                                       mustFinishInSpan=False,
                                                       mustBeginInSpan=True):

                    if id(e) in exemptObjectSet:
                        continue
                    if not inPlace and e.derivation.originId in exemptObjectSet:
                        continue

                    elementOffset = e.getOffsetBySite(returnObj)
                    returnObj.coreSetElementOffset(e, elementOffset - shiftDur)
        else:
            shiftDur = 0.0
            shiftsDict = {}
            listSorted = sorted(listOffsetDurExemption, key=lambda target: target[0])
            for i, durTuple in enumerate(listSorted):
                startOffset, durationAmount, exemptObjects = durTuple

                if i + 1 < len(listSorted):
                    endOffset = listSorted[i + 1][0]
                    includeEnd = False
                else:
                    endOffset = returnObjDuration
                    includeEnd = True

                exemptShift = shiftDur
                shiftDur = shiftDur + durationAmount
                shiftsDict[startOffset] = (shiftDur, endOffset, includeEnd,
                                           exemptObjects, exemptShift)

            for offset in sorted(shiftsDict, key=lambda off: -1 * off):
                shiftDur, endOffset, includeEnd, exemptObjects, exemptShift = shiftsDict[offset]
                # for speed and ID not == checking
                exemptObjectSet = set(id(e) for e in exemptObjects)
                for e in returnObj.getElementsByOffset(offset,
                                                       endOffset,
                                                       includeEndBoundary=includeEnd,
                                                       mustFinishInSpan=False,
                                                       mustBeginInSpan=True):

                    if (
                        id(e) in exemptObjectSet
                        or (not inPlace and e.derivation.originId in exemptObjectSet)
                    ):
                        elementOffset = e.getOffsetBySite(returnObj)
                        returnObj.coreSetElementOffset(e, elementOffset + exemptShift)
                        continue

                    elementOffset = e.getOffsetBySite(returnObj)
                    returnObj.coreSetElementOffset(e, elementOffset + shiftDur)

        # ran coreSetElementOffset
        returnObj.coreElementsChanged()

        if inPlace is True:
            return
        else:
            return returnObj

    def _fixMeasureNumbers(self, deletedMeasures, insertedMeasures):
        # noinspection PyShadowingNames
        '''
        Corrects the measures numbers of a string of measures given a list of measure numbers
        that have been deleted and a
        list of tuples (highest measure number below insertion, number of inserted measures).

        >>> s = converter.parse('tinynotation: 4/4 d4 e4 f4 g4   a2 b-4 a4    g4 a8 g8 f4 e4  g1')
        >>> s[-1].offset = 20.0
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {20.0} <music21.stream.Measure 4 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline type=final>
        >>> s.remove(s.measure(2))
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            ...
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            ...
        {20.0} <music21.stream.Measure 4 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline type=final>
        >>> deletedMeasures = [2]
        >>> m1 = stream.Measure()
        >>> m1.repeatAppend(note.Note('e'),4)
        >>> s.insert(12.0, m1)
        >>> m2 = stream.Measure()
        >>> m2.repeatAppend(note.Note('f'),4)
        >>> s.insert(16.0, m2)
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            ...
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            ...
        {12.0} <music21.stream.Measure 0 offset=12.0>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
        {16.0} <music21.stream.Measure 0 offset=16.0>
            {0.0} <music21.note.Note F>
            {1.0} <music21.note.Note F>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note F>
        {20.0} <music21.stream.Measure 4 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline type=final>
        >>> insertedMeasures = [(3, [m1, m2])]

        >>> s._fixMeasureNumbers(deletedMeasures, insertedMeasures)
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            ...
        {8.0} <music21.stream.Measure 2 offset=8.0>
            {0.0} <music21.note.Note G>
            ...
        {12.0} <music21.stream.Measure 3 offset=12.0>
            {0.0} <music21.note.Note E>
            ...
        {16.0} <music21.stream.Measure 4 offset=16.0>
            {0.0} <music21.note.Note F>
            ...
        {20.0} <music21.stream.Measure 5 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline type=final>
        >>> fixedNumbers = []
        >>> for m in s.getElementsByClass(stream.Measure):
        ...    fixedNumbers.append( m.number )
        >>> fixedNumbers
        [1, 2, 3, 4, 5]

        '''
        deletedMeasures.extend(insertedMeasures)
        allMeasures = deletedMeasures

        if not allMeasures:
            return

        def measureNumberSortRoutine(numOrNumTuple):
            if isinstance(numOrNumTuple, tuple):
                return measureNumberSortRoutine(numOrNumTuple[0])
            elif numOrNumTuple is None:
                return -9999
            else:
                return numOrNumTuple

        allMeasures.sort(key=measureNumberSortRoutine)

        oldMeasures = self.getElementsByClass(Measure).stream()
        newMeasures = []

        cumulativeNumberShift = 0
        oldCorrections = {}
        newCorrections = {}
        # the inserted measures must be treated differently than the original measures.
        # an inserted measure should not shift itself,
        # but it should shift measures with the same number.
        # However, inserted measures should still be shifted by every other correction.

        # First collect dictionaries of shift boundaries and the amount of the shift.
        # at the same time, five un-numbered measures numbers that make sense.
        for measureNumber in allMeasures:
            if isinstance(measureNumber, tuple):  # tuple implies insertion
                measurePrior, extendedMeasures = measureNumber
                if not extendedMeasures:  # No measures were added, therefore no shift.
                    continue
                cumulativeNumberShift += len(extendedMeasures)
                nextMeasure = measurePrior + 1
                for m in extendedMeasures:
                    oldMeasures.remove(m)
                    newMeasures.append(m)
                    m.number = nextMeasure
                    nextMeasure += 1
                oldCorrections[measurePrior + 1] = cumulativeNumberShift
                newCorrections[nextMeasure] = cumulativeNumberShift
            else:  # integer implies deletion
                cumulativeNumberShift -= 1
                oldCorrections[measureNumber + 1] = cumulativeNumberShift
                newCorrections[measureNumber + 1] = cumulativeNumberShift

        # Second, make corrections based on the dictionaries. The key is the measure number
        # above which measures should be shifted by the value up to the next key. It is easiest
        # to do this in reverse order so there is no overlapping.
        previousBoundary = None
        for k in sorted(oldCorrections, key=lambda x: -1 * x):
            shift = oldCorrections[k]
            for m in oldMeasures:
                if previousBoundary is None or m.number < previousBoundary:
                    if m.number >= k:
                        m.number = m.number + shift
            previousBoundary = k

        previousBoundary = None
        for k in sorted(newCorrections, key=lambda x: -1 * x):
            shift = newCorrections[k]
            for m in newMeasures:
                if previousBoundary is None or m.number < previousBoundary:
                    if m.number >= k:
                        m.number = m.number + shift
            previousBoundary = k

    def showVariantAsOssialikePart(self, containedPart, variantGroups, *, inPlace=False):
        # noinspection PyShadowingNames
        '''
        Takes a part within the score and a list of variant groups within that part.
        Puts the variant object
        in a part surrounded by hidden rests to mimic the appearance of an ossia despite limited
        musicXML support for ossia staves. Note that this will ignore variants with .lengthType
        'elongation' and 'deletion' as there is no good way to represent ossia staves like those
        by this method.

        >>> sPartStr = 'd4 e4 f4 g4   a2 b-4 a4    g4 a8 g8 f4 e4    d2 a2 '
        >>> v1Str =    '              a2. b-8 a8 '
        >>> v2Str =    '                                             d4 f4 a2 '

        >>> sPartStr += "d4 e4 f4 g4    a2 b-4 a4    g4 a8 b-8 c'4 c4    f1"

        >>> sPartStream = converter.parse('tinynotation: 4/4 ' + sPartStr)
        >>> sPartStream.makeMeasures(inPlace=True)  # maybe not necessary?
        >>> v1stream = converter.parse('tinynotation: 4/4 ' + v1Str)
        >>> v2stream = converter.parse('tinynotation: 4/4 ' + v2Str)

        >>> v1 = variant.Variant()
        >>> v1measure = stream.Measure()
        >>> v1.insert(0.0, v1measure)
        >>> for e in v1stream.notesAndRests:
        ...    v1measure.insert(e.offset, e)

        >>> v2 = variant.Variant()
        >>> v2measure = stream.Measure()
        >>> v2.insert(0.0, v2measure)
        >>> for e in v2stream.notesAndRests:
        ...    v2measure.insert(e.offset, e)

        >>> v3 = variant.Variant()
        >>> v2.replacementDuration = 4.0
        >>> v3.replacementDuration = 4.0
        >>> v1.groups = ['variant1']
        >>> v2.groups = ['variant2']
        >>> v3.groups = ['variant3']

        >>> sPart = stream.Part()
        >>> for e in sPartStream:
        ...    sPart.insert(e.offset, e)

        >>> sPart.insert(4.0, v1)
        >>> sPart.insert(12.0, v2)
        >>> sPart.insert(20.0, v3)  # This is a deletion variant and will be skipped
        >>> s = stream.Score()
        >>> s.insert(0.0, sPart)
        >>> streamWithOssia = s.showVariantAsOssialikePart(sPart,
        ...          ['variant1', 'variant2', 'variant3'], inPlace=False)
        >>> #_DOCS_SHOW streamWithOssia.show()

        '''
        from music21 import variant

        # containedPart must be in self, or an exception is raised.
        if not (containedPart in self):
            raise variant.VariantException(f'Could not find {containedPart} in {self}')

        if inPlace is True:
            returnObj = self
            returnPart = containedPart
        else:
            returnObj = self.coreCopyAsDerivation('showVariantAsOssialikePart')
            containedPartIndex = self.parts.stream().index(containedPart)
            returnPart = returnObj.iter().parts[containedPartIndex]

        # First build a new part object that is the same length as returnPart
        # but entirely hidden rests.
        # This is done by copying the part and removing unnecessary objects
        # including irrelevant variants
        # but saving relevant variants.
        for variantGroup in variantGroups:
            newPart = copy.deepcopy(returnPart)
            expressedVariantsExist = False
            for e in newPart.elements:
                eClasses = e.classes
                if 'Variant' in eClasses:
                    elementGroups = e.groups
                    if (not (variantGroup in elementGroups)
                            or e.lengthType in ['elongation', 'deletion']):
                        newPart.remove(e)
                    else:
                        expressedVariantsExist = True
                elif 'GeneralNote' in eClasses:
                    nQuarterLength = e.duration.quarterLength
                    nOffset = e.getOffsetBySite(newPart)
                    newPart.remove(e)
                    r = note.Rest()
                    r.style.hideObjectOnPrint = True
                    r.duration.quarterLength = nQuarterLength
                    newPart.insert(nOffset, r)
                elif 'Measure' in eClasses:  # Recurse if measure
                    measureDuration = e.duration.quarterLength
                    for n in e.notesAndRests:
                        e.remove(n)
                    r = note.Rest()
                    r.duration.quarterLength = measureDuration
                    r.style.hideObjectOnPrint = True
                    e.insert(0.0, r)

                e.style.hideObjectOnPrint = True

            newPart.activateVariants(variantGroup, inPlace=True, matchBySpan=True)
            if expressedVariantsExist:
                returnObj.insert(0.0, newPart)

        if inPlace:
            return
        else:
            return returnObj

# -----------------------------------------------------------------------------


class Voice(Stream):
    '''
    A Stream subclass for declaring that all the music in the
    stream belongs to a certain "voice" for analysis or display
    purposes.

    Note that both Finale's Layers and Voices as concepts are
    considered Voices here.

    Voices have a sort order of 1 greater than time signatures
    '''
    recursionType = RecursionType.ELEMENTS_FIRST
    classSortOrder = 5

# -----------------------------------------------------------------------------


class Measure(Stream):
    '''
    A representation of a Measure organized as a Stream.

    All properties of a Measure that are Music21 objects are found as part of
    the Stream's elements.

    Measure number can be explicitly set with the `number` keyword:

    >>> m4 = stream.Measure(number=4)
    >>> m4
    <music21.stream.Measure 4 offset=0.0>
    >>> m4.number
    4

    If passed a single integer as an argument, assumes that this int
    is the measure number.

    >>> m5 = stream.Measure(5)
    >>> m5
    <music21.stream.Measure 5 offset=0.0>

    Number can also be a string if there is a suffix:

    >>> m4 = stream.Measure(number='4a')
    >>> m4
    <music21.stream.Measure 4a offset=0.0>
    >>> m4.numberSuffix
    'a'

    Though they have all the features of general streams,
    Measures have specific attributes that allow for setting their number
    and numberSuffix, keep track of whether they have a different clef or
    key or timeSignature than previous measures, allow for padding (and pickups),
    and can be found as a "measure slice" within a score and parts.
    '''
    recursionType = RecursionType.ELEMENTS_FIRST
    isMeasure = True

    # define order for presenting names in documentation; use strings
    _DOC_ORDER = ['']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR: dict[str, str] = {
        'timeSignatureIsNew': '''
            Boolean describing if the TimeSignature
            is different than the previous Measure.''',
        'clefIsNew': 'Boolean describing if the Clef is different than the previous Measure.',
        'keyIsNew': 'Boolean describing if KeySignature is different than the previous Measure.',
        'number': '''
            A number representing the displayed or shown
            Measure number as presented in a written Score.''',
        'numberSuffix': '''
            If a Measure number has a string annotation, such as "a" or similar,
            this string is stored here. Note that in MusicXML, such
            suffixes often appear as
            prefixes to measure numbers.  In music21 (like most measure
            numbering systems), these
            numbers appear as suffixes.''',
        'showNumber': '''
            Enum describing if the measure number should be displayed.''',
        'layoutWidth': '''
            A suggestion for layout width, though most rendering systems do not support
            this designation. Use :class:`~music21.layout.SystemLayout`
            objects instead.''',
        'paddingLeft': '''
            defines empty space at the front of the measure for purposes of determining
            beat, etc for pickup/anacrusis bars.  In 4/4, a
            measure with a one-beat pickup
            note will have a `paddingLeft` of 3.0.
            (The name comes from the CSS graphical term
            for the amount of padding on the left side of a region.)''',
        'paddingRight': '''
            defines empty space at the end of the measure for purposes of determining
            whether or not a measure is filled.
            In 4/4, a piece beginning a one-beat pickup
            note will often have a final measure of three beats, instead of four.
            The final
            measure should have a `paddingRight` of 1.0.
            (The name comes from the CSS graphical term
            for the amount of padding on the right side of a region.)''',
    }

    def __init__(self, *args, number: int | str = 0, **keywords):
        if len(args) == 1 and isinstance(args[0], int) and number == 0:
            number = args[0]
            args = ()

        super().__init__(*args, **keywords)

        # clef and timeSignature is defined as a property below
        self.timeSignatureIsNew = False
        self.clefIsNew = False
        self.keyIsNew = False

        self.filled = False

        # padding: defining a context for offsets contained within this Measure
        # padding defines dead regions of offsets into the measure
        # the paddingLeft is used by TimeSignature objects to determine beat
        # position; paddingRight defines a QL from the end of the time signature
        # to the last valid offset
        # paddingLeft is used to define pickup/anacrusis bars
        self.paddingLeft: OffsetQL = 0.0
        self.paddingRight: OffsetQL = 0.0

        self.numberSuffix = None  # for measure 14a would be 'a'
        if isinstance(number, str):
            realNum, suffix = common.getNumFromStr(number)
            self.number = int(realNum)
            if suffix:
                self.numberSuffix = suffix
        else:
            self.number = number
        self.showNumber = ShowNumber.DEFAULT
        # we can request layout width, using the same units used
        # in layout.py for systems; most musicxml readers do not support this
        # on input
        self.layoutWidth = None

    # def addRepeat(self):
    #     # TODO: write
    #     pass

    # def addTimeDependentDirection(self, time, direction):
    #     # TODO: write
    #     pass

    def measureNumberWithSuffix(self):
        '''
        Return the measure `.number` with the `.numberSuffix` as a string.

        >>> m = stream.Measure()
        >>> m.number = 4
        >>> m.numberSuffix = 'A'
        >>> m.measureNumberWithSuffix()
        '4A'

        Test that it works as musicxml

        >>> xml = musicxml.m21ToXml.GeneralObjectExporter().parse(m)
        >>> print(xml.decode('utf-8'))
        <?xml version="1.0"...?>
        ...
        <part id="...">
            <!--========================= Measure 4 ==========================-->
            <measure implicit="no" number="4A">
        ...

        Test round tripping:

        >>> s2 = converter.parseData(xml)
        >>> print(s2[stream.Measure].first().measureNumberWithSuffix())
        4A

        Note that we use print here because in parsing the data will become a unicode string.
        '''
        if self.numberSuffix:
            return str(self.number) + self.numberSuffix
        else:
            return str(self.number)

    def _reprInternal(self):
        return self.measureNumberWithSuffix() + f' offset={self.offset}'

    # -------------------------------------------------------------------------
    def mergeAttributes(self, other):
        '''
        Given another Measure, configure all non-element attributes of this
        Measure with the attributes of the other Measure. No elements
        will be changed or copied.

        This method is necessary because Measures, unlike some Streams,
        have attributes independent of any stored elements.

        Overrides base.Music21Object.mergeAttributes

        >>> m1 = stream.Measure()
        >>> m1.id = 'MyMeasure'
        >>> m1.clefIsNew = True
        >>> m1.number = 2
        >>> m1.numberSuffix = 'b'
        >>> m1.layoutWidth = 200

        >>> m2 = stream.Measure()
        >>> m2.mergeAttributes(m1)
        >>> m2.layoutWidth
        200
        >>> m2.id
        'MyMeasure'
        >>> m2
        <music21.stream.Measure 2b offset=0.0>

        Try with not another Measure...

        >>> m3 = stream.Stream()
        >>> m3.id = 'hello'
        >>> m2.mergeAttributes(m3)
        >>> m2.id
        'hello'
        >>> m2.layoutWidth
        200
        '''
        # calling bass class sets id, groups
        super().mergeAttributes(other)

        for attr in ('timeSignatureIsNew', 'clefIsNew', 'keyIsNew', 'filled',
                     'paddingLeft', 'paddingRight', 'number', 'numberSuffix', 'layoutWidth'):
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

    # -------------------------------------------------------------------------
    def makeNotation(self,
                     inPlace=False,
                     **subroutineKeywords):
        # noinspection PyShadowingNames
        '''
        This method calls a sequence of Stream methods on this
        :class:`~music21.stream.Measure` to prepare notation.

        If `inPlace` is True, this is done in-place; if
        `inPlace` is False, this returns a modified deep copy.

        >>> m = stream.Measure()
        >>> n1 = note.Note('g#')
        >>> n2 = note.Note('g')
        >>> m.append([n1, n2])
        >>> m.makeNotation(inPlace=True)
        >>> m.notes[1].pitch.accidental
        <music21.pitch.Accidental natural>
        '''
        # environLocal.printDebug(['Measure.makeNotation'])
        # TODO: this probably needs to look to see what processes need to be done;
        # for example, existing beaming may be destroyed.

        # do this before deepcopy...

        # assuming we are not trying to get context of previous measure
        if not inPlace:  # make a copy
            m = copy.deepcopy(self)
        else:
            m = self

        srkCopy = subroutineKeywords.copy()

        for illegalKey in ('meterStream', 'refStreamOrTimeRange', 'bestClef'):
            if illegalKey in srkCopy:
                del srkCopy[illegalKey]

        m.makeAccidentals(searchKeySignatureByContext=True, inPlace=True, **srkCopy)
        # makeTies is for cross-bar associations, and cannot be used
        # at just the measure level
        # m.makeTies(meterStream, inPlace=True)

        # must have a time signature before calling make beams
        if m.timeSignature is None:
            # get a time signature if not defined, searching the context if
            # necessary
            contextMeters = m.getTimeSignatures(searchContext=True,
                                                returnDefault=False)
            defaultMeters = m.getTimeSignatures(searchContext=False,
                                                returnDefault=True)
            if contextMeters:
                ts = contextMeters[0]
            else:
                try:
                    ts = self.bestTimeSignature()
                except (StreamException, meter.MeterException):
                    # there must be one here
                    ts = defaultMeters[0]
            m.timeSignature = ts  # a Stream; get the first element

        makeNotation.splitElementsToCompleteTuplets(m, recurse=True, addTies=True)
        makeNotation.consolidateCompletedTuplets(m, recurse=True, onlyIfTied=True)

        m.makeBeams(inPlace=True)
        for m_or_v in [m, *m.voices]:
            makeNotation.makeTupletBrackets(m_or_v, inPlace=True)

        if not inPlace:
            return m
        else:
            return None

    def barDurationProportion(self, barDuration=None):
        '''
        Return a floating point value greater than 0 showing the proportion
        of the bar duration that is filled based on the highest time of
        all elements. 0.0 is empty, 1.0 is filled; 1.5 specifies of an
        overflow of half.

        Bar duration refers to the duration of the Measure as suggested by
        the `TimeSignature`. This value cannot be determined without a `TimeSignature`.

        An already-obtained Duration object can be supplied with the `barDuration`
        optional argument.

        >>> import copy
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        Fraction(1, 3)
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        Fraction(2, 3)
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        1.0
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        Fraction(4, 3)
        '''
        # passing a barDuration may save time in the lookup process
        if barDuration is None:
            barDuration = self.barDuration
        return opFrac(self.highestTime / barDuration.quarterLength)

    def padAsAnacrusis(self, useGaps=True, useInitialRests=False):
        '''
        Given an incompletely filled Measure, adjust the `paddingLeft` value to
        represent contained events as shifted to fill the right-most duration of the bar.

        Calling this method will overwrite any previously set `paddingLeft` value,
        based on the current TimeSignature-derived `barDuration` attribute.

        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1.0
        >>> m.append(n)
        >>> m.padAsAnacrusis()
        >>> m.paddingLeft
        2.0

        >>> m.timeSignature = meter.TimeSignature('5/4')
        >>> m.padAsAnacrusis()
        >>> m.paddingLeft
        4.0


        Empty space at the beginning of the measure will not be taken in account:

        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note(type='quarter')
        >>> m.insert(2.0, n)
        >>> m.padAsAnacrusis()
        >>> m.paddingLeft
        0.0

        If useInitialRests is True, then rests at the beginning of the measure
        are removed.  This is especially useful for formats that don't give a
        way to specify a pickup measure (such as tinynotation) or software
        that generates incorrect opening measures.  So, to fix the problem before,
        put a rest at the beginning and call useInitialRests:

        >>> r = note.Rest(type='half')
        >>> m.insert(0, r)
        >>> m.padAsAnacrusis(useInitialRests=True)
        >>> m.paddingLeft
        2.0

        And the rest is gone!

        >>> m.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>


        Only initial rests count for useInitialRests:

        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.append(note.Rest(type='eighth'))
        >>> m.append(note.Rest(type='eighth'))
        >>> m.append(note.Note('C4', type='quarter'))
        >>> m.append(note.Rest(type='eighth'))
        >>> m.append(note.Note('D4', type='eighth'))
        >>> m.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Rest eighth>
        {0.5} <music21.note.Rest eighth>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Rest eighth>
        {2.5} <music21.note.Note D>
        >>> m.padAsAnacrusis(useInitialRests=True)
        >>> m.paddingLeft
        1.0
        >>> m.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Rest eighth>
        {1.5} <music21.note.Note D>
        '''
        if useInitialRests:
            removeList = []
            for gn in self.notesAndRests:
                if not isinstance(gn, note.Rest):
                    break
                removeList.append(gn)
            if removeList:
                self.remove(removeList, shiftOffsets=True)

        # note: may need to set paddingLeft to 0 before examining

        # bar duration is that suggested by time signature; it
        # may not be the same as Stream duration, which is based on contents
        barDuration = self.barDuration
        proportion = self.barDurationProportion(barDuration=barDuration)
        if proportion < 1:
            # get 1 complement
            proportionShift = 1 - proportion
            self.paddingLeft = opFrac(barDuration.quarterLength * proportionShift)

            # shift = barDuration.quarterLength * proportionShift
            # environLocal.printDebug(['got anacrusis shift:', shift,
            #                    barDuration.quarterLength, proportion])
            # this will shift all elements
            # self.shiftElements(shift, classFilterList=(note.GeneralNote,))
        else:
            pass
            # environLocal.printDebug(['padAsAnacrusis() called; however,
            # no anacrusis shift necessary:', barDuration.quarterLength, proportion])

    # --------------------------------------------------------------------------
    @property
    def barDuration(self):
        '''
        Return the bar duration, or the Duration specified by the TimeSignature,
        regardless of what elements are found in this Measure or the highest time.
        TimeSignature is found first within the Measure,
        or within a context based search.

        To get the duration of the total length of elements, just use the
        `.duration` property.

        Here we create a 3/4 measure and "over-stuff" it with five quarter notes.
        `barDuration` still gives a duration of 3.0, or a dotted quarter note,
        while `.duration` gives a whole note tied to a quarter.


        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.barDuration
        <music21.duration.Duration 3.0>
        >>> m.repeatAppend(note.Note(type='quarter'), 5)
        >>> m.barDuration
        <music21.duration.Duration 3.0>
        >>> m.duration
        <music21.duration.Duration 5.0>

        The objects returned by `barDuration` and `duration` are
        full :class:`~music21.duration.Duration`
        objects, will all the relevant properties:

        >>> m.barDuration.fullName
        'Dotted Half'
        >>> m.duration.fullName
        'Whole tied to Quarter (5 total QL)'
        '''
        # TODO: it is possible that this should be cached or exposed as a method
        #     as this search may take some time.
        if self.timeSignature is not None:
            ts = self.timeSignature
        else:  # do a context-based search
            tsStream = self.getTimeSignatures(searchContext=True,
                                              returnDefault=False,
                                              sortByCreationTime=True)
            if not tsStream:
                try:
                    ts = self.bestTimeSignature()
                except exceptions21.Music21Exception:
                    return duration.Duration(self.highestTime)

                # raise StreamException(
                #   'cannot determine bar duration without a time signature reference')
            else:  # it is the first found
                ts = tsStream[0]
        return ts.barDuration

    # --------------------------------------------------------------------------
    # Music21Objects are stored in the Stream's elements list
    # properties are provided to store and access these attribute

    def bestTimeSignature(self):
        '''
        Given a Measure with elements in it,
        get a TimeSignature that contains all elements.
        Calls meter.bestTimeSignature(self)

        Note: this does not yet accommodate triplets.


        We create a simple stream that should be in 3/4


        >>> s = converter.parse('C4 D4 E8 F8', format='tinyNotation', makeNotation=False)
        >>> m = stream.Measure()
        >>> for el in s:
        ...     m.insert(el.offset, el)

        But there is no TimeSignature!

        >>> m.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {2.5} <music21.note.Note F>

        So, we get the best Time Signature and put it in the Stream.

        >>> ts = m.bestTimeSignature()
        >>> ts
        <music21.meter.TimeSignature 3/4>
        >>> m.timeSignature = ts
        >>> m.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {2.5} <music21.note.Note F>

        For further details about complex time signatures, etc.
        see `meter.bestTimeSignature()`

        '''
        return meter.bestTimeSignature(self)

    def _getLeftBarline(self):
        barList = []
        # directly access _elements, as do not want to get any bars
        # in _endElements
        for e in self._elements:
            if isinstance(e, bar.Barline):  # take the first
                if self.elementOffset(e) == 0.0:
                    barList.append(e)
                    break
        if not barList:
            return None
        else:
            return barList[0]

    def _setLeftBarline(self, barlineObj):
        insert = True
        if isinstance(barlineObj, str):
            barlineObj = bar.Barline(barlineObj)
            barlineObj.location = 'left'
        elif barlineObj is None:  # assume removal
            insert = False
        else:  # assume a Barline object
            barlineObj.location = 'left'

        oldLeftBarline = self._getLeftBarline()
        if oldLeftBarline is not None:
            # environLocal.printDebug(['_setLeftBarline()', 'removing left barline'])
            junk = self.pop(self.index(oldLeftBarline))
        if insert:
            # environLocal.printDebug(['_setLeftBarline()',
            # 'inserting new left barline', barlineObj])
            self.insert(0, barlineObj)

    leftBarline = property(_getLeftBarline,
                           _setLeftBarline,
                           doc='''
        Get or set the left barline, or the Barline object
        found at offset zero of the Measure.  Can be set either with a string
        representing barline style or a bar.Barline() object or None.
        Note that not all bars have
        barline objects here -- regular barlines don't need them.
        ''')

    def _getRightBarline(self):
        # TODO: Move to Stream or make setting .rightBarline, etc. on Stream raise an exception...
        # look on _endElements
        barList = []
        for e in self._endElements:
            if isinstance(e, bar.Barline):  # take the first
                barList.append(e)
                break
        # barList = self.getElementsByClass(bar.Barline)
        if not barList:  # do this before searching for barQL
            return None
        else:
            return barList[0]

    def _setRightBarline(self, barlineObj):
        insert = True
        if isinstance(barlineObj, str):
            barlineObj = bar.Barline(barlineObj)
            barlineObj.location = 'right'
        elif barlineObj is None:  # assume removal
            insert = False
        else:  # assume a Barline object
            barlineObj.location = 'right'

        # if a repeat, setup direction if not assigned
        if barlineObj is not None and isinstance(barlineObj, bar.Repeat):
            # environLocal.printDebug(['got barline obj w/ direction', barlineObj.direction])
            if barlineObj.direction in ['start', None]:
                barlineObj.direction = 'end'
        oldRightBarline = self._getRightBarline()

        if oldRightBarline is not None:
            # environLocal.printDebug(['_setRightBarline()', 'removing right barline'])
            junk = self.pop(self.index(oldRightBarline))
        # insert into _endElements
        if insert:
            self.storeAtEnd(barlineObj)

        # environLocal.printDebug(['post _setRightBarline', barlineObj,
        #    'len of elements highest', len(self._endElements)])

    rightBarline = property(_getRightBarline,
                            _setRightBarline,
                            doc='''
        Get or set the right barline, or the Barline object
        found at the offset equal to the bar duration.

        >>> b = bar.Barline('final')
        >>> m = stream.Measure()
        >>> print(m.rightBarline)
        None
        >>> m.rightBarline = b
        >>> m.rightBarline.type
        'final'


        A string can also be used instead:

        >>> c = converter.parse('tinynotation: 3/8 C8 D E F G A B4.')
        >>> c.measure(1).rightBarline = 'light-light'
        >>> c.measure(3).rightBarline = 'light-heavy'
        >>> #_DOCS_SHOW c.show()

        .. image:: images/stream_barline_demo.*
            :width: 211

        OMIT_FROM_DOCS

        .measure currently isn't the same as the
        original measure...

        ''')


class Part(Stream):
    '''
    A Stream subclass for designating music that is considered a single part.

    When put into a Score object, Part objects are all collected in the `Score.parts`
    call.  Otherwise, they mostly work like generic Streams.

    Generally the hierarchy goes: Score > Part > Measure > Voice, but you are not
    required to stick to this.

    Part groupings (piano braces, etc.) are found in the :ref:`moduleLayout` module
    in the :class:`~music21.layout.StaffGroup` Spanner object.

    OMIT_FROM_DOCS
    Check that this is True and works for everything before suggesting that it works!

    May be enclosed in a staff (for instance, 2nd and 3rd trombone
    on a single staff), may enclose staves (piano treble and piano bass),
    or may not enclose or be enclosed by a staff (in which case, it
    assumes that this part fits on one staff and shares it with no other
    part
    '''
    recursionType = RecursionType.FLATTEN

    # _DOC_ATTR: dict[str, str] = {
    # }

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self._partName = None
        self._partAbbreviation = None

    def _getPartName(self):
        if self._partName is not None:
            return self._partName
        elif '_partName' in self._cache:
            return self._cache['_partName']
        else:
            pn = None
            for e in self[instrument.Instrument]:
                pn = e.partName
                if pn is None:
                    pn = e.instrumentName
                if pn is not None:
                    break
            self._cache['_partName'] = pn
            return pn

    def _setPartName(self, newName):
        self._partName = newName

    partName = property(_getPartName, _setPartName, doc='''
        Gets or sets a string representing the name of this part
        as a whole (not counting instrument changes, etc.).

        It can be set explicitly (or set on parsing) or it
        can take its name from the first :class:`~music21.instrument.Instrument` object
        encountered in the stream (or within a substream),
        first checking its .partName, then checking its .instrumentName

        Can also return None.

        >>> p = stream.Part()
        >>> p.partName is None
        True
        >>> cl = instrument.Clarinet()
        >>> p.insert(0, cl)
        >>> p.partName
        'Clarinet'
        >>> p.remove(cl)
        >>> p.partName is None
        True
        >>> p.insert(0, instrument.Flute())
        >>> p.partName
        'Flute'
        >>> p.partName = 'Reed 1'
        >>> p.partName
        'Reed 1'

        Note that changing an instrument's .partName or .instrumentName while it
        is already in the Stream will not automatically update this unless
        .coreElementsChanged() is called or this Stream's elements are otherwise altered.
        This is because the value is cached so that O(n) searches through the Stream
        do not need to be done every time.
    ''')

    def _getPartAbbreviation(self):
        if self._partAbbreviation is not None:
            return self._partAbbreviation
        elif '_partAbbreviation' in self._cache:
            return self._cache['_partAbbreviation']
        else:
            pn = None
            for e in self[instrument.Instrument]:
                pn = e.partAbbreviation
                if pn is None:
                    pn = e.instrumentAbbreviation
                if pn is not None:
                    break
            self._cache['_partAbbreviation'] = pn
            return pn

    def _setPartAbbreviation(self, newName):
        self._partAbbreviation = newName

    partAbbreviation = property(_getPartAbbreviation, _setPartAbbreviation, doc='''
        Gets or sets a string representing the abbreviated name of this part
        as a whole (not counting instrument changes, etc.).

        It can be set explicitly (or set on parsing) or it
        can take its name from the first :class:`~music21.instrument.Instrument` object
        encountered in the stream (or within a substream),
        first checking its .partAbbreviation, then checking its .instrumentAbbreviation

        Can also return None.

        >>> p = stream.Part()
        >>> p.partAbbreviation is None
        True
        >>> cl = instrument.Clarinet()
        >>> p.insert(0, cl)
        >>> p.partAbbreviation
        'Cl'
        >>> p.remove(cl)
        >>> p.partAbbreviation is None
        True
        >>> p.insert(0, instrument.Flute())
        >>> p.partAbbreviation
        'Fl'
        >>> p.partAbbreviation = 'Rd 1'
        >>> p.partAbbreviation
        'Rd 1'

        Note that changing an instrument's .partAbbreviation or .instrumentAbbreviation while it
        is already in the Stream will not automatically update this unless
        .coreElementsChanged() is called or this Stream's elements are otherwise altered.
        This is because the value is cached so that O(n) searches through the Stream
        do not need to be done every time.
    ''')

    def makeAccidentals(
        self,
        *,
        alteredPitches=None,
        cautionaryPitchClass=True,
        cautionaryAll=False,
        inPlace=False,
        overrideStatus=False,
        cautionaryNotImmediateRepeat=True,
        tiePitchSet=None,
    ):
        '''
        This overridden method of Stream.makeAccidentals
        walks measures to arrive at desired values for keyword arguments
        `tiePitchSet` and `pitchPastMeasure` when calling `makeAccidentals()`
        on each Measure.

        1. Ties across barlines are detected so that accidentals are not
        unnecessarily reiterated. (`tiePitchSet`)

        2. Pitches appearing on the same step in an immediately preceding measure,
        if foreign to the key signature of that previous measure,
        are printed with cautionary accidentals in the subsequent measure.
        (`pitchPastMeasure`)

        Most of the logic has been factored out to
        :meth:`~music21.stream.makeNotation.makeAccidentalsInMeasureStream`,
        which is called after managing the `inPlace` keyword and finding
        measures to iterate.

        * Changed in v7: `inPlace` defaults False
        '''
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('makeAccidentals')
        else:
            returnObj = self
        # process make accidentals for each measure
        measureStream = returnObj.getElementsByClass(Measure)
        makeNotation.makeAccidentalsInMeasureStream(
            measureStream,
            alteredPitches=alteredPitches,
            cautionaryPitchClass=cautionaryPitchClass,
            cautionaryAll=cautionaryAll,
            overrideStatus=overrideStatus,
            cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
            tiePitchSet=tiePitchSet,
        )
        if not inPlace:
            return returnObj
        else:  # in place
            return None

    def mergeAttributes(self, other):
        '''
        Merge relevant attributes from the Other part
        into this one. Key attributes of difference: partName and partAbbreviation.

        TODO: doc test
        '''
        super().mergeAttributes(other)

        for attr in ('_partName', '_partAbbreviation'):
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

class PartStaff(Part):
    '''
    A Part subclass for designating music that is
    represented on a single staff but may only be one
    of many staves for a single part.
    '''


# class Performer(Stream):
#     '''
#     A Stream subclass for designating music to be performed by a
#     single Performer.  Should only be used when a single performer
#     performs on multiple parts.  E.g. Bass Drum and Triangle on separate
#     staves performed by one player.
#
#     a Part + changes of Instrument is fine for designating most cases
#     where a player changes instrument in a piece.  A part plus staves
#     with individual instrument changes could also be a way of designating
#     music that is performed by a single performer (see, for instance
#     the Piano doubling Celesta part in Lukas Foss's Time Cycle).  The
#     Performer Stream-subclass could be useful for analyses of, for instance,
#     how 5 percussionists chose to play a piece originally designated for 4
#     (or 6) percussionists in the score.
#     '''
#     # NOTE: not yet implemented
#     pass

class System(Stream):
    '''
    Totally optional and used only in OMR and Capella: a designation that all the
    music in this Stream belongs in a single system.

    The system object has two attributes, systemNumber (which number is it)
    and systemNumbering which says at what point the numbering of
    systems resets.  It can be either "Score" (default), "Opus", or "Page".
    '''
    systemNumber = 0
    systemNumbering = 'Score'  # or Page; when do system numbers reset?


class Score(Stream):
    '''
    A Stream subclass for handling music with more than one Part.

    Almost totally optional (the largest containing Stream in a piece could be
    a generic Stream, or a Part, or a Staff).  And Scores can be
    embedded in other Scores (in fact, our original thought was to call
    this class a Fragment because of this possibility of continuous
    embedding; though it's probably better to embed a Score in an Opus),
    but we figure that many people will like calling the largest
    container a Score and that this will become a standard.
    '''
    recursionType = RecursionType.ELEMENTS_ONLY

    @property
    def parts(self) -> iterator.StreamIterator[Part]:
        '''
        Return all :class:`~music21.stream.Part` objects in a :class:`~music21.stream.Score`.

        It filters out all other things that might be in a Score object, such as Metadata
        returning just the Parts.

        >>> s = corpus.parse('bach/bwv66.6')
        >>> s.parts
        <music21.stream.iterator.StreamIterator for Score:bach/bwv66.6.mxl @:0>
        >>> len(s.parts)
        4
        '''
        partIterator: iterator.StreamIterator[Part] = self.getElementsByClass(Part)
        partIterator.overrideDerivation = 'parts'
        return partIterator

    def measures(self,
                 numberStart,
                 numberEnd,
                 collect=('Clef', 'TimeSignature', 'Instrument', 'KeySignature'),
                 gatherSpanners=GatherSpanners.ALL,
                 indicesNotNumbers=False):
        # noinspection PyShadowingNames
        '''
        This method overrides the :meth:`~music21.stream.Stream.measures`
        method on Stream. This creates a new Score stream that has the same measure
        range for all Parts.

        The `collect` argument is a list of classes that will be collected; see
        Stream.measures()

        >>> s = corpus.parse('bwv66.6')
        >>> post = s.measures(3, 5)  # range is inclusive, i.e., [3, 5]
        >>> len(post.parts)
        4
        >>> len(post.parts[0].getElementsByClass(stream.Measure))
        3
        >>> len(post.parts[1].getElementsByClass(stream.Measure))
        3
        '''
        post = self.__class__()
        # this calls on Music21Object, transfers groups, id if not id(self)
        post.mergeAttributes(self)
        # note that this will strip all objects that are not Parts
        for p in self.parts:
            # insert all at zero
            measuredPart = p.measures(numberStart,
                                      numberEnd,
                                      collect=collect,
                                      gatherSpanners=gatherSpanners,
                                      indicesNotNumbers=indicesNotNumbers)
            post.insert(0, measuredPart)
        # must manually add any spanners; do not need to add .flatten(),
        # as Stream.measures will handle lower level
        if gatherSpanners:
            spStream = self.spanners
            for sp in spStream:
                post.insert(0, sp)

        post.derivation.client = post
        post.derivation.origin = self
        post.derivation.method = 'measures'
        return post

    # this is Score.measure
    def measure(self,
                measureNumber,
                collect=(clef.Clef, meter.TimeSignature, instrument.Instrument, key.KeySignature),
                gatherSpanners=GatherSpanners.ALL,
                indicesNotNumbers=False):
        '''
        Given a measure number (or measure index, if indicesNotNumbers is True)
        return another Score object which contains multiple parts but each of which has only a
        single :class:`~music21.stream.Measure` object if the
        Measure number exists, otherwise returns a score with parts that are empty.

        This method overrides the :meth:`~music21.stream.Stream.measure` method on Stream to
        allow for finding a single "measure slice" within parts:

        >>> bachIn = corpus.parse('bach/bwv324.xml')
        >>> excerpt = bachIn.measure(2)
        >>> excerpt
        <music21.stream.Score bach/bwv324.mxl>
        >>> len(excerpt.parts)
        4
        >>> excerpt.parts[0].show('text')
        {0.0} <music21.instrument.Instrument 'P1: Soprano: '>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.Key of e minor>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.stream.Measure 2 offset=0.0>
            {0.0} <music21.note.Note B>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note B>
            {3.0} <music21.note.Note B>

        Note that the parts created have all the meta-information outside the measure
        unless this information appears in the measure itself at the beginning:

        >>> bachIn.measure(1).parts[0].show('text')
        {0.0} <music21.instrument.Instrument 'P1: Soprano: '>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.key.Key of e minor>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.note.Note B>
            {2.0} <music21.note.Note D>

        This way the original measure objects can be returned without being altered.

        The final measure slice of the piece can be obtained with index -1.  Example:
        quickly get the last chord of the piece, without needing to run .chordify()
        on the whole piece:

        >>> excerpt = bachIn.measure(-1)
        >>> excerptChords = excerpt.chordify()
        >>> excerptChords.show('text')
        {0.0} <music21.instrument.Instrument 'P1: Soprano: '>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.key.Key of e minor>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.stream.Measure 9 offset=0.0>
            {0.0} <music21.chord.Chord E2 G3 B3 E4>
            {4.0} <music21.bar.Barline type=final>

        >>> lastChord = excerptChords[chord.Chord].last()
        >>> lastChord
        <music21.chord.Chord E2 G3 B3 E4>

        Note that we still do a .getElementsByClass(chord.Chord) since many pieces end
        with nothing but a rest...
        '''
        if measureNumber < 0:
            indicesNotNumbers = True

        startMeasureNumber = measureNumber
        endMeasureNumber = measureNumber
        if indicesNotNumbers:
            endMeasureNumber += 1
            if startMeasureNumber == -1:
                endMeasureNumber = None

        post = self.__class__()
        # this calls on Music21Object, transfers id, groups
        post.mergeAttributes(self)
        # note that this will strip all objects that are not Parts
        for p in self.getElementsByClass(Part):
            # insert all at zero
            mStream = p.measures(startMeasureNumber,
                                 endMeasureNumber,
                                 collect=collect,
                                 gatherSpanners=gatherSpanners,
                                 indicesNotNumbers=indicesNotNumbers)
            post.insert(0, mStream)

        if gatherSpanners:
            spStream = self.spanners
            for sp in spStream:
                post.insert(0, sp)

        post.derivation.client = post
        post.derivation.origin = self
        post.derivation.method = 'measure'

        return post

    def expandRepeats(self: Score, copySpanners: bool = True) -> Score:
        '''
        Expand all repeats, as well as all repeat indications
        given by text expressions such as D.C. al Segno.

        This method always returns a new Stream, with deepcopies
        of all contained elements at all level.

        Note that copySpanners is ignored here, as they are always copied.
        '''
        post = self.cloneEmpty(derivationMethod='expandRepeats')
        # this calls on Music21Object, transfers id, groups
        post.mergeAttributes(self)

        # get all things in the score that are not Parts
        for e in self.iter().getElementsNotOfClass(Part):
            eNew = copy.deepcopy(e)  # assume that this is needed
            post.insert(self.elementOffset(e), eNew)

        for p in self.getElementsByClass(Part):
            # get spanners at highest level, not by Part
            post.insert(0, p.expandRepeats(copySpanners=False))

        # spannerBundle = spanner.SpannerBundle(list(post.flatten().spanners))
        spannerBundle = post.spannerBundle  # use property
        # iterate over complete semi flat (need containers); find
        # all new/old pairs
        for e in post.recurse(includeSelf=False):
            # update based on last id, new object
            if e.sites.hasSpannerSite():
                origin = e.derivation.origin
                if origin is not None and e.derivation.method == '__deepcopy__':
                    spannerBundle.replaceSpannedElement(origin, e)
        return post

    def measureOffsetMap(
        self,
        classFilterList: list[t.Type] | list[str] | tuple[t.Type] | tuple[str] = ('Measure',)
    ) -> OrderedDict[float | Fraction, list[Measure]]:
        '''
        This Score method overrides the
        :meth:`~music21.stream.Stream.measureOffsetMap` method of Stream.
        This creates a map based on all contained Parts in this Score.
        Measures found in multiple Parts with the same offset will be
        appended to the same list.

        If no parts are found in the score, then the normal
        :meth:`~music21.stream.Stream.measureOffsetMap` routine is called.

        This method is smart and does not assume that all Parts
        have measures with identical offsets.
        '''
        parts = self.iter().parts
        if not parts:
            return Stream.measureOffsetMap(self, classFilterList)
        # else:
        offsetMap: dict[float | Fraction, list[Measure]] = {}
        for p in parts:
            mapPartial = p.measureOffsetMap(classFilterList)
            # environLocal.printDebug(['mapPartial', mapPartial])
            for k in mapPartial:
                if k not in offsetMap:
                    offsetMap[k] = []
                for m in mapPartial[k]:  # get measures from partial
                    if m not in offsetMap[k]:
                        offsetMap[k].append(m)
        orderedOffsetMap = OrderedDict(sorted(offsetMap.items(), key=lambda o: o[0]))
        return orderedOffsetMap


    @overload
    def sliceByGreatestDivisor(
        self: Score,
        *,
        addTies: bool = True,
        inPlace: t.Literal[True],
    ) -> None:
        pass

    @overload
    def sliceByGreatestDivisor(
        self: Score,
        *,
        addTies: bool = True,
        inPlace: t.Literal[False] = False,
    ) -> Score:
        pass

    def sliceByGreatestDivisor(
        self: Score,
        *,
        addTies: bool = True,
        inPlace: bool = False,
    ) -> Score | None:
        '''
        Slice all duration of all part by the minimum duration
        that can be summed to each concurrent duration.

        Overrides method defined on Stream.
        '''
        if not inPlace:  # make a copy
            returnObj = self.coreCopyAsDerivation('sliceByGreatestDivisor')
        else:

            returnObj = self

        # Find the greatest divisor for each measure at a time.
        # If there are no measures this will be zero.
        firstPart = returnObj.parts.first()
        if firstPart is None:
            raise TypeError('Cannot sliceByGreatestDivisor without parts')
        mStream = firstPart.getElementsByClass(Measure)
        mCount = len(mStream)
        if mCount == 0:
            mCount = 1  # treat as a single measure

        m_or_p: Measure | Part
        for i in range(mCount):  # may be 1
            uniqueQuarterLengths = []
            p: Part
            for p in returnObj.getElementsByClass(Part):
                if p.hasMeasures():
                    m_or_p = p.getElementsByClass(Measure)[i]
                else:
                    m_or_p = p  # treat the entire part as one measure

                # collect all unique quarter lengths
                for e in m_or_p.notesAndRests:
                    # environLocal.printDebug(['examining e', i, e, e.quarterLength])
                    if e.quarterLength not in uniqueQuarterLengths:
                        uniqueQuarterLengths.append(e.quarterLength)

            # after ql for all parts, find divisor
            divisor = common.approximateGCD(uniqueQuarterLengths)
            # environLocal.printDebug(['Score.sliceByGreatestDivisor:
            # got divisor from unique ql:', divisor, uniqueQuarterLengths])

            for p in returnObj.getElementsByClass(Part):
                # in place: already have a copy if nec
                # must do on measure at a time
                if p.hasMeasures():
                    m_or_p = p.getElementsByClass(Measure)[i]
                else:
                    m_or_p = p  # treat the entire part as one measure
                m_or_p.sliceByQuarterLengths(quarterLengthList=[divisor],
                                             target=None,
                                             addTies=addTies,
                                             inPlace=True)
        del mStream  # cleanup Streams
        returnObj.coreElementsChanged()
        if not inPlace:
            return returnObj

    def partsToVoices(self,
                      voiceAllocation: int | list[list | int] = 2,
                      permitOneVoicePerPart=False,
                      setStems=True):
        # noinspection PyShadowingNames
        '''
        Given a multi-part :class:`~music21.stream.Score`,
        return a new Score that combines parts into voices.

        The `voiceAllocation` parameter sets the maximum number
        of voices per Part.

        The `permitOneVoicePerPart` parameter, if True, will encode a
        single voice inside a single Part, rather than leaving it as
        a single Part alone, with no internal voices.


        >>> s = corpus.parse('bwv66.6')
        >>> len(s.flatten().notes)
        165
        >>> post = s.partsToVoices(voiceAllocation=4)
        >>> len(post.parts)
        1
        >>> len(post.parts.first().getElementsByClass(stream.Measure).first().voices)
        4
        >>> len(post.flatten().notes)
        165

        '''
        sub: list[Part] = []
        bundle = []
        if isinstance(voiceAllocation, int):
            voicesPerPart = voiceAllocation
            for pIndex, p in enumerate(self.parts):
                if pIndex % voicesPerPart == 0:
                    sub = []
                    sub.append(p)
                else:
                    sub.append(p)
                if pIndex % voicesPerPart == voicesPerPart - 1:
                    bundle.append(sub)
                    sub = []
            if sub:  # get last
                bundle.append(sub)
        # else, assume it is a list of groupings
        elif common.isIterable(voiceAllocation):
            voiceAllocation = t.cast(list[list | int], voiceAllocation)
            for group in voiceAllocation:
                sub = []
                # if a single entry
                if not isinstance(group, list):
                    # group is a single index
                    sub.append(self.parts[group])
                else:
                    for partId in group:
                        sub.append(self.parts[partId])
                bundle.append(sub)
        else:
            raise StreamException(f'incorrect voiceAllocation format: {voiceAllocation}')

        # environLocal.printDebug(['partsToVoices() bundle:', bundle])

        s = self.cloneEmpty(derivationMethod='partsToVoices')
        s.metadata = self.metadata

        pActive: Part | None
        for sub in bundle:  # each sub contains parts
            if len(sub) == 1 and not permitOneVoicePerPart:
                # probably need to create a new part and measure
                s.insert(0, sub[0])
                continue

            pActive = Part()
            # iterate through each part
            for pIndex, p in enumerate(sub):
                # only check for measures once per part
                if pActive.hasMeasures():
                    hasMeasures = True
                else:
                    hasMeasures = False

                for mIndex, m in enumerate(p.getElementsByClass(Measure)):
                    # environLocal.printDebug(['pIndex, p', pIndex, p,
                    #     'mIndex, m', mIndex, m, 'hasMeasures', hasMeasures])
                    # only create measures if non already exist
                    if not hasMeasures:
                        # environLocal.printDebug(['creating measure'])
                        mActive = Measure()
                        # some attributes may be none
                        # note: not copying here; and first part read will provide
                        # attributes; possible other parts may have other attributes
                        mActive.mergeAttributes(m)
                        mActive.mergeElements(m, classFilterList=(
                            'Barline', 'TimeSignature', 'Clef', 'KeySignature'))

                        # if m.timeSignature is not None:
                        #     mActive.timeSignature = m.timeSignature
                        # if m.keySignature is not None:
                        #     mActive.keySignature = m.keySignature
                        # if m.clef is not None:
                        #     mActive.clef = m.clef
                    else:
                        mActive = pActive.getElementsByClass(Measure)[mIndex]

                    # transfer elements into a voice
                    v = Voice()
                    v.id = pIndex
                    # for now, just take notes, including rests
                    for e in m.notesAndRests:  # m.getElementsByClass():
                        if setStems and isinstance(e, note.Note):
                            e.stemDirection = 'up' if pIndex % 2 == 0 else 'down'
                        v.insert(e.getOffsetBySite(m), e)
                    # insert voice in new measure
                    # environLocal.printDebug(['inserting voice', v, v.id, 'into measure', mActive])
                    mActive.insert(0, v)
                    # mActive.show('t')
                    # only insert measure if new part does not already have measures
                    if not hasMeasures:
                        pActive.insert(m.getOffsetBySite(p), mActive)

            s.insert(0, pActive)
            pActive = None
        return s

    def implode(self):
        '''
        Reduce a polyphonic work into two staves.

        Currently, this is just a synonym for `partsToVoices` with
        `voiceAllocation = 2`, and `permitOneVoicePerPart = False`,
        but someday this will have better methods for finding identical
        parts, etc.
        '''
        voiceAllocation = 2
        permitOneVoicePerPart = False

        return self.partsToVoices(
            voiceAllocation=voiceAllocation,
            permitOneVoicePerPart=permitOneVoicePerPart
        )

    def makeNotation(
        self,
        meterStream=None,
        refStreamOrTimeRange=None,
        inPlace=False,
        bestClef=False,
        **subroutineKeywords
    ):
        '''
        This method overrides the makeNotation method on Stream,
        such that a Score object with one or more Parts or Streams
        that may not contain well-formed notation may be transformed
        and replaced by well-formed notation.

        If `inPlace` is True, this is done in-place;
        if `inPlace` is False, this returns a modified deep copy.
        '''
        # returnStream: Score
        if inPlace:
            returnStream = self
        else:
            returnStream = self.coreCopyAsDerivation('makeNotation')
        returnStream.coreGatherMissingSpanners()  # get spanners needed but not here!

        # do not assume that we have parts here
        if self.hasPartLikeStreams():
            # s: Stream
            for s in returnStream.getElementsByClass('Stream'):
                # process all component Streams inPlace
                s.makeNotation(meterStream=meterStream,
                               refStreamOrTimeRange=refStreamOrTimeRange,
                               inPlace=True,
                               bestClef=bestClef,
                               **subroutineKeywords)
            # note: while the local-streams have updated their caches, the
            # containing score has an out-of-date cache of flat.
            # thus, must call elements changed
            # but... since all we have done in this method is call coreGatherMissingSpanners()
            # and makeNotation(), neither of which are supposed to leave the stream
            # unusable (with an out-of-date cache), the original issue was likely deeper
            # no matter, let's just be extra cautious and run this here (Feb 2021 - JTW)
            returnStream.coreElementsChanged()
        else:  # call the base method
            super(Score, returnStream).makeNotation(meterStream=meterStream,
                                                    refStreamOrTimeRange=refStreamOrTimeRange,
                                                    inPlace=True,
                                                    bestClef=bestClef,
                                                    **subroutineKeywords)

        if inPlace:
            return None
        else:
            return returnStream


class Opus(Stream):
    '''
    A Stream subclass for handling multi-work music encodings.
    Many ABC files, for example, define multiple works or parts within a single file.

    Opus objects can contain multiple Score objects, or even other Opus objects!
    '''
    recursionType = RecursionType.ELEMENTS_ONLY

    # TODO: get by title, possibly w/ regex

    def getNumbers(self):
        '''
        Return a list of all numbers defined in this Opus.

        >>> o = corpus.parse('josquin/oVenusBant')
        >>> o.getNumbers()
        ['1', '2', '3']
        '''
        post = []
        for s in self.getElementsByClass(Score):
            post.append(s.metadata.number)
        return post

    def getScoreByNumber(self, opusMatch):
        # noinspection PyShadowingNames
        '''
        Get Score objects from this Stream by number.
        Performs title search using the
        :meth:`~music21.metadata.Metadata.search` method,
        and returns the first result.

        >>> o = corpus.parse('josquin/oVenusBant')
        >>> o.getNumbers()
        ['1', '2', '3']
        >>> s = o.getScoreByNumber(2)
        >>> s.metadata.title
        'O Venus bant'
        >>> s.metadata.alternativeTitle
        'Tenor'
        '''
        for s in self.getElementsByClass(Score):
            match, unused_field = s.metadata.search(opusMatch, 'number')
            if match:
                return s

    # noinspection SpellCheckingInspection
    def getScoreByTitle(self, titleMatch):
        # noinspection SpellCheckingInspection, PyShadowingNames
        '''
        Get Score objects from this Stream by a title.
        Performs title search using the :meth:`~music21.metadata.Metadata.search` method,
        and returns the first result.

        >>> o = corpus.parse('essenFolksong/erk5')
        >>> s = o.getScoreByTitle('Vrienden, kommt alle gaere')
        >>> s.metadata.title
        'Vrienden, kommt alle gaere'

        Regular expressions work fine

        >>> s = o.getScoreByTitle('(.*)kommt(.*)')
        >>> s.metadata.title
        'Vrienden, kommt alle gaere'
        '''
        for s in self.getElementsByClass(Score):
            match, unused_field = s.metadata.search(titleMatch, 'title')
            if match:
                return s

    @property
    def scores(self):
        '''
        Return all :class:`~music21.stream.Score` objects
        in an iterator
        '''
        return self.getElementsByClass('Score')  # replacing with bare Score is not working.

    def mergeScores(self):
        # noinspection PyShadowingNames
        '''
        Some Opus objects represent numerous scores
        that are individual parts of the same work.
        This method will treat each contained Score as a Part,
        merging and returning a single Score with merged Metadata.

        >>> o = corpus.parse('josquin/milleRegrets')
        >>> s = o.mergeScores()
        >>> s.metadata.title
        'Mille regrets'
        >>> len(s.parts)
        4
        '''
        sNew = Score()
        mdNew = metadata.Metadata()

        for s in self.scores:
            p = s.parts.first().makeNotation()  # assuming only one part
            sNew.insert(0, p)

            md = s.metadata
            # presently just getting the first of attributes encountered
            if md is not None:
                # environLocal.printDebug(['sub-score metadata', md,
                #   'md.composer', md.composer, 'md.title', md.title])
                if md.title is not None and mdNew.title is None:
                    mdNew.title = md.title
                if md.composer is not None and mdNew.composer is None:
                    mdNew.composer = md.composer

        sNew.insert(0, mdNew)
        return sNew

    # -------------------------------------------------------------------------
    def write(self, fmt=None, fp=None, **keywords):
        '''
        Displays an object in a format provided by the `fmt` argument or, if not
        provided, the format set in the user's Environment.

        This method overrides the behavior specified in
        :class:`~music21.base.Music21Object` for all formats besides explicit
        lily.x calls.

        Individual files are written for each score; returns the last file written.

        >>> sc1 = stream.Score()
        >>> sc2 = stream.Score()
        >>> o = stream.Opus()
        >>> o.append([sc1, sc2])

        #_DOCS_SHOW >>> o.write()
        #_DOCS_SHOW PosixPath('/some/temp/path-2.xml')
        '''
        if not self.scores:
            return None

        if fmt is not None and 'lily' in fmt:
            return Stream.write(self, fmt, fp, **keywords)
        elif common.runningInNotebook():
            return Stream.write(self, fmt, fp, **keywords)

        delete = False
        if fp is None:
            if fmt is None:
                suffix = '.' + environLocal['writeFormat']
            else:
                unused_format, suffix = common.findFormat(fmt)
            fp = environLocal.getTempFile(suffix=suffix, returnPathlib=False)
            # Mark for deletion, because it won't actually be used
            delete = True
        if isinstance(fp, str):
            fp = pathlib.Path(fp)

        fpParent = fp.parent
        fpStem = fp.stem
        fpSuffix = '.'.join(fp.suffixes)

        post = []
        placesRequired = math.ceil(math.log10(len(self.scores)))
        for i, s in enumerate(self.scores):
            # if i = 9, num = 10, take log10(11) so the result is strictly greater than 1.0
            placesConsumed = math.ceil(math.log10(i + 2))
            zeroesNeeded = placesRequired - placesConsumed
            zeroes = '0' * zeroesNeeded
            scoreName = fpStem + '-' + zeroes + str(i + 1) + fpSuffix
            fpToUse = fpParent / scoreName
            fpReturned = s.write(fmt=fmt, fp=fpToUse, **keywords)
            environLocal.printDebug(f'Component {s} written to {fpReturned}')
            post.append(fpReturned)

        if delete:
            os.remove(fp)

        return post[-1] if post else None

    def show(self, fmt=None, app=None, **keywords):
        '''
        Show an Opus file.

        This method overrides the behavior specified in
        :class:`~music21.base.Music21Object` for all
        formats besides explicit lily.x calls. or when running under Jupyter notebook.
        '''
        if fmt is not None and 'lily' in fmt:
            return Stream.show(self, fmt, app, **keywords)
        elif common.runningInNotebook():
            return Stream.show(self, fmt, app, **keywords)
        else:
            for s in self.scores:
                s.show(fmt=fmt, app=app, **keywords)


# -----------------------------------------------------------------------------
# Special stream sub-classes that are instantiated as hidden attributes within
# other Music21Objects (i.e., Spanner and Variant).


class SpannerStorage(Stream):
    '''
    For advanced use. This Stream subclass is only used
    inside a Spanner object to provide object storage
    of connected elements (things the Spanner spans).

    This subclass name can be used to search in an
    object's .sites and find any and all
    locations that are SpannerStorage objects.

    A `client` keyword argument must be provided by the Spanner in creation.

    >>> stream.SpannerStorage(client=spanner.Slur())
    <music21.stream.SpannerStorage for music21.spanner.Slur>

    * Changed in v8: spannerParent is renamed client.
    '''
    def __init__(self, givenElements=None, *, client: spanner.Spanner | None = None, **keywords):
        # No longer need store as weakref since Py2.3 and better references
        if client is None:  # should never be none.  Just for testing
            from music21 import spanner
            client = spanner.Spanner()
        self.client: spanner.Spanner = client
        super().__init__(givenElements, **keywords)

        # must provide a keyword argument with a reference to the spanner
        # parent could name spannerContainer or other?

        # environLocal.printDebug('keywords', keywords)

    def _reprInternal(self):
        tc = type(self.client)
        return f'for {tc.__module__}.{tc.__qualname__}'

    # NOTE: for serialization, this will need to properly tag
    # the spanner parent by updating the scaffolding code.
    def coreSelfActiveSite(self, el):
        '''
        Never set activeSite to spannerStorage
        '''
        pass

    def coreStoreAtEnd(self, element, setActiveSite=True):  # pragma: no cover
        raise StreamException('SpannerStorage cannot store at end.')

    def replace(self,
                target: base.Music21Object,
                replacement: base.Music21Object,
                *,
                recurse: bool = False,
                allDerived: bool = True) -> None:
        '''
        Overrides :meth:`~music21.stream.Stream.replace` in order to check first
        whether `replacement` already exists in `self`. If so, delete `target` from
        `self` and return; otherwise call the superclass method.

        * New in v7.
        '''
        # Does not perform a recursive search, but shouldn't need to
        if replacement in self:
            self.remove(target)
            return
        super().replace(target, replacement, recurse=recurse, allDerived=allDerived)


class VariantStorage(Stream):
    '''
    For advanced use. This Stream subclass is only
    used inside a Variant object to provide object
    storage of connected elements (things the Variant
    defines).

    This subclass name can be used to search in an
    object's .sites and find any and all
    locations that are VariantStorage objects.  It also
    ensures that they are pickled properly as Streams on a non-Stream
    object.

    * Changed in v8: variantParent is removed.  Never used.
    '''
# -----------------------------------------------------------------------------


class Test(unittest.TestCase):
    '''
    Note: most Stream tests are found in stream.tests
    '''
    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())


# -----------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Stream, Measure, Part, Score, Opus, Voice,
              SpannerStorage, VariantStorage, OffsetMap]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
