# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         derivation.py
# Purpose:      Class for storing and managing Stream-based derivations
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''This module defines objects for tracking the derivation of one :class:`~music21.stream.Stream` from another.
'''

import doctest, unittest

import music21
from music21 import common
# imported by stream

from music21 import environment
_MOD = "derivation.py"
environLocal = environment.Environment(_MOD)



class Derivation(music21.JSONSerializer):
    '''
    >>> import copy
    >>> from music21 import *  
    >>> s1 = stream.Stream()
    >>> s2 = stream.Stream()
    >>> d1 = derivation.Derivation(s1)
    >>> d1.setAncestor(s2)
    >>> d1.getAncestor() is s2
    True    
    >>> d1.getContainer() is s1
    True    
    >>> d2 = copy.deepcopy(d1)
    >>> d2.getAncestor() is s2
    True
    >>> d1.setMethod('measure')
    >>> d1.getMethod()
    'measure'
    '''
    def __init__(self, container=None):
        music21.JSONSerializer.__init__(self)

        # store a reference to the Stream that contains this derivation
        self._container = None
        self._containerId = None # store id to optimize w/o unwrapping
        self._method = None
        # ancestor should be stored as a weak ref
        self._ancestor = None
        self._ancestorId = None # store id to optimize w/o unwrapping

        # set container; can handle None
        self.setContainer(container)

    def setContainer(self, container):
        # container is the Stream that contains
        if container is None:
            self._containerId = None
            self._container = None
        else:
            self._containerId = id(container)
            self._container = common.wrapWeakref(container)

    def getContainer(self):
        return common.unwrapWeakref(self._container)

    def setAncestor(self, ancestor):
        # for now, ancestor is not a weak ref        
        if ancestor is None:
            self._ancestorId = None
            self._ancestor = None
        else:
            self._ancestorId = id(ancestor)
            self._ancestor = ancestor
            #self._ancestor = common.wrapWeakref(ancestor)

    def getAncestor(self):
        return self._ancestor
        #return common.unwrapWeakref(self._ancestor)

    def setMethod(self, method):
        '''
        sets a string identifying how the object was derived
        '''
        self._method = method

    def getMethod(self):
        return self._method


    def __deepcopy__(self, memo=None):
        '''Manage deepcopying by creating a new reference to the same object. If the ancestor no longer exists, than ancestor is set to None
        '''
        new = self.__class__()
        new.setContainer(self.getContainer())
        new.setAncestor(self.getAncestor())
        return new


    def unwrapWeakref(self):
        '''Unwrap any and all weakrefs stored.

        >>> from music21 import *  
        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> d1 = derivation.Derivation(s1) # sets container
        >>> d1.setAncestor(s2)
        >>> common.isWeakref(d1._container)
        True
        >>> d1.unwrapWeakref()
        >>> common.isWeakref(d1._container)
        False
        '''
        #environLocal.pd(['derivation pre unwrap: self._container', self._container])
        post = common.unwrapWeakref(self._container)
        self._container = post
        #environLocal.pd(['derivation post unwrap: self._container', self._container])

    def wrapWeakref(self):
        '''Wrap all stored objects with weakrefs.
        '''
        if not common.isWeakref(self._container):
            # update id in case it has changed
            self._containerId = id(self._container) 
            post = common.wrapWeakref(self._container)
            self._container = post



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testSerializationA(self):
        from music21 import derivation

        d = derivation.Derivation()
        self.assertEqual(d.jsonAttributes(), ['_ancestor', '_ancestorId', '_container', '_containerId', '_method'])

        self.assertEqual(hasattr(d, 'json'), True)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []



if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof








