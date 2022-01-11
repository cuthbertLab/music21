# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         meter.core.py
# Purpose:      Component objects for meters
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2015, 2021 Michael Scott Cuthbert
#               and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
This module defines two component objects for defining nested metrical structures:
:class:`~music21.meter.core.MeterTerminal` and :class:`~music21.meter.core.MeterSequence`.
'''
import copy
from typing import Optional

from music21 import prebase
from music21.common.numberTools import opFrac
from music21.common.objects import SlottedObjectMixin
from music21 import common
from music21 import duration
from music21 import environment
from music21.exceptions21 import MeterException
from music21.meter import tools

environLocal = environment.Environment('meter.core')

# -----------------------------------------------------------------------------

class MeterTerminal(prebase.ProtoM21Object, SlottedObjectMixin):
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
    '''

    # CLASS VARIABLES #

    __slots__ = (
        '_denominator',
        '_duration',
        '_numerator',
        '_overriddenDuration',
        '_weight',
    )

    # INITIALIZER #

    def __init__(self, slashNotation=None, weight=1):
        self._duration = None
        self._numerator = 0
        self._denominator = 1
        self._weight = None
        self._overriddenDuration = None

        if slashNotation is not None:
            # assign directly to values, not properties, to avoid
            # calling _ratioChanged more than necessary
            values = tools.slashToTuple(slashNotation)
            if values is not None:  # if failed to parse
                self._numerator = values.numerator
                self._denominator = values.denominator
        self._ratioChanged()  # sets self._duration

        # this will set the underlying weight attribute directly for data checking
        # explicitly calling base class method to avoid problems
        # in the derived class MeterSequence
        self._weight = weight

    # SPECIAL METHODS #

    def __deepcopy__(self, memo=None):
        '''
        Helper method to copy.py's deepcopy function. Call it from there.

        Defining a custom __deepcopy__ here is a performance boost,
        particularly in not copying _duration, directly assigning _weight, and
        other benefits.
        '''
        # call class to get a new, empty instance
        new = self.__class__()
        # for name in dir(self):
        new._numerator = self._numerator
        new._denominator = self._denominator
        new._ratioChanged()  # faster than copying dur
        # new._duration = copy.deepcopy(self._duration, memo)
        new._weight = self._weight  # these are numbers
        return new

    def _reprInternal(self):
        return str(self)

    def __str__(self):
        return str(int(self.numerator)) + '/' + str(int(self.denominator))

    def ratioEqual(self, other):
        '''
        Compare the numerator and denominator of another object.
        Note that these have to be exact matches; 3/4 is not the same as 6/8

        >>> from music21 import meter
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

    def subdivideByCount(self, countRequest=None):
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
        for that, see the :meth:`~music21.meter.MeterSequence.load` method
        of :class:`~music21.meter.MeterSequence`.
        '''
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
        # elevate to meter sequence
        ms = MeterSequence()
        ms.load(self)  # do not need to autoWeight here
        ms.partitionByList(numeratorList)  # this will split weight
        return ms

    def subdivideByOther(self, other: 'music21.meter.MeterSequence'):
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
        # elevate to meter sequence
        ms = MeterSequence()
        if other.duration.quarterLength != self.duration.quarterLength:
            raise MeterException(f'cannot subdivide by other: {other}')
        ms.load(other)  # do not need to autoWeight here
        # ms.partitionByOtherMeterSequence(other)  # this will split weight
        return ms

    def subdivide(self, value):
        '''
        Subdivision takes a MeterTerminal and, making it into a collection of MeterTerminals,
        Returns a MeterSequence.

        This is different than a partitioning a MeterSequence in that this does not happen
        in place and instead returns a new object.

        If an integer is provided, assume it is a partition count
        '''
        if common.isListLike(value):
            return self.subdivideByList(value)
        elif isinstance(value, MeterSequence):
            return self.subdivideByOther(value)
        elif common.isNum(value):
            return self.subdivideByCount(value)
        else:
            raise MeterException(f'cannot process partition argument {value}')

    # -------------------------------------------------------------------------
    # properties

    @property
    def weight(self):
        '''
        Return or set the weight of a MeterTerminal

        >>> a = meter.MeterTerminal('2/4')
        >>> a.weight = 0.5
        >>> a.weight
        0.5
        '''
        return self._weight

    @weight.setter
    def weight(self, value):
        self._weight = value

    def _getNumerator(self):
        return self._numerator

    def _setNumerator(self, value):
        '''
        >>> a = meter.MeterTerminal('2/4')
        >>> a.duration.quarterLength
        2.0
        >>> a.numerator = 11
        >>> a.duration.quarterLength
        11.0
        '''
        self._numerator = value
        self._ratioChanged()

    numerator = property(_getNumerator, _setNumerator)

    def _getDenominator(self):
        return self._denominator

    def _setDenominator(self, value):
        '''

        >>> a = meter.MeterTerminal('2/4')
        >>> a.duration.quarterLength
        2.0
        >>> a.numerator = 11
        >>> a.duration.quarterLength
        11.0
        '''
        # use duration.typeFromNumDict?
        if value not in tools.validDenominatorsSet:
            raise MeterException(f'bad denominator value: {value}')
        self._denominator = value
        self._ratioChanged()

    denominator = property(_getDenominator, _setDenominator)

    def _ratioChanged(self):
        '''If ratio has been changed, call this to update duration
        '''
        # NOTE: this is a performance critical method and should only be
        # called when necessary
        if self.numerator is None or self.denominator is None:
            self._duration = None
        else:
            self._duration = duration.Duration()
            try:
                self._duration.quarterLength = (
                    (4.0 * self.numerator) / self.denominator
                )
            except duration.DurationException:
                environLocal.printDebug(
                    ['DurationException encountered',
                     'numerator/denominator',
                     self.numerator,
                     self.denominator
                     ]
                )
                self._duration = None

    def _getDuration(self):
        '''
        duration gets or sets a duration value that
        is equal in length of the terminal.

        >>> a = meter.MeterTerminal()
        >>> a.numerator = 3
        >>> a.denominator = 8
        >>> d = a.duration
        >>> d.type
        'quarter'
        >>> d.dots
        1
        >>> d.quarterLength
        1.5
        '''

        if self._overriddenDuration:
            return self._overriddenDuration
        else:
            return self._duration

    def _setDuration(self, value):
        self._overriddenDuration = value

    duration = property(_getDuration, _setDuration)

    @property
    def depth(self):
        '''
        Return how many levels deep this part is -- the depth of a terminal is always 1
        '''
        return 1


# -----------------------------------------------------------------------------


class MeterSequence(MeterTerminal):
    '''
    A meter sequence is a list of MeterTerminals, or other MeterSequences
    '''

    # CLASS VARIABLES #

    __slots__ = (
        '_levelListCache',
        '_partition',
        'parenthesis',
        'summedNumerator',
    )

    # INITIALIZER #

    def __init__(self, value=None, partitionRequest=None):
        super().__init__()

        self._numerator = None  # rationalized
        self._denominator = None  # lowest common multiple
        self._partition = []  # a list of terminals or MeterSequences
        self._overriddenDuration = None
        self._levelListCache = {}

        # this attribute is only used in MeterTerminals, and note
        # in MeterSequences; a MeterSequences weight is based solely
        # on the sum of its components
        # del self._weight -- no -- screws up pickling -- cannot del a slotted object

        #: Bool stores whether this meter was provided as a summed numerator
        self.summedNumerator = False

        #: an optional parameter used only in meter display sequences.
        #: needed in cases where a meter component is parenthetical
        self.parenthesis = False

        if value is not None:
            self.load(value, partitionRequest)

    # SPECIAL METHODS #

    def __deepcopy__(self, memo=None):
        '''Helper method to copy.py's deepcopy function. Call it from there.

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
        new._numerator = self._numerator
        new._denominator = self._denominator
        # noinspection PyArgumentList
        new._partition = copy.deepcopy(self._partition, memo)
        new._ratioChanged()  # faster than copying dur
        # new._duration = copy.deepcopy(self._duration, memo)

        new._overriddenDuration = self._overriddenDuration
        new.summedNumerator = self.summedNumerator
        new.parenthesis = self.parenthesis

        return new

    def __getitem__(self, key):
        '''Get an MeterTerminal from _partition


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

    def __setitem__(self, key, value):
        '''
        Insert items at index positions.

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a
        <music21.meter.core.MeterSequence {1/4+1/4+1/4+1/4}>
        >>> a[0]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a[0] = a[0].subdivide(2)
        >>> a
        <music21.meter.core.MeterSequence {{1/8+1/8}+1/4+1/4+1/4}>
        >>> a[0][0] = a[0][0].subdivide(2)
        >>> a
        <music21.meter.core.MeterSequence {{{1/16+1/16}+1/8}+1/4+1/4+1/4}>
        >>> a[3]
        <music21.meter.core.MeterTerminal 1/4>
        >>> a[3] = a[0][0]
        Traceback (most recent call last):
        ...
        music21.exceptions21.MeterException: cannot insert {1/16+1/16} into space of 1/4
        '''
        # comparison of numerator and denominator
        if not isinstance(value, MeterTerminal):
            raise MeterException('values in MeterSequences must be MeterTerminals or '
                                 + f'MeterSequences, not {value}')
        if value.ratioEqual(self[key]):
            self._partition[key] = value
        else:
            raise MeterException(f'cannot insert {value} into space of {self[key]}')

        # clear cache
        self._levelListCache = {}

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

    def _addTerminal(self, value):
        '''
        Add a an object to the partition list. This does not update numerator and denominator.

        ???: (targetWeight is the expected total Weight for this MeterSequence. This
        would be self.weight, but often partitions are cleared before _addTerminal is called.)
        '''
        # NOTE: this is a performance critical method

        if isinstance(value, MeterTerminal):  # may be a MeterSequence
            mt = value
        else:  # assume it is a string
            mt = MeterTerminal(value)

        # if isinstance(value, str):
        #     mt = MeterTerminal(value)
        # elif isinstance(value, MeterTerminal):  # may be a MeterSequence
        #     mt = value
        # else:
        #     raise MeterException('cannot add %s to this sequence' % value)
        self._partition.append(mt)
        # clear cache
        self._levelListCache = {}

    def getPartitionOptions(self) -> tools.MeterOptions:
        '''
        Return either a cached or a new set of division/partition options.

        Calls tools.divisionOptionsAlgo and tools.divisionOptionsPreset (which will be empty
        except if the numerator is 5).

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

    def partitionByCount(self, countRequest, loadDefault=True):
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
            self._addTerminal(mStr)
        self.weight = targetWeight

        # clear cache
        self._levelListCache = {}

    def partitionByList(self, numeratorList):
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
        optMatch = None

        # assume a list of terminal definitions
        if isinstance(numeratorList[0], str):
            test = MeterSequence()
            for mtStr in numeratorList:
                test._addTerminal(mtStr)
            test._updateRatio()
            # if durations are equal, this can be used as a partition
            if self.duration.quarterLength == test.duration.quarterLength:
                optMatch = test
            else:
                raise MeterException(f'Cannot set partition by {numeratorList}')

        elif sum(numeratorList) in [self.numerator * x for x in range(1, 9)]:
            for i in range(1, 9):
                if sum(numeratorList) == self.numerator * i:
                    optMatch = []
                    for n in numeratorList:
                        optMatch.append(f'{n}/{self.denominator * i}')
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
            raise MeterException('Cannot set partition by %s (%s/%s)' % (
                numeratorList, self.numerator, self.denominator))

        # if a n/d match, now set this MeterSequence
        targetWeight = self.weight
        self._clearPartition()  # clears self.weight
        for mStr in optMatch:
            self._addTerminal(mStr)
        self.weight = targetWeight

        # clear cache
        self._levelListCache = {}

    def partitionByOtherMeterSequence(self, other):
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
        if (self.numerator == other.numerator
                and self.denominator == other.denominator):
            targetWeight = self.weight
            self._clearPartition()
            for mt in other:
                self._addTerminal(copy.deepcopy(mt))
            self.weight = targetWeight
        else:
            raise MeterException('Cannot set partition for unequal MeterSequences')

        # clear cache
        self._levelListCache = {}

    def partition(self, value, loadDefault=False):
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
        elif common.isNum(value):
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
                if self[i].numerator in [1, 2, 4, 8, 16]:
                    divisionsLocal = 2
                elif self[i].numerator in [3]:
                    divisionsLocal = 3
                elif self[i].numerator in [6, 9, 12, 15, 18]:
                    divisionsLocal = self[i].numerator / 3
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
        '''Recursive nested call routine. Return a reference to the newly created level.

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
            # change self in place, as we cannot re-assign to self
            # self = self.subdivideByOther(firstPartitionForm.getLevel(0))
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
    #             elif firstPartitionForm in [6, 9, 12, 15, 18]:
    #                 divFirst = firstPartitionForm / 3
            # otherwise, set the first div to the number of beats; in 18/4
            # this should be 6
            else:  # set to numerator
                divFirst = firstPartitionForm

            # use partitions equal, divide by number
            self.subdividePartitionsEqual(divFirst)
            # self[h] = self[h].subdivide(divFirst)
            depthCount += 1

#         environLocal.printDebug(['subdivideNestedHierarchy(): firstPartitionForm:',
#   firstPartitionForm, ': self: ', self])

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
             value,
             partitionRequest=None,
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
            ratioList, self.summedNumerator = tools.slashMixedToFraction(value)
            for n, d in ratioList:
                slashNotation = f'{n}/{d}'
                self._addTerminal(MeterTerminal(slashNotation))
            self._updateRatio()
            self.weight = targetWeight  # may be None

        elif isinstance(value, MeterTerminal):
            # if we have a single MeterTerminal and autoWeight is active
            # set this terminal to the old weight
            if targetWeight is not None:
                value.weight = targetWeight
            self._addTerminal(value)
            self._updateRatio()
            # do not need to set weight, as based on terminal
            # environLocal.printDebug([
            #    'created MeterSequence from MeterTerminal; old weight, new weight',
            #    value.weight, self.weight])

        elif common.isIterable(value):  # a list of Terminals or Sequence es
            for obj in value:
                # environLocal.printDebug('creating MeterSequence with %s' % obj)
                self._addTerminal(obj)
            self._updateRatio()
            self.weight = targetWeight  # may be None
        else:
            raise MeterException(f'cannot create a MeterSequence with a {value!r}')

        if partitionRequest is not None:
            self.partition(partitionRequest)

        # clear cache
        self._levelListCache = {}

    def _updateRatio(self):
        '''
        Look at _partition to determine the total
        numerator and denominator values for this sequence

        This should only be called internally, as MeterSequences
        are supposed to be immutable (mostly)
        '''
        fTuple = tuple((mt.numerator, mt.denominator) for mt in self._partition)
        # clear first to avoid partial updating
        # can only set to private attributes
        # self._numerator, self._denominator = None, 1
        self._numerator, self._denominator = tools.fractionSum(fTuple)
        # must call ratio changed directly as not using properties
        self._ratioChanged()

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
        >>> b = meter.MeterTerminal('1/4', 0.25)
        >>> c = meter.MeterTerminal('1/4', 0.25)
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
                totalRatio = self._numerator / self._denominator
            except TypeError:
                raise MeterException(
                    'Something wrong with the type of '
                    + 'this numerator %s %s or this denominator %s %s' %
                    (self._numerator, type(self._numerator),
                                      self._denominator, type(self._denominator)))

            for mt in self._partition:
                # for mt in self:
                partRatio = mt._numerator / mt._denominator
                mt.weight = value * (partRatio / totalRatio)
                # mt.weight = (partRatio/totalRatio) #* totalRatio
                # environLocal.printDebug(['setting weight based on part, total, weight',
                #    partRatio, totalRatio, mt.weight])

    @property
    def numerator(self):
        return self._numerator

    @property
    def denominator(self):
        return self._denominator

    def _getFlatList(self):
        '''Return a flat version of this MeterSequence as a list of MeterTerminals.

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
        Return a new MeterSequence composed of the flattened representation.

        >>> ms = meter.MeterSequence('3/4', 3)
        >>> b = ms.flat
        >>> len(b)
        3

        >>> ms[1] = ms[1].subdivide(4)
        >>> b = ms.flat
        >>> len(b)
        6

        >>> ms[1][2] = ms[1][2].subdivide(4)
        >>> ms
        <music21.meter.core.MeterSequence {1/4+{1/16+1/16+{1/64+1/64+1/64+1/64}+1/16}+1/4}>
        >>> b = ms.flat
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

    def getLevelList(self, levelCount, flat=True):
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
        for i in range(len(self._partition)):
            # environLocal.printDebug(['getLevelList weight', i, self[i].weight])
            if not isinstance(self._partition[i], MeterSequence):
                mt = self[i]  # a meter terminal
                mtList.append(mt)
            else:  # its a sequence
                if levelCount > 0:  # retain this sequence but get lower level
                    # reduce level by 1 when recursing; do not
                    # change levelCount here
                    mtList += self._partition[i].getLevelList(
                        levelCount - 1, flat)
                else:  # level count is at zero
                    if flat:  # make sequence into a terminal
                        mt = MeterTerminal('%s/%s' % (
                            self._partition[i].numerator, self._partition[i].denominator))
                        # set weight to that of the sequence
                        mt.weight = self._partition[i].weight
                        mtList.append(mt)
                    else:  # its not a terminal, its a meter sequence
                        mtList.append(self._partition[i])
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

    def setLevelWeight(self, weightList, level=0):
        '''
        The `weightList` is an array of weights to be applied to a
        single level of the MeterSequence.

        >>> a = meter.MeterSequence('4/4', 4)
        >>> a.setLevelWeight([1, 2, 3, 4])
        >>> a.getLevelWeight()
        [1, 2, 3, 4]

        >>> b = meter.MeterSequence('4/4', 4)
        >>> b.setLevelWeight([2, 3])
        >>> b.getLevelWeight(0)
        [2, 3, 2, 3]

        >>> b[1] = b[1].subdivide(2)
        >>> b[3] = b[3].subdivide(2)
        >>> b.getLevelWeight(0)
        [2, 3.0, 2, 3.0]

        >>> b[3][0] = b[3][0].subdivide(2)
        >>> b
        <music21.meter.core.MeterSequence {1/4+{1/8+1/8}+1/4+{{1/16+1/16}+1/8}}>
        >>> b.getLevelWeight(0)
        [2, 3.0, 2, 3.0]
        >>> b.getLevelWeight(1)
        [2, 1.5, 1.5, 2, 1.5, 1.5]
        >>> b.getLevelWeight(2)
        [2, 1.5, 1.5, 2, 0.75, 0.75, 1.5]
        '''
        levelObjs = self.getLevelList(level)
        for i in range(len(levelObjs)):
            mt = levelObjs[i]
            mt.weight = weightList[i % len(weightList)]

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
        match = None
        for i in range(len(self)):
            start = qPos
            end = opFrac(qPos + self[i].duration.quarterLength)
            # if adjoining ends are permitted, first match is found
            if includeCoincidentBoundaries:
                if start <= qLenPos <= end:
                    match = i
                    break
            else:
                # note that this is >=, meaning that the first boundary
                # is coincident
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

    def offsetToDepth(self, qLenPos, align='quantize', index: Optional[int] = None):
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


if __name__ == '__main__':
    import music21
    music21.mainTest()

