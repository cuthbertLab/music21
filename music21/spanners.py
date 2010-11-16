#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         spanners.py
# Purpose:      Storage and utilities for non-hierarchical object connections
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Management of objects across and between hierarchical organization. 
'''
import unittest

import music21
from music21 import common

from music21 import environment
_MOD = "spanners.py"  
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
# bass classes

# based on models here:
# http://code.activestate.com/recipes/66531/
# http://stackoverflow.com/questions/31875/is-there-a-simple-elegant-way-to-define-singletons-in-python

# note that both Borg and Singleton pass all present tests and likely exhibit
# the same functionality for the design here.

# class Singleton(object):
#     def __new__(type):
#         if not '_the_instance' in type.__dict__:
#             type._the_instance = object.__new__(type)
#         return type._the_instance


class Borg(object):
    _state = {}
    def __new__(cls, *p, **k):
        self = object.__new__(cls, *p, **k)
        self.__dict__ = cls._state
        return self


#-------------------------------------------------------------------------------
# bass classes

class SpannersException(Exception):
    pass


class Spanners(Borg):
    '''
    A storage class for all spanners. 

    This class is an implementation of a Borg/Singleton pattern, and thus many instances will share the same state. 
    '''


    def __init__(self):

        # store a dictionary of id(spanner): (spanner, list of components)
        # ex: id(Slur): Slur, [Note, Note]
        # ex: id(Crescendo): Crescendo, [Note, Note]
        # ex: id(Bracket): Bracket, [Part, Part, Part]
        self._storage = {}

        # store a dictionary of id(spanner): list of component spanners
        # this provides quick reference to permit finding a spanner from
        # component without unwrapping
        self._idRef = {}


    def keys(self):
        '''Return all keys, or id() values of spanner objects.
        '''
        return self._storage.keys()

    def __len__(self):
        return len(self._storage.keys())


    def add(self, spanner, component):
        '''Add a spanner and one or more component references.

        The `spanner` is the object represent the connections, such as a Slur or GroupBracket.

        The `component` is one or more (a list) objects, such as Note or Part.
        
        If the spanner already exists, the component will be added to the components list.


        >>> from music21 import *
        >>> class TestMock(object): pass
        >>> tm1 = TestMock()
        >>> n1 = note.Note('c2')
        >>> n2 = note.Note('g3')
        >>> sp1 = Spanners()
        >>> sp1.add(tm1, [n1, n2])
        >>> len(sp1)
        1
        '''
        idSpanner = id(spanner)
        if idSpanner not in self.keys():
            self._storage[idSpanner] = (common.wrapWeakref(spanner), [])
            self._idRef[idSpanner] = [] # just a list

        refPair = self._storage[idSpanner]
        idList = self._idRef[idSpanner]

        # presently this does not look for redundant entries
        # store component as weak ref
        if common.isListLike(component):
            bundle = component
        else: # just append one
            bundle = [component]

        for sub in bundle: # permit a lost of spanners
            refPair[1].append(common.wrapWeakref(sub))
            idList.append(id(sub))




    def getComponents(self, spanner):
        '''Given a spanner defined in this Spanners, return a list of associated components. 

        Components, while stored as weakrefs, are unwrapped.

        >>> from music21 import *
        >>> class TestMock(object): pass
        >>> tm1 = TestMock()
        >>> n1 = note.Note('c2')
        >>> n2 = note.Note('g3')
        >>> sp1 = Spanners()
        >>> sp1.add(tm1, [n1, n2])
        >>> sp1.getComponents(tm1) == [n1, n2]
        True
        '''
        idSpanner = id(spanner)
        if idSpanner not in self.keys():
            raise SpannersException('cannot return comoponents from an object not defined in spanners: %s' % repr(spanner))

        post = []
        # get all objects, unwrap
        # second index is list of components
        for wr in self._storage[idSpanner][1]:
            post.append(common.unwrapWeakref(wr))
        return post



    def getSpanner(self, component):
        '''Given a component, return a list of all spanner objects that bundle that component.

        >>> from music21 import *
        >>> class TestMock(object): pass
        >>> tm1 = TestMock()
        >>> n1 = note.Note('c2')
        >>> n2 = note.Note('g3')
        >>> sp1 = Spanners()
        >>> sp1.add(tm1, [n1, n2])
        >>> sp1.getSpanner(n2) == [tm1]
        True
        '''
        idComponent = id(component)
        # find all keys
        spannerKeys = []
        for key in self.keys():
            # look at all component ids
            for idKnown in self._idRef[key]:
                if idKnown == idComponent:
                    spannerKeys.append(key)
                    break
        # unwrap spanner for found keys
        post = []
        for key in spannerKeys:
            # first index is spanner object
            post.append(common.unwrapWeakref(self._storage[key][0]))

        return post



    def remove(self, spanner):
        '''Given a spanner, remove it from the stored collection.
        '''
        idSpanner = id(spanner)
        if idSpanner not in self.keys():
            raise SpannersException('this spanner is not defined in the _storage references: %s' % repr(spanner))
        del self._storage[idSpanner]



#-------------------------------------------------------------------------------

class TestMock(object): pass

class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testWeakref(self):
        from music21 import note
        n = note.Note()
        idStored = id(n)
        wn = common.wrapWeakref(n)
        n2 = common.unwrapWeakref(n)
        self.assertEqual(id(n), id(n2))



    def testSpannersA(self):
        from music21 import note, stream

        tm1 = TestMock()
        n1 = note.Note('c2')
        n2 = note.Note('g3')

        tm2 = TestMock()
        p1 = stream.Part()
        p2 = stream.Part()
        p3 = stream.Part()

        tm3 = TestMock()


        sp1 = Spanners()
        sp2 = Spanners()

        # different instances
        self.assertEqual(id(sp1) != id(sp2), True)
        # but common storage
        self.assertEqual(id(sp1._storage) == id(sp2._storage), True)

        sp1.add(tm1, n1)
        self.assertEqual(len(sp1), 1)
        # second instances has state of first
        self.assertEqual(len(sp2), 1)

        sp2.add(tm1, n2)
        self.assertEqual(len(sp1), 1)
        self.assertEqual(len(sp2), 1)

        # both instances can get objects
        self.assertEqual(str(sp1.getComponents(tm1)), '[<music21.note.Note C>, <music21.note.Note G>]')
        self.assertEqual(str(sp2.getComponents(tm1)), '[<music21.note.Note C>, <music21.note.Note G>]')

        sp1.add(tm2, (p1, p2, p3))
        self.assertEqual(len(sp1), 2)
        self.assertEqual(len(sp2), 2)


        # test getting the components given a spanner
        self.assertEqual(len(sp1.getComponents(tm2)), 3)
        self.assertEqual(len(sp2.getComponents(tm2)), 3)

        self.assertEqual(sp1.getComponents(tm2)[0], p1)
        self.assertEqual(sp1.getComponents(tm2)[1], p2)
        self.assertEqual(sp1.getComponents(tm2)[2], p3)
        self.assertEqual(sp2.getComponents(tm2)[0], p1)
        self.assertEqual(sp2.getComponents(tm2)[1], p2)
        self.assertEqual(sp2.getComponents(tm2)[2], p3)


        # test getting the spanner with a component
        self.assertEqual(sp1.getSpanner(n1), [tm1])
        self.assertEqual(sp1.getSpanner(n2), [tm1])
        self.assertEqual(sp2.getSpanner(n1), [tm1])
        self.assertEqual(sp2.getSpanner(n2), [tm1])

        self.assertEqual(sp1.getSpanner(p1), [tm2])
        self.assertEqual(sp2.getSpanner(p1), [tm2])
        self.assertEqual(sp1.getSpanner(p2), [tm2])
        self.assertEqual(sp2.getSpanner(p2), [tm2])
        self.assertEqual(sp1.getSpanner(p3), [tm2])
        self.assertEqual(sp2.getSpanner(p3), [tm2])


        # create a mixed collection
        sp1.add(tm3, [n1, p1, n2, p2])
        self.assertEqual(len(sp2), 3)

        self.assertEqual(sp1.getSpanner(n1), [tm1, tm3])
        self.assertEqual(sp1.getSpanner(p1), [tm2, tm3])
        self.assertEqual(sp2.getSpanner(n1), [tm1, tm3])
        self.assertEqual(sp2.getSpanner(p1), [tm2, tm3])


        sp2.remove(tm2)
        self.assertEqual(len(sp1), 2)
        self.assertEqual(len(sp2), 2)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()





#------------------------------------------------------------------------------
# eof

