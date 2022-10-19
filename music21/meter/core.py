# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         meter.core.py
# Purpose:      Component objects for meters
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009-2022 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
This module defines two component objects for defining nested metrical structures:
:class:`~music21.meter.core.MeterTerminal` and :class:`~music21.meter.core.MeterSequence`.

This is a **core** module, meaning its implementation may change at any time.
'''
from __future__ import annotations

from collections.abc import Iterable
import copy
from functools import lru_cache
import typing as t
from typing import TYPE_CHECKING  # Pylint bug

from music21 import prebase
from music21.common.numberTools import opFrac
from music21.common.objects import SlottedObjectMixin
from music21 import common
from music21 import duration
from music21 import environment
from music21.exceptions21 import MeterException
from music21.meter import tools


if t.TYPE_CHECKING:
    _T = t.TypeVar('_T')


environLocal = environment.Environment('meter.core')


class MeterCoreMixin:
    def subdivideByCount(self, countRequest=None):
        '''
        returns a MeterSequence made up of taking this MeterTerminal and
        subdividing it into the given number of parts.  Each of those parts
        is a MeterTerminal

        >>> a = meter.MeterTerminal(3, 4)
        >>> b = a.subdivideByCount(3)
        >>> b
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> len(b)
        3
        >>> b[0]
        <music21.meter.core.MeterTerminal 1/4>

        What happens if we do this?

        >>> a = meter.MeterTerminal(5, 8)
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
        for that, see the :meth:`~music21.meter.MeterSequence.load` method
        of :class:`~music21.meter.MeterSequence`.
        '''
        if TYPE_CHECKING:
            assert isinstance(self, (MeterTerminal, MeterSequence))
        # elevate to meter sequence
        ms = MeterSequence()
        # cannot set the weight of this MeterSequence w/o having offsets
        # pass this MeterTerminal as an argument
        # when subdividing, use autoWeight
        ms.load(self, countRequest, autoWeight=True, targetWeight=self.weight)
        return ms

    def subdivideByList(self, numeratorList):
        '''
        Return a MeterSequence dividing this
        MeterTerminal according to the numeratorList

        >>> a = meter.MeterTerminal(3, 4)
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
        if TYPE_CHECKING:
            assert isinstance(self, (MeterTerminal, MeterSequence))
        # elevate to meter sequence
        ms = MeterSequence()
        ms.load(self)  # do not need to autoWeight here
        ms.partitionByList(numeratorList)  # this will split weight
        return ms

    def subdivideByOther(self, other: MeterSequence):
        '''
        Return a MeterSequence based on another MeterSequence

        >>> a = meter.MeterSequence('1/4+1/4+1/4')
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4}>
        >>> b = meter.MeterSequence('3/8+3/8')
        >>> a.subdivideByOther(b)
        <music21.meter.core.MeterSequence {3/8+3/8}>

        >>> terminal = meter.MeterTerminal(1, 4)
        >>> divider = meter.MeterSequence('1/8+1/8')
        >>> terminal.subdivideByOther(divider)
        <music21.meter.core.MeterSequence {1/8+1/8}>
        '''
        if TYPE_CHECKING:
            assert isinstance(self, (MeterTerminal, MeterSequence))

        if other.duration.quarterLength != self.duration.quarterLength:
            raise MeterException(f'cannot subdivide by other: {other}')

        # elevate to meter sequence
        ms = MeterSequence()
        ms.load(other)  # do not need to autoWeight here
        # ms.partitionByOtherMeterSequence(other)  # this will split weight
        return ms

    def subdivide(self, value):
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

    def ratioEqual(self, other):
        '''
        Compare the numerator and denominator of another object.
        Note that these have to be exact matches; 3/4 is not the same as 6/8

        >>> a = meter.MeterTerminal(3, 4)
        >>> b = meter.MeterTerminal(6, 4)
        >>> c = meter.MeterTerminal(2, 4)
        >>> d = meter.MeterTerminal(3, 4)
        >>> a.ratioEqual(b)
        False
        >>> a.ratioEqual(c)
        False
        >>> a.ratioEqual(d)
        True
        '''
        if TYPE_CHECKING:
            assert isinstance(self, (MeterTerminal, MeterSequence))
        try:
            if (other.numerator == self.numerator
                    and other.denominator == self.denominator):
                return True
            else:
                return False
        except AttributeError:
            return False

    @staticmethod
    @lru_cache(1024)
    def _durationFromNumeratorDenominator(
        numerator: int,
        denominator: int
    ) -> duration.FrozenDuration:
        '''
        If ratio has been changed internally, call this to update duration
        '''
        # NOTE: this is a performance critical method and should only be
        # called when necessary
        try:
            return duration.FrozenDuration(quarterLength=(
                (4.0 * numerator) / denominator
            ))
        except duration.DurationException:
            environLocal.printDebug(
                ['DurationException encountered',
                 'numerator/denominator',
                 numerator,
                 denominator
                 ]
            )

    @property
    def duration(self):
        '''
        duration gets a duration value that
        is equal in length of the terminal.

        >>> a = meter.MeterTerminal(numerator=3, denominator=8)
        >>> d = a.duration
        >>> d.type
        'quarter'
        >>> d.dots
        1
        >>> d.quarterLength
        1.5
        '''
        return self._durationFromNumeratorDenominator(self.numerator, self.denominator)


class MeterTerminal(prebase.ProtoM21Object, MeterCoreMixin, common.FrozenObject):
    '''
    A MeterTerminal is a nestable primitive of rhythmic division.

    It is an immutable object, so specify all parameters at creation.

    >>> mt = meter.MeterTerminal(2, 4)
    >>> mt.numerator
    2
    >>> mt.denominator
    4

    Meter terminals have a default weight of 1:

    >>> mt.weight
    1

    And they always have a depth of 1

    >>> mt.depth
    1

    Meter terminals can calulate their durations.

    >>> mt.duration.quarterLength
    2.0

    >>> threeEight = meter.MeterTerminal(3, 8)
    >>> threeEight.duration.quarterLength
    1.5
    >>> fiveTwo = meter.MeterTerminal(5, 2)
    >>> fiveTwo.duration.quarterLength
    10.0

    Weights can be specified from the start.

    >>> three16 = meter.MeterTerminal(3, 16, weight=0.5)
    >>> three16.numerator
    3
    >>> three16.weight
    0.5
    >>> three16.duration.quarterLength == 0.75
    True

    * Changed in v9:
      - MeterTerminals are frozen (immutable) objects that need
      to have all their characteristics from start.
      - Nearly all attributes are keyword only
      - Remove overriddenDuration.
    '''

    # CLASS VARIABLES #

    __slots__ = (
        'denominator',
        'numerator',
        'weight',
    )

    _DOC_ATTR = {
        'weight': '''
            Return the weight of a MeterTerminal

            >>> a = meter.MeterTerminal(2, 4, weight=0.5)
            >>> a.weight
            0.5
            ''',
    }

    # INITIALIZER #
    def __init__(self,
                 numerator: int = 0,
                 denominator: int = 1,
                 *,
                 weight: float = 1,
                 ):
        self.numerator = numerator
        self.denominator = denominator
        self.weight = weight

    # SPECIAL METHODS #

    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return (
            self.numerator == other.numerator
            and self.denominator == other.denominator
            and self.weight == other.weight
        )

    def __hash__(self):
        return hash((self.numerator, self.denominator, self.weight))

    def __deepcopy__(self: _T, memo=None) -> _T:
        '''
        Immutable objects return themselves
        '''
        return self

    def _reprInternal(self):
        return str(self)

    def __str__(self):
        return str(int(self.numerator)) + '/' + str(int(self.denominator))

    @property
    def depth(self):
        '''
        Return how many levels deep this part is -- the depth of a terminal is always 1
        '''
        return 1


_meterTerminalCache: dict[tuple[int, int, float | int], MeterTerminal] = {}

def getMeterTerminal(
    numerator: int,
    denominator: int,
    weight: float | int = 1.0,
) -> MeterTerminal:
    '''
    Returns a MeterTerminal from a cache if necessary
    '''
    key = (numerator, denominator, weight)
    if key in _meterTerminalCache:
        return _meterTerminalCache[key]
    else:
        mt = MeterTerminal(numerator=numerator,
                           denominator=denominator,
                           weight=weight)
        _meterTerminalCache[key] = mt
        return mt


# -----------------------------------------------------------------------------
class MeterSequence(MeterCoreMixin, prebase.ProtoM21Object):
    '''
    A meter sequence is a list of MeterTerminals, or other MeterSequences

    * Changed in v9:
      - remove unused overriddenDuration.
      - `summedNumerator` renamed to `isSummedNumerator`.
    '''

    # CLASS VARIABLES #

    __slots__ = (
        'numerator',
        'denominator',
        '_levelListCache',
        '_partition',
        'parenthesis',
        'isSummedNumerator',
    )

    # INITIALIZER #

    def __init__(self,
                 value=None,
                 partitionRequest=None,
                 *,
                 numerator: int | None = None,
                 denominator: int | None = None,
                 ):
        self._levelListCache = {}
        self.numerator: int | None = numerator
        self.denominator: int | None = denominator
        self._partition = []  # a list of MeterTerminals or MeterSequences

        # this attribute is only used in MeterTerminals, and note
        # in MeterSequences; a MeterSequence's weight is based solely
        # on the sum of its component parts.
        # del self._weight -- no -- screws up pickling -- cannot del a slotted object

        # Bool stores whether this meter was provided as a summed numerator
        self.isSummedNumerator = False

        # An optional parameter used only in meter display sequences.
        # Needed in cases where a meter component is parenthetical
        self.parenthesis = False

        if value is not None:
            self.load(value, partitionRequest)

    # SPECIAL METHODS #

    def __deepcopy__(self: _T, memo=None) -> _T:
        '''
        Helper method to copy.py's deepcopy function. Call it from there.

        Defining a custom __deepcopy__ here is a performance boost,
        particularly in not copying _duration and other benefits.

        Notably, self._levelListCache is not copied,
        which may not be needed in the copy and may be large.

        >>> from copy import deepcopy
        >>> ms1 = meter.MeterSequence('4/4+3/8')
        >>> ms2 = deepcopy(ms1)
        >>> ms2
        <music21.meter.core.MeterSequence {4/4+3/8}>
        '''
        # call class to get a new, empty instance
        new = self.__class__()
        # for name in dir(self):
        new.numerator = self.numerator
        new.denominator = self.denominator
        # noinspection PyArgumentList
        new._partition = copy.deepcopy(self._partition, memo)
        new.isSummedNumerator = self.isSummedNumerator
        new.parenthesis = self.parenthesis

        return new

    def __getitem__(self, key):
        '''
        Get a MeterTerminal or MeterSequence from partitions

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a[3].numerator
        1
        >>> a[99]
        Traceback (most recent call last):
        IndexError: MeterSequence does not have level 99.
        '''
        try:
            return self._partition[key]
        except IndexError as ie:
            raise IndexError(f'MeterSequence does not have level {key}.') from ie

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

    def __setitem__(self, key, value):
        '''
        Insert items at index positions.

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> a[0]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a[0] = a[0].subdivide(2)
        >>> a[0]
        <music21.meter.core.MeterSequence {1/8+1/8}>
        >>> a
        <music21.meter.core.MeterSequence {{1/8+1/8}+1/4+1/4+1/4}>
        >>> a[0][0] = a[0][0].subdivide(2)
        >>> a
        <music21.meter.core.MeterSequence {{{1/16+1/16}+1/8}+1/4+1/4+1/4}>
        >>> a[3]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a[3] = a[0][0]
        Traceback (most recent call last):
        music21.exceptions21.MeterException: cannot insert {1/16+1/16} into space of 1/4
        '''
        # comparison of numerator and denominator
        if not isinstance(value, (MeterTerminal, MeterSequence)):
            raise MeterException('values in MeterSequences must be MeterTerminals or '
                                 + f'MeterSequences, not {value}')
        sequence_to_replace = self[key]
        if value.ratioEqual(sequence_to_replace):
            self._partition[key] = value
        else:
            raise MeterException(f'cannot insert {value} into space of {self[key]}')

        # clear cache
        self._levelListCache = {}

    def _reprInternal(self):
        return str(self)

    def __str__(self):
        return '{' + self.partitionDisplay + '}'

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
        >>> a = meter.MeterSequence([a, a])
        >>> a.partitionDisplay
        '{1/4+1/4+1/4+1/4}+{1/4+1/4+1/4+1/4}'
        '''
        msg = []
        for mt in self._partition:
            msg.append(str(mt))
        return '+'.join(msg)

    # -------------------------------------------------------------------------

    def _clearPartition(self):
        '''
        This will not sync with .numerator and .denominator if called alone
        '''
        self._partition = []
        # clear cache
        self._levelListCache = {}

    def addTerminal(self, value: MeterTerminal | MeterSequence | str):
        '''
        Add an object to the partition list.

        This does not update numerator and denominator.  Call updateRatio afterwards.

        ???: (targetWeight is the expected total Weight for this MeterSequence. This
        would be self.weight, but often partitions are cleared before addTerminal is called.)
        '''
        # NOTE: this is a performance critical method

        if isinstance(value, (MeterTerminal, MeterSequence)):
            mt = value
        else:  # assume it is a string
            value_tuple = tools.slashToTuple(value)
            mt = getMeterTerminal(numerator=value_tuple.numerator,
                                  denominator=value_tuple.denominator)
        self._partition.append(mt)
        # clear cache
        self._levelListCache = {}

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
    def partitionByCount(self, countRequest: int, loadDefault: bool = True):
        '''
        Divide the current MeterSequence into the requested number of parts.

        If it is not possible to divide it into the requested number, and
        loadDefault is `True`, then give the default partition:

        This will destroy any established structure in the stored partition.

        >>> a = meter.MeterSequence('4/4')
        >>> a
        <music21.meter.core.MeterSequence {4/4}>
        >>> a.partitionByCount(2)
        >>> a
        <music21.meter.core.MeterSequence {1/2+1/2}>
        >>> str(a)
        '{1/2+1/2}'
        >>> a.partitionByCount(4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        The partitions are not guaranteed to be the same length if the
        meter is irregular:

        >>> b = meter.MeterSequence('5/8')
        >>> b.partitionByCount(2)
        >>> b
         <music21.meter.core.MeterSequence {2/8+3/8}>

        This relies on a pre-defined exemption for partitioning 5 by 3:

        >>> b.partitionByCount(3)
        >>> str(b)
        '{2/8+2/8+1/8}'

        Here we use loadDefault=True to get the default partition in case
        there is no known way to do this:

        >>> a = meter.MeterSequence('5/8')
        >>> a.partitionByCount(11)
        >>> str(a)
        '{2/8+3/8}'

        If loadDefault is False then an error is raised:

        >>> a.partitionByCount(11, loadDefault=False)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by 11 (5/8)
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
            if loadDefault:
                optMatch = opts[0]
            else:
                numerator = self.numerator
                denom = self.denominator
                raise MeterException(
                    f'Cannot set partition by {countRequest} ({numerator}/{denom})'
                )

        targetWeight = self.weight
        # environLocal.printDebug(['partitionByCount, targetWeight', targetWeight])
        self._clearPartition()  # weight will now be zero
        for mStr in optMatch:
            self.addTerminal(mStr)
        self.weight = targetWeight

        # clear cache
        self._levelListCache = {}

    def partitionByList(self, numeratorList: Iterable[int | str]):
        '''
        Given a numerator list, partition MeterSequence into a new list
        of MeterTerminals

        >>> a = meter.MeterSequence('4/4')
        >>> a.partitionByList([1, 1, 1, 1])
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        This divides it into two equal parts:

        >>> a.partitionByList([1, 1])
        >>> str(a)
        '{1/2+1/2}'

        And now into one big part:

        >>> a.partitionByList([1])
        >>> str(a)
        '{1/1}'

        Here we divide 4/4 very unconventionally:

        >>> a.partitionByList(['3/4', '1/8', '1/8'])
        >>> a
        <music21.meter.core.MeterSequence {3/4+1/8+1/8}>

        But the basics of the MeterSequence must be observed:

        >>> a.partitionByList(['3/4', '1/8', '5/8'])
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by ['3/4', '1/8', '5/8']
        '''
        optMatch: MeterSequence | tuple[str, ...] | None = None

        # assume a list of terminal definitions
        if isinstance(numeratorList[0], str):
            test = MeterSequence()
            for mtStr in numeratorList:
                test.addTerminal(mtStr)
            test.updateRatio()
            # if durations are equal, this can be used as a partition
            if self.duration.quarterLength == test.duration.quarterLength:
                optMatch = test
            else:
                raise MeterException(f'Cannot set partition by {numeratorList}')

        elif sum(numeratorList) in [self.numerator * x for x in range(1, 9)]:
            for i in range(1, 9):
                if sum(numeratorList) == self.numerator * i:
                    optMatchList: list[str] = []
                    for n in numeratorList:
                        optMatchList.append(f'{n}/{self.denominator * i}')
                    optMatch = tuple(optMatchList)
                    break

        # last resort: search options
        else:
            opts = self.getPartitionOptions()
            optMatch = None
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

        # Since we have a numerator/denominator match, set this MeterSequence
        targetWeight = self.weight
        self._clearPartition()  # clears self.weight
        for mStr in optMatch:
            self.addTerminal(mStr)
        self.weight = targetWeight

        # clear cache
        self._levelListCache = {}

    def partitionByOtherMeterSequence(self, other: MeterSequence):
        '''
        Set partition to that found in another
        MeterSequence

        >>> a = meter.MeterSequence('4/4', 4)
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        >>> b = meter.MeterSequence('4/4', 2)
        >>> a.partitionByOtherMeterSequence(b)
        >>> len(a)
        2
        >>> str(a)
        '{1/2+1/2}'
        '''
        if (self.numerator != other.numerator
                or self.denominator != other.denominator):
            raise MeterException('Cannot set partition for unequal MeterSequences')
        targetWeight = self.weight
        self._clearPartition()
        for mt in other:
            self.addTerminal(copy.deepcopy(mt))  # REFACTOR: do not deepcopy.
        self.weight = targetWeight
        # clear cache
        self._levelListCache = {}

    def partition(
        self,
        value: int | MeterSequence | Iterable[int, MeterSequence],
        loadDefault: bool = False
    ):
        '''
        Partitioning creates and sets a number of MeterTerminals
        that make up this MeterSequence.

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
        >>> b.partition(13)
        >>> len(b)
        13
        >>> str(b)
        '{1/8+1/8+1/8+...+1/8}'

        >>> a.partition(b)
        >>> len(a)
        13
        >>> str(a)
        '{1/8+1/8+1/8+...+1/8}'

        Demo of loadDefault: if impossible, then do it another way...

        >>> c = meter.MeterSequence('3/128')
        >>> c.partition(2)
        Traceback (most recent call last):
        music21.exceptions21.MeterException: Cannot set partition by 2 (3/128)

        >>> c = meter.MeterSequence('3/128')
        >>> c.partition(2, loadDefault=True)
        >>> len(c)
        3
        >>> str(c)
        '{1/128+1/128+1/128}'
        '''
        if common.isListLike(value):
            self.partitionByList(value)
        elif isinstance(value, MeterSequence):
            self.partitionByOtherMeterSequence(value)
        elif isinstance(value, int):
            self.partitionByCount(value, loadDefault=loadDefault)
        else:
            raise MeterException(f'cannot process partition argument {value}')

    def subdividePartitionsEqual(self, divisions=None):
        '''
        Subdivide all partitions by equally-spaced divisions,
        given a divisions value. Manipulates this MeterSequence in place.

        Divisions value may optionally be a MeterSequence,
        from which a top-level partitioning structure is derived.

        >>> ms = meter.MeterSequence('2/4')
        >>> ms.partition(2)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+1/4}>
        >>> ms.subdividePartitionsEqual(2)
        >>> ms
        <music21.meter.core.MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> ms[0].subdividePartitionsEqual(2)
        >>> ms
        <music21.meter.core.MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{1/8+1/8}}>
        >>> ms[1].subdividePartitionsEqual(2)
        >>> ms
        <music21.meter.core.MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}>

        >>> ms = meter.MeterSequence('2/4+3/4')
        >>> ms.subdividePartitionsEqual(None)
        >>> ms
        <music21.meter.core.MeterSequence {{1/4+1/4}+{1/4+1/4+1/4}}>
        '''
        for i in range(len(self)):
            if divisions is None:  # get dynamically
                if self[i].numerator.bit_count() == 1:  # (1, 2, 4, 8, 16, etc.)
                    divisionsLocal = 2
                elif self[i].numerator == 3:
                    divisionsLocal = 3
                elif not self[i].numerator % 3:
                    divisionsLocal = self[i].numerator // 3
                else:
                    divisionsLocal = self[i].numerator
            else:
                divisionsLocal = divisions
            # environLocal.printDebug(['got divisions:', divisionsLocal,
            #   'for numerator', self[i].numerator, 'denominator', self[i].denominator])
            self[i] = self[i].subdivide(divisionsLocal)

        # clear cache
        self._levelListCache = {}

    def _subdivideNested(self, processObjList, divisions):
        # noinspection PyShadowingNames
        '''
        Recursive nested call routine. Return a reference to the newly created level.

        >>> ms = meter.MeterSequence('2/4')
        >>> ms.partition(2)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+1/4}>
        >>> post = ms._subdivideNested([ms], 2)
        >>> ms
        <music21.meter.core.MeterSequence {{1/8+1/8}+{1/8+1/8}}>
        >>> post = ms._subdivideNested(post, 2)  # pass post here
        >>> ms
        <music21.meter.core.MeterSequence {{{1/16+1/16}+{1/16+1/16}}+{{1/16+1/16}+{1/16+1/16}}}>
        '''
        for obj in processObjList:
            obj.subdividePartitionsEqual(divisions)
        # gather references for recursive processing
        post = []
        for obj in processObjList:
            for sub in obj:
                post.append(sub)
        # clear cache
        self._levelListCache = {}
        return post

    def subdivideNestedHierarchy(self, depth, firstPartitionForm=None,
                                 normalizeDenominators=True):
        '''
        Create nested structure down to a specified depth;
        the first division is set to one; the second division
        may be by 2 or 3; remaining divisions are always by 2.

        This a destructive procedure that will remove
        any existing partition structures.

        `normalizeDenominators`, if True, will reduce all denominators to the same minimum level.

        >>> ms = meter.MeterSequence('4/4')
        >>> ms.subdivideNestedHierarchy(1)
        >>> ms
        <music21.meter.core.MeterSequence {{1/2+1/2}}>
        >>> ms.subdivideNestedHierarchy(2)
        >>> ms
        <music21.meter.core.MeterSequence {{{1/4+1/4}+{1/4+1/4}}}>
        >>> ms.subdivideNestedHierarchy(3)
        >>> ms
        <music21.meter.core.MeterSequence {{{{1/8+1/8}+{1/8+1/8}}+{{1/8+1/8}+{1/8+1/8}}}}>

        I think you get the picture...

        The effects above are not cumulative.  Users can skip directly to
        whatever level of hierarchy they want.

        >>> ms2 = meter.MeterSequence('4/4')
        >>> ms2.subdivideNestedHierarchy(3)
        >>> ms2
        <music21.meter.core.MeterSequence {{{{1/8+1/8}+{1/8+1/8}}+{{1/8+1/8}+{1/8+1/8}}}}>
        '''
        # as a hierarchical representation, zeroth subdivision must be 1
        self.partition(1)
        depthCount = 0

        # initial divisions are often based on numerator or are provided
        # by looking at the number of top-level beat partitions
        # thus, 6/8 will have 2, 18/4 should have 5
        if isinstance(firstPartitionForm, MeterSequence):
            # change self in place, as we cannot re-assign to self:
            #     self = self.subdivideByOther(firstPartitionForm.getLevel(0))
            self.load(firstPartitionForm.getLevel(0))
            depthCount += 1
        else:  # can be just a number
            if firstPartitionForm is None:
                firstPartitionForm = self.numerator
            # use a fixed mapping for first divider; may be a good algo solution
            if firstPartitionForm in [1, 2, 4, 8, 16, 32]:
                divFirst = 2
            elif firstPartitionForm in [3]:
                divFirst = 3
            # elif firstPartitionForm in [6, 9, 12, 15, 18]:
            #     divFirst = firstPartitionForm / 3
            # otherwise, set the first div to the number of beats; in 18/4
            # this should be 6
            else:  # set to numerator
                divFirst = firstPartitionForm

            # use partitions equal, divide by number
            self.subdividePartitionsEqual(divFirst)
            # self[h] = self[h].subdivide(divFirst)
            depthCount += 1

        # environLocal.printDebug(['subdivideNestedHierarchy(): firstPartitionForm:',
        #                          firstPartitionForm, ': self: ', self])

        # all other partitions are recursive; start first with list
        post = [self[0]]
        while depthCount < depth:
            # setting divisions to None will get either 2/3 for all components
            post = self._subdivideNested(post, divisions=None)
            depthCount += 1
            # need to detect cases of unequal denominators
            if not normalizeDenominators:
                continue
            while True:
                d = []
                for ref in post:
                    if ref.denominator not in d:
                        d.append(ref.denominator)
                # if we have more than one denominator; we need to normalize
                # environLocal.printDebug(['subdivideNestedHierarchy():', 'd',  d,
                #   'post', post, 'depthCount', depthCount])
                if len(d) > 1:
                    postNew = []
                    for i in range(len(post)):
                        # if this is a lower denominator (1/4 not 1/8),
                        # process again
                        if post[i].denominator == min(d):
                            postNew += self._subdivideNested([post[i]],
                                                             divisions=None)
                        else:  # keep original if no problem
                            postNew.append(post[i])
                    post = postNew  # reassigning to original
                else:
                    break

        # clear cache; done in self._subdivideNested and possibly not
        # needed here
        self._levelListCache = {}

        # environLocal.printDebug(['subdivideNestedHierarchy(): post nested processing:',  self])

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
        countName = ('Empty',  # should not happen...
                     'Single',
                     'Duple', 'Triple', 'Quadruple', 'Quintuple',
                     'Sextuple', 'Septuple', 'Octuple')

        if count < len(countName):
            return countName[count]
        else:
            return str(count) + '-uple'

    # --------------------------------------------------------------------------
    # loading is always destructive

    def load(self,
             value: str | MeterTerminal | MeterSequence |
                    Iterable[str | MeterTerminal | MeterSequence],
             partitionRequest=None,
             *,
             autoWeight=False,
             targetWeight=None):
        '''
        This method is called when a MeterSequence is created, or if a MeterSequence is re-set.

        User can enter a list of values or an abbreviated slash notation.

        autoWeight, if True, will attempt to set weights.
        targetWeight, if given, will be used instead of self.weight

        loading is a destructive operation.

        >>> a = meter.MeterSequence()
        >>> a.load('4/4', 4)
        >>> str(a)
        '{1/4+1/4+1/4+1/4}'

        >>> a.load('4/4', 2)  # request 2 beats
        >>> str(a)
        '{1/2+1/2}'

        >>> a.load('5/8', 2)  # request 2 beats
        >>> str(a)
        '{2/8+3/8}'

        >>> a.load('5/8+4/4')
        >>> str(a)
        '{5/8+4/4}'
        '''
        # NOTE: this is a performance critical method
        if autoWeight:
            if targetWeight is None:
                # get from current MeterSequence
                targetWeight = self.weight  # store old
        else:  # None will not set any value
            targetWeight = None

        # environLocal.printDebug(['calling load in MeterSequence, got targetWeight', targetWeight])
        self._clearPartition()

        if isinstance(value, str):
            ratioList, self.isSummedNumerator = tools.slashMixedToFraction(value)
            for n, d in ratioList:
                self.addTerminal(getMeterTerminal(n, d))
            self.updateRatio()
            self.weight = targetWeight  # may be None

        elif isinstance(value, MeterTerminal):
            # if we have a single MeterTerminal and autoWeight is active
            # set this terminal to the old weight
            mt = value
            if targetWeight is not None:
                mt = getMeterTerminal(mt.numerator, mt.denominator, weight=targetWeight)
            self.addTerminal(mt)
            self.updateRatio()
            # do not need to set weight, as based on terminal
            # environLocal.printDebug([
            #    'created MeterSequence from MeterTerminal; old weight, new weight',
            #    value.weight, self.weight])

        elif common.isIterable(value):  # a list of Terminals or Sequence es
            for obj in value:
                # environLocal.printDebug('creating MeterSequence with %s' % obj)
                self.addTerminal(obj)
            self.updateRatio()
            self.weight = targetWeight  # may be None
        else:
            raise MeterException(f'cannot create a MeterSequence with a {value!r}')

        if partitionRequest is not None:
            self.partition(partitionRequest)

        # clear cache
        self._levelListCache = {}

    def updateRatio(self):
        '''
        Look at _partition to determine the total
        numerator and denominator values for this sequence

        This should only be called internally, as MeterSequences
        are supposed to be immutable (mostly)
        '''
        fTuple = tuple((mt.numerator, mt.denominator) for mt in self._partition)
        # clear first to avoid partial updating
        # can only set to private attributes
        # self.numerator, self.denominator = None, 1
        self.numerator, self.denominator = tools.fractionSum(fTuple)
        # must call ratio changed directly as not using properties

    # --------------------------------------------------------------------------
    # properties
    # do not permit setting of numerator/denominator

    @property
    def weight(self):
        '''
        Get or set the weight for each object in this MeterSequence

        >>> a = meter.MeterSequence('3/4')
        >>> a.partition(3)
        >>> a.weight = 1
        >>> a[0].weight
        0.333...
        >>> b = meter.MeterTerminal(1, 4, weight=0.25)
        >>> c = meter.MeterTerminal(1, 4, weight=0.25)
        >>> d = meter.MeterSequence([b, c])
        >>> d.weight
        0.5

        Assume this MeterSequence is a whole, not a part of some larger MeterSequence.
        Thus, we cannot use numerator/denominator relationship
        as a scalar.
        '''
        summation = 0
        for obj in self._partition:
            summation += obj.weight  # may be a MeterTerminal or MeterSequence
        return summation

    @weight.setter
    def weight(self, value):
        # environLocal.printDebug(['calling setWeight with value', value])

        if value is None:
            pass  # do nothing
        else:
            if not common.isNum(value):
                raise MeterException('weight values must be numbers')
            try:
                totalRatio = self.numerator / self.denominator
            except TypeError:
                raise MeterException(
                    'Something wrong with the type of '
                    + 'this numerator %s %s or this denominator %s %s' %
                    (self.numerator, type(self.numerator),
                     self.denominator, type(self.denominator)))

            new_partition = []
            for mt in self._partition:
                partRatio = mt.numerator / mt.denominator
                new_weight = value * (partRatio / totalRatio)
                if isinstance(mt, MeterTerminal):
                    new_mt = getMeterTerminal(mt.numerator,
                                              mt.denominator,
                                              weight=new_weight)
                    new_partition.append(new_mt)
                else:
                    # MeterSequence
                    mt.weight = new_weight
                    new_partition.append(mt)
                # mt.weight = (partRatio/totalRatio) #* totalRatio
                # environLocal.printDebug(['setting weight based on part, total, weight',
                #    partRatio, totalRatio, mt.weight])
            self._partition = new_partition

    def _getFlatList(self):
        '''
        Return a flattened version of this
        MeterSequence as a list of MeterTerminals.

        This return a list and not a new MeterSequence b/c MeterSequence objects
        are generally immutable and thus it does not make sense
        to concatenate them.


        >>> a = meter.MeterSequence('3/4')
        >>> a.partition(3)
        >>> b = a._getFlatList()
        >>> len(b)
        3

        >>> a[1] = a[1].subdivide(4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+1/16+1/16}+1/4}>
        >>> len(a)
        3
        >>> b = a._getFlatList()
        >>> len(b)
        6

        >>> a[1][2] = a[1][2].subdivide(4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = a._getFlatList()
        >>> len(b)
        9
        '''
        mtList = []
        for obj in self._partition:
            if not isinstance(obj, MeterSequence):
                mtList.append(obj)
            else:  # its a meter sequence
                mtList += obj._getFlatList()
        return mtList

    @property
    def flat(self):
        '''
        deprecated.  Call .flatten() instead.  To be removed in v11.
        '''
        return self.flatten()

    def flatten(self) -> MeterSequence:
        '''
        Return a new MeterSequence composed of the flattened representation.

        >>> ms = meter.MeterSequence('3/4', 3)
        >>> b = ms.flatten()
        >>> len(b)
        3

        >>> ms[1] = ms[1].subdivide(4)
        >>> b = ms.flatten()
        >>> len(b)
        6

        >>> ms[1][2] = ms[1][2].subdivide(4)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = ms.flatten()
        >>> len(b)
        9
        '''
        post = MeterSequence()
        post.load(self._getFlatList())
        return post

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
        This should be optimized to store values unless the structure has changed.
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
        >>> ms.partition(4)
        >>> ms.isUniformPartition()
        True
        >>> ms[0] = ms[0].subdivideByCount(2)
        >>> ms[1] = ms[1].subdivideByCount(4)
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
        >>> ms.partition(2)
        >>> ms.isUniformPartition()
        False

        Changed in v7 -- depth is keyword only
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

    def getLevelList(self, levelCount, flat=True) -> list[MeterTerminal | MeterSequence]:
        '''
        Recursive utility function that gets everything at a certain level.

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelList(0)
        [<music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>,
         <music21.meter.core.MeterTerminal 1/4>]

        >>> meter.MeterSequence(b.getLevelList(0))
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> meter.MeterSequence(b.getLevelList(1))
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/8+1/8}>
        >>> meter.MeterSequence(b.getLevelList(2))
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        >>> meter.MeterSequence(b.getLevelList(3))
        <music21.meter.core.MeterSequence {1/4+1/8+1/8+1/4+1/16+1/16+1/8}>
        '''
        cacheKey = (levelCount, flat)
        try:  # check in cache
            return self._levelListCache[cacheKey]
        except KeyError:
            pass

        mtList = []
        for i, el in enumerate(self._partition):
            # environLocal.printDebug(['getLevelList weight', i, self[i].weight])
            if isinstance(el, MeterTerminal):
                # a meter terminal
                mtList.append(el)
            else:  # its a sequence
                if levelCount > 0:  # retain this sequence but get lower level
                    # reduce level by 1 when recursing; do not
                    # change levelCount here
                    mtList += el.getLevelList(
                        levelCount - 1, flat)
                else:  # level count is at zero
                    if flat:  # make sequence into a terminal
                        mt = getMeterTerminal(
                            numerator=el.numerator,
                            denominator=el.denominator,
                            weight=el.weight,
                        )
                        # set weight to that of the sequence
                        mtList.append(mt)
                    else:  # its not a terminal, its a meter sequence
                        mtList.append(el)
        # store in cache
        self._levelListCache[cacheKey] = mtList
        return mtList

    def getLevel(self, level=0, flat=True):
        '''
        Return a complete MeterSequence with the same numerator/denominator
        relationship but that represents any partitions found at the requested
        level. A sort of flatness with variable depth.

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
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
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
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

        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b.getLevelWeight(0)
        [0.25, 0.25, 0.25, 0.25]

        >>> b[3][0] = b[3][0].subdivide(2)
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
        >>> a.partition(4)
        >>> a.offsetToIndex(0.5)
        0
        >>> a.offsetToIndex(3.5)
        3

        >>> a.partition([1, 2, 1])
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
                + f'where total duration is {self.duration.quarterLength}'
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
        >>> a[1] = a[1].subdivide(4)
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
            end = qPos + self[i].duration.quarterLength
            # if adjoining ends are permitted, first match is found
            if includeCoincidentBoundaries:
                if start <= qLenPos <= end:
                    match.append(i)
                    break
            else:
                if start <= qLenPos < end:
                    match.append(i)
                    break
            qPos += self[i].duration.quarterLength

        if i is not None and isinstance(self[i], MeterSequence):  # recurse
            # qLenPosition needs to be relative to this subdivision
            # start is our current position that this subdivision
            # starts at
            qLenPosShift = qLenPos - start
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
                    'cannot access qLenPos %s when total duration is %s and ts is %s' % (
                        qLenPos, self.duration.quarterLength, self))

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

        ??? Not sure what this does...
        '''
        qLenPos = opFrac(qLenPos)
        if qLenPos >= self.duration.quarterLength or qLenPos < 0:
            raise MeterException(
                'cannot access qLenPos %s when total duration is %s and ts is %s' % (
                    qLenPos, self.duration.quarterLength, self))
        iMatch = self.offsetToIndex(qLenPos)
        return opFrac(self[iMatch].weight)

    def offsetToDepth(self, qLenPos, align='quantize', index: int | None = None):
        '''
        Given a qLenPos, return the maximum available depth at this position.

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b[3][0] = b[3][0].subdivide(2)
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

        Changed in v.7 -- `index` can be provided, if known, for a long
        `MeterSequence` to improve performance.
        '''
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

@lru_cache(1024)
def constructMeterSequence(value: str, divisions: int) -> MeterSequence:
    '''
    Construct a meter sequence from a string and a number of divisions.
    '''
    return MeterSequence()



if __name__ == '__main__':
    import music21
    music21.mainTest()

