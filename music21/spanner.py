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

    def get(self):
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
        new.set(self.get())
        new.offset = self.offset
        return new


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
            self.add(arguments)
        elif len(arguments) == 1: # assume a list is first arg
            self.add(arguments[0])

        # parameters that spanners need in loading and processing
        # local id is the id for the local area; used by musicxml
        self.idLocal = None
        # after all components have been gathered, setting complete
        # will mark that all parts have been gathered. 
        self.completeStatus = False

    
    def __repr__(self):
        msg = ['<music21.spanner.Spanner ']
        for obj in self.get():
            msg.append(repr(obj))
        msg.append('>')
        return ''.join(msg)


    def get(self):
        '''Return all components for this Spanner. 

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> sl = spanner.Slur()
        >>> sl.add(n1)
        >>> sl.get() == [n1]
        True
        >>> sl.add(n2)
        >>> sl.get() == [n1, n2]
        True
        >>> sl.getIds() == [id(n1), id(n2)]
        True
        >>> sl
        <music21.spanner.Slur <music21.note.Note G><music21.note.Note F#>>

        '''
        post = []
        for c in self._components:
            q = c.get() # unwrap weakreference
            if q != None:
                post.append(q)
        return post


    def getIds(self):
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

        

    def add(self, components, *arguments, **keywords):  
        '''Associate one or more components with this Spanner.

        The order that components is added is retained and may or may not be significant to the spanner. 

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Slur()
        >>> sl.add(n1)
        >>> sl.add(n2, n3)
        >>> sl.add([n4, n5])
        >>> sl.getIds() == [id(n) for n in [n1, n2, n3, n4, n5]]
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


    def getOffsetsBySite(self, site, componentOffset=True):
        '''Given a site shared by all components, return a list of offset values.

        To include `componentOffset` adjustments, set this value to True.
        '''
        post = []
        idSite = id(site)
        for c in self.get():
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
    '''A utility object for collecting and processing spannerin spanner creation and manipulation.
    '''

    def __init__(self):
        self._storage = []

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
        '''Get spanners by matchinging object id

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




#-------------------------------------------------------------------------------
# connect two or more notes anywhere in the score
class Slur(Spanner):

    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace('<music21.spanner.Spanner ', '<music21.spanner.Slur ')
        return msg
    



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
        self.assertEqual(sg1.get(), [p1, p2])
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
        slur1.add([n1, n3])

        p1.append(slur1)

        self.assertEqual(len(s), 3)
        self.assertEqual(slur1.get(), [n1, n3])

        self.assertEqual(slur1.getOffsetsBySite(p1), [0.0, 4.0])
        self.assertEqual(slur1.getOffsetSpanBySite(p1), [0.0, 4.0])



    def testSpannerBundle(self):
        from music21 import spanner

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


    def testDeepcopySpanner(self):
        from music21 import spanner, note
        import copy

        # how slurs might be defined
        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()

        su1 = Slur()
        su1.add([n1, n3])

        su2 = copy.deepcopy(su1)

        self.assertEqual(su1.get(), [n1, n3])
        self.assertEqual(su2.get(), [n1, n3])


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





