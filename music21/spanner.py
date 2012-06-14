# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         spanner.py
# Purpose:      The Spanner base-class and subclasses
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
A spanner is a music21 object that represents a connection usually between 
two or more music21 objects that might live in different streams but need 
some sort of connection between them.  A slur is one type of spanner -- it might
connect notes in different Measure objects or even between different parts.


This package defines some of the most common spanners.  Other spanners
can be found in modules such as :ref:`moduleDynamics` (for things such as crescendos)
or in :ref:`moduleMeter` (a ritardando, for instance).
'''

import unittest
import copy

import music21
from music21 import common
from music21 import duration

from music21 import environment
_MOD = "spanner.py"  
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class SpannerException(Exception):
    pass
class SpannerBundleException(Exception):
    pass


#-------------------------------------------------------------------------------
class Spanner(music21.Music21Object):
    '''
    Spanner objects live on Streams in the same manner as other Music21Objects, but represent and store connections between one or more other Music21Objects.

    Commonly used Spanner subclasses include the :class:`~music21.spanner.Slur`, :class:`~music21.spanner.RepeatBracket`, :class:`~music21.spanner.Crescendo`, and :class:`~music21.spanner.Diminuendo`.

    In some cases you will want to subclass Spanner
    for specific purposes.  

    In the first demo, we create
    a spanner to represent a written-out accelerando, such
    as Elliott Carter uses in his second string quartet (he marks them
    with an arrow).


    >>> from music21 import *
    >>> class CarterAccelerandoSign(spanner.Spanner):
    ...    pass
    >>> n1 = note.Note('C4')
    >>> n2 = note.Note('D4')
    >>> n3 = note.Note('E4')
    >>> sp1 = CarterAccelerandoSign(n1, n2, n3) # or as a list: [n1, n2, n3]
    >>> sp1.getComponents()
    [<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]
    
    
    Now we put the notes and the spanner into a Stream object.  Note that
    the convention is to put the spanner at the beginning:
    
    
    >>> s = stream.Stream()
    >>> s.append([n1, n2, n3])
    >>> s.insert(0, sp1)
    
    
    Now we can get at the spanner in one of three ways.
    
    (1) it is just a normal element in the stream:
    
    >>> for e in s:
    ...    print e
    <music21.note.Note C>
    <music21.spanner.CarterAccelerandoSign <music21.note.Note C><music21.note.Note D><music21.note.Note E>>
    <music21.note.Note D>
    <music21.note.Note E>
    
    
    (2) we can get a stream of spanners (equiv. to getElementsByClass('Spanner'))
        by calling the .spanner property on the stream.
    
    >>> spannerCollection = s.spanners # a stream object
    >>> for thisSpanner in spannerCollection:
    ...     print thisSpanner
    <music21.spanner.CarterAccelerandoSign <music21.note.Note C><music21.note.Note D><music21.note.Note E>>


    (3) we can get the spanner by looking at the list getSpannerSites() on any object.
    

    >>> n2.getSpannerSites()
    [<music21.spanner.CarterAccelerandoSign <music21.note.Note C><music21.note.Note D><music21.note.Note E>>]
    
    
    In this example we will slur a few notes and then iterate over the stream to
    see which are slurred:
    
    
    >>> n1 = note.Note('C4')
    >>> n2 = note.Note('D4')
    >>> n3 = note.Note('E4')
    >>> n4 = note.Note('F4')
    >>> n5 = note.Note('G4')
    >>> n6 = note.Note('A4')
    
    
    Create a slur over the second and third notes at instantiation:
    
    >>> slur1 = spanner.Slur([n2, n3])
    
    Slur the fifth and the sixth notes by adding them to an existing slur:
    
    >>> slur2 = spanner.Slur()
    >>> slur2.addComponents([n5, n6])
    
    Now add them all to a stream:
    
    >>> part1 = stream.Part()
    >>> part1.append([n1, n2, n3, n4, n5, n6])
    >>> part1.insert(0, slur1)
    >>> part1.insert(0, slur2)
    
    Say we wanted to know which notes in a piece started a
    slur, here's how we could do it:
    
    >>> for n in part1.notes:
    ...    ss = n.getSpannerSites()
    ...    for thisSpanner in ss:
    ...       if 'Slur' in thisSpanner.classes:
    ...            if thisSpanner.isFirst(n):
    ...                print n.nameWithOctave
    D4
    G4
    
    Alternatively, you could iterate over the spanners
    of part1 and get their first elements:
    
    >>> for thisSpanner in part1.spanners:
    ...     firstNote = thisSpanner.getComponents()[0]
    ...     print firstNote.nameWithOctave
    D4
    G4
    
    The second method is shorter, but the first is likely to
    be useful in cases where you are doing other things to
    each note object along the way.  
    
    Oh, and of course, slurs do print properly in musicxml:
    
    
    >>> #_DOCS_SHOW part1.show()
    
    .. image:: images/slur1_example.*
        :width: 400
    
    (the Carter example would not print an arrow since that
    element has no corresponding musicxml representation).

    
    
    OMIT_FROM_DOCS
    
    >>> # assert that components Stream subclass is linked to container
    >>> sp1._components.spannerParent == sp1
    True
    '''
    # this class attribute provides performance optimized class selection
    isSpanner = True 

    def __init__(self, *arguments, **keywords):
        music21.Music21Object.__init__(self)

        self._cache = {} #common.DefaultHash()    

        # store this so subclasses can replace
        if self.__module__ != '__main__':
            if self.__module__.startswith('music21') == False:
                self._reprHead = '<music21.' + self.__module__ + '.' + self.__class__.__name__ + ' '
            else:
                self._reprHead = '<' + self.__module__ + '.' + self.__class__.__name__ + ' '
        else:
            self._reprHead = '<music21.spanner.' + self.__class__.__name__ + ' '
        # store a Stream inside of Spanner
        from music21 import stream

        # create a stream subclass, spanner storage; pass a reference
        # to this spanner for getting this spanner from the SpannerStorage 
        # directly
        self._components = stream.SpannerStorage(spannerParent=self)
        # we do not want to auto sort based on offset or class, as 
        # both are meaningless inside of this Stream (and only have meaning
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
        '''This produces a new, independent object containing references to the same components. Components linked in this Spanner must be manually re-set, likely using the replaceComponent() method.

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
            if name == '_cache':
                continue
            part = getattr(self, name)
            # functionality duplicated from Music21Object
            if name == '_activeSite':
                #environLocal.printDebug(['creating parent reference'])
                # keep a reference, not a deepcopy
                setattr(new, name, self.activeSite)
            elif name == '_definedContexts':
                newValue = copy.deepcopy(part, memo)
                newValue.containedById = id(new)
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


    #---------------------------------------------------------------------------
    # as _components is private Stream, unwrap/wrap methods need to override
    # Music21Object to get at these objects 
    # this is the same as with Variants

    def purgeOrphans(self):
        self._components.purgeOrphans()
        music21.Music21Object.purgeOrphans(self)

    def purgeLocations(self, rescanIsDead=False):
        # must override Music21Object to purge locations from the contained
        # Stream
        # base method to perform purge on the Sream
        self._components.purgeLocations(rescanIsDead=rescanIsDead)
        music21.Music21Object.purgeLocations(self, rescanIsDead=rescanIsDead)
            
    def unwrapWeakref(self):
        '''Overridden method for unwrapping all Weakrefs.
        '''
        # call base method: this gets defined contexts and active site
        music21.Music21Object.unwrapWeakref(self)
        # for contained objects that have weak refs
        #environLocal.pd(['spanner unwrapping contained stream'])
        self._components.unwrapWeakref()
        # this presently is not a weakref but in case of future changes

    def wrapWeakref(self):
        '''Overridden method for unwrapping all Weakrefs.
        '''
        # call base method: this gets defined contexts and active site
        music21.Music21Object.wrapWeakref(self)
        self._components.wrapWeakref()


    def freezeIds(self):
        music21.Music21Object.freezeIds(self)
        self._components.freezeIds()

    def unfreezeIds(self):
        music21.Music21Object.unfreezeIds(self)
        self._components.unfreezeIds()


    def getSpannerStorageId(self):
        '''Return the object id of the SpannerStorage object
        '''
        return id(self._components)

    #---------------------------------------------------------------------------
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
        return self._components.__getitem__(key)

    def __len__(self):
        return len(self._components._elements)


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
        # use low-level _elements access for speed; do not need to set
        # active sit or iterator
        # must pass into a new list
        for c in self._components._elements:
#             objRef = c
#             if objRef is not None:
            post.append(c)
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
#         post = []
#         for c in postStream:
#             post.append(objRef)

        # return raw elements list for speed; attached to a temporary stream
        return postStream._elements

    def getComponentIds(self):
        '''Return all id() for all stored objects.
        '''
        if 'componentIds' not in self._cache or self._cache['componentIds'] is None:
            self._cache['componentIds'] = [id(c) for c in self._components._elements]
        return self._cache['componentIds']


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
            if c is None:
                continue
            if not self._components.hasElement(c): # not already in storage
                self._components._appendCore(c)
            else:
                pass
                # it makes sense to not have multiple copies
                #environLocal.printDebug(['attempting to add an object (%s) that is already found in the SpannerStorage stream of spaner %s; this may not be an error.' % (c, self)])

        self._components._elementsChanged()
        # always clear cache
        if len(self._cache) > 0:
            self._cache = {} #common.DefaultHash()

    def hasComponent(self, component):  
        '''Return True if this Spanner has the component.'''
        for c in self._components._elements:
            if id(c) == id(component):
                return True
        return False

    def replaceComponent(self, old, new):
        '''When copying a Spanner, we need to update the spanner with new references for copied components (if the Notes of a Slur have beenc copied, that Slur's Note references need references to the new Notes). Given the old component, this method will replace the old with the new.

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
        if old is None:
            return None # do nothing
        if common.isNum(old):
            # this must be id(obj), not obj.id
            e = self._components.getElementByObjectId(old)
            # e here is the old element that was spanned by this Spanner
            

            #environLocal.printDebug(['current Spanner.componentIds()', self.getComponentIds()])
            #environLocal.printDebug(['Spanner.replaceComponent:', 'getElementById result', e, 'old target', old])
            if e is not None:
                #environLocal.printDebug(['Spanner.replaceComponent:', 'old', e, 'new', new])
                # do not do all Sites: only care about this one
                self._components.replace(e, new, allTargetSites=False)
        else:
            # do not do all Sites: only care about this one
            self._components.replace(old, new, allTargetSites=False)
            #environLocal.printDebug(['Spanner.replaceComponent:', 'old', e, 'new', new])

        # while this Spanner now has proper elements in its _components Stream, the element replaced likely has a site left-over from its previous Spanner

        # always clear cache
        if len(self._cache) > 0:
            self._cache = {} #common.DefaultHash()

        #environLocal.printDebug(['replaceComponent()', 'id(old)', id(old), 'id(new)', id(new)])


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
        objRef = self._components._elements[0]
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
        objRef = self._components._elements[-1]

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
        objRef = self._components.elements[-1]
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
        for c in self._components._elements:
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

        # special handling for case of a single component spanner
        if len(self._components) == 1:
            o = self._components[0].getOffsetBySite(site)
            return o, o + self._components[0].duration.quarterLength

        offsetComponent = [] # store pairs
        for c in self._components._elements:
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
    '''A utility object for collecting and processing collections of Spanner objects. This is necessary because often processing routines that happen at many different levels need access to the same collection of spanners. 

    Because SpannerBundles are so commonly used with :class:`~music21.stream.Stream` objects, the Stream has a :attr:`~music21.stream.Stream.spannerBundle` property that stores and caches a SpannerBundle of the Stream.

    If a Stream or Stream subclass is provided as an argument, all Spanners on this Stream will be accumulated herein. 
    '''
    def __init__(self, *arguments, **keywords):
        self._cache = {} #common.DefaultHash()    
        self._storage = [] # a simple List, not a Stream
        for arg in arguments:
            if common.isListLike(arg):
                for e in arg:
                    self._storage.append(e)    
            # take a Stream and use its .spanners property to get all spanners            
            #elif 'Stream' in arg.classes:
            elif arg.isStream:
                for e in arg.spanners:
                    self._storage.append(e)
            # assume its a spanner
            elif 'Spanner' in arg.classes:
                self._storage.append(arg)
    
        # a special spanners, stored in storage, can be identified in the 
        # SpannerBundle as missing a component; the next obj that meets
        # the class expectation will then be assigned and the component 
        # cleared
        self._pendingComponentAssignment = []

    def append(self, other):
        self._storage.append(other)
        if len(self._cache) > 0:
            self._cache = {} #common.DefaultHash()

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return self._storage.__iter__()

    def __getitem__(self, key):
        return self._storage[key]

    def remove(self, item):
        '''Remove a stored Spanner from the bundle with an instance. Each reference must have a matching id() value.

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
        >>> sb.remove(su2)
        >>> len(sb)
        1

        '''
        if item in self._storage:
            self._storage.remove(item)
        else:
            raise SpannerBundleException('cannot match object for removal: %s' % item)
        if len(self._cache) > 0:
            self._cache = {} #common.DefaultHash()

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

    def getSpannerStorageIds(self):
        '''Return all SpannerStorage ids from all contained Spanners
        '''
        post = []
        for x in self._storage:
            post.append(x.getSpannerStorageId())
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
        cacheKey = 'idLocal-%s' % idLocal
        if cacheKey not in self._cache or self._cache[cacheKey] is None:
            post = self.__class__()
            for sp in self._storage:
                if sp.idLocal == idLocal:
                    post.append(sp)
            self._cache[cacheKey] = post
        return self._cache[cacheKey]


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
        # cannot cache, as complete status may change internally
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
        # NOTE: this is a performance critical operation
#         idTarget = id(component)
#         post = self.__class__()
#         for sp in self._storage: # storage is a list
#             if idTarget in sp.getComponentIds():
#                 post.append(sp)
#         return post

        idTarget = id(component)
        cacheKey = 'getByComponent-%s' % idTarget
        if cacheKey not in self._cache or self._cache[cacheKey] is None:
            post = self.__class__()
            for sp in self._storage: # storage is a list of spanners
                if idTarget in sp.getComponentIds():
                    post.append(sp)
            self._cache[cacheKey] = post
        return self._cache[cacheKey]


    def replaceComponent(self, old, new):
        '''Given a spanner component (an object), replace all old components with new components for all Spanner objects contained in this bundle.

        The `old` parameter can be either an object or object id. 

        If no replacements are found, no errors are raised.
        '''
        #environLocal.printDebug(['SpannerBundle.replaceComponent()', 'old', old, 'new', new, 'len(self._storage)', len(self._storage)])

        if common.isNum(old): # assume this is an id
            idTarget = old
        else:
            idTarget = id(old)

        #post = self.__class__() # return a bundle of spanners that had changes
        for sp in self._storage: # Spanners in a list
            #environLocal.printDebug(['looking at spanner', sp, sp.getComponentIds()])

            # must check to see if this id is in this spanner
            if idTarget in sp.getComponentIds():
                sp.replaceComponent(old, new)
                #post.append(sp)
                #environLocal.printDebug(['replaceComponent()', sp, 'old', old, 'id(old)', id(old), 'new', new, 'id(new)', id(new)])

        if len(self._cache) > 0:
            self._cache = {} #common.DefaultHash()

    def getByClass(self, className):
        '''Given a spanner class, return a bundle of all Spanners of the desired class. 

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su2 = layout.StaffGroup()
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
        # NOTE: this is called very frequently: optimize
#         post = self.__class__()
#         for sp in self._storage:
#             if common.isStr(className):
#                 if className in sp.classes:
#                     post.append(sp)
#             else:
#                 if isinstance(sp, className):
#                     post.append(sp)
#         return post

        cacheKey = 'getByClass-%s' % className
        if cacheKey not in self._cache or self._cache[cacheKey] is None:
            post = self.__class__()
            for sp in self._storage:
                if common.isStr(className):
                    if className in sp.classes:
                        post.append(sp)
                else:
                    if isinstance(sp, className):
                        post.append(sp)
            self._cache[cacheKey] = post
        return self._cache[cacheKey]


    def setIdLocalByClass(self, className, maxId=6):
        '''Automatically set id local values for all members of the provided class. This is necessary in cases where spanners are newly created in potentially overlapping boundaries and need to be tagged for MusicXML or other output. Note that, if some Spanners already have ids, they will be overwritten.

        The `maxId` parameter sets the largest number used in id ass

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su2 = layout.StaffGroup()
        >>> su3 = spanner.Slur()
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.append(su3)
        >>> [sp.idLocal for sp in sb.getByClass('Slur')]
        [None, None]
        >>> sb.setIdLocalByClass('Slur')
        >>> [sp.idLocal for sp in sb.getByClass('Slur')]
        [1, 2]

        '''
        found = []
        # note that this over rides previous values
        for i, sp in enumerate(self.getByClass(className)):
            # 6 seems to be limit in musicxml processing
            sp.idLocal = (i % maxId) + 1
                

    def setIdLocals(self):
        '''Set all id locals for all classes in this SpannerBundle. This will assure that each class has a unique id local number. This is destructive: existing id local values will be lost.

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su2 = layout.StaffGroup()
        >>> su3 = spanner.Slur()
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.append(su3)
        >>> [sp.idLocal for sp in sb.getByClass('Slur')]
        [None, None]
        >>> sb.setIdLocals()
        >>> [(sp, sp.idLocal) for sp in sb]
        [(<music21.spanner.Slur >, 1), (<music21.layout.StaffGroup >, 1), (<music21.spanner.Slur >, 2)]
        '''
        classes = []
        for sp in self._storage:
            if sp.classes[0] not in classes:
                classes.append(sp.classes[0])
        for className in classes:
            self.setIdLocalByClass(className)
    

    def getByComponentAndClass(self, component, className):
        '''Get all Spanners that both contain the component and match the provided class. 
        '''
        return self.getByComponent(component).getByClass(className)

    def getByClassIdLocalComplete(self, className, idLocal, completeStatus):
        '''Get all spanners of a specified class `className`, an id `idLocal`, and a `completeStatus`. This is a convenience routine for multiple filtering when searching for relevant Spanners to pair with. 

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su2 = layout.StaffGroup()
        >>> su2.idLocal = 3
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.getByClassIdLocalComplete('StaffGroup', 3, False).list == [su2]
        True
        >>> su2.completeStatus = True
        >>> sb.getByClassIdLocalComplete('StaffGroup', 3, False).list == []
        True
        '''
        return self.getByClass(className).getByIdLocal(
            idLocal).getByCompleteStatus(completeStatus)

    def getByClassComplete(self, className, completeStatus):
        '''Get all spanner of a specified class `className` and a `completeStatus`. Convenience routine for multiple filtering

        >>> from music21 import *
        >>> su1 = spanner.Slur()
        >>> su1.completeStatus = True
        >>> su2 = layout.StaffGroup()
        >>> su3 = spanner.Slur()
        >>> su3.completeStatus = False
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.append(su3)
        >>> sb.getByClassComplete('Slur', True).list == [su1]
        True
        >>> sb.getByClassComplete('Slur', False).list == [su3]
        True
        '''
        return self.getByClass(className).getByCompleteStatus(completeStatus)


    def setPendingComponentAssignment(self, sp, className):
        ref = {'spanner':sp, 'className':className}
        self._pendingComponentAssignment.append(ref)

    def freePendingComponentAssignment(self, componentCandidate):
        if len(self._pendingComponentAssignment) == 0:
            return

        remove = None
        for i, ref in enumerate(self._pendingComponentAssignment):
            #environLocal.pd(['calling freePendingComponentAssignment()', self._pendingComponentAssignment])
            if componentCandidate.isClassOrSubclass([ref['className']]):
                ref['spanner'].addComponents(componentCandidate)
                remove = i      
                #environLocal.pd(['freePendingComponentAssignment()', 'added component', ref['spanner']])
                break
        if remove is not None:
            self._pendingComponentAssignment.pop(remove)




#-------------------------------------------------------------------------------
# connect two or more notes anywhere in the score
class Slur(Spanner):
    '''A slur represented as a spanner between two Notes. 

    The `idLocal` attribute, defined in the Spanner base class, is used to mark start and end tags of potentially overlapping indicators.
    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)
        self.placement = None # can above or below, after musicxml
        # line type is only needed as a start parameter; suggest that
        # this should also have start/end parameters
        self.lineType = None # can be "dashed" or None

    # TODO: add property for placement

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Slur ')
        return msg
    
#-------------------------------------------------------------------------------
# first/second repeat bracket
class RepeatBracket(Spanner):
    '''A grouping of one or more measures, presumably in sequence, that mark an alternate repeat. 

    These gather what are sometimes called first-time bars and second-time bars.

    It is assumed that numbering starts from 1. Numberings above 2 are permitted. The `number` keyword argument can be used to pass in the desired number. 

    >>> from music21 import *
    >>> m = stream.Measure()
    >>> sp = spanner.RepeatBracket(m, number=1)
    >>> sp # can be one or more measures
    <music21.spanner.RepeatBracket 1 <music21.stream.Measure 0 offset=0.0>>
    >>> sp.number = 3
    >>> sp # can be one or more measures
    <music21.spanner.RepeatBracket 3 <music21.stream.Measure 0 offset=0.0>>
    >>> sp.getNumberList() # the list of repeat numbers
    [3]
    >>> sp.number = '1-3' # range of repeats
    >>> sp.getNumberList()
    [1, 2, 3]
    >>> sp.number = [2,3] # range of repeats
    >>> sp.getNumberList()
    [2, 3]
    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self._number = None
        self._numberRange = [] # store a range, inclusive of the single number assignment
        self._numberSpanIsAdjacent = None
        if 'number' in keywords.keys():
            self.number = keywords['number']

    # property to enforce numerical numbers
    def _getNumber(self):
        '''This must return a string, as we may have single numbers or lists. For a raw numerical list, use getNumberList() below.
        '''
        if len(self._numberRange) == 1:
            return str(self._number)
        else:
            if self._numberSpanIsAdjacent:
                return '%s, %s' % (self._numberRange[0], self._numberRange[-1])
            else: # range of values
                return '%s-%s' % (self._numberRange[0], self._numberRange[-1])

    def _setNumber(self, value):
        '''Set the bracket number. There may be range of values provided
        '''
        if value in ['', None]:
            # assume this is 1 
            self._numberRange = [1]
            self._number = 1
        elif common.isListLike(value):
            self._numberRange = [] # clear
            for x in value:
                if common.isNum(x):
                    self._numberRange.append(x)
                else:
                    raise SpannerException('number for RepeatBracket must be a number, not %r' % value)
            self._number = min(self._numberRange)
        elif common.isStr(value):
            # assume defined a range with a dash; assumed inclusive
            if '-' in value:
                start, end = value.split('-')
                self._numberRange = range(int(start), int(end)+1)
                self._numberSpanIsAdjacent = False
            elif ',' in value: # assuming only two values
                start, end = value.split(',')
                self._numberRange = range(int(start), int(end)+1)
                # mark as contiguous numbers
                self._numberSpanIsAdjacent = True
            elif value.isdigit():
                self._numberRange.append(int(value))
            else:
                raise SpannerException('number for RepeatBracket must be a number, not %r' % value)
            self._number = min(self._numberRange)
        elif common.isNum(value):
            self._numberRange = [] # clear
            self._number = value
            if value not in self._numberRange:
                self._numberRange.append(value)
        else:
            raise SpannerException('number for RepeatBracket must be a number, not %r' % value)

    number = property(_getNumber, _setNumber, doc = '''
        ''')

    def getNumberList(self):
        '''Get a contiguous list of repeat numbers that are applicable for this instance.

        >>> from music21 import *
        >>> rb = spanner.RepeatBracket()
        >>> rb.number = '1,2'
        >>> rb.getNumberList()
        [1, 2]
        '''
        return self._numberRange

    def __repr__(self):
        msg = Spanner.__repr__(self)
        if self.number is not None:
            msg = msg.replace(self._reprHead, '<music21.spanner.RepeatBracket %s ' % self.number)
        else:
            msg = msg.replace(self._reprHead, '<music21.spanner.RepeatBracket ')
        return msg




#-------------------------------------------------------------------------------
# line-based spanners

class Ottava(Spanner):
    '''An octave shift line

    >>> from music21 import *
    >>> os = spanner.Ottava(type='8va')
    >>> os.type
    '8va'
    >>> os.type = 15
    >>> os.type
    '15ma'
    >>> os.type = 8, 'down'
    >>> os.type
    '8vb'
    >>> print os
    <music21.spanner.Ottava 8vb >
    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)
        self._type = None # can be 8va, 8vb, 15ma, 15mb
        if 'type' in keywords.keys():
            self.type = keywords['type'] # use property
        else: # use 8 as a defualt
            self.type = '8va'

        self.placement = 'above' # can above or below, after musicxml

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Ottava %s ' % 
            self.type)
        return msg
    
    def _getType(self):
        return self._type

    def _setType(self, type):
        if common.isNum(type) and type in [8, 15]: 
            if type == 8:
                self._type = '8va'
            else:
                self._type = '15ma'
        # try to parse as list of size, dir
        elif common.isListLike(type) and len(type) >= 1: 
            stub = []
            if type[0] in [8, '8']:
                stub.append(str(type[0]))
                stub.append('v')
            elif type[0] in [15, '15']:
                stub.append(str(type[0]))
                stub.append('m')
            if len(type) >= 2 and type[1] in ['down']:
                stub.append('b')
            else: # default if not provided
                stub.append('a')        
            self._type = ''.join(stub)    
        else:
            if not common.isStr(type) or type.lower() not in [
                '8va', '8vb', '15ma', '15mb']:
                raise SpannerException(
                    'cannot create Ottava of type: %s' % type)
            self._type = type.lower()
    
    type = property(_getType, _setType, doc='''
        Get or set Ottava type. This can be set by as complete string (such as 8va or 15mb) or with a pair specifying size and direction.

        >>> from music21 import *
        >>> os = spanner.Ottava()
        >>> os.type = 15, 'down'
        >>> os.type
        '15mb'
        >>> os.type = '8vb'
        >>> os.type
        '8vb'
        ''')

    def _getShiftMagnitude(self):
        '''Get basic parameters of shift.
        '''
        if self._type.startswith('8'): return 8
        if self._type.startswith('15'): return 15

    def _getShiftDirection(self):
        '''Get basic parameters of shift.
        '''
        # an 8va means that the notes must be shifted down with the mark
        if self._type.endswith('a'): return 'down'
        # an 8vb means that the notes must be shifted upward with the mark
        if self._type.endswith('b'): return 'up'

    def getStartParameters(self):
        '''Return the parameters for the start of this spanners required by MusicXML output. 

        >>> from music21 import *
        >>> os = spanner.Ottava(type='15mb')
        >>> os.getStartParameters()
        {'type': 'up', 'size': 15}
        >>> os.getEndParameters()
        {'type': 'stop', 'size': 15}
        ''' 
        post = {}
        post['size'] = self._getShiftMagnitude()
        post['type'] = self._getShiftDirection() # up or down
        return post

    def getEndParameters(self):
        '''Return the parameters for the start of this spanner required by MusicXML output. 

        >>> from music21 import *
        >>> os = spanner.Ottava(type=8)
        >>> os.getStartParameters()
        {'type': 'down', 'size': 8}
        >>> os.getEndParameters()
        {'type': 'stop', 'size': 8}
        ''' 
        post = {}
        post['size'] = self._getShiftMagnitude()
        post['type'] = 'stop' # always stop
        return post



class Line(Spanner):
    '''A line or bracket represented as a spanner above two Notes. 

    Brackets can take many line types. 

    >>> from music21 import *
    >>> b = spanner.Line()
    >>> b.lineType = 'dotted'
    >>> b.lineType
    'dotted'
    >>> b = spanner.Line(endHeight=20)
    >>> b.endHeight 
    20

    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self._endTick = 'down' # can ne up/down/arrow/both/None
        self._startTick = 'down' # can ne up/down/arrow/both/None

        self._endHeight = None # for up/down, specified in tenths
        self._startHeight = None # for up/down, specified in tenths

        self._lineType = 'solid' # can be solid, dashed, dotted, wavy
        self.placement = 'above' # can above or below, after musicxml
        
        if 'lineType' in keywords.keys():
            self.lineType = keywords['lineType'] # use property

        if 'startTick' in keywords.keys():
            self.startTick = keywords['startTick'] # use property
        if 'endTick' in keywords.keys():
            self.endTick = keywords['endTick'] # use property
        if 'tick' in keywords.keys():
            self.tick = keywords['tick'] # use property

        if 'endHeight' in keywords.keys():
            self.endHeight = keywords['endHeight'] # use property
        if 'startHeight' in keywords.keys():
            self.startHeight = keywords['startHeight'] # use property

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Line ')
        return msg

    def _getEndTick(self):
        return self._endTick

    def _setEndTick(self, value):
        if value.lower() not in ['up', 'down', 'arrow', 'both', 'none']:
            raise SpannerException('not a valid value: %s' % value)
        self._endTick = value.lower()

    endTick = property(_getEndTick, _setEndTick, doc='''
        Get or set the endTick property.
        ''')

    def _getStartTick(self):
        return self._startTick

    def _setStartTick(self, value):
        if value.lower() not in ['up', 'down', 'arrow', 'both', 'none']:
            raise SpannerException('not a valid value: %s' % value)
        self._startTick = value.lower()

    startTick = property(_getStartTick, _setStartTick, doc='''
        Get or set the startTick property.
        ''')


    def _getTick(self):
        return self._startTick # just returning start

    def _setTick(self, value):
        if value.lower() not in ['up', 'down', 'arrow', 'both', 'none']:
            raise SpannerException('not a valid value: %s' % value)
        self._startTick = value.lower()
        self._endTick = value.lower()

    tick = property(_getTick, _setTick, doc='''
        Set the start and end tick to the same value

        >>> from music21 import *
        >>> b = spanner.Line()
        >>> b.tick = 'arrow'
        >>> b.startTick
        'arrow'
        >>> b.endTick
        'arrow'
        ''')


    def _getLineType(self):
        return self._lineType

    def _setLineType(self, value):
        if value is not None and value.lower() not in [
            'solid', 'dashed', 'dotted', 'wavy']:
            raise SpannerException('not a valid value: %s' % value)
        # not sure if we should permit setting as None
        if value is not None:
            self._lineType = value.lower()

    lineType = property(_getLineType, _setLineType, doc='''
        Get or set the lineType property. Valid line types are "solid", "dashed", "dotted", or "wavy".

        >>> from music21 import *
        >>> b = spanner.Line()
        >>> b.lineType = 'dotted'
        >>> b.lineType = 'junk'
        Traceback (most recent call last):
        SpannerException: not a valid value: junk
        ''')

    def _getEndHeight(self):
        return self._endHeight

    def _setEndHeight(self, value):
        if not common.isNum(value) and value >= 0:
            raise SpannerException('not a valid value: %s' % value)
        self._endHeight = value

    endHeight = property(_getEndHeight, _setEndHeight, doc='''
        Get or set the endHeight property.
        ''')


    def _getStartHeight(self):
        return self._startHeight

    def _setStartHeight(self, value):
        if not common.isNum(value) and value >= 0:
            raise SpannerException('not a valid value: %s' % value)
        self._startHeight = value

    startHeight = property(_getStartHeight, _setStartHeight, doc='''
        Get or set the startHeight property.
        ''')


    def getStartParameters(self):
        '''Return the parameters for the start of this spanners required by MusicXML output. 
        ''' 
        post = {}
        post['type'] = 'start'
        post['line-end'] = self._getStartTick()
        post['end-length'] = self._getStartHeight()
        return post

    def getEndParameters(self):
        '''Return the parameters for the start of this spanner required by MusicXML output. 
        ''' 
        post = {}
        post['type'] = 'stop' # always stop
        post['line-end'] = self._getEndTick()
        post['end-length'] = self._getEndHeight()
        return post


class Glissando(Spanner):
    '''A between two Notes specifying a glissando or similar alteration. Different line types can be specified. 
    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self._lineType = 'wavy'
        self._label = None

        if 'lineType' in keywords.keys():
            self.lineType = keywords['lineType'] # use property
        if 'label' in keywords.keys(): 
            self.label = keywords['label'] # use property

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.BracketLine ')
        return msg

    def _getLineType(self):
        return self._lineType

    def _setLineType(self, value):
        if value.lower() not in ['solid', 'dashed', 'dotted', 'wavy']:
            raise SpannerException('not a valid value: %s' % value)
        self._lineType = value.lower()

    lineType = property(_getLineType, _setLineType, doc='''
        Get or set the lineType property.
        ''')


    def _getLabel(self):
        return self._label

    def _setLabel(self, value):
        self._label = value

    label = property(_getLabel, _setLabel, doc='''
        Get or set the label property.
        ''')


# class DashedLine(Spanner):
#     '''A dashed line represented as a spanner between two Notes. 
#     '''
#     # this is the musicxml dashes entity
#     def __init__(self, *arguments, **keywords):
#         Spanner.__init__(self, *arguments, **keywords)
#         # note: musicxml provides a color attribute 
#         self.placement = 'above' # can above or below, after musicxml
# 
#     def __repr__(self):
#         msg = Spanner.__repr__(self)
#         msg = msg.replace(self._reprHead, '<music21.spanner.DashedLine ')
#         return msg
# 
# 

#-------------------------------------------------------------------------------
# other ideas for spanners




# associate two or more notes to be beamed together
# use a stored time signature to apply beaming values 
# class BeamingGroup(Spanner):
#     pass

# optionally define one or more Streams as a staff
# provide settings for staff presentation such as number lines
# presentation of part name?
# class Staff(Spanner):
#     pass

# collection of measures within a Score
# class System(Spanner):
#     pass
# 
# # association of all measures or streams on a page
# class Page(Spanner):
#     pass



#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testBasic(self):

        # how parts might be grouped
        from music21 import stream, spanner, note, layout
        s = stream.Score()
        p1 = stream.Part()
        p2 = stream.Part()

        sg1 = layout.StaffGroup(p1, p2)

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


    def testRepeatBracketA(self):
        from music21 import note, spanner, stream

        m1 = stream.Measure()
        rb1 = spanner.RepeatBracket(m1)
        # if added again; it is not really added, it simply is ignored
        rb1.addComponents(m1)
        self.assertEqual(len(rb1), 1)


    def testRepeatBracketB(self):
        from music21 import note, spanner, stream, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4'), 4)
        p.append(m1)
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('d#4'), 4)
        p.append(m2)
        
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g#4'), 4)
        m3.rightBarline = bar.Repeat(direction='end')
        p.append(m3)
        p.append(spanner.RepeatBracket(m3, number=1))
        
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4'), 4)
        m4.rightBarline = bar.Repeat(direction='end')
        p.append(m4)
        p.append(spanner.RepeatBracket(m4, number=2))
        
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4'), 4)
        m5.rightBarline = bar.Repeat(direction='end')
        p.append(m5)
        p.append(spanner.RepeatBracket(m5, number=3))
        
        m6 = stream.Measure()
        m6.repeatAppend(note.Note('c#5'), 4)
        p.append(m6)
        
        # all spanners should be at the part level
        self.assertEqual(len(p.spanners), 3)


    def testRepeatBracketC(self):
        from music21 import note, spanner, stream, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4'), 4)
        p.append(m1)

        m2 = stream.Measure()
        m2.repeatAppend(note.Note('d#4'), 4)
        p.append(m2)
        
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g#4'), 4)
        m3.rightBarline = bar.Repeat(direction='end')
        p.append(m3)
        rb1 = spanner.RepeatBracket(number=1)
        rb1.addComponents(m2, m3)
        self.assertEqual(len(rb1), 2)
        p.insert(0, rb1)
        
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4'), 4)
        m4.rightBarline = bar.Repeat(direction='end')
        p.append(m4)
        p.append(spanner.RepeatBracket(m4, number=2))
        
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4'), 4)
        p.append(m5)
        
        #p.show()        
        # all spanners should be at the part level
        self.assertEqual(len(p.spanners), 2)
        # have the offsets of the start of each measure
        self.assertEqual(rb1.getOffsetsBySite(p), [4.0, 8.0])
        self.assertEqual(rb1.getDurationBySite(p).quarterLength, 8.0)

        #p.show()
        raw = p.musicxml
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    

    def testRepeatBracketD(self):
        from music21 import note, spanner, stream, bar

        p = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note('c4'), 4)
        p.append(m1)
        
        m2 = stream.Measure()
        m2.repeatAppend(note.Note('d#4'), 4)
        p.append(m2)
        
        m3 = stream.Measure()
        m3.repeatAppend(note.Note('g#4'), 4)
        m3.rightBarline = bar.Repeat(direction='end')
        p.append(m3)
        rb1 = spanner.RepeatBracket(number=1)
        rb1.addComponents(m2, m3)
        self.assertEqual(len(rb1), 2)
        p.insert(0, rb1)
        
        m4 = stream.Measure()
        m4.repeatAppend(note.Note('a4'), 4)
        p.append(m4)
        
        m5 = stream.Measure()
        m5.repeatAppend(note.Note('b4'), 4)
        m5.rightBarline = bar.Repeat(direction='end')
        p.append(m5)
        
        rb2 = spanner.RepeatBracket(number=2)
        rb2.addComponents(m4, m5)
        self.assertEqual(len(rb2), 2)
        p.insert(0, rb2)
        
        m6 = stream.Measure()
        m6.repeatAppend(note.Note('a4'), 4)
        p.append(m6)
        
        m7 = stream.Measure()
        m7.repeatAppend(note.Note('b4'), 4)
        p.append(m7)
        
        m8 = stream.Measure()
        m8.repeatAppend(note.Note('a4'), 4)
        m8.rightBarline = bar.Repeat(direction='end')
        p.append(m8)
        
        rb3 = spanner.RepeatBracket(number=3)
        rb3.addComponents(m6, m8)
        self.assertEqual(len(rb3), 2)
        p.insert(0, rb3)
        
        
        m9 = stream.Measure()
        m9.repeatAppend(note.Note('a4'), 4)
        p.append(m9)
        
        m10 = stream.Measure()
        m10.repeatAppend(note.Note('b4'), 4)
        p.append(m10)
        
        m11 = stream.Measure()
        m11.repeatAppend(note.Note('a4'), 4)
        p.append(m11)
        
        m12 = stream.Measure()
        m12.repeatAppend(note.Note('a4'), 4)
        m12.rightBarline = bar.Repeat(direction='end')
        p.append(m12)
        
        rb4 = spanner.RepeatBracket(number=4)
        rb4.addComponents(m9, m10, m11, m12)
        self.assertEqual(len(rb4), 4)
        p.insert(0, rb4)
        
        #p.show()        
        # all spanners should be at the part level
        self.assertEqual(len(p.getElementsByClass('Measure')), 12)
        self.assertEqual(len(p.spanners), 4)

        self.assertEqual(rb3.getOffsetsBySite(p), [20.0, 28.0])
        self.assertEqual(rb3.getDurationBySite(p).quarterLength, 12.0)

        # have the offsets of the start of each measure
        self.assertEqual(rb4.getOffsetsBySite(p), [32.0, 36.0, 40.0, 44.0])
        self.assertEqual(rb4.getDurationBySite(p).quarterLength, 16.0)

        raw = p.musicxml
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    
        
        p1 = copy.deepcopy(p)
        raw = p1.musicxml
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    

        p2 = copy.deepcopy(p1)
        raw = p2.musicxml
        self.assertEqual(raw.find("""<ending number="1" type="start"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop"/>""")>1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start"/>""")>1, True)    
    

    def testRepeatBracketE(self):
        from music21 import note, spanner, stream, bar

        p = stream.Part()
        m1 = stream.Measure(number=1)
        m1.repeatAppend(note.Note('c4'), 1)
        p.append(m1)
        m2 = stream.Measure(number=2)
        m2.repeatAppend(note.Note('d#4'), 1) 
        p.append(m2)
        
        m3 = stream.Measure(number=3)
        m3.repeatAppend(note.Note('g#4'), 1)
        m3.rightBarline = bar.Repeat(direction='end')
        p.append(m3)
        p.append(spanner.RepeatBracket(m3, number=1))
        
        m4 = stream.Measure(number=4)
        m4.repeatAppend(note.Note('a4'), 1)
        m4.rightBarline = bar.Repeat(direction='end')
        p.append(m4)
        p.append(spanner.RepeatBracket(m4, number=2))
        
        m5 = stream.Measure(number=5)
        m5.repeatAppend(note.Note('b4'), 1)
        m5.rightBarline = bar.Repeat(direction='end')
        p.append(m5)
        p.append(spanner.RepeatBracket(m5, number=3))
        
        m6 = stream.Measure(number=6)
        m6.repeatAppend(note.Note('c#5'), 1)
        p.append(m6)
        
        # all spanners should be at the part level
        self.assertEqual(len(p.spanners), 3)

        # try copying once
        p1 = copy.deepcopy(p)
        self.assertEqual(len(p1.spanners), 3)
        m5 = p1.getElementsByClass('Measure')[-2]
        sp3 = p1.spanners[2]
        self.assertEqual(sp3.hasComponent(m5), True)
#         for m in p1.getElementsByClass('Measure'):
#             print m, id(m)
#         for sp in p1.spanners:
#             print sp, id(sp), [c for c in sp.getComponentIds()]
        #p1.show()

        p2 = copy.deepcopy(p1)
        self.assertEqual(len(p2.spanners), 3)
        m5 = p2.getElementsByClass('Measure')[-2]
        sp3 = p2.spanners[2]
        self.assertEqual(sp3.hasComponent(m5), True)


        p3 = copy.deepcopy(p2)
        self.assertEqual(len(p3.spanners), 3)
        m5 = p3.getElementsByClass('Measure')[-2]
        sp3 = p3.spanners[2]
        self.assertEqual(sp3.hasComponent(m5), True)



    def testOttavaShiftA(self):
        '''Test basic octave shift creation and output, as well as passing
        objects through make measure calls. 
        '''
        from music21 import stream, note, spanner, chord
        s = stream.Stream()
        s.repeatAppend(chord.Chord(['c-3', 'g4']), 12)
        #s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2) # default is 8va
        s.append(sp1)
        raw = s.musicxml
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="down"'), 1)
        #s.show()

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2, type='8vb')
        s.append(sp1)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="up"'), 1)

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2, type='15ma')
        s.append(sp1)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="down"'), 1)

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2, type='15mb')
        s.append(sp1)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="up"'), 1)



    def testOttavaShiftB(self):
        '''Test a single note octave
        '''
        from music21 import stream, note, spanner
        s = stream.Stream()
        n = note.Note('c4')
        sp = spanner.Ottava(n)
        s.append(n)
        s.append(sp)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="down"'), 1)

        


    def testCrescendoA(self):
        from music21 import stream, note, spanner, chord, dynamics
        s = stream.Stream()
        #s.repeatAppend(chord.Chord(['c-3', 'g4']), 12)
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        #s.insert(n1.offset, dynamics.Dynamic('fff'))
        n2 = s.notes[len(s.notes) / 2]
        #s.insert(n2.offset, dynamics.Dynamic('ppp'))
        n3 = s.notes[-1]
        #s.insert(n3.offset, dynamics.Dynamic('ff'))
        sp1 = dynamics.Diminuendo(n1, n2)
        sp2 = dynamics.Crescendo(n2, n3)
        s.append(sp1)
        s.append(sp2)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('<wedge'), 4)

        #self.assertEqual(raw.count('octave-shift'), 2)
        

    def testLineA(self):
        from music21 import stream, note, spanner, chord, dynamics
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[len(s.notes) / 2]
        n3 = s.notes[-1]
        sp1 = spanner.Line(n1, n2, startTick='up', lineType='dotted')
        sp2 = spanner.Line(n2, n3, startTick='down', lineType='dashed',
                                    endHeight=40)
        s.append(sp1)
        s.append(sp2)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('<bracket'), 4)


    def testLineB(self):
        from music21 import stream, note, spanner, chord, dynamics
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[4]
        n2 = s.notes[-1]

        n3 = s.notes[0]
        n4 = s.notes[2]

        sp1 = spanner.Line(n1, n2, startTick='up', endTick='down', lineType='solid')
        sp2 = spanner.Line(n3, n4, startTick='arrow', endTick='none', lineType='solid')

        s.append(sp1)
        s.append(sp2)

        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('<bracket'), 4)
        self.assertEqual(raw.count('line-end="arrow"'), 1)
        self.assertEqual(raw.count('line-end="none"'), 1)
        self.assertEqual(raw.count('line-end="up"'), 1)
        self.assertEqual(raw.count('line-end="down"'), 1)


    def testGlissandoA(self):
        from music21 import stream, note, spanner, chord, dynamics
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        for i, n in enumerate(s.notes):
            n.transpose(i + (i%2*12), inPlace=True)

        # note: this does not suppor glissandi between non-adjacent notes
        n1 = s.notes[0]
        n2 = s.notes[len(s.notes) / 2]
        n3 = s.notes[-1]
        sp1 = spanner.Glissando(n1, n2)
        sp2 = spanner.Glissando(n2, n3)
        sp2.lineType = 'dashed'
        s.append(sp1)
        s.append(sp2)
        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('<glissando'), 4)
        self.assertEqual(raw.count('line-type="dashed"'), 2)        


    def testGlissandoB(self):
        from music21 import stream, note, spanner, chord, dynamics
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        for i, n in enumerate(s.notes):
            n.transpose(i + (i%2*12), inPlace=True)

        # note: this does not suppor glissandi between non-adjacent notes
        n1 = s.notes[0]
        n2 = s.notes[1]
        sp1 = spanner.Glissando(n1, n2)
        sp1.lineType = 'solid'
        sp1.label = 'gliss.'
        s.append(sp1)

        #s.show()
        raw = s.musicxml
        self.assertEqual(raw.count('<glissando'), 2)
        self.assertEqual(raw.count('line-type="solid"'), 2)        
        self.assertEqual(raw.count('>gliss.<'), 1)        


#     def testDashedLineA(self):
#         from music21 import stream, note, spanner, chord, dynamics
#         s = stream.Stream()
#         s.repeatAppend(note.Note(), 12)
#         for i, n in enumerate(s.notes):
#             n.transpose(i + (i%2*12), inPlace=True)
# 
#         # note: musedata presently does not support these
#         n1 = s.notes[0]
#         n2 = s.notes[len(s.notes) / 2]
#         n3 = s.notes[-1]
#         sp1 = spanner.DashedLine(n1, n2)
#         sp2 = spanner.DashedLine(n2, n3)
#         s.append(sp1)
#         s.append(sp2)
#         #s.show()
#         raw = s.musicxml
#         self.assertEqual(raw.count('<dashes'), 4)
        

    def testOneElementSpanners(self):
        from music21 import note, spanner

        n1 = note.Note()
        sp = spanner.Spanner()
        sp.addComponents(n1)
        sp.completeStatus = True
        self.assertEqual(sp.completeStatus, True)
        self.assertEqual(sp.isFirst(n1), True)
        self.assertEqual(sp.isLast(n1), True)

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Spanner]


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof





