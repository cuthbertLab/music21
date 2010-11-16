#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         spanner.py
# Purpose:      The Spanner base-class and subclasses
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest

import music21
from music21 import common

from music21 import environment
_MOD = "spanners.py"  
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class Component(object):
    '''
    Object model that wraps a Music21Object stored in a spanner.
    '''
    def __init__(self, component=None):
        self._id = None # id() of stored object
        self._ref = None # weak ref to stored object

        # Spanner subclasses might define attributes, like weights
        if component is not None:    
            self.set(component)


    def set(self, component):
        self._id = id(component)
        self._ref = common.wrapWeakref(component)

    def get(self):
        return common.unwrapWeakref(self._ref)



class SpannerException(Exception):
    pass


class Spanner(music21.Music21Object):
    '''
    Spanner objects live on Streams as other Music21Objects, but store connections between one or more Music21Objects.
    '''
    # store a spanners object as a class instance; 
    # this assures that only one will be created for all subclasses
    # each instances shares a single
    # storage dictionary and wraps all components in weak refs
    

    def __init__(self, *arguments, **keywords):
        music21.Music21Object.__init__(self)

        # an ordered list of Component objects
        self._components = []

        # add any provided arguments
        if len(arguments) > 1:
            self.addComponents(arguments)
        elif len(arguments) == 1: # assume a list is first arg
            self.addComponents(arguments[0])


    def getComponents(self):
        '''Return all components for this Spanner. 
        '''
        post = []
        for c in self._components:
            q = c.get()
            if q != None:
                post.append(q)

        if post == []:
            return None
        else:
            return post


    def addComponents(self, components):  
        '''Associate one or more components with this Spanner.
        '''  
        # presently, this does not look for redundancies
        if not common.isListLike(components):
            components = [components]
        for c in components:
            # create a component instance for each
            self._components.append(Component(c))

#     def __del__(self):
#         '''On deletion, remove this reference from Spanners.
#         '''
#         self._spanners.remove(self)
# 



#-------------------------------------------------------------------------------
# connect two or more notes anywhere in the score
class Slur(Spanner):
    pass

# crescendo
class Crescendo(Spanner):
    pass


# associate two or more notes to be beamed together
# use a stored time signature to apply beaming values 
class BeamingGroup(Spanner):
    pass


# first/second repeat bracket
class RepeatBracket(Spanner):
    pass




# association of staffs
# designates bracket or brace or combination of many
class StaffGroup(Spanner):
    pass




# optionally define one or more Streams as a staff
# provide settings for staff presentation such as number lines
# presentation of part name?
class Staff(Spanner):
    pass

# 2 parts in on staff
# 1 parts w/ staves


# collection of measures within a Score
class System(Spanner):
    pass


# association of all measures or streams on a page
class Page(Spanner):
    pass



#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testBasic(self):

        # how parts might be grouped
        from music21 import stream, spanner, note
        s = stream.Score()
        p1 = stream.Part()
        p2 = stream.Part()

        sg1 = StaffGroup(p1, p2)

        # place all on Stream
        s.insert(0, p1)
        s.insert(0, p2)
        s.insert(0, sg1)    

        self.assertEqual(len(s), 3)
        self.assertEqual(sg1.getComponents(), [p1, p2])
        # make sure spanners is unified

        # how slurs might be defined
        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()
        p1.append(n1)
        p1.append(n2)
        p1.append(n3)

        slur1 = Slur()
        slur1.addComponents([n1, n3])

        p1.append(slur1)

        self.assertEqual(len(s), 3)
        self.assertEqual(slur1.getComponents(), [n1, n3])


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





