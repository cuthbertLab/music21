# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         spanner.py
# Purpose:      The Spanner base-class and subclasses
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
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

from music21 import exceptions21
from music21 import base
from music21 import common
from music21 import defaults
from music21 import duration

from music21.ext import six

from music21 import environment
_MOD = "spanner.py"  
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class SpannerException(exceptions21.Music21Exception):
    pass
class SpannerBundleException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
class Spanner(base.Music21Object):
    '''
    Spanner objects live on Streams in the same manner as other Music21Objects, 
    but represent and store connections between one or more other Music21Objects.

    Commonly used Spanner subclasses include the :class:`~music21.spanner.Slur`, 
    :class:`~music21.spanner.RepeatBracket`, :class:`~music21.spanner.Crescendo`, 
    and :class:`~music21.spanner.Diminuendo`
    objects.

    In some cases you will want to subclass Spanner
    for specific purposes.  

    In the first demo, we create
    a spanner to represent a written-out accelerando, such
    as Elliott Carter uses in his second string quartet (he marks them
    with an arrow).

    
    >>> class CarterAccelerandoSign(spanner.Spanner):
    ...    pass
    >>> n1 = note.Note('C4')
    >>> n2 = note.Note('D4')
    >>> n3 = note.Note('E4')
    >>> sp1 = CarterAccelerandoSign(n1, n2, n3) # or as a list: [n1, n2, n3]
    >>> sp1.getSpannedElements()
    [<music21.note.Note C>, <music21.note.Note D>, <music21.note.Note E>]
    
    We can iterate over a spanner to get the contexts:
    
    >>> print(" ".join([repr(n) for n in sp1]))
    <music21.note.Note C> <music21.note.Note D> <music21.note.Note E>
    
    Now we put the notes and the spanner into a Stream object.  Note that
    the convention is to put the spanner at the beginning of the innermost
    Stream that contains all the Spanners:
    
    >>> s = stream.Stream()
    >>> s.append([n1, n2, n3])
    >>> s.insert(0, sp1)
    
    Now we can get at the spanner in one of three ways.
    
    (1) it is just a normal element in the stream:
    
    >>> for e in s:
    ...    print(e)
    <music21.note.Note C>
    <music21.CarterAccelerandoSign <music21.note.Note C><music21.note.Note D><music21.note.Note E>>
    <music21.note.Note D>
    <music21.note.Note E>
    
    
    (2) we can get a stream of spanners (equiv. to getElementsByClass('Spanner'))
        by calling the .spanner property on the stream.
    
    >>> spannerCollection = s.spanners # a stream object
    >>> for thisSpanner in spannerCollection:
    ...     print(thisSpanner)
    <music21.CarterAccelerandoSign <music21.note.Note C><music21.note.Note D><music21.note.Note E>>


    (3) we can get the spanner by looking at the list getSpannerSites() on 
    any object that has a spanner:
    
    >>> n2.getSpannerSites()
    [<music21.CarterAccelerandoSign 
            <music21.note.Note C><music21.note.Note D><music21.note.Note E>>]
    
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
    >>> slur2.addSpannedElements([n5, n6])
    
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
    ...                print(n.nameWithOctave)
    D4
    G4
    
    Alternatively, you could iterate over the spanners
    of part1 and get their first elements:
    
    >>> for thisSpanner in part1.spanners:
    ...     firstNote = thisSpanner.getSpannedElements()[0]
    ...     print(firstNote.nameWithOctave)
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
   
   
    Implementation notes:
    
    The elements that are included in a spanner are stored in a
    Stream subclass called :class:`~music21.stream.SpannerStorage`
    found as the `.spannerStorage` attribute.  That Stream has an
    attribute called `spannerParent` which links to the original spanner.
    Thus, `spannerStorage` is smart enough to know where it's stored, but
    it makes deleting/garbage-collecting a spanner a tricky operation:
    
    Ex. Prove that the spannedElement Stream is linked to container via 
    `spannerParent`:
    
    >>> sp1.spannerStorage.spannerParent is sp1
    True


    Spanners have a `.completeStatus` attribute which can be used to find out if
    all spanned elements have been added yet. It's up to the processing agent to
    set this, but it could be useful in deciding where to append a spanner.
    
    >>> sp1.completeStatus
    False
    
    When we're done adding elements:
    
    >>> sp1.completeStatus = True
    '''
    def __init__(self, *arguments, **keywords):
        base.Music21Object.__init__(self)

        self._cache = {}     

        # store this so subclasses can replace
        if self.__module__ != '__main__':
            self._reprHead = '<' + self.__module__ + '.' + self.__class__.__name__ + ' '
        else:
            self._reprHead = '<music21.spanner.' + self.__class__.__name__ + ' '
        # store a Stream inside of Spanner
        from music21 import stream

        # create a stream subclass, spanner storage; pass a reference
        # to this spanner for getting this spanner from the SpannerStorage 
        # directly
        self.spannerStorage = stream.SpannerStorage(spannerParent=self)
        # we do not want to auto sort based on offset or class, as 
        # both are meaningless inside of this Stream (and only have meaning
        # in Stream external to this 
        self.spannerStorage.autoSort = False

        # add arguments as a list or single item
        proc = []
        for arg in arguments:
            if common.isListLike(arg):
                proc += arg
            else:
                proc.append(arg)
        self.addSpannedElements(proc)
#         if len(arguments) > 1:
#             self.spannerStorage.append(arguments)
#         elif len(arguments) == 1: # assume a list is first arg
#                 self.spannerStorage.append(c)

        # parameters that spanners need in loading and processing
        # local id is the id for the local area; used by musicxml
        self.idLocal = None
        # after all spannedElements have been gathered, setting complete
        # will mark that all parts have been gathered. 
        self.completeStatus = False


    def __repr__(self):
        msg = [self._reprHead]
        for c in self.getSpannedElements():
            objRef = c
            msg.append(repr(objRef))
        msg.append('>')
        return ''.join(msg)

    def _deepcopySubclassable(self, memo=None, ignoreAttributes=None, removeFromIgnore=None):
        '''
        see __deepcopy__ for tests and docs
        '''
        # NOTE: this is a performance critical operation        
        defaultIgnoreSet = {'_cache', 'spannerStorage'}
        if ignoreAttributes is None:
            ignoreAttributes = defaultIgnoreSet
        else:
            ignoreAttributes = ignoreAttributes | defaultIgnoreSet

        new = super(Spanner, self)._deepcopySubclassable(memo, ignoreAttributes, removeFromIgnore)

        if removeFromIgnore is not None:
            ignoreAttributes = ignoreAttributes - removeFromIgnore

        if 'spannerStorage' in ignoreAttributes:
            for c in self.spannerStorage:
                try:
                    new.spannerStorage.append(c)
                except exceptions21.StreamException:
                    pass 
                    # there is a bug where it is possible for
                    # an element to appear twice in spannerStorage
                    # this is the TODO item 

        return new
            

    def __deepcopy__(self, memo=None):
        '''
        This produces a new, independent object containing references to the same spannedElements. 
        SpannedElements linked in this Spanner must be manually re-set, likely using the 
        replaceSpannedElement() method.
        
        Notice that we put the references to the same object so that later we can replace them;
        otherwise in a deepcopy of a stream, the notes in the stream
        will become independent from the notes in the spanner.

        >>> import copy
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()

        >>> sp1 = spanner.Spanner(n1, n2, c1)
        >>> sp2 = copy.deepcopy(sp1)
        >>> len(sp2.spannerStorage)
        3
        >>> sp1 is sp2
        False
        >>> sp2[0] is sp1[0]
        True
        >>> sp2[2] is sp1[2]
        True
        >>> sp1[0] is n1
        True
        >>> sp2[0] is n1
        True
        '''
        return self._deepcopySubclassable(memo)

    #---------------------------------------------------------------------------
    # as spannedElements is private Stream, unwrap/wrap methods need to override
    # Music21Object to get at these objects 
    # this is the same as with Variants

    def purgeOrphans(self):
        self.spannerStorage.purgeOrphans()
        base.Music21Object.purgeOrphans(self)

    def purgeLocations(self, rescanIsDead=False):
        # must override Music21Object to purge locations from the contained
        # Stream
        # base method to perform purge on the Stream
        self.spannerStorage.purgeLocations(rescanIsDead=rescanIsDead)
        base.Music21Object.purgeLocations(self, rescanIsDead=rescanIsDead)

    def getSpannerStorageId(self):
        '''Return the object id of the SpannerStorage object
        '''
        return id(self.spannerStorage)

    #---------------------------------------------------------------------------
    def __getitem__(self, key):
        '''
        
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
        return self.spannerStorage.__getitem__(key)

    def __iter__(self):
        return common.Iterator(self.spannerStorage)

    def __len__(self):
        return len(self.spannerStorage._elements)


    def getSpannedElements(self):
        '''
        Return all the elements of `.spannerStorage` for this Spanner 
        as a list of Music21Objects.  

        
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> sl = spanner.Spanner()
        >>> sl.addSpannedElements(n1)
        >>> sl.getSpannedElements() == [n1]
        True
        >>> sl.addSpannedElements(n2)
        >>> sl.getSpannedElements() == [n1, n2]
        True
        >>> sl.getSpannedElementIds() == [id(n1), id(n2)]
        True
        >>> c1 = clef.TrebleClef()
        >>> sl.addSpannedElements(c1)
        >>> sl.getSpannedElements() == [n1, n2, c1] # make sure that not sorting
        True
        '''
        post = []
        # use low-level _elements access for speed; do not need to set
        # active sit or iterator
        # must pass into a new list
        for c in self.spannerStorage._elements:
#             objRef = c
#             if objRef is not None:
            post.append(c)
        return post

    def getSpannedElementsByClass(self, classFilterList):
        '''
        
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> sl = spanner.Spanner()
        >>> sl.addSpannedElements([n1, n2, c1])
        >>> sl.getSpannedElementsByClass('Note') == [n1, n2]
        True
        >>> sl.getSpannedElementsByClass('Clef') == [c1]
        True
        '''
        # returns a Stream; pack in a list
        postStream = self.spannerStorage.getElementsByClass(classFilterList)
#         post = []
#         for c in postStream:
#             post.append(objRef)

        # return raw elements list for speed; attached to a temporary stream
        return list(postStream)

    def getSpannedElementIds(self):
        '''Return all id() for all stored objects.
        '''
        if 'spannedElementIds' not in self._cache or self._cache['spannedElementIds'] is None:
            self._cache['spannedElementIds'] = [id(c) for c in self.spannerStorage._elements]
        return self._cache['spannedElementIds']


    def addSpannedElements(self, spannedElements, *arguments, **keywords):  
        '''
        Associate one or more elements with this Spanner.

        The order in which elements are added is retained and 
        may or may not be significant to the spanner. 

        
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Spanner()
        >>> sl.addSpannedElements(n1)
        >>> sl.addSpannedElements(n2, n3)
        >>> sl.addSpannedElements([n4, n5])
        >>> sl.getSpannedElementIds() == [id(n) for n in [n1, n2, n3, n4, n5]]
        True

        '''  
        # presently, this does not look for redundancies
        if not common.isListLike(spannedElements):
            spannedElements = [spannedElements]
        # assume all other arguments
        spannedElements += arguments
        # environLocal.printDebug(['addSpannedElements():', spannedElements])
        for c in spannedElements:
            if c is None:
                continue
            if not self.hasSpannedElement(c):  # not already in storage
                self.spannerStorage._appendCore(c)
            else:
                pass
                # it makes sense to not have multiple copies
                # environLocal.printDebug(['''attempting to add an object (%s) that is 
                #    already found in the SpannerStorage stream of spanner %s; 
                #    this may not be an error.''' % (c, self)])

        self.spannerStorage.elementsChanged()
        # always clear cache
        if self._cache:
            self._cache = {} 

    def hasSpannedElement(self, spannedElement):  
        '''Return True if this Spanner has the spannedElement.'''
        for c in self.spannerStorage._elements:
            if c is spannedElement:
                return True
        return False

    def replaceSpannedElement(self, old, new):
        '''
        When copying a Spanner, we need to update the 
        spanner with new references for copied  (if the Notes of a 
        Slur have been copied, that Slur's Note references need 
        references to the new Notes). Given the old spanned element, 
        this method will replace the old with the new.

        The `old` parameter can be either an object or object id. 

        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> c2 = clef.BassClef()
        >>> sl = spanner.Spanner(n1, n2, c1)
        >>> sl.replaceSpannedElement(c1, c2)
        >>> sl[-1] == c2
        True
        
        :rtype: None
        '''
        if old is None:
            return None  # do nothing
        if common.isNum(old):
            # this must be id(obj), not obj.id
            e = self.spannerStorage._getElementByObjectId(old)
            # e here is the old element that was spanned by this Spanner
            

            # environLocal.printDebug(['current Spanner.getSpannedElementIdsIds()', 
            #    self.getSpannedElementIds()])
            # environLocal.printDebug(['Spanner.replaceSpannedElement:', 'getElementById result', 
            #    e, 'old target', old])
            if e is not None:
                # environLocal.printDebug(['Spanner.replaceSpannedElement:', 'old', e, 'new', new])
                # do not do all Sites: only care about this one
                self.spannerStorage.replace(e, new, allDerived=False)
        else:
            # do not do all Sites: only care about this one
            self.spannerStorage.replace(old, new, allDerived=False)
            # environLocal.printDebug(['Spanner.replaceSpannedElement:', 'old', e, 'new', new])

        # while this Spanner now has proper elements in its spannerStorage Stream, 
        # the element replaced likely has a site left-over from its previous Spanner

        # always clear cache
        if self._cache:
            self._cache = {} 

        # environLocal.printDebug(['replaceSpannedElement()', 'id(old)', id(old), 
        #    'id(new)', id(new)])


    def isFirst(self, spannedElement):
        '''Given a spannedElement, is it first?

        
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Spanner()
        >>> sl.addSpannedElements(n1, n2, n3, n4, n5)
        >>> sl.isFirst(n2)
        False
        >>> sl.isFirst(n1)
        True
        >>> sl.isLast(n1)
        False
        >>> sl.isLast(n5)
        True
        '''
        objRef = self.spannerStorage._elements[0]
        if objRef is spannedElement:
            return True
        return False

    def getFirst(self):
        '''Get the object of the first spannedElement

        
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Spanner()
        >>> sl.addSpannedElements(n1, n2, n3, n4, n5)
        >>> sl.getFirst() is n1
        True
        '''
        return self.spannerStorage[0]

    def isLast(self, spannedElement):
        '''Given a spannedElement, is it last?  Returns True or False
        '''
        objRef = self.spannerStorage._elements[-1]

        if spannedElement is objRef:
            return True
        return False



    def getLast(self):
        '''Get the object of the first spannedElement

        
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> n3 = note.Note('e')
        >>> n4 = note.Note('c')
        >>> n5 = note.Note('d-')

        >>> sl = spanner.Spanner()
        >>> sl.addSpannedElements(n1, n2, n3, n4, n5)
        >>> sl.getLast() is n5
        True

        '''
        objRef = self.spannerStorage.elements[-1]
        return objRef


    def getOffsetsBySite(self, site):
        '''Given a site shared by all , return a list of offset values.

        
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
        for c in self.spannerStorage._elements:
            # getting site ids is fast, as weakrefs do not have to be unpacked
            if idSite in c.sites.getSiteIds():
                o = site.elementOffset(c)
                post.append(o)
        return post

    def getOffsetSpanBySite(self, site):
        '''Return the span, or min and max values, of all offsets for a given site. 
        '''
        post = self.getOffsetsBySite(site)
        return [min(post), max(post)]


    def getDurationSpanBySite(self, site):
        '''
        Return the duration span, or the distance between the first spanned element's 
        offset and the last spanned element's offset plus its duration in quarterLength. 
        
        returns a two-element tuple of the offset of the first element and the
        end-time of the last element.
        
        Offsets are relative to the `site` given; this is because it's very
        likely that different elements in the Spanner are located in different
        Streams in the hierarchy.
        '''
        # these are in order
        idSite = id(site)

        # special handling for case of a single spannedElement spanner
        if len(self.spannerStorage) == 1:
            o = site.elementOffset(self.spannerStorage[0])
            return o, o + self.spannerStorage[0].duration.quarterLength

        offsetSpannedElement = []  # store pairs
        for c in self.spannerStorage._elements:
        # for c in self.getSpannedElements():
            objRef = c
            if idSite in objRef.sites.getSiteIds():
                o = site.elementOffset(objRef)
                offsetSpannedElement.append([o, objRef])
        offsetSpannedElement.sort()  # sort by offset
        minOffset = offsetSpannedElement[0][0]
        # minSpannedElement = offsetSpannedElement[0][1]

        maxOffset = offsetSpannedElement[-1][0]
        maxSpannedElement = offsetSpannedElement[-1][1]
        if maxSpannedElement.duration is not None:
            highestTime = maxOffset + maxSpannedElement.duration.quarterLength
        else:
            highestTime = maxOffset
    
        return [minOffset, highestTime]


    def getDurationBySite(self, site):
        '''
        Return a Duration object representing the value between the 
        first spanned element's offset and the last spanned-element's 
        offset plus duration. 
        '''
        low, high = self.getDurationSpanBySite(site=site)     
        d = duration.Duration()
        d.quarterLength = high - low
        return d

#-------------------------------------------------------------------------------
class SpannerBundle(object):
    '''
    A utility object for collecting and processing 
    collections of Spanner objects. This is necessary because 
    often processing routines that happen at many different 
    levels need access to the same collection of spanners. 

    Because SpannerBundles are so commonly used with 
    :class:`~music21.stream.Stream` objects, the Stream has a 
    :attr:`~music21.stream.Stream.spannerBundle` property that stores 
    and caches a SpannerBundle of the Stream.

    If a Stream or Stream subclass is provided as an argument, 
    all Spanners on this Stream will be accumulated herein. 
    
    Not to be confused with SpannerStorage (which stores Elements that are spanned)
    '''
    def __init__(self, *arguments, **keywords):
        self._cache = {}     
        self._storage = []  # a simple List, not a Stream
        for arg in arguments:
            if common.isListLike(arg):  # spannners are iterable but not listlike...
                for e in arg:
                    self._storage.append(e)    
            # take a Stream and use its .spanners property to get all spanners            
            # elif 'Stream' in arg.classes:
            elif arg.isStream:
                for e in arg.spanners:
                    self._storage.append(e)
            # assume its a spanner
            elif 'Spanner' in arg.classes:
                self._storage.append(arg)
    
        # a special spanners, stored in storage, can be identified in the 
        # SpannerBundle as missing a spannedElement; the next obj that meets
        # the class expectation will then be assigned and the spannedElement 
        # cleared
        self._pendingSpannedElementAssignment = []

    def append(self, other):
        '''
        adds a Spanner to the bundle. Will be done automatically when adding a Spanner
        to a Stream.
        '''
        self._storage.append(other)
        if self._cache:
            self._cache = {} 

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return self._storage.__iter__()

    def __getitem__(self, key):
        return self._storage[key]

    def remove(self, item):
        '''
        Remove a stored Spanner from the bundle with an instance. 
        Each reference must have a matching id() value.
        
        >>> su1 = spanner.Slur()
        >>> su1.idLocal = 1
        >>> su2 = spanner.Slur()
        >>> su2.idLocal = 2
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> len(sb)
        2
        >>> sb
        <music21.spanner.SpannerBundle of size 2>
        
        >>> sb.remove(su2)
        >>> len(sb)
        1
        '''
        if item in self._storage:
            self._storage.remove(item)
        else:
            raise SpannerBundleException('cannot match object for removal: %s' % item)
        if self._cache:
            self._cache = {} 

    def __repr__(self):
        return '<music21.spanner.SpannerBundle of size %s>' % self.__len__()

    @property
    def list(self):
        '''
        DEPRECATED: use list(sb) instead!

        Return the bundle as a list.
        
        >>> su1 = spanner.Slur()
        >>> su1.idLocal = 1
        >>> su2 = spanner.Glissando()
        >>> su2.idLocal = 2
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> list(sb)
        [<music21.spanner.Slur >, <music21.spanner.Glissando >]
        '''
        post = []
        for x in self._storage:
            post.append(x)
        return post

    def getSpannerStorageIds(self):
        '''Return all SpannerStorage ids from all contained Spanners
        '''
        post = []
        for x in self._storage:
            post.append(x.getSpannerStorageId())
        return post

    def getByIdLocal(self, idLocal=None):
        '''Get spanners by `idLocal`.

        Returns a new SpannerBundle object

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
        '''
        Get spanners by matching status of `completeStatus` to the same attribute

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


    def getBySpannedElement(self, spannedElement):
        '''
        Given a spanner spannedElement (an object), 
        return a new SpannerBundle of all Spanner objects that have this object as a spannedElement. 
        
        >>> n1 = note.Note()
        >>> n2 = note.Note()
        >>> n3 = note.Note()
        >>> su1 = spanner.Slur(n1, n2)
        >>> su2 = spanner.Slur(n2, n3)
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.getBySpannedElement(n1).list == [su1]
        True
        >>> sb.getBySpannedElement(n2).list == [su1, su2]
        True
        >>> sb.getBySpannedElement(n3).list == [su2]
        True
        '''
        # NOTE: this is a performance critical operation
#         idTarget = id(spannedElement)
#         post = self.__class__()
#         for sp in self._storage: # storage is a list
#             if idTarget in sp.getSpannedElementIds():
#                 post.append(sp)
#         return post

        idTarget = id(spannedElement)
        cacheKey = 'getBySpannedElement-%s' % idTarget
        if cacheKey not in self._cache or self._cache[cacheKey] is None:
            post = self.__class__()
            for sp in self._storage:  # storage is a list of spanners
                if idTarget in sp.getSpannedElementIds():
                    post.append(sp)
            self._cache[cacheKey] = post
        return self._cache[cacheKey]


    def replaceSpannedElement(self, old, new):
        '''
        Given a spanner spannedElement (an object), replace all old spannedElements 
        with new spannedElements 
        for all Spanner objects contained in this bundle.

        The `old` parameter can be either an object or object id. 

        If no replacements are found, no errors are raised.
        
        Returns a list of spanners that had elements replaced.

        >>> n1 = note.Note('C')
        >>> n2 = note.Note('D')
        >>> su1 = spanner.Line(n1, n2)
        >>> su2 = spanner.Glissando(n2, n1)
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)

        >>> su1
        <music21.spanner.Line <music21.note.Note C><music21.note.Note D>>
        >>> su2
        <music21.spanner.Glissando <music21.note.Note D><music21.note.Note C>>

        >>> n3 = note.Note('E')
        >>> replacedSpanners = sb.replaceSpannedElement(n2, n3)
        >>> replacedSpanners == [su1, su2]
        True

        >>> su1
        <music21.spanner.Line <music21.note.Note C><music21.note.Note E>>
        >>> su2
        <music21.spanner.Glissando <music21.note.Note E><music21.note.Note C>>


        '''
        # environLocal.printDebug(['SpannerBundle.replaceSpannedElement()', 'old', old, 
        #    'new', new, 'len(self._storage)', len(self._storage)])

        if common.isNum(old):  # assume this is an id
            idTarget = old
        else:
            idTarget = id(old)

        replacedSpanners = []
        # post = self.__class__() # return a bundle of spanners that had changes
        for sp in self._storage:  # Spanners in a list
            # environLocal.printDebug(['looking at spanner', sp, sp.getSpannedElementIds()])

            # must check to see if this id is in this spanner
            if idTarget in sp.getSpannedElementIds():
                sp.replaceSpannedElement(old, new)
                replacedSpanners.append(sp)
                # post.append(sp)
                # environLocal.printDebug(['replaceSpannedElement()', sp, 'old', old, 
                #    'id(old)', id(old), 'new', new, 'id(new)', id(new)])

        if self._cache:
            self._cache = {} 

        return replacedSpanners

    def getByClass(self, className):
        '''
        Given a spanner class, return a bundle of all Spanners of the desired class. 
        
        >>> su1 = spanner.Slur()
        >>> su2 = layout.StaffGroup()
        >>> su3 = layout.StaffGroup()
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> sb.append(su2)
        >>> sb.append(su3)
        
        Classes can be strings (short class) or classes.
        
        >>> sb.getByClass(spanner.Slur).list == [su1]
        True
        >>> sb.getByClass('Slur').list == [su1]
        True
        >>> sb.getByClass('StaffGroup').list == [su2, su3]
        True
        '''
        # NOTE: this is called very frequently: optimize
#         post = self.__class__()
#         for sp in self._storage:
#             if isinstance(className, six.string_types):
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
                if isinstance(className, six.string_types):
                    if className in sp.classes:
                        post.append(sp)
                else:
                    if isinstance(sp, className):
                        post.append(sp)
            self._cache[cacheKey] = post
        return self._cache[cacheKey]


    def setIdLocalByClass(self, className, maxId=6):
        '''
        (See `setIdLocals()` for an explanation of what an idLocal is...)
        
        Automatically set idLocal values for all members of the provided class. 
        This is necessary in cases where spanners are newly created in 
        potentially overlapping boundaries and need to be tagged for MusicXML 
        or other output. Note that, if some Spanners already have idLocals, 
        they will be overwritten.

        The `maxId` parameter sets the largest number that is available for this
        class.  In MusicXML it is 6.

        Currently this method just iterates over the spanners of this class
        and counts the number from 1-6 and then recycles numbers.  It does
        not check whether more than 6 overlapping spanners of the same type
        exist, nor does it reset the count to 1 after all spanners of that
        class have been closed.  The example below demonstrates that the
        position of the contents of the spanner have no bearing on 
        its idLocal (since we don't even put anything into the spanners).

        
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
        # note that this overrides previous values
        for i, sp in enumerate(self.getByClass(className)):
            # 6 seems to be limit in musicxml processing
            sp.idLocal = (i % maxId) + 1
                

    def setIdLocals(self):
        '''
        Utility method for outputting MusicXML (and potentially other formats) for spanners.
        
        Each Spanner type (slur, line, glissando, etc.) in MusicXML has a number assigned to it.
        We call this number, `idLocal`.  idLocal is a number from 1 to 6.  This does not mean
        that your piece can only have six slurs total!  But it does mean that within a single
        part, only up to 6 slurs can happen simultaneously.  But as soon as a slur stops, its
        idLocal can be reused.
        
        This method set all idLocals for all classes in this SpannerBundle. 
        This will assure that each class has a unique idLocal number. 
        
        Calling this method is destructive: existing idLocal values will be lost.

        
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
        [(<music21.spanner.Slur >, 1), 
         (<music21.layout.StaffGroup >, 1), 
         (<music21.spanner.Slur >, 2)]
        '''
        classes = []
        for sp in self._storage:
            if sp.classes[0] not in classes:
                classes.append(sp.classes[0])
        for className in classes:
            self.setIdLocalByClass(className)
    
    def getByClassIdLocalComplete(self, className, idLocal, completeStatus):
        '''
        Get all spanners of a specified class `className`, an id `idLocal`, and a `completeStatus`. 
        This is a convenience routine for multiple filtering when searching for relevant Spanners 
        to pair with. 

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

    def setPendingSpannedElementAssignment(self, sp, className):
        '''
        A SpannerBundle can be set up so that a particular spanner (sp) 
        is looking for an element of class (className) to complete it. Any future
        element that matches the className which is passed to the SpannerBundle
        via freePendingSpannedElementAssignment() will get it.
        
        >>> n1 = note.Note('C')
        >>> r1 = note.Rest()
        >>> n2 = note.Note('D')
        >>> n3 = note.Note('E')
        >>> su1 = spanner.Slur([n1])
        >>> sb = spanner.SpannerBundle()
        >>> sb.append(su1)
        >>> su1.getSpannedElements()
        [<music21.note.Note C>]

        >>> n1.getSpannerSites()
        [<music21.spanner.Slur <music21.note.Note C>>]

        Now set up su1 to get the next note assigned to it.
        
        >>> sb.setPendingSpannedElementAssignment(su1, 'Note')

        Call freePendingSpannedElementAssignment to attach.

        Should not get a rest... because it is not a 'Note'
    
        >>> sb.freePendingSpannedElementAssignment(r1)
        >>> su1.getSpannedElements()
        [<music21.note.Note C>]
        
        But will get the next note:
        
        >>> sb.freePendingSpannedElementAssignment(n2)
        >>> su1.getSpannedElements()
        [<music21.note.Note C>, <music21.note.Note D>]        
        
        >>> n2.getSpannerSites()
        [<music21.spanner.Slur <music21.note.Note C><music21.note.Note D>>]
        
        And now that the assignment has been made, the pending assignment
        has been cleared, so n3 will not get assigned to the slur:
        
        >>> sb.freePendingSpannedElementAssignment(n3)
        >>> su1.getSpannedElements()
        [<music21.note.Note C>, <music21.note.Note D>]        
        
        >>> n3.getSpannerSites()
        []
        
        '''
        ref = {'spanner':sp, 'className':className}
        self._pendingSpannedElementAssignment.append(ref)

    def freePendingSpannedElementAssignment(self, spannedElementCandidate):
        '''
        Assigns and frees up a pendingSpannedElementAssignment if one is
        active and the candidate matches the class.  See 
        setPendingSpannedElementAssignment for documentation and tests.
        
        It is set up via a first-in, first-out priority.
        '''
        
        if len(self._pendingSpannedElementAssignment) == 0:
            return

        remove = None
        for i, ref in enumerate(self._pendingSpannedElementAssignment):
            # environLocal.printDebug(['calling freePendingSpannedElementAssignment()', 
            #    self._pendingSpannedElementAssignment])
            if spannedElementCandidate.isClassOrSubclass([ref['className']]):
                ref['spanner'].addSpannedElements(spannedElementCandidate)
                remove = i      
                # environLocal.printDebug(['freePendingSpannedElementAssignment()', 
                #    'added spannedElement', ref['spanner']])
                break
        if remove is not None:
            self._pendingSpannedElementAssignment.pop(remove)




#-------------------------------------------------------------------------------
# connect two or more notes anywhere in the score
class Slur(Spanner):
    '''A slur represented as a spanner between two Notes. 

    The `idLocal` attribute, defined in the Spanner base class, 
    is used to mark start and end tags of potentially overlapping indicators.
    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)
        self.placement = None  # can above or below, after musicxml
        # line type is only needed as a start parameter; suggest that
        # this should also have start/end parameters
        self.lineType = None  # can be "dashed" or None

    # TODO: add property for placement

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Slur ')
        return msg
    
#-------------------------------------------------------------------------------
class MultiMeasureRest(Spanner):
    '''
    A grouping symbol that indicates that a collection of rests lasts
    multiple measures.
    '''    
    _DOC_ATTR = {'useSymbols': '''boolean to indicate whether rest symbols 
                                    (breve, longa, etc.) should be used when
                                    displaying the rest. Your music21 inventor
                                    is a medievalist, so this defaults to True.

                                    Change defaults.multiMeasureRestUseSymbols to
                                    change globally.
                                    ''',
                 'maxSymbols': '''int, specifying the maximum number of rests
                                     to display as symbols.  Default is 11.
                                     If useSymbols is False then this setting
                                     does nothing.
                                     
                                     Change defaults.multiMeasureRestMaxSymbols to
                                     change globally.                                   
                                     '''
                 }
    
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)
        self._overriddenNumber = None
        self.useSymbols = keywords.get('useSymbols', defaults.multiMeasureRestUseSymbols)
        self.maxSymbols = keywords.get('maxSymbols', defaults.multiMeasureRestMaxSymbols)
        
    def __repr__(self):
        return "<music21.spanner.MultiMeasureRest {} measure{}>".format(self.numRests, 
                                        "s" if self.numRests != 1 else "")
        
    @property
    def numRests(self):
        '''
        Returns the number of measures involved in the
        multi-measure rest.
        
        Calculated automatically from the number of rests in
        the spanner.  Or can be set manually to override the number.
        
        >>> mmr = spanner.MultiMeasureRest()
        >>> for i in range(6):
        ...     mmr.addSpannedElements([note.Rest(type='whole')])
        >>> mmr.numRests
        6
        >>> mmr.numRests = 10
        >>> mmr.numRests
        10
        '''
        if self._overriddenNumber is not None:
            return self._overriddenNumber
        else:
            return len(self)

    @numRests.setter
    def numRests(self, overridden):
        self._overriddenNumber = overridden
    
#-------------------------------------------------------------------------------
# first/second repeat bracket
class RepeatBracket(Spanner):
    '''
    A grouping of one or more measures, presumably in sequence, that mark an alternate repeat. 

    These gather what are sometimes called first-time bars and second-time bars.

    It is assumed that numbering starts from 1. Numberings above 2 are permitted. 
    The `number` keyword argument can be used to pass in the desired number. 
    
    `overrideDisplay` if set will display something other than the number.  For instance
    `ouvert` and `clos` for medieval music.  However, if you use it for something like "1-3"
    be sure to set number properly too.

    
    >>> m = stream.Measure()
    >>> sp = spanner.RepeatBracket(m, number=1)
    >>> sp # can be one or more measures
    <music21.spanner.RepeatBracket 1 <music21.stream.Measure 0 offset=0.0>>

    >>> sp.number = 3
    >>> sp 
    <music21.spanner.RepeatBracket 3 <music21.stream.Measure 0 offset=0.0>>
    >>> sp.getNumberList() # the list of repeat numbers
    [3]
    >>> sp.number
    '3'
    
    >>> sp.number = '1-3' # range of repeats
    >>> sp.getNumberList()
    [1, 2, 3]
    >>> sp.number
    '1-3'
    
    >>> sp.number = [2,3] # range of repeats
    >>> sp.getNumberList()
    [2, 3]
    >>> sp.number
    '2, 3'

    >>> sp.number = '1, 2, 3' # comma separated
    >>> sp.getNumberList()
    [1, 2, 3]
    >>> sp.number
    '1-3'


    >>> sp.number = '1, 2, 3, 7' # disjunct
    >>> sp.getNumberList()
    [1, 2, 3, 7]
    >>> sp.number
    '1, 2, 3, 7'
    >>> sp.overrideDisplay = '1-3, 7' # does not work for number.
    
    
    '''
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self._number = None
        self._numberRange = []  # store a range, inclusive of the single number assignment
        self._numberSpanIsAdjacent = None
        self._numberSpanIsContiguous = None
        self.overrideDisplay = None

        if 'number' in keywords:
            self.number = keywords['number']

    # property to enforce numerical numbers
    def _getNumber(self):
        '''
        This must return a string, as we may have single numbers or lists. 
        For a raw numerical list, use getNumberList() below.
        '''
        if len(self._numberRange) == 1:
            return str(self._number)
        else:
            if self._numberSpanIsContiguous is False:
                return ', '.join([str(x) for x in self._numberRange])                
            elif self._numberSpanIsAdjacent:
                return '%s, %s' % (self._numberRange[0], self._numberRange[-1])
            else:  # range of values
                return '%s-%s' % (self._numberRange[0], self._numberRange[-1])

    def _setNumber(self, value):
        '''
        Set the bracket number. There may be range of values provided
        '''
        if value in ['', None]:
            # assume this is 1 
            self._numberRange = [1]
            self._number = 1
        elif common.isIterable(value):
            self._numberRange = []  # clear
            for x in value:
                if common.isNum(x):
                    self._numberRange.append(x)
                else:
                    raise SpannerException(
                        'number for RepeatBracket must be a number, not %r' % value)
            self._number = min(self._numberRange)
            self._numberSpanIsContiguous = common.contiguousList(self._numberRange)
            if (len(self._numberRange) == 2) and (self._numberRange[0] == self._numberRange[1] - 1):
                self._numberSpanIsAdjacent = True
            else:
                self._numberSpanIsAdjacent = False

        elif isinstance(value, six.string_types):
            # assume defined a range with a dash; assumed inclusive
            if '-' in value:
                start, end = value.split('-')
                self._numberRange = list(range(int(start), int(end) + 1))
                self._numberSpanIsAdjacent = False
                self._numberSpanIsContiguous = True

            elif ',' in value:
                self._numberRange = []  # clear
                for x in value.split(','):
                    x = int(x.strip())
                    self._numberRange.append(x)
                self._number = min(self._numberRange)
                
                # returns bool 
                self._numberSpanIsContiguous = common.contiguousList(self._numberRange)
                if ((len(self._numberRange) == 2)
                        and (self._numberRange[0] == self._numberRange[1] - 1)):
                    self._numberSpanIsAdjacent = True
                else:
                    self._numberSpanIsAdjacent = False
                
            elif value.isdigit():
                self._numberRange.append(int(value))
            else:
                raise SpannerException('number for RepeatBracket must be a number, not %r' % value)
            self._number = min(self._numberRange)
        elif common.isNum(value):
            self._numberRange = []  # clear
            self._number = value
            if value not in self._numberRange:
                self._numberRange.append(value)
        else:
            raise SpannerException('number for RepeatBracket must be a number, not %r' % value)

    number = property(_getNumber, _setNumber, doc='''
        ''')

    def getNumberList(self):
        '''Get a contiguous list of repeat numbers that are applicable for this instance.
        
        Will always have at least one element, but [0] means undefined
        
        >>> rb = spanner.RepeatBracket()
        >>> rb.getNumberList()
        [0]
        
        >>> rb.number = '1,2'
        >>> rb.getNumberList()
        [1, 2]
        '''
        nr = self._numberRange
        if not nr:
            return [0]
        else:
            return nr

    def __repr__(self):
        msg = Spanner.__repr__(self)
        if self.overrideDisplay is not None:
            msg = msg.replace(self._reprHead,
                              '<music21.spanner.RepeatBracket %s' % self.overrideDisplay)
        elif self.number is not None:
            msg = msg.replace(self._reprHead,
                              '<music21.spanner.RepeatBracket %s ' % self.number)
        else:
            msg = msg.replace(self._reprHead,
                              '<music21.spanner.RepeatBracket ')
        return msg




#-------------------------------------------------------------------------------
# line-based spanners

class Ottava(Spanner):
    '''An octave shift line

    
    >>> ottava = spanner.Ottava(type='8va')
    >>> ottava.type
    '8va'
    >>> ottava.type = 15
    >>> ottava.type
    '15ma'
    >>> ottava.type = (8, 'down')
    >>> ottava.type
    '8vb'
    >>> print(ottava)
    <music21.spanner.Ottava 8vb >


    All valid types

    >>> ottava.validOttavaTypes
    ('8va', '8vb', '15ma', '15mb')

    '''
    validOttavaTypes = ('8va', '8vb', '15ma', '15mb')
    
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)
        self._type = None  # can be 8va, 8vb, 15ma, 15mb
        if 'type' in keywords:
            self.type = keywords['type']  # use property
        else:  # use 8 as a defualt
            self.type = '8va'

        self.placement = 'above'  # can above or below, after musicxml

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Ottava %s ' % 
            self.type)
        return msg
    
    def _getType(self):
        return self._type

    def _setType(self, newType):
        if common.isNum(newType) and newType in [8, 15]: 
            if newType == 8:
                self._type = '8va'
            else:
                self._type = '15ma'
        # try to parse as list of size, dir
        elif common.isListLike(newType) and len(newType) >= 1: 
            stub = []
            if newType[0] in [8, '8']:
                stub.append(str(newType[0]))
                stub.append('v')
            elif newType[0] in [15, '15']:
                stub.append(str(newType[0]))
                stub.append('m')
            if len(newType) >= 2 and newType[1] in ['down']:
                stub.append('b')
            else:  # default if not provided
                stub.append('a')        
            self._type = ''.join(stub)    
        else:
            if (not isinstance(newType, six.string_types) 
                    or newType.lower() not in self.validOttavaTypes):
                raise SpannerException(
                    'cannot create Ottava of type: %s' % newType)
            self._type = newType.lower()
    
    type = property(_getType, _setType, doc='''
        Get or set Ottava type. This can be set by as complete string 
        (such as 8va or 15mb) or with a pair specifying size and direction.
 
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
        if self._type.startswith('8'): 
            return 8
        elif self._type.startswith('15'): 
            return 15
        else: 
            raise SpannerException("Cannot get shift magnitude from %s" % self._type)

    def _getShiftDirection(self):
        '''Get basic parameters of shift.
        '''
        # an 8va means that the notes must be shifted down with the mark
        if self._type.endswith('a'): 
            return 'down'
        # an 8vb means that the notes must be shifted upward with the mark
        if self._type.endswith('b'): 
            return 'up'

    def getStartParameters(self):
        '''
        Return a dictionary of the parameters for the start of this spanners 
        (required by MusicXML output). 
        
        TODO: Move to m21ToXml
        
        >>> ottava = spanner.Ottava(type='15mb')
        >>> st = ottava.getStartParameters()
        >>> st['type']
        'up'
        >>> st['size']
        15
        >>> en = ottava.getEndParameters()
        >>> en['type']
        'stop'
        >>> en['size']
        15
        ''' 
        post = {}
        post['size'] = self._getShiftMagnitude()
        post['type'] = self._getShiftDirection()  # up or down
        return post

    def getEndParameters(self):
        '''
        Return a dict of the parameters for the start of this spanner required by MusicXML output. 

        >>> ottava = spanner.Ottava(type=8)
        >>> st = ottava.getStartParameters()
        >>> st['type']
        'down'
        >>> st['size']
        8
        >>> en = ottava.getEndParameters()
        >>> en['type']
        'stop'
        >>> en['size']
        8
        ''' 
        post = {}
        post['size'] = self._getShiftMagnitude()
        post['type'] = 'stop'  # always stop
        return post



class Line(Spanner):
    '''A line or bracket represented as a spanner above two Notes. 

    Brackets can take many line types. 

    
    >>> b = spanner.Line()
    >>> b.lineType = 'dotted'
    >>> b.lineType
    'dotted'
    >>> b = spanner.Line(endHeight=20)
    >>> b.endHeight 
    20

    '''
    validLineTypes = ('solid', 'dashed', 'dotted', 'wavy')

    def __init__(self, *arguments, **keywords):
        
        Spanner.__init__(self, *arguments, **keywords)

        self._endTick = 'down'  # can ne up/down/arrow/both/None
        self._startTick = 'down'  # can ne up/down/arrow/both/None

        self._endHeight = None  # for up/down, specified in tenths
        self._startHeight = None  # for up/down, specified in tenths

        self._lineType = 'solid'  # can be solid, dashed, dotted, wavy
        self.placement = 'above'  # can above or below, after musicxml
        
        if 'lineType' in keywords:
            self.lineType = keywords['lineType']  # use property

        if 'startTick' in keywords:
            self.startTick = keywords['startTick']  # use property
        if 'endTick' in keywords:
            self.endTick = keywords['endTick']  # use property
        if 'tick' in keywords:
            self.tick = keywords['tick']  # use property

        if 'endHeight' in keywords:
            self.endHeight = keywords['endHeight']  # use property
        if 'startHeight' in keywords:
            self.startHeight = keywords['startHeight']  # use property

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
        return self._startTick  # just returning start

    def _setTick(self, value):
        if value.lower() not in ['up', 'down', 'arrow', 'both', 'none']:
            raise SpannerException('not a valid value: %s' % value)
        self._startTick = value.lower()
        self._endTick = value.lower()

    tick = property(_getTick, _setTick, doc='''
        Set the start and end tick to the same value

        
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
        if value is not None and value.lower() not in self.validLineTypes:
            raise SpannerException('not a valid value: %s' % value)
        # not sure if we should permit setting as None
        if value is not None:
            self._lineType = value.lower()

    lineType = property(_getLineType, _setLineType, doc='''
        Get or set the lineType property. Valid line types are listed in .validLineTypes.
        
        >>> b = spanner.Line()
        >>> b.lineType = 'dotted'
        >>> b.lineType = 'navyblue'
        Traceback (most recent call last):
        music21.spanner.SpannerException: not a valid value: navyblue

        >>> b.validLineTypes
        ('solid', 'dashed', 'dotted', 'wavy')
        ''')

    def _getEndHeight(self):
        return self._endHeight

    def _setEndHeight(self, value):
        if not common.isNum(value) and value is not None and value >= 0:
            raise SpannerException('not a valid value: %s' % value)
        self._endHeight = value

    endHeight = property(_getEndHeight, _setEndHeight, doc='''
        Get or set the endHeight property.
        ''')


    def _getStartHeight(self):
        return self._startHeight

    def _setStartHeight(self, value):
        if not common.isNum(value) and value is not None and value >= 0:
            raise SpannerException('not a valid value: %s' % value)
        self._startHeight = value

    startHeight = property(_getStartHeight, _setStartHeight, doc='''
        Get or set the startHeight property.
        ''')


    def getStartParameters(self):
        '''
        Return a dict of the parameters for the start of this spanners required by MusicXML output. 
        ''' 
        post = {}
        post['type'] = 'start'
        post['line-end'] = self._getStartTick()
        post['end-length'] = self._getStartHeight()
        return post

    def getEndParameters(self):
        '''
        Return a dict of the parameters for the start of this spanner required by MusicXML output. 
        ''' 
        post = {}
        post['type'] = 'stop'  # always stop
        post['line-end'] = self._getEndTick()
        post['end-length'] = self._getEndHeight()
        return post


class Glissando(Spanner):
    '''
    A between two Notes specifying a glissando or similar alteration. 
    Different line types can be specified. 
    '''
    validLineTypes = ('solid', 'dashed', 'dotted', 'wavy')
    
    def __init__(self, *arguments, **keywords):
        Spanner.__init__(self, *arguments, **keywords)

        self._lineType = 'wavy'
        self._label = None

        if 'lineType' in keywords:
            self.lineType = keywords['lineType']  # use property
        if 'label' in keywords: 
            self.label = keywords['label']  # use property

    def __repr__(self):
        msg = Spanner.__repr__(self)
        msg = msg.replace(self._reprHead, '<music21.spanner.Glissando ')
        return msg

    def _getLineType(self):
        return self._lineType

    def _setLineType(self, value):
        if value.lower() not in self.validLineTypes:
            raise SpannerException('not a valid value: %s' % value)
        self._lineType = value.lower()

    lineType = property(_getLineType, _setLineType, doc='''
        Get or set the lineType property. See Line for valid line types
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

    def setUp(self):
        from music21.musicxml.m21ToXml import GeneralObjectExporter
        self.GEX = GeneralObjectExporter()

    def xmlStr(self, obj):
        xmlBytes = self.GEX.parse(obj)
        if six.PY2:
            return xmlBytes
        else:
            return xmlBytes.decode('utf-8')
        
    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

    def testBasic(self):

        # how parts might be grouped
        from music21 import stream, note, layout
        s = stream.Score()
        p1 = stream.Part()
        p2 = stream.Part()

        sg1 = layout.StaffGroup(p1, p2)

        # place all on Stream
        s.insert(0, p1)
        s.insert(0, p2)
        s.insert(0, sg1)    

        self.assertEqual(len(s), 3)
        self.assertEqual(sg1.getSpannedElements(), [p1, p2])
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
        slur1.addSpannedElements([n1, n3])

        p1.append(slur1)

        self.assertEqual(len(s), 3)
        self.assertEqual(slur1.getSpannedElements(), [n1, n3])

        self.assertEqual(slur1.getOffsetsBySite(p1), [0.0, 2.0])
        self.assertEqual(slur1.getOffsetSpanBySite(p1), [0.0, 2.0])

        # a note can access what spanners it is part of 
        self.assertEqual(n1.getSpannerSites(), [slur1])

        # can a spanner hold spanners: yes
        sl1 = Slur()
        sl2 = Slur()
        sl3 = Slur()
        sp = Spanner([sl1, sl2, sl3])
        self.assertEqual(len(sp.getSpannedElements()), 3)
        self.assertEqual(sp.getSpannedElements(), [sl1, sl2, sl3])

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

        # how slurs might be defined
        n1 = note.Note()
        # n2 = note.Note()
        n3 = note.Note()

        su1 = Slur()
        su1.addSpannedElements([n1, n3])

        self.assertEqual(n1.getSpannerSites(), [su1])
        self.assertEqual(n3.getSpannerSites(), [su1])

        su2 = copy.deepcopy(su1)

        self.assertEqual(su1.getSpannedElements(), [n1, n3])
        self.assertEqual(su2.getSpannedElements(), [n1, n3])

        self.assertEqual(n1.getSpannerSites(), [su1, su2])
        self.assertEqual(n3.getSpannerSites(), [su1, su2])


        sb1 = spanner.SpannerBundle(su1, su2)
        sb2 = copy.deepcopy(sb1)
        self.assertEqual(sb1[0].getSpannedElements(), [n1, n3])
        self.assertEqual(sb2[0].getSpannedElements(), [n1, n3])
        # spanners stored within are not the same objects
        self.assertEqual(id(sb2[0]) != id(sb1[0]), True)



    def testReplaceSpannedElement(self):
        from music21 import note, spanner

        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()
        n4 = note.Note()
        n5 = note.Note()

        su1 = spanner.Slur()
        su1.addSpannedElements([n1, n3])

        self.assertEqual(su1.getSpannedElements(), [n1, n3])
        self.assertEqual(n1.getSpannerSites(), [su1])

        su1.replaceSpannedElement(n1, n2)
        self.assertEqual(su1.getSpannedElements(), [n2, n3])
        # this note now has no spanner sites
        self.assertEqual(n1.getSpannerSites(), [])
        self.assertEqual(n2.getSpannerSites(), [su1])

        # replace n2 w/ n1
        su1.replaceSpannedElement(n2, n1)
        self.assertEqual(su1.getSpannedElements(), [n1, n3])
        self.assertEqual(n2.getSpannerSites(), [])
        self.assertEqual(n1.getSpannerSites(), [su1])


        su2 = spanner.Slur()
        su2.addSpannedElements([n3, n4])

        su3 = spanner.Slur()
        su3.addSpannedElements([n4, n5])


        # n1a = note.Note()
        # n2a = note.Note()
        n3a = note.Note()
        n4a = note.Note()
        # n5a = note.Note()

        sb1 = spanner.SpannerBundle(su1, su2, su3)
        self.assertEqual(len(sb1), 3)
        self.assertEqual(sb1.list, [su1, su2, su3])

        # n3 is found in su1 and su2

        sb1.replaceSpannedElement(n3, n3a)
        self.assertEqual(len(sb1), 3)
        self.assertEqual(sb1.list, [su1, su2, su3])

        self.assertEqual(sb1[0].getSpannedElements(), [n1, n3a])
        # check su2
        self.assertEqual(sb1[1].getSpannedElements(), [n3a, n4])

        sb1.replaceSpannedElement(n4, n4a)
        self.assertEqual(sb1[1].getSpannedElements(), [n3a, n4a])

        # check su3
        self.assertEqual(sb1[2].getSpannedElements(), [n4a, n5])


    def testRepeatBracketA(self):
        from music21 import spanner, stream

        m1 = stream.Measure()
        rb1 = spanner.RepeatBracket(m1)
        # if added again; it is not really added, it simply is ignored
        rb1.addSpannedElements(m1)
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
        rb1.addSpannedElements(m2, m3)
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
        
        # p.show()        
        # all spanners should be at the part level
        self.assertEqual(len(p.spanners), 2)
        # have the offsets of the start of each measure
        self.assertEqual(rb1.getOffsetsBySite(p), [4.0, 8.0])
        self.assertEqual(rb1.getDurationBySite(p).quarterLength, 8.0)

        # p.show()
        raw = self.xmlStr(p)
        self.assertEqual(raw.find("""<ending number="1" type="start" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start" />""") > 1, True)    

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
        rb1.addSpannedElements(m2, m3)
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
        rb2.addSpannedElements(m4, m5)
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
        rb3.addSpannedElements(m6, m8)
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
        rb4.addSpannedElements(m9, m10, m11, m12)
        self.assertEqual(len(rb4), 4)
        p.insert(0, rb4)
        
        # p.show()        
        # all spanners should be at the part level
        self.assertEqual(len(p.getElementsByClass('Measure')), 12)
        self.assertEqual(len(p.spanners), 4)

        self.assertEqual(rb3.getOffsetsBySite(p), [20.0, 28.0])
        self.assertEqual(rb3.getDurationBySite(p).quarterLength, 12.0)

        # have the offsets of the start of each measure
        self.assertEqual(rb4.getOffsetsBySite(p), [32.0, 36.0, 40.0, 44.0])
        self.assertEqual(rb4.getDurationBySite(p).quarterLength, 16.0)
        raw = self.xmlStr(p)
        self.assertEqual(raw.find("""<ending number="1" type="start" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start" />""") > 1, True)    
        
        p1 = copy.deepcopy(p)
        raw = self.xmlStr(p1)
        self.assertEqual(raw.find("""<ending number="1" type="start" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start" />""") > 1, True)    

        p2 = copy.deepcopy(p1)
        raw = self.xmlStr(p2)
        self.assertEqual(raw.find("""<ending number="1" type="start" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="stop" />""") > 1, True)    
        self.assertEqual(raw.find("""<ending number="2" type="start" />""") > 1, True)    
    

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
        self.assertEqual(sp3.hasSpannedElement(m5), True)
#         for m in p1.getElementsByClass('Measure'):
#             print m, id(m)
#         for sp in p1.spanners:
#             print sp, id(sp), [c for c in sp.getSpannedElementIds()]
        # p1.show()

        p2 = copy.deepcopy(p1)
        self.assertEqual(len(p2.spanners), 3)
        m5 = p2.getElementsByClass('Measure')[-2]
        sp3 = p2.spanners[2]
        self.assertEqual(sp3.hasSpannedElement(m5), True)


        p3 = copy.deepcopy(p2)
        self.assertEqual(len(p3.spanners), 3)
        m5 = p3.getElementsByClass('Measure')[-2]
        sp3 = p3.spanners[2]
        self.assertEqual(sp3.hasSpannedElement(m5), True)



    def testOttavaShiftA(self):
        '''Test basic octave shift creation and output, as well as passing
        objects through make measure calls. 
        '''
        from music21 import stream, note, spanner, chord

        s = stream.Stream()
        s.repeatAppend(chord.Chord(['c-3', 'g4']), 12)
        # s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2)  # default is 8va
        s.append(sp1)
        raw = self.xmlStr(s)
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="down"'), 1)
        # s.show()

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2, type='8vb')
        s.append(sp1)
        # s.show()
        raw = self.xmlStr(s)
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="up"'), 1)

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2, type='15ma')
        s.append(sp1)
        # s.show()
        raw = self.xmlStr(s)
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="down"'), 1)

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[-1]
        sp1 = spanner.Ottava(n1, n2, type='15mb')
        s.append(sp1)
        # s.show()
        raw = self.xmlStr(s)
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
        # s.show()
        raw = self.xmlStr(s)
        self.assertEqual(raw.count('octave-shift'), 2)
        self.assertEqual(raw.count('type="down"'), 1)

        


    def testCrescendoA(self):
        from music21 import stream, note, dynamics
        s = stream.Stream()
#         n1 = note.Note('C')
#         n2 = note.Note('D')
#         n3 = note.Note('E')
#          
#         s.append(n1)
#         s.append(note.Note('A'))
#         s.append(n2)
#         s.append(note.Note('B'))
#         s.append(n3)
         
        # s.repeatAppend(chord.Chord(['c-3', 'g4']), 12)
        s.repeatAppend(note.Note(type='half'), 4)
#        n1 = s._elements[0]
        n1 = s.notes[0]
        n1.pitch.step = 'D'
        # s.insert(n1.offset, dynamics.Dynamic('fff'))
        # n2 = s._elements[2]
        n2 = s.notes[len(s.notes) // 2]
        n2.pitch.step = 'E'
        # s.insert(n2.offset, dynamics.Dynamic('ppp'))
        # n3 = s._elements[-1]
        n3 = s.notes[-1]
        n3.pitch.step = 'F'
        # s.insert(n3.offset, dynamics.Dynamic('ff'))
        sp1 = dynamics.Diminuendo(n1, n2)
        sp2 = dynamics.Crescendo(n2, n3)
        s.append(sp1)
        s.append(sp2)
        # s._reprText()
        # s.show('t')
        raw = self.xmlStr(s)
        # print(raw)
        self.assertEqual(raw.count('<wedge'), 4)

        # self.assertEqual(raw.count('octave-shift'), 2)
        

    def testLineA(self):
        from music21 import stream, note, spanner

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        n1 = s.notes[0]
        n2 = s.notes[len(s.notes) // 2]
        n3 = s.notes[-1]
        sp1 = spanner.Line(n1, n2, startTick='up', lineType='dotted')
        sp2 = spanner.Line(n2, n3, startTick='down', lineType='dashed',
                                    endHeight=40)
        s.append(sp1)
        s.append(sp2)
        # s.show('t')
        raw = self.xmlStr(s)
        # print(raw)
        self.assertEqual(raw.count('<bracket'), 4)


    def testLineB(self):
        from music21 import stream, note, spanner

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

        # s.show()
        raw = self.xmlStr(s)
        self.assertEqual(raw.count('<bracket'), 4)
        self.assertEqual(raw.count('line-end="arrow"'), 1)
        self.assertEqual(raw.count('line-end="none"'), 1)
        self.assertEqual(raw.count('line-end="up"'), 1)
        self.assertEqual(raw.count('line-end="down"'), 1)


    def testGlissandoA(self):
        from music21 import stream, note, spanner

        s = stream.Stream()
        s.repeatAppend(note.Note(), 3)
        for i, n in enumerate(s.notes):
            n.transpose(i + (i % 2 * 12), inPlace=True)

        # note: this does not suppor glissandi between non-adjacent notes
        n1 = s.notes[0]
        n2 = s.notes[len(s.notes) // 2]
        n3 = s.notes[-1]
        sp1 = spanner.Glissando(n1, n2)
        sp2 = spanner.Glissando(n2, n3)
        sp2.lineType = 'dashed'
        s.append(sp1)
        s.append(sp2)
        s = s.makeNotation()
        # s.show('t')
        raw = self.xmlStr(s)
        # print(raw)
        self.assertEqual(raw.count('<glissando'), 4)
        self.assertEqual(raw.count('line-type="dashed"'), 2)        


    def testGlissandoB(self):
        from music21 import stream, note, spanner

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        for i, n in enumerate(s.notes):
            n.transpose(i + (i % 2 * 12), inPlace=True)

        # note: this does not suppor glissandi between non-adjacent notes
        n1 = s.notes[0]
        n2 = s.notes[1]
        sp1 = spanner.Glissando(n1, n2)
        sp1.lineType = 'solid'
        sp1.label = 'gliss.'
        s.append(sp1)

        # s.show()
        raw = self.xmlStr(s)
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
#         n2 = s.notes[len(s.notes) // 2]
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
        sp.addSpannedElements(n1)
        sp.completeStatus = True
        self.assertEqual(sp.completeStatus, True)
        self.assertEqual(sp.isFirst(n1), True)
        self.assertEqual(sp.isLast(n1), True)

    def testRemoveSpanners(self):
        from music21 import stream
        from music21 import note
        
        p = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m1.number = 1
        m2.number = 2
        n1 = note.Note("C#4", type='whole')
        n2 = note.Note("D#4", type='whole')
        m1.insert(0, n1)
        m2.insert(0, n2)
        p.append(m1)
        p.append(m2)
        sl = Slur([n1, n2])
        p.insert(0, sl)
        for x in p:
            if "Spanner" in x.classes:
                p.remove(x)
        self.assertEqual(len(p.spanners), 0)

    def testFreezeSpanners(self):
        from music21 import stream
        from music21 import note
        from music21 import converter

        p = stream.Part()
        m1 = stream.Measure()
        m2 = stream.Measure()
        m1.number = 1
        m2.number = 2
        n1 = note.Note("C#4", type='whole')
        n2 = note.Note("D#4", type='whole')
        m1.insert(0, n1)
        m2.insert(0, n2)
        p.append(m1)
        p.append(m2)
        sl = Slur([n1, n2])
        p.insert(0, sl)
        unused_data = converter.freezeStr(p, fmt='pickle')

    def testDeepcopyJustSpannerAndNotes(self):
        from music21 import note, clef
        n1 = note.Note('g')
        n2 = note.Note('f#')
        c1 = clef.AltoClef()

        sp1 = Spanner(n1, n2, c1)
        sp2 = copy.deepcopy(sp1)
        self.assertEqual(len(sp2.spannerStorage), 3)
        self.assertIsNot(sp1, sp2)
        self.assertIs(sp2[0], sp1[0])
        self.assertIs(sp2[2], sp1[2])
        self.assertIs(sp1[0], n1)
        self.assertIs(sp2[0], n1)

    def testDeepcopySpannerInStreamNotNotes(self):
        from music21 import note, clef, stream
        n1 = note.Note('g')
        n2 = note.Note('f#')
        c1 = clef.AltoClef()

        sp1 = Spanner(n1, n2, c1)
        st1 = stream.Stream()
        st1.insert(0.0, sp1)
        st2 = copy.deepcopy(st1)

        sp2 = st2.spanners[0]
        self.assertEqual(len(sp2.spannerStorage), 3)
        self.assertIsNot(sp1, sp2)
        self.assertIs(sp2[0], sp1[0])
        self.assertIs(sp2[2], sp1[2])
        self.assertIs(sp1[0], n1)
        self.assertIs(sp2[0], n1)
        
    def testDeepcopyNotesInStreamNotSpanner(self):
        from music21 import note, clef, stream
        n1 = note.Note('g')
        n2 = note.Note('f#')
        c1 = clef.AltoClef()

        sp1 = Spanner(n1, n2, c1)
        st1 = stream.Stream()
        st1.insert(0.0, n1)
        st1.insert(1.0, n2)
        st2 = copy.deepcopy(st1)

        n3 = st2.notes[0]
        self.assertEqual(len(n3.getSpannerSites()), 1)
        sp2 = n3.getSpannerSites()[0]
        self.assertIs(sp1, sp2)
        self.assertIsNot(n1, n3)
        self.assertIs(sp2[2], sp1[2])
        self.assertIs(sp1[0], n1)
        self.assertIs(sp2[0], n1)


    def testDeepcopyNotesAndSpannerInStream(self):
        from music21 import note, stream
        n1 = note.Note('g')
        n2 = note.Note('f#')

        sp1 = Spanner(n1, n2)
        st1 = stream.Stream()
        st1.insert(0.0, sp1)
        st1.insert(0.0, n1)
        st1.insert(1.0, n2)
        st2 = copy.deepcopy(st1)

        n3 = st2.notes[0]
        self.assertEqual(len(n3.getSpannerSites()), 1)
        sp2 = n3.getSpannerSites()[0]
        self.assertIsNot(sp1, sp2)
        self.assertIsNot(n1, n3)
        
        sp3 = st2.spanners[0]
        self.assertIs(sp2, sp3)
        self.assertIs(sp1[0], n1)
        self.assertIs(sp2[0], n3)

    def testDeepcopyStreamWithSpanners(self):
        from music21 import note, stream
        n1 = note.Note()
        su1 = Slur((n1,))
        s = stream.Stream()
        s.insert(0.0, su1)
        s.insert(0.0, n1)
        self.assertIs(s.spanners[0].getFirst(), n1)
        self.assertIs(s.notes[0].getSpannerSites()[0], su1)

        t = copy.deepcopy(s)
        su2 = t.spanners[0]
        n2 = t.notes[0]
        self.assertIsNot(su2, su1)
        self.assertIsNot(n2, n1)
        self.assertIs(t.spanners[0].getFirst(), n2)
        self.assertIs(t.notes[0].getSpannerSites()[0], su2)
        self.assertIsNot(s.notes[0].getSpannerSites()[0], su2)

        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Spanner]


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    # import sys
    # sys.argv.append('testDeepcopyNotesAndSpannerInStream')
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof
