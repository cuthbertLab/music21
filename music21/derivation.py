# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         derivation.py
# Purpose:      Class for storing and managing Stream-based derivations
#
# Authors:      Christopher Ariza
#               Josiah Oberholtzer
#
# Copyright:    Copyright © 2011-2014 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

'''
This module defines objects for tracking the derivation of one
:class:`~music21.stream.Stream` from another.
'''

import functools
import unittest

from music21 import common
from music21.common import SlottedObjectMixin
# imported by stream

from music21 import environment
_MOD = "derivation.py"
environLocal = environment.Environment(_MOD)


def derivationMethod(function):
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        result.derivation.origin = self
        result.derivation.method = function.__name__
        return result
    return wrapper


class Derivation(SlottedObjectMixin):
    '''
    A Derivation object keeps track of which Streams (or perhaps other Music21Objects)
    a Stream has come from and how.
    
    Derivation is automatically updated by many methods:
    
    >>> import copy
    >>> sOrig = stream.Stream(id='orig')
    >>> sNew = copy.deepcopy(sOrig)
    >>> sNew.id = 'copy'
    >>> sNew.derivation
    <Derivation of <music21.stream.Stream copy> 
        from <music21.stream.Stream orig> via "__deepcopy__">

    >>> sNew.derivation.client
    <music21.stream.Stream copy>
    >>> sNew.derivation.client is sNew
    True
    >>> sNew.derivation.origin
    <music21.stream.Stream orig>
    >>> sNew.derivation.method
    '__deepcopy__'
    

    >>> s1 = stream.Stream()
    >>> s1.id = "DerivedStream"
    >>> d1 = derivation.Derivation(s1)

    >>> s2 = stream.Stream()
    >>> s2.id = "OriginalStream"
        
    >>> d1.method = 'manual'
    >>> d1.origin = s2
    >>> d1
    <Derivation of <music21.stream.Stream DerivedStream> from 
        <music21.stream.Stream OriginalStream> via "manual">
    >>> d1.origin is s2
    True

    >>> d1.client is s1
    True

    >>> import copy
    >>> d2 = copy.deepcopy(d1)
    >>> d2.origin is s2
    True

    >>> d1.method = 'measure'
    >>> d1.method
    'measure'
        
    Deleting the origin stream does not change the Derivation, since origin is held by strong ref:
    
    >>> import gc  # Garbage collection...
    >>> del(s2)
    >>> unused = gc.collect()  # ensure Garbage collection is run
    >>> d1
    <Derivation of <music21.stream.Stream DerivedStream> 
        from <music21.stream.Stream OriginalStream> via "measure">

    But deleting the client stream changes the Derivation, since client is held by weak ref,
    and will also delete the origin (so long as client was ever set)

    >>> del(s1)
    >>> unused = gc.collect()  # ensure Garbage collection is run
    >>> d1
    <Derivation of None from None via "measure">
    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_client',
        '_clientId',
        '_method',
        '_origin',
        '_originId',
        )

    ### INITIALIZER ###

    def __init__(self, client=None):
        # store a reference to the Stream that has this Derivation object as a property
        self._client = None
        self._clientId = None  # store id to optimize w/o unwrapping
        self._method = None
        # origin should be stored as a weak ref -- the place where the client was derived from.
        self._origin = None
        self._originId = None  # store id to optimize w/o unwrapping
        # set client; can handle None
        self.client = client

    ### SPECIAL METHODS ###

    def __deepcopy__(self, memo=None):
        '''
        Manage deepcopying by creating a new reference to the same object. If
        the origin no longer exists, than origin is set to None
        '''
        new = type(self)()
        new.client = self.client
        new.origin = self.origin
        return new

    def __repr__(self):
        '''
        representation of the Derivation
        '''
        return '<%(class)s of %(client)s from %(origin)s via "%(method)s">' % {
                        'class': self.__class__.__name__,
                        'client': self.client,
                        'origin': self.origin,
                        'method': self.method
                                }
    ## unwrap weakref for pickling

    def __getstate__(self):
        self._client = common.unwrapWeakref(self._client)
        return SlottedObjectMixin.__getstate__(self)

    def __setstate__(self, state):
        SlottedObjectMixin.__setstate__(self, state)
        self._client = common.wrapWeakref(self._client)

    ### PUBLIC METHODS ###

    ### PUBLIC PROPERTIES ###

    @property
    def client(self):
        c = common.unwrapWeakref(self._client)
        if c is None and self._clientId is not None:
            self._clientId = None
            self._client = None
            self._origin = None
            self._originId = None
        return c

    @client.setter
    def client(self, client):
        # client is the Stream that this derivation lives on
        if client is None:
            self._clientId = None
            self._client = None
        else:
            self._clientId = id(client)
            self._client = common.wrapWeakref(client)

    def chain(self):
        '''
        Iterator/Generator
        
        Returns Streams that this Derivation's client Stream was derived
        from. This provides a way to obtain all Streams that the client passed
        through, such as those created by
        :meth:`~music21.stream.Stream.getElementsByClass` or
        :attr:`~music21.stream.Stream.flat`.

        >>> s1 = stream.Stream()
        >>> s1.id = 's1'
        >>> s1.repeatAppend(note.Note(), 10)
        >>> s1.repeatAppend(note.Rest(), 10)
        >>> s2 = s1.getElementsByClass('GeneralNote').stream()
        >>> s2.id = 's2'
        >>> s3 = s2.getElementsByClass('Note').stream()
        >>> s3.id = 's3'
        >>> for y in s3.derivation.chain():
        ...     print(y)
        <music21.stream.Stream s2>
        <music21.stream.Stream s1>
        
        >>> list(s3.derivation.chain()) == [s2, s1]
        True
        '''
        origin = self.origin
        while origin is not None:
            yield origin
            origin = origin.derivation.origin

    @property
    def method(self):
        '''
        Returns the string of the method that was used to generate this
        Stream.

        >>> s = stream.Stream()
        >>> s.derivation.method is None
        True

        >>> sNotes = s.notes.stream()
        >>> sNotes.derivation.method
        'notes'
        '''
        return self._method

    @method.setter
    def method(self, method):
        '''
        Sets a string identifying how the object was derived.

        Some examples are 'getElementsByClass' etc.

        >>> s = stream.Stream()
        >>> s.append(clef.TrebleClef())
        >>> s.append(note.Note())
        >>> sNotes = s.notes
        >>> sNotes.derivation
        <music21.derivation.Derivation object at 0x...>

        >>> sNotes.derivation.method
        >>> derived.method
        'notes'

        >>> derived.method = 'blah'
        >>> derived.method
        'blah'

        >>> sNotes.derivation.method
        'blah'
        '''
        self._method = method

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, origin):
        # for now, origin is not a weak ref
        if origin is None:
            self._originId = None
            self._origin = None
        else:
            self._originId = id(origin)
            self._origin = origin
            #self._origin = common.wrapWeakref(origin)

    @property
    def rootDerivation(self):
        r'''
        Return a reference to the oldest source of this Stream; that is, chain
        calls to :attr:`~music21.stream.Stream.derivesFrom` until we get to a
        Stream that cannot be further derived.

        >>> s1 = stream.Stream()
        >>> s1.repeatAppend(note.Note(), 10)
        >>> s1.repeatAppend(note.Rest(), 10)
        >>> s2 = s1.getElementsByClass('GeneralNote').stream()
        >>> s3 = s2.getElementsByClass('Note').stream()
        >>> s3.derivation.rootDerivation is s1
        True
        '''
        derivationChain = list(self.chain())
        if len(derivationChain):
            return derivationChain[-1]
        else:
            return None

#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------
# define presented order in documentation

_DOC_ORDER = [Derivation]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)
