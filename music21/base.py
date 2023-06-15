# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         base.py
# Purpose:      Music21 base classes and important utilities
#
# Authors:      Michael Scott Asato Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2006-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
`music21.base` is what you get in `music21` if you type ``import music21``. It
contains all the most low-level objects that also appear in the music21 module
(i.e., music21.base.Music21Object is the same as music21.Music21Object).

Music21 base classes for :class:`~music21.stream.Stream` objects and all
elements contained within them including Notes, etc. Additional objects for
defining and manipulating elements are included.

The namespace of this file, as all base.py files, is loaded into the package
that contains this file via __init__.py. Everything in this file is thus
available after importing `music21`.

>>> import music21
>>> music21.Music21Object
<class 'music21.base.Music21Object'>

>>> music21.VERSION_STR
'9.1.0'

Alternatively, after doing a complete import, these classes are available
under the module "base":

>>> base.Music21Object
<class 'music21.base.Music21Object'>
'''
from __future__ import annotations

import builtins
from collections.abc import Generator, Iterable
import copy
import functools
from importlib.util import find_spec
import typing as t
from typing import overload  # Pycharm can't do alias
import unittest
import warnings
import weakref

from music21._version import __version__, __version_info__
from music21 import common
from music21.common.enums import ElementSearch, OffsetSpecial
from music21.common.numberTools import opFrac
from music21.common.types import OffsetQL, OffsetQLIn
from music21 import defaults
from music21.derivation import Derivation
from music21.duration import Duration, DurationException
from music21.editorial import Editorial  # import class directly to not conflict with property.
from music21 import environment
from music21 import exceptions21
from music21 import prebase
from music21.sites import Sites, SitesException, WEAKREF_ACTIVE
from music21.style import Style  # pylint: disable=unused-import
from music21.sorting import SortTuple, ZeroSortTupleLow, ZeroSortTupleHigh
# needed for temporal manipulations; not music21 objects
from music21 import tie

if t.TYPE_CHECKING:
    import fractions
    from io import IOBase
    import pathlib
    from music21 import meter
    from music21 import stream
    from music21 import spanner

    _M21T = t.TypeVar('_M21T', bound='music21.base.Music21Object')

# all other music21 modules below...

# -----------------------------------------------------------------------------
# version string and tuple must be the same

VERSION = __version_info__
VERSION_STR = __version__
# -----------------------------------------------------------------------------
__all__ = [
    'Music21Exception',
    'SitesException',
    'Music21ObjectException',
    'ElementException',

    'Groups',
    'Music21Object',
    'ElementWrapper',

    'VERSION',
    'VERSION_STR',
]

# N.B. for PyDev "all" import working, we need to list this
#       separately in "music21/__init__.py"
# so make sure to update in both places

# ----all exceptions are in the exceptions21 package.

Music21Exception = exceptions21.Music21Exception

environLocal = environment.Environment('base')

_missingImport = []
for modName in ('matplotlib', 'numpy'):
    loader = find_spec(modName)
    if loader is None:  # pragma: no cover
        _missingImport.append(modName)

del find_spec
del modName

if _missingImport:  # pragma: no cover
    if environLocal['warnings'] in (1, '1', True):
        environLocal.warn(common.getMissingImportStr(_missingImport),
                          header='music21:')


class Music21ObjectException(exceptions21.Music21Exception):
    pass


class ElementException(exceptions21.Music21Exception):
    pass


# -----------------------------------------------------------------------------
# for contextSites searches...
class ContextTuple(t.NamedTuple):
    site: stream.Stream
    offset: OffsetQL
    recurseType: stream.enums.RecursionType

class ContextSortTuple(t.NamedTuple):
    site: stream.Stream
    offset: SortTuple
    recurseType: stream.enums.RecursionType


# pseudo class for returning splitAtX() type commands.
class _SplitTuple(tuple):
    '''
    >>> st = base._SplitTuple([1, 2])
    >>> st.spannerList = [3]
    >>> st
    (1, 2)
    >>> st.spannerList
    [3]
    >>> a, b = st
    >>> a
    1
    >>> b
    2
    >>> st.__class__
    <class 'music21.base._SplitTuple'>
    '''
    def __new__(cls, tupEls):
        # noinspection PyTypeChecker
        return super(_SplitTuple, cls).__new__(cls, tuple(tupEls))

    def __init__(self, tupEls):  # pylint: disable=super-init-not-called
        self.spannerList = []

# -----------------------------------------------------------------------------
# make subclass of set once that is defined properly


class Groups(list):  # no need to inherit from slotted object
    '''
    Groups is a list (subclass) of strings used to identify
    associations that an element might have.

    (in the future, Groups will become a set subclass)

    The Groups object enforces that all elements must be strings, and that
    the same element cannot be provided more than once.

    NOTE: In the future, spaces will not be allowed in group names.


    >>> g = Groups()
    >>> g.append('hello')
    >>> g[0]
    'hello'

    >>> g.append('hello')  # not added as already present
    >>> len(g)
    1

    >>> g
    ['hello']

    >>> g.append(5)  # type: ignore
    Traceback (most recent call last):
    music21.exceptions21.GroupException: Only strings can be used as group names, not 5
    '''
    # could be made into a set instance, but actually
    # timing: a subclassed list and a set are almost the same speed
    # and set does not allow calling by number

    # this speeds up creation slightly...
    __slots__ = ()

    def _validName(self, value: str) -> None:
        if not isinstance(value, str):
            raise exceptions21.GroupException('Only strings can be used as group names, '
                                              + f'not {value!r}')
        # if ' ' in value:
        #     raise exceptions21.GroupException('Spaces are not allowed as group names')

    def append(self, value: str) -> None:
        self._validName(value)
        if not list.__contains__(self, value):
            list.append(self, value)

    def __setitem__(self, i, y):
        self._validName(y)
        super().__setitem__(i, y)

    def __eq__(self, other: object):
        '''
        Test Group equality. In normal lists, order matters; here it does not. More like a set.

        >>> a = base.Groups()
        >>> a.append('red')
        >>> a.append('green')
        >>> a
        ['red', 'green']

        >>> b = base.Groups()
        >>> b.append('green')
        >>> a == b
        False

        >>> b.append('reD')  # case insensitive
        >>> a == b
        True

        >>> a == ['red', 'green']  # need both to be groups
        False

        >>> c = base.Groups()
        >>> c.append('black')
        >>> c.append('tuba')
        >>> a == c
        False
        '''
        if not isinstance(other, Groups):
            return False

        if len(self) != len(other):
            return False
        sls = sorted(self)
        slo = sorted(other)

        for x in range(len(sls)):
            if sls[x].lower() != slo[x].lower():
                return False
        return True


# -----------------------------------------------------------------------------
# these are two sentinel objects that are returned when getattr(self, attr) or
# getattr(other, attr) fail, that ensure that the two failed attributes will
# never equal each other.
_EQUALITY_SENTINEL_SELF = object()
_EQUALITY_SENTINEL_OTHER = object()


@functools.cache
def _getEqualityAttributes(cls) -> frozenset[str]:
    '''
    Get equality attributes for a class.  Cached.

    >>> base._getEqualityAttributes(base.Music21Object)
    frozenset({'duration'})
    >>> 'location' in base._getEqualityAttributes(bar.Barline)
    True
    >>> 'pitch' in base._getEqualityAttributes(bar.Barline)
    False

    '''
    equalityAttributes = set()
    # equalityAttributesIgnore works, but not yet needed.
    # equalityAttributesIgnore = set()
    # for klass in [cls, *cls.mro()]:
    #     if hasattr(klass, 'equalityAttributesIgnore'):
    #         ka = klass.equalityAttributesIgnore
    #         if isinstance(ka, str):  # mistake.  Happens TOO often:
    #             ka = (ka,)
    #         equalityAttributesIgnore |= set(ka)

    for klass in [cls, *cls.mro()]:
        if hasattr(klass, 'equalityAttributes'):
            ka = klass.equalityAttributes
            if isinstance(ka, str):  # mistake.  Happens TOO often:
                ka = (ka,)
            equalityAttributes |= set(ka)
    # equalityAttributes.difference_update(equalityAttributesIgnore)
    return frozenset(equalityAttributes)


class Music21Object(prebase.ProtoM21Object):
    '''
    Music21Object is the base class for all elements that can go into Streams.
    Notes, Clefs, TimeSignatures are all sublcasses of Music21Object.  Durations
    and Pitches (which need to be attached to Notes, etc.) are not.

    All music21 objects have these pieces of information:

    1.  id: identification string unique to the object's container (optional).
        Defaults to the `id()` of the element.
    2.  groups: a :class:`~music21.base.Groups` object: which is a
        list of strings identifying internal sub-collections
        (voices, parts, selections) to which this element belongs
    3.  duration: :class:`~music21.duration.Duration` object representing the length of the object
    4.  activeSite: a reference to the currently active :class:`~music21.stream.Stream` or None
    5.  offset: a floating point or Fraction value, generally in quarter lengths,
        specifying the position of the object in a site.
    6.  priority: int representing the position of an object among all
        objects at the same offset.
    7.  sites: a :class:`~music21.base.Sites` object that stores all
        the Streams and Contexts that an
        object is in.
    8.  derivation: a :class:`~music21.derivation.Derivation` object, or None, that shows
        where the object came from.
    9.  style: a :class:`~music21.style.Style` object, that contains Style information
        automatically created if it doesn't exist, so check `.hasStyleInformation` first
        if that is not desired.
    10. editorial: a :class:`~music21.editorial.Editorial` object

    Each of these may be passed in as a named keyword to any music21 object.

    Some of these may be intercepted by the subclassing object (e.g., duration
    within Note)

    **Equality**

    For historical reasons, music21 uses a different idea of object equality
    for Music21Objects than recommended by modern Python standards.

    Two Music21Objects are equal if they are the same class and same duration.

    Their offset, activeSite, id, and groups do not matter for equality.

    Since these two objects are therefore not interchangable, they do not have
    the same hash value.

    >>> obj1 = base.Music21Object(id='obj1')
    >>> obj2 = base.Music21Object(id='obj2')
    >>> obj1 == obj2
    True
    >>> hash(obj1) == hash(obj2)
    False

    This has the stange side effect that structures that use equality to
    report containment (such as lists and tuples) will report differently from
    structures that use hash values to report containment (such as dicts and sets):

    >>> obj1 in [obj2]
    True
    >>> obj1 in {obj2}
    False

    Subclasses need to apply stricter criteria for equality, like Barline does here
    with `.location`

    >>> bar1 = bar.Barline('double', 'left')
    >>> bar2 = bar.Barline('double', 'right')
    >>> bar1 == bar2
    False
    >>> bar2.location = 'left'
    >>> bar1 == bar2
    True
    >>> bar1.duration.type = 'whole'  # Buh?
    >>> bar1 == bar2
    False

    In general, a subclass of Music21Object must match all super-class criteria for
    equality before they can be considered equal themselves.  However, there are some
    exceptions.  For instance, RomanNumeral objects with the same figure and key are
    equal even if their notes are in different octaves or have different doublings.

    Developers creating their own Music21Object subclasses should add a class attribute
    `equalityAttributes = ('one', 'two')`.  (Remember that as a tuple of strings, if there
    is only one string, don't forget the trailing comma: `('only',)`.

    >>> class CarolineShawBreathMark(base.Music21Object):
    ...     equalityAttributes = ('direction',)
    ...     def __init__(self, direction, speed):
    ...         super().__init__(self)
    ...         self.direction = direction
    ...         self.speed = speed
    >>> bm1 = CarolineShawBreathMark('in', 'fast')
    >>> bm2 = CarolineShawBreathMark('out', 'fast')
    >>> bm1 == bm2
    False

    "speed" is not in the equalityAttributes so it can differ while objects are still
    equal.

    >>> bm3 = CarolineShawBreathMark('in', 'slow')
    >>> bm1 == bm3
    True
    '''

    classSortOrder: int | float = 20  # default classSortOrder
    # these values permit fast class comparisons for performance critical cases
    isStream = False

    _styleClass: type[Style] = Style

    equalityAttributes: tuple[str, ...] = ('duration',)
    # equalityAttributesIgnore: tuple[str, ...] = ()  # this must be defined anew in each subclass.

    # define order for presenting names in documentation; use strings
    _DOC_ORDER: list[str] = []

    # documentation for all attributes (not properties or methods)
    _DOC_ATTR: dict[str, str] = {
        'groups': '''An instance of a :class:`~music21.base.Groups`
            object which describes
            arbitrary `Groups` that this object belongs to.''',
        'sites': '''a :class:`~music21.sites.Sites` object that stores
            references to Streams that hold this object.''',
        'isStream': '''Boolean value for quickly identifying
            :class:`~music21.stream.Stream` objects (False by default).''',
        'classSortOrder': '''Property which returns an number (int or otherwise)
            depending on the class of the Music21Object that
            represents a priority for an object based on its class alone --
            used as a tie for stream sorting in case two objects have the
            same offset and priority.  Lower numbers are sorted to the left
            of higher numbers.  For instance, Clef, KeySignature, TimeSignature
            all come (in that order) before Note.

            All undefined classes have classSortOrder of 20 -- same as note.Note

            >>> m21o = base.Music21Object()
            >>> m21o.classSortOrder
            20

            >>> tc = clef.TrebleClef()
            >>> tc.classSortOrder
            0

            >>> ks = key.KeySignature(3)
            >>> ks.classSortOrder
            2


            New classes can define their own default classSortOrder

            >>> class ExampleClass(base.Music21Object):
            ...     classSortOrder = 5
            ...
            >>> ec1 = ExampleClass()
            >>> ec1.classSortOrder
            5
            ''',
    }

    def __init__(self,
                 id: str | int | None = None,  # pylint: disable=redefined-builtin
                 groups: Groups | None = None,
                 sites: Sites | None = None,
                 duration: Duration | None = None,
                 activeSite: stream.Stream | None = None,
                 style: Style | None = None,
                 editorial: Editorial | None = None,
                 offset: OffsetQL = 0.0,
                 quarterLength: OffsetQLIn | None = None,
                 **keywords):
        # do not call super().__init__() since it just wastes time
        self._id: str | int | None = id
        # None is stored as the internal location of an obj w/o any sites
        self._activeSite: stream.Stream | weakref.ReferenceType | None = None
        # offset when no activeSite is available
        self._naiveOffset: OffsetQL = offset

        # offset when activeSite is already garbage collected/dead,
        # as in short-lived sites
        # like .getElementsByClass().stream()
        self._activeSiteStoredOffset: float | fractions.Fraction | None = None

        # store a derivation object to track derivations from other Streams
        # pass a reference to this object
        self._derivation: Derivation | None = None

        self._style: Style | None = style
        self._editorial: Editorial | None = None

        # private duration storage; managed by property
        self._duration: Duration | None = duration
        if duration is not None:
            duration.client = self
        self._priority = 0  # default is zero

        # store cached values here:
        self._cache: dict[str, t.Any] = {}

        self.groups = groups or Groups()
        self.sites = sites or Sites()

        # a duration object is not created until the .duration property is
        # accessed with _getDuration(); this is a performance optimization
        if activeSite is not None:
            self.activeSite = activeSite
        if quarterLength is not None:
            self.duration.quarterLength = quarterLength

    def __eq__(self: _M21T, other) -> t.TypeGuard[_M21T]:
        '''
        Define equality for Music21Objects.  See main class docs.
        '''
        cls = t.cast(type, self.__class__)
        if not isinstance(other, cls):
            return False

        for attr in _getEqualityAttributes(cls):
            if (getattr(self, attr, _EQUALITY_SENTINEL_SELF)
                    != getattr(other, attr, _EQUALITY_SENTINEL_OTHER)):
                return False
        return True

    def __hash__(self) -> int:
        '''
        Restore hashing, but only on id(self)
        '''
        return id(self) >> 4

    @property
    def id(self) -> int | str:
        '''
        A unique identification string or int; not to be confused with Python's
        built-in `id()` method. However, if not set, will return
        Python's `id()` number.

        "Unique" is intended with respect to the stream hierarchy one is likely
        to query with :meth:`~music21.stream.Stream.getElementById`. For
        instance, the `.id` of a Voice should be unique in any single Measure,
        but the id's may reset from measure to measure across a Part.
        '''
        if self._id is not None:
            return self._id
        return builtins.id(self)

    @id.setter
    def id(self, new_id: int | str):
        if isinstance(new_id, int) and new_id > defaults.minIdNumberToConsiderMemoryLocation:
            msg = 'Setting an ID that could be mistaken for a memory location '
            msg += f'is discouraged: got {new_id}'
            warnings.warn(msg)
        self._id = new_id

    def mergeAttributes(self, other: Music21Object) -> None:
        '''
        Merge all elementary, static attributes. Namely,
        `id` and `groups` attributes from another music21 object.
        Can be useful for copy-like operations.

        >>> m1 = base.Music21Object()
        >>> m2 = base.Music21Object()
        >>> m1.id = 'music21Object1'
        >>> m1.groups.append('group1')
        >>> m2.mergeAttributes(m1)
        >>> m2.id
        'music21Object1'
        >>> 'group1' in m2.groups
        True
        '''
        if other.id != id(other):
            self.id = other.id
        self.groups = copy.deepcopy(other.groups)

    def _deepcopySubclassable(self: _M21T,
                              memo: dict[int, t.Any] | None = None,
                              *,
                              ignoreAttributes: set[str] | None = None) -> _M21T:
        '''
        Subclassable __deepcopy__ helper so that the same attributes
        do not need to be called for each Music21Object subclass.

        ignoreAttributes is a set of attributes not to copy via
        the default deepcopy style. More can be passed to it.  But calling
        functions are responsible

        * Changed in v9: removeFromIgnore removed;
          never used and this is performance critical.
        '''
        defaultIgnoreSet = {'_derivation', '_activeSite', '_sites', '_cache'}
        if not self.groups:
            defaultIgnoreSet.add('groups')
        # duration is smart enough to do itself.
        # sites is smart enough to do itself

        if ignoreAttributes is None:
            ignoreAttributes = defaultIgnoreSet
        else:
            ignoreAttributes = ignoreAttributes | defaultIgnoreSet

        new = common.defaultDeepcopy(self, memo, ignoreAttributes=ignoreAttributes)
        setattr(new, '_cache', {})
        setattr(new, '_sites', Sites())
        if 'groups' in defaultIgnoreSet:
            new.groups = Groups()

        # was: keep the old ancestor but need to update the client
        # 2.1 : NO, add a derivation of __deepcopy__ to the client
        newDerivation = Derivation(client=new)
        newDerivation.origin = self
        newDerivation.method = '__deepcopy__'
        setattr(new, '_derivation', newDerivation)
        # None activeSite is correct for new value

        # must do this after copying
        new.purgeOrphans()

        return new

    def __deepcopy__(self: _M21T, memo: dict[int, t.Any] | None = None) -> _M21T:
        '''
        Helper method to copy.py's deepcopy function.  Call it from there.

        memo=None is the default as specified in copy.py

        Problem: if an attribute is defined with an underscore (_priority) but
        is also made available through a property (e.g. priority)  using dir(self)
        results in the copy happening twice. Thus, __dict__.keys() is used.

        >>> from copy import deepcopy
        >>> n = note.Note('A')
        >>> n.offset = 1.0
        >>> n.groups.append('flute')
        >>> n.groups
        ['flute']

        >>> idN = n.id
        >>> idN > 10000  # pointer
        True

        >>> b = deepcopy(n)
        >>> b.offset = 2.0

        >>> n is b
        False
        >>> b.id != n.id
        True
        >>> n.pitch.accidental = '-'
        >>> b.name
        'A'
        >>> n.offset
        1.0
        >>> b.offset
        2.0
        >>> n.groups[0] = 'bassoon'
        >>> ('flute' in n.groups, 'flute' in b.groups)
        (False, True)
        '''
        return self._deepcopySubclassable(memo)

    def __getstate__(self) -> dict[str, t.Any]:
        state = self.__dict__.copy()
        state['_derivation'] = None
        state['_activeSite'] = None
        return state

    def __setstate__(self, state: dict[str, t.Any]):
        # defining self.__dict__ upon initialization currently breaks everything
        object.__setattr__(self, '__dict__', state)  # pylint: disable=attribute-defined-outside-init

    def _reprInternal(self) -> str:
        '''
        If `x.id` is not the same as `id(x)`, then that id is used instead:

        >>> b = base.Music21Object()
        >>> b._reprInternal()
        'object at 0x129a903b1'
        >>> b.id = 'hi'
        >>> b._reprInternal()
        'id=hi'
        '''
        # hasattr is here because of Metadata.__getattr__()
        if not hasattr(self, 'id') or self.id == id(self):
            return super()._reprInternal()
        reprId = self.id
        try:
            reprId = hex(int(reprId))
        except (ValueError, TypeError):
            pass
        return f'id={reprId}'

    # --------------------------------------------------------------------------

    @property
    def hasEditorialInformation(self) -> bool:
        '''
        Returns True if there is a :class:`~music21.editorial.Editorial` object
        already associated with this object, False otherwise.

        Calling .editorial on an object will always create a new
        Editorial object, so even though a new Editorial object isn't too expensive
        to create, this property helps to prevent creating new Editorial objects
        more than is necessary.

        >>> mObj = base.Music21Object()
        >>> mObj.hasEditorialInformation
        False
        >>> mObj.editorial
        <music21.editorial.Editorial {}>
        >>> mObj.hasEditorialInformation
        True
        '''
        # anytime something is changed here, change in style.StyleMixin and vice-versa
        return not (self._editorial is None)

    @property
    def editorial(self) -> Editorial:
        '''
        a :class:`~music21.editorial.Editorial` object that stores editorial information
        (comments, footnotes, harmonic information, ficta).

        Created automatically as needed:

        >>> n = note.Note('C4')
        >>> n.editorial
        <music21.editorial.Editorial {}>
        >>> n.editorial.ficta = pitch.Accidental('sharp')
        >>> n.editorial.ficta
        <music21.pitch.Accidental sharp>
        >>> n.editorial
        <music21.editorial.Editorial {'ficta': <music21.pitch.Accidental sharp>}>
        '''
        # Dev note: because the property "editorial" shadows module editorial,
        # typing has to be in quotes.

        # anytime something is changed here, change in style.StyleMixin and vice-versa
        if self._editorial is None:
            self._editorial = Editorial()
        return self._editorial

    @editorial.setter
    def editorial(self, ed: Editorial):
        self._editorial = ed

    @property
    def hasStyleInformation(self) -> bool:
        '''
        Returns True if there is a :class:`~music21.style.Style` object
        already associated with this object, False otherwise.

        Calling .style on an object will always create a new
        Style object, so even though a new Style object isn't too expensive
        to create, this property helps to prevent creating new Styles more than
        necessary.

        >>> mObj = base.Music21Object()
        >>> mObj.hasStyleInformation
        False
        >>> mObj.style
        <music21.style.Style object at 0x10b0a2080>
        >>> mObj.hasStyleInformation
        True
        '''
        # anytime something is changed here, change in style.StyleMixin and vice-versa
        return not (self._style is None)

    @property
    def style(self) -> Style:
        '''
        Returns (or Creates and then Returns) the Style object
        associated with this object, or sets a new
        style object.  Different classes might use
        different Style objects because they might have different
        style needs (such as text formatting or bezier positioning)

        Eventually will also query the groups to see if they have
        any styles associated with them.

        >>> n = note.Note()
        >>> st = n.style
        >>> st
        <music21.style.NoteStyle object at 0x10ba96208>
        >>> st.absoluteX = 20.0
        >>> st.absoluteX
        20.0
        >>> n.style = style.Style()
        >>> n.style.absoluteX is None
        True
        '''
        # anytime something is changed here, change in style.StyleMixin and vice-versa
        if not self.hasStyleInformation:
            StyleClass = self._styleClass
            self._style = StyleClass()
        assert self._style is not None  # for mypy.
        return self._style

    @style.setter
    def style(self, newStyle: Style | None):
        self._style = newStyle

    # convenience.

    @property
    def quarterLength(self) -> OffsetQL:
        '''
        Set or Return the Duration as represented in Quarter Length, possibly as a fraction.

        Same as setting `.duration.quarterLength`.

        >>> n = note.Note()
        >>> n.quarterLength = 2.0
        >>> n.quarterLength
        2.0
        >>> n.quarterLength = 1/3
        >>> n.quarterLength
        Fraction(1, 3)
        '''
        return self.duration.quarterLength

    @quarterLength.setter
    def quarterLength(self, value: OffsetQLIn):
        self.duration.quarterLength = value

    @property
    def derivation(self) -> Derivation:
        '''
        Return the :class:`~music21.derivation.Derivation` object for this element.

        Or create one if none exists:

        >>> n = note.Note()
        >>> n.derivation
        <Derivation of <music21.note.Note C> from None>
        >>> import copy
        >>> n2 = copy.deepcopy(n)
        >>> n2.pitch.step = 'D'  # for seeing easier...
        >>> n2.derivation
        <Derivation of <music21.note.Note D> from <music21.note.Note C> via '__deepcopy__'>
        >>> n2.derivation.origin is n
        True

        Note that (for now at least) derivation.origin is NOT a weakref:

        >>> del n
        >>> n2.derivation
        <Derivation of <music21.note.Note D> from <music21.note.Note C> via '__deepcopy__'>
        >>> n2.derivation.origin
        <music21.note.Note C>
        '''
        if self._derivation is None:
            self._derivation = Derivation(client=self)
        return self._derivation

    @derivation.setter
    def derivation(self, newDerivation: Derivation | None) -> None:
        self._derivation = newDerivation

    def clearCache(self, **keywords) -> None:
        '''
        A number of music21 attributes (especially with Chords and RomanNumerals, etc.)
        are expensive to compute and are therefore cached.  Generally speaking
        objects are responsible for making sure that their own caches are up to date,
        but a power user might want to do something in an unusual way (such as manipulating
        private attributes on a Pitch object) and need to be able to clear caches.

        That's what this is here for.  If all goes well, you'll never need to call it
        unless you're expanding music21's core functionality.

        `**keywords` is not used in Music21Object but is included for subclassing.

        Look at :func:`~music21.common.decorators.cacheMethod` for the other half of this
        utility.

        * New in v6: exposes previously hidden functionality.
        '''
        # do not replace with self._cache.clear() -- leaves terrible
        # state for shallow copies.
        self._cache = {}

    @overload
    def getOffsetBySite(
        self,
        site: stream.Stream | None,
        *,
        returnSpecial: t.Literal[False] = False,
    ) -> OffsetQL:
        return 0.0  # dummy until Astroid #1015 is fixed.  Replace with ...

    @overload
    def getOffsetBySite(
        self,
        site: stream.Stream | None,
        *,
        returnSpecial: bool = False,
    ) -> OffsetQL | OffsetSpecial:
        return 0.0  # dummy until Astroid #1015 is fixed.  Replace with ...
        # using bool instead of t.Literal[True] because of

    def getOffsetBySite(
        self,
        site: stream.Stream | None,
        *,
        returnSpecial: bool = False,
    ) -> OffsetQL | OffsetSpecial:
        '''
        If this class has been registered in a container such as a Stream,
        that container can be provided here, and the offset in that object
        can be returned.

        >>> n = note.Note('A-4')  # a Music21Object
        >>> n.offset = 30
        >>> n.getOffsetBySite(None)
        30.0

        >>> s1 = stream.Stream()
        >>> s1.id = 'containingStream'
        >>> s1.insert(20 / 3, n)
        >>> n.getOffsetBySite(s1)
        Fraction(20, 3)
        >>> float(n.getOffsetBySite(s1))
        6.6666...

        n.getOffsetBySite(None) should still return 30.0

        >>> n.getOffsetBySite(None)
        30.0

        If the Stream does not contain the element and the element is not derived from
        an element that does, then a SitesException is raised:

        >>> s2 = stream.Stream()
        >>> s2.id = 'notContainingStream'
        >>> n.getOffsetBySite(s2)
        Traceback (most recent call last):
        music21.sites.SitesException: an entry for this object <music21.note.Note A-> is not
              stored in stream <music21.stream.Stream notContainingStream>

        Consider this use of derivations:

        >>> import copy
        >>> nCopy = copy.deepcopy(n)
        >>> nCopy.derivation
        <Derivation of <music21.note.Note A-> from <music21.note.Note A-> via '__deepcopy__'>
        >>> nCopy.getOffsetBySite(s1)
        Fraction(20, 3)

        nCopy can still find the offset of `n` in `s1`!
        This is the primary difference between element.getOffsetBySite(stream)
        and stream.elementOffset(element)

        >>> s1.elementOffset(nCopy)
        Traceback (most recent call last):
        music21.sites.SitesException: an entry for this object ... is not
            stored in stream <music21.stream.Stream containingStream>

        If the object is stored at the end of the Stream, then the highest time
        is usually returned:

        >>> s3 = stream.Stream()
        >>> n3 = note.Note(type='whole')
        >>> s3.append(n3)
        >>> rb = bar.Barline()
        >>> s3.storeAtEnd(rb)  # s3.rightBarline = rb would do the same...
        >>> rb.getOffsetBySite(s3)
        4.0

        However, setting returnSpecial to True will return OffsetSpecial.AT_END

        >>> rb.getOffsetBySite(s3, returnSpecial=True)
        <OffsetSpecial.AT_END>

        Even with returnSpecial normal offsets are still returned as a float or Fraction:

        >>> n3.getOffsetBySite(s3, returnSpecial=True)
        0.0

        * Changed in v7: stringReturns renamed to returnSpecial.
          Returns an OffsetSpecial Enum.
        '''
        if site is None:
            return self._naiveOffset

        try:
            a = None
            tryOrigin: Music21Object = self
            originMemo = set()
            maxSearch = 100
            while a is None:
                try:
                    a = site.elementOffset(tryOrigin, returnSpecial=returnSpecial)
                except AttributeError as ae:
                    raise SitesException(
                        f'You were using {site!r} as a site, when it is not a Stream...'
                    ) from ae
                except Music21Exception as e:  # currently StreamException, but will change
                    if tryOrigin in site._endElements:
                        if returnSpecial is True:
                            return OffsetSpecial.AT_END
                        else:
                            return site.highestTime

                    possiblyNoneTryOrigin = self.derivation.origin
                    if possiblyNoneTryOrigin is None:
                        raise e
                    tryOrigin = possiblyNoneTryOrigin

                    if id(tryOrigin) in originMemo:
                        raise e
                    originMemo.add(id(tryOrigin))
                    maxSearch -= 1  # prevent infinite recursive searches...
                    if maxSearch < 0:
                        raise e
            return a
        except SitesException as se:
            raise SitesException(
                f'an entry for this object {self!r} is not stored in stream {site!r}'
            ) from se

    def setOffsetBySite(self,
                        site: stream.Stream | None,
                        value: OffsetQLIn):
        '''
        Change the offset for a site.  These are equivalent:

            n1.setOffsetBySite(stream1, 20)

        and

            stream1.setElementOffset(n1, 20)

        Which you choose to use will depend on whether you are iterating over a list
        of notes (etc.) or streams.

        >>> import music21
        >>> aSite = stream.Stream()
        >>> aSite.id = 'aSite'
        >>> a = music21.Music21Object()
        >>> aSite.insert(0, a)
        >>> aSite.setElementOffset(a, 20)
        >>> a.setOffsetBySite(aSite, 30)
        >>> a.getOffsetBySite(aSite)
        30.0

        And if it isn't in a Stream? Raises an exception and the offset does not change.

        >>> b = note.Note('D')
        >>> b.setOffsetBySite(aSite, 40)
        Traceback (most recent call last):
        music21.exceptions21.StreamException: Cannot set the offset for element
            <music21.note.Note D>, not in Stream <music21.stream.Stream aSite>.

        >>> b.offset
        0.0

        Setting offset for `None` changes the "naive offset" of an object:

        >>> b.setOffsetBySite(None, 32)
        >>> b.offset
        32.0
        >>> b.activeSite is None
        True

        Running `setOffsetBySite` also changes the `activeSite` of the object.
        '''
        if site is not None:
            site.setElementOffset(self, value)
        else:
            if isinstance(value, int):
                value = float(value)
            self._naiveOffset = value

    def getOffsetInHierarchy(
        self,
        site: stream.Stream | None
    ) -> OffsetQL:
        '''
        For an element which may not be in site, but might be in a Stream in site (or further
        in streams), find the cumulative offset of the element in that site.

        >>> s = stream.Score(id='mainScore')
        >>> p = stream.Part()
        >>> m = stream.Measure()
        >>> n = note.Note()
        >>> m.insert(5.0, n)
        >>> p.insert(10.0, m)
        >>> s.insert(0.0, p)
        >>> n.getOffsetInHierarchy(s)
        15.0

        If no hierarchy beginning with site contains the element
        and the element is not derived from
        an element that does, then a SitesException is raised:

        >>> s2 = stream.Score(id='otherScore')
        >>> n.getOffsetInHierarchy(s2)
        Traceback (most recent call last):
        music21.sites.SitesException: Element <music21.note.Note C>
            is not in hierarchy of <music21.stream.Score otherScore>

        But if the element is derived from an element in
        a hierarchy then it can get the offset:

        >>> n2 = n.transpose('P5')
        >>> n2.derivation.origin is n
        True
        >>> n2.derivation.method
        'transpose'
        >>> n2.getOffsetInHierarchy(s)
        15.0

        There is no corresponding `.setOffsetInHierarchy()`
        since it's unclear what that would mean.

        See also :meth:`music21.stream.iterator.RecursiveIterator.currentHierarchyOffset`
        for a method that is about 10x faster when running through a recursed stream.

        * New in v3.

        OMIT_FROM_DOCS

        Timing: 113microseconds for a search vs 1 microsecond for getOffsetBySite
        vs 0.4 for elementOffset.  Hence the short-circuit for easy looking below...

        TODO: If timing permits, replace .flatten() w/ and w/o retainContainers with this routine.

        Currently not possible; for instance, if b = bwv66.6

        %timeit b = corpus.parse('bwv66.6') -- 24.8ms
        %timeit b = corpus.parse('bwv66.6'); b.flatten() -- 42.9ms
        %timeit b = corpus.parse('bwv66.6'); b.recurse().stream() -- 83.1ms
        '''
        try:
            return self.getOffsetBySite(site)
        except SitesException:
            pass

        # do not use priorityTarget, just slows things down because will need to search
        # all anyhow, since site is not in self.sites.yieldSites()
        for cs in self.contextSites():
            if cs.site is site:
                return cs.offset

        raise SitesException(f'Element {self} is not in hierarchy of {site}')

    def getSpannerSites(self,
                        spannerClassList: Iterable | None = None
                        ) -> list[spanner.Spanner]:
        '''
        Return a list of all :class:`~music21.spanner.Spanner` objects
        (or Spanner subclasses) that contain
        this element. This method provides a way for
        objects to be aware of what Spanners they
        reside in. Note that Spanners are not Streams
        but specialized Music21Objects that use a
        Stream subclass, SpannerStorage, internally to keep track
        of the elements that are spanned.

        >>> c = note.Note('C4')
        >>> d = note.Note('D4')
        >>> slur1 = spanner.Slur(c, d)
        >>> c.getSpannerSites() == [slur1]
        True

        Note that not all Spanners are in the spanner module. They
        tend to reside in modules closer to their musical function:

        >>> cresc = dynamics.Crescendo(d, c)

        The order that Spanners are returned is by sortTuple.  For spanners
        created the same way and in the same order, the order returned will
        be consistent:

        >>> d.getSpannerSites() == [slur1, cresc]
        True

        Optionally a class name or list of class names (as Classes or strings)
        can be specified and only Spanners of that class will be returned

        >>> dim = dynamics.Diminuendo(c, d)
        >>> d.getSpannerSites(dynamics.Diminuendo) == [dim]
        True

        A larger class name can be used to get all subclasses:

        >>> d.getSpannerSites(dynamics.DynamicWedge) == [cresc, dim]
        True
        >>> d.getSpannerSites(['Slur', 'Diminuendo']) == [slur1, dim]
        True

        Note that the order of spanners returned from this routine can vary, so
        changing to a set is useful for comparisons

        >>> set(d.getSpannerSites(['Slur', 'Diminuendo'])) == {dim, slur1}
        True


        Example: see which pairs of notes are in the same slur.

        >>> e = note.Note('E4')
        >>> slur2 = spanner.Slur(c, e)

        >>> for n in [c, d, e]:
        ...    nSlurs = n.getSpannerSites(spanner.Slur)
        ...    for nOther in [c, d, e]:
        ...        if n is nOther:
        ...            continue
        ...        nOtherSlurs = nOther.getSpannerSites(spanner.Slur)
        ...        for thisSlur in nSlurs:
        ...            if thisSlur in nOtherSlurs:
        ...               print(f'{n.name} shares a slur with {nOther.name}')
        C shares a slur with D
        C shares a slur with E
        D shares a slur with C
        E shares a slur with C
        '''
        found = self.sites.getSitesByClass('SpannerStorage')
        post: list[spanner.Spanner] = []
        if spannerClassList is not None:
            if not common.isIterable(spannerClassList):
                spannerClassList = [spannerClassList]

        for obj in found:
            if obj is None:  # pragma: no cover
                continue
            if spannerClassList is None:
                post.append(obj.client)
            else:
                for spannerClass in spannerClassList:
                    if spannerClass in obj.client.classSet:
                        post.append(obj.client)
                        break

        return sorted(post, key=lambda x: x.sortTuple())

    def purgeOrphans(self, excludeStorageStreams=True) -> None:
        '''
        A Music21Object may, due to deep copying or other reasons,
        have a site (with an offset) which
        no longer contains the Music21Object. These lingering sites
        are called orphans. This method gets rid of them.

        The `excludeStorageStreams` are SpannerStorage and VariantStorage.
        '''
        # environLocal.printDebug(['purging orphans'])
        orphans = []
        # TODO: how can this be optimized to not use getSites, to
        # not unwrap weakrefs?
        for s in self.sites.yieldSites(excludeNone=True):
            # of the site does not actually have this Music21Object in
            # its elements list, it is an orphan and should be removed
            # note: this permits non-site context Streams to continue
            if s.isStream and not s.hasElement(self):
                if excludeStorageStreams:
                    # only get those that are not Storage Streams
                    if ('SpannerStorage' not in s.classes
                            and 'VariantStorage' not in s.classes):
                        # environLocal.printDebug(['removing orphan:', s])
                        orphans.append(id(s))
                else:  # get all
                    orphans.append(id(s))
        for i in orphans:
            self.sites.removeById(i)
            p = self._getActiveSite()  # this can be simplified.
            if p is not None and id(p) == i:
                # noinspection PyArgumentList
                self._setActiveSite(None)

    def purgeLocations(self, rescanIsDead=False) -> None:
        '''
        Remove references to all locations in objects that no longer exist.
        '''
        # NOTE: this method is overridden on Spanner
        # and Variant, so not an easy fix to remove...
        self.sites.purgeLocations(rescanIsDead=rescanIsDead)

    # --------------------------------------------------------------------------------
    # contexts...

    @overload
    def getContextByClass(
        self,
        className: type[_M21T],
        *,
        getElementMethod=ElementSearch.AT_OR_BEFORE,
        sortByCreationTime=False,
        followDerivation=True,
        priorityTargetOnly=False,
    ) -> _M21T | None:
        return None  # until Astroid #1015

    @overload
    def getContextByClass(
        self,
        className: str | None,
        *,
        getElementMethod=ElementSearch.AT_OR_BEFORE,
        sortByCreationTime=False,
        followDerivation=True,
        priorityTargetOnly=False,
    ) -> Music21Object | None:
        return None  # until Astroid #1015

    def getContextByClass(
        self,
        className: type[_M21T] | str | None,
        *,
        getElementMethod: ElementSearch = ElementSearch.AT_OR_BEFORE,
        sortByCreationTime=False,
        followDerivation=True,
        priorityTargetOnly=False,
    ) -> _M21T | Music21Object | None:
        # noinspection PyShadowingNames
        '''
        A very powerful method in music21 of fundamental importance: Returns
        the element matching the className that is closest to this element in
        its current hierarchy (or the hierarchy of the derivation origin unless
        `followDerivation` is False).  For instance, take this stream of changing time
        signatures:

        >>> p = converter.parse('tinynotation: 3/4 C4 D E 2/4 F G A B 1/4 c')
        >>> p
        <music21.stream.Part 0x104ce64e0>

        >>> p.show('t')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note F>
            {1.0} <music21.note.Note G>
        {5.0} <music21.stream.Measure 3 offset=5.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
        {7.0} <music21.stream.Measure 4 offset=7.0>
            {0.0} <music21.meter.TimeSignature 1/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.bar.Barline type=final>

        Let's get the last two notes of the piece, the B and high c:

        >>> m4 = p.measure(4)
        >>> c = m4.notes.first()
        >>> c
        <music21.note.Note C>

        >>> m3 = p.measure(3)
        >>> b = m3.notes.last()
        >>> b
        <music21.note.Note B>

        Now when we run `getContextByClass(meter.TimeSignature)` on c, we get a
        time signature of 1/4.

        >>> c.getContextByClass(meter.TimeSignature)
        <music21.meter.TimeSignature 1/4>

        Doing what we just did wouldn't be hard to do with other methods,
        though `getContextByClass` makes it easier.  But the time signature
        context for b would be much harder to get without this method, since in
        order to do it, it searches backwards within the measure, finds that
        there's nothing there.  It goes to the previous measure and searches
        that one backwards until it gets the proper TimeSignature of 2/4:

        >>> b.getContextByClass(meter.TimeSignature)
        <music21.meter.TimeSignature 2/4>

        For backwards compatibility you can also pass in a string of the
        class name:

        >>> b.getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 2/4>

        But if you use Python typing or a typing-aware IDE, then the first call
        (with class name) will signal that it is returning a TimeSignature object
        and allow for error detection, autocomplete, etc.  The latter call
        (with string) will only know that some Music21Object was returned.

        The method is smart enough to stop when it gets to the beginning of the
        part.  This is all you need to know for most uses.  The rest of the
        docs are for advanced uses:

        The method searches both Sites as well as associated objects to find a
        matching class. Returns `None` if no match is found.

        A reference to the caller is required to find the offset of the object
        of the caller.

        The caller may be a Sites reference from a lower-level object.  If so,
        we can access the location of that lower-level object. However, if we
        need a flat representation, the caller needs to be the source Stream,
        not its Sites reference.

        The `getElementMethod` is an enum value (new in v7) from
        :class:`~music21.common.enums.ElementSearch` that selects which
        Stream method is used to get elements for searching. (The historical form
        of supplying one of the following values as a string is also supported.)

        >>> from music21.common.enums import ElementSearch
        >>> [x for x in ElementSearch]
        [<ElementSearch.BEFORE>,
         <ElementSearch.AFTER>,
         <ElementSearch.AT_OR_BEFORE>,
         <ElementSearch.AT_OR_AFTER>,
         <ElementSearch.BEFORE_OFFSET>,
         <ElementSearch.AFTER_OFFSET>,
         <ElementSearch.AT_OR_BEFORE_OFFSET>,
         <ElementSearch.AT_OR_AFTER_OFFSET>,
         <ElementSearch.BEFORE_NOT_SELF>,
         <ElementSearch.AFTER_NOT_SELF>,
         <ElementSearch.ALL>]

        The "after" do forward contexts -- looking ahead.

        Demonstrations of these keywords:

        Because `b` is a `Note`, `.getContextByClass(note.Note)` will only find itself:

        >>> b.getContextByClass(note.Note) is b
        True

        To get the previous `Note`, use `getElementMethod=ElementSearch.BEFORE`:

        >>> a = b.getContextByClass(note.Note, getElementMethod=ElementSearch.BEFORE)
        >>> a
        <music21.note.Note A>

        This is similar to `.previous(note.Note)`, though that method is a bit more
        sophisticated:

        >>> b.previous(note.Note)
        <music21.note.Note A>

        To get the following `Note` use `getElementMethod=ElementSearch.AFTER`:

        >>> c = b.getContextByClass(note.Note, getElementMethod=ElementSearch.AFTER)
        >>> c
        <music21.note.Note C>

        This is similar to `.next(note.Note)`, though, again, that method is a bit more
        sophisticated:

        >>> b.next(note.Note)
        <music21.note.Note C>

        A Stream might contain several elements at the same offset, leading to
        potentially surprising results where searching by `ElementSearch.AT_OR_BEFORE`
        does not find an element that is technically the NEXT node but still at 0.0:

        >>> s = stream.Stream()
        >>> s.insert(0, clef.BassClef())
        >>> s.next()
        <music21.clef.BassClef>
        >>> s.getContextByClass(clef.Clef) is None
        True
        >>> s.getContextByClass(clef.Clef, getElementMethod=ElementSearch.AT_OR_AFTER)
        <music21.clef.BassClef>

        This can be remedied by explicitly searching by offsets:

        >>> s.getContextByClass(clef.Clef, getElementMethod=ElementSearch.AT_OR_BEFORE_OFFSET)
        <music21.clef.BassClef>

        Or by not limiting the search by temporal position at all:

        >>> s.getContextByClass(clef.Clef, getElementMethod=ElementSearch.ALL)
        <music21.clef.BassClef>

        Notice that if searching for a `Stream` context, the element is not
        guaranteed to be in that Stream.  This is obviously true in this case:

        >>> p2 = stream.Part()
        >>> m = stream.Measure(number=1)
        >>> p2.insert(0, m)
        >>> n = note.Note('D')
        >>> m.insert(2.0, n)
        >>> try:
        ...     n.getContextByClass(stream.Part).elementOffset(n)
        ... except Music21Exception:
        ...     print('not there')
        not there

        But it is less clear with something like this:

        >>> import copy
        >>> n2 = copy.deepcopy(n)
        >>> try:
        ...     n2.getContextByClass(stream.Measure).elementOffset(n2)
        ... except Music21Exception:
        ...     print('not there')
        not there

        A measure context is being found, but only through the derivation chain.

        >>> n2.getContextByClass(stream.Measure)
        <music21.stream.Measure 1 offset=0.0>

        To prevent this error, use the `followDerivation=False` setting

        >>> print(n2.getContextByClass(stream.Measure, followDerivation=False))
        None

        Or if you want the offset of the element following the derivation chain,
        call `getOffsetBySite()` on the object:

        >>> n2.getOffsetBySite(n2.getContextByClass(stream.Measure))
        2.0


        Raises `ValueError` if `getElementMethod` is not a value in `ElementSearch`.

        >>> n2.getContextByClass(expressions.TextExpression, getElementMethod='invalid')
        Traceback (most recent call last):
        ValueError: Invalid getElementMethod: invalid

        Raises `ValueError` for incompatible values `followDerivation=True`
        and `priorityTargetOnly=True`.

        * Changed in v5.7: added followDerivation=False and made
          everything but the class keyword only
        * New in v6: added priorityTargetOnly -- see contextSites for description.
        * New in v7: added getElementMethod `all` and `ElementSearch` enum.
        * Changed in v8: class-based calls return properly typed items.  Putting
          multiple types into className (never documented) is no longer allowed.

        OMIT_FROM_DOCS

        Testing that this works:

        >>> import gc
        >>> _ = gc.collect()
        >>> for site, positionStart, searchType in b.contextSites(
        ...                                 returnSortTuples=True,
        ...                                 sortByCreationTime=False,
        ...                                 followDerivation=True
        ...                                 ):
        ...     print(site, positionStart, searchType)
        <music21.stream.Measure 3 offset=5.0> SortTuple(atEnd=0, offset=1.0, ...) elementsFirst
        <music21.stream.Part 0x1118cadd8> SortTuple(atEnd=0, offset=6.0, ...) flatten
        '''
        OFFSET_METHODS = [
            ElementSearch.BEFORE_OFFSET,
            ElementSearch.AFTER_OFFSET,
            ElementSearch.AT_OR_BEFORE_OFFSET,
            ElementSearch.AT_OR_AFTER_OFFSET,
        ]
        BEFORE_METHODS = [
            ElementSearch.BEFORE,
            ElementSearch.BEFORE_OFFSET,
            ElementSearch.AT_OR_BEFORE,
            ElementSearch.AT_OR_BEFORE_OFFSET,
            ElementSearch.BEFORE_NOT_SELF,
        ]
        AFTER_METHODS = [
            ElementSearch.AFTER,
            ElementSearch.AFTER_OFFSET,
            ElementSearch.AT_OR_AFTER,
            ElementSearch.AT_OR_AFTER,
            ElementSearch.AT_OR_AFTER_OFFSET,
            ElementSearch.AFTER_NOT_SELF,
        ]
        AT_METHODS = [
            ElementSearch.AT_OR_BEFORE,
            ElementSearch.AT_OR_AFTER,
            ElementSearch.AT_OR_BEFORE_OFFSET,
            ElementSearch.AT_OR_AFTER_OFFSET,
        ]
        NOT_SELF_METHODS = [
            ElementSearch.BEFORE_NOT_SELF,
            ElementSearch.AFTER_NOT_SELF,
        ]
        # ALL is just a no-op
        def payloadExtractor(checkSite, flatten, innerPositionStart):
            '''
            change the site (stream) to a Tree (using caches if possible),
            then find the node before (or after) the positionStart and
            return the element there or None.

            flatten can be True, 'semiFlat', or False.
            '''
            classList = None if not className else (className,)
            siteTree = checkSite.asTree(flatten=flatten, classList=classList)
            if getElementMethod in OFFSET_METHODS:
                # these methods match only by offset.  Used in .getBeat among other places
                if getElementMethod in (ElementSearch.BEFORE_OFFSET,
                                        ElementSearch.AT_OR_AFTER_OFFSET):
                    innerPositionStart = ZeroSortTupleLow.modify(offset=innerPositionStart.offset)
                else:
                    innerPositionStart = ZeroSortTupleHigh.modify(offset=innerPositionStart.offset)

            if getElementMethod in BEFORE_METHODS:
                contextNode = siteTree.getNodeBefore(innerPositionStart)
            else:
                contextNode = siteTree.getNodeAfter(innerPositionStart)

            if contextNode is not None:
                payload = contextNode.payload
                return payload
            else:
                return None

        def wellFormed(checkContextEl, checkSite) -> bool:
            '''
            Long explanation for a short method.

            It is possible for a contextEl to be returned that contradicts the
            'Before' or 'After' criterion due to the following:

            (I'll take the example of Before; After is much harder
            to construct, but possible).

            Assume that s is a Score, and tb2 = s.flatten()[1] and tb1 is the previous element
            (would be s.flatten()[0]) -- both are at offset 0 in s and are of the same class
            (so same sort order and priority) and are thus ordered entirely by insert
            order.

            in s we have the following.

            s.sortTuple   = 0.0 <0.-20.0>  # not inserted
            tb1.sortTuple = 0.0 <0.-31.1>
            tb2.sortTuple = 0.0 <0.-31.2>

            in s.flatten() we have:

            s.flatten().sortTuple = 0.0 <0.-20.0>  # not inserted
            tb1.sortTuple         = 0.0 <0.-31.3>
            tb2.sortTuple         = 0.0 <0.-31.4>

            Now tb2 is declared through s.flatten()[1], so its activeSite
            is s.flatten().  Calling .previous() finds tb1 in s.flatten().  This is normal.

            tb1 calls .previous().  Search of first site finds nothing before tb1,
            so .getContextByClass() is ready to return None.  But other sites need to be checked

            Search returns to s.  .getContextByClass() asks is there anything before tb1's
            sort tuple of 0.0 <0.-31.3> (.3 is the insertIndex) in s?  Yes, it's tb2 at
            0.0 <0.-31.2> (because s was created before s.flatten(), the insert indices of objects
            in s are lower than the insert indices of objects in s.flatten() (perhaps insert indices
            should be eventually made global within the context of a stream, but not global
            overall? but that wasn't the solution here).  So we go back to tb2 in s. Then in
            theory we should go to tb1 in s, then s, then None.  This would have certain
            elements appear twice in a .previous() search, which is not optimal, but wouldn't be
            such a huge bug to make this method necessary.

            That'd be the only bug that would occur if we did: sf = s.flatten(), tb2 = sf[1]. But
            consider the exact phrasing above:  tb2 = s.flatten()[1].
            s.flatten() is created for an instant,
            it is assigned to tb2's ._activeSite via weakRef, and then tb2's sortTuple is set
            via this temporary stream.

            Suppose tb2 is from that temp s.flatten()[1].  Then tb1 = tb2.previous() which is found
            in s.flatten().  Suppose then that for some reason s._cache['flat'] gets cleaned up
            (It was a bug that s._cache was being cleaned by the positioning of notes during
            s_flat's setOffset,
            but _cache cleanups are allowed to happen at any time,
            so it's not a bug that it's being cleaned; assuming that it wouldn't be cleaned
            would be the bug) and garbage collection runs.

            Now we get tb1.previous() would get tb2 in s. Okay, it's redundant but not a huge deal,
            and tb2.previous() gets tb1.  tb1's ._activeSite is still a weakref to s.flatten().
            When tb1's getContextByClass() is called, it needs its .sortTuple().  This looks
            first at .activeSite.  That is None, so it gets it from .offset which is the .offset
            of the last .activeSite (even if it is dead.  A lot of code depends on .offset
            still being available if .activeSite dies, so changing that is not an option for now).
            So its sortTuple is 0.0 <0.-31.3>. which has a .previous() of tb2 in s, which can
            call previous can get tb1, etc. So with terrible timing of cache cleanups and
            garbage collecting, it's possible to get an infinite loop.

            There may be ways to set activeSite on .getContextByClass() call such that this routine
            is not necessary, but I could not find one that was not disruptive for normal
            usages.

            There are some possible issues that one could raise about "wellFormed".
            Suppose for instance, that in one stream (b) we have [tb1, tb2] and
            then in another stream context (a), created earlier,
            we have [tb0, tb1, tb2].  tb1 is set up with (b) as an activeSite. Finding nothing
            previous, it goes to (a) and finds tb2; it then discovers that in (a), tb2 is after
            tb1, so it returns None for this context.  One might say, "wait a second, why
            isn't tb0 returned? It's going to be skipped." To this, I would answer, the original
            context in which .previous() or .getContextByClass() was called was (b). There is
            no absolute obligation to find what was previous in a different site context. It is
            absolutely fair game to say, "there's nothing prior to tb1".  Then why even
            search other streams/sites? Because it's quite common to create a new site
            for say a single measure or .getElementsByOffset(), etc., so that when leaving
            this extracted section, one wants to see how that fits into a larger stream hierarchy.
            '''
            try:
                selfSortTuple = self.sortTuple(checkSite, raiseExceptionOnMiss=True)
                contextSortTuple = checkContextEl.sortTuple(checkSite, raiseExceptionOnMiss=True)
            except SitesException:
                # might be raised by selfSortTuple; should not be by contextSortTuple.
                # It just means that selfSortTuple isn't in the same stream
                # as contextSortTuple, such as
                # when crossing measure borders.  Thus, it's well-formed.
                return True

            if getElementMethod in BEFORE_METHODS and selfSortTuple < contextSortTuple:
                # print(getElementMethod, selfSortTuple.shortRepr(),
                #       contextSortTuple.shortRepr(), self, contextEl)
                return False
            elif getElementMethod in AFTER_METHODS and selfSortTuple > contextSortTuple:
                # print(getElementMethod, selfSortTuple.shortRepr(),
                #       contextSortTuple.shortRepr(), self, contextEl)
                return False
            else:
                return True

        if getElementMethod not in ElementSearch:
            raise ValueError(f'Invalid getElementMethod: {getElementMethod}')

        if priorityTargetOnly and followDerivation:
            raise ValueError('priorityTargetOnly and followDerivation cannot both be True')

        if getElementMethod in AT_METHODS and className in self.classSet:
            return self

        for site, positionStart, searchType in self.contextSites(
            returnSortTuples=True,
            sortByCreationTime=sortByCreationTime,
            followDerivation=followDerivation,
            priorityTargetOnly=priorityTargetOnly,
        ):
            if searchType in ('elementsOnly', 'elementsFirst'):
                contextEl = payloadExtractor(site,
                                             flatten=False,
                                             innerPositionStart=positionStart)

                if contextEl is not None and wellFormed(contextEl, site):
                    try:
                        site.coreSelfActiveSite(contextEl)
                    except SitesException:
                        pass
                    return contextEl
                # otherwise, continue to check for flattening...

            if searchType != 'elementsOnly':  # flatten or elementsFirst
                if (getElementMethod in AFTER_METHODS
                        and (not className
                             or className in site.classSet)):
                    if getElementMethod in NOT_SELF_METHODS and self is site:
                        pass
                    elif getElementMethod not in NOT_SELF_METHODS:  # for 'After' we can't do the
                        # containing site because that comes before.
                        return site  # if the site itself is the context, return it...

                contextEl = payloadExtractor(site,
                                             flatten='semiFlat',
                                             innerPositionStart=positionStart)
                if contextEl is not None and wellFormed(contextEl, site):
                    try:
                        site.coreSelfActiveSite(contextEl)
                    except SitesException:
                        pass
                    return contextEl

                if (getElementMethod in BEFORE_METHODS
                        and (not className
                             or className in site.classSet)):
                    if getElementMethod in NOT_SELF_METHODS and self is site:
                        pass
                    else:
                        return site  # if the site itself is the context, return it...

                # otherwise, continue to check in next contextSite.

        # nothing found...
        return None


    @overload
    def contextSites(
        self,
        *,
        returnSortTuples: t.Literal[True],
        callerFirst=None,
        memo=None,
        offsetAppend: OffsetQL = 0.0,
        sortByCreationTime: t.Literal['reverse'] | bool = False,
        priorityTarget=None,
        followDerivation=True,
        priorityTargetOnly=False,
    ) -> Generator[ContextSortTuple, None, None]:
        pass

    @overload
    def contextSites(
        self,
        *,
        callerFirst=None,
        memo=None,
        offsetAppend: OffsetQL = 0.0,
        sortByCreationTime: t.Literal['reverse'] | bool = False,
        priorityTarget=None,
        returnSortTuples: t.Literal[False] = False,
        followDerivation=True,
        priorityTargetOnly=False,
    ) -> Generator[ContextTuple, None, None]:
        pass


    def contextSites(
        self,
        *,
        callerFirst=None,
        memo=None,
        offsetAppend: OffsetQL = 0.0,
        sortByCreationTime: t.Literal['reverse'] | bool = False,
        priorityTarget=None,
        returnSortTuples: bool = False,
        followDerivation=True,
        priorityTargetOnly=False,
    ) -> Generator[ContextTuple | ContextSortTuple, None, None]:
        '''
        A generator that returns a list of namedtuples of sites to search for a context...

        Each tuple contains three elements:

        .site --  Stream object
        .offset -- the offset or position (sortTuple) of this element in that Stream
        .recurseType -- the way of searching that should be applied to search for a context.

        The recurseType values are all music21.stream.enums.RecurseType:

            * FLATTEN -- flatten the stream and then look from this offset backwards.

            * ELEMENTS_ONLY -- only search the stream's personal
               elements from this offset backwards

            * ELEMENTS_FIRST -- search this stream backwards,
               and then flatten and search backwards

        >>> c = corpus.parse('bwv66.6')
        >>> c.id = 'bach'
        >>> n = c[2][4][2]
        >>> n
        <music21.note.Note G#>

        Returning sortTuples are important for distinguishing the order of multiple sites
        at the same offset.

        >>> for csTuple in n.contextSites(returnSortTuples=True):
        ...      yClearer = (csTuple.site, csTuple.offset.shortRepr(), csTuple.recurseType)
        ...      print(yClearer)
        (<music21.stream.Measure 3 offset=9.0>, '0.5 <0.20...>', <RecursionType.ELEMENTS_FIRST>)
        (<music21.stream.Part Alto>, '9.5 <0.20...>', <RecursionType.FLATTEN>)
        (<music21.stream.Score bach>, '9.5 <0.20...>', <RecursionType.ELEMENTS_ONLY>)

        Streams have themselves as the first element in their context sites, at position
        zero and classSortOrder negative infinity.

        This example shows the context sites for Measure 3 of the
        Alto part. We will get the measure object using direct access to
        indices to ensure that no other temporary
        streams are created; normally, we would do `c.parts['#Alto'].measure(3)`.

        >>> m = c.parts['#Alto'].getElementsByClass(stream.Measure)[3]
        >>> m
        <music21.stream.Measure 3 offset=9.0>

        If returnSortTuples is true then ContextSortTuples are returned, where the
        second element is a SortTuple:

        >>> for csTuple in m.contextSites(returnSortTuples=True):
        ...     print(csTuple)
        ContextSortTuple(site=<music21.stream.Measure 3 offset=9.0>,
                         offset=SortTuple(atEnd=0, offset=0.0, priority=-inf, ...),
                         recurseType=<RecursionType.ELEMENTS_FIRST>)
        ContextSortTuple(...)
        ContextSortTuple(...)

        Because SortTuples are so detailed, we'll use their `shortRepr()` to see the
        values, removing the insertIndex because it changes from run to run:

        >>> for csTuple in m.contextSites(returnSortTuples=True):
        ...      yClearer = (csTuple.site, csTuple.offset.shortRepr(), csTuple.recurseType)
        ...      print(yClearer)
        (<music21.stream.Measure 3 offset=9.0>, '0.0 <-inf.-20...>', <RecursionType.ELEMENTS_FIRST>)
        (<music21.stream.Part Alto>, '9.0 <0.-20...>', <RecursionType.FLATTEN>)
        (<music21.stream.Score bach>, '9.0 <0.-20...>', <RecursionType.ELEMENTS_ONLY>)

        Here we make a copy of the earlier measure, and we see that its contextSites
        follow the derivationChain from the original measure and still find the Part
        and Score of the original Measure 3 (and also the original Measure 3)
        even though mCopy is not in any of these objects.

        >>> import copy
        >>> mCopy = copy.deepcopy(m)
        >>> mCopy.number = 3333
        >>> for csTuple in mCopy.contextSites():
        ...      print(csTuple, mCopy in csTuple.site)
        ContextTuple(site=<music21.stream.Measure 3333 offset=0.0>,
                     offset=0.0,
                     recurseType=<RecursionType.ELEMENTS_FIRST>) False
        ContextTuple(site=<music21.stream.Measure 3 offset=9.0>,
                     offset=0.0,
                     recurseType=<RecursionType.ELEMENTS_FIRST>) False
        ContextTuple(site=<music21.stream.Part Alto>,
                     offset=9.0,
                     recurseType=<RecursionType.FLATTEN>) False
        ContextTuple(site=<music21.stream.Score bach>,
                     offset=9.0,
                     recurseType=<RecursionType.ELEMENTS_ONLY>) False

        If followDerivation were False, then the Part and Score would not be found.

        >>> for csTuple in mCopy.contextSites(followDerivation=False):
        ...     print(csTuple)
        ContextTuple(site=<music21.stream.Measure 3333 offset=0.0>,
                     offset=0.0,
                     recurseType=<RecursionType.ELEMENTS_FIRST>)

        >>> partIterator = c.parts
        >>> m3 = partIterator[1].measure(3)
        >>> for csTuple in m3.contextSites():
        ...      print(csTuple)
        ContextTuple(site=<music21.stream.Measure 3 offset=9.0>,
                     offset=0.0,
                     recurseType=<RecursionType.ELEMENTS_FIRST>)
        ContextTuple(site=<music21.stream.Part Alto>,
                     offset=9.0,
                     recurseType=<RecursionType.FLATTEN>)
        ContextTuple(site=<music21.stream.Score bach>,
                     offset=9.0,
                     recurseType=<RecursionType.ELEMENTS_ONLY>)

        Sorting order:

        >>> p1 = stream.Part()
        >>> p1.id = 'p1'
        >>> m1 = stream.Measure()
        >>> m1.number = 1
        >>> n = note.Note()
        >>> m1.append(n)
        >>> p1.append(m1)
        >>> for csTuple in n.contextSites():
        ...     print(csTuple.site)
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>

        >>> p2 = stream.Part()
        >>> p2.id = 'p2'
        >>> m2 = stream.Measure()
        >>> m2.number = 2
        >>> m2.append(n)
        >>> p2.append(m2)

        The keys could have appeared in any order, but by default
        we set priorityTarget to activeSite.  So this is the same as omitting.

        >>> for y in n.contextSites(priorityTarget=n.activeSite):
        ...     print(y[0])
        <music21.stream.Measure 2 offset=0.0>
        <music21.stream.Part p2>
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>

        We can sort sites by creationTime...

        >>> for csTuple in n.contextSites(sortByCreationTime=True):
        ...     print(csTuple.site)
        <music21.stream.Measure 2 offset=0.0>
        <music21.stream.Part p2>
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>

        oldest first...

        >>> for csTuple in n.contextSites(sortByCreationTime='reverse'):
        ...     print(csTuple.site)
        <music21.stream.Measure 1 offset=0.0>
        <music21.stream.Part p1>
        <music21.stream.Measure 2 offset=0.0>
        <music21.stream.Part p2>

        Note that by default we search all sites, but you might want to only search
        one, for instance:

        >>> c = note.Note('C')
        >>> m1 = stream.Measure()
        >>> m1.append(c)

        >>> d = note.Note('D')
        >>> m2 = stream.Measure()
        >>> m2.append([c, d])

        >>> c.activeSite = m1
        >>> c.next('Note')  # uses contextSites
        <music21.note.Note D>

        There is a particular site in which there is a Note after c,
        but we want to know if there is one in m1 or its hierarchy, so
        we can pass in activeSiteOnly to `.next()` which sets
        `priorityTargetOnly=True` for contextSites

        >>> print(c.next('Note', activeSiteOnly=True))
        None


        *  Removed in v3: priorityTarget cannot be set, in order
           to use `.sites.yieldSites()`
        *  Changed in v5.5: all arguments are keyword only.
        *  Changed in v6: added `priorityTargetOnly=False` to only search in the
           context of the priorityTarget.
        *  Changed in v8: `returnSortTuple=True` returns a new ContextSortTuple
        '''
        from music21 import stream

        if memo is None:
            memo = set()

        if callerFirst is None:
            callerFirst = self
            if self.isStream and self not in memo:
                streamSelf = t.cast('music21.stream.Stream', self)
                recursionType = streamSelf.recursionType  # pylint: disable=no-member
                environLocal.printDebug(
                    f'Caller first is {callerFirst} with offsetAppend {offsetAppend}')
                if returnSortTuples:
                    selfSortTuple = streamSelf.sortTuple().modify(
                        offset=0.0,
                        priority=float('-inf')
                    )
                    yield ContextSortTuple(streamSelf, selfSortTuple, recursionType)
                else:
                    yield ContextTuple(streamSelf, 0.0, recursionType)
                memo.add(streamSelf)

        if priorityTarget is None and sortByCreationTime is False:
            priorityTarget = self.activeSite
        else:
            environLocal.printDebug(f'sortByCreationTime {sortByCreationTime}')

        topLevel = self
        for siteObj in self.sites.yieldSites(sortByCreationTime=sortByCreationTime,
                                             priorityTarget=priorityTarget,
                                             excludeNone=True):
            if siteObj in memo:
                continue
            if isinstance(siteObj, stream.SpannerStorage):
                continue

            try:
                st = self.sortTuple(siteObj)
                if followDerivation:
                    # do not change this to ElementOffset because getOffsetBySite can
                    # follow derivation chains.
                    offsetInStream = self.getOffsetBySite(siteObj)
                else:
                    offsetInStream = siteObj.elementOffset(self)

                newOffset = opFrac(offsetInStream + offsetAppend)

                positionInStream = st.modify(offset=newOffset)
            except SitesException:
                continue  # not a valid site anymore.  Could be caught in derivationChain

            recursionType = siteObj.recursionType
            if returnSortTuples:
                yield ContextSortTuple(siteObj, positionInStream, recursionType)
            else:
                yield ContextTuple(siteObj, positionInStream.offset, recursionType)

            memo.add(siteObj)
            environLocal.printDebug(
                f'looking in contextSites for {siteObj}'
                + f' with position {positionInStream.shortRepr()}')
            for topLevel, inStreamPos, recurType in siteObj.contextSites(
                callerFirst=callerFirst,
                memo=memo,
                offsetAppend=positionInStream.offset,
                returnSortTuples=True,  # ALWAYS
                sortByCreationTime=sortByCreationTime
            ):
                if priorityTargetOnly and topLevel is not priorityTarget:
                    break
                # get activeSite unless sortByCreationTime
                inStreamOffset = inStreamPos.offset
                # now take that offset and use it to modify the positionInStream
                # to get where Exactly the object would be if it WERE in this stream
                hypotheticalPosition = positionInStream.modify(offset=inStreamOffset)

                if topLevel not in memo:
                    # environLocal.printDebug('Yielding {}, {}, {} from contextSites'.format(
                    #                                                topLevel,
                    #                                                inStreamPos.shortRepr(),
                    #                                                recurType))
                    if returnSortTuples:
                        yield ContextSortTuple(topLevel, hypotheticalPosition, recurType)
                    else:
                        yield ContextTuple(topLevel, inStreamOffset, recurType)
                    memo.add(topLevel)
            if priorityTargetOnly:
                break

        if followDerivation:
            for derivedObject in topLevel.derivation.chain():
                environLocal.printDebug(
                    'looking now in derivedObject, '
                    + f'{derivedObject} with offsetAppend {offsetAppend}')
                for derivedCsTuple in derivedObject.contextSites(
                        callerFirst=None,
                        memo=memo,
                        offsetAppend=0.0,
                        returnSortTuples=True,
                        sortByCreationTime=sortByCreationTime):
                    # get activeSite unless sortByCreationTime
                    if derivedCsTuple.site in memo:
                        continue

                    environLocal.printDebug(
                        f'Yielding {derivedCsTuple} from derivedObject contextSites'
                    )
                    offsetAdjustedCsTuple = ContextSortTuple(
                        derivedCsTuple.site,
                        derivedCsTuple.offset.modify(offset=derivedCsTuple[1].offset
                                                            + offsetAppend),
                        derivedCsTuple.recurseType)
                    if returnSortTuples:
                        yield offsetAdjustedCsTuple
                    else:
                        yield ContextTuple(offsetAdjustedCsTuple.site,
                                           offsetAdjustedCsTuple.offset.offset,
                                           offsetAdjustedCsTuple.recurseType)
                    memo.add(derivedCsTuple.site)

        environLocal.printDebug('--returning from derivedObject search')

    def getAllContextsByClass(self, className):
        '''
        Returns a generator that yields elements found by `.getContextByClass` and
        then finds the previous contexts for that element.

        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('2/4'))
        >>> s.append(note.Note('C'))
        >>> s.append(meter.TimeSignature('3/4'))
        >>> n = note.Note('D')
        >>> s.append(n)


        >>> for ts in n.getAllContextsByClass(meter.TimeSignature):
        ...     print(ts, ts.offset)
        <music21.meter.TimeSignature 3/4> 1.0
        <music21.meter.TimeSignature 2/4> 0.0

        TODO: make it so that it does not skip over multiple matching classes
        at the same offset. with sortTuple

        '''
        el = self.getContextByClass(className)
        while el is not None:
            yield el
            el = el.getContextByClass(className, getElementMethod=ElementSearch.BEFORE_OFFSET)

    # -------------------------------------------------------------------------

    def next(self,
             className: type[Music21Object] | str | None = None,
             *,
             activeSiteOnly=False):
        '''
        Get the next element found in the activeSite (or other Sites)
        of this Music21Object.

        The `className` can be used to specify one or more classes to match.

        >>> s = corpus.parse('bwv66.6')
        >>> m3 = s.parts[0].measure(3)
        >>> m4 = s.parts[0].measure(4)
        >>> m3
        <music21.stream.Measure 3 offset=9.0>
        >>> m3.show('t')
        {0.0} <music21.layout.SystemLayout>
        {0.0} <music21.note.Note A>
        {0.5} <music21.note.Note B>
        {1.0} <music21.note.Note G#>
        {2.0} <music21.note.Note F#>
        {3.0} <music21.note.Note A>
        >>> m3.next()
        <music21.layout.SystemLayout>
        >>> nextM3 = m3.next('Measure')
        >>> nextM3 is m4
        True

        Note that calling next() repeatedly gives...the same object.  You'll want to
        call next on that object...

        >>> m3.next('Measure') is s.parts[0].measure(4)
        True
        >>> m3.next('Measure') is s.parts[0].measure(4)
        True

        So do this instead:

        >>> o = m3
        >>> for i in range(5):
        ...     print(o)
        ...     o = o.next('Measure')
        <music21.stream.Measure 3 offset=9.0>
        <music21.stream.Measure 4 offset=13.0>
        <music21.stream.Measure 5 offset=17.0>
        <music21.stream.Measure 6 offset=21.0>
        <music21.stream.Measure 7 offset=25.0>

        We can find the next element given a certain class with the `className`:

        >>> n = m3.next('Note')
        >>> n
        <music21.note.Note A>
        >>> n.measureNumber
        3
        >>> n is m3.notes.first()
        True
        >>> n.next()
        <music21.note.Note B>

        Notice though that when we get to the end of the set of measures, something
        interesting happens (maybe it shouldn't? don't count on this...): we descend
        into the last measure and give its elements instead.

        We'll leave o where it is (m8 now) to demonstrate what happens, and also
        print its Part for more information...

        >>> while o is not None:
        ...     print(o, o.getContextByClass(stream.Part))
        ...     o = o.next()
        <music21.stream.Measure 8 offset=29.0> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.stream.Measure 9 offset=33.0> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.note.Note E#> <music21.stream.Part Soprano>
        <music21.note.Note F#> <music21.stream.Part Soprano>
        <music21.bar.Barline type=final> <music21.stream.Part Soprano>

        * Changed in v6: added activeSiteOnly -- see description in `.contextSites()`
        '''
        allSiteContexts = list(self.contextSites(
            returnSortTuples=True,
            priorityTargetOnly=activeSiteOnly,
        ))
        maxRecurse = 20

        thisElForNext = self
        while maxRecurse:
            nextEl = thisElForNext.getContextByClass(
                className=className,
                getElementMethod=ElementSearch.AFTER_NOT_SELF,
                followDerivation=not activeSiteOnly,
                priorityTargetOnly=activeSiteOnly,
            )

            callContinue = False
            for singleSiteContext, unused_positionInContext, unused_recurseType in allSiteContexts:
                if nextEl is singleSiteContext:
                    nextEl = t.cast('music21.stream.Stream', nextEl)
                    if nextEl and nextEl[0] is not self:  # has elements
                        return nextEl[0]

                    thisElForNext = nextEl
                    callContinue = True
                    break

            if callContinue:
                maxRecurse -= 1
                continue

            if nextEl is not self:
                return nextEl
            maxRecurse -= 1

        if maxRecurse == 0:
            raise Music21Exception('Maximum recursion!')

    def previous(self,
                 className: type[Music21Object] | str | None = None,
                 *,
                 activeSiteOnly=False):
        '''
        Get the previous element found in the activeSite or other .sites of this
        Music21Object.

        The `className` can be used to specify one or more classes to match.

        >>> s = corpus.parse('bwv66.6')
        >>> m2 = s.parts[0].getElementsByClass(stream.Measure)[2]  # pickup measure
        >>> m3 = s.parts[0].getElementsByClass(stream.Measure)[3]
        >>> m3
        <music21.stream.Measure 3 offset=9.0>
        >>> m3prev = m3.previous()
        >>> m3prev
        <music21.note.Note C#>
        >>> m3prev is m2.notes[-1]
        True
        >>> m3.previous('Measure') is m2
        True

        We'll iterate backwards from the first note of the second measure of the Alto part.

        >>> o = s.parts[1].getElementsByClass(stream.Measure)[2][0]
        >>> while o:
        ...    print(o)
        ...    o = o.previous()
        <music21.note.Note E>
        <music21.stream.Measure 2 offset=5.0>
        <music21.note.Note E>
        <music21.note.Note E>
        <music21.note.Note E>
        <music21.note.Note F#>
        <music21.stream.Measure 1 offset=1.0>
        <music21.note.Note E>
        <music21.meter.TimeSignature 4/4>
        f# minor
        <music21.tempo.MetronomeMark Quarter=96 (playback only)>
        <music21.clef.TrebleClef>
        <music21.stream.Measure 0 offset=0.0>
        P2: Alto: Instrument 2
        <music21.stream.Part Alto>
        <music21.stream.Part Soprano>
        <music21.metadata.Metadata object at 0x11116d080>
        <music21.stream.Score bach/bwv66.6.mxl>

        * Changed in v6: added activeSiteOnly -- see description in `.contextSites()`
        '''
        # allSiteContexts = list(self.contextSites(returnSortTuples=True))
        # maxRecurse = 20

        prevEl = self.getContextByClass(className=className,
                                        getElementMethod=ElementSearch.BEFORE_NOT_SELF,
                                        followDerivation=not activeSiteOnly,
                                        priorityTargetOnly=activeSiteOnly,
                                        )

        # for singleSiteContext, unused_positionInContext, unused_recurseType in allSiteContexts:
        #     if prevEl is singleSiteContext:
        #         prevElPrev = prevEl.getContextByClass(
        #                          prevEl.__class__,
        #                          getElementMethod=ElementSearch.BEFORE_NOT_SELF)
        #         if prevElPrev and prevElPrev is not self:
        #             return prevElPrev
        isInPart = False
        if self.isStream and prevEl is not None:
            # if self is a Part, ensure that the previous element is not in self
            for cs, unused1, unused2 in prevEl.contextSites():
                if cs is self:
                    isInPart = True
                    break

        if prevEl and prevEl is not self and not isInPart:
            return prevEl
        else:
            # okay, go up to next level
            activeS = self.activeSite  # might be None...
            if activeS is None:
                return None
            asTree = activeS.asTree(classList=[className], flatten=False)
            prevNode = asTree.getNodeBefore(self.sortTuple())
            if prevNode is None:
                if className is None or className in activeS.classSet:
                    return activeS
                else:
                    return None
            else:
                return prevNode.payload

    # end contexts...
    # --------------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # properties

    def _getActiveSite(self):
        # can be None
        if WEAKREF_ACTIVE:
            if self._activeSite is None:  # leave None
                return None
            else:  # even if current activeSite is not a weakref, this will work
                # environLocal.printDebug(['_getActiveSite() called:',
                #                          'self._activeSite', self._activeSite])
                return common.unwrapWeakref(self._activeSite)
        else:  # pragma: no cover
            return self._activeSite

    def _setActiveSite(self, site: stream.Stream | None):
        # environLocal.printDebug(['_setActiveSite() called:', 'self', self, 'site', site])

        # NOTE: this is a performance intensive call
        if site is not None:
            try:
                storedOffset = site.elementOffset(self)
            except SitesException as se:
                raise SitesException(
                    'activeSite cannot be set for '
                    + f'object {self} not in the Stream {site}'
                ) from se

            self._activeSiteStoredOffset = storedOffset
            # siteId = id(site)
            # if not self.sites.hasSiteId(siteId):  # This should raise a warning, should not happen
            #    # environLocal.warn('Adding a siteDict entry for a ' +
            #    #                        'site that should already be there!')
            #    self.sites.add(site, idKey=siteId)
        else:
            self._activeSiteStoredOffset = None

        if WEAKREF_ACTIVE:
            if site is None:  # leave None alone
                self._activeSite = None
            else:
                self._activeSite = common.wrapWeakref(site)
        else:  # pragma: no cover
            self._activeSite = site

    activeSite = property(_getActiveSite,
                          _setActiveSite,
                          doc='''
        A reference to the most-recent object used to
        contain this object. In most cases, this will be a
        Stream or Stream sub-class. In most cases, an object's
        activeSite attribute is automatically set when the
        object is attached to a Stream.


        >>> n = note.Note('C#4')
        >>> p = stream.Part()
        >>> p.insert(20.0, n)
        >>> n.activeSite is p
        True
        >>> n.offset
        20.0

        >>> m = stream.Measure()
        >>> m.insert(10.0, n)
        >>> n.activeSite is m
        True
        >>> n.offset
        10.0
        >>> n.activeSite = p
        >>> n.offset
        20.0
        ''')

    @property
    def offset(self) -> OffsetQL:
        '''
        The offset property sets or returns the position of this object
        as a float or fractions.Fraction value
        (generally in `quarterLengths`), depending on what is representable.

        Offsets are measured from the start of the object's `activeSite`,
        that is, the most recently referenced `Stream` or `Stream` subclass such
        as `Part`, `Measure`, or `Voice`.  It is a simpler
        way of calling `o.getOffsetBySite(o.activeSite, returnType='rational')`.

        If we put a `Note` into a `Stream`, we will see the activeSite changes.

        >>> import fractions
        >>> n1 = note.Note('D#3')
        >>> n1.activeSite is None
        True

        >>> m1 = stream.Measure()
        >>> m1.number = 4
        >>> m1.insert(10.0, n1)
        >>> n1.offset
        10.0
        >>> n1.activeSite
        <music21.stream.Measure 4 offset=0.0>

        >>> n1.activeSite is m1
        True

        The most recently referenced `Stream` becomes an object's `activeSite` and
        thus the place where `.offset` looks to find its number.

        >>> m2 = stream.Measure()
        >>> m2.insert(3/5, n1)
        >>> m2.number = 5
        >>> n1.offset
        Fraction(3, 5)
        >>> n1.activeSite is m2
        True

        Notice though that `.offset` depends on the `.activeSite` which is the most
        recently accessed/referenced Stream.

        Here we will iterate over the `elements` in `m1` and we
        will see that the `.offset` of `n1` now is its offset in
        `m1` even though we haven't done anything directly to `n1`.
        Simply iterating over a site is enough to change the `.activeSite`
        of its elements:

        >>> for element in m1:
        ...     pass
        >>> n1.offset
        10.0

        The property can also set the offset for the object if no
        container has been set:

        >>> n1 = note.Note()
        >>> n1.id = 'hi'
        >>> n1.offset = 20/3
        >>> n1.offset
        Fraction(20, 3)
        >>> float(n1.offset)
        6.666...

        >>> s1 = stream.Stream()
        >>> s1.append(n1)
        >>> n1.offset
        0.0
        >>> s2 = stream.Stream()
        >>> s2.insert(30.5, n1)
        >>> n1.offset
        30.5

        After calling `getElementById` on `s1`, the
        returned element's `offset` will be its offset in `s1`.

        >>> n2 = s1.getElementById('hi')
        >>> n2 is n1
        True
        >>> n2.offset
        0.0

        Iterating over the elements in a Stream will
        make its `offset` be the offset in iterated
        Stream.

        >>> for thisElement in s2:
        ...     thisElement.offset
        30.5

        When in doubt, use `.getOffsetBySite(streamObj)`
        which is safer or streamObj.elementOffset(self) which is 3x faster.

        * Changed in v8: using a Duration object as an offset is not allowed.
        '''
        # There is a branch that does slow searches.
        # See test/testSerialization to have it active.

        # there is a problem if a new activeSite is being set and no offsets have
        # been provided for that activeSite; when self.offset is called,
        # the first case here would match
        # environLocal.printDebug(['Music21Object._getOffset', 'self.id',
        #                           self.id, 'id(self)', id(self), self.__class__])
        activeSiteWeakRef = self._activeSite
        if activeSiteWeakRef is not None:
            activeSite = self.activeSite
            if activeSite is None:
                # it has died since last visit, as is the case with short-lived streams like
                # .getElementsByClass, so we will return the most recent position
                return self._activeSiteStoredOffset or 0.0

            try:
                o = activeSite.elementOffset(self)
            except SitesException:
                environLocal.printDebug(
                    'Not in Stream: changing activeSite to None and returning _naiveOffset')
                self.activeSite = None
                o = self._naiveOffset
        else:
            o = self._naiveOffset

        return o

    @offset.setter
    def offset(self, value: OffsetQLIn):
        # assume that most times this is a number; in that case, the fastest
        # thing to do is simply try to set the offset w/ float(value)
        try:
            offset = opFrac(value)
        except TypeError:
            offset = value

        if self.activeSite is not None:
            self.activeSite.setElementOffset(self, offset)
        else:
            self._naiveOffset = offset

    def sortTuple(self,
                  useSite: t.Literal[False] | stream.Stream | None = False,
                  raiseExceptionOnMiss: bool = False
                  ) -> SortTuple:
        '''
        Returns a collections.namedtuple called SortTuple(atEnd, offset, priority, classSortOrder,
        isNotGrace, insertIndex)
        which contains the six elements necessary to determine the sort order of any set of
        objects in a Stream.

        1) atEnd = {0, 1}; Elements specified to always stay at
        the end of a stream (``stream.storeAtEnd``)
        sort after normal elements.

        2) offset = float; Offset (with respect to the active site) is the next and most
        important parameter in determining the order of elements in a stream (the note on beat 1
        has offset 0.0, while the note on beat 2 might have offset 1.0).

        3) priority = int; Priority is a
        user-specified property (default 0) that can set the order of
        elements which have the same
        offset (for instance, two Parts both at offset 0.0).

        4) classSortOrder = int or float; ClassSortOrder
        is the third level of comparison that gives an ordering to elements with different classes,
        ensuring, for instance that Clefs (classSortOrder = 0) sort before Notes
        (classSortOrder = 20).

        5) isNotGrace = {0, 1}; 0 = grace, 1 = normal. Grace notes sort before normal notes

        6) The last tie-breaker is the creation time (insertIndex) of the site object
        represented by the activeSite.

        By default, the site used will be the activeSite:

        >>> n = note.Note()
        >>> n.offset = 4.0
        >>> n.priority = -3
        >>> n.sortTuple()
        SortTuple(atEnd=0, offset=4.0, priority=-3, classSortOrder=20,
                    isNotGrace=1, insertIndex=0)

        >>> st = n.sortTuple()

        Check that all these values are the same as above...

        >>> st.offset == n.offset
        True
        >>> st.priority == n.priority
        True

        An object's classSortOrder comes from the Class object itself:

        >>> st.classSortOrder == note.Note.classSortOrder
        True

        SortTuples have a few methods that are documented in :class:`~music21.sorting.SortTuple`.
        The most useful one for documenting is `.shortRepr()`.

        >>> st.shortRepr()
        '4.0 <-3.20.0>'

        Inserting the note into the Stream will set the insertIndex.  Most implementations of
        music21 will use a global counter rather than an actual timer.  Note that this is a
        last resort, but useful for things such as multiple Parts inserted in order.  It changes
        with each run, so we can't display it here...

        >>> s = stream.Stream()
        >>> s.insert(n)
        >>> n.sortTuple()
        SortTuple(atEnd=0, offset=4.0, priority=-3, classSortOrder=20,
                     isNotGrace=1, insertIndex=...)

        >>> nInsertIndex = n.sortTuple().insertIndex

        If we create another nearly identical note, the insertIndex will be different:

        >>> n2 = note.Note()
        >>> n2.offset = 4.0
        >>> n2.priority = -3
        >>> s.insert(n2)
        >>> n2InsertIndex = n2.sortTuple().insertIndex
        >>> n2InsertIndex > nInsertIndex
        True

        >>> rb = bar.Barline()
        >>> s.storeAtEnd(rb)
        >>> rb.sortTuple()
        SortTuple(atEnd=1, offset=0.0, priority=0, classSortOrder=-5,
                    isNotGrace=1, insertIndex=...)


        Normally if there's a site specified and the element is not in the site,
        the offset of None will be used, but if raiseExceptionOnMiss is set to True
        then a SitesException will be raised:

        >>> aloneNote = note.Note()
        >>> aloneNote.offset = 30
        >>> aloneStream = stream.Stream(id='aloneStream')  # no insert
        >>> aloneNote.sortTuple(aloneStream)
        SortTuple(atEnd=0, offset=30.0, priority=0, classSortOrder=20, isNotGrace=1, insertIndex=0)

        >>> aloneNote.sortTuple(aloneStream, raiseExceptionOnMiss=True)
        Traceback (most recent call last):
        music21.sites.SitesException: an entry for this object 0x... is not stored in
            stream <music21.stream.Stream aloneStream>
        '''
        useSiteNoFalse: stream.Stream | None
        if useSite is False:  # False or a Site; since None is a valid site, default is False
            useSiteNoFalse = self.activeSite
        else:
            useSiteNoFalse = useSite

        foundOffset: OffsetQL | OffsetSpecial
        if useSiteNoFalse is None:
            foundOffset = self.offset
        else:
            try:
                foundOffset = useSiteNoFalse.elementOffset(self, returnSpecial=True)
            except SitesException:
                if raiseExceptionOnMiss:
                    raise
                # environLocal.warn(r)
                    # activeSite may have vanished! or does not have the element
                foundOffset = self._naiveOffset

        offset: OffsetQL
        if foundOffset == OffsetSpecial.AT_END:
            offset = 0.0
            atEnd = 1
        else:  # no other OffsetSpecials currently exist.
            offset = t.cast(OffsetQL, foundOffset)
            atEnd = 0

        if self.duration.isGrace:
            isNotGrace = 0
        else:
            isNotGrace = 1

        if self.sites.hasSiteId(id(useSite)):
            insertIndex = self.sites.siteDict[id(useSite)].globalSiteIndex
        elif self.activeSite is not None:
            insertIndex = self.sites.siteDict[id(self.activeSite)].globalSiteIndex
        else:  # for None, use this instead of default of -2.
            insertIndex = 0

        return SortTuple(atEnd, offset, self.priority,
                          self.classSortOrder, isNotGrace, insertIndex)

    # -----------------------------------------------------------------
    @property
    def duration(self) -> Duration:
        '''
        Get and set the duration of this object as a Duration object.
        '''
        # lazy duration creation
        if self._duration is None:
            self._duration = Duration(0)

        d_out = self._duration
        if t.TYPE_CHECKING:
            assert d_out is not None

        return d_out

    @duration.setter
    def duration(self, durationObj: Duration):
        durationObjAlreadyExists = False
        if self._duration is not None:
            self._duration.client = None
            durationObjAlreadyExists = True

        try:
            ql = durationObj.quarterLength
            self._duration = durationObj
            durationObj.client = self
            if durationObjAlreadyExists:
                self.informSites({'changedElement': 'duration', 'quarterLength': ql})

        except AttributeError as ae:
            # need to permit Duration object assignment here
            raise TypeError(
                f'this must be a Duration object, not {durationObj}'
            ) from ae

    def informSites(self, changedInformation=None):
        '''
        trigger called whenever sites need to be informed of a change
        in the parameters of this object.

        `changedInformation` is not used now, but it can be a dictionary
        of what has changed.

        subclass this to do very interesting things.
        '''
        for s in self.sites.get():
            if hasattr(s, 'coreElementsChanged'):
                # noinspection PyCallingNonCallable
                s.coreElementsChanged(updateIsFlat=False, keepIndex=True)

    def _getPriority(self):
        return self._priority

    def _setPriority(self, value):
        '''
        value is an int.

        Informs all sites of the change.
        '''
        if not isinstance(value, int):
            raise ElementException('priority values must be integers.')
        if self._priority != value:
            self._priority = value
            self.informSites({'changedElement': 'priority', 'priority': value})

    priority = property(_getPriority,
                        _setPriority,
                        doc='''
        Get and set the priority integer value.

        Priority specifies the order of processing from left (lowest number)
        to right (highest number) of objects at the same offset.  For
        instance, if you want a key change and a clef change to happen at
        the same time but the key change to appear first, then set:
        keySigElement.priority = 1; clefElement.priority = 2 this might be
        a slightly counterintuitive numbering of priority, but it does
        mean, for instance, if you had two elements at the same offset,
        an allegro tempo change and an andante tempo change, then the
        tempo change with the higher priority number would apply to the
        following notes (by being processed second).

        Default priority is 0; thus negative priorities are encouraged
        to have Elements that appear before non-priority set elements.

        In case of tie, there are defined class sort orders defined in
        `music21.base.classSortOrder`.  For instance, a key signature
        change appears before a time signature change before a
        note at the same offset.  This produces the familiar order of
        materials at the start of a musical score.

        >>> import music21
        >>> a = music21.Music21Object()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        music21.base.ElementException: priority values must be integers.
        ''')

    # -------------------------------------------------------------------------
    # display and writing

    def write(
        self,
        fmt: str | None = None,
        fp: str | pathlib.Path | IOBase | None = None,
        **keywords
    ) -> pathlib.Path:  # pragma: no cover
        '''
        Write out a file of music notation (or an image, etc.) in a given format.  If
        fp is specified as a file path then the file will be placed there.  If it is not
        given then a temporary file will be created.

        If fmt is not given then the default of your Environment's 'writeFormat' will
        be used.  For most people that is musicxml.

        Returns the full path to the file.

        Some formats, including .musicxml, create a copy of the stream, pack it into a well-formed
        score if necessary, and run :meth:`~music21.stream.Score.makeNotation`. To
        avoid this when writing .musicxml, use `makeNotation=False`, an advanced option
        that prioritizes speed but may not guarantee satisfactory notation.
        '''
        if fmt is None:  # get setting in environment
            fmt = environLocal['writeFormat']
        elif fmt.startswith('.'):
            fmt = fmt[1:]

        if fmt == 'mxl':
            keywords['compress'] = True

        regularizedConverterFormat, unused_ext = common.findFormat(fmt)
        if regularizedConverterFormat is None:
            raise Music21ObjectException(f'cannot support output in this format yet: {fmt}')

        formatSubs = fmt.split('.')
        fmt = formatSubs[0]
        subformats = formatSubs[1:]

        scClass = common.findSubConverterForFormat(regularizedConverterFormat)
        if scClass is None:  # pragma: no cover
            raise Music21ObjectException(f'cannot support output in this format yet: {fmt}')
        formatWriter = scClass()
        return formatWriter.write(self,
                                  fmt=regularizedConverterFormat,
                                  fp=fp,
                                  subformats=subformats,
                                  **keywords)


    def _reprText(self, **keywords):
        '''
        Return a text representation possible with line
        breaks. This method can be overridden by subclasses
        to provide alternative text representations.
        '''
        return repr(self)

    def _reprTextLine(self):
        '''
        Return a text representation without line breaks. This
        method can be overridden by subclasses to provide
        alternative text representations.
        '''
        return repr(self)

    def show(self, fmt=None, app=None, **keywords):  # pragma: no cover
        '''
        Displays an object in a format provided by the
        fmt argument or, if not provided, the format set in the user's Environment

        Valid formats include (but are not limited to)::

            musicxml
            text
            midi
            lily (or lilypond)
            lily.png
            lily.pdf
            lily.svg
            braille
            vexflow
            musicxml.png

        N.B. score.write('lily') returns a bare lilypond file,
        score.show('lily') runs it through lilypond and displays it as a png.

        Some formats, including .musicxml, create a copy of the stream, pack it into a well-formed
        score if necessary, and run :meth:`~music21.stream.Score.makeNotation`. To
        avoid this when showing .musicxml, use `makeNotation=False`, an advanced option
        that prioritizes speed but may not guarantee satisfactory notation.
        '''
        # note that all formats here must be defined in
        # common.VALID_SHOW_FORMATS
        if fmt is None:  # get setting in environment
            if common.runningInNotebook():
                try:
                    fmt = environLocal['ipythonShowFormat']
                except (environment.EnvironmentException, KeyError):
                    fmt = 'ipython.musicxml.png'
            else:
                fmt = environLocal['showFormat']
        elif fmt.startswith('.'):
            fmt = fmt[1:]
        elif common.runningInNotebook() and fmt.startswith('midi'):
            fmt = 'ipython.' + fmt

        regularizedConverterFormat, unused_ext = common.findFormat(fmt)
        if regularizedConverterFormat is None:
            raise Music21ObjectException(f'cannot support showing in this format yet:{fmt}')

        formatSubs = fmt.split('.')
        fmt = formatSubs[0]
        subformats = formatSubs[1:]

        scClass = common.findSubConverterForFormat(regularizedConverterFormat)
        formatWriter = scClass()
        return formatWriter.show(self,
                                 regularizedConverterFormat,
                                 app=app,
                                 subformats=subformats,
                                 **keywords)

    # -------------------------------------------------------------------------
    # duration manipulation, processing, and splitting

    def containerHierarchy(
        self,
        *,
        followDerivation=True,
        includeNonStreamDerivations=False
    ):
        '''
        Return a list of Stream subclasses that this object
        is contained within or (if followDerivation is set) is derived from.

        This method gives access to the hierarchy that contained or
        created this object.

        >>> s = corpus.parse('bach/bwv66.6')
        >>> noteE = s[1][2][3]
        >>> noteE
        <music21.note.Note E>
        >>> [e for e in noteE.containerHierarchy()]
        [<music21.stream.Measure 1 offset=1.0>,
         <music21.stream.Part Soprano>,
         <music21.stream.Score bach/bwv66.6.mxl>]


        Note that derived objects also can follow the container hierarchy:

        >>> import copy
        >>> n2 = copy.deepcopy(noteE)
        >>> [e for e in n2.containerHierarchy()]
        [<music21.stream.Measure 1 offset=1.0>,
         <music21.stream.Part Soprano>,
         <music21.stream.Score bach/bwv66.6.mxl>]

        Unless followDerivation is False:

        >>> [e for e in n2.containerHierarchy(followDerivation=False)]
        []

        if includeNonStreamDerivations is True then n2's containerHierarchy will include
        n even though it's not a container.  It gives a good idea of how the hierarchy is being
        constructed.

        >>> [e for e in n2.containerHierarchy(includeNonStreamDerivations=True)]
        [<music21.note.Note E>,
         <music21.stream.Measure 1 offset=1.0>,
         <music21.stream.Part Soprano>,
         <music21.stream.Score bach/bwv66.6.mxl>]


        The method follows activeSites, so set the activeSite as necessary.

        >>> p = stream.Part(id='newPart')
        >>> m = stream.Measure(number=20)
        >>> p.insert(0, m)
        >>> m.insert(0, noteE)
        >>> noteE.activeSite
        <music21.stream.Measure 20 offset=0.0>
        >>> noteE.containerHierarchy()
        [<music21.stream.Measure 20 offset=0.0>,
         <music21.stream.Part newPart>]

        * Changed in v5.7: `followDerivation` and
          `includeNonStreamDerivations` are now keyword only
        '''
        post = []
        focus = self
        endMe = 200
        while endMe > 0:
            endMe = endMe - 1  # do not go forever
            # collect activeSite unless activeSite is None;
            # if so, try to get rootDerivation
            candidate = focus.activeSite
            # environLocal.printDebug(['containerHierarchy(): activeSite found:', candidate])
            if candidate is None:  # nothing more to derive
                # if this is a Stream, we might find a root derivation
                if followDerivation is True and hasattr(focus, 'derivation'):
                    # environLocal.printDebug(['containerHierarchy():
                    # found rootDerivation:', focus.rootDerivation])
                    alt = focus.derivation.rootDerivation
                    if alt is None:
                        return post
                    else:
                        candidate = alt
                else:
                    return post
            if includeNonStreamDerivations is True or candidate.isStream:
                post.append(candidate)
            focus = candidate
        return post

    def splitAtQuarterLength(
        self,
        quarterLength,
        *,
        retainOrigin=True,
        addTies=True,
        displayTiedAccidentals=False
    ) -> _SplitTuple:
        # noinspection PyShadowingNames
        '''
        Split an Element into two Elements at a provided
        `quarterLength` (offset) into the Element.

        Returns a specialized tuple that also has
        a .spannerList element which is a list of spanners
        that were created during the split, such as by splitting a trill
        note into more than one trill.

        TODO: unite into a "split" function -- document obscure uses.

        >>> a = note.Note('C#5')
        >>> a.duration.type = 'whole'
        >>> a.articulations = [articulations.Staccato()]
        >>> a.lyric = 'hi'
        >>> a.expressions = [expressions.Mordent(), expressions.Trill(), expressions.Fermata()]
        >>> st = a.splitAtQuarterLength(3)
        >>> b, c = st
        >>> b.duration.type
        'half'
        >>> b.duration.dots
        1
        >>> b.duration.quarterLength
        3.0
        >>> b.articulations
        []
        >>> b.lyric
        'hi'
        >>> b.expressions
        [<music21.expressions.Mordent>, <music21.expressions.Trill>]
        >>> c.duration.type
        'quarter'
        >>> c.duration.dots
        0
        >>> c.duration.quarterLength
        1.0
        >>> c.articulations
        [<music21.articulations.Staccato>]
        >>> c.lyric
        >>> c.expressions
        [<music21.expressions.Fermata>]
        >>> c.getSpannerSites()
        [<music21.expressions.TrillExtension <music21.note.Note C#><music21.note.Note C#>>]

        st is a _SplitTuple which can get the spanners from it for inserting into a Stream.

        >>> st.spannerList
        [<music21.expressions.TrillExtension <music21.note.Note C#><music21.note.Note C#>>]



        Make sure that ties and accidentals remain as they should be:

        >>> d = note.Note('D#4')
        >>> d.duration.quarterLength = 3.0
        >>> d.tie = tie.Tie('start')
        >>> e, f = d.splitAtQuarterLength(2.0)
        >>> e.tie, f.tie
        (<music21.tie.Tie start>, <music21.tie.Tie continue>)
        >>> e.pitch.accidental.displayStatus is None
        True
        >>> f.pitch.accidental.displayStatus
        False

        Should be the same for chords...

        >>> g = chord.Chord(['C4', 'E4', 'G#4'])
        >>> g.duration.quarterLength = 3.0
        >>> g[1].tie = tie.Tie('start')
        >>> h, i = g.splitAtQuarterLength(2.0)
        >>> for j in range(3):
        ...   (h[j].tie, i[j].tie)
        (<music21.tie.Tie start>, <music21.tie.Tie stop>)
        (<music21.tie.Tie start>, <music21.tie.Tie continue>)
        (<music21.tie.Tie start>, <music21.tie.Tie stop>)

        >>> h[2].pitch.accidental.displayStatus, i[2].pitch.accidental.displayStatus
        (None, False)


        If quarterLength == self.quarterLength then the second element will be None.

        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> firstPart, secondPart = n.splitAtQuarterLength(0.5)
        >>> secondPart is None
        True
        >>> firstPart is n
        True

        (same with retainOrigin off)

        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> firstPart, secondPart = n.splitAtQuarterLength(0.5, retainOrigin=False)
        >>> firstPart is n
        False


        If quarterLength > self.quarterLength then a DurationException will be raised:

        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> first, second = n.splitAtQuarterLength(0.7)
        Traceback (most recent call last):
        music21.duration.DurationException: cannot split a duration (0.5)
            at this quarterLength (7/10)

        * Changed in v7: all but quarterLength are keyword only
        '''
        from music21 import chord
        from music21 import note
        quarterLength = opFrac(quarterLength)

        if quarterLength > self.duration.quarterLength:
            raise DurationException(
                f'cannot split a duration ({self.duration.quarterLength}) '
                + f'at this quarterLength ({quarterLength})'
            )

        if retainOrigin is True:
            e = self
        else:
            e = copy.deepcopy(self)
        eRemain = copy.deepcopy(self)

        # clear lyrics from remaining parts
        if isinstance(eRemain, note.GeneralNote):
            emptyLyrics: list[note.Lyric] = []
            # not sure why isinstance check is not picking this up.
            eRemain.lyrics = emptyLyrics  # pylint: disable=attribute-defined-outside-init

        spannerList = []
        for listType in ('expressions', 'articulations'):
            if hasattr(e, listType):
                temp = getattr(e, listType)
                setattr(e, listType, [])  # pylint: disable=attribute-defined-outside-init
                setattr(eRemain, listType, [])
                for thisExpression in temp:  # using thisExpression as a shortcut for expr or art.
                    if hasattr(thisExpression, 'splitClient'):  # special method (see Trill)
                        spanners = thisExpression.splitClient([e, eRemain])
                        for s in spanners:
                            spannerList.append(s)
                    elif hasattr(thisExpression, 'tieAttach'):
                        if thisExpression.tieAttach == 'first':
                            eList = getattr(e, listType)
                            eList.append(thisExpression)
                        elif thisExpression.tieAttach == 'last':
                            eRemainList = getattr(eRemain, listType)
                            eRemainList.append(thisExpression)
                        else:  # default = 'all'
                            eList = getattr(e, listType)
                            eList.append(thisExpression)
                            eRemainList = getattr(eRemain, listType)
                            eRemainList.append(thisExpression)
                    else:  # default = 'all'
                        eList = getattr(e, listType)
                        eList.append(thisExpression)
                        eRemainList = getattr(eRemain, listType)
                        eRemainList.append(thisExpression)

        if abs(quarterLength - self.duration.quarterLength) < 0:
            quarterLength = self.duration.quarterLength

        lenEnd = self.duration.quarterLength - quarterLength
        lenStart = self.duration.quarterLength - lenEnd

        d1 = Duration()
        d1.quarterLength = lenStart

        d2 = Duration()
        d2.quarterLength = lenEnd

        e.duration = d1
        eRemain.duration = d2

        # some higher-level classes need this functionality
        # set ties
        if addTies and isinstance(e, (note.Note, note.Unpitched)):
            forceEndTieType = 'stop'
            if e.tie is not None:
                # the last tie of what was formally a start should
                # continue
                if e.tie.type == 'start':
                    # keep start  if already set
                    forceEndTieType = 'continue'
                # a stop was ending a previous tie; we know that
                # the first is now a "continue" type
                elif e.tie.type == 'stop':
                    forceEndTieType = 'stop'
                    e.tie.type = 'continue'
                elif e.tie.type == 'continue':
                    forceEndTieType = 'continue'
                    # keep continue if already set
            else:
                # not sure why this is not being picked up by isinstance check
                e.tie = tie.Tie('start')  # pylint: disable=attribute-defined-outside-init

            if isinstance(eRemain, (note.Note, note.Unpitched)):
                # not sure why this is not being picked up by isinstance check
                newTie = tie.Tie(forceEndTieType)
                eRemain.tie = newTie  # pylint: disable=attribute-defined-outside-init

        elif addTies and isinstance(e, chord.Chord) and isinstance(eRemain, chord.Chord):
            # the last isinstance is redundant, but MyPy needs it.
            for i in range(len(e.notes)):
                component = e.notes[i]
                remainComponent = eRemain.notes[i]
                forceEndTieType = 'stop'
                if component.tie is not None:
                    # the last tie of what was formally a start should
                    # continue
                    if component.tie.type == 'start':
                        # keep start  if already set
                        forceEndTieType = 'continue'
                    # a stop was ending a previous tie; we know that
                    # the first is now a "continue" type
                    elif component.tie.type == 'stop':
                        forceEndTieType = 'stop'
                        component.tie.type = 'continue'
                    elif component.tie.type == 'continue':
                        forceEndTieType = 'continue'
                        # keep continue if already set
                else:
                    component.tie = tie.Tie('start')  # need a tie object
                remainComponent.tie = tie.Tie(forceEndTieType)

        # hide accidentals on tied notes where previous note
        # had an accidental that was shown
        if addTies and isinstance(e, note.NotRest) and isinstance(eRemain, note.NotRest):
            # again -- second isinstance check is redundant
            for i, p in enumerate(e.pitches):
                remainP = eRemain.pitches[i]
                if p.accidental is not None and remainP.accidental is not None:
                    # again -- second remainP.accidental is not None check is redundant
                    if not displayTiedAccidentals:  # if False
                        if p.accidental.displayType != 'even-tied':
                            remainP.accidental.displayStatus = False
                    else:  # display tied accidentals
                        remainP.accidental.displayType = 'even-tied'
                        remainP.accidental.displayStatus = True

        if eRemain.duration.quarterLength > 0.0:
            st = _SplitTuple([e, eRemain])
        else:
            st = _SplitTuple([e, None])

        if spannerList:
            st.spannerList = spannerList

        return st

    def splitByQuarterLengths(
        self,
        quarterLengthList: list[int | float | fractions.Fraction],
        addTies=True,
        displayTiedAccidentals=False
    ) -> _SplitTuple:
        '''
        Given a list of quarter lengths, return a list of
        Music21Object objects, copied from this Music21Object,
        that are partitioned and tied with the specified quarter
        length list durations.

        TODO: unite into a "split" function -- document obscure uses.

        >>> n = note.Note()
        >>> n.quarterLength = 3
        >>> post = n.splitByQuarterLengths([1, 1, 1])
        >>> [n.quarterLength for n in post]
        [1.0, 1.0, 1.0]
        '''
        if opFrac(sum(quarterLengthList)) != self.duration.quarterLength:
            raise Music21ObjectException(
                'cannot split by quarter length list whose sum is not '
                + 'equal to the quarterLength duration of the source: '
                + f'{quarterLengthList}, {self.duration.quarterLength}'
            )

        # if nothing to do
        if len(quarterLengthList) == 1:
            # return a copy of self in a list
            return _SplitTuple([copy.deepcopy(self)])
        elif len(quarterLengthList) <= 1:
            raise Music21ObjectException(
                f'cannot split by this quarter length list: {quarterLengthList}.')

        eList = []
        spannerList = []  # this does not fully work with trills over multiple splits yet.
        eRemain = copy.deepcopy(self)
        for qlIndex in range(len(quarterLengthList) - 1):
            qlSplit = quarterLengthList[qlIndex]
            st = eRemain.splitAtQuarterLength(qlSplit,
                                              addTies=addTies,
                                              displayTiedAccidentals=displayTiedAccidentals)
            newEl, eRemain = st
            eList.append(newEl)
            spannerList.extend(st.spannerList)

        if eRemain is not None:
            eList.append(eRemain)

        stOut = _SplitTuple(eList)
        stOut.spannerList = spannerList
        return stOut

    def splitAtDurations(self) -> _SplitTuple:
        '''
        Takes a Music21Object (e.g., a note.Note) and returns a list of similar
        objects with only a single duration.DurationTuple in each.
        Ties are added if the object supports ties.

        Articulations only appear on the first note.  Same with lyrics.

        Fermatas should be on last note, but not done yet.

        >>> a = note.Note()
        >>> a.duration.clear()  # remove defaults
        >>> a.duration.addDurationTuple(duration.durationTupleFromTypeDots('half', 0))
        >>> a.duration.quarterLength
        2.0
        >>> a.duration.addDurationTuple(duration.durationTupleFromTypeDots('whole', 0))
        >>> a.duration.quarterLength
        6.0
        >>> b = a.splitAtDurations()
        >>> b
        (<music21.note.Note C>, <music21.note.Note C>)
        >>> b[0].pitch == b[1].pitch
        True
        >>> b[0].duration
        <music21.duration.Duration 2.0>
        >>> b[0].duration.type
        'half'
        >>> b[1].duration.type
        'whole'
        >>> b[0].quarterLength, b[1].quarterLength
        (2.0, 4.0)

        >>> c = note.Note()
        >>> c.quarterLength = 2.5
        >>> d, e = c.splitAtDurations()
        >>> d.duration.type
        'half'
        >>> e.duration.type
        'eighth'
        >>> d.tie.type
        'start'
        >>> print(e.tie)
        <music21.tie.Tie stop>

        Assume c is tied to the next note.  Then the last split note should also be tied

        >>> c.tie = tie.Tie('start')
        >>> d, e = c.splitAtDurations()
        >>> d.tie.type
        'start'
        >>> e.tie.type
        'continue'

        Rests have no ties:

        >>> f = note.Rest()
        >>> f.quarterLength = 2.5
        >>> g, h = f.splitAtDurations()
        >>> (g.duration.type, h.duration.type)
        ('half', 'eighth')
        >>> f.tie is None
        True
        >>> g.tie is None
        True


        It should work for complex notes with tuplets.

        (this duration occurs in Modena A, Le greygnour bien, from the ars subtilior, c. 1380;
        hence how I discovered this bug)

        >>> n = note.Note()
        >>> n.duration.quarterLength = 0.5 + 0.0625  # eighth + 64th
        >>> tup = duration.Tuplet(4, 3)
        >>> n.duration.appendTuplet(tup)
        >>> first, last = n.splitAtDurations()
        >>> (first.duration, last.duration)
        (<music21.duration.Duration 0.375>, <music21.duration.Duration 0.046875>)

        Notice that this duration could have been done w/o tuplets, so no tuplets in output:

        >>> (first.duration.type, first.duration.dots, first.duration.tuplets)
        ('16th', 1, ())
        >>> (last.duration.type, last.duration.dots, last.duration.tuplets)
        ('128th', 1, ())

        Test of one with tuplets that cannot be split:

        >>> n = note.Note()
        >>> n.duration.quarterLength = 0.5 + 0.0625  # eighth + 64th
        >>> tup = duration.Tuplet(3, 2, 'eighth')
        >>> n.duration.appendTuplet(tup)
        >>> (n.duration.type, n.duration.dots, n.duration.tuplets)
        ('complex', 0, (<music21.duration.Tuplet 3/2/eighth>,))

        >>> first, last = n.splitAtDurations()
        >>> (first.duration, last.duration)
        (<music21.duration.Duration 1/3>, <music21.duration.Duration 1/24>)

        >>> (first.duration.type, first.duration.dots, first.duration.tuplets)
        ('eighth', 0, (<music21.duration.Tuplet 3/2/eighth>,))
        >>> (last.duration.type, last.duration.dots, last.duration.tuplets)
        ('64th', 0, (<music21.duration.Tuplet 3/2/64th>,))


        TODO: unite this and other functions into a "split" function -- document obscure uses.

        '''
        atm = self.duration.aggregateTupletMultiplier()
        quarterLengthList = [opFrac(c.quarterLength * atm) for c in self.duration.components]
        splitList = self.splitByQuarterLengths(quarterLengthList)
        return splitList
    # -------------------------------------------------------------------------
    # temporal and beat based positioning

    @property
    def measureNumber(self) -> int | None:
        # noinspection PyShadowingNames
        '''
        Return the measure number of a :class:`~music21.stream.Measure` that contains this
        object if the object is in a measure.

        Returns None if the object is not in a measure.  Also note that by
        default Measure objects
        have measure number 0.

        If an object belongs to multiple measures (not in the same hierarchy...)
        then it returns the
        measure number of the :meth:`~music21.base.Music21Object.activeSite` if that is a
        :class:`~music21.stream.Measure` object.  Otherwise, it will use
        :meth:`~music21.base.Music21Object.getContextByClass`
        to find the number of the measure it was most recently added to.

        >>> m = stream.Measure()
        >>> m.number = 12
        >>> n = note.Note()
        >>> m.append(n)
        >>> n.measureNumber
        12

        >>> n2 = note.Note()
        >>> n2.measureNumber is None
        True
        >>> m2 = stream.Measure()
        >>> m2.append(n2)
        >>> n2.measureNumber
        0

        The property updates if the object's surrounding measure's number changes:

        >>> m2.number = 11
        >>> n2.measureNumber
        11


        The most recent measure added to is used unless activeSite is a measure:

        >>> m.append(n2)
        >>> n2.measureNumber
        12
        >>> n2.activeSite = m2
        >>> n2.measureNumber
        11

        Copies can retain measure numbers until set themselves:

        >>> import copy
        >>> nCopy = copy.deepcopy(n2)
        >>> nCopy.measureNumber
        12
        >>> m3 = stream.Measure()
        >>> m3.number = 4
        >>> m3.append(nCopy)
        >>> nCopy.measureNumber
        4
        '''
        mNumber = None  # default for not defined
        if self.activeSite is not None and self.activeSite.isMeasure:
            mNumber = self.activeSite.number
        else:
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            for cs in self.contextSites():
                m = cs[0]
                if m.isMeasure:
                    # mypy does not know that isMeasure is a typeGuard.
                    mNumber = m.number  # type: ignore
        return mNumber

    def _getMeasureOffset(self, includeMeasurePadding=True) -> float | fractions.Fraction:
        # noinspection PyShadowingNames
        '''
        Try to obtain the nearest Measure that contains this object,
        and return the offset of this object within that Measure.

        If a Measure is found, and that Measure has padding
        defined as `paddingLeft` (for pickup measures, etc.), padding will be added to the
        native offset gathered from the object.

        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> n._getMeasureOffset()  # returns zero when not assigned
        0.0
        >>> n.quarterLength = 0.5

        >>> m = stream.Measure()
        >>> m.repeatAppend(n, 4)
        >>> [n._getMeasureOffset() for n in m.notes]
        [0.0, 0.5, 1.0, 1.5]

        >>> m.paddingLeft = 2.0
        >>> [n._getMeasureOffset() for n in m.notes]
        [2.0, 2.5, 3.0, 3.5]
        >>> [n._getMeasureOffset(includeMeasurePadding=False) for n in m.notes]
        [0.0, 0.5, 1.0, 1.5]
        '''
        from music21 import stream

        # TODO: v8 -- expose as public.
        activeS = self.activeSite
        if activeS is not None and activeS.isMeasure:
            # environLocal.printDebug(['found activeSite as Measure, using for offset'])
            offsetLocal = activeS.elementOffset(self)
            if includeMeasurePadding:
                offsetLocal += activeS.paddingLeft
        else:
            # environLocal.printDebug(['did not find activeSite as Measure,
            #    doing context search', 'self.activeSite', self.activeSite])
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            m = self.getContextByClass(stream.Measure, sortByCreationTime=True)
            if m is not None:
                # environLocal.printDebug(['using found Measure for offset access'])
                try:
                    offsetLocal = m.elementOffset(self)
                    if includeMeasurePadding:
                        offsetLocal += m.paddingLeft
                except SitesException:
                    offsetLocal = self.offset

            else:  # hope that we get the right one
                # environLocal.printDebug(
                #  ['_getMeasureOffset(): cannot find a Measure; using standard offset access'])
                offsetLocal = self.offset

        # environLocal.printDebug(
        #     ['_getMeasureOffset(): found local offset as:', offsetLocal, self])
        return offsetLocal

    def _getTimeSignatureForBeat(self) -> meter.TimeSignature:
        '''
        used by all the _getBeat, _getBeatDuration, _getBeatStrength functions.

        extracted to make sure that all three of the routines use the same one.
        '''
        from music21 import meter
        ts: meter.TimeSignature | None = self.getContextByClass(
            meter.TimeSignature,
            getElementMethod=ElementSearch.AT_OR_BEFORE_OFFSET
        )
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')
        return ts

    @property
    def beat(self) -> fractions.Fraction | float:
        # noinspection PyShadowingNames
        '''
        Return the beat of this object as found in the most
        recently positioned Measure. Beat values count from 1 and
        contain a floating-point designation between 0 and 1 to
        show proportional progress through the beat.

        >>> n = note.Note()
        >>> n.quarterLength = 0.5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [n.beat for n in m.notes]
        [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]


        Fractions are returned for positions that cannot be represented perfectly using floats:

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [n.beat for n in m.notes]
        [1.0, Fraction(4, 3), Fraction(5, 3), 2.0, Fraction(7, 3), Fraction(8, 3)]

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beat for n in s.notes]
        [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0]


        Notes inside flat streams can still find the original beat placement from outer
        streams:

        >>> p = stream.Part()
        >>> ts = meter.TimeSignature('2/4')
        >>> p.insert(0, ts)

        >>> n = note.Note('C4', type='eighth')
        >>> m1 = stream.Measure(number=1)
        >>> m1.repeatAppend(n, 4)

        >>> m2 = stream.Measure(number=2)
        >>> m2.repeatAppend(n, 4)

        >>> p.append([m1, m2])
        >>> [n.beat for n in p.flatten().notes]
        [1.0, 1.5, 2.0, 2.5, 1.0, 1.5, 2.0, 2.5]


        Fractions print out as improper fraction strings

        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1/3
        >>> m.repeatAppend(n, 12)
        >>> for n in m.notes[:5]:
        ...    print(n.beat)
        1.0
        4/3
        5/3
        2.0
        7/3

        If there is no TimeSignature object in sites then returns the special float
        `nan` meaning "Not a Number":

        >>> isolatedNote = note.Note('E4')
        >>> isolatedNote.beat
        nan

        Not-a-number objects do not compare equal to themselves:

        >>> isolatedNote.beat == isolatedNote.beat
        False

        Instead, to test for `nan`, import the math module and use `isnan()`:

        >>> import math
        >>> math.isnan(isolatedNote.beat)
        True

        * Changed in v6.3: returns `nan` if
          there is no TimeSignature in sites.
          Previously raised an exception.
        '''
        try:
            ts = self._getTimeSignatureForBeat()
            return ts.getBeatProportion(ts.getMeasureOffsetOrMeterModulusOffset(self))
        except Music21ObjectException:
            return float('nan')

    @property
    def beatStr(self) -> str:
        '''
        Return a string representation of the beat of
        this object as found in the most recently positioned
        Measure. Beat values count from 1 and contain a
        fractional designation to show progress through the beat.


        >>> n = note.Note(type='eighth')
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)

        >>> [n.beatStr for n in m.notes]
        ['1', '1 1/2', '2', '2 1/2', '3', '3 1/2']

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [n.beatStr for n in m.notes]
        ['1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3']

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('3/4'))
        >>> s.repeatAppend(note.Note(type='quarter'), 8)
        >>> [n.beatStr for n in s.notes]
        ['1', '2', '3', '1', '2', '3', '1', '2']

        If there is no TimeSignature object in sites then returns 'nan' for not a number.

        >>> isolatedNote = note.Note('E4')
        >>> isolatedNote.beatStr
        'nan'

        * Changed in v6.3: returns 'nan' if
          there is no TimeSignature in sites.
          Previously raised an exception.
        '''
        try:
            ts = self._getTimeSignatureForBeat()
            return ts.getBeatProportionStr(ts.getMeasureOffsetOrMeterModulusOffset(self))
        except Music21ObjectException:
            return 'nan'

    @property
    def beatDuration(self) -> Duration:
        '''
        Return a :class:`~music21.duration.Duration` of the beat
        active for this object as found in the most recently
        positioned Measure.

        If extending beyond the Measure, or in a Stream with a TimeSignature,
        the meter modulus value will be returned.

        >>> n = note.Note('C4', type='eighth')
        >>> n.duration
        <music21.duration.Duration 0.5>

        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> n0 = m.notes.first()
        >>> n0.beatDuration
        <music21.duration.Duration 1.0>

        Notice that the beat duration is the same for all these notes
        and has nothing to do with the duration of the element itself

        >>> [n.beatDuration.quarterLength for n in m.notes]
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

        Changing the time signature changes the beat duration:

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [n.beatDuration.quarterLength for n in m.notes]
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5]

        Complex time signatures will give different note lengths:

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('2/4+3/4'))
        >>> s.repeatAppend(note.Note(type='quarter'), 8)
        >>> [n.beatDuration.quarterLength for n in s.notes]
        [2.0, 2.0, 3.0, 3.0, 3.0, 2.0, 2.0, 3.0]

        If there is no TimeSignature object in sites then returns a duration object
        of Zero length.

        >>> isolatedNote = note.Note('E4')
        >>> isolatedNote.beatDuration
        <music21.duration.Duration 0.0>

        * Changed in v6.3: returns a duration.Duration object of length 0 if
          there is no TimeSignature in sites.  Previously raised an exception.
        '''
        try:
            ts = self._getTimeSignatureForBeat()
            return ts.getBeatDuration(ts.getMeasureOffsetOrMeterModulusOffset(self))
        except Music21ObjectException:
            return Duration(0)

    @property
    def beatStrength(self) -> float:
        '''
        Return the metrical accent of this object
        in the most recently positioned Measure. Accent values
        are between zero and one, and are derived from the local
        TimeSignature's accent MeterSequence weights. If the offset
        of this object does not match a defined accent weight, a
        minimum accent weight will be returned.


        >>> n = note.Note(type='eighth')
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)

        The first note of a measure is (generally?) always beat strength 1.0:

        >>> m.notes.first().beatStrength
        1.0

        Notes on weaker beats have lower strength:

        >>> [n.beatStrength for n in m.notes]
        [1.0, 0.25, 0.5, 0.25, 0.5, 0.25]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [n.beatStrength for n in m.notes]
        [1.0, 0.25, 0.25, 0.5, 0.25, 0.25]


        Importantly, the actual numbers here have no particular meaning.  You cannot
        "add" two beatStrengths of 0.25 and say that they have the same beat strength
        as one note of 0.5.  Only the ordinal relations really matter.  Even taking
        an average of beat strengths is a tiny bit methodologically suspect (though
        it is common in research for lack of a better method).

        We can also get the beatStrength for elements not in
        a measure, if the enclosing stream has a :class:`~music21.meter.TimeSignature`.
        We just assume that the time signature carries through to
        hypothetical following measures:

        >>> n = note.Note('E-3', type='quarter')
        >>> s = stream.Stream()
        >>> s.insert(0.0, meter.TimeSignature('2/2'))
        >>> s.repeatAppend(n, 12)
        >>> [n.beatStrength for n in s.notes]
        [1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25]


        Changing the meter changes the output, of course, as can be seen from the
        fourth quarter note onward:

        >>> s.insert(4.0, meter.TimeSignature('3/4'))
        >>> [n.beatStrength for n in s.notes]
        [1.0, 0.25, 0.5, 0.25, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5]


        The method returns correct numbers for the prevailing time signature
        even if no measures have been made:

        >>> n = note.Note('E--3', type='half')
        >>> s = stream.Stream()
        >>> s.isMeasure
        False

        >>> s.insert(0, meter.TimeSignature('2/2'))
        >>> s.repeatAppend(n, 16)
        >>> s.notes[0].beatStrength
        1.0
        >>> s.notes[1].beatStrength
        0.5
        >>> s.notes[4].beatStrength
        1.0
        >>> s.notes[5].beatStrength
        0.5

        Getting the beatStrength of an object without a time signature in its context
        returns the not-a-number special object 'nan':

        >>> n2 = note.Note(type='whole')
        >>> n2.beatStrength
        nan
        >>> from math import isnan
        >>> isnan(n2.beatStrength)
        True

        * Changed in v6.3: return 'nan' instead of raising an exception.
        '''
        try:
            ts = self._getTimeSignatureForBeat()
            meterModulus = ts.getMeasureOffsetOrMeterModulusOffset(self)

            return ts.getAccentWeight(meterModulus,
                                      forcePositionMatch=True,
                                      permitMeterModulus=False)
        except Music21ObjectException:
            return float('nan')

    def _getSeconds(self) -> float:
        from music21 import tempo
        # do not search of duration is zero
        if self.duration.quarterLength == 0.0:
            return 0.0

        ti = self.getContextByClass(tempo.TempoIndication)
        if ti is None:
            return float('nan')
        mm = ti.getSoundingMetronomeMark()
        # once we have mm, simply pass in this duration
        return mm.durationToSeconds(self.duration)

    def _setSeconds(self, value: int | float) -> None:
        from music21 import tempo
        ti = self.getContextByClass(tempo.TempoIndication)
        if ti is None:
            raise Music21ObjectException('this object does not have a TempoIndication in Sites')
        mm = ti.getSoundingMetronomeMark()
        self.duration = mm.secondsToDuration(value)
        for s in self.sites.get(excludeNone=True):
            if self in s.elements:
                s.coreElementsChanged()  # highest time is changed.

    seconds = property(_getSeconds, _setSeconds, doc='''
        Get or set the duration of this object in seconds, assuming
        that this object has a :class:`~music21.tempo.MetronomeMark`
        or :class:`~music21.tempo.MetricModulation`
        (or any :class:`~music21.tempo.TempoIndication`) in its past context.

        >>> s = stream.Stream()
        >>> for i in range(3):
        ...    s.append(note.Note(type='quarter'))
        ...    s.append(note.Note(type='quarter', dots=1))
        >>> s.insert(0, tempo.MetronomeMark(number=60))
        >>> s.insert(2, tempo.MetronomeMark(number=120))
        >>> s.insert(4, tempo.MetronomeMark(number=30))
        >>> [n.seconds for n in s.notes]
        [1.0, 1.5, 0.5, 0.75, 2.0, 3.0]

        Setting the number of seconds on a music21 object changes its duration:

        >>> lastNote = s.notes[-1]
        >>> lastNote.duration.fullName
        'Dotted Quarter'
        >>> lastNote.seconds = 4.0
        >>> lastNote.duration.fullName
        'Half'

        Any object of length 0 has zero-second length:

        >>> tc = clef.TrebleClef()
        >>> tc.seconds
        0.0

        If an object has positive duration but no tempo indication in its context,
        then the special number 'nan' for "not-a-number" is returned:

        >>> r = note.Rest(type='whole')
        >>> r.seconds
        nan

        Check for 'nan' with the `math.isnan()` routine:

        >>> import math
        >>> math.isnan(r.seconds)
        True

        Setting seconds for an element without a tempo-indication in its sites raises
        a Music21ObjectException:

        >>> r.seconds = 2.0
        Traceback (most recent call last):
        music21.base.Music21ObjectException: this object does not have a TempoIndication in Sites

        Note that if an object is in multiple Sites with multiple Metronome marks,
        the activeSite (or the hierarchy of the activeSite)
        determines its seconds for getting or setting:

        >>> r = note.Rest(type='whole')
        >>> m1 = stream.Measure()
        >>> m1.insert(0, tempo.MetronomeMark(number=60))
        >>> m1.append(r)
        >>> r.seconds
        4.0

        >>> m2 = stream.Measure()
        >>> m2.insert(0, tempo.MetronomeMark(number=120))
        >>> m2.append(r)
        >>> r.seconds
        2.0
        >>> r.activeSite = m1
        >>> r.seconds
        4.0
        >>> r.seconds = 1.0
        >>> r.duration.type
        'quarter'
        >>> r.activeSite = m2
        >>> r.seconds = 1.0
        >>> r.duration.type
        'half'

        * Changed in v6.3: return `nan` instead of raising an exception.
        ''')


# ------------------------------------------------------------------------------
_m21ObjDefaultDefinedKeys: tuple[str, ...] = tuple(dir(Music21Object()))

class ElementWrapper(Music21Object):
    '''
    An ElementWrapper is a way of containing any object that is not a
    :class:`~music21.base.Music21Object`, so that that object can be positioned
    within a :class:`~music21.stream.Stream`.

    The object stored within ElementWrapper is available from the
    :attr:`~music21.base.ElementWrapper.obj` attribute.  All the attributes of
    the stored object (except .id and anything else that conflicts with a
    Music21Object attribute) are gettable and settable by querying the
    ElementWrapper.  This feature makes it possible easily to mix
    Music21Objects and non-Music21Objects with similarly named attributes in
    the same Stream.

    This example inserts 10 random wave files into a music21 Stream and then
    reports their filename and number of audio channels (in this example, it's
    always 2) if they fall on a strong beat in fast 6/8

    >>> import music21
    >>> #_DOCS_SHOW import wave
    >>> import random
    >>> class Wave_read: #_DOCS_HIDE
    ...    def getnchannels(self): return 2 #_DOCS_HIDE

    >>> s = stream.Stream()
    >>> s.id = 'mainStream'
    >>> s.append(meter.TimeSignature('fast 6/8'))
    >>> for i in range(10):
    ...    #_DOCS_SHOW fileName = 'thisSound_' + str(random.randint(1, 20)) + '.wav'
    ...    fileName = 'thisSound_' + str(1 + ((i * 100) % 19)) + '.wav' #_DOCS_HIDE
    ...    soundFile = Wave_read() #_DOCS_HIDE # #make a more predictable "random" set.
    ...    #_DOCS_SHOW soundFile = wave.open(fileName)
    ...    soundFile.fileName = fileName
    ...    el = music21.ElementWrapper(soundFile)
    ...    s.insert(i, el)

    >>> for j in s.getElementsByClass(base.ElementWrapper):
    ...    if j.beatStrength > 0.4:
    ...        (j.offset, j.beatStrength, j.getnchannels(), j.fileName)
    (0.0, 1.0, 2, 'thisSound_1.wav')
    (3.0, 1.0, 2, 'thisSound_16.wav')
    (6.0, 1.0, 2, 'thisSound_12.wav')
    (9.0, 1.0, 2, 'thisSound_8.wav')
    >>> for j in s.getElementsByClass(base.ElementWrapper):
    ...    if j.beatStrength > 0.4:
    ...        (j.offset, j.beatStrength, j.getnchannels() + 1, j.fileName)
    (0.0, 1.0, 3, 'thisSound_1.wav')
    (3.0, 1.0, 3, 'thisSound_16.wav')
    (6.0, 1.0, 3, 'thisSound_12.wav')
    (9.0, 1.0, 3, 'thisSound_8.wav')

    Test representation of an ElementWrapper

    >>> for i, j in enumerate(s.getElementsByClass(base.ElementWrapper)):
    ...     if i == 2:
    ...         j.id = None
    ...     else:
    ...         j.id = str(i) + '_wrapper'
    ...     if i <=2:
    ...         print(j)
    <music21.base.ElementWrapper id=0_wrapper offset=0.0 obj='<...Wave_read object...'>
    <music21.base.ElementWrapper id=1_wrapper offset=1.0 obj='<...Wave_read object...'>
    <music21.base.ElementWrapper offset=2.0 obj='<...Wave_read object...>'>

    Equality
    --------
    Two ElementWrappers are equal if they would be equal as Music21Objects and they
    wrap objects that are equal.

    >>> list1 = ['a', 'b', 'c']
    >>> a = base.ElementWrapper(list1)
    >>> a.offset = 3.0

    >>> list2 = ['a', 'b', 'c']
    >>> b = base.ElementWrapper(list2)
    >>> b.offset = 3.0
    >>> a == b
    True
    >>> a is not b
    True

    Offset does not need to be equal for equality:

    >>> b.offset = 4.0
    >>> a == b
    True

    But elements must compare equal

    >>> list2.append('d')
    >>> a == b
    False

    * Changed in v9: completely different approach to equality, unified w/
      the rest of music21.
    '''
    equalityAttributes = ('obj',)

    _DOC_ORDER = ['obj']
    _DOC_ATTR: dict[str, str] = {
        'obj': '''
        The object this wrapper wraps. It should not be a Music21Object, since
        if so, you might as well put that directly into the Stream itself.''',
    }

    def __init__(self, obj: t.Any = None, **keywords):
        # note that because of how __setattr__ is overridden and needs
        # to have a self.obj, we set this here.
        self.obj: t.Any = obj  # object stored here
        super().__init__(**keywords)

    # -------------------------------------------------------------------------

    def _reprInternal(self):
        shortObj = (str(self.obj))[0:30]
        if len(str(self.obj)) > 30:
            shortObj += '...'
            if shortObj[0] == '<':
                shortObj += '>'

        if self._id is not None:
            return f'id={self.id} offset={self.offset} obj={shortObj!r}'
        else:
            return f'offset={self.offset} obj={shortObj!r}'

    def __setattr__(self, name: str, value: t.Any) -> None:
        if name == 'obj':
            object.__setattr__(self, 'obj', value)
            return
        # environLocal.printDebug(['calling __setattr__ of ElementWrapper', name, value])

        # if in the ElementWrapper already, set that first
        if name in self.__dict__:
            object.__setattr__(self, name, value)

        # if not, change the attribute in the stored object
        storedObj = object.__getattribute__(self, 'obj')
        if (name not in _m21ObjDefaultDefinedKeys
                and storedObj is not None
                and hasattr(storedObj, name)):
            setattr(storedObj, name, value)
        else:
            # unless neither has the attribute, in which case add it to the ElementWrapper
            object.__setattr__(self, name, value)

    def __getattr__(self, name: str) -> t.Any:
        '''
        This method is only called when __getattribute__() fails.
        Using this also avoids the potential recursion problems of subclassing
        __getattribute__()_

        see: https://stackoverflow.com/questions/371753/python-using-getattribute-method
        for examples
        '''
        storedObj = Music21Object.__getattribute__(self, 'obj')
        if storedObj is None:
            raise AttributeError(f'Could not get attribute {name!r} in an object-less element')
        return object.__getattribute__(storedObj, name)


class Test(unittest.TestCase):
    '''
    All other tests moved to test/test_base.py
    '''
    def testCopyAndDeepcopy(self):
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Music21Object, ElementWrapper]


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest()  # , runTest='testPreviousB')
