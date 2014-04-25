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

import unittest

from music21 import common
from music21.base import SlottedObject
# imported by stream

from music21 import environment
_MOD = "derivation.py"
environLocal = environment.Environment(_MOD)


class Derivation(SlottedObject):
    '''
    A Derivation object keeps track of which Streams

    ::

        >>> import copy
        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> d1 = derivation.Derivation(s1)
        >>> d1.setOrigin(s2)
        >>> d1.getOrigin() is s2
        True

    ::

        >>> d1.getClient() is s1
        True

    ::

        >>> d2 = copy.deepcopy(d1)
        >>> d2.getOrigin() is s2
        True

    ::

        >>> d1.setMethod('measure')
        >>> d1.getMethod()
        'measure'

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_origin',
        '_originId',
        '_client',
        '_clientId',
        '_method',
        )

    ### INITIALIZER ###

    # TODO: Rename `client` to `client`
    # TODO: Rename `origin` to `origin`
    def __init__(self, client=None):
        # store a reference to the Stream that has this Derivation object as a property
        self._client = None
        self._clientId = None  # store id to optimize w/o unwrapping
        self._method = None
        # origin should be stored as a weak ref
        self._origin = None
        self._originId = None  # store id to optimize w/o unwrapping
        # set client; can handle None
        self.setClient(client)

    ### SPECIAL METHODS ###

    def __deepcopy__(self, memo=None):
        '''
        Manage deepcopying by creating a new reference to the same object. If
        the origin no longer exists, than origin is set to None
        '''
        new = self.__class__()
        new.setClient(self.getClient())
        new.setOrigin(self.getOrigin())
        return new

    ### PUBLIC METHODS ###

    def getClient(self):
        return common.unwrapWeakref(self._client)

    def getMethod(self):
        '''
        Returns the string of the method that was used to generate this
        Stream.  Note that it's identical to the property derivationMethod on a
        Stream, so no need for any but the most advanced usages.

        >>> s = stream.Stream()
        >>> s.derivationMethod is s._derivation.getMethod()
        True
        >>> s.derivationMethod is None
        True
        >>> sNotes = s.notes
        >>> sNotes.derivationMethod
        'notes'
        >>> sNotes._derivation.getMethod()
        'notes'
        '''
        return self._method

    def getOrigin(self):
        return self._origin
        #return common.unwrapWeakref(self._origin)

    def setClient(self, client):
        # client is the Stream that this derivation lives on
        if client is None:
            self._clientId = None
            self._client = None
        else:
            self._clientId = id(client)
            self._client = common.wrapWeakref(client)

    def setMethod(self, method):
        '''
        Sets a string identifying how the object was derived.

        Some examples are 'getElementsByClass' etc.

        >>> s = stream.Stream()
        >>> s.append(clef.TrebleClef())
        >>> s.append(note.Note())
        >>> sNotes = s.notes
        >>> sNotes._derivation
        <music21.derivation.Derivation object at 0x...>

        >>> derived = sNotes._derivation
        >>> derived.getMethod()
        'notes'
        >>> derived.setMethod('blah')
        >>> derived.getMethod()
        'blah'
        >>> sNotes.derivationMethod
        'blah'
        '''
        self._method = method

    def setOrigin(self, origin):
        # for now, origin is not a weak ref
        if origin is None:
            self._originId = None
            self._origin = None
        else:
            self._originId = id(origin)
            self._origin = origin
            #self._origin = common.wrapWeakref(origin)

    def unwrapWeakref(self):
        '''
        Unwrap any and all weakrefs stored.

        Necessary for pickling operations.

        ::

            >>> s1 = stream.Stream()
            >>> s2 = stream.Stream()
            >>> d1 = derivation.Derivation(s1) # sets client
            >>> d1.setOrigin(s2)
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

    def wrapWeakref(self):
        '''Wrap all stored objects with weakrefs.
        '''
        if not common.isWeakref(self._client):
            # update id in case it has changed
            self._clientId = id(self._client)
            post = common.wrapWeakref(self._client)
            self._client = post


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
