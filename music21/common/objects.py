#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/objects.py
# Purpose:      Commonly used Objects and Mixins
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
__all__ = ['defaultlist',
           'SingletonCounter',
           'SlottedObjectMixin',
           'Iterator',
           'Timer',           
          ]

import time
import weakref

class defaultlist(list):
    '''
    Call a function for every time something is missing:
    
    TO BE DEPRECATED... soon...
    
    >>> a = common.defaultlist(lambda:True)
    >>> a[5]
    True    
    '''
    def __init__(self, fx):
        list.__init__(self)
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


_singletonCounter = {}
_singletonCounter['value'] = 0

class SingletonCounter(object):
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

#-------------------------------------------------------------------------------
class SlottedObjectMixin(object):
    r'''
    Provides template for classes implementing slots allowing it to be pickled
    properly.
    
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
    
    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __getstate__(self):
        if getattr(self, '__dict__', None) is not None:
            state = getattr(self, '__dict__').copy()
        else:
            state = {}
        slots = set()
        for cls in self.__class__.mro():
            slots.update(getattr(cls, '__slots__', ()))
        for slot in slots:
            sValue = getattr(self, slot, None)
            if isinstance(sValue, weakref.ref):
                sValue = sValue()
                print("Warning: uncaught weakref found in %r - %s, will not be rewrapped" % 
                      (self, slot))
            state[slot] = sValue
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)


#-------------------------------------------------------------------------------
class Iterator(object):
    '''A simple Iterator object used to handle iteration of Streams and other
    list-like objects.
    
    >>> i = common.Iterator([2,3,4])
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

    def next(self):
        return self.__next__()


#-------------------------------------------------------------------------------
class Timer(object):
    """
    An object for timing. Call it to get the current time since starting.
    
    >>> t = common.Timer()
    >>> now = t()
    >>> nownow = t()
    >>> nownow > now
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
    """

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
        self._tStop = None # show that a new run has started so __call__ works
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
        if self._tStop is None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t

    def __str__(self):
        if self._tStop is None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t, 3))


if __name__ == '__main__':
    import music21
    music21.mainTest()

