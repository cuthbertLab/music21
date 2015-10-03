# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         stream.py
# Purpose:      base classes for dealing with groups of positioned objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Josiah Wolf Oberholtzer
#               Evan Lynch
#
# Copyright:    Copyright © 2008-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
The :class:`~music21.stream.Stream` and its subclasses,
a subclass of the :class:`~music21.base.Music21Object`,
is the fundamental container of offset-positioned notation and
musical elements in music21. Common Stream subclasses, such
as the :class:`~music21.stream.Measure`
and :class:`~music21.stream.Score` objects, are defined in
this module.
'''
import collections
import copy
import unittest
import warnings
import sys

from fractions import Fraction

from music21 import base

from music21 import bar
from music21 import common
from music21 import clef
from music21 import chord
from music21 import defaults
from music21 import derivation
from music21 import duration
from music21 import exceptions21
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import spanner
from music21 import tie
from music21 import repeat
from music21 import tempo
from music21 import timespans

from music21.ext import six

from music21.stream import core
from music21.stream import makeNotation
from music21.stream import streamStatus
from music21.stream import iterator
from music21.stream import filter

from music21.common import opFrac

from music21 import environment
_MOD = "stream.py"
environLocal = environment.Environment(_MOD)

StreamException = exceptions21.StreamException

class StreamDeprecationWarning(UserWarning):
    # Do not subclass Deprecation warning, because these
    # warnings need to be passed to users...
    pass

#------------------------------------------------------------------------------
# Metaclass
_OffsetMap = collections.namedtuple('OffsetMap', ['element','offset', 'endTime', 'voiceIndex'])


#------------------------------------------------------------------------------


class Stream(core.StreamCoreMixin, base.Music21Object):
    '''
    This is the fundamental container for Music21Objects;
    objects may be ordered and/or placed in time based on
    offsets from the start of this container.

    As a subclass of Music21Object, Streams have offsets,
    priority, id, and groups.

    Streams may be embedded within other Streams. As each
    Stream can have its own offset, when Streams are
    embedded the offset of an element is relatively only
    to its parent Stream. The :attr:`~music21.stream.Stream.flat`
    property provides access to a flat representation of all
    embedded Streams, with offsets relative to the
    top-level Stream.

    The Stream :attr:`~music21.stream.Stream.elements` attribute
    returns the contents of the Stream as a list. Direct access
    to, and manipulation of, the elements list is not recommended.
    Instead, use the host of high-level methods available.

    The Stream, like all Music21Objects, has a
    :class:`music21.duration.Duration` that is usually the
    "release" time of the chronologically last element in the Stream
    (that is, the highest onset plus the duration of
    any element in the Stream).
    The duration, however, can be "unlinked" and explicitly
    set independent of the Stream's contents.

    The first element passed to the Stream is an optional list,
    tuple, or other Stream of music21 objects which is used to
    populate the Stream by inserting each object at its :attr:`~music21.base.Music21Object.offset`
    property. Other arguments and keywords are ignored, but are
    allowed so that subclassing the Stream is easier.



    >>> s1 = stream.Stream()
    >>> s1.append(note.Note('C#4', type='half'))
    >>> s1.append(note.Note('D5', type='quarter'))
    >>> s1.duration.quarterLength
    3.0
    >>> for thisNote in s1.notes:
    ...     print(thisNote.octave)
    ...
    4
    5


    This is a demonstration of creating a Stream with other elements,
    including embedded Streams (in this case, :class:`music21.stream.Part`,
    a Stream subclass):


    >>> c1 = clef.TrebleClef()
    >>> c1.offset = 0.0
    >>> c1.priority = -1
    >>> n1 = note.Note("E-6", type='eighth')
    >>> n1.offset = 1.0
    >>> p1 = stream.Part()
    >>> p1.offset = 0.0
    >>> p1.id = 'embeddedPart'
    >>> p1.append(note.Rest()) # quarter rest
    >>> s2 = stream.Stream([c1, n1, p1])
    >>> s2.duration.quarterLength
    1.5
    >>> s2.show('text')
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.stream.Part embeddedPart>
        {0.0} <music21.note.Rest rest>
    {1.0} <music21.note.Note E->
    '''

    # this static attributes offer a performance boost over other
    # forms of checking class
    isStream = True
    isMeasure = False
    classSortOrder = -20
    recursionType = 'elementsFirst'

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['append', 'insert', 'insertAndShift',
        'notes', 'pitches',
        'transpose',
        'augmentOrDiminish', 'scaleOffsets', 'scaleDurations']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
        'recursionType': '''
            String of ('elementsFirst' (default), 'flatten', 'elementsOnly)
            that decides whether the stream likely holds relevant
            contexts for the elements in it.  
            
            see :meth:`~music21.base.Music21Object.contextSites` 
            ''',
        'isSorted': '''
            Boolean describing whether the Stream is sorted or not.
            ''',
        'autoSort': '''
            Boolean describing whether the Stream is automatically sorted by
            offset whenever necessary.
            ''',
        'isFlat': '''
            Boolean describing whether this Stream contains embedded
            sub-Streams or Stream subclasses (not flat).
            ''',
        'definesExplicitSystemBreaks': '''
            Boolean that says whether all system breaks in the piece are
            explicitly defined.  Only used on musicxml output (maps to the
            musicxml <supports attribute="new-system"> tag) and only if this is
            the outermost Stream being shown
            ''',
        'definesExplicitPageBreaks': '''
            Boolean that says whether all page breaks in the piece are
            explicitly defined.  Only used on musicxml output (maps to the
            musicxml <supports attribute="new-page"> tag) and only if this is
            the outermost Stream being shown
            ''',
        }

    def __init__(self, givenElements=None, *args, **keywords):
        base.Music21Object.__init__(self, **keywords)
        core.StreamCoreMixin.__init__(self)

        self.streamStatus = streamStatus.StreamStatus(self)        
        self._unlinkedDuration = None

        self.autoSort = True
        self.isFlat = True  # does it have no embedded Streams
        self.definesExplicitSystemBreaks = False
        self.definesExplicitPageBreaks = False

        # property for transposition status;
        self._atSoundingPitch = 'unknown' # True, False, or unknown

        # experimental
        self._mutable = True        

        if givenElements is not None:
            # TODO: perhaps convert a single element into a list?
            try:
                for e in givenElements:
                    self._insertCore(e.offset, e) 
            except (AttributeError, TypeError):
                raise StreamException("Unable to insert {0}".format(e))
            self.elementsChanged()


    def __repr__(self):
        if self.id is not None:
            if self.id != id(self) and str(self.id) != str(id(self)):
                return '<%s.%s %s>' % (self.__module__, self.__class__.__name__, self.id)
            else:
                return '<%s.%s 0x%x>' % (self.__module__, self.__class__.__name__, self.id)
        else:
            return base.Music21Object.__repr__(self)

    # def show(self...    --- see base.py calls .write(


    #---------------------------------------------------------------------------
    # sequence like operations

    def __len__(self):
        '''Get the total number of elements in the Stream.
        This method does not recurse into and count elements in contained Streams.


        >>> import copy
        >>> a = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> len(a)
        4

        >>> b = stream.Stream()
        >>> for x in range(4):
        ...     b.insert(copy.deepcopy(a) ) # append streams
        >>> len(b)
        4
        >>> len(b.flat)
        16
        '''
        return len(self._elements) + len(self._endElements)

    def __iter__(self):
        '''
        The Stream iterator, used in all for
        loops and similar iteration routines. This method returns the
        specialized :class:`music21.stream.StreamIterator` class, which
        adds necessary Stream-specific features.
        '''
        return iterator.StreamIterator(self)

    @property
    def iter(self):
        '''
        The Stream iterator, used in all for
        loops and similar iteration routines. This method returns the
        specialized :class:`music21.stream.StreamIterator` class, which
        adds necessary Stream-specific features.

        Generally you don't need this, but it is necessary to add filters to an
        iterative search.
        '''
        return self.__iter__()

    def __getitem__(self, k):
        '''
        Get a Music21Object from the Stream using a variety of keys or indices.

        If an int is given, the Music21Object at the index is returned. If the Stream is sorted 
        (if isSorted is True), the elements are returned in order.

        If a class name is given (as a string or name), 
        :meth:`~music21.stream.Stream.getElementsByClass` is used to return a Stream of the 
        elements that match the requested class.

        If a string is given, :meth:`~music21.stream.Stream.getElementById` first, then 
        (if no results are found) :meth:`~music21.stream.Stream.getElementsByGroup` is used to 
        collect and return elements as a Stream.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Rest(), [0, 1, 2, 3, 4, 5])
        >>> subslice = a[2:5]
        >>> len(subslice)
        3
        >>> a[1].offset
        1.0
        >>> b = note.Note()
        >>> b.id = 'green'
        >>> b.groups.append('violin')
        >>> a.insert(b)

        >>> a[note.Note][0] == b
        True
        >>> a['violin'][0] == b
        True
        >>> a['green'] == b
        True
        '''

        # need to sort if not sorted, as this call may rely on index positions
        if not self.isSorted and self.autoSort:
            self.sort() # will set isSorted to True

        if common.isNum(k):
            match = None
            # handle easy and most common case first
            if k >= 0 and k < len(self._elements):
                match = self._elements[k]
            # if using negative indices, or trying to access end elements,
            # then need to use .elements property
            else:
                try:
                    match = self.elements[k]
                except IndexError:
                    raise StreamException('attempting to access index %s while elements is of size %s' % 
                                          (k, len(self.elements)))
            # setting active site as cautionary measure
            match.activeSite = self
            return match

        elif isinstance(k, slice): # get a slice of index values
            # manually inserting elements is critical to setting the element
            # locations
            try:
                found = self.cloneEmpty(derivationMethod='__getitem__')
            except TypeError:
                raise StreamException("Error in defining class: %r. " + 
                                      "Stream subclasses and Music21Objects cannot have required arguments in __init__" % self.__class__)
            for e in self.elements[k]:
                found.insert(self.elementOffset(e), e)
            # each insert calls this; does not need to be done here
            #found.elementsChanged()
            return found

        elif common.isStr(k):
            # first search id, then search groups
            idMatch = self.getElementById(k)
            if idMatch is not None:
                return idMatch
            else: # search groups, return first element match
                groupStream = self.iter.getElementsByGroup(k)
                if groupStream:
                    return groupStream.stream()
                else:
                    raise KeyError('provided key (%s) does not match any id or group' % k)
        elif isinstance(k, type(type)):
            # assume it is a class name
            classStream = self.iter.getElementsByClass(k)
            if classStream:
                return classStream.stream()
            else:
                raise KeyError('provided class (%s) does not match any contained Objects' % k)


#    def __del__(self):
#        self.cache = {}
#         #environLocal.printDebug(['calling __del__ from Stream', self])
#         # this is experimental
#         # this did not offer improvements, and raised a number of errors
#         for e in self._elements:
#             e.sites.remove(self)



    def _getElements(self):
        '''
        Combines the two storage lists, _elements and _endElements, such that
        they appear as a single list.

        Note that by the time you call .elements
        the offsets 
        '''
        if 'elements' not in self._cache or self._cache["elements"] is None:
            # this list concatenation may take time; thus, only do when
            # elementsChanged has been called
            if not self.isSorted and self.autoSort:
                self.sort() # will set isSorted to True
            self._cache["elements"] = self._elements + self._endElements
        return tuple(self._cache["elements"])

    def _setElements(self, value):
        '''
        Sets this streams elements to the elements in another stream (just give
        the stream, not the stream's .elements), or to a list of elements.
        
        Safe:
        
        newStream.elements = oldStream
        
        Unsafe:
        
        newStream.elements = oldStream.elements
        
        Why?
        
        The activeSites of some elements may have changed between retrieving
        and setting (esp. if a lot else has happened in the meantime). Where
        are we going to get the new stream's elements' offsets from? why
        from their active sites.
        '''
        if (not common.isListLike(value) and 
                hasattr(value, 'isStream') and
                value.isStream):
            # set from a Stream.
            self._elements = list(value._elements)
            for e in self._elements:
                self.setElementOffset(e, value.elementOffset(e))
                e.sites.add(self)
                e.activeSite = self
            self._endElements = value._endElements
            for e in self._endElements:
                self.setElementOffset(e, value.elementOffset(e, stringReturn=True))
                e.sites.add(self)
                e.activeSite = self
        else:
            # replace the complete elements list
            self._elements = list(value)
            self._endElements = []
            self._offsetDict = {}
            for e in self._elements:
                self.setElementOffset(e, e.offset)
                e.sites.add(self)
                e.activeSite = self
        self.elementsChanged()
        return value

    elements = property(_getElements, _setElements,
        doc='''
        Don't use unless you really know what you're doing.
        
        Treat a Stream like a list!
        
        
        
        
        A list representing the elements contained in the Stream.

        Directly getting, setting, and manipulating this list is
        reserved for advanced usage. Instead, use the the
        provided high-level methods. 
        
        When setting .elements, a
        list of Music21Objects can be provided, or a complete Stream.
        If a complete Stream is provided, elements are extracted
        from that Stream. This has the advantage of transferring
        offset correctly and geting _endElements.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), list(range(10)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note("D"), list(range(10)))
        >>> b.offset = 6
        >>> c = stream.Stream()
        >>> c.repeatInsert(note.Note("E"), list(range(10)))
        >>> c.offset = 12
        >>> b.insert(c)
        >>> b.isFlat
        False

        >>> a.isFlat
        True

        >>> a.elements = b # assigning from a Stream
        >>> a.isFlat
        False

        >>> len(a.flat.notes) == len(b.flat.notes) == 20
        True
        
        :rtype: list(base.Music21Object)
        ''')

    def __setitem__(self, k, value):
        '''
        Insert an item at a currently filled index position,
        as represented in the elements list.


        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), list(range(10)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note("C"), list(range(10)))
        >>> b.offset = 6
        >>> c = stream.Stream()
        >>> c.repeatInsert(note.Note("C"), list(range(10)))
        >>> c.offset = 12
        >>> b.insert(c)
        >>> a.isFlat
        True
        >>> a[3] = b
        >>> a.isFlat
        False
        '''
        # remove old value at this position
        oldValue = self._elements[k]
        oldValue.sites.remove(self)
        oldValue.activeSite = None

        # assign in new position
        self._elements[k] = value
        self.setElementOffset(value, value.offset)
        value.activeSite = self
        # must get native offset

        value.sites.add(self)

        if isinstance(value, Stream):
            # know that this is now not flat
            self.elementsChanged(updateIsFlat=False) # set manualy
            self.isFlat = False
        else:
            # cannot be sure if this is flat, as we do not know if
            # we replaced a Stream at this index
            self.elementsChanged()


    def __delitem__(self, k):
        '''Delete element at an index position. Index positions are based
        on positions in self.elements.


        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), list(range(10)))
        >>> del a[0]
        >>> len(a)
        9
        '''
        del self._elements[k]
        self.elementsChanged()


    def __add__(self, other):
        '''Add, or concatenate, two Streams.

        Presently, this does not manipulate the offsets of the incoming elements to actually be at the end of the Stream. This may be a problem that makes this method not so useful?


        >>> a = stream.Part()
        >>> a.repeatInsert(note.Note("C"), list(range(5)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note("G"), list(range(5)))
        >>> c = a + b
        >>> c.pitches[0:4] # autoSort is True, thus a sorted version results
        [<music21.pitch.Pitch C>, <music21.pitch.Pitch G>, <music21.pitch.Pitch C>, <music21.pitch.Pitch G>]
        >>> len(c.notes)
        10


        The autoSort of the first stream becomes the autoSort of the
        destination.  The class of the first becomes the class of the destination.


        >>> a.autoSort = False
        >>> d = a + b
        >>> [str(p) for p in d.pitches]
        ['C', 'C', 'C', 'C', 'C', 'G', 'G', 'G', 'G', 'G']
        >>> d.__class__.__name__
        'Part'

        '''
        # TODO: check class of other first
        if other is None or not isinstance(other, Stream):
            raise TypeError('cannot concatenate a Stream with a non-Stream')

        s = self.cloneEmpty(derivationMethod='__add__')
        # may want to keep activeSite of source Stream?
        #s.elements = self._elements + other._elements
        # need to iterate over elements and re-assign to create new locations
        for e in self._elements:
            s.insert(self.elementOffset(e), e)
        for e in other._elements:
            s.insert(other.elementOffset(e), e)

        for e in self._endElements:
            s.storeAtEnd(e)
        for e in other._endElements:
            s.storeAtEnd(e)

        #s.elementsChanged()
        return s

    def __bool__(self):
        '''
        As a container class, Streams return True if they are non-empty
        and False if they are empty:
        
        >>> def testBool(s):
        ...    if s:
        ...        return True
        ...    else:
        ...        return False
        
        >>> s = stream.Stream()
        >>> testBool(s)
        False
        >>> s.append(note.Note())
        >>> testBool(s)
        True
        >>> s.append(note.Note())
        >>> testBool(s)
        True
        '''
        if self._elements: # blindingly faster than if len(self._elements) > 0
            return True    # and even about 5x faster than if any(self._elements)
        if self._endElements:
            return True
        return False
    
    if six.PY2:
        __nonzero__ = __bool__

    #-------------------------------
    # Temporary -- Remove in  2016
    def stream(self, returnStreamSubclass=None):
        '''
        During the transition period to the new iteration system,
        there may be times when someone thinks something is a StreamIterator
        (which needs to have .stream() called on it to make a new Stream) but
        actually already has a `Stream`.  
        
        So this is a temporary method.  It will eventually become deprecated
        and then removed.
        
        TODO: 2016 May??? Remove.
        '''
        return self


    def cloneEmpty(self, derivationMethod=None):
        '''
        Create a Stream that is identical to this one except that the elements are empty
        and set derivation (Should this be deleted??? 
        
        >>> p = stream.Part()
        >>> p.autoSort = False
        >>> p.id = 'hi'
        >>> p.insert(0, note.Note())
        >>> q = p.cloneEmpty(derivationMethod="demo")
        >>> q.autoSort
        False
        >>> q
        <music21.stream.Part hi>
        >>> q.derivation.origin is p
        True
        >>> q.derivation.method
        'demo'
        >>> len(q)
        0
        '''
        returnObj = self.__class__()
        returnObj.derivation.client = returnObj
        returnObj.derivation.origin = self
        if derivationMethod is not None:
            returnObj.derivation.method = derivationMethod
        returnObj.mergeAttributes(self) # get groups, optional id
        return returnObj

    def mergeAttributes(self, other):
        '''
        Merge relevant attributes from the Other stream into this one.
        
        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.id = 'hi'
        >>> t = stream.Stream()
        >>> t.mergeAttributes(s)
        >>> t.autoSort
        False
        >>> t
        <music21.stream.Stream hi>
        '''
        base.Music21Object.mergeAttributes(self, other)

        for attr in ('autoSort','isSorted'):
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))


    def hasElement(self, obj):
        '''
        Return True if an element, provided as an argument, is contained in
        this Stream.

        This method is based on object equivalence, not parameter equivalence
        of different objects.

        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> s.append(n1)
        >>> s.hasElement(n1)
        True
        '''
        objId = id(obj)
        for e in self._elements:
            if id(e) == objId:
                return True
        for e in self._endElements:
            if id(e) == objId:
                return True
        return False

    def hasElementOfClass(self, className, forceFlat=False):
        '''
        Given a single class name as string,
        return True or False if an element with the
        specified class is found.

        Only a single class name can be given.


        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('5/8'))
        >>> s.append(note.Note('d-2'))
        >>> s.insert(dynamics.Dynamic('fff'))
        >>> s.hasElementOfClass('TimeSignature')
        True
        >>> s.hasElementOfClass('Measure')
        False
        '''
        clist = [className]
        #environLocal.printDebug(['calling hasElementOfClass()', className])
        for e in self._elements:
            if e.isClassOrSubclass(clist):
                return True
        for e in self._endElements:
            if e.isClassOrSubclass(clist):
                return True
        return False




    def mergeElements(self, other, classFilterList=None):
        '''
        Given another Stream, store references of each element
        in the other Stream in this Stream. This does not make
        copies of any elements, but simply stores all of them in this Stream.

        Optionally, provide a list of classes to exclude with the `classFilter` list.

        This method provides functionality like a shallow copy,
        but manages locations properly, only copies elements,
        and permits filtering by class type.


        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> n1 = note.Note('f#')
        >>> n2 = note.Note('g')
        >>> s1.append(n1)
        >>> s1.append(n2)
        >>> s2.mergeElements(s1)
        >>> len(s2)
        2
        >>> s1[0] is s2[0]
        True
        >>> s1[1] is s2[1]
        True
        '''
        for e in other._elements:
            #self.insert(other.offset, e)
            if classFilterList is not None:
                if e.isClassOrSubclass(classFilterList):
                    self._insertCore(other.elementOffset(e), e)
            else:
                self._insertCore(other.elementOffset(e), e)

#             for c in classFilterList:
#                 if c in e.classes:
#                     match = True
#                     break

#             if len(classFilterList) == 0 or match:
#                 self.insert(e.getOffsetBySite(other), e)
        for e in other._endElements:
            if classFilterList is not None:
                if e.isClassOrSubclass(classFilterList):
                    self._storeAtEndCore(e)
            else:
                self._storeAtEndCore(e)

#             match = False
#             for c in classFilterList:
#                 if c in e.classes:
#                     match = True
#                     break
#             if len(classFilterList) == 0 or match:
#                 self.storeAtEnd(e)
        self.elementsChanged()


    def index(self, obj):
        '''
        Return the first matched index for
        the specified object.

        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')

        >>> s.insert(0, n1)
        >>> s.insert(5, n2)
        >>> len(s)
        2
        >>> s.index(n1)
        0
        >>> s.index(n2)
        1        '''
        if not self.isSorted and self.autoSort:
            self.sort() # will set isSorted to True

        if 'index' in self._cache and self._cache['index'] is not None:
            try:
                return self._cache['index'][id(obj)]
            except KeyError:
                pass  # not in cache
        else:
            self._cache['index'] = {}

        # TODO: possibly replace by binary search
        if common.isNum(obj):
            objId = obj
        else:
            objId = id(obj)

        count = 0
        for e in self._elements:
            if id(e) == objId:
                self._cache['index'][objId] = count
                return count
            count += 1
        for e in self._endElements:
            if id(e) == objId:
                self._cache['index'][objId] = count
                return count # this is the index
            count += 1 # cumulative indices
        raise StreamException('cannot find object (%s) in Stream' % obj)


    def remove(self, 
               targetOrList, 
               firstMatchOnly=True, 
               shiftOffsets=False, 
               recurse=False): 
        '''
        Remove an object from this Stream. Additionally, this Stream is
        removed from the object's sites in :class:`~music21.sites.Sites`.

        By default, only the first match is removed. This can be adjusted with the `firstMatchOnly` parameters.
        If a list of objects is passed, they will all be removed. If shiftOffsets is True, then offsets will be
        corrected after object removal. It is more efficient to pass a list of objects than to call remove on
        each object individually if shiftOffsets is True.

        >>> import copy
        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> # copies of an object are not the same as the object
        >>> n3 = copy.deepcopy(n2)
        >>> s.insert(10, n1)
        >>> s.insert(5, n2)
        >>> s.remove(n1)
        >>> len(s)
        1
        >>> s.insert(20, n3)
        >>> s.remove(n3)
        >>> [e for e in s] == [n2]
        True

        No error is raised if the target is not found.

        >>> s.remove(n3)

        >>> s2 = stream.Stream()
        >>> c = clef.TrebleClef()
        >>> n1, n2, n3, n4 = note.Note('a'), note.Note('b'), note.Note('c'), note.Note('d')
        >>> n5, n6, n7, n8 = note.Note('e'), note.Note('f'), note.Note('g'), note.Note('a')
        >>> s2.insert(0.0, c)
        >>> s2.append([n1,n2,n3,n4,n5,n6,n7,n8])
        >>> s2.remove(n1, shiftOffsets=True)
        >>> s2.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Note C>
        {2.0} <music21.note.Note D>
        {3.0} <music21.note.Note E>
        {4.0} <music21.note.Note F>
        {5.0} <music21.note.Note G>
        {6.0} <music21.note.Note A>

        >>> s2.remove([n3, n6, n4], shiftOffsets=True)
        >>> s2.show('text')
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Note E>
        {2.0} <music21.note.Note G>
        {3.0} <music21.note.Note A>

        With the recurse=True parameter, we can remove elements deeply nested. However, shiftOffsets
        does not work with recurse=True yet.
        
        >>> p1 = stream.Part()
        >>> m1 = stream.Measure()
        >>> c = clef.BassClef()
        >>> m1.insert(0, c)
        >>> m1.append(note.Note())
        >>> p1.append(m1)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.note.Note C>

        Without recurse=True:
        
        >>> p1.remove(c)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.note.Note C>

        With recurse=True:
        
        >>> p1.remove(c, recurse=True)
        >>> p1.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note C>

        '''
        # TODO: Next to clean up... a doozy -- filter out all the different options.
        
        # TODO: Add a renumber measures option
        # TODO: Shift offsets if recurse is True
        if shiftOffsets is True and recurse is True:
            raise StreamException("Cannot do both shiftOffsets and recurse search at the same time...yet")
        
        if not common.isListLike(targetOrList):
            targetList = [targetOrList]
        elif len(targetOrList) > 1:
                targetList = sorted(targetOrList, key=self.elementOffset)
        else:
            targetList = targetOrList

        if shiftOffsets:
            shiftDur = 0.0
            
        for i, target in enumerate(targetList):
            try:
                indexInStream = self.index(target)
            except StreamException:
                if recurse is True:
                    for s in self.recurse(streamsOnly=True):
                        if s is self:
                            continue
                        try:
                            indexInStream = s.index(target)
                            s.remove(target)
                            break
                        except StreamException:
                            continue
                continue # recursion matched or didn't or wasn't run. either way no need for rest...
            
            match = None
            matchedEndElement = False
            baseElementCount = len(self._elements)
            if indexInStream < baseElementCount:
                match = self._elements.pop(indexInStream)
            else:
                match = self._endElements.pop(indexInStream-baseElementCount)
                matchedEndElement = True

            if match is not None:
                if shiftOffsets is True:
                    matchOffset = self.elementOffset(match)

                try:
                    del self._offsetDict[id(match)]
                except KeyError:
                    pass
                self.elementsChanged(clearIsSorted=False)
                match.sites.remove(self)
                match.activeSite = None

            if shiftOffsets is True and matchedEndElement is False: 
                matchDuration = match.duration.quarterLength
                shiftedRegionStart = matchOffset + matchDuration
                if i+1 < len(targetList):
                    shiftedRegionEnd = self.elementOffset(targetList[i+1])
                else:
                    shiftedRegionEnd = self.duration.quarterLength

                shiftDur = shiftDur + matchDuration
                if shiftDur != 0.0:
                    # can this be done with recurse???
                    for e in self.iter.getElementsByOffset(shiftedRegionStart,
                        shiftedRegionEnd,
                        includeEndBoundary=False,
                        mustFinishInSpan=False,
                        mustBeginInSpan=True):

                        elementOffset = self.elementOffset(e)
                        self.setElementOffset(e, elementOffset-shiftDur)
            #if renumberMeasures is True and matchedEndElement is False:
            #   pass  # This should maybe just call a function renumberMeasures

    def pop(self, index):
        '''
        Return and remove the object found at the
        user-specified index value. Index values are
        those found in `elements` and are not necessary offset order.


        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), list(range(10)))
        >>> junk = a.pop(0)
        >>> len(a)
        9
        
        :rtype: base.Music21Object
        '''
        eLen = len(self._elements)
        # if less then base length, its in _elements
        if index < eLen:
            post = self._elements.pop(index)
        else: # its in the _endElements
            post = self._endElements.pop(index - eLen)

        self.elementsChanged(clearIsSorted=False)

        try:
            del self._offsetDict[id(post)]
        except KeyError:
            pass

        post.sites.remove(self)
        post.activeSite = None
        return post


    def _removeIteration(self, streamIterator):
        '''
        helper method to remove different kinds of elements.
        '''
        popDict = {'_elements': [],
                   '_endElements': []
                   }
        for unused_el in streamIterator:
            ai = streamIterator.activeInformation
            popDict[ai['iterSection']].append(ai['sectionIndex'])

        # do not pop while iterating...
        
        for section in popDict:
            sectionList = getattr(self, section) # _elements or _endElements
            popList = popDict[section]
            for popIndex in reversed(popList):
                removeElement = sectionList.pop(popIndex)
                try:
                    del self._offsetDict[id(removeElement)]
                except KeyError:
                    pass

                removeElement.sites.remove(self) # to-do to make recursive, store a tuple of
                    # active sites and index
                removeElement.activeSite = None

        # call elements changed once; sorted arrangement has not changed
        self.elementsChanged(clearIsSorted=False)
        return  

    def removeByClass(self, classFilterList):
        '''
        Remove all elements from the Stream
        based on one or more classes given
        in a list.


        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.repeatAppend(note.Note("C"), 8)
        >>> len(s)
        9
        >>> s.removeByClass('GeneralNote')
        >>> len(s)
        1
        >>> len(s.notes)
        0

        Test that removing from end elements works.

        >>> s = stream.Measure()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.repeatAppend(note.Note("C"), 4)
        >>> s.rightBarline = bar.Barline('final')
        >>> len(s)
        6
        >>> s.removeByClass('Barline')
        >>> len(s)
        5
        
        '''
        elFilter = self.iter.getElementsByClass(classFilterList)
        return self._removeIteration(elFilter)


    def removeByNotOfClass(self, classFilterList):
        '''
        Remove all elements not of the specified
        class or subclass in the Steam in place.

        >>> s = stream.Stream()
        >>> s.append(meter.TimeSignature('4/4'))
        >>> s.repeatAppend(note.Note("C"), 8)
        >>> len(s)
        9
        >>> s.removeByNotOfClass('TimeSignature')
        >>> len(s)
        1
        >>> len(s.notes)
        0
        '''
        #if classFilterList == []:
        #    classFilterList = ['Music21Object']
        elFilter = self.iter.getElementsNotOfClass(classFilterList)
        return self._removeIteration(elFilter)    


    def _deepcopySubclassable(self, memo=None, ignoreAttributes=None, removeFromIgnore=None):
        # NOTE: this is a performance critical operation        
        defaultIgnoreSet = {'_offsetDict', 'streamStatus', '_elements', '_endElements', '_cache',
                            'analysisData' # TODO: REMOVE SOON
                            }
        if ignoreAttributes is None:
            ignoreAttributes = defaultIgnoreSet
        else:
            ignoreAttributes = ignoreAttributes | defaultIgnoreSet

        new = super(Stream, self)._deepcopySubclassable(memo, ignoreAttributes, removeFromIgnore)

        if removeFromIgnore is not None:
            ignoreAttributes = ignoreAttributes - removeFromIgnore

        if '_offsetDict' in ignoreAttributes:
            newValue = {}
            setattr(new, '_offsetDict', newValue)
        # all subclasses of Music21Object that define their own
        # __deepcopy__ methods must be sure to not try to copy activeSite
        if '_offsetDict' in self.__dict__:
            newValue = {}
            setattr(new, '_offsetDict', newValue)
        if 'streamStatus' in ignoreAttributes:
            # update the client
            if self.streamStatus is not None:
                #storedClient = self.streamStatus.client # should be self
                #self.streamStatus.client = None
                newValue = copy.deepcopy(self.streamStatus)
                newValue.client = new
                setattr(new, 'streamStatus', newValue)
                #self.streamStatus.client = storedClient
        #if name == '_cache' or name == 'analysisData':
        #    continue # skip for now
        if '_elements' in ignoreAttributes:
            # must manually add elements to new Stream
            for e in self._elements:
                #environLocal.printDebug(['deepcopy()', e, 'old', old, 'id(old)', id(old), 
                # 'new', new, 'id(new)', id(new), 'old.hasElement(e)', old.hasElement(e), 
                # 'e.activeSite', e.activeSite, 'e.getSites()', e.getSites(), 'e.getSiteIds()', 
                # e.getSiteIds()], format='block')
                # this will work for all with __deepcopy___
                # get the old offset from the activeSite Stream
                # user here to provide new offset
                #new.insert(e.getOffsetBySite(old), newElement,
                #           ignoreSort=True)
                offset = self.elementOffset(e)
                newElement = copy.deepcopy(e, memo)
                ### TEST on copying!!!!
                #if 'Note' in newElement.classes:
                #    newElement.pitch.ps += 2.0
                new._insertCore(offset, newElement, ignoreSort=True)
        if '_endElements' in ignoreAttributes:
            # must manually add elements to
            for e in self._endElements:
                # this will work for all with __deepcopy___
                # get the old offset from the activeSite Stream
                # user here to provide new offset
                new._storeAtEndCore(copy.deepcopy(e, memo))                

        # caching this is CRUCIAL! using new.spannerBundle ever time below added
        # 40% to the test suite time!
        newSpannerBundle = new.spannerBundle
        # only proceed if there are spanners, otherwise creating semiFlat
        if len(newSpannerBundle) > 0:
            # iterate over complete semi-flat (need containers); find
            # all new/old pairs
            for e in new.recurse(skipSelf=True):
                #if 'Spanner' in e.classes:
                if e.isSpanner:
                    continue # we never update Spanners
                # update based on id of old object, and ref to new object
                if e.sites.hasSpannerSite():
                    #environLocal.printDebug(['Stream.__deepcopy__', 'replacing component to', e])
                    # this will clear and replace the proper locations on
                    # the SpannerStorage Stream
                    origin = e.derivation.origin
                    if (origin is not None and e.derivation.method == '__deepcopy__'):
                        newSpannerBundle.replaceSpannedElement(id(origin), e)
                    # need to remove the old SpannerStorage Stream from this element; 
                    # however, all we have here is the new Spanner and new elements
                    # this must be done here, not when originally copying
                    e.purgeOrphans(excludeStorageStreams=False)

        # purging these orphans works in nearly all cases, but there are a few
        # cases where we rely on a Stream having access to Stream it was
        # part of after deepcopying
        #new.purgeOrphans()
        return new



    def __deepcopy__(self, memo=None):
        '''
        Deepcopy the stream from copy.deepcopy()
        '''
        # does not purgeOrphans -- q: is that a bug or by design?
        return self._deepcopySubclassable(memo)




    def setElementOffset(self, element, offset):
        '''
        Sets the Offset for an element, very quickly.
        
        Too quickly.  TODO: check if the offset is actually in the stream!
        '''
        try:
            offset = opFrac(offset)
        except TypeError:
            pass
        
        self._offsetDict[id(element)] = (offset, element) # fast
    
    def elementOffset(self, element, stringReturns=False):
        '''
        return the offset (opFrac) from the offsetMap.
        highly optimized for speed.
        
        if stringReturns are allowed then returns like 'highestOffset' are allowed.
        
        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> d = note.Note('D')
        >>> s.append(d)
        >>> s.elementOffset(d)
        1.0
        
        >>> b = bar.Barline()
        >>> s.storeAtEnd(b)
        >>> s.elementOffset(b)
        2.0
        >>> s.elementOffset(b, stringReturns=True)
        'highestTime' 
        '''
        try:
            o = self._offsetDict[id(element)][0] # 2.3 million times found in TestStream
            #if returnedElement is not element: # stale reference...   
            #    o = None  #             0 in TestStream -- not worth testing
        except KeyError: # 445k - 442,443 = 3k in TestStream
            for idElement in self._offsetDict: # slower search
                o, returnedElement = self._offsetDict[idElement]
                if element is returnedElement:
                    break
            else:
                raise base.SitesException(
                    "an entry for this object 0x%x is not stored in stream %s" % 
                    (id(element), self))
            
        if stringReturns is False and o in ('highestTime', 'lowestOffset', 'highestOffset'):
            try:
                return getattr(self, o)
            except AttributeError:
                raise base.SitesException(
                        'attempted to retrieve a bound offset with a string ' + 
                        'attribute that is not supported: %s' % o)
        else:
            return o

    def insert(self, offsetOrItemOrList, itemOrNone=None,
                     ignoreSort=False, setActiveSite=True):
        '''
        Inserts an item(s) at the given offset(s).

        If `ignoreSort` is True then the inserting does not
        change whether the Stream is sorted or not (much faster if you're 
        going to be inserting dozens
        of items that don't change the sort status)

        The `setActiveSite` parameter should nearly always be True; only for
        advanced Stream manipulation would you not change
        the activeSite after inserting an element.

        Has three forms: in the two argument form, inserts an element at the given offset:



        >>> st1 = stream.Stream()
        >>> st1.insert(32, note.Note("B-"))
        >>> st1.highestOffset
        32.0

        In the single argument form with an object, inserts the element at its stored offset:

        >>> n1 = note.Note("C#")
        >>> n1.offset = 30.0
        >>> st1 = stream.Stream()
        >>> st1.insert(n1)
        >>> st2 = stream.Stream()
        >>> st2.insert(40.0, n1)
        >>> n1.getOffsetBySite(st1)
        30.0

        In single argument form with a list, the list should contain pairs that alternate
        offsets and items; the method then, obviously, inserts the items
        at the specified offsets:

        >>> n1 = note.Note("G")
        >>> n2 = note.Note("F#")
        >>> st3 = stream.Stream()
        >>> st3.insert([1.0, n1, 2.0, n2])
        >>> n1.getOffsetBySite(st3)
        1.0
        >>> n2.getOffsetBySite(st3)
        2.0
        >>> len(st3)
        2

        OMIT_FROM_DOCS
        Raise an error if offset is not a number
        >>> stream.Stream().insert("l","g")
        Traceback (most recent call last):
        StreamException: ...

        '''
        #environLocal.printDebug(['self', self, 'offsetOrItemOrList',
        #            offsetOrItemOrList, 'itemOrNone', itemOrNone,
        #             'ignoreSort', ignoreSort, 'setActiveSite', setActiveSite])
        # normal approach: provide offset and item
        if itemOrNone is not None:
            offset = offsetOrItemOrList
            item = itemOrNone
        elif itemOrNone is None and isinstance(offsetOrItemOrList, list):
            i = 0
            while i < len(offsetOrItemOrList):
                offset = offsetOrItemOrList[i]
                item = offsetOrItemOrList[i+1]
                # recursively calling insert() here
                self.insert(offset, item, ignoreSort=ignoreSort)
                i += 2
            return
        # assume first arg is item, and that offset is local offset of object
        else:
            item = offsetOrItemOrList
            #offset = item.offset
            # this is equivalent to:
            try:
                offset = item.getOffsetBySite(item.activeSite)
            except AttributeError:
                raise StreamException("Cannot insert item %s to stream " % (item,) + 
                                      "-- is it a music21 object?")

        #if not common.isNum(offset):
        try: # using float conversion instead of isNum for performance
            offset = float(offset)
        except (ValueError, TypeError):
            if offset is None:
                offset = 0.0
            else:
                raise StreamException("offset %s must be a number", offset)

        if not isinstance(item, base.Music21Object):
            raise StreamException('to put a non Music21Object in a stream, ' + 
                                  'create a music21.ElementWrapper for the item') 
        else:
            element = item

        # checks of element is self; possibly performs additional checks
        self._addElementPreProcess(element)
        # main insert procedure here
        
        storeSorted = self._insertCore(offset, element,
                     ignoreSort=ignoreSort, setActiveSite=setActiveSite)
        updateIsFlat = False
        if element.isStream:
            updateIsFlat = True
        self.elementsChanged(updateIsFlat=updateIsFlat)
        if ignoreSort is False:
            self.isSorted = storeSorted



    def insertIntoNoteOrChord(self, offset, noteOrChord, chordsOnly=False):
        '''
        Insert a Note or Chord into an offset position in this Stream.
        If there is another Note or Chord in this position,
        create a new Note or Chord that combines the pitches of the
        inserted chord. If there is a Rest in this position,
        the Rest is replaced by the Note or Chord. The duration of the
        previously-found chord will remain the same in the new Chord.

        >>> n1 = note.Note("D4")
        >>> n1.duration.quarterLength = 2.0
        >>> r1 = note.Rest()
        >>> r1.duration.quarterLength = 2.0
        >>> c1 = chord.Chord(['C4','E4'])
        >>> s = stream.Stream()
        >>> s.append(n1)
        >>> s.append(r1)
        >>> s.append(c1)
        >>> s.show('text')
        {0.0} <music21.note.Note D>
        {2.0} <music21.note.Rest rest>
        {4.0} <music21.chord.Chord C4 E4>

        Save the original Stream for later
        >>> import copy
        >>> s2 = copy.deepcopy(s)

        Notice that the duration of the inserted element is not taken into
        consideration and the original element is not broken up,
        as it would be in chordify().  But Chords and Notes are created...

        >>> for i in [0.0, 2.0, 4.0]:
        ...     s.insertIntoNoteOrChord(i, note.Note("F#4"))
        >>> s.show('text')
        {0.0} <music21.chord.Chord D4 F#4>
        {2.0} <music21.note.Note F#>
        {4.0} <music21.chord.Chord C4 E4 F#4>

        if chordsOnly is set to True then no notes are returned, only chords:

        >>> for i in [0.0, 2.0, 4.0]:
        ...     s2.insertIntoNoteOrChord(i, note.Note("F#4"), chordsOnly=True)
        >>> s2.show('text')
        {0.0} <music21.chord.Chord D4 F#4>
        {2.0} <music21.chord.Chord F#4>
        {4.0} <music21.chord.Chord C4 E4 F#4>


        '''
        # could use duration of Note to get end offset span
        targets = list(self.iter.getElementsByOffset(offset,
                offset + noteOrChord.quarterLength, # set end to dur of supplied
                includeEndBoundary=False,
                mustFinishInSpan=False, 
                mustBeginInSpan=True).notesAndRests)
        removeTarget = None
        #environLocal.printDebug(['insertIntoNoteOrChord', [e for e in targets]])
        if len(targets) == 1:
            target = targets[0] # assume first
            removeTarget = target
            if 'Rest' in target.classes:
                pitches = [noteOrChord.pitch]
                components = [noteOrChord]
            if 'Note' in target.classes:
                # if a note, make it into a chord
                if 'Note' in noteOrChord.classes:
                    pitches = [target.pitch, noteOrChord.pitch]
                    components = [target, noteOrChord]
                elif 'Chord' in noteOrChord.classes:
                    pitches = [target.pitch] + noteOrChord.pitches
                    components = [target] + [c for c in noteOrChord]
            if 'Chord' in target.classes:
                # if a chord, make it into a chord
                if 'Note' in noteOrChord.classes:
                    pitches = target.pitches + (noteOrChord.pitch,)
                    components = [c for c in target] + [noteOrChord]
                elif 'Chord' in noteOrChord.classes:
                    pitches = target.pitches + noteOrChord.pitches
                    components = [c for c in target] + [c for c in noteOrChord]

            if len(pitches) > 1 or chordsOnly is True:
                finalTarget = chord.Chord(pitches)
            elif len(pitches) == 1:
                finalTarget = note.Note(pitches[0])
            else:
                finalTarget = note.Rest()

            finalTarget.expressions = target.expressions
            finalTarget.articulations = target.articulations
            finalTarget.duration = target.duration
            # append lyrics list
            if hasattr(target, 'lyrics'):
                for l in target.lyrics:
                    if l.text not in ['', None]:
                        finalTarget.addLyric(l.text)
            #finalTarget.lyrics = target.lyrics
            if hasattr(finalTarget, 'stemDirection') and hasattr(target, 'stemDirection'):
                finalTarget.stemDirection = target.stemDirection
            if hasattr(finalTarget, 'noteheadFill') and hasattr(target, 'noteheadFill'):
                finalTarget.noteheadFill = target.noteheadFill

            # fill component details
            if 'Chord' in finalTarget.classes:
                for i, n in enumerate(finalTarget):
                    nPrevious = components[i]
                    n.noteheadFill = nPrevious.noteheadFill

        elif len(targets) > 1:
            raise StreamException('more than one element found at the specified offset')
        else:
            finalTarget = noteOrChord

        if removeTarget is not None:
            self.remove(removeTarget)
        # insert normally, nothing to handle
        self.insert(offset, finalTarget, ignoreSort=False, setActiveSite=True)


    def append(self, others):
        '''
        Add a Music21Object (including another Stream) to the end of the current Stream.

        If given a list, will append each element in order after the previous one.

        The "end" of the stream is determined by the `highestTime` property
        (that is the latest "release" of an object, or directly after the last
        element ends).

        Runs fast for multiple addition and will preserve isSorted if True

        >>> a = stream.Stream()
        >>> notes = []
        >>> for x in range(0,3):
        ...     n = note.Note('G#')
        ...     n.duration.quarterLength = 3
        ...     notes.append(n)
        >>> a.append(notes[0])
        >>> a.highestOffset, a.highestTime
        (0.0, 3.0)
        >>> a.append(notes[1])
        >>> a.highestOffset, a.highestTime
        (3.0, 6.0)
        >>> a.append(notes[2])
        >>> a.highestOffset, a.highestTime
        (6.0, 9.0)
        >>> notes2 = []

        Since notes are not embedded in Elements here, their offset
        changes when they are added to a stream!

        >>> for x in range(0,3):
        ...     n = note.Note("A-")
        ...     n.duration.quarterLength = 3
        ...     n.offset = 0
        ...     notes2.append(n)
        >>> a.append(notes2) # add em all again
        >>> a.highestOffset, a.highestTime
        (15.0, 18.0)
        >>> a.isSequence()
        True

        Adding a note that already has an offset set does nothing different
        from above! That is, it is still added to the end of the Stream:

        >>> n3 = note.Note("B-")
        >>> n3.offset = 1
        >>> n3.duration.quarterLength = 3
        >>> a.append(n3)
        >>> a.highestOffset, a.highestTime
        (18.0, 21.0)
        >>> n3.getOffsetBySite(a)
        18.0
        
        TODO: Appending a Clef after a KeySignature will not cause sorting to be re-run.
        '''
        # store and increment highest time for insert offset
        highestTime = self.highestTime
        if not common.isListLike(others):
            # back into a list for list processing if single
            others = [others]
        updateIsFlat = False
        for e in others:
            try:
                if e.isStream: # any on that is a Stream req update
                    updateIsFlat = True
            except AttributeError:
                raise StreamException(
                    "The object you tried to add to the Stream, {0}, ".format(repr(e)) +
                    "is not a Music21Object.  Use an ElementWrapper object " + 
                    "if this is what you intend" )
            self._addElementPreProcess(e)
            # add this Stream as a location for the new elements, with the
            # the offset set to the current highestTime
            self.setElementOffset(e, highestTime)
            e.sites.add(self)
            # need to explicitly set the activeSite of the element
            e.activeSite = self
            self._elements.append(e)

            if e.duration.quarterLength != 0:
                #environLocal.printDebug(['incrementing highest time', 
                #                         'e.duration.quarterLength', 
                #                          e.duration.quarterLength])
                highestTime += e.duration.quarterLength

        # does not change sorted state
        storeSorted = self.isSorted
        # we cannot keep the index cache here b/c we might
        self.elementsChanged(updateIsFlat=updateIsFlat)
        self.isSorted = storeSorted
        self._setHighestTime(highestTime) # call after to store in cache


    def storeAtEnd(self, itemOrList, ignoreSort=False):
        '''
        Inserts an item or items at the end of the Stream,
        stored in the special box (called _endElements).

        This method is useful for putting things such as
        right bar lines or courtesy clefs that should always
        be at the end of a Stream no matter what else is appended
        to it

        As sorting is done only by priority and class,
        it cannot avoid setting isSorted to False.

        '''
        if isinstance(itemOrList, list):
            for item in itemOrList:
                # recursively calling insert() here
                self.storeAtEnd(item, ignoreSort=ignoreSort)
            return
        else:
            item = itemOrList
        try:
            unused = item.isStream # will raise attribute error
            element = item
        except AttributeError: # need to wrap
            #element = music21.ElementWrapper(item)
            raise StreamException('to put a non Music21Object in a stream, ' + 
                                  'create a music21.ElementWrapper for the item')
        # if not a Music21Object, embed
#         if not isinstance(item, music21.Music21Object):
#             element = music21.ElementWrapper(item)
#         else:
#             element = item

        # cannot support elements with Durations in the highest time list
        if element.duration is not None and element.duration.quarterLength != 0:
            raise StreamException('cannot insert an object with a non-zero ' + 
                                  'Duration into the highest time elements list')

        # checks of element is self; possibly performs additional checks
        self._addElementPreProcess(element)

#         element.sites.add(self, 'highestTime')
#         # need to explicitly set the activeSite of the element
#         element.activeSite = self
#         self._endElements.append(element)

        self._storeAtEndCore(element)
        # Streams cannot reside in end elements, thus do not update is flat
        self.elementsChanged(updateIsFlat=False)


    #---------------------------------------------------------------------------
    # all the following call either insert() or append()

    def insertAndShift(self, offsetOrItemOrList, itemOrNone=None):
        '''
        Insert an item at a specified or native offset,
        and shift any elements found in the Stream to start at
        the end of the added elements.

        This presently does not shift elements that have durations
        that extend into the lowest insert position.
        
        >>> st1 = stream.Stream()
        >>> st1.insertAndShift(32, note.Note("B-"))
        >>> st1.highestOffset
        32.0
        >>> st1.insertAndShift(32, note.Note("B-"))
        >>> st1.highestOffset
        33.0

        In the single argument form with an object, inserts the element at its stored offset:

        >>> n1 = note.Note("C#")
        >>> n1.offset = 30.0
        >>> n2 = note.Note("C#")
        >>> n2.offset = 30.0
        >>> st1 = stream.Stream()
        >>> st1.insertAndShift(n1)
        >>> st1.insertAndShift(n2) # should shift offset of n1
        >>> n1.getOffsetBySite(st1)
        31.0
        >>> n2.getOffsetBySite(st1)
        30.0
        >>> st2 = stream.Stream()
        >>> st2.insertAndShift(40.0, n1)
        >>> st2.insertAndShift(40.0, n2)
        >>> n1.getOffsetBySite(st2)
        41.0

        In single argument form with a list, the list should contain pairs that alternate
        offsets and items; the method then, obviously, inserts the items
        at the specified offsets:

        >>> n1 = note.Note("G")
        >>> n2 = note.Note("F#")
        >>> st3 = stream.Stream()
        >>> st3.insertAndShift([1.0, n1, 2.0, n2])
        >>> n1.getOffsetBySite(st3)
        1.0
        >>> n2.getOffsetBySite(st3)
        2.0
        >>> len(st3)
        2

        N.B. -- using this method on a list assumes that you'll be inserting
        contiguous objects; you can't shift things that are separated, as this
        following FAILED example shows.

        >>> n1 = note.Note('G', type='half')
        >>> st4 = stream.Stream()
        >>> st4.repeatAppend(n1, 3)
        >>> st4.insertAndShift([2.0, note.Note('e'), 4.0, note.Note('f')])
        >>> st4.show('text')
        {0.0} <music21.note.Note G>
        {2.0} <music21.note.Note E>
        {4.0} <music21.note.Note F>
        {5.0} <music21.note.Note G>
        {7.0} <music21.note.Note G>

        As an FYI, there is no removeAndShift() function, so the opposite of
        insertAndShift(el) is remove(el, shiftOffsets=True).
        '''
        # need to find the highest time after the insert
        if itemOrNone is not None: # we have an offset and an element
            #if hasattr(itemOrNone, 'duration') and itemOrNone.duration is not None:
            insertObject = itemOrNone
            if insertObject.duration is not None:
                qL = insertObject.duration.quarterLength
            else:
                qL = 0.0
            offset = offsetOrItemOrList
            lowestOffsetInsert = offset
            highestTimeInsert = offset + qL
        elif itemOrNone is None and isinstance(offsetOrItemOrList, list):
            # need to find which has the max combined offset and dur
            insertList = offsetOrItemOrList
            highestTimeInsert = 0.0
            lowestOffsetInsert = None
            i = 0
            while i < len(insertList):
                o = insertList[i]
                e = insertList[i+1]
                #if hasattr(e, 'duration')  and e.duration is not None:
                if e.duration is not None:
                    qL = e.duration.quarterLength
                else:
                    qL = 0.0
                if o + qL > highestTimeInsert:
                    highestTimeInsert = o + qL
                if lowestOffsetInsert is None or o < lowestOffsetInsert:
                    lowestOffsetInsert = o
                i += 2
        else: # using native offset
            #if hasattr(offsetOrItemOrList, 'duration'):
            insertObject = offsetOrItemOrList
            if insertObject.duration is not None:
                qL = insertObject.duration.quarterLength
            else:
                qL = 0.0
            # should this be getOffsetBySite(None)?
            highestTimeInsert = insertObject.offset + qL
            lowestOffsetInsert = insertObject.offset

        # this shift is the additional time to move due to the duration
        # of the newly inserted elements

        #environLocal.printDebug(['insertAndShift()', 
        #                         'adding one or more elements', 
        #                         'lowestOffsetInsert', lowestOffsetInsert, 
        #                         'highestTimeInsert', highestTimeInsert])

        # are not assuming that elements are ordered
        # use getElementAtOrAfter() in the future
        lowestElementToShift = None
        lowestGap = None
        for e in self._elements:
            o = self.elementOffset(e)
            # gap is distance from offset to insert point; tells if shift is
            # necessary
            gap = o - lowestOffsetInsert
            if gap < 0: # no shifting necessary
                continue
            # only process elements whose offsets are after the lowest insert
            if lowestGap is None or gap < lowestGap:
                lowestGap = gap
                lowestElementToShift = e

        if lowestElementToShift is not None:
            lowestOffsetToShift = self.elementOffset(lowestElementToShift)
            shiftPos = highestTimeInsert - lowestOffsetToShift
        else:
            shiftPos = 0

        if shiftPos <= 0:
            pass  # no need to move any objects
        # See testStream.py - testInsertAndShiftNoDuration clef 
        #      insertion at offset 3 which gives shiftPos < 0
        else:
            # need to move all the elements already in this stream
            for e in self._elements:
                o = self.elementOffset(e)
                # gap is distance from offset to insert point; tells if shift is
                # necessary
                gap = o - lowestOffsetInsert
                # only process elments whose offsets are after the lowest insert
                if gap >= 0.0:
                    #environLocal.printDebug(['insertAndShift()', e, 'offset', o, 
                    #                         'gap:', gap, 'shiftDur:', shiftDur, 
                    #                         'shiftPos:', shiftPos, 'o+shiftDur', o+shiftDur, 
                    #                         'o+shiftPos', o+shiftPos])

                    # need original offset, shiftDur, plus the distance from the start
                    self.setElementOffset(e, o+shiftPos)
        # after shifting all the necessary elements, append new ones
        # these will not be in order
        self.insert(offsetOrItemOrList, itemOrNone)
        # call this is elements are now out of order
        self.elementsChanged()

    #---------------------------------------------------------------------------
    # searching and replacing routines

    def replace(self, 
                target, 
                replacement, 
                recurse=False,
                allDerived=True):
        '''
        Given a `target` object, replace all references of that object with
        references to the supplied `replacement` object.

        If `allDerived` is True (as it is by default), all sites that
        have a reference for the replacement will be similarly changed.
        This is useful for altering both a flat and nested representation.
        
        firstMatchOnly did NOTHING because each element can only be in a site ONCE.
        Removed!
        
        allTargetSites RENAMED to allDerived -- only searches in derivation chain.
        
        
        >>> csharp = note.Note("C#4")
        >>> s = stream.Stream()
        >>> s.insert(0, csharp)
        >>> dflat = note.Note("D-4")
        >>> s.replace(csharp, dflat)
        >>> s.show('t')
        {0.0} <music21.note.Note D->
        
        If allDerived is True then all streams that this stream comes from get changed 
        (but not non-derived streams)
        
        >>> otherStream = stream.Stream()
        >>> otherStream.insert(0, dflat)
        >>> f = note.Note('F4')
        >>> sf = s.flat
        >>> sf is not s
        True
        >>> sf.replace(dflat, f, allDerived=True)
        >>> sf[0] is f
        True
        >>> s[0] is f
        True
        >>> otherStream[0] is dflat
        True
        
        OMIT_FROM_DOCS
        
        Yes, you can recurse, but not showing it yet... gotta find a good general form...
        and figure out how to make it work properly with allDerived
        
        >>> s = stream.Score()
        >>> p = stream.Part()
        >>> s.append(p)
        >>> m = stream.Measure()
        >>> p.append(m)
        >>> csharp = note.Note("C#4")
        >>> m.append(csharp)
        >>> s.show('t')
        {0.0} <music21.stream.Part 0x109842f98>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.note.Note C#>
                        
        OMIT_FROM_DOCS
        
        Recurse temporarily turned off.
        
        >>> dflat = note.Note("D-4")
        >>> s.replace(csharp, dflat, recurse=True)
        >>> # s.show('t')
        
        {0.0} <music21.stream.Part 0x109842f98>
            {0.0} <music21.stream.Measure 0 offset=0.0>
                {0.0} <music21.note.Note D->        
        '''
        try:
            i = self.index(target)
        except StreamException:
            return  # do nothing if no match
 
        eLen = len(self._elements)
        if i < eLen:
            target = self._elements[i] # target may have been obj id; reclassing
            self._elements[i] = replacement
            # place the replacement at the old objects offset for this site
            self.setElementOffset(replacement, self.elementOffset(target))
            replacement.sites.add(self)
        else:
            # target may have been obj id; reassign
            target = self._endElements[i - eLen]
            self._endElements[i - eLen] = replacement
            self.setElementOffset(replacement, 'highestTime')
            replacement.sites.add(self)
 
        target.sites.remove(self)
        target.activeSite = None
        if id(target) in self._offsetDict:
            del(self._offsetDict[id(target)])
             
 
        updateIsFlat = False
        if replacement.isStream:
            updateIsFlat = True
        # elements have changed: sort order may change b/c have diff classes
        self.elementsChanged(updateIsFlat=updateIsFlat)            
        
#         if target is None:
#             raise StreamException('received a target of None as a candidate for replacement.')
#         if recurse is False:
#             iterator = self.iter
#         else:
#             iterator = self.recurse()
#         iterator.addFilter(filter.IsFilter(target))
#  
#  
#         found = False
#         for el in iterator:
#             # el should be target...
#             index = iterator.activeInformation['sectionIndex']
#             # containingStream will be self for non-recursive
#             containingStream = iterator.activeInformation['stream']
#             elementList = iterator.activeElementList
#             found = True
#             break
# 
#         if found:
#             elementList[index] = replacement
#             
#             containingStream.setElementOffset(
#                                         replacement, 
#                                         containingStream.elementOffset(el, stringReturns=True))
#             replacement.sites.add(containingStream)
#             target.sites.remove(containingStream)
#             target.activeSite = None
#             if id(target) in containingStream._offsetDict:
#                 del(containingStream._offsetDict[id(target)])
#             
#             updateIsFlat = False
#             if replacement.isStream:
#                 updateIsFlat = True
#             # elements have changed: sort order may change b/c have diff classes
#             containingStream.elementsChanged(updateIsFlat=updateIsFlat)

        if allDerived:
            for derivedSite in self.derivation.chain():
                for subsite in derivedSite.recurse(streamsOnly=True, skipSelf=False):
                    if subsite in target.sites:
                        subsite.replace(target, 
                                        replacement, 
                                        allDerived=False)

    def splitAtQuarterLength(self, quarterLength, retainOrigin=True,
        addTies=True, displayTiedAccidentals=False, searchContext=True,
        delta=1e-06):
        '''
        This method overrides the method on Music21Object to provide
        similar functionality for Streams.

        Most arguments are passed to Music21Object.splitAtQuarterLength.
        '''
        quarterLength = opFrac(quarterLength)
        if retainOrigin == True:
            sLeft = self
        else:
            sLeft = copy.deepcopy(self)
        # create empty container for right-hand side
        sRight = self.__class__()

        # if this is a Measure or Part, transfer clefs, ts, and key
        if sLeft.isMeasure:
            timeSignatures = sLeft.getTimeSignatures(
                            searchContext=searchContext)
            if len(timeSignatures) > 0:
                sRight.keySignature = copy.deepcopy(timeSignatures[0]) # pylint: disable=attribute-defined-outside-init
            keySignatures = sLeft.getKeySignatures(searchContext=searchContext)
            if len(keySignatures) > 0:
                sRight.keySignature = copy.deepcopy(keySignatures[0]) # pylint: disable=attribute-defined-outside-init
            endClef = sLeft.getContextByClass('Clef')
            if endClef is not None:
                sRight.clef = copy.deepcopy(endClef) # pylint: disable=attribute-defined-outside-init

        if (quarterLength > sLeft.highestTime): # nothing to do
            return sLeft, sRight

        # use quarterLength as start time
        targets = sLeft.getElementsByOffset(quarterLength, sLeft.highestTime,
            includeEndBoundary=True, 
            mustFinishInSpan=False, 
            includeElementsThatEndAtStart=False,
            mustBeginInSpan=False)

        targetSplit = []
        targetMove = []
        # find all those that need to split v. those that need to be movewd
        for t in targets:
            # if target starts before the boundary, it needs to be split
            if sLeft.elementOffset(t) < quarterLength:
                targetSplit.append(t)
            else:
                targetMove.append(t)

        #environLocal.printDebug(['split', targetSplit, 'move', targetMove])

        for t in targetSplit:
            # must retain origina, as a deepcopy, if necessary, has
            # already been made

            # the split point needs to be relative to this element's start
            qlSplit = quarterLength - sLeft.elementOffset(t)
            unused_eLeft, eRight = t.splitAtQuarterLength(qlSplit,
                retainOrigin=True, addTies=addTies,
                displayTiedAccidentals=displayTiedAccidentals, delta=delta)
            # do not need to insert eLeft, as already positioned and
            # altered in-place above
            # it is assumed that anything cut will start at zero
            sRight.insert(0, eRight)

        for t in targetMove:
            sRight.insert(t.getOffsetBySite(sLeft) - quarterLength, t)
            sLeft.remove(t)

        return sLeft, sRight

    #---------------------------------------------------------------------------
    def _recurseRepr(self, 
                     thisStream, 
                     prefixSpaces=0,
                     addBreaks=True, 
                     addIndent=True, 
                     addEndTimes=False, 
                     useMixedNumerals=False):
        '''
        Used by .show('text')


        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> s3 = stream.Stream()
        >>> n1 = note.Note()
        >>> s3.append(n1)
        >>> s2.append(s3)
        >>> s1.append(s2)
        >>> post = s1._recurseRepr(s1, addBreaks=False, addIndent=False)
        >>> post
        '{0.0} <music21.stream.Stream ...> / {0.0} <music21.stream.Stream ...> / {0.0} <music21.note.Note C>'
        '''
        def singleElement(element, indent, thisStream, addEndTimes, useMixedNumerals):
            offGet = element.getOffsetBySite(thisStream)
            if useMixedNumerals:
                off = common.mixedNumeral(offGet)
            else:
                off = common.strTrimFloat(offGet)            
            if addEndTimes is False:
                return indent + "{" + off + "} " + element.__repr__()
            else:
                ql = offGet + element.duration.quarterLength
                if useMixedNumerals:
                    qlStr = common.mixedNumeral(ql)
                else:
                    qlStr = common.strTrimFloat(ql)
                return indent + "{" + off + ' - ' + qlStr + '} ' + element.__repr__()
            
        msg = []
        insertSpaces = 4
        for element in thisStream:
            if addIndent:
                indent = " " * prefixSpaces
            else:
                indent = ''

            #if isinstance(element, Stream):
            if element.isStream:
                msg.append(singleElement(element, indent, thisStream, addEndTimes, useMixedNumerals))
                msg.append(self._recurseRepr(element,
                                             prefixSpaces + insertSpaces,
                                             addBreaks=addBreaks, 
                                             addIndent=addIndent, 
                                             addEndTimes=addEndTimes,
                                             useMixedNumerals=useMixedNumerals))
            else:
                msg.append(singleElement(element, indent, thisStream, addEndTimes, useMixedNumerals))
        if addBreaks:
            msg = '\n'.join(msg)
        else: # use a slashs
            msg = ' / '.join(msg) # use space
        return msg


    def _reprText(self, **keywords):
        '''
        Return a text representation. This methods can be overridden by
        subclasses to provide alternative text representations.

        This is used by .show('text')
        '''
        if 'addEndTimes' in keywords:
            addEndTimes = keywords['addEndTimes']
        else:
            addEndTimes = False
        if 'useMixedNumerals' in keywords:
            useMixedNumerals = keywords['useMixedNumerals']
        else:
            useMixedNumerals = False
        
        return self._recurseRepr(self, 
                                 addEndTimes=addEndTimes, 
                                 useMixedNumerals=useMixedNumerals)

    def _reprTextLine(self, **keywords):
        '''
        Return a text representation without line breaks.
        This methods can be overridden by subclasses to
        provide alternative text representations.
        '''
        return self._recurseRepr(self, addBreaks=False, addIndent=False)



    #---------------------------------------------------------------------------
    # display methods; in the same manner as show() and write()

    def plot(self, *args, **keywords):
        '''Given a method and keyword configuration arguments, create and display a plot.

        Note: plot() requires the Python package matplotib to be installed.

        For details on arguments this function takes, see :func:`~music21.graph.plotStream`.

        Available plots include the following Plot classes:

        :class:`~music21.graph.PlotHistogramPitchSpace`
        :class:`~music21.graph.PlotHistogramPitchClass`
        :class:`~music21.graph.PlotHistogramQuarterLength`

        :class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`
        :class:`~music21.graph.PlotScatterPitchClassQuarterLength`
        :class:`~music21.graph.PlotScatterPitchClassOffset`
        :class:`~music21.graph.PlotScatterPitchSpaceDynamicSymbol`

        :class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`
        :class:`~music21.graph.PlotHorizontalBarPitchClassOffset`

        :class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`
        :class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`
        :class:`~music21.graph.PlotScatterWeightedPitchSpaceDynamicSymbol`

        :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`

        :class:`~music21.graph.PlotWindowedKrumhanslSchmuckler`
        :class:`~music21.graph.PlotWindowedKrumhanslKessler`
        :class:`~music21.graph.PlotWindowedAardenEssen`
        :class:`~music21.graph.PlotWindowedSimpleWeights`
        :class:`~music21.graph.PlotWindowedBellmanBudge`
        :class:`~music21.graph.PlotWindowedTemperleyKostkaPayne`
        :class:`~music21.graph.PlotWindowedAmbitus`

        :class:`~music21.graph.PlotDolan`


        >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
        >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
        >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
        >>> #_DOCS_SHOW s.plot('pianoroll')

        .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
            :width: 600

        '''
        # import is here to avoid import of matplotlib problems
        from music21 import graph
        # first ordered arg can be method type
        graph.plotStream(self, *args, **keywords)


    def analyze(self, *args, **keywords):
        '''
        Runs a particular analytical method on the contents of the
        stream to find its ambitus (range) or key.

        *  ambitus -- runs :class:`~music21.analysis.discrete.Ambitus`
        *  key -- runs :class:`~music21.analysis.discrete.KrumhanslSchmuckler`

        Some of these methods can take additional arguments.  For details on
        these arguments, see
        :func:`~music21.analysis.discrete.analyzeStream`.

        Example:


        >>> s = corpus.parse('bach/bwv66.6')
        >>> s.analyze('ambitus')
        <music21.interval.Interval m21>
        >>> s.analyze('key')
        <music21.key.Key of f# minor>

        Example: music21 allows you to automatically run an
        analysis to get the key of a piece or excerpt not
        based on the key signature but instead on the
        frequency with which some notes are used as opposed
        to others (first described by Carol Krumhansl).  For
        instance, a piece with mostly Cs and Gs, some Fs,
        and Ds, but fewer G#s, C#s, etc. is more likely to
        be in the key of C major than in D-flat major
        (or A minor, etc.).  You can easily get this analysis
        from a stream by running:

        >>> myStream = corpus.parse('luca/gloria')
        >>> analyzedKey = myStream.analyze('key')
        >>> analyzedKey
        <music21.key.Key of F major>

        analyzedKey is a :class:`~music21.key.Key`
        object with a few extra parameters.
        correlationCoefficient shows how well this key fits the
        profile of a piece in that key:

        >>> analyzedKey.correlationCoefficient
        0.86715...

        `alternateInterpretations` is a list of the other
        possible interpretations sorted from most likely to least:

        >>> analyzedKey.alternateInterpretations
        [<music21.key.Key of d minor>, <music21.key.Key of C major>, <music21.key.Key of g minor>,...]

        Each of these can be examined in turn to see its correlation coefficient:

        >>> analyzedKey.alternateInterpretations[1].correlationCoefficient
        0.788528...
        >>> analyzedKey.alternateInterpretations[22].correlationCoefficient
        -0.86728...
        '''

        from music21.analysis import discrete
        # pass this stream to the analysis procedure
        return discrete.analyzeStream(self, *args, **keywords)

    #---------------------------------------------------------------------------
    # methods that act on individual elements without requiring
    # @ elementsChanged to fire

    def addGroupForElements(self, group, classFilter=None):
        '''
        Add the group to the groups attribute of all elements.
        if `classFilter` is set then only those elements whose objects
        belong to a certain class (or for Streams which are themselves of
        a certain class) are set.

        >>> a = stream.Stream()
        >>> a.repeatAppend(note.Note('A-'), 30)
        >>> a.repeatAppend(note.Rest(), 30)
        >>> a.addGroupForElements('flute')
        >>> a[0].groups
        ['flute']
        >>> a.addGroupForElements('quietTime', note.Rest)
        >>> a[0].groups
        ['flute']
        >>> a[50].groups
        ['flute', 'quietTime']
        >>> a[1].groups.append('quietTime') # set one note to it
        >>> a[1].step = "B"
        >>> b = a.getElementsByGroup('quietTime')
        >>> len(b)
        31
        >>> c = b.getElementsByClass(note.Note)
        >>> len(c)
        1
        >>> c[0].name
        'B-'
        '''
        iterator = self.iter
        if classFilter is not None:
            iterator.addFilter(filter.ClassFilter(classFilter))
        for el in iterator:
            el.groups.append(group)


    #---------------------------------------------------------------------------
    # getElementsByX(self): anything that returns a collection of Elements 
    #  formerly always returned a Stream; turning to Iterators in September 2015

    def getElementsByClass(self, classFilterList, returnStreamSubClass=True):
        '''
        Return a Stream containing all Elements that match one
        or more classes in the `classFilterList`. A single class
        can also used for the `classFilterList` parameter instead of a List.

        >>> a = stream.Score()
        >>> a.repeatInsert(note.Rest(), list(range(10)))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.getElementsByClass(note.Note)
        >>> "Score" in found.classes
        True
        >>> len(found)
        4
        >>> found[0].pitch.accidental.name
        'sharp'


        Notice that we do not find elements that are in
        sub-streams of the main Stream.  We'll add 15 more rests
        in a sub-stream and they won't be found:

        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), list(range(15)))
        >>> a.insert(b)
        >>> found = a.getElementsByClass(note.Rest)
        >>> len(found)
        10

        To find them either (1) use `.flat` to get at everything:

        >>> found = a.flat.getElementsByClass(note.Rest)
        >>> len(found)
        25

        Or, (2) recurse over the main stream and call .getElementsByClass
        on each one.  Notice that the first subStream is actually the outermost
        Stream:

        >>> totalFound = 0
        >>> for subStream in a.recurse(streamsOnly=True):
        ...     found = subStream.getElementsByClass(note.Rest)
        ...     totalFound += len(found)
        >>> totalFound
        25

        The class name of the Stream created is the same as the original:

        >>> found = a.getElementsByClass(note.Note)
        >>> found.__class__.__name__
        'Score'

        ...except if `returnStreamSubClass` is False, which makes the method
        return a generic Stream:

        >>> found = a.getElementsByClass(note.Rest, returnStreamSubClass=False)
        >>> found.__class__.__name__
        'Stream'


        If `returnStreamSubClass` == 'list' then a generic list is returned.
        Generally not to be used, but can help in certain speed-critical applications
        where say only the length of the returned list or the presence or absence of elements matters:

        >>> foundList = a.flat.getElementsByClass(note.Rest, returnStreamSubClass='list')
        >>> len(foundList)
        25

        :rtype: Stream
        '''
        iterator = self.iter.getElementsByClass(classFilterList)
        if returnStreamSubClass == 'list':
            return iterator.matchingElements()
        else:
            return iterator.stream(returnStreamSubClass=returnStreamSubClass)

        # this was 11 micro-sec for BWV 66.6, getElementsByClass('Part', 'list')
        # and 85 w/o list before changing to .iter (and adding mergeAttributes, etc.)
        # how close can we get?
        
        # mergeAttributes added 22 microseconds and should have been done before.  
        # So fair comparison is
        # 107 for old vs. 133 for new.  -- acceptable.

    def getElementsNotOfClass(self, classFilterList, returnStreamSubClass=True):
        '''
        Return a list of all Elements that do not
        match the one or more classes in the `classFilterList`.

        In lieu of a list, a single class can be used as the `classFilterList` parameter.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Rest(), list(range(10)))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.getElementsNotOfClass(note.Note)
        >>> len(found)
        10

        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), list(range(15)))
        >>> a.insert(b)
        >>> # here, it gets elements from within a stream
        >>> # this probably should not do this, as it is one layer lower
        >>> found = a.flat.getElementsNotOfClass(note.Rest)
        >>> len(found)
        4
        >>> found = a.flat.getElementsNotOfClass(note.Note)
        >>> len(found)
        25
        
        :rtype: Stream
        '''
        iterator = self.iter.getElementsNotOfClass(classFilterList)
        if returnStreamSubClass == 'list':
            return iterator.matchingElements()
        else:
            return iterator.stream(returnStreamSubClass=returnStreamSubClass)


    def getElementsByGroup(self, groupFilterList):
        '''
        >>> n1 = note.Note("C")
        >>> n1.groups.append('trombone')
        >>> n2 = note.Note("D")
        >>> n2.groups.append('trombone')
        >>> n2.groups.append('tuba')
        >>> n3 = note.Note("E")
        >>> n3.groups.append('tuba')
        >>> s1 = stream.Stream()
        >>> s1.append(n1)
        >>> s1.append(n2)
        >>> s1.append(n3)
        >>> tboneSubStream = s1.getElementsByGroup("trombone")
        >>> for thisNote in tboneSubStream:
        ...     print(thisNote.name)
        C
        D
        >>> tubaSubStream = s1.getElementsByGroup("tuba")
        >>> for thisNote in tubaSubStream:
        ...     print(thisNote.name)
        D
        E

        OMIT_FROM_DOCS
        # TODO: group comparisons are not YET case insensitive.
        '''
        return self.iter.getElementsByGroup(
                    groupFilterList).stream()
                    

    def getElementById(self, elementId, classFilter=None):
        '''
        Returns the first encountered element for a given id. Return None
        if no match. Note: this uses the id attribute stored on elements, 
        which may not be the same as id(e).

        >>> a = stream.Stream()
        >>> ew = note.Note()
        >>> a.insert(0, ew)
        >>> a[0].id = 'green'
        >>> None == a.getElementById(3)
        True
        >>> a.getElementById('green').id
        'green'
        >>> a.getElementById('Green').id  # case does not matter
        'green'

        Getting an element by getElementById changes its activeSite

        >>> b = stream.Stream()
        >>> b.append(ew)
        >>> ew.activeSite is b
        True
        >>> ew2 = a.getElementById('green')
        >>> ew2 is ew
        True
        >>> ew2.activeSite is a
        True
        >>> ew.activeSite is a
        True
        
        :rtype: base.Music21Object
        '''
        iterator = self.iter.addFilter(filter.IdFilter(elementId))
        if classFilter is not None:
            iterator.getElementsByClass(classFilter)
        for e in iterator:
            return e
        return None


    def getElementsByOffset(self, 
                            offsetStart, 
                            offsetEnd=None,
                            includeEndBoundary=True,
                            mustFinishInSpan=False,
                            mustBeginInSpan=True, 
                            includeElementsThatEndAtStart=True, 
                            classList=None):
        '''
        Returns a Stream containing all Music21Objects that
        are found at a certain offset or within a certain
        offset time range (given the start and optional stop values).

        There are several attributes that govern how this range is
        determined:


        If `mustFinishInSpan` is True then an event that begins
        between offsetStart and offsetEnd but which ends after offsetEnd
        will not be included.  The default is False.


        For instance, a half note at offset 2.0 will be found in
        getElementsByOffset(1.5, 2.5) or getElementsByOffset(1.5, 2.5,
        mustFinishInSpan=False) but not by getElementsByOffset(1.5, 2.5,
        mustFinishInSpan=True).

        The `includeEndBoundary` option determines if an element
        begun just at the offsetEnd should be included.  For instance,
        the half note at offset 2.0 above would be found by
        getElementsByOffset(0, 2.0) or by getElementsByOffset(0, 2.0,
        includeEndBoundary=True) but not by getElementsByOffset(0, 2.0,
        includeEndBoundary=False).

        Setting includeEndBoundary to False at the same time as
        mustFinishInSpan is set to True is probably NOT what you want to do
        unless you want to find things like clefs at the end of the region
        to display as courtesy clefs.

        The `mustBeginInSpan` option determines whether notes or other
        objects that do not begin in the region but are still sounding
        at the beginning of the region are excluded.  The default is
        True -- that is, these notes will not be included.
        For instance the half note at offset 2.0 from above would not be found by
        getElementsByOffset(3.0, 3.5) or getElementsByOffset(3.0, 3.5,
        mustBeginInSpan=True) but it would be found by
        getElementsByOffset(3.0, 3.5, mustBeginInSpan=False)

        Setting includeElementsThatEndAtStart to False is useful for zeroLength
        searches that set mustBeginInSpan == False to not catch notes that were
        playing before the search but that end just before the end of the search type.
        See the code for allPlayingWhileSounding for a demonstration.

        This chart, and the examples below, demonstrate the various
        features of getElementsByOffset.  It is one of the most complex
        methods of music21 but also one of the most powerful, so it
        is worth learning at least the basics.

            .. image:: images/getElementsByOffset.*
                :width: 600




        >>> st1 = stream.Stream()
        >>> n0 = note.Note("C")
        >>> n0.duration.type = "half"
        >>> n0.offset = 0
        >>> st1.insert(n0)
        >>> n2 = note.Note("D")
        >>> n2.duration.type = "half"
        >>> n2.offset = 2
        >>> st1.insert(n2)
        >>> out1 = st1.getElementsByOffset(2)
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = st1.getElementsByOffset(1, 3)
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = st1.getElementsByOffset(1, 3, mustFinishInSpan=True)
        >>> len(out3)
        0
        >>> out4 = st1.getElementsByOffset(1, 2)
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = st1.getElementsByOffset(1, 2, includeEndBoundary=False)
        >>> len(out5)
        0
        >>> out6 = st1.getElementsByOffset(1, 2, includeEndBoundary=False, mustBeginInSpan=False)
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = st1.getElementsByOffset(1, 3, mustBeginInSpan=False)
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']
        
        
        Note, that elements that end at the start offset are included if mustBeginInSpan is False
        
        >>> out8 = st1.getElementsByOffset(2, 4, mustBeginInSpan=False)
        >>> len(out8)
        2
        >>> [el.step for el in out8]
        ['C', 'D']

        To change this behavior set includeElementsThatEndAtStart=False

        >>> out9 = st1.getElementsByOffset(2, 4, mustBeginInSpan=False, includeElementsThatEndAtStart=False)
        >>> len(out9)
        1
        >>> [el.step for el in out9]
        ['D']



        >>> a = stream.Stream()
        >>> n = note.Note('G')
        >>> n.quarterLength = .5
        >>> a.repeatInsert(n, list(range(8)))
        >>> b = stream.Stream()
        >>> b.repeatInsert(a, [0, 3, 6])
        >>> c = b.getElementsByOffset(2,6.9)
        >>> len(c)
        2
        >>> c = b.flat.getElementsByOffset(2,6.9)
        >>> len(c)
        10


        Testing multiple zero-length elements with mustBeginInSpan:

        >>> c = clef.TrebleClef()
        >>> ts = meter.TimeSignature('4/4')
        >>> ks = key.KeySignature(2)
        >>> s = stream.Stream()
        >>> s.insert(0.0, c)
        >>> s.insert(0.0, ts)
        >>> s.insert(0.0, ks)
        >>> len(s.getElementsByOffset(0.0, mustBeginInSpan=True))
        3
        >>> len(s.getElementsByOffset(0.0, mustBeginInSpan=False))
        3

        OMIT_FROM_DOCS
        
        Same test as above, but with floats
        
        >>> out1 = st1.getElementsByOffset(2.0)
        >>> len(out1)
        1
        >>> out1[0].step
        'D'
        >>> out2 = st1.getElementsByOffset(1.0, 3.0)
        >>> len(out2)
        1
        >>> out2[0].step
        'D'
        >>> out3 = st1.getElementsByOffset(1.0, 3.0, mustFinishInSpan=True)
        >>> len(out3)
        0
        >>> out3b = st1.getElementsByOffset(0.0, 3.001, mustFinishInSpan=True)
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'
        >>> out3b = st1.getElementsByOffset(1.0, 3.001, mustFinishInSpan=True, mustBeginInSpan=False)
        >>> len(out3b)
        1
        >>> out3b[0].step
        'C'


        >>> out4 = st1.getElementsByOffset(1.0, 2.0)
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = st1.getElementsByOffset(1.0, 2.0, includeEndBoundary=False)
        >>> len(out5)
        0
        >>> out6 = st1.getElementsByOffset(1.0, 2.0, includeEndBoundary=False, mustBeginInSpan=False)
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = st1.getElementsByOffset(1.0, 3.0, mustBeginInSpan=False)
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']

        :rtype: Stream
        '''
        iterator = self.iter.getElementsByOffset(
                         offsetStart=offsetStart, 
                         offsetEnd=offsetEnd,
                         includeEndBoundary=includeEndBoundary, 
                         mustFinishInSpan=mustFinishInSpan,
                         mustBeginInSpan=mustBeginInSpan, 
                         includeElementsThatEndAtStart=includeElementsThatEndAtStart)
        if classList is not None:
            iterator.getElementsByClass(classList)
        return iterator.stream()


    def getElementAtOrBefore(self, offset, classList=None):
        '''
        Given an offset, find the element at this offset,
        or with the offset less than and nearest to.

        Return one element or None if no elements are at or preceded by this
        offset.

        If the `classList` parameter is used, it should be a
        list of class names or strings, and only objects that
        are instances of
        these classes or subclasses of these classes will be returned.

        >>> stream1 = stream.Stream()
        >>> x = note.Note('D4')
        >>> x.id = 'x'
        >>> y = note.Note('E4')
        >>> y.id = 'y'
        >>> z = note.Rest()
        >>> z.id = 'z'

        >>> stream1.insert(20, x)
        >>> stream1.insert(10, y)
        >>> stream1.insert( 0, z)

        >>> b = stream1.getElementAtOrBefore(21)
        >>> b.offset, b.id
        (20.0, 'x')

        >>> b = stream1.getElementAtOrBefore(19)
        >>> b.offset, b.id
        (10.0, 'y')

        >>> b = stream1.getElementAtOrBefore(0)
        >>> b.offset, b.id
        (0.0, 'z')
        >>> b = stream1.getElementAtOrBefore(0.1)
        >>> b.offset, b.id
        (0.0, 'z')


        You can give a list of acceptable classes to return, and non-matching
        elements will be ignored

        >>> c = stream1.getElementAtOrBefore(100, [clef.TrebleClef, note.Rest])
        >>> c.offset, c.id
        (0.0, 'z')

        Getting an object via getElementAtOrBefore sets the activeSite
        for that object to the Stream, and thus sets its offset

        >>> stream2 = stream.Stream()
        >>> stream2.insert(100.5, x)
        >>> x.offset
        100.5
        >>> d = stream1.getElementAtOrBefore(20)
        >>> d is x
        True
        >>> x.activeSite is stream1
        True
        >>> x.offset
        20.0

        OMIT_FROM_DOCS
        TODO: include sort order for concurrent matches?

        The sort order of returned items is the reverse
        of the normal sort order, so that, for instance,
        if there's a clef and a note at offset 20,
        getting the object before offset 21 will give
        you the note, and not the clef, since clefs
        sort before notes:

        #>>> clef1 = clef.BassClef()
        #>>> stream1.insert(20, clef1)
        #>>> e = stream1.getElementAtOrBefore(21)
        #>>> e
        #<music21.note.Note D4>
        
        # FAILS, returns the clef!

        '''
        # NOTE: this is a performance critical method
        # TODO: need to deal with more than on object the same
        # offset and span from the source
        
        # TODO: switch to timespans
        candidates = []
        offset = opFrac(offset)
        nearestTrailSpan = offset # start with max time

        # need both _elements and _endElements
        for e in self.elements:
            if classList is not None:
                if not e.isClassOrSubclass(classList):
                    continue
            span = opFrac(offset - self.elementOffset(e))
            #environLocal.printDebug(['e span check', span, 'offset', offset, 'e.offset', e.offset, 'self.elementOffset(e)', self.elementOffset(e), 'e', e])
            if span < 0: 
                continue
            elif span == 0:
                candidates.append((span, e))
                nearestTrailSpan = span
            else:
                # do this comparison because may be out of order
                if span <= nearestTrailSpan:
                    candidates.append((span, e))
                    nearestTrailSpan = span
        #environLocal.printDebug(['getElementAtOrBefore(), e candidates', candidates])
        if len(candidates) > 0:
            candidates.sort(key=lambda x: (-1 * x[0], x[1].sortTuple())) # TODO: this sort has side effects -- see icmc2011 -- sorting clef vs. note, etc.
            candidates[-1][1].activeSite = self
            return candidates[-1][1]
        else:
            return None

#         if len(candidates) == 1:
#             x = candidates[0][1]
#             x.activeSite = self
#             return x
#         elif len(candidates) > 0:
#             s = Stream([x[1] for x in candidates])
#             s.sort() # TODO: this sort has side effects
#             x = s[-1]
#             x.activeSite = self
#             return x
#         else:
#             return None



    def getElementBeforeOffset(self, offset, classList=None):
        '''
        Get element before (and not at) a provided offset.

        If the `classList` parameter is used, it should be a
        list of class names or strings, and only objects that
        are instances of
        these classes or subclasses of these classes will be returned.

        >>> stream1 = stream.Stream()
        >>> x = note.Note('D4')
        >>> x.id = 'x'
        >>> y = note.Note('E4')
        >>> y.id = 'y'
        >>> z = note.Rest()
        >>> z.id = 'z'
        >>> stream1.insert(20, x)
        >>> stream1.insert(10, y)
        >>> stream1.insert( 0, z)

        >>> b = stream1.getElementBeforeOffset(21)
        >>> b.offset, b.id
        (20.0, 'x')
        >>> b = stream1.getElementBeforeOffset(20)
        >>> b.offset, b.id
        (10.0, 'y')

        >>> b = stream1.getElementBeforeOffset(10)
        >>> b.offset, b.id
        (0.0, 'z')

        >>> b = stream1.getElementBeforeOffset(0)
        >>> b is None
        True
        >>> b = stream1.getElementBeforeOffset(0.1)
        >>> b.offset, b.id
        (0.0, 'z')

        >>> w = note.Note('F4')
        >>> w.id = 'w'
        >>> stream1.insert( 0, w)

        This should get w because it was inserted last.
        
        >>> b = stream1.getElementBeforeOffset(0.1)
        >>> b.offset, b.id
        (0.0, 'w')
        
        But if we give it a lower priority than z then z will appear first.
        
        >>> w.priority = z.priority - 1
        >>> b = stream1.getElementBeforeOffset(0.1)
        >>> b.offset, b.id
        (0.0, 'z')
        '''
        # NOTE: this is a performance critical method
        candidates = []
        offset = opFrac(offset)
        nearestTrailSpan = offset # start with max time

        # need both _elements and _endElements
        for e in self.elements:
            if classList is not None:
                if not e.isClassOrSubclass(classList):
                    continue
            span = opFrac(offset - self.elementOffset(e))
            #environLocal.printDebug(['e span check', span, 'offset', offset, 'e.offset', e.offset, 'self.elementOffset(e)', self.elementOffset(e), 'e', e])
            # by forcing <= here, we are sure to get offsets not at zero
            if span <= 0: # the e is after this offset
                continue
            else: # do this comparison because may be out of order
                if span <= nearestTrailSpan:
                    candidates.append((span, e))
                    nearestTrailSpan = span
        #environLocal.printDebug(['getElementBeforeOffset(), e candidates', candidates])
        if len(candidates) > 0:
            candidates.sort(key=lambda x: (-1 * x[0], x[1].sortTuple())) 
            candidates[-1][1].activeSite = self
            return candidates[-1][1]
        else:
            return None



#    def getElementAfterOffset(self, offset, classList=None):
#        '''Get element after a provided offset
#
#        TODO: write this
#        '''
#        raise Exception("not yet implemented")
#
#
#    def getElementBeforeElement(self, element, classList=None):
#        '''given an element, get the element before
#
#        TODO: write this
#        '''
#        raise Exception("not yet implemented")

    def getElementAfterElement(self, element, classList=None):
        '''
        Given an element, get the next element.  If classList is specified,
        check to make sure that the element is an instance of the class list

        >>> st1 = stream.Stream()
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> r3 = note.Rest()
        >>> st1.append([n1, n2, r3])
        >>> t2 = st1.getElementAfterElement(n1)
        >>> t2 is n2
        True
        >>> t3 = st1.getElementAfterElement(t2)
        >>> t3 is r3
        True
        >>> t4 = st1.getElementAfterElement(t3)
        >>> t4

        st1.getElementAfterElement("hi") is None
        True
        
        >>> t5 = st1.getElementAfterElement(n1, [note.Rest])
        >>> t5
        <music21.note.Rest rest>
        >>> t5 is r3
        True
        >>> t6 = st1.getElementAfterElement(n1, [note.Rest, note.Note])
        >>> t6 is n2
        True

        >>> t7 = st1.getElementAfterElement(r3)
        >>> t7 is None
        True
        '''
        try:
            # index() ultimately does an autoSort check, so no check here or
            # sorting is necessary
            elPos = self.index(element)
        except ValueError:
            raise StreamException("Could not find element in index")
        # store once as a property call concatenates
        elements = self.elements
        if classList is None:
            if elPos == len(elements) - 1:
                return None        
            else:
                e = elements[elPos + 1]
                e.activeSite = self
                return e                
        else:
            for i in range(elPos + 1, len(elements)):
                if elements[i].isClassOrSubclass(classList):
                    e = elements[i]
                    e.activeSite = self
                    return e

#         iterator = self.iter
#         isFilter = filter.IsFilter(element)
#         iterator.addFilter(isFilter)
# 
#         foundElement = False
#         for x in iterator:
#             if foundElement is True:
#                 return x # it is the element after
#             else:
#                 foundElement = True
#                 iterator.removeFilter(isFilter)
#                 # now add the filter... 
#                 iterator.addFilter(filter.IsNotFilter(element))
#                 if classList is not None:
#                     iterator.addFilter(filter.ClassFilter(classList))
# 
#         return None

    #-----------------------------------------------------
    # end .getElement filters
    
    
    @common.deprecated("September 2015", "February 2016", "use s.elementOffset() instead w/ a try/except")
    def getOffsetByElement(self, obj):
        '''
        DEPRECATED Sep 2015: use s.elementOffset(obj) and if it is possible that
        obj is not in s, then do a try: except base.SitesException
        
        Remove in 2016 Feb.
        '''
        try:
            return self.elementOffset(obj)
        except base.SitesException:
            return None


    def groupElementsByOffset(self, returnDict=False):
        '''
        Returns a List of lists in which each entry in the
        main list is a list of elements occurring at the same time.
        list is ordered by offset (since we need to sort the list
        anyhow in order to group the elements), so there is
        no need to call stream.sorted before running this.

        if returnDict is True then it returns a dictionary of offsets
        and everything at that offset.  If returnDict is False (default)
        then only a list of lists of elements grouped by offset is returned.
        (in other words, you'll need to call self.elementOffset(list[i][0]) to
        get the offset)

        >>> from pprint import pprint as pp
        >>> s = stream.Stream()
        >>> s.insert(3, note.Note('C'))
        >>> s.insert(4, note.Note('C#'))
        >>> s.insert(4, note.Note('D-'))
        >>> s.insert(16.0/3, note.Note('D'))

        >>> returnList = s.groupElementsByOffset()
        >>> returnList
        [[<music21.note.Note C>], 
         [<music21.note.Note C#>, <music21.note.Note D->], 
         [<music21.note.Note D>]]

        >>> returnDict = s.groupElementsByOffset(returnDict=True)
        >>> pp(returnDict)
        {3.0: [<music21.note.Note C>], 
         4.0: [<music21.note.Note C#>, <music21.note.Note D->], 
         Fraction(16, 3): [<music21.note.Note D>]}
        
        Test that sorting still works...

        >>> s.insert(0, meter.TimeSignature('2/4'))
        >>> s.insert(0, clef.TrebleClef()) # sorts first
        >>> s.groupElementsByOffset()[0]
        [<music21.clef.TrebleClef>, <music21.meter.TimeSignature 2/4>]

        it is DEFINITELY a feature that this method does not
        find elements within substreams that have the same
        absolute offset.  See lily.translate for how this is
        useful for finding voices.  
        
        For the other behavior, call Stream.flat first or Stream.recurse()
        '''
        offsetsRepresented = {}
        for el in self.elements:
            elOff = self.elementOffset(el)
            if elOff not in offsetsRepresented:
                offsetsRepresented[elOff] = []
            offsetsRepresented[elOff].append(el)

        if returnDict is True:
            return offsetsRepresented
        else:
            offsetList = []
            for thisOffset in sorted(offsetsRepresented):
                offsetList.append(offsetsRepresented[thisOffset])
            return offsetList



    #--------------------------------------------------------------------------
    # routines for obtaining specific types of elements from a Stream
    # _getNotes and _getPitches are found with the interval routines

    def measures(self, 
                 numberStart, 
                 numberEnd,
                 collect=('Clef', 'TimeSignature', 'Instrument', 'KeySignature'), 
                 gatherSpanners=True, 
                 ignoreNumbers=False):
        '''
        Get a region of Measures based on a start and end Measure number, 
        where the boundary numbers are both included. 
        That is, a request for measures 4 through 10 will return 7 Measures, numbers 4 through 10.
        It is allowed to pass `numberEnd=None`, which will be 
        interpreted as the last measure of the stream.

        Additionally, any number of associated classes can be gathered as well. 
        Associated classes are the last found class relevant to this Stream or Part.

        While all elements in the source are the original elements in the extracted region, 
        new Measure objects are created and returned.

        >>> a = corpus.parse('bach/bwv324.xml')
        >>> b = a.parts[0].measures(1,3)
        >>> len(b.getElementsByClass('Measure'))
        3
        >>> b.getElementsByClass('Measure')[0].notes[0] is a.parts[0].flat.notes[0]
        True

        if gatherSpanners is True or the string 'all' then all spanners in the score are gathered and
        included.  TODO: make True only return spanners from the region.

        if ignoreNumbers is True, then it ignores defined measureNumbers and 
        uses 0-indexed measure objects
        '''
        returnObj = self.cloneEmpty(derivationMethod='measures')
        srcObj = self

        # create a dictionary of measure number: list of Meaures
        # there may be more than one Measure with the same Measure number
        mapRaw = {}
        mNumbersUnique = [] # store just the numbers
        mStreamList = self.getElementsByClass('Measure', returnStreamSubClass='list')
        # if we have no Measures defined, call makeNotation
        # this will  return a deepcopy of all objects
        if len(mStreamList) == 0:
            srcObj = self.makeNotation(inPlace=False)
            # need to set srcObj to this new stream
            mStreamList = srcObj.getElementsByClass('Measure', returnStreamSubClass='list')
            # get spanners from make notation, as this will be a copy
            # TODO: make sure that makeNotation copies spanners
            #mStreamSpanners = mStream.spanners

        # spanners may be store at the container/Part level, not w/n a measure
        # if they are within the Measure, or a voice, they will be transfered
        # below
        # create empty bundle in case not created by other means
        spannerBundle = spanner.SpannerBundle()
        if gatherSpanners:
            spannerBundle = srcObj.spannerBundle

        for index, m in enumerate(mStreamList):
            #environLocal.printDebug(['m', m])
            # mId is a tuple of measure nmber and any suffix
            if ignoreNumbers is False:
                try:
                    mNumber = int(m.number)
                except ValueError:
                    raise StreamException('found problematic measure number: %s' % mNumber)
                # id combines suffice w/ number
                mId = (mNumber, m.numberSuffix)
            else:
                mNumber = index
                mId = (index, None)
            # store unique measure numbers for reference
            if mNumber not in mNumbersUnique:
                mNumbersUnique.append(mNumber)
            if mId not in mapRaw:
                mapRaw[mId] = [] # use a list
            # these will be in order by measure number
            # there may be multiple None and/or 0 measure numbers
            mapRaw[mId].append(m)

        #environLocal.printDebug(['len(mapRaw)', len(mapRaw)])
        #environLocal.printDebug(['mNumbersUnique', mNumbersUnique])

        # if measure numbers are not defined, we should just count them
        # in order, starting from 1
        if len(mNumbersUnique) == 1:
            #environLocal.printDebug(['measures()', 'attempting to assign measures order numbers'])
            mapCooked = {}
            # only one key but we do not know what it is
            i = 1
            for number, suffix in mapRaw:
                for m in mapRaw[(number, suffix)]:
                    # expecting a list of measures
                    mapCooked[(i, None)] = [m]
                    i += 1
        else:
            mapCooked = mapRaw

        #environLocal.printDebug(['mapCooked', mapCooked])
        #environLocal.printDebug(['len(mapCooked)', len(mapCooked)])
        startOffset = None # set with the first measure
        startMeasure = None # store for adding other objects
        # get requested range
        #startMeasureNew = None
        # if end not specified, get last
        if numberEnd is None:
            numberEnd = max([x for x, dummy in mapCooked])
        #environLocal.printDebug(['numberStart', numberStart, 'numberEnd', numberEnd])

        for i in range(numberStart, numberEnd+1):
            matches = []
            # do not know if we have suffixes for the number
            for number, suffix in mapCooked:
                # this will match regardless of suffix
                # numbers may be strings still
                if number == i:
                    matches.append(mapCooked[(number, suffix)])
            # numbers may not be contiguous
            if len(matches) == 0: # None found in this range
                continue
            # if not startOffset then let us make one
            # this assumes measure are in offset order
            # this may not always be the case
            if startOffset is None:
                # is m 2X before 2 or after? can't be sure,
                # so we get the min...
                for mWithSameId in matches:
                    for m in mWithSameId:
                        thisOffset = m.getOffsetBySite(srcObj)
                        if startOffset is None:
                            startOffset = thisOffset # most common
                            startMeasure = m
                        else: # suffixes -- should check priority!
                            if thisOffset < startOffset:
                                startOffset = thisOffset
                                startMeasure = m
                #environLocal.printDebug(['startOffset', startOffset, 'startMeasure', startMeasure, 'm', m])

            # need to make offsets relative to this new Stream
            for mWithSameId in matches:
                for m in mWithSameId:
                    # get offset before doing spanner updates; not sure why yet
                    oldOffset = m.getOffsetBySite(srcObj)
                    # create a new Measure container, but populate it
                    # with the same elements

                    # using the same measure in the return obj
                    newOffset = oldOffset - startOffset
                    returnObj._insertCore(newOffset, m)

        # manipulate startMeasure to add desired context objects
        changedObjects = False
        for className in collect:
            # first, see if it is in this Measure
            if startMeasure is None or startMeasure.hasElementOfClass(className):
                continue

            # placing missing objects in outer container, not Measure
            found = srcObj.flat.getElementAtOrBefore(startOffset, [className])
            if found is not None:
                if startMeasure is not None:
                    found.priority = startMeasure.priority - 1
                    # TODO: This should not change global priority on found, but
                    # instead priority, like offset, should be a per-site attribute
                returnObj._insertCore(0, found)
                changedObjects = True
            # search the flat caller stream, which is usually a Part
            # need to search self, as we ne need to get the instrument
#             found = srcObj.flat.getElementAtOrBefore(startOffset, [className])
#             if found is not None:
#                 startMeasureNew._insertCore(0, found)
#
#
#         # as we have inserted elements, need to call
#         startMeasureNew.elementsChanged()
        if changedObjects:
            returnObj.elementsChanged()
            
        if gatherSpanners:
            for sp in spannerBundle:
                # can use old offsets of spanners, even though components
                # have been updated
                #returnObj.insert(sp.getOffsetBySite(mStreamSpanners), sp)
                returnObj._insertCore(sp.getOffsetBySite(srcObj.flat), sp)

                #environLocal.printDebug(['Stream.measrues: copying spanners:', sp])

        # used _insertcore
        returnObj.elementsChanged()
        #environLocal.printDebug(['len(returnObj.flat)', len(returnObj.flat)])
        return returnObj


    def measure(self, 
                measureNumber,
                collect=('Clef', 'TimeSignature', 'Instrument', 'KeySignature'),
                ignoreNumbers=False):
        '''
        Given a measure number, return a single
        :class:`~music21.stream.Measure` object if the Measure number exists, otherwise return None.

        This method is distinguished from :meth:`~music21.stream.Stream.measures`
        in that this method returns a single Measure object, not a Stream containing
        one or more Measure objects.


        >>> a = corpus.parse('bach/bwv324.xml')
        >>> a.parts[0].measure(3)
        <music21.stream.Measure 3 offset=8.0>

        OMIT_FROM_DOCS

        Getting a non-existent measure should return None, but it doesnt!

        #>>> print(a.measure(0))
        #None
        '''
        # we must be able to obtain a measure from this (not a flat)
        # representation (e.g., this is a Stream or Part, not a Score)
        if len(self.getElementsByClass('Measure', returnStreamSubClass='list')) >= 1:
            #environLocal.printDebug(['got measures from getElementsByClass'])
            s = self.measures(measureNumber, 
                              measureNumber, 
                              collect=collect,
                              ignoreNumbers=ignoreNumbers)
            if len(s) == 0:
                return None
            else:
                m = s.getElementsByClass('Measure', returnStreamSubClass='list')[0]
                # NO m is the same object as before so it does not get a new derivation                
#                 m.derivation.client = m
#                 m.derivation.origin = s # was self, will change some things
#                 m.derivation.method = 'measure'
                m.activeSite = self # this sets its offset to something meaningful...
                return m
        else:
            #environLocal.printDebug(['got not measures from getElementsByClass'])
            return None


    def measureTemplate(self, 
                        fillWithRests=True, 
                        classType='Measure', 
                        customRemove=None):
        '''
        If this Stream contains measures, return a new Stream
        with new Measures populated with the same characteristics of those found in this Stream.

        That is, TimeSignatures, KeySignatures, etc. are retained.
        
        >>> b = corpus.parse('bwv66.6')
        >>> sopr = b.parts[0]
        >>> soprEmpty = sopr.measureTemplate()
        >>> soprEmpty.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.key.KeySignature of 3 sharps, mode minor>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Rest rest>
        {1.0} <music21.stream.Measure 1 offset=1.0>
            {0.0} <music21.note.Rest rest>
        {5.0} <music21.stream.Measure 2 offset=5.0>
            {0.0} <music21.note.Rest rest>
        {9.0} <music21.stream.Measure 3 offset=9.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.note.Rest rest>
        {13.0} <music21.stream.Measure 4 offset=13.0>
        ...
        
        
        Really make empty with fillWithRests = False
        
        >>> alto = b.parts[1]
        >>> altoEmpty = alto.measureTemplate(fillWithRests=False)
        >>> altoEmpty.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.key.KeySignature of 3 sharps, mode minor>
            {0.0} <music21.meter.TimeSignature 4/4>
        {1.0} <music21.stream.Measure 1 offset=1.0>
        <BLANKLINE>
        {5.0} <music21.stream.Measure 2 offset=5.0>
        <BLANKLINE>
        {9.0} <music21.stream.Measure 3 offset=9.0>
            {0.0} <music21.layout.SystemLayout>
        ...
        
        
        customRemove can be a list of classes to remove.  By default it is
        ['GeneralNote', 'Stream', 'Dynamic', 'Expression']
        
        if GeneralNote is not included in customRemove, make sure fillWithRests is False
        
        >>> tenor = b.parts[2]
        >>> tenorNoClefsSignatures = tenor.measureTemplate(fillWithRests=False, 
        ...       customRemove=['Clef','KeySignature','TimeSignature'])
        >>> tenorNoClefsSignatures.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {0.5} <music21.note.Note B>
        {1.0} <music21.stream.Measure 1 offset=1.0>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {5.0} <music21.stream.Measure 2 offset=5.0>
        ...
        
        
        Setting customRemove to True removes everything:
        
        >>> bass = b.parts[3]
        >>> bassEmpty = bass.measureTemplate(fillWithRests=False, customRemove=True)
        >>> bassEmpty.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
        <BLANKLINE>
        {1.0} <music21.stream.Measure 1 offset=1.0>
        <BLANKLINE>
        {5.0} <music21.stream.Measure 2 offset=5.0>
        <BLANKLINE>
        {9.0} <music21.stream.Measure 3 offset=9.0>
        <BLANKLINE>
        {13.0} <music21.stream.Measure 4 offset=13.0>
        <BLANKLINE>
        ...
        
        
        classType explains what to extract.  Might be Voice, etc. 
        
        Is not recursive, so cannot template a whole Score...yet.
        TODO: rename to template -- set default to Stream not Measure, add recurse...
        '''
        if not self.hasMeasures():
            raise StreamException('the requested Stream does not have Measures')
        # should this be deepcopy or just a recursive call...
        measureTemplate = copy.deepcopy(self.getElementsByClass(classType))
        for m in measureTemplate:
            ql = m.duration.quarterLength
            if customRemove is not None:
                if customRemove is True:
                    m.removeByClass('Music21Object')
                else:
                    m.removeByClass(customRemove)
            else:
                #                 + rests    voices/substreams
                m.removeByClass(['GeneralNote', 'Stream', 'Dynamic', 'Expression'])

            if fillWithRests:
                if self.id == 'Soprano':
                    pass
                # quarterLength duration will be appropriate to pickup
                m.insert(0.0, note.Rest(quarterLength=ql))
        return measureTemplate

    def measureOffsetMap(self, classFilterList=None):
        '''
        If this Stream contains Measures, provide a dictionary
        whose keys are the offsets of the start of each measure
        and whose values are a list of references
        to the :class:`~music21.stream.Measure` objects that start
        at that offset.

        Even in normal music there may be more than
        one Measure starting at each offset because each
        :class:`~music21.stream.Part` might define its own Measure.
        However, you are unlikely to encounter such things unless you
        run Score.semiFlat, which retains all the containers found in
        the score.

        The offsets are always measured relative to the
        calling Stream (self).

        You can specify a `classFilterList` argument as a list of classes
        to find instead of Measures.  But the default will of course
        find Measure objects.

        Example 1: This Bach chorale is in 4/4 without a pickup, so
        as expected, measures are found every 4 offsets, until the
        weird recitation in m. 7 which in our edition lasts 10 beats
        and thus causes a gap in measureOffsetMap from 24.0 to 34.0.

        .. image:: images/streamMeasureOffsetMapBWV324.*
            :width: 572


        >>> chorale = corpus.parse('bach/bwv324.xml')
        >>> alto = chorale.parts['alto']
        >>> altoMeasures = alto.measureOffsetMap()
        >>> sorted(altoMeasures)
        [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 34.0, 38.0]

        altoMeasures is a dictionary (hash) of the measures
        that are found in the alto part, so we can get
        the measure beginning on offset 4.0 (measure 2)
        and display it (though it's the only measure
        found at offset 4.0, there might be others as
        in example 2, so we need to call altoMeasures[4.0][0]
        to get this measure.):

        >>> altoMeasures[4.0]
        [<music21.stream.Measure 2 offset=4.0>]
        >>> altoMeasures[4.0][0].show('text')
        {0.0} <music21.note.Note D>
        {1.0} <music21.note.Note D#>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note F#>

        Example 2: How to get all the measures from all parts (not the
        most efficient way, but it works!).  Note that
        you first need to call semiFlat, which finds all containers
        (and other elements) nested inside all parts:

        >>> choraleSemiFlat = chorale.semiFlat
        >>> choraleMeasures = choraleSemiFlat.measureOffsetMap()
        >>> choraleMeasures[4.0]
        [<music21.stream.Measure 2 offset=4.0>, 
         <music21.stream.Measure 2 offset=4.0>, 
         <music21.stream.Measure 2 offset=4.0>, 
         <music21.stream.Measure 2 offset=4.0>]

        OMIT_FROM_DOCS
        see important examples in testMeasureOffsetMap() andtestMeasureOffsetMapPostTie()
        '''
        if classFilterList is None:
            classFilterList = [Measure]
        elif not isinstance(classFilterList, (list, tuple)):
            classFilterList = [classFilterList]

        #environLocal.printDebug(['calling measure offsetMap()'])

        #environLocal.printDebug([classFilterList])
        offsetMap = {}
        # first, try to get measures
        # this works best of this is a Part or Score
        if Measure in classFilterList or 'Measure' in classFilterList:
            for m in self.getElementsByClass('Measure'):
                offset = self.elementOffset(m)
                if offset not in offsetMap:
                    offsetMap[offset] = []
                # there may be more than one measure at the same offset
                offsetMap[offset].append(m)

        # try other classes
        for className in classFilterList:
            if className in [Measure or 'Measure']: # do not redo
                continue
            for e in self.iter.getElementsByClass(className):
                #environLocal.printDebug(['calling measure offsetMap(); e:', e])
                # NOTE: if this is done on Notes, this can take an extremely
                # long time to process
                # 'reverse' here is a reverse sort, where oldest objects are returned
                # first
                m = e.getContextByClass('Measure') #, sortByCreationTime='reverse')
                if m is None:
                    continue
                # assuming that the offset returns the proper offset context
                # this is, the current offset may not be the stream that
                # contains this Measure; its current activeSite
                offset = m.offset
                if offset not in offsetMap:
                    offsetMap[offset] = []
                if m not in offsetMap[offset]:
                    offsetMap[offset].append(m)
        return offsetMap


    def _getFinalBarline(self):
        # if we have part-like streams, process each part
        if self.hasPartLikeStreams():
            post = []
            for p in self.getElementsByClass('Stream'):
                post.append(p._getFinalBarline())
            return post # a list of barlines
        # core routines for a single Stream
        else:
            if self.hasMeasures():
                return self.getElementsByClass('Measure')[-1].rightBarline
            else:
                raise StreamException('cannot get a final barline from this Stream if no Measures are defined. Add Measures or call makeMeasures() first.')

    def _setFinalBarline(self, value):
        # if we have part-like streams, process each part
        if self.hasPartLikeStreams():
            if not common.isListLike(value):
                value = [value]
            for i, p in enumerate(self.getElementsByClass('Stream')):
                # set final barline w/ mod iteration of value list
                bl = value[i%len(value)]
                #environLocal.printDebug(['enumerating measures', i, p, 'setting barline', bl])
                p._setFinalBarline(bl)
        else:
            # core routines for a single Stream
            if self.hasMeasures():
                self.getElementsByClass('Measure')[-1].rightBarline = value
            else:
                raise StreamException('cannot set a final barline on this Stream (%s) if no Measures are defined. Add Measures or call makeMeasures() first.' % self)

    finalBarline = property(_getFinalBarline, _setFinalBarline, doc='''
        Get or set the final barline of this Stream's Measures,
        if and only if there are Measures defined as elements in this Stream.
        This method will not create Measures if non exist.
        Setting a final barline to a Stream that does not have
        Measure will raise an exception.

        This property also works on Scores that contain one or more Parts.
        In that case a list of barlines can be used to set the final barline.

        >>> s = corpus.parse('bwv66.6')
        >>> s.finalBarline = 'none'
        >>> s.finalBarline
        [<music21.bar.Barline style=none>, 
         <music21.bar.Barline style=none>, 
         <music21.bar.Barline style=none>, 
         <music21.bar.Barline style=none>]
        ''')


    def _getVoices(self):
        return self.getElementsByClass('Voice')

    voices = property(_getVoices,
        doc='''
        Return all :class:`~music21.stream.Voices` objects
        in a :class:`~music21.stream.Stream` or Stream subclass.


        >>> s = stream.Stream()
        >>> s.insert(0, stream.Voice())
        >>> s.insert(0, stream.Voice())
        >>> len(s.voices)
        2
        ''')

    def _getSpanners(self):
        return self.getElementsByClass('Spanner')

    spanners = property(_getSpanners,
        doc='''
        Return all :class:`~music21.spanner.Spanner` objects
        (things such as Slurs, long trills, or anything that
        connects many objects)
        into a :class:`~music21.stream.Stream` or Stream subclass.

        >>> s = stream.Stream()
        >>> s.insert(0, spanner.Slur())
        >>> s.insert(0, spanner.Slur())
        >>> len(s.spanners)
        2
        ''')

    #---------------------------------------------------------------------------
    # handling transposition values and status
    def _getAtSoundingPitch(self):
        return self._atSoundingPitch

    def _setAtSoundingPitch(self, value):
        if value in [True, False, 'unknown']:
            self._atSoundingPitch = value
        else:
            raise StreamException('not a valid at sounding pitch value: %s' %
                                value)

    atSoundingPitch = property(_getAtSoundingPitch, _setAtSoundingPitch, doc='''
        Get or set the atSoundingPitch status, that is whether the
        score is at concert pitch or may have transposing instruments
        that will not sound as notated.

        Valid values are True, False, and 'unknown'.

        Note that setting "atSoundingPitch" does not actually transpose the notes. See
        `toSoundingPitch()` for that information.

        >>> s = stream.Stream()
        >>> s.atSoundingPitch = True
        >>> s.atSoundingPitch = False
        >>> s.atSoundingPitch = 'unknown'
        >>> s.atSoundingPitch
        'unknown'
        >>> s.atSoundingPitch = 'junk'
        Traceback (most recent call last):
        StreamException: not a valid at sounding pitch value: junk
        ''')


    def _transposeByInstrument(self, reverse=False, inPlace=True,
        transposeKeySignature=True):
        '''
        If reverse is False, the transposition will happen in the direction
        opposite of what is specified by the Instrument. for instance,
        for changing a concert score to a transposed score or for
        extracting parts.

        TODO: Fill out -- expose publically? inPlace should be False
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # this will change the working Stream; not sure if a problem
        boundaries = returnObj.extendDurationAndGetBoundaries('Instrument',
                        inPlace=True)

#         returnObj.extendDuration('Instrument', inPlace=True)
#         insts = returnObj.getElementsByClass('Instrument')
#
#         boundaries = {}
#         if len(insts) == 0:
#             raise StreamException('no Instruments defined in this Stream')
#         else:
#             for i in insts:
#                 start = i.getOffsetBySite(returnObj)
#                 end = start + i.duration.quarterLength
#                 boundaries[(start, end)] = i

        # store class filter list for transposition
        if transposeKeySignature:
            classFilterList = ['Note', 'Chord', 'KeySignature']
        else:
            classFilterList = ['Note', 'Chord']

        for k in boundaries:
            i = boundaries[k]
            if i.transposition is None:
                continue
            start, end = k
            focus = returnObj.getElementsByOffset(start, end,
                includeEndBoundary=False, mustFinishInSpan=False,
                mustBeginInSpan=True)
            trans = i.transposition
            if reverse:
                trans = trans.reverse()
            focus.transpose(trans, inPlace=True,
                            classFilterList=classFilterList)
            #print(k, i.transposition)
        return returnObj

    def toSoundingPitch(self, inPlace=False):
        '''
        If not at sounding pitch, transpose all Pitch
        elements to sounding pitch. The atSoundingPitch property
        is used to determine if transposition is necessary.

        v2.0.10 changes -- inPlace is False
        
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Stream'):
                # call on each part
                p.toSoundingPitch(inPlace=True)
            return returnObj

        if returnObj.atSoundingPitch == 'unknown':
            raise StreamException('atSoundingPitch is unknown: cannot transpose')
        elif returnObj.atSoundingPitch == False:
            # transposition defined on instrument goes from written to sounding
            returnObj._transposeByInstrument(reverse=False, inPlace=True)
        elif returnObj.atSoundingPitch == True:
            pass
        return returnObj # the Stream or None

    def toWrittenPitch(self, inPlace=True):
        '''
        If not at written pitch, transpose all Pitch elements to
        written pitch. The atSoundingPitch property is used to
        determine if transposition is necessary.

        TODO: by default inPlace should be False
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Stream'):
                # call on each part
                p.toWrittenPitch(inPlace=True)
            return returnObj

        if self.atSoundingPitch == 'unknown':
            raise StreamException('atSoundingPitch is unknown: cannot transpose')
        elif self.atSoundingPitch == False:
            pass
        elif self.atSoundingPitch == True:
            # transposition defined on instrument goes from written to sounding
            # need to reverse to go to written
            returnObj._transposeByInstrument(reverse=True, inPlace=True)
        return returnObj

    #---------------------------------------------------------------------------
    def getTimeSignatures(self, 
                          searchContext=True, 
                          returnDefault=True,
                          sortByCreationTime=True):
        '''
        Collect all :class:`~music21.meter.TimeSignature` objects in this stream.
        If no TimeSignature objects are defined, get a default (4/4 or whatever
        is defined in the defaults.py file).

        >>> a = stream.Stream()
        >>> b = meter.TimeSignature('3/4')
        >>> a.insert(b)
        >>> a.repeatInsert(note.Note("C#"), list(range(10)))
        >>> c = a.getTimeSignatures()
        >>> len(c) == 1
        True
        '''
        # even if this is a Measure, the TimeSignatue in the Stream will be
        # found
        #post = self.getElementsByClass(meter.TimeSignature)
        post = self.getElementsByClass('TimeSignature')

        # search activeSite Streams through contexts
        if len(post) == 0 and searchContext:
            # returns a single value
            post = self.cloneEmpty(derivationMethod='getTimeSignatures')

            # sort by time to search the most recent objects
            obj = self.getContextByClass('TimeSignature', sortByCreationTime=sortByCreationTime)
            #obj = self.previous('TimeSignature')
            #environLocal.printDebug(['getTimeSignatures(): searching contexts: results', obj])
            if obj is not None:
                post.append(obj)

        # get a default and/or place default at zero if nothing at zero
        if returnDefault:
            if len(post) == 0 or post[0].offset > 0:
                ts = meter.TimeSignature('%s/%s' % (defaults.meterNumerator,
                                   defaults.meterDenominatorBeatType))
                post.insert(0, ts)
        #environLocal.printDebug(['getTimeSignatures(): final result:', post[0]])
        return post


    def getInstruments(self, searchActiveSite=True, returnDefault=True):
        '''
        Search this stream or activeSite streams for
        :class:`~music21.instrument.Instrument` objects, otherwise
        return a default Instrument


        >>> s = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.insert(instrument.Violin())
        >>> m1p1 = stream.Measure()
        >>> m1p1.append(note.Note('g'))
        >>> p1.append(m1p1)

        >>> p2 = stream.Part()
        >>> p2.insert(instrument.Viola())
        >>> m1p2 = stream.Measure()
        >>> m1p2.append(note.Note('f#'))
        >>> p2.append(m1p2)

        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> p1.getInstrument(returnDefault=False).instrumentName
        'Violin'
        >>> p2.getInstrument(returnDefault=False).instrumentName
        'Viola'
        '''
        #environLocal.printDebug(['searching for instrument, called from:',
        #                        self])
        #TODO: Rename: getInstruments, and return a Stream of instruments
        #for cases when there is more than one instrument

        instObj = None
        post = self.iter.getElementsByClass('Instrument').stream()
        if post:
            #environLocal.printDebug(['found local instrument:', post[0]])
            instObj = post[0] # get first
        else:
            if searchActiveSite:
                #if isinstance(self.activeSite, Stream) and self.activeSite != self:
                if (self.activeSite is not None and self.activeSite.isStream and
                    self.activeSite is not self):
                    #environLocal.printDebug(['searching activeSite Stream',
                    #    self, self.activeSite])
                    instObj = self.activeSite.getInstrument(
                              searchActiveSite=searchActiveSite,
                              returnDefault=False)
                    if instObj is not None:
                        post.insert(0, instObj)

        # if still not defined, get default
        if returnDefault and instObj is None:
            instObj = instrument.Instrument()
            #instObj.partId = defaults.partId # give a default id
            instObj.partName = defaults.partName # give a default id
            post.insert(0, instObj)

        # returns a Stream
        return post


    def getInstrument(self, searchActiveSite=True, returnDefault=True):
        '''
        Return the first Instrument found in this Stream.
        '''
        post = self.getInstruments(searchActiveSite=searchActiveSite,
                                returnDefault=returnDefault)
        if len(post) > 0:
            return post[0]
        else:
            return None


    def bestClef(self, allowTreble8vb=False):
        '''
        TODO: Move to Clef
        
        Returns the clef that is the best fit for notes and chords found in this Stream.

        This does not automatically get a flat representation of the Stream.


        >>> import random
        >>> a = stream.Stream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(60,72))
        ...    a.insert(n)
        >>> b = a.bestClef()
        >>> b.line
        2
        >>> b.sign
        'G'

        >>> c = stream.Stream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(35,55))
        ...    c.insert(n)
        >>> d = c.bestClef()
        >>> d.line
        4
        >>> d.sign
        'F'
        '''
        #environLocal.printDebug(['calling bestClef()'])

        totalNotes = 0
        totalHeight = 0

        notes = self.getElementsByClass('GeneralNote')
        def findHeight(p):
            height = p.diatonicNoteNum
            if p.diatonicNoteNum > 33: # a4
                height += 3 # bonus
            elif p.diatonicNoteNum < 24: # Bass F or lower
                height += -3 # bonus
            return height

        for n in notes:
            if n.isRest:
                pass
            elif n.isNote:
                totalNotes  += 1
                totalHeight += findHeight(n.pitch)
            elif n.isChord:
                for p in n.pitches:
                    totalNotes += 1
                    totalHeight += findHeight(p)
        if totalNotes == 0:
            averageHeight = 29
        else:
            averageHeight = (totalHeight + 0.0) / totalNotes

        #environLocal.printDebug(['average height', averageHeight])
        if (allowTreble8vb is False):
            if averageHeight > 52: # value found with experimentation; revise
                return clef.Treble8vaClef()
            elif averageHeight > 28:    # c4
                return clef.TrebleClef()
            elif averageHeight > 10: # value found with experimentation; revise
                return clef.BassClef()
            else:
                return clef.Bass8vbClef()
        else:
            if averageHeight > 32:    # g4
                return clef.TrebleClef()
            elif averageHeight > 26:  # a3
                return clef.Treble8vbClef()
            else:
                return clef.BassClef()


    def getClefs(self, searchActiveSite=False, searchContext=True,
        returnDefault=True):
        '''
        Collect all :class:`~music21.clef.Clef` objects in
        this Stream in a new Stream. Optionally search the
        activeSite Stream and/or contexts.

        If no Clef objects are defined, get a default
        using :meth:`~music21.stream.Stream.bestClef`


        >>> a = stream.Stream()
        >>> b = clef.AltoClef()
        >>> a.insert(0, b)
        >>> a.repeatInsert(note.Note("C#"), list(range(10)))
        >>> c = a.getClefs()
        >>> len(c) == 1
        True
        '''
        # TODO: activeSite searching is not yet implemented
        # this may not be useful unless a stream is flat
        post = self.getElementsByClass('Clef')

        #environLocal.printDebug(['getClefs(); count of local', len(post), post])
        if len(post) == 0 and searchActiveSite and self.activeSite is not None:
            #environLocal.printDebug(['getClefs(): search activeSite'])
            post = self.activeSite.getElementsByClass('Clef')

        if len(post) == 0 and searchContext:
            # returns a single element match
            #post = self.__class__()
            obj = self.getContextByClass('Clef')
            if obj is not None:
                post.append(obj)

        # get a default and/or place default at zero if nothing at zero
        if returnDefault and (len(post) == 0 or post[0].offset > 0):
            #environLocal.printDebug(['getClefs(): using bestClef()'])
            post.insert(0, self.bestClef())
        return post

    def getKeySignatures(self, searchActiveSite=True, searchContext=True):
        '''
        Collect all :class:`~music21.key.KeySignature` objects in this
        Stream in a new Stream. Optionally search the activeSite
        stream and/or contexts.

        If no KeySignature objects are defined, returns an empty Stream


        >>> a = stream.Stream()
        >>> b = key.KeySignature(3)
        >>> a.insert(0, b)
        >>> a.repeatInsert(note.Note("C#"), list(range(10)))
        >>> c = a.getKeySignatures()
        >>> len(c) == 1
        True
        '''
        # TODO: activeSite searching is not yet implemented
        # this may not be useful unless a stream is flat
        post = self.getElementsByClass('KeySignature')
        if len(post) == 0 and searchContext:
            # returns a single value
            post = self.cloneEmpty(derivationMethod='getKeySignatures')
            obj = self.getContextByClass(key.KeySignature)
            if obj is not None:
                post.append(obj)

        # do nothing if empty  
        if len(post) == 0 or post[0].offset > 0:
            pass
        return post

    def invertDiatonic(self, inversionNote = note.Note('C4'), inPlace = True ):
        '''
        inverts a stream diatonically around the given note (by default, middle C)

        For pieces where the key signature
        does not change throughout the piece it is MUCH faster than
        for pieces where the key signature changes.

        Here in this test, we put Ciconia's Quod Jactatur (a single voice
        piece that should have a canon solution: see trecento.quodJactatur)
        into 3 flats (instead of its original 1 flat) in measure 1, but
        into 5 sharps in measure 2 and then invert around F4, creating
        a new piece.


        >>> qj = corpus.parse('ciconia/quod_jactatur').parts[0].measures(1,2)
        >>> qj.id = 'measureExcerpt'

        >>> qj.show('text')
        {0.0} <music21.instrument.Instrument P1: MusicXML Part: Grand Piano>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.clef.Treble8vbClef>
            {0.0} <music21.key.KeySignature of 1 flat, mode major>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C>
            {1.5} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note E>
            {0.5} <music21.note.Note D>
            {1.0} <music21.note.Note C>
            {1.5} <music21.note.Note D>
        >>> qjflat = qj.flat
        >>> k1 = qjflat.getElementsByClass(key.KeySignature)[0]
        >>> k3flats = key.KeySignature(-3)
        >>> qjflat.replace(k1, k3flats, allDerived=True)
        >>> qj.getElementsByClass(stream.Measure)[1].insert(0, key.KeySignature(5))
        >>> qj2 = qj.invertDiatonic(note.Note('F4'), inPlace=False)
        >>> qj2.show('text')
        {0.0} <music21.instrument.Instrument P1: MusicXML Part: Grand Piano>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.layout.SystemLayout>
            {0.0} <music21.clef.Treble8vbClef>
            {0.0} <music21.key.KeySignature of 3 flats>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note B->
            {1.5} <music21.note.Note A->
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.key.KeySignature of 5 sharps>
            {0.0} <music21.note.Note G#>
            {0.5} <music21.note.Note A#>
            {1.0} <music21.note.Note B>
            {1.5} <music21.note.Note A#>
        '''
        if inPlace == True:
            returnStream = self
        else:
            returnStream = copy.deepcopy(self)

        keySigSearch = returnStream.flat.getElementsByClass(key.KeySignature)

        quickSearch = True
        if len(keySigSearch) == 0:
            ourKey = key.Key('C')
        elif len(keySigSearch) == 1:
            ourKey = keySigSearch[0]
        else:
            quickSearch = False

        inversionDNN = inversionNote.diatonicNoteNum
        for n in returnStream.recurse(classFilter=('NotRest')):
            n.pitch.diatonicNoteNum = (2*inversionDNN) - n.pitch.diatonicNoteNum
            if quickSearch: # use previously found
                n.pitch.accidental = ourKey.accidentalByStep(n.pitch.step)
            else: # use context search
                ksActive = n.getContextByClass(key.KeySignature)
                n.pitch.accidental = ksActive.accidentalByStep(n.pitch.step)
            if n.pitch.accidental is not None:
                n.pitch.accidental.displayStatus = None

#            if n.step != 'B':
#                n.pitch.accidental = None
#            else:
#                n.pitch.accidental = pitch.Accidental('flat')
#                n.pitch.accidental.displayStatus = None
##            n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.pitch.step)
        return returnStream



    #--------------------------------------------------------------------------
    # offset manipulation

    def shiftElements(self, offset, startOffset=None, endOffset=None, classFilterList=None):
        '''
        Add the given offset value to every offset of
        the objects found in the Stream. Objects that are
        specifically placed at the end of the Stream via
        .storeAtEnd() (such as right barlines) are
        not affected.

        If startOffset is given then all elements before
        that offset will be shifted.  If endOffset is given
        then all elements at or after this offset will be
        shifted

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), list(range(0,10)))
        >>> a.shiftElements(30)
        >>> a.lowestOffset
        30.0
        >>> a.shiftElements(-10)
        >>> a.lowestOffset
        20.0

        Use shiftElements to move elements after a change in
        duration:

        >>> st2 = stream.Stream()
        >>> st2.insert(0, note.Note('D4', type='whole'))
        >>> st2.repeatInsert(note.Note('C4'), list(range(4, 8)))
        >>> st2.show('text')
        {0.0} <music21.note.Note D>
        {4.0} <music21.note.Note C>
        {5.0} <music21.note.Note C>
        {6.0} <music21.note.Note C>
        {7.0} <music21.note.Note C>

        Now make the first note a dotted whole note and shift the rest by two quarters...

        >>> firstNote = st2[0]
        >>> firstNoteOldQL = firstNote.quarterLength
        >>> firstNote.duration.dots = 1
        >>> firstNoteNewQL = firstNote.quarterLength
        >>> shiftAmount = firstNoteNewQL - firstNoteOldQL
        >>> shiftAmount
        2.0

        >>> st2.shiftElements(shiftAmount, startOffset=4.0)
        >>> st2.show('text')
        {0.0} <music21.note.Note D>
        {6.0} <music21.note.Note C>
        {7.0} <music21.note.Note C>
        {8.0} <music21.note.Note C>
        {9.0} <music21.note.Note C>
        '''
        # only want _elements, do not want _endElements
        for e in self._elements:

            if startOffset is not None and self.elementOffset(e) < startOffset:
                continue
            if endOffset is not None and self.elementOffset(e) >= endOffset:
                continue

            match = False
            if classFilterList is not None:
                for className in classFilterList:
                    # this may not match wrapped objects
                    if isinstance(e, className):
                        match = True
                        break
            else:
                match = True
            if match:
                self.setElementOffset(e, self.elementOffset(e) + offset)

        self.elementsChanged()

    def transferOffsetToElements(self):
        '''
        Transfer the offset of this stream to all
        internal elements; then set
        the offset of this stream to zero.

        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), list(range(0,10)))
        >>> a.offset = 30
        >>> a.transferOffsetToElements()
        >>> a.lowestOffset
        30.0
        >>> a.offset
        0.0
        >>> a.offset = 20
        >>> a.transferOffsetToElements()
        >>> a.lowestOffset
        50.0
        '''
        self.shiftElements(self.offset)
        self.offset = 0.0
        self.elementsChanged()


    #--------------------------------------------------------------------------
    # utilities for creating large numbers of elements

    def repeatAppend(self, item, numberOfTimes):
        '''
        Given an object and a number, run append that many times on
        a deepcopy of the object.
        numberOfTimes should of course be a positive integer.

        >>> a = stream.Stream()
        >>> n = note.Note('D--')
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> a.show('text')
        {0.0} <music21.note.Note D-->
        {4.0} <music21.note.Note D-->
        {8.0} <music21.note.Note D-->
        {12.0} <music21.note.Note D-->
        ...
        {36.0} <music21.note.Note D-->

        >>> a.duration.quarterLength
        40.0
        >>> a[9].offset
        36.0
        '''
        try:
            unused = item.isStream
            element = item
        #if not isinstance(item, music21.Music21Object):
        except AttributeError:
            #element = music21.ElementWrapper(item)
            raise StreamException('to put a non Music21Object in a stream, ' + 
                                  'create a music21.ElementWrapper for the item')
        # if not an element, embed
#         if not isinstance(item, music21.Music21Object):
#             element = music21.ElementWrapper(item)
#         else:
#             element = item

        for unused_i in range(0, numberOfTimes):
            self.append(copy.deepcopy(element))

    def repeatInsert(self, item, offsets):
        '''
        Given an object, create a deep copy of each object at
        each positions specified by
        the offset list:

        >>> a = stream.Stream()
        >>> n = note.Note('G-')
        >>> n.quarterLength = 1

        >>> a.repeatInsert(n, [0, 2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11, 12])
        >>> len(a)
        13
        >>> a[10].offset
        10.0
        '''
        if not common.isIterable(offsets):
            raise StreamException('must provide an iterable of offsets, not %s' % offsets)

        try:
            unused = item.isStream
            element = item
        #if not isinstance(item, music21.Music21Object):
        except AttributeError:
            # if not an element, embed
            #element = music21.ElementWrapper(item)
            raise StreamException('to put a non Music21Object in a stream, ' +
                                  'create a music21.ElementWrapper for the item')
#         if not isinstance(item, music21.Music21Object):
#             # if not an element, embed
#             element = music21.ElementWrapper(item)
#         else:
#             element = item

        for offset in offsets:
            elementCopy = copy.deepcopy(element)
            self._insertCore(offset, elementCopy)
        self.elementsChanged()


    def extractContext(self, searchElement, before=4.0, after=4.0,
                       maxBefore=None, maxAfter=None, forceOutputClass=None):
        '''
        Extracts elements around the given element within (before)
        quarter notes and (after) quarter notes (default 4), and
        returns a new Stream.

        >>> qn = note.Note(type='quarter')
        >>> qtrStream = stream.Stream()
        >>> qtrStream.repeatInsert(qn, [0, 1, 2, 3, 4, 5])
        >>> hn = note.Note(type='half')
        >>> hn.name = "B-"
        >>> qtrStream.append(hn)
        >>> qtrStream.repeatInsert(qn, [8, 9, 10, 11])
        >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
        >>> hnStream.show('text')
        {5.0} <music21.note.Note C>
        {6.0} <music21.note.Note B->
        {8.0} <music21.note.Note C>

        OMIT_FROM_DOCS
        TODO: maxBefore -- maximum number of elements to return before; etc.
        TODO: use .template to get new Stream

        NOTE: RENAME: this probably should be renamed, as we use Context in a special way.
        Perhaps better is extractNeighbors?

        '''
        if forceOutputClass is None:
            display = self.__class__()
        else:
            display = forceOutputClass() # is this ever used? prevents using .cloneEmpty('extractContext')
        display.derivation.origin = self
        display.derivation.method = 'extractContext'

        found = None
        foundOffset = 0
        foundEnd = 0
        elements = self.elements
        for i in range(len(elements)):
            b = elements[i]
            if b.id is not None or searchElement.id is not None:
                if b.id == searchElement.id:
                    found = i
                    foundOffset = self.elementOffset(elements[i])
                    foundEnd = foundOffset + elements[i].duration.quarterLength
            else:
                if b is searchElement:
                    found = i
                    foundOffset = self.elementOffset(elements[i])
                    foundEnd = foundOffset + elements[i].duration.quarterLength
        if found is None:
            raise StreamException("Could not find the element in the stream")

        # handle _elements and _endElements independently
        for e in self._elements:
            o = self.elementOffset(e)
            if (o >= foundOffset - before and o < foundEnd + after):
                display._insertCore(o, e)

        for e in self._endElements:
            o = self.elementOffset(e)
            if (o >= foundOffset - before and o < foundEnd + after):
                #display.storeAtEnd(e)
                display._storeAtEndCore(e)
        display.elementsChanged()
        return display


    #---------------------------------------------------------------------------
    # transformations of self that return a new Stream

    def _uniqueOffsetsAndEndTimes(self, offsetsOnly=False,
        endTimesOnly=False):
        '''
        Get a list of all offsets and endtimes
        of notes and rests in this stream.

        Helper method for makeChords and Chordify
        run on .flat.notesAndRests


        >>> s = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.insert(4, note.Note("C#"))
        >>> p1.insert(5.3, note.Rest())
        >>> p2 = stream.Part()
        >>> p2.insert(2.12, note.Note('D-', type='half'))
        >>> p2.insert(5.5, note.Rest())
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        
        We will get a mix of float and fractions.Fraction() objects
        
        >>> [str(o) for o in s.flat._uniqueOffsetsAndEndTimes()]
        ['53/25', '4.0', '103/25', '5.0', '53/10', '5.5', '63/10', '6.5']

        Limit what is returned:

        >>> [str(o) for o in s.flat._uniqueOffsetsAndEndTimes(offsetsOnly=True)]
        ['53/25', '4.0', '53/10', '5.5']
        >>> [str(o) for o in s.flat._uniqueOffsetsAndEndTimes(endTimesOnly=True)]
        ['103/25', '5.0', '63/10', '6.5']

        And this is useless...  :-)

        >>> s.flat._uniqueOffsetsAndEndTimes(offsetsOnly=True, endTimesOnly=True)
        []

        '''
        uniqueOffsets = []
        for e in self.elements:
            o = self.elementOffset(e)
            if endTimesOnly is not True and o not in uniqueOffsets:
                uniqueOffsets.append(o)
            endTime = opFrac(o + e.duration.quarterLength)
            if offsetsOnly is not True and endTime not in uniqueOffsets:
                uniqueOffsets.append(endTime)
        #uniqueOffsets = sorted(uniqueOffsets)
        # must sort do to potential overlaps
        uniqueOffsets.sort() # might be faster in-place
        return uniqueOffsets

    def makeChords(self, 
                   minimumWindowSize=.125, 
                   includePostWindow=True,
                   removeRedundantPitches=True, 
                   useExactOffsets=False,
                   gatherArticulations=True, 
                   gatherExpressions=True, 
                   inPlace=False,
                   transferGroupsToPitches=False, 
                   makeRests=True):
        '''
        Gathers simultaneously sounding :class:`~music21.note.Note` objects
        into :class:`~music21.chord.Chord` objects, each of which
        contains all the pitches sounding together.

        If useExactOffsets is True (default=False), then do an exact
        makeChords using the offsets in the piece.
        If this parameter is set, then minimumWindowSize is ignored.

        This first example puts a part with three quarter notes (C4, D4, E4)
        together with a part consisting of a half note (C#5) and a
        quarter note (E#5) to make two Chords, the first containing the
        three :class:`~music21.pitch.Pitch` objects sounding at the
        beginning, the second consisting of the two Pitches sounding
        on offset 2.0 (beat 3):



        >>> p1 = stream.Part()
        >>> p1.append([note.Note('C4', type='quarter'), 
        ...            note.Note('D4', type='quarter'), 
        ...            note.Note('E4', type='quarter'), 
        ...            note.Note('B2', type='quarter')])
        >>> p2 = stream.Part()
        >>> p2.append([note.Note('C#5', type='half'), 
        ...            note.Note('E#5', type='quarter'), 
        ...            chord.Chord(["E4","G5","C#7"])])
        >>> sc1 = stream.Score()
        >>> sc1.insert(0, p1)
        >>> sc1.insert(0, p2)
        >>> scChords = sc1.flat.makeChords()
        >>> scChords.show('text')
        {0.0} <music21.chord.Chord C4 C#5 D4>
        {2.0} <music21.chord.Chord E4 E#5>
        {3.0} <music21.chord.Chord B2 E4 G5 C#7>

        The gathering of elements, starting from offset 0.0, uses
        the `minimumWindowSize`, in quarter lengths, to collect
        all Notes that start between 0.0 and the minimum window
        size (this permits overlaps within a minimum tolerance).

        After collection, the maximum duration of collected elements
        is found; this duration is then used to set the new
        starting offset. A possible gap then results between the end
        of the window and offset specified by the maximum duration;
        these additional notes are gathered in a second pass if
        `includePostWindow` is True.

        The new start offset is shifted to the larger of either
        the minimum window or the maximum duration found in the
        collected group. The process is repeated until all offsets
        are covered.

        Each collection of Notes is formed into a Chord. The Chord
        is given the longest duration of all constituents, and is
        inserted at the start offset of the window from which it
        was gathered.

        Chords can gather both articulations and expressions from found Notes
        using `gatherArticulations` and `gatherExpressions`.

        If `transferGroupsToPitches` is True, and group defined on the source
        elements Groups object will be transfered to the Pitch
        objects conatained in the resulting Chord.

        The resulting Stream, if not in-place, can also gather
        additional objects by placing class names in the `collect` list.
        By default, TimeSignature and KeySignature objects are collected.     
        '''
        #environLocal.printDebug(['makeChords():', 
        #              'transferGroupsToPitches', transferGroupsToPitches])

        if not inPlace: # make a copy
            # since we do not return Scores, this probably should always be
            # a Stream
            #returnObj = Stream()
            #returnObj = self.__class__() # for output
            returnObj = copy.deepcopy(self)
            returnObj.derivation.origin = self
            returnObj.derivation.method = 'makeChords'
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass('Measure'):
                # offset values are not relative to measure; need to
                # shift by each measure's offset
                m.makeChords(
                    minimumWindowSize=minimumWindowSize,
                    includePostWindow=includePostWindow,
                    removeRedundantPitches=removeRedundantPitches,
                    gatherArticulations=gatherArticulations,
                    gatherExpressions=gatherExpressions,
                    transferGroupsToPitches=transferGroupsToPitches,
                    inPlace=True, 
                    makeRests=makeRests
                    )
            return returnObj # exit

        if returnObj.hasPartLikeStreams():
            # must get Streams, not Parts here
            for p in returnObj.getElementsByClass('Stream'):
                p.makeChords(
                    minimumWindowSize=minimumWindowSize,
                    includePostWindow=includePostWindow,
                    removeRedundantPitches=removeRedundantPitches,
                    gatherArticulations=gatherArticulations,
                    gatherExpressions=gatherExpressions,
                    transferGroupsToPitches=transferGroupsToPitches,
                    inPlace=True, 
                    makeRests=makeRests
                    )
            return returnObj # exit

        # TODO: gather lyrics as an option
        # define classes that are gathered; assume they have pitches
        # matchClasses = ['Note', 'Chord', 'Rest']
        matchClasses = ['Note', 'Chord']
        o = 0.0 # start at zero
        oTerminate = returnObj.highestOffset
        removedPitches = []

        # get temporary boundaries for making rests
        preHighestTime = returnObj.highestTime
        preLowestOffset = returnObj.lowestOffset
        #environLocal.printDebug(['got preLowest, preHighest', preLowestOffset, preHighestTime])
        if useExactOffsets is False:
            while True:
                # get all notes within the start and the minwindow size
                oStart = o
                oEnd = oStart + minimumWindowSize
                subNotes = returnObj.iter.getElementsByOffset(
                                    oStart, 
                                    oEnd,
                                    includeEndBoundary=False, 
                                    mustFinishInSpan=False, 
                                    mustBeginInSpan=True
                        ).getElementsByClass(matchClasses).stream() # get once for speed
                #environLocal.printDebug(['subNotes', subNotes])
                qlMax = None
                # get the max duration found from within the window
                if len(subNotes) > 0:
                    # get largest duration, use for duration of Chord, next span
                    qlMax = max([n.quarterLength for n in subNotes])

                # if the max duration found in the window is greater than the min
                # window size, it is possible that there are notes that will not
                # be gathered; those starting at the end of this window but before
                # the max found duration (as that will become the start of the next
                # window
                # so: if ql > min window, gather notes between
                # oStart + minimumWindowSize and oStart + qlMax
                if (includePostWindow and qlMax is not None
                    and qlMax > minimumWindowSize):
                    subAdd = returnObj.iter.getElementsByOffset(
                                            oStart + minimumWindowSize,
                                            oStart + qlMax,
                                            includeEndBoundary=False, 
                                            mustFinishInSpan=False, 
                                            mustBeginInSpan=True
                                    ).getElementsByClass(matchClasses).stream()
                    # concatenate any additional notes found
                    subNotes += subAdd

                # make subNotes into a chord
                if subNotes:
                    #environLocal.printDebug(['creating chord from subNotes', subNotes, 'inPlace', inPlace])
                    c = chord.Chord()
                    c.duration.quarterLength = qlMax
                    # these are references, not copies, for now
                    tempPitches = []
                    for n in subNotes:
                        if n.isChord:
                            pSub = n.pitches
                        else:
                            pSub = [n.pitch]
                        for p in pSub:
                            if transferGroupsToPitches:
                                for g in n.groups:
                                    p.groups.append(g)
                            tempPitches.append(p)
                    c.pitches = tempPitches
                    if gatherArticulations:
                        for n in subNotes:
                            c.articulations += n.articulations
                    if gatherExpressions:
                        for n in subNotes:
                            c.expressions += n.expressions
                    # always remove all the previous elements
                    for n in subNotes:
                        returnObj.remove(n)
                    # remove all rests found in source
                    for r in list(returnObj.iter.getElementsByClass('Rest')):
                        returnObj.remove(r)
                    if removeRedundantPitches:
                        removedPitches = c.removeRedundantPitches(inPlace=True)
                        
                        if transferGroupsToPitches:
                            for rem_p in removedPitches:
                                for cn in c:
                                    if cn.pitch.nameWithOctave == rem_p.nameWithOctave:
                                        #print(cn.pitch, rem_p)
                                        #print(cn.pitch.groups, rem_p.groups)
                                        cn.pitch.groups.extend(rem_p.groups)
                    # insert chord at start location
                    returnObj._insertCore(o, c)
                #environLocal.printDebug(['len of returnObj', len(returnObj)])
                # shift offset to qlMax or minimumWindowSize
                if qlMax is not None and qlMax >= minimumWindowSize:
                    # update start offset to what was old boundary
                    # note: this assumes that the start of the longest duration
                    # was at oStart; it could have been between oStart and oEnd
                    o += qlMax
                else:
                    o += minimumWindowSize
                # end While loop conditions
                if o > oTerminate:
                    break
        else: # useExactOffsets is True:
            onAndOffOffsets = self.flat.notesAndRests._uniqueOffsetsAndEndTimes()
            #environLocal.printDebug(['makeChords: useExactOffsets=True; onAndOffOffsets:', onAndOffOffsets])

            for i in range(len(onAndOffOffsets) - 1):
                # get all notes within the start and the minwindow size
                oStart = onAndOffOffsets[i]
                oEnd = onAndOffOffsets[i+1]
                subNotes = returnObj.iter.getElementsByOffset(
                                oStart, 
                                oEnd,
                                includeEndBoundary=False, 
                                mustFinishInSpan=False, 
                                mustBeginInSpan=True
                            ).getElementsByClass(matchClasses).stream()
                #environLocal.printDebug(['subNotes', subNotes])
                #subNotes.show('t')

                # make subNotes into a chord
                if subNotes:
                    #environLocal.printDebug(['creating chord from subNotes', subNotes, 'inPlace', inPlace])
                    c = chord.Chord()
                    c.duration.quarterLength = oEnd - oStart
                    # these are references, not copies, for now
                    tempComponents = []
                    for n in subNotes:
                        if n.isChord:  # TODO: this code should be the same as before: combine.
                            cSub = n._notes
                        else:
                            cSub = [n]

                        if transferGroupsToPitches:
                            if n.groups:
                                for comp in cSub:
                                    for g in n.groups:
                                        comp.pitch.groups.append(g)
#                            for g in comp.groups:
#                                comp.pitch.groups.append(g)
                        for comp in cSub:
                            tempComponents.append(comp)
                    c.pitches = [comp.pitch for comp in tempComponents]
                    for comp in tempComponents:
                        if comp.tie is not None:
                            c.setTie(comp.tie.type, comp.pitch)

                    if gatherArticulations:
                        for n in subNotes:
                            c.articulations += n.articulations
                    if gatherExpressions:
                        for n in subNotes:
                            c.expressions += n.expressions
                    # always remove all the previous elements
                    for n in subNotes:
                        returnObj.remove(n)
                    # remove all rests found in source
                    for r in list(returnObj.iter.getElementsByClass('Rest')):
                        returnObj.remove(r)

                    if removeRedundantPitches:
                        removedPitches = c.removeRedundantPitches(inPlace=True)
                        if transferGroupsToPitches:
                            for rem_p in removedPitches:
                                for cn in c:
                                    if cn.pitch.nameWithOctave == rem_p.nameWithOctave:
                                        cn.pitch.groups.extend(rem_p.groups)

                    
                    # insert chord at start location
                    returnObj._insertCore(oStart, c)

        # makeRests to fill any gaps produced by stripping
        #environLocal.printDebug(['pre makeRests show()'])
        if makeRests:
            returnObj.makeRests(
                refStreamOrTimeRange=(preLowestOffset, preHighestTime),
                fillGaps=True, inPlace=True)
        returnObj.elementsChanged()
        return returnObj


    def chordify(self, 
                 addTies=True, 
                 displayTiedAccidentals=False,
                 addPartIdAsGroup=False, 
                 removeRedundantPitches=True,
                 toSoundingPitch=True):
        '''
        Create a chordal reduction of polyphonic music, where each
        change to a new pitch results in a new chord. If a Score or
        Part of Measures is provided, a Stream of Measures will be
        returned. If a flat Stream of notes, or a Score of such
        Streams is provided, no Measures will be returned.

        If using chordify with chord symbols, ensure that the chord symbols
        have durations (by default the duration of a chord symbol object is 0, unlike
        a chord object). If harmony objects are not provided a duration, they
        will not be included in the chordified output pitches but may appear as chord symbol
        in notation on the score. To realize the chord symbol durations on a score, call
        :meth:`music21.harmony.realizeChordSymbolDurations` and pass in the score.

        This functionlaity works by splitting all Durations in
        all parts, or if multi-part by all unique offsets. All
        simultaneous durations are then gathered into single chords.

        If `addPartIdAsGroup` is True, all elements found in the
        Stream will have their source Part id added to the
        element's pitches' Group.  These groups names are useful
        for partially "de-chordifying" the output.  If the element chordifies to
        a :class:`~music21.chord.Chord` object, then the group will be found in each
        :class:`~music21.pitch.Pitch` element's .groups in Chord.pitches.  If the
        element chordifies to a single :class:`~music21.note.Note` then .pitch.groups
        will hold the group name.

        The `addTies` parameter currently does not work for pitches in Chords.

        If `toSoundingPitch` is True, all parts that define one or
        more transpositions will be transposed to sounding pitch before chordification.
        True by default.

        >>> s = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.id = 'part1'
        >>> p1.insert(4, note.Note("C#4"))
        >>> p1.insert(5.3, note.Rest())
        >>> p2 = stream.Part()
        >>> p2.id = 'part2'
        >>> p2.insert(2.12, note.Note('D-4', type='half'))
        >>> p2.insert(5.5, note.Rest())
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> s.show('text', addEndTimes=True)
        {0.0 - 6.3} <music21.stream.Part part1>
            {4.0 - 5.0} <music21.note.Note C#>
            {5.3 - 6.3} <music21.note.Rest rest>
        {0.0 - 6.5} <music21.stream.Part part2>
            {2.12 - 4.12} <music21.note.Note D->
            {5.5 - 6.5} <music21.note.Rest rest>

        >>> cc = s.chordify()
        >>> cc[3]
        <music21.chord.Chord C#4>
        >>> cc[3].duration.quarterLength
        Fraction(22, 25)

        >>> cc.show('text', addEndTimes=True)
        {0.0 - 2.12} <music21.note.Rest rest>
        {2.12 - 4.0} <music21.chord.Chord D-4>
        {4.0 - 4.12} <music21.chord.Chord C#4 D-4>
        {4.12 - 5.0} <music21.chord.Chord C#4>
        {5.0 - 6.5} <music21.note.Rest rest>

        Here's how addPartIdAsGroup works:

        >>> cc2 = s.chordify(addPartIdAsGroup=True)
        >>> csharpDflatChord = cc2[2]
        >>> for p in csharpDflatChord.pitches:
        ...     (str(p), p.groups)
        ('C#4', ['part1'])
        ('D-4', ['part2'])

        >>> s = stream.Stream()
        >>> p1 = stream.Part()
        >>> p1.insert(0, harmony.ChordSymbol('Cm', quarterLength = 4.0))
        >>> p1.insert(2, note.Note('C'))
        >>> p1.insert(4, harmony.ChordSymbol('D', quarterLength = 4.0))
        >>> p1.insert(7, note.Note('A'))
        >>> s.insert(0,p1)
        >>> s.chordify().show('text')
        {0.0} <music21.chord.Chord C3 E-3 G3>
        {2.0} <music21.chord.Chord C C3 E-3 G3>
        {3.0} <music21.chord.Chord C3 E-3 G3>
        {4.0} <music21.chord.Chord D3 F#3 A3>
        {7.0} <music21.chord.Chord A D3 F#3 A3>

        Note that :class:`~music21.harmony.ChordSymbol` objects can also be chordified:

        >>> s = stream.Stream()
        >>> p2 = stream.Part()
        >>> p1 = stream.Part()
        >>> p2.insert(0, harmony.ChordSymbol('Cm', quarterLength = 4.0))
        >>> p1.insert(2, note.Note('C'))
        >>> p2.insert(4, harmony.ChordSymbol('D', quarterLength = 4.0))
        >>> p1.insert(7, note.Note('A'))
        >>> s.insert(0,p1)
        >>> s.insert(0,p2)
        >>> s.chordify().show('text')
        {0.0} <music21.chord.Chord C3 E-3 G3>
        {2.0} <music21.chord.Chord C C3 E-3 G3>
        {3.0} <music21.chord.Chord C3 E-3 G3>
        {4.0} <music21.chord.Chord D3 F#3 A3>
        {7.0} <music21.chord.Chord A D3 F#3 A3>

        If addPartIdAsGroup is True, and there are redundant pitches,
        ensure that the merged pitch has both groups

        >>> s = stream.Score()
        >>> p0 = stream.Part(id='p0')
        >>> p0.insert(0, note.Note("C4"))
        >>> p1 = stream.Part(id='p1')
        >>> p1.insert(0, note.Note("C4"))
        >>> s.insert(0, p0)
        >>> s.insert(0, p1)
        >>> s1 = s.chordify(addPartIdAsGroup=True)
        >>> c = s1.recurse().notes[0]
        >>> c
        <music21.chord.Chord C4>
        >>> c.pitches[0].groups
        ['p0', 'p1']


        OMIT_FROM_DOCS

        Test that chordifying works on a single stream.

        >>> f2 = stream.Score()
        >>> f2.insert(0, metadata.Metadata())
        >>> f2.insert(0, note.Note('C4'))
        >>> f2.insert(0, note.Note('D#4'))
        >>> c = f2.chordify()
        >>> cn = c.notes
        >>> cn[0].pitches
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch D#4>)
        '''
        # TODO: need to handle flat Streams contained in a Stream
        # TODO: need to handle voices
        #       even if those component Stream do not have Measures

        # TODO: make chordify have an option where the Pitches are not deepcopied from the original, but
        #       are the same.

        # for makeChords, below        
        transferGroupsToPitches = False
        if addPartIdAsGroup:
            transferGroupsToPitches = True

        returnObj = copy.deepcopy(self)
        returnObj.isSorted = False # this makes all the difference in the world for some reason...
        if returnObj.hasPartLikeStreams():
            allParts = returnObj.getElementsByClass('Stream')
        else: # simulate a list of Streams
            allParts = [returnObj]

        if toSoundingPitch:
            #environLocal.printDebug(['at sounding pitch',     allParts[0].atSoundingPitch])
            if allParts[0].atSoundingPitch == False: # if false
                returnObj.toSoundingPitch(inPlace=True)

        mStream = allParts[0].getElementsByClass('Measure')
        mCount = len(mStream)
        hasMeasures = True
        if mCount == 0:
            hasMeasures = False
            mCount = 1 # treat as a single measure
        else:
            partsMeasureCache = []
            for p in allParts:
                partsMeasureCache.append(p.getElementsByClass('Measure'))

        for i in range(mCount): # may be 1
            # first, collect all unique offsets for each measure
            uniqueOffsets = []
            for pNum, p in enumerate(allParts):
                if hasMeasures is True: # has measures
                    m = partsMeasureCache[pNum][i]
                else:
                    m = p # treat the entire part as one measure
                mFlatNotes = m.flat.notesAndRests
                theseUniques = mFlatNotes._uniqueOffsetsAndEndTimes()
                for t in theseUniques:
                    if t not in uniqueOffsets:
                        uniqueOffsets.append(t)
            #environLocal.printDebug(['chordify: uniqueOffsets for all parts, m', uniqueOffsets, i])
            uniqueOffsets = sorted(uniqueOffsets)
            for pNum, p in enumerate(allParts):
                # get one measure at a time
                if hasMeasures is True:
                    m = partsMeasureCache[pNum][i]
                else:
                    m = p # treat the entire part as one measure
                # working with a copy, in place can be true
                m.sliceAtOffsets(offsetList=uniqueOffsets, addTies=addTies,
                    inPlace=True,
                    displayTiedAccidentals=displayTiedAccidentals)
                # tag all sliced notes if requested
                if addPartIdAsGroup:
                    for e in m: # add to all elements
                        # some ids may not be strings; must convert
                        e.groups.append(str(p.id))

        # make chords from flat version of sliced parts
        # do in place as already a copy has been made
        post = returnObj.flat.makeChords(includePostWindow=True,
                                         useExactOffsets=True,
                                         removeRedundantPitches=removeRedundantPitches,
                                         gatherArticulations=True, 
                                         gatherExpressions=True, 
                                         inPlace=True,
                                         transferGroupsToPitches=transferGroupsToPitches)

        # re-populate a measure stream with the new chords
        # get a measure stream from the top voice
        # assume we can manipulate this these measures as already have deepcopy
        # the Part may not have had any Measures;
        if mStream:
            for i, m in enumerate(list(mStream.iter.getElementsByClass('Measure'))):
                # get highest time before removal
                mQl = m.duration.quarterLength
                m.removeByClass('GeneralNote')
                # remove any Streams (aka Voices) found in the Measure
                m.removeByClass('Stream')
                # get offset in original measure
                mOffsetStart = m.getOffsetBySite(allParts[0])
                mOffsetEnd = mOffsetStart + mQl
                # not sure if this properly manages padding

                # place all notes in their new location if offsets match
                # TODO: this iterates over all notes at each iteration; can be faster
                for e in post.iter.notesAndRests:
                    # these are flat offset values
                    o = e.getOffsetBySite(post)
                    #environLocal.printDebug(['iterating elements', o, e])
                    if o >= mOffsetStart and o < mOffsetEnd:
                        # get offset in relation to inside of Measure
                        localOffset = o - mOffsetStart
                        #environLocal.printDebug(['inserting element', e, 'at', o, 'in', m, 'localOffset', localOffset])
                        m.insert(localOffset, e)
                # call for each measure
                m.elementsChanged()
            # call this post now
            post = mStream
        else: # place in a single flat Stream
            post.elementsChanged()

        if hasattr(returnObj, 'metadata') and returnObj.metadata is not None and returnObj.hasPartLikeStreams() is True:
            post.insert(0, returnObj.metadata)
        return post

        #post.elementsChanged()
        #return mStream
        #return post


    def splitByClass(self, classObj, fx):
        '''
        Given a stream, get all objects of type classObj and divide them into
        two new streams depending on the results of fx.
        Fx should be a lambda or other function on elements.
        All elements where fx returns True go in the first stream.
        All other elements are put in the second stream.

        If classObj is None then all elements are returned.  ClassObj
        can also be a list of classes.

        In this example, we will create 50 notes from midi note 30 (two
        octaves and a tritone below middle C) to midi note 80 (an octave
        and a minor sixth above middle C) and add them to a Stream.
        We then create a lambda function to split between those notes
        below middle C (midi note 60) and those above
        (google "lambda functions in Python" for more information on
        what these powerful tools are).



        >>> stream1 = stream.Stream()
        >>> for x in range(30,81):
        ...     n = note.Note()
        ...     n.pitch.midi = x
        ...     stream1.append(n)
        >>> fx = lambda n: n.pitch.midi < 60
        >>> b, c = stream1.splitByClass(note.Note, fx)

        Stream b now contains all the notes below middle C,
        that is, 30 notes, beginning with F#1 and ending with B3
        while Stream c has the 21 notes from C4 to A-5:

        >>> len(b)
        30
        >>> (b[0].nameWithOctave, b[-1].nameWithOctave)
        ('F#1', 'B3')
        >>> len(c)
        21
        >>> (c[0].nameWithOctave, c[-1].nameWithOctave)
        ('C4', 'G#5')
        '''
        a = self.cloneEmpty(derivationMethod='splitByClass')
        b = self.cloneEmpty(derivationMethod='splitByClass')
        if classObj is not None:
            found = self.getElementsByClass(classObj)
        else:
            found = self
        for e in found._elements:
            if fx(e):
                a._insertCore(e.getOffsetBySite(found), e) # provide an offset here
            else:
                b._insertCore(e.getOffsetBySite(found), e)
        for e in found._endElements:
            if fx(e):
                #a.storeAtEnd(e)
                a._storeAtEndCore(e)
            else:
                #b.storeAtEnd(e)
                b._storeAtEndCore(e)
        a.elementsChanged()
        b.elementsChanged()
        return a, b


    def _getOffsetMap(self, srcObj=None):
        '''
        Needed for makeMeasures and a few other places

        The Stream source of elements is self by default,
        unless a `srcObj` is provided.


        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 8)
        >>> for om in s._getOffsetMap():
        ...     om
        OffsetMap(element=<music21.note.Note C>, offset=0.0, endTime=1.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=1.0, endTime=2.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=2.0, endTime=3.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=3.0, endTime=4.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=4.0, endTime=5.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=5.0, endTime=6.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=6.0, endTime=7.0, voiceIndex=None)
        OffsetMap(element=<music21.note.Note C>, offset=7.0, endTime=8.0, voiceIndex=None)
        '''
        if srcObj is None:
            srcObj = self
        # assume that flat/sorted options will be set before procesing
        offsetMap = [] # list of start, start+dur, element
        if srcObj.hasVoices():
            groups = []
            for i, v in enumerate(srcObj.voices):
                groups.append((v.flat, i))
        else: # create a single collection
            groups = [(srcObj, None)]
        #environLocal.printDebug(['_getOffsetMap', groups])
        for group, voiceIndex in groups:
            for e in group._elements:
                # do not include barlines
                if isinstance(e, bar.Barline):
                    continue
                #if hasattr(e, 'duration') and e.duration is not None:
                if e.duration is not None:
                    dur = e.duration.quarterLength
                else:
                    dur = 0
                # NOTE: rounding here may cause secondary problems
                offset = e.getOffsetBySite(group) #round(e.getOffsetBySite(group), 8)
                endTime = opFrac(offset + dur)
                # NOTE: used to make a copy.copy of elements here;
                # this is not necssary b/c making deepcopy of entire Stream
                thisOffsetMap = _OffsetMap(e, offset, endTime, voiceIndex)
                #environLocal.printDebug(['_getOffsetMap: thisOffsetMap', thisOffsetMap])
                offsetMap.append(thisOffsetMap)
                #offsetMap.append((offset, offset + dur, e, voiceIndex))
                #offsetMap.append([offset, offset + dur, copy.copy(e)])
        return offsetMap

    offsetMap = property(_getOffsetMap, doc='''
        Returns a list where each element is a dictionary
        consisting of the 'offset' of each element in a stream, the
        'endTime' (that is, the offset plus the duration) and the
        'element' itself.  Also contains a 'voiceIndex' entry which
        contains the voice number of the element, or None if there
        are no voices.

        >>> n1 = note.Note(type='quarter')
        >>> c1 = clef.AltoClef()
        >>> n2 = note.Note(type='half')
        >>> s1 = stream.Stream()
        >>> s1.append([n1, c1, n2])
        >>> om = s1.offsetMap
        >>> om[2].offset
        1.0
        >>> om[2].endTime
        3.0
        >>> om[2].element is n2
        True
        >>> om[2].voiceIndex
    ''')

    def makeMeasures(
        self,
        meterStream=None,
        refStreamOrTimeRange=None,
        searchContext=False,
        innerBarline=None,
        finalBarline='final',
        bestClef=False,
        inPlace=False,
        ):
        '''
        Return a new stream (or if inPlace=True change in place) this
        Stream so that it has internal measures.

        For more details, see :py:func:`~music21.stream.makeNotation.makeMeasures`.
        '''
        return makeNotation.makeMeasures(
            self,
            meterStream=meterStream,
            refStreamOrTimeRange=refStreamOrTimeRange,
            searchContext=searchContext,
            innerBarline=innerBarline,
            finalBarline=finalBarline,
            bestClef=bestClef,
            inPlace=inPlace,
            )

    def makeRests(
        self,
        refStreamOrTimeRange=None,
        fillGaps=False,
        timeRangeFromBarDuration=False,
        inPlace=True,
        ):
        '''
        Calls :py:func:`~music21.stream.makeNotation.makeRests`.
        '''
        return makeNotation.makeRests(
            self,
            refStreamOrTimeRange=refStreamOrTimeRange,
            fillGaps=fillGaps,
            timeRangeFromBarDuration=timeRangeFromBarDuration,
            inPlace=inPlace,
            )

    def makeTies(self,
        meterStream=None,
        inPlace=True,
        displayTiedAccidentals=False,
        ):
        '''
        Calls :py:func:`~music21.stream.makeNotation.makeTies`.
        '''
        return makeNotation.makeTies(
            self,
            meterStream=meterStream,
            inPlace=inPlace,
            displayTiedAccidentals=displayTiedAccidentals,
            )

    def makeBeams(self, inPlace=False):
        '''
        Return a new Stream, or modify the Stream in place, with beams applied to all
        notes.

        See :py:func:`~music21.stream.makeNotation.makeBeams`.
        '''
        return makeNotation.makeBeams(
            self,
            inPlace=inPlace,
            )

    @common.deprecated("September 2015", "Feb. 2016", "use stream.streamStatus.StreamStatus.haveBeamsBeenMade instead")
    def haveBeamsBeenMade(self):
        # could be called: hasAccidentalDisplayStatusSet
        '''
        If any Note in this Stream has .beams defined, it as
        assumed that Beams have not been set and/or makeBeams
        has not been run. If any Beams exist, this method
        returns True, regardless of if makeBeams has actually been run.
        
        DEPRECATED: Use :meth:`~music21.stream.streamStatus.StreamStatus.haveBeamsBeenMade`
        instead.
        
        Remove in Feb 2016
        '''
        return self.streamStatus.haveBeamsBeenMade()

    # @common.deprecated
    def makeTupletBrackets(self, inPlace=False):
        '''
        Calls :py:func:`~music21.stream.makeNotation.makeTupletBrackets`.
        
        Deprecated sep 2015; rem march 2016; call makeNotation.makeTupletBrackets directly.
        '''
        return makeNotation.makeTupletBrackets(
            self,
            inPlace=inPlace,
            )

    def makeAccidentals(self, 
                        pitchPast=None, 
                        pitchPastMeasure=None,
                        useKeySignature=True, 
                        alteredPitches=None,
                        searchKeySignatureByContext=False, 
                        cautionaryPitchClass=True,
                        cautionaryAll=False, 
                        inPlace=True, 
                        overrideStatus=False,
                        cautionaryNotImmediateRepeat=True, 
                        lastNoteWasTied=False):
        '''
        A method to set and provide accidentals given various conditions and contexts.

        `pitchPast` is a list of pitches preceeding this pitch in this measure.

        `pitchPastMeasure` is a list of pitches preceeding this pitch but in a previous measure.


        If `useKeySignature` is True, a :class:`~music21.key.KeySignature` will be searched
        for in this Stream or this Stream's defined contexts. An alternative KeySignature
        can be supplied with this object and used for temporary pitch processing.

        If `alteredPitches` is a list of modified pitches (Pitches with Accidentals) that
        can be directly supplied to Accidental processing. These are the same values obtained
        from a :class:`music21.key.KeySignature` object using the
        :attr:`~music21.key.KeySignature.alteredPitches` property.

        If `cautionaryPitchClass` is True, comparisons to past accidentals are made regardless
        of register. That is, if a past sharp is found two octaves above a present natural,
        a natural sign is still displayed.

        If `cautionaryAll` is True, all accidentals are shown.

        If `overrideStatus` is True, this method will ignore any current `displayStatus` stetting
        found on the Accidental. By default this does not happen. If `displayStatus` is set to
        None, the Accidental's `displayStatus` is set.

        If `cautionaryNotImmediateRepeat` is True, cautionary accidentals will be displayed for
        an altered pitch even if that pitch had already been displayed as altered.

        If `lastNoteWasTied` is True, assume that the first note of the stream was tied
        to the previous note.  TODO: make more robust for tied chords with only some pitches tied...

        The :meth:`~music21.pitch.Pitch.updateAccidentalDisplay` method is used to determine if
        an accidental is necessary.

        This will assume that the complete Stream is the context of evaluation. For smaller context
        ranges, call this on Measure objects.

        If `inPlace` is True, this is done in-place; if `inPlace` is False, this returns a modified deep copy.

        TODO: inPlace default should become False
        TODOL if inPlace is True return None
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # need to reset these lists unless values explicitly provided
        if pitchPast is None:
            pitchPast = []
        if pitchPastMeasure is None:
            pitchPastMeasure = []
        # see if there is any key signatures to add to altered pitches
        if alteredPitches is None:
            alteredPitches = []
        addAlteredPitches = []
        if isinstance(useKeySignature, key.KeySignature):
            addAlteredPitches = useKeySignature.alteredPitches
        elif useKeySignature is True: # get from defined contexts
            # will search local, then activeSite
            ksStream = self.getKeySignatures(
                searchContext=searchKeySignatureByContext)
            if len(ksStream) > 0:
                # assume we want the first found; in some cases it is possible
                # that this may not be true
                addAlteredPitches = ksStream[0].alteredPitches
        alteredPitches += addAlteredPitches
        #environLocal.printDebug(['processing makeAccidentals() with alteredPitches:', alteredPitches])

        # need to move through notes in order
        # NOTE: this may or may have sub-streams that are not being examined
        noteStream = returnObj.notesAndRests

        #environLocal.printDebug(['alteredPitches', alteredPitches])
        #environLocal.printDebug(['pitchPast', pitchPast])

        # get chords, notes, and rests
#         for i in range(len(noteStream)):
#             e = noteStream[i]
        for e in noteStream:
            if isinstance(e, note.Note):
                e.pitch.updateAccidentalDisplay(pitchPast=pitchPast,
                    pitchPastMeasure=pitchPastMeasure,
                    alteredPitches=alteredPitches,
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll,
                    overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                    lastNoteWasTied=lastNoteWasTied)
                pitchPast.append(e.pitch)
                if e.tie is not None and e.tie.type != 'stop':
                    lastNoteWasTied = True
                else:
                    lastNoteWasTied = False
            elif isinstance(e, chord.Chord):
                pGroup = e.pitches
                # add all chord elements to past first
                # when reading a chord, this will apply an accidental
                # if pitches in the chord suggest an accidental
                for p in pGroup:
                    p.updateAccidentalDisplay(pitchPast=pitchPast,
                        pitchPastMeasure=pitchPastMeasure,
                        alteredPitches=alteredPitches,
                        cautionaryPitchClass=cautionaryPitchClass, cautionaryAll=cautionaryAll,
                        overrideStatus=overrideStatus,
                      cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                        lastNoteWasTied=lastNoteWasTied)
                if e.tie is not None and e.tie.type != 'stop':
                    lastNoteWasTied = True
                else:
                    lastNoteWasTied = False
                pitchPast += pGroup
            else:
                lastNoteWasTied = False

        return returnObj


    def haveAccidentalsBeenMade(self):
        # could be called: hasAccidentalDisplayStatusSet
        '''
        If Accidentals.displayStatus is None for all
        contained pitches, it as assumed that accidentals
        have not been set for display and/or makeAccidentals
        has not been run. If any Accidental has displayStatus
        other than None, this method returns True, regardless
        of if makeAccidentals has actually been run.
        '''
        return self.streamStatus.haveAccidentalsBeenMade()

    def makeNotation(self, 
                     meterStream=None, 
                     refStreamOrTimeRange=None,
                     inPlace=False, 
                     bestClef=False, 
                     **subroutineKeywords):
        '''
        This method calls a sequence of Stream methods on this Stream to prepare
        notation, including creating voices for overlapped regions, Measures
        if necessary, creating ties, beams, and accidentals.

        If `inPlace` is True, this is done in-place;
        if `inPlace` is False, this returns a modified deep copy.

        makeAccidentalsKeywords can be a dict specifying additional
        parameters to send to makeAccidentals


        >>> s = stream.Stream()
        >>> n = note.Note('g')
        >>> n.quarterLength = 1.5
        >>> s.repeatAppend(n, 10)
        >>> sMeasures = s.makeNotation()
        >>> len(sMeasures.getElementsByClass('Measure'))
        4
        >>> sMeasures.getElementsByClass('Measure')[-1].rightBarline.style
        'final'
        '''
        # determine what is the object to work on first
        if inPlace:
            returnStream = self
        else:
            returnStream = copy.deepcopy(self)

#         if 'finalBarline' in subroutineKeywords:
#             lastBarlineType = subroutineKeywords['finalBarline']
#         else:
#             lastBarlineType = 'final'

        # only use inPlace arg on first usage
        if not self.hasMeasures():
            # only try to make voices if no Measures are defined
            returnStream.makeVoices(inPlace=True, fillGaps=True)
            # if this is not inPlace, it will return a newStream; if
            # inPlace, this returns None
            # use inPlace=True, as already established above
            returnStream.makeMeasures(
                meterStream=meterStream,
                refStreamOrTimeRange=refStreamOrTimeRange,
                inPlace=True, 
                bestClef=bestClef)

        measureStream = returnStream.getElementsByClass('Measure')
        #environLocal.printDebug(['Stream.makeNotation(): post makeMeasures, length', len(returnStream)])

        # for now, calling makeAccidentals once per measures
        # pitches from last measure are passed
        # this needs to be called before makeTies
        # note that this functionality is also placed in Part
        if not measureStream.haveAccidentalsBeenMade():
            ksLast = None
            srkCopy = subroutineKeywords.copy()
            if 'meterStream' in srkCopy:
                del(srkCopy['meterStream'])
            if 'refStreamOrTimeRange' in srkCopy:
                del(srkCopy['refStreamOrTimeRange'])

            for i in range(len(measureStream)):
                m = measureStream[i]
                if m.keySignature is not None:
                    ksLast = m.keySignature
                if i > 0 and m.keySignature is None:
                    if (measureStream[i-1] and 
                            hasattr(measureStream[i-1][-1], "tie") and 
                            measureStream[i-1][-1].tie is not None and 
                            measureStream[i-1][-1].tie.type != 'stop'):
                        lastNoteWasTied = True
                    else:
                        lastNoteWasTied = False
                        
                    m.makeAccidentals(
                        pitchPastMeasure=measureStream[i-1].pitches,
                        useKeySignature=ksLast, 
                        searchKeySignatureByContext=False,
                        lastNoteWasTied=lastNoteWasTied, 
                        **srkCopy)
                else:
                    m.makeAccidentals(
                        useKeySignature=ksLast,
                        searchKeySignatureByContext=False, 
                        **srkCopy)
        #environLocal.printDebug(['makeNotation(): meterStream:', meterStream, meterStream[0]])
        measureStream.makeTies(meterStream, inPlace=True)
        #measureStream.makeBeams(inPlace=True)
        try:
            measureStream.makeBeams(inPlace=True)
        except (StreamException, meter.MeterException):
            # this is a result of makeMeaures not getting everything
            # note to measure allocation right
            #environLocal.printDebug(['skipping makeBeams exception', StreamException])
            pass

        # note: this needs to be after makeBeams, as placing this before
        # makeBeams was causing the duration's tuplet to loose its type setting
        # check for tuplet brackets one measure at a time
        # this means that they will never extend beyond one measure
        for m in measureStream:
            if m.streamStatus.haveTupletBracketsBeenMade() is False:
                makeNotation.makeTupletBrackets(m, inPlace=True)

        if len(measureStream) == 0:
            raise StreamException('no measures found in stream with %s elements' % (self.__len__()))
        #environLocal.printDebug(['Stream.makeNotation(): created measures:', len(measureStream)])

        return returnStream

    def realizeOrnaments(self):
        '''
        Calls :py:func:`~music21.stream.makeNotation.realizeOrnaments`.
        
        DEPRECATED Sep 2015; will be removed by March 2016
        '''
        warnings.warn("realizeOrnaments; use stream.makeNotation.realizeOrnaments() instead", 
                      StreamDeprecationWarning)
        return makeNotation.realizeOrnaments(self)

    def extendDuration(self, objName, inPlace=True):
        '''
        Given a Stream and an object class name, go through the Stream
        and find each instance of the desired object. The time between
        adjacent objects is then assigned to the duration of each object.
        The last duration of the last object is assigned to extend to the
        end of the Stream.

        If `inPlace` is True, this is done in-place; if `inPlace` is
        False, this returns a modified deep copy.

        >>> stream1 = stream.Stream()
        >>> n = note.Note(type='quarter')
        >>> n.duration.quarterLength
        1.0
        >>> stream1.repeatInsert(n, [0, 10, 20, 30, 40])

        >>> dyn = dynamics.Dynamic('ff')
        >>> stream1.insert(15, dyn)
        >>> stream1[-1].offset # offset of last element
        40.0
        >>> stream1.duration.quarterLength # total duration
        41.0
        >>> len(stream1)
        6

        >>> stream2 = stream1.flat.extendDuration(note.GeneralNote)
        >>> len(stream2)
        6
        >>> stream2[0].duration.quarterLength
        10.0

        The Dynamic does not affect the second note:
        
        >>> stream2[1].offset
        10.0
        >>> stream2[1].duration.quarterLength
        10.0

        >>> stream2[-1].duration.quarterLength # or extend to end of stream
        1.0
        >>> stream2.duration.quarterLength
        41.0
        >>> stream2[-1].offset
        40.0



        TODO: extendDuration inPlace should be False by default
        TODO: if inPlace is True, return None
        '''

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        qLenTotal = returnObj.duration.quarterLength
        elements = []
        for element in returnObj.iter.getElementsByClass(objName):
#             if not hasattr(element, 'duration'):
#                 raise StreamException('can only process objects with duration attributes')
            if element.duration is None:
                element.duration = duration.Duration()
            elements.append(element)

        #print(elements[-1], qLenTotal, elements[-1].duration)
        # print(_MOD, elements)
        for i in range(len(elements)-1):
            #print(i, len(elements))
            span = self.elementOffset(elements[i+1]) - self.elementOffset(elements[i])
            elements[i].duration.quarterLength = span

        # handle last element
        #print(elements[-1], qLenTotal, elements[-1].duration)
        if len(elements) != 0:
            elements[-1].duration.quarterLength = (qLenTotal -
                        self.elementOffset(elements[-1]))
            #print(elements[-1], elements[-1].duration)
        return returnObj


    def extendDurationAndGetBoundaries(self, objName, inPlace=True):
        '''Extend the Duration of elements specified by objName; 
        then, collect a dictionary for every matched element of objName class, 
        where the matched element is the value and the key is the (start, end) offset value.

        >>> from pprint import pprint as pp
        >>> s = stream.Stream()
        >>> s.insert(3, dynamics.Dynamic('mf'))
        >>> s.insert(7, dynamics.Dynamic('f'))
        >>> s.insert(12, dynamics.Dynamic('ff'))
        >>> pp(s.extendDurationAndGetBoundaries('Dynamic'))
        {(3.0, 7.0): <music21.dynamics.Dynamic mf >,
         (7.0, 12.0): <music21.dynamics.Dynamic f >,
         (12.0, 12.0): <music21.dynamics.Dynamic ff >}        


        TODO: only allow inPlace = True or delete or something, can't return two different things
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self
        returnObj.extendDuration(objName, inPlace=True)
        # TODO: use iteration.
        elements = returnObj.getElementsByClass(objName)
        boundaries = {}
        if len(elements) == 0:
            raise StreamException('no elements of this class defined in this Stream')
        else:
            for e in elements:
                start = e.getOffsetBySite(returnObj)
                end = start + e.duration.quarterLength
                boundaries[(start, end)] = e
        return boundaries


    def stripTies(self, inPlace=False, matchByPitch=False,
         retainContainers=False):
        '''
        Find all notes that are tied; remove all tied notes,
        then make the first of the tied notes have a duration
        equal to that of all tied constituents. Lastly,
        remove the formerly-tied notes.

        This method can be used on Stream and Stream subclasses.
        When used on a Score, Parts and Measures are retained.

        If `retainContainers` is False (by default), this method only
        returns Note objects; Measures and other structures are stripped
        from the Stream. Set `retainContainers` to True to remove ties
        from a :class:`~music21.part.Part` Stream that contains
        :class:`~music21.stream.Measure` Streams, and get back a
        multi-Measure structure.

        Presently, this only works if tied notes are sequentual; ultimately
        this will need to look at .to and .from attributes (if they exist)

        In some cases (under makeMeasures()) a continuation note will not have a
        Tie object with a stop attribute set. In that case, we need to look
        for sequential notes with matching pitches. The `matchByPitch` option can
        be used to use this technique.

        Note that inPlace=True on a Stream with substream currently has buggy behavior.  Use inPlace=False for now.
        TODO: Fix this.

        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 6
        >>> a.append(n)
        >>> m = a.makeMeasures()
        >>> m.makeTies()
        >>> len(m.flat.notes)
        2

        >>> m = m.stripTies()
        >>> len(m.flat.notes)
        1
        '''
        #environLocal.printDebug(['calling stripTies'])
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasPartLikeStreams():
            for p in returnObj.iter.getElementsByClass('Part'):
                # already copied if necessary; edit in place
                # when handling a score, retain containers should be true
                p.stripTies(inPlace=True, matchByPitch=matchByPitch,
                            retainContainers=True)
            return returnObj # exit

        # assume this is sorted
        # need to just get .notesAndRests, as there may be other objects in the Measure
        # that come before the first Note, such as a SystemLayout object
        f = returnObj.flat
        notes = f.notesAndRests
        
        posConnected = [] # temporary storage for index of tied notes
        posDelete = [] # store deletions to be processed later

        for i in range(len(notes)):
            endMatch = None # can be True, False, or None
            n = notes[i]
            if i > 0: # get i and n for the previous value
                iLast = i-1
                nLast = notes[iLast]
            else:
                iLast = None
                nLast = None

            # see if we have a tie and it is started
            # a start typed tie may not be a true start tie
            if (hasattr(n, 'tie') and n.tie is not None and
                n.tie.type == 'start'):
                # find a true start, add to known connected positions
                if iLast is None or iLast not in posConnected:
                    posConnected = [i] # reset list with start
                # find a continuation: the last note was a tie
                # start and this note is a tie start (this may happen)
                elif iLast in posConnected:
                    posConnected.append(i)
                # a connection has been started or continued, so no endMatch
                endMatch = False

            elif (hasattr(n, 'tie') and n.tie is not None and
                n.tie.type == 'continue'):
                # a continue always implies a connection
                posConnected.append(i)
                endMatch = False

            # establish end condition
            if endMatch is None: # not yet set, not a start or continue
                # ties tell us when the are ended
                if (hasattr(n, 'tie') and n.tie is not None
                    and n.tie.type == 'stop'):
                    endMatch = True
                # if we cannot find a stop tie, see if last note was connected
                # and this and the last note are the same pitch; this assumes
                # that connected and same pitch value is tied; this is not
                # frequently the case
                elif matchByPitch:
                    # find out if the last index is in position connected
                    # if the pitches are the same for each note
                    if (nLast is not None and iLast in posConnected
                        and hasattr(nLast, "pitch") and hasattr(n, "pitch")
                        and nLast.pitch == n.pitch):
                        endMatch = True
                    # looking for two chords of equal size
                    elif (nLast is not None and not
                        self.isClassOrSubclass('Note') and iLast in posConnected
                        and hasattr(nLast, "pitches") and hasattr(n, "pitches")
                        and len(nLast.pitches) == len(n.pitches)):
                        allPitchesMatched = True
                        for pitchIndex in range(len(nLast.pitches)):
                            if nLast.pitches[pitchIndex] != n.pitches[pitchIndex]:
                                allPitchesMatched = False
                                break
                        if allPitchesMatched == True:
                            endMatch = True

            # process end condition
            if endMatch:
                posConnected.append(i) # add this last position
                if len(posConnected) < 2:
                    # an open tie, not connected to anything
                    # should be an error; presently, just skipping
                    #raise StreamException('cannot consolidate ties when only one tie is present', notes[posConnected[0]])
                    #environLocal.printDebug(['cannot consolidate ties when only one tie is present', notes[posConnected[0]]])
                    posConnected = []
                    continue

                # get sum of durations for all nots
                # do not include first; will add to later; do not delete
                durSum = 0
                for q in posConnected[1:]: # all but the first
                    durSum += notes[q].quarterLength
                    posDelete.append(q) # store for deleting later
                # dur sum should always be greater than zero
                if durSum == 0:
                    raise StreamException('aggregated ties have a zero duration sum')
                # change the duration of the first note to be self + sum
                # of all others
                qLen = notes[posConnected[0]].quarterLength
                notes[posConnected[0]].quarterLength = qLen + durSum

                # set tie to None on first note
                notes[posConnected[0]].tie = None
                posConnected = [] # resset to empty

        # all results have been processed
        # presently removing from notes, not resultObj, as index positions
        # in result object may not be the same
        posDelete.reverse() # start from highest and go down

        if retainContainers:
            for i in posDelete:
                #environLocal.printDebug(['removing note', notes[i]])
                # get the obj ref
                nTarget = notes[i]
                # go through each container and find the note to delete
                # note: this assumes the container is Measure
                # TODO: this is where we need a recursive container Generator out
                for sub in reversed(returnObj.getElementsByClass('Measure')):
                    try:
                        i = sub.index(nTarget)
                    except StreamException:
                        continue # pass if not in Stream
                    junk = sub.pop(i)
                    # get a new note
                    # we should not continue searching Measures
                    break
            returnObj.elementsChanged()
            return returnObj

        else:
            for i in posDelete:
                # removing the note from notes
                junk = notes.pop(i)
            notes.elementsChanged()
            return notes


    def extendTies(self, ignoreRests=False, pitchAttr='nameWithOctave'):
        '''
        Connect any adjacent pitch space values that are the
        same with a Tie. Adjacent pitches can be Chords, Notes, or Voices.

        If `ignoreRests` is True, rests that occur between events will not be
        considered in matching pitches.

        The `pitchAttr` determines the pitch attribute that is
        used for comparison. Any valid pitch attribute name can be used.
        '''
        def _getNextElements(srcStream, currentIndex, targetOffset,
                         ignoreRests=ignoreRests):
            # need to find next event that start at the appropriate offset
            if currentIndex == len(srcStream) - 1: # assume flat
                #environLocal.printDebug(['_getNextElements: nothing to process', currentIndex, len(srcStream.notes) ])
                return [] # nothing left
            # iterate over all possible elements
            if ignoreRests:
                # need to find the offset of the first thing that is not rest
                for j in range(currentIndex+1, len(srcStream._elements)):
                    e = srcStream._elements[j]
                    if 'NotRest' in e.classes:
                        # change target offset to this position
                        targetOffset = srcStream._elements[j].getOffsetBySite(
                                        srcStream)
                        break
            match = srcStream.getElementsByOffset(targetOffset)
            #filter matched elements
            post = []
            for m in match:
                if 'NotRest' in m.classes:
                    post.append(m)
            return post

        # take all flat elements; this will remove all voices; just use offset
        # position
        # do not need to worry about ._endElements
        srcFlat = self.flat.notes
        for i, e in enumerate(srcFlat._elements):
            pSrc = []
            if 'Note' in e.classes:
                pSrc = [e]
            elif 'Chord' in e.classes:
                pSrc = [n for n in e] # get components
            else:
                continue
            #environLocal.printDebug(['examining', i, e])
            connections = _getNextElements(srcFlat, i,
                e.getOffsetBySite(srcFlat) + e.duration.quarterLength)
            #environLocal.printDebug(['possible conections', connections])

            for p in pSrc:
                # for each p, see if there is match in the next position
                for m in connections:
                    # for each element, look for a pitch to match
                    mSrc = []
                    if 'Note' in m.classes:
                        mSrc = [m]
                    elif 'Chord' in m.classes:
                        mSrc = [n for n in m] # get components
                    # final note comparison
                    for q in mSrc:
                        if getattr(q.pitch, pitchAttr) == getattr(p.pitch,
                            pitchAttr):
                            # create a tie from p to q
                            if p.tie is None:
                                p.tie = tie.Tie('start')
                            elif p.tie.type is 'stop':
                                p.tie.type = 'continue'
                            # if dst tie exists, assume it connects
                            q.tie = tie.Tie('stop')
                            break # can only have one match from p to q

    #---------------------------------------------------------------------------

    def sort(self, force=False):
        '''
        Sort this Stream in place by offset, then priority, then
        standard class sort order (e.g., Clefs before KeySignatures before
        TimeSignatures).

        Note that Streams automatically sort themsevlves unless
        autoSort is set to False (as in the example below)

        If `force` is True, a sort will be attempted regardless of any other parameters.


        >>> n1 = note.Note('a')
        >>> n2 = note.Note('b')
        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.insert(100, n2)
        >>> s.insert(0, n1) # now a has a lower offset by higher index
        >>> [n.name for n in s]
        ['B', 'A']
        >>> s.sort()
        >>> [n.name for n in s]
        ['A', 'B']
        '''
        # trust if this is sorted: do not sort again
        # experimental
        if (not self.isSorted and self._mutable) or force:
            #environLocal.printDebug(['sorting _elements, _endElements'])
#             self._elements.sort(
#                 cmp=lambda x, y: cmp(
#                     self.elementOffset(x), self.elementOffset(y))
#                     or cmp(x.priority, y.priority)
#                     or cmp(x.classSortOrder, y.classSortOrder)
#                     or cmp(not x.isGrace, not y.isGrace) # sort graces first
#                     #or cmp(random.randint(1,30), random.randint(1,30))
#                 )
#             self._endElements.sort(
#                 cmp=lambda x, y: cmp(x.priority, y.priority) or
#                     cmp(x.classSortOrder, y.classSortOrder)
#                 )
            self._elements.sort(key=lambda x: x.sortTuple(self))
            self._endElements.sort(key=lambda x: x.sortTuple(self))

            # as sorting changes order, elements have changed;
            # need to clear cache, but flat status is the same
            self.elementsChanged(updateIsFlat=False, clearIsSorted=False)
            self.isSorted = True
            #environLocal.printDebug(['_elements', self._elements])

    def _getSorted(self):
        if 'sorted' not in self._cache or self._cache['sorted'] is None:
            shallowElements = copy.copy(self._elements) # already a copy
            shallowEndElements = copy.copy(self._endElements) # already a copy
            s = copy.copy(self)
            # assign directly to _elements, as we do not need to call
            # elementsChanged()
            s._elements = shallowElements
            s._endElements = shallowEndElements

            for e in shallowElements + shallowEndElements:
                s.setElementOffset(e, self.elementOffset(e))
                e.sites.add(s)
                # need to explicitly set activeSite
                e.activeSite = s
            # now just sort this stream in place; this will update the
            # isSorted attribute and sort only if not already sorted
            s.sort()
            self._cache['sorted'] = s
        return self._cache['sorted']

        # get a shallow copy of elements list
#         shallowElements = copy.copy(self._elements) # already a copy
#         shallowEndElements = copy.copy(self._endElements) # already a copy
#         newStream = copy.copy(self)
#         # assign directly to _elements, as we do not need to call
#         # elementsChanged()
#         newStream._elements = shallowElements
#         newStream._endElements = shallowEndElements
#
#         for e in shallowElements + shallowEndElements:
#             e.sites.add(newStream)
#             # need to explicitly set activeSite
#             e.activeSite = newStream
#         # now just sort this stream in place; this will update the
#         # isSorted attribute and sort only if not already sorted
#         newStream.sort()
#         return newStream

    sorted = property(_getSorted, doc='''
        Returns a new Stream where all the elements are sorted according to offset time, then
        priority, then classSortOrder (so that, for instance, a Clef at offset 0 appears before
        a Note at offset 0)

        if this Stream is not flat, then only the highest elements are sorted.  To sort all,
        run myStream.flat.sorted

        For instance, here is an unsorted Stream


        >>> s = stream.Stream()
        >>> s.autoSort = False # if true, sorting is automatic
        >>> s.insert(1, note.Note("D"))
        >>> s.insert(0, note.Note("C"))
        >>> s.show('text')
        {1.0} <music21.note.Note D>
        {0.0} <music21.note.Note C>


        But a sorted version of the Stream puts the C first:


        >>> s.sorted.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>


        While the original stream remains unsorted:


        >>> s.show('text')
        {1.0} <music21.note.Note D>
        {0.0} <music21.note.Note C>


        OMIT_FROM_DOCS
        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.repeatInsert(note.Note("C#"), [0, 2, 4])
        >>> s.repeatInsert(note.Note("D-"), [1, 3, 5])
        >>> s.isSorted
        False
        >>> g = ""
        >>> for myElement in s:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; '
        >>> y = s.sorted
        >>> y.isSorted
        True
        >>> g = ""
        >>> for myElement in y:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; '
        >>> farRight = note.Note("E")
        >>> farRight.priority = 5
        >>> farRight.offset = 2.0
        >>> y.insert(farRight)
        >>> g = ""
        >>> for myElement in y:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; '
        >>> z = y.sorted
        >>> g = ""
        >>> for myElement in z:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; '
        >>> z[2].name, z[3].name
        ('C#', 'E')

        ''')


    def _getFlatOrSemiFlat(self, retainContainers=False):
        '''
        A private method that implements the .flat or .semiFlat reduction types by using
        `retainContainers` = False to get .flat and retainContainers = True to get .semiFlat
        '''
        #environLocal.printDebug(['_getFlatOrSemiFlat(): self', self, 'self.activeSite', self.activeSite])

        # this copy will have a shared locations object
        # note that copy.copy() in some cases seems to not cause secondary
        # problems that self.__class__() does
        if retainContainers:
            method = 'semiFlat'
        else:
            method = 'flat'

        sNew = copy.copy(self)
        if sNew.id != id(sNew):
            sOldId = sNew.id
            if common.isNum(sOldId) and sOldId > defaults.minIdNumberToConsiderMemoryLocation:
                sOldId = hex(sOldId)
            sNew.id = str(sOldId) + "_" + method
        
        sNew._derivation = derivation.Derivation(sNew)
        sNew._derivation.origin = self
        sNew.derivation.method = method
        # storing .elements in here necessitates
        # create a new, independent cache instance in the flat representation
        sNew._cache = {} 
        sNew._offsetDict = {}
        sNew._elements = []
        sNew._endElements = []
        sNew.elementsChanged()

        for e in self._elements:
            #environLocal.printDebug(['_getFlatOrSemiFlat', 'processing e:', e])
            # check for stream instance instead

            # if this element is a Stream, recurse
            #if hasattr(e, "elements"):
            if e.isStream:
                #environLocal.printDebug(['_getFlatOrSemiFlat', '!!! processing substream:', e])

                recurseStreamOffset = self.elementOffset(e)

                if retainContainers is True: # semiFlat
                    #environLocal.printDebug(['_getFlatOrSemiFlat(), retaining containers, storing element:', e])

                    # this will change the activeSite of e to be sNew, previously
                    # this was the activeSite was the caller; thus, the activeSite here
                    # should not be set
                    #sNew.insert(recurseStreamOffset, e, setActiveSite=False)
                    sNew._insertCore(recurseStreamOffset, e,
                        setActiveSite=False)
                    # this may be a cached version;
                    recurseStream = e.semiFlat
                    #recurseStream = e._getFlatOrSemiFlat(retainContainers=True)
                else:
                    recurseStream = e.flat

                #environLocal.printDebug("recurseStreamOffset: " + str(e.id) + " " + str(recurseStreamOffset))
                # recurse Stream is the flat or semiFlat contents of a Stream
                # contained within the caller
                for eSub in recurseStream:
                    #environLocal.printDebug(['subElement', id(eSub), 'inserted in', sNew, 'id(sNew)', id(sNew)])
                    #oldOffset =
                    #sNew.insert(eSub.getOffsetBySite(recurseStream) +
                    #    recurseStreamOffset, eSub)
                    sNew._insertCore(eSub.getOffsetBySite(recurseStream) +
                        recurseStreamOffset, eSub)
            # if element not a Stream
            else:
                # insert into new stream at offset in old stream
                #self.elementOffset(sNew.insert(e), e)
                sNew._insertCore(self.elementOffset(e), e)

        # highest time elements should never be Streams
        for e in self._endElements:
            #sNew.storeAtEnd(e)
            sNew._storeAtEndCore(e)

        sNew.isFlat = True
        # here, we store the source stream from which this stream was derived
        return sNew


    def _getFlat(self):
        if 'flat' not in self._cache or self._cache['flat'] is None:
            self._cache['flat'] = self._getFlatOrSemiFlat(
                                  retainContainers=False)
        return self._cache['flat']

        # non cached approach
        #return self._getFlatOrSemiFlat(retainContainers=False)

    flat = property(_getFlat, doc=
        '''
        A very important read-only property that returns a new Stream
        that has all sub-containers "flattened" within it,
        that is, it returns a new Stream where no elements nest within
        other elements.

        Here is a simple example of the usefulness of .flat.  We
        will create a Score with two Parts in it, each with two Notes:

        >>> sc = stream.Score()
        >>> p1 = stream.Part()
        >>> p1.id = 'part1'
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> p1.append(n1)
        >>> p1.append(n2)

        >>> p2 = stream.Part()
        >>> p2.id = 'part2'
        >>> n3 = note.Note('E4')
        >>> n4 = note.Note('F4')
        >>> p2.append(n3)
        >>> p2.append(n4)

        >>> sc.insert(0, p1)
        >>> sc.insert(0, p2)

        When we look at sc, we will see only the two parts:

        >>> sc.elements
        (<music21.stream.Part part1>, <music21.stream.Part part2>)

        We can get at the notes by using the indices of the
        stream to get the parts and then looking at the .elements
        there:

        >>> sc[0].elements
        (<music21.note.Note C>, <music21.note.Note D>)

        >>> sc.getElementById('part2').elements
        (<music21.note.Note E>, <music21.note.Note F>)

        ...but if we want to get all the notes, the easiest way
        is via calling .flat on sc and looking at the elements
        there:

        >>> sc.flat.elements
        (<music21.note.Note C>, <music21.note.Note E>, <music21.note.Note D>, <music21.note.Note F>)

        Flattening a stream is a great way to get at all the notes in
        a larger piece.  For instance if we load a four-part
        Bach chorale into music21 from the integrated corpus, it
        will appear at first that there are no notes in the piece:

        >>> bwv66 = corpus.parse('bach/bwv66.6')
        >>> len(bwv66.notes)
        0

        This is because all the notes in the piece lie within :class:`music21.stream.Measure`
        objects and those measures lie within :class:`music21.stream.Part`
        objects.  It'd be a pain to navigate all the way through all those
        objects just to count notes.  Fortunately we can get a Stream of
        all the notes in the piece with .flat.notes and then use the
        length of that Stream to count notes:

        >>> bwv66flat = bwv66.flat
        >>> len(bwv66flat.notes)
        165

        If you look back to our simple example of four notes above,
        you can see that the E (the first note in part2) comes before the D
        (the second note of part1).  This is because the flat stream
        is automatically sorted like all streams are by default.  The
        next example shows how to change this behavior.

        >>> s = stream.Stream()
        >>> s.autoSort = False
        >>> s.repeatInsert(note.Note("C#"), [0, 2, 4])
        >>> s.repeatInsert(note.Note("D-"), [1, 3, 5])
        >>> s.isSorted
        False

        >>> g = ""
        >>> for myElement in s:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        ...

        >>> g
        '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; '

        >>> y = s.sorted
        >>> y.isSorted
        True

        >>> g = ""
        >>> for myElement in y:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        ...

        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; '

        >>> q = stream.Stream()
        >>> for i in range(5):
        ...     p = stream.Stream()
        ...     p.repeatInsert(base.Music21Object(), [0, 1, 2, 3, 4])
        ...     q.insert(i * 10, p)
        ...

        >>> len(q)
        5


        >>> qf = q.flat
        >>> len(qf)
        25
        >>> qf[24].offset
        44.0

        OMIT_FROM_DOCS

        >>> r = stream.Stream()
        >>> for j in range(5):
        ...   q = stream.Stream()
        ...   for i in range(5):
        ...      p = stream.Stream()
        ...      p.repeatInsert(base.Music21Object(), [0, 1, 2, 3, 4])
        ...      q.insert(i * 10, p)
        ...   r.insert(j * 100, q)

        >>> len(r)
        5

        >>> len(r.flat)
        125

        >>> r.flat[124].offset
        444.0
        ''')


    def _getSemiFlat(self):
        if 'semiFlat' not in self._cache or self._cache['semiFlat'] is None:
            #environLocal.printDebug(['using cached semiFlat', self])
            self._cache['semiFlat'] = self._getFlatOrSemiFlat(
                                    retainContainers=True)
        return self._cache['semiFlat']

        #return self._getFlatOrSemiFlat(retainContainers=True)


    semiFlat = property(_getSemiFlat, doc='''
        Returns a flat-like Stream representation.
        Stream sub-classed containers, such as Measure or Part,
        are retained in the output Stream, but positioned at their
        relative offset.


        >>> s = stream.Stream()

        >>> p1 = stream.Part()
        >>> p1.id = 'part1'
        >>> n1 = note.Note('C5')
        >>> p1.append(n1)

        >>> p2 = stream.Part()
        >>> p2.id = 'part2'
        >>> n2 = note.Note('D5')
        >>> p2.append(n2)

        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> sf = s.semiFlat
        >>> sf.elements
        (<music21.stream.Part part1>, <music21.stream.Part part2>, <music21.note.Note C>, <music21.note.Note D>)
        >>> sf[0]
        <music21.stream.Part part1>
        >>> sf[2]
        <music21.note.Note C>
        >>> sf[0][0]
        <music21.note.Note C>

        ''')

    def _yieldReverseUpwardsSearch(self, memo=None, streamsOnly=False,
                             skipDuplicates=True, classFilter=()):
        '''
        Yield all containers (Stream subclasses), including self, and going upward
        and outward.
        
        NOT CURRENTLY USED.

        Note: on first call, a new, fresh memo list must be provided; 
        otherwise, values are retained from one call to the next.
        
        >>> b = corpus.parse('bwv66.6')
        >>> nMid = b[2][4][2]
        >>> nMid
        <music21.note.Note G#>
        >>> nMidMeasure = b[2][4]
        >>> nMidMeasure
        <music21.stream.Measure 3 offset=9.0>
        >>> list(nMidMeasure._yieldReverseUpwardsSearch())
        [<music21.stream.Measure 3 offset=9.0>, 
         <music21.instrument.Instrument P2: Alto: Instrument 2>, 
         <music21.stream.Part Alto>, 
         <music21.metadata.Metadata object at 0x...>, 
         <music21.stream.Part Soprano>, 
         <music21.stream.Score ...>, 
         <music21.stream.Part Tenor>, 
         <music21.stream.Part Bass>, 
         <music21.layout.StaffGroup <music21.stream.Part Soprano><music21.stream.Part Alto><music21.stream.Part Tenor><music21.stream.Part Bass>>, 
         <music21.stream.Measure 0 offset=0.0>, 
         <music21.stream.Measure 1 offset=1.0>, 
         <music21.stream.Measure 2 offset=5.0>, 
         <music21.stream.Measure 4 offset=13.0>, 
         <music21.stream.Measure 5 offset=17.0>, 
         <music21.stream.Measure 6 offset=21.0>, 
         <music21.stream.Measure 7 offset=25.0>, 
         <music21.stream.Measure 8 offset=29.0>, 
         <music21.stream.Measure 9 offset=33.0>]
        '''
        # TODO: add support for filter list
        # TODO: add add end elements
        if memo is None:
            memo = []

        # must exclude spanner storage, as might be found
        if id(self) not in memo and 'SpannerStorage' not in self.classes:
            yield self
            #environLocal.printDebug(['memoing:', self, memo])
            if skipDuplicates:
                memo.append(id(self))

        # may need to make sure that activeSite is correctly assigned
        p = self.activeSite
        # if a activeSite exists, its always a stream!
        #if p is not None and hasattr(p, 'elements'):
        if p is not None and p.isStream and 'SpannerStorage' not in p.classes:
            # using indices so as to not to create an iterator and new locations/activeSites
            # here we access the private _elements, again: no iterator
            for i in range(len(p._elements)):
                # not using __getitem__, also to avoid new locations/activeSites
                e = p._elements[i]
                #environLocal.printDebug(['examining elements:', e])

                # not a Stream; may or may not have a activeSite;
                # its possible that it may have activeSite not identified elsewhere
                #if not hasattr(e, 'elements'):
                if not e.isStream:
                    if not streamsOnly:
                        if id(e) not in memo:
                            yield e
                            if skipDuplicates:
                                memo.append(id(e))
                # for each element in the activeSite that is a Stream,
                # look at the activeSites
                # if the activeSites are a Stream, recurse
                #elif (hasattr(e, 'elements') and e.activeSite is not None
                #    and hasattr(e.activeSite, 'elements')):

                elif (e.isStream and e.activeSite is not None and
                    e.activeSite.isStream and 'SpannerStorage' not in e.classes):
                    # this returns a generator, so need to iterate over it
                    # to get results
                    # e.activeSite will be yielded at top of recurse
                    for y in e.activeSite._yieldReverseUpwardsSearch(memo,
                            skipDuplicates=skipDuplicates,
                            streamsOnly=streamsOnly, classFilter=classFilter):
                        yield y
                    # here, we have found a container at the same level of
                    # the caller; since it is a Stream, we yield
                    # caller is contained in the activeSite; if e is self, skip
                    if id(e) != id(self):
                        if id(e) not in memo:
                            yield e
                            if skipDuplicates:
                                memo.append(id(e))

    def recurse(self, streamsOnly=False,
        restoreActiveSites=True, classFilter=(), skipSelf=False):
        '''
        NOTE: skipSelf is going to become True by default soon -- make sure that you
        are NOT relying on the default value.
        
        Returns an iterator that iterates over a list of Music21Objects 
        contained in the Stream, starting with self (unless skipSelf is True), 
        continuing with self's elements,
        and whenever finding a Stream subclass in self, 
        that Stream subclass's elements.

        Here's an example. Let's create a simple score.
        
        >>> s = stream.Score(id='mainScore')
        >>> p0 = stream.Part(id='part0')
        >>> p1 = stream.Part(id='part1')

        >>> m01 = stream.Measure(number=1)
        >>> m01.append(note.Note('C', type="whole"))
        >>> m02 = stream.Measure(number=2)
        >>> m02.append(note.Note('D', type="whole"))
        >>> m11 = stream.Measure(number=1)
        >>> m11.append(note.Note('E', type="whole"))
        >>> m12 = stream.Measure(number=2)
        >>> m12.append(note.Note('F', type="whole"))

        >>> p0.append([m01, m02])
        >>> p1.append([m11, m12])

        >>> s.insert(0, p0)
        >>> s.insert(0, p1)
        >>> s.show('text')
        {0.0} <music21.stream.Part part0>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note C>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note D>
        {0.0} <music21.stream.Part part1>
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note E>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note F>
                
        Now we could assign the `.recurse()` method to something, but that won't have much effect:
        
        >>> sRecurse = s.recurse()
        >>> sRecurse
        <music21.stream.iterator.RecursiveIterator for Score:mainScore @:0>
        
        So, that's not how we use `.recurse()`.  Instead use it in a for loop:
        
        >>> for el in s.recurse():
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.stream.Score mainScore>, 0.0, None)
        (<music21.stream.Part part0>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part0>)
        (<music21.note.Note C>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part0>)
        (<music21.note.Note D>, 0.0, <music21.stream.Measure 2 offset=4.0>)
        (<music21.stream.Part part1>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part1>)
        (<music21.note.Note E>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part1>)
        (<music21.note.Note F>, 0.0, <music21.stream.Measure 2 offset=4.0>)        
        
        Notice that like calling `.show('text')`, the offsets are relative to their containers.
        
        Compare the difference between putting `classFilter='Note'` and `.flat.notes`:
        
        >>> for el in s.recurse(classFilter='Note'):
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.note.Note C>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.note.Note D>, 0.0, <music21.stream.Measure 2 offset=4.0>)
        (<music21.note.Note E>, 0.0, <music21.stream.Measure 1 offset=0.0>)
        (<music21.note.Note F>, 0.0, <music21.stream.Measure 2 offset=4.0>)

        >>> for el in s.flat.notes:
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.note.Note C>, 0.0, <music21.stream.Stream mainScore_flat>)
        (<music21.note.Note E>, 0.0, <music21.stream.Stream mainScore_flat>)
        (<music21.note.Note D>, 4.0, <music21.stream.Stream mainScore_flat>)
        (<music21.note.Note F>, 4.0, <music21.stream.Stream mainScore_flat>)

        If you don't need correct offsets or activeSites, set `restoreActiveSites` to `False`.
        Then the last offset/activeSite will be used.  It's a bit of a speedup, but leads to some
        bad code, so use it only in highly optimized situations.
        
        We'll also test using multiple classes here... the Stream given is the same as the
        s.flat.notes stream.
        
        >>> for el in s.recurse(classFilter=('Note','Rest'), restoreActiveSites=False):
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.note.Note C>, 0.0, <music21.stream.Stream mainScore_flat>)
        (<music21.note.Note D>, 4.0, <music21.stream.Stream mainScore_flat>)
        (<music21.note.Note E>, 0.0, <music21.stream.Stream mainScore_flat>)
        (<music21.note.Note F>, 4.0, <music21.stream.Stream mainScore_flat>)        

        So, this is pretty unreliable so don't use it unless the tiny speedup is worth it.
        
        The other two attributes are pretty self-explanatory: `streamsOnly` will put only Streams
        in, while `skipSelf` will ignore the initial stream from recursion.  If the inclusion or
        exclusion of `self` is important to you, put it in explicitly, because the default
        will likely change in the future.
        
        >>> for el in s.recurse(skipSelf=True, streamsOnly=True):
        ...     tup = (el, el.offset, el.activeSite)
        ...     print(tup)
        (<music21.stream.Part part0>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part0>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part0>)
        (<music21.stream.Part part1>, 0.0, <music21.stream.Score mainScore>)
        (<music21.stream.Measure 1 offset=0.0>, 0.0, <music21.stream.Part part1>)
        (<music21.stream.Measure 2 offset=4.0>, 4.0, <music21.stream.Part part1>)

        .. warning::
        
            Remember that like all iterators, it is dangerous to alter
            the components of the Stream being iterated over during iteration.
            if you need to edit while recusing, list(s.recurse()) is safer.
        
        #TODO: change skipSelf by January 2016.
        '''
        includeSelf = not skipSelf
        ri = iterator.RecursiveIterator(self, streamsOnly=streamsOnly,
                                        restoreActiveSites=restoreActiveSites,
                                        includeSelf=includeSelf
                                        )
        if classFilter != ():
            ri.addFilter(filter.ClassFilter(classFilter))
        return ri        

    def restoreActiveSites(self):
        '''
        Restore all active sites for all elements from this Stream downward.
        '''
        for dummy in self.recurse(streamsOnly=False,
            restoreActiveSites=True):
            pass

    def makeImmutable(self):
        '''
        Clean this Stream: for self and all elements, purge all dead locations
        and remove all non-contained sites. Further, restore all active sites.
        '''
        self.sort() # must sort before making immutable
        self._mutable = False
        for e in self.recurse(streamsOnly=True):
            #e.purgeLocations(rescanIsDead=True)
            # NOTE: calling this method was having the side effect of removing
            # sites from locations when a Note was both in a Stream and in
            # an Interval
            if e.isStream:
                e.sort() # sort before making immutable
                e._mutable = False

    def makeMutable(self, recurse=True):
        self._mutable = True
        if recurse:
            for e in self.recurse(streamsOnly=True):
                # do not recurse, as will get all Stream
                e.makeMutable(recurse=False)
        self.elementsChanged()

    #---------------------------------------------------------------------------
    # duration and offset methods and properties

    def _getHighestOffset(self):
        '''

        >>> p = stream.Stream()
        >>> p.repeatInsert(note.Note("C"), [0, 1, 2, 3, 4])
        >>> p.highestOffset
        4.0
        '''
        if 'HighestOffset' in self._cache and self._cache["HighestOffset"] is not None:
            pass  # return cache unaltered
        elif len(self._elements) == 0:
            self._cache["HighestOffset"] = 0.0
        elif self.isSorted is True:
            eLast = self._elements[-1]
            self._cache["HighestOffset"] = self.elementOffset(eLast)
        else: # iterate through all elements
            highestOffsetSoFar = None
            for e in self._elements:
                candidateOffset = self.elementOffset(e)
                if highestOffsetSoFar is None or candidateOffset > highestOffsetSoFar:
                    highestOffsetSoFar = candidateOffset
            
            if highestOffsetSoFar is not None:
                self._cache["HighestOffset"] = float(highestOffsetSoFar)
            else:
                self._cache["HighestOffset"] = None
        return self._cache["HighestOffset"]

    highestOffset = property(_getHighestOffset,
        doc='''Get start time of element with the highest offset in the Stream.
        Note the difference between this property and highestTime
        which gets the end time of the highestOffset



        >>> stream1 = stream.Stream()
        >>> for offset in [0, 4, 8]:
        ...     n = note.Note('G#', type='whole')
        ...     stream1.insert(offset, n)
        >>> stream1.highestOffset
        8.0
        >>> stream1.highestTime
        12.0
        ''')

    def _setHighestTime(self, value):
        '''For internal use only.
        '''
        self._cache["HighestTime"] = value

    def _getHighestTime(self):
        '''
        Returns the largest offset plus duration.
        see complete instructions in property highestTime.

        >>> n = note.Note('C#')
        >>> n.quarterLength = 3

        >>> q = stream.Stream()
        >>> for i in [20, 0, 10, 30, 40]:
        ...    p = stream.Stream()
        ...    p.repeatInsert(n, [0, 1, 2, 3, 4])
        ...    q.insert(i, p) # insert out of order
        >>> len(q.flat)
        25
        >>> q.highestTime # this works b/c the component Stream has an duration
        47.0
        >>> r = q.flat

        OMIT_FROM_DOCS

        Make sure that the cache really is empty
        >>> 'HighestTime' in r._cache
        False
        >>> r.highestTime # 44 + 3
        47.0
        '''
#         environLocal.printDebug(['_getHighestTime', 'isSorted', self.isSorted, self])
        # remove cache -- durations might change...
        if 'HighestTime' in self._cache and self._cache["HighestTime"] is not None:
            pass  # return cache unaltered
        elif len(self._elements) == 0:
        #if len(self._elements) == 0:
            self._cache["HighestTime"] = 0.0
            return 0.0
        else:
            highestTimeSoFar = Fraction(0, 1)
            # TODO: optimize for a faster way of doing this.
            # but cannot simply look at the last element because what if the penultimate element, with a
            # lower offset has a longer duration than the last?
            # Take the case where a whole note appears a 0.0, but a textExpression (ql=0) at 0.25 --
            # isSorted would be true, but highestTime should be 4.0 not 0.25
            for e in self._elements:
                try:
                    candidateOffset = (self.elementOffset(e) +
                                   e.duration.quarterLength)
                except:
                    #print(self, e, id(e), e.offset, e.getSites())
                    raise
                if candidateOffset > highestTimeSoFar:
                    highestTimeSoFar = candidateOffset
            self._cache["HighestTime"] = float(highestTimeSoFar)
        return self._cache["HighestTime"]

    highestTime = property(_getHighestTime, doc='''
        Returns the maximum of all Element offsets plus their Duration
        in quarter lengths. This value usually represents the last
        "release" in the Stream.


        Stream.duration is usually equal to the highestTime
        expressed as a Duration object, but it can be set separately
        for advanced operations.


        Example: Insert a dotted half note at position 0 and see where
        it cuts off:



        >>> p1 = stream.Stream()
        >>> p1.highestTime
        0.0

        >>> n = note.Note('A-')
        >>> n.quarterLength = 3
        >>> p1.insert(0, n)
        >>> p1.highestTime
        3.0


        Now insert in the same stream, the dotted half note
        at positions 1, 2, 3, 4 and see when the final note cuts off:



        >>> p1.repeatInsert(n, [1, 2, 3, 4])
        >>> p1.highestTime
        7.0
        ''')


    def _getLowestOffset(self):
        '''



        >>> p = stream.Stream()
        >>> p.repeatInsert(note.Note('D5'), [0, 1, 2, 3, 4])
        >>> q = stream.Stream()
        >>> q.repeatInsert(p, list(range(0,50,10)))
        >>> len(q.flat)
        25
        >>> q.lowestOffset
        0.0
        >>> r = stream.Stream()
        >>> r.repeatInsert(q, list(range(97, 500, 100)))
        >>> len(r.flat)
        125
        >>> r.lowestOffset
        97.0
        '''
        if 'lowestOffset' in self._cache and self._cache["LowestOffset"] is not None:
            pass  # return cache unaltered
        elif len(self._elements) == 0:
            self._cache["LowestOffset"] = 0.0
        elif self.isSorted is True:
            eFirst = self._elements[0]
            self._cache["LowestOffset"] = self.elementOffset(eFirst)
        else: # iterate through all elements
            minOffsetSoFar = None
            for e in self._elements:
                candidateOffset = self.elementOffset(e)
                if minOffsetSoFar is None or candidateOffset < minOffsetSoFar:
                    minOffsetSoFar = candidateOffset
            self._cache["LowestOffset"] = minOffsetSoFar

            #environLocal.printDebug(['_getLowestOffset: iterated elements', min])

        return self._cache["LowestOffset"]


    lowestOffset = property(_getLowestOffset, doc='''
        Get the start time of the Element with the lowest offset in the Stream.



        >>> stream1 = stream.Stream()
        >>> for x in range(3,5):
        ...     n = note.Note('G#')
        ...     stream1.insert(x, n)
        ...
        >>> stream1.lowestOffset
        3.0


        If the Stream is empty, then the lowest offset is 0.0:


        >>> stream2 = stream.Stream()
        >>> stream2.lowestOffset
        0.0

        ''')

    def _getDuration(self):
        '''
        Gets the duration of the whole stream (generally the highestTime, but can be set
        independently).
        '''
        if self._unlinkedDuration is not None:
            return self._unlinkedDuration
        #elif 'Duration' in self._cache and self._cache["Duration"] is not None:
            #environLocal.printDebug(['returning cached duration'])
        #    return self._cache["Duration"]
        else:
            #environLocal.printDebug(['creating new duration based on highest time'])
            self._cache["Duration"] = duration.Duration()
            self._cache["Duration"].quarterLength = self.highestTime
            return self._cache["Duration"]

    def _setDuration(self, durationObj):
        '''
        Set the total duration of the Stream independently of the highestTime
        of the stream.  Useful to define the scope of the stream as independent
        of its constituted elements.

        If set to None, then the default behavior of computing automatically from highestTime is reestablished.
        '''
        if (isinstance(durationObj, duration.Duration)):
            self._unlinkedDuration = durationObj
        elif (durationObj is None):
            self._unlinkedDuration = None
        else: # need to permit Duration object assignment here
            raise Exception('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration, doc='''
        Returns the total duration of the Stream, from the beginning of the stream until the end of the final element.
        May be set independently by supplying a Duration object.



        >>> a = stream.Stream()
        >>> q = note.Note(type='quarter')
        >>> a.repeatInsert(q, [0,1,2,3])
        >>> a.highestOffset
        3.0
        >>> a.highestTime
        4.0
        >>> a.duration.quarterLength
        4.0


        Advanced usage: override the duration from what is set:


        >>> newDuration = duration.Duration("half")
        >>> newDuration.quarterLength
        2.0

        >>> a.duration = newDuration
        >>> a.duration.quarterLength
        2.0


        Note that the highestTime for the stream is the same
        whether duration is overriden or not:


        >>> a.highestTime
        4.0
        ''')


    def _setSeconds(self, value):
        # setting the seconds on a Stream for now is the same as on a
        # Music21Object, which reassigns Duration
        base.Music21Object._setSeconds(self, value)

    def _getSeconds(self):
        getTempoFromContext = False
        # need to find all tempo indications and the number of quarter lengths
        # under each
        tiStream = self.getElementsByClass('TempoIndication')
        offsetMetronomeMarkPairs = []

        if len(tiStream) == 0:
            getTempoFromContext = True
        else:
            for ti in tiStream:
                o = self.elementOffset(ti)
                # get the desired metronome mark from any of ti classes
                mm = ti.getSoundingMetronomeMark()
                offsetMetronomeMarkPairs.append([o, mm])

        for i, (o, mm) in enumerate(offsetMetronomeMarkPairs):
            if i == 0 and o > 0.0:
                getTempoFromContext = True
            break # just need first

        if getTempoFromContext:
            ti = self.getContextByClass('TempoIndication')
            if ti is None:
                raise StreamException('cannot get a seconds duration when no TempoIndication classes are found in or before this Stream.')
            else: # insert at zero offset position, even though coming from
                # outside this stream
                mm = ti.getSoundingMetronomeMark()
                offsetMetronomeMarkPairs = [
                    [0.0, mm]] + offsetMetronomeMarkPairs
        sec = 0.0
        for i, (o, mm) in enumerate(offsetMetronomeMarkPairs):
            # handle only one mm right away
            if len(offsetMetronomeMarkPairs) == 1:
                sec += mm.durationToSeconds(self.highestTime)
                break
            oStart, mmStart = o, mm
            # if not the last ti, get the next by index to get the offset
            if i < len(offsetMetronomeMarkPairs) - 1:
                # cases of two or more remain
                oEnd, unused_mmEnd = offsetMetronomeMarkPairs[i+1]
            else: # at the last
                oEnd = self.highestTime
            sec += mmStart.durationToSeconds(oEnd-oStart)

        return sec


    seconds = property(_getSeconds, _setSeconds, doc = '''
        Get or set the duration of this Stream in seconds, assuming that this object contains a :class:`~music21.tempo.MetronomeMark` or :class:`~music21.tempo.MetricModulation`.


        >>> s = corpus.parse('bwv66.6') # piece without a tempo
        >>> sFlat = s.flat
        >>> t = tempo.MetronomeMark('adagio')
        >>> sFlat.insert(0, t)
        >>> sFlat.seconds
        38.57142857...
        >>> tFast = tempo.MetronomeMark('allegro')
        >>> sFlat.replace(t, tFast)
        >>> sFlat.seconds
        16.363...
        ''')


    def metronomeMarkBoundaries(self, srcObj=None):
        '''
        Return a list of offset start, offset end,
        MetronomeMark triples for all TempoIndication objects found
        in this Stream or a Stream provided by srcObj.

        If no MetronomeMarks are found, or an initial region does not
        have a MetronomeMark, a mark of quarter equal to 120 is provided as default.

        Note that if other TempoIndication objects are defined,
        they will be converted to MetronomeMarks and returned here


        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 8)
        >>> s.insert([6, tempo.MetronomeMark(number=240)])
        >>> s.metronomeMarkBoundaries()
        [(0.0, 6.0, <music21.tempo.MetronomeMark animato Quarter=120>), (6.0, 8.0, <music21.tempo.MetronomeMark Quarter=240>)]
        '''
        if srcObj is None:
            srcObj = self
        # get all tempo indications from the flat Stream;
        # using flat here may not always be desirable
        # may want to do a recursive upward search as well
        srcFlat = srcObj.flat
        tiStream = srcFlat.getElementsByClass('TempoIndication')
        mmBoundaries = [] # a  list of (start, end, mm)

        # not sure if this should be taken from the flat representation
        highestTime = srcFlat.highestTime
        lowestOffset = srcFlat.lowestOffset

        # if no tempo
        if len(tiStream) == 0:
            mmDefault = tempo.MetronomeMark(number=120) # a default
            mmBoundaries.append((lowestOffset, highestTime, mmDefault))
        # if just one tempo
        elif len(tiStream) == 1:
            # get offset from flat source
            o = tiStream[0].getOffsetBySite(srcFlat)
            mm = tiStream[0].getSoundingMetronomeMark()
            if o > lowestOffset:
                mmDefault = tempo.MetronomeMark(number=120) # a default
                mmBoundaries.append((lowestOffset, o, mmDefault))
                mmBoundaries.append((o, highestTime, mm))
            else:
                mmBoundaries.append((lowestOffset, highestTime, mm))
        # one or more tempi
        else:
            offsetPairs = []
            for ti in tiStream:
                o = ti.getOffsetBySite(srcObj)
                offsetPairs.append([o, ti.getSoundingMetronomeMark()])
            # fill boundaries
            # if lowest region not defined, supply as default
            if offsetPairs[0][0] > lowestOffset:
                mmDefault = tempo.MetronomeMark(number=120) # a default
                mmBoundaries.append((lowestOffset, offsetPairs[0][0],
                                     mmDefault))
                mmBoundaries.append((offsetPairs[0][0], offsetPairs[1][0],
                                     offsetPairs[0][1]))
            else: # just add the first range
                mmBoundaries.append((offsetPairs[0][0], offsetPairs[1][0],
                                     offsetPairs[0][1]))
            # add any remaining ranges, starting from the second; if last,
            # use the highest time as the boundary
            for i, (o, mm) in enumerate(offsetPairs):
                if i == 0:
                    continue # already added first
                elif i == len(offsetPairs) - 1: # last index
                    mmBoundaries.append((offsetPairs[i][0], highestTime,
                                         offsetPairs[i][1]))
                else: # add with next boundary
                    mmBoundaries.append((offsetPairs[i][0], offsetPairs[i+1][0],
                                         offsetPairs[i][1]))

        #environLocal.printDebug(['self.metronomeMarkBoundaries()', 'got mmBoundaries:', mmBoundaries])
        return mmBoundaries

    def _accumulatedSeconds(self, mmBoundaries, oStart, oEnd):
        '''
        Given MetronomeMark boundaries, for any pair of offsets,
        determine the realized duration in seconds.
        '''
        # assume tt mmBoundaries are in order
        totalSeconds = 0.0
        activeStart = oStart
        activeEnd = None
        for s, e, mm in mmBoundaries:
            if activeStart >= s and activeStart < e:
                # find time in this region
                if oEnd < e: # if end within this region
                    activeEnd = oEnd
                else: # if end after this region
                    activeEnd = e
                #environLocal.printDebug(['activeStart', activeStart, 'activeEnd', activeEnd, 's, e, mm', s, e, mm])
                totalSeconds += mm.durationToSeconds(activeEnd-activeStart)
            else:
                continue
            if activeEnd == oEnd:
                break
            else: # continue on
                activeStart = activeEnd
        return totalSeconds

    def _getSecondsMap(self, srcObj=None):
        '''
        Return a list of dictionaries for all elements in this Stream,
        where each dictionary defines the real-time characteristics of
        the stored events. This will attempt to find
        all :class:`~music21.tempo.TempoIndication` subclasses and use these
        values to realize tempi. If not initial tempo is found,
        a tempo of 120 BPM will be provided.
        '''
        if srcObj is None:
            srcObj = self
        mmBoundaries = self.metronomeMarkBoundaries(srcObj=srcObj)

        # not sure if this should be taken from the flat representation
        lowestOffset = srcObj.lowestOffset

        secondsMap = [] # list of start, start+dur, element
        if srcObj.hasVoices():
            groups = []
            for i, v in enumerate(srcObj.voices):
                groups.append((v.flat, i))
        else: # create a single collection
            groups = [(srcObj, None)]

        # get accumulated time over many possible tempo changes for
        # start/end offset
        for group, voiceIndex in groups:
            for e in group:
                if isinstance(e, bar.Barline):
                    continue
                if e.duration is not None:
                    dur = e.duration.quarterLength
                else:
                    dur = 0
                offset = round(e.getOffsetBySite(group), 8)
                # calculate all time regions given this offset

                # all stored values are seconds
                secondsDict = {}
                secondsDict['offsetSeconds'] = srcObj._accumulatedSeconds(
                                      mmBoundaries, lowestOffset, offset)
                secondsDict['durationSeconds'] = srcObj._accumulatedSeconds(
                                      mmBoundaries, offset, offset + dur)
                secondsDict['endTimeSeconds'] = (secondsDict['offsetSeconds'] +
                                          secondsDict['durationSeconds'])
                secondsDict['element'] = e
                secondsDict['voiceIndex'] = voiceIndex
                secondsMap.append(secondsDict)
        return secondsMap


    secondsMap = property(_getSecondsMap, doc='''
        Returns a list where each element is a dictionary consisting of the 'offsetSeconds' in seconds of each element in a Stream, the 'duration' in seconds, the 'endTimeSeconds' in seconds (that is, the offset plus the duration), and the 'element' itself. Also contains a 'voiceIndex' entry which contains the voice number of the element, or None if there
        are no voices.


        >>> mm1 = tempo.MetronomeMark(number=120)
        >>> n1 = note.Note(type='quarter')
        >>> c1 = clef.AltoClef()
        >>> n2 = note.Note(type='half')
        >>> s1 = stream.Stream()
        >>> s1.append([mm1, n1, c1, n2])
        >>> om = s1.secondsMap
        >>> om[3]['offsetSeconds']
        0.5
        >>> om[3]['endTimeSeconds']
        1.5
        >>> om[3]['element'] is n2
        True
        >>> om[3]['voiceIndex']
    ''')


    #---------------------------------------------------------------------------
    # Metadata access

    def _getMetadata(self):
        '''


        >>> a = stream.Stream()
        >>> a.metadata = metadata.Metadata()
        '''
        mdList = self.getElementsByClass('Metadata')
        # only return metadata that has an offset = 0.0
        mdList = mdList.getElementsByOffset(0)
        if len(mdList) == 0:
            return None
        else:
            return mdList[0]

    def _setMetadata(self, metadataObj):
        '''

        >>> a = stream.Stream()
        >>> a.metadata = metadata.Metadata()
        '''
        oldMetadata = self._getMetadata()
        if oldMetadata is not None:
            #environLocal.printDebug(['removing old metadata', oldMetadata])
            junk = self.pop(self.index(oldMetadata))

        if metadataObj is not None and isinstance(metadataObj, metadata.Metadata):
            self.insert(0, metadataObj)

    metadata = property(_getMetadata, _setMetadata,
        doc = '''
        Get or set the :class:`~music21.metadata.Metadata` object
        found at the beginning (offset 0) of this Stream.



        >>> s = stream.Stream()
        >>> s.metadata = metadata.Metadata()
        >>> s.metadata.composer = 'frank'
        >>> s.metadata.composer
        'frank'
        ''')

    #---------------------------------------------------------------------------
    # these methods override the behavior inherited from base.py

    def _getMeasureOffset(self):
        # this normally returns the offset of this object in its container
        # for now, simply return the offset
        return self.getOffsetBySite(self.activeSite)

    def _getBeat(self):
        # this normally returns the beat within a measure; here, it could
        # be beats from the beginning?
        return None

    beat = property(_getBeat)

    def _getBeatStr(self):
        return None

    beatStr = property(_getBeatStr, doc='''
    unlike other Music21Objects, streams always have beatStr (beat string) of None
    ''')

    def _getBeatDuration(self):
        # this returns the duration of the active beat
        return None

    beatDuration = property(_getBeatDuration, doc='unlike other Music21Objects, streams always have beatDuration of None')

    def _getBeatStrength(self):
        # this returns the accent weight of the active beat
        return None

    beatStrength = property(_getBeatStrength, doc='unlike other Music21Objects, streams always have beatStrength of None')

    def beatAndMeasureFromOffset(self, searchOffset, fixZeros=True):
        '''
        Returns a two-element tuple of the beat and the Measure object (or the first one
        if there are several at the same offset; unlikely but possible) for a given
        offset from the start of this Stream (that contains measures).

        Recursively searches for measures.  Note that this method assumes that all parts
        have measures of consistent length.  If that's not the case, this
        method can be called on the relevant part.

        This algorithm should work even for weird time signatures such as 2+3+2/8.


        >>> bach = corpus.parse('bach/bwv1.6')
        >>> bach.parts[0].measure(2).getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 4/4>
        >>> returnTuples = []
        >>> for offset in [0.0, 1.0, 2.0, 5.0, 5.5]:
        ...     returnTuples.append(bach.beatAndMeasureFromOffset(offset))
        >>> returnTuples
        [(4.0, <music21.stream.Measure 0 offset=0.0>), (1.0, <music21.stream.Measure 1 offset=1.0>), (2.0, <music21.stream.Measure 1 offset=1.0>), (1.0, <music21.stream.Measure 2 offset=5.0>), (1.5, <music21.stream.Measure 2 offset=5.0>)]

        To get just the measureNumber and beat, use a transformation like this:
        >>> [(beat, measureObj.number) for beat, measureObj in returnTuples]
        [(4.0, 0), (1.0, 1), (2.0, 1), (1.0, 2), (1.5, 2)]

        Adapted from contributed code by Dmitri Tymoczko.  With thanks to DT.
        '''
        myStream = self
        if not myStream.hasMeasures():
            if myStream.hasPartLikeStreams():
                foundPart = False
                for subStream in myStream:
                    if 'Stream' not in subStream.classes:
                        continue
                    if subStream.hasMeasures():
                        foundPart = True
                        myStream = subStream
                        break
                if not foundPart:
                    raise StreamException("beatAndMeasureFromOffset: couldn't find any parts!")
                    # was return False
            else:
                if not myStream.hasMeasures():
                    raise StreamException("beatAndMeasureFromOffset: couldn't find any measures!")
                    # return False
        #Now we get the measure containing our offset.
        #In most cases this second part of the code does the job.
        myMeas = myStream.getElementAtOrBefore(searchOffset, classList = ['Measure'])
        if myMeas is None:
            raise StreamException("beatAndMeasureFromOffset: no measure at that offset.")
        ts1 = myMeas.timeSignature
        if ts1 is None:
            ts1 = myMeas.getContextByClass('TimeSignature')

        if ts1 is None:
            raise StreamException("beatAndMeasureFromOffset: could not find a time signature for that place.")
        try:
            myBeat = ts1.getBeatProportion(searchOffset - myMeas.offset)
        except:
            raise StreamException("beatAndMeasureFromOffset: offset is beyond the end of the piece")
        foundMeasureNumber = myMeas.number
        # deal with second half of partial measures...

        #Now we deal with the problem case, where we have the second half of a partial measure.  These are
        #treated as unnumbered measures (or measures with suffix 'X') by notation programs, even though they are
        #logically part of the previous measure.  The variable padBeats will represent extra beats we add to the front
        #of our partial measure
        numSuffix = myMeas.numberSuffix
        if numSuffix == "":
            numSuffix = None

        if numSuffix is not None or (fixZeros and foundMeasureNumber == 0):
            prevMeas = myStream.getElementBeforeOffset(myMeas.offset, classList = ['Measure'])
            if prevMeas:
                ts2 = prevMeas.getContextByClass('TimeSignature')
                if not ts2:
                    raise StreamException("beatAndMeasureFromOffset: partial measure found, but could not find a time signature for the preceeding measure")
                #foundMeasureNumber = prevMeas.number
                if prevMeas.highestTime == ts2.barDuration.quarterLength:       # need this for chorales 197 and 280, where we
                    padBeats = ts2.beatCount                                    # have a full-length measure followed by a pickup in
                else:                                                           # a new time signature
                    padBeats = ts2.getBeatProportion(prevMeas.highestTime) - 1
                return (myBeat + padBeats, prevMeas)
            else:
                padBeats = ts1.getBeatProportion(ts1.barDuration.quarterLength - myMeas.duration.quarterLength) - 1    # partial measure at start of piece
                return (myBeat + padBeats, myMeas)
        else:
            return (myBeat, myMeas)



    #---------------------------------------------------------------------------
    # transformations

    def transpose(self, value, inPlace=False, recurse=True,
        classFilterList=('Note', 'Chord')):
        '''
        Transpose all specified classes in the
        Stream by the
        user-provided value. If the value is an integer, the
        transposition is treated in half steps. If the value is
        a string, any Interval string specification can be
        provided.

        returns a new Stream by default, but if the
        optional "inPlace" key is set to True then
        it modifies pitches in place.
        
        TODO: for generic interval set accidental by key signature.
        TODO: set recurse = False? 
        

        >>> aInterval = interval.Interval('d5')

        >>> aStream = corpus.parse('bach/bwv324.xml')
        >>> part = aStream.parts[0]
        >>> [str(p) for p in aStream.parts[0].pitches[:10]]
        ['B4', 'D5', 'B4', 'B4', 'B4', 'B4', 'C5', 'B4', 'A4', 'A4']

        >>> bStream = aStream.parts[0].flat.transpose('d5')
        >>> [str(p) for p in bStream.pitches[:10]]
        ['F5', 'A-5', 'F5', 'F5', 'F5', 'F5', 'G-5', 'F5', 'E-5', 'E-5']

        Test that aStream hasn't been changed:

        >>> [str(p) for p in aStream.parts[0].pitches[:10]]
        ['B4', 'D5', 'B4', 'B4', 'B4', 'B4', 'C5', 'B4', 'A4', 'A4']

        >>> cStream = bStream.flat.transpose('a4')
        >>> [str(p) for p in cStream.pitches[:10]]
        ['B5', 'D6', 'B5', 'B5', 'B5', 'B5', 'C6', 'B5', 'A5', 'A5']

        >>> cStream.flat.transpose(aInterval, inPlace=True)
        >>> [str(p) for p in cStream.pitches[:10]]
        ['F6', 'A-6', 'F6', 'F6', 'F6', 'F6', 'G-6', 'F6', 'E-6', 'E-6']
        '''
        # only change the copy
        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self
#         for p in post.pitches: # includes chords
#             # do inplace transpositions on the deepcopy
#             p.transpose(value, inPlace=True)

#         for e in post.getElementsByClass(classFilterList=classFilterList):
#             e.transpose(value, inPlace=True)

        # this will get all elements at this level and downward.
        if recurse is True:
            siterator = post.recurse()
        else:
            siterator = post.__iter__()
        
        for e in siterator.getElementsByClass(classFilterList):
            e.transpose(value, inPlace=True)
        if not inPlace:
            return post
        else:
            return None


    def scaleOffsets(self, amountToScale, anchorZero='lowest',
            anchorZeroRecurse=None, inPlace=True):
        '''
        Scale all offsets by a multiplication factor given
        in `amountToScale`. Durations are not altered.

        To augment or diminish a Stream,
        see the :meth:`~music21.stream.Stream.augmentOrDiminish` method.

        The `anchorZero` parameter determines if and/or where
        the zero offset is established for the set of
        offsets in this Stream before processing.
        Offsets are shifted to make either the lower
        or upper values the new zero; then offsets are scaled;
        then the shifts are removed. Accepted values are None
        (no offset shifting), "lowest", or "highest".

        The `anchorZeroRecurse` parameter determines the
        anchorZero for all embedded Streams, and Streams
        embedded within those Streams. If the lowest offset
        in an embedded Stream is non-zero, setting this value
        to None will a the space between the start of that
        Stream and the first element to be scaled. If the
        lowest offset in an embedded Stream is non-zero,
        setting this value to 'lowest' will not alter the
        space between the start of that Stream and the first
        element to be scaled.

        To shift all the elements in a Stream, see the
        :meth:`~music21.stream.Stream.shiftElements` method.

        TODO: inPlace by default should be False
        TODO: if inPlace is True, return None
        '''
        # if we have offsets at 0, 2, 4
        # we scale by 2, getting offsets at 0, 4, 8

        # compare to offsets at 10, 12, 14
        # we scale by 2; if we do not anchor at lower, we get 20, 24, 28
        # if we anchor, we get 10, 14, 18

        if not amountToScale > 0:
            raise StreamException('amountToScale must be greater than zero')

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # first, get the offset shift requested
        if anchorZero in ['lowest']:
            offsetShift = Fraction(returnObj.lowestOffset)
        elif anchorZero in ['highest']:
            offsetShift = Fraction(returnObj.highestOffset)
        elif anchorZero in [None]:
            offsetShift = Fraction(0, 1)
        else:
            raise StreamException('an achorZero value of %s is not accepted' % anchorZero)

        for e in returnObj._elements:

            # subtract the offset shift (and lowestOffset of 80 becomes 0)
            # then apply the amountToScale
            o = (returnObj.elementOffset(e) - offsetShift) * amountToScale
            # after scaling, return the shift taken away
            o += offsetShift

            #environLocal.printDebug(['changng offset', o, scalar, offsetShift])

            returnObj.setElementOffset(e, o)
            # need to look for embedded Streams, and call this method
            # on them, with inPlace == True, as already copied if
            # inPlace is != True
            #if hasattr(e, "elements"): # recurse time:
            if e.isStream:
                e.scaleOffsets(amountToScale,
                               anchorZero=anchorZeroRecurse,
                               anchorZeroRecurse=anchorZeroRecurse,
                inPlace=True)

        returnObj.elementsChanged()
        return returnObj


    def scaleDurations(self, amountToScale, inPlace=False):
        '''
        Scale all durations by a provided scalar. Offsets are not modified.

        To augment or diminish a Stream, see the :meth:`~music21.stream.Stream.augmentOrDiminish` method.

        We do not retain durations in any circumstance; if inPlace=True, two deepcopies are done
        which can be quite slow.
        '''
        if not amountToScale > 0:
            raise StreamException('amountToScale must be greater than zero')

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        for e in returnObj.recurse().getElementsNotOfClass('Stream'):
            if e.duration is not None:
                e.duration = e.duration.augmentOrDiminish(amountToScale)

        returnObj.elementsChanged()
        if inPlace is not True:
            return returnObj


    def augmentOrDiminish(self, amountToScale, inPlace=False):
        '''
        Given a number greater than zero,
        multiplies the current quarterLength of the
        duration of each element by this number
        as well as their offset and returns a new Stream.
        Or if `inPlace` is
        set to True, modifies the durations of each
        element within the stream.


        A number of .5 will halve the durations and relative
        offset positions; a number of 2 will double the
        durations and relative offset positions.



        Note that the default for inPlace is the opposite
        of what it is for augmentOrDiminish on a Duration.
        This is done purposely to reflect the most common
        usage.



        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> s.repeatAppend(n, 10)
        >>> s.highestOffset, s.highestTime
        (9.0, 10.0)
        >>> s1 = s.augmentOrDiminish(2)
        >>> s1.highestOffset, s1.highestTime
        (18.0, 20.0)
        >>> s1 = s.augmentOrDiminish(.5)
        >>> s1.highestOffset, s1.highestTime
        (4.5, 5.0)
        '''
        if not amountToScale > 0:
            raise StreamException('amountToScale must be greater than zero')
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # inPlace is True as a copy has already been made if nec
        returnObj.scaleOffsets(amountToScale=amountToScale, anchorZero='lowest',
            anchorZeroRecurse=None, inPlace=True)
        returnObj.scaleDurations(amountToScale=amountToScale, inPlace=True)
        returnObj.elementsChanged()

        # do not need to call elements changed, as called in sub methods
        return returnObj


    def quantize(self, quarterLengthDivisors=None,
            processOffsets=True, processDurations=True, inPlace=False, recurse=True):
        '''
        Quantize time values in this Stream by snapping offsets
        and/or durations to the nearest multiple of a quarter length value
        given as one or more divisors of 1 quarter length. The quantized
        value found closest to a divisor multiple will be used.

        The `quarterLengthDivisors` provides a flexible way to provide quantization
        settings. For example, (2,) will snap all events to eighth note grid.
        (4, 3) will snap events to sixteenth notes and eighth note triplets,
        whichever is closer. (4, 6) will snap events to sixteenth notes and
        sixteenth note triplets.  If quarterLengthDivisors is not specified then
        defaults.quantizationQuarterLengthDivisors is used.  The default is (4, 3).

        `processOffsets` determines whether the Offsets are quantized.

        `processDurations` determines whether the Durations are quantized.

        Both are set to True by default.  Setting both to False does nothing to the Stream.

        if `inPlace` is True then the quantization is done on the Stream itself.  If False
        (default) then a new quantized Stream of the same class is returned.

        If `recurse` is True then all substreams are also quantized.  If False (TODO: MAKE default)
        then only the highest level of the Stream is quantized.



        >>> n = note.Note()
        >>> n.quarterLength = .49
        >>> s = stream.Stream()
        >>> s.repeatInsert(n, [0.1, .49, .9])
        >>> nshort = note.Note()
        >>> nshort.quarterLength = .26
        >>> s.repeatInsert(nshort, [1.49, 1.76])
        >>> s.quantize([4], processOffsets=True, processDurations=True, inPlace=True)
        >>> [e.offset for e in s]
        [0.0, 0.5, 1.0, 1.5, 1.75]
        >>> [e.duration.quarterLength for e in s]
        [0.5, 0.5, 0.5, 0.25, 0.25]


        # test with default quarterLengthDivisors...

        >>> s = stream.Stream()
        >>> s.repeatInsert(n, [0.1, .49, .9])
        >>> nshort = note.Note()
        >>> nshort.quarterLength = .26
        >>> s.repeatInsert(nshort, [1.49, 1.76])
        >>> t = s.quantize(processOffsets=True, processDurations=True, inPlace=False)
        >>> [e.offset for e in t]
        [0.0, 0.5, 1.0, 1.5, 1.75]
        >>> [e.duration.quarterLength for e in t]
        [0.5, 0.5, 0.5, 0.25, 0.25]

        OMIT_FROM_DOCS


        Test changing defaults, running, and changing back...
        

        >>> dd = defaults.quantizationQuarterLengthDivisors
        >>> defaults.quantizationQuarterLengthDivisors = (3,)

        >>> u = s.quantize(processOffsets=True, processDurations=True, inPlace=False)
        >>> [e.offset for e in u]
        [0.0, Fraction(1, 3), 1.0, Fraction(4, 3), Fraction(5, 3)]
        >>> [e.duration.quarterLength for e in u]
        [Fraction(1, 3), Fraction(1, 3), Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)]

        >>> defaults.quantizationQuarterLengthDivisors = dd
        >>> v = s.quantize(processOffsets=True, processDurations=True, inPlace=False)
        >>> [e.offset for e in v]
        [0.0, 0.5, 1.0, 1.5, 1.75]
        >>> [e.duration.quarterLength for e in v]
        [0.5, 0.5, 0.5, 0.25, 0.25]
        

        TODO: test recurse and inPlace etc.
        TODO: recurse should be off by default -- standard

        '''
        if quarterLengthDivisors is None:
            quarterLengthDivisors = defaults.quantizationQuarterLengthDivisors
        
        # this presently is not trying to avoid overlaps that
        # result from quantization; this may be necessary

        def bestMatch(target, divisors):
            found = []
            for div in divisors:
                match, error, signedError = common.nearestMultiple(target, (1.0/div))
                found.append((error, match, signedError)) # reverse for sorting
            # get first, and leave out the error
            bestMatchTuple = sorted(found)[0]
            return bestMatchTuple

        # if we have a min of .25 (sixteenth)
        # quarterLengthMin = quarterLengthDivisors[0]


        # TODO: Use new filters...
        if inPlace is False:
            returnStream = copy.deepcopy(self)
        else:
            returnStream = self

        useStreams = [returnStream]
        if recurse is True:
            for obj in returnStream.recurse():
                if 'Stream' in obj.classes:
                    useStreams.append(obj)

        for useStream in useStreams:
            for e in useStream._elements:
                if processOffsets:
                    o = useStream.elementOffset(e)
                    sign = 1
                    if o < 0:
                        sign = -1
                        o = -1 * o
                    unused_error, oNew, signedError = bestMatch(float(o), quarterLengthDivisors)
                    useStream.setElementOffset(e, oNew * sign)
                    if hasattr(e, 'editorial') and hasattr(e.editorial, 'misc') and signedError != 0:
                        e.editorial.misc['offsetQuantizationError'] = signedError * sign
                if processDurations:
                    if e.duration is not None:
                        ql = e.duration.quarterLength
                        if ql < 0:  # buggy MIDI file? 
                            ql = 0
                        unused_error, qlNew, signedError = bestMatch(float(ql), quarterLengthDivisors)
                        e.duration.quarterLength = qlNew
                        if hasattr(e, 'editorial') and hasattr(e.editorial, 'misc') and signedError != 0:
                            e.editorial.misc['quarterLengthQuantizationError'] = signedError

        if inPlace is False:
            return returnStream

    def expandRepeats(self, copySpanners=True):
        '''Expand this Stream with repeats. Nested repeats
        given with :class:`~music21.bar.Repeat` objects, or
        repeats and sections designated with
        :class:`~music21.repeat.RepeatExpression` objects, are all expanded.

        This method always returns a new Stream, with
        deepcopies of all contained elements at all levels.

        Uses the :class:`~music21.repeat.Expander` object in the `repeat` module.

        TODO: DOC TEST
        '''
        if not self.hasMeasures():
            raise StreamException('cannot process repeats on Stream that does not contian measures')

        ex = repeat.Expander(self)
        post = ex.process()

        # copy all non-repeats
        # do not copy repeat brackets
        for e in self.getElementsNotOfClass('Measure'):
            if 'RepeatBracket' not in e.classes:
                eNew = copy.deepcopy(e) # assume that this is needed
                post.insert( self.elementOffset(e), eNew)

        # all elements at this level and in measures have been copied; now we
        # need to reconnect spanners
        if copySpanners:
            #environLocal.printDebug(['Stream.expandRepeats', 'copying spanners'])
            #spannerBundle = spanner.SpannerBundle(post.flat.spanners)
            spannerBundle = post.spannerBundle
            # iterate over complete semi flat (need containers); find
            # all new/old pairs
            for e in post.semiFlat:
                # update based on last id, new object
                if e.sites.hasSpannerSite():
                    origin = e.derivation.origin
                    if (origin is not None and e.derivation.method == '__deepcopy__'):
                        spannerBundle.replaceSpannedElement(id(origin), e)

        return post


    #---------------------------------------------------------------------------
    # slicing and recasting a note as many notes

    def sliceByQuarterLengths(self, quarterLengthList, target=None,
        addTies=True, inPlace=False):
        '''
        Slice all :class:`~music21.duration.Duration` objects on all Notes and Rests 
        of this Stream.
        Duration are sliced according to values provided in `quarterLengthList` list.
        If the sum of these values is less than the Duration, the values are accumulated
        in a loop to try to fill the Duration. If a match cannot be found, an
        Exception is raised.

        If `target` is None, the entire Stream is processed. Otherwise, only the element
        specified is manipulated.

        TODO: return None if inPlace = True
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.iter.getElementsByClass('Measure'):
                m.sliceByQuarterLengths(quarterLengthList,
                    target=target, addTies=addTies, inPlace=True)
            returnObj.elementsChanged()
            return returnObj # exit

        if returnObj.hasPartLikeStreams():
            for p in returnObj.iter.getElementsByClass('Part'):
                p.sliceByQuarterLengths(quarterLengthList,
                    target=target, addTies=addTies, inPlace=True)
            returnObj.elementsChanged()
            return returnObj # exit

        if not common.isListLike(quarterLengthList):
            quarterLengthList = [quarterLengthList]

        if target is not None:
            # get the element out of rutern obj
            # need to use self.index to get index value
            eToProcess = [returnObj.elements[self.index(target)]]
        else: # get elements list from Stream
            eToProcess = returnObj.notesAndRests.elements

        for e in eToProcess:
            # if qlList values are greater than the found duration, skip
            if opFrac(sum(quarterLengthList)) > e.quarterLength:
                continue
            elif not opFrac(sum(quarterLengthList)) == e.quarterLength:
                # try to map a list that is of sufficient duration
                qlProcess = []
                i = 0
                while True:
                    qlProcess.append(
                        quarterLengthList[i%len(quarterLengthList)])
                    i += 1
                    sumQL = opFrac(sum(qlProcess))
                    if sumQL >= e.quarterLength:
                        break
            else:
                qlProcess = quarterLengthList

            #environLocal.printDebug(['got qlProcess', qlProcess, 'for element', e, e.quarterLength])

            if not opFrac(sum(qlProcess)) == e.quarterLength:
                raise StreamException('cannot map quarterLength list into element Duration: %s, %s' % (sum(qlProcess), e.quarterLength))

            post = e.splitByQuarterLengths(qlProcess, addTies=addTies)
            # remove e from the source
            oInsert = e.getOffsetBySite(returnObj)
            returnObj.remove(e)
            for eNew in post:
                returnObj._insertCore(oInsert, eNew)
                oInsert = opFrac(oInsert + eNew.quarterLength)

        returnObj.elementsChanged()
        return returnObj


    def sliceByGreatestDivisor(self, addTies=True, inPlace=False):
        '''
        Slice all :class:`~music21.duration.Duration` objects on all Notes and Rests of this Stream.
        Duration are sliced according to the approximate GCD found in all durations.

        TODO: return None if inPlace is True
        '''
        # when operating on a Stream, this should take all durations found and use the approximateGCD to get a min duration; then, call sliceByQuarterLengths

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.iter.getElementsByClass('Measure'):
                m.sliceByGreatestDivisor(addTies=addTies, inPlace=True)
            returnObj.elementsChanged()
            return returnObj # exit

        uniqueQuarterLengths = []
        for e in returnObj.notesAndRests:
            if e.quarterLength not in uniqueQuarterLengths:
                uniqueQuarterLengths.append(e.quarterLength)

        #environLocal.printDebug(['unique quarter lengths', uniqueQuarterLengths])

        # will raise an exception if no gcd can be found
        divisor = common.approximateGCD(uniqueQuarterLengths)

        # process in place b/c a copy, if necessary, has already been made
        returnObj.sliceByQuarterLengths(quarterLengthList=[divisor],
            target=None, addTies=addTies, inPlace=True)

        returnObj.elementsChanged()
        return returnObj


    def sliceAtOffsets(self, offsetList, target=None,
        addTies=True, inPlace=False, displayTiedAccidentals=False):
        '''
        Given a list of quarter lengths, slice and optionally tie all
        Durations at these points.

        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 4
        >>> s.append(n)
        >>> post = s.sliceAtOffsets([1, 2, 3], inPlace=True)
        >>> [(e.offset, e.quarterLength) for e in s]
        [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0)]

        TODO: return None if inPlace is True
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.iter.getElementsByClass('Measure'):
                # offset values are not relative to measure; need to
                # shift by each measure's offset
                offsetListLocal = [o - m.getOffsetBySite(returnObj) for o in offsetList]
                m.sliceAtOffsets(offsetList=offsetListLocal,
                    addTies=addTies, 
                    inPlace=True,
                    displayTiedAccidentals=displayTiedAccidentals)
            return returnObj # exit

        if returnObj.hasPartLikeStreams():
            # part-like requires getting Streams, not Parts
            for p in returnObj.iter.getElementsByClass('Stream'):
                offsetListLocal = [o - p.getOffsetBySite(returnObj) for o in offsetList]
                p.sliceAtOffsets(offsetList=offsetListLocal,
                    addTies=addTies, 
                    inPlace=True,
                    displayTiedAccidentals=displayTiedAccidentals)
            return returnObj # exit

        # list of start, start+dur, element, all in abs offset time
        offsetMap = self._getOffsetMap(returnObj)

        offsetList = [opFrac(o) for o in offsetList]

        for ob in offsetMap:
            # if target is defined, only modify that object
            e, oStart, oEnd, unused_voiceCount  = ob
            if target is not None and id(e) != id(target):
                continue

            cutPoints = []
            oStart = opFrac(oStart)
            oEnd = opFrac(oEnd)

            for o in offsetList:
                if o > oStart and o < oEnd:
                    cutPoints.append(o)
            #environLocal.printDebug(['cutPoints', cutPoints, 'oStart', oStart, 'oEnd', oEnd])
            if cutPoints:
                # remove old
                #eProc = returnObj.remove(e)
                eNext = e
                oStartNext = oStart
                for o in cutPoints:
                    oCut = o - oStartNext
                    unused_eComplete, eNext = eNext.splitAtQuarterLength(oCut,
                        retainOrigin=True, addTies=addTies,
                        displayTiedAccidentals=displayTiedAccidentals)
                    # only need to insert eNext, as eComplete was modified
                    # in place due to retainOrigin option
                    # insert at o, not oCut (duration into element)
                    returnObj._insertCore(o, eNext)
                    oStartNext = o
        returnObj.elementsChanged()
        return returnObj


    def sliceByBeat(self, target=None,
        addTies=True, inPlace=False, displayTiedAccidentals=False):
        '''
        Slice all elements in the Stream that have a Duration at
        the offsets determined to be the beat from the local TimeSignature.

        TODO: return None if inPlace is True
        '''

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass('Measure'):
                m.sliceByBeat(target=target,
                    addTies=addTies, inPlace=True,
                    displayTiedAccidentals=displayTiedAccidentals)
            return returnObj # exit

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Part'):
                p.sliceByBeat(target=target,
                    addTies=addTies, inPlace=True,
                    displayTiedAccidentals=displayTiedAccidentals)
            return returnObj # exit

        # this will return a default
        # using this method to work on Stream, not just Measures
        tsStream = returnObj.getTimeSignatures(returnDefault=True)

        if len(tsStream) == 0:
            raise StreamException('no time signature was found')
        elif len(tsStream) > 1:
            raise StreamException('not yet implemented: slice by changing time signatures')

        offsetList = tsStream[0].getBeatOffsets()
        returnObj.sliceAtOffsets(offsetList, target=target, addTies=addTies,
            inPlace=True, displayTiedAccidentals=displayTiedAccidentals)

        return returnObj

    #---------------------------------------------------------------------------
    # get boolean information from the Stream

    def hasMeasures(self):
        '''
        Return a boolean value showing if this Stream contains Measures.


        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 8)
        >>> s.hasMeasures()
        False
        >>> s.makeMeasures(inPlace=True)
        >>> len(s.getElementsByClass('Measure'))
        2
        >>> s.hasMeasures()
        True
        '''
        if 'hasMeasures' not in self._cache or self._cache['hasMeasures'] is None:
            post = False
            # do not need to look in endElements
            for obj in self._elements:
                # if obj is a Part, we have multi-parts
                if 'Measure' in obj.classes:
                    post = True
                    break # only need one
            self._cache['hasMeasures'] = post
        return self._cache['hasMeasures']


    def hasVoices(self):
        '''
        Return a boolean value showing if this Stream contains Voices
        '''
        if 'hasVoices' not in self._cache or self._cache['hasVoices'] is None:
            post = False
            # do not need to look in endElements
            for obj in self._elements:
                # if obj is a Part, we have multi-parts
                if 'Voice' in obj.classes:
                    post = True
                    break # only need one
            self._cache['hasVoices'] = post
        return self._cache['hasVoices']


    def hasPartLikeStreams(self):
        '''
        Return a boolean value showing if this Stream contains multiple Parts, or Part-like sub-Streams.
        Part-like sub-streams are Streams that contain Measures or Notes.


        >>> s = stream.Score()
        >>> s.hasPartLikeStreams()
        False
        >>> p1 = stream.Part()
        >>> p1.repeatAppend(note.Note(), 8)
        >>> s.insert(0, p1)
        >>> s.hasPartLikeStreams()
        True

        Flat objects do not have part-like Streams:

        >>> sf = s.flat
        >>> sf.hasPartLikeStreams()
        False
        '''
        if 'hasPartLikeStreams' not in self._cache or self._cache['hasPartLikeStreams'] is None:
            multiPart = False
            if not self.isFlat: # if flat, does not have parts!
                # do not need to look in endElements
                for obj in self._elements:
                    # if obj is a Part, we have multi-parts
                    if obj.isClassOrSubclass(['Part']):
                        multiPart = True
                        break
                    if obj.isClassOrSubclass(['Measure', 'Voice']):
                        multiPart = False
                        break
                    # if components are streams of Notes or Measures,
                    # than assume this is like a Part
                    elif obj.isStream and (
                                obj.iter.getElementsByClass('Measure') or 
                                obj.iter.notesAndRests):
                        multiPart = True
                        break # only need one
            self._cache['hasPartLikeStreams'] = multiPart
        return self._cache['hasPartLikeStreams']


    def isTwelveTone(self):
        '''
        Return true if this Stream only employs twelve-tone equal-tempered pitch values.


        >>> s = stream.Stream()
        >>> s.append(note.Note('G#4'))
        >>> s.isTwelveTone()
        True
        >>> s.append(note.Note('G~4'))
        >>> s.isTwelveTone()
        False
        '''
        for p in self.pitches:
            if not p.isTwelveTone():
                return False
        return True


    def isWellFormedNotation(self):
        '''
        Return True if, given the context of this Stream or Stream subclass,
        contains what appears to be well-formed notation. This often means
        the formation of Measures, or a Score that contains Part with Measures.


        >>> s = corpus.parse('bwv66.6')
        >>> s.isWellFormedNotation()
        True
        >>> s.parts[0].isWellFormedNotation()
        True
        >>> s.parts[0].getElementsByClass('Measure')[0].isWellFormedNotation()
        True
        '''
        # if a measure, we assume we are well-formed
        if 'Measure' in self.classes:
            return True
        elif 'Part' in self.classes:
            if self.hasMeasures():
                return True
        elif self.hasPartLikeStreams():
            # higher constraint than has part-like streams: has sub-streams
            # with Measures
            match = 0
            count = 0
            for s in self.getElementsByClass('Stream'):
                count += 1
                if s.hasMeasures():
                    match += 1
            if match == count:
                return True
        # all other conditions are not well-formed notation
        return False



    #---------------------------------------------------------------------------
    def _getNotesAndRests(self):
        '''
        see property `notesAndRests`, below
        '''
        if 'notesAndRests' not in self._cache or self._cache['notesAndRests'] is None:
            #environLocal.printDebug(['updating noteAndRests cache:', str(self), id(self)])
            # as this Stream will be retained, we do not want it to be
            # the same class as the source, thus, do not return subclass
            if self.isMeasure:
                returnStreamSubClass = False
            else:
                returnStreamSubClass = True
            self._cache['notesAndRests'] = self.getElementsByClass(
                                          'GeneralNote',
                            returnStreamSubClass=returnStreamSubClass)
        return self._cache['notesAndRests']

        #return self.getElementsByClass([note.GeneralNote, chord.Chord])
        # using string class names is import for some test contexts where
        # absolute class name matching fails
        #return self.getElementsByClass(['GeneralNote', 'Chord'])

    notesAndRests = property(_getNotesAndRests, doc='''
        The notesAndRests property of a Stream returns a new Stream object
        that consists only of the :class:`~music21.note.GeneralNote` objects found in
        the stream.  The new Stream will contain
        mostly notes and rests (including
        :class:`~music21.note.Note`,
        :class:`~music21.chord.Chord`,
        :class:`~music21.note.Rest`) but also their subclasses, such as
        `Harmony` objects (`ChordSymbols`, `FiguredBass`), `SpacerRests` etc.


        >>> s1 = stream.Stream()
        >>> k1 = key.KeySignature(0) # key of C
        >>> n1 = note.Note('B')
        >>> r1 = note.Rest()
        >>> c1 = chord.Chord(['A', 'B-'])
        >>> s1.append([k1, n1, r1, c1])
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of no sharps or flats>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Rest rest>
        {2.0} <music21.chord.Chord A B->

        `.notesAndRests` removes the `KeySignature` object but keeps the `Rest`.

        >>> notes1 = s1.notesAndRests
        >>> notes1.show('text')
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Rest rest>
        {2.0} <music21.chord.Chord A B->

        The same caveats about `Stream` classes and `.flat` in `.notes` apply here.
        ''')


    def _getNotes(self):
        if 'notes' not in self._cache or self._cache['notes'] is None:
            self._cache['notes'] = self.getElementsByClass('NotRest',
                                        returnStreamSubClass=False)
            self._cache['notes'].derivation.method = 'notes'
        return self._cache['notes']


    notes = property(_getNotes, doc='''
        The notes property of a Stream returns a new Stream object
        that consists only of the notes (that is,
        :class:`~music21.note.Note`,
        :class:`~music21.chord.Chord`, etc.) found
        in the stream. This excludes :class:`~music21.note.Rest` objects.


        >>> p1 = stream.Part()
        >>> k1 = key.KeySignature(0) # key of C
        >>> n1 = note.Note('B')
        >>> r1 = note.Rest()
        >>> c1 = chord.Chord(['A', 'B-'])
        >>> p1.append([k1, n1, r1, c1])
        >>> p1.show('text')
        {0.0} <music21.key.KeySignature of no sharps or flats>
        {0.0} <music21.note.Note B>
        {1.0} <music21.note.Rest rest>
        {2.0} <music21.chord.Chord A B->

        >>> p1.notes.show('text')
        {0.0} <music21.note.Note B>
        {2.0} <music21.chord.Chord A B->

        Notice that though `p1` is a `Part` object, `.notes` returns
        a generic `Stream` object.

        >>> p1.notes
        <music21.stream.Stream ...>

        Let's add a measure to `p1`:

        >>> m1 = stream.Measure()
        >>> n2 = note.Note("D")
        >>> m1.insert(0, n2)
        >>> p1.append(m1)

        Now note that `n2` is *not* found in `p1.notes`

        >>> p1.notes.show('text')
        {0.0} <music21.note.Note B>
        {2.0} <music21.chord.Chord A B->

        We need to call `p1.flat.notes` to find it:

        >>> p1.flat.notes.show('text')
        {0.0} <music21.note.Note B>
        {2.0} <music21.chord.Chord A B->
        {3.0} <music21.note.Note D>
        ''')

    def _getPitches(self):
        post = []
        for e in self.elements:
            if hasattr(e, "pitch"):
                post.append(e.pitch)
            # both Chords and Stream have a pitches properties; this just
            # causes a recursive pitch gathering
            elif hasattr(e, "pitches"):
                for p in e.pitches:
                    post.append(p)
            # do an ininstance comparison
            elif 'Pitch' in e.classes:
                post.append(e)
        return post

    pitches = property(_getPitches, doc='''
        Returns all :class:`~music21.pitch.Pitch` objects found in any
        element in the Stream as a Python List. Elements such as
        Streams, and Chords will have their Pitch objects accumulated as
        well. For that reason, a flat representation is not required.

        Pitch objects are returned in a List, not a Stream.  This usage
        differs from the .notes property, but makes sense since Pitch
        objects usually have by default a Duration of zero. This is an important difference
        between them and :class:`music21.note.Note` objects.


        >>> from music21 import corpus
        >>> a = corpus.parse('bach/bwv324.xml')
        >>> partOnePitches = a.parts[0].pitches
        >>> len(partOnePitches)
        25
        >>> partOnePitches[0]
        <music21.pitch.Pitch B4>
        >>> [str(p) for p in partOnePitches[0:10]]
        ['B4', 'D5', 'B4', 'B4', 'B4', 'B4', 'C5', 'B4', 'A4', 'A4']


        Note that the pitches returned above are
        objects, not text:

        >>> partOnePitches[0].octave
        4

        Since pitches are found from within internal objects,
        flattening the stream is not required:

        >>> len(a.pitches)
        104

        Chords get their pitches found as well:

        >>> c = chord.Chord(['C4','E4','G4'])
        >>> n = note.Note('F#4')
        >>> m = stream.Measure()
        >>> m.append(n)
        >>> m.append(c)
        >>> m.pitches
        [<music21.pitch.Pitch F#4>, <music21.pitch.Pitch C4>,
         <music21.pitch.Pitch E4>, <music21.pitch.Pitch G4>]
        ''')


    def pitchAttributeCount(self, pitchAttr='name'):
        '''
        Return a dictionary of pitch class usage (count)
        by selecting an attribute of the Pitch object.

        >>> from music21 import corpus
        >>> a = corpus.parse('bach/bwv324.xml')
        >>> pcCount = a.pitchAttributeCount('pitchClass')
        >>> for n in sorted(list(pcCount.keys())):
        ...     print ("%2d: %2d" % (n, pcCount[n]))
         0:  3
         2: 25
         3:  3
         4: 14
         6: 15
         7: 13
         9: 17
        11: 14
        >>> nameCount = a.pitchAttributeCount('name')
        >>> for n in sorted(list(nameCount.keys())):
        ...     print ("%2s: %2d" % (n, nameCount[n]))
         A: 17
         B: 14
         C:  3
         D: 25
        D#:  3
         E: 14
        F#: 15
         G: 13
        >>> nameOctaveCount = a.pitchAttributeCount('nameWithOctave')
        >>> for n in sorted(list(nameOctaveCount.keys())):
        ...     print ("%3s: %2d" % (n, nameOctaveCount[n]))
         A2:  2
         A3:  5
         A4: 10
         B2:  3
         B3:  4
         B4:  7
         C3:  2
         C5:  1
        D#3:  1
        D#4:  2
         D3:  9
         D4: 14
         D5:  2
         E2:  1
         E3:  4
         E4:  9
        F#3: 13
        F#4:  2
         G2:  1
         G3: 10
         G4:  2
        '''
        post = {}
        for p in self.pitches:
            k = getattr(p, pitchAttr)
            if k not in post:
                post[k] = 0
            post[k] += 1
        return post


    def attributeCount(self, classFilterList, attrName='quarterLength'):
        '''
        Return a dictionary of attribute usage for one or more
        classes provided in a the `classFilterList` list and having
        the attribute specified by `attrName`.

        >>> from music21 import corpus
        >>> a = corpus.parse('bach/bwv324.xml')
        >>> a.parts[0].flat.attributeCount(note.Note, 'quarterLength')
        {1.0: 12, 2.0: 11, 4.0: 2}
        '''
        post = {}
        for e in self.getElementsByClass(classFilterList):
            if hasattr(e, attrName):
                k = getattr(e, attrName)
                if k not in post:
                    post[k] = 0
                post[k] += 1
        return post


    #---------------------------------------------------------------------------
    # interval routines

    def findConsecutiveNotes(self, skipRests=False, skipChords=False,
        skipUnisons=False, skipOctaves=False,
        skipGaps=False, getOverlaps=False, noNone=False, **keywords):
        r'''
        Returns a list of consecutive *pitched* Notes in a Stream.

        A single "None" is placed in the list
        at any point there is a discontinuity (such as if there is a
        rest between two pitches), unless the `noNone` parameter is True.

        How to determine consecutive pitches is a little tricky and there are many options:

            The `skipUnisons` parameter uses the midi-note value (.ps) to determine unisons,
            so enharmonic transitions (F# -> Gb) are
            also skipped if `skipUnisons` is true.  We believe that this is the most common usage.
            However, because
            of this, you cannot completely be sure that the
            x.findConsecutiveNotes() - x.findConsecutiveNotes(skipUnisons=True)
            will give you the number of P1s in the piece, because there could be
            d2's in there as well.

        See Test.testFindConsecutiveNotes() for usage details.


        OMIT_FROM_DOCS

        N.B. for chords, currently, only the first pitch is tested for unison.
        this is a bug TODO: FIX

        (\*\*kwargs is there so that other methods that pass along dicts to
        findConsecutiveNotes don't have to remove
        their own args; this method is used in melodicIntervals.)
        '''
        sortedSelf = self.sorted
        returnList = []
        lastStart = 0.0
        lastEnd = 0.0
        lastWasNone = False
        lastPitch = None
        if skipOctaves is True:
            skipUnisons = True  # implied

        # need to look for voices in self and deal with each one at a time
        if self.hasVoices:
            vGroups = []
            for v in self.voices:
                vGroups.append(v.flat)
            vGroups.append(sortedSelf)
        else:
            vGroups = (sortedSelf.flat,)

        for v in vGroups:
            for e in v.elements:
                if (lastWasNone is False and skipGaps is False and
                    e.offset > lastEnd):
                    if not noNone:
                        returnList.append(None)
                        lastWasNone = True
                if hasattr(e, "pitch"):
                    #if (skipUnisons is False or isinstance(lastPitch, list) or
                    if (skipUnisons is False or isinstance(lastPitch, tuple) or
                        lastPitch is None or
                        e.pitch.pitchClass != lastPitch.pitchClass or
                        (skipOctaves is False and e.pitch.ps != lastPitch.ps)):
                        if getOverlaps is True or e.offset >= lastEnd:
                            if e.offset >= lastEnd:  # is not an overlap...
                                lastStart = e.offset
                                if hasattr(e, "duration"):
                                    lastEnd = opFrac(lastStart + e.duration.quarterLength)
                                else:
                                    lastEnd = lastStart
                                lastWasNone = False
                                lastPitch = e.pitch
                            else:  # do not update anything for overlaps
                                pass
                            returnList.append(e)
                # if we have a chord
                elif hasattr(e, "pitches"):
                    if skipChords is True:
                        if lastWasNone is False:
                            if not noNone:
                                returnList.append(None)
                                lastWasNone = True
                                lastPitch = None
                    # if we have a chord
                    else:
                        #environLocal.printDebug(['e.pitches', e, e.pitches])
                        #environLocal.printDebug(['lastPitch', lastPitch])

                        if (skipUnisons is True and isinstance(lastPitch, list) and
                            e.pitches[0].ps == lastPitch[0].ps):
                            pass
                        else:
                            if getOverlaps is True or e.offset >= lastEnd:
                                if e.offset >= lastEnd:  # is not an overlap...
                                    lastStart = e.offset
                                    if hasattr(e, "duration"):
                                        lastEnd = opFrac(lastStart + e.duration.quarterLength)
                                    else:
                                        lastEnd = lastStart
                                    # this is the case where the last pitch is a
                                    # a list
                                    lastPitch = e.pitches
                                    lastWasNone = False
                                else:  # do not update anything for overlaps
                                    pass
                                returnList.append(e)

                elif (skipRests is False and isinstance(e, note.Rest) and
                    lastWasNone is False):
                    if noNone is False:
                        returnList.append(None)
                        lastWasNone = True
                        lastPitch = None
                elif skipRests is True and isinstance(e, note.Rest):
                    lastEnd = opFrac(e.offset + e.duration.quarterLength)

        if lastWasNone is True:
            returnList.pop() # removes the last-added element
        return returnList

    def melodicIntervals(self, *skipArgs, **skipKeywords):
        '''
        Returns a Stream of :class:`~music21.interval.Interval` objects
        between Notes (and by default, Chords) that follow each other in a stream.
        the offset of the Interval is the offset of the beginning of the interval
        (if two notes are adjacent, then this offset is equal to the offset of
        the second note, but if skipRests is set to True or there is a gap
        in the Stream, then these two numbers
        will be different).

        See :meth:`~music21.stream.Stream.findConsecutiveNotes` in this class for
        a discussion of what is meant by default for "consecutive notes", and
        which keywords such as skipChords, skipRests, skipUnisons, etc. can be
        used to change that behavior.

        The interval between a Note and a Chord (or between two chords) is the
        interval to the first pitch of the Chord (pitches[0]) which is usually the lowest.
        For more complex interval calculations,
        run :meth:`~music21.stream.Stream.findConsecutiveNotes` and then calculate
        your own intervals directly.

        Returns an empty Stream if there are not at least two elements found by
        findConsecutiveNotes.



        >>> s1 = converter.parse("tinynotation: 3/4 c4 d' r b b'", makeNotation=False)
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/streamMelodicIntervals1.*
            :width: 246

        >>> intervalStream1 = s1.melodicIntervals()
        >>> intervalStream1.show('text')
        {1.0} <music21.interval.Interval M9>
        {4.0} <music21.interval.Interval P8>

        >>> M9 = intervalStream1[0]
        >>> M9.noteStart.nameWithOctave, M9.noteEnd.nameWithOctave
        ('C4', 'D5')

        Using the skip attributes from :meth:`~music21.stream.Stream.findConsecutiveNotes`,
        we can alter which intervals are reported:

        >>> intervalStream2 = s1.melodicIntervals(skipRests=True, skipOctaves=True)
        >>> intervalStream2.show('text')
        {1.0} <music21.interval.Interval M9>
        {2.0} <music21.interval.Interval m-3>

        >>> m3 = intervalStream2[1]
        >>> m3.directedNiceName
        'Descending Minor Third'
        '''
        returnList = self.findConsecutiveNotes(**skipKeywords)
        if len(returnList) < 2:
            return self.cloneEmpty(derivationMethod='melodicIntervals')

        returnStream = self.cloneEmpty(derivationMethod='melodicIntervals')
        for i in range(len(returnList) - 1):
            firstNote = returnList[i]
            secondNote = returnList[i+1]
            firstPitch = None
            secondPitch = None
            if firstNote is not None and secondNote is not None:
                startIsChord = False
                endIsChord = False
                if hasattr(firstNote, "pitch") and firstNote.pitch is not None:
                    firstPitch = firstNote.pitch
                elif hasattr(firstNote, "pitches") and firstNote.pitches:
                    firstPitch = firstNote.pitches[0]
                    startIsChord = True
                if hasattr(secondNote, "pitch") and secondNote.pitch is not None:
                    secondPitch = secondNote.pitch
                elif hasattr(secondNote, "pitches") and secondNote.pitches:
                    secondPitch = secondNote.pitches[0]
                    endIsChord = True
                if firstPitch is not None and secondPitch is not None:
                    returnInterval = interval.notesToInterval(firstPitch,
                                                              secondPitch)
                    if startIsChord is False:
                        returnInterval.noteStart = firstNote
                    if endIsChord is False:
                        returnInterval.noteEnd = secondNote
                    returnInterval.offset = opFrac(firstNote.offset +
                                     firstNote.duration.quarterLength)
                    returnInterval.duration = duration.Duration(opFrac(
                        secondNote.offset - returnInterval.offset))
                    returnStream.insert(returnInterval)

        return returnStream

    #---------------------------------------------------------------------------
    def _getDurSpan(self, flatStream):
        '''
        Given a flat stream, create a list of the start and end
        times (as a tuple pair) of all elements in the Stream.


        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note(type='half'), [0, 1, 2, 3, 4])
        >>> a._getDurSpan(a.flat)
        [(0.0, 2.0), (1.0, 3.0), (2.0, 4.0), (3.0, 5.0), (4.0, 6.0)]
        '''
        post = []
        for e in flatStream:
            if e.duration is None:
                durSpan = (e.offset, e.offset)
            else:
                dur = e.duration.quarterLength
                durSpan = (e.offset, opFrac(e.offset+dur))
            post.append(durSpan)
        # assume this is already sorted
        # index found here will be the same as elementsSorted
        return post


    def _durSpanOverlap(self, a, b, includeEndBoundary=False):
        '''
        Compare two durSpans and find overlaps; optionally,
        include coincident boundaries. a and b are sorted to permit any ordering.

        If an element ends at 3.0 and another starts at 3.0, this may or may not
        be considered an overlap. The includeCoincidentEnds parameter determines
        this behaviour, where ending and starting 3.0 being a type of overlap
        is set by the includeEndBoundary being True.


        >>> a = stream.Stream()
        >>> a._durSpanOverlap([0, 10], [11, 12], False)
        False
        >>> a._durSpanOverlap([11, 12], [0, 10], False)
        False
        >>> a._durSpanOverlap([0, 3], [3, 6], False)
        False
        >>> a._durSpanOverlap([0, 3], [3, 6], True)
        True
        '''

        durSpans = [a, b]
        # sorting will ensure that leading numbers are ordered from low to high
        durSpans.sort()
        found = False

        if includeEndBoundary:
            # if the start of b is before the end of a
            #if durSpans[1][0] <= durSpans[0][1]:
            if durSpans[1][0] <= durSpans[0][1]:
                found = True
        else: # do not include coincident boundaries
            #if durSpans[1][0] < durSpans[0][1]:
            if durSpans[1][0] < durSpans[0][1]:
                found = True
        return found


    def _findLayering(self, flatStream, includeDurationless=True,
                   includeEndBoundary=False):
        '''
        Find any elements in an elementsSorted list that have simultaneities
        or durations that cause overlaps.

        Returns two lists. Each list contains a list for each element in
        elementsSorted. If that elements has overlaps or simultaneities,
        all index values that match are included in that list.

        See testOverlaps, in unit tests, for examples.


        '''
        flatStream = flatStream.sorted
        # these may not be sorted
        durSpanSorted = self._getDurSpan(flatStream)

        # create a list with an entry for each element
        # in each entry, provide indices of all other elements that overalap
        overlapMap = [[] for dummy in range(len(durSpanSorted))]
        # create a list of keys for events that start at the same time
        simultaneityMap = [[] for dummy in range(len(durSpanSorted))]

        for i in range(len(durSpanSorted)):
            src = durSpanSorted[i]
            # second entry is duration
            if not includeDurationless and flatStream[i].duration is None:
                continue
            # compare to all past and following durations
            for j in range(len(durSpanSorted)):
                if j == i: # index numbers
                    continue # do not compare to self
                dst = durSpanSorted[j]
                # print(src, dst, self._durSpanOverlap(src, dst, includeEndBoundary))

                # if start times are the same (rational comparison; no fudge needed)
                if src[0] == dst[0]:
                    simultaneityMap[i].append(j)
                # this function uses common.py comparions methods
                if self._durSpanOverlap(src, dst, includeEndBoundary):
                    overlapMap[i].append(j)
        return simultaneityMap, overlapMap



    def _consolidateLayering(self, flatStream, layeringMap):
        '''
        Given elementsSorted and a map of equal length with lists of
        index values that meet a given condition (overlap or simultaneities),
        organize into a dictionary by the relevant or first offset
        '''
        flatStream = flatStream.sorted

        if len(layeringMap) != len(flatStream):
            raise StreamException('layeringMap must be the same length as flatStream')

        post = {}
        for i in range(len(layeringMap)):
            # print('examining i:', i)
            indices = layeringMap[i]
            if len(indices) > 0:
                srcOffset = flatStream[i].offset
                srcElementObj = flatStream[i]
                dstOffset = None
                # print('found indices', indices)
                # check indices
                for j in indices: # indices of other elements tt overlap
                    elementObj = flatStream[j]
                    # check if this object has been stored anywhere yet
                    # if so, use the offset of where it was stored to
                    # to store the src element below
                    store = True
                    for k in post:
                        # this comparison needs to be based on object id, not
                        # matching equality
                        if id(elementObj) in [id(e) for e in post[k]]:
                        # if elementObj in post[key]:
                            store = False
                            dstOffset = k
                            break
                    if dstOffset is None:
                        dstOffset = srcOffset
                    if store:
                        # print('storing offset', dstOffset)
                        if dstOffset not in post:
                            post[dstOffset] = [] # create dictionary entry
                        post[dstOffset].append(elementObj)

                # check if this object has been stored anywhere yet
                store = True
                for k in post:
                    if id(srcElementObj) in [id(e) for e in post[k]]:
                    #if srcElementObj in post[key]:
                        store = False
                        break
                # dst offset may have been set when looking at indices
                if store:
                    if dstOffset is None:
                        dstOffset = srcOffset
                    if dstOffset not in post:
                        post[dstOffset] = [] # create dictionary entry
                    # print('storing offset', dstOffset)
                    post[dstOffset].append(srcElementObj)
        #print(post)
        return post



    def findGaps(self):
        '''
        Returns either (1) a Stream containing Elements
        (that wrap the None object) whose offsets and durations
        are the length of gaps in the Stream
        or (2) None if there are no gaps.

        N.B. there may be gaps in the flattened representation of the stream
        but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless
        '''
        if 'GapStream' in self._cache and self._cache["GapStream"] is not None:
            return self._cache["GapStream"]

        sortedElements = self.sorted.elements
        gapStream = self.cloneEmpty(derivationMethod='findGaps')
        highestCurrentEndTime = 0.0
        for e in sortedElements:
            if e.offset > highestCurrentEndTime:
                gapElement = base.Music21Object() #ElementWrapper(obj=None)
                gapQuarterLength = opFrac(e.offset - highestCurrentEndTime)
                gapElement.duration = duration.Duration()
                gapElement.duration.quarterLength = gapQuarterLength
                gapStream.insert(highestCurrentEndTime, gapElement)
            if hasattr(e, 'duration') and e.duration is not None:
                eDur = e.duration.quarterLength
            else:
                eDur = 0.
            highestCurrentEndTime = opFrac(max(highestCurrentEndTime, e.offset + eDur))

        if len(gapStream) == 0:
            return None
        else:
            self._cache["GapStream"] = gapStream
            return gapStream

    def _getIsGapless(self):
        if 'isGapless' in self._cache and self._cache["isGapless"] is not None:
            return self._cache["isGapless"]
        else:
            if self.findGaps() is None:
                self._cache["Gapless"] = True
                return True
            else:
                self._cache["Gapless"] = False
                return False

    isGapless = property(_getIsGapless)

    def getSimultaneous(self, includeDurationless=True):
        '''Find and return any elements that start at the same time.


        >>> stream1 = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 0
        ...     stream1.insert(n)
        ...
        >>> b = stream1.getSimultaneous()
        >>> len(b[0]) == 4
        True
        >>> stream2 = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     stream2.insert(n)
        ...
        >>> d = stream2.getSimultaneous()
        >>> len(d) == 0
        True
        '''
#        checkOverlap = False
        elementsSorted = self.flat
        simultaneityMap, unused_overlapMap = self._findLayering(elementsSorted,
                                                                includeDurationless)

        return self._consolidateLayering(elementsSorted, simultaneityMap)


    def getOverlaps(self, includeDurationless=True,
                     includeEndBoundary=False):
        '''
        Find any elements that overlap. Overlaping might include elements
        that have no duration but that are simultaneous.
        Whether elements with None durations are included is determined by
        includeDurationless.

        This method returns a dictionary, where keys
        are the start time of the first overlap and
        value are a list of all objects included in
        that overlap group.

        This example demonstrates end-joing overlaps: there are four
        quarter notes each following each other. Whether or not
        these count as overlaps
        is determined by the includeEndBoundary parameter.


        >>> a = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('quarter')
        ...     n.offset = x * 1
        ...     a.insert(n)
        ...
        >>> d = a.getOverlaps(True, False)
        >>> len(d)
        0
        >>> d = a.getOverlaps(True, True) # including coincident boundaries
        >>> len(d)
        1
        >>> len(d[0])
        4
        >>> a = stream.Stream()
        >>> for x in [0,0,0,0,13,13,13]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('half')
        ...     n.offset = x
        ...     a.insert(n)
        ...
        >>> d = a.getOverlaps()
        >>> len(d[0])
        4
        >>> len(d[13])
        3
        >>> a = stream.Stream()
        >>> for x in [0,0,0,0,3,3,3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     n.offset = x
        ...     a.insert(n)
        ...
        >>> # default is to not include coincident boundaries
        >>> d = a.getOverlaps()
        >>> len(d[0])
        7

        '''
        elementsSorted = self.flat
        unused_simultaneityMap, overlapMap = self._findLayering(elementsSorted,
                                                                includeDurationless, includeEndBoundary)
        #environLocal.printDebug(['simultaneityMap map', simultaneityMap])
        #environLocal.printDebug(['overlapMap', overlapMap])

        return self._consolidateLayering(elementsSorted, overlapMap)



    def isSequence(self, includeDurationless=True,
                        includeEndBoundary=False):
        '''A stream is a sequence if it has no overlaps.


        >>> a = stream.Stream()
        >>> for x in [0,0,0,0,3,3,3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     n.offset = x * 1
        ...     a.insert(n)
        ...
        >>> a.isSequence()
        False

        OMIT_FROM_DOCS
        TODO: check that co-incident boundaries are properly handled

        '''
        elementsSorted = self.flat
        unused_simultaneityMap, overlapMap = self._findLayering(elementsSorted,
                                                                includeDurationless, includeEndBoundary)
        post = True
        for indexList in overlapMap:
            if indexList:
                post = False
                break
        return post


    #---------------------------------------------------------------------------
    # routines for dealing with relationships to other streams.
    # Formerly in twoStreams.py

    def simultaneousAttacks(self, stream2):
        '''
        returns an ordered list of offsets where elements are started (attacked)
        at the same time in both self and stream2.

        In this example, we create one stream of Qtr, Half, Qtr, and one of Half, Qtr, Qtr.
        There are simultaneous attacks at offset 0.0 (the beginning) and at offset 3.0,
        but not at 1.0 or 2.0:


        >>> st1 = stream.Stream()
        >>> st2 = stream.Stream()
        >>> st1.append([note.Note(type='quarter'), note.Note(type='half'), note.Note(type='quarter')])
        >>> st2.append([note.Note(type='half'), note.Note(type='quarter'), note.Note(type='quarter')])
        >>> print(st1.simultaneousAttacks(st2))
        [0.0, 3.0]
        '''
        stream1Offsets = self.groupElementsByOffset()
        stream2Offsets = stream2.groupElementsByOffset()

        returnKey = {}

        for thisList in stream1Offsets:
            thisOffset = self.elementOffset(thisList[0])
            returnKey[thisOffset] = 1

        for thatList in stream2Offsets:
            thatOffset = thatList[0].getOffsetBySite(stream2)
            if thatOffset in returnKey:
                returnKey[thatOffset] += 1

        returnList = []
        for foundOffset in sorted(returnKey):
            if returnKey[foundOffset] >= 2:
                returnList.append(foundOffset)
        return returnList

    def attachIntervalsBetweenStreams(self, cmpStream):
        '''
        For each element in self, creates an interval.Interval object in the element's
        editorial that is the interval between it and the element in cmpStream that
        is sounding at the moment the element in srcStream is attacked.

        Remember that if you are comparing two streams with measures, etc.,
        you'll need to flatten each stream as follows:

        >>> #_DOCS_SHOW stream1.flat.attachIntervalsBetweenStreams(stream2.flat)

        Example usage:


        >>> s1 = converter.parse('tinynotation: 7/4 C4 d8 e f# g A2 d2', makeNotation=False)
        >>> s2 = converter.parse('tinynotation: 7/4 g4 e8 d c4   a2 r2', makeNotation=False)
        >>> s1.attachIntervalsBetweenStreams(s2)
        >>> for n in s1.notes:
        ...     if n.editorial.harmonicInterval is None: print("None") # if other voice had a rest...
        ...     else: print(n.editorial.harmonicInterval.directedName)
        P12
        M2
        M-2
        A-4
        P-5
        P8
        None
        '''
        for n in self.notes:
            # get simultaneous elements form other stream
            simultEls = cmpStream.iter.getElementsByOffset( self.elementOffset(n),
                mustBeginInSpan=False, mustFinishInSpan=False)
            if simultEls:
                for simultNote in simultEls.notes:
                    interval1 = None
                    try:
                        interval1 = interval.notesToInterval(n, simultNote)
                        n.editorial.harmonicInterval = interval1
                    except exceptions21.Music21Exception:
                        pass
                    if interval1 is not None:
                        break # inner loop

    def attachMelodicIntervals(self):
        '''For each element in self, creates an interval.Interval object in the element's
        editorial that is the interval between it and the previous element in the stream. Thus,
        the first element will have a value of None.

        >>> s1 = converter.parse('tinyNotation: 7/4 C4 d8 e f# g A2 d2', makeNotation=False)
        >>> s1.attachMelodicIntervals()
        >>> for n in s1.notes:
        ...     if n.editorial.melodicInterval is None: print("None")
        ...     else: print(n.editorial.melodicInterval.directedName)
        None
        M9
        M2
        M2
        m2
        m-7
        P4

        OMIT_FROM_DOCS
        >>> s = stream.Stream()
        >>> s.append(note.Note('C'))
        >>> s.append(note.Note('D'))
        >>> s.append(note.Rest(quarterLength = 4.0))
        >>> s.append(note.Note('D'))
        >>> s.attachMelodicIntervals()
        >>> for n in s.notes:
        ...     if n.editorial.melodicInterval is None: print("None") # if other voice had a rest...
        ...     else: print(n.editorial.melodicInterval.directedName)
        None
        M2
        None
        '''

        notes = self.notes
        currentObject = notes[0]
        previousObject = None
        while currentObject is not None:
            if previousObject is not None and \
                  "Note" in currentObject.classes and \
                  "Note" in previousObject.classes:
                currentObject.editorial.melodicInterval = interval.notesToInterval(previousObject, currentObject)
            previousObject = currentObject
            currentObject = currentObject.next()


    def playingWhenAttacked(self, el, elStream=None):
        '''
        Given an element (from another Stream) returns the single element
        in this Stream that is sounding while the given element starts.

        If there are multiple elements sounding at the moment it is
        attacked, the method returns the first element of the same class
        as this element, if any. If no element
        is of the same class, then the first element encountered is
        returned. For more complex usages, use allPlayingWhileSounding.

        Returns None if no elements fit the bill.

        The optional elStream is the stream in which el is found.
        If provided, el's offset
        in that Stream is used.  Otherwise, the current offset in
        el is used.  It is just
        in case you are paranoid that el.offset might not be what
        you want, because of some fancy manipulation of
        el.activeSite

        >>> n1 = note.Note("G#")
        >>> n2 = note.Note("D#")
        >>> s1 = stream.Stream()
        >>> s1.insert(20.0, n1)
        >>> s1.insert(21.0, n2)
        >>> n3 = note.Note("C#")
        >>> s2 = stream.Stream()
        >>> s2.insert(20.0, n3)
        >>> s1.playingWhenAttacked(n3).name
        'G#'
        >>> n3.setOffsetBySite(s2, 20.5)
        >>> s1.playingWhenAttacked(n3).name
        'G#'
        >>> n3.setOffsetBySite(s2, 21.0)
        >>> n3.offset
        21.0
        >>> s1.playingWhenAttacked(n3).name
        'D#'

        Optionally, specify the site to get the offset from:

        >>> n3.setOffsetBySite(None, 100)
        >>> n3.activeSite = None
        >>> s1.playingWhenAttacked(n3)
        <BLANKLINE>
        >>> s1.playingWhenAttacked(n3, s2).name
        'D#'
        '''
        if elStream is not None: # bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset

        otherElements = self.getElementsByOffset(elOffset, mustBeginInSpan=False)
        if len(otherElements) == 0:
            return None
        elif len(otherElements) == 1:
            return otherElements[0]
        else:
            for thisEl in otherElements:
                if isinstance(thisEl, el.__class__):
                    return thisEl
            return otherElements[0]

    def allPlayingWhileSounding(self, el, elStream=None,
                                requireClass=False):
        '''
        Returns a new Stream of elements in this stream that sound
        at the same time as `el`, an element presumably in another Stream.

        The offset of this new Stream is set to el's offset, while the
        offset of elements within the Stream are adjusted relative to
        their position with respect to the start of el.  Thus, a note
        that is sounding already when el begins would have a negative
        offset.  The duration of otherStream is forced
        to be the length of el -- thus a note sustained after el ends
        may have a release time beyond that of the duration of the Stream.

        As above, elStream is an optional Stream to look up el's offset in.

        The method always returns a Stream, but it might be an empty Stream.

        OMIT_FROM_DOCS
        TODO: write: requireClass:
        Takes as an optional parameter "requireClass".  If this parameter
        is boolean True then only elements
        of the same class as el are added to the new Stream.  If requireClass
        is list, it is used like
        classList in elsewhere in stream to provide a list of classes that the
        el must be a part of.


        '''
        if requireClass is not False:
            raise Exception("requireClass is not implemented")

        if elStream is not None: # bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset
        elEnd = elOffset + el.quarterLength

        if elEnd != elOffset: # i.e. not zero length
            otherElements = self.getElementsByOffset(elOffset, elEnd, 
                                                     mustBeginInSpan=False, 
                                                     includeEndBoundary=False, 
                                                     includeElementsThatEndAtStart=False)
        else:
            otherElements = self.getElementsByOffset(elOffset, mustBeginInSpan=False)

        otherElements.offset = elOffset
        otherElements.quarterLength = el.quarterLength
        for thisEl in otherElements:
            thisEl.offset = thisEl.offset - elOffset

        return otherElements

#     def trimPlayingWhileSounding(self, el, elStream=None,
#                                requireClass=False, padStream=False):
#         '''
#         Returns a Stream of deepcopies of elements in otherStream that sound at the same time as`el. but
#         with any element that was sounding when el. begins trimmed to begin with el. and any element
#         sounding when el ends trimmed to end with el.
# 
#         if padStream is set to true then empty space at the beginning and end is filled with a generic
#         Music21Object, so that no matter what otherStream is the same length as el.
# 
#         Otherwise is the same as allPlayingWhileSounding -- but because these elements are deepcopies,
#         the difference might bite you if you're not careful.
# 
#         Note that you can make el an empty stream of offset X and duration Y to extract exactly
#         that much information from otherStream.
# 
#         OMIT_FROM_DOCS
#         TODO: write: ALL. requireClass, padStream
# 
#         always returns a Stream, but might be an empty Stream
#         '''
#         if requireClass is not False:
#             raise StreamException("requireClass is not implemented")
#         if padStream is not False:
#             raise StreamException("padStream is not implemented")
# 
#         raise StreamException("Not written yet")
# 
#         if elStream is not None: # bit of safety
#             elOffset = el.getOffsetBySite(elStream)
#         else:
#             elOffset = el.offset
# 
#         otherElements = self.getElementsByOffset(elOffset, elOffset + el.duration.quarterLength, mustBeginInSpan=False)
# 
#         otherElements.offset = elOffset
#         otherElements.quarterLength = el.duration.quarterLength
#         for thisEl in otherElements:
#             thisEl.offset = thisEl.offset - elOffset
# 
#         return otherElements


    #---------------------------------------------------------------------------
    # voice processing routines
    def makeVoices(self, inPlace=True, fillGaps=True):
        '''
        If this Stream has overlapping Notes or Chords, this method will isolate
        all overlaps in unique Voices, and place those Voices in the Stream.


        >>> s = stream.Stream()
        >>> s.insert(0, note.Note('C4', quarterLength=4))
        >>> s.repeatInsert(note.Note('b-4', quarterLength=.5), [x*.5 for x in list(range(0,8))])
        >>> s.makeVoices(inPlace=True)
        >>> len(s.voices)
        2
        >>> [n.pitch for n in s.voices[0].notes]
        [<music21.pitch.Pitch C4>]
        >>> [str(n.pitch) for n in s.voices[1].notes]
        ['B-4', 'B-4', 'B-4', 'B-4', 'B-4', 'B-4', 'B-4', 'B-4']

        TODO: by default inPlace should be False
        '''
        # this method may not always
        # produce the optimal voice assignment based on context (register
        # chord formation, etc
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self
        # must be sorted
        if not returnObj.isSorted:
            returnObj.sort()
        olDict = returnObj.notes.getOverlaps(
                 includeDurationless=False, includeEndBoundary=False)
        #environLocal.printDebug(['makeVoices(): olDict', olDict])
        # find the max necessary voices by finding the max number
        # of elements in each group; these may not all be necessary
        maxVoiceCount = 1
        for group in olDict.values():
            if len(group) > maxVoiceCount:
                maxVoiceCount = len(group)
        if maxVoiceCount == 1: # nothing to do here
            if not inPlace:
                return returnObj
            return None

        # store all voices in a list
        voices = []
        for dummy in range(0, maxVoiceCount):
            voices.append(Voice()) # add voice classes

        # iterate through all elements; if not in an overlap, place in
        # voice 1, otherwise, distribute
        for e in returnObj.notes:
            o = e.getOffsetBySite(returnObj)
            # cannot match here by offset, as olDict keys are representative
            # of the first overlapped offset, not all contained offsets
            #if o not in olDict: # place in a first voices
            #    voices[0].insert(o, e)
            # find a voice to place in
            # as elements are sorted, can use the highest time
            #else:
            for v in voices:
                if v.highestTime <= o:
                    v.insert(o, e)
                    break
            # remove from source
            returnObj.remove(e)
        # remove any unused voices (possible if overlap group has sus)
        for v in voices:
            if v: # skip empty voices
                if fillGaps:
                    returnObj.makeRests(fillGaps=True, inPlace=True)
                returnObj.insert(0, v)
        # remove rests in returnObj
        returnObj.removeByClass('Rest')
        # elements changed will already have been called
        if not inPlace:
            return returnObj
        return None

    def internalize(self, container=None,
                    classFilterList=('GeneralNote',)):
        '''
        Gather all notes and related classes of this Stream
        and place inside a new container (like a Voice) in this Stream.
        '''
        if container is None:
            container = Voice
        dst = container()
        for e in self.getElementsByClass(classFilterList):
            dst.insert( self.elementOffset(e), e)
            self.remove(e)
        self.insert(0, dst)

#    def externalize(self):
#        '''
#        Assuming there is a container in this Stream
#        (like a Voice), remove the container and place
#        all contents in the Stream.
#        '''
#        pass

    def voicesToParts(self):
        '''
        If this Stream defines one or more voices,
        extract each into a Part, returning a Score.

        If this Stream has no voices, return the Stream as a Part within a Score.
        '''
        s = Score()
        #s.metadata = self.metadata

        # if this is a Score, call this recursively on each Part, then
        # add all parts to one Score
        if self.hasPartLikeStreams():
            for p in self.parts:
                sSub = p.voicesToParts()
                for pSub in sSub:
                    s.insert(0, pSub)
            return s

        # need to find maximum voice count
        partCount = 0
        #partId = []
        if self.hasMeasures():
            for m in self.getElementsByClass('Measure'):
                vCount = len(m.voices)
                if vCount > partCount:
                    partCount = vCount
        elif self.hasVoices():
            partCount = len(self.voices)
        else: # if no measure or voices, get one part
            partCount = 1

        #environLocal.printDebug(['voicesToParts(): got partCount', partCount])

        # create parts, naming ids by voice id?
        for dummy in range(partCount):
            p = Part()
            s.insert(0, p)

        if self.hasMeasures():
            for m in self.getElementsByClass('Measure'):
                if m.hasVoices():
                    mActive = Measure()
                    mActive.mergeAttributes(m) # get groups, optional id
                    # merge everything except Voices; this will get
                    # clefs
                    mActive.mergeElements(m, classFilterList=('Bar', 'TimeSignature', 'Clef', 'KeySignature'))
                    for vIndex, v in enumerate(m.voices):
                        # make an independent copy
                        mNew = copy.deepcopy(mActive)
                        # merge all elements from the voice
                        mNew.mergeElements(v)
                        # insert in the appropriate part
                        s[vIndex].insert( self.elementOffset(m), mNew)
                # if a measure does not have voices, simply populate
                # with elements and append
                else:
                    mNew = Measure()
                    mNew.mergeAttributes(m) # get groups, optional id
                    # get all elements
                    mNew.mergeElements(m)
                    # always place in top-part
                    s[0].insert( self.elementOffset(m), mNew)
        # if no measures but voices, contents of each voice go into the part
        elif self.hasVoices():
            for vIndex, v in enumerate(self.voices):
                s[vIndex].mergeElements(v)
        # if just a Stream of elements, add to a part
        else:
            s[0].mergeElements(self)

        # there is no way to assure proper clef information, so using
        # best clef here is desirable.
        for p in s.parts:
            # only add clef if measures are defined; otherwise, assume
            # best clef will be assigned later
            if p.hasMeasures():
                # place in first measure
                p.getElementsByClass('Measure')[0].clef = p.flat.bestClef()
        return s

    def explode(self):
        '''
        Create a multi-part extraction from a single polyphonic Part.

        Currently just runs :meth:`~music21.stream.Stream.voicesToParts`
        but that will change as part explosion develops, and this
        method will use our best available quick method for part
        extraction.
        '''
        return self.voicesToParts()

    def flattenUnnecessaryVoices(self, force=False, inPlace=True):
        '''
        If this Stream defines one or more internal voices, do the following:

        * If there is more than one voice, and a voice has no elements,
          remove that voice.
        * If there is only one voice left that has elements, place those
          elements in the parent Stream.
        * If `force` is True, even if there is more than one Voice left,
          all voices will be flattened.

        TODO: by default inPlace should be False
        '''
        if len(self.voices) == 0:
            return None # do not make copy; return immediately

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # collect voices for removal and for flattening
        remove = []
        flatten = []
        for v in returnObj.voices:
            if len(v) == 0: # might add other criteria
                remove.append(v)
            else:
                flatten.append(v)
        for v in remove:
            returnObj.remove(v)

        if len(flatten) == 1 or force: # always flatten 1
            for v in flatten: # usually one unless force
                # get offset of voice in returnObj
                shiftOffset = v.getOffsetBySite(returnObj)
                for e in v.elements:
                    # insert shift + offset w/ voice
                    returnObj._insertCore(shiftOffset + e.getOffsetBySite(v), e)
                returnObj.remove(v)

        returnObj.elementsChanged()
        if not inPlace:
            return returnObj
        else:
            return None

    #---------------------------------------------------------------------------
    # Lyric control

    def lyrics(self, ignoreBarlines=True, recurse=False, skipTies=False):
        '''
        Returns a dict of lists of lyric objects (with the keys being
        the lyric numbers) found in self. Each list will have an element for each
        note in the stream (which may be a note.Lyric() or None). By default, this method automatically
        recurses through measures, but not other container streams.


        >>> s = converter.parse("tinynotation: 4/4 a4 b c d     e f g a", makeNotation=False)
        >>> someLyrics = ['this', 'is', 'a', 'list', 'of', 'eight', 'lyric', 'words']
        >>> for n, lyric in zip(s.notes, someLyrics):
        ...     n.lyric = lyric


        >>> s.lyrics()
        {1: [<music21.note.Lyric number=1 syllabic=single text="this">, ..., <music21.note.Lyric number=1 syllabic=single text="words">]}

        >>> s.notes[3].lyric = None
        >>> s.lyrics()[1]
        [<music21.note.Lyric number=1 syllabic=single text="this">, ..., None, ..., <music21.note.Lyric number=1 syllabic=single text="words">]

        If ignoreBarlines is True, it will behave as if the elements in measures are all in a flattened stream (note that this is not stream.flat as it does not copy the elements)
        together without measure containers. This means that even if recurse is False, lyrics() will still essentially recurse through measures.

        >>> s.makeMeasures(inPlace=True)
        >>> s.lyrics()[1]
        [<music21.note.Lyric number=1 syllabic=single text="this">, ..., None, ..., <music21.note.Lyric number=1 syllabic=single text="words">]

        >>> list(s.lyrics(ignoreBarlines=False).keys())
        []

        If recurse is True, this method will recurse through all container streams and build a nested list structure mirroring the hierarchy of the stream.
        Note that if ignoreBarlines is True, measure structure will not be reflected in the hierarchy, although if ignoreBarlines is False, it will.

        Note that streams which do not contain any instance of a lyric number will not appear anywhere in the final list (not as a [] or otherwise).

        >>> p = stream.Part(s)
        >>> scr = stream.Score()
        >>> scr.append(p)

        >>> scr.lyrics(ignoreBarlines=False, recurse=True)[1]
        [[[<music21.note.Lyric number=1 syllabic=single text="this">, <..."is">, <..."a">, None], [<..."of">, <..."eight">, <..."lyric">, <..."words">]]]

        Notice that the measures are nested in the part which is nested in the score.

        >>> scr.lyrics(ignoreBarlines=True, recurse=True)[1]
        [[<music21.note.Lyric number=1 syllabic=single text="this">, <..."is">, <..."a">, None, <..."of">, <..."eight">, <..."lyric">, <..."words">]]

        Notice that this time, the measure structure is ignored.

        >>> list(scr.lyrics(ignoreBarlines=True, recurse=False).keys())
        []

        '''
        returnLists = {}
        numNotes = 0

        #---------------------

        def appendLyricsFromNote(n, returnLists, numNonesToAppend):
            if len(n.lyrics) == 0:
                for k in returnLists:
                    returnLists[k].append(None)
                return

            addLyricNums = []
            for l in n.lyrics:
                if not l.number in returnLists:
                    returnLists[l.number] = [ None for dummy in range(numNonesToAppend) ]
                returnLists[l.number].append(l)
                addLyricNums.append(l.number)
            for k in returnLists:
                if k not in addLyricNums:
                    returnLists[k].append(None)

        #------------------------
        # TODO: use new recurse
        for e in self:
            eclasses = e.classes
            if ignoreBarlines is True and "Measure" in eclasses:
                m = e
                for n in m.notes:
                    if skipTies is True:
                        if n.tie is None or n.tie.type == 'start':
                            appendLyricsFromNote(n, returnLists, numNotes)
                            numNotes +=1
                        else:
                            pass  #do nothing if end tie and skipTies is True
                    else:
                        appendLyricsFromNote(n, returnLists, numNotes)
                        numNotes +=1

            elif recurse is True and "Stream" in eclasses:
                s = e
                sublists = s.lyrics(ignoreBarlines=ignoreBarlines, recurse=True, skipTies=skipTies)
                for k in sublists:
                    if not k in returnLists:
                        returnLists[k] = []
                    returnLists[k].append(sublists[k])
            elif "NotRest" in eclasses: #elif "Stream" not in eclasses and hasattr(e, "lyrics"):
                n = e
                if skipTies is True:
                    if n.tie is None or n.tie.type == 'start':
                        appendLyricsFromNote(n, returnLists, numNotes)
                        numNotes +=1
                    else:
                        pass  #do nothing if end tie and skipTies is True
                else:
                    appendLyricsFromNote(n, returnLists, numNotes)
                    numNotes +=1
            else: # e is a stream (could be a measure if ignoreBarlines is False) and recurse is False
                pass  # do nothing

        return returnLists

    #---------------------------------------------------------------------------
    # Variant control

    def _getVariants(self):
        if 'variants' not in self._cache or self._cache['variants'] is None:
            self._cache['variants'] = self.getElementsByClass('Variant',
                                  returnStreamSubClass=False)
        return self._cache['variants']

    variants = property(_getVariants, doc='''
        Return a Stream containing all :class:`~music21.variant.Variant` objects in this Stream.

        # TODO -- make an iterator...

        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note('C4'), 8)
        >>> v1 = variant.Variant([note.Note('D#4'), note.Note('F#4')])
        >>> s.insert(3, v1)

        >>> varStream = s.variants
        >>> len(varStream)
        1
        >>> varStream[0] is v1
        True
        >>> len(s.variants[0])
        2

        Note that the D# and F# aren't found in the original Stream's pitches

        >>> [str(p) for p in s.pitches]
        ['C4', 'C4', 'C4', 'C4', 'C4', 'C4', 'C4', 'C4']
        ''')


#     def _getVariantBundle(self):
#         from music21 import variant # variant imports Stream
#
#         if ('variantBundle' not in self._cache or
#             self._cache['variantBundle'] is None):
#             # variants are only gotten for this level of the Stream
#             self._cache['variantBundle'] = variant.VariantBundle(self.variants)
#         return self._cache['variantBundle']
#
#     variantBundle = property(_getVariantBundle,
#         doc = '''A high-level object for Variant management. This is only a gettable property. Note that only Variants found on this Stream level (not the flat representation) are gathered in the bundle.
#         ''')
#

    #---- Variant Activation Methods

    def activateVariants(self, group=None, matchBySpan=True, inPlace=False):
        '''
        For any :class:`~music21.variant.Variant` objects defined in this Stream
        (or selected by matching the `group` parameter),
        replace elements defined in the Variant with those in the calling Stream.
        Elements replaced will be gathered into a new Variant
        given the group 'default'. If a variant is activated with
        .replacementDuration different from its length, the appropriate elements
        in the stream will have their offsets shifted, and measure numbering
        will be fixed. If matchBySpan is True, variants with lengthType
        'replacement' will replace all of the elements in the
        replacement region of comparable class. If matchBySpan is False,
        elements will be swapped in when a match is found between an element
        in the variant and an element in the replcement region of the string.

        >>> s = converter.parse("tinynotation: 4/4 d4 e4 f4 g4   a2 b-4 a4    g4 a8 g8 f4 e4    d2 a2                  d4 e4 f4 g4    a2 b-4 a4    g4 a8 b-8 c'4 c4    f1", makeNotation=False)
        >>> s.makeMeasures(inPlace=True)
        >>> v1stream = converter.parse("tinynotation: 4/4        a2. b-8 a8", makeNotation=False)
        >>> v2stream1 = converter.parse("tinynotation: 4/4                                      d4 f4 a2", makeNotation=False)
        >>> v2stream2 = converter.parse("tinynotation: 4/4                                                  d4 f4 AA2", makeNotation=False)

        >>> v1 = variant.Variant()
        >>> v1measure = stream.Measure()
        >>> v1.insert(0.0, v1measure)
        >>> for e in v1stream.notesAndRests:
        ...    v1measure.insert(e.offset, e)

        >>> v2 = variant.Variant()
        >>> v2measure1 = stream.Measure()
        >>> v2measure2 = stream.Measure()
        >>> v2.insert(0.0, v2measure1)
        >>> v2.insert(4.0, v2measure2)
        >>> for e in v2stream1.notesAndRests:
        ...    v2measure1.insert(e.offset, e)
        >>> for e in v2stream2.notesAndRests:
        ...    v2measure2.insert(e.offset, e)

        >>> v3 = variant.Variant()
        >>> v2.replacementDuration = 4.0
        >>> v3.replacementDuration = 4.0
        >>> v1.groups = ["docvariants"]
        >>> v2.groups = ["docvariants"]
        >>> v3.groups = ["docvariants"]

        >>> s.insert(4.0, v1)    # replacement variant
        >>> s.insert(12.0, v2)  # insertion variant (2 bars replace 1 bar)
        >>> s.insert(20.0, v3)  # deletion variant (0 bars replace 1 bar)

        >>> docvariant = s.activateVariants('docvariants')

        >>> #_DOCS_SHOW s.show()

        .. image:: images/stream_activateVariants1.*
            :width: 600

        >>> #_DOCS_SHOW docvariant.show()

        .. image:: images/stream_activateVariants2.*
            :width: 600

        >>> docvariant.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {3.0} <music21.note.Note B->
            {3.5} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {12.0} <music21.variant.Variant object of length 4.0>
        {12.0} <music21.stream.Measure 4 offset=12.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note F>
            {2.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 5 offset=16.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note F>
            {2.0} <music21.note.Note A>
        {20.0} <music21.stream.Measure 6 offset=20.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {24.0} <music21.variant.Variant object of length 4.0>
        {24.0} <music21.stream.Measure 7 offset=24.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note B->
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note C>
        {28.0} <music21.stream.Measure 8 offset=28.0>
            {0.0} <music21.note.Note F>
            {4.0} <music21.bar.Barline style=final>

        After a variant group has been activated, the regions it replaced are stored as variants with the group 'default'.
        It should be noted that this means .activateVariants should rarely if ever be used on a stream which is returned
        by activateVariants because the group information is lost.

        >>> defaultvariant = docvariant.activateVariants('default')
        >>> #_DOCS_SHOW defaultvariant.show()

        .. image:: images/stream_activateVariants3.*
            :width: 600

        >>> defaultvariant.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {12.0} <music21.variant.Variant object of length 8.0>
        {12.0} <music21.stream.Measure 4 offset=12.0>
            {0.0} <music21.note.Note D>
            {2.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 5 offset=16.0>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {20.0} <music21.variant.Variant object of length 0.0>
        {20.0} <music21.stream.Measure 6 offset=20.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {24.0} <music21.stream.Measure 7 offset=24.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note B->
            {2.0} <music21.note.Note C>
            {3.0} <music21.note.Note C>
        {28.0} <music21.stream.Measure 8 offset=28.0>
            {0.0} <music21.note.Note F>
            {4.0} <music21.bar.Barline style=final>
        '''
        if not inPlace: # make a copy if inPlace is False
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # Define Lists to cache variants
        elongationVariants = []
        deletionVariants = []

        #Loop through all variants, deal with replacement variants and save insertion and deletion for later.
        for v in returnObj.variants:
            if group is not None:
                if group not in v.groups:
                    continue # skip those that are not part of this group

            lengthType = v.lengthType

            #save insertions to perform last
            if lengthType == 'elongation':
                elongationVariants.append(v)
            #save deletions to perform after replacements
            elif lengthType == 'deletion':
                deletionVariants.append(v)
            #Deal with cases in which variant is the same length as what it replaces first.
            elif lengthType == 'replacement':
                returnObj._insertReplacementVariant(v, matchBySpan)

        #Now deal with deletions before insertion variants.
        deletedMeasures = [] #For keeping track of which measure numbers have been removed
        insertedMeasures = [] #For keeping track of where new measures without measure numbers have been inserted, will be a list of tuples (measureNumberPrior, [List, of, inserted, measures])

        deletedRegionsForRemoval = [] #For keeping track of the sections that are deleted (so the offset gap can be closed later)

        for v in deletionVariants:
            deletedRegion, vDeletedMeasures, vInsertedMeasuresTuple = returnObj._insertDeletionVariant(v, matchBySpan) #deletes and inserts
            deletedRegionsForRemoval.append(deletedRegion) #Saves the deleted region
            deletedMeasures.extend(vDeletedMeasures) # Saves the deleted measure numbers
            insertedMeasures.append(vInsertedMeasuresTuple) #saves the inserted numberless measures (this will be empty unless there are more bars in the variant than in the replacement region, which is unlikely for a deletion variant.

        returnObj._removeOrExpandGaps(deletedRegionsForRemoval, isRemove=True, inPlace=True) #Squeeze out the gaps that were saved.


        #Before we can deal with insertions, we have to expand the stream to make space.
        insertionRegionsForExpansion = [] #For saving the insertion regions
        for v in elongationVariants: #go through all elongation variants to find the insertion regions.
            lengthDifference = v.replacementDuration - v.containedHighestTime
            insertionStart = v.getOffsetBySite(returnObj) + v.replacementDuration
            insertionRegionsForExpansion.append((insertionStart, -1 * lengthDifference, [v]))   #Saves the information for each gap to be expanded

        returnObj._removeOrExpandGaps(insertionRegionsForExpansion, isRemove=False, inPlace=True)  #Expands the appropriate gaps in the stream.

        # Now deal with elongation variants properly
        for v in elongationVariants:
            vInsertedMeasuresTuple, vDeletedMeasures = returnObj._insertInsertionVariant(v, matchBySpan) #deletes and inserts
            insertedMeasures.append(vInsertedMeasuresTuple) # Saves the numberless inserted measures
            deletedMeasures.extend(vDeletedMeasures) # Saves deleted measures if any (it is unlikely that there will be unless there are fewer measures in the variant than the replacement region, which is unlikely for an elongation variant)

        #Now fix measure numbers given the saved information
        returnObj._fixMeasureNumbers(deletedMeasures, insertedMeasures)

        # have to clear cached variants, as they are no longer the same
        returnObj.elementsChanged()
        if not inPlace:
            return returnObj
        else:
            return None

    def _insertReplacementVariant(self, v, matchBySpan=True):
        '''
        Helper function for activateVariants. Activates variants which are the same size there the
        region they replace.


        >>> v = variant.Variant()
        >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
        >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
        >>> variantData = [variantDataM1, variantDataM2]
        >>> for d in variantData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    v.append(m)
        >>> v.groups = ['paris']
        >>> v.replacementDuration = 8.0

        >>> s = stream.Stream()
        >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
        >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
        >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
        >>> for d in streamData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    s.append(m)
        >>> s.insert(4.0, v)

        >>> deletedMeasures, insertedMeasuresTuple = s._insertReplacementVariant(v)
        >>> deletedMeasures
        []
        >>> insertedMeasuresTuple
        (0, [])
        >>> s.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 8.0>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
        {12.0} <music21.stream.Measure 0 offset=12.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>
        '''
        from music21 import variant

        removed = variant.Variant() # replacement variant
        removed.groups = ['default'] #for now, default
        vStart = self.elementOffset(v)
        # this method matches and removes on an individual basis
        if not matchBySpan:
            targetsMatched = 0
            for e in v.elements: # get components in the Variant
                # get target offset relative to Stream
                oInStream = vStart + e.getOffsetBySite(v.containedSite)
                # get all elements at this offset, force a class match
                targets = self.iter.getElementsByOffset(oInStream).getElementsByClass(e.classes[0])
                # only replace if we match the start
                if targets:
                    targetsMatched += 1
                    # always assume we just want the first one?
                    targetToReplace = targets[0]
                    #environLocal.printDebug(['matchBySpan', matchBySpan, 
                    #     'found target to replace:', targetToReplace])
                    # remove the target, place in removed Variant
                    removed.append(targetToReplace)
                    self.remove(targetToReplace)
                    # extract the variant component and insert into place
                    self.insert(oInStream, e)

                    if "Measure" in targetToReplace.classes:
                        e.number = targetToReplace.number
            # only remove old and add removed if we matched
            if targetsMatched > 0:
                # remove the original variant
                self.remove(v)
                # place newly contained elements in position
                self.insert(vStart, removed)

        # matching by span means that we remove all elements with the
        # span defined by the variant
        else:
            deletedMeasures = []
            insertedMeasures = []
            highestNumber = None

            targets = v.replacedElements(self)

            # this will always remove elements before inserting
            for e in targets:
                # need to get time relative to variant container's position
                oInVariant = self.elementOffset(e) - vStart
                removed.insert(oInVariant, e)
                #environLocal.printDebug(['matchBySpan', matchBySpan, 'activateVariants', 'removing', e])
                self.remove(e)
                if "Measure" in e.classes: #Save deleted measure numbers.
                    deletedMeasures.append(e.number)

            for e in v.elements:
                oInStream = vStart + e.getOffsetBySite(v.containedSite)
                self.insert(oInStream, e)
                if "Measure" in e.classes:
                    if deletedMeasures != []: #If there measure numbers left to use, use them.
                        e.number = deletedMeasures.pop(False) #Assign the next highest deleted measure number
                        highestNumber = e.number #Save the highest number used so far (for use in the case that there are extra measures with no numbers at the end)
                    else:
                        e.number = 0
                        insertedMeasures.append(e) # If no measure numbers left, add this numberless measure to insertedMeasures
            # remove the source variant
            self.remove(v)
            # place newly contained elements in position
            self.insert(vStart, removed)

            # If deletedMeasures != [], then there were more deleted measures than inserted and the remaining numbers in deletedMeasures are those that were removed.
            return deletedMeasures, (highestNumber, insertedMeasures) #In the case that the variant and stream are in the same time-signature, this should return []

    def _insertDeletionVariant(self, v, matchBySpan=True):
        '''
        Helper function for activateVariants used for inserting variants that are shorter than
        the region they replace. Inserts elements in the variant and deletes elements in the
        replaced region but does not close gaps.

        Returns a tuple describing the region where elements were removed, the
        gap is left behind to be dealt with by _removeOrExpandGaps.
        Tuple is of form (startOffset, lengthOfDeletedRegion, []). The empty list is expected by _removeOrExpandGaps
        and describes the list of elements which should be exempted from shifting for a particular gap. In the
        case of deletion, no elements need be exempted.


        >>> v = variant.Variant()
        >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
        >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
        >>> variantData = [variantDataM1, variantDataM2]
        >>> for d in variantData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    v.append(m)
        >>> v.groups = ['paris']
        >>> v.replacementDuration = 12.0

        >>> s = stream.Stream()
        >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
        >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
        >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
        >>> for d in streamData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    s.append(m)
        >>> s.insert(4.0, v)


        >>> deletedRegion, deletedMeasures, insertedMeasuresTuple = s._insertDeletionVariant(v)
        >>> deletedRegion
        (12.0, 4.0, [])
        >>> deletedMeasures
        [0]
        >>> insertedMeasuresTuple
        (0, [])
        >>> s.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 12.0>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>

        '''
        from music21 import variant

        deletedMeasures = [] # For keeping track of what measure numbers are deleted
        lengthDifference = v.replacementDuration - v.containedHighestTime #length of the deleted region
        removed = variant.Variant() # what group should this have?
        removed.groups = ['default'] #for now, default
        removed.replacementDuration = v.containedHighestTime
        vStart = self.elementOffset(v)
        deletionStart = vStart + v.containedHighestTime

        targets = v.replacedElements(self)

        # this will always remove elements before inserting
        for e in targets:
            if "Measure" in e.classes: #if a measure is deleted, save its number
                deletedMeasures.append(e.number)
            oInVariant = self.elementOffset(e) - vStart
            removed.insert(oInVariant, e)
            self.remove(e)

        #Next put in the elements from the variant
        highestNumber = None
        insertedMeasures = []
        for e in v.elements:
            if "Measure" in e.classes:
                if deletedMeasures != []: #If there are deleted numbers still saved, assign this measure the next highest and remove it from the list.
                    e.number = deletedMeasures.pop(False)
                    highestNumber = e.number #Save the highest number assigned so far. If there are numberless inserted measures at the end, this will name where to begin numbering.
                else:
                    e.number = 0
                    insertedMeasures.append(e) #If there are no deleted numbers left (unlikely) save the inserted measures for renumbering later.
            oInStream = vStart + e.getOffsetBySite(v.containedSite)
            self.insert(oInStream, e)

        # remove the source variant
        self.remove(v)
        # place newly contained elements in position
        self.insert(vStart, removed)

        #each variant leaves a gap, this saves the required information about those gaps
        return (deletionStart, lengthDifference, []), deletedMeasures, (highestNumber, insertedMeasures) #In most cases, inserted measures should be [].

    def _insertInsertionVariant(self, v, matchBySpan=True):
        '''
        Helper function for activateVariants. _removeOrExpandGaps must be called on the expanded regions before this function
        or it will not work properly.


        >>> v = variant.Variant()
        >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
        >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
        >>> variantData = [variantDataM1, variantDataM2]
        >>> for d in variantData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    v.append(m)
        >>> v.groups = ['paris']
        >>> v.replacementDuration = 4.0

        >>> s = stream.Stream()
        >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
        >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
        >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
        >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
        >>> for d in streamData:
        ...    m = stream.Measure()
        ...    for pitchName,durType in d:
        ...        n = note.Note(pitchName)
        ...        n.duration.type = durType
        ...        m.append(n)
        ...    s.append(m)
        >>> s.insert(4.0, v)

        >>> insertionRegionsForExpansion = [(8.0, 4.0, [v])]
        >>> s._removeOrExpandGaps(insertionRegionsForExpansion, isRemove=False, inPlace=True)

        >>> insertedMeasuresTuple, deletedMeasures = s._insertInsertionVariant(v)
        >>> measurePrior, insertedMeasures = insertedMeasuresTuple
        >>> measurePrior
        0
        >>> len(insertedMeasures)
        1

        >>> s.show('text')
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note G>
        {4.0} <music21.variant.Variant object of length 4.0>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
        {12.0} <music21.stream.Measure 0 offset=12.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>
        {16.0} <music21.stream.Measure 0 offset=16.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>

        '''
        from music21 import variant

        deletedMeasures = []
        removed = variant.Variant() # what group should this have?
        removed.groups = ['default'] #for now, default
        removed.replacementDuration = v.containedHighestTime
        vStart = self.elementOffset(v)

        #First deal with the elements in the overlapping section (limit by class)
        targets = v.replacedElements(self)

        # this will always remove elements before inserting
        for e in targets:
            if "Measure" in e.classes: # Save deleted measure numbers.
                deletedMeasures.append(e.number)
            oInVariant = self.elementOffset(e) - vStart
            removed.insert(oInVariant, e)
            self.remove(e)

        #Next put in the elements from the variant
        highestMeasure = None
        insertedMeasures = []
        for e in v.elements:
            if "Measure" in e.classes: # If there are deleted measure numbers left, assign the next inserted measure the next highest number and remove it.
                if deletedMeasures != []:
                    e.number = deletedMeasures.pop(False)
                    highestMeasure = e.number # Save the highest number assigned so far so we know where to being numbering new measures.
                else:
                    e.number = 0
                    insertedMeasures.append(e) # If there are no deleted measures, we have begun inserting as yet unnumbered measures, save which those are.
            oInStream = vStart + e.getOffsetBySite(v.containedSite)
            self.insert(oInStream, e)

        if highestMeasure is None: #If the highestMeasure is None (which will occur if the variant is a strict insertion and replaces no measures,
                                    #we need to choose the highest measure number prior to the variant.
            measuresToCheck = self.getElementsByOffset(0.0, self.elementOffset(v),
                includeEndBoundary=True,
                mustFinishInSpan=False,
                mustBeginInSpan=True,
                classList = ["Measure"])
            if measuresToCheck != []:
                for m in measuresToCheck:
                    if highestMeasure is None or m.number > highestMeasure:
                        highestMeasure = m.number
            else:
                highestMeasure = 0

        # remove the source variant
        self.remove(v)
        # place newly contained elements in position
        self.insert(vStart, removed)

        return (highestMeasure, insertedMeasures), deletedMeasures

    def _removeOrExpandGaps(self, listOffsetDurExemption, 
                            isRemove=True, inPlace=False, exemptClasses=None):
        '''
        Helper for activateVariants. Takes a list of tuples in the form 
        (startoffset, duration, [list, of, exempt, objects]). If isRemove is True,
        gaps with duration will be closed at each startOffset. 
        Exempt objects are useful for gap-expansion with variants. The gap must push all objects
        that occur after the insertion ahead, but the variant object 
        itself should not be moved except by other gaps. This is poorly written
        and should be re-written, but it is difficult to describe.


        >>> s = stream.Stream()
        >>> s.insert(5.0, note.Note('a'))
        >>> s.insert(10.0, note.Note('b'))
        >>> s.insert(11.0, note.Note('c'))
        >>> s.insert(12.0, note.Note('d'))
        >>> s.insert(13.0, note.Note('e'))
        >>> s.insert(20.0, note.Note('f'))
        >>> n = note.Note('g')
        >>> s.insert(15.0, n)

        >>> sGapsRemoved = s._removeOrExpandGaps([(0.0,5.0, []), (6.0,4.0, []), (14.0,6.0, [n])], isRemove=True)
        >>> sGapsRemoved.show('text')
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
        {2.0} <music21.note.Note C>
        {3.0} <music21.note.Note D>
        {4.0} <music21.note.Note E>
        {15.0} <music21.note.Note G>
        {5.0} <music21.note.Note F>

        >>> sGapsExpanded = s._removeOrExpandGaps([(0.0,5.0, []), (11.0,5.0, []), (14.0,1.0, [n])], isRemove=False)
        >>> sGapsExpanded.show('text')
        {10.0} <music21.note.Note A>
        {15.0} <music21.note.Note B>
        {21.0} <music21.note.Note C>
        {22.0} <music21.note.Note D>
        {23.0} <music21.note.Note E>
        {25.0} <music21.note.Note G>
        {31.0} <music21.note.Note F>

        '''


        if inPlace is True:
            returnObj = self
        else:
            returnObj = copy.deepcopy(self)

        returnObjDuration = returnObj.duration.quarterLength

        # If any classes should be exempt from gap closing or expanding, this deals with those.
        classList = []
        if exemptClasses is None:
            classList = None
        else:
            for e in returnObj.elements:
                if type(e) not in classList: # pylint: disable=unidiomatic-typecheck
                    classList.append(type(e))
            for c in exemptClasses:
                if c in classList:
                    classList.remove(c)

        if isRemove is True:
            shiftDur = 0.0
            listSorted = sorted(listOffsetDurExemption, key=lambda target: target[0])
            for i,durTuple in enumerate(listSorted):
                startOffset, durationAmount, exemptObjects = durTuple
                if i+1 < len(listSorted):
                    endOffset = listSorted[i+1][0]
                    includeEnd = False
                else:
                    endOffset = returnObjDuration
                    includeEnd = True

                shiftDur = shiftDur + durationAmount
                for e in returnObj.getElementsByOffset(startOffset+durationAmount,
                    endOffset,
                    includeEndBoundary=includeEnd,
                    mustFinishInSpan=False,
                    mustBeginInSpan=True,
                    classList=classList):

                    if e in exemptObjects:
                        continue

                    elementOffset = e.getOffsetBySite(returnObj)
                    returnObj.setElementOffset(e, elementOffset-shiftDur)
        else:
            shiftDur = 0.0
            shiftsDict = {}
            listSorted = sorted(listOffsetDurExemption, key=lambda target: target[0])
            for i, durTuple in enumerate(listSorted):
                startOffset, durationAmount, exemptObjects = durTuple

                if i+1 < len(listSorted):
                    endOffset = listSorted[i+1][0]
                    includeEnd = False
                else:
                    endOffset = returnObjDuration
                    includeEnd = True

                exemptShift = shiftDur
                shiftDur = shiftDur + durationAmount
                shiftsDict[startOffset] = shiftDur, endOffset, includeEnd, exemptObjects, exemptShift

            for offset in sorted(shiftsDict.keys(), key=lambda offset: -offset):
                shiftDur, endOffset, includeEnd, exemptObjects, exemptShift = shiftsDict[offset]
                for e in returnObj.getElementsByOffset(offset,
                    endOffset,
                    includeEndBoundary=includeEnd,
                    mustFinishInSpan=False,
                    mustBeginInSpan=True,
                    classList=classList):

                    if e in exemptObjects:
                        elementOffset = e.getOffsetBySite(returnObj)
                        returnObj.setElementOffset(e, elementOffset + exemptShift)
                        continue

                    elementOffset = e.getOffsetBySite(returnObj)
                    returnObj.setElementOffset(e, elementOffset + shiftDur)

        if inPlace is True:
            return
        else:
            return returnObj

    def _fixMeasureNumbers(self, deletedMeasures, insertedMeasures):
        '''
        Corrects the measures numbers of a string of measures given a list of measure numbers that have been deleted and a
        list of tuples (highest measure number below insertion, number of inserted measures).

        >>> s = converter.parse("tinynotation: 4/4 d4 e4 f4 g4   a2 b-4 a4    g4 a8 g8 f4 e4    g1")
        >>> s.makeMeasures(inPlace=True)
        >>> s[-1].offset = 20.0
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note D>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note G>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note A>
            {2.0} <music21.note.Note B->
            {3.0} <music21.note.Note A>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {1.5} <music21.note.Note G>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note E>
        {20.0} <music21.stream.Measure 4 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline style=final>
        >>> s.remove(s.measure(2))
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            ...
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            ...
        {20.0} <music21.stream.Measure 4 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline style=final>        
        >>> deletedMeasures = [2]
        >>> m1 = stream.Measure()
        >>> m1.repeatAppend(note.Note('e'),4)
        >>> s.insert(12.0, m1)
        >>> m2 = stream.Measure()
        >>> m2.repeatAppend(note.Note('f'),4)
        >>> s.insert(16.0, m2)
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            ...
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note G>
            ...
        {12.0} <music21.stream.Measure 0 offset=12.0>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
        {16.0} <music21.stream.Measure 0 offset=16.0>
            {0.0} <music21.note.Note F>
            {1.0} <music21.note.Note F>
            {2.0} <music21.note.Note F>
            {3.0} <music21.note.Note F>
        {20.0} <music21.stream.Measure 4 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline style=final>
        >>> insertedMeasures = [(3, [m1, m2])]
        
        >>> s._fixMeasureNumbers(deletedMeasures, insertedMeasures)
        >>> s.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            ...
        {8.0} <music21.stream.Measure 2 offset=8.0>
            {0.0} <music21.note.Note G>
            ...
        {12.0} <music21.stream.Measure 3 offset=12.0>
            {0.0} <music21.note.Note E>
            ...
        {16.0} <music21.stream.Measure 4 offset=16.0>
            {0.0} <music21.note.Note F>
            ...
        {20.0} <music21.stream.Measure 5 offset=20.0>
            {0.0} <music21.note.Note G>
            {4.0} <music21.bar.Barline style=final>
        >>> fixedNumbers = []
        >>> for m in s.getElementsByClass("Measure"):
        ...    fixedNumbers.append( m.number )
        >>> fixedNumbers
        [1, 2, 3, 4, 5]

        '''
        deletedMeasures.extend(insertedMeasures)
        allMeasures = deletedMeasures

        if allMeasures is [] or allMeasures is None:
            return
        
        def measureNumberSortRoutine(numOrNumTuple):
            if isinstance(numOrNumTuple, tuple):
                return measureNumberSortRoutine(numOrNumTuple[0])
            elif numOrNumTuple is None:
                return -999
            else:
                return numOrNumTuple
            
        allMeasures.sort(key=measureNumberSortRoutine)

        oldMeasures = self.getElementsByClass("Measure")
        newMeasures = []

        cummulativeNumberShift = 0
        oldCorrections = {}
        newCorrections = {}
        # the inserted measures must be treated differently than the original measures.
        # an inserted measure should not shift itself, but it should shift measures with the same number.
        # However, inserted measures should still be shifted by every other correction.

        # First collect dictionaries of shift boundaries and the amount of the shift.
        # at the same time, five un-numbered measures numbers that make sense.
        for measureNumber in allMeasures:
            if isinstance(measureNumber, tuple): #tuple implies insertion
                measurePrior, extendedMeasures = measureNumber
                if len(extendedMeasures) is 0: #No measures were added, therefore no shift.
                    continue
                cummulativeNumberShift += len(extendedMeasures)
                nextMeasure = measurePrior + 1
                for m in extendedMeasures:
                    oldMeasures.remove(m)
                    newMeasures.append(m)
                    m.number = nextMeasure
                    nextMeasure += 1
                oldCorrections[measurePrior+1] = cummulativeNumberShift
                newCorrections[nextMeasure] = cummulativeNumberShift
            else: #integer implies deletion
                cummulativeNumberShift -= 1
                oldCorrections[measureNumber+1] = cummulativeNumberShift
                newCorrections[measureNumber+1] = cummulativeNumberShift

        # Second, make corrections based on the dictionaries. The key is the measure number
        # above which measures should be shifted by the value up to the next key. It is easiest
        # to do this in reverse order so there is no overlapping.
        previousBoundary = None
        for k in sorted(oldCorrections.keys(), key=lambda x: -x):
            shift = oldCorrections[k]
            for m in oldMeasures:
                if previousBoundary is None or m.number < previousBoundary:
                    if m.number >= k:
                        m.number = m.number + shift
            previousBoundary = k

        previousBoundary = None
        for k in sorted(newCorrections.keys(), key=lambda x: -x):
            shift = newCorrections[k]
            for m in newMeasures:
                if previousBoundary is None or m.number < previousBoundary:
                    if m.number >= k:
                        m.number = m.number + shift
            previousBoundary = k

    def showVariantAsOssialikePart(self, containedPart, variantGroups, inPlace=False):
        '''
        Takes a part within the score and a list of variant groups within that part. Puts the variant object
        in a part surrounded by hidden rests to mimic the appearence of an ossia despite limited
        musicXML support for ossia staves. Note that this will ignore variants with .lengthType
        'elongation' and 'deletion' as there is no good way to represent ossia staves like those
        by this method.


        >>> sPartStream = converter.parse("tinynotation: 4/4      d4 e4 f4 g4   a2 b-4 a4    g4 a8 g8 f4 e4    d2 a2                  d4 e4 f4 g4    a2 b-4 a4    g4 a8 b-8 c'4 c4    f1")
        >>> sPartStream.makeMeasures(inPlace=True)
        >>> v1stream = converter.parse("tinynotation: 4/4                       a2. b-8 a8")
        >>> v2stream = converter.parse("tinynotation: 4/4                                                     d4 f4 a2")

        >>> v1 = variant.Variant()
        >>> v1measure = stream.Measure()
        >>> v1.insert(0.0, v1measure)
        >>> for e in v1stream.notesAndRests:
        ...    v1measure.insert(e.offset, e)

        >>> v2 = variant.Variant()
        >>> v2measure = stream.Measure()
        >>> v2.insert(0.0, v2measure)
        >>> for e in v2stream.notesAndRests:
        ...    v2measure.insert(e.offset, e)

        >>> v3 = variant.Variant()
        >>> v2.replacementDuration = 4.0
        >>> v3.replacementDuration = 4.0
        >>> v1.groups = ["variant1"]
        >>> v2.groups = ["variant2"]
        >>> v3.groups = ["variant3"]

        >>> sPart = stream.Part()
        >>> for e in sPartStream:
        ...    sPart.insert(e.offset, e)

        >>> sPart.insert(4.0, v1)
        >>> sPart.insert(12.0, v2)
        >>> sPart.insert(20.0, v3) #This is a deletion variant and will be skipped
        >>> s = stream.Score()
        >>> s.insert(0.0, sPart)
        >>> streamWithOssia = s.showVariantAsOssialikePart(sPart, ['variant1', 'variant2', 'variant3'], inPlace=False)
        >>> #_DOCS_SHOW streamWithOssia.show()

        '''
        from music21 import variant

        #containedPart must be in self, or an exception is raised.
        if not (containedPart in self):
            raise variant.VariantException("Could not find %s in %s" % (containedPart, self))

        if inPlace is True:
            returnObj = self
            returnPart = containedPart
        else:
            returnObj = copy.deepcopy(self)
            containedPartIndex = self.parts.index(containedPart)
            returnPart = returnObj.parts[containedPartIndex]

        #First build a new part object that is the same length as returnPart but entirely hidden rests.
        #This is done by copying the part and removing unnecessary objects including irrelevant variants
        #but saving relevant variants.
        for variantGroup in variantGroups:
            newPart = copy.deepcopy(returnPart)
            expressedVariantsExist = False
            for e in newPart.elements: #For reasons I cannot explain, using e in newPart does not work because removing the variant elements causes the measures they are associated to be skipped and remain unprocessed.
                eclasses = e.classes
                if "Variant" in eclasses:
                    elementGroups = e.groups
                    if not( variantGroup in elementGroups ) or e.lengthType in ['elongation', 'deletion']:
                        newPart.remove(e)
                    else:
                        expressedVariantsExist = True
                elif "GeneralNote" in eclasses:
                    # elif type(e) in [music21.note.Note, music21.chord.Chord, music21.note.Rest]:
                    nQuarterLength = e.duration.quarterLength
                    nOffset = e.getOffsetBySite(newPart)
                    newPart.remove(e)
                    r = note.Rest()
                    r.hideObjectOnPrint = True
                    r.duration.quarterLenght = nQuarterLength
                    newPart.insert(nOffset, r)
                elif "Measure" in eclasses: #Recurse if measure
                    measureDuration = e.duration.quarterLength
                    for n in e.notesAndRests:
                        e.remove(n)
                    r = note.Rest()
                    r.duration.quarterLength = measureDuration
                    r.hideObjectOnPrint = True
                    e.insert(0.0, r)

                e.hideObjectOnPrint = True

            newPart.activateVariants(variantGroup, inPlace=True, matchBySpan=True)
            if expressedVariantsExist:
                returnObj.insert(0.0, newPart)

        if inPlace:
            return
        else:
            return returnObj

    def makeVariantBlocks(self):
        '''
        from music21 import *
        '''
        #forDeletion = []
        variantsToBeDone = self.variants.elements

        for v in variantsToBeDone:
            #if v in forDeletion:
            #   continue

            #highestVariant = {}

            startOffset = self.elementOffset(v)
            endOffset = v.replacementDuration + startOffset
            conflictingVariants = self.getElementsByOffset(offsetStart= startOffset,
                                                    offsetEnd=endOffset,
                                                    includeEndBoundary=False,
                                                    mustFinishInSpan=False,
                                                    mustBeginInSpan=True,
                                                    classList = ['Variant'])
            for cV in conflictingVariants:
                #if cV in forDeletion:
                #    continue
                oldReplacementDuration = cV.replacementDuration
#                if len(cV.groups) > 0:
#                    cVname = cV.groups[0]
#                else:
#                    cVname = None
#                cVoffset = self.elementOffset(cV)

                #if cVname in highestVariant:
                    #hVendOffset, hV = highestVariant[cVname]
                    #hVstartOffset = self.elementOffset(hV)

                #    if cV.replacementDuration + cVoffset > hVendOffset:
                #        highestVariant[cVname] = (cV.replacementDuration + cVoffset, cV)
                #        shiftOffset = cVoffset-hVendOffset
                #        r = note.SpacerRest()
                #        r.duration.quarterLength = shiftOffset
                #        r.hideObjectOnPrint = True
                #        hV.insert(hVendOffset, r)
                #        for el in cV._stream:
                #            oldOffset = el.getOffsetBySite(cV._stream)
                #            hV.insert(hVendOffset+shiftOffset+oldOffset, el)
                #        hV.replacementDuration += shiftOffset + cV.replacementDuration
                #        forDeletion.append(cV)
                #        variantsToBeDone.append(hV)
                #    else:
                #        pass
                #else:
                    #highestVariant[cVname] = (cV.replacementDuration + cVoffset, cV)
                if self.elementOffset(cV) == startOffset:
                    continue # do nothing
                else:
                    shiftOffset = self.elementOffset(cV) - startOffset
                    r = note.SpacerRest()
                    r.duration.quarterLength = shiftOffset
                    r.hideObjectOnPrint = True
                    for el in cV._stream:
                        oldOffset = el.getOffsetBySite(cV._stream)
                        cV._stream.setElementOffset(el, oldOffset+shiftOffset)
                    cV.insert(0.0, r)
                    cV.replacementDuration = oldReplacementDuration
                    self.remove(cV)
                    self.insert(startOffset, cV)
                    variantsToBeDone.append(cV)

        #for v in forDeletion:
        #    self.remove(v)


#------------------------------------------------------------------------------


class Voice(Stream):
    '''
    A Stream subclass for declaring that all the music in the
    stream belongs to a certain "voice" for analysis or display
    purposes.

    Note that both Finale's Layers and Voices as concepts are
    considered Voices here.
    '''
    recursionType = 'elementsFirst'



#------------------------------------------------------------------------------


class Measure(Stream):
    '''
    A representation of a Measure organized as a Stream.

    All properties of a Measure that are Music21 objects are found as part of
    the Stream's elements.
    '''
    recursionType = 'elementsFirst'
    isMeasure = True

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'timeSignatureIsNew': 'Boolean describing if the TimeSignature is different than the previous Measure.',
    'clefIsNew': 'Boolean describing if the Clef is different than the previous Measure.',
    'keyIsNew': 'Boolean describing if KeySignature is different than the previous Measure.',
    'number': 'A number representing the displayed or shown Measure number as presented in a written Score.',
    'numberSuffix': '''If a Measure number has a string annotation, such as "a" or similar,
                       this string is stored here. Note that in MusicXML, such suffixes often appear as
                       prefixes to measure numbers.  In music21 (like most measure numbering systems), these
                       numbers appear as suffixes.''',
    'layoutWidth': '''A suggestion for layout width, though most rendering systems do not support
                      this designation. Use :class:`~music21.layout.SystemLayout` objects instead.''',
    'paddingLeft': '''defines empty space at the front of the measure for purposes of determining
                      beat, etc for pickup/anacrusis bars.  In 4/4, a measure with a one-beat pickup
                      note will have a `paddingLeft` of 3.0. (The name comes from the CSS graphical term
                      for the amount of padding on the left side of a region.)''',
    'paddingRight': '''defines empty space at the end of the measure for purposes of determining
                       whether or not a measure is filleds.  In 4/4, a piece beginning a one-beat pickup
                       note will often have a final measure of three beats, instead of four.  The final
                       measure should have a `paddingRight` of 1.0. (The name comes from the CSS graphical term
                       for the amount of padding on the right side of a region.)''',
    }

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)

        # clef and timeSignature is defined as a property below
        self.timeSignatureIsNew = False
        self.clefIsNew = False
        self.keyIsNew = False

        self.filled = False

        # padding: defining a context for offsets contained within this Measure
        # padding defines dead regions of offsets into the measure
        # the paddingLeft is used by TimeSignature objects to determine beat
        # position; paddingRight defines a QL from the end of the time signature
        # to the last valid offset
        # paddingLeft is used to define pickup/anacrusis bars
        self.paddingLeft = 0
        self.paddingRight = 0

        if 'number' in keywords:
            self.number = keywords['number']
        else:
            self.number = 0 # 0 means undefined or pickup
        self.numberSuffix = None # for measure 14a would be "a"
        # we can request layout width, using the same units used
        # in layout.py for systems; most musicxml readers do not support this
        # on input
        self.layoutWidth = None

#    def addRepeat(self):
#        # TODO: write
#        pass

#    def addTimeDependentDirection(self, time, direction):
#        # TODO: write
#        pass

    def measureNumberWithSuffix(self):
        '''
        Return the measure `.number` with the `.numberSuffix` as a string.
        
        >>> m = stream.Measure()
        >>> m.number = 4
        >>> m.numberSuffix = "A"
        >>> m.measureNumberWithSuffix()
        '4A'
        
        Test that it works as musicxml
        
        >>> xml = musicxml.m21ToString.fromMeasure(m)
        >>> print(xml)
        <?xml version="1.0"...?>
        ...
        <part id="...">
            <measure number="4A">
        ...
        
        Test round tripping:
        
        >>> s2 = converter.parseData(xml)
        >>> print(s2.semiFlat.getElementsByClass('Measure')[0].measureNumberWithSuffix())
        4A        
        
        Note that we use print here because in parsing the data will become a unicode string.        
        '''
        if self.numberSuffix:
            return str(self.number) + self.numberSuffix
        else:
            return str(self.number)

    def __repr__(self):
        return "<music21.stream.%s %s offset=%s>" % \
            (self.__class__.__name__, self.measureNumberWithSuffix(), self.offset)

    #--------------------------------------------------------------------------
    def mergeAttributes(self, other):
        '''
        Given another Measure, configure all non-element attributes of this
        Measure with the attributes of the other Measure. No elements
        will be changed or copied.

        This method is necessary because Measures, unlike some Streams,
        have attributes independent of any stored elements.

        Overrides base.Music21Object.mergeAttributes
        
        >>> m1 = stream.Measure()
        >>> m1.id = 'MyMeasure'
        >>> m1.clefIsNew = True
        >>> m1.number = 2
        >>> m1.numberSuffix = 'b'
        >>> m1.layoutWidth = 200
        
        >>> m2 = stream.Measure()
        >>> m2.mergeAttributes(m1)
        >>> m2.layoutWidth
        200
        >>> m2.id
        'MyMeasure'
        >>> m2
        <music21.stream.Measure 2b offset=0.0>
        
        Try with not another Measure...
        
        >>> m3 = stream.Stream()
        >>> m3.id = 'hello'
        >>> m2.mergeAttributes(m3)
        >>> m2.id
        'hello'
        >>> m2.layoutWidth
        200
        '''
        # calling bass class sets id, groups
        super(Measure, self).mergeAttributes(other)

        for attr in 'timeSignatureIsNew clefIsNew keyIsNew filled paddingLeft paddingRight number numberSuffix layoutWidth'.split():
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

    #--------------------------------------------------------------------------
    def makeNotation(self, 
                     inPlace=False, 
                     **subroutineKeywords):
        '''
        This method calls a sequence of Stream methods on this
        :class:`~music21.stream.Measure` to prepare notation.

        If `inPlace` is True, this is done in-place; if
        `inPlace` is False, this returns a modified deep copy.

        >>> m = stream.Measure()
        >>> n1 = note.Note('g#')
        >>> n2 = note.Note('g')
        >>> m.append([n1, n2])
        >>> m.makeNotation(inPlace=True)
        >>> m.notes[1].pitch.accidental
        <accidental natural>
        '''
        #environLocal.printDebug(['Measure.makeNotation'])
        # TODO: this probably needs to look to see what processes need to be done; for example, existing beaming may be destroyed.

        # assuming we are not trying to get context of previous measure
        if not inPlace: # make a copy
            m = copy.deepcopy(self)
        else:
            m = self

        srkCopy = subroutineKeywords.copy()
        
        for illegalKey in ('meterStream', 'refStreamOrTimeRange', 'bestClef'):
            if illegalKey in srkCopy:
                del(srkCopy[illegalKey])
        
        m.makeAccidentals(searchKeySignatureByContext=True, inPlace=True, **srkCopy)
        # makeTies is for cross-bar associations, and cannot be used
        # at just the measure level
        #m.makeTies(meterStream, inPlace=True)

        # must have a time signature before calling make beams
        if m.timeSignature is None:
            # get a time signature if not defined, searching the context if
            # necessary
            contextMeters = m.getTimeSignatures(searchContext=True,
                            returnDefault=False)
            defaultMeters = m.getTimeSignatures(searchContext=False,
                            returnDefault=True)
            if len(contextMeters) > 0:
                ts = contextMeters[0]
            else:
                try:
                    ts = self.bestTimeSignature()
                except (StreamException, meter.MeterException):
                    # there must be one here
                    ts = defaultMeters[0]
            m.timeSignature = ts  # a Stream; get the first element

        #environLocal.printDebug(['have time signature', m.timeSignature])
        if m.streamStatus.haveBeamsBeenMade() is False:
            try:
                m.makeBeams(inPlace=True)
            except StreamException:
                # this is a result of makeMeaures not getting everything
                # note to measure allocation right
                pass
                #environLocal.printDebug(['skipping makeBeams exception', StreamException])
        if m.streamStatus.haveTupletBracketsBeenMade() is False:
            m.makeTupletBrackets(inPlace=True)

        if not inPlace:
            return m
        else:
            return None

    def barDurationProportion(self, barDuration=None):
        '''
        Return a floating point value greater than 0 showing the proportion
        of the bar duration that is filled based on the highest time of
        all elements. 0.0 is empty, 1.0 is filled; 1.5 specifies of an
        overflow of half.

        Bar duration refers to the duration of the Measure as suggested by
        the `TimeSignature`. This value cannot be determined without a `TimeSignature`.

        An already-obtained Duration object can be supplied with the `barDuration`
        optional argument.

        >>> import copy
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        Fraction(1, 3)
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        Fraction(2, 3)
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        1.0
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        Fraction(4, 3)
        '''
        # passing a barDuration may save time in the lookup process
        if barDuration is None:
            barDuration = self.barDuration
        return opFrac(self.highestTime / barDuration.quarterLength)

    def padAsAnacrusis(self):
        '''
        Given an incompletely filled Measure, adjust the `paddingLeft` value to to
        represent contained events as shifted to fill the right-most duration of the bar.

        Calling this method will overwrite any previously set `paddingLeft` value,
        based on the current TimeSignature-derived `barDuration` attribute.

        >>> import copy
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1.0
        >>> m.append(copy.deepcopy(n))
        >>> m.padAsAnacrusis()
        >>> m.paddingLeft
        2.0
        >>> m.timeSignature = meter.TimeSignature('5/4')
        >>> m.padAsAnacrusis()
        >>> m.paddingLeft
        4.0
        '''
        # note: may need to set paddingLeft to 0 before examining

        # bar duration is that suggested by time signature; it may
        # may not be the same as Stream duration, which is based on contents
        barDuration = self.barDuration
        proportion = self.barDurationProportion(barDuration=barDuration)
        if proportion < 1:
            # get 1 complement
            proportionShift = 1 - proportion
            self.paddingLeft = opFrac(barDuration.quarterLength * proportionShift)

            #shift = barDuration.quarterLength * proportionShift
            #environLocal.printDebug(['got anacrusis shift:', shift,
            #                    barDuration.quarterLength, proportion])
            # this will shift all elements
            #self.shiftElements(shift, classFilterList=(note.GeneralNote,))
        else:
            pass
            #environLocal.printDebug(['padAsAnacrusis() called; however, no anacrusis shift necessary:', barDuration.quarterLength, proportion])

    #---------------------------------------------------------------------------


    def _getBarDuration(self):
        # Docs in the property.

        # TODO: it is possible that this should be cached or exposed as a method
        # as this search may take some time.
        if self.timeSignature is not None:
            ts = self.timeSignature
        else: # do a context-based search
            tsStream = self.getTimeSignatures(searchContext=True,
                       returnDefault=False, sortByCreationTime=True)
            if len(tsStream) == 0:
                try:
                    ts = self.bestTimeSignature()
                except exceptions21.Music21Exception:
                    return duration.Duration(self.highestTime)

                #raise StreamException('cannot determine bar duration without a time signature reference')
            else: # it is the first found
                ts = tsStream[0]
        return ts.barDuration

    barDuration = property(_getBarDuration,
        doc = '''
        Return the bar duration, or the Duration specified by the TimeSignature,
        regardless of what elements are found in this Measure or the highest time.
        TimeSignature is found first within the Measure,
        or within a context based search.

        To get the duration of the total length of elements, just use the
        `.duration` property.

        Here we create a 3/4 measure and "over-stuff" it with five quarter notes.
        `barDuration` still gives a duration of 3.0, or a dotted quarter note,
        while `.duration` gives a whole note tied to a quarter.


        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.barDuration
        <music21.duration.Duration 3.0>
        >>> m.repeatAppend(note.Note(type='quarter'), 5)
        >>> m.barDuration
        <music21.duration.Duration 3.0>
        >>> m.duration
        <music21.duration.Duration 5.0>

        The objects returned by `barDuration` and `duration` are full :class:`~music21.duration.Duration`
        objects, will all the relevant properties:

        >>> m.barDuration.fullName
        'Dotted Half'
        >>> m.duration.fullName
        'Whole tied to Quarter (5 total QL)'
        ''')

    #---------------------------------------------------------------------------
    # Music21Objects are stored in the Stream's elements list
    # properties are provided to store and access these attribute

    def bestTimeSignature(self):
        '''
        Given a Measure with elements in it,
        get a TimeSignature that contains all elements.
        Calls meter.bestTimeSignature(self)

        Note: this does not yet accommodate triplets.


        We create a simple stream that should be in 3/4


        >>> s = converter.parse('C4 D4 E8 F8', format='tinyNotation', makeNotation=False)
        >>> m = stream.Measure()
        >>> for el in s:
        ...     m.insert(el.offset, el)

        But there is no TimeSignature!

        >>> m.show('text')
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {2.5} <music21.note.Note F>

        So, we get the best Time Signature and put it in the Stream.

        >>> ts = m.bestTimeSignature()
        >>> ts
        <music21.meter.TimeSignature 3/4>
        >>> m.timeSignature = ts
        >>> m.show('text')
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {2.5} <music21.note.Note F>

        For further details about complex time signatures, etc.
        see `meter.bestTimeSignature()`

        '''
        return meter.bestTimeSignature(self)


    def _getClef(self):
        # TODO: perhaps sort by priority?
        clefList = self.getElementsByClass('Clef')
        # only return clefs that have offset = 0.0
        clefList = clefList.getElementsByOffset(0)
        if len(clefList) == 0:
            return None
        else:
            return clefList[0]

    def _setClef(self, clefObj):
        # if clef is None; remove object?
        oldClef = self._getClef()
        if oldClef is not None:
            #environLocal.printDebug(['removing clef', oldClef])
            junk = self.pop(self.index(oldClef))
        if clefObj is None:
            # all that is needed is to remove the old clef
            # there is no new clef - suppresses the clef of a stream
            return
        self.insert(0.0, clefObj)
        self.elementsChanged() # for some reason needed to make sure that sorting of Clef happens before TimeSignature

    clef = property(_getClef, _setClef, doc='''
        Finds or sets a :class:`~music21.clef.Clef` at offset 0.0 in the measure:

        >>> m = stream.Measure()
        >>> m.number = 10
        >>> m.clef = clef.TrebleClef()
        >>> thisTrebleClef = m.clef
        >>> thisTrebleClef.sign
        'G'
        >>> thisTrebleClef.getOffsetBySite(m)
        0.0

        Setting the clef for the measure a second time removes the previous clef
        from the measure and replaces it with the new one:

        >>> m.clef = clef.BassClef()
        >>> m.clef.sign
        'F'

        OMIT_FROM_DOCS
        # TODO: v2.1 -- restore this functionality...

        And the TrebleClef is no longer in the measure:

        thisTrebleClef.getOffsetBySite(m)
        Traceback (most recent call last):
        SitesException: The object <music21.clef.TrebleClef> is not in site <music21.stream.Measure 10 offset=0.0>.

        The `.clef` appears in a `.show()` or other call
        just like any other element

        >>> m.append(note.Note('D#', type='whole'))
        >>> m.show('text')
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.note.Note D#>
        ''')

    def _getTimeSignature(self):
        '''


        >>> a = stream.Measure()
        >>> a.timeSignature = meter.TimeSignature('2/4')
        >>> a.timeSignature.numerator, a.timeSignature.denominator
        (2, 4)
        '''
        # there could be more than one
        tsList = self.getElementsByClass('TimeSignature')
        #environLocal.printDebug(['matched Measure classes of type TimeSignature', tsList, len(tsList)])
        # only return timeSignatures at offset = 0.0
        tsList = tsList.getElementsByOffset(0)
        if len(tsList) == 0:
            return None
        else:
            return tsList[0]

    def _setTimeSignature(self, tsObj):
        '''


        >>> a = stream.Measure()
        >>> a.timeSignature = meter.TimeSignature('5/4')
        >>> a.timeSignature.numerator, a.timeSignature.denominator
        (5, 4)
        >>> a.timeSignature = meter.TimeSignature('2/8')
        >>> a.timeSignature.numerator, a.timeSignature.denominator
        (2, 8)

        '''
        oldTimeSignature = self._getTimeSignature()
        if oldTimeSignature is not None:
            #environLocal.printDebug(['removing ts', oldTimeSignature])
            junk = self.pop(self.index(oldTimeSignature))
        if tsObj is None:
            # all that is needed is to remove the old time signature
            # there is no new time signature - suppresses the time signature of a stream
            return
        self.insert(0, tsObj)

    timeSignature = property(_getTimeSignature, _setTimeSignature)

    def _getKeySignature(self):
        '''
        >>> a = stream.Measure()
        >>> a.keySignature = key.KeySignature(0)
        >>> a.keySignature.sharps
        0
        '''
        keyList = self.getElementsByClass('KeySignature')
        # only return keySignatures with offset = 0.0
        keyList = keyList.getElementsByOffset(0)
        if len(keyList) == 0:
            return None
        else:
            return keyList[0]

    def _setKeySignature(self, keyObj):
        '''
        >>> a = stream.Measure()
        >>> a.keySignature = key.KeySignature(6)
        >>> a.keySignature.sharps
        6


        A key.Key object can be used instead of key.KeySignature,
        since the former derives from the latter.

        >>> a.keySignature = key.Key('E-', 'major')
        >>> a.keySignature.sharps
        -3
        '''
        oldKey = self._getKeySignature()
        if oldKey is not None:
            #environLocal.printDebug(['removing key', oldKey])
            junk = self.pop(self.index(oldKey))
        if keyObj is None:
            # all that is needed is to remove the old key signature
            # there is no new key signature - suppresses the key signature of a stream
            return
        self.insert(0, keyObj)

    keySignature = property(_getKeySignature, _setKeySignature)

    def _getLeftBarline(self):
        barList = []
        # directly access _elements, as do not want to get any bars
        # in _endElements
        for e in self._elements:
            if 'Barline' in e.classes: # take the first
                if self.elementOffset(e) == 0.0:
                    barList.append(e)
                    break
        if len(barList) == 0:
            return None
        else:
            return barList[0]

    def _setLeftBarline(self, barlineObj):
        insert = True
        if common.isStr(barlineObj):
            barlineObj = bar.Barline(barlineObj)
            barlineObj.location = 'left'
        elif barlineObj is None: # assume removal
            insert = False
        else: # assume an Barline object
            barlineObj.location = 'left'

        oldLeftBarline = self._getLeftBarline()
        if oldLeftBarline is not None:
            #environLocal.printDebug(['_setLeftBarline()', 'removing left barline'])
            junk = self.pop(self.index(oldLeftBarline))
        if insert:
            #environLocal.printDebug(['_setLeftBarline()', 'inserting new left barline', barlineObj])
            self.insert(0, barlineObj)

    leftBarline = property(_getLeftBarline, _setLeftBarline,
        doc = '''
        Get or set the left barline, or the Barline object
        found at offset zero of the Measure.  Can be set either with a string
        representing barline style or a bar.Barline() object or None.
        Note that not all bars have
        barline objects here -- regular barlines don't need them.
        ''')

    def _getRightBarline(self):
        # TODO: Move to Stream or make setting .rightBarline, etc. on Stream raise an exception...
        # look on _endElements
        barList = []
        for e in self._endElements:
            if 'Barline' in e.classes: # take the first
                barList.append(e)
                break
        #barList = self.getElementsByClass(bar.Barline)
        if len(barList) == 0: # do this before searching for barQL
            return None
        else:
            return barList[0]

    def _setRightBarline(self, barlineObj):
        insert = True
        if common.isStr(barlineObj):
            barlineObj = bar.Barline(barlineObj)
            barlineObj.location = 'right'
        elif barlineObj is None: # assume removal
            insert = False
        else: # assume an Barline object
            barlineObj.location = 'right'

        # if a repeat, setup direction if not assigned
        if barlineObj is not None and 'Repeat' in barlineObj.classes:
            #environLocal.printDebug(['got barline obj w/ direction', barlineObj.direction])
            if barlineObj.direction in ['start', None]:
                barlineObj.direction = 'end'
        oldRightBarline = self._getRightBarline()

        if oldRightBarline is not None:
            #environLocal.printDebug(['_setRightBarline()', 'removing right barline'])
            junk = self.pop(self.index(oldRightBarline))
        # insert into _endElements
        if insert:
            self.storeAtEnd(barlineObj)

        #environLocal.printDebug(['post _setRightBarline', barlineObj, 'len of elements highest', len(self._endElements)])

    rightBarline = property(_getRightBarline, _setRightBarline,
        doc = '''Get or set the right barline, or the Barline object found at the offset equal to the bar duration.


        >>> b = bar.Barline('final')
        >>> m = stream.Measure()
        >>> print(m.rightBarline)
        None
        >>> m.rightBarline = b
        >>> m.rightBarline.style
        'final'


        OMIT_FROM_DOCS

        .measure currently isn't the same as the
        original measure...


        A string can also be used instead:


        >>> c = converter.parse("tinynotation: 3/8 C8 D E F G A B4.")
        >>> cm = c.makeMeasures()
        >>> cm.measure(1).rightBarline = 'light-light'
        >>> cm.measure(3).rightBarline = 'light-heavy'
        >>> #_DOCS_SHOW c.show()


        .. image:: images/stream_barline_demo.*
            :width: 211


        ''')

class Part(Stream):
    '''
    A Stream subclass for designating music that is considered a single part.

    When put into a Score object, Part objects are all collected in the `Score.parts`
    call.  Otherwise they mostly work like generic Streams.

    Generally the hierarchy goes: Score > Part > Measure > Voice, but you are not
    required to stick to this.

    Part groupings (piano braces, etc.) are found in the :ref:`moduleLayout` module
    in the :class:`~music21.layout.StaffGroup` Spanner object.

    OMIT_FROM_DOCS
    Check that this is True and works for everything before suggesting that it works!

    May be enclosed in a staff (for instance, 2nd and 3rd trombone
    on a single staff), may enclose staves (piano treble and piano bass),
    or may not enclose or be enclosed by a staff (in which case, it
    assumes that this part fits on one staff and shares it with no other
    part
    '''
    recursionType = 'flatten'
    
    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)
        self.staffLines = 5

    def makeAccidentals(self, alteredPitches=None,
         cautionaryPitchClass=True,
         cautionaryAll=False, inPlace=True,
         overrideStatus=False,
         cautionaryNotImmediateRepeat=True,
         lastNoteWasTied=False):
        '''
        This overridden method of Stream.makeAccidentals
        provides the management of passing pitches from
        a past Measure to each new measure for processing.

        TODO: by defaul inPlace should be False
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self
        # process make accidentals for each measure
        measureStream = returnObj.getElementsByClass('Measure')
        ksLast = None
        for i in range(len(measureStream)):
            m = measureStream[i]
            if m.keySignature is not None:
                ksLast = m.keySignature
            # if beyond the first measure, use the pitches from the last
            # measure for context
            if i > 0:
                pitchPastMeasure = measureStream[i-1].pitches
                if (measureStream[i-1] and
                        hasattr(measureStream[i-1][-1], "tie") and
                        measureStream[i-1][-1].tie is not None and
                        measureStream[i-1][-1].tie.type != 'stop'
                    ):
                    lastNoteWasTied = True
                else:
                    lastNoteWasTied = False
            else:
                pitchPastMeasure = None
                lastNoteWasTied = False

            m.makeAccidentals(pitchPastMeasure=pitchPastMeasure,
                              useKeySignature=ksLast, 
                              alteredPitches=alteredPitches,
                              searchKeySignatureByContext=False,
                              cautionaryPitchClass=cautionaryPitchClass,
                              cautionaryAll=cautionaryAll,
                              inPlace=True, # always, has have a copy or source
                              overrideStatus=overrideStatus,
                              cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat,
                              lastNoteWasTied=lastNoteWasTied)
        if not inPlace:
            return returnObj
        else: # in place
            return None





class PartStaff(Part):
    '''
    A Part subclass for designating music that is
    represented on a single staff but may only be one
    of many staves for a single part.
    '''
    def __init__(self, *args, **keywords):
        Part.__init__(self, *args, **keywords)


#
# class Performer(Stream):
#     '''
#     A Stream subclass for designating music to be performed by a
#     single Performer.  Should only be used when a single performer
#     performs on multiple parts.  E.g. Bass Drum and Triangle on separate
#     staves performed by one player.
#
#     a Part + changes of Instrument is fine for designating most cases
#     where a player changes instrument in a piece.  A part plus staves
#     with individual instrument changes could also be a way of designating
#     music that is performed by a single performer (see, for instance
#     the Piano doubling Celesta part in Lukas Foss's Time Cycle).  The
#     Performer Stream-subclass could be useful for analyses of, for instance,
#     how 5 percussionists chose to play a piece originally designated for 4
#     (or 6) percussionists in the score.
#     '''
#     # NOTE: not yet implemented
#     pass
#
#
class System(Stream):
    '''
    Totally optional and used only in OMR and Capella: a designation that all the
    music in this Stream belongs in a single system.

    The system object has two attributes, systemNumber (which number is it)
    and systemNumbering which says at what point the numbering of
    systems resets.  It can be either "Score" (default), "Opus", or "Page".
    '''
    systemNumber = 0
    systemNumbering = "Score" # or Page; when do system numbers reset?


class Score(Stream):
    """
    A Stream subclass for handling multi-part music.

    Almost totally optional (the largest containing Stream in a piece could be
    a generic Stream, or a Part, or a Staff).  And Scores can be
    embedded in other Scores (in fact, our original thought was to call
    this class a Fragment because of this possibility of continuous
    embedding; though it's probably better to embed a Score in an Opus),
    but we figure that many people will like calling the largest
    container a Score and that this will become a standard.
    """
    recursionType = 'elementsOnly'

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)
        # while a metadata object is often expected, adding here prob not
        # a good idea.
        #self.insert(0, metadata.Metadata())


    def _getParts(self):
#         return self.getElementsByClass('Part')
        if 'parts' not in self._cache or self._cache['parts'] is None:
            self._cache['parts'] = self.getElementsByClass('Part',
                                                           returnStreamSubClass=True)
        return self._cache['parts']

    parts = property(_getParts,
        doc='''
        Return all :class:`~music21.stream.Part` objects in a :class:`~music21.stream.Score`.

        It filters out all other things that might be in a Score object, such as Metadata
        returning just the Parts.


        >>> s = corpus.parse('bach/bwv66.6')
        >>> partStream = s.parts
        >>> partStream.classes
        ('Score', 'Stream', 'StreamCoreMixin', 'Music21Object', 'object')
        >>> len(partStream)
        4

        The partStream object is a full `stream.Score` object, thus the elements inside it
        can be accessed by index number or by id string, or iterated over:

        >>> partStream[0]
        <music21.stream.Part Soprano>
        >>> partStream['Alto']
        <music21.stream.Part Alto>
        >>> for p in partStream:
        ...     print(p.id)
        Soprano
        Alto
        Tenor
        Bass
        ''')

    def measures(self, numberStart, numberEnd,
        collect=('Clef', 'TimeSignature', 'Instrument', 'KeySignature'), 
        gatherSpanners=True, searchContext=False, ignoreNumbers=False):
        '''This method override the :meth:`~music21.stream.Stream.measures` method on Stream. This creates a new Score stream that has the same measure range for all Parts.

        The `collect` argument is a list of classes that will be collected.


        >>> s = corpus.parse('bwv66.6')
        >>> post = s.measures(3,5) # range is inclusive, i.e., [3, 5]
        >>> len(post.parts)
        4
        >>> len(post.parts[0].getElementsByClass('Measure'))
        3
        >>> len(post.parts[1].getElementsByClass('Measure'))
        3
        '''
        post = Score()
        # this calls on Music21Object, transfers groups, id if not id(self)
        post.mergeAttributes(self)
        # note that this will strip all objects that are not Parts
        for p in self.parts:
            # insert all at zero
            measuredPart = p.measures(numberStart, numberEnd,
                        collect, gatherSpanners=gatherSpanners, ignoreNumbers=ignoreNumbers)
            post.insert(0, measuredPart)
        # must manually add any spanners; do not need to add .flat, as Stream.measures will handle lower level
        if gatherSpanners:
            spStream = self.spanners
            for sp in spStream:
                post.insert(0, sp)
                
        post.derivation.client = post
        post.derivation.origin = self
        post.derivation.method = 'measures'
        return post


    def measure(self, measureNumber,
        collect=(clef.Clef, meter.TimeSignature,
        instrument.Instrument, key.KeySignature), gatherSpanners=True, ignoreNumbers=False):
        '''
        Given a measure number,
        return a single :class:`~music21.stream.Measure` object if the Measure number exists, otherwise return None.


        This method overrides the :meth:`~music21.stream.Stream.measures` method on Stream.
        This creates a new Score stream that has the
        same measure range for all Parts.


        >>> from music21 import corpus
        >>> a = corpus.parse('bach/bwv324.xml')
        >>> # contains 1 measure
        >>> len(a.measure(3).parts[0].getElementsByClass('Measure'))
        1
        '''

        post = Score()
        # this calls on Music21Object, transfers id, groups
        post.mergeAttributes(self)
        # note that this will strip all objects that are not Parts
        for p in self.getElementsByClass('Part'):
            # insert all at zero
            mStream = p.measures(measureNumber, measureNumber,
                collect=collect, gatherSpanners=gatherSpanners, ignoreNumbers=ignoreNumbers)
            if len(mStream) > 0:
                post.insert(0, mStream)

        if gatherSpanners:
            spStream = self.spanners
            for sp in spStream:
                post.insert(0, sp)

        post.derivation.client = post
        post.derivation.origin = self
        post.derivation.method = 'measure'

        return post


    def expandRepeats(self):
        '''
        Expand all repeats, as well as all repeat indications
        given by text expressions such as D.C. al Segno.

        This method always returns a new Stream, with deepcopies
        of all contained elements at all level.
        '''
        post = self.cloneEmpty(derivationMethod='expandRepeats')
        # this calls on Music21Object, transfers id, groups
        post.mergeAttributes(self)

        # get all things in the score that are not Parts
        for e in self.iter.getElementsNotOfClass('Part'):
            eNew = copy.deepcopy(e) # assume that this is needed
            post.insert(self.elementOffset(e), eNew)

        for p in self.iter.getElementsByClass('Part'):
            # get spanners at highest level, not by Part
            post.insert(0, p.expandRepeats(copySpanners=False))

        #spannerBundle = spanner.SpannerBundle(post.flat.spanners)
        spannerBundle = post.spannerBundle # use property
        # iterate over complete semi flat (need containers); find
        # all new/old pairs
        for e in post.recurse(skipSelf=True):
            # update based on last id, new object
            if e.sites.hasSpannerSite():
                origin = e.derivation.origin
                if (origin is not None and e.derivation.method == '__deepcopy__'):
                    spannerBundle.replaceSpannedElement(id(origin), e)
        return post


    def measureOffsetMap(self, classFilterList=None):
        '''
        This Score method overrides the
        :meth:`~music21.stream.Stream.measureOffsetMap` method of Stream.
        This creates a map based on all contained Parts in this Score.
        Measures found in multiple Parts with the same offset will be
        appended to the same list.

        If no parts are found in the score, then the normal
        :meth:`~music21.stream.Stream.measureOffsetMap` routine is called.

        This method is smart and does not assume that all Parts
        have measures with identical offsets.
        '''
        offsetMap = {}
        parts = self.parts
        if len(parts) == 0:
            return Stream.measureOffsetMap(self, classFilterList)
        else:
            for p in parts:
                mapPartial = p.measureOffsetMap(classFilterList)
                #environLocal.printDebug(['mapPartial', mapPartial])
                for k in mapPartial:
                    if k not in offsetMap:
                        offsetMap[k] = []
                    for m in mapPartial[k]: # get measures from partial
                        if m not in offsetMap[k]:
                            offsetMap[k].append(m)
            return offsetMap

    def sliceByGreatestDivisor(self, inPlace=True, addTies=True):
        '''
        Slice all duration of all part by the minimum duration
        that can be summed to each concurrent duration.

        Overrides method defined on Stream.

        TODO: by defaul inPlace should be False
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        # find greatest divisor for each measure at a time
        # if no measures this will be zero
        mStream = returnObj.parts[0].getElementsByClass('Measure')
        mCount = len(mStream)
        if mCount == 0:
            mCount = 1 # treat as a single measure
        for i in range(mCount): # may be 1
            uniqueQuarterLengths = []
            for p in returnObj.getElementsByClass('Part'):
                if p.hasMeasures():
                    m = p.getElementsByClass('Measure')[i]
                else:
                    m = p # treat the entire part as one measure

                # collect all unique quarter lengths
                for e in m.notesAndRests:
                    #environLocal.printDebug(['examining e', i, e, e.quarterLength])
                    if e.quarterLength not in uniqueQuarterLengths:
                        uniqueQuarterLengths.append(e.quarterLength)

            # after ql for all parts, find divisor
            divisor = common.approximateGCD(uniqueQuarterLengths)
            #environLocal.printDebug(['Score.sliceByGreatestDivisor: got divisor from unique ql:', divisor, uniqueQuarterLengths])

            for p in returnObj.getElementsByClass('Part'):
                # in place: already have a copy if nec
                # must do on measure at a time
                if p.hasMeasures():
                    m = p.getElementsByClass('Measure')[i]
                else:
                    m = p # treat the entire part as one measure
                m.sliceByQuarterLengths(quarterLengthList=[divisor],
                    target=None, addTies=addTies, inPlace=True)
        del mStream # cleanup Streams
        returnObj.elementsChanged()
        return returnObj

    def partsToVoices(self, voiceAllocation=2, permitOneVoicePerPart=False, setStems=True):
        '''
        Given a multi-part :class:`~music21.stream.Score`,
        return a new Score that combines parts into voices.

        The `voiceAllocation` parameter sets the maximum number
        of voices per Part.

        The `permitOneVoicePerPart` parameter, if True, will encode a
        single voice inside a single Part, rather than leaving it as
        a single Part alone, with no internal voices.


        >>> s = corpus.parse('bwv66.6')
        >>> len(s.flat.notes)
        165
        >>> post = s.partsToVoices(voiceAllocation=4)
        >>> len(post.parts)
        1
        >>> len(post.parts[0].getElementsByClass('Measure')[0].voices)
        4
        >>> len(post.flat.notes)
        165

        '''
        bundle = []
        if common.isNum(voiceAllocation):
            voicesPerPart = voiceAllocation
            for pIndex, p in enumerate(self.parts):
                if pIndex % voicesPerPart == 0:
                    sub = []
                    sub.append(p)
                else:
                    sub.append(p)
                if pIndex % voicesPerPart == voicesPerPart - 1:
                    bundle.append(sub)
                    sub = []
            if sub != []: # get last
                bundle.append(sub)
        # else, assume it is a list of groupings
        elif common.isIterable(voiceAllocation):
            for group in voiceAllocation:
                sub = []
                # if a single entry
                if not common.isListLike(group):
                    # group is a single index
                    sub.append(self.parts[group])
                else:
                    for partId in group:
                        sub.append(self.parts[partId])
                bundle.append(sub)
        else:
            raise StreamException('incorrect voiceAllocation format: %s' % voiceAllocation)

        #environLocal.printDebug(['partsToVoices() bundle:', bundle])

        s = self.cloneEmpty(derivationMethod='partsToVoices')
        s.metadata = self.metadata

        for sub in bundle: # each sub contains parts
            if len(sub) == 1 and not permitOneVoicePerPart:
                # probably need to create a new part and measure
                s.insert(0, sub[0])
                continue

            pActive = Part()
            # iterate through each part
            for pIndex, p in enumerate(sub):
                # only check for measures once per part
                if pActive.hasMeasures():
                    hasMeasures = True
                else:
                    hasMeasures = False

                for mIndex, m in enumerate(p.getElementsByClass('Measure')):
                    #environLocal.printDebug(['pindex, p', pIndex, p, 'mIndex, m', mIndex, m, 'hasMeasures', hasMeasures])
                    # only create measures if non already exist
                    if not hasMeasures:
                        #environLocal.printDebug(['creating measure'])
                        mActive = Measure()
                        # some attributes may be none
                        # note: not copying here; and first part read will provide
                        # attributes; possible other parts may have other attributes
                        mActive.mergeAttributes(m)
                        mActive.mergeElements(m, classFilterList=('Bar', 'TimeSignature', 'Clef', 'KeySignature'))

#                         if m.timeSignature is not None:
#                             mActive.timeSignature = m.timeSignature
#                         if m.keySignature is not None:
#                             mActive.keySignature = m.keySignature
#                         if m.clef is not None:
#                             mActive.clef = m.clef
                    else:
                        mActive = pActive.getElementsByClass('Measure')[mIndex]

                    # transfer elements into a voice
                    v = Voice()
                    v.id = pIndex
                    # for now, just take notes, including rests
                    for e in m.notesAndRests: #m.getElementsByClass():
                        if setStems:
                            if hasattr(e, 'stemDirection'):
                                if pIndex % 2 == 0:
                                    e.stemDirection = 'up'
                                else:
                                    e.stemDirection = 'down'
                        v.insert(e.getOffsetBySite(m), e)
                    # insert voice in new  measure
                    #environLocal.printDebug(['inserting voice', v, v.id, 'into measure', mActive])
                    mActive.insert(0, v)
                    #mActive.show('t')
                    # only insert measure if new part does not already have measures
                    if not hasMeasures:
                        pActive.insert(m.getOffsetBySite(p), mActive)

            s.insert(0, pActive)
            pActive = None
        return s

    def implode(self):
        '''
        Reduce a polyphonic work into two staves.

        Currently, this is just a synonym for `partsToVoices` with
        `voiceAllocation = 2`, and `permitOneVoicePerPart = False`,
        but someday this will have better methods for finding identical
        parts, etc.
        '''
        voiceAllocation = 2
        permitOneVoicePerPart = False

        return self.partsToVoices(voiceAllocation=voiceAllocation,
            permitOneVoicePerPart=permitOneVoicePerPart)



    def flattenParts(self, classFilterList=('Note', 'Chord')):
        '''
        Given a Score, combine all Parts into a single Part
        with all elements found in each Measure of the Score.

        The `classFilterList` can be used to specify which objects
        contained in Measures are transferred.

        It also flattens all voices within a part.

        >>> s = corpus.parse('bwv66.6')
        >>> len(s.parts)
        4
        >>> len(s.flat.notes)
        165
        >>> post = s.flattenParts()
        >>> 'Part' in post.classes
        True
        >>> len(post.flat.notes)
        165
        '''
        post = self.parts[0].measureTemplate(fillWithRests=False)
        for i, m in enumerate(post.getElementsByClass('Measure')):
            for p in self.parts:
                mNew = copy.deepcopy(p.getElementsByClass('Measure')[i]).flat
                for e in mNew:
                    match = False
                    for cf in classFilterList:
                        if cf in e.classes:
                            match = True
                            break
                    if match:
                        m.insert(e.getOffsetBySite(mNew), e)
        return post


    def makeNotation(self, meterStream=None, refStreamOrTimeRange=None,
                        inPlace=False, bestClef=False, **subroutineKeywords):
        '''
        This method overrides the makeNotation method on Stream,
        such that a Score object with one or more Parts or Streams
        that may not contain well-formed notation may be transformed
        and replaced by well-formed notation.

        If `inPlace` is True, this is done in-place;
        if `inPlace` is False, this returns a modified deep copy.
        '''
        if inPlace:
            returnStream = self
        else:
            returnStream = copy.deepcopy(self)

        # do not assume that we have parts here
        if self.hasPartLikeStreams():
            for s in returnStream.getElementsByClass('Stream'):
                # process all component Streams inPlace
                s.makeNotation(meterStream=meterStream, 
                               refStreamOrTimeRange=refStreamOrTimeRange, 
                               inPlace=True, 
                               bestClef=bestClef, 
                               **subroutineKeywords)
            # note: while the local-streams have updated their caches, the
            # containing score has an out-of-date cache of flat.
            # this, must call elements changed
            returnStream.elementsChanged()
        else: # call the base method
            super(Score, self).makeNotation(meterStream=meterStream, 
                                            refStreamOrTimeRange=refStreamOrTimeRange, 
                                            inPlace=True, 
                                            bestClef=bestClef, 
                                            **subroutineKeywords)

        if inPlace:
            return None
        else:
            return returnStream


# this was commented out as it is not immediately needed
# could be useful later in a variety of contexts
#     def mergeStaticNotes(self, attributesList=['pitch'], inPlace=False):
#         '''Given a multipart work, look to see if the next verticality causes a change in one or more attributes, as specified by the `attributesList` parameter. If no change is found, merge the next durations with the previous.
#
#         Presently, this assumes that all parts have the same number of notes. This must thus be used in conjunction with sliceByGreatestDivisor() to properly match notes between different parts.
#         '''
#
#         if not inPlace: # make a copy
#             returnObj = copy.deepcopy(self)
#         else:
#             returnObj = self
#
#         # if no measures this will be zero
#         mStream = returnObj.parts[0].getElementsByClass('Measure')
#         mCount = len(mStream)
#         if mCount == 0:
#             mCount = 1 # treat as a single measure
#
#         # step through measures, or one whole part
#         for i in range(mCount): # may be zero
#             #for p in returnObj.getElementsByClass('Part'):
#             # use the top-most part as the guide
#             p = returnObj.getElementsByClass('Part')[0]
#             if p.hasMeasures():
#                 mGuide = p.getElementsByClass('Measure')[i]
#             else:
#                 mGuide = p # treat the entire part as one measure
#
#             mergePairTerminus = [] # store last of merge pair
#             j = 0
#             # only look at everything up to one before the last
#             while j < len(mGuide.notesAndRests) - 1:
#                 jNext = j + 1
#                 # gather all attributes from this j for each part
#                 # doing this by index
#                 compare = []
#                 compareNext = []
#
#                 for pStream in returnObj.getElementsByClass('Part'):
#                     #environLocal.printDebug(['handling part', pStream])
#                     if pStream.hasMeasures():
#                         m = pStream.getElementsByClass('Measure')[i]
#                     else:
#                         m = pStream # treat the entire part as one measure
#                     for attr in attributesList:
#                         compare.append(getattr(m.notesAndRests[j], attr))
#                         compareNext.append(getattr(m.notesAndRests[jNext], attr))
#                 environLocal.printDebug(['compare, compareNext', compare, compareNext])
#
#                 if compare == compareNext:
#                     if j not in mergePairTerminus:
#                         mergePairTerminus.append(j)
#                     mergePairTerminus.append(jNext)
#                 j += 1
#             environLocal.printDebug(['mergePairTerminus', mergePairTerminus])
#
#             # collect objects to merged in continuous groups
#             # store in a list of lists; do each part one at a time
#             for pStream in returnObj.getElementsByClass('Part'):
#                 mergeList = []
#                 for q in mergePairTerminus:
#                     pass

#    def makeNotation(self, *args, **keywords):
#        '''
#
#        >>> s = stream.Score()
#        >>> p1 = stream.Part()
#        >>> p2 = stream.Part()
#        >>> n = note.Note('g')
#        >>> n.quarterLength = 1.5
#        >>> p1.repeatAppend(n, 10)
#        >>> n2 = note.Note('f')
#        >>> n2.quarterLength = 1
#        >>> p2.repeatAppend(n2, 15)
#
#        >>> s.insert(0, p1)
#        >>> s.insert(0, p2)
#        >>> sMeasures = s.makeNotation()
#        >>> len(sMeasures.parts)
#        2
#        '''
#        return Stream.makeNotation(self, *args, **keywords)


class Opus(Stream):
    '''
    A Stream subclass for handling multi-work music encodings.
    Many ABC files, for example, define multiple works or parts within a single file.

    Opus objects can contain multiple Score objects, or even other Opus objects!
    '''
    recursionType = 'elementsOnly'

    #TODO: get by title, possibly w/ regex

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)

    def getNumbers(self):
        '''
        Return a list of all numbers defined in this Opus.

        >>> o = corpus.parse('josquin/oVenusBant')
        >>> o.getNumbers()
        ['1', '2', '3']
        '''
        post = []
        for s in self.iter.getElementsByClass('Score'):
            post.append(s.metadata.number)
        return post

    def getScoreByNumber(self, opusMatch):
        '''
        Get Score objects from this Stream by number.
        Performs title search using the
        :meth:`~music21.metadata.Metadata.search` method,
        and returns the first result.


        >>> o = corpus.parse('josquin/oVenusBant')
        >>> o.getNumbers()
        ['1', '2', '3']
        >>> s = o.getScoreByNumber(2)
        >>> s.metadata.title
        'O Venus bant'
        >>> s.metadata.alternativeTitle
        'Tenor'
        '''
        for s in self.iter.getElementsByClass('Score'):
            match, unused_field = s.metadata.search(opusMatch, 'number')
            if match:
                return s

#             if s.metadata.number == opusMatch:
#                 return s
#             elif s.metadata.number == str(opusMatch):
#                 return s

    def getScoreByTitle(self, titleMatch):
        '''
        Get Score objects from this Stream by a title.
        Performs title search using the :meth:`~music21.metadata.Metadata.search` method,
        and returns the first result.


        >>> o = corpus.parse('essenFolksong/erk5')
        >>> s = o.getScoreByTitle('Vrienden, kommt alle gaere')
        >>> s = o.getScoreByTitle('(.*)kommt(.*)') # regular expression
        >>> s.metadata.title
        'Vrienden, kommt alle gaere'
        '''
        for s in self.getElementsByClass('Score'):
            match, unused_field = s.metadata.search(titleMatch, 'title')
            if match:
                return s

    def _getScores(self):
        return self.getElementsByClass(Score)

    scores = property(_getScores,
        doc='''
        Return all :class:`~music21.stream.Score` objects
        in a :class:`~music21.stream.Opus`.
        ''')

    def mergeScores(self):
        '''
        Some Opus objects represent numerous scores
        that are individual parts of the same work.
        This method will treat each contained Score as a Part,
        merging and returning a single Score with merged Metadata.


        >>> from music21 import corpus
        >>> o = corpus.parse('josquin/milleRegrets')
        >>> s = o.mergeScores()
        >>> s.metadata.title
        'Mille regrets'
        >>> len(s.parts)
        4
        '''
        sNew = Score()
        mdNew = metadata.Metadata()

        for s in self.scores:
            p = s.parts[0]  # assuming only one part
            sNew.insert(0, p)

            md = s.metadata
            # presently just getting the first of attributes encountered
            if md is not None:
                #environLocal.printDebug(['subscore meta data', md, 'md.composer', md.composer, 'md.title', md.title])
                if md.title is not None and mdNew.title is None:
                    mdNew.title = md.title
                if md.composer is not None and mdNew.composer is None:
                    mdNew.composer = md.composer

        sNew.insert(0, mdNew)
        return sNew

    #--------------------------------------------------------------------------
    def write(self, fmt=None, fp=None):
        '''
        Displays an object in a format provided by the fmt argument or, if not
        provided, the format set in the user's Environment.

        This method overrides the behavior specified in
        :class:`~music21.base.Music21Object` for all formats besides explicit
        lily.x calls.

        '''
        if fmt is not None and 'lily' in fmt:
            return Stream.write(self, fmt, fp)
        elif common.runningUnderIPython():
            return Stream.write(self, fmt, fp)
        else:
            for s in self.scores:
                s.write(fmt=fmt, fp=fp)

    def show(self, fmt=None, app=None):
        '''
        Show an Opus file.
        
        This method overrides the behavior specified in
        :class:`~music21.base.Music21Object` for all
        formats besides explicit lily.x calls. or when running under IPython notebook.
        '''
        if fmt is not None and 'lily' in fmt:
            return Stream.show(self, fmt, app)
        elif common.runningUnderIPython():
            return Stream.show(self, fmt, app)
        else:
            for s in self.scores:
                s.show(fmt=fmt, app=app)


#------------------------------------------------------------------------------
# Special stream sub-classes that are instantiated as hidden attributes within
# other Music21Objects (i.e., Spanner and Variant).


class SpannerStorage(Stream):
    '''
    For advanced use. This Stream subclass is only used
    inside of a Spanner object to provide object storage
    of connected elements (things the Spanner spans).

    This subclass name can be used to search in an
    object's .sites and find any and all
    locations that are SpannerStorage objects.

    A `spannerParent` keyword argument must be
    provided by the Spanner in creation.
    '''
    def __init__(self, *arguments, **keywords):
        Stream.__init__(self, *arguments, **keywords)

        # must provide a keyword argument with a reference to the spanner
        # parent could name spannerContainer or other?

        #environLocal.printDebug('keywords', keywords)
        # TODO: this might be better stored as weak ref

        self.spannerParent = None
        if 'spannerParent' in keywords:
            self.spannerParent = keywords['spannerParent']

    # NOTE: for serialization, this will need to properly tage
    # the spanner parent by updating the scaffolding code.


class VariantStorage(Stream):
    '''
    For advanced use. This Stream subclass is only
    used inside of a Variant object to provide object
    storage of connected elements (things the Variant
    defines).

    This subclass name can be used to search in an
    object's .sites and find any and all
    locations that are VariantStorage objects.

    A `variantParent` keyword argument must be provided
    by the Variant in creation.
    
    # TODO: rename to client
    
    '''
    def __init__(self, *arguments, **keywords):
        Stream.__init__(self, *arguments, **keywords)
        # must provide a keyword argument with a reference to the variant
        # parent
        self.variantParent = None
        if 'variantParent' in keywords:
            self.variantParent = keywords['variantParent']

#------------------------------------------------------------------------------


# class GraceStream(Stream):
#     '''A Stream used to contain the notes that make up a section of grace notes.
#     '''
#     # from the outside, this needs to have duration of zero
#     # this is achieved by using by making every note added to this stream
#     # a grace duration; does this mean we make copies of each object,
#     # or change in place?
#     # might have utilities for a normal Stream to be transformed into a
#     # grace stream
#
#     def __init__(self, givenElements=None, *args, **keywords):
#         Stream.__init__(self, givenElements=givenElements, *args, **keywords)
#
#
#     def append(self, others):
#         '''Overridden append method that copies appended elements and replaces their duration with a GraceDuration.
#         '''
#         if not common.isListLike(others):
#             others = [others]
#         # replace and edit in place
#         othersEdited = []
#         for e in others:
#             e = copy.deepcopy(e)
#             e.duration = e.duration.getGraceDuration()
#             #environLocal.printDebug([
#             #    'appending GraceStream, before calling base class',
#             #    e.quarterLength, e.duration.quarterLength])
#             othersEdited.append(e)
#
#         # call bass class append with elements modified durations
#         Stream.append(self, othersEdited)
#
#




#------------------------------------------------------------------------------


class Test(unittest.TestCase):
    '''
    Note: all Stream tests are found in test/testStream.py
    '''

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        for part in sys.modules[self.__module__].__dict__:
            if part.startswith('_') or part.startswith('__'):
                continue
            elif part in ['Test', 'TestExternal']:
                continue
            elif callable(part):
                #environLocal.printDebug(['testing copying on', part])
                obj = getattr(self.__module__, part)()
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertNotEqual(a, obj)
                self.assertNotEqual(b, obj)


#------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Stream, Measure, Part, Score, Opus]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof
