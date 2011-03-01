#-------------------------------------------------------------------------------
# Name:         derivation.py
# Purpose:      Class for storing and managing Stream-based derivations
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''This module defines objects for tracking the derivation of one :class:`~music21.stream.Stream` from another.
'''

import doctest, unittest

import music21
from music21 import common
# imported by stream


class Derivation(object):
    '''
    >>> from music21 import *  
    >>> d = derivation.Derivation()
    >>> s = stream.Stream()
    >>> d.setAncestor(s)
    >>> d.getAncestor() is s
    True    
    '''
    def __init__(self, container=None):
        # store a reference to the Stream that contains this derivation
        self.container = container
        # ancestor should probably be stored as a weak ref
        self._ancestor = None
        self._ancestorId = None # store id to optimize w/o unwrapping

    def setAncestor(self, ancestor):
        if ancestor is None:
            self._ancestorId = None
            self._ancestor = None
        else:
            self._ancestorId = id(ancestor)
            self._ancestor = common.wrapWeakref(ancestor)

    def getAncestor(self):
        return common.unwrapWeakref(self._ancestor)

    def __deepcopy__(self, memo=None):
        '''Manage deepcopying by creating a new reference to the same object. If the ancestor no longer exists, than ancestor is set to None
        '''
        new = self.__class__()
        new.setAncestor(self.getAncestor())
        return new




#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []



if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()


#------------------------------------------------------------------------------
# eof







