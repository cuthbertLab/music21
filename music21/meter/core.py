# -----------------------------------------------------------------------------
# Name:         meter.core.py
# Purpose:      Component objects for meters
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009-2024 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
This module defines two component objects for defining nested metrical structures:
:class:`~music21.meter.core.MeterTerminal` and :class:`~music21.meter.core.MeterSequence`.
'''
from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
import typing as t

from music21 import common
from music21.common.numberTools import opFrac
from music21.common.objects import FrozenObject
from music21.common.types import OffsetQLIn
from music21.duration import FrozenDuration
from music21 import environment
from music21.exceptions21 import MeterException
from music21.meter import tools
from music21 import prebase

environLocal = environment.Environment('meter.core')

# a MeterTerminal or a MeterSequence, the two kinds of things that can appear
# inside a MeterSequence's partition.  (PEP 695 type aliases are evaluated
# lazily, so the forward references resolve fine.)
type MeterNode = MeterTerminal | MeterSequence


# -----------------------------------------------------------------------------
class MeterCore:
    '''
    A mixin holding the read-only behavior shared by both
    :class:`~music21.meter.core.MeterTerminal` and
    :class:`~music21.meter.core.MeterSequence`.

    Each subclass supplies ``numerator``, ``denominator``, and ``weight``
    properties; MeterCore provides the derived, immutable behaviors: the
    duration, ratio comparison, and the various ``subdivide`` methods (which
    build and return a new :class:`~music21.meter.core.MeterSequence`).

    AI-assisted (Claude).
    '''
    __slots__ = ()

    # these are supplied by the concrete classes as read-only properties;
    # declared here (as stubs) for the type checker and to document the contract.
    @property
    def numerator(self) -> int:
        raise NotImplementedError  # pragma: no cover

    @property
    def denominator(self) -> int:
        raise NotImplementedError  # pragma: no cover

    @property
    def weight(self) -> float:
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    @lru_cache(1024)
    def _durationFromNumeratorDenominator(
        numerator: int,
        denominator: int,
    ) -> FrozenDuration:
        '''
        Return the (immutable) duration equal in length to a numerator/denominator
        ratio.

        Cached, since a small set of ratios (1/4, 1/8, 3/8, ...) recurs constantly.

        >>> meter.core.MeterTerminal._durationFromNumeratorDenominator(3, 8)
        <music21.duration.FrozenDuration 1.5>

        AI-assisted (Claude).
        '''
        # NOTE: this is a performance critical method.
        return FrozenDuration(quarterLength=(4.0 * numerator) / denominator)

    @property
    def duration(self) -> FrozenDuration:
        '''
        Returns a :class:`~music21.duration.FrozenDuration` equal in length to this
        terminal (or sequence).  It is shared and cached, and therefore immutable:

        >>> a = meter.MeterTerminal('3/8')
        >>> a.duration
        <music21.duration.FrozenDuration 1.5>
        >>> a.duration.type
        'quarter'
        >>> a.duration.dots
        1

        Trying to change it raises an exception:

        >>> a.duration.quarterLength = 5.0
        Traceback (most recent call last):
        TypeError: This FrozenDuration instance is immutable.

        If you need a changeable duration, unfreeze it first:

        >>> changeable = a.duration.unfreeze()
        >>> changeable.quarterLength = 5.0
        >>> changeable
        <music21.duration.Duration 5.0>

        * Changed in v11: returns a shared, immutable
          :class:`~music21.duration.FrozenDuration` (was a mutable Duration).
        '''
        return self._durationFromNumeratorDenominator(self.numerator, self.denominator)

    def _reprInternal(self):
        return str(self)

    def ratioEqual(self, other) -> bool:
        '''
        Compare the numerator and denominator of another object.
        Note that these have to be exact matches; 3/4 is not the same as 6/8

        >>> a = meter.MeterTerminal('3/4')
        >>> b = meter.MeterTerminal('6/4')
        >>> c = meter.MeterTerminal('2/4')
        >>> d = meter.MeterTerminal('3/4')
        >>> a.ratioEqual(b)
        False
        >>> a.ratioEqual(c)
        False
        >>> a.ratioEqual(d)
        True
        '''
        if other is None:
            return False
        if (other.numerator == self.numerator
                and other.denominator == self.denominator):
            return True
        else:
            return False

    # -------------------------------------------------------------------------

    def subdivideByCount(self, countRequest=None) -> MeterSequence:
        '''
        returns a MeterSequence made up of taking this MeterTerminal and
        subdividing it into the given number of parts.  Each of those parts
        is a MeterTerminal

        >>> a = meter.MeterTerminal('3/4')
        >>> b = a.subdivideByCount(3)
        >>> b
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> len(b)
        3
        >>> b[0]
        <music21.meter.core.MeterTerminal 1/4>

        What happens if we do this?

        >>> a = meter.MeterTerminal('5/8')
        >>> b = a.subdivideByCount(2)
        >>> b
        <music21.meter.core.MeterSequence {2/8+3/8}>
        >>> len(b)
        2
        >>> b[0]
        <music21.meter.core.MeterTerminal 2/8>
        >>> b[1]
        <music21.meter.core.MeterTerminal 3/8>

        But what if you want to divide into 3/8+2/8 or something else?
        for that, see the :meth:`~music21.meter.MeterSequence.partition` method
        of :class:`~music21.meter.MeterSequence`.
        '''
        # cannot set the weight of this MeterSequence w/o having offsets
        # pass this object as an argument; when subdividing, use autoWeight
        return _buildSequence(self, countRequest, autoWeight=True, targetWeight=self.weight)

    def subdivideByList(self, numeratorList) -> MeterSequence:
        '''
        Return a MeterSequence dividing this
        MeterTerminal according to the numeratorList

        >>> a = meter.MeterTerminal('3/4')
        >>> b = a.subdivideByList([1, 1, 1])
        >>> b
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> len(b)
        3
        >>> b[0]
        <music21.meter.core.MeterTerminal 1/4>

        Unequal subdivisions work:

        >>> c = a.subdivideByList([1, 2])
        >>> c
        <music21.meter.core.MeterSequence {1/4+2/4}>
        >>> len(c)
        2
        >>> (c[0], c[1])
        (<music21.meter.core.MeterTerminal 1/4>, <music21.meter.core.MeterTerminal 2/4>)

        So does subdividing by strings

        >>> c = a.subdivideByList(['2/4', '1/4'])
        >>> len(c)
        2
        >>> (c[0], c[1])
        (<music21.meter.core.MeterTerminal 2/4>, <music21.meter.core.MeterTerminal 1/4>)

        See :meth:`~music21.meter.MeterSequence.partitionByList` method
        of :class:`~music21.meter.MeterSequence` for more details.
        '''
        # elevate to meter sequence, then partition
        ms = _buildSequence(self)  # do not need to autoWeight here
        return ms.partitionByList(numeratorList)  # this will split weight

    def subdivideByOther(self, other: MeterSequence) -> MeterSequence:
        '''
        Return a MeterSequence based on another MeterSequence

        >>> a = meter.MeterSequence('1/4+1/4+1/4')
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> b = meter.MeterSequence('3/8+3/8')
        >>> a.subdivideByOther(b)
        <music21.meter.core.MeterSequence {{3/8+3/8}}>

        >>> terminal = meter.MeterTerminal('1/4')
        >>> divider = meter.MeterSequence('1/8+1/8')
        >>> terminal.subdivideByOther(divider)
        <music21.meter.core.MeterSequence {{1/8+1/8}}>
        '''
        if other.duration.quarterLength != self.duration.quarterLength:
            raise MeterException(f'cannot subdivide by other: {other}')
        # elevate to meter sequence
        return _buildSequence(other)  # do not need to autoWeight here

    def subdivide(
        self,
        value: Sequence[int | str] | MeterSequence | int
    ) -> MeterSequence:
        '''
        Subdivision takes a MeterTerminal and, making it into a collection of MeterTerminals,
        Returns a MeterSequence.

        This is different from partitioning a MeterSequence. `subdivide` does not happen
        in place and instead returns a new object.

        If an integer is provided, assume it is a partition count.
        '''
        if common.isListLike(value):
            return self.subdivideByList(value)
        elif isinstance(value, MeterSequence):
            return self.subdivideByOther(value)
        elif common.isNum(value):
            return self.subdivideByCount(value)
        else:
            raise MeterException(f'cannot process partition argument {value}')


# -----------------------------------------------------------------------------

class MeterTerminal(prebase.ProtoM21Object, MeterCore, FrozenObject):
    '''
    A MeterTerminal is a nestable primitive of rhythmic division.

    >>> a = meter.MeterTerminal('2/4')
    >>> a.duration.quarterLength
    2.0
    >>> a = meter.MeterTerminal('3/8')
    >>> a.duration.quarterLength
    1.5
    >>> a = meter.MeterTerminal('5/2')
    >>> a.duration.quarterLength
    10.0

    A MeterTerminal is an immutable value object defined solely by its
    numerator, denominator, and weight.  Its attributes cannot be changed
    after creation; instead make a new one (see :func:`getMeterTerminal`):

    >>> a.numerator = 6
    Traceback (most recent call last):
    TypeError: This MeterTerminal instance is immutable.

    Because it is immutable, deep-copying a MeterTerminal returns the same
    shared object, and equality is by value:

    >>> import copy
    >>> copy.deepcopy(a) is a
    True
    >>> meter.MeterTerminal('2/4') == meter.MeterTerminal('2/4')
    True

    * Changed in v11: MeterTerminal is immutable, deep-copies to itself, and
      compares by value.  Removed the numerator/denominator/weight/duration
      setters (set values when creating the terminal, or use `modify()`).

    AI-assisted (Claude).
    '''
    # CLASS VARIABLES #

    __slots__ = (
        '_denominator',
        '_numerator',
        '_weight',
    )

    # slot type declarations (for the type checker); set via object.__setattr__
    _numerator: int
    _denominator: int
    _weight: float

    # INITIALIZER #
    def __init__(self, slashNotation: str|None = None, weight: float = 1.0, *,
                 numerator: int = 0, denominator: int = 1):
        if slashNotation is not None:
            # raise MeterException early if there is a problem.
            values = tools.slashToTuple(slashNotation)
            numerator = values.numerator
            denominator = values.denominator
        # Set the slots on the known-safe init path with object.__setattr__ to
        # bypass FrozenObject's expensive per-set inspection (which walks the
        # stack to find where in a sequence we are); afterwards the object is
        # fully immutable.
        object.__setattr__(self, '_numerator', numerator)
        object.__setattr__(self, '_denominator', denominator)
        object.__setattr__(self, '_weight', weight)

    # SPECIAL METHODS #

    def __deepcopy__(self, memo=None):
        '''
        Helper method for the deepcopy function in copy.py.

        Do not call this directly.

        A MeterTerminal is immutable and shared, so deep-copying it simply
        returns the same object (a large performance win, since MeterTerminals
        are copied constantly as part of Streams and TimeSignatures).
        '''
        return self

    def __copy__(self):
        '''
        A MeterTerminal is immutable, so a shallow copy is also just itself.
        '''
        return self

    def _reprInternal(self):
        return str(self)

    def __str__(self):
        return str(int(self.numerator)) + '/' + str(int(self.denominator))

    def modify(self, **keywords) -> MeterTerminal:
        '''
        Return a (cached) MeterTerminal identical to this one except for the
        given ``numerator``, ``denominator`` and/or ``weight`` keyword(s); the
        other values carry over.  The original is unchanged, since a
        MeterTerminal is immutable.

        This is how to "change" an immutable terminal -- analogous to
        :func:`copy.replace` (Python 3.13+) or ``namedtuple._replace``.

        >>> a = meter.MeterTerminal('2/4', weight=0.5)
        >>> b = a.modify(weight=0.25)
        >>> b
        <music21.meter.core.MeterTerminal 2/4>
        >>> b.weight
        0.25

        The original is unchanged, and the un-named values carry over (here the
        weight stays 0.5):

        >>> a.weight
        0.5
        >>> c = a.modify(numerator=3)
        >>> c
        <music21.meter.core.MeterTerminal 3/4>
        >>> c.weight
        0.5

        modify goes through the cache, so identical results share one object:

        >>> a.modify(numerator=3) is c
        True

        AI-assisted (Claude).
        '''
        return getMeterTerminal(
            numerator=keywords.get('numerator', self._numerator),
            denominator=keywords.get('denominator', self._denominator),
            weight=keywords.get('weight', self._weight),
        )

    # copy.replace() support (Python 3.13+)
    __replace__ = modify

    # -------------------------------------------------------------------------
    # properties

    @property
    def weight(self) -> float:
        '''
        Return the weight of a MeterTerminal.

        >>> a = meter.MeterTerminal('2/4', 0.5)
        >>> a.weight
        0.5

        To get a MeterTerminal with a different weight, use :meth:`modify`:

        >>> a.modify(weight=0.25)
        <music21.meter.core.MeterTerminal 2/4>

        * Changed in v11: weight is immutable and must be a float (not int).
        '''
        return self._weight

    @property
    def numerator(self) -> int:
        '''
        Return the numerator of the MeterTerminal.

        >>> a = meter.MeterTerminal('2/4')
        >>> a.numerator
        2

        To get a MeterTerminal with a different numerator, use :meth:`modify`:

        >>> a.modify(numerator=3)
        <music21.meter.core.MeterTerminal 3/4>

        * Changed in v11: numerator is immutable.
        '''
        return self._numerator

    @property
    def denominator(self) -> int:
        '''
        Return the denominator of the MeterTerminal.

        >>> a = meter.MeterTerminal('2/4')
        >>> a.denominator
        4

        To get a MeterTerminal with a different denominator, use :meth:`modify`:

        >>> a.modify(denominator=8)
        <music21.meter.core.MeterTerminal 2/8>

        * Changed in v11: denominator is immutable.
        '''
        return self._denominator

    @property
    def depth(self):
        '''
        Return how many levels deep this part is -- the depth of a terminal is always 1
        '''
        return 1


# -----------------------------------------------------------------------------

_meterTerminalCache: dict[tuple[int, int, float], MeterTerminal] = {}


def getMeterTerminal(numerator: int, denominator: int,
                     weight: float = 1.0) -> MeterTerminal:
    '''
    Return a shared, cached, immutable :class:`MeterTerminal` for these values.

    Because MeterTerminals are immutable, identical `(numerator, denominator,
    weight)` triples can all share one object.  This is how a "changed" terminal
    is produced: instead of mutating an existing terminal, request the cached
    terminal for the new values.

    >>> mt = meter.core.getMeterTerminal(1, 4)
    >>> mt
    <music21.meter.core.MeterTerminal 1/4>
    >>> meter.core.getMeterTerminal(1, 4) is mt
    True
    >>> meter.core.getMeterTerminal(1, 4, weight=0.5) is mt
    False

    AI-assisted (Claude).
    '''
    key = (numerator, denominator, weight)
    cached = _meterTerminalCache.get(key)
    if cached is None:
        cached = MeterTerminal(numerator=numerator, denominator=denominator, weight=weight)
        _meterTerminalCache[key] = cached
    return cached


# -----------------------------------------------------------------------------


class MeterSequence(prebase.ProtoM21Object, MeterCore, FrozenObject):
    '''
    A MeterSequence is an immutable, hashable sequence of MeterTerminals, or
    other MeterSequences.

    >>> ms = meter.MeterSequence('4/4', 4)
    >>> ms
    <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>

    Like :class:`~music21.meter.core.MeterTerminal`, a MeterSequence is an
    immutable value object.  Its structure cannot be changed after creation;
    the "mutating" methods (:meth:`partition`, :meth:`subdividePartitionsEqual`,
    :meth:`setLevelWeight`, :meth:`setIndex`, ...) instead RETURN a new
    MeterSequence and leave ``self`` unchanged:

    >>> ms2 = ms.partition(2)
    >>> ms2
    <music21.meter.core.MeterSequence {1/2+1/2}>
    >>> ms
    <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>

    Because it is immutable, deep-copying a MeterSequence returns the same
    shared object, and equality is by value:

    >>> import copy
    >>> copy.deepcopy(ms) is ms
    True
    >>> meter.MeterSequence('4/4', 4) == meter.MeterSequence('4/4', 4)
    True

    * Changed in v11: MeterSequence is immutable, hashable, deep-copies to
      itself, and its formerly in-place operations return a new sequence.
      Removed `load()` (set values when creating the sequence), the `weight`
      setter (use `withWeight()`), and item assignment `ms[i] = x` (use
      `setIndex()`).

    AI-assisted (Claude).
    '''

    # CLASS VARIABLES #

    __slots__ = (
        '_denominator',
        '_numerator',
        '_partition',
        'parenthesis',
        'summedNumerator',
    )

    # slot type declarations (for the type checker); set via object.__setattr__
    _numerator: int
    _denominator: int
    _partition: tuple[MeterNode, ...]
    parenthesis: bool
    summedNumerator: bool

    # INITIALIZER #

    def __init__(
        self,
        value: str | MeterTerminal | Sequence[MeterTerminal] | Sequence[str] | None = None,
        partitionRequest: t.Any|None = None,
    ):
        # Build the data on the known-safe init path using object.__setattr__ to
        # bypass FrozenObject's expensive per-set inspection; after __init__ the
        # object is fully immutable.
        numerator, denominator, partitionList, summedNumerator = _loadData(value)
        parenthesis = False
        if partitionRequest is not None:
            built = makeSequence(
                numerator, denominator, tuple(partitionList),
                summedNumerator=summedNumerator
            ).partition(partitionRequest)
            numerator = built._numerator
            denominator = built._denominator
            partitionList = list(built._partition)
            summedNumerator = built.summedNumerator
            parenthesis = built.parenthesis

        object.__setattr__(self, '_numerator', numerator)
        object.__setattr__(self, '_denominator', denominator)
        object.__setattr__(self, '_partition', tuple(partitionList))
        object.__setattr__(self, 'summedNumerator', summedNumerator)
        object.__setattr__(self, 'parenthesis', parenthesis)

    # SPECIAL METHODS #

    def __deepcopy__(self, memo=None):
        '''
        A MeterSequence is immutable and shared, so deep-copying it simply
        returns the same object.

        >>> from copy import deepcopy
        >>> ms1 = meter.MeterSequence('4/4+3/8')
        >>> deepcopy(ms1) is ms1
        True
        '''
        return self

    def __copy__(self):
        '''
        A MeterSequence is immutable, so a shallow copy is also just itself.
        '''
        return self

    def modify(self, **keywords) -> MeterSequence:
        '''
        Return a (cached) MeterSequence identical to this one except for the
        given ``numerator``, ``denominator``,
        ``partition``, ``parenthesis`` and/or ``summedNumerator``
        keyword(s).

        The original is unchanged, since a MeterSequence is immutable.

        Analogous to :func:`copy.replace` (Python 3.13+); for changing the
        partition structure itself prefer the functional :meth:`partition`,
        :meth:`subdividePartitionsEqual`, and :meth:`setIndex`.

        >>> ms = meter.MeterSequence('4/4', 4)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>

        Modify so that there's a parenthesis around the whole sequence. The original
        is unchanged.

        >>> ms.parenthesis
        False
        >>> ms2 = ms.modify(parenthesis=True)
        >>> ms2.parenthesis
        True
        >>> ms.parenthesis
        False

        Changing the numerator or denominator rebuilds the sequence with that many
        equal parts:

        >>> ms3 = ms.modify(numerator=3)
        >>> ms3
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>

        Any other keyword, including weight, is ignored.

        >>> ms.weight
        1.0
        >>> ms.modify(weight=1.5).weight
        1.0

        For other changes to the MeterSequence, see methods
        :meth:`subdivide`, :meth:`partition`, etc.

        AI-assisted (Claude).
        '''
        if 'partition' in keywords:
            partition = tuple(keywords['partition'])
            numerator, denominator = _ratioFromPartition(partition)
        elif 'numerator' in keywords or 'denominator' in keywords:
            numerator = keywords.get('numerator', self._numerator)
            denominator = keywords.get('denominator', self._denominator)
            # rebuild the new ratio as `numerator` equal parts (each 1/denominator)
            partition = getMeterSequence(f'{numerator}/{denominator}', numerator)._partition
        else:
            partition = self._partition
            numerator, denominator = self._numerator, self._denominator
        return makeSequence(
            numerator, denominator, partition,
            parenthesis=keywords.get('parenthesis', self.parenthesis),
            summedNumerator=keywords.get('summedNumerator', self.summedNumerator),
        )

    # copy.replace() support (Python 3.13+)
    __replace__ = modify

    def __getitem__(self, key: int) -> MeterNode:
        '''
        Get an MeterTerminal (or MeterSequence) from _partition

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a[3].numerator
        1
        '''
        if abs(key) >= len(self):
            raise IndexError
        return self._partition[key]

    def __iter__(self):
        '''
        Support iteration of top level partitions

        >>> a = meter.MeterSequence('4/4', 2)
        >>> for x in a:
        ...     print(repr(x))
        <music21.meter.core.MeterTerminal 1/2>
        <music21.meter.core.MeterTerminal 1/2>
        '''
        return iter(self._partition)

    def __len__(self):
        '''
        Return the length of the partition list

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> len(a)
        4
        '''
        return len(self._partition)

    def setIndex(self, index: int, value: MeterNode) -> MeterSequence:
        '''
        Return a new MeterSequence with the element at `index` replaced by
        `value` (which must occupy the same ratio of time as the element it
        replaces).  This is the immutable replacement for the old
        ``ms[index] = value`` item assignment.

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> a[0]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a = a.setIndex(0, a[0].subdivide(2))
        >>> a
        <music21.meter.core.MeterSequence {{1/8+1/8}+1/4+1/4+1/4}>
        >>> a = a.setIndex(0, a[0].setIndex(0, a[0][0].subdivide(2)))
        >>> a
        <music21.meter.core.MeterSequence {{{1/16+1/16}+1/8}+1/4+1/4+1/4}>
        >>> a[3]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a.setIndex(3, a[0][0])
        Traceback (most recent call last):
        music21.exceptions21.MeterException: cannot insert {1/16+1/16} into space of 1/4

        * New in v11: functional replacement for ``ms[index] = value`` assignment.

        AI-assisted (Claude).
        '''
        # comparison of numerator and denominator
        if not isinstance(value, MeterCore):
            raise MeterException('values in MeterSequences must be MeterTerminals or '
                                 f'MeterSequences, not {value}')
        if not value.ratioEqual(self[index]):
            raise MeterException(f'cannot insert {value} into space of {self[index]}')
        newPartition = list(self._partition)
        newPartition[index] = value
        return self._rebuild(newPartition)

    def __str__(self):
        return '{' + self.partitionDisplay + '}'

    def _reprInternal(self):
        return str(self)

    @property
    def partitionDisplay(self):
        '''
        Property -- Display the partition as a str without the surrounding curly brackets.

        >>> a = meter.MeterSequence('4/4')
        >>> a.partitionDisplay
        '4/4'
        >>> a = meter.MeterSequence('2/4+6/8')
        >>> a.partitionDisplay
        '2/4+6/8'

        partitionDisplay is most useful for non-divided meter sequences. This is less helpful:

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a.partitionDisplay
        '1/4+1/4+1/4+1/4'
        '''
        msg = []
        for mt in self._partition:
            msg.append(str(mt))
        return '+'.join(msg)

    # -------------------------------------------------------------------------

    def _rebuild(self, partition: list) -> MeterSequence:
        '''
        Return a cached MeterSequence with the same numerator, denominator,
        parenthesis, and summedNumerator as ``self`` but a new partition.

        AI-assisted (Claude).
        '''
        return makeSequence(
            self._numerator, self._denominator, tuple(partition),
            parenthesis=self.parenthesis, summedNumerator=self.summedNumerator)

    def getPartitionOptions(self) -> tools.MeterOptions:
        '''
        Return either a cached or a new set of division/partition options.

        Calls `tools.divisionOptionsAlgo` and `tools.divisionOptionsPreset`
        (which will be empty except if the numerator is 5).

        Works on anything that has a .numerator and .denominator.

        >>> meter.MeterSequence('3/4').getPartitionOptions()
        (('1/4', '1/4', '1/4'),
         ('1/8', '1/8', '1/8', '1/8', '1/8', '1/8'),
         ('1/16', '1/16', '1/16', '1/16', '1/16', '1/16', '1/16',
          '1/16', '1/16', '1/16', '1/16', '1/16'),
         ('3/4',), ('6/8',), ('12/16',), ('24/32',), ('48/64',), ('96/128',))

        The additional 2 + 2 + 1 and 2 + 1 + 2 options for numerator 5 are at the end.

        >>> meter.MeterSequence('5/32').getPartitionOptions()
        (('2/32', '3/32'),
         ('3/32', '2/32'),
         ('1/32', '1/32', '1/32', '1/32', '1/32'),
         ('1/64', '1/64', '1/64', '1/64', '1/64',
          '1/64', '1/64', '1/64', '1/64', '1/64'),
         ('5/32',), ('10/64',), ('20/128',),
         ('2/32', '2/32', '1/32'), ('2/32', '1/32', '2/32'))
        '''
        # all-string python dictionaries are optimized; use string key
        n = int(self.numerator)
        d = int(self.denominator)
        opts = []
        opts.extend(list(tools.divisionOptionsAlgo(n, d)))
        opts.extend(list(tools.divisionOptionsPreset(n, d)))
        # store for access later
        return tuple(opts)

    # -------------------------------------------------------------------------

    def partitionByCount(self, countRequest: int, loadDefault: bool = True) -> MeterSequence:
        '''
        Return a new MeterSequence dividing this one into the requested number
        of parts.

        If it is not possible to divide it into the requested number, and
        loadDefault is `True`, then give the default partition.

        >>> a = meter.MeterSequence('4/4')
        >>> a
        <music21.meter.core.MeterSequence {4/4}>
        >>> a = a.partitionByCount(2)
        >>> a
        <music21.meter.core.MeterSequence {1/2+1/2}>
        >>> str(a)
        '{1/2+1/2}'
        >>> a = a.partitionByCount(4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        The partitions are not guaranteed to be the same length if the
        meter is irregular:

        >>> b = meter.MeterSequence('5/8')
        >>> b = b.partitionByCount(2)
        >>> b
         <music21.meter.core.MeterSequence {2/8+3/8}>

        This relies on a pre-defined exemption for partitioning 5 by 3:

        >>> b = b.partitionByCount(3)
        >>> str(b)
        '{2/8+2/8+1/8}'

        Here we use loadDefault=True to get the default partition in case
        there is no known way to do this:

        >>> a = meter.MeterSequence('5/8')
        >>> a = a.partitionByCount(11)
        >>> str(a)
        '{2/8+3/8}'

        If loadDefault is False then an error is raised:

        >>> a.partitionByCount(11, loadDefault=False)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by 11 (5/8)

        * Changed in v11: returns a new MeterSequence rather than mutating in place.
        '''
        opts = self.getPartitionOptions()
        optMatch = None
        # get the first encountered load string with the desired
        # number of beats
        for opt in opts:
            if len(opt) == countRequest:
                optMatch = opt
                break

        # if no matches this method provides a default
        if optMatch is None:
            if loadDefault and opts:
                optMatch = opts[0]
            else:
                raise MeterException(
                    f'Cannot set partition by {countRequest} ({self.numerator}/{self.denominator})'
                )

        targetWeight = self.weight
        partition = [_coerceTerminal(mStr) for mStr in optMatch]
        partition = _applyWeight(partition, self.numerator, self.denominator, targetWeight)
        return self._rebuild(partition)

    def partitionByList(
        self,
        numeratorList: Sequence[int] | Sequence[str]
    ) -> MeterSequence:
        '''
        Given a numerator list, return a new MeterSequence partitioned into a
        list of MeterTerminals.

        >>> a = meter.MeterSequence('4/4')
        >>> a = a.partitionByList([1, 1, 1, 1])
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        This divides it into two equal parts:

        >>> a = a.partitionByList([1, 1])
        >>> str(a)
        '{1/2+1/2}'

        And now into one big part:

        >>> a = a.partitionByList([1])
        >>> str(a)
        '{1/1}'

        Here we divide 4/4 very unconventionally:

        >>> a = a.partitionByList(['3/4', '1/8', '1/8'])
        >>> a
        <music21.meter.core.MeterSequence {3/4+1/8+1/8}>

        But the basics of the MeterSequence must be observed:

        >>> a.partitionByList(['3/4', '1/8', '5/8'])
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by ['3/4', '1/8', '5/8']

        * Changed in v11: returns a new MeterSequence rather than mutating in place.
        '''
        optMatch: Sequence[MeterNode] | tuple[str, ...] | None = None

        # assume a list of terminal definitions
        if isinstance(numeratorList[0], str):
            testPartition = [_coerceTerminal(t.cast(str, mtStr)) for mtStr in numeratorList]
            testNum, testDen = _ratioFromPartition(testPartition)
            testDur = MeterCore._durationFromNumeratorDenominator(
                testNum, testDen).quarterLength
            # if durations are equal, this can be used as a partition
            if self.duration.quarterLength == testDur:
                optMatch = testPartition
            else:
                raise MeterException(f'Cannot set partition by {numeratorList}')

        elif sum(t.cast('list[int]', numeratorList)) in [self.numerator * x for x in range(1, 9)]:
            for i in range(1, 9):
                if sum(t.cast('list[int]', numeratorList)) == self.numerator * i:
                    optMatchInner: list[str] = []
                    for n in numeratorList:
                        optMatchInner.append(f'{n}/{self.denominator * i}')
                    optMatch = tuple(optMatchInner)
                    break

        # last resort: search options
        else:
            opts = self.getPartitionOptions()
            for opt in opts:
                # get numerators as numbers
                nFound = [int(x.split('/')[0]) for x in opt]
                if nFound == numeratorList:
                    optMatch = opt
                    break

        if optMatch is None:
            raise MeterException(
                f'Cannot set partition by {numeratorList} ({self.numerator}/{self.denominator})'
            )

        # Since we have a numerator/denominator match, build the new sequence
        targetWeight = self.weight
        partition = [_coerceTerminal(mStr) for mStr in optMatch]
        partition = _applyWeight(partition, self.numerator, self.denominator, targetWeight)
        return self._rebuild(partition)

    def partitionByOtherMeterSequence(self, other: MeterSequence) -> MeterSequence:
        '''
        Return a new MeterSequence with the partition found in another
        MeterSequence.

        >>> a = meter.MeterSequence('4/4', 4)
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        >>> b = meter.MeterSequence('4/4', 2)
        >>> a = a.partitionByOtherMeterSequence(b)
        >>> len(a)
        2
        >>> str(a)
        '{1/2+1/2}'

        * Changed in v11: returns a new MeterSequence rather than mutating in place.
        '''
        if (self.numerator == other.numerator
                and self.denominator == other.denominator):
            targetWeight = self.weight
            # other's members are immutable, so they can be shared directly
            partition = list(other._partition)
            partition = _applyWeight(partition, self.numerator, self.denominator, targetWeight)
            return self._rebuild(partition)
        else:
            raise MeterException('Cannot set partition for unequal MeterSequences')

    def partition(
        self,
        value: int | Sequence[str] | Sequence[MeterTerminal] | Sequence[int] | MeterSequence,
        loadDefault=False
    ) -> MeterSequence:
        '''
        Return a new MeterSequence partitioned according to `value`.

        A simple way to partition based on argument time. Single integers
        are treated as beat counts; lists are treated as numerator lists;
        MeterSequence objects are partitioned by calling partitionByOtherMeterSequence().

        >>> a = meter.MeterSequence('5/4+3/8')
        >>> len(a)
        2
        >>> str(a)
        '{5/4+3/8}'

        >>> b = meter.MeterSequence('13/8')
        >>> len(b)
        1
        >>> str(b)
        '{13/8}'
        >>> b = b.partition(13)
        >>> len(b)
        13
        >>> str(b)
        '{1/8+1/8+1/8+...+1/8}'

        >>> a = a.partition(b)
        >>> len(a)
        13
        >>> str(a)
        '{1/8+1/8+1/8+...+1/8}'

        Demo of loadDefault: if impossible, then do it another way:

        >>> c = meter.MeterSequence('3/128')
        >>> c.partition(2)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by 2 (3/128)

        >>> c = meter.MeterSequence('3/128')
        >>> c = c.partition(2, loadDefault=True)
        >>> len(c)
        3
        >>> str(c)
        '{1/128+1/128+1/128}'

        * Changed in v9.3: if given a list it must either be all numbers, all strings,
          or all MeterTerminals, not a mix (which was undocumented and buggy)
        * Changed in v11: returns a new MeterSequence rather than mutating in place.
        '''
        if common.isListLike(value):
            return self.partitionByList(value)
        elif isinstance(value, MeterSequence):
            return self.partitionByOtherMeterSequence(value)
        elif isinstance(value, int):
            return self.partitionByCount(value, loadDefault=loadDefault)
        else:
            raise MeterException(f'cannot process partition argument {value}')

    def subdividePartitionsEqual(self, divisions: int|None = None) -> MeterSequence:
        '''
        Return a new MeterSequence with all partitions subdivided by
        equally-spaced divisions, given a divisions value.

        Divisions value may optionally be a MeterSequence,
        from which a top-level partitioning structure is derived.

        Example:  First we will do a normal partition (not subdivided partition)

        >>> ms = meter.MeterSequence('2/4')
        >>> ms
        <music21.meter.core.MeterSequence {2/4}>
        >>> len(ms)
        1
        >>> ms[0]
        <music21.meter.core.MeterTerminal 2/4>
        >>> len(ms[0])
        Traceback (most recent call last):
        TypeError: object of type 'MeterTerminal' has no len()

        Divide the Sequence into two parts, so now there are two
        MeterTerminals of 1/4 each:

        >>> ms = ms.partition(2)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+1/4}>
        >>> len(ms)
        2
        >>> ms[0]
        <music21.meter.core.MeterTerminal 1/4>
        >>> ms[1]
        <music21.meter.core.MeterTerminal 1/4>

        But what happens if we want to divide each of those into 1/8+1/8 are replace
        them by MeterSequences?  subdividePartitionsEqual is what is needed.

        >>> ms = ms.subdividePartitionsEqual(2)
        >>> ms
        <music21.meter.core.MeterSequence {{1/8+1/8}+{1/8+1/8}}>

        Length is still 2, but each of the components are now MeterSequences of their
        own:

        >>> len(ms)
        2
        >>> ms[0]
        <music21.meter.core.MeterSequence {1/8+1/8}>
        >>> ms[1]
        <music21.meter.core.MeterSequence {1/8+1/8}>

        To subdivide a nested component, replace it functionally:

        >>> ms = ms.setIndex(0, ms[0].subdividePartitionsEqual(2))
        >>> ms
        <music21.meter.core.MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{1/8+1/8}}>
        >>> ms = ms.setIndex(1, ms[1].subdividePartitionsEqual(2))
        >>> ms
        <music21.meter.core.MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}>

        If None is given as a parameter, then it will try to find something logical.

        >>> ms = meter.MeterSequence('2/4+3/4')
        >>> ms = ms.subdividePartitionsEqual(None)
        >>> ms
        <music21.meter.core.MeterSequence {{1/4+1/4}+{1/4+1/4+1/4}}>

        If any partition cannot be divided by the given count, a MeterException is raised:

        >>> ms = meter.MeterSequence('5/8+3/8')
        >>> len(ms)
        2
        >>> ms.subdividePartitionsEqual(5)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by 5 (3/8)

        * Changed in v11: returns a new MeterSequence rather than mutating in place.
        '''
        newPartition: list[MeterNode] = []
        for i in range(len(self)):
            el = self[i]
            if divisions is None:  # get dynamically
                partitionNumerator: int = el.numerator
                if partitionNumerator in (1, 2, 4, 8, 16, 32, 64):
                    divisionsLocal = 2
                elif partitionNumerator == 3:
                    divisionsLocal = 3
                elif partitionNumerator in (6, 9, 12, 15, 18, 21, 24, 27):
                    divisionsLocal = partitionNumerator // 3
                else:
                    # TODO: get from the smallest prime number
                    divisionsLocal = partitionNumerator
            else:
                divisionsLocal = divisions
            newPartition.append(el.subdivide(divisionsLocal))

        return self._rebuild(newPartition)

    def subdivideNestedHierarchy(self, depth, firstPartitionForm=None,
                                 normalizeDenominators=True) -> MeterSequence:
        '''
        Return a new MeterSequence with a nested structure down to a specified
        depth; the first division is set to one; the second division may be by
        2 or 3; remaining divisions are always by 2.

        `normalizeDenominators`, if True, will reduce all denominators to the same minimum level.

        >>> ms = meter.MeterSequence('4/4')
        >>> ms.subdivideNestedHierarchy(1)
        <music21.meter.core.MeterSequence {{1/2+1/2}}>
        >>> ms.subdivideNestedHierarchy(2)
        <music21.meter.core.MeterSequence {{{1/4+1/4}+{1/4+1/4}}}>
        >>> ms.subdivideNestedHierarchy(3)
        <music21.meter.core.MeterSequence {{{{1/8+1/8}+{1/8+1/8}}+{{1/8+1/8}+{1/8+1/8}}}}>

        I think you get the picture!

        The effects above are not cumulative -- each call starts from ``ms`` --
        so users can skip directly to whatever level of hierarchy they want.

        >>> ms2 = meter.MeterSequence('4/4')
        >>> ms2.subdivideNestedHierarchy(3)
        <music21.meter.core.MeterSequence {{{{1/8+1/8}+{1/8+1/8}}+{{1/8+1/8}+{1/8+1/8}}}}>

        * Changed in v11: returns a new MeterSequence rather than mutating in place.

        AI-assisted (Claude).
        '''
        # as a hierarchical representation, zeroth subdivision must be 1
        ms = self.partition(1)
        depthCount = 0

        # initial divisions are often based on numerator or are provided
        # by looking at the number of top-level beat partitions
        # thus, 6/8 will have 2, 18/4 should have 5
        if isinstance(firstPartitionForm, MeterSequence):
            ms = _buildSequence(firstPartitionForm.getLevel(0))
            depthCount += 1
        else:  # can be just a number
            if firstPartitionForm is None:
                firstPartitionForm = self.numerator
            # use a fixed mapping for first divider; may be a good algo solution
            if firstPartitionForm in [1, 2, 4, 8, 16, 32]:
                divFirst = 2
            elif firstPartitionForm in [3]:
                divFirst = 3
            # otherwise, set the first div to the number of beats; in 18/4
            # this should be 6
            else:  # set to numerator
                divFirst = firstPartitionForm

            # use partitions equal, divide by number
            ms = ms.subdividePartitionsEqual(divFirst)
            depthCount += 1

        # all other partitions are recursive; start first with list of paths
        post: list[tuple[int, ...]] = [(0,)]
        while depthCount < depth:
            # setting divisions to None will get either 2/3 for all components
            ms, post = _subdivideNestedByPaths(ms, post, None)
            depthCount += 1
            # need to detect cases of unequal denominators
            if not normalizeDenominators:
                continue
            while True:
                d = []
                for p in post:
                    den = _getAtPath(ms, p).denominator
                    if den not in d:
                        d.append(den)
                # if we have more than one denominator; we need to normalize
                if len(d) > 1:
                    postNew: list[tuple[int, ...]] = []
                    minD = min(d)
                    for p in post:
                        # if this is a lower denominator (1/4 not 1/8),
                        # process again
                        if _getAtPath(ms, p).denominator == minD:
                            ms, childPaths = _subdivideNestedByPaths(ms, [p], None)
                            postNew += childPaths
                        else:  # keep original if no problem
                            postNew.append(p)
                    post = postNew  # reassigning to original
                else:
                    break

        return ms

    # --------------------------------------------------------------------------
    @property
    def partitionStr(self):
        '''
        Return the number of top-level partitions in this MeterSequence as a string.

        >>> ms = meter.MeterSequence('2/4+2/4')
        >>> ms
        <music21.meter.core.MeterSequence {2/4+2/4}>
        >>> ms.partitionStr
        'Duple'

        >>> ms = meter.MeterSequence('6/4', 6)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4+1/4+1/4}>
        >>> ms.partitionStr
        'Sextuple'

        >>> ms = meter.MeterSequence('6/4', 2)
        >>> ms.partitionStr
        'Duple'

        >>> ms = meter.MeterSequence('6/4', 3)
        >>> ms.partitionStr
        'Triple'

        Anything larger than 8 is simply the number followed by '-uple'

        >>> ms = meter.MeterSequence('13/4', 13)
        >>> ms.partitionStr
        '13-uple'

        Single partition:

        >>> ms = meter.MeterSequence('3/4', 1)
        >>> ms.partitionStr
        'Single'
        '''
        count = len(self)
        countName = ('Empty',  # should not happen
                     'Single',
                     'Duple', 'Triple', 'Quadruple', 'Quintuple',
                     'Sextuple', 'Septuple', 'Octuple')

        if count < len(countName):
            return countName[count]
        else:
            return str(count) + '-uple'

    # --------------------------------------------------------------------------
    # properties
    # do not permit setting of numerator/denominator

    @property
    def numerator(self) -> int:
        '''
        Return the numerator of the MeterSequence (the rationalized total).

        >>> meter.MeterSequence('3/4+3/8').numerator
        9
        '''
        return self._numerator

    @property
    def denominator(self) -> int:
        '''
        Return the denominator of the MeterSequence (the lowest common multiple).

        >>> meter.MeterSequence('3/4+3/8').denominator
        8
        '''
        return self._denominator

    @property
    def weight(self) -> float:
        '''
        Return the weight for the MeterSequence: the sum of the weights of each
        object in this MeterSequence.

        By default, all the partitions of a MeterSequence's weights sum to 1.0

        >>> a = meter.MeterSequence('3/4')
        >>> a.weight
        1.0
        >>> a = a.partition(3)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> a.weight
        1.0
        >>> a[0].weight
        0.3333...

        When creating a new MeterSequence from MeterTerminals, the sequence has
        the weight of the sum of those creating it.

        >>> downbeat = meter.MeterTerminal('1/4', 0.5)
        >>> upbeat = meter.MeterTerminal('1/4', 0.25)
        >>> accentSequence = meter.MeterSequence([downbeat, upbeat])
        >>> accentSequence.weight
        0.75

        A MeterSequence's weight is not stored; it is recomputed from its parts
        on each call.
        '''
        summation = 0.0
        for obj in self._partition:
            summation += obj.weight  # may be a MeterTerminal or MeterSequence
        return summation

    def withWeight(self, targetWeight: float) -> MeterSequence:
        '''
        Return a new MeterSequence whose children are re-weighted so that they
        sum (proportionally) to ``targetWeight``.

        This is the immutable replacement for the pre-v11 ``ms.weight = x``
        setter: rather than re-weighting the children in place, request a new
        sequence.

        >>> ms = meter.MeterSequence('4/4', 4)
        >>> ms2 = ms.withWeight(1.0)
        >>> [mt.weight for mt in ms2]
        [0.25, 0.25, 0.25, 0.25]

        * New in v11: replaces the ``weight`` setter.

        AI-assisted (Claude).
        '''
        partition = _applyWeight(
            self._partition, self._numerator, self._denominator, targetWeight)
        return self._rebuild(partition)

    def _getFlatList(self):
        '''
        Return a flattened version of this
        MeterSequence as a list of MeterTerminals.

        This return a list and not a new MeterSequence b/c MeterSequence objects
        are generally immutable and thus it does not make sense
        to concatenate them.

        >>> a = meter.MeterSequence('3/4')
        >>> a = a.partition(3)
        >>> b = a._getFlatList()
        >>> b
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>]
        >>> len(b)
        3

        >>> a = a.setIndex(1, a[1].subdivide(4))
        >>> len(a)
        3
        >>> a
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+1/16+1/16}+1/4}>

        >>> b = a._getFlatList()
        >>> len(b)
        6
        >>> b
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/16>,
         <music21.meter.core.MeterTerminal 1/16>,
         <music21.meter.core.MeterTerminal 1/16>,
         <music21.meter.core.MeterTerminal 1/16>,
         <music21.meter.core.MeterTerminal 1/4>]

        >>> a = a.setIndex(1, a[1].setIndex(2, a[1][2].subdivide(4)))
        >>> a
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = a._getFlatList()
        >>> len(b)
        9
        '''
        # Is this the same as getLevelList(0)?
        mtList: list[MeterNode] = []
        for obj in self._partition:  # or for obj in self
            if not isinstance(obj, MeterSequence):
                mtList.append(obj)
            else:  # its a meter sequence
                mtList += obj._getFlatList()
        return mtList

    def flatten(self) -> MeterSequence:
        '''
        Return a new MeterSequence composed of the flattened representation.

        Here a sequence is already flattened:

        >>> ms = meter.MeterSequence('3/4', 3)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> b = ms.flatten()
        >>> b
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> len(b)
        3

        Now take a MeterSequence and subdivide the second beat into 4 parts:

        >>> ms = meter.MeterSequence('3/4', 3)
        >>> ms = ms.setIndex(1, ms[1].subdivide(4))
        >>> ms
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+1/16+1/16}+1/4}>
        >>> b = ms.flatten()
        >>> len(b)
        6
        >>> b
        <music21.meter.core.MeterSequence {1/4+1/16+1/16+1/16+1/16+1/4}>

        >>> ms = ms.setIndex(1, ms[1].setIndex(2, ms[1][2].subdivide(4)))
        >>> ms
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = ms.flatten()
        >>> len(b)
        9
        >>> b
        <music21.meter.core.MeterSequence {1/4+1/16+1/16+1/64+1/64+1/64+1/64+1/16+1/4}>
        '''
        return MeterSequence(self._getFlatList())

    @property
    def flatWeight(self):
        '''
        Return a list of flat weight values
        '''
        post = []
        for mt in self._getFlatList():
            post.append(mt.weight)
        return post

    @property
    def depth(self):
        '''
        Return how many unique levels deep this part is
        '''
        depth = 0  # start with 0, will count this level

        lastMatch = None
        while True:
            test = self.getLevelList(depth)
            if test != lastMatch:
                depth += 1
                lastMatch = test
            else:
                break
        return depth

    def isUniformPartition(self, *, depth=0):
        # noinspection PyShadowingNames
        '''
        Return True if the top-level partitions (if depth=0)
        or a lower-level section has equal durations

        >>> ms = meter.MeterSequence('3/8+2/8+3/4')
        >>> ms.isUniformPartition()
        False
        >>> ms = meter.MeterSequence('4/4')
        >>> ms.isUniformPartition()
        True
        >>> ms = ms.partition(4)
        >>> ms.isUniformPartition()
        True
        >>> ms = ms.setIndex(0, ms[0].subdivideByCount(2))
        >>> ms = ms.setIndex(1, ms[1].subdivideByCount(4))
        >>> ms.isUniformPartition()
        True
        >>> ms.isUniformPartition(depth=1)
        False

        >>> ms = meter.MeterSequence('2/4+2/4')
        >>> ms.isUniformPartition()
        True

        >>> ms = meter.MeterSequence('5/8', 5)
        >>> ms.isUniformPartition()
        True
        >>> ms = ms.partition(2)
        >>> ms.isUniformPartition()
        False

        * Changed in v7: depth is keyword only.
        '''
        n = []
        d = []
        for ms in self.getLevelList(depth):
            if ms.numerator not in n:
                n.append(ms.numerator)
            if ms.denominator not in d:
                d.append(ms.denominator)
            # as soon as we have more than on entry, we do not have uniform
            if len(n) > 1 or len(d) > 1:
                return False
        return True

    # --------------------------------------------------------------------------
    # alternative representations

    def getLevelList(self, levelCount: int, flat: bool = True) -> list[MeterNode]:
        '''
        Recursive utility function that gets everything at a certain level.

        If flat is True, it guarantees to return a list of MeterTerminals and not
        MeterSequences.  Otherwise, there may be Sequences in there.

        Example: a Sequence representing something in 4/4 divided as
        1 quarter, 2 eighth, 1 quarter, ((2-sixteenths) + 1 eighth).

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b = b.setIndex(1, b[1].subdivide(2))
        >>> b = b.setIndex(3, b[3].subdivide(2))
        >>> b = b.setIndex(3, b[3].setIndex(0, b[3][0].subdivide(2)))
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>

        Get the top level of this structure, flattening everything underneath:

        >>> b.getLevelList(0)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>]

        One level down:

        >>> b.getLevelList(1)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/8>,
         <music21.meter.core.MeterTerminal 1/8>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/8>,
         <music21.meter.core.MeterTerminal 1/8>]

        Without flattening, first two levels:

        >>> b.getLevelList(0, flat=False)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterSequence {1/8+1/8}>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterSequence {{1/16+1/16}+1/8}>]

        (Note that levelList 0, flat=False is essentially the same as iterating
        over a MeterSequence)

        >>> list(b)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterSequence {1/8+1/8}>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterSequence {{1/16+1/16}+1/8}>]

        >>> b.getLevelList(1, flat=False)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/8>,
         <music21.meter.core.MeterTerminal 1/8>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterSequence {1/16+1/16}>,
         <music21.meter.core.MeterTerminal 1/8>]

        Generally, these level lists will be converted back to MeterSequences:

        >>> meter.MeterSequence(b.getLevelList(0))
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> meter.MeterSequence(b.getLevelList(1))
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/8+1/8}>
        >>> meter.MeterSequence(b.getLevelList(2))
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        >>> meter.MeterSequence(b.getLevelList(3))
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>

        OMIT_FROM_DOCS

        A fresh list is returned each call, so a caller may mutate it safely:

        >>> b = meter.MeterSequence('3/4', 3)
        >>> o = b.getLevelList(0)
        >>> o.append(meter.core.MeterTerminal('1/8'))
        >>> len(o)
        4
        >>> b.getLevelList(0)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>]
        >>> b.getLevelList(0)[0] is o[0]
        True
        '''
        mtList: list[MeterNode] = []
        for partition_i in self._partition:
            if not isinstance(partition_i, MeterSequence):
                mtList.append(partition_i)  # a MeterTerminal
            else:  # it is a MeterSequence
                if levelCount > 0:  # retain this sequence but get lower level
                    # reduce level by 1 when recursing; do not
                    # change levelCount here
                    mtList += partition_i.getLevelList(levelCount - 1, flat)
                else:  # level count is at zero
                    if flat:  # make sequence into a terminal
                        # weight matches that of the sequence it flattens
                        mtList.append(getMeterTerminal(
                            partition_i.numerator,
                            partition_i.denominator,
                            weight=partition_i.weight,
                        ))
                    else:  # it is not a terminal, it is a meter sequence
                        mtList.append(partition_i)

        return mtList

    def getLevel(self, level=0, flat=True):
        '''
        Return a complete MeterSequence with the same numerator/denominator
        relationship but that represents any partitions found at the requested
        level. A sort of flatness with variable depth.

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b = b.setIndex(1, b[1].subdivide(2))
        >>> b = b.setIndex(3, b[3].subdivide(2))
        >>> b = b.setIndex(3, b[3].setIndex(0, b[3][0].subdivide(2)))
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevel(0)
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> b.getLevel(1)
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/8+1/8}>
        >>> b.getLevel(2)
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        '''
        return MeterSequence(self.getLevelList(level, flat))

    def getLevelSpan(self, level=0):
        '''
        For a given level, return the time span of each terminal or sequence

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b = b.setIndex(1, b[1].subdivide(2))
        >>> b = b.setIndex(3, b[3].subdivide(2))
        >>> b = b.setIndex(3, b[3].setIndex(0, b[3][0].subdivide(2)))
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelSpan(0)
        [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0)]
        >>> b.getLevelSpan(1)
        [(0.0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 3.5), (3.5, 4.0)]
        >>> b.getLevelSpan(2)
        [(0.0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 3.25), (3.25, 3.5), (3.5, 4.0)]
        '''
        ms = self.getLevelList(level, flat=True)
        mapping = []
        pos = 0.0

        for i in range(len(ms)):
            start = pos
            end = opFrac(pos + ms[i].duration.quarterLength)
            mapping.append((start, end))
            pos = end
        return mapping

    def getLevelWeight(self, level=0):
        '''
        The weightList is an array of weights found in the components.
        The MeterSequence has a ._weight attribute, but it is not used here

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a.getLevelWeight()
        [0.25, 0.25, 0.25, 0.25]

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]

        >>> b = b.setIndex(1, b[1].subdivide(2))
        >>> b = b.setIndex(3, b[3].subdivide(2))
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]

        >>> b = b.setIndex(3, b[3].setIndex(0, b[3][0].subdivide(2)))
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]
        >>> b.getLevelWeight(1)
        [0.25, 0.125, 0.125, 0.25, 0.125, 0.125]
        >>> b.getLevelWeight(2)
        [0.25, 0.125, 0.125, 0.25, 0.0625, 0.0625, 0.125]
        '''
        post = []
        for mt in self.getLevelList(level):
            post.append(mt.weight)
        return post

    def setLevelWeight(self, weightList, level=0) -> MeterSequence:
        '''
        The `weightList` is an array of weights to be applied to a
        single level of the MeterSequence.  Returns a new MeterSequence.

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a = a.setLevelWeight([1.0, 2.0, 3.0, 4.0])
        >>> a.getLevelWeight()
        [1.0, 2.0, 3.0, 4.0]

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b = b.setLevelWeight([2.0, 3.0])
        >>> b.getLevelWeight(0)
        [2.0, 3.0, 2.0, 3.0]

        >>> b = b.setIndex(1, b[1].subdivide(2))
        >>> b = b.setIndex(3, b[3].subdivide(2))
        >>> b.getLevelWeight(0)
        [2.0, 3.0, 2.0, 3.0]

        >>> b = b.setIndex(3, b[3].setIndex(0, b[3][0].subdivide(2)))
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelWeight(0)
        [2.0, 3.0, 2.0, 3.0]
        >>> b.getLevelWeight(1)
        [2.0, 1.5, 1.5, 2.0, 1.5, 1.5]
        >>> b.getLevelWeight(2)
        [2.0, 1.5, 1.5, 2.0, 0.75, 0.75, 1.5]

        * Changed in v11: returns a new MeterSequence rather than mutating in place.
        '''
        new, unused_idx = self._withLevelWeights(weightList, level, 0)
        return new

    def _withLevelWeights(self, weightList, level, startIndex=0) -> tuple[MeterSequence, int]:
        '''
        Recursively re-weight the leaf terminals reached at `level`, mirroring
        the flattening order of :meth:`getLevelList` (flat=True) so that the same
        terminals are affected and the same running index into `weightList` is
        used.  Returns the new MeterSequence and the next running index.

        AI-assisted (Claude).
        '''
        idx = startIndex
        newPartition = list(self._partition)
        for i, partition_i in enumerate(self._partition):
            if not isinstance(partition_i, MeterSequence):
                newWeight = weightList[idx % len(weightList)]
                newPartition[i] = getMeterTerminal(
                    partition_i.numerator, partition_i.denominator, weight=newWeight)
                idx += 1
            elif level > 0:
                child, idx = partition_i._withLevelWeights(weightList, level - 1, idx)
                newPartition[i] = child
            else:
                # getLevelList(flat=True) flattens this sequence to a single
                # synthetic terminal that has no persistent home; only the index
                # advances (matching the historical behavior).
                idx += 1
        return self._rebuild(newPartition), idx

    # --------------------------------------------------------------------------
    # given a quarter note position, return the active index

    def offsetToIndex(self, qLenPos, includeCoincidentBoundaries=False) -> int:
        '''
        Given an offset in quarterLengths (0.0 through self.duration.quarterLength), return
        the index of the active MeterTerminal or MeterSequence

        >>> a = meter.MeterSequence('4/4')
        >>> a.offsetToIndex(0.5)
        0
        >>> a.offsetToIndex(3.5)
        0
        >>> a = a.partition(4)
        >>> a.offsetToIndex(0.5)
        0
        >>> a.offsetToIndex(3.5)
        3

        >>> a = a.partition([1, 2, 1])
        >>> len(a)
        3
        >>> a.offsetToIndex(2.9)
        1
        >>> a[a.offsetToIndex(2.9)]
        <music21.meter.core.MeterTerminal 2/4>

        >>> a = meter.MeterSequence('4/4')
        >>> a.offsetToIndex(5.0)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: cannot access from qLenPos 5.0
            where total duration is 4.0

        Negative numbers also raise an exception:

        >>> a.offsetToIndex(-0.5)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: cannot access from qLenPos -0.5
            where total duration is 4.0
        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException(
                f'cannot access from qLenPos {qLenPos} '
                f'where total duration is {self.duration.quarterLength}'
            )

        qPos = 0
        match = -1  # no match -- will not happen.
        for i in range(len(self)):
            start = qPos
            end = opFrac(qPos + self[i].duration.quarterLength)
            # if adjoining ends are permitted, first match is found
            if includeCoincidentBoundaries:
                if start <= qLenPos <= end:
                    match = i
                    break
            else:
                # note that this is <=, meaning that the first boundary
                # is coincident.
                if start <= qLenPos < end:
                    match = i
                    break
            qPos = opFrac(qPos + self[i].duration.quarterLength)
        return match

    def offsetToAddress(self, qLenPos, includeCoincidentBoundaries=False):
        '''
        Give a list of values that show all indices necessary to access
        the exact terminal at a given qLenPos.

        The len of the returned list also provides the depth at the specified qLen.

        >>> a = meter.MeterSequence('3/4', 3)
        >>> a = a.setIndex(1, a[1].subdivide(4))
        >>> a
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+1/16+1/16}+1/4}>
        >>> len(a)
        3
        >>> a.offsetToAddress(0.5)
        [0]
        >>> a[0]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a.offsetToAddress(1.0)
        [1, 0]
        >>> a.offsetToAddress(1.5)
        [1, 2]
        >>> a[1][2]
        <music21.meter.core.MeterTerminal 1/16>
        >>> a.offsetToAddress(1.99)
        [1, 3]
        >>> a.offsetToAddress(2.5)
        [2]
        '''
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException(f'cannot access from qLenPos {qLenPos}')

        start = 0
        qPos = 0
        match = []
        i = None
        for i in range(len(self)):
            start = qPos
            end = opFrac(qPos + self[i].duration.quarterLength)
            # if adjoining ends are permitted, first match is found
            if includeCoincidentBoundaries:
                if start <= qLenPos <= end:
                    match.append(i)
                    break
            else:
                if start <= qLenPos < end:
                    match.append(i)
                    break
            qPos = opFrac(qPos + self[i].duration.quarterLength)

        if i is not None and isinstance(self[i], MeterSequence):  # recurse
            # qLenPosition needs to be relative to this subdivision
            # start is our current position that this subdivision
            # starts at
            qLenPosShift = opFrac(qLenPos - start)
            match += self[i].offsetToAddress(qLenPosShift,
                                             includeCoincidentBoundaries)

        return match

    def offsetToSpan(self, qLenPos, permitMeterModulus=False):
        '''
        Given a qLenPos, return the span of the active region.
        Only applies to the top most level of partitions

        If `permitMeterModulus` is True, quarter length positions
        greater than the duration of the Meter will be accepted
        as the modulus of the total meter duration.

        >>> a = meter.MeterSequence('3/4', 3)
        >>> a.offsetToSpan(0.5)
        (0, 1.0)
        >>> a.offsetToSpan(1.5)
        (1.0, 2.0)

        This is the same as 1.5:

        >>> a.offsetToSpan(4.5, permitMeterModulus=True)
        (1.0, 2.0)

        Make sure it works for tuplets even with so-so rounding:

        >>> a.offsetToSpan(4.33333336, permitMeterModulus=True)
        (1.0, 2.0)

        '''
        qLenPos = opFrac(qLenPos)
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            if not permitMeterModulus:
                # environLocal.printDebug(['exceeding range:', self,
                #   'self.duration', self.duration])
                raise MeterException(
                    f'cannot access qLenPos {qLenPos} when total duration is '
                    f'{self.duration.quarterLength} and ts is {self}'
                )

            # environLocal.printDebug(['offsetToSpan', 'got qLenPos old', qLenPos])
            qLenPos = qLenPos % self.duration.quarterLength
            # environLocal.printDebug(['offsetToSpan', 'got qLenPos old', qLenPos])

        iMatch = self.offsetToIndex(qLenPos)
        pos = 0
        start = None
        end = None
        for i in range(len(self)):
            # print(i, iMatch, self[i])
            if i == iMatch:
                start = pos
                end = opFrac(pos + self[i].duration.quarterLength)
            else:
                pos = opFrac(pos + self[i].duration.quarterLength)
        # environLocal.printDebug(['start, end', start, end])
        return start, end

    def offsetToWeight(self, qLenPos):
        '''
        Given a lenPos, return the weight of the active region.
        Only applies to the top-most level of partitions

        >>> a = meter.MeterSequence('3/4', 3)
        >>> a.offsetToWeight(0.0)
        Fraction(1, 3)
        >>> a.offsetToWeight(1.5)
        Fraction(1, 3)

        '''
        # Not sure what this does!
        qLenPos = opFrac(qLenPos)
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException(
                f'cannot access qLenPos {qLenPos} when total duration is '
                f'{self.duration.quarterLength} and ts is {self}'
            )
        iMatch = self.offsetToIndex(qLenPos)
        return opFrac(self[iMatch].weight)

    def offsetToDepth(self, qLenPos: OffsetQLIn, align: str = 'quantize', index: int|None = None):
        '''
        Given a qLenPos, return the maximum available depth at this position.  Align can be
        start, quantize, or end.

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b = b.setIndex(1, b[1].subdivide(2))
        >>> b = b.setIndex(3, b[3].subdivide(2))
        >>> b = b.setIndex(3, b[3].setIndex(0, b[3][0].subdivide(2)))
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.offsetToDepth(0)
        3
        >>> b.offsetToDepth(0.25)  # quantizing active by default
        3
        >>> b.offsetToDepth(1)
        3
        >>> b.offsetToDepth(1.5)
        2

        >>> b.offsetToDepth(-1)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: cannot access from qLenPos -1.0

        * Changed in v7: `index` can be provided, if known, for a long
          `MeterSequence` to improve performance.
        '''
        # TODO: Change the aligns to be StrEnums.
        qLenPos = opFrac(qLenPos)
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException(f'cannot access from qLenPos {qLenPos}')

        srcMatch = ''

        # need to quantize by lowest level
        mapMin = self.getLevelSpan(self.depth - 1)
        msMin = self.getLevel(self.depth - 1)
        if index is None:
            index = msMin.offsetToIndex(qLenPos)
        qStart, unused_qEnd = mapMin[index]
        if align == 'quantize':
            posMatch = opFrac(qStart)
        else:
            posMatch = qLenPos

        score = 0
        for level in range(self.depth):
            mapping = self.getLevelSpan(level)  # get mapping for each level
            for start, end in mapping:
                if align in ('start', 'quantize'):
                    srcMatch = start
                elif align == 'end':
                    srcMatch = end
                if srcMatch == posMatch:
                    score += 1

        return score


# -----------------------------------------------------------------------------
# module-level building helpers for the immutable MeterSequence

_meterSequenceCache: dict[
    tuple[int, int, tuple, bool, bool], MeterSequence
] = {}


def makeSequence(
    numerator: int,
    denominator: int,
    partition: tuple,
    *,
    parenthesis: bool = False,
    summedNumerator: bool = False,
) -> MeterSequence:
    '''
    Return a shared, cached, immutable MeterSequence for these values,
    building it directly (bypassing __init__) when it is not already cached.

    AI-assisted (Claude).
    '''
    key = (numerator, denominator, partition, parenthesis, summedNumerator)
    cached = _meterSequenceCache.get(key)
    if cached is not None:
        return cached
    ms = MeterSequence.__new__(MeterSequence)
    object.__setattr__(ms, '_numerator', numerator)
    object.__setattr__(ms, '_denominator', denominator)
    object.__setattr__(ms, '_partition', partition)
    object.__setattr__(ms, 'parenthesis', parenthesis)
    object.__setattr__(ms, 'summedNumerator', summedNumerator)
    _meterSequenceCache[key] = ms
    return ms


def getMeterSequence(
    value: str | MeterTerminal | Sequence[MeterTerminal] | Sequence[str] | None = None,
    partitionRequest: t.Any | None = None,
) -> MeterSequence:
    '''
    Return a shared, cached, immutable :class:`MeterSequence` built from the
    same inputs as the :class:`MeterSequence` constructor.

    Because MeterSequences are immutable, identical inputs all share one
    object -- so, e.g., every default ``4/4`` TimeSignature reuses the same
    beam/beat/accent/display sequences.

    >>> ms = meter.core.getMeterSequence('4/4', 4)
    >>> ms
    <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
    >>> meter.core.getMeterSequence('4/4', 4) is ms
    True

    AI-assisted (Claude).
    '''
    built = MeterSequence(value, partitionRequest)
    return makeSequence(
        built._numerator, built._denominator, built._partition,
        parenthesis=built.parenthesis, summedNumerator=built.summedNumerator)


def _coerceTerminal(value: MeterTerminal | MeterSequence | str) -> MeterNode:
    '''
    Return a MeterTerminal/MeterSequence for the given value: if it is already a
    MeterCore, return it as-is (they are immutable and shareable); if it is a
    string, return the cached terminal for that slash notation.

    AI-assisted (Claude).
    '''
    # NOTE: this is a performance critical helper
    if isinstance(value, MeterCore):  # MeterTerminal or MeterSequence
        return value
    # assume it is a string; share the cached immutable terminal
    values = tools.slashToTuple(value)
    return getMeterTerminal(values.numerator, values.denominator)


def _ratioFromPartition(partition) -> tuple[int, int]:
    '''
    Return the (numerator, denominator) sum (not reduced) for a partition of
    MeterTerminals/MeterSequences.

    AI-assisted (Claude).
    '''
    return tools.fractionSum(tuple((mt.numerator, mt.denominator) for mt in partition))


def _applyWeight(partition, numerator: int, denominator: int, targetWeight: float) -> list:
    '''
    Return a new partition list whose members are re-weighted so that they
    sum (proportionally by ratio) to ``targetWeight``.  Terminals are replaced
    by cached re-weighted ones; nested sequences are re-weighted recursively.

    AI-assisted (Claude).
    '''
    totalRatio = numerator / denominator
    out: list[MeterNode] = []
    for mt in partition:
        partRatio = mt.numerator / mt.denominator
        newWeight = targetWeight * (partRatio / totalRatio)
        if isinstance(mt, MeterSequence):
            out.append(mt.withWeight(newWeight))
        else:
            out.append(getMeterTerminal(mt.numerator, mt.denominator, weight=newWeight))
    return out


def _loadData(
    value: str | MeterTerminal | Sequence[MeterTerminal] | Sequence[str] | None = None,
    *,
    autoWeight: bool = False,
    targetWeight: float | None = None,
) -> tuple[int, int, list, bool]:
    '''
    Build the raw data for a MeterSequence from a value: return
    ``(numerator, denominator, partitionList, summedNumerator)``.

    `autoWeight`/`targetWeight` mirror the old ``MeterSequence.load``: when
    ``targetWeight`` is provided the members are re-weighted to sum to it.

    AI-assisted (Claude).
    '''
    # NOTE: this is a performance critical helper
    if not autoWeight:
        targetWeight = None

    if value is None:
        return 1, 0, [], False

    summedNumerator = False
    partition: list[MeterNode] = []

    if isinstance(value, str):
        ratioList, summedNumerator = tools.slashMixedToFraction(value)
        for n, d in ratioList:
            partition.append(getMeterTerminal(n, d))
        numerator, denominator = _ratioFromPartition(partition)
        if targetWeight is not None:
            partition = _applyWeight(partition, numerator, denominator, targetWeight)

    elif isinstance(value, MeterCore):  # a MeterTerminal or MeterSequence
        if targetWeight is not None:
            if isinstance(value, MeterSequence):
                value = value.withWeight(targetWeight)
            else:
                # a terminal is immutable: swap in a re-weighted cached one
                value = getMeterTerminal(value.numerator, value.denominator,
                                         weight=targetWeight)
        partition.append(value)
        numerator, denominator = _ratioFromPartition(partition)

    elif common.isIterable(value):  # a list of Terminals or Sequences
        for obj in value:
            partition.append(_coerceTerminal(obj))
        numerator, denominator = _ratioFromPartition(partition)
        if targetWeight is not None:
            partition = _applyWeight(partition, numerator, denominator, targetWeight)
    else:
        raise MeterException(f'cannot create a MeterSequence with a {value!r}')

    return numerator, denominator, partition, summedNumerator


def _buildSequence(
    value=None,
    partitionRequest=None,
    *,
    autoWeight: bool = False,
    targetWeight: float | None = None,
) -> MeterSequence:
    '''
    Build a cached, immutable MeterSequence from a value (and optional
    partitionRequest), applying weights as the old ``load`` did.

    AI-assisted (Claude).
    '''
    numerator, denominator, partition, summedNumerator = _loadData(
        value, autoWeight=autoWeight, targetWeight=targetWeight)
    ms = makeSequence(numerator, denominator, tuple(partition),
                       summedNumerator=summedNumerator)
    if partitionRequest is not None:
        ms = ms.partition(partitionRequest)
    return ms


def _getAtPath(root: MeterSequence, path: tuple[int, ...]) -> MeterNode:
    '''
    Return the node reached by following `path` (a tuple of indices) from `root`.

    AI-assisted (Claude).
    '''
    node: MeterNode = root
    for i in path:
        node = t.cast('MeterSequence', node)[i]
    return node


def _replaceAtPath(root: MeterSequence, path: tuple[int, ...], newNode) -> MeterSequence:
    '''
    Return a new root MeterSequence with the node at `path` replaced by
    `newNode`, rebuilding each ancestor functionally.

    AI-assisted (Claude).
    '''
    idx = path[0]
    if len(path) == 1:
        return root.setIndex(idx, newNode)
    child = t.cast('MeterSequence', root[idx])
    newChild = _replaceAtPath(child, path[1:], newNode)
    return root.setIndex(idx, newChild)


def _subdivideNestedByPaths(
    root: MeterSequence,
    paths: list[tuple[int, ...]],
    divisions,
) -> tuple[MeterSequence, list[tuple[int, ...]]]:
    '''
    Subdivide (equally) each node reached by a path in `paths`, rebuilding the
    root functionally, and return the new root plus the list of paths to the
    newly created child nodes.

    AI-assisted (Claude).
    '''
    newPaths: list[tuple[int, ...]] = []
    for p in paths:
        node = t.cast('MeterSequence', _getAtPath(root, p))
        newNode = node.subdividePartitionsEqual(divisions)
        root = _replaceAtPath(root, p, newNode)
        for j in range(len(newNode)):
            newPaths.append(p + (j,))
    return root, newPaths


if __name__ == '__main__':
    import music21
    music21.mainTest()
