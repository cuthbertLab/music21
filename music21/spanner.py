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
import copy

import music21
from music21 import common
from music21 import duration

from music21 import environment
_MOD = "spanner.py"  
environLocal = environment.Environment(_MOD)







#-------------------------------------------------------------------------------
# this object was used to weak-ref wrap objects stored in a Spanner
# this is not presently in use, as the new Spanner stores objects in a Stream

# class Component(object):
#     '''
#     Object model that wraps a Music21Object stored in a spanner.
#     '''
#     def __init__(self, component=None):
#         self.id = None # id() of stored object
#         self._ref = None # weak ref to stored object
# 
#         # each component may define and offset in quarterLengths
#         # to suggest positioning not exactly with the component
#         self.offset = 0.0
# 
#         # Spanner subclasses might define attributes, like weights
#         if component is not None:    
#             self.set(component)
# 
# 
#     def set(self, component):
#         self.id = id(component)
#         self._ref = common.wrapWeakref(component)
# 
#     def get(self):
#         return common.unwrapWeakref(self._ref)
# 
#     # for serialization, need to wrap and unwrap weakrefs
#     def freezeIds(self):
#         pass
# 
#     def unfreezeIds(self):
#         pass
# 
# 
#     def __deepcopy__(self, memo=None):
#         '''Manage deepcopying by creating a new reference to the same object.
#         '''
#         new = self.__class__()
#         new.set(self.get())
#         new.offset = self.offset
#         return new




# calculating the duration of components, or even the start of components
# from within the spanner is very hard: the problem is that we do not know 
# what site of the component to use: it may be the activeSite, it may be otherwise
# we may have a slur to two notes that do not have a common activeSite

# but: if we store a weakref to the site, we can always be sure to getComponents the 
# the right offset

# however, if the site is a measure, the offset will be relative to that measure; for a spanner that spans two measures, offset values will be irrelevant

# thus, we cannot getComponents any offset information unless the components share
# all sites

# linking the offset of the Spanner itself to its components is also problematic: when adding a component, we do not know what site is relevant for determining offset. we also cannot be sure that the Spanner will live in the same container as the component. we also have to override all defined contexts operations on the Spanner; and we still cannot be sure what site is relevant to the component to figure out what the offset of the spanner is.

# thus, Spanner objects should be naive. 

# class Spanner(music21.Music21Object):
#     '''
#     Spanner objects live on Streams as other Music21Objects, but store connections between one or more Music21Objects.
#     '''
#     
#     # possible replace Component with WeakElementWrapper
#     # store a Stream in Spanner, and map relevant methods to public 
#     # interface of Spanner
# 
# 
#     def __init__(self, *arguments, **keywords):
#         music21.Music21Object.__init__(self)
# 
#         # an ordered list of Component objects
#         self._components = []
# 
#         # store this so subclasses can replace
#         self._reprHead = '<music21.spanner.Spanner '
# 
#         # addComponents any provided arguments
#         if len(arguments) > 1:
#             self.addComponents(arguments)
#         elif len(arguments) == 1: # assume a list is first arg
#             self.addComponents(arguments[0])
# 
#         # parameters that spanners need in loading and processing
#         # local id is the id for the local area; used by musicxml
#         self.idLocal = None
#         # after all components have been gathered, setting complete
#         # will mark that all parts have been gathered. 
#         self.completeStatus = False
# 
#     
#     def __repr__(self):
#         msg = [self._reprHead]
#         for obj in self.getComponents():
#             msg.append(repr(obj))
#         msg.append('>')
#         return ''.join(msg)
# 
# 
#     def __getitem__(self, key):
#         return self._components[key]
# 
#     def getComponents(self):
#         '''Return all components for this Spanner as objects, without weak-refs.  
# 
#         As this is a Music21Object, the name here is more specific to avoid name clashes.
# 
#         >>> from music21 import *
#         >>> n1 = note.Note('g')
#         >>> n2 = note.Note('f#')
#         >>> sl = spanner.Slur()
#         >>> sl.addComponents(n1)
#         >>> sl.getComponents() == [n1]
#         True
#         >>> sl.addComponents(n2)
#         >>> sl.getComponents() == [n1, n2]
#         True
#         >>> sl.getComponentIds() == [id(n1), id(n2)]
#         True
#         >>> sl
#         <music21.spanner.Slur <music21.note.Note G><music21.note.Note F#>>
# 
#         '''
#         post = []
#         for c in self._components:
#             q = c.get() # unwrap weakreference
#             if q != None:
#                 post.append(q)
#         return post
# 
# 
#     def getComponentIds(self):
#         '''Return all id() for all stored objects.
# 
#         '''
#         # this does not unwrap weakrefs, but simply gets the stored id 
#         # from the Component object
#         post = []
#         for c in self._components:
#             q = c.id # weakref may be dead!
#             if q != None:
#                 post.append(q)
#         return post
# 
#     def addComponents(self, components, *arguments, **keywords):  
#         '''Associate one or more components with this Spanner.
# 
#         The order that components is added is retained and may or may not be significant to the spanner. 
# 
#         >>> from music21 import *
#         >>> n1 = note.Note('g')
#         >>> n2 = note.Note('f#')
#         >>> n3 = note.Note('e')
#         >>> n4 = note.Note('c')
#         >>> n5 = note.Note('d-')
# 
#         >>> sl = spanner.Slur()
#         >>> sl.addComponents(n1)
#         >>> sl.addComponents(n2, n3)
#         >>> sl.addComponents([n4, n5])
#         >>> sl.getComponentIds() == [id(n) for n in [n1, n2, n3, n4, n5]]
#         True
# 
#         '''  
#         # presently, this does not look for redundancies
#         if not common.isListLike(components):
#             components = [components]
#         # assume all other arguments
#         components += arguments
#         for c in components:
#             # create a component instance for each
#             self._components.append(Component(c))
# 
# 
#     def replaceComponent(self, old, new):
#         '''When copying a Spanner, we need to update the spanner with new references for copied components. Given the old component, this method will replace the old with the new.
# 
#         The `old` parameter can be either an object or object id. 
#         '''
#         if common.isNum(old): # assume this is an id
#             idTarget = old
#         else:
#             idTarget = id(old)
# 
#         # get index form id list; 
#         indexTarget = self.getComponentIds().index(idTarget)
#         self._components[indexTarget] = Component(new)
#         #environLocal.printDebug(['replaceComponent()', 'id(old)', id(old), 'id(new)', id(new)])
# 
# #     def __del__(self):
# #         '''On deletion, remove this reference from Spanners.
# #         '''
# #         self._spanners.remove(self)
# # 
# 
#     def isFirst(self, component):
#         '''Given a component, is it first?
# 
#         >>> from music21 import *
#         >>> n1 = note.Note('g')
#         >>> n2 = note.Note('f#')
#         >>> n3 = note.Note('e')
#         >>> n4 = note.Note('c')
#         >>> n5 = note.Note('d-')
# 
#         >>> sl = spanner.Slur()
#         >>> sl.addComponents(n1, n2, n3, n4, n5)
#         >>> sl.isFirst(n2)
#         False
#         >>> sl.isFirst(n1)
#         True
#         >>> sl.isLast(n1)
#         False
#         >>> sl.isLast(n5)
#         True
# 
#         '''
#         idTarget = id(component)
#         if self._components[0].id == idTarget:
#             return True
#         return False
# 
#     def getFirst(self):
#         '''Get the object of the first component
# 
#         >>> from music21 import *
#         >>> n1 = note.Note('g')
#         >>> n2 = note.Note('f#')
#         >>> n3 = note.Note('e')
#         >>> n4 = note.Note('c')
#         >>> n5 = note.Note('d-')
# 
#         >>> sl = spanner.Slur()
#         >>> sl.addComponents(n1, n2, n3, n4, n5)
#         >>> sl.getFirst() is n1
#         True
#         '''
#         return self._components[0].get()
# 
#     def isLast(self, component):
#         '''Given a component, is it last?  Returns True or False
#         '''
#         idTarget = id(component)
#         if self._components[-1].id == idTarget:
#             return True
#         return False
# 
#     def getLast(self):
#         '''Get the object of the first component
# 
#         >>> from music21 import *
#         >>> n1 = note.Note('g')
#         >>> n2 = note.Note('f#')
#         >>> n3 = note.Note('e')
#         >>> n4 = note.Note('c')
#         >>> n5 = note.Note('d-')
# 
#         >>> sl = spanner.Slur()
#         >>> sl.addComponents(n1, n2, n3, n4, n5)
#         >>> sl.getLast() is n5
#         True
# 
#         '''
#         return self._components[-1].get()
# 
#     def getOffsetsBySite(self, site, componentOffset=True):
#         '''Given a site shared by all components, return a list of offset values.
# 
#         To include `componentOffset` adjustments, set this value to True.
#         '''
#         post = []
#         idSite = id(site)
#         for c in self._components:
#         #for c in self.getComponents():
#             obj = c.get()
#             # getting site ids is fast, as weakrefs do not have to be unpacked
#             if idSite in obj.getSiteIds():
#                 o = obj.getOffsetBySite(site)
#                 if componentOffset:
#                     post.append(o+c.offset)
#                 else:    
#                     post.append(o)
#         return post
# 
#     def getOffsetSpanBySite(self, site, componentOffset=True):
#         '''Return the span, or min and max values, of all offsets for a given site. 
#         '''
#         post = self.getOffsetsBySite(site, componentOffset=componentOffset)
#         return [min(post), max(post)]
# 
# 
#     def getDurationSpanBySite(self, site, componentOffset=True):
#         '''Return the duration span, or the distnace between the first component's offset and the last components offset plus duration. 
#         '''
#         # these are in order
#         post = []
#         idSite = id(site)
#         offsetComponent = [] # store pairs
#         for c in self._components:
#         #for c in self.getComponents():
#             # getting site ids is fast, as weakrefs do not have to be unpacked
#             obj = c.get()
#             if idSite in obj.getSiteIds():
#                 o = obj.getOffsetBySite(site)
#                 if componentOffset:
#                     oFinal = o+c.offset
#                 else:    
#                     oFinal = o
#                 offsetComponent.append([oFinal, obj])
#         offsetComponent.sort() # sort by offset
#         minOffset = offsetComponent[0][0]
#         minComponent = offsetComponent[0][1]
# 
#         maxOffset = offsetComponent[-1][0]
#         maxComponent = offsetComponent[-1][1]
#         if maxComponent.duration is not None:
#             highestTime = maxOffset + maxComponent.duration.quarterLength
#         else:
#             highestTime = maxOffset
#     
#         return [minOffset, highestTime]
# 
# 
#     def getDurationBySite(self, site, componentOffset=True):
#         '''Return a Duration object representing the value between the first component's offset and the last components offset plus duration. 
#         '''
#         low, high = self.getDurationSpanBySite(site=site,
#                    componentOffset=componentOffset)     
#         d = duration.Duration()
#         d.quarterLength = high-low
#         return d
# 
# 
# 



class SpannerException(Exception):
    pass


#-------------------------------------------------------------------------------
class Spanner(music21.Music21Object):
    '''
    Spanner objects live on Streams as other Music21Objects, but store connections between one or more Music21Objects.

    >>> from music21 import *
    >>> sp1 = spanner.Spanner()
    >>> # assert that components Stream subclass is linked to container
    >>> sp1._components.spannerParent == sp1
    True
    '''
    def __init__(self, *arguments, **keywords):
        music21.Music21Object.__init__(self)

        # store this so subclasses can replace
        self._reprHead = '<music21.spanner.Spanner '

        # store a Stream inside of Spanner
        from music21 import stream

        # create a stream subclass, spanner storage; pass a reference
        # to this spanner for getting this spanner from the SpannerStorage 
        # directly
        self._components = stream.SpannerStorage(spannerParent=self)
        # we do not want to auto sort based on offset or class, as 
        # both are meaning less inside of this Stream (and only have meaning
        # in Stream external to this 
        self._components.autoSort = False

        # add arguments as a list or single item
        proc = []
        for arg in arguments:
            if common.isListLike(arg):
                proc += arg
            else:
                proc.append(arg)
        self.addComponents(proc)
#         if len(arguments) > 1:
#             self._components.append(arguments)
#         elif len(arguments) == 1: # assume a list is first arg
#                 self._components.append(c)

        # parameters that spanners need in loading and processing
        # local id is the id for the local area; used by musicxml
        self.idLocal = None
        # after all components have been gathered, setting complete
        # will mark that all parts have been gathered. 
        self.completeStatus = False

    
    def __repr__(self):
        msg = [self._reprHead]
        for c in self.getComponents():
            objRef = c
            msg.append(repr(objRef))
        msg.append('>')
        return ''.join(msg)

    def __deepcopy__(self, memo=None):
        '''This produces a new, independent object contain references to the same components.

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> c2 = clef.BassClef()
        >>> sp1 = spanner.Spanner(n1, n2, c1)
        >>> sp2 = copy.deepcopy(sp1)
        >>> len(sp2.getComponents())
        3
        >>> sp2[0] == sp1[0]
        True
        >>> sp2[2] == sp1[2]
        True
        '''
        new = self.__class__()
        old = self
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue

            part = getattr(self, name)

            # functionality duplicated from Music21Object
            if name == '_activeSite':
                #environLocal.printDebug(['creating parent reference'])
                newValue = self.activeSite # keep a reference, not a deepcopy
                setattr(new, name, newValue)

            # do not deepcopy _components, as this will copy the 
            # contained objects
            elif name == '_components':
                for c in old._components:
                    new._components.append(c)
            else: 
                #environLocal.printDebug(['Spanner.__deepcopy__', name])
                newValue = copy.deepcopy(part, memo)
                setattr(new, name, newValue)
    
        # do after all other copying
        new._idLastDeepCopyOf = id(self)
        return new


    def __getitem__(self, key):
        '''
        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.BassClef()
        >>> sl = spanner.Spanner(n1, n2, c1)
        >>> sl[0] == n1
        True
        >>> sl[-1] == c1
        True
        >>> sl[clef.BassClef][0] == c1
        True
        '''
        # delegate to Stream subclass
        # will return None if weakref is dead
        return self._components.__getitem__(key)


    def getComponents(self):
        '''Return all components for this Spanner as objects, without weak-refs.  

        As this is a Music21Object, the name here is more specific to avoid name clashes.

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> sl = spanner.Spanner()
        >>> sl.addComponents(n1)
        >>> sl.getComponents() == [n1]
        True
        >>> sl.addComponents(n2)
        >>> sl.getComponents() == [n1, n2]
        True
        >>> sl.getComponentIds() == [id(n1), id(n2)]
        True
        >>> c1 = clef.TrebleClef()
        >>> sl.addComponents(c1)
        >>> sl.getComponents() == [n1, n2, c1] # make sure that not sorting
        True
        '''
        post = []
        for c in self._components:
            objRef = c
            if objRef is not None:
                post.append(objRef)
        return post

    def getComponentsByClass(self, classFilterList):
        '''
        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> sl = spanner.Spanner()
        >>> sl.addComponents([n1, n2, c1])
        >>> sl.getComponentsByClass('Note') == [n1, n2]
        True
        >>> sl.getComponentsByClass('Clef') == [c1]
        True
        '''
        # returns a Stream; pack in a list
        postStream = self._components.getElementsByClass(classFilterList)
        post = []
        for c in postStream:
            objRef = c
            if objRef is not None:
                post.append(objRef)
        return post

    def getComponentIds(self):
        '''Return all id() for all stored objects.

        '''
        # this does not unwrap weakrefs, but simply gets the stored id 
        # from the Component object
        post = []
        for c in self._components:
            objRef = c
            if objRef is not None:
                post.append(id(objRef))
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

        >>> sl = spanner.Spanner()
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
        #environLocal.printDebug(['addComponents():', components])
        for c in components:
            # create a component instance for each
            #self._components.append(Component(c))
            self._components.append(c)


    def replaceComponent(self, old, new):
        '''When copying a Spanner, we need to update the spanner with new references for copied components. Given the old component, this method will replace the old with the new.

        The `old` parameter can be either an object or object id. 

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> c2 = clef.BassClef()
        >>> sl = spanner.Spanner(n1, n2, c1)
        >>> sl.replaceComponent(c1, c2)
        >>> sl[-1] == c2
        True
        '''
        if common.isNum(old):
            self._components.replace(old, new)
        else:
            self._components.replace(old, new)

        # get index form id list; 
#         indexTarget = self.getComponentIds().index(idTarget)
#         self._components[indexTarget] = Component(new)
        #environLocal.printDebug(['replaceComponent()', 'id(old)', id(old), 'id(new)', id(new)])

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

        >>> sl = spanner.Spanner()
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
        objRef = self._components[0]
        if id(objRef) == idTarget:
            return True
        return False

    def getFirst(self):
        '''Get the object of the first component

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Spanner()
        >>> sl.addComponents(n1, n2, n3, n4, n5)
        >>> sl.getFirst() is n1
        True
        '''
        return self._components[0]

    def isLast(self, component):
        '''Given a component, is it last?  Returns True or False
        '''
        idTarget = id(component)
        objRef = self._components[-1]

        if id(objRef) == idTarget:
            return True
        return False



    def getLast(self):
        '''Get the object of the first component

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Spanner()
        >>> sl.addComponents(n1, n2, n3, n4, n5)
        >>> sl.getLast() is n5
        True

        '''
        objRef = self._components[-1]
        return objRef


    def getOffsetsBySite(self, site):
        '''Given a site shared by all components, return a list of offset values.

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> s = stream.Stream()
        >>> s.insert(3, n1)
        >>> s.insert(11, n2)
        >>> sp = spanner.Spanner(n1, n2)
        >>> sp.getOffsetsBySite(s)
        [3.0, 11.0]
        '''
        post = []
        idSite = id(site)
        for c in self._components:
            # getting site ids is fast, as weakrefs do not have to be unpacked
            if idSite in c.getSiteIds():
                o = c.getOffsetBySite(site)
                post.append(o)
        return post

    def getOffsetSpanBySite(self, site):
        '''Return the span, or min and max values, of all offsets for a given site. 
        '''
        post = self.getOffsetsBySite(site)
        return [min(post), max(post)]


    def getDurationSpanBySite(self, site):
        '''Return the duration span, or the distnace between the first component's offset and the last components offset plus duration. 
        '''
        # these are in order
        post = []
        idSite = id(site)
        offsetComponent = [] # store pairs
        for c in self._components:
        #for c in self.getComponents():
            objRef = c

            if idSite in objRef.getSiteIds():
                o = objRef.getOffsetBySite(site)
                offsetComponent.append([o, objRef])
        offsetComponent.sort() # sort by offset
        minOffset = offsetComponent[0][0]
        minComponent = offsetComponent[0][1]

        maxOffset = offsetComponent[-1][0]
        maxComponent = offsetComponent[-1][1]
        if maxComponent.duration is not None:
            highestTime = maxOffset + maxComponent.duration.quarterLength
        else:
            highestTime = maxOffset
    
        return [minOffset, highestTime]


    def getDurationBySite(self, site):
        '''Return a Duration object representing the value between the first component's offset and the last components offset plus duration. 
        '''
        low, high = self.getDurationSpanBySite(site=site)     
        d = duration.Duration()
        d.quarterLength = high-low
        return d






#-------------------------------------------------------------------------------
class SpannerBundle(object):
    '''A utility object for collecting and processing collections of Spanner objects.

    If a Stream or Stream subclass is provided as an argument, all Spanners on this Stream will be accumulated herein. 
    '''

    def __init__(self, *arguments, **keywords):
        self._storage = []

        for arg in arguments:
            if common.isListLike(arg):
                for e in arg:
                    self._storage.append(e)                
            elif 'Stream' in arg.classes:
                for e in arg.spanners:
                    self._storage.append(e)
            # assume its a spanner
            elif 'Spanner' in arg.classes:
                self._storage.append(arg)
    
    def append(self, other):
        self._storage.append(other)

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return self._storage.__iter__()

    def __getitem__(self, key):
        return self._storage[key]

    def __repr__(self):
        return '<music21.spanner.SpannerBundle of size %s>' % self.__len__()

    def _getList(self):
        '''Return the bundle as a list.
        '''
        post = []
        for x in self._storage:
            post.append(x)
        return post

    list = property(_getList, 
        doc='''Return the bundle as a list.
        ''')

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
        >>> sb.getByComponent(n1).list == [su1]
        True
        >>> sb.getByComponent(n3).list == [su2]
        True
        >>> sb.getByComponent(n2).list == [su1, su2]
        True
        '''
        idTarget = id(component)
        post = self.__class__()
        for sp in self._storage:
            if idTarget in sp.getComponentIds():
                post.append(sp)
        return post


    def replaceComponent(self, old, new):
        '''Given a spanner component (an object), replace all old components with new components for all Spanner objects contained in this bundle.

        The `old` parameter can be either an object or object id. 
        '''
        #environLocal.printDebug(['SpannerBundle.replaceComponent()', 'old', old, 'new', new])

        if common.isNum(old): # assume this is an id
            idTarget = old
        else:
            idTarget = id(old)
        #post = self.__class__() # return a bundle of spanners that had changes
        for sp in self._storage:
            #environLocal.printDebug(['looking at spanner', sp, sp.getComponentIds()])

            # must check to see if this id is in this spanner
            if idTarget in sp.getComponentIds():
                sp.replaceComponent(old, new)
                #post.append(sp)
                #environLocal.printDebug(['replaceComponent()', sp, 'old', old, 'id(old)', id(old), 'new', new, 'id(new)', id(new)])
        #return post


    def getByClass(self, className):
        '''Given a spanner class, return a bundle of all Spanners of the desired class. 

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su2 = spanner.StaffGroup()
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.getByClass(spanner.Slur).list == [su1]
        True
        >>> sb.getByClass('Slur').list == [su1]
        True
        >>> sb.getByClass('StaffGroup').list == [su2]
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
        # line type is only needed as a start parameter; suggest that
        # this should also have start/end parameters
        self.lineType = None # can be "dashed" or None

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Slur ')
        return msg
    



#-------------------------------------------------------------------------------
class DynamicWedge(Spanner):
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self.type = None # crescendo or diminuendo
        self.placement = 'below' # can above or below, after musicxml
        self.spread = 15

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.DynamicWedge ')
        return msg

class Crescendo(DynamicWedge):
    '''A spanner crescendo wedge.

    >>> from music21 import spanner
    >>> d = spanner.Crescendo()
    >>> d.getStartParameters()
    {'spread': 0, 'type': 'crescendo'}
    >>> d.getEndParameters()
    {'spread': 15, 'type': 'stop'}
    '''
    def __init__(self, *arguments, **keywords):
        DynamicWedge.__init__(self, *arguments, **keywords)
        self.type = 'crescendo'

    def getStartParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = self.type # cresc 
        post['spread'] = 0 # start at zero
        return post

    def getEndParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = 'stop'  # end is always stop
        post['spread'] = self.spread # end with spread
        return post

class Diminuendo(DynamicWedge):
    '''A spanner diminuendo wedge.

    >>> from music21 import spanner
    >>> d = spanner.Diminuendo()
    >>> d.getStartParameters()
    {'spread': 15, 'type': 'diminuendo'}
    >>> d.getEndParameters()
    {'spread': 0, 'type': 'stop'}
    '''
    def __init__(self, *arguments, **keywords):
        DynamicWedge.__init__(self, *arguments, **keywords)
        self.type = 'diminuendo'

    def getStartParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = self.type # dim
        post['spread'] = self.spread # start with spread
        return post

    def getEndParameters(self):
        '''Return the parameters for the start of this spanner
        ''' 
        post = {}
        post['type'] = 'stop'  # end is always stop
        post['spread'] = 0
        return post





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

        self.assertEqual(slur1.getOffsetsBySite(p1), [0.0, 2.0])
        self.assertEqual(slur1.getOffsetSpanBySite(p1), [0.0, 2.0])

        # a note can access what spanners it is part of 
        self.assertEqual(n1.getSpannerSites(), [slur1])

        # can a spanner hold spanners: yes
        sl1 = Slur()
        sl2 = Slur()
        sl3 = Slur()
        sp = Spanner([sl1, sl2, sl3])
        self.assertEqual(len(sp.getComponents()), 3)
        self.assertEqual(sp.getComponents(), [sl1, sl2, sl3])

        self.assertEqual(sl1.getSpannerSites(), [sp])


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

        self.assertEqual(n1.getSpannerSites(), [su1])
        self.assertEqual(n3.getSpannerSites(), [su1])

        su2 = copy.deepcopy(su1)

        self.assertEqual(su1.getComponents(), [n1, n3])
        self.assertEqual(su2.getComponents(), [n1, n3])

        self.assertEqual(n1.getSpannerSites(), [su1, su2])
        self.assertEqual(n3.getSpannerSites(), [su1, su2])


        sb1 = spanner.SpannerBundle(su1, su2)
        sb2 = copy.deepcopy(sb1)
        self.assertEqual(sb1[0].getComponents(), [n1, n3])
        self.assertEqual(sb2[0].getComponents(), [n1, n3])
        # spanners stored within are not the same objects
        self.assertEqual(id(sb2[0]) != id(sb1[0]), True)



    def testReplaceComponent(self):
        from music21 import note, spanner

        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()
        n4 = note.Note()
        n5 = note.Note()

        su1 = spanner.Slur()
        su1.addComponents([n1, n3])

        self.assertEqual(su1.getComponents(), [n1, n3])
        self.assertEqual(n1.getSpannerSites(), [su1])

        su1.replaceComponent(n1, n2)
        self.assertEqual(su1.getComponents(), [n2, n3])
        # this note now has no spanner sites
        self.assertEqual(n1.getSpannerSites(), [])
        self.assertEqual(n2.getSpannerSites(), [su1])

        # replace n2 w/ n1
        su1.replaceComponent(n2, n1)
        self.assertEqual(su1.getComponents(), [n1, n3])
        self.assertEqual(n2.getSpannerSites(), [])
        self.assertEqual(n1.getSpannerSites(), [su1])


        su2 = spanner.Slur()
        su2.addComponents([n3, n4])

        su3 = spanner.Slur()
        su3.addComponents([n4, n5])


        n1a = note.Note()
        n2a = note.Note()
        n3a = note.Note()
        n4a = note.Note()
        n5a = note.Note()

        sb1 = spanner.SpannerBundle(su1, su2, su3)
        self.assertEqual(len(sb1), 3)
        self.assertEqual(sb1.list, [su1, su2, su3])

        # n3 is found in su1 and su2

        sb1.replaceComponent(n3, n3a)
        self.assertEqual(len(sb1), 3)
        self.assertEqual(sb1.list, [su1, su2, su3])

        self.assertEqual(sb1[0].getComponents(), [n1, n3a])
        # check su2
        self.assertEqual(sb1[1].getComponents(), [n3a, n4])

        sb1.replaceComponent(n4, n4a)
        self.assertEqual(sb1[1].getComponents(), [n3a, n4a])

        # check su3
        self.assertEqual(sb1[2].getComponents(), [n4a, n5])


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()

        t.testReplaceComponent()



#------------------------------------------------------------------------------
# eof





