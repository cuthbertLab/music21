#-------------------------------------------------------------------------------
# Name:         stream.py
# Purpose:      base classes for dealing with groups of positioned objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''The :class:`~music21.stream.Stream` and its subclasses, a subclass of the :class:`~music21.base.Music21Object`, is the fundamental container of offset-positioned notation and musical elements in music21. Common Stream subclasses, such as the :class:`~music21.stream.Measure` and :class:`~music21.stream.Score` objects, are defined in this module. 
'''


import copy, types, random
import doctest, unittest
import sys
from copy import deepcopy


import music21 # needed to do fully-qualified isinstance name checking

from music21 import bar
from music21 import common
from music21 import clef
from music21 import chord
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import layout
from music21 import lily as lilyModule
from music21 import metadata
from music21 import meter
from music21 import musicxml as musicxmlMod
from music21.musicxml import translate as musicxmlTranslate
from music21 import midi as midiModule
from music21.midi import translate as midiTranslate
from music21 import note
from music21 import spanner
from music21 import tie
from music21 import metadata


from music21 import environment
_MOD = "stream.py"
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------

class StreamException(Exception):
    pass

#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
class StreamIterator(object):
    '''A simple Iterator object used to handle iteration of Streams and other 
    list-like objects. 
    '''
    def __init__(self, srcStream):
        self.srcStream = srcStream
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        # calling .elements here will sort if autoSort = True
        # thus, this does not need to sort or check autoSort status
        if self.index >= len(self.srcStream):
            del self.srcStream
            raise StopIteration
        # here, the .elements property concatenates both ._elements and 
        # ._endElements; this may be a performance detriment
        post = self.srcStream.elements[self.index]
        # here, the activeSite of extracted element is being set to Stream
        # that is the source of the iteration
        post.activeSite = self.srcStream
        self.index += 1
        return post


#-------------------------------------------------------------------------------

class Stream(music21.Music21Object):
    '''
    This is the fundamental container for Music21Objects; objects may be ordered and/or placed in time based on offsets from the start of this container's offset. 
    
    Like the base class, Music21Object, Streams have offsets, priority, id, and groups
    they also have an elements attribute which returns a list of elements; 
    
    The Stream has a duration that is usually the 
    release time of the chronologically last element in the Stream (that is,
    the highest onset plus duration of any element in the Stream).
    However, it can either explicitly set in which case we say that the
    duration is unlinked

    Streams may be embedded within other Streams.
    
    OMIT_FROM_DOCS
    TODO: Get Stream Duration working -- should be the total length of the 
    Stream. -- see the ._getDuration() and ._setDuration() methods
    '''

    # TODO: this and similar attributes are to replaced by checks to .classes
    isMeasure = False

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['append', 'insert', 'insertAndShift', 
        'notes', 'pitches',
        'transpose', 
        'augmentOrDiminish', 'scaleOffsets', 'scaleDurations']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'isSorted': 'Boolean describing whether the Stream is sorted or not.',
    'autoSort': 'Boolean describing whether the Stream is automatically sorted by offset whenever necessary.',

    'isFlat': 'Boolean describing whether this Stream contains embedded sub-Streams or Stream subclasses (not flat).',

    'flattenedRepresentationOf': 'When this flat Stream is derived from another non-flat stream, a reference to the source Stream is stored here.',
    }


    def __init__(self, givenElements=None, *args, **keywords):
        music21.Music21Object.__init__(self)

        # self._elements stores ElementWrapper and Music21Object objects. 
        self._elements = [] 

        # self._endElements stores ElementWrapper and Music21Object found at
        # the highestTime of this Stream. 
        self._endElements = [] 

        self._unlinkedDuration = None

        self.isSorted = True
        self.autoSort = True
        self.isFlat = True  # does it have no embedded Streams

        # seems that this should be named with a leading lower case?
        # when deriving a flat stream, store a reference to the non-flat Stream          
        # from which this was taken
        self.flattenedRepresentationOf = None 
        
        self._cache = common.defHash()

        if givenElements is not None:
            for e in givenElements:
                self.insert(e)


    #---------------------------------------------------------------------------
    # sequence like operations

    # if we want to have all the features of a mutable sequence, 
    # we should implement
    # append(), count(), index(), extend(), insert(), 
    # pop(), remove(), reverse() and sort(), like Python standard list objects.
    # But we're not there yet.

    def __len__(self):
        '''Get the total number of elements
        Does not recurse into objects

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> len(a)
        4

        >>> b = stream.Stream()
        >>> for x in range(4):
        ...     b.insert(deepcopy(a) ) # append streams
        >>> len(b)
        4
        >>> len(b.flat)
        16
        '''
        return len(self._elements) + len(self._endElements)

    def __iter__(self):
        '''
        A Stream can return an iterator.  Same as running x in a.elements
        '''
        return StreamIterator(self)


    def __getitem__(self, key):
        '''Get an ElementWrapper from the stream in current order; sorted if isSorted is True,
        but not necessarily.
        
        if an int is given, returns that index
        if a class is given, it runs getElementsByClass and returns that list
        if a string is given it first runs getElementById on the stream then if that
             fails, getElementsByGroup on the stream returning that list.

        ## maybe it should, but does not yet:    if a float is given, returns the element at that offset

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Rest(), range(6))
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

        if common.isNum(key):
            # TODO: using self._elements here will retain activeSite, as opposed   
            # to using .elements
            e = self.elements[key]
            e.activeSite = self
            return e
    
        elif isinstance(key, slice): # get a slice of index values
            # manually inserting elements is critical to setting the element
            # locations
            found = self.__class__()
            for e in self.elements[key]:
                found.insert(e.getOffsetBySite(self), e)
            found._elementsChanged()
            return found

        elif common.isStr(key):
            # first search id, then search groups
            idMatch = self.getElementById(key)
            if idMatch is not None:
                return idMatch
            else: # search groups, return first element match
                groupStream = self.getElementsByGroup(key)
                if len(groupStream) > 0:
                    return groupStream
                else:
                    raise KeyError('provided key (%s) does not match any id or group' % key)
        elif isinstance(key, type(type)):
            # assume it is a class name
            classStream = self.getElementsByClass(key)
            if len(classStream) > 0:
                return classStream
            else:
                raise KeyError('provided class (%s) does not match any contained Objects' % key)


#     def __del__(self):
#         #environLocal.printDebug(['calling __del__ from Stream', self])
#         # this is experimental
#         # this did not offer improvements, and raised a number of errors
#         siteId = id(self)
#         for e in self._elements:
#             e.removeLocationBySiteId(siteId)


    #---------------------------------------------------------------------------
    # adding and editing Elements and Streams -- all need to call _elementsChanged
    # most will set isSorted to False

    def _elementsChanged(self):
        '''
        Call any time _elements is changed. Called by methods that add or change
        elements.

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.isFlat
        True
        >>> a._elements.append(stream.Stream())
        >>> a._elementsChanged()
        >>> a.isFlat
        False
        '''
        self.isSorted = False
        self.isFlat = True
        # do not need to look in _endElements, as no Streams
        # should be found there (they have a Duration)
        for e in self._elements:
            # only need to find one case, and if so, no longer flat
            # fastest method here is isinstance()
            if isinstance(e, Stream): 
            #if hasattr(e, 'elements'):
                self.isFlat = False
                break
        # resetting the cache removes lowest and highest time storage
        # a slight performance optimization: not creating unless needed
        if len(self._cache) > 0:
            self._cache = common.defHash()

    def _getElements(self):
        # this method is now important, in that it combines self._elements
        # and self._endElements
        if not self.isSorted and self.autoSort:
            self.sort() # will set isSorted to True

        if self._cache["elements"] == None:
            # this list concatenation may take time; thus, only do when
            # _elementsChanged has been called
            self._cache["elements"] =  self._elements + self._endElements

        return self._cache["elements"]

        #return self._elements + self._endElements
   
    def _setElements(self, value):
        '''
        TODO: this should be removed, as this is a bad way to add elements, as locations are not set properly. 

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note("C"), range(10))
        >>> b.offset = 6
        >>> c = stream.Stream()
        >>> c.repeatInsert(note.Note("C"), range(10))
        >>> c.offset = 12
        >>> b.insert(c)
        >>> b.isFlat
        False
        >>> a.isFlat
        True
        >>> a.elements = b.elements
        >>> a.isFlat
        False
        '''
        self._elements = value
        self._elementsChanged()
        return value
        
    elements = property(_getElements, _setElements, 
        doc='''The low-level storage list of all Streams. Directly getting, setting, and manipulating this list is reserved for advanced usage. 
        ''')

    def __setitem__(self, key, value):
        '''Insert items at index positions. Index positions are based
        on position in self.elements. 

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note("C"), range(10))
        >>> b.offset = 6
        >>> c = stream.Stream()
        >>> c.repeatInsert(note.Note("C"), range(10))
        >>> c.offset = 12
        >>> b.insert(c)
        >>> a.isFlat
        True
        >>> a[3] = b
        >>> a.isFlat
        False
        '''
        self._elements[key] = value
        storedIsFlat = self.isFlat
        self._elementsChanged()

        if isinstance(value, Stream): 
            self.isFlat = False
        else:
            self.isFlat = storedIsFlat


    def __delitem__(self, key):
        '''Delete items at index positions. Index positions are based
        on position in self.elements. 

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> del a[0]
        >>> len(a)
        9
        '''
        del self._elements[key]
        self._elementsChanged()


    def __add__(self, other):
        '''Add, or concatenate, two Streams.

        Presently, this does not manipulate the offsets of the incoming elements to actually be at the end of the Stream. This may be a problem that makes this method not so useful?

        >>> from music21 import *
        >>> a = stream.Part()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Note("G"), range(10))
        >>> c = a + b   
        >>> c.pitches # autoSort is True, thus a sorted version results
        [C, G, C, G, C, G, C, G, C, G, C, G, C, G, C, G, C, G, C, G]
        >>> len(c.notes)
        20


        The autoSort of the first stream becomes the autoSort of the
        destination.  The class of the first becomes the class of the destination.
        

        >>> a.autoSort = False
        >>> d = a + b
        >>> d.pitches
        [C, C, C, C, C, C, C, C, C, C, G, G, G, G, G, G, G, G, G, G]
        >>> d.__class__.__name__
        'Part'
        '''
        s = self.__class__()
        s.autoSort = self.autoSort
        # may want to keep activeSite of source Stream?
        #s.elements = self._elements + other._elements
        # need to iterate over elements and re-assign to create new locations
        for e in self._elements:
            s.insert(e.getOffsetBySite(self), e)
        for e in other._elements:
            s.insert(e.getOffsetBySite(other), e)
        #s._elementsChanged()
        return s


    def hasElement(self, obj):
        '''Return True if an element, provided as an argument, is contained in this Stream.

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> s.append(n1)
        >>> s.hasElement(n1)
        True
        '''
        for e in self._elements:
            if id(e) == id(obj): 
                return True
        for e in self._endElements:
            if id(e) == id(obj): 
                return True
        return False


    def mergeElements(self, other, classFilterList=[]):
        '''Given another Stream, store references of each element in the other Stream in this Stream. This does not make copies of any elements, but simply stores all of them in this Stream.

        Optionally, provide a list of classes to exclude with the `classFilter` list. 

        This method provides functionality like a shallow copy, but manages locations properly, only copies elements, and permits filtering by class type. 

        >>> from music21 import *
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
            match = False
            for c in classFilterList:
                if c in e.classes:
                    match = True
                    break
            if len(classFilterList) == 0 or match:
                self.insert(e.getOffsetBySite(other), e)
        for e in other._endElements:
            match = False
            for c in classFilterList:
                if c in e.classes:
                    match = True
                    break
            if len(classFilterList) == 0 or match:
                self.storeAtEnd(e)
        #self._elementsChanged()


    def getElementByObjectId(self, objId):
        '''Low-level tool to get an element based only on the object id. This does not yet handle ElementWrapper objects
        '''
        # TODO: refactor to handle possibility of multiple values
        for e in self._elements:
            if id(e) == objId: 
                return e
        for e in self._endElements:
            if id(e) == objId: 
                return e
        return None


    def indexList(self, obj, firstMatchOnly=False):
        '''Return a list of one or more index values where the supplied object is found on this Stream's `elements` list. 

        To just return the first matched index, set `firstMatchOnly` to True.

        The `obj` parameter may be an object or an id of an object. 

        No matches are found, an empty list is returned.

        Matching is based exclusively on id() of objects.

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')

        >>> s.insert(0, n1)
        >>> s.insert(5, n2)
        >>> len(s)
        2
        >>> s.indexList(n1)
        [0]
        >>> s.indexList(n2)
        [1]
        '''
        # NOTE: this supports multiple instances of the same object in one 
        # stream. to be developed.
        if not self.isSorted and self.autoSort:
            self.sort() # will set isSorted to True
        if common.isNum(obj):
            objId = obj
        else:
            objId = id(obj)

        iMatch = []
        elements = self.elements # store once as concatenating
        for i in range(len(elements)):
            if id(elements[i]) == objId:
                iMatch.append(i)
            # for object wrappers
            elif (hasattr(elements[i], "obj") and obj == elements[i].obj):
                iMatch.append(i)
            if firstMatchOnly and len(iMatch) > 0:
                break
        return iMatch

    def index(self, obj):
        '''Return the first matched index for the specified object.

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> fSharp = note.Note("F#")
        >>> a.repeatInsert(note.Note("A#"), range(10))
        >>> a.append(fSharp)
        >>> a.index(fSharp)
        10
        '''
        iMatch = self.indexList(obj, firstMatchOnly=True)
        if len(iMatch) == 0:
            raise ValueError("Could not find object in index")
        else:
            return iMatch[0] # only need first returned index

    def remove(self, target, firstMatchOnly=True):
        '''Remove an object from this Stream. Additionally, this Stream is removed from the object's sites in :class:`~music21.base.DefinedContexts`.

        By default, only the first match is removed. This can be adjusted with the `firstMatchOnly` parameters. 

        >>> from music21 import *
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
        '''
        iMatch = self.indexList(target, firstMatchOnly=firstMatchOnly)
        match = []
        for i in iMatch:
            # remove from stream with pop with index
            match.append(self._elements.pop(i))

        if len(iMatch) > 0:
            self._elementsChanged()

        # after removing, need to remove self from locations reference 
        # and from activeSite reference, if set; this is taken care of with the 
        # Music21Object method
        for obj in match:
            obj.removeLocationBySite(self)


    def pop(self, index):
        '''Return and remove the object found at the user-specified index value. Index values are those found in `elements` and are not necessary offset order. 

        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> junk = a.pop(0)
        >>> len(a)
        9
        '''
        eLen = len(self._elements)
        # if less then base length, its in _elements
        if index < eLen:
            post = self._elements.pop(index)
        else: # its in the _endElements 
            post = self._endElements.pop(index - eLen)

        self._elementsChanged()
        # remove self from locations here only if
        # there are no further locations
        post.removeLocationBySite(self)
        return post

    def __deepcopy__(self, memo=None):
        '''This produces a new, independent object.
        '''
        #environLocal.printDebug(['Stream calling __deepcopy__', self])

        # get all spanners at or below this level in a spanner bundle
        # it is possible to get spanners above this level too, by using 
        # getAllContextsByClass, but this would orphan the spanner from 
        # its container 
        # what happens here is that every time a Stream is copied, the 
        # all spanners bubble-up to the top of the point of copy; it is 
        # these that are copied
#         spannerBundle = spanner.SpannerBundle()
#         for sp in self.flat.spanners:
#         #for sp in self.flat.getAllContextsByClass('Spanner'):
#             # passing memo here might meant that lower-level Stream
#             # do not pass on spanners 
#             spannerBundle.append(copy.deepcopy(sp, memo))

        new = self.__class__()
        old = self
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue
            part = getattr(self, name)
                    
            # all subclasses of Music21Object that define their own
            # __deepcopy__ methods must be sure to not try to copy activeSite
            if name == '_activeSite':
                newValue = self.activeSite # keep a reference, not a deepcopy
                setattr(new, name, newValue)
            # attributes that require special handling
            elif name == 'flattenedRepresentationOf':
                # keep a reference, not a deepcopy
                newValue = self.flattenedRepresentationOf
                setattr(new, name, newValue)
            elif name == '_cache':
                continue # skip for now
            elif name == '_elements':
                # must manually add elements to 
                for e in self._elements: 
                    #environLocal.printDebug(['deepcopy()', e, 'old', old, 'id(old)', id(old), 'new', new, 'id(new)', id(new), 'old.hasElement(e)', old.hasElement(e), 'e.activeSite', e.activeSite, 'e.getSites()', e.getSites(), 'e.getSiteIds()', e.getSiteIds()], format='block')
                    # this will work for all with __deepcopy___
                    newElement = copy.deepcopy(e, memo)
                    # get the old offset from the activeSite Stream     
                    # user here to provide new offset
                    new.insert(e.getOffsetBySite(old), newElement, 
                               ignoreSort=True)

            elif name == '_endElements':
                # must manually add elements to 
                for e in self._endElements: 
                    # this will work for all with __deepcopy___
                    newElement = copy.deepcopy(e, memo)
                    # get the old offset from the activeSite Stream     
                    # user here to provide new offset
                    new.storeAtEnd(newElement, ignoreSort=True)
                
            elif isinstance(part, Stream):
                environLocal.printDebug(['found stream in dict keys', self,
                    part, name])
                raise StreamException('streams as attributes requires special handling')

            # use copy.deepcopy on all other elements, including contexts    
            else: 
                #environLocal.printDebug(['forced to use copy.deepcopy:',
                #    self, name, part])
                newValue = copy.deepcopy(part, memo)
                #setattr() will call the set method of a named property.
                setattr(new, name, newValue)

        # do after all other copying
        new._idLastDeepCopyOf = id(self)

        # after copying all elements
        # get all spanners at all levels from new: 
        # these have references to old objects
        # NOTE: it is likely that this only needs to be done at the highest
        # level of recursion, not on component Streams
        spannerBundle = spanner.SpannerBundle(new.flat.spanners)
        # iterate over complete semi flat (need containers); find
        # all new/old pairs
        for e in new.semiFlat:
            # update based on last id, new object
            spannerBundle.replaceComponent(e._idLastDeepCopyOf, e)

        return new

    #---------------------------------------------------------------------------
    def _addElementPreProcess(self, element):
        '''Before adding an element, this method provides important checks to that element.

        Used by both insert() and append()
        '''
        # using id() here b/c we do not want to get __eq__ comparisons
        if element is self: # cannot add this Stream into itself
            raise StreamException("this Stream cannot be contained within itself")
        # if we do not purge locations here, we may have ids() for 
        # Stream that no longer exist stored in the locations entry
        # note that dead locations are also purged from DefinedContexts during
        # all get() calls. 
        element.purgeLocations()


    def insert(self, offsetOrItemOrList, itemOrNone=None, 
                     ignoreSort=False, setActiveSite=True):
        '''
        Inserts an item(s) at the given offset(s). 

        If `ignoreSort` is True then the inserting does not
        change whether the Stream is sorted or not (much faster if you're going to be inserting dozens
        of items that don't change the sort status)

        The `setActiveSite` parameter should nearly always be True; only for 
        advanced Stream manipulation would you not change 
        the activeSite after inserting an element. 
        
        Has three forms: in the two argument form, inserts an element at the given offset:
        
        >>> st1 = Stream()
        >>> st1.insert(32, note.Note("B-"))
        >>> st1._getHighestOffset()
        32.0
        
        In the single argument form with an object, inserts the element at its stored offset:
        
        >>> n1 = note.Note("C#")
        >>> n1.offset = 30.0
        >>> st1 = Stream()
        >>> st1.insert(n1)
        >>> st2 = Stream()
        >>> st2.insert(40.0, n1)
        >>> n1.getOffsetBySite(st1)
        30.0
        
        In single argument form with a list, the list should contain pairs that alternate
        offsets and items; the method then, obviously, inserts the items
        at the specified offsets:
        
        >>> n1 = note.Note("G")
        >>> n2 = note.Note("F#")
        >>> st3 = Stream()
        >>> st3.insert([1.0, n1, 2.0, n2])
        >>> n1.getOffsetBySite(st3)
        1.0
        >>> n2.getOffsetBySite(st3)
        2.0
        >>> len(st3)
        2

        OMIT_FROM_DOCS
        Raise an error if offset is not a number
        >>> Stream().insert("l","g")
        Traceback (most recent call last):
        StreamException: ...
        
        '''
        # normal approach: provide offset and item
        if itemOrNone != None:
            offset = offsetOrItemOrList
            item = itemOrNone            
        elif itemOrNone is None and isinstance(offsetOrItemOrList, list):
            i = 0
            while i < len(offsetOrItemOrList):
                offset = offsetOrItemOrList[i]
                item = offsetOrItemOrList[i+1]
                # recursively calling insert() here
                self.insert(offset, item, ignoreSort = ignoreSort)
                i += 2
            return
        # assume first arg is item, and that offset is local offset of object
        else:
            item = offsetOrItemOrList
            offset = item.offset # should this be getOffsetBySite(None)?

        #if not common.isNum(offset):
        try: # using float conversion instead of isNum for performance
            offset = float(offset)
        except ValueError:
            raise StreamException("offset %s must be a number", offset)

        # if not a Music21Object, embed
        if not isinstance(item, music21.Music21Object): 
            element = music21.ElementWrapper(item)
        else:
            element = item

        # checks of element is self; possibly performs additional checks
        self._addElementPreProcess(element)

        element.addLocation(self, offset)
        # need to explicitly set the activeSite of the element
        if setActiveSite:
            element.activeSite = self 

        if ignoreSort is False:
            if self.isSorted is True and self.highestTime <= offset:
                storeSorted = True
            else:
                storeSorted = False

        # could also do self.elements = self.elements + [element]
        self._elements.append(element)  
        self._elementsChanged() 

        if ignoreSort is False:
            self.isSorted = storeSorted

    def append(self, others):
        '''
        Add Music21Objects (including other Streams) to the Stream 
        (or multiple if passed a list)
        with offset equal to the highestTime (that is the latest "release" of an object), 
        that is, directly after the last element ends. 

        if the objects are not Music21Objects, they are wrapped in ElementWrappers

        runs fast for multiple addition and will preserve isSorted if True

        >>> a = Stream()
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
        >>> # since notes are not embedded in Elements here, their offset
        >>> # changes when added to a stream!
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
        
        Add a note that already has an offset set -- does nothing different!
        >>> n3 = note.Note("B-")
        >>> n3.offset = 1
        >>> n3.duration.quarterLength = 3
        >>> a.append(n3)
        >>> a.highestOffset, a.highestTime
        (18.0, 21.0)
        >>> n3.getOffsetBySite(a)
        18.0
        '''
        # store and increment highest time for insert offset
        highestTime = self.highestTime
        if not common.isListLike(others):
            # back into a list for list processing if single
            others = [others]

        for item in others:    
            # if not an element, embed
            if not isinstance(item, music21.Music21Object): 
                environLocal.printDebug(['wrapping item in ElementWrapper:', item])
                element = music21.ElementWrapper(item)
            else:
                element = item
    
            self._addElementPreProcess(element)
    
            # add this Stream as a location for the new elements, with the 
            # the offset set to the current highestTime
            element.addLocation(self, highestTime)
            # need to explicitly set the activeSite of the element
            element.activeSite = self 
            self._elements.append(element)  

            # this should look to the contained object duration
            if (hasattr(element, "duration") and 
                hasattr(element.duration, "quarterLength")):
                # increment highestTime by quarterlength
                highestTime += element.duration.quarterLength

        # does not change sorted state
        storeSorted = self.isSorted    
        self._elementsChanged()         
        self.isSorted = storeSorted



    def storeAtEnd(self, itemOrList, ignoreSort=False):
        '''
        Inserts an item or items at the end of the Stream, stored in the special _endElements

        As sorting is only by priority and class, cannot avoid setting isSorted to False. 
        
        '''
        if isinstance(itemOrList, list):
            i = 0
            for item in itemOrList:
                # recursively calling insert() here
                self.storeAtEnd(item, ignoreSort=ignoreSort)
            return
        else:
            item = itemOrList

        # if not a Music21Object, embed
        if not isinstance(item, music21.Music21Object): 
            element = music21.ElementWrapper(item)
        else:
            element = item

        # cannot support elements with Durations in the highest time list
        if element.duration != None and element.duration.quarterLength != 0:
            raise StreamException('cannot insert an object with a non-zero Duration into the highest time elements list')

        # checks of element is self; possibly performs additional checks
        self._addElementPreProcess(element)

        element.addLocation(self, 'highestTime')
        # need to explicitly set the activeSite of the element
        element.activeSite = self 

        # could also do self.elements = self.elements + [element]
        #self._elements.append(element)  
        self._endElements.append(element)  
        self._elementsChanged() 


    #---------------------------------------------------------------------------
    # all the following call either insert() or append()

    def insertAtNativeOffset(self, item):
        '''Inserts an item at the offset that was defined before the item was inserted into a Stream.

        That is item.getOffsetBySite(None); in fact, the entire code is self.insert(item.getOffsetBySite(None), item)

        >>> n1 = note.Note("F-")
        >>> n1.offset = 20.0
        >>> stream1 = Stream()
        >>> stream1.append(n1)
        >>> n1.getOffsetBySite(stream1)
        0.0
        >>> n1.offset
        0.0
        >>> stream2 = Stream()
        >>> stream2.insertAtNativeOffset(n1)
        >>> stream2[0].offset
        20.0
        >>> n1.getOffsetBySite(stream2)
        20.0
        '''
        self.insert(item.getOffsetBySite(None), item)

    def insertAndShift(self, offsetOrItemOrList, itemOrNone=None):
        '''Insert an item at a specified or native offset, and shit any elements found in the Stream to start at the end of the added elements.

        This presently does not shift elements that have durations that extend into the lowest insert position.

        >>> st1 = Stream()
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
        >>> st1 = Stream()
        >>> st1.insertAndShift(n1)
        >>> st1.insertAndShift(n2) # should shift offset of n1
        >>> n1.getOffsetBySite(st1)
        31.0
        >>> n2.getOffsetBySite(st1)
        30.0
        >>> st2 = Stream()
        >>> st2.insertAndShift(40.0, n1)
        >>> st2.insertAndShift(40.0, n2)
        >>> n1.getOffsetBySite(st2)
        41.0        

        In single argument form with a list, the list should contain pairs that alternate
        offsets and items; the method then, obviously, inserts the items
        at the specified offsets:
        
        >>> n1 = note.Note("G")
        >>> n2 = note.Note("F#")
        >>> st3 = Stream()
        >>> st3.insertAndShift([1.0, n1, 2.0, n2])
        >>> n1.getOffsetBySite(st3)
        1.0
        >>> n2.getOffsetBySite(st3)
        2.0
        >>> len(st3)
        2
        '''
        # need to find the highest time after the insert  
        if itemOrNone != None: # we have an offset and an element
            if hasattr(itemOrNone, 'duration') and itemOrNone.duration != None:
                dur = itemOrNone.duration.quarterLength
            else:
                dur = 0.0
            lowestOffsetInsert = offsetOrItemOrList
            highestTimeInsert = offsetOrItemOrList + dur
        elif itemOrNone == None and isinstance(offsetOrItemOrList, list):
            # need to find which has the max combined offset and dur
            highestTimeInsert = 0.0
            lowestOffsetInsert = None
            i = 0
            while i < len(offsetOrItemOrList):
                o = offsetOrItemOrList[i]
                e = offsetOrItemOrList[i+1]
                if hasattr(e, 'duration')  and e.duration != None:
                    dur = e.duration.quarterLength
                else:
                    dur = 0.0
                if o + dur > highestTimeInsert:
                    highestTimeInsert = o + dur
                if o < lowestOffsetInsert or lowestOffsetInsert == None:
                    lowestOffsetInsert = o
                i += 2
        else: # using native offset
            if hasattr(offsetOrItemOrList, 'duration'):
                dur = offsetOrItemOrList.duration.quarterLength
            else:
                dur = 0.0
            # should this be getOffsetBySite(None)?
            highestTimeInsert = offsetOrItemOrList.offset + dur
            lowestOffsetInsert = offsetOrItemOrList.offset

        # this shift is the additional time to move due to the duration
        # of the newly inserted elements
        shiftDur = highestTimeInsert - lowestOffsetInsert

        #environLocal.printDebug(['insertAndShift()', 'adding one or more elements', 'lowestOffsetInsert', lowestOffsetInsert, 'highestTimeInsert', highestTimeInsert])

        # are not assuming that elements are ordered
        # use getElementAtOrAfter() in the future
        lowestElementToShift = None
        lowestGap = None
        for e in self._elements:
            o = e.getOffsetBySite(self)
            # gap is distance from offset to insert point; tells if shift is 
            # necessary
            gap = o - lowestOffsetInsert
            if gap < 0: # no shifting necessary
                continue 
            # only process elments whose offsets are after the lowest insert
            if lowestGap == None or gap < lowestGap:
                lowestGap = gap
                lowestElementToShift = e

        if lowestElementToShift != None:
            lowestOffsetToShift = lowestElementToShift.getOffsetBySite(self)
            shiftPos = highestTimeInsert - lowestOffsetToShift
        else:
            shiftPos = 0

        if shiftPos > 0:
            # need to move all the elements already in this stream
            for e in self._elements:
                o = e.getOffsetBySite(self)
                # gap is distance from offset to insert point; tells if shift is 
                # necessary
                gap = o - lowestOffsetInsert
                # only process elments whose offsets are after the lowest insert
                if gap >= 0.0:
                    #environLocal.printDebug(['insertAndShift()', e, 'offset', o, 'gap:', gap, 'shiftDur:', shiftDur, 'shiftPos:', shiftPos, 'o+shiftDur', o+shiftDur, 'o+shiftPos', o+shiftPos])
    
                    # need original offset, shiftDur, plus the distance from the start
                    e.setOffsetBySite(self, o+shiftPos)
        # after shifting all the necessary elements, append new ones
        # these will not be in order
        self.insert(offsetOrItemOrList, itemOrNone)
        # call this is elements are now out of order
        self._elementsChanged()         


#     def isClass(self, className):
#         '''Returns true if the Stream or Stream Subclass is a particular class or subclasses that class.
# 
#         Used by getElementsByClass in Stream
# 
#         >>> from music21 import *
#         >>> a = stream.Stream()
#         >>> a.isClass(note.Note)
#         False
#         >>> a.isClass(stream.Stream)
#         True
#         >>> b = stream.Measure()
#         >>> b.isClass(stream.Measure)
#         True
#         >>> b.isClass(stream.Stream)
#         True
#         '''
#         ## same as Music21Object.isClass, not ElementWrapper.isClass
#         if isinstance(self, className):
#             return True
#         else:
#             return False


    #---------------------------------------------------------------------------
    # searching and replacing routines

    def replace(self, target, replacement, firstMatchOnly=False,
                 allTargetSites=True):
        '''Given a `target` object, replace all references of that object with 
        references to the supplied `replacement` object.

        

        If `allTargetSites` is True (as it is by default), all sites that 
        have a reference for the replacement will be similarly changed. 
        This is useful for altering both a flat and nested representation.         
        '''
        # get all indices in this Stream that match
        if common.isNum(target): # matching object id number
            iMatch = self.indexList(target, firstMatchOnly=firstMatchOnly)
        else: # matching object directly
            iMatch = self.indexList(target, firstMatchOnly=firstMatchOnly)

        # target can be given as an obj id number
        if common.isNum(target):
            # replace target id with target
            target = self.getElementByObjectId(target) 

        eLen = len(self._elements)
        for i in iMatch:
            # replace all index target with the replacement
            if i < eLen:
                self._elements[i] = replacement
                # place the replacement at the old objects offset for this site
                replacement.addLocation(self, target.getOffsetBySite(self))
            else:
                self._endElements[i - eLen] = replacement
                replacement.addLocation(self, 'highestTime')

            # NOTE: an alternative way to do this would be to look at all the 
            # sites defined by the target and add them to the replacement
            # this would not put them in those locations elements, however

            # remove this location from old; this will also adjust the activeSite
            # assignment if necessary
            target.removeLocationBySite(self)

        # elements have changed
        self._elementsChanged()

        if allTargetSites:
            for site in target.getSites():
                # each site must be a Stream
                if site == None or site == self:
                    continue
                site.replace(target, replacement, firstMatchOnly=firstMatchOnly)



    #---------------------------------------------------------------------------
    def _recurseRepr(self, thisStream, prefixSpaces=0, 
                    addBreaks=True, addIndent=True):
        '''
        >>> import note
        >>> s1 = Stream()
        >>> s2 = Stream()
        >>> s3 = Stream()
        >>> n1 = note.Note()
        >>> s3.append(n1)
        >>> s2.append(s3)
        >>> s1.append(s2)
        >>> post = s1._recurseRepr(s1, addBreaks=False, addIndent=False)
        '''
        msg = []
        insertSpaces = 4
        for element in thisStream:    
            off = str(element.getOffsetBySite(thisStream))    
            if addIndent:
                indent = " " * prefixSpaces
            else:
                indent = ''

            if isinstance(element, Stream):
                msg.append(indent + "{" + off + "} " + element.__repr__())
                msg.append(self._recurseRepr(element, 
                           prefixSpaces + insertSpaces, 
                           addBreaks=addBreaks, addIndent=addIndent))
            else:
                msg.append(indent + "{" + off + "} " + element.__repr__())
        if addBreaks:
            msg = '\n'.join(msg)
        else: # use a slashs
            msg = ' / '.join(msg) # use space
        return msg


    def _reprText(self):
        '''Retrun a text representation. This methods can be overridden by
        subclasses to provide alternative text representations.
        '''
        return self._recurseRepr(self)

    def _reprTextLine(self):
        '''Retrun a text representation without line breaks. This methods can be overridden by subclasses to provide alternative text representations.
        '''
        return self._recurseRepr(self, addBreaks=False, addIndent=False)



    #---------------------------------------------------------------------------
    # temporary storage

    def setupPickleScaffold(self):
        '''Prepare this stream and all of its contents for pickling.

        >>> a = Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> a.setupPickleScaffold()
        '''
        #environLocal.printDebug(['calling setupPickleScaffold()', self])
        for element in self.elements:
            if hasattr(element, "elements"): # recurse time:
                element.setupPickleScaffold() # recurse
            #if hasattr(element, "unwrapWeakref"): # recurse time:
            elif isinstance(element, music21.Music21Object):
                element.freezeIds()
                element.unwrapWeakref()
        self.freezeIds()
        self.unwrapWeakref()


    def teardownPickleScaffold(self):
        '''After rebuilding this stream from pickled storage, prepare this as a normal Stream.

        >>> a = Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> a.setupPickleScaffold()
        >>> a.teardownPickleScaffold()
        '''
        #environLocal.printDebug(['calling teardownPickleScaffold'])

        self.wrapWeakref()
        self.unfreezeIds()
        for element in self.elements:
            if hasattr(element, "elements"): # recurse time:
                element.teardownPickleScaffold()
            elif hasattr(element, "unwrapWeakref"): # recurse time:
            #elif isinstance(element, music21.Music21Object):
                #environLocal.printDebug(['processing music21 obj', element])
                element.wrapWeakref()
                element.unfreezeIds()

#     def writePickle(self, fp):
#         f = open(fp, 'wb') # binary
#         # a negative protocol value will get the highest protocol; 
#         # this is generally desirable 
#         pickleMod.dump(self, f, protocol=-1)
#         f.close()
# 
# 
#     def openPickle(self, fp):
#         # not sure this will work
#         f = open(fp, 'rb')
#         self = pickleMod.load(f)
#         f.close()


    #---------------------------------------------------------------------------
    # display methods; in the same manner as show() and write()

    def plot(self, *args, **keywords):
        '''Given a method and keyword configuration arguments, create and display a plot.

        Note: plot() requires matplotib to be installed.

        For details on arguments, see :func:`~music21.graph.plotStream`.
   
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
        :class:`~music21.graph.PlotWindowedAmbitus`

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
        >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
        >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
        >>> #_DOCS_SHOW s.plot('pianoroll')
    
        .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
            :width: 600

        '''
        # import is here to avoid import of matplotlib problems
        from music21 import graph
        # first ordered arg can be method type
        graph.plotStream(self, *args, **keywords)


    def analyze(self, *args, **keywords):
        '''Given an analysis method, return an analysis on this Stream.

        For details on arguments, see :func:`~music21.analysis.discrete.analyzeStream`.

        Available plots include the following:
    
        ambitus -- runs :class:`~music21.analysis.discrete.Ambitus`
        key -- :class:`~music21.analysis.discrete.KrumhanslSchmuckler`

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> s.analyze('ambitus')
        <music21.interval.Interval m21>
        >>> s.analyze('key')
        (F#, 'minor', 0.81547089257624916)
        '''

        from music21.analysis import discrete
        # pass this stream to the analysis procedure
        return discrete.analyzeStream(self, *args, **keywords)


    #---------------------------------------------------------------------------
    # methods that act on individual elements without requiring 
    # @ _elementsChanged to fire

    def addGroupForElements(self, group, classFilter=None):
        '''
        Add the group to the groups attribute of all elements.
        if `classFilter` is set then only those elements whose objects
        belong to a certain class (or for Streams which are themselves of
        a certain class) are set.
         
        >>> a = Stream()
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
        for e in self.elements:
            if classFilter is None:
                e.groups.append(group)
            else:
                if hasattr(e, "elements"): # stream type
                    if isinstance(e, classFilter):
                        e.groups.append(group)
                elif hasattr(e, "obj"): # element type
                    if isinstance(e.obj, classFilter):
                        e.groups.append(group)
                else: # music21 type
                    if isinstance(e, classFilter):
                        e.groups.append(group)


    #---------------------------------------------------------------------------
    # getElementsByX(self): anything that returns a collection of Elements should return a Stream

    def getElementsByClass(self, classFilterList, returnStreamSubClass=True):
        '''Return a list of all Elements that match one or more classes in the `classFilterList`. A single class can be provided to the `classFilterList` parameter.
        
        >>> from music21 import *
        >>> a = stream.Score()
        >>> a.repeatInsert(note.Rest(), range(10))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.getElementsByClass(note.Note)
        >>> len(found)
        4
        >>> found[0].pitch.accidental.name
        'sharp'
        >>> b = stream.Stream()
        >>> b.repeatInsert(note.Rest(), range(15))
        >>> a.insert(b)
        >>> # here, it gets elements from within a stream
        >>> # this probably should not do this, as it is one layer lower
        >>> found = a.getElementsByClass(note.Rest)
        >>> len(found)
        10
        >>> found = a.flat.getElementsByClass(note.Rest)
        >>> len(found)
        25
        >>> found.__class__.__name__
        'Score'
        '''
        # TODO: could add `domain` parameter to allow searching only _elements, 
        # or _endElements, or both; possible performance hit

        if returnStreamSubClass:
            found = self.__class__()
        else:
            found = Stream()

        # much faster in the most common case than calling common.isListLike
        if not isinstance(classFilterList, (list, tuple)):
            classFilterList = tuple([classFilterList])

        if not self.isSorted and self.autoSort:
            self.sort() # will set isSorted to True

        # need both _elements and _endElements
        for e in self._elements:
            eClasses = e.classes # store once, as this is property call
            for className in classFilterList:
                # new method uses string matching of .classes attribute
                # temporarily check to see if this is a string
                if className in eClasses or (not isinstance(className, str) and isinstance(e, className)):
                    found.insert(e.getOffsetBySite(self), e, ignoreSort=True)
                    break # match first class and break to next e

#                 if isinstance(className, str):
#                     if className in eClasses:
#                         found.insert(e.getOffsetBySite(self), e,         
#                             ignoreSort=True)
#                         break # match first class and break to next e
#                 # old method uses isClass matching
#                 #elif e.isClass(className):
#                 elif isinstance(e, className):
#                     found.insert(e.getOffsetBySite(self), e, ignoreSort=True)
#                     break # match first class and break to next e

        for e in self._endElements:
            eClasses = e.classes # store once, as this is property call
            for className in classFilterList:

                if className in eClasses or (not isinstance(className, str) and isinstance(e, className)):

                    found.storeAtEnd(e, ignoreSort=True)
                    break # match first class and break to next e


                # new method uses string matching of .classes attribute
                # temporarily check to see if this is a string
#                 if isinstance(className, str):
#                     if className in eClasses:
#                         found.storeAtEnd(e, ignoreSort=True)
#                         break # match first class and break to next e
#                 # old method uses isClass matching
#                 #elif e.isClass(className):
#                 elif isinstance(e, className):
#                     found.storeAtEnd(e, ignoreSort=True)
#                     break # match first class and break to next e

        # if this stream was sorted, the resultant stream is sorted
        found.isSorted = self.isSorted
        # passing on auto sort status may or may not be what is needed here
        found.autoSort = self.autoSort
        return found


    def getElementsNotOfClass(self, classFilterList):
        '''Return a list of all Elements that do not match the one or more classes in the `classFilterList`. A single class can be provided to the `classFilterList` parameter.
        
        >>> a = Stream()
        >>> a.repeatInsert(note.Rest(), range(10))
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> found = a.getElementsNotOfClass(note.Note)
        >>> len(found)
        10

        >>> b = Stream()
        >>> b.repeatInsert(note.Rest(), range(15))
        >>> a.insert(b)
        >>> # here, it gets elements from within a stream
        >>> # this probably should not do this, as it is one layer lower
        >>> found = a.flat.getElementsNotOfClass(note.Rest)
        >>> len(found)
        4
        >>> found = a.flat.getElementsNotOfClass(note.Note)
        >>> len(found)
        25
        '''
        # should probably be whatever class the caller is
        try: 
            found = self.__class__()
        except:
            found = Stream()

        # much faster in the most common case than calling common.isListLike
        if not isinstance(classFilterList, list):
            if not isinstance(classFilterList, tuple):
                classFilterList = [classFilterList]

        # appendedAlready fixes bug where if an element matches two 
        # classes it was appendedTwice
        # need both _elements and _endElements
        for e in self._elements:
            eClasses = e.classes # store once, as this is property call
            for className in classFilterList:
                if className in eClasses or isinstance(e, className):
                #if e.isClass(className):
                    break # if a match to any of the classes, break
                # only insert after all no match to all classes   
                found.insert(e.getOffsetBySite(self), e, ignoreSort=True)

        for e in self._endElements:
            eClasses = e.classes # store once, as this is property call
            for className in classFilterList:
                if className in eClasses or isinstance(e, className):
                #if e.isClass(className):
                    break # if a match to any of the classes, break
                # only insert after all no match to all classes   
                found.storeAtEnd(e, ignoreSort=True)

        # if this stream was sorted, the resultant stream is sorted
        found.isSorted = self.isSorted
        return found


    def getElementsByGroup(self, groupFilterList):
        '''        
        >>> from music21 import note
        >>> n1 = note.Note("C")
        >>> n1.groups.append('trombone')
        >>> n2 = note.Note("D")
        >>> n2.groups.append('trombone')
        >>> n2.groups.append('tuba')
        >>> n3 = note.Note("E")
        >>> n3.groups.append('tuba')
        >>> s1 = Stream()
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
        
        if not hasattr(groupFilterList, "__iter__"):
            groupFilterList = [groupFilterList]

        returnStream = self.__class__()
        # need both _elements and _endElements
        # must handle independently b/c inserting
        for e in self._elements:
            for g in groupFilterList:
                if hasattr(e, "groups") and g in e.groups:
                    returnStream.insert(e.getOffsetBySite(self),
                                        e, ignoreSort = True)
        for e in self._endElements:
            for g in groupFilterList:
                if hasattr(e, "groups") and g in e.groups:
                    returnStream.storeAtEnd(e, ignoreSort=True)
                    #returnStream.append(myEl)
        returnStream.isSorted = self.isSorted
        return returnStream


    def groupCount(self):
        '''Get a dictionary for each groupId and the count of instances.

        >>> a = Stream()
        >>> n = note.Note()
        >>> a.repeatAppend(n, 30)
        >>> a.addGroupForElements('P1')
        >>> a.groupCount()
        {'P1': 30}
        >>> a[12].groups.append('green')
        >>> a.groupCount()
        {'P1': 30, 'green': 1}
        '''

        # TODO: and related:
        #getStreamGroups which does the same but makes the value of the hash key be a stream with all the elements that match the group?
        # this is similar to what getElementsByGroup does

        post = {}
        # need both _elements and _endElements
        for element in self.elements:
            for groupName in element.groups:
                if groupName not in post.keys():
                    post[groupName] = 0
                post[groupName] += 1
        return post


    def getOffsetByElement(self, obj):
        '''Given an object, return the offset of that object in the context of
        this Stream. This method can be called on a flat representation to return the ultimate position of a nested structure. 

        >>> n1 = note.Note('A')
        >>> n2 = note.Note('B')

        >>> s1 = Stream()
        >>> s1.insert(10, n1)
        >>> s1.insert(100, n2)

        >>> s2 = Stream()
        >>> s2.insert(10, s1)

        >>> s2.flat.getOffsetBySite(n1) # this will not work
        Traceback (most recent call last):
        DefinedContextsException: ...

        >>> s2.flat.getOffsetByElement(n1)
        20.0
        >>> s2.flat.getOffsetByElement(n2)
        110.0
        '''
        post = None

        # need both _elements and _endElements
        for e in self.elements:
            # must compare id(), not elements directly
            # TODO: need to test with ElementWrapper
            if isinstance(e, music21.ElementWrapper):
                compareObj = e.obj
            else:
                compareObj = e
            if id(compareObj) == id(obj):
                post = obj.getOffsetBySite(self)
                break
        return post

    def getElementById(self, id, classFilter=None):
        '''Returns the first encountered element for a given id. Return None
        if no match

        >>> import music21
        >>> e = 'test'
        >>> a = music21.stream.Stream()
        >>> ew = music21.ElementWrapper(e)
        >>> a.insert(0, ew)
        >>> a[0].id = 'green'
        >>> None == a.getElementById(3)
        True
        >>> a.getElementById('green').id
        'green'
        >>> a.getElementById('Green').id  # case does not matter
        'green'
        
        
        Getting an element by getElementById changes its activeSite
        
        
        >>> b = music21.stream.Stream()
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
        '''
        # accessing .elements assures an autoSort check
        for element in self.elements:
            # case insensitive; this could be based on an option 
            match = False
            try:
                if element.id.lower() == id.lower():
                    match = True
            except AttributeError: # not a string
                if element.id == id:
                    match = True
            if match:
                if classFilter is not None:
                    eClasses = e.classes # store once, as this is property call
                    #if element.isClass(classFilter):
                    if classFilter in eClasses or isinstance(e, classFilter):
                        element.activeSite = self
                        return element
                    else:
                        continue # id may match but not proper class
                else:
                    element.activeSite = self
                    return element
        return None

    def getElementsByOffset(self, offsetStart, offsetEnd=None,
                    includeEndBoundary=True, mustFinishInSpan=False, mustBeginInSpan=True):
        '''Return a Stream of all Elements that are found at a certain offset or within a certain offset time range, specified as start and stop values.

        If `mustFinishInSpan` is True then an event that begins between offsetStart and offsetEnd but which ends after offsetEnd will not be included.  For instance, a half note at offset 2.0 will be found in.

        The `includeEndBoundary` option determines if an element begun just at offsetEnd should be included.  Setting includeEndBoundary to False at the same time as mustFinishInSpan is set to True is probably NOT what you ever want to do.
        
        Setting `mustBeginInSpan` to False is a good way of finding 
        

            .. image:: images/getElementsByOffset.*
                :width: 600


        >>> st1 = Stream()
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
        >>> out3 = st1.getElementsByOffset(1, 3, mustFinishInSpan = True)
        >>> len(out3)
        0
        >>> out4 = st1.getElementsByOffset(1, 2)
        >>> len(out4)
        1
        >>> out4[0].step
        'D'
        >>> out5 = st1.getElementsByOffset(1, 2, includeEndBoundary = False)
        >>> len(out5)
        0        
        >>> out6 = st1.getElementsByOffset(1, 2, includeEndBoundary = False, mustBeginInSpan = False)
        >>> len(out6)
        1
        >>> out6[0].step
        'C'
        >>> out7 = st1.getElementsByOffset(1, 3, mustBeginInSpan = False)
        >>> len(out7)
        2
        >>> [el.step for el in out7]
        ['C', 'D']
        >>> a = Stream()
        >>> n = note.Note('G')
        >>> n.quarterLength = .5
        >>> a.repeatInsert(n, range(8))
        >>> b = Stream()
        >>> b.repeatInsert(a, [0, 3, 6])
        >>> c = b.getElementsByOffset(2,6.9)
        >>> len(c)
        2
        >>> c = b.flat.getElementsByOffset(2,6.9)
        >>> len(c)
        10
        '''
        if offsetEnd is None:
            offsetEnd = offsetStart
        
        found = self.__class__()


        # need both _elements and _endElements
        for e in self.elements:
            match = False
            # better to specify site of offset source
            offset = e.getOffsetBySite(self)
            #offset = e.offset

            dur = e.duration
            if dur is None or mustFinishInSpan is False:
                eEnd = offset
            else:
                eEnd = offset + dur.quarterLength

            if mustBeginInSpan is False and dur is not None:
                eStart = offset + dur.quarterLength
            else:
                eStart = offset

            if includeEndBoundary is True and mustBeginInSpan is True and \
                eStart >= offsetStart and eEnd <= offsetEnd:
                    match = True
            elif includeEndBoundary is True and mustBeginInSpan is False and \
                eStart > offsetStart and eEnd <= offsetEnd:
                    match = True
            elif includeEndBoundary is False and mustBeginInSpan is True and \
                eStart >= offsetStart and eEnd < offsetEnd:
                    match = True
            elif includeEndBoundary is False and mustBeginInSpan is False and \
                eStart > offsetStart and eEnd < offsetEnd:
                    match = True
            else: # 
                match = False

            if match is True:
                found.insert(e)
        return found


    def getElementAtOrBefore(self, offset, classList=None):
        '''Given an offset, find the element at this offset, or with the offset
        less than and nearest to.

        Return one element or None if no elements are at or preceded by this 
        offset. 

        >>> import music21
        >>> stream1 = music21.stream.Stream()

        >>> x = music21.note.Note('D4')
        >>> x.id = 'x'
        >>> y = music21.note.Note('E4')
        >>> y.id = 'y'
        >>> z = music21.note.Rest()
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
        
                
        >>> c = stream1.getElementAtOrBefore(100, [music21.clef.TrebleClef, music21.note.Rest])
        >>> c.offset, c.id
        (0.0, 'z')


        Getting an object via getElementAtOrBefore sets the activeSite
        for that object to the Stream, and thus sets its offset


        >>> stream2 = music21.stream.Stream()
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
        

        #>>> clef1 = music21.clef.BassClef()
        #>>> stream1.insert(20, clef1)
        #>>> e = stream1.getElementAtOrBefore(21)
        #>>> e
        #<music21.note.Note D4>
        # FAILS, returns the clef!



        '''
        candidates = []
        nearestTrailSpan = offset # start with max time
        # need both _elements and _endElements
        for e in self.elements:
            eClasses = e.classes # store once, as this is property call
            if classList != None:
                match = False
                for cl in classList:
                    # new method uses string matching of .classes attribute
                    # temporarily check to see if this is a string
                    if isinstance(cl, str):
                        if cl in eClasses:
                            match = True
                            break
                    # old method uses isinstance matching
                    else:
                        if isinstance(e, cl):
                            match = True
                            break
                if not match:
                    continue
            span = offset - e.getOffsetBySite(self)
            #environLocal.printDebug(['e span check', span, 'offset', offset, 'e.offset', e.offset, 'e.getOffsetBySite(self)', e.getOffsetBySite(self), 'e', e])
            if span < 0: # the e is after this offset
                continue
            elif span == 0: 
                candidates.append((span, e))
                nearestTrailSpan = span
            else:
                if span <= nearestTrailSpan: # this may be better than the best
                    candidates.append((span, e))
                    nearestTrailSpan = span
                else:
                    continue
        #environLocal.printDebug(['getElementAtOrBefore(), e candidates', candidates])
        if len(candidates) > 0:
            candidates.sort()
            candidates[0][1].activeSite = self
            return candidates[0][1]
        else:
            return None


    def getElementAtOrAfter(self, offset, classList=None):
        '''Given an offset, find the element at this offset, or with the offset
        greater than and nearest to.

        OMIT_FROM_DOCS
        TODO: write this
        '''
        raise Exception("not yet implemented")

    def getElementBeforeOffset(self, offset, classList=None):
        '''Get element before a provided offset

        OMIT_FROM_DOCS
        TODO: write this
        '''
        raise Exception("not yet implemented")

    def getElementAfterOffset(self, offset, classList = None):
        '''Get element after a provided offset

        OMIT_FROM_DOCS
        TODO: write this
        '''
        raise Exception("not yet implemented")


    def getElementBeforeElement(self, element, classList = None):
        '''given an element, get the element before

        OMIT_FROM_DOCS
        TODO: write this
        '''
        raise Exception("not yet implemented")

    def getElementAfterElement(self, element, classList = None):
        '''given an element, get the next element.  If classList is specified, 
        check to make sure that the element is an instance of the class list
        
        >>> st1 = Stream()
        >>> n1 = note.Note()
        >>> n2 = note.Note()
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
        
        >>> st1.getElementAfterElement("hi")
        Traceback (most recent call last):
        StreamException: ...
        >>> t5 = st1.getElementAfterElement(n1, [note.Rest])
        >>> t5 is r3
        True
        >>> t6 = st1.getElementAfterElement(n1, [note.Rest, note.Note])
        >>> t6 is n2
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
                el =  elements[elPos + 1]
                el.activeSite = self
                return el
        else:
            for i in range(elPos + 1, len(elements)):
                for cl in classList:
                    if isinstance(elements[i], cl): 
                        el = elements[i]
                        el.activeSite = self
                        return el
            return None


    def groupElementsByOffset(self, returnDict = False):
        '''
        returns a List of lists in which each entry in the
        main list is a list of elements occurring at the same time.
        list is ordered by offset (since we need to sort the list
        anyhow in order to group the elements), so there is
        no need to call stream.sorted before running this,
        but it can't hurt.
        
        it is DEFINITELY a feature that this method does not
        find elements within substreams that have the same
        absolute offset.  See Score.lily for how this is
        useful.  For the other behavior, call Stream.flat first.
        '''
        offsetsRepresented = common.defHash()
        for el in self.elements:
            if not offsetsRepresented[el.offset]:
                offsetsRepresented[el.offset] = []
            offsetsRepresented[el.offset].append(el)
        if returnDict is True:
            return offsetsRepresented
        else:
            offsetList = []
            for thisOffset in sorted(offsetsRepresented.keys()):
                offsetList.append(offsetsRepresented[thisOffset])
            return offsetList



    #--------------------------------------------------------------------------
    # routines for obtaining specific types of elements from a Stream
    # _getNotes and _getPitches are found with the interval routines

    def measures(self, numberStart, numberEnd, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature], gatherSpanners=True):
        '''Get a region of Measures based on a start and end Measure number, were the boundary numbers are both included. That is, a request for measures 4 through 10 will return 7 Measures, numbers 4 through 10.

        Additionally, any number of associated classes can be gathered as well. Associated classes are the last found class relevant to this Stream or Part.  

        While all elements in the source are made available in the extracted region, new Measure objects are created and returned. 

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> b = a[0].measures(4,6)
        >>> len(b)
        3

        '''
        
        # create a dictionary of measure number, list of Meaures
        # there may be more than one Measure with the same Measure number
        mapRaw = {}
        mNumbersUnique = [] # store just the numbers
        mStream = self.getElementsByClass('Measure')

        # TODO: calling .flat here causes unidentified problems in further
        # processing of the returnObj; need to investigate further
        #tempFlat = self.flat
        #environLocal.printDebug(['measures(): post flat call', self, 'len(self.flat)', len(self.flat)])

        # spanners may be store at the container level, not w/n a measure
        # if they are within the Measure, or a voice, they will be transfered
        # below
        mStreamSpanners = self.spanners

        returnObj = self.__class__()
        returnObj.mergeAttributes(self) # get id and groups
        srcObj = self

        # if we have no Measure defined, call makeNotation
        # this will  return a deepcopy of all objects
        if len(mStream) == 0:
            mStream = self.makeNotation(inPlace=False)
            # need to set srcObj to this new stream
            srcObj = mStream
            # get spanners from make notation, as this will be a copy
            # TODO: make sure that makeNotation copies spanners
            mStreamSpanners = mStream.spanners

        if gatherSpanners:
            for sp in mStreamSpanners:
                #environLocal.printDebug(['copying spanner to returnObj', sp])
                # store in flat locations? could also be end elements?
                returnObj.insert(sp.getOffsetBySite(allSpanners), sp)

        for m in mStream.elements:
            #environLocal.printDebug(['m', m])
            # mId is a tuple of measure nmber and any suffix
            mId = (m.number, m.numberSuffix)
            # store unique measure numbers for reference
            if m.number not in mNumbersUnique:
                mNumbersUnique.append(m.number)
            if mId not in mapRaw.keys():
                mapRaw[mId] = [] # use a list
            # these will be in order by measure number
            # there may be multiple None and/or 0 measure numbers
            mapRaw[mId].append(m)

        #environLocal.printDebug(['len(mapRaw)', len(mapRaw)])

        # if measure numbers are not defined, we should just count them 
        # in order, starting from 1
        if len(mNumbersUnique) == 1:
            mapCooked = {}  
            # only one key but we do not know what it is
            i = 1
            for number, suffix in mapRaw.keys():
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
        startMeasureNew = None

        # if end not specified, get last
        if numberEnd == None:
            numberEnd = max([x for x,y in mapCooked])

        for i in range(numberStart, numberEnd+1):
            match = None
            for number, suffix in mapCooked.keys():
                # this will match regardless of suffix
                if number == i:
                    match = mapCooked[(number, suffix)]
                    break
            if match == None: # None found in this range
                continue 
            # need to make offsets relative to this new Stream
            for m in match:
                # this assumes measure are in offset order
                # this may not always be the case
                if startOffset == None: # only set on first
                    startOffset = m.getOffsetBySite(srcObj)
                    # store reference for collecting objects in src
                    startMeasure = m

                #environLocal.printDebug(['startOffset', startOffset, 'startMeasure', startMeasure])

                # create a new Measure container, but populate it 
                # with the same elements
                mNew = Measure()
                mNew.mergeAttributes(m)
                # will only set on first time through
                if startMeasureNew is None:
                    startMeasureNew = mNew

                # transfer elements to the new measure; these are not copies
                # this might contain voices and/or spanners
                for e in m._elements:
                    mNew.insert(e)
                for e in m._endElements:
                    mNew.storeAtEnd(e)

                oldOffset = m.getOffsetBySite(srcObj)
                # subtract the offset of the first measure
                # this will be zero in the first usage
                newOffset = oldOffset - startOffset
                returnObj.insert(newOffset, mNew)

                #environLocal.printDebug(['old/new offset', oldOffset, newOffset])

        # manipulate startMeasure to add desired context objects
        for className in collect:
            # first, see if it is in this Measure
            # startMeasure here is the original measure
            found = startMeasure.getElementsByClass(className)
            if len(found) > 0:
                continue # already have one on this measure
            # do a context search for the class, searching all stored
            # locations
            found = startMeasure.getContextByClass(className)
            if found != None:
                # only insert into measure new
                # TODO: may want to deepcopy inserted object here
                startMeasureNew.insert(0, found)
            else:
                environLocal.printDebug(['measures(): cannot find requested class in stream:', className])

        #environLocal.printDebug(['len(returnObj.flat)', len(returnObj.flat)])

        return returnObj


    def measure(self, measureNumber, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature]):
        '''Given a measure number, return a single :class:`~music21.stream.Measure` object if the Measure number exists, otherwise return None.

        This method is distinguished from :meth:`~music21.stream.Stream.measures` in that this method returns a single Measure object, not a Stream containing one or more Measure objects.

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> a[0].measure(3)
        <music21.stream.Measure 3 offset=0.0>
        '''
        # we must be able to obtain a measure from this (not a flat) 
        # representation (e.g., this is a Stream or Part, not a Score)
        if len(self.getElementsByClass('Measure')) >= 1:
            s = self.measures(measureNumber, measureNumber, collect=collect)
            if len(s) == 0:
                return None
            else:
                return s.getElementsByClass('Measure')[0]
        else:   
            return None


    def measureOffsetMap(self, classFilterList=None):
        '''If this Stream contains Measures, provide a dictionary 
        where keys are offsets and values are a list of references 
        to one or more Measures that start at that offset. The 
        offset values is always in the frame of the calling Stream (self).

        The `classFilterList` argument can be a list of classes 
        used to find Measures. A default of None uses Measure. 

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> sorted(a[0].measureOffsetMap().keys())
        [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 34.0, 38.0]

        OMIT_FROM_DOCS
        see important examples in testMeasureOffsetMap() andtestMeasureOffsetMapPostTie()
        '''
        if classFilterList == None:
            classFilterList = [Measure]
        if not common.isListLike(classFilterList):
            classFilterList = [classFilterList]

        #environLocal.printDebug(['calling measure offsetMap()'])

        #environLocal.printDebug([classFilterList])
        map = {}
        # first, try to get measures
        # this works best of this is a Part or Score
        if Measure in classFilterList or 'Measure' in classFilterList:
            for m in self.getElementsByClass('Measure'):
                offset = m.getOffsetBySite(self)
                if offset not in map.keys():
                    map[offset] = []
                # there may be more than one measure at the same offset
                map[offset].append(m)

        # try other classes
        for className in classFilterList:
            if className in [Measure or 'Measure']: # do not redo
                continue
            for e in self.getElementsByClass(className):
                #environLocal.printDebug(['calling measure offsetMap(); e:', e])
                # NOTE: if this is done on Notes, this can take an extremely
                # long time to process
                # -1 here is a reverse sort, where oldest objects are returned
                # first
                m = e.getContextByClass(Measure, sortByCreationTime=-1,
                    prioritizeActiveSite=False)
                if m is None: 
                    continue
                # assuming that the offset returns the proper offset context
                # this is, the current offset may not be the stream that 
                # contains this Measure; its current activeSite
                offset = m.offset
                if offset not in map.keys():
                    map[offset] = []
                if m not in map[offset]:
                    map[offset].append(m)
        return map


    def _getVoices(self):
        '''        
        '''
        return self.getElementsByClass(Voice)

    voices = property(_getVoices, 
        doc='''Return all :class:`~music21.stream.Voices` objects in a :class:`~music21.stream.Stream` or Stream subclass.

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> s.insert(0, stream.Voice()) 
        >>> s.insert(0, stream.Voice()) 
        >>> len(s.voices)
        2
        ''')

    def _getSpanners(self):
        '''        
        '''
        return self.getElementsByClass(spanner.Spanner)

    spanners = property(_getSpanners, 
        doc='''Return all :class:`~music21.spanner.Spanner` objects in a :class:`~music21.stream.Stream` or Stream subclass.

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> s.insert(0, spanner.Slur()) 
        >>> s.insert(0, spanner.Slur()) 
        >>> len(s.spanners)
        2
        ''')


    def getTimeSignatures(self, searchContext=True, returnDefault=True,
        sortByCreationTime=True):
        '''Collect all :class:`~music21.meter.TimeSignature` objects in this stream.
        If no TimeSignature objects are defined, get a default
        
        >>> a = Stream()
        >>> b = meter.TimeSignature('3/4')
        >>> a.insert(b)
        >>> a.repeatInsert(note.Note("C#"), range(10)) 
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
            post = self.__class__()
            # sort by time to search the most recent objects
            obj = self.getContextByClass(meter.TimeSignature, 
                  sortByCreationTime=sortByCreationTime)
            #environLocal.printDebug(['getTimeSignatures(): searching contexts: results', obj])
            if obj != None:
                post.append(obj)

        # get a default and/or place default at zero if nothing at zero
        if returnDefault:
            if len(post) == 0 or post[0].offset > 0: 
                ts = meter.TimeSignature('%s/%s' % (defaults.meterNumerator, 
                                   defaults.meterDenominatorBeatType))
                post.insert(0, ts)

        #environLocal.printDebug(['getTimeSignatures(): final result:', post[0]])

        return post
        

    def getInstrument(self, searchActiveSite=True, returnDefault=True):
        '''Search this stream or activeSite streams for :class:`~music21.instrument.Instrument` objects, otherwise 
        return a default

        >>> a = Stream()
        >>> b = a.getInstrument() # a default will be returned
        '''
        #environLocal.printDebug(['searching for instrument, called from:', 
        #                        self])
        #TODO: Rename: getInstruments, and return a Stream of instruments
        #for cases when there is more than one instrument

        instObj = None
        post = self.getElementsByClass('Instrument')
        if len(post) > 0:
            #environLocal.printDebug(['found local instrument:', post[0]])
            instObj = post[0] # get first
        else:
            if searchActiveSite:
                if isinstance(self.activeSite, Stream) and self.activeSite != self:
                    #environLocal.printDebug(['searching activeSite Stream', 
                    #    self, self.activeSite])
                    instObj = self.activeSite.getInstrument(
                              searchActiveSite=searchActiveSite, 
                              returnDefault=False) 

        # if still not defined, get default
        if returnDefault and instObj is None:
            instObj = instrument.Instrument()
            # now set with .mx call
            #instObj.partId = defaults.partId # give a default id
            instObj.partName = defaults.partName # give a default id
        return instObj



    def bestClef(self, allowTreble8vb = False):
        '''Returns the clef that is the best fit for notes and chords found in this Stream.
    
        This does not automatically get a flat representation of the Stream.

        >>> a = Stream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(60,72))
        ...    a.insert(n)
        >>> b = a.bestClef()
        >>> b.line
        2
        >>> b.sign
        'G'

        >>> c = Stream()
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

        notes = self.getElementsByClass(note.GeneralNote)

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
        '''Collect all :class:`~music21.clef.Clef` objects in this Stream in a new Stream. Optionally search the activeSite Stream and/or contexts. 

        If no Clef objects are defined, get a default using :meth:`~music21.stream.Stream.bestClef`
        
        >>> from music21 import clef
        >>> a = Stream()
        >>> b = clef.AltoClef()
        >>> a.insert(0, b)
        >>> a.repeatInsert(note.Note("C#"), range(10)) 
        >>> c = a.getClefs()
        >>> len(c) == 1
        True
        '''
        # TODO: activeSite searching is not yet implemented
        # this may not be useful unless a stream is flat
        post = self.getElementsByClass(clef.Clef)

        #environLocal.printDebug(['getClefs(); count of local', len(post), post])       
        if len(post) == 0 and searchActiveSite and self.activeSite != None:
            environLocal.printDebug(['getClefs(): search activeSite'])       
            post = self.activeSite.getElementsByClass(clef.Clef)

        if len(post) == 0 and searchContext:
            # returns a single element match
            #post = self.__class__()
            obj = self.getContextByClass(clef.Clef)
            if obj != None:
                post.append(obj)

        # get a default and/or place default at zero if nothing at zero
        if returnDefault and (len(post) == 0 or post[0].offset > 0): 
            #environLocal.printDebug(['getClefs(): using bestClef()'])
            post.insert(0, self.bestClef())
        return post



    def getKeySignatures(self, searchActiveSite=True, searchContext=True):
        '''Collect all :class:`~music21.key.KeySignature` objects in this Stream in a new Stream. Optionally search the activeSite stream and/or contexts. 

        If no KeySignature objects are defined, returns an empty Stream 
        
        >>> from music21 import clef
        >>> a = Stream()
        >>> b = key.KeySignature(3)
        >>> a.insert(0, b)
        >>> a.repeatInsert(note.Note("C#"), range(10)) 
        >>> c = a.getKeySignatures()
        >>> len(c) == 1
        True
        '''
        # TODO: activeSite searching is not yet implemented
        # this may not be useful unless a stream is flat
        post = self.getElementsByClass(key.KeySignature)
        if len(post) == 0 and searchContext:
            # returns a single value
            post = self.__class__()
            obj = self.getContextByClass(key.KeySignature)
            if obj != None:
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
               
        >>> from music21 import *
        >>> qj = corpus.parseWork('ciconia/quod_jactatur').parts[0]
        >>> qj.measures(1,2).show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.Treble8vbClef object at 0x...>
            {0.0} <music21.instrument.Instrument P1: MusicXML Part: Grand Piano>
            {0.0} <music21.key.KeySignature of 1 flat>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.layout.SystemLayout object at 0x...>
            {0.0} <music21.note.Note C>
            {1.5} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note E>
            {0.5} <music21.note.Note D>
            {1.0} <music21.note.Note C>
            {1.5} <music21.note.Note D>
        >>> k1 = qj.flat.getElementsByClass(key.KeySignature)[0]
        >>> qj.flat.replace(k1, key.KeySignature(-3))
        >>> qj.getElementsByClass(stream.Measure)[1].insert(0, key.KeySignature(5))
        >>> qj2 = qj.invertDiatonic(note.Note('F4'), inPlace = False)
        >>> qj2.measures(1,2).show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.Treble8vbClef object at 0x...>
            {0.0} <music21.instrument.Instrument P1: MusicXML Part: Grand Piano>
            {0.0} <music21.key.KeySignature of 3 flats>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.layout.SystemLayout object at 0x...>
            {0.0} <music21.note.Note B->
            {1.5} <music21.note.Note A->
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {2.0} <music21.key.KeySignature of 5 sharps>
            {2.0} <music21.note.Note G#>
            {2.5} <music21.note.Note A#>
            {3.0} <music21.note.Note B>
            {3.5} <music21.note.Note A#>
        '''
        keySigSearch = self.flat.getElementsByClass(key.KeySignature)
        
        quickSearch = True
        if len(keySigSearch) == 0:
            ourKey = key.KeySignature('C', 'major')
        elif len(keySigSearch) == 1:
            ourKey = keySigSearch[0]
        else:
            quickSearch = False
        
        if inPlace == True:
            returnStream = self
        else:
            returnStream = copy.deepcopy(self)
        
        
        inversionDNN = inversionNote.diatonicNoteNum
        for n in returnStream.flat.notes:
            if n.isRest is False:
                n.pitch.diatonicNoteNum = (2*inversionDNN) - n.pitch.diatonicNoteNum
                if quickSearch is True:
                    n.pitch.accidental = ourKey.accidentalByStep(n.pitch.step)
                else:
                    n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.pitch.step)
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

    def shiftElements(self, offset, classFilterList=None):
        '''Add offset value to every offset of contained Elements. Elements that are stored on the _endElements list will not be changed

        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(0,10))
        >>> a.shiftElements(30)
        >>> a.lowestOffset
        30.0
        >>> a.shiftElements(-10)
        >>> a.lowestOffset
        20.0
        '''
        # only want _elements, do not want _endElements
        for e in self._elements:
            match = False
            if classFilterList != None:
                for className in classFilterList:
                    # this may not match wrapped objects
                    if isinstance(e, className):
                        match = True
                        break
            else:
                match = True
            if match:
                e.setOffsetBySite(self, e.getOffsetBySite(self) + offset)

        self._elementsChanged() 
        
    def transferOffsetToElements(self):
        '''Transfer the offset of this stream to all internal elements; then set
        the offset of this stream to zero.

        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(0,10))
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
        self._elementsChanged()


    #--------------------------------------------------------------------------
    # utilities for creating large numbers of elements

    def repeatAppend(self, item, numberOfTimes):
        '''
        Given an object and a number, run append that many times on a deepcopy of the object.
        numberOfTimes should of course be a positive integer.
        
        >>> a = Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> a.duration.quarterLength
        40.0
        >>> a[9].offset
        36.0
        '''
        # if not an element, embed
        if not isinstance(item, music21.Music21Object): 
            element = music21.ElementWrapper(item)
        else:
            element = item
            
        for i in range(0, numberOfTimes):
            self.append(deepcopy(element))
    
    def repeatInsert(self, item, offsets):
        '''Given an object, create a deep copy of each object at each positions specified by 
        the offset list:

        >>> a = Stream()
        >>> n = note.Note('G-')
        >>> n.quarterLength = 1
        
        >>> a.repeatInsert(n, [0, 2, 3, 4, 4.5, 5, 6, 7, 8, 9, 10, 11, 12])
        >>> len(a)
        13
        >>> a[10].offset
        10.0
        '''
        if not common.isListLike(offsets): 
            raise StreamException('must provide a lost of offsets, not %s' % offsets)

        if not isinstance(item, music21.Music21Object): 
            # if not an element, embed
            element = music21.ElementWrapper(item)
        else:
            element = item

        for offset in offsets:
            elementCopy = deepcopy(element)
            self.insert(offset, elementCopy)



    def extractContext(self, searchElement, before = 4.0, after = 4.0, 
                       maxBefore = None, maxAfter = None, forceOutputClass=None):
        '''Extracts elements around the given element within (before) quarter notes and (after) quarter notes (default 4), and returns a new Stream.
                
        >>> from music21 import note
        >>> qn = note.QuarterNote()
        >>> qtrStream = Stream()
        >>> qtrStream.repeatInsert(qn, [0, 1, 2, 3, 4, 5])
        >>> hn = note.HalfNote()
        >>> hn.name = "B-"
        >>> qtrStream.append(hn)
        >>> qtrStream.repeatInsert(qn, [8, 9, 10, 11])
        >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
        >>> hnStream._reprText()
        '{5.0} <music21.note.Note C>\\n{6.0} <music21.note.Note B->\\n{8.0} <music21.note.Note C>'

        OMIT_FROM_DOCS
        TODO: maxBefore -- maximum number of elements to return before; etc.

        NOTE: RENAME: this probably should be renamed, as we use Context in a specail way. Perhaps better is extractNeighbors?
        
        '''
        if forceOutputClass == None:
            display = self.__class__()
        else:
            display = forceOutputClass()

        found = None
        foundOffset = 0
        foundEnd = 0 
        elements = self.elements
        for i in range(len(elements)):
            b = elements[i]
            if b.id is not None or searchElement.id is not None:
                if b.id == searchElement.id:
                    found = i
                    foundOffset = elements[i].getOffsetBySite(self)
                    foundEnd = foundOffset + elements[i].duration.quarterLength                        
            else:
                if b is searchElement or (hasattr(b, "obj") and b.obj is searchElement):
                    found = i
                    foundOffset = elements[i].getOffsetBySite(self)
                    foundEnd = foundOffset + elements[i].duration.quarterLength
        if found is None:
            raise StreamException("Could not find the element in the stream")

        # handle _elements and _endElements independently
        for e in self._elements:
            o = e.getOffsetBySite(self)
            if (o >= foundOffset - before and o < foundEnd + after):
                display.insert(o, e)

        for e in self._endElements:
            o = e.getOffsetBySite(self)
            if (o >= foundOffset - before and o < foundEnd + after):
                display.storeAtEnd(e)

        return display


    #---------------------------------------------------------------------------
    # transformations of self that return a new Stream

    def makeChords(self, minimumWindowSize=.125, includePostWindow=True,
            removeRedundantPitches=True,
            gatherArticulations=True, gatherExpressions=True, inPlace=False):
        '''Gather simultaneous Notes into a Chords.
        
        The gathering of elements, starting from offset 0.0, uses the `minimumWindowSize`, in quarter lengths, to collect all Notes that start between 0.0 and the minimum window size (this permits overlaps within a minimum tolerance). 
        
        After collection, the maximum duration of collected elements is found; this duration is then used to set the new starting offset. A possible gap then results between the end of the window and offset specified by the maximum duration; these additional notes are gathered in a second pass if `includePostWindow` is True.
        
        The new start offset is shifted to the larger of either the minimum window or the maximum duration found in the collected group. The process is repeated until all offsets are covered.
        
        Each collection of Notes is formed into a Chord. The Chord is given the longest duration of all constituents, and is inserted at the start offset of the window from which it was gathered. 
        
        Chords can gather both articulations and expressions from found Notes 
        using `gatherArticulations` and `gatherExpressions`.
        
        The resulting Stream, if not in-place, can also gather additional objects by placing class names in the `collect` list. By default, TimeSignature and KeySignature objects are collected. 
        
        '''
        # gather lyrics as an option

        # define classes that are gathered; assume they have pitches
        matchClasses = ['Note', 'Chord', 'Rest']

        if not inPlace: # make a copy
            # since we do not return Scores, this probably should always be 
            # a Stream
            #returnObj = Stream()
            #returnObj = self.__class__() # for output
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass('Measure'):
                # offset values are not relative to measure; need to
                # shift by each measure's offset
                m.makeChords(minimumWindowSize=minimumWindowSize,
                    includePostWindow=includePostWindow,
                    removeRedundantPitches=removeRedundantPitches,
                    gatherArticulations=gatherArticulations,
                    gatherExpressions=gatherExpressions,
                    inPlace=True)
            return returnObj # exit
    
        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Part'):
                p.makeChords(minimumWindowSize=minimumWindowSize,
                    includePostWindow=includePostWindow,
                    removeRedundantPitches=removeRedundantPitches,
                    gatherArticulations=gatherArticulations,
                    gatherExpressions=gatherExpressions,
                    inPlace=True)
            return returnObj # exit

        o = 0.0 # start at zero
        oTerminate = returnObj.highestOffset

        while True: 
            # get all notes within the start and the minwindow size
            oStart = o
            oEnd = oStart + minimumWindowSize 
            sub = returnObj.getElementsByOffset(oStart, oEnd,
                    includeEndBoundary=False, mustFinishInSpan=False, mustBeginInSpan=True)  
            subNotes = sub.getElementsByClass(matchClasses) # get once for speed         

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
            if (includePostWindow and qlMax != None 
                and qlMax > minimumWindowSize):
                subAdd = returnObj.getElementsByOffset(oStart+minimumWindowSize,
                        oStart+qlMax,
                        includeEndBoundary=False, mustFinishInSpan=False, mustBeginInSpan=True)  
                # concatenate any additional notes found
                subNotes += subAdd.getElementsByClass(matchClasses)

            subRest = []
            for e in subNotes:
                if 'Rest' in e.classes:
                    subRest.append(e)
            if len(subRest) > 0:
                # remove from subNotes
                for e in subRest:
                    subNotes.remove(e)
                
            # make subNotes into a chord
            if len(subNotes) > 0:
                #environLocal.printDebug(['creating chord from subNotes', subNotes, 'inPlace', inPlace])

                c = chord.Chord()
                c.duration.quarterLength = qlMax
                # these are references, not copies, for now
                c.pitches = [n.pitch for n in subNotes]
                if gatherArticulations:
                    for n in subNotes:
                        c.articulations += n.articulations
                if gatherExpressions:
                    for n in subNotes:
                        c.expressions += n.expressions
                # always remove all the previous elements      
                for n in subNotes:
                    returnObj.remove(n)
                for r in subRest:
                    returnObj.remove(r)

                if removeRedundantPitches:
                    c.removeRedundantPitches(inPlace=True)
                # insert chord at start location
                returnObj.insert(o, c)

            # only add rests if no notes
            elif len(subRest) > 0:
                r = note.Rest()
                r.quarterLength = qlMax
                # remove old rests if in place
                for rOld in subRest:
                    returnObj.remove(rOld)
                returnObj.insert(o, r)

            #environLocal.printDebug(['len of returnObj', len(returnObj)])

            # shift offset to qlMax or minimumWindowSize
            if qlMax != None and qlMax >= minimumWindowSize:
                # update start offset to what was old boundary
                # note: this assumes that the start of the longest duration
                # was at oStart; it could have been between oStart and oEnd
                o += qlMax
            else:
                o += minimumWindowSize

            # end While loop conditions
            if o > oTerminate:
                break
        return returnObj

# not defined on Stream yet, as not clear what it should do
#     def chordify(self):
#         '''Split all duration in all parts, if multi-part, by all unique offsets. All simultaneous durations are then gathered into single chords. 
#         '''
#         pass


    def splitByClass(self, objName, fx):
        '''Given a stream, get all objects specified by objName and then form
        two new streams.  Fx should be a lambda or other function on elements.
        All elements where fx returns True go in the first stream.
        All other elements are put in the second stream.
        
        >>> stream1 = Stream()
        >>> for x in range(30,81):
        ...     n = note.Note()
        ...     n.offset = x
        ...     n.midi = x
        ...     stream1.insert(n)
        >>> fx = lambda n: n.midi > 60
        >>> b, c = stream1.splitByClass(note.Note, fx)
        >>> len(b)
        20
        >>> len(c)
        31
        '''
        a = self.__class__()
        b = self.__class__()
        found = self.getElementsByClass(objName)
        for e in found._elements:
            if fx(e):
                a.insert(e) # provide an offset here
            else:
                b.insert(e)
        for e in found._endElements:
            if fx(e):
                a.storeAtEnd(e)
            else:
                b.storeAtEnd(e)
        return a, b
            

    def _getOffsetMap(self, srcObj=None):
        '''Needed for makeMeasures and a few other places

        The Stream source of elements is self by default, unless a `srcObj` is provided. 
        '''
        if srcObj == None:
            srcObj = self
            
        # assume that flat/sorted options will be set before procesing
        offsetMap = [] # list of start, start+dur, element

        if srcObj.hasVoices():
            groups = []
            for i, v in enumerate(srcObj.voices):
                groups.append((v.flat, i))
        else: # create a single collection
            groups = [(srcObj, None)]

        for group, voiceIndex in groups:
            for e in group:
                # do not include barlines
                if isinstance(e, bar.Barline):
                    continue
                if hasattr(e, 'duration') and e.duration is not None:
                    dur = e.duration.quarterLength
                else:
                    dur = 0 
                # NOTE: rounding here may cause secondary problems
                offset = round(e.getOffsetBySite(group), 8)
                # NOTE: used to make a copy.copy of elements here; 
                # this is not necssary b/c making deepcopy of entire Stream
                offsetDict = {}
                offsetDict['offset'] = offset
                offsetDict['endTime'] = offset + dur
                offsetDict['element'] = e
                offsetDict['voiceIndex'] = voiceIndex
                offsetMap.append(offsetDict)
                #offsetMap.append((offset, offset + dur, e, voiceIndex))
                #offsetMap.append([offset, offset + dur, copy.copy(e)])
        return offsetMap

    offsetMap = property(_getOffsetMap, doc='''
        returns a list where each element is a dictionary
        consisting of the 'offset' of each element in a stream, the
        'endTime' (that is, the offset plus the duration) and the 
        'element' itself.  Also contains a 'voiceIndex' entry which
        contains the voice number of the element, or None if there
        are no voices.
        
        >>> from music21 import *
        >>> n1 = note.QuarterNote()
        >>> c1 = clef.AltoClef()
        >>> n2 = note.HalfNote()
        >>> s1 = stream.Stream()
        >>> s1.append([n1, c1, n2])
        >>> om = s1.offsetMap
        >>> om[2]['offset']
        1.0
        >>> om[2]['endTime']
        3.0
        >>> om[2]['element'] is n2
        True
        >>> om[2]['voiceIndex']
    ''')

    def makeMeasures(self, meterStream=None, refStreamOrTimeRange=None,
        inPlace=False):
        '''Take a stream and partition all elements into measures based on 
        one or more TimeSignature defined within the stream. If no TimeSignatures are defined, a default is used.

        This always creates a new stream with Measures, though objects are not
        copied from self stream. 
    
        If `meterStream` is provided, this is used to establish a sequence of :class:`~music21.meter.TimeSignature` objects, instead of any 
        found in the Stream. Alternatively, a TimeSignature object can be provided. 
    
        If `refStreamOrTimeRange` is provided, this is used to provide minimum and maximum offset values, necessary to fill empty rests and similar.

        If `inPlace` is True, this is done in-place; if `inPlace` is False, this returns a modified deep copy.
        
        
        A simple example: a single measure of 4/4 is created by adding three quarter
        rests to a stream:
        
        
        >>> from music21 import *
        >>> sSrc = stream.Stream()
        >>> sSrc.repeatAppend(note.Rest(), 3)
        >>> sMeasures = sSrc.makeMeasures()
        >>> len(sMeasures.getElementsByClass('Measure'))
        1
        >>> sMeasures[0].timeSignature
        <music21.meter.TimeSignature 4/4>

        >>> sSrc.insert(0.0, meter.TimeSignature('3/4'))
        >>> sMeasures = sSrc.makeMeasures()
        >>> sMeasures[0].timeSignature
        <music21.meter.TimeSignature 3/4>
            
        
        10 quarter notes are added to a stream, along with 10
        more quarter notes on the upbeat.  After makeMeasures
        is called, 3 measures of 4/4 are created:
        
    
        >>> sSrc = stream.Part()
        >>> n = note.Note()
        >>> n.quarterLength = 1
        >>> sSrc.repeatAppend(n, 10)
        >>> sSrc.repeatInsert(n, [x+.5 for x in range(10)])
        >>> sMeasures = sSrc.makeMeasures()
        >>> len(sMeasures.getElementsByClass('Measure'))
        3
        >>> sMeasures.__class__.__name__
        'Part'
        >>> sMeasures[0].timeSignature
        <music21.meter.TimeSignature 4/4>
        
        
        If after running makeMeasures you run makeTies, it will also split 
        long notes into smaller notes with ties.  Lyrics and articulations
        are attached to the first note.  Expressions (fermatas,
        etc.) will soon be attached to the last note but are NOT YET:
        
        >>> p1 = stream.Part()
        >>> p1.append(meter.TimeSignature('3/4'))
        >>> longNote = note.Note("D#4")
        >>> longNote.quarterLength = 7.5
        >>> longNote.articulations = [articulations.Staccato()]
        >>> longNote.lyric = "hello"
        >>> p1.append(longNote)
        >>> partWithMeasures = p1.makeMeasures()
        >>> dummy = partWithMeasures.makeTies(inPlace = True)
        >>> partWithMeasures.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.clef.TrebleClef object at 0x...>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note D#>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.note.Note D#>
        {6.0} <music21.stream.Measure 3 offset=6.0>
            {0.0} <music21.note.Note D#>
        >>> allNotes = partWithMeasures.flat.notes
        >>> [allNotes[0].articulations, allNotes[1].articulations, allNotes[2].articulations]
        [[<music21.articulations.Staccato>], [], []]
        >>> [allNotes[0].lyric, allNotes[1].lyric, allNotes[2].lyric]
        ['hello', None, None]
        '''
        #environLocal.printDebug(['calling Stream.makeMeasures()'])

        # the srcObj shold not be modified or chagned
        # removed element copying below and now making a deepcopy of entire stream
        # must take a flat representation, as we need to be able to 
        # position components, and sub-streams might hide elements that
        # should be contained

        if self.hasVoices():
            #environLocal.printDebug(['make measures found voices'])
            # cannot make flat here, as this would destroy stream partitions
            srcObj = copy.deepcopy(self.sorted)
            voiceCount = len(srcObj.voices)
        else:
            #environLocal.printDebug(['make measures found no voices'])
            # take flat and sorted version
            srcObj = copy.deepcopy(self.flat.sorted)
            voiceCount = 0

        #environLocal.printDebug(['Stream.makeMeasures(): passed in meterStream', meterStream, meterStream[0]])

        # may need to look in activeSite if no time signatures are found
        if meterStream is None:
            # get from this Stream, or search the contexts
            meterStream = srcObj.flat.getTimeSignatures(returnDefault=True, 
                          searchContext=False,
                          sortByCreationTime=False)
            environLocal.printDebug(['Stream.makeMeasures(): found meterStream', meterStream[0]])

        # if meterStream is a TimeSignature, use it
        elif isinstance(meterStream, meter.TimeSignature):
            ts = meterStream
            meterStream = Stream()
            meterStream.insert(0, ts)

        environLocal.printDebug(['Stream.makeMeasures(): srcObj.activeSite', srcObj.activeSite])


        #environLocal.printDebug(['makeMeasures(): meterStream', 'meterStream[0]', meterStream[0], 'meterStream[0].offset',  meterStream[0].offset, 'meterStream.elements[0].activeSite', meterStream.elements[0].activeSite])

        # get a clef for the entire stream; this will use bestClef
        # presently, this only gets the first clef
        # may need to store a clefStream and access changes in clefs
        # as is done with meterStream
        clefStream = srcObj.getClefs(searchActiveSite=True, searchContext=True,
                        returnDefault=True)
        clefObj = clefStream[0]

        #environLocal.printDebug(['makeMeasures(): first clef found after copying and flattening', clefObj])
    
        # for each element in stream, need to find max and min offset
        # assume that flat/sorted options will be set before procesing
        # list of start, start+dur, element
        offsetMap = srcObj.offsetMap
        #environLocal.printDebug(['makeMeasures(): offset map', offsetMap])    
        #offsetMap.sort() not necessary; just get min and max
        oMin = min([x['offset'] for x in offsetMap])
        oMax = max([x['endTime'] for x in offsetMap])
        
        # if a ref stream is provided, get highst time from there
        # only if it is greater thant the highest time yet encountered

        if refStreamOrTimeRange != None:
            if isinstance(refStreamOrTimeRange, Stream):
                refStreamHighestTime = refStream.highestTime
            else: # assume its a list
                refStreamHighestTime = max(refStreamOrTimeRange)    
            if refStreamHighestTime > oMax:
                oMax = refStreamHighestTime
    
        # create a stream of measures to contain the offsets range defined
        # create as many measures as needed to fit in oMax
        post = self.__class__()
        o = 0.0 # initial position of first measure is assumed to be zero
        measureCount = 0
        lastTimeSignature = None
        while True:    
            m = Measure()
            m.number = measureCount + 1

            #environLocal.printDebug(['handling measure', m, m.number, 'current offset value', o, meterStream._reprTextLine()])

            # get active time signature at this offset
            # make a copy and it to the meter
            thisTimeSignature = meterStream.getElementAtOrBefore(o)

            #environLocal.printDebug(['meterStream.getElementAtOrBefore(o)', meterStream.getElementAtOrBefore(o), 'lastTimeSignature', lastTimeSignature, 'thisTimeSignature', thisTimeSignature ])

            if thisTimeSignature is None and lastTimeSignature is None:
                raise StreamException('failed to find TimeSignature in meterStream; cannot process Measures')

            if thisTimeSignature is not lastTimeSignature and thisTimeSignature is not None:
                lastTimeSignature = thisTimeSignature
                # this seems redundant
                #lastTimeSignature = meterStream.getElementAtOrBefore(o)
                m.timeSignature = deepcopy(thisTimeSignature)
                #environLocal.printDebug(['assigned time sig', m.timeSignature])

            # only add a clef for the first measure when automatically 
            # creating Measures; this clef is from getClefs, called above
            if measureCount == 0: 
                m.clef = clefObj
                #environLocal.printDebug(['assigned clef to measure', measureCount, m.clef])    

            # add voices if necessary (voiceCount > 0)
            for voiceIndex in range(voiceCount):
                v = Voice()
                v.id = voiceIndex # id is voice index, starting at 0
                m.insert(0, v)

            # avoid an infinite loop
            if thisTimeSignature.barDuration.quarterLength == 0:
                raise StreamException('time signature has no duration')    
            post.insert(o, m) # insert measure
            # increment by meter length
            o += thisTimeSignature.barDuration.quarterLength 
            if o >= oMax: # may be zero
                break # if length of this measure exceedes last offset
            else:
                measureCount += 1
        
        # populate measures with elements
        for ob in offsetMap:
            start, end, e, voiceIndex = ob['offset'], ob['endTime'], ob['element'], ob['voiceIndex']
            
            # iterate through all measures, finding a measure that 
            # can contain this element
            match = False
            lastTimeSignature = None
            for i in range(len(post)):
                m = post[i]
                if m.timeSignature is not None:
                    lastTimeSignature = m.timeSignature
                # get start and end offsets for each measure
                # seems like should be able to use m.duration.quarterLengths
                mStart = m.getOffsetBySite(post)
                mEnd = mStart + lastTimeSignature.barDuration.quarterLength
                # if elements start fits within this measure, break and use 
                # offset cannot start on end
                if start >= mStart and start < mEnd:
                    match = True
                    #environLocal.printDebug(['found measure match', i, mStart, mEnd, start, end, e])
                    break
            if not match:
                raise StreamException('cannot place element %s with start/end %s/%s within any measures' % (e, start, end))

            # find offset in the temporal context of this measure
            # i is the index of the measure that this element starts at
            # mStart, mEnd are correct
            oNew = start - mStart # remove measure offset from element offset

            # insert element at this offset in the measure
            # not copying elements here!
            # in the case of a Clef, and possibly other measure attributes, 
            # the element may have already been placed in this measure
            #environLocal.printDebug(['compare e, clef', e, m.clef])
            if m.clef == e:
                continue

            if voiceIndex == None:
                m.insert(oNew, e)
            else: # insert into voice specified by the voice index
                m.voices[voiceIndex].insert(oNew, e)

        return post # returns a new stream populated w/ new measure streams


    def makeRests(self, refStreamOrTimeRange=None, fillGaps=False,
        inPlace=True):
        '''
        Given a Stream with an offset not equal to zero, 
        fill with one Rest preeceding this offset. 
    
        If `refStreamOrTimeRange` is provided as a Stream, this 
        Stream is used to get min and max offsets. If a list is provided, 
        the list assumed to provide minimum and maximum offsets. Rests will 
        be added to fill all time defined within refStream.

        If `fillGaps` is True, this will create rests in any time regions that have no active elements.

        If `inPlace` is True, this is done in-place; if `inPlace` is False, 
        this returns a modified deepcopy.
        
        >>> a = Stream()
        >>> a.insert(20, note.Note())
        >>> len(a)
        1
        >>> a.lowestOffset
        20.0
        >>> b = a.makeRests()
        >>> len(b)
        2
        >>> b.lowestOffset
        0.0

        OMIT_FROM_DOCS
        TODO: if inPlace == True, this should return None
        '''
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        #environLocal.printDebug(['makeRests(): object lowestOffset, highestTime', oLow, oHigh])
        if refStreamOrTimeRange == None: # use local
            oLowTarget = 0
            oHighTarget = returnObj.highestTime
        elif isinstance(refStreamOrTimeRange, Stream):
            oLowTarget = refStreamOrTimeRange.lowestOffset
            oHighTarget = refStreamOrTimeRange.highestTime
            #environLocal.printDebug(['refStream used in makeRests', oLowTarget, oHighTarget, len(refStreamOrTimeRange)])
        # treat as a list
        elif common.isListLike(refStreamOrTimeRange):
            oLowTarget = min(refStreamOrTimeRange)
            oHighTarget = max(refStreamOrTimeRange)
            #environLocal.printDebug(['refStream used in makeRests', oLowTarget, oHighTarget, len(refStreamOrTimeRange)])

        if returnObj.hasVoices():
            bundle = returnObj.voices
        else:
            bundle = [returnObj]

        for v in bundle:
            oLow = v.lowestOffset
            oHigh = v.highestTime
            qLen = oLow - oLowTarget
            if qLen > 0:
                r = note.Rest()
                r.duration.quarterLength = qLen
                #environLocal.printDebug(['makeRests(): add rests', r, r.duration])
                # place at oLowTarget to reach to oLow
                v.insert(oLowTarget, r)
            qLen = oHighTarget - oHigh
            if qLen > 0:
                r = note.Rest()
                r.duration.quarterLength = qLen
                # place at oHigh to reach to oHighTarget
                v.insert(oHigh, r)
            if fillGaps:
                gapStream = v.findGaps()
                if gapStream != None:
                    for e in gapStream:
                        r = note.Rest()
                        r.duration.quarterLength = e.duration.quarterLength
                        v.insert(e.offset, r)
            v.isSorted = False

        # with auto sort no longer necessary. 
        
        #returnObj.elements = returnObj.sorted.elements
        self.isSorted = False
        return returnObj


    def makeTies(self, meterStream=None, inPlace=True, 
        displayTiedAccidentals=False):
        '''Given a stream containing measures, examine each element in the Stream. If the elements duration extends beyond the measures boundary, create a tied entity, placing the split Note in the next Measure.

        Note that his method assumes that there is appropriate space in the next Measure: this will not shift Note, but instead allocate them evenly over barlines. Generall, makeMeasures is called prior to calling this method.
    
        If `inPlace` is True, this is done in-place; if `inPlace` is False, this returns a modified deep copy.
                
        >>> d = Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 12
        >>> d.repeatAppend(n, 10)
        >>> d.repeatInsert(n, [x+.5 for x in range(10)])
        >>> x = d.makeMeasures()
        >>> x = x.makeTies()
    
        OMIT_FROM_DOCS
        TODO: take a list of clases to act as filter on what elements are tied.

        configure ".previous" and ".next" attributes

        '''
        #environLocal.printDebug(['calling Stream.makeTies()'])

        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self
        if len(returnObj) == 0:
            raise StreamException('cannot process an empty stream')        
    
        # get measures from this stream
        measureStream = returnObj.getElementsByClass('Measure')
        if len(measureStream) == 0:
            raise StreamException('cannot process a stream without measures')        
    
        #environLocal.printDebug(['makeTies() processing measureStream, length', measureStream, len(measureStream)])

        # may need to look in activeSite if no time signatures are found
        # presently searchContext is False to save time
        if meterStream is None:
            meterStream = returnObj.getTimeSignatures(sortByCreationTime=True,             
                          searchContext=False)
    
        mCount = 0
        lastTimeSignature = None
        while True:
            # update measureStream on each iteration, 
            # as new measure may have been added to the returnObj stream 
            measureStream = returnObj.getElementsByClass(Measure)
            if mCount >= len(measureStream):
                break # reached the end of all measures available or added
            # get the current measure to look for notes that need ties
            m = measureStream[mCount]
            if m.timeSignature is not None:
                lastTimeSignature = m.timeSignature

            # get next measure; we may not need it, but have it ready
            if mCount + 1 < len(measureStream):
                mNext = measureStream[mCount+1]
                mNextAdd = False # already present; do not append
            else: # create a new measure
                mNext = Measure()
                # set offset to last offset plus total length
                moffset = m.getOffsetBySite(measureStream)
                mNext.offset = (moffset + 
                                lastTimeSignature.barDuration.quarterLength)
                if len(meterStream) == 0: # in case no meters are defined
                    ts = meter.TimeSignature()
                    ts.load('%s/%s' % (defaults.meterNumerator, 
                                       defaults.meterDenominatorBeatType))
                else: # get the last encountered meter
                    ts = meterStream.getElementAtOrBefore(mNext.offset)
                # only copy and assign if not the same as the last
                if not lastTimeSignature.ratioEqual(ts):
                    mNext.timeSignature = deepcopy(ts)
                # increment measure number
                mNext.number = m.number + 1
                mNextAdd = True # new measure, needs to be appended

            if mNext.hasVoices():
                mNextHasVoices = True
            else:
                mNextHasVoices = False
    
            #environLocal.printDebug(['makeTies() dealing with measure', m, 'mNextAdd', mNextAdd])
            # for each measure, go through each element and see if its
            # duraton fits in the bar that contains it
            mStart, mEnd = 0, lastTimeSignature.barDuration.quarterLength
            if m.hasVoices():
                bundle = m.voices
                mHasVoices = True
            else:
                bundle = [m]
                mHasVoices = False
            # bundle components may be voices, or just a measure
            for v in bundle:
                for e in v:
                    #environLocal.printDebug(['Stream.makeTies() iterating over elements in measure', m, e])
    
                    if hasattr(e, 'duration') and e.duration is not None:
                        # check to see if duration is within Measure
                        eOffset = e.getOffsetBySite(v)
                        eEnd = eOffset + e.duration.quarterLength
                        # assume end can be at boundary of end of measure
                        overshot = eEnd - mEnd
                        # only process if overshot is greater than a minimum
                        # 1/64 is 0.015625
                        if overshot > .001:
                            if eOffset >= mEnd:
                                raise StreamException('element (%s) has offset %s within a measure that ends at offset %s' % (e, eOffset, mEnd))  
        
                            qLenBegin = mEnd - eOffset    
                            e, eRemain = e.splitAtQuarterLength(qLenBegin, 
                                retainOrigin=True, 
                                displayTiedAccidentals=displayTiedAccidentals)
        
                            # manage bridging voices
                            if mNextHasVoices:
                                if mHasVoices: # try to match voice id
                                    dst = mNext.voices[v.id]
                                # src does not have voice, but dst does
                                else: # place in top-most voice
                                    dst = mNext.voices[0]
                            else:
                                # mNext has no voices but this one does    
                                if mHasVoices:
                                    # internalize all components in a voice
                                    mNext.internalize(container=Voice)
                                    # place in first voice
                                    dst = mNext.voices[0]
                                else: # no voices in either
                                    dst = mNext

                            #eRemain.activeSite = mNext 
                            # manually set activeSite   
                            dst.insert(0, eRemain)
    
                            # we are not sure that this element fits 
                            # completely in the next measure, thus, need to 
                            # continue processing each measure
                            if mNextAdd:
                                environLocal.printDebug(['makeTies() inserting mNext into returnObj', mNext])
                                returnObj.insert(mNext.offset, mNext)
                        elif overshot > 0:
                            environLocal.printDebug(['makeTies() found and skipping extremely small overshot into next measure', overshot])
            mCount += 1

        return returnObj
    

    def makeBeams(self, inPlace=True):
        '''Return a new measure with beams applied to all notes. 

        In the process of making Beams, this method also updates tuplet types. This is destructive and thus changes an attribute of Durations in Notes.

        If `inPlace` is True, this is done in-place; if `inPlace` is False, this returns a modified deep copy.

        >>> aMeasure = Measure()
        >>> aMeasure.timeSignature = meter.TimeSignature('4/4')
        >>> aNote = note.Note()
        >>> aNote.quarterLength = .25
        >>> aMeasure.repeatAppend(aNote,16)
        >>> bMeasure = aMeasure.makeBeams()

        OMIT_FROM_DOCS
        TODO: inPlace=False does not work in many cases
        '''

        environLocal.printDebug(['calling Stream.makeBeams()'])
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        #if self.isClass(Measure):
        if 'Measure' in self.classes:
            mColl = [] # store a list of measures for processing
            mColl.append(returnObj)
        elif len(self.getElementsByClass('Measure')) > 0:
            mColl = returnObj.getElementsByClass('Measure') # a stream of measures
        else:
            raise StreamException('cannot process a stream that neither is a Measure nor has Measures')        

        lastTimeSignature = None
        
        for m in mColl:
            # this means that the first of a stream of time signatures will
            # be used
            if m.timeSignature is not None:
                lastTimeSignature = m.timeSignature
            if lastTimeSignature is None:
                raise StreamException('cannot proces beams in a Measure without a time signature')

            #environLocal.printDebug(['makeBeams(): lastTimeSignature', lastTimeSignature])

            noteGroups = []
            if m.hasVoices():
                for v in m.voices:
                    noteGroups.append(v.notes)
            else:
                noteGroups.append(m.notes)

            #environLocal.printDebug(['noteGroups', noteGroups, 'len(noteGroups[0])',  len(noteGroups[0])])

            for noteStream in noteGroups:
                if len(noteStream) <= 1: 
                    continue # nothing to beam
    
                durList = []
                for n in noteStream:
                    durList.append(n.duration)
    
                #environLocal.printDebug(['beaming with ts', lastTimeSignature, 'measure', m, durList, noteStream[0], noteStream[1]])
    
                # error check; call before sending to time signature, as, if this
                # fails, it represents a problem that happens before time signature
                # processing
    
                durSum = sum([d.quarterLength for d in durList])
                barQL = lastTimeSignature.barDuration.quarterLength
    
                if durSum > barQL:
                    environLocal.printDebug(['attempting makeBeams with a bar that contains durations that sum greater than bar duration (%s > %s)' % (durSum, barQL)])
                    continue
            
                # getBeams can take a list of Durations; however, this cannot
                # distinguish a Note from a Rest; thus, we can submit a flat 
                # stream of note or note-like entities; will return
                # the saem lost of beam objects
                beamsList = lastTimeSignature.getBeams(noteStream)
                for i in range(len(noteStream)):
                    # this may try to assign a beam to a Rest
                    noteStream[i].beams = beamsList[i]
                # apply tuple types in place; this modifies the durations 
                # in dur lost
                duration.updateTupletType(durList)

        return returnObj


    def makeTupletBrackets(self, inPlace=True):
        '''Given a Stream of mixed durations, the first and last tuplet of any group of tuplets must be designated as the start and end. 

        Need to not only look at Notes, but components within Notes, as these might contain additional tuplets.
        '''

        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self
        
        open = False
        tupletCount = 0
        lastTuplet = None

        # only want to look at notes
        notes = returnObj.notes
        durList = []
        for e in notes:
            for d in e.duration.components: 
                durList.append(d)

        eCount = len(durList)

        #environLocal.printDebug(['calling makeTupletBrackets, lenght of notes:', eCount])

        for i in range(eCount):
            e = durList[i]
            if e != None:
                if e.tuplets == None:
                    continue
                tContainer = e.tuplets
                #environLocal.printDebug(['makeTupletBrackets', tContainer])
                if len(tContainer) == 0:
                    t = None
                else:
                    t = tContainer[0] # get first?
                
                # end case: this Note does not have a tuplet
                if t == None:
                    if open == True: # at the end of a tuplet span
                        open = False
                        # now have a non-tuplet, but the tuplet span was only
                        # one tuplet long; do not place a bracket
                        if tupletCount == 1:        
                            lastTuplet.type = 'startStop'
                            lastTuplet.bracket = False
                        else:
                            lastTuplet.type = 'stop'
                    tupletCount = 0
                else: # have a tuplet
                    tupletCount += 1
                    # store this as the last tupelt
                    lastTuplet = t

                    #environLocal.printDebug(['makeTupletBrackets', e, 'existing typlet type', t.type, 'bracket', t.bracket, 'tuplet count:', tupletCount])
                        
                    # already open bracket
                    if open:
                        # end case: this is the last element and its a tuplet
                        # since this is an open bracket, we know we have more 
                        # than one tuplet in this span
                        if i == eCount - 1:
                            t.type = 'stop'
                        # if this the middle of a span, do nothing
                        else:
                            pass
                    else: # need to open
                        open = True
                        # if this is the last event in this Stream
                        # do not create bracket
                        if i == eCount - 1:
                            t.type = 'startStop'
                            t.bracket = False
                        # normal start of tuplet span
                        else:
                            t.type = 'start'
            
#                 if t != None:
#                     environLocal.printDebug(['makeTupletBrackets', e, 'final type', t.type, 'bracket', t.bracket])

        return returnObj


    def makeAccidentals(self, pitchPast=None, useKeySignature=True, 
        alteredPitches=None, searchKeySignatureByContext=False, 
        cautionaryPitchClass=True, cautionaryAll=False, inPlace=True, overrideStatus=False, cautionaryNotImmediateRepeat=True): 
        '''A method to set and provide accidentals given varous conditions and contexts.

        If `useKeySignature` is True, a :class:`~music21.key.KeySignature` will be searched for in this Stream or this Stream's defined contexts. An alternative KeySignature can be supplied with this object and used for temporary pitch processing. 

        If `alteredPitches` is a list of modified pitches (Pitches with Accidentals) that can be directly supplied to Accidental processing. These are the same values obtained from a :class:`music21.key.KeySignature` object using the :attr:`~music21.key.KeySignature.alteredPitches` property. 

        If `cautionaryPitchClass` is True, comparisons to past accidentals are made regardless of register. That is, if a past sharp is found two octaves above a present natural, a natural sign is still displayed. 

        If `cautionaryAll` is True, all accidentals are shown.

        If `overrideStatus` is True, this method will ignore any current `displayStatus` stetting found on the Accidental. By default this does not happen. If `displayStatus` is set to None, the Accidental's `displayStatus` is set. 

        If `cautionaryNotImmediateRepeat` is True, cautionary accidentals will be displayed for an altered pitch even if that pitch had already been displayed as altered. 

        The :meth:`~music21.pitch.Pitch.updateAccidentalDisplay` method is used to determine if an accidental is necessary.

        This will assume that the complete Stream is the context of evaluation. For smaller context ranges, call this on Measure objects. 

        If `inPlace` is True, this is done in-place; if `inPlace` is False, this returns a modified deep copy.

        '''
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        # need to reset these lists unless values explicitly provided
        if pitchPast == None:
            pitchPast = []
        # see if there is any key signatures to add to altered pitches
        if alteredPitches == None:
            alteredPitches = []

        addAlteredPitches = []
        if isinstance(useKeySignature, key.KeySignature):
            addAlteredPitches = useKeySignature.alteredPitches
        elif useKeySignature == True: # get from defined contexts
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
        noteStream = returnObj.sorted.notes

        # get chords, notes, and rests
        for i in range(len(noteStream)):
            e = noteStream[i]
            if isinstance(e, note.Note):
                e.pitch.updateAccidentalDisplay(pitchPast, alteredPitches,
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll,
                    overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat)
                pitchPast.append(e.pitch)
            elif isinstance(e, chord.Chord):
                pGroup = e.pitches
                # add all chord elements to past first
                # when reading a chord, this will apply an accidental 
                # if pitches in the chord suggest an accidental
                for p in pGroup:
                    p.updateAccidentalDisplay(pitchPast, alteredPitches, 
                        cautionaryPitchClass=cautionaryPitchClass, cautionaryAll=cautionaryAll,
                        overrideStatus=overrideStatus,
                    cautionaryNotImmediateRepeat=cautionaryNotImmediateRepeat)
                pitchPast += pGroup

        return returnObj



    def makeNotation(self, meterStream=None, refStreamOrTimeRange=None,
                        inPlace=False):
        '''This method calls a sequence of Stream methods on this Stream to prepare notation, including creating Measures if necessary, creating ties, beams, and accidentals.

        If `inPlace` is True, this is done in-place; if `inPlace` is False, this returns a modified deep copy.

        >>> from music21 import stream, note
        >>> s = stream.Stream()
        >>> n = note.Note('g')
        >>> n.quarterLength = 1.5
        >>> s.repeatAppend(n, 10)
        >>> sMeasures = s.makeNotation()
        >>> len(sMeasures.getElementsByClass('Measure'))
        4
        '''
        # only use inPlace arg on first usage
        measureStream = self.makeMeasures(meterStream=meterStream,
            refStreamOrTimeRange=refStreamOrTimeRange, inPlace=inPlace)

        #environLocal.printDebug(['Stream.makeNotation(): post makeMeasures, length', len(measureStream)])

        # for now, calling makeAccidentals once per measures       
        # pitches from last measure are passed
        # this needs to be called before makeTies
        # note that this functionality is also placed in Part
        ksLast = None
        for i in range(len(measureStream)):
            m = measureStream[i]
            if m.keySignature != None:
                ksLast = m.keySignature
            if i > 0:
                m.makeAccidentals(measureStream[i-1].pitches,
                    useKeySignature=ksLast, searchKeySignatureByContext=False)
            else:
                m.makeAccidentals(useKeySignature=ksLast, 
                    searchKeySignatureByContext=False)

        #environLocal.printDebug(['makeNotation(): meterStream:', meterStream, meterStream[0]])
        measureStream.makeTies(meterStream, inPlace=True)

        #measureStream.makeBeams(inPlace=True)
        try:
            measureStream.makeBeams(inPlace=True)
        except StreamException:
            # this is a result of makeMeaures not getting everything 
            # note to measure allocation right
            environLocal.printDebug(['skipping makeBeams exception', 
                                    StreamException])

        # note: this needs to be after makeBeams, as placing this before
        # makeBeams was causing the duration's tuplet to loose its type setting
        # check for tuplet brackets one measure at a time       
        # this means that they will never extend beyond one measure
        for m in measureStream.getElementsByClass('Measure'):
            m.makeTupletBrackets(inPlace=True)

        if len(measureStream) == 0:            
            raise StreamException('no measures found in stream with %s elements' % (self.__len__()))
        environLocal.printDebug(['Stream.makeNotation(): created measures:', len(measureStream)])

        return measureStream



    def extendDuration(self, objName, inPlace=True):
        '''Given a Stream and an object class name, go through the Stream 
        and find each instance of the desired object. The time between 
        adjacent objects is then assigned to the duration of each object. 
        The last duration of the last object is assigned to extend to the 
        end of the Stream.

        If `inPlace` is True, this is done in-place; if `inPlace` is 
        False, this returns a modified deep copy.
        
        >>> import music21.dynamics
        >>> stream1 = Stream()
        >>> n = note.QuarterNote()
        >>> n.duration.quarterLength
        1.0
        >>> stream1.repeatInsert(n, [0, 10, 20, 30, 40])
        >>> dyn = music21.dynamics.Dynamic('ff')
        >>> stream1.insert(15, dyn)
        >>> sort1 = stream1.sorted
        >>> sort1[-1].offset # offset of last element
        40.0
        >>> sort1.duration.quarterLength # total duration
        41.0
        >>> len(sort1)
        6
    
        >>> stream2 = sort1.flat.extendDuration(note.GeneralNote)
        >>> len(stream2)
        6
        >>> stream2[0].duration.quarterLength
        10.0
        >>> stream2[1].duration.quarterLength # all note durs are 10
        10.0
        >>> stream2[-1].duration.quarterLength # or extend to end of stream
        1.0
        >>> stream2.duration.quarterLength
        41.0
        >>> stream2[-1].offset
        40.0

        OMIT_FROM_DOCS
        TODO: Chris; what file is testFiles.ALL[2]?? 
        
#        >>> from music21.musicxml import testFiles
#        >>> from music21 import converter
#        >>> mxString = testFiles.ALL[2] # has dynamics
#        >>> a = converter.parse(mxString)
#        >>> b = a.flat.extendDuration(dynamics.Dynamic)    
        '''
    
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        # Should we do this?  or just return an exception if not there.
        # this cannot work unless we use a sorted representation
        returnObj = returnObj.sorted

        qLenTotal = returnObj.duration.quarterLength
        elements = []
        for element in returnObj.getElementsByClass(objName):
            if not hasattr(element, 'duration'):
                raise StreamException('can only process objects with duration attributes')
            if element.duration is None:
                element.duration = duration.Duration()
            elements.append(element)
    
        #print elements[-1], qLenTotal, elements[-1].duration
        # print _MOD, elements
        for i in range(len(elements)-1):
            #print i, len(elements)
            span = elements[i+1].getOffsetBySite(self) - elements[i].getOffsetBySite(self)
            elements[i].duration.quarterLength = span
    
        # handle last element
        #print elements[-1], qLenTotal, elements[-1].duration
        elements[-1].duration.quarterLength = (qLenTotal -
                    elements[-1].getOffsetBySite(self))
        #print elements[-1], elements[-1].duration    
        return returnObj
    


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
        for sequential notes with matching pitches. The matchByPitch option can 
        be used to use this technique. 

        >>> a = Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 6
        >>> a.append(n)
        >>> m = a.makeMeasures()
        >>> m = m.makeTies()
        >>> len(m.flat.notes)
        2
        >>> m = m.stripTies()
        >>> len(m.flat.notes)
        1
        >>> 
        '''
        #environLocal.printDebug(['calling stripTies'])
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Part'):
                # already copied if necessary; edit in place
                # when handling a score, retain containers should be true
                p.stripTies(inPlace=True, matchByPitch=matchByPitch,
                            retainContainers=True)
            return returnObj # exit

        # not sure if this must be sorted
        # but: tied notes must be in consecutive order
        #  returnObj = returnObj.sorted
        notes = returnObj.flat.notes

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
                    # find out if the the last index is in position connected
                    # if the pitches are the same for each note
                    if (nLast is not None and iLast in posConnected 
                        and hasattr(nLast, "pitch") and hasattr(n, "pitch")
                        and nLast.pitch == n.pitch):
                        endMatch = True

            # process end condition
            if endMatch:
                posConnected.append(i) # add this last position
                if len(posConnected) < 2:
                    # an open tie, not connected to anything
                    # should be an error; presently, just skipping
                    #raise StreamException('cannot consolidate ties when only one tie is present', notes[posConnected[0]])
                    environLocal.printDebug(['cannot consolidate ties when only one tie is present', notes[posConnected[0]]])
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
                for sub in reversed(returnObj.getElementsByClass(Measure)):
                    try:
                        i = sub.index(nTarget)
                    except ValueError:
                        continue
                    junk = sub.pop(i)
                    # get a new note
                    # we should not continue searching Measures
                    break 
            return returnObj

        else:
            for i in posDelete:
                # removing the note from notes
                junk = notes.pop(i)
            return notes


    #---------------------------------------------------------------------------

    def sort(self):
        '''
        Sort this Stream in place by offset, then priority, then 
        standard class sort order (e.g., Clefs before KeySignatures before
        TimeSignatures).

        Note that Streams automatically sort themsevlves unless
        autoSort is set to False (as in the example below)


        >>> from music21 import *
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
        self._elements.sort(
            cmp=lambda x,y: cmp(
                x.getOffsetBySite(self), y.getOffsetBySite(self)
                ) or cmp(x.priority, y.priority) or 
                cmp(x.classSortOrder, y.classSortOrder)
            )
        self._endElements.sort(
            cmp=lambda x,y: cmp(x.priority, y.priority) or 
                cmp(x.classSortOrder, y.classSortOrder)
            )
        # as sorting changes order, elements have changed 
        self._elementsChanged()
        self.isSorted = True


    def _getSorted(self):
        # get a shallow copy of elements list
        post = copy.copy(self._elements) # already a copy
#         post.sort(cmp=lambda x,y: cmp(x.getOffsetBySite(self),
#             y.getOffsetBySite(self)) or 
#             cmp(x.priority, y.priority) or 
#             cmp(x.classSortOrder, y.classSortOrder)
#             )
        # get a shallow copy of the Stream itself
        newStream = copy.copy(self)
        # assign directly to _elements, as we do not need to call 
        # _elementsChanged()
        newStream._elements = post
        for e in post:
            e.addLocation(newStream, e.getOffsetBySite(self))
            # need to explicitly set activeSite
            e.activeSite = newStream 
#         newStream.isSorted = True

        # now just sort this stream in place; this will update the 
        # isSorted attribute
        newStream.sort()
        return newStream
    
    sorted = property(_getSorted, doc='''
        Returns a new Stream where all the elements are sorted according to offset time, then
        priority, then classSortOrder (so that, for instance, a Clef at offset 0 appears before
        a Note at offset 0)
        
        if this Stream is not flat, then only the highest elements are sorted.  To sort all,
        run myStream.flat.sorted
        
        For instance, here is an unsorted Stream
        
        >>> from music21 import *
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

        
    def _getFlatOrSemiFlat(self, retainContainers):
        '''The `retainContainers` option, if True, returns a semiFlat version: containers are not discarded in flattening.
        '''
        #environLocal.printDebug(['_getFlatOrSemiFlat(): self', self, 'self.activeSite', self.activeSite])       

        # this copy will have a shared locations object
        # not that copy.copy() in some cases seems to not cause secondary
        # problems that self.__class__() does
        sNew = copy.copy(self)
        #sNew = self.__class__()

        # storing .elements in here necessitates
        # create a new, independent cache instance in the flat representation
        sNew._cache = common.defHash()
        sNew._elements = []
        sNew._endElements = []
        sNew._elementsChanged()

        #environLocal.printDebug(['_getFlatOrSemiFlat(), sNew id', id(sNew)])
        for e in self._elements:
            # check for stream instance instead
            # if this element is a Stream, recurse
            #if isinstance(e, Stream): 
            if hasattr(e, "elements"): 
                recurseStreamOffset = e.getOffsetBySite(self)
                if retainContainers is True: # semiFlat
                    #environLocal.printDebug(['_getFlatOrSemiFlat(), retaining containers, storing element:', e])

                    # this will change the activeSite of e to be sNew, previously
                    # this was the activeSite was the caller; thus, the activeSite here
                    # should not be set
                    sNew.insert(recurseStreamOffset, e, setActiveSite=False)
                    recurseStream = e.semiFlat
                else:
                    recurseStream = e.flat
                
                #environLocal.printDebug("recurseStreamOffset: " + str(e.id) + " " + str(recurseStreamOffset))
                # recurse Stream is the flat or semiFlat contents of a Stream
                # contained within the caller
                for subEl in recurseStream:
                    oldOffset = subEl.getOffsetBySite(recurseStream)
                    sNew.insert(oldOffset + recurseStreamOffset, subEl)

                    #environLocal.printDebug(['subElement', id(subEl), 'inserted in', sNew, 'id(sNew)', id(sNew)])

            # if element not a stream
            else:
                # insert into new stream at offset in old stream
                sNew.insert(e.getOffsetBySite(self), e)
    
        # highest time elements should never be Streams
        for e in self._endElements:
            sNew.storeAtEnd(e)

        sNew.isFlat = True
        # here, we store the source stream from which this stream was derived
        # TODO: this should probably be a weakref
        sNew.flattenedRepresentationOf = self #common.wrapWeakref(self)

#         environLocal.printDebug(['_getFlatOrSemiFlat: break2: self', self, 'self.activeSite', self.activeSite])       

        return sNew
    

    def _getFlat(self):
        '''
        Returns a new Stream where no elements nest within other elements
        
        >>> s = Stream()
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

        >>> q = Stream()
        >>> for i in range(5):
        ...   p = Stream()
        ...   p.repeatInsert(music21.Music21Object(), range(5))
        ...   q.insert(i * 10, p) 
        >>> len(q)
        5
        >>> qf = q.flat
        >>> len(qf)        
        25
        >>> qf[24].offset
        44.0

        OMIT_FROM_DOCS
        >>> r = Stream()
        >>> for j in range(5):
        ...   q = Stream()
        ...   for i in range(5):
        ...      p = Stream()
        ...      p.repeatInsert(music21.Music21Object(), range(5))
        ...      q.insert(i * 10, p) 
        ...   r.insert(j * 100, q)
        >>> len(r)
        5
        >>> len(r.flat)
        125
        >>> r.flat[124].offset
        444.0
        '''
#         reCache = False
#         if self._cache["flat"] == None:
#             reCache = True
#         # see if the ached Stream has cahced elements: if not, this
#         # likely means that they have changed and that that Stream is no 
#         # longer a good cached stream
#         elif len(self._cache["flat"]._cache) == 0:
#             reCache = True
# 
#         if reCache:
#             #environLocal.printDebug(['reCache: flat', reCache, 'self', self])
#             if self.isFlat:
#                 self._cache["flat"] = self
#             else:
#                 self._cache["flat"] = self._getFlatOrSemiFlat(
#                 retainContainers=False)
# 
#         #environLocal.printDebug(['cached: flat', self._cache["flat"], id(self._cache["flat"]), 'len', len(self._cache["flat"])])
# 
#         return self._cache["flat"]

        return self._getFlatOrSemiFlat(retainContainers=False)

    flat = property(_getFlat, 
        doc='''Return a new Stream that has all sub-container flattened within.
        ''')


    def _getSemiFlat(self):
        return self._getFlatOrSemiFlat(retainContainers = True)


    semiFlat = property(_getSemiFlat, doc='''
        Returns a flat-like Stream representation. Stream sub-classed containers, such as Measure or Part, are retained in the output Stream, but positioned at their relative offset. 
        ''')


    def _yieldElementsDownward(self, excludeNonContainers=True):
        '''Yield all containers (Stream subclasses), including self, and going downward.
        '''
        yield self
        # using indices so as to not to create an iterator and new locations/activeSites
        for i in range(len(self._elements)):
            # not using __getitem__, also to avoid new locations/activeSites
            e = self._elements[i]
            if hasattr(e, 'elements'):
                # this returns a generator, so need to iterate over it
                # to get results
                for y in e._yieldElementsDownward(
                        excludeNonContainers=excludeNonContainers):
                    yield y
            # its an element on the Stream that is not a Stream
            else:
                if not excludeNonContainers:
                    yield e


    def _yieldElementsUpward(self, memo, excludeNonContainers=True, 
                             skipDuplicates=True):
        '''Yield all containers (Stream subclasses), including self, and going upward.

        Note: on first call, a new, fresh memo list must be provided; otherwise, values are retained from one call to the next.
        '''
        if id(self) not in memo:
            yield self
            #environLocal.printDebug(['memoing:', self, memo])
            if skipDuplicates:
                memo.append(id(self))

        # may need to make sure that activeSite is correctly assigned
        p = self.activeSite
        # if a activeSite exists, its always a stream!
        if p != None and hasattr(p, 'elements'):
            # using indices so as to not to create an iterator and new locations/activeSites
            # here we access the private _elements, again: no iterator
            for i in range(len(p._elements)):
                # not using __getitem__, also to avoid new locations/activeSites
                e = p._elements[i]
                #environLocal.printDebug(['examining elements:', e])

                # not a Stream; may or may not have a activeSite;
                # its possible that it may have activeSite not identified elsewhere
                if not hasattr(e, 'elements'):
                    if not excludeNonContainers:
                        if id(e) not in memo:
                            yield e
                            if skipDuplicates:
                                memo.append(id(e))

                # for each element in the activeSite that is a Stream, 
                # look at the activeSites
                # if the activeSites are a Stream, recurse
                elif (hasattr(e, 'elements') and e.activeSite != None 
                    and hasattr(e.activeSite, 'elements')):

                    # this returns a generator, so need to iterate over it
                    # to get results
                    # e.activeSite will be yielded at top of recurse
                    for y in e.activeSite._yieldElementsUpward(memo,
                            skipDuplicates=skipDuplicates, 
                            excludeNonContainers=excludeNonContainers):
                        yield y
                    # here, we have found a container at the same level of
                    # the caller; since it is a Stream, we yield
                    # caller is contained in the activeSite; if e is self, skip
                    if id(e) != id(self): 
                        if id(e) not in memo:
                            yield e
                            if skipDuplicates:
                                memo.append(id(e))

    #---------------------------------------------------------------------------
    # duration and offset methods and properties
    
    def _getHighestOffset(self):
        '''
        >>> p = Stream()
        >>> p.repeatInsert(note.Note("C"), range(5))
        >>> p.highestOffset
        4.0
        '''
        if self._cache["HighestOffset"] is not None:
            pass # return cache unaltered
        elif len(self._elements) == 0:
            self._cache["HighestOffset"] = 0.0
        elif self.isSorted is True:
            eLast = self._elements[-1]
            self._cache["HighestOffset"] = eLast.getOffsetBySite(self) 
        else: # iterate through all elements
            max = None
            for e in self._elements:
                candidateOffset = e.getOffsetBySite(self)
                if max is None or candidateOffset > max:
                    max = candidateOffset
            self._cache["HighestOffset"] = max
        return self._cache["HighestOffset"]

    highestOffset = property(_getHighestOffset, 
        doc='''Get start time of element with the highest offset in the Stream.
        Note the difference between this property and highestTime
        which gets the end time of the highestOffset

        >>> stream1 = Stream()
        >>> for offset in [0, 4, 8]:
        ...     n = note.WholeNote('G#')
        ...     stream1.insert(offset, n)
        >>> stream1.highestOffset
        8.0
        >>> stream1.highestTime
        12.0
        ''')

    def _getHighestTime(self):
        '''returns the largest offset plus duration.
      
        >>> n = note.Note('C#')
        >>> n.quarterLength = 3

        >>> q = Stream()
        >>> for i in [20, 0, 10, 30, 40]:
        ...    p = Stream()
        ...    p.repeatInsert(n, [0, 1, 2, 3, 4])
        ...    q.insert(i, p) # insert out of order
        >>> len(q.flat)
        25
        >>> q.highestTime # this works b/c the component Stream has an duration
        47.0
        >>> r = q.flat
        
        Make sure that the cache really is empty
        >>> r._cache['HighestTime']
        >>> r.highestTime # 44 + 3
        47.0
        '''
#         environLocal.printDebug(['_getHighestTime', 'isSorted', self.isSorted, self])
        if self._cache["HighestTime"] is not None:
            pass # return cache unaltered
        elif len(self._elements) == 0:
            self._cache["HighestTime"] = 0.0
            return 0.0
        elif self.isSorted is True:
            eLast = self._elements[-1]
            if hasattr(eLast, "duration") and hasattr(eLast.duration,
                    "quarterLength"):
                self._cache["HighestTime"] = (eLast.getOffsetBySite(self) + 
                    eLast.duration.quarterLength)
            else:
                self._cache["HighestTime"] = eLast.getOffsetBySite(self)
        else:
            max = None
            for e in self._elements:
                if hasattr(e, "duration") and hasattr(e.duration, 
                        "quarterLength"):
                    candidateOffset = (e.getOffsetBySite(self) + 
                                 e.duration.quarterLength)
                else:
                    candidateOffset = e.getOffsetBySite(self)
                if max is None or candidateOffset > max :
                    max = candidateOffset
            self._cache["HighestTime"] = max

        return self._cache["HighestTime"]

    
    highestTime = property(_getHighestTime, doc='''
        Returns the maximum of all Element offsets plus their Duration 
        in quarter lengths. This value usually represents the last 
        "release" in the Stream.

        Stream.duration is usually equal to the highestTime 
        expressed as a Duration object, but it can be set separately 
        for advanced operations.

        Example insert a dotted quarter at positions 0, 1, 2, 3, 4:

        >>> n = note.Note('A-')
        >>> n.quarterLength = 3
        >>> p1 = Stream()
        >>> p1.repeatInsert(n, [0, 1, 2, 3, 4])
        >>> p1.highestTime # 4 + 3
        7.0
        ''')

    
    def _getLowestOffset(self):
        '''
        >>> p = Stream()
        >>> p.repeatInsert(None, range(5))
        >>> q = Stream()
        >>> q.repeatInsert(p, range(0,50,10))
        >>> len(q.flat)        
        25
        >>> q.lowestOffset
        0.0
        >>> r = Stream()
        >>> r.repeatInsert(q, range(97, 500, 100))
        >>> len(r.flat)
        125
        >>> r.lowestOffset
        97.0
        '''
        if self._cache["LowestOffset"] is not None:
            pass # return cache unaltered
        elif len(self._elements) == 0:
            self._cache["LowestOffset"] = 0.0
        elif self.isSorted is True:
            eFirst = self._elements[0]
            self._cache["LowestOffset"] = eFirst.getOffsetBySite(self) 
        else: # iterate through all elements
            min = None
            for e in self._elements:
                candidateOffset = e.getOffsetBySite(self) 
                if min is None or candidateOffset < min:
                    min = candidateOffset
            self._cache["LowestOffset"] = min

            #environLocal.printDebug(['_getLowestOffset: iterated elements', min])

        return self._cache["LowestOffset"]


    lowestOffset = property(_getLowestOffset, doc='''
        Get the start time of the Element with the lowest offset in the Stream.        

        >>> stream1 = Stream()
        >>> for x in range(3,5):
        ...     n = note.Note('G#')
        ...     stream1.insert(x, n)
        ...
        >>> stream1.lowestOffset
        3.0
        
        If the Stream is empty, then the lowest offset is 0.0:
                
        >>> stream2 = Stream()
        >>> stream2.lowestOffset
        0.0

        ''')

    def _getDuration(self):
        '''
        Gets the duration of the ElementWrapper (if separately set), but
        normal returns the duration of the component object if available, otherwise
        returns None.

        '''

        if self._unlinkedDuration is not None:
            return self._unlinkedDuration
        elif self._cache["Duration"] is not None:
            return self._cache["Duration"]
        else:
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
        if (isinstance(durationObj, music21.duration.DurationCommon)):
            self._unlinkedDuration = durationObj
        elif (durationObj is None):
            self._unlinkedDuration = None
        else:
            # need to permit Duration object assignment here
            raise Exception, 'this must be a Duration object, not %s' % durationObj

    duration = property(_getDuration, _setDuration, doc='''
        Returns the total duration of the Stream, from the beginning of the stream until the end of the final element.
        May be set independently by supplying a Duration object.
    
        >>> a = Stream()
        >>> q = note.QuarterNote()
        >>> a.repeatInsert(q, [0,1,2,3])
        >>> a.highestOffset
        3.0
        >>> a.highestTime
        4.0
        >>> a.duration.quarterLength
        4.0
        
        >>> # Advanced usage: overriding the duration
        >>> newDuration = duration.Duration("half")
        >>> newDuration.quarterLength
        2.0
    
        >>> a.duration = newDuration
        >>> a.duration.quarterLength
        2.0
        >>> a.highestTime # unchanged
        4.0
        ''')



    #---------------------------------------------------------------------------
    # Metadata access

    def _getMetadata(self):
        '''
        >>> a = Stream()
        >>> a.metadata = metadata.Metadata()
        '''
        mdList = self.getElementsByClass(metadata.Metadata)
        # only return clefs that have offset = 0.0 
        mdList = mdList.getElementsByOffset(0)
        if len(mdList) == 0:
            return None
        else:
            return mdList[0]    
    
    def _setMetadata(self, metadataObj):
        '''
        >>> from music21 import *
        >>> a = stream.Stream()
        >>> a.metadata = metadata.Metadata()
        '''
        oldMetadata = self._getMetadata()
        if oldMetadata is not None:
            environLocal.printDebug(['removing old metadata', oldMetadata])
            junk = self.pop(self.index(oldMetadata))

        if metadataObj != None and isinstance(metadataObj, metadata.Metadata):
            self.insert(0, metadataObj)

    metadata = property(_getMetadata, _setMetadata, 
        doc = '''Get or set the :class:`~music21.metadata.Metadata` object found at offset zero for this Stream.

        >>> s = Stream()
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

    beatStr = property(_getBeatStr)
  
    def _getBeatDuration(self):
        # this returns the duration of the active beat
        return None

    beatDuration = property(_getBeatDuration)
  
    def _getBeatStrength(self):
        # this returns the accent weight of the active beat
        return None

    beatStrength = property(_getBeatStrength)


    #---------------------------------------------------------------------------
    # transformations

    def transpose(self, value, inPlace=False, 
        classFilterList=['Note', 'Chord']):
        '''Transpose all specified classes in the 
        Stream by the 
        user-provided value. If the value is an integer, the 
        transposition is treated in half steps. If the value is 
        a string, any Interval string specification can be 
        provided.

        returns a new Stream by default, but if the
        optional "inPlace" key is set to True then
        it modifies pitches in place.

        >>> aInterval = interval.Interval('d5')
        
        >>> from music21 import corpus
        >>> aStream = corpus.parseWork('bach/bwv324.xml')
        >>> part = aStream[0]
        >>> aStream[0].pitches[:10]
        [B4, D5, B4, B4, B4, B4, C5, B4, A4, A4]
        >>> bStream = aStream[0].flat.transpose('d5')
        >>> bStream.pitches[:10]
        [F5, A-5, F5, F5, F5, F5, G-5, F5, E-5, E-5]
        >>> aStream[0].pitches[:10]
        [B4, D5, B4, B4, B4, B4, C5, B4, A4, A4]
        >>> cStream = bStream.flat.transpose('a4')
        >>> cStream.pitches[:10]
        [B5, D6, B5, B5, B5, B5, C6, B5, A5, A5]
        
        >>> cStream.flat.transpose(aInterval, inPlace=True)
        >>> cStream.pitches[:10]
        [F6, A-6, F6, F6, F6, F6, G-6, F6, E-6, E-6]
        '''
        # only change the copy
        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self
#         for p in post.pitches: # includes chords
#             # do inplace transpositions on the deepcopy
#             p.transpose(value, inPlace=True)            

        for e in post.getElementsByClass(classFilterList=classFilterList): 
            e.transpose(value, inPlace=True)            


        if not inPlace:
            return post
        else:       
            return None


    def scaleOffsets(self, scalar, anchorZero='lowest', 
            anchorZeroRecurse=None, inPlace=True):
        '''Scale all offsets by a provided scalar. Durations are not altered. 

        To augment or diminish a Stream, see the :meth:`~music21.stream.Stream.augmentOrDiminish` method. 

        The `anchorZero` parameter determines if and/or where the zero offset is established for the set of offsets in this Stream before processing. Offsets are shifted to make either the lower or upper values the new zero; then offsets are scaled; then the shifts are removed. Accepted values are None (no offset shifting), "lowest", or "highest". 

        The `anchorZeroRecurse` parameter determines the anchorZero for all embedded Streams, and Streams embedded within those Streams. If the lowest offset in an embedded Stream is non-zero, setting this value to None will a the space between the start of that Stream and the first element to be scaled. If the lowest offset in an embedded Stream is non-zero, setting this value to 'lowest' will not alter the space between the start of that Stream and the first element to be scaled. 

        To shift all the elements in a Stream, see the :meth:`~music21.stream.Stream.shiftElements` method. 

        >>> from music21 import note
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> s = Stream()
        >>> s.repeatAppend(n, 20)
        '''

        # if we have offsets at 0, 2, 4
        # we scale by 2, getting offsets at 0, 4, 8

        # compare to offsets at 10, 12, 14
        # we scale by 2; if we do not anchor at lower, we get 20, 24, 28
        # if we anchor, we get 10, 14, 18

        if not scalar > 0:
            raise StreamException('scalar must be greater than zero')

        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        # first, get the offset shift requested
        if anchorZero in ['lowest']:
            offsetShift = returnObj.lowestOffset
        elif anchorZero in ['highest']:
            offsetShift = returnObj.highestOffset        
        elif anchorZero in [None]:
            offsetShift = 0
        else:
            raise StreamException('an achorZero value of %s is not accepted' % anchorZero)

        for e in returnObj._elements:

            # subtract the offset shift (and lowestOffset of 80 becomes 0)
            # then apply the scalar
            o = (e.getOffsetBySite(returnObj) - offsetShift) * scalar
            # after scaling, return the shift taken away
            o += offsetShift

            #environLocal.printDebug(['changng offset', o, scalar, offsetShift])

            e.setOffsetBySite(returnObj, o) # reassign
            # need to look for embedded Streams, and call this method
            # on them, with inPlace == True, as already copied if 
            # inPlace is != True
            if hasattr(e, "elements"): # recurse time:
                e.scaleOffsets(scalar, anchorZero=anchorZeroRecurse, anchorZeroRecurse=anchorZeroRecurse,
                inPlace=True)

        returnObj._elementsChanged() 
        return returnObj


    def scaleDurations(self, scalar, inPlace=True):
        '''Scale all durations by a provided scalar. Offsets are not modified.

        To augment or diminish a Stream, see the :meth:`~music21.stream.Stream.augmentOrDiminish` method. 

        '''
        if not scalar > 0:
            raise StreamException('scalar must be greater than zero')
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        for e in returnObj._elements:
            # check if its a Stream, first, as duration is dependent
            # and do not want to override
            if hasattr(e, "elements"): # recurse time:
                e.scaleDurations(scalar)
            elif hasattr(e, 'duration'):
                if e.duration != None:
                    # inPlace is True as a  copy has already been made if nec
                    e.duration.augmentOrDiminish(scalar, inPlace=True)

        returnObj._elementsChanged() 
        return returnObj


    def augmentOrDiminish(self, scalar, inPlace=False):
        '''Scale this Stream by a provided numerical scalar. A scalar of .5 is half the durations and relative offset positions; a scalar of 2 is twice the durations and relative offset positions.
    
        If `inPlace` is True, the alteration will be made to the calling object. Otherwise, a new Stream is returned. 


        >>> from music21 import *
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
        if not scalar > 0:
            raise StreamException('scalar must be greater than zero')
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        # inPlace is True as a copy has already been made if nec
        returnObj.scaleOffsets(scalar=scalar, anchorZero='lowest', 
            anchorZeroRecurse=None, inPlace=True)
        returnObj.scaleDurations(scalar=scalar, inPlace=True)
        returnObj._elementsChanged() 

        # do not need to call elements changed, as called in sub methods
        return returnObj


    def quantize(self, quarterLengthDivisors=[4, 3], 
            processOffsets=True, processDurations=False):
        '''Quantize time values in this Stream by snapping offsets and/or durations to the nearest multiple of a quarter length value given as one or more divisors of 1 quarter length. The quantized value found closest to a divisor multiple will be used.

        The `quarterLengthDivisors` provides a flexible way to provide quantization settings. For example, [2] will snap all events to eighth note grid. [4, 3] will snap events to sixteenth notes and eighth note triplets, whichever is closer. [4, 6] will snap events to sixteenth notes and sixteenth note triplets. 

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .49
        >>> s = stream.Stream()
        >>> s.repeatInsert(n, [0.1, .49, .9, 1.51])
        >>> s.quantize([4], processOffsets=True, processDurations=True)
        >>> [e.offset for e in s]
        [0.0, 0.5, 1.0, 1.5]
        >>> [e.duration.quarterLength for e in s]
        [0.5, 0.5, 0.5, 0.5]
        '''
        # this presently is not trying to avoid overlaps that
        # result from quantization; this may be necessary

        def bestMatch(target, divisors):
            found = []
            for div in divisors:
                match, error = common.nearestMultiple(target, (1.0/div))
                found.append((error, match)) # reverse for sorting
            # get first, and leave out the error
            return sorted(found)[0][1]

        # if we have a min of .25 (sixteenth)
        quarterLengthMin = quarterLengthDivisors[0]
        for e in self._elements:
            if processOffsets:
                o = e.getOffsetBySite(self)
                oNew = bestMatch(o, quarterLengthDivisors)
                #oNew = common.nearestMultiple(o, quarterLengthMin)
                e.setOffsetBySite(self, oNew)
            if processDurations:
                if e.duration != None:
                    ql = e.duration.quarterLength
                    qlNew = bestMatch(ql, quarterLengthDivisors)
                    #qlNew = common.nearestMultiple(ql, quarterLengthMin)
                    e.duration.quarterLength = qlNew

    #---------------------------------------------------------------------------
    # slicing and recasting a note as many notes

    def sliceByQuarterLengths(self, quarterLengthList, target=None, 
        addTies=True, inPlace=False):
        '''Slice all :class:`~music21.duration.Duration` objects on all Notes of this Stream. Duration are sliced according to values provided in `quarterLengthList` list. If the sum of these values is less than the Duration, the values are accumulated in a loop to try to fill the Duration. If a match cannot be found, an Exception is raised. 

        If `target` == None, the entire Stream is processed. Otherwise, only the element specified is manipulated. 
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass('Measure'):
                m.sliceByQuarterLengths(quarterLengthList, 
                    target=target, addTies=addTies, inPlace=True)
            return returnObj # exit

        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Part'):
                p.sliceByQuarterLengths(quarterLengthList, 
                    target=target, addTies=addTies, inPlace=True)
            return returnObj # exit
    
        if not common.isListLike(quarterLengthList):
            quarterLengthList = [quarterLengthList]

        if target != None:
            # get the element out of rutern obj
            # need to use self.index to get index value
            eToProcess = [returnObj.elements[self.index(target)]]
        else: # get elements list from Stream
            eToProcess = returnObj.notes.elements 
        
        for e in eToProcess:
            # if qlList values are greater than the found duration, skip
            if sum(quarterLengthList) > e.quarterLength:
                continue
            elif not common.almostEquals(sum(quarterLengthList),
                e.quarterLength, grain=1e-4):
                # try to map a list that is of sufficient duration
                qlProcess = []
                i = 0
                while True:
                    qlProcess.append(
                        quarterLengthList[i%len(quarterLengthList)])
                    i += 1
                    sumQL = sum(qlProcess)
                    if (common.almostEquals(sumQL, e.quarterLength) or 
                    sumQL >= e.quarterLength):
                        break
            else:
                qlProcess = quarterLengthList

            #environLocal.printDebug(['got qlProcess', qlProcess, 'for element', e, e.quarterLength])

            if not common.almostEquals(sum(qlProcess), e.quarterLength):
                raise StreamException('cannot map quarterLength list into element Duration: %s, %s' % (sum(qlProcess), e.quarterLength))
    
            post = e.splitByQuarterLengths(qlProcess, addTies=addTies)
            # remove e from the source
            oInsert = e.getOffsetBySite(returnObj)
            returnObj.remove(e)
            for eNew in post:
                returnObj.insert(oInsert, eNew)
                oInsert += eNew.quarterLength

        return returnObj


    def sliceByGreatestDivisor(self, addTies=True, inPlace=False):
        '''Slice all :class:`~music21.duration.Duration` objects on all Notes of this Stream. Duration are sliced according to the approximate GCD found in all durations. 
        '''
        # when operating on a Stream, this should take all durations found and use the approximateGCD to get a min duration; then, call sliceByQuarterLengths

        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass('Measure'):
                m.sliceByGreatestDivisor(addTies=addTies, inPlace=True)
            return returnObj # exit
    
        uniqueQuarterLengths = []
        for e in returnObj.notes:
            if e.quarterLength not in uniqueQuarterLengths:
                uniqueQuarterLengths.append(e.quarterLength)

        #environLocal.printDebug(['unique quarter lengths', uniqueQuarterLengths])

        # will raise an exception if no gcd can be found
        divisor = common.approximateGCD(uniqueQuarterLengths)

        # process in place b/c a copy, if necessary, has already been made                            
        returnObj.sliceByQuarterLengths(quarterLengthList=[divisor],
            target=None, addTies=addTies, inPlace=True)

        return returnObj


    def sliceAtOffsets(self, offsetList, target=None, 
        addTies=True, inPlace=False, displayTiedAccidentals=False):
        '''Given a list of quarter lengths, slice and optionally tie all Durations at these points. 

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 4
        >>> s.append(n)
        >>> post = s.sliceAtOffsets([1, 2, 3], inPlace=True)
        >>> [(e.offset, e.quarterLength) for e in s]
        [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0)]
        '''
        if not inPlace: # make a copy
            returnObj = copy.deepcopy(self)
        else:
            returnObj = self

        if returnObj.hasMeasures():
            # call on component measures
            for m in returnObj.getElementsByClass('Measure'):
                # offset values are not relative to measure; need to
                # shift by each measure's offset
                offsetListLocal = [o - m.getOffsetBySite(self) for o in offsetList]
                m.sliceAtOffsets(offsetList=offsetListLocal, 
                    addTies=addTies, inPlace=True, 
                    displayTiedAccidentals=displayTiedAccidentals)
            return returnObj # exit
    
        if returnObj.hasPartLikeStreams():
            for p in returnObj.getElementsByClass('Part'):
                offsetListLocal = [o - p.getOffsetBySite(self) for o in offsetList]
                p.sliceAtOffsets(offsetList=offsetListLocal, 
                    addTies=addTies, inPlace=True, 
                    displayTiedAccidentals=displayTiedAccidentals)
            return returnObj # exit


        # list of start, start+dur, element, all in abs offset time
        offsetMap = self._getOffsetMap(returnObj)
        
        for ob in offsetMap:
            # if target is defined, only modify that object
            oStart, oEnd, e, voiceCount = ob['offset'], ob['endTime'], ob['element'], ob['voiceIndex']
            if target != None and id(e) != id(target):
                continue

            cutPoints = []
            for o in offsetList:
                if o > oStart and o < oEnd:
                    cutPoints.append(o)
            #environLocal.printDebug(['cutPoints', cutPoints, 'oStart', oStart, 'oEnd', oEnd])
            if len(cutPoints) > 0:
                # remove old 
                #eProc = returnObj.remove(e)        
                eNext = e
                oStartNext = oStart
                for o in cutPoints:
                    oCut = o - oStartNext
                    # set the second part of the remainder to e, so that it
                    # will be processed with next cut point
                    eComplete, eNext = eNext.splitAtQuarterLength(oCut,
                        retainOrigin=True, addTies=addTies,
                        displayTiedAccidentals=displayTiedAccidentals)                
                    # only need to insert eNext, as eComplete was modified
                    # in place due to retainOrigin option 
                    # insert at o, not oCut (duration into element)
                    returnObj.insert(o, eNext)
                    oStartNext = o
        return returnObj


    def sliceByBeat(self, target=None, 
        addTies=True, inPlace=False, displayTiedAccidentals=False):
        '''Slice all elements in the Stream that have a Duration at the offsets determined to be the beat from the local TimeSignature. 
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
    def hasMeasures(self):
        '''Return a boolean value showing if this Stream contains Measures
        '''
        post = False
        for obj in self:
            # if obj is a Part, we have multi-parts
            if 'Measure' in obj.classes:
                post = True
                break # only need one
        return post


    def hasVoices(self):
        '''Return a boolean value showing if this Stream contains Voices
        '''
        post = False
        for obj in self:
            # if obj is a Part, we have multi-parts
            if 'Voice' in obj.classes:
                post = True
                break # only need one
        return post


    def hasPartLikeStreams(self):
        '''Return a boolean value showing if this Stream contains multiple Parts, or Part-like sub-Streams. 
        '''
        multiPart = False
        for obj in self:
            # if obj is a Part, we have multi-parts
            if isinstance(obj, Part):
                multiPart = True
                break # only need one
            # if components are Measures, self is a part
            elif isinstance(obj, Measure):
                multiPart = False
                break # only need one
            # if voices are present not multipart
            elif isinstance(obj, Voice):
                multiPart = False
                break
            # if components are streams of Notes or Measures, 
            # than assume this is like a Part
            elif 'Stream' in obj.classes and (
                len(obj.getElementsByClass('Measure')) > 0 or len(obj.notes) > 0):
                multiPart = True
                break # only need one
        return multiPart



    def _getLily(self):
        '''Returns the stream translated into Lilypond format.'''
        if self._overriddenLily is not None:
            return self._overriddenLily
        #elif self._cache["lily"] is not None:
        #    return self._cache["lily"]
        # TODO: RESTORE CACHE WHEN Changes bubble up 
        
        lilyout = u"\n  { "
#        if self.showTimeSignature is not False and self.timeSignature is not None:
#            lilyout += self.timeSignature.lily
    
        for thisObject in self.elements:
            if hasattr(thisObject, "startTransparency") and thisObject.startTransparency is True:
                lilyout += lilyModule.TRANSPARENCY_START

            if hasattr(thisObject.duration, "tuplets") and thisObject.duration.tuplets:
                if thisObject.duration.tuplets[0].type == "start":
                    numerator = str(int(thisObject.duration.tuplets[0].tupletNormal[0]))
                    denominator = str(int(thisObject.duration.tuplets[0].tupletActual[0]))
                    lilyout += "\\times " + numerator + "/" + denominator + " {"
                    ### TODO-- should get the actual ratio not assume that the
                    ### type of top and bottom are the same
            if hasattr(thisObject, "lily"):
                lilyout += unicode(thisObject.lily)
                lilyout += " "
            else:
                pass
            
            if hasattr(thisObject.duration, "tuplets") and thisObject.duration.tuplets:
                if thisObject.duration.tuplets[0].type == "stop":
                    lilyout = lilyout.rstrip()
                    lilyout += "} "

            if hasattr(thisObject, "stopTransparency") and thisObject.stopTransparency is True:
                lilyout += lilyModule.TRANSPARENCY_STOP
        
        lilyout += " } "
        lilyObj = lilyModule.LilyString(lilyout)
#        self._cache["lily"] = lilyObj
        return lilyObj

    def _setLily(self, value):
        '''Sets the Lilypond output for the stream. Overrides what is obtained
        from get_lily.'''
        self._overriddenLily = value
        self._cache["lily"] = None

    lily = property(_getLily, _setLily, doc = r'''
        returns or sets the lilypond output for the Stream.
        Note that (for now at least), setting the Lilypond output for a Stream does not
        change the stream itself.  It's just a way of overriding what is printed when .lily
        is called.
        
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.append(clef.BassClef())
        >>> s1.append(meter.TimeSignature("3/4"))
        >>> k1 = key.KeySignature(5)
        >>> k1.mode = 'minor'
        >>> s1.append(k1)
        >>> s1.append(note.Note("B-3"))   # quarter note
        >>> s1.append(note.HalfNote("C#2"))
        >>> s1.lily
         { \clef "bass"  \time 3/4  \key gis \minor bes4 cis,2  } 
    
    ''')



    #---------------------------------------------------------------------------

    def _getMidiTracksPart(self, instObj=None):
        '''Returns a :class:`music21.midi.base.MidiTrack` object based on the content of this Stream.
        '''
        return midiTranslate.streamToMidiTrack(self, instObj)

    def _setMidiTracksPart(self, mt, ticksPerQuarter=None, quantizePost=True):
        environLocal.printDebug(['got midi track: events', len(mt.events), 'ticksPerQuarter', ticksPerQuarter])
        '''Given a MIDI track, configure a Stream.
        '''
        # pass self as reference to configure this object
        midiTranslate.midiTrackToStream(mt, ticksPerQuarter, quantizePost, self)

    def _getMidiTracks(self):
        return midiTranslate.streamsToMidiTracks(self)

    def _setMidiTracks(self, midiTracks, ticksPerQuarter=None):
        midiTranslate.midiTracksToStreams(midiTracks, 
            ticksPerQuarter=ticksPerQuarter, inputM21=self)


    midiTracks = property(_getMidiTracks, _setMidiTracks, 
        doc='''Get or set this Stream from a list of :class:`music21.midi.base.MidiTracks` objects.

        >>> from music21 import *
        >>> s = stream.Stream()
        >>> n = note.Note('g#3')
        >>> n.quarterLength = .5
        >>> s.repeatAppend(n, 6)
        >>> len(s.midiTracks[0].events)
        28
        ''')

    def _getMidiFile(self):
        '''Return a complete :class:`music21.midi.base.MidiFile` object based on the Stream.

        The :class:`music21.midi.base.MidiFile` object can be used to write a MIDI file of this Stream with default parameters using the :meth:`music21.midi.base.MidiFile.write` method, given a file path. The file must be opened in 'wb' mode.  

        >>> from music21 import *
        >>> sc = scale.PhrygianScale('g')
        >>> s = stream.Stream()
        >>> x=[s.append(note.Note(sc.pitchFromDegree(i%11),quarterLength=.25)) for i in range(60)]
        >>> mf = s.midiFile
        >>> #_DOCS_SHOW mf.open('/Volumes/xdisc/_scratch/midi.mid', 'wb')
        >>> #_DOCS_SHOW mf.write()
        >>> #_DOCS_SHOW mf.close()

        '''
        return midiTranslate.streamToMidiFile(self)

    def _setMidiFile(self, mf):
        '''Given a :class:`music21.midi.base.MidiFile` object, configure a Stream
        '''
        return midiTranslate.midiFileToStream(mf, inputM21=self)

    midiFile = property(_getMidiFile, _setMidiFile,
        doc = '''Get or set a :class:`music21.midi.base.MidiFile` object.
        ''')



    #---------------------------------------------------------------------------
    def _getMXPart(self, instObj=None, meterStream=None, 
        refStreamOrTimeRange=None):
        '''If there are Measures within this stream, use them to create and
        return an MX Part and ScorePart. 

        An `instObj` may be assigned from caller; this Instrument is pre-collected from this Stream in order to configure id and midi-channel values. 

        meterStream can be provided to provide a template within which
        these events are positioned; this is necessary for handling
        cases where one part is shorter than another. 
        '''
        #environLocal.printDebug(['calling Stream._getMXPart'])
        # note: meterStream may have TimeSignature objects from an unrelated
        # Stream.

        # pass self as Stream to use
        return musicxmlTranslate.streamPartToMx(self, instObj=instObj,
            meterStream=meterStream, refStreamOrTimeRange=refStreamOrTimeRange)


    def _getMX(self):
        '''Create and return a musicxml Score object. 

        >>> n1 = note.Note()
        >>> measure1 = Measure()
        >>> measure1.insert(n1)
        >>> str1 = Stream()
        >>> str1.insert(measure1)
        >>> mxScore = str1.mx
        '''
        #environLocal.printDebug('calling Stream._getMX')
        # returns an mxScore object
        return musicxmlTranslate.streamToMx(self)

    def _setMXPart(self, mxScore, partId):
        '''Load a part given an mxScore and a part name.
        '''
        #environLocal.printDebug(['calling Stream._setMXPart'])
        # pass reference to self for building into
        musicxmlTranslate.mxToStreamPart(mxScore, partId, inputM21=self)

    def _setMX(self, mxScore):
        '''Given an mxScore, build into this stream
        '''
        musicxmlTranslate.mxToStream(mxScore, inputM21=self)
    
    mx = property(_getMX, _setMX)
        
    def _getMusicXML(self):
        '''Provide a complete MusicXML representation. 
        '''
        mxScore = self._getMX()
        return mxScore.xmlStr()

    musicxml = property(_getMusicXML,
        doc = '''Return a complete MusicXML reprsentatoin as a string. 
        ''')


    def _getNotes(self):
        '''
        see property `notes`, below
        '''
        #return self.getElementsByClass([note.GeneralNote, chord.Chord])
        # using string class names is import for some test contexts where
        # absolute class name matching fails
        return self.getElementsByClass(['GeneralNote', 'Chord'])

    notes = property(_getNotes, doc='''
        The notes property of a Stream returns a new Stream object
        that consists only of the notes (including 
        :class:`~music21.note.Note`, 
        :class:`~music21.chord.Chord`, 
        :class:`~music21.note.Rest`, etc.) found 
        in the stream.

        >>> from music21 import *
        >>> s1 = Stream()
        >>> k1 = key.KeySignature(0) # key of C
        >>> n1 = note.Note('B')
        >>> c1 = chord.Chord(['A', 'B-'])
        >>> s1.append([k1, n1, c1])
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of no sharps or flats>
        {0.0} <music21.note.Note B>
        {1.0} <music21.chord.Chord A B->

        >>> notes1 = s1.notes
        >>> notes1.show('text')
        {0.0} <music21.note.Note B>
        {1.0} <music21.chord.Chord A B->       
        ''')

    def _getPitches(self):
        '''
        documented as part of property `pitches`, below.
        '''  
        post = []
        for e in self.elements:
            # case of a Note or note-like object
            if hasattr(e, "pitch"):
                post.append(e.pitch)
            # both Chords and Stream have a pitches properties            
            elif hasattr(e, "pitches"):
                for thisPitch in e.pitches:
                    post.append(thisPitch)
            # do an ininstance comparison
            elif isinstance(e, music21.pitch.Pitch):
                post.append(e)
        return post
    
    pitches = property(_getPitches, doc='''
        Return all :class:`~music21.pitch.Pitch` objects found in any 
        element in the Stream as a Python List. Elements such as 
        Streams, and Chords will have their Pitch objects accumulated as 
        well. For that reason, a flat representation may not be required. 

        Pitch objects are returned in a List, not a Stream.  This usage
        differs from the notes property, but makes sense since Pitch
        objects are usually durationless.  (That's the main difference
        between them and notes)

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> voiceOnePitches = a[0].pitches
        >>> len(voiceOnePitches)
        25
        >>> voiceOnePitches[0:10]
        [B4, D5, B4, B4, B4, B4, C5, B4, A4, A4]
        
        Note that the pitches returned above are 
        objects, not text:
        
        >>> voiceOnePitches[0].octave
        4
        
        Since pitches are found from internal objects,
        flattening the stream is not required:
        
        >>> len(a.pitches)
        104

        Pitch objects are also retrieved when stored directly on a Stream.

        >>> from music21 import pitch
        >>> pitch1 = pitch.Pitch()
        >>> st1 = Stream()
        >>> st1.append(pitch1)
        >>> foundPitches = st1.pitches
        >>> len(foundPitches)
        1
        >>> foundPitches[0] is pitch1
        True
        ''')


    def pitchAttributeCount(self, pitchAttr='name'):
        '''Return a dictionary of pitch class usage (count) by selecting an attribute of the Pitch object. 

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> a.pitchAttributeCount('pitchClass')
        {0: 3, 2: 25, 3: 3, 4: 14, 6: 15, 7: 13, 9: 17, 11: 14}
        >>> a.pitchAttributeCount('name')
        {u'A': 17, u'C': 3, u'B': 14, u'E': 14, u'D': 25, u'G': 13, u'D#': 3, u'F#': 15}
        >>> a.pitchAttributeCount('nameWithOctave')
        {u'E3': 4, u'G4': 2, u'F#4': 2, u'A2': 2, u'E2': 1, u'G2': 1, u'D3': 9, u'D#3': 1, u'B4': 7, u'A3': 5, u'F#3': 13, u'A4': 10, u'B2': 3, u'B3': 4, u'C3': 2, u'E4': 9, u'D4': 14, u'D5': 2, u'D#4': 2, u'C5': 1, u'G3': 10}
        '''
        post = {}
        for p in self.pitches:
            key = getattr(p, pitchAttr)
            if key not in post.keys():
                post[key] = 0
            post[key] += 1
        return post


    def attributeCount(self, classFilterList, attrName='quarterLength'):
        '''Return a dictionary of attribute usage for one or more classes provided in a the `classFilterList` list and having the attribute specified by `attrName`.

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> a[0].flat.attributeCount(note.Note, 'quarterLength')
        {1.0: 12, 2.0: 11, 4.0: 2}
        '''
        post = {}
        for e in self.getElementsByClass(classFilterList):
            if hasattr(e, attrName):
                key = getattr(e, attrName)
                if key not in post.keys():
                    post[key] = 0
                post[key] += 1
        return post


    #---------------------------------------------------------------------------
    # interval routines
    
    def findConsecutiveNotes(self, skipRests = False, skipChords = False, 
        skipUnisons = False, skipOctaves = False,
        skipGaps = False, getOverlaps = False, noNone = False, **keywords):
        '''
        Returns a list of consecutive *pitched* Notes in a Stream.  A single "None" is placed in the list 
        at any point there is a discontinuity (such as if there is a rest between two pitches).
        
        
        How to determine consecutive pitches is a little tricky and there are many options.  

        skipUnison uses the midi-note value (.ps) to determine unisons, so enharmonic transitions (F# -> Gb) are
        also skipped if skipUnisons is true.  We believe that this is the most common usage.  However, because
        of this, you cannot completely be sure that the x.findConsecutiveNotes() - x.findConsecutiveNotes(skipUnisons = True)
        will give you the number of P1s in the piece, because there could be d2's in there as well.
                
        See Test.testFindConsecutiveNotes() for usage details.
        
        
        OMIT_FROM_DOCS

        N.B. for chords, currently, only the first pitch is tested for unison.  this is a bug TODO: FIX

        (**keywords is there so that other methods that pass along dicts to findConsecutiveNotes don't have to remove 
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
            else:
                vGroups.append(sortedSelf)

        for v in vGroups:
            for e in v._elements:
                if (lastWasNone is False and skipGaps is False and 
                    e.offset > lastEnd):
                    if not noNone:
                        returnList.append(None)
                        lastWasNone = True
                if hasattr(e, "pitch"):
                    if (skipUnisons is False or isinstance(lastPitch, list) or
                        lastPitch is None or 
                        e.pitch.pitchClass != lastPitch.pitchClass or 
                        (skipOctaves is False and e.pitch.ps != lastPitch.ps)):
                        if getOverlaps is True or e.offset >= lastEnd:
                            if e.offset >= lastEnd:  # is not an overlap...
                                lastStart = e.offset
                                if hasattr(e, "duration"):
                                    lastEnd = lastStart + e.duration.quarterLength
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
                                        lastEnd = lastStart + e.duration.quarterLength
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
                    lastEnd = e.offset + e.duration.quarterLength
        
        if lastWasNone is True:
            returnList.pop() # removes the last-added element
        return returnList
    
    def melodicIntervals(self, *skipArgs, **skipKeywords):
        '''Returns a Stream of :class:`~music21.interval.Interval` objects
        between Notes (and by default, Chords) that follow each other in a stream.
        the offset of the Interval is the offset of the beginning of the interval 
        (if two notes are adjacent, then this offset is equal to the offset of 
        the second note)
        
        See Stream.findConsecutiveNotes for a discussion of what consecutive notes 
        mean, and which keywords are allowed.
        
        The interval between a Note and a Chord (or between two chords) is the 
        interval between pitches[0]. For more complex interval calculations, 
        run findConsecutiveNotes and then use notesToInterval.
                
        Returns None of there are not at least two elements found by 
        findConsecutiveNotes.

        See Test.testMelodicIntervals() for usage details.

        '''
        returnList = self.findConsecutiveNotes(**skipKeywords)
        if len(returnList) < 2:
            return None
        
        returnStream = self.__class__()
        for i in range(len(returnList) - 1):
            firstNote = returnList[i]
            secondNote = returnList[i+1]
            firstPitch = None
            secondPitch = None
            if firstNote is not None and secondNote is not None:
                if hasattr(firstNote, "pitch") and firstNote.pitch is not None:
                    firstPitch = firstNote.pitch
                elif hasattr(firstNote, "pitches") and len(firstNote.pitches) > 0:
                    firstPitch = firstNote.pitches[0]
                if hasattr(secondNote, "pitch") and secondNote.pitch is not None:
                    secondPitch = secondNote.pitch
                elif hasattr(secondNote, "pitches") and len(secondNote.pitches) > 0:
                    secondPitch = secondNote.pitches[0]
                if firstPitch is not None and secondPitch is not None:
                    returnInterval = interval.notesToInterval(firstPitch, 
                                     secondPitch)
                    returnInterval.offset = (firstNote.offset + 
                                     firstNote.duration.quarterLength)
                    returnInterval.duration = duration.Duration(
                        secondNote.offset - returnInterval.offset)
                    returnStream.insert(returnInterval)

        return returnStream

    #---------------------------------------------------------------------------
    def _getDurSpan(self, flatStream):
        '''Given a flat stream, create a list of the start and end 
        times (as a tuple pair) of all elements in the Stream.

        >>> a = Stream()
        >>> a.repeatInsert(note.HalfNote(), range(5))
        >>> a._getDurSpan(a.flat)
        [(0.0, 2.0), (1.0, 3.0), (2.0, 4.0), (3.0, 5.0), (4.0, 6.0)]
        '''
        post = []        
        for e in flatStream:
            if e.duration == None:
                durSpan = (e.offset, e.offset)
            else:
                dur = e.duration.quarterLength
                durSpan = (e.offset, e.offset+dur)
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

        >>> a = Stream()
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
            if durSpans[1][0] <= durSpans[0][1]:   
                found = True
        else: # do not include coincident boundaries
            if durSpans[1][0] < durSpans[0][1]:   
                found = True
        return found


    def _findLayering(self, flatStream, includeDurationless=True,
                   includeEndBoundary=False):
        '''Find any elements in an elementsSorted list that have simultaneities 
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
        overlapMap = [[] for i in range(len(durSpanSorted))]
        # create a list of keys for events that start at the same time
        simultaneityMap = [[] for i in range(len(durSpanSorted))]
        
        for i in range(len(durSpanSorted)):
            src = durSpanSorted[i]
            # second entry is duration
            if not includeDurationless and flatStream[i].duration == None: 
                continue
            # compare to all past and following durations
            for j in range(len(durSpanSorted)):
                if j == i: # index numbers
                    continue # do not compare to self
                dst = durSpanSorted[j]
                # print src, dst, self._durSpanOverlap(src, dst, includeEndBoundary)
        
                if src[0] == dst[0]: # if start times are the same
                    simultaneityMap[i].append(j)
        
                if self._durSpanOverlap(src, dst, includeEndBoundary):
                    overlapMap[i].append(j)
        
        return simultaneityMap, overlapMap



    def _consolidateLayering(self, flatStream, map):
        '''
        Given elementsSorted and a map of equal length with lists of 
        index values that meet a given condition (overlap or simultaneities),
        organize into a dictionary by the relevant or first offset
        '''
        flatStream = flatStream.sorted

        if len(map) != len(flatStream):
            raise StreamException('map must be the same length as flatStream')

        post = {}
        for i in range(len(map)):
            # print 'examining i:', i
            indices = map[i]
            if len(indices) > 0: 
                srcOffset = flatStream[i].offset
                srcElementObj = flatStream[i]
                dstOffset = None
                # print 'found indices', indices
                # check indices
                for j in indices: # indices of other elements tt overlap
                    elementObj = flatStream[j]

                    # check if this object has been stored anywhere yet
                    # if so, use the offset of where it was stored to 
                    # to store the src element below
                    store = True
                    for key in post.keys():
                        # this comparison needs to be based on object id, not
                        # matching equality
                        if id(elementObj) in [id(e) for e in post[key]]:
                        # if elementObj in post[key]:
                            store = False
                            dstOffset = key
                            break
                    if dstOffset is None:
                        dstOffset = srcOffset
                    if store:
                        # print 'storing offset', dstOffset
                        if dstOffset not in post.keys():
                            post[dstOffset] = [] # create dictionary entry
                        post[dstOffset].append(elementObj)

                # check if this object has been stored anywhere yet
                store = True
                for key in post.keys():
                    if id(srcElementObj) in [id(e) for e in post[key]]:
                    #if srcElementObj in post[key]:
                        store = False
                        break
                # dst offset may have been set when looking at indices
                if store:
                    if dstOffset is None:
                        dstOffset = srcOffset
                    if dstOffset not in post.keys():
                        post[dstOffset] = [] # create dictionary entry
                    # print 'storing offset', dstOffset
                    post[dstOffset].append(srcElementObj)
                    # print post
        return post



    def findGaps(self, minimumQuarterLength=.001):
        '''Returns either (1) a Stream containing Elements (that wrap the None object) whose offsets and durations are the length of gaps in the Stream
        or (2) None if there are no gaps.
        
        N.B. there may be gaps in the flattened representation of the stream
        but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless
        '''
        if self._cache["GapStream"]:
            return self._cache["GapStream"]
        
        sortedElements = self.sorted.elements
        gapStream = self.__class__()
        highestCurrentEndTime = 0
        for e in sortedElements:

            if e.offset > highestCurrentEndTime:
                gapElement = music21.ElementWrapper(obj = None)
                gapQuarterLength = e.offset - highestCurrentEndTime
                if gapQuarterLength <= minimumQuarterLength:
                    #environLocal.printDebug(['findGaps(): skipping very small gap:', gapQuarterLength])
                    continue
                gapElement.duration = duration.Duration()
                gapElement.duration.quarterLength = gapQuarterLength
                gapStream.insert(highestCurrentEndTime, gapElement)
            if hasattr(e, 'duration') and e.duration != None:
                eDur = e.duration.quarterLength
            else:
                eDur = 0.
            highestCurrentEndTime = max(highestCurrentEndTime, e.offset + eDur)

        if len(gapStream) == 0:
            return None
        else:
            self._cache["GapStream"] = gapStream
            return gapStream

    def _getIsGapless(self):
        if self._cache["isGapless"] is not None:
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
        >>> stream1 = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 0
        ...     stream1.insert(n)
        ...
        >>> b = stream1.getSimultaneous()
        >>> len(b[0]) == 4
        True
        >>> stream2 = Stream()
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
        elementsSorted = self.flat.sorted
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                                    includeDurationless)
        
        return self._consolidateLayering(elementsSorted, simultaneityMap)


    def getOverlaps(self, includeDurationless=True,
                     includeEndBoundary=False):
        '''
        Find any elements that overlap. Overlaping might include elements
        that have no duration but that are simultaneous. 
        Whether elements with None durations are included is determined by includeDurationless.
                
        This method returns a dictionary, where keys are the start time of the first overlap and value are a list of all objects included in that overlap group. 

        This example demonstrates end-joing overlaps: there are four quarter notes each following each other. Whether or not these count as overlaps
        is determined by the includeEndBoundary parameter. 

        >>> a = Stream()
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
        >>> a = Stream()
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
        >>> a = Stream()
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
        checkSimultaneity = False
        checkOverlap = True
        elementsSorted = self.flat.sorted
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                includeDurationless, includeEndBoundary)
        #environLocal.printDebug(['simultaneityMap map', simultaneityMap])
        #environLocal.printDebug(['overlapMap', overlapMap])

        return self._consolidateLayering(elementsSorted, overlapMap)



    def isSequence(self, includeDurationless=True, 
                        includeEndBoundary=False):
        '''A stream is a sequence if it has no overlaps.

        >>> from music21 import *
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
        elementsSorted = self.flat.sorted
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                includeDurationless, includeEndBoundary)
        post = True
        for indexList in overlapMap:
            if len(indexList) > 0:
                post = False
                break       
        return post


    #---------------------------------------------------------------------------
    # routines for dealing with relationships to other streams.  
    # Formerly in twoStreams.py

    def simultaneousAttacks(self, stream2):
        '''
        returns an ordered list of offsets where elements are started (attacked) in both
        stream1 and stream2.
    
        >>> st1 = Stream()
        >>> st2 = Stream()
        >>> n11 = note.Note()
        >>> n12 = note.Note()
        >>> n21 = note.Note()
        >>> n22 = note.Note()
        
        >>> st1.insert(10, n11)
        >>> st2.insert(10, n21)
        
        >>> st1.insert(20, n12)
        >>> st2.insert(20.5, n22)
        
        >>> simultaneous = st1.simultaneousAttacks(st2)
        >>> simultaneous
        [10.0]
        '''
        stream1Offsets = self.groupElementsByOffset()
        stream2Offsets = stream2.groupElementsByOffset()
        
        returnKey = {}
        
        for thisList in stream1Offsets:
            thisOffset = thisList[0].getOffsetBySite(self)
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
        '''For each element in self, creates an interval.Interval object in the element's
        editorial that is the interval between it and the element in cmpStream that
        is sounding at the moment the element in srcStream is attacked.
        
        remember if comparing two streams with measures, etc., to run:
        
            stream1.flat.attachIntervvalsBetweenStreams(stream2.flat)
            
        example usage:
    
        >>> from music21 import *
        >>> s1 = converter.parse('C4 d8 e f# g A2', '5/4')
        >>> s2 = converter.parse('g4 e8 d c4   a2', '5/4')
        >>> s1.attachIntervalsBetweenStreams(s2)
        >>> for n in s1.notes:
        ...     if "Rest" in n.classes: continue  # safety check
        ...     if n.editorial.harmonicInterval is None: continue # if other voice had a rest...
        ...     print n.editorial.harmonicInterval.directedName
        P12
        M2
        M-2
        A-4
        P-5
        P8
        
        '''
    
        srcNotes = self.notes
        for thisNote in srcNotes:
            if thisNote.isRest is True:
                continue
            simultEls = cmpStream.getElementsByOffset(thisNote.offset, mustBeginInSpan = False, mustFinishInSpan = False)
            if len(simultEls) > 0:
                for simultNote in simultEls.notes:
                    if simultNote.isRest is False:
                        interval1 = interval.notesToInterval(thisNote, simultNote)
                        thisNote.editorial.harmonicInterval = interval1
                        break

    def playingWhenAttacked(self, el, elStream = None):
        '''Given an element (from another Stream) returns the single element in this Stream that is sounding while the given element starts. 
        
        If there are multiple elements sounding at the moment it is attacked, the method
        returns the first element of the same class as this element, if any. If no element
        is of the same class, then the first element encountered is returned.  
        For more complex usages, use allPlayingWhileSounding.
    
        Returns None if no elements fit the bill.
    
        The optional elStream is the stream in which el is found. If provided, el's offset
        in that Stream is used.  Otherwise, the current offset in el is used.  It is just
        in case you are paranoid that el.offset might not be what you want.
        
        >>> n1 = note.Note("G#")
        >>> n2 = note.Note("D#")
        >>> s1 = Stream()
        >>> s1.insert(20.0, n1)
        >>> s1.insert(21.0, n2)
        
        >>> n3 = note.Note("C#")
        >>> s2 = Stream()
        >>> s2.insert(20.0, n3)
        
        >>> s1.playingWhenAttacked(n3).name
        'G#'
        >>> n3._definedContexts.setOffsetBySite(s2, 20.5)
        >>> s1.playingWhenAttacked(n3).name
        'G#'
        >>> n3._definedContexts.setOffsetBySite(s2, 21.0)
        >>> n3.offset
        21.0
        >>> s1.playingWhenAttacked(n3).name
        'D#'

        # optionally, specify the site to get the offset from
        >>> n3._definedContexts.setOffsetBySite(None, 100)
        >>> n3.activeSite = None
        >>> s1.playingWhenAttacked(n3)
        <BLANKLINE>
        >>> s1.playingWhenAttacked(n3, s2).name
        'D#'
        
        OMIT_FROM_DOCS
        perhaps the idea of 'playing' should be recast as 'sustain' or 'sounding' or some other term?

        '''
    
        if elStream is not None: # bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset
        
        otherElements = self.getElementsByOffset(elOffset, mustBeginInSpan = False)
        if len(otherElements) == 0:
            return None
        elif len(otherElements) == 1:
            return otherElements[0]
        else:
            for thisEl in otherElements:
                if isinstance(thisEl, el.__class__):
                    return thisEl
            return otherElements[0]

    def allPlayingWhileSounding(self, el, elStream = None, 
                                requireClass = False):
        '''Returns a new Stream of elements in this stream that sound at the same time as `el`, an element presumably in another Stream.
        
        The offset of this new Stream is set to el's offset, while the offset of elements within the 
        Stream are adjusted relative to their position with respect to the start of el.  Thus, a note 
        that is sounding already when el begins would have a negative offset.  The duration of otherStream is forced
        to be the length of el -- thus a note sustained after el ends may have a release time beyond
        that of the duration of the Stream.
    
        as above, elStream is an optional Stream to look up el's offset in.
        

        OMIT_FROM_DOCS
        TODO: write: requireClass:
        Takes as an optional parameter "requireClass".  If this parameter is boolean True then only elements 
        of the same class as el are added to the new Stream.  If requireClass is list, it is used like 
        classList in elsewhere in stream to provide a list of classes that the el must be a part of.
        
        The method always returns a Stream, but it might be an empty Stream.
        '''
        if requireClass is not False:
            raise Exception("requireClass is not implemented")
    
        if elStream is not None: # bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset
        
        otherElements = self.getElementsByOffset(elOffset, elOffset + el.quarterLength, mustBeginInSpan = False)
    
        otherElements.offset = elOffset
        otherElements.quarterLength = el.quarterLength
        for thisEl in otherElements:
            thisEl.offset = thisEl.offset - elOffset
        
        return otherElements

    def trimPlayingWhileSounding(self, el, elStream = None, 
                               requireClass = False, padStream = False):
        '''
        Returns a Stream of deepcopies of elements in otherStream that sound at the same time as`el. but
        with any element that was sounding when el. begins trimmed to begin with el. and any element 
        sounding when el ends trimmed to end with el.
        
        if padStream is set to true then empty space at the beginning and end is filled with a generic
        Music21Object, so that no matter what otherStream is the same length as el.
        
        Otherwise is the same as allPlayingWhileSounding -- but because these elements are deepcopies,
        the difference might bite you if you're not careful.
        
        Note that you can make el an empty stream of offset X and duration Y to extract exactly
        that much information from otherStream.  
    

        OMIT_FROM_DOCS
        TODO: write: ALL. requireClass, padStream
    
        always returns a Stream, but might be an empty Stream
        '''
        if requireClass is not False:
            raise StreamException("requireClass is not implemented")
        if padStream is not False:
            raise StreamException("padStream is not implemented")
    
        raise StreamException("Not written yet")
    
        if elStream is not None: # bit of safety
            elOffset = el.getOffsetBySite(elStream)
        else:
            elOffset = el.offset
        
        otherElements = self.getElementsByOffset(elOffset, elOffset + el.quarterLength, mustBeginInSpan = False)
    
        otherElements.offset = elOffset
        otherElements.quarterLength = el.quarterLength
        for thisEl in otherElements:
            thisEl.offset = thisEl.offset - elOffset
        
        return otherElements


    #---------------------------------------------------------------------------
    # voice processing routines

    def internalize(self, container=None, 
                    classFilterList=['GeneralNote', 'Rest', 'Chord']):
        '''Gather all notes and related classes of this Stream and place inside a new container (like a Voice) in this Stream.
        '''
        if container == None:
            container = Voice
        dst = container()
        for e in self.getElementsByClass(classFilterList):
            dst.insert(e.getOffsetBySite(self), e)
            self.remove(e)
        self.insert(0, dst)

    def externalize(self):
        '''Assuming there is a container in this Stream (like a Voice), remove the container and place all contents in the Stream. 
        '''
        pass

    def voicesToParts(self):
        '''If this Stream defines one or more voices, extract each into a Part, returning a Score.

        If this Stream has no voice, return the Stream as a Part within a Score. 
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

        environLocal.printDebug(['voicesToParts(): got partCount', partCount])

        # create parts, naming ids by voice id?
        for sub in range(partCount):
            p = Part()
            s.insert(0, p)

        if self.hasMeasures():
            for m in self.getElementsByClass('Measure'):
                if m.hasVoices():
                    mActive = Measure()
                    mActive.mergeAttributes(m)
                    # merge everything except Voices; this will get
                    # clefs
                    mActive.mergeElements(m, classFilterList=['Bar', 'TimeSignature', 'Clef', 'KeySignature'])
                    for vIndex, v in enumerate(m.voices):
                        # make an independent copy
                        mNew = copy.deepcopy(mActive)
                        # merge all elements from the voice
                        mNew.mergeElements(v)
                        # insert in the appropriate part
                        s[vIndex].insert(m.getOffsetBySite(self), mNew)
                # if a measure does not have voices, simply populate
                # with elements and append
                else:
                    mNew = Measure()
                    mNew.mergeAttributes(m)
                    # get all elements
                    mNew.mergeElements(m)
                    # always place in top-part
                    s[0].insert(m.getOffsetBySite(self), mNew)
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
        '''Create a multi-part extraction from a single polyphonic Part.
        '''
        return voicesToParts()



#-------------------------------------------------------------------------------
class Voice(Stream):
    '''
    A Stream subclass for declaring that all the music in the
    stream belongs to a certain "voice" for analysis or display
    purposes.
    
    Note that both Finale's Layers and Voices as concepts are
    considered Voices here.
    '''
    pass





#-------------------------------------------------------------------------------
class Measure(Stream):
    '''A representation of a Measure organized as a Stream. 

    All properties of a Measure that are Music21 objects are found as part of 
    the Stream's elements. 
    '''

    isMeasure = True

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'timeSignatureIsNew': 'Boolean describing if the TimeSignature is different than the previous Measure.',

    'clefIsNew': 'Boolean describing if the Clef is different than the previous Measure.',

    'keyIsNew': 'Boolean describing if KeySignature is different than the previous Measure.',

    'number': 'A number representing the displayed or shown Measure number as presented in a written Score.',

    'numberSuffix': 'If a Measure number has a string annotation, such as "a" or similar, this string is stored here.',

    'layoutWidth': 'A suggestion for layout width, though most rendering systems do not support this designation. Use :class:`~music21.layout.SystemLayout` objects instead.',
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
        self.paddingLeft = 0
        self.paddingRight = 0

        if 'number' in keywords.keys():
            self.number = keywords['number']
        else:
            self.number = 0 # 0 means undefined or pickup
        self.numberSuffix = None # for measure 14a would be "a"
    
        # we can request layout width, using the same units used
        # in layout.py for systems; most musicxml readers do not support this
        # on input
        self.layoutWidth = None


    def addRepeat(self):
        # TODO: write
        pass

    def addTimeDependentDirection(self, time, direction):
        # TODO: write
        pass

    
    def measureNumberWithSuffix(self):
        if self.numberSuffix:
            return str(self.number) + self.numberSuffix
        else:
            return str(self.number)
    
    def __repr__(self):
        return "<music21.stream.%s %s offset=%s>" % \
            (self.__class__.__name__, self.measureNumberWithSuffix(), self.offset)
        
    #---------------------------------------------------------------------------
    def mergeAttributes(self, other):
        '''
        Given another Measure, configure all non-element attributes of this 
        Measure with the attributes of the other Measure. No elements 
        will be changed or copied.

        This method is necessary because Measures, unlike some Streams, 
        have attributes independent of any stored elements.
        '''
        # calling bass class sets id, groups
        music21.Music21Object.mergeAttributes(self, other)

        self.timeSignatureIsNew = other.timeSignatureIsNew
        self.clefIsNew = other.clefIsNew
        self.keyIsNew = other.keyIsNew
        self.filled = other.filled
        self.paddingLeft = other.paddingLeft
        self.paddingRight = other.paddingRight
        self.number = other.number
        self.numberSuffix = other.numberSuffix
        self.layoutWidth = other.layoutWidth

    #---------------------------------------------------------------------------
    def barDurationProportion(self, barDuration=None):
        '''Return a floating point value greater than 0 showing the proportion of the bar duration that is filled based on the highest time of all elements. 0.0 is empty, 1.0 is filled; 1.5 specifies of an overflow of half. 

        Bar duration refers to the duration of the Measure as suggested by the TimeSignature. This value cannot be determined without a Time Signature. 

        An already-obtained Duration object can be supplied with the `barDuration` optional argument. 

        >>> from music21 import *
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        0.33333...
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        0.66666...
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        1.0
        >>> m.append(copy.deepcopy(n))
        >>> m.barDurationProportion()
        1.33333...
        '''
        # passing a barDuration may save time in the lookup process
        if barDuration == None:
            barDuration = self.barDuration
        return self.highestTime / barDuration.quarterLength

    def padAsAnacrusis(self):
        '''Given an incompletely filled Measure, adjust the paddingLeft value to to represent contained events as shifted to fill the left-most duration of the bar.

        Calling this method will overwrite any previously set paddingLeft value, based on the current TimeSignature-derived `barDuration` attribute. 

        >>> from music21 import *
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> n = note.Note()
        >>> n.quarterLength = 1
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
        if proportion < 1.:
            # get 1 complement
            proportionShift = 1 - proportion
            self.paddingLeft = barDuration.quarterLength * proportionShift

            #shift = barDuration.quarterLength * proportionShift
            #environLocal.printDebug(['got anacrusis shift:', shift, 
            #                    barDuration.quarterLength, proportion])
            # this will shift all elements
            #self.shiftElements(shift, classFilterList=[note.GeneralNote])
        else:
            environLocal.printDebug(['padAsAnacrusis() called; however, no anacrusis shift necessary:', barDuration.quarterLength, proportion])

    #---------------------------------------------------------------------------
    def bestTimeSignature(self):
        '''Given a Measure with elements in it, get a TimeSignature that contains all elements.

        Note: this does not yet accommodate triplets. 
        '''
        #TODO: set limit at 11/4?

        minDurQL = 4 # smallest denominator; start with a whole note

        # find sum of all durations in quarter length
        # find if there are any dotted durations
        minDurDotted = False        
        sumDurQL = 0
        for e in self.notes:
            sumDurQL += e.quarterLength
            if e.quarterLength < minDurQL:
                minDurQL = e.quarterLength
                if e.duration.dots > 0:
                    minDurDotted = True

        # first, we need to evenly divide min dur into total
        minDurTest = minDurQL
        while True:
            partsFloor = int(sumDurQL / minDurTest)
            partsReal = sumDurQL / float(minDurTest)
            if (common.almostEquals(partsFloor, partsReal) or 
            minDurTest <= duration.typeToDuration[meter.MIN_DENOMINATOR_TYPE]):
                break
            # need to break down minDur until we can get a match
            else:
                if minDurDotted:
                    minDurTest = minDurTest / 3.
                else:
                    minDurTest = minDurTest / 2.
                    
        # see if we can get a type for the denominator      
        # if we do not have a match; we need to break down this value
        match = False
        while True:
            dType, match = duration.quarterLengthToClosestType(minDurTest) 
            if match or dType == meter.MIN_DENOMINATOR_TYPE:
                break
            if minDurDotted:
                minDurTest = minDurTest / 3.
            else:
                minDurTest = minDurTest / 2.

        minDurQL = minDurTest
        dType, match = duration.quarterLengthToClosestType(minDurQL) 
        if not match: # cant find a type for a denominator
            raise StreamException('cannot find a type for denominator %s' % minDurQL)

        # denominator is the numerical representation of the min type
        # e.g., quarter is 4, whole is 1
        for num, typeName in duration.typeFromNumDict.items():
            if typeName == dType:
                denominator = num
        # numerator is the count of min parts in the sum
        numerator = int(sumDurQL / minDurQL)

        #environLocal.printDebug(['n/d', numerator, denominator])

        ts = meter.TimeSignature()
        ts.loadRatio(numerator, denominator)
        return ts

    def _getBarDuration(self):
        '''Return the bar duration, or the Duration specified by the TimeSignature. 

        '''
        # TODO: it is possible that this should be cached or exposed as a method
        # as this search may take some time. 
        if self.timeSignature != None:
            ts = self.timeSignature
        else: # do a context-based search 
            tsStream = self.getTimeSignatures(searchContext=True,
                       returnDefault=False, sortByCreationTime=True)
            if len(tsStream) == 0:
                raise StreamException('cannot determine bar duration without a time signature reference')
            else: # it is the first found
                ts = tsStream[0]
        return ts.barDuration

    barDuration = property(_getBarDuration, 
        doc = '''Return the bar duration, or the Duration specified by the TimeSignature. TimeSignature is found first within the Measure, or within a context based search.
        ''')

    #---------------------------------------------------------------------------
    # Music21Objects are stored in the Stream's elements list 
    # properties are provided to store and access these attribute

    def _getClef(self):
        '''
        >>> a = Measure()
        >>> a.clef = clef.TrebleClef()
        >>> a.clef.sign  # clef is an element
        'G'
        '''
        # TODO: perhaps sort by priority?
        clefList = self.getElementsByClass(clef.Clef)
        # only return clefs that have offset = 0.0 
        clefList = clefList.getElementsByOffset(0)
        if len(clefList) == 0:
            return None
        else:
            return clefList[0]    
    
    def _setClef(self, clefObj):
        '''
        >>> a = Measure()
        >>> a.clef = clef.TrebleClef()
        >>> a.clef.sign    # clef is an element
        'G'
        >>> a.clef = clef.BassClef()
        >>> a.clef.sign
        'F'
        '''
        oldClef = self._getClef()
        if oldClef is not None:
            environLocal.printDebug(['removing clef', oldClef])
            junk = self.pop(self.index(oldClef))
        self.insert(0, clefObj)

    clef = property(_getClef, _setClef)    

    def _getTimeSignature(self):
        '''
        >>> a = Measure()
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
        >>> a = Measure()
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
        self.insert(0, tsObj)

    timeSignature = property(_getTimeSignature, _setTimeSignature)   

    def _getKeySignature(self):
        '''
        >>> a = Measure()
        >>> a.keySignature = key.KeySignature(0)
        >>> a.keySignature.sharps 
        0
        '''
        keyList = self.getElementsByClass(key.KeySignature)
        # only return keySignatures with offset = 0.0
        keyList = keyList.getElementsByOffset(0)
        if len(keyList) == 0:
            return None
        else:
            return keyList[0]    
    
    def _setKeySignature(self, keyObj):
        '''
        >>> a = Measure()
        >>> a.keySignature = key.KeySignature(3)
        >>> a.keySignature.sharps   
        3
        >>> a.keySignature = key.KeySignature(6)
        >>> a.keySignature.sharps
        6
        '''
        oldKey = self._getKeySignature()
        if oldKey is not None:
            #environLocal.printDebug(['removing key', oldKey])
            junk = self.pop(self.index(oldKey))
        self.insert(0, keyObj)

    keySignature = property(_getKeySignature, _setKeySignature)   

    def _getLeftBarline(self):
        '''
        >>> a = Measure()
        '''
        barList = []
        # directly access _elements, as do not want to get any bars
        # in _endElements
        for e in self._elements:
            if 'Barline' in e.classes: # take the first
                if e.getOffsetBySite(self) == 0.0:
                    barList.append(e)
                    break
        if len(barList) == 0:
            return None
        else:
            return barList[0]    
    
    def _setLeftBarline(self, barlineObj):
        '''
        >>> a = Measure()
        '''
        oldLeftBarline = self._getLeftBarline()
        barlineObj.location = 'left'

        if oldLeftBarline is not None:
            junk = self.pop(self.index(oldLeftBarline))
        self.insert(0, barlineObj)

    leftBarline = property(_getLeftBarline, _setLeftBarline, 
        doc = '''Get or set the left barline, or the Barline object found at offset zero of the Measure.
        ''')   

    def _getRightBarline(self):
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
        oldRightBarline = self._getRightBarline()

        barlineObj.location = 'right'

        if oldRightBarline is not None:
            junk = self.pop(self.index(oldRightBarline))
        # insert into _endElements
        self.storeAtEnd(barlineObj)
        
        #environLocal.printDebug(['post _setRightBarline', barlineObj, 'len of elements highest', len(self._endElements)])

    rightBarline = property(_getRightBarline, _setRightBarline, 
        doc = '''Get or set the right barline, or the Barline object found at the offset equal to the bar duration. 

        >>> from music21 import *
        >>> b = bar.Barline('light-heavy')
        >>> m = stream.Measure()
        >>> m.rightBarline = b
        >>> m.rightBarline.style
        'light-heavy'
        ''')   

    #---------------------------------------------------------------------------
    def _getMX(self):
        '''Return a musicxml Measure, populated with notes, chords, rests
        and a musixcml Attributes, populated with time, meter, key, etc

        >>> a = note.Note()
        >>> a.quarterLength = 4
        >>> b = Measure()
        >>> b.insert(0, a)
        >>> len(b) 
        1
        >>> mxMeasure = b.mx
        >>> len(mxMeasure) 
        1
        '''
        return musicxmlTranslate.measureToMx(self)

    def _setMX(self, mxMeasure):
        '''Given an mxMeasure, create a music21 measure
        '''
        # in just getting value for one measure, cannot create multiple parts
        # for multi-staff presentation
        m, staffReference = musicxmlTranslate.mxToMeasure(mxMeasure,
                            inputM21=self)
        return m

    mx = property(_getMX, _setMX)    

    def _getMusicXML(self):
        '''Provide a complete MusicXML: representation. 
        '''
        return musicxmlTranslate.measureToMusicXML(self)

    musicxml = property(_getMusicXML)



class Part(Stream):
    '''A Stream subclass for designating music that is
    considered a single part.
    
    May be enclosed in a staff (for instance, 2nd and 3rd trombone
    on a single staff), may enclose staves (piano treble and piano bass),
    or may not enclose or be enclosed by a staff (in which case, it
    assumes that this part fits on one staff and shares it with no other
    part
    '''

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)

    def makeAccidentals(self):
        '''
        This overridden method of Stream.makeAccidentals provides the management of passing pitches from a past Measure to each new measure for processing. 
        '''
        # process make accidentals for each measure
        measureStream = self.getElementsByClass('Measure')
        for i in range(len(measureStream)):
            m = measureStream[i]
            if m.keySignature != None:
                ksLast = m.keySignature
            else:
                ksLast = None
            # if beyond the first measure, use the pitches from the last
            # measure for context
            if i > 0:
                m.makeAccidentals(measureStream[i-1].pitches,
                    useKeySignature=ksLast, searchKeySignatureByContext=False)
            else:
                m.makeAccidentals(useKeySignature=ksLast, 
                    searchKeySignatureByContext=False)


    def _getLily(self):
        lv = Stream._getLily(self)
        lv2 = lilyModule.LilyString("\t\n \\new Staff " + lv.value)
        return lv2
    
    lily = property(_getLily)



class PartStaff(Part):
    '''A Part subclass for designating music that is represented on a single staff but may only be one of many staffs for a single part.
    
    '''
    def __init__(self, *args, **keywords):
        Part.__init__(self, *args, **keywords)





# class Staff(Stream):
#     '''
#     A Stream subclass for designating music on a single staff
#     '''
#     # NOTE: not yet implemented
#     staffLines = 5
# 
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
# class System(Stream):
#     '''Totally optional: designation that all the music in this Stream
#     belongs in a single system.
#     '''
#     systemNumber = 0
#     systemNumbering = "Score" # or Page; when do system numbers reset?
# 
# class Page(Stream):
#     '''
#     Totally optional: designation that all the music in this Stream
#     belongs on a single notated page
#     '''
#     pageNumber = 0
#     

class Score(Stream):
    """A Stream subclass for handling multi-part music.
    
    Absolutely optional (the largest containing Stream in a piece could be
    a generic Stream, or a Part, or a Staff).  And Scores can be
    embedded in other Scores (in fact, our original thought was to call
    this class a Fragment because of this possibility of continuous
    embedding), but we figure that many people will like calling the largest
    container a Score and that this will become a standard.
    """

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)
        # while a metadata object is often expected, adding here prob not       
        # a good idea. 
        #self.insert(0, metadata.Metadata())

    def _getLily(self):
        '''
        returns the lily code for a score.
        '''
        ret = lilyModule.LilyString()
        for thisOffsetPosition in self.groupElementsByOffset():
            if len(thisOffsetPosition) > 1:
                ret += " << "
                for thisSubElement in thisOffsetPosition:
                    if hasattr(thisSubElement, "lily"):
                        ret += thisSubElement.lily
                    else:
                        # TODO: write out debug code here
                        pass
                ret += " >>\n"
            else:
                if hasattr(thisOffsetPosition[0], "lily"):
                    ret += thisOffsetPosition[0].lily
                else:
                    # TODO: write out debug code here
                    pass
        return ret
        
    lily = property(_getLily)


    def _getParts(self):
        '''        
        '''
        return self.getElementsByClass(Part)

    parts = property(_getParts, 
        doc='''Return all :class:`~music21.stream.Part` objects in a :class:`~music21.stream.Score`.

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> parts = s.parts     
        >>> len(parts)
        4
        ''')

    def measures(self, numberStart, numberEnd, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature], gatherSpanners=True):
        '''This method override the :meth:`~music21.stream.Stream.measures` method on Stream. This creates a new Score stream that has the same measure range for all Parts.
        '''
        post = Score()
        post.mergeAttributes(self)
        # note that this will strip all objects that are not Parts
        for p in self.getElementsByClass('Part'):
            # insert all at zero
            measuredPart = p.measures(numberStart, numberEnd,
                        collect, gatherSpanners=gatherSpanners)
            post.insert(0, measuredPart)
        # must manually add any spanners; do not need to add .flat, as Stream.measures will handle lower level
        if gatherSpanners:
            spStream = self.spanners
            for sp in spStream:
                post.insert(0, sp)
        return post


    def measure(self, measureNumber, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature], gatherSpanners=True):
        '''Given a measure number, return a single :class:`~music21.stream.Measure` object if the Measure number exists, otherwise return None.

        This method override the :meth:`~music21.stream.Stream.measures` method on Stream. This creates a new Score stream that has the same measure range for all Parts.

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> len(a.measure(3)[0]) # contains 1 measure
        1
        '''

        post = Score()
        post.mergeAttributes(self)
        # note that this will strip all objects that are not Parts
        for p in self.getElementsByClass('Part'):
            # insert all at zero
            mStream = p.measures(measureNumber, measureNumber, 
                collect=collect, gatherSpanners=gatherSpanners)
            if len(mStream) > 0:
                post.insert(0, mStream)

        if gatherSpanners:
            spStream = self.spanners
            for sp in spStream:
                post.insert(0, sp)
        return post


    def measureOffsetMap(self, classFilterList=None):
        '''This method overrides the :meth:`~music21.stream.Stream.measureOffsetMap` method of Stream. This creates a map based on all contained Parts in this Score. Measures found in multiple Parts with the same offset will be appended to the same list. 

        This does not assume that all Parts have measures with identical offsets.
        '''
        map = {}
        for p in self.getElementsByClass(Part):
            mapPartial = p.measureOffsetMap(classFilterList)
            #environLocal.printDebug(['mapPartial', mapPartial])
            for key in mapPartial.keys():
                if key not in map.keys():
                    map[key] = []
                for m in mapPartial[key]: # get measures from partial
                    if m not in map[key]:
                        map[key].append(m)
        return map

# functionality moved to Stream.stripTies()
#     def stripTies(self, inPlace=False, matchByPitch=False):
#         '''Apply strip ties to each class:`~music21.part.Part` contained within this Score. 
# 
#         This method will retain class:`~music21.part.Measure` objects and Parts.
#         '''
# 
#         if not inPlace: # make a copy
#             returnObj = deepcopy(self)
#         else:
#             returnObj = self
# 
#         for p in returnObj.getElementsByClass(Part):
#             # strip ties will use the appropriate flat presentation
#             # in place: already have a copy if nec
#             p.stripTies(inPlace=True, matchByPitch=matchByPitch,
#                          retainContainers=True) 
#         return returnObj
        

    def sliceByGreatestDivisor(self, inPlace=True, addTies=True):
        '''Slice all duration of all part by the minimum duration that can be summed to each concurrent duration. 

        Overrides method defined on Stream.
        '''
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
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
                for e in m.notes:
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

        return returnObj


    def chordify(self, addTies=True, displayTiedAccidentals=False):
        '''Split all Durations in all parts, if multi-part, by all unique offsets. All simultaneous durations are then gathered into single chords. 
        '''
        returnObj = deepcopy(self)

        mStream = returnObj.parts[0].getElementsByClass('Measure')
        mCount = len(mStream)
        if mCount == 0:
            mCount = 1 # treat as a single measure
        for i in range(mCount): # may be 1
            # first, collect all unique offsets for each measure
            uniqueOffsets = []
            for p in returnObj.getElementsByClass('Part'):
                if p.hasMeasures():
                    m = p.getElementsByClass('Measure')[i]
                else:
                    m = p # treat the entire part as one measure
                for e in m.notes:
                    # offset values here will be relative to the Measure
                    o = e.getOffsetBySite(m)
                    if o not in uniqueOffsets:
                        uniqueOffsets.append(o)
            #environLocal.printDebug(['chordify: uniqueOffsets for all parts, m', uniqueOffsets, i])

            uniqueOffsets = sorted(uniqueOffsets)

            for p in returnObj.getElementsByClass('Part'):
                # get one measure at a time
                if p.hasMeasures():
                    m = p.getElementsByClass('Measure')[i]
                else:
                    m = p # treat the entire part as one measure
                # working with a copy, in place can be true
                m.sliceAtOffsets(offsetList=uniqueOffsets, addTies=addTies, 
                    inPlace=True,
                    displayTiedAccidentals=displayTiedAccidentals )

        # do in place as already a copy has been made
        post = returnObj.flat.makeChords(includePostWindow=True, 
            removeRedundantPitches=True,
            gatherArticulations=True, gatherExpressions=True, inPlace=True)
        return post

    def partsToVoices(self, voiceAllocation=2, permitOneVoicePerPart=False):
        '''Given a multi-part :class:`~music21.stream.Score`, return a new Score that combines parts into voices. 

        The `voiceAllocation` parameter can be an integer: if so, this many parts will each be grouped into one part as voices

        The `permitOneVoicePerPart` parameter, if True, will encode a single voice inside a single Part, rather than leaving a single part alone. 
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
        elif common.isListLike(voiceAllocation):
            for group in voiceAllocation:
                sub = []
                # if a single entry
                if not common.isListLike(group):
                    # group is a single index
                    sub.append(self.parts[group])
                else:
                    for id in group:
                        sub.append(self.parts[id])
                bundle.append(sub)
        else:
            raise StreamException('incorrect voiceAllocation format: %s' % voiceAllocation)

        environLocal.printDebug(['partsToVoices() bundle:', bundle]) 

        s = Score()
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
                        mActive.mergeElements(m, classFilterList=['Bar', 'TimeSignature', 'Clef', 'KeySignature'])

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
                    for e in m.notes: #m.getElementsByClass():
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
        '''Reduce a polyphonic work into one or more staves.
        '''
        voiceAllocation = 2
        permitOneVoicePerPart = False

        return self.partsToVoices(voiceAllocation=voiceAllocation,
            permitOneVoicePerPart=permitOneVoicePerPart)



# this was commented out as it is not immediately needed
# could be useful later in a variety of contexts
#     def mergeStaticNotes(self, attributesList=['pitch'], inPlace=False):
#         '''Given a multipart work, look to see if the next verticality causes a change in one or more attributes, as specified by the `attributesList` parameter. If no change is found, merge the next durations with the previous. 
# 
#         Presently, this assumes that all parts have the same number of notes. This must thus be used in conjunction with sliceByGreatestDivisor() to properly match notes between different parts.
#         '''
# 
#         if not inPlace: # make a copy
#             returnObj = deepcopy(self)
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
#             while j < len(mGuide.notes) - 1:
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
#                         compare.append(getattr(m.notes[j], attr))
#                         compareNext.append(getattr(m.notes[jNext], attr))
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




class Opus(Stream):
    '''A Stream subclass for handling multi-work music encodings. Many ABC files, for example, define multiple works or parts within a single file. 
    '''

    #TODO get by title, possibly w/ regex

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)

    def getNumbers(self):
        '''Return a list of all numbers defined in this Opus.

        >>> from music21 import *
        >>> o = corpus.parseWork('josquin/ovenusbant')
        >>> o.getNumbers()
        ['1', '2', '3']
        '''
        post = []
        for s in self.getElementsByClass('Score'):
            post.append(s.metadata.number)
        return post

    def getScoreByNumber(self, opusMatch):
        '''Get Score objects from this Stream by number. Performs title search using the :meth:`~music21.metadata.Metadata.search` method, and returns the first result. 

        >>> from music21 import *
        >>> o = corpus.parseWork('josquin/ovenusbant')
        >>> o.getNumbers()
        ['1', '2', '3']
        >>> s = o.getScoreByNumber(2)
        >>> s.metadata.title
        'O Venus bant'
        >>> s.metadata.alternativeTitle
        'Tenor'
        '''
        for s in self.getElementsByClass('Score'):
            match, field = s.metadata.search(opusMatch, 'number')
            if match:
                return s

#             if s.metadata.number == opusMatch:
#                 return s
#             elif s.metadata.number == str(opusMatch):
#                 return s

    def getScoreByTitle(self, titleMatch):
        '''Get Score objects from this Stream by a title. Performs title search using the :meth:`~music21.metadata.Metadata.search` method, and returns the first result. 

        >>> from music21 import *
        >>> o = corpus.parseWork('essenFolksong/erk5')
        >>> s = o.getScoreByTitle('Vrienden, kommt alle gaere')
        >>> s = o.getScoreByTitle('(.*)kommt(.*)') # regular expression
        >>> s.metadata.title
        'Vrienden, kommt alle gaere'
        '''
        for s in self.getElementsByClass('Score'):
            match, field = s.metadata.search(titleMatch, 'title')
            if match:
                return s

    def _getScores(self):
        '''        
        '''
        return self.getElementsByClass(Score)

    scores = property(_getScores, 
        doc='''Return all :class:`~music21.stream.Score` objects in a :class:`~music21.stream.Opus`.

        >>> from music21 import *
        ''')


    def mergeScores(self):
        '''Some Opus object represent numerous scores that are individual parts of the same work. This method will treat each contained Score as a Part, merging and returning a single Score with merged Metadata.

        >>> from music21 import *
        >>> o = corpus.parseWork('josquin/milleRegrets')
        >>> s = o.mergeScores()
        >>> s.metadata.title
        'Mille regrets'
        >>> len(s.parts)
        4
        '''
        sNew = Score()
        mdNew = metadata.Metadata()

        for s in self.scores:
            p = s.parts[0] # assuming only one part
            sNew.insert(0, p)
    
            md = s.metadata
            # presently just getting the first of attributes encountered
            if md != None:
                #environLocal.printDebug(['subscore meta data', md, 'md.composer', md.composer, 'md.title', md.title])
                if md.title != None and mdNew.title == None:
                    mdNew.title = md.title
                if md.composer != None and mdNew.composer == None:
                    mdNew.composer = md.composer

        sNew.insert(0, mdNew)
        return sNew

    #---------------------------------------------------------------------------
    def write(self, fmt=None, fp=None):
        '''
        Displays an object in a format provided by the fmt argument or, if not provided, the format set in the user's Environment.

        This method overrides the behavior specified in :class:`~music21.base.Music21Object`.
        '''
        for s in self.scores:
            s.write(fmt=fmt, fp=fp)

    def show(self, fmt=None, app=None):
        '''
        Displays an object in a format provided by the fmt argument or, if not provided, the format set in the user's Environment.

        This method overrides the behavior specified in :class:`~music21.base.Music21Object`.
        '''
        for s in self.scores:
            s.show(fmt=fmt, app=app)



#-------------------------------------------------------------------------------
class SpannerStorage(Stream):
    '''
    For advanced use. This Stream subclass is used inside of a Spanner object to provide object storage.

    This subclass name can be used to search an object's DefinedContexts and find any and all locations that are SpannerStorage objects.

    A `spannerParent` keyword argument must be provided by the Spanner in creation. 
    '''
    def __init__(self, *arguments, **keywords):
        Stream.__init__(self, *arguments, **keywords)

        # must provide a keyword argument with a reference to the spanner parent
        # could name spannerContainer or other?
        #environLocal.printDebug('keywords', keywords)
        self.spannerParent = None
        if 'spannerParent' in keywords.keys():
            self.spannerParent = keywords['spannerParent']



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testLilySimple(self):
        a = Stream()
        ts = meter.TimeSignature("3/4")
        
        b = Stream()
        q = note.QuarterNote()
        q.octave = 5
        b.repeatInsert(q, [0,1,2,3])
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.insert(0, bestC)
        a.insert(0, ts)
        a.insert(0, b)
        a.lily.showPNG()

    def testLilySemiComplex(self):
        a = Stream()
        ts = meter.TimeSignature("3/8")
        
        b = Stream()
        q = note.EighthNote()

        dur1 = duration.Duration()
        dur1.type = "eighth"
        
        tup1 = duration.Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur1]

        q.octave = 2
        q.duration.appendTuplet(tup1)
        
        
        for i in range(0,5):
            b.append(deepcopy(q))
            b.elements[i].accidental = pitch.Accidental(i - 2)
        
        b.elements[0].duration.tuplets[0].type = "start"
        b.elements[-1].duration.tuplets[0].type = "stop"
        b.elements[2].editorial.comment.text = "a real C"
         
        bestC = b.bestClef(allowTreble8vb = True)
        a.insert(0, bestC)
        a.insert(0, ts)
        a.insert(0, b)
        a.lily.showPNG()

        
    def testScoreLily(self):
        '''
        Test the lilypond output of various score operations.
        '''

        import meter
        c = note.Note("C4")
        d = note.Note("D4")
        ts = meter.TimeSignature("2/4")
        s1 = Part()
        s1.append(deepcopy(c))
        s1.append(deepcopy(d))
        s2 = Part()
        s2.append(deepcopy(d))
        s2.append(deepcopy(c))
        score1 = Score()
        score1.insert(ts)
        score1.insert(s1)
        score1.insert(s2)
        score1.lily.showPNG()
        

    def testMXOutput(self):
        '''A simple test of adding notes to measures in a stream. 
        '''
        c = Stream()
        for m in range(4):
            b = Measure()
            for pitch in ['a', 'g', 'c#', 'a#']:
                a = note.Note(pitch)
                b.append(a)
            c.append(b)
        c.show()

    def testMxMeasures(self):
        '''A test of the automatic partitioning of notes in a measure and the creation of ties.
        '''

        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.repeatInsert(n, range(0,120,3))
        #a.show() # default time signature used
        
        a.insert( 0, meter.TimeSignature("5/4")  )
        a.insert(10, meter.TimeSignature("2/4")  )
        a.insert( 3, meter.TimeSignature("3/16") )
        a.insert(20, meter.TimeSignature("9/8")  )
        a.insert(40, meter.TimeSignature("10/4") )
        a.show()


    def testMultipartStreams(self):
        '''Test the creation of multi-part streams by simply having streams within streams.

        '''
        q = Stream()
        r = Stream()
        for x in ['c3','a3','g#4','d2'] * 10:
            n = note.Note(x)
            n.quarterLength = .25
            q.append(n)

            m = note.Note(x)
            m.quarterLength = 1.125
            r.append(m)

        s = Stream() # container
        s.insert(q)
        s.insert(r)
        s.insert(0, meter.TimeSignature("3/4") )
        s.insert(3, meter.TimeSignature("5/4") )
        s.insert(8, meter.TimeSignature("3/4") )

        s.show()
            


    def testMultipartMeasures(self):
        '''This demonstrates obtaining slices from a stream and layering
        them into individual parts.

        OMIT_FROM_DOCS
        TODO: this should show instruments
        this is presently not showing instruments 
        probably b/c when appending to s Stream activeSite is set to that stream
        '''
        from music21 import corpus, converter
        a = converter.parse(corpus.getWork(['mozart', 'k155','movement2.xml']))
        b = a[3][10:20]
        c = a[3][20:30]
        d = a[3][30:40]

        s = Stream()
        s.insert(b)
        s.insert(c)
        s.insert(d)
        s.show()


    def testCanons(self):
        '''A test of creating a canon with shifted presentations of a source melody. This also demonstrates 
        the addition of rests to parts that start late or end early.

        The addition of rests happens with makeRests(), which is called in 
        musicxml generation of a Stream.
        '''
        
        a = ['c', 'g#', 'd-', 'f#', 'e', 'f' ] * 4

        s = Stream()
        partOffsetShift = 1.25
        partOffset = 0
        for part in range(6):  
            p = Stream()
            for pitchName in a:
                n = note.Note(pitchName)
                n.quarterLength = 1.5
                p.append(n)
            p.offset = partOffset
            s.insert(p)
            partOffset += partOffsetShift

        s.show()



    def testBeamsPartial(self):
        '''This demonstrates a partial beam; a beam that is not connected between more than one note. 
        '''
        q = Stream()
        for x in [.125, .25, .25, .125, .125, .125] * 30:
            n = note.Note('c')
            n.quarterLength = x
            q.append(n)

        s = Stream() # container
        s.insert(q)

        s.insert(0, meter.TimeSignature("3/4") )
        s.insert(3, meter.TimeSignature("5/4") )
        s.insert(8, meter.TimeSignature("4/4") )

        s.show()


    def testBeamsStream(self):
        '''A test of beams applied to different time signatures. 
        '''
        q = Stream()
        r = Stream()
        p = Stream()
        for x in ['c3','a3','c#4','d3'] * 30:
            n = note.Note(x)
            #n.quarterLength = random.choice([.25, .125, .5])
            n.quarterLength = random.choice([.25])
            q.append(n)
            m = note.Note(x)
            m.quarterLength = .5
            r.append(m)
            o = note.Note(x)
            o.quarterLength = .125
            p.append(o)

        s = Stream() # container
        s.append(q)
        s.append(r)
        s.append(p)

        s.insert(0, meter.TimeSignature("3/4") )
        s.insert(3, meter.TimeSignature("5/4") )
        s.insert(8, meter.TimeSignature("4/4") )
        self.assertEqual(len(s.flat.notes), 360)

        s.show()


    def testBeamsMeasure(self):
        aMeasure = Measure()
        aMeasure.timeSignature = meter.TimeSignature('4/4')
        aNote = note.Note()
        aNote.quarterLength = .25
        aMeasure.repeatAppend(aNote,16)
        bMeasure = aMeasure.makeBeams()
        bMeasure.show()


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        for part in sys.modules[self.__module__].__dict__.keys():
            if part.startswith('_') or part.startswith('__'):
                continue
            elif part in ['Test', 'TestExternal']:
                continue
            elif callable(part):
                environLocal.printDebug(['testing copying on', part])
                obj = getattr(module, part)()
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertNotEqual(a, obj)
                self.assertNotEqual(b, obj)
            
    
    def testAdd(self):
        a = Stream()
        for i in range(5):
            a.insert(0, music21.Music21Object())
        self.assertTrue(a.isFlat)
        a[2] = note.Note("C#")
        self.assertTrue(a.isFlat)
        a[3] = Stream()
        self.assertFalse(a.isFlat)

    def testSort(self):
        s = Stream()
        s.repeatInsert(note.Note("C#"), [0.0, 2.0, 4.0])
        s.repeatInsert(note.Note("D-"), [1.0, 3.0, 5.0])
        self.assertFalse(s.isSorted)
        y = s.sorted
        self.assertTrue(y.isSorted)
        g = ""
        for myElement in y:
            g += "%s: %s; " % (myElement.offset, myElement.name)
        self.assertEqual(g, '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ')

    def testFlatSimple(self):
        s1 = Score()
        s1.id = "s1"
        
        p1 = Part()
        p1.id = "p1"
        
        p2 = Part()
        p2.id = "p2"

        n1 = note.HalfNote("C")
        n2 = note.QuarterNote("D")
        n3 = note.QuarterNote("E")
        n4 = note.HalfNote("F")
        n1.id = "n1"
        n2.id = "n2"
        n3.id = "n3"
        n4.id = "n4"

        p1.append(n1)
        p1.append(n2)

                
        p2.append(n3)
        p2.append(n4)

        p2.offset = 20.0

        s1.insert(p1)
        s1.insert(p2)

        
        sf1 = s1.flat
        sf1.id = "flat s1"
        
#        for site in n4._definedContexts.getSites():
#            print site.id,
#            print n4._definedContexts.getOffsetBySite(site)
        
        self.assertEqual(len(sf1), 4)
        assert(sf1[1] is n2)
        

    def testActiveSiteCopiedStreams(self):
        srcStream = Stream()
        srcStream.insert(3, note.Note())
        # the note's activeSite is srcStream now
        self.assertEqual(srcStream[0].activeSite, srcStream)

        midStream = Stream()
        for x in range(2):
            srcNew = deepcopy(srcStream)
#             for n in srcNew:
#                 offset = n.getOffsetBySite(srcStream)

            #got = srcNew[0].getOffsetBySite(srcStream)

            #for n in srcNew: pass

            srcNew.offset = x * 10 
            midStream.insert(srcNew)
            self.assertEqual(srcNew.offset, x * 10)

        # no offset is set yet
        self.assertEqual(midStream.offset, 0)

        # component streams have offsets
        self.assertEqual(midStream[0].getOffsetBySite(midStream), 0)
        self.assertEqual(midStream[1].getOffsetBySite(midStream), 10.0)

        # component notes still have a location set to srcStream
        self.assertEqual(midStream[1][0].getOffsetBySite(srcStream), 3.0)

        # component notes still have a location set to midStream[1]
        self.assertEqual(midStream[1][0].getOffsetBySite(midStream[1]), 3.0)        

        # one location in midstream
        self.assertEqual(len(midStream._definedContexts), 1)
        
        #environLocal.printDebug(['srcStream', srcStream])
        #environLocal.printDebug(['midStream', midStream])
        x = midStream.flat

    def testSimpleRecurse(self):
        st1 = Stream()
        st2 = Stream()
        n1 = note.Note()
        st2.insert(10, n1)
        st1.insert(12, st2)
        self.assertTrue(st1.flat.sorted[0] is n1)
        self.assertEqual(st1.flat.sorted[0].offset, 22.0)
        
    def testStreamRecursion(self):
        srcStream = Stream()
        for x in range(6):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            n.offset = x * 1
            srcStream.insert(n)

        self.assertEqual(len(srcStream), 6)
        self.assertEqual(len(srcStream.flat), 6)
        self.assertEqual(srcStream.flat[1].offset, 1.0)

#        self.assertEqual(len(srcStream.getOverlaps()), 0)

        midStream = Stream()
        for x in range(4):
            srcNew = deepcopy(srcStream)
            srcNew.offset = x * 10 
            midStream.insert(srcNew)

        self.assertEqual(len(midStream), 4)
        environLocal.printDebug(['pre flat of mid stream'])
        self.assertEqual(len(midStream.flat), 24)
#        self.assertEqual(len(midStream.getOverlaps()), 0)
        mfs = midStream.flat.sorted
        self.assertEqual(mfs[7]._definedContexts.getOffsetBySite(mfs), 11.0)

        farStream = Stream()
        for x in range(7):
            midNew = deepcopy(midStream)
            midNew.offset = x * 100 
            farStream.insert(midNew)

        self.assertEqual(len(farStream), 7)
        self.assertEqual(len(farStream.flat), 168)
#        self.assertEqual(len(farStream.getOverlaps()), 0)
#
        # get just offset times
        # elementsSorted returns offset, dur, element
        offsets = [a.offset for a in farStream.flat]

        # create what we epxect to be the offsets
        offsetsMatch = range(0, 6)
        offsetsMatch += [x + 10 for x in range(0, 6)]
        offsetsMatch += [x + 20 for x in range(0, 6)]
        offsetsMatch += [x + 30 for x in range(0, 6)]
        offsetsMatch += [x + 100 for x in range(0, 6)]
        offsetsMatch += [x + 110 for x in range(0, 6)]

        self.assertEqual(offsets[:len(offsetsMatch)], offsetsMatch)

    def testStreamSortRecursion(self):
        farStream = Stream()
        for x in range(4):
            midStream = Stream()
            for y in range(4):
                nearStream = Stream()
                for z in range(4):
                    n = note.Note("G#")
                    n.duration = duration.Duration('quarter')
                    nearStream.insert(z * 2, n)     # 0, 2, 4, 6
                midStream.insert(y * 5, nearStream) # 0, 5, 10, 15
            farStream.insert(x * 13, midStream)     # 0, 13, 26, 39
        
        # get just offset times
        # elementsSorted returns offset, dur, element
        fsfs = farStream.flat.sorted
        offsets = [a.offset for a in fsfs]  # safer is a.getOffsetBySite(fsfs)
        offsetsBrief = offsets[:20]
        self.assertEquals(offsetsBrief, [0, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 15, 16, 17, 17, 18, 19, 19])





    def testOverlapsA(self):
        a = Stream()
        # here, the thir item overlaps with the first
        for offset, dur in [(0,12), (3,2), (11,3)]:
            n = note.Note('G#')
            n.duration = duration.Duration()
            n.duration.quarterLength = dur
            n.offset = offset
            a.insert(n)

        includeDurationless = True
        includeEndBoundary = False

        simultaneityMap, overlapMap = a._findLayering(a.flat, 
                                  includeDurationless, includeEndBoundary)
        self.assertEqual(simultaneityMap, [[], [], []])
        self.assertEqual(overlapMap, [[1,2], [0], [0]])


        post = a._consolidateLayering(a.flat, overlapMap)
        # print post

        #found = a.getOverlaps(includeDurationless, includeEndBoundary)
        # there should be one overlap group
        #self.assertEqual(len(found.keys()), 1)
        # there should be three items in this overlap group
        #self.assertEqual(len(found[0]), 3)

        a = Stream()
        # here, the thir item overlaps with the first
        for offset, dur in [(0,1), (1,2), (2,3)]:
            n = note.Note('G#')
            n.duration = duration.Duration()
            n.duration.quarterLength = dur
            n.offset = offset
            a.insert(n)

        includeDurationless = True
        includeEndBoundary = True

        simultaneityMap, overlapMap = a._findLayering(a.flat, 
                                  includeDurationless, includeEndBoundary)
        self.assertEqual(simultaneityMap, [[], [], []])
        self.assertEqual(overlapMap, [[1], [0,2], [1]])

        post = a._consolidateLayering(a.flat, overlapMap)



    def testOverlapsB(self):

        a = Stream()
        for x in range(4):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            n.offset = x * 1
            a.insert(n)
        d = a.getOverlaps(True, False) 
        # no overlaps
        self.assertEqual(len(d), 0)

        
        # including coincident boundaries
        d = a.getOverlaps(includeDurationless=True, includeEndBoundary=True) 
        environLocal.printDebug(['testOverlapsB', d])
        # return one dictionary that has a reference to each note that 
        # is in the same overlap group
        self.assertEqual(len(d), 1)
        self.assertEqual(len(d[0]), 4)


#         a = Stream()
#         for x in [0,0,0,0,13,13,13]:
#             n = note.Note('G#')
#             n.duration = duration.Duration('half')
#             n.offset = x
#             a.insert(n)
#         d = a.getOverlaps() 
#         len(d[0])
#         4
#         len(d[13])
#         3
#         a = Stream()
#         for x in [0,0,0,0,3,3,3]:
#             n = note.Note('G#')
#             n.duration = duration.Duration('whole')
#             n.offset = x
#             a.insert(n)
# 
#         # default is to not include coincident boundaries
#         d = a.getOverlaps() 
#         len(d[0])
#         7

    def testStreamDuration(self):
        a = Stream()
        q = note.QuarterNote()
        a.repeatInsert(q, [0,1,2,3])
        self.assertEqual(a.highestOffset, 3)
        self.assertEqual(a.highestTime, 4)
        self.assertEqual(a.duration.quarterLength, 4.0)
         
        newDuration = duration.Duration("half")
        self.assertEqual(newDuration.quarterLength, 2.0)

        a.duration = newDuration
        self.assertEqual(a.duration.quarterLength, 2.0)
        self.assertEqual(a.highestTime, 4)

    def testLilySimple(self):
        a = Stream()
        ts = meter.TimeSignature("3/4")
        
        b = Stream()
        q = note.QuarterNote()
        q.octave = 5
        b.repeatInsert(q, [0,1,2,3])
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.insert(bestC)
        a.insert(ts)
        a.insert(b)
        self.assertEqual(a.lily.value, u'\n  { \\clef "treble"  \\time 3/4  \n  { c\'\'4 c\'\'4 c\'\'4 c\'\'4  }   } ')

    def testLilySemiComplex(self):
        from music21 import pitch

        a = Stream()
        ts = meter.TimeSignature("3/8")
        
        b = Stream()
        q = note.EighthNote()

        dur1 = duration.Duration()
        dur1.type = "eighth"
        
        tup1 = duration.Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur1]

        q.octave = 2
        q.duration.appendTuplet(tup1)
        
        
        for i in range(0,5):
            b.append(deepcopy(q))
            b.elements[i].accidental = pitch.Accidental(i - 2)
        
        b.elements[0].duration.tuplets[0].type = "start"
        b.elements[-1].duration.tuplets[0].type = "stop"
        b2temp = b.elements[2]
        c = b2temp.editorial
        c.comment.text = "a real C"
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.insert(bestC)
        a.insert(ts)
        a.insert(b)
        self.assertEqual(a.lily.value,  u'\n  { \\clef "bass"  \\time 3/8  \n  { \\times 3/5 {ceses,8 ces,8 c,8_"a real C" cis,8 cisis,8}  }   } ')

    def testScoreLily(self):
        c = note.Note("C4")
        d = note.Note("D4")
        ts = meter.TimeSignature("2/4")
        s1 = Part()
        s1.append(deepcopy(c))
        s1.append(deepcopy(d))
        s2 = Part()
        s2.append(deepcopy(d))
        s2.append(deepcopy(c))
        score1 = Score()
        score1.insert(ts)
        score1.insert(s1)
        score1.insert(s2)
        self.assertEqual(u" << \\time 2/4 \t\n \\new Staff \n  { c'4 d'4  } \t\n \\new Staff \n  { d'4 c'4  }  >>\n", score1.lily.value)



    def testMeasureStream(self):
        '''An approach to setting TimeSignature measures in offsets and durations
        '''
        a = meter.TimeSignature('3/4')
        b = meter.TimeSignature('5/4')
        c = meter.TimeSignature('2/4')


        a.duration = duration.Duration()
        b.duration = duration.Duration()
        c.duration = duration.Duration()

        # 20 measures of 3/4
        a.duration.quarterLength = 20 * a.barDuration.quarterLength
        # 10 measures of 5/4
        b.duration.quarterLength = 10 * b.barDuration.quarterLength
        # 5 measures of 2/4
        c.duration.quarterLength = 5 * c.barDuration.quarterLength


        m = Stream()
        m.append(a)
        m.append(b)
        m.append(c)
    
        self.assertEqual(m[1].offset, (20 * a.barDuration.quarterLength))    
        self.assertEqual(m[2].offset, ((20 * a.barDuration.quarterLength) + 
                                      (10 * b.barDuration.quarterLength)))    



    def testMultipartStream(self):
        '''Test the creation of streams with multiple parts. See versions
        of this tests in TestExternal for more details
        '''
        q = Stream()
        r = Stream()
        for x in ['c3','a3','g#4','d2'] * 10:
            n = note.Note(x)
            n.quarterLength = .25
            q.append(n)

            m = note.Note(x)
            m.quarterLength = 1
            r.append(m)

        s = Stream() # container
        s.insert(q)
        s.insert(r)
        s.insert(0, meter.TimeSignature("3/4") )
        s.insert(3, meter.TimeSignature("5/4") )
        s.insert(8, meter.TimeSignature("3/4") )
        self.assertEqual(len(s.flat.notes), 80)

        from music21 import corpus, converter
        thisWork = corpus.getWork('haydn/opus74no2/movement4.xml')
        a = converter.parse(thisWork)

        b = a[3][10:20]
        environLocal.printDebug(['b', b, b.getSiteIds()])
        c = a[3][20:30]
        environLocal.printDebug(['c', c, c.getSiteIds()])
        d = a[3][30:40]
        environLocal.printDebug(['d', d, d.getSiteIds()])

        s2 = Stream()
        environLocal.printDebug(['s2', s2, id(s2)])

        s2.insert(b)
        s2.insert(c)
        s2.insert(d)




    def testActiveSites(self):
        '''Test activeSite relationships.

        Note that here we see why sometimes qualified class names are needed.
        This test passes fine with class names Part and Measure when run interactively, 
        creating a Test instance. When run from the command line
        Part and Measure do not match, and instead music21.stream.Part has to be 
        employed instead. 
        '''

        from music21 import corpus, converter
        a = converter.parse(corpus.getWork('haydn/opus74no2/movement4.xml'))

        # test basic activeSite relationships
        b = a[3]
        self.assertEqual(isinstance(b, music21.stream.Part), True)
        self.assertEqual(b.activeSite, a)

        # this, if called, actively destroys the activeSite relationship!
        # on the measures (as new Elements are not created)
        #m = b.getElementsByClass('Measure')[5]
        #self.assertEqual(isinstance(m, Measure), True)

        # this false b/c, when getting the measures, activeSites are lost
        #self.assertEqual(m.activeSite, b) #measures activeSite should be part

        self.assertEqual(isinstance(b[8], music21.stream.Measure), True)
        self.assertEqual(b[8].activeSite, b) #measures activeSite should be part


        # a different test derived from a TestExternal
        q = Stream()
        r = Stream()
        for x in ['c3','a3','c#4','d3'] * 30:
            n = note.Note(x)
            n.quarterLength = random.choice([.25])
            q.append(n)
            m = note.Note(x)
            m.quarterLength = .5
            r.append(m)
        s = Stream() # container
        s.insert(q)
        s.insert(r)

        self.assertEqual(q.activeSite, s)
        self.assertEqual(r.activeSite, s)

    def testActiveSitesMultiple(self):
        '''Test an object having multiple activeSites.
        '''
        a = Stream()
        b = Stream()
        n = note.Note("G#")
        n.offset = 10
        a.insert(n)
        b.insert(n)
        # the objects elements has been transfered to each activeSite
        # stream in the same way
        self.assertEqual(n.getOffsetBySite(a), n.getOffsetBySite(b))
        self.assertEqual(n.getOffsetBySite(a), 10)



    def testExtractedNoteAssignLyric(self):
        from music21 import converter, corpus, text
        a = converter.parse(corpus.getWork('opus74no1', 3))
        b = a[1] 
        c = b.flat
        for thisNote in c.getElementsByClass(note.Note):
            thisNote.lyric = thisNote.name
        textStr = text.assembleLyrics(b)
        self.assertEqual(textStr.startswith('C D E A F E'), 
                         True)



    def testGetInstrumentFromMxl(self):
        '''Test getting an instrument from an mxl file
        '''
        from music21 import corpus, converter, instrument

        # manually set activeSite to associate 
        a = converter.parse(corpus.getWork(['haydn', 'opus74no2', 
                                            'movement4.xml']))

#         b = a[3][10:20]
#         # TODO: manually setting the activeSite is still necessary
#         b.activeSite = a[3] # manually set the activeSite

        b = a.parts[3]
        # by calling the .part property, we create a new stream; thus, the
        # activeSite of b is no longer a
        self.assertEqual(b.activeSite, None)
        instObj = b.getInstrument()
        self.assertEqual(instObj.partName, 'Cello')

        p = a[3] # get part
        # a mesausre within this part has as its activeSite the part
        self.assertEqual(p[10].activeSite, a[3])
        instObj = p.getInstrument()
        self.assertEqual(instObj.partName, 'Cello')

        instObj = p[10].getInstrument()
        self.assertEqual(instObj.partName, 'Cello')




    def testGetInstrumentManual(self):
        from music21 import corpus, converter


        #import pdb; pdb.set_trace()
        # search activeSite from a measure within

        # a different test derived from a TestExternal
        q = Stream()
        r = Stream()
        for x in ['c3','a3','c#4','d3'] * 15:
            n = note.Note(x)
            n.quarterLength = random.choice([.25])
            q.append(n)
            m = note.Note(x)
            m.quarterLength = .5
            r.append(m)
        s = Stream() # container

        s.insert(q)
        s.insert(r)

        instObj = q.getInstrument()
        self.assertEqual(instObj.partName, defaults.partName)

        instObj = r.getInstrument()
        self.assertEqual(instObj.partName, defaults.partName)

        instObj = s.getInstrument()
        self.assertEqual(instObj.partName, defaults.partName)

        # test mx generation of parts
        mx = q.mx
        mx = r.mx

        # test mx generation of score
        mx = s.mx

    def testMeasureAndTieCreation(self):
        '''A test of the automatic partitioning of notes in a measure and the creation of ties.
        '''

        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.repeatInsert(n, range(0,120,3))        
        a.insert( 0, meter.TimeSignature("5/4")  )
        a.insert(10, meter.TimeSignature("2/4")  )
        a.insert( 3, meter.TimeSignature("3/16") )
        a.insert(20, meter.TimeSignature("9/8")  )
        a.insert(40, meter.TimeSignature("10/4") )

        mx = a.mx

    def testStreamCopy(self):
        '''Test copying a stream
        '''
        from music21 import corpus, converter


        #import pdb; pdb.set_trace()
        # search activeSite from a measure within

        # a different test derived from a TestExternal
        q = Stream()
        r = Stream()
        for x in ['c3','a3','c#4','d3'] * 30:
            n = note.Note(x)
            n.quarterLength = random.choice([.25])
            q.append(n)
            m = note.Note(x)
            m.quarterLength = .5
            r.append(m)
        s = Stream() # container

        s.insert(q)
        s.insert(r)

        # copying the whole: this works
        w = deepcopy(s)

        post = Stream()
        # copying while looping: this gets increasingly slow
        for aElement in s:
            environLocal.printDebug(['copying and inserting an element',
                                     aElement, len(aElement._definedContexts)])
            bElement = deepcopy(aElement)
            post.insert(aElement.offset, bElement)
            

    def testIteration(self):
        '''This test was designed to illustrate a past problem with stream
        Iterations.
        '''
        q = Stream()
        r = Stream()
        for x in ['c3','a3','c#4','d3'] * 5:
            n = note.Note(x)
            n.quarterLength = random.choice([.25])
            q.append(n)
            m = note.Note(x)
            m.quarterLength = .5
            r.append(m)
        src = Stream() # container
        src.insert(q)
        src.insert(r)

        a = Stream()

        for obj in src.getElementsByClass(Stream):
            a.insert(obj)

        environLocal.printDebug(['expected length', len(a)])
        counter = 0
        for x in a:
            if counter >= 4:
                environLocal.printDebug(['infinite loop', counter])
                break
            environLocal.printDebug([x])
            junk = x.getInstrument(searchActiveSite=True)
            del junk
            counter += 1


    def testGetTimeSignatures(self):
        #getTimeSignatures

        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.autoSort = False
        a.insert( 0, meter.TimeSignature("5/4")  )
        a.insert(10, meter.TimeSignature("2/4")  )
        a.insert( 3, meter.TimeSignature("3/16") )
        a.insert(20, meter.TimeSignature("9/8")  )
        a.insert(40, meter.TimeSignature("10/4") )

        offsets = [x.offset for x in a]
        self.assertEqual(offsets, [0.0, 10.0, 3.0, 20.0, 40.0])

        # fill with notes
        a.repeatInsert(n, range(0,120,3))        

        b = a.getTimeSignatures(sortByCreationTime=False)

        self.assertEqual(len(b), 5)
        self.assertEqual(b[0].numerator, 5)
        self.assertEqual(b[4].numerator, 10)

        self.assertEqual(b[4].activeSite, b)

        # none of the offsets are being copied 
        offsets = [x.offset for x in b]
        # with autoSort is passed on from elements search
        #self.assertEqual(offsets, [0.0, 3.0, 10.0, 20.0, 40.0])
        self.assertEqual(offsets, [0.0, 10.0, 3.0, 20.0, 40.0])


  
    def testElements(self):
        '''Test basic Elements wrapping non music21 objects
        '''
        a = Stream()
        a.insert(50, music21.Music21Object())
        self.assertEqual(len(a), 1)

        # there are two locations, default and the one just added
        self.assertEqual(len(a[0]._definedContexts), 2)
        # this works
#        self.assertEqual(a[0]._definedContexts.getOffsetByIndex(-1), 50.0)

#        self.assertEqual(a[0]._definedContexts.getSiteByIndex(-1), a)
        self.assertEqual(a[0].getOffsetBySite(a), 50.0)
        self.assertEqual(a[0].offset, 50.0)

    def testClefs(self):
        s = Stream()
        for x in ['c3','a3','c#4','d3'] * 5:
            n = note.Note(x)
            s.append(n)
        clefObj = s.bestClef()
        self.assertEqual(clefObj.sign, 'F')
        measureStream = s.makeMeasures()
        clefObj = measureStream[0].clef
        self.assertEqual(clefObj.sign, 'F')

    def testFindConsecutiveNotes(self):
        s = Stream()
        n1 = note.Note("c3")
        n1.quarterLength = 1
        n2 = chord.Chord(["c4", "e4", "g4"])
        n2.quarterLength = 4
        s.insert(0, n1)
        s.insert(1, n2)
        l1 = s.findConsecutiveNotes()
        self.assertTrue(l1[0] is n1)
        self.assertTrue(l1[1] is n2)
        l2 = s.findConsecutiveNotes(skipChords = True)
        self.assertTrue(len(l2) == 1)
        self.assertTrue(l2[0] is n1)
        
        r1 = note.Rest()
        s2 = Stream()
        s2.insert([0.0, n1,
                   1.0, r1, 
                   2.0, n2])
        l3 = s2.findConsecutiveNotes()
        self.assertTrue(l3[1] is None)
        l4 = s2.findConsecutiveNotes(skipRests = True)
        self.assertTrue(len(l4) == 2)
        s3 = Stream()
        s3.insert([0.0, n1,
                   1.0, r1,
                   10.0, n2])
        l5 = s3.findConsecutiveNotes(skipRests = False)
        self.assertTrue(len(l5) == 3)  # not 4 because two Nones allowed in a row!
        l6 = s3.findConsecutiveNotes(skipRests = True, skipGaps = True)
        self.assertTrue(len(l6) == 2)
        
        n1.quarterLength = 10
        n3 = note.Note("B-")
        s4 = Stream()
        s4.insert([0.0, n1,
                   1.0, n2,
                   10.0, n3])
        l7 = s4.findConsecutiveNotes()
        self.assertTrue(len(l7) == 2) # n2 is hidden because it is in an overlap
        l8 = s4.findConsecutiveNotes(getOverlaps = True)
        self.assertTrue(len(l8) == 3)
        self.assertTrue(l8[1] is n2)
        l9 = s4.findConsecutiveNotes(getOverlaps = True, skipChords = True)
        self.assertTrue(len(l9) == 3)
        self.assertTrue(l9[1] is None)
        
        n4 = note.Note("A#")
        n1.quarterLength = 1
        n2.quarterLength = 1
        
        s5 = Stream()
        s5.insert([0.0, n1,
                   1.0, n2,
                   2.0, n3,
                   3.0, n4])
        l10 = s5.findConsecutiveNotes()
        self.assertTrue(len(l10) == 4)
        l11 = s5.findConsecutiveNotes(skipUnisons = True)
        self.assertTrue(len(l11) == 3)
        
        self.assertTrue(l11[2] is n3)


        n5 = note.Note("c4")
        s6 = Stream()
        s6.insert([0.0, n1,
                   1.0, n5,
                   2.0, n2])
        l12 = s6.findConsecutiveNotes(noNone = True)
        self.assertTrue(len(l12) == 3)
        l13 = s6.findConsecutiveNotes(noNone = True, skipUnisons = True)
        self.assertTrue(len(l13) == 3)
        l14 = s6.findConsecutiveNotes(noNone = True, skipOctaves = True)
        self.assertTrue(len(l14) == 2)
        self.assertTrue(l14[0] is n1)
        self.assertTrue(l14[1] is n2)


    def testMelodicIntervals(self):
        c4 = note.Note("C4")
        c4.offset = 10
        d5 = note.Note("D5")
        d5.offset = 11
        s1 = Stream([c4, d5])
        intS1 = s1.melodicIntervals()
        self.assertTrue(len(intS1) == 1)
        M9 = intS1[0]
        self.assertEqual(M9.niceName, "Major Ninth") 
        ## TODO: Many more tests
        

    def testStripTiesBuilt(self):
        s1 = Stream()
        n1 = note.Note()
        n1.quarterLength = 6
        s1.append(n1)
        self.assertEqual(len(s1.notes), 1)

        s1 = s1.makeMeasures()
        s1 = s1.makeTies() # makes ties but no end tie positions!
        # flat version has 2 notes
        self.assertEqual(len(s1.flat.notes), 2)

        sUntied = s1.stripTies()
        self.assertEqual(len(sUntied), 1)
        self.assertEqual(sUntied[0].quarterLength, 6)

        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.repeatInsert(n, range(0,120,3))

        self.assertEqual(len(a), 40)
        
        a.insert( 0, meter.TimeSignature("5/4")  )
        a.insert(10, meter.TimeSignature("2/4")  )
        a.insert( 3, meter.TimeSignature("3/16") )
        a.insert(20, meter.TimeSignature("9/8")  )
        a.insert(40, meter.TimeSignature("10/4") )

        b = a.makeMeasures()
        b = b.makeTies()
        
        # we now have 65 notes, as ties have been created
        self.assertEqual(len(b.flat.notes), 65)

        c = b.stripTies() # gets flat, removes measures
        self.assertEqual(len(c.notes), 40)


    def testStripTiesImported(self):
        from music21 import corpus, converter
        from music21.musicxml import testPrimitive

        a = converter.parse(testPrimitive.multiMeasureTies)

        p1 = a.parts[0]
        self.assertEqual(len(p1.flat.notes), 16)
        p1.stripTies(inPlace=True, retainContainers=True)
        self.assertEqual(len(p1.flat.notes), 6)

        p2 = a.parts[1]
        self.assertEqual(len(p2.flat.notes), 16)
        p2Stripped = p2.stripTies(inPlace=False, retainContainers=True)
        self.assertEqual(len(p2Stripped.flat.notes), 5)
        # original part should not be changed
        self.assertEqual(len(p2.flat.notes), 16)

        p3 = a.parts[2]
        self.assertEqual(len(p3.flat.notes), 16)
        p3.stripTies(inPlace=True, retainContainers=True)
        self.assertEqual(len(p3.flat.notes), 3)

        p4 = a.parts[3]
        self.assertEqual(len(p4.flat.notes), 16)
        p4Notes = p4.stripTies(retainContainers=False)
        # original should be unchanged
        self.assertEqual(len(p4.flat.notes), 16)
        # lesser notes
        self.assertEqual(len(p4Notes), 10)
    

    def testStripTiesScore(self):
        '''Test stripTies using the Score method
        '''

        from music21 import corpus, converter
        from music21.musicxml import testPrimitive
        import music21

        s = converter.parse(testPrimitive.multiMeasureTies)
        self.assertEqual(len(s.parts), 4)

        self.assertEqual(len(s.parts[0].flat.notes), 16)
        self.assertEqual(len(s.parts[1].flat.notes), 16)
        self.assertEqual(len(s.parts[2].flat.notes), 16)
        self.assertEqual(len(s.parts[3].flat.notes), 16)

        # first, in place false
        sPost = s.stripTies(inPlace=False)

        self.assertEqual(len(sPost.parts[0].flat.notes), 6)
        self.assertEqual(len(sPost.parts[1].flat.notes), 5)
        self.assertEqual(len(sPost.parts[2].flat.notes), 3)
        self.assertEqual(len(sPost.parts[3].flat.notes), 10)

        # make sure original is unchchanged
        self.assertEqual(len(s.parts[0].flat.notes), 16)
        self.assertEqual(len(s.parts[1].flat.notes), 16)
        self.assertEqual(len(s.parts[2].flat.notes), 16)
        self.assertEqual(len(s.parts[3].flat.notes), 16)

        # second, in place true
        sPost = s.stripTies(inPlace=True)
        self.assertEqual(len(s.parts[0].flat.notes), 6)
        self.assertEqual(len(s.parts[1].flat.notes), 5)
        self.assertEqual(len(s.parts[2].flat.notes), 3)
        self.assertEqual(len(s.parts[3].flat.notes), 10)

        # just two ties here
        s = corpus.parseWork('bach/bwv66.6')
        self.assertEqual(len(s.parts), 4)

        self.assertEqual(len(s.parts[0].flat.notes), 37)
        self.assertEqual(len(s.parts[1].flat.notes), 42)
        self.assertEqual(len(s.parts[2].flat.notes), 45)
        self.assertEqual(len(s.parts[3].flat.notes), 41)

        # perform strip ties in place
        s.stripTies(inPlace=True)

        self.assertEqual(len(s.parts[0].flat.notes), 36)
        self.assertEqual(len(s.parts[1].flat.notes), 42)
        self.assertEqual(len(s.parts[2].flat.notes), 44)
        self.assertEqual(len(s.parts[3].flat.notes), 41)



    def testTwoStreamMethods(self):
        from music21.note import Note
    
        (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
        (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
        n11.step = "C"
        n12.step = "D"
        n13.step = "E"
        n14.step = "F"
        n21.step = "G"
        n22.step = "A"
        n23.step = "B"
        n24.step = "C"
        n24.octave = 5
        
        n11.duration.type = "half"
        n12.duration.type = "whole"
        n13.duration.type = "eighth"
        n14.duration.type = "half"
        
        n21.duration.type = "half"
        n22.duration.type = "eighth"
        n23.duration.type = "whole"
        n24.duration.type = "eighth"
        
        stream1 = Stream()
        stream1.append([n11,n12,n13,n14])
        stream2 = Stream()
        stream2.append([n21,n22,n23,n24])
    
        attackedTogether = stream1.simultaneousAttacks(stream2) 
        self.assertEqual(len(attackedTogether), 3)  # nx1, nx2, nx4
        thisNote = stream2.getElementsByOffset(attackedTogether[1])[0]
        self.assertTrue(thisNote is n22)
        
        playingWhenAttacked = stream1.playingWhenAttacked(n23)
        self.assertTrue(playingWhenAttacked is n12)

        allPlayingWhileSounding = stream2.allPlayingWhileSounding(n14)
        self.assertEqual(len(allPlayingWhileSounding), 1)
        self.assertTrue(allPlayingWhileSounding[0] is n24)

    #    trimPlayingWhileSounding = \
    #         stream2.trimPlayingWhileSounding(n12)
    #    assert trimPlayingWhileSounding[0] == n22
    #    assert trimPlayingWhileSounding[1].duration.quarterLength == 3.5



    def testMeasureRange(self):
        from music21 import corpus
        a = corpus.parseWork('bach/bwv324.xml')
        b = a[3].measures(4,6)
        self.assertEqual(len(b), 3) 
        #b.show('t')
        # first measure now has keu sig
        self.assertEqual(len(b[0].getElementsByClass(key.KeySignature)), 1) 
        # first measure now has meter
        self.assertEqual(len(b[0].getElementsByClass(meter.TimeSignature)), 1) 
        # first measure now has clef
        self.assertEqual(len(b[0].getElementsByClass(clef.Clef)), 1) 

        #b.show()       
        # get first part
        p1 = a.parts[0]
        # get measure by class; this will not manipulate the measure
        mExRaw = p1.getElementsByClass('Measure')[5]
        self.assertEqual(str([n for n in mExRaw.notes]), '[<music21.note.Note B>, <music21.note.Note D>]')
        self.assertEqual(len(mExRaw.flat), 3)

        # get measure by using method; this will add elements
        mEx = p1.measure(6)
        self.assertEqual(str([n for n in mEx.notes]), '[<music21.note.Note B>, <music21.note.Note D>]')
        self.assertEqual(len(mEx.flat), 7)
        
        # make sure source has not chnaged
        mExRaw = p1.getElementsByClass('Measure')[5]
        self.assertEqual(str([n for n in mExRaw.notes]), '[<music21.note.Note B>, <music21.note.Note D>]')
        self.assertEqual(len(mExRaw.flat), 3)


        # test measures with no measure numbesr
        c = Stream()
        for i in range(4):
            m = Measure()
            n = note.Note()
            m.repeatAppend(n, 4)
            c.append(m)
        #c.show()
        d = c.measures(2,3)
        self.assertEqual(len(d), 2) 
        #d.show()

        # try the score method
        a = corpus.parseWork('bach/bwv324.xml')
        b = a.measures(2,4)
        self.assertEqual(len(b[0].flat.getElementsByClass(clef.Clef)), 1) 
        self.assertEqual(len(b[1].flat.getElementsByClass(clef.Clef)), 1) 
        self.assertEqual(len(b[2].flat.getElementsByClass(clef.Clef)), 1) 
        self.assertEqual(len(b[3].flat.getElementsByClass(clef.Clef)), 1) 

        self.assertEqual(len(b[0].flat.getElementsByClass(key.KeySignature)), 1) 
        self.assertEqual(len(b[1].flat.getElementsByClass(key.KeySignature)), 1) 
        self.assertEqual(len(b[2].flat.getElementsByClass(key.KeySignature)), 1) 
        self.assertEqual(len(b[3].flat.getElementsByClass(key.KeySignature)), 1) 

        #b.show()


    def testMeasureOffsetMap(self):
        from music21 import corpus
        a = corpus.parseWork('bach/bwv324.xml')

        mOffsetMap = a[0].measureOffsetMap()

        self.assertEqual(sorted(mOffsetMap.keys()), 
            [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 34.0, 38.0]  )

        # try on a complete score
        a = corpus.parseWork('bach/bwv324.xml')
        mOffsetMap = a.measureOffsetMap()
        #environLocal.printDebug([mOffsetMap])
        self.assertEqual(sorted(mOffsetMap.keys()), 
            [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 34.0, 38.0]  )

        for key, value in mOffsetMap.items():
            # each key contains 4 measures, one for each part
            self.assertEqual(len(value), 4)

        # we can get this information from Notes too!
        a = corpus.parseWork('bach/bwv324.xml')
        # get notes from one measure

        mOffsetMap = a[0].flat.measureOffsetMap(note.Note)
        self.assertEqual(sorted(mOffsetMap.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 34.0, 38.0]   )

        self.assertEqual(str(mOffsetMap[0.0]), '[<music21.stream.Measure 1 offset=0.0>]')

        self.assertEqual(str(mOffsetMap[4.0]), '[<music21.stream.Measure 2 offset=4.0>]')


        # TODO: getting inconsistent results with these
        # instead of storing a time value for locations, use an index 
        # count

        m1 = a[0].getElementsByClass('Measure')[1]
        mOffsetMap = m1.measureOffsetMap(note.Note)
        # offset here is that of measure that originally contained this note
        environLocal.printDebug(['m1', m1, 'mOffsetMap', mOffsetMap])
        self.assertEqual(sorted(mOffsetMap.keys()), [4.0] )

        m2 = a[0].getElementsByClass('Measure')[2]
        mOffsetMap = m2.measureOffsetMap(note.Note)
        # offset here is that of measure that originally contained this note
        self.assertEqual(sorted(mOffsetMap.keys()), [8.0] )


        # this should work but does not yet
        # it seems that the flat score does not work as the flat part
#         mOffsetMap = a.flat.measureOffsetMap('Note')
#         self.assertEqual(sorted(mOffsetMap.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0]  )



    def testMeasureOffsetMapPostTie(self):
        from music21 import corpus, stream
        
        a = corpus.parseWork('bach/bwv4.8.xml')
        # alto line syncopated/tied notes accross bars
        alto = a[1]
        self.assertEqual(len(alto.flat.notes), 73)
        
        # offset map for measures looking at the part's Measures
        # note that pickup bar is taken into account
        post = alto.measureOffsetMap()
        self.assertEqual(sorted(post.keys()), [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0, 37.0, 41.0, 45.0, 49.0, 53.0, 57.0, 61.0] )
        
        # looking at Measure and Notes: no problem
        post = alto.flat.measureOffsetMap([Measure, note.Note])
        self.assertEqual(sorted(post.keys()), [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0, 37.0, 41.0, 45.0, 49.0, 53.0, 57.0, 61.0] )
        
        
        # after stripping ties, we have a stream with fewer notes
        altoPostTie = a[1].stripTies()
        # we can get the length of this directly b/c we just of a stream of 
        # notes, no Measures
        self.assertEqual(len(altoPostTie.notes), 69)
        
        # we can still get measure numbers:
        mNo = altoPostTie[3].getContextByClass(stream.Measure).number
        self.assertEqual(mNo, 1)
        mNo = altoPostTie[8].getContextByClass(stream.Measure).number
        self.assertEqual(mNo, 2)
        mNo = altoPostTie[15].getContextByClass(stream.Measure).number
        self.assertEqual(mNo, 4)
        
        # can we get an offset Measure map by looking for measures
        post = altoPostTie.measureOffsetMap(stream.Measure)
        # nothing: no Measures:
        self.assertEqual(post.keys(), [])
        
        # but, we can get an offset Measure map by looking at Notes
        post = altoPostTie.measureOffsetMap(note.Note)
        # nothing: no Measures:
        self.assertEqual(sorted(post.keys()), [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0, 37.0, 41.0, 45.0, 49.0, 53.0, 57.0, 61.0])

        #from music21 import graph
        #graph.plotStream(altoPostTie, 'scatter', values=['pitchclass','offset'])


    def testMusicXMLGenerationViaPropertyA(self):
        '''Test output tests above just by calling the musicxml attribute
        '''
        a = ['c', 'g#', 'd-', 'f#', 'e', 'f' ] * 4

        s = Stream()
        partOffsetShift = 1.25
        partOffset = 7.5
        p = Stream()
        for pitchName in a:
            n = note.Note(pitchName)
            n.quarterLength = 1.5
            p.append(n)
        p.offset = partOffset

        p.transferOffsetToElements()

        junk = p.getTimeSignatures(searchContext=True, sortByCreationTime=True)
        p.makeRests(refStreamOrTimeRange=[0, 100], 
            inPlace=True)

        self.assertEqual(p.lowestOffset, 0)
        self.assertEqual(p.highestTime, 100.0)
        post = p.musicxml


        # can only recreate problem in the context of two Streams
        s = Stream()
        partOffsetShift = 1.25
        partOffset = 7.5
        for x in range(2):
            p = Stream()
            for pitchName in a:
                n = note.Note(pitchName)
                n.quarterLength = 1.5
                p.append(n)
            p.offset = partOffset
            s.insert(p)
            partOffset += partOffsetShift

        #s.show()
        post = s.musicxml


    def testMusicXMLGenerationViaPropertyB(self):
        '''Test output tests above just by calling the musicxml attribute
        '''
        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.repeatInsert(n, range(0,120,3))
        #a.show() # default time signature used
        a.insert( 0, meter.TimeSignature("5/4")  )
        a.insert(10, meter.TimeSignature("2/4")  )
        a.insert( 3, meter.TimeSignature("3/16") )
        a.insert(20, meter.TimeSignature("9/8")  )
        a.insert(40, meter.TimeSignature("10/4") )
        post = a.musicxml


    def testMusicXMLGenerationViaPropertyC(self):
        '''Test output tests above just by calling the musicxml attribute
        '''
        a = ['c', 'g#', 'd-', 'f#', 'e', 'f' ] * 4

        s = Stream()
        partOffsetShift = 1.25
        partOffset = 0
        for part in range(6):  
            p = Stream()
            for pitchName in a:
                n = note.Note(pitchName)
                n.quarterLength = 1.5
                p.append(n)
            p.offset = partOffset
            s.insert(p)
            partOffset += partOffsetShift
        #s.show()
        post = s.musicxml



    def testContextNestedA(self):
        '''Testing getting clefs from higher-level streams
        '''
        from music21 import note, clef

        s1 = Stream()
        s2 = Stream()
        n1 = note.Note()
        c1 = clef.AltoClef()

        s1.append(n1) # this is the model of a stream with a single part
        s2.append(s1)
        s2.insert(0, c1)


        # from the lower level stream, we should be able to get to the 
        # higher level clef
        post = s1.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        # we can also use getClefs to get this from s1 or s2
        post = s1.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        post = s2.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        environLocal.printDebug(['_definedContexts.get() of s1', s1._definedContexts.get()])


        # attempting to move the substream into a new stream
        s3 = Stream()
        s3.insert(s1) # insert at same offset as s2
        
        # we cannot get the alto clef from s3; this makes sense
        post = s3.getClefs()[0]
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        # s1 has both stream as contexts
        self.assertEqual(s1.hasContext(s3), True)
        self.assertEqual(s1.hasContext(s2), True)

        # but if we search s1, shuold not it find an alto clef?
        post = s1.getClefs()
        #environLocal.printDebug(['should not be treble clef:', post])
        self.assertEqual(isinstance(post[0], clef.AltoClef), True)


        # this all woroks fine
        sMeasures = s2.makeMeasures()
        self.assertEqual(len(sMeasures), 1)
        self.assertEqual(len(sMeasures.getElementsByClass('Measure')), 1) # one measure
        self.assertEqual(len(sMeasures[0]), 3) 
        # first is sig
        self.assertEqual(str(sMeasures[0][0]), '4/4') 
        # second is clef
        self.assertEqual(isinstance(sMeasures[0][1], clef.AltoClef), True)
        #environLocal.printDebug(['here', sMeasures[0][2]])
        #sMeasures.show('t')
        # the third element is a Note; we get it from flattening during
        # makeMeasures
        self.assertEqual(isinstance(sMeasures[0][2], note.Note), True)

        # this shows the proper outpt withs the proper clef.
        #sMeasures.show()

        # we cannot get clefs from sMeasures b/c that is the topmost
        # stream container; there are no clefs here, only at a lower leve
        post = sMeasures.getElementsByClass(clef.Clef)
        self.assertEqual(len(post), 0)


    def testContextNestedB(self):
        '''Testing getting clefs from higher-level streams
        '''
        from music21 import note, clef
        
        s1 = Stream()
        s2 = Stream()
        n1 = note.Note()
        c1 = clef.AltoClef()
        
        s1.append(n1) # this is the model of a stream with a single part
        s2.append(s1)
        s2.insert(0, c1)
        
        # this works fine
        post = s1.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        # if we flatten s1, we cannot still get the clef: why?
        s1Flat = s1.flat
        # but it has s2 has a context
        self.assertEqual(s1Flat.hasContext(s2), True)
        #environLocal.printDebug(['_definedContexts.get() of s1Flat', s1Flat._definedContexts.get()])
        #environLocal.printDebug(['_definedContexts._definedContexts of s1Flat', s1Flat._definedContexts._definedContexts])


        self.assertEqual(s1Flat.hasContext(s2), True)

        # this returns the proper dictionary entry
        #environLocal.printDebug(
        #    ['s1Flat._definedContexts._definedContexts[id(s1)', s1Flat._definedContexts._definedContexts[id(s2)]])
        # we can extract out the same refernce
        s2Out = s1Flat._definedContexts.getById(id(s2))

        # this works
        post = s1Flat.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        # this will only work if the callerFirst is manually set to s1Flat
        # otherwise, this interprets the DefinedContext object as the first 
        # caller
        post = s1Flat._definedContexts.getByClass(clef.Clef, callerFirst=s1Flat)
        self.assertEqual(isinstance(post, clef.AltoClef), True)



    def testContextNestedC(self):
        '''Testing getting clefs from higher-level streams
        '''
        from music21 import note, clef
        
        s1 = Stream()
        s1.id = 's1'
        s2 = Stream()
        s2.id = 's2'
        n1 = note.Note()
        c1 = clef.AltoClef()
        
        s1.append(n1) # this is the model of a stream with a single part
        s2.append(s1)
        s2.insert(0, c1)
        
        # this works fine
        post = s1.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        # this is a key tool of the serial reverse search
        post = s2.getElementAtOrBefore(0, [clef.Clef])
        self.assertEqual(isinstance(post, clef.AltoClef), True)


        # this is a key tool of the serial reverse search
        post = s2.flat.getElementAtOrBefore(0, [clef.Clef])
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        # s1 is in s2; but s1.flat is not in s2!
        self.assertEqual(s2.getOffsetByElement(s1), 0.0)
        self.assertEqual(s2.getOffsetByElement(s1.flat), None)


        # this does not work; the clef is in s2; its not in a context of s2
        post = s2.getContextByClass(clef.Clef)
        self.assertEqual(post, None)

        # we can find the clef from the flat version of 21
        post = s1.flat.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)


    def testContextNestedD(self):
        '''Testing getting clefs from higher-level streams
        '''

        from music21 import clef, note
        n1 = note.Note()
        n2 = note.Note()

        s1 = Stream()
        s2 = Stream()
        s3 = Stream()
        s1.append(n1)
        s2.append(n2)
        s3.insert(0, s1)
        s3.insert(0, s2)
        
        self.assertEqual(s1.activeSite, s3)

        s3.insert(0, clef.AltoClef())
        # both output parts have alto clefs
        #s3.show()

        # get clef form higher level stream; only option
        self.assertEqual(s1.activeSite, s3)
        post = s1.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)
        # TODO: isolated activeSite mangling problem here
        #self.assertEqual(s1.activeSite, s3)

        post = s2.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)
        

        # now we in sert a clef in s2; s2 will get this clef first
        s2.insert(0, clef.TenorClef())
        # only second part should ahve tenor clef
        post = s2.getClefs()[0]
        self.assertEqual(isinstance(post, clef.TenorClef), True)

        # but stream s1 should get the alto clef still
        post = s1.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        # but s2 flat
        post = s2.flat.getClefs()[0]
        self.assertEqual(isinstance(post, clef.TenorClef), True)

        s2FlatCopy = copy.deepcopy(s2.flat)
        post = s2FlatCopy.getClefs()[0]
        self.assertEqual(isinstance(post, clef.TenorClef), True)


        # but s1 flat
        post = s1.flat.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        s1FlatCopy = copy.deepcopy(s1.flat)
        post = s1FlatCopy.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        environLocal.printDebug(['s1.activeSite', s1.activeSite])
        s1Measures = s1.makeMeasures()
        self.assertEqual(isinstance(s1Measures[0].clef, clef.AltoClef), True)

        s2Measures = s2.makeMeasures()
        self.assertEqual(isinstance(s2Measures[0].clef, clef.TenorClef), True)


        # try making a deep copy of s3

        s3copy = copy.deepcopy(s3)
        #s1Measures = s3copy[0].makeMeasures()
        s1Measures = s3copy.getElementsByClass('Stream')[0].makeMeasures()
        self.assertEqual(isinstance(s1Measures[0].clef, clef.AltoClef), True)
        #s1Measures.show() # these show the proper clefs

        s2Measures = s3copy.getElementsByClass('Stream')[1].makeMeasures()
        self.assertEqual(isinstance(s2Measures[0].clef, clef.TenorClef), True)
        #s2Measures.show() # this shows the proper clef

        #TODO: this still retruns tenor cleff for both parts
        # need to examine

        # now we in sert a clef in s2; s2 will get this clef first
        s1.insert(0, clef.BassClef())
        post = s1.getClefs()[0]
        self.assertEqual(isinstance(post, clef.BassClef), True)


        #s3.show()

    def testMakeRests(self):

        from music21 import note
        a = ['c', 'g#', 'd-', 'f#', 'e', 'f' ] * 4


        partOffsetShift = 1.25
        partOffset = 2  # start at non zero
        for part in range(6):  
            p = Stream()
            for pitchName in a:
                n = note.Note(pitchName)
                n.quarterLength = 1.5
                p.append(n)
            p.offset = partOffset

            self.assertEqual(p.lowestOffset, 0)

            p.transferOffsetToElements()
            self.assertEqual(p.lowestOffset, partOffset)

            p.makeRests()

            #environLocal.printDebug(['first element', p[0], p[0].duration])
            # by default, initial rest should be made
            sub = p.getElementsByClass(note.Rest)
            self.assertEqual(len(sub), 1)

            self.assertEqual(sub.duration.quarterLength, partOffset)

            # first element should have offset of first dur
            self.assertEqual(p[1].offset, sub.duration.quarterLength)

            partOffset += partOffsetShift

            


    def testMakeMeasuresMeterStream(self):
        '''Testing making measures of various sizes with a supplied single element meter stream. This illustrates an approach to partitioning elements by various sized windows. 
        '''
        from music21 import meter, corpus
        sBach = corpus.parseWork('bach/bwv324.xml')
        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('2/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 21)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('1/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 42)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('3/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 14)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('12/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 4)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('48/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 1)

    def testRemove(self):
        '''Test removing components from a Stream.
        '''
        s = Stream()
        n1 = note.Note('g')
        n2 = note.Note('g#')
        n3 = note.Note('a')

        s.insert(0, n1)
        s.insert(10, n3)
        s.insert(5, n2)

        self.assertEqual(len(s), 3)

        self.assertEqual(n1.activeSite, s)
        s.remove(n1)
        self.assertEqual(len(s), 2)
        # activeSite is Now sent to None
        self.assertEqual(n1.activeSite, None)


    def testReplace(self):
        '''Test replacing components from a Stream.
        '''
        s = Stream()
        n1 = note.Note('g')
        n2 = note.Note('g#')
        n3 = note.Note('a')
        n4 = note.Note('c')

        s.insert(0, n1)
        s.insert(5, n2)

        self.assertEqual(len(s), 2)

        s.replace(n1, n3)
        self.assertEqual([s[0], s[1]], [n3, n2])

        s.replace(n2, n4)
        self.assertEqual([s[0], s[1]], [n3, n4])

        s.replace(n4, n1)
        self.assertEqual([s[0], s[1]], [n3, n1])


        from music21 import corpus
        sBach = corpus.parseWork('bach/bwv324.xml')
        partSoprano = sBach[0]

        c1 = partSoprano.flat.getElementsByClass(clef.Clef)[0]
        self.assertEqual(isinstance(c1, clef.TrebleClef), True)

        # now, replace with a different clef
        c2 = clef.AltoClef()
        partSoprano.flat.replace(c1, c2)

        # all views of the Stream have been updated
        cTest = sBach[0].flat.getElementsByClass(clef.Clef)[0]
        self.assertEqual(isinstance(cTest, clef.AltoClef), True)

        s1 = Stream()
        s1.insert(10, n1)
        s2 = Stream()
        s2.insert(20, n1)
        s3 = Stream()
        s3.insert(30, n1)
        
        s1.replace(n1, n2)
        self.assertEqual(s1[0], n2)
        self.assertEqual(s1[0].getOffsetBySite(s1), 10)
        
        self.assertEqual(s2[0], n2)
        self.assertEqual(s2[0].getOffsetBySite(s2), 20)
        
        self.assertEqual(s3[0], n2)
        self.assertEqual(s3[0].getOffsetBySite(s3), 30)



    def testDoubleStreamPlacement(self):
        from music21 import note
        n1 = note.Note()
        s1 = Stream()
        s1.insert(n1)

        environLocal.printDebug(['n1.siteIds after one insertion', n1, n1.getSites(), n1.getSiteIds()])


        s2 = Stream()
        s2.insert(s1)

        environLocal.printDebug(['n1.siteIds after container insertion', n1, n1.getSites(), n1.getSiteIds()])

        s2Flat = s2.flat

        #environLocal.printDebug(['s1', s1, id(s1)])    
        #environLocal.printDebug(['s2', s2, id(s2)])    
        #environLocal.printDebug(['s2flat', s2Flat, id(s2Flat)])

        #environLocal.printDebug(['n1.siteIds', n1, n1.getSites(), n1.getSiteIds()])

        # previously, one of these raised an error
        s3 = copy.deepcopy(s2Flat)
        s3 = copy.deepcopy(s2.flat)
        s3Measures = s3.makeMeasures()


    def testBestTimeSignature(self):
        '''Get a time signature based on components in a measure.
        '''
        from music21 import note
        m = Measure()
        for ql in [2,3,2]:
            n = note.Note()
            n.quarterLength = ql
            m.append(n)
        ts = m.bestTimeSignature()
        self.assertEqual(ts.numerator, 7)
        self.assertEqual(ts.denominator, 4)

        m = Measure()
        for ql in [1.5, 1.5]:
            n = note.Note()
            n.quarterLength = ql
            m.append(n)
        ts = m.bestTimeSignature()
        self.assertEqual(ts.numerator, 6)
        self.assertEqual(ts.denominator, 8)

        m = Measure()
        for ql in [.25, 1.5]:
            n = note.Note()
            n.quarterLength = ql
            m.append(n)
        ts = m.bestTimeSignature()
        self.assertEqual(ts.numerator, 7)
        self.assertEqual(ts.denominator, 16)



    def testGetKeySignatures(self):
        '''Searching contexts for key signatures
        '''
        s = Stream()
        ks1 = key.KeySignature(3)        
        ks2 = key.KeySignature(-3)        
        s.append(ks1)
        s.append(ks2)
        post = s.getKeySignatures()
        self.assertEqual(post[0], ks1)
        self.assertEqual(post[1], ks2)


        # try creating a key signature in one of two measures
        # try to get last active key signature
        ks1 = key.KeySignature(3)        
        m1 = Measure()
        n1 = note.Note()
        n1.quarterLength = 4
        m1.append(n1)
        m1.keySignature = ks1 # assign to measure via property

        m2 = Measure()
        n2 = note.Note()
        n2.quarterLength = 4
        m2.append(n2)

        s = Stream()
        s.append(m1)
        s.append(m2)

        # can get from measure
        post = m1.getKeySignatures()
        self.assertEqual(post[0], ks1)

        # we can get from the Stream by flattening
        post = s.flat.getKeySignatures()
        self.assertEqual(post[0], ks1)

        # we can get the key signature in m1 from m2
        post = m2.getKeySignatures()
        self.assertEqual(post[0], ks1)



    def testGetKeySignaturesThreeMeasures(self):
        '''Searching contexts for key signatures
        '''

        ks1 = key.KeySignature(3)        
        ks2 = key.KeySignature(-3)        
        ks3 = key.KeySignature(5)        

        m1 = Measure()
        n1 = note.Note()
        n1.quarterLength = 4
        m1.append(n1)
        m1.keySignature = ks1 # assign to measure via property

        m2 = Measure()
        n2 = note.Note()
        n2.quarterLength = 4
        m2.append(n2)

        m3 = Measure()
        n3 = note.Note()
        n3.quarterLength = 4
        m3.append(n3)
        m3.keySignature = ks3 # assign to measure via property

        s = Stream()
        s.append(m1)
        s.append(m2)
        s.append(m3)

        # can get from measure
        post = m1.getKeySignatures()
        self.assertEqual(post[0], ks1)

        # we can get the key signature in m1 from m2
        post = m2.getKeySignatures()
        self.assertEqual(post[0], ks1)

        # if we search m3, we get the key signature in m3
        post = m3.getKeySignatures()
        self.assertEqual(post[0], ks3)




    def testMakeAccidentals(self):
        '''Test accidental display setting
        '''
        s = Stream()
        n1 = note.Note('a#')
        n2 = note.Note('a4')
        r1 = note.Rest()
        c1 = chord.Chord(['a#2', 'a4', 'a5'])
        n3 = note.Note('a4')
        s.append(n1)
        s.append(r1)
        s.append(n2)
        s.append(c1)
        s.append(n3)
        s.makeAccidentals()

        self.assertEqual(n2.accidental.displayStatus, True)
        # both a's in the chord now have naturals but are hidden
        self.assertEqual(c1.pitches[1].accidental, None)
        #self.assertEqual(c1.pitches[2].accidental.displayStatus, True)

        # not getting a natural here because of chord tones
        #self.assertEqual(n3.accidental.displayStatus, True)
        #self.assertEqual(n3.accidental, None)
        #s.show()

        s = Stream()
        n1 = note.Note('a#')
        n2 = note.Note('a')
        r1 = note.Rest()
        c1 = chord.Chord(['a#2', 'a4', 'a5'])
        s.append(n1)
        s.append(r1)
        s.append(n2)
        s.append(c1)
        s.makeAccidentals(cautionaryPitchClass=False)

        # a's in the chord do not have naturals
        self.assertEqual(c1.pitches[1].accidental, None)
        self.assertEqual(c1.pitches[2].accidental, None)



    def testMakeAccidentalsWithKeysInMeasures(self):
        scale1 = ['c4', 'd4', 'e4', 'f4', 'g4', 'a4', 'b4', 'c5']
        scale2 = ['c', 'd', 'e-', 'f', 'g', 'a-', 'b-', 'c5']
        scale3 = ['c#', 'd#', 'e#', 'f#', 'g#', 'a#', 'b#', 'c#5']
    
        s = Stream()
        for scale in [scale1, scale2, scale3]:
            for ks in [key.KeySignature(0), key.KeySignature(2),
                key.KeySignature(4), key.KeySignature(7), key.KeySignature(-1),
                key.KeySignature(-3)]:
    
                m = Measure()
                m.timeSignature = meter.TimeSignature('4/4')
                m.keySignature = ks
                for p in scale*2:
                    n = note.Note(p)
                    n.quarterLength = .25
                    n.addLyric(n.pitch.name)
                    m.append(n)
                m.makeBeams(inPlace=True)
                m.makeAccidentals(inPlace=True)
                s.append(m)
        # TODO: add tests
        #s.show()




    def testScaleOffsetsBasic(self):
        '''
        '''
        from music21 import note, stream

        def procCompare(s, scalar, match):
            oListSrc = [e.offset for e in s]
            oListSrc.sort()
            sNew = s.scaleOffsets(scalar, inPlace=False)
            oListPost = [e.offset for e in sNew]
            oListPost.sort()

            #environLocal.printDebug(['scaleOffsets', oListSrc, '\npost scaled by:', scalar, oListPost])
            self.assertEqual(oListPost[:len(match)], match)

        # test equally spaced half notes starting at zero
        n = note.Note()
        n.quarterLength = 2
        s = stream.Stream()
        s.repeatAppend(n, 10)

        # provide start of resulting values
        # half not spacing becomes whole note spacing
        procCompare(s, 2, [0.0, 4.0, 8.0])
        procCompare(s, 4, [0.0, 8.0, 16.0, 24.0])
        procCompare(s, 3, [0.0, 6.0, 12.0, 18.0])
        procCompare(s, .5, [0.0, 1.0, 2.0, 3.0])
        procCompare(s, .25, [0.0, 0.5, 1.0, 1.5])

        # test equally spaced quarter notes start at non-zero
        n = note.Note()
        n.quarterLength = 1
        s = stream.Stream()
        s.repeatInsert(n, range(100, 110))

        procCompare(s, 1, [100, 101, 102, 103])
        procCompare(s, 2, [100, 102, 104, 106])
        procCompare(s, 4, [100, 104, 108, 112])
        procCompare(s, 1.5, [100, 101.5, 103.0, 104.5])
        procCompare(s, .5, [100, 100.5, 101.0, 101.5])
        procCompare(s, .25, [100, 100.25, 100.5, 100.75])

        # test non equally spaced notes starting at zero
        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 1
        s.repeatInsert(n, range(0, 30, 3))
        n2 = note.Note()
        n2.quarterLength = 2
        s.repeatInsert(n, range(1, 30, 3))
        # procCompare will  sort offsets; this test non sorted operation
        procCompare(s, 1, [0.0, 1.0, 3.0, 4.0, 6.0, 7.0])
        procCompare(s, .5, [0.0, 0.5, 1.5, 2.0, 3.0, 3.5])
        procCompare(s, 2, [0.0, 2.0, 6.0, 8.0, 12.0, 14.0])

        # test non equally spaced notes starting at non-zero
        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 1
        s.repeatInsert(n, range(100, 130, 3))
        n2 = note.Note()
        n2.quarterLength = 2
        s.repeatInsert(n, range(101, 130, 3))
        # procCompare will  sort offsets; this test non sorted operation
        procCompare(s, 1, [100.0, 101.0, 103.0, 104.0, 106.0, 107.0])
        procCompare(s, .5, [100.0, 100.5, 101.5, 102.0, 103.0, 103.5])
        procCompare(s, 2, [100.0, 102.0, 106.0, 108.0, 112.0, 114.0])
        procCompare(s, 6, [100.0, 106.0, 118.0, 124.0, 136.0, 142.0])



    def testScaleOffsetsBasicInPlaceA(self):
        '''
        '''
        from music21 import note, stream

        def procCompare(s, scalar, match):
            # test equally spaced half notes starting at zero
            n = note.Note()
            n.quarterLength = 2
            s = stream.Stream()
            s.repeatAppend(n, 10)

            oListSrc = [e.offset for e in s]
            oListSrc.sort()
            s.scaleOffsets(scalar, inPlace=True)
            oListPost = [e.offset for e in s]
            oListPost.sort()
            #environLocal.printDebug(['scaleOffsets', oListSrc, '\npost scaled by:', scalar, oListPost])
            self.assertEqual(oListPost[:len(match)], match)

        s = None # placeholder
        # provide start of resulting values
        # half not spacing becomes whole note spacing
        procCompare(s, 2, [0.0, 4.0, 8.0])
        procCompare(s, 4, [0.0, 8.0, 16.0, 24.0])
        procCompare(s, 3, [0.0, 6.0, 12.0, 18.0])
        procCompare(s, .5, [0.0, 1.0, 2.0, 3.0])
        procCompare(s, .25, [0.0, 0.5, 1.0, 1.5])


    def testScaleOffsetsBasicInPlaceB(self):
        '''
        '''
        from music21 import note, stream

        def procCompare(s, scalar, match):
            # test equally spaced quarter notes start at non-zero
            n = note.Note()
            n.quarterLength = 1
            s = stream.Stream()
            s.repeatInsert(n, range(100, 110))

            oListSrc = [e.offset for e in s]
            oListSrc.sort()
            s.scaleOffsets(scalar, inPlace=True)
            oListPost = [e.offset for e in s]
            oListPost.sort()
            #environLocal.printDebug(['scaleOffsets', oListSrc, '\npost scaled by:', scalar, oListPost])
            self.assertEqual(oListPost[:len(match)], match)

        s = None # placeholder
        procCompare(s, 1, [100, 101, 102, 103])
        procCompare(s, 2, [100, 102, 104, 106])
        procCompare(s, 4, [100, 104, 108, 112])
        procCompare(s, 1.5, [100, 101.5, 103.0, 104.5])
        procCompare(s, .5, [100, 100.5, 101.0, 101.5])
        procCompare(s, .25, [100, 100.25, 100.5, 100.75])


    def testScaleOffsetsBasicInPlaceC(self):
        '''
        '''
        from music21 import note, stream

        def procCompare(s, scalar, match):
            # test non equally spaced notes starting at zero
            s = stream.Stream()
            n1 = note.Note()
            n1.quarterLength = 1
            s.repeatInsert(n1, range(0, 30, 3))
            n2 = note.Note()
            n2.quarterLength = 2
            s.repeatInsert(n2, range(1, 30, 3))

            oListSrc = [e.offset for e in s]
            oListSrc.sort()
            s.scaleOffsets(scalar, inPlace=True)
            oListPost = [e.offset for e in s]
            oListPost.sort()
            #environLocal.printDebug(['scaleOffsets', oListSrc, '\npost scaled by:', scalar, oListPost])
            self.assertEqual(oListPost[:len(match)], match)

        # procCompare will  sort offsets; this test non sorted operation
        s = None # placeholder
        procCompare(s, 1, [0.0, 1.0, 3.0, 4.0, 6.0, 7.0])
        procCompare(s, .5, [0.0, 0.5, 1.5, 2.0, 3.0, 3.5])
        procCompare(s, 2, [0.0, 2.0, 6.0, 8.0, 12.0, 14.0])



    def testScaleOffsetsBasicInPlaceD(self):
        '''
        '''
        from music21 import note, stream

        def procCompare(s, scalar, match):
            # test non equally spaced notes starting at non-zero
            s = stream.Stream()
            n1 = note.Note()
            n1.quarterLength = 1
            s.repeatInsert(n1, range(100, 130, 3))
            n2 = note.Note()
            n2.quarterLength = 2
            s.repeatInsert(n2, range(101, 130, 3))

            oListSrc = [e.offset for e in s]
            oListSrc.sort()
            s.scaleOffsets(scalar, inPlace=True)
            oListPost = [e.offset for e in s]
            oListPost.sort()
            #environLocal.printDebug(['scaleOffsets', oListSrc, '\npost scaled by:', scalar, oListPost])
            self.assertEqual(oListPost[:len(match)], match)

        # procCompare will  sort offsets; this test non sorted operation
        s = None # placeholder
        procCompare(s, 1, [100.0, 101.0, 103.0, 104.0, 106.0, 107.0])
        procCompare(s, .5, [100.0, 100.5, 101.5, 102.0, 103.0, 103.5])
        procCompare(s, 2, [100.0, 102.0, 106.0, 108.0, 112.0, 114.0])
        procCompare(s, 6, [100.0, 106.0, 118.0, 124.0, 136.0, 142.0])




    def testScaleOffsetsNested(self):
        '''
        '''
        from music21 import note, stream


        def offsetMap(s): # lists of offsets, with lists of lists
            post = []
            for e in s:
                sub = []
                sub.append(e.offset)
                if hasattr(e, 'elements'):
                    sub.append(offsetMap(e))
                post.append(sub)
            return post
            

        def procCompare(s, scalar, anchorZeroRecurse, match):
            oListSrc = offsetMap(s)
            oListSrc.sort()
            sNew = s.scaleOffsets(scalar, anchorZeroRecurse=anchorZeroRecurse, 
                                  inPlace=False)
            oListPost = offsetMap(sNew)
            oListPost.sort()

            #environLocal.printDebug(['scaleOffsets', oListSrc, '\npost scaled by:', scalar, oListPost])
            self.assertEqual(oListPost[:len(match)], match)


        # test equally spaced half notes starting at zero
        n1 = note.Note()
        n1.quarterLength = 2
        s1 = stream.Stream()
        s1.repeatAppend(n1, 4)

        n2 = note.Note()
        n2.quarterLength = .5
        s2 = stream.Stream()
        s2.repeatAppend(n2, 4)
        s1.append(s2)

        # offset map gives us a nested list presentation of all offsets
        # usefulfor testing
        self.assertEquals(offsetMap(s1),
        [[0.0], [2.0], [4.0], [6.0], [8.0, [[0.0], [0.5], [1.0], [1.5]]]])

        # provide start of resulting values
        # half not spacing becomes whole note spacing
        procCompare(s1, 2, 'lowest', 
        [[0.0], [4.0], [8.0], [12.0], [16.0, [[0.0], [1.0], [2.0], [3.0]]]]
        )
        procCompare(s1, 4, 'lowest', 
        [[0.0], [8.0], [16.0], [24.0], [32.0, [[0.0], [2.0], [4.0], [6.0]]]] 
        )
        procCompare(s1, .25, 'lowest', 
        [[0.0], [0.5], [1.0], [1.5], [2.0, [[0.0], [0.125], [0.25], [0.375]]]]
        )

        # test unequally spaced notes starting at non-zero
        n1 = note.Note()
        n1.quarterLength = 1
        s1 = stream.Stream()
        s1.repeatInsert(n1, [10,14,15,17])

        n2 = note.Note()
        n2.quarterLength = .5
        s2 = stream.Stream()
        s2.repeatInsert(n2, [40,40.5,41,41.5])
        s1.append(s2)
        s1.append(copy.deepcopy(s2))
        s1.append(copy.deepcopy(s2))

        # note that, with these nested streams, 
        # the first value of an embeded stream stays in the same 
        # position relative to that stream. 

        # it might be necessary, in this case, to scale the start
        # time of the first elemen
        # that is, it should have no shift

        # provide anchorZeroRecurse value
        self.assertEquals(offsetMap(s1),
        [[10.0], [14.0], [15.0], [17.0], 
            [18.0, [[40.0], [40.5], [41.0], [41.5]]], 
            [60.0, [[40.0], [40.5], [41.0], [41.5]]], 
            [102.0, [[40.0], [40.5], [41.0], [41.5]]]]
        )

        procCompare(s1, 2, 'lowest', 
        [[10.0], [18.0], [20.0], [24.0], 
            [26.0, [[40.0], [41.0], [42.0], [43.0]]], 
            [110.0, [[40.0], [41.0], [42.0], [43.0]]], 
            [194.0, [[40.0], [41.0], [42.0], [43.0]]]]
        )

        # if anchorZeroRecurse is None, embedded stream that do not
        # start at zero are scaled proportionally
        procCompare(s1, 2, None, 
        [[10.0], [18.0], [20.0], [24.0], 
            [26.0, [[80.0], [81.0], [82.0], [83.0]]], 
            [110.0, [[80.0], [81.0], [82.0], [83.0]]], 
            [194.0, [[80.0], [81.0], [82.0], [83.0]]]] 
        )

        procCompare(s1, .25, 'lowest', 
        [[10.0], [11.0], [11.25], [11.75], 
            [12.0, [[40.0], [40.125], [40.25], [40.375]]], 
            [22.5, [[40.0], [40.125], [40.25], [40.375]]], 
            [33.0, [[40.0], [40.125], [40.25], [40.375]]]] 
        )

        # if anchorZeroRecurse is None, embedded stream that do not
        # start at zero are scaled proportionally
        procCompare(s1, .25, None, 
        [[10.0], [11.0], [11.25], [11.75], 
            [12.0, [[10.0], [10.125], [10.25], [10.375]]], 
            [22.5, [[10.0], [10.125], [10.25], [10.375]]], 
            [33.0, [[10.0], [10.125], [10.25], [10.375]]]] 
        )


    def testScaleDurationsBasic(self):
        '''Scale some durations, independent of offsets. 
        '''
        import note

        def procCompare(s, scalar, match):
            oListSrc = [e.quarterLength for e in s]
            sNew = s.scaleDurations(scalar, inPlace=False)
            oListPost = [e.quarterLength for e in sNew]
            self.assertEqual(oListPost[:len(match)], match)

        n1 = note.Note()
        n1.quarterLength = .5
        s1 = Stream()
        s1.repeatInsert(n1, range(6))

        # test inPlace v/ not inPlace
        sNew = s1.scaleDurations(2, inPlace=False)
        self.assertEqual([e.duration.quarterLength for e in s1], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        self.assertEqual([e.duration.quarterLength for e in sNew], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        # basic test
        procCompare(s1, .5, [0.25, 0.25, 0.25])
        procCompare(s1, 3, [1.5, 1.5, 1.5])

        # a sequence of Durations of different values
        s1 = Stream()
        for ql in [.5, 1.5, 2, 3, .25, .25, .5]:
            n = note.Note('g')
            n.quarterLength = ql
            s1.append(n)

        procCompare(s1, .5, [0.25, 0.75, 1.0, 1.5, 0.125, 0.125, 0.25] )
        procCompare(s1, .25, [0.125, 0.375, 0.5, 0.75, 0.0625, 0.0625, 0.125] )
        procCompare(s1, 4, [2.0, 6.0, 8, 12, 1.0, 1.0, 2.0])
         



    def testAugmentOrDiminishBasic(self):

        def procCompare(s, scalar, matchOffset, matchDuration):
            oListSrc = [e.offset for e in s]
            qlListSrc = [e.quarterLength for e in s]

            sNew = s.augmentOrDiminish(scalar, inPlace=False)
            oListPost = [e.offset for e in sNew]
            qlListPost = [e.quarterLength for e in sNew]

            self.assertEqual(oListPost[:len(matchOffset)], matchOffset)
            self.assertEqual(qlListPost[:len(matchDuration)], matchDuration)

            # test that the last offset is the highest offset
            self.assertEqual(matchOffset[-1], sNew.highestOffset)
            self.assertEqual(matchOffset[-1]+matchDuration[-1], 
                sNew.highestTime)


            # test making measures on this 
            post = sNew.makeMeasures()
            #sNew.show()

        # a sequence of Durations of different values
        s1 = Stream()
        for ql in [.5, 1.5, 2, 3, .25, .25, .5]:
            n = note.Note('g')
            n.quarterLength = ql
            s1.append(n)

        # provide offsets, then durations
        procCompare(s1, .5, 
            [0.0, 0.25, 1.0, 2.0, 3.5, 3.625, 3.75] ,
            [0.25, 0.75, 1.0, 1.5, 0.125, 0.125, 0.25] )

        procCompare(s1, 1.5, 
            [0.0, 0.75, 3.0, 6.0, 10.5, 10.875, 11.25]  ,
            [0.75, 2.25, 3.0, 4.5, 0.375, 0.375, 0.75] )

        procCompare(s1, 3, 
            [0.0, 1.5, 6.0, 12.0, 21.0, 21.75, 22.5]  ,
            [1.5, 4.5, 6, 9, 0.75, 0.75, 1.5]  )




    def testAugmentOrDiminishHighestTimes(self):
        '''Need to make sure that highest offset and time are properly updated
        '''
        from music21 import corpus
        src = corpus.parseWork('bach/bwv324.xml')
        # get some measures of the soprano; just get the notes
        ex = src[0].flat.notes[0:30]

        self.assertEqual(ex.highestOffset, 38.0)
        self.assertEqual(ex.highestTime, 42.0)

        # try first when doing this not in place
        newEx = ex.augmentOrDiminish(2, inPlace=False)
        self.assertEqual(newEx.notes[0].offset, 0.0)
        self.assertEqual(newEx.notes[1].offset, 4.0)

        self.assertEqual(newEx.highestOffset, 76.0)
        self.assertEqual(newEx.highestTime, 84.0)

        # try in place
        ex.augmentOrDiminish(2, inPlace=True)
        self.assertEqual(ex.notes[1].getOffsetBySite(ex), 4.0)
        self.assertEqual(ex.notes[1].offset, 4.0)

        self.assertEqual(ex.highestOffset, 76.0)
        self.assertEqual(ex.highestTime, 84.0)

        

    def testAugmentOrDiminishCorpus(self):
        '''Extract phrases from the corpus and use for testing 
        '''
        from music21 import corpus

        # first method: iterating through notes
        src = corpus.parseWork('bach/bwv324.xml')
        # get some measures of the soprano; just get the notes
        #environLocal.printDebug(['testAugmentOrDiminishCorpus()', 'extracting notes:'])
        ex = src[0].flat.notes[0:30]
        # attach a couple of transformations
        s = Stream()
        for scalar in [.5, 1.5, 2, .25]:
            #n = note.Note()
            part = Part()
            environLocal.printDebug(['testAugmentOrDiminishCorpus()', 'pre augment or diminish', 'ex', ex, 'id(ex)', id(ex)])
            for n in ex.augmentOrDiminish(scalar, inPlace=False):
                part.append(n)
            s.insert(0, part)
        junkTest = s._getMX()
        #s.show()
    
        # second method: getting flattened stream
        src = corpus.parseWork('bach/bwv323.xml')
        # get notes from one part
        ex = src[0].flat.notes
        s = Score()
        for scalar in [1, 2, .5, 1.5]:
            part = ex.augmentOrDiminish(scalar, inPlace=False)
            s.insert(0, part)
        
        junkTest = s._getMX()
        #s.show()


    def testMeasureBarDurationProportion(self):
        
        from music21 import meter, stream, note

        m = stream.Measure()
        m.timeSignature = meter.TimeSignature('3/4')
        n = note.Note()
        n.quarterLength = 1
        m.append(copy.deepcopy(n))

        self.assertEqual(m.notes[0].offset, 0)
        self.assertAlmostEqual(m.barDurationProportion(), .333333, 4)
        self.assertAlmostEqual(m.barDuration.quarterLength, 3, 4)

# temporarily commented out
#         m.shiftElementsAsAnacrusis()
#         self.assertEqual(m.notes[0].hasContext(m), True)
#         self.assertEqual(m.notes[0].offset, 2.0)
#         # now the duration is full
#         self.assertAlmostEqual(m.barDurationProportion(), 1.0, 4)
#         self.assertAlmostEqual(m.highestOffset, 2.0, 4)


        m = stream.Measure()
        m.timeSignature = meter.TimeSignature('5/4')
        n1 = note.Note()
        n1.quarterLength = .5
        n2 = note.Note()
        n2.quarterLength = 1.5
        m.append(n1)
        m.append(n2)

        self.assertAlmostEqual(m.barDurationProportion(), .4, 4)
        self.assertEqual(m.barDuration.quarterLength, 5.0)

#         m.shiftElementsAsAnacrusis()
#         self.assertEqual(m.notes[0].offset, 3.0)
#         self.assertEqual(n1.offset, 3.0)
#         self.assertEqual(n2.offset, 3.5)
#         self.assertAlmostEqual(m.barDurationProportion(), 1.0, 4)


    def testInsertAndShiftBasic(self):
        import random
        from music21 import note
        offsets = [0, 2, 4, 6, 8, 10, 12]
        n = note.Note()
        n.quarterLength = 2
        s = Stream()
        s.repeatInsert(n, offsets)
        # qL, insertOffset, newHighOffset, newHighTime
        data = [
                 (.25, 0, 12.25, 14.25),
                 (3, 0, 15, 17),
                 (6.5, 0, 18.5, 20.5),
                 # shifting at a positing where another element starts
                 (.25, 4, 12.25, 14.25),
                 (3, 4, 15, 17),
                 (6.5, 4, 18.5, 20.5),
                 # shift the same duration at different insert points
                 (1, 2, 13, 15),
                 (2, 2, 14, 16),
                 # this is overlapping element at 2 by 1, ending at 4
                 # results in no change in new high values
                 (1, 3, 12, 14), 
                 # since duration is here 2, extend new starts to 5
                 (2, 3, 13, 15), 
                 (1, 4, 13, 15),
                 (2, 4, 14, 16),
                 # here, we do not shift the element at 4, only event at 6
                 (2, 4.5, 12.5, 14.5),
                 # here, we insert the start of an element and can shift it
                 (2.5, 4, 14.5, 16.5),
            ]
        for qL, insertOffset, newHighOffset, newHighTime in data:
            sProc = copy.deepcopy(s)        
            self.assertEqual(sProc.highestOffset, 12)
            self.assertEqual(sProc.highestTime, 14)
            nAlter = note.Note()
            nAlter.quarterLength = qL
            sProc.insertAndShift(insertOffset, nAlter)
            sProc.elements = sProc.sorted.elements
            self.assertEqual(sProc.highestOffset, newHighOffset)
            self.assertEqual(sProc.highestTime, newHighTime)
            self.assertEqual(len(sProc), len(s)+1)

            # try the same with scrambled elements
            sProc = copy.deepcopy(s)        
            random.shuffle(sProc._elements)
            sProc._elementsChanged()

            self.assertEqual(sProc.highestOffset, 12)
            self.assertEqual(sProc.highestTime, 14)
            nAlter = note.Note()
            nAlter.quarterLength = qL
            sProc.insertAndShift(insertOffset, nAlter)
            sProc.elements = sProc.sorted.elements
            self.assertEqual(sProc.highestOffset, newHighOffset)
            self.assertEqual(sProc.highestTime, newHighTime)
            self.assertEqual(len(sProc), len(s)+1)


    def testInsertAndShiftNoDuration(self):
        import random
        from music21 import note
        offsets = [0, 2, 4, 6, 8, 10, 12]
        n = note.Note()
        n.quarterLength = 2
        s = Stream()
        s.repeatInsert(n, offsets)
        # qL, insertOffset, newHighOffset, newHighTime
        data = [
                 (.25, 0, 12, 14),
                 (3, 0, 12, 14),
                 (6.5, 0, 12, 14),
                 (.25, 4, 12, 14),
                 (3, 4, 12, 14),
                 (6.5, 4, 12, 14),
                 (1, 2, 12, 14),
                 (2, 2, 12, 14),
                 (1, 3, 12, 14), 
            ]
        for qL, insertOffset, newHighOffset, newHighTime in data:
            sProc = copy.deepcopy(s)        
            self.assertEqual(sProc.highestOffset, 12)
            self.assertEqual(sProc.highestTime, 14)

            c = clef.Clef()
            sProc.insertAndShift(insertOffset, c)
            #sProc.elements = sProc.sorted.elements
            self.assertEqual(sProc.highestOffset, newHighOffset)
            self.assertEqual(sProc.highestTime, newHighTime)
            self.assertEqual(len(sProc), len(s)+1)



    def testInsertAndShiftMultipleElements(self):
        import random
        from music21 import note
        offsets = [0, 2, 4, 6, 8, 10, 12]
        n = note.Note()
        n.quarterLength = 2
        s = Stream()
        s.repeatInsert(n, offsets)
        # qL, insertOffset, newHighOffset, newHighTime
        data = [
                 (.25, 0, 12.25, 14.25),
                 (3, 0, 15, 17),
                 (6.5, 0, 18.5, 20.5),
                 # shifting at a positing where another element starts
                 (.25, 4, 12.25, 14.25),
                 (3, 4, 15, 17),
                 (6.5, 4, 18.5, 20.5),
                 # shift the same duration at different insert points
                 (1, 2, 13, 15),
                 (2, 2, 14, 16),
                 # this is overlapping element at 2 by 1, ending at 4
                 # results in no change in new high values
                 (1, 3, 12, 14), 
                 # since duration is here 2, extend new starts to 5
                 (2, 3, 13, 15), 
                 (1, 4, 13, 15),
                 (2, 4, 14, 16),
                 # here, we do not shift the element at 4, only event at 6
                 (2, 4.5, 12.5, 14.5),
                 # here, we insert the start of an element and can shift it
                 (2.5, 4, 14.5, 16.5),
            ]
        for qL, insertOffset, newHighOffset, newHighTime in data:
            sProc = copy.deepcopy(s)        
            self.assertEqual(sProc.highestOffset, 12)
            self.assertEqual(sProc.highestTime, 14)

            # fill with sixteenth notes
            nAlter = note.Note()
            nAlter.quarterLength = .25
            itemList = []
            o = insertOffset
            while o < insertOffset + qL:
                itemList.append(o)
                itemList.append(copy.deepcopy(nAlter))
                o += .25
            #environLocal.printDebug(['itemList', itemList])            

            sProc.insertAndShift(itemList)
            sProc.elements = sProc.sorted.elements
            self.assertEqual(sProc.highestOffset, newHighOffset)
            self.assertEqual(sProc.highestTime, newHighTime)
            self.assertEqual(len(sProc), len(s)+len(itemList) / 2)


    def testMetadataOnStream(self):
        from music21 import note
        s = Stream()
        n1 = note.Note()
        s.append(n1)

        s.metadata = metadata.Metadata()
        s.metadata.composer = 'Frank the Composer'
        s.metadata.title = 'work title' # will get as movement name if not set
        #s.metadata.movementName = 'movement name'
        post = s.musicxml
        #s.show()


    def testMeasureBarline(self):

        from music21 import meter
        
        m1 = Measure()
        m1.timeSignature = meter.TimeSignature('3/4')
        self.assertEqual(len(m1), 1)

        b1 = bar.Barline('heavy')
        # this adds to elements list
        m1.leftBarline = b1
        self.assertEqual(len(m1), 2)
        self.assertEqual(m1[1], b1) # this is on elements
        self.assertEqual(m1.rightBarline, None) # this is on elements

        b2 = bar.Barline('heavy')
        self.assertEqual(m1.barDuration.quarterLength, 3.0)
        m1.rightBarline = b2


        # now have barline, ts, and barline
        self.assertEqual(len(m1), 3)
        b3 = bar.Barline('double')
        b4 = bar.Barline('heavy')

        m1.leftBarline = b3
        # length should be the same, as we replaced
        self.assertEqual(len(m1), 3)
        self.assertEqual(m1.leftBarline, b3)

        m1.rightBarline = b4
        self.assertEqual(len(m1), 3)
        self.assertEqual(m1.rightBarline, b4)

        p = Part()
        p.append(copy.deepcopy(m1))
        p.append(copy.deepcopy(m1))

        #p.show()

        # add right barline first, w/o a time signature
        m2 = Measure()
        self.assertEqual(len(m2), 0)
        m2.rightBarline = b4
        self.assertEqual(len(m2), 1)
        self.assertEqual(m2.leftBarline, None) # this is on elements
        self.assertEqual(m2.rightBarline, b4) # this is on elements



    def testMeasureLayout(self):
        # test both system layout and measure width


        # Note: Measure.layoutWidth is not currently read by musicxml
        from music21 import note, layout
    
        s = Stream()
        for i in range(1,10):
            n = note.Note()
            m = Measure()
            m.append(n)
            m.layoutWidth = i*100
            if i % 2 == 0:
                sl = layout.SystemLayout(isNew=True)
                m.insert(0, sl)
            s.append(m)

        #s.show()
        post = s.musicxml


    def testYieldContainers(self):
        from music21 import stream, note
        
        n1 = note.Note()
        n1.id = 'n(1a)'
        n2 = note.Note()
        n2.id = 'n2(2b)'
        n3 = note.Note()
        n3.id = 'n3(3b)'
        n4 = note.Note()
        n4.id = 'n4(3b)'

        s1 = stream.Stream()
        s1.id = '1a'
        s1.append(n1)

        s2 = stream.Stream()
        s2.id = '2a'
        s3 = stream.Stream()
        s3.id = '2b'
        s3.append(n2)
        s4 = stream.Stream()
        s4.id = '2c'

        s5 = stream.Stream()
        s5.id = '3a'
        s6 = stream.Stream()
        s6.id = '3b'
        s6.append(n3)
        s6.append(n4)
        s7 = stream.Stream()
        s7.id = '3c'
        s8 = stream.Stream()
        s8.id = '3d'
        s9 = stream.Stream()
        s9.id = '3e'
        s10 = stream.Stream()
        s10.id = '3f'

        #environLocal.printDebug(['s1, s2, s3, s4', s1, s2, s3, s4])

        s2.append(s5)
        s2.append(s6)
        s2.append(s7)

        s3.append(s8)
        s3.append(s9)

        s4.append(s10)

        s1.append(s2)
        s1.append(s3)
        s1.append(s4)

        #environLocal.printDebug(['downward:'])

        match = []
        for x in s1._yieldElementsDownward():
            match.append(x.id)
            #environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        self.assertEqual(match, ['1a', '2a', '3a', '3b', '3c', '2b', '3d', '3e', '2c', '3f'])

        #environLocal.printDebug(['downward with elements:'])
        match = []
        for x in s1._yieldElementsDownward(excludeNonContainers=False):
            match.append(x.id)
            #environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        self.assertEqual(match, ['1a', 'n(1a)', '2a', '3a', '3b', 'n3(3b)', 'n4(3b)', '3c', '2b', 'n2(2b)', '3d', '3e', '2c', '3f'])


        #environLocal.printDebug(['downward from non-topmost element:'])
        match = []
        for x in s2._yieldElementsDownward(excludeNonContainers=False):
            match.append(x.id)
            #environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        # test downward
        self.assertEqual(match, ['2a', '3a', '3b', 'n3(3b)', 'n4(3b)', '3c'])

        #environLocal.printDebug(['upward, with skipDuplicates:'])
        match = []
        # must provide empty list for memo
        for x in s7._yieldElementsUpward([], skipDuplicates=True):
            match.append(x.id)
            #environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        self.assertEqual(match, ['3c', '2a', '1a', '2b', '2c', '3a', '3b'] )


        #environLocal.printDebug(['upward from a single node, with skipDuplicates'])
        match = []
        for x in s10._yieldElementsUpward([]):
            match.append(x.id)
            #environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])

        self.assertEqual(match, ['3f', '2c', '1a', '2a', '2b'] )


        #environLocal.printDebug(['upward with skipDuplicates=False:'])
        match = []
        for x in s10._yieldElementsUpward([], skipDuplicates=False):
            match.append(x.id)
            #environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        self.assertEqual(match, ['3f', '2c', '1a', '2a', '1a', '2b', '1a'] )


        #environLocal.printDebug(['upward, with skipDuplicates, excludeNonContainers=False:'])
        match = []
        # must provide empty list for memo
        for x in s8._yieldElementsUpward([], excludeNonContainers=False, 
            skipDuplicates=True):
            match.append(x.id)
            environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        self.assertEqual(match, ['3d', 'n2(2b)', '2b', 'n(1a)', '1a', '2a', '2c', '3e'] )


        #environLocal.printDebug(['upward, with skipDuplicates, excludeNonContainers=False:'])
        match = []
        # must provide empty list for memo
        for x in s4._yieldElementsUpward([], excludeNonContainers=False, 
            skipDuplicates=True):
            match.append(x.id)
            environLocal.printDebug([x, x.id, 'activeSite', x.activeSite])
        # notice that this does not get the nonConatainers for 2b
        self.assertEqual(match, ['2c', 'n(1a)', '1a', '2a', '2b'] )



    def testMidiEventsBuilt(self):

        def procCompare(mf, match):
            triples = []
            for i in range(0, len(mf.tracks[0].events), 2):
                d  = mf.tracks[0].events[i] # delta
                e  = mf.tracks[0].events[i+1] # events
                triples.append((d.time, e.type, e.pitch))
            self.assertEqual(triples, match)
        

        s = Stream()
        n = note.Note('g#3')
        n.quarterLength = .5
        s.repeatAppend(n, 6)
        post = s.midiTracks # get a lost 
        self.assertEqual(len(post[0].events), 28)
        # must be an even number
        self.assertEqual(len(post[0].events) % 2, 0)

        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), (0, 'NOTE_ON', 56), (512, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (512, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (512, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (512, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (512, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (512, 'NOTE_OFF', 56), (0, 'END_OF_TRACK', None)]

        procCompare(mf, match)
        
        s = Stream()
        n = note.Note('g#3')
        n.quarterLength = 1.5
        s.repeatAppend(n, 3)

        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), (0, 'NOTE_ON', 56), (1536, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (1536, 'NOTE_OFF', 56), (0, 'NOTE_ON', 56), (1536, 'NOTE_OFF', 56), (0, 'END_OF_TRACK', None)]
        procCompare(mf, match)

        # combinations of different pitches and durs
        s = Stream()
        data = [('c2', .25), ('c#3', .5), ('g#3', 1.5), ('a#2', 1), ('a4', 2)]
        for p, d in data:
            n = note.Note(p)
            n.quarterLength = d
            s.append(n)

        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), (0, 'NOTE_ON', 36), (256, 'NOTE_OFF', 36), (0, 'NOTE_ON', 49), (512, 'NOTE_OFF', 49), (0, 'NOTE_ON', 56), (1536, 'NOTE_OFF', 56), (0, 'NOTE_ON', 46), (1024, 'NOTE_OFF', 46), (0, 'NOTE_ON', 69), (2048, 'NOTE_OFF', 69), (0, 'END_OF_TRACK', None)] 
        procCompare(mf, match)

        # rests, basic
        #environLocal.printDebug(['rests'])
        s = Stream()
        data = [('c2', 1), (None, .5), ('c#3', 1), (None, .5), ('a#2', 1), (None, .5), ('a4', 1)]
        for p, d in data:
            if p == None:
                n = note.Rest()
            else:
                n = note.Note(p)
            n.quarterLength = d
            s.append(n)
        #s.show('midi')
        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), 
        (0, 'NOTE_ON', 36), (1024, 'NOTE_OFF', 36), 
        (512, 'NOTE_ON', 49), (1024, 'NOTE_OFF', 49), 
        (512, 'NOTE_ON', 46), (1024, 'NOTE_OFF', 46), 
        (512, 'NOTE_ON', 69), (1024, 'NOTE_OFF', 69), 
        (0, 'END_OF_TRACK', None)]
        procCompare(mf, match)


        #environLocal.printDebug(['rests, varied sizes'])
        s = Stream()
        data = [('c2', 1), (None, .25), ('c#3', 1), (None, 1.5), ('a#2', 1), (None, 2), ('a4', 1)]
        for p, d in data:
            if p == None:
                n = note.Rest()
            else:
                n = note.Note(p)
            n.quarterLength = d
            s.append(n)
        #s.show('midi')
        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), 
        (0, 'NOTE_ON', 36), (1024, 'NOTE_OFF', 36), 
        (256, 'NOTE_ON', 49), (1024, 'NOTE_OFF', 49), 
        (1536, 'NOTE_ON', 46), (1024, 'NOTE_OFF', 46), 
        (2048, 'NOTE_ON', 69), (1024, 'NOTE_OFF', 69), 
        (0, 'END_OF_TRACK', None)]
        procCompare(mf, match)

        #environLocal.printDebug(['rests, multiple in a row'])
        s = Stream()
        data = [('c2', 1), (None, 1), (None, 1), ('c#3', 1), ('c#3', 1), (None, .5), (None, .5), (None, .5), (None, .5), ('a#2', 1), (None, 2), ('a4', 1)]
        for p, d in data:
            if p == None:
                n = note.Rest()
            else:
                n = note.Note(p)
            n.quarterLength = d
            s.append(n)
        #s.show('midi')
        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), 
        (0, 'NOTE_ON', 36), (1024, 'NOTE_OFF', 36), 
        (2048, 'NOTE_ON', 49), (1024, 'NOTE_OFF', 49), 
        (0, 'NOTE_ON', 49), (1024, 'NOTE_OFF', 49), 
        (2048, 'NOTE_ON', 46), (1024, 'NOTE_OFF', 46), 
        (2048, 'NOTE_ON', 69), (1024, 'NOTE_OFF', 69), 
        (0, 'END_OF_TRACK', None)]
        procCompare(mf, match)



        #environLocal.printDebug(['w/ chords'])
        s = Stream()
        data = [('c2', 1), (None, 1), (['f3', 'a-4', 'c5'], 1), (None, .5), ('a#2', 1), (None, 2), (['d2', 'a4'], .5), (['d-2', 'a#3', 'g#6'], .5), (None, 1), (['f#3', 'a4', 'c#5'], 4)]
        for p, d in data:
            if p == None:
                n = note.Rest()
            elif isinstance(p, list):
                n = chord.Chord(p)
            else:
                n = note.Note(p)
            n.quarterLength = d
            s.append(n)
        #s.show('midi')
        mf = s.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), 
        (0, 'NOTE_ON', 36), 
        (1024, 'NOTE_OFF', 36), 
        (1024, 'NOTE_ON', 53), (0, 'NOTE_ON', 68), (0, 'NOTE_ON', 72), 
        (1024, 'NOTE_OFF', 53), (0, 'NOTE_OFF', 68), (0, 'NOTE_OFF', 72), 
        (1530, 'NOTE_ON', 46), 
        (1024, 'NOTE_OFF', 46), 
        (2048, 'NOTE_ON', 38), (0, 'NOTE_ON', 69), 
        (512, 'NOTE_OFF', 38), (0, 'NOTE_OFF', 69), 
        (508, 'NOTE_ON', 37), (0, 'NOTE_ON', 58), (0, 'NOTE_ON', 92), 
        (512, 'NOTE_OFF', 37), (0, 'NOTE_OFF', 58), (0, 'NOTE_OFF', 92), 
        (1530, 'NOTE_ON', 54), (0, 'NOTE_ON', 69), (0, 'NOTE_ON', 73), 
        (4096, 'NOTE_OFF', 54), (0, 'NOTE_OFF', 69), (0, 'NOTE_OFF', 73), 
        (0, 'END_OF_TRACK', None)]
        procCompare(mf, match)


    def testMidiEventsImported(self):

        from music21 import corpus

        def procCompare(mf, match):
            triples = []
            for i in range(0, len(mf.tracks[0].events), 2):
                d  = mf.tracks[0].events[i] # delta
                e  = mf.tracks[0].events[i+1] # events
                triples.append((d.time, e.type, e.pitch))
            self.assertEqual(triples, match)
        

        s = corpus.parseWork('bach/bwv66.6')
        part = s.parts[0].measures(6,9) # last meausres
        #part.show('musicxml')
        #part.show('midi')

        mf = part.midiFile
        match = [(0, 'SEQUENCE_TRACK_NAME', None), (0, 'KEY_SIGNATURE', None), (0, 'TIME_SIGNATURE', None), (0, 'NOTE_ON', 69), (1024, 'NOTE_OFF', 69), (0, 'NOTE_ON', 71), (1024, 'NOTE_OFF', 71), (0, 'NOTE_ON', 73), (1024, 'NOTE_OFF', 73), (0, 'NOTE_ON', 69), (1024, 'NOTE_OFF', 69), (0, 'NOTE_ON', 68), (1024, 'NOTE_OFF', 68), (0, 'NOTE_ON', 66), (1024, 'NOTE_OFF', 66), (0, 'NOTE_ON', 68), (2048, 'NOTE_OFF', 68), (0, 'NOTE_ON', 66), (2048, 'NOTE_OFF', 66), (0, 'NOTE_ON', 66), (1024, 'NOTE_OFF', 66), (0, 'NOTE_ON', 66), (2048, 'NOTE_OFF', 66), (0, 'NOTE_ON', 66), (512, 'NOTE_OFF', 66), (0, 'NOTE_ON', 65), (512, 'NOTE_OFF', 65), (0, 'NOTE_ON', 66), (1024, 'NOTE_OFF', 66), (0, 'END_OF_TRACK', None)] 
        procCompare(mf, match)


    def testFindGaps(self):
        from music21 import note
        s = Stream()
        n = note.Note()
        s.repeatInsert(n, [0, 1.5, 2.5, 4, 8])
        post = s.findGaps()
        test = [(e.offset, e.offset+e.duration.quarterLength) for e in post]
        match = [(1.0, 1.5), (3.5, 4.0), (5.0, 8.0)]
        self.assertEqual(test, match)

        self.assertEqual(len(s), 5)
        s.makeRests(fillGaps=True)
        self.assertEqual(len(s), 8)
        self.assertEqual(len(s.getElementsByClass(note.Rest)), 3)


    def testQuantize(self):

        def procCompare(srcOffset, srcDur, dstOffset, dstDur, divList):

            from music21 import note
            s = Stream()
            for i in range(len(srcDur)):
                n = note.Note()
                n.quarterLength = srcDur[i]                
                s.insert(srcOffset[i], n)

            s.quantize(divList, processOffsets=True, processDurations=True)

            targetOffset = [e.offset for e in s]
            targetDur = [e.duration.quarterLength for e in s]
   
            self.assertEqual(targetOffset, dstOffset)
            self.assertEqual(targetDur, dstDur)

            #environLocal.printDebug(['quantization results:', targetOffset, targetDur])


        procCompare([0.01, .24, .57, .78], [0.25, 0.25, 0.25, 0.25], 
                    [0.0, .25, .5, .75], [0.25, 0.25, 0.25, 0.25], 
                    [4]) # snap to .25

        procCompare([0.01, .24, .52, .78], [0.25, 0.25, 0.25, 0.25], 
                    [0.0, .25, .5, .75], [0.25, 0.25, 0.25, 0.25], 
                    [8]) # snap to .125


        procCompare([0.01, .345, .597, 1.02, 1.22], 
                    [0.31, 0.32, 0.33, 0.25, 0.25], 

                    [0.0, 1/3., 2/3., 1.0, 1.25], 
                    [1/3., 1/3., 1/3., 0.25, 0.25], 

                    [4, 3]) # snap to .125 and .3333


        procCompare([0.01, .345, .687, 0.99, 1.28], 
                    [0.31, 0.32, 0.33, 0.22, 0.21], 

                    [0.0, 1/3., 2/3., 1.0, 1.25], 
                    [1/3., 1/3., 1/3., 0.25, 0.25], 

                    [8, 3]) # snap to .125 and .3333


        procCompare([0.03, .335, .677, 1.02, 1.28], 
                    [0.32, 0.35, 0.33, 0.22, 0.21], 

                    [0.0, 1/3., 2/3., 1.0, 1.25], 
                    [1/3., 1/3., 1/3., 0.25, 0.25], 

                    [8, 6]) # snap to .125 and .1666666



    def testAnalyze(self):
        from music21 import stream, corpus, pitch

        s = corpus.parseWork('bach/bwv66.6')

        sub = [s.parts[0], s.parts[1], s.measures(4,5), 
                s.parts[2].measures(4,5)]

        matchAmbitus = [interval.Interval(12), 
                        interval.Interval(15), 
                        interval.Interval(26), 
                        interval.Interval(10)]

        for i in range(len(sub)):
            sTest = sub[i]
            post = sTest.analyze('ambitus')
            self.assertEqual(str(post), str(matchAmbitus[i]))

        # match values for different analysis strings
        for idStr in ['range', 'ambitus', 'span']:
            for i in range(len(sub)):
                sTest = sub[i]
                post = sTest.analyze(idStr)
                self.assertEqual(str(post), str(matchAmbitus[i]))


        # only match first two values
        matchKrumhansl = [(pitch.Pitch('F#'), 'minor'), 
                          (pitch.Pitch('C#'), 'minor'), 
                          (pitch.Pitch('E'), 'major') , 
                          (pitch.Pitch('E'), 'major') ]

        for i in range(len(sub)):
            sTest = sub[i]
            post = sTest.analyze('KrumhanslSchmuckler')
            # returns three values; match 2
            self.assertEqual(post[:2][0].name, matchKrumhansl[i][0].name)
            self.assertEqual(post[:2][1], matchKrumhansl[i][1])

        # match values under different strings provided to analyze
        for idStr in ['key', 'krumhansl', 'keyscape']:
            for i in range(len(sub)):
                sTest = sub[i]
                post = sTest.analyze(idStr)
                # returns three values; match 2
                self.assertEqual(post[:2][0].name, matchKrumhansl[i][0].name)
                self.assertEqual(post[:2][1], matchKrumhansl[i][1])

            

    def testMakeTupletBracketsA(self):
        '''Creating brackets
        '''
        def collectType(s):
            post = []
            for e in s:
                if len(e.duration.tuplets) > 0:
                    post.append(e.duration.tuplets[0].type)
                else:
                    post.append(None)
            return post

        def collectBracket(s):
            post = []
            for e in s:
                if len(e.duration.tuplets) > 0:
                    post.append(e.duration.tuplets[0].bracket)
                else:
                    post.append(None)
            return post

        # case of incomplete, single tuplet ending the Stream
        # remove bracket
        s = Stream()
        qlList = [1, 2, .5, 1/6.]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, None, None, 'startStop'])
        self.assertEqual(collectBracket(s), [None, None, None, False])
        #s.show()


    def testMakeTupletBracketsB(self):
        '''Creating brackets
        '''
        def collectType(s):
            post = []
            for e in s:
                if len(e.duration.tuplets) > 0:
                    post.append(e.duration.tuplets[0].type)
                else:
                    post.append(None)
            return post

        def collectBracket(s):
            post = []
            for e in s:
                if len(e.duration.tuplets) > 0:
                    post.append(e.duration.tuplets[0].bracket)
                else:
                    post.append(None)
            return post

        s = Stream()
        qlList = [1, 1/3., 1/3., 1/3., 1, 1]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, 'start', None, 'stop', None, None])
        #s.show()


        s = Stream()
        qlList = [1, 1/6., 1/6., 1/6., 1/6., 1/6., 1/6., 1, 1]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        # this is the correct type settings but this displays by dividing
        # into two brackets
        self.assertEqual(collectType(s), [None, 'start', None, None, None, None, 'stop', None, None] )
        #s.show()

        # case of tuplet ending the Stream
        s = Stream()
        qlList = [1, 2, .5, 1/6., 1/6., 1/6., ]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, None, None, 'start', None, 'stop'] )
        #s.show()


        # case of incomplete, single tuplets in the middle of a Strem
        s = Stream()
        qlList = [1, 1/3., 1, 1/3., 1, 1/3.]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, 'startStop', None,  'startStop', None,  'startStop'])
        self.assertEqual(collectBracket(s), [None, False, None, False, None, False])
        #s.show()

        # diverse groups that sum to a whole
        s = Stream()
        qlList = [1, 1/3., 2/3., 2/3., 1/6., 1/6., 1]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, 'start', None, None, None, 'stop', None])
        #s.show()


        # diverse groups that sum to a whole
        s = Stream()
        qlList = [1, 1/3., 2/3., 1, 1/12., 1/3., 1/3., 1/12. ]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, 'start', 'stop', None, 'start', None, None, 'stop'] )
        self.assertEqual(collectBracket(s), [None, True, True, None, True, True, True, True])
        #s.show()


        # quintuplets
        s = Stream()
        qlList = [1, 1/5., 1/5., 1/10., 1/10., 1/5., 1/5., 2. ]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        s.makeTupletBrackets()
        self.assertEqual(collectType(s), [None, 'start', None, None, None, None, 'stop', None]  )
        self.assertEqual(collectBracket(s), [None, True, True, True, True, True, True, None] )
        #s.show()




    def testMakeNotation(self):
        '''This is a test of many make procedures
        '''
        def collectTupletType(s):
            post = []
            for e in s:
                if len(e.duration.tuplets) > 0:
                    post.append(e.duration.tuplets[0].type)
                else:
                    post.append(None)
            return post

        def collectTupletBracket(s):
            post = []
            for e in s:
                if len(e.duration.tuplets) > 0:
                    post.append(e.duration.tuplets[0].bracket)
                else:
                    post.append(None)
            return post

#         s = Stream()
#         qlList = [1, 1/3., 1/3., 1/3., 1, 1, 1/3., 1/3., 1/3., 1, 1]
#         for ql in qlList:
#             n = note.Note()
#             n.quarterLength = ql
#             s.append(n)
#         postMake = s.makeNotation()
#         self.assertEqual(collectTupletType(postMake.flat.notes), [None, 'start', None, 'stop', None, None, 'start', None, 'stop', None, None])
#         #s.show()

        s = Stream()
        qlList = [1/3.,]
        for ql in qlList:
            n = note.Note()
            n.quarterLength = ql
            s.append(n)
        postMake = s.makeNotation()
        self.assertEqual(collectTupletType(postMake.flat.notes), ['startStop'])
        self.assertEqual(collectTupletBracket(postMake.flat.notes), [False])

        #s.show()



    def testMakeTies(self):

        from music21 import corpus, meter

        def collectAccidentalDisplayStatus(s):
            post = []
            for e in s.flat.notes:
                if e.pitch.accidental != None:
                    post.append((e.pitch.name, e.pitch.accidental.displayStatus))
                else: # mark as not having an accidental
                    post.append('x')
            return post


        s = corpus.parseWork('bach/bwv66.6')
        # this has accidentals in measures 2 and 6
        sSub = s[3].measures(2,6)
        #sSub.show()
        # only notes that deviate from key signature are True
        self.assertEqual(collectAccidentalDisplayStatus(sSub), ['x', (u'C#', False), 'x', 'x', (u'E#', True), (u'F#', False), 'x', (u'C#', False), (u'F#', False), (u'F#', False), (u'G#', False), (u'F#', False), (u'G#', False), 'x', 'x', 'x', (u'C#', False), (u'F#', False), (u'G#', False), 'x', 'x', 'x', 'x', (u'E#', True), (u'F#', False)] )

        # this removes key signature
        sSub = sSub.flat.notes
        self.assertEqual(len(sSub), 25)

        sSub.insert(0, meter.TimeSignature('3/8'))
        sSub.augmentOrDiminish(2, inPlace=True)

        # explicitly call make measures and make ties
        mStream = sSub.makeMeasures()
        mStream.makeTies(inPlace=True)

        self.assertEqual(len(mStream.flat), 46)

        #mStream.show()

        # this as expected: the only True accidental display status is those
        # that were in the orignal. in Finale display, however, sharps are 
        # displayed when the should not be. 
        self.assertEqual(collectAccidentalDisplayStatus(mStream), ['x', (u'C#', False), (u'C#', False), 'x', 'x', 'x', 'x', (u'E#', True), (u'E#', False), (u'F#', False), 'x', (u'C#', False), (u'C#', False), (u'F#', False), (u'F#', False), (u'F#', False), (u'F#', False), (u'G#', False), (u'G#', False), (u'F#', False), (u'G#', False), 'x', 'x', 'x', 'x', (u'C#', False), (u'C#', False), (u'F#', False), (u'F#', False), (u'G#', False), (u'G#', False), 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', (u'E#', True), (u'E#', False), (u'F#', False), (u'F#', False)]
        )


        # transposing should reset all transposed accidentals
        mStream.flat.transpose('p5', inPlace=True)

        #mStream.show()

        # after transposition all accidentals are reset
        # note: last d# is not showing in Finale, but this seems to be a 
        # finale error, as the musicxml is the same in all D# cases
        self.assertEqual(collectAccidentalDisplayStatus(mStream), ['x', ('G#', None), ('G#', None), 'x', 'x', 'x', 'x', ('B#', None), ('B#', None), ('C#', None), ('F#', None), ('G#', None), ('G#', None), ('C#', None), ('C#', None), ('C#', None), ('C#', None), ('D#', None), ('D#', None), ('C#', None), ('D#', None), 'x', 'x', ('F#', None), ('F#', None), ('G#', None), ('G#', None), ('C#', None), ('C#', None), ('D#', None), ('D#', None), 'x', 'x', 'x', 'x', 'x', 'x', ('F#', None), ('F#', None), ('B#', None), ('B#', None), ('C#', None), ('C#', None)]
        )


    def testMeasuresAndMakeMeasures(self):
        from music21 import converter
        s = converter.parse('g8 e f g e f g a', '2/8')
        sSub = s.measures(3,3)  
        self.assertEqual(str(sSub.pitches), "[E4, F4]")
        #sSub.show()
        


    def testSortAndAutoSort(self):
        from music21 import note
        s = Stream()
        s.autoSort = False

        n1 = note.Note('a')
        n2 = note.Note('b')

        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 has a higher index than n2

        self.assertEqual([x.name for x in s], ['B', 'A'])
        # try getting sorted
        sSorted = s.sorted
        # original unchanged
        self.assertEqual([x.name for x in s], ['B', 'A'])
        # new is chnaged
        self.assertEqual([x.name for x in sSorted], ['A', 'B'])
        # sort in place
        s.sort()
        self.assertEqual([x.name for x in s], ['A', 'B'])


        # test getElements sorting through .notes w/ autoSort
        s = Stream()
        s.autoSort = True
        n1 = note.Note('a')
        n2 = note.Note('b')
        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 (A) has a higher index than n2 (B)
        # if we get .notes, we are getting elements by class, and thus getting 
        # sorted version
        self.assertEqual([x.name for x in s.notes], ['A', 'B'])

        # test getElements sorting through .notes w/o autoSort
        s = Stream()
        s.autoSort = False
        n1 = note.Note('a')
        n2 = note.Note('b')
        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 (A) has a higher index than n2 (B)
        self.assertEqual([x.name for x in s.notes], ['B', 'A'])


        # test __getitem__ calls w/ autoSort
        s = Stream()
        s.autoSort = False
        n1 = note.Note('a')
        n2 = note.Note('b')
        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 (A) has a higher index than n2 (B)
        self.assertEqual(s[0].name, 'B')
        self.assertEqual(s[1].name, 'A')

        # test __getitem__ calls w autoSort
        s = Stream()
        s.autoSort = True
        n1 = note.Note('a')
        n2 = note.Note('b')
        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 (A) has a higher index than n2 (B)
        self.assertEqual(s[0].name, 'A')
        self.assertEqual(s[1].name, 'B')


        # test .elements calls w/ autoSort
        s = Stream()
        s.autoSort = False
        n1 = note.Note('a')
        n2 = note.Note('b')
        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 (A) has a higher index than n2 (B)
        self.assertEqual(s.elements[0].name, 'B')
        self.assertEqual(s.elements[1].name, 'A')

        # test .elements calls w autoSort
        s = Stream()
        s.autoSort = True
        n1 = note.Note('a')
        n2 = note.Note('b')
        s.insert(100, n2) # add  'b' first
        s.insert(0, n1) # now n1 (A) has a higher index than n2 (B)
        self.assertEqual(s.elements[0].name, 'A')
        self.assertEqual(s.elements[1].name, 'B')


        # test possible problematic casses of overlapping parts
        # store start time, dur
        pairs = [(20, 2), (15, 10), (22,1), (10, 2), (5, 25), (8, 10), (0, 2), (0, 30)]
        
        # with autoSort false
        s = Stream()
        s.autoSort = False
        for o, d in pairs:
            n = note.Note()
            n.quarterLength = d
            s.insert(o, n)
        match = []
        for n in s.notes:
            match.append((n.offset, n.quarterLength))
        self.assertEqual(pairs, match)
        
        # with autoSort True
        s = Stream()
        s.autoSort = True
        for o, d in pairs:
            n = note.Note()
            n.quarterLength = d
            s.insert(o, n)
        match = []
        for n in s.notes:
            match.append((n.offset, n.quarterLength))
        self.assertEqual([(0.0, 2), (0.0, 30), (5.0, 25), (8.0, 10), (10.0, 2), (15.0, 10), (20.0, 2), (22.0, 1.0)], match)


    def testMakeChordsBuiltA(self):
        from music21 import stream
        # test with equal durations
        pitchCol = [('A2', 'C2'), 
                    ('A#1', 'C-3', 'G5'), 
                    ('D3', 'B-1', 'C4', 'D#2')]
        # try with different duration assignments; should always get
        # the same results
        for durCol in [[1, 1, 1], [.5, 2, 3], [.25, .25, .5], [6, 6, 8]]: 
            s = stream.Stream()
            o = 0
            for i in range(len(pitchCol)):
                ql = durCol[i]
                for pStr in pitchCol[i]:
                    n = note.Note(pStr)
                    n.quarterLength = ql
                    s.insert(o, n)
                o += ql
            self.assertEqual(len(s), 9)
            self.assertEqual(len(s.getElementsByClass('Chord')), 0)
    
            # do both in place and not in place, compare results
            sMod = s.makeChords(inPlace=False)
            s.makeChords(inPlace=True)
            for sEval in [s, sMod]:
                self.assertEqual(len(sEval.getElementsByClass('Chord')), 3)
                # make sure we have all the original pitches
                for i in range(len(pitchCol)):
                    match = [p.nameWithOctave for p in
                             sEval.getElementsByClass('Chord')[i].pitches]
                    self.assertEqual(match, list(pitchCol[i]))


#         print 'post makeChords'
#         s.show('t')
        #sMod.show('t')
        #s.show()

    def testMakeChordsBuiltB(self):
        from music21 import stream

        n1 = note.Note('c2')
        n1.quarterLength = 2
        n2 = note.Note('d3')
        n2.quarterLength = .5

        n3 = note.Note('e4')
        n3.quarterLength = 2
        n4 = note.Note('f5')
        n4.quarterLength = .5

        s = stream.Stream()
        s.insert(0, n1)
        s.insert(1, n2) # overlapping, starting after n1 but finishing before
        s.insert(2, n3)
        s.insert(3, n4) # overlapping, starting after n3 but finishing before

        self.assertEqual([e.offset for e in s], [0.0, 1.0, 2.0, 3.0])
        # this results in two chords; n2 and n4 are effectively shifted 
        # to the start of n1 and n3
        sMod = s.makeChords(inPlace=False)
        s.makeChords(inPlace=True)   
        for sEval in [s, sMod]:
            self.assertEqual(len(sEval.getElementsByClass('Chord')), 2)
            self.assertEqual([c.offset for c in sEval], [0.0, 2.0])


        # do the same, but reverse the short/long duration relation
        # because the default min window is .25, the first  and last 
        # notes are not gathered into chords
        # into a chord
        n1 = note.Note('c2')
        n1.quarterLength = .5
        n2 = note.Note('d3')
        n2.quarterLength = 1.5
        n3 = note.Note('e4')
        n3.quarterLength = .5
        n4 = note.Note('f5')
        n4.quarterLength = 1.5

        s = stream.Stream()
        s.insert(0, n1)
        s.insert(1, n2) # overlapping, starting after n1 but finishing before
        s.insert(2, n3)
        s.insert(3, n4) # overlapping, starting after n3 but finishing before

        # this results in two chords; n2 and n4 are effectively shifted 
        # to the start of n1 and n3
        sMod = s.makeChords(inPlace=False)
        s.makeChords(inPlace=True)   
        for sEval in [s, sMod]:
            # have three chords, even though 1 only has more than 1 pitch
            # might change this?
            self.assertEqual(len(sEval.getElementsByClass('Chord')), 3)
            self.assertEqual([c.offset for c in sEval], [0.0, 1.0, 3.0] )


    def testMakeChordsBuiltC(self):
        # test removal of redundant pitches
        from music21 import stream

        n1 = note.Note('c2')
        n1.quarterLength = .5
        n2 = note.Note('c2')
        n2.quarterLength = .5
        n3 = note.Note('g2')
        n3.quarterLength = .5

        n4 = note.Note('e4')
        n4.quarterLength = .5
        n5 = note.Note('e4')
        n5.quarterLength = .5
        n6 = note.Note('f#4')
        n6.quarterLength = .5

        s1 = stream.Stream()
        s1.insert(0, n1)
        s1.insert(0, n2)
        s1.insert(0, n3)
        s1.insert(.5, n4)
        s1.insert(.5, n5)
        s1.insert(.5, n6)

        sMod = s1.makeChords(inPlace=False, removeRedundantPitches=True)
        self.assertEquals([p.nameWithOctave for p in sMod.getElementsByClass('Chord')[0].pitches], ['C2', 'G2'])

        self.assertEquals([p.nameWithOctave for p in sMod.getElementsByClass('Chord')[1].pitches], ['E4', 'F#4'])

        # without redundant pitch gathering
        sMod = s1.makeChords(inPlace=False, removeRedundantPitches=False)
        self.assertEquals([p.nameWithOctave for p in sMod.getElementsByClass('Chord')[0].pitches], ['C2', 'C2', 'G2'])

        self.assertEquals([p.nameWithOctave for p in sMod.getElementsByClass('Chord')[1].pitches], ['E4', 'E4', 'F#4'] )
            



    def testMakeChordsImported(self):
        from music21 import corpus
        s = corpus.parseWork('bach/bwv66.6')
        #s.show()
        # using in place to get the stored flat version
        sMod = s.flat.makeChords(includePostWindow=False)
        self.assertEqual(len(sMod.getElementsByClass('Chord')), 35)
        #sMod.show()
        self.assertEqual(
            [len(c.pitches) for c in sMod.getElementsByClass('Chord')], 
            [3, 4, 4, 3, 4, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 3, 4, 3, 4, 3, 4, 4, 4, 4, 3, 4, 4, 2, 4, 3, 4, 4])


        # when we include post-window, we get more tones, per chord
        # but the same number of chords
        sMod = s.flat.makeChords(includePostWindow=True)
        self.assertEqual(len(sMod.getElementsByClass('Chord')), 35)
        self.assertEqual(
            [len(c.pitches) for c in sMod.getElementsByClass('Chord')], 
            [6, 4, 4, 3, 4, 5, 5, 4, 4, 4, 4, 5, 4, 4, 5, 5, 5, 4, 5, 5, 3, 4, 3, 4, 4, 4, 7, 5, 4, 6, 2, 6, 4, 5, 4] )
        #sMod.show()



    def testElementsHighestTimeA(self): 
        '''Test adding elements at the highest time position
        '''
        from music21 import note, bar

        n1 = note.Note()
        n1.quarterLength = 30

        n2 = note.Note()
        n2.quarterLength = 20

        b1 = bar.Barline()

        s = Stream()
        s.append(n1)
        self.assertEqual(s.highestTime, 30)
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0], n1)
        self.assertEqual(s.index(n1), 0)
        self.assertEqual(s[0].activeSite, s)

        # insert bar in highest time position
        s.storeAtEnd(b1)
        self.assertEqual(len(s), 2)
        self.assertEqual(s[1], b1)
        self.assertEqual(s.index(b1), 1)
        self.assertEqual(s[1].activeSite, s)
        # offset of b1 is at the highest time
        self.assertEqual([e.offset for e in s], [0.0, 30.0])
     
        s.append(n2)
        self.assertEqual(len(s), 3)
        self.assertEqual(s[1], n2)
        self.assertEqual(s.index(n2), 1)
        self.assertEqual(s[2], b1)
        self.assertEqual(s.index(b1), 2)
        self.assertEqual(s.highestTime, 50)
        # there are now three elements, and the third is the bar
        self.assertEqual([e.offset for e in s], [0.0, 30, 50.0])


        # get offset by elements
        self.assertEqual(s.getOffsetByElement(n1), 0.0)
        self.assertEqual(s.getOffsetByElement(b1), 50)


        # get elements by offset

        found1 = s.getElementsByOffset(0, 40)
        self.assertEqual(len(found1.notes), 2)
        # check within the maximum range
        found2 = s.getElementsByOffset(40, 60)
        self.assertEqual(len(found2.notes), 0)
        # found the barline
        self.assertEqual(found2[0], b1)

        # should get the barline
        self.assertEqual(s.getElementAtOrBefore(50), b1)
        self.assertEqual(s.getElementAtOrBefore(49), n2)

        # can get element after element
        self.assertEqual(s.getElementAfterElement(n1), n2)
        self.assertEqual(s.getElementAfterElement(n2), b1)

        # try to get elements by class
        sub1 = s.getElementsByClass('Barline')
        self.assertEqual(len(sub1), 1)
        # only found item is barline
        self.assertEqual(sub1[0], b1)
        self.assertEqual([e.offset for e in sub1], [0.0])
        # if we append a new element, the old barline should report
        # an offset at the last element
        n3 = note.Note()
        n3.quarterLength = 10
        sub1.append(n3) # places this before barline
        self.assertEqual(sub1[sub1.index(b1)].offset, 10.0)
        self.assertEqual([e.offset for e in sub1], [0.0, 10.0])

        # try to get elements not of class; only have notes
        sub2 = s.getElementsNotOfClass(bar.Barline)
        self.assertEqual(len(sub2), 2)
        self.assertEqual(len(sub2.notes), 2)

        sub3 = s.getElementsNotOfClass(note.Note)
        self.assertEqual(len(sub3), 1)
        self.assertEqual(len(sub3.notes), 0)


        # make a copy:
        sCopy = copy.deepcopy(s)
        self.assertEqual([e.offset for e in sCopy], [0.0, 30, 50.0])
        # not equal b/c a deepcopy was made
        self.assertEqual(id(sCopy[2]) == id(b1), False)
        # can still match class
        self.assertEqual(isinstance(sCopy[2], bar.Barline), True)    


        # create another barline and try to replace
        b2 = bar.Barline()
        s.replace(b1, b2)
        self.assertEqual(id(s[2]), id(b2))


        # try to remove elements; the the second index is the barline
        self.assertEqual(s.pop(2), b2)
        self.assertEqual(len(s), 2)
        self.assertEqual([e.offset for e in s], [0.0, 30])

        # add back again.
        s.storeAtEnd(b1)
        self.assertEqual([e.offset for e in s], [0.0, 30, 50.0])

        # try to remove intermediary elements
        self.assertEqual(s.pop(1), n2)
        # offset of highest time element has shifted
        self.assertEqual([e.offset for e in s], [0.0, 30.0])
        # index is now 1
        self.assertEqual(s.index(b1), 1)


    def testElementsHighestTimeB(self): 
        '''Test adding elements at the highest time position
        '''
        from music21 import note, bar

        n1 = note.Note()
        n1.quarterLength = 30

        n2 = note.Note()
        n2.quarterLength = 20

        b1 = bar.Barline()

        s = Stream()
        s.append(n1)
        s.append(n2)
        s.storeAtEnd(b1)
        self.assertEqual([e.offset for e in s], [0.0, 30.0, 50.0])

        # can shift elements, altering all, but only really shifting 
        # standard elements
        s.shiftElements(5)
        self.assertEqual([e.offset for e in s], [5.0, 35.0, 55.0])

        # got all
        found1 = s.extractContext(n2, 30)
        self.assertEqual([e.offset for e in found1], [5.0, 35.0, 55.0])
        # just after, none before
        found1 = s.extractContext(n2, 0, 30)
        self.assertEqual([e.offset for e in found1], [35.0, 55.0])



    def testElementsHighestTimeC(self): 

        n1 = note.Note()
        n1.quarterLength = 30
        
        n2 = note.Note()
        n2.quarterLength = 20
        
        ts1 = meter.TimeSignature('6/8')
        b1 = bar.Barline()
        c1 = clef.Treble8vaClef()
        
        s = Stream()
        s.append(n1)
        self.assertEqual([e.offset for e in s], [0.0])
        
        s.storeAtEnd(b1)
        s.storeAtEnd(c1)
        s.storeAtEnd(ts1)
        self.assertEqual([e.offset for e in s], [0.0, 30.0, 30.0, 30.0] )
        
        s.append(n2)
        self.assertEqual([e.offset for e in s], [0.0, 30.0, 50.0, 50.0, 50.0] )
        # sorting of objects is by class
        self.assertEqual([e.classes[0] for e in s], ['Note', 'Note', 'Treble8vaClef', 'TimeSignature', 'Barline']  )
        
        b2 = bar.Barline()
        s.storeAtEnd(b2)
        self.assertEqual([e.classes[0] for e in s], ['Note', 'Note', 'Treble8vaClef', 'TimeSignature', 'Barline', 'Barline'] )




    def testSliceByQuarterLengthsBuilt(self):
        from music21 import note
        s = Stream()
        n1 = note.Note()
        n1.quarterLength = 1

        n2 = note.Note()
        n2.quarterLength = 2

        n3 = note.Note()
        n3.quarterLength = .5

        n4 = note.Note()
        n4.quarterLength = 1.5

        for n in [n1,n2,n3,n4]:
            s.append(n)
    
        post = s.sliceByQuarterLengths(.125, inPlace=False)
        self.assertEqual([n.tie.type for n in post.notes], ['start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop'] )

        post = s.sliceByQuarterLengths(.25, inPlace=False)
        self.assertEqual([n.tie.type for n in post.notes], ['start', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'stop'] )

        post = s.sliceByQuarterLengths(.5, inPlace=False)
        self.assertEqual([n.tie == None for n in post.notes], [False, False, False, False, False, False, True, False, False, False] )

        # cannot map .3333 into .5, so this raises an exception
        self.assertRaises(StreamException, lambda: s.sliceByQuarterLengths(1/3., inPlace=False))

        post = s.sliceByQuarterLengths(1/6., inPlace=False)
        self.assertEqual([n.tie.type for n in post.notes], ['start', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop'])
        #post.show()

        # try to slice just a target
        post = s.sliceByQuarterLengths(.125, target=n2, inPlace=False)
        self.assertEqual([n.tie == None for n in post.notes], [True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True] )

        #post.show()

        # test case where we have an existing tied note in a multi Measure structure that we do not want to break
        s = Stream()
        n1 = note.Note()
        n1.quarterLength = 8

        n2 = note.Note()
        n2.quarterLength = 8

        n3 = note.Note()
        n3.quarterLength = 8

        s.append(n1)
        s.append(n2)
        s.append(n3)

        self.assertEqual(s.highestTime, 24)
        sMeasures = s.makeMeasures()
        sMeasures.makeTies(inPlace=True)

        self.assertEquals([n.tie.type for n in sMeasures.flat.notes], 
            ['start', 'stop', 'start', 'stop', 'start', 'stop'] )

        # this shows that the previous ties across the bar line are maintained
        # even after slicing
        sMeasures.sliceByQuarterLengths([.5], inPlace=True)
        self.assertEquals([n.tie.type for n in sMeasures.flat.notes], 
            ['start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop']  )

        #sMeasures.show()


        s = Stream()
        n1 = note.Note('c#')
        n1.quarterLength = 1

        n2 = note.Note('d-')
        n2.quarterLength = 2

        n3 = note.Note('f#')
        n3.quarterLength = .5

        n4 = note.Note('g#')
        n4.quarterLength = 1.5

        for n in [n1,n2,n3,n4]:
            s.append(n)
    
        post = s.sliceByQuarterLengths(.125, inPlace=False)
        #post.show()

        self.assertEqual([n.tie == None for n in post.notes], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False])


        s = Stream()
        n1 = note.Note()
        n1.quarterLength = .25

        n2 = note.Note()
        n2.quarterLength = .5

        n3 = note.Note()
        n3.quarterLength = 1

        n4 = note.Note()
        n4.quarterLength = 1.5

        for n in [n1,n2,n3,n4]:
            s.append(n)
    
        post = s.sliceByQuarterLengths(.5, inPlace=False)
        self.assertEqual([n.tie == None for n in post.notes], [True, True, False, False, False, False, False])



    def testSliceByQuarterLengthsImported(self):

        from music21 import corpus, converter
        sSrc = corpus.parseWork('bwv66.6')
        s = copy.deepcopy(sSrc)
        for p in s.parts:
            p.sliceByQuarterLengths(.5, inPlace=True, addTies=False)
            p.makeBeams(inPlace=True)
        self.assertEqual(len(s.parts[0].flat.notes), 72)
        self.assertEqual(len(s.parts[1].flat.notes), 72)
        self.assertEqual(len(s.parts[2].flat.notes), 72)
        self.assertEqual(len(s.parts[3].flat.notes), 72)

        s = copy.deepcopy(sSrc)
        for p in s.parts:
            p.sliceByQuarterLengths(.25, inPlace=True, addTies=False)
            p.makeBeams(inPlace=True)
        self.assertEqual(len(s.parts[0].flat.notes), 144)
        self.assertEqual(len(s.parts[1].flat.notes), 144)
        self.assertEqual(len(s.parts[2].flat.notes), 144)
        self.assertEqual(len(s.parts[3].flat.notes), 144)
            

        # test applying to a complete score; works fine
        s = copy.deepcopy(sSrc)
        s.sliceByQuarterLengths(.5, inPlace=True, addTies=False)
        #s.show()
        self.assertEqual(len(s.parts[0].flat.notes), 72)
        self.assertEqual(len(s.parts[1].flat.notes), 72)
        self.assertEqual(len(s.parts[2].flat.notes), 72)
        self.assertEqual(len(s.parts[3].flat.notes), 72)


    def testSliceByGreatestDivisorBuilt(self):
        from music21 import note

        s = Stream()
        n1 = note.Note()
        n1.quarterLength = 1.75
        n2 = note.Note()
        n2.quarterLength = 2
        n3 = note.Note()
        n3.quarterLength = .5
        n4 = note.Note()
        n4.quarterLength = 1.5
        for n in [n1,n2,n3,n4]:
            s.append(n)
        post = s.sliceByGreatestDivisor(inPlace=False)

        self.assertEqual(len(post.flat.notes), 23)
        self.assertEqual([n.tie.type for n in post.notes], ['start', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'stop'])


        s = Stream()
        n1 = note.Note()
        n1.quarterLength = 2
        n2 = note.Note()
        n2.quarterLength = 1/3.
        n3 = note.Note()
        n3.quarterLength = .5
        n4 = note.Note()
        n4.quarterLength = 1.5
        for n in [n1,n2,n3,n4]:
            s.append(n)
        post = s.sliceByGreatestDivisor(inPlace=False)

        self.assertEqual(len(post.flat.notes), 26)
        self.assertEqual([n.tie.type for n in post.notes], ['start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop', 'start', 'stop', 'start', 'continue', 'stop', 'start', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'continue', 'stop'] )


    def testSliceByGreatestDivisorImported(self):

        from music21 import corpus, converter
        sSrc = corpus.parseWork('bwv66.6')
        s = copy.deepcopy(sSrc)
        for p in s.parts:
            p.sliceByGreatestDivisor(inPlace=True, addTies=True)
            p.makeBeams(inPlace=True)
        #s.show()
        # parts have different numbers of notes, as splitting is done on 
        # a note per note basis
        self.assertEqual(len(s.parts[0].flat.notes), 44)
        self.assertEqual(len(s.parts[1].flat.notes), 59)
        self.assertEqual(len(s.parts[2].flat.notes), 61)
        self.assertEqual(len(s.parts[3].flat.notes), 53)


        s = copy.deepcopy(sSrc)
        s.sliceByGreatestDivisor(inPlace=True, addTies=True)
        #s.flat.makeChords().show()
        #s.show()


    def testSliceAtOffsetsBuilt(self):

        from music21 import stream, note
        s = stream.Stream()
        for p, ql in [('d2',4)]:
            n = note.Note(p)
            n.quarterLength = ql
            s.append(n)
        self.assertEqual([e.offset for e in s], [0.0])

        s1 = s.sliceAtOffsets([0.5, 1, 1.5, 2, 2.5, 3, 3.5], inPlace=False)
        self.assertEqual([(e.offset, e.quarterLength) for e in s1], [(0.0, 0.5), (0.5, 0.5), (1.0, 0.5), (1.5, 0.5), (2.0, 0.5), (2.5, 0.5), (3.0, 0.5), (3.5, 0.5)] )

        s1 = s.sliceAtOffsets([.5], inPlace=False)
        self.assertEqual([(e.offset, e.quarterLength) for e in s1], [(0.0, 0.5), (0.5, 3.5)])



        s = stream.Stream()
        for p, ql in [('a2',1.5), ('a2',1.5), ('a2',1.5)]:
            n = note.Note(p)
            n.quarterLength = ql
            s.append(n)
        self.assertEqual([e.offset for e in s], [0.0, 1.5, 3.0])

        s1 = s.sliceAtOffsets([.5], inPlace=False)
        self.assertEqual([e.offset for e in s1], [0.0, 0.5, 1.5, 3.0])
        s1.sliceAtOffsets([1.0, 2.5], inPlace=True)
        self.assertEqual([e.offset for e in s1], [0.0, 0.5, 1.0, 1.5, 2.5, 3.0])
        s1.sliceAtOffsets([3.0, 2.0, 3.5, 4.0], inPlace=True)
        self.assertEqual([e.offset for e in s1], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])

        self.assertEqual([e.quarterLength for e in s1], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])


    def testSliceAtOffsetsImported(self):

        from music21 import corpus, converter
        sSrc = corpus.parseWork('bwv66.6')

        post = sSrc.parts[0].flat.sliceAtOffsets([.25, 1.25, 3.25])
        self.assertEqual([e.offset for e in post], [0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.5, 1.0, 1.25, 2.0, 3.0, 3.25, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.0, 9.5, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 29.0, 31.0, 32.0, 33.0, 34.0, 34.5, 35.0, 36.0] )

        # will also work on measured part
        post = sSrc.parts[0].sliceAtOffsets([.25, 1.25, 3.25, 35.125])
        self.assertEqual([e.offset for e in 
            post.getElementsByClass('Measure')[0].notes], [0.0, 0.25, 0.5])
        self.assertEqual([e.offset for e in 
            post.getElementsByClass('Measure')[1].notes], [0.0, 0.25, 1.0, 2.0, 2.25, 3.0])
        # check for alteration in last measure
        self.assertEqual([e.offset for e in 
            post.getElementsByClass('Measure')[-1].notes], [0.0, 1.0, 1.5, 2.0, 2.125] )


    def testSliceByBeatBuilt(self):

        from music21 import stream, note, meter
        s = stream.Stream()
        ts1 = meter.TimeSignature('3/4')
        s.insert(0, ts1)
        for p, ql in [('d2',3)]:
            n = note.Note(p)
            n.quarterLength = ql
            s.append(n)
        # have time signature and one note
        self.assertEqual([e.offset for e in s], [0.0, 0.0])

        s1 = s.sliceByBeat()
        self.assertEqual([(e.offset, e.quarterLength) for e in s1.notes], [(0.0, 1.0), (1.0, 1.0), (2.0, 1.0)] )

        # replace old ts with a new 
        s.remove(ts1)
        ts2 = meter.TimeSignature('6/8')
        s.insert(0, ts2)
        s1 = s.sliceByBeat()
        self.assertEqual([(e.offset, e.quarterLength) for e in s1.notes], [(0.0, 1.5), (1.5, 1.5)] )



    def testSliceByBeatImported(self):

        from music21 import corpus, converter
        sSrc = corpus.parseWork('bwv66.6')
        post = sSrc.parts[0].sliceByBeat()
        self.assertEqual([e.offset for e in post.flat.notes],  [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.5, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 34.5, 35.0])

        #post.show()

    def testChordifyImported(self):
        from music21 import stream, corpus
        s = corpus.parseWork('gloria')
        #s.show()
        post = s.measures(0,20, gatherSpanners=False)
        # somehow, this is doubling measures
        #post.show()

        self.assertEqual([e.offset for e in post.parts[0].flat.notes], [0.0, 3.0, 3.5, 4.5, 5.0, 6.0, 6.5, 7.5, 8.5, 9.0, 10.5, 12.0, 15.0, 16.5, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 30.0, 33.0, 34.5, 35.5, 36.0, 37.5, 38.0, 39.0, 40.0, 41.0, 42.0, 43.5, 45.0, 45.5, 46.5, 47.0, 48.0, 49.5, 51.0, 51.5, 52.0, 52.5, 53.0, 53.5, 54.0, 55.5, 57.0, 58.5])

        post = post.chordify()
        self.assertEqual([e.offset for e in post.notes], [0.0, 3.0, 3.5, 4.5, 5.0, 5.5, 6.0, 6.5, 7.5, 8.5, 9.0, 10.5, 12.0, 15.0, 16.5, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 30.0, 33.0, 34.5, 35.5, 36.0, 37.5, 38.0, 39.0, 40.0, 40.5, 41.0, 42.0, 43.5, 45.0, 45.5, 46.0, 46.5, 47.0, 47.5, 48.0, 49.5, 51.0, 51.5, 52.0, 52.5, 53.0, 53.5, 54.0, 54.5, 55.0, 55.5, 56.0, 56.5, 57.0, 58.5, 59.5])

        self.assertEqual(len(post.getElementsByClass('Chord')), 71)

# this is not write [0.0, 6.0, 6.5, 7.5, 8.0, 8.5, 12.0, 12.5, 13.5, 14.5, 18.0, 19.5, 24.0, 30.0, 31.5, 32.5, 36.0, 36.5, 37.0, 37.5, 38.0, 38.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 48.0, 48.5, 49.0, 49.5, 50.0, 50.5, 54.0, 60.0, 66.0, 67.5, 68.5, 72.0, 73.5, 74.0, 78.0, 79.0, 79.5, 80.0, 84.0, 85.5, 90.0, 90.5, 91.0, 91.5, 92.0, 92.5, 96.0, 97.5, 102.0, 102.5, 103.0, 103.5, 104.0, 104.5, 108.0, 108.5, 109.0, 109.5, 110.0, 110.5, 114.0, 115.5, 116.5] 

    def testChordifyRests(self):
        # test that chordify does not choke on rests

        from music21 import stream, note

        p1 = stream.Part()
        for p, ql in [(None, 2), ('d2',2), (None, 2), ('e3',2), ('f3', 2)]:
            if p == None:
                n = note.Rest()
            else:
                n = note.Note(p)
            n.quarterLength = ql
            p1.append(n)

        p2 = stream.Part()
        for p, ql in [(None, 2), ('d3',1), ('d#3',1), (None, 2), ('e5',2), (None, 2)]:
            if p == None:
                n = note.Rest()
            else:
                n = note.Note(p)
            n.quarterLength = ql
            p2.append(n)

        self.assertEqual([e.offset for e in p1], [0.0, 2.0, 4.0, 6.0, 8.0])
        self.assertEqual([e.offset for e in p2], [0.0, 2.0, 3.0, 4.0, 6.0, 8.0])

        score = stream.Score()
        score.insert(0, p1)
        score.insert(0, p2)

        # parts retain their characteristics, rests are retained in position
        scoreChords = score.makeChords()
        self.assertEqual(len(scoreChords.parts[0].flat), 5)
        self.assertEqual(len(scoreChords.parts[0].flat.getElementsByClass(
            'Chord')), 3)
        self.assertEqual(len(scoreChords.parts[0].flat.getElementsByClass(
            'Rest')), 2)

        self.assertEqual(len(scoreChords.parts[1].flat), 6)
        self.assertEqual(len(scoreChords.parts[1].flat.getElementsByClass(
            'Chord')), 3)
        self.assertEqual(len(scoreChords.parts[1].flat.getElementsByClass(
            'Rest')), 3)

        # calling this on a flattened version
        scoreChords = score.flat.makeChords()
        self.assertEqual(len(scoreChords.flat.getElementsByClass(
            'Chord')), 3)
        self.assertEqual(len(scoreChords.flat.getElementsByClass(
            'Rest')), 2)

        
        scoreChordify = score.chordify()
        self.assertEqual(len(scoreChordify.flat.getElementsByClass(
            'Chord')), 4)
        self.assertEqual(len(scoreChordify.flat.getElementsByClass(
            'Rest')), 2)

        self.assertEqual(str(scoreChordify.getElementsByClass(
            'Chord')[0].pitches), '[D2, D3]')
        self.assertEqual(str(scoreChordify.getElementsByClass(
            'Chord')[1].pitches), '[D2, D#3]')



    def testOpusSearch(self):
        from music21 import corpus
        import re
        o = corpus.parseWork('essenFolksong/erk5')
        s = o.getScoreByTitle('blauen')
        self.assertEqual(s.metadata.title, 'Ich sach mir einen blauen Storchen')
        
        s = o.getScoreByTitle('pfal.gr.f')
        self.assertEqual(s.metadata.title, 'Es fuhr sich ein Pfalzgraf')
        
        s = o.getScoreByTitle(re.compile('Pfal(.*)'))
        self.assertEqual(s.metadata.title, 'Es fuhr sich ein Pfalzgraf')

    
    def testActiveSiteMangling(self):
        import clef, meter

        s1 = Stream()
        s2 = Stream()
        s2.append(s1)
        
        self.assertEqual(s1.activeSite, s2)
        junk = s1.semiFlat
        self.assertEqual(s1.activeSite, s2)
        junk = s1.flat
        self.assertEqual(s1.activeSite, s2)
        
        # this works fine
        junk = s2.flat
        self.assertEqual(s1.activeSite, s2)
        
        # this was the key problem: getting the semiFlat of the activeSite   
        # looses the activeSite of the sub-stream; this is fixed by the inserting
        # of the sub-Stream with setActiveSite False
        junk = s2.semiFlat
        self.assertEqual(s1.activeSite, s2)

        # these test prove that getting a semiFlat stream does not change the
        # activeSite
        junk = s1._definedContexts.getByClass(meter.TimeSignature)
        self.assertEqual(s1.activeSite, s2)

        junk = s1._definedContexts.getByClass(clef.Clef)
        self.assertEqual(s1.activeSite, s2)

        junk = s1.getContextByClass('Clef')
        self.assertEqual(s1.activeSite, s2)



    def testGetElementsByContextStream(self):
        from music21 import corpus, meter, key, clef

        s = corpus.parseWork('bwv66.6')
        for p in s.parts:
            for m in p.getElementsByClass('Measure'):
                post = m.getContextByClass(clef.Clef)
                self.assertEqual(isinstance(post, clef.Clef), True)
                post = m.getContextByClass(meter.TimeSignature)
                self.assertEqual(isinstance(post, meter.TimeSignature), True)
                post = m.getContextByClass(key.KeySignature)
                self.assertEqual(isinstance(post, key.KeySignature), True)



    def testVoicesA(self):

        v1 = Voice()
        n1 = note.Note('d5')
        n1.quarterLength = .5
        v1.repeatAppend(n1, 8)

        v2 = Voice()
        n2 = note.Note('c4')
        n2.quarterLength = 1
        v2.repeatAppend(n2, 4)
        
        s = Stream()
        s.insert(0, v1)
        s.insert(0, v2)

        # test allocating streams and assigning indices
        oMap = s.offsetMap
        oMapStr = "[\n" # construct string from dict in fixed order...
        for ob in oMap:
            oMapStr += "{'voiceIndex': " + str(ob['voiceIndex']) + ", 'element': " + str(ob['element']) + ", 'endTime': " + str(ob['endTime']) + ", 'offset': " + str(ob['offset']) + "},\n"
        oMapStr += "]\n"
        #print oMapStr
        self.assertEqual(oMapStr, 
        '''[
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 0.5, 'offset': 0.0},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 1.0, 'offset': 0.5},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 1.5, 'offset': 1.0},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 2.0, 'offset': 1.5},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 2.5, 'offset': 2.0},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 3.0, 'offset': 2.5},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 3.5, 'offset': 3.0},
{'voiceIndex': 0, 'element': <music21.note.Note D>, 'endTime': 4.0, 'offset': 3.5},
{'voiceIndex': 1, 'element': <music21.note.Note C>, 'endTime': 1.0, 'offset': 0.0},
{'voiceIndex': 1, 'element': <music21.note.Note C>, 'endTime': 2.0, 'offset': 1.0},
{'voiceIndex': 1, 'element': <music21.note.Note C>, 'endTime': 3.0, 'offset': 2.0},
{'voiceIndex': 1, 'element': <music21.note.Note C>, 'endTime': 4.0, 'offset': 3.0},
]
''')
        oMeasures = s.makeMeasures()
        self.assertEqual(len(oMeasures[0].voices), 2)
        self.assertEqual([e.offset for e in oMeasures[0].voices[0]], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
        self.assertEqual([e.offset for e in oMeasures[0].voices[1]], [0.0, 1.0, 2.0, 3.0])

        post = s.musicxml


        # try version longer than 1 measure, more than 2 voices
        v1 = Voice()
        n1 = note.Note('c5')
        n1.quarterLength = .5
        v1.repeatAppend(n1, 32)

        v2 = Voice()
        n2 = note.Note('c4')
        n2.quarterLength = 1
        v2.repeatAppend(n2, 16)

        v3 = Voice()
        n3 = note.Note('c3')
        n3.quarterLength = .25
        v3.repeatAppend(n3, 64)

        v4 = Voice()
        n4 = note.Note('c2')
        n4.quarterLength = 4
        v4.repeatAppend(n4, 4)
        
        s = Stream()
        s.insert(0, v1)
        s.insert(0, v2)
        s.insert(0, v3)
        s.insert(0, v4)

        oMeasures = s.makeMeasures()

        # each measures has the same number of voices
        for i in range(3):
            self.assertEqual(len(oMeasures[i].voices), 4)
        # each measures has the same total number of voices
        for i in range(3):
            self.assertEqual(len(oMeasures[i].flat.notes), 29)
        # each measures has the same number of notes for each voices
        for i in range(3):
            self.assertEqual(len(oMeasures[i].voices[0].notes), 8)
            self.assertEqual(len(oMeasures[i].voices[1].notes), 4)
            self.assertEqual(len(oMeasures[i].voices[2].notes), 16)
            self.assertEqual(len(oMeasures[i].voices[3].notes), 1)



        post = s.musicxml
        #s.show()



    def testVoicesB(self):

        # make sure strip ties works
        from music21 import stream

        v1 = stream.Voice()
        n1 = note.Note('c5')
        n1.quarterLength = .5
        v1.repeatAppend(n1, 27)

        v2 = stream.Voice()
        n2 = note.Note('c4')
        n2.quarterLength = 3
        v2.repeatAppend(n2, 6)

        v3 = stream.Voice()
        n3 = note.Note('c3')
        n3.quarterLength = 8
        v3.repeatAppend(n3, 4)
        
        s = stream.Stream()
        s.insert(0, v1)
        s.insert(0, v2)
        s.insert(0, v3)

        sPost = s.makeNotation()
        # voices are retained for all measures after make notation
        self.assertEqual(len(sPost.getElementsByClass('Measure')), 8)
        self.assertEqual(len(sPost.getElementsByClass('Measure')[0].voices), 3)
        self.assertEqual(len(sPost.getElementsByClass('Measure')[1].voices), 3)
        self.assertEqual(len(sPost.getElementsByClass('Measure')[5].voices), 3)
        self.assertEqual(len(sPost.getElementsByClass('Measure')[7].voices), 3)

        #s.show()


    def testVoicesC(self):
        from music21 import stream
        v1 = stream.Voice()
        n1 = note.Note('c5')
        n1.quarterLength = .25
        v1.repeatInsert(n1, [2, 4.5, 7.25, 11.75])

        v2 = stream.Voice()
        n2 = note.Note('c4')
        n2.quarterLength = .25
        v2.repeatInsert(n2, [.25, 3.75, 5.5, 13.75])

        s = stream.Stream()
        s.insert(0, v1)
        s.insert(0, v2)

        sPost = s.makeRests(fillGaps=True, inPlace=False)
        self.assertEqual(str([n for n in sPost.voices[0].notes]), '[<music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>]')
        self.assertEqual(str([n for n in sPost.voices[1].notes]), '[<music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>, <music21.note.Note C>, <music21.note.Rest rest>, <music21.note.Note C>]')

        #sPost.show()


    def testPartsToVoicesA(self):
        from music21 import corpus
        s0 = corpus.parseWork('bwv66.6')
        #s.show()
        s1 = s0.partsToVoices(2)
        #s1.show()
        #s1.show('t')
        self.assertEqual(len(s1.parts), 2)

        p1 = s1.parts[0]
        self.assertEqual(len(p1.flat.getElementsByClass('Clef')), 1)
        #p1.show('t')

        # look at individual measure; check counts; these should not
        # change after measure extraction
        m1Raw = p1.getElementsByClass('Measure')[1]
        environLocal.printDebug(['m1Raw', m1Raw])
        self.assertEqual(len(m1Raw.flat), 8)

        #m1Raw.show('t')
        m2Raw = p1.getElementsByClass('Measure')[2]
        environLocal.printDebug(['m2Raw', m2Raw])
        self.assertEqual(len(m2Raw.flat), 9)

        # get a measure from this part
        m1 = p1.measure(2)
        self.assertEqual(len(m1.flat.getElementsByClass('Clef')), 1)

        # look at individual measure; check counts; these should not
        # change after measure extraction
        m1Raw = p1.getElementsByClass('Measure')[1]
        environLocal.printDebug(['m1Raw', m1Raw])
        self.assertEqual(len(m1Raw.flat), 8)

        #m1Raw.show('t')
        m2Raw = p1.getElementsByClass('Measure')[2]
        environLocal.printDebug(['m2Raw', m2Raw])
        self.assertEqual(len(m2Raw.flat), 9)

        #m2Raw.show('t')

        self.assertEqual(len(m1.flat.getElementsByClass('Clef')), 1)
        ex1 = p1.measures(1,3)
        self.assertEqual(len(ex1.flat.getElementsByClass('Clef')), 1)

        #ex1.show()

        for p in s1.parts:
            # need to look in measures to get at voices
            self.assertEqual(len(p.getElementsByClass('Measure')[0].voices), 2)
            self.assertEqual(len(p.measure(2).voices), 2)
            self.assertEqual(len(p.measures(1,3)[2].voices), 2)

        #s1.show()
        #p1.show()



    def testPartsToVoicesB(self):
        from music21 import corpus
        # this work has five parts: results in e parts
        s0 = corpus.parseWork('hwv56', '1-18')
        s1 = s0.partsToVoices(2, permitOneVoicePerPart=True)
        self.assertEqual(len(s1.parts), 3)
        self.assertEqual(len(s1.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s1.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s1.parts[2].getElementsByClass(
            'Measure')[0].voices), 1)

        #s1.show()

        s0 = corpus.parseWork('hwv56', '1-05')
        # can use index values
        s2 = s0.partsToVoices(([0,1], [2,4], 3), permitOneVoicePerPart=True)   
        self.assertEqual(len(s2.parts), 3)
        self.assertEqual(len(s2.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s2.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s2.parts[2].getElementsByClass(
            'Measure')[0].voices), 1)

        s2 = s0.partsToVoices((['Violino I','Violino II'], ['Viola','Bassi'], ['Basso']), permitOneVoicePerPart=True)
        self.assertEqual(len(s2.parts), 3)
        self.assertEqual(len(s2.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s2.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s2.parts[2].getElementsByClass(
            'Measure')[0].voices), 1)


        # this will keep the voice part unaltered
        s2 = s0.partsToVoices((['Violino I','Violino II'], ['Viola','Bassi'], 'Basso'), permitOneVoicePerPart=False)
        self.assertEqual(len(s2.parts), 3)
        self.assertEqual(len(s2.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s2.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(s2.parts[2].getElementsByClass(
            'Measure')[0].hasVoices(), False)


        # mm 16-19 are a good examples
        s1 = corpus.parseWork('hwv56', '1-05').measures(16, 19)
        s2 = s1.partsToVoices((['Violino I','Violino II'], ['Viola','Bassi'], 'Basso'))
        #s2.show()

        self.assertEqual(len(s2.parts), 3)
        self.assertEqual(len(s2.parts[0].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(len(s2.parts[1].getElementsByClass(
            'Measure')[0].voices), 2)
        self.assertEqual(s2.parts[2].getElementsByClass(
            'Measure')[0].hasVoices(), False)



    def testVoicesToPartsA(self):
        
        from music21 import corpus
        s0 = corpus.parseWork('bwv66.6')
        #s.show()
        s1 = s0.partsToVoices(2) # produce two parts each with two voices

        s2 = s1.parts[0].voicesToParts()
        # now a two part score
        self.assertEqual(len(s2.parts), 2)
        # makes sure we have what we started with
        self.assertEqual(len(s2.parts[0].flat.notes), len(s0.parts[0].flat.notes))


        s1 = s0.partsToVoices(4) # create one staff with all parts
        self.assertEqual(s1.classes[0], 'Score') # we get a Score back
        # we have a Score with one part and measures, each with 4 voices
        self.assertEqual(len(s1.parts[0].getElementsByClass(
            'Measure')[0].voices), 4)
        # need to access part
        s2 = s1.voicesToParts() # return to four parts in a score; 
        # make sure we have what we started with
        self.assertEqual(len(s2.parts[0].flat.notes),
                         len(s0.parts[0].flat.notes))
        self.assertEqual(str([n for n in s2.parts[0].flat.notes]),
                         str([n for n in s0.parts[0].flat.notes]))

        self.assertEqual(len(s2.parts[1].flat.notes),
                         len(s0.parts[1].flat.notes))
        self.assertEqual(str([n for n in s2.parts[1].flat.notes]),
                         str([n for n in s0.parts[1].flat.notes]))

        self.assertEqual(len(s2.parts[2].flat.notes),
                         len(s0.parts[2].flat.notes))
        self.assertEqual(str([n for n in s2.parts[2].flat.notes]),
                         str([n for n in s0.parts[2].flat.notes]))

        self.assertEqual(len(s2.parts[3].flat.notes),
                         len(s0.parts[3].flat.notes))
        self.assertEqual(str([n for n in s2.parts[3].flat.notes]),
                         str([n for n in s0.parts[3].flat.notes]))

        # try on a built Stream that has no Measures
        # build a stream
        s0 = Stream()
        v1 = Voice()
        v1.repeatAppend(note.Note('c3'), 4)
        v2 = Voice()
        v2.repeatAppend(note.Note('g4'), 4)
        v3 = Voice()
        v3.repeatAppend(note.Note('b5'), 4)
        s0.insert(0, v1)
        s0.insert(0, v2)
        s0.insert(0, v3)
        #s2.show()
        s1 = s0.voicesToParts()
        self.assertEqual(len(s1.parts), 3)
        #self.assertEqual(len(s1.parts[0].flat), len(v1.flat))
        self.assertEqual([e for e in s1.parts[0].flat], [e for e in v1.flat])

        self.assertEqual(len(s1.parts[1].flat), len(v2.flat))
        self.assertEqual([e for e in s1.parts[1].flat], [e for e in v2.flat])

        self.assertEqual(len(s1.parts[2].flat), len(v3.flat))
        self.assertEqual([e for e in s1.parts[2].flat], [e for e in v3.flat])

        #s1.show()

    def testMergeElements(self):
        from music21 import stream
        s1 = stream.Stream()
        s2 = stream.Stream()
        s3 = stream.Stream()

        n1 = note.Note('f#')
        n2 = note.Note('g')
        s1.append(n1)
        s1.append(n2)

        s2.mergeElements(s1)
        self.assertEqual(len(s2), 2)
        self.assertEqual(id(s1[0]) == id(s2[0]), True)
        self.assertEqual(id(s1[1]) == id(s2[1]), True)

        s3.mergeElements(s1, classFilterList=['Rest'])
        self.assertEqual(len(s3), 0)

        s3.mergeElements(s1, classFilterList=['GeneralNote'])
        self.assertEqual(len(s3), 2)


    def testInternalize(self):
        s = Stream()
        n1 = note.Note()
        s.repeatAppend(n1, 4)
        self.assertEqual(len(s), 4)
        
        s.internalize()
        # now have one component
        self.assertEqual(len(s), 1)        
        self.assertEqual(s[0].classes[0], 'Voice') # default is a Voice
        self.assertEqual(len(s[0]), 4)        
        self.assertEqual(str([n for n in s.voices[0].notes]), '[<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>]')        



    def testDeepcopySpanners(self):
        from music21 import note, spanner, stream
        n1 = note.Note()
        n2 = note.Note('a4')
        n3 = note.Note('g#4')
        n3.quarterLength = .25

        su1 = spanner.Slur(n1, n2)
        s1 = stream.Stream()
        s1.append(n1)
        s1.repeatAppend(n3, 4)
        s1.append(n2)
        s1.insert(su1)
   
        self.assertEqual(s1.notes[0] in s1.spanners[0].getComponents(), True)
        self.assertEqual(s1.notes[-1] in s1.spanners[0].getComponents(), True)
 
        s2 = copy.deepcopy(s1)

        # old relations are still valid
        self.assertEqual(len(s1.spanners), 1)
        self.assertEqual(s1.notes[0] in s1.spanners[0].getComponents(), True)
        self.assertEqual(s1.notes[-1] in s1.spanners[0].getComponents(), True)

        # new relations exist in new stream.
        self.assertEqual(len(s2.spanners), 1)
        self.assertEqual(s2.notes[0] in s2.spanners[0].getComponents(), True)
        self.assertEqual(s2.notes[-1] in s2.spanners[0].getComponents(), True)


        self.assertEqual(s2.spanners[0].getComponents(), [s2.notes[0], s2.notes[-1]])

        post = s2.musicxml
        #s2.show('t')
        #s2.show()


    def testAddSlurByMelisma(self):
        from music21 import corpus, spanner
        s = corpus.parseWork('luca/gloria')
        ex = s.parts[0]
        nStart = None
        nEnd = None
        
        exFlatNotes = ex.flat.notes
        nLast = exFlatNotes[-1]
        
        for i, n in enumerate(exFlatNotes):
            if i < len(exFlatNotes) - 1:
                nNext = exFlatNotes[i+1]
            else:
                continue
        
            if len(n.lyrics) > 0:
                nStart = n
            # if next is a begin, then this is an end
            elif nStart is not None and len(nNext.lyrics) > 0 and n.tie is None:
                nEnd = n
            elif nNext is nLast:
                nEnd = n
        
            if nStart is not None and nEnd is not None:
                # insert in top-most container
                ex.insert(spanner.Slur(nStart, nEnd))
                nStart = None
                nEnd = None
        #ex.show()
        exFlat = ex.flat
        melismaByBeat = {}
        for sp in ex.spanners:  
            n = sp.getFirst()
            oMin, oMax = sp.getDurationSpanBySite(exFlat)
            dur = oMax - oMin
            beatStr = n.beatStr
            if beatStr not in melismaByBeat.keys():
                melismaByBeat[beatStr] = []
            melismaByBeat[beatStr].append(dur)
            environLocal.printDebug(['start note:', n, 'beat:', beatStr, 'slured duration:', dur])

        for beatStr in sorted(melismaByBeat.keys()):
            avg = sum(melismaByBeat[beatStr]) / len(melismaByBeat[beatStr])
            environLocal.printDebug(['melisma beat:', beatStr.ljust(6), 'average duration:', avg])


        # this approach looks for end conditions based on syllabic attributes
        # and ties
        
        #         getNextEndTie = False
        #         for n in ex.flat.notes:
        #             if len(n.lyrics) > 0:
        #                 if n.lyrics[0].syllabic == 'begin':
        #                     nStart = n
        #                 elif n.lyrics[0].syllabic == 'end':
        #                     if n.tie is not None and n.tie.type != 'stop':
        #                         getNextEndTie = True
        #                     else:
        #                         nEnd = n
        # 
        #             if getNextEndTie:
        #                 if n.tie.type == 'stop':
        #                     nEnd = n
        #                     getNextEndTie = False
        # 
        #             if nStart is not None and nEnd is not None:
        #                 # insert in top-most container
        #                 ex.insert(spanner.Slur(nStart, nEnd))
        #                 nStart = None
        #                 nEnd = None


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Stream, Measure]



if __name__ == "__main__":

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()


#------------------------------------------------------------------------------
# eof



