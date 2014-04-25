# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         derivation.py
# Purpose:      Class for storing and managing Stream-based derivations
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL
#------------------------------------------------------------------------------

'''
This module defines objects for tracking the derivation of one
:class:`~music21.stream.Stream` from another.
'''

import functools
import unittest

from music21 import common
from music21.base import SlottedObject
# imported by stream

from music21 import environment
_MOD = "derivation.py"
environLocal = environment.Environment(_MOD)


def derivationMethod(function):
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        result.derivesFrom = self
        result.derivationMethod = function.__name__
        return result
    return wrapper


class Derivation(SlottedObject):
    '''
    A Derivation object keeps track of which Streams

    ::

        >>> import copy
        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> d1 = derivation.Derivation(s1)
        >>> d1.origin = s2
        >>> d1.origin is s2
        True

    ::

        >>> d1.client is s1
        True

    ::

        >>> d2 = copy.deepcopy(d1)
        >>> d2.origin is s2
        True

    ::

        >>> d1.method = 'measure'
        >>> d1.method
        'measure'

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
        # origin should be stored as a weak ref
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
        new = self.__class__()
        new.client = self.client
        new.origin = self.origin
        return new

    ### PUBLIC METHODS ###

    def wrapWeakref(self):
        '''Wrap all stored objects with weakrefs.
        '''
        if not common.isWeakref(self._client):
            # update id in case it has changed
            self._clientId = id(self._client)
            post = common.wrapWeakref(self._client)
            self._client = post

    def unwrapWeakref(self):
        '''
        Unwrap any and all weakrefs stored.

        Necessary for pickling operations.

        ::

            >>> s1 = stream.Stream()
            >>> s2 = stream.Stream()
            >>> d1 = derivation.Derivation(s1) # sets client
            >>> d1.origin = s2
            >>> common.isWeakref(d1._client)
            True

        ::

            >>> d1.unwrapWeakref()
            >>> common.isWeakref(d1._client)
            False

        '''
        #environLocal.printDebug(['derivation pre unwrap: self._client', self._client])
        post = common.unwrapWeakref(self._client)
        self._client = post
        #environLocal.printDebug(['derivation post unwrap: self._client', self._client])

    ### PUBLIC PROPERTIES ###

    @property
    def client(self):
        return common.unwrapWeakref(self._client)

    @client.setter
    def client(self, client):
        # client is the Stream that this derivation lives on
        if client is None:
            self._clientId = None
            self._client = None
        else:
            self._clientId = id(client)
            self._client = common.wrapWeakref(client)

    @property
    def derivationChain(self):
        '''
        Return a list Streams that this Derivation's client Stream was derived
        from. This provides a way to obtain all Streams that the client passed
        through, such as those created by
        :meth:`~music21.stream.Stream.getElementsByClass` or
        :attr:`~music21.stream.Stream.flat`.

        ::

            >>> s1 = stream.Stream()
            >>> s1.repeatAppend(note.Note(), 10)
            >>> s1.repeatAppend(note.Rest(), 10)
            >>> s2 = s1.getElementsByClass('GeneralNote')
            >>> s3 = s2.getElementsByClass('Note')
            >>> s3.derivation.derivationChain == [s2, s1]
            True

        '''

        result = []
        origin = self.origin
        while origin is not None:
            result.append(origin)
            origin = origin.derivation.origin
        return result

    @property
    def method(self):
        '''
        Returns the string of the method that was used to generate this
        Stream.  Note that it's identical to the property derivationMethod on a
        Stream, so no need for any but the most advanced usages.

        ::

            >>> s = stream.Stream()
            >>> s.derivationMethod is None
            True

        ::

            >>> s.derivationMethod is s.derivation.method
            True

        ::

            >>> sNotes = s.notes
            >>> sNotes.derivationMethod
            'notes'

        '''
        return self._method

    @method.setter
    def method(self, method):
        '''
        Sets a string identifying how the object was derived.

        Some examples are 'getElementsByClass' etc.

        ::

            >>> s = stream.Stream()
            >>> s.append(clef.TrebleClef())
            >>> s.append(note.Note())
            >>> sNotes = s.notes
            >>> sNotes._derivation
            <music21.derivation.Derivation object at 0x...>

        ::

            >>> derived = sNotes._derivation
            >>> derived.getMethod()
            'notes'

        ::

            >>> derived.setMethod('blah')
            >>> derived.getMethod()
            'blah'

        ::

            >>> sNotes.derivationMethod
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

        ::

            >>> s1 = stream.Stream()
            >>> s1.repeatAppend(note.Note(), 10)
            >>> s1.repeatAppend(note.Rest(), 10)
            >>> s2 = s1.getElementsByClass('GeneralNote')
            >>> s3 = s2.getElementsByClass('Note')
            >>> s3.derivation.rootDerivation is s1
            True

        '''

        chain = self.derivationChain
        if len(chain):
            return chain[-1]
        else:
            return None



#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


#------------------------------------------------------------------------------
# define presented order in documentation

_DOC_ORDER = []

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)
