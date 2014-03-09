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
        >>> d1.setAncestor(s2)
        >>> d1.getAncestor() is s2
        True

    ::

        >>> d1.getContainer() is s1
        True

    ::

        >>> d2 = copy.deepcopy(d1)
        >>> d2.getAncestor() is s2
        True

    ::

        >>> d1.setMethod('measure')
        >>> d1.getMethod()
        'measure'

    '''

    ### CLASS VARIABLES ###

    __slots__ = (
        '_ancestor',
        '_ancestorId',
        '_container',
        '_containerId',
        '_method',
        )

    ### INITIALIZER ###

    def __init__(self, container=None):
        # store a reference to the Stream that has this Derivation object as a property
        self._container = None
        self._containerId = None  # store id to optimize w/o unwrapping
        self._method = None
        # ancestor should be stored as a weak ref
        self._ancestor = None
        self._ancestorId = None  # store id to optimize w/o unwrapping
        # set container; can handle None
        self.setContainer(container)

    ### SPECIAL METHODS ###

    def __deepcopy__(self, memo=None):
        '''
        Manage deepcopying by creating a new reference to the same object. If
        the ancestor no longer exists, than ancestor is set to None
        '''
        new = self.__class__()
        new.setContainer(self.getContainer())
        new.setAncestor(self.getAncestor())
        return new

    ### PUBLIC METHODS ###

    def getAncestor(self):
        return self._ancestor
        #return common.unwrapWeakref(self._ancestor)

    def getContainer(self):
        return common.unwrapWeakref(self._container)

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

    def setAncestor(self, ancestor):
        # for now, ancestor is not a weak ref
        if ancestor is None:
            self._ancestorId = None
            self._ancestor = None
        else:
            self._ancestorId = id(ancestor)
            self._ancestor = ancestor
            #self._ancestor = common.wrapWeakref(ancestor)

    def setContainer(self, container):
        # container is the Stream that this derivation lives on
        if container is None:
            self._containerId = None
            self._container = None
        else:
            self._containerId = id(container)
            self._container = common.wrapWeakref(container)

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

    def unwrapWeakref(self):
        '''
        Unwrap any and all weakrefs stored.

        ::

            >>> s1 = stream.Stream()
            >>> s2 = stream.Stream()
            >>> d1 = derivation.Derivation(s1) # sets container
            >>> d1.setAncestor(s2)
            >>> common.isWeakref(d1._container)
            True

        ::

            >>> d1.unwrapWeakref()
            >>> common.isWeakref(d1._container)
            False

        '''
        #environLocal.printDebug(['derivation pre unwrap: self._container', self._container])
        post = common.unwrapWeakref(self._container)
        self._container = post
        #environLocal.printDebug(['derivation post unwrap: self._container', self._container])

    def wrapWeakref(self):
        '''Wrap all stored objects with weakrefs.
        '''
        if not common.isWeakref(self._container):
            # update id in case it has changed
            self._containerId = id(self._container)
            post = common.wrapWeakref(self._container)
            self._container = post


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
