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
        self.id = None # id() of stored object
        self._ref = None # weak ref to stored object


        # each component may define and offset in quarterLengths
        # to suggest positioning not exactly with the component
        self.offset = 0.0

        # Spanner subclasses might define attributes, like weights
        if component is not None:    
            self.set(component)


    def set(self, component):
        self.id = id(component)
        self._ref = common.wrapWeakref(component)

    def getComponents(self):
        return common.unwrapWeakref(self._ref)

    # for serialization, need to wrap and unwrap weakrefs
    def freezeIds(self):
        pass

    def unfreezeIds(self):
        pass


    def __deepcopy__(self, memo=None):
        '''Manage deepcopying by creating a new reference.
        '''
        new = self.__class__()
        new.set(self.getComponents())
        new.offset = self.offset
        return new


class SpannerException(Exception):
    pass



# calculating the duration of components, or even that start of components
# from within the spanner is very hard: the problem is that we do not know 
# what site of the component to use: it may be the parent, it may be otherwise
# we may have a slur to two notes that do not have a common parent

# but: if we store a weakref to the site, we can always be sure to getComponents the 
# the right offset

# however, if the site is a measure, the offset will be relative to that measure; for a spanner that spans two measures, offset values will be irrelevant

# thus, we cannot getComponents any offset information unless the components share
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

        # store this so subclasses can replace
        self._reprHead = '<music21.spanner.Spanner '

        # addComponents any provided arguments
        if len(arguments) > 1:
            self.addComponents(arguments)
        elif len(arguments) == 1: # assume a list is first arg
            self.addComponents(arguments[0])

        # parameters that spanners need in loading and processing
        # local id is the id for the local area; used by musicxml
        self.idLocal = None
        # after all components have been gathered, setting complete
        # will mark that all parts have been gathered. 
        self.completeStatus = False

    
    def __repr__(self):
        msg = [self._reprHead]
        for obj in self.getComponents():
            msg.append(repr(obj))
        msg.append('>')
        return ''.join(msg)


    def getComponents(self):
        '''Return all components for this Spanner. 

        As this is a Music21Object, the name here is more specific to avoid name clashes.

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> sl = spanner.Slur()
        >>> sl.addComponents(n1)
        >>> sl.getComponents() == [n1]
        True
        >>> sl.addComponents(n2)
        >>> sl.getComponents() == [n1, n2]
        True
        >>> sl.getComponentIds() == [id(n1), id(n2)]
        True
        >>> sl
        <music21.spanner.Slur <music21.note.Note G><music21.note.Note F#>>

        '''
        post = []
        for c in self._components:
            q = c.getComponents() # unwrap weakreference
            if q != None:
                post.append(q)
        return post


    def getComponentIds(self):
        '''Return all id() for all stored objects.

        '''
        # this does not unwrap weakrefs, but simply gets the stored id 
        # from the Component object
        post = []
        for c in self._components:
            q = c.id # weakref may be dead!
            if q != None:
                post.append(q)
        return post

    def addComponents(self, components, *arguments, **keywords):  
        '''Associate one or more components with this Spanner.

        The order that components is added is retained and may or may not be significant to the spanner. 

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Slur()
        >>> sl.addComponents(n1)
        >>> sl.addComponents(n2, n3)
        >>> sl.addComponents([n4, n5])
        >>> sl.getComponentIds() == [id(n) for n in [n1, n2, n3, n4, n5]]
        True

        '''  
        # presently, this does not look for redundancies
        if not common.isListLike(components):
            components = [components]
        # assume all other arguments
        components += arguments
        for c in components:
            # create a component instance for each
            self._components.append(Component(c))

#     def __del__(self):
#         '''On deletion, remove this reference from Spanners.
#         '''
#         self._spanners.remove(self)
# 

    def isFirst(self, component):
        '''Given a component, is it first?

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Slur()
        >>> sl.addComponents(n1, n2, n3, n4, n5)
        >>> sl.isFirst(n2)
        False
        >>> sl.isFirst(n1)
        True
        >>> sl.isLast(n1)
        False
        >>> sl.isLast(n5)
        True

        '''
        idTarget = id(component)
        if self._components[0].id == idTarget:
            return True
        return False

    def isLast(self, component):
        '''Given a component, is it last?
        '''
        idTarget = id(component)
        if self._components[-1].id == idTarget:
            return True
        return False


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
class SpannerBundle(object):
    '''A utility object for collecting and processing collections of Spanner objects.

    If a Stream or Stream subclass is provided as an argument, all Spanners on this Stream will be accumulated herein. 
    '''

    def __init__(self, *arguments, **keywords):
        self._storage = []

        for arg in arguments:
            if 'Stream' in arg.classes:
                for e in arg.spanners:
                    self._storage.append(e)


    def append(self, other):
        self._storage.append(other)

    def __len__(self):
        '''
        '''
        return len(self._storage)

    def __iter__(self):
        return self._storage.__iter__()

    def __getitem__(self, key):
        return self._storage[key]

    def __repr__(self):
        return '<music21.spanner.SpannerBundle of size %s>' % self.__len__()

    def asList(self):
        '''Return the bundle as a list.
        '''
        post = []
        for x in self._storage:
            post.append(x)
        return post

    def getByIdLocal(self, idLocal=None):
        '''Get spanners by `idLocal` or `complete` status.

        Returns a new SpannerBundle object

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su1.idLocal = 1
        >>> su2 = spanner.Slur()
        >>> su2.idLocal = 2
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> len(sb)
        2
        >>> len(sb.getByIdLocal(1))
        1
        >>> len(sb.getByIdLocal(2))
        1
        '''
        post = self.__class__()
        for sp in self._storage:
            if sp.idLocal == idLocal:
                post.append(sp)
        return post

    def getByCompleteStatus(self, completeStatus):
        '''Get spanners by matching status of `completeStatus` to the same attribute

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su1.idLocal = 1
        >>> su1.completeStatus = True
        >>> su2 = spanner.Slur()
        >>> su2.idLocal = 2
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb2 = sb.getByCompleteStatus(True)
        >>> len(sb2)
        1
        >>> sb2 = sb.getByIdLocal(1).getByCompleteStatus(True)
        >>> sb2[0] == su1
        True
        '''
        post = self.__class__()
        for sp in self._storage:
            if sp.completeStatus == completeStatus:
                post.append(sp)
        return post


    def getByComponent(self, component):
        '''Given a spanner component (an object), return a bundle of all Spanner objects that have this object as a component. 

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> n2 = note.Note()
        >>> n3 = note.Note()
        >>> su1 = spanner.Slur(n1, n2)
        >>> su2 = spanner.Slur(n2, n3)
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.getByComponent(n1).asList() == [su1]
        True
        >>> sb.getByComponent(n3).asList() == [su2]
        True
        >>> sb.getByComponent(n2).asList() == [su1, su2]
        True
        '''
        idTarget = id(component)
        post = self.__class__()
        for sp in self._storage:
            if idTarget in sp.getComponentIds():
                post.append(sp)
        return post



    def getByClass(self, className):
        '''Given a spanner class, return a bundle of all Spanners of the desired class. 

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su2 = spanner.StaffGroup()
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.getByClass(spanner.Slur).asList() == [su1]
        True
        >>> sb.getByClass('Slur').asList() == [su1]
        True
        >>> sb.getByClass('StaffGroup').asList() == [su2]
        True
        '''
        post = self.__class__()
        for sp in self._storage:
            if common.isStr(className):
                if className in sp.classes:
                    post.append(sp)
            else:
                if isinstance(sp, className):
                    post.append(sp)
        return post





#-------------------------------------------------------------------------------
# connect two or more notes anywhere in the score
class Slur(Spanner):

    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self.placement = None # can above or below, after musicxml

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Slur ')
        return msg
    



# crescendo
class DynamicWedge(Spanner):
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



    def testSpannerBundle(self):
        from music21 import spanner, stream

        su1 = spanner.Slur()
        su1.idLocal = 1
        su2 = spanner.Slur()
        su2.idLocal = 2
        sb = spanner.SpannerBundle()
        sb.append(su1)
        sb.append(su2)
        self.assertEqual(len(sb), 2)
        self.assertEqual(sb[0], su1)
        self.assertEqual(sb[1], su2)

        su3 = spanner.Slur()
        su4 = spanner.Slur()

        s = stream.Stream()
        s.append(su3)
        s.append(su4)
        sb2 = spanner.SpannerBundle(s)
        self.assertEqual(len(sb2), 2)
        self.assertEqual(sb2[0], su3)
        self.assertEqual(sb2[1], su4)


    def testDeepcopySpanner(self):
        from music21 import spanner, note
        import copy

        # how slurs might be defined
        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()

        su1 = Slur()
        su1.addComponents([n1, n3])

        su2 = copy.deepcopy(su1)

        self.assertEqual(su1.getComponents(), [n1, n3])
        self.assertEqual(su2.getComponents(), [n1, n3])

        

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





