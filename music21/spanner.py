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


        # each component may define and offset in quarterLengths
        # to suggest positioning not exactly with the component
        self.offset = 0.0

        # Spanner subclasses might define attributes, like weights
        if component is not None:    
            self.set(component)


    def set(self, component):
        self._id = id(component)
        self._ref = common.wrapWeakref(component)

    def get(self):
        return common.unwrapWeakref(self._ref)

    # for serialization, need to wrap and unwrap weakrefs
    def freezeIds(self):
        pass

    def unfreezeIds(self):
        pass


class SpannerException(Exception):
    pass



# calculating the duration of components, or even that start of components
# from within the spanner is very hard: the problem is that we do not know 
# what site of the component to use: it may be the parent, it may be otherwise
# we may have a slur to two notes that do not have a common parent

# but: if we store a weakref to the site, we can always be sure to get the 
# the right offset

# however, if the site is a measure, the offset will be relative to that measure; for a spanner that spans two measures, offset values will be irrelevant

# thus, we cannot get any offset information unless the components share
# all sites

# linking the offset of the Spanner itself to its components is also problematic: when adding a component, we do not know what site is relevant for determining offset. we also cannot be sure that the Spanner will live in the same container as the component. we also have to override all defined contexts operations on the Spanner; and we still cannot be sure what site is relevant to the component to figure out what the offset of the spanner is.

# thus, Spanner objects should be naive. 

class Spanner(music21.Music21Object):
    '''
    Spanner objects live on Streams as other Music21Objects, but store connections between one or more Music21Objects.
    '''
    

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


    def getOffsetsBySite(self, site, componentOffset=True):
        '''Given a site shared by all components, return a list of offset values.

        To include `componentOffset` adjustments, set this value to True.
        '''
        post = []
        idSite = id(site)
        for c in self.getComponents():
            # getting site ids is fast, as weakrefs do not have to be unpacked
            if idSite in c.getSiteIds():
                o = c.getOffsetBySite(site)
                if componentOffset:
                    post.append(o+c.offset)
                else:    
                    post.append(o)
        return post

    def getOffsetSpanBySite(self, site, componentOffset=True):
        '''Return the span, or min and max values, of all offsets for a given site. 
        '''
        post = self.getOffsetsBySite(site, componentOffset=componentOffset)
        return [min(post), max(post)]


#-------------------------------------------------------------------------------
# connect two or more notes anywhere in the score
class Slur(Spanner):

    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)



    



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
        self.assertEqual(sg1.getOffsetsBySite(s), [0.0, 0.0])

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

        self.assertEqual(slur1.getOffsetsBySite(p1), [0.0, 4.0])
        self.assertEqual(slur1.getOffsetSpanBySite(p1), [0.0, 4.0])


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





