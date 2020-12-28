# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/objects.py
# Purpose:      Commonly used Objects and Mixins
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
__all__ = [
    'defaultlist',
    'SingletonCounter',
    'RelativeCounter',
    'SlottedObjectMixin',
    'EqualSlottedObjectMixin',
    'Iterator',
    'Timer',
]

import collections
import time
import weakref


class RelativeCounter(collections.Counter):
    '''
    A counter that iterates from most common to least common
    and can return new RelativeCounters that adjust for proportion or percentage.

    >>> l = ['b', 'b', 'a', 'a', 'a', 'a', 'c', 'd', 'd', 'd'] + ['e'] * 10
    >>> rc = common.RelativeCounter(l)
    >>> for k in rc:
    ...     print(k, rc[k])
    e 10
    a 4
    d 3
    b 2
    c 1

    Ties are iterated according to which appeared first in the generated list in Py3.6+.

    >>> rcProportion = rc.asProportion()
    >>> rcProportion['b']
    0.1
    >>> rcProportion['e']
    0.5
    >>> rcPercentage = rc.asPercentage()
    >>> rcPercentage['b']
    10.0
    >>> rcPercentage['e']
    50.0

    >>> for k, perc in rcPercentage.items():
    ...     print(k, perc)
    e 50.0
    a 20.0
    d 15.0
    b 10.0
    c 5.0
    '''
    # pylint:disable=abstract-method

    def __iter__(self):
        sortedKeys = sorted(super().__iter__(), key=lambda x: self[x], reverse=True)
        for k in sortedKeys:
            yield k

    def items(self):
        for k in self:
            yield k, self[k]

    def asProportion(self):
        selfLen = sum(self[x] for x in self)
        outDict = {}
        for y in self:
            outDict[y] = self[y] / selfLen
        # noinspection PyTypeChecker
        new = self.__class__(outDict)
        return new

    def asPercentage(self):
        selfLen = sum(self[x] for x in self)
        outDict = {}
        for y in self:
            outDict[y] = self[y] * 100 / selfLen
        # noinspection PyTypeChecker
        new = self.__class__(outDict)
        return new


class defaultlist(list):
    '''
    Call a function for every time something is missing:

    >>> a = common.defaultlist(lambda:True)
    >>> a[5]
    True
    '''
    def __init__(self, fx):
        super().__init__()
        self._fx = fx

    def _fill(self, index):
        while len(self) <= index:
            self.append(self._fx())

    def __setitem__(self, index, value):
        self._fill(index)
        list.__setitem__(self, index, value)

    def __getitem__(self, index):
        self._fill(index)
        return list.__getitem__(self, index)


_singletonCounter = {'value': 0}


class SingletonCounter:
    '''
    A simple counter that can produce unique numbers (in ascending order)
    regardless of how many instances exist.

    Instantiate and then call it.

    >>> sc = common.SingletonCounter()
    >>> v0 = sc()
    >>> v1 = sc()
    >>> v1 > v0
    True
    >>> sc2 = common.SingletonCounter()
    >>> v2 = sc2()
    >>> v2 > v1
    True
    '''
    def __init__(self):
        pass

    def __call__(self):
        post = _singletonCounter['value']
        _singletonCounter['value'] += 1
        return post

# ------------------------------------------------------------------------------


class SlottedObjectMixin:
    r'''
    Provides template for classes implementing slots allowing it to be pickled
    properly, even if there are weakrefs in the slots, or it is subclassed
    by something that does not define slots.

    Only use SlottedObjectMixins for objects that we expect to make so many of
    that memory storage and speed become an issue. Thus, unless you are Xenakis,
    Glissdata is probably not the best example:

    >>> import pickle
    >>> class Glissdata(common.SlottedObjectMixin):
    ...     __slots__ = ('time', 'frequency')
    >>> s = Glissdata()
    >>> s.time = 0.125
    >>> s.frequency = 440.0
    >>> #_DOCS_SHOW out = pickle.dumps(s)
    >>> #_DOCS_SHOW t = pickle.loads(out)
    >>> t = s #_DOCS_HIDE -- cannot define classes for pickling in doctests
    >>> t.time, t.frequency
    (0.125, 440.0)

    OMIT_FROM_DOCS

    >>> class BadSubclass(Glissdata):
    ...     pass

    >>> bsc = BadSubclass()
    >>> bsc.amplitude = 2
    >>> #_DOCS_SHOW out = pickle.dumps(bsc)
    >>> #_DOCS_SHOW t = pickle.loads(out)
    >>> t = bsc #_DOCS_HIDE -- cannot define classes for pickling in doctests
    >>> t.amplitude
    2
    '''

    # CLASS VARIABLES #

    __slots__ = ()

    # SPECIAL METHODS #

    def __getstate__(self):
        if getattr(self, '__dict__', None) is not None:
            state = getattr(self, '__dict__').copy()
        else:
            state = {}
        slots = self._getSlotsRecursive()
        for slot in slots:
            sValue = getattr(self, slot, None)
            if isinstance(sValue, weakref.ref):
                sValue = sValue()
                print(f'Warning: uncaught weakref found in {self!r} - {slot}, '
                      + 'will not be wrapped again')
            state[slot] = sValue
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

    def _getSlotsRecursive(self):
        '''
        Find all slots recursively.

        A private attribute so as not to change the contents of inheriting
        objects private interfaces:

        >>> b = beam.Beam()
        >>> sSet = b._getSlotsRecursive()

        sSet is a set -- independent order.  Thus for the doctest
        we need to preserve the order:

        >>> sorted(list(sSet))
        ['_editorial', '_style', 'direction', 'id', 'independentAngle', 'number', 'type']

        When a normal Beam won't cut it...

        >>> class FunkyBeam(beam.Beam):
        ...     __slots__ = ('funkiness', 'groovability')

        >>> fb = FunkyBeam()
        >>> sSet = fb._getSlotsRecursive()
        >>> sorted(list(sSet))
        ['_editorial', '_style', 'direction', 'funkiness', 'groovability',
            'id', 'independentAngle', 'number', 'type']
        '''
        slots = set()
        for cls in self.__class__.mro():
            slots.update(getattr(cls, '__slots__', ()))
        return slots


class EqualSlottedObjectMixin(SlottedObjectMixin):
    '''
    Same as above, but __eq__ and __ne__ functions are defined based on the slots.

    Slots are the only things compared, so do not mix with a __dict__ based object.

    Ignores differences in .id
    '''
    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        for thisSlot in self._getSlotsRecursive():
            if thisSlot == 'id':
                continue
            if getattr(self, thisSlot) != getattr(other, thisSlot):
                return False
        return True

    def __ne__(self, other):
        '''
        Defining __ne__ explicitly so that it inherits the same as __eq__
        '''
        return not (self == other)


# ------------------------------------------------------------------------------
class Iterator(collections.abc.Iterator):
    '''A simple Iterator object used to handle iteration of Streams and other
    list-like objects.

    >>> i = common.Iterator([2, 3, 4])
    >>> for x in i:
    ...     print(x)
    2
    3
    4
    >>> for y in i:
    ...     print(y)
    2
    3
    4
    '''
    def __init__(self, data):
        self.data = data
        self.index = 0

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self.data):
            raise StopIteration
        post = self.data[self.index]
        self.index += 1
        return post

# ------------------------------------------------------------------------------


class Timer:
    '''
    An object for timing. Call it to get the current time since starting.

    >>> t = common.Timer()
    >>> now = t()
    >>> nowNow = t()
    >>> nowNow > now
    True

    Call `stop` to stop it. Calling `start` again will reset the number

    >>> t.stop()
    >>> stopTime = t()
    >>> stopNow = t()
    >>> stopTime == stopNow
    True

    All this had better take less than one second!

    >>> stopTime < 1
    True
    '''
    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''
        Explicit start method; will clear previous values.

        Start always happens on initialization.
        '''
        self._tStart = time.time()
        self._tStop = None  # show that a new run has started so __call__ works
        self._tDif = 0

    def stop(self):
        self._tStop = time.time()
        self._tDif = self._tStop - self._tStart

    def clear(self):
        self._tStop = None
        self._tDif = 0
        self._tStart = None

    def __call__(self):
        '''
        Reports current time or, if stopped, stopped time.
        '''
        # if stopped, gets _tDif; if not stopped, gets current time
        if self._tStop is None:  # if not stopped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t

    def __str__(self):
        if self._tStop is None:  # if not stopped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t, 3))


if __name__ == '__main__':
    import music21
    music21.mainTest()
